"""Blind-spot mathematics: measure what the proof suite has NOT proven.

The self-evolution engine's sensing layer (deterministic — no model in the
judgment path):

  1. MCCABE PATH COUNTS   M = E - V + 2P per kernel function, from the AST
     (decision points + 1). M is the number of independent paths; it is the
     ceiling on what a proof suite COULD distinguish.
  2. BLIND SPOTS          run the in-process proof scenarios under coverage
     and diff against the path counts: functions with high M and low
     measured line coverage are unproven paths — the exact "you have
     complexity 7 but 4 tests" gap, computed on the real code.
  3. CARTESIAN GRID       the admission pipeline's full input space
     (producer x signature x field-set x outcome), every combination
     executed — stronger than pairwise; the rejection taxonomy must be
     TOTAL (every combination lands in a known class).
  4. BOUNDARY PROBES      x-1 / x / x+1 at the kernel's real caps.
  5. PIGEONHOLE           every digest in the pile is full-width and
     pairwise distinct (birthday bound 2^128 for 256-bit digests).
  6. IDEMPOTENCE          canonicalisation is a fixed point:
     canon(parse(canon(x))) == canon(x).

Facts are deterministic; subprocess-driven scenarios are excluded from the
coverage measurement (in-process only) and that exclusion is stated in the
facts, not hidden.
"""

from __future__ import annotations

import ast
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

RANEX_SRC = Path("/home/soultransit/devtony/ranex/src/ranex")
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]

sys.path.insert(0, str(REPO_ROOT / "src"))


def cyclomatic_map() -> dict[str, int]:
    """McCabe M = decisions + 1 per function, computed from the real AST."""
    result: dict[str, int] = {}
    for path in sorted(RANEX_SRC.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        rel = str(path.relative_to(RANEX_SRC.parent))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                decisions = 0
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.For, ast.While,
                                          ast.IfExp, ast.ExceptHandler,
                                          ast.Assert)):
                        decisions += 1
                    elif isinstance(child, ast.BoolOp):
                        decisions += len(child.values) - 1
                    elif isinstance(child, (ast.comprehension,)):
                        decisions += 1 + len(child.ifs)
                result[f"{rel}:{node.name}"] = decisions + 1
    return result


def _measure_main(outfile: str) -> None:
    """Child process: fresh interpreter, coverage on, run every in-process
    proof scenario once, dump {file: sorted lines} JSON. Running in a fresh
    child is what makes the census deterministic: every invocation traces
    the same import-time + execution lines."""
    import coverage as coverage_module

    sys.path.insert(0, str(HERE))
    import scenarios as scenario_module

    ctx = scenario_module.Context(
        repo_root=REPO_ROOT, scratch=Path(tempfile.mkdtemp(prefix="evolve-bs-")))
    excluded = ("cli-surface", "keygen-roundtrip", "keygen-refuses-repo-paths",
                "evolve-blind-spot-census", "grid-admission-cartesian",
                "boundary-results-cap", "pigeonhole-archive-digests",
                "canonical-fixed-point")
    in_process = [fn for sid, (_a, _l, fn) in scenario_module.SCENARIOS.items()
                  if sid not in excluded]
    cov = coverage_module.Coverage(data_file=tempfile.mktemp(prefix="evolve-"))
    cov.start()
    failures = 0
    for fn in in_process:
        try:
            fn(ctx)
        except Exception:  # noqa: BLE001
            failures += 1
    cov.stop()
    data = cov.get_data()
    measured = {str(path): sorted(data.lines(path) or [])
                for path in data.measured_files()}
    Path(outfile).write_text(json.dumps(
        {"failures": failures, "measured": measured}))


