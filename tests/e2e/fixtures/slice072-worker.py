"""Frozen governed worker for SLICE-072's real kernel observations."""

from __future__ import annotations

import ctypes
import json
import mmap
import os
import sys
from pathlib import Path

RUNTIME = Path("/ranex/runtime")
INPUT = Path("/ranex/input")
OUTPUT = Path("/ranex/output")
SCRATCH = Path("/ranex/scratch")
SUBJECT = Path("/ranex/subject")


def denied_dlopen(path: Path) -> str:
    try:
        ctypes.CDLL(str(path))
    except OSError as exc:
        return "denied" if "failed to map segment" in str(exc) else f"wrong:{exc}"
    return "allowed"


def denied_mmap_exec(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
    try:
        try:
            mapped = mmap.mmap(
                descriptor,
                0,
                flags=mmap.MAP_PRIVATE,
                prot=mmap.PROT_READ | mmap.PROT_EXEC,
            )
        except OSError as exc:
            return os.strerror(exc.errno) if exc.errno is not None else "wrong"
        except ValueError:
            return "wrong:empty"
        mapped.close()
        return "allowed"
    finally:
        os.close(descriptor)


def denied_exec(path: Path, *, by_fd: bool) -> str:
    child = os.fork()
    if child == 0:
        try:
            if by_fd:
                descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
                argv = (ctypes.c_char_p * 2)(str(path).encode(), None)
                environment = (ctypes.c_char_p * 1)(None)
                result = ctypes.CDLL(None, use_errno=True).syscall(
                    322,
                    descriptor,
                    ctypes.c_char_p(b""),
                    argv,
                    environment,
                    0x1000,
                )
                if result != 0:
                    os._exit(ctypes.get_errno())
                os._exit(126)
            os.execve(path, [str(path)], {"LC_ALL": "C", "TZ": "UTC"})
        except OSError as exc:
            os._exit(exc.errno or 125)
    _pid, status = os.waitpid(child, 0)
    code = os.waitstatus_to_exitcode(status)
    if code in (13, 1):
        return os.strerror(code)
    return f"wrong:{code}"


def denied_explicit_loader(path: Path, label: str) -> str:
    loader = RUNTIME / "loader/ld-linux-x86-64.so.2"
    error_path = SCRATCH / f"loader-{label}.stderr"
    child = os.fork()
    if child == 0:
        descriptor = os.open(error_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        os.dup2(descriptor, 2)
        os.close(descriptor)
        os.execve(loader, [str(loader), str(path)], {"LC_ALL": "C", "TZ": "UTC"})
    _pid, status = os.waitpid(child, 0)
    detail = error_path.read_text(encoding="utf-8")
    if os.waitstatus_to_exitcode(status) != 0 and "failed to map segment" in detail:
        return "denied"
    return f"wrong:{os.waitstatus_to_exitcode(status)}:{detail}"


def probe(shared: Path, executable: Path, label: str) -> dict[str, str]:
    return {
        "dlopen": denied_dlopen(shared),
        "execve": denied_exec(executable, by_fd=False),
        "execveat": denied_exec(executable, by_fd=True),
        "explicit_loader": denied_explicit_loader(executable, label),
        "mmap_exec": denied_mmap_exec(shared),
    }


def nested_runtime() -> str:
    marker = SCRATCH / "nested.txt"
    loader = RUNTIME / "loader/ld-linux-x86-64.so.2"
    python = RUNTIME / "bin/python3.12"
    child = os.fork()
    if child == 0:
        argv = [
            str(loader), "--inhibit-cache", "--glibc-hwcaps-mask", "",
            "--library-path", str(RUNTIME / "lib"), "--argv0", str(python),
            str(python), "-c", f"open({str(marker)!r}, 'w').write('declared-runtime-only')",
        ]
        os.execve(loader, argv, {"LC_ALL": "C", "TZ": "UTC"})
    _pid, status = os.waitpid(child, 0)
    if os.waitstatus_to_exitcode(status) != 0 or not marker.is_file():
        return "failed"
    return marker.read_text(encoding="utf-8")


def denied_socket_syscall() -> str:
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(41, 2, 1, 0)
    if result == -1:
        return os.strerror(ctypes.get_errno())
    os.close(result)
    return "allowed"


def main() -> int:
    mode = json.loads((INPUT / "mode.json").read_text(encoding="utf-8"))["mode"]
    if mode == "host-only-module":
        try:
            ctypes.CDLL("libnss_systemd.so.2")
        except OSError:
            return 91
        return 92
    if mode == "absolute-old-root":
        try:
            ctypes.CDLL("/lib/x86_64-linux-gnu/libnss_systemd.so.2")
        except OSError:
            return 91
        return 92

    sys.path.insert(0, str(RUNTIME / "lib"))
    import _slice072_extension

    shared_bytes = (RUNTIME / "data/probe.so").read_bytes()
    executable_bytes = (RUNTIME / "data/probe-exec").read_bytes()
    (SCRATCH / "probe.so").write_bytes(shared_bytes)
    (SCRATCH / "probe-exec").write_bytes(executable_bytes)
    (OUTPUT / "result.json").write_bytes(shared_bytes)
    output_shared = OUTPUT / "result.json"
    paths = {
        "input": (INPUT / "probe.so", INPUT / "probe-exec"),
        "runtime_data": (RUNTIME / "data/probe.so", RUNTIME / "data/probe-exec"),
        "scratch": (SCRATCH / "probe.so", SCRATCH / "probe-exec"),
        "subject": (
            SUBJECT / "tests/e2e/fixtures/slice072-probe.so",
            SUBJECT / "tests/e2e/fixtures/slice072-probe-exec",
        ),
    }
    result = {name: probe(shared, executable, name) for name, (shared, executable) in paths.items()}
    output_result = {
        "dlopen": denied_dlopen(output_shared),
        "mmap_exec": denied_mmap_exec(output_shared),
    }
    (OUTPUT / "result.json").write_bytes(executable_bytes)
    output_result.update(
        {
            "execve": denied_exec(output_shared, by_fd=False),
            "execveat": denied_exec(output_shared, by_fd=True),
            "explicit_loader": denied_explicit_loader(output_shared, "output"),
        }
    )
    result["output"] = output_result
    result = {
        "declared_extension": _slice072_extension.identity(),
        "explicit_loader_nested": nested_runtime(),
        "runtime_manifest": {"mmap_exec": denied_mmap_exec(RUNTIME / "closure.json")},
        "seccomp_default": denied_socket_syscall(),
        "runtime_value": (RUNTIME / "data/runtime-value.txt")
        .read_text(encoding="utf-8")
        .strip(),
        **result,
    }
    (OUTPUT / "result.json").write_bytes(canonical(result) + b"\n")
    return 0


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


if __name__ == "__main__":
    raise SystemExit(main())
