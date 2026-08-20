"""SLICE-059 — real e2e: the task family (dispatch/judge/merge) on real
subjects.

Issue #39's exact ownership (file 1 of 2). The task family rides the
ADR-032 frame (docs/adr/ADR-032-real-e2e-suite-framework.md) as its fourth
family customer, following the SLICE-056/057/058 patterns, and mirrors the
``tests/e2e/test_first_delegation.py`` target construction the contract
names: a real disposable git worktree of a real governed target, real git
identity, real journalling — never a fixture repo.

The journeys (every command below was verified against the installed kernel
at 5e1ea681d in a /tmp/opencode prototype before this file was frozen — the
prototype is the freeze-time evidence, not an assumption):

* **The dispatch→judge journey** — ``task dispatch`` creates a real external
  worktree of the governed target and journals the immutable dispatch facts
  (base commit); the worker commits real work in the worktree; the kernel's
  own ``run`` executes the gate's claim command FOR REAL inside the worktree
  (``git status --porcelain``) and records signed evidence bound to the
  emitted tree; ``task judge`` materialises the candidate over that real
  produced evidence. The captured transcript (DISPATCHED + RECORDED +
  CANDIDATE lines) freezes against ``expected/task-dispatch-judge.out``
  through the ONE centralized normalizer — the worktree path and the subject
  digests are the volatile classes (``<ABS-PATH>`` / ``<DIGEST>``).
* **The tampered-evidence arm** (SP-4) — a byte-tampered evidence record
  (its signed body altered, signature kept) is refused admission, so the
  verdict REFUSES: the judge names the now-missing claim and exits 1 —
  never a default PASS on tampered evidence.
* **The merge refusal journey** — real evidence produced by the approver's
  own ``run`` at the candidate tree; the producer approves their own
  evidence → ``sad-path-14 self-approval`` (the C-2 golden,
  ``expected/task-merge-refusal.out``); a moved base → ``sad-path-9
  tip-mismatch`` (the stale base named, SP-6); a wrong subject digest in
  the approval → ``sad-path-5 subject-digest-mismatch`` (the digest
  mismatch named, C-3). Every refusal replays byte-identically (a second
  task id, a second approval, the same named reason).
* **The clean merge** — a reviewer (producer ≠ approver, evidence produced
  by the worker) publishes the candidate through the kernel's ordered
  journalled checks (policy_approval, ancestry, merge_range,
  digest_evidence, cas — all passed, PUBLISHED, journal chain verifies).
  The kernel merges; nothing here merges for it.
* **The worktree-cleanup arm** (SP-7) — the journey removes every
  disposable worktree it created; the detector asserts none survive, and a
  planted survivor provably turns it red.
* **The fanout qualification arm** (AC-4) — the qualification assertions
  over ``task fanout``'s tasks-file contract are authored here and frozen,
  skipped-with-name until SLICE-036 (#19) closes: a follow-up governed
  change enables them, never this slice.

Probe gating: this file's journeys are all-local (real git, real files, the
kernel CLI) — no frame probe gates them, matching the keygen family's
precedent; git and the interpreter are hard tool requirements that fail
loudly when absent. The ``run``/``merge`` stages drive the CLI in-process
under a patched governed root — the frozen kernel-merge convention from
``tests/e2e/test_first_delegation.py`` (``run`` refuses second-repository
targets, and the disposable target is not the CLI's own checkout).

The two goldens ``expected/task-dispatch-judge.out`` and
``expected/task-merge-refusal.out`` are the implementation lane's
artifacts, captured from real runs of these exact journeys (transcripts
piped through ``_prereqs.normalize_transcript`` exactly as the tests do);
their absence is this file's honest frozen red. The sabotage control and
the normalizer-application contract refuse every hand-sanitized golden
shape.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.bootstrap.composition import catalog_digest_for
from ranex.cli.main import subject_digest_for
from ranex.foundation.approval import candidate_row_hash, sign_approval
from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.task import TaskCandidate

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

#: The family's gate and claim, registered in the target's committed catalog:
#: a real command that really runs (in the dispatched worktree) and attests
#: something true about the emitted tree — the tree is clean at the claim
#: command's exit.
FAMILY_GATE = "task-family"
FAMILY_CLAIM = "tree-clean"
FAMILY_COMMAND = ("git", "status", "--porcelain")

DISPATCH_JOURNAL_TASK = "T-TASK-FAMILY"
TAMPER_TASK = "T-TASK-FAMILY-TAMPER"
SELF_APPROVAL_TASK = "T-TASK-FAMILY-SELF"
SELF_APPROVAL_REPLAY_TASK = "T-TASK-FAMILY-SELF-REPLAY"
STALE_BASE_TASK = "T-TASK-FAMILY-STALE"
STALE_BASE_REPLAY_TASK = "T-TASK-FAMILY-STALE-REPLAY"
DIGEST_TASK = "T-TASK-FAMILY-DIGEST"
DIGEST_REPLAY_TASK = "T-TASK-FAMILY-DIGEST-REPLAY"
CLEAN_MERGE_TASK = "T-TASK-FAMILY-CLEAN"

GATES = """\
gates:
  - gate_id: task-family
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tree-clean
        command: ["git", "status", "--porcelain"]
