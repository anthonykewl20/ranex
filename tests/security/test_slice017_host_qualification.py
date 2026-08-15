"""Frozen acceptance tests for SLICE-017 host qualification.

These tests intentionally use the public controller process only.  The small C
harness below changes what the kernel exposes to that process; it never edits a
qualification result.  Imports of ``ranex.cli.host_confinement`` are also
deliberately absent so that the not-yet-implemented module is a normal red test,
not a collection error.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import re
import select
import signal
import socket
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from launcher_host import (
    require_delegated_userns_selftest,
    require_pinned_build_closure,
    require_unprivileged_userns,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE = Path("governance/confinement/strict-local-host-v1.json")
MANIFEST = Path("governance/confinement/native-launcher-build-v1.json")
SOURCE = Path("native/ranex-worker-launcher/launcher.c")
BUILD_ARTIFACT = Path(".local/ranex/build/strict-local-v1/ranex-worker-launcher")
INSTALLED_ARTIFACT = Path(".local/ranex/libexec/strict-local-v1/ranex-worker-launcher")
REPORT = Path(".local/ranex/qualification/strict-local-v1.json")

# Reach the controller through the interpreter already running this suite, not
# through `uv`. The governed run executes this file inside an ADR-009
# materialised sample whose PATH is the pinned toolchain plus the provisioned
# environment's bin, and whose HOME is the sample's own; `uv` lives in neither.
# Spawning it there raised FileNotFoundError in the session fixture and erased
# this file's evidence from the one run that gates the repository, while a
# developer checkout stayed green. `sys.executable` is the project environment
# in a checkout and in a sample alike, and `ROOT/.venv` exists only in the
# former.
CONTROLLER = [
    sys.executable,
    "-m",
    "ranex.cli.host_confinement",
]
# mask-file must exec the controller in the helper's process: a forking launcher
# makes /proc/self/status resolve to a fresh, unmasked PID. The direct form now
# satisfies that by construction.
DIRECT_CONTROLLER = list(CONTROLLER)
BROKER_PREFIX = [
    "/usr/bin/systemd-run",
    "--user",
    "--no-ask-password",
    "--quiet",
    "--collect",
    "--wait",
    "--pipe",
    "--service-type=exec",
    "--property=Delegate=yes",
    "--property=CPUAccounting=yes",
    "--property=MemoryAccounting=yes",
    "--property=TasksAccounting=yes",
]

E_ARCH = "E-C17-ARCH-UNSUPPORTED"
E_DELEGATION = "E-C17-CGROUP-DELEGATION"
E_EXEC = "E-C17-EXEC-OBJECT-DRIFT"
E_FACT = "E-C17-HOST-FACT-MISSING"
E_CLEANUP = "E-C17-CLEANUP"

REQUIRED_CONTROLLERS = {"cpu", "memory", "pids"}
NAMESPACE_FLAGS = {
    "user": 0x10000000,
    "mount": 0x00020000,
    "pid": 0x20000000,
    "ipc": 0x08000000,
    "network": 0x40000000,
}
SYS_OPENAT2_X86_64 = 437
SYS_LANDLOCK_CREATE_RULESET_X86_64 = 444
LANDLOCK_CREATE_RULESET_VERSION = 1


def _confined_no_delegation() -> bool:
    """True inside the landing gate's network-denial sandbox.

    That sandbox runs after unshare(CLONE_NEWUSER|CLONE_NEWNET) with no uid
    mapping, so /proc/self/uid_map is empty: the controller cannot trust a
    launcher built there nor reach a delegated cgroup. Detecting that lets a
    test assert the controller's real refusal instead of constructing a
    host-only scenario it cannot build here.
    """
    try:
        lines = Path("/proc/self/uid_map").read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    return not any(line.strip() for line in lines)


def _controller_argv(subcommand: str, *arguments: str | Path) -> list[str]:
    return [*CONTROLLER, subcommand, *(str(argument) for argument in arguments)]


def _direct_controller_argv(subcommand: str, *arguments: str | Path) -> list[str]:
    return [*DIRECT_CONTROLLER, subcommand, *(str(argument) for argument in arguments)]


def _controller_env(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src"
    environment["UV_OFFLINE"] = "1"
    if overrides:
        environment.update(overrides)
    return environment


def _run_controller(
    subcommand: str,
    *arguments: str | Path,
    environment: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _controller_argv(subcommand, *arguments),
        cwd=ROOT,
        env=_controller_env(environment),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )


def _diagnostic(completed: subprocess.CompletedProcess[str]) -> str:
    return (
        f"exit={completed.returncode}\n"
        f"stdout={completed.stdout!r}\n"
        f"stderr={completed.stderr!r}"
    )


def _json_stdout(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        pytest.fail(f"controller stdout is not one JSON object: {_diagnostic(completed)}\n{error}")
    assert isinstance(value, dict), _diagnostic(completed)
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _refusal(
    completed: subprocess.CompletedProcess[str], expected: str | set[str]
) -> dict[str, Any]:
    assert completed.returncode != 0, _diagnostic(completed)
    refusal = _json_stdout(completed)
    assert set(refusal) == {"refusal", "detail"}
    expected_codes = {expected} if isinstance(expected, str) else expected
    assert refusal["refusal"] in expected_codes
    assert isinstance(refusal["detail"], str) and refusal["detail"]
    report = ROOT / REPORT
    assert not report.exists()
    if report.parent.exists():
        assert not any(
            child.name.startswith(f".{report.name}.")
            or child.name.startswith(f"{report.name}.")
            for child in report.parent.iterdir()
        )
    return refusal


def _load_report() -> dict[str, Any]:
    raw = (ROOT / REPORT).read_bytes()
    value = json.loads(raw)
    assert isinstance(value, dict)
    assert raw == _canonical_bytes(value)
    return value


def _qualify_arguments() -> tuple[str | Path, ...]:
    return (
        "--profile",
        PROFILE,
        "--artifact",
        INSTALLED_ARTIFACT,
        "--manifest",
        MANIFEST,
        "--report",
        REPORT,
    )


def _derived_bus_environment() -> dict[str, str]:
    runtime = Path("/run/user") / str(os.geteuid())
    return {
        "XDG_RUNTIME_DIR": str(runtime),
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime / 'bus'}",
    }


@pytest.fixture(scope="session")
def installed_launcher() -> Iterator[None]:
    """Build and install the frozen launcher for the standalone security file."""

    require_pinned_build_closure()
    generated = [ROOT / BUILD_ARTIFACT, ROOT / INSTALLED_ARTIFACT, ROOT / REPORT]
    (ROOT / REPORT).unlink(missing_ok=True)
    assert not any(path.exists() for path in generated), (
        "SLICE-017 acceptance tests require clean ignored output paths"
    )

    built = _run_controller(
        "launcher-build",
        "--manifest",
        MANIFEST,
        "--source",
        SOURCE,
        "--output",
        BUILD_ARTIFACT,
    )
    assert built.returncode == 0, _diagnostic(built)
    installed = _run_controller(
        "launcher-install",
        "--manifest",
        MANIFEST,
        "--artifact",
        BUILD_ARTIFACT,
        "--destination",
        INSTALLED_ARTIFACT,
    )
    assert installed.returncode == 0, _diagnostic(installed)
    try:
        yield
    finally:
        for path in reversed(generated):
            path.unlink(missing_ok=True)


@pytest.fixture(autouse=True)
def clean_qualification_report() -> Iterator[None]:
    report = ROOT / REPORT
    report.unlink(missing_ok=True)
    try:
        yield
    finally:
        report.unlink(missing_ok=True)


SANDBOX_SOURCE = r"""
#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>
#include <sched.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/personality.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/wait.h>
#include <unistd.h>

