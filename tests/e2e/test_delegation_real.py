"""SLICE-059 — real e2e: the delegation family (a real model, a real diff).

Issue #39's exact ownership (file 2 of 2). The delegation arm mirrors the
frozen ``tests/e2e/test_first_delegation.py`` conventions the contract
names: a real governed target, a real harness fork, bun, a free model over
OpenRouter, a bounded retry budget with a fresh task id per attempt (one
dispatch is one judgement), and a red-at-base note test that can only turn
green through the model's real work reaching the materialised commit.

The family rides the ADR-032 frame: the credential gate is the frame's
``openrouter_key`` probe (SP-1/C-5 — a host without the credential gets
the named ``ranex-prereq:openrouter_key:`` skip, never green, declared in
the suite manifest at the close-time ceremony), the harness fork gate is
the ``harness_fork`` probe, the normalizer is the frame's one function,
and the comparison is the frame's comparator with the family label.

The journeys (verified against the installed kernel at 5e1ea681 — the
freeze-time prototype plus the green first-delegation test itself):

* **The red-at-base proof** — the target's committed note test runs at the
  dispatch base BEFORE any delegation and fails (``1 failed``): the suite
  the kernel records is discriminating by construction, so a model that
  produces no diff cannot pass it (SP-3's guarantee observed up front).
* **The delegated journey** — ``task delegate`` dispatches a real worktree,
  runs the model once (ATTEMPTS=3, fresh task id per attempt on provider
  flake — the assertions are never retried around), and the kernel records
  the suite output at the emitted commit. The diff is read on disk against
  the journal's dispatch-record base — never the worker's report — and its
  normalized bytes freeze against ``expected/delegation-diff.out`` (C-4).
* **The judgement arm** — the emitted commit judged over the real produced
  tree is a CANDIDATE naming its missing claims (no evidence was ever
  produced for the required claim) and there is no PASS anywhere: not in
  the delegate's output, not in the judgement, not in any journal row.

The golden ``expected/delegation-diff.out`` is the implementation lane's
artifact, captured from a real run of this exact journey (the diff piped
through ``_prereqs.normalize_transcript`` exactly as the tests do); its
absence is this file's honest frozen red. The sabotage control and the
normalizer-application contract refuse every hand-sanitized golden shape.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

EXIT_PASS = 0
EXIT_FAIL = 1

#: The declared journey's model, prompt, suite, and budget — the frozen
#: first-delegation conventions (issue #39: "mirroring
#: tests/e2e/test_first_delegation.py conventions").
MODEL = "openrouter/cohere/north-mini-code:free"
PROMPT = (
    "Create a file named AGENT_NOTE.txt at the repository root containing the "
    "single line: delegated work happened. Do not do anything else."
)
SUITE = f"{sys.executable} -m pytest -q -p no:cacheprovider"
HARNESS_TIMEOUT = 300
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
# suite passing is then proof the model's file reached the materialised tree.
NOTE_TEST = '''\
from pathlib import Path


def test_delegated_note_reached_the_materialised_tree() -> None:
    note = Path("AGENT_NOTE.txt")
    assert note.is_file(), "the delegated model created no AGENT_NOTE.txt"
    assert "delegated work happened" in note.read_text(encoding="utf-8")
'''


def clean_env(home: Path, credential: str | None = None) -> dict[str, str]:
    environment = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(REAL_REPO / "src"),
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


def harness_dir() -> Path:
    default = REAL_REPO.parents[0].parent / "ranex-harness"
    return Path(os.environ.get("RANEX_HARNESS_DIR", default))


@pytest.fixture(scope="module")
def bun() -> Path:
    executable = Path.home() / ".bun" / "bin" / "bun"
    if not executable.is_file():
        pytest.skip("bun toolchain not installed at ~/.bun/bin/bun")
    return executable


def build_target(tmp_path: Path) -> Path:
    """A committed governed repository the delegated model will work in."""

    target = tmp_path / "target"
    target.mkdir()
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", str(target)], check=True, env=clean_env(home)
    )
    git(target, "config", "user.email", "task-family@example.invalid", home=home)
    git(target, "config", "user.name", "Task Family Delegation", home=home)

    from ranex.foundation.signing import generate_keypair

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
    git(target, "branch", "-M", "main", home=home)
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


def golden_text(name: str) -> str:
    """Read the family golden, refusing its absence loudly.

    ``expected/delegation-diff.out`` is the implementation lane's artifact,
    captured from a real run of this exact journey (the diff piped through
    ``_prereqs.normalize_transcript``). A missing golden is this file's
    frozen red — the honest one — until that capture lands.
    """

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-059 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture below), pipe the diff through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


@dataclass
class DelegationJourney:
    """Everything the frozen tests consume from the one delegated journey."""

    base: Path
    task_id: str
    worktree: Path
    journal: Path
    base_suite: subprocess.CompletedProcess[str]
    delegated: subprocess.CompletedProcess[str]
    outcome: dict[str, object]
    diff: str
    judged: subprocess.CompletedProcess[str]


@pytest.fixture(scope="module")
def journey(
    tmp_path_factory: pytest.TempPathFactory,
    prereq_openrouter_key: None,
    prereq_harness_fork: None,
    bun: Path,
) -> DelegationJourney:
    """The one delegated journey: red-at-base first, then the real model."""

    base = tmp_path_factory.mktemp("task-family-delegation")
    home = base / "home"
    home.mkdir()
    target = build_target(base)
    journal = base / "journal.sqlite3"
    harness = harness_dir()
    wrapper = write_wrapper(base / "harness-wrapper.sh", bun, harness)
    credential = os.environ["OPENROUTER_API_KEY"]

    # SP-3's guarantee observed up front: the note test is red at the
    # dispatch base, so the recorded suite is discriminating by construction.
    base_suite = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
        cwd=str(target),
        capture_output=True,
        text=True,
        check=False,
        env=clean_env(home),
        timeout=300,
    )
    assert base_suite.returncode == 1, (
        "the note test must be red at the dispatch base — a base that "
        f"passes it cannot discriminate a no-diff model: {base_suite.stdout[-800:]}"
    )
    assert re.search(r"\b1 failed\b", base_suite.stdout), base_suite.stdout

    # A real provider flakes; a fresh task id per attempt because one
    # dispatch is one judgement (SP-2). The assertions are never retried
    # around; a persistent failure stays red.
    failures: list[str] = []
    delegated: subprocess.CompletedProcess[str] | None = None
    task_id = ""
    worktree = base / "worktree-unset"
    outcome_path = base / "outcome-unset.json"
    for attempt in range(1, ATTEMPTS + 1):
        task_id = f"T-TASK-FAMILY-DELEGATION-{attempt}"
        worktree = base / f"worktree-{attempt}"
        outcome_path = base / f"outcome-{attempt}.json"
        delegated = run_delegate(
            target=target,
            task_id=task_id,
            worktree=worktree,
            journal=journal,
            wrapper=wrapper,
            outcome=outcome_path,
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
            "the delegated run never completed against the live provider "
            f"within the ATTEMPTS={ATTEMPTS} budget:\n" + "\n".join(failures)
        )
    assert delegated is not None

    outcome = json.loads(outcome_path.read_text(encoding="utf-8").strip())
    commit = outcome["commit"]
    assert isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit)

    # The diff is reviewable against the journal's dispatch-record base,
    # never the worker's report.
    rows = Journal(journal).entries()
    dispatch = next(
        row
        for row in rows
        if row.get("type") == "task-dispatch" and row.get("task_id") == task_id
    )
    base_commit = dispatch["base_commit"]
    assert re.fullmatch(r"[0-9a-f]{40}", str(base_commit))
    diff = git(worktree, "diff", f"{base_commit}..{commit}", home=home)

    judged = run_judge(
        target=target,
        task_id=task_id,
        worktree=worktree,
        commit=commit,
        journal=journal,
        home=home,
    )

    return DelegationJourney(
        base=base,
        task_id=task_id,
        worktree=worktree,
        journal=journal,
        base_suite=base_suite,
        delegated=delegated,
        outcome=outcome,
        diff=diff,
        judged=judged,
    )


def test_golden_contract_delegation_diff() -> None:
    """The delegation golden's own contract, held on EVERY host (the
    confinement family's ungated precedent): it exists, it is a fixpoint of
    the one normalizer, and it carries the delegated work's real content —
    the prompt-fixed note line and the new-file diff structure, the bytes
    that survive the normalizer's path masking (``a/AGENT_NOTE.txt`` is
    masked to ``<REL-PATH>`` by the frozen grammar, so the note line is
    the journey's discriminating content) — so a hand-invented diff
    cannot pose as a capture. This is the file's ungated red at the
    freeze commit: the golden does not exist yet."""

    golden = golden_text("delegation-diff.out")
    assert "diff --git" in golden, golden
    assert "new file mode" in golden, golden
    assert "+delegated work happened" in golden, (
        "delegation-diff.out carries no delegated work: the prompt-fixed "
        "note line is the journey's real, normalization-surviving content "
        "— a golden without it is hand-sanitized text, not a captured diff"
    )
    assert "<REL-PATH>" in golden, (
        "delegation-diff.out carries no <REL-PATH> token: the diff's "
        "a/… b/… path slots are real volatile material the normalizer "
        "must have tamed"
    )
    assert _prereqs.normalize_transcript(golden) == golden, (
        "delegation-diff.out is not a normalizer fixpoint: it still "
        "contains bytes the frozen grammar would mask, which no capture "
        "piped through normalize_transcript can"
    )


def test_delegated_diff_matches_the_golden_and_proves_execution(
    journey: DelegationJourney,
) -> None:
    """C-4: a real non-empty diff, reviewable against the journal's
    dispatch-record base, byte-frozen against the golden; the
    kernel-recorded suite output proves execution — the note test that was
    red at base is green only through the model's real work reaching the
    materialised commit (SP-3), and the judgement is a CANDIDATE naming
    its missing claims with no PASS anywhere."""

    assert journey.delegated.returncode == EXIT_PASS, journey.delegated.stderr
    assert journey.outcome["task_id"] == journey.task_id
    assert journey.outcome["timed_out"] is False

    assert journey.diff.strip(), "the delegated commit produced an empty diff"
    assert "AGENT_NOTE.txt" in journey.diff, (
        f"reviewable diff names no delegated work:\n{journey.diff}"
    )
    _prereqs.compare_transcript(
        _prereqs.normalize_transcript(journey.diff),
        golden_text("delegation-diff.out"),
        family="delegation-diff",
    )

    tail = str(journey.outcome["suite_output_tail"])
    assert tail.strip(), "suite output is empty; nothing executed"
    assert journey.outcome["suite_exit"] == 0, (
        f"suite failed against the delegated tree:\n{tail}"
    )
    assert re.search(r"\b1 passed\b", tail), f"no evidence the suite ran tests:\n{tail}"
    assert re.search(r"\b1 failed\b", journey.base_suite.stdout)

    assert journey.judged.returncode == EXIT_FAIL, journey.judged.stderr
    assert "CANDIDATE" in journey.judged.stdout, journey.judged.stdout
    candidates = [
        row
        for row in Journal(journey.journal).entries()
        if row.get("type") == "task-candidate" and row.get("task_id") == journey.task_id
    ]
    assert len(candidates) == 1
    assert candidates[0]["missing_claims"] == ["tests-executed"], (
        "the candidate must name its missing claims — 'tests-executed' was "
        f"never evidenced, yet the journal says: "
        f"{candidates[0]['missing_claims']!r}"
    )

    assert "PASS" not in journey.delegated.stdout + journey.delegated.stderr
    assert "PASS" not in journey.judged.stdout
    assert not any(
        row.get("verdict") == "PASS" for row in Journal(journey.journal).entries()
    )
    assert Journal(journey.journal).verify() is True


def test_goldens_carry_real_volatile_material() -> None:
    """The golden is a machine-normalized capture, not hand-sanitized text:
    it is a fixpoint of the one normalizer carrying the model's real note
    content, and a golden holding altered content bytes provably cannot
    match — demonstrated by rewriting the note line inside the real golden
    and proving the comparison fails. Ungated (the golden itself is the
    real captured bytes; the journey is not needed for the discrimination).
    """

    name = "delegation-diff.out"
    golden = golden_text(name)
    assert _prereqs.normalize_transcript(golden) == golden
    doctored = golden.replace(
        "+delegated work happened", "+delegated work never happened", 1
    )
    assert doctored != golden, "the golden carries no note line to doctor"
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _prereqs.normalize_transcript(golden),
            doctored,
            family=name.removesuffix(".out"),
        )


def test_sabotage_control_mutated_golden_diffs_dirty() -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte of
    the expected file and the comparator must diff dirty, naming the family
    and carrying exactly the first differing hunk — never a bare
    ``assert False``. Ungated, with the golden itself as the actual bytes
    (a real captured diff), so the control runs green wherever the
    credential-gated journey skips — G-1's unset-credential run still
    exercises the red control once."""

    name = "delegation-diff.out"
    family = name.removesuffix(".out")
    golden = golden_text(name)
    verdict_word = "delegated work happened"
    assert verdict_word in golden, golden
    mutated = golden.replace(verdict_word, "Q" + verdict_word[1:], 1)
    with pytest.raises(AssertionError) as raised:
        _prereqs.compare_transcript(
            _prereqs.normalize_transcript(golden), mutated, family=family
        )
    message = str(raised.value)
    assert family in message, (
        f"the mismatch must name the golden family {family!r}: {message}"
    )
    assert "@@" in message, (
        "the mismatch must carry the first differing hunk header: " + message
    )
