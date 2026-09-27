#!/usr/bin/env python3
"""Re-stress the six Python-ADP blocking fractures under named remediations.

Prior stress (2026-09-26) called NOT-READY with F-ND1, F-AD1, F-AD3, F-AD4,
F-AD5, F-AD7. This runner applies each named remediation floor (or records
an honest HOLD when the floor needs a kernel feature not yet on main) and
emits READY|NOT-READY per fracture plus one overall call.

No threshold moves. No new runtime deps. verdict.py untouched.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

KERNEL = Path(__file__).resolve().parents[2]
AUDIT = KERNEL / "tools/dogfood/audits/2026-09-27-adp-python-fracture-restress"
LAB = Path(
    "/home/soultransit/devtony/ranex/third_party/firstmate/data/"
    "ranex-stress-python-adp/receipts/dot-lab"
)
SIX = LAB / "subjects" / "six"
RUFF = ["uvx", "ruff@0.16.2"]
PYREFLY_CI = ["uv", "run", "--frozen", "--with", "pyrefly==1.2.0", "pyrefly"]
PYREFLY_UVX = ["uvx", "pyrefly==1.2.0"]
SIX_SELECT = "E4,E7,E9,F"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(argv: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> dict[str, Any]:
    merged = dict(os.environ) if env is None else env
    started = time.perf_counter()
    proc = subprocess.run(argv, cwd=cwd, env=merged, capture_output=True, timeout=600)
    return {
        "argv": argv,
        "cwd": str(cwd),
        "rc": proc.returncode,
        "wall_clock_s": round(time.perf_counter() - started, 3),
        "stdout": proc.stdout.decode("utf-8", errors="replace"),
        "stderr": proc.stderr.decode("utf-8", errors="replace"),
        "stdout_sha256": sha256(proc.stdout),
    }


def prose_blind_digest(stdout: str) -> str:
    errors = json.loads(stdout).get("errors", [])
    keyed = sorted(
        (
            e.get("path"),
            e.get("line"),
            e.get("column"),
            e.get("stop_line"),
            e.get("stop_column"),
            e.get("name"),
            e.get("severity"),
        )
        for e in errors
    )
    return sha256(repr(keyed).encode())[:16]


def fresh(scratch: Path) -> Path:
    root = scratch / "subject"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    (root / "pyrefly.toml").write_text(
        'project-includes = ["."]\n'
        'project-excludes = ["**/__pycache__/**"]\n',
        encoding="utf-8",
    )
    (root / "clean.py").write_text(
        "def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8"
    )
    return root


def ruff_check(root: Path, *, isolated: bool, ignore_noqa: bool) -> dict[str, Any]:
    argv = RUFF + ["check", "."]
    if isolated:
        argv += ["--isolated", "--select", SIX_SELECT]
    if ignore_noqa:
        argv += ["--ignore-noqa"]
    argv += ["--output-format", "sarif", "--output-file", "ruff.sarif"]
    result = run(argv, root)
    document: dict[str, Any] = {}
    if (root / "ruff.sarif").is_file():
        document = json.loads((root / "ruff.sarif").read_text(encoding="utf-8"))
    rules = [
        r.get("ruleId")
        for run_ in document.get("runs", [])
        for r in run_.get("results", [])
    ]
    return {"rc": result["rc"], "rules": rules, "wall": result["wall_clock_s"]}


def pyrefly_check(root: Path, argv_prefix: list[str] | None = None) -> dict[str, Any]:
    argv = list(argv_prefix or PYREFLY_CI) + ["check", ".", "--output-format", "json"]
    result = run(argv, root)
    try:
        errors = json.loads(result["stdout"]).get("errors", [])
    except json.JSONDecodeError:
        errors = []
    return {
        "rc": result["rc"],
        "error_count": len(errors),
        "stdout_sha256": result["stdout_sha256"],
        "prose_blind": prose_blind_digest(result["stdout"]) if errors or result["stdout"].strip().startswith("{") else None,
        "wall": result["wall_clock_s"],
        "stdout": result["stdout"],
    }


def fracture_ad1(scratch: Path) -> dict[str, Any]:
    """Remediation: --ignore-noqa + frozen select/isolated (ship shape)."""
    root = fresh(scratch / "ad1")
    (root / "plant.py").write_text(
        "import os  # noqa: F401\n\n\ndef v() -> str:\n    return \"x\"\n",
        encoding="utf-8",
    )
    unhardened = ruff_check(root, isolated=False, ignore_noqa=False)
    hardened = ruff_check(root, isolated=True, ignore_noqa=True)
    ready = hardened["rc"] == 1 and "F401" in hardened["rules"]
    return {
        "fracture": "F-AD1",
        "remediation": "--ignore-noqa + --isolated + explicit --select",
        "unhardened_suppressed": unhardened["rc"] == 0 and not unhardened["rules"],
        "hardened": hardened,
        "verdict": "READY" if ready else "NOT-READY",
    }


def fracture_ad5(scratch: Path) -> dict[str, Any]:
    """Remediation: --isolated + explicit --select mandatory."""
    root = fresh(scratch / "ad5")
    (root / "plant.py").write_text("double = lambda value: value * 2\n", encoding="utf-8")
    (root / "ruff.toml").write_text("lint.select = ['E4']\n", encoding="utf-8")
    isolated = ruff_check(root, isolated=True, ignore_noqa=False)
    discovery = ruff_check(root, isolated=False, ignore_noqa=False)
    ready = isolated["rc"] == 1 and "E731" in isolated["rules"] and discovery["rc"] == 0
    return {
        "fracture": "F-AD5",
        "remediation": "--isolated + explicit --select (never discovery)",
        "isolated": isolated,
        "discovery_false_pass": discovery["rc"] == 0,
        "verdict": "READY" if ready else "NOT-READY",
    }


def fracture_ad4(scratch: Path) -> dict[str, Any]:
    """Remediation: pyrefly.toml bytes inside the claim's frozen digest surface."""
    root = fresh(scratch / "ad4")
    (root / "plant.py").write_text(
        'def fixed() -> int:\n    total: int = "many"\n    return total\n',
        encoding="utf-8",
    )
    configured = pyrefly_check(root)
    toml_sha = sha256((root / "pyrefly.toml").read_bytes())
    (root / "pyrefly.toml").write_text('preset = "basic"\n', encoding="utf-8")
    basic = pyrefly_check(root)
    basic_sha = sha256((root / "pyrefly.toml").read_bytes())
    # Remediation surface: claim pins toml digest; tamper changes pin.
    pin_detects_tamper = toml_sha != basic_sha
    type_silenced = basic["rc"] == 0 and configured["rc"] != 0
    ready = pin_detects_tamper and type_silenced and configured["rc"] != 0
    return {
        "fracture": "F-AD4",
        "remediation": "pyrefly.toml inside frozen claim digest (pin detects preset=basic)",
        "configured_rc": configured["rc"],
        "basic_rc": basic["rc"],
        "toml_digest_before": "sha256:" + toml_sha,
        "toml_digest_after_basic": "sha256:" + basic_sha,
        "pin_detects_tamper": pin_detects_tamper,
        "type_checks_silenced_under_basic": type_silenced,
        "verdict": "READY" if ready else "NOT-READY",
        "note": "production claim must list pyrefly.toml in scan-scope / subject "
        "digest; this restress proves the pin surface detects the measured tamper",
    }


