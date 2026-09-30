"""Append-only observation log, hash-chained (RISK-11, ADR-068).

`evidence.json` is a current view: `record_evidence` replaces a producer's
earlier record for the same claim, so a recorded FAIL could be overwritten or
deleted and evaluation would read the gap as work never done. `run` therefore
also appends every signed record it writes to this log, with the journal's
schema discipline — no update or delete method, triggers refusing both, and a
link chaining each row to its predecessor.

The log is history; `evidence.json` stays the projection the kernel judges.
`reconcile` compares the two: the chain's latest record for each
claim+producer must be in the projection. A latest record the projection lacks
is a *removed observation*, restored for judgment and named in the diagnosis
rather than read as honest absence. The caller refuses any admitted record the
chain never held.
"""

from __future__ import annotations

import json
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_json, canonical_sha256
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

OBSERVATION_CHAIN_ERROR = "E-OBSERVATION-CHAIN"
REMOVED_OBSERVATION = "removed-observation"
GENESIS = "sha256:" + "0" * 64


@dataclass(frozen=True, slots=True)
class ObservationSnapshot:
    records: tuple[tuple[int, dict[str, Any]], ...]
    head: str
    position: int


def _verified_snapshot(rows: Any, expected_head: str | None) -> ObservationSnapshot:
    head = GENESIS
    retained = expected_head is None or expected_head == GENESIS
    records: list[tuple[int, dict[str, Any]]] = []
    position = 0
    for row in rows:
        try:
            record = json.loads(row["record"])
            link = "sha256:" + canonical_sha256({"prev_link": head, "record": record})
            if row["prev_link"] != head or row["link"] != link:
                raise ValueError("inconsistent link")
            if not isinstance(record, dict) or int(row["seq"]) <= position:
                raise ValueError("invalid observation row")
        except (ValueError, TypeError, RecursionError) as exc:
            raise ValueError(f"{OBSERVATION_CHAIN_ERROR}: invalid observation chain") from exc
        position = int(row["seq"])
        head = link
        retained = retained or head == expected_head
        records.append((position, record))
    if not retained:
        raise ValueError("E-OBSERVATION-ANCHOR: retained history head is absent")
    return ObservationSnapshot(tuple(records), head, position)


class ObservationLog(Journal):
    """Durable, ordered, tamper-evident record of every signed observation."""

    _table = "observations"

    @property
    def path(self) -> Path:
        return self._path

    def records(self) -> list[tuple[int, dict[str, Any]]]:
        """Every row as ``(seq, record)``, read-only; a missing log is empty.

        Absence of the file is not refused here: an evidence file with records
        and no log is refused by the caller, record by record, and an empty
        evidence file with no log has nothing to reconcile.
        """

        if not self._path.is_file():
            return []
        with closing(self._connect_for_verification()) as conn, conn:
            rows = conn.execute(
                "SELECT seq, record FROM observations ORDER BY seq ASC"
            ).fetchall()
        return [(int(row["seq"]), json.loads(row["record"])) for row in rows]

    def snapshot(self, *, expected_head: str | None = None) -> ObservationSnapshot:
        """Verify and decode the same SQLite read snapshot, including its head."""
        if not self.path.is_file():
            if expected_head is not None:
                raise ValueError("E-OBSERVATION-ANCHOR: anchored observation log is missing")
            return ObservationSnapshot((), GENESIS, 0)
        with closing(self._connect_for_verification()) as conn, conn:
            rows = conn.execute(
                "SELECT seq, record, prev_link, link FROM observations ORDER BY seq ASC"
            ).fetchall()
        return _verified_snapshot(rows, expected_head)


def observations_path_for(evidence_path: Path) -> Path:
    """The log paired with one evidence file.

    Paired rather than fixed, because the log reconciles against exactly one
    projection: a second evidence file in the same repository sharing it would
    see the first file's records as removed. The default pairing is
    `governance/evidence.json` beside `governance/observations.sqlite3`.
    """

    if evidence_path.name == "evidence.json":
        return evidence_path.with_name("observations.sqlite3")
    return evidence_path.with_name(evidence_path.name + ".observations.sqlite3")


@dataclass(frozen=True, slots=True)
class RemovedObservation:
    """A chain-latest record the evidence file no longer holds."""

    seq: int
    claim_id: str
    producer_id: str

    def describe(self) -> str:
        return (
            f"{REMOVED_OBSERVATION} claim={self.claim_id} "
            f"producer={self.producer_id} seq={self.seq}"
        )


@dataclass(frozen=True, slots=True)
class Reconciliation:
    """The records to judge, and what had to be restored to get them."""

    records: list[Any]
    removed: tuple[RemovedObservation, ...]
    chained: frozenset[str]
    head: str = GENESIS
    position: int = 0

    def in_chain(self, record: Any) -> bool:
        return identity(record) in self.chained


def identity(record: Any) -> str:
    """A record's canonical bytes; what `run` appended is what must match."""

    try:
        return canonical_json(record)
    except (TypeError, ValueError):
        # A record canonical JSON cannot encode was never written by `run`,
        # so it can match nothing in the chain.
        return ""


def _key(record: Any) -> tuple[str, str] | None:
    if not isinstance(record, dict):
        return None
    claim, producer = record.get("claim_id"), record.get("producer_id")
    if not isinstance(claim, str) or not isinstance(producer, str):
        return None
    return claim, producer


def reconcile(log: ObservationLog, evidence: list[Any], *, expected_head: str | None = None,
              snapshot: ObservationSnapshot | None = None) -> Reconciliation:
    """Project the chain onto the evidence file, or refuse a broken chain.

    The projection `record_evidence` maintains is the chain's latest record per
    claim+producer. An evidence record the chain supersedes (an older record
    put back over a newer one) is dropped, and a chain-latest record the file
    lacks is restored and reported as removed. Records the chain never held
    pass through unchanged; the caller refuses those that would count.
    """

    snapshot = snapshot if snapshot is not None else log.snapshot(expected_head=expected_head)
    latest: dict[tuple[str, str], tuple[int, Any]] = {}
    chained: set[str] = set()
    for seq, record in snapshot.records:
        key = _key(record)
        if key is None:
            raise ValueError(
                f"{OBSERVATION_CHAIN_ERROR}: observation log row seq={seq} "
                "names no claim_id/producer_id"
            )
        latest[key] = (seq, record)
        chained.add(identity(record))
    latest_identities = {identity(record) for _, record in latest.values()}
    present = {identity(record) for record in evidence}

    kept = [
        record
        for record in evidence
        if identity(record) not in chained or identity(record) in latest_identities
    ]
    removed: list[RemovedObservation] = []
    for (claim, producer), (seq, record) in sorted(latest.items(), key=lambda i: i[1][0]):
        if identity(record) not in present:
            kept.append(record)
            removed.append(RemovedObservation(seq, claim, producer))
    return Reconciliation(kept, tuple(removed), frozenset(chained), snapshot.head, snapshot.position)
