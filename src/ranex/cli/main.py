"""`ranex` — the operator entry point.

Two subcommands, and together they close the loop:

`run` observes a command and writes down what it saw. `gate evaluate` answers one
question — may this change land? — from those observations, and writes down why.

Neither reaches a model. Removing every credential on the machine changes no
verdict, and changes nothing `run` records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.cli.confinement import resolve_within_repository
from ranex.cli.subject import (
    SubjectError,
    materialise_subject,
    verified_blob_at_path,
)
from ranex.cli.toolchain import (
    ToolchainError,
    pinned_path_value,
    resolve_tool,
)
from ranex.foundation.canonical import canonical_sha256, command_digest
from ranex.foundation.signing import (
    generate_keypair,
    public_key_for,
    sign_evidence,
)
from ranex.governed_execution.api import (
    Claim,
    Evidence,
    Gate,
    Verdict,
)
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.admission import (
    Admission,
    Rejection,
    RejectionReason,
    admit,
)
from ranex.governed_execution.domain.deps import DepsApproval, DepsDerivation
from ranex.governed_execution.domain.task import TaskCandidate, TaskDispatch
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    KeyringError,
    load_keyring,
    load_keyring_text,
)
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate_text
from ranex.provisioning.approval import depset_digest, package_delta
from ranex.provisioning.derivation import derive_lock, refuse_mismatch
from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.fetching import ensure_wheels
from ranex.provisioning.lockfile import (
    LockError,
    WheelArtifact,
    parse_lock,
    select_wheels,
)
from ranex.provisioning.pins import (
    ResolutionPins,
    load_pins_text,
    refuse_writable_interpreter,
    verified_pinned_binary,
)
from ranex.provisioning.root import assemble_root, verified_wheel_paths
from ranex.provisioning.store import WheelStore
from ranex.provisioning.target import probe_target

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

SIGNING_KEY_VARIABLE = "RANEX_SIGNING_KEY"

# The one path `gate evaluate` writes, and therefore the only path `run` may
# excuse from the dirty-tree check. It is a constant and not an option: a flag
# naming an arbitrary file hands the observed party an exemption from the check
# that binds its evidence to HEAD, which is the whole guarantee.
DEFAULT_JOURNAL = "governance/journal.sqlite3"

# The pins are a constant path for the same reason the journal is: a flag
# naming an arbitrary pins file hands the observed party the choice of
# resolver, index and epoch, which is the whole point of pinning them.
DEFAULT_PINS = "governance/deps.yaml"


def default_store() -> str:
    """Operator-managed wheel storage, outside every governed repository."""

    return str(Path.home() / ".local" / "state" / "ranex" / "store")

# The kernel spawns through this descriptor rather than through the name, so
# the file that runs is the file that was checked. O_PATH needs no read
# permission and never opens the file for content; O_NOFOLLOW plus the regular
# file check below refuses a final component that turned into a symlink between
# the resolution and the open.
EXECUTABLE_OPEN_FLAGS = os.O_NOFOLLOW | getattr(os, "O_PATH", os.O_RDONLY)

# Enough hops to resolve anything real, few enough to end a symlink cycle.
MAX_LINK_HOPS = 40

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


def subject_digest_for(repository_root: Path, ref: str) -> str:
    """The exact subject: the git tree of `ref`, not a mutable branch name."""

    result = git(repository_root, "rev-parse", f"{ref}^{{tree}}")
    if result.returncode != 0:
        raise ValueError(f"cannot resolve ref {ref!r}: {result.stderr.strip()}")
    return "sha256:" + canonical_sha256({"tree": result.stdout.strip()})


def head_commit(repository_root: Path) -> str:
    """The commit HEAD points at, used to detect the ground moving mid-run."""

    result = git(repository_root, "rev-parse", "HEAD")
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
    """Verified bytes `ref` records for `path`, or None when it is absent."""

    relative = path.relative_to(repository_root).as_posix()
    return verified_blob_at_path(repository_root, ref, relative, git)


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

    Bare names are resolved on the pinned toolchain, never on ambient PATH.
    Relative paths are interpreted from the materialised subject tree. The
    answer is resolved through every link and then judged, and the resolved
    path is what gets executed and recorded. Resolving twice — once to check,
    once to run — would be the gap the check exists to close.

    Raises rather than returning None: a command that never ran must not be
    reported as a command with an exit code.
    """

    if "/" in argv0:
        # A path, relative to where the command will run rather than to whatever
        # directory the operator happened to invoke Ranex from.
        named: Path | None = Path(working_directory) / argv0
    else:
        try:
            named = resolve_tool(argv0)
        except ToolchainError as exc:
            raise ValueError(
                f"cannot resolve {argv0!r} on the pinned toolchain: {exc}"
            ) from exc

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


