"""Five audited defects: the tree under observation, and the trust root itself.

Written before the fixes and required to fail first.

They divide into three families, and each family is one way the paint reaches
the board after the dart has landed:

1. `run` binds a record to HEAD's tree but only re-checks HEAD afterwards. A
   command that edits tracked files, runs, and puts them back — or a file hidden
   from `git status` with `--skip-worktree` — is observed against a tree that is
   not the tree the digest names.
2. `gate evaluate` reads the keyring and the gate catalog out of the WORKING
   tree. Both are the trust root. An uncommitted edit to either decides a
   verdict, and review never sees it.
3. The report collapses two different events. A record refused without a usable
   `claim_id`, and a keyring that crashes the loader instead of refusing, both
   arrive at the operator wearing the wrong clothes.

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
# `trivial` is deliberately bound to a command that succeeds against any tree —
# it is the claim the catalog-tampering attack below tries to smuggle in.
COMMAND_FOR: dict[str, list[str]] = {
    "tests-executed": ["sh", "check.sh"],
    "trivial": ["sh", "-c", "exit 0"],
}

# The resolved absolute path of argv[0], as `run` records it (ADR-001). Outside
# the repository under test, which is the containment rule these records obey.
EXECUTABLE = str(Path(shutil.which("sh")).resolve())


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


def write_keyring(repo: Path, **producers: str) -> None:
    lines = "\n".join(f"  {name}: {key}" for name, key in producers.items())
    (repo / "producers.yaml").write_text(f"producers:\n{lines}\n", encoding="utf-8")


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


# --- 1. the observed tree is not the tree the digest names ------------------


def test_run_refuses_a_command_that_edits_and_reverts_the_tree(
    repo: Path,
    keys: Keys,
) -> None:
    """Attack: paint the bullseye, throw the dart, wipe the paint.

    `run` refuses a dirty tree BEFORE the command and re-checks only HEAD after
    it. HEAD is the one thing this attack never touches. The command writes the
    answer the check wants, runs the check, restores the committed content, and
    exits with the check's status — so `run` records exit=0 bound to HEAD's
    digest, and `gate evaluate` then PASSes a tree whose own tests fail.

    This is the project's founding failure in one shell command: the score is
    computed against a board that existed only while nobody was looking. The
    subject digest is the whole guarantee — evidence that does not describe the
    tree it names is worth less than no evidence, because it blocks nothing and
    reads as proof.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    assert not check_passes(repo), (
        "the committed tree must fail its own check, or this test proves nothing"
    )

    attack = (
        "printf 'right\\n' > answer.txt\n"   # paint the bullseye
        "sh check.sh; status=$?\n"           # throw the dart
        "printf 'wrong\\n' > answer.txt\n"   # wipe the paint off the board
        "exit $status\n"                     # report the score anyway
    )
    code = run_cmd(repo, keys.path("worker"), "sh", "-c", attack)

    # The attack put everything back: HEAD never moved, the tree is
    # byte-identical to HEAD, and it still fails.
    assert (repo / "answer.txt").read_text(encoding="utf-8") == COMMITTED_ANSWER
    assert not check_passes(repo)

    assert code == EXIT_USAGE, (
        "`run` recorded a passing observation of a tree that only existed "
        "during the command; the tree it named still fails its own check"
    )
    assert not (repo / "evidence.json").exists(), (
        "evidence was written for a subject digest that does not describe what "
        "was observed"
    )


def test_run_refuses_a_skip_worktree_modification(repo: Path, keys: Keys) -> None:
    """Attack: the same lie, told to `git status` instead of to the clock.

    `git update-index --skip-worktree answer.txt` tells git to assume the file
    matches the index and stop stat-ing it. `git status --porcelain` then reports
    a clean tree while the file on disk differs from HEAD — permanently, with no
    race to win and nothing to restore afterwards.

    `run`'s only defence against "the digest does not describe the tree" is that
    porcelain output. One plumbing command disables it, and every record `run`
    writes from then on is bound to a tree that is not on disk. A cleanliness
    check that the observed party can switch off is not a check.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    subprocess.run(
        ["git", "-C", str(repo), "update-index", "--skip-worktree", "answer.txt"],
        check=True,
    )
    (repo / "answer.txt").write_text(PASSING_ANSWER, encoding="utf-8")

    # The door, stated as fact: porcelain is empty, HEAD disagrees with disk.
    assert git_output(repo, "status", "--porcelain").strip() == "", (
        "skip-worktree no longer hides the change; the attack has moved"
    )
    assert git_output(repo, "show", "HEAD:answer.txt") != (
        repo / "answer.txt"
    ).read_text(encoding="utf-8")
    assert check_passes(repo), "the hidden edit is what makes the check pass"

    code = run_cmd(repo, keys.path("worker"), "sh", "check.sh")

    assert code == EXIT_USAGE, (
        "`run` bound a passing observation to HEAD's digest while a tracked "
        "file on disk differed from HEAD, hidden by skip-worktree"
    )
    assert not (repo / "evidence.json").exists(), (
        "evidence was written against a tree that is not the tree it names"
    )


# --- 2. the trust root is read from the working tree ------------------------


def test_uncommitted_keyring_entry_cannot_admit_evidence(
    repo: Path,
    keys: Keys,
) -> None:
    """Attack: register yourself as a producer without ever committing it.

    `cmd_gate_evaluate` reads `producers.yaml` from the WORKING tree with no
    cleanliness check. The keyring is the trust root, and the module that loads
    it says so in its first line: it is committed *so that review is the control
    on it*. Reading it from disk removes that control entirely — an attacker
    appends one line, signs a record with the matching private key, and the gate
    admits it. Nothing is committed, so nothing is reviewed, and `git diff`
    showing an unstaged edit to the keyring is a fact no verdict consults.

    No-self-approval, one-key-one-producer, and every signature check are
    downstream of "which keys does this repository trust". If that answer comes
    from an uncommitted file, an attacker chooses it.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    keyring_path = repo / "producers.yaml"
    keyring_path.write_text(
        keyring_path.read_text(encoding="utf-8")
        + f"  mallory: {keys.public['mallory']}\n",
        encoding="utf-8",
    )
    assert git_output(repo, "status", "--porcelain", "producers.yaml").strip(), (
        "the keyring edit must be uncommitted, or this test proves nothing"
    )

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
        "an uncommitted line in the keyring made an unregistered producer's "
        "record count; the trust root was chosen by the attacker"
    )


