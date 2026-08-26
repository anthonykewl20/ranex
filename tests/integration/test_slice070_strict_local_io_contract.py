"""SLICE-070 frozen integration contract for the strict-local I/O ABI.

The profile closure is green at SPEC PRD.  The remaining assertions are honest
RED at the absent v2 parser, descriptor-to-fixed-mount assembly, and public run
selection seams.  They must not be satisfied by changing the fixture.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from ranex.cli import host_confinement, main
from ranex.foundation.canonical import canonical_json_bytes

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "governance/confinement/strict-local-v2.json"
EXPECTED_PROFILE_SHA256 = "9625ecc4da209a7a5a5b915f78c944d06310eaf06b92f2844a6392e7652686eb"


def profile() -> dict[str, object]:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def test_profile_bytes_are_digest_bound() -> None:
    assert hashlib.sha256(PROFILE.read_bytes()).hexdigest() == EXPECTED_PROFILE_SHA256


def test_profile_closes_runtime_owned_io_and_self_contained_worker() -> None:
    value = profile()
    mounts = value["mounts"]
    assert isinstance(mounts, dict)
    assert mounts == {
        "dev": {"nodes": [], "type": "tmpfs"},
        "input": {
            "access": "read-only",
            "destination": "/ranex/input",
            "source": "input",
        },
        "output": {
            "access": "writable-bounded",
            "destination": "/ranex/output",
            "source": "output",
        },
        "proc": "fresh",
        "scratch": {
            "access": "writable-bounded",
            "destination": "/ranex/scratch",
            "source": "scratch",
        },
        "subject": {
            "access": "read-only-noexec",
            "destination": "/ranex/subject",
            "mount_attributes": ["MOUNT_ATTR_RDONLY", "MOUNT_ATTR_NOEXEC"],
            "source": "subject",
        },
        "toolchain": {
            "access": "read-only",
            "destination": "/ranex/toolchain",
            "source": "toolchain",
        },
    }
    assert value["cwd"] == "/ranex/input"
    assert value["landlock"] == {
        "subject_allowed_access": [
            "LANDLOCK_ACCESS_FS_READ_FILE",
            "LANDLOCK_ACCESS_FS_READ_DIR",
        ],
        "toolchain_allowed_access": [
            "LANDLOCK_ACCESS_FS_EXECUTE",
            "LANDLOCK_ACCESS_FS_READ_FILE",
            "LANDLOCK_ACCESS_FS_READ_DIR",
        ],
        "v1_policy": "unchanged",
    }
    assert value["worker_executable"] == {
        "dynamic_runtime_closure": "unsupported-refuse",
        "required_linkage": "self-contained-static",
        "source": "descriptor-held-toolchain-object",
    }
    assert value["worker_io"] == {
        "environment": ["LC_ALL", "TZ"],
        "inherited_data_fds": "closed",
        "predecessor_inputs": "none",
        "stdin": "closed",
    }
    assert value["output_contract"] == {
        "collection_source": "descriptor-held-output-object",
        "declared_paths": "absolute-beneath-root",
        "root": "/ranex/output",
    }


def test_runtime_parser_admits_exactly_the_v2_profile() -> None:
    """RED: the production parser still owns only v1's path-preserving map."""

    host_confinement._session_runtime_profile(profile())


def test_public_strict_local_run_selects_v2_without_changing_ordinary_run() -> None:
    """RED: the opt-in path must advance; the ordinary path stays unconfined."""

    assert main._CONFINEMENT_RUNTIME_PROFILE == "governance/confinement/strict-local-v2.json"
    source = (ROOT / "src/ranex/cli/main.py").read_text(encoding="utf-8")
    assert "if confinement is not None:" in source
    assert 'confinement == "strict-local"' in source


def test_descriptor_keeps_sources_only_and_cannot_choose_mount_destinations() -> None:
    """The controller, never descriptor JSON, owns the fixed aliases."""

    source = (ROOT / "src/ranex/cli/host_confinement.py").read_text(encoding="utf-8")
    assert 'expected = {"schema", "argv", "environment", "input", "subject", "toolchain", "output", "scratch", "limits"}' in source
    for forbidden in ('"input_destination"', '"toolchain_destination"', '"output_destination"', '"scratch_destination"'):
        assert forbidden not in source


