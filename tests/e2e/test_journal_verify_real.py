"""SLICE-056 — real e2e: the verdict family (journal verify) on real data.

Issue #36's exact ownership (file 2 of 2), riding the ADR-032 frame: a
real journey — this repository cloned at HEAD as the real subject, real
``gate evaluate`` subprocess runs writing a real hash-chained journal,
then the operator-facing ``journal verify`` CLI over it — whose captured
transcripts compare byte-exactly against golden ``.out`` files through
the one centralized normalizer (``_prereqs.normalize_transcript``).

The journey (every step verified against the installed kernel before
this file was frozen):

1. Two real evaluations of the pristine clone's real ``landing`` gate
   (no evidence — honest FAILs, real data) write a two-row journal: a
   real chain, genesis → row 1 → row 2.
2. ``journal verify`` over that chain prints the clean PASS transcript.
   The stdlib ``sqlite3`` module — the issue's named independent tool —
   re-reads the rows the CLI reported on and checks the chain's link
   continuity as pure data (each row's ``prev_link`` is exactly the
   previous row's ``link``; no kernel code involved).
3. A single byte of row 1's record is flipped (inside the first digest
   hex run, so the row stays parseable JSON — the edit must be detected
   by the chain, not by a parse error), and ``journal verify`` must FAIL
   **naming the row** (issue #36 sad path 3). The frozen contract is
   deliberately red on the naming until the implementation lane lands
   it: today's CLI prints only ``chain=invalid`` with no row identity,
   which is exactly the behavioral red this file freezes.
4. The rollback blind spot, characterized honestly per issue #36 sad
   path 4 ("the test asserts the documented outcome whatever it is"):
   a journal whose last row is deleted out-of-band still verifies
   ``PASS chain=verified`` — the chain over the surviving rows is
   vacuously intact, so a vanished record is invisible to the verifier.
   The truncation arm freezes that documented outcome and the stdlib
   sqlite3 module independently confirms the row really is gone; the
   characterization is recorded in the SLICE-056 slice file for the ADR
   delta the issue's workflow checklist owns.

The goldens ``expected/journal-verify-clean.out`` and
``expected/journal-verify-tampered.out`` are the implementation lane's
artifacts, captured from a real run of this journey through the
normalizer; their absence is this file's honest frozen red. The
sabotage control and the normalizer-application contract refuse every
hand-sanitized golden shape, exactly as in the gate-evaluate file.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

JOURNAL_RELATIVE = "governance/journal.sqlite3"
TRUNCATED_RELATIVE = "governance/journal-truncated.sqlite3"

#: See test_gate_evaluate_real.py's _STRIPPED_ENV for the rationale.
_STRIPPED_ENV = (
    "RANEX_SIGNING_KEY",
    "RANEX_VERDICT_SIGNING_KEY",
    "RANEX_VERDICT_DIR",
    "COVERAGE_PROCESS_START",
    "COVERAGE_PROCESS_CONFIG",
    "COVERAGE_FILE",
)


def ranex(subject: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way an operator does: a real process, the
    subject's own source on PYTHONPATH (the clone judges the clone)."""

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    env["PYTHONPATH"] = str(subject / "src")
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=subject,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def golden_text(name: str) -> str:
    """Read a family golden, refusing its absence loudly (the frozen red)."""

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-056 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture above), pipe the CLI stdout through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


def _flip_one_byte(text: str) -> str:
    """Flip exactly one byte of the first digest hex run, keeping the row
    parseable JSON: the chain, not a parser, must catch the edit."""

    match = re.search(r"sha256:[0-9a-f]", text)
    assert match is not None, f"the record carries no digest to edit: {text!r}"
    index = match.end()
    return text[:index] + ("0" if text[index] != "0" else "1") + text[index + 1 :]


@dataclass
class JournalJourney:
    """Everything the frozen tests consume from the one module journey."""

    subject: Path
    clean_transcript: str
    tampered_transcript: str
    truncated_transcript: str
    tampered_seq: int
    original_record: str
    tampered_record: str


