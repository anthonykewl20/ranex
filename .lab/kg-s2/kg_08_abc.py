"""Abstract payment gateway contract."""
from __future__ import annotations

import abc
import decimal


class PaymentGateway(abc.ABC):
    @abc.abstractmethod
    def charge(self, amount: decimal.Decimal, token: str) -> str: ...

    @abc.abstractmethod
    def refund(self, transaction_id: str, amount: decimal.Decimal) -> bool: ...


class InMemoryGateway(PaymentGateway):
    def __init__(self) -> None:
        self._ledger: dict[str, decimal.Decimal] = {}
        self._counter = 0

    def charge(self, amount: decimal.Decimal, token: str) -> str:
        self._counter += 1
        transaction_id = f"txn-{self._counter}"
        self._ledger[transaction_id] = amount
        return transaction_id

    def refund(self, transaction_id: str, amount: decimal.Decimal) -> bool:
        charged = self._ledger.get(transaction_id)
        if charged is None or amount > charged:
            return False
        self._ledger[transaction_id] = charged - amount
        return True