"""

#: The AC-4 gate: fanout qualification assertions are authored and frozen
#: here, but #19 (SLICE-036) has not closed. The skip is the two-grammar
#: scheme's context tier — byte-stable by construction (a static string),
#: declared in the suite manifest at the close-time ceremony, and enabled
#: only in a follow-up governed change after #19 closes.
FANOUT_SKIP_REASON = (
    "ranex-context:fanout-gated: SLICE-036 (#19) has not closed; the fanout "
    "qualification assertions authored in this file stay skipped-with-name "
    "until a follow-up governed change enables them after #19 closes"
)


def _child_env(home: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """The operator's clean environment for the CLI subprocesses."""

    environment = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(REAL_REPO / "src"),
        "HOME": str(home),
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    environment.update(extra or {})
    return environment


def _git(repo: Path, *arguments: str, home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=_child_env(home),
    )


def _cli(
    argv: list[str], home: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        capture_output=True,
        text=True,
        check=False,
        env=_child_env(home),
    )


def _cli_in_process(
    argv: list[str], *, root: Path, home: Path, key: Path | None = None
) -> tuple[int, str, str]:
    """Drive one CLI command in-process against a patched governed root.

    The kernel-merge convention (tests/e2e/test_first_delegation.py): the
    governed root is the disposable target, the cwd with it, the signing key
    in its real environment variable. stdout/stderr are captured exactly as
    the subprocess arms capture theirs, so transcripts are byte-comparable.
    """

    import ranex.cli.main as cli_main

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(root)
        monkeypatch.setattr(cli_main, "governed_repository_root", lambda: root.resolve())
        monkeypatch.setenv("HOME", str(home))
        if key is not None:
            monkeypatch.setenv("RANEX_SIGNING_KEY", str(key))
        else:
            monkeypatch.delenv("RANEX_SIGNING_KEY", raising=False)
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli_main.main(argv)
    return code, out.getvalue(), err.getvalue()


def golden_text(name: str) -> str:
    """Read a family golden, refusing its absence loudly.

    The two SLICE-059 task-family goldens are the implementation lane's
    artifacts, captured from real runs of these exact journeys (transcripts
    piped through ``_prereqs.normalize_transcript``). A missing golden is
    this file's frozen red — the honest one — until that capture lands.
    """

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-059 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture below), pipe the CLI transcript through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _prereqs.normalize_transcript(transcript),
        golden_text(name),
        family=name.removesuffix(".out"),
    )


@dataclass
class TaskFamilyJourney:
    """Everything the frozen tests consume from the one task-family journey."""

    base: Path
    target: Path
    journal: Path
    dispatch: subprocess.CompletedProcess[str]
    recorded: str
    judged: subprocess.CompletedProcess[str]
    judged_row: dict[str, object]
    tampered_judged: subprocess.CompletedProcess[str]
    tampered_row: dict[str, object]
    self_approval: tuple[int, str, str]
    self_approval_replay: tuple[int, str, str]
    stale_base: tuple[int, str, str]
    stale_base_replay: tuple[int, str, str]
    digest_mismatch: tuple[int, str, str]
    digest_mismatch_replay: tuple[int, str, str]
    clean_merge: tuple[int, str, str]
    published_ref: str
    candidate: str
    clean_checks: list[tuple[str, str]]
    merge_journal_verifies: bool


