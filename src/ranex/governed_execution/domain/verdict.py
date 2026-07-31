"""Deterministic gate evaluation.

The whole point of this module: a verdict is a pure function of (gate, evidence,
subject, approver). No model is consulted, no network is reached, nothing is
inferred. Removing every model credential from the machine must not change a
single verdict.

Absence blocks. A required claim with no satisfying evidence is FAIL, never a
default and never a skip.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ranex.foundation.canonical import canonical_sha256

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{field} must be a canonical sha256 digest")


@dataclass(frozen=True, slots=True)
class Claim:
    claim_id: str

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")


@dataclass(frozen=True, slots=True)
class Evidence:
    """A recorded observation. Bound to the exact subject it was produced for."""

    claim_id: str
    subject_digest: str
    producer_id: str
    command: str
    exit_code: int

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.producer_id, "producer_id")
        _require_text(self.command, "command")
        _require_digest(self.subject_digest, "subject_digest")
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise ValueError("exit_code must be an integer")

    def satisfies(self, claim: Claim, subject_digest: str) -> bool:
        """Satisfying requires the right claim, the right subject, and success.

        The subject check is what makes stale evidence not evidence: the same
        command run against a different commit proves nothing about this one.
        """

        return (
            self.claim_id == claim.claim_id
            and self.subject_digest == subject_digest
            and self.exit_code == 0
        )


@dataclass(frozen=True, slots=True)
class Gate:
    gate_id: str
    rule_id: str
    required_claims: tuple[Claim, ...]
    blocking: bool

    def __post_init__(self) -> None:
        _require_text(self.gate_id, "gate_id")
        _require_text(self.rule_id, "rule_id")
        if not self.required_claims:
            raise ValueError("gate must declare required_claims")
        ids = [claim.claim_id for claim in self.required_claims]
        if len(ids) != len(set(ids)):
            raise ValueError("required_claims must be unique")
        if not self.blocking:
            # A gate that cannot block is decoration. Refused at construction so
            # it can never reach an evaluation and read as governance.
            raise ValueError("gate must be blocking")


@dataclass(frozen=True, slots=True)
class Evaluation:
    verdict: Verdict
    gate_id: str
    failing_rule: str | None
    missing_claims: tuple[str, ...]
    reason: str | None
    subject_digest: str
    subject_lane: str
    catalog_digest: str | None
    approver_id: str
    considered: tuple[str, ...]

    def as_record(self) -> dict[str, object]:
        """The appended record. Ordered and typed so two runs are identical."""

        return {
            "approver_id": self.approver_id,
            "catalog_digest": self.catalog_digest,
            "considered": list(self.considered),
            "failing_rule": self.failing_rule,
            "gate_id": self.gate_id,
            "missing_claims": list(self.missing_claims),
            "reason": self.reason,
            "subject_digest": self.subject_digest,
            "subject_lane": self.subject_lane,
            "verdict": str(self.verdict),
        }

    @property
    def record_digest(self) -> str:
        return "sha256:" + canonical_sha256(self.as_record())


def evaluate(
    gate: Gate,
    evidence: tuple[Evidence, ...],
    *,
    subject_digest: str,
    subject_lane: str = "PRE_READINESS_PRODUCT_SLICE",
    catalog_digest: str | None = None,
    approver_id: str,
) -> Evaluation:
    """Return the verdict. Pure: same inputs, same output, always."""

    _require_digest(subject_digest, "subject_digest")
    _require_text(approver_id, "approver_id")

    considered = tuple(
        sorted(f"{item.claim_id}@{item.subject_digest}:{item.exit_code}" for item in evidence)
    )

    # No self-approval. Checked before evidence so that an approver reviewing
    # their own work fails for that reason rather than appearing to pass.
    self_approved = sorted(
        {item.producer_id for item in evidence if item.producer_id == approver_id}
    )
    if self_approved:
        return Evaluation(
            verdict=Verdict.FAIL,
            gate_id=gate.gate_id,
            failing_rule=gate.rule_id,
            missing_claims=(),
            reason=(
                "self-approval refused: "
                f"{', '.join(self_approved)} produced evidence and approved it"
            ),
            subject_digest=subject_digest,
            subject_lane=subject_lane,
            catalog_digest=catalog_digest,
            approver_id=approver_id,
            considered=considered,
        )

    missing = tuple(
        sorted(
            claim.claim_id
            for claim in gate.required_claims
            if not any(item.satisfies(claim, subject_digest) for item in evidence)
        )
    )
    if missing:
        wrong_subject = sorted(
            {
                item.claim_id
                for item in evidence
                if item.claim_id in missing and item.subject_digest != subject_digest
            }
        )
        if wrong_subject:
            reason = (
                "evidence bound to a different subject digest: "
                f"{', '.join(wrong_subject)}"
            )
        else:
            reason = f"no evidence for required claim: {', '.join(missing)}"
        return Evaluation(
            verdict=Verdict.FAIL,
            gate_id=gate.gate_id,
            failing_rule=gate.rule_id,
            missing_claims=missing,
            reason=reason,
            subject_digest=subject_digest,
            subject_lane=subject_lane,
            catalog_digest=catalog_digest,
            approver_id=approver_id,
            considered=considered,
        )

    return Evaluation(
        verdict=Verdict.PASS,
        gate_id=gate.gate_id,
        failing_rule=None,
        missing_claims=(),
        reason=None,
        subject_digest=subject_digest,
        subject_lane=subject_lane,
        catalog_digest=catalog_digest,
        approver_id=approver_id,
        considered=considered,
    )
