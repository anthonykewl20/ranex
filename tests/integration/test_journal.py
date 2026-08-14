"""Append-only evaluation journal.

Covers the persistence failure modes in the slice definition §9: unreadable
store, mid-append failure, and two concurrent evaluations.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import main, subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import canonical_sha256, command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import (
    TaskCandidate,
)
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    evaluate,
)

SUBJECT = "sha256:" + "c" * 64

# SLICE-003: claim and evidence both name the argv. This file is about the
# journal, so the two agree and the verdict stays PASS.
COMMAND = ["pytest", "-q"]
COMMAND_DIGEST = "sha256:" + canonical_sha256(COMMAND)
EXECUTABLE = "/usr/bin/pytest"
TARGET_REF = "refs/heads/main"
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


@dataclass
class MergeJournalScenario:
    repo: Path
    tip: str
    candidate: str
    subject: str
    approval: Path
    worker_private: str
    approver_private: str

    @classmethod
    def create(cls, root: Path) -> MergeJournalScenario:
        root.mkdir(parents=True, exist_ok=True)
        repo = root / "governed"
        git(root, "init", "-q", str(repo))
        git(repo, "config", "user.email", "test@example.com")
        git(repo, "config", "user.name", "Test")
        worker_private, worker_public = generate_keypair()
        approver_private, approver_public = generate_keypair()
        governance = repo / "governance"
        governance.mkdir()
        (governance / "gates.yaml").write_bytes(CATALOG)
        (governance / "producers.yaml").write_text(
            f"producers:\n  worker: {worker_public}\n  owner: {approver_public}\n",
            encoding="utf-8",
        )
        (repo / ".gitignore").write_text(
            "governance/evidence.json\ngovernance/journal.sqlite3\n",
            encoding="utf-8",
        )
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "base")
        git(repo, "branch", "-M", "main")
        tip = git(repo, "rev-parse", TARGET_REF)
        (repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
        git(repo, "add", "candidate.txt")
        git(repo, "commit", "-q", "-m", "candidate")
        candidate = git(repo, "rev-parse", "HEAD")
        git(repo, "update-ref", TARGET_REF, tip, candidate)
        scenario = cls(
            repo,
            tip,
            candidate,
            subject_digest_for(repo, candidate),
            repo / "approval.json",
            worker_private,
            approver_private,
        )
        scenario.add_attempt("task-1", candidate, scenario.approval)
        return scenario

    @property
    def journal_path(self) -> Path:
        return self.repo / "governance" / "journal.sqlite3"

    def add_attempt(
        self,
        task_id: str,
        candidate: str,
        approval: Path,
        target_ref: str = TARGET_REF,
    ) -> None:
        subject = subject_digest_for(self.repo, candidate)
        evidence = {
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
        (self.repo / "governance" / "evidence.json").write_text(
            json.dumps(
                [{**evidence, "signature": sign_evidence(evidence, self.worker_private)}]
            ),
            encoding="utf-8",
        )
        candidate_value = TaskCandidate(task_id, "landing", subject, ())
        Journal(self.journal_path).append(candidate_value)
        envelope = {
            "candidate": candidate,
            "subject": subject,
            "target_ref": target_ref,
            "tip": self.tip,
            "catalog_digest": catalog_digest_for(CATALOG),
            "candidate_row_hash": candidate_row_hash(candidate_value.as_record()),
            "approver_id": "owner",
        }
        approval.write_text(
            json.dumps(
                {**envelope, "signature": sign_approval(envelope, self.approver_private)}
            ),
            encoding="utf-8",
        )

    def args(
        self,
        *,
        task_id: str = "task-1",
        candidate: str | None = None,
        approval: Path | None = None,
        target_ref: str = TARGET_REF,
    ) -> list[str]:
        return [
            "task",
            "merge",
            "--task-id",
            task_id,
            "--target-ref",
            target_ref,
            "--candidate",
            candidate or self.candidate,
            "--approval",
            str(approval or self.approval),
        ]

    def competing_candidate(self, message: str) -> str:
        return git(
            self.repo,
            "commit-tree",
            git(self.repo, "rev-parse", f"{self.candidate}^{{tree}}"),
            "-p",
            self.tip,
            "-m",
            message,
        )

    def dispatch_judge(self, task_id: str) -> RealMergeAttempt:
        worktrees = self.repo.parent / "worktrees"
        worktrees.mkdir(exist_ok=True)
        worktree = worktrees / task_id
        assert invoke(
            self.repo,
            [
                "task", "dispatch", "--task-id", task_id,
                "--target", str(self.repo), "--worktree", str(worktree),
                "--journal", str(self.journal_path),
            ],
        ) == 0
        candidate_path = worktree / f"{task_id}.txt"
        candidate_path.write_text(f"candidate {task_id}\n", encoding="utf-8")
        git(worktree, "add", candidate_path.name)
        git(worktree, "commit", "-q", "-m", task_id)
        candidate = git(worktree, "rev-parse", "HEAD")
        subject = subject_digest_for(self.repo, candidate)
        evidence = {
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
            **evidence,
            "signature": sign_evidence(evidence, self.worker_private),
        }
        evidence_bytes = json.dumps([evidence_document]).encode()
        (worktree / "governance" / "evidence.json").write_bytes(evidence_bytes)
        (self.repo / "governance" / "evidence.json").write_bytes(evidence_bytes)
        assert invoke(
            self.repo,
            [
                "task", "judge", "--task-id", task_id,
                "--emitted-worktree", str(worktree),
                "--emitted-commit", candidate, "--gate", "landing",
                "--gate-catalog", "governance/gates.yaml",
                "--evidence", "governance/evidence.json",
                "--producers", "governance/producers.yaml",
                "--journal", str(self.journal_path),
            ],
        ) == 0
        candidate_record = next(
            entry
            for entry in reversed(Journal(self.journal_path).entries())
            if entry.get("type") == "task-candidate"
            and entry.get("task_id") == task_id
        )
        envelope = {
            "candidate": candidate,
            "subject": subject,
            "target_ref": TARGET_REF,
            "tip": self.tip,
            "catalog_digest": catalog_digest_for(CATALOG),
            "candidate_row_hash": candidate_row_hash(candidate_record),
            "approver_id": "owner",
        }
        approval = self.repo / f"approval-{task_id}.json"
        approval.write_text(
            json.dumps(
                {**envelope, "signature": sign_approval(envelope, self.approver_private)}
            ),
            encoding="utf-8",
        )
        return RealMergeAttempt(task_id, candidate, approval, evidence_document)


@dataclass(frozen=True)
class RealMergeAttempt:
    task_id: str
    candidate: str
    approval: Path
    evidence_document: dict[str, object]

    def args(self) -> list[str]:
        return [
            "task", "merge", "--task-id", self.task_id,
            "--target-ref", TARGET_REF, "--candidate", self.candidate,
            "--approval", str(self.approval),
        ]


def delete_last_merge_outcome(path: Path, candidate: str, outcome: str) -> None:
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT seq, record FROM evaluations ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        assert row is not None
        record = json.loads(row[1])
        assert record["type"] == "task-merge-outcome"
        assert record["candidate"] == candidate
        assert record["outcome"] == outcome
        connection.execute("DROP TRIGGER evaluations_no_delete")
        connection.execute("DELETE FROM evaluations WHERE seq = ?", (row[0],))


def run_concurrent_merges(
    repo: Path, attempts: tuple[RealMergeAttempt, RealMergeAttempt]
) -> tuple[subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    barrier = threading.Barrier(2)
    results: list[subprocess.CompletedProcess[str] | None] = [None, None]
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
            [sys.executable, "-m", "ranex.cli.main", *attempts[index].args()],
            cwd=repo,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    threads = [threading.Thread(target=run, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads)
    assert results[0] is not None and results[1] is not None
    return results[0], results[1]


def candidate_row_bytes(path: Path, task_id: str) -> bytes:
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT record FROM evaluations WHERE json_extract(record, '$.type') = "
            "'task-candidate' AND json_extract(record, '$.task_id') = ? "
            "ORDER BY seq DESC LIMIT 1",
            (task_id,),
        ).fetchone()
    assert row is not None
    return row[0].encode("utf-8")


def make_evaluation(claim: str = "tests-executed"):
    return evaluate(
        Gate(
            gate_id="landing",
            rule_id="TESTS_EXECUTED",
            required_claims=(
                Claim(claim_id=claim, command_digest=COMMAND_DIGEST),
            ),
            blocking=True,
        ),
        (
            Evidence(
                claim_id=claim,
                subject_digest=SUBJECT,
                producer_id="worker",
                command=" ".join(COMMAND),
                command_digest=COMMAND_DIGEST,
                executable_path=EXECUTABLE,
                exit_code=0,
            ),
        ),
        subject_digest=SUBJECT,
        approver_id="owner",
    )


def _append_concurrently(
    path: str,
    process_number: int,
    start: multiprocessing.synchronize.Event,
    results: multiprocessing.queues.Queue,
) -> None:
    """Append records after every worker is ready to race for the same link."""

    start.wait()
    succeeded = 0
    for append_number in range(25):
        deadline = time.monotonic() + 10
        while True:
            try:
                Journal(Path(path)).append(
                    make_evaluation(f"worker-{process_number}-append-{append_number}")
                )
            except sqlite3.OperationalError as error:
                if "database is locked" not in str(error).lower():
                    results.put((succeeded, str(error)))
                    return
                if time.monotonic() >= deadline:
                    results.put((succeeded, "timed out waiting for database lock"))
                    return
                time.sleep(0.01)
            else:
                succeeded += 1
                break
    results.put((succeeded, None))


def test_append_then_read_back(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "j.sqlite3")
    journal.append(make_evaluation())
    rows = journal.entries()
    assert len(rows) == 1
    assert rows[0]["verdict"] == "PASS"
    assert rows[0]["subject_digest"] == SUBJECT


def test_journal_is_append_only(tmp_path: Path) -> None:
    """No update or delete path exists, and the table refuses both."""

    journal = Journal(tmp_path / "j.sqlite3")
    journal.append(make_evaluation())
    with sqlite3.connect(tmp_path / "j.sqlite3") as conn:
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("UPDATE evaluations SET verdict = 'PASS'")
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("DELETE FROM evaluations")


def test_replay_yields_identical_state(tmp_path: Path) -> None:
    journal = Journal(tmp_path / "j.sqlite3")
    for _ in range(3):
        journal.append(make_evaluation())
    first = journal.entries()
    second = Journal(tmp_path / "j.sqlite3").entries()
    assert first == second


def test_digest_chain_detects_tampering(tmp_path: Path) -> None:
    """Defence in depth: the trigger stops casual writes, the chain catches the rest.

    An attacker with raw file access can drop the trigger — that is the whole
    reason the hash chain exists. This test grants them exactly that power and
    proves `verify()` still refuses the result.
    """

    path = tmp_path / "j.sqlite3"
    journal = Journal(path)
    journal.append(make_evaluation())
    assert journal.verify() is True

    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER evaluations_no_update")
        conn.execute(
            "UPDATE evaluations SET record = ? WHERE seq = 1",
            (json.dumps({"verdict": "PASS", "tampered": True}),),
        )
        conn.commit()

    assert Journal(path).verify() is False


def test_digest_chain_detects_a_rewritten_previous_link(tmp_path: Path) -> None:
    path = tmp_path / "j.sqlite3"
    journal = Journal(path)
    journal.append(make_evaluation("first"))
    journal.append(make_evaluation("second"))

    with sqlite3.connect(path) as conn:
        conn.execute("DROP TRIGGER evaluations_no_update")
        conn.execute("UPDATE evaluations SET prev_link = ? WHERE seq = 2", ("forged",))
        conn.commit()

    assert Journal(path).verify() is False


def test_concurrent_appends_preserve_the_digest_chain(tmp_path: Path) -> None:
    """Each concurrent append must chain onto the row committed before it."""

    path = tmp_path / "j.sqlite3"
    Journal(path).append(make_evaluation("initialise"))
    # fork, not spawn: a spawn child re-executes the parent's __main__, and
    # under mutmut that is mutmut's own module, whose unguarded
    # set_start_method('fork') kills every child before the test begins. The
    # property under test — chain integrity across concurrent processes — is
    # the same under either start method.
    context = multiprocessing.get_context("fork")
    start = context.Event()
    results = context.Queue()
    processes = [
        context.Process(target=_append_concurrently, args=(str(path), number, start, results))
        for number in range(6)
    ]
    for process in processes:
        process.start()
    start.set()
    for process in processes:
        process.join(timeout=30)

    assert [process.exitcode for process in processes] == [0] * len(processes)
    worker_results = [results.get(timeout=5) for _ in processes]
    assert worker_results == [(25, None)] * len(processes)
    assert len(Journal(path).entries()) == 151
    assert Journal(path).verify() is True


def test_verify_missing_journal_does_not_create_it(tmp_path: Path) -> None:
    """Verification never enters append's create-and-initialise connection path."""

    path = tmp_path / "j.sqlite3"
    with pytest.raises(sqlite3.OperationalError):
        Journal(path).verify()

    assert not path.exists()


