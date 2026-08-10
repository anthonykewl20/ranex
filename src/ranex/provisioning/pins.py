"""Load operator pins and refuse resolver binaries that cannot be verified."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ranex.cli.toolchain import ToolchainError, refuse_writable_executable
from ranex.provisioning.errors import ProvisioningError


class PinsError(ProvisioningError):
    """A required provisioning pin is absent, malformed, or unsafe."""


_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True, slots=True)
class ResolutionPins:
    resolver: Path
    resolver_sha256: str
    python: Path
    indexes: tuple[str, ...]
    exclude_newer: str


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PinsError(f"pins field {name!r} must be a mapping")
    return value


def _absolute_path(value: Any, name: str) -> Path:
    if not isinstance(value, str) or not value:
        raise PinsError(f"pins field {name!r} must be a non-empty absolute path")
    path = Path(value)
    if not path.is_absolute():
        raise PinsError(f"pins field {name!r} must be an absolute path: {path}")
    return path


def load_pins_text(text: str) -> ResolutionPins:
    """Parse a complete pins document; omission is never filled by defaults."""
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise PinsError(f"cannot parse pins YAML: {exc}") from exc
    data = _mapping(loaded, "document")
    resolver = _mapping(data.get("resolver"), "resolver")
    python = _mapping(data.get("python"), "python")
    resolver_path = _absolute_path(resolver.get("path"), "resolver.path")
    python_path = _absolute_path(python.get("path"), "python.path")
    digest = resolver.get("sha256")
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise PinsError("pins field 'resolver.sha256' must be 64 lowercase hex")
    indexes = data.get("indexes")
    if not isinstance(indexes, list) or not indexes or any(
        not isinstance(index, str) or not index for index in indexes
    ):
        raise PinsError("pins field 'indexes' must be a non-empty list of strings")
    exclude_newer = data.get("exclude_newer")
    if not isinstance(exclude_newer, str) or not exclude_newer:
        raise PinsError("pins field 'exclude_newer' must be a non-empty string")
    return ResolutionPins(
        resolver=resolver_path,
        resolver_sha256=digest,
        python=python_path,
        indexes=tuple(indexes),
        exclude_newer=exclude_newer,
    )


def refuse_writable_interpreter(path: Path) -> None:
    """The pinned interpreter obeys the same rule as the pinned resolver.

    It has no digest pin — its identity is answered by the probe it runs —
    but a user-writable interpreter lets the observed party rewrite the
    selection and the runtime in one move, so the toolchain's writability
    rule applies unchanged.
    """

    try:
        refuse_writable_executable(path)
    except ToolchainError as exc:
        raise PinsError(f"pinned interpreter {path} is writable: {exc}") from exc


def verified_pinned_binary(
    path: Path, expected_sha256: str, require_unwritable: bool = True
) -> int:
    """Return an open descriptor only after hashing the exact descriptor bytes."""
    if not _SHA256.fullmatch(expected_sha256):
        raise PinsError(f"pinned resolver {path} has malformed expected sha256")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PinsError(f"cannot open pinned resolver {path}: {exc}") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise PinsError(f"pinned resolver {path} is not a regular file")
        if require_unwritable:
            try:
                refuse_writable_executable(path)
            except ToolchainError as exc:
                raise PinsError(f"pinned resolver {path} is writable: {exc}") from exc
        digest = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            raise PinsError(f"pinned resolver {path} sha256 does not match")
        os.lseek(descriptor, 0, os.SEEK_SET)
        return descriptor
    except Exception:
        os.close(descriptor)
        raise
