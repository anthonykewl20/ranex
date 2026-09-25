"""CLI for reversing files line by line."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="reverse file lines")
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--suffix", default=".rev")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def reverse_file(source: Path, suffix: str, dry_run: bool) -> Path:
    lines = source.read_text(encoding="utf-8").splitlines()
    target = source.with_name(f"{source.name}{suffix}")
    if not dry_run:
        target.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    for source in args.sources:
        target = reverse_file(source, args.suffix, args.dry_run)
        print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
