"""Frozen real-process integration contract for the SLICE-018 session service."""

from __future__ import annotations

import inspect
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


def test_gate1_session_entrypoint_and_result_type_are_real_service_api() -> None:
    parser = host_confinement._parser()
    help_text = parser.format_help()
    assert "session" in help_text
    result_type = getattr(host_confinement, "ConfinementResult", None)
    assert result_type is not None
    assert tuple(result_type.__dataclass_fields__) == (
        "schema",
        "profile_digests",
        "namespace_readbacks",
        "cgroup_readbacks",
        "command",
        "teardown",
        "outputs",
    )


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
    mandatory = profile["mandatory_layers"]
    assert mandatory[layer] is True
    assert "fallback" not in profile


def test_gate2_runtime_profile_mounts_only_output_and_scratch_writable() -> None:
    profile = json.loads(RUNTIME_PROFILE.read_bytes())
    mounts = profile["mounts"]
    assert mounts == {
        "subject": "read-only",
        "toolchain": "read-only",
        "output": "writable-bounded",
        "scratch": "writable-bounded",
        "proc": "fresh",
        "dev": "minimal",
    }


def test_gate8_result_schema_is_closed_canonical_and_unsigned() -> None:
    serializer = getattr(host_confinement, "confinement_result_value", None)
    assert serializer is not None
    source = inspect.getsource(serializer)
    assert "ranex-confinement-result-v1" in source
    assert "canonical_json" in source
    assert all(word not in source.lower() for word in ("signature", "signing", "evidence"))


def _real_host_ready() -> tuple[bool, str]:
    required = [Path("/sys/fs/cgroup/cgroup.controllers"), Path("/usr/bin/bwrap")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, f"real host prerequisites absent: {missing}"
    if not os.access("/sys/fs/cgroup", os.W_OK):
        return False, "no delegated writable cgroup-v2 root"
    return True, ""


def test_gate1_real_process_session_observes_namespaces_landlock_and_seccomp(
    tmp_path: Path,
) -> None:
    ready, reason = _real_host_ready()
    assert "session" in host_confinement._parser().format_help()
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
    descriptor = case / "descriptor.json"
    result = case / "result.json"
    subject = case / "subject"
    toolchain = case / "toolchain"
    output = case / "output"
    scratch = case / "scratch"
    for directory in (subject, toolchain, output, scratch):
        directory.mkdir()
    descriptor.write_text(
        json.dumps(
            {
                "argv": ["/bin/true"],
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
                "output": str(output.relative_to(root)),
                "schema": "ranex-confinement-command-v1",
                "scratch": str(scratch.relative_to(root)),
                "subject": str(subject.relative_to(root)),
                "toolchain": str(toolchain.relative_to(root)),
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    completed = subprocess.run(
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
        check=False,
        timeout=30,
    )
    if not ready:
        assert completed.returncode != 0
        refusal = json.loads(completed.stdout)
        assert refusal["refusal"] in {
            "E-C18-CGROUP-DELEGATION",
            "E-C18-HOST-FACT-MISSING",
        }
        assert reason
        assert not result.exists()
        return
    assert completed.returncode == 0, completed.stdout + completed.stderr
    value = json.loads(result.read_bytes())
    assert value["schema"] == "ranex-confinement-result-v1"
    assert all(value["namespace_readbacks"].values())
    assert value["command"]["no_new_privs"] is True
    assert value["command"]["landlock"] is True
    assert value["command"]["seccomp"] is True
    assert value["teardown"]["cgroup_kill"] is True
    assert value["teardown"]["populated"] == 0
