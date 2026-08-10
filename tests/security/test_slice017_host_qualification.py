"""Frozen acceptance tests for SLICE-017 host qualification.

These tests intentionally use the public controller process only.  The small C
harness below changes what the kernel exposes to that process; it never edits a
qualification result.  Imports of ``ranex.cli.host_confinement`` are also
deliberately absent so that the not-yet-implemented module is a normal red test,
not a collection error.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import stat
import subprocess
import threading
import time
import uuid
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROFILE = Path("governance/confinement/strict-local-host-v1.json")
MANIFEST = Path("governance/confinement/native-launcher-build-v1.json")
SOURCE = Path("native/ranex-worker-launcher/launcher.c")
BUILD_ARTIFACT = Path(".local/ranex/build/strict-local-v1/ranex-worker-launcher")
INSTALLED_ARTIFACT = Path(".local/ranex/libexec/strict-local-v1/ranex-worker-launcher")
REPORT = Path(".local/ranex/qualification/strict-local-v1.json")

CONTROLLER = [
    "uv",
    "run",
    "--frozen",
    "python",
    "-m",
    "ranex.cli.host_confinement",
]
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


def _controller_argv(subcommand: str, *arguments: str | Path) -> list[str]:
    return [*CONTROLLER, subcommand, *(str(argument) for argument in arguments)]


def _controller_env(overrides: Mapping[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = "src"
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


def _refusal(
    completed: subprocess.CompletedProcess[str], expected: str | set[str]
) -> dict[str, Any]:
    assert completed.returncode != 0, _diagnostic(completed)
    refusal = _json_stdout(completed)
    assert set(refusal) == {"refusal", "detail"}
    expected_codes = {expected} if isinstance(expected, str) else expected
    assert refusal["refusal"] in expected_codes
    assert isinstance(refusal["detail"], str) and refusal["detail"]
    return refusal


def _load_report() -> dict[str, Any]:
    value = json.loads((ROOT / REPORT).read_text(encoding="utf-8"))
    assert isinstance(value, dict)
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

    generated = [ROOT / BUILD_ARTIFACT, ROOT / INSTALLED_ARTIFACT, ROOT / REPORT]
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
        BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_unshare, 0, 3),
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
    return executable


@dataclass
class CgroupObservation:
    """Independent observation of newly-created cgroups and live members."""

    root: Path
    stop: threading.Event = field(default_factory=threading.Event)
    paths: set[Path] = field(default_factory=set)
    live_pids: dict[Path, set[int]] = field(default_factory=dict)
    _baseline: set[Path] = field(default_factory=set)
    _thread: threading.Thread | None = None

    def _directories(self) -> set[Path]:
        if not self.root.is_dir():
            return set()
        return {path for path in self.root.rglob("*") if path.is_dir()}

    def start(self) -> None:
        self._baseline = self._directories()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()

    def _watch(self) -> None:
        while not self.stop.is_set():
            for path in self._directories() - self._baseline:
                self.paths.add(path)
                try:
                    pids = {
                        int(value)
                        for value in (path / "cgroup.procs").read_text().split()
                        if (Path("/proc") / value).exists()
                    }
                except (FileNotFoundError, PermissionError, ValueError):
                    continue
                if pids:
                    self.live_pids.setdefault(path, set()).update(pids)
            time.sleep(0.001)

    def finish(self) -> None:
        self.stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)


def _user_service_cgroup_root() -> Path:
    uid = os.geteuid()
    return Path(f"/sys/fs/cgroup/user.slice/user-{uid}.slice/user@{uid}.service")


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


def _run_in_delegated_unit(
    subcommand: str,
    *arguments: str | Path,
    sandbox: Sequence[str | Path] = (),
    service_environment: Mapping[str, str] | None = None,
    observe: bool = False,
) -> tuple[subprocess.CompletedProcess[str], CgroupObservation | None]:
    unit = f"ranex-acceptance-{os.getpid()}-{uuid.uuid4().hex}.service"
    command = _controller_argv(subcommand, *arguments)
    if sandbox:
        command = [*(str(value) for value in sandbox), "--", *command]

    service_env = {"PYTHONPATH": "src", "PATH": os.environ["PATH"]}
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
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            env={**os.environ, **_derived_bus_environment()},
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    finally:
        if observer is not None:
            observer.finish()
        _stop_unit(unit)
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
    assert child_pid in observed.live_pids.get(path, set())
    assert not path.exists()


def _assert_success_report(completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    assert completed.returncode == 0, _diagnostic(completed)
    report = _load_report()
    assert report["qualified"] is True
    return report


def test_gate5_existing_delegation_runs_a_real_child_cgroup_probe(
    installed_launcher: None,
) -> None:
    REPORT.unlink(missing_ok=True)
    completed, observed = _run_in_delegated_unit(
        "qualify", *_qualify_arguments(), observe=True
    )
    report = _assert_success_report(completed)
    assert observed is not None
    assert report["delegation"]["source"] == "existing"
    _assert_real_probe(report, observed)


def test_gate5_login_scope_is_rejected_and_broker_runs_a_real_probe(
    installed_launcher: None,
    tmp_path: Path,
) -> None:
    REPORT.unlink(missing_ok=True)
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

    observer = CgroupObservation(_user_service_cgroup_root())
    observer.start()
    trap_connected = False
    try:
        completed = _run_controller(
            "qualify",
            *_qualify_arguments(),
            environment={
                "XDG_RUNTIME_DIR": str(hostile_runtime),
                "DBUS_SESSION_BUS_ADDRESS": f"unix:path={hostile_bus}",
                "RANEX_CGROUP_ROOT": str(hostile_root),
                "CGROUP_ROOT": str(hostile_root),
            },
        )
    finally:
        observer.finish()
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
    assert delegation["existing_root"]["controllers"] == ["memory", "pids"]
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
    _assert_real_probe(report, observer)


def test_gate5_login_scope_without_a_broker_refuses_instead_of_skipping(
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    # Real mechanism: a fresh user+mount namespace hides /run/user/<uid>, so the
    # measured login cgroup (memory+pids, no cpu) has no usable D-Bus broker.
    REPORT.unlink(missing_ok=True)
    runtime = Path("/run/user") / str(os.geteuid())
    completed = subprocess.run(
        [
            str(sandbox_helper),
            "mask-directory",
            str(runtime),
            str(tmp_path),
            "--",
            *_controller_argv("qualify", *_qualify_arguments()),
        ],
        cwd=ROOT,
        env=_controller_env(),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    _refusal(completed, E_DELEGATION)
    assert not (ROOT / REPORT).exists()


def test_gate5_report_records_an_untestable_broker_when_existing_root_is_usable(
    installed_launcher: None,
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
    # Real mechanism: systemd delegates first; only then a private mount hides
    # the derived runtime directory. Existing delegation succeeds, while broker
    # qualification is genuinely untestable and must be recorded as such.
    REPORT.unlink(missing_ok=True)
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
    # Real mechanism: in a delegated unit the harness leaves its unit root
    # process-empty, enables only `present`, creates a child cgroup, moves the
    # gated controller PID into it, and only then execs host-probe. Therefore
    # /proc/self/cgroup names a real root whose cgroup.controllers lacks exactly
    # `missing`; no caller path selects that root and no report field is edited.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "controller-subset", present),
    )
    refusal = _refusal(completed, {E_DELEGATION, E_FACT})
    assert missing in refusal["detail"].lower()


@pytest.mark.parametrize("namespace,flag", sorted(NAMESPACE_FLAGS.items()))
def test_gate6_each_namespace_probe_is_defeated_in_the_kernel(
    namespace: str,
    flag: int,
    sandbox_helper: Path,
) -> None:
    # Real mechanism: after entering fresh user+mount namespaces, inherited
    # seccomp returns ENOSYS only for unshare() carrying the named CLONE_NEW* bit.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "block-namespace", hex(flag)),
    )
    refusal = _refusal(completed, E_FACT)
    assert namespace in refusal["detail"].lower()


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
    # Real mechanism: after entering fresh user+mount namespaces, an unreadable
    # bind-mounted file replaces /proc/self/status before exec. We do not install
    # seccomp here: doing that would itself set NNP and decorate this negative.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "mask-file", "/proc/self/status", tmp_path),
    )
    refusal = _refusal(completed, E_FACT)
    assert "seccomp" in refusal["detail"].lower() or "no_new_privs" in refusal["detail"].lower()


def test_gate6_cgroup_kill_is_genuinely_unavailable_at_the_probe_root(
    sandbox_helper: Path,
    tmp_path: Path,
) -> None:
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
    # Real mechanism: the delegated service starts first; its child then enters
    # fresh user+mount namespaces and bind-mounts an empty directory on /usr/bin.
    # Thus /usr/bin/bwrap is genuinely absent, not deleted from produced JSON.
    completed, _ = _run_in_delegated_unit(
        "host-probe",
        sandbox=(sandbox_helper, "mask-directory", "/usr/bin", tmp_path),
    )
    refusal = _refusal(completed, E_FACT)
    assert "bwrap" in refusal["detail"].lower() or "bubblewrap" in refusal["detail"].lower()


def test_gate8_wrong_architecture_refuses_without_a_partial_report(
    installed_launcher: None,
    sandbox_helper: Path,
) -> None:
    REPORT.unlink(missing_ok=True)
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
    # Real mechanism: qualify begins in a real delegated unit, while a private
    # bind mount makes its own /proc/self/status unreadable before controller exec.
    REPORT.unlink(missing_ok=True)
    completed, _ = _run_in_delegated_unit(
        "qualify",
        *_qualify_arguments(),
        sandbox=(sandbox_helper, "mask-file", "/proc/self/status", tmp_path),
    )
    _refusal(completed, E_FACT)
    assert not (ROOT / REPORT).exists()


@dataclass
class CleanupBlocker:
    """Plant a live nested cgroup after the real probe has a live member."""

    root: Path
    stop: threading.Event = field(default_factory=threading.Event)
    planted: Path | None = None
    sleeper: subprocess.Popen[str] | None = None
    thread: threading.Thread | None = None
    baseline: set[Path] = field(default_factory=set)

    def start(self) -> None:
        self.baseline = {path for path in self.root.rglob("*") if path.is_dir()}
        self.sleeper = subprocess.Popen(
            ["/usr/bin/sleep", "180"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        self.thread = threading.Thread(target=self._plant, daemon=True)
        self.thread.start()

    def _plant(self) -> None:
        assert self.sleeper is not None
        while not self.stop.is_set():
            current = {path for path in self.root.rglob("*") if path.is_dir()}
            for candidate in current - self.baseline:
                if candidate.name.endswith((".service", ".scope")):
                    continue
                try:
                    if not (candidate / "cgroup.procs").read_text().split():
                        continue
                    blocker = candidate / "acceptance-cleanup-blocker"
                    blocker.mkdir()
                    (blocker / "cgroup.procs").write_text(f"{self.sleeper.pid}\n")
                except (FileExistsError, FileNotFoundError, PermissionError, OSError):
                    continue
                self.planted = blocker
                return
            time.sleep(0.001)

    def finish(self) -> None:
        self.stop.set()
        if self.thread is not None:
            self.thread.join(timeout=5)
        if self.sleeper is not None:
            self.sleeper.send_signal(signal.SIGKILL)
            self.sleeper.wait(timeout=10)
        if self.planted is not None:
            for path in (self.planted, self.planted.parent):
                try:
                    path.rmdir()
                except (FileNotFoundError, OSError):
                    pass


def test_gate8_cleanup_failure_refuses_and_test_removes_its_blocker(
    installed_launcher: None,
) -> None:
    REPORT.unlink(missing_ok=True)
    blocker = CleanupBlocker(_user_service_cgroup_root())
    blocker.start()
    try:
        completed, _ = _run_in_delegated_unit("qualify", *_qualify_arguments())
        assert blocker.planted is not None, "did not rendezvous with the live probe cgroup"
        _refusal(completed, E_CLEANUP)
        assert not (ROOT / REPORT).exists()
    finally:
        blocker.finish()
