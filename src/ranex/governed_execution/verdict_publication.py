"""Validate, sign, and atomically publish verdict records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ranex.foundation import atomic_writer
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.foundation.publication_validation import validate_publication_value
from ranex.foundation.verdict_signing import PAYLOAD_TYPE, SIGNED_FIELDS, sign_verdict


def publish_verdict(path: Path, record: Mapping[str, Any], *, root: Path,
                    signer_id: str, private_key: str) -> None:
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
    atomic_writer.write_atomic(path, canonical_json_bytes(envelope), root=root)
