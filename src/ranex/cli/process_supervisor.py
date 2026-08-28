"""Kill-safe ownership for non-confined governed commands.

The kernel cannot clean up after SIGKILL.  This module therefore execs one
minimal guardian before scratch allocation.  The guardian allocates and owns
the exact scratch root, and runs the command below bubblewrap's PID-namespace
init.  A lifeline EOF is the guardian's instruction to kill PID 1 directly,
drain it, and remove the root.
"""

from __future__ import annotations

import array
import ctypes
import errno
import json
import os
import resource
import select
import shutil
import signal
import socket
import stat
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Any, NoReturn, Self

from ranex.cli import subject as subject_module
from ranex.cli.subject import _materialisation_root, _remove_materialisation

_MESSAGE_LIMIT = 65_536
_DRAIN_TIMEOUT = 15.0
_BWRAP_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


class ProcessSupervisorError(ValueError):
    """The external lifecycle owner could not prove a safe result."""


@dataclass(frozen=True, slots=True)
class RawStatus:
    kind: str
    code: int

    @property
    def returncode(self) -> int:
        return self.code if self.kind == "exited" else 128 + self.code


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _send(
    endpoint: socket.socket,
    value: Mapping[str, Any],
    descriptors: Sequence[int] = (),
) -> None:
    data = _json_bytes(value)
    if len(data) > _MESSAGE_LIMIT:
        raise ProcessSupervisorError("lifecycle control message exceeds 65536 bytes")
    ancillary: list[tuple[int, int, bytes]] = []
    if descriptors:
        packed = array.array("i", descriptors)
        ancillary.append((socket.SOL_SOCKET, socket.SCM_RIGHTS, packed.tobytes()))
    written = endpoint.sendmsg([data], ancillary)
    if written != len(data):
        raise ProcessSupervisorError("lifecycle control message was truncated")


def _receive(endpoint: socket.socket) -> tuple[dict[str, Any], tuple[int, ...]]:
    descriptor_space = socket.CMSG_SPACE(8 * array.array("i").itemsize)
    data, ancillary, flags, _address = endpoint.recvmsg(
        _MESSAGE_LIMIT + 1,
        descriptor_space,
        getattr(socket, "MSG_CMSG_CLOEXEC", 0),
    )
    if not data:
        raise EOFError("lifecycle control channel closed")
    if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC) or len(data) > _MESSAGE_LIMIT:
        raise ProcessSupervisorError("lifecycle control message was truncated")
    descriptors: list[int] = []
    for level, kind, payload in ancillary:
        if level != socket.SOL_SOCKET or kind != socket.SCM_RIGHTS:
            raise ProcessSupervisorError("lifecycle control carried unknown ancillary data")
        packed = array.array("i")
        packed.frombytes(payload[: len(payload) - (len(payload) % packed.itemsize)])
        descriptors.extend(packed)
    try:
        for descriptor in descriptors:
            os.set_inheritable(descriptor, False)
    except OSError as exc:
        for descriptor in descriptors:
            os.close(descriptor)
        raise ProcessSupervisorError(
            "lifecycle control descriptor could not be made close-on-exec"
        ) from exc
    try:
        decoded = json.loads(data)
    except json.JSONDecodeError as exc:
        for descriptor in descriptors:
            os.close(descriptor)
        raise ProcessSupervisorError("lifecycle control message is invalid JSON") from exc
    if not isinstance(decoded, dict) or not all(isinstance(key, str) for key in decoded):
        for descriptor in descriptors:
            os.close(descriptor)
        raise ProcessSupervisorError("lifecycle control message is not an object")
    return decoded, tuple(descriptors)


def _libc() -> ctypes.CDLL:
    library = ctypes.CDLL(None, use_errno=True)
    library.pidfd_open.argtypes = (ctypes.c_int, ctypes.c_uint)
    library.pidfd_open.restype = ctypes.c_int
    library.pidfd_send_signal.argtypes = (
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint,
    )
    library.pidfd_send_signal.restype = ctypes.c_int
    return library


def _pidfd_open(pid: int) -> int:
    descriptor = _libc().pidfd_open(pid, 0)
    if descriptor < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), pid)
    os.set_inheritable(descriptor, False)
    return int(descriptor)


