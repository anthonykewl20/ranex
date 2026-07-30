from __future__ import annotations

import pytest

from ranex.foundation.identity import Identity
from ranex.governed_execution.domain.application_control import (
    ApplicationControlFacts,
    ApplicationControlRequest,
    decide_application_control,
)


def identity(prefix: str, suffix: str) -> Identity:
    return Identity.parse(
        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
        expected_prefix=prefix,
    )


def test_application_control_decision_is_pure_and_deterministic() -> None:
    facts = ApplicationControlFacts(
        decision_well_formed=True,
        request_bound=True,
        gate_passed=True,
        gate_authorized=True,
        reason_codes=(),
    )

    first = decide_application_control(facts)
    second = decide_application_control(facts)

    assert first == second
    assert first.permitted is True


def test_application_control_decision_denies_malformed_facts() -> None:
    decision = decide_application_control(
        ApplicationControlFacts(
            decision_well_formed=False,
            request_bound=True,
            gate_passed=True,
            gate_authorized=True,
            reason_codes=(),
        )
    )

    assert decision.permitted is False
    assert decision.reason_codes == ("MALFORMED_POLICY_DECISION",)


def test_application_control_request_rejects_noncanonical_actor_order() -> None:
    later = identity("principal", "603")
    earlier = identity("principal", "602")

    with pytest.raises(ValueError, match="unique and sorted"):
        ApplicationControlRequest(
            request_id=identity("transition", "604"),
            project_id=identity("prj", "605"),
            execution_id=identity("run", "606"),
            action="EXECUTION_START",
            expected_version=0,
            requested_by=identity("principal", "607"),
            subject_actor_ids=(later, earlier),
        )
