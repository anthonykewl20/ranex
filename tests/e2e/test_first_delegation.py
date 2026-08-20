"""SLICE-008 criterion 7 — a real model produces a real verdict.

One delegated run against a real provider (OpenRouter, a free model) ends in a
journalled CANDIDATE naming its missing claims, with no PASS anywhere, and the
diff is reviewable.  Skips loudly by name when the operator's credential is
absent.

The decoration warning this test exists to honour: it must prove the suite
genuinely executed and the diff is non-empty.  A delegation that passes because
nothing ran is the failure the old gear-mesh e2e made with a noop model — so
the target carries a test that is red at base and can only turn green if the
delegated model's file reaches the materialised commit, and the suite output
recorded by the kernel must show it ran.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import main, subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskCandidate

EXIT_PASS = 0
EXIT_FAIL = 1

MODEL = "openrouter/cohere/north-mini-code:free"
PROMPT = (
    "Create a file named AGENT_NOTE.txt at the repository root containing the "
    "single line: delegated work happened. Do not do anything else."
)
SUITE = f"{sys.executable} -m pytest -q -p no:cacheprovider"
HARNESS_TIMEOUT = 300
# Delegated file creation is cheap for the model but the free tier is slow;
# a transient provider failure is retried, never asserted around.
ATTEMPTS = 3

GATES = """\
gates:
  - gate_id: first-delegation
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["/usr/bin/true"]
"""

# Red at base, green only when the delegated commit carries the note: the
# suite passing is then proof the model's work reached the materialised tree.
NOTE_TEST = '''\
from pathlib import Path


def test_delegated_note_reached_the_materialised_tree() -> None:
    note = Path("AGENT_NOTE.txt")
    assert note.is_file(), "the delegated model created no AGENT_NOTE.txt"
    assert "delegated work happened" in note.read_text(encoding="utf-8")
'''


def harness_dir() -> Path:
    default = Path(__file__).resolve().parents[2].parent / "ranex-harness"
    return Path(os.environ.get("RANEX_HARNESS_DIR", default))


@pytest.fixture(scope="module")
def credential() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        pytest.skip(
            "OPENROUTER_API_KEY is absent or empty; the first-delegation e2e "
            "needs a real OpenRouter credential"
        )
    return key


@pytest.fixture(scope="module")
def harness() -> Path:
    tree = harness_dir()
    if not (tree / "package.json").is_file():
        pytest.skip(f"harness fork not present at {tree} (set RANEX_HARNESS_DIR)")
    return tree


@pytest.fixture(scope="module")
def bun() -> Path:
    executable = Path.home() / ".bun" / "bin" / "bun"
    if not executable.is_file():
        pytest.skip("bun toolchain not installed at ~/.bun/bin/bun")
    return executable


def clean_env(home: Path, credential: str | None = None) -> dict[str, str]:
    environment = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if credential is not None:
        environment["OPENROUTER_API_KEY"] = credential
    return environment


def git(repository: Path, *arguments: str, home: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        text=True,
        check=True,
        env=clean_env(home),
    )
    return result.stdout


def build_target(tmp_path: Path) -> Path:
    """A committed governed repository the delegated model will work in."""

    target = tmp_path / "target"
    target.mkdir()
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", str(target)], check=True, env=clean_env(home)
    )
    git(target, "config", "user.email", "first-delegation@example.invalid", home=home)
    git(target, "config", "user.name", "First Delegation", home=home)

    _, public = generate_keypair()
    (target / "app.txt").write_text("governed\n", encoding="utf-8")
    (target / "gates.yaml").write_text(GATES, encoding="utf-8")
    (target / "evidence.json").write_text("[]\n", encoding="utf-8")
    (target / "producers.yaml").write_text(
        f"producers:\n  worker: {public}\n", encoding="utf-8"
    )
    tests = target / "tests"
    tests.mkdir()
    (tests / "test_delegated_note.py").write_text(NOTE_TEST, encoding="utf-8")
    git(target, "add", "-A", home=home)
    git(target, "commit", "-q", "-m", "initial governed work", home=home)
    return target


def write_wrapper(path: Path, bun: Path, harness: Path) -> Path:
    """The delegate spawns [harness, --dir, ...] in a pinned-PATH environment
    where bun does not resolve; this wrapper supplies the absolute runtime and
    the `run` subcommand, exactly as `bin/ranex run` would. The kernel's
    scratch HOME carries no harness config, so the wrapper also seeds the one
    piece the delegated journey needs: the build agent denying the GitHub
    tool family, whose union-shaped parameter schemas (a top-level ``anyOf``
    without ``type``) the frozen free model's upstream rejects on every turn
    (issue #39 CCR-2's real entry; CCR-3's seeded deny)."""

    path.write_text(
        "#!/bin/sh\n"
        'mkdir -p "$HOME/.config/ranex/agent"\n'
        "cat >\"$HOME/.config/ranex/agent/build.md\" <<'CONF'\n"
        "---\n"
        "permission:\n"
        "  github_issue: deny\n"
        "  github_milestone: deny\n"
        "  github_project: deny\n"
        "---\n"
        "CONF\n"
        f'exec "{bun}" run --cwd "{harness / "packages" / "ranex"}" '
        '--conditions=browser src/index.ts run "$@"\n',
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def run_delegate(
    *,
    target: Path,
    task_id: str,
    worktree: Path,
    journal: Path,
    wrapper: Path,
    outcome: Path,
    home: Path,
    credential: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m", "ranex.cli.main",
            "task", "delegate",
            "--task-id", task_id,
            "--target", str(target),
            "--worktree", str(worktree),
            "--journal", str(journal),
            "--harness", str(wrapper),
            "--model", MODEL,
            "--prompt", PROMPT,
            "--timeout", str(HARNESS_TIMEOUT),
            "--suite", SUITE,
            "--outcome", str(outcome),
        ],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(home, credential),
        timeout=HARNESS_TIMEOUT + 120,
    )


def run_judge(
    *,
    target: Path,
    task_id: str,
    worktree: Path,
    commit: str,
    journal: Path,
    home: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m", "ranex.cli.main",
            "task", "judge",
            "--task-id", task_id,
            "--emitted-worktree", str(worktree),
            "--emitted-commit", commit,
            "--gate", "first-delegation",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--journal", str(journal),
        ],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(home),
        timeout=120,
    )


