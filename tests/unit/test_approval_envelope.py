from __future__ import annotations

import pytest

from ranex.foundation import approval, signing
from ranex.governed_execution.domain.task import TaskCandidate

ENVELOPE = {
    "candidate": "a" * 40,
    "subject": "sha256:" + "b" * 64,
    "target_ref": "refs/heads/main",
    "tip": "c" * 40,
    "catalog_digest": "sha256:" + "d" * 64,
    "candidate_row_hash": "sha256:" + "e" * 64,
    "approver_id": "reviewer-alice",
}

EVIDENCE = {
    "claim_id": "tests-executed",
    "command": "uv run --frozen pytest -q",
    "command_digest": "sha256:" + "1" * 64,
    "executable_path": "/usr/bin/uv",
    "exit_code": 0,
    "producer_id": "worker",
    "subject_digest": ENVELOPE["subject"],
    "suite_results": None,
    "confinement_result_digest": "sha256:" + "c" * 64,
    "confinement_profile_digest": "sha256:" + "d" * 64,
}


@pytest.fixture()
def keypair() -> tuple[str, str]:
    return signing.generate_keypair()


def test_valid_envelope_signs_and_verifies(
    keypair: tuple[str, str],
) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)

    assert approval.APPROVAL_DOMAIN == b"ranex-approval-v1\n"
    assert approval.APPROVAL_DOMAIN != signing.EVIDENCE_DOMAIN
    assert approval.verify_approval(ENVELOPE, signature, public) is True


def test_cross_domain_replay_is_refused(keypair: tuple[str, str]) -> None:
    private, public = keypair
    evidence_signature = signing.sign_evidence(EVIDENCE, private)
    approval_signature = approval.sign_approval(ENVELOPE, private)

    assert approval.verify_approval(ENVELOPE, evidence_signature, public) is False
    assert signing.verify_evidence(EVIDENCE, approval_signature, public) is False


def test_extra_field_is_refused(keypair: tuple[str, str]) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)
    malformed = {**ENVELOPE, "timestamp": "2026-08-06"}

    with pytest.raises(ValueError, match="unexpected timestamp"):
        approval.sign_approval(malformed, private)
    assert approval.verify_approval(malformed, signature, public) is False


def test_missing_field_is_refused(keypair: tuple[str, str]) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)
    malformed = {key: value for key, value in ENVELOPE.items() if key != "tip"}

    with pytest.raises(ValueError, match="missing tip"):
        approval.sign_approval(malformed, private)
    assert approval.verify_approval(malformed, signature, public) is False


def test_wrong_typed_field_is_refused(keypair: tuple[str, str]) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)
    malformed = {**ENVELOPE, "target_ref": 7}

    with pytest.raises(ValueError, match="target_ref must be a string"):
        approval.sign_approval(malformed, private)
    assert approval.verify_approval(malformed, signature, public) is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("candidate", "f" * 40),
        ("subject", "sha256:" + "f" * 64),
        ("target_ref", "refs/heads/release"),
        ("tip", "f" * 40),
        ("catalog_digest", "sha256:" + "f" * 64),
        ("candidate_row_hash", "sha256:" + "f" * 64),
    ),
)
def test_each_merge_binding_is_load_bearing(
    keypair: tuple[str, str],
    field: str,
    replacement: str,
) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)

    assert approval.verify_approval(
        {**ENVELOPE, field: replacement}, signature, public
    ) is False


def test_approver_id_is_load_bearing(keypair: tuple[str, str]) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)

    assert approval.verify_approval(
        {**ENVELOPE, "approver_id": "reviewer-bob"}, signature, public
    ) is False


@pytest.mark.parametrize(
    ("field", "replacement", "reason"),
    (
        ("candidate", "not-an-oid", "candidate must be a lowercase 40-hex OID"),
        ("candidate", "F" * 40, "candidate must be a lowercase 40-hex OID"),
        ("tip", "xyz", "tip must be a lowercase 40-hex OID"),
        ("subject", "sha256:short", "subject must be a lowercase sha256 digest"),
        (
            "catalog_digest",
            "sha256:" + "D" * 64,
            "catalog_digest must be a lowercase sha256 digest",
        ),
        (
            "candidate_row_hash",
            "md5:" + "e" * 64,
            "candidate_row_hash must be a lowercase sha256 digest",
        ),
        ("target_ref", "heads/main", "target_ref must start with refs/"),
        ("approver_id", "", "approver_id must not be empty"),
    ),
)
def test_malformed_shape_is_refused_before_any_signature(
    keypair: tuple[str, str],
    field: str,
    replacement: str,
    reason: str,
) -> None:
    private, public = keypair
    signature = approval.sign_approval(ENVELOPE, private)
    malformed = {**ENVELOPE, field: replacement}

    with pytest.raises(ValueError, match=reason):
        approval.sign_approval(malformed, private)
    assert approval.verify_approval(malformed, signature, public) is False


def test_candidate_row_hash_is_stable_and_binds_every_record_field() -> None:
    record = TaskCandidate(
        task_id="task-010",
        gate_id="landing",
        subject_digest=ENVELOPE["subject"],
        missing_claims=(),
    ).as_record()
    digest = approval.candidate_row_hash(record)

    assert digest == approval.candidate_row_hash(dict(reversed(list(record.items()))))
    for field in record:
        changed = dict(record)
        changed[field] = ["tests-executed"] if field == "missing_claims" else "changed"
        assert approval.candidate_row_hash(changed) != digest
