from __future__ import annotations

import fcntl
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_json

_GENESIS_DIGEST = "0" * 64


class LedgerIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    sequence: int
    previous_digest: str
    record_digest: str
    entry_digest: str
    record: dict[str, Any]


@dataclass(frozen=True, slots=True)
class LedgerVerification:
    valid: bool
    entry_count: int
    broken_sequence: int | None
    head_digest: str
    reason: str | None = None


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _entry_digest(
    *,
    sequence: int,
    previous_digest: str,
    record_digest: str,
) -> str:
    return _sha256_text(
        canonical_json(
            {
                "previous_digest": previous_digest,
                "record_digest": record_digest,
                "sequence": sequence,
            }
        )
    )


class HashChainLedger:
    """Append-only API over a tamper-evident canonical JSONL hash chain."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def _verify_lines(self, lines: list[str]) -> LedgerVerification:
        previous_digest = _GENESIS_DIGEST
        for expected_sequence, line in enumerate(lines, start=1):
            try:
                raw = json.loads(line)
                record = raw["record"]
                record_digest = _sha256_text(canonical_json(record))
                computed_entry_digest = _entry_digest(
                    sequence=expected_sequence,
                    previous_digest=previous_digest,
                    record_digest=record_digest,
                )
                valid = (
                    raw["sequence"] == expected_sequence
                    and raw["previous_digest"] == previous_digest
                    and raw["record_digest"] == record_digest
                    and raw["entry_digest"] == computed_entry_digest
                )
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                valid = False
                computed_entry_digest = previous_digest
            if not valid:
                return LedgerVerification(
                    valid=False,
                    entry_count=len(lines),
                    broken_sequence=expected_sequence,
                    head_digest=previous_digest,
                    reason="ledger hash chain is invalid",
                )
            previous_digest = computed_entry_digest
        return LedgerVerification(
            valid=True,
            entry_count=len(lines),
            broken_sequence=None,
            head_digest=previous_digest,
        )

    def verify(self) -> LedgerVerification:
        if not self._path.exists():
            return LedgerVerification(
                valid=False,
                entry_count=0,
                broken_sequence=None,
                head_digest=_GENESIS_DIGEST,
                reason="ledger file is missing",
            )
        with self._path.open("r", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
            lines = [line for line in stream.read().splitlines() if line.strip()]
        if not lines:
            return LedgerVerification(
                valid=False,
                entry_count=0,
                broken_sequence=None,
                head_digest=_GENESIS_DIGEST,
                reason="ledger file is empty",
            )
        return self._verify_lines(lines)

    def append(self, record: dict[str, Any]) -> LedgerEntry:
        return self._append(record, idempotency_key=None)

    def append_once(self, record: dict[str, Any], *, key: str) -> LedgerEntry:
        if not key:
            raise ValueError("idempotency key must be non-empty")
        return self._append(record, idempotency_key=key)

    def _append(
        self,
        record: dict[str, Any],
        *,
        idempotency_key: str | None,
    ) -> LedgerEntry:
        if "_ledger_idempotency_key" in record:
            raise ValueError("record uses a reserved ledger field")
        stored_record = dict(record)
        if idempotency_key is not None:
            stored_record["_ledger_idempotency_key"] = idempotency_key

        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.touch(mode=0o600, exist_ok=True)
        self._path.chmod(0o600)
        with self._path.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.seek(0)
            lines = [line for line in stream.read().splitlines() if line.strip()]
            verification = self._verify_lines(lines)
            if not verification.valid:
                raise LedgerIntegrityError(
                    "refusing append because the ledger hash chain is invalid"
                )

            if idempotency_key is not None:
                for line in lines:
                    raw = json.loads(line)
                    existing_record = raw["record"]
                    if (
                        existing_record.get("_ledger_idempotency_key")
                        == idempotency_key
                    ):
                        if canonical_json(existing_record) != canonical_json(
                            stored_record
                        ):
                            raise LedgerIntegrityError(
                                "idempotency key was reused for a different record"
                            )
                        return LedgerEntry(
                            sequence=raw["sequence"],
                            previous_digest=raw["previous_digest"],
                            record_digest=raw["record_digest"],
                            entry_digest=raw["entry_digest"],
                            record=existing_record,
                        )

            sequence = verification.entry_count + 1
            record_digest = _sha256_text(canonical_json(stored_record))
            entry_digest = _entry_digest(
                sequence=sequence,
                previous_digest=verification.head_digest,
                record_digest=record_digest,
            )
            entry = LedgerEntry(
                sequence=sequence,
                previous_digest=verification.head_digest,
                record_digest=record_digest,
                entry_digest=entry_digest,
                record=stored_record,
            )
            stream.seek(0, os.SEEK_END)
            stream.write(
                canonical_json(
                    {
                        "sequence": entry.sequence,
                        "previous_digest": entry.previous_digest,
                        "record_digest": entry.record_digest,
                        "entry_digest": entry.entry_digest,
                        "record": entry.record,
                    }
                )
                + "\n"
            )
            stream.flush()
            os.fsync(stream.fileno())
            return entry