def _pidfd_kill(descriptor: int) -> None:
    if _libc().pidfd_send_signal(descriptor, signal.SIGKILL, None, 0) == 0:
        return
    error = ctypes.get_errno()
    if error != errno.ESRCH:
        raise OSError(error, os.strerror(error))


def _wait_pidfd(descriptor: int, timeout: float = _DRAIN_TIMEOUT) -> None:
    readable, _writable, _exceptional = select.select([descriptor], [], [], timeout)
    if not readable:
        raise ProcessSupervisorError("PID-namespace init did not drain after SIGKILL")


def _validate_namespace_init(descriptor: int, expected_pid: int) -> None:
    """Bind the held pidfd to the host PID and namespace PID 1 identities."""

    try:
        rows = {
            key: value.strip().split()
            for key, value in (
                line.split(":", 1)
                for line in Path(f"/proc/self/fdinfo/{descriptor}").read_text(
                    encoding="ascii"
                ).splitlines()
                if ":" in line
            )
        }
        pid = rows.get("Pid", [])
        namespace_pids = rows.get("NSpid", [])
        valid = (
            pid == [str(expected_pid)]
            and len(namespace_pids) >= 2
            and namespace_pids[0] == str(expected_pid)
            and namespace_pids[-1] == "1"
        )
    except (OSError, UnicodeError, ValueError):
        valid = False
    if not valid:
        raise ProcessSupervisorError(
            "bubblewrap child identity is not the held PID-namespace init"
        )


def _close_except(allowed: set[int]) -> None:
    try:
        names = tuple(Path("/proc/self/fd").iterdir())
    except OSError:
        maximum = min(resource.getrlimit(resource.RLIMIT_NOFILE)[0], 65_536)
        names = tuple(Path(str(value)) for value in range(3, int(maximum)))
    for name in names:
        try:
            descriptor = int(name.name)
        except ValueError:
            continue
        if descriptor > 2 and descriptor not in allowed:
            try:
                os.close(descriptor)
            except OSError:
                pass


def _open_regular(path: Path, *, root_owned: bool) -> int:
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        facts = os.fstat(descriptor)
        if not stat.S_ISREG(facts.st_mode):
            raise ProcessSupervisorError(f"lifecycle executable is not regular: {path}")
        if root_owned and facts.st_uid != 0:
            raise ProcessSupervisorError(f"bubblewrap is not owned by root: {path}")
        if root_owned and facts.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
            raise ProcessSupervisorError(f"lifecycle executable is group/other writable: {path}")
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


_PROBE = """
import json, os
with open('/dev/null', 'wb', buffering=0) as sink:
    sink.write(b'')
facts = {
    'cwd': os.getcwd(),
    'pid': os.getpid(),
    'proc_pid': int(open('/proc/self/stat').read().split()[0]),
}
print(json.dumps(facts, sort_keys=True, separators=(',', ':')))
""".strip()


def _probe_bubblewrap(bwrap: int, python: int, cwd: Path) -> None:
    argv = [
        "bwrap",
        "--bind",
        "/",
        "/",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--unshare-pid",
        "--die-with-parent",
        "--chdir",
        str(cwd),
        "--",
        f"/proc/self/fd/{python}",
        "-I",
        "-S",
        "-c",
        _PROBE,
    ]
    try:
        completed = subprocess.run(
            argv,
            executable=f"/proc/self/fd/{bwrap}",
            pass_fds=(bwrap, python),
            capture_output=True,
            text=True,
            check=False,
            env={"HOME": "/", "LANG": "C.UTF-8", "PATH": "/usr/bin:/bin"},
        )
    except OSError as exc:
        raise ProcessSupervisorError(f"bubblewrap lifecycle probe failed: {exc}") from exc
    expected = {"cwd": str(cwd), "pid": 2, "proc_pid": 2}
    try:
        observed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ProcessSupervisorError(
            f"bubblewrap lifecycle probe returned invalid JSON: {completed.stderr.strip()}"
        ) from exc
    if completed.returncode != 0 or observed != expected:
        raise ProcessSupervisorError(
            "bubblewrap cannot provide the required root/dev/proc/PID lifecycle view: "
            f"exit={completed.returncode} observed={observed!r} stderr={completed.stderr.strip()!r}"
        )


