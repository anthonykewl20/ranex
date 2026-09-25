'"""Pairing and chunking helpers."""'
from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator, Sequence


def chunked(values: Sequence[int], size: int) -> Iterator[list[int]]:
    if size < 1:
        raise ValueError("size must be >= 1")
    for start in range(0, len(values), size):
        yield list(values[start : start + size])


def pairwise_round_robin(a: Iterable[str], b: Iterable[str]) -> Iterator[tuple[str, str]]:
    return zip(itertools.cycle(a), b)


def dedupe_stable(values: Iterable[int]) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