def test_unreadable_store_raises_rather_than_defaulting(tmp_path: Path) -> None:
    bad = tmp_path / "not-a-db.sqlite3"
    bad.write_text("this is not a database", encoding="utf-8")
    with pytest.raises(sqlite3.DatabaseError):
        Journal(bad).entries()


def test_two_journals_on_one_file_both_persist(tmp_path: Path) -> None:
    path = tmp_path / "j.sqlite3"
    Journal(path).append(make_evaluation("tests-executed"))
    Journal(path).append(make_evaluation("review-recorded"))
    assert len(Journal(path).entries()) == 2


def test_task_merge_journals_intent_checks_cas_and_one_outcome_in_order(
    tmp_path: Path,
) -> None:
    scenario = MergeJournalScenario.create(tmp_path)

    assert invoke(scenario.repo, scenario.args()) == 0
    entries = Journal(scenario.journal_path).entries()
    merge_entries = [
        entry for entry in entries if str(entry.get("type", "")).startswith("task-merge-")
    ]
    assert [
        (
            entry["type"],
            entry.get("check"),
            entry.get("status"),
            entry.get("outcome"),
        )
        for entry in merge_entries
    ] == [
        ("task-merge-intent", None, None, None),
        ("task-merge-check", "policy_approval", "passed", None),
        ("task-merge-check", "ancestry", "passed", None),
        ("task-merge-check", "merge_range", "passed", None),
        ("task-merge-check", "digest_evidence", "passed", None),
        ("task-merge-check", "cas", "passed", None),
        ("task-merge-outcome", None, None, "PUBLISHED"),
    ]
    outcomes = [
        entry
        for entry in merge_entries
        if entry["type"] == "task-merge-outcome" and entry["task_id"] == "task-1"
    ]
    assert len(outcomes) == 1
    assert git(scenario.repo, "rev-parse", TARGET_REF) == scenario.candidate
    assert Journal(scenario.journal_path).verify() is True


