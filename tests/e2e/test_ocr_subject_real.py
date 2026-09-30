"""#105 — OCR Go binary as a v3 ELF entrypoint subject (Arm 0).

The pinned open-code-review release is a static ``ET_EXEC`` with no
``PT_INTERP``. Runtime v3 refuses an entrypoint whose ``pt_interp`` is not
the profile loader's ``self_id`` (ADR-035). This module freezes that
refusal on real OCR bytes when the binary is present, and always freezes
the structural null-interp refusal against the slice072 closure fixture.

Arms 1–4 are field-proof UNVERIFIED when Arm 0 refuses — see
``tools/dogfood/audits/2026-09-30-ocr-subject/``. Findings stay advisory.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path

import pytest
from elftools.elf.elffile import ELFFile

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.dynamic_runtime import parse_runtime_manifest
from ranex.foundation.static_executable import (
    inspect_self_contained_static_executable,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "slice072-runtime" / "closure.json"
OCR_TAG = "v1.12.9"
OCR_SHA256 = "9105c7081b8362a1cb0167f1ddfd1437e147a0e3c9a5af89c03c8859a5b0f0e8"
OCR_ASSET = "opencodereview-linux-amd64"
CACHE = Path.home() / ".cache" / "ranex" / "ocr" / OCR_TAG / OCR_ASSET


def _closure_with_null_interp_entrypoint(*, digest: str) -> bytes:
    base = json.loads(FIXTURE.read_bytes())
    base["entrypoint"] = {
        "path": "bin/opencodereview",
        "pt_interp": None,
        "sha256": digest,
    }
    files = []
    for row in base["files"]:
        if row["kind"] == "entrypoint":
            files.append(
                {
                    "path": "bin/opencodereview",
                    "mode": "0555",
                    "kind": "entrypoint",
                    "sha256": digest,
                    "elf": {
                        "abi_version": 0,
                        "audit": None,
                        "auxiliary": None,
                        "depaudit": None,
                        "elf_class": 64,
                        "endian": "little",
                        "filter": None,
                        "machine": "EM_X86_64",
                        "needed": [],
                        "osabi": "ELFOSABI_SYSV",
                        "pt_interp": None,
                        "rpath": None,
                        "runpath": None,
                        "soname": None,
                        "type": "ET_EXEC",
                    },
                }
            )
        else:
            files.append(row)
    base["files"] = files
    return canonical_json_bytes(base)


def test_v3_refuses_entrypoint_with_null_pt_interp() -> None:
    """Structural Arm 0 control: honest null interp cannot bind the loader."""

    digest = "sha256:" + "ab" * 32
    reasons = []
    for _ in range(3):
        try:
            parse_runtime_manifest(_closure_with_null_interp_entrypoint(digest=digest))
            reasons.append("ADMITTED")
        except ValueError as exc:
            reasons.append(str(exc))
    assert reasons == ["loader or entrypoint binding"] * 3


def _resolve_ocr_binary() -> Path:
    env = os.environ.get("RANEX_OCR_BINARY", "").strip()
    candidates = [Path(env)] if env else []
    candidates.append(CACHE)
    candidates.append(Path("/tmp/ocr-pin") / OCR_ASSET)
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest != OCR_SHA256:
                pytest.skip(
                    "ranex-context:ocr-pin: "
                    f"{candidate} sha256={digest} does not match pin {OCR_SHA256}"
                )
            return candidate
    pytest.skip(
        "ranex-context:ocr-pin: pinned open-code-review "
        f"{OCR_TAG} linux-amd64 absent; set RANEX_OCR_BINARY or cache at {CACHE}"
    )


def test_ocr_v1_12_9_is_static_and_refused_as_v3_entrypoint() -> None:
    """Real OCR pin: static-v2 admits; v3 entrypoint admission refuses ×3."""

    binary = _resolve_ocr_binary()
    payload = binary.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == OCR_SHA256

    elf = ELFFile(io.BytesIO(payload))
    assert elf.header["e_type"] == "ET_EXEC"
    assert not any(seg["p_type"] == "PT_INTERP" for seg in elf.iter_segments())

    fd = os.open(binary, os.O_RDONLY | os.O_CLOEXEC)
    try:
        inspect_self_contained_static_executable(fd, binary)
    finally:
        os.close(fd)

    digest = "sha256:" + OCR_SHA256
    reasons = []
    for _ in range(3):
        try:
            parse_runtime_manifest(_closure_with_null_interp_entrypoint(digest=digest))
            reasons.append("ADMITTED")
        except ValueError as exc:
            reasons.append(str(exc))
    assert reasons == ["loader or entrypoint binding"] * 3
