"""Pure orchestration for the pre-implementation specification lifecycle."""

from __future__ import annotations

from ranex.foundation.canonical import canonical_json, canonical_sha256
from ranex.foundation.specification_abc import (
    SpecificationABCError,
    assert_abc_chain,
    canonical_payload_bytes,
    parse_strict_json,
    payload_digest,
    validate_approval_envelope,
    validate_generated_artifact_manifest,
    validate_spec_packet,
)
from ranex.governed_execution.domain.specification import (
    TRANSITION_TABLE,
    ClarificationInput,
    LifecycleSession,
    LifecycleState,
    RefusalCode,
    TransitionResult,
)


def _request_digest(request: ClarificationInput) -> str:
    return "sha256:" + canonical_sha256(request.as_record())


def draft(request: ClarificationInput) -> LifecycleSession:
    """Start a session. Validation is a transition, not an implicit advance."""

    return LifecycleSession(
        state=LifecycleState.DRAFT,
        actor_id=request.actor_id,
        base_digest=request.base_digest,
    )


def render_questions(request: ClarificationInput) -> str:
    """Render only canonical question facts; prose cannot supply an answer."""

    return canonical_json({"questions": [question.as_record() for question in request.questions]})


def _refuse(
    session: LifecycleSession,
    request: ClarificationInput,
    code: RefusalCode,
    *,
    cause: str | None = None,
) -> TransitionResult:
    return TransitionResult(
        accepted=False,
        session=session,
        actor_id=request.actor_id,
        code=code,
        semantic_digest=session.semantic_digest,
        cause=cause,
    )


def _question_refusal(request: ClarificationInput) -> RefusalCode | None:
    question_ids = [question.question_id for question in request.questions]
    if not question_ids or len(question_ids) != len(set(question_ids)):
        return RefusalCode.MISSING_ANSWER
    for question in request.questions:
        if not question.question_id or not question.prompt:
            return RefusalCode.MISSING_ANSWER
        if len(question.allowed_answers) != 1 or not question.allowed_answers[0]:
            return RefusalCode.AMBIGUOUS_QUESTION
    answer_ids = [answer.question_id for answer in request.answers]
    if set(answer_ids) - set(question_ids):
        return RefusalCode.UNKNOWN_ANSWER
    if len(answer_ids) != len(set(answer_ids)) or set(answer_ids) != set(question_ids):
        return RefusalCode.MISSING_ANSWER
    allowed = {question.question_id: question.allowed_answers[0] for question in request.questions}
    if any(not answer.value or allowed.get(answer.question_id) != answer.value for answer in request.answers):
        return RefusalCode.CONTRADICTORY_ANSWER
    return None


def _has_observed_only_intent(request: ClarificationInput) -> bool:
    return any(len(item) == 3 and item[2] == "observed-only" for item in request.observations)


def _validated_specification(request: ClarificationInput) -> str:
    # Parsing canonical A bytes first exercises the strict-byte parser while the
    # public input remains a closed, serializable lifecycle record.
    parsed = parse_strict_json(canonical_payload_bytes(request.spec_packet))
    checked = validate_spec_packet(parsed)
    if not checked["non_goals"]:
        raise SpecificationABCError("E-ABC-000", "non_goals must not be empty")
    return payload_digest(checked)


def advance(session: LifecycleSession, request: ClarificationInput) -> TransitionResult:
    """Advance exactly one guarded transition, returning refusals as data."""

    try:
        request_digest = _request_digest(request)
        if session.last_request_digest == request_digest:
            return TransitionResult(True, session, request.actor_id, semantic_digest=session.semantic_digest)
        if not isinstance(request.target, LifecycleState):
            return _refuse(session, request, RefusalCode.INVALID_INPUT)
        if not request.actor_id:
            return _refuse(session, request, RefusalCode.MISSING_ACTOR)
        if request.actor_id != session.actor_id:
            return _refuse(session, request, RefusalCode.ACTOR_MISMATCH)
        if request.base_digest != session.base_digest:
            return _refuse(session, request, RefusalCode.STALE_BASE)
        if _has_observed_only_intent(request):
            return _refuse(session, request, RefusalCode.OBSERVED_ONLY_INTENT)
        question_code = _question_refusal(request)
        if question_code is not None:
            return _refuse(session, request, question_code)
        destination = TRANSITION_TABLE.get(session.state)
        if destination is None or request.target is not destination:
            return _refuse(session, request, RefusalCode.OUT_OF_ORDER)
    except (TypeError, AttributeError, KeyError, IndexError, ValueError):
        return _refuse(session, request, RefusalCode.INVALID_INPUT)

    try:
        if session.state is LifecycleState.DRAFT:
            semantic_digest = _validated_specification(request)
        elif session.state is LifecycleState.SPEC_VALIDATED:
            validate_generated_artifact_manifest(request.manifest, spec_packet=request.spec_packet)
            semantic_digest = session.semantic_digest
        else:
            # SLICE-032 owns durable nonce tracking; this lifecycle has no nonce state.
            validate_approval_envelope(request.approval_envelope, used_nonces=())
            semantic_digest = session.semantic_digest
    except SpecificationABCError as exc:
        code = {
            LifecycleState.DRAFT: RefusalCode.INVALID_SPECIFICATION,
            LifecycleState.SPEC_VALIDATED: RefusalCode.INVALID_MANIFEST,
            LifecycleState.TESTS_MAPPED: RefusalCode.INVALID_APPROVAL,
        }[session.state]
        return _refuse(session, request, code, cause=exc.code)
    except (TypeError, AttributeError, KeyError, IndexError, ValueError):
        return _refuse(session, request, RefusalCode.INVALID_INPUT)

    if session.state is LifecycleState.TESTS_MAPPED:
        try:
            assert_abc_chain(
                request.spec_packet,
                request.manifest,
                request.approval_envelope,
                used_nonces=(),
            )
        except SpecificationABCError as exc:
            return _refuse(session, request, RefusalCode.CHAIN_MISMATCH, cause=exc.code)
        except (TypeError, AttributeError, KeyError, IndexError, ValueError):
            return _refuse(session, request, RefusalCode.INVALID_INPUT)

    advanced = LifecycleSession(
        state=destination,
        actor_id=session.actor_id,
        base_digest=session.base_digest,
        semantic_digest=semantic_digest,
        last_request_digest=request_digest,
    )
    return TransitionResult(True, advanced, request.actor_id, semantic_digest=semantic_digest)


__all__ = ["advance", "draft", "render_questions"]
