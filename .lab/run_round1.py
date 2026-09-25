#!/usr/bin/env python3
"""Round-1 scored harness for ADP steal wave 1 (prereg §1-§3).

Runs KG (S1 frozen-allowance + S2 blind bank) and KB (12 plant classes ×3
repeats) arms for ruff 0.16.2 and pyrefly 1.2.0 on the two pinned subjects,
recording output bytes (sha256) for TH-DET. Emits .lab/round1-results.json.
Kernel untouched; scratch only.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

LAB = Path("/home/soultransit/.treehouse/ranex-34bbe7/7/ranex/.lab")
SIX = LAB / "subjects" / "six"
RANEX = Path("/home/soultransit/.treehouse/ranex-34bbe7/7/ranex")
KG = LAB / "kg-s2"
PLANTS = LAB / "plants"
PYREFLY = ["uvx", "pyrefly==1.2.0"]
RUFF = ["ruff"]

# Round-0 frozen allowances: (engine, subject) -> {(rule, file): count}
ALLOWANCES: dict[str, dict[tuple[str, str], int]] = {}


def ruff_json(cwd: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        RUFF + ["check", *args, "--output-format", "json", "--ignore-noqa"],
        cwd=cwd, capture_output=True, text=True, timeout=600,
    )
    return proc.returncode, proc.stdout


def pyrefly_json(cwd: Path, args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        PYREFLY + ["check", *args, "--output-format", "json"],
        cwd=cwd, capture_output=True, text=True, timeout=900,
    )
    return proc.returncode, proc.stdout


def parse_ruff(payload: str) -> list[dict]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return [{"parse_error": payload[:400]}]
    return [
        {"rule": f.get("code") or "?", "file": f["filename"], "line": f["location"]["row"]}
        for f in data
    ]


def parse_pyrefly(payload: str) -> list[dict]:
    try:
        data = json.loads(payload).get("errors", [])
    except json.JSONDecodeError:
        return [{"parse_error": payload[:400]}]
    return [
        {"rule": e.get("name") or "?", "file": e.get("path") or "?", "line": e.get("line")}
        for e in data
    ]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def arm(name: str, runner, cwd: Path, args: list[str], repeats: int = 3) -> dict:
    runs = []
    t0 = time.monotonic()
    for _ in range(repeats):
        rc, out = runner(cwd, args)
        runs.append({"rc": rc, "sha": sha(out), "out": out})
    elapsed = time.monotonic() - t0
    deterministic = len({r["sha"] for r in runs}) == 1
    return {
        "arm": name,
        "cwd": str(cwd),
        "args": args,
        "repeats": [{k: r[k] for k in ("rc", "sha")} for r in runs],
        "deterministic": deterministic,
        "rc": runs[0]["rc"],
        "raw": runs[0]["out"],
        "seconds_per_run": round(elapsed / repeats, 2),
    }


def main() -> int:
    results: dict[str, object] = {
        "prereg_digest": "6af2d809f6363e571702525e87d6a0e2a1a13f2b9a769d7a2d7832aa1e4f0ce9",
        "arms": [],
    }
    arms: list[dict] = results["arms"]  # type: ignore[assignment]

    # ---- S1 clean baselines (freeze allowances) ----
    six_ruff = arm("S1/six/ruff", ruff_json, SIX, ["--isolated", "--select", "E4,E7,E9,F", "."])
    six_py = arm("S1/six/pyrefly", pyrefly_json, SIX, ["six.py", "test_six.py"])
    ranex_ruff = arm("S1/ranex/ruff", ruff_json, RANEX,
                     ["--config", str(RANEX / "pyproject.toml"), "src", "tests"])
    ranex_py = arm("S1/ranex/pyrefly", pyrefly_json, RANEX,
                   ["src/ranex", "--project-excludes", "**/verdict.py"])
    # NOTE ranex pyrefly runs through uv run --frozen in CI; the uvx variant
    # documents the isolated-tool case. CI parity is measured separately.

    for a, engine, subj in ((six_ruff, "ruff", "six"), (six_py, "pyrefly", "six"),
                            (ranex_ruff, "ruff", "ranex"), (ranex_py, "pyrefly", "ranex")):
        parse = parse_ruff if engine == "ruff" else parse_pyrefly
        findings = parse(a["raw"])
        a["findings"] = findings
        a["finding_count"] = len(findings)
        ALLOWANCES[f"{engine}/{subj}"] = {}
        for f in findings:
            key = (f["rule"], str(Path(f["file"]).name))
            ALLOWANCES[f"{engine}/{subj}"][key] = ALLOWANCES[f"{engine}/{subj}"].get(key, 0) + 1
        arms.append(a)
        print(f"[S1] {a['arm']}: {a['finding_count']} findings, det={a['deterministic']}", flush=True)

    # ---- S2 blind KG bank ----
    s2_ruff = arm("S2/kgbank/ruff", ruff_json, KG, ["--isolated", "--select", "E4,E7,E9,F", "."])
    s2_py = arm("S2/kgbank/pyrefly", pyrefly_json, KG, ["."])
    for a, engine in ((s2_ruff, "ruff"), (s2_py, "pyrefly")):
        parse = parse_ruff if engine == "ruff" else parse_pyrefly
        a["findings"] = parse(a["raw"])
        a["finding_count"] = len(a["findings"])
        arms.append(a)
        print(f"[S2] {a['arm']}: {a['finding_count']} findings (FP if >0), det={a['deterministic']}", flush=True)

    # ---- KB plants ----
    # Expected TARGET rules per plant (prereg §3). Catch = target rule fires
    # beyond the allowance; other excess rules are recorded as spillover.
    EXPECTED: dict[str, dict[str, list[str]]] = {
        "t1_wrong_arg_type": {"pyrefly": ["bad-argument-type", "argument-type", "typeddict"], "ruff": []},
        "t2_undefined_name": {"pyrefly": ["unknown-name"], "ruff": ["F821"]},
        "t3_return_type": {"pyrefly": ["return-type", "return-value"], "ruff": []},
        "t4_bad_attribute": {"pyrefly": ["attribute", "maybe-undefined", "unbound"], "ruff": []},
        "t5_wrong_arity": {"pyrefly": ["argument", "arity"], "ruff": []},
        "t6_incompatible_assign": {"pyrefly": ["assignment", "assign"], "ruff": []},
        "l1_unused_import": {"ruff": ["F401"], "pyrefly": []},
        "l2_f821": {"ruff": ["F821"], "pyrefly": ["unknown-name"]},
        "l3_f541": {"ruff": ["F541"], "pyrefly": []},
        "l4_lambda_assign": {"ruff": ["E731"], "pyrefly": []},
        "l5_bare_except": {"ruff": ["E722"], "pyrefly": []},
        "l6_eq_none": {"ruff": ["E711"], "pyrefly": []},
    }
    plant_files = sorted(PLANTS.glob("*.py"))
    plant_results: list[dict] = []
    for plant in plant_files:
        pid = plant.stem
        for subject, root in (("six", SIX), ("ranex", RANEX)):
            dest = (root / f"_lab_plant_{pid}.py") if subject == "six" else (root / "src" / "ranex" / f"_lab_plant_{pid}.py")
            shutil.copy(plant, dest)
            try:
                if subject == "six":
                    ruff_args = ["--isolated", "--select", "E4,E7,E9,F", "."]
                    py_args = ["six.py", "test_six.py", dest.name]
                else:
                    ruff_args = ["--config", str(RANEX / "pyproject.toml"), "src", "tests"]
                    py_args = ["src/ranex", "--project-excludes", "**/verdict.py"]
                ra = arm(f"KB/{subject}/{pid}/ruff", ruff_json, root, ruff_args)
                pa = arm(f"KB/{subject}/{pid}/pyrefly", pyrefly_json, root, py_args)
                for a, engine in ((ra, "ruff"), (pa, "pyrefly")):
                    parse = parse_ruff if engine == "ruff" else parse_pyrefly
                    a["findings"] = parse(a["raw"])
                    base = ALLOWANCES.get(f"{engine}/{subject}", {})
                    counts: dict[tuple[str, str], int] = {}
                    for f in a["findings"]:
                        k2 = (f["rule"], str(Path(f["file"]).name))
                        counts[k2] = counts.get(k2, 0) + 1
                    excess = {k2: c - base.get(k2, 0) for k2, c in counts.items() if c > base.get(k2, 0)}
                    a["excess"] = {f"{r}|{f2}": c for (r, f2), c in excess.items()}
                    arms.append(a)
                    expected_rules = EXPECTED.get(pid, {}).get(engine, [])
                    target_hit = any(
                        any(rule == exp or exp in rule or rule.startswith(exp)
                            for exp in expected_rules)
                        for (rule, _fname) in excess
                    )
                    applicable = bool(expected_rules)
                    caught = target_hit
                    plant_results.append({
                        "plant": pid, "engine": engine, "subject": subject,
                        "applicable": applicable, "caught": caught,
                        "det": a["deterministic"],
                        "excess": a["excess"], "rc": a["rc"],
                        "seconds": a["seconds_per_run"],
                    })
                    print(f"[KB] {pid}/{engine}/{subject}: applicable={applicable} caught={caught} excess={a['excess']} det={a['deterministic']}", flush=True)
            finally:
                dest.unlink(missing_ok=True)

    results["plant_results"] = plant_results  # type: ignore[assignment]
    out = LAB / "round1-results.json"
    slim = json.loads(json.dumps(results))
    for a in slim["arms"]:
        a.pop("raw", None)
    out.write_text(json.dumps(slim, indent=1, sort_keys=True))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
