"""The trace emitter (ADR-031, SLICE-054).

Targets come from two independent env variables, ``RANEX_TRACE`` and
``RANEX_TRACE_EVENT``, each read exactly once at import (in ``__init__.py``).
Grammar, a strict subset of git trace2's (``af_unix:`` refused):

    unset/empty/0/false -> off     1/true -> stderr
    single digit 2-9    -> that already-open fd
    absolute file path  -> append  absolute dir -> one file per process,
                                        named by the last SID component

Relative paths, ``af_unix:`` forms, and unknown values are refused loudly —
one line on stderr naming the variable plus a shape descriptor (length +
first 8 hex of SHA-256), never the bytes — and tracing stays off for that
variable; the governed run proceeds. A well-formed absolute target failing
admission is refused naming the full path (issue #34 sad path 2).

File and directory targets are admitted lazily at first emission, before the
first write, opened once (``O_NOFOLLOW``; fstat on the opened descriptor) and
only the held descriptor is ever written — the path is never re-resolved, so
a later symlink swap or rename cannot redirect a write. Admission refuses a
target that sits under the governed repository root of the emitter's cwd,
that is a symlink, that carries other names (``st_nlink > 1`` — a hard link
is a second name for one file, so a hard link to governed bytes is the
governed bytes by another route), or whose device+inode aliases a file inside
that root (a bind mount is also a second name). Descriptors the emitter
opens are non-inheritable (Python's PEP 446 default), so no trace fd crosses
exec.

File and directory targets carry a byte cap with one max-line of reserved
capacity for the final refusal event: the next event that would exceed
cap-minus-reserved consumes the reserve with a ``cap_exceeded`` refusal and
the target stops — refusal, not rotation. A target whose remaining capacity
cannot fit even that refusal line is refused at admission (setup refusal,
nothing written). stderr and fd targets are operator-owned streams and carry
no cap. Writes are single-call best-effort: on failure the target is
disabled with one warning and the run proceeds; the emitter never blocks,
retries, or raises for a trace problem.
"""

from __future__ import annotations

import os
import stat
import time
from pathlib import Path
from typing import cast

import ranex.observability.schema as schema
from ranex.observability.redaction import screen_event

WARNING_PREFIX = "ranex-trace:"

# Refusal markers returned by _Target.write_line.
_WRITTEN = "written"
_CAP = "cap"
_FAILED = "failed"
_STOPPED = "stopped"

# Bound on the governed-root aliasing walk (files stat-ed, .git skipped).
# Past the bound the walk cannot prove safety, so the target is refused —
# fail closed rather than admit on incomplete evidence.
_WALK_CEILING = 50_000


def _warn(message: str) -> None:
    """One operator-facing line, unconditional, independent of any target."""

    line = f"{WARNING_PREFIX} {message}\n"
    try:
        os.write(2, line.encode("utf-8", "replace"))
    except OSError:
        pass  # never crash the governed run for a trace problem


def parse_target(value: str | None) -> tuple[str, object]:
    """Classify one variable's value. Never echoes the value back.

    Returns ``(kind, operand)`` with kind one of ``off``, ``stderr``, ``fd``,
    ``file``, ``dir``, ``invalid``. The operand is the fd number for ``fd``
    and the path for ``file``/``dir``.
    """

    if value is None or value == "" or value in ("0", "false"):
        return "off", None
    if value in ("1", "true"):
        return "stderr", None
    if len(value) == 1 and value in "23456789":
        return "fd", int(value)
    if value.startswith("/"):
        # Absolute path: an existing directory (symlinks resolved by isdir)
        # is a dir target — admission re-checks with lstat; anything else is
        # a file target, created at admission. O_NOFOLLOW refuses a symlinked
        # final component either way.
        return "dir" if os.path.isdir(value) else "file", Path(value)
    # Relative paths, af_unix:* forms, and everything unknown: case (b),
    # shape descriptor only — these values may carry attacker material.
    return "invalid", None


def _cwd_governed_root() -> Path | None:
    """The governed repository root of the emitter's cwd, or None.

    Walks up from the working directory for a ``.git`` entry — the tree a
    trace file would dirty. Outside any git tree (probes, scratch runs) there
    is nothing to protect and the check is skipped.
    """

    try:
        current = Path.cwd()
        for candidate in (current, *current.parents):
            if (candidate / ".git").exists():
                return candidate
    except OSError:
        return None
    return None


