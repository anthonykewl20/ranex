"""Real-git contracts for publication into checked-out target branches."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from test_task_merge_real_flows import RealAttempt, RealRepository, dispatch_judge, git, invoke

from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

TARGET_MAIN = "refs/heads/main"
TARGET_RELEASE = "refs/heads/release"


def _prepared_attempt(
    tmp_path: Path, task_id: str, *, target_ref: str = TARGET_MAIN
) -> tuple[RealRepository, RealAttempt]:
    scenario = RealRepository.create(tmp_path)
    if target_ref != TARGET_MAIN:
        git(scenario.repo, "update-ref", target_ref, git(scenario.repo, "rev-parse", TARGET_MAIN))
    attempt = dispatch_judge(scenario, task_id, target_ref=target_ref)
    # The real-flow helper writes its mutable evidence fixture to this checkout.
    # Publication must observe a genuinely clean target worktree.
    git(scenario.repo, "checkout", "--", "governance/evidence.json")
    assert git(scenario.repo, "status", "--porcelain") == ""
    return scenario, attempt


def test_checked_out_clean_target_is_synchronized_after_publication(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario, attempt = _prepared_attempt(tmp_path, "worktree-clean")

    assert invoke(scenario.repo, attempt.merge_args()) == 0

    output = capsys.readouterr().out
    assert (
        f"PUBLISHED  task={attempt.task_id}  candidate={attempt.candidate}  "
        f"target={TARGET_MAIN}"
    ) in output
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    assert git(scenario.repo, "rev-parse", "HEAD") == attempt.candidate
    assert git(scenario.repo, "status", "--porcelain") == ""
    assert (scenario.repo / f"{attempt.task_id}.txt").read_text(encoding="utf-8") == (
        f"candidate {attempt.task_id} 0\n"
    )


def test_dirty_checked_out_target_intersecting_candidate_refuses_before_ref_move(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario, attempt = _prepared_attempt(tmp_path, "worktree-dirty-intersecting")
    conflicting_path = f"{attempt.task_id}.txt"
    conflicting_file = scenario.repo / conflicting_path
    conflicting_file.write_text("do not overwrite\n", encoding="utf-8")
    operator_bytes = conflicting_file.read_bytes()

    assert invoke(scenario.repo, attempt.merge_args()) == 1

    error = capsys.readouterr().err
    assert "sad-path-23 worktree-conflict" in error
    assert conflicting_path in error
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.tip
    assert conflicting_file.read_bytes() == operator_bytes


def test_dirty_rename_pre_image_refuses_before_the_ref_moves(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = RealRepository.create(tmp_path)
    (scenario.repo / "old.txt").write_text("base old\n", encoding="utf-8")
    git(scenario.repo, "add", "old.txt")
    git(scenario.repo, "commit", "-q", "-m", "old-file")

    def build(worktree: Path) -> None:
        (worktree / "old.txt").write_text("candidate old\n", encoding="utf-8")
        git(worktree, "add", "old.txt")
        git(worktree, "commit", "-q", "-m", "change-old-file")

    attempt = dispatch_judge(scenario, "worktree-dirty-rename", candidate_builder=build)
    git(scenario.repo, "checkout", "--", "governance/evidence.json")
    assert git(scenario.repo, "status", "--porcelain") == ""
    git(scenario.repo, "mv", "old.txt", "operator-old.txt")
    target_before = git(scenario.repo, "rev-parse", TARGET_MAIN)

    assert invoke(scenario.repo, attempt.merge_args()) == 1

    error = capsys.readouterr().err
    assert "sad-path-23 worktree-conflict" in error
    assert "old.txt" in error
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == target_before
    assert git(scenario.repo, "status", "--porcelain").startswith("R")
    assert (scenario.repo / "operator-old.txt").is_file()


def test_untracked_file_at_a_candidate_path_refuses_before_the_ref_moves(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = RealRepository.create(tmp_path)

    def build(worktree: Path) -> None:
        path = worktree / "dir" / "file.txt"
        path.parent.mkdir()
        path.write_text("candidate\n", encoding="utf-8")
        git(worktree, "add", "dir/file.txt")
        git(worktree, "commit", "-q", "-m", "add-dir-file")

    attempt = dispatch_judge(scenario, "worktree-untracked-path", candidate_builder=build)
    git(scenario.repo, "checkout", "--", "governance/evidence.json")
    assert git(scenario.repo, "status", "--porcelain") == ""
    operator_file = scenario.repo / "dir" / "file.txt"
    operator_file.parent.mkdir()
    operator_bytes = b"operator bytes\n"
    operator_file.write_bytes(operator_bytes)
    target_before = git(scenario.repo, "rev-parse", TARGET_MAIN)

    assert invoke(scenario.repo, attempt.merge_args()) == 1

    error = capsys.readouterr().err
    assert "sad-path-23 worktree-conflict" in error
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == target_before
    assert operator_file.read_bytes() == operator_bytes


def test_ignored_file_at_a_candidate_path_is_never_replaced(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = RealRepository.create(tmp_path)
    ignore = scenario.repo / ".gitignore"
    ignore.write_text(ignore.read_text(encoding="utf-8") + "path\n", encoding="utf-8")
    git(scenario.repo, "add", ".gitignore")
    git(scenario.repo, "commit", "-q", "-m", "ignore-path")

    def build(worktree: Path) -> None:
        (worktree / "path").write_text("candidate\n", encoding="utf-8")
        git(worktree, "add", "-f", "path")
        git(worktree, "commit", "-q", "-m", "add-ignored-path")

    attempt = dispatch_judge(scenario, "worktree-ignored-path", candidate_builder=build)
    git(scenario.repo, "checkout", "--", "governance/evidence.json")
    assert git(scenario.repo, "status", "--porcelain") == ""
    operator_file = scenario.repo / "path"
    operator_file.write_text("operator secrets\n", encoding="utf-8")
    target_before = git(scenario.repo, "rev-parse", TARGET_MAIN)

    assert invoke(scenario.repo, attempt.merge_args()) == 1

    error = capsys.readouterr().err
    assert "sad-path-23 worktree-conflict" in error
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == target_before
    assert operator_file.read_text(encoding="utf-8") == "operator secrets\n"


def test_ignored_file_disjoint_from_the_candidate_publishes_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario = RealRepository.create(tmp_path)
    ignore = scenario.repo / ".gitignore"
    ignore.write_text(ignore.read_text(encoding="utf-8") + "scratch.log\n", encoding="utf-8")
    git(scenario.repo, "add", ".gitignore")
    git(scenario.repo, "commit", "-q", "-m", "ignore-scratch")

    def build(worktree: Path) -> None:
        (worktree / "pub.txt").write_text("published\n", encoding="utf-8")
        git(worktree, "add", "pub.txt")
        git(worktree, "commit", "-q", "-m", "add-published-file")

    attempt = dispatch_judge(scenario, "worktree-ignored-disjoint", candidate_builder=build)
    git(scenario.repo, "checkout", "--", "governance/evidence.json")
    assert git(scenario.repo, "status", "--porcelain") == ""
    operator_file = scenario.repo / "scratch.log"
    operator_file.write_text("operator scratch\n", encoding="utf-8")

    assert invoke(scenario.repo, attempt.merge_args()) == 0

    assert (
        f"PUBLISHED  task={attempt.task_id}  candidate={attempt.candidate}  "
        f"target={TARGET_MAIN}"
    ) in capsys.readouterr().out
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    assert git(scenario.repo, "rev-parse", "HEAD") == attempt.candidate
    assert git(scenario.repo, "status", "--porcelain") == ""
    assert operator_file.read_text(encoding="utf-8") == "operator scratch\n"
    assert (scenario.repo / "pub.txt").read_text(encoding="utf-8") == "published\n"


def test_dirty_checked_out_target_disjoint_from_candidate_is_preserved(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario, attempt = _prepared_attempt(tmp_path, "worktree-dirty-disjoint")
    local_path = scenario.repo / "base.txt"
    local_path.write_text("operator change\n", encoding="utf-8")

    assert invoke(scenario.repo, attempt.merge_args()) == 0

    assert (
        f"PUBLISHED  task={attempt.task_id}  candidate={attempt.candidate}  "
        f"target={TARGET_MAIN}"
    ) in capsys.readouterr().out
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    assert git(scenario.repo, "rev-parse", "HEAD") == attempt.candidate
    assert (scenario.repo / f"{attempt.task_id}.txt").read_text(encoding="utf-8") == (
        f"candidate {attempt.task_id} 0\n"
    )
    assert local_path.read_text(encoding="utf-8") == "operator change\n"
    assert git(scenario.repo, "status", "--porcelain") == "M base.txt"


def test_unchecked_out_target_preserves_ref_only_publication(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario, attempt = _prepared_attempt(
        tmp_path, "worktree-unchecked-out", target_ref=TARGET_RELEASE
    )

    assert invoke(scenario.repo, attempt.merge_args()) == 0

    assert (
        f"PUBLISHED  task={attempt.task_id}  candidate={attempt.candidate}  "
        f"target={TARGET_RELEASE}"
    ) in capsys.readouterr().out
    assert git(scenario.repo, "rev-parse", TARGET_RELEASE) == attempt.candidate
    assert git(scenario.repo, "rev-parse", "HEAD") == attempt.tip


def test_sync_failure_reports_partial_state_and_requires_explicit_repair(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    scenario, attempt = _prepared_attempt(tmp_path, "worktree-sync-failure")
    original_mode = scenario.repo.stat().st_mode
    scenario.repo.chmod(0o500)
    try:
        assert invoke(scenario.repo, attempt.merge_args()) == 1
    finally:
        scenario.repo.chmod(original_mode)

    captured = capsys.readouterr()
    repair = (
        f"git -C {scenario.repo} checkout --detach {attempt.tip} && "
        f"git -C {scenario.repo} merge --ff-only {attempt.candidate} && "
        f"git -C {scenario.repo} symbolic-ref HEAD {TARGET_MAIN}"
    )
    assert "PUBLISHED" not in captured.out
    assert "ref moved to" in captured.err
    assert repair in captured.err
    assert git(scenario.repo, "rev-parse", TARGET_MAIN) == attempt.candidate
    outcomes = [
        entry
        for entry in Journal(scenario.journal).entries()
        if entry.get("type") == "task-merge-outcome" and entry.get("task_id") == attempt.task_id
    ]
    assert outcomes[-1]["outcome"] == "ABORTED"
    assert repair in str(outcomes[-1]["detail"])

    assert invoke(scenario.repo, attempt.merge_args()) == 1
    retry = capsys.readouterr()
    assert "sad-path-9 tip-mismatch" in retry.err
    assert "PUBLISHED" not in retry.out

    subprocess.run(
        ["git", "-C", str(scenario.repo), "checkout", "--detach", attempt.tip],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "-C", str(scenario.repo), "merge", "--ff-only", attempt.candidate],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        ["git", "-C", str(scenario.repo), "symbolic-ref", "HEAD", TARGET_MAIN],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert git(scenario.repo, "rev-parse", "HEAD") == attempt.candidate
    assert git(scenario.repo, "status", "--porcelain") == ""
