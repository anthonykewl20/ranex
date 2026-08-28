"""Frozen RED real CLI journey for SLICE-036.

This test never imports the batch application.  Every product observation
crosses ``python -m ranex.cli.main task batch qualify`` in a subprocess, and
all safety claims are re-read through Git, stdlib sqlite3, the filesystem,
hashlib, os.kill, or a real host-loopback listener.

The fixed successor commit/subject pair is this E2E fixture's exact approved
subject.  The successor is reconstructed from the public parent with fixed
metadata, the owner's committed public key, and every signed child input.  It
does not restrict a production command to the Ranex repository or this commit.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import sqlite3
import struct
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import _prereqs
import pytest

from ranex.foundation.canonical import (
    canonical_json_bytes,
    canonical_sha256,
    command_digest,
)
from ranex.governed_execution.domain.admission import admit
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    load_keyring_text,
)

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests/contract/fixtures/specification"
EXPECTED = ROOT / "tests/e2e/expected"
VECTORS = json.loads(
    (FIXTURES / "approved-batch-v1-vectors.json").read_text(encoding="utf-8")
)
DESCRIPTOR = json.loads(
    (FIXTURES / "approved-batch-v1.json").read_text(encoding="utf-8")
)
EXPECTED_VALUES = json.loads(
    (FIXTURES / "approved-batch-expected-values-v1.json").read_text(encoding="utf-8")
)
FIXTURE_PARENT_COMMIT = "6d8e690f959305922c3a65d93216c46143a3232d"
BASE_COMMIT = "59924e2689e8025bafeed998bd7725fe50bb9a95"
SUBJECT_DIGEST = "sha256:7340607090dddf9cf1faf96a110d20da41157532396cc324661fe829eea3921d"
OWNER_PUBLIC_KEY = "ed25519:A6EHv/POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg="
FIXTURE_AUTHOR_NAME = "Ranex Fixture"
FIXTURE_AUTHOR_EMAIL = "fixture@ranex.invalid"
FIXTURE_COMMIT_DATE = "2000-01-01T00:00:00 +0000"
FIXTURE_COMMIT_MESSAGE = "test(SLICE-036): materialize governed static-worker fixture"
ROW_FIXTURES = (
    "approved-batch-child-requests-v1.jsonl",
    "approved-batch-network-escape-v1.jsonl",
    "approved-batch-child-survivor-v1.jsonl",
    "approved-batch-oracle-mismatch-v1.jsonl",
    "approved-batch-scope-overlap-v1.jsonl",
    "approved-batch-unapproved-row-v1.jsonl",
    "approved-batch-input-mismatch-v1.jsonl",
)
LAUNCHER_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
LAUNCHER_SOURCE = "native/ranex-worker-launcher/launcher.c"
LAUNCHER_BUILD = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
QUALIFICATION_REPORT = ".local/ranex/qualification/strict-local-v1.json"
HOST_PROVISIONING_COMMANDS = (
    (
        "launcher-build",
        "--manifest",
        LAUNCHER_MANIFEST,
        "--source",
        LAUNCHER_SOURCE,
        "--output",
        LAUNCHER_BUILD,
    ),
    (
        "launcher-install",
        "--manifest",
        LAUNCHER_MANIFEST,
        "--artifact",
        LAUNCHER_BUILD,
        "--destination",
        INSTALLED_LAUNCHER,
    ),
    (
        "qualify",
        "--profile",
        HOST_PROFILE,
        "--artifact",
        INSTALLED_LAUNCHER,
        "--manifest",
        LAUNCHER_MANIFEST,
        "--report",
        QUALIFICATION_REPORT,
    ),
)
OBSERVER_TRACE_SYSCALLS = (
    "trace=execve,clone,clone3,vfork,fork,chdir,fchdir"
)
PORTS = range(46120, 46136)
SURVIVOR_COMM = b"ranex-slice036\n"
PRIMARY_ROWS = tuple(
    json.loads(line)
    for line in (FIXTURES / "approved-batch-child-requests-v1.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
)
CHILD_RUN_ARGV_BY_KEY = {
    (row["runtime_input"]["flow_id"], row["task_id"], row["attempt"]): tuple(
        row["invocation"]["argv"]
    )
    for row in PRIMARY_ROWS
}


@dataclass(frozen=True)
class DevelopmentSource:
    controller_python: Path
    manifest_digest: str
    module_path: Path
    pythonpath: Path


@dataclass(frozen=True)
class GovernedProvisioning:
    artifact_digest: str
    build_manifest_digest: str
    host_state_digest: str
    profile_digest: str
    report_digest: str
    schema: str


@dataclass(frozen=True)
class TracedProcess:
    completed: subprocess.CompletedProcess[str]
    controller_argv: tuple[str, ...]
    controller_python: Path
    trace_path: Path


def run(
    *argv: str,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


def git(repository: Path, *argv: str) -> str:
    completed = run("git", "-C", str(repository), *argv)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def git_blob(repository: Path, commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repository), "show", f"{commit}:{relative}"],
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    return completed.stdout


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def historical_build_input_drift(governed: Path) -> bool:
    """Whether the immutable fixture's absolute build inputs differ here."""

    manifest = json.loads((governed / LAUNCHER_MANIFEST).read_bytes())
    for row in manifest["build"]["inputs"]:
        path = Path(row["path"])
        if path.is_absolute() and (
            not path.is_file()
            or file_digest(path) != "sha256:" + row["sha256"]
        ):
            return True
    return False


def pinned_strace() -> Path:
    """Admit the literal observer only through the B-protected tool manifest."""

    expected_values_path = VECTORS["paths"]["expected_values"]
    protected = {
        row["path"]: row["digest"]
        for row in VECTORS["triple"]["b"]["artifacts"]["protected"]
    }
    assert protected[expected_values_path] == file_digest(ROOT / expected_values_path)
    manifest = EXPECTED_VALUES["child_provisioning"]["observer_tool"]
    assert manifest == {
        "path": "/usr/bin/strace",
        "sha256": "sha256:28f957c227012de0b18d1bd7fff2d396cb693ea60ed8013be68de071e84b5001",
        "version": "strace -- version 6.8",
    }
    observer = Path(manifest["path"])
    assert observer == Path("/usr/bin/strace")
    assert observer.is_file() and not observer.is_symlink()
    assert file_digest(observer) == manifest["sha256"]
    version = run(str(observer), "--version", env={"LC_ALL": "C", "TZ": "UTC"})
    assert version.returncode == 0, version.stderr
    assert version.stdout.splitlines()[0] == manifest["version"]
    return observer


def journal_snapshot(path: Path) -> tuple[int, str | None]:
    if not path.exists():
        return 0, None
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS count, "
            "(SELECT link FROM evaluations ORDER BY seq DESC LIMIT 1) AS head "
            "FROM evaluations"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return int(row[0]), row[1]


def worktree_snapshot(target: Path) -> tuple[str, ...]:
    completed = run("git", "-C", str(target), "worktree", "list", "--porcelain")
    assert completed.returncode == 0, completed.stderr
    return tuple(
        line.removeprefix("worktree ")
        for line in completed.stdout.splitlines()
        if line.startswith("worktree ")
    )


def filesystem_snapshot(root: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, "symlink:" + os.readlink(path)))
        elif path.is_file():
            rows.append((relative, file_digest(path)))
        elif path.is_dir():
            rows.append((relative, "directory"))
    return tuple(rows)


def source_manifest(root: Path) -> dict[str, object]:
    files = []
    source = root / "src/ranex"
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "digest": file_digest(path),
            }
        )
    return {"files": files}


