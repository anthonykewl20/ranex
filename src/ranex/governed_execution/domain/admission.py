"""Which records become evidence, and why the rest did not.

`evaluate()` is a pure function of (gate, evidence, subject, approver) and stays
one. Verification happens here instead, so a record that does not verify is
never admitted and reaches the kernel as *absence* — which already blocks.

That reduction is only safe because rejections leave here as **structured data**.
Both forged and absent produce FAIL, but they are not the same event: absence is
work not done, forgery is an attack. If the difference lived only in printed
prose, an automated consumer would read an attack as a missing task.

The trust chain, stated once:

    raw records + keyring  ──admit──▶  admitted evidence  ──evaluate()──▶  verdict
                                       + rejections

The keyring is an input to admission and never to the kernel. Keys are ambient
machine state, and a kernel whose judgement depended on them would break the
principle behind "removing every credential from the machine must not change a
verdict".

`admit` takes a plain mapping of producer id to public key, never a path and
never a loader: the domain does not reach for adapters.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from ranex.foundation.signing import (
    SIGNED_FIELDS,
    is_signature,
    verify_evidence,
)
from ranex.governed_execution.domain.verdict import Evidence


class RejectionReason(StrEnum):
    """Why a record is not evidence.

    Deliberately none of these reads as "no evidence for required claim". That
    is the kernel's phrasing for honest absence, and a rejection must never be
    mistakable for it.
    """

    MALFORMED_RECORD = "malformed-record"
    MISSING_SIGNATURE = "missing-signature"
    MALFORMED_SIGNATURE = "malformed-signature"
    UNKNOWN_PRODUCER = "unknown-producer"
    BAD_SIGNATURE = "bad-signature"


@dataclass(frozen=True, slots=True)
class Rejection:
    """One record that did not become evidence, locatable by a human."""

    index: int
    reason: RejectionReason
    detail: str
    producer_id: str | None
    claim_id: str | None


@dataclass(frozen=True, slots=True)
class Admission:
    evidence: tuple[Evidence, ...]
    rejections: tuple[Rejection, ...]


_SIGNATURE = "signature"


def _text_or_none(record: Mapping[str, Any], field: str) -> str | None:
    value = record.get(field)
    return value if isinstance(value, str) else None


def admit(
    records: Sequence[Any],
    keyring: Mapping[str, str],
) -> Admission:
    """Split records into evidence and rejections. Never raises on bad input."""

    evidence: list[Evidence] = []
    rejections: list[Rejection] = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            rejections.append(
                Rejection(
                    index=index,
                    reason=RejectionReason.MALFORMED_RECORD,
                    detail="record is not a JSON object",
                    producer_id=None,
                    claim_id=None,
                )
            )
            continue

        producer_id = _text_or_none(record, "producer_id")
        claim_id = _text_or_none(record, "claim_id")

        def reject(reason: RejectionReason, detail: str) -> None:
            rejections.append(
                Rejection(
                    index=index,
                    reason=reason,
                    detail=detail,
                    producer_id=producer_id,
                    claim_id=claim_id,
                )
            )

        content = {k: v for k, v in record.items() if k != _SIGNATURE}
        if set(content) != set(SIGNED_FIELDS):
            unexpected = sorted(set(content) - set(SIGNED_FIELDS))
            missing = sorted(set(SIGNED_FIELDS) - set(content))
            parts = []
            if unexpected:
                parts.append(f"unexpected field(s): {', '.join(unexpected)}")
            if missing:
                parts.append(f"missing field(s): {', '.join(missing)}")
            # Checked before the signature: an extra field is outside the signed
            # bytes by construction, so verifying first would pass a record
            # carrying content nobody attested to.
            reject(RejectionReason.MALFORMED_RECORD, "; ".join(parts))
            continue

        if _SIGNATURE not in record:
            reject(
                RejectionReason.MISSING_SIGNATURE,
                "record carries no signature; unsigned records are not evidence",
            )
            continue

        if producer_id is None:
            reject(RejectionReason.MALFORMED_RECORD, "producer_id is not a string")
            continue

        public_key = keyring.get(producer_id)
        if public_key is None:
            # Never trusted by default. An unregistered producer is not a
            # producer.
            reject(
                RejectionReason.UNKNOWN_PRODUCER,
                f"no public key registered for producer {producer_id!r}",
            )
            continue

        signature = record[_SIGNATURE]
        if not is_signature(signature):
            reject(
                RejectionReason.MALFORMED_SIGNATURE,
                "signature is not an ed25519:<base64> value of the right length",
            )
            continue

        # Verified against the key registered for the producer the record
        # CLAIMS to be. Without that binding, a holder of any trusted key could
        # produce evidence under another identity and walk past no-self-approval.
        if not verify_evidence(content, signature, public_key):
            reject(
                RejectionReason.BAD_SIGNATURE,
                f"signature does not verify against the registered key for "
                f"{producer_id!r}; the record was altered or signed by another key",
            )
            continue

        try:
            admitted = Evidence(
                claim_id=content["claim_id"],
                subject_digest=content["subject_digest"],
                producer_id=content["producer_id"],
                command=content["command"],
                exit_code=content["exit_code"],
            )
        except (ValueError, TypeError) as exc:
            # A signature proves who wrote it, never that what they wrote is
            # well-formed.
            reject(RejectionReason.MALFORMED_RECORD, str(exc))
            continue

        evidence.append(admitted)

    return Admission(evidence=tuple(evidence), rejections=tuple(rejections))
