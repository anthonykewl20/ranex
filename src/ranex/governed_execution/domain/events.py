from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.status import ExecutionStatus


def _require_text(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_identity(value: Identity, *, prefix: str, field: str) -> None:
    if not isinstance(value, Identity) or value.prefix != prefix:
        raise ValueError(f"{field} must be a canonical {prefix!r} identity")


def _require_utc_timestamp(value: str) -> None:
    _require_text(value, field="occurred_at")
    if not value.endswith("Z"):
        raise ValueError("occurred_at must use canonical UTC Z notation")
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as exc:
        raise ValueError("occurred_at must be a valid UTC timestamp") from exc
    if parsed.tzinfo != UTC:
        raise ValueError("occurred_at must be UTC")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionEventMetadata:
    event_id: Identity
    execution_id: Identity
    expected_version: int
    occurred_at: str

    def __post_init__(self) -> None:
        _require_identity(
            self.event_id,
            prefix="transition",
            field="event_id",
        )
        _require_identity(
            self.execution_id,
            prefix="run",
            field="execution_id",
        )
        if (
            isinstance(self.expected_version, bool)
            or not isinstance(self.expected_version, int)
            or self.expected_version < 0
        ):
            raise ValueError("expected_version must be a non-negative integer")
        _require_utc_timestamp(self.occurred_at)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionCreated(ExecutionEventMetadata):
    work_item_id: Identity
    created_by_principal_id: Identity
    workflow_request_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_identity(
            self.work_item_id,
            prefix="work",
            field="work_item_id",
        )
        _require_identity(
            self.created_by_principal_id,
            prefix="principal",
            field="created_by_principal_id",
        )
        _require_text(self.workflow_request_ref, field="workflow_request_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionMarkedReady(ExecutionEventMetadata):
    readiness_snapshot_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(
            self.readiness_snapshot_ref,
            field="readiness_snapshot_ref",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionStarted(ExecutionEventMetadata):
    authorization_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(self.authorization_ref, field="authorization_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionWaited(ExecutionEventMetadata):
    wait_reason_code: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(self.wait_reason_code, field="wait_reason_code")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionResumed(ExecutionEventMetadata):
    signal_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(self.signal_ref, field="signal_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionBlocked(ExecutionEventMetadata):
    block_reason_code: str
    blocking_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(self.block_reason_code, field="block_reason_code")
        if not self.blocking_refs:
            raise ValueError("blocking_refs must not be empty")
        if any(not reference.strip() for reference in self.blocking_refs):
            raise ValueError("blocking_refs must contain non-empty references")
        if self.blocking_refs != tuple(sorted(set(self.blocking_refs))):
            raise ValueError("blocking_refs must be unique and canonically sorted")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionUnblocked(ExecutionEventMetadata):
    target_status: ExecutionStatus
    refreshed_evidence_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.target_status not in {
            ExecutionStatus.READY,
            ExecutionStatus.RUNNING,
            ExecutionStatus.WAITING,
        }:
            raise ValueError("unblock target must be READY, RUNNING, or WAITING")
        _require_text(
            self.refreshed_evidence_ref,
            field="refreshed_evidence_ref",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionSucceeded(ExecutionEventMetadata):
    outcome_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(self.outcome_ref, field="outcome_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionFailed(ExecutionEventMetadata):
    failure_reason_code: str
    evidence_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(
            self.failure_reason_code,
            field="failure_reason_code",
        )
        _require_text(self.evidence_ref, field="evidence_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionCancelled(ExecutionEventMetadata):
    decision_ref: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_text(self.decision_ref, field="decision_ref")


ExecutionEvent = (
    ExecutionCreated
    | ExecutionMarkedReady
    | ExecutionStarted
    | ExecutionWaited
    | ExecutionResumed
    | ExecutionBlocked
    | ExecutionUnblocked
    | ExecutionSucceeded
    | ExecutionFailed
    | ExecutionCancelled
)
