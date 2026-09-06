"""An operator governs a separate application's real tests without vendoring."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.foundation.signing import generate_keypair
from ranex.github_app.acceptance import resolve_acceptance
from ranex.github_app.binding import bind_pr_head

KERNEL = Path(__file__).resolve().parents[2]
PYTEST_PYTHON = Path("/usr/bin/python3")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def commit(repo: Path) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "pilot application")


def invoke(repo: Path, *args: str, key: Path | None = None,
           verdict_key: Path | None = None) -> subprocess.CompletedProcess[str]:
    environment = {
        name: value for name, value in os.environ.items()
        if not name.startswith(("RANEX_", "GIT_", "PYTHON"))
    }
    environment["PYTHONPATH"] = str(KERNEL / "src")
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    if verdict_key is not None:
        environment["RANEX_VERDICT_SIGNING_KEY"] = str(verdict_key)
        environment["RANEX_VERDICT_DIR"] = "governance/verdicts"
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *args], cwd=repo,
        env=environment, capture_output=True, text=True, check=False, timeout=60,
    )


@pytest.fixture
def application(tmp_path: Path) -> tuple[Path, Path, Path, str]:
    available = subprocess.run(
        [str(PYTEST_PYTHON), "-m", "pytest", "--version"],
        capture_output=True, check=False,
    ) if PYTEST_PYTHON.exists() else None
    if available is None or available.returncode:
        pytest.skip("real system Python with pytest is needed for hermetic observation")
    repo = tmp_path / "application"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Pilot")
    git(repo, "config", "user.email", "pilot@example.invalid")
    (repo / "src").mkdir()
    (repo / "src" / "application.py").write_text("VALUE = 42\n")
    (repo / "test_application.py").write_text(
        "from src.application import VALUE\n\ndef test_value():\n    assert VALUE == 42\n"
    )
    (repo / "governance").mkdir()
    (repo / ".gitignore").write_text(
        "governance/evidence.json\ngovernance/suite_results.xml\n"
        "governance/journal.sqlite3*\ngovernance/verdicts/\n"
        "__pycache__/\n.pytest_cache/\n"
    )
    private, public = generate_keypair()
    worker = tmp_path / "worker.key"
    worker.write_text(private + "\n")
    worker.chmod(0o600)
    signing, verifying = generate_keypair()
    signer = tmp_path / "verdict.key"
    signer.write_text(signing + "\n")
    signer.chmod(0o600)
    (repo / "governance/producers.yaml").write_text(
        f"producers:\n  worker: {public}\n"
        f"verdict_signer:\n  id: kernel-verdict-signer\n  public_key: {verifying}\n"
    )
    command = [str(PYTEST_PYTHON), "-m", "pytest", "-q",
               "--junitxml=governance/suite_results.xml", "test_application.py"]
    (repo / "governance/gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        f"        command: {json.dumps(command)}\n"
        "        results_artifact: governance/suite_results.xml\n"
    )
    commit(repo)
    return repo, worker, signer, verifying


def test_separate_src_application_freeze_observe_sign_reject_and_recover(application) -> None:
    repo, worker, signer, verifying = application
    command = [str(PYTEST_PYTHON), "-m", "pytest", "-q",
               "--junitxml=governance/suite_results.xml", "test_application.py"]
    frozen = invoke(repo, "suite", "freeze", "--external-repository", str(repo),
                    "--artifact", "governance/suite_results.xml", "--", *command)
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    commit(repo)

    def observe():
        return invoke(repo, "run", "--external-repository", str(repo),
                      "--claim", "tests-executed", "--producer", "worker",
                      "--", *command, key=worker)

    def evaluate():
        return invoke(repo, "gate", "evaluate", "HEAD", "--external-repository", str(repo),
                      "--approver", "pilot", verdict_key=signer)

    observed = observe()
    assert observed.returncode == 0, observed.stdout + observed.stderr
    passed = evaluate()
    assert passed.returncode == 0, passed.stdout + passed.stderr
    binding = bind_pr_head(repo, git(repo, "rev-parse", "HEAD"))
    acceptance = resolve_acceptance(
        repo / "governance/verdicts", binding, {"kernel-verdict-signer": verifying},
        gate_id="landing", catalog_digest=catalog_digest_for((repo / "governance/gates.yaml").read_bytes()),
        approver_id="pilot",
    )
    assert acceptance.publishable and acceptance.record["verdict"] == "PASS"
    evidence = repo / "governance/evidence.json"
    original = evidence.read_bytes()
    records = json.loads(original)
    records[0]["signature"] = "ed25519:" + "A" * 88
    evidence.write_text(json.dumps(records))
    tampered = evaluate()
    assert tampered.returncode == 1, tampered.stdout + tampered.stderr
    evidence.write_bytes(original)
    (repo / "src/application.py").write_text("VALUE = 41\n")
    commit(repo)
    stale = evaluate()
    assert stale.returncode == 1 and "different subject digest" in stale.stdout
    failed = observe()
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert evaluate().returncode == 1
    (repo / "src/application.py").write_text("VALUE = 42  # repaired\n")
    commit(repo)
    assert observe().returncode == 0
    assert evaluate().returncode == 0
    journal = invoke(repo, "journal", "verify", "--external-repository", str(repo))
    assert journal.returncode == 0 and "chain=verified" in journal.stdout
    assert not (repo / "src/ranex").exists()


def test_external_target_does_not_relax_paths_keys_or_implicit_authority(application) -> None:
    repo, worker, _signer, _verifying = application
    implicit = invoke(repo, "journal", "verify", "--repository", str(repo))
    assert implicit.returncode == 2
    conflict = invoke(repo, "journal", "verify", "--external-repository", str(repo),
                      "--repository", "other")
    assert conflict.returncode == 2 and "cannot combine" in conflict.stderr
    nested = invoke(repo, "journal", "verify", "--external-repository", str(repo / "src"))
    assert nested.returncode == 2 and "checkout root" in nested.stderr
    escape = invoke(repo, "journal", "verify", "--external-repository", str(repo),
                    "--journal", "../outside.sqlite3")
    assert escape.returncode == 2 and "outside the repository" in escape.stderr
    inside = repo / "private.key"
    keygen = invoke(repo, "keygen", "--external-repository", str(repo),
                    "--producer", "new-worker", key=inside)
    assert keygen.returncode == 2 and "inside the repository" in keygen.stderr
    assert not inside.exists()
    outside = worker.parent / "new-worker.key"
    keygen = invoke(repo, "keygen", "--external-repository", str(repo),
                    "--producer", "new-worker", key=outside)
    assert keygen.returncode == 0, keygen.stderr
    assert outside.stat().st_mode & 0o777 == 0o600
