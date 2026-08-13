from __future__ import annotations

import pytest

from ranex.foundation.signing import generate_keypair


def body(module) -> dict[str, object]:
    values = {field: None for field in module.SIGNED_FIELDS}
    values.update(
        verdict="FAIL", gate_id="landing", subject_digest="sha256:" + "a" * 64,
        subject_lane="PRE_READINESS_PRODUCT_SLICE", catalog_digest=None,
        approver_id="owner", failing_rule="TESTS_EXECUTED",
        missing_claims=["tests-executed"], considered=[],
        causes=[{"claim_id": "tests-executed", "cause": "absent"}],
        rejections=[], self_approval=False,
        reason="no evidence for required claim: tests-executed",
    )
    return values


def test_verdict_domain_payload_type_and_exact_field_set() -> None:
    from ranex.foundation import verdict_signing as module

    assert module.VERDICT_DOMAIN == b"ranex-verdict-v1\n"
    assert module.PAYLOAD_TYPE == "application/vnd.ranex.verdict.v1+json"
    assert "record_digest" not in module.SIGNED_FIELDS
    content = body(module)
    with pytest.raises(ValueError):
        module.signed_payload({**content, "record_digest": "sha256:" + "b" * 64})
    with pytest.raises(ValueError):
        module.signed_payload({k: v for k, v in content.items() if k != "reason"})


def test_verdict_signature_is_domain_separated_and_payload_type_asserted() -> None:
    from ranex.foundation import verdict_signing as module
    from ranex.foundation.approval import verify_approval
    from ranex.foundation.signing import verify_evidence

    private, public = generate_keypair()
    content = body(module)
    signature = module.sign_verdict(content, private)
    assert module.verify_verdict(content, signature, public, payload_type=module.PAYLOAD_TYPE)
    assert not module.verify_verdict(content, signature, public, payload_type="text/plain")
    assert not verify_evidence(content, signature, public)
    assert not verify_approval(content, signature, public)
