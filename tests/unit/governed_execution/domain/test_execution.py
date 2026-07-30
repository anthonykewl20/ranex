from __future__ import annotations

from dataclasses import replace

import pytest

from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.events import (
    ExecutionBlocked,
    ExecutionCancelled,
    ExecutionCreated,
    ExecutionFailed,
    ExecutionMarkedReady,
    ExecutionResumed,
    ExecutionStarted,
    ExecutionSucceeded,
    ExecutionUnblocked,
    ExecutionWaited,
)
from ranex.governed_execution.domain.execution import (
    LEGAL_STATUS_TRANSITIONS,
    InvalidExecutionTransition,
    reduce_execution,
)
from ranex.governed_execution.domain.status import ExecutionStatus

RUN_ID = Identity.parse(
    "run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7",
    expected_prefix="run",
)
WORK_ITEM_ID = Identity.parse(
    "work_01890f47-25a1-7cc2-98b3-5f5f6bb25af7",
    expected_prefix="work",
)
PRINCIPAL_ID = Identity.parse(
    "principal_01890f47-25a1-7cc3-98b3-5f5f6bb25af7",
    expected_prefix="principal",
)


def transition_id(sequence: int) -> Identity:
    value = f"transition_01890f47-25a1-7d{sequence:02x}-98b3-5f5f6bb25af7"
    return Identity.parse(value, expected_prefix="transition")


def created() -> ExecutionCreated:
    return ExecutionCreated(
        event_id=transition_id(1),
        execution_id=RUN_ID,
        expected_version=0,
        occurred_at="2026-07-29T00:00:00Z",
        work_item_id=WORK_ITEM_ID,
        created_by_principal_id=PRINCIPAL_ID,
        workflow_request_ref="workflow-request:sha256:created",
    )


def ready(*, version: int = 1, sequence: int = 2) -> ExecutionMarkedReady:
    return ExecutionMarkedReady(
        event_id=transition_id(sequence),
        execution_id=RUN_ID,
        expected_version=version,
        occurred_at=f"2026-07-29T00:00:{sequence:02d}Z",
        readiness_snapshot_ref="snapshot:sha256:ready",
    )


def started(*, version: int = 2, sequence: int = 3) -> ExecutionStarted:
    return ExecutionStarted(
        event_id=transition_id(sequence),
        execution_id=RUN_ID,
        expected_version=version,
        occurred_at=f"2026-07-29T00:00:{sequence:02d}Z",
        authorization_ref="authorization:sha256:start",
    )


def test_creation_is_a_reducer_transition_from_no_state() -> None:
    state = reduce_execution(None, created())

    assert state.execution_id == RUN_ID
    assert state.work_item_id == WORK_ITEM_ID
    assert state.status is ExecutionStatus.PROPOSED
    assert state.version == 1
    assert state.last_event_id == transition_id(1)


def test_reducer_is_deterministic_and_does_not_mutate_input() -> None:
    proposed = reduce_execution(None, created())
    original = replace(proposed)
    event = ready()

    first = reduce_execution(proposed, event)
    second = reduce_execution(proposed, event)

    assert first == second
    assert proposed == original
    assert proposed.status is ExecutionStatus.PROPOSED
    assert first.status is ExecutionStatus.READY
    assert first.version == 2


def test_block_and_unblock_restore_the_recorded_prior_status() -> None:
    running = reduce_execution(
        reduce_execution(reduce_execution(None, created()), ready()),
        started(),
    )
    blocked = reduce_execution(
        running,
        ExecutionBlocked(
            event_id=transition_id(4),
            execution_id=RUN_ID,
            expected_version=3,
            occurred_at="2026-07-29T00:00:04Z",
            block_reason_code="POLICY_UNAVAILABLE",
            blocking_refs=("policy:sha256:unavailable",),
        ),
    )

    assert blocked.status is ExecutionStatus.BLOCKED
    assert blocked.blocked_from_status is ExecutionStatus.RUNNING

    unblocked = reduce_execution(
        blocked,
        ExecutionUnblocked(
            event_id=transition_id(5),
            execution_id=RUN_ID,
            expected_version=4,
            occurred_at="2026-07-29T00:00:05Z",
            target_status=ExecutionStatus.RUNNING,
            refreshed_evidence_ref="snapshot:sha256:refreshed",
        ),
    )

    assert unblocked.status is ExecutionStatus.RUNNING
    assert unblocked.blocked_from_status is None
    assert unblocked.version == 5


def test_illegal_transition_fails_without_changing_state() -> None:
    proposed = reduce_execution(None, created())
    original = replace(proposed)

    with pytest.raises(
        InvalidExecutionTransition,
        match="PROPOSED cannot apply ExecutionSucceeded",
    ):
        reduce_execution(
            proposed,
            ExecutionSucceeded(
                event_id=transition_id(2),
                execution_id=RUN_ID,
                expected_version=1,
                occurred_at="2026-07-29T00:00:02Z",
                outcome_ref="outcome:sha256:impossible",
            ),
        )

    assert proposed == original


