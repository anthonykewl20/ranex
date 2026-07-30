from __future__ import annotations

from dataclasses import replace

from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
from ranex.foundation.identity import Identity
from ranex.governed_execution.application.gate_controller import GateController
from ranex.governed_execution.domain.application_control import (
    ApplicationControlRequest,
)
from ranex.policy.api.contracts import (
    GateDefinition,
    RuleDefinition,
    RuleEnforcementClass,
    RuleResolution,
)


def identity(prefix: str, suffix: str) -> Identity:
    return Identity.parse(
        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
        expected_prefix=prefix,
    )


PROJECT_ID = identity("prj", "101")
RUN_ID = identity("run", "102")
REQUESTER_ID = identity("principal", "103")
CHECKER_ID = identity("principal", "104")


def request() -> ApplicationControlRequest:
    return ApplicationControlRequest(
        request_id=identity("transition", "105"),
        project_id=PROJECT_ID,
        execution_id=RUN_ID,
        action="EXECUTION_START",
        expected_version=2,
        requested_by=REQUESTER_ID,
        subject_actor_ids=(REQUESTER_ID,),
    )


def gate() -> GateDefinition:
    return GateDefinition(
        gate_id=identity("gate", "106"),
        action="EXECUTION_START",
        rules=(
            RuleDefinition(
                rule_id="RULE-STATIC-CHECK",
                enforcement=RuleEnforcementClass.BLOCKING,
                resolution=RuleResolution.DETERMINISTIC,
                required_claim_ids=("CLAIM-STATIC-CHECK",),
                independent_producer_required=True,
            ),
        ),
    )


def evidence() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=identity("evd", "107"),
        claim_id="CLAIM-STATIC-CHECK",
        outcome=GateOutcome.PASS,
        project_id=PROJECT_ID,
        execution_id=RUN_ID,
        action="EXECUTION_START",
        subject_version=2,
        producer_id=CHECKER_ID,
        producer_role="qualified_checker",
        command="ruff check",
        exit_code=0,
        observed_at="2026-07-29T04:00:00Z",
        artifact_sha256="sha256:" + "a" * 64,
        artifact_verified=True,
    )


def evaluate(records: tuple[EvidenceRecord, ...]):
    return GateController().evaluate(
        gate=gate(),
        request=request(),
        evidence=records,
        catalog_id="RANEX-RD-CATALOG",
        catalog_digest="sha256:" + "b" * 64,
    )


def test_gate_controller_fails_closed_when_evidence_is_missing() -> None:
    decision = evaluate(())

    assert decision.outcome is GateOutcome.UNKNOWN
    assert decision.authorized is False
    assert decision.missing_claim_ids == ("CLAIM-STATIC-CHECK",)
    assert decision.reason_codes == ("MISSING_BLOCKING_EVIDENCE",)


def test_gate_controller_accepts_verified_exact_subject_evidence() -> None:
    decision = evaluate((evidence(),))

    assert decision.outcome is GateOutcome.PASS
    assert decision.authorized is True
    assert decision.reason_codes == ()
    assert decision.policy_digest.startswith("sha256:")
    assert decision.evidence_digest.startswith("sha256:")


def test_gate_controller_rejects_conflict_and_nonindependent_producer() -> None:
    conflict = replace(
        evidence(),
        evidence_id=identity("evd", "108"),
        outcome=GateOutcome.FAIL,
    )
    conflicting = evaluate((evidence(), conflict))
    self_produced = evaluate((replace(evidence(), producer_id=REQUESTER_ID),))

    assert conflicting.outcome is GateOutcome.CONFLICT
    assert conflicting.authorized is False
    assert self_produced.outcome is GateOutcome.FAIL
    assert self_produced.reason_codes == ("INDEPENDENCE_VIOLATION",)


def test_gate_controller_rejects_wrong_subject_and_unverified_artifact() -> None:
    other_run = identity("run", "109")

    wrong_subject = evaluate((replace(evidence(), execution_id=other_run),))
    unverified = evaluate((replace(evidence(), artifact_verified=False),))

    assert wrong_subject.outcome is GateOutcome.UNKNOWN
    assert wrong_subject.reason_codes == ("WRONG_SUBJECT_EVIDENCE",)
    assert unverified.outcome is GateOutcome.UNKNOWN
    assert unverified.reason_codes == ("UNVERIFIED_EVIDENCE_ARTIFACT",)
