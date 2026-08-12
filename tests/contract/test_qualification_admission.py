"""SLICE-019 — frozen host-qualification evidence and admission contract."""

from __future__ import annotations

import copy
from collections.abc import Mapping

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.foundation import approval, signing
from ranex.foundation.canonical import canonical_json_bytes
from ranex.governed_execution.domain.verdict import Verdict

SUBJECT = "sha256:" + "a" * 64
QUALIFY_ARGV = (
    "python",
    "-m",
    "ranex.cli.host_confinement",
    "qualify",
    "--profile",
    "governance/confinement/strict-local-host-v1.json",
    "--artifact",
    ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
    "--manifest",
    "governance/confinement/native-launcher-build-v1.json",
    "--report",
    ".local/ranex/qualification/strict-local-v1.json",
)

HOST_STATE = {
    "lsm": {
        "securityfs_lsm": "landlock,lockdown,yama,apparmor,bpf",
        "apparmor_policy_identity": "sha256:" + "1" * 64,
        "selinux_policy_identity": None,
    },
    "unprivileged_userns_sysctls": {
        "kernel.unprivileged_userns_clone": 1,
        "user.max_user_namespaces": 15000,
    },
    "boot_id": "11111111-2222-3333-4444-555555555555",
    "machine_id": "0123456789abcdef0123456789abcdef",
    "delegation_identity": {
        "uid": 1000,
        "gid": 1000,
        "cgroup_root": "/sys/fs/cgroup",
        "cgroup_relative_path": "/user.slice/user-1000.slice/session.scope",
        "source": "direct",
        "userns_state_source": "qualification-host-probe",
    },
}

CONTENT = {
    "schema": "ranex-strict-local-qualification-v1",
    "qualified": True,
    "host_state": HOST_STATE,
    "profile_digest": "sha256:" + "2" * 64,
    "build_manifest_digest": "sha256:" + "3" * 64,
    "artifact_digest": "sha256:" + "4" * 64,
    "subject_digest": SUBJECT,
    "producer_id": "qualifier",
    "approver_id": "reviewer",
}


@pytest.fixture()
def qa():
    """Defer the new domain import so the rest of the suite still collects red."""

    from ranex.foundation import qualification
    from ranex.governed_execution.domain import admission

    class Bundle:
        qualification = qualification
        RejectionReason = admission.RejectionReason
        admit = staticmethod(admission.admit_qualification_reports)

    return Bundle


@pytest.fixture()
def identities() -> dict[str, tuple[str, str]]:
    return {
        "qualifier": signing.generate_keypair(),
        "reviewer": signing.generate_keypair(),
    }


def envelope(qa, identities, content: Mapping[str, object] = CONTENT) -> dict[str, object]:
    producer_private, _ = identities[str(content["producer_id"])]
    approver_private, _ = identities[str(content["approver_id"])]
    return {
        **content,
        "producer_signature": qa.qualification.sign_qualification(content, producer_private),
        "approver_signature": qa.qualification.sign_qualification(content, approver_private),
    }


def unchecked_envelope(qa, identities, content: Mapping[str, object]) -> dict[str, object]:
    """Sign reader-adversarial bytes without asking the producer-side validator."""

    def sign(identity: str) -> str:
        private, _ = identities[identity]
        raw = signing._decode(private, expected=32, field="private key")
        payload = qa.qualification.QUALIFICATION_DOMAIN + canonical_json_bytes(dict(content))
        return signing._encode(Ed25519PrivateKey.from_private_bytes(raw).sign(payload))

    return {
        **content,
        "producer_signature": sign(str(content["producer_id"])),
        "approver_signature": sign(str(content["approver_id"])),
    }


def admit(qa, identities, reports, *, live_host_state=HOST_STATE):
    return qa.admit(
        reports,
        {identity: pair[1] for identity, pair in identities.items()},
        subject_digest=SUBJECT,
        live_host_state=live_host_state,
        claim_id="host-qualification",
        command=QUALIFY_ARGV,
    )


def test_absent_report_leaves_host_qualification_missing_and_blocks() -> None:
    # Use the repository trust root, not a test-only gate which could conceal a
    # missing production wiring change.
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    evaluator = build_gate_evaluator(
        (root / "governance/gates.yaml").read_bytes(),
        suite_manifest=(root / "governance/suite_manifest.json").read_bytes(),
    )
    result = evaluator.evaluate("landing", (), subject_digest=SUBJECT, approver_id="reviewer")

    assert result.verdict is Verdict.FAIL
    assert "host-qualification" in result.missing_claims


