from __future__ import annotations

from dataclasses import dataclass

from ranex.foundation.identity import Identity


def _require_identity(value: Identity, prefix: str, field: str) -> None:
    if not isinstance(value, Identity) or value.prefix != prefix:
        raise ValueError(f"{field} must be a canonical {prefix!r} identity")


@dataclass(frozen=True, slots=True)
class ApplicationControlRequest:
    request_id: Identity
    project_id: Identity
    execution_id: Identity
    action: str
    expected_version: int
    requested_by: Identity
    subject_actor_ids: tuple[Identity, ...] = ()

    def __post_init__(self) -> None:
        _require_identity(self.request_id, "transition", "request_id")
        _require_identity(self.project_id, "prj", "project_id")
        _require_identity(self.execution_id, "run", "execution_id")
        _require_identity(self.requested_by, "principal", "requested_by")
        if not isinstance(self.action, str) or not self.action.strip():
            raise ValueError("action must be a non-empty string")
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


@dataclass(frozen=True, slots=True)
class ApplicationControlFacts:
    decision_well_formed: bool
    request_bound: bool
    gate_passed: bool
    gate_authorized: bool
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApplicationControlDecision:
    permitted: bool
    reason_codes: tuple[str, ...]


def deny_application_control(*reason_codes: str) -> ApplicationControlDecision:
    reasons = tuple(sorted(set(reason_codes)))
    if not reasons or any(not reason for reason in reasons):
        raise ValueError("denial requires non-empty reason codes")
    return ApplicationControlDecision(permitted=False, reason_codes=reasons)


def decide_application_control(
    facts: ApplicationControlFacts,
) -> ApplicationControlDecision:
    """Pure fail-closed application-control decision."""
    if not facts.decision_well_formed:
        return deny_application_control("MALFORMED_POLICY_DECISION")
    if not facts.request_bound:
        return deny_application_control("POLICY_DECISION_SUBJECT_MISMATCH")
    if not facts.gate_passed or not facts.gate_authorized:
        return deny_application_control(*(facts.reason_codes or ("POLICY_DENIED",)))
    if facts.reason_codes:
        return deny_application_control("PASS_DECISION_CONTAINS_REASONS")
    return ApplicationControlDecision(permitted=True, reason_codes=())
