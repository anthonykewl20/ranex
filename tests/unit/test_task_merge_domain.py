from __future__ import annotations

import pytest

from ranex.governed_execution.domain.task import TaskMergeCheck, TaskMergeOutcome


def test_task_merge_check_refuses_unknown_check() -> None:
    with pytest.raises(ValueError, match="unknown task merge check: unknown"):
        TaskMergeCheck("task-1", "unknown", "passed", "detail")


def test_task_merge_check_refuses_unknown_status() -> None:
    with pytest.raises(ValueError, match="unknown task merge check status: unknown"):
        TaskMergeCheck("task-1", "cas", "unknown", "detail")


def test_task_merge_check_refuses_unknown_evidence_disposition() -> None:
    with pytest.raises(ValueError, match="unknown evidence disposition: unknown"):
        TaskMergeCheck(
            "task-1",
            "cas",
            "passed",
            "detail",
            evidence_disposition="unknown",
        )


def test_task_merge_outcome_refuses_unknown_outcome() -> None:
    with pytest.raises(ValueError, match="unknown task merge outcome: unknown"):
        TaskMergeOutcome("task-1", "candidate", "refs/heads/main", "unknown", "detail")
