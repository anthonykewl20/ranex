"""Crash recovery exercised by killing a real process, per SQLite's own method.

The existing crash-boundary test installs a SQLite `RAISE(ABORT)` trigger. The
resulting exception is caught by the store's own `except` handler, which issues
`ROLLBACK` — the code path a real crash never executes. No process dies, the
filesystem is never exposed to an interrupted commit, and removing durability
settings would not fail that test.

SQLite documents the credible procedure (https://sqlite.org/testing.html): a
parent creates a known durable database, a separate child performs the
transition, the parent kills the child, a fresh process reopens the real file,
runs `PRAGMA integrity_check`, and accepts only the complete old state or the
complete new state — never a mixture.
"""

from __future__ import annotations

import os
import signal
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from ranex.foundation.identity import Identity
from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    SQLiteExecutionStore,
)
from ranex.governed_execution.domain.events import (
    ExecutionCreated,
    ExecutionMarkedReady,
)
from ranex.governed_execution.domain.status import ExecutionStatus

RUN_ID = Identity.parse(
    "run_01890f47-25a1-7e01-98b3-5f5f6bb25af7", expected_prefix="run"
)
WORK_ITEM_ID = Identity.parse(
    "work_01890f47-25a1-7e02-98b3-5f5f6bb25af7", expected_prefix="work"
)
PRINCIPAL_ID = Identity.parse(
    "principal_01890f47-25a1-7e03-98b3-5f5f6bb25af7", expected_prefix="principal"
)


def event_id(sequence: int) -> Identity:
    return Identity.parse(
        f"transition_01890f47-25a1-7f{sequence:02x}-98b3-5f5f6bb25af7",
        expected_prefix="transition",
    )


CHILD = textwrap.dedent(
    """
    import os, signal, sys
    from ranex.foundation.identity import Identity
    from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
        SQLiteExecutionStore,
    )
    from ranex.governed_execution.domain.events import ExecutionMarkedReady

    database_path, hold = sys.argv[1], sys.argv[2]
    run_id = Identity.parse(
        "run_01890f47-25a1-7e01-98b3-5f5f6bb25af7", expected_prefix="run"
    )
    store = SQLiteExecutionStore(database_path)

    # Die abruptly while the write transaction is open. SIGKILL cannot be
    # handled, so no rollback handler, atexit hook, or context manager runs --
    # the operating system removes the process mid-transaction.
    import ranex.governed_execution.adapters.persistence.sqlite.execution_store as mod
    original = mod.SQLiteExecutionStore._require_journal_agreement

    real_execute = None

    class Killer:
        def __init__(self, connection):
            self._connection = connection

        def __getattr__(self, name):
            return getattr(self._connection, name)

        def execute(self, statement, *args):
            result = self._connection.execute(statement, *args)
            if hold in statement:
                os.kill(os.getpid(), signal.SIGKILL)
            return result

    connect = mod.SQLiteExecutionStore._connect
    mod.SQLiteExecutionStore._connect = lambda self: Killer(connect(self))

    store.append(
        ExecutionMarkedReady(
            event_id=Identity.parse(
                "transition_01890f47-25a1-7f02-98b3-5f5f6bb25af7",
                expected_prefix="transition",
            ),
            execution_id=run_id,
            expected_version=1,
            occurred_at="2026-07-30T02:00:01Z",
            readiness_snapshot_ref="snapshot:sha256:ready",
        )
    )
    """
).strip()


def seed(database_path: Path) -> None:
    store = SQLiteExecutionStore(database_path)
    store.initialize()
    store.append(
        ExecutionCreated(
            event_id=event_id(1),
            execution_id=RUN_ID,
            expected_version=0,
            occurred_at="2026-07-30T02:00:00Z",
            work_item_id=WORK_ITEM_ID,
            created_by_principal_id=PRINCIPAL_ID,
            workflow_request_ref="workflow-request:sha256:crash",
        )
    )


@pytest.mark.parametrize(
    "kill_after",
    ["UPDATE execution_state", "INSERT INTO execution_journal", "COMMIT"],
    ids=["after-state-update", "after-journal-insert", "at-commit"],
)
def test_process_kill_leaves_only_complete_old_or_new_state(
    tmp_path: Path,
    kill_after: str,
) -> None:
    database_path = tmp_path / "kernel.sqlite3"
    seed(database_path)

    child = subprocess.run(
        [sys.executable, "-c", CHILD, str(database_path), kill_after],
        capture_output=True,
        env={**os.environ, "PYTHONPATH": "src"},
    )
    # SIGKILL is not catchable; a negative return code proves the process was
    # killed rather than exiting through any application code path.
    assert child.returncode == -signal.SIGKILL, child.stderr.decode()[-400:]

    # A FRESH process reopens the real file, as SQLite's method requires.
    with sqlite3.connect(database_path) as connection:
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []

    reopened = SQLiteExecutionStore(database_path)
    state = reopened.load(RUN_ID)
    assert state is not None

    # Only the complete old state or the complete new state is acceptable.
    assert state.status in {ExecutionStatus.PROPOSED, ExecutionStatus.READY}
    assert state.version in {1, 2}
    if state.status is ExecutionStatus.PROPOSED:
        assert state.version == 1
    else:
        assert state.version == 2

    # The journal must agree with whichever state survived, which load() now
    # enforces, and replay of persisted bytes must reproduce it.
    assert reopened.replay_history(RUN_ID) == state
