"""End-to-end: SLICE-060 — the FAIL presentation on a mixed verdict.

Freezes the contract for a gate whose missing claims fall into different
partitions at once: one claim's evidence is bound to another subject digest
(stale), another has no record at all (absent). The absence sentence is spent
exactly once — pinned by full-block stdout equality, so no surface can smuggle
a second copy — the kernel's stale clause still prints, and the recorded
reason in the journal carries both clauses untouched: presentation must never
change the record.

And dedup must never cost information: a trusted catalog may declare a claim
ID that itself contains "; " or even the absence sentence. Splitting the
recorded reason on "; " would mistake such an ID's fragments for repeats and
drop them. When any missing claim ID contains "; ", dedup steps aside and the
full recorded reason prints verbatim — fail toward repetition, never loss.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import main
from ranex.foundation.canonical import canonical_sha256, command_digest

# SLICE-003: each claim declares the command that satisfies it, and the
# hand-built records below describe that same command.
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

# A claim ID the reason-clause separator also appears in — and which embeds
# the absence sentence itself. Legal (claim_id is any non-empty string), so
# the printed diagnosis must never split on "; " and truncate it.
AMBIGUOUS_ID = f"tests-executed; {ABSENCE}: lint-clean"

AMBIGUOUS_GATES = f"""
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: "{AMBIGUOUS_ID}"
        command: ["pytest", "-q"]
      - claim_id: lint-clean
        command: ["ruff", "check"]
"""


def _make_repo(tmp_path: Path, signing: Signing, gates: str) -> Path:
    """A real git repository with a real commit and the given catalog."""

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
    (repository / "gates.yaml").write_text(gates, encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    return repository


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    return _make_repo(tmp_path, signing, GATES)


@pytest.fixture()
def ambiguous_repo(tmp_path: Path, signing: Signing) -> Path:
    return _make_repo(tmp_path, signing, AMBIGUOUS_GATES)


def subject_of(repo: Path) -> str:
    """The subject digest of HEAD, computed the way the CLI computes it."""

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


def stale_evidence(repo: Path, claim_id: str) -> None:
    """Exactly one signed record for `claim_id`, bound to a foreign subject.

    The subject digest names no real tree — mirrors
    test_evidence_from_a_different_commit_does_not_satisfy — so the record is
    admitted but satisfies nothing here. Nothing is recorded for lint-clean.
    """

    (repo / "evidence.json").write_text(
        json.dumps(
            [
                signing_for(repo).sign(
                    {
                        "claim_id": claim_id,
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

    Pinned by whole-block equality, not substrings: the CLI partitions missing
    claims itself and then prints the kernel's recorded reason, and only exact
    equality can tell WHICH surface carried the sentence — a dedup that moved
    or reworded it would still pass a mere count.
    """

    stale_evidence(repo, "tests-executed")
    assert run(repo) == 1
    out = capsys.readouterr().out
    assert out.count(ABSENCE) == 1
    assert out == (
        "FAIL  gate=landing  rule=TESTS_EXECUTED\n"
        f"      {ABSENCE}: lint-clean\n"
        f"      {STALE}: tests-executed\n"
        f"      subject={subject_of(repo)}\n"
    )


def test_mixed_verdict_still_prints_the_stale_clause(repo: Path, capsys) -> None:
    """Deduplicating absence must not swallow the stale diagnosis."""

    stale_evidence(repo, "tests-executed")
    assert run(repo) == 1
    out = capsys.readouterr().out
    assert f"{STALE}: tests-executed" in out


def test_recorded_reason_carries_both_clauses_untouched(repo: Path) -> None:
    """The journal record is the kernel's verdict, not the presentation.

    _diagnosis() orders clauses stale before absent and joins with "; " — that
    exact string is what gets appended, whatever stdout does with it.
    """

    stale_evidence(repo, "tests-executed")
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


def test_ambiguous_claim_id_disables_dedup_never_truncates(
    ambiguous_repo: Path, capsys
) -> None:
    """A claim ID containing "; " turns dedup off — repeat, never truncate.

    The recorded reason is clause-joined with "; ", so a claim ID carrying
    that separator makes the string ambiguous to split. Splitting anyway
    mistakes the ID's own fragments for repeats of the partition's absence
    sentence and silently drops them from the printed diagnosis. When any
    missing claim ID contains "; ", the full recorded reason must print
    verbatim, duplicate absence sentence and all.
    """

    stale_evidence(ambiguous_repo, AMBIGUOUS_ID)
    # The stale clause names the ambiguous ID verbatim; the absent clause
    # names lint-clean. "; "-joined, per _diagnosis().
    reason = f"{STALE}: {AMBIGUOUS_ID}; {ABSENCE}: lint-clean"

    assert run(ambiguous_repo, "--journal", "journal.sqlite3") == 1
    out = capsys.readouterr().out
    # The anti-truncation oracle: the whole recorded reason, verbatim.
    assert reason in out
    # The partition's own absence line still prints above it.
    assert f"      {ABSENCE}: lint-clean\n" in out

    from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

    entries = Journal(ambiguous_repo / "journal.sqlite3").entries()
    assert len(entries) == 1
    assert entries[0]["reason"] == reason
