"""Integration coverage for the strict-local host workflow's process seams."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from ranex.cli import host_confinement, host_workflow
from ranex.foundation.canonical import canonical_json_bytes


def _passing_checks() -> list[host_workflow.CheckResult]:
    """The host-only checks needed by an in-process workflow double."""
    return [
        host_workflow.CheckResult(name, True, "present", "repair the host")
        for name in (
            "pid1-systemd",
            "systemd-run-present",
            "user-session-bus",
            "user-manager-alive",
            "not-root",
            "build-closure",
            "already-delegated",
        )
    ]


def _step(name: str, argv: list[str], exit_code: int = 0) -> host_workflow.StepResult:
    return host_workflow.StepResult(name, argv, exit_code, None, None, "", "")


def _report(result_dir: Path) -> dict[str, object]:
    path = result_dir / "host-run-report.json"
    contents = path.read_bytes()
    report = json.loads(contents)
    assert contents == canonical_json_bytes(report) + b"\n"
    assert report["schema"] == "ranex-host-strict-local-run-v1"
    return report


def _assert_logs(result_dir: Path, report: dict[str, object]) -> None:
    """The #58 retained-stream shape, including its independently checked hashes."""
    logs = report["logs"]
    assert isinstance(logs, dict)
    assert set(logs) == {"stdout", "stderr"}
    directory = result_dir / "logs"
    assert {path.name for path in directory.iterdir()} == {
        "stdout.log",
        "stderr.log",
        "manifest.json",
    }
    for entry in logs.values():
        assert isinstance(entry, dict)
        stream = directory / str(entry["file"])
        payload = stream.read_bytes()
        assert entry["bytes"] == len(payload)
        assert entry["sha256"] == "sha256:" + hashlib.sha256(payload).hexdigest()
        assert stream.stat().st_mode & 0o777 == 0o444
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest_path.read_bytes() == canonical_json_bytes(manifest) + b"\n"
    manifest_streams = manifest["streams"]
    assert isinstance(manifest_streams, dict)
    for name, entry in logs.items():
        assert isinstance(entry, dict)
        manifest_entry = manifest_streams[name]
        assert isinstance(manifest_entry, dict)
        assert {
            key: manifest_entry[key] for key in ("file", "bytes", "sha256")
        } == entry


