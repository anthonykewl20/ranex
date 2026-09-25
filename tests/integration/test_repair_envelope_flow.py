"""SLICE-092 flow: retained junit → projection envelope → stop-hook loop.

A real governed application repository, driven through the real CLI, in
the shape of `test_external_repository.py`: freeze, observe a genuinely
failing subject, evaluate with verdict publication, and prove the repair
envelope carries the failing test's ID, assertion and file:line from the
run's own junit; that the envelope is refused as evidence when offered;
and that the C6 stop-hook gates an autonomous 3-miss loop on the
published verdict + envelope alone.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.foundation.suite_results import validate_suite_results
from ranex.governed_execution.repair_envelope import validate_repair_envelope

KERNEL = Path(__file__).resolve().parents[2]
PYTEST_PYTHON = Path("/usr/bin/python3")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True,
    ).stdout.strip()


def commit(repo: Path, message: str = "pilot application") -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", message)


def invoke(repo: Path, *args: str, key: Path | None = None,
           verdict_key: Path | None = None,
           stdin: str | None = None) -> subprocess.CompletedProcess[str]:
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
        env=environment, capture_output=True, text=True, check=False, timeout=120,
        input=stdin,
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
    (repo / "src/application.py").write_text("VALUE = 42\n")
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
    command = [str(PYTEST_PYTHON), "-m", "pytest", "-q", "-o", "xfail_strict=true",
               "--junitxml=governance/suite_results.xml", "test_application.py"]
    (repo / "governance/gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TESTS\n    blocking: true\n"
        "    required_claims:\n      - claim_id: tests-executed\n"
        f"        command: {json.dumps(command)}\n"
        "        results_artifact: governance/suite_results.xml\n"
    )
    commit(repo)
    return repo, worker, signer, verifying


COMMAND = [str(PYTEST_PYTHON), "-m", "pytest", "-q", "-o", "xfail_strict=true",
           "--junitxml=governance/suite_results.xml", "test_application.py"]


def _break_the_subject(repo: Path) -> None:
    (repo / "src/application.py").write_text("VALUE = 41\n")
    commit(repo, "break the value")


def _subject_hex(repo: Path) -> str:
    # Mirrors `subject_digest_for`: the subject is the git TREE of the ref,
    # canonically wrapped — never the commit hash itself.
    tree = git(repo, "rev-parse", "HEAD^{tree}")
    return hashlib.sha256(canonical_json_bytes({"tree": tree})).hexdigest()


def _stop_hook(repo: Path, worker: Path, signer: Path, *, stdin: str = "{}",
               mode: str = "stop", with_key: bool = True) -> dict[str, object]:
    completed = invoke(
        repo, "task", "stop-hook", "--mode", mode, "--external-repository", str(repo),
        "--producer", "worker", "--approver", "pilot",
        key=worker if with_key else None, verdict_key=signer, stdin=stdin,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return json.loads(completed.stdout.strip().splitlines()[-1])


def _freeze(application) -> Path:
    repo, _worker, _signer, _verifying = application
    frozen = invoke(repo, "suite", "freeze", "--external-repository", str(repo),
                    "--artifact", "governance/suite_results.xml", "--", *COMMAND)
    assert frozen.returncode == 0, frozen.stdout + frozen.stderr
    commit(repo)
    return repo


def test_retained_junit_and_projection_envelope_carry_real_failure_detail(
    application,
) -> None:
    repo, worker, signer, _verifying = application
    _freeze(application)
    _break_the_subject(repo)
    observed = invoke(repo, "run", "--external-repository", str(repo),
                      "--claim", "tests-executed", "--producer", "worker",
                      "--", *COMMAND, key=worker)
    assert observed.returncode == 1, observed.stdout + observed.stderr

    subject_hex = _subject_hex(repo)
    # The run retained the junit one seam longer, keyed by the subject it
    # was produced for — in the read channel, not in evidence.
    retained = repo / "governance/verdicts" / f"{subject_hex}.junit.xml"
    assert retained.is_file()
    junit_bytes = retained.read_bytes()
    assert b"test_value" in junit_bytes and b"<failure" in junit_bytes

    evaluated = invoke(repo, "gate", "evaluate", "HEAD", "--external-repository",
                       str(repo), "--approver", "pilot", verdict_key=signer)
    assert evaluated.returncode == 1, evaluated.stdout + evaluated.stderr

    envelope_path = repo / "governance/verdicts" / f"{subject_hex}.envelope.json"
    assert envelope_path.is_file()
    envelope = validate_repair_envelope(json.loads(envelope_path.read_bytes()))
    assert envelope["verdict"] == "FAIL"
    assert envelope["junit_retained"] is True
    assert envelope["failure_count"] == 1
    assert envelope["failures"] == [
        {
            "id": "test_application.py::test_value",
            "assertion": "assert 41 == 42",
            "at": "test_application.py:4",
        }
    ]
    assert envelope["causes"] and envelope["causes"][0]["claim_id"] == "tests-executed"
    assert envelope["repro_argv"].startswith(str(PYTEST_PYTHON))
    assert any(rung.startswith("L1 ") for rung in envelope["next_rung"])
    # The verdict record digest binds the advisory packet to the authority.
    verdict = json.loads(
        (repo / "governance/verdicts" / f"{subject_hex}.json").read_bytes()
    )
    assert envelope["verdict_record_digest"] == verdict["record"]["record_digest"]


def test_envelope_bytes_offered_as_evidence_are_refused(application) -> None:
    repo, worker, signer, _verifying = application
    _freeze(application)
    _break_the_subject(repo)
    observed = invoke(repo, "run", "--external-repository", str(repo),
                      "--claim", "tests-executed", "--producer", "worker",
                      "--", *COMMAND, key=worker)
    assert observed.returncode == 1, observed.stdout + observed.stderr
    evaluated = invoke(repo, "gate", "evaluate", "HEAD", "--external-repository",
                       str(repo), "--approver", "pilot", verdict_key=signer)
    assert evaluated.returncode == 1, evaluated.stdout + evaluated.stderr

    subject_hex = _subject_hex(repo)
    envelope = json.loads(
        (repo / "governance/verdicts" / f"{subject_hex}.envelope.json").read_bytes()
    )
    # The envelope's own shape is refused by the closed suite-summary
    # validator: advisory bytes are structurally not evidence.
    with pytest.raises(ValueError):
        validate_suite_results(envelope)

    # And when actually offered — a signed record whose suite_results is the
    # envelope — admission rejects it and the claim stays unsatisfied.
    private = worker.read_text(encoding="utf-8").strip()
    content = {
        "claim_id": "tests-executed",
        "subject_digest": f"sha256:{subject_hex}",
        "producer_id": "worker",
        "command": " ".join(COMMAND),
        "command_digest": "sha256:" + "0" * 64,
        "executable_path": str(PYTEST_PYTHON),
        "exit_code": 0,
        "suite_results": envelope,
        "confinement_result_digest": None,
        "confinement_profile_digest": None,
        "envelope_type": "ranex-evidence-v3",
        "gate_id": "landing",
        "catalog_digest": "sha256:" + "1" * 64,
    }
    forged = [{**content, "signature": sign_evidence(content, private)}]
    (repo / "governance/evidence.json").write_bytes(
        canonical_json_bytes(forged) + b"\n"
    )
    refused = invoke(repo, "gate", "evaluate", "HEAD", "--external-repository",
                     str(repo), "--approver", "pilot", verdict_key=signer)
    assert refused.returncode == 1, refused.stdout + refused.stderr
    assert "malformed" in (refused.stdout + refused.stderr).lower()


def test_stop_hook_runs_autonomous_three_miss_loop(application) -> None:
    repo, worker, signer, _verifying = application
    _freeze(application)
    _break_the_subject(repo)

    first = _stop_hook(repo, worker, signer)
    assert first["decision"] == "block"
    assert first["read_state"] == "verified"
    assert first["misses"] == 1 and first["budget"] == 3
    envelope = validate_repair_envelope(first["envelope"])
    assert envelope["verdict"] == "FAIL"
    assert envelope["failures"][0]["id"] == "test_application.py::test_value"
    assert "assert 41 == 42" in first["reason"]

    second = _stop_hook(repo, worker, signer)
    assert second["decision"] == "block" and second["misses"] == 2

    third = _stop_hook(repo, worker, signer)
    # The 3-miss rule: the stop is deterministic, not a human's decision.
    assert third["decision"] == "approve"
    assert third["misses"] == 3
    assert "miss budget exhausted" in third["reason"]

    # A passing subject resets the budget and approves.
    (repo / "src/application.py").write_text("VALUE = 42\n")
    commit(repo, "repair the value")
    repaired = _stop_hook(repo, worker, signer)
    assert repaired["decision"] == "approve"
    assert repaired["misses"] == 0
    assert repaired["envelope"]["verdict"] == "PASS"

    assert not (repo / "governance/verdicts" / f"{_subject_hex(repo)}.budget.json").exists()


def test_stop_hook_without_credential_never_fabricates(application) -> None:
    repo, _worker, signer, _verifying = application
    _freeze(application)
    _break_the_subject(repo)

    answer = _stop_hook(repo, _worker, signer, with_key=False)
    assert answer["decision"] == "approve"
    assert answer["read_state"] == "absent"
    assert "no signing credential" in answer["reason"]
    assert answer["envelope"] is None


def test_pretooluse_blocks_running_the_suite_by_hand(application) -> None:
    repo, worker, signer, _verifying = application
    _freeze(application)
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": " ".join(COMMAND)}})
    blocked = _stop_hook(repo, worker, signer, stdin=payload, mode="pretooluse")
    assert blocked["decision"] == "block"
    assert "verdict read channel" in blocked["reason"]

    unrelated = _stop_hook(
        repo, worker, signer,
        stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}),
        mode="pretooluse",
    )
    assert unrelated["decision"] == "approve"