def test_task_merge_recovers_post_cas_crash_as_inferred(tmp_path: Path) -> None:
    scenario = MergeJournalScenario.create(tmp_path)
    attempt = scenario.dispatch_judge("recovery-inferred")

    assert invoke(scenario.repo, attempt.args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_REF) == attempt.candidate
    entries = Journal(scenario.journal_path).entries()
    assert any(
        entry.get("type") == "task-merge-outcome"
        and entry.get("candidate") == attempt.candidate
        and entry.get("outcome") == "PUBLISHED"
        for entry in entries
    )

    delete_last_merge_outcome(scenario.journal_path, attempt.candidate, "PUBLISHED")
    assert Journal(scenario.journal_path).verify() is True
    entries = Journal(scenario.journal_path).entries()
    assert entries[-1]["type"] == "task-merge-check"
    assert (entries[-1]["check"], entries[-1]["status"]) == ("cas", "passed")
    assert not any(
        entry
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("candidate") == attempt.candidate
    )

    missing = scenario.repo / "missing-approval.json"
    assert invoke(
        scenario.repo,
        scenario.args(
            task_id=attempt.task_id,
            candidate=attempt.candidate,
            approval=missing,
        ),
    ) != 0
    outcomes = [
        entry
        for entry in Journal(scenario.journal_path).entries()
        if entry.get("type") == "task-merge-outcome"
        and entry.get("candidate") == attempt.candidate
    ]
    assert [entry["outcome"] for entry in outcomes] == ["INFERRED"]
    assert git(scenario.repo, "rev-parse", TARGET_REF) == attempt.candidate
    assert Journal(scenario.journal_path).verify() is True


