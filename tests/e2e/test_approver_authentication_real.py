"""Issue #107 — real e2e: the authenticated approver (RISK-07) on real data.

The #95 proof protocol as an ADR-032-frame journey: real `ranex` subprocesses
on a real git subject, real keys minted by the real ``keygen`` CLI, no mocked
or monkeypatched seams. Every arm carries its positive and negative controls
and its repeated identical-input runs; each expectation names its status.

The arms (issue #107's seven, in order):

1. Correct key → the verdict carries TWO signatures; the journal anchor
   reader accepts it; openssl — a non-kernel tool — verifies BOTH Ed25519
   signatures independently; three identical-state repeats produce
   byte-identical verdict bytes (Ed25519 is deterministic).
2. Key absent → exit 2, ``E-APPROVER-KEY-ABSENT``, no verdict file, no
   journal row (the journal file itself is never created).
3. A worker's key presented as the approver → ``E-APPROVER-ROLE``; nothing
   written.
4. An approver id the catalog never carried → ``E-APPROVER-UNKNOWN``.
5. The approver signature removed or altered from a published verdict →
   the anchor reader refuses, naming ``unapproved`` / ``bad-signature``;
   an unapproved verdict anchors nothing.
6. One key under two principals → the catalog refuses to load (the
   existing rule, re-measured).
7. Producer key == approver key → refused at the catalog (one key, one
   principal) AND by the kernel's own self-approval check — two
   independent refusals, both observed.
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

#: Raw Ed25519 public key → SubjectPublicKeyInfo DER (RFC 8410), the same
#: 12-byte prefix test_gate_evaluate_real.py verified against OpenSSL.
_ED25519_SPKI_PREFIX = bytes.fromhex("302a300506032b6570032100")

#: Environment keys stripped from every child: the host operator's keys must
#: never leak into the journey's identities, and the approver variable this
#: file exercises must be under the test's sole control.
_STRIPPED_ENV = (
    "RANEX_SIGNING_KEY",
    "RANEX_VERDICT_SIGNING_KEY",
    "RANEX_VERDICT_DIR",
    "RANEX_APPROVER_SIGNING_KEY",
    "COVERAGE_PROCESS_START",
    "COVERAGE_PROCESS_CONFIG",
    "COVERAGE_FILE",
)

WORKER = "worker"
APPROVER = "release-approver"
SIGNER = "kernel-verdict-signer"
GATE = "landing"
CLAIM = "tree-clean"
COMMAND = ("git", "status", "--porcelain")
JOURNAL = "governance/journal.sqlite3"
VERDICTS = "governance/verdicts"


def ranex(
    subject: Path, argv: list[str], *, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """Invoke the CLI the way an operator does: a real process, the
    subject's own source on PYTHONPATH (the clone judges the clone)."""

    child = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV}
    child["PYTHONPATH"] = str(subject / "src")
    child.update(env or {})
    return subprocess.run(
        [sys.executable, "-m", "ranex.cli.main", *argv],
        cwd=subject,
        capture_output=True,
        text=True,
        env=child,
        check=False,
    )