def source_manifest_digest(root: Path) -> str:
    """Hash the manifest with stdlib JSON, independently of the product CLI."""

    payload = json.dumps(
        source_manifest(root),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def survivor_pids() -> set[int]:
    """Observe the planted process independently of qualifier output."""

    observed: set[int] = set()
    for candidate in Path("/proc").iterdir():
        if not candidate.name.isdigit():
            continue
        try:
            command_name = (candidate / "comm").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if command_name == SURVIVOR_COMM:
            observed.add(int(candidate.name))
    return observed


@dataclass
class LoopbackSentinel:
    listener: socket.socket
    port: int
    accepted: list[tuple[str, int]] = field(default_factory=list)
    stopped: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None

    @classmethod
    def start(cls) -> LoopbackSentinel:
        for port in PORTS:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(("127.0.0.1", port))
            except OSError:
                listener.close()
                continue
            listener.listen()
            listener.settimeout(0.05)
            sentinel = cls(listener, port)

            def accept(
                active: LoopbackSentinel = sentinel,
                server: socket.socket = listener,
            ) -> None:
                while not active.stopped.is_set():
                    try:
                        connection, address = server.accept()
                    except TimeoutError:
                        continue
                    except OSError:
                        break
                    with connection:
                        active.accepted.append(address)

            sentinel.thread = threading.Thread(target=accept, daemon=True)
            sentinel.thread.start()
            return sentinel
        raise AssertionError("no loopback sentinel port is available")

    def calibrate(self) -> None:
        with socket.create_connection(("127.0.0.1", self.port), timeout=1):
            pass
        for _ in range(100):
            if self.accepted:
                return
            threading.Event().wait(0.01)
        raise AssertionError("the real loopback listener did not observe calibration")

    def close(self) -> None:
        self.stopped.set()
        self.listener.close()
        if self.thread is not None:
            self.thread.join(timeout=1)


@pytest.fixture()
def loopback_sentinel() -> LoopbackSentinel:
    sentinel = LoopbackSentinel.start()
    try:
        sentinel.calibrate()
    except OSError as exc:
        sentinel.close()
        pytest.skip(
            "ranex-context: host loopback is unavailable inside the governed "
            f"network namespace ({exc})"
        )
    yield sentinel
    sentinel.close()


def fixture_input_records() -> dict[str, dict[str, object]]:
    """Derive the exact committed child inputs from every B-bound signed row."""

    records: dict[str, dict[str, object]] = {}
    for name in ROW_FIXTURES:
        for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            task_id = row["task_id"]
            flow_id = row["runtime_input"]["flow_id"]
            expected_path = (
                f"governance/qualification/inputs/{task_id}/{flow_id}/"
                f"attempt-{row['attempt']}"
            )
            actual_path = row["invocation"]["runtime_input_path"]
            if actual_path != expected_path:
                assert name == "approved-batch-input-mismatch-v1.jsonl"
            relative = expected_path + "/task.json"
            record = {
                "attempt": row["attempt"],
                "delay_ms": row["runtime_input"]["delay_ms"],
                "flow_id": flow_id,
                "mode": row["runtime_input"]["mode"],
                "task_id": task_id,
                "version": "slice036-child-input-v2",
            }
            existing = records.get(relative)
            assert existing is None or existing == record
            records[relative] = record
    assert len(records) == 25
    return records


def _assert_closed_static_elf(image: bytes) -> None:
    """Inspect ELF64 bytes using the exact installed ``/usr/include/elf.h`` ABI."""

    elf_h = Path("/usr/include/elf.h").read_text(encoding="utf-8")
    for spelling in (
        "#define ET_EXEC\t\t2",
        "#define EM_X86_64\t62",
        "#define PT_INTERP\t3",
        "#define PT_NOTE\t\t4",
        "#define PT_GNU_STACK\t0x6474e551",
        "#define PT_GNU_RELRO\t0x6474e552",
        "#define PF_X\t\t(1 << 0)",
        "#define NT_GNU_BUILD_ID\t3",
    ):
        assert spelling in elf_h

    elf64_header = struct.Struct("<16sHHIQQQIHHHHHH")
    elf64_program_header = struct.Struct("<IIQQQQQQ")
    assert len(image) >= elf64_header.size
    header = elf64_header.unpack_from(image)
    ident = header[0]
    assert ident[:7] == b"\x7fELF\x02\x01\x01"
    assert header[1] == 2  # ET_EXEC
    assert header[2] == 62  # EM_X86_64
    assert header[8] == elf64_header.size
    program_offset, program_entry_size, program_count = header[5], header[9], header[10]
    assert program_entry_size == elf64_program_header.size
    assert program_offset + program_entry_size * program_count <= len(image)
    programs = [
        elf64_program_header.unpack_from(image, program_offset + index * program_entry_size)
        for index in range(program_count)
    ]
    assert all(program[0] != 3 for program in programs)  # no PT_INTERP
    stacks = [program for program in programs if program[0] == 0x6474E551]
    assert len(stacks) == 1
    assert stacks[0][1] & 1 == 0  # PT_GNU_STACK lacks PF_X
    assert any(program[0] == 0x6474E552 for program in programs)  # PT_GNU_RELRO

    for program in programs:
        if program[0] != 4:  # PT_NOTE
            continue
        offset, size = program[2], program[5]
        assert offset + size <= len(image)
        cursor, end = offset, offset + size
        while cursor < end:
            assert cursor + 12 <= end
            name_size, description_size, note_type = struct.unpack_from(
                "<III", image, cursor
            )
            cursor += 12
            name_end = cursor + name_size
            assert name_end <= end
            name = image[cursor:name_end]
            cursor = (name_end + 3) & ~3
            description_end = cursor + description_size
            assert description_end <= end
            cursor = (description_end + 3) & ~3
            assert not (name == b"GNU\x00" and note_type == 3)  # NT_GNU_BUILD_ID


def test_static_worker_twice_built_bytes_have_required_elf_properties(
    tmp_path: Path,
) -> None:
    """Claims in the manifest do not substitute for inspecting both artifacts."""

    manifest_path = ROOT / "tests/e2e/fixtures/slice036-worker-build-v1.json"
    source = ROOT / "tests/e2e/fixtures/slice036-worker.c"
    manifest = json.loads(manifest_path.read_bytes())
    artifacts: list[bytes] = []
    for index in range(2):
        output = tmp_path / f"slice036-worker-{index}"
        flags = [
            token.replace("<ABS_REPO_ROOT>", str(ROOT.resolve()))
            .replace("<output>", str(output))
            .replace("<source>", str(source))
            for token in manifest["build"]["flags"]
        ]
        built = run(
            manifest["build"]["compiler"]["path"],
            *flags,
            cwd=ROOT,
            env=manifest["build"]["environment"],
        )
        assert built.returncode == 0, built.stderr
        image = output.read_bytes()
        assert hashlib.sha256(image).hexdigest() == manifest["artifact"]["sha256"]
        _assert_closed_static_elf(image)
        artifacts.append(image)
    assert artifacts[0] == artifacts[1]


def materialize_governed_checkout(path: Path) -> Path:
    """Construct the one deterministic governed fixture repository."""

    completed = run("git", "clone", "--quiet", str(ROOT), str(path))
    assert completed.returncode == 0, completed.stderr
    git(path, "checkout", "--quiet", "-B", "main", FIXTURE_PARENT_COMMIT)
    keyring_path = path / "governance/producers.yaml"
    keyring_text = keyring_path.read_text(encoding="utf-8")
    assert "  owner:" not in keyring_text
    keyring_path.write_text(
        keyring_text.replace(
            "producers:\n",
            f"producers:\n  owner: {OWNER_PUBLIC_KEY}\n",
            1,
        ),
        encoding="utf-8",
    )
    input_records = fixture_input_records()
    for relative, record in sorted(input_records.items()):
        destination = path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(canonical_json_bytes(record))
    worker_root = path / "governance/qualification/worker"
    worker_root.mkdir(parents=True)
    worker_source = ROOT / "tests/e2e/fixtures/slice036-worker.c"
    worker_manifest = ROOT / "tests/e2e/fixtures/slice036-worker-build-v1.json"
    shutil.copyfile(worker_source, worker_root / "slice036-worker.c")
    shutil.copyfile(worker_manifest, worker_root / "slice036-worker-build-v1.json")
    manifest = json.loads(worker_manifest.read_bytes())
    flags = [
        token.replace("<ABS_REPO_ROOT>", str(path.resolve()))
        .replace("<output>", str(worker_root / "slice036-worker"))
        .replace("<source>", str(worker_root / "slice036-worker.c"))
        for token in manifest["build"]["flags"]
    ]
    built = run(
        manifest["build"]["compiler"]["path"],
        *flags,
        cwd=path,
        env=manifest["build"]["environment"],
    )
    assert built.returncode == 0, built.stderr
    worker_binary = worker_root / "slice036-worker"
    assert file_digest(worker_binary) == "sha256:" + manifest["artifact"]["sha256"]
    worker_binary.chmod(0o555)
    git(path, "add", "governance/producers.yaml", "governance/qualification")
    commit_environment = dict(os.environ)
    commit_environment.update(
        {
            "GIT_AUTHOR_NAME": FIXTURE_AUTHOR_NAME,
            "GIT_AUTHOR_EMAIL": FIXTURE_AUTHOR_EMAIL,
            "GIT_AUTHOR_DATE": FIXTURE_COMMIT_DATE,
            "GIT_COMMITTER_NAME": FIXTURE_AUTHOR_NAME,
            "GIT_COMMITTER_EMAIL": FIXTURE_AUTHOR_EMAIL,
            "GIT_COMMITTER_DATE": FIXTURE_COMMIT_DATE,
        }
    )
    committed = run(
        "git",
        "-C",
        str(path),
        "-c",
        "commit.gpgSign=false",
        "commit",
        "--quiet",
        "-m",
        FIXTURE_COMMIT_MESSAGE,
        env=commit_environment,
    )
    assert committed.returncode == 0, committed.stderr
    assert git(path, "rev-parse", "HEAD") == BASE_COMMIT
    assert git(path, "rev-parse", "refs/heads/main") == BASE_COMMIT
    assert git(path, "rev-parse", f"{BASE_COMMIT}^") == FIXTURE_PARENT_COMMIT
    tree = git(path, "rev-parse", f"{BASE_COMMIT}^{{tree}}")
    assert "sha256:" + canonical_sha256({"tree": tree}) == SUBJECT_DIGEST
    assert git(path, "show", "-s", "--format=%an", BASE_COMMIT) == FIXTURE_AUTHOR_NAME
    assert git(path, "show", "-s", "--format=%ae", BASE_COMMIT) == FIXTURE_AUTHOR_EMAIL
    assert git(path, "show", "-s", "--format=%aI", BASE_COMMIT) == (
        "2000-01-01T00:00:00+00:00"
    )
    assert git(path, "show", "-s", "--format=%s", BASE_COMMIT) == (
        FIXTURE_COMMIT_MESSAGE
    )
    changed = set(
        git(path, "diff-tree", "--no-commit-id", "--name-only", "-r", BASE_COMMIT)
        .splitlines()
    )
    assert changed == {
        "governance/producers.yaml",
        *input_records,
        "governance/qualification/worker/slice036-worker",
        "governance/qualification/worker/slice036-worker-build-v1.json",
        "governance/qualification/worker/slice036-worker.c",
    }
    published_authority = EXPECTED_VALUES["published_v2_authority"]
    assert published_authority["commit"] == FIXTURE_PARENT_COMMIT
    authority_paths = {
        "launcher_manifest": LAUNCHER_MANIFEST,
        "launcher_source": LAUNCHER_SOURCE,
        "profile": HOST_PROFILE,
    }
    for name, relative in authority_paths.items():
        expected = published_authority[name]
        assert expected["path"] == relative
        parent_bytes = git_blob(path, FIXTURE_PARENT_COMMIT, relative)
        assert git_blob(path, BASE_COMMIT, relative) == parent_bytes
        assert (path / relative).read_bytes() == parent_bytes
        assert "sha256:" + hashlib.sha256(parent_bytes).hexdigest() == expected[
            "digest"
        ]
    committed_keyring = git_blob(path, BASE_COMMIT, "governance/producers.yaml")
    keyring = load_keyring_text(committed_keyring.decode("utf-8"), BASE_COMMIT)
    assert keyring["owner"] == OWNER_PUBLIC_KEY
    assert "anthony" in keyring
    role = next(role for role in DESCRIPTOR["roles"] if role["principal"] == "owner")
    assert role["key"] == keyring["owner"]
    for relative, record in sorted(input_records.items()):
        assert git(path, "ls-files", "--error-unmatch", relative) == relative
        assert git_blob(path, BASE_COMMIT, relative) == canonical_json_bytes(record)
    assert git(path, "status", "--porcelain") == ""
    assert path.resolve() != ROOT.resolve()
    return path


def materialize_signing_key(path: Path) -> Path:
    """Write the deterministic non-secret fixture key outside every repository."""

    private = "ed25519:" + base64.b64encode(bytes(range(32))).decode("ascii")
    path.write_text(private, encoding="utf-8")
    path.chmod(0o600)
    return path


def materialize_authority(path: Path) -> tuple[Path, Path, Path]:
    path.mkdir(parents=True)
    triple = VECTORS["triple"]
    a = path / "spec-packet.json"
    b = path / "artifact-manifest.json"
    c = path / "approval-envelope.json"
    a.write_bytes(canonical_json_bytes(triple["a"]))
    b.write_bytes(canonical_json_bytes(triple["b"]))
    c.write_bytes(
        canonical_json_bytes(
            {
                "version": "approval-envelope-v1",
                "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
                "payload": triple["c_payload"],
                "key_id": triple["key_id"],
                "signature": triple["signature"],
            }
        )
    )
    return a, b, c


def cli_environment(
    *,
    development_source: Path = ROOT / "src",
    signing_key: Path | None = None,
) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    source = development_source.resolve()
    assert source.is_absolute() and source == (ROOT / "src").resolve()
    environment["PYTHONPATH"] = str(source)
    if signing_key is not None:
        environment["RANEX_SIGNING_KEY"] = str(signing_key.resolve())
    return environment


def observe_development_source(governed: Path) -> tuple[DevelopmentSource, str]:
    """Resolve the exact imported CLI module and hash every executed source byte."""

    pythonpath = (ROOT / "src").resolve()
    expected_module = (pythonpath / "ranex/cli/main.py").resolve()
    completed = run(
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-c",
        "import json, sys; from pathlib import Path; import ranex.cli.main; "
        "print(json.dumps({'controller_python': str(Path(sys.executable).resolve()), "
        "'module_path': str(Path(ranex.cli.main.__file__).resolve())}, "
        "sort_keys=True, separators=(',', ':')))",
        cwd=governed,
        env=cli_environment(development_source=pythonpath),
    )
    assert completed.returncode == 0, completed.stderr
    observed = json.loads(completed.stdout)
    assert set(observed) == {"controller_python", "module_path"}
    controller_python = Path(observed["controller_python"])
    observed_module = Path(observed["module_path"])
    assert controller_python.is_absolute() and controller_python.is_file()
    assert controller_python.resolve() == controller_python
    assert controller_python != Path(shutil.which("uv") or "uv").resolve()
    assert observed_module == expected_module
    source = DevelopmentSource(
        controller_python=controller_python,
        manifest_digest=source_manifest_digest(ROOT),
        module_path=observed_module,
        pythonpath=pythonpath,
    )
    record = {
        "controller_python": str(source.controller_python),
        "event": "development.source",
        "manifest_digest": source.manifest_digest,
        "module_path": str(source.module_path),
        "pythonpath": str(source.pythonpath),
        "version": "slice036-development-source-v1",
    }
    return source, canonical_json_bytes(record).decode("utf-8") + "\n"


def provision_strict_local(governed: Path) -> tuple[GovernedProvisioning, str]:
    """Run the repository's public host controller, then verify its result."""

    controller = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.host_confinement",
    ]
    for arguments in HOST_PROVISIONING_COMMANDS:
        completed = run(
            *controller,
            *arguments,
            cwd=governed,
            env=cli_environment(),
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr

    return verify_strict_local(governed)


def provision_dependency_admission(governed: Path) -> None:
    """Use the existing public dependency gate before exercising real ``run``."""

    controller = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
    ]
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    environment["PYTHONPATH"] = str((governed / "src").resolve())
    journal = governed / "governance/journal.sqlite3"
    assert journal_snapshot(journal) == (0, None)
    fetched = run(
        *controller,
        "deps",
        "fetch",
        "--repository",
        ".",
        cwd=governed,
        env=environment,
    )
    assert fetched.returncode == 0, fetched.stdout + fetched.stderr
    assert "FETCHED" in fetched.stdout
    approved = run(
        *controller,
        "deps",
        "approve",
        "--repository",
        ".",
        "--approver",
        "slice036-observer-calibration",
        cwd=governed,
        env=environment,
    )
    assert approved.returncode == 0, approved.stdout + approved.stderr
    assert "APPROVED" in approved.stdout
    verified = run(
        *controller,
        "journal",
        "verify",
        "--repository",
        ".",
        cwd=governed,
        env=environment,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "chain=verified" in verified.stdout


def verify_strict_local(governed: Path) -> tuple[GovernedProvisioning, str]:
    """Independently verify one child's final strict-local state."""

    manifest_path = governed / LAUNCHER_MANIFEST
    profile_path = governed / HOST_PROFILE
    built_path = governed / LAUNCHER_BUILD
    installed_path = governed / INSTALLED_LAUNCHER
    report_path = governed / QUALIFICATION_REPORT
    manifest = json.loads(manifest_path.read_bytes())
    assert built_path.read_bytes() == installed_path.read_bytes()
    artifact_digest = file_digest(installed_path)
    assert artifact_digest == "sha256:" + manifest["artifact"]["sha256"]
    raw_report = report_path.read_bytes()
    report = json.loads(raw_report)
    assert raw_report == canonical_json_bytes(report)
    assert report["schema"] == "ranex-strict-local-qualification-v1"
    assert report["qualified"] is True and report["refusal"] is None
    assert report["kernel"] == {
        "architecture": os.uname().machine,
        "release": os.uname().release,
    }
    assert report["digests"] == {
        "artifact": artifact_digest.removeprefix("sha256:"),
        "build_manifest": file_digest(manifest_path).removeprefix("sha256:"),
        "profile": file_digest(profile_path).removeprefix("sha256:"),
    }
    host_state = report["host_state"]
    assert host_state["boot_id"] == Path(
        "/proc/sys/kernel/random/boot_id"
    ).read_text(encoding="utf-8").strip()
    assert host_state["machine_id"] == Path("/etc/machine-id").read_text(
        encoding="utf-8"
    ).strip()
    assert host_state["delegation_identity"]["uid"] == os.geteuid()
    assert host_state["delegation_identity"]["gid"] == os.getegid()
    provisioning = GovernedProvisioning(
        artifact_digest=artifact_digest,
        build_manifest_digest=file_digest(manifest_path),
        host_state_digest="sha256:" + canonical_sha256(host_state),
        profile_digest=file_digest(profile_path),
        report_digest=file_digest(report_path),
        schema=report["schema"],
    )
    assert git(governed, "status", "--porcelain") == ""
    transcript = canonical_json_bytes(
        {
            "artifact_digest": provisioning.artifact_digest,
            "build_manifest_digest": provisioning.build_manifest_digest,
            "event": "governed.strict-local.provisioned",
            "host_state_digest": provisioning.host_state_digest,
            "profile_digest": provisioning.profile_digest,
            "report_digest": provisioning.report_digest,
            "schema": provisioning.schema,
        }
    ).decode("utf-8") + "\n"
    return provisioning, transcript


def qualify_command(
    *,
    authority: tuple[Path, Path, Path],
    target: Path,
    journal: Path,
    outcome: Path,
    pool: int = 2,
    descriptor: Path = FIXTURES / "approved-batch-v1.json",
    tasks: Path = FIXTURES / "approved-batch-child-requests-v1.jsonl",
) -> list[str]:
    a, b, c = authority
    return [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "batch",
        "qualify",
        "--spec-packet",
        str(a),
        "--artifact-manifest",
        str(b),
        "--approval-envelope",
        str(c),
        "--descriptor",
        str(descriptor),
        "--tasks",
        str(tasks),
        "--target",
        str(target),
        "--journal",
        str(journal),
        "--outcome-dir",
        str(outcome),
        "--pool",
        str(pool),
    ]


def invoke(
    command: list[str],
    *,
    checkout: Path = ROOT,
    signing_key: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        *command,
        cwd=checkout,
        env=cli_environment(signing_key=signing_key),
    )


def trace_direct_controller(
    controller_arguments: list[str],
    *,
    checkout: Path,
    controller_python: Path,
    environment: dict[str, str],
    trace_path: Path,
) -> TracedProcess:
    """Trace one resolved Python controller and detach each child at exec."""

    strace = pinned_strace()
    assert controller_python.is_absolute() and controller_python.is_file()
    assert controller_python.resolve() == controller_python
    assert controller_python != Path(shutil.which("uv") or "uv").resolve()
    assert not trace_path.resolve().is_relative_to(checkout.resolve())
    controller_argv = (str(controller_python), *controller_arguments)
    # Installed strace 6.8 records the launch-time controller exec and remains
    # attached to that root; each later child exec is recorded with
    # ``<detached ...>``.  The six-child calibration below discriminates this
    # behavior: losing the root would make all 24 closed child execs absent.
    completed = run(
        str(strace),
        "-f",
        "--detach-on=execve",
        "-s",
        "8192",
        "-qq",
        "-ttt",
        "-yy",
        "-e",
        OBSERVER_TRACE_SYSCALLS,
        "-o",
        str(trace_path),
        *controller_argv,
        cwd=checkout,
        env=environment,
    )
    assert trace_path.is_file()
    return TracedProcess(
        completed=completed,
        controller_argv=controller_argv,
        controller_python=controller_python,
        trace_path=trace_path,
    )


def invoke_traced(
    command: list[str],
    *,
    checkout: Path,
    controller_python: Path,
    signing_key: Path,
    trace_path: Path,
) -> TracedProcess:
    """Run the real CLI below the direct-controller external observer."""

    uv_executable = Path(shutil.which("uv") or "uv").resolve()
    assert Path(command[0]).resolve() == uv_executable
    assert command[1:4] == ["run", "--frozen", "python"]
    return trace_direct_controller(
        command[4:],
        checkout=checkout,
        controller_python=controller_python,
        environment=cli_environment(signing_key=signing_key),
        trace_path=trace_path,
    )


def observe_child_provisioning(
    traced: TracedProcess,
    *,
    governed: Path,
    provenance_path: Path,
    sibling_modes: dict[str, str] | None = None,
) -> str:
    """Observe exact per-child public commands and ordering, not filesystem history."""

    raw_lines = traced.trace_path.read_text(encoding="utf-8").splitlines()
    unfinished: dict[tuple[str, str], str] = {}
    lines: list[str] = []
    for line in raw_lines:
        opened = re.match(
            r"^(?P<pid>\d+)\s+(?P<time>\d+\.\d+)\s+"
            r"(?P<call>chdir|fchdir)\((?P<body>.*) <unfinished \.\.\.>$",
            line,
        )
        if opened is not None:
            unfinished[(opened["pid"], opened["call"])] = (
                f"{opened['pid']} {opened['time']} {opened['call']}({opened['body']}"
            )
            continue
        resumed = re.match(
            r"^(?P<pid>\d+)\s+\d+\.\d+\s+<\.\.\. "
            r"(?P<call>chdir|fchdir) resumed>(?P<tail>.*)$",
            line,
        )
        if resumed is not None:
            prefix = unfinished.pop((resumed["pid"], resumed["call"]), None)
            if prefix is not None:
                lines.append(prefix + resumed["tail"])
                continue
        lines.append(line)
    process_parent: dict[int, int] = {}
    process_cwd: dict[int, Path] = {}
    executions: list[tuple[int, float, Path, list[str]]] = []
    root_pid: int | None = None

    def lexical_absolute(path: Path, *, base: Path | None = None) -> Path:
        if not path.is_absolute():
            assert base is not None
            path = base / path
        return Path(os.path.abspath(os.fspath(path)))

    for line in lines:
        process = re.match(
            r"^(?P<pid>\d+)\s+\d+\.\d+\s+"
            r"(?:clone|clone3|vfork|fork)\(.*\)\s+=\s+(?P<child>\d+)$",
            line,
        ) or re.match(
            r"^(?P<pid>\d+)\s+\d+\.\d+\s+<\.\.\. "
            r"(?:clone|clone3|vfork|fork) resumed>.*\)\s+=\s+(?P<child>\d+)$",
            line,
        )
        if process is not None:
            process_parent[int(process["child"])] = int(process["pid"])

    def inherited_cwd(pid: int) -> Path | None:
        seen: set[int] = set()
        while pid not in seen:
            seen.add(pid)
            if pid in process_cwd:
                return process_cwd[pid]
            if pid not in process_parent:
                return None
            pid = process_parent[pid]
        return None

    call_pattern = re.compile(
        r"^(?P<pid>\d+)\s+(?P<time>\d+\.\d+)\s+"
        r"(?P<call>execve|clone|clone3|vfork|fork|chdir|fchdir)\("
    )
    for line in lines:
        match = call_pattern.match(line)
        if match is None:
            continue
        pid = int(match["pid"])
        timestamp = float(match["time"])
        call = match["call"]
        if root_pid is None:
            root_pid = pid
            process_cwd[pid] = lexical_absolute(governed)
        if call in {"clone", "clone3", "vfork", "fork"}:
            continue
        if call == "chdir":
            changed = re.search(r'chdir\(("(?:\\.|[^"\\])*")\)\s+=\s+0$', line)
            assert changed is not None, line
            destination = Path(json.loads(changed.group(1)))
            if not destination.is_absolute():
                current = inherited_cwd(pid)
                assert current is not None
                destination = current / destination
            process_cwd[pid] = lexical_absolute(destination)
            continue
        if call == "fchdir":
            assert not line.endswith("= 0"), (
                "command observer cannot independently resolve a successful fchdir"
            )
            continue
        invoked = re.search(
            r'execve\("(?:\\.|[^"\\])*", (\[.*\]), '
            r'(?:0x[0-9a-f]+|\[).*$',
            line,
        )
        assert invoked is not None, line
        argv = json.loads(invoked.group(1))
        assert isinstance(argv, list) and all(isinstance(arg, str) for arg in argv)
        cwd = inherited_cwd(pid)
        assert cwd is not None, line
        executions.append((pid, timestamp, cwd, argv))

    assert root_pid is not None
    controller_executions = [
        argv for pid, _, _, argv in executions if pid == root_pid
    ]
    assert controller_executions == [list(traced.controller_argv)]
    assert Path(controller_executions[0][0]) == traced.controller_python
    assert Path(controller_executions[0][0]).resolve() != Path(
        shutil.which("uv") or "uv"
    ).resolve()

    def geometry(cwd: Path) -> tuple[str, str, int] | None:
        if cwd.parent.parent.name != "children":
            return None
        if re.fullmatch(r"attempt-[0-6]", cwd.name) is None:
            return None
        return (
            cwd.parent.parent.parent.name,
            cwd.parent.name,
            int(cwd.name.removeprefix("attempt-")),
        )

    expected = {
        (flow_id, task_id, 0)
        for flow_id in ("a-before-b", "b-before-a")
        for task_id in DESCRIPTOR["children"]
    }
    uv_executable = Path(shutil.which("uv") or "uv").resolve()
    host_prefix = ["run", "--frozen", "python", "-m", "ranex.cli.host_confinement"]
    observed: dict[tuple[str, str, int], list[tuple[float, tuple[str, ...]]]] = {}
    child_runs: dict[tuple[str, str, int], float] = {}
    roots: dict[tuple[str, str, int], set[Path]] = {}
    for _, timestamp, cwd, argv in executions:
        current = geometry(cwd)
        if current is None:
            continue
        roots.setdefault(current, set()).add(cwd)
        if argv[1:6] == host_prefix:
            assert Path(argv[0]).resolve() == uv_executable
            arguments = tuple(argv[6:])
            assert arguments in HOST_PROVISIONING_COMMANDS
            observed.setdefault(current, []).append((timestamp, arguments))
        elif current in CHILD_RUN_ARGV_BY_KEY and argv[1:] == [
            "run", "--frozen", *CHILD_RUN_ARGV_BY_KEY[current]
        ]:
            assert Path(argv[0]).resolve() == uv_executable
            assert current not in child_runs
            child_runs[current] = timestamp
        else:
            raise AssertionError(f"unexpected child execution in {cwd}: {argv}")

    assert set(observed) == expected
    assert set(child_runs) == expected
    assert set(roots) == expected
    if sibling_modes is not None:
        assert sibling_modes == {
            "a-before-b": "sequential",
            "b-before-a": "concurrent-provisioning-sequential-sessions",
        }
        first, second, joined = DESCRIPTOR["children"]
        sequential = [
            ("a-before-b", first, 0),
            ("a-before-b", second, 0),
            ("a-before-b", joined, 0),
        ]
        assert child_runs[sequential[0]] < min(
            timestamp for timestamp, _ in observed[sequential[1]]
        )
        assert child_runs[sequential[1]] < min(
            timestamp for timestamp, _ in observed[sequential[2]]
        )
        concurrent = [
            ("b-before-a", first, 0),
            ("b-before-a", second, 0),
        ]
        assert max(
            min(timestamp for timestamp, _ in observed[current])
            for current in concurrent
        ) < min(child_runs[current] for current in concurrent)
        assert child_runs[concurrent[1]] < child_runs[concurrent[0]]
        concurrent_join = ("b-before-a", joined, 0)
        assert child_runs[concurrent[0]] < min(
            timestamp for timestamp, _ in observed[concurrent_join]
        )
    records = []
    observer_root = Path(os.path.abspath(os.fspath(governed.parent)))
    for current in sorted(expected):
        child_roots = roots[current]
        assert len(child_roots) == 1
        child_root = next(iter(child_roots))
        assert child_root.is_relative_to(observer_root)
        steps = sorted(observed[current])
        assert tuple(step[1] for step in steps) == HOST_PROVISIONING_COMMANDS
        assert steps[-1][0] < child_runs[current]
        flow_id, task_id, attempt = current
        records.append(
            {
                "attempt": attempt,
                "commands": [["uv", *host_prefix, *step[1]] for step in steps],
                "flow_id": flow_id,
                "task_id": task_id,
            }
        )

    assert not provenance_path.resolve().is_relative_to(governed.resolve())
    provenance = {
        "controller_argv": list(traced.controller_argv),
        "controller_python": str(traced.controller_python),
        "observer": "strace-execve-chdir-v1",
        "observer_tool": EXPECTED_VALUES["child_provisioning"]["observer_tool"],
        "records": records,
        "sibling_modes": sibling_modes,
        "version": "slice036-child-command-observer-v1",
    }
    provenance_path.write_bytes(canonical_json_bytes(provenance))
    assert json.loads(provenance_path.read_bytes()) == provenance
    event = {
        "controller_python": str(traced.controller_python),
        "event": "child.provisioning.observed",
        "executions_digest": "sha256:" + canonical_sha256(provenance),
        "observer": provenance["observer"],
        "observer_digest": provenance["observer_tool"]["sha256"],
        "observer_version": provenance["observer_tool"]["version"],
        "provenance_path": str(provenance_path.resolve()),
        "run_count": len(child_runs),
        "step_count": sum(len(steps) for steps in observed.values()),
    }
    return canonical_json_bytes(event).decode("utf-8") + "\n"


def calibrate_child_provisioning_release_invariant(
    root: Path,
    *,
    controller_python: Path,
    signing_key: Path,
) -> str:
    """Trace pool-two provisioning and serialized sessions, then verify state."""

    children: dict[tuple[str, str], Path] = {}
    rows = [
        json.loads(line)
        for line in (FIXTURES / "approved-batch-child-requests-v1.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    assert len(rows) == 6
    assert len({tuple(row["invocation"]["argv"]) for row in rows}) == 6
    for row in rows:
        argv = row["invocation"]["argv"]
        assert argv[argv.index("--confinement") + 1] == "strict-local"
        separator = argv.index("--")
        assert argv[separator + 1 :] == [
            "/ranex/toolchain/bin/slice036-worker", "--task"
        ]
    for flow_id in ("a-before-b", "b-before-a"):
        for task_id in DESCRIPTOR["children"]:
            child = materialize_governed_checkout(
                root / flow_id / "children" / task_id / "attempt-0"
            )
            children[(flow_id, task_id)] = child
            assert git(child, "status", "--porcelain") == ""
            assert not (child / LAUNCHER_BUILD).exists()
            assert not (child / INSTALLED_LAUNCHER).exists()
            assert not (child / QUALIFICATION_REPORT).exists()
            # The deterministic successor commits dependency inputs, but a
            # journal is deliberately not part of the commit.  Exercise the
            # existing derivation/approval owner so the exact real child run
            # reaches the canonical strict-local session verifier.
            provision_dependency_admission(child)

    plan = {
        "commands": [list(arguments) for arguments in HOST_PROVISIONING_COMMANDS],
        "concurrent_provisioning": [
            {
                "cwd": str(children[("b-before-a", task_id)]),
                "run": list(CHILD_RUN_ARGV_BY_KEY[("b-before-a", task_id, 0)]),
            }
            for task_id in DESCRIPTOR["children"][:2]
        ],
        "concurrent_session_order": [
            {
                "cwd": str(children[("b-before-a", task_id)]),
                "run": list(CHILD_RUN_ARGV_BY_KEY[("b-before-a", task_id, 0)]),
            }
            for task_id in reversed(DESCRIPTOR["children"][:2])
        ],
        "concurrent_join": {
            "cwd": str(children[("b-before-a", DESCRIPTOR["children"][2])]),
            "run": list(CHILD_RUN_ARGV_BY_KEY[("b-before-a", DESCRIPTOR["children"][2], 0)]),
        },
        "sequential": [
            {
                "cwd": str(children[("a-before-b", task_id)]),
                "run": list(CHILD_RUN_ARGV_BY_KEY[("a-before-b", task_id, 0)]),
            }
            for task_id in DESCRIPTOR["children"]
        ],
        "results": str(root / "controller-results.json"),
        "uv": str(Path(shutil.which("uv") or "uv").resolve()),
    }
    plan_path = root / "controller-plan.json"
    plan_path.write_bytes(canonical_json_bytes(plan))
    controller = """\
import json, os, subprocess, sys, threading
from concurrent.futures import ThreadPoolExecutor

p = json.load(open(sys.argv[1], encoding="utf-8"))
host = [p["uv"], "run", "--frozen", "python", "-m", "ranex.cli.host_confinement"]
results = []
lock = threading.Lock()
provisioning_barrier = threading.Barrier(2)
active_provisioning = 0
active_sessions = 0
maximum_active_provisioning = 0
maximum_active_sessions = 0

def provision(entry, *, concurrent=False):
    global active_provisioning, maximum_active_provisioning
    cwd = entry["cwd"]
    with lock:
        active_provisioning += 1
        maximum_active_provisioning = max(maximum_active_provisioning, active_provisioning)
    try:
        if concurrent:
            provisioning_barrier.wait()
        for command in p["commands"]:
            subprocess.run(host + command, cwd=cwd, env=os.environ, check=True)
    finally:
        with lock:
            active_provisioning -= 1

def execute(entry):
    global active_sessions, maximum_active_sessions
    cwd = entry["cwd"]
    with lock:
        active_sessions += 1
        maximum_active_sessions = max(maximum_active_sessions, active_sessions)
        if active_sessions != 1:
            raise RuntimeError("overlapping strict-local sessions are forbidden")
    try:
        completed = subprocess.run(
            [p["uv"], "run", "--frozen", *entry["run"]],
            cwd=cwd,
            env=os.environ,
            check=False,
            capture_output=True,
            text=True,
        )
        with lock:
            results.append({"cwd": cwd, "returncode": completed.returncode,
                            "stderr": completed.stderr})
    finally:
        with lock:
            active_sessions -= 1

for entry in p["sequential"]:
    provision(entry)
    execute(entry)
with ThreadPoolExecutor(max_workers=2) as pool:
    futures = [pool.submit(provision, entry, concurrent=True)
               for entry in p["concurrent_provisioning"]]
    for future in futures:
        future.result()
for entry in p["concurrent_session_order"]:
    execute(entry)
provision(p["concurrent_join"])
execute(p["concurrent_join"])
with open(p["results"], "w", encoding="utf-8") as destination:
    json.dump({"maximum_active_provisioning": maximum_active_provisioning,
               "maximum_active_sessions": maximum_active_sessions,
               "outcomes": results}, destination, sort_keys=True,
              separators=(",", ":"))
"""
    traced = trace_direct_controller(
        ["-c", controller, str(plan_path)],
        checkout=root,
        controller_python=controller_python,
        environment=cli_environment(signing_key=signing_key),
        trace_path=root.parent / "child-provisioning-calibration.strace",
    )
    assert traced.completed.returncode == 0, (
        traced.completed.stdout + traced.completed.stderr
    )
    calibration = json.loads(Path(plan["results"]).read_bytes())
    assert calibration["maximum_active_provisioning"] == 2
    assert calibration["maximum_active_sessions"] == 1
    outcomes = calibration["outcomes"]
    assert {outcome["cwd"] for outcome in outcomes} == {
        str(child) for child in children.values()
    }
    assert len(outcomes) == 6
    for outcome in outcomes:
        assert set(outcome) == {"cwd", "returncode", "stderr"}
        assert outcome["returncode"] == 0, (
            "pre-implementation RED: public strict-local v2 run source "
            "selectors have not landed; after that seam lands this calibration "
            "passes and the journey advances to the batch "
            f"parser/application seams: {outcome['stderr']}"
        )
    # Every exact child run above crosses the existing public strict-local
    # session owner, which performs the canonical full host-state drift check
    # before opening the launcher.  The independent reads below then verify
    # the resulting launcher/report bytes and qualified state.
    observer_event = json.loads(
        observe_child_provisioning(
            traced,
            governed=root,
            provenance_path=root.parent / "child-provisioning-calibration-observer.json",
            sibling_modes={
                "a-before-b": "sequential",
                "b-before-a": "concurrent-provisioning-sequential-sessions",
            },
        )
    )
    assert observer_event["run_count"] == 6
    assert observer_event["step_count"] == 18

    records = []
    for (flow_id, task_id), child in sorted(children.items()):
        provisioning, _ = verify_strict_local(child)
        report = json.loads((child / QUALIFICATION_REPORT).read_bytes())
        assert report["qualified"] is True and report["refusal"] is None
        assert file_digest(child / INSTALLED_LAUNCHER) == provisioning.artifact_digest
        assert file_digest(child / QUALIFICATION_REPORT) == provisioning.report_digest
        records.append(
            {
                "artifact_digest": provisioning.artifact_digest,
                "flow_id": flow_id,
                "qualified": True,
                "report_digest": provisioning.report_digest,
                "task_id": task_id,
            }
        )
    assert len(records) == 6
    event = {
        "canonical_verifier_outcomes": ["passed"],
        "event": "child.provisioning.calibrated",
        "maximum_active_provisioning": calibration["maximum_active_provisioning"],
        "maximum_active_sessions": calibration["maximum_active_sessions"],
        "observation_modes": [
            "sequential", "concurrent-provisioning", "sequential-sessions"
        ],
        "observer_executions_digest": observer_event["executions_digest"],
        "records_digest": "sha256:" + canonical_sha256({"records": records}),
        "run_count": len(records),
        "version": "slice036-child-provisioning-release-v1",
    }
    return canonical_json_bytes(event).decode("utf-8") + "\n"



def compare_golden(actual: str, name: str, sandbox: Path) -> None:
    del sandbox  # every family uses the one argument-free-mask frame normalizer
    expected = (EXPECTED / name).read_text(encoding="utf-8")
    # This signed family deliberately retains exact selector paths so the
    # integration contract can verify them against every B-bound child row.
    # Normalize both sides at the comparison boundary; all semantic selector
    # values are independently asserted before this byte comparison.
    try:
        _prereqs.compare_transcript(
            _prereqs.normalize_transcript(actual),
            _prereqs.normalize_transcript(expected),
            family=name.removesuffix(".out"),
        )
    except AssertionError as exc:
        raise AssertionError(f"normalized transcript differs from {name}: {exc}") from exc


def verify_actual_qualification(
    path: Path,
    *,
    command: list[str],
    journal: Path,
    evidence_events: dict[str, str],
) -> tuple[dict[str, object], str]:
    """Verify actual output with canonical JSON, the keyring loader, and admission."""

    raw = path.read_bytes()
    governed = Path(command[command.index("--target") + 1]).resolve()
    assert journal.resolve() == governed / "governance/journal.sqlite3"
    assert git(governed, "rev-parse", "refs/heads/main") == BASE_COMMIT
    artifact = json.loads(raw)
    assert raw == canonical_json_bytes(artifact)
    assert set(artifact) == {"attestation", "payload", "version"}
    assert artifact["version"] == "batch-qualification-v1"
    payload = artifact["payload"]
    assert isinstance(payload, dict)
    assert payload["version"] == "batch-qualification-payload-v1"
    assert payload["publication_allowed"] is False
    assert payload["producer_id"] == DESCRIPTOR["qualification_output"]["producer_id"]

    identities = {
        "a_digest": VECTORS["triple"]["a_digest"],
        "b_digest": VECTORS["triple"]["b_digest"],
        "base_commit": BASE_COMMIT,
        "base_digest": SUBJECT_DIGEST,
        "c_digest": VECTORS["triple"]["c_digest"],
        "child_requests_digest": VECTORS["digests"]["children"],
        "descriptor_digest": VECTORS["digests"]["descriptor"],
    }
    assert {name: payload[name] for name in identities} == identities
    assert payload["batch_digest"] == "sha256:" + canonical_sha256(identities)

    child_results = {
        "results": [
            {
                "task_id": relative.split("/")[1],
                "evidence_digest": digest,
            }
            for relative, digest in sorted(evidence_events.items())
        ]
    }
    assert payload["child_results_digest"] == (
        "sha256:" + canonical_sha256(child_results)
    )

    journal_fact = payload["qualification_journal"]
    assert isinstance(journal_fact, dict)
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT seq, record, prev_link, link FROM evaluations WHERE seq = ?",
            (journal_fact["seq"],),
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    seq, raw_record, previous_head, head = row
    record = json.loads(raw_record)
    assert record["type"] == "batch-qualified"
    assert journal_fact == {
        "seq": seq,
        "previous_head": previous_head,
        "head": head,
    }
    assert head == "sha256:" + canonical_sha256(
        {"prev_link": previous_head, "record": record}
    )
    assert payload["qualification_record_digest"] == (
        "sha256:" + canonical_sha256(record)
    )
    for field_name in (
        "a_digest",
        "b_digest",
        "base_commit",
        "base_digest",
        "batch_digest",
        "c_digest",
        "child_requests_digest",
        "child_results_digest",
        "descriptor_digest",
        "producer_id",
        "publication_allowed",
    ):
        assert record[field_name] == payload[field_name]

    attestation = artifact["attestation"]
    assert isinstance(attestation, dict)
    keyring_bytes = git_blob(governed, BASE_COMMIT, "governance/producers.yaml")
    keyring = load_keyring_text(
        keyring_bytes.decode("utf-8"),
        f"{BASE_COMMIT}:governance/producers.yaml",
    )
    role = next(
        role
        for role in DESCRIPTOR["roles"]
        if role["principal"] == payload["producer_id"]
    )
    assert keyring[payload["producer_id"]] == role["key"] == OWNER_PUBLIC_KEY
    admission = admit([attestation], keyring)
    assert admission.rejections == ()
    assert len(admission.evidence) == 1
    evidence = admission.evidence[0]
    assert evidence.claim_id == DESCRIPTOR["qualification_output"]["claim_id"]
    assert evidence.subject_digest == SUBJECT_DIGEST
    signed_command = shlex.split(attestation["command"])
    assert signed_command == command[3:]
    assert attestation["command_digest"] == command_digest(signed_command)
    suite_results = attestation["suite_results"]
    assert suite_results["manifest_digest"] == VECTORS["digests"]["descriptor"]
    assert suite_results["outcome_digest"] == (
        "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    )
    assert suite_results["counts"] == {
        "errors": 0,
        "failed": 0,
        "passed": 3,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
    }
    return artifact, file_digest(path)


def verify_publication_keyrings(
    artifact: dict[str, object],
    *,
    governed: Path,
    candidate_worktree: Path,
    candidate: str,
    tip: str,
) -> None:
    """Admit the actual outcome through all immutable publication snapshots."""

    relative = "governance/producers.yaml"
    snapshots = {
        f"base:{BASE_COMMIT}": git_blob(governed, BASE_COMMIT, relative),
        f"candidate:{candidate}": git_blob(candidate_worktree, candidate, relative),
        f"tip:{tip}": git_blob(governed, tip, relative),
    }
    assert len(set(snapshots.values())) == 1
    descriptor_role = next(
        role for role in DESCRIPTOR["roles"] if role["principal"] == "owner"
    )
    attestation = artifact["attestation"]
    assert isinstance(attestation, dict)
    for identity, raw_keyring in snapshots.items():
        keyring = load_keyring_text(raw_keyring.decode("utf-8"), identity)
        assert keyring["owner"] == descriptor_role["key"] == OWNER_PUBLIC_KEY
        admission = admit([attestation], keyring)
        assert admission.rejections == ()
        assert len(admission.evidence) == 1


def assert_pre_journal_refusal(
    command: list[str],
    *,
    code: str,
    sandbox: Path,
    target: Path,
    journal: Path,
    sentinel: LoopbackSentinel,
    checkout: Path,
    signing_key: Path,
) -> subprocess.CompletedProcess[str]:
    before = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    completed = invoke(command, checkout=checkout, signing_key=signing_key)
    assert completed.returncode != 0
    assert code in completed.stdout + completed.stderr
    after = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    assert after == before, f"{code} refusal produced a side effect"
    return completed


def assert_survivor_refusal(
    command: list[str],
    *,
    sandbox: Path,
    target: Path,
    journal: Path,
    sentinel: LoopbackSentinel,
    checkout: Path,
    signing_key: Path,
) -> None:
    """Run the protected survivor control, then prove cleanup and no append."""

    before = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    survivors_before = survivor_pids()
    process = subprocess.Popen(
        command,
        cwd=checkout,
        env=cli_environment(signing_key=signing_key),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = process.communicate(timeout=180)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    assert process.returncode != 0
    assert "E-BATCH-CHILD-SURVIVOR" in stdout + stderr
    assert re.search(r"emitted survivor pid [1-9][0-9]*", stdout + stderr)
    cleanup_deadline = time.monotonic() + 3
    while survivor_pids() - survivors_before and time.monotonic() < cleanup_deadline:
        time.sleep(0.01)
    leaked = survivor_pids() - survivors_before
    for pid in leaked:
        os.kill(pid, 9)
    assert not leaked, f"qualifier left child survivors: {sorted(leaked)}"
    after = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    assert after == before, "survivor refusal produced a persistent side effect"


def test_real_cli_qualifies_both_orders_and_independently_proves_no_publication(
    tmp_path: Path,
    loopback_sentinel: LoopbackSentinel,
) -> None:
    """The decisive real journey: no application import and no trusted booleans."""

    carried_parent = subprocess.run(
        ["git", "-C", str(ROOT), "cat-file", "-e", f"{FIXTURE_PARENT_COMMIT}^{{commit}}"],
        capture_output=True,
        check=False,
    )
    if carried_parent.returncode != 0:
        assert ROOT.name == "tree"
        assert ROOT.parent.name.startswith("ranex-subject-")
        return

    sandbox = tmp_path / "slice036"
    sandbox.mkdir()
    governed = materialize_governed_checkout(sandbox / "governed")
    governed_source_before = source_manifest(governed)
    if historical_build_input_drift(governed):
        artifact = governed / LAUNCHER_BUILD
        report = governed / QUALIFICATION_REPORT
        journal = governed / "governance/journal.sqlite3"
        before = (
            git(governed, "rev-parse", "refs/heads/main"),
            journal_snapshot(journal),
            worktree_snapshot(governed),
        )
        refused = run(
            shutil.which("uv") or "uv",
            "run",
            "--frozen",
            "python",
            "-m",
            "ranex.cli.host_confinement",
            *HOST_PROVISIONING_COMMANDS[0],
            cwd=governed,
            env=cli_environment(),
        )
        assert refused.returncode != 0
        assert "E-C17-BUILD-INPUT-DRIFT" in refused.stdout + refused.stderr
        assert not artifact.exists()
        assert not report.exists()
        after = (
            git(governed, "rev-parse", "refs/heads/main"),
            journal_snapshot(journal),
            worktree_snapshot(governed),
        )
        assert after == before
        assert git(governed, "status", "--porcelain") == ""
        return
    development_source, source_transcript = observe_development_source(governed)
    signing_key = materialize_signing_key(tmp_path / "slice036-owner.key")
    child_calibration_transcript = calibrate_child_provisioning_release_invariant(
        sandbox / "child-provisioning-calibration",
        controller_python=development_source.controller_python,
        signing_key=signing_key,
    )
    provisioning, provisioning_transcript = provision_strict_local(governed)
    assert not development_source.module_path.is_relative_to(governed.resolve())
    provenance_record = {
        "controller_python": str(development_source.controller_python),
        "governed_repository": str(governed.resolve()),
        "manifest_digest": development_source.manifest_digest,
        "module_path": str(development_source.module_path),
        "pythonpath": str(development_source.pythonpath),
        "version": "slice036-development-source-v1",
    }
    provenance_path = sandbox / "source-provenance.json"
    provenance_path.write_bytes(canonical_json_bytes(provenance_record))
    assert json.loads(provenance_path.read_bytes()) == provenance_record
    authority = materialize_authority(sandbox / "authority")
    journal = governed / "governance/journal.sqlite3"
    outcome = sandbox / "outcomes"
    ref_before = git(governed, "rev-parse", "refs/heads/main")
    worktrees_before = worktree_snapshot(governed)
    network_before = len(loopback_sentinel.accepted)

    positive_command = qualify_command(
        authority=authority,
        target=governed,
        journal=journal,
        outcome=outcome,
    )
    assert Path(positive_command[positive_command.index("--target") + 1]).resolve() == (
        governed.resolve()
    )
    assert journal.resolve() == governed.resolve() / "governance/journal.sqlite3"
    traced = invoke_traced(
        positive_command,
        checkout=governed,
        controller_python=development_source.controller_python,
        signing_key=signing_key,
        trace_path=sandbox / "child-provisioning.strace",
    )
    completed = traced.completed
    assert completed.returncode == 0, completed.stderr
    child_observer_transcript = observe_child_provisioning(
        traced,
        governed=governed,
        provenance_path=sandbox / "child-provisioning-observer.json",
    )
    compare_golden(
        source_transcript
        + provisioning_transcript
        + child_calibration_transcript
        + child_observer_transcript
        + completed.stdout,
        "slice036-approved-batch-qualification.out",
        sandbox,
    )

    assert git(governed, "rev-parse", "refs/heads/main") == ref_before == BASE_COMMIT
    assert worktree_snapshot(governed) == worktrees_before
    assert git(governed, "status", "--porcelain") == ""
    assert source_manifest(governed) == governed_source_before
    assert file_digest(governed / QUALIFICATION_REPORT) == provisioning.report_digest
    assert len(loopback_sentinel.accepted) == network_before

    rows, head = journal_snapshot(journal)
    assert rows == 1 and isinstance(head, str) and head.startswith("sha256:")
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        record = json.loads(
            connection.execute(
                "SELECT record FROM evaluations ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
        )
    finally:
        connection.close()
    assert record["type"] == "batch-qualified"
    assert record["base_commit"] == BASE_COMMIT
    assert record["base_digest"] == SUBJECT_DIGEST

    evidence_events = {
        event["path"]: event["digest"]
        for event in map(json.loads, completed.stdout.splitlines())
        if event["event"] == "batch.evidence"
    }
    expected_evidence = {
        row["path"]
        for child in (
            json.loads(line)
            for line in (FIXTURES / "approved-batch-child-requests-v1.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        for row in child["evidence"]
    }
    assert set(evidence_events) == expected_evidence
    for relative, reported_digest in evidence_events.items():
        evidence = outcome / relative
        assert evidence.is_file()
        assert file_digest(evidence) == reported_digest

    qualification_events = [
        event
        for event in map(json.loads, completed.stdout.splitlines())
        if event["event"] == "batch.qualification"
    ]
    assert len(qualification_events) == 1
    qualification_event = qualification_events[0]
    batch_artifact = outcome / DESCRIPTOR["qualification_output"]["path"]
    qualification, qualification_digest = verify_actual_qualification(
        batch_artifact,
        command=positive_command,
        journal=journal,
        evidence_events=evidence_events,
    )
    assert qualification_event == {
        "digest": qualification_digest,
        "event": "batch.qualification",
        "path": DESCRIPTOR["qualification_output"]["path"],
        "producer_id": DESCRIPTOR["qualification_output"]["producer_id"],
    }
    assert qualification["payload"]["qualification_journal"]["head"] == head

    # Each control below is a separately B-protected child-input artifact and
    # enters only through the real public CLI.  No helper receives a post-hoc
    # failure boolean and no application result is trusted as the observer.
    protected = {
        row["path"]: row["digest"]
        for row in VECTORS["triple"]["b"]["artifacts"]["protected"]
    }
    public_controls = (
        ("unapproved_rows", "E-BATCH-UNAPPROVED-ROW"),
        ("input_mismatch_rows", "E-BATCH-INPUT-MISMATCH"),
        ("overlap_rows", "E-BATCH-SCOPE-OVERLAP"),
        ("network_rows", "E-BATCH-NETWORK-ESCAPE"),
        ("oracle_mismatch_rows", "E-BATCH-ORACLE-MISMATCH"),
    )
    for ordinal, (fixture_name, code) in enumerate(public_controls, start=1):
        relative = VECTORS["paths"][fixture_name]
        tasks = ROOT / relative
        assert file_digest(tasks) == protected[relative]
        control_journal = sandbox / f"public-control-{ordinal}.sqlite3"
        control_outcome = sandbox / f"public-control-{ordinal}"
        control = assert_pre_journal_refusal(
            qualify_command(
                authority=authority,
                target=governed,
                journal=control_journal,
                outcome=control_outcome,
                tasks=tasks,
            ),
            code=code,
            sandbox=sandbox,
            target=governed,
            journal=control_journal,
            sentinel=loopback_sentinel,
            checkout=governed,
            signing_key=signing_key,
        )
        if fixture_name == "oracle_mismatch_rows":
            assert "exited 92 before emitting the oracle result" in control.stderr

    survivor_relative = VECTORS["paths"]["survivor_rows"]
    survivor_tasks = ROOT / survivor_relative
    assert file_digest(survivor_tasks) == protected[survivor_relative]
    assert_survivor_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=sandbox / "survivor-refusal.sqlite3",
            outcome=sandbox / "survivor-refusal",
            tasks=survivor_tasks,
        ),
        sandbox=sandbox,
        target=governed,
        journal=sandbox / "survivor-refusal.sqlite3",
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )

    # Calibration proves the golden comparator itself detects changed bytes.
    with pytest.raises(AssertionError, match="normalized transcript differs"):
        compare_golden(
            source_transcript
            + provisioning_transcript
            + completed.stdout.replace('"publication":false', '"publication":true'),
            "slice036-approved-batch-qualification.out",
            sandbox,
        )

    # Stale C/journal predecessor is known before execution and leaves even the
    # successful outcome bytes untouched.
    assert_pre_journal_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=journal,
            outcome=outcome,
        ),
        code="E-BATCH-STALE-BASE",
        sandbox=sandbox,
        target=governed,
        journal=journal,
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )

    # Pool widening and protected-byte substitution each use fresh absent
    # journals, and independent snapshots prove the refusal precedes writes.
    pool_journal = sandbox / "pool-refusal.sqlite3"
    pool_outcome = sandbox / "pool-refusal"
    assert_pre_journal_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=pool_journal,
            outcome=pool_outcome,
            pool=3,
        ),
        code="E-BATCH-POOL-EXCEEDS",
        sandbox=sandbox,
        target=governed,
        journal=pool_journal,
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )
    tampered = sandbox / "tampered-descriptor.json"
    tampered_record = json.loads(
        (FIXTURES / "approved-batch-v1.json").read_text(encoding="utf-8")
    )
    tampered_record["maximum_pool"] = 1
    tampered.write_bytes(canonical_json_bytes(tampered_record))
    tamper_journal = sandbox / "tamper-refusal.sqlite3"
    tamper_outcome = sandbox / "tamper-refusal"
    assert_pre_journal_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=tamper_journal,
            outcome=tamper_outcome,
            descriptor=tampered,
        ),
        code="E-BATCH-SCHEMA",
        sandbox=sandbox,
        target=governed,
        journal=tamper_journal,
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )

    # A moved real ref and a real surviving Git worktree are planted controls,
    # not values returned by the application under test.
    moved = git(governed, "rev-parse", f"{BASE_COMMIT}^")
    git(governed, "update-ref", "refs/heads/main", moved, BASE_COMMIT)
    moved_journal = sandbox / "moved-refusal.sqlite3"
    moved_outcome = sandbox / "moved-refusal"
    try:
        assert_pre_journal_refusal(
            qualify_command(
                authority=authority,
                target=governed,
                journal=moved_journal,
                outcome=moved_outcome,
            ),
            code="E-BATCH-STALE-BASE",
            sandbox=sandbox,
            target=governed,
            journal=moved_journal,
            sentinel=loopback_sentinel,
            checkout=governed,
            signing_key=signing_key,
        )
    finally:
        git(governed, "update-ref", "refs/heads/main", BASE_COMMIT, moved)

    rogue = sandbox / "rogue-worktree"
    assert run(
        "git", "-C", str(governed), "worktree", "add", "--quiet", "--detach", str(rogue), BASE_COMMIT
    ).returncode == 0
    residue_journal = sandbox / "residue-refusal.sqlite3"
    residue_outcome = sandbox / "residue-refusal"
    try:
        assert_pre_journal_refusal(
            qualify_command(
                authority=authority,
                target=governed,
                journal=residue_journal,
                outcome=residue_outcome,
            ),
            code="E-BATCH-WORKTREE-RESIDUE",
            sandbox=sandbox,
            target=governed,
            journal=residue_journal,
            sentinel=loopback_sentinel,
            checkout=governed,
            signing_key=signing_key,
        )
    finally:
        removal = run(
            "git", "-C", str(governed), "worktree", "remove", "--force", str(rogue)
        )
        assert removal.returncode == 0, removal.stderr

    # Judge/merge use the same disposable governed checkout and actual fixed
    # journal qualification already appended.  There is no unrelated database
    # and no second checkout with different source provenance.
    publication_journal = journal
    publication_worktree = sandbox / "publication-worktree"
    dispatch = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "dispatch",
        "--task-id",
        "SLICE-036-child-A",
        "--target",
        str(governed),
        "--worktree",
        str(publication_worktree),
        "--journal",
        str(publication_journal),
    ]
    dispatch_result = invoke(
        dispatch,
        checkout=governed,
        signing_key=signing_key,
    )
    assert dispatch_result.returncode == 0, dispatch_result.stderr
    assert Path(dispatch[dispatch.index("--target") + 1]).resolve() == governed.resolve()
    assert journal_snapshot(publication_journal)[0] == 2

    first_evidence = outcome / sorted(expected_evidence)[0]
    governed_evidence = publication_worktree / "governance/qualification/evidence.json"
    governed_evidence.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(first_evidence, governed_evidence)
    candidate = git(publication_worktree, "rev-parse", "HEAD")
    assert candidate == BASE_COMMIT
    verify_publication_keyrings(
        qualification,
        governed=governed,
        candidate_worktree=publication_worktree,
        candidate=candidate,
        tip=ref_before,
    )
    judge = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "judge",
        "--task-id",
        "SLICE-036-child-A",
        "--emitted-worktree",
        str(publication_worktree),
        "--emitted-commit",
        candidate,
        "--gate",
        "landing",
        "--gate-catalog",
        str(publication_worktree / "governance/gates.yaml"),
        "--evidence",
        str(governed_evidence),
        "--producers",
        str(publication_worktree / "governance/producers.yaml"),
        "--suite-manifest",
        str(publication_worktree / "governance/suite_manifest.json"),
        "--journal",
        str(publication_journal),
        "--batch-qualification",
        str(batch_artifact),
    ]
    merge = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "merge",
        "--task-id",
        "SLICE-036-child-A",
        "--target-ref",
        "refs/heads/main",
        "--candidate",
        candidate,
        "--approval",
        str(authority[2]),
        "--batch-qualification",
        str(batch_artifact),
    ]
    publication_before = (
        git(governed, "rev-parse", "refs/heads/main"),
        journal_snapshot(publication_journal),
        worktree_snapshot(governed),
        filesystem_snapshot(sandbox),
        len(loopback_sentinel.accepted),
        survivor_pids(),
    )
    judge_result = invoke(judge, checkout=governed, signing_key=signing_key)
    merge_result = invoke(merge, checkout=governed, signing_key=signing_key)
    assert judge_result.returncode != 0 and merge_result.returncode != 0
    transcript = (
        "task judge: " + judge_result.stderr.strip() + "\n"
        "task merge: " + merge_result.stderr.strip() + "\n"
    )
    compare_golden(
        transcript,
        "slice036-approved-batch-publication-refusal.out",
        sandbox,
    )
    assert (
        git(governed, "rev-parse", "refs/heads/main"),
        journal_snapshot(publication_journal),
        worktree_snapshot(governed),
        filesystem_snapshot(sandbox),
        len(loopback_sentinel.accepted),
        survivor_pids(),
    ) == publication_before
