"""Frozen least-authority child grant vectors for SLICE-032."""

from __future__ import annotations

import copy

import pytest

from ranex.governed_execution.domain.specification_approval import (
    ApprovalRefusal,
    CapabilityGrant,
    PolicyCapabilities,
    issue_child_grant,
)


def capability(**changes: object) -> PolicyCapabilities:
    record = {
        "executable": "python", "argv": ["-m", "pytest"], "cwd": ".",
        "roots": ["src", "tests"], "actions": ["read", "write"],
        "environment": {"allow": ["PATH", "HOME"]},
        "network": {"allow": True, "hosts": ["example.test"]},
        "secret": {"allow": True, "names": ["TOKEN"]},
        "commit": {"allow": True}, "subagent": {"allow": True, "max_children": 2},
    }
    record.update(changes)
    return PolicyCapabilities.from_record(record)


def parent() -> CapabilityGrant:
    return CapabilityGrant("parent", "sha256:" + "a" * 64, None, capability(), "worker", "eval", "pub")


def test_child_intersection_is_closed_and_never_expands() -> None:
    request = capability(roots=["src"], actions=["read"], environment={"allow": ["PATH"]})
    grant = issue_child_grant("child", request, parent(), capability())
    assert grant.capabilities.roots == ("src",)
    assert grant.capabilities.actions == ("read",)
    assert grant.capabilities.secret_allow is False
    assert grant.capabilities.secret_names == ()
    assert grant.capabilities.commit_allow is False
    assert grant.capabilities.network_allow is True
    assert grant.publisher_key is None
    assert "publisher_key" not in grant.as_record()

    offline = issue_child_grant(
        "offline", capability(network={"allow": False, "hosts": ["example.test"]}), parent(), capability()
    )
    assert offline.capabilities.network_allow is False
    assert offline.capabilities.network_hosts == ()


def test_capability_grammar_refuses_ambiguous_authority() -> None:
    for record in (
        {"roots": "src"}, {"roots": ["src/*"]}, {"roots": ["../src"]},
        {"roots": ["src\\bad"]}, {"subagent": {"allow": True, "max_children": True}},
    ):
        raw = copy.deepcopy(capability().as_record())
        raw.update(record)
        with pytest.raises(ApprovalRefusal):
            PolicyCapabilities.from_record(raw)


def test_sibling_path_action_scopes_are_disjoint() -> None:
    existing = issue_child_grant("one", capability(roots=["src"], actions=["read"]), parent(), capability())
    with pytest.raises(ApprovalRefusal, match="OVERLAP"):
        issue_child_grant("two", capability(roots=["src"], actions=["read"]), parent(), capability(), siblings=(existing,))
    grant = issue_child_grant("two", capability(roots=["tests"], actions=["read"]), parent(), capability(), siblings=(existing,))
    assert grant.grant_id == "two"
