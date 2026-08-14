"""Frozen behavioural attack contract for SLICE-018 lifecycle ownership."""

from __future__ import annotations

import argparse
import os
import socket
import stat
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from ranex.cli import host_confinement

REPOSITORY = Path(__file__).resolve().parents[2]
ADR = REPOSITORY / "docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md"


def _refusal_code(operation: Callable[[], Any]) -> str:
    """Execute an attack and require a closed refusal, not a truthy sentinel."""

    try:
        outcome = operation()
    except Exception as exc:  # the implementation owns its typed refusal class
        code = getattr(exc, "code", None)
        assert isinstance(code, str) and code.startswith("E-C18-"), repr(exc)
        return code
    assert isinstance(outcome, dict), "attack returned success/None instead of a refusal"
    assert set(outcome) >= {"refusal"}
    code = outcome["refusal"]
    assert isinstance(code, str) and code.startswith("E-C18-")
    return code


def _session_for_state_tests(tmp_path: Path) -> Any:
    service = getattr(host_confinement, "ConfinementSession", None)
    assert service is not None, "ConfinementSession lifecycle service is absent"
    start_read, start_write = os.pipe()
    os.close(start_read)
    session = service(worker_cgroup=tmp_path / "worker", start_gate_fd=start_write)
    return session


def test_gate4_releasing_start_gate_before_enrollment_is_refused(tmp_path: Path) -> None:
    session = _session_for_state_tests(tmp_path)
    try:
        assert _refusal_code(session.release_start_gate) == "E-C18-GATE"
    finally:
        os.close(session.start_gate_fd)


def test_gate4_forged_worker_enrollment_readback_is_refused(tmp_path: Path) -> None:
    session = _session_for_state_tests(tmp_path)
    try:
        code = _refusal_code(
            lambda: session.enroll_and_read_back(worker_pid=4123, readback="9999\n")
        )
        assert code == "E-C18-CGROUP-READBACK"
    finally:
        os.close(session.start_gate_fd)


@pytest.mark.parametrize(
    "limit,observed",
    [
        pytest.param("cpu_usage_usec", {"cpu_usage_usec": 101}, id="cpu"),
        pytest.param("memory_bytes", {"memory.events.max": 1}, id="memory"),
        pytest.param("pids", {"pids.events.max": 1}, id="pids"),
        pytest.param("wall_time_ms", {"wall_time_ms": 101}, id="wall"),
        pytest.param("output_bytes", {"output_bytes": 101}, id="output-bytes"),
        pytest.param("output_inodes", {"output_inodes": 101}, id="output-inodes"),
    ],
)
def test_gate5_exceeded_bound_kills_tree_and_refuses_result(
    tmp_path: Path, limit: str, observed: dict[str, int]
) -> None:
    session = _session_for_state_tests(tmp_path)
    session.enrolled_worker_pid = 4123
    session.limits = {limit: 100}
    try:
        code = _refusal_code(lambda: session.observe_limits(observed))
        assert code == "E-C18-LIMIT"
        assert session.cgroup_kill_written is True
        assert session.result_published is False
    finally:
        os.close(session.start_gate_fd)


def test_gate6_collecting_before_drain_is_refused(tmp_path: Path) -> None:
    collector = getattr(host_confinement, "collect_drained_output", None)
    assert callable(collector), "bounded output collector is absent"
    output = tmp_path / "output"
    output.mkdir()
    (output / "safe.txt").write_text("must not be collected", encoding="utf-8")
    fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
    try:
        code = _refusal_code(lambda: collector(fd, _output_limits(), {"populated": 1}))
    finally:
        os.close(fd)
    assert code == "E-C18-DRAIN"


def _output_limits(**changes: int) -> dict[str, int]:
    limits = {"output_bytes": 8 * 1024 * 1024, "output_inodes": 32, "output_depth": 8}
    limits.update(changes)
    return limits


def _collect(root: Path, limits: dict[str, int] | None = None) -> Any:
    collector = getattr(host_confinement, "collect_drained_output", None)
    assert callable(collector), "bounded output collector is absent"
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        return collector(fd, limits or _output_limits(), {"populated": 0})
    finally:
        os.close(fd)


def _make_output_attack(root: Path, kind: str) -> Callable[[], None]:
    target = root.parent / "secret"
    target.write_text("secret outside output", encoding="utf-8")
    cleanups: list[Callable[[], None]] = []
    if kind == "symlink":
        (root / "attack").symlink_to(target)
    elif kind == "magic-link":
        target_fd = os.open(target, os.O_RDONLY)
        cleanups.append(lambda: os.close(target_fd))
        (root / "attack").symlink_to(f"/proc/self/fd/{target_fd}")
    elif kind == "device":
        os.mknod(root / "attack", stat.S_IFCHR | 0o600, os.makedev(1, 3))
    elif kind == "fifo":
        os.mkfifo(root / "attack")
    elif kind == "socket":
        listener = socket.socket(socket.AF_UNIX)
        listener.bind(str(root / "attack"))
        cleanups.append(listener.close)
    elif kind == "hardlink-exceed":
        original = root / "original"
        original.write_text("same inode", encoding="utf-8")
        os.link(original, root / "attack")
    elif kind == "inode-excess":
        for number in range(3):
            (root / f"file-{number}").write_text(str(number), encoding="utf-8")
    else:  # pragma: no cover - the parameter table is closed
        raise AssertionError(kind)

    def cleanup() -> None:
        for close in reversed(cleanups):
            close()

    return cleanup


