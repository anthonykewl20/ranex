"""Integration arms for `github bind`: real git stores, real CLI subprocess.

The journey the receiver will make, exercised directly: a source repository
standing in for GitHub's object store, an operator clone that must fetch the
head SHA before it can name the subject, and the CLI printing exactly what
the later slices will publish against.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from ranex.github_app.binding import (
    BindingRefusal,
    bind_pr_head,
    fetch_pr_head,
    revalidate_pr_head,
    subject_digest_for_tree,
)


def clean_env() -> dict[str, str]:
    return {
        "PATH": os.path.dirname(sys.executable) + os.pathsep + os.defpath,
        "PYTHONPATH": "src",
        "LC_ALL": "C",
    }


def git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True, text=True, check=True, env=clean_env(),
    )
    return result.stdout.strip()


def seeded_repository(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=clean_env())
    git(path, "config", "user.email", "bind-test@example.invalid")
    git(path, "config", "user.name", "Bind Test")
    (path / "work.txt").write_text("pull request content\n", encoding="utf-8")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "the PR head")
    # GitHub serves arbitrary SHAs to fetch; a local path remote refuses to
    # until it is told to, the same server-side opt-in GitHub already runs.
    git(path, "config", "uploadpack.allowAnySHA1InWant", "true")
    return path


def operator_clone(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(path)], check=True, env=clean_env())
    git(path, "config", "user.email", "operator@example.invalid")
    git(path, "config", "user.name", "Operator")
    return path


def invoke(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python", "-m", "ranex.cli.main", *arguments],
        capture_output=True, text=True, check=False, env=clean_env(),
    )


def test_fetch_then_bind_names_the_exact_tree_and_subject(tmp_path: Path) -> None:
    source = seeded_repository(tmp_path / "source")
    head = git(source, "rev-parse", "HEAD")
    tree = git(source, "rev-parse", "HEAD^{tree}")
    clone = operator_clone(tmp_path / "clone")

    fetch_pr_head(clone, str(source), head)
    binding = bind_pr_head(clone, head)

    assert binding.head_sha == head
    assert binding.tree == tree
    assert binding.subject_digest == subject_digest_for_tree(tree)


def test_bind_refuses_a_head_the_clone_never_fetched(tmp_path: Path) -> None:
    source = seeded_repository(tmp_path / "source")
    head = git(source, "rev-parse", "HEAD")
    clone = operator_clone(tmp_path / "clone")

    try:
        bind_pr_head(clone, head)
    except BindingRefusal as refusal:
        assert refusal.code == "E-GITHUB-UNFETCHABLE-HEAD"
    else:
        raise AssertionError("an unfetched head must refuse")


def test_fetch_refuses_a_sha_the_source_does_not_hold(tmp_path: Path) -> None:
    source = seeded_repository(tmp_path / "source")
    clone = operator_clone(tmp_path / "clone")

    try:
        fetch_pr_head(clone, str(source), "9" * 40)
    except BindingRefusal as refusal:
        assert refusal.code == "E-GITHUB-UNFETCHABLE-HEAD"
    else:
        raise AssertionError("an unknown head must refuse")


def test_revalidation_refuses_when_the_ground_moves(tmp_path: Path) -> None:
    source = seeded_repository(tmp_path / "source")
    head = git(source, "rev-parse", "HEAD")
    clone = operator_clone(tmp_path / "clone")
    fetch_pr_head(clone, str(source), head)
    binding = bind_pr_head(clone, head)

    # The ground moves under a derived binding: the object vanishes locally
    # (an aggressive gc between derivation and publication would do this).
    loose = clone / ".git" / "objects" / head[:2] / head[2:]
    assert loose.is_file(), "fetched objects arrive loose in a fresh clone"
    loose.unlink()

    try:
        revalidate_pr_head(clone, binding)
    except BindingRefusal as refusal:
        assert refusal.code == "E-GITHUB-HEAD-MOVED"
    else:
        raise AssertionError("a moved head must refuse")


def test_the_cli_prints_the_binding(tmp_path: Path) -> None:
    source = seeded_repository(tmp_path / "source")
    head = git(source, "rev-parse", "HEAD")
    tree = git(source, "rev-parse", "HEAD^{tree}")
    clone = operator_clone(tmp_path / "clone")
    fetch_pr_head(clone, str(source), head)

    result = invoke("github", "bind", "--head-sha", head, "--repository", str(clone))

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        f"BIND  head={head}  tree={tree}",
        f"      subject={subject_digest_for_tree(tree)}",
    ]


def test_the_cli_refuses_a_malformed_sha(tmp_path: Path) -> None:
    clone = operator_clone(tmp_path / "clone")
    result = invoke("github", "bind", "--head-sha", "nope", "--repository", str(clone))
    assert result.returncode == 2
    assert "ERROR  E-GITHUB-BAD-SHA" in result.stderr


def test_the_cli_refuses_an_unfetched_head(tmp_path: Path) -> None:
    source = seeded_repository(tmp_path / "source")
    head = git(source, "rev-parse", "HEAD")
    clone = operator_clone(tmp_path / "clone")
    result = invoke("github", "bind", "--head-sha", head, "--repository", str(clone))
    assert result.returncode == 2
    assert "ERROR  E-GITHUB-UNFETCHABLE-HEAD" in result.stderr


def test_the_binding_digest_is_byte_identical_to_the_judged_subject(
    tmp_path: Path,
) -> None:
    from ranex.cli.main import subject_digest_for

    source = seeded_repository(tmp_path / "source")
    head = git(source, "rev-parse", "HEAD")
    clone = operator_clone(tmp_path / "clone")
    fetch_pr_head(clone, str(source), head)

    binding = bind_pr_head(clone, head)

    # The outward binding and the judged subject are the same bytes; if this
    # ever fails, the two formulas drifted and every check is about the
    # wrong tree.
    assert binding.subject_digest == subject_digest_for(clone, head)
