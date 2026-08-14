"""Ed25519 signatures over evidence records.

The verifier holds only public keys and therefore cannot forge. That is the one
property this module exists to provide, and it is why HMAC was refused: a shared
secret makes every verifier a forger, which contradicts the separation of
producer from approver.

Nothing here reaches a network or a model. Signing is a pure function of the
record and the key.

Four details are pinned rather than left to the caller, because `run` and the
loader must compute identical bytes on different machines:

1. **The domain prefix is inside the signed bytes.** Without it, a signature
   over these bytes stays valid if the same key is ever reused to sign some
   other structure whose canonical form happens to collide. It also carries the
   format version: SLICE-003 moved it to `v2`, which is what makes a v1
   signature fail against v2 content instead of being accepted as a downgrade.
2. **The signed field set is exactly seven**, not "every key except signature".
   The two differ the moment a record carries an extra field, and then the
   producer and the verifier disagree about what was covered.
3. **Encoding is base64 throughout.** A record written on one machine must
   verify on another; that is the whole point of the slice.
4. **That base64 must be the canonical spelling.** Callers key identities by the
   *string* — see `_decode` for why the two must be the same question.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from ranex.foundation.canonical import canonical_json_bytes

EVIDENCE_DOMAIN = b"ranex-evidence-v4\n"

# SLICE-009 added suite_results, and the version above moved with it.
# `command_digest` is what the kernel compares, so an unsigned digest would be a
# field the attacker chooses; `command` stays signed beside it so the legible
# field cannot be swapped under a matching digest; `executable_path` is signed
# because the containment rule is re-checked from it at evaluation, which an
# unsigned field could not carry.
SIGNED_FIELDS: tuple[str, ...] = (
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
)

_PREFIX = "ed25519:"


def _encode(raw: bytes) -> str:
    return _PREFIX + base64.b64encode(raw).decode("ascii")


def _decode(value: object, *, expected: int | None, field: str) -> bytes:
    """Decode `ed25519:<base64>`. Raises ValueError on anything else."""

    if not isinstance(value, str) or not value.startswith(_PREFIX):
        raise ValueError(f"{field} must be an {_PREFIX}<base64> string")
    encoded = value[len(_PREFIX) :]
    if not encoded:
        raise ValueError(f"{field} carries no key material")
    try:
        # validate=True so "!!!" is rejected rather than silently skipped.
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{field} is not valid base64: {exc}") from exc
    # validate=True checks the alphabet and nothing else. Neither 32 nor 64 bytes
    # divide into 3-byte base64 groups, so the final character carries bits no
    # decoder reads: a public key has four spellings and a signature sixteen, all
    # decoding to identical material. Every caller here keys an identity by the
    # *string* — the keyring's one-key-one-producer rule, `run`'s "is this the key
    # the keyring trusts for me" check — so two spellings of one key would be two
    # identities, and the alias attack that rule exists to make unrepresentable is
    # back for the price of one character. Re-encoding is what makes key identity
    # and string identity the same question, and it closes every call site at once.
    if base64.b64encode(raw).decode("ascii") != encoded:
        raise ValueError(
            f"{field} is not canonically encoded; the same bytes have another "
            "base64 spelling, and only the canonical one names this key"
        )
    if expected is not None and len(raw) != expected:
        raise ValueError(
            f"{field} is {len(raw)} bytes, expected {expected} for Ed25519"
        )
    return raw


def signed_payload(content: Mapping[str, Any]) -> bytes:
    """The exact bytes a signature covers.

    Refuses a record that is not exactly the eight content fields. Silently
    signing an extra field would let the producer cover something the verifier
    does not check; silently dropping it would let an attacker append a field
    the signature never protected.
    """

    present = set(content)
    expected = set(SIGNED_FIELDS)
    if present != expected:
        unexpected = sorted(present - expected)
        missing = sorted(expected - present)
        detail = []
        if unexpected:
            detail.append(f"unexpected {', '.join(unexpected)}")
        if missing:
            detail.append(f"missing {', '.join(missing)}")
        raise ValueError(f"evidence content must be exactly {list(SIGNED_FIELDS)}: "
                         + "; ".join(detail))

    # canonical_json_bytes sorts keys, so field order on disk cannot change the
    # signature.
    return EVIDENCE_DOMAIN + canonical_json_bytes(dict(content))


def generate_keypair() -> tuple[str, str]:
    """Return (private, public), both `ed25519:<base64>`."""

    private = Ed25519PrivateKey.generate()
    return public_private_pair(private)


def public_private_pair(private: Ed25519PrivateKey) -> tuple[str, str]:
    raw_private = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    raw_public = private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return _encode(raw_private), _encode(raw_public)


def public_key_for(private_key: str) -> str:
    """Derive the public key. `run` uses this to refuse, before executing, when
    its key is not the one the keyring trusts for the producer it claims."""

    raw = _decode(private_key, expected=32, field="private key")
    _, public = public_private_pair(Ed25519PrivateKey.from_private_bytes(raw))
    return public


def sign_evidence(content: Mapping[str, Any], private_key: str) -> str:
    """Sign the eight content fields. Deterministic per RFC 8032."""

    raw = _decode(private_key, expected=32, field="private key")
    key = Ed25519PrivateKey.from_private_bytes(raw)
    return _encode(key.sign(signed_payload(content)))


def verify_evidence(
    content: Mapping[str, Any],
    signature: object,
    public_key: object,
) -> bool:
    """True only if this exact content was signed by this exact key.

    Returns False rather than raising for every malformed input. A hand-mangled
    record must be rejected as evidence, not crash the operator's CLI — and a
    crash on the verify path would be a denial of service reachable by editing a
    file.
    """

    try:
        raw_signature = _decode(signature, expected=64, field="signature")
        raw_public = _decode(public_key, expected=32, field="public key")
        payload = signed_payload(content)
    except ValueError:
        return False

    try:
        Ed25519PublicKey.from_public_bytes(raw_public).verify(raw_signature, payload)
    except (InvalidSignature, ValueError):
        return False
    return True


def is_public_key(value: object) -> bool:
    """Whether `value` is a well-formed Ed25519 public key, for the keyring."""

    try:
        raw = _decode(value, expected=32, field="public key")
        Ed25519PublicKey.from_public_bytes(raw)
    except ValueError:
        return False
    return True


def is_signature(value: object) -> bool:
    """Whether `value` is a well-formed signature, independent of whether it
    verifies.

    Admission needs the difference. "This is not a signature at all" and "this
    is a signature over different bytes" are different accusations, and
    collapsing them would tell an operator investigating a forgery less than the
    data supports.
    """

    try:
        _decode(value, expected=64, field="signature")
    except ValueError:
        return False
    return True
