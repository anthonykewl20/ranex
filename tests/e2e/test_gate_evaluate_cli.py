"""End-to-end: the CLI against a real git repository.

Acceptance criterion 2 of the slice definition — the command must block a real
change, not merely be capable of blocking one.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import main
from ranex.foundation.canonical import canonical_sha256, command_digest

# SLICE-003: the claim declares the command that satisfies it, and the
# hand-built records below describe that same command.
BOUND = ["pytest", "-q"]
# A resolved absolute path outside any repository under test.
EXECUTABLE = "/usr/bin/pytest"

GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["pytest", "-q"]
"""


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
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
    signing.write_keyring(repository)
    attach(repository, signing)
    # Committed, like the keyring beside it. Both are the trust root, and since
    # SLICE-002 was reopened a trust-root path HEAD does not carry is refused
    # outright rather than read from disk — so a catalog written after the
    # commit is no longer a catalog the CLI will evaluate against.
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
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
                "--producers",
                "producers.yaml",
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
                signing_for(repo).sign(
                    {
                        "claim_id": "tests-executed",
                        "subject_digest": subject,
                        "producer_id": "worker",
                        "command": "pytest -q",
                        "command_digest": command_digest(BOUND),
                        "executable_path": EXECUTABLE,
                        "exit_code": 0,
                    },
                    "worker",
                )
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
                signing_for(repo).sign(
                    {
                        "claim_id": "tests-executed",
                        "subject_digest": "sha256:" + "f" * 64,
                        "producer_id": "worker",
                        "command": "pytest -q",
                        "command_digest": command_digest(BOUND),
                        "executable_path": EXECUTABLE,
                        "exit_code": 0,
                    },
                    "worker",
                )
            ]
        ),
        encoding="utf-8",
    )
    assert run(repo) == 1
    assert "different subject" in capsys.readouterr().out


def test_evidence_without_subject_digest_is_refused_and_named(repo: Path, capsys) -> None:
    """The CLI must not stamp omitted subject binding onto evidence.

    SLICE-002 changed HOW this is refused, not WHETHER. It used to be a usage
    error (exit 2): a missing key raised, and the whole evaluation died. Now the
    record is refused by admission and the evaluation continues without it, so
    the verdict is FAIL (exit 1) with the record named.

    That is the better behaviour, and deliberately so: one malformed record must
    not stop the other records from being judged. The property the original test
    was defending — that a shrugging parser must never turn a bad record into
    silent absence — is stronger now than it was, because the refusal is
    reported with a reason rather than inferred from an exit code.
    """

    (repo / "evidence.json").write_text(
        json.dumps(
            [
                {
                    "claim_id": "tests-executed",
                    "producer_id": "worker",
                    "command": "echo i-never-ran",
                    "command_digest": command_digest(["echo", "i-never-ran"]),
                    "executable_path": EXECUTABLE,
                    "exit_code": 0,
                }
            ]
        ),
        encoding="utf-8",
    )
    assert run(repo) == 1
    captured = capsys.readouterr()
    assert "PASS" not in captured.out
    assert "subject_digest" in captured.out
    assert "REFUSED" in captured.out
    # And it must not be reported as honest absence.
    assert "no evidence for required claim" not in captured.out


def test_two_runs_write_identical_journal_records(repo: Path) -> None:
    journal = repo / "journal.sqlite3"
    run(repo, "--journal", "journal.sqlite3")
    run(repo, "--journal", "journal.sqlite3")
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    entries = Journal(journal).entries()
    assert len(entries) == 2
    assert entries[0] == entries[1]
    assert Journal(journal).verify() is True


def test_empty_journal_path_is_a_usage_error_not_an_unrecorded_pass(
    repo: Path, capsys
) -> None:
    """An unset shell variable must not silently turn off the append-only record."""

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    subject = "sha256:" + canonical_sha256({"tree": tree})
    (repo / "evidence.json").write_text(
        json.dumps(
            [
                signing_for(repo).sign(
                    {
                        "claim_id": "tests-executed",
                        "subject_digest": subject,
                        "producer_id": "worker",
                        "command": "pytest -q",
                        "command_digest": command_digest(BOUND),
                        "executable_path": EXECUTABLE,
                        "exit_code": 0,
                    },
                    "worker",
                )
            ]
        ),
        encoding="utf-8",
    )
    assert run(repo, "--journal", "") == 2
    captured = capsys.readouterr()
    assert "journal" in captured.err
    assert "PASS" not in captured.out
    assert not (repo / "governance" / "journal.sqlite3").exists()


def test_non_sqlite_journal_is_a_usage_error_not_a_gate_failure(
    repo: Path, capsys
) -> None:
    """A journal I/O crash must not use the exit code for a judged FAIL."""

    bad_journal = repo / "not-a-database.sqlite3"
    bad_journal.write_text("not sqlite", encoding="utf-8")

    assert run(repo, "--journal", bad_journal.name) == 2
    captured = capsys.readouterr()
    assert "database" in captured.err
    assert "FAIL" not in captured.out


def test_journal_verify_reports_a_valid_chain(repo: Path, capsys) -> None:
    """Operators need a CLI path to query the journal's tamper evidence."""

    journal = repo / "journal.sqlite3"
    assert run(repo, "--journal", journal.name) == 1

    def verify(path: str) -> int:
        monkeypatch.chdir(repo)
        return main(
            [
                "journal",
                "verify",
                "--repository",
                ".",
                "--journal",
                path,
            ]
        )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        assert verify(journal.name) == 0
        captured = capsys.readouterr()
        assert "PASS" in captured.out
        assert journal.name in captured.out

        with sqlite3.connect(journal) as conn:
            conn.execute("DROP TRIGGER evaluations_no_update")
            conn.execute("UPDATE evaluations SET record = '{}' WHERE seq = 1")
        assert verify(journal.name) == 1
        assert "chain=invalid" in capsys.readouterr().out

        bad = repo / "not-a-database.sqlite3"
        bad.write_text("not sqlite", encoding="utf-8")
        assert verify(bad.name) == 2
        assert "database" in capsys.readouterr().err


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
    """Regression for the second-repository attack from 2026-07-31-final-gate-adjudication.md."""

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