_RELAY = r"""
import json, os, signal, sys

gate, raw, executable, config_fd = map(int, sys.argv[1:5])
config_bytes = bytearray()
while True:
    block = os.read(config_fd, 8192)
    if not block:
        break
    config_bytes.extend(block)
    if len(config_bytes) > 65536:
        os._exit(124)
os.close(config_fd)
try:
    config = json.loads(config_bytes)
except Exception:
    os._exit(124)
release = bytearray()
while len(release) < 2:
    block = os.read(gate, 2 - len(release))
    if not block:
        break
    release.extend(block)
os.close(gate)
if bytes(release) != b'1':
    os.write(raw, b'{"code":125,"kind":"exited"}\n')
    os.close(raw)
    os._exit(125)
error_read, error_write = os.pipe2(os.O_CLOEXEC)
child = os.fork()
if child == 0:
    os.close(error_read)
    os.close(raw)
    try:
        os.chdir(config['cwd'])
        allowed = {0, 1, 2, executable, error_write}
        for entry in tuple(os.listdir('/proc/self/fd')):
            try:
                descriptor = int(entry)
            except ValueError:
                continue
            if descriptor > 2 and descriptor not in allowed:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        os.execve('/proc/self/fd/%d' % executable, config['argv'], config['environment'])
    except OSError as exc:
        try:
            os.write(error_write, str(exc.errno or 5).encode())
        finally:
            os._exit(127)
os.close(error_write)
_waited, status = os.waitpid(child, 0)
error = os.read(error_read, 32)
os.close(error_read)
if error:
    record = {'code': int(error), 'kind': 'exec_error'}
    exit_code = 127
elif os.WIFEXITED(status):
    record = {'code': os.WEXITSTATUS(status), 'kind': 'exited'}
    exit_code = record['code']
elif os.WIFSIGNALED(status):
    record = {'code': os.WTERMSIG(status), 'kind': 'signalled'}
    exit_code = 128 + record['code']
else:
    record = {'code': 255, 'kind': 'exited'}
    exit_code = 255
payload = json.dumps(record, sort_keys=True, separators=(',', ':')).encode() + b'\n'
view = memoryview(payload)
while view:
    view = view[os.write(raw, view):]
os.close(raw)
os._exit(exit_code)
""".strip()


_GUARDIAN_BOOTSTRAP = r"""
import os, socket, sys, types

endpoint, lifeline, bwrap, python, subject_source, supervisor_source = map(
    int, sys.argv[1:7]
)
ranex = types.ModuleType('ranex')
ranex.__path__ = []
cli = types.ModuleType('ranex.cli')
cli.__path__ = []
sys.modules['ranex'] = ranex
sys.modules['ranex.cli'] = cli

def load_exact(name, descriptor, filename):
    source = bytearray()
    while True:
        block = os.read(descriptor, 8192)
        if not block:
            break
        source.extend(block)
    os.close(descriptor)
    module = types.ModuleType(name)
    module.__file__ = filename
    module.__package__ = name.rpartition('.')[0]
    sys.modules[name] = module
    exec(compile(bytes(source), filename, 'exec'), module.__dict__)
    return module

load_exact('ranex.cli.subject', subject_source, 'ranex/cli/subject.py')
supervisor = load_exact(
    'ranex.cli.process_supervisor', supervisor_source,
    'ranex/cli/process_supervisor.py'
)
supervisor._guardian(socket.socket(fileno=endpoint), lifeline, bwrap, python)
""".strip()


def _lifeline_closed(descriptor: int) -> bool:
    try:
        return os.read(descriptor, 1) == b""
    except BlockingIOError:
        return False


