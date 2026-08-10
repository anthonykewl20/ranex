"""SLICE-002 — the loop end to end, with signatures.

Written before the implementation and required to fail first.

    ranex keygen --producer worker         # key outside the repo
    ranex run    --producer worker -- ...  # signs what it observed
    ranex gate evaluate HEAD               # verifies, or refuses to count it

Pins one new CLI argument, `--producers`, defaulting to
`governance/producers.yaml`, so the committed keyring is addressable the same
way the gate catalog and evidence file already are.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from ranex.cli.main import main
from ranex.foundation.canonical import canonical_sha256, command_digest

# SLICE-003: a claim declares the command that satisfies it. `tests-executed`
# means this argv and nothing else, so `sh -c 'exit 0'` below is deliberately
# *not* the bound command — see the note on the first test.
BOUND = ["uv", "run", "pytest", "-q"]

GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]
"""

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "gates.yaml").write_text(GATES, encoding="utf-8")
    return repository


def commit_all(repo: Path, message: str = "initial") -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


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
    """Generate a key and return the `producers.yaml` line it prints."""

    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = invoke(repo, ["keygen", "--producer", producer], key_path)
    assert code == EXIT_PASS, buffer.getvalue()

    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", buffer.getvalue())
    assert match, f"keygen printed no public key: {buffer.getvalue()!r}"
    return match.group(1)


def write_keyring(repo: Path, **producers: str) -> None:
    lines = "\n".join(f"  {name}: {key}" for name, key in producers.items())
    (repo / "producers.yaml").write_text(f"producers:\n{lines}\n", encoding="utf-8")


def run_cmd(repo: Path, key_path: Path | None, *command: str,
            producer: str = "worker") -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", "tests-executed",
            "--producer", producer,
            "--repository", ".",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--", *command,
        ],
        key_path,
    )


def evaluate(repo: Path, approver: str = "reviewer_alice") -> int:
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


# --- the loop closes --------------------------------------------------------


def test_keygen_run_evaluate_refuses_an_unbound_command(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """SLICE-003 inverted this test, deliberately.

    It used to assert that `sh -c 'exit 0'` satisfied `tests-executed` — a
    correctly signed, subject-bound record that a gate accepted as proof the
    tests ran. That was the project's founding failure asserted as intended
    behaviour: the dart thrower painting the bullseye where the dart landed.

    Everything SLICE-002 proved still holds and is still asserted here: keygen
    writes a key, `run` signs what it observed, the record is well formed. What
    changed is the last line. Satisfaction now also asks *what ran*, and
    `sh -c 'exit 0'` is not the command the catalog binds to this claim.

    The bound command passing is not dropped, only moved — see
    `tests/e2e/test_claim_command_binding.py`.
    """

    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    write_keyring(repo, worker=public)
    commit_all(repo)

    assert run_cmd(repo, key_path, "sh", "-c", "exit 0") == EXIT_PASS

    (record,) = records(repo)
    assert record["signature"].startswith("ed25519:")
    assert record["command_digest"] == command_digest(["sh", "-c", "exit 0"])
    assert record["command_digest"] != command_digest(BOUND)

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL
    assert "PASS" not in capsys.readouterr().out


def test_hand_edited_record_fails_and_names_the_signature(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The headline attack: flip a failure into a pass with a text editor."""

    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    write_keyring(repo, worker=public)
    commit_all(repo)

    assert run_cmd(repo, key_path, "sh", "-c", "exit 1") == 1
    (record,) = records(repo)
    assert record["exit_code"] == 1

    record["exit_code"] = 0
    (repo / "evidence.json").write_text(json.dumps([record], indent=2), encoding="utf-8")

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL

    output = capsys.readouterr().out + capsys.readouterr().err
    assert "signature" in output.lower(), output
    # It must NOT read as honest absence. That is the distinction the whole
    # admission design exists to preserve.
    assert "no evidence for required claim" not in output


def test_unsigned_record_stops_counting(repo: Path, tmp_path: Path) -> None:
    """No migration, no grandfathering: an old unsigned record is unverifiable,
    so it is not evidence."""

    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    write_keyring(repo, worker=public)
    commit_all(repo)

    subject = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()

    # Complete and correct in every field, including the SLICE-003 command
    # binding, so the only thing wrong with it is the missing signature.
    (repo / "evidence.json").write_text(
        json.dumps([{
            "claim_id": "tests-executed",
            "subject_digest": "sha256:" + canonical_sha256({"tree": subject}),
            "producer_id": "worker",
            "command": "uv run pytest -q",
            "command_digest": command_digest(BOUND),
            "executable_path": "/usr/bin/uv",
            "exit_code": 0,
        }], indent=2),
        encoding="utf-8",
    )

    assert evaluate(repo) == EXIT_FAIL


# --- run refuses rather than producing evidence it knows will be rejected ----


def test_run_refuses_without_a_signing_key(repo: Path, tmp_path: Path) -> None:
    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    write_keyring(repo, worker=public)
    commit_all(repo)

    assert run_cmd(repo, None, "sh", "-c", "exit 0") == EXIT_USAGE
    assert not (repo / "evidence.json").exists()


def test_run_refuses_when_its_key_is_not_the_producers_key(
    repo: Path,
    tmp_path: Path,
) -> None:
    """Otherwise `run` burns a full test run to write a record that admission is
    guaranteed to reject."""

    worker_key = tmp_path / "worker.key"
    stranger_key = tmp_path / "stranger.key"
    keygen(repo, worker_key, producer="worker")
    stranger_public = keygen(repo, stranger_key, producer="stranger")

    # The keyring registers `worker` with the stranger's key, so the key at
    # $RANEX_SIGNING_KEY is not the one `worker` is trusted to sign with.
    write_keyring(repo, worker=stranger_public)
    commit_all(repo)

    marker = repo / "ran.txt"
    assert run_cmd(
        repo, worker_key, "sh", "-c", f"touch {marker.name}; exit 0"
    ) == EXIT_USAGE
    assert not marker.exists(), "refused only AFTER running the command"
    assert not (repo / "evidence.json").exists()
