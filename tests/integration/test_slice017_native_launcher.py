"""Frozen black-box acceptance tests for the SLICE-017 native launcher.

The implementation deliberately does not exist when this file is frozen.  These
tests therefore avoid importing it: collection must stay healthy while every
journey remains red until the controller, manifest, and native launcher exist.

The prose contract does not assign JSON member names to the build manifest or
host profile.  This suite freezes the narrow schema used below: build inputs are
``build.inputs`` entries with ``path`` and ``sha256`` members, the source is
``source``, the final object is ``artifact``, and a profile binds
``build_manifest_sha256`` plus ``artifact_sha256`` and has a ``helpers`` mapping
whose ``bubblewrap`` entry pins ``path`` and ``sha256``.  Those names are part of
the acceptance target, not guesses made by the future implementation.
"""

from __future__ import annotations

import contextlib
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import select
import shutil
import signal
import stat
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from launcher_host import build_closure_limitation, require_pinned_build_closure

REPOSITORY = Path(__file__).resolve().parents[2]
MANIFEST = Path("governance/confinement/native-launcher-build-v1.json")
PROFILE = Path("governance/confinement/strict-local-host-v1.json")
SOURCE = Path("native/ranex-worker-launcher/launcher.c")
BUILD_ARTIFACT = Path(
    ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
)
INSTALLED_ARTIFACT = Path(
    ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
)
QUALIFICATION_REPORT = Path(".local/ranex/qualification/strict-local-v1.json")

# See the note in tests/security/test_slice017_host_qualification.py: the
# governed run has no `uv` on its pinned PATH, so reaching the controller
# through it erased this file's evidence inside the gating run.
CONTROLLER = (
    sys.executable,
    "-m",
    "ranex.cli.host_confinement",
)
BUILD_INPUT_DRIFT = "E-C17-BUILD-INPUT-DRIFT"
BUILD_UNTRACED_INPUT = "E-C17-BUILD-UNTRACED-INPUT"
INSTALL_REFUSED = "E-C17-INSTALL-REFUSED"
EXEC_OBJECT_DRIFT = "E-C17-EXEC-OBJECT-DRIFT"
PROTOCOL_REFUSED = "E-C17-PROTOCOL"

PROTOCOL = "ranex-launcher-v1"
INJECTED_SECRET_NAME = "RANEX_SLICE017_INJECTED_SECRET"
SYS_EXECVEAT = 322
SYS_KEYCTL = 250
AT_EMPTY_PATH = 0x1000
KEYCTL_JOIN_SESSION_KEYRING = 1
RESPONSE_LIMIT = 65_536
# SLICE-020 deliberately changes the production entrypoint to protect and root
# verdict-key loading/publication while retaining the frozen launcher boundary.
# SLICE-047 deliberately refreshes this pin for its confined-controller boundary.
# SLICE-054 (ADR-031) refreshes it again for the observability stage boundary.
# SLICE-056 (#36 sad path 3) refreshes it for the journal-verify row-naming
# presentation in cmd_journal_verify's FAIL output.
# SLICE-060 (#40) refreshes it for the mixed-verdict presentation dedup in
# cmd_gate_evaluate's FAIL output, and again for the qa-gate remediation:
# anchored suffix dedup that steps aside on ambiguous claim IDs.
# The CI lint-debt repair (fix/ci-lint-debt, off main 5e1ea681d) refreshes
# it for ruff 0.16.2 isort reordering only: the two ranex.observability
# import statements re-split their names into canonical order; no other
# statement added, removed, or changed.
MAIN_PY_SHA256 = "996939c90ebd85f7cf9e253708d42967ec9e6fafd61d5329730dcdc9a109b6d7"

PTRACE_TRACEME = 0
PTRACE_CONT = 7
PTRACE_KILL = 8
PTRACE_GETREGS = 12
PTRACE_SYSCALL = 24
PTRACE_SETOPTIONS = 0x4200
PTRACE_GETEVENTMSG = 0x4201
PTRACE_O_TRACESYSGOOD = 0x00000001
PTRACE_O_TRACEFORK = 0x00000002
PTRACE_O_TRACEVFORK = 0x00000004
PTRACE_O_TRACECLONE = 0x00000008
PTRACE_O_TRACEEXEC = 0x00000010
PTRACE_EVENT_FORK = 1
PTRACE_EVENT_VFORK = 2
PTRACE_EVENT_CLONE = 3
PTRACE_EVENT_EXEC = 4
WAIT_ALL = 0x40000000


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


class UserRegsStruct(ctypes.Structure):
    """Linux x86-64 ``struct user_regs_struct``."""

    _fields_ = [
        ("r15", ctypes.c_ulonglong),
        ("r14", ctypes.c_ulonglong),
        ("r13", ctypes.c_ulonglong),
        ("r12", ctypes.c_ulonglong),
        ("rbp", ctypes.c_ulonglong),
        ("rbx", ctypes.c_ulonglong),
        ("r11", ctypes.c_ulonglong),
        ("r10", ctypes.c_ulonglong),
        ("r9", ctypes.c_ulonglong),
        ("r8", ctypes.c_ulonglong),
        ("rax", ctypes.c_ulonglong),
        ("rcx", ctypes.c_ulonglong),
        ("rdx", ctypes.c_ulonglong),
        ("rsi", ctypes.c_ulonglong),
        ("rdi", ctypes.c_ulonglong),
        ("orig_rax", ctypes.c_ulonglong),
        ("rip", ctypes.c_ulonglong),
        ("cs", ctypes.c_ulonglong),
        ("eflags", ctypes.c_ulonglong),
        ("rsp", ctypes.c_ulonglong),
        ("ss", ctypes.c_ulonglong),
        ("fs_base", ctypes.c_ulonglong),
        ("gs_base", ctypes.c_ulonglong),
        ("ds", ctypes.c_ulonglong),
        ("es", ctypes.c_ulonglong),
        ("fs", ctypes.c_ulonglong),
        ("gs", ctypes.c_ulonglong),
    ]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    assert isinstance(value, dict)
    return value