def _kill_owned(pidfd: int | None, process_group: int | None) -> None:
    if pidfd is not None:
        try:
            _pidfd_kill(pidfd)
        except OSError:
            pass
    if process_group is not None:
        try:
            os.killpg(process_group, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _read_first_status(
    descriptor: int, lifeline: int, process_group: int
) -> tuple[dict[str, Any], bytes]:
    data = bytearray()
    while b"\n" not in data:
        readable, _writable, _exceptional = select.select(
            [descriptor, lifeline], [], [], _DRAIN_TIMEOUT
        )
        if lifeline in readable and _lifeline_closed(lifeline):
            _kill_owned(None, process_group)
            raise EOFError("kernel died before PID-1 identity transfer")
        if descriptor not in readable:
            raise ProcessSupervisorError("bubblewrap did not report PID-1 identity")
        block = os.read(descriptor, 8192)
        if not block:
            raise ProcessSupervisorError("bubblewrap closed before PID-1 identity")
        data.extend(block)
        if len(data) > _MESSAGE_LIMIT:
            raise ProcessSupervisorError("bubblewrap status exceeded 65536 bytes")
    line, remainder = bytes(data).split(b"\n", 1)
    try:
        value = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ProcessSupervisorError("bubblewrap PID-1 identity is invalid JSON") from exc
    if not isinstance(value, dict):
        raise ProcessSupervisorError("bubblewrap PID-1 identity is not an object")
    return value, remainder


def _parse_raw(data: bytes) -> RawStatus:
    if not data.endswith(b"\n") or data.count(b"\n") != 1 or len(data) > 256:
        raise ProcessSupervisorError("raw command status is absent, duplicated, or malformed")
    try:
        value = json.loads(data)
    except json.JSONDecodeError as exc:
        raise ProcessSupervisorError("raw command status is invalid JSON") from exc
    if not isinstance(value, dict) or set(value) != {"code", "kind"}:
        raise ProcessSupervisorError("raw command status has the wrong fields")
    kind, code = value["kind"], value["code"]
    if kind not in {"exited", "signalled", "exec_error"} or not isinstance(code, int):
        raise ProcessSupervisorError("raw command status has invalid values")
    if code < 0 or code > 255 or (kind == "signalled" and not 0 < code < signal.NSIG):
        raise ProcessSupervisorError("raw command status code is out of range")
    return RawStatus(kind, code)


def bubblewrap_arguments(
    *,
    block: int,
    status: int,
    root: Path,
    cwd: Path,
    python: int,
    gate: int,
    raw: int,
    executable: int,
    config: int,
    deny_network: bool,
) -> list[str]:
    """Return the one reviewed lifecycle argv used by the real guardian."""

    return [
        "bwrap",
        "--bind",
        "/",
        "/",
        "--bind",
        str(root),
        str(root),
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--unshare-pid",
        "--die-with-parent",
        *(["--unshare-net"] if deny_network else []),
        "--block-fd",
        str(block),
        "--json-status-fd",
        str(status),
        "--chdir",
        str(cwd),
        "--",
        f"/proc/self/fd/{python}",
        "-I",
        "-S",
        "-c",
        _RELAY,
        str(gate),
        str(raw),
        str(executable),
        str(config),
    ]


def _guardian_execute(
    endpoint: socket.socket,
    lifeline: int,
    bwrap: int,
    python: int,
    message: Mapping[str, Any],
    descriptors: tuple[int, ...],
    root: Path,
) -> bool:
    if len(descriptors) != 2:
        raise ProcessSupervisorError("RUN requires executable and start-gate descriptors")
    executable, gate = descriptors
    block_read, block_write = os.pipe2(os.O_CLOEXEC)
    status_read, status_write = os.pipe2(os.O_CLOEXEC)
    raw_read, raw_write = os.pipe2(os.O_CLOEXEC)
    config_read, config_write = os.pipe2(os.O_CLOEXEC)
    process: subprocess.Popen[bytes] | None = None
    pidfd: int | None = None
    try:
        config = {
            "argv": message.get("argv"),
            "cwd": message.get("cwd"),
            "deny_network": message.get("deny_network"),
            "environment": message.get("environment"),
        }
        config_data = _json_bytes(config)
        if len(config_data) > _MESSAGE_LIMIT:
            raise ProcessSupervisorError("relay configuration exceeds 65536 bytes")
        os.write(config_write, config_data)
        os.close(config_write)
        config_write = -1
        cwd = message.get("cwd")
        if not isinstance(cwd, str):
            raise ProcessSupervisorError("RUN cwd is invalid")
        argv = bubblewrap_arguments(
            block=block_read,
            status=status_write,
            root=root,
            cwd=Path(cwd),
            python=python,
            gate=gate,
            raw=raw_write,
            executable=executable,
            config=config_read,
            deny_network=message.get("deny_network") is True,
        )
        process = subprocess.Popen(
            argv,
            executable=f"/proc/self/fd/{bwrap}",
            pass_fds=(
                bwrap,
                python,
                block_read,
                status_write,
                gate,
                raw_write,
                executable,
                config_read,
            ),
            close_fds=True,
            env={"HOME": "/", "LANG": "C.UTF-8", "PATH": "/usr/bin:/bin"},
            process_group=0,
        )
        for descriptor in (block_read, status_write, gate, raw_write, executable, config_read):
            os.close(descriptor)
        block_read = status_write = gate = raw_write = executable = config_read = -1
        identity, status_data = _read_first_status(status_read, lifeline, process.pid)
        expected_identity = {"child-pid", "mnt-namespace", "pid-namespace"}
        if message.get("deny_network") is True:
            expected_identity.add("net-namespace")
        if set(identity) != expected_identity:
            raise ProcessSupervisorError("bubblewrap PID-1 identity has the wrong fields")
        child_pid = identity.get("child-pid")
        if not isinstance(child_pid, int) or child_pid <= 0:
            raise ProcessSupervisorError("bubblewrap PID-1 identity has an invalid PID")
        pidfd = _pidfd_open(child_pid)
        _validate_namespace_init(pidfd, child_pid)
        _send(
            endpoint,
            {"bwrap_pid": process.pid, "kind": "IDENTITY", "pid": child_pid},
            (pidfd,),
        )
        while True:
            readable, _writable, _exceptional = select.select(
                [endpoint, lifeline], [], [], _DRAIN_TIMEOUT
            )
            if lifeline in readable and _lifeline_closed(lifeline):
                _kill_owned(pidfd, process.pid)
                _wait_pidfd(pidfd)
                process.wait(timeout=_DRAIN_TIMEOUT)
                _remove_materialisation(root)
                return False
            if endpoint in readable:
                acknowledgement, received = _receive(endpoint)
                for descriptor in received:
                    os.close(descriptor)
                if acknowledgement != {"kind": "ACK"}:
                    raise ProcessSupervisorError("kernel did not ACK PID-1 identity")
                break
        os.write(block_write, b"1")
        os.close(block_write)
        block_write = -1

        raw_data = bytearray()
        status_buffer = bytearray(status_data)
        raw_open = status_open = True
        pid_drained = False
        while process.poll() is None or raw_open or status_open or not pid_drained:
            watched: list[Any] = [lifeline, endpoint]
            if raw_open:
                watched.append(raw_read)
            if status_open:
                watched.append(status_read)
            if not pid_drained:
                watched.append(pidfd)
            readable, _writable, _exceptional = select.select(watched, [], [], 0.1)
            if lifeline in readable and _lifeline_closed(lifeline):
                _kill_owned(pidfd, process.pid)
                _wait_pidfd(pidfd)
                process.wait(timeout=_DRAIN_TIMEOUT)
                _remove_materialisation(root)
                return False
            if endpoint in readable:
                request, received = _receive(endpoint)
                for descriptor in received:
                    os.close(descriptor)
                if request == {"kind": "ABORT"}:
                    _kill_owned(pidfd, process.pid)
                    _wait_pidfd(pidfd)
                    process.wait(timeout=_DRAIN_TIMEOUT)
                    _send(endpoint, {"kind": "ABORTED"})
                    return True
                raise ProcessSupervisorError("unexpected control message during command")
            if raw_open and raw_read in readable:
                block = os.read(raw_read, 8192)
                if block:
                    raw_data.extend(block)
                    if len(raw_data) > 256:
                        raise ProcessSupervisorError("raw command status exceeded its bound")
                else:
                    raw_open = False
            if status_open and status_read in readable:
                block = os.read(status_read, 8192)
                if block:
                    status_buffer.extend(block)
                    if len(status_buffer) > _MESSAGE_LIMIT:
                        raise ProcessSupervisorError("bubblewrap status exceeded its bound")
                else:
                    status_open = False
            if pidfd in readable:
                pid_drained = True
        returncode = process.wait(timeout=_DRAIN_TIMEOUT)
        raw = _parse_raw(bytes(raw_data))
        if raw.kind == "exec_error":
            raise ProcessSupervisorError(f"cannot execute governed command: errno {raw.code}")
        if returncode != raw.returncode:
            raise ProcessSupervisorError(
                f"bubblewrap exit {returncode} disagrees with raw command status {raw.returncode}"
            )
        documents = [line for line in bytes(status_buffer).splitlines() if line]
        if len(documents) != 1:
            raise ProcessSupervisorError("bubblewrap emitted an invalid exit-status sequence")
        try:
            exit_document = json.loads(documents[0])
        except json.JSONDecodeError as exc:
            raise ProcessSupervisorError("bubblewrap exit status is invalid JSON") from exc
        if exit_document != {"exit-code": raw.returncode}:
            raise ProcessSupervisorError("bubblewrap exit status disagrees with raw status")
        _send(
            endpoint,
            {"code": raw.code, "kind": "RESULT", "status_kind": raw.kind},
        )
        return True
    finally:
        for descriptor in (
            executable,
            gate,
            block_read,
            block_write,
            status_read,
            status_write,
            raw_read,
            raw_write,
            config_read,
            config_write,
        ):
            if descriptor >= 0:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
        if process is not None and process.poll() is None:
            _kill_owned(pidfd, process.pid)
            if pidfd is not None:
                try:
                    _wait_pidfd(pidfd)
                except ProcessSupervisorError:
                    pass
            try:
                process.wait(timeout=_DRAIN_TIMEOUT)
            except subprocess.TimeoutExpired:
                pass
        if pidfd is not None:
            os.close(pidfd)


def _guardian(
    endpoint: socket.socket,
    lifeline: int,
    bwrap: int,
    python: int,
) -> NoReturn:
    root: Path | None = None
    try:
        os.set_blocking(lifeline, False)
        _close_except({endpoint.fileno(), lifeline, bwrap, python})
        while True:
            readable, _writable, _exceptional = select.select(
                [endpoint, lifeline], [], [], None
            )
            if lifeline in readable and _lifeline_closed(lifeline):
                if root is not None and root.exists():
                    _remove_materialisation(root)
                os._exit(0)
            if endpoint not in readable:
                continue
            message, descriptors = _receive(endpoint)
            kind = message.get("kind")
            if kind == "ALLOC" and root is None and not descriptors:
                repository = message.get("repository")
                environment = message.get("environment")
                if (
                    not isinstance(repository, str)
                    or not isinstance(environment, dict)
                    or not all(
                        isinstance(name, str) and isinstance(value, str)
                        for name, value in environment.items()
                    )
                ):
                    raise ProcessSupervisorError("ALLOC repository is invalid")
                root = _materialisation_root(Path(repository), environment=environment)
                _send(endpoint, {"kind": "ROOT", "path": str(root)})
            elif kind == "RUN" and root is not None:
                if not _guardian_execute(
                    endpoint, lifeline, bwrap, python, message, descriptors, root
                ):
                    os._exit(0)
            elif kind == "CLEANUP" and root is not None and not descriptors:
                if root.exists():
                    _remove_materialisation(root)
                _send(endpoint, {"kind": "CLEANED"})
                os._exit(0)
            else:
                for descriptor in descriptors:
                    os.close(descriptor)
                raise ProcessSupervisorError("invalid lifecycle protocol transition")
    except BaseException as exc:
        try:
            _send(endpoint, {"detail": str(exc), "kind": "ERROR"})
        except BaseException:
            pass
        if root is not None and root.exists():
            try:
                _remove_materialisation(root)
            except BaseException:
                pass
        os._exit(126)


class KillSafeSupervisor:
    """Kernel-side handle to the external lifecycle guardian."""

    def __init__(self, repository: Path) -> None:
        self._repository = repository.resolve()
        self._control: socket.socket | None = None
        self._lifeline = -1
        self._guardian_pid = -1
        self._guardian_pidfd = -1
        self._guardian_process: subprocess.Popen[bytes] | None = None
        self._pidfd = -1
        self._process_group: int | None = None
        self._root: Path | None = None
        self._last_raw_status: RawStatus | None = None
        self._finished = False

    @property
    def last_raw_status(self) -> RawStatus | None:
        return self._last_raw_status

    def __enter__(self) -> Self:
        from ranex.foundation.dynamic_runtime import seal_runtime_bytes

        resolved_bwrap = shutil.which("bwrap", path=_BWRAP_PATH)
        if resolved_bwrap is None:
            raise ProcessSupervisorError(
                "bubblewrap is required for kill-safe non-confined execution"
            )
        bwrap = _open_regular(Path(resolved_bwrap).resolve(), root_owned=True)
        python = _open_regular(Path(sys.executable).resolve(), root_owned=False)
        subject_source = seal_runtime_bytes(
            Path(subject_module.__file__).resolve().read_bytes(), kind="data", mode=0o400
        ).descriptor
        supervisor_source = seal_runtime_bytes(
            Path(__file__).resolve().read_bytes(), kind="data", mode=0o400
        ).descriptor
        parent: socket.socket | None = None
        child: socket.socket | None = None
        lifeline_read = lifeline_write = -1
        guardian: subprocess.Popen[bytes] | None = None
        try:
            _probe_bubblewrap(bwrap, python, self._repository)
            parent, child = socket.socketpair(
                socket.AF_UNIX, socket.SOCK_SEQPACKET | socket.SOCK_CLOEXEC
            )
            lifeline_read, lifeline_write = os.pipe2(os.O_CLOEXEC)
            guardian = subprocess.Popen(
                [
                    "python",
                    "-I",
                    "-S",
                    "-c",
                    _GUARDIAN_BOOTSTRAP,
                    str(child.fileno()),
                    str(lifeline_read),
                    str(bwrap),
                    str(python),
                    str(subject_source),
                    str(supervisor_source),
                ],
                executable=f"/proc/self/fd/{python}",
                pass_fds=(
                    child.fileno(),
                    lifeline_read,
                    bwrap,
                    python,
                    subject_source,
                    supervisor_source,
                ),
                close_fds=True,
                env={"HOME": "/", "LANG": "C.UTF-8", "PATH": "/usr/bin:/bin"},
                start_new_session=True,
            )
            child.close()
            child = None
            os.close(lifeline_read)
            lifeline_read = -1
            for descriptor in (bwrap, python, subject_source, supervisor_source):
                os.close(descriptor)
            bwrap = python = subject_source = supervisor_source = -1
            self._control = parent
            parent = None
            self._lifeline = lifeline_write
            lifeline_write = -1
            self._guardian_process = guardian
            self._guardian_pid = guardian.pid
            self._guardian_pidfd = _pidfd_open(guardian.pid)
            return self
        except BaseException:
            if guardian is not None and guardian.poll() is None:
                guardian.kill()
                guardian.wait()
            if parent is not None:
                parent.close()
            if child is not None:
                child.close()
            for descriptor in (
                bwrap,
                python,
                subject_source,
                supervisor_source,
                lifeline_read,
                lifeline_write,
            ):
                if descriptor < 0:
                    continue
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            raise

    def allocate_root(self, repository_root: Path) -> Path:
        if self._control is None or repository_root.resolve() != self._repository:
            raise ProcessSupervisorError("guardian repository identity changed")
        environment = {
            name: value
            for name in subject_module._NESTED_ENVIRONMENT_KEYS
            if (value := os.environ.get(name)) is not None
        }
        _send(
            self._control,
            {
                "environment": environment,
                "kind": "ALLOC",
                "repository": str(self._repository),
            },
        )
        response, descriptors = self._receive_or_fallback()
        for descriptor in descriptors:
            os.close(descriptor)
        path = response.get("path")
        if response.get("kind") != "ROOT" or not isinstance(path, str):
            self._raise_response(response)
        root = Path(path).resolve()
        if not root.name.startswith("ranex-subject-") or root.parent not in {
            Path("/tmp"),
            Path("/var/tmp"),
        }:
            raise ProcessSupervisorError("guardian returned an invalid materialisation root")
        self._root = root
        return root

    def run(
        self,
        command: Sequence[str],
        executable: int,
        *,
        cwd: Path,
        environment: Mapping[str, str],
        deny_network: bool,
    ) -> subprocess.CompletedProcess[str]:
        if self._control is None or self._root is None:
            raise ProcessSupervisorError("guardian has no allocated root")
        gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
        try:
            _send(
                self._control,
                {
                    "argv": list(command),
                    "cwd": str(cwd),
                    "deny_network": deny_network,
                    "environment": dict(environment),
                    "kind": "RUN",
                },
                (executable, gate_read),
            )
        finally:
            os.close(gate_read)
        try:
            identity, descriptors = self._receive_or_fallback()
            if identity.get("kind") != "IDENTITY" or len(descriptors) != 1:
                for descriptor in descriptors:
                    os.close(descriptor)
                self._raise_response(identity)
            pid = identity.get("pid")
            process_group = identity.get("bwrap_pid")
            if not isinstance(pid, int) or not isinstance(process_group, int):
                os.close(descriptors[0])
                raise ProcessSupervisorError("guardian returned invalid process identity")
            self._pidfd = descriptors[0]
            self._process_group = process_group
            _send(self._control, {"kind": "ACK"})
            os.write(gate_write, b"1")
        finally:
            os.close(gate_write)
        response, descriptors = self._receive_or_fallback()
        for descriptor in descriptors:
            os.close(descriptor)
        if response.get("kind") != "RESULT":
            self._raise_response(response)
        kind, code = response.get("status_kind"), response.get("code")
        if kind not in {"exited", "signalled"} or not isinstance(code, int):
            raise ProcessSupervisorError("guardian returned invalid raw status")
        raw = RawStatus(kind, code)
        self._last_raw_status = raw
        return subprocess.CompletedProcess(list(command), raw.returncode)

    def _receive_or_fallback(self) -> tuple[dict[str, Any], tuple[int, ...]]:
        assert self._control is not None
        try:
            return _receive(self._control)
        except (EOFError, OSError):
            self._fallback()
            raise ProcessSupervisorError(
                "lifecycle guardian died before completion"
            ) from None

    @staticmethod
    def _raise_response(response: Mapping[str, Any]) -> NoReturn:
        detail = response.get("detail")
        if response.get("kind") == "ERROR" and isinstance(detail, str):
            raise ProcessSupervisorError(f"lifecycle guardian refused: {detail}")
        raise ProcessSupervisorError("lifecycle guardian returned an invalid response")

    def _fallback(self) -> None:
        if self._pidfd >= 0:
            _kill_owned(self._pidfd, self._process_group)
            _wait_pidfd(self._pidfd)
        elif self._process_group is not None:
            _kill_owned(None, self._process_group)
        if self._root is not None and self._root.exists():
            _remove_materialisation(self._root)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        del exc, traceback
        active_failure = exc_type is not None
        if self._finished:
            return
        self._finished = True
        try:
            if self._control is not None:
                try:
                    _send(self._control, {"kind": "CLEANUP"})
                    response, descriptors = self._receive_or_fallback()
                    for descriptor in descriptors:
                        os.close(descriptor)
                    if response != {"kind": "CLEANED"}:
                        self._raise_response(response)
                except BaseException:
                    try:
                        self._fallback()
                    except BaseException:
                        if not active_failure:
                            raise
                    if not active_failure:
                        raise
        finally:
            if self._lifeline >= 0:
                os.close(self._lifeline)
                self._lifeline = -1
            if self._control is not None:
                self._control.close()
                self._control = None
            if self._guardian_pid > 0:
                returncode = (
                    self._guardian_process.wait()
                    if self._guardian_process is not None
                    else 0
                )
                if returncode != 0:
                    try:
                        self._fallback()
                    except BaseException:
                        if not active_failure:
                            raise
                    if not active_failure:
                        raise ProcessSupervisorError("lifecycle guardian exited abnormally")
                self._guardian_process = None
            for descriptor_name in ("_guardian_pidfd", "_pidfd"):
                descriptor = getattr(self, descriptor_name)
                if descriptor >= 0:
                    os.close(descriptor)
                    setattr(self, descriptor_name, -1)
