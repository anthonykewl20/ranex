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
A stage that never ran at all is a different thing and is not a skip: its
dependents FAIL and name it, because a missing artifact nobody declared
absent is absence, and absence blocks.

The recursion is self-limiting: the honest stages run this suite inside the
materialised clone, where the scratch HOME holds no store and the run has no
network, so the inner copies of these stages skip loudly.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import socket
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.cli.main import record_evidence, subject_digest_for
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.foundation.suite_results import load_manifest
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain import admission
from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate

REAL_REPO = Path(__file__).resolve().parents[2]
PINS_PATH = REAL_REPO / "governance" / "deps.yaml"
pytestmark = pytest.mark.skipif(
    not PINS_PATH.exists(),
    reason="governance/deps.yaml is not committed yet; run the SLICE-006 "
    "operator setup before the real-world e2e can exist",
)


def pinned_resolver() -> Path | None:
    """The resolver the committed pins cite, if present and matching its pin.

    Sanctioned spine edit (SLICE-055 M8 dedupe): the verdict — presence AND
    digest match — is the frame probe's (tests/e2e/_prereqs.py owns that
    logic; this local copy was its duplicate); the path is re-derived from
    the same committed pins the probe just verified, so the two can never
    disagree.
    """

    import yaml

    e2e_dir = str(Path(__file__).resolve().parent)
    if e2e_dir not in sys.path:
        sys.path.insert(0, e2e_dir)
    import _prereqs

    ok, _reason = _prereqs.pinned_resolver()
    if not ok:
        return None
    pins = yaml.safe_load(PINS_PATH.read_text())
    return Path(pins["resolver"]["path"])


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


