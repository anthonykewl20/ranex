"""Natural-sort key for version-ish strings."""
from __future__ import annotations

import re
from functools import cmp_to_key

_CHUNK = re.compile(r"(\d+|\D+)")


def _compare(a: str, b: str) -> int:
    if a == b:
        return 0
    if a.isdigit() and b.isdigit():
        return -1 if int(a) < int(b) else 1
    return -1 if a < b else 1


def natural_key(value: str) -> list[str]:
    return _CHUNK.findall(value)


def natural_sorted(values: list[str]) -> list[str]:
    def compare(x: str, y: str) -> int:
        xs, ys = natural_key(x), natural_key(y)
        for a, b in zip(xs, ys):
            outcome = _compare(a, b)
            if outcome:
                return outcome
        return len(xs) - len(ys)

    return sorted(values, key=cmp_to_key(compare))
