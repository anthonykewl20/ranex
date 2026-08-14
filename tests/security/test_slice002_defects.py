"""SLICE-002 — the twelve defects adversarial review found, one attack each.

Written before the fixes and required to fail first. Every test here is a
concrete attack against a property SLICE-002 claims to hold: that a private key
never enters the tree, that a record cannot be edited into a pass, that a
refusal is never reported as honest absence, and that one key serves exactly one
producer.

Nothing here is a style complaint. Each test names a way the current code lets
an operator believe something untrue.

Imports of `ranex` are deliberately deferred into fixtures and test bodies. A
module-level import of a symbol a fix has not created yet is a collection error,
and a collection error takes the whole suite down with it — hiding the very
tests that prove nothing else regressed.
"""

from __future__ import annotations

import base64
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

# The standard alphabet, needed to construct a base64 string that decodes to the
# same bytes as another one. See `noncanonical_variant`.
_B64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

# A well-formed digest that is not the digest of any tree in the test repository.
STALE_DIGEST = "sha256:" + "a" * 64


# SLICE-003: a claim declares the command that satisfies it, so the catalog and
# the hand-built records below have to agree about what each claim means.
# Explicit rather than defaulted: a claim with no declared command is a claim
# whose satisfaction is undefined, which the loader refuses outright.
COMMAND_FOR: dict[str, list[str]] = {
    "tests-executed": ["sh", "run-tests.sh"],
    "lint-clean": ["sh", "lint.sh"],
}

# Succeeds against any tree. Never bound to anything; used only to show that a
# record of it satisfies nothing.
TRIVIAL = ["sh", "-c", "exit 0"]

# The resolved absolute path of argv[0], as `run` records it (ADR-001).
# Outside the repository under test, which is the containment rule it obeys.
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
    for producer in ("worker", "alice"):
        private_key, public_key = generate_keypair()
        bundle.private[producer] = private_key
        bundle.public[producer] = public_key
        path = bundle.path(producer)
        path.write_text(private_key + "\n", encoding="utf-8")
        path.chmod(0o600)
    return bundle


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
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


def subject_digest(repo: Path, ref: str = "HEAD") -> str:
    from ranex.foundation.canonical import canonical_sha256

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", f"{ref}^{{tree}}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


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
    """A record body for `claim`, describing the command that claim names.

    SLICE-003 rewrote this helper. It used to default to `sh -c 'exit 0'`, and
    every test below that expected a PASS was therefore asserting that a command
    which succeeds against any tree is evidence that this tree's tests ran. The
    default is now the command the catalog binds to the claim; a record of
    anything else is exercised deliberately, by passing `argv`, and is expected
    to be refused — see `test_a_trivial_command_satisfies_no_bound_claim`.
    """

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


def write_evidence(
    repo: Path, records: list[dict[str, object]], name: str = "evidence.json"
) -> Path:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
    return path


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
    approver: str = "reviewer",
    evidence: str = "evidence.json",
) -> int:
    return invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", evidence,
            "--producers", "producers.yaml",
            "--approver", approver,
        ],
    )


def noncanonical_variant(public_key: str) -> str:
    """A second spelling of the same Ed25519 key.

    32 bytes do not divide into 3-byte base64 groups, so the final character
    carries two bits no decoder uses. Flipping them yields a different string
    that decodes to byte-identical key material — four spellings per key.
    """

    prefix, _, encoded = public_key.partition(":")
    assert encoded.endswith("="), f"unexpected padding in {public_key!r}"
    value = _B64_ALPHABET.index(encoded[-2])
    variant = (value & 0b111100) | ((value + 1) & 0b11)
    return f"{prefix}:{encoded[:-2]}{_B64_ALPHABET[variant]}="


# --- 0. SLICE-003: the blessing this file used to carry ---------------------


