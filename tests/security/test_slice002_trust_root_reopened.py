"""SLICE-002 reopened: the trust root, walked around rather than edited.

Written before the fix and required to fail first.

`refuse_uncommitted_trust_root` compares the file on disk against the bytes the
evaluated ref records for it — and when the ref records nothing for that path it
returns having compared nothing at all. The branch is deliberate and its
docstring argues for it: "there is no reviewed version to prefer, and taking one
out of the history is itself a commit a reviewer sees."

That reasoning holds only for a path the OPERATOR chose. The party being gated
chooses it too. It writes `attacker-gates.yaml`, or drops a keyring under a
directory a committed `.gitignore` hides, or commits a symlink whose name HEAD
carries and whose target no commit does — and every one of them lands on the
`return` above. The check that was supposed to make review the control on the
trust root is skipped by the one input the attacker fully controls: the path.

The required behaviour is the narrow one. A `--gate-catalog` or a `--producers`
naming a file the evaluated ref does not carry is REFUSED: exit 2, no verdict
reached, nothing written to the journal. The trust root is the committed path
itself, not whatever bytes happen to sit at a name that resembles one.

The sixth test is a control. A fix that refuses every path passes all five
attacks and breaks the product, and that failure would be invisible without it.

Tests 7 to 9 were appended after two independent audits found the check has a
second way around it, and this one needs no unusual path at all. The comparison
`refuse_uncommitted_trust_root` makes is against bytes it reads and then throws
away: it returns, and every loader afterwards re-opens the same name. The bytes
that were checked and the bytes that decide the verdict are two separate reads
of a name the observed party controls, so replacing the file between them
decides the verdict with bytes nothing verified. The ninth test is their
control, and it earns its place: it must prove the harness those two tests use
is not itself what broke the run.

Imports of `ranex` are deliberately deferred into fixtures and test bodies. A
module-level import of a symbol a fix has not created yet is a collection error,
and a collection error takes the whole suite down with it — hiding the very
tests that prove nothing else regressed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from ranex.foundation.canonical import command_digest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

# The committed tree fails its own check. Every attack below is a way of getting
# a PASS recorded against this tree anyway.
COMMITTED_ANSWER = "wrong\n"
PASSING_ANSWER = "right\n"
CHECK_SCRIPT = "grep -qx right answer.txt\n"

# SLICE-003: a claim declares the command that satisfies it. `check.sh` is the
# repository's own check, so `tests-executed` means running it and nothing else.
# `trivial` is bound to a command that succeeds against any tree — it is the
# claim every catalog-substitution attack below tries to smuggle in.
COMMAND_FOR: dict[str, list[str]] = {
    "tests-executed": ["sh", "check.sh"],
    "trivial": ["sh", "-c", "exit 0"],
}

# The resolved absolute path of argv[0], as `run` records it (ADR-001). Outside
# the repository under test, which is the containment rule these records obey.
EXECUTABLE = str(Path(shutil.which("sh")).resolve())

# Names HEAD is never made to carry. The whole attack is that the trust-root
# check has nothing to compare them against and says so by saying nothing.
UNCARRIED_CATALOG = "attacker-gates.yaml"
UNCARRIED_KEYRING = "attacker-producers.yaml"
HIDDEN_KEYRING = ".cache/producers.yaml"
SYMLINK_TARGET = "generated-gates.yaml"


def build_gates(*claims: str) -> str:
    entries = "".join(
        f"      - claim_id: {claim}\n"
        f"        command: {json.dumps(COMMAND_FOR[claim])}\n"
        for claim in claims
    )
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n" + entries
    )


@dataclass
class Keys:
    """Producer keys, kept outside the repository under test."""

    root: Path
    private: dict[str, str] = field(default_factory=dict)
    public: dict[str, str] = field(default_factory=dict)

    def path(self, producer: str) -> Path:
        return self.root / f"{producer}.key"


@pytest.fixture()
def keys(tmp_path: Path) -> Keys:
    from ranex.foundation.signing import generate_keypair

    root = tmp_path / "keys"
    root.mkdir(parents=True, exist_ok=True)
    bundle = Keys(root=root)
    for producer in ("worker", "mallory"):
        private_key, public_key = generate_keypair()
        bundle.private[producer] = private_key
        bundle.public[producer] = public_key
        path = bundle.path(producer)
        path.write_text(private_key + "\n", encoding="utf-8")
        path.chmod(0o600)
    return bundle


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """A repository whose own check FAILS on the tree as committed."""

    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "answer.txt").write_text(COMMITTED_ANSWER, encoding="utf-8")
    (repository / "check.sh").write_text(CHECK_SCRIPT, encoding="utf-8")
    (repository / "gates.yaml").write_text(
        build_gates("tests-executed"), encoding="utf-8"
    )
    return repository


def invoke(repo: Path, argv: list[str], key_path: Path | None = None) -> int:
    from ranex.cli.main import main

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


def commit_all(repo: Path, message: str = "initial") -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", message], check=True)


def keyring_text(**producers: str) -> str:
    """The bytes a keyring holds, without writing one anywhere.

    Separate from `write_keyring` because the swap harness below needs the
    content and must not put it on disk until it is standing inside the window.
    """

    lines = "\n".join(f"  {name}: {key}" for name, key in producers.items())
    return f"producers:\n{lines}\n"


def write_keyring(repo: Path, path: str = "producers.yaml", **producers: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(keyring_text(**producers), encoding="utf-8")


def git_output(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def subject_digest(repo: Path, ref: str = "HEAD") -> str:
    from ranex.foundation.canonical import canonical_sha256

    tree = git_output(repo, "rev-parse", f"{ref}^{{tree}}").strip()
    return "sha256:" + canonical_sha256({"tree": tree})


def check_passes(repo: Path) -> bool:
    """Does the tree on disk right now satisfy its own check?"""

    return subprocess.run(
        ["sh", "check.sh"], cwd=repo, capture_output=True, check=False
    ).returncode == 0


def signed(content: dict[str, object], private_key: str) -> dict[str, object]:
    from ranex.foundation.signing import sign_evidence

    return {**content, "signature": sign_evidence(content, private_key)}


def record(
    *,
    claim: str,
    digest: str,
    producer: str,
    exit_code: int = 0,
    argv: list[str] | None = None,
) -> dict[str, object]:
    """A record body describing the command the claim names (SLICE-003)."""

    command = argv if argv is not None else COMMAND_FOR[claim]
    return {
        "claim_id": claim,
        "subject_digest": digest,
        "producer_id": producer,
        "command": " ".join(command),
        "command_digest": command_digest(command),
        "executable_path": EXECUTABLE,
        "exit_code": exit_code,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }


def write_evidence(repo: Path, records: list[dict[str, object]]) -> None:
    (repo / "evidence.json").write_text(
        json.dumps(records, indent=2) + "\n", encoding="utf-8"
    )


def run_cmd(
    repo: Path,
    key_path: Path | None,
    *command: str,
    claim: str = "tests-executed",
    producer: str = "worker",
) -> int:
    return invoke(
        repo,
        [
            "run",
            "--claim", claim,
            "--producer", producer,
            "--repository", ".",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--", *command,
        ],
        key_path,
    )


def evaluate(
    repo: Path,
    *,
    catalog: str = "gates.yaml",
    producers: str = "producers.yaml",
    approver: str = "reviewer",
) -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", catalog,
            "--evidence", "evidence.json",
            "--producers", producers,
            "--approver", approver,
        ],
    )


def verdict_lines(output: str) -> list[str]:
    """Every line on which the CLI announced a verdict.

    A refusal must reach none of them. Exit 2 with a PASS already printed would
    be a verdict an operator has seen and a script may already have acted on.
    """

    return [
        line
        for line in output.splitlines()
        if line.startswith("PASS  gate=") or line.startswith("FAIL  gate=")
    ]


# --- 1. a catalog at a name no commit carries -------------------------------


def test_gate_catalog_at_an_uncarried_path_is_refused(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: do not edit the goalposts — bring your own, under a new name.

    Editing the committed catalog is caught: the bytes on disk differ from the
    bytes HEAD records and the run is refused. So the attacker does not edit it.
    It writes `attacker-gates.yaml`, a file HEAD carries no entry for at all, and
    passes `--gate-catalog attacker-gates.yaml`. `committed_bytes` asks git for
    `HEAD:attacker-gates.yaml`, git has nothing, and the trust-root check returns
    without comparing anything. The catalog that decides this verdict was written
    by the party the verdict is about, seconds ago, and reviewed by nobody.

    The evidence here is entirely honest: `run` produced it, a registered
    producer signed it, and it truthfully reports a trivial command exiting 0.
    Only the question changed. "The coordinates are fixed before any throw and
    approved by whoever owns the target" is the project's first claim, and a
    catalog path the implementer chooses at scoring time makes it decoration —
    the journal then preserves the substitute as if it had been the policy.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    assert not check_passes(repo), (
        "the committed tree must fail its own check, or this test proves nothing"
    )

    # Honest work, for a claim the committed gate does not require.
    assert run_cmd(
        repo, keys.path("worker"), "sh", "-c", "exit 0", claim="trivial"
    ) == EXIT_PASS, "the honest observation this attack reuses must be recorded"
    assert evaluate(repo) != EXIT_PASS, (
        "the committed gate must not already be satisfied, or the flip below "
        "proves nothing"
    )

    (repo / UNCARRIED_CATALOG).write_text(build_gates("trivial"), encoding="utf-8")
    assert git_output(repo, "ls-tree", "HEAD", UNCARRIED_CATALOG).strip() == "", (
        f"HEAD must carry no {UNCARRIED_CATALOG}, or the defect under test is "
        "not the one being exercised"
    )

    capsys.readouterr()
    code = evaluate(repo, catalog=UNCARRIED_CATALOG)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_USAGE, (
        "a gate catalog HEAD does not carry decided this verdict; the party "
        f"being gated wrote the file that says what the gate demands: {output}"
    )
    assert verdict_lines(output) == [], (
        "a verdict was announced from an unreviewed gate catalog: " + output
    )


# --- 2. a keyring at a name no commit carries -------------------------------


def test_producer_keyring_at_an_uncarried_path_is_refused(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: self-register as a producer in a file nobody ever reviewed.

    The keyring answers one question — which keys does this repository trust —
    and every other control is downstream of it. Appending a line to the
    committed keyring is caught. So the attacker writes a whole keyring at
    `attacker-producers.yaml`, a name HEAD carries nothing for, generates its own
    Ed25519 keypair, registers the public half, signs a record with the private
    half, and names the file with `--producers`. No key was stolen and no
    signature was broken: the attacker simply chose which signatures count.

    `run` refuses to sign for a producer the keyring does not hold, which reads
    as protection until you notice the keyring is an argument. Every downstream
    guarantee — one key one producer, no self-approval, admission itself — is
    computed against whichever file this flag names.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    forged = signed(
        record(
            claim="tests-executed",
            digest=subject_digest(repo),
            producer="mallory",
        ),
        keys.private["mallory"],
    )
    write_evidence(repo, [forged])

    assert evaluate(repo) != EXIT_PASS, (
        "mallory must be unregistered in the committed keyring, or this test "
        "proves nothing"
    )

    write_keyring(repo, UNCARRIED_KEYRING, mallory=keys.public["mallory"])
    assert git_output(repo, "ls-tree", "HEAD", UNCARRIED_KEYRING).strip() == "", (
        f"HEAD must carry no {UNCARRIED_KEYRING}, or the defect under test is "
        "not the one being exercised"
    )

    capsys.readouterr()
    code = evaluate(repo, producers=UNCARRIED_KEYRING)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_USAGE, (
        "a keyring HEAD does not carry admitted a producer nobody registered; "
        f"the attacker chose which keys this repository trusts: {output}"
    )
    assert verdict_lines(output) == [], (
        "a verdict was announced from an unreviewed keyring: " + output
    )


# --- 3. the same attack, invisible to `git status` --------------------------


def test_gitignored_producer_keyring_is_refused(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: hide the substitute keyring behind a committed `.gitignore`.

    An untracked file at least shows up as `??` in `git status`. This one does
    not. A `.gitignore` line as unremarkable as `.cache/` is committed in
    ordinary work, and the attacker's keyring goes under it — so the single
    signal an operator actually watches reports a completely clean tree while an
    unreviewed file decides which producers exist.

    This is the same defect as the previous test with its last excuse removed.
    The comment in `refuse_uncommitted_trust_root` reasons that taking a
    trust-root file out of the history "is itself a commit a reviewer sees";
    nothing is taken out here, nothing is added to the history, and there is
    nothing for a reviewer to see. `private_signing_key` already refuses a key
    inside the tree for exactly this reason — that a `.gitignore` entry keeps
    `git status` clean so nothing else notices. The keyring deserves the same
    suspicion.
    """

    write_keyring(repo, worker=keys.public["worker"])
    (repo / ".gitignore").write_text(
        ".cache/\nevidence.json\ngovernance/\n", encoding="utf-8"
    )
    commit_all(repo)

    write_evidence(
        repo,
        [
            signed(
                record(
                    claim="tests-executed",
                    digest=subject_digest(repo),
                    producer="mallory",
                ),
                keys.private["mallory"],
            )
        ],
    )
    write_keyring(repo, HIDDEN_KEYRING, mallory=keys.public["mallory"])

    # The door, stated as fact: the tree an operator inspects is spotless.
    assert git_output(repo, "status", "--porcelain", "-uall").strip() == "", (
        "the attack must leave no trace in `git status`, or it is not the "
        "attack this test describes"
    )
    assert (repo / HIDDEN_KEYRING).is_file(), (
        "the hidden keyring must exist on disk while git reports nothing"
    )

    capsys.readouterr()
    code = evaluate(repo, producers=HIDDEN_KEYRING)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_USAGE, (
        "a gitignored keyring admitted a producer nobody registered, and the "
        f"working tree an operator inspects was clean throughout: {output}"
    )
    assert verdict_lines(output) == [], (
        "a verdict was announced from a keyring hidden by .gitignore: " + output
    )


