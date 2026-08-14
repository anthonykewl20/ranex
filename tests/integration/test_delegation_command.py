"""In-process coverage for delegation cross-checking.

These tests mirror criterion-4 refusal branches directly in-process so coverage sees
`cmd_task_delegate` paths that subprocess-based tests do not attribute.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import threading
import time
from pathlib import Path

import pytest

from ranex.cli.delegation import (
    _read_emission,
    _run_suite,
    _run_suite_with_results,
    _tail_output,
    _write_outcome,
    cmd_task_delegate,
    exec_environment_holds_signing_key,
    execute_environment,
)
from ranex.cli.fanout import _run_one_delegation, cmd_task_fanout
from ranex.cli.main import (
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_USAGE,
    _latest_task_dispatch,
    _perform_task_dispatch,
    cmd_task_dispatch,
    cmd_task_judge,
    main,
    subject_digest_for,
)
from ranex.foundation.canonical import canonical_json_bytes, command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskDispatch


def build_harness(path: Path) -> Path:
    path.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)
    return path


def delegation_args(tmp_path: Path, *, task_id: str, worktree: Path, journal: Path, harness: Path) -> argparse.Namespace:
    return argparse.Namespace(
        task_id=task_id,
        target=str(tmp_path / "target"),
        worktree=str(worktree),
        journal=str(journal),
        harness=str(harness),
        model="ranex-noop/noop",
        prompt="perform work then emit",
        timeout=120,
        suite="/usr/bin/true",
        outcome=str(tmp_path / "outcome.json"),
    )


def fanout_args(
    tmp_path: Path,
    *,
    tasks: Path,
    target: Path,
    journal: Path,
    harness: Path,
    pool: int,
) -> argparse.Namespace:
    return argparse.Namespace(
        tasks=str(tasks),
        target=str(target),
        journal=str(journal),
        harness=str(harness),
        model="ranex-noop/noop",
        timeout=120,
        suite="/usr/bin/true",
        outcome_dir=str(tmp_path / "outcomes"),
        pool=pool,
    )


def seed_dispatch(journal: Path, task_id: str, worktree: Path, commit: str) -> None:
    Journal(journal).append(TaskDispatch(task_id, str(worktree), commit))


def fake_subprocess_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(_args[0], 0, "", "")


def fake_harness_run(**_kwargs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["harness"], 0, "", "")


def configure_truthful_delegate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    task_id: str,
) -> tuple[argparse.Namespace, Path, str, str]:
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    emitted_commit = "b" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    def fake_git(
        _root: Path, *arguments: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        tree = "emitted-tree" if emitted_commit in str(arguments) else "base-tree"
        return subprocess.CompletedProcess(arguments, 0, f"{tree}\n", "")

    monkeypatch.setattr(
        "ranex.cli.main._perform_task_dispatch",
        lambda *_args, **_kwargs: dispatched_worktree,
    )
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: emitted_commit)
    monkeypatch.setattr("ranex.cli.delegation.git", fake_git)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": emitted_commit,
        },
    )
    monkeypatch.setattr(
        "ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    return args, dispatched_worktree.resolve(), base_commit, emitted_commit


def test_candidate_manifest_edit_cannot_change_delegated_judgement(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    subprocess.run(["git", "init", "-q", str(target)], check=True)
    subprocess.run(
        ["git", "-C", str(target), "config", "user.email", "slice009@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(target), "config", "user.name", "Slice 009"],
        check=True,
    )
    private, public = generate_keypair()
    command = ["/usr/bin/true", "--junitxml=artifacts/junit.xml"]
    required_id = "tests/test_required.py::test_required"
    stable_id = "tests/test_stable.py::test_stable"
    base_manifest = {
        "suite": [required_id, stable_id],
        "expected_skips": {},
    }
    (target / "governance").mkdir()
    (target / "governance" / "gates.yaml").write_text(
        """gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: [\"/usr/bin/true\", \"--junitxml=artifacts/junit.xml\"]
        results_artifact: artifacts/junit.xml
""",
        encoding="utf-8",
    )
    (target / "governance" / "suite_manifest.json").write_bytes(
        canonical_json_bytes(base_manifest)
    )
    (target / "governance" / "producers.yaml").write_text(
        f"producers:\n  worker: {public}\n", encoding="utf-8"
    )
    (target / "governance" / "evidence.json").write_text("[]\n", encoding="utf-8")
    (target / "app.txt").write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(target), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(target), "commit", "-q", "-m", "base policy"],
        check=True,
    )
    base_commit = subprocess.run(
        ["git", "-C", str(target), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    observed: list[tuple[int, list[str]]] = []
    for suffix, edits_manifest in (("control", False), ("edited", True)):
        task_id = f"T-9-{suffix.upper()}"
        worktree = tmp_path / f"worktree-{suffix}"
        subprocess.run(
            [
                "git",
                "-C",
                str(target),
                "worktree",
                "add",
                "-q",
                "-b",
                f"candidate-{suffix}",
                str(worktree),
                base_commit,
            ],
            check=True,
        )
        (worktree / "app.txt").write_text(f"candidate {suffix}\n", encoding="utf-8")
        candidate_manifest = base_manifest
        if edits_manifest:
            candidate_manifest = {"suite": [stable_id], "expected_skips": {}}
            (worktree / "governance" / "suite_manifest.json").write_bytes(
                canonical_json_bytes(candidate_manifest)
            )
        subprocess.run(["git", "-C", str(worktree), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(worktree), "commit", "-q", "-m", suffix],
            check=True,
        )
        commit = subprocess.run(
            ["git", "-C", str(worktree), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        subject = subject_digest_for(worktree, commit)
        outcomes = {stable_id: "passed"}
        suite_results = {
            "manifest_digest": "sha256:"
            + hashlib.sha256(canonical_json_bytes(candidate_manifest)).hexdigest(),
            "counts": {
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "non_passed": [],
            "missing": [] if edits_manifest else [required_id],
            "extra_count": 0,
            "outcome_digest": "sha256:"
            + hashlib.sha256(canonical_json_bytes(outcomes)).hexdigest(),
        }
        content = {
            "claim_id": "tests-executed",
            "command": " ".join(command),
            "command_digest": command_digest(command),
            "executable_path": "/usr/bin/true",
            "exit_code": 0,
            "producer_id": "worker",
            "subject_digest": subject,
            "suite_results": suite_results,
            "confinement_result_digest": "sha256:" + "c" * 64,
            "confinement_profile_digest": "sha256:" + "d" * 64,
        }
        (worktree / "governance" / "evidence.json").write_text(
            json.dumps([{**content, "signature": sign_evidence(content, private)}]),
            encoding="utf-8",
        )
        journal = tmp_path / f"journal-{suffix}.sqlite3"
        seed_dispatch(journal, task_id, worktree, base_commit)
        result = cmd_task_judge(
            argparse.Namespace(
                task_id=task_id,
                emitted_worktree=str(worktree),
                emitted_commit=commit,
                gate="landing",
                gate_catalog="governance/gates.yaml",
                evidence="governance/evidence.json",
                producers="governance/producers.yaml",
                suite_manifest="governance/suite_manifest.json",
                journal=str(journal),
            )
        )
        candidate = next(
            row
            for row in Journal(journal).entries()
            if row.get("type") == "task-candidate"
        )
        observed.append((result, candidate["missing_claims"]))

    assert observed == [
        (1, ["tests-executed"]),
        (1, ["tests-executed"]),
    ]


def test_judge_refuses_dispatch_with_invalid_base_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-INVALID-BASE"
    worktree = tmp_path / "dispatch-worktree"
    journal_path = tmp_path / "journal.sqlite3"
    journal_path.touch()
    emitted_commit = "b" * 40

    class InvalidDispatchJournal:
        def __init__(self, _path: Path) -> None:
            pass

        def verify(self) -> bool:
            return True

        def entries(self) -> list[dict[str, object]]:
            return [
                {
                    "type": "task-dispatch",
                    "task_id": task_id,
                    "worktree": str(worktree),
                    "base_commit": "not-a-commit",
                }
            ]

    monkeypatch.setattr("ranex.cli.main.Journal", InvalidDispatchJournal)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: emitted_commit)

    result = cmd_task_judge(
        argparse.Namespace(
            task_id=task_id,
            emitted_worktree=str(worktree),
            emitted_commit=emitted_commit,
            journal=str(journal_path),
        )
    )
    captured = capsys.readouterr()

    assert result == EXIT_FAIL
    assert "invalid base commit in dispatch" in captured.err
    assert task_id in captured.err


def test_delegate_refuses_absent_dispatch_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8-ABSENT"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
    )

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(worktree),
            "commit": "a" * 40,
        },
    )
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*dispatch", captured.err.lower())
    assert "traceback" not in captured.err.lower()
    assert not Path(args.outcome).exists()


def test_delegate_refuses_task_id_mismatch_before_materialisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8-TASK"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    seed_dispatch(journal, task_id, worktree, "a" * 40)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
    )

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": "other-task",
            "worktree": str(worktree),
            "commit": "a" * 40,
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*task", captured.err.lower())
    assert "traceback" not in captured.err.lower()
    assert not Path(args.outcome).exists()
    assert all(record.get("type") != "task-candidate" for record in Journal(journal).entries())


def test_delegate_refuses_worktree_mismatch_before_materialisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8-WTREE"
    dispatched = tmp_path / "dispatch-worktree"
    forged = tmp_path / "forged-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    seed_dispatch(journal, task_id, dispatched, "a" * 40)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched,
        journal=journal,
        harness=harness,
    )

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(forged),
            "commit": "a" * 40,
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*worktree", captured.err.lower())
    assert "traceback" not in captured.err.lower()
    assert not Path(args.outcome).exists()


def test_delegate_refuses_commit_mismatch_before_materialisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8-COMMIT"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    seed_dispatch(journal, task_id, worktree, "a" * 40)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
    )

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(worktree),
            "commit": "b" * 40,
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*commit", captured.err.lower())
    assert "traceback" not in captured.err.lower()
    assert not Path(args.outcome).exists()


def test_delegate_refuses_deleted_dispatched_worktree_before_materialisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8-REAPED"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    seed_dispatch(journal, task_id, worktree, "a" * 40)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
    )

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr(
        "ranex.cli.main.head_commit",
        lambda _path: (_ for _ in ()).throw(ValueError("deleted")),
    )
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(worktree),
            "commit": "a" * 40,
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*worktree", captured.err.lower())
    assert "traceback" not in captured.err.lower()
    assert not Path(args.outcome).exists()


def test_refuses_emitted_commit_equal_to_base_commit_before_materialisation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-8-BASE"
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    monkeypatch.setattr(
        "ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched_worktree
    )
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: base_commit)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": base_commit,
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*base", captured.err.lower())


def test_refuses_emitted_commit_with_identical_tree_before_materialisation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-8-TREE"
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    emitted_commit = "b" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    def fake_git(_root, *arguments: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if arguments == ("rev-parse", f"{emitted_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "tree-id\n", "")
        if arguments == ("rev-parse", f"{base_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "tree-id\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(
        "ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched_worktree
    )
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: emitted_commit)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": emitted_commit,
        },
    )
    monkeypatch.setattr("ranex.cli.delegation.git", fake_git)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*base", captured.err.lower())


def test_subject_with_new_tree_proceeds_to_materialisation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-8-NONEMPTY"
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    emitted_commit = "b" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    suite_calls: list[tuple[Path, str]] = []

    def fake_run_suite(worktree: Path, commit: str, suite: str) -> tuple[int, str]:
        suite_calls.append((worktree, commit))
        return 0, ""

    def fake_git(_root, *arguments: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if arguments == ("rev-parse", f"{emitted_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "tree-emitted\n", "")
        if arguments == ("rev-parse", f"{base_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "tree-base\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr(
        "ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched_worktree
    )
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: emitted_commit)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": emitted_commit,
        },
    )
    monkeypatch.setattr("ranex.cli.delegation._run_suite", fake_run_suite)
    monkeypatch.setattr("ranex.cli.delegation.git", fake_git)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_PASS
    assert suite_calls == [(dispatched_worktree.resolve(), emitted_commit)]
    assert "DELEGATED" in captured.out


def test_truthful_emission_uses_dispatched_worktree_and_commit_for_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-8-TRUTH"
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    dispatched_commit = "b" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    suite_calls: list[tuple[Path, str]] = []

    def fake_run_suite(worktree: Path, commit: str, suite: str) -> tuple[int, str]:
        suite_calls.append((worktree, commit))
        return 0, ""

    def fake_git(
        _root, *arguments: object, **_kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if arguments == ("rev-parse", f"{dispatched_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "tree-dispatched\n", "")
        if arguments == ("rev-parse", f"{base_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "tree-base\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched_worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: dispatched_commit)
    monkeypatch.setattr("ranex.cli.delegation._run_suite", fake_run_suite)
    monkeypatch.setattr("ranex.cli.delegation.git", fake_git)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": dispatched_commit,
        },
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_PASS
    assert "DELEGATED" in captured.out
    assert suite_calls == [(dispatched_worktree.resolve(), dispatched_commit)]


def test_refuses_when_emitted_tree_is_not_reachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-8-EMITTED-TREE-FAIL"
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    emitted_commit = "b" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    def fake_git(_root, *arguments: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if arguments == ("rev-parse", f"{emitted_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 1, "", "bad emitted")
        if arguments == ("rev-parse", f"{base_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "base-tree\n", "")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched_worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: emitted_commit)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": emitted_commit,
        },
    )
    monkeypatch.setattr("ranex.cli.delegation.git", fake_git)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*cannot determine emitted tree", captured.err.lower())


def test_refuses_when_base_tree_is_not_reachable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    task_id = "T-8-BASE-TREE-FAIL"
    dispatched_worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    base_commit = "a" * 40
    emitted_commit = "b" * 40
    seed_dispatch(journal, task_id, dispatched_worktree, base_commit)
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=dispatched_worktree,
        journal=journal,
        harness=harness,
    )

    def fake_git(_root, *arguments: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if arguments == ("rev-parse", f"{emitted_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 0, "emitted-tree\n", "")
        if arguments == ("rev-parse", f"{base_commit}^{{tree}}"):
            return subprocess.CompletedProcess(arguments, 1, "", "bad base")
        return subprocess.CompletedProcess(arguments, 0, "", "")

    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: dispatched_worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: emitted_commit)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(dispatched_worktree),
            "commit": emitted_commit,
        },
    )
    monkeypatch.setattr("ranex.cli.delegation.git", fake_git)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert re.search(r"refusing.*cannot determine base tree", captured.err.lower())


def test_exec_environment_holds_signing_key_reads_proc_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ranex.cli.delegation.Path.read_bytes",
        lambda _self: b"FOO=1\x00RANEX_SIGNING_KEY=secret\x00BAR=2\x00",
    )
    assert exec_environment_holds_signing_key()


def test_exec_environment_holds_signing_key_absent_when_proc_env_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ranex.cli.delegation.Path.read_bytes", lambda _self: b"FOO=1\x00BAR=2\x00"
    )
    assert not exec_environment_holds_signing_key()


def test_execute_environment_refuses_signing_key_in_ambient(tmp_path: Path) -> None:
    ambient = {"RANEX_SIGNING_KEY": "x", "OPENROUTER_API_KEY": "y"}
    with pytest.raises(ValueError, match="signing credential"):
        execute_environment(ambient, task_id="T", emit="/tmp/e.jsonl", home=str(tmp_path))


def test_execute_environment_refuses_without_model_credential(tmp_path: Path) -> None:
    ambient: dict[str, str] = {}
    with pytest.raises(ValueError, match="model credential"):
        execute_environment(ambient, task_id="T", emit="/tmp/e.jsonl", home=str(tmp_path))


def test_execute_environment_is_built_from_scratch(tmp_path: Path) -> None:
    ambient = {"OPENROUTER_API_KEY": "k"}
    env = execute_environment(ambient, task_id="T", emit="/tmp/e.jsonl", home=str(tmp_path))
    assert env["RANEX_TASK_ID"] == "T"
    assert env["RANEX_EMIT"] == "/tmp/e.jsonl"
    assert env["OPENROUTER_API_KEY"] == "k"
    assert env["HOME"] == str(tmp_path)
    assert "PATH" in env


def test_write_outcome_round_trips_json(tmp_path: Path) -> None:
    path = tmp_path / "out.json"
    _write_outcome(path, {"task_id": "T", "commit": "a", "suite_exit": 0})
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["task_id"] == "T"
    assert loaded["suite_exit"] == 0


def test_tail_output_respects_limit() -> None:
    value = "x" * 5000
    assert len(_tail_output(value)) == 4000
    assert _tail_output("tiny") == "tiny"


def test_read_emission_rejects_unreadable_path(tmp_path: Path) -> None:
    path = tmp_path / "missing.jsonl"
    with pytest.raises(ValueError, match="refusing emission: cannot read"):
        _read_emission(path)


def test_read_emission_rejects_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "emit.jsonl"
    path.write_text("\n", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing emission: no lines"):
        _read_emission(path)


def test_read_emission_rejects_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "emit.jsonl"
    path.write_text("not-json\n", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing emission: cannot parse"):
        _read_emission(path)


def test_read_emission_rejects_non_object_payload(tmp_path: Path) -> None:
    path = tmp_path / "emit.jsonl"
    path.write_text('["x"]\n', encoding="utf-8")
    with pytest.raises(ValueError, match="refusing emission: payload"):
        _read_emission(path)


def test_read_emission_rejects_payload_missing_fields(tmp_path: Path) -> None:
    path = tmp_path / "emit.jsonl"
    path.write_text(json.dumps({"task_id": "T"}), encoding="utf-8")
    with pytest.raises(ValueError, match="refusing emission: .* missing a valid"):
        _read_emission(path)


def test_read_emission_accepts_valid_payload(tmp_path: Path) -> None:
    path = tmp_path / "emit.jsonl"
    expected = {"task_id": "T-8", "worktree": "/tmp/worktree", "commit": "a" * 40}
    path.write_text(json.dumps(expected) + "\n", encoding="utf-8")
    assert _read_emission(path) == expected


def test_run_suite_respects_tail_and_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeMaterialisation:
        def __init__(self) -> None:
            self.tree = tmp_path / "tree"
            self.home = tmp_path / "home"
            self.temporary = tmp_path / "tmp"
            self.tree.mkdir()
            self.home.mkdir()
            self.temporary.mkdir()

        def __enter__(self) -> FakeMaterialisation:
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> bool | None:
            return None

    captured: list[tuple[list[str], Path, dict[str, str]]] = []
    monkeypatch.setattr(
        "ranex.cli.delegation.materialise_subject",
        lambda *_args, **_kwargs: FakeMaterialisation(),
    )
    def fake_run(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured.append((args, kwargs["cwd"], kwargs["env"]))
        return subprocess.CompletedProcess(args, 3, stdout="out", stderr="err")
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_run)

    suite_exit, suite_output_tail = _run_suite(tmp_path / "repo", "a" * 40, "python -c 'print(1)'")
    assert suite_exit == 3
    assert suite_output_tail == "outerr"
    assert captured[0][0] == ["python", "-c", "print(1)"]
    assert captured[0][1] == tmp_path / "tree"
    assert captured[0][2]["TMPDIR"] == str(tmp_path / "tmp")
    assert captured[0][2]["GIT_CONFIG_NOSYSTEM"] == "1"
    assert captured[0][2]["GIT_ATTR_NOSYSTEM"] == "1"


def test_run_suite_refuses_empty_command(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no arguments"):
        _run_suite(tmp_path / "repo", "a" * 40, "")


def test_run_suite_with_results_reads_artifact_before_teardown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    active = False

    class FakeMaterialisation:
        def __init__(self) -> None:
            self.tree = tmp_path / "tree"
            self.home = tmp_path / "home"
            self.temporary = tmp_path / "tmp"
            self.tree.mkdir()
            self.home.mkdir()
            self.temporary.mkdir()

        def __enter__(self) -> FakeMaterialisation:
            nonlocal active
            active = True
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> bool | None:
            nonlocal active
            active = False
            return None

    manifest = {"suite": ["tests/test_example.py::test_pass"]}
    observed: dict[str, object] = {}

    def fake_run(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        observed["command"] = command
        observed["cwd"] = kwargs["cwd"]
        observed["environment"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 3, stdout="out", stderr="err")

    def fake_parse(path: Path, pinned: dict[str, object]) -> dict[str, object]:
        assert active, "results must be read before materialisation teardown"
        observed["artifact"] = path
        observed["manifest"] = pinned
        return {"counts": {"passed": 1}}

    monkeypatch.setattr(
        "ranex.cli.delegation.materialise_subject",
        lambda *_args, **_kwargs: FakeMaterialisation(),
    )
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_run)
    monkeypatch.setattr("ranex.cli.delegation.parse_results_artifact", fake_parse)

    suite_exit, output_tail, results = _run_suite_with_results(
        tmp_path / "repo",
        "a" * 40,
        "python -c 'print(1)'",
        results_artifact="artifacts/junit.xml",
        manifest=manifest,
    )

    assert (suite_exit, output_tail, results) == (
        3,
        "outerr",
        {"counts": {"passed": 1}},
    )
    assert observed["command"] == ["python", "-c", "print(1)"]
    assert observed["cwd"] == tmp_path / "tree"
    assert observed["artifact"] == tmp_path / "tree" / "artifacts/junit.xml"
    assert observed["manifest"] is manifest
    assert observed["environment"] == {
        "PATH": observed["environment"]["PATH"],
        "HOME": str(tmp_path / "home"),
        "TMPDIR": str(tmp_path / "tmp"),
        "LANG": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTR_NOSYSTEM": "1",
    }
    assert active is False


def test_run_suite_with_results_refuses_empty_command(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="refusing suite command: no arguments"):
        _run_suite_with_results(
            tmp_path / "repo",
            "a" * 40,
            "",
            results_artifact="artifacts/junit.xml",
            manifest={},
        )


def test_delegate_refuses_suite_command_that_differs_from_dispatch_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, _worktree, _base_commit, _emitted_commit = configure_truthful_delegate(
        tmp_path, monkeypatch, task_id="T-9-COMMAND-MISMATCH"
    )
    args.gate_catalog = "governance/gates.yaml"
    claim = argparse.Namespace(
        claim_id="tests-executed",
        command=("/usr/bin/false",),
        results_artifact="artifacts/junit.xml",
    )
    monkeypatch.setattr(
        "ranex.cli.delegation.verified_blob_at_path",
        lambda *_args, **_kwargs: b"gate catalog",
    )
    monkeypatch.setattr(
        "ranex.cli.delegation.load_gate_text",
        lambda source, gate: argparse.Namespace(required_claims=(claim,)),
    )

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert (
        "refusing suite command: it does not match the dispatch-time claim "
        "'tests-executed'"
    ) in captured.err


def test_delegate_refuses_dispatch_base_without_suite_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, _worktree, _base_commit, _emitted_commit = configure_truthful_delegate(
        tmp_path, monkeypatch, task_id="T-9-MISSING-MANIFEST"
    )
    args.gate_catalog = "governance/gates.yaml"
    args.suite_manifest = "governance/suite_manifest.json"
    claim = argparse.Namespace(
        claim_id="tests-executed",
        command=("/usr/bin/true",),
        results_artifact="artifacts/junit.xml",
    )

    def fake_verified_blob(
        _worktree: Path, _commit: str, path: str, _git: object
    ) -> bytes | None:
        return b"gate catalog" if path == args.gate_catalog else None

    monkeypatch.setattr(
        "ranex.cli.delegation.verified_blob_at_path", fake_verified_blob
    )
    monkeypatch.setattr(
        "ranex.cli.delegation.load_gate_text",
        lambda source, gate: argparse.Namespace(required_claims=(claim,)),
    )

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert (
        "refusing suite: dispatch base carries no manifest at "
        "governance/suite_manifest.json"
    ) in captured.err


def test_delegate_uses_dispatch_catalog_manifest_and_results_aware_suite(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args, worktree, base_commit, emitted_commit = configure_truthful_delegate(
        tmp_path, monkeypatch, task_id="T-9-RESULTS"
    )
    args.gate_catalog = "governance/gates.yaml"
    args.suite_manifest = "governance/suite_manifest.json"
    claim = argparse.Namespace(
        claim_id="tests-executed",
        command=("/usr/bin/true",),
        results_artifact="artifacts/junit.xml",
    )
    manifest = {"suite": ["tests/test_example.py::test_pass"]}
    suite_results = {"counts": {"passed": 1}}
    calls: dict[str, object] = {}

    def fake_verified_blob(
        received_worktree: Path,
        received_commit: str,
        path: str,
        _git: object,
    ) -> bytes:
        assert received_worktree == worktree
        assert received_commit == base_commit
        return b"gate catalog" if path == args.gate_catalog else b"manifest"

    def fake_load_manifest(source: bytes) -> dict[str, object]:
        calls["manifest_source"] = source
        return manifest

    def fake_results_suite(**kwargs: object) -> tuple[int, str, dict[str, object]]:
        calls["suite"] = kwargs
        return 0, "suite output", suite_results

    monkeypatch.setattr(
        "ranex.cli.delegation.verified_blob_at_path", fake_verified_blob
    )
    monkeypatch.setattr(
        "ranex.cli.delegation.load_gate_text",
        lambda source, gate: argparse.Namespace(required_claims=(claim,)),
    )
    monkeypatch.setattr("ranex.cli.delegation.load_manifest_bytes", fake_load_manifest)
    monkeypatch.setattr(
        "ranex.cli.delegation._run_suite_with_results", fake_results_suite
    )

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_PASS
    assert "DELEGATED" in captured.out
    assert calls["manifest_source"] == b"manifest"
    assert calls["suite"] == {
        "worktree": worktree,
        "commit": emitted_commit,
        "suite": "/usr/bin/true",
        "results_artifact": "artifacts/junit.xml",
        "manifest": manifest,
    }
    assert json.loads(Path(args.outcome).read_text(encoding="utf-8"))[
        "suite_results"
    ] == suite_results


def test_latest_task_dispatch_prefers_latest_record() -> None:
    entries: list[dict[str, object]] = [
        {"type": "task-dispatch", "task_id": "A", "worktree": "one"},
        {"type": "other", "task_id": "A", "worktree": "ignored"},
        {"type": "task-dispatch", "task_id": "A", "worktree": "two"},
    ]
    assert _latest_task_dispatch(entries, "A") == entries[2]
    assert _latest_task_dispatch(entries, "missing") is None


def test_perform_task_dispatch_checks_task_id_and_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    class FakeJournal:
        appended: list[dict[str, object]] = []

        def __init__(self, _path) -> None:
            pass

        def append(self, record: object) -> str:
            if hasattr(record, "as_record"):
                self.appended.append(record.as_record())  # type: ignore[attr-defined]
            return "sha256:ok"

    target = tmp_path / "target"
    target.mkdir()
    (target / "file").write_text("x", encoding="utf-8")
    (tmp_path / ".git").mkdir()

    monkeypatch.setattr("ranex.cli.main.git", lambda *args, **kwargs: FakeResult(0, "true\n"))
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    monkeypatch.setattr("ranex.cli.main.Journal", FakeJournal)

    worktree = _perform_task_dispatch(
        task_id="T-8",
        raw_target=target,
        raw_worktree=tmp_path / "dispatch-worktree",
        raw_journal=tmp_path / "journal.sqlite3",
    )
    assert worktree == (tmp_path / "dispatch-worktree").resolve()


def test_perform_task_dispatch_refuses_blank_task_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-blank"):
        _perform_task_dispatch(
            task_id=" ",
            raw_target=tmp_path / "target",
            raw_worktree=tmp_path / "w",
            raw_journal=tmp_path / "j",
        )


def test_perform_task_dispatch_refuses_invalid_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr("ranex.cli.main.git", lambda *args, **kwargs: FakeResult(1, "", "not worktree"))
    with pytest.raises(ValueError, match="not a git working repository"):
        _perform_task_dispatch(
            task_id="T-8",
            raw_target=tmp_path / "target",
            raw_worktree=tmp_path / "w",
            raw_journal=tmp_path / "j",
        )


def test_perform_task_dispatch_refuses_existing_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    worktree = tmp_path / "dispatch-worktree"
    worktree.mkdir()
    with pytest.raises(ValueError, match="already exists"):
        _perform_task_dispatch(
            task_id="T-8",
            raw_target=tmp_path / "target",
            raw_worktree=worktree,
            raw_journal=tmp_path / "journal.sqlite3",
        )


def test_perform_task_dispatch_refuses_duplicate_task_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    journal = tmp_path / "journal.sqlite3"
    Journal(journal).append(TaskDispatch("T-8-SHARED", str(tmp_path / "other"), "a" * 40))

    target = tmp_path / "target"
    target.mkdir()
    monkeypatch.setattr("ranex.cli.main.git", lambda *args, **kwargs: FakeResult(0, "true\n"))
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)

    with pytest.raises(ValueError, match="already dispatched; one dispatch, one judgement"):
        _perform_task_dispatch(
            task_id="T-8-SHARED",
            raw_target=target,
            raw_worktree=tmp_path / "dispatch-worktree",
            raw_journal=journal,
        )


def test_perform_task_dispatch_refuses_invalid_head(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr("ranex.cli.main.git", lambda *args, **kwargs: FakeResult(0, "true\n"))
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "not-a-commit")
    with pytest.raises(ValueError, match="40-hex"):
        _perform_task_dispatch(
            task_id="T-8",
            raw_target=tmp_path / "target",
            raw_worktree=tmp_path / "dispatch-worktree",
            raw_journal=tmp_path / "journal.sqlite3",
        )


def test_perform_task_dispatch_refuses_failed_worktree_add(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    calls = {"count": 0}
    def fake_git(target: Path, *command: str) -> FakeResult:
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResult(0, "true\n")
        return FakeResult(1, "", "cannot add")
    monkeypatch.setattr("ranex.cli.main.git", fake_git)

    with pytest.raises(ValueError, match="cannot create worktree"):
        _perform_task_dispatch(
            task_id="T-8",
            raw_target=tmp_path / "target",
            raw_worktree=tmp_path / "dispatch-worktree",
            raw_journal=tmp_path / "journal.sqlite3",
        )


def test_cmd_task_dispatch_returns_usage_on_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        task_id="T-8",
        target=str(tmp_path / "target"),
        worktree=str(tmp_path / "wt"),
        journal=str(tmp_path / "journal.sqlite3"),
    )
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: (_ for _ in ()).throw(ValueError("nope")))

    result = cmd_task_dispatch(args)
    assert result == EXIT_USAGE
    captured = capsys.readouterr()
    assert "ERROR" in captured.err


def test_cmd_task_dispatch_returns_ok_with_task_dispatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    journal_path = tmp_path / "journal.sqlite3"
    worktree = tmp_path / "wt"
    args = argparse.Namespace(
        task_id="T-8",
        target=str(tmp_path / "target"),
        worktree=str(worktree),
        journal=str(journal_path),
    )
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    result = cmd_task_dispatch(args)
    assert result == EXIT_PASS
    captured = capsys.readouterr()
    assert f"DISPATCHED  task=T-8  worktree={worktree}" in captured.out


def test_cmd_task_fanout_refuses_missing_tasks_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = fanout_args(
        tmp_path,
        tasks=tmp_path / "tasks.jsonl",
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "tasks.jsonl" in captured.err.lower()


def test_cmd_task_fanout_refuses_bad_json_line(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text("not-json\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "json" in captured.err.lower()


def test_cmd_task_fanout_refuses_blank_field(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(json.dumps({"task_id": "", "prompt": "p", "worktree": "x"}) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "missing" in captured.err.lower() or "must be non-empty" in captured.err.lower()


def test_cmd_task_fanout_refuses_empty_tasks_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text("", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "empty" in captured.err.lower()


def test_cmd_task_fanout_refuses_non_object_payload(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text("[\"bad\"]\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "not an object" in captured.err.lower()


def test_cmd_task_fanout_refuses_extra_fields(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        json.dumps({"task_id": "a", "prompt": "p", "worktree": "w", "extra": "x"}) + "\n",
        encoding="utf-8",
    )
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "exactly" in captured.err.lower()


def test_cmd_task_fanout_refuses_blank_prompt(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        json.dumps({"task_id": "a", "prompt": "", "worktree": "w"}) + "\n",
        encoding="utf-8",
    )
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "prompt is missing or blank" in captured.err.lower()


def test_cmd_task_fanout_refuses_blank_worktree(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        json.dumps({"task_id": "a", "prompt": "p", "worktree": ""}) + "\n",
        encoding="utf-8",
    )
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "worktree is missing or blank" in captured.err.lower()


def test_cmd_task_fanout_refuses_duplicate_task_id(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    rows = [
        {"task_id": "dup-id", "prompt": "p", "worktree": "w1"},
        {"task_id": "dup-id", "prompt": "p", "worktree": "w2"},
    ]
    tasks.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "duplicate task_id" in captured.err.lower()


def test_cmd_task_fanout_refuses_duplicate_worktree(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    rows = [
        {"task_id": "a", "prompt": "p", "worktree": "shared"},
        {"task_id": "b", "prompt": "p", "worktree": "shared"},
    ]
    tasks.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "duplicate worktree" in captured.err.lower()


def test_cmd_task_fanout_refuses_invalid_pool_size(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(json.dumps({"task_id": "a", "prompt": "p", "worktree": "w"}) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=0,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "pool" in captured.err.lower()


def test_cmd_task_fanout_refuses_path_separator_in_task_id(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(json.dumps({"task_id": "bad/id", "prompt": "p", "worktree": "w"}) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "task_id" in captured.err.lower() and "separator" in captured.err.lower()


def test_cmd_task_fanout_reports_results_in_input_order_and_refuses_on_any_nonpass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    # Two distinct tasks, so one fails intentionally.
    rows = [
        {"task_id": "first", "prompt": "p", "worktree": "worktree-a"},
        {"task_id": "second", "prompt": "p", "worktree": "worktree-b"},
    ]
    tasks.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=2,
    )

    calls: list[str] = []

    def fake_run_one_delegation(command: list[str], *, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        task_id = command[command.index("--task-id") + 1]
        calls.append(task_id)
        if task_id == "second":
            time.sleep(0.05)
            return subprocess.CompletedProcess(command, EXIT_USAGE, "", "second failed")
        return subprocess.CompletedProcess(command, EXIT_PASS, "", "")

    monkeypatch.setattr("ranex.cli.fanout._run_one_delegation", fake_run_one_delegation)
    result = cmd_task_fanout(args)
    captured = capsys.readouterr()

    assert calls
    assert result == EXIT_USAGE
    lines = [line for line in captured.out.splitlines() if line.startswith("FANOUT")]
    assert lines == [
        "FANOUT  task=first  exit=0",
        "FANOUT  task=second  exit=2",
    ]
    assert "second failed" in captured.err


def test_run_one_delegation_invokes_subprocess() -> None:
    result = _run_one_delegation(["/usr/bin/true"], capture_output=True, text=True)
    assert result.returncode == 0


def test_fanout_pool_of_one_never_overlaps_and_embeds_the_bound(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Structural pin for "the wall-clock bound does not tick while queued":
    # the pool passes no timeout of its own, and the bound travels inside each
    # delegate command's argv, so a queued task's clock starts when it runs.
    target = tmp_path / "target"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    tasks = tmp_path / "tasks.jsonl"
    rows = [
        {"task_id": "first", "prompt": "p", "worktree": "worktree-a"},
        {"task_id": "second", "prompt": "p", "worktree": "worktree-b"},
    ]
    tasks.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    args = fanout_args(
        tmp_path,
        tasks=tasks,
        target=target,
        journal=journal,
        harness=harness,
        pool=1,
    )

    lock = threading.Lock()
    state = {"in_flight": 0, "overlapped": False}
    calls: list[dict[str, object]] = []

    def fake_run_one_delegation(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert "timeout" not in kwargs
        with lock:
            state["in_flight"] += 1
            if state["in_flight"] > 1:
                state["overlapped"] = True
        entered = time.monotonic()
        time.sleep(0.05)
        exited = time.monotonic()
        with lock:
            state["in_flight"] -= 1
            calls.append({"command": command, "entered": entered, "exited": exited})
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("ranex.cli.fanout._run_one_delegation", fake_run_one_delegation)
    result = cmd_task_fanout(args)

    assert result == EXIT_PASS
    assert state["overlapped"] is False
    assert len(calls) == 2
    first_call, second_call = calls
    assert second_call["entered"] >= first_call["exited"]
    observed_task_ids: list[str] = []
    for call in calls:
        command = call["command"]
        assert isinstance(command, list)
        assert command[command.index("--timeout") + 1] == "120"
        observed_task_ids.append(command[command.index("--task-id") + 1])
    assert observed_task_ids == ["first", "second"]


def test_main_parses_task_delegate_and_reaches_its_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)

    result = main(
        [
            "task",
            "delegate",
            "--task-id", "T-8-PARSE",
            "--target", str(tmp_path / "target"),
            "--worktree", str(tmp_path / "dispatch-worktree"),
            "--journal", str(tmp_path / "journal.sqlite3"),
            "--harness", str(tmp_path / "harness.sh"),
            "--model", "ranex-noop/noop",
            "--prompt", "perform work then emit",
            "--timeout", "120",
            "--suite", "/usr/bin/true",
            "--outcome", str(tmp_path / "outcome.json"),
        ]
    )
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "OPENROUTER_API_KEY" in captured.err


def test_main_parses_task_fanout_and_reaches_its_refusal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        json.dumps({"task_id": "a", "prompt": "p", "worktree": "w"}) + "\n",
        encoding="utf-8",
    )

    result = main(
        [
            "task",
            "fanout",
            "--tasks", str(tasks),
            "--target", str(tmp_path / "target"),
            "--journal", str(tmp_path / "journal.sqlite3"),
            "--harness", str(tmp_path / "harness.sh"),
            "--model", "ranex-noop/noop",
            "--timeout", "120",
            "--suite", "/usr/bin/true",
            "--outcome-dir", str(tmp_path / "outcomes"),
            "--pool", "0",
        ]
    )
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "--pool" in captured.err


def test_cmd_task_delegate_refuses_signing_key_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)

    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: True)

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    # Genuine /proc-based refusal is exercised by subprocess tests; this branch is
    # exercised here only so coverage can see the in-process code path.
    assert "refusing" in captured.err.lower()
    assert "RANEX_SIGNING_KEY" in captured.err


def test_cmd_task_delegate_refuses_missing_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = tmp_path / "missing-harness.sh"
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)

    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "refusing harness executable" in captured.err.lower()


def test_cmd_task_delegate_refuses_missing_model_credential(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)

    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "refusing to delegate execution: OPENROUTER_API_KEY is absent" in captured.err


def test_cmd_task_delegate_refuses_non_executable_harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = tmp_path / "harness.sh"
    harness.write_text("#!/usr/bin/env sh\nexit 0\n", encoding="utf-8")
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)

    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "refusing harness executable" in captured.err


def test_cmd_task_delegate_refuses_harness_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)
    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr(
        "ranex.cli.delegation._run_harness",
        lambda *_a, **_k: (_ for _ in ()).throw(OSError("boom")),
    )
    monkeypatch.setattr("ranex.cli.delegation._read_emission", lambda _path: {})
    result = cmd_task_delegate(args)
    captured = capsys.readouterr()
    assert result == EXIT_USAGE
    assert "cannot run harness" in captured.err.lower()


def test_cmd_task_delegate_refuses_harness_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)
    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr(
        "ranex.cli.delegation._run_harness",
        lambda *_a, **_k: (_ for _ in ()).throw(
            _timeout_with_returncode()
        ),
    )
    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "refusing to delegate: timed out" in captured.err.lower()
    assert Path(args.outcome).exists()
    payload = json.loads(Path(args.outcome).read_text(encoding="utf-8"))
    assert payload["timed_out"] is True
    assert payload["commit"] is None
    assert payload["suite_exit"] is None


def test_cmd_task_delegate_records_non_zero_harness_exit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    task_id = "T-8-HARNESS-NON-ZERO"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    worktree.mkdir()
    args = delegation_args(
        tmp_path,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        harness=harness,
    )
    seed_dispatch(journal, task_id, worktree, "a" * 40)

    def fake_run_harness(
        *_args: object,
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            [str(harness), "--dir", str(worktree), "--model", "ranex-noop/noop", "--auto", args.prompt],
            9,
            "",
            "",
        )

    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_run_harness)
    monkeypatch.setattr(
        "ranex.cli.delegation._read_emission",
        lambda _path: {
            "task_id": task_id,
            "worktree": str(worktree),
            "commit": "b" * 40,
        },
    )
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "b" * 40)
    monkeypatch.setattr(
        "ranex.cli.delegation._run_suite",
        lambda *_a, **_k: (0, ""),
    )
    monkeypatch.setattr(
        "ranex.cli.delegation.git",
        lambda _root, *arguments, **_kwargs: (
            subprocess.CompletedProcess(arguments, 0, "tree-emitted\n", "")
            if arguments[1].startswith("b" * 40)
            else subprocess.CompletedProcess(arguments, 0, "tree-base\n", "")
        ),
    )
    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_PASS
    assert "DELEGATED" in captured.out
    payload = json.loads(Path(args.outcome).read_text(encoding="utf-8"))
    assert payload["task_id"] == task_id
    assert payload["harness_exit"] == 9
    assert payload["timed_out"] is False
    assert payload["suite_exit"] == 0
    assert all(record.get("type") != "task-candidate" for record in Journal(journal).entries())


def _timeout_with_returncode() -> subprocess.TimeoutExpired:
    timeout = subprocess.TimeoutExpired(cmd="x", timeout=1, output="o", stderr="e")
    timeout.returncode = 9
    return timeout


def test_cmd_task_delegate_refuses_dispatch_record_without_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    task_id = "T-8-BAD"
    worktree = tmp_path / "dispatch-worktree"
    journal = tmp_path / "journal.sqlite3"
    harness = build_harness(tmp_path / "harness.sh")
    args = delegation_args(tmp_path, task_id=task_id, worktree=worktree, journal=journal, harness=harness)
    seed_dispatch(journal, task_id, worktree, "a" * 40)

    class FakeRecordJournal:
        def __init__(self, _path):
            self._entries = [{"type": "task-dispatch", "task_id": task_id, "worktree": 12, "base_commit": "a" * 40}]

        def entries(self):
            return self._entries

    monkeypatch.setattr("ranex.cli.main.Journal", FakeRecordJournal)
    monkeypatch.setattr("ranex.cli.main._perform_task_dispatch", lambda *_a, **_k: worktree)
    monkeypatch.setattr("ranex.cli.delegation._run_harness", fake_harness_run)
    monkeypatch.setattr("ranex.cli.delegation.subprocess.run", fake_subprocess_run)
    monkeypatch.setattr("ranex.cli.delegation._read_emission", lambda _path: {
        "task_id": task_id,
        "worktree": str(worktree),
        "commit": "a" * 40,
    })
    monkeypatch.setattr("ranex.cli.main.head_commit", lambda _path: "a" * 40)
    monkeypatch.setattr("ranex.cli.delegation._run_suite", lambda *args, **kwargs: (0, ""))
    monkeypatch.setattr("ranex.cli.delegation.exec_environment_holds_signing_key", lambda: False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    result = cmd_task_delegate(args)
    captured = capsys.readouterr()

    assert result == EXIT_USAGE
    assert "refusing worktree does not exist in dispatch record" in captured.err.lower()