def test_a_trivial_command_satisfies_no_bound_claim(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The inversion of this file's old `record()` default, stated as a test.

    Every record here used to describe `sh -c 'exit 0'` and count. The record
    below is flawless by every SLICE-002 measure — correctly signed, registered
    producer, bound to this exact tree, exit code 0 — and it must not satisfy
    `tests-executed`, because `tests-executed` names a command and this is not
    it. Signature and subject digest prove who recorded what against which tree.
    Neither proves any work happened; that is what this slice adds.
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
                    producer="worker",
                    argv=TRIVIAL,
                ),
                keys.private["worker"],
            )
        ],
    )

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL, (
        "a command that exits 0 against any tree was accepted as evidence for a "
        "claim bound to a different command"
    )
    assert "PASS" not in capsys.readouterr().out


# --- 1. non-canonical base64 is accepted as key material --------------------


def test_noncanonical_base64_is_not_a_public_key() -> None:
    """Attack: one key, four spellings.

    `base64.b64decode(validate=True)` validates the alphabet but not the unused
    trailing bits, so an Ed25519 public key has four distinct encodings that all
    decode to the same 32 bytes. Any identity keyed by the *string* — the
    keyring, `run`'s "is this my registered key" check — can therefore be given
    two entries that are the same key. A canonical encoding is the only thing
    that makes key identity and string identity the same question.
    """

    from ranex.foundation.signing import generate_keypair, is_public_key

    _, public_key = generate_keypair()
    variant = noncanonical_variant(public_key)

    assert variant != public_key
    assert base64.b64decode(variant.partition(":")[2], validate=True) == (
        base64.b64decode(public_key.partition(":")[2], validate=True)
    ), "the variant must be the same key, or this test proves nothing"

    assert is_public_key(public_key) is True
    assert is_public_key(variant) is False, (
        "a non-canonical encoding was accepted as a distinct public key"
    )


def test_keyring_refuses_two_spellings_of_one_key(tmp_path: Path) -> None:
    """Attack: defeat one-key-one-producer with a single character.

    The keyring already refuses two producers sharing a public key, because the
    holder of the private half would produce evidence as one identity and
    approve it as the other, walking straight past no-self-approval. That
    refusal compares strings. Registering `worker` and `alice` with two
    spellings of the SAME key passes the check and restores the attack.
    """

    from ranex.foundation.signing import generate_keypair
    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        KeyringError,
        load_keyring,
    )

    _, public_key = generate_keypair()
    variant = noncanonical_variant(public_key)
    path = tmp_path / "producers.yaml"
    path.write_text(
        f"producers:\n  worker: {public_key}\n  alice: {variant}\n",
        encoding="utf-8",
    )

    with pytest.raises(KeyringError):
        load_keyring(path)


# --- 2. the observed command inherits the signing key -----------------------


