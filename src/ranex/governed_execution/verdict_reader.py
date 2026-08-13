"""Closed-state reader for signed verdict publications."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.verdict_signing import PAYLOAD_TYPE, SIGNED_FIELDS, verify_verdict


class ReadState(StrEnum):
    ABSENT = "absent"
    MALFORMED = "malformed"
    UNSIGNED = "unsigned"
    BAD_SIGNATURE = "bad-signature"
    UNKNOWN_SIGNER = "unknown-signer"
    WRONG_PAYLOAD_TYPE = "wrong-payload-type"
    MISSING_KEY = "missing-key"
    CONTEXT_MISMATCH = "context-mismatch"
    UNKNOWN_CAUSE = "unknown-cause"
    VERIFIED = "verified"


STATE_PRESENTATION = {
    ReadState.ABSENT: "No verdict publication exists.",
    ReadState.MALFORMED: "The verdict publication is malformed or unreadable.",
    ReadState.UNSIGNED: "The verdict publication is unsigned.",
    ReadState.BAD_SIGNATURE: "The verdict signature is invalid.",
    ReadState.UNKNOWN_SIGNER: "The verdict names an unknown signer.",
    ReadState.WRONG_PAYLOAD_TYPE: "The verdict payload type is unsupported.",
    ReadState.MISSING_KEY: "The verdict signer key is unavailable.",
    ReadState.CONTEXT_MISMATCH: "The verdict belongs to another judgment context.",
    ReadState.UNKNOWN_CAUSE: "The verdict contains an unclassified blocking cause.",
    ReadState.VERIFIED: "The verdict is verified; freshness is unestablished.",
}


@dataclass(frozen=True, slots=True)
class ReadResult:
    state: ReadState
    record: Mapping[str, Any] | None = None


def read_verdict(path: Path, keyring: Mapping[str, str], *, subject_digest: str,
                  gate_id: str, catalog_digest: str | None, approver_id: str) -> ReadResult:
    try:
        value = json.loads(
            Path(path).read_bytes(),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number: {value}")
            ),
        )
    except FileNotFoundError:
        return ReadResult(ReadState.ABSENT)
    except (OSError, UnicodeError, ValueError, TypeError):
        return ReadResult(ReadState.MALFORMED)
    try:
        if not isinstance(value, Mapping) or set(value) != {"payload_type", "record", "signatures"}:
            return ReadResult(ReadState.MALFORMED)
        if value["payload_type"] != PAYLOAD_TYPE:
            return ReadResult(ReadState.WRONG_PAYLOAD_TYPE)
        signatures = value["signatures"]
        if not isinstance(signatures, list):
            return ReadResult(ReadState.MALFORMED)
        if not signatures:
            return ReadResult(ReadState.UNSIGNED)
        signature = signatures[0]
        if not isinstance(signature, Mapping) or set(signature) != {"signer_id", "signature"}:
            return ReadResult(ReadState.MALFORMED)
        signer = signature["signer_id"]
        if not isinstance(signer, str):
            return ReadResult(ReadState.MALFORMED)
        if signer not in keyring:
            return ReadResult(ReadState.MISSING_KEY if not keyring else ReadState.UNKNOWN_SIGNER)
        record = value["record"]
        if not isinstance(record, Mapping) or set(record) != {*SIGNED_FIELDS, "record_digest"}:
            return ReadResult(ReadState.MALFORMED)
        content = {field: record[field] for field in SIGNED_FIELDS}
        if record["record_digest"] != "sha256:" + canonical_sha256(content):
            return ReadResult(ReadState.BAD_SIGNATURE)
        if not verify_verdict(content, signature["signature"], keyring[signer], payload_type=value["payload_type"]):
            return ReadResult(ReadState.BAD_SIGNATURE)
        if any(record[field] != expected for field, expected in (
            ("subject_digest", subject_digest), ("gate_id", gate_id),
            ("catalog_digest", catalog_digest), ("approver_id", approver_id),
        )):
            return ReadResult(ReadState.CONTEXT_MISMATCH)
        known = {"contradicted", "failed", "mismatched", "stale", "absent", "refused", "unattributable"}
        causes = record["causes"]
        if not isinstance(causes, list):
            return ReadResult(ReadState.MALFORMED)
        if any(not isinstance(cause, Mapping) or cause.get("cause") not in known for cause in causes):
            return ReadResult(ReadState.UNKNOWN_CAUSE, record)
        return ReadResult(ReadState.VERIFIED, record)
    except (OSError, UnicodeError, ValueError, TypeError):
        return ReadResult(ReadState.MALFORMED)
