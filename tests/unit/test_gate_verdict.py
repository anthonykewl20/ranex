"""Behavioural contracts BC-1..BC-7 of the first walking skeleton.

Written before the implementation, per ADR-0008. Each test names the contract it
enforces so a failure points at the contract, not just at a line number.
"""

from __future__ import annotations

from pathlib import Path

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


def observed(claim: str, *, exit_code: int = 0, command_digest: str = COMMAND_DIGEST,
             subject: str = SUBJECT) -> Evidence:
    return Evidence(
        claim_id=claim, subject_digest=subject, producer_id="worker",
        command=" ".join(COMMAND), command_digest=command_digest,
        executable_path=EXECUTABLE, exit_code=exit_code,
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


def test_journal_persists_structured_causes_and_self_approval(tmp_path: Path) -> None:
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    journal = Journal(tmp_path / "journal.sqlite3")
    failed = evaluate(gate("tests-executed"), (), subject_digest=SUBJECT, approver_id="owner")
    self_approved = evaluate(
        gate("tests-executed"), (evidence("tests-executed"),),
        subject_digest=SUBJECT, approver_id="worker",
    )

    journal.append(failed)
    journal.append(self_approved)

    failed_row, self_approval_row = journal.entries()
    assert failed_row["causes"] == [{"cause": "absent", "claim_id": "tests-executed"}]
    assert failed_row["self_approval"] is False
    assert self_approval_row["causes"] == []
    assert self_approval_row["self_approval"] is True


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


def test_claim_refuses_non_boolean_results_required() -> None:
    with pytest.raises(ValueError, match="results_required must be a boolean"):
        Claim(
            claim_id="tests-executed",
            command_digest=COMMAND_DIGEST,
            results_required=1,  # type: ignore[arg-type]
        )


def test_exit_code_only_claim_refuses_suite_manifest_fields() -> None:
    with pytest.raises(
        ValueError,
        match="exit-code-only claims cannot carry suite manifest fields",
    ):
        Claim(
            claim_id="tests-executed",
            command_digest=COMMAND_DIGEST,
            manifest_digest="sha256:" + "c" * 64,
        )


def test_suite_claim_refuses_unsorted_expected_ids() -> None:
    with pytest.raises(
        ValueError,
        match="expected_ids must be a sorted tuple of unique test IDs",
    ):
        Claim(
            claim_id="tests-executed",
            command_digest=COMMAND_DIGEST,
            results_required=True,
            manifest_digest="sha256:" + "c" * 64,
            expected_ids=("tests/test_z.py::test_z", "tests/test_a.py::test_a"),
            expected_skips={},
        )


def test_suite_claim_refuses_non_mapping_expected_skips() -> None:
    with pytest.raises(ValueError, match="expected_skips must be a mapping"):
        Claim(
            claim_id="tests-executed",
            command_digest=COMMAND_DIGEST,
            results_required=True,
            manifest_digest="sha256:" + "c" * 64,
            expected_ids=("tests/test_a.py::test_a",),
            expected_skips=[],  # type: ignore[arg-type]
        )


def test_suite_claim_refuses_expected_skip_without_an_expected_id() -> None:
    with pytest.raises(
        ValueError,
        match="expected_skips must name expected IDs with non-empty reasons",
    ):
        Claim(
            claim_id="tests-executed",
            command_digest=COMMAND_DIGEST,
            results_required=True,
            manifest_digest="sha256:" + "c" * 64,
            expected_ids=("tests/test_a.py::test_a",),
            expected_skips={"tests/test_other.py::test_other": "environment"},
        )


def test_suite_claim_ignores_non_passed_extra_test_ids() -> None:
    manifest = "sha256:" + "c" * 64
    claim = Claim(
        claim_id="tests-executed",
        command_digest=COMMAND_DIGEST,
        results_required=True,
        manifest_digest=manifest,
        expected_ids=("tests/test_a.py::test_a",),
        expected_skips={},
    )
    observed = Evidence(
        claim_id="tests-executed",
        subject_digest=SUBJECT,
        producer_id="worker",
        command=" ".join(COMMAND),
        command_digest=COMMAND_DIGEST,
        executable_path=EXECUTABLE,
        exit_code=0,
        suite_results={
            "manifest_digest": manifest,
            "counts": {
                "passed": 1,
                "skipped": 0,
                "failed": 1,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "non_passed": [["tests/test_extra.py::test_extra", "failed"]],
            "missing": [],
            "extra_count": 1,
            "outcome_digest": "sha256:" + "d" * 64,
        },
    )

    assert observed.satisfies(claim, SUBJECT) is True


def test_suite_diagnosis_names_an_absent_artifact() -> None:
    claim = Claim(
        claim_id="tests-executed",
        command_digest=COMMAND_DIGEST,
        results_required=True,
        manifest_digest="sha256:" + "c" * 64,
        expected_ids=("tests/test_a.py::test_a",),
        expected_skips={},
    )

    assert evidence("tests-executed").suite_diagnosis(claim) == (
        "suite results artifact was absent",
    )


def test_suite_diagnosis_names_a_manifest_digest_mismatch() -> None:
    claim = Claim(
        claim_id="tests-executed",
        command_digest=COMMAND_DIGEST,
        results_required=True,
        manifest_digest="sha256:" + "c" * 64,
        expected_ids=("tests/test_a.py::test_a",),
        expected_skips={},
    )
    observed = Evidence(
        claim_id="tests-executed",
        subject_digest=SUBJECT,
        producer_id="worker",
        command=" ".join(COMMAND),
        command_digest=COMMAND_DIGEST,
        executable_path=EXECUTABLE,
        exit_code=0,
        suite_results={
            "manifest_digest": "sha256:" + "e" * 64,
            "counts": {
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "non_passed": [],
            "missing": [],
            "extra_count": 0,
            "outcome_digest": "sha256:" + "d" * 64,
        },
    )

    assert observed.suite_diagnosis(claim) == (
        "suite manifest digest did not match the claim",
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


def test_structured_causes_cover_every_diagnosis_branch_without_rewording() -> None:
    claim_ids = ("absent", "contradicted", "failed", "mismatched", "stale")
    required = gate(*claim_ids)
    records = (
        evidence("contradicted"),
        observed("contradicted", exit_code=1),
        observed("failed", exit_code=1),
        observed("mismatched", command_digest="sha256:" + "c" * 64),
        evidence("stale", subject=OTHER_SUBJECT),
    )
    result = evaluate(required, records, subject_digest=SUBJECT, approver_id="owner")
    assert [(cause.claim_id, cause.cause, cause.detail) for cause in result.causes] == [
        ("contradicted", "contradicted", None),
        ("failed", "failed", None),
        ("mismatched", "mismatched", None),
        ("stale", "stale", None),
        ("absent", "absent", None),
    ]
    assert result.reason == (
        "contradictory evidence — the same claim, subject and command reported both success and failure: contradicted; "
        "the bound command was observed failing: failed; evidence describes a command the claim does not bind: mismatched; "
        "evidence bound to a different subject digest: stale; no evidence for required claim: absent"
    )


def test_suite_failure_is_failed_detail_not_a_sixth_cause() -> None:
    claim = Claim(
        claim_id="suite", command_digest=COMMAND_DIGEST, results_required=True,
        manifest_digest="sha256:" + "c" * 64,
        expected_ids=("tests/test_a.py::test_a",), expected_skips={},
    )
    result = evaluate(
        Gate("landing", "TESTS_EXECUTED", (claim,), True),
        (evidence("suite"),), subject_digest=SUBJECT, approver_id="owner",
    )
    assert [(item.claim_id, item.cause, item.detail) for item in result.causes] == [
        ("suite", "failed", "suite results artifact was absent")
    ]
    assert result.reason == "suite: suite results artifact was absent"


def test_self_approval_is_data_not_a_claim_cause() -> None:
    result = evaluate(
        gate("tests-executed"), (evidence("tests-executed", producer="worker"),),
        subject_digest=SUBJECT, approver_id="worker",
    )
    assert result.self_approval is True
    assert result.causes == ()


def test_claim_cause_refuses_an_empty_cause() -> None:
    from ranex.governed_execution.domain.verdict import ClaimCause

    with pytest.raises(ValueError, match="cause"):
        ClaimCause(claim_id="tests-executed", cause="", detail=None)
