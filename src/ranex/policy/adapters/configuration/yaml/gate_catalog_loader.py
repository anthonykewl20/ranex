from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode

from ranex.foundation.identity import Identity
from ranex.policy.api.contracts import (
    GateCatalog,
    GateDefinition,
    RuleDefinition,
    RuleEnforcementClass,
    RuleResolution,
)


class _UniqueKeySafeLoader(yaml.SafeLoader):
    def construct_mapping(
        self,
        node: MappingNode,
        deep: bool = False,
    ) -> dict[object, object]:
        mapping: dict[object, object] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError(f"duplicate YAML key: {key!r}")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be a mapping")
    return value


def _closed(
    value: dict[str, Any],
    *,
    allowed: frozenset[str],
    field: str,
) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        raise ValueError(f"{field} contains unexpected fields: {unexpected}")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


def _parse(raw_value: Any) -> GateCatalog:
    raw = _mapping(raw_value, "catalog")
    _closed(
        raw,
        allowed=frozenset(
            {
                "schema_version",
                "artifact_type",
                "catalog_id",
                "project_id",
                "status",
                "owner",
                "gates",
            }
        ),
        field="catalog",
    )
    if raw.get("schema_version") != "1":
        raise ValueError("unsupported policy schema_version")
    if raw.get("artifact_type") != "application_control_policy":
        raise ValueError("unsupported policy artifact_type")
    raw_gates = raw.get("gates")
    if not isinstance(raw_gates, list) or not raw_gates:
        raise ValueError("gates must be a non-empty list")

    gates: list[GateDefinition] = []
    for gate_index, raw_gate_value in enumerate(raw_gates):
        raw_gate = _mapping(raw_gate_value, f"gates[{gate_index}]")
        _closed(
            raw_gate,
            allowed=frozenset({"gate_id", "action", "rules"}),
            field=f"gates[{gate_index}]",
        )
        raw_rules = raw_gate.get("rules")
        if not isinstance(raw_rules, list) or not raw_rules:
            raise ValueError(f"gates[{gate_index}].rules must be non-empty")
        rules: list[RuleDefinition] = []
        for rule_index, raw_rule_value in enumerate(raw_rules):
            raw_rule = _mapping(
                raw_rule_value,
                f"gates[{gate_index}].rules[{rule_index}]",
            )
            _closed(
                raw_rule,
                allowed=frozenset(
                    {
                        "rule_id",
                        "enforcement",
                        "resolution",
                        "required_claim_ids",
                        "independent_producer_required",
                    }
                ),
                field=f"gates[{gate_index}].rules[{rule_index}]",
            )
            claims_value = raw_rule.get("required_claim_ids")
            if not isinstance(claims_value, list) or not claims_value:
                raise ValueError("required_claim_ids must be a non-empty list")
            claims = tuple(sorted(_text(claim, "claim_id") for claim in claims_value))
            rules.append(
                RuleDefinition(
                    rule_id=_text(raw_rule.get("rule_id"), "rule_id"),
                    enforcement=RuleEnforcementClass(raw_rule.get("enforcement")),
                    resolution=RuleResolution(raw_rule.get("resolution")),
                    required_claim_ids=claims,
                    independent_producer_required=_boolean(
                        raw_rule.get("independent_producer_required", False),
                        "independent_producer_required",
                    ),
                )
            )
        gates.append(
            GateDefinition(
                gate_id=Identity.parse(
                    _text(raw_gate.get("gate_id"), "gate_id"),
                    expected_prefix="gate",
                ),
                action=_text(raw_gate.get("action"), "action"),
                rules=tuple(rules),
            )
        )
    return GateCatalog(
        catalog_id=_text(raw.get("catalog_id"), "catalog_id"),
        project_id=Identity.parse(
            _text(raw.get("project_id"), "project_id"),
            expected_prefix="prj",
        ),
        status=_text(raw.get("status"), "status"),
        owner=_text(raw.get("owner"), "owner"),
        gates=tuple(gates),
    )


def load_gate_catalog_bytes(content: bytes) -> GateCatalog:
    try:
        raw = yaml.load(content, Loader=_UniqueKeySafeLoader)
    except ValueError:
        raise
    except yaml.YAMLError as exc:
        raise ValueError("invalid policy YAML") from exc
    return _parse(raw)


def load_gate_catalog(path: Path) -> GateCatalog:
    return load_gate_catalog_bytes(path.read_bytes())


def load_gate_catalog_with_digest(path: Path) -> tuple[GateCatalog, str]:
    content = path.read_bytes()
    digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
    return load_gate_catalog_bytes(content), digest