def _descriptor(root: Path, **overrides: object) -> Path:
    case = root / "case"
    case.mkdir(exist_ok=True)
    for name in ("subject", "toolchain", "output", "scratch"):
        (case / name).mkdir(parents=True, exist_ok=True)
    value = {
        "argv": ["/bin/true"],
        "environment": {"LC_ALL": "C", "TZ": "UTC"},
        "limits": {
            "cpu_usage_usec": 1_000_000,
            "memory_bytes": 134_217_728,
            "output_bytes": 65_536,
            "output_depth": 8,
            "output_inodes": 32,
            "pids": 16,
            "wall_time_ms": 5_000,
        },
        "output": "case/output",
        "schema": "ranex-confinement-command-v1",
        "scratch": "case/scratch",
        "subject": "case/subject",
        "toolchain": "case/toolchain",
    }
    value.update(overrides)
    path = case / "descriptor.json"
    path.write_bytes(canonical_json_bytes(value))
    return path


def test_source_reference_alias_is_refused_before_runtime_mounts(tmp_path: Path) -> None:
    descriptor = _descriptor(tmp_path)
    (tmp_path / "case" / "toolchain").rmdir()
    (tmp_path / "case" / "toolchain").symlink_to("subject", target_is_directory=True)

    with pytest.raises(host_confinement.HostConfinementError) as refusal:
        host_confinement._session_descriptor(tmp_path, str(descriptor.relative_to(tmp_path)))
    assert refusal.value.code == host_confinement.E_C18_PATH_ALIAS


def test_writable_and_authority_overlap_is_refused(tmp_path: Path) -> None:
    nested = tmp_path / "case" / "subject" / "output"
    nested.mkdir(parents=True)
    descriptor = _descriptor(tmp_path, output="case/subject/output")

    with pytest.raises(host_confinement.HostConfinementError) as refusal:
        host_confinement._session_descriptor(tmp_path, str(descriptor.relative_to(tmp_path)))
    assert refusal.value.code == host_confinement.E_C18_PATH_ALIAS


def test_source_traversal_is_refused_before_descriptor_admission(tmp_path: Path) -> None:
    descriptor = _descriptor(tmp_path, output="../outside")

    with pytest.raises(ValueError, match="outside the repository"):
        host_confinement._session_descriptor(tmp_path, str(descriptor.relative_to(tmp_path)))


@pytest.mark.parametrize("hostile", ["/tmp/outside", "https://example.invalid/tree"])
def test_absolute_and_remote_sources_are_refused(tmp_path: Path, hostile: str) -> None:
    descriptor = _descriptor(tmp_path, output=hostile)

    with pytest.raises(ValueError, match="refused"):
        host_confinement._session_descriptor(tmp_path, str(descriptor.relative_to(tmp_path)))


def test_symlink_escape_is_refused(tmp_path: Path) -> None:
    descriptor = _descriptor(tmp_path, output="case/escape")
    (tmp_path / "case" / "escape").symlink_to(tmp_path.parent)

    with pytest.raises(ValueError, match="outside the repository"):
        host_confinement._session_descriptor(tmp_path, str(descriptor.relative_to(tmp_path)))


def test_descriptor_cannot_add_a_caller_selected_destination(tmp_path: Path) -> None:
    descriptor = _descriptor(tmp_path, input_destination="/attacker-selected")

    with pytest.raises(host_confinement.HostConfinementError) as refusal:
        host_confinement._session_descriptor(tmp_path, str(descriptor.relative_to(tmp_path)))
    assert refusal.value.code == host_confinement.E_C18_GATE


