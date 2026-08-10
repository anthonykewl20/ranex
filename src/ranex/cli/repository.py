"""Repository-query service helpers: mechanics only, no policy or orchestration."""

from __future__ import annotations

import os
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

from ranex.cli.toolchain import resolve_tool

# `git replace` writes `refs/replace/<oid>`, and from that moment every command
# in the repository resolves that object to a substitute the observed party
# authored. `git cat-file blob HEAD:gates.yaml` returns bytes no commit carries;
# `git rev-parse HEAD^{tree}` peels to a tree the commit does not name while
# `git rev-parse HEAD` still reports the honest id. It needs no privilege, is an
# ordinary documented command, appears in no commit and in no `git log`, leaves
# `git status` empty, and is never pushed or fetched — so a reviewer reading the
# branch on any other machine sees the honest tree, and only the machine
# deciding the verdict sees the substitute.
#
# That defeats ADR-002 underneath every defence it built. The path is committed,
# the name is asked about exactly as the operator typed it, and the on-disk bytes
# match the "committed" bytes — because both sides of the comparison are the
# attacker's. "Reviewed and committed are the same fact" only holds while git
# answers honestly about what a commit carries, and git can be told not to.
_NO_SUBSTITUTES = "--no-replace-objects"


def git(
    repository_root: Path,
    *arguments: str,
    text: bool = True,
    overrides: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Ask git a question about this repository, refusing local substitutions.

    Every question this CLI puts to git is a question about what a commit
    carries, and no call site here wants the replaced answer. So the refusal is
    injected once, in the function they all go through, rather than remembered
    at ten call sites where the eleventh forgets — which is how this defect
    reached a PASS in the first place.

    Returns the completed process rather than raising: each caller already
    distinguishes "git said no" from "git failed", and several of them treat a
    nonzero exit as a legitimate answer.

    ``overrides`` are variables the CALLER deliberately sets, applied on top of
    a GIT_*-free environment. This closes ambient GIT_* injection into Ranex's
    OWN queries; it does not close the repository-local .git/config vector, it
    does not sanitise the BOUND COMMAND's environment, and non-GIT_ variables
    git honours (including HOME and therefore ~/.gitconfig) are still inherited.
    System configuration also remains enabled by default for operator-facing
    repository queries. Subject/materialisation callers deliberately provide
    ``GIT_CONFIG_NOSYSTEM`` and ``GIT_ATTR_NOSYSTEM`` through ``overrides``.
    """

    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    if overrides is not None:
        environment.update(overrides)

    return subprocess.run(
        [
            str(resolve_tool("git")),
            "-C",
            str(repository_root),
            _NO_SUBSTITUTES,
            *arguments,
        ],
        capture_output=True,
        text=text,
        check=False,
        env=environment,
    )


def named_within_repository(repository_root: Path, candidate: str) -> Path:
    """What `candidate` *names*, with `.` and `..` collapsed and nothing followed.

    `resolve_within_repository` answers where a name leads. That is the right
    question for what to read and for containment, and the wrong one to put to
    git: a ref carries names, and following a symlink before asking replaces the
    name the operator typed with one the working tree chose. `gates.yaml`
    committed as a link to a file no commit carries resolves to the target, git
    is asked about the target, and the reviewed name is never consulted at all.

    Only the lexical parts are collapsed, so what comes back is the operator's
    own spelling. That is safe here because the caller compares the bytes this
    name carries against the bytes the resolved path holds: a component swapped
    for a symlink makes the two disagree, and disagreement is a refusal.
    """

    named = Path(os.path.normpath(candidate))
    if named.is_absolute() or named.parts[:1] == ("..",):
        raise ValueError(f"path resolves outside the repository: {candidate!r}")
    return repository_root / named


def nearest_existing_directory(path: Path) -> Path:
    """The closest ancestor of `path`, or `path` itself, that exists.

    Neither git nor `os.access` can answer a question about a path that does not
    exist yet. The directory that would hold it is what constrains it.
    """

    candidate = path
    while not candidate.is_dir() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def git_common_dir(directory: Path) -> Path | None:
    """The object store of the repository `directory` sits in, or None.

    Two checkouts of one repository have different toplevels and the same common
    dir. That is exactly what makes them one repository for the only question
    asked here: could a file written under this path be committed?
    """

    result = git(directory, "rev-parse", "--git-common-dir")
    if result.returncode != 0:
        return None
    # Relative when asked from inside the checkout, absolute when asked from a
    # linked worktree. Joining onto the directory it was asked from normalises
    # both; an absolute answer replaces the left side.
    return (directory / result.stdout.strip()).resolve()


def committable_into(target: Path, governed_root: Path) -> bool:
    """Would `target` land in the governed repository's history if committed?

    Containment under the root is the obvious half. The other half is a linked
    worktree: `git worktree add` produces a second checkout at an unrelated path
    that shares one object store, so a private key written there is `git add`-able
    and reachable from the main checkout while every containment check passes.
    Only git knows which checkouts those are, so ask it from the target's own
    directory.
    """

    if target == governed_root or governed_root in target.parents:
        return True
    common = git_common_dir(nearest_existing_directory(target))
    return common is not None and common == git_common_dir(governed_root)


def tracked_by_git(repository_root: Path, relative: str) -> bool:
    """Does git hold `relative` at all — in HEAD's tree, or in the index?

    HEAD alone was the wrong question. The dirty-tree exemption is withheld from
    a tracked file on the reasoning that tracked means reviewed, and a staged
    file is tracked while HEAD does not carry it: asking only about HEAD made
    `git add` enough to render any path exemptible, and staging is not review.

    `cat-file -e` is cheap and reads no content; `ls-files --error-unmatch`
    answers the same question of the index.
    """

    carried = git(repository_root, "cat-file", "-e", f"HEAD:{relative}")
    if carried.returncode == 0:
        return True
    # `:(literal)` so a name holding glob characters is matched as itself and
    # never as a pattern that happens to match something reviewed.
    staged = git(
        repository_root,
        "ls-files",
        "--cached",
        "--error-unmatch",
        "-z",
        "--",
        f":(literal){relative}",
    )
    return staged.returncode == 0


def uncommitted_paths(
    repository_root: Path,
    *,
    ignoring: Path | Sequence[Path] | None = None,
) -> tuple[str, ...]:
    """Paths where the working tree differs from HEAD.

    Untracked files count. They are absent from HEAD's tree yet present when a
    command runs, so a digest of HEAD would not describe what was observed.

    Asked against a scratch index read fresh from HEAD, never the repository's
    own. `git update-index --skip-worktree <file>` (and `--assume-unchanged`)
    tells git to stop stat-ing a file, and `git status` — `git diff HEAD` with
    it — then reports a clean tree while that file on disk differs from HEAD,
    permanently, with nothing to restore afterwards. A cleanliness check the
    observed party can switch off with one plumbing command is not a check.
    Those bits live in the index, so an index built from HEAD does not carry
    them and the question is answered by what is actually on disk.

    `ignoring` exempts Ranex's own bookkeeping — the evidence file `run` writes
    and the journal `gate evaluate` writes. Neither is ever produced by the
    observed command, so neither can have influenced the outcome; and without
    the exemption the second `run` in a repository would always refuse itself,
    and a `run` following an `evaluate` never succeed at all.

    That exemption applies ONLY to a path git does not track at all — neither
    in HEAD nor staged. Ranex's own output is gitignored and therefore in
    neither, so the exemption keeps doing its job; but applied to whatever
    `--evidence` named, it also excused an already-tracked file. Naming a
    committed, modified file then suppressed the refusal for it, and a tree HEAD
    does not describe was recorded as clean.

    `-uall`, because porcelain's default collapses a wholly-untracked directory
    into one `dir/` entry. An exemption naming a file can never match that, so
    Ranex's own output defeated its own exemption in the default layout: with
    `governance/` absent from HEAD, the first `run` creates
    `governance/evidence.json` and every later one refuses `governance/`.
    Listing untracked files individually is also the more informative refusal.
    """

    with tempfile.TemporaryDirectory() as scratch:
        # Outside the repository on purpose: an index file inside the working
        # tree would itself be untracked, and every call would report dirty.
        overrides = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
        read_tree = git(repository_root, "read-tree", "HEAD", overrides=overrides)
        if read_tree.returncode != 0:
            raise ValueError(
                f"cannot read HEAD into a scratch index: {read_tree.stderr.strip()}"
            )
        # --ignore-submodules=none overrides any submodule.<name>.ignore or
        # diff.ignoreSubmodules setting. Left to the repository's own config, a
        # changed submodule is invisible here while still being present when the
        # command runs — a dirty tree bound to a clean digest.
        result = git(
            repository_root,
            "status",
            "--porcelain",
            "-uall",
            "--ignore-submodules=none",
            overrides=overrides,
        )
    if result.returncode != 0:
        raise ValueError(f"cannot read repository status: {result.stderr.strip()}")

    if ignoring is None:
        exempted: tuple[Path, ...] = ()
    elif isinstance(ignoring, Path):
        exempted = (ignoring,)
    else:
        exempted = tuple(ignoring)

    # `ignoring` carries paths **as named**, never resolved, and this loop must
    # not resolve them either. Removing the flags stopped the observed party
    # naming the exempted path; it can still point it. A symlink at Ranex's own
    # constant name — and in the default layout `governance/` holds two
    # gitignored ones, so the link needs no commit and leaves no reviewable
    # artifact — re-aims the exemption at any untracked file in the tree. The
    # exemption then covers the file the bound command reads, and a tree HEAD
    # does not describe is recorded as clean. The name is what Ranex promised to
    # excuse; where that name leads is the observed party's choice, and a choice
    # it makes is not a thing to grant an exemption to.
    exempt: set[str] = set()
    for path in exempted:
        try:
            candidate = path.relative_to(repository_root).as_posix()
        except ValueError:
            continue
        # Tracked means reviewed: a difference from HEAD in such a file is the
        # dirty tree this check exists to see, whoever pointed --evidence at it.
        if not tracked_by_git(repository_root, candidate):
            exempt.add(candidate)

    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        payload = line[3:]
        # A rename reports "old -> new" and touches BOTH paths. Taking only the
        # destination let `git mv victim.txt <evidence>` report clean: the
        # destination was exempt, so the source's deletion vanished with it.
        candidates = payload.split(" -> ", 1) if " -> " in payload else [payload]
        for candidate in candidates:
            path = candidate.strip().strip('"')
            if path and path not in exempt:
                dirty.append(path)
    return tuple(sorted(dirty))


def tracked_paths(repository_root: Path) -> tuple[str, ...]:
    """Every path git holds in the index, NUL-separated so no name can lie."""

    result = git(repository_root, "ls-files", "-z")
    if result.returncode != 0:
        raise ValueError(f"cannot list the tracked files: {result.stderr.strip()}")
    return tuple(sorted(path for path in result.stdout.split("\0") if path))


def stat_fingerprint(
    repository_root: Path,
    paths: Sequence[str],
) -> dict[str, tuple[int, ...] | None]:
    """Filesystem identity and timestamps for each path, as they are right now.

    Content cannot answer "was this tree written while the command ran". A
    command that edits a tracked file, runs the check against the edit and puts
    the original bytes back leaves a tree byte-identical to HEAD: `git status`,
    `git diff HEAD` and any digest of the files all agree before and after, and
    the observation was still made against a tree that has existed in no commit.
    Comparing this before and after is what sees it happen.

    Inode, size and mtime all move when a file is rewritten. ctime moves too and
    is the one the writing process cannot set back, so restoring the timestamps
    does not restore this. `None` records a path that is not there — absent both
    times is no change, appearing or vanishing is.
    """

    fingerprint: dict[str, tuple[int, ...] | None] = {}
    for path in paths:
        try:
            info = (repository_root / path).lstat()
        except OSError:
            fingerprint[path] = None
            continue
        fingerprint[path] = (
            info.st_dev,
            info.st_ino,
            info.st_size,
            info.st_mtime_ns,
            info.st_ctime_ns,
        )
    return fingerprint


def governed_repository_root() -> Path:
    """Return the Git checkout containing this CLI, independent of caller cwd."""

    installation_path = Path(__file__).resolve()
    result = git(installation_path.parent, "rev-parse", "--show-toplevel")
    if result.returncode != 0:
        raise ValueError(
            "cannot locate the repository containing the Ranex CLI: "
            f"{result.stderr.strip()}"
        )
    return Path(result.stdout.strip()).resolve()