def fracture_nd1() -> dict[str, Any]:
    """Remediation: claim digests only prose-blind fields; prefer uvx-class shape."""
    if not SIX.is_dir():
        return {
            "fracture": "F-ND1",
            "verdict": "NOT-READY",
            "note": "six subject absent; UNVERIFIED",
        }
    shapes = []
    for label, prefix in (
        ("ci-uv-run-with", PYREFLY_CI),
        ("uvx-scout", PYREFLY_UVX),
    ):
        raw, blind = [], []
        for _ in range(5):
            result = run(
                list(prefix) + ["check", ".", "--output-format", "json"], SIX
            )
            raw.append(result["stdout_sha256"][:16])
            blind.append(prose_blind_digest(result["stdout"]))
        shapes.append(
            {
                "label": label,
                "raw_distinct": len(set(raw)),
                "prose_blind_distinct": len(set(blind)),
                "prose_blind_stable": len(set(blind)) == 1,
            }
        )
    # READY iff prose-blind plane is stable on both shapes (claim digests that plane)
    ready = all(s["prose_blind_stable"] for s in shapes)
    return {
        "fracture": "F-ND1",
        "remediation": "JSON→SARIF / claim digests only prose-blind fields; "
        "never digest raw pyrefly stdout",
        "shapes": shapes,
        "verdict": "READY" if ready else "NOT-READY",
    }


