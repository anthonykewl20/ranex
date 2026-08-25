"""Frozen RED real CLI journey for SLICE-036.

This test never imports the batch application.  Every product observation
crosses ``python -m ranex.cli.main task batch qualify`` in a subprocess, and
all safety claims are re-read through Git, stdlib sqlite3, the filesystem,
hashlib, os.kill, or a real host-loopback listener.

The fixed 5586d68/34fa pair is this E2E fixture's exact approved subject.  It
does not restrict a production command to the Ranex repository or this commit.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shlex
import shutil
import socket
import sqlite3
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import _prereqs
import pytest

from ranex.foundation.canonical import (
    canonical_json_bytes,
    canonical_sha256,
    command_digest,
)
from ranex.governed_execution.domain.admission import admit
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    load_keyring_text,
)

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests/contract/fixtures/specification"
EXPECTED = ROOT / "tests/e2e/expected"
VECTORS = json.loads(
    (FIXTURES / "approved-batch-v1-vectors.json").read_text(encoding="utf-8")
)
DESCRIPTOR = json.loads(
    (FIXTURES / "approved-batch-v1.json").read_text(encoding="utf-8")
)
BASE_COMMIT = "5586d68b0936f554759022caabe847087f1d03ef"
SUBJECT_DIGEST = "sha256:34fa645d616fc0b0383d424573d60a447ddd829e8891b7f992b809be9a783953"
PORTS = range(46120, 46136)
SURVIVOR_TOKEN = b"ranex-slice036-survivor-control-v1"


@dataclass(frozen=True)
class DevelopmentSource:
    manifest_digest: str
    module_path: Path
    pythonpath: Path


def run(
    *argv: str,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(argv),
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


def git(repository: Path, *argv: str) -> str:
    completed = run("git", "-C", str(repository), *argv)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def journal_snapshot(path: Path) -> tuple[int, str | None]:
    if not path.exists():
        return 0, None
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS count, "
            "(SELECT link FROM evaluations ORDER BY seq DESC LIMIT 1) AS head "
            "FROM evaluations"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return int(row[0]), row[1]


def worktree_snapshot(target: Path) -> tuple[str, ...]:
    completed = run("git", "-C", str(target), "worktree", "list", "--porcelain")
    assert completed.returncode == 0, completed.stderr
    return tuple(
        line.removeprefix("worktree ")
        for line in completed.stdout.splitlines()
        if line.startswith("worktree ")
    )


def filesystem_snapshot(root: Path) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, "symlink:" + os.readlink(path)))
        elif path.is_file():
            rows.append((relative, file_digest(path)))
        elif path.is_dir():
            rows.append((relative, "directory"))
    return tuple(rows)


def source_manifest(root: Path) -> dict[str, object]:
    files = []
    source = root / "src/ranex"
    for path in sorted(source.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "digest": file_digest(path),
            }
        )
    return {"files": files}


def source_manifest_digest(root: Path) -> str:
    """Hash the manifest with stdlib JSON, independently of the product CLI."""

    payload = json.dumps(
        source_manifest(root),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def survivor_pids() -> set[int]:
    """Observe the planted process independently of qualifier output."""

    observed: set[int] = set()
    for candidate in Path("/proc").iterdir():
        if not candidate.name.isdigit():
            continue
        try:
            command = (candidate / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if SURVIVOR_TOKEN in command:
            observed.add(int(candidate.name))
    return observed


@dataclass
class LoopbackSentinel:
    listener: socket.socket
    port: int
    accepted: list[tuple[str, int]] = field(default_factory=list)
    stopped: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None

    @classmethod
    def start(cls) -> LoopbackSentinel:
        for port in PORTS:
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(("127.0.0.1", port))
            except OSError:
                listener.close()
                continue
            listener.listen()
            listener.settimeout(0.05)
            sentinel = cls(listener, port)

            def accept(
                active: LoopbackSentinel = sentinel,
                server: socket.socket = listener,
            ) -> None:
                while not active.stopped.is_set():
                    try:
                        connection, address = server.accept()
                    except TimeoutError:
                        continue
                    except OSError:
                        break
                    with connection:
                        active.accepted.append(address)

            sentinel.thread = threading.Thread(target=accept, daemon=True)
            sentinel.thread.start()
            return sentinel
        raise AssertionError("no loopback sentinel port is available")

    def calibrate(self) -> None:
        with socket.create_connection(("127.0.0.1", self.port), timeout=1):
            pass
        for _ in range(100):
            if self.accepted:
                return
            threading.Event().wait(0.01)
        raise AssertionError("the real loopback listener did not observe calibration")

    def close(self) -> None:
        self.stopped.set()
        self.listener.close()
        if self.thread is not None:
            self.thread.join(timeout=1)


@pytest.fixture()
def loopback_sentinel() -> LoopbackSentinel:
    sentinel = LoopbackSentinel.start()
    sentinel.calibrate()
    yield sentinel
    sentinel.close()


def materialize_governed_checkout(path: Path) -> Path:
    """Build the one unmodified repository qualified and publication-refused."""

    completed = run("git", "clone", "--quiet", str(ROOT), str(path))
    assert completed.returncode == 0, completed.stderr
    git(path, "checkout", "--quiet", "-B", "main", BASE_COMMIT)
    assert git(path, "rev-parse", "HEAD") == BASE_COMMIT
    assert git(path, "rev-parse", "refs/heads/main") == BASE_COMMIT
    tree = git(path, "rev-parse", f"{BASE_COMMIT}^{{tree}}")
    assert "sha256:" + canonical_sha256({"tree": tree}) == SUBJECT_DIGEST
    assert git(path, "status", "--porcelain") == ""
    assert path.resolve() != ROOT.resolve()
    return path


def materialize_signing_key(path: Path) -> Path:
    """Write the deterministic non-secret fixture key outside every repository."""

    private = "ed25519:" + base64.b64encode(bytes(range(32))).decode("ascii")
    path.write_text(private, encoding="utf-8")
    path.chmod(0o600)
    return path


def materialize_authority(path: Path) -> tuple[Path, Path, Path]:
    path.mkdir(parents=True)
    triple = VECTORS["triple"]
    a = path / "spec-packet.json"
    b = path / "artifact-manifest.json"
    c = path / "approval-envelope.json"
    a.write_bytes(canonical_json_bytes(triple["a"]))
    b.write_bytes(canonical_json_bytes(triple["b"]))
    c.write_bytes(
        canonical_json_bytes(
            {
                "version": "approval-envelope-v1",
                "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
                "payload": triple["c_payload"],
                "key_id": triple["key_id"],
                "signature": triple["signature"],
            }
        )
    )
    return a, b, c


def cli_environment(
    *,
    development_source: Path = ROOT / "src",
    signing_key: Path | None = None,
) -> dict[str, str]:
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    source = development_source.resolve()
    assert source.is_absolute() and source == (ROOT / "src").resolve()
    environment["PYTHONPATH"] = str(source)
    if signing_key is not None:
        environment["RANEX_SIGNING_KEY"] = str(signing_key.resolve())
    return environment


def observe_development_source(governed: Path) -> tuple[DevelopmentSource, str]:
    """Resolve the exact imported CLI module and hash every executed source byte."""

    pythonpath = (ROOT / "src").resolve()
    expected_module = (pythonpath / "ranex/cli/main.py").resolve()
    completed = run(
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-c",
        "from pathlib import Path; import ranex.cli.main; "
        "print(Path(ranex.cli.main.__file__).resolve())",
        cwd=governed,
        env=cli_environment(development_source=pythonpath),
    )
    assert completed.returncode == 0, completed.stderr
    observed_module = Path(completed.stdout.strip())
    assert observed_module == expected_module
    source = DevelopmentSource(
        manifest_digest=source_manifest_digest(ROOT),
        module_path=observed_module,
        pythonpath=pythonpath,
    )
    record = {
        "event": "development.source",
        "manifest_digest": source.manifest_digest,
        "module_path": str(source.module_path),
        "pythonpath": str(source.pythonpath),
        "version": "slice036-development-source-v1",
    }
    return source, canonical_json_bytes(record).decode("utf-8") + "\n"


def qualify_command(
    *,
    authority: tuple[Path, Path, Path],
    target: Path,
    journal: Path,
    outcome: Path,
    pool: int = 2,
    descriptor: Path = FIXTURES / "approved-batch-v1.json",
    tasks: Path = FIXTURES / "approved-batch-child-requests-v1.jsonl",
) -> list[str]:
    a, b, c = authority
    return [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "batch",
        "qualify",
        "--spec-packet",
        str(a),
        "--artifact-manifest",
        str(b),
        "--approval-envelope",
        str(c),
        "--descriptor",
        str(descriptor),
        "--tasks",
        str(tasks),
        "--target",
        str(target),
        "--journal",
        str(journal),
        "--outcome-dir",
        str(outcome),
        "--pool",
        str(pool),
    ]


def invoke(
    command: list[str],
    *,
    checkout: Path = ROOT,
    signing_key: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    return run(
        *command,
        cwd=checkout,
        env=cli_environment(signing_key=signing_key),
    )


def compare_golden(actual: str, name: str, sandbox: Path) -> None:
    del sandbox  # every family uses the one argument-free-mask frame normalizer
    expected = (EXPECTED / name).read_text(encoding="utf-8")
    assert _prereqs.normalize_transcript(expected) == expected
    try:
        _prereqs.compare_transcript(
            _prereqs.normalize_transcript(actual),
            expected,
            family=name.removesuffix(".out"),
        )
    except AssertionError as exc:
        raise AssertionError(f"normalized transcript differs from {name}: {exc}") from exc


def verify_actual_qualification(
    path: Path,
    *,
    command: list[str],
    journal: Path,
    evidence_events: dict[str, str],
) -> tuple[dict[str, object], str]:
    """Verify actual output with canonical JSON, the keyring loader, and admission."""

    raw = path.read_bytes()
    governed = Path(command[command.index("--target") + 1]).resolve()
    assert journal.resolve() == governed / "governance/journal.sqlite3"
    assert git(governed, "rev-parse", "refs/heads/main") == BASE_COMMIT
    artifact = json.loads(raw)
    assert raw == canonical_json_bytes(artifact)
    assert set(artifact) == {"attestation", "payload", "version"}
    assert artifact["version"] == "batch-qualification-v1"
    payload = artifact["payload"]
    assert isinstance(payload, dict)
    assert payload["version"] == "batch-qualification-payload-v1"
    assert payload["publication_allowed"] is False
    assert payload["producer_id"] == DESCRIPTOR["qualification_output"]["producer_id"]

    identities = {
        "a_digest": VECTORS["triple"]["a_digest"],
        "b_digest": VECTORS["triple"]["b_digest"],
        "base_commit": BASE_COMMIT,
        "base_digest": SUBJECT_DIGEST,
        "c_digest": VECTORS["triple"]["c_digest"],
        "child_requests_digest": VECTORS["digests"]["children"],
        "descriptor_digest": VECTORS["digests"]["descriptor"],
    }
    assert {name: payload[name] for name in identities} == identities
    assert payload["batch_digest"] == "sha256:" + canonical_sha256(identities)

    child_results = {
        "results": [
            {
                "task_id": relative.split("/")[1],
                "evidence_digest": digest,
            }
            for relative, digest in sorted(evidence_events.items())
        ]
    }
    assert payload["child_results_digest"] == (
        "sha256:" + canonical_sha256(child_results)
    )

    journal_fact = payload["qualification_journal"]
    assert isinstance(journal_fact, dict)
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT seq, record, prev_link, link FROM evaluations WHERE seq = ?",
            (journal_fact["seq"],),
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    seq, raw_record, previous_head, head = row
    record = json.loads(raw_record)
    assert record["type"] == "batch-qualified"
    assert journal_fact == {
        "seq": seq,
        "previous_head": previous_head,
        "head": head,
    }
    assert head == "sha256:" + canonical_sha256(
        {"prev_link": previous_head, "record": record}
    )
    assert payload["qualification_record_digest"] == (
        "sha256:" + canonical_sha256(record)
    )
    for field_name in (
        "a_digest",
        "b_digest",
        "base_commit",
        "base_digest",
        "batch_digest",
        "c_digest",
        "child_requests_digest",
        "child_results_digest",
        "descriptor_digest",
        "producer_id",
        "publication_allowed",
    ):
        assert record[field_name] == payload[field_name]

    attestation = artifact["attestation"]
    assert isinstance(attestation, dict)
    role = next(
        role
        for role in DESCRIPTOR["roles"]
        if role["principal"] == payload["producer_id"]
    )
    keyring = load_keyring_text(
        f"producers:\n  {payload['producer_id']}: {role['key']}\n",
        "approved-batch descriptor roles",
    )
    admission = admit([attestation], keyring)
    assert admission.rejections == ()
    assert len(admission.evidence) == 1
    evidence = admission.evidence[0]
    assert evidence.claim_id == DESCRIPTOR["qualification_output"]["claim_id"]
    assert evidence.subject_digest == SUBJECT_DIGEST
    signed_command = shlex.split(attestation["command"])
    assert signed_command == command[3:]
    assert attestation["command_digest"] == command_digest(signed_command)
    suite_results = attestation["suite_results"]
    assert suite_results["manifest_digest"] == VECTORS["digests"]["descriptor"]
    assert suite_results["outcome_digest"] == (
        "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    )
    assert suite_results["counts"] == {
        "errors": 0,
        "failed": 0,
        "passed": 3,
        "skipped": 0,
        "xfailed": 0,
        "xpassed": 0,
    }
    return artifact, file_digest(path)


def assert_pre_journal_refusal(
    command: list[str],
    *,
    code: str,
    sandbox: Path,
    target: Path,
    journal: Path,
    sentinel: LoopbackSentinel,
    checkout: Path,
    signing_key: Path,
) -> subprocess.CompletedProcess[str]:
    before = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    completed = invoke(command, checkout=checkout, signing_key=signing_key)
    assert completed.returncode != 0
    assert code in completed.stdout + completed.stderr
    after = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    assert after == before, f"{code} refusal produced a side effect"
    return completed


def assert_survivor_refusal(
    command: list[str],
    *,
    sandbox: Path,
    target: Path,
    journal: Path,
    sentinel: LoopbackSentinel,
    checkout: Path,
    signing_key: Path,
) -> None:
    """See the exact child process in /proc, then prove cleanup and no append."""

    before = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    process = subprocess.Popen(
        command,
        cwd=checkout,
        env=cli_environment(signing_key=signing_key),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    observed: set[int] = set()
    deadline = time.monotonic() + 15
    try:
        while process.poll() is None and time.monotonic() < deadline:
            observed.update(survivor_pids())
            time.sleep(0.01)
        stdout, stderr = process.communicate(timeout=120)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
    assert process.returncode != 0
    assert "E-BATCH-CHILD-SURVIVOR" in stdout + stderr
    assert observed, "the exact B-bound survivor argv was never observed in /proc"
    cleanup_deadline = time.monotonic() + 3
    while survivor_pids() & observed and time.monotonic() < cleanup_deadline:
        time.sleep(0.01)
    leaked = survivor_pids() & observed
    for pid in leaked:
        os.kill(pid, 9)
    assert not leaked, f"qualifier left child survivors: {sorted(leaked)}"
    after = (
        git(target, "rev-parse", "refs/heads/main"),
        journal_snapshot(journal),
        worktree_snapshot(target),
        filesystem_snapshot(sandbox),
        len(sentinel.accepted),
    )
    assert after == before, "survivor refusal produced a persistent side effect"


def test_real_cli_qualifies_both_orders_and_independently_proves_no_publication(
    tmp_path: Path,
    loopback_sentinel: LoopbackSentinel,
) -> None:
    """The decisive real journey: no application import and no trusted booleans."""

    sandbox = tmp_path / "slice036"
    sandbox.mkdir()
    governed = materialize_governed_checkout(sandbox / "governed")
    governed_source_before = source_manifest(governed)
    development_source, source_transcript = observe_development_source(governed)
    assert not development_source.module_path.is_relative_to(governed.resolve())
    provenance_record = {
        "governed_repository": str(governed.resolve()),
        "manifest_digest": development_source.manifest_digest,
        "module_path": str(development_source.module_path),
        "pythonpath": str(development_source.pythonpath),
        "version": "slice036-development-source-v1",
    }
    provenance_path = sandbox / "source-provenance.json"
    provenance_path.write_bytes(canonical_json_bytes(provenance_record))
    assert json.loads(provenance_path.read_bytes()) == provenance_record
    signing_key = materialize_signing_key(tmp_path / "slice036-owner.key")
    authority = materialize_authority(sandbox / "authority")
    journal = governed / "governance/journal.sqlite3"
    outcome = sandbox / "outcomes"
    ref_before = git(governed, "rev-parse", "refs/heads/main")
    worktrees_before = worktree_snapshot(governed)
    network_before = len(loopback_sentinel.accepted)

    positive_command = qualify_command(
        authority=authority,
        target=governed,
        journal=journal,
        outcome=outcome,
    )
    assert Path(positive_command[positive_command.index("--target") + 1]).resolve() == (
        governed.resolve()
    )
    assert journal.resolve() == governed.resolve() / "governance/journal.sqlite3"
    completed = invoke(
        positive_command,
        checkout=governed,
        signing_key=signing_key,
    )
    assert completed.returncode == 0, completed.stderr
    compare_golden(
        source_transcript + completed.stdout,
        "slice036-approved-batch-qualification.out",
        sandbox,
    )

    assert git(governed, "rev-parse", "refs/heads/main") == ref_before == BASE_COMMIT
    assert worktree_snapshot(governed) == worktrees_before
    assert git(governed, "status", "--porcelain") == ""
    assert source_manifest(governed) == governed_source_before
    assert len(loopback_sentinel.accepted) == network_before

    rows, head = journal_snapshot(journal)
    assert rows == 1 and isinstance(head, str) and head.startswith("sha256:")
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        record = json.loads(
            connection.execute(
                "SELECT record FROM evaluations ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
        )
    finally:
        connection.close()
    assert record["type"] == "batch-qualified"
    assert record["base_commit"] == BASE_COMMIT
    assert record["base_digest"] == SUBJECT_DIGEST

    evidence_events = {
        event["path"]: event["digest"]
        for event in map(json.loads, completed.stdout.splitlines())
        if event["event"] == "batch.evidence"
    }
    expected_evidence = {
        row["path"]
        for child in (
            json.loads(line)
            for line in (FIXTURES / "approved-batch-child-requests-v1.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
        for row in child["evidence"]
    }
    assert set(evidence_events) == expected_evidence
    for relative, reported_digest in evidence_events.items():
        evidence = outcome / relative
        assert evidence.is_file()
        assert file_digest(evidence) == reported_digest

    qualification_events = [
        event
        for event in map(json.loads, completed.stdout.splitlines())
        if event["event"] == "batch.qualification"
    ]
    assert len(qualification_events) == 1
    qualification_event = qualification_events[0]
    batch_artifact = outcome / DESCRIPTOR["qualification_output"]["path"]
    qualification, qualification_digest = verify_actual_qualification(
        batch_artifact,
        command=positive_command,
        journal=journal,
        evidence_events=evidence_events,
    )
    assert qualification_event == {
        "digest": qualification_digest,
        "event": "batch.qualification",
        "path": DESCRIPTOR["qualification_output"]["path"],
        "producer_id": DESCRIPTOR["qualification_output"]["producer_id"],
    }
    assert qualification["payload"]["qualification_journal"]["head"] == head

    # Each control below is a separately B-protected child-input artifact and
    # enters only through the real public CLI.  No helper receives a post-hoc
    # failure boolean and no application result is trusted as the observer.
    protected = {
        row["path"]: row["digest"]
        for row in VECTORS["triple"]["b"]["artifacts"]["protected"]
    }
    public_controls = (
        ("unapproved_rows", "E-BATCH-UNAPPROVED-ROW"),
        ("overlap_rows", "E-BATCH-SCOPE-OVERLAP"),
        ("network_rows", "E-BATCH-NETWORK-ESCAPE"),
        ("oracle_mismatch_rows", "E-BATCH-ORACLE-MISMATCH"),
    )
    for ordinal, (fixture_name, code) in enumerate(public_controls, start=1):
        relative = VECTORS["paths"][fixture_name]
        tasks = ROOT / relative
        assert file_digest(tasks) == protected[relative]
        control_journal = sandbox / f"public-control-{ordinal}.sqlite3"
        control_outcome = sandbox / f"public-control-{ordinal}"
        assert_pre_journal_refusal(
            qualify_command(
                authority=authority,
                target=governed,
                journal=control_journal,
                outcome=control_outcome,
                tasks=tasks,
            ),
            code=code,
            sandbox=sandbox,
            target=governed,
            journal=control_journal,
            sentinel=loopback_sentinel,
            checkout=governed,
            signing_key=signing_key,
        )

    survivor_relative = VECTORS["paths"]["survivor_rows"]
    survivor_tasks = ROOT / survivor_relative
    assert file_digest(survivor_tasks) == protected[survivor_relative]
    assert_survivor_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=sandbox / "survivor-refusal.sqlite3",
            outcome=sandbox / "survivor-refusal",
            tasks=survivor_tasks,
        ),
        sandbox=sandbox,
        target=governed,
        journal=sandbox / "survivor-refusal.sqlite3",
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )

    # Calibration proves the golden comparator itself detects changed bytes.
    with pytest.raises(AssertionError, match="normalized transcript differs"):
        compare_golden(
            source_transcript
            + completed.stdout.replace('"publication":false', '"publication":true'),
            "slice036-approved-batch-qualification.out",
            sandbox,
        )

    # Stale C/journal predecessor is known before execution and leaves even the
    # successful outcome bytes untouched.
    assert_pre_journal_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=journal,
            outcome=outcome,
        ),
        code="E-BATCH-STALE-BASE",
        sandbox=sandbox,
        target=governed,
        journal=journal,
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )

    # Pool widening and protected-byte substitution each use fresh absent
    # journals, and independent snapshots prove the refusal precedes writes.
    pool_journal = sandbox / "pool-refusal.sqlite3"
    pool_outcome = sandbox / "pool-refusal"
    assert_pre_journal_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=pool_journal,
            outcome=pool_outcome,
            pool=3,
        ),
        code="E-BATCH-POOL-EXCEEDS",
        sandbox=sandbox,
        target=governed,
        journal=pool_journal,
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )
    tampered = sandbox / "tampered-descriptor.json"
    tampered_record = json.loads(
        (FIXTURES / "approved-batch-v1.json").read_text(encoding="utf-8")
    )
    tampered_record["maximum_pool"] = 1
    tampered.write_bytes(canonical_json_bytes(tampered_record))
    tamper_journal = sandbox / "tamper-refusal.sqlite3"
    tamper_outcome = sandbox / "tamper-refusal"
    assert_pre_journal_refusal(
        qualify_command(
            authority=authority,
            target=governed,
            journal=tamper_journal,
            outcome=tamper_outcome,
            descriptor=tampered,
        ),
        code="E-BATCH-PROTECTED-ARTIFACT",
        sandbox=sandbox,
        target=governed,
        journal=tamper_journal,
        sentinel=loopback_sentinel,
        checkout=governed,
        signing_key=signing_key,
    )

    # A moved real ref and a real surviving Git worktree are planted controls,
    # not values returned by the application under test.
    moved = git(governed, "rev-parse", f"{BASE_COMMIT}^")
    git(governed, "update-ref", "refs/heads/main", moved, BASE_COMMIT)
    moved_journal = sandbox / "moved-refusal.sqlite3"
    moved_outcome = sandbox / "moved-refusal"
    try:
        assert_pre_journal_refusal(
            qualify_command(
                authority=authority,
                target=governed,
                journal=moved_journal,
                outcome=moved_outcome,
            ),
            code="E-BATCH-STALE-BASE",
            sandbox=sandbox,
            target=governed,
            journal=moved_journal,
            sentinel=loopback_sentinel,
            checkout=governed,
            signing_key=signing_key,
        )
    finally:
        git(governed, "update-ref", "refs/heads/main", BASE_COMMIT, moved)

    rogue = sandbox / "rogue-worktree"
    assert run(
        "git", "-C", str(governed), "worktree", "add", "--quiet", "--detach", str(rogue), BASE_COMMIT
    ).returncode == 0
    residue_journal = sandbox / "residue-refusal.sqlite3"
    residue_outcome = sandbox / "residue-refusal"
    try:
        assert_pre_journal_refusal(
            qualify_command(
                authority=authority,
                target=governed,
                journal=residue_journal,
                outcome=residue_outcome,
            ),
            code="E-BATCH-WORKTREE-RESIDUE",
            sandbox=sandbox,
            target=governed,
            journal=residue_journal,
            sentinel=loopback_sentinel,
            checkout=governed,
            signing_key=signing_key,
        )
    finally:
        removal = run(
            "git", "-C", str(governed), "worktree", "remove", "--force", str(rogue)
        )
        assert removal.returncode == 0, removal.stderr

    # Judge/merge use the same disposable governed checkout and actual fixed
    # journal qualification already appended.  There is no unrelated database
    # and no second checkout with different source provenance.
    publication_journal = journal
    publication_worktree = sandbox / "publication-worktree"
    dispatch = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "dispatch",
        "--task-id",
        "SLICE-036-child-A",
        "--target",
        str(governed),
        "--worktree",
        str(publication_worktree),
        "--journal",
        str(publication_journal),
    ]
    dispatch_result = invoke(
        dispatch,
        checkout=governed,
        signing_key=signing_key,
    )
    assert dispatch_result.returncode == 0, dispatch_result.stderr
    assert Path(dispatch[dispatch.index("--target") + 1]).resolve() == governed.resolve()
    assert journal_snapshot(publication_journal)[0] == 2

    first_evidence = outcome / sorted(expected_evidence)[0]
    governed_evidence = publication_worktree / "governance/qualification/evidence.json"
    governed_evidence.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(first_evidence, governed_evidence)
    candidate = git(publication_worktree, "rev-parse", "HEAD")
    judge = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "judge",
        "--task-id",
        "SLICE-036-child-A",
        "--emitted-worktree",
        str(publication_worktree),
        "--emitted-commit",
        candidate,
        "--gate",
        "landing",
        "--gate-catalog",
        str(publication_worktree / "governance/gates.yaml"),
        "--evidence",
        str(governed_evidence),
        "--producers",
        str(publication_worktree / "governance/producers.yaml"),
        "--suite-manifest",
        str(publication_worktree / "governance/suite_manifest.json"),
        "--journal",
        str(publication_journal),
        "--batch-qualification",
        str(batch_artifact),
    ]
    merge = [
        shutil.which("uv") or "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.main",
        "task",
        "merge",
        "--task-id",
        "SLICE-036-child-A",
        "--target-ref",
        "refs/heads/main",
        "--candidate",
        candidate,
        "--approval",
        str(authority[2]),
        "--batch-qualification",
        str(batch_artifact),
    ]
    publication_before = (
        git(governed, "rev-parse", "refs/heads/main"),
        journal_snapshot(publication_journal),
        worktree_snapshot(governed),
        filesystem_snapshot(sandbox),
        len(loopback_sentinel.accepted),
        survivor_pids(),
    )
    judge_result = invoke(judge, checkout=governed, signing_key=signing_key)
    merge_result = invoke(merge, checkout=governed, signing_key=signing_key)
    assert judge_result.returncode != 0 and merge_result.returncode != 0
    transcript = (
        "task judge: " + judge_result.stderr.strip() + "\n"
        "task merge: " + merge_result.stderr.strip() + "\n"
    )
    compare_golden(
        transcript,
        "slice036-approved-batch-publication-refusal.out",
        sandbox,
    )
    assert (
        git(governed, "rev-parse", "refs/heads/main"),
        journal_snapshot(publication_journal),
        worktree_snapshot(governed),
        filesystem_snapshot(sandbox),
        len(loopback_sentinel.accepted),
        survivor_pids(),
    ) == publication_before
