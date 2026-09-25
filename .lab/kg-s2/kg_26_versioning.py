"""Semver parsing and comparison."""
from __future__ import annotations

import re
from functools import total_ordering

PATTERN = re.compile(
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+(?P<build>[0-9A-Za-z.-]+))?"
)


@total_ordering
class Version:
    def __init__(self, text: str) -> None:
        match = PATTERN.fullmatch(text.strip())
        if match is None:
            raise ValueError(f"invalid semantic version: {text!r}")
        self.major = int(match["major"])
        self.minor = int(match["minor"])
        self.patch = int(match["patch"])
        self.pre = match["pre"]

    def _tuple(self) -> tuple[int, int, int, bool, str]:
        return (self.major, self.minor, self.patch, self.pre is None, self.pre or "")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._tuple() == other._tuple()

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._tuple() < other._tuple()

    def __repr__(self) -> str:
        return f"Version({self.major}.{self.minor}.{self.patch})"
