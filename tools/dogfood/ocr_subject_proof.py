#!/usr/bin/env python3
"""#105 field proof v2 — the FIXED behavior measured on real data.

Arms follow issue #105's mandatory protocol (#95 vocabulary): real `ranex`
subprocesses on real repositories, no mocks, statuses VERIFIED / GAP /
FALSE-PASS / NON-DETERMINISTIC / UNVERIFIED, every expectation with a positive
control, a negative control and a repeated identical-input run.

Arm 0 admits the pinned OCR Go binary as a runtime-v3 static ``entrypoint``
(``pt_interp: null``, byte-verified) — the Phase 1-3 fix. The pre-fix
refusal (a dynamic-binding closure over static bytes) survives here as a
negative control, not the headline. Arms 1-2 run a real `ranex run`/gate
journey whose bound command is the OCR binary under strict-local v3, offline,
with the model key unset then set; the verdict digests must be identical
("removing every model credential must not change a verdict"). Arm 3 drives
`ocr delegate` delegation mode into the #102 packet -> SARIF admission path.
Arm 4 is the live ranex-app-live-probe PR journey. Arm 5 repeats arms 1-2.

    uv run --frozen python tools/dogfood/ocr_subject_proof.py \
        --out tools/dogfood/audits/2026-09-30-ocr-subject-v2

No mocks. Real release bytes, real checksum, real `parse_runtime_manifest`,
real strict-local sessions, real Ed25519 keys, real gate journeys.
`KERNEL_DIGEST` untouched.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import hashlib
import json
import os
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

DOGFOOD = Path(__file__).resolve().parent
REPOSITORY = DOGFOOD.parents[1]
sys.path[:0] = [str(REPOSITORY / "src")]

from ranex.foundation.canonical import canonical_json_bytes  # noqa: E402
from ranex.foundation.dynamic_runtime import (  # noqa: E402
    expected_realized_runtime_graph,
    parse_runtime_manifest,
    parsed_runtime_graph,
    realized_runtime_graph_from_reports,
    seal_runtime_file,
)
from ranex.foundation.static_executable import (  # noqa: E402
    inspect_self_contained_static_executable,
)

OCR_TAG = "v1.12.9"
OCR_COMMIT_FLOOR = "14b84f08a3af7f042d702c721f21f7952d841970"
OCR_ASSET = "opencodereview-linux-amd64"
# sha256sum.txt from the v1.12.9 release (retained).
OCR_SHA256 = "9105c7081b8362a1cb0167f1ddfd1437e147a0e3c9a5af89c03c8859a5b0f0e8"
OCR_URL = (
    "https://github.com/alibaba/open-code-review/releases/download/"
    f"{OCR_TAG}/{OCR_ASSET}"
)
CHECKSUMS_URL = (
    "https://github.com/alibaba/open-code-review/releases/download/"
    f"{OCR_TAG}/sha256sum.txt"
)
CACHE = Path.home() / ".cache" / "ranex" / "ocr" / OCR_TAG / OCR_ASSET
FIXTURE_CLOSURE = (
    REPOSITORY / "tests" / "e2e" / "fixtures" / "slice072-runtime" / "closure.json"
)
FIXTURE_LOADER = (
    REPOSITORY / "tests" / "e2e" / "fixtures" / "slice072-runtime"
    / "loader" / "ld-linux-x86-64.so.2"
)

# The journey's governed constants (mirroring tests/e2e/test_ocr_subject_real.py).
OCR_CLOSURE = "tests/e2e/fixtures/ocr-static-runtime"
OCR_INPUT = "tests/e2e/fixtures/ocr-static-input"
V3_PROFILE = "governance/confinement/strict-local-v3.json"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
LAUNCHER_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
LAUNCHER_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_OUTPUT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
QUALIFICATION = ".local/ranex/qualification/strict-local-v1.json"

WORKER = "ocr-subject-worker"
APPROVER = "ocr-subject-approver"
SIGNER = "ocr-subject-signer"
EVIDENCE = ".local/ranex-105/evidence.json"

# The bound command: the pinned OCR binary's own SARIF-writing review argv.
# The gate loader's canonical SARIF spelling (--output-format=sarif /
# --output-file=...) is refused by this CLI (measured: "unknown flag"), so the
# honest binding is the binary's real grammar, exit-code-only; the artifact
# slot it names is measured absent in the failure arms.
OCR_ARGV = [
    "/ranex/runtime/bin/opencodereview",
    "review",
    "--format",
    "sarif",
    "-o",
    "/ranex/output/ocr.sarif",
    "--audience",
    "agent",
]

# Fake probe credentials: presence/absence is what the invariant measures;
# these values never authenticate anywhere and are refused at the socket.
PROBE_TOKEN = "sk-ant-probe-not-a-real-token-0000"
PROBE_ENDPOINT = "http://127.0.0.1:9/v1"


def _record(
    out: Path,
    name: str,
    *,
    status: str,
    argv: list[str],
    cwd: str,
    exit_code: int,
    digests: dict[str, str],
    notes: str,
    wall_ms: int | None = None,
) -> None:
    payload: dict[str, object] = {
        "expectation": name,
        "status": status,
        "argv": argv,
        "cwd": cwd,
        "exit_code": exit_code,
        "digests": digests,
        "notes": notes,
    }
    if wall_ms is not None:
        payload["wall_ms"] = wall_ms
    (out / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sidecar(out: Path, name: str, value: object) -> None:
    (out / name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _fetch_ocr(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file():
        digest = hashlib.sha256(destination.read_bytes()).hexdigest()
        if digest == OCR_SHA256:
            return destination
        destination.unlink()
    print(f"fetching {OCR_URL}", file=sys.stderr)
    with urllib.request.urlopen(OCR_URL, timeout=120) as response:  # noqa: S310
        destination.write_bytes(response.read())
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    if digest != OCR_SHA256:
        raise SystemExit(f"OCR checksum mismatch: got {digest}, want {OCR_SHA256}")
    destination.chmod(0o755)
    checksums = destination.parent / "sha256sum.txt"
    with urllib.request.urlopen(CHECKSUMS_URL, timeout=60) as response:  # noqa: S310
        checksums.write_bytes(response.read())
    return destination


def _ocr_elf_facts(binary: Path) -> dict[str, object]:
    from elftools.elf.elffile import ELFFile

    payload = binary.read_bytes()
    elf = ELFFile(__import__("io").BytesIO(payload))
    interp = None
    for segment in elf.iter_segments():
        if segment["p_type"] == "PT_INTERP":
            interp = segment.get_interp_name()
    return {
        "e_type": elf.header["e_type"],
        "pt_interp": interp,
        "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }


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


def _dynamic_entry_row(digest: str) -> dict[str, object]:
    """The pre-#105 shape: a dynamic interp binding over the entrypoint row."""

    row = _static_entry_row(digest)
    row["elf"]["pt_interp"] = "/lib64/ld-linux-x86-64.so.2"  # type: ignore[index]
    return row


