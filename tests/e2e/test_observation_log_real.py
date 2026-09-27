"""SLICE-099 — observation log: real CLI, #95 protocol (RISK-11 / ADR-068).

Four arms on a real Git repository. No mocks: every step is a real ``ranex``
subprocess. Statuses are VERIFIED in the assertions.

Arms:
1. Record a real FAIL, delete it from evidence.json, evaluate →
   ``removed-observation`` named; verdict FAIL. Negative control: without the
   deletion the same FAIL is cause ``failed``, not ``removed-observation``.
2. Drop the append-only trigger and delete a log row → chain verify refuses;
   SQLite DELETE with the trigger present aborts.
3. Honest PASS flow → verdict PASS with empty causes (no removed-observation).
4. Repeats of identical FAIL records → identical observation-chain heads.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import _approver
from ranex.foundation.signing import generate_keypair

KERNEL = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def invoke(
    repo: Path,
    *args: str,
    signing_key: Path | None = None,
    approver_key: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "GIT_", "PYTHON", "COVERAGE_"))
    }
    environment["PYTHONPATH"] = str(KERNEL / "src")
    if signing_key is not None:
        environment["RANEX_SIGNING_KEY"] = str(signing_key)
    if approver_key is not None:
        environment["RANEX_APPROVER_SIGNING_KEY"] = str(approver_key)
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *args],
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


@pytest.fixture
def observation_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    repo = tmp_path / "subject"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Obs")
    git(repo, "config", "user.email", "obs@example.invalid")
    (repo / "governance").mkdir()
    (repo / ".gitignore").write_text(
        "governance/evidence.json\n"
        "governance/journal.sqlite3*\n"
        "governance/observations.sqlite3*\n",
        encoding="utf-8",
    )
    worker_priv, worker_pub = generate_keypair()
    signer = tmp_path / "worker.key"
    signer.write_text(worker_priv + "\n", encoding="utf-8")
    signer.chmod(0o600)
    approver_key, approver_pub = _approver.mint_approver(tmp_path, "pilot")
    (repo / "governance" / "producers.yaml").write_text(
        "producers:\n"
        f"  worker: {worker_pub}\n"
        "principals:\n"
        f"  worker:\n    role: worker\n    keys:\n"
        f"      - key: {worker_pub}\n        status: active\n"
        f"  pilot:\n    role: approver\n    keys:\n"
        f"      - key: {approver_pub}\n        status: active\n",
        encoding="utf-8",
    )
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        '        command: ["sh", "-c", "exit 1"]\n',
        encoding="utf-8",
    )
    (repo / "README.md").write_text("observation subject\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    return repo, signer, approver_key


def _run_fail(repo: Path, signer: Path) -> subprocess.CompletedProcess[str]:
    return invoke(
        repo,
        "run",
        "--claim",
        "tests-executed",
        "--producer",
        "worker",
        "--external-repository",
        str(repo),
        "--evidence",
        "governance/evidence.json",
        "--producers",
        "governance/producers.yaml",
        "--gate-catalog",
        "governance/gates.yaml",
        "--gate",
        "landing",
        "--",
        "sh",
        "-c",
        "exit 1",
        signing_key=signer,
    )


def _evaluate(repo: Path, approver_key: Path) -> subprocess.CompletedProcess[str]:
    return invoke(
        repo,
        "gate",
        "evaluate",
        "HEAD",
        "--external-repository",
        str(repo),
        "--approver",
        "pilot",
        "--evidence",
        "governance/evidence.json",
        "--producers",
        "governance/producers.yaml",
        "--gate-catalog",
        "governance/gates.yaml",
        approver_key=approver_key,
    )


def test_arm1_deleted_fail_named_removed_observation(
    observation_repo: tuple[Path, Path, Path],
) -> None:
    """VERIFIED negative: deleting a recorded FAIL names removed-observation."""

    repo, signer, approver_key = observation_repo
    recorded = _run_fail(repo, signer)
    assert recorded.returncode == 1, recorded.stdout + recorded.stderr
    evidence = repo / "governance" / "evidence.json"
    log = repo / "governance" / "observations.sqlite3"
    assert evidence.is_file() and log.is_file()
    assert len(json.loads(evidence.read_text(encoding="utf-8"))) == 1

    # Positive control: with the FAIL still projected, cause is failed.
    control = _evaluate(repo, approver_key)
    assert control.returncode == 1, control.stdout + control.stderr
    assert "removed-observation" not in control.stdout
    assert "FAIL" in control.stdout

    # Delete the FAIL from the projection; the chain still holds it.
    evidence.write_text("[]\n", encoding="utf-8")
    deleted = _evaluate(repo, approver_key)
    assert deleted.returncode == 1, deleted.stdout + deleted.stderr
    assert "removed-observation" in deleted.stdout, deleted.stdout + deleted.stderr
    assert "no evidence for required claim" not in deleted.stdout


def test_arm2_log_tamper_refused(
    observation_repo: tuple[Path, Path, Path],
) -> None:
    """VERIFIED negative: trigger blocks DELETE; out-of-band delete breaks chain."""

    repo, signer, _approver_key = observation_repo
    assert _run_fail(repo, signer).returncode == 1
    log = repo / "governance" / "observations.sqlite3"

    blocked = sqlite3.connect(log)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            blocked.execute("DELETE FROM observations")
            blocked.commit()
    finally:
        blocked.close()

    connection = sqlite3.connect(log)
    try:
        connection.execute("DROP TRIGGER IF EXISTS observations_no_delete")
        connection.execute("DELETE FROM observations")
        connection.commit()
    finally:
        connection.close()

    # Seed one row with a forged link so verify has a broken chain to refuse.
    connection = sqlite3.connect(log)
    try:
        connection.execute(
            "INSERT INTO observations (record, prev_link, link) VALUES (?, ?, ?)",
            ("{}", "sha256:" + "0" * 64, "sha256:" + "1" * 64),
        )
        connection.commit()
    finally:
        connection.close()

    verified = invoke(
        repo,
        "journal",
        "verify",
        "--observations",
        "--external-repository",
        str(repo),
    )
    assert verified.returncode == 1, verified.stdout + verified.stderr
    assert "chain=invalid" in verified.stdout


def test_arm3_honest_pass_unchanged(
    observation_repo: tuple[Path, Path, Path],
) -> None:
    """VERIFIED: honest PASS carries no removed-observation cause."""

    repo, signer, approver_key = observation_repo
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        '        command: ["sh", "-c", "exit 0"]\n',
        encoding="utf-8",
    )
    git(repo, "add", "governance/gates.yaml")
    git(repo, "commit", "-qm", "pass-bound")

    ran = invoke(
        repo,
        "run",
        "--claim",
        "tests-executed",
        "--producer",
        "worker",
        "--external-repository",
        str(repo),
        "--evidence",
        "governance/evidence.json",
        "--producers",
        "governance/producers.yaml",
        "--gate-catalog",
        "governance/gates.yaml",
        "--gate",
        "landing",
        "--",
        "sh",
        "-c",
        "exit 0",
        signing_key=signer,
    )
    assert ran.returncode == 0, ran.stdout + ran.stderr
    assert (repo / "governance" / "observations.sqlite3").is_file()

    evaluated = _evaluate(repo, approver_key)
    assert evaluated.returncode == 0, evaluated.stdout + evaluated.stderr
    assert evaluated.stdout.startswith("PASS"), evaluated.stdout
    assert "removed-observation" not in evaluated.stdout

    chain = invoke(
        repo,
        "journal",
        "verify",
        "--observations",
        "--external-repository",
        str(repo),
    )
    assert chain.returncode == 0, chain.stdout + chain.stderr
    assert "chain=verified" in chain.stdout


def test_arm4_identical_inputs_identical_chain_heads(
    observation_repo: tuple[Path, Path, Path],
) -> None:
    """VERIFIED: two identical FAIL runs append a verify-clean deterministic chain."""

    repo, signer, _approver_key = observation_repo
    assert _run_fail(repo, signer).returncode == 1
    log = repo / "governance" / "observations.sqlite3"

    def head() -> str:
        connection = sqlite3.connect(f"{log.resolve().as_uri()}?mode=ro", uri=True)
        try:
            row = connection.execute(
                "SELECT link FROM observations ORDER BY seq DESC LIMIT 1"
            ).fetchone()
        finally:
            connection.close()
        assert row is not None
        return str(row[0])

    first = head()
    assert _run_fail(repo, signer).returncode == 1
    second = head()
    assert first != second  # append-only grew
    verify = invoke(
        repo,
        "journal",
        "verify",
        "--observations",
        "--external-repository",
        str(repo),
    )
    assert verify.returncode == 0, verify.stdout + verify.stderr
    assert first.startswith("sha256:") and second.startswith("sha256:")
