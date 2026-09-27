"""DSSE envelopes — Pre-Authentication Encoding and Ed25519 signatures.

Owned by Ranex under the §15.3 copy-improve-own rule. Shape follows the
secure-systems-lab DSSE signing-spec (vendored under ADR-067): payload and
payloadType are base64-encoded in the envelope JSON; the signature covers the
PAE bytes, not the envelope JSON itself. Pure Ed25519 — the form Rekor's
``dsse`` entry type verifies (``hashedrekord`` only accepts Ed25519ph).
"""

from __future__ import annotations

import base64
import binascii
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ranex.foundation.signing import _decode

PAYLOAD_TYPE_VERDICT_V2 = "application/vnd.ranex.verdict.v2+json"


def pae(payload_type: str, payload: bytes) -> bytes:
    """DSSE Pre-Authentication Encoding (DSSEv1)."""

    encoded_type = payload_type.encode("utf-8")
    return b"DSSEv1 %d %b %d %b" % (
        len(encoded_type),
        encoded_type,
        len(payload),
        payload,
    )


def _b64encode(data: bytes) -> str:
    return base64.standard_b64encode(data).decode("ascii")


def _b64decode(text: str) -> bytes:
    try:
        return base64.b64decode(text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("malformed base64 in DSSE envelope") from exc


def sign_envelope(
    *,
    payload_type: str,
    payload: bytes,
    private_key: str,
) -> dict[str, Any]:
    """Build a DSSE envelope signed with pure Ed25519 over the PAE bytes."""

    key = Ed25519PrivateKey.from_private_bytes(
        _decode(private_key, expected=32, field="private key")
    )
    signature = key.sign(pae(payload_type, payload))
    return {
        "payload": _b64encode(payload),
        "payloadType": payload_type,
        "signatures": [{"sig": _b64encode(signature)}],
    }


def verify_envelope(
    envelope: dict[str, Any],
    *,
    public_key: str,
    expected_payload_type: str | None = None,
) -> bytes | None:
    """Return the payload bytes if the envelope verifies, else None."""

    if not isinstance(envelope, dict):
        return None
    payload_b64 = envelope.get("payload")
    payload_type = envelope.get("payloadType")
    signatures = envelope.get("signatures")
    if (
        not isinstance(payload_b64, str)
        or not isinstance(payload_type, str)
        or not isinstance(signatures, list)
        or not signatures
    ):
        return None
    if expected_payload_type is not None and payload_type != expected_payload_type:
        return None
    try:
        payload = _b64decode(payload_b64)
        public = Ed25519PublicKey.from_public_bytes(
            _decode(public_key, expected=32, field="public key")
        )
        for item in signatures:
            if not isinstance(item, dict) or not isinstance(item.get("sig"), str):
                continue
            sig = _b64decode(item["sig"])
            try:
                public.verify(sig, pae(payload_type, payload))
            except (InvalidSignature, ValueError):
                continue
            return payload
    except (TypeError, ValueError):
        return None
    return None