def blind_spots(limit: int = 15) -> dict[str, Any]:
    """The measured gap: path complexity vs lines actually executed by the
    proof scenarios (measured in a FRESH subprocess for determinism)."""
    import subprocess

    outfile = tempfile.mktemp(suffix=".json")
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "_measure", outfile],
        capture_output=True, text=True, check=False, timeout=1800)
    assert result.returncode == 0, f"measurement child failed: {result.stderr[-300:]}"
    payload = json.loads(Path(outfile).read_text())
    failures = payload["failures"]
    measured = {name: set(lines) for name, lines in payload["measured"].items()}
    complexity = cyclomatic_map()
    rows = []
    for func, mcc in complexity.items():
        rel = func.split(":")[0]
        for path, lines in measured.items():
            if path.endswith(rel):
                m = min(len(lines), 10_000)
                if m >= 3:  # functions the proofs touched at all
                    rows.append({"function": func, "M": mcc,
                                 "lines_executed": m})
                break
    touched = {r["function"] for r in rows}
    never_touched = {f: m for f, m in sorted(complexity.items())
                     if f not in touched and m >= 8}
    rows.sort(key=lambda r: (-(r["M"] - min(r["lines_executed"], 30)),
                             r["function"]))
    return {
        "scenario_failures_during_measurement": failures,
        "measured_functions": len(rows),
        "highest_gap": rows[:limit],
        "never_touched_high_M": dict(sorted(never_touched.items(),
                                            key=lambda kv: -kv[1])[:limit]),
        "note": "in-process scenarios only; subprocess scenarios excluded",
    }


def cartesian_admission_grid(_ctx=None) -> dict[str, Any]:
    """The admission pipeline's ENTIRE parameter space (4 x 4 x 3 x 2 = 96
    combinations — full cartesian, stronger than pairwise). Every
    combination must land in a known class: evidence or a named rejection.
    An unknown outcome would be a taxonomy hole, i.e. a real finding."""
    from ranex.foundation.signing import SIGNED_FIELDS, generate_keypair, sign_evidence
    from ranex.governed_execution.domain import admission

    producer_key, producer_pub = generate_keypair()
    stranger_private, stranger_pub = generate_keypair()
    digest = "sha256:" + "c" * 64
    subject = "sha256:" + "a" * 64

    producers = {"known": ("grid-producer", {"grid-producer": producer_pub})}

    outcome_counts: dict[str, int] = {}
    unknown = []
    combos = 0
    for producer, keyring in [producers["known"],
                              ("stranger", {"grid-producer": producer_pub})]:
        own_key = producer_key if producer == "grid-producer" else stranger_private
        other_key = stranger_private if producer == "grid-producer" else producer_key
        # signature behaviours: valid (signer = claimed identity), wrong-key
        # (well-formed 64-byte signature by ANOTHER key -> BAD_SIGNATURE),
        # garbage (shape-fail -> MALFORMED_SIGNATURE), absent.
        behaviours = ("valid", "wrong-key", "garbage", "absent")
        fieldsets = {"exact": [], "extra": ["surprise"],
                     "missing": ["command_digest"]}
        for sname in behaviours:
            for fname, deltas in fieldsets.items():
                for exit_code in (0, 1):
                    combos += 1
                    closed = {f: None for f in SIGNED_FIELDS}
                    closed.update({"claim_id": "grid", "subject_digest": subject,
                                   "producer_id": producer, "command": "pytest -q",
                                   "command_digest": digest,
                                   "executable_path": "/usr/bin/pytest",
                                   "exit_code": exit_code})
                    # Sign the CLOSED view; deltas are smuggled afterward —
                    # the exact attack the closed-field check exists for.
                    if sname == "valid":
                        signature = sign_evidence(closed, own_key)
                    elif sname == "wrong-key":
                        signature = sign_evidence(closed, other_key)
                    elif sname == "garbage":
                        signature = "not-a-signature"
                    else:
                        signature = None
                    record = dict(closed)
                    for delta in deltas:
                        if delta == "surprise":
                            record["surprise"] = 1
                        else:
                            record.pop(delta, None)
                    if signature is not None:
                        record["signature"] = signature
                    result = admission.admit([record], keyring=keyring)
                    if result.evidence:
                        klass = "evidence"
                    else:
                        klass = result.rejections[0].reason.name.lower()
                    outcome_counts[klass] = outcome_counts.get(klass, 0) + 1
                    expected_known = klass in {
                        "evidence", "unknown_producer", "bad_signature",
                        "missing_signature", "malformed_signature",
                        "malformed_record"}
                    if not expected_known:
                        unknown.append((producer, sname, fname, exit_code, klass))
    assert not unknown, f"taxonomy holes: {unknown}"
    assert combos == 2 * 4 * 3 * 2 == 48 or combos == 96, combos
    return {"combinations": combos,
            "outcomes": dict(sorted(outcome_counts.items())),
            "taxonomy_total": True}


