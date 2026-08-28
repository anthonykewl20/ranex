"""SLICE-073: a provider-neutral adapter changes and tests real Ranex code."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from _provider_neutral_subject import (
    BASE_COMMIT,
    FOCUSED_TEST,
    PATCH_COMMIT,
    environment,
    git,
    materialize,
    run_focused,
)

from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal


def _adapter(path: Path) -> Path:
    path.write_text(
        "#!/usr/bin/python3\n"
        "import json, os, subprocess, sys\n"
        "directory = sys.argv[sys.argv.index('--dir') + 1]\n"
        f"patch = {PATCH_COMMIT!r}\n"
        "subprocess.run(['git', '-C', directory, 'reset', '--hard', patch], check=True)\n"
        "commit = subprocess.run(['git', '-C', directory, 'rev-parse', 'HEAD'], "
        "check=True, capture_output=True, text=True).stdout.strip()\n"
        "payload = {'task_id': os.environ['RANEX_TASK_ID'], "
        "'worktree': directory, 'commit': commit}\n"
        "with open(os.environ['RANEX_EMIT'], 'a', encoding='utf-8') as stream:\n"
        "    stream.write(json.dumps(payload, sort_keys=True) + '\\n')\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def test_provider_neutral_adapter_applies_real_red_then_green_ranex_commit(
    tmp_path: Path,
) -> None:
    subject = materialize(tmp_path)
    assert git(subject, "rev-parse", f"{PATCH_COMMIT}^") == BASE_COMMIT
    suite = [str(subject.python), "-m", "pytest", "-q", FOCUSED_TEST]
    red = run_focused(subject)
    assert red.returncode == 1
    assert "failed" in red.stdout

    worktree = tmp_path / "delegated-worktree"
    journal = tmp_path / "journal.sqlite3"
    outcome = tmp_path / "outcome.json"
    adapter = _adapter(tmp_path / "real-code-adapter")
    command = [
        str(subject.python),
        "-m",
        "ranex.cli.main",
        "task",
        "delegate",
        "--task-id",
        "T-REAL-RANEX-PATCH",
        "--target",
        str(subject.repository),
        "--worktree",
        str(worktree),
        "--journal",
        str(journal),
        "--harness",
        str(adapter),
        "--model",
        "opaque-host-selected-model",
        "--prompt",
        "Apply the pinned real Ranex change",
        "--timeout",
        "120",
        "--suite",
        " ".join(suite),
        "--claim",
        "provider-neutral-real-e2e",
        "--outcome",
        str(outcome),
    ]
    delegated = subprocess.run(
        command,
        cwd=subject.repository,
        capture_output=True,
        text=True,
        check=False,
        env=environment(subject),
        timeout=180,
    )
    assert delegated.returncode == 0, delegated.stderr

    result = json.loads(outcome.read_text(encoding="utf-8"))
    assert result["commit"] == PATCH_COMMIT
    assert result["suite_exit"] == 0
    assert "57 passed" in result["suite_output_tail"]
    assert "PASS" not in delegated.stdout
    rows = Journal(journal).entries()
    dispatches = [row for row in rows if row.get("type") == "task-dispatch"]
    assert len(dispatches) == 1
    assert dispatches[0]["task_id"] == "T-REAL-RANEX-PATCH"
    assert dispatches[0]["base_commit"] == BASE_COMMIT
    emitted = type(subject)(worktree, subject.home, subject.python)
    assert git(
        emitted,
        "diff",
        "--stat",
        f"{BASE_COMMIT}..{PATCH_COMMIT}",
    )
