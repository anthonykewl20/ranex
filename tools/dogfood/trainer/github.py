"""GitHub corpus source: real enterprise code, pinned, honestly measured.

A GitHub repository has no gold patch — its PRISTINE HEAD is the solution.
The trainer therefore measures the baseline first (run the repo's own suite
under the pinned interpreter) and derives labels from that measurement:

  baseline green   -> `gold` (pristine HEAD) MUST PASS the gate, and the
                      gaming/staleness variants MUST FAIL it;
  baseline red     -> recorded as `github/baseline-red` (a fact about the
                      repo or the pinned interpreter), no gold label claimed.

Only dependency-free test trees are candidates on this host (the pinned
interpreter is system Python); a repo whose tests need uninstalled modules
is classified baseline-red with the reason — never silently skipped.

Clone is pinned: --depth 1 at the requested rev (default HEAD), and the
resolved commit sha is recorded in the pass.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from trainer import variants
from trainer.corpus import _NODE_ID

GITHUB_VARIANTS = ("gold", "delete-tests", "goalpost-move",
                   "manifest-swap", "manifest-crossbind")


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=str(cwd) if cwd else None,
                          capture_output=True, text=True, check=False)


def clone_pinned(url: str, rev: str, out: Path) -> tuple[Path, str]:
    """Clone at a pinned rev; -> (repo dir, resolved commit sha)."""
    out.mkdir(parents=True, exist_ok=True)
    result = _git("clone", "--quiet", "--filter=blob:none", url, str(out))
    if result.returncode != 0:
        raise AssertionError(f"clone failed: {result.stderr[-200:]}")
    if rev.upper() != "HEAD":
        checked = _git("checkout", "--quiet", rev, cwd=out)
        if checked.returncode != 0:
            raise AssertionError(f"rev {rev} not found: {checked.stderr[-200:]}")
    sha = _git("rev-parse", "HEAD", cwd=out).stdout.strip()
    return out, sha


def collect_node_ids(repo: Path, max_ids: int, env: dict) -> list[str]:
    """The repo's own test ids, via real collection under the pinned toolchain."""
    run = subprocess.run(
        ["/usr/bin/python3", "-m", "pytest", "--collect-only", "-q", "--no-header"],
        cwd=str(repo), capture_output=True, text=True, check=False, timeout=300,
        env=env,
    )
    ids = sorted({line.strip() for line in run.stdout.splitlines()
                  if _NODE_ID.match(line.strip())})
    if not ids:
        raise AssertionError(
            f"no test ids collected (pytest exit {run.returncode}): "
            f"{(run.stdout + run.stderr)[-200:]}")
    return ids[:max_ids]


def baseline_green(repo: Path, node_ids: list[str], env: dict) -> tuple[bool, str]:
    """Run the pristine suite honestly; -> (all selected ids pass?, tail)."""
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False,
                                     dir=repo.parent) as probe:
        junit = Path(probe.name)
    try:
        run = subprocess.run(
            ["/usr/bin/python3", "-m", "pytest", "-q", f"--junitxml={junit}",
             *node_ids],
            cwd=str(repo), capture_output=True, text=True, check=False, timeout=600,
            env=env,
        )
        tail = run.stdout.strip().splitlines()[-1] if run.stdout.strip() else ""
        return run.returncode == 0, tail[:120]
    finally:
        junit.unlink(missing_ok=True)


def train_github(url: str, rev: str, max_ids: int, wanted: list[str],
                 record: dict) -> list[dict[str, Any]]:
    """Fetch, measure, and run the labelled exercise set; -> example rows."""
    unknown = [v for v in wanted if v not in GITHUB_VARIANTS]
    if unknown:
        raise ValueError(f"github variants are {GITHUB_VARIANTS}; got {unknown}")
    with tempfile.TemporaryDirectory(prefix="ranex-trainer-gh-") as tmp:
        scratch = Path(tmp)
        repo_dir, sha = clone_pinned(url, rev, scratch / "repo")
        record["github"] = {"url": url, "rev": rev, "commit": sha,
                            "max_ids": max_ids}
        # Labels must be measured under the GOVERNED-equivalent env, not the
        # trainer's inherited shell env: `ranex run` confines the child
        # (pinned PATH, scratch HOME/TMPDIR, LANG=C.UTF-8), and a baseline
        # that is only green under our shell would false-diverge the gold
        # variant under governance (review P1-6).
        from trainer.governed import governed_equivalent_env

        env = governed_equivalent_env(scratch)
        node_ids = collect_node_ids(repo_dir, max_ids, env)
        record["github"]["node_ids"] = node_ids
        green, tail = baseline_green(repo_dir, node_ids, env)
        record["github"]["baseline_green"] = green
        record["github"]["baseline_tail"] = tail
        if not green:
            return [{"variant": "baseline", "task": url, "skipped":
                     f"baseline not green under pinned interpreter: {tail}",
                     "agree": None}]

        # Shape a task_dir the governed runner understands: repo/ (tests live
        # inside it), no separate hidden-tests dir, no gold patch — pristine
        # HEAD is the solution.
        import shutil

        task_dir = scratch / "task"
        (task_dir / "repo").mkdir(parents=True)
        shutil.copytree(repo_dir, task_dir / "repo",
                        ignore=shutil.ignore_patterns(".git"),
                        dirs_exist_ok=True)

        examples: list[dict[str, Any]] = []
        for variant in wanted:
            out = scratch / variant
            try:
                example = variants.run_exercise(
                    variant, task_dir, out, node_ids, gold_patch=None)
            except Exception as exc:  # noqa: BLE001 — a failed build is data
                example = {"variant": variant, "task": url, "actual_gate": "ERROR",
                           "expected_gate": "PASS" if variant == "gold" else "FAIL",
                           "agree": False,
                           "error": f"{type(exc).__name__}: {exc}"[:300]}
            if not example.get("skipped"):
                example["task"] = f"github:{url.split('/')[-1]}@{sha[:8]}"
                example["classes"] = variants.classes_for(example) + [
                    "corpus/github-real-enterprise"]
            examples.append(example)
            mark = ("SKIP" if example.get("skipped")
                    else ("agree" if example.get("agree") else "DIVERGE"))
            print(f"  {mark:<8} {example['task'][:44]:<44} {variant}", flush=True)
        return examples
