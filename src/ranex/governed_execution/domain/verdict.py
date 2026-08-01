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
    """A required claim, and the command that satisfies it.

    The command arrives already digested. A claim whose bound command cannot be
    compared has undefined satisfaction, and an undefined claim cannot block, so
    a malformed digest is refused here rather than defaulted anywhere.
    """

    claim_id: str
    command_digest: str

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_digest(self.command_digest, "command_digest")


@dataclass(frozen=True, slots=True)
class Evidence:
    """A recorded observation. Bound to the exact subject it was produced for."""

    claim_id: str
    subject_digest: str
    producer_id: str
    command: str
    command_digest: str
    executable_path: str
    exit_code: int

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.producer_id, "producer_id")
        _require_text(self.command, "command")
        _require_text(self.executable_path, "executable_path")
        _require_digest(self.subject_digest, "subject_digest")
        _require_digest(self.command_digest, "command_digest")
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise ValueError("exit_code must be an integer")

    def addresses(self, claim: Claim, subject_digest: str) -> bool:
        """A report *about* this claim: right claim, right subject, right command.

        Everything `satisfies` asks except the outcome. Two records that both
        address one claim and disagree about the outcome cannot both be true,
        and telling that apart from silence is what stops a reported failure
        being outvoted by a reported success.
        """

        return (
            self.claim_id == claim.claim_id
            and self.subject_digest == subject_digest
            and self.command_digest == claim.command_digest
        )

    def satisfies(self, claim: Claim, subject_digest: str) -> bool:
        """The right claim, the right subject, the right command, and success.

        The subject check is what makes stale evidence not evidence: the same
        command run against a different commit proves nothing about this one.

        The command check is what makes a trivial run not evidence: `true` exits
        0 against every tree, so a record of it proves nothing about this one
        however well it is signed. The digest is compared and never the legible
        `command`, so a record cannot read like the bound command while
        describing something else.
        """

        return self.addresses(claim, subject_digest) and self.exit_code == 0


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


def _contradicted(
    claim: Claim,
    evidence: tuple[Evidence, ...],
    subject_digest: str,
) -> bool:
    """Do two records addressing this claim disagree about what happened?

    A contradiction is not evidence. It is the one case where more records make
    the answer less certain, and resolving it by taking the favourable half —
    which is exactly what `any(... satisfies ...)` does — discards a signed,
    admitted report of failure without saying so.
    """

    outcomes = {
        item.exit_code == 0
        for item in evidence
        if item.addresses(claim, subject_digest)
    }
    return len(outcomes) > 1


def _diagnosis(
    gate: Gate,
    evidence: tuple[Evidence, ...],
    subject_digest: str,
    contradicted: tuple[str, ...],
    missing: tuple[str, ...],
) -> str:
    """Why the gate failed, per claim and in its own words.

    Four different events reach a caller as "this claim is not satisfied", and
    only one of them is work never done. Reporting a record that names another
    command, another tree, or a failing run under the phrasing reserved for
    absence files an attack — or a genuine red suite — as an unfinished task.
    So each claim is named under what actually happened to it, and the absence
    sentence is spent only on claims nothing at all was recorded for.
    """

    absent: list[str] = []
    stale: list[str] = []
    mismatched: list[str] = []
    failed: list[str] = []
    for claim in gate.required_claims:
        if claim.claim_id not in missing or claim.claim_id in contradicted:
            # A contradiction is already named, and naming it twice under a
            # second heading would invite reading it as two separate problems.
            continue
        named = [item for item in evidence if item.claim_id == claim.claim_id]
        if not named:
            absent.append(claim.claim_id)
        elif any(item.addresses(claim, subject_digest) for item in named):
            # Addressed and still unsatisfied means the bound command ran
            # against this tree and did not exit 0.
            failed.append(claim.claim_id)
        elif any(item.subject_digest == subject_digest for item in named):
            mismatched.append(claim.claim_id)
        else:
            stale.append(claim.claim_id)

    clauses = [
        (
            contradicted,
            "contradictory evidence — the same claim, subject and command "
            "reported both success and failure",
        ),
        (tuple(failed), "the bound command was observed failing"),
        (tuple(mismatched), "evidence describes a command the claim does not bind"),
        (tuple(stale), "evidence bound to a different subject digest"),
        (tuple(absent), "no evidence for required claim"),
    ]
    return "; ".join(
        f"{text}: {', '.join(sorted(claims))}" for claims, text in clauses if claims
    )


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

    # A claim whose records disagree is not satisfied however many of them say
    # PASS. It is listed as unsatisfied like any other — a caller reading
    # `missing_claims` must see every claim that failed to clear — and the
    # reason says which of the two it was, because "nobody ran it" and "two
    # producers disagree about what happened" are not the same event.
    contradicted = tuple(
        sorted(
            claim.claim_id
            for claim in gate.required_claims
            if _contradicted(claim, evidence, subject_digest)
        )
    )
    missing = tuple(
        sorted(
            claim.claim_id
            for claim in gate.required_claims
            if claim.claim_id in contradicted
            or not any(item.satisfies(claim, subject_digest) for item in evidence)
        )
    )
    if missing:
        reason = _diagnosis(gate, evidence, subject_digest, contradicted, missing)
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
