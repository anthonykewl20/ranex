"""Dogfood training and benchmarking loop for ranex.

The loop is ITERATIVE and EVIDENCE-BASED:

  capabilities  print the source-derived capability catalog (anchors: file:line)
  list          print the scenario curriculum (what each scenario trains)
  run           execute scenarios once; double-run determinism self-check
  baseline      record the current deterministic facts as the golden baseline
  iterate       full loop pass: run -> verify determinism -> diff against the
                baseline -> append one iteration record to the ledger -> diff
                against the previous iteration (new findings, resolved ones)
  drift         compare the two most recent ledger iterations
  bench         repeat scenarios and time them (NON-deterministic: timings are
                excluded from baselines and ledgers on purpose)

Nothing here mutates the working tree, the committed governance state, or the
network. Every recorded fact is canonical JSON with no clocks, no randomness,
no environment — a baseline diff is therefore a REAL behavioural change, not
noise. Assumptions are not entertained: a scenario that cannot prove its
lesson against the installed kernel fails.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from scenarios import SCENARIOS, REPO_ROOT, Context

TOOL_DIR = Path(__file__).parent
CATALOG = TOOL_DIR / "capabilities.json"
BASELINE = TOOL_DIR / "baselines.json"
LEDGER_DIR = TOOL_DIR / "iterations"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def git_head() -> str:
    result = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
                            capture_output=True, text=True, check=False)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


# --------------------------------------------------------------------------
# execution
# --------------------------------------------------------------------------


def execute(scenario_id: str, scratch: Path) -> dict[str, Any]:
    """Run one scenario; return a deterministic outcome record."""
    _area, _lesson, fn = SCENARIOS[scenario_id]
    try:
        facts = fn(Context(repo_root=REPO_ROOT, scratch=scratch))
        if not isinstance(facts, dict):
            raise AssertionError(f"scenario returned {type(facts).__name__}, not a facts dict")
        # Round-trip proves the facts are canonical-JSON encodable: anything
        # that cannot be serialised deterministically was never evidence.
        canonical_bytes(facts)
        return {"id": scenario_id, "status": "pass", "facts": facts, "error": None}
    except Exception as exc:  # noqa: BLE001 — scenario failure is data
        return {"id": scenario_id, "status": "fail", "facts": {},
                "error": f"{type(exc).__name__}: {exc}"}


def execute_with_determinism_check(scenario_id: str, scratch: Path) -> dict[str, Any]:
    """Run a scenario TWICE in fresh scratch trees; the two fact records must
    be byte-identical or the scenario itself is declared non-deterministic."""
    with tempfile.TemporaryDirectory(prefix="ranex-dogfood-a-") as tmp_a, \
            tempfile.TemporaryDirectory(prefix="ranex-dogfood-b-") as tmp_b:
        first = execute(scenario_id, Path(tmp_a))
        second = execute(scenario_id, Path(tmp_b))
    first["deterministic"] = (
        first["status"] == second["status"] == "pass"
        and canonical_bytes(first["facts"]) == canonical_bytes(second["facts"])
    )
    if first["status"] == "pass" and not first["deterministic"]:
        first["error"] = "NON-DETERMINISTIC: two runs produced different facts"
    return first


def run_all(filter_: str | None) -> list[dict[str, Any]]:
    selected = [sid for sid in SCENARIOS if filter_ is None or filter_ in sid]
    results = []
    with tempfile.TemporaryDirectory(prefix="ranex-dogfood-") as tmp:
        scratch = Path(tmp)
        for sid in selected:
            outcome = execute_with_determinism_check(sid, scratch)
            mark = "PASS" if outcome["status"] == "pass" and outcome["deterministic"] else "FAIL"
            print(f"{mark}  {sid}")
            if outcome["error"]:
                print(f"     {outcome['error']}")
            results.append(outcome)
    return results


# --------------------------------------------------------------------------
# baselines and iteration ledger
# --------------------------------------------------------------------------


def facts_digest(outcome: dict[str, Any]) -> str:
    return sha256_hex(canonical_bytes(outcome["facts"]))


def load_baseline() -> dict[str, str]:
    if not BASELINE.is_file():
        return {}
    return json.loads(BASELINE.read_text())


def diff_against_baseline(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A finding is any drift from the golden baseline, or any failure."""
    baseline = load_baseline()
    findings: list[dict[str, Any]] = []
    for outcome in results:
        sid = outcome["id"]
        if outcome["status"] != "pass" or not outcome.get("deterministic"):
            findings.append({"scenario": sid, "kind": "failure",
                             "error": outcome["error"]})
            continue
        digest = facts_digest(outcome)
        if sid not in baseline:
            findings.append({"scenario": sid, "kind": "unbaselined",
                             "facts_digest": digest})
        elif baseline[sid] != digest:
            findings.append({"scenario": sid, "kind": "baseline-drift",
                             "was": baseline[sid], "now": digest})
    return findings


