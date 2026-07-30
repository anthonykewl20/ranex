from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ranex.foundation.identity import Identity


class RuleEnforcementClass(StrEnum):
    ADVISORY = "ADVISORY"
    REQUIRED = "REQUIRED"
    BLOCKING = "BLOCKING"
    EXPERIMENTAL = "EXPERIMENTAL"


class RuleResolution(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")


@dataclass(frozen=True, slots=True)
class RuleDefinition:
    rule_id: str
    enforcement: RuleEnforcementClass
    resolution: RuleResolution
    required_claim_ids: tuple[str, ...]
    independent_producer_required: bool = False

    def __post_init__(self) -> None:
        _require_text(self.rule_id, "rule_id")
        if not self.required_claim_ids:
            raise ValueError("required_claim_ids must not be empty")
        if self.required_claim_ids != tuple(sorted(set(self.required_claim_ids))):
            raise ValueError("required_claim_ids must be unique and sorted")
        if any(not claim_id for claim_id in self.required_claim_ids):
            raise ValueError("required_claim_ids must contain non-empty values")
        if not isinstance(self.independent_producer_required, bool):
            raise ValueError("independent_producer_required must be a boolean")


@dataclass(frozen=True, slots=True)
class GateDefinition:
    gate_id: Identity
    action: str
    rules: tuple[RuleDefinition, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.gate_id, Identity) or self.gate_id.prefix != "gate":
            raise ValueError("gate_id must be a canonical gate identity")
        _require_text(self.action, "action")
        if not self.rules:
            raise ValueError("gate rules must not be empty")
        rule_ids = tuple(rule.rule_id for rule in self.rules)
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError("gate rule IDs must be unique")
        if not any(
            rule.enforcement is RuleEnforcementClass.BLOCKING for rule in self.rules
        ):
            raise ValueError("gate must contain a BLOCKING rule")


@dataclass(frozen=True, slots=True)
class GateCatalog:
    catalog_id: str
    project_id: Identity
    status: str
    owner: str
    gates: tuple[GateDefinition, ...]

    def __post_init__(self) -> None:
        _require_text(self.catalog_id, "catalog_id")
        if not isinstance(self.project_id, Identity) or self.project_id.prefix != "prj":
            raise ValueError("project_id must be a canonical project identity")
        if self.status != "R_AND_D":
            raise ValueError("tracer policy status must be R_AND_D")
        _require_text(self.owner, "owner")
        if not self.gates:
            raise ValueError("gate catalog must not be empty")
        gate_ids = tuple(gate.gate_id for gate in self.gates)
        actions = tuple(gate.action for gate in self.gates)
        if len(gate_ids) != len(set(gate_ids)):
            raise ValueError("gate IDs must be unique")
        if len(actions) != len(set(actions)):
            raise ValueError("gate actions must be unique")

    def require_project(self, project_id: Identity) -> None:
        if project_id != self.project_id:
            raise ValueError("policy project does not match control request")

    def gate_for(self, action: str) -> GateDefinition:
        matches = tuple(gate for gate in self.gates if gate.action == action)
        if len(matches) != 1:
            raise ValueError(
                f"expected exactly one gate for {action!r}; found {len(matches)}"
            )
        return matches[0]
