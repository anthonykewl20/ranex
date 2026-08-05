"""Concurrent `task delegate` fan-out helpers."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def _run_one_delegation(
    command: list[str],
    *,
    capture_output: bool,
    text: bool,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=capture_output,
        text=text,
        check=False,
    )


def _load_tasks(path: Path) -> list[dict[str, str]]:
    try:
        lines = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except OSError as exc:
        raise ValueError(f"refusing tasks file {path}: {exc}") from exc
    if not lines:
        raise ValueError(f"refusing tasks file {path}: empty or unreadable")

    tasks: list[dict[str, str]] = []
    task_ids: set[str] = set()
    worktrees: set[str] = set()
    for line_number, payload_line in enumerate(lines, start=1):
        try:
            payload = json.loads(payload_line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"refusing tasks file {path}: cannot parse line {line_number}"
            ) from exc
        if not isinstance(payload, dict):
            raise ValueError(
                f"refusing tasks file {path}: line {line_number} payload is not an object"
            )
        if set(payload.keys()) != {"task_id", "prompt", "worktree"}:
            raise ValueError(
                f"refusing tasks file {path}: line {line_number} must contain exactly "
                "task_id, prompt and worktree"
            )

        task_id = payload["task_id"]
        prompt = payload["prompt"]
        worktree = payload["worktree"]
        if (
            not isinstance(task_id, str)
            or not task_id.strip()
            or (os.path.sep in task_id)
            or (".." in task_id)
            or (os.path.altsep is not None and os.path.altsep in task_id)
        ):
            if not isinstance(task_id, str) or not task_id.strip():
                raise ValueError(
                    f"refusing tasks file {path}: line {line_number}: task_id is missing"
                )
            raise ValueError(
                f"refusing tasks file {path}: line {line_number}: task_id contains path separator"
            )
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(
                f"refusing tasks file {path}: line {line_number}: prompt is missing or blank"
            )
        if not isinstance(worktree, str) or not worktree.strip():
            raise ValueError(
                f"refusing tasks file {path}: line {line_number}: worktree is missing or blank"
            )
        if task_id in task_ids:
            raise ValueError(
                f"refusing tasks file {path}: duplicate task_id {task_id!r} on line {line_number}"
            )
        if worktree in worktrees:
            raise ValueError(
                f"refusing tasks file {path}: duplicate worktree {worktree!r} on line {line_number}"
            )

        task_ids.add(task_id)
        worktrees.add(worktree)
        tasks.append({"task_id": task_id, "prompt": prompt, "worktree": worktree})

    return tasks


def cmd_task_fanout(args: argparse.Namespace) -> int:
    """Run multiple delegations with a bounded pool, preserving in-order reporting."""

    from ranex.cli.main import EXIT_PASS, EXIT_USAGE  # avoid circular import at module import time

    try:
        if args.pool < 1:
            raise ValueError("--pool must be >= 1")
        tasks = _load_tasks(Path(args.tasks))
        task_specs = [
            (task["task_id"], task["prompt"], task["worktree"]) for task in tasks
        ]

        def _task_command(task_id: str, prompt: str, worktree: str) -> list[str]:
            return [
                sys.executable,
                "-m",
                "ranex.cli.main",
                "task",
                "delegate",
                "--task-id",
                task_id,
                "--target",
                str(args.target),
                "--worktree",
                worktree,
                "--journal",
                str(args.journal),
                "--harness",
                str(args.harness),
                "--model",
                args.model,
                "--prompt",
                prompt,
                "--timeout",
                str(args.timeout),
                "--suite",
                args.suite,
                "--gate",
                getattr(args, "gate", "landing"),
                "--claim",
                getattr(args, "claim", "tests-executed"),
                "--gate-catalog",
                getattr(args, "gate_catalog", "governance/gates.yaml"),
                "--suite-manifest",
                getattr(args, "suite_manifest", "governance/suite_manifest.json"),
                "--outcome",
                str(Path(args.outcome_dir) / f"{task_id}.json"),
            ]

        with ThreadPoolExecutor(max_workers=args.pool) as pool:
            futures = [
                pool.submit(
                    _run_one_delegation,
                    _task_command(task_id, prompt, worktree),
                    capture_output=True,
                    text=True,
                )
                for task_id, prompt, worktree in task_specs
            ]
            results = [future.result() for future in futures]

        exit_code = EXIT_PASS
        for task_id, completed in zip(task_specs, results, strict=True):
            print(f"FANOUT  task={task_id[0]}  exit={completed.returncode}")
            if completed.returncode != EXIT_PASS:
                print(completed.stderr, file=sys.stderr)
                exit_code = EXIT_USAGE
    except (OSError, ValueError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    return exit_code
