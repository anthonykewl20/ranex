"""Frozen binding contract: ``run`` signs only a completed child session result."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.cli import main as cli
from ranex.foundation.signing import SIGNED_FIELDS, generate_keypair, verify_evidence

PROJECT = Path(__file__).resolve().parents[2]
CONTROLLER = (sys.executable, "-m", "ranex.cli.host_confinement")


def _result(exit_code: int = 0) -> dict[str, object]:
    return {
        "schema": "ranex-confinement-result-v1",
        "profile_digests": {"runtime": "4" * 64, "host": "5" * 64, "launcher": "6" * 64},
        "namespace_readbacks": {
            name: "namespace-id" for name in ("user", "mount", "pid", "ipc", "network", "cgroup")
        },
        "cgroup_readbacks": {
            "limits": {"cpu.max": "max 100000", "memory.max": "1024", "pids.max": "16"},
            "events": {"memory": {"max": 0}, "pids": {"max": 0}, "populated": 0},
            "usage": {"cpu_usage_usec": 1},
        },
        "command": {
            "argv_digest": "7" * 64,
            "exit_code": exit_code,
            "no_new_privs": True,
            "landlock": True,
            "seccomp": True,
        },
        "teardown": {"cgroup_kill": True, "populated": 0, "cgroup_removed": True},
        "outputs": {"files": [], "bytes": 0, "inodes": 0},
    }


def _real_host_ready() -> tuple[bool, str]:
    required = [Path("/sys/fs/cgroup/cgroup.controllers"), Path("/usr/bin/bwrap")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, f"real host prerequisites absent: {missing}"
    if not os.access("/sys/fs/cgroup", os.W_OK):
        return False, "no delegated writable cgroup-v2 root"
    return True, ""


@pytest.fixture()
def repo(tmp_path: Path) -> tuple[Path, Path, str]:
    root = tmp_path / "governed"
    root.mkdir()
    private, public = generate_keypair()
    key = tmp_path / "worker.key"
    key.write_text(private + "\n", encoding="utf-8")
    key.chmod(0o600)
    (root / "file.txt").write_text("subject\n", encoding="utf-8")
    (root / "producers.yaml").write_text(f"producers:\n  worker: {public}\n", encoding="utf-8")
    (root / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n    required_claims:\n      - claim_id: tests-executed\n"
        "        command: [\"/bin/true\"]\n",
        encoding="utf-8",
    )
    for relative in (
        "governance/confinement/strict-local-v1.json",
        "governance/confinement/strict-local-host-v1.json",
        "governance/confinement/native-launcher-build-v1.json",
        "native/ranex-worker-launcher/launcher.c",
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / relative, destination)
    (root / ".gitignore").write_text("evidence.json\n.local/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for name, value in (("user.email", "test@example.invalid"), ("user.name", "test")):
        subprocess.run(["git", "-C", str(root), "config", name, value], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "initial"], check=True)
    return root, key, public


def _arguments() -> argparse.Namespace:
    """The public flag's parsed shape, passed directly to isolate child protocol cases."""

    return argparse.Namespace(
        claim="tests-executed", producer="worker", repository=".", evidence="evidence.json",
        producers="producers.yaml", gate="landing", gate_catalog="gates.yaml",
        suite_manifest="suite_manifest.json", store=cli.default_store(),
        confinement="strict-local", command=["--", "/bin/true"],
    )


def _run_bound(
    repo: Path,
    key: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    controller: subprocess.CompletedProcess[str],
) -> tuple[int, str]:
    """Let ordinary subprocesses work; only the required child is substituted."""

    real_popen = cli.subprocess.Popen

    class ControllerPopen:
        """Controller double usable through today's `run` and tomorrow's direct Popen."""

        pid = 7123

        def __init__(self, arguments: object, *args: object, **kwargs: object) -> None:
            self.args = arguments
            self.arguments = arguments
            self.returncode = controller.returncode
            if controller.returncode == 0 and controller.stdout.startswith("WRITE-RESULT"):
                result_path = Path(arguments[arguments.index("--result") + 1])  # type: ignore[index]
                exit_code = int(controller.stdout.rsplit("-", 1)[-1])
                result_path.parent.mkdir(parents=True, exist_ok=True)
                result_path.write_bytes(json.dumps(_result(exit_code), sort_keys=True, separators=(",", ":")).encode())
            elif controller.returncode == 0 and controller.stdout == "WRITE-INCOMPLETE":
                result_path = Path(arguments[arguments.index("--result") + 1])  # type: ignore[index]
                value = _result()
                del value["teardown"]
                result_path.parent.mkdir(parents=True, exist_ok=True)
                result_path.write_text(json.dumps(value), encoding="utf-8")

        def communicate(
            self, input: object | None = None, timeout: float | None = None
        ) -> tuple[str, str]:
            return controller.stdout, controller.stderr

        def __enter__(self) -> ControllerPopen:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def kill(self) -> None:
            return None

        def poll(self) -> int:
            return self.returncode

        def wait(self) -> int:
            return self.returncode

    def popen(arguments: object, *args: object, **kwargs: object) -> ControllerPopen | subprocess.Popen[bytes]:
        if tuple(arguments[:3]) == CONTROLLER:  # type: ignore[index]
            return ControllerPopen(arguments, *args, **kwargs)
        return real_popen(arguments, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.chdir(repo)
    monkeypatch.setattr(cli, "governed_repository_root", lambda: repo)
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(key))
    monkeypatch.setattr(cli.subprocess, "Popen", popen)
    code = cli.cmd_run(_arguments())
    return code, capsys.readouterr().err


