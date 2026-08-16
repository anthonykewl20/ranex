"""Frozen pure approval event records and ordered revocation reduction."""

from __future__ import annotations

from dataclasses import dataclass

from ranex.foundation.specification_abc import payload_digest
from ranex.governed_execution.domain.specification_approval import ApprovalRefusal, CapabilityGrant

_KINDS = frozenset({"APPROVED", "IMPLEMENTABLE", "GRANT_ISSUED", "GRANT_REVOKED", "APPROVAL_REVOKED", "EXPIRY_RECORDED"})


@dataclass(frozen=True)
class SpecificationEvent:
    """A pure lifecycle event.

    For an ``APPROVED`` event, ``journal_head_link`` is C's observed journal
    predecessor. For projected lifecycle events it is an informational
    predecessor token; ``previous_event_digest`` alone binds the in-domain
    event chain. SLICE-036's CAS contract is: compare the storage head to the
    authoritative observed head supplied to that append, append exactly one
    event, then return the resulting storage head. It must not treat a
    projected non-``APPROVED`` event's ``journal_head_link`` as the CAS head.
    """
    event_id: str
    kind: str
    seq: int
    journal_head_link: str | None
    c_digest: str
    grant_id: str | None
    parent_grant_id: str | None
    principal_id: str
    key_id: str
    previous_event_digest: str | None
    code: str

    def __post_init__(self) -> None:
        if self.kind not in _KINDS or not self.event_id or not self.c_digest or not self.principal_id or not self.key_id or not self.code:
            raise ApprovalRefusal("E-APPROVAL-EVENT", "event has an unknown kind or absent required field")
        if type(self.seq) is not int or self.seq < 0:
            raise ApprovalRefusal("E-APPROVAL-EVENT", "event sequence is invalid")

    def as_record(self) -> dict[str, object]:
        return {
            "version": "approval-event-v1", "event_id": self.event_id, "kind": self.kind,
            "journal_position": {"seq": self.seq, "head_link": self.journal_head_link},
            "c_digest": self.c_digest, "grant_id": self.grant_id,
            "parent_grant_id": self.parent_grant_id, "principal_id": self.principal_id,
            "key_id": self.key_id, "previous_event_digest": self.previous_event_digest,
            "code": self.code,
        }

    @property
    def digest(self) -> str:
        return payload_digest(self.as_record())


def grant_issued_event(
    grant: CapabilityGrant, *, seq: int, journal_head_link: str | None,
    principal_id: str, key_id: str, previous_event_digest: str | None,
) -> SpecificationEvent:
    """Construct the closed event that establishes a grant's ancestry."""

    return SpecificationEvent(
        f"grant-issued:{grant.grant_id}", "GRANT_ISSUED", seq, journal_head_link,
        grant.c_digest, grant.grant_id, grant.parent_grant_id, principal_id, key_id,
        previous_event_digest, "OK",
    )


def grant_revoked_event(
    grant: CapabilityGrant, *, seq: int, journal_head_link: str | None,
    principal_id: str, key_id: str, previous_event_digest: str | None,
) -> SpecificationEvent:
    """Construct the closed event that revokes one grant and its descendants."""

    return SpecificationEvent(
        f"grant-revoked:{grant.grant_id}", "GRANT_REVOKED", seq, journal_head_link,
        grant.c_digest, grant.grant_id, grant.parent_grant_id, principal_id, key_id,
        previous_event_digest, "OK",
    )


def approval_revoked_event(
    c_digest: str, *, seq: int, journal_head_link: str | None,
    principal_id: str, key_id: str, previous_event_digest: str | None,
) -> SpecificationEvent:
    """Construct the closed event that revokes every grant for an approval."""

    return SpecificationEvent(
        f"approval-revoked:{c_digest}", "APPROVAL_REVOKED", seq, journal_head_link,
        c_digest, None, None, principal_id, key_id, previous_event_digest, "OK",
    )