def refuse_resolution_inside(
    resolution: Resolution,
    argv0: str,
    subject_root: Path,
    description: str,
) -> None:
    """Refuse a destination or route the observed subject gets to choose."""

    step = route_inside(resolution, subject_root)
    if step is not None:
        raise ValueError(
            f"refusing to run {argv0!r}: it resolves to {resolution.executable} "
            f"by way of {step}, inside {description}. A route the observed tree "
            "carries chooses the binary as surely as supplying it does"
        )
    if committable_into(resolution.executable, subject_root):
        raise ValueError(
            f"refusing to run {argv0!r}: it resolves to {resolution.executable}, "
            f"inside {description}. A binary the observed tree supplies cannot "
            "be what proves that tree"
        )


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
    result = git(installation_path.parent, "rev-parse", "--show-toplevel")
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
        # An empty value is what an unset shell variable supplies to
        # ``--journal "$JOURNAL"``. Treating it as None silently disabled the
        # append-only, hash-chained record while still printing PASS, turning a
        # repository invariant off from the command line. Evaluation always
        # records; callers that need another location must name one.
        if not args.journal:
            raise ValueError("--journal must name a journal; an empty path is refused")
        journal_path = resolve_within_repository(root, args.journal)
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
        SubjectError,
        ToolchainError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        # SQLite failures are operational refusals, not gate verdicts. Letting
        # one escape turned a malformed journal into exit 1, whose meaning is
        # that the gate was judged unsatisfied rather than that no judgment ran.
        sqlite3.Error,
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


