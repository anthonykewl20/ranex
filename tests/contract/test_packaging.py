"""The packaging contract for issue #63 (installed operator CLI), frozen red-first.

These tests are intentionally red against the pre-packaging tree. ``uv build``
must always be invoked with ``--exclude-newer 2026-08-04T00:00:00Z`` because a
bare ``uv lock``/epoch-less build silently escapes the frozen trust root
(probe-verified 2026-08-29).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tarfile
import tomllib
import zipfile
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

REPO_ROOT = Path(__file__).resolve().parents[2]
EXCLUDE_NEWER = "2026-08-04T00:00:00Z"
_UV_ON_PATH_SKIP_REASON = (
    "ranex-context:hermetic-freeze: uv-on-path prerequisite is absent; "
    "packaging build assertions run where uv is provisioned"
)


def _pyproject() -> dict:
    return tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _require_uv_on_path() -> None:
    """Skip build assertions only when this environment cannot resolve uv."""

    if shutil.which("uv") is None:
        pytest.skip(_UV_ON_PATH_SKIP_REASON)


def _run_build(distribution_flag: str, output_dir: Path) -> subprocess.CompletedProcess[str]:
    build_dir = REPO_ROOT / "build"
    build_dir_preexisted = build_dir.exists()
    try:
        return subprocess.run(
            [
                "uv",
                "build",
                distribution_flag,
                "--exclude-newer",
                EXCLUDE_NEWER,
                "--out-dir",
                str(output_dir),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    finally:
        if not build_dir_preexisted and build_dir.is_dir():
            shutil.rmtree(build_dir)


def _require_build_success(
    completed: subprocess.CompletedProcess[str], distribution: str
) -> None:
    assert completed.returncode == 0, (
        f"uv build {distribution} failed with exit code {completed.returncode}\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )


def _metadata_value(metadata: str, field: str) -> str:
    match = re.search(rf"^{re.escape(field)}: (.+)$", metadata, re.MULTILINE)
    assert match is not None, f"wheel METADATA is missing {field}:"
    return match.group(1)


@pytest.fixture(scope="module")
def wheel_build(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    _require_uv_on_path()
    output_dir = tmp_path_factory.mktemp("wheel-build")
    return output_dir, _run_build("--wheel", output_dir)


def test_pyproject_declares_build_system_and_entry_point() -> None:
    config = _pyproject()

    build_system = config.get("build-system")
    assert build_system is not None
    assert build_system["build-backend"] == "hatchling.build"
    assert build_system["requires"] == ["hatchling"]

    project = config["project"]
    assert project["scripts"]["ranex"] == "ranex.cli.main:main"
    assert config.get("tool", {}).get("uv", {}).get("package") is not False


def test_uv_lock_carries_nonvirtual_ranex_and_epoch() -> None:
    lock_text = (REPO_ROOT / "uv.lock").read_text(encoding="utf-8")
    package_blocks = re.findall(
        r"(?ms)^\[\[package\]\]\n.*?(?=^\[\[package\]\]\n|\Z)",
        lock_text,
    )
    ranex_entries = [
        block for block in package_blocks if re.search(r'^name = "ranex"$', block, re.MULTILINE)
    ]

    assert ranex_entries, 'uv.lock has no [[package]] entry named "ranex"'
    assert any('source = { editable = "." }' in block for block in ranex_entries)
    assert not any('source = { virtual = "." }' in block for block in ranex_entries)

    options = re.search(r"(?ms)^\[options\]\n(.*?)(?=^\[|\Z)", lock_text)
    assert options is not None, "uv.lock is missing its [options] section"
    assert re.search(
        rf'^exclude-newer = "{re.escape(EXCLUDE_NEWER)}"$',
        options.group(1),
        re.MULTILINE,
    )


def test_wheel_contains_package_and_console_entry_point(
    wheel_build: tuple[Path, subprocess.CompletedProcess[str]],
) -> None:
    output_dir, completed = wheel_build
    _require_build_success(completed, "--wheel")
    wheels = sorted(output_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    with zipfile.ZipFile(wheels[0]) as archive:
        members = set(archive.namelist())
        top_level_members = {member.split("/", 1)[0] for member in members}
        dist_info_dirs = {
            directory for directory in top_level_members if directory.endswith(".dist-info")
        }

        assert len(dist_info_dirs) == 1
        assert top_level_members == {"ranex", *dist_info_dirs}
        assert "ranex/__init__.py" in members
        assert "ranex/cli/main.py" in members

        dist_info = next(iter(dist_info_dirs))
        entry_points = archive.read(f"{dist_info}/entry_points.txt").decode("utf-8")
        assert entry_points == "[console_scripts]\nranex = ranex.cli.main:main\n"

        metadata = archive.read(f"{dist_info}/METADATA").decode("utf-8")
        project = _pyproject()["project"]
        assert _metadata_value(metadata, "Name") == "ranex"
        assert _metadata_value(metadata, "Version") == project["version"]


def test_sdist_contains_required_sources(tmp_path: Path) -> None:
    _require_uv_on_path()
    output_dir = tmp_path / "sdist-build"
    output_dir.mkdir()
    completed = _run_build("--sdist", output_dir)
    _require_build_success(completed, "--sdist")
    archives = sorted(output_dir.glob("*.tar.gz"))
    assert len(archives) == 1, f"expected exactly one sdist, found {archives}"

    with tarfile.open(archives[0], mode="r:gz") as archive:
        members = set(archive.getnames())
    project = _pyproject()["project"]
    root_prefix = f"ranex-{project['version']}/"
    assert all(member.startswith(root_prefix) for member in members), (
        f"expected every sdist member to start with {root_prefix!r}, found {members}"
    )
    root = root_prefix.rstrip("/")

    required_members = {
        f"{root}/pyproject.toml",
        f"{root}/src/ranex/__init__.py",
        f"{root}/README.md",
        f"{root}/LICENSE",
        f"{root}/uv.lock",
    }
    assert required_members <= members
    ignored_sdist_dirs = (".local", ".pytest_cache", ".venv", "mutants")
    for ignored_name in ignored_sdist_dirs:
        assert not any(
            f"/{ignored_name}/" in member or member.startswith(f"{root}/{ignored_name}/")
            for member in members
        ), f"sdist contains gitignored directory {ignored_name!r}"


def test_built_wheel_metadata_matches_project_metadata(
    wheel_build: tuple[Path, subprocess.CompletedProcess[str]],
) -> None:
    output_dir, completed = wheel_build
    _require_build_success(completed, "--wheel")
    wheels = sorted(output_dir.glob("*.whl"))
    assert len(wheels) == 1, f"expected exactly one wheel, found {wheels}"

    with zipfile.ZipFile(wheels[0]) as archive:
        metadata_names = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        assert len(metadata_names) == 1
        metadata = archive.read(metadata_names[0]).decode("utf-8")

    project = _pyproject()["project"]
    assert canonicalize_name(_metadata_value(metadata, "Name")) == canonicalize_name(
        project["name"]
    ) == "ranex"
    assert SpecifierSet(_metadata_value(metadata, "Requires-Python")) == SpecifierSet(
        project["requires-python"]
    )
