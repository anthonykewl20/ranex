"""SLICE-073: a provider-neutral adapter changes and tests real Ranex code."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


REAL_REPO = Path(__file__).resolve().parents[2]
BASE_COMMIT = "f940da0f44a78fd754a402bcae98d745515b6354"
PATCH_COMMIT = "cebc06a33ba1f28fd21815bb21edbdc768b4a669"
FOCUSED_TEST = "tests/integration/test_slice072_dynamic_runtime_contract.py"


def _environment(home: Path) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "PYTHONPATH": str(REAL_REPO / "src"),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _git(repository: Path, *arguments: str, home: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=_environment(home),
    )
    return completed.stdout.strip()


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
    home = tmp_path / "home"
    home.mkdir()
    target = tmp_path / "ranex-subject"
    subprocess.run(
        ["git", "clone", "--quiet", str(REAL_REPO), str(target)],
        check=True,
        env=_environment(home),
    )
    _git(target, "checkout", "--quiet", BASE_COMMIT, home=home)
    assert _git(target, "rev-parse", f"{PATCH_COMMIT}^", home=home) == BASE_COMMIT

    python = str(REAL_REPO / ".venv" / "bin" / "python3")
    suite = [python, "-m", "pytest", "-q", FOCUSED_TEST]
    red = subprocess.run(
        suite,
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=_environment(home),
        timeout=120,
    )
    assert red.returncode == 1
    assert "failed" in red.stdout

    worktree = tmp_path / "delegated-worktree"
    journal = tmp_path / "journal.sqlite3"
    outcome = tmp_path / "outcome.json"
    adapter = _adapter(tmp_path / "real-code-adapter")
    command = [
        python,
        "-m",
        "ranex.cli.main",
        "task",
        "delegate",
        "--task-id",
        "T-REAL-RANEX-PATCH",
        "--target",
        str(target),
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
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
        env=_environment(home),
        timeout=180,
    )
    assert delegated.returncode == 0, delegated.stderr

    result = json.loads(outcome.read_text(encoding="utf-8"))
    assert result["commit"] == PATCH_COMMIT
    assert result["suite_exit"] == 0
    assert "57 passed" in result["suite_output_tail"]
    assert _git(
        worktree,
        "diff",
        "--stat",
        f"{BASE_COMMIT}..{PATCH_COMMIT}",
        home=home,
    )