# ADR-031 anchor seam (D4): the confinement-session child runs with a cwd
# that resolves to no governed repository (a disposable session directory),
# yet its session tree IS one — sad path 12 (a target inside the governed
# repository root is refused before the first write) must apply there too.
# The child anchors admission to the session's governed root through
# ``set_governed_root`` before its first emission; the anchor takes
# precedence over cwd resolution. The observable is frozen by
# tests/unit/test_observability.py (refuse inside the anchor, admit under no
# root — never over-refuse); the mechanism behind the seam is otherwise
# implementer-free.
_ANCHORED_GOVERNED_ROOT: Path | None = None

# Live emitters of this process (remediation N2): admission is lazy at
# first emission, and the CLI's authoritative governed root resolves only
# at the dispatch boundary — possibly AFTER a target was already admitted
# against the caller's cwd. Anchoring therefore re-checks every held
# target; each emitter registers itself here so the module-level seam can
# reach it. One emitter per process; the list exists only because the seam
# is a module function while the targets are instance state.
_LIVE_EMITTERS: list[Emitter] = []


def set_governed_root(path: Path | str | None) -> None:
    """Anchor governed-root admission to ``path``, or clear the anchor with None.

    Setting the anchor RE-CHECKS every admitted/held target and DROPS any
    that sits under, or aliases, the newly anchored root (N2): one warning
    each — a well-formed target failing the check is named in full, case
    (a) — and fail closed when non-aliasing cannot be proven. Targets
    admitted later are judged against the anchor directly.
    """

    global _ANCHORED_GOVERNED_ROOT
    if path is None:
        _ANCHORED_GOVERNED_ROOT = None
        return
    anchored = Path(path)
    if not anchored.is_absolute():
        raise ValueError("the governed-root anchor must be an absolute path")
    _ANCHORED_GOVERNED_ROOT = anchored
    for emitter in list(_LIVE_EMITTERS):
        emitter.recheck_against_anchored_root(anchored)


def _admission_root() -> Path | None:
    """The governed root admission judges against: the explicit anchor, else cwd.

    The aliasing walk (device+inode) applies to whichever root this returns,
    so an anchored child gets the full sad-path-12 admission ceremony —
    under-root refusal included — exactly as a cwd-discovered root would.
    """

    if _ANCHORED_GOVERNED_ROOT is not None:
        return _ANCHORED_GOVERNED_ROOT
    return _cwd_governed_root()


def _under(path: Path, root: Path) -> bool:
    try:
        resolved = Path(os.path.realpath(path))
        return resolved == root or root in resolved.parents
    except OSError:
        return False


def _governed_file_inodes(root: Path) -> frozenset[tuple[int, int]] | None:
    """(st_dev, st_ino) of every file under the governed root, or None.

    None means the walk exceeded its bound, which the caller treats as a
    refusal — safety could not be proven. ``.git`` metadata is skipped: the
    governed surface is the worktree (journal and evidence paths always sit
    inside it; absolute path arguments are refused by the CLI).
    """

    inodes: set[tuple[int, int]] = set()
    try:
        for directory, subdirectories, filenames in os.walk(root, followlinks=False):
            subdirectories[:] = [name for name in subdirectories if name != ".git"]
            for name in filenames:
                try:
                    info = os.stat(Path(directory) / name, follow_symlinks=False)
                except OSError:
                    continue
                if stat.S_ISREG(info.st_mode):
                    inodes.add((info.st_dev, info.st_ino))
                if len(inodes) > _WALK_CEILING:
                    return None
    except OSError:
        return None
    return frozenset(inodes)


class _Target:
    """A single-call-per-line sink with per-target failure accounting."""

    variable: str = ""
    capped = False  # only file/dir targets

    def write_line(self, line: bytes) -> str:  # pragma: no cover - interface
        raise NotImplementedError

    def write_final(self, line: bytes) -> bool:
        """Consume the reserved capacity with the final refusal line."""

        return False

    def close(self) -> None:
        return None

    def describe(self) -> str:
        return self.variable


