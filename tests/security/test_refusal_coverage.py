"""Security-relevant refusal branches must be reached by focused tests."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ranex.cli import toolchain
from ranex.cli.subject import SubjectError, TreeEntry, _tree_entries, _verified_blob

OID = "0" * 40


def git_result(
    *, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess((), returncode, stdout, stderr)


def tree_output(*paths: str) -> bytes:
    return b"".join(
        f"100644 blob {OID}\t{path}\0".encode() for path in paths
    )


def test_uninspectable_toolchain_directory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "bin"
    monkeypatch.setattr(
        Path, "stat", lambda _path: (_ for _ in ()).throw(PermissionError("denied"))
    )

    with pytest.raises(
        toolchain.ToolchainError,
        match=r"cannot inspect pinned toolchain directory .*denied",
    ):
        toolchain._refuse_writable(directory, directory)


def test_directory_writable_by_effective_uid_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "bin"
    directory.mkdir(mode=0o700)
    monkeypatch.setattr(toolchain.os, "geteuid", lambda: 1234)
    monkeypatch.setattr(toolchain.os, "access", lambda *_args, **_kwargs: True)

    with pytest.raises(
        toolchain.ToolchainError, match=r"writable by effective uid 1234"
    ):
        toolchain._refuse_writable(directory, directory)


def test_uninspectable_pinned_tool_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable = tmp_path / "git"
    monkeypatch.setattr(
        Path, "stat", lambda _path: (_ for _ in ()).throw(PermissionError("denied"))
    )

    with pytest.raises(
        toolchain.ToolchainError, match=r"cannot inspect pinned tool .*denied"
    ):
        toolchain.refuse_writable_executable(executable)


def test_pinned_toolchain_candidate_that_is_not_a_directory_is_refused(
    tmp_path: Path,
) -> None:
    candidate = tmp_path / "bin"
    candidate.write_text("not a directory", encoding="utf-8")

    with pytest.raises(
        toolchain.ToolchainError, match=r"pinned toolchain directory .* is not a directory"
    ):
        toolchain.pinned_directories((candidate,))


def test_tool_name_with_path_components_is_refused() -> None:
    with pytest.raises(
        toolchain.ToolchainError,
        match=r"tool name must be a single path component: '../git'",
    ):
        toolchain.resolve_tool("../git")


def test_malformed_tree_entry_is_refused(tmp_path: Path) -> None:
    git = lambda *_args, **_kwargs: git_result(stdout=b"not metadata\0")

    with pytest.raises(SubjectError, match=r"malformed tree entry in 'HEAD'"):
        _tree_entries(tmp_path, "HEAD", git)


def test_unsafe_tree_path_is_refused(tmp_path: Path) -> None:
    git = lambda *_args, **_kwargs: git_result(stdout=tree_output("../escape"))

    with pytest.raises(
        SubjectError, match=r"refusing unsafe path '../escape'.*'HEAD'"
    ):
        _tree_entries(tmp_path, "HEAD", git)


def test_dot_git_tree_path_is_refused(tmp_path: Path) -> None:
    git = lambda *_args, **_kwargs: git_result(stdout=tree_output("nested/.git/config"))

    with pytest.raises(SubjectError, match=r"refusing unsafe path 'nested/.git/config'.*'HEAD'"):
        _tree_entries(tmp_path, "HEAD", git)


def test_duplicate_tree_path_is_refused(tmp_path: Path) -> None:
    git = lambda *_args, **_kwargs: git_result(stdout=tree_output("same", "same"))

    with pytest.raises(SubjectError, match=r"duplicate path 'same'.*'HEAD'"):
        _tree_entries(tmp_path, "HEAD", git)


def test_unreadable_tree_blob_is_refused(tmp_path: Path) -> None:
    entry = TreeEntry("100644", "blob", OID, "payload")
    git = lambda *_args, **_kwargs: git_result(returncode=1, stderr=b"permission denied")

    with pytest.raises(
        SubjectError,
        match=rf"cannot read blob {OID} for 'payload': permission denied",
    ):
        _verified_blob(tmp_path, entry, git)
