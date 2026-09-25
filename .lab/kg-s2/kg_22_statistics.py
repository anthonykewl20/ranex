"""Small numeric summaries without external deps."""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("values must not be empty")
    return sum(values) / len(values)


def variance(values: Sequence[float]) -> float:
    mu = mean(values)
    return sum((v - mu) ** 2 for v in values) / len(values)


def median(values: Iterable[float]) -> float:
    ordered = sorted(values)
    count = len(ordered)
    if count == 0:
        raise ValueError("values must not be empty")
    middle = count // 2
    if count % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return math.nan
    return numerator / denominator