static void die(const char *what) { perror(what); _exit(125); }

static void write_text(const char *path, const char *text) {
    int fd = open(path, O_WRONLY | O_CLOEXEC);
    if (fd < 0) die(path);
    size_t size = strlen(text);
    if (write(fd, text, size) != (ssize_t)size) die("write");
    if (close(fd) != 0) die("close");
}

static void private_user_mount_namespace(void) {
    char map[128];
    uid_t uid = getuid();
    gid_t gid = getgid();
    if (unshare(CLONE_NEWUSER) != 0) die("unshare user");
    write_text("/proc/self/setgroups", "deny\n");
    snprintf(map, sizeof(map), "0 %u 1\n", uid);
    write_text("/proc/self/uid_map", map);
    snprintf(map, sizeof(map), "0 %u 1\n", gid);
    write_text("/proc/self/gid_map", map);
    if (unshare(CLONE_NEWNS) != 0) die("unshare mount");
    if (mount(NULL, "/", NULL, MS_REC | MS_PRIVATE, NULL) != 0) die("private mounts");
}

static void block_syscall(unsigned int number) {
    struct sock_filter code[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, number, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | ENOSYS),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = { .len = 4, .filter = code };
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) die("NNP");
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program) != 0) die("seccomp");
}

static void block_namespace(unsigned int flag) {
    struct sock_filter code[] = {
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_unshare, 0, 4),
        BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, args[0])),
        BPF_STMT(BPF_ALU | BPF_AND | BPF_K, flag),
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, flag, 0, 1),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ERRNO | ENOSYS),
        BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    };
    struct sock_fprog program = { .len = 7, .filter = code };
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0) die("NNP");
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &program) != 0) die("seccomp");
}

static void mask_directory(const char *target, const char *scratch) {
    char empty[4096];
    snprintf(empty, sizeof(empty), "%s/empty", scratch);
    if (mkdir(empty, 0700) != 0 && errno != EEXIST) die("mkdir empty");
    if (mount(empty, target, NULL, MS_BIND | MS_REC, NULL) != 0) die("bind directory");
}

static void mask_file(const char *target, const char *scratch) {
    char placeholder[4096];
    int fd;
    snprintf(placeholder, sizeof(placeholder), "%s/unavailable", scratch);
    fd = open(placeholder, O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC, 0000);
    if (fd < 0 && errno != EEXIST) die("create unavailable");
    if (fd >= 0 && close(fd) != 0) die("close unavailable");
    if (mount(placeholder, target, NULL, MS_BIND, NULL) != 0) die("bind file");
}

static void mask_cgroup_kill(const char *scratch) {
    FILE *stream = fopen("/proc/self/cgroup", "re");
    char line[4096], target[8192];
    if (!stream) die("cgroup");
    if (!fgets(line, sizeof(line), stream)) die("read cgroup");
    if (fclose(stream) != 0) die("close cgroup");
    char *relative = strstr(line, "::");
    if (!relative) die("parse cgroup");
    relative += 2;
    relative[strcspn(relative, "\n")] = '\0';
    snprintf(target, sizeof(target), "/sys/fs/cgroup%s/cgroup.kill", relative);
    mask_file(target, scratch);
}

static void current_cgroup(char *path, size_t size) {
    FILE *stream = fopen("/proc/self/cgroup", "re");
    char line[4096];
    if (!stream) die("cgroup");
    if (!fgets(line, sizeof(line), stream)) die("read cgroup");
    if (fclose(stream) != 0) die("close cgroup");
    char *relative = strstr(line, "::");
    if (!relative) die("parse cgroup");
    relative += 2;
    relative[strcspn(relative, "\n")] = '\0';
    snprintf(path, size, "/sys/fs/cgroup%s", relative);
}

static void write_pid(const char *directory, pid_t pid) {
    char path[8192], text[64];
    snprintf(path, sizeof(path), "%s/cgroup.procs", directory);
    snprintf(text, sizeof(text), "%d\n", pid);
    write_text(path, text);
}

