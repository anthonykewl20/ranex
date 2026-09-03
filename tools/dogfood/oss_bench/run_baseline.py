#!/usr/bin/env python3
"""Initial GLM 5.3 baseline: WITHOUT ranex vs WITH ranex on real tasks.

Per task, ONE real model run (zai:glm-5.3 through the VulcanBench harness on
the GLM Coding Plan endpoint) produces the agent's solution (final.patch).
That SAME solution then gets two independent verdicts:

  WITHOUT ranex — VulcanBench's hidden-test grader (its functional score),
                   plus the task's own test commands run bare.
  WITH ranex    — the identical solution in a governed repo: every test
                   command under `ranex run` (signed evidence), then
                   `gate evaluate` decides; the journal chain must verify.

Honest framing: ranex is governance, not model capability — the model's
solution is the same in both arms BY CONSTRUCTION. The baseline measures
whether the governed verdict matches hidden-test reality, at what overhead,
and what the bare arm trusts that the governed arm proves. No number is
typed by hand: grader scores come from summary.json, gate verdicts from
ranex, costs from the harness.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from two_arm import (  # noqa: E402
    RANEX_PY, build_governed_repo, governed_cycle, pinned_python_has_pytest,
)

DEFAULT_TASKS = ("py-paginate-cursor", "py-txn-kvstore", "py-config-parse")


def _env(state: dict) -> dict[str, str]:
    env = dict(os.environ)
    key_file = Path(state["api_key_file"])
    lines = key_file.read_text().splitlines()
    env[state["api_key_env"]] = lines[state["api_key_file_line"] - 1].strip()
    for name, value in state.get("provider_env", {}).items():
        env[name] = value
    return env


def vulcanbench_run(vulcan_root: Path, task: str, env: dict[str, str],
                    model: str, cap: float, sandbox: str = "docker") -> dict:
    """One real agent run; returns the newest run dir for this task."""
    started = time.perf_counter()
    result = subprocess.run(
        [str(vulcan_root / ".venv" / "bin" / "vulcanbench"), "run",
         "--task", task, "--model", model,
         "--sandbox", sandbox, "--no-judges", "--max-run-cost", str(cap)],
        cwd=str(vulcan_root), env=env, capture_output=True, text=True,
        check=False, timeout=3600,
    )
    elapsed = round(time.perf_counter() - started, 1)
    tail = result.stdout.strip().splitlines()[-6:]
    run_id = None
    for line in result.stdout.splitlines():
        match = re.search(r"run complete (\S+)", line)
        if match:
            run_id = match.group(1)
    return {"ok": result.returncode == 0, "run_id": run_id, "elapsed_s": elapsed,
            "tail": tail, "stderr": result.stderr.strip()[-400:]}


def claim_commands_for(task_dir: Path) -> list[tuple[str, list[str]]]:
    metadata = json.loads((task_dir / "metadata.json").read_text())
    commands = []
    for entry in metadata["tests"]["fail_to_pass"]:
        argv = shlex.split(entry["cmd"])
        if argv[0] == "python":
            argv[0] = "/usr/bin/python3"
        commands.append((entry["name"], argv))
    return commands


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", nargs="*", default=list(DEFAULT_TASKS))
    parser.add_argument("--suite", default="v1")
    parser.add_argument("--vulcan-root", type=Path,
                        default=Path("/home/soultransit/devtony/VulcanBench"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-run-cap", type=float, default=1.0)
    args = parser.parse_args()

    state = json.loads((Path(__file__).parent / "state.json").read_text())
    model = state["model"]
    ok, detail = pinned_python_has_pytest()
    if not ok:
        print(f"PREREQUISITE-MISSING: {detail}")
        return 4
    env = _env(state)
    args.out.mkdir(parents=True, exist_ok=True)

    rows = []
    for task in args.tasks:
        task_dir = args.vulcan_root / "tasks" / args.suite / task
        print(f"=== {task}: agent run (model {model}) ...", flush=True)
        run = vulcanbench_run(args.vulcan_root, task, env, model,
                              args.per_run_cap)
        row: dict = {"task": task, "agent_run": run}
        if not run["ok"] or not run["run_id"]:
            rows.append(row)
            print(f"    agent run FAILED: {run['stderr'][-200:]}")
            continue
        run_dir = args.vulcan_root / "runs" / run["run_id"]
        summary = json.loads((run_dir / "summary.json").read_text())
        patch = run_dir / "final.patch"
        scores = summary.get("scores", {})
        row["grader_functional"] = scores.get("functional")
        row["grader_total"] = scores.get("total")
        row["agent_steps"] = summary.get("steps")

        commands = claim_commands_for(task_dir)
        print(f"    grader functional={row['grader_functional']} "
              f"steps={row['agent_steps']}; governed verdict ...", flush=True)
        governed_started = time.perf_counter()
        try:
            repo, key_path = build_governed_repo(
                task_dir, args.out / task, patch=patch if patch.exists() else None,
                claim_commands=commands)
            cycle = governed_cycle(repo, key_path, commands)
            passing = sum(1 for r in cycle["runs"] if r["exit"] == 0)
            row["governed"] = {
                "gate_verdict": cycle["gate_verdict"],
                "journal_verified": cycle["journal_verified"],
                "commands_passing": f"{passing}/{len(commands)}",
                "overhead_s": round(time.perf_counter() - governed_started, 1),
            }
        except AssertionError as exc:
            row["governed"] = {"error": f"agent patch would not apply: {exc}"}
        rows.append(row)
        gov = row["governed"]
        print(f"    WITH ranex: gate {gov.get('gate_verdict')} "
              f"({gov.get('commands_passing', '?')} cmds, journal "
              f"{'verified' if gov.get('journal_verified') else '?'}, "
              f"{gov.get('overhead_s', '?')}s)", flush=True)

    report = {
        "schema": "ranex-oss-bench-baseline-v1",
        "model": model,
        "suite": args.suite,
        "per_run_cap_usd": args.per_run_cap,
        "note": "same model solution judged twice: hidden-test grader (WITHOUT "
                "ranex) vs signed-evidence gate (WITH ranex)",
        "tasks": rows,
    }
    (args.out / "baseline.json").write_text(json.dumps(report, indent=2) + "\n")
    print("\n=== BASELINE ===")
    for row in rows:
        gov = row.get("governed", {})
        print(f"{row['task']:22} grader={row.get('grader_functional')} "
              f"gate={gov.get('gate_verdict', 'n/a')} "
              f"cmds={gov.get('commands_passing', '-')} "
              f"journal={'verified' if gov.get('journal_verified') else '-'} "
              f"gov_overhead={gov.get('overhead_s', '-')}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
