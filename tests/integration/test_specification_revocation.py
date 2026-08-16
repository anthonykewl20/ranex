"""Ordered pure revocation reduction vectors for SLICE-032."""

from __future__ import annotations

from dataclasses import replace

from ranex.governed_execution.domain.specification_approval import (
    CapabilityGrant,
    PolicyCapabilities,
    issue_child_grant,
)
from ranex.governed_execution.domain.specification_events import (
    ApprovalRefusal,
    SpecificationEvent,
    approval_revoked_event,
    evaluate_use,
    grant_issued_event,
    grant_revoked_event,
)


def grant() -> CapabilityGrant:
    caps = PolicyCapabilities.from_record({
        "executable": "python", "argv": [], "cwd": ".", "roots": ["src"], "actions": ["read"],
        "environment": {"allow": []}, "network": {"allow": False, "hosts": []},
        "secret": {"allow": False, "names": []}, "commit": {"allow": False},
        "subagent": {"allow": False, "max_children": 0},
    })
    return CapabilityGrant("child", "sha256:" + "a" * 64, "parent", caps, "worker", "eval", "pub", 0, 50)


def event(kind: str, seq: int, grant_id: str = "parent") -> SpecificationEvent:
    return SpecificationEvent(f"{kind}-{seq}", kind, seq, "sha256:" + "b" * 64, "sha256:" + "a" * 64, grant_id, None, "owner", "key", None, "OK")


def test_revoke_and_expiry_propagate_through_descendants() -> None:
    issued_parent = event("GRANT_ISSUED", 1, "parent")
    issued_child = SpecificationEvent("child", "GRANT_ISSUED", 2, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "child", "parent", "owner", "key", issued_parent.digest, "OK")
    revoked = SpecificationEvent("revoke", "GRANT_REVOKED", 3, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "parent", None, "owner", "key", issued_child.digest, "OK")
    assert evaluate_use((issued_parent, issued_child, revoked), grant(), 4).valid is False
    expiry = SpecificationEvent("expiry", "EXPIRY_RECORDED", 3, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "parent", None, "owner", "key", issued_child.digest, "OK")
    assert evaluate_use((issued_parent, issued_child, expiry), grant(), 4).valid is False


def test_event_and_use_facts_are_canonical_and_deterministic() -> None:
    root = replace(grant(), parent_grant_id=None)
    issued = event("GRANT_ISSUED", 1, "child")
    issued = replace(issued, parent_grant_id=None)
    first = evaluate_use((issued,), root, 2)
    assert first == evaluate_use((issued,), root, 2)
    assert first.valid is True
    revoke = SpecificationEvent("revoke", "GRANT_REVOKED", 2, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "child", None, "owner", "key", issued.digest, "OK")
    assert evaluate_use((issued, revoke), root, 3).valid is False


def test_grant_window_and_expiry_event_both_refuse_outside_boundaries() -> None:
    base = grant()
    child = CapabilityGrant("child", base.c_digest, "parent", base.capabilities, "worker", "eval", "pub", 10, 20)
    parent = event("GRANT_ISSUED", 8, "parent")
    issued = SpecificationEvent("GRANT_ISSUED-9", "GRANT_ISSUED", 9, "sha256:" + "b" * 64, child.c_digest, "child", "parent", "owner", "key", parent.digest, "OK")
    expiry = SpecificationEvent("expiry", "EXPIRY_RECORDED", 21, "sha256:" + "b" * 64, child.c_digest, "child", "parent", "owner", "key", issued.digest, "OK")
    assert evaluate_use((parent, issued), child, 10).valid is True
    assert evaluate_use((parent, issued), child, 20).valid is True
    with __import__("pytest").raises(ApprovalRefusal, match="E-APPROVAL-GRANT-UNISSUED"):
        evaluate_use((), child, 9)
    assert evaluate_use((parent, issued), child, 21).code == "E-APPROVAL-WINDOW"
    assert evaluate_use((parent, issued, expiry), child, 22).code == "E-APPROVAL-WINDOW"