def test_task_merge_recovers_pre_cas_crash_as_aborted(tmp_path: Path) -> None:
    scenario = MergeJournalScenario.create(tmp_path)
    attempt = scenario.dispatch_judge("recovery-aborted")
    approval_document = json.loads(attempt.approval.read_text(encoding="utf-8"))
    approval_document["signature"] = "forged"
    attempt.approval.write_text(json.dumps(approval_document), encoding="utf-8")

    assert invoke(scenario.repo, attempt.args()) != 0
    assert git(scenario.repo, "rev-parse", TARGET_REF) == scenario.tip
    delete_last_merge_outcome(scenario.journal_path, attempt.candidate, "REFUSED")
    assert Journal(scenario.journal_path).verify() is True

    missing = scenario.repo / "missing-approval.json"
    assert invoke(
        scenario.repo,
        scenario.args(
            task_id=attempt.task_id,
            candidate=attempt.candidate,
            approval=missing,
        ),
    ) != 0
    outcomes = [
        entry
        for entry in Journal(scenario.journal_path).entries()
        if entry.get("type") == "task-merge-outcome"
        and entry.get("candidate") == attempt.candidate
    ]
    assert [entry["outcome"] for entry in outcomes] == ["ABORTED"]
    assert git(scenario.repo, "rev-parse", TARGET_REF) == scenario.tip
    assert Journal(scenario.journal_path).verify() is True


