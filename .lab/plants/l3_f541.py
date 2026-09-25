"""Plant l3: f-string without any placeholder (ruff F541)."""
from __future__ import annotations


def banner(name: str) -> str:
    title = f":: report ::"
    return f"{title} {name}"


def main() -> None:
    print(banner("weekly"))


if __name__ == "__main__":
    main()
