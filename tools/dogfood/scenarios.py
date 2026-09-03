"""Dogfood scenarios: each one exercises a REAL ranex capability and asserts
the behaviour the source actually implements. No scenario touches the working
tree, the committed governance state, or the network (unless flagged).

Every scenario returns a facts dict on success and raises AssertionError (or
the kernel's own refusal ValueError) on failure — so a capability regression
fails the dogfood run rather than silently passing.
"""

from __future__ import annotations

import os
import json
import subprocess
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ranex.foundation.canonical import command_digest
from ranex.foundation.signing import (
    SIGNED_FIELDS,
    generate_keypair,
    public_key_for,
    sign_evidence,
    verify_evidence,
)
from ranex.foundation.suite_results import (
    freeze_manifest,
    suite_results_from_junitxml,
)
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain import admission
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    Verdict,
    evaluate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Context:
    repo_root: Path
    scratch: Path

    def ranex(self, *args: str, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [sys.executable, "-m", "ranex.cli.main", *args],
            cwd=self.repo_root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )


Scenario = Callable[[Context], dict[str, Any]]


def _record(producer: str, claim_id: str, subject: str, digest: str, exit_code: int, key: str) -> dict[str, Any]:
    """A closed, correctly signed evidence record built against the live
    SIGNED_FIELDS constant, so it stays valid if the field set changes."""
    content: dict[str, Any] = {field: None for field in SIGNED_FIELDS}
    content.update(
        {
            "claim_id": claim_id,
            "subject_digest": subject,
            "producer_id": producer,
            "command": "pytest -q",
            "command_digest": digest,
            "executable_path": "/usr/bin/pytest",
            "exit_code": exit_code,
        }
    )
    return {**content, "signature": sign_evidence(content, key)}


# --------------------------------------------------------------------------
# CLI-level scenarios (subprocess against the real installed entry module)
# --------------------------------------------------------------------------


def cli_surface(ctx: Context) -> dict[str, Any]:
    """Every command path in capabilities.json must be accepted by the parser."""
    import json

    catalog = json.loads((Path(__file__).parent / "capabilities.json").read_text())
    paths = [cmd for area in catalog["areas"] if area["id"] == "cli" for cmd in area["commands"]]
    assert paths, "cli area missing from capabilities catalog"
    for path in paths:
        result = ctx.ranex(*path, "--help")
        assert result.returncode == 0, (
            f"ranex {' '.join(path)} --help exited {result.returncode}: {result.stderr.strip()}"
        )
    return {"commands_verified": len(paths)}


def keygen_roundtrip(ctx: Context) -> dict[str, Any]:
    """keygen writes a fresh keypair outside the repository; the private key
    derives the same public key it reports. Key material is RANDOM by design,
    so only the behavioural facts are recorded — never key bytes."""
    key_path = ctx.scratch / "keys" / "dogfood.key"
    result = ctx.ranex("keygen", "--producer", "dogfood-producer",
                       env_extra={"RANEX_SIGNING_KEY": str(key_path)})
    assert result.returncode == 0, f"keygen failed: {result.stderr.strip()}"
    assert key_path.is_file(), "key file not created"
    private = key_path.read_text().strip()
    assert public_key_for(private).startswith("ed25519:")
    # Second run must refuse: silently replacing a key orphans its records.
    again = ctx.ranex("keygen", "--producer", "dogfood-producer",
                      env_extra={"RANEX_SIGNING_KEY": str(key_path)})
    assert again.returncode != 0 and "refusing to overwrite" in again.stderr, (
        "keygen did not refuse to overwrite an existing key"
    )
    return {"created": True, "overwrite_refused": True}


