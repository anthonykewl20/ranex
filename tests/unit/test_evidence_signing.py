"""SLICE-002 — the signing primitives.

The target for this slice. Written before the implementation and required to
fail first: a test that passes before the code exists is not a target, it is a
circle painted around wherever the dart landed.

SLICE-003 added the claim to command binding: `command_digest` and
`executable_path` are the sixth and seventh signed fields, and the domain moved
to v2 so a v1 signature cannot be replayed against v2 content. The refusal of v1
at admission is tested in tests/security/test_slice003_command_binding.py.

API pinned by these tests, in `ranex.foundation.signing`:

    EVIDENCE_DOMAIN: bytes                  # b"ranex-evidence-v4\\n"
    SIGNED_FIELDS: tuple[str, ...]          # exactly the ten content fields
    generate_keypair() -> tuple[str, str]   # (private, public), "ed25519:<b64>"
    public_key_for(private_key) -> str
    signed_payload(content) -> bytes        # domain prefix + canonical bytes
    sign_evidence(content, private_key) -> str
    verify_evidence(content, signature, public_key) -> bool

Encoding is pinned rather than left open because a record written on one machine
must verify on another. That is the only thing this slice actually buys.
"""

from __future__ import annotations

import pytest

from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256


@pytest.fixture()
def sg():
    """Imported inside a fixture, not at module scope.

    `ranex.foundation.signing` does not exist until this slice is built. A
    module-level import would be a COLLECTION error, which aborts the entire
    run and hides the 78 tests that already pass — leaving the implementer
    unable to see regressions while working. Deferring it makes each test fail
    loudly on its own instead.
    """

    from ranex.foundation import signing

    return signing


ARGV = ["uv", "run", "pytest", "-q"]
SUBJECT = "sha256:" + "a" * 64

CONTENT = {
    "claim_id": "tests-executed",
    "command": "uv run pytest -q",
    "command_digest": "sha256:" + canonical_sha256(ARGV),
    "executable_path": "/usr/bin/uv",
    "exit_code": 0,
    "producer_id": "worker",
    "subject_digest": "sha256:" + "a" * 64,
    "suite_results": None,
    "confinement_result_digest": "sha256:" + "c" * 64,
    "confinement_profile_digest": "sha256:" + "d" * 64,
}


@pytest.fixture()
def keypair(sg) -> tuple[str, str]:
    return sg.generate_keypair()


# --- the payload is pinned --------------------------------------------------


def test_signed_fields_are_exactly_the_eight_content_fields(sg) -> None:
    """Not "everything except signature". The two differ the moment a record
    carries an extra field, and then `run` and `load` disagree about what was
    signed.

    SLICE-003 made it seven. `command_digest` is what the kernel compares, so an
    unsigned digest would be a field the attacker chooses; `command` stays
    signed alongside it so the legible field cannot be swapped under a matching
    digest; and `executable_path` is signed because the containment rule is
    re-checked from it at evaluation, which an unsigned field could not carry.
    """

    assert (sg.EVIDENCE_DOMAIN, set(sg.SIGNED_FIELDS)) == (
        b"ranex-evidence-v4\n",
        {
            "claim_id",
            "command",
            "command_digest",
            "executable_path",
            "exit_code",
            "producer_id",
            "subject_digest",
            "suite_results",
            "confinement_result_digest",
            "confinement_profile_digest",
        },
    )
    assert len(sg.SIGNED_FIELDS) == 10


def test_payload_carries_the_domain_prefix(sg) -> None:
    """Without domain separation a signature over these bytes stays valid if the
    same key is ever reused to sign a different structure.

    v1 → v2 with the field set: the prefix is what makes a v1 signature fail
    against v2 content instead of being silently accepted as a downgrade.
    """

    payload = sg.signed_payload(CONTENT)
    assert payload.startswith(sg.EVIDENCE_DOMAIN)
    assert payload == sg.EVIDENCE_DOMAIN + canonical_json_bytes(CONTENT)


def test_payload_ignores_key_order(sg) -> None:
    """Canonical JSON sorts keys, so record field order cannot change the
    signature."""

    shuffled = dict(reversed(list(CONTENT.items())))
    assert sg.signed_payload(shuffled) == sg.signed_payload(CONTENT)


def test_payload_refuses_an_unexpected_field(sg) -> None:
    """A record with an extra field must be refused, never silently signed over
    and never silently dropped."""

    with pytest.raises(ValueError):
        sg.signed_payload({**CONTENT, "timestamp": "2026-08-01"})


