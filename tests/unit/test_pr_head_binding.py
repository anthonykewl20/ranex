"""Unit arms for the PR-head binding: the formula, the shape, the refusals.

The digest literal below is computed by hand from the pinned subject formula
(`sha256` over canonical JSON of `{"tree": <oid>}`), not by calling the code
under test — so a change to the arithmetic changes this test, not follows it.
"""

from __future__ import annotations

import pytest

from ranex.github_app.binding import (
    BindingRefusal,
    PrHeadBinding,
    bind_pr_head,
    subject_digest_for_tree,
)


def test_the_digest_formula_is_the_pinned_subject_formula() -> None:
    assert (
        subject_digest_for_tree("0123456789abcdef0123456789abcdef01234567")
        == "sha256:e72f62a73517e18cb6b0a9f3615bf2f998c7610e679b6136153ab37b9a6b7439"
    )


def test_two_trees_with_equal_content_but_different_names_differ() -> None:
    # Content addressing, forwards: distinct trees are distinct subjects.
    assert subject_digest_for_tree("0" * 40) != subject_digest_for_tree("1" * 40)


def test_the_binding_carries_head_tree_and_subject() -> None:
    binding = PrHeadBinding(
        head_sha="a" * 40,
        tree="b" * 40,
        subject_digest=subject_digest_for_tree("b" * 40),
    )
    assert binding.subject_digest == subject_digest_for_tree(binding.tree)


def test_a_malformed_sha_refuses_before_git_is_asked() -> None:
    # A path that is not a repository proves no subprocess ran: the refusal
    # must come from the SHA itself.
    with pytest.raises(BindingRefusal) as raised:
        bind_pr_head(path_of_no_repository(), "deadbeef")
    assert raised.value.code == "E-GITHUB-BAD-SHA"


@pytest.mark.parametrize(
    "sha",
    [
        "DEADBEEF" + "0" * 32,  # uppercase hex is not a git object id
        "g" * 40,  # not hex at all
        "0" * 41,  # too long
        "0" * 39,  # too short
        "",
    ],
)
def test_every_malformed_shape_refuses_with_the_same_code(sha: str) -> None:
    with pytest.raises(BindingRefusal) as raised:
        bind_pr_head(path_of_no_repository(), sha)
    assert raised.value.code == "E-GITHUB-BAD-SHA"


def path_of_no_repository():
    from pathlib import Path

    return Path("/nonexistent-repository-for-binding-unit-tests")
