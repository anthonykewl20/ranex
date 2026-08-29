"""Frozen RED security contract for the sealed v3 verifier boundary."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "governance/confinement/strict-local-v3.json"
LAUNCHER = ROOT / "native/ranex-worker-launcher/launcher.c"
HOST_OWNER = ROOT / "src/ranex/cli/host_confinement.py"
DYNAMIC_OWNER = ROOT / "src/ranex/foundation/dynamic_runtime.py"


def _profile() -> dict[str, object]:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def _function(source: str, name: str) -> str:
    match = re.search(rf"static [^\n]+\b{name}\([^{{]+\) \{{", source)
    assert match is not None, f"missing launcher function {name}"
    opening = source.index("{", match.start())
    depth = 0
    for offset in range(opening, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[match.start() : offset + 1]
    raise AssertionError(f"unterminated launcher function {name}")


def test_profile_separates_native_and_data_mount_attributes() -> None:
    value = _profile()
    assert value["sealed_mount_attributes"] == {
        "native": ["MOUNT_ATTR_RDONLY"],
        "runtime-data": ["MOUNT_ATTR_RDONLY", "MOUNT_ATTR_NOEXEC"],
        "manifest": ["MOUNT_ATTR_RDONLY", "MOUNT_ATTR_NOEXEC"],
    }
    assert value["mounts"] == {
        "input": {"access": "read-only-noexec", "destination": "/ranex/input"},
        "output": {"access": "writable-noexec-bounded", "destination": "/ranex/output"},
        "runtime": {"access": "sealed-file-map", "destination": "/ranex/runtime"},
        "scratch": {"access": "writable-noexec-bounded", "destination": "/ranex/scratch"},
        "subject": {"access": "read-only-noexec", "destination": "/ranex/subject"},
    }


def test_profile_freezes_loader_probe_and_single_use_acknowledgement() -> None:
    verifier = _profile()["verifier"]
    assert verifier["argv"] == [
        "/ranex/runtime/loader/ld-linux-x86-64.so.2",
        "--inhibit-cache",
        "--glibc-hwcaps-mask",
        "",
        "--library-path",
        "/ranex/runtime/lib",
        "--list",
        "<root>",
    ]
    assert verifier["report_bytes_per_root_maximum"] == 65536
    assert verifier["acknowledgement"] == ["GO", "REFUSE"]
    assert verifier["acknowledgement_uses"] == 1
    assert verifier["host_root"] == "absent"
    assert verifier["secrets"] == "none"
    assert verifier["network"] == "denied"
    assert verifier["filesystem"] == {"runtime": ["read", "execute"]}
    assert verifier["fork"] == "denied"
    assert verifier["report_framing"] == (
        "u32be-root-length-plus-root-plus-u32be-report-length-plus-report"
    )
    assert verifier["authority_attach_order"] == [
        "runtime-only-verifier",
        "kill-and-drain-verifier-cgroup",
        "attach-worker-authorities",
    ]


def test_profile_pins_loader_tcb_and_closed_dynamic_syscall_delta() -> None:
    value = _profile()
    assert set(value["loader_tcb"]) == {
        "sha256",
        "self_id",
        "version",
        "architecture",
    }
    assert value["loader_tcb"]["sha256"].startswith("sha256:")
    assert value["seccomp"]["base_profile"] == "strict-local-v2"
    assert value["seccomp"]["verifier_additions"] == ["writev"]
    assert value["seccomp"]["worker_additions"] == [
        "access",
        "getcwd",
        "ioctl",
        "readlink",
        "readlinkat",
        "statx",
        "sysinfo",
        "unlinkat",
    ]


def test_launcher_mounts_only_the_sealed_file_map_at_literal_runtime_paths() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assembly = _function(source, "assemble_v3_runtime")
    for token in (
        '"/ranex/runtime"',
        "sealed_file_fds",
        "SYS_open_tree",
        "AT_EMPTY_PATH",
        "SYS_mount_setattr",
        "MOUNT_ATTR_RDONLY",
        "MOUNT_ATTR_NOEXEC",
        "SYS_move_mount",
        "MOVE_MOUNT_F_EMPTY_PATH | MOVE_MOUNT_T_EMPTY_PATH",
        "pivot_root",
        "MNT_DETACH",
    ):
        assert token in assembly
    for forbidden in ("runtime_source_path", "runtime_destination", "MS_BIND"):
        assert forbidden not in assembly


def test_launcher_v3_seccomp_matches_profile_and_retains_default_deny() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    policy = _function(source, "enforce_seccomp_v3")
    v2_policy = _function(source, "enforce_seccomp")
    v2_expected = {
        "arch_prctl", "brk", "clone", "clock_gettime", "clock_nanosleep",
        "close", "dup", "dup2", "dup3", "execve", "execveat", "exit",
        "exit_group", "fcntl", "fstat", "futex", "getdents64", "geteuid",
        "getegid", "getgid", "getpid", "getppid", "getrandom", "gettid",
        "getuid", "lseek", "madvise", "mkdir", "mmap", "mprotect", "munmap",
        "newfstatat", "openat", "pread64", "prlimit64", "read", "rseq",
        "rt_sigaction", "rt_sigprocmask", "rt_sigreturn", "sched_yield",
        "set_robust_list", "set_tid_address", "wait4", "write",
    }
    additions = set(_profile()["seccomp"]["worker_additions"])
    assert set(re.findall(r"__NR_([a-z0-9_]+)", v2_policy)) == v2_expected
    assert set(re.findall(r"__NR_([a-z0-9_]+)", policy)) == v2_expected | additions
    assert "SECCOMP_RET_ERRNO" in policy


def test_loader_probe_and_worker_share_snapshot_but_not_process_authority() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    verifier = _function(source, "run_v3_verifier")
    worker = _function(source, "v3_worker_exec")
    for token in (
        "deny_network",
        "enforce_limits",
        "close_worker_descriptors",
        "runtime_only_landlock",
        "kill_verifier_cgroup",
        "wait_cgroup_empty",
    ):
        assert token in verifier
    assert "read_controller_ack" in verifier
    assert "GO" in verifier and "REFUSE" in verifier
    assert "execveat" in worker
    assert "runtime_snapshot" in verifier
    assert "runtime_snapshot" in worker
    assert source.index("run_v3_verifier") < source.index("v3_worker_exec")
    assert source.index("wait_cgroup_empty") < source.index("attach_v3_worker_authorities")


def test_controller_never_executes_the_closure_loader_on_the_host_root() -> None:
    foundation = DYNAMIC_OWNER.read_text(encoding="utf-8")
    controller = HOST_OWNER.read_text(encoding="utf-8")
    assert "subprocess" not in foundation
    assert "ld-linux-x86-64.so.2" not in foundation
    assert "--ranex-verifier-report-fd" in controller
    assert "--ranex-verifier-ack-fd" in controller
    assert "normalize_loader_report" in controller
    # The dead duplicate `_release_runtime_worker` was removed in 56b0192
    # (issue #67); the live inline path writes the validated decision.
    assert "os.write(verifier_ack_write, decision)" in controller


def test_command_v2_carries_runtime_source_only_and_no_destination() -> None:
    source = HOST_OWNER.read_text(encoding="utf-8")
    assert '"ranex-confinement-command-v2"' in source
    assert """expected_v2 = {
            "cgroup",
            "cwd",
            "landlock",
            "landlock_abi_minimum",
            "mandatory_layers",
            "mount_api",
            "mounts",
            "output_contract",
            "output_resolution",
            "profile",
            "schema",
            "seccomp",
            "worker_executable",
            "worker_io",
        }""" in source
    for forbidden in (
        '"runtime_destination"',
        '"loader_destination"',
        '"library_destination"',
        '"toolchain_destination"',
    ):
        assert forbidden not in source


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"garbage\n",
        b"linux-vdso.so.1 (0x1)\nlinux-vdso.so.1 (0x2)\n",
        b"libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x1)\n",
        b"x" * 65537,
    ],
    ids=["empty", "garbage", "duplicate-vdso", "host-path", "oversize"],
)
def test_malformed_or_host_resolved_verifier_report_never_gets_go(raw: bytes) -> None:
    from ranex.cli.host_confinement import runtime_verifier_decision

    expected = {
        "bin/python3.12": {
            "loader": "/ranex/runtime/loader/ld-linux-x86-64.so.2",
            "synthetic": ["linux-vdso.so.1"],
            "resolved": {"libc.so.6": "/ranex/runtime/lib/libc.so.6"},
        }
    }
    assert runtime_verifier_decision(expected, {"bin/python3.12": raw}) == b"REFUSE"


def test_matching_verifier_report_gets_exactly_one_go() -> None:
    from ranex.cli.host_confinement import runtime_verifier_decision

    expected = {
        "bin/python3.12": {
            "loader": "/ranex/runtime/loader/ld-linux-x86-64.so.2",
            "synthetic": ["linux-vdso.so.1"],
            "resolved": {"libc.so.6": "/ranex/runtime/lib/libc.so.6"},
        },
        "lib/_slice072_extension.so": {
            "loader": "/ranex/runtime/loader/ld-linux-x86-64.so.2",
            "synthetic": ["linux-vdso.so.1"],
            "resolved": {
                "libc.so.6": "/ranex/runtime/lib/libc.so.6",
                "libpython3.12.so.1.0": "/ranex/runtime/lib/libpython3.12.so.1.0",
            },
        },
    }
    raw = b"""\
