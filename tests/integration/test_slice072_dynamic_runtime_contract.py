"""Frozen RED contract for ADR-035's sealed dynamic runtime closure."""

from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import subprocess
import threading
from pathlib import Path

import pytest

from ranex.cli import host_confinement, main
from ranex.foundation.canonical import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[2]
V1_PROFILE = ROOT / "governance/confinement/strict-local-v1.json"
V2_PROFILE = ROOT / "governance/confinement/strict-local-v2.json"
V3_PROFILE = ROOT / "governance/confinement/strict-local-v3.json"
SCHEMA_ROOT = ROOT / "governance/schemas/confinement"
MANIFEST_SCHEMA = SCHEMA_ROOT / "dynamic-runtime-closure-v1.schema.json"
COMMAND_SCHEMA = SCHEMA_ROOT / "confinement-command-v2.schema.json"
RESULT_SCHEMA = SCHEMA_ROOT / "confinement-result-v2.schema.json"
V1_SHA256 = "da4db020e95668e292599bf748c69fef4a9ece920208b184e33074c65a7e4565"
V2_SHA256 = "9625ecc4da209a7a5a5b915f78c944d06310eaf06b92f2844a6392e7652686eb"
DIGEST = "sha256:" + "a" * 64


def _run(*selectors: str, command: str = "/ranex/runtime/bin/python3.12") -> list[str]:
    return [
        "run",
        "--claim",
        "dynamic-runtime-qualified",
        "--producer",
        "owner",
        "--confinement",
        "strict-local",
        *selectors,
        "--",
        command,
        "/ranex/runtime/data/worker.py",
    ]


def _dynamic_selectors() -> tuple[str, ...]:
    return (
        "--runtime-input-path",
        "tests/e2e/fixtures/slice072-input",
        "--runtime-closure-root",
        "tests/e2e/fixtures/slice072-runtime",
    )


def _manifest() -> dict[str, object]:
    value = {
        "schema": "ranex-dynamic-runtime-closure-v1",
        "architecture": {
            "elf_class": 64,
            "endian": "little",
            "machine": "EM_X86_64",
            "osabi": "ELFOSABI_SYSV",
            "abi_version": 0,
        },
        "loader": {
            "path": "loader/ld-linux-x86-64.so.2",
            "self_id": "/lib64/ld-linux-x86-64.so.2",
            "version": "glibc-2.39",
            "sha256": DIGEST,
        },
        "entrypoint": {
            "path": "bin/python3.12",
            "sha256": DIGEST,
            "pt_interp": "/lib64/ld-linux-x86-64.so.2",
        },
        "library_paths": ["lib"],
        "files": [
            {
                "path": "bin/python3.12",
                "mode": "0555",
                "kind": "entrypoint",
                "sha256": DIGEST,
                "elf": _elf(pt_interp="/lib64/ld-linux-x86-64.so.2"),
            },
            {
                "path": "loader/ld-linux-x86-64.so.2",
                "mode": "0555",
                "kind": "loader",
                "sha256": DIGEST,
                "elf": _elf(),
            },
        ],
    }
    return value


def _elf(
    *,
    pt_interp: str | None = None,
    soname: str | None = None,
    needed: list[str] | None = None,
) -> dict[str, object]:
    return {
        "elf_class": 64,
        "endian": "little",
        "machine": "EM_X86_64",
        "osabi": "ELFOSABI_SYSV",
        "abi_version": 0,
        "type": "ET_DYN",
        "pt_interp": pt_interp,
        "soname": soname,
        "needed": [] if needed is None else needed,
        "rpath": None,
        "runpath": None,
        "filter": None,
        "auxiliary": None,
        "audit": None,
        "depaudit": None,
    }


def _runtime_row(path: str = "data/runtime-value.txt") -> dict[str, object]:
    return {
        "path": path,
        "mode": "0444",
        "kind": "runtime-data",
        "sha256": DIGEST,
        "elf": None,
    }


def test_legacy_profiles_remain_byte_identical() -> None:
    assert hashlib.sha256(V1_PROFILE.read_bytes()).hexdigest() == V1_SHA256
    assert hashlib.sha256(V2_PROFILE.read_bytes()).hexdigest() == V2_SHA256
    v2 = json.loads(V2_PROFILE.read_text(encoding="utf-8"))
    assert v2["worker_executable"]["dynamic_runtime_closure"] == (
        "unsupported-refuse"
    )