def test_public_gate_refuses_subject_selected_top_level_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The profile-aware public seam refuses before launcher or result."""

    authorities = {
        name: tmp_path / name
        for name in ("input", "output", "scratch", "subject", "toolchain")
    }
    for authority in authorities.values():
        authority.mkdir()
    subject_worker = authorities["subject"] / ".local" / "subject-worker"
    subject_worker.parent.mkdir()
    subject_worker.write_bytes(b"executable subject calibration\n")
    subject_worker.chmod(0o555)
    toolchain_worker = authorities["toolchain"] / "bin" / "worker"
    toolchain_worker.parent.mkdir()
    toolchain_worker.write_bytes(b"valid fixed toolchain authority\n")
    toolchain_worker.chmod(0o555)

    runtime_profile = tmp_path / "strict-local-v2.json"
    runtime_profile.write_bytes(PROFILE.read_bytes())
    for name in ("host-profile.json", "manifest.json", "launcher"):
        (tmp_path / name).write_bytes(b"present before admission\n")
    qualification = {
        "host_state": {
            "boot_id": "fixture-boot",
            "delegation_identity": {
                "cgroup_relative_path": "/fixture",
                "cgroup_root": str(tmp_path / "cgroup"),
            },
            "lsm": {"securityfs_lsm": "landlock,fixture"},
            "machine_id": "fixture-machine",
            "unprivileged_userns_sysctls": {"fixture": 1},
        },
        "primitives": {
            "landlock": {"abi": 6, "available": True},
            "no_new_privs": True,
            "openat2": True,
            "seccomp_filter": True,
        },
        "qualified": True,
        "schema": "ranex-strict-local-qualification-v1",
    }
    qualification_path = tmp_path / "qualification.json"
    qualification_path.write_bytes(canonical_json_bytes(qualification))
    result_path = tmp_path / "result.json"
    descriptor = {
        "argv": ["/ranex/subject/.local/subject-worker"],
        "environment": {"LC_ALL": "C", "TZ": "UTC"},
        "limits": {
            "cpu_usage_usec": 1_000_000,
            "memory_bytes": 134_217_728,
            "output_bytes": 65_536,
            "output_depth": 8,
            "output_inodes": 32,
            "pids": 16,
            "wall_time_ms": 5_000,
        },
        "_resolved": authorities,
    }

    monkeypatch.setattr(
        host_confinement,
        "_required_host_text",
        lambda _path, _name: "landlock,fixture",
    )
    monkeypatch.setattr(
        host_confinement,
        "_unprivileged_userns_sysctls",
        lambda: {"fixture": 1},
    )
    monkeypatch.setattr(
        host_confinement,
        "_current_cgroup_root",
        lambda: (tmp_path / "cgroup", "/fixture"),
    )
    monkeypatch.setattr(host_confinement, "_probe_openat2", lambda: None)
    monkeypatch.setattr(
        host_confinement,
        "_session_cgroup_parent",
        lambda: tmp_path / "cgroup",
    )

    def launcher_must_not_be_reached(*_args: object) -> object:
        raise AssertionError("launcher validation ran before argv0 authority refusal")

    monkeypatch.setattr(
        host_confinement,
        "_validate_profile_and_objects",
        launcher_must_not_be_reached,
    )
    with pytest.raises(
        host_confinement.HostConfinementError,
        match="worker executable must be under /ranex/toolchain",
    ) as refusal:
        host_confinement.confinement_session(
            tmp_path,
            profile_arg=runtime_profile.name,
            host_profile_arg="host-profile.json",
            artifact_arg="launcher",
            manifest_arg="manifest.json",
            qualification_arg=qualification_path.name,
            descriptor=descriptor,
            result_arg=result_path.name,
        )
    assert refusal.value.code == host_confinement.E_C18_GATE
    assert not result_path.exists()


def test_existing_held_identity_owner_discriminates_path_substitution(
    tmp_path: Path,
) -> None:
    """The v2 implementation must reuse this owner for every held source."""

    source = tmp_path / "input"
    source.mkdir()
    descriptor = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    facts = os.fstat(descriptor)
    opened = host_confinement.OpenedObject(
        descriptor,
        source,
        "unused-for-identity",
        facts.st_uid,
        facts.st_mode & 0o7777,
    )
    try:
        host_confinement._require_same_named_object(
            opened, host_confinement.E_C18_GATE
        )
        source.rename(tmp_path / "held-input")
        source.mkdir()
        with pytest.raises(host_confinement.HostConfinementError) as refusal:
            host_confinement._require_same_named_object(
                opened, host_confinement.E_C18_GATE
            )
        assert refusal.value.code == host_confinement.E_C18_GATE
    finally:
        os.close(descriptor)
