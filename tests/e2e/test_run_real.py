"""SLICE-057 — real e2e: the execution family (run) on real data.

Issue #37's exact ownership (file 1 of 3). The execution family rides the
ADR-032 frame (docs/adr/ADR-032-real-e2e-suite-framework.md), following the
SLICE-056 verdict-family pattern: real journeys — a real git subject, real
ranex keys via the real ``keygen`` CLI, real ``run`` subprocess spines —
whose captured transcripts compare byte-exactly against golden ``.out``
files through the ONE centralized normalizer
(``_prereqs.normalize_transcript``). No per-family masks exist and none
may be added: over-masking is a reviewed golden edit (ADR-032 sad path
11), never a comparator hack.

The journey (every command below was verified against the installed
kernel at e84b5176a in a /tmp/opencode prototype before this file was
frozen — the prototype is the freeze-time evidence, not an assumption):

* **The run arm** — this repository cloned at HEAD, the journey's
  ``keygen``-generated producer registered in the committed keyring, a
  family gate (``execution-family``) whose single claim binds
  ``git status --porcelain`` (the SLICE-056 spine's pattern: a real
  command that really runs and attests something true), and
  ``governance/deps.yaml`` removed so the subject keeps the kernel's
  documented self-contained behaviour (cmd ``_provisioning_for``) — the
  family runs anywhere with git and python, sealed env included. The real
  ``run`` of the bound command records real signed evidence whose
  ``RECORDED`` transcript freezes against ``expected/run-evidence.out``.
* **The sabotage arms** (issue #37 deterministic gate 2, AC3, sad path
  4) — post-run evidence tampering: the evidence file REMOVED after the
  run makes the evaluation FAIL honestly (absence blocks), and evidence
  produced by a real run of a DIFFERENT subject, swapped in between run
  and verify, is refused by the subject-digest binding with the stable
  reason ``evidence bound to a different subject digest``.
* **The traced-run arm** (AC2, sad path 7; the SLICE-054 invariance
  contract reused) — one full traced run with ``RANEX_TRACE_EVENT=1``
  whose stderr event stream IS an asserted artifact: version-first,
  carrying the run group's stage events (``cli.run.start`` /
  ``cli.run.end`` with ``exit:0``). A file target outside every governed
  root additionally proves verdict neutrality: the run's stdout stays
  byte-identical to the untraced baseline, its stderr stays byte-empty
  (the stream belongs to the governed command), and the evidence file's
  bytes are identical traced vs untraced.

Independent re-checks (issue #37's real-data rule): the record's subject
digest is recomputed with the stdlib ``json`` + ``hashlib`` modules over
``git rev-parse HEAD^{tree}`` — no kernel import — and openssl (a
non-kernel tool) verifies the Ed25519 signature the kernel admitted,
over the payload bytes the repo's own ``signed_payload`` builds (the
serialization is shared vocabulary; the cryptography is independent).

The golden ``expected/run-evidence.out`` is the implementation lane's
artifact, captured from a real run of this journey (stdout piped through
the normalizer exactly as the tests do it); its absence is this file's
honest frozen red. The sabotage control and the normalizer-application
contract refuse every hand-sanitized golden shape.

The family declares no expected skips: git and python are hard tool
requirements of the whole e2e lane, and openssl is a hard requirement of
this file's independent re-check. A host missing a required tool fails
honestly; it does not skip green.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
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
FAMILY_PRODUCER = "execution-family"
FAMILY_GATE = "execution-family"
FAMILY_CLAIM = "tree-clean"
FAMILY_COMMAND = ("git", "status", "--porcelain")

#: Raw Ed25519 public key → SubjectPublicKeyInfo DER: the 12-byte SPKI
#: header for an Ed25519 point (RFC 8410), verified against the installed
#: OpenSSL in the freeze-time journey prototype (SLICE-056's constant).
_ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

_DIGEST_RE = re.compile(r"sha256:[0-9a-f]{64}")

#: Environment keys stripped from every child: the signing variables (a
#: host's operator key must not leak into the journey's producer
#: identity, and a stray verdict-publication pair would change the
#: evaluate transcript), the coverage switches (the frame's sanctioned
#: unwired-children rule), and the trace variables (the off-state
#: baseline must be genuinely off; the traced arms set their own).
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
    subject: Path, argv: list[str], key: Path | None = None, extra_env: dict[str, str] | None = None
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

    The three SLICE-057 goldens are the implementation lane's artifacts,
    captured from real runs of these exact journeys (transcripts piped
    through ``_prereqs.normalize_transcript``). A missing golden is this
    file's frozen red — the honest one — until that capture lands.
    """

    path = EXPECTED / name
    assert path.is_file(), (
        f"the golden {path} does not exist yet. It is the SLICE-057 "
        "implementation lane's artifact: capture it from a real run of "
        "this journey (the fixture above), pipe the CLI stdout through "
        "_prereqs.normalize_transcript exactly as the tests do, and "
        "commit the bytes. A hand-written golden cannot pass the "
        "sabotage control or the normalizer-application contracts in "
        "this file."
    )
    return path.read_text(encoding="utf-8")


