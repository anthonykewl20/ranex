"""Real-host acceptance coverage for ``ranex host strict-local`` (issue #64)."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
ROOT = E2E_DIR.parents[1]
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def _requires_qualified_host() -> None:
    """Every arm has the frame's exact delegated-cgroup prerequisite gate."""
    _prereqs.prereq_or_skip("qualified_host")


def _cli(arguments: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return _module(ROOT, "ranex.cli.main", *arguments, env=env)


def _environment(key: Path | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    return environment


def _module(
    repository: Path,
    module: str,
    *arguments: str,
    key: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # Source-run governance follows the CLI's checkout (ADR-009), so cwd
    # alone cannot select the provisioned clone's launcher and trust roots.
    environment = {**_environment(key), "PYTHONPATH": str(repository / "src")} if env is None else env
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def _require_git(repository: Path, *arguments: str) -> str:
    completed = _git(repository, *arguments)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _clone_governed_repository(path: Path, key: Path, producer: str) -> None:
    cloned = subprocess.run(
        ["git", "clone", "-q", str(ROOT), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, cloned.stderr
    _require_git(path, "config", "user.name", "Host Workflow E2E")
    _require_git(path, "config", "user.email", "host-workflow@example.invalid")
    generated = _module(path, "ranex.cli.main", "keygen", "--producer", producer, key=key)
    assert generated.returncode == 0, generated.stdout + generated.stderr
    public = re.search(r"ed25519:[A-Za-z0-9+/=]+", generated.stdout)
    assert public is not None, generated.stdout
    producers = path / "governance" / "producers.yaml"
    lines = producers.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next(index for index, line in enumerate(lines) if line.rstrip() == "producers:")
    lines.insert(header + 1, f"  {producer}: {public.group(0)}\n")
    producers.write_text("".join(lines), encoding="utf-8")
    _require_git(path, "rm", "-q", "governance/deps.yaml")
    _require_git(path, "add", "governance/producers.yaml")
    _require_git(path, "commit", "-qm", f"test: register {producer} for host workflow")


@dataclass(frozen=True)
class GovernedRepository:
    path: Path
    key: Path


def _v2_authority(repository: Path) -> tuple[str, str]:
    """Build and commit the exact public-v2 source-selector authorities."""
    task_root = "governance/qualification/inputs/SLICE-036-child-A"
    input_path = f"{task_root}/a-before-b/attempt-0"
    toolchain_root = "governance/qualification/worker"
    task = {
        "attempt": 0,
        "delay_ms": 0,
        "flow_id": "a-before-b",
        "mode": "normal",
        "task_id": "SLICE-036-child-A",
        "version": "slice036-child-input-v2",
    }
    input_file = repository / input_path / "task.json"
    input_file.parent.mkdir(parents=True)
    input_file.write_text(json.dumps(task, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    worker_root = repository / toolchain_root
    worker_root.mkdir(parents=True)
    source = ROOT / "tests" / "e2e" / "fixtures" / "slice036-worker.c"
    manifest_source = ROOT / "tests" / "e2e" / "fixtures" / "slice036-worker-build-v1.json"
    shutil.copyfile(source, worker_root / "slice036-worker.c")
    shutil.copyfile(manifest_source, worker_root / "slice036-worker-build-v1.json")
    manifest = json.loads(manifest_source.read_bytes())
    worker = worker_root / "slice036-worker"
    flags = [
        token.replace("<ABS_REPO_ROOT>", str(repository.resolve()))
        .replace("<output>", str(worker))
        .replace("<source>", str(worker_root / "slice036-worker.c"))
        for token in manifest["build"]["flags"]
    ]
    built = subprocess.run(
        [manifest["build"]["compiler"]["path"], *flags],
        cwd=repository,
        env=manifest["build"]["environment"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    assert hashlib.sha256(worker.read_bytes()).hexdigest() == manifest["artifact"]["sha256"]
    worker.chmod(0o555)
    _require_git(repository, "add", "governance/qualification")
    _require_git(repository, "commit", "-qm", "test: add admitted v2 authorities")
    return input_path, toolchain_root


def _v1_identity_probe(tmp_path: Path) -> Path:
    """Build one static v1 command allowed by the confined filesystem policy."""
    source = tmp_path / "v1-identity-probe.c"
    executable = tmp_path / "v1-identity-probe"
    source.write_text(
        """#include <stdio.h>
#include <unistd.h>

int main(void) {
    printf("uid=%ld\\n", (long)geteuid());
    return 0;
}
""",
        encoding="utf-8",
    )
    built = subprocess.run(
        [
            "/usr/bin/x86_64-linux-gnu-gcc-13",
            "-std=gnu17",
            "-O2",
            "-static",
            "-fno-pie",
            "-no-pie",
            "-Wl,-z,relro,-z,now",
            "-Wl,-z,noexecstack",
            "-Wl,--build-id=none",
            "-o",
            str(executable),
            str(source),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert built.returncode == 0, built.stderr
    executable.chmod(0o555)
    return executable


@pytest.fixture(scope="module")
def v2_repository(tmp_path_factory: pytest.TempPathFactory) -> GovernedRepository:
    base = tmp_path_factory.mktemp("host-workflow-v2")
    repository = base / "repository"
    key = base / "owner.key"
    _clone_governed_repository(repository, key, "owner")
    _v2_authority(repository)
    assert _require_git(repository, "status", "--porcelain", "--untracked-files=all") == ""
    return GovernedRepository(repository, key)


@pytest.fixture(scope="module")
def v3_repository(tmp_path_factory: pytest.TempPathFactory) -> GovernedRepository:
    base = tmp_path_factory.mktemp("host-workflow-v3")
    repository = base / "repository"
    key = base / "owner.key"
    _clone_governed_repository(repository, key, "slice072-owner")
    assert _require_git(repository, "status", "--porcelain", "--untracked-files=all") == ""
    return GovernedRepository(repository, key)


@pytest.fixture(scope="module")
def drift_repository(tmp_path_factory: pytest.TempPathFactory) -> GovernedRepository:
    base = tmp_path_factory.mktemp("host-workflow-drift")
    repository = base / "repository"
    key = base / "owner.key"
    _clone_governed_repository(repository, key, "slice072-owner")
    return GovernedRepository(repository, key)


def _report(result_dir: Path) -> dict[str, object]:
    path = result_dir / "host-run-report.json"
    raw = path.read_bytes()
    report = json.loads(raw)
    assert report["schema"] == "ranex-host-strict-local-run-v1"
    assert raw.endswith(b"\n")
    return report


def _assert_retained_logs(result_dir: Path, report: dict[str, object]) -> None:
    logs = report["logs"]
    assert isinstance(logs, dict)
    manifest = json.loads((result_dir / "logs" / "manifest.json").read_bytes())
    manifest_streams = manifest["streams"]
    assert isinstance(manifest_streams, dict)
    for name, entry in logs.items():
        assert isinstance(entry, dict)
        manifest_entry = manifest_streams[name]
        assert isinstance(manifest_entry, dict)
        assert {
            key: manifest_entry[key] for key in ("file", "bytes", "sha256")
        } == entry
        contents = (result_dir / "logs" / str(entry["file"])).read_bytes()
        assert entry["bytes"] == len(contents)
        assert entry["sha256"] == "sha256:" + hashlib.sha256(contents).hexdigest()


def test_v1_real_workflow_records_delegated_cgroup_and_run_record(
    tmp_path: Path, v2_repository: GovernedRepository
) -> None:
    """The documented v1 command enters (or reuses) a delegated user scope."""
    result_dir = tmp_path / "v1"
    probe = _v1_identity_probe(tmp_path)
    completed = _module(
        v2_repository.path,
        "ranex.cli.main",
        "host",
        "strict-local",
        "--version",
        "v1",
        "--claim",
        "host-workflow-v1",
        "--producer",
        "owner",
        "--repository",
        ".",
        "--evidence",
        ".local/ranex-e2e/v1-evidence.json",
        "--result-dir",
        str(result_dir),
        "--",
        str(probe),
        key=v2_repository.key,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "ENTERED  strict-local delegated scope" in completed.stdout or "BUILT" in completed.stdout
    lifecycle_positions = []
    for lifecycle in ("BUILT", "INSTALLED", "QUALIFIED", "CONFINED"):
        assert lifecycle in completed.stdout
        lifecycle_positions.append(completed.stdout.index(lifecycle))
    assert lifecycle_positions == sorted(lifecycle_positions)
    report = _report(result_dir)
    assert report["outcome"] == "confined"
    scope = report["scope"]
    assert isinstance(scope, dict)
    assert "/user@1000.service" in str(scope["cgroup_relative_path"])
    assert {"cpu", "memory", "pids"} <= set(scope["controllers"])
    assert "RECORDED  claim=host-workflow-v1" in (
        result_dir / "logs" / "stdout.log"
    ).read_text(encoding="utf-8")
    manifest = json.loads(
        (v2_repository.path / "governance/confinement/native-launcher-build-v1.json").read_bytes()
    )
    launcher = report["launcher"]
    assert isinstance(launcher, dict)
    assert launcher["artifact_sha256"] == "sha256:" + manifest["artifact"]["sha256"]
    qualification = result_dir / "qualification.json"
    canonical_qualification = v2_repository.path / ".local/ranex/qualification/strict-local-v1.json"
    assert qualification.read_bytes() == canonical_qualification.read_bytes()
    assert hashlib.sha256(qualification.read_bytes()).hexdigest() == hashlib.sha256(
        canonical_qualification.read_bytes()
    ).hexdigest()
    _assert_retained_logs(result_dir, report)


def test_v2_real_workflow_uses_paired_input_and_toolchain_selectors(
    tmp_path: Path, v2_repository: GovernedRepository
) -> None:
    """The wrapper runs the committed public-v2 source authorities for real."""
    result_dir = tmp_path / "v2"
    completed = _module(
        v2_repository.path,
        "ranex.cli.main",
        "host",
        "strict-local",
        "--version",
        "v2",
        "--claim",
        "slice036-child-check",
        "--producer",
        "owner",
        "--repository",
        ".",
        "--evidence",
        "governance/qualification/evidence.json",
        "--producers",
        "governance/producers.yaml",
        "--gate",
        "landing",
        "--gate-catalog",
        "governance/gates.yaml",
        "--suite-manifest",
        "governance/suite_manifest.json",
        "--store",
        str(tmp_path / "store"),
        "--runtime-input-path",
        "governance/qualification/inputs/SLICE-036-child-A/a-before-b/attempt-0",
        "--toolchain-root",
        "governance/qualification/worker",
        "--result-dir",
        str(result_dir),
        "--",
        "/ranex/toolchain/bin/slice036-worker",
        "--task",
        key=v2_repository.key,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "CONFINED  strict-local command" in completed.stdout
    report = _report(result_dir)
    assert report["outcome"] == "confined"
    _assert_retained_logs(result_dir, report)


def test_v3_real_workflow_records_runtime_result_binding_when_published(
    tmp_path: Path, v3_repository: GovernedRepository
) -> None:
    """The wrapper runs the committed v3 runtime closure with real signing."""
    result_dir = tmp_path / "v3"
    completed = _module(
        v3_repository.path,
        "ranex.cli.main",
        "host",
        "strict-local",
        "--version",
        "v3",
        "--claim",
        "dynamic-runtime-qualified",
        "--producer",
        "slice072-owner",
        "--repository",
        ".",
        "--evidence",
        ".local/ranex-e2e/v3-evidence.json",
        "--runtime-input-path",
        "tests/e2e/fixtures/slice072-input",
        "--runtime-closure-root",
        "tests/e2e/fixtures/slice072-runtime",
        "--result-dir",
        str(result_dir),
        "--",
        "/ranex/runtime/bin/python3.12",
        "/ranex/runtime/data/worker.py",
        key=v3_repository.key,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "CONFINED  strict-local command" in completed.stdout
    report = _report(result_dir)
    assert report["outcome"] == "confined"
    assert report["result_binding"] is None
    _assert_retained_logs(result_dir, report)


def test_real_missing_session_bus_is_named_and_retained(tmp_path: Path) -> None:
    """The preflight path is a real CLI process with only PATH and HOME."""
    result_dir = tmp_path / "no-session-bus"
    completed = _cli(
        [
            "host",
            "strict-local",
            "--version",
            "v1",
            "--claim",
            "prereq-probe",
            "--producer",
            "owner",
            "--result-dir",
            str(result_dir),
            "--",
            "/bin/true",
        ],
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(tmp_path / "home")},
    )
    assert completed.returncode == 1, completed.stdout + completed.stderr
    assert "user-session-bus" in completed.stdout + completed.stderr
    assert "HINT" in completed.stdout + completed.stderr
    report = _report(result_dir)
    assert report["outcome"] == "prereq-failed"
    _assert_retained_logs(result_dir, report)


def test_named_host_drift_refuses_from_a_different_delegated_scope(
    tmp_path: Path, drift_repository: GovernedRepository
) -> None:
    """A qualification from scope A is fail-closed when used from scope B."""
    provisioning = (
        ("launcher-build", "--manifest", "governance/confinement/native-launcher-build-v1.json", "--source", "native/ranex-worker-launcher/launcher.c", "--output", ".local/ranex/build/strict-local-v1/ranex-worker-launcher"),
        ("launcher-install", "--manifest", "governance/confinement/native-launcher-build-v1.json", "--artifact", ".local/ranex/build/strict-local-v1/ranex-worker-launcher", "--destination", ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"),
        ("qualify", "--profile", "governance/confinement/strict-local-host-v1.json", "--artifact", ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher", "--manifest", "governance/confinement/native-launcher-build-v1.json", "--report", ".local/ranex/qualification/strict-local-v1.json"),
    )
    for arguments in provisioning:
        completed = _module(drift_repository.path, "ranex.cli.host_confinement", *arguments)
        assert completed.returncode == 0, completed.stdout + completed.stderr

    evidence = ".local/ranex-e2e/drift-evidence.json"
    run_argv = [
        sys.executable,
        "-m",
        "ranex.cli.main",
        "run",
        "--claim",
        "dynamic-runtime-qualified",
        "--producer",
        "slice072-owner",
        "--repository",
        ".",
        "--evidence",
        evidence,
        "--confinement",
        "strict-local",
        "--runtime-input-path",
        "tests/e2e/fixtures/slice072-input",
        "--runtime-closure-root",
        "tests/e2e/fixtures/slice072-runtime",
        "--",
        "/ranex/runtime/bin/python3.12",
        "/ranex/runtime/data/worker.py",
    ]
    command = f"cd {shlex.quote(str(drift_repository.path))} && exec {shlex.join(run_argv)}"
    nested = subprocess.run(
        [
            "/usr/bin/systemd-run",
            "--user",
            "--scope",
            "--quiet",
            "--property=Delegate=yes",
            f"--setenv=PYTHONPATH={drift_repository.path / 'src'}",
            f"--setenv=RANEX_SIGNING_KEY={drift_repository.key}",
            f"--setenv=PATH={os.environ['PATH']}",
            f"--setenv=HOME={os.environ['HOME']}",
            "--",
            "/bin/sh",
            "-c",
            command,
        ],
        cwd=drift_repository.path,
        env=_environment(drift_repository.key),
        capture_output=True,
        text=True,
        check=False,
        timeout=240,
    )
    assert nested.returncode != 0
    assert "E-C18-HOST-DRIFT" in nested.stdout + nested.stderr
    assert not (drift_repository.path / evidence).exists()
