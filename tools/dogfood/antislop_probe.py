#!/usr/bin/env python3
"""P2 proof — the C3 anti-slop claim, frozen and governed on the real six.

Real `ranex` subprocesses over the pinned `benjaminp/six` subject; no mocks,
keys generated per run and discarded, receipts committed (#95 protocol).
The frozen control bank is the science bank (§3.3: three slop plants, six
known-good edits) plus the two plants the wave-1 ruling promoted
(snapshot-blind-update, input-range-narrowing), replayed as in-place edits
of six's own test file against a freeze of the pristine tree.

Run from the kernel checkout with its venv interpreter:

    .venv/bin/python tools/dogfood/antislop_probe.py

Prerequisite: the pinned subject cached at /tmp/ranex-p2-proof/six-cache
(git clone https://github.com/benjaminp/six && git checkout <rev>).

Writes tools/dogfood/audits/2026-09-25-antislop/ (commands.json,
receipt.json, arms/*.json).
"""

from __future__ import annotations

import argparse
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
AUDIT = KERNEL / "tools/dogfood/audits" / "2026-09-25-antislop"
SIX_URL = "https://github.com/benjaminp/six"
SIX_REV = "c8e394065cd541a16c040515dc0afb85cf22a7c3"
SIX_CACHE = Path("/tmp/ranex-p2-proof/six-cache")
ROOT = Path("/tmp/ranex-p2-proof")
KEY = ROOT / "worker.key"
REPEATS = 3

#: The blessed scanner argv, markers' discipline: the installed kernel's own
#: console script, whose shebang carries its kernel.
ANTISLOP_ARGV = [
    str(KERNEL / ".venv" / "bin" / "ranex"), "antislop",
    "--output-format=sarif", "--output-file=governance/antislop/scan.sarif",
]
ARTIFACT = "governance/antislop/scan.sarif"
MANIFEST = "governance/antislop/expectations.json"

# --- the science bank, as exact in-place edits of the pinned tree ----------

#: SLOP-S1-a: the whole body of a one-assert test replaced by `pass`.
S1A_BODY_REMOVED = [(
    'def test_add_doc():\n'
    '    def f():\n'
    '        """Icky doc"""\n'
    '        pass\n'
    '    six._add_doc(f, """New doc""")\n'
    '    assert f.__doc__ == "New doc"\n',
    'def test_add_doc():\n'
    '    pass\n',
)]
#: SLOP-S1-b: the same assertion replaced by a constant truth.
S1B_TAUTOLOGY = [(
    '    assert f.__doc__ == "New doc"',
    '    assert True',
)]
#: SLOP-S1-c: one of test_integer_types' four assertions commented out.
S1C_ASSERT_COMMENTED = [(
    '    assert not isinstance(.1, six.integer_types)',
    '    # assert not isinstance(.1, six.integer_types)',
)]
#: S2-g (wave-1): a snapshot-update flag so the assertion regenerates.
S2G_SNAPSHOT_BLIND = [(
    "",
    '\n\ndef test_slop_snapshot():\n'
    '    import subprocess\n'
    '    subprocess.check_call(["pytest", "--snapshot-update"])\n'
    '    assert six.__name__ == "six"\n',
)]
#: S2-h (wave-1): the generated-input range narrowed to a point sample.
S2H_RANGE_NARROWED = [(
    "",
    '\n\ndef test_slop_range():\n'
    '    settings(max_examples=1)\n'
    '    integers(min_value=0, max_value=0)\n',
)]
#: SLOP-S1-e shape for the census tripwire: a test deleted outright.
TEST_DELETED = [(
    'def test_integer_types():\n'
    '    assert isinstance(1, six.integer_types)\n'
    '    assert isinstance(-1, six.integer_types)\n'
    '    assert isinstance(six.MAXSIZE + 23, six.integer_types)\n'
    '    assert not isinstance(.1, six.integer_types)\n\n\n',
    '',
)]

