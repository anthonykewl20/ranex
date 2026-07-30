from __future__ import annotations

from collections.abc import Iterable

from ranex.assurance.api.contracts import (
    EvidenceRecord,
    GateEvaluation,
    GateOutcome,
)
from ranex.governed_execution.application.ports.application_control_policy import (
    ApplicationControlPolicy,
)
from ranex.governed_execution.domain.application_control import (
    ApplicationControlDecision,
    ApplicationControlFacts,
    ApplicationControlRequest,
    decide_application_control,
    deny_application_control,
)


class ApplicationControlPEP:
    """Fail-closed policy-enforcement point with no dispatch capability."""

    def __init__(self, policy: ApplicationControlPolicy) -> None:
        self._policy = policy

    def decide(
        self,
        *,
        request: ApplicationControlRequest,
        evidence: Iterable[EvidenceRecord],
    ) -> ApplicationControlDecision:
        try:
            evaluation = self._policy.evaluate(
                request=request,
                evidence=tuple(evidence),
            )
        except Exception:
            return deny_application_control("POLICY_ADAPTER_EXCEPTION")

        if not isinstance(evaluation, GateEvaluation):
            return deny_application_control("MALFORMED_POLICY_DECISION")

        return decide_application_control(
            ApplicationControlFacts(
                decision_well_formed=True,
                request_bound=evaluation.request_id == request.request_id,
                gate_passed=evaluation.outcome is GateOutcome.PASS,
                gate_authorized=evaluation.authorized,
                reason_codes=evaluation.reason_codes,
            )
        )
