"""SLICE-004 — the six false-PASS paths SLICE-003 froze, closed.

Each test here was a strict xfail in `test_slice003_audit_defects.py`. None of
them could simply have the marker removed: every one asserts a PASS is
*reachable* before asserting it must not be, so under the fix each refuses at
its own setup assertion. That is a red-to-green transition that leaves a green
suite proving nothing, which is the failure this repository has shipped twice.

So each is rewritten to assert the property **positively**: the honest red suite
is reported red, the substitution is refused with the object id named, the
shadowed binary never runs. A negative — "not a PASS" — is satisfied by a `run`
that refuses everything, so every reproduction keeps a control beside it that
must still PASS.

D1  shadowed binary on PATH   — argv[0] resolves on the pinned toolchain
D11 inherited environment     — the child's environment is built from empty
D12 ignored file              — nothing untracked is materialised
D14 configured clean filter   — the materialisation carries committed bytes
D15 poisoned loose object     — blob bytes checked against the tree's object id
D17 the oracle itself         — Ranex's own `git` comes from the pinned toolchain

Imports of `ranex` are deferred into fixtures and test bodies: a module-level
import of a symbol a fix has not created yet is a collection error, and a
collection error takes the whole suite down with it.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import zlib
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from ranex.foundation.canonical import command_digest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

# Absolute, so `argv[0]` needs no PATH lookup and these tests stay about the
# defect they name rather than about resolution.
INTERPRETER = str(Path(sys.executable).resolve())
BOUND_SUITE = [INTERPRETER, "-m", "unittest", "discover", "-s", "tests"]


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


def script(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return path


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
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "producers.yaml").write_text(
        f"producers:\n  worker: {keys['public']}\n", encoding="utf-8"
    )
    return repository


def commit_all(repo: Path, message: str = "initial") -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


def invoke(
    repo: Path,
    argv: list[str],
    key_path: str | None = None,
    *,
    path_prefix: Path | None = None,
    environment: dict[str, str] | None = None,
) -> int:
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
        if path_prefix is not None:
            monkeypatch.setenv(
                "PATH", f"{path_prefix}{os.pathsep}{os.environ['PATH']}"
            )
        for name, value in (environment or {}).items():
            monkeypatch.setenv(name, value)
        try:
            return main(argv)
        except SystemExit as exit_info:
            return int(exit_info.code or 0)


def run_cmd(
    repo: Path,
    keys: dict[str, str],
    *command: str,
    claim: str = "tests-executed",
    path_prefix: Path | None = None,
    environment: dict[str, str] | None = None,
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
        keys["path"],
        path_prefix=path_prefix,
        environment=environment,
    )


def evaluate(repo: Path, *, path_prefix: Path | None = None) -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--approver", "reviewer",
        ],
        path_prefix=path_prefix,
    )


def records(repo: Path) -> list[dict]:
    return json.loads((repo / "evidence.json").read_text(encoding="utf-8"))


def object_id(repo: Path, revision: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", revision],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def suite_manifest() -> dict[str, object]:
    return {
        "suite": ["tests/test_sample.py::test_one"],
        "expected_skips": {},
    }


def safe_junitxml() -> bytes:
    return (
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<testsuites><testsuite><testcase '
        b'classname="tests.test_sample" name="test_one" />'
        b'</testsuite></testsuites>'
    )


def hermetic_materialisation(tmp_path: Path) -> SimpleNamespace:
    root = tmp_path / "materialisation"
    tree = root / "tree"
    home = root / "home"
    temporary = root / "tmp"
    for path in (tree, home, temporary):
        path.mkdir(parents=True, exist_ok=True)
    return SimpleNamespace(
        root=root,
        tree=tree,
        home=home,
        temporary=temporary,
        tracked_paths=(),
    )


@pytest.fixture()
def repo_failing_its_own_check(repo: Path) -> Path:
    """A committed repository whose own committed check exits 1."""

    script(repo / "run-tests.sh", "test -f allow.txt")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    return repo


# --- the honest path, first. Everything below is a refusal, and a refusal is
# --- only meaningful while the loop it guards still works. ------------------


def test_a_self_contained_command_runs_records_and_passes(
    repo: Path, keys: dict[str, str]
) -> None:
    """The control the whole slice rests on: the governed loop still closes."""

    script(repo / "run-tests.sh", "exit 0")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_PASS
    (record,) = records(repo)
    assert record["exit_code"] == 0
    assert record["command_digest"] == command_digest(["sh", "run-tests.sh"])
    assert evaluate(repo) == EXIT_PASS


def test_suite_results_refuses_utf16_dtd_before_xml_parsing() -> None:
    from ranex.foundation.suite_results import suite_results_from_junitxml

    payload = (
        '<?xml version="1.0" encoding="utf-16"?>'
        '<!DOCTYPE testsuites [<!ENTITY expanded "unsafe">]>'
        '<testsuites><testsuite><testcase '
        'classname="tests.test_sample" name="test_one">'
        '<failure>&expanded;</failure></testcase></testsuite></testsuites>'
    ).encode("utf-16")

    with pytest.raises(ValueError, match="UTF-8"):
        suite_results_from_junitxml(payload, suite_manifest())


def test_results_artifact_refuses_a_symlink(tmp_path: Path) -> None:
    from ranex.foundation.suite_results import parse_results_artifact

    target = tmp_path / "target.xml"
    target.write_bytes(safe_junitxml())
    link = tmp_path / "report.xml"
    link.symlink_to(target)

    with pytest.raises(ValueError, match="open results artifact|symlink"):
        parse_results_artifact(link, suite_manifest())


def test_results_artifact_refuses_a_special_file(tmp_path: Path) -> None:
    from ranex.foundation.suite_results import parse_results_artifact

    with pytest.raises(ValueError, match="regular file"):
        parse_results_artifact(tmp_path, suite_manifest())


def test_results_artifact_reads_at_most_limit_plus_one_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ranex.foundation import suite_results

    artifact = tmp_path / "oversized.xml"
    with artifact.open("wb") as handle:
        handle.truncate(suite_results.MAX_RESULTS_BYTES + 100)

    real_read = suite_results.os.read
    bytes_read = 0

    def measured_read(descriptor: int, count: int) -> bytes:
        nonlocal bytes_read
        chunk = real_read(descriptor, count)
        bytes_read += len(chunk)
        return chunk

    monkeypatch.setattr(suite_results.os, "read", measured_read)
    with pytest.raises(ValueError, match="50 MB"):
        suite_results.parse_results_artifact(artifact, suite_manifest())

    assert bytes_read == suite_results.MAX_RESULTS_BYTES + 1


def test_hermetic_execution_refuses_a_non_regular_executable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ranex.cli import main as cli

    materialisation = hermetic_materialisation(tmp_path)
    executable = tmp_path / "executable-directory"
    executable.mkdir()
    resolution = SimpleNamespace(executable=executable)
    monkeypatch.setattr(
        cli,
        "materialise_subject",
        lambda *_args: nullcontext(materialisation),
    )
    monkeypatch.setattr(cli, "refuse_resolution_inside", lambda *_args: None)

    with pytest.raises(ValueError, match="not a regular file"):
        cli._execute_hermetically(
            tmp_path / "repo",
            "a" * 40,
            [str(executable)],
            None,
            (),
            resolution,
            False,
        )


def test_hermetic_execution_refuses_when_opened_path_differs_from_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ranex.cli import main as cli

    materialisation = hermetic_materialisation(tmp_path)
    executable = tmp_path / "resolved-tool"
    executable.write_text("tool\n", encoding="utf-8")
    opened = tmp_path / "substituted-tool"
    resolution = SimpleNamespace(executable=executable)
    monkeypatch.setattr(
        cli,
        "materialise_subject",
        lambda *_args: nullcontext(materialisation),
    )
    monkeypatch.setattr(cli, "refuse_resolution_inside", lambda *_args: None)
    monkeypatch.setattr(cli, "path_behind", lambda *_args: opened)

    with pytest.raises(ValueError, match="file actually opened is .*substituted-tool"):
        cli._execute_hermetically(
            tmp_path / "repo",
            "a" * 40,
            [str(executable)],
            None,
            (),
            resolution,
            False,
        )


def test_hermetic_execution_refuses_an_artifact_reader_without_a_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ranex.cli import main as cli

    materialisation = hermetic_materialisation(tmp_path)
    executable = tmp_path / "tool"
    executable.write_text("tool\n", encoding="utf-8")
    resolution = SimpleNamespace(executable=executable)
    monkeypatch.setattr(
        cli,
        "materialise_subject",
        lambda *_args: nullcontext(materialisation),
    )
    monkeypatch.setattr(cli, "refuse_resolution_inside", lambda *_args: None)
    monkeypatch.setattr(cli, "path_behind", lambda *_args: executable)
    monkeypatch.setattr(cli, "same_file_inside", lambda *_args: None)
    monkeypatch.setattr(cli, "stat_fingerprint", lambda *_args: {})
    monkeypatch.setattr(
        cli.subprocess,
        "run",
        lambda command, **_kwargs: subprocess.CompletedProcess(command, 0),
    )

    with pytest.raises(ValueError, match="artifact reader has no confined artifact path"):
        cli._execute_hermetically(
            tmp_path / "repo",
            "a" * 40,
            [str(executable)],
            None,
            (),
            resolution,
            False,
            artifact_reader=lambda _path: b"results",
        )


def test_the_observed_tree_carries_a_fresh_synthetic_git_directory(
    repo: Path, keys: dict[str, str]
) -> None:
    """The materialisation has a fresh repository carrying only the subject.

    `.git` is where `config` lives, and `config` is where `filter.<name>.clean`
    lives. D14 remains closed because this config is freshly created: no filter
    from the governed repository reaches it, and no clean filter is present.
    """

    script(
        repo / "run-tests.sh",
        "test -d .git && test \"$(git rev-list --count HEAD)\" = 1 && "
        "test -z \"$(git remote)\" && ! git config --get-regexp '^filter\\.'",
    )
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    subprocess.run(
        ["git", "-C", str(repo), "config", "filter.governed.clean", "cat"],
        check=True,
    )

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_PASS, (
        "the observation did not construct a fresh synthetic repository with "
        "the governed repository's configuration excluded"
    )


def test_system_git_configuration_is_absent_from_the_observed_tree(
    repo: Path, keys: dict[str, str], tmp_path: Path
) -> None:
    """A machine-level clean/smudge filter cannot enter the observation.

    The child environment is built from empty, so the ambient selector is not
    inherited. Export it in the committed check as well to make Git consult the
    hostile file just as it consults ``/etc/gitconfig`` on a configured runner,
    without changing the host running this test.
    """

    hostile_system_config = tmp_path / "hostile-system.gitconfig"
    hostile_system_config.write_text(
        "[filter \"hostile\"]\n"
        "\tclean = cat\n"
        "\tsmudge = cat\n",
        encoding="utf-8",
    )
    script(
        repo / "run-tests.sh",
        f"export GIT_CONFIG_SYSTEM={shlex.quote(str(hostile_system_config))}\n"
        "! git config --get-regexp '^filter\\.' && "
        "test \"$GIT_CONFIG_NOSYSTEM\" = 1 && "
        "test \"$GIT_ATTR_NOSYSTEM\" = 1",
    )
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(
        repo,
        keys,
        "sh",
        "run-tests.sh",
        environment={"GIT_CONFIG_SYSTEM": str(hostile_system_config)},
    ) == EXIT_PASS, "system Git configuration reached the governed observation"


def test_the_command_does_not_run_in_the_governed_worktree(
    repo: Path, keys: dict[str, str]
) -> None:
    """A file the tree does not carry must not be beside the command.

    Written as an untracked *empty directory* on purpose: git has no
    representation for one, so it is invisible to `git status` at every `-u`
    level and to `--ignored` as well. If the command can see it, the command is
    running in the worktree.
    """

    script(repo / "run-tests.sh", "test ! -d scratch")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    (repo / "scratch").mkdir()

    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "-uall", "--ignored"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "scratch" not in status, (
        f"git must be blind to the directory, or this test is weaker: {status!r}"
    )

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_PASS, (
        "the observed command saw a directory no commit carries; it is running "
        "in the worktree the observed party owns"
    )


# --- D12: an ignored file decided the bound command's outcome ---------------


def test_the_honest_run_of_a_tree_that_fails_its_own_check_reports_failure(
    repo_failing_its_own_check: Path, keys: dict[str, str]
) -> None:
    """The control for D12. Without it the reproduction passes on any refusal."""

    repo = repo_failing_its_own_check
    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_FAIL
    (record,) = records(repo)
    assert record["exit_code"] == 1
    assert evaluate(repo) == EXIT_FAIL


def test_an_ignored_file_cannot_decide_the_outcome_of_the_bound_command(
    repo_failing_its_own_check: Path, keys: dict[str, str]
) -> None:
    """D12 — the file is in no commit, so it is in no observation.

    The concealment is `.git/info/exclude` rather than a committed `.gitignore`:
    it leaves no reviewable artifact at all — not in the tree, not in any commit,
    not in the subject digest, and absent from every clone.

    Previously a strict xfail asserting a PASS was obtained. It now asserts the
    committed check is observed failing, which is the property that was wanted.
    """

    repo = repo_failing_its_own_check
    exclude = repo / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text("allow.txt\n", encoding="utf-8")
    (repo / "allow.txt").write_text("yes\n", encoding="utf-8")

    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "allow.txt" not in status, (
        f"the file must be invisible to git status, or this is another test: {status!r}"
    )

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_FAIL, (
        "an ignored file decided the bound command's outcome; the command ran "
        "against HEAD plus everything git was told not to mention"
    )
    (record,) = records(repo)
    assert record["exit_code"] == 1
    assert evaluate(repo) == EXIT_FAIL, (
        "a PASS was bound to the digest of a tree whose own committed check fails"
    )


# --- D14: a configured clean filter hid an edit to a tracked file -----------


def test_editing_a_tracked_file_is_still_refused_as_a_dirty_tree(
    repo: Path, keys: dict[str, str]
) -> None:
    """The control for D14, and the operator-facing half of the guarantee.

    Materialising means an uncommitted edit can no longer change what is
    observed. It must still be *reported*, or an operator who edits a check and
    forgets to commit silently scores the committed version instead.
    """

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    script(repo / "run-tests.sh", "exit 0")

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_USAGE
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"


def test_a_configured_clean_filter_cannot_hide_a_modified_tracked_file(
    repo: Path, keys: dict[str, str]
) -> None:
    """D14 — git was asked whether the tree was clean and chose its own answer.

    `filter.hide.clean` pointed at `git cat-file blob HEAD:%f` makes every
    tracked file hash to exactly what HEAD carries however it was edited, so
    `git status` reports clean while the committed check on disk has been
    rewritten to pass. No git flag ignores repository-local configuration, so
    there is no better question to ask git.

    The fix is to stop asking. The observation is built from the committed
    bytes, so the edit never reaches it and the check is observed failing.
    """

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    script(repo / "run-tests.sh", "exit 0")

    (repo / ".git" / "info" / "attributes").write_text(
        "* filter=hide\n", encoding="utf-8"
    )
    subprocess.run(
        ["git", "-C", str(repo), "config",
         "filter.hide.clean", "git cat-file blob HEAD:%f"],
        check=True,
    )

    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "run-tests.sh" not in status, (
        f"the filter must hide the edit, or this is another test: {status!r}"
    )

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_FAIL, (
        "the on-disk edit decided the observation while git reported the tree "
        "clean; the committed bytes are what must have been observed"
    )
    (record,) = records(repo)
    assert record["exit_code"] == 1
    assert evaluate(repo) == EXIT_FAIL


# --- D15: a loose object overwritten in place ------------------------------


def poison_loose_object(repo: Path, blob: str, replacement: bytes) -> None:
    """Overwrite `blob`'s loose object so it no longer hashes to its own name.

    Loose objects are created read-only, which is a speed bump and not a
    control: the owner chmods them.
    """

    loose = repo / ".git" / "objects" / blob[:2] / blob[2:]
    loose.chmod(0o644)
    loose.write_bytes(
        zlib.compress(b"blob %d\0" % len(replacement) + replacement)
    )


def test_an_honest_catalog_is_read_and_evaluated(
    repo: Path, keys: dict[str, str]
) -> None:
    """The control for D15: verification must not refuse an untampered store."""

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_FAIL
    assert evaluate(repo) == EXIT_FAIL, "an honest store must reach a verdict"


def test_a_poisoned_loose_object_cannot_substitute_the_gate_catalog(
    repo: Path, keys: dict[str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    """D15 — the trust root substituted underneath the flag that closed D13.

    `--no-replace-objects` removes one lookup indirection; it does not make git
    authenticate the bytes it streams. Confirmed locally: after the overwrite,
    `cat-file blob` serves the substitute while `ls-tree` still reports the
    honest object id. Comparing the two is the whole fix.

    The commit is untouched, so `HEAD` and its tree stay honest — git verifies
    commits and trees when it parses them, and blobs never.

    Asserted as a refusal, not as a FAIL: nothing was evaluated here, and
    EXIT_FAIL means the gate was judged unsatisfied.
    """

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_FAIL

    attacker = build_gates("tests-executed", ["true"]).encode("utf-8")
    blob = object_id(repo, "HEAD:gates.yaml")
    poison_loose_object(repo, blob, attacker)
    (repo / "gates.yaml").write_bytes(attacker)

    served = subprocess.run(
        ["git", "-C", str(repo), "--no-replace-objects",
         "cat-file", "blob", "HEAD:gates.yaml"],
        capture_output=True, check=True,
    ).stdout
    assert served == attacker, (
        "git must serve the substituted bytes, or this is another test"
    )

    capsys.readouterr()
    code = evaluate(repo)
    output = capsys.readouterr()

    assert code == EXIT_USAGE, (
        f"a gate catalog no commit carries was read and exited {code}; git "
        "streamed a loose object without checking it hashes to its own name"
    )
    assert blob in (output.out + output.err), (
        "the refusal must name the object id it expected, or an operator cannot "
        f"tell a poisoned store from a bug in the reader: {output.err!r}"
    )


def test_a_poisoned_loose_object_cannot_substitute_the_keyring(
    repo: Path, keys: dict[str, str]
) -> None:
    """D15, second input — the other half of the trust root.

    The keyring decides whose signature counts. Verification that covers only
    the file a test happened to name is not verification.
    """

    from ranex.foundation.signing import generate_keypair

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    _, mallory_public = generate_keypair()
    attacker = (
        f"producers:\n  worker: {keys['public']}\n  mallory: {mallory_public}\n"
    ).encode()
    poison_loose_object(repo, object_id(repo, "HEAD:producers.yaml"), attacker)
    (repo / "producers.yaml").write_bytes(attacker)

    assert evaluate(repo) == EXIT_USAGE, (
        "a keyring no commit carries was admitted; a producer nobody reviewed "
        "could sign the evidence that decides this verdict"
    )


def test_a_poisoned_blob_cannot_reach_the_observed_command(
    repo_failing_its_own_check: Path, keys: dict[str, str]
) -> None:
    """D15, third input — the materialisation itself is built from blobs.

    Verifying the trust root and then materialising the tree unverified would
    move the substitution one step sideways: the check the command runs is a
    blob like any other.
    """

    repo = repo_failing_its_own_check
    poison_loose_object(
        repo, object_id(repo, "HEAD:run-tests.sh"), b"#!/bin/sh\nexit 0\n"
    )

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_USAGE, (
        "a substituted blob was written into the observation and decided the "
        "outcome of the bound command"
    )
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"


def test_remove_materialisation_removes_an_unsearchable_directory(tmp_path: Path) -> None:
    """The real cleanup control removes directories the bound command closed."""

    from ranex.cli import subject

    root = tmp_path / "materialisation"
    blocked = root / "sub"
    blocked.mkdir(parents=True)
    (blocked / "f").write_text("x", encoding="utf-8")
    blocked.chmod(0)

    try:
        subject._remove_materialisation(root)
    finally:
        # Keep the test's mutation run from leaking the intentionally blocked
        # directory when the broken implementation raises before removing it.
        if root.exists():
            blocked.chmod(stat.S_IRWXU)
            shutil.rmtree(root)

    assert not root.exists()


def test_a_cleanup_failure_does_not_replace_the_refusal_that_caused_it(
    repo_failing_its_own_check: Path,
    keys: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    request: pytest.FixtureRequest,
) -> None:
    """The refusal an operator acts on must be the one that fired.

    Removing the materialisation happens in a `finally`, so an exception raised
    there *replaces* the one already propagating and the original survives only
    as `__context__`. An operator handed "cannot remove materialisation" for
    what was actually a substituted blob will go looking at their disk instead
    of at their object store.

    This is the same defect class this repository has now fixed four times:
    a refusal reported under another refusal's wording. D6 was a command
    mismatch printed as absence; D18 was a malformed catalog printed as a
    failing gate. Cleanup is noise; the substitution is the finding.
    """

    from ranex.cli import subject

    repo = repo_failing_its_own_check
    poison_loose_object(
        repo, object_id(repo, "HEAD:run-tests.sh"), b"#!/bin/sh\nexit 0\n"
    )

    # Record the roots so this test can remove what its unrecoverable cleanup
    # failure stopped Ranex from removing.
    abandoned: list[Path] = []
    real_rmtree = subject.shutil.rmtree

    def cleanup_explodes(root: Path | str, **kwargs: object) -> None:
        materialisation = Path(root)
        if materialisation.name.startswith("ranex-subject-"):
            abandoned.append(materialisation)
            raise TypeError("rmtree is irrecoverably unavailable")
        real_rmtree(root, **kwargs)

    monkeypatch.setattr(subject.shutil, "rmtree", cleanup_explodes)
    request.addfinalizer(
        lambda: [real_rmtree(root) for root in abandoned if root.exists()]
    )

    capsys.readouterr()
    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_USAGE
    output = capsys.readouterr()
    combined = output.out + output.err

    assert "substituted blob" in combined, (
        "the operator was told the cleanup failed and never told the object "
        f"store had been substituted: {combined!r}"
    )


# --- D17: the oracle itself was resolved on an editable PATH ---------------


def test_the_git_ranex_asks_cannot_be_chosen_by_the_observed_party(
    repo: Path, keys: dict[str, str], tmp_path: Path
) -> None:
    """D17 — one shim on PATH, and the fix that closed D13 is gone.

    Every fact the verdict rests on is obtained by spawning `git`. The shim is
    honest about everything except the one flag: it forwards every argument to
    the real git minus `--no-replace-objects`, which restores the replace-ref
    substitution entirely.

    The control is the same setup without the shim, asserted inline below, so
    this can only pass because the pinned toolchain was consulted.
    """

    real_git = str(Path(shutil.which("git")).resolve())

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_FAIL

    attacker = build_gates("tests-executed", ["true"]).encode("utf-8")
    new = subprocess.run(
        ["git", "-C", str(repo), "hash-object", "-w", "--stdin"],
        input=attacker, capture_output=True, check=True,
    ).stdout.decode().strip()
    subprocess.run(
        ["git", "-C", str(repo), "replace", object_id(repo, "HEAD:gates.yaml"), new],
        check=True,
    )
    (repo / "gates.yaml").write_bytes(attacker)

    assert evaluate(repo) == EXIT_USAGE, "the fix must hold without the shim"

    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "git").write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        f"os.execv({real_git!r}, ['git'] + "
        "[a for a in sys.argv[1:] if a != '--no-replace-objects'])\n",
        encoding="utf-8",
    )
    (shim / "git").chmod(0o755)

    assert evaluate(repo, path_prefix=shim) == EXIT_USAGE, (
        "a `git` the observed party placed on PATH answered every question the "
        "verdict rests on; deleting one argument removed the fix"
    )


def test_a_git_shim_cannot_hide_a_dirty_tree_from_ranex(
    repo: Path, keys: dict[str, str], tmp_path: Path
) -> None:
    """D17, and the test that actually binds to the pinned `git`.

    Mutation testing found the gap this closes. Removing the toolchain pin left
    the whole suite green, because the reproduction above is *also* caught by
    the blob verification: a replace ref makes `cat-file` and `ls-tree` disagree,
    and that check fires whichever `git` answered. So the shim above proved the
    verification worked and proved nothing about where `git` came from.

    This shim lies about something no digest can catch. `git status` is a
    question about the working tree, not about any object, so there is no id to
    compare its answer against — the only defence is that the observed party did
    not choose who answered. The shim reports every tree clean; under the pin it
    is never consulted and the uncommitted edit is still refused.
    """

    script(repo / "run-tests.sh", "exit 1")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)
    script(repo / "run-tests.sh", "exit 0")  # the tree is now dirty

    real_git = str(Path(shutil.which("git")).resolve())
    shim = tmp_path / "shim"
    shim.mkdir()
    (shim / "git").write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "if 'status' in sys.argv[1:]:\n"
        "    sys.exit(0)\n"  # every tree is clean, says the observed party
        f"os.execv({real_git!r}, ['git'] + sys.argv[1:])\n",
        encoding="utf-8",
    )
    (shim / "git").chmod(0o755)

    lied = subprocess.run(
        [str(shim / "git"), "-C", str(repo), "status", "--porcelain"],
        capture_output=True, text=True, check=False,
    )
    assert lied.stdout == "", (
        "the shim must actually hide the edit, or this test proves nothing: "
        f"{lied.stdout!r}"
    )

    assert run_cmd(
        repo, keys, "sh", "run-tests.sh", path_prefix=shim
    ) == EXIT_USAGE, (
        "a `git` the observed party placed on PATH was asked whether the tree "
        "was clean and said yes; the uncommitted edit went unreported"
    )
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"


# --- D11: the inherited environment rewrote the bound command ---------------


@pytest.fixture()
def repo_with_a_red_suite(repo: Path) -> Path:
    """A committed repository whose own test suite genuinely fails.

    Stdlib `unittest`, so the bound command needs nothing installed and the
    control is a real red suite rather than an import error wearing its exit
    code.
    """

    (repo / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    tests = repo / "tests"
    tests.mkdir()
    (tests / "test_truth.py").write_text(
        "import unittest\n\n\n"
        "class TheProduct(unittest.TestCase):\n"
        "    def test_it_works(self):\n"
        "        self.assertEqual(1, 2, 'the product is broken')\n",
        encoding="utf-8",
    )
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", BOUND_SUITE), encoding="utf-8"
    )
    commit_all(repo)
    return repo


def test_an_honest_run_of_the_bound_command_reports_the_red_suite(
    repo_with_a_red_suite: Path, keys: dict[str, str]
) -> None:
    """The control for D11, and load-bearing rather than decorative.

    Without it the reproduction is satisfied by any run that fails for any
    reason — an interpreter that is not there, a fixture that never committed,
    a materialisation that did not copy `tests/`.
    """

    repo = repo_with_a_red_suite
    assert run_cmd(repo, keys, *BOUND_SUITE) == EXIT_FAIL
    (record,) = records(repo)
    assert record["exit_code"] == 1, f"the suite must genuinely fail: {record}"
    assert record["command_digest"] == command_digest(BOUND_SUITE)
    assert evaluate(repo) == EXIT_FAIL


def test_the_inherited_environment_must_not_rewrite_the_bound_command(
    repo_with_a_red_suite: Path, keys: dict[str, str], tmp_path: Path
) -> None:
    """D11 — every check passed and the suite never ran.

    Nothing here is forged. The argv is the argv the catalog binds, the
    executable is a genuine interpreter at an absolute path outside the tree,
    the signature verifies and the subject digest is HEAD's. The one thing the
    observed party touched is an environment variable, and an interpreter reads
    its instructions from the environment before it reads argv: `sitecustomize`
    is imported during startup, before `-m` is looked at.

    `NODE_OPTIONS`, `RUBYOPT`, `PERL5OPT`, `JAVA_TOOL_OPTIONS` and `LD_PRELOAD`
    are the same defect in other languages, which is why the fix is not a
    denylist — nothing is inherited, so the next name needs no edit.
    """

    repo = repo_with_a_red_suite
    outside = tmp_path / "outside-the-tree"
    outside.mkdir()
    (outside / "sitecustomize.py").write_text(
        "import os\nos._exit(0)\n", encoding="utf-8"
    )

    assert run_cmd(
        repo, keys, *BOUND_SUITE, environment={"PYTHONPATH": str(outside)}
    ) == EXIT_FAIL, (
        "the bound command was recorded as succeeding while the committed suite "
        "still fails; the environment decided what the command did"
    )
    (record,) = records(repo)
    assert record["exit_code"] == 1
    assert evaluate(repo) == EXIT_FAIL


def test_no_ambient_variable_reaches_the_observed_command(
    repo: Path, keys: dict[str, str]
) -> None:
    """The positive form of D11: built from empty, not filtered.

    A denylist is refuted by one name nobody thought of. This asserts the
    property that makes the name irrelevant.
    """

    script(repo / "run-tests.sh", 'test -z "$RANEX_AMBIENT_PROBE"')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(
        repo, keys, "sh", "run-tests.sh",
        environment={"RANEX_AMBIENT_PROBE": "reached the child"},
    ) == EXIT_PASS, (
        "a variable exported beside Ranex reached the observed command; the "
        "environment is inherited and filtered rather than constructed"
    )


def test_the_signing_key_never_reaches_the_observed_command(
    repo: Path, keys: dict[str, str]
) -> None:
    """The one variable whose leak forges everything downstream."""

    script(repo / "run-tests.sh", 'test -z "$RANEX_SIGNING_KEY"')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(repo, keys, "sh", "run-tests.sh") == EXIT_PASS


# --- D1: the binary the claim names was chosen on the operator's PATH -------


def test_a_shadowed_binary_on_path_must_not_satisfy_the_claim(
    repo: Path, keys: dict[str, str], tmp_path: Path
) -> None:
    """D1 — the forgery the whole of SLICE-003 was written to close.

    `pytest` is a name looked up on a PATH the observed party owns, so the
    recorded argv is honest and the binary is not. in-toto's spec concedes
    exactly this ("can easily be forged… by changing the PATH").

    The required property is that the shadow does not execute and no PASS is
    reachable. *How* is the implementer's choice — refusing a name absent from
    the pinned toolchain, or running the pinned one — so the marker file is what
    is asserted, not the exit code.
    """

    marker = tmp_path / "shadow-ran"
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["pytest", "-q"]), encoding="utf-8"
    )
    commit_all(repo)

    shadow = tmp_path / "shadow"
    script(shadow / "pytest", f'touch "{marker}"\nexit 0')

    run_cmd(repo, keys, "pytest", "-q", path_prefix=shadow)

    assert not marker.exists(), (
        "a binary the observed party placed on PATH executed and satisfied "
        "`tests-executed`; the claim names a command and the machine decided "
        "which one"
    )
    assert evaluate(repo) != EXIT_PASS


def test_the_observed_command_is_not_handed_the_operators_path(
    repo: Path, keys: dict[str, str], tmp_path: Path
) -> None:
    """D1 and D17 meeting: the child's PATH is pinned too.

    A command that finds the operator's PATH in its own environment can put a
    shim in front of anything the *next* run resolves.
    """

    shadow = tmp_path / "shadow"
    shadow.mkdir()

    script(repo / "run-tests.sh", f'! echo "$PATH" | grep -q "{shadow}"')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(
        repo, keys, "sh", "run-tests.sh", path_prefix=shadow
    ) == EXIT_PASS, "the operator's PATH was handed to the observed command"


# --- the toolchain pin refuses a directory the observed party can edit ------


def test_a_writable_toolchain_directory_is_refused_at_construction(
    tmp_path: Path,
) -> None:
    """A pinned path the observed party can write to is not pinned.

    Sharing a uid, the worker writes a binary into any directory that uid owns
    and the operator's next invocation picks it up. That is the precondition
    D17 rests on, and it is refused here rather than documented.
    """

    from ranex.cli.toolchain import ToolchainError, pinned_directories

    writable = tmp_path / "bin"
    writable.mkdir()
    assert os.access(writable, os.W_OK), "the fixture must be writable"

    with pytest.raises(ToolchainError) as refused:
        pinned_directories((writable,))
    assert str(writable) in str(refused.value)


def test_a_world_writable_toolchain_directory_is_refused(tmp_path: Path) -> None:
    """Ownership is not the only way in."""

    from ranex.cli.toolchain import ToolchainError, pinned_directories

    directory = tmp_path / "bin"
    directory.mkdir()
    directory.chmod(0o777)
    assert stat.S_IMODE(directory.stat().st_mode) & stat.S_IWOTH

    with pytest.raises(ToolchainError):
        pinned_directories((directory,))


def test_a_writable_executable_inside_a_protected_directory_is_refused(
    tmp_path: Path,
) -> None:
    """A protected directory is not the same as a protected binary.

    Refusing a writable *directory* stops the worker creating or replacing an
    entry in it. It does nothing about an entry that is itself writable: the
    bytes of `/usr/bin/git` at mode 0777 can be overwritten in place without
    touching the directory at all, and the pin would still report the route
    clean. Found by the implementer auditing its own work, and closed here
    rather than written down as a limit.
    """

    from ranex.cli.toolchain import ToolchainError, refuse_writable_executable

    tool = tmp_path / "git"
    tool.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

    # 0555, not 0755: a system binary is owned by root and this test is not run
    # as root, so the honest case is one this uid cannot write. At 0755 the
    # fixture owns a writable file and is refused — correctly, which is why the
    # owner-writable mode is asserted as hostile below rather than as control.
    tool.chmod(0o555)
    refuse_writable_executable(tool)  # the control: an ordinary binary is fine

    for hostile in (0o777, 0o775, 0o755):
        tool.chmod(hostile)
        with pytest.raises(ToolchainError) as refused:
            refuse_writable_executable(tool)
        assert str(tool) in str(refused.value), hostile


def test_the_pinned_toolchain_resolves_git_to_an_absolute_path() -> None:
    """The control for the two refusals above: the real toolchain is usable."""

    from ranex.cli.toolchain import resolve_tool

    resolved = resolve_tool("git")
    assert resolved.is_absolute()
    assert resolved.is_file()
    assert os.access(resolved, os.X_OK)


def test_a_tool_absent_from_the_pinned_toolchain_is_refused() -> None:
    """Absence blocks here as it blocks everywhere else."""

    from ranex.cli.toolchain import ToolchainError, resolve_tool

    with pytest.raises(ToolchainError):
        resolve_tool("ranex-tool-that-does-not-exist")
