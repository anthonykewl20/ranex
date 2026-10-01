from __future__ import annotations

from pathlib import Path

import pytest

from ranex.governed_execution.adapters.persistence.sqlite.observations import (
    ObservationLog,
    reconcile,
)


def observation(exit_code: int) -> dict[str, object]:
    return {"claim_id": "tests", "producer_id": "worker", "exit_code": exit_code}


def test_reconciliation_reads_verified_rows_and_head_in_one_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    log = ObservationLog(tmp_path / "observations.sqlite3")
    recorded = observation(1)
    head = log.append_record(recorded)
    original = log._connect_for_verification
    connections = 0

    def connect():
        nonlocal connections
        connections += 1
        return original()

    monkeypatch.setattr(log, "_connect_for_verification", connect)
    result = reconcile(log, [])

    assert connections == 1
    assert result.head == head
    assert result.records == [recorded]
    assert result.removed[0].seq == 1


def test_retained_checkpoint_accepts_an_honest_history_extension(tmp_path: Path) -> None:
    log = ObservationLog(tmp_path / "observations.sqlite3")
    checkpoint = log.append_record(observation(0))
    latest = observation(1)
    current = log.append_record(latest)

    result = reconcile(log, [], expected_head=checkpoint)

    assert result.head == current
    assert result.records == [latest]


def test_rebuilt_consistent_history_cannot_discard_a_retained_failure_head(
    tmp_path: Path,
) -> None:
    path = tmp_path / "observations.sqlite3"
    log = ObservationLog(path)
    passed = observation(0)
    log.append_record(passed)
    checkpoint = log.append_record(observation(1))
    path.unlink()
    replacement = ObservationLog(path)
    replacement.append_record(passed)
    assert replacement.verify()

    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile(replacement, [passed], expected_head=checkpoint)


def test_a_retained_history_checkpoint_refuses_a_deleted_log(tmp_path: Path) -> None:
    log = ObservationLog(tmp_path / "observations.sqlite3")
    checkpoint = log.append_record(observation(1))
    log.path.unlink()

    with pytest.raises(ValueError, match="E-OBSERVATION-ANCHOR"):
        reconcile(log, [], expected_head=checkpoint)
