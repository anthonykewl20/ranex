"""Represent dependency approval changes and bind them to an exact target."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass

from ranex.foundation.canonical import canonical_sha256
from ranex.provisioning.lockfile import TargetEnvironment


@dataclass(frozen=True, slots=True)
class DepsDelta:
    baseline_exists: bool
    added: tuple[tuple[str, str], ...]
    removed: tuple[tuple[str, str], ...]
    changed: tuple[tuple[str, str, str], ...]


def package_delta(previous: Mapping[str, str] | None, current: Mapping[str, str]) -> DepsDelta:
    """Report every package difference; a missing baseline is intentionally visible."""
    if previous is None:
        return DepsDelta(False, tuple(sorted(current.items())), (), ())
    added = tuple(sorted((name, version) for name, version in current.items() if name not in previous))
    removed = tuple(sorted((name, version) for name, version in previous.items() if name not in current))
    changed = tuple(sorted((name, previous[name], version) for name, version in current.items() if name in previous and previous[name] != version))
    return DepsDelta(True, added, removed, changed)


def depset_digest(lock_bytes: bytes, target: TargetEnvironment) -> str:
    """Bind the lock bytes and every target selector into one stable digest."""
    payload = {
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "implementation": target.implementation,
        "python_version": list(target.python_version),
        "platforms": list(target.platforms),
        "marker_environment": dict(target.marker_environment),
    }
    return "sha256:" + canonical_sha256(payload)
