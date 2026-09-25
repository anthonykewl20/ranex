"""Issue #111 acceptance tests: the instruction digest, on real processes.

Every arm drives the real CLI as a subprocess against a real committed Git
target with a real shell harness, mirroring the issue's completion arms:

1. a real delegated run's outcome and log manifest name the sha256 of the
   canonical instruction bytes, reproduced out of band by ``sha256sum``;
2. one changed word changes the digest; the same prompt is byte-stable across
   three repeats;
3. removing the retained instruction stream makes the manifest's own digest
   check (``sha256sum -c`` over the manifest's per-stream digests) refuse
   rather than report a clean run;
4. a credential-shaped prompt literal is redacted in the retained stream while
   the digest still covers the unredacted bytes the worker received;
5. two concurrent fanout prompts yield two different digests, each matching its
   own task's outcome — no cross-contamination.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.execution.retained_logs import instruction_bytes, instruction_digest

REPOSITORY = Path(__file__).resolve().parents[2]


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
        ("user.email", "instruction-digest@example.invalid"),
        ("user.name", "Instruction Digest"),
    ):
        configured = _git(target, home, "config", name, value)
        assert configured.returncode == 0, configured.stderr
    (target / "base.txt").write_text("base\n", encoding="utf-8")
    added = _git(target, home, "add", "base.txt")
    assert added.returncode == 0, added.stderr
    committed = _git(target, home, "commit", "-q", "-m", "base")
    assert committed.returncode == 0, committed.stderr
    return target, home


def _harness(path: Path) -> Path:
    """A real shell harness that commits real work and emits its dispatched HEAD."""

    path.write_text(
        """#!/usr/bin/env sh
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
printf '%s\\n' 'HARNESS STDOUT: issue-111 worker ran'
printf '%s\\n' 'real harness work' > "$worktree/agent.txt"
git -C "$worktree" add agent.txt
git -C "$worktree" -c user.email=harness@example.invalid -c user.name=Harness commit -q -m 'real harness work'
commit=$(git -C "$worktree" rev-parse HEAD)
printf '{"task_id":"%s","worktree":"%s","commit":"%s"}\\n' "$RANEX_TASK_ID" "$worktree" "$commit" > "$RANEX_EMIT"
""",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def _delegate(
    *,
    target: Path,
    home: Path,
    task_id: str,
    prompt: str,
    tmp_path: Path,
    harness: Path,
    log_max_bytes: int | None = None,
) -> tuple[subprocess.CompletedProcess[str], Path]:
    outcome = tmp_path / f"{task_id}.json"
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
        str(tmp_path / f"worktree-{task_id}"),
        "--journal",
        str(tmp_path / "journal.sqlite3"),
        "--harness",
        str(harness),
        "--model",
        "ranex-noop/noop",
        "--prompt",
        prompt,
        "--timeout",
        "30",
        "--suite",
        "/usr/bin/true",
        "--outcome",
        str(outcome),
    ]
    if log_max_bytes is not None:
        argv.extend(["--log-max-bytes", str(log_max_bytes)])
    completed = subprocess.run(
        argv,
        capture_output=True,
        check=False,
        cwd=target,
        env=_environment(home),
        text=True,
    )
    return completed, outcome


def _outcome_payload(outcome: Path) -> dict[str, object]:
    payload = json.loads(outcome.read_bytes())
    assert isinstance(payload, dict)
    return payload


def _log_directory(outcome: Path) -> Path:
    return outcome.with_name(outcome.name + ".logs")


def _sha256sum(
    home: Path, *arguments: str, cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """The out-of-band digest oracle: real sha256sum, not ranex code."""

    return subprocess.run(
        ["sha256sum", *arguments],
        capture_output=True,
        check=False,
        cwd=str(cwd) if cwd is not None else None,
        env=_environment(home),
        text=True,
    )


def _manifest_checksums(outcome: Path) -> Path:
    """Render the manifest's per-stream digests as a sha256sum(1) checklist."""

    manifest = json.loads((_log_directory(outcome) / "manifest.json").read_bytes())
    lines = [
        f"{entry['sha256'].removeprefix('sha256:')}  {entry['file']}"
        for entry in manifest["streams"].values()
    ]
    checklist = outcome.parent / f"{outcome.name}.sha256sums"
    checklist.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checklist