#: KG-S1-01..06: edits a real review carries that must not fire anything.
KG_BANK: dict[str, dict[str, list[tuple[str, str]]]] = {
    "comment-six": {"six.py": [("",
                                "# an unrelated library comment\n")]},
    "comment-test": {"test_six.py": [(
        "def test_add_doc():\n",
        "def test_add_doc():\n    # an unrelated comment\n",
    )]},
    "blankline-six": {"six.py": [("", "\n")]},
    "docstring-six": {"six.py": [(
        '"""Utilities for writing code that runs on Python 2 and 3"""\n',
        '"""A proof docstring, inserted before the real one."""\n'
        '"""Utilities for writing code that runs on Python 2 and 3"""\n',
    )]},
    "comment-import": {"test_six.py": [(
        "import operator\n",
        "import operator  # the operator module\n",
    )]},
    "whitespace-test": {"test_six.py": [("", "\n\n")]},
}

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
    return run(["git", "-C", str(repo), "-c", "user.email=antislop-proof@ranex.invalid",
                "-c", "user.name=antislop-proof", *args], repo)


def apply_edits(scratch: Path, edits: dict[str, list[tuple[str, str]]]) -> None:
    """Apply exact in-place edits, refusing a no-op as the false pass it is."""

    for name, pairs in edits.items():
        path = scratch / name
        body = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old == "":
                body = body + new
            else:
                if old not in body:
                    raise SystemExit(f"edit anchor missing in {name}: {old[:60]!r}")
                body = body.replace(old, new, 1)
        path.write_text(body, encoding="utf-8")


def build_subject(edits: dict[str, list[tuple[str, str]]]) -> Path:
    scratch = ROOT / "subject"
    if scratch.exists():
        shutil.rmtree(scratch)
    completed = run(["git", "clone", "--quiet", "--no-hardlinks", str(SIX_CACHE),
                     str(scratch)], ROOT)
    if completed.returncode != 0:
        raise SystemExit(f"cannot clone the pinned six cache: {completed.stderr}")
    apply_edits(scratch, edits)
    (scratch / "producers.yaml").write_text(
        "producers:\n  worker: " + PUBLIC_KEY + "\n", encoding="utf-8"
    )
    (scratch / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: ANTISLOP_SANE\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: antislop\n"
        f"        command: {json.dumps(ANTISLOP_ARGV)}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: antislop-sarif-2.1.0\n"
        f"        results_manifest: {MANIFEST}\n",
        encoding="utf-8",
    )
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "six at the pinned ref + proof files").returncode == 0
    return scratch


def freeze(scratch: Path) -> int:
    argv = [
        "suite", "freeze",
        "--external-repository", str(scratch),
        "--artifact", ARTIFACT,
        "--output", MANIFEST,
        "--results-reporter", "antislop-sarif-2.1.0",
    ]
    argv += ["--", *ANTISLOP_ARGV]
    return ranex(scratch, *argv, key=KEY).returncode


def one_cycle(scratch: Path, repeat: int) -> dict[str, Any]:
    """run -> evaluate on the frozen subject; the observed facts only."""

    for junk in ("governance/evidence.json", "governance/journal.sqlite3"):
        (scratch / junk).unlink(missing_ok=True)
    # ADR-059's controller reporting leaves a verdict junit in the tree; it
    # is the operator's own artifact, not part of the subject under
    # observation, and left in place it dirties the next cycle's run.
    shutil.rmtree(scratch / "governance" / "verdicts", ignore_errors=True)
    run_exit = ranex(
        scratch,
        "run", "--claim", "antislop", "--producer", "worker",
        "--external-repository", str(scratch),
        "--evidence", "governance/evidence.json",
        "--producers", "producers.yaml",
        "--gate-catalog", "gates.yaml",
        "--", *ANTISLOP_ARGV,
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
        "non_passed": sorted(
            [test_id, kind] for test_id, kind in suite.get("non_passed", [])
        ),
        "missing": sorted(suite.get("missing", [])),
        "outcome_digest": suite.get("outcome_digest"),
        "counts": suite.get("counts"),
    }


