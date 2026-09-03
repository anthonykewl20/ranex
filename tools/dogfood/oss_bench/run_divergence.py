#!/usr/bin/env python3
"""Divergence experiment: WITHOUT ranex vs WITH ranex, where they differ.

The baseline judged one solution twice — the arms could only agree. This
experiment measures the four positions that actually diverge when an agent's
work goes wrong:

  ground truth   VulcanBench's hidden-test grader (pristine tests, docker).
  bare CI        the repo's own test command after the agent patch — trusts
                 whatever tests are now in the tree (fooled by weakened
                 tests; green on luck).
  self-report    the agent's final claim, parsed from the run trace
                 (heuristic keyword match, labeled as such).
  ranex gate     a claim bound to a manifest frozen from the PRISTINE tests
                 BEFORE the agent patch: junitxml results must match the
                 committed expected IDs — deleted/renamed tests surface as
                 missing, failures as non_passed. Goalposts cannot move.

Every verdict comes from a real execution; self-report is the only parsed
opinion and is labeled heuristic.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/soultransit/devtony/ranex/src")
from two_arm import PRODUCER, APPROVER, _git, _ranex, pinned_python_has_pytest  # noqa: E402
from ranex.foundation.signing import generate_keypair  # noqa: E402
from ranex.foundation.suite_results import freeze_manifest  # noqa: E402

RANEX_REPO = Path("/home/soultransit/devtony/ranex")
DEFAULT_VULCAN = Path("/home/soultransit/devtony/VulcanBench")
PY = "/usr/bin/python3"


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def test_files_for(task_dir: Path) -> list[str]:
    return sorted(p.name for p in (task_dir / "tests").iterdir()
                  if p.name.endswith(".py"))


def build_manifest_governed_repo(task_dir: Path, out: Path, patch: Path | None
                                 ) -> tuple[Path, str, list[str]]:
    """Repo with a PRISTINE frozen suite manifest committed BEFORE the agent
    patch, and one results-bound claim. Returns (repo, key_path, junit_cmd)."""
    repo = out / "repo"
    repo.mkdir(parents=True)
    for item in (task_dir / "repo").iterdir():
        if item.is_dir():
            shutil.copytree(item, repo / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, repo / item.name)
    for item in (task_dir / "tests").iterdir():
        if item.name == "__pycache__":
            continue
        shutil.copy2(item, repo / item.name)
    test_files = test_files_for(task_dir)
    assert _git(repo, "init", "-q").returncode == 0
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", "task base + pristine tests").returncode == 0

    # Freeze the manifest from the PRISTINE suite (fail_to_pass tests are
    # red pre-fix; freeze records IDs only, never outcomes).
    metadata = json.loads((task_dir / "metadata.json").read_text())
    selected = [entry for entry in metadata["tests"]["fail_to_pass"]]
    # cmd shape: python -m pytest <test node id> -q  -> node id is argv[3]
    junit_cmd = [PY, "-m", "pytest", "-q",
                 "--junitxml=governance/suite_results.xml",
                 *[shlex.split(entry["cmd"])[3] for entry in selected]]
    # Freeze the manifest over EXACTLY the task's contracted test set (the
    # fail_to_pass IDs). They are red pre-fix; the manifest records IDs only,
    # never outcomes — the same freeze discipline the kernel repo uses.
    probe_cmd = [PY, "-m", "pytest", "-q", "--junitxml=/tmp/freeze-probe.xml",
                 *[shlex.split(entry["cmd"])[3] for entry in selected]]
    subprocess.run(probe_cmd, cwd=str(repo), capture_output=True, check=False)
    manifest = freeze_manifest(Path("/tmp/freeze-probe.xml").read_bytes(),
                               expected_skips={})
    (repo / "governance").mkdir(exist_ok=True)
    (repo / "governance" / "suite_manifest.json").write_bytes(_canonical(manifest))

    # Vendor the kernel: governed_repository_root() resolves the repo that
    # CONTAINS the CLI, so the governed subject must carry its own copy.
    shutil.copytree(RANEX_REPO / "src", repo / "src", dirs_exist_ok=True)
    shutil.copy2(RANEX_REPO / "pyproject.toml", repo / "pyproject.toml")
    shutil.copy2(RANEX_REPO / "uv.lock", repo / "uv.lock")

    private, public = generate_keypair()
    (out / "keys").mkdir(exist_ok=True)
    key_path = out / "keys" / "bench.key"
    key_path.write_text(private)
    key_path.chmod(0o600)
    (repo / "governance" / "producers.yaml").write_text(
        "producers:\n  {}: {}\n".format(PRODUCER, public))
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TASK_TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        "        command: [{}]\n"
        "        results_artifact: governance/suite_results.xml\n".format(
            ", ".join(json.dumps(part) for part in junit_cmd)))
    (repo / ".gitignore").write_text(
        "governance/evidence.json\n"
        "governance/suite_results.xml\n"
        "__pycache__/\n*.pyc\n.pytest_cache/\n")
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm",
                "governance: pristine frozen manifest + results-bound gate").returncode == 0

    if patch is not None:
        result = subprocess.run(["git", "-C", str(repo), "apply", str(patch)],
                                capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise AssertionError(f"agent patch failed to apply: {result.stderr[:200]}")
        status = _git(repo, "status", "--porcelain")
        if status.stdout.strip():
            assert _git(repo, "add", "-A").returncode == 0
            assert _git(repo, "commit", "-qm", "agent solution").returncode == 0
        # else: the agent's patch makes no net change — a legitimate failed
        # outcome; the base tree already IS the agent's solution.
    return repo, str(key_path), junit_cmd


def bare_ci(repo: Path, junit_cmd: list[str]) -> dict:
    """What a normal CI does: run the test FILES in the tree, whatever they
    now contain. Deleted or weakened tests are invisible to it."""
    files_cmd = [PY, "-m", "pytest", "-q",
                 *sorted({part.split("::")[0] for part in junit_cmd[4:]
                          if "::" in part})]
    started = time.perf_counter()
    result = subprocess.run(files_cmd, cwd=str(repo), capture_output=True,
                            text=True, check=False, timeout=600)
    tail = [line for line in result.stdout.strip().splitlines()
            if line.strip()][-1:] or ["<no output>"]
    return {"command": " ".join(files_cmd),
            "output_tail": tail[0],
            "exit": result.returncode,
            "verdict": "GREEN" if result.returncode == 0 else "RED",
            "elapsed_s": round(time.perf_counter() - started, 1)}


def self_report(vulcan_root: Path, run_id: str) -> dict:
    """Heuristic: does the agent's final message claim success?"""
    trace = vulcan_root / "runs" / run_id / "trace.jsonl"
    last_text = ""
    for line in trace.read_text().splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "llm_response":
            content = (event.get("data") or {}).get("content") or ""
            if isinstance(content, str) and content.strip():
                last_text = content
    claimed = bool(re.search(
        r"\b(all tests|tests? (now )?pass|passing\b|fixed|implemented|"
        r"completed successfully|done\b|finish)", last_text, re.I))
    return {"claimed_success": claimed, "final_words": last_text[-160:],
            "heuristic": True}


