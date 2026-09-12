"""The lanes must be parallel and bounded, and the guard must be able to refuse.

`tools/dogfood/lane.py` exists because this host runs three legitimate kinds of
heavy work at once — the dogfood iterate loop, verification suites, and the
soak campaign — and two of them cannot share a checkout. The loop writes
`backlog.json` and `iterations/` at repo-relative paths by design; the freeze
journey and `ranex run` both refuse a dirty tree. Serialising them would be
correct and would waste the machine.

Every property below was a real failure first. A guard that reports 13 phantom
watcher shells, an anchored pattern that reports "clear" while a freeze runs, a
lock that cannot break itself after the OOM kill that is this host's expected
death — each of those happened, and each is why the corresponding test is here
rather than in a design note.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE = REPO_ROOT / "tools" / "dogfood" / "lane.py"


@pytest.fixture
def lane(tmp_path, monkeypatch):
    monkeypatch.setenv("RANEX_LANE_DIR", str(tmp_path / "lanes"))
    spec = importlib.util.spec_from_file_location("ranex_lane", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_a_slot_admits_one_and_refuses_the_next(lane) -> None:
    """An acquire refuses. It does not warn and let the caller proceed.

    An advisory check a caller may ignore reproduces exactly the failure it
    exists to prevent — which is how a second full suite launched into a
    running freeze ceremony and cost it its result.
    """

    held = lane.acquire("soak", detail="first")
    with pytest.raises(SystemExit) as refusal:
        lane.acquire("soak", detail="second")
    assert "REFUSED" in str(refusal.value)
    assert "soak lane is full" in str(refusal.value)
    lane.release(held)
    lane.release(lane.acquire("soak", detail="after release"))


def test_a_dead_holder_frees_its_slot(lane) -> None:
    """An OOM kill is this host's expected death, not an edge case.

    A lock that cannot break itself would wedge the machine on the first kill,
    which is a worse failure than the contention it prevents.
    """

    directory = Path(os.environ["RANEX_LANE_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    dead = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    dead.kill()
    dead.wait()
    (directory / f"soak-{dead.pid}.json").write_text(json.dumps({
        "kind": "soak", "pid": dead.pid, "boot": lane.boot_id(),
        "started": time.time(), "detail": "killed",
    }), encoding="utf-8")

    assert lane._holders() == [], "a killed holder must not keep its slot"
    lane.release(lane.acquire("soak"))


def test_a_lock_from_another_boot_is_stale(lane) -> None:
    """Pids are reused across boots, so a live pid is not proof of a live holder."""

    directory = Path(os.environ["RANEX_LANE_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "soak-1.json").write_text(json.dumps({
        "kind": "soak", "pid": os.getpid(), "boot": "a-different-boot",
        "started": time.time(), "detail": "previous boot",
    }), encoding="utf-8")

    assert lane._holders() == [], "a lock from another boot must be stale"


def test_the_memory_guard_refuses_a_doomed_run(lane, monkeypatch) -> None:
    """Below the headroom a run needs, the answer is to wait, not to start.

    Concurrent full suites have exhausted 62 GB on this host and been
    OOM-killed; starting anyway produces a result nobody can trust.
    """

    monkeypatch.setitem(lane.MIN_AVAILABLE_GB, "verify", 10**6)
    with pytest.raises(SystemExit) as refusal:
        lane.acquire("verify")
    assert "REFUSED" in str(refusal.value) and "GB available" in str(refusal.value)


def test_a_leased_worktree_is_not_dirtied_by_writes_to_the_repository(lane, tmp_path) -> None:
    """The property that makes the lanes genuinely parallel rather than polite.

    The dogfood loop writes into the checkout it was started in. A verification
    lane leases a worktree elsewhere, so the loop cannot dirty the tree the
    suite is judging — and the freeze journey, which refuses a dirty tree, can
    run at the same time as the loop instead of waiting for it.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    for args in (("init", "-q", "."), ("config", "user.email", "a@b.c"), ("config", "user.name", "t")):
        subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)
    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "base"], check=True, capture_output=True)

    leased = lane.lease_worktree(repo, "HEAD")
    try:
        # The dogfood-shaped write: a new file at a repo-relative path.
        (repo / "backlog.json").write_text('{"regenerated": true}\n', encoding="utf-8")

        def dirty(where: Path) -> int:
            out = subprocess.run(["git", "-C", str(where), "status", "--porcelain"],
                                 capture_output=True, text=True, check=True).stdout
            return len([line for line in out.splitlines() if line.strip()])

        assert dirty(repo) == 1, "the write should dirty the checkout it was made in"
        assert dirty(leased) == 0, (
            "the leased worktree must be unaffected — this is the whole basis for "
            "running a suite while the dogfood loop is mid-iteration"
        )
    finally:
        lane.drop_worktree(repo, leased)


def test_status_reports_holders_without_taking_a_slot(lane) -> None:
    """Reading who holds what must never itself contend for the thing."""

    held = lane.acquire("dogfood", detail="reported")
    try:
        holders = lane._holders()
        assert [h.kind for h in holders] == ["dogfood"]
        assert holders[0].detail == "reported"
        assert lane._holders() == holders, "observing must not consume"
    finally:
        lane.release(held)


def test_simultaneous_processes_cannot_share_one_slot(tmp_path) -> None:
    """Three real races must each admit one holder out of sixteen contenders."""

    probe = REPO_ROOT / "tools/dogfood/audits/2026-09-12-leitir-lane-race/race.py"
    completed = subprocess.run(
        [sys.executable, str(probe), str(MODULE), str(tmp_path / "race")],
        capture_output=True, text=True, check=False, timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    rows = json.loads((tmp_path / "race/summary.json").read_text())
    assert len(rows) == 3
    assert all((row["ADMITTED"], row["REFUSED"], row["ERROR"]) == (1, 15, 0)
               for row in rows)
