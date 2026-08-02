"""SLICE-003 — D9: a bind mount is a second name that `st_nlink` never counts.

D8 said the property is identity, not location: the resolved executable must not
be the same file as anything inside the subject worktree. `same_file_inside`
decides that on `(st_dev, st_ino)`, which is right, and then declines to ask
whenever `st_nlink <= 1`.

A hard link is not the only way to give one inode a second name. `mount --bind`
gives it one without touching the link count at all — the same device, the same
inode, and `st_nlink == 1` on both names. So the fast path answers "there is no
second name to find" about a file that has exactly one, and every other check
agrees with it honestly: the resolved path is outside, no component of the route
is inside, and `/proc/self/fd` confirms the descriptor leads to the outside
name. The bytes that execute are the ones the observed tree carries, and the
gate PASSes.

This is D1, D2 and D8 in a fourth costume — the tree under observation choosing
which bytes run — and it is the costume the D8 fix was measured against and does
not see.

The reproduction needs a mount namespace, because a bind mount made in one is
invisible outside it. That means the whole `ranex run` invocation happens inside
it, as a real subprocess, and not through the in-process `main(argv)` helper the
sibling file uses. `governed_repository_root()` reads the CLI's own location, and
a subprocess cannot be monkeypatched, so the repository under test carries its
own copy of `src/ranex` and the child is pointed at it with `PYTHONPATH`. That
copy is committed like everything else, so the tree is clean and the governed
root is genuinely the temporary repository.

An unprivileged user *can* do this on the machine this was written on: `bwrap`
ships an AppArmor profile that permits unprivileged user namespaces, the uid
inside the namespace is the same uid outside it, and no capability is granted
that the worker did not already have. `unshare --map-root-user` is refused here
by `kernel.apparmor_restrict_unprivileged_userns`, which is why the tool is
probed rather than named.

Imports of `ranex` are deferred into fixtures and test bodies, for the reason the
sibling file gives: a module-level import of a symbol a fix has not created yet
is a collection error, and a collection error takes the whole suite down.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

# The `src/ranex` tree this suite is testing, copied into each repository under
# test so the child process's governed root is that repository and not this one.
CLI_SOURCE = Path(__file__).resolve().parents[2] / "src" / "ranex"

# Printed by the wrapper before the CLI starts, so the test can prove the bind
# mount actually took effect rather than assuming it did.
IDENTITY_PREFIX = "IDENTITY"


def bind_mounted_argv(
    tool: str,
    source: Path,
    destination: Path,
    command: list[str],
) -> list[str]:
    """argv that bind-mounts `source` over `destination`, then runs `command`.

    Two shapes because two tools reach the same namespace by different routes,
    and which one an unprivileged account may use is a property of the machine.
    """

    if tool == "bwrap":
        return [
            "bwrap",
            # The host filesystem as it is, so the repository, the key and the
            # interpreter are all where the CLI expects them.
            "--dev-bind", "/", "/",
            "--bind", str(source), str(destination),
            "--",
            *command,
        ]
    return [
        "unshare",
        "--map-root-user",
        "--mount",
        "sh",
        "-c",
        'mount --bind "$1" "$2" || exit 125; shift 2; exec "$@"',
        "sh",
        str(source),
        str(destination),
        *command,
    ]


def working_bind_mount_tool() -> str | None:
    """The first tool that really gives one inode a second name here, or None.

    Asked with a bind mount and answered by comparing `(st_dev, st_ino)`, not by
    checking an exit code: a tool that runs the command in the host namespace
    without mounting anything would otherwise be reported as working, and the
    reproduction below would then prove nothing while looking green.
    """

    scratch = Path(tempfile.mkdtemp())
    try:
        source = scratch / "source"
        source.write_text("bytes\n", encoding="utf-8")
        destination = scratch / "destination"
        destination.write_text("", encoding="utf-8")
        for tool in ("bwrap", "unshare"):
            if shutil.which(tool) is None:
                continue
            try:
                result = subprocess.run(
                    bind_mounted_argv(
                        tool,
                        source,
                        destination,
                        ["stat", "-c", "%d %i", str(destination), str(source)],
                    ),
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError:
                continue
            lines = result.stdout.split("\n")
            if result.returncode == 0 and len(lines) >= 2 and lines[0] == lines[1]:
                return tool
        return None
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


BIND_MOUNT_TOOL = working_bind_mount_tool()

needs_bind_mount = pytest.mark.skipif(
    BIND_MOUNT_TOOL is None,
    reason=(
        "no unprivileged mount namespace available: neither bwrap nor unshare "
        "could bind-mount one file over another as this uid. The defect is not "
        "thereby absent — it is only unreproducible here, and a machine where "
        "an unprivileged user CAN mount is a machine where this test must run"
    ),
)


def build_gates(claim_id: str, argv: list[str]) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        f"      - claim_id: {claim_id}\n"
        f"        command: {json.dumps(argv)}\n"
    )


def script(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


@pytest.fixture()
def keys(tmp_path: Path) -> dict[str, str]:
    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    path = tmp_path / "worker.key"
    path.write_text(private + "\n", encoding="utf-8")
    path.chmod(0o600)
    return {"private": private, "public": public, "path": str(path)}


@pytest.fixture()
def repo(tmp_path: Path, keys: dict[str, str]) -> Path:
    """A governed repository that carries its own copy of the CLI.

    `governed_repository_root()` answers with the checkout the CLI module lives
    in, and these tests run the CLI in a subprocess inside a mount namespace
    where `monkeypatch` cannot reach. Installing the CLI into the repository is
    the honest way to make the governed root be this repository: nothing is
    stubbed, the same code path decides the same question, and the answer is
    load-bearing rather than injected.
    """

    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    shutil.copytree(
        CLI_SOURCE,
        repository / "src" / "ranex",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "producers.yaml").write_text(
        f"producers:\n  worker: {keys['public']}\n", encoding="utf-8"
    )
    return repository


def commit_all(repo: Path, message: str = "initial") -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


def environment_for(
    repo: Path,
    tmp_path: Path,
    *,
    key_path: str | None = None,
    path_prefix: Path | None = None,
) -> dict[str, str]:
    """The child's whole environment, built rather than inherited."""

    search_path = os.environ["PATH"]
    if path_prefix is not None:
        search_path = f"{path_prefix}{os.pathsep}{search_path}"
    environment = {
        "PATH": search_path,
        "HOME": str(tmp_path),
        "LC_ALL": "C",
        # Byte-code caches would land inside the repository as untracked files,
        # and `run` would then refuse its own installation as a dirty tree.
        "PYTHONDONTWRITEBYTECODE": "1",
        # The copy inside the repository, never this checkout's.
        "PYTHONPATH": str(repo / "src"),
    }
    if key_path is not None:
        environment["RANEX_SIGNING_KEY"] = key_path
    return environment