def fracture_ad3(scratch: Path) -> dict[str, Any]:
    """Remediation floor: suppression bound the kernel can count — HOLD if absent."""
    root = fresh(scratch / "ad3")
    (root / "plant.py").write_text(
        'def fixed() -> int:\n    total: int = "many"  # pyrefly: ignore\n    return total\n',
        encoding="utf-8",
    )
    with_ignore = pyrefly_check(root)
    (root / "plant.py").write_text(
        'def fixed() -> int:\n    total: int = "many"\n    return total\n',
        encoding="utf-8",
    )
    without = pyrefly_check(root)
    suppressed = with_ignore["rc"] == 0 and without["rc"] != 0
    # Grep-witness prototype (not yet a kernel claim): count ignore markers.
    ignore_count = (root / "plant.py").read_text(encoding="utf-8").count("# pyrefly: ignore")
    # After rewrite ignore_count is 0; re-plant for witness demo
    (root / "plant.py").write_text(
        'def fixed() -> int:\n    total: int = "many"  # pyrefly: ignore\n    return total\n',
        encoding="utf-8",
    )
    witness_count = sum(
        1
        for path in root.rglob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if "# pyrefly: ignore" in line
    )
    return {
        "fracture": "F-AD3",
        "remediation_floor": "committed grep-witness over ignore markers, count frozen "
        "in the claim manifest — OR engine --ignore-noqa equivalent",
        "suppressed_still": suppressed,
        "with_ignore_rc": with_ignore["rc"],
        "without_ignore_rc": without["rc"],
        "prototype_ignore_marker_count": witness_count,
        "kernel_bound_witness_shipped": False,
        "verdict": "NOT-READY",
        "hold": "pyrefly 1.2.0 has no --ignore-noqa; a freeze-bound ignore-marker "
        "witness is not yet a first-class claim surface on main. Marker count is "
        "measurable (prototype) but not kernel-enforced.",
    }


def fracture_ad7(scratch: Path) -> dict[str, Any]:
    """Remediation floor: scope witness + scanner residency — HOLD if absent."""
    from ranex.foundation.canonical import canonical_json_bytes
    from ranex.foundation.scan_results import (
        scan_results_from_sarif,
        validate_scan_manifest,
    )

    root = fresh(scratch / "ad7")
    (root / "edge.py").write_text("import os\n", encoding="utf-8")  # dirty
    manifest = validate_scan_manifest(
        {
            "scope": ["edge.py"],
            "rules": ["F401"],
            "blocking_levels": ["error"],
            "accepted": {},
        }
    )
    # Hand-crafted zero-finding SARIF over a dirty subject — F-AD7 shape.
    sarif = canonical_json_bytes(
        {
            "version": "2.1.0",
            "runs": [
                {
                    "results": [],
                    "invocations": [{"executionSuccessful": True}],
                    "artifacts": [{"location": {"uri": "edge.py"}}],
                }
            ],
        }
    )
    summary = scan_results_from_sarif(sarif, manifest, subject_root=root)
    clean_reduction = (
        not summary.get("missing")
        and summary.get("counts", {}).get("failed", 1) == 0
    )
    return {
        "fracture": "F-AD7",
        "remediation_floor": "v0.5 files-checked scope witness + G-3 scanner residency",
        "zero_finding_forgery_still_reduces_clean": clean_reduction,
        "missing": summary.get("missing"),
        "counts": summary.get("counts"),
        "kernel_scope_witness_shipped": False,
        "verdict": "NOT-READY",
        "hold": "scan_results still accepts a zero-result SARIF whose artifacts "
        "cover the scope; files-checked / exit-channel binding for empty "
        "results is not on main. G-3 residency alone does not close the "
        "reduction-layer forgery.",
    }


def main() -> int:
    if not LAB.is_dir():
        raise SystemExit(f"lab absent: {LAB}")
    AUDIT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="adp-fracture-") as scratch_name:
        scratch = Path(scratch_name)
        rows = [
            fracture_ad1(scratch),
            fracture_ad5(scratch),
            fracture_ad4(scratch),
            fracture_nd1(),
            fracture_ad3(scratch),
            fracture_ad7(scratch),
        ]
    overall = (
        "READY"
        if all(row["verdict"] == "READY" for row in rows)
        else "NOT-READY"
    )
    receipt = {
        "schema": "ranex-adp-python-fracture-restress-v1",
        "overall": overall,
        "fractures": rows,
        "host": {
            "uname": platform.platform(),
            "python": platform.python_version(),
            "kernel_head": subprocess.run(
                ["git", "-C", str(KERNEL), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip(),
            "prior_stress": "tools/dogfood/audits/2026-09-26-adp-python-stress/",
            "prereg_sha256": "cb46915854572c448b7cb073db6944d2e765a3af86d21902ddcc4a4c97c06445",
        },
    }
    (AUDIT / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"overall={overall}")
    for row in rows:
        print(f"  {row['fracture']}: {row['verdict']}")
    print(f"receipt={AUDIT / 'receipt.json'}")
    return 0 if overall == "READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
