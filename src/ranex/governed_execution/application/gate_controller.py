from __future__ import annotations

from collections.abc import Iterable

from ranex.assurance.api.contracts import (
    EvidenceRecord,
    GateEvaluation,
    GateOutcome,
)
from ranex.foundation.canonical import canonical_json, canonical_sha256
from ranex.governed_execution.domain.application_control import (
    ApplicationControlRequest,
)
from ranex.policy.api.contracts import (
    GateDefinition,
    RuleEnforcementClass,
    RuleResolution,
)


def _digest(value: object) -> str:
    return f"sha256:{canonical_sha256(value)}"


def _gate_document(gate: GateDefinition) -> dict[str, object]:
    return {
        "gate_id": str(gate.gate_id),
        "action": gate.action,
        "rules": [
            {
                "rule_id": rule.rule_id,
                "enforcement": rule.enforcement.value,
                "resolution": rule.resolution.value,
                "required_claim_ids": list(rule.required_claim_ids),
                "independent_producer_required": (rule.independent_producer_required),
            }
            for rule in gate.rules
        ],
    }


def _evidence_document(record: EvidenceRecord) -> dict[str, object]:
    return {
        "evidence_id": str(record.evidence_id),
        "claim_id": record.claim_id,
        "outcome": record.outcome.value,
        "project_id": str(record.project_id),
        "execution_id": str(record.execution_id),
        "action": record.action,
        "subject_version": record.subject_version,
        "producer_id": str(record.producer_id),
        "producer_role": record.producer_role,
        "command": record.command,
        "exit_code": record.exit_code,
        "observed_at": record.observed_at,
        "artifact_sha256": record.artifact_sha256,
        "artifact_verified": record.artifact_verified,
    }


class GateController:
    """Pure fail-closed evaluator; it is not an Execution reducer."""

    def evaluate(
        self,
        *,
        gate: GateDefinition,
        request: ApplicationControlRequest,
        evidence: Iterable[EvidenceRecord],
        catalog_id: str,
        catalog_digest: str,
    ) -> GateEvaluation:
        records = tuple(evidence)
        policy_digest = _digest(_gate_document(gate))
        documents = [_evidence_document(record) for record in records]
        documents.sort(key=canonical_json)
        evidence_digest = _digest(documents)

        def result(
            outcome: GateOutcome,
            *,
            authorized: bool = False,
            missing: tuple[str, ...] = (),
            reasons: tuple[str, ...],
        ) -> GateEvaluation:
            return GateEvaluation(
                gate_id=gate.gate_id,
                request_id=request.request_id,
                outcome=outcome,
                authorized=authorized,
                missing_claim_ids=tuple(sorted(set(missing))),
                reason_codes=tuple(sorted(set(reasons))),
                catalog_id=catalog_id,
                catalog_digest=catalog_digest,
                policy_digest=policy_digest,
                evidence_digest=evidence_digest,
            )

        if request.action != gate.action:
            return result(
                GateOutcome.FAIL,
                reasons=("ACTION_DOES_NOT_MATCH_GATE",),
            )

        authority_rules = tuple(
            rule
            for rule in gate.rules
            if rule.enforcement
            in {
                RuleEnforcementClass.REQUIRED,
                RuleEnforcementClass.BLOCKING,
            }
        )
        if not authority_rules:
            return result(
                GateOutcome.UNKNOWN,
                reasons=("NO_AUTHORITY_RULES",),
            )
        if any(
            rule.resolution is RuleResolution.HUMAN_DECISION_REQUIRED
            for rule in authority_rules
        ):
            return result(
                GateOutcome.UNKNOWN,
                reasons=("HUMAN_DECISION_NOT_VERIFIED",),
            )

        actor_ids = {request.requested_by, *request.subject_actor_ids}
        conflicts: list[str] = []
        checker_faults: list[str] = []
        unverified: list[str] = []
        independence_violations: list[str] = []
        failed: list[str] = []
        missing: list[str] = []
        wrong_subject: list[str] = []

        for rule in authority_rules:
            for claim_id in rule.required_claim_ids:
                claim_records = tuple(
                    record for record in records if record.claim_id == claim_id
                )
                candidates = tuple(
                    record
                    for record in claim_records
                    if record.project_id == request.project_id
                    and record.execution_id == request.execution_id
                    and record.action == request.action
                    and record.subject_version == request.expected_version
                )
                if claim_records and not candidates:
                    wrong_subject.append(claim_id)
                    missing.append(claim_id)
                    continue

                outcomes = {record.outcome for record in candidates}
                if GateOutcome.CHECKER_FAULT in outcomes:
                    checker_faults.append(claim_id)
                    continue
                if GateOutcome.CONFLICT in outcomes or (
                    GateOutcome.PASS in outcomes and GateOutcome.FAIL in outcomes
                ):
                    conflicts.append(claim_id)
                    continue
                passing = tuple(
                    record
                    for record in candidates
                    if record.outcome is GateOutcome.PASS and record.exit_code == 0
                )
                if passing and not any(record.artifact_verified for record in passing):
                    unverified.append(claim_id)
                    continue
                if rule.independent_producer_required and any(
                    record.producer_id in actor_ids for record in passing
                ):
                    independence_violations.append(claim_id)
                    continue
                if any(
                    record.outcome is GateOutcome.FAIL or record.exit_code != 0
                    for record in candidates
                ):
                    failed.append(claim_id)
                    continue
                if not passing:
                    missing.append(claim_id)

        if checker_faults:
            return result(
                GateOutcome.CHECKER_FAULT,
                reasons=("CHECKER_FAULT",),
            )
        if conflicts:
            return result(
                GateOutcome.CONFLICT,
                reasons=("CONFLICTING_EXACT_SUBJECT_EVIDENCE",),
            )
        if unverified:
            return result(
                GateOutcome.UNKNOWN,
                missing=tuple(unverified),
                reasons=("UNVERIFIED_EVIDENCE_ARTIFACT",),
            )
        if independence_violations:
            return result(
                GateOutcome.FAIL,
                reasons=("INDEPENDENCE_VIOLATION",),
            )
        if failed:
            return result(
                GateOutcome.FAIL,
                reasons=("BLOCKING_EVIDENCE_FAILED",),
            )
        if missing:
            return result(
                GateOutcome.UNKNOWN,
                missing=tuple(missing),
                reasons=(
                    ("WRONG_SUBJECT_EVIDENCE",)
                    if wrong_subject
                    else ("MISSING_BLOCKING_EVIDENCE",)
                ),
            )
        return result(GateOutcome.PASS, authorized=True, reasons=())
