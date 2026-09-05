"""PR-head binding: a head SHA derives the subject a verdict must already name.

The binding is a projection, not a signed surface (ADR-049): the signed
subject stays the git tree digest, and the mapping from a pull-request head
SHA to its tree is taken from the local git object store, which carries its
own hashes. No GitHub API response is ever asked what a commit contains.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ranex.cli.repository import git
from ranex.foundation.canonical import canonical_sha256

_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class BindingRefusal(ValueError):
    """A head SHA that cannot become a subject, named for the operator."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code} {detail}")
        self.code = code
        self.detail = detail


def subject_digest_for_tree(tree: str) -> str:
    """The exact subject formula (`subject_digest_for`), restated for trees.

    Kept beside the binding so the outward derivation cannot drift from the
    judged one by a refactor it never sees; a contract test pins the two
    together against a live repository.
    """

    return "sha256:" + canonical_sha256({"tree": tree})


@dataclass(frozen=True, slots=True)
class PrHeadBinding:
    """What a PR head is, as a Ranex subject: content, not names."""

    head_sha: str
    tree: str
    subject_digest: str


def fetch_pr_head(repository_root: Path, remote: str, head_sha: str) -> None:
    """Bring the head commit's objects into the local store, or refuse.

    `git fetch` is given the SHA alone as the refspec: no remote branch name
    is involved, so the fetch cannot be steered by what a remote chooses to
    point a name at — only by the object GitHub's event named.
    """

    if not isinstance(head_sha, str) or not _SHA_PATTERN.fullmatch(head_sha):
        raise BindingRefusal("E-GITHUB-BAD-SHA", "head must be a 40-hex commit id")
    try:
        fetched = git(repository_root, "fetch", "--no-tags", remote, head_sha, timeout=30)
    except subprocess.TimeoutExpired as exc:
        raise BindingRefusal("E-GITHUB-UNFETCHABLE-HEAD", "git fetch exceeded 30 seconds") from exc
    if fetched.returncode != 0:
        raise BindingRefusal(
            "E-GITHUB-UNFETCHABLE-HEAD",
            f"git fetch {remote} {head_sha}: {fetched.stderr.strip()}",
        )


def bind_pr_head(repository_root: Path, head_sha: str) -> PrHeadBinding:
    """Derive the binding for `head_sha` from the local object store."""

    if not isinstance(head_sha, str) or not _SHA_PATTERN.fullmatch(head_sha):
        raise BindingRefusal(
            "E-GITHUB-BAD-SHA", f"not a 40-hex commit id: {head_sha!r}"
        )
    resolved = git(repository_root, "rev-parse", f"{head_sha}^{{tree}}")
    if resolved.returncode != 0:
        raise BindingRefusal(
            "E-GITHUB-UNFETCHABLE-HEAD",
            f"cannot resolve {head_sha!r}: {resolved.stderr.strip()}",
        )
    tree = resolved.stdout.strip()
    if not _SHA_PATTERN.fullmatch(tree):
        raise BindingRefusal(
            "E-GITHUB-UNFETCHABLE-HEAD", f"not a 40-hex tree id: {tree!r}"
        )
    return PrHeadBinding(
        head_sha=head_sha, tree=tree, subject_digest=subject_digest_for_tree(tree)
    )


def revalidate_pr_head(repository_root: Path, binding: PrHeadBinding) -> None:
    """Refuse if the ground moved under a binding already derived.

    The check-run publication names the head SHA it was derived from; if the
    local store can no longer produce that SHA's tree by the time the
    pipeline reaches the wire, the binding says so rather than publishing a
    check about an object it can no longer testify to.
    """

    resolved = git(repository_root, "rev-parse", f"{binding.head_sha}^{{tree}}")
    if resolved.returncode != 0 or resolved.stdout.strip() != binding.tree:
        raise BindingRefusal(
            "E-GITHUB-HEAD-MOVED",
            f"{binding.head_sha!r} no longer resolves to tree {binding.tree}",
        )
