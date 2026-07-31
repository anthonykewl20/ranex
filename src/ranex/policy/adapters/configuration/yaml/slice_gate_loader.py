"""Load one gate definition from a YAML catalog.

Deliberately loads from YAML and **not** from `architecture/contracts/`.
`SPIKE-01` proved the generated registry holds readiness gates
(`evidence_role` -> tier) while this kernel needs action gates
(`action` -> rules): five fields would have to be invented. Inventing them and
calling the result "derived from the contract tree" would be a false closure.

Closing that gap needs someone to decide what the action gates are and author
them. That decision is deferred, and this loader does not pretend otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class SliceClaimDefinition:
    """A policy-owned claim identifier."""

    claim_id: str


@dataclass(frozen=True, slots=True)
class SliceGateDefinition:
    """Adapter output expressed only in policy-owned scalar values."""

    gate_id: str
    rule_id: str
    required_claims: tuple[SliceClaimDefinition, ...]
    blocking: bool


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently taking the last one."""


def _no_duplicates(
    loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate key in gate catalog: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(  # type: ignore[no-untyped-call]
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates
)


def load_gate(
    catalog_path: Path,
    gate_id: str,
) -> SliceGateDefinition:
    """Return the named gate, or raise. A malformed catalog never yields a gate."""

    text = Path(catalog_path).read_text(encoding="utf-8")
    document = yaml.load(text, Loader=_UniqueKeyLoader)
    if not isinstance(document, dict):
        raise ValueError("gate catalog must be a mapping")

    gates = document.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("gate catalog must declare a non-empty 'gates' list")

    matches = [g for g in gates if isinstance(g, dict) and g.get("gate_id") == gate_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one gate {gate_id!r}, found {len(matches)}")

    entry = matches[0]
    allowed = {"gate_id", "rule_id", "required_claims", "blocking"}
    unknown = set(entry) - allowed
    if unknown:
        raise ValueError(f"unknown keys in gate {gate_id!r}: {sorted(unknown)}")

    claims = entry.get("required_claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError(f"gate {gate_id!r} must declare required_claims")
    blocking = entry.get("blocking", True)
    if blocking is not True:
        raise ValueError(f"gate {gate_id!r} must be blocking")

    return SliceGateDefinition(
        gate_id=str(entry["gate_id"]),
        rule_id=str(entry["rule_id"]),
        required_claims=tuple(
            SliceClaimDefinition(str(claim)) for claim in claims
        ),
        blocking=True,
    )