def test_v3_profile_has_no_dynamic_toolchain_or_caller_destination() -> None:
    value = json.loads(V3_PROFILE.read_text(encoding="utf-8"))
    assert value["schema"] == "ranex-strict-local-runtime-v3"
    assert value["inherits"] == {
        "profile": "governance/confinement/strict-local-v2.json",
        "sha256": f"sha256:{V2_SHA256}",
    }
    assert value["runtime_root"] == "/ranex/runtime"
    assert value["runtime_files"]["maximum"] == 511
    assert value["runtime_files"]["sealed_descriptors_maximum"] == 512
    assert value["runtime_files"]["source"] == "sealed-memfd-map"
    assert "toolchain" not in value["mounts"]
    assert "destination" not in value["runtime_files"]


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    (
        ("loader_tcb", "allowed_objects", []),
        ("verifier", "decision", "controller-may-skip"),
        ("seccomp", "unknown_syscall", "allow"),
        ("mounts", "runtime", {"destination": "/tmp/runtime"}),
        ("sealed_mount_attributes", "executable", ["RDONLY"]),
    ),
)
def test_v3_profile_refuses_every_mutated_policy_section(
    section: str,
    field: str,
    replacement: object,
) -> None:
    changed = json.loads(V3_PROFILE.read_text(encoding="utf-8"))
    changed[section][field] = replacement
    with pytest.raises(
        host_confinement.HostConfinementError,
        match="runtime v3 profile differs from the admitted contract",
    ):
        host_confinement._session_runtime_profile(changed)


def test_three_new_schemas_are_closed_and_exactly_versioned() -> None:
    manifest = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    command = json.loads(COMMAND_SCHEMA.read_text(encoding="utf-8"))
    result = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    for value in (manifest, command, result):
        assert value["additionalProperties"] is False
    assert manifest["properties"]["schema"]["const"] == (
        "ranex-dynamic-runtime-closure-v1"
    )
    assert command["properties"]["schema"]["const"] == (
        "ranex-confinement-command-v2"
    )
    assert result["properties"]["schema"]["const"] == (
        "ranex-confinement-result-v2"
    )
    assert manifest["properties"]["files"]["maxItems"] == 511
    assert set(command["required"]) == {
        "schema",
        "argv",
        "environment",
        "input",
        "subject",
        "runtime",
        "output",
        "scratch",
        "limits",
    }


def test_manifest_schema_freezes_abi_and_loader_affecting_tags() -> None:
    value = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
    assert set(value["$defs"]["architecture"]["required"]) == {
        "elf_class",
        "endian",
        "machine",
        "osabi",
        "abi_version",
    }
    assert set(value["$defs"]["elf"]["required"]) == {
        "elf_class",
        "endian",
        "machine",
        "osabi",
        "abi_version",
        "type",
        "pt_interp",
        "soname",
        "needed",
        "rpath",
        "runpath",
        "filter",
        "auxiliary",
        "audit",
        "depaudit",
    }
    assert value["properties"]["files"]["items"]["$ref"] == "#/$defs/file"
    assert value["$defs"]["file"]["properties"]["kind"]["enum"] == [
        "loader",
        "entrypoint",
        "shared-library",
        "native-extension",
        "runtime-data",
    ]


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda value: value.update(extra=True), "unknown"),
        (lambda value: value.update(library_paths=["lib", "other"]), "library"),
        (lambda value: value["loader"].update(path="../loader"), "canonical"),
        (lambda value: value["entrypoint"].update(path="/bin/python"), "canonical"),
        (lambda value: value["architecture"].update(machine="EM_AARCH64"), "architecture"),
    ],
)
def test_manifest_parser_refuses_closed_shape_and_architecture_drift(
    mutation: object,
    message: str,
) -> None:
    from ranex.foundation.dynamic_runtime import parse_runtime_manifest

    value = _manifest()
    mutation(value)
    with pytest.raises(ValueError, match=message):
        parse_runtime_manifest(canonical_json_bytes(value))


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value["files"].reverse(), "sorted"),
        (
            lambda value: value.update(
                files=sorted(
                    value["files"]
                    + [_runtime_row(f"data/{index:03}.txt") for index in range(510)],
                    key=lambda row: row["path"],
                )
            ),
            "511",
        ),
        (lambda value: value["files"].append(value["files"][0]), "duplicate path"),
        (
            lambda value: value["files"].insert(
                1,
                {
                    **_runtime_row("lib/x.so"),
                    "kind": "shared-library",
                    "elf": _elf(soname="x.so", needed=["$ORIGIN/x"]),
                },
            ),
            "dynamic string",
        ),
    ],
)
def test_manifest_parser_refuses_unsorted_overbound_duplicate_and_dynamic_tokens(
    mutate: object,
    message: str,
) -> None:
    from ranex.foundation.dynamic_runtime import parse_runtime_manifest

    value = _manifest()
    mutate(value)
    with pytest.raises(ValueError, match=message):
        parse_runtime_manifest(canonical_json_bytes(value))


