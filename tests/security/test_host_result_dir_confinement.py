"""`--result-dir` is confined like every other path-taking flag.

Found by a sad-path sweep enumerated from argparse rather than written by hand:
31 leaf commands, 189 value-taking flags, each probed with a path escaping the
repository, an absolute path, an empty value, a newline, 4000 characters and a
shell metacharacter. 1153 cases, 12 defects — all of them this one flag.

`host launcher-build`, `launcher-install`, `host-probe` and `qualify` all take
`--result-dir`, and it reached `write_run_report` without passing through
`resolve_within_repository`. `result_dir / "logs"` was then created directly, so

    --result-dir ../../../etc/passwd   -> NotADirectoryError traceback
    --result-dir /etc/passwd           -> NotADirectoryError traceback
    --result-dir <4000 chars>          -> OSError [Errno 36] traceback

A traceback is the worst refusal shape available: an operator cannot tell it
from a crash, and it prints a stack where a reason belongs. The guard already
existed — this flag simply never reached it.

The hand-written sweeps that preceded this one scored 25/25 and 35/35 and found
none of it, because they probed the flags I thought of rather than the flags
that exist.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Every verb that accepts the flag, so a fifth cannot be added unguarded.
VERBS = ("launcher-build", "launcher-install", "host-probe", "qualify")

# Each value still refuses, but for the reason that is TRUE of it: the
# filesystem cannot use it. `--result-dir` is an operator output location like
# `--store` and `--credentials-dir`, both of which live outside the repository,
# so "outside the repository" was never the defect — `/etc/passwd/logs` is not
# a directory, and a 4000-character name is too long. Refusing every absolute
# path banned `--result-dir /var/log/ranex` and broke four contract tests that
# encode the shipped operator surface.
# Each shape must produce a NAMED refusal rather than a traceback. The errno
# behind it is deliberately not pinned: it is host-dependent. `/etc/passwd`
# gives EEXIST here (the path exists and is not a directory) and
# `../../../etc/passwd` resolves to /home/etc/passwd, giving EACCES on a host
# where /home is not writable and something else where it is. Asserting the
# refusal SHAPE — the flag named, the reason present, no stack — is the real
# contract; asserting a particular strerror would pin this suite to one
# machine's filesystem layout. ENAMETOOLONG is universal, so that one keeps its
# text as a spot check that the reason is the filesystem's own.
REFUSED = {
    "traversal": ("../../../etc/passwd", None),
    "absolute": ("/etc/passwd", None),
    "too-long": ("x" * 4000, "File name too long"),
}


def ranex(*args: str) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    for variable in ("RANEX_SIGNING_KEY", "RANEX_VERDICT_SIGNING_KEY", "RANEX_VERDICT_DIR"):
        environment.pop(variable, None)
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *args],
        cwd=REPO_ROOT, capture_output=True, text=True, env=environment, timeout=180,
    )


@pytest.mark.parametrize("verb", VERBS)
@pytest.mark.parametrize("shape", sorted(REFUSED))
def test_a_hostile_result_dir_is_a_named_refusal_not_a_traceback(
    verb: str, shape: str
) -> None:
    value, expected = REFUSED[shape]
    result = ranex("host", verb, "--result-dir", value)
    output = result.stdout + result.stderr

    assert "Traceback (most recent call last)" not in output, (
        f"host {verb} --result-dir <{shape}> crashed instead of refusing:\n"
        f"{output[-400:]}"
    )
    assert result.returncode != 0, f"host {verb} accepted a {shape} --result-dir"
    assert "refusing --result-dir" in output, (
        f"the refusal must name the flag it is about: {output[:300]!r}"
    )
    assert ":" in output.split("refusing --result-dir", 1)[1][:200], (
        f"the refusal must carry a reason, not only a verdict: {output[:300]!r}"
    )
    if expected is not None:
        assert expected in output, (
            f"the refusal must name why: expected {expected!r} in {output[:300]!r}"
        )


def test_the_refusal_does_not_echo_an_unbounded_value() -> None:
    """The value that provokes ENAMETOOLONG is too long to print.

    Echoing all 4000 characters buries the reason it was printed for.
    """

    result = ranex("host", "host-probe", "--result-dir", "x" * 4000)
    output = result.stdout + result.stderr
    assert "File name too long" in output
    assert "x" * 200 not in output, "the refusal echoed an unbounded value"
    assert "..." in output, "a truncated value should say that it was truncated"


def test_a_confinement_refusal_is_distinguishable_from_honest_absence() -> None:
    """A refusal that reads like absence is a reporting defect one layer out.

    ADR-011's whole point is that absence blocks *visibly*. If `--result-dir
    ../../../etc/passwd` and a genuinely missing artifact produced the same
    words, an operator could not tell "you pointed outside the repository"
    from "the thing you asked about is not there" — and would debug the wrong
    one. Raised in peer review of the sweep; worth pinning rather than
    assuming.
    """

    traversal = ranex("host", "host-probe", "--result-dir", "../../../etc/passwd")
    absence = ranex("journal", "verify", "--journal", "governance/absent.sqlite3")

    traversal_text = (traversal.stdout + traversal.stderr).strip()
    absence_text = (absence.stdout + absence.stderr).strip()

    assert traversal.returncode != 0 and absence.returncode != 0
    assert traversal_text != absence_text
    assert "refusing --result-dir" in traversal_text
    assert "does not exist" in absence_text
    assert "refusing --result-dir" not in absence_text, (
        "an absent file must not be reported as an unusable output path"
    )


def test_a_legitimate_result_dir_is_still_accepted(tmp_path: Path) -> None:
    """The guard must refuse the hostile shapes and nothing else.

    A relative path inside the repository is the documented normal usage, and
    a guard that also refused that would be worse than the crash it replaced.
    `host-probe` may still fail on host facts — that is a different, named
    refusal, and this only asserts the path was not what stopped it.
    """

    result = ranex("host", "host-probe", "--result-dir", ".local/ranex/host-results")
    output = result.stdout + result.stderr
    assert "refusing --result-dir" not in output, output[:300]
    assert "Traceback (most recent call last)" not in output


def test_an_absolute_result_dir_that_is_usable_succeeds(tmp_path: Path) -> None:
    """The assertion whose absence let the over-broad fix ship.

    `--result-dir` names where an operator wants run reports, and an operator
    legitimately wants them outside the governed tree — `--store` defaults
    outside it and `--credentials-dir` must be outside it. A guard that refuses
    every absolute path passes all three hostile cases above while breaking the
    flag's normal use, and nothing here would have noticed. This is the
    positive control: a usable absolute path must work and leave its report.
    """

    destination = tmp_path / "reports"
    completed = ranex("host", "host-probe", "--result-dir", str(destination))

    combined = completed.stdout + completed.stderr
    assert "refusing --result-dir" not in combined, (
        f"a usable absolute --result-dir was refused: {combined[:400]}"
    )
    assert destination.is_dir(), "the run did not create the directory it was given"
