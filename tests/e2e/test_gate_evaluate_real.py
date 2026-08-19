"""SLICE-056 — real e2e: the verdict family (gate evaluate) on real data.

Issue #36's exact ownership (file 1 of 2). The verdict family rides the
ADR-032 frame (docs/adr/ADR-032-real-e2e-suite-framework.md): real journeys
— a real git subject, real ranex keys via the real ``keygen`` CLI, real
``run`` → ``gate evaluate`` subprocess spines — whose captured transcripts
compare byte-exactly against golden ``.out`` files through the ONE
centralized normalizer (``_prereqs.normalize_transcript``). No per-family
masks exist and none may be added: over-masking is a reviewed golden edit
(ADR-032 sad path 11), never a comparator hack.

The journeys (every command below was verified against the installed
kernel before this file was frozen; the clone-judges-clone construction is
tests/e2e/test_gating_real_suite.py's):

* **FAIL arm** — this repository cloned at HEAD, untouched: the real
  ``governance/gates.yaml``, the real ``governance/suite_manifest.json``,
  the real committed keyring, and *no evidence at all*.
  ``gate evaluate HEAD`` (the real ``landing`` gate) must FAIL: absence
  blocks, never default-pass (issue #36 deterministic gate 2). The journal
  row that evaluation writes is re-read with the stdlib ``sqlite3``
  module — the issue's independent-tool re-check: the durable record a
  non-kernel tool reads must agree with the transcript the CLI printed.
* **PASS arm** — the same clone plus two honest committed differences,
  both the canonical spine's own pattern ("the real tree with one honest
  difference", test_gating_real_suite.py stage 01): the journey's
  ``keygen``-generated producer registered in the committed keyring, and
  a family gate (``verdict-family``) whose single claim binds
  ``git status --porcelain`` — a real command that really runs on any
  host with git and attests something true (the subject tree was clean).
  ``governance/deps.yaml`` is removed in the same commit: the kernel's
  documented rule is that a subject without the committed pins file
  "keeps the self-contained behaviour unchanged" (cmd ``_provisioning_for``),
  so the journey does not drag the network/provisioning stack in. The
  real ``run`` of the bound command records real signed evidence; the
  green ``gate evaluate`` prints the PASS transcript. openssl — a
  non-kernel tool — then verifies the Ed25519 signature the kernel
  admitted, over the payload bytes the repo's own ``signed_payload``
  builds (the serialization is shared vocabulary; the cryptography is
  independent).

Frozen contracts proven red-first here (goldens do not exist at the
freeze commit — their absence is the honest red):

- ``expected/gate-evaluate-pass.out`` and
  ``expected/gate-evaluate-fail.out`` — captured by the implementation
  lane from a real run of these journeys, stdout piped through
  ``_prereqs.normalize_transcript`` exactly as the tests do it. Never
  hand-written: the sabotage control (a mutated golden byte must diff
  dirty, naming the family and the first hunk) and the
  normalizer-application contract (the goldens must carry the
  normalizer's own tokens where the journey emits live volatile
  material, must be a fixpoint of the normalizer, and a golden holding
  raw volatile bytes provably cannot match) together refuse every
  hand-sanitized shape.
- The PASS evidence's honesty guards, folded into the pass-golden test
  because they are that evidence's own contract: ``run`` without
  ``RANEX_SIGNING_KEY`` refuses to write anything (issue #36 sad path 5),
  and once the subject moves past the recorded evidence the evaluation
  FAILs with the stable reason ``evidence bound to a different subject
  digest`` (issue #36 sad path 1).

The family declares no expected skips: git and python are hard tool
requirements of the whole e2e lane, and openssl is a hard requirement of
this file's independent re-check (issue #36 names it). A host missing a
required tool fails honestly; it does not skip green.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import sqlite3
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

#: The journey's producer, gate, claim, and bound command. The claim
#: honestly names what the bound command attests: ``git status
#: --porcelain`` really ran against the subject and the tree was clean.
FAMILY_PRODUCER = "verdict-family"
FAMILY_GATE = "verdict-family"
FAMILY_CLAIM = "tree-clean"
FAMILY_COMMAND = ("git", "status", "--porcelain")

#: Raw Ed25519 public key → SubjectPublicKeyInfo DER: the 12-byte SPKI
#: header for an Ed25519 point (RFC 8410), verified against OpenSSL 3.0.13
#: in the journey prototype before freezing.
_ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")

#: Environment keys stripped from every child: the signing variables (a
#: host's operator key must not leak into the journey's producer
#: identity, and a stray verdict-publication pair would change the
#: evaluate transcript) and the coverage switches (the spine's sanctioned
#: SLICE-055 R2 edit: unwired children carry no coverage environment).
_STRIPPED_ENV = (
    "RANEX_SIGNING_KEY",
    "RANEX_VERDICT_SIGNING_KEY",
    "RANEX_VERDICT_DIR",
    "COVERAGE_PROCESS_START",
    "COVERAGE_PROCESS_CONFIG",
    "COVERAGE_FILE",
)


def ranex(
    subject: Path, argv: list[str], key: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way an operator does: a real process, the
    subject's own source on PYTHONPATH (the clone judges the clone), the
    key in the real environment variable."""

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    env["PYTHONPATH"] = str(subject / "src")
    if key is not None:
        env["RANEX_SIGNING_KEY"] = str(key)
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

    The four SLICE-056 goldens are the implementation lane's artifacts,
    captured from real runs of these exact journeys (stdout piped through
    ``_prereqs.normalize_transcript``). A missing golden is this file's
    frozen red — the honest one — until that capture lands.
    """

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-056 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture above), pipe the CLI stdout through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


@dataclass
class GateJourney:
    """Everything the frozen tests consume from the one module journey."""

    subject: Path
    key: Path
    public: str
    record: dict[str, object]
    fail_transcript: str
    pass_transcript: str
    stale_transcript: str


@pytest.fixture(scope="module")
def journey(tmp_path_factory: pytest.TempPathFactory) -> GateJourney:
    """The one real journey: real subject, real keys, real verdicts.

    Ordered, spine-style: every stage's refusal is loud and names the
    stage, so a journey that cannot complete fails here with the CLI's
    own words instead of a dereference error in a test below.
    """

    base = tmp_path_factory.mktemp("verdict-family-gate")
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
        ("user.email", "verdict-family@example.com"),
        ("user.name", "verdict-family journey"),
    ):
        assert git(subject, "config", name, value).returncode == 0

    # --- FAIL arm: the pristine real subject, no evidence at all --------
    fail = ranex(
        subject,
        ["gate", "evaluate", "HEAD", "--repository", ".", "--approver", "reviewer"],
    )
    assert fail.returncode == 1, (
        "the no-evidence evaluation of the real landing gate must FAIL "
        f"(exit 1), got {fail.returncode}: {fail.stdout}{fail.stderr}"
    )
    assert fail.stdout.startswith("FAIL"), fail.stdout

    # --- the journey's own producer, via the real keygen CLI ------------
    generated = ranex(subject, ["keygen", "--producer", FAMILY_PRODUCER], key=key)
    assert generated.returncode == 0, generated.stderr
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", generated.stdout)
    assert match, f"keygen printed no public key: {generated.stdout!r}"
    public = match.group(1)

    keyring = subject / "governance" / "producers.yaml"
    lines = keyring.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.rstrip() == "producers:"), None)
    assert header is not None, "the committed keyring carries no producers: mapping"
    lines.insert(header + 1, f"  {FAMILY_PRODUCER}: {public}\n")
    keyring.write_text("".join(lines), encoding="utf-8")

    catalog = subject / "governance" / "gates.yaml"
    with catalog.open("a", encoding="utf-8") as file:
        file.write(
            "  - gate_id: verdict-family\n"
            "    rule_id: TESTS_EXECUTED\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: tree-clean\n"
            '        command: ["git", "status", "--porcelain"]\n'
        )

    # The self-contained subject: no committed pins file, no dependency
    # provisioning demanded — the kernel's own documented activation rule.
    removed = git(subject, "rm", "-q", "governance/deps.yaml")
    assert removed.returncode == 0, removed.stderr
    staged = git(subject, "add", "governance/producers.yaml", "governance/gates.yaml")
    assert staged.returncode == 0, staged.stderr
    committed = git(subject, "commit", "-q", "-m", "register the verdict-family producer and gate")
    assert committed.returncode == 0, committed.stderr

    # --- the real run of the bound command, then the green evaluation ---
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

    passed = ranex(
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
    assert passed.returncode == 0, (
        f"the green evaluation must exit 0: {passed.stdout}{passed.stderr}"
    )
    assert passed.stdout.startswith("PASS"), passed.stdout
    assert _DIGEST_RE.search(passed.stdout), passed.stdout

    evidence = subject / "governance" / "evidence.json"
    record = json.loads(evidence.read_text(encoding="utf-8"))[0]
    assert record["claim_id"] == FAMILY_CLAIM
    assert record["exit_code"] == 0

    # --- the subject moves on: the recorded evidence must go stale ------
    (subject / "journey-moves-on.txt").write_text(
        "the subject tree changed after the evidence was recorded\n", encoding="utf-8"
    )
    assert git(subject, "add", "journey-moves-on.txt").returncode == 0
    moved = git(subject, "commit", "-q", "-m", "the subject moves on")
    assert moved.returncode == 0, moved.stderr
    stale = ranex(
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
    assert stale.returncode == 1, (
        f"evidence bound to a moved tree must FAIL (exit 1): {stale.stdout}"
    )

    return GateJourney(
        subject=subject,
        key=key,
        public=public,
        record=record,
        fail_transcript=fail.stdout,
        pass_transcript=passed.stdout,
        stale_transcript=stale.stdout,
    )


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


def test_fail_transcript_matches_the_golden(journey: GateJourney) -> None:
    """The absence-blocks FAIL transcript, byte-frozen against its golden.

    Independent re-check first (issue #36: a non-kernel tool reads what
    the CLI reported on): the evaluation journal row the FAIL verdict
    wrote, read with the stdlib sqlite3 module — never the kernel's own
    Journal adapter — must agree with the transcript: the landing gate,
    the FAIL verdict, the approver, and both required claims honestly
    named as missing.
    """

    journal = journey.subject / "governance" / "journal.sqlite3"
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        rows = connection.execute("SELECT seq, record FROM evaluations ORDER BY seq").fetchall()
    finally:
        connection.close()
    assert rows, "the FAIL evaluation wrote no journal row"
    first = json.loads(rows[0][1])
    assert first["gate_id"] == "landing", first
    assert first["verdict"] == "FAIL", first
    assert first["approver_id"] == "reviewer", first
    missing = set(first["missing_claims"])
    assert {"tests-executed", "host-qualification"} <= missing, first

    compare_golden(journey.fail_transcript, "gate-evaluate-fail.out")


def test_pass_transcript_matches_the_golden(journey: GateJourney) -> None:
    """The real green gate's PASS transcript, byte-frozen against its golden.

    Three honesty guards ride the same test because they are this
    evidence's own contract: the independent openssl verification of the
    signature the kernel admitted, the refusal to record without a
    signing key (issue #36 sad path 5), and the stale-evidence refusal
    once the subject moves (issue #36 sad path 1, stable reason).
    """

    # --- independent re-check: openssl verifies what the kernel accepted --
    openssl = shutil.which("openssl")
    assert openssl is not None, (
        "the openssl binary is a hard requirement of this family's "
        "independent re-check (issue #36 names it): a host without it "
        "fails honestly rather than skipping green"
    )
    scratch = journey.subject.parent / "openssl-recheck"
    scratch.mkdir(exist_ok=True)
    content = {k: v for k, v in journey.record.items() if k != "signature"}
    (scratch / "payload.bin").write_bytes(signed_payload(content))
    signature = journey.record["signature"]
    assert isinstance(signature, str) and signature.startswith("ed25519:"), signature
    (scratch / "sig.bin").write_bytes(base64.b64decode(signature.removeprefix("ed25519:")))
    raw_public = journey.public.removeprefix("ed25519:")
    (scratch / "pub.der").write_bytes(_ED25519_SPKI_PREFIX + base64.b64decode(raw_public))
    verified = subprocess.run(
        [
            openssl,
            "pkeyutl",
            "-verify",
            "-pubin",
            "-keyform",
            "DER",
            "-inkey",
            str(scratch / "pub.der"),
            "-rawin",
            "-in",
            str(scratch / "payload.bin"),
            "-sigfile",
            str(scratch / "sig.bin"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert verified.returncode == 0, (
        "openssl (a non-kernel tool) refused the signature the kernel "
        f"admitted as evidence: {verified.stdout}{verified.stderr}"
    )

    # --- sad path 5: no signing key, no record, never a silent green ------
    keyless = ranex(
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
        key=None,
    )
    assert keyless.returncode == 2, (
        f"`run` without RANEX_SIGNING_KEY must refuse (exit 2): {keyless.stderr}"
    )
    assert "RANEX_SIGNING_KEY" in keyless.stderr, keyless.stderr

    # --- sad path 1: evidence bound to a moved tree FAILs, stable reason --
    assert journey.stale_transcript.startswith("FAIL"), journey.stale_transcript
    assert "different subject digest" in journey.stale_transcript, (
        "the stale-evidence refusal must keep its stable reason "
        f"('evidence bound to a different subject digest'): "
        f"{journey.stale_transcript}"
    )

    compare_golden(journey.pass_transcript, "gate-evaluate-pass.out")


def test_goldens_carry_real_volatile_material(journey: GateJourney) -> None:
    """The goldens are machine-normalized captures, not hand-sanitized text.

    Three refusals in one contract: (1) each golden carries the
    normalizer's own token exactly where the journey emits live volatile
    material — the subject digest is real, computed from the real tree,
    and the golden must show ``<DIGEST>`` where it appeared; (2) each
    golden is a fixpoint of the normalizer — re-normalizing it changes
    nothing, so any raw volatile class a hand-writer missed fails; (3) a
    golden holding the LIVE volatile bytes cannot match the normalized
    actual — demonstrated by re-substituting one live digest into the
    real golden and proving the comparison fails.
    """

    for name, transcript in (
        ("gate-evaluate-fail.out", journey.fail_transcript),
        ("gate-evaluate-pass.out", journey.pass_transcript),
    ):
        golden = golden_text(name)
        assert "<DIGEST>" in golden, (
            f"{name} carries no <DIGEST> token: the journey's subject "
            "digest is real volatile material the normalizer must have "
            "tamed — a golden without the token is hand-sanitized text, "
            "not a captured transcript"
        )
        assert _prereqs.normalize_transcript(golden) == golden, (
            f"{name} is not a normalizer fixpoint: it still contains "
            "bytes the frozen grammar would mask, which no capture "
            "piped through normalize_transcript can"
        )
        match = _DIGEST_RE.search(transcript)
        assert match, transcript
        live = match.group(0)
        doctored = golden.replace("<DIGEST>", live, 1)
        with pytest.raises(AssertionError):
            _prereqs.compare_transcript(
                _normalized(transcript), doctored, family=name.removesuffix(".out")
            )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: GateJourney) -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte
    of the expected file and the comparator must diff dirty, naming the
    family and carrying exactly the first differing hunk — never a bare
    ``assert False``."""

    for name, transcript, verdict_word in (
        ("gate-evaluate-fail.out", journey.fail_transcript, "FAIL"),
        ("gate-evaluate-pass.out", journey.pass_transcript, "PASS"),
    ):
        golden = golden_text(name)
        family = name.removesuffix(".out")
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