def test_task_merge_and_recovery_never_rewrite_candidate_rows(tmp_path: Path) -> None:
    scenario = MergeJournalScenario.create(tmp_path)
    attempt = scenario.dispatch_judge("candidate-immutability")
    before = candidate_row_bytes(scenario.journal_path, attempt.task_id)

    assert invoke(scenario.repo, attempt.args()) == 0
    assert git(scenario.repo, "rev-parse", TARGET_REF) == attempt.candidate
    delete_last_merge_outcome(scenario.journal_path, attempt.candidate, "PUBLISHED")

    missing = scenario.repo / "missing-approval.json"
    assert invoke(
        scenario.repo,
        scenario.args(
            task_id=attempt.task_id,
            candidate=attempt.candidate,
            approval=missing,
        ),
    ) != 0
    assert candidate_row_bytes(scenario.journal_path, attempt.task_id) == before
    outcomes = [
        entry
        for entry in Journal(scenario.journal_path).entries()
        if entry.get("type") == "task-merge-outcome"
        and entry.get("candidate") == attempt.candidate
    ]
    assert [entry["outcome"] for entry in outcomes] == ["INFERRED"]
    assert Journal(scenario.journal_path).verify() is True


def test_sad_path_18_same_task_competing_merges_journal_one_winner_and_loser(
    tmp_path: Path,
) -> None:
    if "MUTANT_UNDER_TEST" in os.environ:
        # The spawned merge processes import the copied tree, whose trampoline
        # cannot initialise mutmut's runtime outside its runner. The CAS refusal
        # they observe is asserted in-process by test_task_merge, and cli/main.py
        # is outside the mutated scope, so mutation pressure is not lost.
        pytest.skip("spawned merge subprocesses cannot run the mutmut-trampolined tree")
    scenario = MergeJournalScenario.create(tmp_path)
    attempt = scenario.dispatch_judge("same-task-race")

    for _ in range(10):
        git(scenario.repo, "update-ref", TARGET_REF, scenario.tip)
        before = len(Journal(scenario.journal_path).entries())
        results = run_concurrent_merges(scenario.repo, (attempt, attempt))
        entries = Journal(scenario.journal_path).entries()[before:]
        cas_refusals = [
            entry
            for entry in entries
            if entry.get("type") == "task-merge-check"
            and entry.get("task_id") == attempt.task_id
            and entry.get("check") == "cas"
            and entry.get("status") == "refused"
            and entry.get("detail") == "sad-path-1 ref-moved"
        ]
        if cas_refusals:
            break
    else:
        pytest.fail(
            "no real same-task CAS-refused loser in 10 concurrent attempts: "
            f"{[(result.returncode, result.stderr) for result in results]}"
        )

    outcomes = [
        entry for entry in entries if entry.get("type") == "task-merge-outcome"
    ]
    assert sum(entry.get("outcome") == "PUBLISHED" for entry in outcomes) == 1
    assert sum(result.returncode == 0 for result in results) == 1
    assert sum(result.returncode != 0 for result in results) == 1
    assert any(entry.get("outcome") == "REFUSED" for entry in outcomes)
    assert git(scenario.repo, "rev-parse", TARGET_REF) == attempt.candidate
    assert Journal(scenario.journal_path).verify() is True


