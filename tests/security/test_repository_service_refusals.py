"""Refusal branches surfaced by the main.py -> repository.py extraction.

This file focuses on paths that regressed from coverage bookkeeping and were not
re-driven by existing audit runs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ranex.cli.repository import (
    governed_repository_root,
    named_within_repository,
    stat_fingerprint,
    tracked_paths,
    uncommitted_paths,
)


def _init_repository(root: Path) -> None:
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    for key, value in (("user.email", "tester@example.invalid"), ("user.name", "Tester")):
        subprocess.run(["git", "-C", str(root), "config", key, value], check=True)


def test_named_within_repository_rejects_outside_paths(tmp_path: Path) -> None:
    repository_root = tmp_path

    with pytest.raises(ValueError, match=r"path resolves outside the repository"):
        named_within_repository(repository_root, "../outside")


def test_uncommitted_paths_read_tree_nonzero_return_refuses(tmp_path: Path) -> None:
    repository_root = tmp_path

    with pytest.raises(ValueError, match=r"cannot read HEAD into a scratch index"):
        uncommitted_paths(repository_root)


def test_uncommitted_paths_status_nonzero_return_refuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository_root = tmp_path / "repo"
    _init_repository(repository_root)
    (repository_root / "file.txt").write_text("data\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository_root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository_root), "commit", "-q", "-m", "initial"],
        check=True,
    )

    real_git = uncommitted_paths.__globals__["git"]

    def status_fails(path: Path, *arguments: str, **kwargs: object) -> subprocess.CompletedProcess:
        if arguments[:1] == ("read-tree",):
            return real_git(path, *arguments, **kwargs)
        if arguments[:1] == ("status",):
            return subprocess.CompletedProcess(arguments, 2, "", "forced status failure")
        return real_git(path, *arguments, **kwargs)

    with pytest.raises(ValueError, match=r"cannot read repository status: forced status failure"):
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr("ranex.cli.repository.git", status_fails)
            uncommitted_paths(repository_root)


def test_uncommitted_paths_happy_path_and_no_ignoring(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _init_repository(repository_root)
    tracked = repository_root / "tracked.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository_root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository_root), "commit", "-q", "-m", "initial"],
        check=True,
    )

    tracked.write_text("dirty\n", encoding="utf-8")
    assert uncommitted_paths(repository_root) == ("tracked.txt",)


def test_uncommitted_paths_skips_blank_status_lines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository_root = tmp_path / "repo"
    _init_repository(repository_root)
    tracked = repository_root / "tracked.txt"
    tracked.write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository_root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository_root), "commit", "-q", "-m", "initial"],
        check=True,
    )

    real_git = uncommitted_paths.__globals__["git"]

    def status_with_blank_line(
        path: Path, *arguments: str, **kwargs: object
    ) -> subprocess.CompletedProcess:
        if arguments[:1] == ("read-tree",):
            return real_git(path, *arguments, **kwargs)
        if arguments[:1] == ("status",):
            return subprocess.CompletedProcess(arguments, 0, "\n M tracked.txt", "")
        return real_git(path, *arguments, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("ranex.cli.repository.git", status_with_blank_line)
        tracked.write_text("dirty\n", encoding="utf-8")
        assert uncommitted_paths(repository_root) == ("tracked.txt",)


def test_uncommitted_paths_ignoring_path_outside_repository_does_not_raise(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _init_repository(repository_root)
    (repository_root / "tracked.txt").write_text("committed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository_root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository_root), "commit", "-q", "-m", "initial"],
        check=True,
    )

    (repository_root / "untracked.txt").write_text("new\n", encoding="utf-8")
    assert uncommitted_paths(repository_root, ignoring=tmp_path / "outside.txt") == (
        "untracked.txt",
    )


def test_tracked_paths_happy_path(tmp_path: Path) -> None:
    repository_root = tmp_path / "repo"
    _init_repository(repository_root)
    (repository_root / "zeta.txt").write_text("z\n", encoding="utf-8")
    (repository_root / "alpha.txt").write_text("a\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository_root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository_root), "commit", "-q", "-m", "initial"],
        check=True,
    )

    assert tracked_paths(repository_root) == ("alpha.txt", "zeta.txt")


def test_tracked_paths_nonzero_return_refuses(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"cannot list the tracked files"):
        tracked_paths(tmp_path)


def test_stat_fingerprint_records_missing_paths_as_none(tmp_path: Path) -> None:
    assert stat_fingerprint(tmp_path, ("missing.txt",)) == {"missing.txt": None}


def test_governed_repository_root_nonzero_return_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failing_rev_parse(_repository_root: Path, *arguments: str, **kwargs: object) -> subprocess.CompletedProcess:
        return subprocess.CompletedProcess(arguments, 1, "", "rev-parse failure")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("ranex.cli.repository.git", failing_rev_parse)
        with pytest.raises(
            ValueError, match=r"cannot locate the repository containing the Ranex CLI"
        ):
            governed_repository_root()
