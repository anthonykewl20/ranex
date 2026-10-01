"""A verdict must not change when nobody is watching through a terminal.

Rule 1 of the verdict presentation contract: the *content* of output is
invariant under TTY detection. Styling — colour, bold, dim, glyph choice — may
differ. Wording, ordering, field values and which lines appear may not. A
verdict that reads one way in CI and another on a desk is not evidence.

Two claims, deliberately separated, because they are not the same strength:

* Everything the CLI prints must carry identical content either way.
* A *verdict* must additionally carry no styling at all.

The second is narrower on purpose. Python 3.14 gave `argparse` a `color`
parameter and turned colouring on for help and usage text when stdout is a
terminal, so `--help` is styled today without anyone in this repository choosing
it. Help is not evidence, so that is accepted. It is also the reason this file
exists rather than a one-line search for `isatty`: styling arrived here through
a dependency upgrade, not a commit.

ADR-018 is what puts the narrow claim at risk — the redesigned TUI styles
everything through a generated theme and is the surface that renders verdicts
next.
"""

from __future__ import annotations

import json
import os
import pty
import re
import subprocess
import sys
from pathlib import Path

import _approver
import _history
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "src" / "ranex"

ESC = b"\x1b"

# CSI sequences, which is all either argparse or a future renderer emits here.
# Stripped only to compare *content*; never to excuse a difference in content.
_ANSI = re.compile(rb"\x1b\[[0-9;]*[A-Za-z]")

# The pty line discipline turns "\n" into "\r\n" on the way out. That is the
# terminal driver's doing, not the program's, so it is normalised away before
# comparing. Nothing else is.
_CR = re.compile(rb"\r$", re.MULTILINE)


def _cli(*args: str) -> list[str]:
    return [sys.executable, "-m", "ranex.cli.main", *args]


def _environment(verdict: bool = False, extra: dict[str, str] | None = None) -> dict[str, str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment.pop("NO_COLOR", None)
    for variable in ("RANEX_APPROVER_SIGNING_KEY", "RANEX_VERDICT_SIGNING_KEY",
                     "RANEX_VERDICT_DIR", "RANEX_HISTORY_CHECKPOINT"):
        environment.pop(variable, None)
    environment.update(extra or {})
    return environment


def _through_pipe(args: list[str], *, verdict: bool = False, extra=None) -> bytes:
    """stdout and stderr interleaved, with neither attached to a terminal."""

    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=_environment(verdict, extra),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=600,
        check=False,
    )
    return completed.stdout


def _through_pty(args: list[str], *, verdict: bool = False, extra=None) -> bytes:
    """The same command with a real terminal on both streams."""

    master, slave = pty.openpty()
    process = subprocess.Popen(
        args,
        cwd=REPO_ROOT,
        env=_environment(verdict, extra),
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)

    chunks: list[bytes] = []
    while True:
        # Linux raises EIO on the master once the last slave fd closes; that is
        # end of output, not a failure.
        try:
            data = os.read(master, 65536)
        except OSError:
            break
        if not data:
            break
        chunks.append(data)

    os.close(master)
    process.wait(timeout=600)
    return _CR.sub(b"", b"".join(chunks))


def _subject(tmp_path: Path) -> tuple[Path, dict[str, str], str, str, Path]:
    from ranex.foundation.signing import generate_keypair

    repository = tmp_path / "subject"
    repository.mkdir()
    governance = repository / "governance"
    governance.mkdir()
    _, worker = generate_keypair()
    (governance / "producers.yaml").write_text(f"producers:\n  worker: {worker}\n")
    approver, public = _approver.mint_approver(tmp_path)
    _approver.register_approver(governance / "producers.yaml", "release-approver", public)
    private, service, key = _history.mint_service(tmp_path)
    _history.register_service(governance / "producers.yaml", service)
    catalog = (
        "gates:\n  - gate_id: landing\n    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n    required_claims:\n"
    )
    for claim in ("tests-executed", "host-qualification", "architecture"):
        catalog += f"      - claim_id: {claim}\n        command: [\"{claim}\"]\n"
    (governance / "gates.yaml").write_text(catalog)
    for args in (("init", "-q"), ("config", "user.email", "fixture@example.invalid"),
                 ("config", "user.name", "Fixture"), ("add", "."), ("commit", "-qm", "fixture")):
        subprocess.run(["git", "-C", str(repository), *args], check=True, capture_output=True)
    checkpoint = tmp_path / "history.json"
    _history.establish(repository, "governance/evidence.json", checkpoint, private, service)
    environment = {"RANEX_APPROVER_SIGNING_KEY": str(approver),
                   "RANEX_VERDICT_SIGNING_KEY": str(key),
                   "RANEX_HISTORY_CHECKPOINT": str(checkpoint)}
    return repository, environment, private, service, checkpoint


def _verdict_arguments(tmp_path: Path) -> tuple[list[str], Path, dict[str, str]]:
    repository, environment, _, _, _ = _subject(tmp_path)
    journal = repository / "governance" / "presentation.sqlite3"
    arguments = [
        "gate", "evaluate", "HEAD", "--external-repository", str(repository),
        "--approver", "release-approver", "--journal", "governance/presentation.sqlite3",
    ]
    return arguments, journal, environment


# One invocation per output shape the CLI has. A rule proven only on the happy
# path is a rule proven on the part that was never in doubt.
_INVOCATIONS = ("verdict", "usage-error", "help")


