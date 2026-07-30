from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return stable compact JSON suitable for hashing kernel records."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def canonical_json_bytes(value: Any) -> bytes:
    """Return the UTF-8 bytes of the canonical JSON representation."""
    return canonical_json(value).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    """Return lowercase SHA-256 hex over the canonical JSON bytes."""
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
