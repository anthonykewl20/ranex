"""SLICE-003 — the binding, through the real CLI.

Written before the implementation and required to fail first.

Reproducible today, and the reason this slice exists:

    ranex run --claim tests-executed --producer worker -- true

yields a correctly signed, subject-bound record that satisfies a gate requiring
`tests-executed`. The signature proves who recorded it; the subject digest proves
which tree it was recorded against. Neither proves any work happened.

Done criteria 1, 2 and 8 of docs/slices/SLICE-003-claim-command-binding.md.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import subprocess
from pathlib import Path

import pytest

from ranex.cli.main import main
from ranex.foundation.canonical import command_digest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

# The bound command does real work against the committed tree, so a claim
# satisfied by it is a claim about *this* tree. A catalog naming `true` would be
# the defect wearing the new schema.
CHECK_SCRIPT = "grep -qx content file.txt\n"
BOUND = ["sh", "check.sh"]


def build_gates(claim_id: str, argv: list[str]) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        f"      - claim_id: {claim_id}\n"
        f"        command: {json.dumps(argv)}\n"
    )


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "check.sh").write_text(CHECK_SCRIPT, encoding="utf-8")
    return repository


def invoke(repo: Path, argv: list[str], key_path: Path | None = None) -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        if key_path is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv("RANEX_SIGNING_KEY", str(key_path))
        return main(argv)


def keygen(repo: Path, key_path: Path, producer: str = "worker") -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = invoke(repo, ["keygen", "--producer", producer], key_path)
    assert code == EXIT_PASS, buffer.getvalue()
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", buffer.getvalue())
    assert match, f"keygen printed no public key: {buffer.getvalue()!r}"
    return match.group(1)


def prepare(
    repo: Path,
    tmp_path: Path,
    *,
    argv: list[str] = BOUND,
    claim: str = "tests-executed",
) -> Path:
    """Commit the catalog, the keyring and the tree. Return the key path.

    Everything the verdict depends on is committed before anything runs, because
    `gate evaluate` refuses a trust root the ref does not carry.
    """

    (repo / "gates.yaml").write_text(build_gates(claim, argv), encoding="utf-8")
    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    (repo / "producers.yaml").write_text(
        f"producers:\n  worker: {public}\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "initial"], check=True
    )
    return key_path


def run_cmd(
    repo: Path,
    key_path: Path,
    *command: str,
    claim: str = "tests-executed",
) -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", claim,
            "--producer", "worker",
            "--repository", ".",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--", *command,
        ],
        key_path,
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


def records(repo: Path) -> list[dict]:
    return json.loads((repo / "evidence.json").read_text(encoding="utf-8"))


# --- criterion 1: `-- true` records honestly and satisfies nothing ----------


def test_true_produces_evidence_that_does_not_satisfy_the_claim(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The founding failure, in one command.

    `run` still records it: `true` exited 0 and that is what was observed, so
    refusing to write would be `run` judging, which is not its job. The record is
    signed, bound to this tree, and completely honest. It simply is not evidence
    for `tests-executed`, because `tests-executed` names a different command.
    """

    key_path = prepare(repo, tmp_path)

    assert run_cmd(repo, key_path, "true") == EXIT_PASS
    (record,) = records(repo)
    assert record["exit_code"] == 0
    assert record["signature"].startswith("ed25519:")
    assert record["command_digest"] == command_digest(["true"]), (
        "the record must state which command it observed, in the form the gate "
        "compares"
    )

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL
    output = capsys.readouterr().out
    assert "PASS" not in output, output
    assert "tests-executed" in output, output


# --- criterion 2: the bound command does satisfy ----------------------------


def test_the_catalog_bound_command_satisfies_the_claim(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The loop still closes. A binding that nothing can satisfy is a broken
    gate, not a control."""

    key_path = prepare(repo, tmp_path)

    assert run_cmd(repo, key_path, *BOUND) == EXIT_PASS
    (record,) = records(repo)
    assert record["command_digest"] == command_digest(BOUND)

    capsys.readouterr()
    assert evaluate(repo) == EXIT_PASS
    assert "PASS" in capsys.readouterr().out


def test_the_recorded_digest_is_the_digest_of_the_argv_that_ran(
    repo: Path,
    tmp_path: Path,
) -> None:
    """`run` must record what it spawned, not what it was told to claim.

    Pinned against the same formula the catalog uses, computed here from the
    argv rather than read back out of the record, so a change to either side
    that leaves them agreeing with each other but not with the spec is caught.
    """

    key_path = prepare(repo, tmp_path)
    assert run_cmd(repo, key_path, "sh", "-c", "exit 0") == EXIT_PASS

    (record,) = records(repo)
    assert record["command_digest"] == command_digest(["sh", "-c", "exit 0"])
    assert record["command"] == "sh -c 'exit 0'", (
        "the readable command stays, so review can see what ran without "
        "reversing a digest"
    )


# --- criterion 8: argument order is part of the binding ---------------------


def test_argv_in_a_different_order_is_a_different_command(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`true alpha beta` and `true beta alpha` both exit 0 against any tree.

    They differ only in argument order, which is exactly the distinction a
    string-and-shell comparison loses and a digest over argv keeps.
    """

    bound = ["true", "alpha", "beta"]
    key_path = prepare(repo, tmp_path, argv=bound)

    assert run_cmd(repo, key_path, "true", "beta", "alpha") == EXIT_PASS
    (record,) = records(repo)
    assert record["command_digest"] != command_digest(bound)

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL
    assert "PASS" not in capsys.readouterr().out

    # And the bound order does satisfy, so the refusal above is about order and
    # not about the binding being unsatisfiable.
    assert run_cmd(repo, key_path, *bound) == EXIT_PASS
    capsys.readouterr()
    assert evaluate(repo) == EXIT_PASS
