#!/usr/bin/env python3
"""#114 ceremony: prove the two-arm benchmark's bare arm is actually bare.

Real live data only (#95 protocol): every arm below is a real subprocess of
the real driver (tools/dogfood/oss_bench/two_arm.py) with the checkout's
venv interpreter, against the real pinned VulcanBench task. Scratch trees —
task repo copies, governed repos, per-run Ed25519 keys — live under /tmp and
are discarded; only JSON artifacts and their sha256 digests are retained.

Phases (ORDER MATTERS — before must run against the pre-change driver):

  --phase before   3x full two-arm runs on the pinned task using the
                   PRE-CHANGE driver bytes (run this before editing
                   two_arm.py; the driver sha256 is recorded per run).
  --phase after    3x full runs with the new driver, plus 3x each
                   negative-control flavor (deliberate contamination that
                   must be caught).
  --phase receipt  assemble receipt.json + commands.json from the retained
                   artifacts; statuses are the #95 vocabulary.

Arms (issue #114):
  1 contamination probe   bare env measured IN-CHILD, findings empty, 3x
  2 negative control      pythonpath / ranex-var / vendored-path each caught 3x
  3 governed unaffected   governed arms byte-identical before/after (elapsed
                          zeroed — timing is the only permitted variation)
  4 real task both arms   bare ground truth + governed verdicts + journals,
                          both environments retained
  5 env digests stable    identical environment digests per arm across 3x
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RANEX_REPO = HERE.parents[1]
RANEX_PY = RANEX_REPO / ".venv" / "bin" / "python"
TWO_ARM = HERE / "oss_bench" / "two_arm.py"
DEFAULT_TASK = "py-txn-kvstore"
FLAVORS = ("pythonpath", "ranex-var", "vendored-path")
SEVERITY = {"VERIFIED": 0, "UNVERIFIED": 1, "GAP": 2,
            "NON-DETERMINISTIC": 3, "FALSE-PASS": 4}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_commands(audit: Path) -> list[dict]:
    path = audit / "commands.json"
    if path.is_file():
        return json.loads(path.read_text())
    return []


def save_commands(audit: Path, commands: list[dict]) -> None:
    (audit / "commands.json").write_text(json.dumps(commands, indent=1) + "\n")


def record(audit: Path, argv: list[str], cwd: Path,
           result: subprocess.CompletedProcess[str], wall_ms: float,
           driver_sha: str) -> None:
    commands = load_commands(audit)
    commands.append({
        "argv": argv, "cwd": str(cwd), "exit": result.returncode,
        "wall_ms": round(wall_ms, 1),
        "stdout": result.stdout[-600:], "stderr": result.stderr[-600:],
        "driver_sha256": driver_sha,
    })
    save_commands(audit, commands)


def run_driver(audit: Path, extra: list[str]) -> subprocess.CompletedProcess[str]:
    driver_sha = sha256_file(TWO_ARM)
    argv = [str(RANEX_PY), str(TWO_ARM), *extra]
    started = time.perf_counter()
    result = subprocess.run(argv, cwd=str(RANEX_REPO), capture_output=True,
                            text=True, check=False)
    record(audit, argv, RANEX_REPO, result,
           (time.perf_counter() - started) * 1000.0, driver_sha)
    print(f"exit {result.returncode}: {' '.join(extra)}")
    if result.stdout.strip():
        print(result.stdout.strip()[-400:])
    return result


def retain(scratch: Path, dest: Path, names: tuple[str, ...]) -> list[str]:
    """Copy named artifacts from a scratch run into the audit tree."""

    kept = []
    dest.mkdir(parents=True, exist_ok=True)
    for name in names:
        source = scratch / name
        if source.is_file():
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            kept.append(name)
    return kept


def normalized_governed(validation: Path) -> bytes:
    """validation.json with elapsed_s zeroed — timing is the only permitted
    variation (#95 anti-flake rule); everything else must be byte-stable."""

    report = json.loads(validation.read_text())
    for arm in report.get("arms", []):
        arm["elapsed_s"] = 0.0
    return json.dumps(report, indent=2, sort_keys=True).encode()


def phase_before(audit: Path, task: str) -> None:
    for run in (1, 2, 3):
        with tempfile.TemporaryDirectory(prefix=f"ranex-114-before-{run}-") as tmp:
            out = Path(tmp) / "out"
            result = run_driver(audit, ["--task", task, "--mode", "tasks",
                                        "--out", str(out)])
            if result.returncode != 0:
                print(f"before run {run}: driver exit {result.returncode} — "
                      "recorded; the receipt will carry it", file=sys.stderr)
            names = ("validation.json", "bare_ground_truth.json")
            kept = retain(out, audit / "arms" / "3-governed-unaffected"
                          / "before" / f"run{run}", names)
            print(f"retained: {kept}")


def phase_after(audit: Path, task: str, full_only: bool = False) -> None:
    if not full_only:
        for flavor in FLAVORS:
            for run in (1, 2, 3):
                with tempfile.TemporaryDirectory(
                        prefix=f"ranex-114-negative-{flavor}-") as tmp:
                    out = Path(tmp) / "out"
                    result = run_driver(
                        audit, ["--task", task, "--mode", "tasks",
                                "--out", str(out), "--contaminate", flavor])
                    finding = {"argv_flavor": flavor,
                               "exit": result.returncode,
                               "stderr": result.stderr.strip()[-400:],
                               "ground_truth_written":
                                   (out / "bare_ground_truth.json").is_file()}
                    dest = audit / "arms" / "2-negative-control" / flavor
                    dest.mkdir(parents=True, exist_ok=True)
                    (dest / f"run{run}.json").write_text(
                        json.dumps(finding, indent=1) + "\n")
    for run in (1, 2, 3):
        with tempfile.TemporaryDirectory(prefix=f"ranex-114-after-{run}-") as tmp:
            out = Path(tmp) / "out"
            result = run_driver(audit, ["--task", task, "--mode", "tasks",
                                        "--out", str(out)])
            if result.returncode != 0:
                print(f"after run {run}: driver exit {result.returncode} — "
                      "recorded; the receipt will carry it", file=sys.stderr)
            names = ("validation.json", "bare_ground_truth.json",
                     "gold/governed_environment.json",
                     "empty/governed_environment.json")
            kept = retain(out, audit / "arms" / "4-real-task" / f"run{run}",
                          names)
            print(f"retained: {kept}")


def _arm1(audit: Path) -> str:
    """Contamination probe: in-child findings empty, environment recorded."""
    runs = sorted((audit / "arms" / "4-real-task").glob("run*/bare_ground_truth.json"))
    if len(runs) != 3:
        return "GAP"
    digests, ok = set(), True
    for path in runs:
        environment = json.loads(path.read_text()).get("environment", {})
        if not environment or environment.get("contamination_findings") != []:
            ok = False
            continue
        if environment.get("probes", 0) < 1 or "child_env" not in environment:
            ok = False
            continue
        digests.add(environment["child_env_sha256"])
    if not ok:
        return "GAP"
    if len(digests) != 1:
        return "NON-DETERMINISTIC"
    return "VERIFIED"


def _arm2(audit: Path) -> str:
    """Negative control: every deliberate contamination is caught, 3x each."""
    statuses = []
    for flavor in FLAVORS:
        for run in (1, 2, 3):
            path = audit / "arms" / "2-negative-control" / flavor / f"run{run}.json"
            if not path.is_file():
                statuses.append("GAP")
                continue
            finding = json.loads(path.read_text())
            caught = (finding["exit"] == 3
                      and "BARE-ARM-CONTAMINATED" in finding["stderr"]
                      and finding["ground_truth_written"] is False)
            statuses.append("VERIFIED" if caught else "FALSE-PASS")
    return max(statuses, key=lambda s: SEVERITY[s])


def _arm3(audit: Path) -> str:
    """Governed arm unaffected: byte-identical (elapsed zeroed) before/after."""

    def digests(side: str) -> set[str]:
        found = set()
        if side == "before":
            paths = sorted((audit / "arms" / "3-governed-unaffected" / side
                           ).glob("run*/validation.json"))
        else:
            paths = sorted((audit / "arms" / "4-real-task"
                           ).glob("run*/validation.json"))
        for path in paths:
            found.add(hashlib.sha256(normalized_governed(path)).hexdigest())
        return found

    before, after = digests("before"), digests("after")
    if not before or not after:
        return "GAP"
    if len(before) > 1 or len(after) > 1:
        return "NON-DETERMINISTIC"
    return "VERIFIED" if before == after else "GAP"


def _arm4(audit: Path) -> str:
    """Real task, both arms: ground truth + governed verdicts + environments."""
    runs = sorted((audit / "arms" / "4-real-task").glob("run*"))
    if len(runs) != 3:
        return "GAP"
    for run in runs:
        ground = json.loads((run / "bare_ground_truth.json").read_text())
        gold_bare = [entry["exit"] for entry in ground["gold"]]
        empty_bare = [entry["exit"] for entry in ground["empty"]]
        if not gold_bare or any(code != 0 for code in gold_bare):
            return "GAP"
        if not empty_bare or any(code == 0 for code in empty_bare):
            return "GAP"
        validation = json.loads((run / "validation.json").read_text())
        arms = {arm["arm"]: arm for arm in validation["arms"]}
        if arms["gold"]["gate_verdict"] != "PASS":
            return "GAP"
        if arms["empty"]["gate_verdict"] != "FAIL":
            return "GAP"
        if not all(arm["journal_verified"] for arm in arms.values()):
            return "GAP"
        for governed in ("gold", "empty"):
            if not (run / governed / "governed_environment.json").is_file():
                return "GAP"
        if "environment" not in ground:
            return "GAP"
    return "VERIFIED"


def _arm5(audit: Path) -> str:
    """3x repeats: identical environment digests per arm."""
    runs = list((audit / "arms" / "4-real-task").glob("run*"))
    if len(runs) != 3:
        return "GAP"
    bare = {sha256_file(path) for path in
            (audit / "arms" / "4-real-task").glob("run*/bare_ground_truth.json")}
    embedded = set()
    for path in (audit / "arms" / "4-real-task").glob(
            "run*/bare_ground_truth.json"):
        environment = json.loads(path.read_text()).get("environment", {})
        embedded.add(environment.get("child_env_sha256"))
    governed = {}
    for path in (audit / "arms" / "4-real-task").glob(
            "run*/*/governed_environment.json"):
        governed.setdefault(path.parent.name, set()).add(sha256_file(path))
    if len(bare) != 1 or len(embedded) != 1:
        return "NON-DETERMINISTIC"
    if sorted(governed) != ["empty", "gold"]:
        return "GAP"
    if any(len(digests) != 1 for digests in governed.values()):
        return "NON-DETERMINISTIC"
    return "VERIFIED"


def phase_receipt(audit: Path) -> int:
    arms = {
        "1-contamination-probe": _arm1(audit),
        "2-negative-control": _arm2(audit),
        "3-governed-unaffected": _arm3(audit),
        "4-real-task-both-arms": _arm4(audit),
        "5-env-digests-stable": _arm5(audit),
    }
    overall = max(arms.values(), key=lambda s: SEVERITY[s])
    receipt = {
        "issue": "anthonykewl20/ranex#114",
        "protocol": "#95 — real subprocesses of the real driver on the real "
                    "pinned VulcanBench task, no mocks, 3x repeats, "
                    "VERIFIED/GAP/FALSE-PASS/NON-DETERMINISTIC/UNVERIFIED",
        "task": DEFAULT_TASK,
        "driver": {
            "before_sha256": None,  # filled from commands.json below
            "after_sha256": None,
        },
        "arm_statuses": arms,
        "overall": overall,
        "host": {
            "node": platform.node(),
            "python": sys.version.split()[0],
            "release": platform.release(),
            "system": platform.system(),
        },
        "kernel_commit": subprocess.run(
            ["git", "-C", str(RANEX_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False).stdout.strip(),
        "limitations": [
            "The venv interpreter stays first on the bare PATH by design (the "
            "deliberate bare-agent choice from the adapter's origin); the "
            "control proves it carries no RANEX_* variable, no kernel-naming "
            "PYTHONPATH, and no vendored kernel directory on PATH",
            "governed_environment.json retains variable NAMES plus the two "
            "governance values and a digest, not full ambient values, so no "
            "operator secret is committed",
        ],
    }
    commands = load_commands(audit)
    if commands:
        receipt["driver"]["before_sha256"] = commands[0]["driver_sha256"]
        receipt["driver"]["after_sha256"] = commands[-1]["driver_sha256"]
    (audit / "receipt.json").write_text(json.dumps(receipt, indent=1) + "\n")
    print(json.dumps(arms, indent=1))
    print(f"overall: {overall}  receipt: {audit / 'receipt.json'}")
    return 0 if overall == "VERIFIED" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--task", default=DEFAULT_TASK)
    parser.add_argument("--phase",
                        choices=("before", "after", "after-full", "receipt"),
                        required=True)
    args = parser.parse_args()
    audit = args.audit_dir.resolve()
    audit.mkdir(parents=True, exist_ok=True)
    if args.phase == "before":
        phase_before(audit, args.task)
    elif args.phase in ("after", "after-full"):
        # after-full continues just the full-run half after an interrupted
        # phase (negative-control records already retained stay as-is)
        phase_after(audit, args.task, full_only=args.phase == "after-full")
    else:
        return phase_receipt(audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
