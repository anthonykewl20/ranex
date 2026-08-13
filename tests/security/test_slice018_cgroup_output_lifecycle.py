"""Frozen adversarial contract for SLICE-018 lifecycle ownership.

These tests intentionally name the future service API.  They collect cleanly
against the shipped SLICE-017 tree and fail because that API/profile is absent.
They become read-only after the red freeze commit.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
from pathlib import Path

import pytest

from ranex.cli import host_confinement
from ranex.foundation import atomic_writer


REPOSITORY = Path(__file__).resolve().parents[2]
RUNTIME_PROFILE = REPOSITORY / "governance/confinement/strict-local-v1.json"
MAIN = REPOSITORY / "src/ranex/cli/main.py"
ADR = REPOSITORY / "docs/adr/ADR-006-landlock-confinement-of-the-bound-command.md"
MAIN_SHA256 = "4f29feb1c486fcd2600253db912d87069d946151b1924da89301ace0d7be3e14"


def test_gate3_lifecycle_service_owns_real_cgroup_kill_drain_and_removal() -> None:
    service = getattr(host_confinement, "ConfinementSession", None)
    assert service is not None
    methods = {
        name for name, value in inspect.getmembers(service) if callable(value)
    }
    assert {
        "create_worker_cgroup",
        "enroll_and_read_back",
        "release_start_gate",
        "kill_drain_remove",
    } <= methods


@pytest.mark.parametrize(
    "attack,refusal",
    [
        pytest.param("gate-release-before-enrollment", "E-C18-GATE", id="gate-race"),
        pytest.param("limit-readback-forgery", "E-C18-CGROUP-READBACK", id="readback-forgery"),
        pytest.param("threaded-worker", "E-C18-CGROUP-THREADED", id="threaded-escape"),
        pytest.param("delegation-fd-stale", "E-C18-DELEGATION-STALE", id="stale-delegation"),
        pytest.param("drain-read-error", "E-C18-DRAIN", id="drain-read-error"),
    ],
)
def test_gate4_gate_and_readback_attacks_have_closed_refusals(
    attack: str, refusal: str
) -> None:
    table = getattr(host_confinement, "LIFECYCLE_ATTACK_REFUSALS", None)
    assert isinstance(table, dict)
    assert table.get(attack) == refusal


@pytest.mark.parametrize(
    "limit,event",
    [
        pytest.param("cpu_usage_usec", "cpu.stat", id="cpu"),
        pytest.param("memory_bytes", "memory.events", id="memory"),
        pytest.param("pids", "pids.events", id="pids"),
        pytest.param("wall_time_ms", "cgroup.kill", id="wall"),
        pytest.param("output_bytes", "output.bytes", id="output-bytes"),
        pytest.param("output_inodes", "output.inodes", id="output-inodes"),
    ],
)
def test_gate5_every_bound_is_monitored_as_a_whole_tree_fact(
    limit: str, event: str
) -> None:
    monitored = getattr(host_confinement, "SESSION_LIMIT_READBACKS", None)
    assert isinstance(monitored, dict)
    assert monitored.get(limit) == event


def test_gate6_output_collection_is_held_dirfd_bounded_and_post_drain() -> None:
    collector = getattr(host_confinement, "collect_drained_output", None)
    assert collector is not None
    signature = inspect.signature(collector)
    assert list(signature.parameters) == ["output_dirfd", "limits", "drain_readback"]
    source = inspect.getsource(collector)
    for required in (
        "RESOLVE_BENEATH",
        "RESOLVE_NO_SYMLINKS",
        "RESOLVE_NO_MAGICLINKS",
        "populated 0",
        "st_nlink",
    ):
        assert required in source


@pytest.mark.parametrize(
    "kind",
    [
        pytest.param("symlink", id="symlink"),
        pytest.param("magic-link", id="magic-link"),
        pytest.param("device", id="device"),
        pytest.param("fifo", id="fifo"),
        pytest.param("socket", id="socket"),
        pytest.param("hardlink", id="hardlink"),
        pytest.param("replacement-race", id="replacement-race"),
        pytest.param("depth", id="depth"),
    ],
)
def test_gate6_every_unsafe_output_kind_is_an_explicit_refusal(kind: str) -> None:
    refusals = getattr(host_confinement, "UNSAFE_OUTPUT_REFUSALS", None)
    assert isinstance(refusals, frozenset)
    assert kind in refusals


def test_gate9_surface_has_no_cmd_run_evidence_or_signing_path() -> None:
    parser = host_confinement._parser()
    subparser_action = next(
        action
        for action in parser._actions
        if isinstance(action, __import__("argparse")._SubParsersAction)
    )
    session = subparser_action.choices["session"]
    options = {
        option
        for action in session._actions
        for option in action.option_strings
    }
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
    assert not {"--sign", "--signing-key", "--evidence", "--claim"} & options
    assert hashlib.sha256(MAIN.read_bytes()).hexdigest() == MAIN_SHA256
    assert "**Status:** proposed" in ADR.read_text(encoding="utf-8")


def test_gate10_host_directory_walker_is_only_a_foundation_delegation() -> None:
    tree = ast.parse(inspect.getsource(host_confinement._open_created_directory))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call.func, ast.Attribute)
    assert isinstance(call.func.value, ast.Name)
    assert (call.func.value.id, call.func.attr) == (
        "atomic_writer",
        "_open_created_directory",
    )
    assert callable(atomic_writer._open_created_directory)


def test_gate8_runtime_profile_exists_as_canonical_closed_json() -> None:
    raw = RUNTIME_PROFILE.read_bytes()
    value = json.loads(raw)
    assert raw == json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()
    assert value["schema"] == "ranex-strict-local-runtime-v1"
