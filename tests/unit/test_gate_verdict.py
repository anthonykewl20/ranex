"""Behavioural contracts BC-1..BC-7 of the first walking skeleton.

Written before the implementation, per ADR-0008. Each test names the contract it
enforces so a failure points at the contract, not just at a line number.
"""

from __future__ import annotations

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    Verdict,
    evaluate,
)

SUBJECT = "sha256:" + "a" * 64
OTHER_SUBJECT = "sha256:" + "b" * 64

# SLICE-003: a claim names the argv that satisfies it, and evidence names the
# argv that ran. BC-1..BC-7 are about the other conditions, so both sides use
# the same command throughout and the binding stays out of the way.
COMMAND = ["pytest", "-q"]
COMMAND_DIGEST = "sha256:" + canonical_sha256(COMMAND)
EXECUTABLE = "/usr/bin/pytest"


def gate(*claims: str, blocking: bool = True) -> Gate:
    return Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=tuple(
            Claim(claim_id=c, command_digest=COMMAND_DIGEST) for c in claims
        ),
        blocking=blocking,
    )


def evidence(claim: str, subject: str = SUBJECT, producer: str = "worker") -> Evidence:
    return Evidence(
        claim_id=claim,
        subject_digest=subject,
        producer_id=producer,
        command=" ".join(COMMAND),
        command_digest=COMMAND_DIGEST,
        executable_path=EXECUTABLE,
        exit_code=0,
    )


# --- BC-1 -------------------------------------------------------------------


def test_bc1_required_claim_with_satisfying_evidence_passes() -> None:
    result = evaluate(
        gate("tests-executed"),
        (evidence("tests-executed"),),
        subject_digest=SUBJECT,
        approver_id="owner",
    )
    assert result.verdict is Verdict.PASS
    assert result.missing_claims == ()
    assert result.reason is None


# --- BC-2 : absence blocks --------------------------------------------------


def test_bc2_required_claim_with_no_evidence_fails() -> None:
    result = evaluate(
        gate("tests-executed"),
        (),
        subject_digest=SUBJECT,
        approver_id="owner",
    )
    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)
    assert result.failing_rule == "TESTS_EXECUTED"


def test_bc2_absence_never_defaults_to_pass_even_with_other_evidence() -> None:
    result = evaluate(
        gate("tests-executed", "review-recorded"),
        (evidence("tests-executed"),),
        subject_digest=SUBJECT,
        approver_id="owner",
    )
    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("review-recorded",)


# --- BC-3 : exact-subject binding -------------------------------------------


def test_bc3_evidence_for_a_different_subject_is_not_evidence() -> None:
    result = evaluate(
        gate("tests-executed"),
        (evidence("tests-executed", subject=OTHER_SUBJECT),),
        subject_digest=SUBJECT,
        approver_id="owner",
    )
    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)
    assert "subject" in (result.reason or "").lower()


# --- BC-4 : determinism -----------------------------------------------------


def test_bc4_identical_inputs_produce_identical_records() -> None:
    args = (gate("tests-executed"), (evidence("tests-executed"),))
    a = evaluate(*args, subject_digest=SUBJECT, approver_id="owner")
    b = evaluate(*args, subject_digest=SUBJECT, approver_id="owner")
    assert a.record_digest == b.record_digest
    assert a.as_record() == b.as_record()


# --- BC-5 : no model in the enforcement path --------------------------------


def test_bc5_no_model_is_consulted() -> None:
    """The verdict module must not import or reach any model client.

    Structural, not behavioural: a network or model import in this path would be
    a defect regardless of whether a test happened to exercise it.
    """
    import ranex.governed_execution.domain.verdict as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as handle:
        text = handle.read()
    for forbidden in ("requests", "httpx", "urllib", "openai", "anthropic", "socket"):
        assert forbidden not in text, f"enforcement path references {forbidden!r}"


# --- BC-6 : no self-approval ------------------------------------------------


def test_bc6_producer_may_not_approve_own_work() -> None:
    result = evaluate(
        gate("tests-executed"),
        (evidence("tests-executed", producer="worker"),),
        subject_digest=SUBJECT,
        approver_id="worker",
    )
    assert result.verdict is Verdict.FAIL
    assert "self-approval" in (result.reason or "").lower()


# --- BC-7 : a gate must be able to block ------------------------------------


def test_bc7_non_blocking_gate_is_refused_at_construction() -> None:
    with pytest.raises(ValueError, match="blocking"):
        gate("tests-executed", blocking=False)


# --- failure modes ----------------------------------------------------------


def test_gate_with_no_required_claims_is_refused() -> None:
    with pytest.raises(ValueError, match="required_claims"):
        Gate(
            gate_id="landing",
            rule_id="TESTS_EXECUTED",
            required_claims=(),
            blocking=True,
        )


def test_duplicate_claim_ids_are_refused() -> None:
    with pytest.raises(ValueError, match="unique"):
        gate("tests-executed", "tests-executed")


def test_empty_kernel_identifier_is_refused() -> None:
    with pytest.raises(ValueError, match="claim_id must be a non-empty string"):
        Claim(claim_id=" ", command_digest=COMMAND_DIGEST)


def test_non_integer_evidence_exit_code_is_refused() -> None:
    with pytest.raises(ValueError, match="exit_code must be an integer"):
        Evidence(
            claim_id="tests-executed",
            subject_digest=SUBJECT,
            producer_id="worker",
            command=" ".join(COMMAND),
            command_digest=COMMAND_DIGEST,
            executable_path=EXECUTABLE,
            exit_code=True,
        )


def test_malformed_subject_digest_is_refused() -> None:
    with pytest.raises(ValueError, match="digest"):
        evaluate(
            gate("tests-executed"),
            (),
            subject_digest="not-a-digest",
            approver_id="owner",
        )


def test_evidence_with_nonzero_exit_does_not_satisfy_a_claim() -> None:
    failed = Evidence(
        claim_id="tests-executed",
        subject_digest=SUBJECT,
        producer_id="worker",
        command=" ".join(COMMAND),
        command_digest=COMMAND_DIGEST,
        executable_path=EXECUTABLE,
        exit_code=1,
    )
    result = evaluate(
        gate("tests-executed"), (failed,), subject_digest=SUBJECT, approver_id="owner"
    )
    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)
