"""A VERIFIED control must have refused something. MAP §8.4, issue #95.

`tools/dogfood/calibration.py` exists because "VERIFIED" said with no negative
control beside it is an unfalsifiable claim: the check passed, and nobody knows
whether it could ever fail. This file holds that rule to the receipts, and
holds the classifier to being able to raise its own alarms.

Two directions, because either alone is decoration:

* every committed calibration receipt is well formed — a VERIFIED case names a
  negative control that was actually refused, and a FALSE-PASS names the window
  of verdicts it invalidates;
* the classifier itself fires. A runner that can only ever return VERIFIED
  would satisfy the first direction perfectly.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDITS = REPO_ROOT / "tools" / "dogfood" / "audits"
MODULE = REPO_ROOT / "tools" / "dogfood" / "calibration.py"


def _calibration():
    """Load the driver by path: tools/ is operator tooling, not a package."""

    spec = importlib.util.spec_from_file_location("ranex_calibration", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Registered BEFORE execution: with postponed annotations, dataclasses
    # resolves a field's type through `sys.modules[cls.__module__]`, which is
    # None for a module that has not been registered yet.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _receipts() -> list[Path]:
    if not AUDITS.is_dir():
        return []
    return [
        path
        for path in sorted(AUDITS.rglob("calibration.json"))
        if json.loads(path.read_text(encoding="utf-8")).get("schema") == "ranex-calibration-v1"
    ]


def _violations(receipt: dict) -> list[str]:
    """Every way a receipt can claim more than it measured."""

    problems: list[str] = []
    repeats = receipt.get("repeats")
    for case in receipt.get("cases", []):
        name = case.get("control", "<unnamed>")
        status = case.get("status")
        negative = case.get("negative")
        if status == "VERIFIED":
            if not negative:
                problems.append(f"{name}: VERIFIED with no negative control recorded")
                continue
            if not negative.get("runs"):
                problems.append(f"{name}: VERIFIED but its negative control never ran")
            if any(negative.get("ok", [])):
                problems.append(
                    f"{name}: VERIFIED while its negative control was ACCEPTED — "
                    "that is a FALSE-PASS wearing a green label"
                )
        if status == "FALSE-PASS" and "recall" not in case:
            problems.append(
                f"{name}: FALSE-PASS without a recall window; §8.4 recalls what a bad "
                "gauge approved, and a receipt that does not name it recalls nothing"
            )
        if not isinstance(case.get("repeats", repeats), int) or case.get("repeats", repeats) < 3:
            problems.append(f"{name}: fewer than 3 identical-input repeats")
    return problems


@pytest.mark.parametrize("receipt", _receipts(), ids=lambda p: p.parent.name)
def test_a_committed_receipt_claims_only_what_it_measured(receipt: Path) -> None:
    problems = _violations(json.loads(receipt.read_text(encoding="utf-8")))
    assert not problems, f"{receipt.relative_to(REPO_ROOT)}: {problems}"


# --- the classifier must be able to raise its own alarms --------------------


def _observation(module, ok: bool, facts: dict | None = None):
    return module.Observation(ok=ok, facts=facts if facts is not None else {"n": 1})


def test_a_control_with_no_negative_is_a_gap_not_a_pass() -> None:
    module = _calibration()
    calibration = module.Calibration(out=Path("/dev/null").parent / "unused-calibration")
    case = calibration._classify(
        module.Control("c", "e", lambda: _observation(module, True)),
        [_observation(module, True)],
        [],
    )
    assert case[0] is module.Status.GAP, case


def test_an_accepted_negative_is_a_false_pass() -> None:
    """The alarm this whole file exists for: a check that cannot block."""

    module = _calibration()
    calibration = module.Calibration(out=Path("/tmp/unused-calibration"))
    status, reason = calibration._classify(
        module.Control("c", "e", lambda: _observation(module, True), lambda: _observation(module, True)),
        [_observation(module, True)],
        [_observation(module, True)],
    )
    assert status is module.Status.FALSE_PASS, (status, reason)
    assert "cannot block" in reason


def test_differing_digests_across_repeats_are_non_deterministic() -> None:
    module = _calibration()
    calibration = module.Calibration(out=Path("/tmp/unused-calibration"))
    status, reason = calibration._classify(
        module.Control("c", "e", lambda: _observation(module, True), lambda: _observation(module, False)),
        [_observation(module, True, {"n": 1}), _observation(module, True, {"n": 2})],
        [_observation(module, False), _observation(module, False)],
    )
    assert status is module.Status.NON_DETERMINISTIC, (status, reason)


def test_a_refused_positive_is_a_gap() -> None:
    """A known-good input rejected is a false positive, and never VERIFIED."""

    module = _calibration()
    calibration = module.Calibration(out=Path("/tmp/unused-calibration"))
    status, _ = calibration._classify(
        module.Control("c", "e", lambda: _observation(module, False), lambda: _observation(module, False)),
        [_observation(module, False)],
        [_observation(module, False)],
    )
    assert status is module.Status.GAP


def test_the_happy_path_still_reaches_verified() -> None:
    """A classifier that never returns VERIFIED would pass every test above."""

    module = _calibration()
    calibration = module.Calibration(out=Path("/tmp/unused-calibration"))
    status, _ = calibration._classify(
        module.Control("c", "e", lambda: _observation(module, True), lambda: _observation(module, False)),
        [_observation(module, True)],
        [_observation(module, False)],
    )
    assert status is module.Status.VERIFIED


# --- the receipt checker must be able to fail -------------------------------


@pytest.mark.parametrize(
    "case, expected",
    [
        ({"control": "c", "status": "VERIFIED", "repeats": 3}, "no negative control"),
        (
            {"control": "c", "status": "VERIFIED", "repeats": 3,
             "negative": {"runs": 1, "ok": [True]}},
            "ACCEPTED",
        ),
        ({"control": "c", "status": "FALSE-PASS", "repeats": 3,
          "negative": {"runs": 3, "ok": [True, True, True]}}, "recall window"),
        (
            {"control": "c", "status": "VERIFIED", "repeats": 1,
             "negative": {"runs": 1, "ok": [False]}},
            "fewer than 3",
        ),
    ],
    ids=["missing-negative", "negative-accepted", "no-recall-window", "too-few-repeats"],
)
def test_the_receipt_checker_catches_each_overclaim(case: dict, expected: str) -> None:
    problems = _violations({"repeats": case.get("repeats"), "cases": [case]})
    assert any(expected in problem for problem in problems), (expected, problems)


def test_a_well_formed_receipt_passes_the_checker() -> None:
    """Otherwise the checker above could be rejecting everything."""

    assert not _violations(
        {
            "repeats": 3,
            "cases": [
                {
                    "control": "c",
                    "status": "VERIFIED",
                    "repeats": 3,
                    "negative": {"runs": 3, "ok": [False, False, False]},
                }
            ],
        }
    )
