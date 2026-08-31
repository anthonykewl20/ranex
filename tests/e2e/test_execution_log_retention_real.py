"""Issue #58 acceptance tests for retained execution logs using real processes."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from ranex.foundation.canonical import canonical_json_bytes

REPOSITORY = Path(__file__).resolve().parents[2]
STREAM_NAMES = (
    "harness.stdout",
    "harness.stderr",
    "suite.stdout",
    "suite.stderr",
)
TRUNCATION = re.compile(
    r"^\[ranex truncated: policy=tail dropped=(\d+) retained=(\d+) original=(\d+)\]$"
)


def _environment(home: Path) -> dict[str, str]:
    """Supply a clean, real CLI environment for each disposable target."""

    return {
        "HOME": str(home),
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(REPOSITORY / "src"),
    }


def _git(target: Path, home: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(target), *arguments],
        capture_output=True,
        check=False,
        env=_environment(home),
        text=True,
    )


@pytest.fixture
def real_target(tmp_path: Path) -> tuple[Path, Path]:
    """A committed git target that delegate can dispatch into for real."""

    home = tmp_path / "home"
    home.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    initialized = subprocess.run(
        ["git", "init", "-q", str(target)],
        capture_output=True,
        check=False,
        env=_environment(home),
        text=True,
    )
    assert initialized.returncode == 0, initialized.stderr
    for name, value in (
        ("user.email", "execution-logs@example.invalid"),
        ("user.name", "Execution Logs"),
    ):
        configured = _git(target, home, "config", name, value)
        assert configured.returncode == 0, configured.stderr
    (target / "base.txt").write_text("base\n", encoding="utf-8")
    added = _git(target, home, "add", "base.txt")
    assert added.returncode == 0, added.stderr
    committed = _git(target, home, "commit", "-q", "-m", "base")
    assert committed.returncode == 0, committed.stderr
    return target, home


def _harness(
    path: Path, *, failure_task_id: str | None = None, timeout: bool = False
) -> Path:
    """Build a real shell harness that commits and emits its dispatched HEAD."""

    ending = ""
    if timeout:
        ending = "sleep 4\n"
    elif failure_task_id is not None:
        ending = (
            f"if [ \"$RANEX_TASK_ID\" = \"{failure_task_id}\" ]; then\n"
            "  printf '%s\\n' 'HARNESS FAILURE banner' >&2\n"
            "  exit 1\n"
            "fi\n"
        )
    body = f"""#!/usr/bin/env sh
set -eu
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dir)
      worktree="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done
