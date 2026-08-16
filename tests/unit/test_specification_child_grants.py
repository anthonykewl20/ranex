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
    return CapabilityGrant("parent", "sha256:" + "a" * 64, None, capability(), "worker", "eval", "pub", 1, 20)


def issue(grant_id: str, request: PolicyCapabilities, parent_grant: CapabilityGrant, policy: PolicyCapabilities, **kwargs: object) -> tuple[CapabilityGrant, object]:
    return issue_child_grant(
        grant_id, request, parent_grant, policy, journal_position=kwargs.pop("journal_position", 2),
        journal_head_link="sha256:" + "b" * 64, prior_events=kwargs.pop("prior_events", ()),
        principal_id="owner", key_id="key", **kwargs,
    )


def test_child_intersection_is_closed_and_never_expands() -> None:
    request = capability(roots=["src"], actions=["read"], environment={"allow": ["PATH"]})
    grant, issued = issue("child", request, parent(), capability())
    assert grant.capabilities.roots == ("src",)
    assert grant.capabilities.actions == ("read",)
    assert grant.capabilities.secret_allow is False
    assert grant.capabilities.secret_names == ()
    assert grant.capabilities.commit_allow is False
    assert grant.capabilities.network_allow is True
    assert grant.publisher_key is None
    assert "publisher_key" not in grant.as_record()
    assert issued.kind == "GRANT_ISSUED"

    offline, _ = issue(
        "offline", capability(network={"allow": False, "hosts": ["example.test"]}), parent(), capability()
    )
    assert offline.capabilities.network_allow is False
    assert offline.capabilities.network_hosts == ()

    disjoint_hosts, _ = issue(
        "disjoint-hosts", capability(network={"allow": True, "hosts": ["other.test"]}), parent(), capability()
    )
    assert disjoint_hosts.capabilities.network_allow is False
    assert disjoint_hosts.capabilities.network_hosts == ()


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
    existing, issued = issue("one", capability(roots=["src"], actions=["read"]), parent(), capability())
    with pytest.raises(ApprovalRefusal, match="OVERLAP"):
        issue("two", capability(roots=["src"], actions=["read"]), parent(), capability(), siblings=(existing,), prior_events=(issued,))
    with pytest.raises(ApprovalRefusal, match="OVERLAP"):
        issue("nested", capability(roots=["src/x"], actions=["read"]), parent(), capability(), siblings=(existing,), prior_events=(issued,))
    grant, _ = issue("two", capability(roots=["tests"], actions=["read"]), parent(), capability(), siblings=(existing,), prior_events=(issued,))
    assert grant.grant_id == "two"


def test_reordered_argv_is_a_refused_child_expansion() -> None:
    with pytest.raises(ApprovalRefusal, match="EXPANSION"):
        issue("reordered", capability(argv=["pytest", "-m"]), parent(), capability())
