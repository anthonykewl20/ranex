"""Validate, sign, and atomically publish verdict records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ranex.foundation import atomic_writer
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.foundation.verdict_signing import PAYLOAD_TYPE, SIGNED_FIELDS, sign_verdict

_SAFE = 2**53 - 1


def validate_publication_value(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("floats cannot be published")
    if isinstance(value, int) and not isinstance(value, bool) and not -_SAFE <= value <= _SAFE:
        raise ValueError("integer is outside the TypeScript safe range")
    if isinstance(value, str) and any(ord(char) > 0xFFFF for char in value):
        raise ValueError("non-BMP Unicode cannot be published")
    if isinstance(value, Mapping):
        for key, item in value.items():
            validate_publication_value(key)
            validate_publication_value(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_publication_value(item)


def publish_verdict(path: Path, record: Mapping[str, Any], *, signer_id: str, private_key: str) -> None:
    if set(record) != {*SIGNED_FIELDS, "record_digest"}:
        raise ValueError("verdict publication must contain the exact Record fields")
    content = {field: record[field] for field in SIGNED_FIELDS}
    validate_publication_value(content)
    expected = "sha256:" + canonical_sha256(content)
    if record.get("record_digest") != expected:
        raise ValueError("record_digest does not bind the signed verdict fields")
    envelope = {"payload_type": PAYLOAD_TYPE, "record": dict(record), "signatures": [
        {"signer_id": signer_id, "signature": sign_verdict(content, private_key)}
    ]}
    atomic_writer.write_atomic(path, canonical_json_bytes(envelope))
