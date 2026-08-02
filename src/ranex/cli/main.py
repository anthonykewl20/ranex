"""`ranex` — the operator entry point.

Two subcommands, and together they close the loop:

`run` observes a command and writes down what it saw. `gate evaluate` answers one
question — may this change land? — from those observations, and writes down why.

Neither reaches a model. Removing every credential on the machine changes no
verdict, and changes nothing `run` records.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.cli.confinement import resolve_within_repository
from ranex.foundation.canonical import canonical_sha256, command_digest
from ranex.foundation.signing import (
    generate_keypair,
    public_key_for,
    sign_evidence,
)
from ranex.governed_execution.api import (
    Evidence,
    Verdict,
)
from ranex.governed_execution.domain.admission import (
    Admission,
    Rejection,
    RejectionReason,
    admit,
)
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    KeyringError,
    load_keyring,
    load_keyring_text,
)

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

SIGNING_KEY_VARIABLE = "RANEX_SIGNING_KEY"

# The one path `gate evaluate` writes, and therefore the only path `run` may
# excuse from the dirty-tree check. It is a constant and not an option: a flag
# naming an arbitrary file hands the observed party an exemption from the check
# that binds its evidence to HEAD, which is the whole guarantee.
DEFAULT_JOURNAL = "governance/journal.sqlite3"

# The kernel spawns through this descriptor rather than through the name, so
# the file that runs is the file that was checked. O_PATH needs no read
# permission and never opens the file for content; O_NOFOLLOW plus the regular
# file check below refuses a final component that turned into a symlink between
# the resolution and the open.
EXECUTABLE_OPEN_FLAGS = os.O_NOFOLLOW | getattr(os, "O_PATH", os.O_RDONLY)

# Enough hops to resolve anything real, few enough to end a symlink cycle.
MAX_LINK_HOPS = 40


def subject_digest_for(repository_root: Path, ref: str) -> str:
    """The exact subject: the git tree of `ref`, not a mutable branch name."""

    result = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", f"{ref}^{{tree}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot resolve ref {ref!r}: {result.stderr.strip()}")
    return "sha256:" + canonical_sha256({"tree": result.stdout.strip()})


def head_commit(repository_root: Path) -> str:
    """The commit HEAD points at, used to detect the ground moving mid-run."""

    result = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot resolve HEAD: {result.stderr.strip()}")
    return result.stdout.strip()


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


def committed_bytes(repository_root: Path, ref: str, path: Path) -> bytes | None:
    """The bytes `ref` records for `path`, or None if `ref` has no such file."""

    relative = path.relative_to(repository_root).as_posix()
    result = subprocess.run(
        # `cat-file blob` and not `show`: it refuses anything that is not a
        # blob, so a directory or a tag never arrives here as file content.
        ["git", "-C", str(repository_root), "cat-file", "blob", f"{ref}:{relative}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def committed_trust_root(
    repository_root: Path,
    ref: str,
    candidate: str,
    resolved: Path,
    description: str,
) -> bytes:
    """The reviewed bytes of a trust-root file. Refuses if disk disagrees.

    **Returns the bytes, and those are what the caller must parse.** Handing
    back a path was the defect: the check compared one read of a name and the
    loaders then opened that same name again, so the bytes that were verified
    and the bytes that decided the verdict were two separate reads of a file
    the observed party can replace in between. Nothing here yields a path, so
    that second read has nowhere to happen.

    The on-disk comparison stays, and its job has changed. It no longer decides
    which bytes are used — it refuses a working tree that disagrees with the
    commit, so an operator who edits the catalog and forgets to commit is told
    rather than watching a verdict quietly ignore the edit. Losing that race
    now costs nothing: the committed bytes are what comes back either way.

    The keyring and the gate catalog are the trust root: one says which keys
    this repository trusts, the other says what the gate demands. Both are
    committed *so that review is the control on them*, and reading them from the
    working tree removes that control entirely. An unstaged line in the keyring
    registers a producer nobody reviewed; an unstaged edit to `required_claims`
    rewrites the target after the throw and the journal then preserves it as if
    it had been the policy all along.

    A path the ref does not carry used to be read from disk unchanged, on the
    reasoning that there was no reviewed version to prefer. That reasoning holds
    only for a path the *operator* chose, and the party being gated chooses it
    too: it writes `attacker-gates.yaml`, or drops a keyring under a committed
    `.gitignore` where `git status` will never mention it, and names it with a
    flag. Nothing was edited, so nothing was caught. The one input an attacker
    fully controls skipped the check outright, which made this the weakest link
    in a chain every other control hangs from. So absence blocks here as it
    blocks everywhere else: no committed file, no verdict.

    Two paths, because they answer different questions. `candidate` is what the
    operator named and is what git is asked about — a ref carries names.
    `resolved` is what will actually be read. Requiring them to agree byte for
    byte is what closes the committed-name-uncommitted-bytes case: a symlink at
    a reviewed name yields the link text from the ref and the target's contents
    from disk, and those are never equal.
    """

    named = named_within_repository(repository_root, candidate)
    relative = named.relative_to(repository_root).as_posix()
    committed = committed_bytes(repository_root, ref, named)
    if committed is None:
        raise ValueError(
            f"refusing to evaluate: {ref} carries no {description} at "
            f"{relative}, and it decides this verdict. A file no commit carries "
            "is a file review never saw — commit it, or name the one that is "
            "committed"
        )
    try:
        on_disk = resolved.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read the {description} at {resolved}: {exc}") from exc
    if on_disk != committed:
        through = "" if resolved == named else f" (reached through {resolved})"
        raise ValueError(
            f"refusing to evaluate: the {description} at {relative}{through} "
            f"differs from the version committed in {ref}, and it decides this "
            "verdict. Commit the change so review sees it, or revert it"
        )
    return committed


def load_records(path: Path) -> list[object]:
    """Read the raw evidence array. A missing file is no evidence, not an error.

    A malformed file is an error, never silently no evidence. `{}` used to
    iterate zero keys and return nothing at all, which is indistinguishable
    from an honest absence and therefore the more dangerous of the two.

    Records are returned raw. Deciding which of them are evidence is admission's
    job, and it needs the signature this function deliberately does not strip.
    """

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        # The only OSError that means absence. `Path.exists()` also answers
        # False for EACCES, ENOTDIR and ELOOP, which reports a machine that
        # cannot read its own records as work never done — and chmod is a great
        # deal easier than forging a signature. Every other OSError propagates.
        return []
    except json.JSONDecodeError as exc:
        # A truncated file is corruption, not absence. Saying "no evidence"
        # here would report an interrupted write as work never done.
        raise ValueError(
            f"evidence file at {path} is corrupt and cannot be parsed: {exc}"
        ) from exc
    if not isinstance(raw, list):
        raise ValueError("evidence file must contain a JSON array")
    return list(raw)


def admitted_evidence(
    path: Path,
    keyring_path: Path,
    repository_root: Path | None = None,
) -> Admission:
    """Raw records plus the keyring, in; evidence plus rejections, out.

    `repository_root`, when given, also re-checks the containment rule `run`
    applied to `argv[0]`. Omitting it verifies signatures only, which is what a
    caller asking "did this record verify" wants.
    """

    return admit_records(path, load_keyring(keyring_path), repository_root)


def admit_records(
    path: Path,
    keyring: Mapping[str, str],
    repository_root: Path | None = None,
) -> Admission:
    """The same, from a keyring already in hand rather than a path to one.

    This is what the CLI calls. The keyring it passes came out of the commit,
    and re-deriving it from a path here would reopen the trust root by name
    after it was checked — the whole hole `committed_trust_root` exists to close.
    """

    records = load_records(path)
    admission = admit(records, keyring)
    if repository_root is None:
        return admission
    return refuse_executables_inside(admission, len(records), repository_root)


def refuse_executables_inside(
    admission: Admission,
    record_count: int,
    repository_root: Path,
) -> Admission:
    """Refuse records whose executable lives in the tree they describe.

    `run` will not execute an `argv[0]` that resolves inside the subject
    worktree, because a worker that can drop `./pytest` in the repository it is
    judged on chooses what the claim means. That refusal binds only whoever ran
    `run`: a keyholder can write the record by hand and never invoke it. So
    `executable_path` is a signed field and the decision is taken again here,
    from the record — a field nothing re-checks would be decoration, which is
    what in-toto's advisory-only `expected_command` amounts to.

    Refused rather than quietly dropped. The record exists and is signed, so
    reporting it as absence would file an attack under work never done.

    `admit` produces exactly one outcome per record, so the admitted evidence
    lines up in order with the record positions no rejection claimed. That is
    what lets a rejection raised here still name the record a human must open.
    """

    already_refused = {rejection.index for rejection in admission.rejections}
    positions = [i for i in range(record_count) if i not in already_refused]

    kept: list[Evidence] = []
    added: list[Rejection] = []
    for index, item in zip(positions, admission.evidence, strict=True):
        executable = Path(item.executable_path)
        if not executable.is_absolute():
            detail = (
                f"executable_path {item.executable_path!r} is not absolute, so "
                "where the command actually came from cannot be decided"
            )
        elif committable_into(executable, repository_root):
            detail = (
                f"executable_path {item.executable_path} is inside the repository "
                "under observation, so the party being judged chose the binary "
                "that satisfied the claim"
            )
        else:
            kept.append(item)
            continue
        added.append(
            Rejection(
                index=index,
                reason=RejectionReason.EXECUTABLE_INSIDE_SUBJECT,
                detail=detail,
                producer_id=item.producer_id,
                claim_id=item.claim_id,
            )
        )

    return Admission(
        evidence=tuple(kept),
        rejections=tuple(
            sorted(admission.rejections + tuple(added), key=lambda r: r.index)
        ),
    )


@dataclass(frozen=True, slots=True)
class Resolution:
    """Where `argv[0]` leads, and every path walked to get there.

    Both halves are needed to answer one question: did the tree under
    observation choose which bytes run? The destination answers it for a binary
    the tree supplies; the route answers it for a binary the tree *points at*.
    """

    executable: Path
    route: tuple[Path, ...]


def walked_route(named: Path) -> tuple[Path, ...]:
    """Every path traversed while resolving `named`, in the order walked.

    `Path.resolve()` says where a name ends up and throws away how it got
    there, and the route is half the question. A symlink committed inside the
    subject worktree pointing at a binary outside it has an honestly-outside
    destination, and the observed tree still chose which bytes run: moving the
    link changes what the claim means and touches nothing a check on the target
    can see.

    Symlinks are expanded the way the kernel expands them — the target's
    components pushed back onto what is left to walk, `..` applied to the
    already-resolved position — so what comes back is what was walked.
    """

    route: list[Path] = []
    current = Path(named.anchor or "/")
    remaining = list(named.parts[1:] if named.anchor else named.parts)
    hops = 0
    while remaining:
        component = remaining.pop(0)
        if component == ".":
            continue
        if component == "..":
            current = current.parent
            route.append(current)
            continue
        current = current / component
        route.append(current)
        if not current.is_symlink():
            continue
        hops += 1
        if hops > MAX_LINK_HOPS:
            raise ValueError(
                f"refusing to resolve {named}: too many symbolic links to follow"
            )
        target = Path(os.readlink(current))
        if target.is_absolute():
            remaining = list(target.parts[1:]) + remaining
            current = Path(target.anchor)
        else:
            remaining = list(target.parts) + remaining
            current = current.parent
    return tuple(route)


def resolve_executable(argv0: str, working_directory: Path) -> Resolution:
    """Where `argv[0]` actually leads: absolute, symlinks followed, once.

    PATH is ambient state the observed party can edit, and the in-toto spec
    concedes that is what defeats a declared command (§4.3.1). So PATH decides
    only where to *look*; the answer is resolved through every link and then
    judged, and the resolved path is what gets executed and recorded. Resolving
    twice — once to check, once to run — would be the gap the check exists to
    close.

    Raises rather than returning None: a command that never ran must not be
    reported as a command with an exit code.
    """

    if "/" in argv0:
        # A path, relative to where the command will run rather than to whatever
        # directory the operator happened to invoke Ranex from.
        named: Path | None = Path(working_directory) / argv0
    else:
        found = shutil.which(argv0)
        # `which` may answer with a relative name when PATH holds one; the
        # command runs in the repository root, so that is what it is relative to.
        named = Path(working_directory) / found if found is not None else None

    candidate: Path | None = None
    if named is not None:
        candidate = named.resolve()
        if not (candidate.is_file() and os.access(candidate, os.X_OK)):
            candidate = None

    if named is None or candidate is None:
        raise ValueError(
            f"cannot resolve {argv0!r} to an executable; refusing to record an "
            "observation of a command that never ran"
        )
    return Resolution(executable=candidate, route=walked_route(named))


def route_inside(resolution: Resolution, governed_root: Path) -> Path | None:
    """The first step of the route that lies inside the worktree, if any.

    The root itself is not a step inside it: every path under the repository is
    reached through the root, and refusing that would refuse the repository for
    existing. What must not appear is a component *below* it — a directory or a
    link the observed tree carries and can edit.
    """

    for step in resolution.route:
        if governed_root in step.parents:
            return step
    return None


def same_file_inside(identity: os.stat_result, governed_root: Path) -> Path | None:
    """A second name inside the worktree for the exact file `identity` names.

    A hard link is not a copy and not a link that can be followed: it is another
    directory entry for one inode. Containment compares paths, and an inode has
    many, so `ln <repo>/tools/pytest /tmp/bin/pytest` is outside by every path
    test while the bytes that run are the ones the observed tree carries.
    Identity is `(st_dev, st_ino)`, and nothing cheaper stands in for it.

    Two cheaper questions were asked here and both were wrong, for one reason.
    `st_nlink <= 1` read as "one name, so there is no second one to find" —
    `mount --bind <repo>/tools/pytest /tmp/bin/pytest` gives one inode a second
    name and never touches the link count, so the fast path answered "no second
    name" about a file that had exactly one. Comparing the root's `st_dev` first
    fails the same way: a mount inside the worktree puts an in-repo path on
    another device, and the pre-filter then skips the search that would have
    found it. Both assumed the observed party cannot manipulate the filesystem,
    and unprivileged user namespaces are the standing proof that it can. An
    optimisation that is only sound against an attacker who is not trying is not
    an optimisation.

    So the search is unconditional, and paid for by reading the inode straight
    out of the directory entry: on Linux `scandir` returns it from `readdir`
    with no `stat` syscall, so a full pass costs one syscall per directory
    rather than one per file. Measured on this repository — 3227 entries, a
    666 MB `.git` included — a miss, which is the common case and the worst
    case, takes about 5 ms against 23 ms for the `os.walk`-and-`lstat` shape it
    replaces. `run` wraps a test suite; this is noise beside it, and the cost
    grows with the number of entries rather than with their size.

    Only a matching inode number is worth a `stat`, and that stat is what
    settles the device — two files on two filesystems can share an inode number
    and are not the same file. Symlinked directories are not descended, so the
    pass terminates without needing a hop count.
    """

    stack = [governed_root]
    while stack:
        directory = stack.pop()
        try:
            entries = os.scandir(directory)
        except OSError as exc:
            # A directory that cannot be read is not a directory with nothing
            # in it. The observed party owns this tree and shares the uid, so
            # one `chmod 000` closes a directory; git records the executable
            # bit on files and nothing at all about directory modes, so the
            # tree still reads as clean and the dirty check never fires. The
            # pass would then walk past the one name that matches and report
            # that it found none.
            #
            # So ignorance refuses, exactly as `path_behind` refuses when
            # /proc/self/fd is missing. This function's contract is "no second
            # name inside the worktree", and a scan that was not permitted to
            # look has established nothing of the kind.
            raise ValueError(
                f"refusing to run: {directory}, inside the repository under "
                f"observation, cannot be read ({exc}), so whether this command "
                "is a second name for a file in the observed tree cannot be "
                "decided. A question that could not be asked is not a question "
                "answered no"
            ) from exc
        with entries:
            for entry in entries:
                try:
                    directory_entry = entry.is_dir(follow_symlinks=False)
                except OSError as exc:
                    raise ValueError(
                        f"refusing to run: {entry.path}, inside the repository "
                        f"under observation, cannot be classified ({exc}), so "
                        "the identity of the command cannot be decided"
                    ) from exc
                if directory_entry:
                    stack.append(Path(entry.path))
                    continue
                # Free: `scandir` carries the inode number out of `readdir`.
                if entry.inode() != identity.st_ino:
                    continue
                try:
                    found = entry.stat(follow_symlinks=False)
                except OSError:
                    # The inode number already matches. Without the device that
                    # match cannot be confirmed — and an unconfirmable match is
                    # not a licence to run, so it is treated as the twin it
                    # most likely is.
                    return Path(entry.path)
                if (found.st_dev, found.st_ino) == (identity.st_dev, identity.st_ino):
                    return Path(entry.path)
    return None


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

    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
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


def path_behind(descriptor: int, refusal: str) -> Path:
    """Where an already-open descriptor actually leads.

    Containment judged against a *name* is only true for as long as nobody
    edits the path. An open descriptor cannot be re-pointed, so this is the one
    form of the question whose answer survives until the file is used.
    `/proc/self/fd` is how the kernel is asked; if it is not there, refuse
    rather than guess — neither a key we cannot prove landed outside the tree
    nor a binary we cannot prove came from outside it may be acted on.
    """

    try:
        return Path(os.readlink(f"/proc/self/fd/{descriptor}")).resolve()
    except OSError as exc:
        raise ValueError(f"{refusal} (/proc/self/fd is unavailable: {exc})") from exc


def directory_behind(descriptor: int) -> Path:
    """Where an already-open directory actually leads."""

    return path_behind(
        descriptor,
        "cannot confirm which directory this key would be written into, so it "
        "will not be created",
    )


def private_signing_key(governed_root: Path) -> str:
    """Read the producer's private key from the environment.

    Refuses a key any other account can read. `keygen` writes 0600, but a key
    copied between machines usually arrives with whatever mode the copy gave it,
    and a world-readable signing key makes the whole slice decorative.

    Refuses a key inside the repository for the same reason `keygen` refuses to
    create one there. A refusal only at the point of creation is advisory: the
    key can be placed by hand, and a `.gitignore` entry keeps `git status` clean
    so nothing else notices it is one `git add -f` from being published.
    """

    raw_path = os.environ.get(SIGNING_KEY_VARIABLE)
    if not raw_path:
        raise ValueError(
            f"{SIGNING_KEY_VARIABLE} is not set, so nothing can sign this "
            "record; refusing to write unsigned evidence"
        )
    # Resolved before it is judged: the check must be about the file that will
    # actually be read, not about the name it was reached by.
    key_path = Path(raw_path).resolve()
    if not key_path.is_file():
        raise ValueError(f"{SIGNING_KEY_VARIABLE} points at no file: {key_path}")

    if committable_into(key_path, governed_root):
        raise ValueError(
            f"refusing to sign with the private key at {key_path}: it is inside "
            "the repository under governance and therefore committable. Keys "
            "live outside the tree"
        )

    mode = stat.S_IMODE(key_path.stat().st_mode)
    if mode & 0o077:
        raise ValueError(
            f"private key {key_path} is mode {oct(mode)}; it must not be "
            "readable by group or other. chmod 600 it"
        )
    return key_path.read_text(encoding="utf-8").strip()


def tracked_by_git(repository_root: Path, relative: str) -> bool:
    """Does git hold `relative` at all — in HEAD's tree, or in the index?

    HEAD alone was the wrong question. The dirty-tree exemption is withheld from
    a tracked file on the reasoning that tracked means reviewed, and a staged
    file is tracked while HEAD does not carry it: asking only about HEAD made
    `git add` enough to render any path exemptible, and staging is not review.

    `cat-file -e` is cheap and reads no content; `ls-files --error-unmatch`
    answers the same question of the index.
    """

    carried = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "-e", f"HEAD:{relative}"],
        capture_output=True,
        check=False,
    )
    if carried.returncode == 0:
        return True
    staged = subprocess.run(
        # `:(literal)` so a name holding glob characters is matched as itself
        # and never as a pattern that happens to match something reviewed.
        [
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "--cached",
            "--error-unmatch",
            "-z",
            "--",
            f":(literal){relative}",
        ],
        capture_output=True,
        check=False,
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
        environment = os.environ | {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
        read_tree = subprocess.run(
            ["git", "-C", str(repository_root), "read-tree", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        if read_tree.returncode != 0:
            raise ValueError(
                f"cannot read HEAD into a scratch index: {read_tree.stderr.strip()}"
            )
        result = subprocess.run(
            # --ignore-submodules=none overrides any submodule.<name>.ignore or
            # diff.ignoreSubmodules setting. Left to the repository's own config,
            # a changed submodule is invisible here while still being present
            # when the command runs — a dirty tree bound to a clean digest.
            [
                "git",
                "-C",
                str(repository_root),
                "status",
                "--porcelain",
                "-uall",
                "--ignore-submodules=none",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
    if result.returncode != 0:
        raise ValueError(f"cannot read repository status: {result.stderr.strip()}")

    if ignoring is None:
        exempted: tuple[Path, ...] = ()
    elif isinstance(ignoring, Path):
        exempted = (ignoring,)
    else:
        exempted = tuple(ignoring)

    exempt: set[str] = set()
    for path in exempted:
        try:
            candidate = path.resolve().relative_to(repository_root).as_posix()
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

    result = subprocess.run(
        ["git", "-C", str(repository_root), "ls-files", "-z"],
        capture_output=True,
        text=True,
        check=False,
    )
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


def refuse_unwritable_evidence(path: Path) -> None:
    """Refuse now if the record could not be written afterwards.

    Probes without creating anything: an existing file must be writable, and an
    absent one needs a directory that accepts it, since `record_evidence` creates
    the missing parents itself.
    """

    if path.exists():
        if not os.access(path, os.W_OK):
            raise ValueError(f"evidence file at {path} cannot be written to")
        return
    directory = nearest_existing_directory(path.parent)
    if not os.access(directory, os.W_OK | os.X_OK):
        raise ValueError(
            f"cannot create the evidence file at {path}: {directory} is not writable"
        )


def record_evidence(path: Path, record: dict[str, object]) -> None:
    """Write one record, replacing any earlier one for the same claim+producer.

    Replacing rather than appending keeps one producer's latest observation of a
    claim authoritative. Records from other claims or other producers are left
    untouched — this file is shared.
    """

    kept: list[dict[str, object]] = []
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            raise ValueError("evidence file must contain a JSON array")
        kept = [
            item
            for item in existing
            if not (
                isinstance(item, dict)
                and item.get("claim_id") == record["claim_id"]
                and item.get("producer_id") == record["producer_id"]
            )
        ]

    kept.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(kept, indent=2) + "\n", encoding="utf-8")


def governed_repository_root() -> Path:
    """Return the Git checkout containing this CLI, independent of caller cwd."""

    installation_path = Path(__file__).resolve()
    result = subprocess.run(
        ["git", "-C", str(installation_path.parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            "cannot locate the repository containing the Ranex CLI: "
            f"{result.stderr.strip()}"
        )
    return Path(result.stdout.strip()).resolve()


def cmd_gate_evaluate(args: argparse.Namespace) -> int:
    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        gate_catalog = resolve_within_repository(root, args.gate_catalog)
        evidence_path = resolve_within_repository(root, args.evidence)
        keyring_path = resolve_within_repository(root, args.producers)
        journal_path = (
            resolve_within_repository(root, args.journal) if args.journal else None
        )
        subject = subject_digest_for(root, args.ref)
        # Before either is read, and against the ref being judged rather than
        # against whatever is checked out: these two files choose the verdict,
        # so the copy that decides it must be the copy review saw.
        # The reviewed bytes themselves, never a path to fetch them from again.
        # Everything below parses what comes back here, so between the check and
        # the verdict there is no second read for anyone to get in front of.
        keyring_source = committed_trust_root(
            root, args.ref, args.producers, keyring_path, "producer keyring"
        )
        catalog_source = committed_trust_root(
            root, args.ref, args.gate_catalog, gate_catalog, "gate catalog"
        )
        keyring = load_keyring_text(keyring_source.decode("utf-8"), keyring_path)
        # The root is passed so the containment decision `run` made about
        # argv[0] is taken again here, from the signed path in the record.
        admission = admit_records(evidence_path, keyring, root)
        evaluator = build_gate_evaluator(
            catalog_source,
            journal_path,
        )
        result = evaluator.evaluate(
            args.gate,
            admission.evidence,
            subject_digest=subject,
            approver_id=args.approver,
        )
    except (
        KeyringError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    if result.verdict is Verdict.PASS:
        print(f"PASS  gate={result.gate_id}  subject={result.subject_digest}")
    else:
        print(f"FAIL  gate={result.gate_id}  rule={result.failing_rule}")

    # Reported whatever the verdict. A forgery the gate happened to pass without
    # is still a forgery, and returning early on PASS made a probe that leaves no
    # trace — which is a probe worth repeating.
    for rejection in admission.rejections:
        print(
            f"      REFUSED record {rejection.index} "
            f"[{rejection.reason}] {rejection.detail}"
        )

    if result.verdict is Verdict.PASS:
        return EXIT_PASS

    # Three different events arrive as `missing_claims`, and the operator must
    # not have to guess which one happened: a record was refused (an attack), a
    # record describes another tree (a replay), or the work was never done. The
    # kernel names them in one sentence because it judges claims, not causes;
    # partitioning per claim here is what keeps a forgery from being printed
    # under the phrasing reserved for honest absence.

    # A rejection carries the claim it names, and `claim_id` is read off the
    # record with `_text_or_none` — so changing that one field to a non-string
    # produces a rejection naming no claim at all. None intersects no required
    # claim, so the claim used to fall through into `absent` and print under the
    # kernel's phrasing for honest absence: the attacker chose the wording of
    # the report by choosing which field to tamper with. Counted separately, and
    # the absence sentence is withheld while any of them exist.
    unattributable = sum(1 for r in admission.rejections if r.claim_id is None)
    explained = {r.claim_id for r in admission.rejections if r.claim_id is not None}
    missing = set(result.missing_claims)
    # A claim some admitted record names is not work never done, whatever else
    # is wrong with that record: it may describe another tree, another command,
    # or a run that failed. Each of those is an event an operator must be able
    # to tell from silence, and the kernel already names which one it was — so
    # the absence sentence is spent only on claims nothing was recorded for, and
    # the kernel's diagnosis is printed for the rest. A digest mismatch reported
    # as absence is the reporting defect SLICE-002 was reopened to fix, one
    # field further along.
    observed = {item.claim_id for item in admission.evidence if item.claim_id in missing}
    refused = sorted(missing & explained)
    absent = sorted(missing - explained - observed)

    if refused:
        print(
            f"      {len(admission.rejections)} record(s) were refused above; "
            f"no verifying evidence remains for: {', '.join(refused)}"
        )
    if absent and unattributable:
        print(
            f"      {unattributable} record(s) above were refused without a usable "
            "claim_id, so these required claims cannot be called work never "
            f"done: {', '.join(absent)}"
        )
    elif absent:
        print(f"      no evidence for required claim: {', '.join(absent)}")
    if result.reason and (observed or not missing):
        # The kernel's own diagnosis, kept whenever it says something the
        # partition cannot: which of the four ways a record failed to satisfy
        # the claim it names, a contradiction between two records, or a
        # self-approval refusal that names no claim at all. Withheld when every
        # missing claim is genuinely absent, because then it would only repeat
        # the sentence printed above — possibly for claims that were refused.
        print(f"      {result.reason}")

    print(f"      subject={result.subject_digest}")
    return EXIT_FAIL


def cmd_run(args: argparse.Namespace) -> int:
    """Run a command and record what was observed. Never judge it.

    Exits with the wrapped command's own exit code so `run && gate evaluate`
    composes. A failing command is honest evidence of failure, not a usage
    error — only refusals to record are, and those exit 2 having written
    nothing.
    """

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]

    descriptor: int | None = None
    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        evidence_path = resolve_within_repository(root, args.evidence)
        keyring_path = resolve_within_repository(root, args.producers)
        # `run` never writes the journal, and never takes its path from the
        # caller. It is named here for one reason: a preceding `gate evaluate`
        # leaves it in the tree, and without knowing which path is its own
        # bookkeeping `run` reports Ranex's output as a dirty tree and refuses
        # every run after the first evaluation. A flag would turn that one
        # exemption into an exemption for any file the observed party names.
        journal_path = resolve_within_repository(root, DEFAULT_JOURNAL)
        if not command:
            raise ValueError("a command is required after --")

        # Resolved once, here, and used for the containment decision, for the
        # execution below and for the record. `argv[0]` landing inside the tree
        # under observation is the worker choosing what the claim means by
        # writing a file into the tree its own evidence describes — the bullseye
        # painted around the dart, one layer down. Symlinks are followed first,
        # so a link outside the tree pointing back into it gets the same answer.
        resolution = resolve_executable(command[0], root)
        executable = resolution.executable
        # The destination is only half of "did the observed tree choose these
        # bytes". A link committed inside the worktree points at a binary
        # outside it, so the target clears containment while the tree still
        # decides what runs — and re-pointing the link changes what the claim
        # means without touching anything the target check can see.
        step = route_inside(resolution, root)
        if step is not None:
            raise ValueError(
                f"refusing to run {command[0]!r}: it resolves to {executable} "
                f"by way of {step}, inside the repository under observation. A "
                "route the observed tree carries chooses the binary as surely "
                "as supplying it does"
            )
        if committable_into(executable, root):
            raise ValueError(
                f"refusing to run {command[0]!r}: it resolves to {executable}, "
                "inside the repository under observation. A binary the observed "
                "tree supplies cannot be what proves that tree"
            )

        # Opened once, now, and executed through this descriptor below. A name
        # is re-walked at exec time and every directory on it traversed a second
        # time, so swapping an ancestor between the decision and the spawn runs
        # a file that was never checked while the record names the one that was.
        # A descriptor cannot be re-pointed: the file that runs is this file.
        descriptor = os.open(executable, EXECUTABLE_OPEN_FLAGS)
        identity = os.fstat(descriptor)
        if not stat.S_ISREG(identity.st_mode):
            raise ValueError(
                f"refusing to run {command[0]!r}: {executable} is not a regular "
                "file, so what would execute is not what was resolved"
            )
        opened = path_behind(
            descriptor,
            f"cannot confirm which file {command[0]!r} opened, so it will not "
            "be run",
        )
        if opened != executable:
            raise ValueError(
                f"refusing to run {command[0]!r}: it resolved to {executable} "
                f"and the file actually opened is {opened}; the path changed "
                "while it was being checked"
            )
        twin = same_file_inside(identity, root)
        if twin is not None:
            raise ValueError(
                f"refusing to run {command[0]!r}: {executable} is the same file "
                f"as {twin}, inside the repository under observation. A hard "
                "link and a bind mount are both a second name for one file, not "
                "a second file, so the bytes that would run are the ones the "
                "observed tree carries"
            )

        # Everything that can refuse, refuses before the command runs. A test
        # suite is expensive; discovering afterwards that the record cannot be
        # written honestly wastes all of it.
        private_key = private_signing_key(governed_root)
        # The same trust root, and the same refusal, on the way in. `run` only
        # consults the keyring to avoid writing a record that evaluation would
        # refuse — but a keyring the caller supplies at an uncommitted path
        # turns that courtesy into a way to self-register, and a gitignored one
        # is invisible to the dirty-tree check below as well as to `git status`.
        keyring_source = committed_trust_root(
            root, "HEAD", args.producers, keyring_path, "producer keyring"
        )
        keyring = load_keyring_text(keyring_source.decode("utf-8"), keyring_path)
        registered = keyring.get(args.producer)
        if registered is None:
            raise ValueError(
                f"producer {args.producer!r} is not in {keyring_path.name}; "
                "register its public key before recording evidence"
            )
        if public_key_for(private_key) != registered:
            raise ValueError(
                f"the key in {SIGNING_KEY_VARIABLE} is not the key registered "
                f"for producer {args.producer!r}; the record would be written "
                "and then refused at evaluation"
            )

        # Whether the record can be written is knowable now. Left to
        # `record_evidence`, a corrupt or unwritable evidence file is discovered
        # only once the command has run, changed the tree, and left no record of
        # having done so.
        load_records(evidence_path)
        refuse_unwritable_evidence(evidence_path)

        # Refuse before running, not after: a claim we cannot honestly bind to a
        # subject should cost nothing to discover.
        dirty = uncommitted_paths(root, ignoring=(evidence_path, journal_path))
        if dirty:
            raise ValueError(
                "refusing to record evidence against a dirty working tree; "
                f"HEAD does not describe: {', '.join(dirty)}"
            )
        # HEAD, always, and deliberately not selectable. The command runs against
        # the checked-out tree, so naming any other ref would record a digest for
        # a tree that was never observed — a false claim reachable straight from
        # the documented interface.
        subject = subject_digest_for(root, "HEAD")
        started_at = head_commit(root)
        # Taken last, immediately before the command: everything above may run
        # git, and this has to describe the tree as the command finds it.
        observed = tracked_paths(root)
        untouched = stat_fingerprint(root, observed)
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        if descriptor is not None:
            os.close(descriptor)
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    try:
        # The observed command is the agent's work, untrusted by definition.
        # Inheriting $RANEX_SIGNING_KEY hands it the producer's private key, and
        # a key the subject of the observation can read lets it sign whatever
        # record it likes — signatures would then prove only that something ran
        # on this machine. The key was read before this point; the child has no
        # use for the variable.
        environment = {
            name: value
            for name, value in os.environ.items()
            if name != SIGNING_KEY_VARIABLE
        }
        # The descriptor, not the name: executing either the name or the
        # resolved path re-walks every directory on it, and an ancestor swapped
        # since the check would deliver a different file to the exec than the
        # one that was cleared. `argv[0]` stays the resolved path so the child
        # still sees the name it was invoked under.
        completed = subprocess.run(
            [str(executable), *command[1:]],
            executable=f"/proc/self/fd/{descriptor}",
            pass_fds=(descriptor,),
            cwd=root,
            check=False,
            env=environment,
        )
    except OSError as exc:
        print(f"ERROR  cannot run {command[0]!r}: {exc}", file=sys.stderr)
        return EXIT_USAGE
    finally:
        os.close(descriptor)

    try:
        # Removing --ref shut one door; the command could still walk through
        # another by checking out elsewhere, leaving the recorded digest
        # describing a tree it never ran against. Creating files is legitimate
        # and must still pass — moving HEAD never is.
        if head_commit(root) != started_at:
            raise ValueError(
                "refusing to record evidence: the command moved HEAD from "
                f"{started_at[:12]} during the run, so {subject[:19]}… "
                "does not describe what was observed"
            )
        # Clean before and clean after is not the same as clean throughout. A
        # command that paints the bullseye, throws, and wipes the paint off —
        # write the answer the check wants, run it, restore the committed bytes,
        # exit with the check's status — leaves HEAD untouched and every content
        # comparison satisfied. The tree it was scored against existed only
        # while nobody was looking, so the digest names a tree whose own check
        # still fails. Creating files remains legitimate: only paths git already
        # tracked are watched, and only for having been written.
        written = sorted(
            path
            for path, fingerprint in stat_fingerprint(root, observed).items()
            if fingerprint != untouched[path]
        )
        if written:
            raise ValueError(
                "refusing to record evidence: the command wrote to tracked "
                f"file(s) while it ran — {', '.join(written)} — so {subject[:19]}… "
                "does not describe the tree that was observed, whatever the tree "
                "on disk looks like now"
            )
        content = {
            "claim_id": args.claim,
            "subject_digest": subject,
            "producer_id": args.producer,
            # Both stay: the digest is what the gate compares, the string is what
            # review reads. Signing only one would leave the other free to lie.
            "command": shlex.join(command),
            "command_digest": command_digest(command),
            "executable_path": str(executable),
            "exit_code": int(completed.returncode),
        }
        record_evidence(
            evidence_path,
            {**content, "signature": sign_evidence(content, private_key)},
        )
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(
        f"RECORDED  claim={args.claim}  producer={args.producer}  "
        f"exit={completed.returncode}"
    )
    print(f"          subject={subject}")
    return int(completed.returncode)


def cmd_keygen(args: argparse.Namespace) -> int:
    """Generate a producer's signing key, outside the repository.

    The confinement here is the inverse of `resolve_within_repository`: that
    refuses paths outside the repository, this refuses paths inside it. The
    slice's premise is that private keys never enter the tree, and an
    environment variable pointing inward must be refused rather than obeyed —
    otherwise the key ends up committed and every other guarantee is theatre.
    """

    try:
        governed_root = governed_repository_root()

        raw_path = os.environ.get(SIGNING_KEY_VARIABLE)
        if not raw_path:
            raise ValueError(
                f"{SIGNING_KEY_VARIABLE} is not set; point it at the file the "
                "private key should live in, outside this repository"
            )

        target = Path(raw_path)
        if not target.is_absolute():
            # A relative path resolves against whatever the current directory
            # happens to be, which is very often the repository itself.
            raise ValueError(
                f"{SIGNING_KEY_VARIABLE} must be an absolute path, got {raw_path!r}"
            )
        target = target.resolve()

        if committable_into(target, governed_root):
            raise ValueError(
                f"refusing to write a private key inside the repository: {target}. "
                "Private keys must never be committable"
            )
        if target.is_dir():
            raise ValueError(f"{SIGNING_KEY_VARIABLE} is a directory: {target}")
        if target.exists():
            # Replacing a key silently orphans every record it ever signed.
            raise ValueError(
                f"refusing to overwrite the existing key at {target}; "
                "remove it deliberately if you mean to replace it"
            )

        private_key, public_key = generate_keypair()
        target.parent.mkdir(parents=True, exist_ok=True)

        # The check above judged a path; the write below traverses a directory,
        # and O_EXCL guards only the last component. Anything that swaps a
        # parent for a symlink into the repository in between gets the key
        # planted in the tree while the refusal — and the path printed after —
        # still describe the directory that no longer receives it. So: take the
        # directory once, decide containment against THAT, and create the file
        # inside it. O_NOFOLLOW refuses a parent that has become a symlink;
        # O_DIRECTORY refuses one that is no longer a directory at all.
        parent = os.open(
            target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        try:
            target = directory_behind(parent) / target.name
            if committable_into(target, governed_root):
                raise ValueError(
                    "refusing to write a private key inside the repository: "
                    f"{target}. Private keys must never be committable"
                )
            # dir_fd, not the path: re-walking the path is the whole race.
            # Created 0600, not chmod'ed to 0600 afterwards: between creation
            # and chmod the key would briefly be world-readable.
            handle = os.open(
                target.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=parent,
            )
        finally:
            os.close(parent)
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(private_key + "\n")
    except (ValueError, OSError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(f"WROTE  {target}  mode 0600")
    print("       register the producer by adding this line to the keyring:")
    print(f"  {args.producer}: {public_key}")
    return EXIT_PASS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranex",
        description="Deterministic governance for AI agents that build software",
    )
    sub = parser.add_subparsers(dest="group", required=True)
    gate = sub.add_parser("gate", help="gate operations").add_subparsers(
        dest="action", required=True
    )
    ev = gate.add_parser("evaluate", help="evaluate a change against a gate")
    ev.add_argument("ref", help="git ref to evaluate")
    ev.add_argument("--repository", default=".", help="repository root")
    ev.add_argument("--gate", default="landing", help="gate id")
    ev.add_argument(
        "--gate-catalog",
        default="governance/gates.yaml",
        help="gate catalog path",
    )
    ev.add_argument(
        "--evidence",
        default="governance/evidence.json",
        help="evidence records path",
    )
    ev.add_argument(
        "--producers",
        default="governance/producers.yaml",
        help="committed keyring of producer public keys",
    )
    ev.add_argument("--approver", required=True, help="identity approving")
    ev.add_argument("--journal", default=DEFAULT_JOURNAL, help="journal path")
    ev.set_defaults(func=cmd_gate_evaluate)

    rn = sub.add_parser("run", help="run a command and record evidence of it")
    rn.add_argument("--claim", required=True, help="claim this evidences")
    rn.add_argument("--producer", required=True, help="identity running the command")
    rn.add_argument("--repository", default=".", help="repository root")
    # No --ref. The subject is always HEAD, because HEAD is what the command
    # runs against. Offering a choice offers a way to record a false claim.
    rn.add_argument(
        "--evidence",
        default="governance/evidence.json",
        help="evidence records path",
    )
    rn.add_argument(
        "--producers",
        default="governance/producers.yaml",
        help="committed keyring of producer public keys",
    )
    # No --journal. `run` never writes the journal, and the only thing naming it
    # bought was an exemption from the dirty-tree check — offered to whatever
    # path the caller chose, which is an exemption for any untracked file and
    # therefore a way to bind a passing observation to a tree that is not HEAD.
    # The one path `gate evaluate` writes is a constant; see DEFAULT_JOURNAL.
    rn.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to run, after --",
    )
    rn.set_defaults(func=cmd_run)

    kg = sub.add_parser("keygen", help="generate a producer signing key")
    kg.add_argument("--producer", required=True, help="identity the key belongs to")
    kg.set_defaults(func=cmd_keygen)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
