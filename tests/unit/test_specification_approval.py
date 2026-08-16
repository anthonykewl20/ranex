"""Frozen approval issuance vectors for SLICE-032."""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import payload_digest, sign_approval_payload
from ranex.governed_execution.application.specification_approval import issue_approval
from ranex.governed_execution.domain.specification_approval import (
    ApprovalPendingContext,
    ApprovalRefusal,
    PolicyCapabilities,
    RoleAssignment,
    RoleAssignments,
)

VECTORS = json.loads(
    (Path(__file__).parents[1] / "contract/fixtures/specification/abc-v1-vectors.json").read_text()
)["triple"]
PRIVATE = "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="


def approved_input(*, position: int = 10, head: str | None = "sha256:" + "f" * 64):
    policy = PolicyCapabilities.from_record(VECTORS["c_payload"]["capability_request"])
    payload = copy.deepcopy(VECTORS["c_payload"])
    payload["profile_digests"]["policy"] = policy.digest
    payload["journal_predecessor"] = head
    payload["time_window"] = {"not_before": 10, "not_after": 20}
    envelope = {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": payload,
        "key_id": payload["key"],
        "signature": sign_approval_payload(payload, PRIVATE),
    }
    c_digest = payload_digest(payload)
    roles = RoleAssignments(
        (
            RoleAssignment("approver", "owner", payload["key"], "approver", c_digest),
            RoleAssignment("worker", "worker", "ed25519:ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA=", "worker", c_digest),
            RoleAssignment("evaluator", "evaluator", "ed25519:QEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEA=", "evaluator", c_digest),
            RoleAssignment("publisher", "publisher", "ed25519:YGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGBgYGA=", "publisher", c_digest),
        )
    )
    pending = ApprovalPendingContext(payload_digest(VECTORS["a"]), VECTORS["c_payload"]["subject_digest"], "owner")
    return VECTORS["a"], VECTORS["b"], envelope, policy, pending, roles, position, head


def test_approval_binds_policy_roles_head_nonce_and_window() -> None:
    args = approved_input()
    outcome = issue_approval(*args, prior_events=(), prior_event_head=None)
    assert outcome.c_digest == payload_digest(args[2]["payload"])
    assert outcome.grant.capabilities.as_record() == args[3].as_record()
    assert outcome.approved_event.kind == "APPROVED"
    assert outcome.implementable_event.kind == "IMPLEMENTABLE"
    assert outcome.grant_issued_event.kind == "GRANT_ISSUED"
    assert outcome.expiry_recorded_event.kind == "EXPIRY_RECORDED"
    assert outcome.expiry_recorded_event.seq == 21
    assert outcome.grant.not_before == 10
    assert outcome.grant.not_after == 20

    for position in (10, 18):
        assert issue_approval(*approved_input(position=position), prior_events=(), prior_event_head=None).c_digest == outcome.c_digest
    for position in (9, 19, 20, 21):
        with pytest.raises(ApprovalRefusal) as refused:
            issue_approval(*approved_input(position=position), prior_events=(), prior_event_head=None)
        assert refused.value.code == "E-APPROVAL-WINDOW"

    stale = approved_input(head="sha256:" + "a" * 64)
    stale[2]["payload"]["journal_predecessor"] = "sha256:" + "b" * 64
    stale[2]["signature"] = sign_approval_payload(stale[2]["payload"], PRIVATE)
    with pytest.raises(ApprovalRefusal, match="PREDECESSOR"):
        issue_approval(*stale, prior_events=(), prior_event_head=None)

    conflicting = list(args[5].assignments)
    conflicting.append(RoleAssignment("bad", "worker", args[2]["payload"]["key"], "worker", outcome.c_digest))
    with pytest.raises(ApprovalRefusal, match="ROLE"):
        issue_approval(*args[:5], RoleAssignments(tuple(conflicting)), *args[6:], prior_events=(), prior_event_head=None)


