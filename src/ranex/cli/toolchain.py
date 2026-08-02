"""Resolve commands only from system directories the observed party cannot edit."""

from __future__ import annotations

import os
import stat
from collections.abc import Sequence
from pathlib import Path


class ToolchainError(Exception):
    """The pinned toolchain cannot safely answer the requested lookup."""


# `os.access` probes the real uid unless told otherwise, and every guard here is
# written against `geteuid()`. Passed as a mapping rather than a literal because
# the platform decides whether the flag exists; where it does not, the real uid
# is the only identity available and the probe is the same one it always was.
_EFFECTIVE_IDS = (
    {"effective_ids": True} if os.access in os.supports_effective_ids else {}
)


DEFAULT_DIRECTORIES: tuple[Path, ...] = (
    Path("/usr/bin"),
    Path("/bin"),
    Path("/usr/sbin"),
    Path("/sbin"),
)


def _components(path: Path) -> tuple[Path, ...]:
    """Existing directory components walked by a lookup through ``path``."""

    absolute = path.absolute()
    current = Path(absolute.anchor)
    walked = [current]
    for component in absolute.parts[1:]:
        current = current / component
        walked.append(current)
    return tuple(walked)


def _refuse_writable(directory: Path, offending: Path) -> None:
    try:
        mode = stat.S_IMODE(directory.stat().st_mode)
    except OSError as exc:
        raise ToolchainError(
            f"cannot inspect pinned toolchain directory {offending}: {exc}"
        ) from exc

    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise ToolchainError(
            f"pinned toolchain directory {offending} is reached through writable "
            f"directory {directory} (mode {oct(mode)})"
        )
    # Under euid 0 every directory answers writable. ADR-005 records that as a
    # limit of the pin rather than making root unable to use the CLI at all.
    #
    # `effective_ids` because everything else here reasons about `geteuid()`, and
    # `os.access` probes the REAL uid by default. Under setuid/setgid those are
    # different identities, so the default would test one identity and report the
    # other — and a directory writable only through the effective uid or an ACL
    # would pass. Guarded because the flag is not universal.
    if os.geteuid() != 0 and os.access(directory, os.W_OK, **_EFFECTIVE_IDS):
        raise ToolchainError(
            f"pinned toolchain directory {offending} is reached through "
            f"directory {directory}, writable by effective uid {os.geteuid()}"
        )


def refuse_writable_executable(tool: Path) -> None:
    """Refuse a binary the observed party can rewrite where it stands.

    A protected directory stops an entry being created or replaced in it. It
    says nothing about an entry that is itself writable: `/usr/bin/git` at mode
    0777 can be overwritten in place without touching `/usr/bin`, and every
    route check above would still report the pin clean. Same rule as the
    directories, for the same reason, and the same deliberate silence under
    euid 0 — where the pin cannot help and refusing would only stop legitimate
    root use.
    """

    try:
        mode = stat.S_IMODE(tool.stat().st_mode)
    except OSError as exc:
        raise ToolchainError(f"cannot inspect pinned tool {tool}: {exc}") from exc

    if mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise ToolchainError(
            f"pinned tool {tool} is writable by group or other (mode {oct(mode)}); "
            "its bytes can be replaced without touching the directory holding it"
        )
    if os.geteuid() != 0 and os.access(tool, os.W_OK, **_EFFECTIVE_IDS):
        raise ToolchainError(
            f"pinned tool {tool} is writable by effective uid {os.geteuid()}; "
            "the observed party can rewrite the binary the verdict rests on"
        )


def pinned_directories(candidates: Sequence[Path]) -> tuple[Path, ...]:
    """Return existing, resolved candidates whose complete routes are protected."""

    pinned: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if not candidate.exists():
            continue
        if not candidate.is_dir():
            raise ToolchainError(
                f"pinned toolchain directory {candidate} is not a directory"
            )

        resolved = candidate.resolve()
        # Checking the lexical route protects a symlink component from being
        # replaced; checking the resolved route protects every directory the
        # link actually selects. Either writable route lets the worker choose
        # what the supposedly pinned name means on the next invocation.
        route = (*_components(candidate), *_components(resolved))
        checked: set[Path] = set()
        for component in route:
            actual = component.resolve()
            if actual in checked:
                continue
            checked.add(actual)
            _refuse_writable(actual, candidate)

        if resolved not in seen:
            seen.add(resolved)
            pinned.append(resolved)
    return tuple(pinned)


def resolve_tool(name: str) -> Path:
    """Resolve ``name`` on the pinned toolchain, never the ambient ``PATH``."""

    if not name or Path(name).name != name:
        raise ToolchainError(f"tool name must be a single path component: {name!r}")
    for directory in pinned_directories(DEFAULT_DIRECTORIES):
        candidate = directory / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            resolved = candidate.resolve()
            # A protected directory entry may itself be a symlink. Its target
            # route must be pinned too or the worker edits the bytes through the
            # supposedly harmless destination rather than through /usr/bin.
            pinned_directories((resolved.parent,))
            # Both names, because a hardened entry can point at an unhardened
            # file. Both calls `stat`, which FOLLOWS symlinks, so when the entry
            # is a link these inspect one inode twice — the link's own mode is
            # never examined and deliberately so: on Linux a symlink is always
            # 0777 to `lstat` and `chmod` on one raises NotImplementedError, so
            # checking it would refuse every `/bin/sh -> dash` on earth while
            # proving nothing. Replacing a link means writing in its parent, and
            # that is what `pinned_directories` above already refuses.
            refuse_writable_executable(candidate)
            refuse_writable_executable(resolved)
            return resolved
    raise ToolchainError(f"tool {name!r} is absent from the pinned toolchain")


def pinned_path_value() -> str:
    """The only PATH handed to an observed command."""

    return os.pathsep.join(str(path) for path in pinned_directories(DEFAULT_DIRECTORIES))
