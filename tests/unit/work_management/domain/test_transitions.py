from __future__ import annotations

import pytest

from ranex.foundation.identity import Identity
from ranex.work_management.domain.transitions import (
    WorkItemStatus,
    WorkTransitionRequest,
)


def identity(prefix: str, suffix: str) -> Identity:
    return Identity.parse(
        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
        expected_prefix=prefix,
    )


def test_work_transition_request_owns_work_item_transition_subject() -> None:
    request = WorkTransitionRequest(
        request_id=identity("transition", "501"),
        project_id=identity("prj", "502"),
        work_item_id=identity("work", "503"),
        repository_id=identity("repo", "504"),
        candidate_commit="a" * 40,
        from_status=WorkItemStatus.IN_PROGRESS,
        to_status=WorkItemStatus.VERIFICATION,
        expected_version=7,
        requested_by=identity("principal", "505"),
    )

    assert request.from_status is WorkItemStatus.IN_PROGRESS
    assert request.to_status is WorkItemStatus.VERIFICATION
    assert request.expected_version == 7


def test_work_transition_request_rejects_noop_and_bad_commit() -> None:
    common = {
        "request_id": identity("transition", "511"),
        "project_id": identity("prj", "512"),
        "work_item_id": identity("work", "513"),
        "repository_id": identity("repo", "514"),
        "candidate_commit": "a" * 40,
        "from_status": WorkItemStatus.READY,
        "to_status": WorkItemStatus.IN_PROGRESS,
        "expected_version": 0,
        "requested_by": identity("principal", "515"),
    }

    with pytest.raises(ValueError, match="must differ"):
        WorkTransitionRequest(**(common | {"to_status": WorkItemStatus.READY}))
    with pytest.raises(ValueError, match="commit"):
        WorkTransitionRequest(**(common | {"candidate_commit": "not-a-commit"}))


def test_work_transition_request_rejects_noncanonical_actor_order() -> None:
    with pytest.raises(ValueError, match="unique and sorted"):
        WorkTransitionRequest(
            request_id=identity("transition", "521"),
            project_id=identity("prj", "522"),
            work_item_id=identity("work", "523"),
            repository_id=identity("repo", "524"),
            candidate_commit="b" * 40,
            from_status=WorkItemStatus.READY,
            to_status=WorkItemStatus.IN_PROGRESS,
            expected_version=0,
            requested_by=identity("principal", "525"),
            subject_actor_ids=(
                identity("principal", "527"),
                identity("principal", "526"),
            ),
        )
