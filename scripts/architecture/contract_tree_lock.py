#!/usr/bin/env python3
"""Repo-scoped interprocess lock for architecture-contract publication.

The generator publishes several related directories.  Serializing generators
and validators prevents a validator (or a second writer) from observing the
intentional cleanup window before the complete deterministic tree is restored.
The lock lives outside every generator-owned tree, so cleanup cannot unlink it.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO


LOCK_PROTOCOL_VERSION = "ranex-architecture-contract-tree-lock-v1"

# Emitted on stderr, once, at the moment a process discovers the lock is held
# and begins waiting for it.  The concurrency regression observes this marker
# directly instead of inferring contention from elapsed time.  A deterministic
# signal is both faster and stricter than a timing heuristic: it proves the
# process reached the lock and yielded, rather than proving only that it had
# not finished yet.
LOCK_WAIT_MARKER = "ranex-contract-tree-lock: waiting for exclusive lock"


def contract_tree_lock_path(root: Path) -> Path:
    """Return one stable lock path for all processes addressing ``root``."""

    canonical_root = root.resolve(strict=True)
    repository_key = hashlib.sha256(
        f"{LOCK_PROTOCOL_VERSION}\0{canonical_root}".encode("utf-8")
    ).hexdigest()
    lock_directory = (
        Path(tempfile.gettempdir()) / f"ranex-architecture-contract-locks-{os.getuid()}"
    )
    lock_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    return lock_directory / f"{repository_key}.lock"


@contextmanager
def contract_tree_lock(root: Path) -> Iterator[None]:
    """Exclusively serialize all reads and publications of the contract tree."""

    lock_path = contract_tree_lock_path(root)
    handle: TextIO = lock_path.open("a+", encoding="utf-8")
    try:
        try:
            fcntl.flock(
                handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB
            )
        except OSError:
            # Held by another publisher.  Announce the wait before blocking so
            # an observer learns of contention immediately rather than by
            # timing out.  This never changes who acquires the lock.
            print(LOCK_WAIT_MARKER, file=sys.stderr, flush=True)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()