@pytest.fixture(scope="module")
def journey(tmp_path_factory: pytest.TempPathFactory) -> JournalJourney:
    """The one real journey: a real journal, verified, tampered, rolled back."""

    base = tmp_path_factory.mktemp("verdict-family-journal")
    subject = base / "subject"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(subject)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, f"cannot clone the real subject: {cloned.stderr}"

    # Two real evaluations write a real two-row chain. Both FAILs are the
    # honest no-evidence verdicts of the real landing gate — real data.
    for attempt in (1, 2):
        evaluation = ranex(
            subject,
            ["gate", "evaluate", "HEAD", "--repository", ".", "--approver", "reviewer"],
        )
        assert evaluation.returncode == 1, (
            f"no-evidence evaluation {attempt} must FAIL (exit 1): "
            f"{evaluation.stdout}{evaluation.stderr}"
        )

    journal = subject / JOURNAL_RELATIVE
    clean = ranex(
        subject, ["journal", "verify", "--repository", ".", "--journal", JOURNAL_RELATIVE]
    )
    assert clean.returncode == 0, (
        f"the untouched chain must verify (exit 0): {clean.stdout}{clean.stderr}"
    )
    assert clean.stdout.startswith("PASS"), clean.stdout

    # The rollback blind spot: copy the CLEAN chain while it is still
    # untouched, then delete the copy's LAST row out-of-band (the
    # append-only triggers refuse nothing once dropped — this is the
    # out-of-band edit the chain exists to catch) and verify the copy:
    # the chain over the surviving rows is vacuously intact.
    truncated = subject / TRUNCATED_RELATIVE
    shutil.copy(journal, truncated)
    connection = sqlite3.connect(truncated)
    try:
        connection.execute("DROP TRIGGER evaluations_no_delete")
        connection.execute("DELETE FROM evaluations WHERE seq = (SELECT MAX(seq) FROM evaluations)")
        connection.commit()
    finally:
        connection.close()
    truncated_run = ranex(
        subject, ["journal", "verify", "--repository", ".", "--journal", TRUNCATED_RELATIVE]
    )

    # A single byte of the first row's record, edited out-of-band.
    connection = sqlite3.connect(journal)
    try:
        row = connection.execute(
            "SELECT seq, record FROM evaluations ORDER BY seq LIMIT 1"
        ).fetchone()
        assert row is not None, "the evaluations wrote no journal rows to tamper"
        seq, record = row
        tampered = _flip_one_byte(record)
        connection.execute("DROP TRIGGER evaluations_no_update")
        connection.execute("UPDATE evaluations SET record = ? WHERE seq = ?", (tampered, seq))
        connection.commit()
    finally:
        connection.close()

    tampered_run = ranex(
        subject, ["journal", "verify", "--repository", ".", "--journal", JOURNAL_RELATIVE]
    )
    assert tampered_run.returncode == 1, (
        "the byte-edited chain must FAIL verification (exit 1): "
        f"{tampered_run.stdout}{tampered_run.stderr}"
    )

    return JournalJourney(
        subject=subject,
        clean_transcript=clean.stdout,
        tampered_transcript=tampered_run.stdout,
        truncated_transcript=truncated_run.stdout,
        tampered_seq=seq,
        original_record=record,
        tampered_record=tampered,
    )


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


def test_clean_transcript_matches_the_golden(journey: JournalJourney) -> None:
    """The clean-chain PASS transcript, byte-frozen against its golden.

    Independent re-check first (issue #36: a non-kernel tool reads what
    the CLI reported on): the stdlib sqlite3 module re-reads the journal
    rows the CLI just verified and checks the chain as pure data — the
    two rows the evaluations wrote, each row's ``prev_link`` exactly the
    previous row's ``link``, the first rooted at the genesis link, and
    every record an honest FAIL verdict of the real landing gate.
    """

    journal = journey.subject / JOURNAL_RELATIVE
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT seq, record, prev_link, link FROM evaluations ORDER BY seq"
        ).fetchall()
    finally:
        connection.close()
    assert len(rows) == 2, f"expected the two evaluation rows, got {len(rows)}"
    genesis = "sha256:" + "0" * 64
    previous = genesis
    for seq, record, prev_link, link in rows:
        assert prev_link == previous, (
            f"row {seq} does not chain to its predecessor as data: {prev_link!r} != {previous!r}"
        )
        parsed = json.loads(record)
        assert parsed["gate_id"] == "landing", parsed
        assert parsed["verdict"] == "FAIL", parsed
        previous = link

    compare_golden(journey.clean_transcript, "journal-verify-clean.out")