class _StderrTarget(_Target):
    def __init__(self, variable: str) -> None:
        self.variable = variable

    def write_line(self, line: bytes) -> str:
        try:
            os.write(2, line)
            return _WRITTEN
        except OSError:
            return _FAILED

    def describe(self) -> str:
        return f"{self.variable} (stderr)"


class _FdTarget(_Target):
    """An already-open fd supplied by the operator (single digit 2-9).

    A socket fd is refused outright: a socket is an exfiltration channel out
    of a confined tree (ADR-031 refuses ``af_unix:`` target values for the
    same reason; admitting an already-open socket through the fd form would
    undo that narrowing). Regular files, character devices, and pipes are the
    admissible streams.

    At admission the fd is set non-blocking and non-inheritable. Non-blocking
    is the never-block guarantee (ADR-031 sad path 3): a full or stalled
    stream raises instead of parking the governed run — the write failure
    path (one warning, target disabled, never a retry) then applies to
    ``BlockingIOError``/``EAGAIN``/``EWOULDBLOCK`` exactly as to any other
    ``OSError``. Non-inheritable is defense-in-depth for the CLOEXEC posture:
    no trace fd crosses exec even if a later spawn forgets ``close_fds``.
    """

    def __init__(self, variable: str, fd: int, root: Path | None) -> None:
        self.variable = variable
        self.fd = fd
        self.disabled = False
        try:
            info = os.fstat(fd)
            if stat.S_ISSOCK(info.st_mode):
                raise ValueError(
                    f"fd {fd} is a socket; a socket is an exfiltration channel "
                    "and is refused as a trace target"
                )
            if not (
                stat.S_ISREG(info.st_mode)
                or stat.S_ISCHR(info.st_mode)
                or stat.S_ISFIFO(info.st_mode)
            ):
                raise ValueError("not a usable stream")
            if stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
                raise ValueError(
                    f"fd {fd} names a file with {info.st_nlink} links; a second "
                    "name for one file is a second file"
                )
            # Fail closed on aliasing with the governed tree: resolve
            # /proc/self/fd and refuse a target pointing into it.
            link = Path(os.readlink(f"/proc/self/fd/{fd}"))
            if link.is_absolute() and root is not None and _under(link, root):
                raise ValueError(f"fd {fd} resolves into the governed repository root {root}")
            if root is not None:
                inodes = _governed_file_inodes(root)
                if inodes is None:
                    raise ValueError(
                        f"fd {fd}: the governed tree {root} is too large to prove "
                        "non-aliasing; refused fail-closed"
                    )
                if (info.st_dev, info.st_ino) in inodes:
                    raise ValueError(
                        f"fd {fd} aliases a file inside {root} by device and inode"
                    )
            # Admission is the one moment the emitter may adjust the stream:
            # never block the run, never leak the fd across exec.
            os.set_blocking(fd, False)
            os.set_inheritable(fd, False)
        except OSError as exc:
            raise ValueError(f"fd {fd} cannot be inspected ({exc.strerror}); fail closed") from exc

    def write_line(self, line: bytes) -> str:
        if self.disabled:
            return _STOPPED
        try:
            os.write(self.fd, line)
            return _WRITTEN
        except OSError:
            # BlockingIOError (EAGAIN/EWOULDBLOCK on the full, non-blocking
            # stream) lands here like any write failure: disable, one warning
            # in the dispatcher, never a retry, never a block.
            self.disabled = True
            return _FAILED

    def describe(self) -> str:
        return f"fd {self.fd}"