def keygen_refuses_repo_paths(ctx: Context) -> dict[str, Any]:
    """Private keys must never be committable: a RANEX_SIGNING_KEY inside the
    repository is refused, not obeyed."""
    inside = ctx.repo_root / ".local" / "dogfood-inside.key"
    result = ctx.ranex("keygen", "--producer", "dogfood-producer",
                       env_extra={"RANEX_SIGNING_KEY": str(inside)})
    assert result.returncode != 0, "keygen accepted a repository-committable key path"
    assert "refusing" in result.stderr, f"refusal not explained: {result.stderr.strip()}"
    assert not inside.exists(), "key was written despite the refusal"
    return {"refused_path": str(inside.relative_to(ctx.repo_root))}


# --------------------------------------------------------------------------
# Kernel-level scenarios (in-process, against the real kernel modules)
# --------------------------------------------------------------------------


def _evaluation() -> Any:
    """One real kernel Evaluation (an absent-claim FAIL) to journal."""
    digest = "sha256:" + "c" * 64
    claim = Claim(claim_id="tests-executed", command_digest=digest)
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)
    return evaluate(gate, (), subject_digest="sha256:" + "a" * 64,
                    approver_id="dogfood-approver")


def journal_chain(ctx: Context) -> dict[str, Any]:
    """The journal hash-chains real Evaluation records and verifies its chain."""
    journal = Journal(ctx.scratch / "journal.sqlite3")
    journal.append(_evaluation())
    head1 = journal.head()
    journal.append(_evaluation())
    assert journal.verify(), "fresh journal failed verification"
    assert journal.head() not in (None, head1), "head did not advance after appends"
    return {"rows": 2, "verified": True}


def journal_tamper_detected(ctx: Context) -> dict[str, Any]:
    """An out-of-band edit of a record to DIFFERENT VALID JSON (bypassing the
    triggers) must be detected by verify() -> False, per the documented
    contract. Non-JSON corruption is covered separately."""
    path = ctx.scratch / "tampered.sqlite3"
    journal = Journal(path)
    journal.append(_evaluation())
    conn = sqlite3.connect(path)
    try:
        try:
            conn.execute("UPDATE evaluations SET record = 'forged'")
            raise AssertionError("UPDATE trigger did not abort an edit")
        except sqlite3.IntegrityError:
            pass
        conn.execute("DROP TRIGGER evaluations_no_update")
        row = conn.execute("SELECT record FROM evaluations").fetchone()
        forged = json.dumps({**json.loads(row[0]), "tampered": True}, sort_keys=True)
        conn.execute("UPDATE evaluations SET record = ?", (forged,))
        conn.commit()
    finally:
        conn.close()
    assert not journal.verify(), "verify() accepted an out-of-band edit"
    return {"trigger_refused_update": True, "tamper_detected": True}


def journal_nonjson_corruption_fails_closed(ctx: Context) -> dict[str, Any]:
    """FINDING F-001: verify()'s docstring says "False means a row changed
    outside append", but a record corrupted to non-JSON raises
    JSONDecodeError instead of returning False (journal.py:176 json.loads).
    It fails CLOSED — the corruption is never accepted — so this is an API
    contract weak point, not a security hole. This scenario pins the ACTUAL
    behaviour so a future fix is noticed as drift."""
    path = ctx.scratch / "nonjson.sqlite3"
    journal = Journal(path)
    journal.append(_evaluation())
    conn = sqlite3.connect(path)
    try:
        conn.execute("DROP TRIGGER evaluations_no_update")
        conn.execute("UPDATE evaluations SET record = 'not json at all'")
        conn.commit()
    finally:
        conn.close()
    try:
        journal.verify()
    except ValueError:  # JSONDecodeError is a ValueError
        return {"verdict": "raises ValueError (fails closed, not False)",
                "finding": "F-001"}
    raise AssertionError(
        "verify() accepted non-JSON corruption: neither False nor an exception"
    )


def admission_unknown_producer(ctx: Context) -> dict[str, Any]:
    """An unknown producer is never trusted by default: its record is a
    structured rejection, not evidence, and admit() never raises."""
    _, stranger = generate_keypair()
    record = _record("stranger", "tests-executed", "sha256:" + "a" * 64,
                     command_digest(["pytest", "-q"]), 0, stranger)
    admitted = admission.admit([record], keyring={"someone-else": "ed25519:" + "b" * 64})
    assert admitted.evidence == (), "unknown producer was admitted as evidence"
    assert len(admitted.rejections) == 1
    assert admitted.rejections[0].reason is admission.RejectionReason.UNKNOWN_PRODUCER
    return {"rejected": admitted.rejections[0].reason.name}