def arm(name: str, edits: dict[str, list[tuple[str, str]]], *,
        expect_pass: bool) -> dict[str, Any]:
    """The governed candidate flow, exactly: freeze the approved tree, then
    land the candidate edit as its own commit, then REPEATS identical
    run+evaluate cycles against the frozen universe."""

    scratch = build_subject({})
    if freeze(scratch) != 0:
        return {"arm": name, "status": "GAP", "why": "the freeze refused"}
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze the antislop expectations").returncode == 0
    if any(pairs for pairs in edits.values()):
        apply_edits(scratch, edits)
        assert git(scratch, "add", "-A").returncode == 0
        assert git(scratch, "commit", "-qm", "the candidate edit under proof").returncode == 0
    cycles = [one_cycle(scratch, repeat) for repeat in range(REPEATS)]
    digests = {
        json.dumps(c["non_passed"]) + "|" + str(c["outcome_digest"]) for c in cycles
    }
    result: dict[str, Any] = {
        "arm": name,
        "edits": {name: [old[:80] for old, _ in pairs]
                  for name, pairs in edits.items()},
        "cycles": cycles,
        "identical": len(digests) == 1,
        "expect_pass": expect_pass,
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


def keygen() -> None:
    global PUBLIC_KEY
    ROOT.mkdir(parents=True, exist_ok=True)
    KEY.unlink(missing_ok=True)
    completed = ranex(ROOT, "keygen", "--producer", "worker", key=KEY)
    if completed.returncode != 0:
        raise SystemExit(f"keygen refused: {completed.stderr}")
    sys.path.insert(0, str(KERNEL / "src"))
    from ranex.foundation.signing import public_key_for  # noqa: E402

    with KEY.open("r", encoding="utf-8") as handle:
        PUBLIC_KEY = public_key_for(handle.read().strip())


def control_arm() -> dict[str, Any]:
    """The positive control, plus the detector-bug regression on real six:
    `test_print_exceptions` asserts only through `pytest.raises` and must be
    frozen with a non-zero count, not refused as assertion-free."""

    result = arm("1-control-pristine", {}, expect_pass=True)
    subject = ROOT / "subject"
    expectations = json.loads((subject / MANIFEST).read_bytes())
    result["frozen_scope"] = expectations["scope"]
    result["frozen_test_count"] = len(expectations["tests"])
    result["print_exceptions_frozen_count"] = expectations["tests"].get(
        "test_six.py::test_print_exceptions"
    )
    if result["status"] == "as-expected" and (
        result["frozen_scope"] != ["test_six.py"]
        or result["print_exceptions_frozen_count"] is None
        or result["print_exceptions_frozen_count"] < 1
    ):
        result["status"] = "GAP"
        result["why"] = "the freeze did not carry the pytest.raises-only test"
    return result


def kg_arms() -> list[dict[str, Any]]:
    """Six known-good edits, each a separate candidate against the pristine
    freeze — the false-positive bank, live on the real tree."""

    return [
        arm(f"7-kg-{name}", edits, expect_pass=True)
        for name, edits in sorted(KG_BANK.items())
    ]


def tamper_arm() -> dict[str, Any]:
    """The freeze's digest discipline (#97 arm 4's shape): evidence produced
    under the frozen expectations, then the committed manifest widened out of
    band — the same evidence must FAIL on the digest alone, and a fresh run
    under the tampered root must FAIL on the never-scanned scope member."""

    scratch = build_subject({})
    assert freeze(scratch) == 0
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "freeze").returncode == 0
    before = one_cycle(scratch, 0)
    frozen_digest = before["outcome_digest"]
    tampered = json.loads((scratch / MANIFEST).read_bytes())
    tampered["scope"] = sorted(set(tampered["scope"]) | {"never_scanned_test.py"})
    sys.path.insert(0, str(KERNEL / "src"))
    from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402

    (scratch / MANIFEST).write_bytes(canonical_json_bytes(tampered))
    assert git(scratch, "add", "-A").returncode == 0
    assert git(scratch, "commit", "-qm", "widen the frozen scope out of band").returncode == 0
    (scratch / "governance/journal.sqlite3").unlink(missing_ok=True)
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
        "arm": "9-manifest-tamper",
        "frozen_outcome_digest": frozen_digest,
        "before_tamper": before,
        "tampered_evaluate_same_evidence": tampered_evaluate,
        "fresh_run_under_tamper": fresh,
        "status": "as-expected"
        if before["verdict"] == "PASS"
        and tampered_evaluate["verdict"] == "FAIL"
        and fresh["verdict"] == "FAIL"
        else "GAP",
    }


