"""SLICE-003 — the seven fraudulent PASSes three audits reproduced.

Written after the implementation landed 214 green and required to fail first
anyway: a suite that is green while the slice's core promise does not hold is
the thing this project exists to prevent. Each test below is a gate PASS (or a
recorded observation) an auditor actually obtained, not a hypothetical.

They share one shape. SLICE-003 decided *what* satisfies a claim and then
decided it from values the observed party can still choose: the PATH it is
looked up on, a symlink it committed, a directory it swapped, a flag it passed,
a second record it added. The binding is only as good as the weakest input to it.

D1 PATH shadow          — argv[0] resolved on an attacker-editable PATH
D2 in-repo symlink      — containment judged on the target, not on the route
D3 check-then-spawn     — the path re-walked between the decision and the exec
D4 --journal exemption  — an arbitrary path excused from the dirty-tree check
D5 contradictory records — `any()` lets a pass outvote a failure
D6 reporting regression — a refusal printed in the wording reserved for absence
D8 hardlink bypass      — containment compares paths, and an inode has many

D1, D2 and D8 are **one defect wearing three costumes**: the observed tree gets
to choose which bytes run, through PATH, through a committed link, or through a
second name for one inode. They are kept as three tests because each is a
distinct reproduction, not because a separate fix is expected for each — one
fix, judging identity rather than location, should close all three.

Imports of `ranex` are deferred into fixtures and test bodies: a module-level
import of a symbol a fix has not created yet is a collection error, and a
collection error takes the whole suite down with it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from ranex.foundation.canonical import command_digest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

RESOLVED_SH = str(Path(shutil.which("sh")).resolve())


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
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
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
) -> int:
    """Run the CLI. Returns the exit code, including argparse's own.

    A refusal expressed by removing an option is still a refusal, and a test for
    "this flag must not be able to do that" must not depend on the flag
    continuing to exist.
    """

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
        try:
            return main(argv)
        except SystemExit as exit_info:
            return int(exit_info.code or 0)


def run_cmd(
    repo: Path,
    keys: dict[str, str],
    *command: str,
    claim: str = "tests-executed",
    extra: list[str] | None = None,
    path_prefix: Path | None = None,
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
            *(extra or []),
            "--", *command,
        ],
        keys["path"],
        path_prefix=path_prefix,
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


def head_subject(repo: Path) -> str:
    from ranex.foundation.canonical import canonical_sha256

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


# --- D1: PATH is still what decides which binary the claim names ------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Not closable inside SLICE-003 as ADR-001 specifies it. The catalog "
        "binds argv, and `pytest` is a name looked up on a PATH the observed "
        "party owns, so the recorded argv is honest and the binary is not. "
        "Two fixes exist and both are decisions this ADR did not take: require "
        "`command[0]` to be an absolute path in the catalog — which closes it "
        "completely but makes the committed trust root machine-specific — or "
        "stop inheriting the observed party's environment, which is SLSA L3 and "
        "SLICE-004's subject (ADR-001 sad path 17). Marked strict so the day "
        "either lands, this test fails loudly and the marker comes off."
    ),
)
def test_a_shadowed_binary_on_path_must_not_satisfy_the_claim(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """D1 — the forgery the whole slice was written to close, still open.

    `resolve_executable` asks one question of the resolved path: is it outside
    the repository? A fake `pytest` in any other directory answers yes. It is
    resolved, executed, recorded with the argv the catalog demands, cleared by
    the evaluate-time containment re-check, and the gate PASSes — while the real
    test suite never ran.

    in-toto's spec concedes exactly this ("can easily be forged… by changing the
    PATH"). ADR-001 claims to improve on that by "not using PATH for trust", and
    the implementation still does.
    """

    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["pytest", "-q"]), encoding="utf-8"
    )
    commit_all(repo)

    shadow = tmp_path / "shadow"
    script(shadow / "pytest", 'echo "not the tests"\nexit 0')

    assert run_cmd(repo, keys, "pytest", "-q", path_prefix=shadow) == EXIT_PASS
    (record,) = records(repo)
    assert record["command_digest"] == command_digest(["pytest", "-q"]), (
        "the record must claim the bound argv, or this test proves nothing"
    )

    assert evaluate(repo) != EXIT_PASS, (
        "a binary the observed party placed on PATH satisfied `tests-executed`; "
        "the claim names a command and the machine decided which one"
    )


# --- D2: containment is judged on the target, never on the route ------------


def test_run_refuses_a_committed_in_repo_symlink_to_an_outside_binary(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """D2 — the route matters as much as the destination.

    `tools2/pytest` is a symlink committed *inside* the tree under observation.
    It points at a binary outside, so resolving first and asking about the
    target alone says "outside, allowed". But the observed party chose the
    target by committing the link: the indirection is in the tree its own
    evidence describes, and moving the link moves what the claim means without
    touching anything the containment check looks at.

    Required: refuse when any component of the pre-resolution path lies inside
    the worktree, not only when the resolved target does.

    The same root cause as D1 and D8 — the tree choosing which outside bytes
    run. One fix is expected to close all three; this is the reproduction, not a
    separate defect.
    """

    marker = tmp_path / "outside-tool-ran"
    outside = script(tmp_path / "tools" / "pytest", f'touch "{marker}"\nexit 0')

    (repo / "tools2").mkdir()
    (repo / "tools2" / "pytest").symlink_to(outside)
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["./tools2/pytest", "-q"]), encoding="utf-8"
    )
    commit_all(repo)
    assert (repo / "tools2" / "pytest").is_symlink(), (
        "the link must be committed as a symlink, or this test proves nothing"
    )

    code = run_cmd(repo, keys, "./tools2/pytest", "-q")

    assert code == EXIT_USAGE, (
        "an executable reached through a symlink committed inside the subject "
        "worktree was accepted; containment was decided on the target and the "
        "observed party owns the route"
    )
    assert not marker.exists(), "refused only AFTER running through the link"
    assert not (repo / "evidence.json").exists()


def test_a_genuine_outside_binary_is_still_allowed(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """The control for D2. Without it the refusal above is satisfied by a `run`
    that refuses everything, which is a broken loop and not a governed one."""

    marker = tmp_path / "outside-tool-ran"
    outside = script(tmp_path / "tools" / "checker", f'touch "{marker}"\nexit 0')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", [str(outside)]), encoding="utf-8"
    )
    commit_all(repo)

    assert run_cmd(repo, keys, str(outside)) == EXIT_PASS
    assert marker.exists()
    assert evaluate(repo) == EXIT_PASS


# --- D8: one inode, two names, and containment only reads names -------------


def test_run_refuses_a_hardlink_to_a_file_inside_the_worktree(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
) -> None:
    """D8 — a hard link is the same file, and containment cannot see that.

    `ln <repo>/tools/pytest /tmp/pytest` gives the in-repo file a second name
    outside the tree. `resolve_executable` returns the outside name, so
    `committable_into` is False and both the run-time check and the
    evaluate-time re-check clear it, while the bytes that execute are the ones
    the observed party wrote into the tree its own evidence describes. Symlink
    resolution does not help: there is no link to follow, only two directory
    entries for one inode.

    The required property is identity, not location: the resolved executable
    must not be the same file as anything inside the subject worktree. How that
    is decided — `(st_dev, st_ino)` against the tracked tree, `st_nlink == 1`,
    or something better — is the implementer's choice; this test asserts only
    that the run is refused and no PASS is reachable.

    The same weakness class the SLICE-004 Landlock spike hit independently:
    Landlock rules are inode-bound, so a hard link to the signing key under any
    allowed path silently re-grants read. The two fixes will want one helper.
    """

    marker = tmp_path / "in-repo-bytes-ran"
    script(repo / "tools" / "pytest", f'touch "{marker}"\nexit 0')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["pytest", "-q"]), encoding="utf-8"
    )
    commit_all(repo)

    outside = tmp_path / "bin"
    outside.mkdir()
    os.link(repo / "tools" / "pytest", outside / "pytest")
    assert (outside / "pytest").stat().st_ino == (
        repo / "tools" / "pytest"
    ).stat().st_ino, "the link must share the inode, or this test proves nothing"

    code = run_cmd(repo, keys, "pytest", "-q", path_prefix=outside)

    assert code == EXIT_USAGE, (
        "a second name for a file inside the worktree was accepted as an "
        "outside binary; containment compared paths and an inode has many"
    )
    assert not marker.exists(), "the in-repo bytes executed"
    assert not (repo / "evidence.json").exists()
    assert evaluate(repo) != EXIT_PASS


# --- D3: the path is re-walked between the decision and the exec ------------


def test_the_file_that_runs_is_the_file_containment_cleared(
    repo: Path,
    keys: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """D3 — check-then-spawn, the same shape as the keygen check-then-open.

    `resolve_executable` returns a *name*. `subprocess.run` walks that name
    again at exec time, and every directory on it is traversed a second time.
    Replace an ancestor with a symlink into the worktree in between and the
    in-repo binary runs while the record names the outside path that was
    cleared — a containment decision about a file that never executed.

    Deterministic rather than threaded: the window is entered exactly once, at
    the pre-run `stat_fingerprint`, which runs after containment and before the
    spawn. A racing test would be flaky and would prove less. (An auditor won
    the threaded version 9/9 at 75-85ms, so the window is not theoretical.)

    Asserted as identity rather than as a mechanism: whatever `run` does, the
    file that executes must be the file that was cleared. Opening the resolved
    path once and spawning through `/proc/self/fd/N` is the obvious way to get
    there, and this test is written not to require it.
    """

    inside_marker = tmp_path / "in-repo-binary-ran"
    outside_marker = tmp_path / "cleared-binary-ran"

    # Committed inside the repository, so the tree stays clean and the only
    # thing under test is which file the exec reaches.
    script(repo / "evil" / "holder" / "tool", f'touch "{inside_marker}"\nexit 0')
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "-c", "exit 0"]), encoding="utf-8"
    )
    commit_all(repo)

    outside = tmp_path / "outside"
    target = script(outside / "holder" / "tool", f'touch "{outside_marker}"\nexit 0')

    real_fingerprint = __import__(
        "ranex.cli.main", fromlist=["stat_fingerprint"]
    ).stat_fingerprint
    swapped = False

    def swap_the_ancestor_then_fingerprint(*args, **kwargs):
        nonlocal swapped
        if not swapped:
            swapped = True
            (outside / "holder" / "tool").unlink()
            (outside / "holder").rmdir()
            outside.rmdir()
            outside.symlink_to(repo / "evil", target_is_directory=True)
        return real_fingerprint(*args, **kwargs)

    monkeypatch.setattr(
        "ranex.cli.main.stat_fingerprint", swap_the_ancestor_then_fingerprint
    )

    run_cmd(repo, keys, str(target))

    assert not inside_marker.exists(), (
        "a binary inside the repository executed through an ancestor swapped "
        "after the containment check; the file that ran is not the file that "
        "was cleared, and the record names the one that did not run"
    )
    if (repo / "evidence.json").exists():
        (record,) = records(repo)
        assert outside_marker.exists(), (
            f"a record was written naming {record['executable_path']}, which "
            "never executed"
        )


# --- D4: --journal excuses an arbitrary path from the dirty-tree check ------


def test_journal_flag_cannot_exempt_an_arbitrary_path_from_the_dirty_check(
    repo: Path,
    keys: dict[str, str],
) -> None:
    """D4 — one flag turns the dirty-working-tree refusal into a false claim.

    `run` exempts whatever `--journal` names, exactly as it once exempted
    whatever `--evidence` named — the defect
    `test_evidence_exemption_never_covers_a_tracked_file` was written to close,
    reintroduced under a second flag this session.

    The repository's own check is gated on a file HEAD does not carry. Clean, it
    fails. With the file present and named by `--journal`, the file is invisible
    to the dirty check, the check passes, and the record binds a PASS to HEAD's
    digest — a tree that fails its own check.
    """

    script(repo / "run-tests.sh", "test -f allow.txt")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    assert subprocess.run(
        ["sh", "run-tests.sh"], cwd=repo, capture_output=True
    ).returncode == 1, "the committed tree must fail its own check"

    (repo / "allow.txt").write_text("yes\n", encoding="utf-8")

    code = run_cmd(
        repo, keys, "sh", "run-tests.sh", extra=["--journal", "allow.txt"]
    )

    assert code == EXIT_USAGE, (
        "--journal exempted an arbitrary untracked file from the dirty-tree "
        "check, so a passing observation was bound to a tree that fails"
    )
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"


def test_a_staged_but_uncommitted_file_is_never_exempt(
    repo: Path,
    keys: dict[str, str],
) -> None:
    """D4, second half — `carried_by_head` is the wrong question.

    The exemption is withheld from files HEAD carries, on the reasoning that
    tracked means reviewed. A staged file is tracked and is not in HEAD, so it
    slips through: `git add` is enough to make any path exemptible, and staging
    is not review.
    """

    script(repo / "run-tests.sh", "test -f staged.txt")
    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    commit_all(repo)

    (repo / "staged.txt").write_text("yes\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "staged.txt"], check=True)

    code = run_cmd(
        repo, keys, "sh", "run-tests.sh", extra=["--journal", "staged.txt"]
    )

    assert code == EXIT_USAGE, (
        "a staged, uncommitted file was exempted from the dirty-tree check "
        "because HEAD does not carry it; `git add` is not review"
    )
    assert not (repo / "evidence.json").exists()


# --- D5: two records for one claim, disagreeing -----------------------------


def test_contradictory_records_for_one_claim_do_not_pass() -> None:
    """D5 — `any()` lets a pass outvote a failure, silently.

    Two producers observe the same claim against the same tree with the same
    bound command and disagree: one saw it fail, one saw it succeed. At least
    one of them is wrong, and nothing in the verdict says so — `any()` finds the
    zero and returns PASS, discarding a signed, admitted, honest report of
    failure.

    A contradiction is not evidence. It is the one situation where more evidence
    must make the verdict *less* certain, and a control that resolves it by
    taking the favourable half is not a control.
    """

    from ranex.governed_execution.domain.verdict import (
        Claim,
        Evidence,
        Gate,
        Verdict,
        evaluate,
    )

    subject = "sha256:" + "a" * 64
    argv = ["sh", "run-tests.sh"]
    digest = command_digest(argv)

    def record(producer: str, exit_code: int) -> Evidence:
        return Evidence(
            claim_id="tests-executed",
            subject_digest=subject,
            producer_id=producer,
            command=" ".join(argv),
            command_digest=digest,
            executable_path=RESOLVED_SH,
            exit_code=exit_code,
        )

    gate = Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(Claim(claim_id="tests-executed", command_digest=digest),),
        blocking=True,
    )
    result = evaluate(
        gate,
        (record("worker-a", 1), record("worker-b", 0)),
        subject_digest=subject,
        approver_id="reviewer",
    )

    assert result.verdict is Verdict.FAIL, (
        "a signed report of failure was outvoted by a signed report of success "
        "for the same claim, same subject and same command"
    )
    assert "tests-executed" in (
        (result.reason or "") + " ".join(result.missing_claims)
    ), (
        "the contradiction must be named; a FAIL an operator cannot attribute "
        f"is barely better than the wrong verdict: {result!r}"
    )


# --- D6: a refusal printed in the wording reserved for absence --------------


def test_a_command_mismatch_is_not_reported_as_work_never_done(
    repo: Path,
    keys: dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """D6 — the exact reporting defect SLICE-002 was reopened to fix.

    A record is present, signed, admitted, bound to this tree, and describes a
    command the claim does not name. The gate FAILs, correctly, and prints "no
    evidence for required claim" — the kernel's phrasing for honest absence.

    An operator reading that sees a task nobody got to. What happened is that
    someone ran something else and recorded it, which is the event this whole
    slice exists to surface. Absence and mismatch must never share a sentence.
    """

    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", ["sh", "run-tests.sh"]), encoding="utf-8"
    )
    script(repo / "run-tests.sh", "exit 0")
    commit_all(repo)

    assert run_cmd(repo, keys, "true") == EXIT_PASS
    (record,) = records(repo)
    assert record["command_digest"] != command_digest(["sh", "run-tests.sh"])

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert "tests-executed" in output, output
    assert "no evidence for required claim" not in output, (
        "a record describing the wrong command was reported as work never "
        "done: " + output
    )


# --- D7: the containment refusal's own reason is never asserted -------------


def signed_record(
    repo: Path,
    keys: dict[str, str],
    *,
    executable_path: str,
    argv: list[str],
) -> None:
    from ranex.foundation.signing import sign_evidence

    body = {
        "claim_id": "tests-executed",
        "command": " ".join(argv),
        "command_digest": command_digest(argv),
        "executable_path": executable_path,
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": head_subject(repo),
    }
    (repo / "evidence.json").write_text(
        json.dumps([{**body, "signature": sign_evidence(body, keys["private"])}]),
        encoding="utf-8",
    )


@pytest.mark.parametrize("relative", [False, True])
def test_containment_refusal_names_its_own_reason(
    repo: Path,
    keys: dict[str, str],
    relative: bool,
) -> None:
    """D7 — an enum value nothing asserts is an enum value nothing enforces.

    `EXECUTABLE_INSIDE_SUBJECT` exists so an operator can tell a shadowed binary
    apart from a forged signature, and until now swapping it for BAD_SIGNATURE
    kept the suite green — which means the distinction was decoration. Both
    branches that raise it are pinned here: a path inside the repository, and a
    path that is not absolute at all and therefore decides nothing.
    """

    from ranex.cli.main import admitted_evidence
    from ranex.governed_execution.domain.admission import RejectionReason

    argv = ["sh", "run-tests.sh"]
    (repo / "gates.yaml").write_text(build_gates("tests-executed", argv), encoding="utf-8")
    script(repo / "run-tests.sh", "exit 0")
    commit_all(repo)

    signed_record(
        repo,
        keys,
        executable_path="run-tests.sh" if relative else str(repo / "run-tests.sh"),
        argv=argv,
    )

    admission = admitted_evidence(
        repo / "evidence.json",
        repo / "producers.yaml",
        repository_root=repo.resolve(),
    )

    assert admission.evidence == ()
    (rejection,) = admission.rejections
    assert rejection.reason is RejectionReason.EXECUTABLE_INSIDE_SUBJECT, (
        "the containment refusal was reported under another reason, so an "
        f"operator cannot tell it from a forgery: {rejection.detail}"
    )
    assert rejection.claim_id == "tests-executed"
    assert rejection.producer_id == "worker"