class _FileTarget(_Target):
    """Opened once at admission; only the held descriptor is ever written."""

    capped = True

    def __init__(self, variable: str, path: Path, root: Path | None) -> None:
        self.variable = variable
        if schema.TRACE_BYTE_CAP < schema.MAX_LINE_LENGTH:
            raise ValueError(
                f"trace byte cap {schema.TRACE_BYTE_CAP} is smaller than one max "
                f"line ({schema.MAX_LINE_LENGTH}); refused"
            )
        if root is not None and _under(path, root):
            raise ValueError(
                f"trace target {path} sits under the governed repository root "
                f"{root} and would dirty the tree it observes"
            )
        try:
            # O_NONBLOCK (remediation N3): admission of an absolute path must
            # never park the run. On a FIFO with no reader, plain O_WRONLY
            # blocks until a reader appears; with O_NONBLOCK the open instead
            # fails immediately with ENXIO (or, with a reader attached,
            # succeeds and the S_ISREG check below refuses it). Regular files
            # are unaffected by O_NONBLOCK, so nothing else changes.
            fd = os.open(
                path,
                os.O_WRONLY
                | os.O_CREAT
                | os.O_APPEND
                | os.O_NOFOLLOW
                | os.O_NONBLOCK,
                0o600,
            )
        except OSError as exc:
            raise ValueError(f"trace target {path} cannot be opened: {exc.strerror}") from exc
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            # A FIFO, device, or socket reached through the path form: not a
            # regular file, refused — one warning in the dispatcher, target
            # disabled, never a block, never a crash (N3).
            os.close(fd)
            raise ValueError(f"trace target {path} is not a regular file")
        if info.st_nlink != 1:
            os.close(fd)
            raise ValueError(
                f"trace target {path} has {info.st_nlink} links; a hard link is a "
                "second name for one file, and the governed bytes by another route"
            )
        if root is not None:
            inodes = _governed_file_inodes(root)
            if inodes is None:
                os.close(fd)
                raise ValueError(
                    f"trace target {path}: the governed tree {root} is too large "
                    "to prove non-aliasing; refused fail-closed"
                )
            if (info.st_dev, info.st_ino) in inodes:
                os.close(fd)
                raise ValueError(
                    f"trace target {path} aliases a file inside {root} by device "
                    "and inode"
                )
        self.path = path
        self.fd = fd
        self.written = info.st_size  # append semantics: count what is there
        self.stopped = False
        self.disabled = False

    def _fits(self, line: bytes) -> bool:
        return self.written + len(line) <= schema.TRACE_BYTE_CAP - schema.MAX_LINE_LENGTH

    def write_line(self, line: bytes) -> str:
        if self.stopped or self.disabled:
            return _STOPPED
        if not self._fits(line):
            return _CAP
        try:
            os.write(self.fd, line)
            self.written += len(line)
            return _WRITTEN
        except OSError:
            self.disabled = True
            return _FAILED

    def write_final(self, line: bytes) -> bool:
        """The reserved refusal line: allowed up to the full cap, then stop."""

        self.stopped = True
        if self.disabled or self.written + len(line) > schema.TRACE_BYTE_CAP:
            return False
        try:
            os.write(self.fd, line)
            self.written += len(line)
            return True
        except OSError:
            return False

    def close(self) -> None:
        descriptor = getattr(self, "fd", None)
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
            self.fd = None  # type: ignore[assignment]


