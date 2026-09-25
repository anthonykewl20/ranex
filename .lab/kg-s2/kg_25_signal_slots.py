"""Observer pattern with weak references."""
from __future__ import annotations

import weakref
from collections.abc import Callable


class Signal:
    def __init__(self) -> None:
        self._subscribers: list[weakref.ref[Callable[[str], None]]] = []

    def connect(self, handler: Callable[[str], None]) -> None:
        self._subscribers.append(weakref.ref(handler, self._drop))

    def _drop(self, ref: weakref.ref[Callable[[str], None]]) -> None:
        self._subscribers = [s for s in self._subscribers if s != ref]

    def emit(self, message: str) -> int:
        delivered = 0
        for ref in list(self._subscribers):
            handler = ref()
            if handler is not None:
                handler(message)
                delivered += 1
        return delivered


def announce(message: str) -> None:
    print(message.upper())