def _build_target(base: Path) -> tuple[Path, Path, Path, Path, str]:
    """A real governed target on the first-delegation construction."""

    target = base / "target"
    target.mkdir()
    home = base / "home"
    home.mkdir(exist_ok=True)
    initialized = subprocess.run(
        ["git", "init", "-q", str(target)], check=False, env=_child_env(home)
    )
    assert initialized.returncode == 0, initialized.stderr
    for name, value in (
        ("user.email", "task-family@example.invalid"),
        ("user.name", "Task Family"),
    ):
        assert _git(target, "config", name, value, home=home).returncode == 0

    worker_private, worker_public = generate_keypair()
    owner_private, owner_public = generate_keypair()
    reviewer_private, reviewer_public = generate_keypair()
    governance = target / "governance"
    governance.mkdir()
    # Ranex's own bookkeeping is gitignored, never committed: the evidence
    # file `run` writes must be untracked for run's own dirty-tree exemption
    # to hold on the second run (the kernel's frozen rule).
    (target / ".gitignore").write_text(
        "governance/journal.sqlite3\ngovernance/evidence.json\n", encoding="utf-8"
    )
    (target / "app.txt").write_text("governed\n", encoding="utf-8")
    (governance / "gates.yaml").write_text(GATES, encoding="utf-8")
    (governance / "producers.yaml").write_text(
        f"producers:\n  worker: {worker_public}\n  owner: {owner_public}\n"
        f"  reviewer: {reviewer_public}\n",
        encoding="utf-8",
    )
    assert _git(target, "add", "-A", home=home).returncode == 0
    assert _git(target, "commit", "-q", "-m", "initial governed work", home=home).returncode == 0
    assert _git(target, "branch", "-M", "main", home=home).returncode == 0

    worker_key = base / "worker.key"
    worker_key.write_text(worker_private + "\n", encoding="utf-8")
    worker_key.chmod(0o600)
    owner_key = base / "owner.key"
    owner_key.write_text(owner_private + "\n", encoding="utf-8")
    owner_key.chmod(0o600)
    return target, worker_key, owner_key, home, reviewer_private


def _judge(
    *,
    task_id: str,
    worktree: Path,
    journal: Path,
    home: Path,
) -> subprocess.CompletedProcess[str]:
    """Judge the worktree's HEAD once — one dispatch, one judgement."""

    emitted = _git(worktree, "rev-parse", "HEAD", home=home).stdout.strip()
    return _cli(
        [
            "task",
            "judge",
            "--task-id",
            task_id,
            "--emitted-worktree",
            str(worktree),
            "--emitted-commit",
            emitted,
            "--gate",
            FAMILY_GATE,
            "--gate-catalog",
            "governance/gates.yaml",
            "--evidence",
            "governance/evidence.json",
            "--producers",
            "governance/producers.yaml",
            "--journal",
            str(journal),
        ],
        home,
    )


def _candidate_row(journal: Path, task_id: str) -> dict[str, object]:
    rows = [
        row
        for row in Journal(journal).entries()
        if row.get("type") == "task-candidate" and row.get("task_id") == task_id
    ]
    assert len(rows) == 1, f"expected exactly one candidate row for {task_id}: {rows}"
    return rows[0]


def _dispatch_work_and_run(
    *,
    task_id: str,
    target: Path,
    journal: Path,
    home: Path,
    base: Path,
    worker_key: Path,
    work_name: str,
) -> tuple[subprocess.CompletedProcess[str], str, Path]:
    """dispatch → real work commit → real run evidence, once."""

    worktree = base / f"worktree-{task_id}"
    dispatched = _cli(
        [
            "task",
            "dispatch",
            "--task-id",
            task_id,
            "--target",
            str(target),
            "--worktree",
            str(worktree),
            "--journal",
            str(journal),
        ],
        home,
    )
    assert dispatched.returncode == 0, dispatched.stderr

    notes = worktree / "NOTES"
    notes.mkdir()
    (notes / work_name).write_text(f"{work_name} ran\n", encoding="utf-8")
    assert _git(worktree, "add", "-A", home=home).returncode == 0
    committed = _git(worktree, "commit", "-q", "-m", "the worker's real work", home=home)
    assert committed.returncode == 0, committed.stderr

    code, recorded, err = _cli_in_process(
        [
            "run",
            "--claim",
            FAMILY_CLAIM,
            "--producer",
            "worker",
            "--gate",
            FAMILY_GATE,
            "--repository",
            ".",
            "--evidence",
            "governance/evidence.json",
            "--producers",
            "governance/producers.yaml",
            "--",
            *FAMILY_COMMAND,
        ],
        root=worktree,
        home=home,
        key=worker_key,
    )
    assert code == 0, err
    return dispatched, recorded, worktree


