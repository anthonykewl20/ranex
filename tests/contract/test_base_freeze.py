"""The committed BASE freeze is a gauge, and gauges are held to their bytes.

SLICE-093 / ADR-063. Three bindings, each one direction of the same rule
(that the instrument is what review saw, not what a treatment wishes it
said):

* the committed freeze validates and is exact canonical bytes — a gauge
  whose bytes drift from its parsed meaning is two gauges;
* its kernel_digest is verdict.py's actual bytes, so the kernel the BASE
  numbers were measured on is provably the kernel this tree ships;
* its digest is the digest the mint receipt recorded, and the standing
  controls hold: the gate REFUSES an uncited improvement claim and ADMITS
  the report's paired C4 marginal against v1, through the real CLI, on the
  real committed freeze, in this repository.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ranex.cli.main import main
from ranex.foundation.canonical import canonical_json_bytes
from ranex.governed_execution.promotion_gate import validate_base_freeze

REPO_ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = REPO_ROOT / "governance" / "calibration" / "base-freeze-v1.json"
RECEIPT_PATH = (
    REPO_ROOT / "tools" / "dogfood" / "audits" / "2026-09-25-base-freeze"
    / "freeze-proof.json"
)
VERDICT_PATH = (
    REPO_ROOT / "src" / "ranex" / "governed_execution" / "domain" / "verdict.py"
)


def _committed_bytes() -> bytes:
    assert FREEZE_PATH.is_file(), (
        "governance/calibration/base-freeze-v1.json is committed"
    )
    return FREEZE_PATH.read_bytes()


def test_freeze_validates_and_is_exact_canonical_bytes() -> None:
    raw = _committed_bytes()
    freeze = validate_base_freeze(json.loads(raw))
    assert raw == canonical_json_bytes(freeze), (
        "the freeze file must be exact canonical JSON bytes: its digest is "
        "the binding, and a reformatted file is a different gauge"
    )


def test_freeze_kernel_digest_is_this_kernel() -> None:
    freeze = validate_base_freeze(json.loads(_committed_bytes()))
    actual = "sha256:" + hashlib.sha256(VERDICT_PATH.read_bytes()).hexdigest()
    assert freeze["kernel_digest"] == actual, (
        "the frozen kernel identity must equal this tree's verdict.py bytes; "
        "a kernel move is a deliberate act that mints a new freeze, never an "
        "edit to this one"
    )


def test_freeze_digest_is_the_digest_the_receipt_recorded() -> None:
    receipt = json.loads(RECEIPT_PATH.read_bytes())
    actual = "sha256:" + hashlib.sha256(_committed_bytes()).hexdigest()
    assert receipt["freeze_digest"] == actual, (
        "the mint receipt binds the freeze by digest; disagreement means the "
        "gauge moved after its proof"
    )


def _claim_path(name: str, claim: dict[str, object]) -> str:
    directory = REPO_ROOT / ".local" / "promotion-claims"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(json.dumps(claim, indent=2, sort_keys=True) + "\n")
    return str(path.relative_to(REPO_ROOT))


def test_gate_refuses_an_improvement_claim_without_a_freeze_id(
    capsys: pytest.CaptureFixture[str],
) -> None:
    freeze = validate_base_freeze(json.loads(_committed_bytes()))
    claim = {
        "schema": "ranex-promotion-claim-v1",
        "claim_id": "standing-negative-control",
        "treatment": "any measured treatment, stated without its gauge",
        "marginal_deltas": [
            {"axis": "six.raw_false_pass", "base": 0.625,
             "treatment": 0.6, "delta": -0.025},
        ],
        "evidence_receipts_digest": freeze["receipts_digest"],
    }
    exit_code = main([
        "promotion", "evaluate", "--claim",
        _claim_path("contract-negative.json", claim), "--json",
    ])
    record = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert record["verdict"] == "REFUSED"
    assert [cause["cause"] for cause in record["causes"]] == ["no-freeze-citation"]


def test_gate_admits_the_paired_c4_marginal_against_v1(
    capsys: pytest.CaptureFixture[str],
) -> None:
    freeze = validate_base_freeze(json.loads(_committed_bytes()))
    metrics = freeze["reference_metrics"]
    claim = {
        "schema": "ranex-promotion-claim-v1",
        "claim_id": "standing-positive-control",
        "treatment": "differential coexistence oracle (composed with BASE and C3)",
        "base_freeze": "base-freeze-v1",
        "marginal_deltas": [
            {"axis": "six.raw_false_pass",
             "base": metrics["six"]["raw_false_pass"],
             "treatment": 0.6, "delta": 0.6 - metrics["six"]["raw_false_pass"]},
            {"axis": "ranex-handbook.false_pass",
             "base": metrics["ranex-handbook"]["false_pass"],
             "treatment": 0.0,
             "delta": -metrics["ranex-handbook"]["false_pass"]},
        ],
        "tau": [{"axis": "six.tau_max_honest_kill_rate",
                 "value": metrics["six"]["tau_max_honest_kill_rate"]}],
        "evidence_receipts_digest": freeze["receipts_digest"],
    }
    exit_code = main([
        "promotion", "evaluate", "--claim",
        _claim_path("contract-positive.json", claim),
    ])
    captured = capsys.readouterr().out
    assert exit_code == 0
    assert captured.startswith("ADMITTED")
