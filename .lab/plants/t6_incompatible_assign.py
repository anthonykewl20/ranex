"""Plant t6: assignment of an incompatible type to an annotated variable."""
from __future__ import annotations

import pathlib

TARGET: pathlib.Path = "output/results.json"


def main() -> None:
    print(TARGET)


if __name__ == "__main__":
    main()
