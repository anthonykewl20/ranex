"""Token budget tracker with __slots__."""
from __future__ import annotations


class BudgetTracker:
    __slots__ = ("_capacity", "_used")

    def __init__(self, capacity: int) -> None:
        if capacity < 0:
            raise ValueError("capacity must be non-negative")
        self._capacity = capacity
        self._used = 0

    @property
    def remaining(self) -> int:
        return self._capacity - self._used

    def spend(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("amount must be non-negative")
        if amount > self.remaining:
            raise RuntimeError("budget exhausted")
        self._used += amount
        return self.remaining

    def refund(self, amount: int) -> int:
        self._used = max(0, self._used - amount)
        return self.remaining
