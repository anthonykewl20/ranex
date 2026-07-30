"""Replay from persisted journal bytes, not from in-memory events.

The previous replay test folded `reduce_execution` over the same in-memory
events that `replay_execution` folds, and compared the two results. That is a
comparison of the production reducer with itself: it cannot fail unless the
wrapper diverges from the function it wraps, so it could not evidence the
Phase 1 exit criterion. These tests replay the recorded `event_json` bytes and
compare against the snapshot, which is the form that can detect encoder loss,
field drift, and a broken digest chain.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from ranex.foundation.identity import Identity
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    ExecutionPersistenceIntegrityError,
    SQLiteExecutionStore,
)
from ranex.governed_execution.domain.events import (
    ExecutionCreated,
    ExecutionMarkedReady,
    ExecutionStarted,
    ExecutionSucceeded,
)
from ranex.governed_execution.domain.status import ExecutionStatus

RUN_ID = Identity.parse(
    "run_01890f47-25a1-7e01-98b3-5f5f6bb25af7", expected_prefix="run"
)
WORK_ITEM_ID = Identity.parse(
    "work_01890f47-25a1-7e02-98b3-5f5f6bb25af7", expected_prefix="work"
)
PRINCIPAL_ID = Identity.parse(
    "principal_01890f47-25a1-7e03-98b3-5f5f6bb25af7", expected_prefix="principal"
)


def event_id(sequence: int) -> Identity:
    return Identity.parse(
        f"transition_01890f47-25a1-7f{sequence:02x}-98b3-5f5f6bb25af7",
        expected_prefix="transition",
    )


@pytest.fixture
def store(tmp_path: Path) -> SQLiteExecutionStore:
    execution_store = SQLiteExecutionStore(tmp_path / "kernel.sqlite3")
    execution_store.initialize()
    return execution_store


@pytest.fixture
def database_path(store: SQLiteExecutionStore, tmp_path: Path) -> Path:
    return tmp_path / "kernel.sqlite3"


def drive_to_success(store: SQLiteExecutionStore) -> None:
    store.append(
        ExecutionCreated(
            event_id=event_id(1),
            execution_id=RUN_ID,
            expected_version=0,
            occurred_at="2026-07-30T02:00:00Z",
            work_item_id=WORK_ITEM_ID,
            created_by_principal_id=PRINCIPAL_ID,
            workflow_request_ref="workflow-request:sha256:replay",
        )
    )
    store.append(
        ExecutionMarkedReady(
            event_id=event_id(2),
            execution_id=RUN_ID,
            expected_version=1,
            occurred_at="2026-07-30T02:00:01Z",
            readiness_snapshot_ref="snapshot:sha256:ready",
        )
    )
    store.append(
        ExecutionStarted(
            event_id=event_id(3),
            execution_id=RUN_ID,
            expected_version=2,
            occurred_at="2026-07-30T02:00:02Z",
            authorization_ref="permit:sha256:start",
        )
    )
    store.append(
        ExecutionSucceeded(
            event_id=event_id(4),
            execution_id=RUN_ID,
            expected_version=3,
            occurred_at="2026-07-30T02:00:03Z",
            outcome_ref="outcome:sha256:success",
        )
    )


def test_replaying_persisted_journal_reproduces_the_snapshot(
    store: SQLiteExecutionStore,
) -> None:
    drive_to_success(store)
    snapshot = store.load(RUN_ID)
    replayed = store.replay_history(RUN_ID)

    assert snapshot is not None
    assert replayed == snapshot
    assert replayed.status is ExecutionStatus.SUCCEEDED
    assert replayed.version == 4


def test_replay_detects_a_corrupted_persisted_event(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    """Encoder loss or field drift must surface, which the old test could not do."""
    drive_to_success(store)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT event_json FROM execution_journal WHERE resulting_version = 1"
        ).fetchone()
        document = json.loads(str(row["event_json"]))
        document["workflow_request_ref"] = "workflow-request:sha256:drifted"
        connection.execute("DROP TRIGGER execution_journal_reject_update")
        connection.execute(
            "UPDATE execution_journal SET event_json = ? WHERE resulting_version = 1",
            (json.dumps(document, separators=(",", ":"), sort_keys=True),),
        )

    with pytest.raises(ExecutionPersistenceIntegrityError) as raised:
        store.replay_history(RUN_ID)
    assert "digest" in str(raised.value)


def test_replay_rejects_an_unknown_persisted_event_type(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    """An event outside the declared union must fail closed, not be treated as a base event."""
    drive_to_success(store)

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT event_json FROM execution_journal WHERE resulting_version = 2"
        ).fetchone()
        document = json.loads(str(row["event_json"]))
        document["event_type"] = "ExecutionForceReady"
        connection.execute("DROP TRIGGER execution_journal_reject_update")
        connection.execute(
            "UPDATE execution_journal SET event_json = ? WHERE resulting_version = 2",
            (json.dumps(document, separators=(",", ":"), sort_keys=True),),
        )

    with pytest.raises(ExecutionPersistenceIntegrityError) as raised:
        store.replay_history(RUN_ID)
    assert "event type" in str(raised.value)
