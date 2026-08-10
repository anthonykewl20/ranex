"""Defects found by independent review after SLICE-001 closed.

Each was confirmed by execution before this file was written. They share one
shape: `run` reporting a subject digest for a tree it did not actually observe,
which is the exact false claim the project exists to prevent.

A separate file from the SLICE-001 target so that target stays frozen and
red-then-green remains checkable for both.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from conftest import Signing, attach, signing_for

from ranex.cli.main import main, uncommitted_paths
from ranex.foundation.canonical import canonical_sha256


@pytest.fixture()
def repo(tmp_path: Path, signing: Signing) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("original\n", encoding="utf-8")
    (repository / "victim.txt").write_text("delete me\n", encoding="utf-8")
    # SLICE-003: claim entries are mappings naming the argv that satisfies them.
    # `c` is a placeholder claim; this file never asserts a PASS, it asserts what
    # `run` refuses to record.
    (repository / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: c\n"
        '        command: ["sh", "-c", "exit 0"]\n',
        encoding="utf-8",
    )
    signing.write_keyring(repository)
    attach(repository, signing)
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "initial"], check=True
    )
    # A second ref whose tree genuinely differs from HEAD.
    subprocess.run(["git", "-C", str(repository), "branch", "other"], check=True)
    (repository / "file.txt").write_text("changed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repository), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "commit", "-q", "-m", "second"], check=True
    )
    return repository


def head_subject(repo: Path) -> str:
    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


def invoke(repo: Path, argv: list[str], producer: str = "w") -> int:
    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(repo)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: repo.resolve()
        )
        monkeypatch.setenv(
            "RANEX_SIGNING_KEY", str(signing_for(repo).key_path(producer))
        )
        return main(argv)


BASE = ["run", "--claim", "c", "--producer", "w", "--repository", ".",
        "--evidence", "evidence.json", "--producers", "producers.yaml"]


# --- the subject must be the tree that was actually observed ---------------


def test_evidence_always_binds_to_head(repo: Path) -> None:
    """`other` has a different tree, but the command runs against HEAD."""

    assert invoke(repo, [*BASE, "--", "sh", "-c", "exit 0"]) == 0

    (record,) = json.loads((repo / "evidence.json").read_text(encoding="utf-8"))
    assert record["subject_digest"] == head_subject(repo)


def test_no_flag_can_point_the_subject_at_another_ref(repo: Path) -> None:
    """A caller must not be able to name a ref the command did not run against.

    `run` previously accepted `--ref`, which recorded that ref's digest while
    executing against the checked-out tree — a false claim reachable from the
    documented interface.
    """

    with pytest.raises(SystemExit) as exit_info:
        invoke(repo, [*BASE, "--ref", "other", "--", "sh", "-c", "exit 0"])

    assert exit_info.value.code == 2, "an unrecognised option must not be accepted"
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"


# --- the exemption must not become a blind spot ---------------------------


def test_rename_into_the_evidence_path_is_still_dirty(repo: Path) -> None:
    """Exempting the evidence path must not hide the source of a rename.

    `git mv victim.txt evidence.json` reports one porcelain entry whose new path
    is exempt. Dropping the whole entry hid that victim.txt was deleted.
    """

    subprocess.run(
        ["git", "-C", str(repo), "mv", "victim.txt", "evidence.json"], check=True
    )

    dirty = uncommitted_paths(repo.resolve(), ignoring=(repo / "evidence.json").resolve())
    assert dirty, "a rename into the exempt path still deletes its source"
    assert any("victim" in path for path in dirty)


def test_run_refuses_a_rename_into_the_evidence_path(repo: Path) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "mv", "victim.txt", "evidence.json"], check=True
    )

    assert invoke(repo, [*BASE, "--", "sh", "-c", "exit 0"]) == 2


def test_plain_untracked_evidence_file_is_still_exempt(repo: Path) -> None:
    """The fix must not break the exemption the second `run` depends on."""

    assert invoke(repo, [*BASE, "--", "sh", "-c", "exit 0"]) == 0
    assert invoke(repo, [*BASE, "--", "sh", "-c", "exit 0"]) == 0


# --- the command must not move the ground under the subject ---------------


def test_refuses_when_the_command_moves_head(repo: Path) -> None:
    """Removing `--ref` shut one door; the command could still walk through
    another. A wrapped command that checks out a different branch was recorded
    against the pre-checkout digest while executing somewhere else entirely.

    A command creating files is legitimate and must still pass. A command
    moving HEAD is never legitimate for an observation.
    """

    # Absolute -C keeps this aimed at the governed repo now that cwd is the sample.
    assert invoke(
        repo,
        [
            *BASE,
            "--",
            "sh",
            "-c",
            'git -C "$1" checkout -q other',
            "sh",
            str(repo),
        ],
    ) == 2
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"


def test_a_command_that_creates_files_is_still_fine(repo: Path) -> None:
    """Guard against over-correcting: side effects are expected, not suspect."""

    assert invoke(repo, [*BASE, "--", "sh", "-c", "echo x > artifact.txt"]) == 0
    assert (repo / "evidence.json").exists()


# --- malformed evidence must fail loudly, never silently ------------------


@pytest.mark.parametrize(
    "content", ["{}", '{"claim_id": "x"}', "[1, 2]", '"a string"', "null"]
)
def test_wrong_shaped_evidence_is_refused_not_silently_emptied(
    repo: Path, content: str
) -> None:
    """`{}` previously returned no evidence at all, quietly. Absence must be
    caused by nothing having been recorded, never by a parser shrugging."""

    (repo / "evidence.json").write_text(content, encoding="utf-8")

    assert invoke(
        repo,
        ["gate", "evaluate", "HEAD", "--repository", ".", "--gate-catalog",
         "gates.yaml", "--evidence", "evidence.json", "--approver", "someone"],
    ) == 2


# --- an unrunnable command is a usage error, not a traceback --------------


def test_nonexistent_command_is_a_clean_usage_error(repo: Path) -> None:
    assert invoke(repo, [*BASE, "--", "definitely-not-a-real-binary"]) == 2
    assert not (repo / "evidence.json").exists()
