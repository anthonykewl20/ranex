from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.assurance.adapters.persistence.jsonl.hash_chain_ledger import (
    HashChainLedger,
    LedgerIntegrityError,
)
from ranex.foundation.canonical import canonical_json


def test_hash_chain_ledger_appends_and_verifies(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    ledger = HashChainLedger(path)

    first = ledger.append({"decision": "UNKNOWN", "request_id": "one"})
    second = ledger.append({"decision": "PASS", "request_id": "two"})
    verification = ledger.verify()

    assert first.sequence == 1
    assert second.sequence == 2
    assert second.previous_digest == first.entry_digest
    assert verification.valid is True
    assert verification.entry_count == 2
    assert verification.head_digest == second.entry_digest
    assert path.stat().st_mode & 0o777 == 0o600


def test_hash_chain_ledger_detects_edit_and_refuses_append(
    tmp_path: Path,
) -> None:
    path = tmp_path / "audit.jsonl"
    ledger = HashChainLedger(path)
    ledger.append({"decision": "PASS"})
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["record"]["decision"] = "FAIL"
    path.write_text(canonical_json(raw) + "\n", encoding="utf-8")

    verification = ledger.verify()

    assert verification.valid is False
    assert verification.broken_sequence == 1
    with pytest.raises(LedgerIntegrityError):
        ledger.append({"decision": "UNKNOWN"})


def test_hash_chain_idempotency_key_cannot_change_record(tmp_path: Path) -> None:
    ledger = HashChainLedger(tmp_path / "audit.jsonl")
    first = ledger.append_once({"decision": "PASS"}, key="request-1")
    replay = ledger.append_once({"decision": "PASS"}, key="request-1")

    assert replay == first
    with pytest.raises(LedgerIntegrityError, match="reused"):
        ledger.append_once({"decision": "FAIL"}, key="request-1")
