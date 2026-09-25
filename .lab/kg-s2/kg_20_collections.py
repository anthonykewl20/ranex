"""Bounded LRU store built on OrderedDict."""
from __future__ import annotations

from collections import OrderedDict, Counter
from collections.abc import Hashable


class BoundedCache:
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self._capacity = capacity
        self._store: OrderedDict[str, str] = OrderedDict()

    def get(self, key: str) -> str | None:
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key: str, value: str) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        while len(self._store) > self._capacity:
            self._store.popitem(last=False)

    def keys(self) -> tuple[str, ...]:
        return tuple(self._store)


def tally(words: list[str], top: int = 5) -> list[tuple[str, int]]:
    return Counter(words).most_common(top)


def is_hashable(value: object) -> bool:
    return isinstance(value, Hashable)
