from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ranex.policy.adapters.configuration.yaml.gate_catalog_loader import (
    load_gate_catalog,
    load_gate_catalog_bytes,
    load_gate_catalog_with_digest,
)
from ranex.policy.api.contracts import (
    RuleEnforcementClass,
    RuleResolution,
)

POLICY = b"""\
schema_version: "1"
artifact_type: application_control_policy
catalog_id: RANEX-RD-CATALOG
project_id: prj_01890f47-25a1-7301-98b3-5f5f6bb25af7
status: R_AND_D
owner: human-owner
gates:
  - gate_id: gate_01890f47-25a1-7302-98b3-5f5f6bb25af7
    action: EXECUTION_START
    rules:
      - rule_id: RULE-POLICY
        enforcement: BLOCKING
        resolution: DETERMINISTIC
        required_claim_ids: [CLAIM-POLICY]
        independent_producer_required: true
"""


def test_loader_parses_closed_secure_policy_contract() -> None:
    catalog = load_gate_catalog_bytes(POLICY)

    rule = catalog.gates[0].rules[0]
    assert catalog.status == "R_AND_D"
    assert catalog.owner == "human-owner"
    assert rule.enforcement is RuleEnforcementClass.BLOCKING
    assert rule.resolution is RuleResolution.DETERMINISTIC
    assert rule.independent_producer_required is True


def test_loader_rejects_duplicate_yaml_keys() -> None:
    duplicate = POLICY.replace(
        b"owner: human-owner",
        b"owner: human-owner\nowner: attacker",
    )

    with pytest.raises(ValueError, match="duplicate YAML key"):
        load_gate_catalog_bytes(duplicate)


def test_loader_rejects_unsafe_yaml_tag() -> None:
    unsafe = POLICY.replace(
        b"owner: human-owner",
        b"owner: !!python/object/apply:os.system ['touch /tmp/never']",
    )

    with pytest.raises(ValueError, match="invalid policy YAML"):
        load_gate_catalog_bytes(unsafe)


def test_loader_returns_digest_of_exact_policy_bytes(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_bytes(POLICY)

    catalog, digest = load_gate_catalog_with_digest(policy_path)

    assert catalog.catalog_id == "RANEX-RD-CATALOG"
    assert digest == "sha256:" + hashlib.sha256(POLICY).hexdigest()
    assert load_gate_catalog(policy_path) == catalog