def _register_family_gate(subject: Path, producer: str, public: str) -> None:
    """Register the journey's producer and gate in the committed tree."""

    keyring = subject / "governance" / "producers.yaml"
    lines = keyring.read_text(encoding="utf-8").splitlines(keepends=True)
    header = next((i for i, line in enumerate(lines) if line.rstrip() == "producers:"), None)
    assert header is not None, "the committed keyring carries no producers: mapping"
    lines.insert(header + 1, f"  {producer}: {public}\n")
    keyring.write_text("".join(lines), encoding="utf-8")

    with (subject / "governance" / "gates.yaml").open("a", encoding="utf-8") as file:
        file.write(
            "  - gate_id: execution-family\n"
            "    rule_id: TESTS_EXECUTED\n"
            "    blocking: true\n"
            "    required_claims:\n"
            "      - claim_id: tree-clean\n"
            '        command: ["git", "status", "--porcelain"]\n'
        )


def subject_digest_by_stdlib(subject: Path) -> str:
    """Recompute the subject digest with the stdlib alone — no kernel
    import — over the canonical JSON body the kernel digests."""

    tree = subprocess.run(
        ["git", "-C", str(subject), "rev-parse", "HEAD^{tree}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    body = json.dumps({"tree": tree}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(body).hexdigest()


@dataclass
class RunJourney:
    """Everything the frozen tests consume from the one module journey."""

    subject: Path
    key: Path
    public: str
    record: dict[str, object]
    baseline_run: subprocess.CompletedProcess[str]
    baseline_evidence: bytes
    removed_transcript: str
    swapped_transcript: str
    traced_run: subprocess.CompletedProcess[str]
    trace_events: list[dict]
    filed_run: subprocess.CompletedProcess[str]
    filed_events: list[dict]


@pytest.fixture(scope="module")
def journey(tmp_path_factory: pytest.TempPathFactory) -> RunJourney:
    """The one real journey: real subject, real keys, real sabotage.

    Ordered, spine-style: every stage's refusal is loud and names the
    stage, so a journey that cannot complete fails here with the CLI's
    own words instead of a dereference error in a test below.
    """

    base = tmp_path_factory.mktemp("execution-family-run")
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
        ("user.email", "execution-family@example.com"),
        ("user.name", "execution-family journey"),
    ):
        assert git(subject, "config", name, value).returncode == 0

    # --- the journey's own producer, via the real keygen CLI ------------
    generated = ranex(subject, ["keygen", "--producer", FAMILY_PRODUCER], key=key)
    assert generated.returncode == 0, generated.stderr
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", generated.stdout)
    assert match, f"keygen printed no public key: {generated.stdout!r}"
    public = match.group(1)

    _register_family_gate(subject, FAMILY_PRODUCER, public)

    # The self-contained subject: no committed pins file, no dependency
    # provisioning demanded — the kernel's own documented activation rule.
    removed = git(subject, "rm", "-q", "governance/deps.yaml")
    assert removed.returncode == 0, removed.stderr
    staged = git(subject, "add", "governance/producers.yaml", "governance/gates.yaml")
    assert staged.returncode == 0, staged.stderr
    committed = git(subject, "commit", "-q", "-m", "register the execution-family producer and gate")
    assert committed.returncode == 0, committed.stderr

    run_argv = [
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
    ]

    def spine(extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return ranex(subject, run_argv, key=key, extra_env=extra_env)

    # --- the untraced baseline: stdout + evidence bytes ------------------
    baseline = spine()
    assert baseline.returncode == 0, (
        f"the bound command's governed run must exit 0: {baseline.stderr}"
    )
    assert baseline.stdout.startswith("RECORDED"), baseline.stdout
    baseline_evidence = (subject / "governance" / "evidence.json").read_bytes()
    record = json.loads(baseline_evidence)[0]
    assert record["claim_id"] == FAMILY_CLAIM
    assert record["exit_code"] == 0

    # --- sabotage arm 1: evidence REMOVED post-run ----------------------
    evidence_path = subject / "governance" / "evidence.json"
    evidence_path.unlink()
    removed_eval = ranex(
        subject,
        ["gate", "evaluate", "HEAD", "--repository", ".", "--gate", FAMILY_GATE,
         "--approver", "reviewer"],
    )
    assert removed_eval.returncode == 1, (
        f"the no-evidence evaluation must FAIL (exit 1): "
        f"{removed_eval.stdout}{removed_eval.stderr}"
    )
    assert removed_eval.stdout.startswith("FAIL"), removed_eval.stdout
    assert "no evidence for required claim" in removed_eval.stdout, removed_eval.stdout

    # --- sabotage arm 2: evidence SWAPPED between two real subjects -----
    other = base / "other-subject"
    subprocess.run(["git", "clone", "-q", str(REAL_REPO), str(other)], check=True)
    for name, value in (
        ("user.email", "other-subject@example.com"),
        ("user.name", "execution-family other subject"),
    ):
        subprocess.run(["git", "-C", str(other), "config", name, value], check=True)
    _register_family_gate(other, FAMILY_PRODUCER, public)
    subprocess.run(["git", "-C", str(other), "rm", "-q", "governance/deps.yaml"], check=True)
    (other / "a-different-tree.txt").write_text(
        "the other subject's tree differs from the first\n", encoding="utf-8"
    )
    subprocess.run(["git", "-C", str(other), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(other), "commit", "-q", "-m", "the other subject"],
        check=True,
    )
    other_run = ranex(other, run_argv, key=key)
    assert other_run.returncode == 0, (
        f"the other subject's governed run must exit 0: {other_run.stderr}"
    )
    shutil.copy(other / "governance" / "evidence.json", evidence_path)
    swapped_eval = ranex(
        subject,
        ["gate", "evaluate", "HEAD", "--repository", ".", "--gate", FAMILY_GATE,
         "--approver", "reviewer"],
    )
    assert swapped_eval.returncode == 1, (
        "swapped evidence must FAIL the evaluation (exit 1): "
        f"{swapped_eval.stdout}{swapped_eval.stderr}"
    )
    assert "evidence bound to a different subject digest" in swapped_eval.stdout, (
        "the subject-digest binding must keep its stable refusal reason: "
        f"{swapped_eval.stdout}"
    )

    # --- traced arm 1: RANEX_TRACE_EVENT=1, the stderr event stream -----
    traced = spine({"RANEX_TRACE_EVENT": "1"})
    assert traced.returncode == baseline.returncode, traced.stderr
    assert traced.stdout == baseline.stdout, "tracing changed the run's stdout"
    trace_events = [
        json.loads(line)
        for line in traced.stderr.splitlines()
        if line.strip()
    ]
    assert trace_events, "an admitted stderr target must receive events"
    assert trace_events[0]["event"] == "version", trace_events[:1]
    stages = [(event["event"], event["stage"]) for event in trace_events]
    assert ("stage", "cli.run.start") in stages, stages
    assert ("stage", "cli.run.end") in stages, stages
    ends = [e for e in trace_events if e["event"] == "stage" and e["stage"] == "cli.run.end"]
    assert all(e.get("code") == "exit:0" for e in ends), ends

    # --- traced arm 2: file target outside every governed root -----------
    trace_path = base / "trace.jsonl"
    filed = spine({"RANEX_TRACE": str(trace_path), "RANEX_TRACE_EVENT": str(trace_path)})
    assert filed.returncode == baseline.returncode, filed.stderr
    assert filed.stdout == baseline.stdout, "a trace target changed the run's stdout"
    assert filed.stderr == "", (
        f"a valid off-stderr trace target leaked onto the run's stderr: {filed.stderr!r}"
    )
    assert trace_path.is_file(), "an admitted file target must receive the stream"
    filed_events = [
        json.loads(line)
        for line in trace_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert filed_events and filed_events[0]["event"] == "version", filed_events[:1]
    assert any(e["event"] == "stage" and e["stage"] == "cli.run.start" for e in filed_events)
    assert any(e["event"] == "stage" and e["stage"] == "cli.run.end" for e in filed_events)
    assert (subject / "governance" / "evidence.json").read_bytes() == baseline_evidence, (
        "tracing must leave the evidence bytes identical to the untraced baseline"
    )

    return RunJourney(
        subject=subject,
        key=key,
        public=public,
        record=record,
        baseline_run=baseline,
        baseline_evidence=baseline_evidence,
        removed_transcript=removed_eval.stdout,
        swapped_transcript=swapped_eval.stdout,
        traced_run=traced,
        trace_events=trace_events,
        filed_run=filed,
        filed_events=filed_events,
    )


def _normalized(transcript: str) -> str:
    return _prereqs.normalize_transcript(transcript)


def compare_golden(transcript: str, name: str) -> None:
    """Compare one journey transcript against its family golden."""

    _prereqs.compare_transcript(
        _normalized(transcript), golden_text(name), family=name.removesuffix(".out")
    )


def test_run_transcript_matches_the_golden(journey: RunJourney) -> None:
    """The RECORDED transcript, byte-frozen against its golden.

    Independent re-checks first (issue #37: real data, independently
    re-checkable): the stdlib recomputes the subject digest the record
    claims to be bound to, and openssl verifies the Ed25519 signature the
    kernel admitted. Only then does the transcript compare.
    """

    record = journey.record
    assert record["subject_digest"] == subject_digest_by_stdlib(journey.subject), (
        "the record's subject digest must equal the pure-stdlib recompute — "
        "the digest binding is the contract, not the kernel's word for it"
    )

    openssl = shutil.which("openssl")
    assert openssl is not None, (
        "the openssl binary is a hard requirement of this family's "
        "independent re-check: a host without it fails honestly rather "
        "than skipping green"
    )
    scratch = journey.subject.parent / "openssl-recheck"
    scratch.mkdir(exist_ok=True)
    content = {k: v for k, v in record.items() if k != "signature"}
    (scratch / "payload.bin").write_bytes(signed_payload(content))
    signature = record["signature"]
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

    compare_golden(journey.baseline_run.stdout, "run-evidence.out")


def test_post_run_sabotage_controls_refuse(journey: RunJourney) -> None:
    """Issue #37 deterministic gate 2 / AC3 / sad path 4: post-run
    tampering with the evidence never converts into a pass.

    Both refusals were produced by the journey against real subjects:
    removal (absence blocks — the FAIL names the missing claim) and the
    swap between two real subjects (the subject-digest binding refuses
    with its stable reason). Both transcripts must start FAIL and name
    their cause; both are part of the red output the implementation lane
    posts on issue #37 for AC3.
    """

    assert journey.removed_transcript.startswith("FAIL"), journey.removed_transcript
    assert "no evidence for required claim: tree-clean" in journey.removed_transcript
    assert journey.swapped_transcript.startswith("FAIL"), journey.swapped_transcript
    assert "evidence bound to a different subject digest" in journey.swapped_transcript


def test_traced_run_is_an_artifact_and_verdict_neutral(journey: RunJourney) -> None:
    """AC2: the traced run's event stream is an asserted artifact, and
    tracing is verdict-neutral over the evidence (SLICE-054's contract,
    re-asserted here per issue #37 sad path 7).

    The stderr arm (``RANEX_TRACE_EVENT=1``) proves the stream's shape:
    version-first, one SID for the whole run, the run group's start/end
    stage events with the honest exit code. The file arm proves the
    neutrality the issue demands: stdout byte-identical, stderr
    byte-empty, evidence bytes identical to the untraced baseline.
    """

    sids = {event["sid"] for event in journey.trace_events}
    assert len(sids) == 1, (
        f"one traced CLI process must carry one SID: {sorted(sids)[:3]}"
    )
    assert journey.trace_events[0]["event"] == "version"
    assert journey.filed_events[0]["event"] == "version"
    assert journey.traced_run.stderr != "", "the stderr arm must carry the event stream"
    assert journey.baseline_run.stderr == "", (
        "the untraced baseline must stay byte-empty on stderr — the "
        "neutrality comparison is against a genuinely off-state run"
    )
    assert journey.filed_run.stdout == journey.baseline_run.stdout
    assert (
        journey.subject / "governance" / "evidence.json"
    ).read_bytes() == journey.baseline_evidence


def test_goldens_carry_real_volatile_material(journey: RunJourney) -> None:
    """The golden is a machine-normalized capture, not hand-sanitized
    text: it carries the normalizer's own token where the journey emits
    live volatile material (the subject digest is real, computed from the
    real tree), it is a fixpoint of the normalizer, and a golden holding
    the LIVE volatile bytes provably cannot match.
    """

    name = "run-evidence.out"
    transcript = journey.baseline_run.stdout
    golden = golden_text(name)
    assert "<DIGEST>" in golden, (
        f"{name} carries no <DIGEST> token: the journey's subject digest "
        "is real volatile material the normalizer must have tamed — a "
        "golden without the token is hand-sanitized text, not a captured "
        "transcript"
    )
    assert _prereqs.normalize_transcript(golden) == golden, (
        f"{name} is not a normalizer fixpoint: it still contains bytes "
        "the frozen grammar would mask, which no capture piped through "
        "normalize_transcript can"
    )
    match = _DIGEST_RE.search(transcript)
    assert match, transcript
    doctored = golden.replace("<DIGEST>", match.group(0), 1)
    with pytest.raises(AssertionError):
        _prereqs.compare_transcript(
            _normalized(transcript), doctored, family=name.removesuffix(".out")
        )


def test_sabotage_control_mutated_golden_diffs_dirty(journey: RunJourney) -> None:
    """ADR-032's red control, frozen per golden: mutate a meaningful byte
    of the expected file and the comparator must diff dirty, naming the
    family and carrying exactly the first differing hunk — never a bare
    ``assert False``."""

    name = "run-evidence.out"
    transcript = journey.baseline_run.stdout
    verdict_word = "RECORDED"
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