def _write_canonical(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _manifest_inputs(manifest: Mapping[str, Any]) -> list[dict[str, str]]:
    build = manifest["build"]
    assert isinstance(build, dict)
    inputs = build["inputs"]
    assert isinstance(inputs, list)
    assert all(isinstance(item, dict) for item in inputs)
    return inputs


def _manifest_artifact(manifest: Mapping[str, Any]) -> dict[str, Any]:
    artifact = manifest["artifact"]
    assert isinstance(artifact, dict)
    return artifact


def _manifest_source(manifest: Mapping[str, Any]) -> dict[str, Any]:
    source = manifest["source"]
    assert isinstance(source, dict)
    return source


def _copy_repository(destination: Path, *, include_outputs: bool = False) -> Path:
    ignored = [
        ".git",
        ".venv",
        ".uv-cache",
        "mutants",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    ]
    if not include_outputs:
        ignored.append(".local")
    return Path(
        shutil.copytree(
            REPOSITORY,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(*ignored),
        )
    )


def _controller_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = "src"
    environment["UV_OFFLINE"] = "1"
    return environment


def _run_controller(
    root: Path,
    subcommand: str,
    *arguments: str | Path,
    timeout: float = 180.0,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [*CONTROLLER, subcommand, *(str(argument) for argument in arguments)],
        cwd=root,
        env=_controller_environment(),
        capture_output=True,
        check=False,
        timeout=timeout,
    )


def _qualify_arguments() -> tuple[str | Path, ...]:
    return (
        "--profile",
        PROFILE,
        "--artifact",
        INSTALLED_ARTIFACT,
        "--manifest",
        MANIFEST,
        "--report",
        QUALIFICATION_REPORT,
    )


def _refusal(
    completed: subprocess.CompletedProcess[bytes], expected: str | set[str]
) -> dict[str, Any]:
    assert completed.returncode != 0
    refusal = json.loads(completed.stdout)
    assert isinstance(refusal, dict)
    assert set(refusal) == {"refusal", "detail"}
    expected_codes = {expected} if isinstance(expected, str) else expected
    assert refusal["refusal"] in expected_codes
    assert isinstance(refusal["detail"], str) and refusal["detail"]
    report = REPOSITORY / QUALIFICATION_REPORT
    assert not report.exists()
    if report.parent.exists():
        assert not any(
            child.name.startswith(f".{report.name}.")
            or child.name.startswith(f"{report.name}.")
            for child in report.parent.iterdir()
        )
    return refusal


def _build(root: Path, *, manifest: Path = MANIFEST) -> subprocess.CompletedProcess[bytes]:
    return _run_controller(
        root,
        "launcher-build",
        "--manifest",
        str(manifest),
        "--source",
        str(SOURCE),
        "--output",
        str(BUILD_ARTIFACT),
    )


def _install(
    root: Path,
    *,
    manifest: Path = MANIFEST,
) -> subprocess.CompletedProcess[bytes]:
    return _run_controller(
        root,
        "launcher-install",
        "--manifest",
        str(manifest),
        "--artifact",
        str(BUILD_ARTIFACT),
        "--destination",
        str(INSTALLED_ARTIFACT),
    )


def _qualify(
    root: Path,
    *,
    artifact: Path = INSTALLED_ARTIFACT,
    manifest: Path = MANIFEST,
    profile: Path = PROFILE,
    report: Path = QUALIFICATION_REPORT,
    timeout: float = 180.0,
) -> subprocess.CompletedProcess[bytes]:
    return _run_controller(
        root,
        "qualify",
        "--profile",
        str(profile),
        "--artifact",
        str(artifact),
        "--manifest",
        str(manifest),
        "--report",
        str(report),
        timeout=timeout,
    )


def _assert_success(result: subprocess.CompletedProcess[bytes]) -> None:
    assert result.returncode == 0, (
        f"stdout={result.stdout.decode(errors='replace')!r} "
        f"stderr={result.stderr.decode(errors='replace')!r}"
    )


def _assert_refusal(
    result: subprocess.CompletedProcess[bytes],
    expected: str,
) -> dict[str, object]:
    assert result.returncode != 0
    stdout = result.stdout.strip()
    assert stdout, f"missing refusal; stderr={result.stderr.decode(errors='replace')!r}"
    value = json.loads(stdout)
    assert isinstance(value, dict)
    assert set(value) == {"detail", "refusal"}
    assert value["refusal"] == expected
    assert isinstance(value["detail"], str) and value["detail"]
    return value


def _assert_no_partial(path: Path) -> None:
    assert not os.path.lexists(path)
    if path.parent.exists():
        assert not any(
            child.name.startswith(f".{path.name}.")
            or child.name.startswith(f"{path.name}.")
            for child in path.parent.iterdir()
        )


@pytest.fixture(scope="module")
def built_repository(tmp_path_factory: pytest.TempPathFactory) -> Path:
    require_pinned_build_closure()
    root = _copy_repository(tmp_path_factory.mktemp("slice017-built") / "repository")
    result = _build(root)
    _assert_success(result)
    artifact = root / BUILD_ARTIFACT
    assert artifact.is_file()
    return root


def _case_from_built(tmp_path: Path, built_repository: Path) -> Path:
    return Path(
        shutil.copytree(
            built_repository,
            tmp_path / "repository",
            symlinks=True,
            ignore=shutil.ignore_patterns(
                ".venv",
                ".uv-cache",
                "mutants",
                "__pycache__",
                ".pytest_cache",
                ".ruff_cache",
            ),
        )
    )


def _installed_case(tmp_path: Path, built_repository: Path) -> Path:
    root = _case_from_built(tmp_path, built_repository)
    result = _install(root)
    _assert_success(result)
    installed = root / INSTALLED_ARTIFACT
    assert installed.is_file()
    assert stat.S_IMODE(installed.stat().st_mode) == 0o555
    return root


def test_gate1_clean_builds_in_different_absolute_roots_match_manifest(
    tmp_path: Path,
) -> None:
    if build_closure_limitation() is not None:
        # A host outside the pin cannot prove reproducibility. Its honest
        # contract is the controller refusing the foreign build closure.
        root = _copy_repository(tmp_path / "foreign-build-closure" / "repository")
        _assert_refusal(_build(root), BUILD_INPUT_DRIFT)
        return
    first_root = _copy_repository(tmp_path / "first-absolute-root" / "repository")
    second_root = _copy_repository(tmp_path / "second-absolute-root" / "repository")
    assert first_root.resolve().parent != second_root.resolve().parent

    first_result = _build(first_root)
    second_result = _build(second_root)
    _assert_success(first_result)
    _assert_success(second_result)

    first_bytes = (first_root / BUILD_ARTIFACT).read_bytes()
    second_bytes = (second_root / BUILD_ARTIFACT).read_bytes()
    assert first_bytes == second_bytes

    # The committed manifest IS the artifact pin, so gate 1 does not carry a
    # second hardcoded digest: a constant written before launcher.c existed
    # cannot be satisfied by any correct implementation, and one written after
    # would only restate the manifest. What binds here is that the two builds
    # agree with each other AND with the digest the manifest records.
    manifest = _read_json(first_root / MANIFEST)
    expected = _manifest_artifact(manifest)["sha256"]
    assert _sha256_bytes(first_bytes) == expected
    assert _sha256_bytes(second_bytes) == expected


def test_gate2_manifest_pins_the_whole_closure_by_bytes() -> None:
    manifest = _read_json(REPOSITORY / MANIFEST)
    inputs = _manifest_inputs(manifest)

    limitation = build_closure_limitation()
    if limitation is not None:
        # The foreign host disagrees with a pin by bytes; gate 1 therefore
        # fails closed rather than treating this absence as a passing build.
        mismatch = next(
            (
                item
                for item in inputs
                if Path(item["path"]).is_absolute()
                and Path(item["path"]).is_file()
                and _sha256_file(Path(item["path"])) != item["sha256"]
            ),
            None,
        )
        assert mismatch is not None, limitation
        return

    paths = [item["realpath"] for item in inputs]
    headers = [
        path
        for path in paths
        if path.startswith("/usr/include/")
        or (path.startswith("/usr/lib/gcc/") and "/include/" in path)
    ]
    # The closure size depends on launcher.c's includes, so it is deliberately not
    # asserted as a count: a magic number fails for the wrong reason on any include
    # change and invites padding the manifest to reach it. The binding invariants
    # are that every pinned digest matches the bytes on disk, that the load-bearing
    # toolchain objects below are present, and that adding, removing or replacing
    # any traced input refuses (the gate-2 behaviour tests that follow).
    assert headers, "a closure with no headers cannot be a real traced C build"
    for item in inputs:
        assert set(item) >= {"path", "realpath", "role", "sha256"}
        declared = Path(item["path"])
        source = Path(item["realpath"])
        assert declared.is_absolute()
        assert source.is_absolute()
        assert not source.is_symlink()
        assert source == declared.resolve(strict=True)
        assert source == source.resolve(strict=True)
        assert len(item["sha256"]) == 64
        int(item["sha256"], 16)
        assert _sha256_bytes(source.read_bytes()) == item["sha256"], (
            f"manifest pins {source} to a digest that is not its bytes on disk"
        )

    required_roles = {
        "cc1",
        "as",
        "ld",
        "crt",
        "libgcc",
        "libc",
    }
    assert required_roles <= {item["role"] for item in inputs}

    build = manifest["build"]
    assert isinstance(build, dict)
    tracer = build["tracer"]
    assert isinstance(tracer, dict)
    assert set(tracer) >= {"path", "sha256"}
    tracer_path = Path(tracer["path"])
    assert tracer_path.is_absolute() and not tracer_path.is_symlink()
    assert _sha256_file(tracer_path) == tracer["sha256"]


def test_gate2_deleting_a_traced_header_refuses_input_drift(
    tmp_path: Path,
) -> None:
    root = _copy_repository(tmp_path / "repository")
    manifest = _read_json(root / MANIFEST)
    inputs = _manifest_inputs(manifest)
    header_index = next(
        index
        for index, item in enumerate(inputs)
        if item["path"].startswith("/usr/include/")
    )
    inputs.pop(header_index)
    mutated = Path("governance/confinement/test-deleted-header.json")
    _write_canonical(root / mutated, manifest)

    result = _build(root, manifest=mutated)
    _assert_refusal(result, BUILD_INPUT_DRIFT)
    _assert_no_partial(root / BUILD_ARTIFACT)


def test_gate2_replacing_a_crt_object_digest_refuses_input_drift(
    tmp_path: Path,
) -> None:
    root = _copy_repository(tmp_path / "repository")
    manifest = _read_json(root / MANIFEST)
    crt = next(
        item
        for item in _manifest_inputs(manifest)
        if Path(item["path"]).name == "Scrt1.o"
    )
    crt["sha256"] = "0" * 64
    mutated = Path("governance/confinement/test-replaced-crt.json")
    _write_canonical(root / mutated, manifest)

    result = _build(root, manifest=mutated)
    _assert_refusal(result, BUILD_INPUT_DRIFT)
    _assert_no_partial(root / BUILD_ARTIFACT)


def test_gate2_adding_an_unobserved_closure_input_refuses_untraced_input(
    tmp_path: Path,
) -> None:
    root = _copy_repository(tmp_path / "repository")
    manifest = _read_json(root / MANIFEST)
    inputs = _manifest_inputs(manifest)
    assert all(item["path"] != "/etc/passwd" for item in inputs)
    inputs.append({"path": "/etc/passwd", "sha256": _sha256_file(Path("/etc/passwd"))})
    inputs.sort(key=lambda item: item["path"])
    mutated = Path("governance/confinement/test-added-input.json")
    _write_canonical(root / mutated, manifest)

    result = _build(root, manifest=mutated)
    _assert_refusal(result, BUILD_UNTRACED_INPUT)
    _assert_no_partial(root / BUILD_ARTIFACT)


def test_gate2_real_compilation_change_refuses_an_untraced_open(
    tmp_path: Path,
) -> None:
    root = _copy_repository(tmp_path / "repository")
    manifest = _read_json(root / MANIFEST)
    source = root / SOURCE
    extra_header = source.with_name("slice017-extra-real-input.h")
    extra_header.write_text("#define SLICE017_EXTRA_REAL_INPUT 1\n", encoding="utf-8")
    source.write_text(
        '#include "slice017-extra-real-input.h"\n' + source.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    _manifest_source(manifest)["sha256"] = _sha256_file(source)
    mutated = Path("governance/confinement/test-real-extra-include.json")
    _write_canonical(root / mutated, manifest)

    result = _build(root, manifest=mutated)
    _assert_refusal(result, BUILD_UNTRACED_INPUT)
    _assert_no_partial(root / BUILD_ARTIFACT)


def test_gate3_install_refuses_a_symlink_staging_artifact(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _case_from_built(tmp_path, built_repository)
    artifact = root / BUILD_ARTIFACT
    backing = artifact.with_name("verified-bytes")
    artifact.rename(backing)
    artifact.symlink_to(backing.name)

    result = _install(root)
    _assert_refusal(result, INSTALL_REFUSED)
    _assert_no_partial(root / INSTALLED_ARTIFACT)


def test_gate3_install_refuses_a_symlink_destination(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _case_from_built(tmp_path, built_repository)
    destination = root / INSTALLED_ARTIFACT
    destination.parent.mkdir(parents=True)
    destination.symlink_to("missing-target")

    result = _install(root)
    _assert_refusal(result, INSTALL_REFUSED)
    assert destination.is_symlink()
    assert os.readlink(destination) == "missing-target"
    assert {child.name for child in destination.parent.iterdir()} == {destination.name}


def test_gate3_install_refuses_an_existing_destination_without_replacement(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _case_from_built(tmp_path, built_repository)
    destination = root / INSTALLED_ARTIFACT
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"existing-destination\n")
    destination.chmod(0o555)

    result = _install(root)
    _assert_refusal(result, INSTALL_REFUSED)
    assert destination.read_bytes() == b"existing-destination\n"
    assert {child.name for child in destination.parent.iterdir()} == {destination.name}


def test_gate3_install_refuses_a_writable_staging_mode(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _case_from_built(tmp_path, built_repository)
    (root / BUILD_ARTIFACT).chmod(0o777)

    result = _install(root)
    _assert_refusal(result, INSTALL_REFUSED)
    _assert_no_partial(root / INSTALLED_ARTIFACT)


def test_gate3_install_refuses_staging_byte_drift(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _case_from_built(tmp_path, built_repository)
    artifact = root / BUILD_ARTIFACT
    artifact.chmod(0o755)
    with artifact.open("ab") as handle:
        handle.write(b"slice017-byte-drift")
    artifact.chmod(0o555)

    result = _install(root)
    _assert_refusal(result, INSTALL_REFUSED)
    _assert_no_partial(root / INSTALLED_ARTIFACT)


def test_gate3_install_refuses_staging_elf_fact_drift(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _case_from_built(tmp_path, built_repository)
    artifact = root / BUILD_ARTIFACT
    changed = bytearray(artifact.read_bytes())
    assert changed[:4] == b"\x7fELF"
    assert changed[16:18] == b"\x03\x00"  # ET_DYN/PIE in little-endian ELF64.
    changed[16:18] = b"\x02\x00"  # A parseable but forbidden ET_EXEC object.
    artifact.chmod(0o755)
    artifact.write_bytes(changed)
    artifact.chmod(0o555)
    manifest = _read_json(root / MANIFEST)
    _manifest_artifact(manifest)["sha256"] = _sha256_bytes(changed)
    mutated = Path("governance/confinement/test-wrong-elf-facts.json")
    _write_canonical(root / mutated, manifest)

    result = _install(root, manifest=mutated)
    _assert_refusal(result, INSTALL_REFUSED)
    _assert_no_partial(root / INSTALLED_ARTIFACT)


def _libc() -> ctypes.CDLL:
    return ctypes.CDLL(None, use_errno=True)


def _ptrace(
    request: int,
    pid: int,
    address: int = 0,
    data: int | object = 0,
) -> int:
    libc = _libc()
    data_pointer = (
        ctypes.c_void_p(data)
        if isinstance(data, int)
        else ctypes.cast(ctypes.byref(data), ctypes.c_void_p)
    )
    result = libc.ptrace(
        ctypes.c_uint(request),
        ctypes.c_int(pid),
        ctypes.c_void_p(address),
        data_pointer,
    )
    if result == -1:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return int(result)


def _tracee_string(pid: int, address: int) -> bytes:
    if address == 0:
        return b""
    descriptor = os.open(f"/proc/{pid}/mem", os.O_RDONLY | os.O_CLOEXEC)
    try:
        value = os.pread(descriptor, 4096, address)
    finally:
        os.close(descriptor)
    return value.split(b"\0", 1)[0]


def _same_object(left: os.stat_result, right: os.stat_result) -> bool:
    return left.st_dev == right.st_dev and left.st_ino == right.st_ino


def _fd_stat(pid: int, descriptor: int) -> os.stat_result | None:
    try:
        return os.stat(f"/proc/{pid}/fd/{descriptor}")
    except OSError:
        return None


def _proc_fd_path_stat(pid: int, executable: bytes) -> os.stat_result | None:
    parts = executable.decode(errors="surrogateescape").split("/")
    try:
        fd_index = parts.index("fd")
        descriptor = int(parts[fd_index + 1])
    except (ValueError, IndexError):
        return None
    return _fd_stat(pid, descriptor)


def _kill_tracees(tracees: set[int]) -> None:
    pending = set(tracees)
    for pid in pending:
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    deadline = time.monotonic() + 5.0
    while pending and time.monotonic() < deadline:
        for pid in tuple(pending):
            try:
                waited, _status = os.waitpid(pid, os.WNOHANG | WAIT_ALL)
            except ChildProcessError:
                pending.discard(pid)
                tracees.discard(pid)
                continue
            if waited == pid:
                pending.discard(pid)
                tracees.discard(pid)
        if pending:
            time.sleep(0.01)
    assert not pending, f"ptrace cleanup did not reap tracees before deadline: {pending}"


def _controller_qualify_argv() -> list[str]:
    return [
        *CONTROLLER,
        "qualify",
        "--profile",
        str(PROFILE),
        "--artifact",
        str(INSTALLED_ARTIFACT),
        "--manifest",
        str(MANIFEST),
        "--report",
        str(QUALIFICATION_REPORT),
    ]


def _trace_controller_swap(root: Path, original: Path, impostor: Path) -> None:
    original_stat = original.stat()
    stdout_path = root / ".local/slice017-trace-stdout"
    stderr_path = root / ".local/slice017-trace-stderr"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_fd = os.open(stdout_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    stderr_fd = os.open(stderr_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)

    pid = os.fork()
    if pid == 0:
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.close(stdout_fd)
        os.close(stderr_fd)
        os.chdir(root)
        if _ptrace(PTRACE_TRACEME, 0) != 0:
            os._exit(125)
        os.kill(os.getpid(), signal.SIGSTOP)
        os.execve(CONTROLLER[0], _controller_qualify_argv(), _controller_environment())
        os._exit(126)

    os.close(stdout_fd)
    os.close(stderr_fd)
    tracees = {pid}
    entering: dict[int, bool] = {pid: True}
    swapped_pid: int | None = None
    executed_original = False
    deadline = time.monotonic() + 180.0
    try:
        waited_pid, status = os.waitpid(pid, 0)
        assert waited_pid == pid and os.WIFSTOPPED(status)
        options = (
            PTRACE_O_TRACESYSGOOD
            | PTRACE_O_TRACEFORK
            | PTRACE_O_TRACEVFORK
            | PTRACE_O_TRACECLONE
            | PTRACE_O_TRACEEXEC
        )
        _ptrace(PTRACE_SETOPTIONS, pid, 0, options)
        _ptrace(PTRACE_SYSCALL, pid)

        while tracees and time.monotonic() < deadline and not executed_original:
            waited_pid, status = os.waitpid(-1, WAIT_ALL)
            if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                tracees.discard(waited_pid)
                entering.pop(waited_pid, None)
                continue
            if not os.WIFSTOPPED(status):
                continue

            stop_signal = os.WSTOPSIG(status)
            event = status >> 16
            if event in {PTRACE_EVENT_FORK, PTRACE_EVENT_VFORK, PTRACE_EVENT_CLONE}:
                child = ctypes.c_ulonglong()
                _ptrace(PTRACE_GETEVENTMSG, waited_pid, 0, child)
                tracees.add(int(child.value))
                entering[int(child.value)] = True
            elif event == PTRACE_EVENT_EXEC:
                entering[waited_pid] = True
                if waited_pid == swapped_pid:
                    executed_original = _same_object(
                        os.stat(f"/proc/{waited_pid}/exe"), original_stat
                    )
            elif stop_signal == signal.SIGTRAP | 0x80:
                at_entry = entering.get(waited_pid, True)
                entering[waited_pid] = not at_entry
                if at_entry:
                    registers = UserRegsStruct()
                    _ptrace(PTRACE_GETREGS, waited_pid, 0, registers)
                    syscall_number = ctypes.c_longlong(registers.orig_rax).value
                    if syscall_number == 59:
                        executable = _tracee_string(waited_pid, registers.rdi)
                        reopened = _proc_fd_path_stat(waited_pid, executable)
                        if reopened is not None and _same_object(reopened, original_stat):
                            raise AssertionError(
                                "controller used a procfs pathname re-open instead of execveat"
                            )
                    elif syscall_number == SYS_EXECVEAT:
                        descriptor = ctypes.c_longlong(registers.rdi).value
                        target = _fd_stat(waited_pid, descriptor)
                        if target is not None and _same_object(target, original_stat):
                            assert _tracee_string(waited_pid, registers.rsi) == b""
                            assert registers.r8 == AT_EMPTY_PATH
                            assert swapped_pid is None
                            os.replace(impostor, original)
                            swapped_pid = waited_pid

            delivered_signal = 0
            if event == 0 and stop_signal not in {
                signal.SIGSTOP,
                signal.SIGTRAP,
                signal.SIGTRAP | 0x80,
            }:
                delivered_signal = stop_signal
            _ptrace(PTRACE_SYSCALL, waited_pid, 0, delivered_signal)

        assert swapped_pid is not None, (
            f"no execveat of the verified launcher observed; "
            f"stderr={stderr_path.read_text(errors='replace')!r}"
        )
        assert executed_original
    finally:
        _kill_tracees(tracees)


def test_gate4_controller_execveat_survives_a_real_pathname_swap(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller(REPOSITORY, "qualify", *_qualify_arguments())
        _refusal(completed, EXEC_OBJECT_DRIFT)
        return
    root = _installed_case(tmp_path, built_repository)
    installed = root / INSTALLED_ARTIFACT
    impostor = installed.with_name("pathname-swap-impostor")
    shutil.copy2("/usr/bin/false", impostor)
    impostor.chmod(0o555)
    impostor_stat = impostor.stat()

    _trace_controller_swap(root, installed, impostor)
    assert not impostor.exists()
    assert _same_object(installed.stat(), impostor_stat)


def test_gate4_writable_launcher_chain_refuses_before_exec(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _installed_case(tmp_path, built_repository)
    (root / INSTALLED_ARTIFACT).chmod(0o755)

    result = _qualify(root)
    _assert_refusal(result, EXEC_OBJECT_DRIFT)
    _assert_no_partial(root / QUALIFICATION_REPORT)


def _file_capable_binary() -> Path:
    for directory in (Path("/usr/bin"), Path("/usr/sbin"), Path("/usr/libexec")):
        if not directory.is_dir():
            continue
        for candidate in sorted(directory.iterdir()):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            try:
                capability = os.getxattr(candidate, "security.capability")
            except OSError:
                continue
            if capability and os.access(candidate, os.X_OK):
                return candidate
    raise AssertionError("host has no discoverable executable with security.capability")


def _profile_pinning_helper(root: Path, helper: Path, name: str) -> Path:
    profile = _read_json(root / PROFILE)
    helpers = profile["helpers"]
    assert isinstance(helpers, dict)
    bubblewrap = helpers["bubblewrap"]
    assert isinstance(bubblewrap, dict)
    bubblewrap["path"] = str(helper)
    bubblewrap["sha256"] = _sha256_file(helper)
    path = Path(f"governance/confinement/{name}.json")
    _write_canonical(root / path, profile)
    return path


def test_gate4_file_capability_is_the_differential_refusal_fact(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller(REPOSITORY, "qualify", *_qualify_arguments())
        _refusal(completed, EXEC_OBJECT_DRIFT)
        return
    capable = _file_capable_binary()
    capability = os.getxattr(capable, "security.capability")
    assert capability
    capable_root = _installed_case(tmp_path / "capable", built_repository)
    stripped_root = _installed_case(tmp_path / "stripped", built_repository)
    stripped = stripped_root / ".local/ranex/file-capability-differential"
    stripped.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(capable, stripped)
    assert _sha256_file(stripped) == _sha256_file(capable)
    assert stat.S_IMODE(stripped.stat().st_mode) == stat.S_IMODE(capable.stat().st_mode)
    assert "security.capability" not in os.listxattr(stripped)

    capable_profile = _profile_pinning_helper(
        capable_root, capable, "test-file-capable-helper"
    )
    stripped_profile = _profile_pinning_helper(
        stripped_root, stripped, "test-capability-stripped-helper"
    )

    capable_result = _qualify(capable_root, profile=capable_profile)
    capable_refusal = _assert_refusal(capable_result, EXEC_OBJECT_DRIFT)
    assert "capab" in str(capable_refusal["detail"]).lower()
    _assert_no_partial(capable_root / QUALIFICATION_REPORT)

    stripped_result = _qualify(stripped_root, profile=stripped_profile)
    stripped_report = stripped_root / QUALIFICATION_REPORT
    if stripped_result.returncode == 0:
        assert _read_json(stripped_report)["qualified"] is True
        stripped_report.unlink()
    else:
        stripped_refusal = _assert_refusal(stripped_result, EXEC_OBJECT_DRIFT)
        assert "capab" not in str(stripped_refusal["detail"]).lower()
        _assert_no_partial(stripped_report)


def _high_cloexec(descriptor: int) -> int:
    return int(fcntl.fcntl(descriptor, fcntl.F_DUPFD_CLOEXEC, 64))


def _execveat(descriptor: int, argv: Sequence[str], environment: Mapping[str, str]) -> None:
    argv_values = [value.encode() for value in argv]
    environment_values = [f"{key}={value}".encode() for key, value in environment.items()]
    argv_array = (ctypes.c_char_p * (len(argv_values) + 1))(*argv_values, None)
    environment_array = (ctypes.c_char_p * (len(environment_values) + 1))(
        *environment_values, None
    )
    result = _libc().syscall(
        ctypes.c_long(SYS_EXECVEAT),
        ctypes.c_int(descriptor),
        ctypes.c_char_p(b""),
        argv_array,
        environment_array,
        ctypes.c_int(AT_EMPTY_PATH),
    )
    error = ctypes.get_errno()
    os.write(5, f"execveat failed: result={result} errno={error}\n".encode())
    os._exit(127)


def _join_injected_session_keyring() -> int:
    result = _libc().syscall(
        ctypes.c_long(SYS_KEYCTL),
        ctypes.c_long(KEYCTL_JOIN_SESSION_KEYRING),
        ctypes.c_char_p(b"ranex-slice017-injected-session"),
    )
    if result < 0:
        error = ctypes.get_errno()
        os.write(5, f"keyctl injection failed: errno={error}\n".encode())
        os._exit(125)
    return int(result)


def _assert_blocked_reading_gate(pid: int, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    last_observation = ""
    while time.monotonic() < deadline:
        try:
            last_observation = Path(f"/proc/{pid}/syscall").read_text().strip()
        except OSError as error:
            last_observation = repr(error)
        fields = last_observation.split()
        if len(fields) >= 2 and fields[0] == "0" and int(fields[1], 16) == 3:
            return
        time.sleep(0.01)
    raise AssertionError(
        f"launcher was not observed blocked in read(3, ...): {last_observation!r}"
    )


def _wait_child(pid: int, timeout: float = 20.0) -> int:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        waited, status = os.waitpid(pid, os.WNOHANG)
        if waited == pid:
            return status
        time.sleep(0.01)
    os.kill(pid, signal.SIGKILL)
    os.waitpid(pid, 0)
    raise AssertionError("native launcher did not exit before timeout")


def _read_pipe(descriptor: int, timeout: float = 20.0) -> bytes:
    output = bytearray()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        readable, _, _ = select.select([descriptor], [], [], 0.1)
        if not readable:
            continue
        block = os.read(descriptor, 8192)
        if not block:
            return bytes(output)
        output.extend(block)
    raise AssertionError("native launcher response pipe did not close")


def _launch_protocol(
    artifact: Path,
    request: bytes,
    *,
    injected_secret: bool = False,
    injected_fd: Path | None = None,
    injected_keyring: bool = False,
    prove_gate: bool = False,
    secret_expected_at_gate: bool = False,
    argv: Sequence[str] | None = None,
) -> tuple[int, bytes, int | None, int | None]:
    gate_read, gate_write = os.pipe2(os.O_CLOEXEC)
    request_read, request_write = os.pipe2(os.O_CLOEXEC)
    response_read, response_write = os.pipe2(os.O_CLOEXEC)
    metadata_read, metadata_write = os.pipe2(os.O_CLOEXEC)
    launcher_fd = os.open(artifact, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
    child_gate = _high_cloexec(gate_read)
    child_request = _high_cloexec(request_read)
    child_response = _high_cloexec(response_write)
    child_launcher = _high_cloexec(launcher_fd)
    unexpected = -1
    if injected_fd is not None:
        source = os.open(injected_fd, os.O_RDONLY | os.O_CLOEXEC)
        unexpected = _high_cloexec(source)
        os.close(source)

    os.write(request_write, request)
    os.close(request_write)
    environment = {"LC_ALL": "C", "TZ": "UTC"}
    if injected_secret:
        environment[INJECTED_SECRET_NAME] = "must-not-survive"

    pid = os.fork()
    child_reaped = False
    if pid == 0:
        os.dup2(child_gate, 3, inheritable=True)
        os.dup2(child_request, 4, inheritable=True)
        os.dup2(child_response, 5, inheritable=True)
        if unexpected >= 0:
            os.set_inheritable(unexpected, True)
        keyring_id = -1
        if injected_keyring:
            keyring_id = _join_injected_session_keyring()
        os.write(metadata_write, keyring_id.to_bytes(8, "little", signed=True))
        controlled_descriptors = {3, 4, 5, unexpected}
        inherited_descriptors = [
            int(entry.name) for entry in os.scandir("/proc/self/fd")
        ]
        for descriptor in inherited_descriptors:
            if descriptor in controlled_descriptors:
                continue
            try:
                os.set_inheritable(descriptor, False)
            except OSError as error:
                # The directory descriptor used by scandir is closed before this
                # loop and may still be present in the enumeration snapshot.
                if error.errno != errno.EBADF:
                    raise
        _execveat(child_launcher, argv or [str(artifact)], environment)

    os.close(metadata_write)
    for descriptor in (
        gate_read,
        request_read,
        response_write,
        launcher_fd,
        child_gate,
        child_request,
        child_response,
        child_launcher,
        unexpected,
    ):
        if descriptor >= 0:
            os.close(descriptor)

    try:
        metadata = os.read(metadata_read, 8)
        assert len(metadata) == 8, "launcher child did not confirm injected keyring state"
        keyring_value = int.from_bytes(metadata, "little", signed=True)
        if prove_gate:
            _assert_blocked_reading_gate(pid)
            observed_environment = Path(f"/proc/{pid}/environ").read_bytes()
            assert (
                INJECTED_SECRET_NAME.encode() in observed_environment
            ) is secret_expected_at_gate
            if unexpected >= 0:
                assert not os.path.lexists(f"/proc/{pid}/fd/{unexpected}")
            readable, _, _ = select.select([response_read], [], [], 0.35)
            assert not readable, "launcher performed work before FD 3 was released"
            waited, _status = os.waitpid(pid, os.WNOHANG)
            assert waited == 0, "launcher exited before FD 3 was released"
        os.write(gate_write, b"1")
        os.close(gate_write)
        gate_write = -1
        response = _read_pipe(response_read)
        status = _wait_child(pid)
        child_reaped = True
        return (
            status,
            response,
            unexpected if unexpected >= 0 else None,
            keyring_value if keyring_value >= 0 else None,
        )
    finally:
        if gate_write >= 0:
            os.close(gate_write)
        os.close(metadata_read)
        os.close(response_read)
        if not child_reaped:
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
            with contextlib.suppress(ChildProcessError):
                os.waitpid(pid, 0)


def _protocol_response(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw)
    assert isinstance(value, dict)
    assert raw == _canonical_bytes(value)
    assert set(value) == {"probes", "protocol", "refusal"}
    assert value["protocol"] == PROTOCOL
    assert isinstance(value["probes"], dict)
    return value


def _assert_protocol_refusal_exit(status: int) -> None:
    # WIFEXITED is what separates a deliberate refusal from a signal death such as
    # SIGSEGV — that is the property worth asserting. The specific non-zero value is
    # NOT pinned: neither the slice nor the frozen contract fixes one ("any refusal =
    # non-zero exit"), so pinning a number here would invent a contract value and fail
    # a correct implementation that chose a different one.
    assert os.WIFEXITED(status), f"protocol refusal died by signal: status={status}"
    assert os.WEXITSTATUS(status) != 0, "a protocol refusal must not exit 0"


def _valid_request(*additional_allowlisted_names: str) -> bytes:
    return _canonical_bytes(
        {
            "protocol": PROTOCOL,
            "action": "qualify-probe",
            "env_allowlist": ["LC_ALL", "TZ", *additional_allowlisted_names],
        }
    )


def test_gate7_real_launcher_blocks_then_removes_secret_fd_env_and_keyring(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _installed_case(tmp_path, built_repository)
    secret_fd_file = tmp_path / "inheritable-secret-fd"
    secret_fd_file.write_text("must-not-survive\n", encoding="utf-8")

    status, raw, injected_descriptor, injected_keyring_id = _launch_protocol(
        root / INSTALLED_ARTIFACT,
        _valid_request(),
        injected_secret=True,
        injected_fd=secret_fd_file,
        injected_keyring=True,
        prove_gate=True,
    )
    assert os.waitstatus_to_exitcode(status) == 0
    assert injected_descriptor is not None
    assert injected_keyring_id is not None
    response = _protocol_response(raw)
    assert response["refusal"] is None
    probes = response["probes"]
    assert probes["injected_secret_env_absent"] is True
    assert probes["injected_unexpected_fd_absent"] is True
    assert probes["inherited_session_keyring_invalidated"] is True
    closed = set(probes["closed_unexpected_fds"])
    assert injected_descriptor in closed
    assert closed <= {0, 1, 2, injected_descriptor}
    assert probes["session_keyring_before"] == injected_keyring_id
    assert isinstance(probes["session_keyring_after"], int)
    assert probes["session_keyring_after"] > 0
    assert probes["session_keyring_after"] != injected_keyring_id

    allowed_status, allowed_raw, _, _ = _launch_protocol(
        root / INSTALLED_ARTIFACT,
        _valid_request(INJECTED_SECRET_NAME),
        injected_secret=True,
        prove_gate=True,
        secret_expected_at_gate=True,
    )
    assert os.waitstatus_to_exitcode(allowed_status) == 0
    allowed_response = _protocol_response(allowed_raw)
    assert allowed_response["refusal"] is None
    assert allowed_response["probes"]["injected_secret_env_absent"] is False


@pytest.mark.parametrize(
    "wire_request",
    [
        pytest.param(b"{", id="malformed-json"),
        pytest.param(
            _canonical_bytes(
                {
                    "protocol": PROTOCOL,
                    "action": "qualify-probe",
                    "env_allowlist": ["LC_ALL", "TZ"],
                    "extra": True,
                }
            ),
            id="extra-field",
        ),
    ],
)
def test_gate8_malformed_or_extra_field_protocol_refuses_without_partial_output(
    tmp_path: Path,
    built_repository: Path,
    wire_request: bytes,
) -> None:
    root = _installed_case(tmp_path, built_repository)

    status, raw, _injected_descriptor, _injected_keyring_id = _launch_protocol(
        root / INSTALLED_ARTIFACT, wire_request
    )
    # A structured protocol refusal exits 1. Pinning it separates the deliberate
    # response below from a signal death such as SIGSEGV (-11).
    _assert_protocol_refusal_exit(status)
    assert len(raw) <= RESPONSE_LIMIT
    response = _protocol_response(raw)
    assert response["refusal"] == PROTOCOL_REFUSED
    assert response["probes"] == {}


@pytest.mark.parametrize(
    "wire_request",
    [
        pytest.param(
            _canonical_bytes(
                {
                    "protocol": PROTOCOL,
                    "action": "execute",
                    "env_allowlist": ["LC_ALL", "TZ"],
                }
            ),
            id="different-action",
        ),
        pytest.param(
            _canonical_bytes(
                {
                    "protocol": PROTOCOL,
                    "action": "qualify-probe",
                    "env_allowlist": ["LC_ALL", "TZ"],
                    "command": ["/bin/true"],
                }
            ),
            id="command-payload",
        ),
    ],
)
def test_control7_launcher_refuses_an_arbitrary_action_or_command(
    tmp_path: Path,
    built_repository: Path,
    wire_request: bytes,
) -> None:
    root = _installed_case(tmp_path, built_repository)
    status, raw, _, _ = _launch_protocol(root / INSTALLED_ARTIFACT, wire_request)
    _assert_protocol_refusal_exit(status)
    response = _protocol_response(raw)
    assert response["refusal"] == PROTOCOL_REFUSED
    assert response["probes"] == {}


def test_control7_hostile_extra_argv_is_refused_and_never_executed(
    tmp_path: Path,
    built_repository: Path,
) -> None:
    root = _installed_case(tmp_path, built_repository)
    marker = tmp_path / "hostile-argv-executed"
    hostile = tmp_path / "hostile-extra-argv"
    hostile.write_text(f"#!/bin/sh\nprintf x > {marker}\n", encoding="utf-8")
    hostile.chmod(0o755)

    status, raw, _, _ = _launch_protocol(
        root / INSTALLED_ARTIFACT,
        _valid_request(),
        argv=[str(root / INSTALLED_ARTIFACT), str(hostile)],
    )
    _assert_protocol_refusal_exit(status)
    response = _protocol_response(raw)
    assert response["refusal"] == PROTOCOL_REFUSED
    assert response["probes"] == {}
    assert not marker.exists()


def _adversarial_responder_source(response: bytes) -> str:
    if len(response) > RESPONSE_LIMIT:
        declaration = f"static unsigned char response[{len(response)}];"
        preparation = "memset(response, 'x', sizeof(response));"
    else:
        values = ",".join(str(value) for value in response)
        declaration = f"static const unsigned char response[] = {{{values}}};"
        preparation = ""
    return f"""\
#include <errno.h>
#include <string.h>
#include <unistd.h>

{declaration}

static int write_all(int fd, const unsigned char *buffer, size_t length) {{
    while (length != 0) {{
        ssize_t written = write(fd, buffer, length);
        if (written < 0 && errno == EINTR) continue;
        if (written <= 0) return 111;
        buffer += written;
        length -= (size_t)written;
    }}
    return 0;
}}

int main(void) {{
    char gate;
    {preparation}
    if (read(3, &gate, 1) != 1) return 112;
    return write_all(5, response, sizeof(response));
}}
"""


def _compile_adversarial_responder(root: Path, output: Path, response: bytes) -> None:
    source = root / "native/ranex-worker-launcher/adversarial-responder.c"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(_adversarial_responder_source(response), encoding="utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "TZ": "UTC",
        "SOURCE_DATE_EPOCH": "0",
    }
    result = subprocess.run(
        [
            "/usr/bin/x86_64-linux-gnu-gcc-13",
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
            f"-ffile-prefix-map={root.resolve()}=.",
            f"-fmacro-prefix-map={root.resolve()}=.",
            "-o",
            str(output),
            str(source),
        ],
        cwd=root,
        env=environment,
        capture_output=True,
        check=False,
    )
    _assert_success(result)
    output.chmod(0o555)


def _bind_adversarial_manifest_and_profile(
    root: Path,
    artifact: Path,
) -> tuple[Path, Path]:
    manifest = _read_json(root / MANIFEST)
    artifact_digest = _sha256_file(artifact)
    _manifest_artifact(manifest)["sha256"] = artifact_digest
    manifest_path = Path("governance/confinement/test-oversized-manifest.json")
    _write_canonical(root / manifest_path, manifest)

    profile = _read_json(root / PROFILE)
    profile["build_manifest_sha256"] = _sha256_file(root / manifest_path)
    profile["artifact_sha256"] = artifact_digest
    profile_path = Path("governance/confinement/test-oversized-profile.json")
    _write_canonical(root / profile_path, profile)
    return manifest_path, profile_path


@pytest.mark.parametrize(
    "wire_response",
    [
        pytest.param(b"{", id="malformed-response"),
        pytest.param(
            _canonical_bytes(
                {
                    "protocol": PROTOCOL,
                    "probes": {},
                    "refusal": None,
                    "extra": True,
                }
            ),
            id="extra-response-field",
        ),
        pytest.param(b"x" * (RESPONSE_LIMIT + 1), id="oversized-response"),
    ],
)
def test_gate8_controller_refuses_invalid_launcher_output_without_report(
    tmp_path: Path,
    built_repository: Path,
    wire_response: bytes,
) -> None:
    if _confined_no_delegation():
        completed = _run_controller(REPOSITORY, "qualify", *_qualify_arguments())
        _refusal(completed, EXEC_OBJECT_DRIFT)
        return
    root = _case_from_built(tmp_path, built_repository)
    artifact = root / INSTALLED_ARTIFACT
    _compile_adversarial_responder(root, artifact, wire_response)
    manifest, profile = _bind_adversarial_manifest_and_profile(root, artifact)
    report = root / QUALIFICATION_REPORT

    result = _qualify(root, artifact=INSTALLED_ARTIFACT, manifest=manifest, profile=profile)
    _assert_refusal(result, PROTOCOL_REFUSED)
    _assert_no_partial(report)


def test_gate10_production_entrypoint_adr_and_risk_remain_frozen() -> None:
    main = REPOSITORY / "src/ranex/cli/main.py"
    assert _sha256_file(main) == MAIN_PY_SHA256

    adr = (
        REPOSITORY / "docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md"
    ).read_text(encoding="utf-8")
    assert [line for line in adr.splitlines() if line.startswith("**Status:**")] == [
        "**Status:** accepted"
    ]

    risk_map = (REPOSITORY / "docs/MAP.md").read_text(encoding="utf-8")
    assert "| `RISK-06` |" in risk_map
    assert (REPOSITORY / SOURCE).is_file(), "SLICE-017 launcher source is not implemented"


def test_gate9_slice017_files_have_no_test_bypass_and_keep_the_frozen_count() -> None:
    files = {
        "tests/integration/test_slice017_native_launcher.py": 26,
        "tests/security/test_slice017_host_qualification.py": 21,
    }
    forbidden = (
        "unittest." + "mock",
        "Magic" + "Mock",
        "monkey" + "patch",
        "pytest." + "skip",
        "skip" + "if",
        "x" + "fail",
    )
    for relative in files:
        source = (REPOSITORY / relative).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{relative} contains forbidden test bypass {token!r}"

    environment = _controller_environment()
    environment.pop("PYTEST_ADDOPTS", None)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            *files,
            "--collect-only",
        ],
        cwd=REPOSITORY,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    collected = {
        relative: sum(
            line.startswith(f"{relative}::") for line in completed.stdout.splitlines()
        )
        for relative in files
    }
    assert collected == files
    assert (REPOSITORY / SOURCE).is_file(), "SLICE-017 launcher source is not implemented"
