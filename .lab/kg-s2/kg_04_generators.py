"""Streaming window statistics."""
from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence


def sliding_windows(values: Sequence[int], width: int) -> Iterator[tuple[int, ...]]:
    if width < 1:
        raise ValueError("width must be >= 1")
    for start in range(len(values) - width + 1):
        yield tuple(values[start : start + width])


def running_means(chunks: Iterable[Sequence[float]]) -> Iterator[float]:
    total = 0.0
    count = 0
    for chunk in chunks:
        for value in chunk:
            total += value
            count += 1
        if count:
            yield total / count


def flatten(nested: Iterable[Iterable[int]]) -> list[int]:
    return [item for inner in nested for item in inner]
