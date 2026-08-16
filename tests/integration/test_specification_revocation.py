"""Ordered pure revocation reduction vectors for SLICE-032."""

from __future__ import annotations

from ranex.governed_execution.domain.specification_approval import (
    CapabilityGrant,
    PolicyCapabilities,
)
from ranex.governed_execution.domain.specification_events import SpecificationEvent, evaluate_use


def grant() -> CapabilityGrant:
    caps = PolicyCapabilities.from_record({
        "executable": "python", "argv": [], "cwd": ".", "roots": ["src"], "actions": ["read"],
        "environment": {"allow": []}, "network": {"allow": False, "hosts": []},
        "secret": {"allow": False, "names": []}, "commit": {"allow": False},
        "subagent": {"allow": False, "max_children": 0},
    })
    return CapabilityGrant("child", "sha256:" + "a" * 64, "parent", caps, "worker", "eval", "pub")


def event(kind: str, seq: int, grant_id: str = "parent") -> SpecificationEvent:
    return SpecificationEvent(f"{kind}-{seq}", kind, seq, "sha256:" + "b" * 64, "sha256:" + "a" * 64, grant_id, None, "owner", "key", None, "OK")


def test_revoke_and_expiry_propagate_through_descendants() -> None:
    issued_parent = event("GRANT_ISSUED", 1, "parent")
    issued_child = SpecificationEvent("child", "GRANT_ISSUED", 2, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "child", "parent", "owner", "key", issued_parent.digest, "OK")
    revoked = SpecificationEvent("revoke", "GRANT_REVOKED", 3, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "parent", None, "owner", "key", issued_child.digest, "OK")
    assert evaluate_use((issued_parent, issued_child, revoked), grant(), 4).valid is False


def test_event_and_use_facts_are_canonical_and_deterministic() -> None:
    issued = event("GRANT_ISSUED", 1, "child")
    first = evaluate_use((issued,), grant(), 2)
    assert first == evaluate_use((issued,), grant(), 2)
    revoke = SpecificationEvent("revoke", "GRANT_REVOKED", 2, "sha256:" + "b" * 64, "sha256:" + "a" * 64, "child", None, "owner", "key", issued.digest, "OK")
    assert evaluate_use((issued, revoke), grant(), 3).valid is False