def write_iteration(results: list[dict[str, Any]], findings: list[dict[str, Any]]) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(LEDGER_DIR.glob("iteration-*.json"))
    number = len(existing) + 1
    record = {
        "schema": "ranex-dogfood-iteration-v1",
        "iteration": number,
        "git_head": git_head(),
        "scenarios": [
            {"id": o["id"], "status": o["status"],
             "deterministic": o.get("deterministic", False),
             "facts_digest": facts_digest(o) if o["status"] == "pass" else None}
            for o in results
        ],
        "findings": findings,
    }
    path = LEDGER_DIR / f"iteration-{number:03d}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return path


def load_iterations() -> list[dict[str, Any]]:
    if not LEDGER_DIR.is_dir():
        return []
    return [json.loads(p.read_text())
            for p in sorted(LEDGER_DIR.glob("iteration-*.json"))]


def diff_iterations(previous: dict[str, Any], current: dict[str, Any]) -> list[str]:
    prev_by_id = {s["id"]: s for s in previous["scenarios"]}
    lines = []
    for entry in current["scenarios"]:
        sid, status = entry["id"], entry["status"]
        before = prev_by_id.get(sid)
        if before is None:
            lines.append(f"NEW      {sid} ({status})")
        elif before["status"] != status:
            lines.append(f"CHANGED  {sid}: {before['status']} -> {status}")
        elif before["facts_digest"] != entry["facts_digest"]:
            lines.append(f"DRIFT    {sid}: facts digest changed")
    for sid in sorted(set(prev_by_id) - {s["id"] for s in current["scenarios"]}):
        lines.append(f"GONE     {sid} (present in previous iteration only)")
    return lines


# --------------------------------------------------------------------------
# commands
# --------------------------------------------------------------------------


def cmd_capabilities() -> int:
    catalog = json.loads(CATALOG.read_text())
    print(f"schema: {catalog['schema']}")
    print(f"source: {catalog['derived_from']}\n")
    for area in catalog["areas"]:
        print(f"[{area['id']}] {area['capability']}")
        for anchor in area.get("anchors", []):
            print(f"    anchor: {anchor}")
    return 0


def cmd_list() -> int:
    for scenario_id, (area, lesson, _fn) in SCENARIOS.items():
        print(f"[{area}] {scenario_id}")
        print(f"    {lesson}")
    return 0


def cmd_run(filter_: str | None) -> int:
    results = run_all(filter_)
    passed = sum(1 for r in results if r["status"] == "pass" and r["deterministic"])
    print(f"\n{passed}/{len(results)} scenarios passed deterministically")
    findings = diff_against_baseline(results)
    for finding in findings:
        print(f"FINDING {finding['kind']}: {finding['scenario']}")
    return 1 if any(f["kind"] == "failure" or f["kind"] == "baseline-drift"
                    for f in findings) else 0


def cmd_baseline(filter_: str | None) -> int:
    results = run_all(filter_)
    failures = [r for r in results if r["status"] != "pass" or not r["deterministic"]]
    if failures:
        print("refusing to baseline: scenarios failed")
        return 1
    baseline = load_baseline() if BASELINE.is_file() else {}
    for outcome in results:
        baseline[outcome["id"]] = facts_digest(outcome)
    BASELINE.write_text(json.dumps(baseline, indent=2, sort_keys=True) + "\n")
    print(f"baseline recorded: {len(results)} scenarios -> {BASELINE}")
    return 0


def cmd_iterate(filter_: str | None) -> int:
    print(f"dogfood iteration at {git_head()[:12]}\n")
    results = run_all(filter_)
    findings = diff_against_baseline(results)
    path = write_iteration(results, findings)
    iterations = load_iterations()
    print(f"\niteration record: {path}")
    print(f"findings this pass: {len(findings)}")
    for finding in findings:
        print(f"  - {finding['kind']}: {finding['scenario']}")
    if len(iterations) >= 2:
        lines = diff_iterations(iterations[-2], iterations[-1])
        print(f"\nvs previous iteration ({iterations[-2]['iteration']}):")
        for line in lines or ["  (no change)"]:
            print(f"  {line}")
    exited = 1 if any(f["kind"] in ("failure", "baseline-drift") for f in findings) else 0
    print(f"\nexited {exited}")
    return exited


def cmd_drift() -> int:
    iterations = load_iterations()
    if len(iterations) < 2:
        print("need at least two recorded iterations (run `iterate` twice)")
        return 2
    previous, current = iterations[-2], iterations[-1]
    print(f"iteration {previous['iteration']} ({previous['git_head'][:12]}) -> "
          f"{current['iteration']} ({current['git_head'][:12]})")
    for line in diff_iterations(previous, current) or ["(no change)"]:
        print(f"  {line}")
    return 0


