"""Closed projection from kernel evaluation and admission to the wire record."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.publication_validation import validate_publication_value
from ranex.governed_execution.domain.admission import Admission
from ranex.governed_execution.domain.verdict import Evaluation


def validate_projection(record: Mapping[str, Any], *, required_claims: Sequence[str]) -> None:
    causes = record.get("causes")
    if not isinstance(causes, list):
        raise ValueError("causes must be a list")
    required = set(required_claims)
    seen: set[str | None] = set()
    for cause in causes:
        if not isinstance(cause, Mapping):
            raise ValueError("cause must be a mapping")
        claim_id = cause["claim_id"]
        kind = cause.get("cause")
        if not isinstance(kind, str) or not kind:
            raise ValueError("cause must have a non-empty kind")
        if claim_id is None and kind != "unattributable":
            raise ValueError("only unattributable causes may have a null claim")
        if claim_id is not None and not isinstance(claim_id, str):
            raise ValueError("cause claim must be a string or null")
        if claim_id is not None and claim_id not in required:
            raise ValueError("cause names a non-required claim")
        if claim_id is not None and claim_id in seen:
            raise ValueError("duplicate cause for claim")
        if claim_id is not None:
            seen.add(claim_id)


def project_verdict(evaluation: Evaluation, admission: Admission, *, required_claims: Sequence[str]) -> dict[str, Any]:
    missing = set(evaluation.missing_claims)
    refused = {
        item.claim_id for item in admission.rejections
        if item.claim_id is not None and item.claim_id in missing
    }
    causes: list[dict[str, str | None]] = [
        {"claim_id": item.claim_id, "cause": item.cause, **({"detail": item.detail} if item.detail is not None else {})}
        for item in evaluation.causes if item.claim_id not in refused
    ]
    causes.extend({"claim_id": claim_id, "cause": "refused"} for claim_id in sorted(refused))
    causes.extend(
        {"claim_id": None, "cause": "unattributable"}
        for item in admission.rejections if item.claim_id is None
    )
    rejections = [
        {"index": item.index, "reason": str(item.reason), "detail": item.detail,
         "claim_id": item.claim_id, "producer_id": item.producer_id}
        for item in admission.rejections
    ]
    body = {
        "verdict": str(evaluation.verdict), "gate_id": evaluation.gate_id,
        "subject_digest": evaluation.subject_digest, "subject_lane": evaluation.subject_lane,
        "catalog_digest": evaluation.catalog_digest, "approver_id": evaluation.approver_id,
        "failing_rule": evaluation.failing_rule, "missing_claims": list(evaluation.missing_claims),
        "considered": list(evaluation.considered), "causes": causes, "rejections": rejections,
        "self_approval": evaluation.self_approval, "reason": evaluation.reason,
    }
    validate_projection(body, required_claims=required_claims)
    validate_publication_value(body)
    return {**body, "record_digest": "sha256:" + canonical_sha256(body)}


def presentation_partition(record: Mapping[str, Any], admission: Admission) -> tuple[int, list[str], list[str], set[str]]:
    causes = record["causes"]
    unattributable = sum(1 for item in causes if item["cause"] == "unattributable")
    refused = {item["claim_id"] for item in causes if item["cause"] == "refused"}
    absent_causes = {item["claim_id"] for item in causes if item["cause"] == "absent"}
    missing = set(record["missing_claims"])
    considered = {item.claim_id for item in admission.evidence if item.claim_id in missing}
    return unattributable, sorted(refused), sorted(absent_causes - considered), considered
