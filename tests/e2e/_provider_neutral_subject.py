"""Shared mechanics for the pinned real-Ranex delegation subject."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REAL_REPO = Path(__file__).resolve().parents[2]
BASE_COMMIT = "f940da0f44a78fd754a402bcae98d745515b6354"
PATCH_COMMIT = "cebc06a33ba1f28fd21815bb21edbdc768b4a669"
FOCUSED_TEST = "tests/integration/test_slice072_dynamic_runtime_contract.py"


def nested_hermetic_boundary() -> bool:
    dependency_root = os.environ.get("UV_PROJECT_ENVIRONMENT")
    home = os.environ.get("HOME")
    temporary = os.environ.get("TMPDIR")
    if not dependency_root or not home or not temporary:
        return False
    materialisation = REAL_REPO.parent
    return (
        REAL_REPO.name == "tree"
        and materialisation.name.startswith("ranex-subject-")
        and Path.cwd().resolve() == REAL_REPO.resolve()
        and Path(dependency_root) == materialisation / "deps" / "env"
        and Path(home) == materialisation / "home"
        and Path(temporary) == materialisation / "tmp"
    )


def assert_nested_hermetic_boundary() -> None:
    assert nested_hermetic_boundary()
    assert (REAL_REPO / "src/ranex/cli/delegation.py").is_file()
    assert (REAL_REPO / FOCUSED_TEST).is_file()


@dataclass(frozen=True)
class RealSubject:
    repository: Path
    home: Path
    python: Path


def environment(subject: RealSubject) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(subject.home),
        "PYTHONPATH": str(REAL_REPO / "src"),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def git(subject: RealSubject, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(subject.repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment(subject),
    )
    return completed.stdout.strip()


def materialize(base: Path, *, commit: str = BASE_COMMIT) -> RealSubject:
    home = base / "home"
    home.mkdir()
    repository = base / "ranex-subject"
    subject = RealSubject(
        repository=repository,
        home=home,
        python=Path(sys.executable),
    )
    subprocess.run(
        ["git", "clone", "--quiet", str(REAL_REPO), str(repository)],
        check=True,
        env=environment(subject),
    )
    git(subject, "checkout", "--quiet", commit)
    return subject


def suite_command(subject: RealSubject) -> list[str]:
    """Use the active installed pytest entrypoint, preserving candidate imports."""
    executable = subject.python.with_name("pytest")
    assert executable.is_file(), "the active test environment must provide pytest"
    return [str(executable), "-q", FOCUSED_TEST]


def run_focused(subject: RealSubject) -> subprocess.CompletedProcess[str]:
    suite_environment = environment(subject)
    suite_environment["PYTHONPATH"] = str(subject.repository / "src")
    return subprocess.run(
        suite_command(subject),
        cwd=subject.repository,
        capture_output=True,
        text=True,
        check=False,
        env=suite_environment,
        timeout=120,
    )
