"""SLICE-002 — admission, and the forged-versus-absent distinction.

Written before the implementation and required to fail first.

API pinned by these tests, in `ranex.governed_execution.domain.admission`:

    class RejectionReason(StrEnum): ...
    class Rejection:  index, reason, detail, producer_id, claim_id
    class Admission:  evidence: tuple[Evidence, ...]
                      rejections: tuple[Rejection, ...]
    admit(records, keyring) -> Admission

`admit` takes a plain mapping of producer_id -> public key, never a file path or
a loader. The domain does not reach for adapters.

The load-bearing property: `evaluate()` sees only admitted records, so forgery
reaches the kernel as absence. That is safe only because admission reports the
rejection as structured data. If the distinction lived only in CLI prose, a
programmatic consumer would read forgery as missing work.
"""

from __future__ import annotations

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.domain.verdict import (
    Claim,
    Gate,
    Verdict,
    evaluate,
)

SUBJECT = "sha256:" + "a" * 64

# SLICE-003: the record names the argv that ran, and the claim names the argv
# that satisfies it. This file is about admission, which does not judge
# satisfaction, so the two agree everywhere below.
ARGV = ["uv", "run", "pytest", "-q"]
COMMAND_DIGEST = "sha256:" + canonical_sha256(ARGV)
EXECUTABLE = "/usr/bin/uv"


@pytest.fixture()
def adm():
    """Deferred import — see the note in test_evidence_signing.py. A
    module-level import of a module that does not exist yet aborts collection
    for the whole suite."""

    from ranex.foundation import signing
    from ranex.governed_execution.domain import admission

    class Bundle:
        Admission = admission.Admission
        Rejection = admission.Rejection
        RejectionReason = admission.RejectionReason
        admit = staticmethod(admission.admit)
        generate_keypair = staticmethod(signing.generate_keypair)
        sign_evidence = staticmethod(signing.sign_evidence)

    return Bundle


@pytest.fixture()
def worker(adm) -> tuple[str, str]:
    return adm.generate_keypair()


