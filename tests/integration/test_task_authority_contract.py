from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import main, subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskCandidate

CATALOG = (
    b"gates:\n"
    b"  - gate_id: landing\n"
    b"    rule_id: TESTS_EXECUTED\n"
    b"    blocking: true\n"
    b"    required_claims:\n"
    b"      - claim_id: tests-executed\n"
    b"        command: [pytest, -q]\n"
)


def git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def invoke(repository: Path, arguments: list[str]) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repository)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repository.resolve()
        )
        return main(arguments)


@dataclass(frozen=True)
class Scenario:
    repository: Path
    worktrees: Path
    worker_private: str
    approver_private: str

    @property
    def journal(self) -> Path:
        return self.repository / "governance" / "journal.sqlite3"

    @classmethod
    def create(cls, root: Path) -> Scenario:
        repository = root / "governed"
        worktrees = root / "worktrees"
        worktrees.mkdir()
        git(root, "init", "-q", str(repository))
        git(repository, "config", "user.email", "test@example.com")
        git(repository, "config", "user.name", "Test")
        worker_private, worker_public = generate_keypair()
        approver_private, approver_public = generate_keypair()
        governance = repository / "governance"
        governance.mkdir()
        (governance / "gates.yaml").write_bytes(CATALOG)
        (governance / "producers.yaml").write_text(
            f"producers:\n  worker: {worker_public}\n  owner: {approver_public}\n",
            encoding="utf-8",
        )
        (repository / ".gitignore").write_text(
            "governance/evidence.json\ngovernance/journal.sqlite3\napproval.json\n",
            encoding="utf-8",
        )
        (repository / "base.txt").write_text("base\n", encoding="utf-8")
        git(repository, "add", "-A")
        git(repository, "commit", "-q", "-m", "base")
        git(repository, "branch", "-M", "main")
        return cls(repository, worktrees, worker_private, approver_private)


def dispatch(scenario: Scenario, task_id: str, *, journal: Path | None = None) -> Path:
    worktree = scenario.worktrees / task_id
    arguments = [
        "task",
        "dispatch",
        "--task-id",
        task_id,
        "--target",
        str(scenario.repository),
        "--worktree",
        str(worktree),
    ]
    if journal is not None:
        arguments.extend(("--journal", str(journal)))
    assert invoke(scenario.repository, arguments) == 0
    return worktree


def make_candidate(scenario: Scenario, worktree: Path, task_id: str) -> tuple[str, str]:
    candidate_path = worktree / f"{task_id}.txt"
    candidate_path.write_text(f"candidate {task_id}\n", encoding="utf-8")
    git(worktree, "add", candidate_path.name)
    git(worktree, "commit", "-q", "-m", task_id)
    candidate = git(worktree, "rev-parse", "HEAD")
    subject = subject_digest_for(scenario.repository, candidate)
    body: dict[str, object] = {
        "claim_id": "tests-executed",
        "command": "pytest -q",
        "command_digest": command_digest(["pytest", "-q"]),
        "executable_path": "/usr/bin/pytest",
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": subject,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    (worktree / "governance" / "evidence.json").write_text(
        json.dumps([{**body, "signature": sign_evidence(body, scenario.worker_private)}]),
        encoding="utf-8",
    )
    return candidate, subject


def judge(scenario: Scenario, task_id: str, worktree: Path, candidate: str, *, journal: Path | None = None) -> int:
    arguments = [
        "task",
        "judge",
        "--task-id",
        task_id,
        "--emitted-worktree",
        str(worktree),
        "--emitted-commit",
        candidate,
        "--gate",
        "landing",
        "--gate-catalog",
        "governance/gates.yaml",
        "--producers",
        "governance/producers.yaml",
    ]
    if journal is not None:
        arguments.extend(("--journal", str(journal)))
    return invoke(scenario.repository, arguments)


def approval(scenario: Scenario, task_id: str, candidate: str, subject: str, journal: Path) -> Path:
    candidate_record = next(
        record
        for record in reversed(Journal(journal).entries())
        if record.get("type") == "task-candidate" and record.get("task_id") == task_id
    )
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": git(scenario.repository, "rev-parse", "refs/heads/main"),
        "catalog_digest": catalog_digest_for(CATALOG),
        "candidate_row_hash": candidate_row_hash(candidate_record),
        "approver_id": "owner",
    }
    path = scenario.repository / "approval.json"
    path.write_text(
        json.dumps({**envelope, "signature": sign_approval(envelope, scenario.approver_private)}),
        encoding="utf-8",
    )
    return path


def merge_arguments(task_id: str, candidate: str, signed_approval: Path) -> list[str]:
    return [
        "task",
        "merge",
        "--task-id",
        task_id,
        "--target-ref",
        "refs/heads/main",
        "--candidate",
        candidate,
        "--approval",
        str(signed_approval),
    ]


def test_dispatch_default_journal_is_target_owned(tmp_path: Path) -> None:
    scenario = Scenario.create(tmp_path)

    worktree = dispatch(scenario, "task-dispatch")

    assert scenario.journal.is_file()
    assert Journal(scenario.journal).entries() == [
        {
            "type": "task-dispatch",
            "task_id": "task-dispatch",
            "worktree": str(worktree.resolve()),
            "base_commit": git(scenario.repository, "rev-parse", "HEAD"),
        }
    ]


