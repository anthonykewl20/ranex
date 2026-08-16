"""Closed, effect-free records for specification clarification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class LifecycleState(StrEnum):
    DRAFT = "DRAFT"
    SPEC_VALIDATED = "SPEC_VALIDATED"
    TESTS_MAPPED = "TESTS_MAPPED"
    APPROVAL_PENDING = "APPROVAL_PENDING"


class RefusalCode(StrEnum):
    ACTOR_MISMATCH = "E-SPEC-030-ACTOR-MISMATCH"
    MISSING_ACTOR = "E-SPEC-030-MISSING-ACTOR"
    STALE_BASE = "E-SPEC-030-STALE-BASE"
    MISSING_ANSWER = "E-SPEC-030-MISSING-ANSWER"
    UNKNOWN_ANSWER = "E-SPEC-030-UNKNOWN-ANSWER"
    CONTRADICTORY_ANSWER = "E-SPEC-030-CONTRADICTORY-ANSWER"
    AMBIGUOUS_QUESTION = "E-SPEC-030-AMBIGUOUS-QUESTION"
    OBSERVED_ONLY_INTENT = "E-SPEC-030-OBSERVED-ONLY-INTENT"
    INVALID_SPECIFICATION = "E-SPEC-030-INVALID-SPECIFICATION"
    INVALID_MANIFEST = "E-SPEC-030-INVALID-MANIFEST"
    INVALID_APPROVAL = "E-SPEC-030-INVALID-APPROVAL"
    CHAIN_MISMATCH = "E-SPEC-030-CHAIN-MISMATCH"
    INVALID_INPUT = "E-SPEC-030-INVALID-INPUT"
    OUT_OF_ORDER = "E-SPEC-030-OUT-OF-ORDER"


TRANSITION_TABLE = MappingProxyType(
    {
        LifecycleState.DRAFT: LifecycleState.SPEC_VALIDATED,
        LifecycleState.SPEC_VALIDATED: LifecycleState.TESTS_MAPPED,
        LifecycleState.TESTS_MAPPED: LifecycleState.APPROVAL_PENDING,
    }
)


@dataclass(frozen=True, slots=True)
class Question:
    question_id: str
    prompt: str
    allowed_answers: tuple[str, ...]

    def as_record(self) -> dict[str, object]:
        return {
            "question_id": self.question_id,
            "prompt": self.prompt,
            "allowed_answers": list(self.allowed_answers),
        }


@dataclass(frozen=True, slots=True)
class ClarificationAnswer:
    question_id: str
    value: str

    def as_record(self) -> dict[str, str]:
        return {"question_id": self.question_id, "value": self.value}


@dataclass(frozen=True, slots=True)
class ClarificationInput:
    """Closed lifecycle input; opaque A/B/C fields retain the foundation v1 shape.

    Observations are precisely ``(id, text, label)`` triples. Their label is
    examined only for ``observed-only`` intent promotion.
    """

    actor_id: str
    target: LifecycleState
    base_digest: str
    spec_packet: object
    manifest: object
    approval_envelope: object
    questions: tuple[Question, ...]
    answers: tuple[ClarificationAnswer, ...]
    observations: tuple[tuple[str, str, str], ...]

    def as_record(self) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "target": str(self.target),
            "answers": [answer.as_record() for answer in self.answers],
            "approval_envelope": self.approval_envelope,
            "base_digest": self.base_digest,
            "manifest": self.manifest,
            "observations": [list(observation) for observation in self.observations],
            "questions": [question.as_record() for question in self.questions],
            "spec_packet": self.spec_packet,
        }


@dataclass(frozen=True, slots=True)
class LifecycleSession:
    state: LifecycleState
    actor_id: str
    base_digest: str
    semantic_digest: str | None = None
    last_request_digest: str | None = None

    def as_record(self) -> dict[str, object]:
        return {
            "actor_id": self.actor_id,
            "base_digest": self.base_digest,
            "last_request_digest": self.last_request_digest,
            "semantic_digest": self.semantic_digest,
            "state": str(self.state),
        }

    @classmethod
    def from_record(cls, record: object) -> LifecycleSession:
        if not isinstance(record, dict):
            raise ValueError("session must be an object")
        try:
            return cls(
                state=LifecycleState(record["state"]),
                actor_id=record["actor_id"],
                base_digest=record["base_digest"],
                semantic_digest=record.get("semantic_digest"),
                last_request_digest=record.get("last_request_digest"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid lifecycle session") from exc


@dataclass(frozen=True, slots=True)
class TransitionResult:
    accepted: bool
    session: LifecycleSession
    actor_id: str
    code: RefusalCode | None = None
    semantic_digest: str | None = None
    cause: str | None = None

    def as_record(self) -> dict[str, object]:
        return {
            "accepted": self.accepted,
            "actor_id": self.actor_id,
            "cause": self.cause,
            "code": str(self.code) if self.code is not None else None,
            "semantic_digest": self.semantic_digest,
            "session": self.session.as_record(),
        }


__all__ = [
    "ClarificationAnswer",
    "ClarificationInput",
    "LifecycleSession",
    "LifecycleState",
    "Question",
    "RefusalCode",
    "TRANSITION_TABLE",
    "TransitionResult",
]
