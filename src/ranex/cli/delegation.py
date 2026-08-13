"""CLI helpers for headless delegated execution."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from ranex.cli.repository import git
from ranex.cli.subject import materialise_subject, verified_blob_at_path
from ranex.cli.toolchain import ToolchainError, pinned_path_value
from ranex.foundation.suite_results import load_manifest_bytes, parse_results_artifact
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate_text

MODEL_CREDENTIAL_VARIABLE = "OPENROUTER_API_KEY"
BRIDGE_TASK_VARIABLE = "RANEX_TASK_ID"
BRIDGE_EMIT_VARIABLE = "RANEX_EMIT"
SIGNING_KEY_VARIABLE = "RANEX_SIGNING_KEY"
VERDICT_SIGNING_KEY_VARIABLE = "RANEX_VERDICT_SIGNING_KEY"

_OUTPUT_TAIL_LIMIT = 4000


def exec_environment_holds_signing_key() -> bool:
    """Inspect `/proc` for either signing credential, ignoring `os.environ`."""

    data = Path("/proc/self/environ").read_bytes()
    signing_key_variables = {
        SIGNING_KEY_VARIABLE.encode(),
        VERDICT_SIGNING_KEY_VARIABLE.encode(),
    }
    for field in data.split(b"\0"):
        if not field:
            continue
        name = field.split(b"=", 1)[0]
        if name in signing_key_variables:
            return True
    return False


def execute_environment(
    ambient: Mapping[str, str],
    *,
    task_id: str,
    emit: str,
    home: str,
) -> dict[str, str]:
    """Build the child environment for execution from an empty environment."""

    if SIGNING_KEY_VARIABLE in ambient:
        raise ValueError(
            f"refusing to execute with signing credential in ambient: "
            f"{SIGNING_KEY_VARIABLE} was present in the environment"
        )
    if VERDICT_SIGNING_KEY_VARIABLE in ambient:
        raise ValueError(
            f"refusing to execute with signing credential in ambient: "
            f"{VERDICT_SIGNING_KEY_VARIABLE} was present in the environment"
        )
    if MODEL_CREDENTIAL_VARIABLE not in ambient:
        raise ValueError(
            f"refusing to execute without model credential: "
            f"{MODEL_CREDENTIAL_VARIABLE} must be present"
        )

    return {
        "PATH": pinned_path_value(),
        "HOME": home,
        BRIDGE_TASK_VARIABLE: task_id,
        BRIDGE_EMIT_VARIABLE: emit,
        MODEL_CREDENTIAL_VARIABLE: ambient[MODEL_CREDENTIAL_VARIABLE],
    }


def _tail_output(value: str) -> str:
    return value[-_OUTPUT_TAIL_LIMIT:] if len(value) > _OUTPUT_TAIL_LIMIT else value


def _read_emission(path: Path) -> dict[str, str]:
    try:
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError as exc:
        raise ValueError(f"refusing emission: cannot read {path}: {exc}") from exc
    if not lines:
        raise ValueError(f"refusing emission: no lines in {path}")
    payload_line = lines[-1]
    try:
        payload = json.loads(payload_line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"refusing emission: cannot parse JSON from {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"refusing emission: payload at {path} is not an object")

    required = ("task_id", "worktree", "commit")
    for key in required:
        if not isinstance(payload.get(key), str) or not payload[key]:
            raise ValueError(
                f"refusing emission: {path} is missing a valid {key!r}"
            )
    return payload


def _write_outcome(path: Path, outcome: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(outcome) + "\n", encoding="utf-8")


def _run_suite(worktree: Path, commit: str, suite: str) -> tuple[int, str]:
    command = shlex.split(suite)
    if not command:
        raise ValueError("refusing suite command: no arguments")

    with materialise_subject(worktree, commit, git) as materialisation:
        environment = {
            "PATH": pinned_path_value(),
            "HOME": str(materialisation.home),
            "TMPDIR": str(materialisation.temporary),
            "LANG": "C.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
        }
        completed = subprocess.run(
            command,
            check=False,
            cwd=materialisation.tree,
            env=environment,
            capture_output=True,
            text=True,
        )

    combined = f"{completed.stdout or ''}{completed.stderr or ''}"
    return completed.returncode, _tail_output(combined)


def _run_suite_with_results(
    worktree: Path,
    commit: str,
    suite: str,
    *,
    results_artifact: str,
    manifest: dict[str, object],
) -> tuple[int, str, dict[str, object]]:
    """Run against the candidate, reading results before materialisation teardown."""

    command = shlex.split(suite)
    if not command:
        raise ValueError("refusing suite command: no arguments")
    with materialise_subject(worktree, commit, git) as materialisation:
        environment = {
            "PATH": pinned_path_value(),
            "HOME": str(materialisation.home),
            "TMPDIR": str(materialisation.temporary),
            "LANG": "C.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_ATTR_NOSYSTEM": "1",
        }
        completed = subprocess.run(
            command,
            check=False,
            cwd=materialisation.tree,
            env=environment,
            capture_output=True,
            text=True,
        )
        suite_results = parse_results_artifact(
            materialisation.tree / results_artifact,
            manifest,
        )
    combined = f"{completed.stdout or ''}{completed.stderr or ''}"
    return completed.returncode, _tail_output(combined), suite_results


def _run_harness(
    *,
    harness: Path,
    worktree: Path,
    model: str,
    prompt: str,
    timeout: int | float,
    environment: Mapping[str, str],
) -> subprocess.CompletedProcess[str]:
    command = [
        str(harness),
        "--dir",
        str(worktree),
        "--model",
        model,
        "--auto",
        prompt,
    ]

    process = subprocess.Popen(
        command,
        cwd=str(worktree),
        env=environment,
        start_new_session=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    with process:
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            return subprocess.CompletedProcess(
                command,
                process.returncode,
                stdout or "",
                stderr or "",
            )
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
            raise


def cmd_task_delegate(args: argparse.Namespace) -> int:
    """Run a task in a delegated worktree and evaluate the suite against the emission."""

    from ranex.cli.main import EXIT_PASS, EXIT_USAGE  # avoid circular import at module import time

    try:
        if exec_environment_holds_signing_key():
            raise ValueError(
                "refusing to delegate execution while a signing credential "
                "(RANEX_SIGNING_KEY or RANEX_VERDICT_SIGNING_KEY) is present"
            )
        if not os.environ.get(MODEL_CREDENTIAL_VARIABLE):
            raise ValueError(
                f"refusing to delegate execution: {MODEL_CREDENTIAL_VARIABLE} is absent"
            )

        harness = Path(args.harness)
        if (not harness.is_file()) or (not os.access(harness, os.X_OK)):
            raise ValueError(f"refusing harness executable {harness}")

        from ranex.cli.main import (
            Journal,
            _latest_task_dispatch,
            _perform_task_dispatch,
            head_commit,
        )

        worktree = _perform_task_dispatch(
            task_id=args.task_id,
            raw_target=args.target,
            raw_worktree=args.worktree,
            raw_journal=args.journal,
        )

        scratch = Path(tempfile.mkdtemp(prefix="ranex-delegate-"))
        emit = scratch / "emission.jsonl"
        execution_environment = execute_environment(
            os.environ,
            task_id=args.task_id,
            emit=str(emit),
            home=str(scratch),
        )

        try:
            completed = _run_harness(
                harness=harness,
                worktree=worktree,
                model=args.model,
                prompt=args.prompt,
                timeout=args.timeout,
                environment=execution_environment,
            )
        except subprocess.TimeoutExpired as exc:
            timed_out_exit = getattr(exc, "returncode", None)
            _write_outcome(
                Path(args.outcome),
                {
                    "task_id": args.task_id,
                    # null, never 0: no suite ran, and a timeout that records a
                    # zero exit is a pass by omission. Absence blocks.
                    "commit": None,
                    "harness_exit": timed_out_exit if timed_out_exit is not None else -1,
                    "suite_exit": None,
                    "suite_output_tail": "",
                    "suite_results": None,
                    "timed_out": True,
                },
            )
            print(
                f"ERROR  refusing to delegate: timed out after {args.timeout} seconds",
                file=sys.stderr,
            )
            return EXIT_USAGE
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError(f"cannot run harness: {exc}") from exc

        emission = _read_emission(emit)
        dispatch = _latest_task_dispatch(
            Journal(Path(args.journal).resolve()).entries(),
            args.task_id,
        )
        if dispatch is None:
            raise ValueError(f"refusing dispatch for task {args.task_id!r}")
        if emission["task_id"] != args.task_id:
            raise ValueError("refusing task id in emission does not match command task_id")
        recorded_worktree_raw = dispatch.get("worktree")
        if not isinstance(recorded_worktree_raw, str) or not recorded_worktree_raw:
            raise ValueError("refusing worktree does not exist in dispatch record")
        recorded_worktree = Path(recorded_worktree_raw).resolve()
        if Path(emission["worktree"]).resolve() != recorded_worktree:
            raise ValueError(
                f"refusing worktree does not match dispatch for {args.task_id!r}"
            )
        try:
            commit = head_commit(recorded_worktree)
        except ValueError as exc:
            raise ValueError(f"refusing worktree {recorded_worktree} is not readable") from exc
        if emission["commit"] != commit:
            raise ValueError("refusing commit does not match dispatch worktree HEAD")

        base_commit = cast(str, dispatch["base_commit"])
        if emission["commit"] == base_commit:
            raise ValueError("refusing emitted commit matches base commit; there is no subject to judge")

        emitted_tree = git(
            recorded_worktree,
            "rev-parse",
            f"{emission['commit']}^{{tree}}",
        )
        base_tree = git(
            recorded_worktree,
            "rev-parse",
            f"{base_commit}^{{tree}}",
        )
        if emitted_tree.returncode != 0:
            raise ValueError(
                f"refusing cannot determine emitted tree: {emitted_tree.stderr.strip()}"
            )
        if base_tree.returncode != 0:
            raise ValueError(
                f"refusing cannot determine base tree: {base_tree.stderr.strip()}"
            )
        if emitted_tree.stdout.strip() == base_tree.stdout.strip():
            raise ValueError("refusing emitted tree matches base tree; there is no subject to judge")

        suite_results: dict[str, object] | None = None
        gate_catalog = getattr(args, "gate_catalog", None)
        catalog_source = (
            verified_blob_at_path(
                recorded_worktree,
                base_commit,
                gate_catalog,
                git,
            )
            if gate_catalog is not None
            else None
        )
        selected_claim = None
        if catalog_source is not None:
            definition = load_gate_text(
                catalog_source.decode("utf-8"),
                getattr(args, "gate", "landing"),
            )
            claim_id = getattr(args, "claim", "tests-executed")
            selected_claim = next(
                (
                    claim
                    for claim in definition.required_claims
                    if claim.claim_id == claim_id
                ),
                None,
            )
        if selected_claim is not None and selected_claim.results_artifact is not None:
            suite_command = shlex.split(args.suite)
            if tuple(suite_command) != selected_claim.command:
                raise ValueError(
                    "refusing suite command: it does not match the dispatch-time "
                    f"claim {selected_claim.claim_id!r}"
                )
            suite_manifest = getattr(
                args,
                "suite_manifest",
                "governance/suite_manifest.json",
            )
            manifest_source = verified_blob_at_path(
                recorded_worktree,
                base_commit,
                suite_manifest,
                git,
            )
            if manifest_source is None:
                raise ValueError(
                    f"refusing suite: dispatch base carries no manifest at {suite_manifest}"
                )
            manifest = load_manifest_bytes(manifest_source)
            suite_exit, suite_output_tail, suite_results = _run_suite_with_results(
                worktree=recorded_worktree,
                commit=commit,
                suite=args.suite,
                results_artifact=selected_claim.results_artifact,
                manifest=manifest,
            )
        else:
            suite_exit, suite_output_tail = _run_suite(
                worktree=recorded_worktree,
                commit=commit,
                suite=args.suite,
            )
        _write_outcome(
            Path(args.outcome),
            {
                "task_id": args.task_id,
                "commit": commit,
                "harness_exit": completed.returncode,
                "suite_exit": suite_exit,
                "suite_output_tail": suite_output_tail,
                "suite_results": suite_results,
                "timed_out": False,
            },
        )
    except (
        ValueError,
        ToolchainError,
        OSError,
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        KeyError,
        sqlite3.Error,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE
    finally:
        if "scratch" in locals():
            shutil.rmtree(scratch, ignore_errors=True)

    print(
        f"DELEGATED  task={args.task_id}  commit={commit}  "
        f"suite_exit={suite_exit}"
    )
    return EXIT_PASS
