from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ranex.foundation.identity import Identity

_COMMIT_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class WorkItemStatus(StrEnum):
    FUNNEL = "FUNNEL"
    TRIAGE = "TRIAGE"
    DISCOVERY = "DISCOVERY"
    DEFINITION = "DEFINITION"
    DESIGN = "DESIGN"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFICATION = "VERIFICATION"
    RELEASE_READY = "RELEASE_READY"
    RELEASING = "RELEASING"
    OPERATING = "OPERATING"
    OUTCOME_REVIEW = "OUTCOME_REVIEW"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    ROLLED_BACK = "ROLLED_BACK"


def _require_identity(value: Identity, prefix: str, field: str) -> None:
    if not isinstance(value, Identity) or value.prefix != prefix:
        raise ValueError(f"{field} must be a canonical {prefix!r} identity")


@dataclass(frozen=True, slots=True)
class WorkTransitionRequest:
    request_id: Identity
    project_id: Identity
    work_item_id: Identity
    repository_id: Identity
    candidate_commit: str
    from_status: WorkItemStatus
    to_status: WorkItemStatus
    expected_version: int
    requested_by: Identity
    subject_actor_ids: tuple[Identity, ...] = ()

    def __post_init__(self) -> None:
        _require_identity(self.request_id, "transition", "request_id")
        _require_identity(self.project_id, "prj", "project_id")
        _require_identity(self.work_item_id, "work", "work_item_id")
        _require_identity(self.repository_id, "repo", "repository_id")
        _require_identity(self.requested_by, "principal", "requested_by")
        if _COMMIT_PATTERN.fullmatch(self.candidate_commit) is None:
            raise ValueError("candidate_commit must be lowercase Git commit hex")
        if not isinstance(self.from_status, WorkItemStatus) or not isinstance(
            self.to_status,
            WorkItemStatus,
        ):
            raise ValueError("work transition statuses must be canonical")
        if self.from_status is self.to_status:
            raise ValueError("from_status and to_status must differ")
        if (
            isinstance(self.expected_version, bool)
            or not isinstance(self.expected_version, int)
            or self.expected_version < 0
        ):
            raise ValueError("expected_version must be a non-negative integer")
        canonical_actor_ids = tuple(sorted(set(self.subject_actor_ids), key=str))
        if self.subject_actor_ids != canonical_actor_ids:
            raise ValueError("subject_actor_ids must be unique and sorted")
        for actor_id in self.subject_actor_ids:
            _require_identity(actor_id, "principal", "subject_actor_ids")