def _wire_in_place(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RANEX_STRICT_LOCAL_IN_SCOPE", "1")
    monkeypatch.setattr(host_workflow, "preflight_checks", lambda **_kwargs: _passing_checks())
    monkeypatch.setattr(
        host_workflow,
        "delegated_controllers",
        lambda: (Path("/sys/fs/cgroup"), "/user.slice/user-1000.slice/user@1000.service/app.slice", host_confinement.REQUIRED_CONTROLLERS),
    )
    monkeypatch.setattr(host_workflow, "_launcher_matches_manifest", lambda *_args: True)


def test_sentinel_reexec_preserves_the_strict_local_invocation(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The scope child receives the complete operator invocation, not just a version."""
    monkeypatch.delenv("RANEX_STRICT_LOCAL_IN_SCOPE", raising=False)
    monkeypatch.setattr(host_workflow, "preflight_checks", lambda **_kwargs: _passing_checks())
    monkeypatch.setattr(
        host_workflow,
        "delegated_controllers",
        lambda: (Path("/sys/fs/cgroup"), "/", frozenset()),
    )
    monkeypatch.setattr(host_workflow, "_launcher_matches_manifest", lambda *_args: True)
    monkeypatch.setattr(host_workflow, "_run_step", _step)
    entered: list[list[str]] = []
    monkeypatch.setattr(host_workflow, "enter_delegated_scope", lambda argv: entered.append(list(argv)))

    assert host_workflow.run_workflow(
        "v1",
        runtime_input_path=None,
        toolchain_root=None,
        runtime_closure_root=None,
        command=("/bin/true",),
        result_dir=str(tmp_path / "result"),
        skip_build=True,
    ) == 0

    assert entered == [
        [
            "ranex",
            "host",
            "strict-local",
            "--version",
            "v1",
            "--result-dir",
            str(tmp_path / "result"),
            "--skip-build",
            "--",
            "/bin/true",
        ]
    ]


def test_scope_entry_sets_sentinel_and_systemd_delegation_properties(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The actual exec seam carries the recursion guard into the child process."""
    invoked: list[tuple[str, list[str], dict[str, str]]] = []

    def execve(path: str, argv: list[str], environment: dict[str, str]) -> None:
        invoked.append((path, argv, environment))

    monkeypatch.setattr(host_workflow.os, "execve", execve)
    with pytest.raises(AssertionError, match=r"os\.execve returned"):
        host_workflow.enter_delegated_scope(["ranex", "host", "strict-local", "--version", "v1"])

    path, argv, environment = invoked.pop()
    assert path == "/usr/bin/systemd-run"
    assert argv[:4] == ["/usr/bin/systemd-run", "--user", "--scope", "--quiet"]
    assert "--property=Delegate=yes" in argv
    assert "--setenv=RANEX_STRICT_LOCAL_IN_SCOPE=1" in argv
    assert environment["RANEX_STRICT_LOCAL_IN_SCOPE"] == "1"


def test_in_place_final_exit_code_and_retained_report_propagate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An already delegated child neither re-execs nor swallows command failure."""
    _wire_in_place(monkeypatch)
    entered: list[object] = []
    monkeypatch.setattr(host_workflow, "enter_delegated_scope", lambda argv: entered.append(argv))

    def run_step(name: str, argv: list[str]) -> host_workflow.StepResult:
        return _step(name, argv, 7 if name == "run" else 0)

    monkeypatch.setattr(host_workflow, "_run_step", run_step)
    result_dir = tmp_path / "result"
    assert host_workflow.run_workflow(
        "v1", runtime_input_path=None, toolchain_root=None, runtime_closure_root=None,
        command=("/bin/false",), result_dir=str(result_dir), skip_build=True,
    ) == 7
    assert entered == []
    report = _report(result_dir)
    assert report["outcome"] == "refused"
    assert report["command"] == {"argv": ["/bin/false"], "exit_code": 7}
    _assert_logs(result_dir, report)


def test_refusal_json_is_humanized_and_retained(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A kernel refusal remains named in both operator output and the report."""
    _wire_in_place(monkeypatch)
    code = host_confinement.E_C18_HOST_DRIFT
    detail = "cgroup delegation drifted since qualification"

    def run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if argv[0] == "ranex":
            return subprocess.CompletedProcess(argv, 1, json.dumps({"refusal": code, "detail": detail}), "")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(host_workflow.subprocess, "run", run)
    result_dir = tmp_path / "refused"
    assert host_workflow.run_workflow(
        "v1", runtime_input_path=None, toolchain_root=None, runtime_closure_root=None,
        command=("/bin/false",), result_dir=str(result_dir), skip_build=True,
    ) == 1
    captured = capsys.readouterr()
    assert f"ERROR  {code}: {detail}" in captured.err
    assert f"HINT  {host_workflow.corrective_for(code)}" in captured.err
    report = _report(result_dir)
    assert report["outcome"] == "refused"
    steps = report["steps"]
    assert isinstance(steps, list)
    assert steps[-1]["refusal_code"] == code
    assert steps[-1]["refusal_detail"] == detail
    _assert_logs(result_dir, report)


def test_prerequisite_failure_retains_check_report_and_logs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing session bus fails closed but remains operator-auditable."""
    failed = host_workflow.CheckResult(
        "user-session-bus", False, "requires XDG runtime bus or DBUS session bus", "restore the session bus"
    )
    monkeypatch.delenv("RANEX_STRICT_LOCAL_IN_SCOPE", raising=False)
    monkeypatch.setattr(host_workflow, "preflight_checks", lambda **_kwargs: [failed])
    result_dir = tmp_path / "prereq"
    assert host_workflow.run_workflow(
        "v1", runtime_input_path=None, toolchain_root=None, runtime_closure_root=None,
        command=("/bin/true",), result_dir=str(result_dir), skip_build=True,
    ) == 1
    assert "ERROR  user-session-bus:" in capsys.readouterr().err
    report = _report(result_dir)
    assert report["outcome"] == "prereq-failed"
    assert report["checks"] == [
        {"name": failed.name, "ok": False, "detail": failed.detail, "corrective_action": failed.corrective_action}
    ]
    _assert_logs(result_dir, report)


def test_launcher_identity_reports_manifest_mismatch_and_exec_drift_remedy(tmp_path: Path) -> None:
    """Identity is a comparison, and executable-object drift has a named remedy."""
    artifact = tmp_path / "launcher"
    manifest = tmp_path / "manifest.json"
    artifact.write_bytes(b"actual launcher")
    manifest.write_text(json.dumps({"artifact": {"sha256": "0" * 64}}), encoding="utf-8")

    identity = host_workflow.launcher_identity(artifact, manifest)
    assert identity["artifact_sha256"] == "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert identity["manifest_sha256"] == "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert identity["matches"] is False
    assert "executable" in host_workflow.corrective_for(host_confinement.E_EXEC).lower()


def test_v3_toolchain_pairing_refuses_before_scope_entry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Selector misuse is usage failure, never a reason to create a scope."""
    entered: list[object] = []
    monkeypatch.setattr(host_workflow, "enter_delegated_scope", lambda argv: entered.append(argv))
    result_dir = tmp_path / "bad-pair"
    assert host_workflow.run_workflow(
        "v3", runtime_input_path="tests/e2e/fixtures/slice072-input",
        toolchain_root="governance/qualification/worker", runtime_closure_root=None,
        command=("/bin/true",), result_dir=str(result_dir), skip_build=True,
    ) == 2
    assert "ENTERED" not in capsys.readouterr().out
    assert entered == []
    report = _report(result_dir)
    assert report["outcome"] == "prereq-failed"
    _assert_logs(result_dir, report)


def test_preflight_checks_record_success_and_host_probe_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every host prerequisite has both its normal and readable failure arm."""
    original_read_text = host_workflow.Path.read_text
    monkeypatch.setattr(host_workflow.Path, "is_file", lambda _path: True)
    monkeypatch.setattr(host_workflow.os, "access", lambda *_args: True)
    monkeypatch.setattr(host_workflow.os, "geteuid", lambda: 1000)
    monkeypatch.setenv("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1000/bus")
    monkeypatch.setattr(
        host_workflow.subprocess,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "degraded\n", ""),
    )
    monkeypatch.setattr(
        host_workflow,
        "delegated_controllers",
        lambda: (Path("/sys/fs/cgroup"), "/", frozenset()),
    )

    def systemd_pid1(path: Path, *args: object, **kwargs: object) -> str:
        if path == Path("/proc/1/comm"):
            return "systemd\n"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(host_workflow.Path, "read_text", systemd_pid1)
    checks = host_workflow.preflight_checks(build_needed=True)
    assert [check.name for check in checks] == list(host_workflow._PREFLIGHT_NAMES)
    assert checks[0].ok and checks[3].ok
    assert checks[-1].ok is False
    assert checks[3].detail == "desktop-unit failures do not block delegation"

    monkeypatch.setattr(
        host_workflow.Path,
        "read_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("permission denied")),
    )
    monkeypatch.setattr(
        host_workflow.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("no user manager")),
    )
    monkeypatch.setattr(
        host_workflow,
        "delegated_controllers",
        lambda: (_ for _ in ()).throw(ValueError("no unified cgroup")),
    )
    failed = host_workflow.preflight_checks(build_needed=False)
    assert failed[0].detail.startswith("cannot read /proc/1/comm:")
    assert failed[3].detail.startswith("cannot query user manager:")
    assert failed[-1].detail.startswith("cannot inspect current cgroup delegation:")


def test_host_probe_and_identity_helpers_fail_closed_on_unreadable_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Malformed or unreadable local probe inputs never become admitted facts."""
    monkeypatch.setattr(
        host_workflow.Path,
        "read_text",
        lambda *_args, **_kwargs: "0::not-absolute\n",
    )
    with pytest.raises(ValueError, match="unified cgroup"):
        host_workflow.delegated_controllers()

    artifact = tmp_path / "launcher"
    manifest = tmp_path / "manifest.json"
    artifact.write_bytes(b"launcher")
    manifest.write_text("{not json", encoding="utf-8")
    identity = host_workflow.launcher_identity(artifact, manifest)
    assert identity["matches"] is False
    assert host_workflow._launcher_matches_manifest(artifact, manifest) is False
    assert host_workflow.launcher_identity(tmp_path / "missing", tmp_path / "also-missing")["matches"] is False

    monkeypatch.setattr(host_workflow, "BUILD_ARTIFACT", str(tmp_path / "missing-artifact"))
    monkeypatch.setattr(host_workflow, "INSTALLED_ARTIFACT", str(tmp_path / "missing-installed"))
    assert host_workflow._managed_launcher_is_unchanged() is False
    monkeypatch.setattr(
        host_workflow.Path,
        "read_text",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("unreadable")),
    )
    monkeypatch.setattr(
        host_workflow.subprocess,
        "run",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("no manager")),
    )
    facts = host_workflow._host_facts()
    assert facts["boot_id"] is None
    assert facts["is_system_running"] is None