def test_manifest_parser_accepts_one_closed_valid_shape() -> None:
    from ranex.foundation.dynamic_runtime import parse_runtime_manifest

    parsed = parse_runtime_manifest(canonical_json_bytes(_manifest()))
    assert [row.path for row in parsed.files] == [
        "bin/python3.12",
        "loader/ld-linux-x86-64.so.2",
    ]


@pytest.mark.parametrize("tag", ["rpath", "runpath", "filter", "auxiliary", "audit", "depaudit"])
def test_manifest_parser_refuses_each_loader_affecting_tag(tag: str) -> None:
    from ranex.foundation.dynamic_runtime import parse_runtime_manifest

    value = _manifest()
    value["files"][0]["elf"][tag] = "forbidden"
    with pytest.raises(ValueError, match=tag.upper()):
        parse_runtime_manifest(canonical_json_bytes(value))


def test_dynamic_and_static_selector_pairs_are_distinct() -> None:
    dynamic = main.build_parser().parse_args(_run(*_dynamic_selectors()))
    assert dynamic.runtime_input_path == "tests/e2e/fixtures/slice072-input"
    assert dynamic.runtime_closure_root == "tests/e2e/fixtures/slice072-runtime"
    assert dynamic.toolchain_root is None

    static = main.build_parser().parse_args(
        _run(
            "--runtime-input-path",
            "governance/qualification/inputs/T/F/attempt-0",
            "--toolchain-root",
            "governance/qualification/worker",
            command="/ranex/toolchain/bin/slice036-worker",
        )
    )
    assert static.toolchain_root is not None
    assert static.runtime_closure_root is None


@pytest.mark.parametrize(
    "selectors",
    [
        ("--runtime-closure-root", "tests/e2e/fixtures/slice072-runtime"),
        ("--runtime-input-path", "tests/e2e/fixtures/slice072-input"),
        (*_dynamic_selectors(), "--toolchain-root", "governance/qualification/worker"),
        (*_dynamic_selectors(), "--runtime-closure-root", "duplicate"),
    ],
)
def test_invalid_dynamic_selector_combinations_refuse(selectors: tuple[str, ...]) -> None:
    with pytest.raises(SystemExit):
        main.build_parser().parse_args(_run(*selectors))


def test_dynamic_selectors_are_strict_local_only() -> None:
    arguments = _run(*_dynamic_selectors())
    confinement = arguments.index("--confinement")
    del arguments[confinement : confinement + 2]
    with pytest.raises(SystemExit):
        main.build_parser().parse_args(arguments)


@pytest.mark.parametrize(
    "hostile",
    ["/absolute", "../traversal", "https://example.invalid/runtime", "a//b", "a/./b"],
)
def test_dynamic_selector_reuses_canonical_repo_relative_grammar(
    tmp_path: Path,
    hostile: str,
) -> None:
    with pytest.raises(ValueError):
        main._selector_name(tmp_path, hostile, "runtime closure")


def test_dynamic_materialisation_uses_captured_commit_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ranex.cli.subject import Materialisation

    live = tmp_path / "live"
    captured = tmp_path / "captured"
    session = tmp_path / "session"
    for base, marker in ((live, b"live-mutated"), (captured, b"captured-commit")):
        (base / "selected/input").mkdir(parents=True)
        (base / "selected/runtime/data").mkdir(parents=True)
        (base / "selected/input/task.json").write_bytes(marker)
        (base / "selected/runtime/data/value.txt").write_bytes(marker)
    session.mkdir()
    monkeypatch.chdir(live)
    materialisation = Materialisation(
        root=session,
        tree=captured,
        home=session / "home",
        temporary=session / "tmp",
        tracked_paths=(),
    )

    runtime_input, runtime = main._materialise_dynamic_runtime_sources(
        materialisation,
        main.DynamicRuntimeSources(Path("selected/input"), Path("selected/runtime")),
    )

    assert (runtime_input / "task.json").read_bytes() == b"captured-commit"
    assert (runtime / "data/value.txt").read_bytes() == b"captured-commit"


