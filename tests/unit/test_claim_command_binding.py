"""SLICE-003 — a claim declares the command that satisfies it.

Written before the implementation and required to fail first: a test that passes
before the code exists is not a target, it is a circle painted around wherever
the dart landed.

The defect this closes: `Evidence.satisfies()` decided satisfaction from claim
name, subject digest and exit code 0, and never looked at what ran. `-- true`
therefore satisfied `tests-executed` — a correctly signed, subject-bound record
proving that something exited 0, and nothing else.

API pinned by these tests (ADR-001):

    Claim(claim_id=..., command_digest=...)
    Evidence(claim_id=..., subject_digest=..., producer_id=...,
             command=..., command_digest=..., executable_path=..., exit_code=...)
    Evidence.satisfies(claim, subject_digest)   # + command_digest equality

`command_digest` is `"sha256:" + canonical_sha256(argv)` — sha256 over
`canonical_json_bytes(argv)`. argv is a list of strings, not a string, so the
comparison needs no shell parsing and argument order is inside the digest.

`executable_path` is the resolved absolute path of `argv[0]`. It is a signed
field and the containment rule on it is enforced by `run` and re-checked at
evaluation; the confinement behaviour lives in
tests/security/test_executable_path_confinement.py.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes, command_digest
from ranex.governed_execution.domain.verdict import (
    Claim,
    Evidence,
    Gate,
    Verdict,
    evaluate,
)

SUBJECT = "sha256:" + "a" * 64

BOUND_ARGV = ["uv", "run", "pytest", "-q"]
TRIVIAL_ARGV = ["true"]

# A real, resolved, absolute path that is outside any repository under test.
# `satisfies()` does not compare it — the claim declares argv, not a machine
# layout — but every record carries one, so the helpers below do too.
EXECUTABLE = str(Path(shutil.which("sh")).resolve())


def claim(argv: list[str] = BOUND_ARGV, claim_id: str = "tests-executed") -> Claim:
    return Claim(claim_id=claim_id, command_digest=command_digest(argv))


def evidence(
    argv: list[str] = BOUND_ARGV,
    *,
    claim_id: str = "tests-executed",
    subject: str = SUBJECT,
    producer: str = "worker",
    exit_code: int = 0,
) -> Evidence:
    return Evidence(
        claim_id=claim_id,
        subject_digest=subject,
        producer_id=producer,
        command=" ".join(argv),
        command_digest=command_digest(argv),
        executable_path=EXECUTABLE,
        exit_code=exit_code,
    )


# --- the digest is a digest, and it is over the argv ------------------------


def test_command_digest_is_sha256_over_the_canonical_argv_bytes() -> None:
    """Pinned so `run`, the loader and any future producer compute the same
    bytes. A binding whose two sides disagree about the encoding is no binding."""

    expected = "sha256:" + hashlib.sha256(canonical_json_bytes(BOUND_ARGV)).hexdigest()
    assert command_digest(BOUND_ARGV) == expected

    # And the value actually reaches the domain objects under that name.
    assert claim().command_digest == expected
    assert evidence().command_digest == expected


def test_claim_refuses_a_command_digest_that_is_not_a_digest() -> None:
    """A claim whose bound command cannot be compared has undefined
    satisfaction, and an undefined claim cannot block. Refused at construction."""

    with pytest.raises(ValueError, match="digest"):
        Claim(claim_id="tests-executed", command_digest="uv run pytest -q")


def test_evidence_refuses_a_command_digest_that_is_not_a_digest() -> None:
    with pytest.raises(ValueError, match="digest"):
        Evidence(
            claim_id="tests-executed",
            subject_digest=SUBJECT,
            producer_id="worker",
            command="uv run pytest -q",
            command_digest="not-a-digest",
            executable_path=EXECUTABLE,
            exit_code=0,
        )


# --- satisfaction now asks what ran -----------------------------------------


def test_the_bound_command_satisfies() -> None:
    assert evidence(BOUND_ARGV).satisfies(claim(BOUND_ARGV), SUBJECT) is True


def test_a_trivial_command_does_not_satisfy_a_bound_claim() -> None:
    """The headline defect. `true` exits 0 against any tree, so a record of it
    proves nothing about this one however well it is signed."""

    assert evidence(TRIVIAL_ARGV).satisfies(claim(BOUND_ARGV), SUBJECT) is False


def test_the_readable_command_field_is_not_what_is_compared() -> None:
    """A record whose legible `command` reads like the bound one, with the
    digest of something else, must not satisfy — otherwise the digest is
    decoration and the string is the control."""

    lying = Evidence(
        claim_id="tests-executed",
        subject_digest=SUBJECT,
        producer_id="worker",
        command="uv run pytest -q",
        command_digest=command_digest(TRIVIAL_ARGV),
        executable_path=EXECUTABLE,
        exit_code=0,
    )
    assert lying.satisfies(claim(BOUND_ARGV), SUBJECT) is False


def test_argument_order_is_part_of_the_digest() -> None:
    """argv, not a string, so ordering is structural rather than a parsing
    accident. `pytest -q tests/unit` and `pytest tests/unit -q` are two commands
    and two digests."""

    forward = ["pytest", "-q", "tests/unit"]
    shuffled = ["pytest", "tests/unit", "-q"]

    assert command_digest(forward) != command_digest(shuffled)
    assert evidence(shuffled).satisfies(claim(forward), SUBJECT) is False


def test_subject_and_exit_code_still_gate_satisfaction() -> None:
    """The command binding is added to the existing conditions, never in place
    of them."""

    other_subject = "sha256:" + "b" * 64
    assert evidence(BOUND_ARGV, subject=other_subject).satisfies(
        claim(BOUND_ARGV), SUBJECT
    ) is False
    assert evidence(BOUND_ARGV, exit_code=1).satisfies(claim(BOUND_ARGV), SUBJECT) is False


# --- and it reaches the kernel as absence, which already blocks --------------


def test_an_unbound_command_reaches_the_verdict_as_a_missing_claim() -> None:
    gate = Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(claim(BOUND_ARGV),),
        blocking=True,
    )
    result = evaluate(
        gate,
        (evidence(TRIVIAL_ARGV),),
        subject_digest=SUBJECT,
        approver_id="reviewer",
    )

    assert result.verdict is Verdict.FAIL
    assert result.missing_claims == ("tests-executed",)


def test_an_unbound_record_beside_a_bound_one_carries_nothing() -> None:
    """ADR-001 sad path 15.

    Two records for one claim, from two producers: one describes the bound
    command, one does not. The gate passes on the bound record alone, so the
    unbound one must be contributing nothing — otherwise a worker could stand
    next to someone else's real run and be counted by association.
    """

    gate = Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(claim(BOUND_ARGV),),
        blocking=True,
    )
    unbound = evidence(TRIVIAL_ARGV, producer="worker-a")
    bound = evidence(BOUND_ARGV, producer="worker-b")

    both = evaluate(gate, (unbound, bound), subject_digest=SUBJECT, approver_id="reviewer")
    assert both.verdict is Verdict.PASS

    alone = evaluate(gate, (unbound,), subject_digest=SUBJECT, approver_id="reviewer")
    assert alone.verdict is Verdict.FAIL, (
        "the unbound record satisfied the claim on its own, so its presence "
        "beside the bound one was never harmless"
    )


def test_an_equivalent_spelling_of_the_argv_does_not_satisfy() -> None:
    """ADR-001 sad path 7: exactness over convenience, stated not hidden.

    `pytest --quiet` does what `pytest -q` does. The kernel has no way to know
    that and must not guess; the catalog names one argv and that is the one.
    """

    assert evidence(["pytest", "--quiet"]).satisfies(
        claim(["pytest", "-q"]), SUBJECT
    ) is False


def test_the_bound_command_passes_the_gate() -> None:
    gate = Gate(
        gate_id="landing",
        rule_id="TESTS_EXECUTED",
        required_claims=(claim(BOUND_ARGV),),
        blocking=True,
    )
    result = evaluate(
        gate,
        (evidence(BOUND_ARGV),),
        subject_digest=SUBJECT,
        approver_id="reviewer",
    )

    assert result.verdict is Verdict.PASS