def test_run_does_not_hand_the_signing_key_to_the_command(
    repo: Path,
    keys: Keys,
    tmp_path: Path,
) -> None:
    """Attack: the command Ranex observes steals the key that signs the verdict.

    `subprocess.run(command, cwd=root)` passes no `env=`, so the child inherits
    `$RANEX_SIGNING_KEY` and the ambient permission to read it. The observed
    command is by definition untrusted — it is the agent's work. Given the
    producer's private key it can sign any record it likes for any subject,
    which collapses the whole slice: signatures then prove nothing beyond
    "something on this machine ran".
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    leak = tmp_path / "leak"
    leak.mkdir()
    variable_file = leak / "variable"
    key_file = leak / "key"
    script = (
        f'printf %s "${{RANEX_SIGNING_KEY-<unset>}}" > "{variable_file}"\n'
        f'cat "${{RANEX_SIGNING_KEY-/nonexistent}}" > "{key_file}" 2>/dev/null || true\n'
    )

    assert run_cmd(repo, keys.path("worker"), "sh", "-c", script) == EXIT_PASS

    leaked_variable = variable_file.read_text(encoding="utf-8")
    leaked_key = key_file.read_text(encoding="utf-8")

    assert str(keys.path("worker")) not in leaked_variable, (
        "the observed command was told where the signing key lives"
    )
    assert "ed25519:" not in leaked_key, (
        "the observed command read the producer's private key"
    )


# --- 3. keygen writes into a linked worktree --------------------------------


def test_keygen_refuses_a_linked_worktree(
    repo: Path,
    tmp_path: Path,
) -> None:
    """Attack: put the key in a checkout of the same repository.

    Containment only asks whether the target is under `governed_repository_root()`.
    A linked worktree lives at a different path yet is the same repository: it
    shares the object store, and anything written there is `git add`-able and
    lands in a commit. The premise "private keys are never committable" fails
    while every existing confinement test still passes.
    """

    commit_all(repo)
    worktree = tmp_path / "linked-worktree"
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "-q",
         str(worktree), "-b", "side"],
        check=True,
    )
    target = worktree / "worker.key"

    assert invoke(repo, ["keygen", "--producer", "worker"], target) == EXIT_USAGE
    assert not target.exists(), "a private key was written into a linked worktree"


# --- 4. a refused claim is also reported as honest absence ------------------


def test_refused_claim_is_never_listed_as_no_evidence(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: hide a forgery inside a list of missing work.

    `if missing and missing <= explained` is all-or-nothing. With two required
    claims, one tampered record and one genuinely absent claim, the subset test
    fails and the kernel's phrasing for honest absence is printed for BOTH — so
    the tampered claim appears under "no evidence for required claim". An
    operator reading that sees an unfinished task where an attack occurred,
    which is precisely the distinction admission exists to preserve.
    """

    (repo / "gates.yaml").write_text(
        build_gates("tests-executed", "lint-clean"), encoding="utf-8"
    )
    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    tampered = signed(
        record(
            claim="tests-executed",
            digest=subject_digest(repo),
            producer="worker",
            exit_code=1,
        ),
        keys.private["worker"],
    )
    tampered["exit_code"] = 0  # the classic edit: a failure turned into a pass
    write_evidence(repo, [tampered])

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL
    captured = capsys.readouterr()
    output = captured.out + captured.err

    absence_lines = [
        line for line in output.splitlines()
        if "no evidence for required claim" in line
    ]
    assert absence_lines, output
    for line in absence_lines:
        assert "tests-executed" not in line, (
            "a tampered record was reported as work never done: " + line
        )


# --- 5. a PASS hides the refusals ------------------------------------------


