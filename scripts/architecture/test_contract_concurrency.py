#!/usr/bin/env python3
"""Deterministic concurrency regression for contract generation/validation.

The test runs only in a disposable repository copy.  It proves that:

* a validator cannot observe the generator's empty-denominator cleanup window;
* a second generator cannot enter while another publisher owns the lock; and
* publication followed by validation reproduces the same complete tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from contract_tree_lock import LOCK_WAIT_MARKER, contract_tree_lock


ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOTS = (
    Path("architecture/contracts"),
    Path("schemas"),
    Path("docs/architecture/assessments"),
)
PROCESS_TIMEOUT_SECONDS = 180.0


def copy_test_repository(destination: Path) -> None:
    clone = subprocess.run(
        [
            "git",
            "clone",
            "--quiet",
            "--shared",
            "--no-checkout",
            str(ROOT),
            str(destination),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if clone.returncode != 0:
        raise AssertionError(
            "disposable repository clone failed: " + clone.stderr
        )
    for relative in (
        Path("architecture"),
        Path("schemas"),
        Path("docs/architecture"),
        Path("docs/research"),
        Path("legal"),
        Path("scripts/architecture"),
    ):
        shutil.copytree(
            ROOT / relative,
            destination / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


def launch(repository: Path, script_name: str) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [
            sys.executable,
            str(repository / "scripts" / "architecture" / script_name),
        ],
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def finish(process: subprocess.Popen[str], label: str) -> dict[str, Any]:
    stdout, stderr = process.communicate(
        timeout=PROCESS_TIMEOUT_SECONDS
    )
    if process.returncode != 0:
        raise AssertionError(
            f"{label} failed with {process.returncode}: stdout={stdout!r} stderr={stderr!r}"
        )
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise AssertionError(f"{label} produced no JSON result")
    result = json.loads(lines[-1])
    if label.startswith("validator") and result.get("status") != "PASS":
        raise AssertionError(f"{label} did not PASS: {result}")
    return result


def run(repository: Path, script_name: str, label: str) -> tuple[dict[str, Any], float]:
    started = time.monotonic()
    result = finish(launch(repository, script_name), label)
    return result, time.monotonic() - started


def assert_blocked(
    process: subprocess.Popen[str],
    label: str,
    baseline_seconds: float,
) -> None:
    """Prove the process reached the lock and yielded to the holder.

    An earlier revision inferred contention by waiting four baseline durations
    and observing that the process had not exited.  That was sound but paid for
    the proof in wall-clock time, and it degraded quadratically: a slower runner
    produced a slower baseline, which produced a proportionally longer wait.
    Measured, the two waits were 57% of this test's runtime.

    The lock now announces the wait on stderr the moment it finds the lock held
    (``contract_tree_lock.LOCK_WAIT_MARKER``).  Observing that marker is both
    faster and stricter: elapsed time proves only that the process had not
    finished, whereas the marker proves it reached the lock and yielded.

    ``baseline_seconds`` bounds how long to wait for the marker, so a process
    that never reaches the lock still fails rather than hanging.
    """

    assert process.stderr is not None
    stream = process.stderr
    descriptor = stream.fileno()
    timeout_seconds = max(30.0, baseline_seconds * 4.0)
    deadline = time.monotonic() + timeout_seconds
    # A process may announce the wait and then die. Seeing the marker is
    # therefore necessary but not sufficient: re-check liveness after a short
    # settle before declaring the process blocked.
    settle_seconds = 1.0
    seen = ""
    # Non-blocking reads: a blocking readline() would hang past the deadline on
    # a process that neither writes nor exits, converting a failing test into a
    # stalled one.
    os.set_blocking(descriptor, False)
    try:
        while time.monotonic() < deadline:
            try:
                chunk = stream.read()
            except (BlockingIOError, TypeError):
                chunk = None
            if chunk:
                seen += chunk
                if LOCK_WAIT_MARKER in seen:
                    break
                continue
            if process.poll() is not None:
                raise AssertionError(
                    f"{label} bypassed the contract-tree lock: it exited with "
                    f"returncode={process.returncode} without waiting. "
                    f"stderr={seen!r}"
                )
            time.sleep(0.05)
        else:
            process.kill()
            raise AssertionError(
                f"{label} never announced waiting for the contract-tree lock "
                f"within {timeout_seconds:.0f}s; contention was not proven. "
                f"stderr={seen!r}"
            )
    finally:
        os.set_blocking(descriptor, True)
    time.sleep(settle_seconds)
    if process.poll() is not None:
        raise AssertionError(
            f"{label} announced waiting for the contract-tree lock and then "
            f"exited while the lock was still held: "
            f"returncode={process.returncode}"
        )


def generated_tree_digest(repository: Path) -> str:
    aggregate = hashlib.sha256()
    for relative_root in GENERATED_ROOTS:
        root = repository / relative_root
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(repository).as_posix()
            aggregate.update(relative.encode("utf-8"))
            aggregate.update(b"\0")
            aggregate.update(hashlib.sha256(path.read_bytes()).digest())
            aggregate.update(b"\0")
    return aggregate.hexdigest()


def restore_controls(controls: Path, staged_controls: Path) -> None:
    if controls.exists() and not any(controls.iterdir()):
        controls.rmdir()
    if staged_controls.exists() and not controls.exists():
        staged_controls.rename(controls)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="ranex-contract-concurrency.") as tmp:
        repository = Path(tmp) / "ranex"
        copy_test_repository(repository)

        _, generator_seconds = run(
            repository, "generate_contracts.py", "generator baseline"
        )
        _, validator_seconds = run(
            repository, "validate_contracts.py", "validator baseline"
        )
        baseline_digest = generated_tree_digest(repository)

        controls = repository / "docs" / "architecture" / "assessments" / "controls"
        staged_controls = controls.with_name("controls.complete")
        validator = None
        try:
            with contract_tree_lock(repository):
                controls.rename(staged_controls)
                controls.mkdir()
                validator = launch(repository, "validate_contracts.py")
                assert_blocked(
                    validator,
                    "validator during empty-denominator publication window",
                    validator_seconds,
                )
                restore_controls(controls, staged_controls)
        finally:
            restore_controls(controls, staged_controls)
            if validator is not None and validator.poll() is not None:
                validator.communicate()
        if validator is None:
            raise AssertionError("validator contention process was not started")
        finish(validator, "validator after complete-tree restoration")

        writer = None
        with contract_tree_lock(repository):
            writer = launch(repository, "generate_contracts.py")
            assert_blocked(writer, "second generator", generator_seconds)
        finish(writer, "generator after writer-lock release")
        final_validation, _ = run(
            repository, "validate_contracts.py", "validator after second generator"
        )
        final_digest = generated_tree_digest(repository)
        if final_digest != baseline_digest:
            raise AssertionError(
                "concurrent publication changed the deterministic tree: "
                f"{baseline_digest} != {final_digest}"
            )

        print(
            json.dumps(
                {
                    "final_tree_digest": final_digest,
                    "generator_waited_for_writer_lock": True,
                    "status": "PASS",
                    "validator_result": final_validation["status"],
                    "validator_waited_through_empty_denominator": True,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
