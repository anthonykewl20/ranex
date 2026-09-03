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


def _run_pytest(root: Path, junit: Path | None, node_ids: list[str],
                env: dict) -> subprocess.CompletedProcess:
    argv = ["/usr/bin/python3", "-m", "pytest", "-q"]
    if junit is not None:
        argv.append(f"--junitxml={junit}")
    return subprocess.run(argv + sorted(set(node_ids)),
                          cwd=str(root), capture_output=True, text=True,
                          check=False, timeout=PROBE_TIMEOUT_SECONDS, env=env)


def _collection_ok(root: Path, node_ids: list[str], env: dict,
                   scratch: Path | None = None) -> str | None:
    """None when the suite collects under `env`, else a short reason."""
    import tempfile as _tf

    with _tf.NamedTemporaryFile(suffix=".xml", delete=False,
                                dir=scratch if scratch else None) as probe:
        junit = Path(probe.name)
    try:
        run = _run_pytest(root, junit, node_ids, env)
        from ranex.foundation.suite_results import freeze_manifest

        freeze_manifest(junit.read_bytes(), expected_skips={})
        return None
    except FileNotFoundError:
        return "pytest wrote no junitxml (collection-time crash)"
    except ValueError as exc:
        return str(exc)[:200]
    except subprocess.TimeoutExpired:
        return f"suite exceeded {PROBE_TIMEOUT_SECONDS}s"
    finally:
        junit.unlink(missing_ok=True)


def preflight_task(task_dir: Path, node_ids: list[str],
                   env_assignments: list[str] | None = None) -> dict:
    """Soundness gate mirroring GOVERNANCE conditions on a throwaway copy.

    `ranex run` hermetically strips the child environment (verified: the
    confined child sees PYTHONPATH=None), so labels are only sound when the
    task's tests work WITHOUT its env assignments:

      1. confined-equivalent collection must succeed (else
         governance-env-unsupported when the task's own env would fix it,
         plain failed when nothing fixes it);
      2. the gold patch must make the selected ids green confined-equivalent
         (else gold-not-green with the failing summary).
    """
    task_env = dict(os.environ)
    for assignment in env_assignments or []:
        key, _, value = assignment.partition("=")
        task_env[key] = value

    with tempfile.TemporaryDirectory(prefix="ranex-preflight-") as tmp:
        scratch = Path(tmp)
        root = scratch / "repo"
        root.mkdir()
        try:
            from trainer.governed import governed_equivalent_env, materialize_repo

            governed_env = governed_equivalent_env(scratch)
            materialize_repo(task_dir, root)
        except Exception as exc:  # noqa: BLE001 — any materialization failure is data
            return {"status": "failed",
                    "reason": f"cannot materialize repo: {str(exc)[:150]}"}
        for source in [task_dir / "tests"]:
            if not source.is_dir():
                continue
            for item in sorted(source.iterdir()):
                if item.name == "__pycache__":
                    continue
                target = root / item.name
                if target.exists():
                    # GovernedRepo refuses collisions; preflight must agree.
                    return {"status": "failed",
                            "reason": f"hidden test collides with repo file: {item.name}"}
                if item.is_dir():
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
        _git_init(root)

        confined_reason = _collection_ok(root, node_ids, governed_env)
        if confined_reason is not None:
            with_env_reason = _collection_ok(root, node_ids, task_env)
            if with_env_reason is None:
                return {"status": "governance-env-unsupported",
                        "reason": f"tests collect only with the task env "
                                  f"({env_assignments}); ranex run strips it"}
            return {"status": "failed", "reason": confined_reason}

        gold = task_dir / "gold_patch.diff"
        if not gold.is_file():
            return {"status": "no-gold-patch",
                    "reason": "corpus task carries no gold_patch.diff; the "
                              "gold variant has no solution to apply"}

        # Pristine-red gate: the empty variant's FAIL label is only sound
        # when the contracted tests actually fail BEFORE the fix. A task
        # whose f2p ids already pass on this interpreter (VulcanBench graded
        # them red inside docker, not here) would false-diverge.
        try:
            pristine = _run_pytest(root, None, node_ids, governed_env)
        except subprocess.TimeoutExpired:
            return {"status": "failed", "reason": "pristine suite timeout"}
        if pristine.returncode == 0:
            return {"status": "pristine-green-here",
                    "reason": "contracted tests pass BEFORE the fix on this "
                              "host; the empty/partial labels are unsound"}

        applied = subprocess.run(
            ["git", "-C", str(root), "apply", str(gold)],
            capture_output=True, text=True, check=False)
        if applied.returncode != 0:
            return {"status": "gold-not-green",
                    "reason": f"gold patch does not apply: {applied.stderr[-120:]}"}
        try:
            gold_run = _run_pytest(root, None, node_ids, governed_env)
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
