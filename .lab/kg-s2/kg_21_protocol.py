"""Protocols for pluggable storage."""
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable


@runtime_checkable
class KVStore(Protocol):
    def get(self, key: str) -> str | None: ...
    def put(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> bool: ...


class MemoryStore:
    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def put(self, key: str, value: str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None


def bulk_load(store: KVStore, pairs: Sequence[tuple[str, str]]) -> int:
    loaded = 0
    for key, value in pairs:
        store.put(key, value)
        loaded += 1
    return loaded


def accepts_store(candidate: object) -> bool:
    return isinstance(candidate, KVStore)
