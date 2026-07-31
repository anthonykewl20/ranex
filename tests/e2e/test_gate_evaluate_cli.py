"""End-to-end: the CLI against a real git repository.

Acceptance criterion 2 of the slice definition — the command must block a real
change, not merely be capable of blocking one.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.cli.main import main

GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims: [tests-executed]
"""


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A real git repository with a real commit."""

    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.email", "t@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repository), "config", "user.name", "Test"], check=True
    )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    return repository


def run(repo: Path, *extra: str) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        return main(
            [
                "gate",
                "evaluate",
                "HEAD",
                "--repository",
                ".",
                "--gate-catalog",
                "gates.yaml",
                "--evidence",
                "evidence.json",
                "--approver",
                "owner",
                *extra,
            ]
        )


def test_blocks_a_real_change_with_no_evidence(repo: Path, capsys) -> None:
    assert run(repo) == 1
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "tests-executed" in out


def test_passes_once_real_evidence_exists(repo: Path, capsys) -> None:
    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    from ranex.foundation.canonical import canonical_sha256

    subject = "sha256:" + canonical_sha256({"tree": tree})
    (repo / "evidence.json").write_text(
        json.dumps(
            [
                {
                    "claim_id": "tests-executed",
                    "subject_digest": subject,
                    "producer_id": "worker",
                    "command": "pytest -q",
                    "exit_code": 0,
                }
            ]
        ),
        encoding="utf-8",
    )
    assert run(repo) == 0
    assert "PASS" in capsys.readouterr().out


def test_evidence_from_a_different_commit_does_not_satisfy(repo: Path, capsys) -> None:
    """Stale evidence is not evidence — the whole point of subject binding."""

    (repo / "evidence.json").write_text(
        json.dumps(
            [
                {
                    "claim_id": "tests-executed",
                    "subject_digest": "sha256:" + "f" * 64,
                    "producer_id": "worker",
                    "command": "pytest -q",
                    "exit_code": 0,
                }
            ]
        ),
        encoding="utf-8",
    )
    assert run(repo) == 1
    assert "different subject" in capsys.readouterr().out


def test_evidence_without_subject_digest_is_a_usage_error(repo: Path, capsys) -> None:
    """The CLI must not stamp omitted subject binding onto evidence."""

    (repo / "evidence.json").write_text(
        json.dumps(
            [
                {
                    "claim_id": "tests-executed",
                    "producer_id": "worker",
                    "command": "echo i-never-ran",
                    "exit_code": 0,
                }
            ]
        ),
        encoding="utf-8",
    )
    assert run(repo) == 2
    captured = capsys.readouterr()
    assert "PASS" not in captured.out
    assert "subject_digest" in captured.err


def test_two_runs_write_identical_journal_records(repo: Path) -> None:
    journal = repo / "journal.sqlite3"
    run(repo, "--journal", "journal.sqlite3")
    run(repo, "--journal", "journal.sqlite3")
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    entries = Journal(journal).entries()
    assert len(entries) == 2
    assert entries[0] == entries[1]
    assert Journal(journal).verify() is True


def test_unresolvable_ref_is_a_usage_error_not_a_pass(repo: Path) -> None:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        assert (
            main(
                [
                    "gate",
                    "evaluate",
                    "does-not-exist",
                    "--repository",
                    ".",
                    "--gate-catalog",
                    "gates.yaml",
                    "--approver",
                    "owner",
                ]
            )
            == 2
        )


@pytest.mark.parametrize("option", ["--gate-catalog", "--evidence", "--journal"])
def test_absolute_path_inputs_are_refused_by_cli(
    repo: Path, capsys, option: str
) -> None:
    assert run(repo, option, str(repo / "outside.json")) == 2
    captured = capsys.readouterr()
    assert "absolute paths are refused" in captured.err
    assert "PASS" not in captured.out


def test_foreign_repository_evaluation_is_refused_by_real_cli(repo: Path) -> None:
    """Regression for the exact second-repository attack from FINAL-GATE.md."""

    foreign = repo.parent / "foreign"
    subprocess.run(["git", "init", "-q", str(foreign)], check=True)
    (foreign / "payload.txt").write_text("ATTACKER CONTROLLED\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(foreign), "add", "-A"], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(foreign),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=t@example.com",
            "commit",
            "-q",
            "-m",
            "foreign",
        ],
        check=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ranex.cli.main",
            "gate",
            "evaluate",
            "HEAD",
            "--repository",
            str(foreign),
            "--gate-catalog",
            str(repo / "gates.yaml"),
            "--evidence",
            str(repo / "evidence.json"),
            "--journal",
            str(repo / "journal.sqlite3"),
            "--approver",
            "owner",
        ],
        cwd=repo,
        env=os.environ | {"PYTHONPATH": str(Path(__file__).parents[2] / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "absolute paths are refused" in result.stderr
    assert "PASS" not in result.stdout
