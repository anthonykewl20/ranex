"""The bare arm is declared, measured, and provably uncontaminated. #114.

`tools/dogfood/oss_bench/two_arm.py` used to build the bare arm's
environment as `dict(os.environ)` plus a venv-on-PATH prepend — defensible,
but nothing proved it. An inherited PYTHONPATH, an inherited RANEX_*
variable, or a vendored kernel on PATH would make the bare arm quietly
governed and the two-arm comparison would report a difference that is not
there. These tests pin the #114 contract: the bare environment comes from an
explicit allowlist (never ambient inheritance), a probe measures the
environment the child ACTUALLY receives and fails the run on contamination,
and each named contamination channel has a negative control that is caught.

The real-instrument proof (real VulcanBench task, both arms, 3x repeats)
lives in the operator audit tools/dogfood/audits/2026-09-24-bare-purity/;
unit tests are never the completion evidence and these do not claim to be.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOGFOOD = REPO_ROOT / "tools" / "dogfood"


def _two_arm() -> types.ModuleType:
    """Load two_arm by path: tools/ is operator tooling, not a package."""

    spec = importlib.util.spec_from_file_location(
        "two_arm_under_test", DOGFOOD / "oss_bench" / "two_arm.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fake_task(tmp_path: Path) -> Path:
    """A minimal VulcanBench-shaped task: enough for the bare arm's bookkeeping."""

    task = tmp_path / "task"
    (task / "repo").mkdir(parents=True)
    (task / "repo" / "README.md").write_text("task\n")
    (task / "tests").mkdir()
    (task / "gold_patch.diff").write_text("")
    (task / "metadata.json").write_text(json.dumps({
        "id": "unit-fake-task",
        "tests": {"fail_to_pass": [
            {"name": "t1", "cmd": "python -c pass"},
        ]},
    }))
    return task


# --- the allowlist ------------------------------------------------------------


def test_bare_environment_drops_everything_off_the_allowlist(
        monkeypatch: pytest.MonkeyPatch) -> None:
    two_arm = _two_arm()
    for name, value in {
        "RANEX_SIGNING_KEY": "/tmp/leaked.key",
        "PYTHONPATH": "/somewhere/ranex/src",
        "VIRTUAL_ENV": "/somewhere/venv",
        "PYENV_ROOT": "/somewhere/pyenv",
        "PYTHONWARNINGS": "ignore",
        "CLAUDE_CODE_OAUTH_TOKEN": "ambient-secret",
    }.items():
        monkeypatch.setenv(name, value)
    env = two_arm.bare_environment()
    for forbidden in ("RANEX_SIGNING_KEY", "PYTHONPATH", "VIRTUAL_ENV",
                      "PYENV_ROOT", "PYTHONWARNINGS", "CLAUDE_CODE_OAUTH_TOKEN"):
        assert forbidden not in env
    assert not [name for name in env if name.startswith("RANEX_")]


def test_bare_environment_path_is_declared_not_inherited(
        monkeypatch: pytest.MonkeyPatch) -> None:
    two_arm = _two_arm()
    monkeypatch.setenv("PATH", "/inherited/junk:/bin")
    env = two_arm.bare_environment()
    assert env["PATH"] == f"{two_arm.RANEX_PY.parent}:{two_arm.BARE_SYSTEM_PATH}"
    assert "/inherited/junk" not in env["PATH"]


def test_bare_environment_is_deterministic(
        monkeypatch: pytest.MonkeyPatch) -> None:
    two_arm = _two_arm()
    monkeypatch.setenv("HOME", "/home/stable")
    first = two_arm.bare_environment()
    second = two_arm.bare_environment()
    assert first == second


def test_bare_environment_passthrough_carries_only_listed_names(
        monkeypatch: pytest.MonkeyPatch) -> None:
    two_arm = _two_arm()
    for name in two_arm.BARE_ENV_PASSTHROUGH:
        monkeypatch.setenv(name, f"value-of-{name}")
    env = two_arm.bare_environment()
    assert set(env) == {*two_arm.BARE_ENV_PASSTHROUGH, "PATH"}


# --- the detector -------------------------------------------------------------


def test_contamination_findings_is_empty_for_a_clean_bare_environment() -> None:
    two_arm = _two_arm()
    assert two_arm.contamination_findings(two_arm.bare_environment()) == []


