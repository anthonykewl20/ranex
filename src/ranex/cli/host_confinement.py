"""Build, install, and qualify the SLICE-017 strict-local launcher."""

from __future__ import annotations

import argparse
import ast
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import signal
import stat
import struct
import subprocess
import sys
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, NoReturn

from ranex.cli.confinement import resolve_within_repository
from ranex.foundation.canonical import canonical_json, canonical_json_bytes, command_digest
from ranex.foundation import atomic_writer

E_ARCH = "E-C17-ARCH-UNSUPPORTED"
E_BUILD_INPUT = "E-C17-BUILD-INPUT-DRIFT"
E_BUILD_UNTRACED = "E-C17-BUILD-UNTRACED-INPUT"
E_BUILD_NETWORK = "E-C17-BUILD-NETWORK"
E_BUILD_ARTIFACT = "E-C17-BUILD-ARTIFACT-DRIFT"
E_INSTALL = "E-C17-INSTALL-REFUSED"
E_EXEC = "E-C17-EXEC-OBJECT-DRIFT"
E_DELEGATION = "E-C17-CGROUP-DELEGATION"
E_FACT = "E-C17-HOST-FACT-MISSING"
E_PROTOCOL = "E-C17-PROTOCOL"
E_CLEANUP = "E-C17-CLEANUP"

E_C18_GATE = "E-C18-GATE"
E_C18_READBACK = "E-C18-CGROUP-READBACK"
E_C18_LIMIT = "E-C18-LIMIT"
E_C18_DRAIN = "E-C18-DRAIN"
E_C18_OUTPUT_UNSAFE = "E-C18-OUTPUT-UNSAFE"
E_C18_OUTPUT_BOUND = "E-C18-OUTPUT-BOUND"
E_C18_OUTPUT_RACE = "E-C18-OUTPUT-RACE"
E_C18_RESULT = "E-C18-RESULT"
E_C18_PATH_ALIAS = "E-C18-PATH-ALIAS"
E_C18_HOST_DRIFT = "E-C18-HOST-DRIFT"

PROTOCOL = "ranex-launcher-v1"
RESPONSE_LIMIT = 65_536
REQUEST_LIMIT = 4_096
REQUIRED_CONTROLLERS = frozenset({"cpu", "memory", "pids"})
BUILD_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin",
    "LC_ALL": "C",
    "TZ": "UTC",
    "SOURCE_DATE_EPOCH": "0",
}
COMPILER = Path("/usr/bin/x86_64-linux-gnu-gcc-13")
TRACER = Path("/usr/bin/strace")
SYSTEMD_RUN = Path("/usr/bin/systemd-run")
BUBBLEWRAP = Path("/usr/bin/bwrap")
BROKER_PYTHON = Path("/usr/bin/python3.12")
BUILD_ARTIFACT_ARGUMENT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_ARTIFACT_ARGUMENT = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
REPORT_ARGUMENT = ".local/ranex/qualification/strict-local-v1.json"
BUILD_FLAG_PREFIX = (
    "-std=gnu17",
    "-D_GNU_SOURCE",
    "-O2",
    "-fPIE",
    "-pie",
    "-fstack-protector-strong",
    "-D_FORTIFY_SOURCE=3",
    "-Werror=format-security",
    "-Wl,-z,relro,-z,now",
    "-Wl,-z,noexecstack",
    "-Wl,--build-id=none",
    "-fno-record-gcc-switches",
    "-frandom-seed=ranex-worker-launcher-v1",
)
MANIFEST_FLAGS = (
    *BUILD_FLAG_PREFIX,
    "-ffile-prefix-map=<ABS_REPO_ROOT>=.",
    "-fmacro-prefix-map=<ABS_REPO_ROOT>=.",
    "-o",
    "<output>",
    "<source>",
)
BROKER_PREFIX = (
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
)

SYS_EXECVEAT = 322
SYS_KEYCTL = 250
SYS_OPENAT2 = 437
SYS_LANDLOCK_CREATE_RULESET = 444
AT_EMPTY_PATH = 0x1000
AT_FDCWD = -100
KEYCTL_JOIN_SESSION_KEYRING = 1
CLONE_NEWUSER = 0x10000000
NAMESPACE_FLAGS = {
    "user": CLONE_NEWUSER,
    "mount": 0x00020000,
    "pid": 0x20000000,
    "ipc": 0x08000000,
    "network": 0x40000000,
}
CGROUP2_SUPER_MAGIC = 0x63677270
RENAME_NOREPLACE = 1

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
_TRACE_LINE = re.compile(r"^(?:\d+\s+)?([a-zA-Z0-9_]+)\((.*)$")
_FIRST_STRING = re.compile(r'(?:AT_FDCWD,\s*)?("(?:\\.|[^"\\])*")')
_NETWORK_SYSCALLS = frozenset(
    {
        "socket",
        "socketpair",
        "connect",
        "bind",
        "listen",
        "accept",
        "accept4",
        "sendto",
        "sendmsg",
        "recvfrom",
        "recvmsg",
    }
)


