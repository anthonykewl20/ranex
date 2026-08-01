from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
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


def command_digest(argv: Sequence[str]) -> str:
    """The digest a claim is bound to, over the argv that satisfies it.

    Lives here, once, because the catalog and `run` are in different layers and
    both must produce the same bytes for the same argv. A second encoding
    anywhere between them would make every binding unsatisfiable while looking
    correct in both files.

    Over the argv list rather than a joined string: comparison then needs no
    shell parsing, and argument order is inside the digest, so `pytest -q tests`
    and `pytest tests -q` are two commands and two digests.
    """

    return "sha256:" + canonical_sha256(list(argv))
