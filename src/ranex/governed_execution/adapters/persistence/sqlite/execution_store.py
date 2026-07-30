from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from contextlib import closing
from pathlib import Path

from ranex.foundation.canonical import canonical_json, canonical_sha256
from ranex.foundation.identity import Identity
from ranex.governed_execution.application.ports.execution_repository import (
    ExecutionRepository,
)
from ranex.governed_execution.domain.events import (
    ExecutionBlocked,
    ExecutionCancelled,
    ExecutionCreated,
    ExecutionEvent,
    ExecutionFailed,
    ExecutionMarkedReady,
    ExecutionResumed,
    ExecutionStarted,
    ExecutionSucceeded,
    ExecutionUnblocked,
    ExecutionWaited,
)
from ranex.governed_execution.domain.execution import (
    Execution,
    reduce_execution,
)
from ranex.governed_execution.domain.status import ExecutionStatus

_MIGRATION = Path(__file__).with_name("migrations") / "001_execution_kernel.sql"
_STATE_FIELDS = frozenset(
    {
        "schema_version",
        "execution_id",
        "work_item_id",
        "created_by_principal_id",
        "workflow_request_ref",
        "status",
        "version",
        "last_event_id",
        "updated_at",
        "blocked_from_status",
    }
)


class ExecutionPersistenceIntegrityError(RuntimeError):
    """Stored execution bytes disagree with their relational metadata."""


class ConcurrentExecutionWriteError(RuntimeError):
    """The expected canonical execution version changed before commit."""


