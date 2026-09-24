#!/usr/bin/env python3
"""#110 proof — deliberate-shortcut markers as deterministic evidence.

Real `ranex` subprocesses over the real pinned `benjaminp/six` subject; no
mocks, keys generated per run and discarded, receipts committed (#95
protocol). Arms 1-8 of the issue, including Correction 2's arm 8: a claim
bound to a system interpreter plus an in-tree script that always exits 0 must
not reach PASS.

Run from the kernel checkout with its venv interpreter:

    .venv/bin/python tools/dogfood/markers_probe.py

Prerequisite: the pinned subject cached at /tmp/ranex-110-proof/six-cache
(git clone https://github.com/benjaminp/six && git checkout <rev>).

Writes tools/dogfood/audits/2026-09-23-markers/ (commands.json, receipt.json,
arms/*.json).
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

KERNEL = Path(__file__).resolve().parents[2]
PY = KERNEL / ".venv" / "bin" / "python"
AUDIT = KERNEL / "tools/dogfood/audits" / "2026-09-23-markers"
SIX_URL = "https://github.com/benjaminp/six"
SIX_REV = "c8e394065cd541a16c040515dc0afb85cf22a7c3"
SIX_CACHE = Path("/tmp/ranex-110-proof/six-cache")
ROOT = Path("/tmp/ranex-110-proof")
KEY = ROOT / "worker.key"
REPEATS = 3

#: The blessed scanner argv (Correction 2): the installed kernel's own
#: console script. The module form (`python -P -m ranex.foundation.markers`)
#: is the same program, but a governed run resolves `argv[0]` through every
#: symlink — a venv interpreter leads to the base python with no ranex in its
#: site-packages (measured: ModuleNotFoundError) — while the console script
#: carries its own shebang and therefore its own kernel.
MARKER_ARGV = [
    str(KERNEL / ".venv" / "bin" / "ranex"), "markers",
    "--output-format=sarif", "--output-file=governance/markers.sarif",
]
RULES = ["ranex/marker-malformed", "ranex/marker-no-trigger", "ranex/marker-shortcut"]
ARTIFACT = "governance/markers.sarif"
MANIFEST = "governance/scan-manifest.json"

WELL_FORMED = "# ranex: global lock; per-account locks if throughput matters\n"
TRIGGERLESS = "# ranex: global lock\n"
EMPTY_CEILING = "# ranex: ; whenever throughput matters\n"
EMPTY_TRIGGER = "# ranex: global lock ;\n"
IN_STRING = 'EXAMPLE = "# ranex: global lock"\n'

COMMANDS: list[dict[str, Any]] = []
STARTED = time.monotonic()
PUBLIC_KEY = ""


def run(argv: list[str], cwd: Path, *, env: dict[str, str] | None = None,
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


def ranex(scratch: Path, *args: str, key: Path | None = None,
          timeout: int = 900) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("RANEX_")}
    if key is not None:
        env["RANEX_SIGNING_KEY"] = str(key)
    return run([PY, "-m", "ranex.cli.main", *args], KERNEL, env=env, timeout=timeout)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(repo), "-c", "user.email=markers-proof@ranex.invalid",
                "-c", "user.name=markers-proof", *args], repo)


def scanner_only(scratch: Path) -> tuple[list[str], list[dict[str, Any]]]:
    """One standalone scan of the working tree, for scope and finding IDs."""

    out = scratch.parent / "probe-scan.sarif"
    completed = run([PY, "-P", "-m", "ranex.foundation.markers",
                     "--output-format=sarif", f"--output-file={out}",
                     "--root", str(scratch)], scratch)
    if completed.returncode != 0:
        raise SystemExit(f"standalone scan failed: {completed.stderr}")
    (run_data,) = json.loads(out.read_bytes())["runs"]
    return (
        [a["location"]["uri"] for a in run_data["artifacts"]],
        run_data["results"],
    )


def build_subject(files: dict[str, str], command: list[str] | None) -> Path:
    scratch = ROOT / "subject"
    if scratch.exists():
        shutil.rmtree(scratch)
    completed = run(["git", "clone", "--quiet", "--no-hardlinks", str(SIX_CACHE),
                     str(scratch)], ROOT)
    if completed.returncode != 0:
        raise SystemExit(f"cannot clone the pinned six cache: {completed.stderr}")
    for name, body in files.items():
        (scratch / name).write_text(body, encoding="utf-8")
    (scratch / "producers.yaml").write_text(
        "producers:\n  worker: " + PUBLIC_KEY + "\n", encoding="utf-8"
    )
    (scratch / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: MARKERS_SANE\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: scan\n"
        f"        command: {json.dumps(command or MARKER_ARGV)}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: sarif-2.1.0\n"
        f"        results_manifest: {MANIFEST}\n",
        encoding="utf-8",
    )
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "six at the pinned ref + proof files").returncode == 0
    return scratch


def freeze(scratch: Path, accepted: dict[str, str] | None = None,
           command: list[str] | None = None) -> int:
    scope, _ = scanner_only(scratch)
    argv = [
        "suite", "freeze",
        "--external-repository", str(scratch),
        "--artifact", ARTIFACT,
        "--output", MANIFEST,
        "--results-reporter", "sarif-2.1.0",
    ]
    for path in sorted(scope):
        argv += ["--scan-scope", path]
    for rule in RULES:
        argv += ["--scan-rule", rule]
    for identifier, reason in (accepted or {}).items():
        argv += ["--accepted", f"{identifier}={reason}"]
    argv += ["--", *(command or MARKER_ARGV)]
    return ranex(scratch, *argv, key=KEY).returncode


def one_cycle(scratch: Path, repeat: int, command: list[str] | None = None) -> dict[str, Any]:
    """run -> evaluate on the frozen subject; the observed facts only."""

    for junk in ("governance/evidence.json", "governance/journal.sqlite3"):
        (scratch / junk).unlink(missing_ok=True)
    run_exit = ranex(
        scratch,
        "run", "--claim", "scan", "--producer", "worker",
        "--external-repository", str(scratch),
        "--evidence", "governance/evidence.json",
        "--producers", "producers.yaml",
        "--gate-catalog", "gates.yaml",
        "--", *(command or MARKER_ARGV),
        key=KEY,
    ).returncode
    evaluated = ranex(
        scratch,
        "gate", "evaluate", "HEAD",
        "--external-repository", str(scratch),
        "--gate-catalog", "gates.yaml",
        "--evidence", "governance/evidence.json",
        "--producers", "producers.yaml",
        "--approver", "reviewer",
    )
    evidence_path = scratch / "governance/evidence.json"
    records = json.loads(evidence_path.read_bytes()) if evidence_path.exists() else []
    suite = (records[-1].get("suite_results") or {}) if records else {}
    return {
        "repeat": repeat,
        "run_exit": run_exit,
        "evaluate_exit": evaluated.returncode,
        "verdict": "PASS" if evaluated.returncode == 0 else "FAIL",
        "evaluate_line": (evaluated.stdout + evaluated.stderr).strip().splitlines()[:2],
        "finding_ids": sorted(
            test_id for test_id, _ in suite.get("non_passed", []) if "::" in test_id
        ),
        "outcome_digest": suite.get("outcome_digest"),
        "counts": suite.get("counts"),
    }


def arm(name: str, files: dict[str, str], *, accepted: dict[str, str] | None = None,
        command: list[str] | None = None, expect_pass: bool,
        extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """One subject variant, frozen, then REPEATS identical run+evaluate cycles."""

    scratch = build_subject(files, command)
    if freeze(scratch, accepted=accepted, command=command) != 0:
        return {"arm": name, "status": "GAP", "why": "the freeze refused"}
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze the marker scan manifest").returncode == 0
    # The pure grep over the same tree bytes, recorded beside the governed
    # run: this is where a `note` finding and a finding's line number are
    # visible, because suite_results carry only blocking outcomes.
    _, standalone = scanner_only(scratch)
    cycles = [one_cycle(scratch, repeat) for repeat in range(REPEATS)]
    digests = {
        json.dumps(c["finding_ids"]) + "|" + str(c["outcome_digest"]) for c in cycles
    }
    result: dict[str, Any] = {
        "arm": name,
        "files": files,
        "standalone_findings": [
            {
                "ruleId": r["ruleId"],
                "level": r["level"],
                "location": r["locations"][0]["physicalLocation"],
                "fingerprint": r["fingerprints"]["ranex/v1"],
            }
            for r in standalone
        ],
        "cycles": cycles,
        "identical": len(digests) == 1,
        "expect_pass": expect_pass,
        **(extra or {}),
    }
    if len(digests) != 1:
        result["status"] = "NON-DETERMINISTIC"
        return result
    verdicts = [c["verdict"] for c in cycles]
    passed, failed = all(v == "PASS" for v in verdicts), all(v == "FAIL" for v in verdicts)
    result["reached_pass"] = passed
    if (expect_pass and passed) or (not expect_pass and failed):
        result["status"] = "as-expected"
    else:
        result["status"] = "GAP"
        result["why"] = f"expect_pass={expect_pass} but verdicts={verdicts}"
    return result


def arm4() -> dict[str, Any]:
    """Acceptance is a committed, reviewable act — both directions measured."""

    scratch = build_subject({"shortcut_probe.py": TRIGGERLESS}, None)
    scanner_only(scratch)
    sys.path.insert(0, str(KERNEL / "src"))
    from ranex.foundation.scan_results import observed_findings  # noqa: E402

    identifier = next(
        found for found, _path, _level in observed_findings(
            (scratch.parent / "probe-scan.sarif").read_bytes(), scratch
        )
        if found.startswith("shortcut_probe.py::ranex/marker-no-trigger::")
    )
    assert freeze(scratch, accepted={identifier: "review answered for this shortcut"}) == 0
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze with the accepted declaration").returncode == 0
    accepted_cycles = [one_cycle(scratch, repeat) for repeat in range(REPEATS)]
    for junk in ("governance/evidence.json", "governance/journal.sqlite3"):
        (scratch / junk).unlink(missing_ok=True)
    # The removal must itself be a committed act: freezing refuses a dirty
    # tree, and the previous manifest is tracked at HEAD.
    assert git(scratch, "rm", "-q", MANIFEST).returncode == 0
    assert git(scratch, "commit", "-qm", "remove the accepted declaration").returncode == 0
    assert freeze(scratch) == 0
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze without the declaration").returncode == 0
    removed_cycles = [one_cycle(scratch, repeat) for repeat in range(REPEATS)]
    return {
        "arm": "4-accepted-both-directions",
        "finding_id": identifier,
        "accepted_cycles": accepted_cycles,
        "removed_cycles": removed_cycles,
        "accepted_status": "as-expected"
        if all(c["verdict"] == "PASS" for c in accepted_cycles) else "GAP",
        "removed_status": "as-expected"
        if all(c["verdict"] == "FAIL" for c in removed_cycles) else "GAP",
        "status": "as-expected"
        if all(c["verdict"] == "PASS" for c in accepted_cycles)
        and all(c["verdict"] == "FAIL" for c in removed_cycles) else "GAP",
    }


def arm5() -> dict[str, Any]:
    """Manifest tamper after freeze: the digest mismatch FAILs (#97 arm 4).

    The evidence was produced under the frozen manifest; the committed
    manifest is then widened out of band; the SAME evidence is evaluated
    against the tampered rulebook and must FAIL on the digest alone. A fresh
    run under the tampered manifest is recorded beside it — the run side of
    the same refusal.
    """

    scratch = build_subject({"shortcut_probe.py": WELL_FORMED}, None)
    assert freeze(scratch) == 0
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze").returncode == 0
    before = one_cycle(scratch, 0)
    # Keep this evidence: the tamper is judged against it, not against a
    # re-run.
    frozen_evidence = (scratch / "governance/evidence.json").read_bytes()
    frozen_digest = before["outcome_digest"]
    tampered = json.loads((scratch / MANIFEST).read_bytes())
    tampered["scope"] = sorted(set(tampered["scope"]) | {"never-scanned.py"})
    sys.path.insert(0, str(KERNEL / "src"))
    from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402

    (scratch / MANIFEST).write_bytes(canonical_json_bytes(tampered))
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "widen the frozen scope out of band").returncode == 0
    evaluated = ranex(
        scratch,
        "gate", "evaluate", "HEAD",
        "--external-repository", str(scratch),
        "--gate-catalog", "gates.yaml",
        "--evidence", "governance/evidence.json",
        "--producers", "producers.yaml",
        "--approver", "reviewer",
    )
    tampered_evaluate = {
        "exit": evaluated.returncode,
        "verdict": "PASS" if evaluated.returncode == 0 else "FAIL",
        "line": (evaluated.stdout + evaluated.stderr).strip().splitlines()[:3],
    }
    (scratch / "governance/journal.sqlite3").unlink(missing_ok=True)
    fresh = one_cycle(scratch, 1)
    return {
        "arm": "5-manifest-tamper",
        "frozen_outcome_digest": frozen_digest,
        "frozen_evidence_bytes": len(frozen_evidence),
        "before_tamper": before,
        "tampered_evaluate_same_evidence": tampered_evaluate,
        "fresh_run_under_tamper": fresh,
        "status": "as-expected"
        if before["verdict"] == "PASS"
        and tampered_evaluate["verdict"] == "FAIL"
        and fresh["verdict"] == "FAIL"
        else "GAP",
    }


def arm8() -> dict[str, Any]:
    """Correction 2: an in-tree scanner substitution must not reach PASS."""

    neuter = (
        "import json, sys\n"
        "out = [a for a in sys.argv if a.startswith('--output-file=')][0].split('=', 1)[1]\n"
        "open(out, 'w').write(json.dumps({'version': '2.1.0', 'runs': [{'tool': "
        "{'driver': {'name': 'neuter'}}, 'invocations': [{'executionSuccessful': True}], "
        "'artifacts': [{'location': {'uri': 'six.py'}}], 'results': []}]}))\n"
    )
    neuter_argv = ["/usr/bin/python3", "neuter.py",
                   "--output-format=sarif", f"--output-file={ARTIFACT}"]
    result: dict[str, Any] = {
        "arm": "8-in-tree-scanner-substitution",
        "bound_command": neuter_argv,
        "neuter_behaviour": "committed in-tree script; always exits 0 and writes a clean SARIF",
    }
    scratch = build_subject({"shortcut_probe.py": TRIGGERLESS, "neuter.py": neuter},
                            neuter_argv)
    refused = ranex(
        scratch,
        "run", "--claim", "scan", "--producer", "worker",
        "--external-repository", str(scratch),
        "--evidence", "governance/evidence.json",
        "--producers", "producers.yaml",
        "--gate-catalog", "gates.yaml",
        "--", *neuter_argv,
        key=KEY,
    )
    evaluated = ranex(
        scratch,
        "gate", "evaluate", "HEAD",
        "--external-repository", str(scratch),
        "--gate-catalog", "gates.yaml",
        "--evidence", "governance/evidence.json",
        "--producers", "producers.yaml",
        "--approver", "reviewer",
    )
    result["catalog_bound"] = {
        "run_exit": refused.returncode,
        "run_refusal": (refused.stdout + refused.stderr).strip()[:400],
        "evaluate_exit": evaluated.returncode,
        "reached_pass": evaluated.returncode == 0,
    }
    # The same neuter argv under the honest catalog: a real, signed, exit-0
    # record that still cannot satisfy the claim the catalog binds.
    (scratch / "gates.yaml").write_text(
        (scratch / "gates.yaml").read_text().replace(
            json.dumps(neuter_argv), json.dumps(MARKER_ARGV)
        ),
        encoding="utf-8",
    )
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "rebind the claim to the kernel scanner").returncode == 0
    assert freeze(scratch) == 0
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze under the honest catalog").returncode == 0
    cycles = [one_cycle(scratch, repeat, neuter_argv) for repeat in range(REPEATS)]
    result["honest_catalog_neuter_argv"] = cycles
    result["status"] = (
        "as-expected"
        if refused.returncode not in (0, 1)
        and evaluated.returncode not in (0, 1)
        and all(c["verdict"] == "FAIL" for c in cycles)
        else "GAP"
    )
    return result


def main() -> int:
    global PUBLIC_KEY
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "arms").mkdir(exist_ok=True)
    if not SIX_CACHE.exists():
        print(f"cache the pinned subject first: git clone {SIX_URL} {SIX_CACHE} "
              f"&& git -C {SIX_CACHE} checkout {SIX_REV}")
        return 2
    KEY.parent.mkdir(parents=True, exist_ok=True)
    KEY.unlink(missing_ok=True)
    generated = ranex(ROOT, "keygen", "--producer", "worker", key=KEY)
    if generated.returncode != 0:
        print(f"keygen refused: {generated.stderr}")
        return 2
    sys.path.insert(0, str(KERNEL / "src"))
    from ranex.foundation.signing import public_key_for  # noqa: E402

    with KEY.open("r", encoding="utf-8") as handle:
        PUBLIC_KEY = public_key_for(handle.read().strip())
    print(f"producer key generated; public {PUBLIC_KEY[:24]}…")

    arms = [
        lambda: arm("1-well-formed", {"shortcut_probe.py": WELL_FORMED}, expect_pass=True),
        lambda: arm("2-trigger-less", {"shortcut_probe.py": TRIGGERLESS}, expect_pass=False),
        lambda: arm("3a-empty-ceiling", {"shortcut_probe.py": EMPTY_CEILING}, expect_pass=False),
        lambda: arm("3b-empty-trigger", {"shortcut_probe.py": EMPTY_TRIGGER}, expect_pass=False),
        lambda: arm("6-string-literal", {"docstring_probe.py": IN_STRING}, expect_pass=True),
        arm4,
        arm5,
        arm8,
    ]
    results = []
    for construct in arms:
        result = construct()
        results.append(result)
        (AUDIT / "arms" / f"{result['arm']}.json").write_text(
            json.dumps(result, indent=1, sort_keys=True), encoding="utf-8"
        )
        (AUDIT / "commands.json").write_text(
            json.dumps(COMMANDS, indent=1), encoding="utf-8"
        )
    statuses = {result["arm"]: result["status"] for result in results}
    ok = all(status == "as-expected" for status in statuses.values())
    receipt = {
        "issue": "anthonykewl20/ranex#110",
        "protocol": "#95 — real subprocesses, no mocks, 3x repeats, "
                    "VERIFIED/GAP/FALSE-PASS/NON-DETERMINISTIC/UNVERIFIED",
        "kernel_commit": subprocess.run(
            ["git", "-C", str(KERNEL), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "subject": {"url": SIX_URL, "rev": SIX_REV},
        "scanner_argv": MARKER_ARGV,
        "scanner": "python -P -m ranex.foundation.markers (installed kernel entry point)",
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
            "Line-level quote tracking: a marker inside a multi-line string "
            "literal whose quotes open on an earlier line is still reported",
            "The scanner walks a fixed exclusion set (.git, node_modules, "
            "build, dist, target, __pycache__); other build outputs are walked",
            "Arm 2/3 verdicts name the file in the finding ID and the line in "
            "the signed artifact's region; suite_results carry no line numbers",
        ],
    }
    (AUDIT / "receipt.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True), encoding="utf-8"
    )
    (AUDIT / "commands.json").write_text(json.dumps(COMMANDS, indent=1), encoding="utf-8")
    KEY.unlink(missing_ok=True)
    print(json.dumps(statuses, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
