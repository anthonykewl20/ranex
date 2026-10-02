"""Immutable platform ABI facts selected only from the running machine."""

import platform
import sys
from dataclasses import dataclass
from types import MappingProxyType


class PlatformUnsupported(RuntimeError):
    """The running OS and architecture have no supported ABI table."""


@dataclass(frozen=True)
class PlatformFacts:
    execveat: int
    keyctl: int
    openat2: int
    landlock_create_ruleset: int
    target_triple: str
    loader_name: str
    loader_path: str


PLATFORMS = MappingProxyType({
    ("linux", "x86_64"): PlatformFacts(
        execveat=322,
        keyctl=250,
        openat2=437,
        landlock_create_ruleset=444,
        target_triple="x86_64-linux-gnu",
        loader_name="ld-linux-x86-64.so.2",
        loader_path="/lib64/ld-linux-x86-64.so.2",
    ),
})


def current() -> PlatformFacts:
    """Return the running platform's facts, refusing unsupported platforms."""
    machine = platform.machine().strip().lower()
    try:
        return PLATFORMS[(sys.platform, machine)]
    except KeyError:
        raise PlatformUnsupported(
            f"Unsupported platform: os={sys.platform} machine={machine}"
        ) from None