def cmd_bench(filter_: str | None, repeat: int, output: Path | None) -> int:
    """Timings are explicitly NON-deterministic; they never enter baselines
    or the ledger. They answer capacity questions, not correctness ones."""
    selected = [sid for sid in SCENARIOS if filter_ is None or filter_ in sid]
    report: dict[str, object] = {
        "schema": "ranex-dogfood-benchmark-v1",
        "git_head": git_head(),
        "repeat": repeat,
        "note": "timings are wall-clock and non-deterministic by nature",
        "scenarios": [],
    }
    failures = 0
    with tempfile.TemporaryDirectory(prefix="ranex-dogfood-") as tmp:
        scratch = Path(tmp)
        for sid in selected:
            timings = []
            failed = False
            for _ in range(repeat):
                import time

                started = time.perf_counter()
                outcome = execute(sid, scratch)
                timings.append(round((time.perf_counter() - started) * 1000, 3))
                failed = failed or outcome["status"] != "pass"
            if failed:
                failures += 1
            report["scenarios"].append({
                "id": sid,
                "status": "fail" if failed else "pass",
                "timings_ms": timings,
                "median_ms": round(statistics.median(timings), 3),
                "min_ms": min(timings),
                "max_ms": max(timings),
            })
            print(f"{sid}: median {statistics.median(timings):.1f} ms "
                  f"(min {min(timings):.1f} / max {max(timings):.1f})")
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload)
        print(f"\nreport written to {output}")
    return 1 if failures else 0


def open_findings() -> list[str]:
    """F-ids currently under '## Open' in FINDINGS.md."""
    path = TOOL_DIR / "FINDINGS.md"
    if not path.is_file():
        return []
    ids, in_open = [], False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            in_open = line.strip() == "## Open"
        elif in_open and line.startswith("### "):
            finding_id = line[4:].split("—")[0].strip()
            finding_id = finding_id.split("(")[0].strip() or finding_id
            ids.append(finding_id)
    return ids


def cmd_report(output_dir: Path) -> int:
    """Generate the public benchmark page: deterministic proof board +
    environment-labeled timings + scaling + loop history. The HTML embeds
    the sha256 of the JSON it was rendered from."""
    import benchmarks
    import report_site

    print(f"collecting proof board at {git_head()[:12]} ...")
    with tempfile.TemporaryDirectory(prefix="ranex-dogfood-") as tmp:
        scratch = Path(tmp)
        results = [execute(sid, scratch) for sid in SCENARIOS]
        failures = [r for r in results if r["status"] != "pass"]
        for failure in failures:
            print(f"FAIL {failure['id']}: {failure['error']}")
        print(f"proof board: {len(results) - len(failures)}/{len(results)} passed")
        print("collecting timings ...")
        metrics = benchmarks.collect_timings(scratch / "bench", repeats=3)

    by_area: dict[str, int] = {}
    for sid in SCENARIOS:
        by_area[SCENARIOS[sid][0]] = by_area.get(SCENARIOS[sid][0], 0) + 1
    report = {
        "schema": "ranex-dogfood-report-v1",
        "git_head": git_head(),
        "environment": benchmarks.environment(),
        "proof_board": {
            "total": len(results),
            "passed": len(results) - len(failures),
            "by_area": by_area,
            "findings_open": open_findings(),
        },
        "timings": [m.as_dict() for m in metrics],
        "scaling": benchmarks.scaling_series(metrics),
        "ledger": [
            {"iteration": it["iteration"], "git_head": it["git_head"],
             "scenarios": len(it["scenarios"]), "findings": len(it["findings"])}
            for it in load_iterations()
        ],
    }
    html_path, json_path = report_site.generate_site(report, output_dir)
    print(f"page:    {html_path}")
    print(f"data:    {json_path}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dogfood", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities")
    sub.add_parser("list")
    run_p = sub.add_parser("run")
    run_p.add_argument("--filter")
    base_p = sub.add_parser("baseline")
    base_p.add_argument("--filter")
    iter_p = sub.add_parser("iterate")
    iter_p.add_argument("--filter")
    sub.add_parser("drift")
    report_p = sub.add_parser("report")
    report_p.add_argument("--output-dir", type=Path,
                          default=TOOL_DIR / "site")
    bench_p = sub.add_parser("bench")
    bench_p.add_argument("--filter")
    bench_p.add_argument("--repeat", type=int, default=3)
    bench_p.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    if args.command == "capabilities":
        return cmd_capabilities()
    if args.command == "list":
        return cmd_list()
    if args.command == "run":
        return cmd_run(args.filter)
    if args.command == "baseline":
        return cmd_baseline(args.filter)
    if args.command == "iterate":
        return cmd_iterate(args.filter)
    if args.command == "drift":
        return cmd_drift()
    if args.command == "report":
        return cmd_report(args.output_dir)
    return cmd_bench(args.filter, args.repeat, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