def test_reducer_rejects_wrong_execution_and_stale_version() -> None:
    proposed = reduce_execution(None, created())
    other_run = Identity.parse(
        "run_01890f47-25a1-7cc4-98b3-5f5f6bb25af7",
        expected_prefix="run",
    )

    with pytest.raises(InvalidExecutionTransition, match="different execution"):
        reduce_execution(proposed, replace(ready(), execution_id=other_run))
    with pytest.raises(InvalidExecutionTransition, match="expected version"):
        reduce_execution(proposed, replace(ready(), expected_version=99))


def test_event_type_cannot_impersonate_a_different_legal_edge() -> None:
    proposed = reduce_execution(None, created())
    ready_state = reduce_execution(proposed, ready())
    running = reduce_execution(ready_state, started())
    blocked = reduce_execution(
        running,
        ExecutionBlocked(
            event_id=transition_id(4),
            execution_id=RUN_ID,
            expected_version=3,
            occurred_at="2026-07-29T00:00:04Z",
            block_reason_code="BLOCKED",
            blocking_refs=("block:ref",),
        ),
    )

    with pytest.raises(InvalidExecutionTransition):
        reduce_execution(
            ready_state,
            ExecutionResumed(
                event_id=transition_id(3),
                execution_id=RUN_ID,
                expected_version=2,
                occurred_at="2026-07-29T00:00:03Z",
                signal_ref="signal:not-a-start",
            ),
        )
    with pytest.raises(InvalidExecutionTransition):
        reduce_execution(blocked, started(version=4, sequence=5))


def test_registered_execution_transition_set_is_exhaustive() -> None:
    assert (
        frozenset(
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
        == LEGAL_STATUS_TRANSITIONS
    )


@pytest.mark.parametrize(
    ("build_state", "event_type", "target"),
    [
        ("proposed", ExecutionCancelled, ExecutionStatus.CANCELLED),
        ("ready", ExecutionCancelled, ExecutionStatus.CANCELLED),
        ("running", ExecutionWaited, ExecutionStatus.WAITING),
        ("running", ExecutionSucceeded, ExecutionStatus.SUCCEEDED),
        ("running", ExecutionFailed, ExecutionStatus.FAILED),
        ("running", ExecutionCancelled, ExecutionStatus.CANCELLED),
        ("waiting", ExecutionResumed, ExecutionStatus.RUNNING),
        ("waiting", ExecutionFailed, ExecutionStatus.FAILED),
        ("waiting", ExecutionCancelled, ExecutionStatus.CANCELLED),
        ("blocked", ExecutionFailed, ExecutionStatus.FAILED),
        ("blocked", ExecutionCancelled, ExecutionStatus.CANCELLED),
    ],
)
def test_reducer_computes_each_non_blocking_transition_family(
    build_state: str,
    event_type: type,
    target: ExecutionStatus,
) -> None:
    states = _states_for_transition_examples()
    state = states[build_state]
    event = _event_for(event_type, state.version)

    assert reduce_execution(state, event).status is target


def _states_for_transition_examples() -> dict[str, object]:
    proposed = reduce_execution(None, created())
    ready_state = reduce_execution(proposed, ready())
    running = reduce_execution(ready_state, started())
    waiting = reduce_execution(
        running,
        ExecutionWaited(
            event_id=transition_id(4),
            execution_id=RUN_ID,
            expected_version=3,
            occurred_at="2026-07-29T00:00:04Z",
            wait_reason_code="AWAITING_SIGNAL",
        ),
    )
    blocked = reduce_execution(
        running,
        ExecutionBlocked(
            event_id=transition_id(4),
            execution_id=RUN_ID,
            expected_version=3,
            occurred_at="2026-07-29T00:00:04Z",
            block_reason_code="BLOCKED",
            blocking_refs=("block:ref",),
        ),
    )
    return {
        "proposed": proposed,
        "ready": ready_state,
        "running": running,
        "waiting": waiting,
        "blocked": blocked,
    }


def _event_for(event_type: type, version: int) -> object:
    common = {
        "event_id": transition_id(version + 1),
        "execution_id": RUN_ID,
        "expected_version": version,
        "occurred_at": f"2026-07-29T00:00:{version + 1:02d}Z",
    }
    if event_type is ExecutionCancelled:
        return ExecutionCancelled(**common, decision_ref="decision:cancel")
    if event_type is ExecutionWaited:
        return ExecutionWaited(**common, wait_reason_code="WAIT")
    if event_type is ExecutionResumed:
        return ExecutionResumed(**common, signal_ref="signal:resolved")
    if event_type is ExecutionSucceeded:
        return ExecutionSucceeded(**common, outcome_ref="outcome:succeeded")
    if event_type is ExecutionFailed:
        return ExecutionFailed(
            **common,
            failure_reason_code="FAILED",
            evidence_ref="evidence:failure",
        )
    raise AssertionError(f"unsupported test event type: {event_type}")
