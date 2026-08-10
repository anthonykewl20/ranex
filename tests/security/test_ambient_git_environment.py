"""GIT_* in Ranex's ambient environment must not choose its subject repository.

Git accepts environment variables such as GIT_DIR and GIT_WORK_TREE before it
interprets ``-C``.  Consequently, a worker could make Ranex's own binding
queries describe a repository it controls, then place that genuine evidence in
the governed repository.  This module keeps the relative-GIT_DIR reproduction:
an absolute spelling happens to trip an unrelated containment check and is not
a control.

Imports of ``ranex`` are deferred into test bodies so this regression test can
be collected before the implementation that closes it exists.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

EXIT_PASS = 0
EXIT_FAIL = 1


def command_catalog() -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: tests-executed\n"
        f"        command: {json.dumps(['sh', 'run-tests.sh'])}\n"
    )


def make_repository(path: Path, public_key: str, check_body: str) -> Path:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(["git", "-C", str(path), "config", key, value], check=True)
    (path / "producers.yaml").write_text(
        f"producers:\n  worker: {public_key}\n", encoding="utf-8"
    )
    (path / "gates.yaml").write_text(command_catalog(), encoding="utf-8")
    check = path / "run-tests.sh"
    check.write_text(f"#!/bin/sh\n{check_body}\n", encoding="utf-8")
    check.chmod(0o755)
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "initial"], check=True)
    return path


def invoke(
    repository: Path, argv: list[str], key_path: str | None = None
) -> int:
    from ranex.cli.main import main

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repository)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repository.resolve()
        )
        if key_path is None:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        else:
            monkeypatch.setenv("RANEX_SIGNING_KEY", key_path)
        try:
            return main(argv)
        except SystemExit as exit_info:
            return int(exit_info.code or 0)


def run(repository: Path, key_path: str) -> int:
    return invoke(
        repository,
        [
            "run", "--claim", "tests-executed", "--producer", "worker",
            "--repository", ".", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--", "sh", "run-tests.sh",
        ],
        key_path,
    )


def evaluate(repository: Path) -> int:
    return invoke(
        repository,
        [
            "gate", "evaluate", "HEAD", "--repository", ".",
            "--gate-catalog", "gates.yaml", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--approver", "reviewer",
        ],
    )


@pytest.fixture()
def signing_key(tmp_path: Path) -> tuple[str, str]:
    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    key_path = tmp_path / "worker.key"
    key_path.write_text(private + "\n", encoding="utf-8")
    key_path.chmod(0o600)
    return str(key_path), public


def test_relative_git_dir_cannot_make_shadow_evidence_pass(
    tmp_path: Path, signing_key: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A relative GIT_DIR must not redirect Ranex's own git queries."""
    key_path, public = signing_key
    honest = make_repository(tmp_path / "governed", public, "exit 1")
    shadow = make_repository(tmp_path / "shadow", public, "exit 0")

    assert run(shadow, key_path) == EXIT_PASS, (
        "the shadow run must succeed honestly, or this reproduction proves nothing"
    )
    shutil.copy(shadow / "evidence.json", honest / "evidence.json")

    with monkeypatch.context() as environment:
        environment.chdir(honest)
        environment.delenv("GIT_DIR", raising=False)
        honest_verdict = evaluate(honest)
    assert honest_verdict == EXIT_FAIL, (
        "control: without GIT_DIR, evidence from the shadow must fail against "
        "the governed repository whose committed check exits 1"
    )

    with monkeypatch.context() as environment:
        environment.chdir(honest)
        environment.setenv("GIT_DIR", "../shadow/.git")
        poisoned_verdict = evaluate(honest)
    # The same verdict as the control, not merely "not a PASS". GIT_DIR must
    # make no difference at all: an assertion of `!= EXIT_PASS` is also
    # satisfied by a crash, and a refusal Ranex reaches by falling over is a
    # different defect wearing this one's clothes.
    assert poisoned_verdict == honest_verdict, (
        "GIT_DIR changed the verdict: it redirected Ranex's binding queries to "
        "the shadow repository, so that repository's genuine evidence decided "
        "the governed repository's gate"
    )


def test_honest_run_and_evaluation_still_pass_without_git_environment(
    tmp_path: Path, signing_key: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanitising GIT_* must not prevent an ordinary honest PASS."""
    key_path, public = signing_key
    repository = make_repository(tmp_path / "governed", public, "exit 0")

    with monkeypatch.context() as environment:
        environment.chdir(repository)
        environment.delenv("GIT_DIR", raising=False)
        assert run(repository, key_path) == EXIT_PASS, (
            "control: an honest check must still record successfully with GIT_* absent"
        )
        assert evaluate(repository) == EXIT_PASS, (
            "control: an honest record must still satisfy its matching gate"
        )


def test_git_strips_ambient_git_variables_but_honours_explicit_overrides(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The wrapper supplies only caller-deliberate GIT_* settings to git."""
    from ranex.cli.main import git

    observed: list[dict[str, str]] = []

    def capture(*args: object, **kwargs: object) -> subprocess.CompletedProcess:
        observed.append(kwargs["env"])  # type: ignore[arg-type,index]
        return subprocess.CompletedProcess(args[0], 0, "", "")  # type: ignore[index]

    with monkeypatch.context() as environment:
        environment.setenv("GIT_DIR", "attacker/.git")
        environment.setenv("GIT_CONFIG_COUNT", "1")
        environment.setattr("ranex.cli.main.subprocess.run", capture)
        git(tmp_path, "status")
        git(tmp_path, "status", overrides={"GIT_INDEX_FILE": "/scratch/index"})

    assert "GIT_DIR" not in observed[0] and "GIT_CONFIG_COUNT" not in observed[0], (
        "ambient GIT_* variables must not reach Ranex's git child process"
    )
    assert observed[1]["GIT_INDEX_FILE"] == "/scratch/index", (
        "a caller's deliberate scratch-index override must still reach git"
    )