def test_pass_still_reports_refused_records(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: bury a forgery attempt under a legitimate pass.

    `cmd_gate_evaluate` returns as soon as the verdict is PASS, before the
    rejection loop. An attacker who forges a record and also happens to satisfy
    the gate honestly gets a clean PASS with no mention that a forged record was
    sitting in the evidence file. Forgery attempts must be visible whatever the
    verdict; a probe that leaves no trace is a probe worth repeating.
    """

    write_keyring(repo, worker=keys.public["worker"], alice=keys.public["alice"])
    commit_all(repo)

    digest = subject_digest(repo)
    honest = signed(
        record(claim="tests-executed", digest=digest, producer="worker"),
        keys.private["worker"],
    )
    forged = signed(
        record(claim="tests-executed", digest=digest, producer="alice", exit_code=1),
        keys.private["alice"],
    )
    forged["exit_code"] = 0
    write_evidence(repo, [honest, forged])

    capsys.readouterr()
    assert evaluate(repo) == EXIT_PASS
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert "REFUSED" in output, (
        "a forged record was silently discarded because the gate passed anyway"
    )
    assert "alice" in output


# --- 6. an empty producers mapping is a silent empty keyring ----------------


def test_empty_producers_mapping_is_an_error(tmp_path: Path) -> None:
    """Attack: disable the trust root by deleting its contents, not its file.

    `producers: {}` parses, is a mapping, and loops zero times — so it returns
    an empty keyring. Every record is then rejected as an unknown producer, the
    gate FAILs, and the output is indistinguishable from a project that has not
    run its tests. That is the exact failure mode this module's own docstring
    says must never happen.
    """

    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        KeyringError,
        load_keyring,
    )

    path = tmp_path / "producers.yaml"
    for text in ("producers: {}\n", "producers:\n"):
        path.write_text(text, encoding="utf-8")
        with pytest.raises(KeyringError):
            load_keyring(path)


# --- 7. an unreadable evidence file reads as no evidence --------------------


def test_unreadable_evidence_is_loud_not_absent(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: suppress evidence by making it unreadable.

    `Path.exists()` swallows every OSError and answers False, so a permission
    error on the evidence file is reported as "no evidence for required claim".
    The gate FAILs either way, but the two are different events: one is work not
    done, the other is a machine that cannot be trusted to see its own records.
    Silently downgrading the second to the first also hides a tampering
    technique — chmod is easier than forging a signature.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    vault = repo / "vault"
    vault.mkdir()
    valid = signed(
        record(
            claim="tests-executed",
            digest=subject_digest(repo),
            producer="worker",
        ),
        keys.private["worker"],
    )
    (vault / "evidence.json").write_text(
        json.dumps([valid], indent=2) + "\n", encoding="utf-8"
    )
    vault.chmod(0o000)

    capsys.readouterr()
    try:
        code = evaluate(repo, evidence="vault/evidence.json")
        captured = capsys.readouterr()
    finally:
        vault.chmod(0o755)

    output = captured.out + captured.err
    assert code == EXIT_USAGE, (
        "an unreadable evidence file produced a verdict instead of an error"
    )
    assert "no evidence for required claim" not in output, output


# --- 8. run pays for the command before finding it cannot record ------------


def test_run_refuses_before_running_when_evidence_is_corrupt(
    repo: Path,
    keys: Keys,
) -> None:
    """Attack surface: an expensive run thrown away, and a half-told story.

    `run`'s own comment promises that everything which can refuse refuses before
    the command runs. It does not check that the evidence file can be rewritten,
    so a corrupt `evidence.json` is discovered only by `record_evidence` after
    the command has already executed and had all its side effects. The operator
    is left with a command that ran, changed the tree, and left no record of
    having done so.
    """

    write_keyring(repo, worker=keys.public["worker"])
    commit_all(repo)

    (repo / "evidence.json").write_text("[{ truncated", encoding="utf-8")

    marker = repo / "ran.txt"
    code = run_cmd(
        repo, keys.path("worker"), "sh", "-c", f"touch {marker.name}; exit 0"
    )

    assert code == EXIT_USAGE
    assert not marker.exists(), (
        "the command ran before `run` discovered it could not record the result"
    )


# --- 9. the kernel's diagnosis is discarded ---------------------------------


def test_stale_subject_diagnosis_survives_a_refusal(
    repo: Path,
    keys: Keys,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Attack: replay old evidence next to a forgery and lose the diagnosis.

    When every missing claim is named by some rejection, `cmd_gate_evaluate`
    prints its own summary and throws `result.reason` away. Here the claim is
    missing for a second, independent reason: the one record that verifies is
    bound to a different subject digest. The operator is told only that records
    were refused, and never that valid-looking evidence for a different tree is
    sitting in the file — the replay attack the subject binding exists to catch.
    """

    write_keyring(repo, worker=keys.public["worker"], alice=keys.public["alice"])
    commit_all(repo)

    stale = signed(
        record(claim="tests-executed", digest=STALE_DIGEST, producer="worker"),
        keys.private["worker"],
    )
    forged = signed(
        record(
            claim="tests-executed",
            digest=subject_digest(repo),
            producer="alice",
            exit_code=1,
        ),
        keys.private["alice"],
    )
    forged["exit_code"] = 0
    write_evidence(repo, [stale, forged])

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL
    captured = capsys.readouterr()
    output = captured.out + captured.err

    assert "different subject" in output, (
        "the kernel's stale-subject diagnosis was discarded: " + output
    )


# --- 10. run accepts a signing key that lives in the repository -------------


def test_run_refuses_a_signing_key_inside_the_repository(
    repo: Path,
    keys: Keys,
) -> None:
    """Attack: put the key where keygen refuses to, then use it anyway.

    `keygen` will not create a key inside the repository, but
    `private_signing_key` will happily read one from there. A `.gitignore` entry
    makes the working tree read clean, so `run` records evidence signed by a key
    that is one `git add -f` away from being published. The refusal must live at
    the point of use, not only at the point of creation, or it is advisory.
    """

    write_keyring(repo, worker=keys.public["worker"])
    inside = repo / "worker.key"
    inside.write_text(keys.private["worker"] + "\n", encoding="utf-8")
    inside.chmod(0o600)
    (repo / ".gitignore").write_text("worker.key\n", encoding="utf-8")
    commit_all(repo)

    marker = repo / "ran.txt"
    code = run_cmd(repo, inside, "sh", "-c", f"touch {marker.name}; exit 0")

    assert code == EXIT_USAGE, (
        "a private key inside the repository was accepted for signing"
    )
    assert not marker.exists()
    assert not (repo / "evidence.json").exists()


# --- 11. a complex YAML key crashes the loader ------------------------------


def test_unhashable_keyring_key_raises_keyring_error(tmp_path: Path) -> None:
    """Attack: crash the trust-root loader with two characters of YAML.

    A complex key (`? [a, b]`) constructs to a list, and the duplicate-key guard
    tests membership in a set — so the loader raises TypeError instead of
    KeyringError. `cmd_gate_evaluate` does catch TypeError, but nothing else
    that imports `load_keyring` promises to; the loader's contract is that every
    untrustworthy keyring fails as KeyringError, and a caller written to that
    contract crashes instead of refusing.
    """

    from ranex.foundation.signing import generate_keypair
    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        KeyringError,
        load_keyring,
    )

    _, public_key = generate_keypair()
    path = tmp_path / "producers.yaml"
    path.write_text(
        f"producers:\n  ? [alice, worker]\n  : {public_key}\n", encoding="utf-8"
    )

    with pytest.raises(KeyringError):
        load_keyring(path)