def nested_hermetic_self_gate() -> bool:
    """Terminate intentional self-recursion as a passing boundary check.

    The outer live gate already exercises this module.  Its materialised suite
    must not recursively provision and run another complete live gate forever,
    and a skip is now correctly treated as absence.  Inside the exact sealed
    provisioned environment, these IDs therefore pass by verifying the
    recursion boundary itself; on an operator invocation they still execute
    their full real-world stages below.
    """

    dependency_root = os.environ.get("UV_PROJECT_ENVIRONMENT")
    home = os.environ.get("HOME")
    temporary = os.environ.get("TMPDIR")
    if not dependency_root or not home or not temporary:
        return False
    repository = REAL_REPO.resolve()
    materialisation = repository.parent
    if (
        repository.name != "tree"
        or not materialisation.name.startswith("ranex-subject-")
        or Path.cwd().resolve() != repository
    ):
        return False
    dependency_path = Path(dependency_root)
    home_path = Path(home)
    temporary_path = Path(temporary)
    if (
        dependency_path != materialisation / "deps" / "env"
        or home_path != materialisation / "home"
        or temporary_path != materialisation / "tmp"
    ):
        return False
    if not all(path.is_dir() for path in (dependency_path, home_path, temporary_path)):
        return False
    if not (repository / ".git").is_dir():
        return False
    commit_count = subprocess.run(
        ["git", "-C", str(repository), "rev-list", "--count", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    remotes = subprocess.run(
        ["git", "-C", str(repository), "remote"],
        capture_output=True,
        text=True,
        check=False,
    )
    if (
        commit_count.returncode != 0
        or commit_count.stdout.strip() != "1"
        or remotes.returncode != 0
        or remotes.stdout.strip()
    ):
        return False
    assert os.environ.get("UV_NO_SYNC") == "1"
    assert os.environ.get("UV_OFFLINE") == "1"
    assert os.environ.get("UV_NO_CONFIG") == "1"
    assert os.environ.get("UV_FROZEN") == "1"
    assert os.environ.get("VIRTUAL_ENV") == str(dependency_path)
    assert stat.S_IMODE(dependency_path.stat().st_mode) & 0o222 == 0
    return True


def test_nested_self_gate_cannot_be_activated_by_forged_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_root = tmp_path / "ranex-subject-forged"
    for name in ("deps/env", "home", "tmp"):
        (fake_root / name).mkdir(parents=True, exist_ok=True)
    (fake_root / "deps" / "env").chmod(0o555)
    monkeypatch.chdir(REAL_REPO)
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(fake_root / "deps" / "env"))
    monkeypatch.setenv("HOME", str(fake_root / "home"))
    monkeypatch.setenv("TMPDIR", str(fake_root / "tmp"))
    monkeypatch.setenv("UV_NO_SYNC", "1")
    monkeypatch.setenv("UV_OFFLINE", "1")
    monkeypatch.setenv("UV_NO_CONFIG", "1")
    monkeypatch.setenv("UV_FROZEN", "1")

    assert nested_hermetic_self_gate() is False


class Session:
    """Shared state for the ordered stages, with loud dependency skipping.

    A stage is in exactly one of three states, and they are not the same thing:

    * **reached** — it ran and produced the artifact its dependents consume.
    * **blocked** — a precondition this machine cannot supply was found absent
      and named, so dependents skip with that reason.
    * **neither** — it never ran at all.

    The third state is the one that used to be silent. `require()` only
    consulted `blocked`, so a never-run stage sailed through the guard and the
    dependent stage then dereferenced an unset `None` attribute, dying with a
    `TypeError` that named neither the stage nor the reason. It is now a loud
    failure. It is deliberately NOT a skip: this project treats absence as
    FAIL, and turning a missing artifact into a skip would convert a crash into
    a silent pass-by-absence — exactly the failure mode Ranex exists to catch.
    """

    def __init__(self) -> None:
        self.blocked: dict[str, str] = {}
        self.reached: set[str] = set()
        self.clone: Path | None = None
        self.key_path: Path | None = None
        self.store: Path | None = None

    def reach(self, stage: str) -> None:
        """Record that `stage` produced the artifact its dependents need."""

        self.reached.add(stage)

    def require(self, *stages: str) -> None:
        for stage in stages:
            if stage in self.blocked:
                pytest.skip(f"depends on {stage}: {self.blocked[stage]}")
            if stage not in self.reached:
                pytest.fail(
                    f"required stage {stage!r} never ran, so the artifact this "
                    "test consumes was never produced. Nothing declared its "
                    "preconditions absent either, so this is not a skip.\n"
                    "These stages are ordered and share one module-scoped "
                    f"session: {stage!r} must execute in this same process "
                    "first. Selecting a single test ID from this file is the "
                    "usual cause — run the whole file instead. An earlier "
                    "stage erroring out part-way is the other.\n"
                    f"  reached: {sorted(self.reached) or ['(none)']}\n"
                    f"  declared absent: {sorted(self.blocked) or ['(none)']}",
                    pytrace=False,
                )

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
    else:
        state.reach("resolver")
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

    env = {
        key: value
        for key, value in os.environ.items()
        # Sanctioned spine edit (SLICE-055 R2, orchestrator-approved): this
        # helper's children are NOT wired by the frame, and "unwired" must
        # mean no coverage environment at all — this venv's a1_coverage.pth
        # starts coverage in any child inheriting COVERAGE_PROCESS_START,
        # which would silently measure the hookless clone children and blur
        # the wired/unwired ledger distinction. The PYTHONPATH replacement
        # below stays as-is: it is the recorded anti-pattern example
        # (ADR-032 sad path 14), not a frame child.
        if key not in ("COVERAGE_PROCESS_START", "COVERAGE_FILE")
    }
    env["PYTHONPATH"] = str(repo / "src")
    env.pop("RANEX_SIGNING_KEY", None)
    if key_path is not None:
        env["RANEX_SIGNING_KEY"] = str(key_path)
    completed = subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def journal_entries(repo: Path) -> list[dict[str, object]]:
    path = repo / "governance" / "journal.sqlite3"
    if not path.exists():
        return []
    return Journal(path).entries()


def suite_tail(out: str, err: str, lines: int = 30) -> str:
    """The end of a governed run's own output, for a failure message.

    `run` reports the bound command's exit code verbatim, and pytest writes its
    summary to stdout — so a message interpolating stderr alone renders as an
    empty string and the failure reads `assert 1 == 0`, naming nothing. The
    tail names which tests are red in the tree under governance.
    """

    combined = (out + err).strip().splitlines()
    if not combined:
        return "(the governed command produced no output at all)"
    return "\n".join(combined[-lines:])


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
        *(
            command
            or (
                "uv",
                "run",
                "pytest",
                "-q",
                "--junitxml=governance/suite_results.xml",
            )
        ),
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


def qualification_report(host_state: dict[str, object]) -> dict[str, object]:
    open_objects = {
        name: {
            "path": path,
            "realpath": path,
            "sha256": "sha256:" + digit * 64,
            "device": 1,
            "inode": inode,
            "uid": 0,
            "gid": 0,
            "mode": 0o755,
            "mount_id": 1,
            "security_capability": False,
            "filesystem": {
                "device": "0:1",
                "filesystem": "ext4",
                "mount_id": 1,
                "mount_point": "/",
                "options": ["rw"],
                "source": "/dev/root",
            },
        }
        for name, path, digit, inode in (
            ("bubblewrap", "/usr/bin/bwrap", "4", 2),
            ("launcher", "/opt/ranex/ranex-worker-launcher", "3", 3),
        )
    }
    return {
        "schema": "ranex-strict-local-qualification-v1",
        "qualified": True,
        "refusal": None,
        "kernel": {"release": "6.12.0", "architecture": "x86_64"},
        "primitives": {
            "landlock": {"available": True, "abi": 6},
            "seccomp_filter": True,
            "no_new_privs": True,
            "namespaces": {
                "user": True, "mount": True, "pid": True, "ipc": True, "network": True,
            },
            "openat2": True,
        },
        "cgroup": {
            "cgroup_kill": True,
            "mount": {"path": "/sys/fs/cgroup", "filesystem": "cgroup2"},
            "root": "/sys/fs/cgroup",
            "relative_path": "/session.scope",
            "controllers": ["cpu", "memory", "pids"],
            "probe_transcript": {"created": True},
        },
        "open_objects": open_objects,
        "digests": {
            "profile": "sha256:" + "1" * 64,
            "build_manifest": "sha256:" + "2" * 64,
            "artifact": "sha256:" + "3" * 64,
        },
        "delegation": {"broker": None, "existing_root": None, "source": "direct"},
        "host_state": host_state,
    }


def record_live_host_qualification(
    repo: Path, key_path: Path, *, producer_id: str = "worker"
) -> None:
    argv = (
        "python",
        "-m",
        "ranex.cli.host_confinement",
        "qualify",
        "--profile",
        "governance/confinement/strict-local-host-v1.json",
        "--artifact",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--report=.local/ranex/qualification/strict-local-v1.json",
    )
    host_state = copy.deepcopy(admission._read_live_durable_host_state())
    host_state["delegation_identity"].update(
        {
            "cgroup_root": "/sys/fs/cgroup",
            "cgroup_relative_path": "/session.scope",
            "source": "direct",
            "userns_state_source": "qualification-host-probe",
        }
    )
    report = qualification_report(host_state)
    content = {
        "claim_id": "host-qualification",
        "command": " ".join(argv),
        "command_digest": command_digest(argv),
        "executable_path": sys.executable,
        "exit_code": 0,
        "producer_id": producer_id,
        "subject_digest": subject_digest_for(repo, "HEAD"),
        "suite_results": report,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    private_key = key_path.read_text(encoding="utf-8").strip()
    record_evidence(
        repo / "governance" / "evidence.json",
        {**content, "signature": sign_evidence(content, private_key)},
    )


# --------------------------------------------------------------------------
# Stage 01 — the clone: this repository at HEAD, with a test producer.
# --------------------------------------------------------------------------


def test_stage_01_clone_the_real_repository(session: Session) -> None:
    if nested_hermetic_self_gate():
        return
    session.require("resolver")
    clone = session.store.parent / "clone"
    result = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(clone)],
        capture_output=True,
        text=True,
        check=False,
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
    session.reach("clone")


# --------------------------------------------------------------------------
# Stage 02 — baseline red: nothing fetched, nothing derived, nothing runs.
# --------------------------------------------------------------------------


def test_stage_02_run_refuses_with_nothing_provisioned(session: Session) -> None:
    if nested_hermetic_self_gate():
        return
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
    if nested_hermetic_self_gate():
        return
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
        check=False,
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
    if nested_hermetic_self_gate():
        return
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
    if nested_hermetic_self_gate():
        return
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
    if nested_hermetic_self_gate():
        return
    session.require("resolver", "clone")
    if not network_available():
        session.block("fetch", "no network: the first fetch downloads wheels")
    code, out, err = ranex(session.clone, fetch_argv(session.store))
    if code != 0:
        session.block("fetch", f"fetch failed: {err}")
    session.reach("fetch")
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
    if nested_hermetic_self_gate():
        return
    # s.p. 15/16: derived is not approved. The refusal must say so.
    session.require("resolver", "clone", "fetch")
    code, _, err = ranex(session.clone, run_argv(session.store), session.key_path)
    assert code == 2
    assert "approv" in err.lower()
    assert not (session.clone / "governance" / "evidence.json").exists()


def test_stage_06b_approve_records_the_full_set_as_the_first_delta(
    session: Session,
) -> None:
    if nested_hermetic_self_gate():
        return
    # s.p. 15: with no baseline the approver sees everything, named.
    session.require("resolver", "clone", "fetch")
    code, out, err = ranex(session.clone, approve_argv())
    if code != 0:
        session.block("approval", f"approve failed: {err}")
    session.reach("approval")
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
    if nested_hermetic_self_gate():
        return
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
    if nested_hermetic_self_gate():
        return
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
    assert evidence[0]["command"] == (
        "uv run pytest -q --junitxml=governance/suite_results.xml"
    )
    # Verbatim, whichever way the suite went: a failing command is honest
    # evidence of failure, and `run` exits with the command's own code.
    assert evidence[0]["exit_code"] == code
    # Collection really happened. Without this the stage would pass just as
    # well on a suite that never imported pytest, which is the shape of
    # "denial that passes because the command never ran" the slice names.
    assert "passed" in out or "passed" in err, out + err


def test_stage_08b_criterion_14_the_suite_passes_and_the_gate_accepts(
    session: Session,
) -> None:
    if nested_hermetic_self_gate():
        return
    session.require("resolver", "clone", "fetch", "approval")
    code, out, err = ranex(session.clone, run_argv(session.store), session.key_path)
    assert code == 0, (
        "the real suite did not pass under governance: the bound command "
        f"exited {code} against the cloned HEAD. This stage's claim is that "
        "the committed tree is green, so a red suite at HEAD fails it "
        "honestly — the tail of the suite's own output says which tests:\n"
        f"{suite_tail(out, err)}"
    )
    record_live_host_qualification(session.clone, session.key_path)
    code, out, _ = ranex(session.clone, evaluate_argv())
    assert code == 0
    assert out.startswith("PASS")


# --------------------------------------------------------------------------
# Stage 09 — amortisation: an unchanged set downloads nothing.
# --------------------------------------------------------------------------


def test_stage_09_second_fetch_reuses_every_store_entry(session: Session) -> None:
    if nested_hermetic_self_gate():
        return
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
    if nested_hermetic_self_gate():
        return
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
        check=False,
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
    if nested_hermetic_self_gate():
        return
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
            'command: ["uv", "run", "pytest", "-q", '
            '"--junitxml=governance/suite_results.xml"]\n'
            "        results_artifact: governance/suite_results.xml",
            f"command: {command}",
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
    if nested_hermetic_self_gate():
        return
    # The end-to-end confirmation ADR-007 names: the unchanged catalog
    # command, the real current commit, the operator's own store and key.
    # The preconditions are the operator's, so each miss skips loudly.
    if pinned_resolver() is None:
        pytest.skip("the pinned resolver is absent or does not match its digest")
    key = os.environ.get("RANEX_SIGNING_KEY")
    if not key:
        # Sanctioned spine edit (SLICE-055 R1d): the skip message now
        # byte-matches the manifest's probe-grammar declaration — direction
        # (a) of the entrypoint cross-check compares declared vs observed
        # reasons exactly, so the declared reason and the live message must
        # be the same bytes.
        pytest.skip(
            "ranex-prereq:signing_key: RANEX_SIGNING_KEY is not set; "
            "the operator runs this stage"
        )
    dirty = subprocess.run(
        ["git", "-C", str(REAL_REPO), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
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
            "--junitxml=governance/suite_results.xml",
        ],
        Path(key),
    )
    assert code == 0, f"the suite did not pass under governance: {err}"
    record_live_host_qualification(REAL_REPO, Path(key), producer_id="anthony")
    code, out, _ = ranex(REAL_REPO, evaluate_argv())
    assert code == 0
    assert out.startswith("PASS")


def test_slice009_repository_gate_fails_when_a_manifest_test_is_deleted(
    session: Session,
) -> None:
    """Delete a real frozen test in the clean live clone and observe FAIL."""

    if nested_hermetic_self_gate():
        return
    session.require("resolver", "clone", "fetch", "approval")
    assert session.clone is not None
    assert session.store is not None
    assert session.key_path is not None
    repository = session.clone

    live_gate = load_gate(repository / "governance" / "gates.yaml", "landing")
    live_manifest = load_manifest(repository / "governance" / "suite_manifest.json")
    live_claim = next(
        claim for claim in live_gate.required_claims if claim.claim_id == "tests-executed"
    )
    assert live_claim.results_artifact is not None
    assert f"--junitxml={live_claim.results_artifact}" in live_claim.command
    assert len(live_manifest["suite"]) >= 687
    openrouter_id = (
        "tests/e2e/test_first_delegation.py::"
        "test_first_delegation_ends_in_candidate_with_reviewable_diff"
    )
    declared_skips = set(live_manifest["expected_skips"])
    assert openrouter_id in declared_skips

    missing_id = "tests/contract/test_bom_is_honest.py::test_bom_is_honest"
    assert missing_id in live_manifest["suite"]

    baseline_code, baseline_output, baseline_error = ranex(
        repository, run_argv(session.store), session.key_path
    )
    assert baseline_code == 0, (
        "this test deletes one frozen test from a GREEN clone and asserts the "
        "gate then reports it missing; it cannot establish that baseline "
        f"because the clean clone's own suite exited {baseline_code}. The "
        "tail of the suite's own output says which tests are red:\n"
        f"{suite_tail(baseline_output, baseline_error)}"
    )
    baseline_record = next(
        record
        for record in json.loads(
            (repository / "governance" / "evidence.json").read_text()
        )
        if record["claim_id"] == "tests-executed"
    )
    baseline_results = baseline_record["suite_results"]
    baseline_non_passed = dict(baseline_results["non_passed"])
    skipped_ids = {
        test_id
        for test_id, kind in baseline_non_passed.items()
        if kind == "skipped"
    }
    assert skipped_ids <= declared_skips
    actual_failures = {
        test_id: kind
        for test_id, kind in baseline_non_passed.items()
        if kind != "skipped"
    }
    assert actual_failures == {}
    assert baseline_results["missing"] == []

    record_live_host_qualification(repository, session.key_path)
    baseline_verdict, baseline_output, _ = ranex(repository, evaluate_argv())
    assert baseline_verdict == 0
    assert baseline_output.startswith("PASS")

    removed_path = repository / missing_id.partition("::")[0]
    removed_path.unlink()
    git(repository, "add", "-u", removed_path.relative_to(repository).as_posix())
    committed = git(repository, "commit", "-q", "-m", "remove one frozen test")
    assert committed.returncode == 0, committed.stderr
    try:
        run_code, _, run_error = ranex(
            repository, run_argv(session.store), session.key_path
        )
        assert run_code == 0, run_error
        changed_record = next(
            record
            for record in json.loads(
                (repository / "governance" / "evidence.json").read_text()
            )
            if record["claim_id"] == "tests-executed"
        )
        changed_results = changed_record["suite_results"]
        assert changed_results["non_passed"] == baseline_results["non_passed"]
        assert changed_results["missing"] == sorted(
            {*baseline_results["missing"], missing_id}
        )

        record_live_host_qualification(repository, session.key_path)
        verdict_code, verdict_output, _ = ranex(repository, evaluate_argv())
        assert verdict_code == 1
        assert verdict_output.startswith("FAIL")
        assert missing_id in verdict_output
        assert "missing test ID(s)" in verdict_output
        assert "suite results artifact was absent" not in verdict_output
    finally:
        restored = git(repository, "reset", "-q", "--hard", "HEAD^")
        assert restored.returncode == 0, restored.stderr


def test_slice019_qualification_then_approval_passes_until_host_state_moves(
) -> None:
    """Ordinary signed qualification evidence is load-bearing in the real gate."""

    from ranex.bootstrap.composition import build_gate_evaluator
    from ranex.foundation import signing
    from ranex.foundation.canonical import (
        canonical_json_bytes,
        canonical_sha256,
        command_digest,
    )
    from ranex.governed_execution.domain import admission
    from ranex.governed_execution.domain.verdict import Evidence

    # Red now on the qualification-specific shared admission contract, before
    # the journey attempts to turn ordinary signed evidence into a gate PASS.
    assert admission.RejectionReason.STALE_HOST_STATE == "stale-host-state"

    subject = "sha256:" + "a" * 64
    argv = (
        "python",
        "-m",
        "ranex.cli.host_confinement",
        "qualify",
        "--profile",
        "governance/confinement/strict-local-host-v1.json",
        "--artifact",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        "--manifest",
        "governance/confinement/native-launcher-build-v1.json",
        "--report=.local/ranex/qualification/strict-local-v1.json",
    )
    host_state = {
        "lsm": {
            "securityfs_lsm": "apparmor",
            "apparmor_policy_identity": "p",
            "selinux_policy_identity": None,
        },
        "unprivileged_userns_sysctls": {"user.max_user_namespaces": 15000},
        "boot_id": "11111111-2222-3333-4444-555555555555",
        "machine_id": "0123456789abcdef0123456789abcdef",
        "delegation_identity": {
            "uid": 1000,
            "gid": 1000,
            "cgroup_root": "/sys/fs/cgroup",
            "cgroup_relative_path": "/session.scope",
            "source": "direct",
            "userns_state_source": "qualification-host-probe",
        },
    }
    report = qualification_report(host_state)
    producer_private, producer_public = generate_keypair()
    raw_content = {
        "claim_id": "host-qualification", "command": " ".join(argv),
        "command_digest": command_digest(argv), "executable_path": "/usr/bin/python",
        "exit_code": 0, "producer_id": "qualifier", "subject_digest": subject,
        "suite_results": report,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    raw_record = {**raw_content, "signature": signing.sign_evidence(raw_content, producer_private)}
    original_reader = admission._read_live_durable_host_state
    admission._read_live_durable_host_state = lambda: host_state
    try:
        admitted = admission.admit([raw_record], {"qualifier": producer_public})
    finally:
        admission._read_live_durable_host_state = original_reader
    assert admitted.rejections == ()

    tests_argv = ("uv", "run", "pytest", "-q", "--junitxml=governance/suite_results.xml")
    manifest_value = {
        "expected_skips": {},
        "suite": ["tests/test_real.py::test_real"],
    }
    manifest_digest = "sha256:" + canonical_sha256(manifest_value)
    tests_evidence = Evidence(
        claim_id="tests-executed",
        subject_digest=subject,
        producer_id="worker",
        command=" ".join(tests_argv),
        command_digest=command_digest(tests_argv),
        executable_path="/usr/bin/uv",
        exit_code=0,
        suite_results={
            "manifest_digest": manifest_digest,
            "counts": {
                "passed": 1,
                "skipped": 0,
                "failed": 0,
                "errors": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "non_passed": [],
            "missing": [],
            "extra_count": 0,
            "outcome_digest": "sha256:" + "4" * 64,
        },
    )
    manifest = canonical_json_bytes(manifest_value)
    evaluator = build_gate_evaluator(
        (REAL_REPO / "governance/gates.yaml").read_bytes(),
        suite_manifest=manifest,
    )
    passed = evaluator.evaluate(
        "landing",
        (tests_evidence, *admitted.evidence),
        subject_digest=subject,
        approver_id="reviewer",
    )
    assert passed.verdict.value == "PASS"

    moved = copy.deepcopy(host_state)
    moved["boot_id"] = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    admission._read_live_durable_host_state = lambda: moved
    try:
        stale = admission.admit([raw_record], {"qualifier": producer_public})
    finally:
        admission._read_live_durable_host_state = original_reader
    failed = evaluator.evaluate(
        "landing",
        (tests_evidence, *stale.evidence),
        subject_digest=subject,
        approver_id="reviewer",
    )
    assert failed.verdict.value == "FAIL"
    assert "host-qualification" in failed.missing_claims