def test_successful_approval_nonce_is_the_only_nonce_that_is_consumed() -> None:
    args = approved_input()
    first = issue_approval(*args, prior_events=(), prior_event_head=None)
    with pytest.raises(ApprovalRefusal) as refused:
        issue_approval(*args, prior_events=(first.approved_event,), prior_event_head=first.approved_event.digest)
    assert refused.value.code == "E-ABC-015"


def test_argv_order_is_preserved_and_digest_bound() -> None:
    baseline = PolicyCapabilities.from_record(VECTORS["c_payload"]["capability_request"])
    ordered = PolicyCapabilities.from_record({
        **VECTORS["c_payload"]["capability_request"], "argv": ["pytest", "-q"],
    })
    reordered = PolicyCapabilities.from_record({
        **VECTORS["c_payload"]["capability_request"], "argv": ["-q", "pytest"],
    })
    assert ordered.argv == ("pytest", "-q")
    assert ordered.as_record()["argv"] == ["pytest", "-q"]
    assert baseline.as_record()["version"] == "policy-capabilities-v1"
    assert baseline.digest == "sha256:6bbd2e0e5e2a7b02ce001346ab3ad9dafebb0eccef33f447b7cfb2fe5f050b38"
    assert ordered.digest != reordered.digest
    assert replace(ordered, argv=("pytest", "-q")).argv == ("pytest", "-q")


def test_approval_refuses_absent_prior_event_context() -> None:
    with pytest.raises(TypeError):
        issue_approval(*approved_input())


def test_role_assignment_sequence_is_snapshotted_as_a_tuple() -> None:
    assignments = list(approved_input()[5].assignments)
    snapshot = RoleAssignments(assignments)
    assignments.clear()
    assert isinstance(snapshot.assignments, tuple)
    assert len(snapshot.assignments) == 4


def test_approval_pending_context_binds_a_and_subject_to_their_distinct_c_fields() -> None:
    args = approved_input()
    assert issue_approval(*args, prior_events=(), prior_event_head=None).c_digest

    subject_only = ApprovalPendingContext(
        args[2]["payload"]["subject_digest"], args[2]["payload"]["subject_digest"], "owner"
    )
    with pytest.raises(ApprovalRefusal) as refused:
        issue_approval(*args[:4], subject_only, *args[5:], prior_events=(), prior_event_head=None)
    assert refused.value.code == "E-APPROVAL-PENDING"


def test_approval_events_link_only_a_complete_prefix_and_fit_before_expiry() -> None:
    args = approved_input(position=18)
    prefix = __import__("ranex.governed_execution.domain.specification_events", fromlist=["SpecificationEvent"]).SpecificationEvent(
        "prior", "APPROVED", 17, args[-1], "sha256:" + "a" * 64, None, None, "owner", "key", None, "OK"
    )
    outcome = issue_approval(*args, prior_events=(prefix,), prior_event_head=prefix.digest)
    events = (prefix, outcome.approved_event, outcome.implementable_event, outcome.grant_issued_event, outcome.expiry_recorded_event)
    assert [event.seq for event in events] == sorted(event.seq for event in events)
    assert outcome.approved_event.previous_event_digest == prefix.digest
    assert outcome.expiry_recorded_event.seq == 21

    with pytest.raises(ApprovalRefusal) as refused:
        issue_approval(*args, prior_events=(prefix,), prior_event_head=None)
    assert refused.value.code == "E-APPROVAL-EVENT-CHAIN"

    first = __import__("ranex.governed_execution.domain.specification_events", fromlist=["SpecificationEvent"]).SpecificationEvent(
        "first", "APPROVED", 9, args[-1], "sha256:" + "a" * 64, None, None, "owner", "key", None, "OK"
    )
    reordered = __import__("ranex.governed_execution.domain.specification_events", fromlist=["SpecificationEvent"]).SpecificationEvent(
        "reordered", "IMPLEMENTABLE", 5, args[-1], "sha256:" + "a" * 64, None, None, "owner", "key", first.digest, "OK"
    )
    with pytest.raises(ApprovalRefusal) as refused:
        issue_approval(*approved_input(position=10), prior_events=(first, reordered), prior_event_head=reordered.digest)
    assert refused.value.code == "E-APPROVAL-EVENT-CHAIN"
