"""SLICE-007 §17.5 — every gear turns, but approval remains human.

This single mesh sends a dispatched task through the bridged worker loop, its
commit emission, signed evidence, and kernel judgement.  Nothing is operated
by hand between gears: the worker commits the dirty worktree and the kernel
records only ``CANDIDATE``.  A PASS stamp belongs to an out-of-band human.

Written red-first: the fork bridge's deterministic ``ranex-noop/noop`` model
does not exist yet, so this test currently stops at the worker-loop boundary.
The dispatch and dirty-worktree setup before that boundary are intentionally
asserted to make that failure meaningful.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_sha256, command_digest
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

BOUND_COMMAND = ["uv", "run", "pytest", "-q"]
GATES = """\
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]
"""


@dataclass(frozen=True)
class Signing:
    public: str
    path: Path


def clean_env() -> dict[str, str]:
    return {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
    }


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=True,
        env=clean_env(),
    )
    return result.stdout.strip()


def commit_all(repository: Path, message: str) -> None:
    git(repository, "add", "-A")
    git(repository, "commit", "-q", "-m", message)


def subject_digest(repository: Path, ref: str = "HEAD") -> str:
    tree = git(repository, "rev-parse", f"{ref}^{{tree}}")
    return "sha256:" + canonical_sha256({"tree": tree})


def evidence_record(signing: Signing, digest: str) -> dict[str, object]:
    from ranex.foundation.signing import sign_evidence

    body: dict[str, object] = {
        "claim_id": "tests-executed",
        "subject_digest": digest,
        "producer_id": "worker",
        "command": " ".join(BOUND_COMMAND),
        "command_digest": command_digest(BOUND_COMMAND),
        "executable_path": "/usr/bin/uv",
        "exit_code": 0,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    return {**body, "signature": sign_evidence(body, signing.path.read_text().strip())}


def harness_dir() -> Path:
    default = Path(__file__).resolve().parents[2].parent / "ranex-harness"
    return Path(os.environ.get("RANEX_HARNESS_DIR", default))


@pytest.fixture(scope="module")
def harness() -> Path:
    tree = harness_dir()
    if not (tree / "package.json").is_file():
        pytest.skip(f"harness fork not present at {tree} (set RANEX_HARNESS_DIR)")
    return tree


@pytest.fixture(scope="module")
def bun() -> Path:
    executable = Path.home() / ".bun" / "bin" / "bun"
    if not executable.is_file():
        pytest.skip("bun toolchain not installed at ~/.bun/bin/bun")
    return executable


@pytest.fixture()
def signing(tmp_path: Path) -> Signing:
    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    path = tmp_path / "worker.key"
    path.write_text(private + "\n", encoding="utf-8")
    path.chmod(0o600)
    return Signing(public=public, path=path)


@pytest.fixture()
def target(tmp_path: Path, signing: Signing, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A committed trust root; its signing key stays outside this repository."""

    monkeypatch.setenv("RANEX_SIGNING_KEY", str(signing.path))
    repository = tmp_path / "target"
    subprocess.run(["git", "init", "-q", str(repository)], check=True, env=clean_env())
    git(repository, "config", "user.email", "mesh-test@example.invalid")
    git(repository, "config", "user.name", "Mesh Test")
    (repository / "app.txt").write_text("committed work\n", encoding="utf-8")
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    (repository / "producers.yaml").write_text(
        f"producers:\n  worker: {signing.public}\n", encoding="utf-8"
    )
    commit_all(repository, "initial governed work")
    return repository


def invoke_task(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", "-m", "ranex.cli.main", *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(),
    )


def bridged_environment(bun: Path, task_id: str, emit: Path) -> dict[str, str]:
    """The fork gets only its runtime path, HOME, and explicit bridge values."""

    return {
        "PATH": f"{bun.parent}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "HOME": str(Path.home()),
        "RANEX_TASK_ID": task_id,
        "RANEX_EMIT": str(emit),
    }


def test_gear_mesh_ends_in_candidate_without_auto_approval(
    target: Path, signing: Signing, harness: Path, bun: Path, tmp_path: Path
) -> None:
    """Dispatch → bridged commit → emission → evidence → candidate journal."""

    task_id = "T-MESH"
    worktree, journal, emit = tmp_path / "worktree", tmp_path / "journal.sqlite3", tmp_path / "emit.jsonl"
    dispatch = invoke_task(
        "task", "dispatch", "--task-id", task_id, "--target", str(target),
        "--worktree", str(worktree), "--journal", str(journal),
    )
    assert dispatch.returncode == 0, dispatch.stderr
    base_commit = git(target, "rev-parse", "HEAD")
    assert Journal(journal).verify() is True

    worked_file = "worker-output.txt"
    (worktree / worked_file).write_text("mesh work, not yet committed\n", encoding="utf-8")
    assert git(worktree, "status", "--porcelain") == f"?? {worked_file}"

    worker = subprocess.run(
        [
            str(bun), "run", "--cwd", "packages/ranex", "src/index.ts",
            "run", "--dir", str(worktree), "--model", "ranex-noop/noop",
            "Commit the existing worktree change.",
        ],
        cwd=harness,
        capture_output=True,
        text=True,
        timeout=180,
        env=bridged_environment(bun, task_id, emit),
        check=False,
    )
    assert worker.returncode == 0, worker.stderr

    (emission_line,) = emit.read_text(encoding="utf-8").splitlines()
    emission = json.loads(emission_line)
    emitted_commit = emission["commit"]
    assert emission["task_id"] == task_id
    assert emission["worktree"] == str(worktree.resolve())
    assert re.fullmatch(r"[0-9a-f]{40}", emitted_commit)
    assert emitted_commit == git(worktree, "rev-parse", "HEAD")
    assert emitted_commit != base_commit
    assert git(worktree, "show", f"HEAD:{worked_file}") == "mesh work, not yet committed"

    (worktree / "evidence.json").write_text(
        json.dumps([evidence_record(signing, subject_digest(worktree, emitted_commit))]) + "\n",
        encoding="utf-8",
    )
    judgement = invoke_task(
        "task", "judge", "--task-id", task_id,
        "--emitted-worktree", emission["worktree"], "--emitted-commit", emitted_commit,
        "--gate", "landing", "--gate-catalog", "gates.yaml", "--evidence", "evidence.json",
        "--producers", "producers.yaml", "--journal", str(journal),
    )
    assert judgement.returncode == 0, judgement.stderr

    records = Journal(journal).entries()
    assert Journal(journal).verify() is True
    assert len(records) == 2
    assert records[0]["type"] == "task-dispatch"
    candidate = records[1]
    assert candidate["type"] == "task-candidate"
    assert candidate["verdict"] == "CANDIDATE"
    assert candidate["task_id"] == task_id and candidate["gate_id"] == "landing"
    assert candidate["subject_digest"] == subject_digest(worktree, emitted_commit)
    assert candidate["missing_claims"] == [] and "approver_id" not in candidate
    assert not any(record.get("verdict") == "PASS" for record in records)