def test_dynamic_runtime_path_never_enters_dependency_provisioning() -> None:
    source = (ROOT / "src/ranex/cli/main.py").read_text(encoding="utf-8")
    assert (
        "if strict_local_sources is not None or dynamic_runtime_sources is not None\n"
        "            else _provisioning_for(root, started_at, args.store)"
    ) in source


def test_sealed_runtime_file_cannot_change_after_source_write_or_replace(
    tmp_path: Path,
) -> None:
    from ranex.foundation.dynamic_runtime import seal_runtime_file

    source = tmp_path / "libfixture.so"
    original = b"declared-runtime-bytes"
    source.write_bytes(original)
    sealed = seal_runtime_file(
        source,
        hashlib.sha256(original).hexdigest(),
        kind="shared-library",
        mode=0o555,
    )
    try:
        source.write_bytes(b"same-inode-mutation")
        replacement = tmp_path / "replacement"
        replacement.write_bytes(b"rename-replacement")
        replacement.replace(source)
        assert os.pread(sealed.descriptor, len(original), 0) == original
        seals = fcntl.fcntl(sealed.descriptor, fcntl.F_GET_SEALS)
        expected = (
            fcntl.F_SEAL_WRITE
            | fcntl.F_SEAL_GROW
            | fcntl.F_SEAL_SHRINK
            | 0x0020  # F_SEAL_EXEC from the installed linux/fcntl.h
            | fcntl.F_SEAL_SEAL
        )
        assert seals & expected == expected
        with pytest.raises(OSError) as write_refusal:
            os.pwrite(sealed.descriptor, b"x", 0)
        assert write_refusal.value.errno == errno.EPERM
        with pytest.raises(OSError) as grow_refusal:
            os.ftruncate(sealed.descriptor, len(original) + 1)
        assert grow_refusal.value.errno == errno.EPERM
    finally:
        os.close(sealed.descriptor)


def test_mutation_during_copy_can_never_admit_changed_bytes(tmp_path: Path) -> None:
    from ranex.foundation.dynamic_runtime import seal_runtime_file

    source = tmp_path / "large-runtime-data"
    original = b"a" * (8 * 1024 * 1024)
    changed = b"b" * len(original)
    source.write_bytes(original)
    stop = threading.Event()

    def mutate() -> None:
        while not stop.is_set():
            source.write_bytes(changed)
            source.write_bytes(original)

    writer = threading.Thread(target=mutate)
    writer.start()
    try:
        try:
            sealed = seal_runtime_file(
                source,
                hashlib.sha256(original).hexdigest(),
                kind="runtime-data",
                mode=0o444,
            )
        except ValueError:
            return
        try:
            assert os.pread(sealed.descriptor, len(original), 0) == original
        finally:
            os.close(sealed.descriptor)
    finally:
        stop.set()
        writer.join()


@pytest.mark.parametrize(
    ("kind", "mode", "creation_flag", "execute_allowed"),
    [
        ("shared-library", 0o555, 0x0010, True),
        ("runtime-data", 0o444, 0x0008, False),
        ("manifest", 0o444, 0x0008, False),
    ],
)
def test_sealing_freezes_per_kind_memfd_execution_and_mode(
    tmp_path: Path,
    kind: str,
    mode: int,
    creation_flag: int,
    execute_allowed: bool,
) -> None:
    from ranex.foundation.dynamic_runtime import seal_runtime_file

    source = tmp_path / kind
    payload = b"declared"
    source.write_bytes(payload)
    sealed = seal_runtime_file(
        source,
        hashlib.sha256(payload).hexdigest(),
        kind=kind,
        mode=mode,
    )
    try:
        assert sealed.creation_flags & creation_flag == creation_flag
        assert os.fstat(sealed.descriptor).st_mode & 0o777 == mode
        assert fcntl.fcntl(sealed.descriptor, fcntl.F_GET_SEALS) & 0x0020
        assert sealed.execute_allowed is execute_allowed
    finally:
        os.close(sealed.descriptor)