class _DirTarget(_FileTarget):
    """One file per process, named by the last SID component (git trace2).

    The directory is pinned by descriptor (remediation N4): opened once
    with ``O_DIRECTORY|O_NOFOLLOW``, and the per-process file is created
    RELATIVE to that pinned descriptor (``dir_fd=``). The admitted path is
    never re-walked, so swapping the directory entry for a symlink after
    the pin cannot redirect the created file into a location admission
    never checked — the file lands under the admitted directory's
    filesystem identity (device and inode), rename or no rename.
    """

    def __init__(self, variable: str, directory: Path, component: str, root: Path | None) -> None:
        self.variable = variable
        if schema.TRACE_BYTE_CAP < schema.MAX_LINE_LENGTH:
            raise ValueError(
                f"trace byte cap {schema.TRACE_BYTE_CAP} is smaller than one max "
                f"line ({schema.MAX_LINE_LENGTH}); refused"
            )
        if root is not None and _under(directory, root):
            raise ValueError(
                f"trace directory {directory} sits under the governed repository "
                f"root {root} and would dirty the tree it observes"
            )
        # Resolve the directory exactly once, on the opened descriptor:
        # O_NOFOLLOW refuses a symlinked final component, O_DIRECTORY plus
        # the fstat below pins a real directory.
        try:
            dirfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise ValueError(
                f"trace directory {directory} cannot be opened: {exc.strerror}"
            ) from exc
        try:
            info = os.fstat(dirfd)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError(f"trace directory {directory} is not a real directory")
            # O_EXCL with bounded .N retries (the git precedent); O_NONBLOCK
            # so even a pre-created FIFO entry cannot park the admission
            # open (N3's rule on the per-process file too). Creation is
            # RELATIVE to the pinned dirfd — never a re-walk of the path.
            last: OSError | None = None
            fd: int | None = None
            chosen: str | None = None
            for name in [component] + [f"{component}.{n}" for n in range(1, 11)]:
                try:
                    fd = os.open(
                        name,
                        os.O_WRONLY
                        | os.O_CREAT
                        | os.O_EXCL
                        | os.O_APPEND
                        | os.O_NOFOLLOW
                        | os.O_NONBLOCK,
                        0o600,
                        dir_fd=dirfd,
                    )
                    chosen = name
                    break
                except OSError as exc:
                    last = exc
            if fd is None or chosen is None:
                raise ValueError(
                    f"trace directory {directory} admits no per-process file: "
                    f"{last.strerror if last else 'unknown error'}"
                )
            try:
                # The pinned descriptor's stat carries the existing
                # alias/governed-root validation: the created child must be
                # a regular file and must not alias any file inside the
                # governed tree (a hard link planted under the directory
                # would be the governed bytes by another route).
                child = os.fstat(fd)
                if not stat.S_ISREG(child.st_mode):
                    raise ValueError(
                        f"trace directory {directory} per-process entry "
                        f"{chosen!r} is not a regular file"
                    )
                if root is not None:
                    inodes = _governed_file_inodes(root)
                    if inodes is None:
                        raise ValueError(
                            f"trace directory {directory}: the governed tree "
                            f"{root} is too large to prove non-aliasing; "
                            "refused fail-closed"
                        )
                    if (child.st_dev, child.st_ino) in inodes:
                        raise ValueError(
                            f"trace directory {directory} per-process file "
                            f"aliases a file inside {root} by device and inode"
                        )
            except BaseException:
                os.close(fd)
                raise
            # The pin has served its purpose: the child descriptor is held,
            # so the directory descriptor is released, not leaked.
            try:
                os.close(dirfd)
            except OSError:  # pragma: no cover - close of a valid fd
                pass
        except BaseException:
            os.close(dirfd)
            raise
        self.path = directory / chosen
        self.fd = fd
        self.written = 0
        self.stopped = False
        self.disabled = False


