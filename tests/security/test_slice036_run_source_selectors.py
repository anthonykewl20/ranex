"""Frozen public-run source-selector refusal contract for SLICE-036."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.cli import main as cli

ROOT = Path(__file__).parents[2]
TASK_ROOT = "governance/qualification/inputs/SLICE-036-child-A"
INPUT = f"{TASK_ROOT}/a-before-b/attempt-0"
TOOLCHAIN = "governance/qualification/worker"
JOURNAL = "governance/journal.sqlite3"


@dataclass(frozen=True)
class SelectorCase:
    case_id: str
    expected_refusal: str


CASES = (
    SelectorCase(
        "final-symlink",
        "E-C18-PATH-ALIAS: runtime input selector contains a symlink",
    ),
    SelectorCase(
        "intermediate-symlink",
        "E-C18-PATH-ALIAS: runtime input selector contains a symlink",
    ),
    SelectorCase(
        "untracked",
        "E-C18-GATE: runtime input selector is not tracked at started_at",
    ),
    SelectorCase(
        "dirty",
        "E-C18-GATE: runtime input selector differs from started_at",
    ),
    SelectorCase(
        "wrong-base",
        "E-C18-GATE: runtime input selector is absent from started_at",
    ),
    SelectorCase(
        "held-object-overlap",
        "E-C18-PATH-ALIAS: input and toolchain source objects overlap",
    ),
    SelectorCase(
        "dynamic-elf",
        "E-C18-GATE: v2 worker requests an unsupported dynamic runtime closure",
    ),
    SelectorCase(
        "manifest-drift",
        "E-C18-GATE: toolchain source digest differs from its build manifest",
    ),
    SelectorCase(
        "digest-drift",
        "E-C18-GATE: toolchain worker digest differs from its build manifest",
    ),
)


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(root), *arguments],
        capture_output=True,
        check=False,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def commit(root: Path, message: str) -> str:
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "HEAD")


def task_record(*, flow_id: str, attempt: int) -> bytes:
    value = {
        "attempt": attempt,
        "delay_ms": 0,
        "flow_id": flow_id,
        "mode": "normal",
        "task_id": "SLICE-036-child-A",
        "version": "slice036-child-input-v2",
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def assert_dynamic_runtime_elf(image: bytes) -> None:
    """Prove the planted host executable really requests a runtime loader."""

    elf_h = Path("/usr/include/elf.h").read_text(encoding="utf-8")
    assert "#define PT_INTERP\t3" in elf_h
    elf64_header = struct.Struct("<16sHHIQQQIHHHHHH")
    elf64_program_header = struct.Struct("<IIQQQQQQ")
    assert len(image) >= elf64_header.size
    header = elf64_header.unpack_from(image)
    assert header[0][:7] == b"\x7fELF\x02\x01\x01"
    assert header[1] == 2  # ET_EXEC
    assert header[2] == 62  # EM_X86_64
    program_offset, program_entry_size, program_count = header[5], header[9], header[10]
    assert program_entry_size == elf64_program_header.size
    assert program_offset + program_entry_size * program_count <= len(image)
    programs = [
        elf64_program_header.unpack_from(
            image, program_offset + index * program_entry_size
        )
        for index in range(program_count)
    ]
    assert any(program[0] == 3 for program in programs)  # PT_INTERP


@pytest.fixture(scope="module")
def selector_repo_template(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("slice036-selector-template") / "governed"
    root.mkdir()
    for flow_id in ("a-before-b", "b-before-a"):
        for attempt in (0, 1):
            destination = root / TASK_ROOT / flow_id / f"attempt-{attempt}" / "task.json"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(task_record(flow_id=flow_id, attempt=attempt))

    worker_root = root / TOOLCHAIN
    worker_root.mkdir(parents=True)
    source = ROOT / "tests/e2e/fixtures/slice036-worker.c"
    manifest_source = ROOT / "tests/e2e/fixtures/slice036-worker-build-v1.json"
    shutil.copyfile(source, worker_root / "slice036-worker.c")
    shutil.copyfile(manifest_source, worker_root / "slice036-worker-build-v1.json")
    manifest = json.loads(manifest_source.read_bytes())
    worker = worker_root / "slice036-worker"
    flags = [
        token.replace("<ABS_REPO_ROOT>", str(root.resolve()))
        .replace("<output>", str(worker))
        .replace("<source>", str(worker_root / "slice036-worker.c"))
        for token in manifest["build"]["flags"]
    ]
    built = subprocess.run(
        [manifest["build"]["compiler"]["path"], *flags],
        cwd=root,
        env=manifest["build"]["environment"],
        capture_output=True,
        check=False,
        text=True,
    )
    assert built.returncode == 0, built.stderr
    assert hashlib.sha256(worker.read_bytes()).hexdigest() == manifest["artifact"]["sha256"]
    worker.chmod(0o555)

    governance = root / "governance"
    (governance / "producers.yaml").write_text(
        "producers:\n  owner: ed25519:A6EHv/POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg=\n",
        encoding="utf-8",
    )
    (governance / "gates.yaml").write_text("gates: []\n", encoding="utf-8")
    (root / ".gitignore").write_text(
        "governance/qualification/evidence.json\ngovernance/journal.sqlite3\n.local/\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.name", "Ranex Selector Fixture")
    git(root, "config", "user.email", "selector@ranex.invalid")
    commit(root, "test(SLICE-036): selector security fixture")
    return root


def arguments(
    root: Path,
    *,
    runtime_input_path: str = INPUT,
    toolchain_root: str = TOOLCHAIN,
) -> argparse.Namespace:
    return argparse.Namespace(
        claim="slice036-child-check",
        producer="owner",
        repository=str(root),
        evidence="governance/qualification/evidence.json",
        producers="governance/producers.yaml",
        gate="landing",
        gate_catalog="governance/gates.yaml",
        suite_manifest="governance/suite_manifest.json",
        store=cli.default_store(),
        confinement="strict-local",
        runtime_input_path=runtime_input_path,
        toolchain_root=toolchain_root,
        command=["--", "/ranex/toolchain/bin/slice036-worker", "--task"],
    )


def journal_snapshot(path: Path) -> tuple[int, str | None]:
    if not path.exists():
        return 0, None
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT COUNT(*), (SELECT link FROM evaluations ORDER BY seq DESC LIMIT 1) "
            "FROM evaluations"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return int(row[0]), row[1]


def filesystem_snapshot(root: Path) -> tuple[tuple[str, str], ...]:
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if relative == ".git" or relative.startswith(".git/"):
            continue
        if path.is_symlink():
            rows.append((relative, "symlink:" + os.readlink(path)))
        elif path.is_file():
            rows.append((relative, "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()))
        elif path.is_dir():
            rows.append((relative, "directory"))
    return tuple(rows)


def governed_snapshot(root: Path) -> dict[str, object]:
    return {
        "filesystem": filesystem_snapshot(root),
        "journal": journal_snapshot(root / JOURNAL),
        "refs": git(root, "show-ref"),
        "status": git(root, "status", "--porcelain=v1", "--untracked-files=all"),
        "tracked_tree": git(root, "rev-parse", "HEAD^{tree}"),
    }


def plant(case: SelectorCase, root: Path) -> tuple[str, str, str]:
    runtime_input_path = INPUT
    toolchain_root = TOOLCHAIN
    started_at = git(root, "rev-parse", "HEAD")
    input_path = root / INPUT
    manifest_path = root / TOOLCHAIN / "slice036-worker-build-v1.json"
    worker_path = root / TOOLCHAIN / "slice036-worker"

    if case.case_id == "final-symlink":
        shutil.rmtree(input_path)
        input_path.symlink_to("attempt-1", target_is_directory=True)
        commit(root, "test: plant final selector symlink")
    elif case.case_id == "intermediate-symlink":
        flow = input_path.parent
        shutil.rmtree(flow)
        flow.symlink_to("b-before-a", target_is_directory=True)
        commit(root, "test: plant intermediate selector symlink")
    elif case.case_id == "untracked":
        runtime_input_path = f"{TASK_ROOT}/a-before-b/attempt-2"
        untracked = root / runtime_input_path / "task.json"
        untracked.parent.mkdir(parents=True)
        untracked.write_bytes(task_record(flow_id="a-before-b", attempt=2))
    elif case.case_id == "dirty":
        (input_path / "task.json").write_bytes(task_record(flow_id="a-before-b", attempt=1))
    elif case.case_id == "wrong-base":
        runtime_input_path = f"{TASK_ROOT}/a-before-b/attempt-3"
        added = root / runtime_input_path / "task.json"
        added.parent.mkdir(parents=True)
        added.write_bytes(task_record(flow_id="a-before-b", attempt=3))
        commit(root, "test: add selector after captured base")
    elif case.case_id == "held-object-overlap":
        toolchain_root = runtime_input_path
    elif case.case_id == "dynamic-elf":
        manifest = json.loads(manifest_path.read_bytes())
        flags = [
            token.replace("<ABS_REPO_ROOT>", str(root.resolve()))
            .replace("<output>", str(worker_path))
            .replace("<source>", str(root / TOOLCHAIN / "slice036-worker.c"))
            for token in manifest["build"]["flags"]
            if token != "-static"
        ]
        built = subprocess.run(
            [manifest["build"]["compiler"]["path"], *flags],
            cwd=root,
            env=manifest["build"]["environment"],
            capture_output=True,
            check=False,
            text=True,
        )
        assert built.returncode == 0, built.stderr
        assert_dynamic_runtime_elf(worker_path.read_bytes())
        manifest["artifact"]["sha256"] = hashlib.sha256(worker_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
        commit(root, "test: plant internally bound dynamic worker")
    elif case.case_id == "manifest-drift":
        manifest = json.loads(manifest_path.read_bytes())
        manifest["build"]["source"]["sha256"] = "0" * 64
        manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
        commit(root, "test: plant source manifest drift")
    elif case.case_id == "digest-drift":
        worker_path.chmod(0o755)
        worker_path.write_bytes(worker_path.read_bytes() + b"digest-drift")
        worker_path.chmod(0o555)
        commit(root, "test: plant worker digest drift")
    else:  # pragma: no cover - the closed parameter table makes this unreachable.
        raise AssertionError(case.case_id)
    return runtime_input_path, toolchain_root, started_at


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.case_id)
def test_public_cmd_run_selector_refusal_is_exact_and_precedes_every_side_effect(
    case: SelectorCase,
    selector_repo_template: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = tmp_path / "governed"
    subprocess.run(["git", "clone", "--quiet", str(selector_repo_template), str(root)], check=True)
    git(root, "config", "user.name", "Ranex Selector Fixture")
    git(root, "config", "user.email", "selector@ranex.invalid")
    runtime_input_path, toolchain_root, started_at = plant(case, root)
    before = governed_snapshot(root)
    controller_temp = tmp_path / "controller-temp"
    controller_temp.mkdir()
    controller_temp_before = filesystem_snapshot(controller_temp)

    real_head_commit = cli.head_commit
    observations: list[str] = []

    def captured_head(repository: Path) -> str:
        observations.append("started_at")
        if case.case_id == "wrong-base":
            return started_at
        return real_head_commit(repository)

    def forbidden_provisioning(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("selector refusal crossed the provisioning boundary")

    monkeypatch.setattr(cli, "governed_repository_root", lambda: root)
    monkeypatch.setattr(cli, "head_commit", captured_head)
    monkeypatch.setattr(cli, "_provisioning_for", forbidden_provisioning)
    monkeypatch.setattr(cli.tempfile, "tempdir", str(controller_temp))
    result = cli.cmd_run(
        arguments(
            root,
            runtime_input_path=runtime_input_path,
            toolchain_root=toolchain_root,
        )
    )
    captured = capsys.readouterr()

    assert result == cli.EXIT_USAGE
    assert captured.out == ""
    assert captured.err == f"ERROR  {case.expected_refusal}\n"
    assert observations == ["started_at"]
    assert governed_snapshot(root) == before
    assert filesystem_snapshot(controller_temp) == controller_temp_before
    for relative in (
        "governance/qualification/evidence.json",
        JOURNAL,
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        ".local/ranex/qualification/strict-local-v1.json",
        ".local/ranex/slice036/output",
        ".local/ranex/slice036/scratch",
        ".local/ranex/slice036/confinement-result.json",
    ):
        assert not (root / relative).exists()


def test_parser_keeps_source_selectors_out_of_ordinary_and_v1_run() -> None:
    parser = cli.build_parser()
    ordinary = parser.parse_args(
        ["run", "--claim", "claim", "--producer", "owner", "--", "/bin/true"]
    )
    assert ordinary.confinement is None
    assert ordinary.runtime_input_path is None
    assert ordinary.toolchain_root is None

    strict = parser.parse_args(
        [
            "run", "--claim", "claim", "--producer", "owner",
            "--confinement", "strict-local",
            "--runtime-input-path", INPUT,
            "--toolchain-root", TOOLCHAIN,
            "--", "/ranex/toolchain/bin/slice036-worker", "--task",
        ]
    )
    assert strict.runtime_input_path == INPUT
    assert strict.toolchain_root == TOOLCHAIN
    assert strict.command == ["--", "/ranex/toolchain/bin/slice036-worker", "--task"]
