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
from ranex.foundation.suite_results import validate_suite_results

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
    results_required: bool = False
    manifest_digest: str | None = None
    expected_ids: tuple[str, ...] | None = None
    expected_skips: dict[str, str] | None = None

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_digest(self.command_digest, "command_digest")
        if not isinstance(self.results_required, bool):
            raise ValueError("results_required must be a boolean")
        if not self.results_required:
            if any(
                value is not None
                for value in (
                    self.manifest_digest,
                    self.expected_ids,
                    self.expected_skips,
                )
            ):
                raise ValueError("exit-code-only claims cannot carry suite manifest fields")
            return
        _require_digest(self.manifest_digest, "manifest_digest")
        if (
            not isinstance(self.expected_ids, tuple)
            or any(
                not isinstance(test_id, str) or not test_id
                for test_id in self.expected_ids
            )
            or self.expected_ids != tuple(sorted(self.expected_ids))
            or len(self.expected_ids) != len(set(self.expected_ids))
        ):
            raise ValueError("expected_ids must be a sorted tuple of unique test IDs")
        if not isinstance(self.expected_skips, dict):
            raise ValueError("expected_skips must be a mapping")
        expected = set(self.expected_ids)
        for test_id, reason in self.expected_skips.items():
            if test_id not in expected or not isinstance(reason, str) or not reason.strip():
                raise ValueError("expected_skips must name expected IDs with non-empty reasons")


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
    suite_results: dict[str, object] | None = None

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.producer_id, "producer_id")
        _require_text(self.command, "command")
        _require_text(self.executable_path, "executable_path")
        _require_digest(self.subject_digest, "subject_digest")
        _require_digest(self.command_digest, "command_digest")
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise ValueError("exit_code must be an integer")
        if self.suite_results is not None:
            validate_suite_results(self.suite_results)

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

        if not self.addresses(claim, subject_digest) or self.exit_code != 0:
            return False
        if not claim.results_required:
            return True
        if self.suite_results is None:
            return False
        if self.suite_results["manifest_digest"] != claim.manifest_digest:
            return False

        expected_ids = set(claim.expected_ids or ())
        expected_skips = set(claim.expected_skips or {})
        if expected_ids.intersection(self.suite_results["missing"]):
            return False
        for test_id, kind in self.suite_results["non_passed"]:
            if test_id not in expected_ids:
                continue
            if kind == "skipped" and test_id in expected_skips:
                continue
            return False
        return True

    def suite_diagnosis(self, claim: Claim) -> tuple[str, ...]:
        """Specific manifest-diff failures for an addressed suite claim."""

        if not claim.results_required:
            return ()
        if self.suite_results is None:
            return ("suite results artifact was absent",)
        if self.suite_results["manifest_digest"] != claim.manifest_digest:
            return ("suite manifest digest did not match the claim",)
        expected_ids = set(claim.expected_ids or ())
        expected_skips = set(claim.expected_skips or {})
        missing = sorted(expected_ids.intersection(self.suite_results["missing"]))
        clauses: list[str] = []
        if missing:
            clauses.append(f"missing test ID(s): {', '.join(missing)}")
        offenders = sorted(
            (test_id, kind)
            for test_id, kind in self.suite_results["non_passed"]
            if test_id in expected_ids
            and not (kind == "skipped" and test_id in expected_skips)
        )
        if offenders:
            clauses.append(
                "blocking suite outcome(s): "
                + ", ".join(f"{test_id} ({kind})" for test_id, kind in offenders)
            )
        return tuple(clauses)


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
class ClaimCause:
    claim_id: str
    cause: str
    detail: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.claim_id, "claim_id")
        _require_text(self.cause, "cause")


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
    causes: tuple[ClaimCause, ...]
    self_approval: bool

    def as_record(self) -> dict[str, object]:
        """The appended record. Ordered and typed so two runs are identical."""

        return {
            "approver_id": self.approver_id,
            "catalog_digest": self.catalog_digest,
            "causes": [
                {
                    "claim_id": item.claim_id,
                    "cause": item.cause,
                    **({"detail": item.detail} if item.detail is not None else {}),
                }
                for item in self.causes
            ],
            "considered": list(self.considered),
            "failing_rule": self.failing_rule,
            "gate_id": self.gate_id,
            "missing_claims": list(self.missing_claims),
            "reason": self.reason,
            "self_approval": self.self_approval,
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
        item.satisfies(claim, subject_digest)
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
) -> tuple[tuple[ClaimCause, ...], str]:
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
    suite_failures: list[tuple[str, str]] = []
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
            addressed = [
                item for item in named if item.addresses(claim, subject_digest)
            ]
            details = sorted(
                {
                    detail
                    for item in addressed
                    for detail in item.suite_diagnosis(claim)
                }
            )
            if details:
                suite_failures.append((claim.claim_id, ", ".join(details)))
            else:
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
    standard = [
        f"{text}: {', '.join(sorted(claims))}" for claims, text in clauses if claims
    ]
    causes = tuple(
        ClaimCause(claim_id, kind, detail)
        for entries, kind in (
            (((claim_id, None) for claim_id in contradicted), "contradicted"),
            (((claim_id, None) for claim_id in failed), "failed"),
            (suite_failures, "failed"),
            (((claim_id, None) for claim_id in mismatched), "mismatched"),
            (((claim_id, None) for claim_id in stale), "stale"),
            (((claim_id, None) for claim_id in absent), "absent"),
        )
        for claim_id, detail in sorted(entries)
    )
    reason = "; ".join(
        [*(f"{claim_id}: {detail}" for claim_id, detail in suite_failures), *standard]
    )
    return causes, reason


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
            causes=(),
            self_approval=True,
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
        causes, reason = _diagnosis(gate, evidence, subject_digest, contradicted, missing)
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
            causes=causes,
            self_approval=False,
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
        causes=(),
        self_approval=False,
    )
