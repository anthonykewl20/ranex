from __future__ import annotations

import copy
import json
from pathlib import Path

from ranex.foundation.specification_abc import payload_digest, sign_approval_payload
from ranex.governed_execution.application.specification import advance, draft, render_questions
from ranex.governed_execution.domain.specification import (
    ClarificationAnswer,
    ClarificationInput,
    LifecycleSession,
    LifecycleState,
    Question,
    RefusalCode,
)

VECTORS = json.loads(
    (Path(__file__).parents[1] / "contract/fixtures/specification/abc-v1-vectors.json").read_text()
)


def clarification(**changes: object) -> ClarificationInput:
    triple = copy.deepcopy(VECTORS["triple"])
    values: dict[str, object] = {
        "actor_id": "owner",
        "target": LifecycleState.SPEC_VALIDATED,
        "base_digest": triple["c_payload"]["base_digest"],
        "spec_packet": triple["a"],
        "manifest": triple["b"],
        "approval_envelope": {
            "version": "approval-envelope-v1",
            "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
            "payload": triple["c_payload"],
            "key_id": triple["key_id"],
            "signature": triple["signature"],
        },
        "questions": (Question("Q-1", "Confirm scope", ("owner approved",)),),
        "answers": (ClarificationAnswer("Q-1", "owner approved"),),
        "observations": (),
    }
    values.update(changes)
    return ClarificationInput(**values)


def test_transition_table_and_refusals_are_closed() -> None:
    session = draft(clarification(target=LifecycleState.SPEC_VALIDATED))
    expected = (
        (LifecycleState.DRAFT, LifecycleState.SPEC_VALIDATED),
        (LifecycleState.SPEC_VALIDATED, LifecycleState.TESTS_MAPPED),
        (LifecycleState.TESTS_MAPPED, LifecycleState.APPROVAL_PENDING),
    )
    for source, destination in expected:
        assert session.state is source
        result = advance(session, clarification(target=destination))
        assert result.accepted and result.session.state is destination
        session = result.session
    refused = advance(session, clarification(target=LifecycleState.TESTS_MAPPED))
    assert not refused.accepted
    assert refused.code is RefusalCode.OUT_OF_ORDER
    assert refused.session.state is LifecycleState.APPROVAL_PENDING


def test_actor_base_and_answer_guards_are_distinct() -> None:
    session = draft(clarification())
    cases = (
        (clarification(actor_id=""), RefusalCode.MISSING_ACTOR),
        (clarification(actor_id="reviewer"), RefusalCode.ACTOR_MISMATCH),
        (clarification(base_digest="sha256:" + "0" * 64), RefusalCode.STALE_BASE),
        (clarification(answers=()), RefusalCode.MISSING_ANSWER),
        (
            clarification(answers=(ClarificationAnswer("Q-2", "owner approved"),)),
            RefusalCode.UNKNOWN_ANSWER,
        ),
        (
            clarification(answers=(ClarificationAnswer("Q-1", "different"),)),
            RefusalCode.CONTRADICTORY_ANSWER,
        ),
        (
            clarification(questions=(Question("Q-1", "Confirm scope", ("yes", "no")),)),
            RefusalCode.AMBIGUOUS_QUESTION,
        ),
    )
    for request, code in cases:
        result = advance(session, request)
        assert not result.accepted
        assert result.code is code
        assert result.actor_id == request.actor_id


def test_foundation_refusals_preserve_causes_and_lifecycle_context() -> None:
    invalid_specification = copy.deepcopy(VECTORS["triple"]["a"])
    invalid_specification["ids"]["question"] = ["Q-1", "Q-1"]
    rejected_specification = advance(
        draft(clarification()),
        clarification(spec_packet=invalid_specification),
    )
    assert rejected_specification.code is RefusalCode.INVALID_SPECIFICATION
    assert rejected_specification.cause == "E-ABC-020"

    validated = advance(draft(clarification()), clarification())
    assert validated.accepted
    rejected_manifest = advance(
        validated.session,
        clarification(target=LifecycleState.TESTS_MAPPED, manifest={}),
    )
    assert rejected_manifest.code is RefusalCode.INVALID_MANIFEST
    assert rejected_manifest.cause == "E-ABC-012"


def test_approval_validation_and_chain_binding_refusals_are_distinct() -> None:
    validated = advance(draft(clarification()), clarification())
    assert validated.accepted
    mapped = advance(validated.session, clarification(target=LifecycleState.TESTS_MAPPED))
    assert mapped.accepted

    invalid_envelope = copy.deepcopy(clarification().approval_envelope)
    invalid_envelope["signature"] = "not-a-signature"
    rejected_envelope = advance(
        mapped.session,
        clarification(target=LifecycleState.APPROVAL_PENDING, approval_envelope=invalid_envelope),
    )
    assert rejected_envelope.code is RefusalCode.INVALID_APPROVAL
    assert rejected_envelope.cause == "E-ABC-016"

    unbound_envelope = copy.deepcopy(clarification().approval_envelope)
    unbound_envelope["payload"]["b_digest"] = "sha256:" + "f" * 64
    unbound_envelope["signature"] = sign_approval_payload(
        unbound_envelope["payload"],
        "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=",
    )
    rejected_chain = advance(
        mapped.session,
        clarification(target=LifecycleState.APPROVAL_PENDING, approval_envelope=unbound_envelope),
    )
    assert rejected_chain.code is RefusalCode.CHAIN_MISMATCH
    assert rejected_chain.cause == "E-ABC-019"


def test_malformed_clarification_items_become_durable_invalid_input_refusals() -> None:
    session = draft(clarification())
    for request in (
        clarification(observations=(None,)),
        clarification(questions=(None,)),
    ):
        result = advance(session, request)
        assert result.code is RefusalCode.INVALID_INPUT
        assert not result.accepted


def test_retry_returns_the_recorded_result_without_an_effect() -> None:
    request = clarification(target=LifecycleState.SPEC_VALIDATED)
    initial = draft(request)
    result = advance(initial, request)
    assert advance(result.session, request) == result
    assert result.as_record() == advance(result.session, request).as_record()


def test_same_target_retry_survives_session_reconstruction() -> None:
    request = clarification(target=LifecycleState.SPEC_VALIDATED)
    result = advance(draft(request), request)
    reconstructed = LifecycleSession.from_record(result.session.as_record())
    assert advance(reconstructed, request).as_record() == result.as_record()


def test_questions_and_semantic_digest_are_stable() -> None:
    request = clarification(target=LifecycleState.SPEC_VALIDATED)
    assert render_questions(request) == render_questions(clarification())
    first = advance(draft(request), request)
    second_request = clarification(target=LifecycleState.SPEC_VALIDATED)
    second = advance(draft(second_request), second_request)
    assert first.semantic_digest == second.semantic_digest == payload_digest(request.spec_packet)


def test_observed_only_facts_cannot_promote_intent() -> None:
    request = clarification(observations=(("O-1", "runtime says it works", "observed-only"),))
    result = advance(draft(request), request)
    assert not result.accepted
    assert result.code is RefusalCode.OBSERVED_ONLY_INTENT


def test_no_preapproval_authority_is_exposed() -> None:
    from ranex.governed_execution.application import specification

    assert all("capability" not in name.lower() for name in specification.__all__)
    assert all("producer" not in name.lower() for name in specification.__all__)
    assert draft(clarification()).state is LifecycleState.DRAFT
