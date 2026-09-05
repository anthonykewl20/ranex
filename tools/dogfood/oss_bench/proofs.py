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
import os
import re
from pathlib import Path
from typing import Any

ARCHIVE = Path(__file__).resolve().parent / "proofs"
SCHEMA = "ranex-oss-proof-entry-v1"
# Gate evaluate that loaded the kernel checkout rather than the task repo.
_KERNEL_JOURNAL = re.compile(r"journal=.*/ranex/governance/journal\.sqlite3")


def harness_fault_reason(entry: dict[str, Any]) -> str | None:
    """Return a reason when the row did not actually judge the task.

    Existing pile entries are never edited (append-only). Callers recompute
    this over stored rows so a harness bug cannot sit in the kernel
    false-block / false-pass counts.
    """
    stored = entry.get("harness_fault")
    if stored:
        return str(stored)
    if entry.get("kind") != "run":
        return None
    gate = entry.get("ranex_gate") or {}
    journal = gate.get("journal_output") or ""
    if _KERNEL_JOURNAL.search(journal.replace("\\", "/")):
        return "gate journal is the kernel checkout, not the task repo"
    command = gate.get("run_command") or ""
    if " pytest pytest" in command:
        return "bound command has no test node ids (argv misparse)"
    error = gate.get("run_error") or ""
    exit_code = gate.get("run_exit")
    if exit_code not in (0, 1, None) and "points at no file" in error:
        return "signing key path did not resolve"
    if exit_code not in (0, 1, None) and "file or directory not found: pytest" in error:
        return "bound command invoked pytest as a test path"
    if exit_code == 0 and "missing test ID(s): tools/dogfood/oss_bench/results/" in (
        gate.get("gate_output") or ""
    ):
        return "pristine manifest inherited the enclosing benchmark checkout's pytest root"
    return None


def _next_entry_number() -> int:
    numbers = []
    for path in ARCHIVE.glob("proof-*.json"):
        try:
            numbers.append(int(path.name.split("-")[1]))
        except (IndexError, ValueError):
            continue
    return (max(numbers) + 1) if numbers else 1


def _write(entry: dict[str, Any]) -> Path:
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    number = _next_entry_number()
    name = "proof-{}-{}-{}.json".format(
        f"{number:04d}", entry["date"],
        entry["task"].replace("/", "-").replace(":", "-"))
    path = ARCHIVE / name
    payload = json.dumps(entry, indent=2, sort_keys=True) + "\n"
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        os.write(fd, payload.encode())
    finally:
        os.close(fd)
    return path


def append_external(entry: dict[str, Any]) -> Path:
    """Append one entry produced by the external-repository proof driver
    (tools/dogfood/external_proof.py — released-kernel governance of a clean
    third-party repo). Same append-only collision guard as every entry; the
    caller owns idempotence by (run_id / attack, kernel commit)."""
    return _write(entry)


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
        gate = row["ranex_gate"]
        if gate.get("run_exit") not in (0, 1):
            # A run that never produced task evidence is not a kernel verdict.
            # Still archived, labeled, and excluded from false-block counts.
            pass
        entry = {
            "schema": SCHEMA, "kind": "run", "date": date,
            "kernel_head": kernel_head, "task": row["task"],
            "run_id": row["run_id"], "model": report.get("model"),
            "ground_truth_functional": row["ground_truth_functional"],
            "agent_steps": row.get("agent_steps"),
            "tokens": row.get("tokens"), "cost_usd": row.get("cost_usd"),
            "duration_s": row.get("duration_s"),
            "self_report": row["self_report"],
            "bare_ci": row["bare_ci"], "ranex_gate": gate,
        }
        fault = harness_fault_reason(entry)
        if fault:
            entry["harness_fault"] = fault
        entry["false_pass"] = (
            not fault
            and gate.get("gate_verdict") == "PASS"
            and row["ground_truth_functional"] != 1.0
        )
        entry["false_block"] = (
            not fault
            and gate.get("gate_verdict") == "FAIL"
            and row["ground_truth_functional"] == 1.0
        )
        written.append(_write(entry))

    demo = report.get("gaming_demo")
    if demo and ("deleted-tests", kernel_head) not in seen_attacks and demo.get("ranex_gate"):
        written.append(_write({
            "schema": SCHEMA, "kind": "attack", "attack": "deleted-tests",
            "date": date, "kernel_head": kernel_head,
            # The demo's task is stamped by run_divergence.py; the fallback
            # names the gap honestly instead of guessing a wrong repo.
            "task": demo.get("task", "unknown-task"), "run_id": "gaming",
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
            "task": stale.get("task", "unknown-task"), "run_id": "stale",
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


def _hidden_score(entry: dict[str, Any]) -> float | None:
    if entry.get("external") or entry.get("agentless"):
        return None
    score = entry.get("ground_truth_functional")
    return score if isinstance(score, (int, float)) else None


def _is_false_pass(entry: dict[str, Any]) -> bool:
    if entry.get("kind") != "run" or harness_fault_reason(entry):
        return False
    score = _hidden_score(entry)
    if score is None:
        return False
    gate = (entry.get("ranex_gate") or {}).get("gate_verdict")
    return gate == "PASS" and score != 1.0


def _is_false_block(entry: dict[str, Any]) -> bool:
    if entry.get("kind") != "run" or harness_fault_reason(entry):
        return False
    score = _hidden_score(entry)
    if score is None:
        return False
    gate = (entry.get("ranex_gate") or {}).get("gate_verdict")
    return gate == "FAIL" and score == 1.0


def summary() -> dict[str, Any]:
    entries = corpus()
    runs = [e for e in entries if e["kind"] == "run"]
    attacks = [e for e in entries if e["kind"] == "attack"]
    faults = [e for e in runs if harness_fault_reason(e)]
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
        "false_passes": sum(1 for e in runs if _is_false_pass(e)),
        "false_blocks": sum(1 for e in runs if _is_false_block(e)),
        "harness_faults": len(faults),
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
