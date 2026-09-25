"""Plant l4: assignment of a lambda expression (ruff E731)."""
from __future__ import annotations


def main() -> None:
    double = lambda x: x * 2
    print(double(21))


if __name__ == "__main__":
    main()
