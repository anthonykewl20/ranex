"""SLICE-007 — the kernel materialises committed work, never an emission.

The harness may name any worktree and any commit, but neither is authority.
`task judge` must trust only the latest dispatch record it appended and the
HEAD it reads from that recorded worktree.  A candidate is consequently a
durable judgement, not a PASS or an approval.

Written red-first: until the ``task`` command exists, every test stops at the
CLI boundary with argparse's unknown-subcommand error rather than accidentally
passing from fixture state alone.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_sha256, command_digest
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

EXIT_FAIL = 1
EXIT_PASS = 0
EXIT_USAGE = 2
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
    """A small process environment; notably, no model credentials are copied."""

    environment = {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
    }
    return environment


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
    private_key = signing.path.read_text(encoding="utf-8").strip()
    return {**body, "signature": sign_evidence(body, private_key)}


@pytest.fixture()
def signing(tmp_path: Path) -> Signing:
    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    path = tmp_path / "worker.key"
    path.write_text(private + "\n", encoding="utf-8")
    path.chmod(0o600)
    assert path.stat().st_mode & 0o777 == 0o600
    return Signing(public=public, path=path)


@pytest.fixture()
def target(tmp_path: Path, signing: Signing) -> Path:
    repository = tmp_path / "target"
    subprocess.run(["git", "init", "-q", str(repository)], check=True, env=clean_env())
    git(repository, "config", "user.email", "kernel-test@example.invalid")
    git(repository, "config", "user.name", "Kernel Test")
    (repository / "app.txt").write_text("committed work\n", encoding="utf-8")
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    (repository / "producers.yaml").write_text(
        f"producers:\n  worker: {signing.public}\n", encoding="utf-8"
    )
    commit_all(repository, "initial governed work")
    return repository


def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", "-m", "ranex.cli.main", *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(),
    )


def require_task_command(result: subprocess.CompletedProcess[str]) -> None:
    """Make usage-refusal tests red until argparse knows the task group too."""

    assert "invalid choice: 'task'" not in result.stderr, result.stderr


def dispatch(target: Path, worktree: Path, journal: Path, task_id: str = "T-7") -> subprocess.CompletedProcess[str]:
    result = invoke(
        "task", "dispatch", "--task-id", task_id, "--target", str(target),
        "--worktree", str(worktree), "--journal", str(journal),
    )
    require_task_command(result)
    return result


def judge(worktree: Path, journal: Path, *, task_id: str = "T-7", emitted_worktree: Path | None = None,
          emitted_commit: str | None = None) -> subprocess.CompletedProcess[str]:
    result = invoke(
        "task", "judge", "--task-id", task_id,
        "--emitted-worktree", str(emitted_worktree or worktree),
        "--emitted-commit", emitted_commit or git(worktree, "rev-parse", "HEAD"),
        "--gate", "landing", "--gate-catalog", "gates.yaml",
        "--evidence", "evidence.json", "--producers", "producers.yaml",
        "--journal", str(journal),
    )
    require_task_command(result)
    return result


def dispatched(target: Path, tmp_path: Path) -> tuple[Path, Path]:
    worktree, journal = tmp_path / "worktree", tmp_path / "journal.sqlite3"
    result = dispatch(target, worktree, journal)
    assert result.returncode == EXIT_PASS, result.stderr
    return worktree, journal


def write_satisfying_evidence(worktree: Path, signing: Signing) -> None:
    """Write signed evidence for the materialised committed subject.

    Evidence is an exempted working-tree artefact, never part of the judged
    subject — committing it would change the subject it attests.
    """

    (worktree / "evidence.json").write_text(
        json.dumps([evidence_record(signing, subject_digest(worktree))]) + "\n",
        encoding="utf-8",
    )


def test_dispatch_materialises_head_and_appends_a_chained_record(target: Path, tmp_path: Path) -> None:
    worktree, journal = dispatched(target, tmp_path)
    (record,) = Journal(journal).entries()
    assert worktree.is_dir()
    assert record == {
        "type": "task-dispatch", "task_id": "T-7", "worktree": str(worktree.resolve()),
        "base_commit": git(target, "rev-parse", "HEAD"),
    }
    assert Journal(journal).verify() is True


def test_dispatch_refuses_a_blank_task_id(target: Path, tmp_path: Path) -> None:
    worktree, journal = tmp_path / "worktree", tmp_path / "journal.sqlite3"
    result = dispatch(target, worktree, journal, task_id=" ")
    assert result.returncode == EXIT_USAGE
    assert not worktree.exists() and not journal.exists()


def test_dispatch_refuses_an_existing_worktree(target: Path, tmp_path: Path) -> None:
    worktree, journal = tmp_path / "worktree", tmp_path / "journal.sqlite3"
    worktree.mkdir()
    result = dispatch(target, worktree, journal)
    assert result.returncode == EXIT_USAGE
    assert Journal(journal).entries() == []


def test_dispatch_refuses_a_non_git_target(tmp_path: Path) -> None:
    target, worktree, journal = tmp_path / "plain", tmp_path / "worktree", tmp_path / "j.sqlite3"
    target.mkdir()
    result = dispatch(target, worktree, journal)
    assert result.returncode == EXIT_USAGE
    assert not worktree.exists() and not journal.exists()


def test_judge_refuses_when_no_dispatch_exists(target: Path, tmp_path: Path) -> None:
    worktree, journal = tmp_path / "worktree", tmp_path / "journal.sqlite3"
    result = judge(target, journal, emitted_worktree=worktree, emitted_commit=git(target, "rev-parse", "HEAD"))
    assert result.returncode == EXIT_FAIL
    assert "T-7" in result.stderr and not journal.exists()


def test_judge_refuses_a_forged_worktree_reference(target: Path, tmp_path: Path) -> None:
    worktree, journal = dispatched(target, tmp_path)
    forged = tmp_path / "forged"
    forged.mkdir()
    result = judge(worktree, journal, emitted_worktree=forged)
    assert result.returncode == EXIT_FAIL
    assert Journal(journal).entries() == [{"type": "task-dispatch", "task_id": "T-7", "worktree": str(worktree.resolve()), "base_commit": git(target, "rev-parse", "HEAD")}]


def test_judge_refuses_a_forged_commit_reference(target: Path, tmp_path: Path) -> None:
    worktree, journal = dispatched(target, tmp_path)
    result = judge(worktree, journal, emitted_commit="0" * 40)
    assert result.returncode == EXIT_FAIL
    assert len(Journal(journal).entries()) == 1


def test_judge_refuses_a_deleted_dispatched_worktree(target: Path, tmp_path: Path) -> None:
    worktree, journal = dispatched(target, tmp_path)
    shutil.rmtree(worktree)
    result = judge(worktree, journal, emitted_commit="0" * 40)
    assert result.returncode == EXIT_FAIL
    assert "traceback" not in result.stderr.lower() and len(Journal(journal).entries()) == 1


def test_judge_records_a_candidate_without_pass_or_approval(target: Path, signing: Signing, tmp_path: Path) -> None:
    worktree, journal = dispatched(target, tmp_path)
    write_satisfying_evidence(worktree, signing)
    result = judge(worktree, journal)
    records = Journal(journal).entries()
    candidate = records[-1]
    assert result.returncode == EXIT_PASS, result.stderr
    assert candidate["type"] == "task-candidate" and candidate["verdict"] == "CANDIDATE"
    assert candidate["task_id"] == "T-7" and candidate["gate_id"] == "landing"
    assert candidate["subject_digest"] == subject_digest(worktree)
    assert candidate["missing_claims"] == [] and "approver_id" not in candidate
    assert not any(record.get("verdict") == "PASS" for record in records)
    assert Journal(journal).verify() is True


def test_judge_persists_an_unsatisfied_candidate(target: Path, tmp_path: Path) -> None:
    worktree, journal = dispatched(target, tmp_path)
    result = judge(worktree, journal)
    candidate = Journal(journal).entries()[-1]
    assert result.returncode == EXIT_FAIL
    assert candidate["type"] == "task-candidate" and candidate["verdict"] == "CANDIDATE"
    assert candidate["missing_claims"] == ["tests-executed"]
    assert Journal(journal).verify() is True
