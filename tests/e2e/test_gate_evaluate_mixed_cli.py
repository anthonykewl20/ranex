"""End-to-end: SLICE-060 — the FAIL presentation on a mixed verdict.

Freezes the contract for a gate whose missing claims fall into different
partitions at once: one claim's evidence is bound to another subject digest
(stale), another has no record at all (absent). The absence sentence is spent
exactly once, the kernel's stale clause still prints, and the recorded reason
in the journal carries both clauses untouched — presentation must never change
the record.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import main
from ranex.foundation.canonical import command_digest

# SLICE-003: each claim declares the command that satisfies it, and the
# hand-built record below describes that same command.
BOUND = ["pytest", "-q"]
# A resolved absolute path outside any repository under test.
EXECUTABLE = "/usr/bin/pytest"

# Wordings copied from _diagnosis() in
# src/ranex/governed_execution/domain/verdict.py — the contract under test.
ABSENCE = "no evidence for required claim"
STALE = "evidence bound to a different subject digest"

# Two required claims so the verdict can be mixed: one stale, one absent.
GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["pytest", "-q"]
      - claim_id: lint-clean
        command: ["ruff", "check"]
"""


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    """A real git repository with a real commit and the two-claim catalog."""

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
    # Committed, like the keyring beside it: the trust root must be carried by
    # HEAD or the CLI refuses it outright.
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    return repository


def mixed_evidence(repo: Path) -> None:
    """Exactly one signed record: stale for tests-executed, nothing for lint-clean.

    The subject digest names no real tree — mirrors
    test_evidence_from_a_different_commit_does_not_satisfy — so the record is
    admitted but satisfies nothing here.
    """

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


def test_mixed_verdict_prints_the_absence_sentence_once(repo: Path, capsys) -> None:
    """One claim is absent, so the absence sentence is spent exactly once.

    The CLI partitions missing claims itself and then prints the kernel's
    recorded reason, which names the same absence again — the sentence must
    not appear twice for one event.
    """

    mixed_evidence(repo)
    assert run(repo) == 1
    out = capsys.readouterr().out
    assert out.count(ABSENCE) == 1
    assert f"{ABSENCE}: lint-clean" in out


def test_mixed_verdict_still_prints_the_stale_clause(repo: Path, capsys) -> None:
    """Deduplicating absence must not swallow the stale diagnosis."""

    mixed_evidence(repo)
    assert run(repo) == 1
    out = capsys.readouterr().out
    assert f"{STALE}: tests-executed" in out


def test_recorded_reason_carries_both_clauses_untouched(repo: Path) -> None:
    """The journal record is the kernel's verdict, not the presentation.

    _diagnosis() orders clauses stale before absent and joins with "; " — that
    exact string is what gets appended, whatever stdout does with it.
    """

    mixed_evidence(repo)
    assert run(repo, "--journal", "journal.sqlite3") == 1
    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    entries = Journal(repo / "journal.sqlite3").entries()
    assert len(entries) == 1
    assert entries[0]["reason"] == (
        f"{STALE}: tests-executed; {ABSENCE}: lint-clean"
    )


def test_all_absent_verdict_prints_the_absence_sentence_once(repo: Path, capsys) -> None:
    """No evidence at all: one absence sentence naming both claims.

    A missing evidence file is no evidence, not an error — same as
    test_blocks_a_real_change_with_no_evidence. Pinned so the mixed-verdict
    fix cannot regress the already-correct all-absent presentation.
    """

    assert run(repo) == 1
    out = capsys.readouterr().out
    assert out.count(ABSENCE) == 1
    sentence = next(line for line in out.splitlines() if ABSENCE in line)
    assert "lint-clean" in sentence
    assert "tests-executed" in sentence