def test_uncommitted_gate_catalog_cannot_decide_a_verdict(
    repo: Path,
    keys: Keys,
) -> None:
    """Attack: move the goalposts in the working tree, then take the shot.

    The gate catalog is read from disk with the same absence of a cleanliness
    check. Here nothing is forged: the record is produced by `run`, signed by a
    registered producer, and honestly reports a trivial command exiting 0. The
    only thing that changes between FAIL and PASS is an uncommitted edit to
    `required_claims`, rewriting the gate to demand exactly what the attacker
    already has.

    "The coordinates are fixed before any throw and approved by whoever owns the
    target" is the project's first claim. A catalog an implementer can edit
    between the throw and the scoring makes that claim decorative — and the
    catalog digest recorded in the journal preserves the edit as if it had been
    the policy all along.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    # Honest work, for a claim the committed gate does not require.
    assert run_cmd(
        repo, keys.path("worker"), "sh", "-c", "exit 0", claim="trivial"
    ) == EXIT_PASS
    assert evaluate(repo) != EXIT_PASS, (
        "the committed gate must not already be satisfied"
    )

    (repo / "gates.yaml").write_text(build_gates("trivial"), encoding="utf-8")
    assert git_output(repo, "status", "--porcelain", "gates.yaml").strip(), (
        "the catalog edit must be uncommitted, or this test proves nothing"
    )

    assert evaluate(repo) != EXIT_PASS, (
        "an uncommitted edit to required_claims turned a FAIL into a PASS; the "
        "gate was chosen after the work, by the party being gated"
    )


# --- 3. the loader crashes where it promised to refuse ----------------------


def test_set_valued_keyring_key_raises_keyring_error(tmp_path: Path) -> None:
    """Attack: crash the trust-root loader, this time past the guard.

    `_NoDuplicateKeys.construct_mapping` wraps `key in seen` in a try/except that
    converts an unhashable key into KeyringError, but `seen.add(key)` sits
    OUTSIDE it. CPython's set lookup silently retries an unhashable `set` as a
    `frozenset`, so `key in seen` answers False without raising and the guard
    never fires; `set.add` has no such retry and raises TypeError one line later,
    outside every handler. A YAML `!!set` key therefore escapes as a bare
    TypeError.

    The loader's stated contract is that a keyring it cannot fully trust fails as
    KeyringError. `cmd_gate_evaluate` happens to catch TypeError; nothing else
    that imports `load_keyring` promises to, so a caller written to the contract
    crashes where it meant to refuse. The previous fix for the list-key variant
    looked complete and closed only the door it was shown.
    """

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        KeyringError,
        load_keyring,
    )

    path = tmp_path / "producers.yaml"
    path.write_text(
        "producers:\n  ? !!set {a: , b: }\n  : ed25519:AAAA\n", encoding="utf-8"
    )

    try:
        load_keyring(path)
    except KeyringError:
        return
    except Exception as exc:
        pytest.fail(
            f"load_keyring raised {type(exc).__name__}({exc}) instead of "
            "KeyringError; the guard against unhashable producer ids does not "
            "cover `seen.add`"
        )
    pytest.fail("a keyring with a set-valued producer id loaded without error")


# --- 4. a refusal wearing the clothes of honest absence ---------------------


def test_rejection_without_a_claim_id_is_not_reported_as_absence(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: tamper in the one field that erases your own fingerprints.

    Admission reads `claim_id` with `_text_or_none`, so a non-string value makes
    the resulting Rejection carry `claim_id=None`. The report then computes
    `refused = missing & explained` — and None intersects no required claim, so
    the claim drops through into the `absent` bucket and is printed as "no
    evidence for required claim". That is the kernel's phrasing for honest
    absence, and admission's whole reason for returning structured rejections is
    that absence and attack must never share a sentence.

    An operator reading that line sees a task nobody got to. What happened is a
    tampered record sitting in the evidence file, and the tamper was in the very
    field the report needs in order to say so. Changing `"tests-executed"` to
    `7` is the entire attack.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    tampered = signed(
        record(
            claim="tests-executed",
            digest=subject_digest(repo),
            producer="worker",
        ),
        keys.private["worker"],
    )
    tampered["claim_id"] = 7  # not a string: admission cannot name the claim
    write_evidence(repo, [tampered])

    capsys.readouterr()
    code = evaluate(repo)
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert code == EXIT_FAIL, output
    assert "REFUSED" in output, (
        "the tampered record must be reported as refused: " + output
    )

    absence_lines = [
        line for line in output.splitlines()
        if "no evidence for required claim" in line
    ]
    for line in absence_lines:
        assert "tests-executed" not in line, (
            "a tampered record was reported as work never done: " + line
        )
