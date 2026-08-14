from __future__ import annotations

import json
import sqlite3
import subprocess
import zlib
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import main, subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskCandidate, TaskMergeIntent


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def invoke(repo: Path, argv: list[str]) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        return main(argv)


def prepare(repo: Path, *, orphan: bool = False) -> tuple[str, str, Path, dict[str, object]]:
    git(repo.parent, "init", "-q", str(repo))
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test")
    worker_private, worker_public = generate_keypair()
    approver_private, approver_public = generate_keypair()
    governance = repo / "governance"
    governance.mkdir()
    catalog = (
        b"gates:\n"
        b"  - gate_id: landing\n"
        b"    rule_id: TESTS_EXECUTED\n"
        b"    blocking: true\n"
        b"    required_claims:\n"
        b"      - claim_id: tests-executed\n"
        b"        command: [pytest, -q]\n"
    )
    (governance / "gates.yaml").write_bytes(catalog)
    (governance / "producers.yaml").write_text(
        f"producers:\n  worker: {worker_public}\n  owner: {approver_public}\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text("governance/evidence.json\ngovernance/journal.sqlite3\n", encoding="utf-8")
    (repo / "base.txt").write_text("base\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    git(repo, "branch", "-M", "main")
    tip = git(repo, "rev-parse", "refs/heads/main")
    (repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    git(repo, "add", "candidate.txt")
    git(repo, "commit", "-q", "-m", "candidate")
    linear_candidate = git(repo, "rev-parse", "HEAD")
    candidate = linear_candidate
    if orphan:
        candidate = git(repo, "commit-tree", git(repo, "rev-parse", f"{linear_candidate}^{{tree}}"), "-m", "orphan")
    git(repo, "update-ref", "refs/heads/main", tip, linear_candidate)
    subject = subject_digest_for(repo, candidate)
    evidence_body = {
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
    (governance / "evidence.json").write_text(
        json.dumps([{**evidence_body, "signature": sign_evidence(evidence_body, worker_private)}]),
        encoding="utf-8",
    )
    journal = Journal(governance / "journal.sqlite3")
    candidate_record = TaskCandidate("task-1", "landing", subject, ()).as_record()
    journal.append(TaskCandidate("task-1", "landing", subject, ()))
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": tip,
        "catalog_digest": catalog_digest_for(catalog),
        "candidate_row_hash": candidate_row_hash(candidate_record),
        "approver_id": "owner",
    }
    approval = repo / "approval.json"
    approval.write_text(
        json.dumps({**envelope, "signature": sign_approval(envelope, approver_private)}),
        encoding="utf-8",
    )
    return tip, candidate, approval, candidate_record


def merge_args(candidate: str, approval: Path) -> list[str]:
    return [
        "task", "merge",
        "--task-id", "task-1",
        "--target-ref", "refs/heads/main",
        "--candidate", candidate,
        "--approval", str(approval),
    ]


def test_task_merge_publishes_a_fast_forward_and_journals_order(tmp_path: Path) -> None:
    repo = tmp_path / "governed"
    _, candidate, approval, candidate_record = prepare(repo)

    assert invoke(repo, merge_args(candidate, approval)) == 0
    assert git(repo, "rev-parse", "refs/heads/main") == candidate
    journal = Journal(repo / "governance" / "journal.sqlite3")
    entries = journal.entries()
    assert entries[0] == candidate_record
    merge_entries = entries[1:]
    assert [entry["type"] for entry in merge_entries] == [
        "task-merge-intent",
        "task-merge-check",
        "task-merge-check",
        "task-merge-check",
        "task-merge-check",
        "task-merge-check",
        "task-merge-outcome",
    ]
    assert [entry["check"] for entry in merge_entries[1:-1]] == [
        "policy_approval", "ancestry", "merge_range", "digest_evidence", "cas"
    ]
    assert all(entry["status"] == "passed" for entry in merge_entries[1:-1])
    assert merge_entries[-1]["outcome"] == "PUBLISHED"
    assert journal.verify() is True


def test_task_merge_refuses_unrelated_history_at_ancestry(tmp_path: Path) -> None:
    repo = tmp_path / "governed"
    tip, candidate, approval, _ = prepare(repo, orphan=True)

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert git(repo, "rev-parse", "refs/heads/main") == tip
    entries = Journal(repo / "governance" / "journal.sqlite3").entries()
    checks = [entry for entry in entries if entry.get("type") == "task-merge-check"]
    assert [(entry["check"], entry["status"]) for entry in checks] == [
        ("policy_approval", "passed"),
        ("ancestry", "refused"),
    ]
    assert entries[-1]["outcome"] == "REFUSED"



def test_task_merge_refuses_when_journal_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "governed"
    _, candidate, approval, _ = prepare(repo)
    journal_path = repo / "governance" / "journal.sqlite3"
    journal_path.unlink()

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert f"task journal does not exist at {journal_path}" in capsys.readouterr().err


def test_task_merge_refuses_tampered_journal(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "governed"
    _, candidate, approval, _ = prepare(repo)
    journal_path = repo / "governance" / "journal.sqlite3"
    with sqlite3.connect(journal_path) as connection:
        connection.execute("DROP TRIGGER evaluations_no_update")
        connection.execute("UPDATE evaluations SET link = ? WHERE seq = 1", ("tampered",))

    assert Journal(journal_path).verify() is False
    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert "journal is invalid; refusing task merge" in capsys.readouterr().err


def test_task_merge_refuses_non_object_approval(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "governed"
    _, candidate, approval, _ = prepare(repo)
    approval.write_text("[]", encoding="utf-8")

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert "approval file must contain a JSON object" in capsys.readouterr().err


def test_task_merge_refuses_non_string_approval_subject_and_tip(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "governed"
    _, candidate, approval, _ = prepare(repo)
    approval.write_text(json.dumps({"subject": 1, "tip": None}), encoding="utf-8")

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert "approval must carry string subject and tip fields" in capsys.readouterr().err


def test_task_merge_refuses_malformed_unmatched_intent(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "governed"
    _, candidate, approval, _ = prepare(repo)
    journal = Journal(repo / "governance" / "journal.sqlite3")
    journal.append(TaskMergeIntent("", candidate, "subject", "refs/heads/main", "tip"))

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert "invalid unmatched task merge intent" in capsys.readouterr().err


def test_task_merge_journals_refusal_when_candidate_catalog_blob_is_missing(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "governed"
    tip, _, approval, _ = prepare(repo)
    git(repo, "rm", "governance/gates.yaml")
    git(repo, "commit", "-q", "-m", "remove candidate catalog")
    candidate = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/heads/main", tip, candidate)

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert git(repo, "rev-parse", "refs/heads/main") == tip
    entries = Journal(repo / "governance" / "journal.sqlite3").entries()
    assert entries[-2]["detail"] == (
        f"policy_approval-error commit {candidate} carries no blob at governance/gates.yaml"
    )
    assert entries[-1]["outcome"] == "REFUSED"


def test_task_merge_journals_refusal_when_candidate_catalog_is_not_a_blob(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "governed"
    tip, _, approval, _ = prepare(repo)
    git(repo, "rm", "governance/gates.yaml")
    catalog = repo / "governance" / "gates.yaml"
    catalog.mkdir()
    (catalog / "entry").write_text("not a blob\n", encoding="utf-8")
    git(repo, "add", "governance/gates.yaml/entry")
    git(repo, "commit", "-q", "-m", "replace candidate catalog with tree")
    candidate = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/heads/main", tip, candidate)

    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert git(repo, "rev-parse", "refs/heads/main") == tip
    entries = Journal(repo / "governance" / "journal.sqlite3").entries()
    assert entries[-2]["detail"] == (
        f"policy_approval-error object at {candidate}:governance/gates.yaml is not a blob"
    )
    assert entries[-1]["outcome"] == "REFUSED"


def test_task_merge_journals_refusal_when_committed_catalog_blob_is_corrupt(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "governed"
    tip, _, approval, _ = prepare(repo)
    corrupt_oid = "a" * 40
    object_directory = repo / ".git" / "objects" / corrupt_oid[:2]
    object_directory.mkdir(exist_ok=True)
    compressed = zlib.compress(b"blob 5\0hello")
    (object_directory / corrupt_oid[2:]).write_bytes(compressed[:-1])
    git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        "100644",
        corrupt_oid,
        "governance/gates.yaml",
    )
    tree = git(repo, "write-tree")
    corrupt_tip = git(repo, "commit-tree", tree, "-p", tip, "-m", "corrupt catalog tip")
    candidate = git(repo, "commit-tree", tree, "-p", corrupt_tip, "-m", "candidate")
    git(repo, "update-ref", "refs/heads/main", corrupt_tip, tip)

    assert git(repo, "cat-file", "-t", corrupt_oid) == "blob"
    assert invoke(repo, merge_args(candidate, approval)) != 0
    assert git(repo, "rev-parse", "refs/heads/main") == corrupt_tip
    entries = Journal(repo / "governance" / "journal.sqlite3").entries()
    assert entries[-2]["detail"] == (
        "policy_approval-error cannot read committed blob at governance/gates.yaml"
    )
    assert entries[-1]["outcome"] == "REFUSED"
