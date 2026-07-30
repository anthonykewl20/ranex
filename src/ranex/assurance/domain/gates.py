from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from ranex.foundation.identity import Identity

_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class GateOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    CHECKER_FAULT = "CHECKER_FAULT"


def _require_identity(value: Identity, prefix: str, field: str) -> None:
    if not isinstance(value, Identity) or value.prefix != prefix:
        raise ValueError(f"{field} must be a canonical {prefix!r} identity")


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


def _require_digest(value: str, field: str) -> None:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field} must be canonical sha256 lowercase hex")


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_id: Identity
    claim_id: str
    outcome: GateOutcome
    project_id: Identity
    execution_id: Identity
    action: str
    subject_version: int
    producer_id: Identity
    producer_role: str
    command: str
    exit_code: int
    observed_at: str
    artifact_sha256: str
    artifact_verified: bool = False

    def __post_init__(self) -> None:
        _require_identity(self.evidence_id, "evd", "evidence_id")
        _require_identity(self.project_id, "prj", "project_id")
        _require_identity(self.execution_id, "run", "execution_id")
        _require_identity(self.producer_id, "principal", "producer_id")
        for field, value in (
            ("claim_id", self.claim_id),
            ("action", self.action),
            ("producer_role", self.producer_role),
            ("command", self.command),
            ("observed_at", self.observed_at),
        ):
            _require_text(value, field)
        if (
            isinstance(self.subject_version, bool)
            or not isinstance(self.subject_version, int)
            or self.subject_version < 0
        ):
            raise ValueError("subject_version must be a non-negative integer")
        if isinstance(self.exit_code, bool) or not isinstance(self.exit_code, int):
            raise ValueError("exit_code must be an integer")
        _require_digest(self.artifact_sha256, "artifact_sha256")
        if not isinstance(self.artifact_verified, bool):
            raise ValueError("artifact_verified must be a boolean")


@dataclass(frozen=True, slots=True)
class GateEvaluation:
    gate_id: Identity
    request_id: Identity
    outcome: GateOutcome
    authorized: bool
    missing_claim_ids: tuple[str, ...]
    reason_codes: tuple[str, ...]
    catalog_id: str
    catalog_digest: str
    policy_digest: str
    evidence_digest: str

    def __post_init__(self) -> None:
        _require_identity(self.gate_id, "gate", "gate_id")
        _require_identity(self.request_id, "transition", "request_id")
        if not isinstance(self.authorized, bool):
            raise ValueError("authorized must be a boolean")
        if self.authorized != (self.outcome is GateOutcome.PASS):
            raise ValueError("only PASS may be authorized and PASS must be authorized")
        if self.outcome is GateOutcome.PASS and self.reason_codes:
            raise ValueError("PASS evaluation must not contain reason codes")
        if self.outcome is not GateOutcome.PASS and not self.reason_codes:
            raise ValueError("non-PASS evaluation must contain a reason code")
        for field, values in (
            ("missing_claim_ids", self.missing_claim_ids),
            ("reason_codes", self.reason_codes),
        ):
            if values != tuple(sorted(set(values))):
                raise ValueError(f"{field} must be unique and sorted")
            if any(not value for value in values):
                raise ValueError(f"{field} must contain non-empty values")
        _require_text(self.catalog_id, "catalog_id")
        _require_digest(self.catalog_digest, "catalog_digest")
        _require_digest(self.policy_digest, "policy_digest")
        _require_digest(self.evidence_digest, "evidence_digest")
