from __future__ import annotations

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.domain.admission import Admission, Rejection, RejectionReason
from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate

SUBJECT = "sha256:" + "a" * 64
COMMAND = "sha256:" + canonical_sha256(["pytest"])


def evaluation():
    return evaluate(
        Gate("landing", "TESTS_EXECUTED", (Claim("tests", COMMAND),), True), (),
        subject_digest=SUBJECT, approver_id="owner",
    )


def test_projection_matches_extended_kernel_first_wire_shape() -> None:
    from ranex.governed_execution.verdict_projection import project_verdict

    rejection = Rejection(0, RejectionReason.BAD_SIGNATURE, "bad", "worker", "tests")
    record = project_verdict(evaluation(), Admission((), (rejection,)), required_claims=("tests",))
    assert set(record) == {
        "verdict", "gate_id", "subject_digest", "subject_lane", "catalog_digest",
        "approver_id", "failing_rule", "missing_claims", "considered", "causes",
        "rejections", "self_approval", "reason", "record_digest",
    }
    assert record["self_approval"] is False
    assert record["rejections"] == [{
        "index": 0, "reason": "bad-signature", "detail": "bad",
        "claim_id": "tests", "producer_id": "worker",
    }]


@pytest.mark.parametrize("kind", ["duplicate", "non-required"])
def test_projection_refuses_duplicate_or_non_required_causes(kind: str) -> None:
    from ranex.governed_execution.verdict_projection import validate_projection

    causes = [{"claim_id": "tests", "cause": "absent"}]
    if kind == "duplicate":
        causes *= 2
    else:
        causes = [{"claim_id": "other", "cause": "absent"}]
    with pytest.raises(ValueError, match="cause|claim"):
        validate_projection({"causes": causes}, required_claims=("tests",))
