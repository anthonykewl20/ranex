"""Issue #64's public host-operator surface, frozen red before implementation.

The future ``ranex host`` group is an operator-facing wrapper around the
existing, deliberately machine-oriented ``host_confinement`` module.  These
tests pin the wrapper's command spelling, human diagnostics, and retained
report boundary; they do not re-test the confinement kernel.
"""

from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

BUILD_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
BUILD_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_ARTIFACT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_ARTIFACT = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
QUALIFICATION_REPORT = ".local/ranex/qualification/strict-local-v1.json"
REPORT_SCHEMA = "ranex-host-strict-local-run-v1"
REPORT_KEYS = {
    "schema",
    "started_at",
    "finished_at",
    "outcome",
    "host",
    "scope",
    "checks",
    "steps",
    "launcher",
    "qualification",
    "command",
    "result_binding",
    "logs",
}

_CANONICAL_INVOCATIONS = (
    (
        "launcher-build",
        [
            "launcher-build",
            "--manifest",
            BUILD_MANIFEST,
            "--source",
            BUILD_SOURCE,
            "--output",
            BUILD_ARTIFACT,
        ],
    ),
    (
        "launcher-install",
        [
            "launcher-install",
            "--manifest",
            BUILD_MANIFEST,
            "--artifact",
            BUILD_ARTIFACT,
            "--destination",
            INSTALLED_ARTIFACT,
        ],
    ),
    (
        "qualify",
        [
            "qualify",
            "--profile",
            HOST_PROFILE,
            "--artifact",
            INSTALLED_ARTIFACT,
            "--manifest",
            BUILD_MANIFEST,
            "--report",
            QUALIFICATION_REPORT,
        ],
    ),
)


def _workflow() -> ModuleType:
    """Import lazily: the absent module is this contract's intended red."""

    return importlib.import_module("ranex.cli.host_workflow")


def _host_args(*argv: str):
    """Parse one host invocation only after requiring its owning module."""

    _workflow()
    from ranex.cli.main import build_parser

    return build_parser().parse_args(["host", *argv])


def _read_report(result_dir: Path) -> dict[str, object]:
    return json.loads((result_dir / "host-run-report.json").read_text(encoding="utf-8"))


def _assert_report_shape(report: dict[str, object]) -> None:
    assert set(report) == REPORT_KEYS
    assert report["schema"] == REPORT_SCHEMA
    assert report["outcome"] in {"confined", "refused", "prereq-failed"}
    logs = report["logs"]
    assert isinstance(logs, dict)
    assert set(logs) == {"stdout", "stderr"}
    for stream in logs.values():
        assert isinstance(stream, dict)
        assert set(stream) == {"file", "bytes", "sha256"}


def test_host_group_help_discovers_all_operator_verbs(capsys: pytest.CaptureFixture[str]) -> None:
    """``host`` is a visible top-level group with a closed six-verb surface."""

    _workflow()
    from ranex.cli.main import build_parser

    parser = build_parser()
    with pytest.raises(SystemExit) as host_help:
        parser.parse_args(["host", "--help"])
    assert host_help.value.code == 0
    host_output = capsys.readouterr().out
    for verb in (
        "launcher-build",
        "launcher-install",
        "host-probe",
        "qualify",
        "launcher-identity",
        "strict-local",
    ):
        assert verb in host_output

    with pytest.raises(SystemExit) as top_level_help:
        parser.parse_args(["--help"])
    assert top_level_help.value.code == 0
    assert "host" in capsys.readouterr().out


@pytest.mark.parametrize(("verb", "expected"), _CANONICAL_INVOCATIONS)
def test_host_wrappers_forward_the_frozen_module_argv(
    monkeypatch: pytest.MonkeyPatch,
    verb: str,
    expected: list[str],
) -> None:
    """The friendly surface cannot reorder or reinterpret the kernel argv."""

    workflow = _workflow()
    forwarded: list[tuple[str, list[str]]] = []

    def spy(name: str, argv: list[str]) -> object:
        forwarded.append((name, argv))
        return workflow.StepResult(name, argv, 0, None, None, "", "")

    monkeypatch.setattr(workflow, "_run_step", spy)
    args = _host_args(verb)
    assert args.func(args) == 0
    assert forwarded == [
        (verb, ["python", "-m", "ranex.cli.host_confinement", *expected])
    ]


def test_corrective_action_catalog_covers_exactly_confinement_refusals() -> None:
    """Every C17/C18 refusal has one durable, operator-readable correction."""

    workflow = _workflow()
    confinement = importlib.import_module("ranex.cli.host_confinement")
    known_codes = {
        value
        for name, value in vars(confinement).items()
        if re.fullmatch(r"E_C1[78].*", name) and isinstance(value, str)
    }
    corrective_actions = workflow.CORRECTIVE_ACTIONS
    preflight_checks = workflow.PREFLIGHT_CHECKS

    assert set(corrective_actions) == known_codes
    assert preflight_checks and not isinstance(preflight_checks, str)
    assert set(preflight_checks) <= known_codes
    for code in known_codes:
        corrective = corrective_actions[code]
        assert isinstance(corrective, str) and len(corrective) >= 20
        assert workflow.corrective_for(code) == corrective