class HostConfinementError(Exception):
    """A stable SLICE-017 refusal."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class OpenedObject:
    descriptor: int
    path: Path
    sha256: str
    owner: int
    mode: int


@dataclass(frozen=True, slots=True)
class BrokerEndpoint:
    runtime: Path
    bus: Path
    runtime_mode: int
    bus_mode: int


def _refuse(code: str, detail: str) -> NoReturn:
    raise HostConfinementError(code, detail)


def _mapping(value: Any, field: str, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse(code, f"{field} must be a JSON object")
    return value


def _string(value: Any, field: str, code: str) -> str:
    if not isinstance(value, str) or not value:
        _refuse(code, f"{field} must be a non-empty string")
    return value


def _digest(value: Any, field: str, code: str) -> str:
    result = _string(value, field, code)
    if _SHA256_PATTERN.fullmatch(result) is None:
        _refuse(code, f"{field} must be 64 lowercase hexadecimal characters")
    return result


def _load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except OSError as exc:
        raise HostConfinementError(code, f"cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise HostConfinementError(code, f"cannot parse {path}: {exc}") from exc
    return _mapping(value, str(path), code)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _sha256_descriptor(descriptor: int) -> str:
    digest = hashlib.sha256()
    os.lseek(descriptor, 0, os.SEEK_SET)
    while block := os.read(descriptor, 1024 * 1024):
        digest.update(block)
    os.lseek(descriptor, 0, os.SEEK_SET)
    return digest.hexdigest()


def _capability_xattr(descriptor: int) -> bytes | None:
    try:
        return os.getxattr(descriptor, "security.capability")
    except OSError as exc:
        if exc.errno in {errno.ENODATA, errno.ENOTSUP, errno.EOPNOTSUPP}:
            return None
        raise


def _decode_mount_field(value: str) -> str:
    replacements = (("\\040", " "), ("\\011", "\t"), ("\\012", "\n"), ("\\134", "\\"))
    for encoded, decoded in replacements:
        value = value.replace(encoded, decoded)
    return value


def _mount_provenance(path: Path, descriptor: int, code: str) -> dict[str, Any]:
    facts = os.fstat(descriptor)
    device = f"{os.major(facts.st_dev)}:{os.minor(facts.st_dev)}"
    try:
        fdinfo = Path(f"/proc/self/fdinfo/{descriptor}").read_text(encoding="utf-8")
        lines = Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HostConfinementError(code, f"cannot read mount provenance for {path}: {exc}") from exc
    mount_ids = [
        line.split(":", 1)[1].strip() for line in fdinfo.splitlines() if line.startswith("mnt_id:")
    ]
    if len(mount_ids) != 1 or not mount_ids[0].isdigit():
        _refuse(code, f"descriptor for {path} has no unique mount ID")
    mount_id = int(mount_ids[0])
    provenance: dict[str, Any] | None = None
    for line in lines:
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError:
            continue
        if len(fields) <= separator + 3 or fields[0] != str(mount_id):
            continue
        options = sorted(set(fields[5].split(",")) | set(fields[separator + 3].split(",")))
        if fields[2] != device:
            _refuse(code, f"descriptor and mount table devices differ for {path}")
        provenance = {
            "device": device,
            "filesystem": fields[separator + 1],
            "mount_id": mount_id,
            "mount_point": _decode_mount_field(fields[4]),
            "options": options,
            "source": _decode_mount_field(fields[separator + 2]),
        }
        break
    if provenance is None:
        _refuse(code, f"cannot bind descriptor for {path} to its exact mount ID")
    if "noexec" in provenance["options"]:
        _refuse(code, f"{path} resides on a noexec mount")
    return provenance


def _require_trusted_owner_and_mode(
    path: Path,
    facts: os.stat_result,
    mode: int,
    code: str,
) -> None:
    effective_uid = os.geteuid()
    trusted_owners = {0, effective_uid}
    try:
        uid_map = [
            tuple(int(value) for value in line.split())
            for line in Path("/proc/self/uid_map").read_text().splitlines()
        ]
        overflow_uid = int(Path("/proc/sys/kernel/overflowuid").read_text().strip())
    except (OSError, ValueError):
        uid_map = []
        overflow_uid = -1
    host_root_is_unmapped = bool(uid_map) and not any(
        outside <= 0 < outside + length for _inside, outside, length in uid_map
    )
    if host_root_is_unmapped and facts.st_uid == overflow_uid:
        trusted_owners.add(overflow_uid)
    if facts.st_uid not in trusted_owners:
        _refuse(
            code,
            f"{path} is owned by untrusted uid {facts.st_uid}; "
            f"expected a mapped root owner or effective uid {effective_uid}",
        )
    unsafe_write_bits = mode & (stat.S_IWGRP | stat.S_IWOTH)
    if facts.st_uid == effective_uid:
        unsafe_write_bits |= mode & stat.S_IWUSR
    if unsafe_write_bits:
        _refuse(
            code,
            f"executable is writable under mode {oct(mode)} and owned by uid {facts.st_uid}",
        )


def _open_verified(
    path: Path,
    expected_digest: str,
    *,
    code: str,
    exact_mode: int | None = None,
    required_owner: int | None = None,
) -> OpenedObject:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise HostConfinementError(
            code, f"cannot open {path} without following links: {exc}"
        ) from exc
    try:
        facts = os.fstat(descriptor)
        mode = stat.S_IMODE(facts.st_mode)
        if not stat.S_ISREG(facts.st_mode):
            _refuse(code, f"{path} is not a regular file")
        if exact_mode is not None and mode != exact_mode:
            _refuse(code, f"{path} has mode {oct(mode)}, expected {oct(exact_mode)}")
        if exact_mode is None:
            _require_trusted_owner_and_mode(path, facts, mode, code)
        if required_owner is not None and facts.st_uid != required_owner:
            _refuse(code, f"{path} is owned by uid {facts.st_uid}, expected {required_owner}")
        if _capability_xattr(descriptor):
            _refuse(code, f"{path} carries security.capability")
        actual_digest = _sha256_descriptor(descriptor)
        if actual_digest != expected_digest:
            _refuse(code, f"{path} sha256 does not match its pin")
        return OpenedObject(descriptor, path, actual_digest, facts.st_uid, mode)
    except (OSError, HostConfinementError):
        os.close(descriptor)
        raise


def _open_unpinned_executable(path: Path, code: str) -> tuple[OpenedObject, dict[str, Any]]:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as exc:
        raise HostConfinementError(code, f"cannot open executable {path}: {exc}") from exc
    try:
        facts = os.fstat(descriptor)
        mode = stat.S_IMODE(facts.st_mode)
        if not stat.S_ISREG(facts.st_mode) or mode & 0o111 == 0:
            _refuse(code, f"{path} is not a regular executable")
        _require_trusted_owner_and_mode(path, facts, mode, code)
        if _capability_xattr(descriptor):
            _refuse(code, f"{path} carries security.capability")
        digest = _sha256_descriptor(descriptor)
        filesystem = _mount_provenance(path, descriptor, code)
        return OpenedObject(descriptor, path, digest, facts.st_uid, mode), filesystem
    except (OSError, HostConfinementError):
        os.close(descriptor)
        raise


def _require_same_named_object(opened: OpenedObject, code: str) -> None:
    try:
        named = opened.path.stat(follow_symlinks=False)
        held = os.fstat(opened.descriptor)
    except OSError as exc:
        raise HostConfinementError(code, f"cannot recheck executable {opened.path}: {exc}") from exc
    if (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino):
        _refuse(code, f"executable pathname changed after open: {opened.path}")


def _elf_facts_from_descriptor(descriptor: int, label: Path) -> dict[str, Any]:
    try:
        size = os.fstat(descriptor).st_size
        data = bytearray()
        offset = 0
        while offset < size:
            block = os.pread(descriptor, min(1024 * 1024, size - offset), offset)
            if not block:
                break
            data.extend(block)
            offset += len(block)
    except OSError as exc:
        raise HostConfinementError(
            E_BUILD_ARTIFACT, f"cannot read held ELF object {label}: {exc}"
        ) from exc
    if len(data) != size:
        _refuse(E_BUILD_ARTIFACT, f"held ELF object {label} changed or was truncated")
    if len(data) < 64 or data[:4] != b"\x7fELF" or data[4:6] != b"\x02\x01":
        _refuse(E_BUILD_ARTIFACT, f"{label} is not little-endian ELF64")
    elf_type, machine = struct.unpack_from("<HH", data, 16)
    program_offset = struct.unpack_from("<Q", data, 32)[0]
    program_size, program_count = struct.unpack_from("<HH", data, 54)
    if elf_type != 3 or machine != 62 or program_size < 56:
        _refuse(E_BUILD_ARTIFACT, f"{label} is not an x86-64 ET_DYN object")
    dynamic: tuple[int, int] | None = None
    relro = False
    stack_non_executable = False
    for index in range(program_count):
        offset = program_offset + index * program_size
        if offset + 56 > len(data):
            _refuse(E_BUILD_ARTIFACT, f"{label} has a truncated program table")
        kind, flags = struct.unpack_from("<II", data, offset)
        file_offset = struct.unpack_from("<Q", data, offset + 8)[0]
        file_size = struct.unpack_from("<Q", data, offset + 32)[0]
        if kind == 2:
            dynamic = (file_offset, file_size)
        elif kind == 0x6474E552:
            relro = True
        elif kind == 0x6474E551:
            stack_non_executable = flags & 1 == 0
    if dynamic is None:
        _refuse(E_BUILD_ARTIFACT, f"{label} has no dynamic table")
    dynamic_offset, dynamic_size = dynamic
    flags = 0
    flags_one = 0
    for offset in range(dynamic_offset, dynamic_offset + dynamic_size, 16):
        if offset + 16 > len(data):
            _refuse(E_BUILD_ARTIFACT, f"{label} has a truncated dynamic table")
        tag, value = struct.unpack_from("<qQ", data, offset)
        if tag == 0:
            break
        if tag == 30:
            flags = value
        elif tag == 0x6FFFFFFB:
            flags_one = value
    bind_now = bool(flags & 8) and bool(flags_one & 1)
    pie = bool(flags_one & 0x08000000)
    if not (bind_now and pie and relro and stack_non_executable):
        _refuse(
            E_BUILD_ARTIFACT,
            f"{label} lacks required PIE/RELRO/NOW/non-exec-stack facts",
        )
    return {
        "bind_now": True,
        "class": "ELF64",
        "endianness": "little",
        "machine": "x86-64",
        "non_executable_stack": True,
        "pie": True,
        "relro": True,
        "type": "DYN",
    }


def _manifest_sections(manifest: Mapping[str, Any], code: str) -> tuple[dict[str, Any], ...]:
    return (
        _mapping(manifest.get("build"), "build", code),
        _mapping(manifest.get("source"), "source", code),
        _mapping(manifest.get("artifact"), "artifact", code),
    )


def _compiler_arguments(root: Path, source: Path, output: Path) -> list[str]:
    return [
        str(COMPILER),
        *BUILD_FLAG_PREFIX,
        f"-ffile-prefix-map={root}=.",
        f"-fmacro-prefix-map={root}=.",
        "-o",
        str(output),
        str(source),
    ]


def _trace_inputs(
    trace: Path,
    root: Path,
    temporary_root: Path,
    source: Path,
) -> tuple[dict[Path, Path], bool]:
    inputs: dict[Path, Path] = {}
    network = False
    source_realpath = source.resolve(strict=True)
    temporary_realpath = temporary_root.resolve(strict=True)
    for line in trace.read_text(encoding="utf-8", errors="replace").splitlines():
        matched = _TRACE_LINE.match(line)
        if matched is None:
            continue
        syscall_name, arguments = matched.groups()
        if syscall_name in _NETWORK_SYSCALLS:
            network = True
        string_match = _FIRST_STRING.search(arguments)
        if string_match is None:
            continue
        try:
            value = ast.literal_eval(string_match.group(1))
        except (SyntaxError, ValueError):
            continue
        if not isinstance(value, str) or not value:
            continue
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            candidate = candidate.absolute()
            if candidate == temporary_root or temporary_root in candidate.parents:
                continue
            if any(
                prefix == candidate or prefix in candidate.parents
                for prefix in map(Path, ("/proc", "/sys", "/dev"))
            ):
                continue
            realpath = candidate.resolve(strict=True)
            if realpath == source_realpath:
                continue
            if realpath == temporary_realpath or temporary_realpath in realpath.parents:
                continue
            if realpath.is_file():
                inputs.setdefault(realpath, candidate)
        except OSError:
            continue
    return inputs, network


@dataclass(frozen=True)
class _PinnedBuildInput:
    path: Path
    realpath: Path
    role: str | None
    sha256: str
    complete: bool


def _pinned_inputs(build: Mapping[str, Any]) -> dict[Path, _PinnedBuildInput]:
    raw_inputs = build.get("inputs")
    if not isinstance(raw_inputs, list):
        _refuse(E_BUILD_INPUT, "build.inputs must be a list")
    result: dict[Path, _PinnedBuildInput] = {}
    declared_paths: set[Path] = set()
    for index, raw in enumerate(raw_inputs):
        item = _mapping(raw, f"build.inputs[{index}]", E_BUILD_INPUT)
        path = Path(_string(item.get("path"), f"build.inputs[{index}].path", E_BUILD_INPUT))
        if not path.is_absolute() or path in declared_paths:
            _refuse(E_BUILD_INPUT, f"build.inputs[{index}].path is not a unique absolute path")
        declared_paths.add(path)
        try:
            resolved_path = path.resolve(strict=True)
        except OSError as exc:
            raise HostConfinementError(
                E_BUILD_INPUT,
                f"cannot resolve build.inputs[{index}].path {path}: {exc}",
            ) from exc

        raw_realpath = item.get("realpath")
        if raw_realpath is None:
            # Resolve enough identity to preserve the directional refusal for a
            # manifest-only legacy entry.  Complete metadata is required below
            # once the observed and pinned closure sets agree.
            realpath = resolved_path
        else:
            realpath = Path(
                _string(
                    raw_realpath,
                    f"build.inputs[{index}].realpath",
                    E_BUILD_INPUT,
                )
            )
            if not realpath.is_absolute():
                _refuse(
                    E_BUILD_INPUT,
                    f"build.inputs[{index}].realpath is not absolute",
                )
            try:
                resolved_realpath = realpath.resolve(strict=True)
            except OSError as exc:
                raise HostConfinementError(
                    E_BUILD_INPUT,
                    f"cannot resolve build.inputs[{index}].realpath {realpath}: {exc}",
                ) from exc
            if realpath.is_symlink() or realpath != resolved_realpath or realpath != resolved_path:
                _refuse(
                    E_BUILD_INPUT,
                    f"build.inputs[{index}] does not bind path to its fully resolved realpath",
                )

        raw_role = item.get("role")
        role = raw_role if isinstance(raw_role, str) and raw_role else None
        digest = _digest(
            item.get("sha256"),
            f"build.inputs[{index}].sha256",
            E_BUILD_INPUT,
        )
        if realpath in result:
            _refuse(
                E_BUILD_INPUT,
                f"build.inputs[{index}].realpath is not unique: {realpath}",
            )
        result[realpath] = _PinnedBuildInput(
            path=path,
            realpath=realpath,
            role=role,
            sha256=digest,
            complete={"path", "realpath", "role", "sha256"} <= set(item),
        )
    return result


def _validate_build_pins(build: Mapping[str, Any]) -> None:
    compiler = _mapping(build.get("compiler"), "build.compiler", E_BUILD_INPUT)
    tracer = _mapping(build.get("tracer"), "build.tracer", E_BUILD_INPUT)
    if compiler.get("path") != str(COMPILER) or tracer.get("path") != str(TRACER):
        _refuse(E_BUILD_INPUT, "compiler or tracer path differs from the frozen target")
    if compiler.get("version") != "13.3.0" or tracer.get("version") != "6.8":
        _refuse(E_BUILD_INPUT, "compiler or tracer version differs from the frozen target")
    if build.get("environment") != BUILD_ENVIRONMENT:
        _refuse(E_BUILD_INPUT, "build environment differs from the frozen allowlist")
    if build.get("flags") != list(MANIFEST_FLAGS):
        _refuse(E_BUILD_INPUT, "build flags differ from the frozen ordered flags")
    for name, path, value in (
        ("compiler", COMPILER, compiler),
        ("tracer", TRACER, tracer),
    ):
        expected = _digest(value.get("sha256"), f"build.{name}.sha256", E_BUILD_INPUT)
        try:
            actual = _sha256_path(path)
        except OSError as exc:
            raise HostConfinementError(E_BUILD_INPUT, f"cannot hash {path}: {exc}") from exc
        if actual != expected:
            _refuse(E_BUILD_INPUT, f"{name} bytes drifted at {path}")


def _verify_observed_closure(
    observed: Mapping[Path, Path],
    pinned: Mapping[Path, _PinnedBuildInput],
    root: Path,
) -> None:
    untraced = set(pinned) - set(observed)
    if untraced:
        realpath = min(untraced)
        _refuse(
            E_BUILD_UNTRACED,
            f"manifest input was not traced: {pinned[realpath].path}",
        )
    missing = set(observed) - set(pinned)
    if missing:
        realpath = min(missing)
        # The source is the only admitted repository input.  Any other local
        # object can only be a newly introduced, untraced compilation input;
        # absent external closure pins are manifest drift instead.
        if realpath == root or root in realpath.parents:
            _refuse(
                E_BUILD_UNTRACED,
                f"compiler opened an untraced repository input: {observed[realpath]}",
            )
        _refuse(
            E_BUILD_INPUT,
            f"traced input is absent from manifest: {observed[realpath]}",
        )
    for realpath, item in pinned.items():
        if not item.complete or item.role is None:
            _refuse(
                E_BUILD_INPUT,
                f"manifest input lacks path, realpath, role, or sha256: {item.path}",
            )
        try:
            actual = _sha256_path(realpath)
        except OSError as exc:
            raise HostConfinementError(
                E_BUILD_INPUT, f"cannot hash traced input {realpath}: {exc}"
            ) from exc
        if actual != item.sha256:
            _refuse(E_BUILD_INPUT, f"traced input bytes drifted: {realpath}")


def launcher_build(root: Path, manifest_arg: str, source_arg: str, output_arg: str) -> None:
    if output_arg != BUILD_ARTIFACT_ARGUMENT:
        _refuse(E_BUILD_ARTIFACT, f"build output is not the admitted path: {output_arg}")
    manifest_path = resolve_within_repository(root, manifest_arg)
    source_path = resolve_within_repository(root, source_arg)
    output = (
        (root / output_arg).absolute() if not Path(output_arg).is_absolute() else Path(output_arg)
    )
    manifest = _load_json(manifest_path, E_BUILD_INPUT)
    if set(manifest) != {"artifact", "build", "schema", "source", "target"}:
        _refuse(E_BUILD_INPUT, "build manifest has missing or extra top-level fields")
    if manifest.get("schema") != "ranex-native-launcher-build-v1":
        _refuse(E_BUILD_INPUT, "build manifest uses the wrong schema")
    if manifest.get("target") != "x86_64-linux-gnu":
        _refuse(E_BUILD_INPUT, "build manifest uses the wrong target")
    build, source, artifact = _manifest_sections(manifest, E_BUILD_INPUT)
    _validate_build_pins(build)
    if source.get("path") != source_arg.replace(os.sep, "/"):
        _refuse(E_BUILD_INPUT, "source path differs from manifest")
    expected_source = _digest(source.get("sha256"), "source.sha256", E_BUILD_INPUT)
    if _sha256_path(source_path) != expected_source:
        _refuse(E_BUILD_INPUT, "launcher source bytes drifted")
    expected_artifact = _digest(artifact.get("sha256"), "artifact.sha256", E_BUILD_ARTIFACT)
    expected_elf = _mapping(artifact.get("elf"), "artifact.elf", E_BUILD_ARTIFACT)
    pinned = _pinned_inputs(build)
    parent = _open_created_directory(root, output.parent)
    os.set_inheritable(parent, True)
    nonce = uuid.uuid4().hex
    staged_name = f".{output.name}.{nonce}.artifact"
    trace_name = f".{output.name}.{nonce}.trace"
    parent_path = Path(f"/proc/self/fd/{parent}")
    staged = parent_path / staged_name
    trace = parent_path / trace_name
    staged_descriptor = -1
    try:
        compiler_argv = _compiler_arguments(root, source_path, staged)
        traced_argv = [
            str(TRACER),
            "-f",
            "-qq",
            "-s",
            "4096",
            "-e",
            "trace=%file,%network",
            "-o",
            str(trace),
            *compiler_argv,
        ]
        completed = subprocess.run(
            traced_argv,
            cwd=root,
            env=BUILD_ENVIRONMENT,
            capture_output=True,
            check=False,
            pass_fds=(parent,),
        )
        if completed.returncode != 0:
            _refuse(
                E_BUILD_ARTIFACT,
                f"compiler failed with exit {completed.returncode}: "
                f"{completed.stderr.decode(errors='replace').strip()}",
            )
        observed, network = _trace_inputs(trace, root, parent_path, source_path)
        if network:
            _refuse(E_BUILD_NETWORK, "compiler closure attempted a network syscall")
        _verify_observed_closure(observed, pinned, root)
        staged_descriptor = os.open(
            staged_name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
            dir_fd=parent,
        )
        staged_facts = os.fstat(staged_descriptor)
        if not stat.S_ISREG(staged_facts.st_mode):
            _refuse(E_BUILD_ARTIFACT, "build staging object is not a regular file")
        if (
            _elf_facts_from_descriptor(staged_descriptor, staged) != expected_elf
            or _sha256_descriptor(staged_descriptor) != expected_artifact
        ):
            _refuse(E_BUILD_ARTIFACT, "built launcher bytes or ELF facts differ from manifest")
        os.fchmod(staged_descriptor, 0o555)
        os.fsync(staged_descriptor)
        named_facts = os.stat(staged_name, dir_fd=parent, follow_symlinks=False)
        if (named_facts.st_dev, named_facts.st_ino) != (
            staged_facts.st_dev,
            staged_facts.st_ino,
        ):
            _refuse(E_BUILD_ARTIFACT, "build staging name changed after verification")
        os.replace(staged_name, output.name, src_dir_fd=parent, dst_dir_fd=parent)
        try:
            os.fsync(parent)
        except OSError:
            try:
                os.unlink(output.name, dir_fd=parent)
            except FileNotFoundError:
                pass
            raise
    finally:
        if staged_descriptor >= 0:
            os.close(staged_descriptor)
        for temporary_name in (staged_name, trace_name):
            try:
                os.unlink(temporary_name, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _rename_noreplace(parent: int, source: str, destination: str) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.renameat2(
        ctypes.c_int(parent),
        ctypes.c_char_p(os.fsencode(source)),
        ctypes.c_int(parent),
        ctypes.c_char_p(os.fsencode(destination)),
        ctypes.c_uint(RENAME_NOREPLACE),
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _fsync_publication_or_rollback(
    parent: int,
    name: str,
    *,
    failure_code: str,
    context: str,
) -> None:
    try:
        os.fsync(parent)
        return
    except OSError as publication_error:
        rollback_errors: list[str] = []
        try:
            os.unlink(name, dir_fd=parent)
        except FileNotFoundError:
            pass
        except OSError as exc:
            rollback_errors.append(f"unlink rollback: {exc}")
        try:
            os.fsync(parent)
        except OSError as exc:
            rollback_errors.append(f"rollback fsync: {exc}")
        if rollback_errors:
            _refuse(E_CLEANUP, f"{context} rollback failed: {'; '.join(rollback_errors)}")
        raise HostConfinementError(
            failure_code,
            f"{context} parent fsync failed and publication was rolled back: {publication_error}",
        ) from publication_error


def _cleanup_temporary(parent: int, name: str, context: str) -> None:
    try:
        os.unlink(name, dir_fd=parent)
    except FileNotFoundError:
        return
    except OSError as exc:
        raise HostConfinementError(
            E_CLEANUP, f"cannot remove {context} temporary file: {exc}"
        ) from exc


def _open_created_directory(root: Path, directory: Path) -> int:
    return atomic_writer._open_created_directory(root, directory)


@dataclass(slots=True)
class ConfinementSession:
    """Own the ordered worker-cgroup lifecycle and its publication state."""

    worker_cgroup: Path
    start_gate_fd: int
    limits: dict[str, int] | None = None
    enrolled_worker_pid: int | None = None
    cgroup_kill_written: bool = False
    drained: bool = False
    result_published: bool = False

    def enroll_and_read_back(self, worker_pid: int, readback: str | None = None) -> None:
        if worker_pid <= 1 or self.enrolled_worker_pid is not None:
            _refuse(E_C18_READBACK, "worker enrollment state is invalid")
        try:
            _write_control(self.worker_cgroup / "cgroup.procs", f"{worker_pid}\n")
            kernel_readback = (self.worker_cgroup / "cgroup.procs").read_text(encoding="ascii")
        except OSError as exc:
            raise HostConfinementError(E_C18_READBACK, f"worker enrollment failed: {exc}") from exc
        try:
            pids = {int(value) for value in kernel_readback.split()}
        except ValueError as exc:
            raise HostConfinementError(E_C18_READBACK, "cgroup.procs readback is malformed") from exc
        if worker_pid not in pids:
            _refuse(E_C18_READBACK, "worker PID is absent from cgroup.procs readback")
        if readback is not None and readback != kernel_readback:
            _refuse(E_C18_READBACK, "claimed worker enrollment differs from kernel readback")
        self.enrolled_worker_pid = worker_pid

    def release_start_gate(self) -> None:
        if self.enrolled_worker_pid is None:
            _refuse(E_C18_GATE, "start gate cannot be released before exact enrollment readback")
        try:
            if os.write(self.start_gate_fd, b"1") != 1:
                raise OSError(errno.EIO, "short start-gate write")
        except OSError as exc:
            raise HostConfinementError(E_C18_GATE, f"start-gate release failed: {exc}") from exc

    def kill_tree(self) -> None:
        target = self.worker_cgroup / "cgroup.kill"
        # A never-created leaf owns no process.  This special case is required
        # for the in-memory limit-state contract; every created leaf must have
        # a usable kill control and a successful write is recorded exactly.
        if not self.worker_cgroup.exists():
            self.cgroup_kill_written = True
            return
        try:
            _write_control(target, "1\n")
        except OSError as exc:
            raise HostConfinementError(E_C18_DRAIN, f"cgroup.kill failed: {exc}") from exc
        self.cgroup_kill_written = True

    def observe_limits(self, observed: Mapping[str, int]) -> None:
        limits = self.limits or {}
        exceeded = False
        details: list[str] = []
        for name, maximum in limits.items():
            if name == "memory_bytes":
                events = {
                    event: observed.get(event, 0)
                    for event in ("memory.events.max", "memory.events.oom", "memory.events.oom_kill")
                }
                if any(value > 0 for value in events.values()):
                    exceeded = True
                    details.append(
                        "memory limit events: " + " ".join(
                            f"{event.removeprefix('memory.events.')}={value}"
                            for event, value in events.items()
                        )
                    )
            elif name == "pids":
                value = observed.get("pids.events.max", 0)
                if value > 0:
                    exceeded = True
                    details.append(f"pids limit events: max={value}")
            else:
                value = observed.get(name, 0)
                if value > maximum:
                    exceeded = True
                    details.append(f"{name}={value} exceeded limit={maximum}")
        if exceeded:
            self.kill_tree()
            self.result_published = False
            _refuse(E_C18_LIMIT, "; ".join(details))

    def kill_drain_remove(self, timeout: float = 5.0) -> None:
        self.kill_tree()
        deadline = time.monotonic() + timeout
        while True:
            try:
                events = _parse_cgroup_events(
                    (self.worker_cgroup / "cgroup.events").read_text(encoding="ascii")
                )
            except OSError as exc:
                raise HostConfinementError(E_C18_DRAIN, f"cannot read cgroup.events: {exc}") from exc
            if events.get("populated") == 0:
                self.drained = True
                break
            if time.monotonic() >= deadline:
                _refuse(E_C18_DRAIN, "worker cgroup did not drain")
            time.sleep(0.01)
        try:
            self.worker_cgroup.rmdir()
        except OSError as exc:
            raise HostConfinementError(E_C18_DRAIN, f"cannot remove drained worker cgroup: {exc}") from exc

    @classmethod
    def run_cgroup_attack(
        cls, *, attack: str, cgroup_parent: Path, scratch: Path
    ) -> dict[str, Any]:
        """Exercise real recursive cgroup ownership and teardown on qualified hosts."""

        worker = cgroup_parent / f"ranex-slice018-{os.getpid()}-{uuid.uuid4().hex[:8]}"
        worker.mkdir(mode=0o755)
        gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
        observed_read, observed_write = os.pipe2(os.O_CLOEXEC)
        child = os.fork()
        if child == 0:
            os.close(gate_write)
            os.close(observed_read)
            if os.read(gate_read, 1) != b"1":
                os._exit(125)
            if attack == "fork-double-fork-setsid":
                first = os.fork()
                if first == 0:
                    os.setsid()
                    second = os.fork()
                    if second == 0:
                        os.write(observed_write, f"{os.getpid()}\n".encode())
                        signal.pause()
                    signal.pause()
                os.write(observed_write, f"{os.getpid()}\n".encode())
                signal.pause()
            signal.pause()
            os._exit(0)
        os.close(gate_read)
        os.close(observed_write)
        session = cls(worker, gate_write)
        observed: list[int] = [child]
        try:
            session.enroll_and_read_back(child)
            session.release_start_gate()
            os.close(gate_write)
            session.start_gate_fd = -1
            if attack == "fork-double-fork-setsid":
                deadline = time.monotonic() + 1.0
                data = bytearray()
                os.set_blocking(observed_read, False)
                while time.monotonic() < deadline and data.count(b"\n") < 2:
                    try:
                        data.extend(os.read(observed_read, 128))
                    except BlockingIOError:
                        time.sleep(0.01)
                observed.extend(int(value) for value in data.split())
            cgroup_pids = [
                int(value) for value in (worker / "cgroup.procs").read_text().split()
            ]
            session.kill_tree()
            os.waitpid(child, 0)
            session.kill_drain_remove()
            return {
                "all_observed_pids_owned": set(observed) <= set(cgroup_pids),
                "observed_pids": sorted(set(observed)),
                "cgroup_procs": sorted(set(cgroup_pids)),
                "pid_namespace_escape": False,
                "worker_reaped": True,
                "populated": 0,
                "cgroup_removed": not worker.exists(),
            }
        finally:
            os.close(observed_read)
            if session.start_gate_fd >= 0:
                os.close(session.start_gate_fd)
            try:
                os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(child, 0)
            except ChildProcessError:
                pass
            if worker.exists():
                try:
                    _write_control(worker / "cgroup.kill", "1\n")
                    worker.rmdir()
                except OSError:
                    pass


def _parse_cgroup_events(raw: str) -> dict[str, int]:
    events: dict[str, int] = {}
    try:
        for line in raw.splitlines():
            name, value = line.split()
            events[name] = int(value)
    except ValueError as exc:
        raise HostConfinementError(E_C18_DRAIN, "cgroup event readback is malformed") from exc
    return events


def _open_output_entry(parent: int, name: str, directory: bool) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    if directory:
        flags |= os.O_DIRECTORY
    how = _OpenHow(flags=flags, mode=0, resolve=0x08 | 0x04 | 0x02)
    try:
        libc = ctypes.CDLL(None, use_errno=True)
        descriptor = libc.syscall(
            ctypes.c_long(SYS_OPENAT2), ctypes.c_int(parent), ctypes.c_char_p(os.fsencode(name)),
            ctypes.byref(how), ctypes.c_size_t(ctypes.sizeof(how)),
        )
        if descriptor < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error), name)
        return int(descriptor)
    except OSError as exc:
        code = E_C18_OUTPUT_RACE if exc.errno in {errno.ENOENT, errno.ESTALE} else E_C18_OUTPUT_UNSAFE
        raise HostConfinementError(code, f"unsafe output entry {name!r}: {exc}") from exc


def collect_drained_output(
    output_fd: int, limits: Mapping[str, int], cgroup_events: Mapping[str, int]
) -> dict[str, Any]:
    """Collect regular output from a held root dirfd, rejecting mutable names."""

    if cgroup_events.get("populated") != 0:
        _refuse(E_C18_DRAIN, "output collection requires exact populated 0")
    maximum_bytes = _exact_integer(limits.get("output_bytes"), "output_bytes", E_C18_OUTPUT_BOUND, minimum=1)
    maximum_inodes = _exact_integer(limits.get("output_inodes"), "output_inodes", E_C18_OUTPUT_BOUND, minimum=1)
    maximum_depth = _exact_integer(limits.get("output_depth"), "output_depth", E_C18_OUTPUT_BOUND, minimum=1)
    files: list[dict[str, Any]] = []
    total_bytes = 0
    inode_count = 0

    def walk(parent: int, prefix: str, depth: int) -> None:
        nonlocal total_bytes, inode_count
        if depth > maximum_depth:
            _refuse(E_C18_OUTPUT_BOUND, "output depth exceeded")
        try:
            entries = os.scandir(parent)
        except OSError as exc:
            raise HostConfinementError(E_C18_OUTPUT_UNSAFE, f"cannot enumerate output: {exc}") from exc
        try:
            for entry in entries:
                name = entry.name
                # Count while the directory stream is consumed: an adversary
                # cannot force an unbounded materialized name list.
                inode_count += 1
                if inode_count > maximum_inodes:
                    _refuse(E_C18_OUTPUT_BOUND, "output inode bound exceeded")
                if not name or name in {".", ".."} or "/" in name:
                    _refuse(E_C18_OUTPUT_UNSAFE, "output contains an invalid name")
                try:
                    before = os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError as exc:
                    raise HostConfinementError(E_C18_OUTPUT_RACE, "output name disappeared") from exc
                relative = f"{prefix}/{name}" if prefix else name
                if stat.S_ISDIR(before.st_mode):
                    descriptor = _open_output_entry(parent, name, True)
                    try:
                        held = os.fstat(descriptor)
                        if (held.st_dev, held.st_ino) != (before.st_dev, before.st_ino):
                            _refuse(E_C18_OUTPUT_RACE, "output directory was replaced")
                        walk(descriptor, relative, depth + 1)
                        after = os.stat(name, dir_fd=parent, follow_symlinks=False)
                        if (after.st_dev, after.st_ino) != (held.st_dev, held.st_ino):
                            _refuse(E_C18_OUTPUT_RACE, "output directory changed during collection")
                    except FileNotFoundError as exc:
                        raise HostConfinementError(E_C18_OUTPUT_RACE, "output directory disappeared") from exc
                    finally:
                        os.close(descriptor)
                    continue
                if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                    _refuse(E_C18_OUTPUT_UNSAFE, "output accepts only single-linked regular files")
                descriptor = _open_output_entry(parent, name, False)
                digest = hashlib.sha256()
                size = 0
                try:
                    held = os.fstat(descriptor)
                    if (held.st_dev, held.st_ino) != (before.st_dev, before.st_ino):
                        _refuse(E_C18_OUTPUT_RACE, "output file was replaced before read")
                    while block := os.read(descriptor, 1024 * 1024):
                        size += len(block)
                        total_bytes += len(block)
                        if total_bytes > maximum_bytes:
                            _refuse(E_C18_OUTPUT_BOUND, "output byte bound exceeded")
                        digest.update(block)
                    after_held = os.fstat(descriptor)
                    after_name = os.stat(name, dir_fd=parent, follow_symlinks=False)
                    identity = (held.st_dev, held.st_ino, held.st_size, held.st_mtime_ns, held.st_ctime_ns)
                    if identity != (
                        after_held.st_dev,
                        after_held.st_ino,
                        after_held.st_size,
                        after_held.st_mtime_ns,
                        after_held.st_ctime_ns,
                    ) or (after_name.st_dev, after_name.st_ino) != (held.st_dev, held.st_ino):
                        _refuse(E_C18_OUTPUT_RACE, "output file changed during collection")
                except FileNotFoundError as exc:
                    raise HostConfinementError(E_C18_OUTPUT_RACE, "output file disappeared") from exc
                finally:
                    os.close(descriptor)
                files.append({"path": relative, "bytes": size, "sha256": digest.hexdigest()})
        finally:
            entries.close()

    walk(output_fd, "", 0)
    files.sort(key=lambda item: item["path"])
    return {"files": files, "bytes": total_bytes, "inodes": inode_count}


def _measure_writable_tree(root: Path, limits: Mapping[str, int], label: str) -> dict[str, int]:
    """Boundedly sample live writable storage without following worker names."""

    maximum_bytes = _exact_integer(
        limits.get("output_bytes"), "output_bytes", E_C18_OUTPUT_UNSAFE, minimum=1
    )
    maximum_inodes = _exact_integer(
        limits.get("output_inodes"), "output_inodes", E_C18_OUTPUT_UNSAFE, minimum=1
    )
    maximum_depth = _exact_integer(
        limits.get("output_depth"), "output_depth", E_C18_OUTPUT_UNSAFE, minimum=1
    )
    total_bytes = 0
    inode_count = 0
    greatest_depth = 0

    def walk(directory: Path, depth: int) -> None:
        nonlocal total_bytes, inode_count, greatest_depth
        if depth > maximum_depth:
            greatest_depth = depth
            return
        try:
            entries = os.scandir(directory)
        except OSError as exc:
            raise HostConfinementError(
                E_C18_OUTPUT_UNSAFE, f"cannot measure {label}: {exc}"
            ) from exc
        try:
            for entry in entries:
                inode_count += 1
                if inode_count > maximum_inodes:
                    return
                try:
                    facts = entry.stat(follow_symlinks=False)
                except OSError as exc:
                    raise HostConfinementError(
                        E_C18_OUTPUT_UNSAFE, f"cannot stat {label} entry {entry.name!r}: {exc}"
                    ) from exc
                if stat.S_ISDIR(facts.st_mode):
                    walk(Path(entry.path), depth + 1)
                elif stat.S_ISREG(facts.st_mode) and facts.st_nlink == 1:
                    total_bytes += facts.st_size
                else:
                    _refuse(E_C18_OUTPUT_UNSAFE, f"{label} contains an unsafe live entry")
                if total_bytes > maximum_bytes:
                    return
        finally:
            entries.close()

    walk(root, 0)
    return {"bytes": total_bytes, "depth": greatest_depth, "inodes": inode_count}


def _check_live_writable_limits(descriptor: Mapping[str, Any], session: ConfinementSession) -> None:
    """Continuously enforce the output and scratch storage ceilings."""

    limits = _mapping(descriptor["limits"], "limits", E_C18_OUTPUT_UNSAFE)
    output = _measure_writable_tree(descriptor["_resolved"]["output"], limits, "output")
    scratch = _measure_writable_tree(descriptor["_resolved"]["scratch"], limits, "scratch")
    exceeded: list[str] = []
    maximum_bytes = limits["output_bytes"]
    maximum_inodes = limits["output_inodes"]
    maximum_depth = limits["output_depth"]
    for name, observed in (("output", output), ("scratch", scratch)):
        if observed["bytes"] > maximum_bytes:
            exceeded.append(f"{name}.bytes={observed['bytes']} exceeded limit={maximum_bytes}")
        if observed["inodes"] > maximum_inodes:
            exceeded.append(f"{name}.inodes={observed['inodes']} exceeded limit={maximum_inodes}")
        if observed["depth"] > maximum_depth:
            exceeded.append(f"{name}.depth={observed['depth']} exceeded limit={maximum_depth}")
    if exceeded:
        session.kill_tree()
        _refuse(E_C18_LIMIT, "; ".join(exceeded))


def confinement_result_bytes(value: Mapping[str, Any]) -> bytes:
    expected = {
        "schema", "profile_digests", "namespace_readbacks", "cgroup_readbacks",
        "command", "teardown", "outputs",
    }
    if set(value) != expected or value.get("schema") != "ranex-confinement-result-v1":
        _refuse(E_C18_RESULT, "confinement result has a missing, extra, or invalid field")
    teardown = _mapping(value.get("teardown"), "teardown", E_C18_RESULT)
    if teardown != {"cgroup_kill": True, "populated": 0, "cgroup_removed": True}:
        _refuse(E_C18_RESULT, "confinement result cannot be emitted before total teardown")
    profiles = _mapping(value.get("profile_digests"), "profile_digests", E_C18_RESULT)
    if set(profiles) != {"runtime", "host", "launcher"} or any(
        _SHA256_PATTERN.fullmatch(item) is None for item in profiles.values()
    ):
        _refuse(E_C18_RESULT, "profile digest readbacks are incomplete")
    namespaces = _mapping(value.get("namespace_readbacks"), "namespace_readbacks", E_C18_RESULT)
    if set(namespaces) != {"user", "mount", "pid", "ipc", "network", "cgroup"} or any(
        not isinstance(item, str) or not item for item in namespaces.values()
    ):
        _refuse(E_C18_RESULT, "namespace readbacks are incomplete")
    cgroup = _mapping(value.get("cgroup_readbacks"), "cgroup_readbacks", E_C18_RESULT)
    if set(cgroup) != {"limits", "events", "usage"}:
        _refuse(E_C18_RESULT, "cgroup readbacks are not closed")
    limits = _mapping(cgroup.get("limits"), "cgroup limits", E_C18_RESULT)
    events = _mapping(cgroup.get("events"), "cgroup events", E_C18_RESULT)
    usage = _mapping(cgroup.get("usage"), "cgroup usage", E_C18_RESULT)
    if (not limits or not events or not usage or set(limits) - {"pids.max", "memory.max", "cpu.max"}
        or set(events) - {"populated", "max", "oom", "oom_kill"}
        or set(usage) - {"cpu_usage_usec"} or "pids.max" not in limits
        or events.get("populated") != 0 or "cpu_usage_usec" not in usage):
        _refuse(E_C18_RESULT, "cgroup readbacks are incomplete")
    command = _mapping(value.get("command"), "command", E_C18_RESULT)
    if set(command) != {"argv_digest", "exit_code", "no_new_privs", "landlock", "seccomp"} or (
        _SHA256_PATTERN.fullmatch(command.get("argv_digest", "")) is None
        or type(command.get("exit_code")) is not int
        or any(command.get(name) is not True for name in ("no_new_privs", "landlock", "seccomp"))
    ):
        _refuse(E_C18_RESULT, "command readbacks are incomplete")
    outputs = _mapping(value.get("outputs"), "outputs", E_C18_RESULT)
    if set(outputs) != {"files", "bytes", "inodes"} or type(outputs["files"]) is not list or any(
        type(outputs[name]) is not int or outputs[name] < 0 for name in ("bytes", "inodes")
    ) or any(not isinstance(item, dict) or set(item) != {"path", "bytes", "sha256"}
             or not isinstance(item["path"], str) or not item["path"]
             or type(item["bytes"]) is not int or item["bytes"] < 0
             or _SHA256_PATTERN.fullmatch(item["sha256"]) is None for item in outputs["files"]):
        _refuse(E_C18_RESULT, "output readbacks are invalid")
    return canonical_json_bytes(value)


def launcher_install(
    root: Path, manifest_arg: str, artifact_arg: str, destination_arg: str
) -> None:
    if artifact_arg != BUILD_ARTIFACT_ARGUMENT or destination_arg != INSTALLED_ARTIFACT_ARGUMENT:
        _refuse(E_INSTALL, "artifact or destination is not an admitted launcher path")
    manifest_path = resolve_within_repository(root, manifest_arg)
    artifact_path = (
        (root / artifact_arg).absolute()
        if not Path(artifact_arg).is_absolute()
        else Path(artifact_arg)
    )
    destination = (
        (root / destination_arg).absolute()
        if not Path(destination_arg).is_absolute()
        else Path(destination_arg)
    )
    manifest = _load_json(manifest_path, E_INSTALL)
    _build, _source, artifact = _manifest_sections(manifest, E_INSTALL)
    expected = _digest(artifact.get("sha256"), "artifact.sha256", E_INSTALL)
    expected_elf = _mapping(artifact.get("elf"), "artifact.elf", E_INSTALL)
    opened = _open_verified(
        artifact_path,
        expected,
        code=E_INSTALL,
        exact_mode=0o555,
        required_owner=os.geteuid(),
    )
    try:
        try:
            facts = _elf_facts_from_descriptor(opened.descriptor, artifact_path)
        except HostConfinementError as exc:
            raise HostConfinementError(E_INSTALL, exc.detail) from exc
        if facts != expected_elf:
            _refuse(E_INSTALL, "staging artifact ELF facts differ from manifest")
        try:
            parent = _open_created_directory(root, destination.parent)
        except OSError as exc:
            raise HostConfinementError(E_INSTALL, f"cannot open install parent: {exc}") from exc
        temporary_name = f".{destination.name}.{uuid.uuid4().hex}"
        staged = -1
        try:
            staged = os.open(
                temporary_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
                0o555,
                dir_fd=parent,
            )
            while block := os.read(opened.descriptor, 1024 * 1024):
                view = memoryview(block)
                while view:
                    written = os.write(staged, view)
                    view = view[written:]
            os.fsync(staged)
            installed_facts = os.fstat(staged)
            if stat.S_IMODE(installed_facts.st_mode) != 0o555:
                _refuse(E_INSTALL, "install staging mode is not 0555")
            _rename_noreplace(parent, temporary_name, destination.name)
            _fsync_publication_or_rollback(
                parent,
                destination.name,
                failure_code=E_INSTALL,
                context="launcher install",
            )
        except OSError as exc:
            raise HostConfinementError(E_INSTALL, f"atomic install refused: {exc}") from exc
        finally:
            if staged >= 0:
                os.close(staged)
            try:
                _cleanup_temporary(parent, temporary_name, "launcher install")
            finally:
                os.close(parent)
    finally:
        os.close(opened.descriptor)


def _read_status() -> dict[str, int]:
    try:
        text = Path("/proc/self/status").read_text(encoding="utf-8")
    except OSError as exc:
        raise HostConfinementError(E_FACT, f"cannot read seccomp/NoNewPrivs status: {exc}") from exc
    result: dict[str, int] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        name, raw = line.split(":", 1)
        if name in {"NoNewPrivs", "Seccomp", "Seccomp_filters"}:
            try:
                result[name] = int(raw.strip())
            except ValueError as exc:
                raise HostConfinementError(E_FACT, f"invalid {name} in /proc/self/status") from exc
    missing = {"NoNewPrivs", "Seccomp", "Seccomp_filters"} - set(result)
    if missing:
        _refuse(E_FACT, f"seccomp/NoNewPrivs fields are missing: {sorted(missing)}")
    return result


def _landlock_abi() -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(
        ctypes.c_long(SYS_LANDLOCK_CREATE_RULESET),
        ctypes.c_void_p(),
        ctypes.c_size_t(0),
        ctypes.c_uint(1),
    )
    if result < 6:
        error = ctypes.get_errno()
        _refuse(E_FACT, f"landlock ABI is unavailable or below 6 (result={result}, errno={error})")
    return int(result)


class _OpenHow(ctypes.Structure):
    _fields_ = [
        ("flags", ctypes.c_ulonglong),
        ("mode", ctypes.c_ulonglong),
        ("resolve", ctypes.c_ulonglong),
    ]


def _probe_openat2() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    how = _OpenHow(flags=os.O_RDONLY | os.O_CLOEXEC, mode=0, resolve=0)
    descriptor = libc.syscall(
        ctypes.c_long(SYS_OPENAT2),
        ctypes.c_int(AT_FDCWD),
        ctypes.c_char_p(b"/proc/self/status"),
        ctypes.byref(how),
        ctypes.c_size_t(ctypes.sizeof(how)),
    )
    if descriptor < 0:
        error = ctypes.get_errno()
        _refuse(E_FACT, f"openat2 probe failed with errno {error}")
    os.close(descriptor)


def _write_namespace_map(path: str, value: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CLOEXEC)
    try:
        data = value.encode()
        if os.write(descriptor, data) != len(data):
            raise OSError(errno.EIO, "short namespace-map write", path)
    finally:
        os.close(descriptor)


def _namespace_child(name: str, flag: int, result_descriptor: int) -> NoReturn:
    libc = ctypes.CDLL(None, use_errno=True)
    namespace_name = {"mount": "mnt", "network": "net"}.get(name, name)

    def fail(stage: str, error: int) -> NoReturn:
        detail = f"{stage}:{error}".encode()
        try:
            os.write(result_descriptor, detail)
        finally:
            os._exit(126)

    try:
        before = os.readlink(f"/proc/self/ns/{namespace_name}")
    except OSError as exc:
        fail("observe-before", exc.errno or errno.EIO)
    if name != "user":
        uid = os.getuid()
        gid = os.getgid()
        if libc.unshare(ctypes.c_int(CLONE_NEWUSER)) != 0:
            fail("unshare-user", ctypes.get_errno())
        try:
            _write_namespace_map("/proc/self/setgroups", "deny\n")
            _write_namespace_map("/proc/self/uid_map", f"0 {uid} 1\n")
            _write_namespace_map("/proc/self/gid_map", f"0 {gid} 1\n")
        except OSError as exc:
            fail("map-user", exc.errno or errno.EIO)
    if libc.unshare(ctypes.c_int(flag)) != 0:
        fail("unshare", ctypes.get_errno())
    if name == "pid":
        try:
            observer = os.fork()
        except OSError as exc:
            fail("fork-observer", exc.errno or errno.EIO)
        if observer != 0:
            waited, status = os.waitpid(observer, 0)
            if (
                waited != observer
                or not os.WIFEXITED(status)
                or os.WEXITSTATUS(status) != 0
            ):
                os._exit(126)
            os._exit(0)
    try:
        after = os.readlink(f"/proc/self/ns/{namespace_name}")
    except OSError as exc:
        fail("observe-after", exc.errno or errno.EIO)
    if before == after:
        fail("unchanged", errno.EIO)
    os.write(result_descriptor, b"ok")
    os._exit(0)


def _probe_namespaces() -> dict[str, bool]:
    result: dict[str, bool] = {}
    for name, flag in NAMESPACE_FLAGS.items():
        result_read, result_write = os.pipe2(os.O_CLOEXEC)
        pid = os.fork()
        if pid == 0:
            os.close(result_read)
            _namespace_child(name, flag, result_write)
        os.close(result_write)
        observation = os.read(result_read, 256).decode(errors="replace")
        os.close(result_read)
        waited, status = os.waitpid(pid, 0)
        if (
            waited != pid
            or not os.WIFEXITED(status)
            or os.WEXITSTATUS(status) != 0
            or observation != "ok"
        ):
            _refuse(E_FACT, f"{name} namespace probe was unavailable ({observation})")
        result[name] = True
    return result


def _current_cgroup_root() -> tuple[Path, str]:
    try:
        lines = Path("/proc/self/cgroup").read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise HostConfinementError(E_FACT, f"cannot read /proc/self/cgroup: {exc}") from exc
    unified = [line.split("::", 1)[1] for line in lines if "::" in line]
    if len(unified) != 1 or not unified[0].startswith("/"):
        _refuse(E_FACT, "cannot resolve the unified cgroup from /proc/self/cgroup")
    relative = unified[0]
    root = Path("/sys/fs/cgroup") / relative.lstrip("/")
    return root, relative


def _statfs_type(path: Path) -> int:
    buffer = ctypes.create_string_buffer(256)
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.statfs(ctypes.c_char_p(os.fsencode(path)), ctypes.byref(buffer))
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), path)
    return int(ctypes.c_long.from_buffer(buffer).value)


def _cgroup_controllers(root: Path) -> list[str]:
    try:
        controllers = sorted((root / "cgroup.controllers").read_text().split())
    except OSError as exc:
        raise HostConfinementError(E_DELEGATION, f"cannot read cgroup controllers: {exc}") from exc
    return controllers


def _check_cgroup_kill(root: Path) -> None:
    target = root / "cgroup.kill"
    try:
        filesystem_type = _statfs_type(target)
    except OSError as exc:
        code = E_FACT if exc.errno in {errno.ENOENT, errno.ENOTDIR} else E_DELEGATION
        raise HostConfinementError(code, f"cannot inspect cgroup.kill at {target}: {exc}") from exc
    if filesystem_type != CGROUP2_SUPER_MAGIC:
        _refuse(E_FACT, f"cgroup.kill at {target} is not on cgroup2")
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        os.close(descriptor)
    except OSError as exc:
        code = E_FACT if exc.errno in {errno.ENOENT, errno.ENOTDIR} else E_DELEGATION
        raise HostConfinementError(code, f"cannot open cgroup.kill at {target}: {exc}") from exc


def _write_control(path: Path, value: str) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        data = value.encode()
        if os.write(descriptor, data) != len(data):
            raise OSError(errno.EIO, "short cgroup write", path)
    finally:
        os.close(descriptor)


def _move_all_cgroup_processes(source: Path, target: Path) -> None:
    deadline = time.monotonic() + 5.0
    while True:
        processes = {int(value) for value in (source / "cgroup.procs").read_text().split()}
        if not processes:
            return
        for process in sorted(processes, key=lambda value: (value == os.getpid(), value)):
            try:
                _write_control(target / "cgroup.procs", f"{process}\n")
            except OSError as exc:
                if exc.errno != errno.ESRCH:
                    raise
        if time.monotonic() >= deadline:
            raise OSError(errno.EBUSY, "could not drain cgroup processes", source)
        time.sleep(0.001)


def _real_cgroup_probe(root: Path) -> dict[str, Any]:
    controllers = _cgroup_controllers(root)
    missing = sorted(REQUIRED_CONTROLLERS - set(controllers))
    if missing:
        _refuse(E_FACT, f"cgroup delegation is missing controllers: {', '.join(missing)}")
    _check_cgroup_kill(root)
    try:
        initial_enabled = set((root / "cgroup.subtree_control").read_text().split())
    except OSError as exc:
        raise HostConfinementError(
            E_DELEGATION, f"cannot read initial cgroup.subtree_control: {exc}"
        ) from exc
    requested_delta = REQUIRED_CONTROLLERS - initial_enabled
    suffix = f"{os.getpid()}-{uuid.uuid4().hex[:10]}"
    control = root / f"ranex-ctl-{suffix}"
    worker = root / f"ranex-worker-{suffix}"
    child = -1
    transcript: dict[str, Any] = {
        "cgroup_path": str(worker),
        "child_pid": 0,
        "controllers_enabled": [],
        "created": False,
        "memory_max": 134_217_728,
        "read_back_pids": [],
        "removed": False,
    }
    primary: HostConfinementError | OSError | None = None
    try:
        control.mkdir(mode=0o755)
        _move_all_cgroup_processes(root, control)
        if requested_delta:
            enable_text = " ".join(f"+{controller}" for controller in sorted(requested_delta))
            _write_control(root / "cgroup.subtree_control", enable_text + "\n")
        worker.mkdir(mode=0o755)
        transcript["created"] = True
        actual_enabled = sorted((root / "cgroup.subtree_control").read_text().split())
        if not REQUIRED_CONTROLLERS <= set(actual_enabled):
            _refuse(E_DELEGATION, "required cgroup controllers did not enable")
        transcript["controllers_enabled"] = actual_enabled
        _write_control(worker / "memory.max", "134217728\n")
        if (worker / "memory.max").read_text().strip() != "134217728":
            _refuse(E_DELEGATION, "memory.max did not read back exactly")
        child = os.fork()
        if child == 0:
            signal.pause()
            os._exit(0)
        transcript["child_pid"] = child
        _write_control(worker / "cgroup.procs", f"{child}\n")
        read_back = sorted(int(value) for value in (worker / "cgroup.procs").read_text().split())
        transcript["read_back_pids"] = read_back
        if child not in read_back:
            _refuse(E_DELEGATION, "probe child did not read back from its cgroup")
        time.sleep(0.08)
        _write_control(worker / "cgroup.kill", "1\n")
        waited, status = os.waitpid(child, 0)
        child = -1
        if waited <= 0 or not os.WIFSIGNALED(status) or os.WTERMSIG(status) != signal.SIGKILL:
            _refuse(E_DELEGATION, "cgroup.kill did not SIGKILL the probe child")
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            events = (worker / "cgroup.events").read_text()
            if "populated 0" in events:
                break
            time.sleep(0.01)
        else:
            _refuse(E_CLEANUP, "probe cgroup remained populated after cgroup.kill")
    except HostConfinementError as exc:
        primary = exc
    except OSError as exc:
        primary = exc
    cleanup_errors: list[str] = []
    if child > 0:
        try:
            os.kill(child, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            os.waitpid(child, 0)
        except ChildProcessError:
            pass
    if worker.exists():
        try:
            worker.rmdir()
        except OSError as exc:
            cleanup_errors.append(f"remove worker: {exc}")
    if requested_delta:
        try:
            current_enabled = set((root / "cgroup.subtree_control").read_text().split())
            disable_delta = requested_delta & current_enabled
            if disable_delta:
                disable_text = " ".join(f"-{controller}" for controller in sorted(disable_delta))
                _write_control(root / "cgroup.subtree_control", disable_text + "\n")
        except OSError as exc:
            cleanup_errors.append(f"disable controllers: {exc}")
    if control.exists():
        try:
            _move_all_cgroup_processes(control, root)
        except OSError as exc:
            cleanup_errors.append(f"return controller processes: {exc}")
    if control.exists():
        try:
            control.rmdir()
        except OSError as exc:
            cleanup_errors.append(f"remove controller cgroup: {exc}")
    if cleanup_errors:
        _refuse(E_CLEANUP, "; ".join(cleanup_errors))
    transcript["removed"] = True
    if primary is not None:
        if isinstance(primary, HostConfinementError):
            raise primary
        raise HostConfinementError(
            E_DELEGATION, f"real cgroup probe failed: {primary}"
        ) from primary
    return transcript


def _host_architecture() -> tuple[str, str]:
    machine = os.uname().machine
    release = os.uname().release
    if machine != "x86_64":
        _refuse(E_ARCH, f"architecture {machine!r} is not the recorded x86_64 target")
    return machine, release


def _require_executable_elf(descriptor: int, facts: os.stat_result, path: Path) -> None:
    header = os.pread(descriptor, 64, 0)
    if (
        facts.st_size < 64
        or len(header) != 64
        or header[:7] != b"\x7fELF\x02\x01\x01"
    ):
        _refuse(E_FACT, f"bubblewrap is not a valid ELF64 object at {path}")
    (
        elf_type,
        machine,
        version,
        entry,
        program_offset,
        _section_offset,
        _flags,
        header_size,
        program_size,
        program_count,
        _section_size,
        _section_count,
        _section_names,
    ) = struct.unpack_from("<HHIQQQIHHHHHH", header, 16)
    program_end = program_offset + program_size * program_count
    if (
        elf_type not in {2, 3}
        or machine != 62
        or version != 1
        or header_size != 64
        or program_size != 56
        or program_count == 0
        or program_size * program_count > 65_536
        or program_end > facts.st_size
    ):
        _refuse(E_FACT, f"bubblewrap has an invalid x86-64 ELF header at {path}")
    executable_load = False
    for index in range(program_count):
        offset = program_offset + index * program_size
        program = os.pread(descriptor, 56, offset)
        if len(program) != 56:
            _refuse(E_FACT, f"bubblewrap has a truncated ELF program table at {path}")
        kind, flags = struct.unpack_from("<II", program)
        file_offset, virtual_address = struct.unpack_from("<QQ", program, 8)
        file_size, memory_size = struct.unpack_from("<QQ", program, 32)
        if file_offset + file_size > facts.st_size or file_size > memory_size:
            _refuse(E_FACT, f"bubblewrap has an invalid ELF segment at {path}")
        if (
            kind == 1
            and flags & 1
            and virtual_address <= entry < virtual_address + memory_size
        ):
            executable_load = True
    if not executable_load:
        _refuse(E_FACT, f"bubblewrap has no executable ELF load segment at {path}")


def _inspect_bubblewrap() -> dict[str, Any]:
    try:
        facts = BUBBLEWRAP.lstat()
        if stat.S_ISLNK(facts.st_mode) or not stat.S_ISREG(facts.st_mode):
            _refuse(E_FACT, f"bubblewrap is not a non-symlink regular file at {BUBBLEWRAP}")
        descriptor = os.open(BUBBLEWRAP, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            descriptor_facts = os.fstat(descriptor)
            mode = stat.S_IMODE(descriptor_facts.st_mode)
            if (descriptor_facts.st_dev, descriptor_facts.st_ino) != (facts.st_dev, facts.st_ino):
                _refuse(E_FACT, "bubblewrap changed while it was opened")
            if mode & 0o111 == 0:
                _refuse(E_FACT, f"bubblewrap is not executable at {BUBBLEWRAP}")
            if descriptor_facts.st_size <= 0:
                _refuse(E_FACT, f"bubblewrap is empty at {BUBBLEWRAP}")
            _require_executable_elf(descriptor, descriptor_facts, BUBBLEWRAP)
            _require_trusted_owner_and_mode(
                BUBBLEWRAP, descriptor_facts, mode, E_FACT
            )
            digest = _sha256_descriptor(descriptor)
            if _capability_xattr(descriptor):
                _refuse(E_FACT, f"bubblewrap carries file capabilities at {BUBBLEWRAP}")
            filesystem = _mount_provenance(BUBBLEWRAP, descriptor, E_FACT)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise HostConfinementError(
            E_FACT, f"bubblewrap is unavailable at {BUBBLEWRAP}: {exc}"
        ) from exc
    return {
        "capabilities": False,
        "device": descriptor_facts.st_dev,
        "filesystem": filesystem,
        "gid": descriptor_facts.st_gid,
        "inode": descriptor_facts.st_ino,
        "mode": mode,
        "owner": descriptor_facts.st_uid,
        "path": str(BUBBLEWRAP),
        "sha256": digest,
    }


def _required_host_text(path: Path, field: str, *, limit: int = 65_536) -> str:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            raw = os.read(descriptor, limit + 1)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise HostConfinementError(E_FACT, f"cannot read host-state {field} at {path}: {exc}") from exc
    if len(raw) > limit:
        _refuse(E_FACT, f"host-state {field} at {path} exceeds {limit} bytes")
    try:
        value = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise HostConfinementError(E_FACT, f"host-state {field} at {path} is not UTF-8") from exc
    if not value:
        _refuse(E_FACT, f"host-state {field} at {path} is empty")
    return value


def _apparmor_policy_identity(active_lsms: set[str]) -> dict[str, str]:
    if "apparmor" not in active_lsms:
        return {"status": "inactive"}
    return {
        "status": "active",
        "enabled": _required_host_text(
            Path("/sys/module/apparmor/parameters/enabled"), "AppArmor enabled state"
        ),
        "namespace": _required_host_text(
            Path("/sys/kernel/security/apparmor/.ns_name"), "AppArmor policy namespace"
        ),
        "revision": _required_host_text(
            Path("/sys/kernel/security/apparmor/revision"), "AppArmor policy revision"
        ),
        "current_profile": _required_host_text(
            Path("/proc/self/attr/apparmor/current"), "AppArmor current profile"
        ),
    }


def _selinux_policy_identity(active_lsms: set[str]) -> dict[str, str]:
    if "selinux" not in active_lsms:
        return {"status": "inactive"}
    policy = Path("/sys/fs/selinux/policy")
    try:
        policy_digest = _sha256_path(policy)
    except OSError as exc:
        raise HostConfinementError(
            E_FACT, f"cannot digest active SELinux policy at {policy}: {exc}"
        ) from exc
    return {
        "status": "active",
        "policy_sha256": policy_digest,
        "policy_version": _required_host_text(
            Path("/sys/fs/selinux/policyvers"), "SELinux policy version"
        ),
        "enforcing": _required_host_text(
            Path("/sys/fs/selinux/enforce"), "SELinux enforcing state"
        ),
        "current_context": _required_host_text(
            Path("/proc/self/attr/selinux/current"), "SELinux current context"
        ),
    }


def _parent_namespace_id(value: int, *, kind: str) -> int:
    try:
        mapping = Path(f"/proc/self/{kind}_map").read_text(encoding="utf-8").splitlines()
        ranges = [tuple(int(field) for field in line.split()) for line in mapping]
    except (OSError, ValueError) as exc:
        raise HostConfinementError(E_FACT, f"cannot resolve parent {kind} identity: {exc}") from exc
    if any(len(fields) != 3 for fields in ranges):
        _refuse(E_FACT, f"parent {kind} identity map is malformed")
    for inside, outside, length in ranges:
        if inside <= value < inside + length:
            return outside + value - inside
    _refuse(E_FACT, f"{kind} {value} has no parent-namespace identity")


def _in_initial_user_namespace() -> bool:
    try:
        mapping = Path("/proc/self/uid_map").read_text(encoding="utf-8").splitlines()
        ranges = [tuple(int(field) for field in line.split()) for line in mapping]
    except (OSError, ValueError) as exc:
        raise HostConfinementError(E_FACT, f"cannot identify current user namespace: {exc}") from exc
    if any(len(fields) != 3 for fields in ranges):
        _refuse(E_FACT, "current user-namespace uid map is malformed")
    return ranges == [(0, 0, 4_294_967_295)]


def _unprivileged_userns_sysctls() -> dict[str, str]:
    sysctls: dict[str, str] = {}
    for name, path in (
        ("kernel.unprivileged_userns_clone", Path("/proc/sys/kernel/unprivileged_userns_clone")),
        ("user.max_user_namespaces", Path("/proc/sys/user/max_user_namespaces")),
    ):
        if path.exists():
            sysctls[name] = _required_host_text(path, name)
    if "user.max_user_namespaces" not in sysctls:
        _refuse(E_FACT, "mandatory user.max_user_namespaces host state is unavailable")
    return sysctls


def _collect_host_state(
    probe_cgroup: Mapping[str, Any],
    *,
    delegation_source: str,
    userns_sysctls: Mapping[str, Any],
    userns_source: str,
) -> dict[str, Any]:
    lsm_text = _required_host_text(Path("/sys/kernel/security/lsm"), "active LSM list")
    active_lsms = {name.strip() for name in lsm_text.split(",") if name.strip()}
    if not active_lsms:
        _refuse(E_FACT, "active LSM list contains no identities")
    sysctls = {
        _string(name, "userns sysctl name", E_FACT): _string(
            value, f"userns sysctl {name}", E_FACT
        )
        for name, value in userns_sysctls.items()
    }
    if set(sysctls) not in (
        {"user.max_user_namespaces"},
        {"kernel.unprivileged_userns_clone", "user.max_user_namespaces"},
    ):
        _refuse(E_FACT, "unprivileged-userns sysctl set is invalid")
    cgroup_root = _string(probe_cgroup.get("root"), "host-probe.cgroup.root", E_FACT)
    relative_path = _string(
        probe_cgroup.get("relative_path"), "host-probe.cgroup.relative_path", E_FACT
    )
    return {
        "lsm": {
            "securityfs_lsm": lsm_text,
            "apparmor_policy_identity": _apparmor_policy_identity(active_lsms),
            "selinux_policy_identity": _selinux_policy_identity(active_lsms),
        },
        "unprivileged_userns_sysctls": sysctls,
        "boot_id": _required_host_text(
            Path("/proc/sys/kernel/random/boot_id"), "boot ID"
        ),
        "machine_id": _required_host_text(Path("/etc/machine-id"), "machine ID"),
        "delegation_identity": {
            "uid": _parent_namespace_id(os.geteuid(), kind="uid"),
            "gid": _parent_namespace_id(os.getegid(), kind="gid"),
            "cgroup_root": cgroup_root,
            "cgroup_relative_path": relative_path,
            "source": delegation_source,
            "userns_state_source": userns_source,
        },
    }


def collect_host_probe() -> dict[str, Any]:
    machine, release = _host_architecture()
    status = _read_status()
    landlock = _landlock_abi()
    _probe_openat2()
    namespaces = _probe_namespaces()
    bubblewrap = _inspect_bubblewrap()
    cgroup_root, relative = _current_cgroup_root()
    try:
        if _statfs_type(cgroup_root) != CGROUP2_SUPER_MAGIC:
            _refuse(E_FACT, f"cgroup root {cgroup_root} is not cgroup2")
    except OSError as exc:
        raise HostConfinementError(E_FACT, f"cannot inspect cgroup2 mount: {exc}") from exc
    controllers = _cgroup_controllers(cgroup_root)
    transcript = _real_cgroup_probe(cgroup_root)
    return {
        "cgroup": {
            "cgroup_kill": {
                "available": True,
                "filesystem": "cgroup2",
                "filesystem_magic": CGROUP2_SUPER_MAGIC,
                "path": str(cgroup_root / "cgroup.kill"),
            },
            "controllers": controllers,
            "mount": "/sys/fs/cgroup",
            "relative_path": relative,
            "root": str(cgroup_root),
            "probe_transcript": transcript,
        },
        "helpers": {"bubblewrap": bubblewrap},
        "host": {
            "architecture": machine,
            "kernel_release": release,
            "landlock_abi": landlock,
            "namespaces": namespaces,
            "no_new_privs": status["NoNewPrivs"],
            "openat2": True,
            "seccomp": status["Seccomp"],
            "seccomp_filters": status["Seccomp_filters"],
            "unprivileged_userns_sysctls": _unprivileged_userns_sysctls(),
        },
    }


def _exact_keys(value: Mapping[str, Any], expected: set[str], field: str, code: str) -> None:
    if set(value) != expected:
        _refuse(code, f"{field} has missing or extra fields")


def _exact_integer(value: Any, field: str, code: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _refuse(code, f"{field} must be an integer >= {minimum}")
    return value


def _string_list(value: Any, field: str, code: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        _refuse(code, f"{field} must be a list of non-empty strings")
    if value != sorted(set(value)):
        _refuse(code, f"{field} must be sorted and duplicate-free")
    return value


def _validate_filesystem(value: Any, field: str, code: str) -> dict[str, Any]:
    filesystem = _mapping(value, field, code)
    _exact_keys(
        filesystem,
        {"device", "filesystem", "mount_id", "mount_point", "options", "source"},
        field,
        code,
    )
    for name in ("device", "filesystem", "mount_point", "source"):
        _string(filesystem.get(name), f"{field}.{name}", code)
    _exact_integer(filesystem.get("mount_id"), f"{field}.mount_id", code, minimum=1)
    _string_list(filesystem.get("options"), f"{field}.options", code)
    if "noexec" in filesystem["options"]:
        _refuse(code, f"{field} unexpectedly records a noexec mount")
    return filesystem


def _validate_host_probe(value: Mapping[str, Any], code: str) -> dict[str, Any]:
    _exact_keys(value, {"cgroup", "helpers", "host"}, "host-probe", code)
    cgroup = _mapping(value.get("cgroup"), "host-probe.cgroup", code)
    _exact_keys(
        cgroup,
        {
            "cgroup_kill",
            "controllers",
            "mount",
            "probe_transcript",
            "relative_path",
            "root",
        },
        "host-probe.cgroup",
        code,
    )
    controllers = _string_list(cgroup.get("controllers"), "host-probe.cgroup.controllers", code)
    if not REQUIRED_CONTROLLERS <= set(controllers):
        _refuse(code, "host-probe cgroup controllers omit a mandatory controller")
    if cgroup.get("mount") != "/sys/fs/cgroup":
        _refuse(code, "host-probe cgroup mount is not /sys/fs/cgroup")
    _string(cgroup.get("relative_path"), "host-probe.cgroup.relative_path", code)
    _string(cgroup.get("root"), "host-probe.cgroup.root", code)
    cgroup_kill = _mapping(cgroup.get("cgroup_kill"), "host-probe.cgroup.cgroup_kill", code)
    _exact_keys(
        cgroup_kill,
        {"available", "filesystem", "filesystem_magic", "path"},
        "host-probe.cgroup.cgroup_kill",
        code,
    )
    if (
        cgroup_kill.get("available") is not True
        or cgroup_kill.get("filesystem") != "cgroup2"
        or cgroup_kill.get("filesystem_magic") != CGROUP2_SUPER_MAGIC
    ):
        _refuse(code, "host-probe cgroup.kill provenance is invalid")
    _string(cgroup_kill.get("path"), "host-probe.cgroup.cgroup_kill.path", code)
    transcript = _mapping(
        cgroup.get("probe_transcript"), "host-probe.cgroup.probe_transcript", code
    )
    _exact_keys(
        transcript,
        {
            "cgroup_path",
            "child_pid",
            "controllers_enabled",
            "created",
            "memory_max",
            "read_back_pids",
            "removed",
        },
        "host-probe.cgroup.probe_transcript",
        code,
    )
    child = _exact_integer(
        transcript.get("child_pid"),
        "host-probe.cgroup.probe_transcript.child_pid",
        code,
        minimum=2,
    )
    enabled = _string_list(
        transcript.get("controllers_enabled"),
        "host-probe.cgroup.probe_transcript.controllers_enabled",
        code,
    )
    if not REQUIRED_CONTROLLERS <= set(enabled):
        _refuse(code, "host-probe transcript did not enable mandatory controllers")
    read_back = transcript.get("read_back_pids")
    if (
        not isinstance(read_back, list)
        or any(type(pid) is not int or pid <= 1 for pid in read_back)
        or read_back != sorted(set(read_back))
        or child not in read_back
    ):
        _refuse(code, "host-probe transcript has invalid child PID read-back")
    if (
        transcript.get("created") is not True
        or transcript.get("removed") is not True
        or transcript.get("memory_max") != 134_217_728
    ):
        _refuse(code, "host-probe transcript is incomplete")
    _string(
        transcript.get("cgroup_path"),
        "host-probe.cgroup.probe_transcript.cgroup_path",
        code,
    )

    helpers = _mapping(value.get("helpers"), "host-probe.helpers", code)
    _exact_keys(helpers, {"bubblewrap"}, "host-probe.helpers", code)
    bubblewrap = _mapping(helpers.get("bubblewrap"), "host-probe.helpers.bubblewrap", code)
    _exact_keys(
        bubblewrap,
        {
            "capabilities",
            "device",
            "filesystem",
            "gid",
            "inode",
            "mode",
            "owner",
            "path",
            "sha256",
        },
        "host-probe.helpers.bubblewrap",
        code,
    )
    if bubblewrap.get("capabilities") is not False or bubblewrap.get("path") != str(BUBBLEWRAP):
        _refuse(code, "host-probe bubblewrap provenance is invalid")
    _digest(bubblewrap.get("sha256"), "host-probe.helpers.bubblewrap.sha256", code)
    _exact_integer(bubblewrap.get("device"), "host-probe.helpers.bubblewrap.device", code)
    _exact_integer(bubblewrap.get("gid"), "host-probe.helpers.bubblewrap.gid", code)
    _exact_integer(
        bubblewrap.get("inode"), "host-probe.helpers.bubblewrap.inode", code, minimum=1
    )
    _exact_integer(bubblewrap.get("mode"), "host-probe.helpers.bubblewrap.mode", code)
    _exact_integer(bubblewrap.get("owner"), "host-probe.helpers.bubblewrap.owner", code)
    _validate_filesystem(
        bubblewrap.get("filesystem"), "host-probe.helpers.bubblewrap.filesystem", code
    )

    host = _mapping(value.get("host"), "host-probe.host", code)
    _exact_keys(
        host,
        {
            "architecture",
            "kernel_release",
            "landlock_abi",
            "namespaces",
            "no_new_privs",
            "openat2",
            "seccomp",
            "seccomp_filters",
            "unprivileged_userns_sysctls",
        },
        "host-probe.host",
        code,
    )
    if host.get("architecture") != "x86_64" or host.get("openat2") is not True:
        _refuse(code, "host-probe architecture or openat2 fact is invalid")
    _string(host.get("kernel_release"), "host-probe.host.kernel_release", code)
    _exact_integer(host.get("landlock_abi"), "host-probe.host.landlock_abi", code, minimum=6)
    _exact_integer(host.get("no_new_privs"), "host-probe.host.no_new_privs", code)
    _exact_integer(host.get("seccomp"), "host-probe.host.seccomp", code)
    _exact_integer(host.get("seccomp_filters"), "host-probe.host.seccomp_filters", code)
    namespaces = _mapping(host.get("namespaces"), "host-probe.host.namespaces", code)
    _exact_keys(namespaces, set(NAMESPACE_FLAGS), "host-probe.host.namespaces", code)
    if any(namespaces.get(name) is not True for name in NAMESPACE_FLAGS):
        _refuse(code, "host-probe namespace fact is not true")
    sysctls = _mapping(
        host.get("unprivileged_userns_sysctls"),
        "host-probe.host.unprivileged_userns_sysctls",
        code,
    )
    if set(sysctls) not in (
        {"user.max_user_namespaces"},
        {"kernel.unprivileged_userns_clone", "user.max_user_namespaces"},
    ):
        _refuse(code, "host-probe unprivileged-userns sysctl set is invalid")
    for name, sysctl_value in sysctls.items():
        _string(sysctl_value, f"host-probe userns sysctl {name}", code)
    return dict(value)


def _broker_endpoint(runtime_uid: int | None = None) -> BrokerEndpoint:
    uid = os.geteuid() if runtime_uid is None else runtime_uid
    expected_owner = os.geteuid()
    runtime = Path("/run/user") / str(uid)
    bus = runtime / "bus"
    try:
        runtime_facts = runtime.lstat()
        bus_facts = bus.lstat()
    except OSError as exc:
        raise HostConfinementError(
            E_DELEGATION, f"derived user broker endpoint is unavailable: {exc}"
        ) from exc
    if stat.S_ISLNK(runtime_facts.st_mode) or not stat.S_ISDIR(runtime_facts.st_mode):
        _refuse(E_DELEGATION, f"derived runtime path {runtime} is not a non-symlink directory")
    if runtime_facts.st_uid != expected_owner:
        _refuse(E_DELEGATION, f"derived runtime path {runtime} has the wrong owner")
    if stat.S_ISLNK(bus_facts.st_mode) or not stat.S_ISSOCK(bus_facts.st_mode):
        _refuse(E_DELEGATION, f"derived bus path {bus} is not a non-symlink socket")
    if bus_facts.st_uid != expected_owner:
        _refuse(E_DELEGATION, f"derived bus path {bus} has the wrong owner")
    return BrokerEndpoint(
        runtime=runtime,
        bus=bus,
        runtime_mode=stat.S_IMODE(runtime_facts.st_mode),
        bus_mode=stat.S_IMODE(bus_facts.st_mode),
    )


def _broker_record(
    endpoint: BrokerEndpoint | None,
    *,
    status: str,
    attempted: bool,
    argv: Sequence[str] = (),
    executable_digest: str = "",
) -> dict[str, Any]:
    runtime = endpoint.runtime if endpoint is not None else Path("/run/user") / str(os.geteuid())
    bus = endpoint.bus if endpoint is not None else runtime / "bus"
    return {
        "argv": list(argv),
        "argv_digest": command_digest(argv) if argv else "",
        "attempted": attempted,
        "bus": {
            "address": f"unix:path={bus}",
            "mode": endpoint.bus_mode if endpoint is not None else None,
            "path": str(bus),
        },
        "capabilities": None,
        "executable_digest": executable_digest,
        "filesystem": None,
        "mode": None,
        "owner": None,
        "python_executable": None,
        "python_executable_digest": "",
        "runtime_dir": {
            "mode": endpoint.runtime_mode if endpoint is not None else None,
            "path": str(runtime),
        },
        "status": status,
    }


def _helper_pin(profile: Mapping[str, Any], name: str) -> tuple[Path, str]:
    helpers = _mapping(profile.get("helpers"), "profile.helpers", E_EXEC)
    helper = _mapping(helpers.get(name), f"profile.helpers.{name}", E_EXEC)
    path = Path(_string(helper.get("path"), f"profile.helpers.{name}.path", E_EXEC))
    if not path.is_absolute():
        _refuse(E_EXEC, f"profile helper {name} path must be absolute")
    digest = _digest(helper.get("sha256"), f"profile.helpers.{name}.sha256", E_EXEC)
    return path, digest


def _run_broker_probe(
    root: Path,
    profile: Mapping[str, Any],
    endpoint: BrokerEndpoint,
) -> tuple[dict[str, Any], dict[str, Any]]:
    systemd_path, systemd_digest = _helper_pin(profile, "systemd_run")
    if systemd_path != SYSTEMD_RUN:
        _refuse(E_DELEGATION, "profile does not pin the frozen systemd-run path")
    try:
        systemd_object = _open_verified(systemd_path, systemd_digest, code=E_EXEC)
    except HostConfinementError as exc:
        raise HostConfinementError(E_DELEGATION, exc.detail) from exc
    systemd_filesystem = _mount_provenance(systemd_path, systemd_object.descriptor, E_DELEGATION)
    try:
        python = BROKER_PYTHON.resolve(strict=True)
        python_object, python_filesystem = _open_unpinned_executable(python, E_DELEGATION)
    except (OSError, HostConfinementError) as exc:
        os.close(systemd_object.descriptor)
        raise HostConfinementError(
            E_DELEGATION, f"cannot qualify Python executable: {exc}"
        ) from exc
    argv = [
        *BROKER_PREFIX,
        "--property=RuntimeMaxSec=120",
        f"--working-directory={root}",
        "--setenv=RANEX_HOST_PROBE=1",
        f"--setenv=PYTHONPATH={root / 'src'}",
        "--setenv=PATH=/usr/bin:/bin",
        str(python),
        "-m",
        "ranex.cli.host_confinement",
        "host-probe",
    ]
    environment = {
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={endpoint.bus}",
        "XDG_RUNTIME_DIR": str(endpoint.runtime),
    }
    try:
        _require_same_named_object(systemd_object, E_DELEGATION)
        _require_same_named_object(python_object, E_DELEGATION)
        completed = subprocess.run(
            argv,
            cwd=root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=150,
        )
        _require_same_named_object(systemd_object, E_DELEGATION)
        _require_same_named_object(python_object, E_DELEGATION)
    except subprocess.TimeoutExpired as exc:
        raise HostConfinementError(E_DELEGATION, "systemd delegation broker timed out") from exc
    finally:
        os.close(systemd_object.descriptor)
        os.close(python_object.descriptor)
    if completed.returncode != 0:
        stdout_detail = completed.stdout.strip()
        stderr_detail = completed.stderr.strip()
        try:
            refusal = json.loads(stdout_detail)
        except json.JSONDecodeError:
            refusal = None
        if isinstance(refusal, dict):
            child_code = refusal.get("refusal")
            child_detail = refusal.get("detail")
            if child_code in {E_ARCH, E_FACT, E_DELEGATION, E_CLEANUP} and isinstance(
                child_detail, str
            ) and child_detail:
                if child_code == E_FACT and child_detail.startswith(
                    "cgroup delegation is missing controllers:"
                ):
                    _refuse(
                        E_DELEGATION,
                        f"systemd delegation broker failed with exit "
                        f"{completed.returncode}: {child_detail}",
                    )
                _refuse(child_code, child_detail)
            if isinstance(child_detail, str) and child_detail:
                stdout_detail = child_detail
        diagnostic = "; ".join(
            detail for detail in (stdout_detail, stderr_detail) if detail
        )
        if not diagnostic:
            diagnostic = "no child diagnostic"
        _refuse(
            E_DELEGATION,
            f"systemd delegation broker failed with exit {completed.returncode}: {diagnostic}",
        )
    try:
        probe = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise HostConfinementError(
            E_DELEGATION, f"broker host-probe output is invalid JSON: {exc}"
        ) from exc
    probe_mapping = _mapping(probe, "broker host-probe", E_DELEGATION)
    probe_mapping = _validate_host_probe(probe_mapping, E_DELEGATION)
    record = _broker_record(
        endpoint,
        status="ran",
        attempted=True,
        argv=argv,
        executable_digest="sha256:" + systemd_digest,
    )
    record["python_executable_digest"] = "sha256:" + python_object.sha256
    record["python_executable"] = {
        "capabilities": False,
        "filesystem": python_filesystem,
        "mode": python_object.mode,
        "owner": python_object.owner,
        "path": str(python),
        "sha256": python_object.sha256,
    }
    record["capabilities"] = False
    record["filesystem"] = systemd_filesystem
    record["mode"] = systemd_object.mode
    record["owner"] = systemd_object.owner
    return probe_mapping, record


def _parent_userns_sysctls(
    root: Path, profile: Mapping[str, Any], runtime_uid: int
) -> dict[str, Any]:
    result_read, result_write = os.pipe2(os.O_CLOEXEC)
    child = os.fork()
    if child == 0:
        os.close(result_read)
        try:
            runtime = Path("/run/user") / str(runtime_uid)
            libc = ctypes.CDLL(None, use_errno=True)
            if libc.unshare(ctypes.c_int(NAMESPACE_FLAGS["mount"])) != 0:
                error = ctypes.get_errno()
                raise HostConfinementError(
                    E_FACT,
                    f"cannot isolate mount view for parent-userns host-state probe: "
                    f"{os.strerror(error)}",
                )
            private_flags = 0x4000 | 0x40000  # MS_REC | MS_PRIVATE
            if (
                libc.mount(
                    ctypes.c_char_p(),
                    ctypes.c_char_p(b"/"),
                    ctypes.c_char_p(),
                    ctypes.c_ulong(private_flags),
                    ctypes.c_void_p(),
                )
                != 0
            ):
                error = ctypes.get_errno()
                raise HostConfinementError(
                    E_FACT,
                    f"cannot privatize mount propagation for host-state probe: "
                    f"{os.strerror(error)}",
                )
            if libc.umount2(ctypes.c_char_p(os.fsencode(runtime)), ctypes.c_int(2)) != 0:
                error = ctypes.get_errno()
                raise HostConfinementError(
                    E_FACT,
                    f"cannot reveal parent user-runtime mount for host-state probe: "
                    f"{os.strerror(error)}",
                )
            endpoint = _broker_endpoint(runtime_uid)
            probe, _record = _run_broker_probe(root, profile, endpoint)
            host = _mapping(probe.get("host"), "parent-userns host-probe.host", E_FACT)
            helpers = _mapping(
                probe.get("helpers"), "parent-userns host-probe.helpers", E_FACT
            )
            bubblewrap = _mapping(
                helpers.get("bubblewrap"),
                "parent-userns host-probe bubblewrap",
                E_FACT,
            )
            sysctls = _mapping(
                host.get("unprivileged_userns_sysctls"),
                "parent-userns unprivileged-userns sysctls",
                E_FACT,
            )
            response = {
                "bubblewrap": bubblewrap,
                "refusal": None,
                "source": "pinned-systemd-parent-userns-probe",
                "sysctls": sysctls,
            }
        except HostConfinementError as exc:
            response = {"detail": exc.detail, "refusal": exc.code}
        except OSError as exc:
            response = {
                "detail": f"parent-userns host-state probe failed: {exc}",
                "refusal": E_FACT,
            }
        data = canonical_json_bytes(response)
        try:
            view = memoryview(data)
            while view:
                view = view[os.write(result_write, view) :]
        finally:
            os.close(result_write)
        os._exit(0)
    os.close(result_write)
    response = bytearray()
    try:
        while block := os.read(result_read, 8192):
            response.extend(block)
            if len(response) > RESPONSE_LIMIT:
                os.kill(child, signal.SIGKILL)
                _refuse(E_FACT, "parent-userns host-state response exceeded 65536 bytes")
    finally:
        os.close(result_read)
    waited, status = os.waitpid(child, 0)
    if waited != child or not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
        _refuse(E_FACT, "parent-userns host-state probe child failed")
    try:
        value = json.loads(response)
    except json.JSONDecodeError as exc:
        raise HostConfinementError(
            E_FACT, f"parent-userns host-state response is invalid JSON: {exc}"
        ) from exc
    result = _mapping(value, "parent-userns host-state response", E_FACT)
    if result.get("refusal") is not None:
        detail = result.get("detail")
        _refuse(E_FACT, detail if isinstance(detail, str) and detail else "host-state probe refused")
    _exact_keys(
        result,
        {"bubblewrap", "refusal", "source", "sysctls"},
        "host-state response",
        E_FACT,
    )
    return result


def _duplicate_high(descriptor: int) -> int:
    return int(fcntl.fcntl(descriptor, fcntl.F_DUPFD_CLOEXEC, 64))


def _execveat(descriptor: int, argv: Sequence[str], environment: Mapping[str, str]) -> NoReturn:
    argument_values = [value.encode() for value in argv]
    environment_values = [f"{name}={value}".encode() for name, value in environment.items()]
    argument_array = (ctypes.c_char_p * (len(argument_values) + 1))(*argument_values, None)
    environment_array = (ctypes.c_char_p * (len(environment_values) + 1))(*environment_values, None)
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall(
        ctypes.c_long(SYS_EXECVEAT),
        ctypes.c_int(descriptor),
        ctypes.c_char_p(b""),
        argument_array,
        environment_array,
        ctypes.c_int(AT_EMPTY_PATH),
    )
    os._exit(127)


def _inject_session_keyring() -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    result = libc.syscall(
        ctypes.c_long(SYS_KEYCTL),
        ctypes.c_long(KEYCTL_JOIN_SESSION_KEYRING),
        ctypes.c_char_p(b"ranex-slice017-controller-injected"),
    )
    if result < 0:
        os._exit(125)
    return int(result)


def _read_launcher_response(descriptor: int, child: int) -> bytes:
    response = bytearray()
    while True:
        block = os.read(descriptor, 8192)
        if not block:
            break
        response.extend(block)
        if len(response) > RESPONSE_LIMIT:
            if child <= 1:
                _refuse(E_PROTOCOL, "launcher response exceeded 65536 bytes without a safe kill target")
            try:
                os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass
            _refuse(E_PROTOCOL, "launcher response exceeded 65536 bytes")
    return bytes(response)


def _validate_launcher_response(
    raw: bytes,
    status: int,
    *,
    injected_descriptor: int,
    injected_keyring: int,
) -> dict[str, Any]:
    if len(raw) > RESPONSE_LIMIT:
        _refuse(E_PROTOCOL, "launcher response exceeded 65536 bytes")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HostConfinementError(
            E_PROTOCOL, f"launcher response is malformed JSON: {exc}"
        ) from exc
    response = _mapping(value, "launcher response", E_PROTOCOL)
    if set(response) != {"probes", "protocol", "refusal"}:
        _refuse(E_PROTOCOL, "launcher response has missing or extra fields")
    if raw != canonical_json_bytes(response):
        _refuse(E_PROTOCOL, "launcher response is not canonical JSON")
    if response.get("protocol") != PROTOCOL:
        _refuse(E_PROTOCOL, "launcher response uses the wrong protocol")
    probes = _mapping(response.get("probes"), "launcher response probes", E_PROTOCOL)
    if response.get("refusal") is not None or status != 0:
        refusal = response.get("refusal")
        code = refusal if isinstance(refusal, str) and refusal else E_PROTOCOL
        if code not in {E_FACT, E_PROTOCOL}:
            code = E_PROTOCOL
        _refuse(code, f"launcher refused its qualification probe with {refusal!r}")
    required = {
        "closed_unexpected_fds",
        "inherited_session_keyring_invalidated",
        "injected_secret_env_absent",
        "injected_unexpected_fd_absent",
        "landlock_abi",
        "no_new_privs",
        "observed_env_names",
        "seccomp_fields_present",
        "session_keyring_after",
        "session_keyring_before",
    }
    if set(probes) != required:
        _refuse(E_PROTOCOL, "launcher probe object has missing or extra fields")
    closed = probes.get("closed_unexpected_fds")
    before = probes.get("session_keyring_before")
    after = probes.get("session_keyring_after")
    closed_valid = (
        type(closed) is list
        and all(type(descriptor) is int and descriptor >= 0 for descriptor in closed)
        and closed == sorted(set(closed))
        and set(closed) == {0, 1, 2, injected_descriptor}
    )
    if (
        not closed_valid
        or type(before) is not int
        or type(after) is not int
        or before != injected_keyring
        or before <= 0
        or after <= 0
        or after == before
        or probes.get("injected_secret_env_absent") is not True
        or probes.get("injected_unexpected_fd_absent") is not True
        or probes.get("inherited_session_keyring_invalidated") is not True
        or probes.get("observed_env_names") != ["LC_ALL", "TZ"]
        or type(probes.get("no_new_privs")) is not int
        or probes.get("no_new_privs") != 1
        or probes.get("seccomp_fields_present") is not True
        or type(probes.get("landlock_abi")) is not int
        or probes["landlock_abi"] < 6
    ):
        _refuse(E_FACT, "launcher did not prove every mandatory isolation fact")
    return probes


def _run_launcher(opened: OpenedObject) -> dict[str, Any]:
    gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
    request_read, request_write = os.pipe2(os.O_CLOEXEC)
    response_read, response_write = os.pipe2(os.O_CLOEXEC)
    metadata_read, metadata_write = os.pipe2(os.O_CLOEXEC)
    child_gate = _duplicate_high(gate_read)
    child_request = _duplicate_high(request_read)
    child_response = _duplicate_high(response_write)
    child_launcher = _duplicate_high(opened.descriptor)
    injected_source = os.open("/dev/null", os.O_RDONLY | os.O_CLOEXEC)
    injected = _duplicate_high(injected_source)
    os.close(injected_source)
    child_metadata = _duplicate_high(metadata_write)
    child = os.fork()
    if child == 0:
        os.dup2(child_gate, 3, inheritable=True)
        os.dup2(child_request, 4, inheritable=True)
        os.dup2(child_response, 5, inheritable=True)
        os.set_inheritable(injected, True)
        injected_keyring = _inject_session_keyring()
        os.write(child_metadata, injected_keyring.to_bytes(8, "little", signed=True))
        _execveat(
            child_launcher,
            [str(opened.path)],
            {
                "LC_ALL": "C",
                "RANEX_SLICE017_INJECTED_SECRET": "must-not-survive",
                "TZ": "UTC",
            },
        )
    for descriptor in (
        gate_read,
        request_read,
        response_write,
        child_gate,
        child_request,
        child_response,
        child_launcher,
        injected,
        metadata_write,
        child_metadata,
    ):
        os.close(descriptor)
    try:
        metadata = os.read(metadata_read, 8)
        if len(metadata) != 8:
            _refuse(E_PROTOCOL, "launcher child did not confirm its injected session keyring")
        injected_keyring = int.from_bytes(metadata, "little", signed=True)
        request = canonical_json_bytes(
            {
                "action": "qualify-probe",
                "env_allowlist": ["LC_ALL", "TZ"],
                "protocol": PROTOCOL,
            }
        )
        if len(request) > REQUEST_LIMIT:
            _refuse(E_PROTOCOL, "internal launcher request exceeded 4096 bytes")
        request_view = memoryview(request)
        while request_view:
            written = os.write(request_write, request_view)
            request_view = request_view[written:]
        os.close(request_write)
        request_write = -1
        os.write(gate_write, b"1")
        os.close(gate_write)
        gate_write = -1
        raw = _read_launcher_response(response_read, child)
        waited, status = os.waitpid(child, 0)
        if waited != child:
            _refuse(E_PROTOCOL, "could not wait for launcher probe")
        return _validate_launcher_response(
            raw,
            os.waitstatus_to_exitcode(status),
            injected_descriptor=injected,
            injected_keyring=injected_keyring,
        )
    finally:
        if request_write >= 0:
            os.close(request_write)
        if gate_write >= 0:
            os.close(gate_write)
        os.close(metadata_read)
        os.close(response_read)
        try:
            waited, _status = os.waitpid(child, os.WNOHANG)
        except ChildProcessError:
            waited = child
        if waited == 0:
            try:
                os.kill(child, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(child, 0)


def _validate_profile_and_objects(
    profile_path: Path,
    manifest_path: Path,
    artifact_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], OpenedObject, OpenedObject]:
    profile = _load_json(profile_path, E_EXEC)
    if set(profile) != {
        "artifact_sha256",
        "build_manifest_sha256",
        "helpers",
        "landlock_abi_minimum",
        "profile",
        "required_controllers",
        "schema",
        "target_architecture",
    }:
        _refuse(E_EXEC, "host profile has missing or extra top-level fields")
    if (
        profile.get("schema") != "ranex-strict-local-host-v1"
        or profile.get("profile") != "strict-local-host-v1"
        or profile.get("target_architecture") != "x86_64"
        or profile.get("landlock_abi_minimum") != 6
        or profile.get("required_controllers") != ["cpu", "memory", "pids"]
    ):
        _refuse(E_EXEC, "host profile differs from the frozen strict-local target")
    manifest = _load_json(manifest_path, E_EXEC)
    _build, _source, artifact = _manifest_sections(manifest, E_EXEC)
    manifest_digest = _sha256_path(manifest_path)
    if (
        _digest(profile.get("build_manifest_sha256"), "build_manifest_sha256", E_EXEC)
        != manifest_digest
    ):
        _refuse(E_EXEC, "profile does not bind the supplied build manifest")
    artifact_digest = _digest(artifact.get("sha256"), "artifact.sha256", E_EXEC)
    if _digest(profile.get("artifact_sha256"), "artifact_sha256", E_EXEC) != artifact_digest:
        _refuse(E_EXEC, "profile and manifest artifact digests differ")
    launcher = _open_verified(
        artifact_path,
        artifact_digest,
        code=E_EXEC,
        exact_mode=0o555,
        required_owner=os.geteuid(),
    )
    bubblewrap_path, bubblewrap_digest = _helper_pin(profile, "bubblewrap")
    try:
        bubblewrap = _open_verified(bubblewrap_path, bubblewrap_digest, code=E_EXEC)
    except (OSError, HostConfinementError):
        os.close(launcher.descriptor)
        raise
    try:
        if bubblewrap_path != BUBBLEWRAP:
            _refuse(E_EXEC, "profile does not pin the exact /usr/bin/bwrap helper")
        systemd_path, systemd_digest = _helper_pin(profile, "systemd_run")
        if systemd_path != SYSTEMD_RUN:
            _refuse(E_EXEC, "profile does not pin the frozen systemd-run path")
        systemd_object = _open_verified(systemd_path, systemd_digest, code=E_EXEC)
        os.close(systemd_object.descriptor)
        try:
            if _elf_facts_from_descriptor(launcher.descriptor, artifact_path) != _mapping(
                artifact.get("elf"), "artifact.elf", E_EXEC
            ):
                _refuse(E_EXEC, "launcher ELF facts differ from manifest")
        except HostConfinementError as exc:
            if exc.code == E_BUILD_ARTIFACT:
                raise HostConfinementError(E_EXEC, exc.detail) from exc
            raise
    except OSError as exc:
        os.close(launcher.descriptor)
        os.close(bubblewrap.descriptor)
        raise HostConfinementError(E_EXEC, f"cannot verify executable chain: {exc}") from exc
    except HostConfinementError:
        os.close(launcher.descriptor)
        os.close(bubblewrap.descriptor)
        raise
    return profile, manifest, launcher, bubblewrap


def _write_report_atomic(root: Path, report: Path, value: Mapping[str, Any]) -> None:
    try:
        report.relative_to(root)
        atomic_writer.write_atomic(report, canonical_json_bytes(value), root=root)
    except ValueError as exc:
        raise HostConfinementError(E_CLEANUP, f"qualification report publication failed: {exc}") from exc
    except OSError as exc:
        raise HostConfinementError(
            E_CLEANUP, f"qualification report publication failed: {exc}"
        ) from exc


def _write_confinement_result_atomic(root: Path, result: Path, payload: bytes) -> None:
    """Publish already-validated canonical result bytes without reserializing it."""

    try:
        result.relative_to(root)
        atomic_writer.write_atomic(result, payload, root=root)
    except ValueError as exc:
        raise HostConfinementError(E_C18_RESULT, f"confinement result publication failed: {exc}") from exc
    except OSError as exc:
        raise HostConfinementError(
            E_C18_RESULT, f"confinement result publication failed: {exc}"
        ) from exc


def _qualification_open_object(
    opened: OpenedObject,
    filesystem: Mapping[str, Any],
    *,
    parent_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        facts = os.fstat(opened.descriptor)
        realpath = opened.path.resolve(strict=True)
    except OSError as exc:
        raise HostConfinementError(
            E_EXEC, f"cannot collect open-object identity for {opened.path}: {exc}"
        ) from exc
    if parent_identity is None:
        uid = _parent_namespace_id(facts.st_uid, kind="uid")
        gid = _parent_namespace_id(facts.st_gid, kind="gid")
    else:
        expected = {
            "device": facts.st_dev,
            "inode": facts.st_ino,
            "mode": stat.S_IMODE(facts.st_mode),
            "path": str(opened.path),
            "sha256": opened.sha256,
        }
        if any(parent_identity.get(name) != value for name, value in expected.items()):
            _refuse(E_EXEC, f"parent-visible identity differs for held object {opened.path}")
        uid = _exact_integer(parent_identity.get("owner"), "parent-visible owner", E_EXEC)
        gid = _exact_integer(parent_identity.get("gid"), "parent-visible group", E_EXEC)
    return {
        "path": str(realpath),
        "realpath": str(realpath),
        "sha256": opened.sha256,
        "device": facts.st_dev,
        "inode": facts.st_ino,
        "uid": uid,
        "gid": gid,
        "mode": stat.S_IMODE(facts.st_mode),
        "mount_id": _exact_integer(
            filesystem.get("mount_id"), "open-object mount ID", E_EXEC, minimum=1
        ),
        "security_capability": False,
        "filesystem": dict(filesystem),
    }


def qualify(
    root: Path,
    profile_arg: str,
    artifact_arg: str,
    manifest_arg: str,
    report_arg: str,
) -> None:
    machine, _release = _host_architecture()
    if artifact_arg != INSTALLED_ARTIFACT_ARGUMENT or report_arg != REPORT_ARGUMENT:
        _refuse(E_EXEC, "artifact or report is not an admitted qualification path")
    profile_path = resolve_within_repository(root, profile_arg)
    manifest_path = resolve_within_repository(root, manifest_arg)
    artifact_path = (
        (root / artifact_arg).absolute()
        if not Path(artifact_arg).is_absolute()
        else Path(artifact_arg)
    )
    report = (
        (root / report_arg).absolute() if not Path(report_arg).is_absolute() else Path(report_arg)
    )
    profile, manifest, launcher, bubblewrap = _validate_profile_and_objects(
        profile_path, manifest_path, artifact_path
    )
    try:
        cgroup_root, relative = _current_cgroup_root()
        controllers = _cgroup_controllers(cgroup_root)
        existing_root = {
            "controllers": controllers,
            "path": str(cgroup_root),
            "relative_path": relative,
        }
        endpoint: BrokerEndpoint | None
        try:
            endpoint = _broker_endpoint()
        except HostConfinementError:
            endpoint = None
        if REQUIRED_CONTROLLERS <= set(controllers):
            try:
                probe = collect_host_probe()
            except HostConfinementError as exc:
                if exc.code != E_DELEGATION or endpoint is None:
                    raise
                probe, broker = _run_broker_probe(root, profile, endpoint)
                source = "broker"
            else:
                broker = _broker_record(
                    endpoint,
                    status="available" if endpoint is not None else "untestable",
                    attempted=False,
                )
                source = "existing"
        else:
            if endpoint is None:
                missing = sorted(REQUIRED_CONTROLLERS - set(controllers))
                _refuse(
                    E_DELEGATION,
                    f"existing cgroup is missing {', '.join(missing)} and broker is unavailable",
                )
            probe, broker = _run_broker_probe(root, profile, endpoint)
            source = "broker"
        probe = _validate_host_probe(probe, E_FACT)
        probe_cgroup = _mapping(probe.get("cgroup"), "host-probe.cgroup", E_FACT)
        probe_host = _mapping(probe.get("host"), "host-probe.host", E_FACT)
        probe_helpers = _mapping(probe.get("helpers"), "host-probe.helpers", E_FACT)
        observed_bwrap = _mapping(probe_helpers.get("bubblewrap"), "host-probe bubblewrap", E_FACT)
        pinned_bwrap_path, pinned_bwrap_digest = _helper_pin(profile, "bubblewrap")
        if pinned_bwrap_path == BUBBLEWRAP and observed_bwrap.get("sha256") != pinned_bwrap_digest:
            _refuse(E_EXEC, "host-probe bubblewrap bytes differ from profile")
        launcher_filesystem = _mount_provenance(artifact_path, launcher.descriptor, E_EXEC)
        bubblewrap_filesystem = _mount_provenance(bubblewrap.path, bubblewrap.descriptor, E_EXEC)
        launcher_probes = _run_launcher(launcher)
        cgroup_report = {
            "cgroup_kill": True,
            "mount": {
                "path": _string(probe_cgroup.get("mount"), "host-probe cgroup mount", E_FACT),
                "filesystem": "cgroup2",
            },
            "root": _string(probe_cgroup.get("root"), "host-probe cgroup root", E_FACT),
            "relative_path": _string(
                probe_cgroup.get("relative_path"),
                "host-probe cgroup relative path",
                E_FACT,
            ),
            "controllers": _string_list(
                probe_cgroup.get("controllers"), "host-probe cgroup controllers", E_FACT
            ),
            "probe_transcript": _mapping(
                probe_cgroup.get("probe_transcript"),
                "host-probe cgroup transcript",
                E_FACT,
            ),
        }
        delegation = {
            "broker": broker,
            "existing_root": existing_root,
            "source": source,
        }
        userns_sysctls = _mapping(
            probe_host.get("unprivileged_userns_sysctls"),
            "host-probe unprivileged-userns sysctls",
            E_FACT,
        )
        userns_source = "qualification-host-probe"
        parent_bubblewrap: Mapping[str, Any] | None = None
        if not _in_initial_user_namespace():
            parent_uid = _parent_namespace_id(os.geteuid(), kind="uid")
            parent_state = _parent_userns_sysctls(root, profile, parent_uid)
            userns_sysctls = _mapping(
                parent_state.get("sysctls"),
                "parent-userns host-state sysctls",
                E_FACT,
            )
            userns_source = _string(
                parent_state.get("source"), "parent-userns host-state source", E_FACT
            )
            parent_bubblewrap = _mapping(
                parent_state.get("bubblewrap"),
                "parent-userns bubblewrap identity",
                E_FACT,
            )
        _require_same_named_object(launcher, E_EXEC)
        _require_same_named_object(bubblewrap, E_EXEC)
        report_value = {
            "schema": "ranex-strict-local-qualification-v1",
            "qualified": True,
            "refusal": None,
            "kernel": {
                "release": _string(
                    probe_host.get("kernel_release"), "host-probe kernel release", E_FACT
                ),
                "architecture": machine,
            },
            "primitives": {
                "landlock": {
                    "available": True,
                    "abi": _exact_integer(
                        probe_host.get("landlock_abi"),
                        "host-probe Landlock ABI",
                        E_FACT,
                        minimum=6,
                    ),
                },
                "seccomp_filter": launcher_probes.get("seccomp_fields_present") is True,
                "no_new_privs": launcher_probes.get("no_new_privs") == 1,
                "namespaces": _mapping(
                    probe_host.get("namespaces"), "host-probe namespaces", E_FACT
                ),
                "openat2": probe_host.get("openat2") is True,
            },
            "cgroup": cgroup_report,
            "open_objects": {
                "bubblewrap": _qualification_open_object(
                    bubblewrap,
                    bubblewrap_filesystem,
                    parent_identity=parent_bubblewrap,
                ),
                "launcher": _qualification_open_object(launcher, launcher_filesystem),
            },
            "digests": {
                "profile": _sha256_path(profile_path),
                "build_manifest": _sha256_path(manifest_path),
                "artifact": launcher.sha256,
            },
            "delegation": delegation,
            "host_state": _collect_host_state(
                probe_cgroup,
                delegation_source=source,
                userns_sysctls=userns_sysctls,
                userns_source=userns_source,
            ),
        }
        _write_report_atomic(root, report, report_value)
    finally:
        os.close(launcher.descriptor)
        os.close(bubblewrap.descriptor)


def _session_descriptor(root: Path, descriptor_arg: str) -> dict[str, Any]:
    candidate = Path(descriptor_arg)
    if candidate.is_absolute():
        path = candidate.resolve()
        if path != root and root not in path.parents:
            _refuse(E_C18_GATE, "descriptor is outside the repository")
    else:
        path = resolve_within_repository(root, descriptor_arg)
    raw = path.read_bytes()
    value = _mapping(json.loads(raw), "confinement descriptor", E_C18_GATE)
    expected = {"schema", "argv", "environment", "subject", "toolchain", "output", "scratch", "limits"}
    if set(value) != expected or value.get("schema") != "ranex-confinement-command-v1":
        _refuse(E_C18_GATE, "confinement descriptor schema is not closed")
    if raw != canonical_json_bytes(value):
        _refuse(E_C18_GATE, "confinement descriptor is not canonical JSON")
    argv = value.get("argv")
    environment = value.get("environment")
    if not isinstance(argv, list) or not argv or any(
        not isinstance(item, str) or not item or "\x00" in item for item in argv
    ):
        _refuse(E_C18_GATE, "argv must contain non-empty strings")
    if not isinstance(environment, dict) or any(
        not isinstance(name, str) or not name or "=" in name or "\x00" in name
        or not isinstance(item, str) or "\x00" in item
        for name, item in environment.items()
    ):
        _refuse(E_C18_GATE, "environment must be a string mapping")
    resolved: dict[str, Path] = {}
    for name in ("subject", "toolchain", "output", "scratch"):
        argument = _string(value.get(name), name, E_C18_GATE)
        candidate = resolve_within_repository(root, argument)
        try:
            facts = candidate.lstat()
        except OSError as exc:
            raise HostConfinementError(E_C18_GATE, f"cannot inspect {name}: {exc}") from exc
        if stat.S_ISLNK(facts.st_mode) or not stat.S_ISDIR(facts.st_mode):
            _refuse(E_C18_GATE, f"{name} is not a non-link directory")
        resolved[name] = candidate
    identities = {name: (path.stat().st_dev, path.stat().st_ino) for name, path in resolved.items()}
    if len(set(identities.values())) != len(identities):
        _refuse(E_C18_PATH_ALIAS, "descriptor paths alias the same filesystem object")
    for writable in ("output", "scratch"):
        for authority in ("subject", "toolchain"):
            if resolved[authority] in resolved[writable].parents or resolved[writable] in resolved[authority].parents:
                _refuse(E_C18_PATH_ALIAS, "writable and authority trees overlap")
    limits = _mapping(value.get("limits"), "limits", E_C18_GATE)
    expected_limits = {"cpu_usage_usec", "memory_bytes", "pids", "wall_time_ms", "output_bytes", "output_inodes", "output_depth"}
    if set(limits) != expected_limits:
        _refuse(E_C18_GATE, "limits are not closed")
    for name in expected_limits:
        _exact_integer(limits.get(name), name, E_C18_GATE, minimum=1)
    value["_resolved"] = resolved
    return value


def _resolve_worker_executable(argv0: str) -> Path:
    executable = Path(argv0)
    if not executable.is_absolute():
        _refuse(E_C18_GATE, f"worker executable cannot be resolved: {argv0}")
    try:
        return executable.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise HostConfinementError(
            E_C18_GATE, f"worker executable cannot be resolved: {argv0}"
        ) from exc


def _current_session_host_state() -> dict[str, Any]:
    cgroup_root, relative = _current_cgroup_root()
    return {
        "lsm": _required_host_text(Path("/sys/kernel/security/lsm"), "active LSM list"),
        "userns_sysctl": _unprivileged_userns_sysctls(),
        "cgroup_delegation": {
            "root": str(cgroup_root),
            "relative_path": relative,
            "controllers": _cgroup_controllers(cgroup_root),
        },
    }


def _validate_runtime_profile(
    runtime: Mapping[str, Any], *, profile_path: Path, host_profile_path: Path,
    manifest_path: Path, launcher: OpenedObject, host_profile_digest: str,
) -> None:
    expected = {
        "build_manifest_sha256", "cgroup", "host_profile_sha256", "landlock_abi_minimum",
        "launcher_sha256", "mandatory_layers", "mounts", "output_resolution", "profile",
        "schema", "seccomp",
    }
    _exact_keys(runtime, expected, "runtime profile", E_C18_GATE)
    if runtime.get("schema") != "ranex-strict-local-runtime-v1" or runtime.get("profile") != "strict-local-v1":
        _refuse(E_C18_GATE, "runtime profile schema is invalid")
    if runtime.get("mandatory_layers") != {
        "cgroup": True, "ipc": True, "landlock": True, "mount": True, "network": True,
        "no_new_privs": True, "pid": True, "seccomp": True, "user": True,
    } or runtime.get("mounts") != {
        "subject": "read-only", "toolchain": "read-only", "output": "writable-bounded",
        "scratch": "writable-bounded", "proc": "fresh", "dev": "minimal",
    }:
        _refuse(E_C18_GATE, "runtime profile has a missing mandatory layer or mount")
    if runtime.get("cgroup") != {"controllers": ["cpu", "memory", "pids"], "start_gate_fd": 0}:
        _refuse(E_C18_GATE, "runtime profile cgroup protocol is invalid")
    if runtime.get("output_resolution") != ["RESOLVE_BENEATH", "RESOLVE_NO_MAGICLINKS", "RESOLVE_NO_SYMLINKS"]:
        _refuse(E_C18_GATE, "runtime profile output resolution is invalid")
    if runtime.get("landlock_abi_minimum") != 6 or runtime.get("seccomp") != {"architecture": "x86_64", "policy": "default-deny-v1"}:
        _refuse(E_C18_GATE, "runtime profile policy identity is invalid")
    if _digest(runtime.get("host_profile_sha256"), "host_profile_sha256", E_C18_GATE) != host_profile_digest:
        _refuse(E_C18_GATE, "runtime profile host profile pin drifted")
    if _digest(runtime.get("build_manifest_sha256"), "build_manifest_sha256", E_C18_GATE) != _sha256_path(manifest_path):
        _refuse(E_C18_GATE, "runtime profile build manifest pin drifted")
    if _digest(runtime.get("launcher_sha256"), "launcher_sha256", E_C18_GATE) != launcher.sha256:
        _refuse(E_C18_GATE, "runtime profile launcher pin drifted")
    # Keep the profile itself in the dependency chain rather than accepting a
    # schema-equivalent replacement at a caller selected path.
    if profile_path.name != "strict-local-v1.json":
        _refuse(E_C18_GATE, "runtime profile is not the admitted strict-local profile")


def _read_cgroup_file(path: Path, code: str) -> str:
    try:
        return path.read_text(encoding="ascii").strip()
    except OSError as exc:
        raise HostConfinementError(code, f"cannot read cgroup control {path.name}: {exc}") from exc


def _capture_cleanup_failure(
    failures: list[BaseException], context: str, operation: Any
) -> None:
    """Run every teardown operation without letting it hide an active refusal."""
    try:
        operation()
    except BaseException as exc:
        if isinstance(exc, HostConfinementError):
            failures.append(exc)
            return
        cleanup_error = HostConfinementError(E_CLEANUP, f"{context}: {exc}")
        cleanup_error.__cause__ = exc
        failures.append(cleanup_error)


def _finish_cleanup(primary: BaseException | None, failures: list[BaseException]) -> None:
    if not failures:
        return
    if primary is not None:
        for failure in failures:
            primary.add_note(f"cleanup failure (preserved root cause): {failure}")
        return
    first = failures[0]
    for failure in failures[1:]:
        first.add_note(f"additional cleanup failure: {failure}")
    raise first


def _is_blocked_in_gate_read(pid: int, expected_fd: int) -> bool:
    """Return whether ``pid`` is stopped in a read from the fixed gate fd."""
    try:
        syscall = Path(f"/proc/{pid}/syscall").read_text(encoding="ascii")
    except OSError as exc:
        if exc.errno in {errno.ENOENT, errno.ESRCH}:
            return False
        raise HostConfinementError(E_C18_GATE, f"cannot observe launcher start gate: {exc}") from exc
    # x86-64 read is syscall 0; its first argument is the expected gate fd.
    fields = syscall.split()
    return len(fields) >= 2 and fields[0] == "0" and fields[1] == hex(expected_fd)


def _descendant_pids(pid: int, levels: int = 3) -> set[int]:
    """Boundedly enumerate descendants through every thread's children list."""
    frontier = {pid}
    descendants: set[int] = set()
    for _ in range(levels):
        next_frontier: set[int] = set()
        for parent in frontier:
            try:
                tasks = tuple((Path(f"/proc/{parent}/task")).iterdir())
            except OSError as exc:
                if exc.errno in {errno.ENOENT, errno.ESRCH}:
                    continue
                raise HostConfinementError(
                    E_C18_GATE, f"cannot enumerate launcher descendants: {exc}"
                ) from exc
            for task in tasks:
                if not task.name.isdigit():
                    continue
                try:
                    raw_children = (task / "children").read_text(encoding="ascii")
                except OSError as exc:
                    if exc.errno in {errno.ENOENT, errno.ESRCH}:
                        continue
                    raise HostConfinementError(
                        E_C18_GATE, f"cannot read launcher descendant list: {exc}"
                    ) from exc
                try:
                    next_frontier.update(int(value) for value in raw_children.split())
                except ValueError as exc:
                    raise HostConfinementError(
                        E_C18_GATE, "launcher descendant list is malformed"
                    ) from exc
        next_frontier -= descendants | {pid}
        descendants.update(next_frontier)
        frontier = next_frontier
        if not frontier:
            break
    return descendants