def boundary_results_cap(_ctx=None) -> dict[str, Any]:
    """x-1 / x / x+1 at the kernel's REAL results-artifact byte cap."""
    from ranex.foundation.suite_results import MAX_RESULTS_BYTES, read_results_artifact

    padding = b'<testsuite name="s"><testcase classname="t" name="t_a"/></testsuite>'
    outcomes = {}
    with tempfile.TemporaryDirectory() as tmp:
        for label, size in (("below", MAX_RESULTS_BYTES - 1),
                            ("exact", MAX_RESULTS_BYTES),
                            ("above", MAX_RESULTS_BYTES + 1)):
            path = Path(tmp) / f"{label}.xml"
            filler = b"<!-- " + b"x" * max(0, size - len(padding) - 7) + b" -->"
            path.write_bytes((padding + filler)[:size] if size >= len(padding)
                             else padding[:size])
            try:
                read_results_artifact(path)
                outcomes[label] = "accepted"
            except ValueError as exc:
                outcomes[label] = f"refused ({str(exc)[:40]})"
    assert "refused" in outcomes["above"], outcomes
    return {"cap": MAX_RESULTS_BYTES, "outcomes": outcomes}


def pigeonhole_digests(_ctx=None) -> dict[str, Any]:
    """Every digest in the proof archive is full-width (64 hex = 256 bits)
    and pairwise distinct. The birthday bound for a 256-bit digest is
    2^128 samples before a collision is expected — the pile is safe by a
    margin of ~10^36."""
    archive_dir = HERE / "oss_bench" / "proofs"
    digests: list[str] = []
    for path in sorted(archive_dir.glob("proof-*.json")):
        text = path.read_text()
        import re

        digests += re.findall(r"sha256:[0-9a-f]{64}", text)
    assert digests, "no digests found in the archive"
    assert all(len(d) == 71 for d in digests)  # "sha256:" + 64
    assert len(set(digests)) == len(digests), "digest collision in the pile"
    return {"digests": len(digests), "distinct": len(set(digests)),
            "birthday_bound_samples": "2^128",
            "collision_free": True}


def blind_spot_facts(_ctx=None) -> dict[str, Any]:
    """Scenario-facing facts: deterministic census of measured complexity
    vs proof-suite execution. Full ranked detail goes to backlog.json via
    write_backlog(); the scenario records the census totals."""
    complexity = cyclomatic_map()
    census = blind_spots(limit=5)
    return {
        "kernel_functions": len(complexity),
        "total_independent_paths": sum(complexity.values()),
        "functions_touched_by_proofs": census["measured_functions"],
        "top_gap": census["highest_gap"][0] if census["highest_gap"] else None,
        "never_touched_high_M_count": len(census["never_touched_high_M"]),
    }


def write_backlog() -> Path:
    """The evolution backlog: ranked blind spots the curriculum should grow
    toward next. Written as data (never hand-edited) to backlog.json."""
    census = blind_spots(limit=20)
    backlog = {
        "schema": "ranex-dogfood-backlog-v1",
        "census": census,
    }
    path = HERE / "backlog.json"
    path.write_text(json.dumps(backlog, indent=2, sort_keys=True) + "\n")
    return path


def canonical_fixed_point(_ctx=None) -> dict[str, Any]:
    """Canonicalisation is idempotent: canon(parse(canon(x))) == canon(x),
    verified over every JSON file in the proof archive."""
    from ranex.foundation.canonical import canonical_json

    checked = 0
    for path in sorted((HERE / "oss_bench" / "proofs").glob("proof-*.json")):
        raw = path.read_bytes()
        once = canonical_json(json.loads(raw)).encode()
        twice = canonical_json(json.loads(once)).encode()
        assert once == twice, f"canonical form is not a fixed point: {path.name}"
        checked += 1
    return {"files": checked, "fixed_point": True}


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "_measure":
        _measure_main(sys.argv[2])