def test_tampered_row_detection_names_the_row_and_rolls_back_honestly(
    journey: JournalJourney,
) -> None:
    """The tampered-journal FAIL: detected, the row named, goldens frozen.

    Three frozen layers: (1) the edit really was a single byte — proven
    against the original record text, so the detection claim is honest;
    (2) the FAIL transcript must name WHICH row failed the chain (issue
    #36 sad path 3) — deliberately red until the implementation lands
    it, since today's CLI prints only ``chain=invalid``; (3) the
    rollback blind spot is asserted as the documented outcome (issue #36
    sad path 4): a journal whose last row was deleted out-of-band still
    verifies PASS, with the stdlib sqlite3 module independently
    confirming the row is really gone.
    """

    # (1) exactly one byte differs between the original and edited row.
    assert len(journey.original_record) == len(journey.tampered_record), (
        "the tamper must keep the record's length — a single byte flip"
    )
    differences = [
        index
        for index, (before, after) in enumerate(
            zip(journey.original_record, journey.tampered_record, strict=True)
        )
        if before != after
    ]
    assert len(differences) == 1, (
        f"the tamper must be exactly one byte; differing positions: {differences}"
    )

    # (2) detection must FAIL and NAME the row.
    assert journey.tampered_transcript.startswith("FAIL"), journey.tampered_transcript
    assert "chain=invalid" in journey.tampered_transcript, journey.tampered_transcript
    named = re.search(rf"\b(?:row|seq)[= :]+{journey.tampered_seq}\b", journey.tampered_transcript)
    assert named is not None, (
        "the tampered-journal FAIL must name the row that broke the "
        f"chain (expected row/seq {journey.tampered_seq}); today's CLI "
        "prints only 'chain=invalid' — this is the frozen behavioral "
        "red of issue #36 sad path 3, landed by the implementation lane"
    )

    # (3) the characterized rollback blind spot, asserted as documented.
    truncated = journey.subject / TRUNCATED_RELATIVE
    connection = sqlite3.connect(f"{truncated.as_uri()}?mode=ro", uri=True)
    try:
        remaining = connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
    finally:
        connection.close()
    assert remaining == 1, (
        f"the rollback arm must have deleted exactly the last row (got {remaining} remaining)"
    )
    assert journey.truncated_transcript.startswith("PASS"), (
        "the DOCUMENTED outcome of the rollback blind spot (issue #36 "
        "sad path 4) is a verifying PASS over the surviving rows: "
        f"{journey.truncated_transcript!r}"
    )
    assert "chain=verified" in journey.truncated_transcript

    compare_golden(journey.tampered_transcript, "journal-verify-tampered.out")


def test_goldens_carry_real_volatile_material(journey: JournalJourney) -> None:
    """The goldens are machine-normalized captures, not hand-sanitized text.

    Same three-refusal contract as the gate-evaluate file, on the
    journal family's own volatile material: the journal path the CLI
    prints is a live absolute path, so each golden must carry
    ``<ABS-PATH>`` where it appeared, be a normalizer fixpoint, and a
    golden holding the live path bytes provably cannot match.
    """

    live_path = re.search(r"journal=(\S+)", journey.clean_transcript)
    assert live_path is not None, journey.clean_transcript
    for name, transcript in (
        ("journal-verify-clean.out", journey.clean_transcript),
        ("journal-verify-tampered.out", journey.tampered_transcript),
    ):
        golden = golden_text(name)
        assert "<ABS-PATH>" in golden, (
            f"{name} carries no <ABS-PATH> token: the journal path the "
            "CLI prints is real volatile material the normalizer must "
            "have tamed — a golden without the token is hand-sanitized "
            "text, not a captured transcript"
        )
        assert _prereqs.normalize_transcript(golden) == golden, (
            f"{name} is not a normalizer fixpoint: it still contains "
            "bytes the frozen grammar would mask, which no capture "
            "piped through normalize_transcript can"
        )
        doctored = golden.replace("<ABS-PATH>", live_path.group(1), 1)
        with pytest.raises(AssertionError):
            _prereqs.compare_transcript(
                _normalized(transcript), doctored, family=name.removesuffix(".out")
            )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: JournalJourney) -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte
    of the expected file and the comparator must diff dirty, naming the
    family and carrying exactly the first differing hunk."""

    for name, transcript, verdict_word in (
        ("journal-verify-clean.out", journey.clean_transcript, "PASS"),
        ("journal-verify-tampered.out", journey.tampered_transcript, "FAIL"),
    ):
        golden = golden_text(name)
        family = name.removesuffix(".out")
        assert verdict_word in golden, golden
        mutated = golden.replace(verdict_word, "Q" + verdict_word[1:], 1)
        with pytest.raises(AssertionError) as raised:
            _prereqs.compare_transcript(_normalized(transcript), mutated, family=family)
        message = str(raised.value)
        assert family in message, f"the mismatch must name the golden family {family!r}: {message}"
        assert "@@" in message, (
            "the mismatch must carry the first differing hunk header: " + message
        )
        assert "Q" + verdict_word[1:] in message, (
            "the first hunk must show the mutated bytes untruncated: " + message
        )