def test_host_refusal_is_humanized_with_a_corrective_hint(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Kernel refusal JSON never leaks through the operator-facing stderr."""

    workflow = _workflow()
    confinement = importlib.import_module("ranex.cli.host_confinement")
    code = confinement.E_FACT
    detail = "delegated cgroup controller is unavailable"

    def refused(name: str, argv: list[str]) -> object:
        return workflow.StepResult(
            name,
            argv,
            1,
            code,
            detail,
            json.dumps({"detail": detail, "refusal": code}, separators=(",", ":")),
            "",
        )

    monkeypatch.setattr(workflow, "_run_step", refused)
    args = _host_args("qualify", "--result-dir", str(tmp_path / "refused"))
    assert args.func(args) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"ERROR  {code}: {detail}" in captured.err
    assert f"HINT  {workflow.corrective_for(code)}" in captured.err


def test_host_success_prints_the_operation_lifecycle(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A successful operation says what completed and names its artifact."""

    workflow = _workflow()

    def succeeded(name: str, argv: list[str]) -> object:
        return workflow.StepResult(name, argv, 0, None, None, "", "")

    monkeypatch.setattr(workflow, "_run_step", succeeded)

    args = _host_args("launcher-build", "--result-dir", str(tmp_path / "built"))
    assert args.func(args) == 0
    output = capsys.readouterr().out
    assert output.startswith("BUILT")
    assert BUILD_ARTIFACT in output


@pytest.mark.parametrize(
    "argv",
    (
        (
            "strict-local",
            "--runtime-input-path",
            "governance/qualification/inputs/slice036/a-before-b/attempt-0",
        ),
        (
            "strict-local",
            "--runtime-input-path",
            "tests/e2e/fixtures/slice072-input",
            "--runtime-closure-root",
            "tests/e2e/fixtures/slice072-runtime",
            "--toolchain-root",
            "governance/qualification/worker",
        ),
    ),
)
def test_host_strict_local_rejects_invalid_v2_v3_selector_pairing_before_scope_entry(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, argv: tuple[str, ...]
) -> None:
    """Invalid source-selector pairs fail before a delegated scope can exist."""

    workflow = _workflow()
    entered: list[tuple[object, ...]] = []

    def enter_scope(*args: object, **kwargs: object) -> None:
        entered.append((*args, *kwargs.values()))

    monkeypatch.setattr(workflow, "enter_delegated_scope", enter_scope)
    from ranex.cli.main import EXIT_USAGE, build_parser

    with pytest.raises(SystemExit) as rejected:
        build_parser().parse_args(["host", *argv])
    assert rejected.value.code == EXIT_USAGE
    captured = capsys.readouterr()
    assert "ENTERED" not in captured.out
    assert entered == []


def test_host_refusal_writes_its_report_without_touching_the_suite_artifact_home(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A host-wrapper refusal owns its report, never a suite-home byproduct."""

    workflow = _workflow()
    result_dir = tmp_path / "result"
    suite_home = tmp_path / "suite-artifact-home"
    suite_home.mkdir()
    monkeypatch.setenv("COVERAGE_FILE", str(suite_home / ".coverage"))

    def refused(name: str, argv: list[str]) -> object:
        return workflow.StepResult(
            name,
            argv,
            1,
            "E-C17-HOST-FACT-MISSING",
            "host prerequisites absent",
            '{"detail":"host prerequisites absent","refusal":"E-C17-HOST-FACT-MISSING"}',
            "",
        )

    monkeypatch.setattr(workflow, "_run_step", refused)
    before = sorted(path.relative_to(suite_home) for path in suite_home.rglob("*"))
    args = _host_args("host-probe", "--result-dir", str(result_dir))
    assert args.func(args) == 1
    after = sorted(path.relative_to(suite_home) for path in suite_home.rglob("*"))
    assert (result_dir / "host-run-report.json").is_file()
    assert after == before

    e2e_dir = Path(__file__).resolve().parents[1] / "e2e"
    sys.path.insert(0, str(e2e_dir))
    import _prereqs  # noqa: PLC0415

    assert _prereqs.probe_artifact_home_writable(suite_home) is None


def test_host_run_reports_keep_the_fixed_retention_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Success and refusal reports retain the same closed #58-shaped envelope."""

    workflow = _workflow()
    from ranex.cli import main as cli_main

    success_dir = tmp_path / "success"

    def succeeded(name: str, argv: list[str]) -> object:
        return workflow.StepResult(name, argv, 0, None, None, "", "")

    monkeypatch.setattr(workflow, "_run_step", succeeded)
    assert cli_main.main(["host", "launcher-build", "--result-dir", str(success_dir)]) == 0
    success = _read_report(success_dir)
    _assert_report_shape(success)
    assert success["outcome"] == "confined"

    refusal_dir = tmp_path / "refusal"

    def refused(name: str, argv: list[str]) -> object:
        return workflow.StepResult(
            name,
            argv,
            1,
            "E-C17-HOST-FACT-MISSING",
            "host prerequisites absent",
            '{"detail":"host prerequisites absent","refusal":"E-C17-HOST-FACT-MISSING"}',
            "",
        )

    monkeypatch.setattr(workflow, "_run_step", refused)
    assert cli_main.main(["host", "launcher-build", "--result-dir", str(refusal_dir)]) == 1
    refusal = _read_report(refusal_dir)
    _assert_report_shape(refusal)
    assert refusal["outcome"] == "refused"
