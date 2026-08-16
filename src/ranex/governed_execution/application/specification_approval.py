"""Pure approval issuance composed from frozen ABC and SLICE-032 domain rules."""

from __future__ import annotations

from dataclasses import dataclass

from ranex.foundation.specification_abc import (
    SpecificationABCError,
    assert_abc_chain,
    payload_digest,
)
from ranex.governed_execution.domain.specification_approval import (
    ApprovalPendingContext,
    ApprovalRefusal,
    CapabilityGrant,
    PolicyCapabilities,
    RoleAssignments,
    intersect_capabilities,
)
from ranex.governed_execution.domain.specification_events import (
    SpecificationEvent,
    expiry_recorded_event,
    grant_issued_event,
)


@dataclass(frozen=True)
class ApprovalOutcome:
    c_digest: str
    grant: CapabilityGrant
    approved_event: SpecificationEvent
    implementable_event: SpecificationEvent
    grant_issued_event: SpecificationEvent
    expiry_recorded_event: SpecificationEvent

    def as_record(self) -> dict[str, object]:
        return {
            "c_digest": self.c_digest, "grant": self.grant.as_record(),
            "approved_event": self.approved_event.as_record(),
            "implementable_event": self.implementable_event.as_record(),
            "grant_issued_event": self.grant_issued_event.as_record(),
            "expiry_recorded_event": self.expiry_recorded_event.as_record(),
        }


def issue_approval(
    spec_packet: object, manifest: object, envelope: object, policy: PolicyCapabilities,
    pending: ApprovalPendingContext, roles: RoleAssignments, journal_position: int,
    current_head: str | None, *, prior_events: tuple[SpecificationEvent, ...],
) -> ApprovalOutcome:
    """Validate a C at the observed head and project deterministic lifecycle facts."""

    if not isinstance(envelope, dict) or not isinstance(envelope.get("payload"), dict):
        raise ApprovalRefusal("E-APPROVAL-SHAPE", "approval envelope is absent")
    payload = envelope["payload"]
    used_nonces = tuple(
        event.event_id.removeprefix("approval:")
        for event in prior_events
        if event.kind == "APPROVED" and event.code == "OK" and event.event_id.startswith("approval:")
    )
    try:
        assert_abc_chain(spec_packet, manifest, envelope, used_nonces=used_nonces)
    except SpecificationABCError as exc:
        raise ApprovalRefusal(exc.code, exc.detail) from exc
    c_digest = payload_digest(payload)
    if payload["profile_digests"]["policy"] != policy.digest:
        raise ApprovalRefusal("E-APPROVAL-POLICY", "policy content digest differs from C")
    if pending.semantic_digest != payload["subject_digest"] or pending.actor != payload["principal"]:
        raise ApprovalRefusal("E-APPROVAL-PENDING", "approval-pending context does not bind C")
    if type(journal_position) is not int or journal_position < 0:
        raise ApprovalRefusal("E-APPROVAL-POSITION", "journal position is invalid")
    if (journal_position == 0) != (current_head is None) or payload["journal_predecessor"] != current_head:
        raise ApprovalRefusal("E-APPROVAL-PREDECESSOR", "C predecessor does not equal observed head/genesis")
    window = payload["time_window"]
    if not window["not_before"] <= journal_position <= window["not_after"]:
        raise ApprovalRefusal("E-APPROVAL-WINDOW", "journal position is outside C's inclusive window")
    roles.require(payload["principal"], payload["key"], "approver", c_digest)
    grant = CapabilityGrant(
        "grant:" + c_digest, c_digest, None,
        intersect_capabilities(PolicyCapabilities.from_record(payload["capability_request"]), policy, child=False),
        roles.key_for("worker", c_digest),
        roles.key_for("evaluator", c_digest), roles.key_for("publisher", c_digest),
        window["not_before"], window["not_after"],
    )
    approved = SpecificationEvent(
        "approval:" + payload["nonce"], "APPROVED", journal_position, current_head, c_digest,
        grant.grant_id, None, payload["principal"], payload["key"], None, "OK",
    )
    implementable = SpecificationEvent(
        "implementable:" + c_digest, "IMPLEMENTABLE", journal_position + 1, approved.digest,
        c_digest, grant.grant_id, None, payload["principal"], payload["key"], approved.digest, "OK",
    )
    issued = grant_issued_event(
        grant, seq=journal_position + 2, journal_head_link=current_head,
        principal_id=payload["principal"], key_id=payload["key"], previous_event_digest=implementable.digest,
    )
    expiry = expiry_recorded_event(
        grant, journal_head_link=current_head, principal_id=payload["principal"], key_id=payload["key"],
        previous_event_digest=issued.digest,
    )
    return ApprovalOutcome(c_digest, grant, approved, implementable, issued, expiry)