def governed(repo: Path, key_path: str, junit_cmd: list[str]) -> dict:
    started = time.perf_counter()
    run = _ranex(repo, key_path, "run", "--claim", "tests-executed",
                 "--producer", PRODUCER, "--", *junit_cmd)
    verdict = _ranex(repo, key_path, "gate", "evaluate", "HEAD",
                     "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    journal = _ranex(repo, key_path, "journal", "verify",
                     "--journal", "governance/journal.sqlite3")
    gate_pass = verdict.returncode == 0 and "FAIL" not in verdict.stdout
    return {"run_command": "ranex run --claim tests-executed --producer "
                           + PRODUCER + " -- " + " ".join(junit_cmd),
            "run_exit": run.returncode,
            "run_error": run.stderr.strip()[-250:] if run.returncode != 0 else "",
            "gate_verdict": "PASS" if gate_pass else "FAIL",
            "gate_output": verdict.stdout.strip()[:800],
            "journal_output": journal.stdout.strip()[:400],
            "journal_verified": journal.returncode == 0 and "verified" in journal.stdout,
            "elapsed_s": round(time.perf_counter() - started, 1)}


def demo_gaming(task_dir: Path, out: Path, patch: Path,
                delete_tests: int = 4) -> dict:
    """FAULT-INJECTED demo of test-deletion gaming: take a genuinely solved
    task, then 'the agent' deletes some test functions on top. Bare CI stays
    green (the remaining tests pass); the manifest-bound gate must FAIL
    (deleted IDs are missing). Clearly labeled — this row is a mechanism
    demonstration, not model behavior."""
    import ast

    repo, key_path, junit_cmd = build_manifest_governed_repo(task_dir, out, patch)
    test_files = test_files_for(task_dir)
    victim = repo / test_files[0]
    tree = ast.parse(victim.read_text())
    kept, removed = [], []
    for node in tree.body:
        if (isinstance(node, ast.FunctionDef)
                and node.name.startswith("test")
                and len(removed) < delete_tests):
            removed.append(node.name)
            continue
        kept.append(node)
    tree.body = kept
    victim.write_text(ast.unparse(tree))
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm",
                "agent solution (some tests 'cleaned up')").returncode == 0
    row = {"bare_ci": bare_ci(repo, junit_cmd),
           "ranex_gate": governed(repo, key_path, junit_cmd),
           "removed_tests": removed, "fault_injected": True}
    return row


