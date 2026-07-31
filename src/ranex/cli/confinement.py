"""Repository confinement.

`SLICE-LANE-007` says a slice governs only the repository it is scoped to. That
is a claim until something enforces it. This is the something.

Every path argument resolves against the repository root and is refused if it is
absolute, names a remote, or lands outside the root after symlinks are followed.
"""

from __future__ import annotations

import re
from pathlib import Path

_REMOTE = re.compile(
    r"^(?:[a-z][a-z0-9+.-]*://|[^/\s]+@[^/\s]+:)",
    re.IGNORECASE,
)


def resolve_within_repository(repository_root: Path, candidate: str) -> Path:
    """Resolve `candidate` inside `repository_root`, or raise.

    Refuses before touching the filesystem where possible, and re-checks after
    resolution because a symlink can point outside a path that looked safe.
    """

    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError("path must be a non-empty string")

    if _REMOTE.match(candidate):
        raise ValueError(f"remote targets are refused: {candidate!r}")

    path = Path(candidate)
    if path.is_absolute():
        raise ValueError(f"absolute paths are refused: {candidate!r}")

    root = Path(repository_root).resolve()
    resolved = (root / path).resolve()

    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path resolves outside the repository: {candidate!r}")

    return resolved
