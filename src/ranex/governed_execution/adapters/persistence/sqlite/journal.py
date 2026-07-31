"""Append-only evaluation journal, hash-chained.

Append-only is enforced twice: there is no update or delete method, and SQLite
triggers reject both even for a caller holding a raw connection. The hash chain
makes an out-of-band edit detectable rather than merely discouraged.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ranex.foundation.canonical import canonical_json, canonical_sha256

_GENESIS = "sha256:" + "0" * 64

_SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluations (
    seq        INTEGER PRIMARY KEY AUTOINCREMENT,
    record     TEXT NOT NULL,
    prev_link  TEXT NOT NULL,
    link       TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS evaluations_no_update
BEFORE UPDATE ON evaluations
BEGIN
    SELECT RAISE(ABORT, 'evaluations is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evaluations_no_delete
BEFORE DELETE ON evaluations
BEGIN
    SELECT RAISE(ABORT, 'evaluations is append-only');
END;
"""


class Journal:
    """Durable, ordered, tamper-evident record of every evaluation."""

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path)
        conn.row_factory = sqlite3.Row
        conn.executescript(_SCHEMA)
        return conn

    def append(self, evaluation: Any) -> str:
        """Append one evaluation and return its chain link."""

        record = evaluation.as_record()
        payload = canonical_json(record)
        with self._connect() as conn:
            row = conn.execute(
                "SELECT link FROM evaluations ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            prev_link = row["link"] if row is not None else _GENESIS
            link = "sha256:" + canonical_sha256(
                {"prev_link": prev_link, "record": record}
            )
            conn.execute(
                "INSERT INTO evaluations (record, prev_link, link) VALUES (?, ?, ?)",
                (payload, prev_link, link),
            )
        return link

    def entries(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT record FROM evaluations ORDER BY seq ASC"
            ).fetchall()
        return [json.loads(row["record"]) for row in rows]

    def verify(self) -> bool:
        """Recompute the chain. False means a row changed outside `append`."""

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT record, prev_link, link FROM evaluations ORDER BY seq ASC"
            ).fetchall()
        prev_link = _GENESIS
        for row in rows:
            if row["prev_link"] != prev_link:
                return False
            expected = "sha256:" + canonical_sha256(
                {"prev_link": prev_link, "record": json.loads(row["record"])}
            )
            if expected != row["link"]:
                return False
            prev_link = row["link"]
        return True
