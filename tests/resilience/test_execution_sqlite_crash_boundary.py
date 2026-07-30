"""Rollback-on-error test. NOT a crash test — see test_execution_crash_recovery.py.

This exercises a SQLite `RAISE(ABORT)` trigger whose exception is caught by the
store's own handler, which issues `ROLLBACK`. That verifies error handling
inside a live process; it does not verify crash durability, because no process
dies and the filesystem is never exposed to an interrupted commit. An
independent audit found the test name over-claimed relative to what its
assertions establish.

Retained deliberately: rollback-on-statement-error is a real property worth
covering. Crash recovery is covered by killing an actual child process with
SIGKILL in test_execution_crash_recovery.py, following SQLite's documented
methodology.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ranex.foundation.identity import Identity
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    SQLiteExecutionStore,
)
from ranex.governed_execution.domain.events import (
    ExecutionCreated,
    ExecutionMarkedReady,
)
from ranex.governed_execution.domain.status import ExecutionStatus

RUN_ID = Identity.parse(
    "run_01890f47-25a1-7a11-98b3-5f5f6bb25af7",
    expected_prefix="run",
)


def identity(prefix: str, suffix: str) -> Identity:
    return Identity.parse(
        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
        expected_prefix=prefix,
    )


def test_failure_between_journal_and_outbox_leaves_no_partial_state(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "crash-boundary.sqlite3"
    store = SQLiteExecutionStore(database_path)
    store.initialize()
    store.append(
        ExecutionCreated(
            event_id=identity("transition", "a12"),
            execution_id=RUN_ID,
            expected_version=0,
            occurred_at="2026-07-29T03:00:00Z",
            work_item_id=identity("work", "a13"),
            created_by_principal_id=identity("principal", "a14"),
            workflow_request_ref="workflow-request:sha256:crash",
        )
    )

    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TRIGGER simulate_crash_before_outbox
            BEFORE INSERT ON execution_outbox
            WHEN NEW.aggregate_version = 2
            BEGIN
                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
            END;
            """
        )

    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
        store.append(
            ExecutionMarkedReady(
                event_id=identity("transition", "a15"),
                execution_id=RUN_ID,
                expected_version=1,
                occurred_at="2026-07-29T03:00:01Z",
                readiness_snapshot_ref="snapshot:sha256:crash-ready",
            )
        )

    unchanged = store.load(RUN_ID)
    assert unchanged is not None
    assert unchanged.status is ExecutionStatus.PROPOSED
    assert unchanged.version == 1
    assert unchanged.last_event_id == identity("transition", "a12")
    assert store.count_journal_entries(RUN_ID) == 1
    assert store.count_outbox_entries(RUN_ID) == 1

    with sqlite3.connect(database_path) as connection:
        absent_everywhere = connection.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM execution_state
                 WHERE last_event_id = ?) +
                (SELECT COUNT(*) FROM execution_journal
                 WHERE event_id = ?) +
                (SELECT COUNT(*) FROM execution_outbox
                 WHERE event_id = ?)
            """,
            (
                str(identity("transition", "a15")),
                str(identity("transition", "a15")),
                str(identity("transition", "a15")),
            ),
        ).fetchone()

    assert absent_everywhere == (0,)
