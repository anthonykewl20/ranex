"""Plant t4: attribute access impossible on the declared union."""
from __future__ import annotations

import datetime


def describe(when: datetime.date | None) -> str:
    return when.isoformat() + "Z"


def main() -> None:
    print(describe(datetime.date(2026, 1, 1)))


if __name__ == "__main__":
    main()
