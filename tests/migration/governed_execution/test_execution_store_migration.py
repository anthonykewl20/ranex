from __future__ import annotations

import sqlite3
from pathlib import Path

from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    SQLiteExecutionStore,
)


def test_initial_migration_is_repeatable_and_records_schema_version(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "migration.sqlite3"
    store = SQLiteExecutionStore(database_path)

    store.initialize()
    store.initialize()

    with sqlite3.connect(database_path) as connection:
        user_version = connection.execute("PRAGMA user_version").fetchone()
        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_schema
                WHERE type = 'table' AND name LIKE 'execution_%'
                """
            )
        }

    assert user_version == (1,)
    assert tables == {
        "execution_state",
        "execution_journal",
        "execution_outbox",
    }
