"""SLICE-081 — the rulebook a record was produced under is checked, not assumed.

Before the Evidence Envelope carried policy context, this attack needed no
forged signature, no stolen key and no changed subject:

    1. run the suite honestly and take the green, signed evidence
    2. edit `governance/gates.yaml` — drop a required claim, or point a claim's
       bound command at something weaker
    3. evaluate

The evidence still verified, still matched the subject, and satisfied a
rulebook the run had never seen. The subject binding — the property the
published attack demonstration exercises — does not help: nothing about the
code changed. Only the rules did.

These arms pin the refusal, and pin that it is reported as its own reason.
"policy-context-mismatch" is not "bad-signature": nothing is wrong with the
record, and telling an operator to hunt a forgery that did not happen wastes
the one thing a refusal is for.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import (
    CATALOG_ABSENT,
    ENVELOPE_TYPE,
    generate_keypair,
    sign_evidence,
)
from ranex.governed_execution.domain.admission import RejectionReason

ARGV = ["sh", "run-tests.sh"]
SUBJECT = "sha256:" + "a" * 64
EXECUTABLE = "/usr/bin/sh"

GATES = (
    "gates:\n"
    "  - gate_id: landing\n"
    "    rule_id: TESTS_EXECUTED\n"
    "    blocking: true\n"
    "    required_claims:\n"
    "      - claim_id: tests-executed\n"
    f"        command: {json.dumps(ARGV)}\n"
)

WEAKENED = GATES.replace('"run-tests.sh"', '"true"')


@pytest.fixture()
def keypair() -> tuple[str, str]:
    return generate_keypair()


def content(**overrides: object) -> dict[str, object]:
    record: dict[str, object] = {
        "claim_id": "tests-executed",
        "subject_digest": SUBJECT,
        "producer_id": "worker",
        "command": " ".join(ARGV),
        "command_digest": command_digest(ARGV),
        "executable_path": EXECUTABLE,
        "exit_code": 0,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
        "envelope_type": ENVELOPE_TYPE,
        "gate_id": "landing",
        "catalog_digest": catalog_digest_for(GATES.encode("utf-8")),
    }
    record.update(overrides)
    return record


def signed(private_key: str, **overrides: object) -> dict[str, object]:
    body = content(**overrides)
    return {**body, "signature": sign_evidence(body, private_key)}


def admit_with_policy(
    tmp_path: Path,
    records: list[dict[str, object]],
    public_key: str,
    *,
    gate_id: str = "landing",
    catalog: str = GATES,
):
    from ranex.cli.main import admit_records

    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps(records), encoding="utf-8")
    return admit_records(
        evidence,
        {"worker": public_key},
        None,
        gate_id=gate_id,
        catalog_digest=catalog_digest_for(catalog.encode("utf-8")),
    )


# --- the attack -------------------------------------------------------------


def test_evidence_is_admitted_under_the_catalog_it_was_produced_for(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """The honest path, so the refusals below mean something."""

    private, public = keypair

    admitted = admit_with_policy(tmp_path, [signed(private)], public)

    assert admitted.rejections == ()
    assert len(admitted.evidence) == 1


def test_editing_the_gate_catalog_invalidates_the_evidence(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """The attack, refused.

    Green signed evidence, an unchanged subject, and one edit to the catalog:
    the claim's bound command now points at `true`, which succeeds against any
    tree. Before SLICE-081 this passed.
    """

    private, public = keypair

    admitted = admit_with_policy(tmp_path, [signed(private)], public, catalog=WEAKENED)

    assert admitted.evidence == ()
    (rejection,) = admitted.rejections
    assert rejection.reason is RejectionReason.POLICY_CONTEXT_MISMATCH
    assert "the rulebook changed after the work was done" in rejection.detail


def test_the_refusal_is_not_reported_as_a_forgery(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """Nothing is wrong with the record: it verifies, and its producer is known.

    Reporting it as `bad-signature` would send an operator hunting an attack
    that did not happen; reporting it as absence would file work done under
    other rules as work never done. It is its own event and says so.
    """

    private, public = keypair

    admitted = admit_with_policy(tmp_path, [signed(private)], public, catalog=WEAKENED)
    (rejection,) = admitted.rejections

    assert rejection.reason is not RejectionReason.BAD_SIGNATURE
    assert rejection.reason is not RejectionReason.MALFORMED_RECORD
    assert str(rejection.reason) == "policy-context-mismatch"


def test_evidence_for_one_gate_does_not_satisfy_another(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """One catalog defines many gates, so the catalog digest alone is not enough."""

    private, public = keypair

    admitted = admit_with_policy(tmp_path, [signed(private)], public, gate_id="release")

    assert admitted.evidence == ()
    (rejection,) = admitted.rejections
    assert rejection.reason is RejectionReason.POLICY_CONTEXT_MISMATCH
    assert "'landing'" in rejection.detail and "'release'" in rejection.detail


def test_a_record_naming_no_catalog_satisfies_no_gate(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """`run` records `catalog-absent` when no catalog is committed.

    That is the honest answer and is why `run` does not refuse — but a record
    that names no rulebook could otherwise satisfy any of them, so absence
    blocks here, at the verdict, exactly as ADR-011 requires.
    """

    private, public = keypair

    admitted = admit_with_policy(
        tmp_path, [signed(private, catalog_digest=CATALOG_ABSENT)], public
    )

    assert admitted.evidence == ()
    (rejection,) = admitted.rejections
    assert rejection.reason is RejectionReason.POLICY_CONTEXT_MISMATCH
    assert "names no rulebook" in rejection.detail


# --- the refusal is precise -------------------------------------------------


def test_the_refusal_names_the_record_a_human_must_open(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """A rejection that cannot be located is a rumour.

    The second record is the foreign one; the refusal must say so rather than
    reporting a count, and must keep the honest record admitted.
    """

    private, public = keypair
    good = signed(private)
    foreign = signed(private, gate_id="release")

    admitted = admit_with_policy(tmp_path, [good, foreign], public)

    assert len(admitted.evidence) == 1
    (rejection,) = admitted.rejections
    assert rejection.index == 1
    assert rejection.producer_id == "worker"
    assert rejection.claim_id == "tests-executed"


def test_a_foreign_record_does_not_displace_the_diagnosis_of_the_others(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """Refusals from both passes coexist and stay in record order."""

    private, public = keypair
    foreign = signed(private, gate_id="release")
    forged = {**content(), "signature": "ed25519:" + "A" * 86 + "=="}

    admitted = admit_with_policy(tmp_path, [foreign, forged], public)

    assert admitted.evidence == ()
    assert [r.index for r in admitted.rejections] == [0, 1]
    assert admitted.rejections[0].reason is RejectionReason.POLICY_CONTEXT_MISMATCH
    assert admitted.rejections[1].reason is not RejectionReason.POLICY_CONTEXT_MISMATCH


def test_omitting_the_policy_context_verifies_signatures_only(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """The narrower question a non-gate caller asks.

    `admit_records` without a gate and catalog checks signatures the way
    omitting `repository_root` checks signatures without containment. A caller
    asking "did this record verify" is not asking which rulebook it served.
    """

    from ranex.cli.main import admit_records

    private, public = keypair
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps([signed(private, gate_id="release")]), encoding="utf-8")

    admitted = admit_records(evidence, {"worker": public}, None)

    assert admitted.rejections == ()
    assert len(admitted.evidence) == 1


# --- the envelope itself ----------------------------------------------------


def test_a_v4_record_cannot_be_spelled_as_v5(keypair: tuple[str, str]) -> None:
    """The downgrade, refused by the exact field set rather than by a version check.

    A record carrying the ten old fields is not v5 content, so `signed_payload`
    refuses to compute bytes for it at all — there is nothing to sign and
    nothing to verify against.
    """

    from ranex.foundation.signing import signed_payload

    v4 = {
        key: value
        for key, value in content().items()
        if key not in {"envelope_type", "gate_id", "catalog_digest"}
    }

    with pytest.raises(ValueError, match="must be exactly"):
        signed_payload(v4)


def test_a_v4_signature_does_not_verify_against_v5_bytes(
    keypair: tuple[str, str]
) -> None:
    """The domain prefix is inside the signed bytes, which is what makes the
    version bump a refusal rather than a convention."""

    import base64

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from ranex.foundation.canonical import canonical_json_bytes
    from ranex.foundation.signing import verify_evidence

    private, public = keypair
    body = content()
    raw = base64.b64decode(private.removeprefix("ed25519:"))
    v4_signature = "ed25519:" + base64.b64encode(
        Ed25519PrivateKey.from_private_bytes(raw).sign(
            b"ranex-evidence-v4\n" + canonical_json_bytes(body)
        )
    ).decode("ascii")

    assert verify_evidence(body, v4_signature, public) is False


def test_the_envelope_type_is_signed_and_cannot_be_relabelled(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """`envelope_type` is inside the signature, so it cannot be edited on disk
    to make a record claim to be something else."""

    private, public = keypair
    record = signed(private)
    record["envelope_type"] = "ranex-evidence-envelope-v2"

    admitted = admit_with_policy(tmp_path, [record], public)

    assert admitted.evidence == ()
    (rejection,) = admitted.rejections
    assert rejection.reason is RejectionReason.BAD_SIGNATURE


def test_the_policy_fields_are_signed_and_cannot_be_edited_on_disk(
    tmp_path: Path, keypair: tuple[str, str]
) -> None:
    """The whole point of putting them inside the signed set: an attacker who
    edits the evidence file to match the new catalog invalidates the record."""

    private, public = keypair
    record = signed(private)
    record["catalog_digest"] = catalog_digest_for(WEAKENED.encode("utf-8"))

    admitted = admit_with_policy(tmp_path, [record], public, catalog=WEAKENED)

    assert admitted.evidence == ()
    (rejection,) = admitted.rejections
    assert rejection.reason is RejectionReason.BAD_SIGNATURE
