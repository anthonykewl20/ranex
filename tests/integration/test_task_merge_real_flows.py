from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import main, subject_digest_for
from ranex.foundation.approval import APPROVAL_DOMAIN, candidate_row_hash, sign_approval
from ranex.foundation.canonical import (
    canonical_json_bytes,
    canonical_sha256,
    command_digest,
)
from ranex.foundation.signing import _decode, _encode, generate_keypair, sign_evidence
from ranex.foundation.suite_results import validate_suite_results
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

TARGET_MAIN = "refs/heads/main"
TARGET_RELEASE = "refs/heads/release"
CATALOG = (
    b"gates:\n"
    b"  - gate_id: landing\n"
    b"    rule_id: TESTS_EXECUTED\n"
    b"    blocking: true\n"
    b"    required_claims:\n"
    b"      - claim_id: tests-executed\n"
    b"        command: [pytest, -q]\n"
)


def git(repo: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout.strip()
    except subprocess.CalledProcessError as exc:
        # Surface stderr so a failing `git commit` in CI is diagnosable instead
        # of a bare exit code. add_note (3.11+) keeps the original exception type.
        exc.add_note(f"git {' '.join(args)} stderr: {exc.stderr}")
        raise


def add_and_commit(worktree: Path, name: str, message: str) -> None:
    """Stage `name` and commit it, with a loud safety-net retry.

    Used by the single-commit dispatch path (one blob). The CI-only
    "invalid object ... Error building trees" race — a just-written blob absent
    at commit time — is undiagnosed (not reproducible locally; not gc, which
    never fires at these object counts) and is eliminated for the multi-commit
    path by dispatch_judge's --allow-empty. This is the safety net for the
    single-commit case: on failure, `git add --renormalize -A` re-hashes and
    re-writes every tracked file regardless of git's stat cache (recreating any
    absent blob, including nested), a warning is emitted so a recovering run is
    visible, then retry. A commit that fails for an unrelated reason still
    surfaces via git()'s stderr note.
    """

    last: subprocess.CalledProcessError | None = None
    for _ in range(5):
        try:
            git(worktree, "add", name)
            git(worktree, "commit", "-q", "-m", message)
            return
        except subprocess.CalledProcessError as exc:
            last = exc
            warnings.warn(
                f"add_and_commit retrying in {worktree} after git failure; "
                f"re-hashing all tracked files: {exc}",
                stacklevel=2,
            )
            try:
                git(worktree, "add", "--renormalize", "-A")
            except subprocess.CalledProcessError:
                pass
            time.sleep(0.05)
    assert last is not None
    raise last


def invoke(repo: Path, argv: list[str]) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        return main(argv)


def candidate_record_bytes(journal: Path, task_id: str) -> bytes:
    with sqlite3.connect(journal) as connection:
        records = connection.execute(
            "SELECT record FROM evaluations ORDER BY seq ASC"
        ).fetchall()
    matches = [
        record.encode()
        for (record,) in records
        if (value := json.loads(record)).get("type") == "task-candidate"
        and value.get("task_id") == task_id
    ]
    assert matches
    return matches[-1]


@dataclass(frozen=True)
class RealRepository:
    repo: Path
    worktrees: Path
    journal: Path
    producer_private: str
    approver_private: str

    @classmethod
    def create(cls, root: Path) -> RealRepository:
        repo = root / "governed"
        worktrees = root / "worktrees"
        worktrees.mkdir()
        git(root, "init", "-q", str(repo))
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test")
        # Quiesce git during tests: fewer process forks, harmless hardening.
        # This is NOT the fix for the CI-only "invalid object ... Error building
        # trees" race — git's auto-gc/maintenance provably never fires at these
        # object counts (verified on git 2.43: ~600 loose objects vs the ~7000
        # gc.auto threshold). That race's real mitigation is in dispatch_judge:
        # the multi-commit huge-linear history is built with --allow-empty, so
        # no loose objects are churned at all. Worktrees share this config.
        git(repo, "config", "gc.auto", "0")
        git(repo, "config", "maintenance.auto", "false")
        producer_private, producer_public = generate_keypair()
        approver_private, approver_public = generate_keypair()
        governance = repo / "governance"
        governance.mkdir()
        (governance / "gates.yaml").write_bytes(CATALOG)
        (governance / "producers.yaml").write_text(
            f"producers:\n  worker: {producer_public}\n  approver: {approver_public}\n",
            encoding="utf-8",
        )
        (governance / "evidence.json").write_text("[]\n", encoding="utf-8")
        (repo / ".gitignore").write_text(
            "governance/journal.sqlite3\napproval-*.json\n", encoding="utf-8"
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base")
        git(repo, "branch", "-M", "main")
        return cls(
            repo,
            worktrees,
            governance / "journal.sqlite3",
            producer_private,
            approver_private,
        )


@dataclass(frozen=True)
class RealAttempt:
    task_id: str
    target_ref: str
    tip: str
    candidate: str
    subject: str
    approval: Path
    approval_document: dict[str, object]
    candidate_record: dict[str, object]
    candidate_record_bytes: bytes
    evidence_document: dict[str, object]

    def merge_args(self, *, approval: Path | None = None) -> list[str]:
        return [
            "task",
            "merge",
            "--task-id",
            self.task_id,
            "--target-ref",
            self.target_ref,
            "--candidate",
            self.candidate,
            "--approval",
            str(approval or self.approval),
        ]


def dispatch_judge(
    scenario: RealRepository,
    task_id: str,
    *,
    target_ref: str = TARGET_MAIN,
    same_tree: bool = False,
    evidence_document: dict[str, object] | None = None,
    evidence_factory: Callable[[str], list[dict[str, object]]] | None = None,
    commit_count: int = 1,
    judge_exit: int = 0,
    candidate_builder: Callable[[Path], None] | None = None,
    observed_tip: str | None = None,
) -> RealAttempt:
    tip = observed_tip or git(scenario.repo, "rev-parse", target_ref)
    worktree = scenario.worktrees / task_id
    assert invoke(
        scenario.repo,
        [
            "task",
            "dispatch",
            "--task-id",
            task_id,
            "--target",
            str(scenario.repo),
            "--worktree",
            str(worktree),
            "--journal",
            str(scenario.journal),
        ],
    ) == 0
    if candidate_builder is not None:
        candidate_builder(worktree)
    elif same_tree:
        git(worktree, "commit", "-q", "--allow-empty", "-m", task_id)
    elif commit_count > 1:
        # One real file gives the candidate a tree distinct from base — ranex
        # refuses a no-subject candidate (sad-path-4), so all-empty commits do
        # not work. The rest are empty: 200 commits total, but only ONE loose
        # blob is ever written. The CI-only "invalid object ... Error building
        # trees" race strikes a FRESHLY written blob — the one from the previous
        # iteration, gone inside a <10ms window (undiagnosed, not gc which
        # never fires at this volume, not reproducible locally in 25k+ commits).
        # Writing the only blob up front removes the per-iteration fresh-blob
        # surface; that blob is old and stable by the time later commits
        # reference it. add_and_commit's retry backstops that single commit.
        path = worktree / f"{task_id}-0.txt"
        path.write_text(f"candidate {task_id} 0\n", encoding="utf-8")
        add_and_commit(worktree, path.name, f"{task_id}-0")
        for number in range(1, commit_count):
            git(worktree, "commit", "-q", "--allow-empty", "-m", f"{task_id}-{number}")
    else:
        path = worktree / f"{task_id}.txt"
        path.write_text(f"candidate {task_id} 0\n", encoding="utf-8")
        add_and_commit(worktree, path.name, f"{task_id}-0")
    candidate = git(worktree, "rev-parse", "HEAD")
    subject = subject_digest_for(scenario.repo, candidate)
    if evidence_factory is not None:
        evidence_documents = evidence_factory(subject)
        evidence_document = evidence_documents[0]
    elif evidence_document is None:
        evidence_body: dict[str, object] = {
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
        evidence_document = {
            **evidence_body,
            "signature": sign_evidence(evidence_body, scenario.producer_private),
        }
        evidence_documents = [evidence_document]
    else:
        evidence_documents = [evidence_document]
    evidence_bytes = json.dumps(evidence_documents).encode()
    (worktree / "governance" / "evidence.json").write_bytes(evidence_bytes)
    (scenario.repo / "governance" / "evidence.json").write_bytes(evidence_bytes)
    assert invoke(
        scenario.repo,
        [
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
            "--evidence",
            "governance/evidence.json",
            "--producers",
            "governance/producers.yaml",
            "--journal",
            str(scenario.journal),
        ],
    ) == judge_exit
    candidates = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-candidate"
        and entry.get("task_id") == task_id
    ]
    assert candidates
    candidate_record = candidates[-1]
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": target_ref,
        "tip": tip,
        "catalog_digest": catalog_digest_for(CATALOG),
        "candidate_row_hash": candidate_row_hash(candidate_record),
        "approver_id": "approver",
    }
    approval_document = {
        **envelope,
        "signature": sign_approval(envelope, scenario.approver_private),
    }
    approval = scenario.repo / f"approval-{task_id}-{candidate[:12]}.json"
    approval.write_text(json.dumps(approval_document), encoding="utf-8")
    return RealAttempt(
        task_id,
        target_ref,
        tip,
        candidate,
        subject,
        approval,
        approval_document,
        candidate_record,
        candidate_record_bytes(scenario.journal, task_id),
        evidence_document,
    )


def run_concurrent_merges(
    repo: Path, attempts: tuple[RealAttempt, RealAttempt, RealAttempt]
) -> tuple[
    subprocess.CompletedProcess[str],
    subprocess.CompletedProcess[str],
    subprocess.CompletedProcess[str],
]:
    barrier = threading.Barrier(3)
    results: list[subprocess.CompletedProcess[str] | None] = [None, None, None]
    subprocess_source = repo / ".ranex-test-src"
    if not subprocess_source.exists():
        shutil.copytree(
            Path(__file__).resolve().parents[2] / "src" / "ranex",
            subprocess_source / "ranex",
        )
    environment = os.environ | {"PYTHONPATH": str(subprocess_source)}

    def run(index: int) -> None:
        barrier.wait()
        results[index] = subprocess.run(
            [sys.executable, "-m", "ranex.cli.main", *attempts[index].merge_args()],
            cwd=repo,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    threads = [threading.Thread(target=run, args=(index,)) for index in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads)
    assert results[0] is not None and results[1] is not None and results[2] is not None
    return results[0], results[1], results[2]


def signed_evidence_record(
    scenario: RealRepository, subject: str, executable_path: str
) -> dict[str, object]:
    body: dict[str, object] = {
        "claim_id": "tests-executed",
        "command": "pytest -q",
        "command_digest": command_digest(["pytest", "-q"]),
        "executable_path": executable_path,
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": subject,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    return {**body, "signature": sign_evidence(body, scenario.producer_private)}


@dataclass(frozen=True)
class RealRejudge:
    task_id: str
    tip: str
    candidate: str
    first_subject: str
    second_subject: str
    first_candidate_row: dict[str, object]
    second_candidate_row: dict[str, object]
    first_candidate_row_hash: str
    second_candidate_row_hash: str


def dispatch_rejudge(scenario: RealRepository, task_id: str) -> RealRejudge:
    tip = git(scenario.repo, "rev-parse", TARGET_MAIN)
    worktree = scenario.worktrees / task_id
    assert invoke(
        scenario.repo,
        [
            "task",
            "dispatch",
            "--task-id",
            task_id,
            "--target",
            str(scenario.repo),
            "--worktree",
            str(worktree),
            "--journal",
            str(scenario.journal),
        ],
    ) == 0

    def judge(candidate: str, subject: str) -> dict[str, object]:
        evidence = [signed_evidence_record(scenario, subject, "/usr/bin/pytest")]
        evidence_bytes = json.dumps(evidence).encode()
        (worktree / "governance" / "evidence.json").write_bytes(evidence_bytes)
        (scenario.repo / "governance" / "evidence.json").write_bytes(evidence_bytes)
        assert invoke(
            scenario.repo,
            [
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
                "--evidence",
                "governance/evidence.json",
                "--producers",
                "governance/producers.yaml",
                "--journal",
                str(scenario.journal),
            ],
        ) == 0
        rows = [
            entry
            for entry in Journal(scenario.journal).entries()
            if entry.get("type") == "task-candidate"
            and entry.get("task_id") == task_id
        ]
        return rows[-1]

    first_subject = subject_digest_for(scenario.repo, tip)
    first_candidate_row = judge(tip, first_subject)
    (worktree / f"{task_id}.txt").write_text(
        f"candidate {task_id}\n", encoding="utf-8"
    )
    git(worktree, "add", f"{task_id}.txt")
    git(worktree, "commit", "-q", "-m", f"{task_id}-rejudge")
    candidate = git(worktree, "rev-parse", "HEAD")
    second_subject = subject_digest_for(scenario.repo, candidate)
    second_candidate_row = judge(candidate, second_subject)
    candidate_rows = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-candidate"
        and entry.get("task_id") == task_id
    ]
    assert candidate_rows == [first_candidate_row, second_candidate_row]
    assert first_subject != second_subject
    assert candidate_row_hash(first_candidate_row) != candidate_row_hash(
        second_candidate_row
    )
    return RealRejudge(
        task_id,
        tip,
        candidate,
        first_subject,
        second_subject,
        first_candidate_row,
        second_candidate_row,
        candidate_row_hash(first_candidate_row),
        candidate_row_hash(second_candidate_row),
    )


def rejudge_approval(
    scenario: RealRepository,
    attempt: RealRejudge,
    *,
    candidate: str,
    subject: str,
    row_hash: str,
    name: str,
) -> Path:
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": TARGET_MAIN,
        "tip": attempt.tip,
        "catalog_digest": catalog_digest_for(CATALOG),
        "candidate_row_hash": row_hash,
        "approver_id": "approver",
    }
    approval = scenario.repo / f"approval-{name}.json"
    approval.write_text(
        json.dumps(
            {
                **envelope,
                "signature": sign_approval(envelope, scenario.approver_private),
            }
        ),
        encoding="utf-8",
    )
    return approval


def assert_candidate_row_hash_refusal(
    scenario: RealRepository, task_id: str
) -> None:
    entries = Journal(scenario.journal).entries()
    refused = [
        entry
        for entry in entries
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == task_id
        and entry.get("status") == "refused"
    ]
    assert refused[-1]["check"] == "policy_approval"
    assert refused[-1]["detail"] == "sad-path-12 candidate-row-hash-mismatch"
    outcomes = [
        entry
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("task_id") == task_id
    ]
    assert outcomes[-1]["outcome"] == "REFUSED"


def test_multiple_candidate_rows_same_task_id_binds_latest(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    attempt = dispatch_rejudge(scenario, "T1")
    latest_approval = rejudge_approval(
        scenario,
        attempt,
        candidate=attempt.candidate,
        subject=attempt.second_subject,
        row_hash=attempt.second_candidate_row_hash,
        name="latest",
    )

    assert invoke(
        scenario.repo,
        [
            "task",
            "merge",
            "--task-id",
            attempt.task_id,
            "--target-ref",
            TARGET_MAIN,
            "--candidate",
            attempt.candidate,
            "--approval",
            str(latest_approval),
        ],
    ) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate

    git(scenario.repo, "update-ref", TARGET_MAIN, attempt.tip, attempt.candidate)
    stale_approval = rejudge_approval(
        scenario,
        attempt,
        candidate=attempt.tip,
        subject=attempt.first_subject,
        row_hash=attempt.first_candidate_row_hash,
        name="older-row",
    )
    assert invoke(
        scenario.repo,
        [
            "task",
            "merge",
            "--task-id",
            attempt.task_id,
            "--target-ref",
            TARGET_MAIN,
            "--candidate",
            attempt.tip,
            "--approval",
            str(stale_approval),
        ],
    ) != 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.tip
    assert_candidate_row_hash_refusal(scenario, attempt.task_id)
    assert Journal(scenario.journal).verify() is True


def test_rejudge_then_stale_merge_refused(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    attempt = dispatch_rejudge(scenario, "T1")
    stale_approval = rejudge_approval(
        scenario,
        attempt,
        candidate=attempt.tip,
        subject=attempt.first_subject,
        row_hash=attempt.first_candidate_row_hash,
        name="stale-rejudge",
    )

    assert invoke(
        scenario.repo,
        [
            "task",
            "merge",
            "--task-id",
            attempt.task_id,
            "--target-ref",
            TARGET_MAIN,
            "--candidate",
            attempt.tip,
            "--approval",
            str(stale_approval),
        ],
    ) != 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.tip
    assert_candidate_row_hash_refusal(scenario, attempt.task_id)
    assert Journal(scenario.journal).verify() is True


def test_real_dispatch_judge_merge_flow(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    attempt = dispatch_judge(scenario, "real-1")

    assert invoke(scenario.repo, attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    journal = Journal(scenario.journal)
    entries = journal.entries()
    assert candidate_record_bytes(scenario.journal, attempt.task_id) == (
        attempt.candidate_record_bytes
    )
    merge_entries = [
        entry
        for entry in entries
        if entry.get("task_id") == attempt.task_id
        and str(entry.get("type", "")).startswith("task-merge-")
    ]
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
        "policy_approval",
        "ancestry",
        "merge_range",
        "digest_evidence",
        "cas",
    ]
    assert all(entry["status"] == "passed" for entry in merge_entries[1:-1])
    assert merge_entries[-1]["outcome"] == "PUBLISHED"
    assert journal.verify() is True
    assert subject_digest_for(scenario.repo, attempt.candidate) == attempt.approval_document["subject"]


def test_deep_sequential_merge_chain(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    attempts: list[RealAttempt] = []

    for number in range(9):
        attempt = dispatch_judge(scenario, f"chain-{number}")
        attempts.append(attempt)
        assert invoke(scenario.repo, attempt.merge_args()) == 0
        assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
        journal = Journal(scenario.journal)
        assert journal.verify() is True
        if number:
            stale = attempts[number - 1]
            assert invoke(scenario.repo, stale.merge_args()) != 0
            assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
            entries = Journal(scenario.journal).entries()
            refused = [
                entry
                for entry in entries
                if entry.get("type") == "task-merge-check"
                and entry.get("task_id") == stale.task_id
                and entry.get("status") == "refused"
            ]
            assert refused[-1]["check"] == "policy_approval"
            assert refused[-1]["detail"] == "sad-path-9 tip-mismatch"
            assert Journal(scenario.journal).verify() is True

    entries = Journal(scenario.journal).entries()
    published = [
        entry
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("outcome") == "PUBLISHED"
    ]
    assert len(published) == 9
    assert len({entry["candidate"] for entry in published}) == 9
    assert [entry["candidate"] for entry in published] == [
        attempt.candidate for attempt in attempts
    ]
    assert len({attempt.tip for attempt in attempts}) == 9
    assert [attempt.tip for attempt in attempts[1:]] == [
        attempt.candidate for attempt in attempts[:-1]
    ]
    assert Journal(scenario.journal).verify() is True


def test_interleaved_main_release_real_flow(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    base = git(scenario.repo, "rev-parse", TARGET_MAIN)
    git(scenario.repo, "update-ref", TARGET_RELEASE, base)
    main_attempts: list[RealAttempt] = []

    for number in range(3):
        attempt = dispatch_judge(scenario, f"main-{number}")
        main_attempts.append(attempt)
        assert invoke(scenario.repo, attempt.merge_args()) == 0

    release_attempt = dispatch_judge(
        scenario,
        "release-0",
        target_ref=TARGET_RELEASE,
        same_tree=True,
        evidence_document=main_attempts[-1].evidence_document,
    )
    assert release_attempt.subject == main_attempts[-1].subject
    assert invoke(scenario.repo, release_attempt.merge_args()) == 0
    release_winner = release_attempt.candidate

    for number in range(3, 5):
        attempt = dispatch_judge(scenario, f"main-{number}")
        main_attempts.append(attempt)
        assert invoke(scenario.repo, attempt.merge_args()) == 0

    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == main_attempts[-1].candidate
    assert git(scenario.repo, "rev-parse", TARGET_RELEASE) == release_winner
    assert main_attempts[-1].candidate != release_winner
    entries = Journal(scenario.journal).entries()
    release_digest = next(
        entry
        for entry in entries
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == release_attempt.task_id
        and entry.get("check") == "digest_evidence"
    )
    assert release_digest["evidence_disposition"] == "REUSE"
    published = [
        entry
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("outcome") == "PUBLISHED"
    ]
    assert len(published) == 6
    assert Journal(scenario.journal).verify() is True


def test_closed_field_envelope_refuses_extra_field(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    attempt = dispatch_judge(scenario, "closed-field")
    envelope = {
        key: value
        for key, value in attempt.approval_document.items()
        if key != "signature"
    }
    envelope["domain_version"] = "2"
    private_key = Ed25519PrivateKey.from_private_bytes(
        _decode(scenario.approver_private, expected=32, field="private key")
    )
    approval = scenario.repo / "approval-closed-field-extra.json"
    approval.write_text(
        json.dumps(
            {
                **envelope,
                "signature": _encode(
                    private_key.sign(APPROVAL_DOMAIN + canonical_json_bytes(envelope))
                ),
            }
        ),
        encoding="utf-8",
    )

    assert invoke(scenario.repo, attempt.merge_args(approval=approval)) != 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.tip
    refused = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == attempt.task_id
        and entry.get("status") == "refused"
    ]
    assert refused[-1]["check"] == "policy_approval"
    assert refused[-1]["detail"] == "sad-path-22 forged-approval"
    assert Journal(scenario.journal).verify() is True


def test_non_branch_target_ref_behaviour(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    base = git(scenario.repo, "rev-parse", TARGET_MAIN)
    tag = "refs/tags/release"
    slash_branch = "refs/heads/feature/x"
    git(scenario.repo, "update-ref", tag, base)
    git(scenario.repo, "update-ref", slash_branch, base)

    tag_attempt = dispatch_judge(scenario, "tag-target", target_ref=tag)
    assert invoke(scenario.repo, tag_attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", tag) == tag_attempt.candidate

    branch_attempt = dispatch_judge(
        scenario, "slash-branch-target", target_ref=slash_branch
    )
    assert invoke(scenario.repo, branch_attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", slash_branch) == branch_attempt.candidate
    outcomes = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-merge-outcome"
        and entry.get("task_id") in {tag_attempt.task_id, branch_attempt.task_id}
    ]
    assert [(entry["task_id"], entry["outcome"]) for entry in outcomes] == [
        (tag_attempt.task_id, "PUBLISHED"),
        (branch_attempt.task_id, "PUBLISHED"),
    ]
    assert Journal(scenario.journal).verify() is True


def test_huge_linear_history_publishes_as_fast_forward(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    base = git(scenario.repo, "rev-parse", TARGET_MAIN)
    attempt = dispatch_judge(scenario, "huge-linear", commit_count=200)

    assert invoke(scenario.repo, attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == git(
        scenario.repo, "rev-parse", "HEAD"
    )
    assert git(scenario.repo, "rev-list", "--count", f"{base}..HEAD") == "200"
    assert git(scenario.repo, "rev-list", "--merges", f"{base}..HEAD") == ""
    assert Journal(scenario.journal).verify() is True


def test_multiple_satisfying_evidence_records_one_claim(tmp_path: Path) -> None:
    positive_root = tmp_path / "positive"
    positive_root.mkdir()
    scenario = RealRepository.create(positive_root)
    other_subject = "sha256:" + "0" * 64
    records: list[dict[str, object]] = []

    def positive_evidence(subject: str) -> list[dict[str, object]]:
        records.extend(
            [
                signed_evidence_record(scenario, subject, "/usr/bin/pytest"),
                signed_evidence_record(scenario, other_subject, "/opt/bin/pytest"),
            ]
        )
        return records

    attempt = dispatch_judge(
        scenario, "multiple-evidence", evidence_factory=positive_evidence
    )
    assert invoke(scenario.repo, attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    digest_check = next(
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == attempt.task_id
        and entry.get("check") == "digest_evidence"
    )
    assert digest_check["evidence_ids"] == [
        canonical_sha256(record) for record in records
    ]
    assert Journal(scenario.journal).verify() is True

    negative_root = tmp_path / "negative"
    negative_root.mkdir()
    refused_scenario = RealRepository.create(negative_root)

    def negative_evidence(_: str) -> list[dict[str, object]]:
        return [
            signed_evidence_record(
                refused_scenario, "sha256:" + "1" * 64, "/usr/bin/pytest"
            ),
            signed_evidence_record(
                refused_scenario, "sha256:" + "2" * 64, "/opt/bin/pytest"
            ),
        ]

    refused_attempt = dispatch_judge(
        refused_scenario,
        "nonmatching-evidence",
        evidence_factory=negative_evidence,
        judge_exit=1,
    )
    assert invoke(refused_scenario.repo, refused_attempt.merge_args()) != 0
    assert git(refused_scenario.repo, "rev-parse", TARGET_MAIN) == refused_attempt.tip
    refused = [
        entry
        for entry in Journal(refused_scenario.journal).entries()
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == refused_attempt.task_id
        and entry.get("status") == "refused"
    ]
    assert refused[-1]["check"] == "digest_evidence"
    assert refused[-1]["detail"] == "sad-path-5 satisfying-evidence-missing"
    assert Journal(refused_scenario.journal).verify() is True


def test_evidence_suite_results_present_vs_absent_irrelevant_to_merge(
    tmp_path: Path,
) -> None:
    suite_results: dict[str, object] = {
        "manifest_digest": "sha256:" + "a" * 64,
        "counts": {
            "passed": 1,
            "skipped": 0,
            "failed": 0,
            "errors": 0,
            "xfailed": 0,
            "xpassed": 0,
        },
        "non_passed": [],
        "missing": [],
        "extra_count": 0,
        "outcome_digest": "sha256:" + "b" * 64,
    }
    assert validate_suite_results(suite_results) == suite_results
    outcomes: list[str] = []

    for name, results in (("present", suite_results), ("absent", None)):
        root = tmp_path / name
        root.mkdir()
        scenario = RealRepository.create(root)

        def evidence(subject: str, *, _results=results, _scenario=scenario) -> list[dict[str, object]]:
            body: dict[str, object] = {
                "claim_id": "tests-executed",
                "command": "pytest -q",
                "command_digest": command_digest(["pytest", "-q"]),
                "executable_path": "/usr/bin/pytest",
                "exit_code": 0,
                "producer_id": "worker",
                "subject_digest": subject,
                "suite_results": _results,
                "confinement_result_digest": "sha256:" + "c" * 64,
                "confinement_profile_digest": "sha256:" + "d" * 64,
            }
            return [{**body, "signature": sign_evidence(body, _scenario.producer_private)}]

        attempt = dispatch_judge(
            scenario, f"suite-results-{name}", evidence_factory=evidence
        )
        assert attempt.evidence_document["suite_results"] == results
        assert invoke(scenario.repo, attempt.merge_args()) == 0
        assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
        published = [
            entry
            for entry in Journal(scenario.journal).entries()
            if entry.get("type") == "task-merge-outcome"
            and entry.get("task_id") == attempt.task_id
        ]
        assert len(published) == 1
        assert published[0]["candidate"] == attempt.candidate
        outcomes.append(str(published[0]["outcome"]))
        assert Journal(scenario.journal).verify() is True

    assert outcomes == ["PUBLISHED", "PUBLISHED"]


def test_deep_enormous_tree_candidate_publishes(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)

    def build(worktree: Path) -> None:
        directory = worktree
        for depth in range(120):
            directory /= f"dir{depth}"
            directory.mkdir()
            for number in range(2):
                (directory / f"file_{depth}_{number}.txt").write_text(
                    f"depth {depth} file {number}\n", encoding="utf-8"
                )
        git(worktree, "add", "-A")
        git(worktree, "commit", "-q", "-m", "deep-enormous-tree")

    attempt = dispatch_judge(
        scenario, "deep-enormous-tree", candidate_builder=build
    )

    assert invoke(scenario.repo, attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    assert subject_digest_for(scenario.repo, attempt.candidate) == attempt.subject
    outcomes = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-merge-outcome"
        and entry.get("task_id") == attempt.task_id
    ]
    assert outcomes[-1]["outcome"] == "PUBLISHED"
    assert Journal(scenario.journal).verify() is True


def test_unusual_target_ref_name_behaviour(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)
    base = git(scenario.repo, "rev-parse", TARGET_MAIN)
    valid_ref = "refs/heads/release/v2.0"
    invalid_ref = "refs/heads/x~y"
    git(scenario.repo, "update-ref", valid_ref, base)

    valid = dispatch_judge(scenario, "valid-unusual-ref", target_ref=valid_ref)
    assert invoke(scenario.repo, valid.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", valid_ref) == valid.candidate

    creation = subprocess.run(
        ["git", "-C", str(scenario.repo), "update-ref", invalid_ref, base],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert creation.returncode != 0
    invalid = dispatch_judge(
        scenario,
        "invalid-unusual-ref",
        target_ref=invalid_ref,
        observed_tip=base,
    )
    assert invoke(scenario.repo, invalid.merge_args()) != 0
    verification = subprocess.run(
        ["git", "-C", str(scenario.repo), "rev-parse", "--verify", invalid_ref],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert verification.returncode != 0
    refused = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-merge-check"
        and entry.get("task_id") == invalid.task_id
        and entry.get("status") == "refused"
    ]
    assert refused[-1]["detail"] == "sad-path-20 target-ref-missing"
    assert Journal(scenario.journal).verify() is True


def test_git_author_identity_irrelevant_to_merge(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)

    def build(worktree: Path) -> None:
        git(worktree, "config", "user.name", "approver")
        git(worktree, "config", "user.email", "approver@example.com")
        (worktree / "authored-by-approver.txt").write_text(
            "candidate\n", encoding="utf-8"
        )
        git(worktree, "add", "authored-by-approver.txt")
        git(worktree, "commit", "-q", "-m", "approver-authored-candidate")

    attempt = dispatch_judge(scenario, "approver-authored", candidate_builder=build)
    assert git(
        scenario.repo, "show", "-s", "--format=%an <%ae>", attempt.candidate
    ) == "approver <approver@example.com>"

    assert invoke(scenario.repo, attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    assert attempt.evidence_document["producer_id"] == "worker"
    assert attempt.approval_document["approver_id"] == "approver"
    assert Journal(scenario.journal).verify() is True


def test_candidate_edits_product_and_test_files_publishes(tmp_path: Path) -> None:
    scenario = RealRepository.create(tmp_path)

    def build(worktree: Path) -> None:
        product = worktree / "src" / "app.py"
        test = worktree / "tests" / "test_app.py"
        product.parent.mkdir()
        test.parent.mkdir()
        product.write_text("def answer():\n    return 42\n", encoding="utf-8")
        test.write_text(
            "from app import answer\n\n\ndef test_answer():\n    assert answer() == 42\n",
            encoding="utf-8",
        )
        git(worktree, "add", "src/app.py", "tests/test_app.py")
        git(worktree, "commit", "-q", "-m", "product-and-test")

    attempt = dispatch_judge(scenario, "product-and-test", candidate_builder=build)

    assert invoke(scenario.repo, attempt.merge_args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    changed = git(
        scenario.repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        attempt.candidate,
    ).splitlines()
    assert "src/app.py" in changed
    assert "tests/test_app.py" in changed
    assert Journal(scenario.journal).verify() is True


def test_three_way_concurrent_cas_race_one_winner(tmp_path: Path) -> None:
    if "MUTANT_UNDER_TEST" in os.environ:
        # The spawned merge processes import the copied tree, whose trampoline
        # cannot initialise mutmut's runtime outside its runner. The CAS refusal
        # is asserted in-process by test_task_merge, and cli/main.py is outside
        # the mutated scope, so mutation pressure is not lost.
        pytest.skip("spawned merge subprocesses cannot run the mutmut-trampolined tree")
    scenario = RealRepository.create(tmp_path)
    attempts = tuple(
        dispatch_judge(scenario, f"three-way-race-{number}") for number in range(3)
    )
    assert len({attempt.candidate for attempt in attempts}) == 3
    assert len({attempt.task_id for attempt in attempts}) == 3
    (scenario.repo / "governance" / "evidence.json").write_text(
        json.dumps([attempt.evidence_document for attempt in attempts]), encoding="utf-8"
    )

    for _ in range(10):
        git(scenario.repo, "update-ref", TARGET_MAIN, attempts[0].tip)
        before = len(Journal(scenario.journal).entries())
        results = run_concurrent_merges(scenario.repo, attempts)
        entries = Journal(scenario.journal).entries()[before:]
        outcomes = [
            entry for entry in entries if entry.get("type") == "task-merge-outcome"
        ]
        published = [
            entry for entry in outcomes if entry.get("outcome") == "PUBLISHED"
        ]
        assert len(published) <= 1
        # Only the two race-specific refusals count as genuine losers — the CAS
        # check (sad-path-1 ref-moved) and the tip check (sad-path-9
        # tip-mismatch) both prove the ref moved under the loser. Other refused
        # checks (policy, error) must not count, or a non-race failure could
        # satisfy the break. Require them from two distinct task_ids: each merge
        # emits at most one refused check, so two distinct ids = two real losers.
        race_losers = [
            entry
            for entry in entries
            if entry.get("type") == "task-merge-check"
            and entry.get("status") == "refused"
            and entry.get("detail")
            in ("sad-path-1 ref-moved", "sad-path-9 tip-mismatch")
        ]
        if len({entry.get("task_id") for entry in race_losers}) >= 2:
            break
    else:
        pytest.fail(
            "fewer than two real race losers in 10 three-way races: "
            f"{[(result.returncode, result.stderr) for result in results]}"
        )

    assert len(published) == 1
    assert sum(result.returncode == 0 for result in results) == 1
    assert sum(result.returncode != 0 for result in results) == 2
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == published[0]["candidate"]
    assert Journal(scenario.journal).verify() is True
