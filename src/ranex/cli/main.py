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
import signal
import sqlite3
import stat
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from ranex.bootstrap.composition import (
    build_gate_evaluator,
    catalog_digest_for,
    claim_definition_for,
)
from ranex.cli.confinement import resolve_within_repository
from ranex.cli.delegation import cmd_task_delegate
from ranex.cli.fanout import cmd_task_fanout
from ranex.cli.repository import (
    committable_into,
    git,
    governed_repository_root,
    named_within_repository,
    nearest_existing_directory,
    stat_fingerprint,
    uncommitted_paths,
)
from ranex.cli.subject import (
    Materialisation,
    SubjectError,
    materialise_subject,
    verified_blob_at_path,
)
from ranex.cli.toolchain import (
    ToolchainError,
    pinned_path_value,
    resolve_tool,
)
from ranex.foundation.approval import candidate_row_hash, verify_approval
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256, command_digest
from ranex.foundation.confinement_result import validate_confinement_result
from ranex.foundation.signing import (
    generate_keypair,
    public_key_for,
    sign_evidence,
)
from ranex.foundation.suite_results import (
    freeze_manifest,
    load_manifest_bytes,
    manifest_digest,
    parse_results_artifact,
    read_results_artifact,
)
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.api import (
    Claim,
    Evidence,
    Gate,
    Verdict,
)
from ranex.governed_execution.domain.admission import (
    Admission,
    Rejection,
    RejectionReason,
    admit,
)
from ranex.governed_execution.domain.deps import DepsApproval, DepsDerivation
from ranex.governed_execution.domain.task import (
    TaskCandidate,
    TaskDispatch,
    TaskMergeCheck,
    TaskMergeIntent,
    TaskMergeOutcome,
)
from ranex.governed_execution.verdict_projection import presentation_partition, project_verdict
from ranex.governed_execution.verdict_publication import publish_verdict
from ranex.observability import TRACE_VARIABLES, stage_begin, stage_end
from ranex.observability import schema as trace_schema
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    KeyringError,
    load_keyring,
    load_keyring_text,
    load_trust_keyring_text,
)
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate_text
from ranex.provisioning.approval import depset_digest, package_delta
from ranex.provisioning.derivation import derive_lock, refuse_mismatch
from ranex.provisioning.errors import ProvisioningError
from ranex.provisioning.fetching import ensure_wheels
from ranex.provisioning.lockfile import (
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
DEFAULT_GATE_CATALOG = "governance/gates.yaml"
DEFAULT_SUITE_MANIFEST = "governance/suite_manifest.json"
DEFAULT_EVIDENCE = "governance/evidence.json"

# The committed keyring's conventional path. A constant so `keygen` can tell a
# first-time operator exactly which file to create, and say the same name the
# other commands default to.
DEFAULT_PRODUCERS = "governance/producers.yaml"
DEFAULT_VERDICT_DIR = "governance/verdicts"
VERDICT_SIGNING_KEY_VARIABLE = "RANEX_VERDICT_SIGNING_KEY"
VERDICT_DIR_VARIABLE = "RANEX_VERDICT_DIR"


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


def private_signing_key(
    governed_root: Path, *, variable: str = SIGNING_KEY_VARIABLE
) -> str:
    """Read the producer's private key from the environment.

    Refuses a key any other account can read. `keygen` writes 0600, but a key
    copied between machines usually arrives with whatever mode the copy gave it,
    and a world-readable signing key makes the whole slice decorative.

    Refuses a key inside the repository for the same reason `keygen` refuses to
    create one there. A refusal only at the point of creation is advisory: the
    key can be placed by hand, and a `.gitignore` entry keeps `git status` clean
    so nothing else notices it is one `git add -f` from being published.
    """

    raw_path = os.environ.get(variable)
    if not raw_path:
        raise ValueError(
            f"{variable} is not set, so nothing can sign this "
            "record; refusing to write unsigned evidence"
        )
    # Resolved before it is judged: the check must be about the file that will
    # actually be read, not about the name it was reached by.
    key_path = Path(raw_path).resolve()
    if not key_path.is_file():
        raise ValueError(f"{variable} points at no file: {key_path}")

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
        definition = load_gate_text(catalog_source.decode("utf-8"), args.gate)
        suite_manifest_source: bytes | None = None
        if any(
            claim.results_artifact is not None
            for claim in definition.required_claims
        ):
            manifest_path = resolve_within_repository(root, args.suite_manifest)
            suite_manifest_source = committed_trust_root(
                root,
                args.ref,
                args.suite_manifest,
                manifest_path,
                "suite manifest",
            )
            load_manifest_bytes(suite_manifest_source)
        keyring = load_keyring_text(keyring_source.decode("utf-8"), keyring_path)
        # The root is passed so the containment decision `run` made about
        # argv[0] is taken again here, from the signed path in the record.
        admission = admit_records(evidence_path, keyring, root)
        evaluator = build_gate_evaluator(
            catalog_source,
            journal_path,
            suite_manifest_source,
        )
        result = evaluator.evaluate(
            args.gate,
            admission.evidence,
            subject_digest=subject,
            approver_id=args.approver,
        )
        projected = project_verdict(
            result, admission,
            required_claims=tuple(claim.claim_id for claim in definition.required_claims),
        )
        verdict_key_path = os.environ.get(VERDICT_SIGNING_KEY_VARIABLE)
        verdict_dir_value = os.environ.get(VERDICT_DIR_VARIABLE)
        if (verdict_key_path is None) != (verdict_dir_value is None):
            raise ValueError(
                f"{VERDICT_SIGNING_KEY_VARIABLE} and {VERDICT_DIR_VARIABLE} must be configured together"
            )
        if verdict_key_path is not None and verdict_dir_value is not None:
            trust_keyring = load_trust_keyring_text(
                keyring_source.decode("utf-8"), keyring_path
            )
            private_key = private_signing_key(
                governed_root, variable=VERDICT_SIGNING_KEY_VARIABLE
            )
            if public_key_for(private_key) != trust_keyring.verdict_signer_public_key:
                raise ValueError("verdict signing key does not match the committed verdict signer")
            verdict_dir = resolve_within_repository(root, verdict_dir_value)
            publish_verdict(
                verdict_dir / f"{result.subject_digest.removeprefix('sha256:')}.json",
                projected,
                root=governed_root,
                signer_id=trust_keyring.verdict_signer_id,
                private_key=private_key,
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
    # A claim some admitted record names is not work never done, whatever else
    # is wrong with that record: it may describe another tree, another command,
    # or a run that failed. Each of those is an event an operator must be able
    # to tell from silence, and the kernel already names which one it was — so
    # the absence sentence is spent only on claims nothing was recorded for, and
    # the kernel's diagnosis is printed for the rest. A digest mismatch reported
    # as absence is the reporting defect SLICE-002 was reopened to fix, one
    # field further along.
    unattributable, refused, absent, observed = presentation_partition(projected, admission)
    missing = set(result.missing_claims)

    # The absence sentence this block prints, verbatim, when it prints one.
    # The kernel's own diagnosis follows and restates that same absence as its
    # final clause; a sentence printed twice reads as two separate problems.
    absence_sentence: str | None = None
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
        absence_sentence = f"no evidence for required claim: {', '.join(absent)}"
        print(f"      {absence_sentence}")
    if result.reason and (observed or not missing):
        # The kernel's own diagnosis, kept whenever it says something the
        # partition cannot: which of the four ways a record failed to satisfy
        # the claim it names, a contradiction between two records, or a
        # self-approval refusal that names no claim at all. Withheld when every
        # missing claim is genuinely absent, because then it would only repeat
        # the sentence printed above — possibly for claims that were refused.
        #
        # That withholding covered the all-absent case only. In the mixed case
        # — one claim stale, another genuinely absent — the reason carries both
        # clauses and the absence one was already printed above, so it appeared
        # twice in a single verdict. The genuine absence clause is always the
        # reason's FINAL clause (_diagnosis appends it last), so the repeat is
        # removed by anchored suffix comparison — never by splitting the
        # reason, whose "; " separator a claim ID may legally contain. When
        # any missing claim ID carries "; ", the string is ambiguous and dedup
        # steps aside entirely: the full reason prints verbatim, duplicate and
        # all — fail toward repetition, never toward loss. The reason string
        # itself is unchanged — it is the recorded diagnosis and what the
        # journal and verdict record carry. This is presentation only.
        reason = result.reason
        if absence_sentence is not None and not any(
            "; " in claim_id for claim_id in missing
        ):
            suffix = f"; {absence_sentence}"
            if reason == absence_sentence:
                reason = ""
            elif reason.endswith(suffix):
                reason = reason[: -len(suffix)]
        if reason:
            print(f"      {reason}")

    print(f"      subject={result.subject_digest}")
    return EXIT_FAIL


def _journal_first_broken_row(journal_path: Path) -> tuple[int, int, int] | None:
    """Name the first row that breaks the chain, for the refusal's wording.

    A detection that says only ``chain=invalid`` sends the operator to
    re-derive by hand which row to inspect. This walk mirrors
    ``Journal.verify`` exactly — same row order, same genesis root, same
    recomputation over the parsed record — and reports the first row that
    fails either link check, as ``(seq, ordinal, total)``: the row's own
    ``seq`` (AUTOINCREMENT, so after an out-of-band delete it is not its
    position) plus its 1-based ordinal among the surviving rows. It runs
    only after ``verify`` already said the chain is broken, read-only: it
    is the refusal's presentation, never a second verdict. ``None`` is the
    unreachable defensive shape (verify said False but the mirror walk
    found no break); the caller prints the row-less refusal rather than
    guessing one.
    """

    connection = sqlite3.connect(f"{journal_path.as_uri()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT seq, record, prev_link, link FROM evaluations ORDER BY seq ASC"
        ).fetchall()
    finally:
        connection.close()
    previous = "sha256:" + "0" * 64
    for ordinal, (seq, record, prev_link, link) in enumerate(rows, start=1):
        if prev_link != previous:
            return seq, ordinal, len(rows)
        expected = "sha256:" + canonical_sha256(
            {"prev_link": previous, "record": json.loads(record)}
        )
        if expected != link:
            return seq, ordinal, len(rows)
        previous = link
    return None


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
        # The naming walk reads the same database verify just read, so it
        # belongs inside the same refusal surface: a SQLite failure here is
        # an operational refusal (exit 2), never a mangled verdict print.
        broken = None if verified else _journal_first_broken_row(journal_path)
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
    # Sad path 3's demand (issue #36): the refusal names WHICH row broke the
    # chain — seq plus ordinal — so the operator inspects the edited row, not
    # the whole journal. Presentation only: detection and exit code are
    # settled above; `None` is the unreachable defensive shape and prints the
    # row-less refusal rather than guessing a row.
    if broken is None:
        print(f"FAIL  journal={journal_path}  chain=invalid")
        return EXIT_FAIL
    seq, ordinal, total = broken
    print(
        f"FAIL  journal={journal_path}  chain=invalid  "
        f"row=seq {seq} (row {ordinal} of {total})"
    )
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


def _perform_task_dispatch(
    task_id: str,
    raw_target: str | Path,
    raw_worktree: str | Path,
    raw_journal: str | Path,
) -> Path:
    if not task_id.strip():
        raise ValueError("--task-id must be non-blank")
    raw_worktree_path = Path(raw_worktree)
    if os.path.lexists(raw_worktree_path):
        raise ValueError(f"--worktree already exists: {raw_worktree_path}")
    target = Path(raw_target).resolve()
    worktree = raw_worktree_path.resolve()
    target_check = git(target, "rev-parse", "--is-inside-work-tree")
    if target_check.returncode != 0 or target_check.stdout.strip() != "true":
        raise ValueError(f"--target is not a git working repository: {target}")
    base_commit = head_commit(target)
    if len(base_commit) != 40 or any(
        character not in "0123456789abcdef" for character in base_commit
    ):
        raise ValueError(f"--target HEAD is not a 40-hex commit: {base_commit!r}")
    journal_path = Path(raw_journal).resolve()
    if journal_path.is_file():
        for entry in Journal(journal_path).entries():
            if entry.get("type") == "task-dispatch" and entry.get("task_id") == task_id:
                raise ValueError(
                    f"refusing task id {task_id!r}: already dispatched; one dispatch, one judgement"
                )
    created = git(target, "worktree", "add", str(worktree), "HEAD")
    if created.returncode != 0:
        raise ValueError(f"cannot create worktree: {created.stderr.strip()}")
    Journal(journal_path).append(
        TaskDispatch(task_id, str(worktree), base_commit)
    )
    return worktree


def cmd_task_dispatch(args: argparse.Namespace) -> int:
    """Create an external worktree and record the immutable dispatch facts."""

    try:
        worktree = _perform_task_dispatch(
            task_id=args.task_id,
            raw_target=args.target,
            raw_worktree=args.worktree,
            raw_journal=args.journal,
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

        base_commit = dispatch.get("base_commit")
        if not isinstance(base_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", base_commit):
            raise ValueError(f"invalid base commit in dispatch for task {args.task_id!r}")

        catalog_source = _task_committed_blob(
            worktree, base_commit, args.gate_catalog, "gate catalog"
        )
        keyring_source = _task_committed_blob(
            worktree, base_commit, args.producers, "producer keyring"
        )
        evidence_path = resolve_within_repository(worktree, args.evidence)
        keyring = load_keyring_text(keyring_source.decode("utf-8"), args.producers)
        admission = admit_records(evidence_path, keyring, worktree)
        definition = load_gate_text(catalog_source.decode("utf-8"), args.gate)
        manifest = None
        if any(
            claim.results_artifact is not None
            for claim in definition.required_claims
        ):
            manifest_source = _task_committed_blob(
                worktree,
                base_commit,
                args.suite_manifest,
                "suite manifest",
            )
            manifest = load_manifest_bytes(manifest_source)
        gate = Gate(
            gate_id=definition.gate_id,
            rule_id=definition.rule_id,
            required_claims=tuple(
                Claim(
                    claim_id=claim.claim_id,
                    command_digest=claim.command_digest,
                    results_required=claim.results_artifact is not None,
                    manifest_digest=(
                        manifest_digest(manifest)
                        if claim.results_artifact is not None and manifest is not None
                        else None
                    ),
                    expected_ids=(
                        tuple(cast(list[str], manifest["suite"]))
                        if claim.results_artifact is not None and manifest is not None
                        else None
                    ),
                    expected_skips=(
                        dict(cast(dict[str, str], manifest["expected_skips"]))
                        if claim.results_artifact is not None and manifest is not None
                        else None
                    ),
                )
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


def _merge_blob_oid(repository_root: Path, commit: str, path: str) -> str:
    result = git(repository_root, "rev-parse", "--verify", f"{commit}:{path}")
    if result.returncode != 0:
        raise ValueError(f"commit {commit} carries no blob at {path}")
    oid = result.stdout.strip()
    kind = git(repository_root, "cat-file", "-t", oid)
    if kind.returncode != 0 or kind.stdout.strip() != "blob":
        raise ValueError(f"object at {commit}:{path} is not a blob")
    return oid


def _merge_blob_bytes(repository_root: Path, oid: str, path: str) -> bytes:
    result = git(repository_root, "cat-file", "blob", oid, text=False)
    if result.returncode != 0:
        raise ValueError(f"cannot read committed blob at {path}")
    return result.stdout


def _recover_task_merges(
    repository_root: Path,
    journal: Journal,
    entries: list[dict[str, object]],
) -> None:
    pending: list[dict[str, object]] = []
    for record in entries:
        if record.get("type") == "task-merge-intent":
            pending.append(record)
        elif record.get("type") == "task-merge-outcome":
            match = next(
                (
                    intent
                    for intent in pending
                    if intent.get("task_id") == record.get("task_id")
                    and intent.get("candidate") == record.get("candidate")
                    and intent.get("target_ref") == record.get("target_ref")
                ),
                None,
            )
            if match is not None:
                pending.remove(match)
    for intent in pending:
        task_id = intent.get("task_id")
        candidate = intent.get("candidate")
        target_ref = intent.get("target_ref")
        if not all(isinstance(value, str) and value for value in (task_id, candidate, target_ref)):
            raise ValueError("invalid unmatched task merge intent")
        task_id = cast(str, task_id)
        candidate = cast(str, candidate)
        target_ref = cast(str, target_ref)
        observed = git(repository_root, "rev-parse", "--verify", target_ref)
        landed = observed.returncode == 0 and observed.stdout.strip() == candidate
        journal.append(
            TaskMergeOutcome(
                task_id,
                candidate,
                target_ref,
                "INFERRED" if landed else "ABORTED",
                "recovery observed candidate at target ref"
                if landed
                else "recovery did not observe candidate at target ref",
            )
        )


def _merge_refuse(
    journal: Journal,
    intent: TaskMergeIntent,
    check: str,
    reason: str,
) -> int:
    journal.append(TaskMergeCheck(intent.task_id, check, "refused", reason))
    journal.append(
        TaskMergeOutcome(
            intent.task_id,
            intent.candidate,
            intent.target_ref,
            "REFUSED",
            reason,
        )
    )
    print(f"REFUSED  task={intent.task_id}  reason={reason}", file=sys.stderr)
    return EXIT_FAIL


def cmd_task_merge(args: argparse.Namespace) -> int:
    """Publish an already judged candidate through ordered, journalled checks."""

    journal: Journal | None = None
    intent: TaskMergeIntent | None = None
    current_check = "policy_approval"
    cas_succeeded = False
    try:
        repository_root = governed_repository_root()
        journal_path = repository_root / DEFAULT_JOURNAL
        if not journal_path.is_file():
            raise ValueError(f"task journal does not exist at {journal_path}")
        journal = Journal(journal_path)
        if not journal.verify():
            raise ValueError("journal is invalid; refusing task merge")
        entries = journal.entries()
        _recover_task_merges(repository_root, journal, entries)
        entries = journal.entries()

        approval_document = json.loads(Path(args.approval).read_text(encoding="utf-8"))
        if not isinstance(approval_document, dict):
            raise ValueError("approval file must contain a JSON object")
        signature = approval_document.get("signature")
        envelope = {key: value for key, value in approval_document.items() if key != "signature"}
        subject = envelope.get("subject")
        tip = envelope.get("tip")
        if not isinstance(subject, str) or not isinstance(tip, str):
            raise ValueError("approval must carry string subject and tip fields")
        intent_candidate = envelope.get("candidate")
        intent = TaskMergeIntent(
            args.task_id,
            intent_candidate if isinstance(intent_candidate, str) else args.candidate,
            subject,
            args.target_ref,
            tip,
        )
        journal.append(intent)

        target = git(repository_root, "rev-parse", "--verify", args.target_ref)
        if target.returncode != 0:
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-20 target-ref-missing")
        observed_tip = target.stdout.strip()
        candidate_exists = git(repository_root, "cat-file", "-e", f"{args.candidate}^{{commit}}")
        if candidate_exists.returncode != 0:
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-21 candidate-missing")
        resolved = git(repository_root, "rev-parse", "--verify", f"{args.candidate}^{{commit}}")
        candidate = resolved.stdout.strip()

        catalog_c_oid = _merge_blob_oid(repository_root, candidate, DEFAULT_GATE_CATALOG)
        catalog_t_oid = _merge_blob_oid(repository_root, observed_tip, DEFAULT_GATE_CATALOG)
        if catalog_c_oid != catalog_t_oid:
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-15 catalog-changed")
        keyring_c_oid = _merge_blob_oid(repository_root, candidate, DEFAULT_PRODUCERS)
        keyring_t_oid = _merge_blob_oid(repository_root, observed_tip, DEFAULT_PRODUCERS)
        if keyring_c_oid != keyring_t_oid:
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-16 keyring-changed")
        catalog_source = _merge_blob_bytes(repository_root, catalog_c_oid, DEFAULT_GATE_CATALOG)
        keyring_source = _merge_blob_bytes(repository_root, keyring_c_oid, DEFAULT_PRODUCERS)
        keyring = load_keyring_text(keyring_source.decode("utf-8"), DEFAULT_PRODUCERS)

        candidate_record = next(
            (
                record
                for record in reversed(entries)
                if record.get("type") == "task-candidate"
                and record.get("task_id") == args.task_id
            ),
            None,
        )
        if candidate_record is None:
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-11 candidate-row-missing")
        if envelope.get("candidate_row_hash") != candidate_row_hash(candidate_record):
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-12 candidate-row-hash-mismatch")
        approver_id = envelope.get("approver_id")
        approver_key = keyring.get(approver_id) if isinstance(approver_id, str) else None
        if approver_key is None:
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-13 approver-absent")
        if not verify_approval(envelope, signature, approver_key):
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-22 forged-approval")

        expected_bindings = (
            ("candidate", candidate, "sad-path-6 candidate-mismatch"),
            ("subject", candidate_record.get("subject_digest"), "sad-path-7 subject-mismatch"),
            ("target_ref", args.target_ref, "sad-path-8 target-ref-mismatch"),
            ("tip", observed_tip, "sad-path-9 tip-mismatch"),
            ("catalog_digest", catalog_digest_for(catalog_source), "sad-path-10 catalog-digest-mismatch"),
        )
        for field, expected, reason in expected_bindings:
            if envelope.get(field) != expected:
                return _merge_refuse(journal, intent, "policy_approval", reason)

        evidence_path = resolve_within_repository(repository_root, DEFAULT_EVIDENCE)
        admission = admit_records(evidence_path, keyring, repository_root)
        if any(item.producer_id == approver_id for item in admission.evidence):
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-14 self-approval")
        candidate_tree = git(repository_root, "rev-parse", f"{candidate}^{{tree}}")
        tip_tree = git(repository_root, "rev-parse", f"{observed_tip}^{{tree}}")
        if candidate == observed_tip or candidate_tree.stdout.strip() == tip_tree.stdout.strip():
            return _merge_refuse(journal, intent, "policy_approval", "sad-path-4 no-subject")
        journal.append(
            TaskMergeCheck(
                args.task_id,
                "policy_approval",
                "passed",
                "policy and approval verified",
            )
        )

        current_check = "ancestry"
        ancestry = git(repository_root, "merge-base", "--is-ancestor", observed_tip, candidate)
        if ancestry.returncode != 0:
            return _merge_refuse(journal, intent, "ancestry", "sad-path-2 not-an-ancestor")
        journal.append(
            TaskMergeCheck(
                args.task_id, "ancestry", "passed", "target tip is an ancestor"
            )
        )

        current_check = "merge_range"
        merges = git(repository_root, "rev-list", "--merges", f"{observed_tip}..{candidate}")
        if merges.returncode != 0 or merges.stdout.strip():
            return _merge_refuse(journal, intent, "merge_range", "sad-path-3 merge-commit-in-range")
        journal.append(
            TaskMergeCheck(
                args.task_id, "merge_range", "passed", "candidate range is linear"
            )
        )

        current_check = "digest_evidence"
        actual_subject = subject_digest_for(repository_root, candidate)
        if actual_subject != subject:
            return _merge_refuse(journal, intent, "digest_evidence", "sad-path-5 subject-digest-mismatch")
        if candidate_record.get("missing_claims") or not any(
            item.subject_digest == subject for item in admission.evidence
        ):
            return _merge_refuse(journal, intent, "digest_evidence", "sad-path-5 satisfying-evidence-missing")
        raw = load_records(evidence_path)
        rejected = {rejection.index for rejection in admission.rejections}
        admitted_ids = [
            canonical_sha256(raw[index])
            for index in range(len(raw))
            if index not in rejected
        ]
        prior_ids = {
            evidence_id
            for record in entries
            if record.get("type") == "task-merge-check"
            and record.get("check") == "digest_evidence"
            and record.get("status") == "passed"
            for evidence_id in record.get("evidence_ids", [])
            if isinstance(evidence_id, str)
        }
        # FRESH means first admission by the merge layer; merge never executes the suite.
        disposition = "REUSE" if set(admitted_ids) <= prior_ids else "FRESH"
        journal.append(
            TaskMergeCheck(
                args.task_id,
                "digest_evidence",
                "passed",
                "digest-bound evidence admitted",
                evidence_disposition=disposition,
                evidence_ids=tuple(admitted_ids),
            )
        )

        current_check = "cas"
        updated = git(repository_root, "update-ref", args.target_ref, candidate, observed_tip)
        if updated.returncode != 0:
            return _merge_refuse(journal, intent, "cas", "sad-path-1 ref-moved")
        cas_succeeded = True
        journal.append(
            TaskMergeCheck(
                args.task_id, "cas", "passed", "expected-old ref update succeeded"
            )
        )
        journal.append(
            TaskMergeOutcome(
                args.task_id,
                candidate,
                args.target_ref,
                "PUBLISHED",
                "candidate published",
            )
        )
    except (
        KeyringError,
        SubjectError,
        ToolchainError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        sqlite3.Error,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        if journal is not None and intent is not None and not cas_succeeded:
            return _merge_refuse(
                journal,
                intent,
                current_check,
                f"{current_check}-error {exc}",
            )
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_FAIL

    print(f"PUBLISHED  task={args.task_id}  candidate={candidate}  target={args.target_ref}")
    return EXIT_PASS


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
        previous = cast(
            Mapping[str, str] | None,
            approval.get("packages") if approval is not None else None,
        )
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


@dataclass(frozen=True, slots=True)
class CommandObservation:
    """Outputs that survive teardown of one verified materialisation."""

    completed: subprocess.CompletedProcess
    executable: Path
    artifact: object | None
    confinement_result_digest: str | None = None
    confinement_profile_digest: str | None = None


_CONFINEMENT_RUNTIME_PROFILE = "governance/confinement/strict-local-v1.json"
_CONFINEMENT_HOST_PROFILE = "governance/confinement/strict-local-host-v1.json"
_CONFINEMENT_LAUNCHER_MANIFEST = "governance/confinement/native-launcher-build-v1.json"
_CONFINEMENT_LAUNCHER = ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"
_CONFINEMENT_QUALIFICATION = ".local/ranex/qualification/strict-local-v1.json"
_CONFINEMENT_LIMITS = {
    "cpu_usage_usec": 1_000_000,
    "memory_bytes": 134_217_728,
    "output_bytes": 65_536,
    "output_depth": 8,
    "output_inodes": 32,
    "pids": 16,
    "wall_time_ms": 5_000,
}


def _copy_session_input(source: Path, destination: Path) -> None:
    """Copy a host-side session prerequisite into the disposable controller root."""

    if source.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _execute_confinement_session(
    root: Path,
    materialisation: object,
    command: Sequence[str],
    executable: Path,
    deps_environment: Path | None,
    *,
    artifact_relative: Path | None,
    artifact_reader: Callable[[Path], object] | None,
) -> CommandObservation:
    """Run strict-local in its controller process and bind its verified result."""

    # Kept structural rather than importing host_confinement: this process owns
    # signing while the child owns its cgroup and must be able to exit first.
    session_root = cast(Materialisation, materialisation)
    session_directory = session_root.root
    temporary = session_root.temporary
    toolchain = deps_environment
    if toolchain is None:
        toolchain = session_directory / "toolchain"
        toolchain.mkdir(mode=0o700)
    scratch = session_directory / "scratch"
    scratch.mkdir(mode=0o700)

    # Qualification and the installed launcher are deliberately copied from the
    # live repository only into the disposable controller root.  The controller
    # revalidates both before opening an executable.
    _copy_session_input(root / _CONFINEMENT_LAUNCHER, session_directory / _CONFINEMENT_LAUNCHER)
    _copy_session_input(root / _CONFINEMENT_QUALIFICATION, session_directory / _CONFINEMENT_QUALIFICATION)
    descriptor_path = session_directory / "confinement-command.json"
    result_path = session_directory / "confinement-result.json"
    descriptor_path.write_bytes(canonical_json_bytes({
        "schema": "ranex-confinement-command-v1",
        "argv": [str(executable), *command[1:]],
        "environment": {"LC_ALL": "C", "TZ": "UTC"},
        "subject": "tree",
        "toolchain": str(toolchain.relative_to(session_directory)),
        "output": str(temporary.relative_to(session_directory)),
        "scratch": "scratch",
        "limits": _CONFINEMENT_LIMITS,
    }))
    source_root = str(Path(__file__).resolve().parents[2])
    environment = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": source_root,
        "LC_ALL": "C",
        "TZ": "UTC",
    }
    # ADR-031's one-child seam: when tracing is enabled, the confinement-
    # session controller — the Ranex-owned Python child that can import the
    # emitter — receives exactly the enabled trace target variable(s) plus
    # RANEX_TRACE_PARENT_SID, extending its fixed four-variable base by
    # exactly the trace variables; tracing off, byte-identical to today.
    # Imported at call time so a reloaded emitter module (tests) governs the
    # seam; the values come from the module's import-time env snapshot.
    import ranex.observability as _observability

    environment.update(_observability.controller_trace_environment())
    try:
        process = subprocess.Popen(
            [
                sys.executable, "-m", "ranex.cli.host_confinement", "session",
                "--profile", f"tree/{_CONFINEMENT_RUNTIME_PROFILE}",
                "--host-profile", f"tree/{_CONFINEMENT_HOST_PROFILE}",
                "--artifact", _CONFINEMENT_LAUNCHER,
                "--manifest", f"tree/{_CONFINEMENT_LAUNCHER_MANIFEST}",
                "--qualification", _CONFINEMENT_QUALIFICATION,
                "--descriptor", str(descriptor_path), "--result", str(result_path),
            ],
            cwd=session_directory,
            start_new_session=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        try:
            stdout, stderr = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                for pipe in (getattr(process, "stdout", None), getattr(process, "stderr", None)):
                    if pipe is not None:
                        try:
                            pipe.close()
                        except OSError:
                            pass
            raise ValueError(
                "E-C46-CONTROLLER: confinement controller timed out and its process group was killed"
            ) from None
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"E-C18-RESULT: cannot run confinement controller: {exc}") from exc
    completed = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    if completed.returncode != 0:
        try:
            refusal = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"E-C18-RESULT: confinement controller failed without a refusal: {completed.stdout!r}"
            ) from exc
        if (
            not isinstance(refusal, dict)
            or not isinstance(refusal.get("refusal"), str)
            or not isinstance(refusal.get("detail"), str)
        ):
            raise ValueError("E-C18-RESULT: confinement controller emitted an invalid refusal")
        raise ValueError(f"{refusal['refusal']}: {refusal['detail']}")
    try:
        raw_result = result_path.read_bytes()
    except OSError as exc:
        raise ValueError(f"E-C18-RESULT: cannot read confinement result: {exc}") from exc
    result, runtime_digest = validate_confinement_result(raw_result)
    result_command = cast(dict[str, object], result["command"])
    artifact: object | None = None
    if artifact_reader is not None:
        if artifact_relative is None:
            raise ValueError("artifact reader has no confined artifact path")
        artifact = artifact_reader(temporary / artifact_relative)
    return CommandObservation(
        subprocess.CompletedProcess(command, cast(int, result_command["exit_code"])),
        executable,
        artifact,
        hashlib.sha256(raw_result).hexdigest(),
        runtime_digest,
    )


def _command_resolution(
    root: Path,
    command: Sequence[str],
    provisioning: Provisioning | None,
) -> tuple[Resolution | None, bool]:
    """Resolve argv[0] exactly as both observation ceremonies require."""

    provisioned_resolver = (
        provisioning is not None and command[0] == provisioning.pins.resolver.name
    )
    preliminary: Resolution | None = None
    if provisioned_resolver:
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
    return preliminary, provisioned_resolver


def _approved_artifacts(
    root: Path,
    provisioning: Provisioning | None,
) -> tuple[WheelArtifact, ...]:
    """Refuse an unverified, unapproved, absent or corrupt dependency set."""

    if provisioning is None:
        return ()
    artifacts, depset = _selected_artifacts(provisioning)
    entries = Journal(resolve_within_repository(root, DEFAULT_JOURNAL)).entries()
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
        delta = _render_delta(recorded if isinstance(recorded, dict) else None, packages)
        raise ValueError(
            "refusing to run: this dependency set is not approved. "
            "The delta awaiting approval:\n"
            + "\n".join(delta)
            + "\nRun `ranex deps approve --approver <id>` to accept it"
        )
    verified_wheel_paths(artifacts, provisioning.store)
    return artifacts


def _execute_hermetically(
    root: Path,
    started_at: str,
    command: Sequence[str],
    provisioning: Provisioning | None,
    artifacts: tuple[WheelArtifact, ...],
    preliminary: Resolution | None,
    provisioned_resolver: bool,
    *,
    artifact_relative: Path | None = None,
    artifact_reader: Callable[[Path], object] | None = None,
    confinement: str | None = None,
) -> CommandObservation:
    """Run once inside the shared verified, offline, sealed execution boundary."""

    with materialise_subject(root, started_at, git) as materialisation:
        confinement_result_digest: str | None = None
        confinement_profile_digest: str | None = None
        confined_artifact: object | None = None
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

        descriptor = (
            verified_pinned_binary(
                provisioning.pins.resolver, provisioning.pins.resolver_sha256
            )
            if provisioned_resolver and provisioning is not None
            else os.open(executable, EXECUTABLE_OPEN_FLAGS)
        )
        try:
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

            observed = materialisation.tracked_paths
            untouched = stat_fingerprint(materialisation.tree, observed)
            environment = {
                "PATH": pinned_path_value(),
                "HOME": str(materialisation.home),
                "TMPDIR": str(materialisation.temporary),
                "LANG": "C.UTF-8",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_ATTR_NOSYSTEM": "1",
            }
            before_exec = None
            if provisioning is not None and deps_environment is not None:
                environment["PATH"] = (
                    f"{deps_environment / 'bin'}{os.pathsep}{environment['PATH']}"
                )
                environment.update(
                    {
                        "UV_PROJECT_ENVIRONMENT": str(deps_environment),
                        "VIRTUAL_ENV": str(deps_environment),
                        "UV_NO_SYNC": "1",
                        "UV_OFFLINE": "1",
                        "UV_NO_CONFIG": "1",
                        "UV_FROZEN": "1",
                        "UV_PYTHON_DOWNLOADS": "never",
                        "UV_CACHE_DIR": str(materialisation.temporary / "uv-cache"),
                    }
                )
                before_exec = _deny_network
            if confinement is not None:
                confined = _execute_confinement_session(
                    root,
                    materialisation,
                    command,
                    executable,
                    deps_environment,
                    artifact_relative=artifact_relative,
                    artifact_reader=artifact_reader,
                )
                completed = confined.completed
                confined_artifact = confined.artifact
                confinement_result_digest = confined.confinement_result_digest
                confinement_profile_digest = confined.confinement_profile_digest
            else:
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

        artifact: object | None = confined_artifact
        if artifact_reader is not None and confinement is None:
            if artifact_relative is None:
                raise ValueError("artifact reader has no confined artifact path")
            artifact = artifact_reader(materialisation.tree / artifact_relative)

        if head_commit(root) != started_at:
            raise ValueError(
                "refusing to record evidence: the command moved HEAD from "
                f"{started_at[:12]} during the run"
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
                f"file(s) while it ran — {', '.join(written)} — so the observed "
                "commit no longer describes the tree the command saw"
            )

        return CommandObservation(
            completed,
            executable,
            artifact,
            confinement_result_digest,
            confinement_profile_digest,
        )


def _execute_host_qualification(
    root: Path,
    started_at: str,
    command: Sequence[str],
    preliminary: Resolution | None,
    *,
    artifact_relative: Path,
    artifact_reader: Callable[[Path], object],
) -> CommandObservation:
    """Run qualification against the live host, never a subject materialisation."""

    resolution = preliminary or resolve_executable(command[0], root)
    executable = resolution.executable
    refuse_resolution_inside(
        resolution, command[0], root, "the governed repository being qualified"
    )
    descriptor = os.open(executable, EXECUTABLE_OPEN_FLAGS)
    try:
        identity = os.fstat(descriptor)
        if not stat.S_ISREG(identity.st_mode):
            raise ValueError(
                f"refusing to run {command[0]!r}: {executable} is not a regular file"
            )
        opened = path_behind(
            descriptor,
            f"cannot confirm which file {command[0]!r} opened, so it will not be run",
        )
        if opened != executable:
            raise ValueError(
                f"refusing to run {command[0]!r}: it resolved to {executable} and "
                f"the file actually opened is {opened}; the path changed while it was checked"
            )
        twin = same_file_inside(identity, root)
        if twin is not None:
            raise ValueError(
                f"refusing to run {command[0]!r}: {executable} is the same file as "
                f"{twin}, inside the governed repository being qualified"
            )

        environment = dict(os.environ)
        # ADR-031 propagation boundary: an observed command that sees a trace
        # variable can branch on it and break byte-invariance, so the ambient
        # copy strips every RANEX_TRACE* variable (sad path 13). The observed
        # command's own environment in the run path is a fixed dict and
        # already admits nothing ambient.
        for variable in TRACE_VARIABLES:
            environment.pop(variable, None)
        source_root = str(Path(__file__).resolve().parents[2])
        existing_pythonpath = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            source_root
            if not existing_pythonpath
            else f"{source_root}{os.pathsep}{existing_pythonpath}"
        )
        try:
            completed = subprocess.run(
                [str(executable), *command[1:]],
                executable=f"/proc/self/fd/{descriptor}",
                pass_fds=(descriptor,),
                cwd=root,
                check=False,
                env=environment,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise ValueError(f"cannot run host qualification {command[0]!r}: {exc}") from exc
    finally:
        os.close(descriptor)

    artifact: object | None = None
    if completed.returncode == 0:
        artifact_path = root / artifact_relative
        artifact = artifact_reader(artifact_path)
        artifact_path.unlink()
    if head_commit(root) != started_at:
        raise ValueError(
            "refusing to record evidence: host qualification moved HEAD from "
            f"{started_at[:12]} during the run"
        )
    return CommandObservation(completed, executable, artifact)


def _host_qualification_resolution(root: Path, command: Sequence[str]) -> Resolution:
    """Resolve the catalog's Python name to this running host interpreter."""

    if command[0] != "python":
        return resolve_executable(command[0], root)
    executable = Path(sys.executable).resolve()
    return Resolution(executable=executable, route=walked_route(executable))


def cmd_run(args: argparse.Namespace) -> int:
    """Run a command and record what was observed. Never judge it.

    Exits with the wrapped command's own exit code so `run && gate evaluate`
    composes. A failing command is honest evidence of failure, not a usage
    error. Exit 2 can therefore mean either a refusal to record, which writes
    nothing, or a wrapped command that exited 2 after its record was written.
    The exit code alone cannot distinguish those cases; inspect the evidence
    file to learn whether a record is present.
    """

    confinement = getattr(args, "confinement", None)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]

    descriptor: int | None = None
    try:
        governed_root = governed_repository_root()
        root = Path(args.repository).resolve() if confinement == "strict-local" else resolve_within_repository(
            governed_root, args.repository
        )
        if confinement != "strict-local" and root != governed_root:
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
        if confinement not in (None, "strict-local"):
            raise ValueError(
                f"unsupported confinement profile {confinement!r}; expected 'strict-local'"
            )

        # Captured once, and everything below is asked about this exact commit
        # rather than about `HEAD`, which is a name the observed party can move
        # between two questions. Taken before argv[0] resolution now, because
        # whether this subject provisions dependencies is also a question
        # about this exact commit.
        started_at = head_commit(root)
        provisioning = _provisioning_for(root, started_at, args.store)
        results_artifact: str | None = None
        qualification_report: str | None = None
        suite_manifest: dict[str, object] | None = None
        catalog_name = named_within_repository(root, args.gate_catalog)
        if committed_bytes(root, started_at, catalog_name) is not None:
            catalog_path = resolve_within_repository(root, args.gate_catalog)
            catalog_source = committed_trust_root(
                root,
                started_at,
                args.gate_catalog,
                catalog_path,
                "gate catalog",
            )
            selected_claim = claim_definition_for(catalog_source, args.gate, args.claim)
            if selected_claim is not None and selected_claim.results_artifact is not None:
                manifest_path = resolve_within_repository(root, args.suite_manifest)
                manifest_source = committed_trust_root(
                    root,
                    started_at,
                    args.suite_manifest,
                    manifest_path,
                    "suite manifest",
                )
                suite_manifest = load_manifest_bytes(manifest_source)
                results_artifact = selected_claim.results_artifact
            if selected_claim is not None:
                qualification_report = selected_claim.qualification_report

        # Bare and absolute names do not depend on the materialised cwd, so
        # resolve them before materialisation. This keeps the governed-root
        # route and inode controls live for absolute same-uid access, including
        # a committed symlink whose tree entry the materialiser also refuses.
        if qualification_report is not None:
            preliminary = _host_qualification_resolution(root, command)
            provisioned_resolver = False
        else:
            preliminary, provisioned_resolver = _command_resolution(
                root, command, provisioning
            )

        # Everything knowable without constructing the sample refuses before
        # the command runs. A test suite is expensive; discovering afterwards
        # that its record cannot be written honestly wastes all of it.
        private_key = private_signing_key(root)
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

        artifacts = (
            ()
            if qualification_report is not None
            else _approved_artifacts(root, provisioning)
        )
        carrier_path = results_artifact or qualification_report
        artifact_relative = Path(carrier_path) if carrier_path is not None else None
        artifact_reader: Callable[[Path], object] | None = None
        if results_artifact is not None:
            if suite_manifest is None:
                raise ValueError("suite-results claim has no loaded manifest")
            artifact_reader = lambda path: parse_results_artifact(path, suite_manifest)
        elif qualification_report is not None:
            artifact_reader = lambda path: json.loads(path.read_bytes())
        if qualification_report is not None:
            if artifact_relative is None or artifact_reader is None:
                raise ValueError("qualification claim has no report carrier")
            observation = _execute_host_qualification(
                root,
                started_at,
                command,
                preliminary,
                artifact_relative=artifact_relative,
                artifact_reader=artifact_reader,
            )
        else:
            observation = _execute_hermetically(
                root,
                started_at,
                command,
                provisioning,
                artifacts,
                preliminary,
                provisioned_resolver,
                artifact_relative=artifact_relative,
                artifact_reader=artifact_reader,
                confinement=confinement,
            )
        completed = observation.completed
        executable = observation.executable
        observed_suite_results = observation.artifact

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
            "suite_results": observed_suite_results,
            "confinement_result_digest": observation.confinement_result_digest,
            "confinement_profile_digest": observation.confinement_profile_digest,
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


def cmd_suite_freeze(args: argparse.Namespace) -> int:
    """Run a committed tree hermetically and freeze its junitxml ID set."""

    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        artifact = resolve_within_repository(root, args.artifact)
        artifact_relative = artifact.relative_to(root)
        output = resolve_within_repository(root, args.output)
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            raise ValueError("a freeze command is required after --")
        expected_skips: dict[str, str] = {}
        for declaration in args.expected_skip:
            test_id, separator, reason = declaration.partition("=")
            if not separator or not test_id or not reason.strip():
                raise ValueError(
                    "--expected-skip must be TEST_ID=REASON with a non-empty reason"
                )
            if test_id in expected_skips:
                raise ValueError(f"duplicate --expected-skip declaration for {test_id}")
            expected_skips[test_id] = reason
        started_at = head_commit(root)
        provisioning = _provisioning_for(root, started_at, args.store)
        preliminary, provisioned_resolver = _command_resolution(
            root, command, provisioning
        )
        dirty = uncommitted_paths(
            root,
            ignoring=(named_within_repository(root, args.output),),
        )
        if dirty:
            raise ValueError(
                "refusing to freeze against a dirty working tree; HEAD does not "
                f"describe: {', '.join(dirty)}"
            )
        artifacts = _approved_artifacts(root, provisioning)
        observation = _execute_hermetically(
            root,
            started_at,
            command,
            provisioning,
            artifacts,
            preliminary,
            provisioned_resolver,
            artifact_relative=artifact_relative,
            artifact_reader=read_results_artifact,
        )
        if not isinstance(observation.artifact, bytes):
            raise ValueError("freeze run produced no readable results artifact")
        manifest = freeze_manifest(
            observation.artifact,
            expected_skips=expected_skips,
        )
        completed = observation.completed
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(canonical_json_bytes(manifest))
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

    print(
        f"FROZEN  tests={len(cast(list[str], manifest['suite']))}  "
        f"expected_skips={len(cast(dict[str, str], manifest['expected_skips']))}  "
        f"run_exit={completed.returncode}  output={output}"
    )
    return EXIT_PASS


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
    # The whole shape, not just the entry. This repository commits no keyring,
    # so a first-time operator is CREATING the file, and the bare entry they
    # used to be handed parses as a document with no `producers` mapping —
    # the loader then refuses it, correctly, after telling them to write it.
    # Printing both lines is right either way: appending to an existing
    # keyring means taking the indented one, and that is said explicitly.
    print(
        f"       register the producer in the committed keyring "
        f"({DEFAULT_PRODUCERS}). It is one `producers` mapping — create the "
        "file with exactly this, or if it already exists add only the "
        "indented line:"
    )
    print("  producers:")
    print(f"    {args.producer}: {public_key}")
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
        default=DEFAULT_GATE_CATALOG,
        help="gate catalog path",
    )
    ev.add_argument(
        "--suite-manifest",
        default=DEFAULT_SUITE_MANIFEST,
        help="committed frozen suite manifest",
    )
    ev.add_argument(
        "--evidence",
        default="governance/evidence.json",
        help="evidence records path",
    )
    ev.add_argument(
        "--producers",
        default=DEFAULT_PRODUCERS,
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
        default=DEFAULT_PRODUCERS,
        help="committed keyring of producer public keys",
    )
    rn.add_argument("--gate", default="landing", help="gate containing the claim")
    rn.add_argument(
        "--gate-catalog",
        default=DEFAULT_GATE_CATALOG,
        help="committed gate catalog when the claim carries suite results",
    )
    rn.add_argument(
        "--suite-manifest",
        default=DEFAULT_SUITE_MANIFEST,
        help="committed frozen suite manifest",
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
        "--confinement",
        help="opt into the named qualified confinement profile",
    )
    rn.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to run, after --",
    )
    rn.set_defaults(func=cmd_run)

    suite = sub.add_parser("suite", help="frozen suite operations").add_subparsers(
        dest="action", required=True
    )
    freeze = suite.add_parser("freeze", help="freeze junitxml test IDs")
    freeze.add_argument("--repository", default=".", help="repository root")
    freeze.add_argument("--artifact", required=True, help="junitxml artifact path")
    freeze.add_argument(
        "--output",
        default=DEFAULT_SUITE_MANIFEST,
        help="canonical suite manifest output",
    )
    freeze.add_argument(
        "--store",
        default=default_store(),
        help="operator wheel store, outside the repository",
    )
    freeze.add_argument(
        "--expected-skip",
        action="append",
        default=[],
        help="operator declaration TEST_ID=REASON; repeat for each expected skip",
    )
    freeze.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="hermetic command to run, after --",
    )
    freeze.set_defaults(func=cmd_suite_freeze)

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
    judge.add_argument(
        "--suite-manifest",
        default=DEFAULT_SUITE_MANIFEST,
        help="suite manifest from the dispatch-time base tree",
    )
    judge.add_argument("--journal", required=True, help="external task journal")
    judge.set_defaults(func=cmd_task_judge)

    merge = task_actions.add_parser("merge", help="publish a judged task candidate")
    merge.add_argument("--task-id", required=True, help="task identifier")
    merge.add_argument("--target-ref", required=True, help="governed target ref")
    merge.add_argument("--candidate", required=True, help="candidate commit OID")
    merge.add_argument("--approval", required=True, help="signed approval JSON")
    merge.set_defaults(func=cmd_task_merge)

    delegate = task_actions.add_parser("delegate", help="execute and attest a task in a worktree")
    delegate.add_argument("--task-id", required=True, help="task identifier")
    delegate.add_argument("--target", required=True, help="external git repository")
    delegate.add_argument("--worktree", required=True, help="new external worktree")
    delegate.add_argument("--journal", required=True, help="external task journal")
    delegate.add_argument("--harness", required=True, help="harness executable")
    delegate.add_argument("--model", required=True, help="harness model identifier")
    delegate.add_argument("--prompt", required=True, help="delegation prompt")
    delegate.add_argument("--timeout", required=True, type=int, help="wall-clock bound")
    delegate.add_argument("--suite", required=True, help="suite command to run")
    delegate.add_argument("--gate", default="landing", help="dispatch-time gate")
    delegate.add_argument(
        "--claim", default="tests-executed", help="dispatch-time suite claim"
    )
    delegate.add_argument(
        "--gate-catalog",
        default=DEFAULT_GATE_CATALOG,
        help="gate catalog path in the dispatch base tree",
    )
    delegate.add_argument(
        "--suite-manifest",
        default=DEFAULT_SUITE_MANIFEST,
        help="suite manifest path in the dispatch base tree",
    )
    delegate.add_argument("--outcome", required=True, help="outcome file path")
    delegate.set_defaults(func=cmd_task_delegate)

    fanout = task_actions.add_parser(
        "fanout", help="dispatch multiple tasks through a bounded delegation pool"
    )
    fanout.add_argument("--tasks", required=True, help="JSONL file with task_id/prompt/worktree")
    fanout.add_argument("--target", required=True, help="external git repository")
    fanout.add_argument("--journal", required=True, help="external task journal")
    fanout.add_argument("--harness", required=True, help="harness executable")
    fanout.add_argument("--model", required=True, help="harness model identifier")
    fanout.add_argument("--timeout", required=True, type=int, help="per-task wall-clock bound")
    fanout.add_argument("--suite", required=True, help="suite command to run")
    fanout.add_argument("--gate", default="landing", help="dispatch-time gate")
    fanout.add_argument(
        "--claim", default="tests-executed", help="dispatch-time suite claim"
    )
    fanout.add_argument(
        "--gate-catalog",
        default=DEFAULT_GATE_CATALOG,
        help="gate catalog path in each dispatch base tree",
    )
    fanout.add_argument(
        "--suite-manifest",
        default=DEFAULT_SUITE_MANIFEST,
        help="suite manifest path in each dispatch base tree",
    )
    fanout.add_argument(
        "--outcome-dir",
        required=True,
        help="directory for per-task outcome files",
    )
    fanout.add_argument("--pool", required=True, type=int, help="max concurrent delegations")
    fanout.set_defaults(func=cmd_task_fanout)
    return parser


def _dispatch_stage(args: argparse.Namespace) -> tuple[str, str] | None:
    """The registry stage pair for the subcommand being dispatched, or None.

    ADR-031's one CLI stage boundary: `cli.<group>.start` / `cli.<group>.end`
    around subcommand dispatch, where `<group>` is the argparse dispatch group
    (`run`, `gate.evaluate`, …). A group outside the frozen registry emits
    nothing — adding a CLI group is a deliberate schema-contract edit, not a
    silent extra stage.
    """

    group = getattr(args, "group", None)
    if not isinstance(group, str) or not group:
        return None
    action = getattr(args, "action", None)
    name = f"{group}.{action}" if isinstance(action, str) and action else group
    begin, end = f"cli.{name}.start", f"cli.{name}.end"
    if begin not in trace_schema.STAGES or end not in trace_schema.STAGES:
        return None
    return begin, end


def _anchor_trace_admission_to_governed_root() -> None:
    """Anchor trace-target admission to the CLI's authoritative root (N2).

    ``governed_repository_root()`` resolves the checkout containing THIS
    CLI — independent of the caller's cwd — which is exactly the tree trace
    targets must never dirty. Emitter admission is lazy at first emission
    and judges against the caller's cwd until anchored, so a CLI invoked
    from OUTSIDE its checkout would admit a ``RANEX_TRACE`` target inside
    the checkout before the command even runs. Resolution needs no command
    context, so the anchor is set here, before the first stage emission;
    ``set_governed_root`` also drops any already-held conflicting target
    (one warning, fail closed). Off state: nothing runs — no extra
    subprocess, no behavior change. A trace problem never crashes the run:
    on any resolution failure the anchor is simply not set and admission
    keeps its cwd discovery fallback.
    """

    import ranex.observability as _observability
    from ranex.observability.emitter import set_governed_root

    if not _observability.TRACING_ENABLED:
        return
    try:
        set_governed_root(governed_repository_root())
    except Exception:  # noqa: BLE001 - never crash the run for a trace problem
        pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _anchor_trace_admission_to_governed_root()
    stages = _dispatch_stage(args)
    if stages is not None:
        stage_begin(stages[0])
    try:
        code = int(args.func(args))
    except BaseException:
        # Crash-paired end: an unmatched start is precisely the moment a
        # trace is most valuable (slice decision 4: exit:-1 marks the crash).
        if stages is not None:
            stage_end(stages[1], "exit:-1")
        raise
    if stages is not None:
        stage_end(stages[1], f"exit:{code}")
    return code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