@pytest.mark.parametrize(
    "kind,limits",
    [
        pytest.param("symlink", _output_limits(), id="symlink"),
        pytest.param("magic-link", _output_limits(), id="magic-link-proc-self-fd"),
        pytest.param("device", _output_limits(), id="device-node"),
        pytest.param("fifo", _output_limits(), id="fifo"),
        pytest.param("socket", _output_limits(), id="socket"),
        pytest.param("hardlink-exceed", _output_limits(), id="hardlink-exceed"),
        pytest.param("inode-excess", _output_limits(output_inodes=2), id="inode-excess"),
    ],
)
def test_gate6_constructed_output_attacks_are_refused(
    tmp_path: Path, kind: str, limits: dict[str, int]
) -> None:
    if kind == "device":
        probe = tmp_path / "cap-mknod-probe"
        try:
            os.mknod(probe, stat.S_IFCHR | 0o600, os.makedev(1, 3))
        except PermissionError:
            pytest.skip(
                "CAP_MKNOD unavailable — device-node output-tamper refusal is host-unverified"
            )
        finally:
            probe.unlink(missing_ok=True)
    output = tmp_path / "output"
    output.mkdir()
    cleanup = _make_output_attack(output, kind)
    try:
        code = _refusal_code(lambda: _collect(output, limits))
    finally:
        cleanup()
    assert code in {"E-C18-OUTPUT-UNSAFE", "E-C18-OUTPUT-BOUND"}


def test_gate6_replacement_during_collection_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    victim = output / "victim"
    victim.write_bytes(b"a" * (4 * 1024 * 1024))
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"b" * (4 * 1024 * 1024))
    replaced = False
    original_read = os.read

    def replace_inside_read_window(descriptor: int, count: int) -> bytes:
        nonlocal replaced
        if not replaced:
            # collect_drained_output reaches os.read only after it has opened
            # victim and verified its dev/ino (host_confinement.py:1129-1132).
            # Replacing the name here therefore deterministically exercises the
            # post-read name-identity check, rather than racing a scheduler.
            os.replace(replacement, victim)
            replaced = True
        return original_read(descriptor, count)

    monkeypatch.setattr(host_confinement.os, "read", replace_inside_read_window)
    code = _refusal_code(lambda: _collect(output))
    assert replaced, "collector never opened a file read window"
    assert code == "E-C18-OUTPUT-RACE"


def _delegated_cgroup() -> tuple[Path | None, str | None]:
    try:
        cgroup_line = next(
            line for line in Path("/proc/self/cgroup").read_text().splitlines() if "::" in line
        )
        root = Path("/sys/fs/cgroup") / cgroup_line.split("::", 1)[1].lstrip("/")
        controllers = set((root / "cgroup.controllers").read_text().split())
    except (OSError, StopIteration):
        return None, "cgroup-v2 delegation cannot be inspected"
    missing = sorted({"cpu", "memory", "pids"} - controllers)
    if missing:
        return None, "delegated cgroup lacks controllers: " + ", ".join(missing)
    if not os.access(root, os.W_OK):
        return None, "delegated cgroup-v2 root is not writable"
    return root, None


def _require_delegated_cgroup() -> Path:
    root, limitation = _delegated_cgroup()
    if limitation is not None:
        pytest.skip(f"SLICE-018 host qualification unavailable: {limitation}")
    assert root is not None
    return root


def test_gate3_fork_double_fork_and_setsid_cannot_escape_session_cgroup(tmp_path: Path) -> None:
    cgroup_parent = _require_delegated_cgroup()
    service = getattr(host_confinement, "ConfinementSession", None)
    assert service is not None, "ConfinementSession lifecycle service is absent"
    outcome = service.run_cgroup_attack(
        attack="fork-double-fork-setsid", cgroup_parent=cgroup_parent, scratch=tmp_path
    )
    assert outcome["all_observed_pids_owned"] is True
    assert set(outcome["observed_pids"]) <= set(outcome["cgroup_procs"])
    assert outcome["pid_namespace_escape"] is False


def test_gate3_kill_drain_remove_is_total_under_worker_exit_race(tmp_path: Path) -> None:
    cgroup_parent = _require_delegated_cgroup()
    service = getattr(host_confinement, "ConfinementSession", None)
    assert service is not None, "ConfinementSession lifecycle service is absent"
    outcome = service.run_cgroup_attack(
        attack="kill-drain-worker-exit-race",
        cgroup_parent=cgroup_parent,
        scratch=tmp_path,
    )
    assert outcome["worker_reaped"] is True
    assert outcome["populated"] == 0
    assert outcome["cgroup_removed"] is True


def test_gate9_surface_has_no_cmd_run_evidence_or_signing_path() -> None:
    parser = host_confinement._parser()
    subparser_action = next(
        action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
    )
    session = subparser_action.choices["session"]
    options = {option for action in session._actions for option in action.option_strings}
    assert options == {
        "-h",
        "--help",
        "--profile",
        "--host-profile",
        "--artifact",
        "--manifest",
        "--qualification",
        "--descriptor",
        "--result",
    }
    assert "**Status:** accepted" in ADR.read_text(encoding="utf-8")


def test_gate10_host_directory_walker_preserves_foundation_behavior(tmp_path: Path) -> None:
    walker = host_confinement._open_created_directory
    target = tmp_path / "one/two"
    fd = walker(tmp_path, target)
    os.close(fd)
    assert target.is_dir()
    (tmp_path / "linked").symlink_to(tmp_path / "one")
    with pytest.raises(OSError):
        walker(tmp_path, tmp_path / "linked/escape")