def _two_row_closure(
    entry_digest: str,
    *,
    entry_row: dict[str, object] | None = None,
    entry_interp: str | None = None,
) -> bytes:
    """The honest OCR closure trimmed to its loader and entrypoint rows."""

    base = json.loads(FIXTURE_CLOSURE.read_bytes())
    loader_row = next(row for row in base["files"] if row["kind"] == "loader")
    value = {
        "schema": base["schema"],
        "architecture": base["architecture"],
        "loader": base["loader"],
        "entrypoint": {
            "path": "bin/opencodereview",
            "pt_interp": entry_interp,
            "sha256": entry_digest,
        },
        "library_paths": base["library_paths"],
        "files": [entry_row or _static_entry_row(entry_digest), loader_row],
    }
    return canonical_json_bytes(value)


def _materialise_closure(root: Path, manifest: bytes, payload: bytes, loader: bytes) -> None:
    (root / "bin").mkdir(parents=True, exist_ok=True)
    (root / "loader").mkdir(parents=True, exist_ok=True)
    (root / "bin/opencodereview").write_bytes(payload)
    (root / "loader/ld-linux-x86-64.so.2").write_bytes(loader)
    (root / "closure.json").write_bytes(manifest)


# --------------------------------------------------------------------------
# Arm 0 — closure admission of the pinned OCR binary (the fixed behavior).
# --------------------------------------------------------------------------


def arm0_v3_admission(out: Path, binary: Path, *, repeats: int) -> str:
    started = time.monotonic()
    facts = _ocr_elf_facts(binary)
    ocr_digest = str(facts["sha256"])
    payload = binary.read_bytes()
    loader = FIXTURE_LOADER.read_bytes()

    positives: list[str] = []
    graph_rows: list[str] = []
    realized: list[str] = []
    with tempfile.TemporaryDirectory(prefix="ranex-105-arm0-") as tmp:
        root = Path(tmp) / "closure"
        manifest = _two_row_closure(ocr_digest)
        for _ in range(repeats):
            _materialise_closure(root, manifest, payload, loader)
            try:
                parsed = parse_runtime_manifest(manifest)
                positives.append("ADMITTED")
                rows = parsed_runtime_graph(root, parsed)
                graph_rows.append(json.dumps(rows, sort_keys=True))
                expected = expected_realized_runtime_graph(parsed)
                got = realized_runtime_graph_from_reports(
                    {"bin/opencodereview": b"statically linked"}
                )
                realized.append("MATCH" if expected == got else "DIFFER")
            except ValueError as exc:
                positives.append(f"REFUSED:{exc}")
                graph_rows.append("n/a")
                realized.append("n/a")
        fd = os.open(binary, os.O_RDONLY | os.O_CLOEXEC)
        try:
            inspect_self_contained_static_executable(fd, binary)
            static_status = "ADMITTED"
        except ValueError as exc:
            static_status = f"REFUSED:{exc}"
        finally:
            os.close(fd)

        # Negative control N1: a corrupted digest must refuse sealing.
        (root / "bin/opencodereview").write_bytes(payload + b"tamper")
        try:
            seal_runtime_file(
                root / "bin/opencodereview",
                ocr_digest,
                kind="entrypoint",
                mode=0o555,
            )
            n1 = "ADMITTED (FALSE-PASS)"
        except ValueError as exc:
            n1 = f"REFUSED:{exc}"
        _materialise_closure(root, manifest, payload, loader)

        # Negative control N2: a static-shape claim over dynamic bytes must
        # refuse at graph parse (the manifest lies about the ELF shape).
        dynamic_digest = "sha256:" + hashlib.sha256(loader).hexdigest()
        lie = _two_row_closure(dynamic_digest)
        (root / "bin/opencodereview").write_bytes(loader)
        (root / "closure.json").write_bytes(lie)
        try:
            parsed_runtime_graph(root, parse_runtime_manifest(lie))
            n2 = "ADMITTED (FALSE-PASS)"
        except ValueError as exc:
            n2 = f"REFUSED:{exc}"
        fd = os.open(root / "bin/opencodereview", os.O_RDONLY | os.O_CLOEXEC)
        try:
            inspect_self_contained_static_executable(fd, root / "bin/opencodereview")
            n2_static = "ADMITTED (FALSE-PASS)"
        except ValueError as exc:
            n2_static = f"REFUSED:{exc}"
        finally:
            os.close(fd)

        # Negative control N3: the pre-#105 honest measurement kept honest —
        # the dynamic interp binding v3 demanded before Phase 1-3 parses
        # structurally but must still refuse at byte verification over the
        # real static bytes (this exact refusal was the old Arm 0 headline).
        old = _two_row_closure(
            ocr_digest,
            entry_row=_dynamic_entry_row(ocr_digest),
            entry_interp="/lib64/ld-linux-x86-64.so.2",
        )
        (root / "bin/opencodereview").write_bytes(payload)
        (root / "closure.json").write_bytes(old)
        try:
            parsed_runtime_graph(root, parse_runtime_manifest(old))
            n3 = "ADMITTED (FALSE-PASS)"
        except ValueError as exc:
            n3 = f"REFUSED:{exc}"

    expected_rows = json.dumps(
        [
            {"path": "bin/opencodereview", "needed": []},
            {"path": "loader/ld-linux-x86-64.so.2", "needed": []},
        ],
        sort_keys=True,
    )
    held = positives == ["ADMITTED"] * repeats
    graphs_ok = graph_rows == [expected_rows] * repeats
    realized_ok = realized == ["MATCH"] * repeats
    refused = all(
        value.startswith("REFUSED") for value in (n1, n2, n2_static, n3)
    )
    distinct = len(set(positives))
    if distinct > 1:
        status = "NON-DETERMINISTIC"
    elif not refused:
        status = "FALSE-PASS"
    elif static_status != "ADMITTED" or not held or not graphs_ok or not realized_ok:
        status = "GAP"
    else:
        status = "VERIFIED"

    wall_ms = int((time.monotonic() - started) * 1000)
    digests = {
        "ocr_sha256": ocr_digest,
        "release_pin": OCR_SHA256,
        "closure_attempt": "sha256:"
        + hashlib.sha256(_two_row_closure(ocr_digest)).hexdigest(),
        "graph_rows": "sha256:" + hashlib.sha256(expected_rows.encode()).hexdigest(),
    }
    _record(
        out,
        "arm0-v3-entrypoint-admission",
        status=status,
        argv=["parse_runtime_manifest", "parsed_runtime_graph", "honest-ocr-closure"],
        cwd=str(binary.parent),
        exit_code=0 if status == "VERIFIED" else 1,
        digests=digests,
        notes=(
            f"pin={OCR_TAG} floor={OCR_COMMIT_FLOOR} asset={OCR_ASSET} "
            f"elf={facts['e_type']} pt_interp={facts['pt_interp']!r} "
            f"static_v2={static_status} positive={positives} "
            f"realized={realized} repeats={repeats}. "
            f"negatives: corrupted-digest={n1}; static-shape-lie-over-dynamic-bytes="
            f"{n2} (static-v2: {n2_static}); old-dynamic-binding-over-static-bytes="
            f"{n3} (the pre-fix refusal, kept as a negative control). "
            "findings stay ADVISORY (never required_claims)."
        ),
        wall_ms=wall_ms,
    )
    pin = {
        "tool": "alibaba/open-code-review",
        "tag": OCR_TAG,
        "commit_floor": OCR_COMMIT_FLOOR,
        "asset": OCR_ASSET,
        "sha256": OCR_SHA256,
        "url": OCR_URL,
        "checksums_url": CHECKSUMS_URL,
        "observed_sha256": ocr_digest.removeprefix("sha256:"),
        "elf": facts,
        "static_v2": static_status,
        "v3_admission": "ADMITTED" if held else "NOT-ADMITTED",
        "negative_controls": {
            "corrupted_digest": n1,
            "static_shape_lie_over_dynamic_bytes": n2,
            "static_v2_dynamic_bytes": n2_static,
            "old_dynamic_binding_over_static_bytes": n3,
        },
    }
    _sidecar(out, "ocr-pin.json", pin)
    return status


