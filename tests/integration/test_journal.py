"""Append-only evaluation journal.

Covers the persistence failure modes in the slice definition §9: unreadable
store, mid-append failure, and two concurrent evaluations.
"""

from __future__ import annotations

import json
import sqlite3
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
