"""SLICE-058 — real e2e: the provisioning family (keygen + independent key
verification) on real data.

Issue #38's exact ownership (file 2 of 2). The keygen family rides the
ADR-032 frame (docs/adr/ADR-032-real-e2e-suite-framework.md), following the
SLICE-056/057 family patterns: a real journey whose captured transcripts
compare byte-exactly against golden ``.out`` files through the ONE
centralized normalizer (``_prereqs.normalize_transcript``).

The journey (every command below was verified against the installed kernel
at 271344443 and OpenSSL 3.0.13 in a /tmp/opencode prototype before this
file was frozen — the prototype is the freeze-time evidence, not an
assumption):

* The real ``keygen`` CLI generates a fresh Ed25519 producer keypair outside
  the repository (O_EXCL, mode 0600, absolute-path and committable-target
  refusals upstream). The journey's clone then registers that producer,
  binds a family gate, and a real governed ``run`` records evidence the
  kernel SIGNED with the keygen key — and a green ``gate evaluate`` proves
  the kernel VERIFIED it. That is the kernel half of issue #38
  deterministic gate 3.
* The independent half is the golden's own subject: ``openssl`` — a
  non-kernel tool — makes a real signature with the PRIVATE key (raw seed
  wrapped per RFC 5958/8410 into the DER the CLI accepts) over real
  material (the subject clone's HEAD commit identity), and verifies it
  with the PUBLIC key keygen printed; then openssl independently verifies
  the KERNEL's own evidence signature over the payload bytes the repo's
  ``signed_payload`` builds (the serialization is shared vocabulary; the
  cryptography is independent — the SLICE-056 pattern). Both verifications'
  captured stdout — one ``Signature Verified Successfully`` line each — is
  the transcript frozen against ``expected/keygen-verify.out``. A tampered
  message flips openssl to a refusal (exit 1, ``Signature Verification
  Failure``), the discriminating negative folded into the same test.
* Key material confinement (issue #38 deterministic gate 4, sad paths 5
  and 6): keygen refuses to write inside the governed repository and
  leaves no file; an unwritable parent directory refuses with no partial
  key material; the generated key is mode 0600 outside the tree and its
  private bytes appear in no tracked file; and a private key that has
  become readable by group or other (mode 0644) makes the governed ``run``
  refuse — the confinement rule is enforced at use, not only at creation.

The family declares no expected skips: git, python, and openssl are hard
tool requirements (openssl is issue #38's named independent verifier). A
host missing a required tool fails honestly; it does not skip green.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

E2E_DIR = Path(__file__).resolve().parent
if str(E2E_DIR) not in sys.path:
    sys.path.insert(0, str(E2E_DIR))
import _prereqs  # noqa: E402

from ranex.foundation.signing import signed_payload  # noqa: E402

REAL_REPO = E2E_DIR.parents[1]
EXPECTED = E2E_DIR / "expected"

#: The journey's producer, gate, claim, and bound command — the family
#: spine's pattern: a real command that really runs and attests something
#: true about the subject tree.
FAMILY_PRODUCER = "keygen-family"
FAMILY_GATE = "keygen-family"
FAMILY_CLAIM = "tree-clean"
FAMILY_COMMAND = ("git", "status", "--porcelain")

#: Raw Ed25519 public key → SubjectPublicKeyInfo DER: the 12-byte SPKI
#: header for an Ed25519 point (RFC 8410), verified against OpenSSL 3.0.13
#: in the journey prototype before freezing (SLICE-056's constant).
_ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

#: Raw Ed25519 private seed → PKCS#8 v2 DER: the 16-byte RFC 5958 header
#: around the 32-byte seed (algorithm id 1.3.101.112, RFC 8410), verified
#: against OpenSSL 3.0.13 ``pkeyutl -sign -rawin`` in the prototype.
_ED25519_PKCS8_PREFIX = bytes.fromhex("302e020100300506032b657004220420")

#: Environment keys stripped from every child: the signing variables (the
#: journey sets its own key), the coverage switches (the frame's
#: unwired-children rule), and the trace variables.
_STRIPPED_ENV = (
    "RANEX_SIGNING_KEY",
    "RANEX_VERDICT_SIGNING_KEY",
    "RANEX_VERDICT_DIR",
    "COVERAGE_PROCESS_START",
    "COVERAGE_PROCESS_CONFIG",
    "COVERAGE_FILE",
    "RANEX_TRACE",
    "RANEX_TRACE_EVENT",
    "RANEX_TRACE_PARENT_SID",
)


def ranex(
    subject: Path,
    argv: list[str],
    key: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way an operator does: a real process, the
    subject's own source on PYTHONPATH (the clone judges the clone), the
    key in the real environment variable."""

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    env["PYTHONPATH"] = str(subject / "src")
    if key is not None:
        env["RANEX_SIGNING_KEY"] = str(key)
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=subject,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def git(subject: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(subject), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def golden_text(name: str) -> str:
    """Read a family golden, refusing its absence loudly.

    The two SLICE-058 goldens are the implementation lane's artifacts,
    captured from real runs of these exact journeys (transcripts piped
    through ``_prereqs.normalize_transcript``). A missing golden is this
    file's frozen red — the honest one — until that capture lands.
    """

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-058 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture above), pipe the CLI stdout through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


