"""'Governs only this repository' must be enforced, not merely stated.

Slice definition §9, last three failure modes. These are the difference between
a prose boundary and a real one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ranex.cli.confinement import resolve_within_repository


def test_relative_path_inside_the_repository_is_allowed(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    target = resolve_within_repository(tmp_path, "docs")
    assert target == (tmp_path / "docs").resolve()


def test_absolute_path_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absolute"):
        resolve_within_repository(tmp_path, "/etc/passwd")


def test_traversal_above_the_repository_root_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        resolve_within_repository(tmp_path, "../../etc/passwd")


def test_sneaky_traversal_that_returns_inside_is_still_refused(
    tmp_path: Path,
) -> None:
    """`a/../../root/a` leaves the repository even though it ends inside one."""

    with pytest.raises(ValueError, match="outside"):
        resolve_within_repository(tmp_path, "docs/../../escape")


def test_remote_target_is_refused(tmp_path: Path) -> None:
    for remote in (
        "https://github.com/other/repo",
        "git@github.com:other/repo.git",
        "ssh://host/repo",
    ):
        with pytest.raises(ValueError, match="remote"):
            resolve_within_repository(tmp_path, remote)


def test_symlink_escaping_the_repository_is_refused(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside_repo"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "escape"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="outside"):
        resolve_within_repository(tmp_path, "escape")
