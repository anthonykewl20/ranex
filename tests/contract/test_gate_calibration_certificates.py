"""#115 — committed gate calibration certificates claim only what they measured."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT = REPO_ROOT / "tools" / "dogfood" / "audits" / "2026-09-30-gate-calibration"
CERTIFICATES = (
    "certificate-marker.json",
    "certificate-landing.json",
    "certificate-handbook-delegate.json",
)
SUMMARY = AUDIT / "SUMMARY.json"
RECALL = AUDIT / "recall-false-pass.json"
STATUSES = frozenset(
    {"VERIFIED", "GAP", "FALSE-PASS", "NON-DETERMINISTIC", "UNVERIFIED"}
)


@pytest.mark.parametrize("name", CERTIFICATES)
def test_certificate_shape_and_repeatability(name: str) -> None:
    path = AUDIT / name
    assert path.is_file(), f"missing certificate {path}"
    certificate = json.loads(path.read_text(encoding="utf-8"))
    assert certificate.get("schema") == "ranex-gate-certificate-v1"
    assert certificate.get("status") in STATUSES
    assert certificate.get("repeats", 0) >= 3
    assert certificate["known_defect"]["caught"] is True
    repeatability = certificate["repeatability"]
    assert repeatability["identical"] is True
    assert repeatability["repeats"] >= 3
    assert certificate["reproducibility"]["status"] == "UNVERIFIED"
    assert "base_freeze" in certificate
    assert certificate["base_freeze"]["freeze_id"] == "base-freeze-v1"


def test_recall_false_pass_names_a_window() -> None:
    receipt = json.loads(RECALL.read_text(encoding="utf-8"))
    assert receipt["status"] == "FALSE-PASS"
    assert receipt["as_expected"] is True
    recall = receipt["recall"]
    assert recall["determinable"] is True
    assert recall["suspect_count"] >= 1
    assert recall["suspect_positions"]
    assert recall["suspect_verdict_digests"]


def test_summary_licenses_only_what_certificates_cover() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert summary["schema"] == "ranex-gate-calibration-summary-v1"
    assert summary["statuses"]["marker"] == "VERIFIED"
    assert summary["statuses"]["landing"] == "VERIFIED"
    assert summary["statuses"]["handbook-governed-delegate"] == "VERIFIED"
    assert summary["gauge_rr"]["reproducibility"]["status"] == "UNVERIFIED"
    assert summary["UNVERIFIED"], "production statement must leave an UNVERIFIED list"
    for key in (
        "1_known_defect_detection",
        "2_firing_rate_recorded",
        "3_recall_armed",
        "4_built_vs_calibrated",
    ):
        assert summary["map_8_4_consequences"][key]["status"] == "satisfied"


def test_bom_calibrated_rows_resolve_under_this_audit() -> None:
    import yaml

    bom = yaml.safe_load(
        (REPO_ROOT / "governance" / "bom.yaml").read_text(encoding="utf-8")
    )
    named = [
        part["calibrated"]
        for part in bom["parts"]
        if part.get("calibrated")
    ]
    assert named, "at least one BOM row must name a calibration receipt"
    for receipt in named:
        assert (REPO_ROOT / receipt).is_file(), receipt