def test_real_delegate_digest_is_reproduced_by_out_of_band_sha256sum(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    prompt = "add one comment line to README.md and stop"
    completed, outcome = _delegate(
        target=target,
        home=home,
        task_id="T-111-OK",
        prompt=prompt,
        tmp_path=tmp_path,
        harness=_harness(tmp_path / "harness.sh"),
    )

    assert completed.returncode == 0, completed.stderr
    payload = _outcome_payload(outcome)
    digest = payload["instruction_digest"]
    assert digest == instruction_digest(prompt)

    manifest = json.loads((_log_directory(outcome) / "manifest.json").read_bytes())
    assert manifest["instruction_digest"] == digest

    instruction_log = _log_directory(outcome) / "instruction.log"
    measured = _sha256sum(home, str(instruction_log))
    assert measured.returncode == 0, measured.stderr
    assert measured.stdout.split()[0] == digest.removeprefix("sha256:")
    assert json.loads(instruction_log.read_bytes()) == {
        "handbook_chapters": [],
        "prompt": prompt,
    }


def test_real_delegate_digest_changes_with_one_word_and_is_stable_across_repeats(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    harness = _harness(tmp_path / "harness.sh")
    digests: dict[str, str] = {}
    for task_id, prompt in (
        ("T-111-STABLE-1", "write the deployment note for staging"),
        ("T-111-STABLE-2", "write the deployment note for staging"),
        ("T-111-STABLE-3", "write the deployment note for staging"),
        ("T-111-CHANGED", "write the deployment note for production"),
    ):
        completed, outcome = _delegate(
            target=target,
            home=home,
            task_id=task_id,
            prompt=prompt,
            tmp_path=tmp_path,
            harness=harness,
        )
        assert completed.returncode == 0, completed.stderr
        digests[task_id] = str(_outcome_payload(outcome)["instruction_digest"])

    stable = digests["T-111-STABLE-1"]
    assert stable == digests["T-111-STABLE-2"] == digests["T-111-STABLE-3"]
    assert stable == instruction_digest("write the deployment note for staging")
    assert digests["T-111-CHANGED"] != stable
    assert digests["T-111-CHANGED"] == instruction_digest(
        "write the deployment note for production"
    )


def test_manifest_digest_check_refuses_a_silently_dropped_instruction_stream(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    completed, outcome = _delegate(
        target=target,
        home=home,
        task_id="T-111-DROP",
        prompt="do the auditable work",
        tmp_path=tmp_path,
        harness=_harness(tmp_path / "harness.sh"),
    )
    assert completed.returncode == 0, completed.stderr
    checklist = _manifest_checksums(outcome)

    intact = _sha256sum(
        home, "-c", "--strict", str(checklist), cwd=_log_directory(outcome)
    )
    assert intact.returncode == 0, intact.stdout + intact.stderr

    (_log_directory(outcome) / "instruction.log").unlink()
    dropped = _sha256sum(
        home, "-c", "--strict", str(checklist), cwd=_log_directory(outcome)
    )
    assert dropped.returncode != 0
    assert "instruction.log" in dropped.stdout
    assert "FAILED open or read" in dropped.stdout


def test_real_delegate_redacts_credential_prompt_but_digests_what_was_received(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    password = "RANEX111PROMPTPW0123456789abcdef"
    prompt = f"pull using https://ci:{password}@registry.invalid/wheels and stop"
    completed, outcome = _delegate(
        target=target,
        home=home,
        task_id="T-111-REDACT",
        prompt=prompt,
        tmp_path=tmp_path,
        harness=_harness(tmp_path / "harness.sh"),
    )

    assert completed.returncode == 0, completed.stderr
    payload = _outcome_payload(outcome)
    retained = (_log_directory(outcome) / "instruction.log").read_text(encoding="utf-8")
    assert password not in retained
    assert "[REDACTED:credential]" in retained

    # The digest is over the unredacted canonical bytes the worker received:
    # prove it by feeding exactly those bytes to sha256sum out of band.
    unredacted = tmp_path / "unredacted-instruction.json"
    unredacted.write_bytes(instruction_bytes(prompt))
    measured = _sha256sum(home, str(unredacted))
    assert measured.returncode == 0, measured.stderr
    assert measured.stdout.split()[0] == str(payload["instruction_digest"]).removeprefix(
        "sha256:"
    )


def test_real_delegate_truncates_the_instruction_stream_under_the_byte_cap(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    prompt = "t" * 5000
    completed, outcome = _delegate(
        target=target,
        home=home,
        task_id="T-111-TRUNC",
        prompt=prompt,
        tmp_path=tmp_path,
        harness=_harness(tmp_path / "harness.sh"),
        log_max_bytes=4096,
    )

    assert completed.returncode == 0, completed.stderr
    payload = _outcome_payload(outcome)
    assert payload["instruction_digest"] == instruction_digest(prompt)
    retained = (_log_directory(outcome) / "instruction.log").read_text(encoding="utf-8")
    assert retained.startswith("[ranex truncated: policy=tail ")
    manifest = json.loads((_log_directory(outcome) / "manifest.json").read_bytes())
    assert manifest["instruction_digest"] == payload["instruction_digest"]
    assert manifest["streams"]["instruction"]["truncated"] is True


def test_real_fanout_yields_isolated_per_task_instruction_digests(
    tmp_path: Path, real_target: tuple[Path, Path]
) -> None:
    target, home = real_target
    prompts = {
        "T-111-FAN-1": "describe the api layer in one paragraph",
        "T-111-FAN-2": "describe the database layer in one paragraph",
    }
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        "\n".join(
            json.dumps(
                {
                    "task_id": task_id,
                    "prompt": prompt,
                    "worktree": str(tmp_path / f"worktree-{task_id}"),
                }
            )
            for task_id, prompt in prompts.items()
        )
        + "\n",
        encoding="utf-8",
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
        str(_harness(tmp_path / "fanout-harness.sh")),
        "--model",
        "ranex-noop/noop",
        "--timeout",
        "30",
        "--suite",
        "/usr/bin/true",
        "--outcome-dir",
        str(tmp_path / "outcomes"),
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
    observed: dict[str, str] = {}
    for task_id, prompt in prompts.items():
        outcome = tmp_path / "outcomes" / f"{task_id}.json"
        payload = _outcome_payload(outcome)
        digest = str(payload["instruction_digest"])
        assert digest == instruction_digest(prompt)
        instruction_log = _log_directory(outcome) / "instruction.log"
        measured = _sha256sum(home, str(instruction_log))
        assert measured.returncode == 0, measured.stderr
        assert measured.stdout.split()[0] == digest.removeprefix("sha256:")
        observed[task_id] = digest

    assert observed["T-111-FAN-1"] != observed["T-111-FAN-2"]
