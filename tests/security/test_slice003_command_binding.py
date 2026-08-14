"""SLICE-003 — the binding is signed, and v1 is not accepted.

Written before the implementation and required to fail first.

Three attacks against the claim to command binding, one test family each:

1. **Downgrade.** `ranex-evidence-v1` covered five fields and said nothing about
   what ran. If a v1 signature is still admitted, every record produced before
   this slice — and every record a v1 signer can still produce — satisfies a
   bound claim without naming a command. That is a downgrade attack against the
   whole slice, so v1 records are refused rather than migrated.
2. **Digest swap.** `command_digest` is what the kernel compares. If the
   signature does not cover it, a keyholder-free attacker with a text editor
   rewrites it to whatever the catalog demands.
3. **Legible-field swap.** `command` is what a human reads in review. If only
   the digest were signed, the readable field could be replaced under a matching
   digest and review would be reading fiction.
4. **Path swap.** `executable_path` carries the containment decision forward to
   evaluation (ADR-001, improvement 2). An unsigned path would let an attacker
   rewrite the one field the re-check reads, and a signed path that nothing
   re-checks would be decoration. Both halves are tested.

Done criteria 5, 6 and 7 of docs/slices/SLICE-003-claim-command-binding.md, and
ADR-001 sad paths 8, 9, 10 and 14. The `run`-side confinement lives in
tests/security/test_executable_path_confinement.py.

Imports of `ranex` are deliberately deferred into fixtures and test bodies. A
module-level import of a symbol a fix has not created yet is a collection error,
and a collection error takes the whole suite down with it — hiding the very
tests that prove nothing else regressed.
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from ranex.foundation.canonical import command_digest

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

V1_DOMAIN = b"ranex-evidence-v1\n"
V1_FIELDS = ("claim_id", "command", "exit_code", "producer_id", "subject_digest")

CHECK_SCRIPT = "grep -qx content file.txt\n"
BOUND = ["sh", "check.sh"]

# Resolved, absolute, and outside any repository under test — what `run` records
# for `sh` and what the containment re-check must accept.
EXECUTABLE = str(Path(shutil.which("sh")).resolve())

SUBJECT = "sha256:" + "a" * 64


def content(
    *,
    argv: list[str] = BOUND,
    claim: str = "tests-executed",
    digest: str = SUBJECT,
    producer: str = "worker",
    exit_code: int = 0,
    executable: str = EXECUTABLE,
) -> dict[str, object]:
    """A v2 record body: the five v1 fields, the command digest, the path."""

    return {
        "claim_id": claim,
        "command": " ".join(argv),
        "command_digest": command_digest(argv),
        "executable_path": executable,
        "exit_code": exit_code,
        "producer_id": producer,
        "subject_digest": digest,
        "suite_results": None,
        "confinement_result_digest": "sha256:" + "c" * 64,
        "confinement_profile_digest": "sha256:" + "d" * 64,
    }


def sign_with_domain(body: dict[str, object], private_key: str, domain: bytes) -> str:
    """Sign `body` under an arbitrary domain prefix.

    Bypasses `sign_evidence` on purpose: the attacks below need bytes the
    current signer would refuse to produce, which is exactly what a v1 signer or
    an old record already is.
    """

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from ranex.foundation.canonical import canonical_json_bytes

    raw = base64.b64decode(private_key.removeprefix("ed25519:"))
    key = Ed25519PrivateKey.from_private_bytes(raw)
    signature = key.sign(domain + canonical_json_bytes(dict(body)))
    return "ed25519:" + base64.b64encode(signature).decode("ascii")


@pytest.fixture()
def worker() -> tuple[str, str]:
    from ranex.foundation.signing import generate_keypair

    return generate_keypair()


# --- criterion 5: a v1 signature is refused at admission --------------------


def test_the_evidence_domain_moved_to_v3() -> None:
    """The domain prefix is inside the signed bytes, so bumping it is what makes
    a v1 signature fail to verify against v2 content rather than merely being
    unusual."""

    from ranex.foundation.signing import EVIDENCE_DOMAIN, SIGNED_FIELDS

    assert EVIDENCE_DOMAIN == b"ranex-evidence-v4\n"
    assert set(SIGNED_FIELDS) == set(V1_FIELDS) | {
        "command_digest",
        "executable_path",
        "suite_results",
        "confinement_result_digest",
        "confinement_profile_digest",
    }
    assert len(SIGNED_FIELDS) == 10


def test_a_whole_v1_record_is_not_admitted(worker: tuple[str, str]) -> None:
    """The old record, exactly as it sits in an existing evidence file: five
    fields, signed under the v1 domain. `governance/evidence.json` is gitignored
    and no signed evidence is committed, so there is nothing to migrate — and a
    silent acceptance path would be the downgrade this slice must not leave
    open.

    Which control catches it is asserted, not left open. An audit rolled
    `EVIDENCE_DOMAIN` back to v1 and this test stayed green, because a genuine
    five-field record never reaches the signature at all — the field-set check
    refuses it first. That is correct behaviour and it is *not* evidence that the
    domain bump works, so asserting only "rejected" let this stand in as proof
    for something it does not prove. The domain prefix is load bearing, and
    `test_a_v2_shaped_record_signed_under_v1_does_not_verify` is what proves it.
    """

    from ranex.governed_execution.domain.admission import RejectionReason, admit

    private, public = worker
    body = {field: content()[field] for field in V1_FIELDS}
    v1_record = {**body, "signature": sign_with_domain(body, private, V1_DOMAIN)}

    result = admit([v1_record], {"worker": public})

    assert result.evidence == (), (
        "a v1 record was admitted; every pre-slice record then satisfies a "
        "bound claim without ever naming a command"
    )
    (rejection,) = result.rejections
    assert rejection.reason is RejectionReason.MALFORMED_RECORD, (
        "a five-field record must be refused for the fields it does not carry; "
        f"reported instead as {rejection.reason}: {rejection.detail}"
    )
    assert "command_digest" in rejection.detail
    assert "executable_path" in rejection.detail


def test_a_v2_shaped_record_signed_under_v1_does_not_verify(
    worker: tuple[str, str],
) -> None:
    """The sharper form: an attacker holding a v1 signer emits the new field set
    but signs it with the old domain. Only the domain prefix distinguishes the
    two payloads, so this is the test that proves the prefix is load bearing."""

    from ranex.governed_execution.domain.admission import RejectionReason, admit

    private, public = worker
    body = content()
    record = {**body, "signature": sign_with_domain(body, private, V1_DOMAIN)}

    result = admit([record], {"worker": public})

    assert result.evidence == ()
    (rejection,) = result.rejections
    assert rejection.reason is RejectionReason.BAD_SIGNATURE


def test_a_v2_signature_over_v2_content_is_admitted(worker: tuple[str, str]) -> None:
    """The control: without this the three tests above would pass on a signer
    that verifies nothing at all."""

    from ranex.foundation.signing import sign_evidence
    from ranex.governed_execution.domain.admission import admit

    private, public = worker
    body = content()
    result = admit([{**body, "signature": sign_evidence(body, private)}], {"worker": public})

    assert result.rejections == ()
    (evidence,) = result.evidence
    assert evidence.command_digest == command_digest(BOUND)


# --- criterion 6: the signature covers command_digest -----------------------


def test_flipping_the_command_digest_breaks_the_signature(
    worker: tuple[str, str],
) -> None:
    """Without this the binding is decoration: the digest is the field the
    kernel compares, so an unsigned digest is a field the attacker chooses."""

    from ranex.foundation.signing import sign_evidence
    from ranex.governed_execution.domain.admission import RejectionReason, admit

    private, public = worker
    body = content(argv=["true"])
    record = {**body, "signature": sign_evidence(body, private)}

    # `true` ran; the record now claims the digest of the bound command.
    record["command_digest"] = command_digest(BOUND)

    result = admit([record], {"worker": public})
    assert result.evidence == ()
    (rejection,) = result.rejections
    assert rejection.reason is RejectionReason.BAD_SIGNATURE


# --- criterion 7: the readable command stays signed too ---------------------


def test_flipping_the_readable_command_alone_breaks_the_signature(
    worker: tuple[str, str],
) -> None:
    """`command_digest` matching does not make `command` free.

    Review reads the legible field. If only the digest were signed, a record
    could carry the bound digest next to a sentence describing something else,
    and every human control downstream of review would be reading fiction.
    """

    from ranex.foundation.signing import sign_evidence
    from ranex.governed_execution.domain.admission import RejectionReason, admit

    private, public = worker
    body = content(argv=BOUND)
    record = {**body, "signature": sign_evidence(body, private)}

    record["command"] = "true"  # digest untouched, story rewritten

    result = admit([record], {"worker": public})
    assert result.evidence == ()
    (rejection,) = result.rejections
    assert rejection.reason is RejectionReason.BAD_SIGNATURE


# --- ADR-001 sad path 14: the resolved path is signed too -------------------


def test_flipping_the_executable_path_breaks_the_signature(
    worker: tuple[str, str],
) -> None:
    """The containment decision is carried forward in `executable_path`, so an
    unsigned path would let an attacker rewrite the one field the evaluate-time
    re-check reads. in-toto's spec concedes `expected_command` "can easily be
    forged… by changing the PATH"; this field is the answer, and it is worth
    nothing unless the signature covers it."""

    from ranex.foundation.signing import sign_evidence
    from ranex.governed_execution.domain.admission import RejectionReason, admit

    private, public = worker
    body = content()
    record = {**body, "signature": sign_evidence(body, private)}

    record["executable_path"] = "/opt/attacker/sh"

    result = admit([record], {"worker": public})
    assert result.evidence == ()
    (rejection,) = result.rejections
    assert rejection.reason is RejectionReason.BAD_SIGNATURE


# --- and the operator sees it, through the real CLI -------------------------


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


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    repository = tmp_path / "governed"
    subprocess.run(["git", "init", "-q", str(repository)], check=True)
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test")):
        subprocess.run(
            ["git", "-C", str(repository), "config", key, value], check=True
        )
    (repository / "file.txt").write_text("content\n", encoding="utf-8")
    (repository / "check.sh").write_text(CHECK_SCRIPT, encoding="utf-8")
    (repository / "gates.yaml").write_text(
        build_gates("tests-executed", BOUND), encoding="utf-8"
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


def keygen(repo: Path, key_path: Path, producer: str = "worker") -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = invoke(repo, ["keygen", "--producer", producer], key_path)
    assert code == EXIT_PASS, buffer.getvalue()
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", buffer.getvalue())
    assert match, f"keygen printed no public key: {buffer.getvalue()!r}"
    return match.group(1)


def register(repo: Path, tmp_path: Path) -> Path:
    """keygen a worker key, commit the keyring, return the key path."""

    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    (repo / "producers.yaml").write_text(
        f"producers:\n  worker: {public}\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "initial"], check=True
    )
    return key_path


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


def head_subject(repo: Path) -> str:
    from ranex.foundation.canonical import canonical_sha256

    tree = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD^{tree}"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return "sha256:" + canonical_sha256({"tree": tree})


def test_a_record_naming_an_in_repository_executable_does_not_satisfy(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """ADR-001 sad path 14, second half: verified at both ends.

    `run` refuses to execute an `argv[0]` that resolves inside the subject
    worktree. That refusal is worth nothing on its own — a keyholder can write
    the record by hand and never invoke `run`. So the containment rule is
    re-checked at evaluation from the recorded path, and a record naming a
    binary inside the repository must not satisfy the claim however perfect its
    signature is.

    This is the whole point of `executable_path` being a field rather than a
    check `run` performs and forgets. It must also not be reported as honest
    absence: the record exists and is signed, so calling it "work never done"
    would hide the attack in a list of unfinished tasks.
    """

    from ranex.foundation.signing import sign_evidence

    key_path = register(repo, tmp_path)
    private = key_path.read_text(encoding="utf-8").strip()

    # A shadowed `sh` sitting in the tree under observation: exactly the
    # PATH-aliasing forgery the in-toto spec concedes defeats expected_command.
    body = content(
        argv=BOUND,
        digest=head_subject(repo),
        executable=str((repo / "sh").resolve()),
    )
    (repo / "evidence.json").write_text(
        json.dumps([{**body, "signature": sign_evidence(body, private)}], indent=2),
        encoding="utf-8",
    )

    capsys.readouterr()
    assert evaluate(repo) == EXIT_FAIL, (
        "a record naming an executable inside the repository under observation "
        "satisfied the claim; the containment rule is enforced only by `run` "
        "and can be walked around by writing the record directly"
    )
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "PASS" not in output, output
    assert "no evidence for required claim" not in output, (
        "a signed record naming an in-repository executable was reported as "
        "work never done: " + output
    )


def test_a_hand_swapped_digest_is_reported_as_a_refusal_not_as_absence(
    repo: Path,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The whole attack end to end: run something trivial, then edit the record
    to claim the bound command.

    It must fail, and it must not fail wearing the clothes of honest absence —
    "no evidence for required claim" is a task nobody got to, and this is an
    attack sitting in the evidence file.
    """

    key_path = tmp_path / "worker.key"
    public = keygen(repo, key_path)
    (repo / "producers.yaml").write_text(
        f"producers:\n  worker: {public}\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-q", "-m", "initial"], check=True
    )

    assert invoke(
        repo,
        [
            "run",
            "--claim", "tests-executed",
            "--producer", "worker",
            "--repository", ".",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--", "true",
        ],
        key_path,
    ) == EXIT_PASS

    path = repo / "evidence.json"
    (record,) = json.loads(path.read_text(encoding="utf-8"))
    record["command_digest"] = command_digest(BOUND)
    record["command"] = " ".join(BOUND)
    path.write_text(json.dumps([record], indent=2) + "\n", encoding="utf-8")

    capsys.readouterr()
    assert invoke(
        repo,
        [
            "gate", "evaluate", "HEAD",
            "--repository", ".",
            "--gate-catalog", "gates.yaml",
            "--evidence", "evidence.json",
            "--producers", "producers.yaml",
            "--approver", "reviewer",
        ],
    ) == EXIT_FAIL

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "REFUSED" in output, output
    assert "no evidence for required claim" not in output, output