def test_refusal_fallback_and_unreadable_qualification_are_retained(tmp_path: Path) -> None:
    """Text refusals and an optional unreadable qualification remain auditable."""
    assert host_workflow._refusal_from_streams("not json", "ERROR E-C18-GATE: gate closed") == (
        "E-C18-GATE",
        "gate closed",
    )
    result_dir = tmp_path / "result"
    result_dir.mkdir()
    report = {"qualification": {"path": str(tmp_path / "missing-qualification")}, "_stdout": "", "_stderr": ""}
    assert host_workflow.write_run_report(result_dir, report) == result_dir / "host-run-report.json"
    assert not (result_dir / "qualification.json").exists()


def test_v2_selectors_forward_to_scope_and_run_with_launcher_build(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A v2 workflow forwards both selector authorities through every child."""
    monkeypatch.delenv("RANEX_STRICT_LOCAL_IN_SCOPE", raising=False)
    monkeypatch.setattr(host_workflow, "preflight_checks", lambda **_kwargs: _passing_checks())
    monkeypatch.setattr(host_workflow, "delegated_controllers", lambda: (Path("/sys/fs/cgroup"), "/", frozenset()))
    monkeypatch.setattr(host_workflow, "_launcher_matches_manifest", lambda *_args: True)
    monkeypatch.setattr(host_workflow, "_managed_launcher_is_unchanged", lambda: False)
    entered: list[list[str]] = []
    steps: list[host_workflow.StepResult] = []
    monkeypatch.setattr(host_workflow, "enter_delegated_scope", lambda argv: entered.append(list(argv)))

    def run_step(name: str, argv: list[str]) -> host_workflow.StepResult:
        step = _step(name, argv)
        steps.append(step)
        return step

    monkeypatch.setattr(host_workflow, "_run_step", run_step)
    assert host_workflow.run_workflow(
        "v2",
        runtime_input_path="inputs/task",
        toolchain_root="toolchain",
        runtime_closure_root=None,
        command=("/bin/true",),
        result_dir=str(tmp_path / "result"),
        skip_build=False,
        claim="claim",
        producer="producer",
    ) == 0
    assert [step.name for step in steps] == ["launcher-build", "launcher-install", "qualify", "run"]
    for argv in (entered[0], steps[-1].argv):
        assert "--runtime-input-path" in argv
        assert "inputs/task" in argv
        assert "--toolchain-root" in argv
        assert "toolchain" in argv
    assert "--runtime-closure-root" not in entered[0]

    assert host_workflow.run_workflow(
        "v3",
        runtime_input_path="inputs/runtime",
        toolchain_root=None,
        runtime_closure_root="runtime-closure",
        command=("/bin/true",),
        result_dir=str(tmp_path / "v3-result"),
        skip_build=False,
        claim="claim",
        producer="producer",
    ) == 0
    for argv in (entered[-1], steps[-1].argv):
        assert "--runtime-closure-root" in argv
        assert "runtime-closure" in argv


def test_workflow_reports_phase_refusal_and_controller_probe_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A phase refusal and unavailable outer cgroup probe both retain reports."""
    _wire_in_place(monkeypatch)
    monkeypatch.setattr(host_workflow, "_managed_launcher_is_unchanged", lambda: False)
    code, detail = host_confinement.E_C18_GATE, "qualification required"
    monkeypatch.setattr(
        host_workflow,
        "_run_step",
        lambda name, argv: host_workflow.StepResult(name, argv, 1, code, detail, "", ""),
    )
    assert host_workflow.run_workflow(
        "v1", runtime_input_path=None, toolchain_root=None, runtime_closure_root=None,
        command=("/bin/true",), result_dir=str(tmp_path / "refused"), skip_build=True,
    ) == 1
    assert f"ERROR  {code}: {detail}" in capsys.readouterr().err

    monkeypatch.setattr(
        host_workflow,
        "delegated_controllers",
        lambda: (_ for _ in ()).throw(ValueError("cgroup unavailable")),
    )
    monkeypatch.setattr(host_workflow, "_run_step", _step)
    assert host_workflow.run_workflow(
        "v1", runtime_input_path=None, toolchain_root=None, runtime_closure_root=None,
        command=("/bin/true",), result_dir=str(tmp_path / "fallback"), skip_build=True,
    ) == 0
    assert _report(tmp_path / "fallback")["scope"]["cgroup_relative_path"] == "/"


def test_v2_pairing_and_public_main_dispatch_cover_public_arms(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The public workflow rejects incomplete v2 selectors and prints identity."""
    assert host_workflow.run_workflow(
        "v2", runtime_input_path=None, toolchain_root=None, runtime_closure_root=None,
        command=("/bin/true",), result_dir=str(tmp_path / "bad-v2"), skip_build=True,
    ) == 2
    assert "v2 requires" in capsys.readouterr().err
    artifact = tmp_path / "launcher"
    manifest = tmp_path / "manifest.json"
    artifact.write_bytes(b"launcher")
    manifest.write_text(json.dumps({"artifact": {"sha256": hashlib.sha256(b"launcher").hexdigest()}}), encoding="utf-8")
    from ranex.cli.main import build_parser

    args = build_parser().parse_args(
        ["host", "launcher-identity", "--artifact", str(artifact), "--manifest", str(manifest)]
    )
    assert args.func(args) == 0
    assert json.loads(capsys.readouterr().out)["matches"] is True

    dispatched: list[tuple[object, dict[str, object]]] = []
    monkeypatch.setattr(
        host_workflow,
        "run_workflow",
        lambda version, **kwargs: dispatched.append((version, kwargs)) or 0,
    )
    strict_local = build_parser().parse_args(
        [
            "host",
            "strict-local",
            "--version",
            "v3",
            "--claim",
            "claim",
            "--producer",
            "producer",
            "--runtime-input-path",
            "inputs/runtime",
            "--runtime-closure-root",
            "runtime-closure",
            "--",
            "/bin/true",
        ]
    )
    assert strict_local.func(strict_local) == 0
    assert dispatched == [
        (
            "v3",
            {
                "runtime_input_path": "inputs/runtime",
                "toolchain_root": None,
                "runtime_closure_root": "runtime-closure",
                "command": ["/bin/true"],
                "result_dir": ".local/ranex/host-results",
                "skip_build": False,
                "claim": "claim",
                "producer": "producer",
                "repository": None,
                "evidence": None,
                "producers": None,
                "gate": None,
                "gate_catalog": None,
                "suite_manifest": None,
                "store": None,
            },
        )
    ]
