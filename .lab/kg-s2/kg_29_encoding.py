"""Base32/16 codec pair with checksum."""
from __future__ import annotations

import base64
import binascii
import hashlib

ALPHABET = "0123456789abcdef"


def checksum(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()[:8]


def encode(payload: bytes) -> str:
    body = base64.b32encode(payload).decode("ascii").rstrip("=")
    return f"{body}-{checksum(payload)}"


def decode(text: str) -> bytes:
    body, _, suffix = text.rpartition("-")
    if not body:
        raise ValueError("missing payload")
    padded = body + "=" * (-len(body) % 8)
    try:
        payload = base64.b32decode(padded, casefold=True)
    except binascii.Error as error:
        raise ValueError(f"corrupt payload: {error}") from error
    if checksum(payload) != suffix:
        raise ValueError("checksum mismatch")
    return payload


def is_hex(text: str) -> bool:
    return all(char in ALPHABET for char in text.lower())
