"""ADR-001 improvement 2 — PATH aliasing is closed by not using PATH for trust.

Written before the implementation and required to fail first.

in-toto declares `expected_command` per step and then refuses to enforce it. Its
own specification (§4.3.1) says why: the field "can easily be forged (e.g., by
changing the PATH environment variable)… should not be trusted for security
checks", so a mismatch is a warning and never a verification failure. Copying
that as-is would ship a control that does nothing.

Ranex spawns the process itself, so it can do what in-toto cannot. The kernel
resolves `argv[0]` **once**, and:

- refuses to execute at all if the resolution lands inside the subject worktree,
  because a worker that can drop `./pytest` in the repo it is being judged on
  chooses what `tests-executed` means;
- resolves symlinks *before* deciding containment, so a link outside the tree
  pointing back into it is the same attack and gets the same answer;
- refuses, clearly, when `argv[0]` resolves to nothing — a command that never ran
  must not be reported as a command with an exit code;
- records the resolved absolute path as the signed `executable_path`, so the
  decision is re-checkable at evaluation instead of being taken on trust.

The signature and evaluate-time halves live in
tests/security/test_slice003_command_binding.py. This file is about `run`.

Imports of `ranex` are deferred into fixtures and test bodies: a module-level
import of a symbol a fix has not created yet is a collection error, and a
collection error takes the whole suite down with it.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

CHECK_SCRIPT = "grep -qx content file.txt\n"
BOUND = ["sh", "check.sh"]

# What `run` must record for `sh`: resolved through every symlink, absolute.
RESOLVED_SH = str(Path(shutil.which("sh")).resolve())

# A tiny executable the tests plant *inside* the repository under observation.
SHADOW = "#!/bin/sh\nexit 0\n"


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
def keys(tmp_path: Path) -> dict[str, str]:
    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    path = tmp_path / "worker.key"
    path.write_text(private + "\n", encoding="utf-8")
    path.chmod(0o600)
    return {"private": private, "public": public, "path": str(path)}


@pytest.fixture()
def repo(tmp_path: Path, keys: dict[str, str]) -> Path:
    """A committed repository that also carries a planted executable."""

    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "check.sh").write_text(CHECK_SCRIPT, encoding="utf-8")
    (repository / "gates.yaml").write_text(
        build_gates("tests-executed", BOUND), encoding="utf-8"
    )
    # Committed, so the tree stays clean and the refusal under test is about
    # where the binary lives rather than about a dirty working tree.
    shadow = repository / "sh"
    shadow.write_text(SHADOW, encoding="utf-8")
    shadow.chmod(0o755)
    (repository / "producers.yaml").write_text(
        f"producers:\n  worker: {keys['public']}\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    return repository


def invoke(repo: Path, argv: list[str], key_path: str | None) -> int:
    from ranex.cli.main import main

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        if key_path is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv("RANEX_SIGNING_KEY", key_path)
        return main(argv)


def run_cmd(repo: Path, keys: dict[str, str], *command: str) -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", "tests-executed",
            "--producer", "worker",
            "--repository", ".",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--", *command,
        ],
        keys["path"],
    )


def records(repo: Path) -> list[dict]:
    return json.loads((repo / "evidence.json").read_text(encoding="utf-8"))


# --- the resolved path is what gets recorded --------------------------------


def test_run_records_the_resolved_absolute_executable_path(
    repo: Path,
    keys: dict[str, str],
) -> None:
    """Resolved once, and the resolved value is the one written down.

    Recording the name and checking the resolution would be a check-then-use
    gap: the field a verifier reads would not be the field the refusal was
    decided on.
    """

    assert run_cmd(repo, keys, *BOUND) == EXIT_PASS

    (record,) = records(repo)
    path = record["executable_path"]
    assert Path(path).is_absolute(), path
    assert path == RESOLVED_SH, (
        "executable_path must be argv[0] resolved through PATH and through "
        "every symlink, so the containment check and the record agree"
    )


# --- argv[0] must not live in the tree under observation --------------------


def test_run_refuses_an_executable_inside_the_repository(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The forgery in-toto concedes it cannot stop.

    `./sh` is committed in the repository being judged. If `run` executes it,
    the worker has chosen what `tests-executed` means by writing a file into the
    tree its own evidence describes — the bullseye painted around the dart, one
    layer down.

    The exit code alone is a weak assertion: `run` exits 2 for a dirty tree, an
    unwritable evidence file and a dozen other refusals, so a generic failure
    passes this test while proving nothing about containment. The message is
    checked too, and it must name both the binary and where it landed.
    """

    marker = tmp_path / "ran-from-inside"
    (repo / "sh").write_text(
        f'#!/bin/sh\ntouch "{marker}"\nexit 0\n', encoding="utf-8"
    )
    (repo / "sh").chmod(0o755)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "shadow"], check=True
    )

    capsys.readouterr()
    code = run_cmd(repo, keys, "./sh", "check.sh")
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_USAGE, (
        "an executable inside the subject worktree was accepted as argv[0]: "
        + output
    )
    assert not marker.exists(), "refused only AFTER running the planted binary"
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"
    assert "/tree/sh" in output, (
        "the refusal must name the resolved path it objected to, so an operator "
        "can tell containment apart from a dirty tree: " + output
    )
    assert "inside the materialised subject tree" in output, (
        "the refusal must say why the path is a problem, not merely that it "
        "is one: " + output
    )


def test_run_refuses_a_symlink_outside_the_repository_pointing_into_it(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """The same attack wearing a path that passes a naive containment check.

    The link lives outside the tree, so any check on the *name* says the binary
    is external. Only resolving it first says otherwise, which is why the
    resolution has to happen before containment is decided rather than after.
    """

    marker = tmp_path / "ran-through-the-link"
    (repo / "sh").write_text(
        f'#!/bin/sh\ntouch "{marker}"\nexit 0\n', encoding="utf-8"
    )
    (repo / "sh").chmod(0o755)
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "shadow"], check=True
    )

    outside = tmp_path / "bin"
    outside.mkdir()
    link = outside / "sh"
    link.symlink_to(repo / "sh")
    assert not link.is_relative_to(repo), (
        "the link must sit outside the repository, or this test proves nothing"
    )

    code = run_cmd(repo, keys, str(link), "check.sh")

    assert code == EXIT_USAGE, (
        "a symlink outside the repository resolving to a binary inside it was "
        "accepted; containment was judged on the name, not on the target"
    )
    assert not marker.exists(), "refused only AFTER running the planted binary"
    assert not (repo / "evidence.json").exists()


def test_an_executable_outside_the_repository_is_still_allowed(
    repo: Path,
    keys: dict[str, str],
) -> None:
    """The control. Without it the two refusals above would pass on a `run` that
    refuses everything, which is not a governed loop but a broken one."""

    assert run_cmd(repo, keys, *BOUND) == EXIT_PASS
    (record,) = records(repo)
    assert record["exit_code"] == 0


# --- and a name that resolves to nothing is refused, clearly ----------------


def test_run_refuses_an_argv0_that_resolves_to_nothing(
    repo: Path,
    keys: dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A command that never ran must not be reported as a command with an exit
    code, and the operator must be told which half failed: resolution, not
    execution."""

    capsys.readouterr()
    code = run_cmd(repo, keys, "definitely-not-a-real-binary", "--now")
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_USAGE
    assert not (repo / "evidence.json").exists()
    assert "definitely-not-a-real-binary" in output, output
    assert "resolve" in output.lower(), (
        "the refusal must name resolution as the failure; 'cannot run' after the "
        "fact does not tell an operator whether the binary was missing or the "
        "run itself failed: " + output
    )
