"""Plant l5: bare except clause (ruff E722)."""
from __future__ import annotations


def parse(text: str) -> int | None:
    try:
        return int(text)
    except:
        return None


def main() -> None:
    print(parse("7"))


if __name__ == "__main__":
    main()
