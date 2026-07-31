"""Catalog loading and its malformed-input failure modes."""

from __future__ import annotations

from pathlib import Path

import pytest

from ranex.policy.adapters.configuration.yaml.slice_gate_loader import load_gate


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "gates.yaml"
    path.write_text(text, encoding="utf-8")
    return path


GOOD = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims: [tests-executed]
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
    text = GOOD.replace("required_claims: [tests-executed]", "required_claims: []")
    with pytest.raises(ValueError, match="required_claims"):
        load_gate(write(tmp_path, text), "landing")


def test_malformed_document_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mapping"):
        load_gate(write(tmp_path, "just a string"), "landing")
