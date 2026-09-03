#!/usr/bin/env python3
"""Two-arm ranex-vs-bare adapter over REAL VulcanBench tasks.

Arm semantics (both arms run the task's own hidden-test commands against
the task's own real repo):

  bare      — the commands run; a bare agent's "done" is its own claim.
  governed  — the same repo carries vendored ranex + committed governance;
              each test command runs under `ranex run` producing SIGNED
              evidence; `gate evaluate` decides; the journal chain must
              verify.

TWO verified integration facts shape this adapter (F-003):
  1. governed_repository_root() resolves the repo containing the CLI, so the
     ranex source is VENDORED into the task repo (committed) and the CLI is
     run with PYTHONPATH=<task-repo>/src — the kernel's own
     clone-judges-clone model.
  2. `ranex run` resolves argv[0] only through the pinned toolchain
     (/usr/bin, /bin, /usr/sbin, /sbin). Task commands naming `python` need
     a pinned interpreter WITH pytest: PREREQUISITE, checked honestly here.

MODES:
  --mode tasks     the real two-arm study (requires the pinned-python
                   pytest prerequisite; refuses to invent results without it)
  --mode plumbing  end-to-end pipeline proof on the real task repo using a
                   genuinely pinned tool (`git`) — proves vendoring, run,
                   signed evidence, gate verdict, journal verification.
                   NOT a benchmark result; never publish it as one.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

RANEX_REPO = Path("/home/soultransit/devtony/ranex")
RANEX_PY = RANEX_REPO / ".venv" / "bin" / "python"
DEFAULT_VULCAN = Path("/home/soultransit/devtony/VulcanBench")

sys.path.insert(0, str(RANEX_REPO / "src"))
from ranex.foundation.signing import generate_keypair  # noqa: E402

APPROVER = "oss-bench-approver"
PRODUCER = "oss-bench-producer"


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=bench@ranex.invalid",
         "-c", "user.name=ranex-oss-bench", *args],
        capture_output=True, text=True, check=False,
    )


def pinned_python_has_pytest() -> tuple[bool, str]:
    """The real prerequisite, checked against the real pin."""
    candidates = [Path("/usr/bin/python3"), Path("/bin/python3")]
    for candidate in candidates:
        if not candidate.exists():
            continue
        probe = subprocess.run(
            [str(candidate), "-c", "import pytest"], capture_output=True,
            text=True, check=False,
        )
        if probe.returncode == 0:
            return True, str(candidate)
        return False, (
            f"{candidate} (the pinned interpreter) cannot import pytest — "
            "install it system-wide (e.g. `sudo apt install python3-pytest`) "
            "or run this study on a machine where the pinned python has pytest"
        )
    return False, "no pinned python found in /usr/bin or /bin"


def build_governed_repo(task_dir: Path, out: Path, apply_gold: bool,
                        claim_commands: list[tuple[str, list[str]]]) -> tuple[Path, str]:
    """Task repo + hidden tests (+gold) + VENDORED ranex + governance, committed."""
    repo = out / "repo"
    repo.mkdir(parents=True)
    for item in (task_dir / "repo").iterdir():
        if item.is_dir():
            shutil.copytree(item, repo / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, repo / item.name)
    tests_dir = task_dir / "tests"
    if tests_dir.is_dir():
        for item in tests_dir.iterdir():
            if (repo / item.name).exists():
                raise AssertionError(f"hidden test collides with repo file: {item.name}")
            shutil.copy2(item, repo / item.name)

    if apply_gold:
        result = subprocess.run(
            ["git", "-C", str(repo), "apply", str(task_dir / "gold_patch.diff")],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"gold patch failed to apply: {result.stderr}")

    assert _git(repo, "init", "-q").returncode == 0
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm",
                "task base (+gold)" if apply_gold else "task base").returncode == 0

    # Vendor the kernel source: the CLI governs the repo that CONTAINS it.
    shutil.copytree(RANEX_REPO / "src", repo / "src", dirs_exist_ok=True)
    shutil.copy2(RANEX_REPO / "pyproject.toml", repo / "pyproject.toml")
    shutil.copy2(RANEX_REPO / "uv.lock", repo / "uv.lock")

    private, public = generate_keypair()
    (out / "keys").mkdir(exist_ok=True)
    key_path = out / "keys" / "bench.key"
    key_path.write_text(private)
    key_path.chmod(0o600)

    claims_yaml = "".join(
        "      - claim_id: {}\n        command: [{}]\n".format(
            claim_id, ", ".join(json.dumps(part) for part in argv))
        for claim_id, argv in claim_commands
    )
    (repo / "governance").mkdir(exist_ok=True)
    (repo / "governance" / "producers.yaml").write_text(
        "producers:\n  {}: {}\n".format(PRODUCER, public))
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TASK_TESTS\n    blocking: true\n"
        "    required_claims:\n" + claims_yaml)
    (repo / "governance" / "evidence.json").write_text("[]\n")
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm",
                "vendor ranex kernel; governance: bench keyring and task gate").returncode == 0
    return repo, str(key_path)


def _ranex(repo: Path, key_path: str, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["RANEX_SIGNING_KEY"] = key_path
    env["PYTHONPATH"] = str(repo / "src")
    return subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", *args],
        cwd=str(repo), env=env, capture_output=True, text=True, check=False,
        timeout=600,
    )


def governed_cycle(repo: Path, key_path: str,
                   claim_commands: list[tuple[str, list[str]]]) -> dict[str, Any]:
    runs = []
    for claim_id, argv in claim_commands:
        result = _ranex(repo, key_path, "run", "--claim", claim_id,
                        "--producer", PRODUCER, "--", *argv)
        runs.append({"claim": claim_id, "exit": result.returncode,
                     "error": (result.stderr.strip()[-300:]
                               if result.returncode != 0 else "")})
    verdict = _ranex(repo, key_path, "gate", "evaluate", "HEAD",
                     "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    journal = _ranex(repo, key_path, "journal", "verify",
                     "--journal", "governance/journal.sqlite3")
    gate_pass = verdict.returncode == 0 and "FAIL" not in verdict.stdout
    journal_ok = journal.returncode == 0 and "verified" in journal.stdout
    return {"runs": runs, "gate_verdict": "PASS" if gate_pass else "FAIL",
            "gate_output": verdict.stdout.strip()[:400] + verdict.stderr.strip()[-200:],
            "journal_verified": journal_ok}


def mode_plumbing(task_dir: Path, out: Path) -> dict[str, Any]:
    """Pipeline proof with a genuinely pinned tool. Positive repo: `git
    --version` claim -> expect gate PASS. Negative repo: claim bound to a
    failing real command (`git rev-parse --verify definitely-missing-ref`)
    -> expect gate FAIL. Real commands, real verdicts, zero task results."""
    started = time.perf_counter()
    positive_claims = [("plumbing-pass", ["git", "--version"])]
    negative_claims = [("plumbing-pass", ["git", "rev-parse", "--verify",
                                          "definitely-missing-ref-0000000"])]

    repo_pos, key_pos = build_governed_repo(task_dir, out / "positive",
                                            apply_gold=False,
                                            claim_commands=positive_claims)
    pos = governed_cycle(repo_pos, key_pos, positive_claims)
    repo_neg, key_neg = build_governed_repo(task_dir, out / "negative",
                                            apply_gold=False,
                                            claim_commands=negative_claims)
    neg = governed_cycle(repo_neg, key_neg, negative_claims)

    report = {
        "schema": "ranex-oss-bench-plumbing-v1",
        "task": task_dir.name,
        "note": "pipeline validation on a real task repo via pinned git; "
                "NOT a benchmark result",
        "positive": pos, "negative": neg,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }
    ok = (pos["gate_verdict"] == "PASS" and pos["journal_verified"]
          and neg["gate_verdict"] == "FAIL" and neg["journal_verified"])
    report["validation"] = "PASS" if ok else "FAIL"
    (out / "plumbing.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"plumbing: positive gate {pos['gate_verdict']} (journal "
          f"{'verified' if pos['journal_verified'] else 'BROKEN'}), "
          f"negative gate {neg['gate_verdict']} (journal "
          f"{'verified' if neg['journal_verified'] else 'BROKEN'}) -> "
          f"VALIDATION {report['validation']}")
    return report


def mode_tasks(task_dir: Path, out: Path) -> int:
    ok, detail = pinned_python_has_pytest()
    if not ok:
        print(f"PREREQUISITE-MISSING: {detail}")
        print("The governed arm refuses to run without it; no results are "
              "invented. The bare arm still runs for ground truth.")
    metadata = json.loads((task_dir / "metadata.json").read_text())
    entries = metadata["tests"]["fail_to_pass"]

    # Bare arm always runs: real ground truth from the task's own commands,
    # using the ranex venv interpreter (ambient; exactly what a bare agent
    # would use — no governance).
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        bare_repo = Path(tmp) / "repo"
        shutil.copytree(task_dir / "repo", bare_repo)
        for item in (task_dir / "tests").iterdir():
            shutil.copy2(item, bare_repo / item.name)
        gold = subprocess.run(
            ["git", "-C", str(bare_repo), "apply", str(task_dir / "gold_patch.diff")],
            capture_output=True, text=True, check=False)
        bare_gold, bare_empty = [], []
        env = dict(os.environ)
        env["PATH"] = f"{RANEX_PY.parent}:{env.get('PATH', '')}"
        targets = [("gold", bare_gold, gold.returncode == 0),
                   ("empty", bare_empty, True)]
        for arm, sink, _ in targets:
            for entry in entries:
                if arm == "empty":
                    subprocess.run(["git", "-C", str(bare_repo), "checkout", "--", "."],
                                   capture_output=True, check=False)
                    subprocess.run(["git", "-C", str(bare_repo), "clean", "-fdq"],
                                   capture_output=True, check=False)
                    shutil.rmtree(bare_repo)
                    shutil.copytree(task_dir / "repo", bare_repo)
                    for item in (task_dir / "tests").iterdir():
                        shutil.copy2(item, bare_repo / item.name)
                result = subprocess.run(shlex.split(entry["cmd"]), cwd=str(bare_repo),
                                        capture_output=True, text=True, check=False,
                                        timeout=300, env=env)
                sink.append({"name": entry["name"], "exit": result.returncode})
        print(f"[gold ] bare {sum(1 for r in bare_gold if r['exit'] == 0)}/{len(entries)}")
        print(f"[empty] bare {sum(1 for r in bare_empty if r['exit'] == 0)}/{len(entries)}")
        (out / "bare_ground_truth.json").write_text(json.dumps({
            "schema": "ranex-oss-bench-bare-v1", "task": metadata["id"],
            "gold": bare_gold, "empty": bare_empty}, indent=2) + "\n")

    if not ok:
        return 4

    claim_commands = []
    for entry in entries:
        argv = shlex.split(entry["cmd"])
        argv[0] = "/usr/bin/python3" if argv[0] == "python" else argv[0]
        claim_commands.append((entry["name"], argv))
    arms = []
    for arm, apply_gold in (("gold", True), ("empty", False)):
        started = time.perf_counter()
        repo, key_path = build_governed_repo(task_dir, out / arm, apply_gold,
                                             claim_commands)
        cycle = governed_cycle(repo, key_path, claim_commands)
        arms.append({"arm": arm, "gate_verdict": cycle["gate_verdict"],
                     "journal_verified": cycle["journal_verified"],
                     "runs": cycle["runs"],
                     "elapsed_s": round(time.perf_counter() - started, 3),
                     "simulation": "gold-patch (no model) — NOT a model benchmark"})
        print(f"[{arm:5}] gate {arms[-1]['gate_verdict']} · journal "
              f"{'verified' if arms[-1]['journal_verified'] else 'BROKEN'} · "
              f"{arms[-1]['elapsed_s']}s")
    report = {"schema": "ranex-oss-bench-validation-v1", "task": metadata["id"],
              "arms": arms}
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    valid = arms[0]["gate_verdict"] == "PASS" and arms[1]["gate_verdict"] == "FAIL" \
        and all(a["journal_verified"] for a in arms)
    print("VALIDATION", "PASS" if valid else "FAIL")
    return 0 if valid else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--suite", default="v1")
    parser.add_argument("--mode", choices=("tasks", "plumbing"), default="tasks")
    parser.add_argument("--vulcan-root", type=Path, default=DEFAULT_VULCAN)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    task_dir = args.vulcan_root / "tasks" / args.suite / args.task
    if not task_dir.is_dir():
        print(f"no such task: {task_dir}", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    if args.mode == "plumbing":
        report = mode_plumbing(task_dir, args.out)
        return 0 if report["validation"] == "PASS" else 1
    return mode_tasks(task_dir, args.out)


if __name__ == "__main__":
    raise SystemExit(main())
