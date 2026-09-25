"""Plant t2: use of a name that is never defined (pyrefly + ruff F821)."""
from __future__ import annotations


def main() -> None:
    total = SHIFT_COUNT * 2
    print(total)


if __name__ == "__main__":
    main()
