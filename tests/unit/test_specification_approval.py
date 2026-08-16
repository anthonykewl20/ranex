"""Frozen approval issuance vectors for SLICE-032."""

from __future__ import annotations

import copy
import json
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
    pending = ApprovalPendingContext(VECTORS["c_payload"]["subject_digest"], "owner")
    return VECTORS["a"], VECTORS["b"], envelope, policy, pending, roles, position, head


def test_approval_binds_policy_roles_head_nonce_and_window() -> None:
    args = approved_input()
    outcome = issue_approval(*args)
    assert outcome.c_digest == payload_digest(args[2]["payload"])
    assert outcome.grant.capabilities.as_record() == args[3].as_record()
    assert outcome.approved_event.kind == "APPROVED"
    assert outcome.implementable_event.kind == "IMPLEMENTABLE"

    for position in (10, 20):
        assert issue_approval(*approved_input(position=position)).c_digest == outcome.c_digest
    for position in (9, 21):
        with pytest.raises(ApprovalRefusal) as refused:
            issue_approval(*approved_input(position=position))
        assert refused.value.code == "E-APPROVAL-WINDOW"

    stale = approved_input(head="sha256:" + "a" * 64)
    stale[2]["payload"]["journal_predecessor"] = "sha256:" + "b" * 64
    stale[2]["signature"] = sign_approval_payload(stale[2]["payload"], PRIVATE)
    with pytest.raises(ApprovalRefusal, match="PREDECESSOR"):
        issue_approval(*stale)

    conflicting = list(args[5].assignments)
    conflicting.append(RoleAssignment("bad", "worker", args[2]["payload"]["key"], "worker", outcome.c_digest))
    with pytest.raises(ApprovalRefusal, match="ROLE"):
        issue_approval(*args[:5], RoleAssignments(tuple(conflicting)), *args[6:])


def test_successful_approval_nonce_is_the_only_nonce_that_is_consumed() -> None:
    args = approved_input()
    first = issue_approval(*args)
    with pytest.raises(ApprovalRefusal) as refused:
        issue_approval(*args, prior_events=(first.approved_event,))
    assert refused.value.code == "E-ABC-015"