def _execution_to_document(execution: Execution) -> dict[str, object]:
    return {
        "schema_version": "execution-state/v1",
        "execution_id": str(execution.execution_id),
        "work_item_id": str(execution.work_item_id),
        "created_by_principal_id": str(execution.created_by_principal_id),
        "workflow_request_ref": execution.workflow_request_ref,
        "status": execution.status.value,
        "version": execution.version,
        "last_event_id": str(execution.last_event_id),
        "updated_at": execution.updated_at,
        "blocked_from_status": (
            execution.blocked_from_status.value
            if execution.blocked_from_status is not None
            else None
        ),
    }


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _execution_from_document(document: Mapping[str, object]) -> Execution:
    if set(document) != _STATE_FIELDS:
        raise ValueError("canonical execution state has unexpected fields")
    if document["schema_version"] != "execution-state/v1":
        raise ValueError("unsupported execution state schema version")
    version = document["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("execution state version must be a positive integer")
    blocked_from_value = document["blocked_from_status"]
    blocked_from = (
        None
        if blocked_from_value is None
        else ExecutionStatus(_require_string(blocked_from_value, "blocked_from_status"))
    )
    return Execution(
        execution_id=Identity.parse(
            _require_string(document["execution_id"], "execution_id"),
            expected_prefix="run",
        ),
        work_item_id=Identity.parse(
            _require_string(document["work_item_id"], "work_item_id"),
            expected_prefix="work",
        ),
        created_by_principal_id=Identity.parse(
            _require_string(
                document["created_by_principal_id"],
                "created_by_principal_id",
            ),
            expected_prefix="principal",
        ),
        workflow_request_ref=_require_string(
            document["workflow_request_ref"],
            "workflow_request_ref",
        ),
        status=ExecutionStatus(_require_string(document["status"], "status")),
        version=version,
        last_event_id=Identity.parse(
            _require_string(document["last_event_id"], "last_event_id"),
            expected_prefix="transition",
        ),
        updated_at=_require_string(document["updated_at"], "updated_at"),
        blocked_from_status=blocked_from,
    )


_EVENT_TYPES: Mapping[str, type[ExecutionEvent]] = {
    "ExecutionCreated": ExecutionCreated,
    "ExecutionMarkedReady": ExecutionMarkedReady,
    "ExecutionStarted": ExecutionStarted,
    "ExecutionWaited": ExecutionWaited,
    "ExecutionResumed": ExecutionResumed,
    "ExecutionBlocked": ExecutionBlocked,
    "ExecutionUnblocked": ExecutionUnblocked,
    "ExecutionSucceeded": ExecutionSucceeded,
    "ExecutionFailed": ExecutionFailed,
    "ExecutionCancelled": ExecutionCancelled,
}

_EVENT_IDENTITY_FIELDS: Mapping[str, str] = {
    "work_item_id": "work",
    "created_by_principal_id": "principal",
}


def _event_from_document(document: Mapping[str, object]) -> ExecutionEvent:
    """Rebuild an event from its persisted canonical document.

    The inverse of `_event_to_document`. Without it a replay test cannot read
    the journal at all, which is why the previous replay test could only fold
    the same in-memory events through the same reducer and compare the result
    with itself. Replay of persisted bytes is the only form that can detect
    encoder loss, field drift, or a broken digest chain.
    """
    if document.get("schema_version") != "execution-event/v1":
        raise ExecutionPersistenceIntegrityError(
            "journal event has an unsupported schema version"
        )
    event_type = document.get("event_type")
    if not isinstance(event_type, str) or event_type not in _EVENT_TYPES:
        raise ExecutionPersistenceIntegrityError(
            "journal event has an unknown event type"
        )
    cls = _EVENT_TYPES[event_type]
    payload: dict[str, object] = {
        "event_id": Identity.parse(
            str(document["event_id"]), expected_prefix="transition"
        ),
        "execution_id": Identity.parse(
            str(document["execution_id"]), expected_prefix="run"
        ),
        "expected_version": document["expected_version"],
        "occurred_at": document["occurred_at"],
    }
    known = set(payload) | {"schema_version", "event_type"}
    for name, value in document.items():
        if name in known:
            continue
        if name in _EVENT_IDENTITY_FIELDS:
            payload[name] = Identity.parse(
                str(value), expected_prefix=_EVENT_IDENTITY_FIELDS[name]
            )
        elif name == "target_status":
            payload[name] = ExecutionStatus(str(value))
        elif name == "blocking_refs":
            if not isinstance(value, list):
                raise ExecutionPersistenceIntegrityError(
                    "journal event blocking_refs is not a list"
                )
            payload[name] = tuple(str(item) for item in value)
        else:
            payload[name] = value
    try:
        return cls(**payload)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ExecutionPersistenceIntegrityError(
            "journal event does not satisfy its event contract"
        ) from exc


def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
    document: dict[str, object] = {
        "schema_version": "execution-event/v1",
        "event_type": type(event).__name__,
        "event_id": str(event.event_id),
        "execution_id": str(event.execution_id),
        "expected_version": event.expected_version,
        "occurred_at": event.occurred_at,
    }
    if isinstance(event, ExecutionCreated):
        document.update(
            {
                "work_item_id": str(event.work_item_id),
                "created_by_principal_id": str(event.created_by_principal_id),
                "workflow_request_ref": event.workflow_request_ref,
            }
        )
    elif isinstance(event, ExecutionMarkedReady):
        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
    elif isinstance(event, ExecutionStarted):
        document["authorization_ref"] = event.authorization_ref
    elif isinstance(event, ExecutionWaited):
        document["wait_reason_code"] = event.wait_reason_code
    elif isinstance(event, ExecutionResumed):
        document["signal_ref"] = event.signal_ref
    elif isinstance(event, ExecutionBlocked):
        document.update(
            {
                "block_reason_code": event.block_reason_code,
                "blocking_refs": list(event.blocking_refs),
            }
        )
    elif isinstance(event, ExecutionUnblocked):
        document.update(
            {
                "target_status": event.target_status.value,
                "refreshed_evidence_ref": event.refreshed_evidence_ref,
            }
        )
    elif isinstance(event, ExecutionSucceeded):
        document["outcome_ref"] = event.outcome_ref
    elif isinstance(event, ExecutionFailed):
        document.update(
            {
                "failure_reason_code": event.failure_reason_code,
                "evidence_ref": event.evidence_ref,
            }
        )
    elif isinstance(event, ExecutionCancelled):
        document["decision_ref"] = event.decision_ref
    else:
        raise TypeError(f"unsupported execution event: {type(event).__name__}")
    return document


class SQLiteExecutionStore(ExecutionRepository):
    """State, audit journal, and outbox committed in one SQLite transaction."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._path,
            isolation_level=None,
            timeout=5.0,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        return connection

    def initialize(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        migration = _MIGRATION.read_text(encoding="utf-8")
        connection = self._connect()
        try:
            connection.executescript(migration)
        finally:
            connection.close()
        self._path.chmod(0o600)

    def load(self, execution_id: Identity) -> Execution | None:
        self._require_run_id(execution_id)
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT execution_id, canonical_state_json, version, last_event_id
                FROM execution_state
                WHERE execution_id = ?
                """,
                (str(execution_id),),
            ).fetchone()
            if row is None:
                return None
            state = self._decode_state_row(row)
            self._require_journal_agreement(connection, row, state)
        return state

    @staticmethod
    def _require_journal_agreement(
        connection: sqlite3.Connection,
        row: sqlite3.Row,
        state: Execution,
    ) -> None:
        """Reject a snapshot that disagrees with the append-only journal.

        The architecture declares a dual model: the current row is the
        operational read source and the ordered journal is the replay and
        audit oracle, snapshots never replace the journal, and a
        current-row/journal mismatch is corruption that blocks advancement
        (HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md section 8.3).

        Row-internal checks in `_decode_state_row` cannot satisfy that
        obligation: a forger who rewrites `canonical_state_json`, `version`
        and `last_event_id` together passes every one of them. Agreement is
        only demonstrable against the journal, which independently records
        the resulting version, the canonical state digest and the event
        identity for each transition.
        """
        head = connection.execute(
            """
            SELECT resulting_version, resulting_state_sha256, event_id
            FROM execution_journal
            WHERE execution_id = ?
            ORDER BY resulting_version DESC
            LIMIT 1
            """,
            (str(state.execution_id),),
        ).fetchone()
        if head is None:
            raise ExecutionPersistenceIntegrityError(
                "execution state has no journal history"
            )
        if int(head["resulting_version"]) != state.version:
            raise ExecutionPersistenceIntegrityError(
                "execution state version disagrees with journal head version"
            )
        if str(head["event_id"]) != str(state.last_event_id):
            raise ExecutionPersistenceIntegrityError(
                "execution state last event disagrees with journal head event"
            )
        snapshot_digest = canonical_sha256(
            json.loads(str(row["canonical_state_json"]))
        )
        if str(head["resulting_state_sha256"]) != snapshot_digest:
            raise ExecutionPersistenceIntegrityError(
                "execution state digest disagrees with journal head digest"
            )
        gap = connection.execute(
            """
            SELECT COUNT(*) AS present
            FROM execution_journal
            WHERE execution_id = ?
            """,
            (str(state.execution_id),),
        ).fetchone()
        if int(gap["present"]) != state.version:
            raise ExecutionPersistenceIntegrityError(
                "journal row count disagrees with execution state version"
            )

    def replay_history(self, execution_id: Identity) -> Execution:
        """Rebuild state by replaying the persisted journal, ignoring the snapshot.

        This is the verify-or-rebuild control: the journal is the replay and
        audit oracle, and replaying its recorded bytes must reproduce the
        snapshot. Because it decodes `event_json` rather than reusing
        in-memory events, it can detect encoder loss, field drift, and a
        broken digest chain that a same-reducer comparison cannot.
        """
        self._require_run_id(execution_id)
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT event_json, resulting_version, resulting_state_sha256
                FROM execution_journal
                WHERE execution_id = ?
                ORDER BY resulting_version ASC
                """,
                (str(execution_id),),
            ).fetchall()
        if not rows:
            raise ExecutionPersistenceIntegrityError(
                "execution has no journal history to replay"
            )
        state: Execution | None = None
        for expected_version, row in enumerate(rows, start=1):
            if int(row["resulting_version"]) != expected_version:
                raise ExecutionPersistenceIntegrityError(
                    "journal history has a version gap"
                )
            event = _event_from_document(json.loads(str(row["event_json"])))
            state = reduce_execution(state, event)
            if canonical_sha256(_execution_to_document(state)) != str(
                row["resulting_state_sha256"]
            ):
                raise ExecutionPersistenceIntegrityError(
                    "replayed state digest disagrees with journal digest"
                )
        assert state is not None
        return state

    def append(self, event: ExecutionEvent) -> Execution:
        connection = self._connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            current_row = connection.execute(
                """
                SELECT execution_id, canonical_state_json, version, last_event_id
                FROM execution_state
                WHERE execution_id = ?
                """,
                (str(event.execution_id),),
            ).fetchone()
            current = (
                None if current_row is None else self._decode_state_row(current_row)
            )
            next_state = reduce_execution(current, event)
            next_document = _execution_to_document(next_state)
            next_json = canonical_json(next_document)

            if current is None:
                connection.execute(
                    """
                    INSERT INTO execution_state(
                        execution_id,
                        canonical_state_json,
                        version,
                        last_event_id,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(next_state.execution_id),
                        next_json,
                        next_state.version,
                        str(next_state.last_event_id),
                        next_state.updated_at,
                    ),
                )
                previous_json = None
                previous_version = 0
            else:
                assert current_row is not None
                previous_json = str(current_row["canonical_state_json"])
                previous_version = current.version
                cursor = connection.execute(
                    """
                    UPDATE execution_state
                    SET canonical_state_json = ?,
                        version = ?,
                        last_event_id = ?,
                        updated_at = ?
                    WHERE execution_id = ?
                      AND version = ?
                      AND canonical_state_json = ?
                    """,
                    (
                        next_json,
                        next_state.version,
                        str(next_state.last_event_id),
                        next_state.updated_at,
                        str(next_state.execution_id),
                        current.version,
                        previous_json,
                    ),
                )
                if cursor.rowcount != 1:
                    raise ConcurrentExecutionWriteError(
                        "canonical execution compare-and-swap failed"
                    )

            event_document = _event_to_document(event)
            event_json = canonical_json(event_document)
            resulting_digest = canonical_sha256(next_document)
            previous_digest = (
                None
                if previous_json is None
                else canonical_sha256(json.loads(previous_json))
            )
            connection.execute(
                """
                INSERT INTO execution_journal(
                    event_id,
                    execution_id,
                    event_type,
                    previous_version,
                    resulting_version,
                    event_json,
                    previous_state_sha256,
                    resulting_state_sha256,
                    resulting_state_json,
                    recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(event.event_id),
                    str(event.execution_id),
                    type(event).__name__,
                    previous_version,
                    next_state.version,
                    event_json,
                    previous_digest,
                    resulting_digest,
                    next_json,
                    event.occurred_at,
                ),
            )

            outbox_document = {
                "schema_version": "execution-outbox/v1",
                "event_id": str(event.event_id),
                "event_type": type(event).__name__,
                "execution_id": str(event.execution_id),
                "aggregate_version": next_state.version,
                "occurred_at": event.occurred_at,
                "event": event_document,
            }
            connection.execute(
                """
                INSERT INTO execution_outbox(
                    event_id,
                    execution_id,
                    aggregate_version,
                    payload_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(event.event_id),
                    str(event.execution_id),
                    next_state.version,
                    canonical_json(outbox_document),
                    event.occurred_at,
                ),
            )
            connection.execute("COMMIT")
            return next_state
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def count_journal_entries(self, execution_id: Identity) -> int:
        return self._count_rows("execution_journal", execution_id)

    def count_outbox_entries(self, execution_id: Identity) -> int:
        return self._count_rows("execution_outbox", execution_id)

    def _count_rows(self, table: str, execution_id: Identity) -> int:
        self._require_run_id(execution_id)
        if table not in {"execution_journal", "execution_outbox"}:
            raise ValueError("unsupported execution table")
        with closing(self._connect()) as connection:
            row = connection.execute(
                f"SELECT COUNT(*) AS count FROM {table} WHERE execution_id = ?",
                (str(execution_id),),
            ).fetchone()
        assert row is not None
        return int(row["count"])

    @staticmethod
    def _require_run_id(execution_id: Identity) -> None:
        if not isinstance(execution_id, Identity) or execution_id.prefix != "run":
            raise ValueError("execution_id must be a canonical run identity")

    @staticmethod
    def _decode_state_row(row: sqlite3.Row) -> Execution:
        raw = str(row["canonical_state_json"])
        try:
            document = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ExecutionPersistenceIntegrityError(
                "canonical execution state is not JSON"
            ) from exc
        if not isinstance(document, dict) or canonical_json(document) != raw:
            raise ExecutionPersistenceIntegrityError(
                "execution state is not canonically serialized"
            )
        try:
            state = _execution_from_document(document)
        except (TypeError, ValueError) as exc:
            raise ExecutionPersistenceIntegrityError(
                "canonical execution state is invalid"
            ) from exc
        if int(row["version"]) != state.version:
            raise ExecutionPersistenceIntegrityError(
                "relational version disagrees with canonical state version"
            )
        if str(row["last_event_id"]) != str(state.last_event_id):
            raise ExecutionPersistenceIntegrityError(
                "relational last event disagrees with canonical state"
            )
        if str(row["execution_id"]) != str(state.execution_id):
            raise ExecutionPersistenceIntegrityError(
                "relational identity disagrees with canonical state identity"
            )
        return state