static int controller_subset(const char *controllers, char **command) {
    char root[4096], keeper[8192], probe[8192], control[8192], enable[256], disable[256];
    int gate[2], status;
    pid_t child;
    current_cgroup(root, sizeof(root));
    snprintf(keeper, sizeof(keeper), "%s/acceptance-keeper-%d", root, getpid());
    snprintf(probe, sizeof(probe), "%s/acceptance-root-%d", root, getpid());
    snprintf(control, sizeof(control), "%s/cgroup.subtree_control", root);
    if (mkdir(keeper, 0755) != 0) die("mkdir keeper");
    write_pid(keeper, getpid());
    snprintf(enable, sizeof(enable), "%s", controllers);
    write_text(control, enable);
    if (mkdir(probe, 0755) != 0) die("mkdir root");
    if (pipe2(gate, O_CLOEXEC) != 0) die("pipe");
    child = fork();
    if (child < 0) die("fork");
    if (child == 0) {
        char byte;
        close(gate[1]);
        if (read(gate[0], &byte, 1) != 1) die("gate");
        close(gate[0]);
        execvp(command[0], command);
        die("exec controller");
    }
    close(gate[0]);
    write_pid(probe, child);
    if (write(gate[1], "x", 1) != 1) die("release");
    close(gate[1]);
    if (waitpid(child, &status, 0) != child) die("waitpid");
    if (rmdir(probe) != 0) die("rmdir root");
    snprintf(disable, sizeof(disable), "%s", controllers);
    for (char *plus = disable; (plus = strchr(plus, '+')); plus++) *plus = '-';
    write_text(control, disable);
    write_pid(root, getpid());
    if (rmdir(keeper) != 0) die("rmdir keeper");
    if (WIFEXITED(status)) return WEXITSTATUS(status);
    if (WIFSIGNALED(status)) return 128 + WTERMSIG(status);
    return 125;
}

