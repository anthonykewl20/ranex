"""The real pinned Ranex patch makes its independently run suite green."""

from __future__ import annotations

from pathlib import Path

from _provider_neutral_subject import PATCH_COMMIT, git, materialize, run_focused


def test_real_ranex_patch_is_green_after_delegation(tmp_path: Path) -> None:
    subject = materialize(tmp_path, commit=PATCH_COMMIT)
    assert git(subject, "rev-parse", "HEAD") == PATCH_COMMIT

    completed = run_focused(subject)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "57 passed" in completed.stdout


def test_real_ranex_patch_is_an_existing_git_commit(tmp_path: Path) -> None:
    subject = materialize(tmp_path, commit=PATCH_COMMIT)
    commit_type = git(subject, "cat-file", "-t", PATCH_COMMIT)
    parent_type = git(subject, "cat-file", "-t", f"{PATCH_COMMIT}^")

    assert commit_type == "commit"
    assert parent_type == "commit"
    assert git(subject, "show", "-s", "--format=%s", PATCH_COMMIT) == (
        "feat(SLICE-072): close dynamic runtime authority"
    )