def test_judge_defaults_to_target_journal_and_worktree_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = Scenario.create(tmp_path)
    worktree = dispatch(scenario, "task-judge")
    candidate, _ = make_candidate(scenario, worktree, "task-judge")

    assert judge(scenario, "task-judge", worktree, candidate) == 0

    assert "CANDIDATE  task=task-judge  gate=landing" in capsys.readouterr().out
    assert any(
        record.get("type") == "task-candidate" and record.get("task_id") == "task-judge"
        for record in Journal(scenario.journal).entries()
    )


def test_merge_default_evidence_comes_from_dispatched_worktree(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = Scenario.create(tmp_path)
    worktree = dispatch(scenario, "task-merge")
    candidate, subject = make_candidate(scenario, worktree, "task-merge")
    assert judge(scenario, "task-merge", worktree, candidate) == 0
    signed_approval = approval(scenario, "task-merge", candidate, subject, scenario.journal)

    assert invoke(scenario.repository, merge_arguments("task-merge", candidate, signed_approval)) == 0

    assert f"PUBLISHED  task=task-merge  candidate={candidate}" in capsys.readouterr().out
    assert git(scenario.repository, "rev-parse", "refs/heads/main") == candidate


def test_merge_refuses_deleted_worktree_evidence_as_sad_path_5(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = Scenario.create(tmp_path)
    worktree = dispatch(scenario, "task-missing-evidence")
    candidate, subject = make_candidate(scenario, worktree, "task-missing-evidence")
    assert judge(scenario, "task-missing-evidence", worktree, candidate) == 0
    signed_approval = approval(
        scenario, "task-missing-evidence", candidate, subject, scenario.journal
    )

    (worktree / "governance" / "evidence.json").unlink()

    assert (
        invoke(
            scenario.repository,
            merge_arguments("task-missing-evidence", candidate, signed_approval),
        )
        == 1
    )
    assert "sad-path-5 satisfying-evidence-missing" in capsys.readouterr().err


def test_merge_explicit_journal_and_evidence_override_defaults(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = Scenario.create(tmp_path)
    worktree = dispatch(scenario, "task-overrides")
    candidate, subject = make_candidate(scenario, worktree, "task-overrides")
    assert judge(scenario, "task-overrides", worktree, candidate) == 0
    signed_approval = approval(scenario, "task-overrides", candidate, subject, scenario.journal)
    second_journal = tmp_path / "second.sqlite3"
    Journal(second_journal).append(TaskCandidate("other-task", "landing", subject, ()))

    assert invoke(
        scenario.repository,
        merge_arguments("task-overrides", candidate, signed_approval)
        + ["--journal", str(second_journal)],
    ) == 1
    assert "sad-path-11 candidate-row-missing" in capsys.readouterr().err

    empty_evidence = scenario.repository / "governance" / "empty-evidence.json"
    empty_evidence.write_text("[]\n", encoding="utf-8")
    assert invoke(
        scenario.repository,
        merge_arguments("task-overrides", candidate, signed_approval)
        + ["--evidence", "governance/empty-evidence.json"],
    ) == 1
    assert "sad-path-5 satisfying-evidence-missing" in capsys.readouterr().err


def test_merge_legacy_candidate_without_dispatch_uses_governed_evidence(tmp_path: Path) -> None:
    scenario = Scenario.create(tmp_path)
    tip = git(scenario.repository, "rev-parse", "refs/heads/main")
    (scenario.repository / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    git(scenario.repository, "add", "candidate.txt")
    git(scenario.repository, "commit", "-q", "-m", "candidate")
    candidate = git(scenario.repository, "rev-parse", "HEAD")
    git(scenario.repository, "update-ref", "refs/heads/main", tip, candidate)
    subject = subject_digest_for(scenario.repository, candidate)
    body: dict[str, object] = {
        "claim_id": "tests-executed",
        "command": "pytest -q",
        "command_digest": command_digest(["pytest", "-q"]),
        "executable_path": "/usr/bin/pytest",
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": subject,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    (scenario.repository / "governance" / "evidence.json").write_text(
        json.dumps([{**body, "signature": sign_evidence(body, scenario.worker_private)}]),
        encoding="utf-8",
    )
    Journal(scenario.journal).append(TaskCandidate("legacy", "landing", subject, ()))
    signed_approval = approval(scenario, "legacy", candidate, subject, scenario.journal)

    assert invoke(scenario.repository, merge_arguments("legacy", candidate, signed_approval)) == 0
    assert git(scenario.repository, "rev-parse", "refs/heads/main") == candidate


def test_judge_explicit_journal_remains_supported(tmp_path: Path) -> None:
    scenario = Scenario.create(tmp_path)
    explicit_journal = tmp_path / "explicit.sqlite3"
    worktree = dispatch(scenario, "task-explicit", journal=explicit_journal)
    candidate, _ = make_candidate(scenario, worktree, "task-explicit")

    assert judge(scenario, "task-explicit", worktree, candidate, journal=explicit_journal) == 0
    assert any(
        record.get("type") == "task-candidate" and record.get("task_id") == "task-explicit"
        for record in Journal(explicit_journal).entries()
    )
