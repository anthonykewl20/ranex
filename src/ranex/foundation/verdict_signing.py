"""Ed25519 signatures over the closed verdict publication record."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.signing import _decode, _encode

VERDICT_DOMAIN = b"ranex-verdict-v1\n"
PAYLOAD_TYPE = "application/vnd.ranex.verdict.v1+json"
SIGNED_FIELDS = (
    "verdict", "gate_id", "subject_digest", "subject_lane", "catalog_digest",
    "approver_id", "failing_rule", "missing_claims", "considered", "causes",
    "rejections", "self_approval", "reason",
)


def signed_payload(record: Mapping[str, Any]) -> bytes:
    if set(record) != set(SIGNED_FIELDS):
        raise ValueError(f"verdict record must contain exactly {list(SIGNED_FIELDS)}")
    return VERDICT_DOMAIN + canonical_json_bytes(dict(record))


def sign_verdict(record: Mapping[str, Any], private_key: str) -> str:
    key = Ed25519PrivateKey.from_private_bytes(_decode(private_key, expected=32, field="private key"))
    return _encode(key.sign(signed_payload(record)))


def verify_verdict(record: Mapping[str, Any], signature: object, public_key: object, *, payload_type: object) -> bool:
    if payload_type != PAYLOAD_TYPE:
        return False
    try:
        sig = _decode(signature, expected=64, field="signature")
        public = _decode(public_key, expected=32, field="public key")
        payload = signed_payload(record)
        Ed25519PublicKey.from_public_bytes(public).verify(sig, payload)
    except (TypeError, ValueError, InvalidSignature):
        return False
    return True