def test_three_level_revocation_is_produced_by_typed_constructors() -> None:
    caps = grant().capabilities
    root = CapabilityGrant("root", "sha256:" + "a" * 64, None, caps, "worker", "eval", "pub", 1, 50)
    root_issued = grant_issued_event(
        root, seq=1, journal_head_link="sha256:" + "a" * 64, principal_id="owner", key_id="key",
        previous_event_digest=None,
    )
    child, child_issued = issue_child_grant(
        "child", caps, root, caps, journal_position=2, journal_head_link="sha256:" + "b" * 64,
        prior_events=(root_issued,), principal_id="owner", key_id="key",
    )
    grandchild, grandchild_issued = issue_child_grant(
        "grandchild", caps, child, caps, journal_position=3, journal_head_link="sha256:" + "c" * 64,
        prior_events=(root_issued, child_issued), principal_id="owner", key_id="key",
    )
    revoke = grant_revoked_event(
        root, seq=4, journal_head_link="sha256:" + "d" * 64, principal_id="owner", key_id="key",
        previous_event_digest=grandchild_issued.digest,
    )
    assert child_issued.grant_id == child.grant_id
    assert child_issued.parent_grant_id == root.grant_id
    assert grandchild_issued.grant_id == grandchild.grant_id
    assert grandchild_issued.parent_grant_id == child.grant_id
    assert evaluate_use((root_issued, child_issued, grandchild_issued, revoke), grandchild, 5).valid is False
    approval_revoke = approval_revoked_event(
        root.c_digest, seq=5, journal_head_link="sha256:" + "e" * 64, principal_id="owner", key_id="key",
        previous_event_digest=revoke.digest,
    )
    assert evaluate_use((root_issued, child_issued, grandchild_issued, revoke, approval_revoke), grandchild, 6).valid is False


def test_use_refuses_without_a_matching_c_bound_grant_issuance() -> None:
    with __import__("pytest").raises(ApprovalRefusal) as refused:
        evaluate_use((), grant(), 10)
    assert refused.value.code == "E-APPROVAL-GRANT-UNISSUED"


def test_grant_ancestry_requires_parents_to_precede_descendants() -> None:
    child = grant()
    child_issued = SpecificationEvent(
        "child-issued", "GRANT_ISSUED", 1, "sha256:" + "b" * 64, child.c_digest,
        "child", "parent", "owner", "key", None, "OK",
    )
    parent_issued = SpecificationEvent(
        "parent-issued", "GRANT_ISSUED", 2, "sha256:" + "b" * 64, child.c_digest,
        "parent", None, "owner", "key", child_issued.digest, "OK",
    )
    with __import__("pytest").raises(ApprovalRefusal) as refused:
        evaluate_use((child_issued, parent_issued), child, 3)
    assert refused.value.code == "E-APPROVAL-GRANT-UNISSUED"

    ordered_parent = __import__("dataclasses").replace(parent_issued, seq=1, previous_event_digest=None)
    ordered_child = __import__("dataclasses").replace(child_issued, seq=2, previous_event_digest=ordered_parent.digest)
    assert evaluate_use((ordered_parent, ordered_child), child, 3).valid is True


def test_use_refuses_duplicate_grant_issuance_that_would_reparent_a_child() -> None:
    child = grant()
    parent_a = event("GRANT_ISSUED", 1, "parent-a")
    first_child_issuance = SpecificationEvent(
        "child-issued-a", "GRANT_ISSUED", 2, "sha256:" + "b" * 64, child.c_digest,
        "child", "parent-a", "owner", "key", parent_a.digest, "OK",
    )
    parent_b = SpecificationEvent(
        "parent-issued-b", "GRANT_ISSUED", 3, "sha256:" + "b" * 64, child.c_digest,
        "parent", None, "owner", "key", first_child_issuance.digest, "OK",
    )
    second_child_issuance = SpecificationEvent(
        "child-issued-b", "GRANT_ISSUED", 4, "sha256:" + "b" * 64, child.c_digest,
        "child", "parent", "owner", "key", parent_b.digest, "OK",
    )
    with __import__("pytest").raises(ApprovalRefusal) as refused:
        evaluate_use((parent_a, first_child_issuance, parent_b, second_child_issuance), child, 5)
    assert refused.value.code == "E-APPROVAL-GRANT-DUPLICATE"
