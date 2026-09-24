#!/usr/bin/env python3
"""#113 proof — instrument self-test, all nine arms on real invocations.

Real `python`/`ranex` subprocesses against the real drivers and the real lane
admission machinery; no mocks, keys generated per run and discarded, receipts
committed (#95 protocol). Arms 1-5 are the issue body; arms 6-9 are the added
lock scope, proven against the shipped `lane.py` — the acquire is taken by the
operation running under its lane, which is the design that replaced
pattern-matching on command strings.

Run from the kernel checkout with its venv interpreter:

    .venv/bin/python tools/dogfood/selftest_probe.py

Writes tools/dogfood/audits/2026-09-24-selftest/ (receipt.json, arms/*.json,
commands.json).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

KERNEL = Path(__file__).resolve().parents[2]
PY = KERNEL / ".venv" / "bin" / "python"
RANEX = KERNEL / ".venv" / "bin" / "ranex"
TOOL_DIR = KERNEL / "tools" / "dogfood"
AUDIT = TOOL_DIR / "audits" / "2026-09-24-selftest"
LANE = TOOL_DIR / "lane.py"
REPEATS = 3
STARTED = time.monotonic()

COMMANDS: list[dict[str, Any]] = []


def run(argv: list[str], cwd: Path = KERNEL, *, env: dict[str, str] | None = None,
        timeout: int = 900) -> subprocess.CompletedProcess[str]:
    started = time.monotonic()
    completed = subprocess.run(
        [str(part) for part in argv], cwd=str(cwd), env=env,
        capture_output=True, text=True, check=False, timeout=timeout,
    )
    COMMANDS.append({
        "argv": [str(part) for part in argv],
        "cwd": str(cwd),
        "exit": completed.returncode,
        "wall_ms": round((time.monotonic() - started) * 1000.0, 1),
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-2000:],
    })
    return completed


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_arm(payload: dict[str, Any]) -> None:
    slug = (payload["arm"].replace(" ", "-").replace("+", "-and-")
            .replace("(", "").replace(")", "").replace(",", "")
            .replace(":", "").lower())
    (AUDIT / "arms" / f"{slug}.json").write_text(
        json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    (AUDIT / "commands.json").write_text(json.dumps(COMMANDS, indent=1),
                                         encoding="utf-8")


# --- arms 1 and 5: every instrument proves itself, three byte-identical times --

#: The three instrument drivers, invoked exactly as an operator would. argv is
#: held IDENTICAL across the three repeats (same --out), because the receipt
#: records argv and byte-identity is the arm-5 assertion; the receipt is moved
#: aside between repeats.
DRIVERS: dict[str, list[str]] = {
    "marker-scanner": [str(PY), str(TOOL_DIR / "markers_probe.py"), "--selftest",
                       "--audit-dir", ""],
    "release-audit": [str(PY), str(TOOL_DIR / "release_audit.py"), "--selftest",
                      "--out", ""],
    "receiver-audit": [str(PY), str(TOOL_DIR / "receiver_audit.py"), "--selftest",
                       "--out", ""],
}


def arm1_and_5() -> dict[str, Any]:
    """Good reference passes, bad reference is caught, for every instrument,
    on 3 repeats; the receipts are byte-identical."""

    rows: dict[str, Any] = {"arm": "1+5-instruments-prove-themselves"}
    for instrument, template in DRIVERS.items():
        target = AUDIT / "arms" / f"1-{instrument}"
        target.mkdir(parents=True, exist_ok=True)
        workspace = target / "run"
        argv = template[:-1] + [str(workspace)]
        digests: list[str] = []
        for repeat in range(1, REPEATS + 1):
            shutil.rmtree(workspace, ignore_errors=True)
            completed = run(argv)
            if completed.returncode != 0:
                rows[instrument] = {
                    "status": "GAP",
                    "why": f"repeat {repeat} exited {completed.returncode}",
                    "output": (completed.stdout + completed.stderr)[-500:],
                }
                return rows
            receipt = workspace / "selftest" / "selftest.json"
            digests.append(sha256_file(receipt))
            shutil.copyfile(receipt, target / f"repeat-{repeat}.json")
        shutil.rmtree(workspace, ignore_errors=True)
        payload = json.loads((target / "repeat-1.json").read_bytes())
        row = next(item for item in payload["instruments"]
                   if item["instrument"] == instrument)
        rows[instrument] = {
            "argv": argv,
            "repeat_digests": digests,
            "byte_identical": len(set(digests)) == 1,
            "status": row["status"],
            "good": {"digest": row["good"]["digest"], "outcome": row["good"]["outcome"]},
            "bad": {"digest": row["bad"]["digest"], "outcome": row["bad"]["outcome"]},
            "sides_identical": row["good"]["identical"] and row["bad"]["identical"],
        }
    instruments = [row for row in rows.values() if isinstance(row, dict)]
    ok = (
        all(row["status"] == "VERIFIED" for row in instruments)
        and all(row["byte_identical"] for row in instruments)
        and all(row["good"]["outcome"] == "passed" for row in instruments)
        and all(row["bad"]["outcome"] == "caught" for row in instruments)
    )
    rows["status"] = "as-expected" if ok else "GAP"
    return rows


# --- arm 2: a broken instrument stops the run, no measurement receipt --------


def arm2() -> dict[str, Any]:
    """Blunt the marker scanner; the #95 driver must refuse before measuring.

    The absence of the measurement receipt is the assertion.
    """

    target = AUDIT / "arms" / "2-blunted-instrument-stops-the-run"
    completed = run([str(PY), str(TOOL_DIR / "calibration.py"),
                     "--out", str(target), "--blunt", "marker-scanner"])
    receipts = sorted(str(path.relative_to(target)) for path in target.rglob("*.json"))
    measurement = [name for name in receipts if name.endswith("calibration.json")]
    payload = json.loads((target / "selftest" / "selftest.json").read_bytes())
    blunt = next(item for item in payload["instruments"]
                 if item["instrument"] == "marker-scanner")
    return {
        "arm": "2-blunted-instrument-stops-the-run",
        "argv": [str(PY), str(TOOL_DIR / "calibration.py"), "--out", str(target),
                 "--blunt", "marker-scanner"],
        "exit": completed.returncode,
        "refusal": (completed.stdout + completed.stderr).strip().splitlines()[-1],
        "blunt_status": blunt["status"],
        "receipts_written": receipts,
        "measurement_receipt_absent": not measurement,
        "status": "as-expected"
        if completed.returncode == 1 and blunt["status"] == "FALSE-PASS"
        and not measurement else "GAP",
    }


# --- arm 3: a self-test that cannot fail is refused ---------------------------


def arm3() -> dict[str, Any]:
    """An instrument whose bad reference also passes is FALSE-PASS, not
    VERIFIED — for a blunted judgment (release-audit, receiver-audit) as well
    as a blunted scanner (marker-scanner, proven in arm 2)."""

    rows: dict[str, Any] = {"arm": "3-cannot-fail-is-refused"}
    for instrument in ("release-audit", "receiver-audit"):
        target = AUDIT / "arms" / f"3-false-pass-{instrument}"
        completed = run([str(PY), str(TOOL_DIR / "selftest.py"),
                         "--out", str(target), "--blunt", instrument])
        # The standalone runner writes its receipt directly into --out; the
        # drivers nest it under <out>/selftest because they pass that path in.
        payload = json.loads((target / "selftest.json").read_bytes())
        row = next(item for item in payload["instruments"]
                   if item["instrument"] == instrument)
        rows[instrument] = {
            "exit": completed.returncode,
            "status": row["status"],
            "bad_outcome": row["bad"]["outcome"],
            "overall": payload["overall"],
        }
    entries = [row for row in rows.values() if isinstance(row, dict)]
    ok = all(
        entry["exit"] == 1 and entry["status"] == "FALSE-PASS"
        and entry["bad_outcome"] == "accepted"
        for entry in entries
    )
    rows["status"] = "as-expected" if ok else "GAP"
    return rows


# --- arm 4: ordering is enforced, not documented -------------------------------


def arm4() -> dict[str, Any]:
    """Skip the self-test on a measurement run: the driver refuses, and the
    output directory stays empty. Beside it, the same driver with the
    self-test passing produces the measurement receipt in the same run — the
    pairing that makes the absence in arm 2 meaningful."""

    target = AUDIT / "arms" / "4-skip-refused"
    completed = run([str(PY), str(TOOL_DIR / "calibration.py"),
                     "--out", str(target), "--skip-selftest"])
    skip_empty = not target.exists() or not any(
        path.is_file() for path in target.rglob("*"))

    wired = AUDIT / "arms" / "4-wired-clean"
    clean = run([str(PY), str(TOOL_DIR / "calibration.py"), "--out", str(wired)])
    measurement = wired / "calibration.json"
    payload = json.loads((wired / "selftest" / "selftest.json").read_bytes())
    cases = json.loads(measurement.read_bytes()) if measurement.exists() else {}
    return {
        "arm": "4-ordering-enforced",
        "skip": {
            "argv": [str(PY), str(TOOL_DIR / "calibration.py"), "--out", str(target),
                     "--skip-selftest"],
            "exit": completed.returncode,
            "refusal": (completed.stdout + completed.stderr).strip().splitlines()[-1],
            "directory_empty": skip_empty,
        },
        "wired_clean": {
            "argv": [str(PY), str(TOOL_DIR / "calibration.py"), "--out", str(wired)],
            "exit": clean.returncode,
            "selftest_overall": payload["overall"],
            "measurement_receipt": measurement.name if measurement.exists() else None,
            "worst": cases.get("worst"),
        },
        "status": "as-expected"
        if completed.returncode == 1 and skip_empty and clean.returncode == 0
        and measurement.exists() and payload["overall"] == "VERIFIED" else "GAP",
    }


# --- arms 6-9: the host lane machinery -----------------------------------------


class Lane:
    """The real lane admission, isolated to a probe-owned lane directory.

    The lock's scope is the host, so the probe drives the shipped machinery
    (pid+boot liveness, refusal, self-healing) through its public CLI with a
    private registry — exactly how #117's race probe isolated its contenders.
    """

    def __init__(self, root: Path) -> None:
        self.dir = root / "lanes"
        self.dir.mkdir(parents=True)
        self.env = {**os.environ, "RANEX_LANE_DIR": str(self.dir)}
        self._holders: list[subprocess.Popen] = []

    def run(self, command: list[str], *, timeout: int = 120
            ) -> subprocess.CompletedProcess[str]:
        return run([str(PY), str(LANE), "run", "--kind", "verify", "--", *command],
                   env=self.env, timeout=timeout)

    def holders(self) -> list[dict[str, Any]]:
        listed = run([str(PY), str(LANE), "status", "--json"], env=self.env)
        return json.loads(listed.stdout)

    def hold(self, seconds: int = 30) -> subprocess.Popen:
        process = subprocess.Popen(
            [str(PY), str(LANE), "run", "--kind", "verify", "--", "sleep", str(seconds)],
            env=self.env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self._holders.append(process)
        return process

    def wait_until_held(self, count: int, *, timeout: float = 20.0) -> None:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if len(self.holders()) >= count:
                return
            time.sleep(0.1)
        raise TimeoutError(f"lane never reported {count} holders")

    def release_all(self) -> None:
        for process in self._holders:
            if process.poll() is None:
                process.terminate()
        for process in self._holders:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        self._holders.clear()


def _build_governed(repo: Path, key: Path) -> None:
    """A minimal real governed repository for the arm-8 governed child."""

    completed = run([str(RANEX), "keygen", "--producer", "selftest"],
                    cwd=repo.parent,
                    env={**os.environ, "RANEX_SIGNING_KEY": str(key)})
    public = next(token for token in completed.stdout.split()
                  if token.startswith("ed25519:"))
    spec = json.loads((TOOL_DIR / "selftest" / "references" / "release" / "good.json")
                      .read_bytes())
    (repo / "governance").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "-C", str(repo), "init", "-q", "."], check=True,
                   capture_output=True)
    (repo / ".gitignore").write_text(
        "governance/journal.sqlite3\ngovernance/evidence.json\n", encoding="utf-8")
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: SELFTEST_SANITY\n"
        "    blocking: true\n    required_claims:\n      - claim_id: scan\n"
        f"        command: {json.dumps(spec['bound_command'])}\n", encoding="utf-8")
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  selftest: {public}\nprincipals:\n  selftest:\n"
        f"    role: worker\n    keys:\n      - key: {public}\n        status: active\n",
        encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=p@i", "-c", "user.name=p",
                    "commit", "-qm", "arm8 governed subject"], check=True,
                   capture_output=True)


def arms_6_through_9(root: Path) -> list[dict[str, Any]]:
    lane = Lane(root)
    results: list[dict[str, Any]] = []
    try:
        # 6 — second run refuses, and names its holder; the no-lock negative
        # control (same command, empty lane) proceeds.
        unguarded = lane.run(["/usr/bin/true"])
        lane.hold()
        lane.hold()
        lane.wait_until_held(2)
        refused = lane.run(["/usr/bin/true"])
        holders = lane.holders()
        results.append({
            "arm": "6-second-run-refuses",
            "without_the_lock": {"exit": unguarded.returncode},
            "refused": {"exit": refused.returncode,
                        "output": (refused.stdout + refused.stderr).strip()[:400]},
            "holders_named": holders,
            "status": "as-expected"
            if unguarded.returncode == 0 and refused.returncode != 0
            and "REFUSED" in (refused.stdout + refused.stderr) and holders
            else "GAP",
        })
        lane.release_all()

        # 7 — a SIGKILLed holder (the OOM shape) breaks its own stale slot.
        holder = lane.hold()
        lane.wait_until_held(1)
        holder.send_signal(signal.SIGKILL)
        holder.wait(timeout=5)
        acquired = lane.run(["/usr/bin/true"])
        results.append({
            "arm": "7-stale-lock-breaks",
            "sigkill": "SIGKILL to the holder; no manual cleanup performed",
            "after_kill": {"exit": acquired.returncode,
                           "holders_left": lane.holders()},
            "status": "as-expected" if acquired.returncode == 0 else "GAP",
        })
        lane.release_all()

        # 8 — every spelling acquires admission: a bare suite, the freeze
        # inner-run spelling, and a governed `ranex run` child, each started
        # while the lane is held, each refused before doing any work.
        _build_governed(root / "governed", root / "arm8.key")
        lane.hold()
        lane.hold()
        lane.wait_until_held(2)
        junit = root / "arm8-junit.xml"
        spellings = {
            "bare-suite": [str(PY), "-m", "pytest", "-q",
                           "tests/unit/test_gate_verdict.py"],
            "suite-freeze-inner-run": [str(PY), "-m", "pytest", "-q",
                                       "-o", "xfail_strict=true",
                                       "-p", "ranex.foundation.pytest_xpass",
                                       f"--junitxml={junit}",
                                       "tests/unit/test_gate_verdict.py"],
            "ranex-run-governed-child": [
                str(RANEX), "run", "--claim", "scan", "--producer", "selftest",
                "--external-repository", str(root / "governed"),
                "--evidence", "governance/evidence.json",
                "--producers", "governance/producers.yaml",
                "--gate-catalog", "governance/gates.yaml",
                "--", "/usr/bin/true",
            ],
        }
        refusals: dict[str, dict[str, Any]] = {}
        for name, command in spellings.items():
            outcome = lane.run(command)
            refusals[name] = {
                "exit": outcome.returncode,
                "refusal": (outcome.stdout + outcome.stderr).strip()[:300],
                "did_no_work": (not junit.exists())
                if name == "suite-freeze-inner-run" else None,
            }
        results.append({
            "arm": "8-every-spelling-acquires",
            "note": "admission is taken by the operation under its lane — the "
                    "design that replaced pattern-matching on command strings",
            "spellings": spellings,
            "refusals": refusals,
            "status": "as-expected"
            if all(entry["exit"] != 0 and "REFUSED" in entry["refusal"]
                   for entry in refusals.values()) else "GAP",
        })
        lane.release_all()

        # 9 — a holder whose recorded boot id is not the live one is stale
        # regardless of pid: pids are reused across boots.
        forged = lane.dir / f"verify-{os.getpid()}-forged.json"
        forged.write_text(json.dumps({
            "kind": "verify", "pid": os.getpid(),
            "boot": "00000000-0000-0000-0000-000000000000",
            "started": time.time(), "detail": "forged stale boot id",
        }), encoding="utf-8")
        acquired = lane.run(["/usr/bin/true"])
        results.append({
            "arm": "9-reboot-safety",
            "forged_holder": json.loads(forged.read_bytes()) if forged.exists()
            else "cleaned",
            "live_pid_was_alive": True,
            "after_attempt": {"exit": acquired.returncode,
                              "forged_still_present": forged.exists()},
            "status": "as-expected"
            if acquired.returncode == 0 and not forged.exists() else "GAP",
        })
    finally:
        lane.release_all()
    return results


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "arms").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ranex-113-proof-") as directory:
        root = Path(directory)
        results = [
            arm1_and_5(),
            arm2(),
            arm3(),
            arm4(),
            *arms_6_through_9(root),
        ]
    for result in results:
        write_arm(result)
    statuses = {result["arm"]: result["status"] for result in results}
    ok = all(status == "as-expected" for status in statuses.values())
    receipt = {
        "issue": "anthonykewl20/ranex#113",
        "protocol": "#95 — real subprocesses, no mocks, 3x repeats where the "
                    "arm is a repeat claim, VERIFIED/GAP/FALSE-PASS/"
                    "NON-DETERMINISTIC/UNVERIFIED",
        "kernel_commit": subprocess.run(
            ["git", "-C", str(KERNEL), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "scanner_argv": "the installed console script (.venv/bin/ranex markers)",
        "host": {
            "node": platform.node(),
            "system": platform.system(),
            "release": platform.release(),
            "python": subprocess.run([str(PY), "--version"], capture_output=True,
                                     text=True, check=True).stdout.strip(),
        },
        "arm_statuses": statuses,
        "overall": "VERIFIED" if ok else "GAP",
        "wall_s": round(time.monotonic() - STARTED, 1),
        "limitations": [
            "Arm 8 proves admission is acquired by the operation under its "
            "lane — the shipped design; pytest itself does not self-acquire, "
            "and a bare suite outside its lane is not guarded",
            "Arms 6-9 drive the lane registry through a probe-owned "
            "RANEX_LANE_DIR, as #117's race probe did, so the proof cannot "
            "collide with a real lane on this host",
            "The receiver self-test exercises the local audit fixture "
            "listener; live GitHub authentication remains UNVERIFIED as before",
        ],
    }
    (AUDIT / "receipt.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8")
    (AUDIT / "commands.json").write_text(json.dumps(COMMANDS, indent=1),
                                         encoding="utf-8")
    print(json.dumps(statuses, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
