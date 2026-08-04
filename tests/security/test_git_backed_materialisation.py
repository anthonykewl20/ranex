"""ADR-009 — a materialised subject has a fresh, contained Git identity."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from ranex.cli import subject, toolchain
from ranex.cli.main import git
from ranex.cli.subject import SubjectError, materialise_subject


def git_output(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def commit(repository: Path, path: str, content: str) -> None:
    destination = repository / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-f", path], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "subject"],
        check=True,
    )


@pytest.fixture()
def repository(tmp_path: Path) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    commit(repository, ".gitignore", "ignored.txt\n")
    commit(repository, "ignored.txt", "tracked despite ignore\n")
    commit(repository, "nested/payload.txt", "subject bytes\n")
    return repository


def test_materialisation_is_deterministic_identical_and_hygienic(repository: Path) -> None:
    commit_ids: list[str] = []
    for _ in range(2):
        with materialise_subject(repository, "HEAD", git) as sample:
            commit_ids.append(git_output(sample.tree, "rev-parse", "HEAD"))
            assert git_output(sample.tree, "rev-parse", "HEAD^{tree}") == git_output(
                repository, "rev-parse", "HEAD^{tree}"
            )
            assert git_output(sample.tree, "remote") == ""
            assert git_output(sample.tree, "rev-list", "--count", "HEAD") == "1"
            assert not (sample.tree / ".git" / "logs").exists()
            assert not (sample.tree / ".git" / "refs" / "stash").exists()
            hooks = sample.tree / ".git" / "hooks"
            assert not hooks.exists() or not any(hooks.iterdir())
            assert (sample.tree / "ignored.txt").read_text(encoding="utf-8") == "tracked despite ignore\n"
    assert commit_ids[0] == commit_ids[1]


def test_materialisation_does_not_share_the_governed_object_store(repository: Path) -> None:
    governed_objects = sorted((repository / ".git" / "objects").rglob("*"))
    governed_refs = git_output(repository, "show-ref")
    with materialise_subject(repository, "HEAD", git) as sample:
        assert (sample.tree / ".git" / "objects").resolve() != (repository / ".git" / "objects").resolve()
        subprocess.run(
            ["git", "-C", str(sample.tree), "-c", "user.name=Attack", "-c", "user.email=a@example.invalid", "commit", "--allow-empty", "-qm", "attack"],
            check=True,
        )
    assert sorted((repository / ".git" / "objects").rglob("*")) == governed_objects
    assert git_output(repository, "show-ref") == governed_refs


@pytest.mark.parametrize("failure", ["init", "commit"])
def test_construction_failure_refuses_and_removes_the_sample(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    root = tmp_path / "sample"
    root.mkdir()
    monkeypatch.setattr(subject, "_materialisation_root", lambda _repository: root)

    def failing_git(path: Path, *arguments: str, **kwargs: object) -> subprocess.CompletedProcess:
        if failure in arguments:
            return subprocess.CompletedProcess(arguments, 1, "", "intentional failure")
        return git(path, *arguments, **kwargs)

    with pytest.raises(SubjectError, match=rf"cannot {failure} materialised repository.*intentional failure"):
        with materialise_subject(repository, "HEAD", failing_git):
            pytest.fail("a partial materialisation was yielded")
    assert not root.exists()


def test_a_failing_tree_comparison_refuses_and_removes_the_sample(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "sample"
    root.mkdir()
    monkeypatch.setattr(subject, "_materialisation_root", lambda _repository: root)

    def failing_git(path: Path, *arguments: str, **kwargs: object) -> subprocess.CompletedProcess:
        if "rev-parse" in arguments:
            return subprocess.CompletedProcess(arguments, 1, "", "intentional failure")
        return git(path, *arguments, **kwargs)

    with pytest.raises(SubjectError, match=r"cannot compare materialised tree.*intentional failure"):
        with materialise_subject(repository, "HEAD", failing_git):
            pytest.fail("a partial materialisation was yielded")
    assert not root.exists()


def test_a_sample_tree_that_is_not_the_subject_refuses(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "sample"
    root.mkdir()
    monkeypatch.setattr(subject, "_materialisation_root", lambda _repository: root)

    def substituting_git(path: Path, *arguments: str, **kwargs: object) -> subprocess.CompletedProcess:
        if "rev-parse" in arguments and path == repository:
            return subprocess.CompletedProcess(arguments, 0, "0" * 40 + "\n", "")
        return git(path, *arguments, **kwargs)

    with pytest.raises(SubjectError, match=r"refusing materialised tree that does not match"):
        with materialise_subject(repository, "HEAD", substituting_git):
            pytest.fail("a substituted materialisation was yielded")
    assert not root.exists()


def test_absent_git_refuses_and_removes_the_sample(
    repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "sample"
    root.mkdir()
    monkeypatch.setattr(subject, "_materialisation_root", lambda _repository: root)

    def missing_git(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess:
        raise toolchain.ToolchainError("tool 'git' is absent from the pinned toolchain")

    with pytest.raises(toolchain.ToolchainError, match="absent from the pinned toolchain"):
        with materialise_subject(repository, "HEAD", missing_git):
            pytest.fail("a partial materialisation was yielded")
    assert not root.exists()
