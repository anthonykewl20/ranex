from __future__ import annotations

from typing import Any

import pytest

from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
from ranex.foundation.identity import Identity
from ranex.governed_execution.adapters.policy.deterministic import (
    DeterministicPolicyAdapter,
)
from ranex.governed_execution.application.application_control_pep import (
    ApplicationControlPEP,
)
from ranex.governed_execution.domain.application_control import (
    ApplicationControlRequest,
)
from ranex.policy.api.contracts import (
    GateCatalog,
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


PROJECT_ID = identity("prj", "201")
RUN_ID = identity("run", "202")
REQUESTER_ID = identity("principal", "203")
CHECKER_ID = identity("principal", "204")


def request() -> ApplicationControlRequest:
    return ApplicationControlRequest(
        request_id=identity("transition", "205"),
        project_id=PROJECT_ID,
        execution_id=RUN_ID,
        action="EXECUTION_START",
        expected_version=1,
        requested_by=REQUESTER_ID,
    )


def evidence() -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=identity("evd", "206"),
        claim_id="CLAIM-POLICY",
        outcome=GateOutcome.PASS,
        project_id=PROJECT_ID,
        execution_id=RUN_ID,
        action="EXECUTION_START",
        subject_version=1,
        producer_id=CHECKER_ID,
        producer_role="qualified_checker",
        command="policy-check",
        exit_code=0,
        observed_at="2026-07-29T05:00:00Z",
        artifact_sha256="sha256:" + "c" * 64,
        artifact_verified=True,
    )


def catalog() -> GateCatalog:
    return GateCatalog(
        catalog_id="RANEX-RD-CATALOG",
        project_id=PROJECT_ID,
        status="R_AND_D",
        owner="human-owner",
        gates=(
            GateDefinition(
                gate_id=identity("gate", "207"),
                action="EXECUTION_START",
                rules=(
                    RuleDefinition(
                        rule_id="RULE-POLICY",
                        enforcement=RuleEnforcementClass.BLOCKING,
                        resolution=RuleResolution.DETERMINISTIC,
                        required_claim_ids=("CLAIM-POLICY",),
                    ),
                ),
            ),
        ),
    )


class RaisingPolicyAdapter:
    def evaluate(self, **_kwargs: Any) -> Any:
        raise RuntimeError("policy backend exploded")


class MalformedPolicyAdapter:
    def evaluate(self, **_kwargs: Any) -> object:
        return object()


def test_pep_fails_closed_when_policy_adapter_raises() -> None:
    decision = ApplicationControlPEP(RaisingPolicyAdapter()).decide(
        request=request(),
        evidence=(evidence(),),
    )

    assert decision.permitted is False
    assert decision.reason_codes == ("POLICY_ADAPTER_EXCEPTION",)


def test_pep_fails_closed_on_malformed_policy_result() -> None:
    decision = ApplicationControlPEP(MalformedPolicyAdapter()).decide(
        request=request(),
        evidence=(evidence(),),
    )

    assert decision.permitted is False
    assert decision.reason_codes == ("MALFORMED_POLICY_DECISION",)


def test_deterministic_policy_adapter_and_pep_produce_same_decision() -> None:
    adapter = DeterministicPolicyAdapter(
        catalog=catalog(),
        catalog_digest="sha256:" + "d" * 64,
    )
    pep = ApplicationControlPEP(adapter)

    first = pep.decide(request=request(), evidence=(evidence(),))
    second = pep.decide(request=request(), evidence=(evidence(),))

    assert first == second
    assert first.permitted is True
    assert first.reason_codes == ()


def test_pep_denies_when_deterministic_policy_has_no_evidence() -> None:
    adapter = DeterministicPolicyAdapter(
        catalog=catalog(),
        catalog_digest="sha256:" + "d" * 64,
    )

    decision = ApplicationControlPEP(adapter).decide(
        request=request(),
        evidence=(),
    )

    assert decision.permitted is False
    assert decision.reason_codes == ("MISSING_BLOCKING_EVIDENCE",)


def test_deterministic_policy_adapter_rejects_noncanonical_digest() -> None:
    with pytest.raises(ValueError, match="catalog_digest"):
        DeterministicPolicyAdapter(
            catalog=catalog(),
            catalog_digest="sha256:" + "z" * 64,
        )
