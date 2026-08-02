"""Catalog loading and its malformed-input failure modes."""

from __future__ import annotations

from pathlib import Path

import pytest

from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")
    return path


# SLICE-003 replaced the bare-string claim entry with a mapping that names the
# command satisfying the claim. The shape's own failure modes live in
# tests/contract/test_gate_catalog_claim_commands.py; this file keeps the
# catalog-level ones it already covered.
GOOD = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]
"""

CLAIMS_BLOCK = """    required_claims:
      - claim_id: tests-executed
        command: ["uv", "run", "pytest", "-q"]
"""


def test_loads_the_named_gate(tmp_path: Path) -> None:
    gate = load_gate(write(tmp_path, GOOD), "landing")
    assert gate.gate_id == "landing"
    assert gate.required_claims[0].claim_id == "tests-executed"


def test_unknown_gate_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="found 0"):
        load_gate(write(tmp_path, GOOD), "nope")


def test_duplicate_yaml_keys_are_refused(tmp_path: Path) -> None:
    text = GOOD + "\ngates:\n  - gate_id: other\n"
    with pytest.raises(ValueError, match="duplicate"):
        load_gate(write(tmp_path, text), "landing")


def test_unknown_keys_are_refused(tmp_path: Path) -> None:
    text = GOOD.replace("blocking: true", "blocking: true\n    waiver: yes")
    with pytest.raises(ValueError, match="unknown keys"):
        load_gate(write(tmp_path, text), "landing")


def test_non_blocking_gate_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="blocking"):
        load_gate(write(tmp_path, GOOD.replace("blocking: true", "blocking: false")), "landing")


def test_empty_required_claims_is_refused(tmp_path: Path) -> None:
    text = GOOD.replace(CLAIMS_BLOCK, "    required_claims: []\n")
    assert text != GOOD, "the claims block must actually have been replaced"
    with pytest.raises(ValueError, match="required_claims"):
        load_gate(write(tmp_path, text), "landing")


def test_empty_claim_identifier_is_refused(tmp_path: Path) -> None:
    text = GOOD.replace("claim_id: tests-executed", 'claim_id: ""')
    with pytest.raises(ValueError, match="non-empty string claim_id"):
        load_gate(write(tmp_path, text), "landing")


def test_catalog_without_any_gates_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-empty 'gates' list"):
        load_gate(write(tmp_path, "gates: []\n"), "landing")


def test_malformed_document_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mapping"):
        load_gate(write(tmp_path, "just a string"), "landing")