int main(int argc, char **argv) {
    int command = 3;
    if (argc < 4) return 124;
    if (strcmp(argv[1], "linux32") == 0) {
        if (personality(PER_LINUX32) == -1) die("personality");
    } else if (strcmp(argv[1], "controller-subset") == 0) {
        if (strcmp(argv[3], "--") != 0) return 124;
        return controller_subset(argv[2], &argv[4]);
    } else {
        private_user_mount_namespace();
        if (strcmp(argv[1], "block-syscall") == 0) {
            block_syscall((unsigned int)strtoul(argv[2], NULL, 0));
        } else if (strcmp(argv[1], "block-namespace") == 0) {
            block_namespace((unsigned int)strtoul(argv[2], NULL, 0));
        } else if (strcmp(argv[1], "mask-directory") == 0) {
            if (argc < 5) return 124;
            mask_directory(argv[2], argv[3]);
            command = 4;
        } else if (strcmp(argv[1], "mask-file") == 0) {
            if (argc < 5) return 124;
            mask_file(argv[2], argv[3]);
            command = 4;
        } else if (strcmp(argv[1], "mask-cgroup-kill") == 0) {
            if (argc < 4) return 124;
            mask_cgroup_kill(argv[2]);
            command = 3;
        } else {
            return 124;
        }
    }
    if (strcmp(argv[command], "--") == 0) command++;
    execvp(argv[command], &argv[command]);
    die("exec controller");
}
"""


@pytest.fixture(scope="session")
def sandbox_helper(tmp_path_factory: pytest.TempPathFactory) -> Path:
    require_unprivileged_userns()
    directory = tmp_path_factory.mktemp("slice017-sandbox")
    source = directory / "sandbox.c"
    executable = directory / "sandbox"
    source.write_text(SANDBOX_SOURCE, encoding="utf-8")
    subprocess.run(
        [
            "/usr/bin/x86_64-linux-gnu-gcc-13",
            "-std=gnu17",
            "-O2",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-o",
            str(executable),
            str(source),
        ],
        check=True,
    )
    if _confined_no_delegation():
        return executable
    # Namespace qualification is specified in terms of unshare(2), so this
    # filter deliberately does not intercept clone(2)/clone3(2).
    self_test = subprocess.run(
        [
            str(executable),
            "block-namespace",
            hex(NAMESPACE_FLAGS["user"]),
            "--",
            "/bin/true",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    require_delegated_userns_selftest(self_test.returncode, self_test.stderr)
    assert self_test.returncode == 0, _diagnostic(self_test)
    return executable


@dataclass
class CgroupObservation:
    """Independent observation of newly-created cgroups and live members."""

    root: Path
    stop: threading.Event = field(default_factory=threading.Event)
    ready: threading.Event = field(default_factory=threading.Event)
    paths: set[Path] = field(default_factory=set)
    deleted_paths: set[Path] = field(default_factory=set)
    live_pids: dict[Path, set[int]] = field(default_factory=dict)
    _baseline: set[Path] = field(default_factory=set)
    _thread: threading.Thread | None = None
    _error: BaseException | None = None

    def _directories(self) -> set[Path]:
        if not self.root.is_dir():
            return set()
        return {path for path in self.root.rglob("*") if path.is_dir()}

    def start(self) -> None:
        self._baseline = self._directories()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()
        assert self.ready.wait(timeout=5), "cgroup inotify observer did not become ready"
        if self._error is not None:
            raise AssertionError("cgroup inotify observer failed to start") from self._error

    def _sample_members(self) -> None:
        for path in tuple(self.paths):
            try:
                pids = {
                    int(value)
                    for value in (path / "cgroup.procs").read_text().split()
                    if (Path("/proc") / value).exists()
                }
            except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError):
                continue
            if pids:
                self.live_pids.setdefault(path, set()).update(pids)

    def _watch(self) -> None:
        descriptor = -1
        try:
            libc = ctypes.CDLL(None, use_errno=True)
            descriptor = int(libc.inotify_init1(os.O_CLOEXEC | os.O_NONBLOCK))
            if descriptor < 0:
                error = ctypes.get_errno()
                raise OSError(error, os.strerror(error))

            watches: dict[int, Path] = {}
            event_mask = 0x00000100 | 0x00000200  # IN_CREATE | IN_DELETE

            def add_watch(path: Path) -> None:
                watch = int(libc.inotify_add_watch(descriptor, os.fsencode(path), event_mask))
                if watch < 0:
                    error = ctypes.get_errno()
                    if error == 2:  # A short-lived cgroup may already be gone.
                        return
                    raise OSError(error, os.strerror(error), path)
                watches[watch] = path

            for path in {self.root, *self._baseline}:
                add_watch(path)
            self.ready.set()

            while True:
                # Topology is event-driven; only already-known cgroup membership
                # is sampled, at 1 ms, as supplementary diagnostic evidence.
                readable, _, _ = select.select([descriptor], [], [], 0.001)
                if readable:
                    data = os.read(descriptor, 64 * 1024)
                    offset = 0
                    while offset < len(data):
                        watch, mask, _cookie, length = struct.unpack_from(
                            "iIII", data, offset
                        )
                        offset += 16
                        if mask & 0x00004000:  # IN_Q_OVERFLOW
                            raise AssertionError("cgroup inotify event queue overflowed")
                        name = data[offset : offset + length].split(b"\0", 1)[0]
                        offset += length
                        parent = watches.get(watch)
                        if parent is None or not name:
                            continue
                        path = parent / os.fsdecode(name)
                        if not mask & 0x40000000:  # IN_ISDIR
                            continue
                        if mask & 0x00000100:  # IN_CREATE
                            self.paths.add(path)
                            self._sample_members()
                            try:
                                add_watch(path)
                                for descendant in self._directories() - self._baseline:
                                    if descendant == path or path in descendant.parents:
                                        self.paths.add(descendant)
                                        add_watch(descendant)
                            except NotADirectoryError:
                                continue
                        if mask & 0x00000200:  # IN_DELETE
                            self.deleted_paths.add(path)
                self._sample_members()
                if self.stop.is_set() and not readable:
                    break
        except BaseException as error:
            self._error = error
        finally:
            self.ready.set()
            if descriptor >= 0:
                os.close(descriptor)

    def finish(self) -> None:
        self.stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
            assert not self._thread.is_alive(), "cgroup inotify observer did not stop"
        if self._error is not None:
            raise AssertionError("cgroup inotify observer failed") from self._error


def _user_service_cgroup_root() -> Path:
    uid = os.geteuid()
    root = Path(f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service")
    assert root.is_dir(), (
        "the systemd user-service cgroup root does not exist at the derived path "
        f"{root}; cannot corroborate delegated probe creation"
    )
    return root


def _stop_unit(unit: str) -> None:
    environment = {**os.environ, **_derived_bus_environment()}
    subprocess.run(
        ["/usr/bin/systemctl", "--user", "stop", unit],
        env=environment,
        capture_output=True,
        check=False,
    )
    subprocess.run(
        ["/usr/bin/systemctl", "--user", "reset-failed", unit],
        env=environment,
        capture_output=True,
        check=False,
    )


def _await_probe_pid(marker: Path, broker: subprocess.Popen[str]) -> int:
    """Read the controller PID recorded before it is released to exec."""

    deadline = time.monotonic() + 5
    while broker.poll() is None and time.monotonic() < deadline:
        try:
            value = marker.read_text(encoding="ascii").strip()
        except FileNotFoundError:
            value = ""
        if value.isdecimal() and int(value) > 1:
            return int(value)
        time.sleep(0.001)
    raise AssertionError("did not observe the live delegated controller PID")


def _run_in_delegated_unit(
    subcommand: str,
    *arguments: str | Path,
    sandbox: Sequence[str | Path] = (),
    service_environment: Mapping[str, str] | None = None,
    observe: bool = False,
    direct_controller: bool = False,
    on_unit_started: Callable[[int], None] | None = None,
) -> tuple[subprocess.CompletedProcess[str], CgroupObservation | None]:
    unit = f"ranex-acceptance-{os.getpid()}-{uuid.uuid4().hex}.service"
    command_builder = _direct_controller_argv if direct_controller else _controller_argv
    command = command_builder(subcommand, *arguments)
    if sandbox:
        command = [*(str(value) for value in sandbox), "--", *command]

    marker_directory: tempfile.TemporaryDirectory[str] | None = None
    release: Path | None = None
    if on_unit_started is not None:
        marker_directory = tempfile.TemporaryDirectory(prefix="ranex-cleanup-probe-")
        marker = Path(marker_directory.name) / "pid"
        release = Path(marker_directory.name) / "release"
        command = [
            sys.executable,
            "-c",
            (
                "from pathlib import Path\n"
                "import os\n"
                "import sys\n"
                "import time\n"
                "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='ascii')\n"
                "while not Path(sys.argv[2]).exists():\n"
                "    time.sleep(0.001)\n"
                "os.execvpe(sys.argv[3], sys.argv[3:], os.environ)\n"
            ),
            str(marker),
            str(release),
            *command,
        ]

    service_env = {
        "PYTHONPATH": "src",
        "PATH": os.environ["PATH"],
        "UV_OFFLINE": "1",
    }
    service_env.update(service_environment or {})
    argv = [
        *BROKER_PREFIX,
        f"--unit={unit}",
        f"--working-directory={ROOT}",
        *(f"--setenv={name}={value}" for name, value in service_env.items()),
        *command,
    ]
    observer = CgroupObservation(_user_service_cgroup_root()) if observe else None
    if observer is not None:
        observer.start()
    try:
        broker = subprocess.Popen(
            argv,
            cwd=ROOT,
            env={**os.environ, **_derived_bus_environment()},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if on_unit_started is not None:
            on_unit_started(_await_probe_pid(marker, broker))
            release.touch()
        stdout, stderr = broker.communicate(timeout=180)
        completed = subprocess.CompletedProcess(argv, broker.returncode, stdout, stderr)
    finally:
        if observer is not None:
            observer.finish()
        _stop_unit(unit)
        if marker_directory is not None:
            marker_directory.cleanup()
    return completed, observer


def _probe_transcript(report: Mapping[str, Any]) -> Mapping[str, Any]:
    cgroup = report["cgroup"]
    assert isinstance(cgroup, dict)
    transcript = cgroup["probe_transcript"]
    assert isinstance(transcript, dict)
    return transcript


def _assert_real_probe(report: Mapping[str, Any], observed: CgroupObservation) -> None:
    transcript = _probe_transcript(report)
    assert transcript["created"] is True
    assert REQUIRED_CONTROLLERS <= set(transcript["controllers_enabled"])
    child_pid = transcript["child_pid"]
    assert isinstance(child_pid, int) and child_pid > 1
    assert child_pid in transcript["read_back_pids"]
    assert transcript["removed"] is True

    path = Path(transcript["cgroup_path"])
    assert path in observed.paths
    assert path in observed.deleted_paths
    assert not path.exists()


def _assert_open_object(
    value: object,
    *,
    expected_path: Path,
) -> None:
    assert isinstance(value, dict)
    assert set(value) >= {
        "path",
        "realpath",
        "sha256",
        "device",
        "inode",
        "uid",
        "gid",
        "mode",
        "mount_id",
        "security_capability",
    }
    path = Path(value["path"])
    realpath = Path(value["realpath"])
    assert path == expected_path
    assert path.is_absolute()
    assert realpath == path.resolve(strict=True)
    assert realpath == realpath.resolve(strict=True)
    assert value["sha256"] == _sha256_file(realpath)
    assert value["security_capability"] in (None, "", False)
    observed = realpath.stat()
    assert value["device"] == observed.st_dev
    assert value["inode"] == observed.st_ino
    assert value["uid"] == observed.st_uid
    assert value["gid"] == observed.st_gid
    assert value["mode"] == stat.S_IMODE(observed.st_mode)
    assert isinstance(value["mount_id"], int) and value["mount_id"] > 0


def _landlock_abi() -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    result = int(
        libc.syscall(
            ctypes.c_long(SYS_LANDLOCK_CREATE_RULESET_X86_64),
            ctypes.c_void_p(),
            ctypes.c_size_t(0),
            ctypes.c_uint(LANDLOCK_CREATE_RULESET_VERSION),
        )
    )
    if result < 0:
        error = ctypes.get_errno()
        raise AssertionError(f"independent Landlock ABI probe failed: {os.strerror(error)}")
    return result


def _cgroup2_mounts() -> set[Path]:
    mounts: set[Path] = set()
    for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
        left, separator, right = line.partition(" - ")
        assert separator, f"malformed mountinfo line: {line!r}"
        if right.split()[0] != "cgroup2":
            continue
        escaped = left.split()[4]
        mount = escaped.replace("\\040", " ").replace("\\011", "\t")
        mounts.add(Path(mount.replace("\\134", "\\")))
    assert mounts, "no cgroup2 mount was reported by /proc/self/mountinfo"
    return mounts


def _assert_nonempty(value: object) -> None:
    if isinstance(value, str):
        assert value.strip()
    elif isinstance(value, Mapping):
        assert value
        assert all(isinstance(key, str) and key for key in value)
        for item in value.values():
            _assert_nonempty(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        assert value
        for item in value:
            _assert_nonempty(item)
    elif isinstance(value, int) and not isinstance(value, bool):
        assert value >= 0
    else:
        raise AssertionError(f"host-state value is not a nonempty JSON value: {value!r}")


def _required_host_text(path: Path) -> str:
    value = path.read_text(encoding="utf-8").strip()
    assert value, f"mandatory host-state source is empty: {path}"
    return value


def _assert_success_report(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert completed.returncode == 0, _diagnostic(completed)
    report = _load_report()
    assert set(report) == {
        "schema",
        "qualified",
        "refusal",
        "kernel",
        "primitives",
        "cgroup",
        "open_objects",
        "digests",
        "delegation",
        "host_state",
    }
    assert isinstance(report["schema"], str) and report["schema"]
    assert report["qualified"] is True
    assert report["refusal"] is None

    kernel = report["kernel"]
    assert isinstance(kernel, dict)
    assert set(kernel) == {"release", "architecture"}
    assert kernel["release"] == os.uname().release
    assert kernel["architecture"] == os.uname().machine

    primitives = report["primitives"]
    assert isinstance(primitives, dict)
    assert set(primitives) >= {
        "landlock",
        "seccomp_filter",
        "no_new_privs",
        "namespaces",
        "openat2",
    }
    landlock = primitives["landlock"]
    assert isinstance(landlock, dict)
    assert set(landlock) >= {"available", "abi"}
    assert landlock["available"] is True
    assert landlock["abi"] == _landlock_abi()
    assert landlock["abi"] >= 6
    assert primitives["seccomp_filter"] is True
    assert primitives["no_new_privs"] is True
    namespaces = primitives["namespaces"]
    assert isinstance(namespaces, dict)
    assert set(namespaces) == set(NAMESPACE_FLAGS)
    assert all(namespaces[name] is True for name in NAMESPACE_FLAGS)
    assert primitives["openat2"] is True

    cgroup = report["cgroup"]
    assert isinstance(cgroup, dict)
    assert set(cgroup) >= {
        "cgroup_kill",
        "mount",
        "root",
        "controllers",
        "probe_transcript",
    }
    assert cgroup["cgroup_kill"] is True
    mount = cgroup["mount"]
    assert isinstance(mount, dict)
    assert set(mount) >= {"path", "filesystem"}
    cgroup_mounts = _cgroup2_mounts()
    cgroup_mount = Path(mount["path"])
    assert cgroup_mount in cgroup_mounts
    assert mount["filesystem"] == "cgroup2"
    cgroup_root = Path(cgroup["root"])
    assert cgroup_root.is_absolute()
    assert cgroup_root == cgroup_mount or cgroup_mount in cgroup_root.parents
    assert REQUIRED_CONTROLLERS <= set(cgroup["controllers"])

    profile = json.loads((ROOT / PROFILE).read_bytes())
    assert isinstance(profile, dict)
    helpers = profile["helpers"]
    assert isinstance(helpers, dict)
    bubblewrap = helpers["bubblewrap"]
    assert isinstance(bubblewrap, dict)
    open_objects = report["open_objects"]
    assert isinstance(open_objects, dict)
    assert set(open_objects) == {"bubblewrap", "launcher"}
    _assert_open_object(
        open_objects["bubblewrap"], expected_path=Path(bubblewrap["path"])
    )
    _assert_open_object(
        open_objects["launcher"], expected_path=(ROOT / INSTALLED_ARTIFACT).resolve()
    )

    digests = report["digests"]
    assert isinstance(digests, dict)
    assert set(digests) == {"profile", "build_manifest", "artifact"}
    assert digests["profile"] == _sha256_file(ROOT / PROFILE)
    assert digests["build_manifest"] == _sha256_file(ROOT / MANIFEST)
    assert digests["artifact"] == _sha256_file(ROOT / INSTALLED_ARTIFACT)

    host_state = report["host_state"]
    assert isinstance(host_state, dict)
    assert set(host_state) == {
        "lsm",
        "unprivileged_userns_sysctls",
        "boot_id",
        "machine_id",
        "delegation_identity",
    }
    lsm = host_state["lsm"]
    assert isinstance(lsm, dict)
    assert set(lsm) == {
        "securityfs_lsm",
        "apparmor_policy_identity",
        "selinux_policy_identity",
    }
    assert lsm["securityfs_lsm"] == _required_host_text(Path("/sys/kernel/security/lsm"))
    _assert_nonempty(lsm["apparmor_policy_identity"])
    _assert_nonempty(lsm["selinux_policy_identity"])
    sysctls = host_state["unprivileged_userns_sysctls"]
    assert isinstance(sysctls, dict)
    sysctl_paths = {
        "user.max_user_namespaces": Path("/proc/sys/user/max_user_namespaces"),
        "kernel.unprivileged_userns_clone": Path(
            "/proc/sys/kernel/unprivileged_userns_clone"
        ),
    }
    expected_sysctls = {
        name: _required_host_text(path)
        for name, path in sysctl_paths.items()
        if path.exists()
    }
    assert set(sysctls) == set(expected_sysctls)
    assert {name: str(value) for name, value in sysctls.items()} == expected_sysctls
    assert host_state["boot_id"] == _required_host_text(
        Path("/proc/sys/kernel/random/boot_id")
    )
    assert host_state["machine_id"] == _required_host_text(Path("/etc/machine-id"))
    delegation_identity = host_state["delegation_identity"]
    assert isinstance(delegation_identity, dict)
    assert set(delegation_identity) >= {"uid", "gid", "cgroup_root", "source"}
    assert delegation_identity["uid"] == os.geteuid()
    assert delegation_identity["gid"] == os.getegid()
    assert Path(delegation_identity["cgroup_root"]) == cgroup_root
    assert delegation_identity["source"] == report["delegation"]["source"]
    _assert_nonempty(delegation_identity)
    return report


def test_gate5_existing_delegation_runs_a_real_child_cgroup_probe(
    installed_launcher: None,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    completed, observed = _run_in_delegated_unit(
        "qualify", *_qualify_arguments(), observe=True
    )
    report = _assert_success_report(completed)
    assert observed is not None
    assert report["delegation"]["source"] == "existing"
    _assert_real_probe(report, observed)


def test_gate5_login_scope_is_rejected_and_broker_runs_a_real_probe(
    installed_launcher: None,
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    hostile_runtime = tmp_path / "attacker-runtime"
    hostile_runtime.mkdir()
    hostile_bus = hostile_runtime / "bus"
    trap = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    trap.bind(str(hostile_bus))
    trap.listen()
    trap.setblocking(False)
    hostile_root = tmp_path / "attacker-cgroup"
    hostile_root.mkdir()
    (hostile_root / "cgroup.controllers").write_text("cpu memory pids\n")

    trap_connected = False
    try:
        completed, observer = _run_in_delegated_unit(
            "qualify",
            *_qualify_arguments(),
            sandbox=(sandbox_helper, "controller-subset", "+memory +pids"),
            service_environment={
                "XDG_RUNTIME_DIR": str(hostile_runtime),
                "DBUS_SESSION_BUS_ADDRESS": f"unix:path={hostile_bus}",
                "RANEX_CGROUP_ROOT": str(hostile_root),
                "CGROUP_ROOT": str(hostile_root),
            },
            observe=True,
        )
    finally:
        try:
            connection, _ = trap.accept()
        except BlockingIOError:
            pass
        else:
            trap_connected = True
            connection.close()
        trap.close()

    report = _assert_success_report(completed)
    delegation = report["delegation"]
    broker = delegation["broker"]
    assert delegation["source"] == "broker"
    existing_controllers = set(delegation["existing_root"]["controllers"])
    assert existing_controllers < REQUIRED_CONTROLLERS
    assert "cpu" not in existing_controllers
    assert broker["status"] == "ran"
    assert broker["argv"][: len(BROKER_PREFIX)] == BROKER_PREFIX
    assert broker["executable_digest"].startswith("sha256:")
    assert broker["argv_digest"].startswith("sha256:")

    runtime = Path("/run/user") / str(os.geteuid())
    bus = runtime / "bus"
    assert broker["runtime_dir"]["path"] == str(runtime)
    assert broker["runtime_dir"]["mode"] == stat.S_IMODE(runtime.lstat().st_mode)
    assert broker["bus"]["path"] == str(bus)
    assert broker["bus"]["address"] == f"unix:path={bus}"
    assert broker["bus"]["mode"] == stat.S_IMODE(bus.lstat().st_mode)
    assert str(hostile_runtime) not in json.dumps(report)
    assert str(hostile_root) not in json.dumps(report)
    assert trap_connected is False
    assert observer is not None
    _assert_real_probe(report, observer)


def test_gate5_login_scope_without_a_broker_refuses_instead_of_skipping(
    installed_launcher: None,
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: the outer delegated unit constructs a child root with only
    # memory+pids, then a nested user+mount namespace hides the derived D-Bus
    # runtime. Thus both insufficiency and broker unavailability are constructed.
    runtime = Path("/run/user") / str(os.geteuid())
    completed, _ = _run_in_delegated_unit(
        "qualify",
        *_qualify_arguments(),
        sandbox=(
            sandbox_helper,
            "controller-subset",
            "+memory +pids",
            "--",
            sandbox_helper,
            "mask-directory",
            runtime,
            tmp_path,
        ),
    )
    _refusal(completed, E_DELEGATION)
    assert not (ROOT / REPORT).exists()


def test_gate5_report_records_an_untestable_broker_when_existing_root_is_usable(
    installed_launcher: None,
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: systemd delegates first; only then a private mount hides
    # the derived runtime directory. Existing delegation succeeds, while broker
    # qualification is genuinely untestable and must be recorded as such.
    runtime = Path("/run/user") / str(os.geteuid())
    completed, _ = _run_in_delegated_unit(
        "qualify",
        *_qualify_arguments(),
        sandbox=(sandbox_helper, "mask-directory", runtime, tmp_path),
    )
    report = _assert_success_report(completed)
    assert report["delegation"]["source"] == "existing"
    assert report["delegation"]["broker"]["status"] == "untestable"
    assert report["delegation"]["broker"]["attempted"] is False


@pytest.mark.parametrize(
    "missing,present",
    [
        ("cpu", "+memory +pids"),
        ("memory", "+cpu +pids"),
        ("pids", "+cpu +memory"),
    ],
)
def test_gate6_each_required_controller_is_genuinely_absent(
    missing: str,
    present: str,
    sandbox_helper: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: in a delegated unit the harness leaves its unit root
    # process-empty, enables only `present`, creates a child cgroup, moves the
    # gated controller PID into it, and only then execs host-probe. Therefore
    # /proc/self/cgroup names a real root whose cgroup.controllers lacks exactly
    # `missing`; no caller path selects that root and no report field is edited.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "controller-subset", present),
    )
    refusal = _refusal(completed, E_FACT)
    detail = refusal["detail"].lower()
    assert re.search(rf"\b{re.escape(missing)}\b", detail)
    for other in REQUIRED_CONTROLLERS - {missing}:
        assert not re.search(rf"\b{re.escape(other)}\b", detail)


@pytest.mark.parametrize("namespace,flag", sorted(NAMESPACE_FLAGS.items()))
def test_gate6_each_namespace_probe_is_defeated_in_the_kernel(
    namespace: str,
    flag: int,
    sandbox_helper: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: after entering fresh user+mount namespaces, inherited
    # seccomp returns ENOSYS only for unshare() carrying the named CLONE_NEW* bit.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "block-namespace", hex(flag)),
    )
    refusal = _refusal(completed, E_FACT)
    detail = refusal["detail"].lower()
    assert re.search(rf"\b{re.escape(namespace)} namespace\b", detail)
    for other in set(NAMESPACE_FLAGS) - {namespace}:
        assert not re.search(rf"\b{re.escape(other)} namespace\b", detail)


@pytest.mark.parametrize(
    "fact,syscall_number",
    [
        ("landlock", SYS_LANDLOCK_CREATE_RULESET_X86_64),
        ("openat2", SYS_OPENAT2_X86_64),
    ],
)
def test_gate6_kernel_syscall_probe_is_defeated_for_real(
    fact: str,
    syscall_number: int,
    sandbox_helper: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: a fresh user+mount namespace inherits a narrow seccomp
    # filter returning ENOSYS for the actual x86_64 probe syscall. Landlock ABI
    # 8 cannot be downgraded to a weaker policy and openat2 cannot be inferred.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "block-syscall", str(syscall_number)),
    )
    refusal = _refusal(completed, E_FACT)
    assert fact in refusal["detail"].lower()


def test_gate6_seccomp_and_nnp_status_must_be_readable(
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: after entering fresh user+mount namespaces, an unreadable
    # bind-mounted file replaces /proc/self/status before exec. We do not install
    # seccomp here: doing that would itself set NNP and decorate this negative.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "mask-file", "/proc/self/status", tmp_path),
        direct_controller=True,
    )
    refusal = _refusal(completed, E_FACT)
    assert "seccomp" in refusal["detail"].lower() or "no_new_privs" in refusal["detail"].lower()


def test_gate6_cgroup_kill_is_genuinely_unavailable_at_the_probe_root(
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: inside a fresh user+mount namespace an inaccessible,
    # non-cgroup bind mount covers the live delegated root's cgroup.kill inode.
    # Controllers and cgroup.procs remain the real cgroup-v2 files.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "mask-cgroup-kill", tmp_path),
    )
    refusal = _refusal(completed, E_FACT)
    assert "cgroup.kill" in refusal["detail"].lower()


def test_gate6_bubblewrap_binary_is_genuinely_absent_from_the_mount_view(
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: the delegated service starts first; its child then enters
    # fresh user+mount namespaces and masks only the profile-pinned bwrap object.
    profile = json.loads((ROOT / PROFILE).read_bytes())
    bwrap_path = profile["helpers"]["bubblewrap"]["path"]
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "mask-file", bwrap_path, tmp_path),
    )
    refusal = _refusal(completed, E_FACT)
    assert "bwrap" in refusal["detail"].lower() or "bubblewrap" in refusal["detail"].lower()


def test_gate6_positive_host_probe_succeeds_on_the_qualified_host() -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    completed, _ = _run_in_delegated_unit("host-probe")
    if completed.returncode != 0:
        # The controller truthfully reporting an unqualified host is contract
        # behavior. Only this known hosted-runner signature is that absence.
        refusal = _refusal(completed, E_FACT)
        assert "map-user:13" in refusal["detail"]
        return
    assert completed.returncode == 0, _diagnostic(completed)
    facts = _json_stdout(completed)
    assert facts, "successful host-probe emitted no measured facts"


def test_gate8_wrong_architecture_refuses_without_a_partial_report(
    installed_launcher: None,
    sandbox_helper: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    completed = subprocess.run(
        [str(sandbox_helper), "linux32", "unused", "--", *_controller_argv(
            "qualify", *_qualify_arguments()
        )],
        cwd=ROOT,
        env=_controller_env(),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    _refusal(completed, E_ARCH)
    assert not (ROOT / REPORT).exists()


def test_gate8_unreadable_kernel_fact_refuses_without_a_partial_report(
    installed_launcher: None,
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    # Real mechanism: qualify begins in a real delegated unit, while a private
    # bind mount makes its own /proc/self/status unreadable before controller exec.
    completed, _ = _run_in_delegated_unit(
        "qualify",
        *_qualify_arguments(),
        sandbox=(sandbox_helper, "mask-file", "/proc/self/status", tmp_path),
        direct_controller=True,
    )
    _refusal(completed, E_FACT)
    assert not (ROOT / REPORT).exists()


@dataclass
class CleanupBlocker:
    """Plant a live nested cgroup after the real probe has a live member."""

    root: Path
    probe_pid: int | None = None
    probe_root: Path | None = None
    stop: threading.Event = field(default_factory=threading.Event)
    planted: Path | None = None
    sleeper: subprocess.Popen[str] | None = None
    thread: threading.Thread | None = None
    baseline: set[Path] = field(default_factory=set)
    created_paths: set[Path] = field(default_factory=set)
    thread_error: BaseException | None = None

    def start(self) -> None:
        self.baseline = {path for path in self.root.rglob("*") if path.is_dir()}
        self.sleeper = subprocess.Popen(
            ["/usr/bin/sleep", "180"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.thread = threading.Thread(target=self._plant, daemon=True)
        self.thread.start()

    def _plant(self) -> None:
        try:
            self._plant_observed()
        except BaseException as error:
            self.thread_error = error

    def _plant_observed(self) -> None:
        assert self.sleeper is not None
        while not self.stop.is_set():
            probe_pid = self.probe_pid
            probe_root = self.probe_root
            if probe_pid is None or probe_root is None:
                time.sleep(0.001)
                continue
            try:
                current = {path for path in probe_root.iterdir() if path.is_dir()}
            except (FileNotFoundError, PermissionError):
                continue
            for candidate in current - self.baseline:
                if candidate.name.endswith((".service", ".scope")):
                    continue
                try:
                    if str(probe_pid) not in (candidate / "cgroup.procs").read_text().split():
                        continue
                    blocker = candidate / (
                        f"acceptance-cleanup-blocker-{os.getpid()}-{uuid.uuid4().hex[:8]}"
                    )
                    blocker.mkdir()
                except (FileExistsError, FileNotFoundError, PermissionError):
                    continue
                self.created_paths.add(blocker)
                try:
                    (blocker / "cgroup.procs").write_text(f"{self.sleeper.pid}\n")
                except OSError as error:
                    cleanup_error: OSError | None = None
                    try:
                        blocker.rmdir()
                    except FileNotFoundError:
                        pass
                    except OSError as failure:
                        cleanup_error = failure
                    self.thread_error = AssertionError(
                        "created blocker cgroup but failed to enroll sleeper: "
                        f"write={error}; cleanup={cleanup_error}"
                    )
                    return
                self.planted = blocker
                return
            time.sleep(0.001)

    def observe_probe(self, probe_pid: int) -> None:
        try:
            cgroup = next(
                line.split("::", 1)[1]
                for line in Path(f"/proc/{probe_pid}/cgroup").read_text(encoding="ascii").splitlines()
                if "::" in line
            )
        except (FileNotFoundError, StopIteration) as error:
            raise AssertionError(f"cannot resolve cgroup for live delegated controller {probe_pid}") from error
        probe_root = Path("/sys/fs/cgroup") / cgroup.lstrip("/")
        self.baseline = {path for path in probe_root.iterdir() if path.is_dir()}
        self.probe_root = probe_root
        self.probe_pid = probe_pid

    def finish(self) -> None:
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=5)
            assert not self.thread.is_alive(), "cleanup blocker thread did not stop"
        if self.sleeper is not None:
            if self.sleeper.poll() is None:
                self.sleeper.send_signal(signal.SIGKILL)
            self.sleeper.wait(timeout=10)
        if self.created_paths:
            failures: list[str] = []
            cleanup_paths = {
                path for blocker in self.created_paths for path in (blocker, blocker.parent)
            }
            for path in sorted(cleanup_paths, key=lambda candidate: len(candidate.parts), reverse=True):
                try:
                    path.rmdir()
                except FileNotFoundError:
                    continue
                except OSError as error:
                    failures.append(f"{path}: {error}")
            surviving = [path for path in cleanup_paths if path.exists()]
            assert not surviving, (
                f"cleanup cgroups survived fixture teardown: {surviving}; "
                + "; ".join(failures)
            )
        if self.thread_error is not None:
            raise AssertionError("cleanup blocker worker failed") from self.thread_error


def test_gate8_cleanup_failure_refuses_and_test_removes_its_blocker(
    installed_launcher: None,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller("qualify", *_qualify_arguments())
        _refusal(completed, E_EXEC)
        return
    blocker = CleanupBlocker(_user_service_cgroup_root())
    try:
        blocker.start()
        completed, _ = _run_in_delegated_unit(
            "qualify", *_qualify_arguments(), on_unit_started=blocker.observe_probe
        )
        assert blocker.planted is not None, "did not rendezvous with the live probe cgroup"
        _refusal(completed, E_CLEANUP)
        assert not (ROOT / REPORT).exists()
    finally:
        blocker.finish()