def demo_stale(task_dir: Path, out: Path, patch: Path) -> dict:
    """The stale-proof trap, run for real. A solved task's proof is recorded
    (gate PASS). Then the classic move: one more 'small fix' AFTER the green
    run, and 'done'. The old green output is still a perfectly valid-looking
    screenshot — no bare-world mechanism can tell it stopped being evidence.
    The gate can: evidence is digest-bound to the exact tree, one edit later
    the proof is stale and the gate names it."""
    repo, key_path, junit_cmd = build_manifest_governed_repo(task_dir, out, patch)
    before = governed(repo, key_path, junit_cmd)

    # The one extra tweak after the green: a one-line comment in a source file.
    source = next((repo / "txnkv").glob("*.py"))
    source.write_text(source.read_text() + "\n# post-green tweak: tiny fix, no re-run\n")
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", "small cleanup after the green run").returncode == 0
    # The agent does NOT re-run the tests — that is the whole point. The gate
    # must judge the OLD evidence against the NEW tree.
    verdict = _ranex(repo, key_path, "gate", "evaluate", "HEAD",
                     "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    journal = _ranex(repo, key_path, "journal", "verify",
                     "--journal", "governance/journal.sqlite3")
    gate_pass = verdict.returncode == 0 and "FAIL" not in verdict.stdout
    after = {"gate_verdict": "PASS" if gate_pass else "FAIL",
             "gate_output": verdict.stdout.strip()[:800],
             "journal_output": journal.stdout.strip()[:400],
             "journal_verified": journal.returncode == 0 and "verified" in journal.stdout,
             "elapsed_s": 0.0}

    return {"before": before, "after": after,
            "bare_world": "the earlier green output is indistinguishable from "
                          "valid proof — nothing binds it to the code shipped",
            "fault_injected": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--row-task", action="append", default=[],
                        metavar="TASK=RUN_ID", help="reuse an existing run's patch")
    parser.add_argument("--fresh-task", action="append", default=[],
                        metavar="TASK[:EFFORT]", help="new agent run")
    parser.add_argument("--demo-gaming", metavar="TASK=RUN_ID",
                        help="fault-injected test-deletion demo on a solved task")
    parser.add_argument("--demo-stale", metavar="TASK=RUN_ID",
                        help="fault-injected stale-proof demo on a solved task")
    parser.add_argument("--vulcan-root", type=Path, default=DEFAULT_VULCAN)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-run-cap", type=float, default=1.0)
    args = parser.parse_args()

    ok, detail = pinned_python_has_pytest()
    if not ok:
        print(f"PREREQUISITE-MISSING: {detail}")
        return 4
    state = json.loads((Path(__file__).parent / "state.json").read_text())
    env = dict(os.environ)
    lines = Path(state["api_key_file"]).read_text().splitlines()
    env[state["api_key_env"]] = lines[state["api_key_file_line"] - 1].strip()
    for name, value in state.get("provider_env", {}).items():
        env[name] = value
    args.out.mkdir(parents=True, exist_ok=True)

    rows = []
    plan = [(t, rid, None) for t, rid in
            (spec.split("=", 1) for spec in args.row_task)]
    for spec in args.fresh_task:
        task, _, effort = spec.partition(":")
        plan.append((task, None, effort or None))

    for task, run_id, effort in plan:
        run_id_given = run_id is not None
        task_dir = None
        task_suite = "v1"
        for suite in ("v1", "coding-intelligence-index-v4"):
            candidate = args.vulcan_root / "tasks" / suite / task
            if candidate.is_dir():
                task_dir = candidate
                task_suite = suite
                break
        if task_dir is None:
            rows.append({"task": task, "error": "task not found in known suites"})
            continue
        if run_id is None:
            print(f"=== {task}: agent run (effort {effort or 'default'}) ...", flush=True)
            cmd = [str(args.vulcan_root / ".venv" / "bin" / "vulcanbench"), "run",
                   "--task", task, "--model", state["model"], "--sandbox", "docker",
                   "--no-judges", "--max-run-cost", str(args.per_run_cap)]
            if task_suite != "v1":
                cmd += ["--tasks-root",
                        str(args.vulcan_root / "tasks" / task_suite)]
            if effort:
                cmd += ["--effort", effort]
            result = subprocess.run(cmd, cwd=str(args.vulcan_root), env=env,
                                    capture_output=True, text=True, check=False,
                                    timeout=3600)
            match = re.search(r"run complete (\S+)", result.stdout)
            if not match:
                rows.append({"task": task, "error": result.stderr[-300:]})
                print("    agent run FAILED:", result.stderr[-200:], flush=True)
                continue
            run_id = match.group(1)
        run_dir = args.vulcan_root / "runs" / run_id
        summary = json.loads((run_dir / "summary.json").read_text())
        patch = run_dir / "final.patch"
        row = {"task": task, "run_id": run_id,
               "ground_truth_functional": summary["scores"].get("functional"),
               "agent_steps": summary.get("steps"),
               "tokens": summary.get("total_tokens"),
               "cost_usd": summary.get("cost_usd"),
               "duration_s": summary.get("duration_s"),
               "cost_capped": summary.get("cost_capped"),
               "self_report": self_report(args.vulcan_root, run_id)}
        print(f"    ground truth functional={row['ground_truth_functional']} "
              f"self-claim={row['self_report']['claimed_success']}", flush=True)
        try:
            repo, key_path, junit_cmd = build_manifest_governed_repo(
                task_dir, args.out / f"{task}-{(run_id or 'fresh')[-8:]}",
                patch if patch.exists() else None)
            row["bare_ci"] = bare_ci(repo, junit_cmd)
            row["ranex_gate"] = governed(repo, key_path, junit_cmd)
        except AssertionError as exc:
            row["error"] = str(exc)[:250]
        rows.append(row)
        gov = row.get("ranex_gate", {})
        print(f"    bare CI={row.get('bare_ci', {}).get('verdict')} "
              f"gate={gov.get('gate_verdict')} journal="
              f"{'verified' if gov.get('journal_verified') else '?'}", flush=True)

    report_demo = None
    report_stale = None
    if args.demo_gaming:
        task, _, run_id = args.demo_gaming.partition("=")
        task_dir = args.vulcan_root / "tasks" / "v1" / task
        patch = args.vulcan_root / "runs" / run_id / "final.patch"
        print(f"=== {task}: fault-injected gaming demo ...", flush=True)
        demo = demo_gaming(task_dir, args.out / f"{task}-gamed", patch)
        report_demo = demo
        print(f"    bare CI={demo['bare_ci']['verdict']} (deleted "
              f"{len(demo['removed_tests'])} tests, remaining still green) "
              f"gate={demo['ranex_gate']['gate_verdict']}", flush=True)
    if args.demo_stale:
        task, _, run_id = args.demo_stale.partition("=")
        task_dir = args.vulcan_root / "tasks" / "v1" / task
        patch = args.vulcan_root / "runs" / run_id / "final.patch"
        print(f"=== {task}: stale-proof demo ...", flush=True)
        report_stale = demo_stale(task_dir, args.out / f"{task}-stale", patch)
        print(f"    green proof -> gate "
              f"{report_stale['before']['gate_verdict']}; one tiny edit later -> "
              f"gate {report_stale['after']['gate_verdict']}", flush=True)

    report = {"schema": "ranex-oss-bench-divergence-v1",
              "model": state["model"], "rows": rows,
              "gaming_demo": report_demo,
              "stale_demo": report_stale,
              "note": "four positions: pristine grader / bare CI on the "
                      "patched tree / parsed self-report / manifest-bound gate"}
    (args.out / "divergence.json").write_text(json.dumps(report, indent=2) + "\n")
    print("\n=== DIVERGENCE ===")
    for row in rows:
        if "error" in row and "ranex_gate" not in row:
            print(f"{row['task']:28} ERROR {row['error'][:80]}")
            continue
        print(f"{row['task']:28} truth={row['ground_truth_functional']} "
              f"bareCI={row['bare_ci']['verdict']} "
              f"selfclaim={row['self_report']['claimed_success']} "
              f"gate={row['ranex_gate']['gate_verdict']}")
    if report_demo:
        print(f"{'GAMED (fault-injected)':28} bareCI={report_demo['bare_ci']['verdict']} "
              f"gate={report_demo['ranex_gate']['gate_verdict']} "
              f"(deleted: {', '.join(report_demo['removed_tests'])})")
    if report_stale:
        print(f"{'STALE (fault-injected)':28} green->gate "
              f"{report_stale['before']['gate_verdict']}, tiny edit->gate "
              f"{report_stale['after']['gate_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
