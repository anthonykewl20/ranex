"""Frozen strict-local controller authority and timeout contract for SLICE-047."""

from __future__ import annotations

import argparse
import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from ranex.cli import main as cli
from ranex.foundation.signing import generate_keypair

PROJECT = Path(__file__).resolve().parents[2]
CONTROLLER = (sys.executable, "-m", "ranex.cli.host_confinement")


def _result() -> dict[str, object]:
    return {
        "schema": "ranex-confinement-result-v1",
        "profile_digests": {"runtime": "4" * 64, "host": "5" * 64, "launcher": "6" * 64},
        "namespace_readbacks": {name: "namespace-id" for name in ("user", "mount", "pid", "ipc", "network", "cgroup")},
        "cgroup_readbacks": {"limits": {"pids.max": "16"}, "events": {"populated": 0}, "usage": {"cpu_usage_usec": 1}},
        "command": {"argv_digest": "7" * 64, "exit_code": 0, "no_new_privs": True, "landlock": True, "seccomp": True},
        "teardown": {"cgroup_kill": True, "populated": 0, "cgroup_removed": True},
        "outputs": {"files": [], "bytes": 0, "inodes": 0},
    }


@pytest.fixture()
def repository(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "governed"
    root.mkdir()
    private, public = generate_keypair()
    key = tmp_path / "worker.key"
    key.write_text(private + "\n", encoding="utf-8")
    key.chmod(0o600)
    (root / "file.txt").write_text("subject\n", encoding="utf-8")
    (root / "producers.yaml").write_text(f"producers:\n  worker: {public}\n", encoding="utf-8")
    (root / "gates.yaml").write_text("gates:\n  - gate_id: landing\n    rule_id: TESTS_EXECUTED\n    blocking: true\n    required_claims:\n      - claim_id: tests-executed\n        command: [\"/bin/true\"]\n", encoding="utf-8")
    for relative in ("governance/confinement/strict-local-v1.json", "governance/confinement/strict-local-host-v1.json", "governance/confinement/native-launcher-build-v1.json", "native/ranex-worker-launcher/launcher.c"):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / relative, destination)
    (root / ".gitignore").write_text("evidence.json\n.local/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "initial"], check=True)
    return root, key


class _ControllerPopen:
    pid = 7123

    def __init__(self, argv: list[str], calls: dict[str, Any], mode: str) -> None:
        self.args = argv
        self.argv = argv
        self.calls = calls
        self.mode = mode
        self.returncode = 0

    def communicate(
        self, input: object | None = None, timeout: float | None = None
    ) -> tuple[str, str]:
        if self.mode == "timeout" and timeout is not None:
            raise subprocess.TimeoutExpired(self.argv, timeout)
        return "", ""

    def __enter__(self) -> _ControllerPopen:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def kill(self) -> None:
        return None

    def poll(self) -> int:
        return self.returncode

    def wait(self) -> int:
        return self.returncode


def _arguments() -> argparse.Namespace:
    return argparse.Namespace(claim="tests-executed", producer="worker", repository=".", evidence="evidence.json", producers="producers.yaml", gate="landing", gate_catalog="gates.yaml", suite_manifest="suite_manifest.json", store=cli.default_store(), confinement="strict-local", command=["--", "/bin/true"])


def _run_bound(root: Path, key: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], mode: str) -> tuple[int, str, dict[str, Any]]:
    calls: dict[str, Any] = {}
    real_popen = cli.subprocess.Popen

    def popen(argv: list[str], *args: Any, **kwargs: Any) -> _ControllerPopen:
        if tuple(argv[:3]) != CONTROLLER:
            return real_popen(argv, *args, **kwargs)  # type: ignore[return-value]
        calls["argv"] = argv
        calls["env"] = kwargs.get("env")
        if mode == "success":
            result_path = Path(argv[argv.index("--result") + 1])
            result_path.write_text(json.dumps(_result(), sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return _ControllerPopen(argv, calls, mode)

    monkeypatch.chdir(root)
    monkeypatch.setattr(cli, "governed_repository_root", lambda: root)
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(key))
    monkeypatch.setattr(cli.subprocess, "Popen", popen)
    code = cli.cmd_run(_arguments())
    return code, capsys.readouterr().err, calls


def _reload_observability(monkeypatch: pytest.MonkeyPatch, env: dict[str, str]):
    """Re-import ranex.observability under a patched environment.

    The emitter reads each trace variable exactly once at import, so the
    tracing-on arm needs a fresh module (the same pattern as the frozen
    SLICE-054 tests); main.py's controller seam resolves the module at call
    time, so the reloaded snapshot governs the spawned environment.
    """

    for name in [
        name
        for name in sys.modules
        if name == "ranex.observability" or name.startswith("ranex.observability.")
    ]:
        del sys.modules[name]
    for variable in ("RANEX_TRACE", "RANEX_TRACE_EVENT", "RANEX_TRACE_PARENT_SID"):
        monkeypatch.delenv(variable, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import ranex.observability

    return ranex.observability


def test_controller_gets_only_the_declared_environment(repository: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, key = repository
    # Hermetic off state first: earlier tests in the same process may leave a
    # traced emitter module behind (module state survives their monkeypatch),
    # and the seam reads whatever module is current at spawn time.
    _reload_observability(monkeypatch, {})
    _code, _diagnostic, calls = _run_bound(root, key, monkeypatch, capsys, "success")
    environment = calls.get("env", {})
    assert set(environment) == {"PATH", "PYTHONPATH", "LC_ALL", "TZ"}
    assert "RANEX_SIGNING_KEY" not in environment

    # ADR-031's tracing-on seam (sanctioned amendment, SLICE-054): over the
    # frozen four-variable base the controller gains exactly the enabled
    # trace target variable(s) plus RANEX_TRACE_PARENT_SID — nothing else.
    trace_target = root.parent / "controller-trace.jsonl"
    module = _reload_observability(monkeypatch, {"RANEX_TRACE": str(trace_target)})
    assert module.TRACING_ENABLED is True
    _code, _diagnostic, calls = _run_bound(root, key, monkeypatch, capsys, "success")
    environment = calls.get("env", {})
    assert set(environment) == {
        "PATH", "PYTHONPATH", "LC_ALL", "TZ", "RANEX_TRACE", "RANEX_TRACE_PARENT_SID",
    }
    assert environment["RANEX_TRACE"] == str(trace_target)
    assert environment["RANEX_TRACE_PARENT_SID"] == module.SESSION_ID
    assert "RANEX_SIGNING_KEY" not in environment
    _reload_observability(monkeypatch, {})  # restore the off state for later tests


def test_controller_timeout_kills_group_and_refuses_without_evidence(repository: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, key = repository
    killed: list[tuple[int, int]] = []
    monkeypatch.setattr(cli.os, "getpgid", lambda pid: pid + 1)
    monkeypatch.setattr(cli.os, "killpg", lambda pgid, signal: killed.append((pgid, signal)))
    code, diagnostic, _calls = _run_bound(root, key, monkeypatch, capsys, "timeout")
    assert code == cli.EXIT_USAGE and "E-C46-CONTROLLER" in diagnostic
    assert killed == [(7124, cli.signal.SIGKILL)]
    assert not (root / "evidence.json").exists()


def test_timeout_kill_race_still_refuses_without_evidence(repository: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    root, key = repository
    monkeypatch.setattr(cli.os, "getpgid", lambda pid: pid + 1)
    monkeypatch.setattr(cli.os, "killpg", lambda pgid, signal: (_ for _ in ()).throw(ProcessLookupError()))
    code, diagnostic, _calls = _run_bound(root, key, monkeypatch, capsys, "timeout")
    assert code == cli.EXIT_USAGE and "E-C46-CONTROLLER" in diagnostic
    assert not (root / "evidence.json").exists()


def test_only_host_confinement_module_may_name_host_confinement() -> None:
    source_root = PROJECT / "src"
    offenders = []
    for path in source_root.rglob("*.py"):
        if path.name == "host_confinement.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(
            (
                isinstance(node, ast.ImportFrom)
                and node.module == "ranex.cli.host_confinement"
            )
            or (
                isinstance(node, ast.Import)
                and any(
                    alias.name == "ranex.cli.host_confinement"
                    or alias.name.startswith("ranex.cli.host_confinement.")
                    for alias in node.names
                )
            )
            or (
                isinstance(node, ast.ImportFrom)
                and node.module == "ranex.cli"
                and any(alias.name == "host_confinement" for alias in node.names)
            )
            for node in ast.walk(tree)
        ):
            offenders.append(path.relative_to(source_root).as_posix())
    assert not offenders