def expiry_recorded_event(
    grant: CapabilityGrant, *, journal_head_link: str | None,
    principal_id: str, key_id: str, previous_event_digest: str | None, seq: int | None = None,
) -> SpecificationEvent:
    """Project the inclusive grant window's first invalid position as revocation."""

    return SpecificationEvent(
        f"expiry:{grant.grant_id}", "EXPIRY_RECORDED", grant.not_after + 1 if seq is None else seq,
        journal_head_link, grant.c_digest, grant.grant_id, grant.parent_grant_id,
        principal_id, key_id, previous_event_digest, "OK",
    )


@dataclass(frozen=True)
class UseFact:
    grant_id: str
    valid: bool
    code: str
    observed_event_head: str | None
    observed_position: int

    def as_record(self) -> dict[str, object]:
        return {
            "version": "approval-use-fact-v1", "grant_id": self.grant_id, "valid": self.valid,
            "code": self.code, "observed_event_head": self.observed_event_head,
            "observed_position": self.observed_position,
        }


def _checked_prefix(events: tuple[SpecificationEvent, ...], position: int) -> None:
    previous_seq = -1
    previous_digest: str | None = None
    for event in events:
        if event.seq <= previous_seq or event.seq >= position or event.previous_event_digest != previous_digest:
            raise ApprovalRefusal("E-APPROVAL-EVENT-CHAIN", "event prefix is not canonically ordered")
        previous_seq = event.seq
        previous_digest = event.digest


def evaluate_use(
    events_prefix: tuple[SpecificationEvent, ...], grant: CapabilityGrant, journal_position: int
) -> UseFact:
    """Evaluate only a committed ordered prefix; persistence supplies CAS separately."""

    if type(journal_position) is not int or journal_position < 0:
        raise ApprovalRefusal("E-APPROVAL-EVENT", "use position is invalid")
    _checked_prefix(events_prefix, journal_position)
    issued_by_grant: dict[str, SpecificationEvent] = {}
    for event in events_prefix:
        if event.kind != "GRANT_ISSUED" or event.grant_id is None:
            continue
        if event.grant_id in issued_by_grant:
            raise ApprovalRefusal("E-APPROVAL-GRANT-DUPLICATE", "grant has more than one issuance event")
        issued_by_grant[event.grant_id] = event
    current_grant = grant.grant_id
    expected_parent = grant.parent_grant_id
    seen: set[str] = set()
    while current_grant not in seen:
        seen.add(current_grant)
        issued = issued_by_grant.get(current_grant)
        if (
            issued is None
            or issued.c_digest != grant.c_digest
            or issued.parent_grant_id != expected_parent
        ):
            raise ApprovalRefusal("E-APPROVAL-GRANT-UNISSUED", "grant has no complete C-bound issuance ancestry")
        current_grant = expected_parent
        if current_grant is None:
            break
        parent_issued = issued_by_grant.get(current_grant)
        if parent_issued is None or parent_issued.seq >= issued.seq:
            raise ApprovalRefusal("E-APPROVAL-GRANT-UNISSUED", "grant issuance ancestry is not temporally ordered")
        expected_parent = parent_issued.parent_grant_id
    else:
        raise ApprovalRefusal("E-APPROVAL-GRANT-UNISSUED", "grant issuance ancestry cycles")
    if not grant.not_before <= journal_position <= grant.not_after:
        head = events_prefix[-1].digest if events_prefix else None
        return UseFact(grant.grant_id, False, "E-APPROVAL-WINDOW", head, journal_position)
    parent_by_grant = {event.grant_id: event.parent_grant_id for event in events_prefix if event.kind == "GRANT_ISSUED" and event.grant_id}
    ancestors = {grant.grant_id}
    current = grant.parent_grant_id
    while current is not None and current not in ancestors:
        ancestors.add(current)
        current = parent_by_grant.get(current)
    revoked = any(
        event.kind in {"GRANT_REVOKED", "EXPIRY_RECORDED"} and event.grant_id in ancestors
        or event.kind == "APPROVAL_REVOKED" and event.c_digest == grant.c_digest
        for event in events_prefix
    )
    head = events_prefix[-1].digest if events_prefix else None
    return UseFact(grant.grant_id, not revoked, "OK" if not revoked else "E-APPROVAL-REVOKED", head, journal_position)