def _run(name: str, tmp_path: Path) -> tuple[bytes, bytes]:
    journal: Path | None = None
    environment = None
    if name == "verdict":
        arguments, journal, environment = _verdict_arguments(tmp_path)
    elif name == "usage-error":
        arguments = ["gate", "evaluate", "HEAD"]  # no --approver
    else:
        arguments = ["gate", "evaluate", "--help"]

    try:
        verdict = name == "verdict"
        return (
            _through_pipe(_cli(*arguments), verdict=verdict, extra=environment),
            _through_pty(_cli(*arguments), verdict=verdict, extra=environment),
        )
    finally:
        if journal is not None:
            journal.unlink(missing_ok=True)


@pytest.mark.parametrize("name", _INVOCATIONS)
def test_content_is_identical_under_pipe_and_pty(name: str, tmp_path: Path) -> None:
    """The same command, watched and unwatched, says exactly the same thing."""

    piped, attended = _run(name, tmp_path)

    assert piped, f"{name} produced no output, so this test would prove nothing"
    assert _ANSI.sub(b"", piped) == _ANSI.sub(b"", attended), (
        f"{name}: content differs between a pipe and a terminal, which is a "
        f"defect no amount of styling policy excuses.\n"
        f"piped:    {piped!r}\n"
        f"attended: {attended!r}"
    )


def test_a_verdict_carries_no_styling_even_on_a_terminal(tmp_path: Path) -> None:
    """Equality alone would pass two identically coloured captures. A verdict is
    held to the stronger claim: it is undecorated wherever it is read."""

    piped, attended = _run("verdict", tmp_path)

    assert b"FAIL" in attended or b"PASS" in attended, (
        "the verdict invocation printed no verdict, so this proves nothing"
    )
    assert ESC not in attended, (
        "an escape sequence reached a terminal on the verdict path. Styling may "
        "differ between destinations only where content does not, and a verdict "
        "is the one surface that must stay plain."
    )
    assert ESC not in piped


# Grepping the source is not a substitute for running the command, but it fails
# on the *first* line of styling rather than on the first line a test happens to
# exercise. It cannot see styling that arrives from a dependency — argparse is
# exactly that case — which is why both checks exist.
_STYLING = re.compile(
    r"\bisatty\b|\bcolorama\b|\btermcolor\b|from\s+rich\b|import\s+rich\b"
    r"|click\.style|\\x1b\[|\\033\[",
)


def test_source_contains_no_styling_primitives() -> None:
    """`src/ranex` decides verdicts; it does not decorate them."""

    offenders = [
        f"{path.relative_to(REPO_ROOT)}:{number}"
        for path in sorted(SOURCE.rglob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if _STYLING.search(line)
    ]
    assert not offenders, (
        "styling primitives in the kernel CLI: "
        + ", ".join(offenders)
        + ". Content is computed before any TTY check; styling belongs to a "
        "later step that cannot add, remove, reorder or reword a line."
    )


def test_refused_and_unattributable_stdout_stays_byte_exact() -> None:
    """The pure formatter preserves diagnosis for records with no usable claim."""
    from ranex.foundation.canonical import command_digest
    from ranex.governed_execution.domain.admission import admit
    from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate
    from ranex.governed_execution.verdict_presentation import render_verdict_stdout
    from ranex.governed_execution.verdict_projection import project_verdict

    subject = "sha256:" + "a" * 64
    gate = Gate("landing", "TESTS_EXECUTED", tuple(
        Claim(claim, command_digest([claim]))
        for claim in ("tests-executed", "host-qualification", "architecture")
    ), True)
    admission = admit([{"claim_id": "tests-executed"}, {"claim_id": 7}], {})
    result = evaluate(gate, admission.evidence, subject_digest=subject, approver_id="owner")
    projected = project_verdict(result, admission, required_claims=tuple(
        claim.claim_id for claim in gate.required_claims), journal_head=None)
    rendered = render_verdict_stdout(result, admission, projected).encode()
    expected = (
        b"FAIL  gate=landing  rule=TESTS_EXECUTED\n"
        b"      REFUSED record 0 [malformed-record] missing field(s): catalog_digest, command, command_digest, confinement_profile_digest, confinement_result_digest, envelope_type, executable_path, exit_code, gate_id, producer_id, subject_digest, suite_results\n"
        b"      REFUSED record 1 [malformed-record] missing field(s): catalog_digest, command, command_digest, confinement_profile_digest, confinement_result_digest, envelope_type, executable_path, exit_code, gate_id, producer_id, subject_digest, suite_results\n"
        b"      2 record(s) were refused above; no verifying evidence remains for: tests-executed\n"
        b"      1 record(s) above were refused without a usable claim_id, so these required claims cannot be called work never done: architecture, host-qualification\n"
    ) + f"      subject={subject}\n".encode()
    assert rendered == expected


def test_anchored_cli_refuses_malformed_projection_before_judgment(tmp_path: Path) -> None:
    repository, environment, _, _, _ = _subject(tmp_path)
    (repository / "governance/evidence.json").write_text(json.dumps([
        {"claim_id": "tests-executed"}, {"claim_id": 7},
    ]))
    command = _cli("gate", "evaluate", "HEAD", "--external-repository", str(repository),
                   "--approver", "release-approver")
    piped = _through_pipe(command, verdict=True, extra=environment)
    attended = _through_pty(command, verdict=True, extra=environment)
    assert piped == b"ERROR  E-OBSERVATION-CHAIN: projection includes unchained records\n"
    assert attended == piped
    assert not (repository / "governance/journal.sqlite3").exists()
