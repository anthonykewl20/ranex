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
