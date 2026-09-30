"""SLICE-102 — acceptance task loop: real CLI refusals (#95 vocabulary).

Arms exercise the installed argparse surface and fail-closed refusals without
Docker. Live Docker qualification is tools/dogfood/acceptance_task_proof.py
(opt-in RANEX_LIVE_TASK_EXPERIMENT=1). Statuses asserted here are VERIFIED
refusals — never PASS borrowed from a model.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.signing import generate_keypair
from ranex.foundation.specification_abc import canonical_payload_bytes

KERNEL = Path(__file__).resolve().parents[2]


def invoke(*args: object, key: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "GIT_", "PYTHON", "COVERAGE_"))
    }
    environment["PYTHONPATH"] = str(KERNEL / "src")
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *map(str, args)],
        cwd=KERNEL,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def test_help_surfaces_task_commands() -> None:
    """Positive: public CLI names the task loop. Negative: no silent alias."""
    help_text = invoke("specification", "--help").stdout
    for name in ("approve-task", "build-task", "reapprove-task", "land-task", "observe-http"):
        assert name in help_text
    prove = invoke("prove", "--help")
    assert prove.returncode == 0 and "--task" in prove.stdout
    # Negative: a fake command is refused, not silently remapped.
    missing = invoke("specification", "approve-task-fake")
    assert missing.returncode == 2
    assert "invalid choice" in missing.stderr or "unrecognized" in missing.stderr.lower() or missing.returncode != 0


def test_prove_and_land_refuse_absent_task_directory(tmp_path: Path) -> None:
    """VERIFIED refusal: no caller-supplied report path invents a task."""
    absent = tmp_path / "no-such-task"
    for argv in (("prove", "--task", absent), ("specification", "land-task", "--task", absent)):
        result = invoke(*argv)
        assert result.returncode == 2
        assert "E-TASK-" in result.stderr
        assert not absent.exists()


def test_approve_task_refuses_unsigned_and_committable_state(tmp_path: Path) -> None:
    """Negative controls before any live observer process starts."""
    # Minimal fake bundle is enough for path/signature refusals; pin check is deeper.
    state_inside = KERNEL / "governance" / "would-be-task-state"
    private, _ = generate_keypair()
    key = tmp_path / "owner.key"
    key.write_text(private, encoding="utf-8")
    key.chmod(0o600)
    unsigned = invoke(
        "specification",
        "approve-task",
        "--bundle",
        tmp_path / "missing-bundle",
        "--manifest-digest",
        "sha256:" + "0" * 64,
        "--worker-profile",
        "acceptance/worker.json",
        "--state",
        tmp_path / "external-state",
    )
    assert unsigned.returncode == 2 and "E-TASK-" in unsigned.stderr
    # State inside the governed tree must refuse (committable).
    inside = invoke(
        "specification",
        "approve-task",
        "--bundle",
        tmp_path / "missing-bundle",
        "--manifest-digest",
        "sha256:" + "0" * 64,
        "--worker-profile",
        "acceptance/worker.json",
        "--state",
        state_inside,
        key=key,
    )
    assert inside.returncode == 2 and "E-TASK-" in inside.stderr
    assert not state_inside.exists()
    # Keep payload helper available for future golden expansions.
    assert json.loads(canonical_payload_bytes({"ok": True}).decode())["ok"] is True


@pytest.mark.skipif(
    os.environ.get("RANEX_LIVE_TASK_EXPERIMENT") != "1",
    reason=(
        "ranex-context:live-task-experiment: requires RANEX_LIVE_TASK_EXPERIMENT=1 "
        "and local Docker images"
    ),
)
def test_live_acceptance_task_experiment_matches(tmp_path: Path) -> None:
    output = tmp_path / "live"
    result = subprocess.run(
        [
            sys.executable,
            str(KERNEL / "tools/dogfood/acceptance_task_proof.py"),
            "--output",
            str(output),
        ],
        cwd=KERNEL,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["status"] == "EXPERIMENT-MATCH"
    cases = summary.get("cases") or []
    assert cases, "proof must retain #95 vocabulary cases"
    assert all(case["status"] == "VERIFIED" for case in cases)