def cmd_journal_verify(args: argparse.Namespace) -> int:
    """Recompute the journal chain without judging or changing an evaluation."""

    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        # The chain exists to expose out-of-band edits. Leaving it callable only
        # from tests made that evidence unavailable to operators, so this path
        # is confined exactly as evaluation's journal path is before it is read.
        if not args.journal:
            raise ValueError("--journal must name a journal; an empty path is refused")
        journal_path = resolve_within_repository(root, args.journal)
        # A missing record is not an empty chain: reporting PASS after deletion
        # inverted absence-blocks into a clean bill of health. Check before the
        # verifier opens SQLite so this command refuses without creating it.
        # This does not eliminate a replacement race after the check; the
        # verifier's immutable read-only connection separately prevents writes.
        if not journal_path.is_file():
            raise ValueError(f"journal does not exist: {journal_path}")
        verified = Journal(journal_path).verify()
    except (
        ToolchainError,
        ValueError,
        OSError,
        sqlite3.Error,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    if verified:
        print(f"PASS  journal={journal_path}  chain=verified")
        return EXIT_PASS
    print(f"FAIL  journal={journal_path}  chain=invalid")
    return EXIT_FAIL


def _task_committed_blob(worktree: Path, commit: str, candidate: str, description: str) -> bytes:
    """Read a task trust root from the dispatched commit, never from its disk.

    The harness owns the worktree after dispatch, so its catalog and keyring on
    disk are assertions rather than authority.  Object verification also keeps
    a repository-local replacement ref from answering with bytes that the HEAD
    commit does not carry.
    """

    named = named_within_repository(worktree, candidate)
    relative = named.relative_to(worktree).as_posix()
    content = verified_blob_at_path(worktree, commit, relative, git)
    if content is None:
        raise ValueError(
            f"commit {commit} carries no {description} at {relative}"
        )
    return content


def _latest_task_dispatch(entries: list[dict[str, object]], task_id: str) -> dict[str, object] | None:
    """Return the latest dispatch the kernel recorded for this task identifier."""

    return next(
        (
            record
            for record in reversed(entries)
            if record.get("type") == "task-dispatch"
            and record.get("task_id") == task_id
        ),
        None,
    )


def cmd_task_dispatch(args: argparse.Namespace) -> int:
    """Create an external worktree and record the immutable dispatch facts."""

    try:
        if not args.task_id.strip():
            raise ValueError("--task-id must be non-blank")
        raw_worktree = Path(args.worktree)
        if os.path.lexists(raw_worktree):
            raise ValueError(f"--worktree already exists: {raw_worktree}")
        target = Path(args.target).resolve()
        worktree = raw_worktree.resolve()
        target_check = git(target, "rev-parse", "--is-inside-work-tree")
        if target_check.returncode != 0 or target_check.stdout.strip() != "true":
            raise ValueError(f"--target is not a git working repository: {target}")
        base_commit = head_commit(target)
        if len(base_commit) != 40 or any(
            character not in "0123456789abcdef" for character in base_commit
        ):
            raise ValueError(f"--target HEAD is not a 40-hex commit: {base_commit!r}")
        created = git(target, "worktree", "add", str(worktree), "HEAD")
        if created.returncode != 0:
            raise ValueError(f"cannot create worktree: {created.stderr.strip()}")
        Journal(Path(args.journal).resolve()).append(
            TaskDispatch(args.task_id, str(worktree), base_commit)
        )
    except (ToolchainError, ValueError, OSError, sqlite3.Error) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(f"DISPATCHED  task={args.task_id}  worktree={worktree}")
    return EXIT_PASS


def cmd_task_judge(args: argparse.Namespace) -> int:
    """Materialise a candidate from the dispatched worktree without approving it."""

    try:
        journal_path = Path(args.journal).resolve()
        if not journal_path.is_file():
            raise ValueError(f"no task dispatch recorded for {args.task_id!r}")
        journal = Journal(journal_path)
        if not journal.verify():
            raise ValueError(f"journal is invalid; refusing task {args.task_id!r}")
        dispatch = _latest_task_dispatch(journal.entries(), args.task_id)
        if dispatch is None:
            raise ValueError(f"no task dispatch recorded for {args.task_id!r}")
        recorded_worktree = dispatch.get("worktree")
        if not isinstance(recorded_worktree, str) or not recorded_worktree:
            raise ValueError(f"invalid dispatch record for task {args.task_id!r}")
        worktree = Path(recorded_worktree)
        if Path(args.emitted_worktree).resolve() != worktree:
            raise ValueError(f"emitted worktree does not match dispatch for {args.task_id!r}")
        commit = head_commit(worktree)
        if args.emitted_commit != commit:
            raise ValueError(f"emitted commit does not match HEAD for {args.task_id!r}")

        catalog_source = _task_committed_blob(
            worktree, commit, args.gate_catalog, "gate catalog"
        )
        keyring_source = _task_committed_blob(
            worktree, commit, args.producers, "producer keyring"
        )
        evidence_path = resolve_within_repository(worktree, args.evidence)
        keyring = load_keyring_text(keyring_source.decode("utf-8"), args.producers)
        admission = admit_records(evidence_path, keyring, worktree)
        definition = load_gate_text(catalog_source.decode("utf-8"), args.gate)
        gate = Gate(
            gate_id=definition.gate_id,
            rule_id=definition.rule_id,
            required_claims=tuple(
                Claim(claim_id=claim.claim_id, command_digest=claim.command_digest)
                for claim in definition.required_claims
            ),
            blocking=definition.blocking,
        )
        subject = subject_digest_for(worktree, commit)
        missing = tuple(
            sorted(
                claim.claim_id
                for claim in gate.required_claims
                if not any(
                    item.satisfies(claim, subject) for item in admission.evidence
                )
            )
        )
        journal.append(TaskCandidate(args.task_id, gate.gate_id, subject, missing))
    except (
        KeyringError,
        SubjectError,
        ToolchainError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        sqlite3.Error,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_FAIL

    print(f"CANDIDATE  task={args.task_id}  gate={gate.gate_id}  subject={subject}")
    return EXIT_PASS if not missing else EXIT_FAIL


def _deny_network() -> None:
    """Child-side, between fork and exec: no network, no privileges needed.

    A fresh user namespace makes CLONE_NEWNET available to an unprivileged
    process, and a fresh network namespace has no interfaces up — every
    connect fails with ENETUNREACH. This is the run-time half of ADR-007's
    hermeticity row; a host that refuses unprivileged user namespaces fails
    the spawn, and that failure is a refusal: a provisioned run that cannot
    be denied the network is not run at all.
    """

    os.unshare(os.CLONE_NEWUSER | os.CLONE_NEWNET)


@dataclass(frozen=True, slots=True)
class Provisioning:
    """Everything the provisioned paths agree on, read once from the commit."""

    pins: ResolutionPins
    manifest: bytes
    lock: bytes
    root_package: str
    store: WheelStore


def _normalised_project_name(manifest: bytes) -> str:
    """The lock's name for the project, from the manifest's own declaration."""

    try:
        parsed = tomllib.loads(manifest.decode("utf-8"))
        name = parsed["project"]["name"]
    except (UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise ValueError(
            f"the committed pyproject.toml declares no project name: {exc}"
        ) from exc
    if not isinstance(name, str) or not name:
        raise ValueError("the committed pyproject.toml declares no project name")
    return re.sub(r"[-_.]+", "-", name).lower()


def _store_outside(root: Path, raw: str) -> WheelStore:
    store_path = Path(raw).expanduser().resolve()
    if committable_into(store_path, root):
        raise ValueError(
            f"refusing a wheel store inside the governed repository: "
            f"{store_path}. Store contents would become part of the subject"
        )
    return WheelStore(store_path)


def _provisioning_for(
    root: Path, ref: str, store: str
) -> Provisioning | None:
    """The committed provisioning inputs, or None when the subject has none.

    Activation is the committed pins file. A subject that carries
    `governance/deps.yaml` is asking for dependency-bearing commands, and
    from that moment absence of any other input blocks; a subject without it
    keeps the self-contained behaviour unchanged.
    """

    named = named_within_repository(root, DEFAULT_PINS)
    if committed_bytes(root, ref, named) is None:
        return None
    pins_source = committed_trust_root(
        root, ref, DEFAULT_PINS, resolve_within_repository(root, DEFAULT_PINS),
        "dependency pins",
    )
    pins = load_pins_text(pins_source.decode("utf-8"))
    manifest = committed_bytes(root, ref, named_within_repository(root, "pyproject.toml"))
    if manifest is None:
        raise ValueError(
            f"refusing: {ref} carries no pyproject.toml, and the committed "
            "dependency pins say this subject has dependencies. A manifest "
            "that is not committed cannot be derived from"
        )
    lock = committed_bytes(root, ref, named_within_repository(root, "uv.lock"))
    if lock is None:
        raise ValueError(
            f"refusing: {ref} carries no uv.lock. Absence cannot mean an "
            "empty dependency set — commit the lock the manifest resolves to"
        )
    return Provisioning(
        pins=pins,
        manifest=manifest,
        lock=lock,
        root_package=_normalised_project_name(manifest),
        store=_store_outside(root, store),
    )


def _selected_artifacts(provisioning: Provisioning) -> tuple[tuple[WheelArtifact, ...], str]:
    """The wheel set the committed lock selects, and its depset identity."""

    refuse_writable_interpreter(provisioning.pins.python)
    target = probe_target(provisioning.pins.python)
    artifacts = select_wheels(
        parse_lock(provisioning.lock), provisioning.root_package, target
    )
    return artifacts, depset_digest(provisioning.lock, target)


def _latest_of(entries: list[dict[str, object]], record_type: str) -> dict[str, object] | None:
    return next(
        (
            record
            for record in reversed(entries)
            if record.get("type") == record_type
        ),
        None,
    )


def _render_delta(previous: Mapping[str, str] | None, current: Mapping[str, str]) -> list[str]:
    delta = package_delta(previous, current)
    lines: list[str] = []
    if not delta.baseline_exists:
        lines.append("no prior approval; the full set is the delta:")
    for name, version in delta.added:
        lines.append(f"  + {name} {version}")
    for name, version in delta.removed:
        lines.append(f"  - {name} {version}")
    for name, old, new in delta.changed:
        lines.append(f"  ~ {name} {old} -> {new}")
    if delta.baseline_exists and not (delta.added or delta.removed or delta.changed):
        lines.append("  unchanged since the last approval")
    return lines


def cmd_deps_fetch(args: argparse.Namespace) -> int:
    """Derive, verify and provision the committed dependency set. Networked."""

    descriptor: int | None = None
    scratch: str | None = None
    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        journal_path = resolve_within_repository(root, DEFAULT_JOURNAL)
        started_at = head_commit(root)
        provisioning = _provisioning_for(root, started_at, args.store)
        if provisioning is None:
            raise ValueError(
                f"HEAD carries no {DEFAULT_PINS}; there is nothing to "
                "provision. Commit the operator pins first"
            )
        descriptor = verified_pinned_binary(
            provisioning.pins.resolver, provisioning.pins.resolver_sha256
        )
        scratch = tempfile.mkdtemp(prefix="ranex-deps-")
        derived = derive_lock(
            provisioning.manifest, provisioning.pins, descriptor, Path(scratch)
        )
        refuse_mismatch(provisioning.lock, derived)
        artifacts, depset = _selected_artifacts(provisioning)
        report = ensure_wheels(artifacts, provisioning.store)
        packages = {item.package: item.version for item in artifacts}
        journal = Journal(journal_path)
        journal.append(
            DepsDerivation(
                lock_sha256=canonical_sha256_of_bytes(provisioning.lock),
                depset_digest=depset,
                packages=packages,
            )
        )
        approval = _latest_of(journal.entries(), "deps-approval")
        approved = approval is not None and approval.get("depset_digest") == depset
    except (
        ProvisioningError,
        SubjectError,
        ToolchainError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        sqlite3.Error,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if scratch is not None:
            shutil.rmtree(scratch, ignore_errors=True)

    print(
        f"FETCHED  packages={len(packages)}  "
        f"downloaded={len(report.downloaded)}  reused={len(report.reused)}"
    )
    print(f"         depset={depset}")
    if not approved:
        print("         not yet approved: run `ranex deps approve --approver <id>`")
    return EXIT_PASS


def cmd_deps_approve(args: argparse.Namespace) -> int:
    """Record a human's acceptance of the exact derived package set.

    Approving an underived lock is refused: the delta would describe bytes
    nothing regenerated, and hashes that were never checked as output. What
    approval means — and does not mean — is printed with the delta: the
    accepted code still runs inside the measured command (ADR-007 s.p. 17).
    """

    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        if not args.approver.strip():
            raise ValueError("--approver must be non-blank")
        journal_path = resolve_within_repository(root, DEFAULT_JOURNAL)
        started_at = head_commit(root)
        provisioning = _provisioning_for(root, started_at, default_store())
        if provisioning is None:
            raise ValueError(
                f"HEAD carries no {DEFAULT_PINS}; there is nothing to approve"
            )
        artifacts, depset = _selected_artifacts(provisioning)
        packages = {item.package: item.version for item in artifacts}
        journal = Journal(journal_path)
        entries = journal.entries()
        derivation = _latest_of(entries, "deps-derivation")
        if derivation is None or derivation.get("depset_digest") != depset:
            raise ValueError(
                "no derivation is recorded for this lock and target; run "
                "`ranex deps fetch` first — approval covers checked bytes only"
            )
        approval = _latest_of(entries, "deps-approval")
        previous = approval.get("packages") if approval is not None else None
        delta_lines = _render_delta(previous, packages)
        journal.append(
            DepsApproval(
                depset_digest=depset, packages=packages, approver_id=args.approver
            )
        )
    except (
        ProvisioningError,
        SubjectError,
        ToolchainError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        sqlite3.Error,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    for line in delta_lines:
        print(line)
    print(f"APPROVED  packages={len(packages)}  approver={args.approver}")
    print(f"          depset={depset}")
    print(
        "          approval reduces hidden change; the approved code still "
        "chooses its own behaviour inside the gated command"
    )
    return EXIT_PASS


def canonical_sha256_of_bytes(data: bytes) -> str:
    """Plain content hash, hex — the journal's name for exact lock bytes."""

    return hashlib.sha256(data).hexdigest()


def cmd_run(args: argparse.Namespace) -> int:
    """Run a command and record what was observed. Never judge it.

    Exits with the wrapped command's own exit code so `run && gate evaluate`
    composes. A failing command is honest evidence of failure, not a usage
    error. Exit 2 can therefore mean either a refusal to record, which writes
    nothing, or a wrapped command that exited 2 after its record was written.
    The exit code alone cannot distinguish those cases; inspect the evidence
    file to learn whether a record is present.
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
        # `run` never writes the journal. Knowing its constant path only keeps
        # Ranex's own preceding evaluation from making the operator-facing
        # dirty-tree courtesy refuse every later run.
        resolve_within_repository(root, DEFAULT_JOURNAL)
        if not command:
            raise ValueError("a command is required after --")

        # Captured once, and everything below is asked about this exact commit
        # rather than about `HEAD`, which is a name the observed party can move
        # between two questions. Taken before argv[0] resolution now, because
        # whether this subject provisions dependencies is also a question
        # about this exact commit.
        started_at = head_commit(root)
        provisioning = _provisioning_for(root, started_at, args.store)

        # Bare and absolute names do not depend on the materialised cwd, so
        # resolve them before materialisation. This keeps the governed-root
        # route and inode controls live for absolute same-uid access, including
        # a committed symlink whose tree entry the materialiser also refuses.
        preliminary: Resolution | None = None
        provisioned_resolver = (
            provisioning is not None
            and command[0] == provisioning.pins.resolver.name
        )
        if provisioned_resolver:
            # The catalog's bare resolver name means the pinned resolver —
            # never ambient PATH, and never the pinned system directories,
            # which deliberately do not carry it. Identity is enforced by
            # digest at spawn; the usual route and containment rules apply
            # to the pinned path unchanged.
            preliminary = Resolution(
                executable=provisioning.pins.resolver.resolve(),
                route=walked_route(provisioning.pins.resolver),
            )
            refuse_resolution_inside(
                preliminary,
                command[0],
                root,
                "the governed repository under observation",
            )
        elif "/" not in command[0] or Path(command[0]).is_absolute():
            preliminary = resolve_executable(command[0], root)
            refuse_resolution_inside(
                preliminary,
                command[0],
                root,
                "the governed repository under observation",
            )

        # Everything knowable without constructing the sample refuses before
        # the command runs. A test suite is expensive; discovering afterwards
        # that its record cannot be written honestly wastes all of it.
        private_key = private_signing_key(governed_root)
        # The same trust root, and the same refusal, on the way in. `run` only
        # consults the keyring to avoid writing a record that evaluation would
        # refuse — but a keyring the caller supplies at an uncommitted path
        # turns that courtesy into a way to self-register, and a gitignored one
        # is invisible to the dirty-tree check below as well as to `git status`.
        keyring_source = committed_trust_root(
            root, started_at, args.producers, keyring_path, "producer keyring"
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

        # An operator courtesy since ADR-005, not the guarantee it used to be:
        # the observation is built from committed bytes, so an uncommitted edit
        # can no longer change what is observed. It must still be *reported*, or
        # someone who edits a check and forgets to commit silently scores the
        # committed version instead.
        #
        # Named, not resolved. `resolve_within_repository` answers "what will be
        # read and written", which is the right question for I/O and the wrong
        # one for an exemption: it follows a symlink the observed party controls,
        # and the exemption then lands on whatever that link chose (D16).
        dirty = uncommitted_paths(
            root,
            ignoring=(
                named_within_repository(root, args.evidence),
                named_within_repository(root, DEFAULT_JOURNAL),
            ),
        )
        if dirty:
            raise ValueError(
                "refusing to record evidence against a dirty working tree; "
                f"HEAD does not describe: {', '.join(dirty)}"
            )
        if head_commit(root) != started_at:
            raise ValueError(
                f"refusing to run: HEAD moved from {started_at[:12]} while the "
                "subject was being prepared"
            )
        subject = subject_digest_for(root, started_at)

        # A provisioned subject proves its dependency chain before anything
        # spawns: the committed lock must have been derivation-verified, the
        # exact package set must be approved, and every wheel must re-verify
        # out of the store. Absence of any link blocks — a run that cannot
        # prove its dependencies were checked does not get to produce
        # evidence that looks like one that could.
        artifacts: tuple[WheelArtifact, ...] = ()
        if provisioning is not None:
            artifacts, depset = _selected_artifacts(provisioning)
            entries = Journal(
                resolve_within_repository(root, DEFAULT_JOURNAL)
            ).entries()
            derivation = _latest_of(entries, "deps-derivation")
            if (
                derivation is None
                or derivation.get("lock_sha256")
                != canonical_sha256_of_bytes(provisioning.lock)
                or derivation.get("depset_digest") != depset
            ):
                raise ValueError(
                    "refusing to run: the committed uv.lock was never "
                    "derivation-verified for this target. Only `ranex deps "
                    "fetch` checks the lock as output; a lock nothing "
                    "regenerated may be entirely authored"
                )
            packages = {item.package: item.version for item in artifacts}
            approval = _latest_of(entries, "deps-approval")
            if approval is None or approval.get("depset_digest") != depset:
                recorded = approval.get("packages") if approval is not None else None
                delta = _render_delta(
                    recorded if isinstance(recorded, dict) else None, packages
                )
                raise ValueError(
                    "refusing to run: this dependency set is not approved. "
                    "The delta awaiting approval:\n"
                    + "\n".join(delta)
                    + "\nRun `ranex deps approve --approver <id>` to accept it"
                )
            # Re-verified out of the store now, so a missing or corrupt entry
            # refuses before the expensive materialisation, not after.
            verified_wheel_paths(artifacts, provisioning.store)

        # The command sees only this verified sample. HOME and TMPDIR are
        # siblings of the sample tree, so command scratch cannot become an
        # undeclared subject input and all three disappear in one cleanup.
        with materialise_subject(root, started_at, git) as materialisation:
            deps_environment: Path | None = None
            if provisioning is not None:
                assembly = verified_pinned_binary(
                    provisioning.pins.resolver, provisioning.pins.resolver_sha256
                )
                try:
                    deps_environment = assemble_root(
                        artifacts,
                        provisioning.store,
                        provisioning.pins,
                        assembly,
                        materialisation.root / "deps",
                    )
                finally:
                    os.close(assembly)
            resolution = preliminary or resolve_executable(
                command[0], materialisation.tree
            )
            executable = resolution.executable
            refuse_resolution_inside(
                resolution,
                command[0],
                root,
                "the governed repository under observation",
            )
            refuse_resolution_inside(
                resolution,
                command[0],
                materialisation.tree,
                "the materialised subject tree",
            )

            # Open once and spawn through the descriptor. Re-walking a cleared
            # name at exec time would reopen the ancestor-swap race. The
            # pinned resolver is opened by its verifier instead, so the bytes
            # that hash to the pin are the bytes the descriptor will execute.
            if provisioned_resolver:
                descriptor = verified_pinned_binary(
                    provisioning.pins.resolver, provisioning.pins.resolver_sha256
                )
            else:
                descriptor = os.open(executable, EXECUTABLE_OPEN_FLAGS)
            identity = os.fstat(descriptor)
            if not stat.S_ISREG(identity.st_mode):
                raise ValueError(
                    f"refusing to run {command[0]!r}: {executable} is not a "
                    "regular file, so what would execute is not what was resolved"
                )
            opened = path_behind(
                descriptor,
                f"cannot confirm which file {command[0]!r} opened, so it will "
                "not be run",
            )
            if opened != executable:
                raise ValueError(
                    f"refusing to run {command[0]!r}: it resolved to {executable} "
                    f"and the file actually opened is {opened}; the path changed "
                    "while it was being checked"
                )
            for subject_root, description in (
                (root, "the governed repository under observation"),
                (materialisation.tree, "the materialised subject tree"),
            ):
                twin = same_file_inside(identity, subject_root)
                if twin is not None:
                    raise ValueError(
                        f"refusing to run {command[0]!r}: {executable} is the "
                        f"same file as {twin}, inside {description}. A hard link "
                        "and a bind mount are both a second name for one file, "
                        "not a second file, so the observed tree chose the bytes"
                    )

            # Taken last and against the sample, not the governed checkout: it
            # is these inodes whose mutation would make the subject digest stop
            # describing what the command observed.
            observed = materialisation.tracked_paths
            untouched = stat_fingerprint(materialisation.tree, observed)
            environment = {
                "PATH": pinned_path_value(),
                "HOME": str(materialisation.home),
                "TMPDIR": str(materialisation.temporary),
                "LANG": "C.UTF-8",
            }
            before_exec = None
            if provisioning is not None and deps_environment is not None:
                # ADR-007: the run sees the sealed root and nothing else. The
                # root's bin joins the pinned search so the command's own
                # child processes find the provisioned entry points; the uv
                # controls stop the runner syncing, fetching or reading
                # ambient configuration; the namespace pair denies the
                # network outright rather than asking uv to abstain.
                environment["PATH"] = (
                    f"{deps_environment / 'bin'}{os.pathsep}{environment['PATH']}"
                )
                environment.update(
                    {
                        "UV_PROJECT_ENVIRONMENT": str(deps_environment),
                        "UV_NO_SYNC": "1",
                        "UV_OFFLINE": "1",
                        "UV_NO_CONFIG": "1",
                        # The committed lock is an input to this run and was
                        # derivation-verified before it started. `uv run`
                        # will re-lock and rewrite it given the chance —
                        # measured: a plain `uv run pytest -q` here dropped
                        # the `[options]` epoch block from uv.lock, which
                        # then failed its own byte comparison on the next
                        # fetch. Rewriting a tracked file would also trip
                        # the write check below and refuse the record, so
                        # this turns a confusing late refusal into no
                        # rewrite at all.
                        "UV_FROZEN": "1",
                        "UV_PYTHON_DOWNLOADS": "never",
                        "UV_CACHE_DIR": str(materialisation.temporary / "uv-cache"),
                    }
                )
                before_exec = _deny_network
            try:
                completed = subprocess.run(
                    [str(executable), *command[1:]],
                    executable=f"/proc/self/fd/{descriptor}",
                    pass_fds=(descriptor,),
                    cwd=materialisation.tree,
                    check=False,
                    env=environment,
                    preexec_fn=before_exec,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                raise ValueError(f"cannot run {command[0]!r}: {exc}") from exc
            finally:
                os.close(descriptor)
                descriptor = None

            # Same-uid absolute access can still move the governed repository.
            # This is not the hermeticity boundary, but recording the old digest
            # after seeing it happen would still be a knowingly false claim.
            if head_commit(root) != started_at:
                raise ValueError(
                    "refusing to record evidence: the command moved HEAD from "
                    f"{started_at[:12]} during the run, so {subject[:19]}… "
                    "does not describe what was observed"
                )
            written = sorted(
                path
                for path, fingerprint in stat_fingerprint(
                    materialisation.tree, observed
                ).items()
                if fingerprint != untouched[path]
            )
            if written:
                raise ValueError(
                    "refusing to record evidence: the command wrote to tracked "
                    f"file(s) while it ran — {', '.join(written)} — so "
                    f"{subject[:19]}… does not describe the tree that was "
                    "observed, whatever the tree looks like now"
                )

        # Cleanup completed before evidence becomes durable. A scratch tree we
        # cannot remove is an operational refusal, not a gate verdict.
        content = {
            "claim_id": args.claim,
            "subject_digest": subject,
            "producer_id": args.producer,
            "command": shlex.join(command),
            "command_digest": command_digest(command),
            "executable_path": str(executable),
            "exit_code": int(completed.returncode),
        }
        record_evidence(
            evidence_path,
            {**content, "signature": sign_evidence(content, private_key)},
        )
    except (
        ProvisioningError,
        SubjectError,
        ToolchainError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        sqlite3.Error,
        json.JSONDecodeError,
    ) as exc:
        if descriptor is not None:
            os.close(descriptor)
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
    except (ToolchainError, ValueError, OSError) as exc:
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

    journal = sub.add_parser("journal", help="journal operations").add_subparsers(
        dest="action", required=True
    )
    verify = journal.add_parser("verify", help="verify the journal hash chain")
    verify.add_argument("--repository", default=".", help="repository root")
    verify.add_argument("--journal", default=DEFAULT_JOURNAL, help="journal path")
    verify.set_defaults(func=cmd_journal_verify)

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
        "--store",
        default=default_store(),
        help="operator wheel store, outside the repository",
    )
    rn.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to run, after --",
    )
    rn.set_defaults(func=cmd_run)

    deps = sub.add_parser("deps", help="dependency provisioning").add_subparsers(
        dest="action", required=True
    )
    fe = deps.add_parser(
        "fetch", help="derive, verify and provision dependencies (networked)"
    )
    fe.add_argument("--repository", default=".", help="repository root")
    fe.add_argument(
        "--store",
        default=default_store(),
        help="operator wheel store, outside the repository",
    )
    fe.set_defaults(func=cmd_deps_fetch)

    ap = deps.add_parser("approve", help="approve the derived dependency delta")
    ap.add_argument("--repository", default=".", help="repository root")
    ap.add_argument("--approver", required=True, help="identity approving")
    ap.set_defaults(func=cmd_deps_approve)

    kg = sub.add_parser("keygen", help="generate a producer signing key")
    kg.add_argument("--producer", required=True, help="identity the key belongs to")
    kg.set_defaults(func=cmd_keygen)

    task = sub.add_parser("task", help="dispatch and materialise task candidates")
    task_actions = task.add_subparsers(dest="action", required=True)
    dispatch = task_actions.add_parser("dispatch", help="create a task worktree")
    dispatch.add_argument("--task-id", required=True, help="task identifier")
    dispatch.add_argument("--target", required=True, help="external git repository")
    dispatch.add_argument("--worktree", required=True, help="new external worktree")
    dispatch.add_argument("--journal", required=True, help="external task journal")
    dispatch.set_defaults(func=cmd_task_dispatch)

    judge = task_actions.add_parser("judge", help="materialise a task candidate")
    judge.add_argument("--task-id", required=True, help="task identifier")
    judge.add_argument("--emitted-worktree", required=True, help="harness worktree")
    judge.add_argument("--emitted-commit", required=True, help="harness commit")
    judge.add_argument("--gate", required=True, help="gate identifier")
    judge.add_argument("--gate-catalog", required=True, help="committed gate catalog")
    judge.add_argument("--evidence", required=True, help="worktree evidence path")
    judge.add_argument("--producers", required=True, help="committed producer keyring")
    judge.add_argument("--journal", required=True, help="external task journal")
    judge.set_defaults(func=cmd_task_judge)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