def _refusal_reason(transcript: str) -> str:
    """The stable named-reason portion of a REFUSED line (the bytes after
    ``reason=``): the line's task-id slot differs per task by design (one
    dispatch, one judgement), so replay equality compares the reason —
    the named refusal the kernel guarantees identical — never the id."""

    line = next(
        line for line in transcript.splitlines() if line.startswith("REFUSED")
    )
    return line.split("  reason=", 1)[1]


def _merge_refusal(
    *,
    task_id: str,
    approver: str,
    subject: str,
    tip: str,
    candidate: str,
    target: Path,
    home: Path,
    base: Path,
    private_key: str,
) -> tuple[int, str, str]:
    """Append a candidate row, sign an approval, attempt the merge once."""

    merge_journal = target / "governance" / "journal.sqlite3"
    domain = TaskCandidate(task_id, FAMILY_GATE, subject, ())
    row = domain.as_record()
    Journal(merge_journal).append(domain)
    envelope = {
        "candidate": candidate,
        "subject": subject,
        "target_ref": "refs/heads/main",
        "tip": tip,
        "catalog_digest": catalog_digest_for((target / "governance" / "gates.yaml").read_bytes()),
        "candidate_row_hash": candidate_row_hash(row),
        "approver_id": approver,
    }
    approval = base / f"approval-{task_id}.json"
    approval.write_text(
        json.dumps({**envelope, "signature": sign_approval(envelope, private_key)}),
        encoding="utf-8",
    )
    return _cli_in_process(
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
        ],
        root=target,
        home=home,
    )


