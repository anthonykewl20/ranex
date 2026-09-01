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
