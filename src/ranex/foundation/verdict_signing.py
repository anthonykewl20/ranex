"""Ed25519 signatures over the closed verdict publication record."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.signing import _decode, _encode

# v2 adds `journal_head` (ADR-057). The domain string is inside the signed
# bytes, so the two versions are cryptographically distinct: a v2 signature
# cannot be replayed as v1 or the reverse.
#
# Old records stay VERIFIABLE, and that is deliberate rather than lenient.
# ADR-011's evidence v2 -> v3 bump could refuse old records outright because
# evidence is produced fresh every run and never re-read. Verdicts are not:
# `tools/dogfood/verify_repository_pilot.py` re-verifies ARCHIVED verdicts to
# prove old audits still hold, and those receipts are signed history that
# cannot honestly be re-signed. A bump that makes retained evidence
# unverifiable does not harden the system, it destroys its own audit trail.
#
# What v1 may no longer do is *gate* anything. It carries no anchor, so
# `journal verify --against-verdict` and check publication both refuse it as
# UNANCHORED. Reading is permitted; deciding is not — so a downgrade buys an
# attacker nothing.
VERDICT_DOMAIN_V1 = b"ranex-verdict-v1\n"
PAYLOAD_TYPE_V1 = "application/vnd.ranex.verdict.v1+json"

VERDICT_DOMAIN = b"ranex-verdict-v2\n"
PAYLOAD_TYPE = "application/vnd.ranex.verdict.v2+json"
SIGNED_FIELDS_V1 = (
    "verdict", "gate_id", "subject_digest", "subject_lane", "catalog_digest",
    "approver_id", "failing_rule", "missing_claims", "considered", "causes",
    "rejections", "self_approval", "reason",
)
SIGNED_FIELDS = (
    *SIGNED_FIELDS_V1,
    # The journal chain head this evaluation's own record produced, retained
    # OUTSIDE the journal and signed by the verdict signer — a different key
    # from the one that writes the journal. `Journal.verify()` alone accepts a
    # complete self-consistent rewrite (it says so itself); an anchor the
    # rewriter does not hold is what closes that. `null` when no journal was
    # configured: present and explicit, so an unanchored verdict is legible as
    # unanchored rather than indistinguishable from an anchored one.
    "journal_head",
)


#: Every readable verdict version: payload type -> (domain, signed fields).
#: New records are only ever written at PAYLOAD_TYPE.
VERSIONS = {
    PAYLOAD_TYPE: (VERDICT_DOMAIN, SIGNED_FIELDS),
    PAYLOAD_TYPE_V1: (VERDICT_DOMAIN_V1, SIGNED_FIELDS_V1),
}


def signed_fields_for(payload_type: object) -> tuple[str, ...]:
    """The exact field set a record of this version must carry, or raise."""

    if not isinstance(payload_type, str) or payload_type not in VERSIONS:
        raise ValueError(f"unsupported verdict payload type: {payload_type!r}")
    return VERSIONS[payload_type][1]


def signed_payload(
    record: Mapping[str, Any], *, payload_type: str = PAYLOAD_TYPE
) -> bytes:
    domain, fields = VERSIONS[payload_type] if payload_type in VERSIONS else (None, None)
    if domain is None or fields is None:
        raise ValueError(f"unsupported verdict payload type: {payload_type!r}")
    if set(record) != set(fields):
        raise ValueError(f"verdict record must contain exactly {list(fields)}")
    return domain + canonical_json_bytes(dict(record))


def sign_verdict(
    record: Mapping[str, Any], private_key: str, *, payload_type: str = PAYLOAD_TYPE
) -> str:
    """Sign a verdict record. Production never passes `payload_type`.

    The parameter exists so a reader's handling of an older version can be
    exercised against a record built the way that version really was, rather
    than against a hand-forged approximation. Writing an old version is not a
    downgrade risk on its own: nothing accepts an unanchored record for gating.
    """

    key = Ed25519PrivateKey.from_private_bytes(_decode(private_key, expected=32, field="private key"))
    return _encode(key.sign(signed_payload(record, payload_type=payload_type)))


def verify_verdict(record: Mapping[str, Any], signature: object, public_key: object, *, payload_type: object) -> bool:
    if not isinstance(payload_type, str) or payload_type not in VERSIONS:
        return False
    try:
        sig = _decode(signature, expected=64, field="signature")
        public = _decode(public_key, expected=32, field="public key")
        # The domain is selected by the declared version and is inside the
        # signed bytes, so claiming the wrong version simply fails to verify.
        payload = signed_payload(record, payload_type=payload_type)
        Ed25519PublicKey.from_public_bytes(public).verify(sig, payload)
    except (TypeError, ValueError, InvalidSignature):
        return False
    return True