\tlinux-vdso.so.1 (0x00007fff00000000)
\tlibc.so.6 => /ranex/runtime/lib/libc.so.6 (0x0000700000000000)
\t/ranex/runtime/loader/ld-linux-x86-64.so.2 (0x0000700000200000)
"""
    extension = raw.replace(
        b"\tlibc.so.6",
        b"\tlibpython3.12.so.1.0 => /ranex/runtime/lib/libpython3.12.so.1.0 (0x0000700000100000)\n\tlibc.so.6",
    )
    reports = {
        "bin/python3.12": raw,
        "lib/_slice072_extension.so": extension,
    }
    assert runtime_verifier_decision(expected, reports) == b"GO"
    assert runtime_verifier_decision(expected, dict(reversed(reports.items()))) == b"REFUSE"
    assert runtime_verifier_decision(expected, {"bin/python3.12": raw}) == b"REFUSE"


def _frame(root: str, report: bytes) -> bytes:
    root_bytes = root.encode("utf-8")
    return (
        struct.pack(">I", len(root_bytes))
        + root_bytes
        + struct.pack(">I", len(report))
        + report
    )


def test_multi_root_frame_parser_is_exact_and_rejects_ambiguous_streams() -> None:
    from ranex.cli.host_confinement import parse_runtime_verifier_frames

    roots = ["bin/python3.12", "lib/_slice072_extension.so"]
    first = _frame(roots[0], b"first")
    second = _frame(roots[1], b"second")
    assert parse_runtime_verifier_frames(first + second, roots) == {
        roots[0]: b"first",
        roots[1]: b"second",
    }
    malformed = [
        b"",
        first[:-1],
        first + first,
        second + first,
        first + second + b"trailing",
        _frame("unknown", b"x") + second,
        _frame(roots[0], b"x" * 65537) + second,
        struct.pack(">I", 0xFFFFFFFF),
    ]
    for raw in malformed:
        with pytest.raises(ValueError):
            parse_runtime_verifier_frames(raw, roots)


def test_worker_release_is_ordered_after_report_comparison_and_go() -> None:
    source = HOST_OWNER.read_text(encoding="utf-8")
    report = source.index("_read_runtime_verifier_report")
    decision = source.index("runtime_verifier_decision", report)
    go = source.index("os.write(verifier_ack_write", decision)
    worker = source.index("_read_launcher_readiness", go)
    assert report < decision < go < worker
