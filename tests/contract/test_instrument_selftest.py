"""No gauge is trusted until it has caught a known-bad. Issue #113.

`tools/dogfood/selftest.py` exists because a green result with no negative
control beside it is fluff, and — worse — a gauge that silently stopped
catching still prints green. These tests hold the harness to the properties
the issue states: a committed good/bad reference pair per instrument, an exit
contract a caller can branch on, a receipt that stays byte-identical across
identical repeats, and drivers whose measurement cannot start before the
self-test has passed.

The observers here are stubs on purpose: the suite pins the classification
contract quickly and deterministically, while the real-instrument proof runs
in the operator audit (tools/dogfood/audits/2026-09-24-selftest/) — unit
tests with stubs are never the completion evidence, and these do not claim to
be.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOGFOOD = REPO_ROOT / "tools" / "dogfood"
sys.path.insert(0, str(DOGFOOD))

from selftest import (  # noqa: E402
    INSTRUMENTS,
    _reference,
    assemble_receipt,
    exit_code,
)


def _module(name: str) -> types.ModuleType:
    """Load a dogfood module by path: tools/ is operator tooling, not a package."""

    spec = importlib.util.spec_from_file_location(name, DOGFOOD / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _stub_observer(good_ok: bool, bad_ok: bool, *, flaky: bool = False):
    """An observer whose verdicts are fixed and whose facts are stable."""

    calls = {"n": 0}

    def observe(side: str):
        calls["n"] += 1
        facts = {"exit": 0, "n": calls["n"] // 2 if flaky else 1}
        return _module("calibration").Observation(
            ok=good_ok if side == "good" else bad_ok, facts=facts,
        )

    return observe


def _proved(good_ok: bool = True, bad_ok: bool = False, **kwargs) -> dict:
    selftest = _module("selftest")
    return selftest._prove(
        "marker-scanner", 3, Path("/tmp/selftest-classify-unused"),
        _stub_observer(good_ok, bad_ok, **kwargs),
    )


# --- the committed reference pairs -------------------------------------------


@pytest.mark.parametrize("instrument", sorted(INSTRUMENTS))
@pytest.mark.parametrize("side", ["good", "bad"])
def test_every_instrument_ships_both_references(instrument: str, side: str) -> None:
    reference = _reference(instrument, side)
    assert reference.is_file(), f"missing committed reference: {reference}"
    if reference.suffix == ".json":
        loaded = json.loads(reference.read_bytes())
        assert isinstance(loaded, dict) and loaded, "a JSON reference must be an object"


@pytest.mark.parametrize("instrument", sorted(INSTRUMENTS))
def test_good_and_bad_references_differ(instrument: str) -> None:
    assert (_reference(instrument, "good").read_bytes()
            != _reference(instrument, "bad").read_bytes())


def test_the_reference_inventory_names_the_wired_drivers() -> None:
    for instrument, driver in INSTRUMENTS.items():
        assert (REPO_ROOT / driver).is_file(), f"{instrument} names a missing driver"


# --- the classification vocabulary -------------------------------------------


def test_a_gauge_that_passes_good_and_catches_bad_is_verified() -> None:
    row = _proved(good_ok=True, bad_ok=False)
    assert row["status"] == "VERIFIED"
    assert row["good"]["outcome"] == "passed"
    assert row["bad"]["outcome"] == "caught"
    assert exit_code([row]) == 0


def test_an_accepted_bad_reference_is_reported_false_pass() -> None:
    """The alarm this file exists for: a self-test that cannot fail."""

    row = _proved(good_ok=True, bad_ok=True)
    assert row["status"] == "FALSE-PASS", "an accepted known-bad must never read VERIFIED"
    assert row["bad"]["outcome"] == "accepted"
    assert exit_code([row]) == 1


def test_a_refused_good_reference_is_a_gap() -> None:
    row = _proved(good_ok=False, bad_ok=False)
    assert row["status"] == "GAP"
    assert row["good"]["outcome"] == "refused"
    assert exit_code([row]) == 1


def test_flaky_observations_are_non_deterministic() -> None:
    row = _proved(good_ok=True, bad_ok=False, flaky=True)
    assert row["status"] == "NON-DETERMINISTIC"
    assert exit_code([row]) == 1


def test_reference_digests_land_in_the_receipt() -> None:
    row = _proved()
    for side in ("good", "bad"):
        digest = row[side]["digest"]
        assert digest.startswith("sha256:") and len(digest) == 71
        assert row[side]["reference"].startswith("tools/dogfood/selftest/references/")


# --- the receipt and the exit contract ----------------------------------------


_TIMING_KEYS = {"duration_s", "wall_ms", "wall_s", "started", "elapsed", "time"}


def _timing_keys(node: object, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key in _TIMING_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_timing_keys(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_timing_keys(value, f"{path}[{index}]"))
    return found


def test_the_receipt_is_timing_free_so_repeats_can_be_byte_identical() -> None:
    row = _proved()
    first = assemble_receipt([row], repeats=3, blunt=None, argv=["selftest", "--out", "x"])
    second = assemble_receipt([row], repeats=3, blunt=None, argv=["selftest", "--out", "x"])
    assert not _timing_keys(first), _timing_keys(first)
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_incomplete_execution_is_never_a_silent_green(tmp_path: Path, monkeypatch) -> None:
    selftest = _module("selftest")

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("the harness could not run")

    monkeypatch.setattr(selftest, "run", _boom)
    monkeypatch.setattr(sys, "argv", ["selftest.py", "--out", str(tmp_path / "out")])
    assert selftest.main() == 2
    receipt = json.loads((tmp_path / "out" / "selftest.json").read_text(encoding="utf-8"))
    assert receipt["overall"] == "UNVERIFIED"
    assert "RuntimeError" in receipt["error"]


def test_an_unknown_blunt_target_refuses_before_any_execution() -> None:
    selftest = _module("selftest")
    with pytest.raises(KeyError):
        selftest.run(Path("/tmp/never-written-selftest"), blunt="does-not-exist")


# --- the wiring: measurement cannot precede a passing self-test ---------------


def test_calibration_refuses_to_skip_the_selftest(tmp_path: Path) -> None:
    calibration = _module("calibration")

    class Args:
        out = tmp_path / "refused"
        repeats = 3
        skip_selftest = True
        blunt = None

    assert calibration.preflight(Args()) == 1
    leftovers = [path for path in tmp_path.rglob("*") if path.is_file()]
    assert not leftovers, f"the skip refusal must write nothing; found {leftovers}"


def test_a_failed_preflight_code_stops_the_run(tmp_path: Path, monkeypatch) -> None:
    class Args:
        out = tmp_path / "blunted"
        repeats = 3
        skip_selftest = False
        blunt = "marker-scanner"

    fake = types.ModuleType("selftest")
    fake.run = lambda *a, **k: ({"instruments": [
        {"instrument": "marker-scanner", "status": "FALSE-PASS", "reason": "blunted"}]}, 1)
    monkeypatch.setitem(sys.modules, "selftest", fake)
    calibration = _module("calibration")
    assert calibration.preflight(Args()) == 1


_DRIVER_WIRING = {
    "calibration": "subject.build()",
    "release_audit": "audit.execute()",
    "receiver_audit": "execute(out)",
    # the arms section of main(), not the build_subject definition above it
    "markers_probe": 'arm("1-well-formed"',
}


@pytest.mark.parametrize("driver,measurement", sorted(_DRIVER_WIRING.items()))
def test_every_driver_self_tests_before_it_measures(driver: str, measurement: str) -> None:
    source = (DOGFOOD / f"{driver}.py").read_text(encoding="utf-8")
    assert 'add_argument("--selftest"' in source or "--skip-selftest" in source, (
        f"{driver} must expose the #113 self-test surface"
    )
    preflight = source.index("selftest.run(")
    assert preflight < source.index(measurement), (
        f"{driver}: the self-test must run before {measurement} — before any "
        "measurement and before any spend"
    )