def test_contamination_findings_catches_each_named_channel() -> None:
    two_arm = _two_arm()
    kernel_root = str(two_arm.RANEX_REPO / "src")
    ranex_var = dict(two_arm.bare_environment(), RANEX_SIGNING_KEY="/tmp/x.key")
    pythonpath = dict(two_arm.bare_environment(), PYTHONPATH=kernel_root)
    on_path = two_arm.bare_environment()
    on_path["PATH"] = f"{kernel_root}:{on_path['PATH']}"
    assert two_arm.contamination_findings(ranex_var) == [
        "RANEX_* variable present: RANEX_SIGNING_KEY"]
    assert two_arm.contamination_findings(pythonpath) == [
        f"PYTHONPATH names a ranex source root: {kernel_root}"]
    assert two_arm.contamination_findings(on_path) == [
        f"PATH names a ranex source root: {kernel_root}"]


def test_in_child_canary_measures_the_environment_actually_used(
        tmp_path: Path) -> None:
    two_arm = _two_arm()
    env = two_arm.bare_environment()
    child = two_arm.probe_bare_environment(env, cwd=tmp_path,
                                           python=sys.executable)
    assert child == env  # the child sees exactly what was constructed
    assert two_arm.contamination_findings(child) == []


def test_in_child_canary_catches_contamination_in_the_child(
        tmp_path: Path) -> None:
    two_arm = _two_arm()
    kernel_root = str(two_arm.RANEX_REPO / "src")
    env = dict(two_arm.bare_environment(), PYTHONPATH=kernel_root,
               RANEX_SIGNING_KEY="/tmp/x.key")
    child = two_arm.probe_bare_environment(env, cwd=tmp_path,
                                           python=sys.executable)
    findings = two_arm.contamination_findings(child)
    assert f"PYTHONPATH names a ranex source root: {kernel_root}" in findings
    assert "RANEX_* variable present: RANEX_SIGNING_KEY" in findings


def test_assert_bare_environment_fails_loudly_on_contamination(
        tmp_path: Path) -> None:
    two_arm = _two_arm()
    kernel_root = str(two_arm.RANEX_REPO / "src")
    env = dict(two_arm.bare_environment(), PYTHONPATH=kernel_root)
    with pytest.raises(two_arm.BareArmContaminated) as caught:
        two_arm.assert_bare_environment(env, cwd=tmp_path, python=sys.executable)
    assert f"PYTHONPATH names a ranex source root: {kernel_root}" \
        in caught.value.findings


# --- the wiring ---------------------------------------------------------------


def test_run_bare_arm_records_the_probe_and_passes_clean(
        tmp_path: Path) -> None:
    two_arm = _two_arm()
    task = _fake_task(tmp_path)
    entries = [{"name": "t1", "cmd": "python -c pass"}]
    ground = two_arm.run_bare_arm(task, entries, env=two_arm.bare_environment(),
                                  python=sys.executable)
    environment = ground["environment"]
    assert environment["contamination_findings"] == []
    assert environment["probes"] >= 1
    assert environment["child_env"] == two_arm.bare_environment()
    assert len(environment["child_env_sha256"]) == 64
    canonical = json.dumps(environment["child_env"], sort_keys=True,
                           separators=(",", ":"))
    assert environment["child_env_sha256"] \
        == hashlib.sha256(canonical.encode()).hexdigest()


def test_run_bare_arm_refuses_to_run_contaminated(tmp_path: Path) -> None:
    two_arm = _two_arm()
    task = _fake_task(tmp_path)
    entries = [{"name": "t1", "cmd": "python -c pass"}]
    env = dict(two_arm.bare_environment(),
               PYTHONPATH=str(two_arm.RANEX_REPO / "src"),
               RANEX_SIGNING_KEY="/tmp/x.key")
    with pytest.raises(two_arm.BareArmContaminated):
        two_arm.run_bare_arm(task, entries, env=env, python=sys.executable)


def test_mode_tasks_contaminated_flavors_exit_loudly_without_results(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    two_arm = _two_arm()
    task = _fake_task(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    for flavor in two_arm.CONTAMINATIONS:
        assert two_arm.mode_tasks(task, out, contaminate=flavor) == 3
        assert not (out / "bare_ground_truth.json").exists()
        stderr = capsys.readouterr().err
        assert "BARE-ARM-CONTAMINATED" in stderr


def test_governed_environment_stays_deliberately_governed(
        tmp_path: Path) -> None:
    two_arm = _two_arm()
    repo = tmp_path / "repo"
    key = tmp_path / "bench.key"
    env = two_arm._governed_environment(repo, str(key))
    assert env["PYTHONPATH"] == str(repo / "src")
    assert env["RANEX_SIGNING_KEY"] == str(key)
