"""Unit tests for retained execution-stream logs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from ranex.execution.retained_logs import (
    EMPTY_STREAM_SHA256,
    MAX_LOG_MAX_BYTES,
    MIN_LOG_MAX_BYTES,
    decode_stream,
    log_dir_for_outcome,
    persist_stream,
    truncate_tail,
    validate_max_bytes,
    write_log_manifest,
)
from ranex.foundation.canonical import canonical_json_bytes

MARKER_PATTERN = re.compile(
    r"^\[ranex truncated: policy=tail dropped=(\d+) retained=(\d+) original=(\d+)\]\n"
)


@pytest.mark.parametrize("value", (MIN_LOG_MAX_BYTES, MAX_LOG_MAX_BYTES))
def test_validate_max_bytes_accepts_contract_boundaries(value: int) -> None:
    assert validate_max_bytes(value) == value


@pytest.mark.parametrize("value", (MIN_LOG_MAX_BYTES - 1, MAX_LOG_MAX_BYTES + 1))
def test_validate_max_bytes_rejects_outside_contract_boundaries(value: int) -> None:
    with pytest.raises(
        ValueError,
        match=r"^--log-max-bytes must be between 4096 and 8388608 bytes$",
    ):
        validate_max_bytes(value)


@pytest.mark.parametrize(
    ("outcome", "expected"),
    ((Path("T-1.json"), Path("T-1.json.logs")), (Path("outcome"), Path("outcome.logs"))),
)
def test_log_dir_for_outcome_preserves_full_outcome_name(outcome: Path, expected: Path) -> None:
    assert log_dir_for_outcome(outcome) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    ((None, ""), ("already text", "already text"), (b"snowman \xe2\x98\x83", "snowman ☃")),
)
def test_decode_stream_handles_none_text_and_bytes(data: bytes | str | None, expected: str) -> None:
    assert decode_stream(data) == expected


def test_decode_stream_replaces_invalid_utf8() -> None:
    assert decode_stream(b"before\xffafter") == "before\ufffdafter"


def test_truncate_tail_leaves_under_cap_text_unchanged() -> None:
    text = "hello ☃"

    assert truncate_tail(text, 100) == (text, False, len(text.encode()), len(text.encode()))


def test_truncate_tail_emits_final_marker_and_tail_deterministically() -> None:
    text = "head-" * 40 + "terminal failure reason"

    first = truncate_tail(text, 100)
    second = truncate_tail(text, 100)
    retained, truncated, retained_bytes, original_bytes = first
    marker = MARKER_PATTERN.match(retained)

    assert second == first
    assert truncated is True
    assert marker is not None
    dropped, stated_retained, stated_original = (int(value) for value in marker.groups())
    assert dropped + stated_retained == stated_original
    assert stated_retained == retained_bytes == len(retained.encode()) <= 100
    assert stated_original == original_bytes == len(text.encode())
    assert marker.group(0).isascii()
    assert retained.endswith(text[-(len(retained) - len(marker.group(0))) :])


def test_truncate_tail_aligns_multibyte_tail_to_utf8_boundary() -> None:
    text = "é" * 80 + "終" * 80

    retained, truncated, retained_bytes, original_bytes = truncate_tail(text, 101)
    marker = MARKER_PATTERN.match(retained)

    assert truncated is True
    assert marker is not None
    assert retained.encode().decode("utf-8") == retained
    assert retained_bytes == len(retained.encode()) <= 101
    assert original_bytes == len(text.encode())
    assert retained.endswith("終" * ((len(retained) - len(marker.group(0))) // len("終")))


def test_truncate_tail_returns_empty_when_cap_cannot_fit_a_marker() -> None:
    retained, truncated, retained_bytes, original_bytes = truncate_tail("long enough", 1)

    assert (retained, truncated, retained_bytes, original_bytes) == ("", True, 0, 11)


def test_persist_stream_redacts_before_truncation_publishes_read_only_and_replaces(
    tmp_path: Path,
) -> None:
    secret = "top-secret-value-1234"
    directory = tmp_path / "logs"
    entry = persist_stream(
        directory,
        "stderr",
        "x" * 80 + secret + " terminal failure",
        literals=(("env:SECRET", secret),),
        max_bytes=100,
    )
    target = directory / "stderr.log"
    data = target.read_bytes()

    assert secret not in data.decode()
    assert entry == {
        "file": "stderr.log",
        "bytes": len(data),
        "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
        "original_bytes": len(("x" * 80 + "[REDACTED:env:SECRET] terminal failure").encode()),
        "truncated": True,
        "redactions": {"env:SECRET": 1},
    }
    assert target.stat().st_mode & 0o777 == 0o444
    second = persist_stream(directory, "stderr", "second", literals=(), max_bytes=100)
    assert target.read_text() == "second"
    assert second["sha256"] == "sha256:" + hashlib.sha256(b"second").hexdigest()


def test_empty_stream_sha256_is_the_digest_of_empty_bytes() -> None:
    assert EMPTY_STREAM_SHA256 == "sha256:" + hashlib.sha256(b"").hexdigest()


def test_write_log_manifest_writes_canonical_read_only_json(tmp_path: Path) -> None:
    directory = tmp_path / "logs"
    directory.mkdir()
    streams = {"stdout": {"file": "stdout.log", "bytes": 4}}
    policy = {"max_bytes": 4096, "mode": "tail"}
    manifest = {"version": 1, "policy": policy, "streams": streams}

    write_log_manifest(directory, streams, policy)

    target = directory / "manifest.json"
    assert json.loads(target.read_text()) == manifest
    assert target.read_bytes() == canonical_json_bytes(manifest) + b"\n"
    assert target.stat().st_mode & 0o777 == 0o444


def test_persisting_three_streams_and_manifest_lists_every_entry(tmp_path: Path) -> None:
    directory = tmp_path / "T-1.json.logs"
    streams = {
        name: persist_stream(directory, name, text, literals=(), max_bytes=100)
        for name, text in {"stdout": "out", "stderr": "err", "combined": "both"}.items()
    }
    write_log_manifest(directory, streams, {"max_bytes": 100, "retention": "tail"})

    manifest = json.loads((directory / "manifest.json").read_text())
    assert set(manifest["streams"]) == {"stdout", "stderr", "combined"}
    assert manifest["streams"] == streams