printf '%s\\n' 'HARNESS STDOUT: issue-58 operator banner'
printf '%s\\n' 'HARNESS STDERR: issue-58 operator banner' >&2
printf '%s\\n' 'real harness work' > "$worktree/agent.txt"
git -C "$worktree" add agent.txt
git -C "$worktree" -c user.email=harness@example.invalid -c user.name=Harness commit -q -m 'real harness work'
commit=$(git -C "$worktree" rev-parse HEAD)
printf '{{"task_id":"%s","worktree":"%s","commit":"%s"}}\\n' "$RANEX_TASK_ID" "$worktree" "$commit" > "$RANEX_EMIT"
{ending}"""
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _delegate(
    *,
    target: Path,
    home: Path,
    task_id: str,
    worktree: Path,
    journal: Path,
    harness: Path,
    outcome: Path,
    suite: str = "/usr/bin/true",
    timeout: int = 30,
    log_max_bytes: int | None = None,
    retention: str | None = None,
) -> subprocess.CompletedProcess[str]:
    argv = [
        sys.executable,
        "-m",
        "ranex.cli.main",
        "task",
        "delegate",
        "--task-id",
        task_id,
        "--target",
        str(target),
        "--worktree",
        str(worktree),
        "--journal",
        str(journal),
        "--harness",
        str(harness),
        "--model",
        "ranex-noop/noop",
        "--prompt",
        "perform the real issue-58 acceptance work",
        "--timeout",
        str(timeout),
        "--suite",
        suite,
        "--outcome",
        str(outcome),
    ]
    if log_max_bytes is not None:
        argv.extend(["--log-max-bytes", str(log_max_bytes)])
    if retention is not None:
        argv.extend(["--log-retention", retention])
    return subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=target,
        env=_environment(home),
        text=True,
    )


def _read_canonical_json(path: Path) -> dict[str, Any]:
    assert path.exists()
    contents = path.read_bytes()
    payload = json.loads(contents)
    assert isinstance(payload, dict)
    assert contents == canonical_json_bytes(payload) + b"\n"
    return payload


def _assert_retained_bundle(
    directory: Path,
    streams: object,
    expected_names: tuple[str, ...] = STREAM_NAMES,
) -> None:
    """Verify a retained bundle against its manifest and exact stored bytes."""

    assert directory.exists()
    assert directory.is_dir()
    assert isinstance(streams, dict)
    assert set(streams) == set(expected_names)
    expected_files = {f"{name}.log" for name in expected_names} | {"manifest.json"}
    assert {path.name for path in directory.iterdir()} == expected_files
    for name in expected_names:
        entry = streams[name]
        assert isinstance(entry, dict)
        filename = entry["file"]
        assert isinstance(filename, str)
        stream_path = directory / filename
        assert stream_path.exists()
        contents = stream_path.read_bytes()
        assert entry["bytes"] == len(contents)
        assert entry["sha256"] == "sha256:" + hashlib.sha256(contents).hexdigest()
        assert stat.S_IMODE(stream_path.stat().st_mode) == 0o444

    manifest_path = directory / "manifest.json"
    assert manifest_path.exists()
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    assert manifest_bytes == canonical_json_bytes(manifest) + b"\n"
    assert manifest["streams"] == streams
    assert stat.S_IMODE(manifest_path.stat().st_mode) == 0o444


def _assert_outcome_logs(outcome: Path) -> dict[str, Any]:
    payload = _read_canonical_json(outcome)
    assert stat.S_IMODE(outcome.stat().st_mode) == 0o444
    logs = payload["logs"]
    assert isinstance(logs, dict)
    assert logs["version"] == 1
    directory_name = logs["dir"]
    assert isinstance(directory_name, str)
    streams = logs["streams"]
    _assert_retained_bundle(outcome.parent / directory_name, streams)
    return payload


def _failure_suite(*, filler: bool) -> str:
    if filler:
        return (
            "/bin/sh -c 'i=0; while [ \"$i\" -lt 5000 ]; do "
            "printf x >&2; i=$((i + 1)); done; "
            "printf " + "\"\\nFINAL: suite failed because the world is broken\\n\"" + " >&2; exit 1'"
        )
    return "/bin/sh -c 'printf " + "\"FINAL: suite failed because the world is broken\\n\"" + " >&2; exit 1'"


def test_real_delegate_success_retains_operator_readable_streams(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    outcome = tmp_path / "ok.json"
    result = _delegate(
        target=target,
        home=home,
        task_id="T-58-OK",
        worktree=tmp_path / "worktree-ok",
        journal=tmp_path / "journal.sqlite3",
        harness=_harness(tmp_path / "harness-ok.sh"),
        outcome=outcome,
    )

    assert result.returncode == 0, result.stderr
    payload = _assert_outcome_logs(outcome)
    logs = payload["logs"]
    assert isinstance(logs, dict)
    assert logs["version"] == 1
    streams = logs["streams"]
    assert isinstance(streams, dict)
    for name in STREAM_NAMES:
        entry = streams[name]
        assert isinstance(entry, dict)
        assert isinstance(entry["bytes"], int)
        assert entry["bytes"] >= 0
    directory = outcome.parent / str(logs["dir"])
    stdout_path = directory / "harness.stdout.log"
    assert stdout_path.exists()
    assert "HARNESS STDOUT: issue-58 operator banner" in stdout_path.read_text(
        encoding="utf-8"
    )


def test_real_delegate_failure_preserves_terminal_reason_and_truncates_explicitly(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    journal = tmp_path / "journal.sqlite3"
    harness = _harness(tmp_path / "harness.sh")
    ordinary = tmp_path / "ordinary-failure.json"
    first = _delegate(
        target=target,
        home=home,
        task_id="T-58-FAIL-ORDINARY",
        worktree=tmp_path / "worktree-ordinary",
        journal=journal,
        harness=harness,
        outcome=ordinary,
        suite=_failure_suite(filler=False),
    )

    assert first.returncode == 0, first.stderr
    ordinary_payload = _assert_outcome_logs(ordinary)
    assert ordinary_payload["suite_exit"] != 0
    ordinary_logs = ordinary_payload["logs"]
    assert isinstance(ordinary_logs, dict)
    ordinary_stderr = ordinary.parent / str(ordinary_logs["dir"]) / "suite.stderr.log"
    assert ordinary_stderr.exists()
    assert ordinary_stderr.read_text(encoding="utf-8").splitlines()[-1] == (
        "FINAL: suite failed because the world is broken"
    )

    capped = tmp_path / "capped-failure.json"
    second = _delegate(
        target=target,
        home=home,
        task_id="T-58-FAIL-CAPPED-1",
        worktree=tmp_path / "worktree-capped-1",
        journal=journal,
        harness=harness,
        outcome=capped,
        suite=_failure_suite(filler=True),
        log_max_bytes=4096,
    )
    assert second.returncode == 0, second.stderr
    capped_payload = _assert_outcome_logs(capped)
    capped_logs = capped_payload["logs"]
    assert isinstance(capped_logs, dict)
    capped_stderr = capped.parent / str(capped_logs["dir"]) / "suite.stderr.log"
    assert capped_stderr.exists()
    capped_contents = capped_stderr.read_text(encoding="utf-8")
    marker = TRUNCATION.match(capped_contents.splitlines()[0])
    assert marker is not None
    dropped, retained, original = (int(value) for value in marker.groups())
    assert dropped + retained == original
    assert capped_contents.splitlines()[-1] == "FINAL: suite failed because the world is broken"

    replay = tmp_path / "capped-failure-replay.json"
    third = _delegate(
        target=target,
        home=home,
        task_id="T-58-FAIL-CAPPED-2",
        worktree=tmp_path / "worktree-capped-2",
        journal=journal,
        harness=harness,
        outcome=replay,
        suite=_failure_suite(filler=True),
        log_max_bytes=4096,
    )
    assert third.returncode == 0, third.stderr
    replay_payload = _assert_outcome_logs(replay)
    replay_logs = replay_payload["logs"]
    assert isinstance(replay_logs, dict)
    replay_stderr = replay.parent / str(replay_logs["dir"]) / "suite.stderr.log"
    assert replay_stderr.exists()
    assert replay_stderr.read_bytes() == capped_contents.encode("utf-8")


def test_real_delegate_timeout_retains_partial_output(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    outcome = tmp_path / "timeout.json"
    result = _delegate(
        target=target,
        home=home,
        task_id="T-58-TIMEOUT",
        worktree=tmp_path / "worktree-timeout",
        journal=tmp_path / "journal.sqlite3",
        harness=_harness(tmp_path / "harness-timeout.sh", timeout=True),
        outcome=outcome,
        timeout=2,
    )

    assert result.returncode != 0
    payload = _assert_outcome_logs(outcome)
    assert payload["timed_out"] is True
    logs = payload["logs"]
    assert isinstance(logs, dict)
    stdout_path = outcome.parent / str(logs["dir"]) / "harness.stdout.log"
    assert stdout_path.exists()
    assert "HARNESS STDOUT: issue-58 operator banner" in stdout_path.read_text(
        encoding="utf-8"
    )


def test_real_fanout_retains_parent_and_child_transcripts(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    task_ids = ("T-58-FANOUT-1", "T-58-FANOUT-2", "T-58-FANOUT-3")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        "\n".join(
            json.dumps(
                {
                    "task_id": task_id,
                    "prompt": "perform real fanout work",
                    "worktree": str(tmp_path / f"worktree-{task_id}"),
                }
            )
            for task_id in task_ids
        )
        + "\n",
        encoding="utf-8",
    )
    outcome_dir = tmp_path / "outcomes"
    harness = _harness(
        tmp_path / "fanout-harness.sh", failure_task_id="T-58-FANOUT-2"
    )
    argv = [
        sys.executable,
        "-m",
        "ranex.cli.main",
        "task",
        "fanout",
        "--tasks",
        str(tasks),
        "--target",
        str(target),
        "--journal",
        str(tmp_path / "journal.sqlite3"),
        "--harness",
        str(harness),
        "--model",
        "ranex-noop/noop",
        "--timeout",
        "30",
        "--suite",
        "/usr/bin/true",
        "--outcome-dir",
        str(outcome_dir),
        "--pool",
        "2",
    ]
    result = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=target,
        env=_environment(home),
        text=True,
    )

    assert result.returncode == 0, result.stderr
    fanout_lines = [line for line in result.stdout.splitlines() if line.startswith("FANOUT")]
    assert len(fanout_lines) == len(task_ids)
    assert all("logs=" in line for line in fanout_lines)
    failures = 0
    for task_id in task_ids:
        outcome = outcome_dir / f"{task_id}.json"
        payload = _assert_outcome_logs(outcome)
        if payload["harness_exit"] != 0:
            failures += 1
    assert failures == 1

    parent_directory = outcome_dir / "fanout.logs"
    parent_names = tuple(
        f"{task_id}.{stream}" for task_id in task_ids for stream in ("stdout", "stderr")
    )
    parent_manifest = parent_directory / "manifest.json"
    assert parent_manifest.exists()
    parent_payload = json.loads(parent_manifest.read_bytes())
    _assert_retained_bundle(parent_directory, parent_payload["streams"], parent_names)


def test_real_delegate_log_retention_keep_and_off(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    journal = tmp_path / "journal.sqlite3"
    harness = _harness(tmp_path / "harness.sh")
    kept = tmp_path / "kept.json"
    first = _delegate(
        target=target,
        home=home,
        task_id="T-58-KEEP-1",
        worktree=tmp_path / "worktree-keep-1",
        journal=journal,
        harness=harness,
        outcome=kept,
    )
    assert first.returncode == 0, first.stderr
    kept_payload = _assert_outcome_logs(kept)
    kept_logs = kept_payload["logs"]
    assert isinstance(kept_logs, dict)
    kept_directory = kept.parent / str(kept_logs["dir"])
    assert kept_directory.exists()
    before: dict[str, bytes] = {}
    for path in kept_directory.iterdir():
        assert path.exists()
        before[path.name] = path.read_bytes()

    refused = _delegate(
        target=target,
        home=home,
        task_id="T-58-KEEP-2",
        worktree=tmp_path / "worktree-keep-2",
        journal=journal,
        harness=harness,
        outcome=kept,
        retention="keep",
    )
    expected = (
        f"refusing to overwrite existing log directory {kept_directory}: "
        "--log-retention is keep"
    )
    assert refused.returncode != 0
    assert expected in refused.stdout + refused.stderr
    for name, contents in before.items():
        path = kept_directory / name
        assert path.exists()
        assert path.read_bytes() == contents

    disabled = tmp_path / "disabled.json"
    off = _delegate(
        target=target,
        home=home,
        task_id="T-58-OFF",
        worktree=tmp_path / "worktree-off",
        journal=journal,
        harness=harness,
        outcome=disabled,
        retention="off",
    )
    assert off.returncode == 0, off.stderr
    disabled_payload = _read_canonical_json(disabled)
    disabled_directory = disabled.with_name(disabled.name + ".logs")
    assert not disabled_directory.exists()
    assert disabled_payload["logs"] == {
        "version": 1,
        "retained": False,
        "reason": "operator-disabled",
    }


def test_real_delegate_refuses_out_of_bounds_log_max_bytes(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    harness = _harness(tmp_path / "harness.sh")
    message = "ERROR  --log-max-bytes must be between 4096 and 8388608 bytes\n"
    for value in (4095, 8_388_609):
        result = _delegate(
            target=target,
            home=home,
            task_id=f"T-58-BOUND-{value}",
            worktree=tmp_path / f"worktree-{value}",
            journal=tmp_path / "journal.sqlite3",
            harness=harness,
            outcome=tmp_path / f"bounds-{value}.json",
            log_max_bytes=value,
        )
        assert result.returncode != 0
        assert result.stderr == message
