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
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from contract_tree_lock import contract_tree_lock


ROOT = Path(__file__).resolve().parents[2]
GENERATED_ROOTS = (
    Path("architecture/contracts"),
    Path("schemas"),
    Path("docs/architecture/assessments"),
)


def copy_test_repository(destination: Path) -> None:
    for relative in (
        Path("architecture"),
        Path("schemas"),
        Path("docs/architecture"),
        Path("scripts/architecture"),
    ):
        shutil.copytree(
            ROOT / relative,
            destination / relative,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    research_inputs = (
        Path("docs/research/engineering-reference-practice-registry.json"),
        Path("docs/research/ranex-architecture-practice-application-profile.json"),
    )
    for research_input in research_inputs:
        (destination / research_input.parent).mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / research_input, destination / research_input)


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
    stdout, stderr = process.communicate(timeout=30)
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
    # Four baseline durations (and never less than two seconds) distinguish
    # lock contention from normal interpreter/schema startup without relying
    # on a generator timing hook.
    probe_seconds = max(2.0, baseline_seconds * 4.0)
    try:
        stdout, stderr = process.communicate(timeout=probe_seconds)
    except subprocess.TimeoutExpired:
        return
    raise AssertionError(
        f"{label} bypassed the contract-tree lock: "
        f"returncode={process.returncode} stdout={stdout!r} stderr={stderr!r}"
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