class Emitter:
    """One per process. Admits targets lazily; emits canonical JSONL lines."""

    def __init__(
        self,
        enabled: dict[str, str],
        sid: str,
        malformed_parent_note: str | None,
    ) -> None:
        self.sid = sid
        self._malformed_parent_note = malformed_parent_note
        self._targets: list[_Target] = []
        self._admitted = False
        self._stage_started: dict[str, int] = {}
        self._plans: list[tuple[str, str, object]] = []
        for variable, value in enabled.items():
            kind, operand = parse_target(value)
            if kind in ("off", "invalid"):  # invalid already warned at import
                continue
            self._plans.append((variable, kind, operand))
        _LIVE_EMITTERS.append(self)

    # -- late-anchor re-check (N2) ----------------------------------------

    def recheck_against_anchored_root(self, root: Path) -> None:
        """Drop every held target under or aliasing the anchored root.

        Admission may already have happened against the caller's cwd when
        the authoritative anchor appears (the CLI resolves its governed
        root at the dispatch boundary); each conflicting target is dropped
        with exactly one warning and its descriptor closed — no further
        writes, never a warning again, fail closed.
        """

        if not self._admitted:
            # Nothing held yet; admission judges against the anchor directly.
            return
        surviving: list[_Target] = []
        for target in self._targets:
            reason = self._anchored_root_conflict(target, root)
            if reason is None:
                surviving.append(target)
                continue
            _warn(
                f"{target.variable}: {reason}; target dropped, tracing stays "
                "off for this variable"
            )
            target.close()
        self._targets = surviving

    def _anchored_root_conflict(self, target: _Target, root: Path) -> str | None:
        """The case-(a) drop reason for a held target against ``root``, or None."""

        if isinstance(target, _StderrTarget):
            return None  # an operator-owned stream has no location to dirty
        if isinstance(target, _FdTarget):
            if target.disabled:
                return None  # already dead; its one warning has been spent
            try:
                info = os.fstat(target.fd)
                link = Path(os.readlink(f"/proc/self/fd/{target.fd}"))
            except OSError:
                return (
                    f"fd {target.fd} can no longer be inspected against the "
                    f"governed repository root {root}; dropped fail-closed"
                )
            if link.is_absolute() and _under(link, root):
                return f"fd {target.fd} resolves into the governed repository root {root}"
            return self._alias_conflict(info, root, name=f"fd {target.fd}")
        # stderr and fd targets returned above; what remains is a file or
        # dir target, both of which hold the admitted path and open fd.
        held = cast(_FileTarget, target)
        path = held.path  # file and dir targets hold the admitted path
        if _under(path, root):
            return (
                f"trace target {path} sits under the governed repository root "
                f"{root} and would dirty the tree it observes"
            )
        try:
            info = os.fstat(held.fd)
        except OSError:
            return (
                f"trace target {path} can no longer be inspected against the "
                f"governed repository root {root}; dropped fail-closed"
            )
        return self._alias_conflict(info, root, name=str(path))

    @staticmethod
    def _alias_conflict(info: os.stat_result, root: Path, *, name: str) -> str | None:
        inodes = _governed_file_inodes(root)
        if inodes is None:
            return (
                f"trace target {name}: the governed tree {root} is too large "
                "to prove non-aliasing; dropped fail-closed"
            )
        if (info.st_dev, info.st_ino) in inodes:
            return (
                f"trace target {name} aliases a file inside {root} by device "
                "and inode"
            )
        return None

    # -- admission -------------------------------------------------------

    def _admit(self) -> None:
        """Lazily, before the first write: open targets, write version first."""

        self._admitted = True
        root = _admission_root()
        admitted: list[_Target] = []
        failures: list[str] = []
        for variable, kind, operand in self._plans:
            target: _Target | None = None
            try:
                if kind == "stderr":
                    target = _StderrTarget(variable)
                elif kind == "fd":
                    target = _FdTarget(variable, cast(int, operand), root)
                elif kind == "file":
                    target = _FileTarget(variable, operand, root)  # type: ignore[arg-type]
                elif kind == "dir":
                    target = _DirTarget(
                        variable, operand, self.sid.rsplit("/", 1)[-1], root  # type: ignore[arg-type]
                    )
            except ValueError as exc:
                # Case (a): a well-formed target failing admission is named
                # in full (issue #34 sad path 2). Never a crash.
                _warn(f"{variable}: {exc}; tracing stays off for this variable")
                failures.append(variable)
                target = None
            if target is not None:
                admitted.append(target)
        self._targets = admitted
        # The version event is the first write on each admitted target,
        # through the same cap-aware dispatch as every later event — a target
        # whose remaining capacity cannot fit it refuses at setup instead.
        if self._targets:
            self._dispatch(self._version_payload(), internal=True)
        for _variable in failures:
            self._dispatch(
                {
                    "event": "refusal",
                    "level": "warn",
                    "module": "observability",
                    "stage": "observability.emission",
                    "code": "target_admission_failed",
                }
            )
        # A malformed parent SID is noted once, on the admitted targets.
        if self._malformed_parent_note is not None:
            note, self._malformed_parent_note = self._malformed_parent_note, None
            self._dispatch(
                {
                    "event": "note",
                    "level": "info",
                    "module": "observability",
                    "stage": "observability.note",
                    "code": note,
                }
            )

    def variable_admitted(self, variable: str) -> bool:
        """Whether ``variable``'s target is currently held, forcing admission first.

        ADR-031's controller seam (D4): the seam must only ever propagate
        variables whose targets this process actually holds, so admission is
        forced here if it has not happened yet and the answer reflects the
        live target list — a target refused at admission, or since disabled
        by write failure or the cap, is not held and does not propagate.
        """

        if not self._admitted:
            self._admit()
        return any(target.variable == variable for target in self._targets)

    def _version_payload(self) -> dict:
        """The literal-built version event (bypasses screening by construction)."""

        return {
            "event": "version",
            "level": None,
            "module": None,
            "stage": None,
            "subject_digest": None,
            "duration_us": None,
            "hierarchy": None,
            "child_id": None,
            "code": None,
            "evt": schema.SCHEMA_NUMBER,
            "exe": schema.ranex_version(),
        }

    # -- rendering and dispatch -------------------------------------------

    def _render(self, payload: dict) -> bytes:
        import json

        ordered: dict = {}
        for field in schema.FIELDS:
            if field == "sid":
                ordered["sid"] = self.sid
            elif field == "time":
                ordered["time"] = schema.now_truncated_ms(time.time())
            else:
                ordered[field] = payload.get(field)
        if payload.get("event") == "version":
            ordered["evt"] = payload.get("evt", schema.SCHEMA_NUMBER)
            ordered["exe"] = payload.get("exe")
            if ordered["exe"] is None:
                ordered["exe"] = schema.ranex_version()
        return (
            json.dumps(ordered, separators=(",", ":"), ensure_ascii=True).encode("utf-8") + b"\n"
        )

    def _dispatch(self, payload: dict, internal: bool = False) -> None:
        """Serialize one already-screened payload and write it everywhere."""

        if not self._targets:
            return
        line = self._render(payload)
        if len(line) > schema.MAX_LINE_LENGTH:
            # Oversized payloads are refused, never truncated, never written.
            if not internal:
                self._dispatch(
                    {
                        "event": "refusal",
                        "level": "warn",
                        "module": "observability",
                        "stage": "observability.emission",
                        "code": f"oversized_event:len={len(line)}",
                    },
                    internal=True,
                )
            else:  # pragma: no cover - the literal refusals are all small
                _warn("trace refusal line itself exceeded the max line length")
            return
        surviving: list[_Target] = []
        for target in self._targets:
            result = target.write_line(line)
            if result == _CAP:
                # The reserve exists for exactly one final refusal event;
                # after it the target stops — refusal, not rotation.
                refusal = self._render(
                    {
                        "event": "refusal",
                        "level": "warn",
                        "module": "observability",
                        "stage": "observability.emission",
                        "code": "cap_exceeded",
                    }
                )
                if target.write_final(refusal):
                    _warn(
                        f"{target.variable}: trace target reached its byte cap "
                        f"and stopped (refusal, not rotation)"
                    )
                else:
                    _warn(
                        f"{target.variable}: trace target {getattr(target, 'path', target.describe())} "
                        f"has no capacity for the final cap refusal; tracing stays "
                        "off for this variable"
                    )
                target.close()
            elif result == _FAILED:
                _warn(
                    f"{target.variable}: trace write failed on {target.describe()}; "
                    "target disabled, the run proceeds"
                )
                target.close()
            else:
                surviving.append(target)
        self._targets = surviving

    # -- public surface ----------------------------------------------------

    def emit_raw(self, raw: object) -> None:
        """The screened emission surface (also the rogue-probe entry point)."""

        try:
            if not self._admitted:
                self._admit()
            accepted, refusals = screen_event(raw)
            if accepted is not None:
                self._dispatch(accepted)
            for refusal in refusals:
                self._dispatch(refusal)
        except Exception:  # noqa: BLE001 - the emitter never crashes the run
            _warn("trace emission problem suppressed; the run proceeds")

    def stage_begin(self, stage: str) -> None:
        if stage not in schema.STAGES:
            return
        key = stage[: -len(".start")] if stage.endswith(".start") else stage
        self._stage_started[key] = time.perf_counter_ns()
        self.emit_raw(
            {
                "event": "stage",
                "level": "info",
                "module": "observability" if stage.startswith("observability.") else "cli",
                "stage": stage,
            }
        )

    def stage_end(self, stage: str, code: str | None) -> None:
        if stage not in schema.STAGES:
            return
        key = stage[: -len(".end")] if stage.endswith(".end") else stage
        started = self._stage_started.pop(key, None)
        duration_us = 0 if started is None else (time.perf_counter_ns() - started) // 1000
        self.emit_raw(
            {
                "event": "stage",
                "level": "info",
                "module": "observability" if stage.startswith("observability.") else "cli",
                "stage": stage,
                "duration_us": duration_us,
                "code": code,
            }
        )