def test_kernel_merge_publishes_clean_fast_forward_end_to_end(
    tmp_path: Path,
) -> None:
    target = tmp_path / "merge-target"
    target.mkdir()
    home = tmp_path / "merge-home"
    home.mkdir()
    subprocess.run(
        ["git", "init", "-q", str(target)], check=True, env=clean_env(home)
    )
    git(target, "config", "user.email", "kernel-merge@example.invalid", home=home)
    git(target, "config", "user.name", "Kernel Merge", home=home)

    worker_private, worker_public = generate_keypair()
    approver_private, approver_public = generate_keypair()
    governance = target / "governance"
    governance.mkdir()
    catalog = (
        b"gates:\n"
        b"  - gate_id: landing\n"
        b"    rule_id: TESTS_EXECUTED\n"
        b"    blocking: true\n"
        b"    required_claims:\n"
        b"      - claim_id: tests-executed\n"
        b"        command: [/usr/bin/true]\n"
    )
    (governance / "gates.yaml").write_bytes(catalog)
    (governance / "producers.yaml").write_text(
        f"producers:\n  worker: {worker_public}\n  owner: {approver_public}\n",
        encoding="utf-8",
    )
    (governance / "evidence.json").write_text("[]\n", encoding="utf-8")
    (target / ".gitignore").write_text(
        "governance/journal.sqlite3\n", encoding="utf-8"
    )
    (target / "base.txt").write_text("base\n", encoding="utf-8")
    git(target, "add", "-A", home=home)
    git(target, "commit", "-q", "-m", "governed base", home=home)
    git(target, "branch", "-M", "main", home=home)
    tip = git(target, "rev-parse", "HEAD", home=home).strip()

    git(target, "switch", "-q", "-c", "candidate-work", home=home)
    (target / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    git(target, "add", "candidate.txt", home=home)
    git(target, "commit", "-q", "-m", "candidate", home=home)
    candidate = git(target, "rev-parse", "HEAD", home=home).strip()
    assert git(target, "rev-parse", f"{candidate}^", home=home).strip() == tip
    assert git(target, "rev-parse", f"{candidate}^{{tree}}", home=home).strip() != git(
        target, "rev-parse", f"{tip}^{{tree}}", home=home
    ).strip()
    git(target, "switch", "-q", "main", home=home)

    subject = subject_digest_for(target, candidate)
    evidence_body = {
        "claim_id": "tests-executed",
        "command": "/usr/bin/true",
        "command_digest": command_digest(["/usr/bin/true"]),
        "executable_path": "/usr/bin/true",
        "exit_code": 0,
        "producer_id": "worker",
        "subject_digest": subject,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }
    (governance / "evidence.json").write_text(
        json.dumps(
            [
                {
                    **evidence_body,
                    "signature": sign_evidence(evidence_body, worker_private),
                }
            ]
        ),
        encoding="utf-8",
    )

    task_id = "T-KERNEL-MERGE-E2E"
    journal = Journal(governance / "journal.sqlite3")
    candidate_record = TaskCandidate(task_id, "landing", subject, ()).as_record()
    journal.append(TaskCandidate(task_id, "landing", subject, ()))
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": tip,
        "catalog_digest": catalog_digest_for(catalog),
        "candidate_row_hash": candidate_row_hash(candidate_record),
        "approver_id": "owner",
    }
    approval = tmp_path / "merge-approval.json"
    approval.write_text(
        json.dumps(
            {**envelope, "signature": sign_approval(envelope, approver_private)}
        ),
        encoding="utf-8",
    )

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(target)
        monkeypatch.setattr(
            "ranex.cli.main.governed_repository_root", lambda: target.resolve()
        )
        exit_code = main(
            [
                "task",
                "merge",
                "--task-id",
                task_id,
                "--target-ref",
                "refs/heads/main",
                "--candidate",
                candidate,
                "--approval",
                str(approval),
            ]
        )

    assert exit_code == EXIT_PASS
    published = git(target, "rev-parse", "refs/heads/main", home=home).strip()
    assert published == candidate
    assert subject_digest_for(target, published) == envelope["subject"]
    assert envelope == {
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": tip,
        "catalog_digest": catalog_digest_for(catalog),
        "candidate_row_hash": candidate_row_hash(candidate_record),
        "approver_id": "owner",
    }

    entries = journal.entries()
    assert entries[0] == candidate_record
    merge_entries = entries[1:]
    assert [entry["type"] for entry in merge_entries] == [
        "task-merge-intent",
        "task-merge-check",
        "task-merge-check",
        "task-merge-check",
        "task-merge-check",
        "task-merge-check",
        "task-merge-outcome",
    ]
    assert merge_entries[0] == {
        "type": "task-merge-intent",
        "task_id": task_id,
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": tip,
    }
    assert [
        (entry["check"], entry["status"]) for entry in merge_entries[1:-1]
    ] == [
        ("policy_approval", "passed"),
        ("ancestry", "passed"),
        ("merge_range", "passed"),
        ("digest_evidence", "passed"),
        ("cas", "passed"),
    ]
    outcomes = [
        entry for entry in merge_entries if entry["type"] == "task-merge-outcome"
    ]
    assert len(outcomes) == 1
    assert outcomes[0]["candidate"] == candidate
    assert outcomes[0]["outcome"] == "PUBLISHED"
    assert journal.verify() is True


