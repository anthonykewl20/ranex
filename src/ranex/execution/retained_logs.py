"""Durable, redacted retention of execution-stream logs."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path

from ranex.execution.log_redaction import redact_text
from ranex.foundation.atomic_writer import write_atomic
from ranex.foundation.canonical import canonical_json_bytes

DEFAULT_LOG_MAX_BYTES: int = 262_144
MIN_LOG_MAX_BYTES: int = 4_096
MAX_LOG_MAX_BYTES: int = 8_388_608
EMPTY_STREAM_SHA256: str = "sha256:" + hashlib.sha256(b"").hexdigest()


def log_dir_for_outcome(outcome: Path) -> Path:
    """Return the sidecar directory reserved for an outcome's retained logs."""

    return outcome.with_name(outcome.name + ".logs")


def validate_max_bytes(value: int) -> int:
    """Validate the retained-log byte cap."""

    if MIN_LOG_MAX_BYTES <= value <= MAX_LOG_MAX_BYTES:
        return value
    raise ValueError("--log-max-bytes must be between 4096 and 8388608 bytes")


def decode_stream(data: bytes | str | None) -> str:
    """Decode a captured process stream without losing malformed-byte evidence."""

    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")


def truncate_tail(text: str, max_bytes: int) -> tuple[str, bool, int, int]:
    """Retain a UTF-8-safe tail, prefixed with an exact final-size marker."""

    encoded = text.encode("utf-8")
    original_bytes = len(encoded)
    if original_bytes <= max_bytes:
        return text, False, original_bytes, original_bytes
    if max_bytes <= 0:
        return "", True, 0, original_bytes

    marker_lengths = _marker_lengths(original_bytes, max_bytes)
    retained_candidates: list[tuple[bytes, bytes]] = []
    for reservation in {
        marker_length + extra_bytes
        for marker_length in marker_lengths
        for extra_bytes in range(4)
    }:
        if reservation > max_bytes:
            continue
        retained_tail = _utf8_tail(encoded, max_bytes - reservation)
        for marker_length in marker_lengths:
            retained_bytes = marker_length + len(retained_tail)
            marker = _truncation_marker(original_bytes, retained_bytes)
            if len(marker) == marker_length and retained_bytes <= max_bytes:
                retained_candidates.append((marker, retained_tail))

    if not retained_candidates:
        return "", True, 0, original_bytes

    marker, retained_tail = max(
        retained_candidates,
        key=lambda candidate: len(candidate[0]) + len(candidate[1]),
    )
    retained_bytes = len(marker) + len(retained_tail)
    retained_text = marker.decode("ascii") + retained_tail.decode("utf-8")
    return retained_text, True, retained_bytes, original_bytes


def persist_stream(
    directory: Path,
    name: str,
    text: str,
    *,
    literals: Sequence[tuple[str, str]],
    max_bytes: int,
) -> dict[str, object]:
    """Redact, retain, and atomically publish one named execution stream."""

    redacted, redactions = redact_text(text, literals)
    retained_text, truncated, retained_bytes, original_bytes = truncate_tail(redacted, max_bytes)
    data = retained_text.encode("utf-8")
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{name}.log"
    write_atomic(directory / filename, data, root=directory)
    return {
        "file": filename,
        "bytes": retained_bytes,
        "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
        "original_bytes": original_bytes,
        "truncated": truncated,
        "redactions": redactions,
    }


def write_log_manifest(
    directory: Path,
    streams: Mapping[str, Mapping[str, object]],
    policy: Mapping[str, object],
) -> None:
    """Atomically publish the canonical manifest for retained execution streams."""

    manifest: dict[str, object] = {
        "version": 1,
        "policy": dict(policy),
        "streams": dict(streams),
    }
    write_atomic(
        directory / "manifest.json",
        canonical_json_bytes(manifest) + b"\n",
        root=directory,
    )


def _truncation_marker(original_bytes: int, retained_bytes: int) -> bytes:
    """Format the ASCII marker whose values describe the final retained file."""

    dropped_bytes = original_bytes - retained_bytes
    return (
        f"[ranex truncated: policy=tail dropped={dropped_bytes} retained={retained_bytes} "
        f"original={original_bytes}]\n"
    ).encode("ascii")


def _utf8_tail(data: bytes, max_bytes: int) -> bytes:
    """Return at most ``max_bytes`` from the tail at a UTF-8 character boundary."""

    if max_bytes <= 0:
        return b""
    return data[-max_bytes:].decode("utf-8", errors="ignore").encode("utf-8")


def _marker_lengths(original_bytes: int, max_bytes: int) -> set[int]:
    """Return all marker lengths possible from the relevant decimal digit widths."""

    fixed_bytes = len(_truncation_marker(0, 0)) - 3
    original_digits = len(str(original_bytes))
    retained_digits = len(str(min(original_bytes, max_bytes)))
    return {
        fixed_bytes + dropped_digits + retained_digits_value + original_digits
        for dropped_digits in range(1, original_digits + 1)
        for retained_digits_value in range(1, retained_digits + 1)
    }
