"""Plant t3: function returns a value violating its annotation."""
from __future__ import annotations


def page_count(report: str) -> int:
    if not report:
        return 0
    return len(report) / 1800


def main() -> None:
    print(page_count("body" * 100))


if __name__ == "__main__":
    main()