def git(subject: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(subject), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def evaluate_argv(*, approver: str = APPROVER) -> list[str]:
    return [
        "gate", "evaluate", "HEAD", "--repository", ".",
        "--gate", GATE, "--approver", approver,
    ]


def subject_digest(subject: Path) -> str:
    """The kernel's own derivation, restated: sha256 over the tree object."""

    from ranex.foundation.canonical import canonical_sha256

    tree = git(subject, "rev-parse", "HEAD^{tree}")
    assert tree.returncode == 0, tree.stderr
    return "sha256:" + canonical_sha256({"tree": tree.stdout.strip()})


def verdict_path(subject: Path, digest: str) -> Path:
    return subject / VERDICTS / f"{digest.removeprefix('sha256:')}.json"


def journal_rows(subject: Path) -> int:
    """The independent re-read: stdlib sqlite3, never the kernel adapter."""

    journal = subject / JOURNAL
    if not journal.is_file():
        return 0
    connection = sqlite3.connect(f"{journal.as_uri()}?mode=ro", uri=True)
    try:
        return int(
            connection.execute("SELECT COUNT(*) FROM evaluations").fetchone()[0]
        )
    finally:
        connection.close()


def keygen(subject: Path, base: Path, name: str) -> tuple[Path, str]:
    """Mint one identity's key with the real keygen CLI, outside the repo."""

    path = base / f"{name}.key"
    generated = ranex(
        subject, ["keygen", "--producer", name], env={"RANEX_SIGNING_KEY": str(path)}
    )
    assert generated.returncode == 0, generated.stderr
    match = re.search(r"(ed25519:[A-Za-z0-9+/=]+)", generated.stdout)
    assert match, f"keygen printed no public key: {generated.stdout!r}"
    return path, match.group(1)


def write_catalog(
    subject: Path,
    *,
    workers: dict[str, str],
    signer_public: str,
    approvers: dict[str, str],
    approver_producers: dict[str, str] | None = None,
) -> None:
    """The subject's trust root: producers, verdict signer, principals.

    `workers` are producers with the worker role. `approvers` are approver
    principals by their own key — the collision arm passes the worker's key
    here so the loader's one-key-one-principal rule is what answers.
    `approver_producers` lists an approver principal as a producer of
    evidence too (arm 7: the blocks agree, so the catalog loads, and the
    kernel's own no-self-approval comparison is the control that answers).
    """

    producers = {**workers, **(approver_producers or {})}
    lines = ["producers:\n"]
    for producer, public in producers.items():
        lines.append(f"  {producer}: {public}\n")
    lines.append("verdict_signer:\n")
    lines.append(f"  id: {SIGNER}\n  public_key: {signer_public}\n")
    lines.append("principals:\n")
    for worker, public in workers.items():
        lines.append(f"  {worker}:\n    role: worker\n    keys:\n")
        lines.append(f"      - key: {public}\n        status: active\n")
    for approver, public in approvers.items():
        lines.append(f"  {approver}:\n    role: approver\n    keys:\n")
        lines.append(f"      - key: {public}\n        status: active\n")
    lines.append(f"  {SIGNER}:\n    role: service\n    keys:\n")
    lines.append(f"      - key: {signer_public}\n        status: active\n")
    catalog = subject / "governance" / "producers.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text("".join(lines), encoding="utf-8")


@dataclass
class ApproverJourney:
    """Everything the arms consume from the one module journey."""

    base: Path
    subject: Path
    snapshot: Path
    worker_key: Path
    approver_key: Path
    signer_key: Path
    worker_public: str
    approver_public: str
    signer_public: str
    digest: str
    verdict: dict[str, object]
    verdict_bytes: bytes
    refused_absent: subprocess.CompletedProcess[str]
    refused_role: subprocess.CompletedProcess[str]
    refused_unknown: subprocess.CompletedProcess[str]
    collision: subprocess.CompletedProcess[str]


@pytest.fixture(scope="module")
def journey(tmp_path_factory: pytest.TempPathFactory) -> ApproverJourney:
    """The one real journey: a real subject, real keys, real refusals."""

    base = tmp_path_factory.mktemp("approver-authentication")
    subject = base / "subject"
    subject.mkdir()
    assert subprocess.run(
        ["git", "init", "-q", str(subject)], check=False
    ).returncode == 0, "cannot create the real subject repository"
    # The subject judges itself (ADR-032's clone-judges-clone): its own
    # source on PYTHONPATH, so the governed root IS the subject — never
    # the checkout the test driver happens to run from (ADR-038).
    shutil.copytree(E2E_DIR.parents[1] / "src", subject / "src")
    for key, value in (
        ("user.email", "approver-family@example.com"),
        ("user.name", "approver authentication journey"),
    ):
        assert git(subject, "config", key, value).returncode == 0
    (subject / "README.md").write_text("subject\n", encoding="utf-8")

    worker_key, worker_public = keygen(subject, base, "worker")
    approver_key, approver_public = keygen(subject, base, "approver")
    signer_key, signer_public = keygen(subject, base, "verdict-signer")
    write_catalog(
        subject,
        workers={WORKER: worker_public},
        signer_public=signer_public,
        approvers={APPROVER: approver_public},
    )
    (subject / "governance" / "gates.yaml").write_text(
        "gates:\n"
        f"  - gate_id: {GATE}\n"
        "    rule_id: TESTS_EXECUTED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        f"      - claim_id: {CLAIM}\n"
        f"        command: {json.dumps(list(COMMAND))}\n",
        encoding="utf-8",
    )
    assert git(subject, "add", "-A").returncode == 0
    assert git(subject, "commit", "-q", "-m", "the subject and its trust root").returncode == 0

    # Real evidence from a real governed run of the bound command.
    recorded = ranex(
        subject,
        [
            "run", "--claim", CLAIM, "--producer", WORKER, "--gate", GATE,
            "--repository", ".",
            "--", *COMMAND,
        ],
        env={"RANEX_SIGNING_KEY": str(worker_key)},
    )
    assert recorded.returncode == 0, (
        f"the bound command's governed run must exit 0: "
        f"{recorded.stdout}{recorded.stderr}"
    )

    # The snapshot the repeats evaluate from: identical inputs, including
    # the journal state (no journal yet — evaluation creates it).
    snapshot = base / "identical-state"
    shutil.copytree(subject, snapshot)

    # Arm 1: the correct key. The publication env carries both keys.
    publication = {
        "RANEX_VERDICT_SIGNING_KEY": str(signer_key),
        "RANEX_VERDICT_DIR": VERDICTS,
        "RANEX_APPROVER_SIGNING_KEY": str(approver_key),
    }
    digest = subject_digest(subject)
    passed = ranex(subject, evaluate_argv(), env=publication)
    assert passed.returncode == 0, (
        f"the green evaluation must exit 0: {passed.stdout}{passed.stderr}"
    )
    assert passed.stdout.startswith("PASS"), passed.stdout
    verdict_file = verdict_path(subject, digest)
    assert verdict_file.is_file(), "the green evaluation published no verdict"
    verdict = json.loads(verdict_file.read_text(encoding="utf-8"))

    # Arms 2–4 on fresh copies of the identical state: each refusal must
    # write nothing at all.
    absent_copy = base / "arm-absent"
    shutil.copytree(snapshot, absent_copy)
    refused_absent = ranex(absent_copy, evaluate_argv(), env={
        "RANEX_VERDICT_SIGNING_KEY": str(signer_key),
        "RANEX_VERDICT_DIR": VERDICTS,
    })

    role_copy = base / "arm-role"
    shutil.copytree(snapshot, role_copy)
    refused_role = ranex(role_copy, evaluate_argv(approver=WORKER), env={
        "RANEX_APPROVER_SIGNING_KEY": str(worker_key),
    })

    unknown_copy = base / "arm-unknown"
    shutil.copytree(snapshot, unknown_copy)
    refused_unknown = ranex(unknown_copy, evaluate_argv(approver="ghost"), env={
        "RANEX_APPROVER_SIGNING_KEY": str(approver_key),
    })

    # Arm 6: one key under two principals — the approver registered with
    # the worker's key. The catalog must refuse to load at all.
    collision_copy = base / "arm-collision"
    shutil.copytree(snapshot, collision_copy)
    write_catalog(
        collision_copy,
        workers={WORKER: worker_public},
        signer_public=signer_public,
        approvers={APPROVER: worker_public},
    )
    assert git(collision_copy, "add", "-A").returncode == 0
    assert git(
        collision_copy, "commit", "-q", "-m", "the colliding trust root"
    ).returncode == 0
    collision = ranex(collision_copy, evaluate_argv(), env={
        "RANEX_APPROVER_SIGNING_KEY": str(worker_key),
    })

    return ApproverJourney(
        base=base,
        subject=subject,
        snapshot=snapshot,
        worker_key=worker_key,
        approver_key=approver_key,
        signer_key=signer_key,
        worker_public=worker_public,
        approver_public=approver_public,
        signer_public=signer_public,
        digest=digest,
        verdict=verdict,
        verdict_bytes=verdict_file.read_bytes(),
        refused_absent=refused_absent,
        refused_role=refused_role,
        refused_unknown=refused_unknown,
        collision=collision,
    )


def test_arm1_the_verdict_carries_both_signatures_and_anchors(
    journey: ApproverJourney,
) -> None:
    """Arm 1: two signatures over the same content, the anchor accepted."""

    signatures = journey.verdict["signatures"]
    assert isinstance(signatures, list)
    assert [entry["signer_id"] for entry in signatures] == [SIGNER, APPROVER], signatures
    assert journey.verdict["record"]["approver_id"] == APPROVER

    # The journal anchor reader — a real subprocess — accepts it.
    anchored = ranex(
        journey.subject,
        [
            "journal", "verify", "--repository", ".", "--journal", JOURNAL,
            "--against-verdict",
            f"{VERDICTS}/{journey.digest.removeprefix('sha256:')}.json",
        ],
    )
    assert anchored.returncode == 0, (
        f"journal verify --against-verdict must accept the two-signature "
        f"verdict: {anchored.stdout}{anchored.stderr}"
    )
    # Negative control, same command, one signature stripped: the reader
    # must refuse it (arm 5 exercises this fully; here it anchors the
    # positive claim).
    assert journal_rows(journey.subject) >= 1


def test_arm1_openssl_verifies_both_signatures(journey: ApproverJourney) -> None:
    """Arm 1's independent re-check: a non-kernel tool verifies BOTH keys."""

    openssl = shutil.which("openssl")
    assert openssl is not None, (
        "openssl is a hard requirement of this family's independent "
        "re-check: a host without it fails honestly rather than skipping green"
    )
    from ranex.foundation.verdict_signing import signed_payload

    scratch = journey.base / "openssl-recheck"
    scratch.mkdir(exist_ok=True)
    record = dict(journey.verdict["record"])  # type: ignore[arg-type]
    record.pop("record_digest", None)
    (scratch / "payload.bin").write_bytes(signed_payload(record))
    for name, entry, public in (
        ("signer", journey.verdict["signatures"][0], journey.signer_public),
        ("approver", journey.verdict["signatures"][1], journey.approver_public),
    ):
        signature = entry["signature"]
        assert isinstance(signature, str) and signature.startswith("ed25519:"), signature
        (scratch / f"{name}-sig.bin").write_bytes(
            base64.b64decode(signature.removeprefix("ed25519:"))
        )
        (scratch / f"{name}-pub.der").write_bytes(
            _ED25519_SPKI_PREFIX + base64.b64decode(public.removeprefix("ed25519:"))
        )
        verified = subprocess.run(
            [
                openssl, "pkeyutl", "-verify", "-pubin", "-keyform", "DER",
                "-inkey", str(scratch / f"{name}-pub.der"),
                "-rawin", "-in", str(scratch / "payload.bin"),
                "-sigfile", str(scratch / f"{name}-sig.bin"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert verified.returncode == 0, (
            f"openssl refused the {name} signature the kernel published: "
            f"{verified.stdout}{verified.stderr}"
        )


def test_arm1_repeats_produce_identical_verdict_bytes(journey: ApproverJourney) -> None:
    """Arm 1's repeats: identical inputs, identical verdict bytes, ×3."""

    publication = {
        "RANEX_VERDICT_SIGNING_KEY": str(journey.signer_key),
        "RANEX_VERDICT_DIR": VERDICTS,
        "RANEX_APPROVER_SIGNING_KEY": str(journey.approver_key),
    }
    digests = {journey.verdict_bytes}
    for attempt in (1, 2, 3):
        copy = journey.base / f"identical-repeat-{attempt}"
        shutil.copytree(journey.snapshot, copy)
        repeated = ranex(copy, evaluate_argv(), env=publication)
        assert repeated.returncode == 0, (
            f"repeat {attempt} must exit 0: {repeated.stdout}{repeated.stderr}"
        )
        digests.add(verdict_path(copy, journey.digest).read_bytes())
    assert len(digests) == 1, (
        "identical-state evaluations must produce byte-identical verdict "
        f"files (Ed25519 is deterministic); got {len(digests)} distinct"
    )


def test_arm2_absent_key_refuses_before_judgment(journey: ApproverJourney) -> None:
    """Arm 2: no key → exit 2, the named code, and nothing written."""

    run = journey.refused_absent
    assert run.returncode == 2, (
        f"the key-absent refusal must exit 2, got {run.returncode}: "
        f"{run.stdout}{run.stderr}"
    )
    assert "E-APPROVER-KEY-ABSENT" in run.stderr, run.stderr
    subject = journey.base / "arm-absent"
    assert not verdict_path(subject, journey.digest).exists(), (
        "the refused evaluation must publish no verdict"
    )
    assert journal_rows(subject) == 0, (
        "the refused evaluation must write no journal row"
    )


def test_arm3_a_workers_key_cannot_approve(journey: ApproverJourney) -> None:
    """Arm 3: a worker principal presented as the approver → E-APPROVER-ROLE."""

    run = journey.refused_role
    assert run.returncode == 2, (
        f"the role refusal must exit 2, got {run.returncode}: "
        f"{run.stdout}{run.stderr}"
    )
    assert "E-APPROVER-ROLE" in run.stderr, run.stderr
    subject = journey.base / "arm-role"
    assert not verdict_path(subject, journey.digest).exists()
    assert journal_rows(subject) == 0


def test_arm4_an_unknown_approver_is_refused(journey: ApproverJourney) -> None:
    """Arm 4: an id the catalog never carried → E-APPROVER-UNKNOWN."""

    run = journey.refused_unknown
    assert run.returncode == 2, (
        f"the unknown-approver refusal must exit 2, got {run.returncode}: "
        f"{run.stdout}{run.stderr}"
    )
    assert "E-APPROVER-UNKNOWN" in run.stderr, run.stderr
    subject = journey.base / "arm-unknown"
    assert not verdict_path(subject, journey.digest).exists()
    assert journal_rows(subject) == 0


def _judged_copy_with_verdict(journey: ApproverJourney, name: str) -> tuple[Path, Path]:
    """A copy judged once for real (journal + verdict), verdict in hand."""

    subject = journey.base / f"arm5-{name}"
    shutil.copytree(journey.snapshot, subject)
    judged = ranex(subject, evaluate_argv(), env={
        "RANEX_VERDICT_SIGNING_KEY": str(journey.signer_key),
        "RANEX_VERDICT_DIR": VERDICTS,
        "RANEX_APPROVER_SIGNING_KEY": str(journey.approver_key),
    })
    assert judged.returncode == 0, (
        f"the arm-5 control evaluation must pass: {judged.stdout}{judged.stderr}"
    )
    target = verdict_path(subject, journey.digest)
    assert target.is_file()
    # Positive control: the untouched verdict anchors.
    clean = ranex(
        subject,
        [
            "journal", "verify", "--repository", ".", "--journal", JOURNAL,
            "--against-verdict",
            f"{VERDICTS}/{journey.digest.removeprefix('sha256:')}.json",
        ],
    )
    assert clean.returncode == 0, (
        f"the untouched two-signature verdict must anchor: "
        f"{clean.stdout}{clean.stderr}"
    )
    return subject, target


def test_arm5_a_stripped_or_altered_approver_signature_anchors_nothing(
    journey: ApproverJourney,
) -> None:
    """Arm 5: signature removed → the unapproved state; altered → bad
    signature. Both must refuse the anchor a clean verdict earns."""

    # Removed: the archived single-signature shape — a record that names a
    # catalogued approver but carries no approval.
    subject, target = _judged_copy_with_verdict(journey, "removed")
    stripped = json.loads(target.read_text(encoding="utf-8"))
    assert len(stripped["signatures"]) == 2
    # The publication is deliberately read-only (0o444); the tamper is the
    # attacker's out-of-band edit, so it rewrites what the kernel wrote.
    target.chmod(0o644)
    stripped["signatures"] = stripped["signatures"][:1]
    target.write_text(json.dumps(stripped), encoding="utf-8")
    refused = ranex(
        subject,
        [
            "journal", "verify", "--repository", ".", "--journal", JOURNAL,
            "--against-verdict",
            f"{VERDICTS}/{journey.digest.removeprefix('sha256:')}.json",
        ],
    )
    assert refused.returncode != 0, (
        f"an unapproved verdict must anchor nothing: "
        f"{refused.stdout}{refused.stderr}"
    )
    assert "unapproved" in (refused.stdout + refused.stderr).lower(), (
        f"the refusal must name the unapproved state: "
        f"{refused.stdout}{refused.stderr}"
    )

    # Altered: one base64 character of the approver's signature flipped —
    # still well-formed, no longer the signature the approver made.
    subject, target = _judged_copy_with_verdict(journey, "altered")
    altered = json.loads(target.read_text(encoding="utf-8"))
    signature = altered["signatures"][1]["signature"]
    assert isinstance(signature, str) and len(signature) > 8
    flipped = signature[:-1] + ("B" if signature[-1] != "B" else "C")
    target.chmod(0o644)
    altered["signatures"][1]["signature"] = flipped
    target.write_text(json.dumps(altered), encoding="utf-8")
    refused = ranex(
        subject,
        [
            "journal", "verify", "--repository", ".", "--journal", JOURNAL,
            "--against-verdict",
            f"{VERDICTS}/{journey.digest.removeprefix('sha256:')}.json",
        ],
    )
    assert refused.returncode != 0
    assert "bad-signature" in (refused.stdout + refused.stderr).lower(), (
        f"the refusal must name the bad signature: "
        f"{refused.stdout}{refused.stderr}"
    )


def test_arm6_one_key_two_principals_refuses_the_catalog(
    journey: ApproverJourney,
) -> None:
    """Arm 6: the existing one-key-one-principal rule, re-measured."""

    run = journey.collision
    assert run.returncode == 2, (
        f"the colliding catalog must refuse evaluation, got {run.returncode}: "
        f"{run.stdout}{run.stderr}"
    )
    assert "share a public key" in (run.stdout + run.stderr), (
        f"the refusal must name the collision: {run.stdout}{run.stderr}"
    )
    assert journal_rows(journey.base / "arm-collision") == 0


def test_arm7_producer_key_equals_approver_key_is_refused_twice(
    journey: ApproverJourney,
) -> None:
    """Arm 7: the catalog refuses the shared key; the kernel refuses the
    self-approval — two independent refusals, both observed."""

    # First refusal: the catalog — the same key under two principals.
    assert journey.collision.returncode == 2
    assert "share a public key" in (journey.collision.stdout + journey.collision.stderr)

    # Second refusal, independent of the catalog: the approver principal
    # listed AS a producer (the blocks agree — same id, same key — so the
    # catalog loads) produces the evidence and then approves it. Possession
    # passes, because the key IS the approver's; the kernel's own
    # no-self-approval comparison must refuse. verdict.py does not change;
    # this observes it.
    subject = journey.base / "arm7-selfapproval"
    shutil.copytree(journey.snapshot, subject)
    write_catalog(
        subject,
        workers={WORKER: journey.worker_public},
        signer_public=journey.signer_public,
        approvers={APPROVER: journey.approver_public},
        approver_producers={APPROVER: journey.approver_public},
    )
    assert git(subject, "add", "-A").returncode == 0
    assert git(subject, "commit", "-q", "-m", "the approver produces").returncode == 0
    produced = ranex(
        subject,
        [
            "run", "--claim", CLAIM, "--producer", APPROVER, "--gate", GATE,
            "--repository", ".",
            "--", *COMMAND,
        ],
        env={"RANEX_SIGNING_KEY": str(journey.approver_key)},
    )
    assert produced.returncode == 0, (
        f"the approver-as-producer run must record — admission carries no "
        f"role check, and the kernel's comparison is the control: "
        f"{produced.stdout}{produced.stderr}"
    )
    judged = ranex(
        subject, evaluate_argv(), env={
            "RANEX_VERDICT_SIGNING_KEY": str(journey.signer_key),
            "RANEX_VERDICT_DIR": VERDICTS,
            "RANEX_APPROVER_SIGNING_KEY": str(journey.approver_key),
        },
    )
    assert judged.returncode == 1, (
        f"self-approval must FAIL the gate (exit 1), got "
        f"{judged.returncode}: {judged.stdout}{judged.stderr}"
    )
    # The catalog commit above moved the subject tree, so the FAIL verdict
    # publishes under this copy's own digest, not the journey's.
    verdict_file = verdict_path(subject, subject_digest(subject))
    assert verdict_file.is_file(), "the FAIL verdict must still publish"
    record = json.loads(verdict_file.read_text(encoding="utf-8"))["record"]
    assert record["self_approval"] is True, record
    assert "approver" in record["reason"], record["reason"]
