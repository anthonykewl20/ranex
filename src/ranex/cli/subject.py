"""Build an observation tree from commit bytes that prove their object names."""

from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


class SubjectError(Exception):
    """The subject commit cannot be materialised without guessing or substitution."""


GitRunner = Callable[..., subprocess.CompletedProcess]


@dataclass(frozen=True, slots=True)
class TreeEntry:
    mode: str
    object_type: str
    object_id: str
    path: str


@dataclass(frozen=True, slots=True)
class Materialisation:
    root: Path
    tree: Path
    home: Path
    temporary: Path
    tracked_paths: tuple[str, ...]


_SYSTEM_GIT_ISOLATION = {
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_ATTR_NOSYSTEM": "1",
}


def _tree_entries(
    repository_root: Path,
    ref: str,
    git: GitRunner,
) -> tuple[TreeEntry, ...]:
    result = git(
        repository_root,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        ref,
        text=False,
        overrides=_SYSTEM_GIT_ISOLATION,
    )
    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip()
        raise SubjectError(f"cannot read the tree for {ref!r}: {detail}")

    entries: list[TreeEntry] = []
    names: set[str] = set()
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        try:
            metadata, raw_path = raw.split(b"\t", 1)
            raw_mode, raw_type, raw_oid = metadata.split(b" ", 2)
            mode = raw_mode.decode("ascii")
            object_type = raw_type.decode("ascii")
            object_id = raw_oid.decode("ascii")
        except (UnicodeDecodeError, ValueError) as exc:
            raise SubjectError(f"malformed tree entry in {ref!r}: {raw!r}") from exc

        path = os.fsdecode(raw_path)
        parts = Path(path).parts
        if not path or Path(path).is_absolute() or any(p in ("", ".", "..") for p in parts):
            raise SubjectError(f"refusing unsafe path {path!r} in the tree for {ref!r}")
        if any(part == ".git" for part in parts):
            raise SubjectError(f"refusing unsafe path {path!r} in the tree for {ref!r}")
        if len(object_id) != 40 or any(c not in "0123456789abcdef" for c in object_id):
            raise SubjectError(
                f"unsupported object id {object_id!r} for {path!r} in {ref!r}"
            )
        if path in names:
            raise SubjectError(f"duplicate path {path!r} in the tree for {ref!r}")
        names.add(path)
        entries.append(TreeEntry(mode, object_type, object_id, path))
    return tuple(entries)


def _regular_blob(entry: TreeEntry) -> None:
    if entry.object_type != "blob" or entry.mode not in ("100644", "100755"):
        raise SubjectError(
            f"refusing unimplemented tree entry {entry.path!r}: "
            f"mode {entry.mode}, type {entry.object_type}"
        )


def _verified_blob(
    repository_root: Path,
    entry: TreeEntry,
    git: GitRunner,
) -> bytes:
    _regular_blob(entry)
    result = git(
        repository_root,
        "cat-file",
        "blob",
        entry.object_id,
        text=False,
        overrides=_SYSTEM_GIT_ISOLATION,
    )
    if result.returncode != 0:
        detail = os.fsdecode(result.stderr).strip()
        raise SubjectError(
            f"cannot read blob {entry.object_id} for {entry.path!r}: {detail}"
        )
    content = result.stdout
    actual = hashlib.sha1(
        b"blob " + str(len(content)).encode("ascii") + b"\0" + content
    ).hexdigest()
    if actual != entry.object_id:
        raise SubjectError(
            f"refusing substituted blob for {entry.path!r}: expected "
            f"{entry.object_id}, computed {actual} from the streamed bytes"
        )
    return content


def verified_blob_at_path(
    repository_root: Path,
    ref: str,
    path: str,
    git: GitRunner,
) -> bytes | None:
    """Return verified committed bytes for ``path``, or None when it is absent."""

    for entry in _tree_entries(repository_root, ref, git):
        if entry.path == path:
            return _verified_blob(repository_root, entry, git)
    return None


def _remove_materialisation(root: Path) -> None:
    try:
        # Pytest's on_rm_rf_error intentionally does not retry os.open: unlike
        # unlink and rmdir, it needs arguments beyond the path.  We take that
        # warning about callback contracts, but not pytest's choice to leave
        # the tree behind: this scratch materialisation must always be removed.
        #
        # A directory's parent permits changing that directory's mode, so this
        # top-down pass makes each child traversable and writable before
        # os.walk descends into it.  Plain rmtree then has no version-specific
        # onerror/onexc callback contract to depend on.
        root.chmod(root.stat().st_mode | stat.S_IRWXU)
        for parent, directories, _files in os.walk(root, topdown=True):
            for directory in directories:
                path = Path(parent, directory)
                path.chmod(path.stat().st_mode | stat.S_IRWXU)
        shutil.rmtree(root)
    # This function runs in a finally block, where anything that escapes
    # replaces the refusal already travelling to the operator — which is the
    # defect this whole function was rewritten for. So the catch is deliberately
    # wider than OSError: the bug that reopened this slice was a TypeError.
    #
    # `Exception`, not `BaseException`. The caller's finally discards a
    # SubjectError when the body did not complete, so converting KeyboardInterrupt
    # here would swallow a Ctrl-C entirely. An interrupt replacing the refusal is
    # correct — the operator pressed the key and knows why it stopped.
    except Exception as exc:
        raise SubjectError(f"cannot remove materialisation at {root}: {exc}") from exc