def test_strict_local_flag_refuses_an_unqualified_host_before_evidence(
    repo: tuple[Path, Path, str],
) -> None:
    root, key, _public = repo
    completed = subprocess.run(
        [
            sys.executable, "-m", "ranex.cli.main", "run", "--claim", "tests-executed",
            "--producer", "worker", "--repository", ".", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--confinement", "strict-local", "--", "/bin/true",
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": str(PROJECT / "src"), "RANEX_SIGNING_KEY": str(key)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == cli.EXIT_USAGE
    assert "E-C18-HOST-DRIFT" in completed.stderr + completed.stdout
    assert not (root / "evidence.json").exists()


def test_nonzero_controller_refusal_is_propagated_without_evidence(
    repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    root, key, _public = repo
    refusal = json.dumps({"detail": "qualification changed", "refusal": "E-C18-HOST-DRIFT"})
    code, diagnostic = _run_bound(
        root, key, monkeypatch, capsys,
        subprocess.CompletedProcess(CONTROLLER, 1, refusal, ""),
    )
    assert code == cli.EXIT_USAGE
    assert "E-C18-HOST-DRIFT" in diagnostic and "qualification changed" in diagnostic
    assert not (root / "evidence.json").exists()


def test_zero_controller_exit_without_a_result_refuses_without_evidence(
    repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    root, key, _public = repo
    code, diagnostic = _run_bound(
        root, key, monkeypatch, capsys, subprocess.CompletedProcess(CONTROLLER, 0, "", ""),
    )
    assert code == cli.EXIT_USAGE
    assert "result" in diagnostic.lower()
    assert not (root / "evidence.json").exists()


def test_incomplete_result_refuses_e_c18_result_without_evidence(
    repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    root, key, _public = repo
    code, diagnostic = _run_bound(
        root, key, monkeypatch, capsys,
        subprocess.CompletedProcess(CONTROLLER, 0, "WRITE-INCOMPLETE", ""),
    )
    assert code == cli.EXIT_USAGE
    assert "E-C18-RESULT" in diagnostic
    assert not (root / "evidence.json").exists()


def test_valid_child_result_is_signed_and_supplies_the_evidence_exit_code(
    repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    root, key, public = repo
    code, diagnostic = _run_bound(
        root, key, monkeypatch, capsys,
        subprocess.CompletedProcess(CONTROLLER, 0, "WRITE-RESULT-7", ""),
    )
    assert code == 7, diagnostic
    (record,) = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    assert "confinement_result_digest" in record
    result_bytes = json.dumps(_result(7), sort_keys=True, separators=(",", ":")).encode()
    assert record["confinement_result_digest"] == hashlib.sha256(result_bytes).hexdigest()
    assert record["confinement_profile_digest"] == "4" * 64
    assert record["exit_code"] == _result(7)["command"]["exit_code"]
    content = {name: value for name, value in record.items() if name != "signature"}
    assert {"confinement_result_digest", "confinement_profile_digest"} <= set(SIGNED_FIELDS)
    assert verify_evidence(content, record["signature"], public)


def test_real_strict_local_session_is_host_gated_and_binds_its_result(
    repo: tuple[Path, Path, str],
) -> None:
    ready, reason = _real_host_ready()
    if not ready:
        pytest.skip(f"SLICE-046 real session unavailable: {reason}")
    root, key, public = repo
    environment = {**os.environ, "PYTHONPATH": str(PROJECT / "src")}
    controller = [*CONTROLLER]
    for arguments in (
        ["launcher-build", "--manifest", "governance/confinement/native-launcher-build-v1.json",
         "--source", "native/ranex-worker-launcher/launcher.c", "--output",
         ".local/ranex/build/strict-local-v1/ranex-worker-launcher"],
        ["launcher-install", "--manifest", "governance/confinement/native-launcher-build-v1.json",
         "--artifact", ".local/ranex/build/strict-local-v1/ranex-worker-launcher", "--destination",
         ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"],
        ["qualify", "--profile", "governance/confinement/strict-local-host-v1.json", "--artifact",
         ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher", "--manifest",
         "governance/confinement/native-launcher-build-v1.json", "--report",
         ".local/ranex/qualification/strict-local-v1.json"],
    ):
        completed = subprocess.run(
            [*controller, *arguments], cwd=root, env=environment, capture_output=True,
            text=True, check=False, timeout=180,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
    completed = subprocess.run(
        [
            sys.executable, "-m", "ranex.cli.main", "run", "--claim", "tests-executed",
            "--producer", "worker", "--repository", ".", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--confinement", "strict-local", "--", "/bin/true",
        ],
        cwd=root,
        env={**environment, "RANEX_SIGNING_KEY": str(key)},
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    (record,) = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    assert record["confinement_result_digest"]
    assert record["confinement_profile_digest"]
    content = {name: value for name, value in record.items() if name != "signature"}
    assert verify_evidence(content, record["signature"], public)


def test_tampering_a_signed_confinement_result_digest_breaks_verification(
    repo: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    root, key, public = repo
    code, diagnostic = _run_bound(
        root, key, monkeypatch, capsys,
        subprocess.CompletedProcess(CONTROLLER, 0, "WRITE-RESULT-0", ""),
    )
    assert code == 0, diagnostic
    (record,) = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    assert "confinement_result_digest" in record
    altered = {name: value for name, value in record.items() if name != "signature"}
    altered["confinement_result_digest"] = "0" + altered["confinement_result_digest"][1:]
    assert not verify_evidence(altered, record["signature"], public)