@pytest.fixture(scope="module")
def family(tmp_path_factory: pytest.TempPathFactory) -> TaskFamilyJourney:
    """The one task-family journey: ordered, loud at every stage."""

    base = tmp_path_factory.mktemp("task-family")
    target, worker_key, owner_key, home, reviewer_private = _build_target(base)
    journal = base / "journal.sqlite3"

    # --- journey 1: dispatch -> work -> real run evidence -> judge ----------
    dispatched, recorded, worktree = _dispatch_work_and_run(
        task_id=DISPATCH_JOURNAL_TASK,
        target=target,
        journal=journal,
        home=home,
        base=base,
        worker_key=worker_key,
        work_name="task-family.txt",
    )
    judged = _judge(
        task_id=DISPATCH_JOURNAL_TASK,
        worktree=worktree,
        journal=journal,
        home=home,
    )
    judged_row = _candidate_row(journal, DISPATCH_JOURNAL_TASK)

    # --- SP-4: tampered judge evidence -> the verdict refuses ---------------
    tamper_dispatch, _, tamper_worktree = _dispatch_work_and_run(
        task_id=TAMPER_TASK,
        target=target,
        journal=journal,
        home=home,
        base=base,
        worker_key=worker_key,
        work_name="tamper.txt",
    )
    assert tamper_dispatch.returncode == 0, tamper_dispatch.stderr
    evidence_path = tamper_worktree / "governance" / "evidence.json"
    records = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert records, "the run recorded no evidence to tamper with"
    tampered_records = json.loads(json.dumps(records))
    tampered_records[-1]["exit_code"] = 99  # alter the signed body, keep the signature
    evidence_path.write_text(json.dumps(tampered_records), encoding="utf-8")
    tampered_judged = _judge(
        task_id=TAMPER_TASK,
        worktree=tamper_worktree,
        journal=journal,
        home=home,
    )
    tampered_rows = [_candidate_row(journal, TAMPER_TASK)]

    # --- the merge journey on the same target -------------------------------
    stale_tip = _git(target, "rev-parse", "HEAD", home=home).stdout.strip()
    assert _git(target, "switch", "-q", "-c", "candidate-work", home=home).returncode == 0
    (target / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    assert _git(target, "add", "candidate.txt", home=home).returncode == 0
    committed = _git(target, "commit", "-q", "-m", "candidate", home=home)
    assert committed.returncode == 0, committed.stderr
    assert _git(target, "switch", "-q", "main", home=home).returncode == 0

    # the base moves BEFORE any approval exists (SP-6's premise)
    (target / "base-moved.txt").write_text("the base moved\n", encoding="utf-8")
    assert _git(target, "add", "base-moved.txt", home=home).returncode == 0
    moved = _git(target, "commit", "-q", "-m", "the base moves", home=home)
    assert moved.returncode == 0, moved.stderr
    moved_tip = _git(target, "rev-parse", "HEAD", home=home).stdout.strip()

    # the candidate rides on top of the moved base (clean tree: no evidence yet)
    assert _git(target, "switch", "-q", "candidate-work", home=home).returncode == 0
    rebased = _git(target, "rebase", "main", home=home)
    assert rebased.returncode == 0, rebased.stderr
    candidate = _git(target, "rev-parse", "HEAD", home=home).stdout.strip()
    assert _git(target, "switch", "-q", "main", home=home).returncode == 0

    # real evidence AT the candidate tree: the owner (the self-approval arm's
    # producer-approver) and the worker (the clean arm's producer) each run
    # the claim for real on the candidate branch; the untracked evidence file
    # carries across the branch switches.
    for producer, key in (("owner", owner_key), ("worker", worker_key)):
        assert _git(target, "switch", "-q", "candidate-work", home=home).returncode == 0
        code, _, err = _cli_in_process(
            [
                "run",
                "--claim",
                FAMILY_CLAIM,
                "--producer",
                producer,
                "--gate",
                FAMILY_GATE,
                "--repository",
                ".",
                "--evidence",
                "governance/evidence.json",
                "--producers",
                "governance/producers.yaml",
                "--",
                *FAMILY_COMMAND,
            ],
            root=target,
            home=home,
            key=key,
        )
        assert code == 0, err
        assert _git(target, "switch", "-q", "main", home=home).returncode == 0

    candidate_subject = subject_digest_for(target, candidate)
    wrong_subject = "sha256:" + "0" * 64
    owner_private = owner_key.read_text(encoding="utf-8").strip()

    self_approval = _merge_refusal(
        task_id=SELF_APPROVAL_TASK,
        approver="owner",
        subject=candidate_subject,
        tip=moved_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=owner_private,
    )
    self_approval_replay = _merge_refusal(
        task_id=SELF_APPROVAL_REPLAY_TASK,
        approver="owner",
        subject=candidate_subject,
        tip=moved_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=owner_private,
    )
    stale_base = _merge_refusal(
        task_id=STALE_BASE_TASK,
        approver="reviewer",
        subject=candidate_subject,
        tip=stale_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=reviewer_private,
    )
    stale_base_replay = _merge_refusal(
        task_id=STALE_BASE_REPLAY_TASK,
        approver="reviewer",
        subject=candidate_subject,
        tip=stale_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=reviewer_private,
    )
    digest_mismatch = _merge_refusal(
        task_id=DIGEST_TASK,
        approver="reviewer",
        subject=wrong_subject,
        tip=moved_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=reviewer_private,
    )
    digest_mismatch_replay = _merge_refusal(
        task_id=DIGEST_REPLAY_TASK,
        approver="reviewer",
        subject=wrong_subject,
        tip=moved_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=reviewer_private,
    )
    clean_merge = _merge_refusal(
        task_id=CLEAN_MERGE_TASK,
        approver="reviewer",
        subject=candidate_subject,
        tip=moved_tip,
        candidate=candidate,
        target=target,
        home=home,
        base=base,
        private_key=reviewer_private,
    )
    published_ref = _git(target, "rev-parse", "refs/heads/main", home=home).stdout.strip()
    merge_journal = target / "governance" / "journal.sqlite3"
    merge_entries = Journal(merge_journal).entries()
    clean_checks = [
        (entry["check"], entry["status"])
        for entry in merge_entries
        if entry.get("type") == "task-merge-check" and entry.get("task_id") == CLEAN_MERGE_TASK
    ]
    merge_journal_verifies = Journal(merge_journal).verify()

    # --- SP-7: every disposable worktree is removed; survivors detected -----
    for task_id in (DISPATCH_JOURNAL_TASK, TAMPER_TASK):
        worktree = base / f"worktree-{task_id}"
        removed = _git(target, "worktree", "remove", "--force", str(worktree), home=home)
        assert removed.returncode == 0, removed.stderr
    assert _git(target, "worktree", "prune", home=home).returncode == 0

    return TaskFamilyJourney(
        base=base,
        target=target,
        journal=journal,
        dispatch=dispatched,
        recorded=recorded,
        judged=judged,
        judged_row=judged_row,
        tampered_judged=tampered_judged,
        tampered_row=tampered_rows[0],
        self_approval=self_approval,
        self_approval_replay=self_approval_replay,
        stale_base=stale_base,
        stale_base_replay=stale_base_replay,
        digest_mismatch=digest_mismatch,
        digest_mismatch_replay=digest_mismatch_replay,
        clean_merge=clean_merge,
        published_ref=published_ref,
        candidate=candidate,
        clean_checks=clean_checks,
        merge_journal_verifies=merge_journal_verifies,
    )


def _surviving_worktrees(base: Path) -> list[Path]:
    """Directories under the journey base that still carry a worktree marker."""

    return sorted(
        path
        for path in base.rglob(".git")
        if path.is_file() and path.parent != base / "target"
    )


def test_golden_contract_task_dispatch_judge() -> None:
    """The dispatch→judge golden's own contract, held on EVERY host: it
    exists, it is a fixpoint of the one normalizer, and it carries the
    journey's real volatile classes — the masked worktree path and the
    masked subject digests. This is the file's ungated red at the freeze
    commit: the golden does not exist yet, and a host that cannot run the
    journey still holds the golden to its contract once captured."""

    golden = golden_text("task-dispatch-judge.out")
    assert "DISPATCHED" in golden, golden
    assert "RECORDED" in golden, golden
    assert "CANDIDATE" in golden, golden
    assert "<ABS-PATH>" in golden, (
        "task-dispatch-judge.out carries no <ABS-PATH> token: the journey's "
        "dispatched worktree path is real volatile material the normalizer "
        "must have tamed — a golden without the token is hand-sanitized "
        "text, not a captured transcript"
    )
    assert "<DIGEST>" in golden, (
        "task-dispatch-judge.out carries no <DIGEST> token: the journey's "
        "subject digests are real volatile material the normalizer must "
        "have tamed"
    )
    assert _prereqs.normalize_transcript(golden) == golden, (
        "task-dispatch-judge.out is not a normalizer fixpoint: it still "
        "contains bytes the frozen grammar would mask, which no capture "
        "piped through normalize_transcript can"
    )


def test_dispatch_run_judge_transcript_matches_the_golden(
    family: TaskFamilyJourney,
) -> None:
    """C-1: the dispatch→judge lifecycle transcript, byte-frozen against its
    golden — the verdict is CANDIDATE strictly per kernel rules (the judge
    never emits a verdict word beyond its frozen contract), with the real
    produced evidence satisfying every required claim (exit 0, no missing
    claims) and the journal chain still verifying after the whole flow."""

    assert family.dispatch.returncode == 0, family.dispatch.stderr
    assert family.judged.returncode == 0, family.judged.stderr
    assert family.judged_row["verdict"] == "CANDIDATE"
    assert family.judged_row["missing_claims"] == []
    transcript = f"{family.dispatch.stdout}{family.recorded}{family.judged.stdout}"
    compare_golden(transcript, "task-dispatch-judge.out")
    assert Journal(family.journal).verify() is True


def test_tampered_judge_evidence_refuses_never_a_default_pass(
    family: TaskFamilyJourney,
) -> None:
    """SP-4: judge input evidence tampered → the verdict refuses. The
    tampered record (signed body altered, signature kept) is refused
    admission, the claim it claimed to satisfy is named missing, and the
    judge exits 1 — discriminated against the clean journey's exit 0 above,
    so a default PASS on tampered evidence is impossible."""

    assert family.tampered_judged.returncode == 1, family.tampered_judged.stdout
    assert "CANDIDATE" in family.tampered_judged.stdout
    assert family.tampered_row["verdict"] == "CANDIDATE"
    assert family.tampered_row["missing_claims"] == [FAMILY_CLAIM], (
        "the tampered evidence must leave the claim it forged named "
        f"missing, yet the journal says: {family.tampered_row['missing_claims']!r}"
    )
    assert family.tampered_judged.returncode != family.judged.returncode


def test_self_approval_refusal_on_real_evidence(family: TaskFamilyJourney) -> None:
    """C-2 / SP-5: the producer approves its own evidence → refusal. The
    approver's evidence is genuinely the kernel's own output (a real `run`
    at the candidate tree), so the refusal is demonstrated on real
    evidence, and the transcript freezes against the merge-refusal golden.
    The refusal is identical on replay (a second task, a second approval,
    byte-equal reason)."""

    code, out, err = family.self_approval
    assert code == 1, out
    transcript = err
    assert "REFUSED" in transcript
    assert "sad-path-14 self-approval" in transcript, transcript
    compare_golden(transcript, "task-merge-refusal.out")

    replay_code, replay_out, replay_err = family.self_approval_replay
    assert replay_code == 1, replay_out
    assert _refusal_reason(replay_err) == _refusal_reason(transcript), (
        "the self-approval refusal's named reason must be byte-identical on "
        f"replay:\nfirst={_refusal_reason(transcript)!r}\n"
        f"replay={_refusal_reason(replay_err)!r}"
    )


def test_moved_base_and_digest_mismatch_refusals_name_the_reason(
    family: TaskFamilyJourney,
) -> None:
    """C-3 / SP-6: merge with a moved base → refusal naming the stale base;
    merge with a wrong digest → refusal naming the digest mismatch. Never a
    silent merge, never an unnamed failure; the same named refusal on
    replay."""

    code, out, err = family.stale_base
    assert code == 1, out
    assert "REFUSED" in err
    assert "sad-path-9 tip-mismatch" in err, err
    replay_code, replay_out, replay_err = family.stale_base_replay
    assert replay_code == 1, replay_out
    assert _refusal_reason(replay_err) == _refusal_reason(err), (
        "the stale-base refusal's named reason must be byte-identical on "
        f"replay:\nfirst={_refusal_reason(err)!r}\n"
        f"replay={_refusal_reason(replay_err)!r}"
    )

    digest_code, digest_out, digest_err = family.digest_mismatch
    assert digest_code == 1, digest_out
    assert "REFUSED" in digest_err
    assert "sad-path-5 subject-digest-mismatch" in digest_err, digest_err
    digest_replay_code, digest_replay_out, digest_replay_err = family.digest_mismatch_replay
    assert digest_replay_code == 1, digest_replay_out
    assert _refusal_reason(digest_replay_err) == _refusal_reason(digest_err), (
        "the digest-mismatch refusal's named reason must be byte-identical "
        f"on replay:\nfirst={_refusal_reason(digest_err)!r}\n"
        f"replay={_refusal_reason(digest_replay_err)!r}"
    )


def test_clean_candidate_publishes_through_the_ordered_checks(
    family: TaskFamilyJourney,
) -> None:
    """The Real E2E journey's last step: the clean candidate (producer ≠
    approver, real evidence, current base) publishes through the kernel's
    ordered journalled checks — the kernel merges, the test never does."""

    code, out, err = family.clean_merge
    assert code == 0, err
    assert "PUBLISHED" in out, out
    assert family.published_ref == family.candidate
    assert family.clean_checks == [
        ("policy_approval", "passed"),
        ("ancestry", "passed"),
        ("merge_range", "passed"),
        ("digest_evidence", "passed"),
        ("cas", "passed"),
    ], family.clean_checks
    assert family.merge_journal_verifies is True


def test_worktree_residue_detection_goes_red_on_a_survivor(
    family: TaskFamilyJourney,
) -> None:
    """SP-7: a disposable worktree that survives cleanup is detected — the
    detector is green on the cleaned journey and provably red on a planted
    survivor, so silent residue is impossible."""

    assert _surviving_worktrees(family.base) == [], (
        "the journey left disposable worktrees behind: "
        f"{_surviving_worktrees(family.base)}"
    )
    survivor = family.base / "worktree-left-behind"
    survivor.mkdir()
    (survivor / ".git").write_text(
        f"gitdir: {family.target / '.git' / 'worktrees' / 'left-behind'}\n",
        encoding="utf-8",
    )
    try:
        assert _surviving_worktrees(family.base) == [survivor / ".git"], (
            "the planted survivor went undetected"
        )
    finally:
        (survivor / ".git").unlink()
        survivor.rmdir()


def test_goldens_carry_real_volatile_material(family: TaskFamilyJourney) -> None:
    """AC-1's integrity contract: each golden is a machine-normalized
    capture, not hand-sanitized text — a fixpoint of the one normalizer,
    carrying the masked class exactly where the journey emits live volatile
    material, and a golden holding LIVE volatile bytes provably cannot
    match: re-substituting a live digest into the real golden makes the
    comparison fail."""

    name = "task-dispatch-judge.out"
    transcript = f"{family.dispatch.stdout}{family.recorded}{family.judged.stdout}"
    golden = golden_text(name)
    assert "<DIGEST>" in golden
    assert _prereqs.normalize_transcript(golden) == golden
    live = family.judged_row["subject_digest"]
    assert isinstance(live, str) and live.startswith("sha256:")
    doctored = golden.replace("<DIGEST>", live, 1)
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _prereqs.normalize_transcript(transcript),
            doctored,
            family=name.removesuffix(".out"),
        )

    refusal_name = "task-merge-refusal.out"
    refusal_golden = golden_text(refusal_name)
    assert _prereqs.normalize_transcript(refusal_golden) == refusal_golden, (
        "task-merge-refusal.out is not a normalizer fixpoint"
    )
    assert "sad-path-14 self-approval" in refusal_golden, refusal_golden


