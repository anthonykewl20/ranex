from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from ranex.foundation.canonical import canonical_json
from ranex.foundation.identity import Identity
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    ExecutionPersistenceIntegrityError,
    SQLiteExecutionStore,
    _execution_to_document,
)
from ranex.governed_execution.domain.events import (
    ExecutionCreated,
    ExecutionMarkedReady,
)
from ranex.governed_execution.domain.execution import Execution
from ranex.governed_execution.domain.status import ExecutionStatus

RUN_ID = Identity.parse(
    "run_01890f47-25a1-7e01-98b3-5f5f6bb25af7",
    expected_prefix="run",
)
WORK_ITEM_ID = Identity.parse(
    "work_01890f47-25a1-7e02-98b3-5f5f6bb25af7",
    expected_prefix="work",
)
PRINCIPAL_ID = Identity.parse(
    "principal_01890f47-25a1-7e03-98b3-5f5f6bb25af7",
    expected_prefix="principal",
)


def event_id(sequence: int) -> Identity:
    return Identity.parse(
        f"transition_01890f47-25a1-7f{sequence:02x}-98b3-5f5f6bb25af7",
        expected_prefix="transition",
    )


def create_event() -> ExecutionCreated:
    return ExecutionCreated(
        event_id=event_id(1),
        execution_id=RUN_ID,
        expected_version=0,
        occurred_at="2026-07-29T02:00:00Z",
        work_item_id=WORK_ITEM_ID,
        created_by_principal_id=PRINCIPAL_ID,
        workflow_request_ref="workflow-request:sha256:sqlite",
    )


def ready_event() -> ExecutionMarkedReady:
    return ExecutionMarkedReady(
        event_id=event_id(2),
        execution_id=RUN_ID,
        expected_version=1,
        occurred_at="2026-07-29T02:00:01Z",
        readiness_snapshot_ref="snapshot:sha256:sqlite-ready",
    )


@pytest.fixture
def database_path(tmp_path: Path) -> Path:
    return tmp_path / "kernel.sqlite3"


@pytest.fixture
def store(database_path: Path) -> SQLiteExecutionStore:
    execution_store = SQLiteExecutionStore(database_path)
    execution_store.initialize()
    return execution_store


def test_transition_commits_canonical_state_version_journal_and_outbox_together(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    proposed = store.append(create_event())
    ready = store.append(ready_event())

    assert proposed.status is ExecutionStatus.PROPOSED
    assert proposed.version == 1
    assert ready.status is ExecutionStatus.READY
    assert ready.version == 2
    assert store.load(RUN_ID) == ready

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        state_row = connection.execute(
            """
            SELECT canonical_state_json, version, last_event_id
            FROM execution_state
            WHERE execution_id = ?
            """,
            (str(RUN_ID),),
        ).fetchone()
        journal_rows = connection.execute(
            """
            SELECT event_id, previous_version, resulting_version,
                   event_json, resulting_state_json
            FROM execution_journal
            ORDER BY sequence
            """
        ).fetchall()
        outbox_rows = connection.execute(
            """
            SELECT event_id, aggregate_version, payload_json
            FROM execution_outbox
            ORDER BY sequence
            """
        ).fetchall()

    assert state_row is not None
    state_document = json.loads(state_row["canonical_state_json"])
    assert state_row["canonical_state_json"] == canonical_json(state_document)
    assert state_row["version"] == state_document["version"] == 2
    assert state_row["last_event_id"] == str(event_id(2))

    assert [
        (row["event_id"], row["previous_version"], row["resulting_version"])
        for row in journal_rows
    ] == [
        (str(event_id(1)), 0, 1),
        (str(event_id(2)), 1, 2),
    ]
    assert all(
        row["event_json"] == canonical_json(json.loads(row["event_json"]))
        and row["resulting_state_json"]
        == canonical_json(json.loads(row["resulting_state_json"]))
        for row in journal_rows
    )

    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
        (str(event_id(1)), 1),
        (str(event_id(2)), 2),
    ]
    assert all(
        row["payload_json"] == canonical_json(json.loads(row["payload_json"]))
        for row in outbox_rows
    )


def test_journal_is_database_enforced_append_only(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    store.append(create_event())

    with sqlite3.connect(database_path) as connection:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            connection.execute("DELETE FROM execution_journal")


def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
    store: SQLiteExecutionStore,
) -> None:
    store.append(create_event())
    store.append(ready_event())

    with pytest.raises(ValueError, match="expected version"):
        store.append(ready_event())

    assert store.count_journal_entries(RUN_ID) == 2
    assert store.count_outbox_entries(RUN_ID) == 2


def test_load_rejects_relational_and_canonical_version_disagreement(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    store.append(create_event())
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE execution_state SET version = 99 WHERE execution_id = ?",
            (str(RUN_ID),),
        )

    with pytest.raises(
        ExecutionPersistenceIntegrityError,
        match="version disagrees",
    ):
        store.load(RUN_ID)


