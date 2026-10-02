import inspect
import os
import time
from pathlib import Path

import pytest

from ranex.cli.process_supervisor import (
    BUBBLEWRAP_PROBE_TIMEOUT_SECONDS,
    ProcessSupervisorError,
    _probe_bubblewrap,
)


def test_hung_probe_is_refused_within_its_deadline(tmp_path: Path) -> None:
    path = tmp_path / "hang.sh"
    path.write_text("#!/bin/sh\nexec sleep 30\n")
    path.chmod(0o755)
    bwrap_fd = os.open(path, os.O_RDONLY)
    python_fd = os.open("/bin/true", os.O_RDONLY)
    try:
        started = time.monotonic()
        with pytest.raises(ProcessSupervisorError, match="deadline"):
            _probe_bubblewrap(bwrap_fd, python_fd, tmp_path, timeout=0.5)
        assert time.monotonic() - started < 5
    finally:
        os.close(bwrap_fd)
        os.close(python_fd)


def test_probe_deadline_constant_is_finite() -> None:
    assert 0 < BUBBLEWRAP_PROBE_TIMEOUT_SECONDS <= 60
    assert (
        inspect.signature(_probe_bubblewrap).parameters["timeout"].default
        == BUBBLEWRAP_PROBE_TIMEOUT_SECONDS
    )
