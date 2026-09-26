"""Validate, sign, and atomically publish verdict records."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ranex.foundation import atomic_writer
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256
from ranex.foundation.publication_validation import validate_publication_value
from ranex.foundation.verdict_signing import PAYLOAD_TYPE, SIGNED_FIELDS, sign_verdict


def publish_verdict(
    path: Path, record: Mapping[str, Any], *, root: Path,
    signer_id: str, private_key: str,
    approver: tuple[str, str] | None = None,
) -> None:
    """Publish the signed verdict, optionally countersigned by its approver.

    `approver` is the catalogued approver's `(principal_id, private_key)`
    (RISK-07). The approver signs the same content over the same domain as the
    verdict signer — a second proof, never a different payload — and the entry
    is appended after the signer's so `signatures[0]` stays the judgment
    signature every existing reader already verifies.
    """

    if set(record) != {*SIGNED_FIELDS, "record_digest"}:
        raise ValueError("verdict publication must contain the exact Record fields")
    content = {field: record[field] for field in SIGNED_FIELDS}
    validate_publication_value(content)
    expected = "sha256:" + canonical_sha256(content)
    if record.get("record_digest") != expected:
        raise ValueError("record_digest does not bind the signed verdict fields")
    signatures = [
        {"signer_id": signer_id, "signature": sign_verdict(content, private_key)}
    ]
    if approver is not None:
        approver_id, approver_key = approver
        signatures.append(
            {"signer_id": approver_id, "signature": sign_verdict(content, approver_key)}
        )
    envelope = {
        "payload_type": PAYLOAD_TYPE, "record": dict(record), "signatures": signatures,
    }
    atomic_writer.write_atomic(path, canonical_json_bytes(envelope), root=root)