@pytest.mark.parametrize(
    "malformed",
    (
        {**CONTENT, "schema": "ranex-strict-local-qualification-v2"},
        {
            **CONTENT,
            "host_state": {key: value for key, value in HOST_STATE.items() if key != "boot_id"},
        },
    ),
    ids=("unknown-schema", "missing-required-host-fact"),
)
def test_unknown_schema_or_missing_host_fact_refuses(
    qa, identities, malformed: dict[str, object]
) -> None:
    result = admit(qa, identities, [unchecked_envelope(qa, identities, malformed)])

    assert result.evidence == ()
    assert len(result.rejections) == 1


def test_disagreeing_reports_refuse_as_ambiguity_not_newest_wins(qa, identities) -> None:
    changed_state = copy.deepcopy(HOST_STATE)
    changed_state["boot_id"] = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    changed = {**CONTENT, "host_state": changed_state}

    result = admit(
        qa,
        identities,
        [envelope(qa, identities), envelope(qa, identities, changed)],
    )

    assert result.evidence == ()
    assert len(result.rejections) == 2
    assert all("ambigu" in rejection.detail.lower() for rejection in result.rejections)


@pytest.mark.parametrize(
    "field",
    ("boot_id", "machine_id", "lsm", "unprivileged_userns_sysctls"),
)
def test_genuine_report_refuses_when_a_live_anchor_differs(qa, identities, field: str) -> None:
    live = copy.deepcopy(HOST_STATE)
    if field == "lsm":
        live[field]["securityfs_lsm"] = "selinux"
    elif field == "unprivileged_userns_sysctls":
        live[field]["user.max_user_namespaces"] = 0
    else:
        live[field] = "live-host-has-different-bytes"
    genuine = envelope(qa, identities)

    result = admit(qa, identities, [genuine], live_host_state=live)

    assert result.evidence == ()
    assert result.rejections[0].reason is qa.RejectionReason.STALE_HOST_STATE
    assert field in result.rejections[0].detail


def test_producer_cannot_approve_its_own_qualification(qa, identities) -> None:
    self_approved = {**CONTENT, "approver_id": "qualifier"}
    result = admit(qa, identities, [envelope(qa, identities, self_approved)])

    assert result.evidence == ()
    assert len(result.rejections) == 1
    assert "self" in result.rejections[0].detail.lower()


def test_domain_and_exact_signed_fields_are_pinned(qa) -> None:
    assert qa.qualification.QUALIFICATION_DOMAIN == b"ranex-qualification-v1\n"
    assert qa.qualification.SIGNED_FIELDS == (
        "schema",
        "qualified",
        "host_state",
        "profile_digest",
        "build_manifest_digest",
        "artifact_digest",
        "subject_digest",
        "producer_id",
        "approver_id",
    )
    assert set(CONTENT["host_state"]) == {
        "lsm",
        "unprivileged_userns_sysctls",
        "boot_id",
        "machine_id",
        "delegation_identity",
    }
    assert qa.qualification.signed_payload(CONTENT) == (
        qa.qualification.QUALIFICATION_DOMAIN + canonical_json_bytes(CONTENT)
    )


@pytest.mark.parametrize("operation", ("add", "remove"))
def test_adding_or_removing_a_signed_field_refuses(qa, identities, operation: str) -> None:
    private, public = identities["qualifier"]
    signature = qa.qualification.sign_qualification(CONTENT, private)
    malformed = dict(CONTENT)
    if operation == "add":
        malformed["timestamp"] = "2026-08-12T00:00:00Z"
    else:
        del malformed["artifact_digest"]

    with pytest.raises(ValueError):
        qa.qualification.sign_qualification(malformed, private)
    assert qa.qualification.verify_qualification(malformed, signature, public) is False


def test_qualification_signature_cannot_cross_signing_domains(qa, identities) -> None:
    private, public = identities["qualifier"]
    signature = qa.qualification.sign_qualification(CONTENT, private)
    evidence_content = {
        "claim_id": "host-qualification",
        "command": " ".join(QUALIFY_ARGV),
        "command_digest": "sha256:" + "5" * 64,
        "executable_path": "/usr/bin/python",
        "exit_code": 0,
        "producer_id": "qualifier",
        "subject_digest": SUBJECT,
        "suite_results": None,
    }
    approval_content = {
        "candidate": "a" * 40,
        "subject": SUBJECT,
        "target_ref": "refs/heads/main",
        "tip": "b" * 40,
        "catalog_digest": "sha256:" + "c" * 64,
        "candidate_row_hash": "sha256:" + "d" * 64,
        "approver_id": "reviewer",
    }

    assert signing.verify_evidence(evidence_content, signature, public) is False
    assert approval.verify_approval(approval_content, signature, public) is False
