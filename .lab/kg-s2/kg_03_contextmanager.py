"""A temporary working directory helper."""
from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def pushed_directory(target: Path) -> Iterator[Path]:
    original = Path.cwd()
    os.chdir(target)
    try:
        yield target
    finally:
        os.chdir(original)


def deepest_common_root(paths: list[Path]) -> Path:
    if not paths:
        raise ValueError("paths must not be empty")
    common = paths[0].resolve()
    for candidate in paths[1:]:
        while not candidate.resolve().is_relative_to(common):
            common = common.parent
    return common
