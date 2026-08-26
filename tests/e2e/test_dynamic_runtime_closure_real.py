"""Frozen RED public journey for ADR-035's sealed dynamic runtime.

The test invokes Ranex's public launcher build/install/qualify/run surfaces and
independently reads the emitted result-v2 and signed evidence. The governed
worker's expected output is frozen separately; no implementation helper reports
booleans to this test.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.cli.main import admitted_evidence
from ranex.foundation.canonical import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "governance/confinement/strict-local-v3.json"
HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
LAUNCHER_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
LAUNCHER_SOURCE = "native/ranex-worker-launcher/launcher.c"
BUILD_OUTPUT = ".local/ranex/build/strict-local-v1/ranex-worker-launcher"
INSTALLED_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
QUALIFICATION = ".local/ranex/qualification/strict-local-v1.json"
RUNTIME = "tests/e2e/fixtures/slice072-runtime"
INPUT = "tests/e2e/fixtures/slice072-input"
EXPECTED = ROOT / "tests/e2e/expected/slice072-result.json"
RESULT_PREFIX = "RANEX-RUNTIME-RESULT "
OUTPUT_PREFIX = "RANEX-RUNTIME-OUTPUT "
PRODUCER = "slice072-owner"


@dataclass(frozen=True)
class Journey:
    repository: Path
    key: Path


def _env(repository: Path, key: Path | None = None) -> dict[str, str]:
    value = {
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(repository / "src"),
        "LC_ALL": "C",
        "TZ": "UTC",
    }
    if key is not None:
        value["RANEX_SIGNING_KEY"] = str(key)
    return value


def _module(repository: Path, module: str, *arguments: str, key: Path | None = None):
    return subprocess.run(
        [sys.executable, "-m", module, *arguments],
        cwd=repository,
        env=_env(repository, key),
        capture_output=True,
        text=True,
        check=False,
    )


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _clone(repository: Path) -> None:
    completed = subprocess.run(
        ["git", "clone", "-q", str(ROOT), str(repository)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    _git(repository, "config", "user.name", "Ranex E2E")
    _git(repository, "config", "user.email", "ranex-e2e@example.invalid")


def _register_owner(repository: Path, key: Path) -> None:
    generated = _module(
        repository,
        "ranex.cli.main",
        "keygen",
        "--producer",
        PRODUCER,
        key=key,
    )
    assert generated.returncode == 0, generated.stderr
    public = re.search(r"ed25519:[A-Za-z0-9+/=]+", generated.stdout)
    assert public is not None
    producers = repository / "governance/producers.yaml"
    lines = producers.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next(
        index for index, line in enumerate(lines) if line.rstrip() == "producers:"
    )
    lines.insert(header + 1, f"  {PRODUCER}: {public.group(0)}\n")
    producers.write_text("".join(lines), encoding="utf-8")
    _git(repository, "rm", "-q", "governance/deps.yaml")
    _git(repository, "add", "governance/producers.yaml")
    _git(repository, "commit", "-qm", "test: register slice072 fixture owner")


@pytest.fixture(scope="module")
def journey(
    tmp_path_factory: pytest.TempPathFactory,
    prereq_qualified_host: None,
) -> Journey:
    repository = tmp_path_factory.mktemp("slice072") / "repository"
    key = repository.parent / "owner.key"
    _clone(repository)
    _register_owner(repository, key)
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
    assert _git(repository, "status", "--porcelain", "--untracked-files=all") == ""
    return Journey(repository, key)


def _run(journey: Journey, evidence: str):
    return _module(
        journey.repository,
        "ranex.cli.main",
        "run",
        "--claim",
        "dynamic-runtime-qualified",
        "--producer",
        PRODUCER,
        "--repository",
        ".",
        "--evidence",
        evidence,
        "--confinement",
        "strict-local",
        "--runtime-input-path",
        INPUT,
        "--runtime-closure-root",
        RUNTIME,
        "--",
        "/ranex/runtime/bin/python3.12",
        "/ranex/runtime/data/worker.py",
        key=journey.key,
    )


def _runtime_result(stderr: str) -> tuple[dict[str, object], bytes]:
    lines = [line for line in stderr.splitlines() if line.startswith(RESULT_PREFIX)]
    assert len(lines) == 1, stderr
    raw = lines[0].removeprefix(RESULT_PREFIX).encode("utf-8")
    value = json.loads(raw)
    assert raw == canonical_json_bytes(value)
    return value, raw


def _runtime_output(stderr: str) -> bytes:
    lines = [line for line in stderr.splitlines() if line.startswith(OUTPUT_PREFIX)]
    assert len(lines) == 1, stderr
    return base64.b64decode(lines[0].removeprefix(OUTPUT_PREFIX), validate=True)


def _evidence(repository: Path, relative: str) -> dict[str, object]:
    rows = json.loads((repository / relative).read_text(encoding="utf-8"))
    assert isinstance(rows, list) and len(rows) == 1
    record = rows[0]
    admission = admitted_evidence(
        repository / relative,
        repository / "governance/producers.yaml",
    )
    assert len(admission.evidence) == 1
    assert admission.rejections == ()
    return record


def _independent_file_set_rows(repository: Path) -> list[dict[str, object]]:
    manifest_path = repository / RUNTIME / "closure.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = []
    for item in manifest["files"]:
        path = repository / RUNTIME / item["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        assert item["sha256"] == f"sha256:{actual}"
        rows.append(
            {
                **item,
                "seals": ["WRITE", "GROW", "SHRINK", "EXEC", "SEAL"],
                "mount_attributes": (
                    ["RDONLY", "NOEXEC"]
                    if item["kind"] == "runtime-data"
                    else ["RDONLY"]
                ),
            }
        )
    rows.append(
        {
            "path": "closure.json",
            "mode": "0444",
            "kind": "manifest",
            "sha256": "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
            "elf": None,
            "seals": ["WRITE", "GROW", "SHRINK", "EXEC", "SEAL"],
            "mount_attributes": ["RDONLY", "NOEXEC"],
        }
    )
    return sorted(rows, key=lambda row: row["path"])


def _independent_file_set_digest(repository: Path) -> str:
    return hashlib.sha256(
        canonical_json_bytes(_independent_file_set_rows(repository))
    ).hexdigest()


def _independent_parsed_graph_digest(repository: Path) -> str:
    manifest = json.loads((repository / RUNTIME / "closure.json").read_text())
    rows = []
    for item in manifest["files"]:
        if item["kind"] == "runtime-data" or item["elf"] is None:
            continue
        completed = subprocess.run(
            ["/usr/bin/readelf", "-d", str(repository / RUNTIME / item["path"])],
            capture_output=True,
            text=True,
            check=False,
            env={"LC_ALL": "C", "TZ": "UTC"},
        )
        assert completed.returncode == 0, completed.stderr
        needed = sorted(re.findall(r"\(NEEDED\).*\[([^]]+)\]", completed.stdout))
        assert needed == sorted(item["elf"]["needed"])
        rows.append({"path": item["path"], "needed": needed})
    return hashlib.sha256(canonical_json_bytes(sorted(rows, key=lambda row: row["path"]))).hexdigest()


def _independent_realized_graph_digest(repository: Path) -> str:
    root = repository / RUNTIME
    manifest = json.loads((root / "closure.json").read_text())
    loader = root / manifest["loader"]["path"]
    roots = [manifest["entrypoint"]["path"]] + [
        item["path"] for item in manifest["files"] if item["kind"] == "native-extension"
    ]
    rows = []
    for relative in sorted(roots):
        completed = subprocess.run(
            [
                str(loader),
                "--inhibit-cache",
                "--glibc-hwcaps-mask",
                "",
                "--library-path",
                str(root / "lib"),
                "--list",
                str(root / relative),
            ],
            capture_output=True,
            text=True,
            check=False,
            env={"LC_ALL": "C", "TZ": "UTC"},
        )
        assert completed.returncode == 0, completed.stderr
        resolved = []
        for name, path in re.findall(r"^\s*(\S+) => (\S+) \(0x[0-9a-f]+\)$", completed.stdout, re.M):
            resolved.append({"name": name, "path": Path(path).relative_to(root).as_posix()})
        rows.append({"root": relative, "resolved": sorted(resolved, key=lambda row: row["name"])})
    return hashlib.sha256(canonical_json_bytes(rows)).hexdigest()


def test_dynamic_runtime_fixture_and_golden_are_frozen() -> None:
    manifest = json.loads((ROOT / RUNTIME / "closure.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "ranex-dynamic-runtime-closure-v1"
    assert manifest["library_paths"] == ["lib"]
    assert (ROOT / RUNTIME / "data/worker.py").read_bytes() == (
        ROOT / "tests/e2e/fixtures/slice072-worker.py"
    ).read_bytes()
    for relative in (
        "tests/e2e/fixtures/slice072-probe.so",
        "tests/e2e/fixtures/slice072-probe-exec",
        f"{INPUT}/probe.so",
        f"{INPUT}/probe-exec",
        f"{RUNTIME}/data/probe.so",
        f"{RUNTIME}/data/probe-exec",
    ):
        payload = (ROOT / relative).read_bytes()
        assert payload.startswith(b"\x7fELF"), relative
    expected = EXPECTED.read_bytes()
    assert expected.endswith(b"\n")
    assert canonical_json_bytes(json.loads(expected)) + b"\n" == expected


def test_qualification_behaviorally_proves_verifier_isolation_and_drain(
    journey: Journey,
) -> None:
    report = json.loads((journey.repository / QUALIFICATION).read_text(encoding="utf-8"))
    assert report["runtime_v3_verifier_isolation"] == {
        "fork": "EPERM",
        "output_write": "ENOENT",
        "scratch_write": "ENOENT",
        "worker_released": False,
        "verifier_cgroup_populated_after_drain": 0,
    }


def test_public_dynamic_run_binds_output_result_and_evidence_twice(
    journey: Journey,
) -> None:
    observations = []
    for index in (1, 2):
        evidence = f".local/ranex-e2e/slice072-{index}.json"
        completed = _run(journey, evidence)
        assert completed.returncode == 0, completed.stdout + completed.stderr
        result, raw_result = _runtime_result(completed.stderr)
        record = _evidence(journey.repository, evidence)
        assert record["confinement_result_digest"] == hashlib.sha256(raw_result).hexdigest()
        if index == 1:
            tampered = f"{evidence}.tampered"
            changed = json.loads(
                (journey.repository / evidence).read_text(encoding="utf-8")
            )
            changed[0]["confinement_result_digest"] = "0" * 64
            (journey.repository / tampered).write_bytes(
                canonical_json_bytes(changed) + b"\n"
            )
            admission = admitted_evidence(
                journey.repository / tampered,
                journey.repository / "governance/producers.yaml",
            )
            assert admission.evidence == ()
            assert admission.rejections
        runtime = result["runtime_closure"]
        assert set(runtime) == {
            "manifest_digest",
            "sealed_file_set_digest",
            "parsed_graph_digest",
            "realized_graph_digest",
            "loader_digest",
            "profile_digest",
        }
        expected_output = EXPECTED.read_bytes()
        assert _runtime_output(completed.stderr) == expected_output
        assert result["outputs"] == [
            {
                "path": "result.json",
                "bytes": len(expected_output),
                "sha256": hashlib.sha256(expected_output).hexdigest(),
            }
        ]
        assert runtime["sealed_file_set_digest"] == _independent_file_set_digest(
            journey.repository
        )
        assert result["sealed_files"] == _independent_file_set_rows(journey.repository)
        assert runtime["manifest_digest"] == hashlib.sha256(
            (journey.repository / RUNTIME / "closure.json").read_bytes()
        ).hexdigest()
        manifest = json.loads(
            (journey.repository / RUNTIME / "closure.json").read_text(encoding="utf-8")
        )
        assert runtime["loader_digest"] == hashlib.sha256(
            (journey.repository / RUNTIME / manifest["loader"]["path"]).read_bytes()
        ).hexdigest()
        assert runtime["profile_digest"] == hashlib.sha256(
            (journey.repository / PROFILE).read_bytes()
        ).hexdigest()
        assert runtime["parsed_graph_digest"] == _independent_parsed_graph_digest(
            journey.repository
        )
        assert runtime["realized_graph_digest"] == _independent_realized_graph_digest(
            journey.repository
        )
        observations.append(runtime)
    assert observations[0] == observations[1]


def test_ordinary_runtime_semantics_match_governed_output(journey: Journey) -> None:
    root = journey.repository / RUNTIME
    manifest = json.loads((root / "closure.json").read_text(encoding="utf-8"))
    loader = root / manifest["loader"]["path"]
    python = root / manifest["entrypoint"]["path"]
    program = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "import _slice072_extension as e;"
        "print(json.dumps({'declared_extension':e.identity(),"
        "'runtime_value':open(sys.argv[2]).read().strip()},"
        "sort_keys=True,separators=(',',':')))"
    )
    completed = subprocess.run(
        [
            str(loader),
            "--inhibit-cache",
            "--glibc-hwcaps-mask",
            "",
            "--library-path",
            str(root / "lib"),
            str(python),
            "-c",
            program,
            str(root / "lib"),
            str(root / "data/runtime-value.txt"),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={"LC_ALL": "C", "TZ": "UTC"},
    )
    assert completed.returncode == 0, completed.stderr
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    assert json.loads(completed.stdout) == {
        "declared_extension": expected["declared_extension"],
        "runtime_value": expected["runtime_value"],
    }


@pytest.mark.parametrize(
    "kind", ["loader", "entrypoint", "shared-library", "native-extension", "runtime-data"]
)
def test_each_runtime_class_tamper_refuses_before_output(
    journey: Journey,
    kind: str,
) -> None:
    manifest_path = journey.repository / RUNTIME / "closure.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = next(item for item in manifest["files"] if item["kind"] == kind)
    target = journey.repository / RUNTIME / row["path"]
    original = target.read_bytes()
    target.write_bytes(original + b"tamper")
    _git(journey.repository, "add", str(target.relative_to(journey.repository)))
    _git(journey.repository, "commit", "-qm", f"test: tamper {kind}")
    try:
        completed = _run(journey, f".local/ranex-e2e/tamper-{kind}.json")
        assert completed.returncode != 0
        assert RESULT_PREFIX not in completed.stderr
        assert "digest" in (completed.stdout + completed.stderr).lower()
    finally:
        target.write_bytes(original)
        _git(journey.repository, "add", str(target.relative_to(journey.repository)))
        _git(journey.repository, "commit", "-qm", f"test: restore {kind}")


@pytest.mark.parametrize("mode", ["host-only-module", "absolute-old-root"])
def test_host_only_computed_dependency_refuses_without_survivor(
    journey: Journey,
    mode: str,
) -> None:
    input_path = journey.repository / INPUT / "mode.json"
    original = input_path.read_bytes()
    input_path.write_text(json.dumps({"mode": mode}) + "\n", encoding="utf-8")
    _git(journey.repository, "add", str(input_path.relative_to(journey.repository)))
    _git(journey.repository, "commit", "-qm", f"test: select {mode}")
    try:
        completed = _run(journey, f".local/ranex-e2e/{mode}.json")
        assert completed.returncode != 0
        result, _raw = _runtime_result(completed.stderr)
        assert result["outputs"] == []
        assert result["teardown"] == {
            "cgroup_kill": True,
            "populated": 0,
            "cgroup_removed": True,
        }
    finally:
        input_path.write_bytes(original)
        _git(journey.repository, "add", str(input_path.relative_to(journey.repository)))
        _git(journey.repository, "commit", "-qm", "test: restore normal mode")
