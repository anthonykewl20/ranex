"""The real-world proof archive: append-only, dated, per-run proof entries.

Every dogfood cycle that runs the divergence experiment appends one JSON
file per proof (agent run verdicts, or a fault-injected demonstration) to
tools/dogfood/oss_bench/proofs/. Files are never edited or deleted — the
corpus only grows, and every page number is derived from it, never typed.

Entry kinds:
  run     a real agent run judged from four positions (hidden tests, bare
          CI, parsed self-report, ranex gate) with raw transcripts.
  attack  a fault-injected demonstration (deleted tests / stale proof) on
          a real solved run — always labeled fault_injected.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ARCHIVE = Path(__file__).resolve().parent / "proofs"
SCHEMA = "ranex-oss-proof-entry-v1"


def _entry_id(existing: int) -> str:
    return f"{existing + 1:04d}"


def _write(entry: dict[str, Any]) -> Path:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    number = len(list(ARCHIVE.glob("proof-*.json"))) + 1
    name = "proof-{}-{}-{}.json".format(
        _entry_id(number - 1), entry["date"], entry["task"].replace("/", "-"))
    path = ARCHIVE / name
    if path.exists():
        raise AssertionError(f"proof entry collision (archive is append-only): {path}")
    path.write_text(json.dumps(entry, indent=2, sort_keys=True) + "\n")
    return path


def append_from_divergence(divergence_path: Path, date: str,
                           kernel_head: str) -> list[Path]:
    """Turn one experiment output into dated archive entries. Idempotent per
    run: entries whose (run_id, kind) already exist are skipped."""
    report = json.loads(divergence_path.read_text())
    written: list[Path] = []
    existing = corpus()
    seen = {(e.get("run_id"), e.get("kind")) for e in existing}
    # Attacks are re-proven per kernel release: catching them again on a new
    # kernel is a NEW proof, not a duplicate.
    seen_attacks = {(e.get("attack"), e.get("kernel_head")) for e in existing}

    for row in report.get("rows", []):
        if "ranex_gate" not in row:
            continue
        key = (row.get("run_id"), "run")
        if key in seen:
            continue
        entry = {
            "schema": SCHEMA, "kind": "run", "date": date,
            "kernel_head": kernel_head, "task": row["task"],
            "run_id": row["run_id"], "model": report.get("model"),
            "ground_truth_functional": row["ground_truth_functional"],
            "agent_steps": row.get("agent_steps"),
            "tokens": row.get("tokens"), "cost_usd": row.get("cost_usd"),
            "duration_s": row.get("duration_s"),
            "self_report": row["self_report"],
            "bare_ci": row["bare_ci"], "ranex_gate": row["ranex_gate"],
            "false_pass": (row["ranex_gate"]["gate_verdict"] == "PASS"
                           and row["ground_truth_functional"] != 1.0),
            "false_block": (row["ranex_gate"]["gate_verdict"] == "FAIL"
                            and row["ground_truth_functional"] == 1.0),
        }
        written.append(_write(entry))

    demo = report.get("gaming_demo")
    if demo and ("deleted-tests", kernel_head) not in seen_attacks and demo.get("ranex_gate"):
        written.append(_write({
            "schema": SCHEMA, "kind": "attack", "attack": "deleted-tests",
            "date": date, "kernel_head": kernel_head,
            "task": "py-txn-kvstore", "run_id": "gaming",
            "model": report.get("model"), "fault_injected": True,
            "removed_tests": demo.get("removed_tests", []),
            "bare_ci": demo["bare_ci"], "ranex_gate": demo["ranex_gate"],
            "caught": demo["ranex_gate"]["gate_verdict"] == "FAIL",
        }))
    stale = report.get("stale_demo")
    if stale and ("stale-proof", kernel_head) not in seen_attacks and stale.get("after"):
        written.append(_write({
            "schema": SCHEMA, "kind": "attack", "attack": "stale-proof",
            "date": date, "kernel_head": kernel_head,
            "task": "py-txn-kvstore", "run_id": "stale",
            "model": report.get("model"), "fault_injected": True,
            "before": stale["before"], "after": stale["after"],
            "caught": stale["after"]["gate_verdict"] == "FAIL",
        }))
    return written


def corpus() -> list[dict[str, Any]]:
    if not ARCHIVE.is_dir():
        return []
    return [json.loads(p.read_text())
            for p in sorted(ARCHIVE.glob("proof-*.json"))]


def summary() -> dict[str, Any]:
    entries = corpus()
    runs = [e for e in entries if e["kind"] == "run"]
    attacks = [e for e in entries if e["kind"] == "attack"]
    by_date: dict[str, int] = {}
    for entry in entries:
        by_date[entry["date"]] = by_date.get(entry["date"], 0) + 1
    cumulative, timeline = 0, []
    for date in sorted(by_date):
        cumulative += by_date[date]
        timeline.append({"date": date, "total": cumulative})
    return {
        "entries": len(entries),
        "runs": len(runs),
        "attacks": len(attacks),
        "attacks_caught": sum(1 for e in attacks if e.get("caught")),
        "false_passes": sum(1 for e in runs if e.get("false_pass")),
        "false_blocks": sum(1 for e in runs if e.get("false_block")),
        "tokens": sum(e.get("tokens") or 0 for e in runs),
        "cost_usd": sum(e.get("cost_usd") or 0 for e in runs),
        "nights": len(by_date),
        "timeline": timeline,
        "archive_digest": "sha256:" + hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(ARCHIVE.glob("proof-*.json")))
        ).hexdigest(),
    }


if __name__ == "__main__":
    import sys

    if sys.argv[1] == "summary":
        print(json.dumps(summary(), indent=2))
    elif sys.argv[1] == "append":
        date, head = sys.argv[3], sys.argv[4]
        for path in append_from_divergence(Path(sys.argv[2]), date, head):
            print("appended", path.name)
