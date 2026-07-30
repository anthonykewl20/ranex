from __future__ import annotations

from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.events import (
    ExecutionCreated,
    ExecutionMarkedReady,
    ExecutionStarted,
    ExecutionSucceeded,
)
from ranex.governed_execution.domain.execution import (
    reduce_execution,
    replay_execution,
)
from ranex.governed_execution.domain.status import ExecutionStatus


def identity(prefix: str, suffix: str) -> Identity:
    return Identity.parse(
        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
        expected_prefix=prefix,
    )


def test_replay_reproduces_identical_final_state_and_version() -> None:
    run_id = identity("run", "a01")
    events = (
        ExecutionCreated(
            event_id=identity("transition", "b01"),
            execution_id=run_id,
            expected_version=0,
            occurred_at="2026-07-29T01:00:00Z",
            work_item_id=identity("work", "a02"),
            created_by_principal_id=identity("principal", "a03"),
            workflow_request_ref="workflow-request:sha256:one",
        ),
        ExecutionMarkedReady(
            event_id=identity("transition", "b02"),
            execution_id=run_id,
            expected_version=1,
            occurred_at="2026-07-29T01:00:01Z",
            readiness_snapshot_ref="snapshot:sha256:ready",
        ),
        ExecutionStarted(
            event_id=identity("transition", "b03"),
            execution_id=run_id,
            expected_version=2,
            occurred_at="2026-07-29T01:00:02Z",
            authorization_ref="authorization:sha256:start",
        ),
        ExecutionSucceeded(
            event_id=identity("transition", "b04"),
            execution_id=run_id,
            expected_version=3,
            occurred_at="2026-07-29T01:00:03Z",
            outcome_ref="outcome:sha256:success",
        ),
    )

    direct = None
    for event in events:
        direct = reduce_execution(direct, event)
    replayed = replay_execution(events)

    assert replayed == direct
    assert replayed.status is ExecutionStatus.SUCCEEDED
    assert replayed.version == len(events) == 4
