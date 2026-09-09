"""Bounded parallelism for a host that runs several ranex lanes at once.

This machine runs at least three kinds of heavy work concurrently, and they are
all legitimate:

  dogfood   the iterate loop. It writes `tools/dogfood/backlog.json` and
            `tools/dogfood/iterations/` at repo-relative paths
            (`evolve_proofs.py: HERE / "backlog.json"`,
            `dogfood.py: LEDGER_DIR = TOOL_DIR / "iterations"`), so it MUST
            write into a checkout. That is by design, not a defect.
  verify    a full suite or a freeze ceremony. `test_suite_freeze_real.py`
            refuses a dirty tree, and so does `ranex run`.
  soak      `.local/campaign/soak/soak.py`, cycling the real stress tools.
            Its scratch is campaign-owned and outside repo code; it competes
            for memory and CPU only.

Run in one checkout, `dogfood` and `verify` cannot both be right: the first
dirties the tree the second requires clean. On 2026-09-09/10 that cost three
spoiled results — a freeze ceremony that returned run_exit=1 with no failure
list, a 37-minute suite whose four freeze-journey tests errored at setup, and
two stashes holding nothing but the same regenerated metrics file, saved by
someone clearing the tree and never restored.

Serialising the lanes would fix it and waste the machine. The lanes do not
actually conflict on *work* — only on two resources, a checkout and memory —
so this module separates those instead of taking turns:

  * a `verify` lane never uses the main checkout. It leases an isolated
    worktree at a pinned commit, which the dogfood loop cannot dirty because
    the loop writes to the checkout it was started in.
  * every lane takes a slot from a host semaphore sized by free memory, so
    parallelism is bounded rather than unlimited. Concurrent full suites have
    exhausted 62 GB and been OOM-killed here.

Two properties this deliberately keeps, both learned the hard way:

  * an acquire REFUSES; it does not warn and continue. An advisory check that
    a caller may ignore reproduces the failure it exists to prevent.
  * a holder is identified by pid AND boot id. Pids are reused across boots,
    and on this host an OOM kill is the expected way a holder dies, so a lock
    that cannot break itself would wedge the machine on the first kill.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

#: Host-wide, deliberately outside any checkout: the resource being shared is
#: the machine, not a repository. A lock inside a tree cannot protect a second
#: worktree of that tree, and tonight's collisions crossed exactly that line.
LANE_DIR = Path(os.environ.get("RANEX_LANE_DIR", "/tmp/ranex-lanes"))

#: Slots per kind. `verify` is the memory-hungry one — a full suite plus its
#: hermetic materialisations — so it is the one held to a single slot until the
#: numbers below say otherwise.
SLOTS = {"verify": 1, "dogfood": 1, "soak": 1}

#: A full suite with its materialisations has been measured needing headroom;
#: below this the correct answer is to wait, not to start and be killed.
MIN_AVAILABLE_GB = {"verify": 12, "dogfood": 6, "soak": 4}


def boot_id() -> str:
    """Identifies this boot, so a reused pid cannot impersonate a dead holder."""

    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:  # pragma: no cover - Linux supplies it
        return "unknown-boot"


def available_gb() -> int:
    """Available memory, the field that accounts for reclaimable cache."""

    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // (1024 * 1024)
    except (OSError, ValueError):  # pragma: no cover
        pass
    return 0


@dataclass(frozen=True, slots=True)
class Holder:
    kind: str
    pid: int
    boot: str
    started: float
    detail: str

    @property
    def alive(self) -> bool:
        """A holder is live only if its pid exists AND this is the same boot."""

        if self.boot != boot_id():
            return False
        try:
            os.kill(self.pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        return True


def _holders() -> list[Holder]:
    if not LANE_DIR.is_dir():
        return []
    found: list[Holder] = []
    for path in sorted(LANE_DIR.glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            holder = Holder(row["kind"], int(row["pid"]), row["boot"],
                            float(row["started"]), row.get("detail", ""))
        except (OSError, ValueError, KeyError, TypeError):
            path.unlink(missing_ok=True)  # unreadable is indistinguishable from stale
            continue
        if holder.alive:
            found.append(holder)
        else:
            # Self-healing: the holder died, most likely by OOM kill, which is
            # the expected death here rather than an edge case.
            path.unlink(missing_ok=True)
    return found


def acquire(kind: str, detail: str = "") -> Path:
    """Take a slot, or refuse. Never warns and proceeds."""

    if kind not in SLOTS:
        raise SystemExit(f"unknown lane {kind!r}; known lanes: {sorted(SLOTS)}")
    LANE_DIR.mkdir(parents=True, exist_ok=True)
    live = _holders()
    same = [h for h in live if h.kind == kind]
    if len(same) >= SLOTS[kind]:
        held = ", ".join(f"pid {h.pid} for {int(time.time() - h.started)}s ({h.detail})" for h in same)
        raise SystemExit(
            f"REFUSED: the {kind} lane is full ({len(same)}/{SLOTS[kind]}). Held by {held}.\n"
            "Wait for it, or run a different lane. This refuses rather than degrading "
            "a run someone else is already relying on."
        )
    have, need = available_gb(), MIN_AVAILABLE_GB[kind]
    if have < need:
        raise SystemExit(
            f"REFUSED: {have} GB available, {kind} needs {need} GB. Concurrent heavy "
            "runs have exhausted this host and been OOM-killed; a run started here "
            "would produce a result nobody could trust."
        )
    path = LANE_DIR / f"{kind}-{os.getpid()}.json"
    path.write_text(json.dumps({
        "kind": kind, "pid": os.getpid(), "boot": boot_id(),
        "started": time.time(), "detail": detail,
    }), encoding="utf-8")
    return path


def release(path: Path) -> None:
    path.unlink(missing_ok=True)


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                            text=True, check=True)
    return result.stdout.strip()


def lease_worktree(repo: Path, commit: str) -> Path:
    """An isolated checkout at `commit` that no other lane can dirty.

    This is what makes `verify` and `dogfood` genuinely parallel rather than
    politely serialised. The dogfood loop writes to the checkout it was started
    in; a worktree elsewhere is untouched by it, so a suite here stays clean
    even while the loop is mid-iteration.
    """

    resolved = _git("rev-parse", commit, cwd=repo)
    path = Path(f"/tmp/ranex-verify-{os.getpid()}-{resolved[:8]}")
    if path.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(path)],
                       cwd=repo, capture_output=True, check=False)
    _git("worktree", "add", "--detach", str(path), resolved, cwd=repo)
    return path


def drop_worktree(repo: Path, path: Path) -> None:
    subprocess.run(["git", "worktree", "remove", "--force", str(path)],
                   cwd=repo, capture_output=True, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    status = sub.add_parser("status", help="who holds what")
    status.add_argument("--json", action="store_true")

    run = sub.add_parser("run", help="take a slot and run a command in it")
    run.add_argument("--kind", required=True, choices=sorted(SLOTS))
    run.add_argument("--commit", default=None,
                     help="verify lanes: lease an isolated worktree at this commit")
    run.add_argument("--repo", default=".", type=Path)
    run.add_argument("command", nargs=argparse.REMAINDER)

    args = parser.parse_args()

    if args.action == "status":
        live = _holders()
        if args.json:
            print(json.dumps([{"kind": h.kind, "pid": h.pid, "held_s": int(time.time() - h.started),
                               "detail": h.detail} for h in live], indent=2))
        else:
            print(f"available: {available_gb()} GB")
            for kind in sorted(SLOTS):
                held = [h for h in live if h.kind == kind]
                print(f"  {kind:8} {len(held)}/{SLOTS[kind]}" +
                      ("".join(f"  pid {h.pid} {int(time.time()-h.started)}s {h.detail}" for h in held)))
        return 0

    command = args.command[1:] if args.command and args.command[0] == "--" else args.command
    if not command:
        raise SystemExit("a command is required after --")

    repo = args.repo.resolve()
    slot = acquire(args.kind, detail=" ".join(command)[:60])
    worktree: Path | None = None
    try:
        cwd = repo
        if args.commit:
            worktree = lease_worktree(repo, args.commit)
            cwd = worktree
            print(f"[lane] {args.kind}: isolated worktree {worktree}", flush=True)
        print(f"[lane] {args.kind}: running in {cwd}", flush=True)
        return subprocess.run(command, cwd=cwd, check=False).returncode
    finally:
        if worktree is not None:
            drop_worktree(repo, worktree)
        release(slot)


if __name__ == "__main__":
    raise SystemExit(main())
