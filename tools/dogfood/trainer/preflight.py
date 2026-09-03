"""Preflight: can this task's pristine suite even run on THIS host?

VulcanBench tasks are graded inside Docker with their dependencies installed;
the trainer runs them under the pinned system interpreter. A task whose tests
import uninstalled modules (psycopg2, redis, ...) is not exercisable here,
and that fact must be a CLASSIFICATION ("preflight-failed", with the reason),
never a training divergence — the divergence would describe our environment,
not ranex.

The probe mirrors GovernedRepo's freeze step on a throwaway copy: run the
pristine suite once with junitxml, freeze the manifest. Any failure shortens
to a one-line reason. Results are cached in the corpus snapshot.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

PROBE_TIMEOUT_SECONDS = 120


def preflight_task(task_dir: Path, node_ids: list[str],
                   env_assignments: list[str] | None = None) -> dict:
    """-> ok | failed | gold-not-green (labels are only sound when gold is green).

    Two gates, both on a throwaway copy, both with the task's own env:
      1. the pristine suite must COLLECT (freeze the manifest);
      2. the gold patch (when the corpus has one) must make the selected ids
         PASS under the pinned interpreter. A gold that is only green inside
         VulcanBench's docker (extra backends, databases) makes the `gold`
         label unsound on this host — the task is excluded and the failing
         test named, never silently trained with a wrong label.
    """
    env = dict(os.environ)
    for assignment in env_assignments or []:
        key, _, value = assignment.partition("=")
        env[key] = value
    with tempfile.TemporaryDirectory(prefix="ranex-preflight-") as tmp:
        root = Path(tmp) / "repo"
        root.mkdir()
        for source in (task_dir / "repo", task_dir / "tests"):
            if not source.is_dir():
                continue
            for item in sorted(source.iterdir()):
                if item.name == "__pycache__":
                    continue
                target = root / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target)
        _git_init(root)
        junit = Path(tmp) / "probe.xml"
        try:
            run = subprocess.run(
                ["/usr/bin/python3", "-m", "pytest", "-q",
                 f"--junitxml={junit}", *sorted(set(node_ids))],
                cwd=str(root), capture_output=True, text=True, check=False,
                timeout=PROBE_TIMEOUT_SECONDS, env=env,
            )
        except subprocess.TimeoutExpired:
            return {"status": "failed",
                    "reason": f"pristine suite exceeded {PROBE_TIMEOUT_SECONDS}s"}
        try:
            from ranex.foundation.suite_results import freeze_manifest

            freeze_manifest(junit.read_bytes(), expected_skips={})
        except FileNotFoundError:
            return {"status": "failed",
                    "reason": "pytest wrote no junitxml (collection-time crash)"}
        except ValueError as exc:
            return {"status": "failed", "reason": str(exc)[:200]}
        if not junit.is_file():
            return {"status": "failed", "reason": "no junitxml artifact"}

        gold = task_dir / "gold_patch.diff"
        if not gold.is_file():
            return {"status": "ok"}
        applied = subprocess.run(
            ["git", "-C", str(root), "apply", str(gold)],
            capture_output=True, text=True, check=False)
        if applied.returncode != 0:
            return {"status": "gold-not-green",
                    "reason": f"gold patch does not apply: {applied.stderr[-120:]}"}
        try:
            gold_run = subprocess.run(
                ["/usr/bin/python3", "-m", "pytest", "-q", *sorted(set(node_ids))],
                cwd=str(root), capture_output=True, text=True, check=False,
                timeout=PROBE_TIMEOUT_SECONDS, env=env,
            )
        except subprocess.TimeoutExpired:
            return {"status": "gold-not-green",
                    "reason": f"gold suite exceeded {PROBE_TIMEOUT_SECONDS}s"}
        if gold_run.returncode != 0:
            tail = (gold_run.stdout.strip().splitlines() or ["?"])[-1]
            return {"status": "gold-not-green",
                    "reason": f"gold not green here: {tail[:120]}"}
        return {"status": "ok"}


def _git_init(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"],
                   capture_output=True, check=False)


def run_preflights(snapshot_path: Path, only_missing: bool = True) -> dict:
    """Preflight every exercisable task in the snapshot; write results back."""
    snapshot = json.loads(snapshot_path.read_text())
    checked = failed = 0
    for raw in snapshot["tasks"]:
        if raw["classification"] != "exercisable":
            continue
        if only_missing and raw.get("preflight", {}).get("status") == "ok":
            continue
        ids = sorted({nid for e in raw["entries"] for nid in e["node_ids"]})
        env = sorted({a for e in raw["entries"] for a in e.get("env", [])})
        raw["preflight"] = preflight_task(Path(raw["path"]), ids, env)
        checked += 1
        if raw["preflight"]["status"] == "failed":
            failed += 1
            print(f"  preflight-failed {raw['suite']}/{raw['task']}: "
                  f"{raw['preflight']['reason'][:80]}", flush=True)
    snapshot_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    return {"checked": checked, "failed": failed}
