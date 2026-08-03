"""Append-only evaluation journal.

Covers the persistence failure modes in the slice definition §9: unreadable
store, mid-append failure, and two concurrent evaluations.
"""

from __future__ import annotations

import json
import multiprocessing
import sqlite3
import time
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
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