def test_sabotage_control_mutated_golden_diffs_dirty(family: TaskFamilyJourney) -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte of
    the expected file and the comparator must diff dirty, naming the family
    and carrying exactly the first differing hunk — never a bare
    ``assert False``. The dispatch golden's verdict word and the refusal
    golden's reason word are the discriminating bytes."""

    journey_transcript = (
        f"{family.dispatch.stdout}{family.recorded}{family.judged.stdout}"
    )
    for name, transcript, verdict_word in (
        ("task-dispatch-judge.out", journey_transcript, "CANDIDATE"),
        ("task-merge-refusal.out", family.self_approval[2], "REFUSED"),
    ):
        family_label = name.removesuffix(".out")
        golden = golden_text(name)
        assert verdict_word in golden, golden
        mutated = golden.replace(verdict_word, "Q" + verdict_word[1:], 1)
        with pytest.raises(AssertionError) as raised:
            _prereqs.compare_transcript(
                _prereqs.normalize_transcript(transcript),
                mutated,
                family=family_label,
            )
        message = str(raised.value)
        assert family_label in message, (
            f"the mismatch must name the golden family {family_label!r}: {message}"
        )
        assert "@@" in message, (
            "the mismatch must carry the first differing hunk header: " + message
        )


def test_fanout_qualification_arms_wait_for_slice036(tmp_path: Path) -> None:
    """AC-4: the fanout qualification assertions are authored and frozen,
    skipped-with-name before #19 (SLICE-036) closes — never green, never
    failed. Enabled only in a follow-up governed change after #19 closes.

    Authored assertions (the qualification-only surface, all local, no
    credential): `task fanout` refuses a pool below one, a tasks file whose
    lines are not exactly {task_id, prompt, worktree}, and duplicate task
    ids or worktrees — the batch grammar SLICE-036 froze. Publishing and
    production fanout remain refused by surfaces this family does not own.
    """

    pytest.skip(FANOUT_SKIP_REASON)

    # Enabled shape (dead until the skip is lifted by the follow-up governed
    # change): every arm below was verified against the installed kernel at
    # 5e1ea681 in the freeze-time prototype.
    home = tmp_path / "home"
    home.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    assert subprocess.run(
        ["git", "init", "-q", str(target)], check=False, env=_child_env(home)
    ).returncode == 0

    tasks = tmp_path / "tasks.jsonl"
    tasks.write_text(
        '{"task_id": "F-1", "prompt": "p", "worktree": "wt-a"}\n'
        '{"task_id": "F-1", "prompt": "p2", "worktree": "wt-b"}\n',
        encoding="utf-8",
    )
    refused = _cli(
        [
            "task",
            "fanout",
            "--tasks",
            str(tasks),
            "--target",
            str(target),
            "--journal",
            str(tmp_path / "journal.sqlite3"),
            "--harness",
            "/bin/false",
            "--model",
            "m",
            "--timeout",
            "10",
            "--suite",
            "/bin/true",
            "--pool",
            "1",
            "--outcome-dir",
            str(tmp_path),
        ],
        home,
    )
    assert refused.returncode == 3, refused.stdout
    assert "duplicate task_id" in refused.stderr, refused.stderr

    tasks.write_text('{"task_id": "F-1", "prompt": "p"}\n', encoding="utf-8")
    malformed = _cli(
        [
            "task",
            "fanout",
            "--tasks",
            str(tasks),
            "--target",
            str(target),
            "--journal",
            str(tmp_path / "journal.sqlite3"),
            "--harness",
            "/bin/false",
            "--model",
            "m",
            "--timeout",
            "10",
            "--suite",
            "/bin/true",
            "--pool",
            "1",
            "--outcome-dir",
            str(tmp_path),
        ],
        home,
    )
    assert malformed.returncode == 3, malformed.stdout
    assert "must contain exactly task_id, prompt and worktree" in malformed.stderr