def admission_bad_signature(ctx: Context) -> dict[str, Any]:
    """A signature from the wrong key is a distinct accusation (bad-signature)
    from no signature at all."""
    _, wrong_key = generate_keypair()
    record = _record("dogfood-producer", "tests-executed", "sha256:" + "a" * 64,
                     command_digest(["pytest", "-q"]), 0, wrong_key)
    _, real_public = generate_keypair()
    admitted = admission.admit([record], keyring={"dogfood-producer": real_public})
    assert admitted.evidence == ()
    assert admitted.rejections[0].reason is admission.RejectionReason.BAD_SIGNATURE
    return {"rejected": "BAD_SIGNATURE"}


def admission_good_record(ctx: Context) -> dict[str, Any]:
    """A correctly signed record from a keyring producer is admitted."""
    private, public = generate_keypair()
    record = _record("dogfood-producer", "tests-executed", "sha256:" + "a" * 64,
                     command_digest(["pytest", "-q"]), 0, private)
    admitted = admission.admit([record], keyring={"dogfood-producer": public})
    assert len(admitted.evidence) == 1, (
        f"good record rejected: {admitted.rejections!r}"
    )
    return {"admitted": admitted.evidence[0].claim_id}


def verdict_self_approval_blocks(ctx: Context) -> dict[str, Any]:
    """An approver who produced evidence fails for that reason — before the
    evidence is even considered."""
    digest = "sha256:" + "c" * 64
    claim = Claim(claim_id="tests-executed", command_digest=digest)
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)
    evidence = (Evidence(claim_id="tests-executed", subject_digest="sha256:" + "a" * 64,
                         producer_id="alice", command="pytest -q", command_digest=digest,
                         executable_path="/usr/bin/pytest", exit_code=0),)
    result = evaluate(gate, evidence, subject_digest="sha256:" + "a" * 64, approver_id="alice")
    assert result.verdict is Verdict.FAIL
    assert result.self_approval and "self-approval refused" in result.reason
    return {"verdict": "FAIL", "reason": result.reason}


def verdict_contradiction_blocks(ctx: Context) -> dict[str, Any]:
    """Two records addressing one claim that disagree make it unsatisfied,
    however many other records say PASS."""
    digest = "sha256:" + "c" * 64
    claim = Claim(claim_id="tests-executed", command_digest=digest)
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)
    subject = "sha256:" + "a" * 64

    def ev(exit_code: int, producer: str) -> Evidence:
        return Evidence(claim_id="tests-executed", subject_digest=subject,
                        producer_id=producer, command="pytest -q", command_digest=digest,
                        executable_path="/usr/bin/pytest", exit_code=exit_code)

    result = evaluate(gate, (ev(0, "alice"), ev(0, "bob"), ev(1, "carol")),
                      subject_digest=subject, approver_id="dana")
    assert result.verdict is Verdict.FAIL, "contradiction was outvoted by passes"
    assert "tests-executed" in result.missing_claims
    return {"verdict": "FAIL", "missing_claims": list(result.missing_claims)}


def verdict_absence_blocks(ctx: Context) -> dict[str, Any]:
    """A required claim with no records at all blocks — absence never passes."""
    digest = "sha256:" + "c" * 64
    claim = Claim(claim_id="tests-executed", command_digest=digest)
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)
    result = evaluate(gate, (), subject_digest="sha256:" + "a" * 64, approver_id="dana")
    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)
    return {"verdict": "FAIL"}


