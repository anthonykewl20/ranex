"""Core logic-method proofs against the real kernel: exhaustive truth tables,
precondition/postcondition enforcement, and De Morgan equivalence between
kernel predicates. All domains here are FINITE, so the checks are exhaustive,
not sampled.
"""

from __future__ import annotations

import itertools
from typing import Any

from ranex.foundation.canonical import canonical_json
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    Verdict,
    evaluate,
)

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
DIGEST_C = "sha256:" + "c" * 64


def _claim(digest: str = DIGEST_C) -> Claim:
    return Claim(claim_id="tests-executed", command_digest=digest)


def _gate(claim: Claim) -> Gate:
    return Gate(gate_id="landing", rule_id="landing-rule",
                required_claims=(claim,), blocking=True)


def _evidence(*, claim_id: str = "tests-executed", subject: str = DIGEST_A,
              command_digest: str = DIGEST_C, exit_code: int = 0,
              producer: str = "producer") -> Evidence:
    return Evidence(claim_id=claim_id, subject_digest=subject,
                    producer_id=producer, command="pytest -q",
                    command_digest=command_digest,
                    executable_path="/usr/bin/pytest", exit_code=exit_code)


def truth_table_addresses(ctx) -> dict[str, Any]:
    """Exhaustive 8-row truth table: addresses == claim_match ∧ subject_match
    ∧ command_match, for every combination."""
    claim = _claim()
    rows = []
    for claim_match, subject_match, command_match in itertools.product((True, False), repeat=3):
        evidence = _evidence(
            claim_id="tests-executed" if claim_match else "other-claim",
            subject=DIGEST_A if subject_match else DIGEST_B,
            command_digest=DIGEST_C if command_match else DIGEST_B,
        )
        expected = claim_match and subject_match and command_match
        assert evidence.addresses(claim, DIGEST_A) is expected, (
            f"addresses != C∧S∧D at {(claim_match, subject_match, command_match)}"
        )
        rows.append([claim_match, subject_match, command_match, expected])
    return {"rows": rows}


def truth_table_satisfies(ctx) -> dict[str, Any]:
    """Exhaustive 16-row truth table: satisfies == addresses ∧ exit_code==0.
    The suite-results conjunct is exercised separately (claims without
    results_required), keeping this table finite and exact."""
    claim = _claim()
    for claim_match, subject_match, command_match, exit_ok in itertools.product(
        (True, False), repeat=4
    ):
        evidence = _evidence(
            claim_id="tests-executed" if claim_match else "other-claim",
            subject=DIGEST_A if subject_match else DIGEST_B,
            command_digest=DIGEST_C if command_match else DIGEST_B,
            exit_code=0 if exit_ok else 1,
        )
        expected = claim_match and subject_match and command_match and exit_ok
        assert evidence.satisfies(claim, DIGEST_A) is expected, (
            f"satisfies != C∧S∧D∧E at "
            f"{(claim_match, subject_match, command_match, exit_ok)}"
        )
    return {"rows": 16, "formula": "satisfies == addresses AND exit_code==0"}


def demorgan_between_kernel_predicates(ctx) -> dict[str, Any]:
    """De Morgan, executed against the kernel predicates themselves:
    NOT satisfies  ==  NOT addresses  OR  exit_code != 0, for every valuation.
    ¬(A ∧ B) ⟺ ¬A ∨ ¬B proven on real Evidence objects, not on paper."""
    claim = _claim()
    for claim_match, subject_match, command_match in itertools.product((True, False), repeat=3):
        for exit_code in (0, 1):
            evidence = _evidence(
                claim_id="tests-executed" if claim_match else "other-claim",
                subject=DIGEST_A if subject_match else DIGEST_B,
                command_digest=DIGEST_C if command_match else DIGEST_B,
                exit_code=exit_code,
            )
            left = not evidence.satisfies(claim, DIGEST_A)
            right = (not evidence.addresses(claim, DIGEST_A)) or exit_code != 0
            assert left == right, (
                f"De Morgan fails at {(claim_match, subject_match, command_match, exit_code)}"
            )
    return {"law": "¬(A ∧ B) ⟺ ¬A ∨ ¬B", "valuations": 16}