def test_sad_path_19_different_tasks_competing_for_ref_journal_one_winner_and_loser(
    tmp_path: Path,
) -> None:
    if "MUTANT_UNDER_TEST" in os.environ:
        # Same trampoline limitation as the same-task race above.
        pytest.skip("spawned merge subprocesses cannot run the mutmut-trampolined tree")
    scenario = MergeJournalScenario.create(tmp_path)
    first = scenario.dispatch_judge("different-task-race-1")
    second = scenario.dispatch_judge("different-task-race-2")
    (scenario.repo / "governance" / "evidence.json").write_text(
        json.dumps([first.evidence_document, second.evidence_document]), encoding="utf-8"
    )
    assert first.task_id != second.task_id
    assert first.candidate != second.candidate
    assert first.approval != second.approval
    assert first.approval.read_bytes() != second.approval.read_bytes()

    for _ in range(10):
        git(scenario.repo, "update-ref", TARGET_REF, scenario.tip)
        before = len(Journal(scenario.journal_path).entries())
        results = run_concurrent_merges(scenario.repo, (first, second))
        entries = Journal(scenario.journal_path).entries()[before:]
        cas_refusals = [
            entry
            for entry in entries
            if entry.get("type") == "task-merge-check"
            and entry.get("task_id") in {first.task_id, second.task_id}
            and entry.get("check") == "cas"
            and entry.get("status") == "refused"
            and entry.get("detail") == "sad-path-1 ref-moved"
        ]
        if cas_refusals:
            break
    else:
        pytest.fail(
            "no real different-task CAS-refused loser in 10 concurrent attempts: "
            f"{[(result.returncode, result.stderr) for result in results]}"
        )

    outcomes = [
        entry for entry in entries if entry.get("type") == "task-merge-outcome"
    ]
    published = [entry for entry in outcomes if entry.get("outcome") == "PUBLISHED"]
    assert len(published) == 1
    assert sum(result.returncode == 0 for result in results) == 1
    assert sum(result.returncode != 0 for result in results) == 1
    assert any(entry.get("outcome") == "REFUSED" for entry in outcomes)
    assert git(scenario.repo, "rev-parse", TARGET_REF) == published[0]["candidate"]
    assert Journal(scenario.journal_path).verify() is True