def signing_roundtrip(ctx: Context) -> dict[str, Any]:
    """Ed25519 signing is deterministic; any field change breaks verification;
    verify never raises on mangled input."""
    private, public = generate_keypair()
    content = {field: None for field in SIGNED_FIELDS}
    content.update({"claim_id": "x", "exit_code": 0})
    sig1 = sign_evidence(content, private)
    assert sign_evidence(content, private) == sig1, "signing is not deterministic"
    assert verify_evidence(content, sig1, public)
    assert not verify_evidence({**content, "exit_code": 1}, sig1, public)
    assert not verify_evidence(content, "not-a-signature", public)
    assert not verify_evidence(content, sig1, "ed25519:zz")
    return {"tamper_detected": True, "mangled_inputs_rejected": True}


def suite_freeze_drift(ctx: Context) -> dict[str, Any]:
    """REAL TOOLCHAIN: freeze a manifest from a real pytest run, then edit the
    real test file (one test made to fail, one removed) and run real pytest
    again. The manifest must separate 'test disappeared' (missing) from 'test
    now fails' (non_passed). No hand-written XML anywhere."""
    test_file = ctx.scratch / "test_dogfood_real.py"
    test_file.write_text(
        "def test_alpha() -> None:\n    assert 1 + 1 == 2\n\n\n"
        "def test_beta() -> None:\n    assert \"ranex\" != \"fake\"\n"
    )

    def run_pytest(expect_pass: bool) -> bytes:
        xml = ctx.scratch / f"results-{time.time_ns()}.xml"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(test_file),
             "--junitxml", str(xml), "-q", "--rootdir", str(ctx.scratch)],
            capture_output=True, text=True, check=False, timeout=120,
        )
        if expect_pass:
            assert result.returncode == 0, (
                f"real pytest failed on the passing file: {result.stdout}{result.stderr}"
            )
        else:
            assert result.returncode != 0, (
                "real pytest passed a deliberately broken test file"
            )
        return xml.read_bytes()

    baseline_xml = run_pytest(expect_pass=True)
    manifest = freeze_manifest(baseline_xml)
    ids = sorted(manifest["suite"])
    assert len(ids) == 2, f"expected both real tests frozen, got {ids}"

    alpha_id = next(i for i in ids if "alpha" in i)
    beta_id = next(i for i in ids if "beta" in i)
    test_file.write_text(
        "def test_alpha() -> None:\n    assert 1 + 1 == 3  # deliberately broken\n"
    )
    drifted_xml = run_pytest(expect_pass=False)
    results = suite_results_from_junitxml(drifted_xml, manifest)
    assert results["missing"] == [beta_id], results["missing"]
    assert [alpha_id, "failed"] in results["non_passed"], results["non_passed"]
    return {"frozen_ids": ids, "missing_after_drift": results["missing"],
            "failed_after_drift": [alpha_id, "failed"]}


def real_subject_digest_binding(ctx: Context) -> dict[str, Any]:
    """REAL GIT HISTORY: bind evidence to the real digest of the repository's
    HEAD tree, and prove staleness against the real HEAD~1 tree — the same
    evidence that satisfies the current subject proves nothing about the
    previous one. No synthetic digests."""
    from ranex.cli.main import subject_digest_for

    head_digest = subject_digest_for(REPO_ROOT, "HEAD")
    prior_digest = subject_digest_for(REPO_ROOT, "HEAD~1")
    assert head_digest != prior_digest, "HEAD and HEAD~1 have identical trees"

    digest = command_digest(["pytest", "-q"])
    claim = Claim(claim_id="tests-executed", command_digest=digest)
    gate = Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)
    evidence = Evidence(claim_id="tests-executed", subject_digest=head_digest,
                        producer_id="dogfood-producer", command="pytest -q",
                        command_digest=digest,
                        executable_path="/usr/bin/pytest", exit_code=0)
    # Real current subject: addresses and satisfies.
    assert evidence.addresses(claim, head_digest)
    assert evidence.satisfies(claim, head_digest)
    # The SAME record against the real previous subject: stale, proves nothing.
    assert not evidence.addresses(claim, prior_digest)
    stale_gate_result = evaluate(
        gate, (evidence,), subject_digest=prior_digest, approver_id="dogfood-approver")
    assert stale_gate_result.verdict is Verdict.FAIL, (
        "stale evidence (real HEAD run against real HEAD~1 subject) satisfied a gate"
    )
    assert stale_gate_result.missing_claims == ("tests-executed",)
    return {"bound_to": "real HEAD tree", "stale_against": "real HEAD~1 tree",
            "stale_verdict": "FAIL"}


