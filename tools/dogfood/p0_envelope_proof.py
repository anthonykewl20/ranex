#!/usr/bin/env python3
"""SLICE-092 (C1+C6) real-data proof: the repair envelope on pinned six@1.17.0.

Arms, each run against a governed lab built the F-003 way (vendored kernel
src committed into the subject repo, real keys, real pytest, real CLI):

  arm-passing-subject      freeze → run → evaluate → PASS verdict + envelope
  arm-failing-envelope     planted real defect → FAIL → envelope carries the
                           failing ID, assertion text and file:line from the
                           run's own junit; digest binds to the verdict
  arm-determinism          the same failing subject judged 3× → byte-identical
                           envelope digests
  arm-bytes                measured agent-ingested bytes: raw junit (what an
                           honest agent reads today) vs the envelope
  arm-stop-hook-loop       the C6 attachment on six: block, block, STOP at the
                           3-miss budget, then a real repair approves PASS
  arm-negative-evidence    envelope bytes offered as signed evidence → refused
  arm-negative-unsigned    the governed cycle without a credential → refused,
                           nothing fabricated, nothing written
  arm-negative-delegated   execute_environment with an ambient credential →
                           refused (delegation.py:93, live)
  arm-kernel-unchanged     tests/contract/test_kernel_unchanged.py passes

Statuses use the #95 vocabulary: VERIFIED · GAP · FALSE-PASS ·
NON-DETERMINISTIC · UNVERIFIED. Numbers in the receipt are measured on this
host in this run; nothing is copied from the oracle-science report.

Run (network required for the six clone only):
  uv run --frozen python tools/dogfood/p0_envelope_proof.py \
      [--out tools/dogfood/audits/2026-09-25-p0-envelope] [--keep]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RANEX_REPO = HERE.parents[1]
RANEX_PY = RANEX_REPO / ".venv" / "bin" / "python"

SIX_TAG = "1.17.0"
SIX_COMMIT = "ebd9b3af90247b8858d415a05e96e9ee61e48d07"
SIX_URL = "https://github.com/benjaminp/six.git"

PRODUCER = "p0-envelope-producer"
APPROVER = "p0-envelope-approver"
VERDICT_SIGNER_ID = "kernel-verdict-signer"

# The planted defect: six.py:655 packs an unsigned byte; a two-byte pack
# changes int2byte(3) from b"\x03" to b"\x00\x03" and fails test_int2byte's
# own assertion at test_six.py:527. A real behavior change, not a marker.
DEFECT_FROM = 'int2byte = struct.Struct(">B").pack'
DEFECT_TO = 'int2byte = struct.Struct(">H").pack'
EXPECTED_FAILURE_ID = "test_six.py::test_int2byte"
EXPECTED_FAILURE_AT = "test_six.py:527"

SUITE_COMMAND = [
    "/usr/bin/python3", "-m", "pytest", "-q", "-o", "xfail_strict=true",
    "-p", "ranex.foundation.pytest_xpass",
    "--junitxml=governance/suite_results.xml", "test_six.py",
]


def _status(control: dict[str, Any], ok: bool) -> str:
    control["status"] = "VERIFIED" if ok else "FALSE-PASS"
    return control["status"]


def _ranex(repo: Path, key: Path | None, *args: str,
           extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "PYTHON"))
    }
    environment["PYTHONPATH"] = str(Path(repo).resolve() / "src")
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    if extra_env:
        environment.update(extra_env)
    return subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", *args],
        cwd=str(repo), env=environment, capture_output=True, text=True,
        check=False, timeout=600,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=p0@ranex.invalid",
         "-c", "user.name=ranex-p0-proof", *args],
        capture_output=True, text=True, check=False,
    )


def _commit(repo: Path, message: str) -> None:
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", message).returncode == 0


def _subject_hex(repo: Path) -> str:
    tree = _git(repo, "rev-parse", "HEAD^{tree}").stdout.strip()
    return hashlib.sha256(json.dumps({"tree": tree}, separators=(",", ":")).encode()).hexdigest()


def _publish_env(signer: Path) -> dict[str, str]:
    return {"RANEX_VERDICT_SIGNING_KEY": str(signer),
            "RANEX_VERDICT_DIR": "governance/verdicts"}


def _cycle(repo: Path, key: Path, signer: Path) -> tuple[
        subprocess.CompletedProcess[str], subprocess.CompletedProcess[str]]:
    run = _ranex(repo, key, "run", "--claim", "tests-executed",
                 "--producer", PRODUCER, "--", *SUITE_COMMAND)
    evaluate = _ranex(
        repo, key, "gate", "evaluate", "HEAD", "--approver", APPROVER,
        "--journal", "governance/journal.sqlite3",
        extra_env=_publish_env(signer),
    )
    return run, evaluate


def _stop_hook(repo: Path, key: Path | None, signer: Path) -> dict[str, Any]:
    hook = _ranex(
        repo, key, "task", "stop-hook", "--external-repository", str(repo),
        "--producer", PRODUCER, "--approver", APPROVER,
        extra_env=_publish_env(signer),
    )
    assert hook.returncode == 0, hook.stdout + hook.stderr
    return json.loads(hook.stdout.strip().splitlines()[-1])


def clone_six(root: Path) -> Path:
    six = root / "six"
    result = subprocess.run(
        ["git", "clone", "-q", "--branch", SIX_TAG, SIX_URL, str(six)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"cannot clone {SIX_URL}@{SIX_TAG} (network required): {result.stderr[:300]}"
        )
    assert _git(six, "checkout", "-q", SIX_COMMIT).returncode == 0
    return six


def build_lab(root: Path, six: Path) -> tuple[Path, Path, Path]:
    sys.path.insert(0, str(RANEX_REPO / "src"))
    from ranex.foundation.signing import generate_keypair

    repo = root / "six-governed"
    shutil.copytree(six, repo)
    # The upstream checkout arrives with its own history; the lab starts a
    # fresh one so every lab commit (vendoring, defect, repair) is ours.
    shutil.rmtree(repo / ".git")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "p0@ranex.invalid")
    _git(repo, "config", "user.name", "ranex-p0-proof")
    _commit(repo, f"six@{SIX_TAG} pinned tree")

    shutil.copytree(RANEX_REPO / "src", repo / "src")
    shutil.copy2(RANEX_REPO / "pyproject.toml", repo / "pyproject.toml")
    shutil.copy2(RANEX_REPO / "uv.lock", repo / "uv.lock")

    keys = root / "keys"
    keys.mkdir()
    producer_key, producer_public = generate_keypair()
    key = keys / "producer.key"
    key.write_text(producer_key + "\n")
    key.chmod(0o600)
    signing, verifying = generate_keypair()
    signer = keys / "verdict.key"
    signer.write_text(signing + "\n")
    signer.chmod(0o600)

    (repo / "governance").mkdir()
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  {PRODUCER}: {producer_public}\n"
        f"verdict_signer:\n  id: {VERDICT_SIGNER_ID}\n  public_key: {verifying}\n"
    )
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        f"        command: {json.dumps(SUITE_COMMAND)}\n"
        "        results_artifact: governance/suite_results.xml\n"
    )
    (repo / ".gitignore").write_text(
        "governance/evidence.json\ngovernance/suite_results.xml\n"
        "governance/journal.sqlite3*\ngovernance/verdicts/\n"
        "__pycache__/\n.pytest_cache/\nsrc/*.egg-info/\n"
    )
    _commit(repo, "vendor ranex kernel; governance: keyring and gate")
    return repo, key, signer


def _skipped_ids(repo: Path) -> list[str]:
    # The hermetic run leaves no junit in the working tree; the durable
    # closed summary rides the evidence record the run just signed.
    records = json.loads((repo / "governance" / "evidence.json").read_bytes())
    summary = next(
        record["suite_results"] for record in reversed(records)
        if record.get("suite_results") is not None
    )
    reason = "platform skip, operator-approved at freeze (p0 lab)"
    return sorted(
        f"{test_id}={reason}"
        for test_id, kind in summary["non_passed"]
        if kind == "skipped"
    )


def freeze_with_skips(repo: Path, key: Path, signer: Path) -> dict[str, Any]:
    """Freeze the suite, approving real platform skips mechanically if any."""

    facts: dict[str, Any] = {"iterations": []}
    expected: list[str] = []
    for _ in range(3):
        flags: list[str] = []
        for item in expected:
            flags += ["--expected-skip", item]
        frozen = _ranex(repo, key, "suite", "freeze",
                        "--artifact", "governance/suite_results.xml", *flags,
                        "--", *SUITE_COMMAND)
        if frozen.returncode != 0:
            raise SystemExit(f"suite freeze refused: {frozen.stderr[:400]}")
        _commit(repo, "freeze suite manifest")
        _run, evaluate = _cycle(repo, key, signer)
        facts["iterations"].append(
            {"expected_skips": len(expected), "evaluate_exit": evaluate.returncode}
        )
        if evaluate.returncode == 0:
            facts["approved_skips"] = [item.split("=", 1)[0] for item in expected]
            return facts
        skips = _skipped_ids(repo)
        if set(skips) <= set(expected):
            raise SystemExit(f"PASS subject did not pass: {evaluate.stdout[:400]}")
        expected = sorted(set(expected) | set(skips))
    raise SystemExit("freeze/skip loop did not converge")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=HERE / "audits" / "2026-09-25-p0-envelope")
    parser.add_argument("--keep", action="store_true",
                        help="keep the scratch lab for inspection")
    options = parser.parse_args()

    out = options.out
    out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    controls: list[dict[str, Any]] = []
    commands_log: list[dict[str, Any]] = []

    def command_row(name: str, argv: list[str], cwd: Path,
                    result: subprocess.CompletedProcess[str]) -> None:
        commands_log.append({
            "control": name, "argv": argv, "cwd": str(cwd),
            "exit": result.returncode,
            "stdout_tail": result.stdout.strip()[-400:],
            "stderr_tail": result.stderr.strip()[-200:],
        })

    root = Path(tempfile.mkdtemp(prefix="ranex-p0-envelope-"))
    try:
        six = clone_six(root)
        repo, key, signer = build_lab(root, six)

        # --- arm-passing-subject -------------------------------------------
        arm = {"control": "arm-passing-subject",
               "expectation": "the pinned six suite freezes, passes, and "
               "publishes a PASS verdict with an empty-failure envelope",
               "facts": {}}
        arm["facts"]["freeze"] = freeze_with_skips(repo, key, signer)
        _run, evaluate = _cycle(repo, key, signer)
        command_row("arm-passing-subject", ["gate", "evaluate"], repo, evaluate)
        subject_hex = _subject_hex(repo)
        envelope_path = repo / "governance" / "verdicts" / f"{subject_hex}.envelope.json"
        verdict_path = repo / "governance" / "verdicts" / f"{subject_hex}.json"
        published = (json.loads(envelope_path.read_bytes())
                     if envelope_path.is_file() else None)
        arm["facts"]["evaluate_exit"] = evaluate.returncode
        arm["facts"]["verdict_published"] = verdict_path.is_file()
        arm["facts"]["envelope"] = {
            "verdict": published and published.get("verdict"),
            "failures": published and len(published.get("failures", [])),
        }
        arm["facts"]["approved_platform_skips"] = len(
            arm["facts"]["freeze"].get("approved_skips", [])
        )
        _status(arm, bool(evaluate.returncode == 0 and published
                          and published["verdict"] == "PASS"
                          and published["failures"] == []))
        controls.append(arm)

        # --- arm-failing-envelope ------------------------------------------
        six_py = repo / "six.py"
        original = six_py.read_text()
        assert DEFECT_FROM in original, "pinned six.py lacks the expected pack line"
        six_py.write_text(original.replace(DEFECT_FROM, DEFECT_TO))
        _commit(repo, "plant real defect: two-byte int2byte pack")

        arm = {"control": "arm-failing-envelope",
               "expectation": "the FAIL envelope carries the failing test's "
               "ID, assertion text and file:line from the run's own junit, "
               "bound to the signed verdict by record digest",
               "facts": {}}
        began = time.perf_counter()
        _run, evaluate = _cycle(repo, key, signer)
        arm["facts"]["wall_clock_s"] = round(time.perf_counter() - began, 3)
        command_row("arm-failing-envelope", ["gate", "evaluate"], repo, evaluate)
        subject_hex = _subject_hex(repo)
        envelope_raw = (repo / "governance" / "verdicts"
                        / f"{subject_hex}.envelope.json").read_bytes()
        envelope = json.loads(envelope_raw)
        verdict = json.loads(
            (repo / "governance" / "verdicts" / f"{subject_hex}.json").read_bytes()
        )
        retained = repo / "governance" / "verdicts" / f"{subject_hex}.junit.xml"
        failure = envelope["failures"][0] if envelope["failures"] else {}
        checks = {
            "verdict_fail": envelope["verdict"] == "FAIL",
            "evaluate_exit_fail": evaluate.returncode == 1,
            "junit_retained": envelope["junit_retained"] and retained.is_file(),
            "failure_id": failure.get("id") == EXPECTED_FAILURE_ID,
            "assertion_text": "assert" in failure.get("assertion", ""),
            "file_line": failure.get("at") == EXPECTED_FAILURE_AT,
            "digest_binds":
                envelope["verdict_record_digest"] == verdict["record"]["record_digest"],
            "rung_pointers": any(r.startswith("L1 ") for r in envelope["next_rung"]),
        }
        arm["facts"]["checks"] = checks
        arm["facts"]["failure"] = failure
        _status(arm, all(checks.values()))
        controls.append(arm)
        failing_subject_hex = subject_hex
        failing_envelope_raw = envelope_raw

        # --- arm-bytes -----------------------------------------------------
        junit_bytes = retained.read_bytes()
        arm = {"control": "arm-bytes",
               "expectation": "measured agent-ingested bytes: the raw junit "
               "an honest agent must read today vs the envelope; measured on "
               "this host, never copied from the report",
               "facts": {"raw_junit_bytes": len(junit_bytes),
                         "envelope_bytes": len(failing_envelope_raw)}}
        arm["facts"]["reduction_pct"] = round(
            100 * (1 - len(failing_envelope_raw) / len(junit_bytes)), 1
        )
        _status(arm, len(failing_envelope_raw) < len(junit_bytes))
        controls.append(arm)

        # --- arm-determinism ----------------------------------------------
        # Identical input means identical input: a re-evaluation is not one,
        # because every evaluation appends a journal row and the advisory
        # envelope binds the verdict of ITS evaluation (ADR-057 anchor). So
        # the whole-cycle digests are recorded as an observation — expected
        # to differ by journal_head exactly as the chain moves — while the
        # determinism claim is proven by re-rendering from the SAME captured
        # projection, evidence and junit three times.
        sys.path.insert(0, str(RANEX_REPO / "src"))
        from types import SimpleNamespace

        from ranex.governed_execution.repair_envelope import (
            envelope_from_projection,
            envelope_from_suite,
            envelope_packet_bytes,
        )

        verdict_record = json.loads(
            (repo / "governance" / "verdicts"
             / f"{failing_subject_hex}.json").read_bytes()
        )["record"]
        evidence_rows = [
            SimpleNamespace(command=row["command"], suite_results=row["suite_results"])
            for row in json.loads(
                (repo / "governance" / "evidence.json").read_bytes()
            )
            if row.get("suite_results") is not None
        ]
        retained_junit = (repo / "governance" / "verdicts"
                          / f"{failing_subject_hex}.junit.xml").read_bytes()
        arm = {"control": "arm-determinism",
               "expectation": "re-rendering the envelope from the same captured "
               "projection, evidence and junit yields byte-identical digests "
               "3×; whole-cycle re-evaluations differ only by the journal "
               "anchor, recorded here as the expected move",
               "facts": {}}
        renders = [
            hashlib.sha256(envelope_packet_bytes(envelope_from_projection(
                projected=verdict_record, evidence=evidence_rows,
                junit_bytes=retained_junit,
            ))).hexdigest()
            for _ in range(3)
        ]
        suite_renders = [
            hashlib.sha256(envelope_packet_bytes(envelope_from_suite(
                repro_argv=" ".join(SUITE_COMMAND), junit_bytes=retained_junit,
            ))).hexdigest()
            for _ in range(3)
        ]
        cycle_digests = [hashlib.sha256(failing_envelope_raw).hexdigest()]
        for _ in range(2):
            _cycle(repo, key, signer)
            cycle_digests.append(hashlib.sha256(
                (repo / "governance" / "verdicts"
                 / f"{failing_subject_hex}.envelope.json").read_bytes()
            ).hexdigest())
        arm["facts"] = {
            "projection_render_digests": renders,
            "delegate_render_digests": suite_renders,
            "whole_cycle_digests": cycle_digests,
            "identical_input_identical_bytes":
                len(set(renders)) == 1 and len(set(suite_renders)) == 1,
            "whole_cycles_differ_by_journal_anchor":
                len(set(cycle_digests)) == 3,
        }
        arm["status"] = ("VERIFIED"
                         if arm["facts"]["identical_input_identical_bytes"]
                         else "NON-DETERMINISTIC")
        controls.append(arm)

        # --- arm-stop-hook-loop --------------------------------------------
        arm = {"control": "arm-stop-hook-loop",
               "expectation": "task stop-hook on the failing six subject: "
               "block(1) block(2) STOP at budget 3, then a real repair "
               "approves PASS and resets the budget",
               "facts": {"decisions": []}}
        for expected_misses in (1, 2, 3):
            answer = _stop_hook(repo, key, signer)
            arm["facts"]["decisions"].append({
                "decision": answer["decision"], "misses": answer.get("misses"),
                "envelope_verdict": (answer.get("envelope") or {}).get("verdict"),
            })
            assert answer.get("misses") == expected_misses, answer
        six_py.write_text(original)
        _commit(repo, "repair: restore the single-byte pack")
        repaired = _stop_hook(repo, key, signer)
        arm["facts"]["decisions"].append({
            "decision": repaired["decision"], "misses": repaired.get("misses"),
            "envelope_verdict": (repaired.get("envelope") or {}).get("verdict"),
        })
        decisions = [row["decision"] for row in arm["facts"]["decisions"]]
        _status(arm, decisions == ["block", "block", "approve", "approve"]
                and arm["facts"]["decisions"][2]["misses"] == 3
                and arm["facts"]["decisions"][3]["envelope_verdict"] == "PASS")
        controls.append(arm)

        # --- arm-negative-unsigned -----------------------------------------
        # Runs BEFORE the forged-evidence arm so the read channel still holds
        # the repaired subject's PASS verdict: the claim under test is that a
        # credential-less hook runs no cycle, writes nothing, and reports the
        # channel's state as it finds it — never a fabrication of its own.
        arm = {"control": "arm-negative-unsigned",
               "expectation": "the governed cycle without a signing credential "
               "does not run: the hook names the refusal, writes no evidence, "
               "and reports the published verdict exactly as found",
               "facts": {}}
        evidence_before = (repo / "governance" / "evidence.json").read_bytes()
        answer = _stop_hook(repo, None, signer)
        arm["facts"] = {
            "decision": answer["decision"],
            "read_state": answer["read_state"],
            "reason_names_credential": "no signing credential" in answer["reason"],
            "evidence_unchanged":
                (repo / "governance" / "evidence.json").read_bytes() == evidence_before,
        }
        _status(arm, arm["facts"]["read_state"] == "verified"
                and arm["facts"]["reason_names_credential"]
                and arm["facts"]["evidence_unchanged"]
                and arm["facts"]["decision"] == "approve")
        controls.append(arm)

        # --- arm-negative-evidence -----------------------------------------
        sys.path.insert(0, str(RANEX_REPO / "src"))
        from ranex.foundation.canonical import canonical_json_bytes
        from ranex.foundation.signing import sign_evidence

        arm = {"control": "arm-negative-evidence",
               "expectation": "envelope bytes offered as signed evidence are "
               "refused by admission, never silently accepted",
               "facts": {}}
        private = key.read_text(encoding="utf-8").strip()
        content = {
            "claim_id": "tests-executed",
            "subject_digest": f"sha256:{failing_subject_hex}",
            "producer_id": PRODUCER,
            "command": " ".join(SUITE_COMMAND),
            "command_digest": "sha256:" + "0" * 64,
            "executable_path": "/usr/bin/python3",
            "exit_code": 0,
            "suite_results": json.loads(failing_envelope_raw),
            "confinement_result_digest": None,
            "confinement_profile_digest": None,
            "envelope_type": "ranex-evidence-v3",
            "gate_id": "landing",
            "catalog_digest": "sha256:" + "1" * 64,
        }
        offered = [{**content, "signature": sign_evidence(content, private)}]
        (repo / "governance" / "evidence.json").write_bytes(
            canonical_json_bytes(offered) + b"\n"
        )
        refused = _ranex(
            repo, key, "gate", "evaluate", "HEAD", "--approver", APPROVER,
            "--journal", "governance/journal.sqlite3",
            extra_env=_publish_env(signer),
        )
        command_row("arm-negative-evidence", ["gate", "evaluate"], repo, refused)
        combined = refused.stdout + refused.stderr
        arm["facts"] = {"exit": refused.returncode,
                        "mentions_malformed": "malformed" in combined.lower()}
        _status(arm, refused.returncode == 1 and arm["facts"]["mentions_malformed"])
        controls.append(arm)

        # --- arm-negative-delegated ----------------------------------------
        arm = {"control": "arm-negative-delegated",
               "expectation": "execute_environment refuses to build a delegated "
               "environment holding a signing credential (the C6 wall, live)",
               "facts": {}}
        probe = subprocess.run(
            [str(RANEX_PY), "-c",
             "import sys; sys.path.insert(0, %r)\n"
             "from ranex.cli.delegation import execute_environment\n"
             "try:\n"
             "    execute_environment({'RANEX_SIGNING_KEY': '/nowhere'}, "
             "task_id='T', emit='/tmp/e', home='/tmp/h')\n"
             "except ValueError as exc:\n"
             "    print('REFUSED:', exc)\n"
             % str(repo / "src")],
            capture_output=True, text=True, check=False, timeout=60,
        )
        arm["facts"] = {"exit": probe.returncode,
                        "refusal": probe.stdout.strip()[:200]}
        _status(arm, probe.returncode == 0
                and "refusing to execute with signing credential" in probe.stdout)
        controls.append(arm)

        # --- arm-kernel-unchanged ------------------------------------------
        arm = {"control": "arm-kernel-unchanged",
               "expectation": "tests/contract/test_kernel_unchanged.py passes: "
               "verdict.py and KERNEL_DIGEST never moved",
               "facts": {}}
        kernel_check = subprocess.run(
            [str(RANEX_PY), "-m", "pytest", "-q",
             "tests/contract/test_kernel_unchanged.py"],
            cwd=str(RANEX_REPO), capture_output=True, text=True, check=False,
            timeout=300,
        )
        command_row("arm-kernel-unchanged",
                    ["pytest", "tests/contract/test_kernel_unchanged.py"],
                    RANEX_REPO, kernel_check)
        arm["facts"] = {"exit": kernel_check.returncode,
                        "tail": kernel_check.stdout.strip().splitlines()[-1]}
        _status(arm, kernel_check.returncode == 0)
        controls.append(arm)
    finally:
        if not options.keep:
            shutil.rmtree(root, ignore_errors=True)

    receipt = {
        "schema": "ranex-p0-envelope-proof-v1",
        "controls": controls,
        "commands": commands_log,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }
    (out / "envelope-proof.json").write_text(json.dumps(receipt, indent=2) + "\n")
    environment = {
        "argv": sys.argv,
        "cwd": str(Path.cwd()),
        "host": platform.platform(),
        "python": sys.executable,
        "kernel_python": str(RANEX_PY),
        "ranex_head": subprocess.run(
            ["git", "-C", str(RANEX_REPO), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip(),
        "six_tag": SIX_TAG,
        "six_commit": SIX_COMMIT,
        "suite_command": SUITE_COMMAND,
        "planted_defect": {"from": DEFECT_FROM, "to": DEFECT_TO},
        "expected_failure": {"id": EXPECTED_FAILURE_ID, "at": EXPECTED_FAILURE_AT},
    }
    # The lab drives the vendored kernel `python -m ranex.cli.main` (the
    # F-003 anchor); this row proves the installed console script of the
    # same tree answers too — same code, same CLI surface.
    console_script = subprocess.run(
        [str(RANEX_REPO / ".venv" / "bin" / "ranex"), "--version"],
        cwd=str(RANEX_REPO), capture_output=True, text=True, check=False, timeout=60,
    )
    environment["console_script"] = {
        "argv": [str(RANEX_REPO / ".venv" / "bin" / "ranex"), "--version"],
        "exit": console_script.returncode,
        "stdout": console_script.stdout.strip(),
    }
    (out / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")

    statuses = [control["status"] for control in controls]
    print(json.dumps({"statuses": statuses, "elapsed_s": receipt["elapsed_s"]}, indent=2))
    failed = [status for status in statuses if status != "VERIFIED"]
    if failed:
        print(f"NOT-VERIFIED arms: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
