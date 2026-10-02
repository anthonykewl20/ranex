"""Host-capability limitation checks against a temporary build manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from launcher_host import build_closure_limitation


def _write_manifest(tmp_path: Path, path: Path, sha256: str) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"build": {"inputs": [{"path": str(path), "sha256": sha256}]}}
        ),
        encoding="utf-8",
    )
    return manifest_path


def test_wrong_sha256_returns_reason(tmp_path: Path) -> None:
    input_file = tmp_path / "input.c"
    input_file.write_bytes(b"payload")
    manifest_path = _write_manifest(
        tmp_path, input_file, hashlib.sha256(b"other").hexdigest()
    )
    reason = build_closure_limitation(manifest_path)
    assert isinstance(reason, str)
    assert str(input_file) in reason


def test_absent_input_returns_reason(tmp_path: Path) -> None:
    absent = tmp_path / "absent.c"
    manifest_path = _write_manifest(
        tmp_path, absent, hashlib.sha256(b"payload").hexdigest()
    )
    reason = build_closure_limitation(manifest_path)
    assert isinstance(reason, str)
    assert str(absent) in reason


def test_matching_entries_return_none(tmp_path: Path) -> None:
    input_file = tmp_path / "input.c"
    input_file.write_bytes(b"payload")
    manifest_path = _write_manifest(
        tmp_path, input_file, hashlib.sha256(b"payload").hexdigest()
    )
    assert build_closure_limitation(manifest_path) is None