# --- 12. unencodable content is reported as a forgery -----------------------


def test_unencodable_record_is_malformed_not_a_bad_signature() -> None:
    """Attack: manufacture a false accusation of forgery.

    `json.loads` accepts a lone surrogate (`"\\ud800"`) and a bare `NaN`; the
    canonical encoder does not. `verify_evidence` catches the resulting
    ValueError and returns False, so admission reports BAD_SIGNATURE — "the
    record was altered or signed by another key" — when no verification ever
    took place. That is an accusation against a named producer, generated by
    anyone who can write six characters into the evidence file. A record that
    cannot be encoded is MALFORMED_RECORD; only a real verification failure may
    say bad-signature.
    """

    from ranex.foundation.signing import generate_keypair
    from ranex.governed_execution.domain.admission import RejectionReason, admit

    _, public_key = generate_keypair()
    keyring = {"worker": public_key}
    digest = STALE_DIGEST
    signature = "ed25519:" + "A" * 86 + "=="
    # Present and well formed, so the field set is complete and the record fails
    # for the one reason under test rather than for a missing SLICE-003 field.
    bound = command_digest(COMMAND_FOR["tests-executed"])

    surrogate = json.loads(
        f'{{"claim_id": "tests-executed", "subject_digest": "{digest}", '
        f'"producer_id": "worker", "command": "\\ud800", "command_digest": "{bound}", '
        f'"executable_path": "/usr/bin/sh", "exit_code": 0, "signature": "{signature}"}}'
    )
    (rejection,) = admit([surrogate], keyring).rejections
    assert rejection.reason is RejectionReason.MALFORMED_RECORD, (
        f"a record that cannot be encoded was called a forgery: {rejection.detail}"
    )

    not_a_number = json.loads(
        f'{{"claim_id": "tests-executed", "subject_digest": "{digest}", '
        f'"producer_id": "worker", "command": "sh -c true", "command_digest": "{bound}", '
        f'"executable_path": "/usr/bin/sh", "exit_code": NaN, "signature": "{signature}"}}'
    )
    (rejection,) = admit([not_a_number], keyring).rejections
    assert rejection.reason is RejectionReason.MALFORMED_RECORD, (
        f"a record that cannot be encoded was called a forgery: {rejection.detail}"
    )


# --- 13. the evidence exemption covers a tracked, modified file -------------


