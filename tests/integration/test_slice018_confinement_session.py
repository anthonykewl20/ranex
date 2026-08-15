"""Frozen real-process integration contract for the SLICE-018 session service."""

from __future__ import annotations

import ctypes
import errno
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from launcher_host import require_pinned_build_closure

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
        "dev": {
            "type": "tmpfs",
            "nodes": [],
        },
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


def test_gate8_controller_refuses_a_launcher_without_pre_exec_witness_and_checks_proc_facts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A launcher exit is never allowed to masquerade as a command result."""

    readiness_read, readiness_write = os.pipe()
    os.close(readiness_write)
    try:
        with pytest.raises(host_confinement.HostConfinementError) as absent:
            host_confinement._read_launcher_readiness(readiness_read, 0.1)
    finally:
        os.close(readiness_read)
    assert absent.value.code == "E-C18-CGROUP-READBACK"

    readiness_read, readiness_write = os.pipe()
    payload = (
        b"ranex-worker-ready-v1 pid=4242 nnp=1 landlock=1 seccomp=1 "
        b"namespaces=user,mount,pid,ipc,network,cgroup\n"
    )
    os.write(readiness_write, payload)
    os.close(readiness_write)
    try:
        worker_pid, layers = host_confinement._read_launcher_readiness(readiness_read, 0.1)
    finally:
        os.close(readiness_read)
    assert worker_pid == 4242
    assert layers == {"no_new_privs": True, "landlock": True, "seccomp": True}

    readiness_read, readiness_write = os.pipe()
    os.write(readiness_write, payload + b"forged")
    os.close(readiness_write)
    try:
        with pytest.raises(host_confinement.HostConfinementError) as malformed:
            host_confinement._read_launcher_readiness(readiness_read, 0.1)
    finally:
        os.close(readiness_read)
    assert malformed.value.code == "E-C18-CGROUP-READBACK"

    original_read_text = Path.read_text

    def active_status(path: Path, *args: object, **kwargs: object) -> str:
        if str(path) == "/proc/4242/status":
            return "NoNewPrivs:\t1\nSeccomp:\t2\n"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", active_status)
    assert host_confinement._worker_enforcement_readbacks(4242) == {
        "no_new_privs": True,
        "seccomp": True,
    }

    def inactive_status(path: Path, *args: object, **kwargs: object) -> str:
        if str(path) == "/proc/4242/status":
            return "NoNewPrivs:\t0\nSeccomp:\t2\n"
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", inactive_status)
    with pytest.raises(host_confinement.HostConfinementError) as inactive:
        host_confinement._worker_enforcement_readbacks(4242)
    assert inactive.value.code == "E-C18-CGROUP-READBACK"


def test_gate1_readiness_releases_controller_before_the_worker_pipe_drains() -> None:
    """A /bin/true-equivalent worker must not be hidden by readiness EOF waiting."""

    readiness_read, readiness_write = os.pipe()
    payload = (
        b"ranex-worker-ready-v1 pid=4242 nnp=1 landlock=1 seccomp=1 "
        b"namespaces=user,mount,pid,ipc,network,cgroup\n"
    )
    try:
        os.write(readiness_write, payload)
        # Keep the write end open: the worker may exec and exit immediately,
        # so the controller must bind facts on the witness rather than EOF.
        worker_pid, layers = host_confinement._read_launcher_readiness(readiness_read, 0.1)
    finally:
        os.close(readiness_write)
        os.close(readiness_read)
    assert worker_pid == 4242
    assert layers == {"no_new_privs": True, "landlock": True, "seccomp": True}


def _real_host_ready() -> tuple[bool, str]:
    required = [Path("/sys/fs/cgroup/cgroup.controllers"), Path("/usr/bin/bwrap")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, f"real host prerequisites absent: {missing}"
    if not os.access("/sys/fs/cgroup", os.W_OK):
        return False, "no delegated writable cgroup-v2 root"
    return True, ""


def _unprivileged_namespaces_available() -> bool:
    """Probe the launcher's namespace set without changing this pytest process."""
    clone_newcgroup = 0x02000000
    clone_newns = 0x00020000
    clone_newipc = 0x08000000
    clone_newpid = 0x20000000
    clone_newuser = 0x10000000
    clone_newnet = 0x40000000
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            libc.unshare.argtypes = [ctypes.c_int]
            libc.unshare.restype = ctypes.c_int
            if (
                libc.unshare(
                    clone_newuser
                    | clone_newns
                    | clone_newpid
                    | clone_newipc
                    | clone_newnet
                    | clone_newcgroup
                )
                == 0
            ):
                os._exit(0)
            os.write(write_fd, str(ctypes.get_errno()).encode())
        finally:
            os.close(write_fd)
        os._exit(1)
    os.close(write_fd)
    try:
        reported_errno = os.read(read_fd, 32)
    finally:
        os.close(read_fd)
    os.waitpid(child, 0)
    return reported_errno not in {
        str(errno.EPERM).encode(),
        str(errno.EACCES).encode(),
        str(errno.EINVAL).encode(),
    }


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
    if not _unprivileged_namespaces_available():
        pytest.skip(
            "unprivileged user namespaces unavailable in this execution context — "
            "launcher enforcement host-unverified here"
        )
    root, descriptor = _materialize_case(tmp_path)
    compiler = Path("/usr/bin/x86_64-linux-gnu-gcc-13")
    subject = descriptor.parent / "subject"
    output = descriptor.parent / "output"
    worker_source = subject / "output-writer.c"
    worker = subject / "output-writer"
    worker_source.write_text(
        """
#include <fcntl.h>
#include <unistd.h>
int main(int argc, char **argv) {
    int fd;
    if (argc != 2) return 99;
    fd = open(argv[1], O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) return 98;
    return write(fd, "collected", 9) == 9 && close(fd) == 0 ? 0 : 97;
}
""",
        encoding="utf-8",
    )
    assert compiler.exists(), "C toolchain required for mandatory output lifecycle test"
    compiled = subprocess.run(
        [str(compiler), "-static", "-O2", "-o", str(worker), str(worker_source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    value = json.loads(descriptor.read_text())
    value["argv"] = [str(worker), str(output / "proof.txt")]
    descriptor.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")))
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
    assert value["command"]["exit_code"] == 0
    assert value["outputs"] == {
        "files": [{
            "path": "proof.txt",
            "bytes": 9,
            "sha256": hashlib.sha256(b"collected").hexdigest(),
        }],
        "bytes": 9,
        "inodes": 1,
    }
    assert value["teardown"] == {"cgroup_kill": True, "populated": 0, "cgroup_removed": True}


def test_gate7_launcher_enforces_landlock_and_seccomp_for_a_worker(tmp_path: Path) -> None:
    """NNP makes both kernel layers testable without a privileged host setup."""
    if not _unprivileged_namespaces_available():
        pytest.skip(
            "unprivileged user namespaces unavailable in this execution context — "
            "launcher enforcement host-unverified here"
        )
    require_pinned_build_closure()
    build = REPOSITORY / ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
    compiler = Path("/usr/bin/x86_64-linux-gnu-gcc-13")
    worker_source = tmp_path / "worker.c"
    subject = tmp_path / "subject"
    worker = subject / "worker"
    toolchain = Path("/usr/lib")
    output = tmp_path / "output"
    scratch = tmp_path / "scratch"
    denied = tmp_path / "outside-ruleset"
    subject.mkdir()
    output.mkdir()
    scratch.mkdir()
    worker_source.write_text(
        """
#include <errno.h>
#include <fcntl.h>
#include <linux/keyctl.h>
#include <string.h>
#include <sys/syscall.h>
#include <unistd.h>

int main(int argc, char **argv) {
    int fd;
    if (argc != 2) return 99;
    if (strcmp(argv[1], "keyctl") == 0) {
        errno = 0;
        return syscall(SYS_keyctl, KEYCTL_GET_KEYRING_ID, -3, 0) == -1 ? errno : 98;
    }
    fd = open(argv[1], O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) return errno;
    if (write(fd, "ok", 2) != 2 || close(fd) != 0) return 97;
    return 0;
}
""",
        encoding="utf-8",
    )
    assert compiler.exists(), "C toolchain required for mandatory launcher enforcement test"
    try:
        built = subprocess.run(
            [
                *CONTROLLER,
                "launcher-build",
                "--manifest",
                "governance/confinement/native-launcher-build-v1.json",
                "--source",
                "native/ranex-worker-launcher/launcher.c",
                "--output",
                ".local/ranex/build/strict-local-v1/ranex-worker-launcher",
            ],
            cwd=REPOSITORY,
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert built.returncode == 0, built.stdout + built.stderr
        compiled = subprocess.run(
            [str(compiler), "-static", "-O2", "-o", str(worker), str(worker_source)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr

        permitted = subprocess.run(
            [
                str(build), "--ranex-worker-exec", str(subject), str(toolchain), str(output),
                str(scratch), str(worker), str(scratch / "allowed"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert permitted.returncode == 0, permitted.stdout + permitted.stderr
        assert (scratch / "allowed").read_text(encoding="utf-8") == "ok"

        landlock_denied = subprocess.run(
            [
                str(build), "--ranex-worker-exec", str(subject), str(toolchain), str(output),
                str(scratch), str(worker), str(denied),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert landlock_denied.returncode in {13, 1}
        assert not denied.exists()

        seccomp_denied = subprocess.run(
            [
                str(build), "--ranex-worker-exec", str(subject), str(toolchain), str(output),
                str(scratch), str(worker), "keyctl",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert seccomp_denied.returncode == 1

    finally:
        build.unlink(missing_ok=True)


def test_gate7_dynamic_elf_interpreter_resolves_from_toolchain_mount(tmp_path: Path) -> None:
    """The dynamic loader and libc must be readable from the declared toolchain tree."""
    if not _unprivileged_namespaces_available():
        pytest.skip(
            "unprivileged user namespaces unavailable in this execution context — "
            "launcher enforcement host-unverified here"
        )
    require_pinned_build_closure()
    build = REPOSITORY / ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
    compiler = Path("/usr/bin/x86_64-linux-gnu-gcc-13")
    subject = tmp_path / "subject"
    output = tmp_path / "output"
    scratch = tmp_path / "scratch"
    toolchain = Path("/usr/lib")
    subject.mkdir()
    output.mkdir()
    scratch.mkdir()
    worker_source = subject / "dynamic-worker.c"
    worker = subject / "dynamic-worker"
    worker_source.write_text(
        """
#include <fcntl.h>
#include <unistd.h>
int main(int argc, char **argv) {
    int fd;
    if (argc != 2) return 99;
    fd = open(argv[1], O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (fd < 0) return 98;
    return write(fd, "dynamic", 7) == 7 && close(fd) == 0 ? 0 : 97;
}
""",
        encoding="utf-8",
    )
    assert compiler.exists(), "C toolchain required for dynamic loader test"
    try:
        built = subprocess.run(
            [
                *CONTROLLER, "launcher-build", "--manifest",
                "governance/confinement/native-launcher-build-v1.json", "--source",
                "native/ranex-worker-launcher/launcher.c", "--output",
                ".local/ranex/build/strict-local-v1/ranex-worker-launcher",
            ],
            cwd=REPOSITORY,
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert built.returncode == 0, built.stdout + built.stderr
        compiled = subprocess.run(
            [str(compiler), "-O2", "-o", str(worker), str(worker_source)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert compiled.returncode == 0, compiled.stdout + compiled.stderr
        completed = subprocess.run(
            [
                str(build), "--ranex-worker-exec", str(subject), str(toolchain), str(output),
                str(scratch), str(worker), str(output / "dynamic-proof"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert (output / "dynamic-proof").read_text(encoding="utf-8") == "dynamic"
    finally:
        build.unlink(missing_ok=True)