# --- 4. a committed name, uncommitted bytes ---------------------------------


def test_committed_symlink_to_an_uncarried_catalog_is_refused(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: commit the name, and let the bytes arrive later.

    `gates.yaml` is committed as a symlink to `generated-gates.yaml`, a path no
    commit carries. The operator then runs the ordinary invocation naming the
    ordinary path: HEAD carries `gates.yaml`, `git status` reports it unmodified,
    and everything visible says the reviewed catalog is in use.

    Two different files are involved and the question is which one each half of
    the check sees. `resolve_within_repository` resolves the link first, so
    `committed_bytes` is asked about `generated-gates.yaml` and git has nothing —
    the trust-root check returns having compared nothing. What loads is the
    attacker's file. The bytes HEAD actually records for `gates.yaml` are the
    link text `generated-gates.yaml`, which is not a gate catalog at all: there
    is no reading of this repository under which the reviewed content decided
    the verdict.

    Committing the indirection once buys the ability to rewrite policy forever
    afterwards without another commit. Whatever the fix does with it, it must not
    reach a PASS.
    """

    write_keyring(repo, worker=keys.public["worker"])
    (repo / "gates.yaml").unlink()
    (repo / "gates.yaml").symlink_to(SYMLINK_TARGET)
    commit_all(repo)

    entry = git_output(repo, "ls-tree", "HEAD", "gates.yaml").strip()
    assert entry.startswith("120000"), (
        f"HEAD must carry gates.yaml as a symlink for this attack: {entry!r}"
    )
    assert "gates:" not in git_output(repo, "show", "HEAD:gates.yaml"), (
        "the bytes HEAD records for gates.yaml must be link text and not a "
        "catalog, which is the whole point of this test"
    )

    # Symlinks are not a materialised entry type, so observation now refuses first.
    capsys.readouterr()
    run_code = run_cmd(
        repo, keys.path("worker"), "sh", "-c", "exit 0", claim="trivial"
    )
    run_output = capsys.readouterr()
    assert run_code == EXIT_USAGE
    assert "unimplemented tree entry" in (run_output.out + run_output.err)
    assert "gates.yaml" in (run_output.out + run_output.err)
    assert not (repo / "evidence.json").exists(), "nothing may be recorded"

    (repo / SYMLINK_TARGET).write_text(build_gates("trivial"), encoding="utf-8")
    assert git_output(repo, "status", "--porcelain", "gates.yaml").strip() == "", (
        "the committed name must read as unmodified, or the operator would see "
        "the attack in the ordinary signal"
    )

    capsys.readouterr()
    code = evaluate(repo)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_USAGE, (
        "a committed symlink delivered an uncommitted gate catalog to the "
        f"verdict; the name was reviewed and the bytes never were: {output}"
    )
    assert not any(line.startswith("PASS  gate=") for line in output.splitlines()), (
        "the gate PASSed on a catalog no commit carries: " + output
    )


# --- 5. the committed path, spelled differently -----------------------------


def test_a_path_normalising_onto_a_committed_path_is_still_the_trust_root(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: spell the path so a string comparison stops recognising it.

    A fix that decides "is this the trust root" by comparing the text of the
    argument against the text of a committed path is defeated by a redundant
    component. `./nested/../gates.yaml` is `gates.yaml` — the same inode, the
    same blob in HEAD — and `./nested/../attacker-gates.yaml` is still a file no
    commit carries. Both must be judged by where the path lands, never by how it
    was typed.

    Two halves, and they fail differently today. Tampering under the redundant
    spelling is already caught, because resolution normalises before the check
    runs; that half is here so a fix cannot regress it while closing the other.
    The second half is the open defect wearing a disguise: the uncarried catalog
    of the first test, reached by a path that walks through a directory HEAD does
    carry. A refusal that can be spelled around is not a refusal.
    """

    write_keyring(repo, worker=keys.public["worker"])
    (repo / "nested").mkdir()
    (repo / "nested" / "keep.txt").write_text("keep\n", encoding="utf-8")
    commit_all(repo)

    assert run_cmd(
        repo, keys.path("worker"), "sh", "-c", "exit 0", claim="trivial"
    ) == EXIT_PASS, "the honest observation this attack reuses must be recorded"

    # Half one: the committed catalog, tampered with, named the long way round.
    (repo / "gates.yaml").write_text(build_gates("trivial"), encoding="utf-8")
    assert git_output(repo, "status", "--porcelain", "gates.yaml").strip(), (
        "the catalog edit must be uncommitted, or this half proves nothing"
    )

    capsys.readouterr()
    tampered_code = evaluate(repo, catalog="./nested/../gates.yaml")
    tampered_output = "".join(capsys.readouterr())

    assert tampered_code == EXIT_USAGE, (
        "a redundant path component made an uncommitted edit to the committed "
        f"gate catalog decide the verdict: {tampered_output}"
    )
    assert verdict_lines(tampered_output) == [], (
        "a verdict was announced from a tampered catalog named the long way "
        "round: " + tampered_output
    )

    # Half two: the uncarried catalog, reached through a committed directory.
    subprocess.run(["git", "-C", str(repo), "checkout", "--", "gates.yaml"], check=True)
    (repo / UNCARRIED_CATALOG).write_text(build_gates("trivial"), encoding="utf-8")

    capsys.readouterr()
    substituted_code = evaluate(repo, catalog=f"./nested/../{UNCARRIED_CATALOG}")
    substituted_output = "".join(capsys.readouterr())

    assert substituted_code == EXIT_USAGE, (
        "a catalog HEAD does not carry decided the verdict when it was named "
        f"through a committed directory: {substituted_output}"
    )
    assert verdict_lines(substituted_output) == [], (
        "a verdict was announced from an unreviewed catalog named the long way "
        "round: " + substituted_output
    )


# --- 6. the control: the product must still work ----------------------------


def test_committed_catalog_and_keyring_still_reach_a_pass(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Control: the ordinary, honest run must still PASS.

    Everything above is refused because the file that decided the verdict was
    not the file the ref carries. Here it is: the catalog is committed and
    unmodified, the keyring is committed and unmodified, a registered producer
    ran the gate's own bound command against a clean tree that genuinely passes
    it, and a different identity approves.

    Refusing every path also refuses this, and would satisfy all five attacks
    above while leaving nothing that can ever be landed. A gate that can never
    PASS is exactly as useless as one that can never FAIL — it just fails in the
    direction that looks responsible.
    """

    (repo / "answer.txt").write_text(PASSING_ANSWER, encoding="utf-8")
    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    assert check_passes(repo), (
        "the committed tree must pass its own check, or this control cannot "
        "reach a PASS for honest reasons"
    )

    assert run_cmd(repo, keys.path("worker"), "sh", "check.sh") == EXIT_PASS, (
        "the gate's own bound command must be observed succeeding"
    )

    capsys.readouterr()
    code = evaluate(repo)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_PASS, (
        "the committed trust root no longer reaches a PASS; a refusal that "
        f"refuses everything is not a control, it is an outage: {output}"
    )
    assert any(line.startswith("PASS  gate=") for line in output.splitlines()), (
        "the PASS verdict must be announced to the operator: " + output
    )


# --- the window between the byte that is checked and the byte that decides ---


def swap_inside_the_window(
    monkeypatch: pytest.MonkeyPatch,
    repo: Path,
    replacements: dict[str, str],
) -> list[str]:
    """Rewrite `replacements` on disk exactly once, from inside `gate evaluate`.

    `refuse_uncommitted_trust_root` reads the file, compares it against the
    bytes the ref records, and returns — and the bytes it read are then thrown
    away. Every loader afterwards re-opens the same path BY NAME. So there are
    two reads of a name the observed party owns, and this hook stands between
    them: the evidence load runs after both trust-root checks and before either
    the keyring or the catalog is opened, verified by tracing an ordinary
    evaluation, which touches them in the order

        trust-root check (keyring), trust-root check (catalog), evidence,
        keyring, catalog.

    Deterministic and not threaded, the same technique as
    `test_the_file_that_runs_is_the_file_containment_cleared`. A racing test
    would be flaky and would prove strictly less: it would show that the window
    is sometimes wide enough, where this shows that the window exists at all.
    The hook fires once, writes the files and delegates to the real function, so
    nothing else about the run changes.

    Returns the log of entries. A hook that quietly stopped firing — because a
    fix moved the evidence load, or renamed it — would turn every test using it
    green while proving nothing, so each caller asserts it fired.
    """

    import ranex.cli.main as cli

    real_load_records = cli.load_records
    entered: list[str] = []

    def swap_then_load(path: Path) -> list[object]:
        if not entered:
            entered.append(str(path))
            for relative, content in replacements.items():
                (repo / relative).write_text(content, encoding="utf-8")
        return real_load_records(path)

    monkeypatch.setattr("ranex.cli.main.load_records", swap_then_load)
    return entered


# --- 7. the catalog, replaced after it was checked --------------------------


def test_a_catalog_swapped_after_the_check_does_not_decide_the_verdict(
    repo: Path,
    keys: Keys,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: let the check read the reviewed catalog, then replace it.

    Nothing unusual is named here. The operator types the ordinary invocation
    against the ordinary committed path, and the trust-root check does exactly
    what it was written to do: it reads `gates.yaml`, finds it byte-identical to
    what HEAD records, and returns satisfied. Then it drops the bytes it read.
    The catalog is opened a second time, by name, to decide the verdict — and a
    worker sharing the uid owns that file between the two reads.

    So the committed catalog requires `tests-executed`, bound to this
    repository's own check, and the tree genuinely fails it. Inside the window
    the file becomes a catalog requiring only `trivial` — the claim the attacker
    already holds honest, signed, correctly bound evidence for. Nothing is
    forged: the evidence is true, and the question was changed after it was
    asked. The journal then records the substitute as the policy that decided
    this landing.

    A check whose result can be invalidated before it is used is not a check, it
    is a delay. The required property is stated without naming a mechanism: once
    the trust-root check has passed, replacing the catalog on disk must not
    change the verdict, and the verdict must be the one the committed bytes
    produce. Reading both out of the ref and never touching the working tree is
    the obvious way there, and this test is written not to require it.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    assert not check_passes(repo), (
        "the committed tree must fail its own check, or this test proves nothing"
    )

    # Honest work, for a claim the committed gate does not require. The attacker
    # never needs a forgery — only a different question.
    assert run_cmd(
        repo, keys.path("worker"), "sh", "-c", "exit 0", claim="trivial"
    ) == EXIT_PASS, "the honest observation this attack reuses must be recorded"

    committed_catalog = git_output(repo, "show", "HEAD:gates.yaml")
    assert "tests-executed" in committed_catalog, (
        "HEAD must require the claim this tree fails, or the flip below proves "
        "nothing"
    )
    assert evaluate(repo) == EXIT_FAIL, (
        "the committed catalog must FAIL this tree before the swap, or there is "
        "no verdict for the swap to change"
    )

    entered = swap_inside_the_window(
        monkeypatch, repo, {"gates.yaml": build_gates("trivial")}
    )

    capsys.readouterr()
    code = evaluate(repo)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert entered, (
        "the evidence load never ran, so the catalog was never replaced and "
        "this test exercised nothing"
    )
    assert (repo / "gates.yaml").read_text(encoding="utf-8") != committed_catalog, (
        "the catalog on disk must differ from the committed one by the time the "
        "verdict is announced, or the substitution never happened"
    )

    assert not any(line.startswith("PASS  gate=") for line in output.splitlines()), (
        "a gate catalog written after the trust-root check had passed decided "
        "this verdict; the checked bytes and the deciding bytes were two "
        f"separate reads of one name: {output}"
    )
    assert code == EXIT_FAIL, (
        "the verdict was not the one the committed catalog produces. The tree "
        "fails the claim HEAD requires, and that is the only verdict a reviewed "
        f"catalog can reach for it: {output}"
    )


# --- 8. the keyring, replaced after it was checked --------------------------


def test_a_keyring_swapped_after_the_check_does_not_admit_a_record(
    repo: Path,
    keys: Keys,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: the same window, aimed at which keys this repository trusts.

    The committed keyring registers `worker` and nobody else. Mallory generates
    an Ed25519 keypair, signs a record claiming `tests-executed` succeeded
    against this exact tree, and leaves the committed keyring untouched — the
    trust-root check reads it, agrees with HEAD byte for byte, and returns. Then
    the keyring is opened again, by name, and mallory's own registration is
    sitting in it.

    No key was stolen and no signature was broken. The attacker chose which
    signatures count, after the moment that was supposed to decide it. Every
    control downstream of the keyring — one key one producer, no self-approval,
    admission itself — is computed against whatever file that second read finds.

    The committed keyring must be what decides, so mallory's record must be
    refused and named. Asserted on what the operator can see: no PASS, and a
    refusal that names the record a human has to open.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    write_evidence(
        repo,
        [
            signed(
                record(
                    claim="tests-executed",
                    digest=subject_digest(repo),
                    producer="mallory",
                ),
                keys.private["mallory"],
            )
        ],
    )

    assert evaluate(repo) != EXIT_PASS, (
        "mallory must be unregistered in the committed keyring, or this test "
        "proves nothing"
    )

    entered = swap_inside_the_window(
        monkeypatch,
        repo,
        {"producers.yaml": keyring_text(mallory=keys.public["mallory"])},
    )

    capsys.readouterr()
    code = evaluate(repo)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert entered, (
        "the evidence load never ran, so the keyring was never replaced and "
        "this test exercised nothing"
    )
    assert "mallory" in (repo / "producers.yaml").read_text(encoding="utf-8"), (
        "the keyring on disk must register mallory by the time admission runs, "
        "or the substitution never happened"
    )

    assert not any(line.startswith("PASS  gate=") for line in output.splitlines()), (
        "a keyring written after the trust-root check had passed admitted a "
        "producer the committed keyring never registered, and the gate PASSed "
        f"on that producer's word: {output}"
    )
    assert code != EXIT_PASS, (
        "an unreviewed keyring decided this verdict: " + output
    )
    assert "REFUSED record 0" in output and "mallory" in output, (
        "mallory's record must be refused and named. The committed keyring does "
        "not register mallory, and the committed keyring is the one that "
        f"decides; a record admitted on a swapped keyring is not evidence: {output}"
    )


# --- 9. the control: the harness must not be what breaks the run ------------


def test_the_swap_harness_alone_does_not_disturb_an_honest_pass(
    repo: Path,
    keys: Keys,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Control: the same harness, swapping nothing, must still reach a PASS.

    The two tests above conclude "no PASS" from a run made under a patched
    evidence load. If that patch were what suppressed the PASS — a signature
    that no longer matched, records silently dropped, an exception swallowed
    into exit 2 — both would pass for a reason that has nothing to do with the
    defect, and would keep passing after a fix that fixed nothing.

    So: the identical harness, installed the identical way, entering the window
    the identical number of times, with an empty set of replacements. Everything
    else is the honest run — committed catalog, committed keyring, a registered
    producer that ran the gate's own bound command against a tree that genuinely
    passes it, and a different identity approving. If this does not PASS, the
    two tests above are measuring the harness and not the product.

    `test_committed_catalog_and_keyring_still_reach_a_pass` covers the plain
    case, and covers a different thing: that a fix has not refused the world.
    This one covers the instrument.
    """

    (repo / "answer.txt").write_text(PASSING_ANSWER, encoding="utf-8")
    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    assert check_passes(repo), (
        "the committed tree must pass its own check, or this control cannot "
        "reach a PASS for honest reasons"
    )
    assert run_cmd(repo, keys.path("worker"), "sh", "check.sh") == EXIT_PASS, (
        "the gate's own bound command must be observed succeeding"
    )

    entered = swap_inside_the_window(monkeypatch, repo, {})

    capsys.readouterr()
    code = evaluate(repo)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert entered, (
        "the harness never fired, so it is not the harness the two tests above "
        "run under and this control vouches for nothing"
    )
    assert code == EXIT_PASS, (
        "the swap harness suppressed an honest PASS while swapping nothing at "
        "all; the two tests above would then hold for a reason unrelated to the "
        f"trust root: {output}"
    )
    assert any(line.startswith("PASS  gate=") for line in output.splitlines()), (
        "the PASS verdict must be announced to the operator: " + output
    )