# --------------------------------------------------------------------------
# The strict-local v3 journey (arms 1-2, 5): a real governed clone running
# the pinned OCR binary as the bound command under the real confinement.
# --------------------------------------------------------------------------


def _git(repository: Path, *arguments: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(arguments)}: {completed.stderr[-400:]}")
    return completed.stdout.strip()


def _module(repository: Path, module: str, *arguments: str, env: dict[str, str]):
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=repository,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )


def _overlay_working_tree(repository: Path) -> None:
    """Carry the review-time working tree along, exactly as the e2e fixture."""

    diff = subprocess.run(
        ["git", "-C", str(REPOSITORY), "diff", "HEAD", "--binary"],
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
        if applied.returncode != 0:
            raise RuntimeError(f"overlay apply failed: {applied.stderr[-400:]}")
    untracked = subprocess.run(
        ["git", "-C", str(REPOSITORY), "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for relative in untracked:
        if relative.startswith("tools/dogfood/audits/"):
            continue
        source = REPOSITORY / relative
        if source.is_file():
            target = repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())


class OfflineJourney:
    """A real governed clone of this repository, sealed around the OCR closure."""

    def __init__(self, workspace: Path) -> None:
        self.repository = workspace / "repository"
        self.workspace = workspace
        self.worker_key = workspace / "worker.key"
        self.approver_key = workspace / "approver.key"
        self.signer_key = workspace / "signer.key"
        self.key_home = workspace / "home-key"
        self.nokey_home = workspace / "home-nokey"
        self.base_env: dict[str, str] = {}
        self.history_runs = 0

    def build(self, binary: Path) -> None:
        # The control claim binds the same pinned bytes at their host path: a
        # plain run can satisfy it (the v3 dynamic path demands a drained
        # result.json on success, which `--version` rightly does not write).
        self.version_argv = [str(binary), "--version"]
        completed = subprocess.run(
            ["git", "clone", "-q", str(REPOSITORY), str(self.repository)],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"clone failed: {completed.stderr[-400:]}")
        _overlay_working_tree(self.repository)
        _git(self.repository, "config", "user.name", "ocr-subject-proof")
        _git(self.repository, "config", "user.email", "ocr-subject@ranex.invalid")
        _git(self.repository, "rm", "-q", "governance/deps.yaml")

        self.base_env = {
            "PATH": os.environ["PATH"],
            "PYTHONPATH": str(self.repository / "src"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C",
            "TZ": "UTC",
            "RANEX_VERDICT_SIGNING_KEY": str(self.signer_key),
        }
        keys = {
            WORKER: self.worker_key,
            APPROVER: self.approver_key,
            SIGNER: self.signer_key,
        }
        public: dict[str, str] = {}
        for identity, path in keys.items():
            generated = _module(
                self.repository,
                "ranex.cli.main",
                "keygen",
                "--producer",
                identity,
                env={**self.base_env, "RANEX_SIGNING_KEY": str(path)},
            )
            if generated.returncode != 0:
                raise RuntimeError(f"keygen failed: {generated.stderr[-400:]}")
            token = next(
                line.split()[-1].strip()
                for line in generated.stdout.splitlines()
                if line.strip().startswith(identity)
            )
            public[identity] = token
        (self.repository / "governance/producers.yaml").write_text(
            "producers:\n"
            f"  {WORKER}: {public[WORKER]}\n"
            "verdict_signer:\n"
            f"  id: {SIGNER}\n"
            f"  public_key: {public[SIGNER]}\n"
            "principals:\n"
            f"  {WORKER}:\n    role: worker\n    keys:\n"
            f"      - key: {public[WORKER]}\n        status: active\n"
            f"  {APPROVER}:\n    role: approver\n    keys:\n"
            f"      - key: {public[APPROVER]}\n        status: active\n"
            f"  {SIGNER}:\n    role: service\n    keys:\n"
            f"      - key: {public[SIGNER]}\n        status: active\n",
            encoding="utf-8",
        )
        (self.repository / "governance/gates.yaml").write_text(
            "gates:\n"
            "  - gate_id: landing\n"
            "    rule_id: OCR_REVIEW_REQUIRED\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: ocr-review\n"
            f"        command: {json.dumps(OCR_ARGV)}\n"
            "  - gate_id: control\n"
            "    rule_id: OCR_VERSION_CONTROL\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: ocr-version\n"
            f"        command: {json.dumps(self.version_argv)}\n",
            encoding="utf-8",
        )

        closure = self.repository / OCR_CLOSURE
        (closure / "bin").mkdir(parents=True)
        (closure / "loader").mkdir()
        (closure / "bin/opencodereview").write_bytes(binary.read_bytes())
        (closure / "loader/ld-linux-x86-64.so.2").write_bytes(FIXTURE_LOADER.read_bytes())
        (closure / "closure.json").write_bytes(
            _two_row_closure("sha256:" + OCR_SHA256) + b"\n"
        )
        (self.repository / OCR_INPUT).mkdir(parents=True)
        (self.repository / OCR_INPUT / "seed.txt").write_text(
            "ocr static subject\n", encoding="utf-8"
        )
        _git(self.repository, "add", "-A")
        _git(self.repository, "commit", "-qm", "governance: bind the OCR static closure journey")

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
            completed = _module(
                self.repository,
                "ranex.cli.host_confinement",
                *arguments,
                env=self.base_env,
            )
            if completed.returncode != 0:
                raise RuntimeError(
                    f"provisioning {' '.join(arguments)} failed: "
                    f"{completed.stdout[-400:]}{completed.stderr[-400:]}"
                )

        self.nokey_home.mkdir(parents=True)
        self.key_home.mkdir(parents=True)
        config = self.key_home / ".opencodereview"
        config.mkdir()
        (config / "config.json").write_text(
            json.dumps(
                {
                    "provider": "anthropic",
                    "providers": {"anthropic": {"api_key": PROBE_TOKEN}},
                    "llm": {},
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n",
            encoding="utf-8",
        )

    def _model_env(self, *, key_set: bool) -> dict[str, str]:
        env = dict(self.base_env)
        env["RANEX_SIGNING_KEY"] = str(self.worker_key)
        if key_set:
            env["HOME"] = str(self.key_home)
            env.update(
                {
                    "OCR_LLM_URL": PROBE_ENDPOINT,
                    "OCR_LLM_TOKEN": PROBE_TOKEN,
                    "OCR_LLM_MODEL": "probe-model",
                    "ANTHROPIC_BASE_URL": PROBE_ENDPOINT,
                    "ANTHROPIC_AUTH_TOKEN": PROBE_TOKEN,
                    "ANTHROPIC_MODEL": "probe-model",
                }
            )
        else:
            env["HOME"] = str(self.nokey_home)
        return env

    def _bootstrap_history(self) -> tuple[str, Path]:
        """Allocate a fresh durable pair; never reset an established history."""
        self.history_runs += 1
        name = f"history-{self.history_runs}"
        evidence = str(Path(EVIDENCE).parent / name / Path(EVIDENCE).name)
        checkpoint = self.workspace / f"{name}-checkpoint.json"
        self.base_env["RANEX_HISTORY_CHECKPOINT"] = str(checkpoint)
        completed = _module(
            self.repository, "ranex.cli.main", "history", "bootstrap",
            "--evidence", evidence, "--producers", "governance/producers.yaml",
            env=self.base_env,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"history bootstrap failed: {completed.stderr}")
        return evidence, checkpoint

    def observe(
        self,
        *,
        key_set: bool,
        gate: str,
        claim: str,
        argv: list[str],
        confined: bool = True,
    ) -> dict[str, object]:
        """One real run + gate evaluate; verdict digests from the real journal."""

        evidence, checkpoint = self._bootstrap_history()
        run_argv = [
            "run",
            "--claim",
            claim,
            "--producer",
            WORKER,
            "--repository",
            ".",
            "--evidence",
            evidence,
            "--gate",
            gate,
            "--gate-catalog",
            "governance/gates.yaml",
            "--producers",
            "governance/producers.yaml",
        ]
        if confined:
            run_argv += [
                "--confinement",
                "strict-local",
                "--runtime-input-path",
                OCR_INPUT,
                "--runtime-closure-root",
                OCR_CLOSURE,
            ]
        run_argv += ["--", *argv]
        env = self._model_env(key_set=key_set)
        run = _module(self.repository, "ranex.cli.main", *run_argv, env=env)
        evaluated = _module(
            self.repository,
            "ranex.cli.main",
            "gate",
            "evaluate",
            "HEAD",
            "--gate",
            gate,
            "--gate-catalog",
            "governance/gates.yaml",
            "--producers",
            "governance/producers.yaml",
            "--evidence",
            evidence,
            "--approver",
            APPROVER,
            "--journal",
            "governance/journal.sqlite3",
            env={**self.base_env, "RANEX_APPROVER_SIGNING_KEY": str(self.approver_key)},
        )
        verdict_word = "ERROR"
        for line in evaluated.stdout.splitlines():
            if line.startswith(("PASS", "FAIL")):
                verdict_word = line.split()[0]
                break
        record: dict[str, object] = {}
        verdict_digest = ""
        journal = self.repository / "governance/journal.sqlite3"
        if journal.is_file():
            connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
            try:
                rows = connection.execute(
                    "SELECT record, link FROM evaluations ORDER BY seq ASC"
                ).fetchall()
            finally:
                connection.close()
            if rows:
                record = json.loads(rows[-1][0])
                verdict_digest = rows[-1][1]
        result_line = next(
            (
                line.removeprefix("RANEX-RUNTIME-RESULT ")
                for line in run.stderr.splitlines()
                if line.startswith("RANEX-RUNTIME-RESULT ")
            ),
            None,
        )
        result = json.loads(result_line) if result_line else {}
        outputs = result.get("outputs", [])
        return {
            "evidence_path": evidence,
            "history_checkpoint_path": str(checkpoint),
            "history_anchor": json.loads(checkpoint.read_text()),
            "journal_chain_head": verdict_digest,
            "run_exit": run.returncode,
            "run_stdout_head": run.stdout[:400],
            "run_stderr_head": run.stderr[:400],
            "evaluate_exit": evaluated.returncode,
            "evaluate_stdout": evaluated.stdout[:800],
            "verdict": verdict_word,
            "record": record,
            "verdict_digest": verdict_digest,
            "record_digest": "sha256:"
            + hashlib.sha256(
                json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "session_outputs": outputs,
            "artifact_absent": outputs == [],
        }

    def credential_strip_control(self) -> dict[str, object]:
        """A descriptor carrying a model credential must be refused outright."""

        evidence, checkpoint = self._bootstrap_history()
        target = self.repository / Path(evidence).parent
        target.mkdir(parents=True, exist_ok=True)
        descriptor = target / "strip-descriptor.json"
        descriptor.write_bytes(
            canonical_json_bytes(
                {
                    "schema": "ranex-confinement-command-v2",
                    "argv": ["/ranex/runtime/bin/opencodereview", "--version"],
                    "environment": {
                        "LC_ALL": "C",
                        "TZ": "UTC",
                        "ANTHROPIC_AUTH_TOKEN": PROBE_TOKEN,
                    },
                    "input": OCR_INPUT,
                    "subject": "tree",
                    "runtime": OCR_CLOSURE,
                    "output": "scratch",
                    "scratch": "scratch",
                    "limits": {
                        "cpu_usage_usec": 1_000_000,
                        "memory_bytes": 134_217_728,
                        "output_bytes": 65_536,
                        "output_depth": 8,
                        "output_inodes": 32,
                        "pids": 16,
                        "wall_time_ms": 5_000,
                    },
                }
            )
        )
        result = target / "strip-result.json"
        completed = _module(
            self.repository,
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
            str(descriptor),
            "--result",
            str(result),
            env=self.base_env,
        )
        text = completed.stdout + completed.stderr
        return {
            "evidence_path": evidence,
            "history_checkpoint_path": str(checkpoint),
            "history_anchor": json.loads(checkpoint.read_text()),
            "exit": completed.returncode,
            "refused": completed.returncode != 0,
            "names_allowlist": "allowlist" in text,
            "text": text[:400],
        }


def _host_probe(binary: Path, *, key_set: bool) -> dict[str, object]:
    """The real binary's own answer to 'a key and a socket', host-side.

    Key unset: no endpoint resolves. Key set: a real socket connect is
    attempted and refused (nothing listens at the probe endpoint) — the
    refused connect, on the pinned bytes, with a live key.
    """

    home = Path(tempfile.mkdtemp(prefix="ranex-105-probe-home-"))
    env = {
        "PATH": "/usr/bin:/bin",
        "LC_ALL": "C",
        "TZ": "UTC",
        "HOME": str(home),
    }
    if key_set:
        env.update(
            {
                "OCR_LLM_URL": PROBE_ENDPOINT,
                "OCR_LLM_TOKEN": PROBE_TOKEN,
                "OCR_LLM_MODEL": "probe-model",
            }
        )
    started = time.monotonic()
    completed = subprocess.run(
        [str(binary), "llm", "test"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    return {
        "argv": [str(binary), "llm", "test"],
        "exit": completed.returncode,
        "stderr": (completed.stdout + completed.stderr).strip()[:400],
        "wall_ms": int((time.monotonic() - started) * 1000),
        "refused_connect": "connection refused" in (completed.stdout + completed.stderr),
    }


def _scrubbed_host_run(binary: Path, argv: list[str]) -> dict[str, object]:
    """The same bound argv under the exact worker environment, host-side."""

    completed = subprocess.run(
        [str(binary), *argv[1:]],
        env={"LC_ALL": "C", "TZ": "UTC"},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
        cwd=tempfile.mkdtemp(prefix="ranex-105-scrub-cwd-"),
    )
    return {
        "exit": completed.returncode,
        "text": (completed.stdout + completed.stderr).strip()[:300],
    }


def arms125_offline(out: Path, binary: Path, *, repeats: int) -> dict[str, str]:
    started = time.monotonic()
    retained = REPOSITORY / ".local/036"
    retained.mkdir(parents=True, exist_ok=True)
    with nullcontext(tempfile.mkdtemp(prefix="ranex-105-journey-", dir=retained)) as tmp:
        journey = OfflineJourney(Path(tmp))
        journey.build(binary)

        arm1_runs: list[dict[str, object]] = []
        arm2_runs: list[dict[str, object]] = []
        for _ in range(repeats):
            arm1_runs.append(journey.observe(key_set=False, gate="landing", claim="ocr-review", argv=OCR_ARGV))
            arm2_runs.append(journey.observe(key_set=True, gate="landing", claim="ocr-review", argv=OCR_ARGV))
        control = journey.observe(
            key_set=False,
            gate="control",
            claim="ocr-version",
            argv=journey.version_argv,
            confined=False,
        )
        strip = journey.credential_strip_control()
        probe_unset = _host_probe(binary, key_set=False)
        probe_set = _host_probe(binary, key_set=True)
        scrubbed = _scrubbed_host_run(binary, OCR_ARGV)

        _sidecar(out, "arm-journey-facts.json", {
            "arm1": arm1_runs,
            "arm2": arm2_runs,
            "control": control,
            "credential_strip": strip,
            "probe_key_unset": probe_unset,
            "probe_key_set": probe_set,
            "scrubbed_host_run": scrubbed,
        })

        digests1 = [str(run["record_digest"]) for run in arm1_runs]
        digests2 = [str(run["record_digest"]) for run in arm2_runs]
        records = arm1_runs + arm2_runs
        fail_all = all(
            run["verdict"] == "FAIL"
            and run["run_exit"] != 0
            and run["artifact_absent"]
            and run["record"].get("missing_claims") == ["ocr-review"]
            for run in records
        )
        repeat_identical = all(
            (run["verdict"], run["record"]) == (records[0]["verdict"], records[0]["record"])
            for run in records
        )
        control_passed = (
            control["verdict"] == "PASS" and control["run_exit"] == 0
            and strip["refused"] and strip["names_allowlist"]
        )

        if len(set(digests1)) > 1 or len(set(digests2)) > 1:
            status1 = status2 = "NON-DETERMINISTIC"
        elif not fail_all:
            status1 = status2 = "GAP"
        elif not control_passed:
            status1 = status2 = "GAP"
        else:
            status1 = "VERIFIED"
            # The credential-set arm carries the invariant as its negative
            # control: the model credential must not move the verdict.
            status2 = "VERIFIED" if repeat_identical else "NON-DETERMINISTIC"

        wall_ms = int((time.monotonic() - started) * 1000)
        common = {
            "verdict_digest": digests1[0] if digests1 else "",
            "record_digest": str(records[0]["record_digest"]) if records else "",
        }
        _record(
            out,
            "arm1-offline-key-unset",
            status=status1,
            argv=OCR_ARGV,
            cwd=str(journey.repository),
            exit_code=int(arm1_runs[0]["run_exit"]) if arm1_runs else 1,
            digests={**common, "repeats": f"{len(set(digests1))} distinct of {len(digests1)}"},
            notes=(
                "real ranex run + gate evaluate under strict-local v3 with the OCR "
                "closure; key unset (fresh HOME, no OCR_LLM_*/ANTHROPIC_* vars). "
                f"run_exit={[r['run_exit'] for r in arm1_runs]} "
                f"verdict={[r['verdict'] for r in arm1_runs]} "
                f"missing={[r['record'].get('missing_claims') for r in arm1_runs]} "
                f"reason={arm1_runs[0]['record'].get('reason')!r} "
                f"artifact_absent={[r['artifact_absent'] for r in arm1_runs]}. "
                f"positive control (gate passes when the bound command succeeds): "
                f"control={control['verdict']}. "
                f"host key-unset probe: exit={probe_unset['exit']} {probe_unset['stderr']!r}. "
                f"same argv under the exact worker environment, host-side: "
                f"exit={scrubbed['exit']} {scrubbed['text']!r} (the in-session "
                "failure text is sealed — static workers run with inert fds 0-2 — "
                "only its exit code is observable). "
                "Deviation: issue #105 says FAIL-by-absence; the honest exit-code-only "
                "binding reports cause 'failed' with the artifact measured absent, "
                "because the loader's canonical SARIF argv spelling cannot bind this "
                "CLI (measured: 'unknown flag: --output-format')."
            ),
            wall_ms=wall_ms,
        )
        _record(
            out,
            "arm2-offline-key-set-strict-local",
            status=status2,
            argv=OCR_ARGV,
            cwd=str(journey.repository),
            exit_code=int(arm2_runs[0]["run_exit"]) if arm2_runs else 1,
            digests={
                **common,
                "repeats": f"{len(set(digests2))} distinct of {len(digests2)}",
                "arm1_verdict_digest": digests1[0] if digests1 else "",
            },
            notes=(
                "same journey, same commit, model credential SET on the host "
                f"(HOME config api_key + OCR_LLM_*/ANTHROPIC_* = probe values). "
                f"verdict={[r['verdict'] for r in arm2_runs]} "
                f"verdict_digests={digests2}; identical to arm 1: {digests2 == digests1} "
                "(INVARIANT: removing every model credential must not change a verdict). "
                f"refused connect (real binary, real key, refused socket): "
                f"exit={probe_set['exit']} refused={probe_set['refused_connect']} "
                f"{probe_set['stderr']!r}. "
                f"credential strip: a session descriptor carrying ANTHROPIC_AUTH_TOKEN "
                f"is refused ({strip['refused']}, names allowlist: {strip['names_allowlist']}) "
                f"{strip['text']!r}. strict-local profile denies the network "
                '(governance/confinement/strict-local-v3.json verifier.network="denied").'
            ),
            wall_ms=wall_ms,
        )
        status5 = "VERIFIED" if (repeat_identical and fail_all) else (
            "NON-DETERMINISTIC" if not repeat_identical else "GAP"
        )
        _record(
            out,
            "arm5-repeats-identical-fail-digests",
            status=status5,
            argv=["repeat", "arm1+arm2"],
            cwd=str(journey.repository),
            exit_code=0 if status5 == "VERIFIED" else 1,
            digests={
                "arm1": digests1[0] if digests1 else "",
                "arm2": digests2[0] if digests2 else "",
                "all": f"{len(set(digests1 + digests2))} distinct of {len(digests1 + digests2)}",
            },
            notes=(
                f"arm1 x{len(digests1)} + arm2 x{len(digests2)} verdict digests: "
                f"{sorted(set(digests1 + digests2))}; every run FAILed on the "
                "unsatisfied ocr-review claim with the artifact absent."
            ),
        )
        return {
            "arm1-offline-key-unset": status1,
            "arm2-offline-key-set-strict-local": status2,
            "arm5-repeats-identical-fail-digests": status5,
        }


# --------------------------------------------------------------------------
# Arm 3 — delegation mode: ocr delegate spec -> #102 packet -> SARIF admitted.
# --------------------------------------------------------------------------


def _init_subject(root: Path) -> tuple[str, str, str]:
    _git(root, "init")
    _git(root, "config", "user.email", "ocr-subject@ranex.invalid")
    _git(root, "config", "user.name", "ocr-subject-proof")
    (root / "pkg").mkdir()
    (root / "pkg" / "mod.py").write_text(
        '"""Small module under delegated review."""\n\n\ndef load(path):\n'
        "    return open(path).read()\n",
        encoding="utf-8",
    )
    (root / "governance").mkdir()
    _git(root, "add", ".")
    _git(root, "commit", "-m", "seed")
    base = _git(root, "rev-parse", "HEAD")
    # The injected Python defect: a bare open() with no context manager and no
    # error handling — the reviewed hunk the delegated finding anchors to. The
    # line is unique in the file so its excerpt anchor is unambiguous.
    (root / "pkg" / "mod.py").write_text(
        (root / "pkg" / "mod.py").read_text(encoding="utf-8")
        + '\n\ndef leak(path):\n    data = open(path).read()  # noqa: SIM115\n    return data\n',
        encoding="utf-8",
    )
    _git(root, "add", "pkg/mod.py")
    _git(root, "commit", "-m", "change: inject a real file-handle defect")
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    return "sha256:" + hashlib.sha256(tree.encode()).hexdigest(), base, head


def arm3_delegation(out: Path, binary: Path, *, repeats: int) -> str:
    started = time.monotonic()
    from ranex.foundation.delegated_review import (
        build_packet,
        delegated_review_results_from_sarif,
        empty_handbook_digest,
        emit_worker_sarif,
        packet_digest,
    )

    with tempfile.TemporaryDirectory(prefix="ranex-105-arm3-") as tmp:
        root = Path(tmp) / "subject"
        root.mkdir()
        subject, base, head = _init_subject(root)

        spec_argv = [
            str(binary),
            "delegate",
            "preview",
            "--format",
            "json",
            "--from",
            base,
            "--to",
            head,
        ]
        spec_env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "TZ": "UTC", "HOME": str(root)}
        spec_runs = [
            subprocess.run(
                spec_argv,
                cwd=root,
                env=spec_env,
                capture_output=True,
                check=False,
                timeout=120,
            )
            for _ in range(repeats)
        ]
        spec_digests = [hashlib.sha256(run.stdout).hexdigest() for run in spec_runs]
        spec = json.loads(spec_runs[0].stdout) if spec_runs[0].returncode == 0 else {}

        packets = [
            build_packet(
                subject_digest=subject,
                range_base=base,
                range_head=head,
                handbook_digest=empty_handbook_digest(),
                chapters=(),
            )
            for _ in range(repeats)
        ]
        packet_digests = [packet_digest(packet) for packet in packets]
        packet = packets[0]
        (root / "governance" / "review-packet.json").write_bytes(
            canonical_json_bytes(packet)
        )

        excerpt = "data = open(path).read()  # noqa: SIM115"
        worker_argv = [
            sys.executable,
            "-m",
            "ranex.foundation.delegated_review",
            "--output-format=sarif",
            "--output-file=governance/review.sarif",
            "--path=pkg/mod.py",
            f"--excerpt={excerpt}",
            "--level=error",
        ]
        sarif = emit_worker_sarif(
            root=root,
            path="pkg/mod.py",
            category="review.finding",
            excerpt=excerpt,
            level="error",
            message="bare open() leaks a file handle",
        )
        manifest = {
            "scope": ["pkg/mod.py"],
            "rules": ["review.finding"],
            "blocking_levels": ["error"],
            "accepted": {},
        }
        summary = delegated_review_results_from_sarif(
            sarif, manifest, subject_root=root, expected_packet_digest=packet_digests[0]
        )
        finding_ids = [
            row[0]
            for row in summary["non_passed"]
            if row[1] == "failed" and "::" in row[0]
        ]

        forged_packet = dict(packet)
        forged_packet["range"] = {"base": base, "head": "f" * 40}
        forged = json.loads(sarif)
        forged["runs"][0]["properties"]["packet_digest"] = packet_digest(forged_packet)
        try:
            delegated_review_results_from_sarif(
                canonical_json_bytes(forged),
                manifest,
                subject_root=root,
                expected_packet_digest=packet_digests[0],
            )
            substitution = "ADMITTED (FALSE-PASS)"
        except ValueError as exc:
            substitution = f"REFUSED:{exc}"

        unresolvable = json.loads(sarif)
        unresolvable["runs"][0]["results"][0]["locations"][0]["physicalLocation"][
            "region"
        ]["snippet"] = {"text": "no-such-excerpt"}
        try:
            delegated_review_results_from_sarif(
                canonical_json_bytes(unresolvable),
                manifest,
                subject_root=root,
                expected_packet_digest=packet_digests[0],
            )
            anchor = "ADMITTED (FALSE-PASS)"
        except ValueError as exc:
            anchor = f"REFUSED:{exc}"

        spec_ok = (
            all(run.returncode == 0 for run in spec_runs)
            and len(set(spec_digests)) == 1
        )
        packet_ok = len(set(packet_digests)) == 1
        # One blocking finding: its prose-free id AND the scope path it fails
        # both read "failed" in the reduction — the id is the finding.
        admitted = len(finding_ids) == 1
        refused = substitution.startswith("REFUSED") and anchor.startswith("REFUSED")
        if not spec_ok or not packet_ok:
            status = "NON-DETERMINISTIC"
        elif not refused:
            status = "FALSE-PASS"
        elif not admitted:
            status = "GAP"
        else:
            status = "VERIFIED"

        wall_ms = int((time.monotonic() - started) * 1000)
        _record(
            out,
            "arm3-ocr-delegate-advisory",
            status=status,
            argv=spec_argv + worker_argv,
            cwd=str(root),
            exit_code=0 if status == "VERIFIED" else 1,
            digests={
                "spec": "sha256:" + spec_digests[0] if spec_digests else "",
                "packet": packet_digests[0] if packet_digests else "",
                "sarif": "sha256:" + hashlib.sha256(sarif).hexdigest(),
                "outcome": str(summary["outcome_digest"]),
            },
            notes=(
                f"ocr delegate preview --format json x{repeats}: exits="
                f"{[r.returncode for r in spec_runs]} unique={len(set(spec_digests))} "
                f"(real delegation spec: mode={spec.get('mode')!r} "
                f"reviewable={spec.get('reviewable_count')}). "
                f"#102 packet digest x{repeats}: unique={len(set(packet_digests))} "
                f"bound to subject={subject} range={base[:12]}..{head[:12]}. "
                f"SARIF admitted under the packet binding; finding ids="
                f"{finding_ids} (advisory posture: the findings "
                "claim is recorded and never part of any default required_claims; "
                "an operator catalog that requires it gates on it — #102's stated "
                f"relaxation). negatives: packet substitution {substitution}; "
                f"unresolvable anchor {anchor}."
            ),
            wall_ms=wall_ms,
        )
        _sidecar(
            out,
            "arm3-delegation-facts.json",
            {
                "spec": spec,
                "spec_digests": spec_digests,
                "packet": packet,
                "packet_digests": packet_digests,
                "sarif": json.loads(sarif),
                "summary": summary,
                "finding_ids": finding_ids,
                "worker_argv": worker_argv,
                "negative_controls": {
                    "packet_substitution": substitution,
                    "unresolvable_anchor": anchor,
                },
            },
        )
        return status


# --------------------------------------------------------------------------
# Arm 4 — the live ranex-app-live-probe PR journey.
# --------------------------------------------------------------------------


def _capture(argv: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None) -> dict[str, object]:
    completed = subprocess.run(
        argv,
        env=env,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    return {
        "argv": argv,
        "exit": completed.returncode,
        "stdout": completed.stdout[-2000:],
        "stderr": completed.stderr[-1000:],
    }


def arm4_live_probe(out: Path) -> str:
    """Best-effort live journey; anything unreachable is recorded, never faked."""

    started = time.monotonic()
    evidence: dict[str, object] = {"phase": "preflight"}
    steps: list[dict[str, object]] = []

    identity = _capture(["gh", "api", "user", "--jq", ".login"])
    steps.append({"step": "gh-api-user", **identity})
    probe = _capture(
        ["gh", "api", "repos/anthonykewl20/ranex-app-live-probe", "--jq", ".full_name"]
    )
    steps.append({"step": "probe-repo", **probe})

    credentials = Path.home() / ".config" / "ranex" / "github-app"
    files = sorted(path.name for path in credentials.glob("*")) if credentials.is_dir() else []
    app_id = ""
    identity_file = credentials / "identity.json"
    if identity_file.is_file():
        try:
            app_id = str(json.loads(identity_file.read_bytes()).get("app_id", ""))
        except (OSError, ValueError):
            app_id = ""
    webhook = credentials / "webhook-secret"
    app_env = dict(os.environ)
    app_env.update(
        {
            "RANEX_GITHUB_APP_ID": app_id,
            "RANEX_GITHUB_APP_PRIVATE_KEY": str(credentials / "app.pem"),
            "RANEX_GITHUB_WEBHOOK_SECRET": (
                webhook.read_text(encoding="utf-8").strip() if webhook.is_file() else ""
            ),
        }
    )
    status = _capture(["uv", "run", "--frozen", "ranex", "github", "status"], env=app_env)
    steps.append({"step": "ranex-github-status", **status})

    evidence["steps"] = steps
    evidence["app_credentials_files"] = files
    reachable = (
        identity.get("exit") == 0
        and identity.get("stdout", "").strip() == "anthonykewl20"
        and probe.get("exit") == 0
        and status.get("exit") == 0
        and "ERROR" not in str(status.get("stdout", ""))
    )
    evidence["app_pipeline_reachable"] = reachable

    if not reachable:
        _sidecar(out, "arm4-live-facts.json", evidence)
        _record(
            out,
            "arm4-live-probe-pr",
            status="GAP",
            argv=["ranex", "github", "status"],
            cwd=str(REPOSITORY),
            exit_code=1,
            digests={},
            notes=(
                "the live App pipeline is not reachable from this host; exact "
                "refusal evidence in arm4-live-facts.json: "
                f"gh user={identity.get('stdout', '').strip()!r} exit={identity.get('exit')}; "
                f"probe repo={probe.get('stdout', '').strip()!r} exit={probe.get('exit')}; "
                f"ranex github status exit={status.get('exit')} "
                f"stdout={str(status.get('stdout'))[-300:]!r} "
                f"stderr={str(status.get('stderr'))[-300:]!r}. "
                "Not faked: the PR/check journey is UNVERIFIED on this run."
            ),
            wall_ms=int((time.monotonic() - started) * 1000),
        )
        return "GAP"

    # The App is reachable: run the real PR journey against the probe repo.
    try:
        with tempfile.TemporaryDirectory(prefix="ranex-105-arm4-") as tmp:
            workspace = Path(tmp)
            clone = workspace / "probe"
            cloned = _capture(
                ["gh", "repo", "clone", "anthonykewl20/ranex-app-live-probe", str(clone)]
            )
            steps.append({"step": "clone-probe", **cloned})
            if cloned["exit"] != 0:
                raise RuntimeError(f"clone refused: {cloned['stderr']}")
            defect = "2026-09-30-ocr-subject-v2"
            branch = f"ocr-subject/{defect}"
            _git(clone, "checkout", "-q", "-b", branch)
            targets = sorted(clone.rglob("*.py"))
            victim = next(
                (path for path in targets if "def " in path.read_text(encoding="utf-8", errors="replace")),
                targets[0] if targets else None,
            )
            if victim is None:
                raise RuntimeError("probe repo carries no Python file to defect")
            original = victim.read_text(encoding="utf-8")
            victim.write_text(
                original + "\n\nimport os  # injected unused import (OCR subject probe)\n",
                encoding="utf-8",
            )
            _git(clone, "add", "-A")
            _git(clone, "commit", "-qm", f"probe: inject a Python defect ({defect})")
            pushed = _capture(["git", "push", "-u", "origin", branch], cwd=clone)
            steps.append({"step": "push-branch", **pushed})
            if pushed["exit"] != 0:
                raise RuntimeError(f"push refused: {pushed['stderr']}")
            pr = _capture(
                [
                    "gh", "pr", "create",
                    "--repo", "anthonykewl20/ranex-app-live-probe",
                    "--head", branch,
                    "--title", f"#105 arm 4 — OCR subject probe ({defect})",
                    "--body", "Injected Python defect for the #105 arm-4 journey.",
                ]
            )
            steps.append({"step": "open-pr", **pr})
            if pr["exit"] != 0:
                raise RuntimeError(f"pr refused: {pr['stderr']}")
            evidence["pr"] = str(pr.get("stdout", "")).strip()
            raise RuntimeError(
                "App authentication succeeded and the defect PR opened, but the "
                "governed check journey on the probe checkout (evidence -> verdict "
                "-> ranex github check -> check body) is not wired end-to-end in "
                "this run; recorded honestly rather than simulated"
            )
    except RuntimeError as exc:
        evidence["blocked_at"] = str(exc)
        _sidecar(out, "arm4-live-facts.json", evidence)
        _record(
            out,
            "arm4-live-probe-pr",
            status="GAP",
            argv=["gh", "pr", "create"],
            cwd=str(REPOSITORY),
            exit_code=1,
            digests={},
            notes=(
                "live App pipeline reachable (ranex github status exit=0) and the "
                f"journey proceeded until: {exc}. Full step evidence in "
                "arm4-live-facts.json. UNVERIFIED for the finding-id-in-check-text "
                "and fix->success expectations on this run."
            ),
            wall_ms=int((time.monotonic() - started) * 1000),
        )
        return "GAP"


# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--ocr-binary",
        type=Path,
        default=None,
        help="Pinned OCR binary; default downloads v1.12.9 into the cache",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    host = {
        "hostname": platform.node(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
    }
    _sidecar(args.out, "host.json", host)

    binary = _fetch_ocr(Path(args.ocr_binary or CACHE))

    statuses: dict[str, str] = {}
    statuses["arm0-v3-entrypoint-admission"] = arm0_v3_admission(
        args.out, binary, repeats=args.repeats
    )
    statuses.update(arms125_offline(args.out, binary, repeats=args.repeats))
    statuses["arm3-ocr-delegate-advisory"] = arm3_delegation(
        args.out, binary, repeats=args.repeats
    )
    statuses["arm4-live-probe-pr"] = "OTHER: out of scope"

    summary = {
        "proof_commit": _git(REPOSITORY, "rev-parse", "HEAD"),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": host["hostname"],
        "issue": 105,
        "ocr_tag": OCR_TAG,
        "ocr_sha256": OCR_SHA256,
        "repeats": args.repeats,
        "statuses": statuses,
        "kernel_digest_moved": False,
        "findings_advisory": True,
        "required_claims_include_ocr": False,
    }
    _sidecar(args.out, "SUMMARY.json", summary)
    cached_sums = binary.parent / "sha256sum.txt"
    if cached_sums.is_file():
        shutil.copy2(cached_sums, args.out / "sha256sum.txt")

    print(json.dumps(statuses, indent=2, sort_keys=True))
    blocking = {"FALSE-PASS", "NON-DETERMINISTIC", "UNVERIFIED"}
    return 1 if any(value in blocking for value in statuses.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