def content(**overrides: object) -> dict[str, object]:
    record = {
        "claim_id": "tests-executed",
        "command": " ".join(ARGV),
        "command_digest": COMMAND_DIGEST,
        "executable_path": EXECUTABLE,
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": SUBJECT,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    record.update(overrides)
    return record


def signed(adm, private_key: str, **overrides: object) -> dict[str, object]:
    body = content(**overrides)
    return {**body, "signature": adm.sign_evidence(body, private_key)}


# --- the happy path ---------------------------------------------------------


def test_a_validly_signed_record_is_admitted(adm, worker: tuple[str, str]) -> None:
    private, public = worker
    result = adm.admit([signed(adm, private)], {"worker": public})

    assert isinstance(result, adm.Admission)
    assert result.rejections == ()
    assert len(result.evidence) == 1
    assert result.evidence[0].claim_id == "tests-executed"
    assert result.evidence[0].producer_id == "worker"


def test_admitted_evidence_carries_no_signature_field(
    adm,
    worker: tuple[str, str],
) -> None:
    """`Evidence` must not gain a signature field. The loader verifies, discards
    the signature, and constructs Evidence from the content fields, so keys
    never reach `evaluate()`."""

    private, public = worker
    admitted = adm.admit([signed(adm, private)], {"worker": public}).evidence[0]
    assert not hasattr(admitted, "signature")


# --- every rejection path ---------------------------------------------------


def test_unsigned_record_is_rejected(adm, worker: tuple[str, str]) -> None:
    """Existing unsigned records stop counting. No migration, no
    grandfathering."""

    _, public = worker
    result = adm.admit([content()], {"worker": public})

    assert result.evidence == ()
    assert [r.reason for r in result.rejections] == [
        adm.RejectionReason.MISSING_SIGNATURE
    ]


def test_tampered_record_is_rejected(adm, worker: tuple[str, str]) -> None:
    private, public = worker
    record = signed(adm, private, exit_code=1)
    record["exit_code"] = 0  # the classic: flip a failure into a pass

    result = adm.admit([record], {"worker": public})
    assert result.evidence == ()
    assert result.rejections[0].reason is adm.RejectionReason.BAD_SIGNATURE


def test_malformed_signature_is_rejected(adm, worker: tuple[str, str]) -> None:
    _, public = worker
    result = adm.admit([{**content(), "signature": "not-a-signature"}], {"worker": public})

    assert result.evidence == ()
    assert result.rejections[0].reason is adm.RejectionReason.MALFORMED_SIGNATURE


def test_unknown_producer_is_rejected_never_trusted_by_default(
    adm,
    worker: tuple[str, str],
) -> None:
    private, _ = worker
    result = adm.admit([signed(adm, private)], {})

    assert result.evidence == ()
    assert result.rejections[0].reason is adm.RejectionReason.UNKNOWN_PRODUCER


def test_record_signed_by_one_producer_claiming_another_is_rejected(adm) -> None:
    """The alias attack. alice signs, but the record claims producer_id worker.
    Verification uses the key registered for the claimed id, so it fails.

    Without this, an approver could produce evidence under another name and walk
    straight past no-self-approval."""

    alice_private, alice_public = adm.generate_keypair()
    _, worker_public = adm.generate_keypair()

    record = signed(adm, alice_private, producer_id="worker")
    result = adm.admit([record], {"worker": worker_public, "alice": alice_public})

    assert result.evidence == ()
    assert result.rejections[0].reason is adm.RejectionReason.BAD_SIGNATURE


def test_unexpected_field_is_rejected(adm, worker: tuple[str, str]) -> None:
    private, public = worker
    record = signed(adm, private)
    record["timestamp"] = "2026-08-01"

    result = adm.admit([record], {"worker": public})
    assert result.evidence == ()
    assert result.rejections[0].reason is adm.RejectionReason.MALFORMED_RECORD


def test_missing_field_is_rejected(adm, worker: tuple[str, str]) -> None:
    private, public = worker
    record = signed(adm, private)
    del record["command"]

    result = adm.admit([record], {"worker": public})
    assert result.evidence == ()
    assert result.rejections[0].reason is adm.RejectionReason.MALFORMED_RECORD


# --- rejections are structured, and distinguishable -------------------------


def test_rejection_identifies_the_record(adm, worker: tuple[str, str]) -> None:
    """A rejection a human cannot locate is only marginally better than
    silence."""

    private, public = worker
    good = signed(adm, private)
    bad = content(claim_id="contracts-validated")

    result = adm.admit([good, bad], {"worker": public})
    assert len(result.evidence) == 1
    assert len(result.rejections) == 1

    rejection = result.rejections[0]
    assert isinstance(rejection, adm.Rejection)
    assert rejection.index == 1
    assert rejection.claim_id == "contracts-validated"
    assert rejection.producer_id == "worker"
    assert rejection.detail


def test_every_rejection_reason_is_distinct(adm) -> None:
    """Forged, unknown-producer and malformed must not collapse into one
    another, and none of them may read as absence."""

    values = [str(reason) for reason in adm.RejectionReason]
    assert len(values) == len(set(values))
    assert "no evidence for required claim" not in values


def test_rejection_reason_set_has_all_seven_closed_values(adm) -> None:
    assert {str(reason) for reason in adm.RejectionReason} == {
        "malformed-record", "missing-signature", "malformed-signature",
        "unknown-producer", "bad-signature", "stale-host-state",
        "executable-inside-subject",
    }


def test_admission_preserves_good_records_alongside_bad(
    adm,
    worker: tuple[str, str],
) -> None:
    private, public = worker
    result = adm.admit(
        [content(), signed(adm, private), {**content(), "signature": "bogus"}],
        {"worker": public},
    )
    assert len(result.evidence) == 1
    assert len(result.rejections) == 2


# --- the reduction to absence, end to end -----------------------------------


def test_forgery_reaches_the_kernel_as_absence(adm, worker: tuple[str, str]) -> None:
    """The reduction this design rests on: a forged record is not admitted, so
    the required claim has no satisfying evidence, so absence blocks."""

    _, public = worker
    forged = content()  # unsigned: what a text editor produces

    result = adm.admit([forged], {"worker": public})
    gate = Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(
            Claim(claim_id="tests-executed", command_digest=COMMAND_DIGEST),
        ),
        blocking=True,
    )
    evaluation = evaluate(
        gate,
        result.evidence,
        subject_digest=SUBJECT,
        approver_id="reviewer_alice",
    )

    assert evaluation.verdict is Verdict.FAIL
    assert result.rejections  # and the reason survives, outside the verdict
