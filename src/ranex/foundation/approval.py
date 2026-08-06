"""Ed25519 signatures over merge approval envelopes.

The signed payload is the dedicated approval domain followed by canonical JSON
over exactly ``SIGNED_FIELDS``.  Verification returns ``False`` for malformed
envelopes so a merge caller can refuse them; payload construction and signing
raise ``ValueError`` so an approver cannot silently create one.

``candidate_row_hash(record)`` is ``"sha256:" + canonical_sha256(record)``:
the SHA-256 digest of the exact CANDIDATE row's canonical JSON.  It is therefore
computable from the journal record alone and reproducible by signer and verifier.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.foundation.signing import _decode, _encode

APPROVAL_DOMAIN = b"ranex-approval-v1\n"

SIGNED_FIELDS: tuple[str, ...] = (
    "candidate",
    "subject",
    "target_ref",
    "tip",
    "catalog_digest",
    "candidate_row_hash",
    "approver_id",
)

_OID = re.compile(r"[0-9a-f]{40}").fullmatch
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}").fullmatch


def candidate_row_hash(record: Mapping[str, Any]) -> str:
    """Return the stable digest of an exact CANDIDATE journal row record."""

    return "sha256:" + canonical_sha256(dict(record))


def signed_payload(envelope: Mapping[str, Any]) -> bytes:
    """Return the exact approval bytes, refusing malformed or open envelopes."""

    present = set(envelope)
    expected = set(SIGNED_FIELDS)
    if present != expected:
        unexpected = sorted(present - expected)
        missing = sorted(expected - present)
        detail = []
        if unexpected:
            detail.append(f"unexpected {', '.join(unexpected)}")
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        raise ValueError(
            f"approval envelope must be exactly {list(SIGNED_FIELDS)}: "
            + "; ".join(detail)
        )

    for field in SIGNED_FIELDS:
        if not isinstance(envelope[field], str):
            raise ValueError(f"approval {field} must be a string")
    if _OID(envelope["candidate"]) is None:
        raise ValueError("approval candidate must be a lowercase 40-hex OID")
    if _OID(envelope["tip"]) is None:
        raise ValueError("approval tip must be a lowercase 40-hex OID")
    for field in ("subject", "catalog_digest", "candidate_row_hash"):
        if _DIGEST(envelope[field]) is None:
            raise ValueError(f"approval {field} must be a lowercase sha256 digest")
    if not envelope["target_ref"].startswith("refs/"):
        raise ValueError("approval target_ref must start with refs/")
    if not envelope["approver_id"]:
        raise ValueError("approval approver_id must not be empty")

    return APPROVAL_DOMAIN + canonical_json_bytes(dict(envelope))


def sign_approval(envelope: Mapping[str, Any], private_key: str) -> str:
    """Sign the closed approval envelope. Deterministic per RFC 8032."""

    raw = _decode(private_key, expected=32, field="private key")
    key = Ed25519PrivateKey.from_private_bytes(raw)
    return _encode(key.sign(signed_payload(envelope)))


def verify_approval(
    envelope: Mapping[str, Any],
    signature: object,
    public_key: object,
) -> bool:
    """Return whether this exact, well-formed approval has this signature."""

    try:
        raw_signature = _decode(signature, expected=64, field="signature")
        raw_public = _decode(public_key, expected=32, field="public key")
        payload = signed_payload(envelope)
    except (TypeError, ValueError):
        return False

    try:
        Ed25519PublicKey.from_public_bytes(raw_public).verify(raw_signature, payload)
    except (InvalidSignature, ValueError):
        return False
    return True