@pytest.mark.parametrize(
    ("path", "kind"),
    [
        ("closure.json", "runtime-data"),
        ("data/native.so", "native-extension"),
        ("lib/value.txt", "runtime-data"),
        ("bin/libpython.so", "shared-library"),
        ("lib", "shared-library"),
        ("a" * 256, "runtime-data"),
    ],
)
def test_manifest_refuses_reserved_kind_prefix_and_ancestor_collisions(
    path: str,
    kind: str,
) -> None:
    from ranex.foundation.dynamic_runtime import validate_runtime_rows

    with pytest.raises(ValueError):
        validate_runtime_rows([{"path": path, "kind": kind}])


def test_manifest_refuses_actual_file_ancestor_collision() -> None:
    from ranex.foundation.dynamic_runtime import validate_runtime_rows

    with pytest.raises(ValueError, match="ancestor|collision"):
        validate_runtime_rows(
            [
                {"path": "lib/x.so", "kind": "shared-library"},
                {"path": "lib/x.so/y.so", "kind": "shared-library"},
            ]
        )


def test_dynamic_source_admission_refuses_dirty_untracked_symlink_and_overlap(
    tmp_path: Path,
) -> None:
    from ranex.cli.main import _strict_local_runtime_sources

    repository = tmp_path / "repository"
    repository.mkdir()
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.email", "test@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.name", "test"], check=True
    )
    input_root = repository / "input"
    closure_root = repository / "runtime"
    input_root.mkdir()
    closure_root.mkdir()
    (input_root / "mode.json").write_text("{}\n", encoding="utf-8")
    (closure_root / "closure.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-qm", "fixture"], check=True
    )
    base = subprocess.run(
        ["git", "-C", str(repository), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    _strict_local_runtime_sources(repository, base, "input", "runtime")
    (input_root / "mode.json").write_text("dirty\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs|dirty"):
        _strict_local_runtime_sources(repository, base, "input", "runtime")
    subprocess.run(
        ["git", "-C", str(repository), "restore", "input/mode.json"], check=True
    )
    (closure_root / "untracked").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="untracked|exact"):
        _strict_local_runtime_sources(repository, base, "input", "runtime")
    (closure_root / "untracked").unlink()
    with pytest.raises(ValueError, match="overlap"):
        _strict_local_runtime_sources(repository, base, "runtime", "runtime")
    (repository / "runtime-link").symlink_to("runtime", target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        _strict_local_runtime_sources(repository, base, "input", "runtime-link")
    with pytest.raises(ValueError, match="base|started_at|commit"):
        _strict_local_runtime_sources(repository, "0" * 40, "input", "runtime")


def test_loader_report_normalization_is_address_independent_and_closed() -> None:
    from ranex.foundation.dynamic_runtime import normalize_loader_report

    raw = b"""\
\tlinux-vdso.so.1 (0x00007fff00000000)
\tlibc.so.6 => /ranex/runtime/lib/libc.so.6 (0x0000700000000000)
\t/ranex/runtime/loader/ld-linux-x86-64.so.2 (0x0000700000200000)
"""
    assert normalize_loader_report(raw) == {
        "loader": "/ranex/runtime/loader/ld-linux-x86-64.so.2",
        "synthetic": ["linux-vdso.so.1"],
        "resolved": {"libc.so.6": "/ranex/runtime/lib/libc.so.6"},
    }
    with pytest.raises(ValueError, match="outside"):
        normalize_loader_report(raw.replace(b"/ranex/runtime/lib", b"/lib/x86_64-linux-gnu"))


def test_result_v2_requires_all_six_runtime_digests() -> None:
    value = json.loads(RESULT_SCHEMA.read_text(encoding="utf-8"))
    runtime = value["properties"]["runtime_closure"]
    assert runtime["additionalProperties"] is False
    assert runtime["required"] == [
        "manifest_digest",
        "sealed_file_set_digest",
        "parsed_graph_digest",
        "realized_graph_digest",
        "loader_digest",
        "profile_digest",
    ]


def test_result_v2_consumer_refuses_runtime_digest_substitution() -> None:
    from ranex.cli.host_confinement import validate_confinement_result_v2

    sealed_files = [
        {
            "path": "bin/python3.12",
            "mode": "0555",
            "kind": "entrypoint",
            "sha256": "sha256:" + "a" * 64,
            "elf": _elf(pt_interp="/lib64/ld-linux-x86-64.so.2"),
            "seals": ["WRITE", "GROW", "SHRINK", "FUTURE_WRITE", "EXEC", "SEAL"],
            "mount_attributes": ["RDONLY"],
        },
        {
            "path": "closure.json",
            "mode": "0444",
            "kind": "manifest",
            "sha256": "sha256:" + "c" * 64,
            "elf": None,
            "seals": ["WRITE", "GROW", "SHRINK", "EXEC", "SEAL"],
            "mount_attributes": ["RDONLY", "NOEXEC"],
        },
        {
            "path": "data/value.txt",
            "mode": "0444",
            "kind": "runtime-data",
            "sha256": "sha256:" + "b" * 64,
            "elf": None,
            "seals": ["WRITE", "GROW", "SHRINK", "EXEC", "SEAL"],
            "mount_attributes": ["RDONLY", "NOEXEC"],
        },
    ]
    file_set_digest = hashlib.sha256(canonical_json_bytes(sealed_files)).hexdigest()
    value: dict[str, object] = {
        "schema": "ranex-confinement-result-v2",
        "profile_digests": {
            "runtime": "1" * 64,
            "host": "2" * 64,
            "launcher": "3" * 64,
        },
        "namespace_readbacks": {
            "user": "user:[1001]",
            "mount": "mnt:[1002]",
            "pid": "pid:[1003]",
            "ipc": "ipc:[1004]",
            "network": "net:[1005]",
            "cgroup": "cgroup:[1006]",
        },
        "cgroup_readbacks": {
            "limits": {
                "cpu.max": "max 100000",
                "memory.max": "1073741824",
                "pids.max": "16",
            },
            "events": {"memory": {"max": 0}, "pids": {"max": 0}, "populated": 0},
            "usage": {"cpu_usage_usec": 1},
        },
        "command": {
            "argv_digest": "4" * 64,
            "exit_code": 0,
            "no_new_privs": True,
            "landlock": True,
            "seccomp": True,
        },
        "runtime_closure": {
            "manifest_digest": "a" * 64,
            "sealed_file_set_digest": file_set_digest,
            "parsed_graph_digest": "c" * 64,
            "realized_graph_digest": "d" * 64,
            "loader_digest": "e" * 64,
            "profile_digest": "f" * 64,
        },
        "sealed_files": sealed_files,
        "outputs": [],
        "teardown": {"cgroup_kill": True, "populated": 0, "cgroup_removed": True},
    }
    runtime_expected = dict(value["runtime_closure"])
    expected = {
        "runtime_closure": runtime_expected,
        "profile_digests": dict(value["profile_digests"]),
        "argv_digest": value["command"]["argv_digest"],
        "cgroup_limits": dict(value["cgroup_readbacks"]["limits"]),
        "namespace_readbacks": dict(value["namespace_readbacks"]),
        "cgroup_readbacks": json.loads(json.dumps(value["cgroup_readbacks"])),
    }
    validate_confinement_result_v2(value, expected)
    for digest_name in runtime_expected:
        changed = json.loads(json.dumps(value))
        changed["runtime_closure"][digest_name] = "0" * 64
        with pytest.raises(ValueError, match=digest_name):
            validate_confinement_result_v2(changed, expected)
    for mutation in (
        lambda rows: rows.reverse(),
        lambda rows: rows.append(rows[0]),
        lambda rows: rows[0].update(mode="0777"),
        lambda rows: rows[0].update(seals=[]),
        lambda rows: rows[0].update(mount_attributes=[]),
    ):
        changed = json.loads(json.dumps(value))
        mutation(changed["sealed_files"])
        with pytest.raises(ValueError, match="sealed"):
            validate_confinement_result_v2(changed, expected)
    missing = json.loads(json.dumps(value))
    del missing["runtime_closure"]["manifest_digest"]
    with pytest.raises(ValueError, match="manifest_digest"):
        validate_confinement_result_v2(missing, expected)
    for field in (
        "profile_digests",
        "namespace_readbacks",
        "cgroup_readbacks",
        "command",
        "teardown",
    ):
        changed = json.loads(json.dumps(value))
        changed[field] = {}
        with pytest.raises(ValueError, match=field.replace("_digests", "_digests")):
            validate_confinement_result_v2(changed, expected)
    for field, mutation in (
        ("profile_digests", lambda changed: changed["profile_digests"].update(runtime="0" * 64)),
        ("command", lambda changed: changed["command"].update(argv_digest="0" * 64)),
        ("cgroup_readbacks", lambda changed: changed["cgroup_readbacks"]["limits"].update({"pids.max": "17"})),
        ("cgroup_readbacks", lambda changed: changed["cgroup_readbacks"]["events"]["memory"].update(max=1)),
        ("cgroup_readbacks", lambda changed: changed["cgroup_readbacks"]["usage"].update(cpu_usage_usec=999_999)),
        ("namespace_readbacks", lambda changed: changed["namespace_readbacks"].update(user="user:[999999]")),
    ):
        changed = json.loads(json.dumps(value))
        mutation(changed)
        with pytest.raises(ValueError, match=field):
            validate_confinement_result_v2(changed, expected)


def test_production_expected_map_binds_the_realized_graph() -> None:
    from ranex.foundation.dynamic_runtime import (
        expected_realized_runtime_graph,
        parse_runtime_manifest,
        realized_graph_digest,
    )

    manifest_path = ROOT / "tests/e2e/fixtures/slice072-runtime/closure.json"
    manifest = parse_runtime_manifest(manifest_path.read_bytes())
    assert realized_graph_digest(expected_realized_runtime_graph(manifest)) == (
        "6e9354103f3e38a3ffdd6aadab1e7370cc3ecd9b5166fb993fac472bd3b3e365"
    )
    source = (ROOT / "src/ranex/cli/main.py").read_text(encoding="utf-8")
    assert '"realized_graph_digest": realized_graph_digest(' in source
    assert '"profile_digests": {' in source
    assert '"argv_digest": hashlib.sha256(' in source
    assert '"cgroup_limits": {' in source
    assert 'expected_runtime_closure["namespace_readbacks"] = observations[' in source
    assert 'expected_runtime_closure["cgroup_readbacks"] = observations[' in source


def test_v3_shared_deadline_refuses_before_readiness_or_ack(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(host_confinement.time, "monotonic", lambda: 10.0)
    assert host_confinement._remaining_session_time(10.25, "launcher readiness") == 0.25
    for boundary in ("launcher readiness", "readiness acknowledgement"):
        with pytest.raises(host_confinement.HostConfinementError, match=boundary):
            host_confinement._remaining_session_time(10.0, boundary)

    source = (ROOT / "src/ranex/cli/host_confinement.py").read_text(encoding="utf-8")
    deadline = source.index("session_deadline = time.monotonic() + (")
    release_start = source.index("session.release_start_gate()", deadline)
    mount_readback = source.index(
        '_remaining_session_time(session_deadline, "runtime mount readback")'
    )
    drain = source.index(
        '_remaining_session_time(session_deadline, "verifier cgroup drain")',
        mount_readback,
    )
    verifier_go = source.index(
        '_remaining_session_time(session_deadline, "runtime verifier GO")', drain
    )
    readiness = source.index(
        '_remaining_session_time(\n                session_deadline, "launcher readiness"'
    )
    readbacks = source.index("_read_worker_cgroup_membership", readiness)
    acknowledgement = source.index(
        '_remaining_session_time(session_deadline, "readiness acknowledgement")',
        readbacks,
    )
    release = source.index('os.write(readiness_ack_write, b"1")', acknowledgement)
    assert (
        deadline
        < release_start
        < mount_readback
        < drain
        < verifier_go
        < readiness
        < readbacks
        < acknowledgement
        < release
    )


def test_controller_admits_v3_and_preserves_ordinary_and_v2_parsing() -> None:
    parsed_v3 = host_confinement._session_runtime_profile(
        json.loads(V3_PROFILE.read_text(encoding="utf-8"))
    )
    assert parsed_v3.schema == "ranex-strict-local-runtime-v3"
    host_confinement._session_runtime_profile(
        json.loads(V2_PROFILE.read_text(encoding="utf-8"))
    )
    ordinary = main.build_parser().parse_args(
        ["run", "--claim", "x", "--producer", "owner", "--", "/bin/true"]
    )
    assert ordinary.confinement is None
    assert ordinary.command == ["--", "/bin/true"]
