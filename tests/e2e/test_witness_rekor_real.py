"""SLICE-098 — external witness: real Rekor, real CLI, #95 protocol.

Five arms against the public transparency log (or an unreachable URL for the
network-down negative control). No mocks: every step is a real ``ranex``
subprocess on a real Git repository. Statuses are VERIFIED in the assertions;
a red here is a GAP, never a FALSE-PASS.

Arms:
1. Publish + witness → ``witness.json`` present; ``--witnessed`` verify accepts.
2. Truncate journal + re-sign → local ``--against-verdict`` may accept;
   ``--witnessed`` refuses (digest differs from the witnessed one).
3. Network down + ``--witness`` → exit 2, no verdict published; without
   ``--witness`` the verdict publishes unwitnessed.
4. Tamper ``witness.json`` → inclusion proof fails.
5. Repeats → identical local payload digests; the public log coalesces
   equivalent DSSE entries (same UUID/index on the second submit).
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import _approver
import _prereqs
import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.history import bootstrap_history

KERNEL = Path(__file__).resolve().parents[2]
REKOR_KEY = KERNEL / "governance" / "rekor_public_key.pem"


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
    verdict_key: Path | None = None,
    approver_key: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "GIT_", "PYTHON", "COVERAGE_"))
    }
    environment["PYTHONPATH"] = str(KERNEL / "src")
    environment["RANEX_HISTORY_CHECKPOINT"] = str(repo.parent / "history-checkpoint.json")
    environment["RANEX_VERDICT_SIGNING_KEY"] = str(repo.parent / "verdict.key")
    if verdict_key is not None:
        environment["RANEX_VERDICT_SIGNING_KEY"] = str(verdict_key)
        environment["RANEX_VERDICT_DIR"] = "governance/verdicts"
    if approver_key is not None:
        environment["RANEX_APPROVER_SIGNING_KEY"] = str(approver_key)
    if env_extra:
        environment.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *args],
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def subject_hex(repo: Path) -> str:
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    return hashlib.sha256(canonical_json_bytes({"tree": tree})).hexdigest()


@pytest.fixture
def prereq_rekor_network() -> None:
    _prereqs.prereq_or_skip("rekor_network")


@pytest.fixture
def witnessed_repo(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    if not REKOR_KEY.is_file():
        pytest.fail(f"pinned Rekor public key missing: {REKOR_KEY}")
    repo = tmp_path / "subject"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Witness")
    git(repo, "config", "user.email", "witness@example.invalid")
    (repo / "governance").mkdir()
    (repo / "governance" / "rekor_public_key.pem").write_bytes(REKOR_KEY.read_bytes())
    (repo / ".gitignore").write_text(
        "governance/evidence.json\ngovernance/journal.sqlite3*\n"
        "governance/observations.sqlite3*\n"
        "governance/verdicts/\n"
    )
    signing, verifying = generate_keypair()
    signer = tmp_path / "verdict.key"
    signer.write_text(signing + "\n", encoding="utf-8")
    signer.chmod(0o600)
    _worker_priv, worker_pub = generate_keypair()
    del _worker_priv
    approver_key, approver_pub = _approver.mint_approver(tmp_path, "pilot")
    other_key, other_pub = _approver.mint_approver(tmp_path, "other-pilot")
    (repo / "governance" / "producers.yaml").write_text(
        "producers:\n"
        f"  worker: {worker_pub}\n"
        "verdict_signer:\n"
        f"  id: kernel-verdict-signer\n  public_key: {verifying}\n"
        "principals:\n"
        f"  worker:\n    role: worker\n    keys:\n"
        f"      - key: {worker_pub}\n        status: active\n"
        f"  kernel-verdict-signer:\n    role: service\n    keys:\n"
        f"      - key: {verifying}\n        status: active\n"
        f"  pilot:\n    role: approver\n    keys:\n"
        f"      - key: {approver_pub}\n        status: active\n"
        f"  other-pilot:\n    role: approver\n    keys:\n"
        f"      - key: {other_pub}\n        status: active\n",
        encoding="utf-8",
    )
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        '        command: ["true"]\n',
        encoding="utf-8",
    )
    (repo / "README.md").write_text("witness subject\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "init")
    bootstrap_history(repo / "governance/evidence.json", repo.parent / "history-checkpoint.json", signing, verifying, repo)
    return repo, signer, approver_key, other_key


def _evaluate(
    repo: Path,
    signer: Path,
    approver_key: Path,
    *,
    witness: bool = False,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    args = [
        "gate",
        "evaluate",
        "HEAD",
        "--external-repository",
        str(repo),
        "--approver",
        "pilot",
    ]
    if witness:
        args.append("--witness")
    return invoke(
        repo, *args, verdict_key=signer, approver_key=approver_key, env_extra=env_extra
    )


def test_arm1_publish_and_witnessed_verify(
    prereq_rekor_network: None,
    witnessed_repo: tuple[Path, Path, Path, Path],
) -> None:
    """VERIFIED: witness.json present; --witnessed accepts."""

    repo, signer, approver_key, _other = witnessed_repo
    completed = _evaluate(repo, signer, approver_key, witness=True)
    assert completed.returncode == 1, completed.stdout + completed.stderr
    hex_digest = subject_hex(repo)
    verdict = repo / "governance" / "verdicts" / f"{hex_digest}.json"
    witness = repo / "governance" / "verdicts" / f"{hex_digest}.witness.json"
    assert verdict.is_file() and witness.is_file()
    record = json.loads(witness.read_text(encoding="utf-8"))
    assert record["schema"] == "ranex-witness-v1"
    assert record["payload_digest"].startswith("sha256:")
    verified = invoke(
        repo,
        "journal",
        "verify",
        "--external-repository",
        str(repo),
        "--against-verdict",
        str(verdict.relative_to(repo)),
        "--witnessed",
        verdict_key=signer,
        approver_key=approver_key,
    )
    assert verified.returncode == 0, verified.stdout + verified.stderr
    assert "witness=verified" in verified.stdout


def test_arm2_rewrite_refused_when_witnessed(
    prereq_rekor_network: None,
    witnessed_repo: tuple[Path, Path, Path, Path],
) -> None:
    """VERIFIED negative: self-consistent rewrite fails --witnessed."""

    repo, signer, approver_key, other_key = witnessed_repo
    assert _evaluate(repo, signer, approver_key, witness=True).returncode == 1
    hex_digest = subject_hex(repo)
    verdict = repo / "governance" / "verdicts" / f"{hex_digest}.json"
    witness = repo / "governance" / "verdicts" / f"{hex_digest}.witness.json"
    original_digest = json.loads(witness.read_text(encoding="utf-8"))["payload_digest"]

    journal = repo / "governance" / "journal.sqlite3"
    connection = sqlite3.connect(journal)
    try:
        connection.execute("DROP TRIGGER IF EXISTS evaluations_no_delete")
        connection.execute("DELETE FROM evaluations")
        connection.commit()
    finally:
        connection.close()
    rewritten = invoke(
        repo,
        "gate",
        "evaluate",
        "HEAD",
        "--external-repository",
        str(repo),
        "--approver",
        "other-pilot",
        verdict_key=signer,
        approver_key=other_key,
    )
    assert rewritten.returncode == 1, rewritten.stdout + rewritten.stderr
    new_digest = "sha256:" + hashlib.sha256(verdict.read_bytes()).hexdigest()
    assert new_digest != original_digest
    assert json.loads(witness.read_text(encoding="utf-8"))["payload_digest"] == (
        original_digest
    )

    witnessed = invoke(
        repo,
        "journal",
        "verify",
        "--external-repository",
        str(repo),
        "--against-verdict",
        str(verdict.relative_to(repo)),
        "--witnessed",
        verdict_key=signer,
        approver_key=approver_key,
    )
    assert witnessed.returncode == 2, witnessed.stdout + witnessed.stderr
    assert "E-WITNESS" in witnessed.stderr
    assert "does not match witnessed digest" in witnessed.stderr


def test_arm3_network_down_refuses_and_unwitnessed_publishes(
    witnessed_repo: tuple[Path, Path, Path, Path],
) -> None:
    """VERIFIED negative: --witness + unreachable log → exit 2, no verdict."""

    repo, signer, approver_key, _other = witnessed_repo
    down = _evaluate(
        repo,
        signer,
        approver_key,
        witness=True,
        env_extra={"RANEX_WITNESS_URL": "http://127.0.0.1:1"},
    )
    assert down.returncode == 2, down.stdout + down.stderr
    assert "E-WITNESS" in down.stderr
    hex_digest = subject_hex(repo)
    verdict = repo / "governance" / "verdicts" / f"{hex_digest}.json"
    assert not verdict.exists()

    published = _evaluate(repo, signer, approver_key, witness=False)
    assert published.returncode == 1, published.stdout + published.stderr
    assert verdict.is_file()
    assert not (repo / "governance" / "verdicts" / f"{hex_digest}.witness.json").exists()


def test_arm4_tampered_witness_refused(
    prereq_rekor_network: None,
    witnessed_repo: tuple[Path, Path, Path, Path],
) -> None:
    """VERIFIED negative: edited inclusion proof fails."""

    repo, signer, approver_key, _other = witnessed_repo
    assert _evaluate(repo, signer, approver_key, witness=True).returncode == 1
    hex_digest = subject_hex(repo)
    verdict = repo / "governance" / "verdicts" / f"{hex_digest}.json"
    witness = repo / "governance" / "verdicts" / f"{hex_digest}.witness.json"
    os.chmod(witness, 0o644)
    record = json.loads(witness.read_text(encoding="utf-8"))
    record["inclusion_proof"]["hashes"][0] = "0" * 64
    witness.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    completed = invoke(
        repo,
        "journal",
        "verify",
        "--external-repository",
        str(repo),
        "--against-verdict",
        str(verdict.relative_to(repo)),
        "--witnessed",
        verdict_key=signer,
        approver_key=approver_key,
    )
    assert completed.returncode == 2, completed.stdout + completed.stderr
    assert "inclusion proof does not verify" in completed.stderr


def test_arm5_repeats_identical_local_artifacts(
    prereq_rekor_network: None,
    witnessed_repo: tuple[Path, Path, Path, Path],
) -> None:
    """VERIFIED: identical inputs → identical payload digests; log coalesces."""

    repo, signer, approver_key, _other = witnessed_repo
    first = _evaluate(repo, signer, approver_key, witness=True)
    assert first.returncode == 1, first.stdout + first.stderr
    hex_digest = subject_hex(repo)
    witness_path = repo / "governance" / "verdicts" / f"{hex_digest}.witness.json"
    first_record = json.loads(witness_path.read_text(encoding="utf-8"))
    journal = repo / "governance" / "journal.sqlite3"
    connection = sqlite3.connect(journal)
    try:
        connection.execute("DROP TRIGGER IF EXISTS evaluations_no_delete")
        connection.execute("DELETE FROM evaluations")
        connection.commit()
    finally:
        connection.close()
    second = _evaluate(repo, signer, approver_key, witness=True)
    assert second.returncode == 1, second.stdout + second.stderr
    second_record = json.loads(witness_path.read_text(encoding="utf-8"))
    assert first_record["payload_digest"] == second_record["payload_digest"]
    assert second_record["entry_uuid"] == first_record["entry_uuid"]
    assert second_record["log_index"] == first_record["log_index"]