def command_digest_structural(ctx: Context) -> dict[str, Any]:
    """command_digest digests the argv LIST: argument order is structural, and
    catalog/run must produce identical bytes for identical argv."""
    assert command_digest(["pytest", "-q"]) == command_digest(["pytest", "-q"])
    assert command_digest(["pytest", "-q"]) != command_digest(["-q", "pytest"])
    return {"order_sensitive": True}


import math_proofs
import logic_proofs
import advanced_proofs
import evolve_proofs
import formal_proofs

SCENARIOS: dict[str, tuple[str, str, Scenario]] = {
    # id: (area, lesson, fn)
    "cli-surface": (
        "cli",
        "The real CLI surface is the parser, not the docs: every catalogued "
        "command path must still parse.",
        cli_surface,
    ),
    "keygen-roundtrip": (
        "keygen",
        "keygen mints an Ed25519 pair outside the repository and refuses to "
        "overwrite an existing key.",
        keygen_roundtrip,
    ),
    "keygen-refuses-repo-paths": (
        "keygen",
        "Private keys are never committable: paths inside the repository are "
        "refused with an explanation.",
        keygen_refuses_repo_paths,
    ),
    "journal-chain": (
        "journal",
        "Evaluations append to a hash chain; the chain verifies while intact.",
        journal_chain,
    ),
    "journal-tamper-detected": (
        "journal",
        "Append-only is enforced twice: triggers abort edits, and verify() "
        "returns False for a valid-JSON out-of-band edit.",
        journal_tamper_detected,
    ),
    "journal-nonjson-corruption": (
        "journal",
        "FINDING F-001 pinned: non-JSON record corruption makes verify() "
        "RAISE (fail closed) instead of returning False — contract weak "
        "point, recorded as drift-sensitive behaviour.",
        journal_nonjson_corruption_fails_closed,
    ),
    "admission-unknown-producer": (
        "admission",
        "Unknown producers are never trusted by default; their records become "
        "structured rejections.",
        admission_unknown_producer,
    ),
    "admission-bad-signature": (
        "admission",
        "A wrong-key signature is BAD_SIGNATURE — a distinct accusation from "
        "a missing signature.",
        admission_bad_signature,
    ),
    "admission-good-record": (
        "admission",
        "A correctly signed record from a keyring producer becomes evidence.",
        admission_good_record,
    ),
    "verdict-self-approval-blocks": (
        "verdict",
        "Self-approval is refused before evidence is considered.",
        verdict_self_approval_blocks,
    ),
    "verdict-contradiction-blocks": (
        "verdict",
        "Two disagreeing records for one claim cannot be outvoted by passes.",
        verdict_contradiction_blocks,
    ),
    "verdict-absence-blocks": (
        "verdict",
        "Absence blocks: a required claim nobody ran fails the gate.",
        verdict_absence_blocks,
    ),
    "signing-roundtrip": (
        "signing",
        "Evidence signatures are deterministic, byte-bound to the closed "
        "field set, and verify fails closed on mangled input.",
        signing_roundtrip,
    ),
    "suite-freeze-drift": (
        "suite_results",
        "REAL TOOLCHAIN: a manifest frozen from a real pytest run separates "
        "'test disappeared' (missing) from 'test now fails' (non_passed) "
        "after a real second run of an edited test file. No synthetic XML.",
        suite_freeze_drift,
    ),
    "real-subject-digest-binding": (
        "verdict",
        "REAL GIT HISTORY: evidence bound to the real HEAD tree digest "
        "satisfies its claim, and the same evidence against the real HEAD~1 "
        "tree is stale and blocks. No synthetic digests.",
        real_subject_digest_binding,
    ),
    "command-digest-structural": (
        "canonical",
        "command_digest is structural over argv, so argument order changes "
        "the claim binding.",
        command_digest_structural,
    ),
    # -- deterministic math proofs (independent recomputation, not trust) --
    "proof-journal-chain-algebra": (
        "journal",
        "Every stored journal link equals an independent hashlib recomputation "
        "of sha256(canonical({prev_link, record})) chained from 64 zeros, "
        "proven over raw SQLite rows — not via Journal.verify().",
        math_proofs.journal_chain_algebra,
    ),
    "proof-journal-tamper-propagation": (
        "journal",
        "A one-record edit makes every later stored link diverge from the "
        "independent recomputation: tamper sensitivity propagates forward "
        "through the whole chain.",
        math_proofs.journal_tamper_propagation,
    ),
    "proof-canonical-agreement": (
        "canonical",
        "The kernel's canonical JSON agrees byte-for-byte with an independent "
        "implementation, and key insertion order never changes the bytes.",
        math_proofs.canonical_agreement,
    ),
    "proof-signature-determinism-stress": (
        "signing",
        "Ed25519 signatures are repeat-stable, distinct across 128 contents, "
        "and key-sensitive — verified by stress, not assumed.",
        math_proofs.signature_determinism_stress,
    ),
    "proof-digest-avalanche": (
        "canonical",
        "8192 generated argvs yield 8192 distinct command digests, and a "
        "one-character argv difference changes the digest.",
        math_proofs.digest_avalanche_and_distinctness,
    ),
    "proof-manifest-digest": (
        "suite_results",
        "manifest_digest equals an independent sha256 over independently "
        "canonicalised manifest bytes.",
        math_proofs.manifest_digest_recomputation,
    ),
    # -- core logic methods (finite-domain, exhaustive) --
    "logic-truth-table-addresses": (
        "verdict",
        "Exhaustive 8-row truth table: addresses == claim_match AND "
        "subject_match AND command_match.",
        logic_proofs.truth_table_addresses,
    ),
    "logic-truth-table-satisfies": (
        "verdict",
        "Exhaustive 16-row truth table: satisfies == addresses AND "
        "exit_code==0.",
        logic_proofs.truth_table_satisfies,
    ),
    "logic-demorgan-kernel-predicates": (
        "verdict",
        "De Morgan's law executed on the kernel's own predicates: "
        "NOT satisfies == NOT addresses OR exit_code != 0, every valuation.",
        logic_proofs.demorgan_between_kernel_predicates,
    ),
    "logic-preconditions-refuse": (
        "verdict",
        "Malformed Claim/Gate/Evidence inputs raise ValueError — never "
        "silently defaulted. Precondition enforcement, enumerated.",
        logic_proofs.preconditions_refuse_silence,
    ),
    "logic-evaluate-postconditions": (
        "verdict",
        "PASS implies no blocking facts, FAIL always names a cause, and "
        "evaluate is pure: byte-identical records across calls.",
        logic_proofs.evaluate_postconditions,
    ),
    # -- advanced methods, honestly mapped --
    "graph-lock-dag": (
        "provisioning",
        "Kahn's algorithm over the real committed uv.lock: the dependency "
        "graph must be a DAG or wheel selection could not terminate.",
        advanced_proofs.lock_graph_is_dag,
    ),
    "graph-selection-closure": (
        "provisioning",
        "select_wheels over the real lock and pinned interpreter is "
        "deterministic, duplicate-free, sha256-pinned, and stays inside the "
        "independent reachable-closure over-approximation.",
        advanced_proofs.lock_selection_closure,
    ),
    "numerics-publication-boundaries": (
        "canonical",
        "Exact numeric boundaries of publication: 2^53 - 1 accepted, 2^53 "
        "refused, floats always refused, non-BMP Unicode refused.",
        advanced_proofs.publication_value_boundaries,
    ),
    "numerics-canonical-refuses-nan": (
        "canonical",
        "canonical_json refuses NaN and Infinity, so non-deterministic bytes "
        "can never enter a digest.",
        advanced_proofs.canonical_json_refuses_indeterminates,
    ),
    "asymptotics-append-nondestructive": (
        "journal",
        "Append is structurally O(1), proven in bytes: appending rows k+1..N "
        "leaves rows 1..k byte-identical including links.",
        advanced_proofs.journal_append_is_nondestructive,
    ),
    "asymptotics-permutation-invariance": (
        "verdict",
        "Gate evaluation is invariant under all 6 permutations of the same "
        "evidence: one byte-identical canonical record.",
        advanced_proofs.evidence_permutation_invariance,
    ),
    # -- blind-spot mathematics (sensing layer for curriculum evolution) --
    "grid-admission-cartesian": (
        "admission",
        "The admission pipeline's ENTIRE parameter space (2 producers x 4 "
        "signature behaviours x 3 field-sets x 2 outcomes = 48 combinations, "
        "full cartesian — stronger than pairwise): every combination lands "
        "in a known class; the rejection taxonomy is total.",
        evolve_proofs.cartesian_admission_grid,
    ),
    "boundary-results-cap": (
        "suite_results",
        "x-1 / x / x+1 at the kernel's real 50 MiB results-artifact cap: "
        "accepted, accepted, refused — the boundary is exactly where the "
        "code says it is.",
        evolve_proofs.boundary_results_cap,
    ),
    "pigeonhole-archive-digests": (
        "signing",
        "Every digest in the proof pile is full-width (256-bit) and "
        "pairwise distinct; the birthday bound is 2^128 samples — the pile "
        "is collision-free by a margin of ~10^36.",
        evolve_proofs.pigeonhole_digests,
    ),
    "canonical-fixed-point": (
        "canonical",
        "Canonicalisation is idempotent — a fixed point: "
        "canon(parse(canon(x))) == canon(x) over every archive file.",
        evolve_proofs.canonical_fixed_point,
    ),
    "formal-verdict-monotonicity": (
        "verdict",
        "Order theory on the knowledge states: every small evidence set and "
        "every extension enumerated — FAIL->PASS only via admitted satisfying "
        "evidence, PASS->FAIL only via contradiction. The one sanctioned "
        "non-monotonicity, proven to be the only one.",
        formal_proofs.verdict_monotonicity,
    ),
    "formal-irrelevance-invariance": (
        "verdict",
        "Stability under irrelevant perturbation: records the gate does not "
        "ask about never change the decision (Lipschitz-0 on the irrelevant "
        "subspace), 21 perturbations, quotiented by the attendance list.",
        formal_proofs.irrelevance_invariance,
    ),
    "formal-permutation-group-s4": (
        "verdict",
        "Group action: all 24 orderings of four records yield one canonical "
        "record (S4-invariance), while producer relabeling deliberately "
        "breaks symmetry — identity binds no-self-approval.",
        formal_proofs.permutation_group_s4,
    ),
    "formal-lock-closure-equality": (
        "provisioning",
        "Set equality, not over-approximation: the kernel's reachable wheel "
        "set equals an independent inductive fixpoint over enabled edges "
        "for the real committed lock (29 wheels).",
        formal_proofs.lock_closure_equality,
    ),
    "formal-grid-pair-completeness": (
        "admission",
        "Combinatorial completeness: the cartesian admission grid covers "
        "every pair of factors in every projection (t=2, 44 projections) — "
        "strictly stronger than pairwise orthogonal arrays (it is t=4).",
        formal_proofs.grid_pair_completeness,
    ),
    "evolve-blind-spot-census": (
        "evolution",
        "McCabe path counts (M = decisions + 1) for every kernel function "
        "vs lines actually executed by the in-process proof scenarios: the "
        "measured blind-spot census that drives curriculum evolution. "
        "Facts: how many functions, total paths, and the top unproven "
        "complexity — deterministic per commit.",
        evolve_proofs.blind_spot_facts,
    ),
}
