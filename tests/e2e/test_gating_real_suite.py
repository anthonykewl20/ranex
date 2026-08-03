"""SLICE-006 — Ranex gates a real test suite, end to end, for real.

No synthetic packages, no toy indexes, no in-process shortcuts. Every stage
here shells out to `python -m ranex.cli.main` exactly as an operator does,
against a clone of THIS repository — the real committed `uv.lock`, the real
pinned resolver, real wheels from the real index, and the real bound command
`uv run pytest -q` — and walks the sad paths in the order a user trips them:

    baseline red -> tamper with the lock -> unpin an input -> fetch ->
    skip approval -> approve -> corrupt the store -> quarantine -> refetch ->
    honest PASS -> store reuse -> dependency change -> stale approval ->
    criterion 14 against the working repository itself.

The clone's own CLI code judges the clone: PYTHONPATH points at the clone's
`src`, so `governed_repository_root` resolves the clone through the real
mechanism, with no monkeypatching anywhere. The clone is taken from HEAD —
uncommitted implementation is invisible here by design, exactly as it is
invisible to `run`.

Stages are ordered and share one session. A stage that cannot meet its
preconditions skips loudly and everything depending on it skips with the
same reason; on a machine with no pinned resolver, no network, or no signing
key this file reports exactly what is missing instead of passing vacuously.

The recursion is self-limiting: the honest stages run this suite inside the
materialised clone, where the scratch HOME holds no store and the run has no
network, so the inner copies of these stages skip loudly.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

REAL_REPO = Path(__file__).resolve().parents[2]
PINS_PATH = REAL_REPO / "governance" / "deps.yaml"

pytestmark = pytest.mark.skipif(
    not PINS_PATH.exists(),
    reason="governance/deps.yaml is not committed yet; run the SLICE-006 "
    "operator setup before the real-world e2e can exist",
)


def pinned_resolver() -> Path | None:
    """The resolver the committed pins cite, if present and matching its pin."""

    import yaml

    pins = yaml.safe_load(PINS_PATH.read_text())
    path = Path(pins["resolver"]["path"])
    if not path.is_file():
        return None
    if hashlib.sha256(path.read_bytes()).hexdigest() != pins["resolver"]["sha256"]:
        return None
    return path


def network_available() -> bool:
    probe = socket.socket()
    probe.settimeout(3)
    try:
        probe.connect(("pypi.org", 443))
    except OSError:
        return False
    finally:
        probe.close()
    return True


class Session:
    """Shared state for the ordered stages, with loud dependency skipping."""

    def __init__(self) -> None:
        self.blocked: dict[str, str] = {}
        self.clone: Path | None = None
        self.key_path: Path | None = None
        self.store: Path | None = None

    def require(self, *stages: str) -> None:
        for stage in stages:
            if stage in self.blocked:
                pytest.skip(f"depends on {stage}: {self.blocked[stage]}")

    def block(self, stage: str, reason: str) -> None:
        self.blocked[stage] = reason
        pytest.skip(reason)


@pytest.fixture(scope="module")
def session(tmp_path_factory: pytest.TempPathFactory) -> Session:
    state = Session()
    if pinned_resolver() is None:
        state.blocked["resolver"] = (
            "the resolver named in governance/deps.yaml is absent or its "
            "bytes do not match the pinned sha256"
        )
    state.store = tmp_path_factory.mktemp("real-world") / "store"
    return state


def git(repo: Path, *arguments: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def ranex(
    repo: Path, argv: list[str], key_path: Path | None = None
) -> tuple[int, str, str]:
    """Invoke the CLI the way an operator does: a real process, the repo's
    own source on PYTHONPATH, the key in the real environment variable."""

    env = {**os.environ, "PYTHONPATH": str(repo / "src")}
    env.pop("RANEX_SIGNING_KEY", None)
    if key_path is not None:
        env["RANEX_SIGNING_KEY"] = str(key_path)
    completed = subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
    )
    return completed.returncode, completed.stdout, completed.stderr


def journal_entries(repo: Path) -> list[dict[str, object]]:
    path = repo / "governance" / "journal.sqlite3"
    if not path.exists():
        return []
    return Journal(path).entries()


def fetch_argv(store: Path) -> list[str]:
    return ["deps", "fetch", "--repository", ".", "--store", str(store)]


def approve_argv() -> list[str]:
    return ["deps", "approve", "--repository", ".", "--approver", "reviewer"]


def run_argv(store: Path, *command: str) -> list[str]:
    return [
        "run",
        "--claim",
        "tests-executed",
        "--producer",
        "worker",
        "--repository",
        ".",
        "--store",
        str(store),
        "--",
        *(command or ("uv", "run", "pytest", "-q")),
    ]


def evaluate_argv() -> list[str]:
    return [
        "gate",
        "evaluate",
        "HEAD",
        "--repository",
        ".",
        "--approver",
        "reviewer",
    ]


# --------------------------------------------------------------------------
# Stage 01 — the clone: this repository at HEAD, with a test producer.
# --------------------------------------------------------------------------


def test_stage_01_clone_the_real_repository(session: Session) -> None:
    session.require("resolver")
    clone = session.store.parent / "clone"
    result = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(clone)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        session.block("clone", f"cannot clone the repository: {result.stderr}")
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        git(clone, "config", key, value)

    # The clone is the real tree with one honest difference: a producer this
    # session holds the key for. Committed, as the trust root demands.
    private_key, public_key = generate_keypair()
    (clone / "governance" / "producers.yaml").write_text(
        f"producers:\n  worker: {public_key}\n"
    )
    key_path = session.store.parent / "worker.key"
    key_path.write_text(private_key + "\n")
    key_path.chmod(0o600)
    git(clone, "add", "governance/producers.yaml")
    committed = git(clone, "commit", "-q", "-m", "register the e2e producer")
    assert committed.returncode == 0, committed.stderr
    session.clone = clone
    session.key_path = key_path


# --------------------------------------------------------------------------
# Stage 02 — baseline red: nothing fetched, nothing derived, nothing runs.
# --------------------------------------------------------------------------


def test_stage_02_run_refuses_with_nothing_provisioned(session: Session) -> None:
    # ADR-005 sad path 14 re-proven at user level: before provisioning, the
    # bound command cannot run, and the refusal is loud — not a false PASS.
    session.require("resolver", "clone")
    code, _, err = ranex(session.clone, run_argv(session.store), session.key_path)
    assert code == 2
    assert "deriv" in err.lower() or "fetch" in err.lower()
    assert not (session.clone / "governance" / "evidence.json").exists()


# --------------------------------------------------------------------------
# Stage 03 — the limit that motivates derivation: uv lock --check says yes
# to a fabricated hash. (ADR-007, improvement 2 — kept executable.)
# --------------------------------------------------------------------------


def test_stage_03_uv_lock_check_accepts_a_fabricated_wheel_hash(
    session: Session,
) -> None:
    session.require("resolver", "clone")
    if not network_available():
        pytest.skip("no network: uv lock --check consults the index")
    scratch = session.store.parent / "lock-check"
    scratch.mkdir(exist_ok=True)
    shutil.copy(session.clone / "pyproject.toml", scratch)
    text = (session.clone / "uv.lock").read_text()
    marker = 'hash = "sha256:'
    start = text.index(marker) + len(marker)
    (scratch / "uv.lock").write_text(
        text[:start] + ("0" if text[start] != "0" else "1") + text[start + 1 :]
    )
    result = subprocess.run(
        # The epoch is passed because the lock records it: omitting it makes
        # uv re-resolve for that reason alone and report a stale lock, which
        # would let this test claim uv catches fabricated hashes when what it
        # caught was its own changed inputs.
        [
            str(pinned_resolver()),
            "lock",
            "--check",
            "--exclude-newer",
            "2026-08-04T00:00:00Z",
        ],
        cwd=scratch,
        capture_output=True,
        text=True,
        env={**os.environ, "UV_NO_CONFIG": "1"},
    )
    # The point on record: uv's own check binds the graph, not the artifact
    # bytes. If a uv upgrade makes this refuse, the derivation control has
    # become redundant rather than wrong — retire this test with a note.
    assert result.returncode == 0, (
        "uv lock --check began refusing fabricated hashes; revisit ADR-007 "
        f"improvement 2: {result.stderr}"
    )


# --------------------------------------------------------------------------
# Stage 04 — sad paths at fetch, in the order a user trips them.
# --------------------------------------------------------------------------


def test_stage_04_fetch_refuses_a_hand_edited_lock(session: Session) -> None:
    # ADR-007 s.p. 3: the same fabrication as stage 03, judged by byte
    # equality against a clean derivation instead of by uv's check.
    session.require("resolver", "clone")
    if not network_available():
        pytest.skip("no network: derivation resolves against the pinned index")
    lock = session.clone / "uv.lock"
    text = lock.read_text()
    marker = 'hash = "sha256:'
    start = text.index(marker) + len(marker)
    lock.write_text(
        text[:start] + ("0" if text[start] != "0" else "1") + text[start + 1 :]
    )
    git(session.clone, "add", "uv.lock")
    git(session.clone, "commit", "-q", "-m", "fabricate a wheel hash")
    try:
        code, _, err = ranex(session.clone, fetch_argv(session.store))
        assert code == 2
        assert "differ" in err.lower() or "match" in err.lower()
        assert all(
            entry.get("type") != "deps-derivation"
            for entry in journal_entries(session.clone)
        )
    finally:
        git(session.clone, "reset", "-q", "--hard", "HEAD^")


def test_stage_04b_fetch_refuses_an_unpinned_input(session: Session) -> None:
    # ADR-007 s.p. 4: remove one pin and the phase refuses before the network.
    session.require("resolver", "clone")
    pins = session.clone / "governance" / "deps.yaml"
    original = pins.read_text()
    pins.write_text(
        "\n".join(
            line
            for line in original.splitlines()
            if not line.startswith("exclude_newer")
        )
        + "\n"
    )
    git(session.clone, "add", "governance/deps.yaml")
    git(session.clone, "commit", "-q", "-m", "drop the resolution epoch")
    try:
        code, _, err = ranex(session.clone, fetch_argv(session.store))
        assert code == 2
        assert "exclude_newer" in err
    finally:
        git(session.clone, "reset", "-q", "--hard", "HEAD^")


# --------------------------------------------------------------------------
# Stage 05 — the real fetch: clean derivation, real wheels, real store.
# --------------------------------------------------------------------------


def test_stage_05_fetch_provisions_the_real_dependency_set(
    session: Session,
) -> None:
    session.require("resolver", "clone")
    if not network_available():
        session.block("fetch", "no network: the first fetch downloads wheels")
    code, out, err = ranex(session.clone, fetch_argv(session.store))
    if code != 0:
        session.block("fetch", f"fetch failed: {err}")
    derivations = [
        entry
        for entry in journal_entries(session.clone)
        if entry.get("type") == "deps-derivation"
    ]
    assert len(derivations) == 1
    lock_digest = hashlib.sha256(
        (session.clone / "uv.lock").read_bytes()
    ).hexdigest()
    assert derivations[0]["lock_sha256"] == lock_digest
    # The real closure, not a toy: the packages the committed lock names.
    packages = derivations[0]["packages"]
    for expected in ("pytest", "pyyaml", "cryptography", "coverage"):
        assert expected in packages, f"{expected} missing from {sorted(packages)}"
    # Wheels are on disk, content-addressed, and re-verifiable.
    entries = list((session.store / "sha256").iterdir())
    assert len(entries) >= len(packages)
    for entry in entries:
        assert hashlib.sha256(entry.read_bytes()).hexdigest() == entry.name


# --------------------------------------------------------------------------
# Stage 06 — approval is not optional and not a formality.
# --------------------------------------------------------------------------


def test_stage_06_run_refuses_the_unapproved_depset(session: Session) -> None:
    # s.p. 15/16: derived is not approved. The refusal must say so.
    session.require("resolver", "clone", "fetch")
    code, _, err = ranex(session.clone, run_argv(session.store), session.key_path)
    assert code == 2
    assert "approv" in err.lower()
    assert not (session.clone / "governance" / "evidence.json").exists()


def test_stage_06b_approve_records_the_full_set_as_the_first_delta(
    session: Session,
) -> None:
    # s.p. 15: with no baseline the approver sees everything, named.
    session.require("resolver", "clone", "fetch")
    code, out, err = ranex(session.clone, approve_argv())
    if code != 0:
        session.block("approval", f"approve failed: {err}")
    assert "pytest" in out
    approvals = [
        entry
        for entry in journal_entries(session.clone)
        if entry.get("type") == "deps-approval"
    ]
    assert len(approvals) == 1
    assert approvals[0]["approver_id"] == "reviewer"


# --------------------------------------------------------------------------
# Stage 07 — corruption: quarantined at run, healed only by refetch.
# --------------------------------------------------------------------------


def test_stage_07_corrupt_wheel_quarantines_refuses_and_refetches(
    session: Session,
) -> None:
    # s.p. 9 and 12 against real bytes: corrupt one real wheel, watch the run
    # refuse before spawning, then watch only `deps fetch` repair it.
    session.require("resolver", "clone", "fetch", "approval")
    victim = next((session.store / "sha256").iterdir())
    victim.chmod(0o600)
    victim.write_bytes(b"corrupted-real-wheel")
    code, _, err = ranex(session.clone, run_argv(session.store), session.key_path)
    assert code == 2
    assert "quarantine" in err.lower()
    assert not victim.exists()
    assert not (session.clone / "governance" / "evidence.json").exists()
    if not network_available():
        pytest.skip("no network: cannot exercise the refetch half")
    code, _, err = ranex(session.clone, fetch_argv(session.store))
    assert code == 0, err
    assert victim.exists()
    assert hashlib.sha256(victim.read_bytes()).hexdigest() == victim.name


# --------------------------------------------------------------------------
# Stage 08 — the honest run: the real suite, offline, and a real PASS.
# --------------------------------------------------------------------------


def test_stage_08a_the_real_suite_really_runs_under_governance(
    session: Session,
) -> None:
    # What provisioning actually delivers: the unchanged catalog command
    # executes against the materialised clone, imports the provisioned
    # dependencies, collects and runs the real suite, and its exit code is
    # recorded verbatim. This asserts execution and honest recording — not a
    # passing suite, which is stage 08b's separate and currently-unmet claim.
    session.require("resolver", "clone", "fetch", "approval")
    code, out, err = ranex(session.clone, run_argv(session.store), session.key_path)
    evidence_path = session.clone / "governance" / "evidence.json"
    assert evidence_path.exists(), f"no evidence was recorded: {err}"
    evidence = json.loads(evidence_path.read_text())
    assert evidence[0]["claim_id"] == "tests-executed"
    assert evidence[0]["command"] == "uv run pytest -q"
    # Verbatim, whichever way the suite went: a failing command is honest
    # evidence of failure, and `run` exits with the command's own code.
    assert evidence[0]["exit_code"] == code
    # Collection really happened. Without this the stage would pass just as
    # well on a suite that never imported pytest, which is the shape of
    # "denial that passes because the command never ran" the slice names.
    assert "passed" in out or "passed" in err, out + err


@pytest.mark.xfail(
    strict=True,
    reason=(
        "SLICE-006 criterion 14 is NOT met, and this records the miss rather "
        "than routing around it. The provisioned run works — 362 of this "
        "suite's tests pass inside the sealed offline environment — but five "
        "fail for one reason: they need a git checkout, and ADR-005's "
        "materialisation is committed blobs with no .git. Those five are "
        "test_docs_discipline::test_every_cited_implementation_is_vendored_"
        "and_matches_its_digest, test_gate_evaluate_cli::test_foreign_"
        "repository_evaluation_is_refused_by_real_cli, and the three in "
        "test_keygen_key_confinement that reach governed_repository_root(). "
        "Relaxing them is refused: _tracked_by_git documents failing closed "
        "outside a repository as deliberate, because skipping would be an "
        "author-manufactured escape hatch. The fix is an owner decision on "
        "whether the materialisation should be a git repository whose HEAD "
        "carries the subject tree — an amendment to ADR-005, so it needs its "
        "own ADR and is deliberately not started here. strict=True so this "
        "fails loudly the moment criterion 14 actually starts passing."
    ),
)
def test_stage_08b_criterion_14_the_suite_passes_and_the_gate_accepts(
    session: Session,
) -> None:
    session.require("resolver", "clone", "fetch", "approval")
    code, out, err = ranex(session.clone, run_argv(session.store), session.key_path)
    assert code == 0, f"the real suite did not pass under governance: {err}"
    code, out, _ = ranex(session.clone, evaluate_argv())
    assert code == 0
    assert out.startswith("PASS")


# --------------------------------------------------------------------------
# Stage 09 — amortisation: an unchanged set downloads nothing.
# --------------------------------------------------------------------------


def test_stage_09_second_fetch_reuses_every_store_entry(session: Session) -> None:
    # ADR-007 quality attribute: second fetch, zero downloads. Proven by
    # store identity: no entry changes inode or bytes, and none is added.
    session.require("resolver", "clone", "fetch")
    if not network_available():
        pytest.skip("no network: derivation still resolves against the index")
    before = {
        entry.name: entry.stat().st_ino
        for entry in (session.store / "sha256").iterdir()
    }
    code, _, err = ranex(session.clone, fetch_argv(session.store))
    assert code == 0, err
    after = {
        entry.name: entry.stat().st_ino
        for entry in (session.store / "sha256").iterdir()
    }
    assert after == before


# --------------------------------------------------------------------------
# Stage 10 — a dependency change is visible, named, and blocks until
# re-approved. (criterion 9 at user level)
# --------------------------------------------------------------------------


def test_stage_10_a_dependency_change_blocks_until_reapproved(
    session: Session,
) -> None:
    session.require("resolver", "clone", "fetch", "approval")
    if not network_available():
        pytest.skip("no network: the changed set must re-derive and re-fetch")
    pyproject = session.clone / "pyproject.toml"
    original = pyproject.read_text()
    changed = original.replace('"PyYAML>=6.0.2,<7"', '"PyYAML>=6.0.1,<6.0.2"')
    assert changed != original
    pyproject.write_text(changed)
    relock = subprocess.run(
        [
            str(pinned_resolver()),
            "lock",
            "--exclude-newer",
            "2026-08-04T00:00:00Z",
            "--python",
            "3.12",
        ],
        cwd=session.clone,
        capture_output=True,
        text=True,
        env={**os.environ, "UV_NO_CONFIG": "1"},
    )
    assert relock.returncode == 0, relock.stderr
    git(session.clone, "add", "pyproject.toml", "uv.lock")
    git(session.clone, "commit", "-q", "-m", "downgrade pyyaml")
    try:
        code, _, err = ranex(session.clone, fetch_argv(session.store))
        assert code == 0, err
        # Derived and fetched — but the approval on record is for the old
        # set, so the run refuses, and the refusal names the moved package.
        code, _, err = ranex(
            session.clone, run_argv(session.store), session.key_path
        )
        assert code == 2
        assert "approv" in err.lower()
        assert "pyyaml" in err.lower()
        # Approving the exact new delta unblocks; it names old and new.
        code, out, err = ranex(session.clone, approve_argv())
        assert code == 0, err
        assert "pyyaml" in out.lower()
        assert "6.0.1" in out
    finally:
        git(session.clone, "reset", "-q", "--hard", "HEAD^")
        # The journal is append-only; history stays. Re-derive and re-approve
        # the restored set explicitly so later stages meet a clean state.
        code, _, err = ranex(session.clone, fetch_argv(session.store))
        assert code == 0, err
        code, _, err = ranex(session.clone, approve_argv())
        assert code == 0, err


# --------------------------------------------------------------------------
# Stage 11 — the run is offline and its root is sealed, proven through the
# real pinned uv, not a mock. (criteria 7, 8)
# --------------------------------------------------------------------------


def test_stage_11_the_gated_run_is_offline_with_a_sealed_root(
    session: Session,
) -> None:
    session.require("resolver", "clone", "fetch", "approval")
    probe = (
        "import os, socket, sys\n"
        "ok = (os.environ.get('UV_NO_SYNC') == '1'\n"
        "      and os.environ.get('UV_OFFLINE') == '1')\n"
        "root = os.environ.get('UV_PROJECT_ENVIRONMENT', '')\n"
        "ok = ok and bool(root)\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 443), timeout=5)\n"
        "    ok = False\n"
        "except OSError:\n"
        "    pass\n"
        "try:\n"
        "    open(os.path.join(root, 'planted'), 'w')\n"
        "    ok = False\n"
        "except OSError:\n"
        "    pass\n"
        "sys.exit(0 if ok else 6)\n"
    )
    # The probe replaces the suite for one committed catalog edit, reverted
    # after: the claim command must stay bound, so the catalog names it.
    gates = session.clone / "governance" / "gates.yaml"
    original = gates.read_text()
    command = json.dumps(["uv", "run", "--no-project", "python", "-c", probe])
    gates.write_text(
        original.replace(
            'command: ["uv", "run", "pytest", "-q"]', f"command: {command}"
        )
    )
    assert gates.read_text() != original, "catalog rewrite missed its anchor"
    git(session.clone, "add", "governance/gates.yaml")
    git(session.clone, "commit", "-q", "-m", "bind the offline probe")
    try:
        code, _, err = ranex(
            session.clone,
            run_argv(
                session.store,
                "uv",
                "run",
                "--no-project",
                "python",
                "-c",
                probe,
            ),
            session.key_path,
        )
        assert code == 0, f"offline/sealed probe failed: {err}"
    finally:
        git(session.clone, "reset", "-q", "--hard", "HEAD^")


# --------------------------------------------------------------------------
# Stage 12 — criterion 14: this working repository gates itself.
# --------------------------------------------------------------------------


def test_stage_12_ranex_gates_its_own_repository(tmp_path: Path) -> None:
    # The end-to-end confirmation ADR-007 names: the unchanged catalog
    # command, the real current commit, the operator's own store and key.
    # The preconditions are the operator's, so each miss skips loudly.
    if pinned_resolver() is None:
        pytest.skip("the pinned resolver is absent or does not match its digest")
    key = os.environ.get("RANEX_SIGNING_KEY")
    if not key:
        pytest.skip("RANEX_SIGNING_KEY is not set; the operator runs this stage")
    dirty = subprocess.run(
        ["git", "-C", str(REAL_REPO), "status", "--porcelain"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    if dirty:
        pytest.skip("the working tree is dirty; the self-gate needs HEAD honest")
    default_store = Path.home() / ".local" / "state" / "ranex" / "store"
    if not (default_store / "sha256").is_dir():
        pytest.skip("the operator store is empty; run `ranex deps fetch` first")

    code, _, err = ranex(
        REAL_REPO,
        [
            "run",
            "--claim",
            "tests-executed",
            "--producer",
            "anthony",
            "--repository",
            ".",
            "--store",
            str(default_store),
            "--",
            "uv",
            "run",
            "pytest",
            "-q",
        ],
        Path(key),
    )
    assert code == 0, f"the suite did not pass under governance: {err}"
    code, out, _ = ranex(REAL_REPO, evaluate_argv())
    assert code == 0
    assert out.startswith("PASS")
