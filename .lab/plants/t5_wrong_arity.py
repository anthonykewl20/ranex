"""Plant t5: call with the wrong number of arguments."""
from __future__ import annotations


def scale(value: float, factor: float, offset: float) -> float:
    return value * factor + offset


def main() -> None:
    print(scale(2.0, 3.0))


if __name__ == "__main__":
    main()