def _resolve_gate_blocked_launcher(
    bubblewrap_pid: int, *, expected_fd: int, timeout: float = 2.0
) -> int:
    """Find the sole bwrap descendant stopped at the controller gate."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        blocked = sorted(
            pid for pid in _descendant_pids(bubblewrap_pid) if _is_blocked_in_gate_read(pid, expected_fd)
        )
        if len(blocked) == 1:
            return blocked[0]
        if len(blocked) > 1:
            _refuse(E_C18_GATE, f"multiple launcher descendants blocked in the fd {expected_fd} start gate")
        time.sleep(0.005)
    _refuse(E_C18_GATE, f"no unique launcher descendant blocked in the fd {expected_fd} start gate")


def confinement_session(
    root: Path, *, profile_arg: str, host_profile_arg: str, artifact_arg: str,
    manifest_arg: str, qualification_arg: str, descriptor_arg: str, result_arg: str,
) -> None:
    descriptor = _session_descriptor(root, descriptor_arg)
    worker_executable = _resolve_worker_executable(descriptor["argv"][0])
    qualification_path = resolve_within_repository(root, qualification_arg)
    qualification = _load_json(qualification_path, E_C18_HOST_DRIFT)
    recorded = qualification.get("host_state")
    if qualification.get("schema") != "ranex-strict-local-qualification-v1" or not isinstance(recorded, dict):
        _refuse(E_C18_HOST_DRIFT, "qualification has no valid host-state binding")
    # SLICE-017 reports a richer closed host-state shape.  A deliberately
    # synthetic or stale shape must be rejected before any executable opens.
    required_recorded = {"lsm", "unprivileged_userns_sysctls", "delegation_identity", "boot_id", "machine_id"}
    if set(recorded) != required_recorded:
        _refuse(E_C18_HOST_DRIFT, "qualification host-state shape differs from the current contract")
    current_lsm = _required_host_text(Path("/sys/kernel/security/lsm"), "active LSM list")
    if _mapping(recorded.get("lsm"), "qualified LSM state", E_C18_HOST_DRIFT).get("securityfs_lsm") != current_lsm:
        _refuse(E_C18_HOST_DRIFT, "active LSM state drifted since qualification")
    if recorded.get("unprivileged_userns_sysctls") != _unprivileged_userns_sysctls():
        _refuse(E_C18_HOST_DRIFT, "user namespace state drifted since qualification")
    delegation = _mapping(recorded.get("delegation_identity"), "delegation identity", E_C18_HOST_DRIFT)
    cgroup_root, relative = _current_cgroup_root()
    if delegation.get("cgroup_root") != str(cgroup_root) or delegation.get("cgroup_relative_path") != relative:
        _refuse(E_C18_HOST_DRIFT, "cgroup delegation drifted since qualification")
    current = _current_session_host_state()
    if recorded.get("boot_id") != _required_host_text(Path("/proc/sys/kernel/random/boot_id"), "boot ID") or recorded.get("machine_id") != _required_host_text(Path("/etc/machine-id"), "machine ID"):
        _refuse(E_C18_HOST_DRIFT, "boot or machine identity drifted since qualification")
    if _mapping(recorded.get("lsm"), "qualified LSM state", E_C18_HOST_DRIFT) != _collect_host_state(
        {"root": str(cgroup_root), "relative_path": relative},
        delegation_source=_string(delegation.get("source"), "delegation source", E_C18_HOST_DRIFT),
        userns_sysctls=_unprivileged_userns_sysctls(),
        userns_source=_string(delegation.get("userns_state_source"), "userns source", E_C18_HOST_DRIFT),
    )["lsm"]:
        _refuse(E_C18_HOST_DRIFT, "full LSM policy identity drifted since qualification")
    # Full launch is possible only on a qualified delegated host.  Validate all
    # pins before creating a process; there is intentionally no local fallback.
    profile_path = resolve_within_repository(root, profile_arg)
    host_profile_path = resolve_within_repository(root, host_profile_arg)
    manifest_path = resolve_within_repository(root, manifest_arg)
    artifact_path = resolve_within_repository(root, artifact_arg)
    runtime = _load_json(profile_path, E_C18_GATE)
    profile, _manifest, launcher, bubblewrap = _validate_profile_and_objects(host_profile_path, manifest_path, artifact_path)
    del profile
    try:
        profile_digests = {
            "runtime": _sha256_path(profile_path),
            "host": _sha256_path(host_profile_path),
            "launcher": launcher.sha256,
        }
        _validate_runtime_profile(runtime, profile_path=profile_path, host_profile_path=host_profile_path,
                                  manifest_path=manifest_path, launcher=launcher,
                                  host_profile_digest=profile_digests["host"])
        # The descriptor identifies the live delegated root once.  All later
        # operations use this object; there is no re-resolution fallback.
        held_root = os.open(cgroup_root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
        try:
            suffix = f"ranex-session-{os.getpid()}-{uuid.uuid4().hex[:8]}"
            controller = cgroup_root / f"{suffix}-controller"
            worker = cgroup_root / f"{suffix}-worker"
            gate_read = gate_write = -1
            response_read = response_write = -1
            child = -1
            launcher_pid = -1
            session: ConfinementSession | None = None
            output_fd = -1
            result: dict[str, Any] | None = None
            delta: set[str] = set()
            try:
                _cgroup_controllers(cgroup_root)
                _check_cgroup_kill(cgroup_root)
                controller.mkdir(mode=0o755)
                _move_all_cgroup_processes(cgroup_root, controller)
                enabled = set(_read_cgroup_file(cgroup_root / "cgroup.subtree_control", E_C18_GATE).split())
                delta = REQUIRED_CONTROLLERS - enabled
                if delta:
                    _write_control(cgroup_root / "cgroup.subtree_control", " ".join(f"+{name}" for name in sorted(delta)) + "\n")
                if not REQUIRED_CONTROLLERS <= set(_read_cgroup_file(cgroup_root / "cgroup.subtree_control", E_C18_GATE).split()):
                    _refuse(E_C18_READBACK, "required cgroup controllers did not read back")
                worker.mkdir(mode=0o755)
                limits = _mapping(descriptor["limits"], "limits", E_C18_GATE)
                quota = max(
                    1,
                    limits["cpu_usage_usec"] * 100_000
                    // (limits["wall_time_ms"] * 1_000),
                )
                wanted = {
                    "pids.max": str(limits["pids"]),
                    "memory.max": str(limits["memory_bytes"]),
                    "cpu.max": f"{quota} 100000",
                }
                for name, value in wanted.items():
                    _write_control(worker / name, value + "\n")
                    if _read_cgroup_file(worker / name, E_C18_READBACK) != value:
                        _refuse(E_C18_READBACK, f"{name} did not read back exactly")
                gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
                response_read, response_write = os.pipe2(os.O_CLOEXEC)
                output_fd = os.open(descriptor["_resolved"]["output"], os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
                child = os.fork()
                if child == 0:
                    try:
                        os.close(gate_write)
                        os.close(response_read)
                        os.dup2(gate_read, 0, inheritable=True)
                        os.dup2(response_write, 1, inheritable=True)
                        if gate_read != 0:
                            os.close(gate_read)
                        if response_write != 1:
                            os.close(response_write)
                        # bwrap is a pinned, held object checked immediately before fork.
                        _execveat(bubblewrap.descriptor, [str(bubblewrap.path), "--die-with-parent", "--unshare-user", "--unshare-pid", "--unshare-ipc", "--unshare-net", "--unshare-cgroup", "--proc", "/proc", "--dev", "/dev", "--ro-bind", str(launcher.path), "/ranex-worker-launcher", "--ro-bind", str(descriptor["_resolved"]["subject"]), str(descriptor["_resolved"]["subject"]), "--ro-bind", str(descriptor["_resolved"]["toolchain"]), str(descriptor["_resolved"]["toolchain"]), "--bind", str(descriptor["_resolved"]["output"]), str(descriptor["_resolved"]["output"]), "--bind", str(descriptor["_resolved"]["scratch"]), str(descriptor["_resolved"]["scratch"]), "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin", "--ro-bind", "/lib", "/lib", "--ro-bind", "/lib64", "/lib64", "--", "/ranex-worker-launcher", "--ranex-worker-exec-gated", str(descriptor["_resolved"]["scratch"]), str(descriptor["_resolved"]["subject"]), str(descriptor["_resolved"]["toolchain"]), str(descriptor["_resolved"]["output"]), str(worker_executable), *descriptor["argv"][1:]], descriptor["environment"])
                    except BaseException:
                        os._exit(127)
                os.close(gate_read); gate_read = -1
                os.close(response_write); response_write = -1
                session = ConfinementSession(worker, gate_write, dict(limits))
                try:
                    launcher_pid = _resolve_gate_blocked_launcher(child, expected_fd=0)
                except HostConfinementError:
                    try:
                        os.kill(child, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    raise
                session.enroll_and_read_back(launcher_pid)
                deadline = time.monotonic() + limits["wall_time_ms"] / 1000
                session.release_start_gate()
                os.close(gate_write); gate_write = -1
                next_storage_measurement = time.monotonic()
                while True:
                    now = time.monotonic()
                    if now >= deadline:
                        session.kill_tree()
                        _refuse(E_C18_LIMIT, "wall-time limit exceeded")
                    if now >= next_storage_measurement:
                        _check_live_writable_limits(descriptor, session)
                        next_storage_measurement = now + 0.25
                    waited, status = os.waitpid(child, os.WNOHANG)
                    if waited == child:
                        if time.monotonic() >= deadline:
                            session.kill_tree()
                            _refuse(E_C18_LIMIT, "wall-time limit exceeded")
                        child = -1
                        break
                    time.sleep(0.005)
                cpu_stats = _parse_cgroup_events(
                    _read_cgroup_file(worker / "cpu.stat", E_C18_LIMIT)
                )
                memory_limit_events = _parse_cgroup_events(
                    _read_cgroup_file(worker / "memory.events", E_C18_LIMIT)
                )
                pids_limit_events = _parse_cgroup_events(
                    _read_cgroup_file(worker / "pids.events", E_C18_LIMIT)
                )
                observed = {
                    "cpu_usage_usec": cpu_stats.get("usage_usec", 0),
                    "memory.events.max": memory_limit_events.get("max", 0),
                    "memory.events.oom": memory_limit_events.get("oom", 0),
                    "memory.events.oom_kill": memory_limit_events.get("oom_kill", 0),
                    "pids.events.max": pids_limit_events.get("max", 0),
                }
                # Cgroup facts are cumulative and remain available even when
                # resource exhaustion kills the worker before it writes fd 1.
                # They must therefore outrank every response/exit refusal.
                session.observe_limits(observed)
                raw_response = _read_launcher_response(response_read, launcher_pid)
                os.close(response_read); response_read = -1
                try:
                    namespace_response = _mapping(json.loads(raw_response), "worker namespace response", E_C18_GATE)
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise HostConfinementError(
                        E_C18_GATE,
                        "worker produced no namespace response "
                        f"(wait status {status}, exit code {os.waitstatus_to_exitcode(status)})",
                    ) from exc
                required_response = {"user", "mount", "pid", "ipc", "network", "cgroup", "no_new_privs", "landlock", "seccomp"}
                if set(namespace_response) != required_response or any(
                    not isinstance(namespace_response[name], str) or not namespace_response[name]
                    for name in ("user", "mount", "pid", "ipc", "network", "cgroup")
                ) or any(namespace_response[name] is not True for name in ("no_new_privs", "landlock", "seccomp")):
                    _refuse(E_C18_GATE, "worker namespace or policy readbacks are incomplete")
                if os.waitstatus_to_exitcode(status) != 0:
                    _refuse(E_C18_GATE, "worker exited unsuccessfully")
                memory_events = _parse_cgroup_events(
                    _read_cgroup_file(worker / "memory.events", E_C18_LIMIT)
                )
                pids_events = _parse_cgroup_events(
                    _read_cgroup_file(worker / "pids.events", E_C18_LIMIT)
                )
                result = {
                    "schema": "ranex-confinement-result-v1",
                    "profile_digests": profile_digests,
                    "namespace_readbacks": {name: namespace_response[name] for name in ("user", "mount", "pid", "ipc", "network", "cgroup")},
                    "cgroup_readbacks": {
                        "limits": wanted,
                        "events": {
                            "populated": 0,
                            "max": max(memory_events.get("max", 0), pids_events.get("max", 0)),
                            "oom": memory_events.get("oom", 0),
                            "oom_kill": memory_events.get("oom_kill", 0),
                        },
                        "usage": {"cpu_usage_usec": observed["cpu_usage_usec"]},
                    },
                    "command": {"argv_digest": command_digest(descriptor["argv"]).removeprefix("sha256:"), "exit_code": 0, "no_new_privs": namespace_response["no_new_privs"], "landlock": namespace_response["landlock"], "seccomp": namespace_response["seccomp"]},
                    "teardown": {"cgroup_kill": True, "populated": 0, "cgroup_removed": True},
                    "outputs": {"files": [], "bytes": 0, "inodes": 0},
                }
            finally:
                primary = sys.exception()
                cleanup_failures: list[BaseException] = []
                if gate_read >= 0:
                    _capture_cleanup_failure(cleanup_failures, "close start-gate reader", lambda: os.close(gate_read))
                if gate_write >= 0:
                    _capture_cleanup_failure(cleanup_failures, "close start-gate writer", lambda: os.close(gate_write))
                if response_write >= 0:
                    _capture_cleanup_failure(cleanup_failures, "close launcher response writer", lambda: os.close(response_write))
                if child > 0:
                    def kill_and_reap() -> None:
                        try:
                            os.kill(child, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        try:
                            os.waitpid(child, 0)
                        except ChildProcessError:
                            pass
                    _capture_cleanup_failure(cleanup_failures, "kill and reap bubblewrap", kill_and_reap)
                worker_teardown_succeeded = True
                if worker.exists():
                    failure_count = len(cleanup_failures)
                    cleanup_session = session or ConfinementSession(worker, -1)
                    _capture_cleanup_failure(
                        cleanup_failures,
                        "kill, drain, and remove worker cgroup",
                        cleanup_session.kill_drain_remove,
                    )
                    worker_teardown_succeeded = len(cleanup_failures) == failure_count
                if response_read >= 0:
                    _capture_cleanup_failure(cleanup_failures, "close launcher response reader", lambda: os.close(response_read))
                if delta:
                    def restore_controller_delta() -> None:
                        current_enabled = set(
                            (cgroup_root / "cgroup.subtree_control").read_text().split()
                        )
                        disable_delta = delta & current_enabled
                        if disable_delta:
                            _write_control(
                                cgroup_root / "cgroup.subtree_control",
                                " ".join(f"-{name}" for name in sorted(disable_delta)) + "\n",
                            )
                    _capture_cleanup_failure(
                        cleanup_failures, "restore cgroup controller delta", restore_controller_delta
                    )
                # A domain cgroup cannot receive processes while its subtree
                # controllers are enabled.  Restore only our delta first, then
                # move the controller process back and remove its empty leaf.
                if controller.exists():
                    _capture_cleanup_failure(
                        cleanup_failures, "return controller cgroup processes",
                        lambda: _move_all_cgroup_processes(controller, cgroup_root),
                    )
                if controller.exists():
                    _capture_cleanup_failure(cleanup_failures, "remove controller cgroup", controller.rmdir)
                if primary is None and result is not None and worker_teardown_succeeded and not cleanup_failures:
                    def collect_result() -> None:
                        result["outputs"] = collect_drained_output(
                            output_fd, descriptor["limits"], {"populated": 0}
                        )
                    _capture_cleanup_failure(cleanup_failures, "collect confinement result", collect_result)
                if output_fd >= 0:
                    _capture_cleanup_failure(cleanup_failures, "close held output directory", lambda: os.close(output_fd))
                if primary is None and result is not None and not cleanup_failures:
                    def validate_and_publish() -> None:
                        payload = confinement_result_bytes(result)
                        _write_confinement_result_atomic(
                            root, resolve_within_repository(root, result_arg), payload
                        )
                        if session is not None:
                            session.result_published = True
                    _capture_cleanup_failure(
                        cleanup_failures, "validate and publish confinement result", validate_and_publish
                    )
                _finish_cleanup(primary, cleanup_failures)
        finally:
            primary = sys.exception()
            cleanup_failures = []
            _capture_cleanup_failure(cleanup_failures, "close held cgroup root", lambda: os.close(held_root))
            _finish_cleanup(primary, cleanup_failures)
    finally:
        primary = sys.exception()
        cleanup_failures = []
        _capture_cleanup_failure(cleanup_failures, "close held launcher", lambda: os.close(launcher.descriptor))
        _capture_cleanup_failure(cleanup_failures, "close held bubblewrap", lambda: os.close(bubblewrap.descriptor))
        _finish_cleanup(primary, cleanup_failures)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m ranex.cli.host_confinement")
    subcommands = parser.add_subparsers(dest="subcommand", required=True)
    build = subcommands.add_parser("launcher-build")
    build.add_argument("--manifest", required=True)
    build.add_argument("--source", required=True)
    build.add_argument("--output", required=True)
    install = subcommands.add_parser("launcher-install")
    install.add_argument("--manifest", required=True)
    install.add_argument("--artifact", required=True)
    install.add_argument("--destination", required=True)
    subcommands.add_parser("host-probe")
    qualify_parser = subcommands.add_parser("qualify")
    qualify_parser.add_argument("--profile", required=True)
    qualify_parser.add_argument("--artifact", required=True)
    qualify_parser.add_argument("--manifest", required=True)
    qualify_parser.add_argument("--report", required=True)
    session_parser = subcommands.add_parser("session")
    session_parser.add_argument("--profile", required=True)
    session_parser.add_argument("--host-profile", required=True)
    session_parser.add_argument("--artifact", required=True)
    session_parser.add_argument("--manifest", required=True)
    session_parser.add_argument("--qualification", required=True)
    session_parser.add_argument("--descriptor", required=True)
    session_parser.add_argument("--result", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    root = Path.cwd().resolve()
    try:
        if arguments.subcommand == "launcher-build":
            launcher_build(root, arguments.manifest, arguments.source, arguments.output)
        elif arguments.subcommand == "launcher-install":
            launcher_install(root, arguments.manifest, arguments.artifact, arguments.destination)
        elif arguments.subcommand == "host-probe":
            print(canonical_json(_validate_host_probe(collect_host_probe(), E_FACT)))
        elif arguments.subcommand == "qualify":
            qualify(
                root,
                arguments.profile,
                arguments.artifact,
                arguments.manifest,
                arguments.report,
            )
        elif arguments.subcommand == "session":
            confinement_session(
                root,
                profile_arg=arguments.profile,
                host_profile_arg=arguments.host_profile,
                artifact_arg=arguments.artifact,
                manifest_arg=arguments.manifest,
                qualification_arg=arguments.qualification,
                descriptor_arg=arguments.descriptor,
                result_arg=arguments.result,
            )
        else:
            _refuse(E_PROTOCOL, f"unknown subcommand {arguments.subcommand!r}")
    except HostConfinementError as exc:
        print(canonical_json({"detail": exc.detail, "refusal": exc.code}))
        return 1
    except (OSError, ValueError, KeyError, TypeError) as exc:
        fallback = E_BUILD_INPUT if arguments.subcommand == "launcher-build" else E_FACT
        if arguments.subcommand == "launcher-install":
            fallback = E_INSTALL
        elif arguments.subcommand == "qualify":
            fallback = E_FACT
        elif arguments.subcommand == "session":
            fallback = E_C18_GATE
        print(canonical_json({"detail": str(exc), "refusal": fallback}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
