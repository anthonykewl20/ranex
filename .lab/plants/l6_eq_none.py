"""Plant l6: equality comparison against None (ruff E711)."""
from __future__ import annotations


def is_blank(value: str | None) -> bool:
    if value == None:
        return True
    return value.strip() == ""


def main() -> None:
    print(is_blank(None))


if __name__ == "__main__":
    main()
