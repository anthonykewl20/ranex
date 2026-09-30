"""The promotion command against a real git checkout, end to end.

SLICE-095. The unit tests judge the pure function; these rows hold the
command to its read discipline: the freeze is the gauge, so it is read
committed at the ref being judged (an uncommitted edit is an unreviewed
rewrite of every future baseline), while the claim is read from disk as it
stands, because the command's job is to judge what was claimed.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes

KERNEL = Path(__file__).resolve().parents[2]

DIGEST = "sha256:" + "0" * 64


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=promotion@ranex.invalid",
         "-c", "user.name=ranex-promotion-test", *args],
        capture_output=True, text=True, check=False,
    )


def _invoke(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "GIT_", "PYTHON"))
    }
    environment["PYTHONPATH"] = str(KERNEL / "src")
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", "promotion", "evaluate",
         "--external-repository", str(repo), *args],
        cwd=str(repo), env=environment, capture_output=True, text=True,
        check=False, timeout=60,
    )


def synthetic_freeze() -> dict[str, object]:
    return {
        "schema": "ranex-base-freeze-v1",
        "freeze_id": "base-freeze-v1",
        "minted": "2026-09-25",
        "kernel_commit": "638f7d8613fe5cbdeed96b89c103d5185ce39866",
        "kernel_digest": DIGEST,
        "vendored_src_tree": "sha256:" + "7" * 40,
        "subjects": {
            "six@1.17.0": {
                "commit": "ebd9b3af90247b8858d415a05e96e9ee61e48d07",
                "suite_manifest_digest": "sha256:" + "1" * 64,
                "control_bank_digest": "sha256:" + "8" * 64,
            },
        },
        "reference_metrics": {
            "six": {
                "raw_false_pass": 0.625,
                "honest_false_pass": 0.025,
                "tau_max_honest_kill_rate": 0.6,
            },
        },
        "receipts_digest": "sha256:" + "2" * 64,
        "source_prereg_digest": "sha256:" + "3" * 64,
        "journal_head_at_freeze": DIGEST,
        "mint_receipts_digest": "sha256:" + "1" * 64,
        "provenance": {
            "source": "synthetic integration fixture",
            "report_digest": "sha256:" + "2" * 64,
        },
    }


def paired_claim() -> dict[str, object]:
    return {
        "schema": "ranex-promotion-claim-v1",
        "claim_id": "integration-positive",
        "treatment": "synthetic treatment for the command surface",
        "base_freeze": "base-freeze-v1",
        "marginal_deltas": [
            {"axis": "six.raw_false_pass", "base": 0.625,
             "treatment": 0.6, "delta": -0.025},
        ],
        "evidence_receipts_digest": "sha256:" + "2" * 64,
    }


@pytest.fixture
def lab(tmp_path: Path) -> Path:
    repo = tmp_path / "promotion-lab"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0
    calibration = repo / "governance" / "calibration"
    calibration.mkdir(parents=True)
    (calibration / "base-freeze-v1.json").write_bytes(
        canonical_json_bytes(synthetic_freeze())
    )
    claims = repo / "claims"
    claims.mkdir()
    (claims / "positive.json").write_bytes(canonical_json_bytes(paired_claim()))
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", "synthetic freeze and claims").returncode == 0
    return repo


def _write_claim(repo: Path, name: str, claim: dict[str, object]) -> str:
    path = repo / "claims" / name
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(canonical_json_bytes(claim))
    return f"claims/{name}"


def _without_citation() -> dict[str, object]:
    return {k: v for k, v in paired_claim().items() if k != "base_freeze"}


def test_admits_a_paired_claim_citing_the_committed_freeze(lab: Path) -> None:
    result = _invoke(lab, "--claim", "claims/positive.json")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("ADMITTED")
    assert "freeze=base-freeze-v1" in result.stdout


def test_refuses_a_claim_lacking_a_freeze_id(lab: Path) -> None:
    named = _write_claim(lab, "uncited.json", _without_citation())
    result = _invoke(lab, "--claim", named)
    assert result.returncode == 1
    assert "REFUSED" in result.stdout
    assert "no-freeze-citation" in result.stdout


def test_refuses_an_uncited_claim_with_no_calibration_directory(
    tmp_path: Path,
) -> None:
    # No gauge exists anywhere in the repo: the refusal is still the gate's
    # structured one, never a crash and never a default ADMIT.
    repo = tmp_path / "empty-lab"
    repo.mkdir()
    assert _git(repo, "init", "-q").returncode == 0
    (repo / "claims").mkdir()
    (repo / "claims" / "uncited.json").write_bytes(
        canonical_json_bytes(_without_citation())
    )
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm", "no calibration at all").returncode == 0
    result = _invoke(repo, "--claim", "claims/uncited.json")
    assert result.returncode == 1
    assert "no-freeze-citation" in result.stdout


def test_refuses_an_invented_baseline(lab: Path) -> None:
    claim = paired_claim()
    claim["marginal_deltas"] = [
        {"axis": "six.raw_false_pass", "base": 0.5,
         "treatment": 0.6, "delta": 0.1},
    ]
    named = _write_claim(lab, "invented.json", claim)
    result = _invoke(lab, "--claim", named)
    assert result.returncode == 1
    assert "unpaired-baseline" in result.stdout


def test_refuses_a_constant_tau(lab: Path) -> None:
    claim = paired_claim()
    claim["tau"] = [{"axis": "six.tau_max_honest_kill_rate", "value": 0.8}]
    named = _write_claim(lab, "constant-tau.json", claim)
    result = _invoke(lab, "--claim", named)
    assert result.returncode == 1
    assert "tau-not-derived-from-freeze" in result.stdout


def test_refuses_against_a_committed_but_malformed_freeze(lab: Path) -> None:
    frozen = synthetic_freeze()
    frozen["reference_metrics"]["six"]["raw_false_pass"] = "25/40"
    (lab / "governance" / "calibration" / "base-freeze-v1.json").write_bytes(
        canonical_json_bytes(frozen)
    )
    assert _git(lab, "add", "-A").returncode == 0
    assert _git(lab, "commit", "-qm", "commit a broken gauge").returncode == 0
    result = _invoke(lab, "--claim", "claims/positive.json")
    assert result.returncode == 1
    assert "freeze-malformed" in result.stdout


def test_refuses_to_read_an_uncommitted_freeze_edit(lab: Path) -> None:
    # A gauge the working tree disagrees with the ref about is an unreviewed
    # rewrite of every future baseline: operational refusal, never a quiet
    # evaluation against the edited bytes.
    frozen = synthetic_freeze()
    frozen["reference_metrics"]["six"]["raw_false_pass"] = 0.1
    (lab / "governance" / "calibration" / "base-freeze-v1.json").write_bytes(
        canonical_json_bytes(frozen)
    )
    result = _invoke(lab, "--claim", "claims/positive.json")
    assert result.returncode == 2
    assert "differs from the version committed" in result.stderr


def test_refuses_a_freeze_that_was_never_committed(lab: Path) -> None:
    frozen = synthetic_freeze()
    frozen["freeze_id"] = "base-freeze-v2"
    (lab / "governance" / "calibration" / "base-freeze-v2.json").write_bytes(
        canonical_json_bytes(frozen)
    )
    claim = paired_claim() | {"base_freeze": "base-freeze-v2"}
    named = _write_claim(lab, "cites-v2.json", claim)
    result = _invoke(lab, "--claim", named)
    assert result.returncode == 2
    assert "carries no base freeze" in result.stderr


def test_json_decision_bytes_are_identical_across_three_runs(lab: Path) -> None:
    outputs = [
        _invoke(lab, "--claim", "claims/positive.json", "--json").stdout
        for _ in range(3)
    ]
    assert len(set(outputs)) == 1
    record = json.loads(outputs[0])
    assert record["verdict"] == "ADMITTED"
    assert record["schema"] == "ranex-promotion-decision-v1"
    assert record["freeze_digest"] == "sha256:" + hashlib.sha256(
        canonical_json_bytes(synthetic_freeze())
    ).hexdigest()


def test_json_refusal_bytes_are_identical_across_three_runs(lab: Path) -> None:
    named = _write_claim(lab, "uncited.json", _without_citation())
    outputs = [
        _invoke(lab, "--claim", named, "--json").stdout for _ in range(3)
    ]
    assert len(set(outputs)) == 1
    assert json.loads(outputs[0])["verdict"] == "REFUSED"