def _materialisation_root(repository_root: Path) -> Path:
    """Create scratch outside the subject without consulting ambient ``TMPDIR``."""

    for base in (Path("/tmp"), Path("/var/tmp")):
        if not base.is_dir():
            continue
        try:
            root = Path(tempfile.mkdtemp(prefix="ranex-subject-", dir=base)).resolve()
        except OSError:
            continue
        if root != repository_root and repository_root not in root.parents:
            return root
        _remove_materialisation(root)
    raise SubjectError(
        f"cannot create a materialisation outside the governed repository at "
        f"{repository_root}"
    )


_CONSTRUCTION_ENVIRONMENT = {
    **_SYSTEM_GIT_ISOLATION,
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "Ranex Subject",
    "GIT_AUTHOR_EMAIL": "subject@ranex.invalid",
    "GIT_AUTHOR_DATE": "@0 +0000",
    "GIT_COMMITTER_NAME": "Ranex Subject",
    "GIT_COMMITTER_EMAIL": "subject@ranex.invalid",
    "GIT_COMMITTER_DATE": "@0 +0000",
}


def _construct_repository(
    repository_root: Path,
    ref: str,
    tree: Path,
    git: GitRunner,
) -> None:
    for operation, arguments in (
        (
            "init",
            ("-c", "init.defaultBranch=ranex-subject", "-c", "core.logAllRefUpdates=false", "init", "--template="),
        ),
        ("add", ("-c", "core.logAllRefUpdates=false", "add", "--all", "--force")),
        (
            "commit",
            ("-c", "commit.gpgsign=false", "-c", "core.logAllRefUpdates=false", "commit", "--no-verify", "-m", "ranex subject"),
        ),
    ):
        result = git(tree, *arguments, overrides=_CONSTRUCTION_ENVIRONMENT)
        if result.returncode != 0:
            detail = result.stderr.strip()
            raise SubjectError(f"cannot {operation} materialised repository: {detail}")

    sample_tree = git(
        tree, "rev-parse", "HEAD^{tree}", overrides=_CONSTRUCTION_ENVIRONMENT
    )
    governed_tree = git(
        repository_root, "rev-parse", f"{ref}^{{tree}}", overrides=_CONSTRUCTION_ENVIRONMENT
    )
    if sample_tree.returncode != 0 or governed_tree.returncode != 0:
        detail = (sample_tree.stderr if sample_tree.returncode else governed_tree.stderr).strip()
        raise SubjectError(f"cannot compare materialised tree for {ref!r}: {detail}")
    if sample_tree.stdout.strip() != governed_tree.stdout.strip():
        raise SubjectError(f"refusing materialised tree that does not match {ref!r}")


@contextmanager
def materialise_subject(
    repository_root: Path,
    ref: str,
    git: GitRunner,
) -> Iterator[Materialisation]:
    """Yield a fresh verified tree and remove its whole scratch root afterwards."""

    root = _materialisation_root(repository_root)
    tree = root / "tree"
    home = root / "home"
    temporary = root / "tmp"
    # Set only when the body AND the caller's `with` block both finished. Any
    # other exit means something is already propagating and a cleanup failure
    # must not replace it. Deliberately a local flag rather than
    # `sys.exc_info()`: that reports whatever is being handled anywhere up the
    # stack, so one caller inside an `except` would make the happy path look
    # like a failure and swallow a genuine cleanup error.
    completed = False
    try:
        tree.mkdir()
        entries = _tree_entries(repository_root, ref, git)
        for entry in entries:
            content = _verified_blob(repository_root, entry, git)
            destination = tree / entry.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
            destination.chmod(0o755 if entry.mode == "100755" else 0o644)
        _construct_repository(repository_root, ref, tree, git)
        home.mkdir(mode=0o700)
        temporary.mkdir(mode=0o700)
        yield Materialisation(
            root=root,
            tree=tree,
            home=home,
            temporary=temporary,
            tracked_paths=tuple(entry.path for entry in entries),
        )
        completed = True
    except SubjectError:
        raise
    except OSError as exc:
        raise SubjectError(f"cannot materialise {ref!r}: {exc}") from exc
    finally:
        # An exception raised in `finally` REPLACES the one already propagating,
        # leaving the original reachable only as `__context__` — which nothing
        # prints. A failed rmtree would therefore report "cannot remove
        # materialisation" for what was actually a substituted blob, sending the
        # operator to look at their disk instead of their object store. Cleanup
        # is noise; the refusal that fired is the finding, and it wins.
        #
        # The tree is always removed either way. Only the *reporting* of a
        # cleanup failure is suppressed, and only while something better is
        # already on its way to the operator.
        try:
            _remove_materialisation(root)
        except SubjectError:
            if completed:
                raise
