"""Frozen real-process integration contract for the SLICE-018 session service."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.cli import host_confinement

REPOSITORY = Path(__file__).resolve().parents[2]
RUNTIME_PROFILE = REPOSITORY / "governance/confinement/strict-local-v1.json"
CONTROLLER = (sys.executable, "-m", "ranex.cli.host_confinement")


@pytest.mark.parametrize(
    "layer",
    [
        pytest.param("user", id="user-namespace"),
        pytest.param("mount", id="mount-namespace"),
        pytest.param("pid", id="pid-namespace"),
        pytest.param("ipc", id="ipc-namespace"),
        pytest.param("network", id="network-namespace"),
        pytest.param("cgroup", id="cgroup-namespace"),
        pytest.param("landlock", id="landlock"),
        pytest.param("seccomp", id="seccomp"),
        pytest.param("no_new_privs", id="no-new-privs"),
    ],
)
def test_gate7_runtime_profile_makes_every_layer_mandatory(layer: str) -> None:
    profile = json.loads(RUNTIME_PROFILE.read_bytes())
    assert profile["mandatory_layers"][layer] is True
    assert "fallback" not in profile


def test_gate2_runtime_profile_mounts_only_output_and_scratch_writable() -> None:
    profile = json.loads(RUNTIME_PROFILE.read_bytes())
    assert profile["mounts"] == {
        "subject": "read-only",
        "toolchain": "read-only",
        "output": "writable-bounded",
        "scratch": "writable-bounded",
        "proc": "fresh",
        "dev": "minimal",
    }


def _sample_result() -> dict[str, object]:
    return {
        "schema": "ranex-confinement-result-v1",
        "profile_digests": {"runtime": "0" * 64, "host": "1" * 64, "launcher": "2" * 64},
        "namespace_readbacks": {
            name: "namespace-id" for name in ("user", "mount", "pid", "ipc", "network", "cgroup")
        },
        "cgroup_readbacks": {
            "limits": {"pids.max": "16"},
            "events": {"populated": 0},
            "usage": {"cpu_usage_usec": 1},
        },
        "command": {
            "argv_digest": "3" * 64,
            "exit_code": 0,
            "no_new_privs": True,
            "landlock": True,
            "seccomp": True,
        },
        "teardown": {"cgroup_kill": True, "populated": 0, "cgroup_removed": True},
        "outputs": {"files": [], "bytes": 0, "inodes": 0},
    }


def test_gate8_emitted_result_is_closed_canonical_and_unsigned() -> None:
    emit = getattr(host_confinement, "confinement_result_bytes", None)
    assert callable(emit), "ConfinementResult emitter is absent"
    value = _sample_result()
    raw = emit(value)
    assert (
        raw == json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )
    decoded = json.loads(raw)
    assert set(decoded) == {
        "schema",
        "profile_digests",
        "namespace_readbacks",
        "cgroup_readbacks",
        "command",
        "teardown",
        "outputs",
    }
    assert decoded["schema"] == "ranex-confinement-result-v1"
    assert not {"signature", "signing_identity", "evidence"} & set(decoded)


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param("unknown", id="unknown-field"),
        pytest.param("missing", id="missing-field"),
        pytest.param("live", id="not-drained"),
    ],
)
def test_gate8_malformed_or_live_result_is_refused(mutation: str) -> None:
    emit = getattr(host_confinement, "confinement_result_bytes", None)
    assert callable(emit), "ConfinementResult emitter is absent"
    value = _sample_result()
    if mutation == "unknown":
        value["signature"] = "forged"
    elif mutation == "missing":
        del value["teardown"]
    else:
        value["teardown"] = {"cgroup_kill": True, "populated": 1, "cgroup_removed": False}
    with pytest.raises(Exception) as caught:
        emit(value)
    assert getattr(caught.value, "code", "").startswith("E-C18-")


def _real_host_ready() -> tuple[bool, str]:
    required = [Path("/sys/fs/cgroup/cgroup.controllers"), Path("/usr/bin/bwrap")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, f"real host prerequisites absent: {missing}"
    if not os.access("/sys/fs/cgroup", os.W_OK):
        return False, "no delegated writable cgroup-v2 root"
    return True, ""


def _materialize_case(tmp_path: Path, argv: list[str] | None = None) -> tuple[Path, Path]:
    root = Path(
        shutil.copytree(
            REPOSITORY,
            tmp_path / "repository",
            symlinks=True,
            ignore=shutil.ignore_patterns(
                ".git", ".venv", ".uv-cache", "__pycache__", ".pytest_cache"
            ),
        )
    )
    case = root / ".local/ranex/slice018-contract"
    paths = {name: case / name for name in ("subject", "toolchain", "output", "scratch")}
    for directory in paths.values():
        directory.mkdir(parents=True)
    descriptor = case / "descriptor.json"
    descriptor.write_text(
        json.dumps(
            {
                "argv": argv or ["/bin/true"],
                "environment": {"LC_ALL": "C", "TZ": "UTC"},
                "limits": {
                    "cpu_usage_usec": 1_000_000,
                    "memory_bytes": 134_217_728,
                    "output_bytes": 65_536,
                    "output_depth": 8,
                    "output_inodes": 32,
                    "pids": 16,
                    "wall_time_ms": 5_000,
                },
                "output": str(paths["output"].relative_to(root)),
                "schema": "ranex-confinement-command-v1",
                "scratch": str(paths["scratch"].relative_to(root)),
                "subject": str(paths["subject"].relative_to(root)),
                "toolchain": str(paths["toolchain"].relative_to(root)),
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    return root, descriptor


def _invoke_session(root: Path, descriptor: Path, result: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            *CONTROLLER,
            "session",
            "--profile",
            "governance/confinement/strict-local-v1.json",
            "--host-profile",
            "governance/confinement/strict-local-host-v1.json",
            "--artifact",
            ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
            "--manifest",
            "governance/confinement/native-launcher-build-v1.json",
            "--qualification",
            ".local/ranex/qualification/strict-local-v1.json",
            "--descriptor",
            str(descriptor),
            "--result",
            str(result),
        ],
        cwd=root,
        env={**os.environ, "PYTHONPATH": "src"},
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def test_gate4_output_scratch_aliasing_is_refused_before_launch(tmp_path: Path) -> None:
    root, descriptor = _materialize_case(tmp_path)
    value = json.loads(descriptor.read_text())
    value["scratch"] = value["output"]
    descriptor.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
    marker = root / ".local/ranex/slice018-contract/ran"
    value["argv"] = ["/bin/sh", "-c", f"touch {marker}"]
    descriptor.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
    result = descriptor.parent / "result.json"
    completed = _invoke_session(root, descriptor, result)
    assert completed.returncode != 0
    assert json.loads(completed.stdout)["refusal"] == "E-C18-PATH-ALIAS"
    assert not marker.exists() and not result.exists()


def test_gate4_host_state_drift_since_qualification_is_refused_before_launch(
    tmp_path: Path,
) -> None:
    root, descriptor = _materialize_case(tmp_path)
    qualification = root / ".local/ranex/qualification/strict-local-v1.json"
    qualification.parent.mkdir(parents=True, exist_ok=True)
    qualification.write_text(
        json.dumps(
            {
                "schema": "ranex-strict-local-qualification-v1",
                "host_state": {
                    "userns_sysctl": "drifted",
                    "lsm": "drifted",
                    "cgroup_delegation": "drifted",
                },
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    marker = descriptor.parent / "ran"
    value = json.loads(descriptor.read_text())
    value["argv"] = ["/bin/sh", "-c", f"touch {marker}"]
    descriptor.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
    result = descriptor.parent / "result.json"
    completed = _invoke_session(root, descriptor, result)
    assert completed.returncode != 0
    assert json.loads(completed.stdout)["refusal"] == "E-C18-HOST-DRIFT"
    assert not marker.exists() and not result.exists()


def test_gate1_real_process_session_observes_namespaces_landlock_and_seccomp(
    tmp_path: Path,
) -> None:
    ready, reason = _real_host_ready()
    if not ready:
        pytest.skip(f"SLICE-018 host qualification unavailable: {reason}")
    root, descriptor = _materialize_case(tmp_path)
    result = descriptor.parent / "result.json"
    completed = _invoke_session(root, descriptor, result)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    raw = result.read_bytes()
    value = json.loads(raw)
    assert (
        raw == json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    )
    assert value["schema"] == "ranex-confinement-result-v1"
    assert all(value["namespace_readbacks"].values())
    assert value["command"]["no_new_privs"] is True
    assert value["command"]["landlock"] is True
    assert value["command"]["seccomp"] is True
    assert value["teardown"] == {"cgroup_kill": True, "populated": 0, "cgroup_removed": True}