def test_first_delegation_ends_in_candidate_with_reviewable_diff(
    credential: str, harness: Path, bun: Path, tmp_path: Path
) -> None:
    target = build_target(tmp_path)
    home = tmp_path / "home"
    journal = tmp_path / "journal.sqlite3"
    wrapper = write_wrapper(tmp_path / "harness-wrapper.sh", bun, harness)

    # A real provider flakes; a fresh task id per attempt because one dispatch
    # is one judgement. The assertions themselves are never retried around.
    failures: list[str] = []
    for attempt in range(1, ATTEMPTS + 1):
        task_id = f"T-FIRST-DELEGATION-{attempt}"
        worktree = tmp_path / f"worktree-{attempt}"
        outcome = tmp_path / f"outcome-{attempt}.json"
        delegated = run_delegate(
            target=target,
            task_id=task_id,
            worktree=worktree,
            journal=journal,
            wrapper=wrapper,
            outcome=outcome,
            home=home,
            credential=credential,
        )
        if delegated.returncode == EXIT_PASS:
            break
        failures.append(
            f"attempt {attempt}: exit={delegated.returncode} "
            f"stderr={delegated.stderr[-1500:]!r}"
        )
    else:
        raise AssertionError(
            "the delegated run never completed against the live provider:\n"
            + "\n".join(failures)
        )

    # 1. The delegation completed and recorded a real outcome.
    assert delegated.returncode == EXIT_PASS, delegated.stderr
    written = json.loads(outcome.read_text(encoding="utf-8").strip())
    assert written["task_id"] == task_id
    assert written["timed_out"] is False
    commit = written["commit"]
    assert isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit)
    assert isinstance(written["suite_exit"], int)

    # 2. The diff is reviewable and non-empty, base taken from the journal's
    # dispatch record, never from the worker's report.
    rows = Journal(journal).entries()
    dispatch = next(
        row
        for row in rows
        if row.get("type") == "task-dispatch" and row.get("task_id") == task_id
    )
    base_commit = dispatch["base_commit"]
    assert re.fullmatch(r"[0-9a-f]{40}", str(base_commit))
    assert base_commit != commit
    diff = git(worktree, "diff", f"{base_commit}..{commit}", home=home)
    assert diff.strip(), "the delegated commit produced an empty diff"
    assert "AGENT_NOTE.txt" in diff, f"reviewable diff names no delegated work:\n{diff}"

    # 3. The suite genuinely executed against the materialised commit: the
    # note-test is red at base and can only pass if the model's file is in the
    # tree the kernel materialised. An empty tail or a collection error would
    # mean nothing ran.
    tail = str(written["suite_output_tail"])
    assert tail.strip(), "suite output is empty; nothing executed"
    assert written["suite_exit"] == 0, f"suite failed against the delegated tree:\n{tail}"
    assert re.search(r"\b1 passed\b", tail), f"no evidence the suite ran tests:\n{tail}"

    # 4. Judgement is a CANDIDATE naming its missing claims — non-empty,
    # because no evidence was ever produced for the required claim.
    judged = run_judge(
        target=target,
        task_id=task_id,
        worktree=worktree,
        commit=commit,
        journal=journal,
        home=home,
    )
    assert judged.returncode == EXIT_FAIL, judged.stderr
    assert "CANDIDATE" in judged.stdout, judged.stdout

    candidates = [
        row
        for row in Journal(journal).entries()
        if row.get("type") == "task-candidate" and row.get("task_id") == task_id
    ]
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate["verdict"] == "CANDIDATE"
    assert candidate["missing_claims"] == ["tests-executed"], (
        "the candidate must name its missing claims — 'tests-executed' was "
        f"never evidenced, yet the journal says: {candidate['missing_claims']!r}"
    )

    # 5. No PASS anywhere: not in the delegate's output, not in the judgement,
    # not in any journal row for this task.
    assert "PASS" not in delegated.stdout + delegated.stderr
    assert "PASS" not in judged.stdout
    assert not any(row.get("verdict") == "PASS" for row in Journal(journal).entries())

    # 6. The chain still verifies after the whole flow.
    assert Journal(journal).verify() is True
