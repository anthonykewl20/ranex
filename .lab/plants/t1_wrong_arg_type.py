"""Plant t1: call passes an int where str is required (pyrefly must fail)."""
from __future__ import annotations


def greet(name: str) -> str:
    return f"hello {name}"


def main() -> None:
    message = greet(42)
    print(message)


if __name__ == "__main__":
    main()
