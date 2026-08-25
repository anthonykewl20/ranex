"""SLICE-070 security freeze for exact-object fixed mount assembly."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT / "native/ranex-worker-launcher/launcher.c"
PROFILE = ROOT / "governance/confinement/strict-local-v2.json"


def _function(source: str, name: str) -> str:
    match = re.search(rf"static [^\n]+\b{name}\([^{{]+\) \{{", source)
    assert match is not None, f"missing launcher function {name}"
    start = match.start()
    opening = source.index("{", match.start())
    depth = 0
    for offset in range(opening, len(source)):
        if source[offset] == "{":
            depth += 1
        elif source[offset] == "}":
            depth -= 1
            if depth == 0:
                return source[start : offset + 1]
    raise AssertionError(f"unterminated launcher function {name}")


def test_profile_pins_descriptor_mount_syscalls_with_no_legacy_fallback() -> None:
    value = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert value["mount_api"] == {
        "attach": {
            "flags": ["MOVE_MOUNT_F_EMPTY_PATH", "MOVE_MOUNT_T_EMPTY_PATH"],
            "from_path": "",
            "syscall": "move_mount",
            "to_path": "",
        },
        "clone": {
            "flags": ["OPEN_TREE_CLONE", "OPEN_TREE_CLOEXEC", "AT_EMPTY_PATH", "AT_RECURSIVE"],
            "path": "",
            "syscall": "open_tree",
        },
        "fallback": "refuse",
        "readonly": {
            "attr_set": ["MOUNT_ATTR_RDONLY"],
            "flags": ["AT_EMPTY_PATH", "AT_RECURSIVE"],
            "path": "",
            "syscall": "mount_setattr",
        },
        "readonly_noexec": {
            "attr_set": ["MOUNT_ATTR_RDONLY", "MOUNT_ATTR_NOEXEC"],
            "attr_set_mask": "0x00000009",
            "flags": ["AT_EMPTY_PATH", "AT_RECURSIVE"],
            "path": "",
            "syscall": "mount_setattr",
        },
        "root": {
            "old_root": "detached",
            "owner": "runtime",
            "pivot": "pivot_root",
            "type": "tmpfs",
        },
    }


def test_v2_subject_is_kernel_noexec_and_not_landlock_execute_authority() -> None:
    """Profile freezes Linux UAPI bits; launcher behavior remains honest RED."""

    linux_mount = Path("/usr/include/linux/mount.h").read_text(encoding="utf-8")
    assert "#define MOUNT_ATTR_RDONLY\t0x00000001" in linux_mount
    assert "#define MOUNT_ATTR_NOEXEC\t0x00000008" in linux_mount
    value = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert value["mounts"]["subject"]["access"] == "read-only-noexec"
    assert value["mounts"]["subject"]["mount_attributes"] == [
        "MOUNT_ATTR_RDONLY",
        "MOUNT_ATTR_NOEXEC",
    ]
    assert value["mount_api"]["readonly_noexec"]["attr_set"] == [
        "MOUNT_ATTR_RDONLY",
        "MOUNT_ATTR_NOEXEC",
    ]
    assert value["mount_api"]["readonly_noexec"]["attr_set_mask"] == "0x00000009"
    assert value["landlock"]["subject_allowed_access"] == [
        "LANDLOCK_ACCESS_FS_READ_FILE",
        "LANDLOCK_ACCESS_FS_READ_DIR",
    ]
    assert "LANDLOCK_ACCESS_FS_EXECUTE" not in value["landlock"][
        "subject_allowed_access"
    ]

    source = LAUNCHER.read_text(encoding="utf-8")
    assembly = _function(source, "assemble_mounts")
    assert "MOUNT_ATTR_NOEXEC" in assembly
    assert "subject_allowed_access" in source
    assert "LANDLOCK_ACCESS_FS_EXECUTE" not in _function(
        source, "v2_subject_allowed_access"
    )


def test_v1_landlock_subject_execute_policy_remains_unchanged() -> None:
    """The additive v2 branch cannot silently narrow the existing v1 ABI."""

    source = LAUNCHER.read_text(encoding="utf-8")
    v1 = _function(source, "enforce_landlock")
    assert "const __u64 readonly_access = LANDLOCK_ACCESS_FS_EXECUTE |" in v1
    assert "add_path_rule(ruleset_fd, subject_fd, readonly_access)" in v1
    assert "add_path_rule(ruleset_fd, toolchain_fd, readonly_access)" in v1


def test_launcher_clones_held_objects_and_attaches_to_held_fixed_targets() -> None:
    """RED: no source or destination path may be re-resolved for the bind."""

    source = LAUNCHER.read_text(encoding="utf-8")
    assembly = _function(source, "assemble_mounts")
    for token in (
        "SYS_open_tree",
        "OPEN_TREE_CLONE | OPEN_TREE_CLOEXEC | AT_EMPTY_PATH | AT_RECURSIVE",
        "SYS_mount_setattr",
        "MOUNT_ATTR_RDONLY",
        "SYS_move_mount",
        "MOVE_MOUNT_F_EMPTY_PATH | MOVE_MOUNT_T_EMPTY_PATH",
        '"/ranex/input"',
        '"/ranex/toolchain"',
        '"/ranex/output"',
        '"/ranex/scratch"',
        '"/ranex/subject"',
        "pivot_root",
        "MNT_DETACH",
    ):
        assert token in assembly
    assert "mount(path, path" not in assembly


def test_worker_cannot_mount_or_reopen_a_hidden_authority_channel() -> None:
    """The setup syscalls are launcher-only and absent after seccomp enters."""

    source = LAUNCHER.read_text(encoding="utf-8")
    seccomp = _function(source, "enforce_seccomp")
    for forbidden in (
        "__NR_mount",
        "__NR_umount2",
        "__NR_pivot_root",
        "__NR_open_tree",
        "__NR_move_mount",
        "__NR_mount_setattr",
    ):
        assert forbidden not in seccomp
    worker = _function(source, "worker_exec")
    assert "(void)close(0);" in worker
    assert "close_worker_descriptors" in worker
    assert 'environment_names = {"LC_ALL", "TZ"}' in worker


def test_fixed_destination_vocabulary_has_no_predecessor_namespace() -> None:
    """SLICE-036 C is ordered after A/B but consumes no predecessor bytes."""

    value = json.loads(PROFILE.read_text(encoding="utf-8"))
    encoded = json.dumps(value, sort_keys=True)
    assert "/ranex/predecessor" not in encoded
    assert value["worker_io"]["predecessor_inputs"] == "none"


def test_dynamic_runtime_closure_is_explicitly_unsupported() -> None:
    """Initial v2 cannot silently inherit a host loader or runtime."""

    value = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert value["worker_executable"] == {
        "dynamic_runtime_closure": "unsupported-refuse",
        "required_linkage": "self-contained-static",
        "source": "descriptor-held-toolchain-object",
    }