def test_criterion_13_reused_evidence_is_distinguishable_from_fresh_execution(
    tmp_path: Path,
) -> None:
    scenario = MergeJournalScenario.create(tmp_path)
    release_ref = "refs/heads/release"
    git(scenario.repo, "update-ref", release_ref, scenario.tip)

    assert invoke(scenario.repo, scenario.args()) == 0
    entries = Journal(scenario.journal_path).entries()
    assert next(
        entry["outcome"]
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("task_id") == "task-1"
    ) == "PUBLISHED"
    fresh_check = next(
        entry
        for entry in entries
        if entry.get("type") == "task-merge-check"
        and entry.get("check") == "digest_evidence"
        and entry.get("task_id") == "task-1"
    )
    assert fresh_check["evidence_disposition"] == "FRESH"
    assert len(fresh_check["evidence_ids"]) == 1
    h = fresh_check["evidence_ids"][0]
    assert fresh_check["evidence_ids"] == [h]

    second = git(
        scenario.repo,
        "commit-tree",
        git(scenario.repo, "rev-parse", f"{scenario.candidate}^{{tree}}"),
        "-p",
        scenario.tip,
        "-m",
        "reuse evidence on release",
    )
    assert subject_digest_for(scenario.repo, second) == scenario.subject
    second_approval = scenario.repo / "task-2-approval.json"
    scenario.add_attempt(
        "task-2",
        second,
        second_approval,
        target_ref=release_ref,
    )

    assert invoke(
        scenario.repo,
        scenario.args(
            task_id="task-2",
            candidate=second,
            approval=second_approval,
            target_ref=release_ref,
        ),
    ) == 0
    entries = Journal(scenario.journal_path).entries()
    assert next(
        entry["outcome"]
        for entry in entries
        if entry.get("type") == "task-merge-outcome"
        and entry.get("task_id") == "task-2"
    ) == "PUBLISHED"
    reused_check = next(
        entry
        for entry in entries
        if entry.get("type") == "task-merge-check"
        and entry.get("check") == "digest_evidence"
        and entry.get("task_id") == "task-2"
    )
    assert reused_check["evidence_disposition"] == "REUSE"
    assert reused_check["evidence_ids"] == [h]


def test_sad_path_1_cas_race_refuses_exactly_once_and_keeps_the_winner(
    tmp_path: Path,
) -> None:
    from test_task_merge import merge_args, prepare

    repo = tmp_path / "governed"
    tip, candidate, approval, _ = prepare(repo)
    competitor = git(
        repo,
        "commit-tree",
        git(repo, "rev-parse", f"{candidate}^{{tree}}"),
        "-p",
        tip,
        "-m",
        "competitor",
    )

    from ranex.cli import main as main_module

    real_git = main_module.git

    def racing_git(repository_root: Path, *arguments: str, **kwargs: object):
        if arguments and arguments[0] == "update-ref":
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository_root),
                    "update-ref",
                    "refs/heads/main",
                    competitor,
                    tip,
                ],
                check=True,
            )
        return real_git(repository_root, *arguments, **kwargs)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        monkeypatch.setattr("ranex.cli.main.git", racing_git)
        exit_code = main(merge_args(candidate, approval))

    assert exit_code != 0
    assert git(repo, "rev-parse", "refs/heads/main") == competitor
    entries = Journal(repo / "governance" / "journal.sqlite3").entries()
    checks = [entry for entry in entries if entry.get("type") == "task-merge-check"]
    assert [(entry["check"], entry["status"]) for entry in checks] == [
        ("policy_approval", "passed"),
        ("ancestry", "passed"),
        ("merge_range", "passed"),
        ("digest_evidence", "passed"),
        ("cas", "refused"),
    ]
    assert checks[-1]["detail"] == "sad-path-1 ref-moved"
    outcomes = [entry for entry in entries if entry.get("type") == "task-merge-outcome"]
    assert len(outcomes) == 1
    assert outcomes[0]["outcome"] == "REFUSED"
    assert Journal(repo / "governance" / "journal.sqlite3").verify() is True