def freeze_refusal_arm() -> dict[str, Any]:
    """The freeze itself refuses a tree that already carries violations:
    expectations recorded over slop would be expectations for it."""

    scratch = build_subject({"test_six.py": S1B_TAUTOLOGY})
    completed = ranex(
        scratch,
        "suite", "freeze",
        "--external-repository", str(scratch),
        "--artifact", ARTIFACT,
        "--output", MANIFEST,
        "--results-reporter", "antislop-sarif-2.1.0",
        "--", *ANTISLOP_ARGV,
        key=KEY,
    )
    refusal = (completed.stdout + completed.stderr).strip()
    wrote_manifest = (scratch / MANIFEST).exists()
    return {
        "arm": "10-freeze-refuses-slop",
        "freeze_exit": completed.returncode,
        "refusal": refusal[:400],
        "wrote_manifest": wrote_manifest,
        "status": "as-expected"
        if completed.returncode != 0
        and not wrote_manifest
        and "already carries antislop violations" in refusal
        else "GAP",
    }


def main() -> int:
    global REPEATS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=3)
    arguments = parser.parse_args()
    REPEATS = arguments.repeats

    if not SIX_CACHE.exists():
        raise SystemExit(
            f"cache the pinned subject first:\n"
            f"  git clone {SIX_URL} {SIX_CACHE}\n"
            f"  git -C {SIX_CACHE} checkout {SIX_REV}"
        )
    keygen()
    AUDIT.mkdir(parents=True, exist_ok=True)

    arms: list[dict[str, Any]] = [control_arm()]
    arms.append(arm("2-s1a-body-removed",
                    {"test_six.py": S1A_BODY_REMOVED}, expect_pass=False))
    arms.append(arm("3-s1b-tautology",
                    {"test_six.py": S1B_TAUTOLOGY}, expect_pass=False))
    arms.append(arm("4-s1c-assert-commented",
                    {"test_six.py": S1C_ASSERT_COMMENTED}, expect_pass=False))
    arms.append(arm("5-s2g-snapshot-blind-update",
                    {"test_six.py": S2G_SNAPSHOT_BLIND}, expect_pass=False))
    arms.append(arm("6-s2h-input-range-narrowing",
                    {"test_six.py": S2H_RANGE_NARROWED}, expect_pass=False))
    arms.extend(kg_arms())
    arms.append(arm("8-test-deleted",
                    {"test_six.py": TEST_DELETED}, expect_pass=False))
    arms.append(tamper_arm())
    arms.append(freeze_refusal_arm())

    statuses = {entry["arm"]: entry["status"] for entry in arms}
    receipt = {
        "protocol": "#95 — real subprocesses, no mocks, 3x repeats, "
                    "VERIFIED/GAP/FALSE-PASS/NON-DETERMINISTIC/UNVERIFIED",
        "overall": "VERIFIED" if all(s == "as-expected" for s in statuses.values()) else "GAP",
        "arm_statuses": statuses,
        "issue": "DIRECT 004/009 — P2 C3 anti-slop (SLICE proposal B)",
        "scanner": "ranex antislop (installed kernel entry point)",
        "scanner_argv": ANTISLOP_ARGV,
        "subject": {"url": SIX_URL, "rev": SIX_REV},
        "kernel_commit": subprocess.run(
            ["git", "-C", str(KERNEL), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip(),
        "host": {
            "node": platform.node(),
            "python": sys.version.split()[0],
            "release": platform.release(),
            "system": platform.system(),
        },
        "limitations": [
            "Census counts ride in SARIF message text, which the #97 fingerprint "
            "deliberately does not bind: a producer forging counts has forged the "
            "artifact (F-012 standing limit), while a test quietly dropped from "
            "observation is a miss and blocks",
            "Input-range narrowing is caught only in its named shapes "
            "(max_examples below the floor; a point integers range); narrowing "
            "that keeps those shapes and its assert count is invisible here",
            "Snapshot-blind updating is caught as the update flag/kwarg shapes, "
            "not as any possible snapshot workflow",
        ],
        "wall_s": round(time.monotonic() - STARTED, 1),
    }
    (AUDIT / "arms").mkdir(exist_ok=True)
    for entry in arms:
        (AUDIT / "arms" / f"{entry['arm']}.json").write_text(
            json.dumps(entry, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
    (AUDIT / "commands.json").write_text(
        json.dumps(COMMANDS, indent=1) + "\n", encoding="utf-8"
    )
    (AUDIT / "receipt.json").write_text(
        json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=1, sort_keys=True))
    return 0 if receipt["overall"] == "VERIFIED" else 1


if __name__ == "__main__":
    sys.exit(main())