def run_argv(*command: str, claim: str = "tests-executed") -> list[str]:
    return [
        sys.executable, "-m", "ranex.cli.main",
        "run",
        "--claim", claim,
        "--producer", "worker",
        "--repository", ".",
        "--evidence", "evidence.json",
        "--producers", "producers.yaml",
        "--", *command,
    ]


def evaluate(
    repo: Path,
    tmp_path: Path,
    approver: str = "reviewer",
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable, "-m", "ranex.cli.main",
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--approver", approver,
        ],
        cwd=repo,
        env=environment_for(repo, tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )


# --- D9: one inode, two names, and the link count says there is one ---------


@needs_bind_mount
def test_run_refuses_a_bind_mounted_second_name_for_an_in_repo_file(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """D9 — the second name a bind mount makes is one `st_nlink` cannot count.

    `mount --bind <repo>/tools/pytest <outside>/bin/pytest` leaves the outside
    path reporting the same device and the same inode as the in-repo file, and a
    link count of one. Every location check then answers honestly and wrongly:
    the resolved path is outside the worktree, no component of the route lies
    inside it, and `/proc/self/fd` confirms the descriptor opened the outside
    name. Only identity sees it, and identity is asked only when the link count
    says a second name exists — which is exactly what a bind mount does not do.

    An unprivileged worker running as the same uid as the tool can make this
    mount; it needs a user namespace and no privilege beyond that.

    The required property is the one D8 stated and this shows unmet: the
    resolved executable must not BE a file inside the subject worktree, however
    the second name was obtained. `st_nlink` is a cheap answer to a different
    question — "does another *link* exist" — and the question that matters is
    "is this the same file".
    """

    marker = tmp_path / "in-repo-bytes-ran"
    inside = script(repo / "tools" / "pytest", f'touch "{marker}"\nexit 0')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["pytest", "-q"]), encoding="utf-8"
    )
    commit_all(repo)

    # The mount point. Its own bytes never run: the bind mount covers them, and
    # a distinct exit code makes that visible if it ever stops being true.
    outside = tmp_path / "bin"
    script(outside / "pytest", "exit 77")

    wrapped = [
        "sh",
        "-c",
        f'stat -c "{IDENTITY_PREFIX} %d %i %h" "$1" "$2"; shift 2; exec "$@"',
        "sh",
        str(outside / "pytest"),
        str(inside),
        *run_argv("pytest", "-q"),
    ]
    completed = subprocess.run(
        bind_mounted_argv(BIND_MOUNT_TOOL, inside, outside / "pytest", wrapped),
        cwd=repo,
        env=environment_for(
            repo, tmp_path, key_path=keys["path"], path_prefix=outside
        ),
        capture_output=True,
        text=True,
        check=False,
    )

    seen = [
        line for line in completed.stdout.splitlines()
        if line.startswith(IDENTITY_PREFIX)
    ]
    assert len(seen) == 2 and seen[0] == seen[1], (
        "the bind mount did not give the outside path the in-repo file's "
        f"identity, so this test proves nothing: {seen} / {completed.stderr}"
    )
    assert seen[0].split()[3] == "1", (
        "the whole point is a second name the link count does not report; if it "
        f"reports one here, this reproduction is not D9: {seen[0]}"
    )

    assert completed.returncode == EXIT_USAGE, (
        "a bind-mounted second name for a file inside the worktree was accepted "
        "as an outside binary. Identity was decided on the link count, and a "
        f"bind mount does not move it: exit={completed.returncode} "
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert not marker.exists(), (
        "the in-repo bytes executed; the tree under observation chose the binary "
        "that proves it"
    )
    assert not (repo / "evidence.json").exists(), (
        "a record was written for a command whose bytes came out of the subject "
        "worktree"
    )
    assert evaluate(repo, tmp_path).returncode != EXIT_PASS, (
        "a PASS remained reachable after the refusal should have stopped it"
    )


# --- the property itself, on a machine that cannot mount --------------------


@pytest.mark.parametrize("link_count", [1, 2])
def test_the_identity_check_does_not_depend_on_the_link_count(
    repo: Path,
    tmp_path: Path,
    link_count: int,
) -> None:
    """The same file, two reported link counts, and one required answer.

    A real second name for a real in-repo inode is made with a hard link, which
    is the only way to get one without a mount namespace. The link count is then
    the single field that differs between the two cases, and it is not invented:
    `link_count == 1` is byte-for-byte what `os.fstat` returns for the
    descriptor `run` opens when the second name came from a bind mount — same
    device, same inode, one link — as the reproduction above measures on this
    machine. So this is the same situation stated without needing to mount
    anything, and it must get the same answer.

    This is the one test here that names an internal, because the property is
    about a value the implementation reads and the observable path to it needs a
    namespace. If the fix moves the check somewhere else, this test moves with
    it; what must not move is the answer.
    """

    from ranex.cli.main import same_file_inside

    inside = script(repo / "tools" / "pytest", "exit 0")
    outside = tmp_path / "bin"
    outside.mkdir()
    os.link(inside, outside / "pytest")

    observed = (outside / "pytest").stat()
    assert observed.st_ino == inside.stat().st_ino, (
        "the second name must share the inode, or this test proves nothing"
    )
    identity = os.stat_result(
        (
            observed.st_mode,
            observed.st_ino,
            observed.st_dev,
            link_count,
            observed.st_uid,
            observed.st_gid,
            observed.st_size,
            int(observed.st_atime),
            int(observed.st_mtime),
            int(observed.st_ctime),
        )
    )

    twin = same_file_inside(identity, repo.resolve())

    assert twin is not None, (
        f"a file reporting {link_count} link(s) was declared to have no second "
        "name inside the worktree, while it is the very same inode as "
        f"{inside}. The link count answers 'does another link exist'; the "
        "question is 'is this the same file', and a bind mount separates the two"
    )
    assert twin.resolve() == inside.resolve(), (
        f"the twin found was {twin}, not the in-repo file {inside}"
    )


# --- D10: a directory the scan cannot read is not one with nothing in it ----


def test_run_refuses_when_the_identity_scan_cannot_read_the_worktree(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """D10 — one `chmod 000` inside the worktree and the identity check answers no.

    The scan that decides "is this the same file as something inside the tree"
    walks the tree with `os.scandir`, and a directory it cannot open is skipped
    and forgotten. The worker runs as the same uid as the tool, so it owns every
    directory in its own worktree and may close one; git records the executable
    bit on files and nothing whatever about directory modes, so `git status
    --porcelain` stays empty and the dirty-tree check agrees the tree is clean.

    So: commit an in-repo script, hard-link it to a name outside the repository
    while the directory is still readable, then close the directory. The link
    count still says two and the inode is still shared — nothing about the file
    changed — but the pass now walks past the only name that would have matched.
    It reports no twin, `run` accepts the outside name as an ordinary tool, and
    the bytes the observed tree carries execute and prove the tree that carries
    them. This is D1, D2, D8 and D9 in a fifth costume, and the cheapest one yet:
    it needs no namespace, no privilege and no link the scan cannot see, only a
    directory the scan is not allowed to look in.

    The required answer is not "search harder", because a directory that cannot
    be read cannot be searched at all. It is that a question the tool was unable
    to ask must never be recorded as one it asked and answered no. `path_behind`
    already holds this line — with `/proc/self/fd` missing it refuses rather than
    guessing where a descriptor leads — and an unreadable directory is the same
    ignorance about the same claim. `run` must exit 2, execute nothing, and write
    no record.
    """

    marker = tmp_path / "in-repo-bytes-ran"
    inside = script(repo / "tools" / "pytest", f'touch "{marker}"\nexit 0')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["pytest", "-q"]), encoding="utf-8"
    )
    commit_all(repo)

    # The second name, taken while the directory is still open to everyone. An
    # ordinary hard link: no namespace, no privilege, and nothing the scan has
    # not already been shown to find when it is allowed to look.
    outside = tmp_path / "bin"
    outside.mkdir()
    os.link(inside, outside / "pytest")
    assert (outside / "pytest").stat().st_ino == inside.stat().st_ino, (
        "the outside name must share the in-repo inode, or this test proves "
        "nothing about identity"
    )

    closed = repo / "tools"
    restore = closed.stat().st_mode & 0o777
    try:
        closed.chmod(0o000)

        status = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert status.stdout == "", (
            "the attack rests on the tree still looking clean: git holds no "
            "directory modes, so closing one changes nothing it reports. If it "
            "reported this, the dirty-tree check would refuse before identity "
            f"was ever asked and the reproduction would prove nothing: "
            f"{status.stdout!r}"
        )

        completed = subprocess.run(
            run_argv("pytest", "-q"),
            cwd=repo,
            env=environment_for(
                repo, tmp_path, key_path=keys["path"], path_prefix=outside
            ),
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        # Reopened whatever happened above: `tmp_path` cleanup cannot descend
        # through a directory it may not open, and would error tearing down.
        closed.chmod(restore)

    assert completed.returncode == EXIT_USAGE, (
        "a file the identity scan was not permitted to look for was treated as "
        "one it looked for and did not find. A single chmod inside the worktree "
        "— untracked by git, unreported by `git status` — turned the in-repo "
        f"bytes into an outside tool: exit={completed.returncode} "
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert not marker.exists(), (
        "the in-repo bytes executed; the tree under observation chose the "
        "binary that proves it, by closing the directory holding its own copy"
    )
    assert not (repo / "evidence.json").exists(), (
        "a record was written for a command the tool could not prove came from "
        "outside the subject worktree"
    )
    assert evaluate(repo, tmp_path).returncode != EXIT_PASS, (
        "a PASS remained reachable after the refusal should have stopped it"
    )


# --- the control: refusing everything is not a fix --------------------------


def test_a_genuine_outside_binary_still_runs_and_still_reaches_a_pass(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """The control. A binary that is neither bound nor linked into the tree is
    an ordinary tool, and the loop is worth nothing if it cannot use one.

    Run through the same subprocess machinery as the reproduction — same
    installed CLI, same built environment — so that what it controls for is the
    fix and not the harness. Deliberately not wrapped in a namespace: this must
    be asserted on every machine, including the ones where the reproduction
    above skips.

    Re-aimed for SLICE-004. It used to name the tool `pytest` and reach it
    through a PATH prefix, which the pinned toolchain now ignores by design — so
    the refusal it started reporting was ADR-005 working, not a regression. The
    *property* is unchanged and still worth asserting, so the catalog binds the
    binary's absolute path: resolution no longer depends on a PATH the observed
    party owns, and the containment and inode checks are what decide. Left as a
    PATH lookup it would have failed for a reason that has nothing to do with
    bind-mount identity, which is this file's subject.
    """

    marker = tmp_path / "outside-tool-ran"
    outside = tmp_path / "bin"
    tool = script(outside / "pytest", f'touch "{marker}"\nexit 0')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", [str(tool), "-q"]), encoding="utf-8"
    )
    commit_all(repo)

    completed = subprocess.run(
        run_argv(str(tool), "-q"),
        cwd=repo,
        env=environment_for(repo, tmp_path, key_path=keys["path"]),
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == EXIT_PASS, (
        "an ordinary binary outside the repository was refused; a `run` that "
        f"refuses everything is a broken loop, not a governed one: "
        f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
    )
    assert marker.exists(), "the outside tool did not actually run"
    assert (repo / "evidence.json").exists(), "no record was written"

    verdict = evaluate(repo, tmp_path)
    assert verdict.returncode == EXIT_PASS, (
        "honest evidence from an honest binary did not reach a PASS: "
        f"stdout={verdict.stdout!r} stderr={verdict.stderr!r}"
    )
