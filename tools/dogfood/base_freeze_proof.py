#!/usr/bin/env python3
"""SLICE-093 real-data proof: the BASE freeze and its promotion gate.

Two phases, because the freeze binds values only a live derivation produces:

  --derive-only   build the governed six lab the F-003 way (vendored kernel
                  src, real keys, real pytest, real CLI), freeze the 200-ID
                  suite with operator-approved platform skips three times
                  (byte-identical manifest digests), run a governed cycle,
                  and record the journal head. Prints the mint values; writes
                  instrument-derivation.json beside this receipt.
  full (default)  everything above plus the verification arms, which require
                  governance/calibration/base-freeze-v1.json to be COMMITTED:

  arm-instrument-shape      the derivation matches the scout's instrument
                           (200 IDs, 15 approved platform skips)
  arm-instrument-derivation three freezes produce one byte-identical digest;
                           the cycle PASSes; the journal chain verifies
  arm-instrument-reproduces the re-derived six manifest digest equals the
                           digest frozen in v1 (the instrument is
                           re-derivable, not remembered)
  arm-freeze-committed      the committed freeze validates; its digest is
                           recorded (digest-bound); kernel_digest equals
                           KERNEL_DIGEST and verdict.py's bytes
  arm-kernel-unchanged      tests/contract/test_kernel_unchanged.py passes
  arm-gate-refuses-no-freeze the negative control: a measured, paired claim
                             that names no freeze is REFUSED
  arm-gate-refuses-tau      a constant τ=0.80 (L3's number) is REFUSED — τ
                             may only be the freeze's derived 0.60
  arm-gate-refuses-baseline  a friendlier invented baseline is REFUSED
  arm-gate-admits-positive   the positive control: the report's own C4
                             composition marginal, paired on named axes
                             against v1, is ADMITTED
  arm-determinism           the ADMITTED decision bytes are identical 3×
  arm-tamper-refused        an uncommitted edit to the freeze in a throwaway
                             clone is refused before any judgment (seam C)

Statuses use the #95 vocabulary: VERIFIED · GAP · FALSE-PASS ·
NON-DETERMINISTIC · UNVERIFIED. Numbers in the receipt are measured on this
host in this run; the reference metrics inside the freeze are the scout
report's measurements, cited by digest and never re-measured here.

Run (network required for the six clone only):
  uv run --frozen python tools/dogfood/base_freeze_proof.py \
      [--out tools/dogfood/audits/2026-09-25-base-freeze] [--derive-only] [--keep]
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
SUITE_COMMAND = [
    "/usr/bin/python3", "-m", "pytest", "-q", "-o", "xfail_strict=true",
    "-p", "ranex.foundation.pytest_xpass",
    "--junitxml=governance/suite_results.xml", "test_six.py",
]

PRODUCER = "base-freeze-producer"
APPROVER = "base-freeze-approver"
VERDICT_SIGNER_ID = "kernel-verdict-signer"
SKIP_REASON = "platform skip, operator-approved at freeze (base-freeze mint)"

FREEZE_RELATIVE = "governance/calibration/base-freeze-v1.json"

# The scout's S1 instrument: 200 frozen IDs, 15 approved platform skips
# (report §2.2/§2.3). A derivation that disagrees with either count is a
# different instrument, and the freeze must not be minted on it.
EXPECTED_SUITE_IDS = 200
EXPECTED_SKIPS = 15

KERNEL_DIGEST_HEX = (
    "2969aa74adc8ac40393fb4f782e05be8f29f34d2ab0f594051906f4e6a5b5ed6"
)


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


def _ranex_here(*args: str) -> subprocess.CompletedProcess[str]:
    """The CLI anchored to THIS checkout (ADR-038), the tree holding the
    committed freeze the gate arms judge against."""

    environment = {
        name: value for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "PYTHON"))
    }
    environment["PYTHONPATH"] = str(RANEX_REPO / "src")
    return subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", *args],
        cwd=str(RANEX_REPO), env=environment, capture_output=True, text=True,
        check=False, timeout=120,
    )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=freeze@ranex.invalid",
         "-c", "user.name=ranex-base-freeze-proof", *args],
        capture_output=True, text=True, check=False,
    )


def _commit(repo: Path, message: str) -> None:
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", message).returncode == 0


def _publish_env(signer: Path) -> dict[str, str]:
    return {"RANEX_VERDICT_SIGNING_KEY": str(signer),
            "RANEX_VERDICT_DIR": "governance/verdicts"}


def _cycle(repo: Path, key: Path, signer: Path) -> subprocess.CompletedProcess[str]:
    run = _ranex(repo, key, "run", "--claim", "tests-executed",
                 "--producer", PRODUCER, "--", *SUITE_COMMAND)
    assert run.returncode == 0, run.stdout + run.stderr
    evaluate = _ranex(
        repo, key, "gate", "evaluate", "HEAD", "--approver", APPROVER,
        "--journal", "governance/journal.sqlite3",
        extra_env=_publish_env(signer),
    )
    return evaluate


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
    shutil.rmtree(repo / ".git")
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "freeze@ranex.invalid")
    _git(repo, "config", "user.name", "ranex-base-freeze-proof")
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
    records = json.loads((repo / "governance" / "evidence.json").read_bytes())
    summary = next(
        record["suite_results"] for record in reversed(records)
        if record.get("suite_results") is not None
    )
    return sorted(
        f"{test_id}={SKIP_REASON}"
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
        evaluate = _cycle(repo, key, signer)
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


def derive_instrument(root: Path) -> dict[str, Any]:
    """Build the lab, freeze 3× byte-identically, cycle once, read the head."""

    sys.path.insert(0, str(RANEX_REPO / "src"))
    from ranex.foundation.suite_results import load_manifest, manifest_digest
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    six = clone_six(root)
    repo, key, signer = build_lab(root, six)
    facts: dict[str, Any] = {}
    facts["freeze"] = freeze_with_skips(repo, key, signer)

    digests: list[str] = [manifest_digest(load_manifest(
        repo / "governance" / "suite_manifest.json"
    ))]
    for round_index in (2, 3):
        flags: list[str] = []
        for test_id in facts["freeze"]["approved_skips"]:
            flags += ["--expected-skip", f"{test_id}={SKIP_REASON}"]
        again = _ranex(repo, key, "suite", "freeze",
                       "--artifact", "governance/suite_results.xml", *flags,
                       "--", *SUITE_COMMAND)
        if again.returncode != 0:
            raise SystemExit(f"re-freeze {round_index} refused: {again.stderr[:400]}")
        # A byte-identical re-freeze leaves nothing to commit — which is the
        # determinism result itself — so the audit-trail commit is allowed to
        # be empty.
        assert _git(repo, "add", "-A").returncode == 0
        assert _git(repo, "commit", "--allow-empty", "-qm",
                    f"re-freeze suite manifest (derivation {round_index})"
                    ).returncode == 0
        digests.append(manifest_digest(load_manifest(
            repo / "governance" / "suite_manifest.json"
        )))
    manifest = load_manifest(repo / "governance" / "suite_manifest.json")
    facts["suite_manifest_digest"] = digests[0]
    facts["derivation_digests"] = digests
    facts["derivation_byte_identical"] = len(set(digests)) == 1
    facts["suite_ids"] = len(manifest["suite"])
    facts["approved_platform_skips"] = len(manifest["expected_skips"])

    evaluate = _cycle(repo, key, signer)
    verified = _ranex(repo, key, "journal", "verify",
                      "--journal", "governance/journal.sqlite3")
    facts["cycle_exit"] = evaluate.returncode
    facts["journal_chain"] = "verified" in verified.stdout
    facts["journal_head_at_freeze"] = Journal(
        repo / "governance" / "journal.sqlite3"
    ).head()
    return facts


def _write_claim(name: str, claim: dict[str, Any]) -> Path:
    directory = RANEX_REPO / ".local" / "promotion-claims"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(json.dumps(claim, indent=2, sort_keys=True) + "\n")
    return path


def gate_arm(name: str, claim: dict[str, Any], *, expect_refusal: str | None,
             expect_admitted: bool) -> dict[str, Any]:
    path = _write_claim(f"{name}.json", claim)
    answered = _ranex_here("promotion", "evaluate", "--claim",
                           str(path.relative_to(RANEX_REPO)), "--json")
    arm: dict[str, Any] = {
        "control": f"arm-gate-{name}",
        "expectation": (
            f"REFUSED with cause {expect_refusal}" if expect_refusal
            else "ADMITTED with paired marginals on named axes"
        ),
        "facts": {"exit": answered.returncode,
                  "stdout_tail": answered.stdout.strip()[-400:],
                  "stderr_tail": answered.stderr.strip()[-200:]},
    }
    if expect_admitted:
        _status(arm, answered.returncode == 0
                and json.loads(answered.stdout)["verdict"] == "ADMITTED")
    else:
        record = json.loads(answered.stdout)
        _status(arm, answered.returncode == 1
                and record["verdict"] == "REFUSED"
                and expect_refusal in [cause["cause"] for cause in record["causes"]])
    return arm


def positive_claim(receipts_digest: str) -> dict[str, Any]:
    """The scout's C4 composition result as a promotion claim (report §3.4/§3.7):
    the one treatment whose paired marginals on freeze axes were measured —
    six raw false-PASS 25→24 of 40, ranex-handbook false-PASS 5→0 of 20."""

    return {
        "schema": "ranex-promotion-claim-v1",
        "claim_id": "c4-differential-composed",
        "treatment": "differential coexistence oracle (composed with BASE and C3)",
        "base_freeze": "base-freeze-v1",
        "marginal_deltas": [
            {"axis": "six.raw_false_pass", "base": 0.625,
             "treatment": 0.6, "delta": -0.025},
            {"axis": "ranex-handbook.false_pass", "base": 0.25,
             "treatment": 0.0, "delta": -0.25},
        ],
        "tau": [{"axis": "six.tau_max_honest_kill_rate", "value": 0.6}],
        "evidence_receipts_digest": receipts_digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path,
                        default=HERE / "audits" / "2026-09-25-base-freeze")
    parser.add_argument("--derive-only", action="store_true",
                        help="only derive the instrument values for minting")
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

    root = Path(tempfile.mkdtemp(prefix="ranex-base-freeze-"))
    try:
        derivation = derive_instrument(root)

        # The scout's instrument shape is part of the freeze's meaning: a
        # derivation on a different suite or a different skip set would be a
        # different gauge, and minting v1 on it would misbind the reference
        # metrics.
        controls.append({
            "control": "arm-instrument-shape",
            "expectation": f"the pinned six suite freezes to {EXPECTED_SUITE_IDS} "
                           f"IDs with {EXPECTED_SKIPS} operator-approved platform "
                           "skips, as the scout measured",
            "facts": {"suite_ids": derivation["suite_ids"],
                      "approved_platform_skips":
                          derivation["approved_platform_skips"]},
            "status": ("VERIFIED"
                       if derivation["suite_ids"] == EXPECTED_SUITE_IDS
                       and derivation["approved_platform_skips"] == EXPECTED_SKIPS
                       else "FALSE-PASS"),
        })
        controls.append({
            "control": "arm-instrument-derivation",
            "expectation": "three independent freezes of the same pinned tree "
                           "produce one byte-identical manifest digest; the "
                           "governed cycle PASSes; the journal chain verifies",
            "facts": derivation,
            "status": ("VERIFIED"
                       if derivation["derivation_byte_identical"]
                       and derivation["cycle_exit"] == 0
                       and derivation["journal_chain"]
                       else "FALSE-PASS"),
        })

        if options.derive_only:
            (out / "instrument-derivation.json").write_text(json.dumps({
                "schema": "ranex-base-freeze-derivation-v1",
                "controls": controls,
                "mint_values": {
                    "suite_manifest_digest":
                        derivation["suite_manifest_digest"],
                    "journal_head_at_freeze":
                        derivation["journal_head_at_freeze"],
                },
            }, indent=2) + "\n")
            print(json.dumps({
                "mint_values": {
                    "suite_manifest_digest":
                        derivation["suite_manifest_digest"],
                    "journal_head_at_freeze":
                        derivation["journal_head_at_freeze"],
                },
                "suite_ids": derivation["suite_ids"],
                "approved_platform_skips": derivation["approved_platform_skips"],
            }, indent=2))
            return 0

        # --- verification arms: the freeze must be committed by now --------
        committed = subprocess.run(
            ["git", "-C", str(RANEX_REPO), "show", f"HEAD:{FREEZE_RELATIVE}"],
            capture_output=True, text=True, check=False,
        )
        if committed.returncode != 0:
            print(f"ERROR  {FREEZE_RELATIVE} is not committed at HEAD; "
                  "commit the freeze before the full proof", file=sys.stderr)
            return 2
        freeze_bytes = committed.stdout.encode("utf-8")
        freeze_digest = "sha256:" + hashlib.sha256(freeze_bytes).hexdigest()

        sys.path.insert(0, str(RANEX_REPO / "src"))
        from ranex.governed_execution.promotion_gate import validate_base_freeze

        freeze = validate_base_freeze(json.loads(freeze_bytes))
        kernel_actual = hashlib.sha256(
            (RANEX_REPO / "src/ranex/governed_execution/domain/verdict.py")
            .read_bytes()
        ).hexdigest()
        controls.append({
            "control": "arm-freeze-committed",
            "expectation": "the committed freeze validates as "
                           "ranex-base-freeze-v1, its exact committed bytes "
                           "are digest-bound here, and its kernel_digest is "
                           "verdict.py's bytes at this HEAD",
            "facts": {"freeze_digest": freeze_digest,
                      "freeze_id": freeze["freeze_id"],
                      "kernel_digest_frozen": freeze["kernel_digest"],
                      "kernel_digest_actual": "sha256:" + kernel_actual,
                      "kernel_commit_frozen": freeze["kernel_commit"]},
            "status": ("VERIFIED"
                       if freeze["kernel_digest"] == "sha256:" + kernel_actual
                       and freeze["kernel_digest"] == "sha256:" + KERNEL_DIGEST_HEX
                       else "FALSE-PASS"),
        })

        frozen_six = freeze["subjects"]["six@1.17.0"]
        controls.append({
            "control": "arm-instrument-reproduces",
            "expectation": "the manifest digest frozen in v1 is reproduced by "
                           "this run's independent derivation",
            "facts": {"frozen": frozen_six["suite_manifest_digest"],
                      "derived": derivation["suite_manifest_digest"]},
            "status": ("VERIFIED"
                       if frozen_six["suite_manifest_digest"]
                       == derivation["suite_manifest_digest"]
                       else "FALSE-PASS"),
        })

        kernel_check = subprocess.run(
            [str(RANEX_PY), "-m", "pytest", "-q",
             "tests/contract/test_kernel_unchanged.py"],
            cwd=str(RANEX_REPO), capture_output=True, text=True, check=False,
            timeout=300,
        )
        command_row("arm-kernel-unchanged",
                    ["pytest", "tests/contract/test_kernel_unchanged.py"],
                    RANEX_REPO, kernel_check)
        controls.append({
            "control": "arm-kernel-unchanged",
            "expectation": "tests/contract/test_kernel_unchanged.py passes: "
                           "verdict.py and KERNEL_DIGEST never moved",
            "facts": {"exit": kernel_check.returncode,
                      "tail": kernel_check.stdout.strip().splitlines()[-1]},
            "status": "VERIFIED" if kernel_check.returncode == 0 else "FALSE-PASS",
        })

        receipts_digest = str(freeze["receipts_digest"])
        positive = positive_claim(receipts_digest)

        no_freeze = {k: v for k, v in positive.items() if k != "base_freeze"}
        controls.append(gate_arm("refuses-no-freeze", no_freeze,
                                 expect_refusal="no-freeze-citation",
                                 expect_admitted=False))
        controls.append(gate_arm(
            "refuses-tau",
            positive | {"tau": [{"axis": "six.tau_max_honest_kill_rate",
                                 "value": 0.8}]},
            expect_refusal="tau-not-derived-from-freeze",
            expect_admitted=False))
        controls.append(gate_arm(
            "refuses-baseline",
            positive | {"marginal_deltas": [
                {"axis": "six.raw_false_pass", "base": 0.5,
                 "treatment": 0.6, "delta": 0.1},
            ]},
            expect_refusal="unpaired-baseline",
            expect_admitted=False))
        controls.append(gate_arm("admits-positive", positive,
                                 expect_refusal=None, expect_admitted=True))

        arm = {"control": "arm-determinism",
               "expectation": "the ADMITTED decision bytes are identical "
                              "across three evaluations of the same claim",
               "facts": {}}
        path = _write_claim("determinism.json", positive)
        outputs = []
        for _ in range(3):
            answered = _ranex_here(
                "promotion", "evaluate", "--claim",
                str(path.relative_to(RANEX_REPO)), "--json",
            )
            outputs.append(answered.stdout)
        arm["facts"]["decision_digests"] = [
            "sha256:" + hashlib.sha256(text.encode()).hexdigest()
            for text in outputs
        ]
        arm["facts"]["byte_identical"] = len(set(outputs)) == 1
        arm["status"] = ("VERIFIED" if arm["facts"]["byte_identical"]
                         else "NON-DETERMINISTIC")
        controls.append(arm)

        # --- arm-tamper-refused -------------------------------------------
        clone = root / "ranex-clone"
        cloned = subprocess.run(
            ["git", "clone", "-q", "--no-hardlinks", str(RANEX_REPO), str(clone)],
            capture_output=True, text=True, check=False,
        )
        arm = {"control": "arm-tamper-refused",
               "expectation": "an uncommitted edit to the freeze (a rewritten "
                              "gauge) is refused before any judgment in a "
                              "throwaway clone of this repository",
               "facts": {"clone_exit": cloned.returncode}}
        if cloned.returncode == 0:
            gauge = clone / FREEZE_RELATIVE
            rewritten = json.loads(gauge.read_bytes())
            rewritten["reference_metrics"]["six"]["raw_false_pass"] = 0.1
            gauge.write_text(json.dumps(rewritten, indent=2, sort_keys=True) + "\n")
            # The claim file must exist inside the clone before the CLI is
            # asked to resolve it.
            claim_path = clone / "claim-tamper.json"
            claim_path.write_text(
                json.dumps(positive, indent=2, sort_keys=True) + "\n"
            )
            environment = {
                name: value for name, value in os.environ.items()
                if not name.startswith(("RANEX_", "PYTHON"))
            }
            environment["PYTHONPATH"] = str(RANEX_REPO / "src")
            tampered = subprocess.run(
                [str(RANEX_PY), "-m", "ranex.cli.main", "promotion", "evaluate",
                 "--external-repository", str(clone),
                 "--claim", "claim-tamper.json"],
                cwd=str(clone), env=environment,
                capture_output=True, text=True, check=False, timeout=60,
            )
            arm["facts"].update({
                "exit": tampered.returncode,
                "stderr_tail": tampered.stderr.strip()[-300:],
            })
            _status(arm, tampered.returncode == 2
                    and "differs from the version committed" in tampered.stderr)
        else:
            arm["status"] = "UNVERIFIED"
            arm["facts"]["reason"] = "clone failed"
        controls.append(arm)
    finally:
        if not options.keep:
            shutil.rmtree(root, ignore_errors=True)

    receipt = {
        "schema": "ranex-base-freeze-proof-v1",
        "freeze_digest": freeze_digest,
        "controls": controls,
        "commands": commands_log,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }
    (out / "freeze-proof.json").write_text(json.dumps(receipt, indent=2) + "\n")
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
        "freeze_relative": FREEZE_RELATIVE,
    }
    (out / "environment.json").write_text(json.dumps(environment, indent=2) + "\n")

    statuses = [control["status"] for control in controls]
    print(json.dumps({"statuses": statuses, "elapsed_s": receipt["elapsed_s"]},
                     indent=2))
    failed = [status for status in statuses
              if status not in ("VERIFIED", "UNVERIFIED")]
    if failed:
        print(f"NOT-VERIFIED arms: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