def test_evidence_exemption_never_covers_a_tracked_file(
    repo: Path,
    keys: Keys,
) -> None:
    """Attack: name a committed file with --evidence and the dirty check dies.

    The exemption exists so the second `run` in a repository does not refuse
    itself over Ranex's own output — output that is gitignored and so is never
    in HEAD. But it is applied to whatever `--evidence` names, so pointing it at
    an already-tracked file suppresses the refusal for that path: the file is
    modified on disk, present when the command runs, absent from HEAD's tree,
    and the record still binds to HEAD's digest. One flag turns the
    dirty-working-tree refusal into a false claim.
    """

    write_keyring(repo, worker=keys.public["worker"])
    (repo / "payload.json").write_text("[]\n", encoding="utf-8")
    commit_all(repo)

    # Tracked, committed, and now different from HEAD — dirty by any reading,
    # and exactly what `run` promises never to bind a subject digest to.
    (repo / "payload.json").write_text('[{"tampered": true}]\n', encoding="utf-8")

    marker = repo / "ran.txt"
    code = invoke(
        repo,
        [
            "run",
            "--claim", "tests-executed",
            "--producer", "worker",
            "--repository", ".",
            "--evidence", "payload.json",
            "--producers", "producers.yaml",
            "--", "sh", "-c", f"touch {marker.name}; exit 0",
        ],
        keys.path("worker"),
    )

    assert code == EXIT_USAGE, (
        "a modified tracked file was exempted from the dirty-tree check "
        "because --evidence named it"
    )
    assert not marker.exists()
    assert json.loads((repo / "payload.json").read_text(encoding="utf-8")) == [
        {"tampered": True}
    ], "evidence was recorded against a tree HEAD does not describe"


# --- 14. keygen's containment check is check-then-open ----------------------


def test_keygen_writes_through_the_directory_it_checked(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Attack: swap the parent directory between the check and the write.

    `cmd_keygen` resolves the target, asks `committable_into` about that path,
    and only later mkdirs and opens it. `O_EXCL` guards the final component
    alone; every parent is traversed again at open time. Replace a parent that
    was a real directory with a symlink into the repository in that interval and
    the key lands in the tree while `WROTE` prints the path that was checked —
    the one thing this slice says can never happen, reported as success.

    Deterministic rather than threaded: the window is entered exactly once, at
    `generate_keypair`, which runs after the check and before the open. A racing
    test would be flaky and would prove less.
    """

    from ranex.foundation.signing import generate_keypair

    commit_all(repo)
    inside = repo / "secrets"
    inside.mkdir()

    # A real directory outside the repository, so the check passes honestly.
    holder = tmp_path / "outside" / "holder"
    holder.mkdir(parents=True)
    target = holder / "worker.key"

    def flip_the_parent_then_generate() -> tuple[str, str]:
        holder.rmdir()
        holder.symlink_to(inside, target_is_directory=True)
        return generate_keypair()

    monkeypatch.setattr(
        "ranex.cli.main.generate_keypair", flip_the_parent_then_generate
    )

    code = invoke(repo, ["keygen", "--producer", "worker"], target)

    assert not (inside / "worker.key").exists(), (
        "a private key was written inside the repository through a parent "
        "directory swapped after the containment check"
    )
    assert code == EXIT_USAGE, (
        "keygen reported success for a directory it no longer wrote through"
    )


def test_keygen_refuses_an_ancestor_swapped_for_a_repository_symlink(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The same attack one level up, where refusing symlinked parents is blind.

    Only the final component of a path is subject to `O_NOFOLLOW`, so swapping
    the target's own parent is the easy half. Swap an ancestor instead and the
    parent is still a real directory — reached, now, through a symlink into the
    repository. Nothing about the open call can see that; only asking where the
    opened directory actually leads can.
    """

    from ranex.foundation.signing import generate_keypair

    commit_all(repo)
    inside = repo / "secrets"
    (inside / "holder").mkdir(parents=True)

    outside = tmp_path / "outside"
    (outside / "holder").mkdir(parents=True)
    target = outside / "holder" / "worker.key"

    def flip_the_ancestor_then_generate() -> tuple[str, str]:
        (outside / "holder").rmdir()
        outside.rmdir()
        outside.symlink_to(inside, target_is_directory=True)
        return generate_keypair()

    monkeypatch.setattr(
        "ranex.cli.main.generate_keypair", flip_the_ancestor_then_generate
    )

    code = invoke(repo, ["keygen", "--producer", "worker"], target)

    assert not (inside / "holder" / "worker.key").exists(), (
        "a private key was written inside the repository through an ancestor "
        "swapped after the containment check"
    )
    assert code == EXIT_USAGE