def preconditions_refuse_silence(ctx) -> dict[str, Any]:
    """Precondition enforcement: malformed inputs raise ValueError and are
    never silently defaulted. Each violation names the constructor that must
    refuse it."""
    violations: list[tuple[str, Any]] = [
        ("Claim: empty claim_id", lambda: Claim(claim_id="", command_digest=DIGEST_C)),
        ("Claim: malformed digest", lambda: Claim(claim_id="x", command_digest="not-a-digest")),
        ("Claim: results fields on exit-code-only claim",
         lambda: Claim(claim_id="x", command_digest=DIGEST_C, manifest_digest=DIGEST_A)),
        ("Gate: non-blocking", lambda: Gate(gate_id="g", rule_id="r",
                                            required_claims=(_claim(),), blocking=False)),
        ("Gate: duplicate claims", lambda: Gate(
            gate_id="g", rule_id="r", required_claims=(_claim(), _claim()), blocking=True)),
        ("Gate: no claims", lambda: Gate(gate_id="g", rule_id="r",
                                         required_claims=(), blocking=True)),
        ("Evidence: bool exit_code", lambda: Evidence(
            claim_id="x", subject_digest=DIGEST_A, producer_id="p", command="c",
            command_digest=DIGEST_C, executable_path="/x", exit_code=True)),
    ]
    for name, construct in violations:
        try:
            construct()
        except ValueError:
            continue
        raise AssertionError(f"precondition not enforced: {name}")
    return {"violations_refused": len(violations)}


def evaluate_postconditions(ctx) -> dict[str, Any]:
    """Postconditions of the pure verdict kernel, checked on every scenario:
    PASS ⟹ no missing claims and no self-approval flag; FAIL ⟹ at least one
    named cause (missing claims, self-approval, or an explicit reason); and
    the same inputs always yield byte-identical records (purity)."""
    claim = _claim()
    gate = _gate(claim)
    subject = DIGEST_A

    cases = {
        "absence": evaluate(gate, (), subject_digest=subject, approver_id="dana"),
        "satisfied": evaluate(
            gate, (_evidence(),), subject_digest=subject, approver_id="dana"),
        "self-approval": evaluate(
            gate, (_evidence(producer="dana"),), subject_digest=subject,
            approver_id="dana"),
        "contradiction": evaluate(
            gate, (_evidence(producer="alice"), _evidence(producer="bob", exit_code=1)),
            subject_digest=subject, approver_id="dana"),
        "wrong-subject": evaluate(
            gate, (_evidence(subject=DIGEST_B),), subject_digest=subject,
            approver_id="dana"),
    }
    assert cases["absence"].verdict is Verdict.FAIL
    assert cases["satisfied"].verdict is Verdict.PASS
    assert cases["self-approval"].verdict is Verdict.FAIL
    assert cases["contradiction"].verdict is Verdict.FAIL
    assert cases["wrong-subject"].verdict is Verdict.FAIL

    for name, result in cases.items():
        if result.verdict is Verdict.PASS:
            assert result.missing_claims == () and not result.self_approval, (
                f"{name}: PASS with blocking facts"
            )
        else:
            assert result.missing_claims or result.self_approval or result.reason, (
                f"{name}: FAIL without a named cause"
            )
    # Purity: identical inputs, byte-identical record.
    for _ in range(2):
        repeat = evaluate(gate, (), subject_digest=subject, approver_id="dana")
        assert canonical_json(repeat.as_record()) == canonical_json(
            cases["absence"].as_record()
        ), "evaluate is not pure across calls"
    return {"cases": sorted(cases), "pass_case": "satisfied",
            "fail_cases": 4, "pure": True}
