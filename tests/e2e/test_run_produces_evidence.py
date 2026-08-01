"""SLICE-001 — `ranex run` observes a command and emits evidence.

The target for this slice. Written before the implementation and required to
fail first: a test that passes before the code exists is not a target, it is a
circle painted around wherever the dart landed.

Contract under test:

    ranex run --claim <id> --producer <id> -- <command...>

- exits with the wrapped command's exit code, so `run && gate evaluate` composes
- records the exit code verbatim, success or failure — a failing command is
  honest evidence, not an error
- refuses a dirty working tree, because a digest of HEAD does not describe an
  uncommitted tree
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from ranex.cli.main import main
from ranex.foundation.canonical import canonical_sha256

from conftest import Signing, attach, signing_for

GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims: [tests-executed]
"""


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    """A real git repository whose working tree is clean."""

    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    # The keyring is committed with the tree, as it is in production: it is the
    # trust root, and review of this file is the control on it.
    signing.write_keyring(repository)
    attach(repository, signing)
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    return repository


def subject_of(repo: Path) -> str:
    """The digest `gate evaluate` will compute for HEAD."""

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


def invoke(repo: Path, argv: list[str], producer: str | None = None) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        if producer is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv(
                "RANEX_SIGNING_KEY", str(signing_for(repo).key_path(producer))
            )
        return main(argv)


def run_cmd(repo: Path, *command: str, claim: str = "tests-executed",
            producer: str = "worker", evidence: str = "evidence.json") -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", claim,
            "--producer", producer,
            "--repository", ".",
            "--evidence", evidence,
            "--producers", "producers.yaml",
            "--", *command,
        ],
        producer=producer,
    )


def evaluate(repo: Path, approver: str = "reviewer") -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--approver", approver,
        ],
    )


def records(repo: Path, name: str = "evidence.json") -> list[dict]:
    return json.loads((repo / name).read_text(encoding="utf-8"))


# --- observation -----------------------------------------------------------


def test_records_a_successful_command(repo: Path) -> None:
    assert run_cmd(repo, "sh", "-c", "exit 0") == 0

    (record,) = records(repo)
    assert record["claim_id"] == "tests-executed"
    assert record["producer_id"] == "worker"
    assert record["exit_code"] == 0
    assert record["subject_digest"] == subject_of(repo)
    assert "exit 0" in record["command"]


def test_records_a_failing_command_and_exits_with_its_code(repo: Path) -> None:
    """A failing command is evidence of failure, not a usage error."""

    assert run_cmd(repo, "sh", "-c", "exit 3") == 3

    (record,) = records(repo)
    assert record["exit_code"] == 3


def test_subject_matches_what_gate_evaluate_computes(repo: Path) -> None:
    """One digest implementation, not two."""

    run_cmd(repo, "sh", "-c", "exit 0")
    assert records(repo)[0]["subject_digest"] == subject_of(repo)


# --- refusing to make a false claim ----------------------------------------


def test_refuses_a_dirty_working_tree(repo: Path) -> None:
    """HEAD's digest does not describe an uncommitted tree."""

    (repo / "file.txt").write_text("modified\n", encoding="utf-8")

    assert run_cmd(repo, "sh", "-c", "exit 0") == 2
    assert not (repo / "evidence.json").exists(), "nothing may be written"


def test_refuses_an_untracked_file(repo: Path) -> None:
    """An untracked file is absent from HEAD's tree but present when the
    command runs, so the digest would not describe what was observed."""

    (repo / "stray.py").write_text("x = 1\n", encoding="utf-8")

    assert run_cmd(repo, "sh", "-c", "exit 0") == 2
    assert not (repo / "evidence.json").exists()


def test_existing_evidence_file_does_not_count_as_dirty(repo: Path) -> None:
    """Ranex's own output is written after the command ran and cannot have
    influenced it. Without this exemption the second run always refuses."""

    assert run_cmd(repo, "sh", "-c", "exit 0") == 0
    assert run_cmd(repo, "sh", "-c", "exit 0", claim="contracts-validated") == 0

    assert {r["claim_id"] for r in records(repo)} == {
        "tests-executed",
        "contracts-validated",
    }


def test_refuses_absolute_evidence_path(repo: Path) -> None:
    assert run_cmd(repo, "sh", "-c", "exit 0", evidence=str(repo / "out.json")) == 2


# --- the evidence file -----------------------------------------------------


def test_creates_the_evidence_file_when_absent(repo: Path) -> None:
    assert not (repo / "evidence.json").exists()
    run_cmd(repo, "sh", "-c", "exit 0")
    assert (repo / "evidence.json").is_file()


def test_preserves_unrelated_records(repo: Path) -> None:
    (repo / "evidence.json").write_text(
        json.dumps(
            [
                signing_for(repo).sign(
                    {
                        "claim_id": "contracts-validated",
                        "subject_digest": subject_of(repo),
                        "producer_id": "auditor",
                        "command": "validate",
                        "exit_code": 0,
                    },
                    "auditor",
                )
            ]
        ),
        encoding="utf-8",
    )

    run_cmd(repo, "sh", "-c", "exit 0")

    assert {r["claim_id"] for r in records(repo)} == {
        "contracts-validated",
        "tests-executed",
    }


def test_replaces_the_same_claim_and_producer(repo: Path) -> None:
    run_cmd(repo, "sh", "-c", "exit 0")
    run_cmd(repo, "sh", "-c", "exit 0")

    assert len(records(repo)) == 1


def test_keeps_the_same_claim_from_a_different_producer(repo: Path) -> None:
    run_cmd(repo, "sh", "-c", "exit 0", producer="worker-a")
    run_cmd(repo, "sh", "-c", "exit 0", producer="worker-b")

    assert {r["producer_id"] for r in records(repo)} == {"worker-a", "worker-b"}


def test_output_round_trips_through_admission(repo: Path) -> None:
    """`load_evidence` became `admitted_evidence` in SLICE-002: records are read
    raw and admission decides which are evidence. The round trip still has to
    hold, and now it also has to verify."""

    from ranex.cli.main import admitted_evidence

    run_cmd(repo, "sh", "-c", "exit 0")

    admission = admitted_evidence(repo / "evidence.json", repo / "producers.yaml")
    assert admission.rejections == ()
    (evidence,) = admission.evidence
    assert evidence.claim_id == "tests-executed"
    assert evidence.exit_code == 0
    assert evidence.subject_digest == subject_of(repo)


# --- the closed loop -------------------------------------------------------


def test_run_then_gate_evaluate_passes(repo: Path, capsys) -> None:
    """The whole point of the slice: produced evidence satisfies the gate."""

    assert run_cmd(repo, "sh", "-c", "exit 0") == 0
    capsys.readouterr()

    assert evaluate(repo) == 0
    assert "PASS" in capsys.readouterr().out


def test_failed_command_produces_evidence_that_blocks(repo: Path, capsys) -> None:
    assert run_cmd(repo, "sh", "-c", "exit 1") == 1
    capsys.readouterr()

    assert evaluate(repo) == 1
    assert "FAIL" in capsys.readouterr().out


def test_self_approval_still_refused_end_to_end(repo: Path, capsys) -> None:
    assert run_cmd(repo, "sh", "-c", "exit 0", producer="alice") == 0
    capsys.readouterr()

    assert evaluate(repo, approver="alice") == 1
    assert "self-approval" in capsys.readouterr().out
