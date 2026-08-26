"""Cross-process regression for the shared strict-local host-probe mutation."""

from __future__ import annotations

import os
import time
from pathlib import Path

from launcher_host import require_unprivileged_userns

from ranex.cli.host_confinement import _host_probe_lock


def test_host_probe_lock_serializes_waiting_controller_processes(tmp_path: Path) -> None:
    require_unprivileged_userns()
    events = tmp_path / "events"
    gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
    children: list[int] = []
    for identity in ("first", "second"):
        child = os.fork()
        if child == 0:
            os.close(gate_write)
            if os.read(gate_read, 1) != b"1":
                os._exit(125)
            with _host_probe_lock():
                descriptor = os.open(
                    events,
                    os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_CLOEXEC,
                    0o600,
                )
                try:
                    os.write(descriptor, f"start:{identity}\n".encode())
                    time.sleep(0.15)
                    os.write(descriptor, f"end:{identity}\n".encode())
                finally:
                    os.close(descriptor)
            os._exit(0)
        children.append(child)
    os.close(gate_read)
    with _host_probe_lock():
        os.write(gate_write, b"11")
        os.close(gate_write)
        time.sleep(0.1)
        assert all(os.waitpid(child, os.WNOHANG) == (0, 0) for child in children)

    for child in children:
        waited, status = os.waitpid(child, 0)
        assert waited == child and os.waitstatus_to_exitcode(status) == 0
    observed = events.read_text(encoding="utf-8").splitlines()
    assert observed in (
        ["start:first", "end:first", "start:second", "end:second"],
        ["start:second", "end:second", "start:first", "end:first"],
    )