@dataclass
class KeygenJourney:
    """Everything the frozen tests consume from the one module journey."""

    subject: Path
    key: Path
    public: str
    private_text: str
    keygen_transcript: str
    recorded_run: subprocess.CompletedProcess[str]
    evaluate_transcript: str
    record: dict[str, object]
    message: bytes
    verify_external: subprocess.CompletedProcess[str]
    verify_kernel: subprocess.CompletedProcess[str]
    tampered_refusal: subprocess.CompletedProcess[str]
    scratch: Path


@pytest.fixture(scope="module")
def journey(tmp_path_factory: pytest.TempPathFactory) -> KeygenJourney:
    """The one real journey: real keygen, real kernel signing and
    verification, real independent openssl verification both ways.

    Ordered, spine-style: every stage's refusal is loud and names the
    stage, so a journey that cannot complete fails here with the CLI's own
    words instead of a dereference error in a test below.
    """

    openssl = shutil.which("openssl")
    assert openssl is not None, (
        "the openssl binary is a hard requirement of this family's "
        "independent verification (issue #38 names it): a host without it "
        "fails honestly rather than skipping green"
    )

    base = tmp_path_factory.mktemp("provisioning-family-keygen")
    subject = base / "subject"
    key = base / f"{FAMILY_PRODUCER}.key"
    cloned = subprocess.run(
        ["git", "clone", "-q", str(REAL_REPO), str(subject)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert cloned.returncode == 0, f"cannot clone the real subject: {cloned.stderr}"
    for name, value in (
        ("user.email", "keygen-family@example.com"),
        ("user.name", "keygen-family journey"),
    ):
        assert git(subject, "config", name, value).returncode == 0

    # The self-contained subject: no committed pins file, no dependency
    # provisioning demanded — the kernel's own documented activation rule
    # (the provisioning family's journeys are the deps file's business).
    removed = git(subject, "rm", "-q", "governance/deps.yaml")
    assert removed.returncode == 0, removed.stderr

    # --- the journey's own producer, via the real keygen CLI --------------
    generated = ranex(subject, ["keygen", "--producer", FAMILY_PRODUCER], key=key)
    assert generated.returncode == 0, generated.stderr
    assert generated.stdout.startswith("WROTE"), generated.stdout
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", generated.stdout)
    assert match, f"keygen printed no public key: {generated.stdout!r}"
    public = match.group(1)
    private_text = key.read_text(encoding="utf-8").strip()
    assert private_text.startswith("ed25519:"), private_text[:16]
    mode = stat.S_IMODE(key.stat().st_mode)
    assert mode == 0o600, f"keygen must write 0600, wrote {oct(mode)}"
    assert not subject.resolve() in key.resolve().parents, (
        "the generated key must live outside the governed subject"
    )

    keyring = subject / "governance" / "producers.yaml"
    lines = keyring.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.rstrip() == "producers:"), None)
    assert header is not None, "the committed keyring carries no producers: mapping"
    lines.insert(header + 1, f"  {FAMILY_PRODUCER}: {public}\n")
    keyring.write_text("".join(lines), encoding="utf-8")
    with (subject / "governance" / "gates.yaml").open("a", encoding="utf-8") as file:
        file.write(
            "  - gate_id: keygen-family\n"
            "    rule_id: TESTS_EXECUTED\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: tree-clean\n"
            '        command: ["git", "status", "--porcelain"]\n'
        )
    staged = git(subject, "add", "governance/producers.yaml", "governance/gates.yaml")
    assert staged.returncode == 0, staged.stderr
    committed = git(
        subject, "commit", "-q", "-m", "register the keygen-family producer and gate"
    )
    assert committed.returncode == 0, committed.stderr

    # --- the kernel half: it signs with the keygen key, then accepts it ---
    recorded = ranex(
        subject,
        [
            "run",
            "--claim",
            FAMILY_CLAIM,
            "--producer",
            FAMILY_PRODUCER,
            "--gate",
            FAMILY_GATE,
            "--repository",
            ".",
            "--",
            *FAMILY_COMMAND,
        ],
        key=key,
    )
    assert recorded.returncode == 0, (
        f"the bound command's governed run must exit 0: {recorded.stderr}"
    )
    assert recorded.stdout.startswith("RECORDED"), recorded.stdout
    record = json.loads(
        (subject / "governance" / "evidence.json").read_text(encoding="utf-8")
    )[0]
    assert record["producer_id"] == FAMILY_PRODUCER

    evaluated = ranex(
        subject,
        [
            "gate",
            "evaluate",
            "HEAD",
            "--repository",
            ".",
            "--gate",
            FAMILY_GATE,
            "--approver",
            "reviewer",
        ],
    )
    assert evaluated.returncode == 0, (
        f"the green evaluation must exit 0: {evaluated.stdout}{evaluated.stderr}"
    )
    assert evaluated.stdout.startswith("PASS"), evaluated.stdout

    # --- the independent half: openssl verifies, both directions ----------
    scratch = base / "openssl-journey"
    scratch.mkdir()
    raw_public = base64.b64decode(public.removeprefix("ed25519:"))
    assert len(raw_public) == 32
    (scratch / "pub.spki.der").write_bytes(_ED25519_SPKI_PREFIX + raw_public)
    raw_private = base64.b64decode(private_text.removeprefix("ed25519:"))
    assert len(raw_private) == 32
    (scratch / "priv.pk8.der").write_bytes(_ED25519_PKCS8_PREFIX + raw_private)

    head = subprocess.run(
        ["git", "-C", str(subject), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    message = head.encode("utf-8") + b"\n"
    (scratch / "message.bin").write_bytes(message)

    def pkeyutl(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [openssl, "pkeyutl", *arguments],
            capture_output=True,
            text=True,
            check=False,
        )

    signed = pkeyutl(
        "-sign",
        "-rawin",
        "-inkey",
        str(scratch / "priv.pk8.der"),
        "-keyform",
        "DER",
        "-in",
        str(scratch / "message.bin"),
        "-out",
        str(scratch / "sig.bin"),
    )
    assert signed.returncode == 0, signed.stderr

    verify_external = pkeyutl(
        "-verify",
        "-pubin",
        "-keyform",
        "DER",
        "-inkey",
        str(scratch / "pub.spki.der"),
        "-rawin",
        "-in",
        str(scratch / "message.bin"),
        "-sigfile",
        str(scratch / "sig.bin"),
    )
    assert verify_external.returncode == 0, (
        "openssl refused the signature it made with the keygen private "
        f"key: {verify_external.stdout}{verify_external.stderr}"
    )
    assert "Verified" in verify_external.stdout, verify_external.stdout

    content = {k: v for k, v in record.items() if k != "signature"}
    (scratch / "kernel-payload.bin").write_bytes(signed_payload(content))
    signature = record["signature"]
    assert isinstance(signature, str) and signature.startswith("ed25519:"), signature
    (scratch / "kernel-sig.bin").write_bytes(
        base64.b64decode(signature.removeprefix("ed25519:"))
    )
    verify_kernel = pkeyutl(
        "-verify",
        "-pubin",
        "-keyform",
        "DER",
        "-inkey",
        str(scratch / "pub.spki.der"),
        "-rawin",
        "-in",
        str(scratch / "kernel-payload.bin"),
        "-sigfile",
        str(scratch / "kernel-sig.bin"),
    )
    assert verify_kernel.returncode == 0, (
        "openssl (a non-kernel tool) refused the signature the kernel "
        f"admitted as evidence: {verify_kernel.stdout}{verify_kernel.stderr}"
    )

    tampered = bytearray(message)
    tampered[0] ^= 0x01
    (scratch / "message.tampered.bin").write_bytes(bytes(tampered))
    tampered_refusal = pkeyutl(
        "-verify",
        "-pubin",
        "-keyform",
        "DER",
        "-inkey",
        str(scratch / "pub.spki.der"),
        "-rawin",
        "-in",
        str(scratch / "message.tampered.bin"),
        "-sigfile",
        str(scratch / "sig.bin"),
    )
    assert tampered_refusal.returncode != 0, (
        "openssl accepted a signature over tampered bytes — the "
        "verification would be decorative"
    )

    return KeygenJourney(
        subject=subject,
        key=key,
        public=public,
        private_text=private_text,
        keygen_transcript=generated.stdout,
        recorded_run=recorded,
        evaluate_transcript=evaluated.stdout,
        record=record,
        message=message,
        verify_external=verify_external,
        verify_kernel=verify_kernel,
        tampered_refusal=tampered_refusal,
        scratch=scratch,
    )


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


def test_keygen_keys_verify_via_openssl_matching_the_golden(
    journey: KeygenJourney,
) -> None:
    """Issue #38 deterministic gate 3 / AC2: the keygen-generated public key
    verifies a real signature made with the private key, checked by openssl
    — not just the kernel. The golden freezes BOTH external verifications'
    real stdout: the signature openssl itself made over the subject's HEAD
    identity, and the kernel's own evidence signature over the payload the
    repo's signed_payload builds. The tampered-message refusal (exit 1,
    ``Signature Verification Failure``) rides the same test as the
    verification's discriminating negative — a verify that cannot fail
    would prove nothing."""

    assert "Signature Verified Successfully" in journey.verify_external.stdout
    assert "Signature Verified Successfully" in journey.verify_kernel.stdout
    assert journey.tampered_refusal.returncode != 0
    assert journey.recorded_run.stdout.startswith("RECORDED")
    assert journey.evaluate_transcript.startswith("PASS")

    transcript = (
        journey.verify_external.stdout + journey.verify_kernel.stdout
    )
    compare_golden(transcript, "keygen-verify.out")


def test_key_material_confinement_holds(journey: KeygenJourney) -> None:
    """Issue #38 deterministic gate 4, sad paths 5 and 6: generated keys
    never leave the declared path, and a key that breaks confinement rules
    is refused at use.

    Four refusals and two invariants, all produced against the real
    subject: keygen refuses a target inside the governed repository; an
    unwritable parent directory refuses with no partial key material; the
    generated key is 0600 and outside the tree, and its private bytes
    appear in no tracked file; and a group-readable copy of the key makes
    the governed run refuse before anything is signed."""

    # --- invariant: the declared path, and only the declared path ----------
    assert journey.key.is_file()
    assert stat.S_IMODE(journey.key.stat().st_mode) == 0o600
    assert not journey.subject.resolve() in journey.key.resolve().parents
    tracked = git(journey.subject, "ls-files")
    assert tracked.returncode == 0, tracked.stderr
    for name in tracked.stdout.splitlines():
        blob = (journey.subject / name).read_bytes()
        assert journey.private_text.encode("utf-8") not in blob, (
            f"private key material leaked into the tracked file {name}"
        )

    # --- keygen refuses to write inside the repository ---------------------
    inside = journey.subject / "governance" / "inside.key"
    refused_inside = ranex(
        journey.subject,
        ["keygen", "--producer", "inside-key"],
        extra_env={"RANEX_SIGNING_KEY": str(inside)},
    )
    assert refused_inside.returncode == 2, refused_inside.stderr
    assert "refusing to write a private key inside the repository" in refused_inside.stderr
    assert not inside.exists()

    # --- keygen refuses an unwritable parent, leaving no partial key -------
    readonly = journey.key.parent / "readonly-dir"
    readonly.mkdir()
    readonly.chmod(0o500)
    refused_unwritable = ranex(
        journey.subject,
        ["keygen", "--producer", "unwritable-key"],
        extra_env={"RANEX_SIGNING_KEY": str(readonly / "x.key")},
    )
    assert refused_unwritable.returncode == 2, refused_unwritable.stderr
    assert list(readonly.iterdir()) == [], (
        "a refused keygen must leave no partial key material behind"
    )

    # --- a group-readable key is refused at use, not only at creation ------
    loose = journey.key.parent / "loose.key"
    loose.write_text(journey.private_text + "\n", encoding="utf-8")
    loose.chmod(0o644)
    refused_loose = ranex(
        journey.subject,
        [
            "run",
            "--claim",
            FAMILY_CLAIM,
            "--producer",
            FAMILY_PRODUCER,
            "--gate",
            FAMILY_GATE,
            "--repository",
            ".",
            "--",
            *FAMILY_COMMAND,
        ],
        key=loose,
    )
    assert refused_loose.returncode == 2, refused_loose.stderr
    assert "must not be readable by group or other" in refused_loose.stderr

    # --- no declared path at all: keygen refuses ---------------------------
    refused_unset = ranex(
        journey.subject,
        ["keygen", "--producer", "nokey"],
        key=None,
    )
    assert refused_unset.returncode == 2, refused_unset.stderr
    assert "RANEX_SIGNING_KEY is not set" in refused_unset.stderr


def test_goldens_carry_real_volatile_material(journey: KeygenJourney) -> None:
    """The keygen golden's normalizer-application contract. This family's
    golden deliberately holds NO volatile class — the volatile material of
    keygen (the fresh public key) never enters the transcript, because the
    verification verdict lines are the artifact — so the contract is the
    inverse shape: the golden must contain no raw key material (a golden
    holding ``ed25519:`` bytes is leaked text, not a capture), must be a
    normalizer fixpoint, and a golden doctored with the FAILING
    verification's outcome provably cannot match the passing actual — the
    same live-substitution refusal the other families freeze for digests.
    """

    name = "keygen-verify.out"
    transcript = journey.verify_external.stdout + journey.verify_kernel.stdout
    golden = golden_text(name)
    assert "ed25519:" not in golden, (
        f"{name} carries raw key material: the verification verdict "
        "transcript never contains key bytes — a golden holding them is "
        "leaked text, not a captured transcript"
    )
    assert _prereqs.normalize_transcript(golden) == golden, (
        f"{name} is not a normalizer fixpoint: it still contains bytes "
        "the frozen grammar would mask, which no capture piped through "
        "normalize_transcript can"
    )
    assert "Signature Verified Successfully" in golden, golden
    doctored = golden.replace(
        "Signature Verified Successfully", "Signature Verification Failure", 1
    )
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _normalized(transcript), doctored, family=name.removesuffix(".out")
        )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: KeygenJourney) -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte of
    the expected file and the comparator must diff dirty, naming the family
    and carrying exactly the first differing hunk — never a bare
    ``assert False``."""

    name = "keygen-verify.out"
    transcript = journey.verify_external.stdout + journey.verify_kernel.stdout
    verdict_word = "Signature Verified Successfully"
    family = name.removesuffix(".out")
    golden = golden_text(name)
    assert verdict_word in golden, golden
    mutated = golden.replace(verdict_word, "Q" + verdict_word[1:], 1)
    with pytest.raises(AssertionError) as raised:
        _prereqs.compare_transcript(_normalized(transcript), mutated, family=family)
    message = str(raised.value)
    assert family in message, f"the mismatch must name the golden family {family!r}: {message}"
    assert "@@" in message, (
        "the mismatch must carry the first differing hunk header: " + message
    )
    assert "Q" + verdict_word[1:] in message, (
        "the first hunk must show the mutated bytes untruncated: " + message
    )
