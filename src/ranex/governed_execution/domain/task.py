"""Durable records for the kernel's dispatch-to-candidate bridge.

These records deliberately carry only facts the kernel established itself.  A
dispatch names the worktree it created and the commit it started from; a
candidate says that admitted evidence did, or did not, satisfy a materialised
subject.  Neither record is an approval.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskDispatch:
    """The kernel's deterministic account of one worktree dispatch."""

    task_id: str
    worktree: str
    base_commit: str

    def as_record(self) -> dict[str, object]:
        """Return the exact, time-independent record stored in the journal."""

        return {
            "type": "task-dispatch",
            "task_id": self.task_id,
            "worktree": self.worktree,
            "base_commit": self.base_commit,
        }


@dataclass(frozen=True, slots=True)
class TaskCandidate:
    """A materialised candidate for later human approval, never a verdict."""

    task_id: str
    gate_id: str
    subject_digest: str
    missing_claims: tuple[str, ...]

    def as_record(self) -> dict[str, object]:
        """Return the candidate record without an approver or clock value."""

        return {
            "type": "task-candidate",
            "task_id": self.task_id,
            "gate_id": self.gate_id,
            "subject_digest": self.subject_digest,
            "verdict": "CANDIDATE",
            "missing_claims": list(self.missing_claims),
        }


@dataclass(frozen=True, slots=True)
class TaskMergeIntent:
    task_id: str
    candidate: str
    subject: str
    target_ref: str
    tip: str

    def as_record(self) -> dict[str, object]:
        return {
            "type": "task-merge-intent",
            "task_id": self.task_id,
            "candidate": self.candidate,
            "subject": self.subject,
            "target_ref": self.target_ref,
            "tip": self.tip,
        }


@dataclass(frozen=True, slots=True)
class TaskMergeCheck:
    task_id: str
    check: str
    status: str
    detail: str
    evidence_disposition: str | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.check not in {
            "policy_approval",
            "ancestry",
            "merge_range",
            "digest_evidence",
            "cas",
        }:
            raise ValueError(f"unknown task merge check: {self.check}")
        if self.status not in {"passed", "refused"}:
            raise ValueError(f"unknown task merge check status: {self.status}")
        if self.evidence_disposition not in {None, "REUSE", "FRESH"}:
            raise ValueError(
                f"unknown evidence disposition: {self.evidence_disposition}"
            )

    def as_record(self) -> dict[str, object]:
        record: dict[str, object] = {
            "type": "task-merge-check",
            "task_id": self.task_id,
            "check": self.check,
            "status": self.status,
            "detail": self.detail,
        }
        if self.evidence_disposition is not None:
            record["evidence_disposition"] = self.evidence_disposition
        if self.evidence_ids:
            record["evidence_ids"] = list(self.evidence_ids)
        return record


@dataclass(frozen=True, slots=True)
class TaskMergeOutcome:
    task_id: str
    candidate: str
    target_ref: str
    outcome: str
    detail: str

    def __post_init__(self) -> None:
        if self.outcome not in {"PUBLISHED", "REFUSED", "INFERRED", "ABORTED"}:
            raise ValueError(f"unknown task merge outcome: {self.outcome}")

    def as_record(self) -> dict[str, object]:
        return {
            "type": "task-merge-outcome",
            "task_id": self.task_id,
            "candidate": self.candidate,
            "target_ref": self.target_ref,
            "outcome": self.outcome,
            "detail": self.detail,
        }
