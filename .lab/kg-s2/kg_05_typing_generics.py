"""A typed registry with bounded lookup."""
from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class Registry(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[str, T] = {}
        self._factories: dict[str, Callable[[], T]] = {}

    def register(self, name: str, item: T) -> None:
        if name in self._items:
            raise KeyError(f"duplicate registration: {name}")
        self._items[name] = item

    def register_factory(self, name: str, factory: Callable[[], T]) -> None:
        self._factories[name] = factory

    def get(self, name: str) -> T | None:
        if name in self._items:
            return self._items[name]
        factory = self._factories.get(name)
        if factory is None:
            return None
        item = factory()
        self._items[name] = item
        return item

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._items))
