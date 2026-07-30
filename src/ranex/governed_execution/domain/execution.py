from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace

from ranex.foundation.identity import Identity
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
from ranex.governed_execution.domain.status import ExecutionStatus


class InvalidExecutionTransition(ValueError):
    """An event cannot evolve the supplied execution state."""


LEGAL_STATUS_TRANSITIONS = frozenset(
    {
        (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
        (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
        (ExecutionStatus.READY, ExecutionStatus.RUNNING),
        (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
        (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
        (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
        (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
        (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
        (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
        (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
        (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
        (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
        (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
        (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
        (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
        (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    }
)


@dataclass(frozen=True, slots=True)
class Execution:
    execution_id: Identity
    work_item_id: Identity
    created_by_principal_id: Identity
    workflow_request_ref: str
    status: ExecutionStatus
    version: int
    last_event_id: Identity
    updated_at: str
    blocked_from_status: ExecutionStatus | None = None


def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    return InvalidExecutionTransition(
        f"{state.status.value} cannot apply {type(event).__name__}"
    )


def _advance(
    state: Execution,
    event: ExecutionEvent,
    target_status: ExecutionStatus,
    *,
    blocked_from_status: ExecutionStatus | None = None,
) -> Execution:
    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
        raise _invalid(state, event)
    return replace(
        state,
        status=target_status,
        version=state.version + 1,
        last_event_id=event.event_id,
        updated_at=event.occurred_at,
        blocked_from_status=blocked_from_status,
    )


def _require_source(
    state: Execution,
    event: ExecutionEvent,
    allowed: frozenset[ExecutionStatus],
) -> None:
    if state.status not in allowed:
        raise _invalid(state, event)


def reduce_execution(
    current: Execution | None,
    event: ExecutionEvent,
) -> Execution:
    """Purely compute the next immutable Execution from one event."""
    if current is None:
        if not isinstance(event, ExecutionCreated):
            raise InvalidExecutionTransition(
                f"no execution can apply {type(event).__name__}"
            )
        if event.expected_version != 0:
            raise InvalidExecutionTransition(
                "ExecutionCreated expected version must be zero"
            )
        return Execution(
            execution_id=event.execution_id,
            work_item_id=event.work_item_id,
            created_by_principal_id=event.created_by_principal_id,
            workflow_request_ref=event.workflow_request_ref,
            status=ExecutionStatus.PROPOSED,
            version=1,
            last_event_id=event.event_id,
            updated_at=event.occurred_at,
        )

    if isinstance(event, ExecutionCreated):
        raise _invalid(current, event)
    if event.execution_id != current.execution_id:
        raise InvalidExecutionTransition("event targets a different execution")
    if event.expected_version != current.version:
        raise InvalidExecutionTransition(
            "event expected version does not match execution version"
        )
    if event.event_id == current.last_event_id:
        raise InvalidExecutionTransition("last event cannot be applied twice")

    if isinstance(event, ExecutionMarkedReady):
        _require_source(
            current,
            event,
            frozenset({ExecutionStatus.PROPOSED}),
        )
        return _advance(current, event, ExecutionStatus.READY)
    if isinstance(event, ExecutionStarted):
        _require_source(
            current,
            event,
            frozenset({ExecutionStatus.READY}),
        )
        return _advance(current, event, ExecutionStatus.RUNNING)
    if isinstance(event, ExecutionWaited):
        _require_source(
            current,
            event,
            frozenset({ExecutionStatus.RUNNING}),
        )
        return _advance(current, event, ExecutionStatus.WAITING)
    if isinstance(event, ExecutionResumed):
        _require_source(
            current,
            event,
            frozenset({ExecutionStatus.WAITING}),
        )
        return _advance(current, event, ExecutionStatus.RUNNING)
    if isinstance(event, ExecutionBlocked):
        _require_source(
            current,
            event,
            frozenset(
                {
                    ExecutionStatus.READY,
                    ExecutionStatus.RUNNING,
                    ExecutionStatus.WAITING,
                }
            ),
        )
        return _advance(
            current,
            event,
            ExecutionStatus.BLOCKED,
            blocked_from_status=current.status,
        )
    if isinstance(event, ExecutionUnblocked):
        if (
            current.status is not ExecutionStatus.BLOCKED
            or current.blocked_from_status is not event.target_status
        ):
            raise _invalid(current, event)
        return _advance(current, event, event.target_status)
    if isinstance(event, ExecutionSucceeded):
        _require_source(
            current,
            event,
            frozenset({ExecutionStatus.RUNNING}),
        )
        return _advance(current, event, ExecutionStatus.SUCCEEDED)
    if isinstance(event, ExecutionFailed):
        _require_source(
            current,
            event,
            frozenset(
                {
                    ExecutionStatus.RUNNING,
                    ExecutionStatus.WAITING,
                    ExecutionStatus.BLOCKED,
                }
            ),
        )
        return _advance(current, event, ExecutionStatus.FAILED)
    if isinstance(event, ExecutionCancelled):
        _require_source(
            current,
            event,
            frozenset(
                {
                    ExecutionStatus.PROPOSED,
                    ExecutionStatus.READY,
                    ExecutionStatus.RUNNING,
                    ExecutionStatus.WAITING,
                    ExecutionStatus.BLOCKED,
                }
            ),
        )
        return _advance(current, event, ExecutionStatus.CANCELLED)
    raise TypeError(f"unsupported execution event: {type(event).__name__}")


def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
    """Replay an ordered history through the same production reducer."""
    state: Execution | None = None
    seen_event_ids: set[Identity] = set()
    for event in events:
        if event.event_id in seen_event_ids:
            raise InvalidExecutionTransition("event identity is duplicated in history")
        seen_event_ids.add(event.event_id)
        state = reduce_execution(state, event)
    if state is None:
        raise InvalidExecutionTransition("execution history must not be empty")
    return state
