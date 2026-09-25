"""Manifest walking over a directory tree."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def digest_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            hasher.update(block)
    return hasher.hexdigest()


def manifest(root: Path, suffix: str = ".py") -> dict[str, str]:
    entries: dict[str, str] = {}
    for path in sorted(root.rglob(f"*{suffix}")):
        if path.is_file():
            entries[str(path.relative_to(root))] = digest_file(path)
    return entries


def write_manifest(root: Path, destination: Path) -> None:
    payload = json.dumps(manifest(root), indent=1, sort_keys=True)
    destination.write_text(payload, encoding="utf-8")
