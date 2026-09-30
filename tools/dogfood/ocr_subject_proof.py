#!/usr/bin/env python3
"""#105 field proof — govern open-code-review as a SARIF claim subject.

Arm 0: admit the pinned OCR Go binary as a runtime-v3 ELF ``entrypoint``.
OCR v1.12.9 ships a self-contained static ``ET_EXEC`` (no ``PT_INTERP``).
v3 requires ``entrypoint.pt_interp == loader.self_id`` (ADR-035 /
``parse_runtime_manifest``), so honest admission of the real bytes is refused.
static-v2 admits the same bytes (contrast only — not Arm 0).

Issue protocol: when Arm 0 v3 refuses, arms 1–4 are UNVERIFIED (not skipped).

    uv run --frozen python tools/dogfood/ocr_subject_proof.py \\
        --out tools/dogfood/audits/2026-09-30-ocr-subject

No mocks. Real release bytes, real checksum, real ``parse_runtime_manifest``
and ``inspect_self_contained_static_executable``. ``KERNEL_DIGEST`` untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

DOGFOOD = Path(__file__).resolve().parent
REPOSITORY = DOGFOOD.parents[1]
sys.path[:0] = [str(REPOSITORY / "src")]

from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402
from ranex.foundation.dynamic_runtime import parse_runtime_manifest  # noqa: E402
from ranex.foundation.static_executable import (  # noqa: E402
    inspect_self_contained_static_executable,
)

OCR_TAG = "v1.12.9"
OCR_COMMIT_FLOOR = "14b84f08a3af7f042d702c721f21f7952d841970"
OCR_ASSET = "opencodereview-linux-amd64"
# sha256sum.txt from the v1.12.9 release (retained).
OCR_SHA256 = "9105c7081b8362a1cb0167f1ddfd1437e147a0e3c9a5af89c03c8859a5b0f0e8"
OCR_URL = (
    "https://github.com/alibaba/open-code-review/releases/download/"
    f"{OCR_TAG}/{OCR_ASSET}"
)
CHECKSUMS_URL = (
    "https://github.com/alibaba/open-code-review/releases/download/"
    f"{OCR_TAG}/sha256sum.txt"
)
CACHE = Path.home() / ".cache" / "ranex" / "ocr" / OCR_TAG / OCR_ASSET
FIXTURE_CLOSURE = (
    REPOSITORY / "tests" / "e2e" / "fixtures" / "slice072-runtime" / "closure.json"
)


def _record(
    out: Path,
    name: str,
    *,
    status: str,
    argv: list[str],
    cwd: str,
    exit_code: int,
    digests: dict[str, str],
    notes: str,
    wall_ms: int | None = None,
) -> None:
    payload: dict[str, object] = {
        "expectation": name,
        "status": status,
        "argv": argv,
        "cwd": cwd,
        "exit_code": exit_code,
        "digests": digests,
        "notes": notes,
    }
    if wall_ms is not None:
        payload["wall_ms"] = wall_ms
    (out / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _fetch_ocr(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest == OCR_SHA256:
            return destination
        destination.unlink()
    print(f"fetching {OCR_URL}", file=sys.stderr)
    with urllib.request.urlopen(OCR_URL, timeout=120) as response:  # noqa: S310
        destination.write_bytes(response.read())
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if digest != OCR_SHA256:
        raise SystemExit(f"OCR checksum mismatch: got {digest}, want {OCR_SHA256}")
    destination.chmod(0o755)
    checksums = destination.parent / "sha256sum.txt"
    with urllib.request.urlopen(CHECKSUMS_URL, timeout=60) as response:  # noqa: S310
        checksums.write_bytes(response.read())
    return destination


def _ocr_elf_facts(binary: Path) -> dict[str, object]:
    from elftools.elf.elffile import ELFFile

    payload = binary.read_bytes()
    elf = ELFFile(__import__("io").BytesIO(payload))
    interp = None
    for segment in elf.iter_segments():
        if segment["p_type"] == "PT_INTERP":
            interp = segment.get_interp_name()
    return {
        "e_type": elf.header["e_type"],
        "pt_interp": interp,
        "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }


def _honest_ocr_closure(ocr_digest: str) -> bytes:
    """A v3 closure that names OCR as entrypoint with its real (null) interp."""

    base = json.loads(FIXTURE_CLOSURE.read_bytes())
    loader_self = base["loader"]["self_id"]
    assert loader_self == "/lib64/ld-linux-x86-64.so.2"
    base["entrypoint"] = {
        "path": "bin/opencodereview",
        "pt_interp": None,
        "sha256": ocr_digest,
    }
    files = []
    for row in base["files"]:
        if row["kind"] == "entrypoint":
            files.append(
                {
                    "path": "bin/opencodereview",
                    "mode": "0555",
                    "kind": "entrypoint",
                    "sha256": ocr_digest,
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


def arm0_v3_admission(out: Path, binary: Path, *, repeats: int) -> str:
    facts = _ocr_elf_facts(binary)
    ocr_digest = str(facts["sha256"])
    reasons: list[str] = []
    started = time.monotonic()
    for _ in range(repeats):
        raw = _honest_ocr_closure(ocr_digest)
        try:
            parse_runtime_manifest(raw)
            reasons.append("ADMITTED")
        except ValueError as exc:
            reasons.append(str(exc))
    wall_ms = int((time.monotonic() - started) * 1000)

    fd = os.open(binary, os.O_RDONLY | os.O_CLOEXEC)
    try:
        inspect_self_contained_static_executable(fd, binary)
        static_status = "ADMITTED"
    except ValueError as exc:
        static_status = f"REFUSED:{exc}"
    finally:
        os.close(fd)

    unique = sorted(set(reasons))
    refused = unique == ["loader or entrypoint binding"]
    status = "VERIFIED" if refused and facts["pt_interp"] is None else "FALSE-PASS"
    if static_status != "ADMITTED":
        status = "GAP"
    digests = {
        "ocr_sha256": ocr_digest,
        "release_pin": OCR_SHA256,
        "closure_attempt": "sha256:"
        + hashlib.sha256(_honest_ocr_closure(ocr_digest)).hexdigest(),
        "refusal_reason": "sha256:"
        + hashlib.sha256(reasons[0].encode()).hexdigest(),
    }
    _record(
        out,
        "arm0-v3-entrypoint-admission",
        status=status,
        argv=["parse_runtime_manifest", "honest-ocr-closure"],
        cwd=str(binary.parent),
        exit_code=0 if status == "VERIFIED" else 1,
        digests=digests,
        notes=(
            f"pin={OCR_TAG} floor={OCR_COMMIT_FLOOR} asset={OCR_ASSET} "
            f"elf={facts['e_type']} pt_interp={facts['pt_interp']!r} "
            f"static_v2={static_status} v3_reasons={unique} repeats={repeats} "
            "findings stay ADVISORY (never required_claims)."
        ),
        wall_ms=wall_ms,
    )
    pin = {
        "tool": "alibaba/open-code-review",
        "tag": OCR_TAG,
        "commit_floor": OCR_COMMIT_FLOOR,
        "asset": OCR_ASSET,
        "sha256": OCR_SHA256,
        "url": OCR_URL,
        "checksums_url": CHECKSUMS_URL,
        "observed_sha256": ocr_digest.removeprefix("sha256:"),
        "elf": facts,
        "static_v2": static_status,
        "v3_admission": "REFUSED" if refused else "UNEXPECTED",
        "v3_refusal": unique[0] if unique else None,
    }
    (out / "ocr-pin.json").write_text(
        json.dumps(pin, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return status


def _unverified(out: Path, name: str, reason: str) -> None:
    _record(
        out,
        name,
        status="UNVERIFIED",
        argv=[],
        cwd=str(out),
        exit_code=0,
        digests={},
        notes=reason,
    )


def arm3_delegate_probe(out: Path, binary: Path) -> None:
    """Measure ``ocr delegate`` offline; still UNVERIFIED for #105 subject path."""

    with tempfile.TemporaryDirectory(prefix="ranex-105-delegate-") as tmp:
        root = Path(tmp)
        subprocess.run(
            ["git", "init"], cwd=root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", "ocr-subject@ranex.local"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "ocr-subject"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        (root / "pkg").mkdir()
        (root / "pkg" / "mod.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "."], cwd=root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "seed"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        base = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        (root / "pkg" / "mod.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "pkg/mod.py"], cwd=root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "change"],
            cwd=root,
            check=True,
            capture_output=True,
        )
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(root)}
        argv = [
            str(binary),
            "delegate",
            "preview",
            "--format",
            "json",
            "--from",
            base,
            "--to",
            head,
        ]
        digests: list[str] = []
        exit_codes: list[int] = []
        for _ in range(3):
            completed = subprocess.run(
                argv,
                cwd=root,
                env=env,
                capture_output=True,
                check=False,
            )
            exit_codes.append(completed.returncode)
            digests.append(hashlib.sha256(completed.stdout).hexdigest())
        stable = len(set(digests)) == 1 and set(exit_codes) == {0}
        _record(
            out,
            "arm3-ocr-delegate-advisory",
            status="UNVERIFIED",
            argv=argv,
            cwd=str(root),
            exit_code=exit_codes[0] if exit_codes else 1,
            digests={"stdout": "sha256:" + digests[0]} if digests else {},
            notes=(
                "v3 Arm 0 refused; arm 3 stays UNVERIFIED per issue protocol. "
                f"offline delegate probe stable={stable} exits={exit_codes} "
                f"unique_digests={len(set(digests))}; findings remain ADVISORY "
                "never required_claims (#102 / ADR-069)."
            ),
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--ocr-binary",
        type=Path,
        default=None,
        help="Pinned OCR binary; default downloads v1.12.9 into the cache",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    host = {
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
    }
    (args.out / "host.json").write_text(
        json.dumps(host, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    binary = _fetch_ocr(Path(args.ocr_binary or CACHE))

    statuses: dict[str, str] = {}
    statuses["arm0-v3-entrypoint-admission"] = arm0_v3_admission(
        args.out, binary, repeats=args.repeats
    )

    blocked = (
        "Arm 0 v3 entrypoint admission REFUSED for static OCR Go binary "
        f"(pin {OCR_TAG} sha256={OCR_SHA256}); issue protocol marks this arm "
        "UNVERIFIED (not skipped). static-v2 would admit the same bytes but "
        "is not the named Arm 0 path."
    )
    for name in (
        "arm1-offline-key-unset",
        "arm2-offline-key-set-strict-local",
        "arm4-live-probe-pr",
        "arm5-repeats-identical-fail-digests",
    ):
        _unverified(args.out, name, blocked)
        statuses[name] = "UNVERIFIED"

    arm3_delegate_probe(args.out, binary)
    statuses["arm3-ocr-delegate-advisory"] = "UNVERIFIED"

    summary = {
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": host["hostname"],
        "issue": 105,
        "ocr_tag": OCR_TAG,
        "ocr_sha256": OCR_SHA256,
        "repeats": args.repeats,
        "statuses": statuses,
        "kernel_digest_moved": False,
        "findings_advisory": True,
        "required_claims_include_ocr": False,
    }
    (args.out / "SUMMARY.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    cached_sums = binary.parent / "sha256sum.txt"
    if cached_sums.is_file():
        shutil.copy2(cached_sums, args.out / "sha256sum.txt")

    print(json.dumps(statuses, indent=2, sort_keys=True))
    return 0 if statuses["arm0-v3-entrypoint-admission"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
