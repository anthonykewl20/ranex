"""Inventory line items with value semantics."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LineItem:
    sku: str
    quantity: int
    unit_price_cents: int
    tags: tuple[str, ...] = ()

    @property
    def total_cents(self) -> int:
        return self.quantity * self.unit_price_cents


@dataclass
class Order:
    items: list[LineItem] = field(default_factory=list)

    def add(self, item: LineItem) -> None:
        self.items.append(item)

    def total(self) -> int:
        return sum(item.total_cents for item in self.items)


def cheap_items(orders: list[Order], ceiling: int) -> list[str]:
    return [i.sku for o in orders for i in o.items if i.unit_price_cents <= ceiling]