def test_load_rejects_relational_and_canonical_identity_disagreement(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    store.append(create_event())
    with sqlite3.connect(database_path) as connection:
        raw = connection.execute(
            """
            SELECT canonical_state_json
            FROM execution_state
            WHERE execution_id = ?
            """,
            (str(RUN_ID),),
        ).fetchone()
        assert raw is not None
        document = json.loads(raw[0])
        document["execution_id"] = str(
            Identity.parse(
                "run_01890f47-25a1-7e09-98b3-5f5f6bb25af7",
                expected_prefix="run",
            )
        )
        connection.execute(
            """
            UPDATE execution_state
            SET canonical_state_json = ?
            WHERE execution_id = ?
            """,
            (canonical_json(document), str(RUN_ID)),
        )

    with pytest.raises(
        ExecutionPersistenceIntegrityError,
        match="identity disagrees",
    ):
        store.load(RUN_ID)


def test_concurrent_same_version_transitions_have_one_cas_winner(
    store: SQLiteExecutionStore,
) -> None:
    store.append(create_event())
    barrier = Barrier(2)

    def attempt() -> Execution | Exception:
        barrier.wait()
        try:
            return store.append(ready_event())
        except Exception as exc:
            return exc

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = tuple(executor.map(lambda _index: attempt(), range(2)))

    assert sum(isinstance(result, Execution) for result in results) == 1
    assert sum(isinstance(result, Exception) for result in results) == 1
    assert store.load(RUN_ID).version == 2  # type: ignore[union-attr]
    assert store.count_journal_entries(RUN_ID) == 2
    assert store.count_outbox_entries(RUN_ID) == 2


def _journal_head_digest(database_path: Path) -> str:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        return str(
            connection.execute(
                """
                SELECT resulting_state_sha256
                FROM execution_journal
                WHERE execution_id = ?
                ORDER BY resulting_version DESC
                LIMIT 1
                """,
                (str(RUN_ID),),
            ).fetchone()["resulting_state_sha256"]
        )


def test_load_blocks_internally_consistent_snapshot_forgery(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    """A forged snapshot that passes every row-internal check must still block.

    HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md section 8.3 requires that a
    current-row/journal mismatch is corruption and blocks advancement. This is
    the exact attack an independent adversarial audit executed successfully
    against the previous implementation: rewrite canonical_state_json, version
    and last_event_id together so the row agrees with itself, and load()
    returned the forged state.
    """
    store.append(create_event())
    store.append(ready_event())
    honest = store.load(RUN_ID)
    assert honest is not None
    assert honest.status is ExecutionStatus.READY
    assert honest.version == 2

    document = json.loads(canonical_json(_execution_to_document(honest)))
    document["status"] = ExecutionStatus.SUCCEEDED.value
    document["version"] = 99
    document["last_event_id"] = str(event_id(0x5A))
    forged = canonical_json(document)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            UPDATE execution_state
            SET canonical_state_json = ?, version = ?, last_event_id = ?
            WHERE execution_id = ?
            """,
            (forged, 99, str(event_id(0x5A)), str(RUN_ID)),
        )

    with pytest.raises(ExecutionPersistenceIntegrityError) as raised:
        store.load(RUN_ID)
    assert "journal" in str(raised.value)


def test_load_blocks_snapshot_whose_digest_diverges_from_journal(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    """Version and event identity may agree while the state itself does not."""
    store.append(create_event())
    store.append(ready_event())
    loaded = store.load(RUN_ID)
    assert loaded is not None

    document = json.loads(canonical_json(_execution_to_document(loaded)))
    document["workflow_request_ref"] = "workflow-request:sha256:tampered"
    tampered = canonical_json(document)

    with sqlite3.connect(database_path) as connection:
        connection.execute(
            "UPDATE execution_state SET canonical_state_json = ? WHERE execution_id = ?",
            (tampered, str(RUN_ID)),
        )

    with pytest.raises(ExecutionPersistenceIntegrityError) as raised:
        store.load(RUN_ID)
    assert "digest" in str(raised.value)


def test_journal_deletion_is_rejected_by_the_append_only_trigger(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    """First line of defence: the journal refuses row deletion outright."""
    store.append(create_event())
    store.append(ready_event())

    with pytest.raises(sqlite3.IntegrityError, match="append-only"):
        with sqlite3.connect(database_path) as connection:
            connection.execute(
                "DELETE FROM execution_journal WHERE execution_id = ?",
                (str(RUN_ID),),
            )


def test_load_blocks_truncated_journal_even_without_the_trigger(
    store: SQLiteExecutionStore,
    database_path: Path,
) -> None:
    """Second line of defence: the mismatch gate catches truncation anyway.

    An attacker able to write the database file can also drop the append-only
    triggers, which an independent audit raised as the counter-argument to
    relying on them. The section 8.3 mismatch gate must therefore still block,
    so that trigger removal alone does not yield a loadable forged history.
    """
    store.append(create_event())
    store.append(ready_event())
    assert _journal_head_digest(database_path)

    with sqlite3.connect(database_path) as connection:
        connection.execute("DROP TRIGGER execution_journal_reject_delete")
        connection.execute(
            "DELETE FROM execution_journal WHERE execution_id = ? AND resulting_version = 2",
            (str(RUN_ID),),
        )

    with pytest.raises(ExecutionPersistenceIntegrityError):
        store.load(RUN_ID)
