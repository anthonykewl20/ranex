"""Closed-state reader for signed verdict publications."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.verdict_signing import (
    VERSIONS,
    signed_fields_for,
    verify_verdict,
)


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
    payload_type: str | None = None

    @property
    def journal_head(self) -> str | None:
        """The anchor this verdict fixed, or None when it fixes none.

        ADR-057. A v1 record predates the anchor and carries no head at all, so
        it reads the same as a v2 record signed with no journal configured:
        unanchored. Callers that need an anchor must refuse both, and the two
        cases are deliberately indistinguishable here because the consequence
        is identical — there is no head to compare a chain against.
        """

        if self.record is None:
            return None
        head = self.record.get("journal_head")
        return head if isinstance(head, str) else None


def read_verdict_unbound(path: Path, keyring: Mapping[str, str]) -> ReadResult:
    """Envelope, digest and signature only — no judgment-context comparison.

    ADR-057. `journal verify --against-verdict` needs the anchor a verdict
    signed, and it knows nothing about the subject, gate, catalog or approver
    that verdict was about, so the four context fields cannot be supplied and
    must not be faked. Everything that establishes the record is *authentic*
    still runs; only the "is this the verdict I was expecting" comparison is
    absent, which is the caller's own question here.
    """

    return _read(path, keyring, context=None)


def read_verdict(path: Path, keyring: Mapping[str, str], *, subject_digest: str,
                  gate_id: str, catalog_digest: str | None, approver_id: str) -> ReadResult:
    return _read(path, keyring, context=(
        ("subject_digest", subject_digest), ("gate_id", gate_id),
        ("catalog_digest", catalog_digest), ("approver_id", approver_id),
    ))


def _read(path: Path, keyring: Mapping[str, str],
          *, context: tuple[tuple[str, str | None], ...] | None) -> ReadResult:
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
        payload_type = value["payload_type"]
        if payload_type not in VERSIONS:
            return ReadResult(ReadState.WRONG_PAYLOAD_TYPE)
        # ADR-057: every readable version verifies, because archived verdicts
        # are re-verified to prove old audits still hold. Only a v2 record may
        # ANCHOR anything — see `anchor` on the result.
        fields = signed_fields_for(payload_type)
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
        if not isinstance(record, Mapping) or set(record) != {*fields, "record_digest"}:
            return ReadResult(ReadState.MALFORMED)
        content = {field: record[field] for field in fields}
        if record["record_digest"] != "sha256:" + canonical_sha256(content):
            return ReadResult(ReadState.BAD_SIGNATURE)
        if not verify_verdict(content, signature["signature"], keyring[signer], payload_type=payload_type):
            return ReadResult(ReadState.BAD_SIGNATURE)
        if context is not None and any(
            record[field] != expected for field, expected in context
        ):
            return ReadResult(ReadState.CONTEXT_MISMATCH)
        known = {"contradicted", "failed", "mismatched", "stale", "absent", "refused", "unattributable"}
        causes = record["causes"]
        if not isinstance(causes, list):
            return ReadResult(ReadState.MALFORMED)
        if any(not isinstance(cause, Mapping) or cause.get("cause") not in known for cause in causes):
            return ReadResult(ReadState.UNKNOWN_CAUSE, record, payload_type)
        return ReadResult(ReadState.VERIFIED, record, payload_type)
    except (OSError, UnicodeError, ValueError, TypeError):
        return ReadResult(ReadState.MALFORMED)