def test_payload_refuses_a_missing_field(sg) -> None:
    with pytest.raises(ValueError):
        sg.signed_payload({k: v for k, v in CONTENT.items() if k != "command"})


# --- signatures -------------------------------------------------------------


def test_signature_is_deterministic(sg, keypair: tuple[str, str]) -> None:
    """Ed25519 is deterministic per RFC 8032. A record must not change bytes
    between signings, or evidence differs run to run for no semantic reason."""

    private, _ = keypair
    assert sg.sign_evidence(CONTENT, private) == sg.sign_evidence(CONTENT, private)


def test_signature_encoding_is_pinned(sg, keypair: tuple[str, str]) -> None:
    """Base64, fixed, so a record crosses machines."""

    private, public = keypair
    signature = sg.sign_evidence(CONTENT, private)
    assert signature.startswith("ed25519:")
    assert public.startswith("ed25519:")
    assert private.startswith("ed25519:")


def test_signature_verifies_with_the_matching_public_key(
    sg,
    keypair: tuple[str, str],
) -> None:
    private, public = keypair
    assert sg.verify_evidence(CONTENT, sg.sign_evidence(CONTENT, private), public) is True


def test_public_key_is_derivable_from_the_private_key(
    sg,
    keypair: tuple[str, str],
) -> None:
    """`run` needs this to refuse before executing when its key does not match
    the keyring entry for the producer it claims to be."""

    private, public = keypair
    assert sg.public_key_for(private) == public


def test_a_different_key_does_not_verify(sg, keypair: tuple[str, str]) -> None:
    private, _ = keypair
    _, other_public = sg.generate_keypair()
    assert sg.verify_evidence(CONTENT, sg.sign_evidence(CONTENT, private), other_public) is False


@pytest.mark.parametrize("field", sorted(CONTENT))
def test_mutating_any_signed_field_invalidates_the_signature(
    sg,
    keypair: tuple[str, str],
    field: str,
) -> None:
    """This is the whole point. Every one of the seven, not just exit_code.

    `command`, `command_digest` and `executable_path` are all in the
    parametrisation, which is how criteria 6, 7 and the ADR-001 path-forgery
    case are held at the primitive level: none of the three can be moved without
    the signature noticing.
    """

    private, public = keypair
    signature = sg.sign_evidence(CONTENT, private)
    tampered = dict(CONTENT)
    tampered[field] = 1 if field == "exit_code" else str(CONTENT[field]) + "-tampered"
    assert sg.verify_evidence(tampered, signature, public) is False


def test_malformed_signature_is_false_not_an_exception(
    sg,
    keypair: tuple[str, str],
) -> None:
    """A hand-mangled record must be rejected as evidence, not crash the CLI."""

    _, public = keypair
    for bad in ("", "ed25519:", "ed25519:!!!not-base64!!!", "nonsense", "sha256:abc"):
        assert sg.verify_evidence(CONTENT, bad, public) is False


def test_signature_over_a_different_domain_does_not_verify(
    sg,
    keypair: tuple[str, str],
) -> None:
    """Proves the domain prefix is actually inside the signed bytes rather than
    decoration: a signature made over the bare canonical JSON must fail."""

    import base64

    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    private, public = keypair
    raw = base64.b64decode(private.removeprefix("ed25519:"))
    key = Ed25519PrivateKey.from_private_bytes(raw)
    undomained = "ed25519:" + base64.b64encode(
        key.sign(canonical_json_bytes(CONTENT))
    ).decode()
    assert sg.verify_evidence(CONTENT, undomained, public) is False


def test_verdict_signature_cannot_verify_as_evidence(sg, keypair) -> None:
    from ranex.foundation import verdict_signing

    private, public = keypair
    record = {
        field: None for field in verdict_signing.SIGNED_FIELDS
    }
    record.update(
        verdict="FAIL", gate_id="landing", subject_digest=SUBJECT,
        subject_lane="PRE_READINESS_PRODUCT_SLICE", catalog_digest=None,
        approver_id="owner", failing_rule="TESTS_EXECUTED", missing_claims=[],
        considered=[], causes=[], rejections=[], self_approval=False,
        reason="no evidence",
    )
    signature = verdict_signing.sign_verdict(record, private)
    assert sg.verify_evidence(CONTENT, signature, public) is False
