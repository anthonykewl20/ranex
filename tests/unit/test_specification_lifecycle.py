from __future__ import annotations

import copy
import json
from pathlib import Path

from ranex.foundation.specification_abc import payload_digest
from ranex.governed_execution.application.specification import advance, draft, render_questions
from ranex.governed_execution.domain.specification import (
    ClarificationAnswer,
    ClarificationInput,
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


def to_pending() -> tuple[object, ClarificationInput]:
    request = clarification()
    session = draft(request)
    for _ in range(2):
        result = advance(session, request)
        assert result.accepted
        session = result.session
    return session, request


def test_transition_table_and_refusals_are_closed() -> None:
    request = clarification()
    session = draft(request)
    expected = (
        (LifecycleState.DRAFT, LifecycleState.SPEC_VALIDATED),
        (LifecycleState.SPEC_VALIDATED, LifecycleState.TESTS_MAPPED),
        (LifecycleState.TESTS_MAPPED, LifecycleState.APPROVAL_PENDING),
    )
    for source, destination in expected:
        assert session.state is source
        result = advance(session, request)
        assert result.accepted and result.session.state is destination
        session = result.session
    refused = advance(session, request)
    assert not refused.accepted
    assert refused.code is RefusalCode.OUT_OF_ORDER
    assert refused.session.state is LifecycleState.APPROVAL_PENDING


def test_actor_base_and_answer_guards_are_distinct() -> None:
    session = draft(clarification())
    cases = (
        (clarification(actor_id="reviewer"), RefusalCode.ACTOR_MISMATCH),
        (clarification(base_digest="sha256:" + "0" * 64), RefusalCode.STALE_BASE),
        (clarification(answers=()), RefusalCode.MISSING_ANSWER),
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


def test_retry_returns_the_recorded_result_without_an_effect() -> None:
    request = clarification()
    initial = draft(request)
    result = advance(initial, request)
    assert advance(result.session, request) == result
    assert result.as_record() == advance(result.session, request).as_record()


def test_questions_and_semantic_digest_are_stable() -> None:
    request = clarification()
    assert render_questions(request) == render_questions(clarification())
    first = advance(draft(request), request)
    second = advance(draft(clarification()), clarification())
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
