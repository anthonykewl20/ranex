"""Read-write lock on a threading condition."""
from __future__ import annotations

import threading


class ReadWriteLock:
    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._readers = 0
        self._writer = False

    def read_acquire(self) -> None:
        with self._condition:
            while self._writer:
                self._condition.wait()
            self._readers += 1

    def read_release(self) -> None:
        with self._condition:
            self._readers -= 1
            if self._readers == 0:
                self._condition.notify_all()

    def write_acquire(self) -> None:
        with self._condition:
            while self._writer or self._readers:
                self._condition.wait()
            self._writer = True

    def write_release(self) -> None:
        with self._condition:
            self._writer = False
            self._condition.notify_all()
