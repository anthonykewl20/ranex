"""Deadline propagation helpers."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class Deadline:
    _unix: float

    @classmethod
    def after(cls, seconds: float) -> Deadline:
        if seconds < 0:
            raise ValueError("seconds must be non-negative")
        return cls(time.monotonic() + seconds)

    def remaining(self) -> float:
        return max(0.0, self._unix - time.monotonic())

    def expired(self) -> bool:
        return self.remaining() <= 0


def budget(steps: int, deadline: Deadline) -> list[float]:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    slices = [1.0 / steps] * steps
    now = deadline.remaining()
    if now <= 0:
        raise TimeoutError("deadline already expired")
    return [s * now for s in slices]
