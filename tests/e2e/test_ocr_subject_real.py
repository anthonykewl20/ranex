"""#105 — OCR Go binary as a v3 ELF entrypoint subject (Arm 0).

The pinned open-code-review release is a self-contained static ``ET_EXEC``
with no ``PT_INTERP``. Runtime v3 admits exactly that shape as a closure
``entrypoint`` (``pt_interp: null`` plus the exact static entrypoint shape,
ADR-035 / issue #105 arm 0). This module freezes the admission on the
structural control and, when the pinned binary is present, on the real OCR
bytes through ``parsed_runtime_graph`` and the realized-graph round-trip.

Arms 1–5 remain field-proof UNVERIFIED pending their own runs — see
``tools/dogfood/audits/2026-09-30-ocr-subject/``. Findings stay advisory.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from elftools.elf.elffile import ELFFile

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.dynamic_runtime import (
    expected_realized_runtime_graph,
    parse_runtime_manifest,
    parsed_graph_digest,
    parsed_runtime_graph,
    realized_graph_digest,
    realized_runtime_graph_from_reports,
)
from ranex.foundation.static_executable import (
    inspect_self_contained_static_executable,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests" / "e2e" / "fixtures" / "slice072-runtime" / "closure.json"
OCR_TAG = "v1.12.9"
OCR_SHA256 = "9105c7081b8362a1cb0167f1ddfd1437e147a0e3c9a5af89c03c8859a5b0f0e8"
OCR_ASSET = "opencodereview-linux-amd64"
CACHE = Path.home() / ".cache" / "ranex" / "ocr" / OCR_TAG / OCR_ASSET


def _static_entry_row(digest: str) -> dict[str, object]:
    return {
        "path": "bin/opencodereview",
        "mode": "0555",
        "kind": "entrypoint",
        "sha256": digest,
        "elf": {
            "abi_version": 0,
            "audit": None,
            "auxiliary": None,
            "depaudit": None,
            "elf_class": 64,
            "endian": "little",
            "filter": None,
            "machine": "EM_X86_64",
            "needed": [],
            "osabi": "ELFOSABI_SYSV",
            "pt_interp": None,
            "rpath": None,
            "runpath": None,
            "soname": None,
            "type": "ET_EXEC",
        },
    }


def _closure_with_null_interp_entrypoint(*, digest: str) -> bytes:
    base = json.loads(FIXTURE.read_bytes())
    base["entrypoint"] = {
        "path": "bin/opencodereview",
        "pt_interp": None,
        "sha256": digest,
    }
    base["files"] = [
        _static_entry_row(digest) if row["kind"] == "entrypoint" else row
        for row in base["files"]
    ]
    return canonical_json_bytes(base)


def _two_row_closure(digest: str) -> bytes:
    """The honest OCR closure trimmed to its loader and static entrypoint rows."""
    base = json.loads(FIXTURE.read_bytes())
    loader_row = next(row for row in base["files"] if row["kind"] == "loader")
    value = {
        "schema": base["schema"],
        "architecture": base["architecture"],
        "loader": base["loader"],
        "entrypoint": {"path": "bin/opencodereview", "pt_interp": None, "sha256": digest},
        "library_paths": base["library_paths"],
        "files": [_static_entry_row(digest), loader_row],
    }
    return canonical_json_bytes(value)


def test_v3_admits_entrypoint_with_null_pt_interp() -> None:
    """Structural Arm 0 control: an honest null interp binds the loader."""

    digest = "sha256:" + "ab" * 32
    outcomes = []
    for _ in range(3):
        try:
            parsed = parse_runtime_manifest(
                _closure_with_null_interp_entrypoint(digest=digest)
            )
            outcomes.append(parsed.value["entrypoint"]["pt_interp"])
        except ValueError as exc:
            outcomes.append(str(exc))
    assert outcomes == [None] * 3


def _resolve_ocr_binary() -> Path:
    env = os.environ.get("RANEX_OCR_BINARY", "").strip()
    candidates = [Path(env)] if env else []
    candidates.append(CACHE)
    candidates.append(Path("/tmp/ocr-pin") / OCR_ASSET)
    for candidate in candidates:
        if candidate.is_file() and os.access(candidate, os.X_OK):
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if digest != OCR_SHA256:
                pytest.skip(
                    "ranex-context:ocr-pin: "
                    f"{candidate} sha256={digest} does not match pin {OCR_SHA256}"
                )
            return candidate
    pytest.skip(
        "ranex-context:ocr-pin: pinned open-code-review "
        f"{OCR_TAG} linux-amd64 absent; set RANEX_OCR_BINARY or cache at {CACHE}"
    )


def test_ocr_v1_12_9_is_static_and_admitted_as_v3_entrypoint(tmp_path: Path) -> None:
    """Real OCR pin: static-v2 admits and the v3 entrypoint path admits x3."""

    binary = _resolve_ocr_binary()
    payload = binary.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == OCR_SHA256

    elf = ELFFile(io.BytesIO(payload))
    assert elf.header["e_type"] == "ET_EXEC"
    assert not any(seg["p_type"] == "PT_INTERP" for seg in elf.iter_segments())
    assert not any(seg["p_type"] == "PT_DYNAMIC" for seg in elf.iter_segments())

    fd = os.open(binary, os.O_RDONLY | os.O_CLOEXEC)
    try:
        inspect_self_contained_static_executable(fd, binary)
    finally:
        os.close(fd)

    digest = "sha256:" + OCR_SHA256
    reasons = []
    for _ in range(3):
        try:
            parse_runtime_manifest(_closure_with_null_interp_entrypoint(digest=digest))
            reasons.append("ADMITTED")
        except ValueError as exc:
            reasons.append(str(exc))
    assert reasons == ["ADMITTED"] * 3

    root = tmp_path / "closure"
    (root / "bin").mkdir(parents=True)
    (root / "loader").mkdir()
    (root / "bin/opencodereview").write_bytes(payload)
    (root / "loader/ld-linux-x86-64.so.2").write_bytes(
        (FIXTURE.parent / "loader/ld-linux-x86-64.so.2").read_bytes()
    )
    manifest = parse_runtime_manifest(_two_row_closure(digest))
    assert parsed_runtime_graph(root, manifest) == [
        {"path": "bin/opencodereview", "needed": []},
        {"path": "loader/ld-linux-x86-64.so.2", "needed": []},
    ]
    assert expected_realized_runtime_graph(
        manifest
    ) == realized_runtime_graph_from_reports({"bin/opencodereview": b"statically linked"})


# --- #105 Phase 3: the real launcher/confinement harness ----------------------
#
# The three tests below run the pinned OCR bytes as a v3 static entrypoint
# through the real `host_confinement` session surface (real launcher binary,
# real namespaces/Landlock/seccomp/cgroups — no mocks).  The verifier report
# binding is observed through the result's realized-graph digest: only the
# frozen `statically linked` text normalizes to the empty static shape, and
# the launcher emits exactly that literal (frozen in
# tests/security/test_slice072_dynamic_runtime_security.py).  The worker's
# `--version` TEXT cannot ride the harness — the launcher closes fds 0-2
# before exec and the output drain collects /ranex/output files only — so
# the binary's own real output is asserted on the byte-identical payload as
# a host-side real subprocess while its own exit code is asserted in-session.

HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
V3_PROFILE = "governance/confinement/strict-local-v3.json"
LAUNCHER_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
LAUNCHER_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_OUTPUT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
QUALIFICATION = ".local/ranex/qualification/strict-local-v1.json"
OCR_CLOSURE = "tests/e2e/fixtures/ocr-static-runtime"
OCR_INPUT = "tests/e2e/fixtures/ocr-static-input"


@dataclass(frozen=True)
class OcrJourney:
    repository: Path
    binary: Path


def _module(repository: Path, module: str, *arguments: str):
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=repository,
        env={
            "PATH": os.environ["PATH"],
            "PYTHONPATH": str(repository / "src"),
            "LC_ALL": "C",
            "TZ": "UTC",
        },
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def ocr_journey(
    tmp_path_factory: pytest.TempPathFactory, prereq_qualified_host: None
) -> OcrJourney:
    """Clone, seal the OCR closure, build the pinned launcher, qualify."""

    binary = _resolve_ocr_binary()
    payload = binary.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == OCR_SHA256
    repository = tmp_path_factory.mktemp("ocr-static") / "repository"
    completed = subprocess.run(
        ["git", "clone", "-q", str(ROOT), str(repository)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    # The clone alone carries only committed bytes: the review-time working
    # tree rides along so the journey always exercises the tree under test.
    diff = subprocess.run(
        ["git", "-C", str(ROOT), "diff", "HEAD", "--binary"],
        capture_output=True,
        check=True,
    ).stdout
    if diff:
        applied = subprocess.run(
            ["git", "-C", str(repository), "apply", "--whitespace=nowarn", "-"],
            input=diff,
            capture_output=True,
            check=False,
        )
        assert applied.returncode == 0, applied.stderr
    untracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for relative in untracked:
        source = ROOT / relative
        if source.is_file():
            target = repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
    closure = repository / OCR_CLOSURE
    (closure / "bin").mkdir(parents=True)
    (closure / "loader").mkdir()
    (closure / "bin/opencodereview").write_bytes(payload)
    (closure / "loader/ld-linux-x86-64.so.2").write_bytes(
        (FIXTURE.parent / "loader/ld-linux-x86-64.so.2").read_bytes()
    )
    (closure / "closure.json").write_bytes(_two_row_closure("sha256:" + OCR_SHA256) + b"\n")
    (repository / OCR_INPUT).mkdir(parents=True)
    (repository / OCR_INPUT / "seed.txt").write_text(
        "ocr static subject\n", encoding="utf-8"
    )
    for arguments in (
        (
            "launcher-build",
            "--manifest",
            LAUNCHER_MANIFEST,
            "--source",
            LAUNCHER_SOURCE,
            "--output",
            BUILD_OUTPUT,
        ),
        (
            "launcher-install",
            "--manifest",
            LAUNCHER_MANIFEST,
            "--artifact",
            BUILD_OUTPUT,
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
            QUALIFICATION,
        ),
    ):
        completed = _module(repository, "ranex.cli.host_confinement", *arguments)
        assert completed.returncode == 0, completed.stdout + completed.stderr
    return OcrJourney(repository, binary)


def _run_session(journey: OcrJourney, token: str, argv: list[str]):
    session_root = journey.repository / "ocr-session" / token
    subject = session_root / "subject"
    for name in (subject, session_root / "output", session_root / "scratch"):
        name.mkdir(parents=True)
    (subject / "demo.txt").write_text("demo\n", encoding="utf-8")
    descriptor_path = session_root / "descriptor.json"
    result_path = session_root / "result.json"
    descriptor_path.write_bytes(
        canonical_json_bytes(
            {
                "argv": argv,
                "environment": {"LC_ALL": "C", "TZ": "UTC"},
                "input": OCR_INPUT,
                "limits": {
                    "cpu_usage_usec": 2_000_000,
                    "memory_bytes": 268_435_456,
                    "output_bytes": 65_536,
                    "output_depth": 8,
                    "output_inodes": 32,
                    "pids": 32,
                    "wall_time_ms": 30_000,
                },
                "output": (session_root / "output")
                .relative_to(journey.repository)
                .as_posix(),
                "runtime": OCR_CLOSURE,
                "schema": "ranex-confinement-command-v2",
                "scratch": (session_root / "scratch")
                .relative_to(journey.repository)
                .as_posix(),
                "subject": subject.relative_to(journey.repository).as_posix(),
            }
        )
    )
    completed = _module(
        journey.repository,
        "ranex.cli.host_confinement",
        "session",
        "--profile",
        V3_PROFILE,
        "--host-profile",
        HOST_PROFILE,
        "--artifact",
        INSTALLED_LAUNCHER,
        "--manifest",
        LAUNCHER_MANIFEST,
        "--qualification",
        QUALIFICATION,
        "--descriptor",
        descriptor_path.relative_to(journey.repository).as_posix(),
        "--result",
        result_path.relative_to(journey.repository).as_posix(),
    )
    return completed, result_path


def test_static_entrypoint_session_binds_the_statically_linked_report(
    ocr_journey: OcrJourney,
) -> None:
    """Phase 3: static root reports exactly `statically linked`, no exec."""

    argv = ["/ranex/runtime/bin/opencodereview", "--version"]
    completed, result_path = _run_session(ocr_journey, "version", argv)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(result_path.read_bytes())
    assert result["schema"] == "ranex-confinement-result-v2"
    command = result["command"]
    # The static worker runs to completion in-session: its closed standard
    # descriptors are replaced by the launcher's own sealed, empty memfd
    # (inert_standard_fds — a channel-free fd set the Go runtime's checkfds
    # accepts), so the in-session exit code equals the host-side `--version`
    # exit code instead of the pre-main checkfds fatal.
    assert command["exit_code"] == 0
    assert command["argv_digest"] == hashlib.sha256(
        canonical_json_bytes(argv)
    ).hexdigest()
    assert command["no_new_privs"] is True
    assert command["landlock"] is True
    assert command["seccomp"] is True

    static_report = realized_runtime_graph_from_reports(
        {"bin/opencodereview": b"statically linked"}
    )
    assert static_report == [{"root": "bin/opencodereview", "resolved": []}]
    raw_manifest = (ocr_journey.repository / OCR_CLOSURE / "closure.json").read_bytes()
    manifest = parse_runtime_manifest(raw_manifest)
    assert static_report == expected_realized_runtime_graph(manifest)
    runtime = result["runtime_closure"]
    assert runtime["realized_graph_digest"] == realized_graph_digest(static_report)
    assert runtime["parsed_graph_digest"] == parsed_graph_digest(
        parsed_runtime_graph(ocr_journey.repository / OCR_CLOSURE, manifest)
    )
    assert runtime["manifest_digest"] == hashlib.sha256(raw_manifest).hexdigest()
    assert result["outputs"] == []
    assert result["teardown"] == {
        "cgroup_kill": True,
        "populated": 0,
        "cgroup_removed": True,
    }


def test_static_entrypoint_runs_in_session_with_inert_standard_fds(
    ocr_journey: OcrJourney,
) -> None:
    """OCR's own real output exists and the in-session run matches the host.

    The sealed payload is byte-identical to the pinned release binary and its
    own ``--version`` text carries ``open-code-review`` (asserted below on the
    real bytes).  A static Go runtime's ``checkfds`` reopens fds 0-2 through
    ``/dev/null`` when they are closed, which a zero-device-node namespace
    cannot serve (``fatal error: cannot open standard fds``, exit 2 before
    main() — measured in a fully traced real session with zero seccomp
    denials).  The remedy (owner decision, 2026-09-30): the launcher dups ONE
    sealed, empty memfd it creates itself — never inherited authority — over
    fds 0-2 for static workers only.  The descriptors exist but carry no
    channel: reads are EOF and writes fail under F_SEAL_WRITE.  In-session
    exit codes now equal the host-side exit codes measured below.
    """

    sealed = ocr_journey.repository / OCR_CLOSURE / "bin/opencodereview"
    assert sealed.read_bytes() == ocr_journey.binary.read_bytes()
    version = subprocess.run(
        [str(ocr_journey.binary), "--version"],
        capture_output=True,
        text=True,
        check=False,
        env={"LC_ALL": "C", "TZ": "UTC"},
    )
    assert version.returncode == 0
    assert "open-code-review" in version.stdout
    bad_flag = subprocess.run(
        [str(ocr_journey.binary), "--definitely-not-an-ocr-flag"],
        capture_output=True,
        text=True,
        check=False,
        env={"LC_ALL": "C", "TZ": "UTC"},
    )
    assert bad_flag.returncode == 1
    for token, arguments, host_code in (
        ("inert-version", ["--version"], version.returncode),
        ("inert-bad-flag", ["--definitely-not-an-ocr-flag"], bad_flag.returncode),
    ):
        completed, result_path = _run_session(
            ocr_journey, token, ["/ranex/runtime/bin/opencodereview", *arguments]
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result = json.loads(result_path.read_bytes())
        assert result["command"]["exit_code"] == host_code
        assert result["outputs"] == []


def test_tampered_ocr_bytes_refuse_the_session(ocr_journey: OcrJourney) -> None:
    """Phase 3: a tampered static binary digest refuses before any result."""

    target = ocr_journey.repository / OCR_CLOSURE / "bin/opencodereview"
    original = target.read_bytes()
    target.write_bytes(original + b"tamper")
    try:
        completed, result_path = _run_session(
            ocr_journey, "tampered", ["/ranex/runtime/bin/opencodereview", "--version"]
        )
        assert completed.returncode != 0
        assert not result_path.exists()
        assert "digest" in (completed.stdout + completed.stderr).lower()
    finally:
        target.write_bytes(original)
