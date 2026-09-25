"""Atomic file replacement helper."""
from __future__ import annotations

import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def atomic_write(destination: Path, render: Callable[[Path], T]) -> T:
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp_name = tempfile.mkstemp(
        dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        os.close(handle)
        result = render(tmp_path)
        os.replace(tmp_path, destination)
        return result
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def write_text_atomic(destination: Path, text: str) -> None:
    atomic_write(destination, lambda p: p.write_text(text, encoding="utf-8"))
