"""Closed scenario/oracle DSL parsing for specification projections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NoReturn

from ranex.foundation.specification_abc import (
    SpecificationABCError,
    canonical_payload_bytes,
    parse_strict_json,
    validate_spec_packet,
)

E_SG_DSL_ABSENT = "E-SG-001"
E_SG_DSL_CANONICAL = "E-SG-002"
E_SG_DSL_SHAPE = "E-SG-003"
E_SG_UNSUPPORTED = "E-SG-004"
E_SG_DUPLICATE = "E-SG-005"
E_SG_UNMAPPED = "E-SG-006"
E_SG_UNKNOWN_ID = "E-SG-007"
E_SG_PROSE_ONLY = "E-SG-008"
E_SG_COVERAGE = "E-SG-009"
E_SG_EMPTY_VOCABULARY = "E-SG-012"
E_SG_PATH = "E-SG-013"
E_SG_SYMBOL = "E-SG-014"

_PREFIX = "ranex-scenario-v1:"
_LANGUAGES = frozenset({"python", "typescript", "javascript", "sidecar-json"})
_PORTABLE_RELATIVE_PATH = re.compile(
    r"^(?!.*\.\.)[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)*$"
)
_PYTHON_SYMBOL = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_ECMASCRIPT_SYMBOL = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_OUTCOME_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ProjectionError(ValueError):
    """A deterministic refusal from the closed projection boundary."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True, slots=True)
class Rule:
    identifier: str
    when: str
    transition: str
    outcome: str


@dataclass(frozen=True, slots=True)
class Transition:
    identifier: str
    source: str
    target: str


@dataclass(frozen=True, slots=True)
class Outcome:
    identifier: str
    value: str


@dataclass(frozen=True, slots=True)
class Target:
    path: str
    language: str
    symbol: str
    rules: tuple[str, ...]
    transitions: tuple[str, ...]
    outcomes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Scenario:
    domain: str
    task: str
    rules: tuple[Rule, ...]
    transitions: tuple[Transition, ...]
    outcomes: tuple[Outcome, ...]
    targets: tuple[Target, ...]
    test_ids: tuple[str, ...]
    mapping_ids: tuple[str, ...]


def _refuse(code: str, detail: str) -> NoReturn:
    raise ProjectionError(code, detail)


def _closed_object(value: object, fields: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        _refuse(E_SG_DSL_SHAPE, "object has missing or extra fields")
    return value


def _string(value: object) -> str:
    if not isinstance(value, str) or not value:
        _refuse(E_SG_DSL_SHAPE, "required string is absent or empty")
    return value


def _ids(value: object, *, name: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        _refuse(E_SG_DSL_SHAPE, f"{name} must be a nonempty string list")
    if len(set(value)) != len(value):
        _refuse(E_SG_DUPLICATE, f"duplicate {name} ID")
    return tuple(sorted(value))


def _safe_path(value: object) -> str:
    path = _string(value)
    if not _PORTABLE_RELATIVE_PATH.fullmatch(path):
        _refuse(E_SG_PATH, "target path is not a portable relative path")
    return path


def _safe_symbol(value: object, language: str) -> str:
    symbol = _string(value)
    grammar = _ECMASCRIPT_SYMBOL if language in {"typescript", "javascript"} else _PYTHON_SYMBOL
    if not grammar.fullmatch(symbol):
        _refuse(E_SG_SYMBOL, f"target symbol is invalid for {language}")
    return symbol


def _unique_a_ids(packet: dict[str, object]) -> dict[str, set[str]]:
    raw = packet["ids"]
    if not isinstance(raw, dict):  # Foundation has already checked this.
        _refuse(E_SG_DSL_SHAPE, "A IDs are invalid")
    all_ids: list[str] = []
    result: dict[str, set[str]] = {}
    for kind, values in raw.items():
        if not isinstance(values, list) or any(not isinstance(item, str) or not item for item in values):
            _refuse(E_SG_DSL_SHAPE, "A IDs are invalid")
        if len(set(values)) != len(values):
            _refuse(E_SG_DUPLICATE, f"duplicate A {kind} ID")
        result[kind] = set(values)
        all_ids.extend(values)
    if len(set(all_ids)) != len(all_ids):
        _refuse(E_SG_DUPLICATE, "A IDs must be unique across vocabularies")
    return result


def parse_scenario(spec_packet: object) -> Scenario:
    """Parse exactly one canonical v1 DSL string; no prose is executable."""
    try:
        packet = validate_spec_packet(spec_packet)
    except SpecificationABCError as exc:
        _refuse(E_SG_DSL_SHAPE, exc.detail)
    identifiers = _unique_a_ids(packet)
    if not identifiers["test"] or not identifiers["mapping"]:
        _refuse(E_SG_EMPTY_VOCABULARY, "A test and mapping vocabularies must be nonempty")
    semantics = packet["semantics"]
    assert isinstance(semantics, list)
    dsl_entries = [item for item in semantics if isinstance(item, str) and item.startswith(_PREFIX)]
    if not dsl_entries:
        _refuse(E_SG_PROSE_ONLY, "no closed scenario DSL is present")
    if len(dsl_entries) != 1:
        _refuse(E_SG_DSL_ABSENT, "exactly one closed scenario DSL is required")
    raw = dsl_entries[0][len(_PREFIX) :].encode("utf-8")
    try:
        dsl = parse_strict_json(raw)
    except SpecificationABCError as exc:
        _refuse(E_SG_DSL_CANONICAL, exc.detail)
    if raw != canonical_payload_bytes(dsl):
        _refuse(E_SG_DSL_CANONICAL, "DSL JSON bytes are not canonical")
    root = _closed_object(dsl, {"version", "rules", "transitions", "outcomes", "targets"})
    if root["version"] != "ranex-scenario-v1":
        _refuse(E_SG_UNSUPPORTED, "unsupported scenario version")
    rules: list[Rule] = []
    transitions: list[Transition] = []
    outcomes: list[Outcome] = []
    targets: list[Target] = []
    for row in _list(root["rules"], "rules"):
        item = _closed_object(row, {"id", "when", "transition", "outcome"})
        rules.append(Rule(_string(item["id"]), _string(item["when"]), _string(item["transition"]), _string(item["outcome"])))
    for row in _list(root["transitions"], "transitions"):
        item = _closed_object(row, {"id", "from", "to"})
        transitions.append(Transition(_string(item["id"]), _string(item["from"]), _string(item["to"])))
    for row in _list(root["outcomes"], "outcomes"):
        item = _closed_object(row, {"id", "value"})
        identifier = _string(item["id"])
        if not _OUTCOME_FILENAME.fullmatch(identifier):
            _refuse(E_SG_PATH, "outcome ID is not filename-safe")
        outcomes.append(Outcome(identifier, _string(item["value"])))
    for row in _list(root["targets"], "targets"):
        item = _closed_object(row, {"path", "language", "symbol", "rules", "transitions", "outcomes"})
        language = _string(item["language"])
        if language not in _LANGUAGES:
            _refuse(E_SG_UNSUPPORTED, f"unsupported target language: {language}")
        targets.append(Target(_safe_path(item["path"]), language, _safe_symbol(item["symbol"], language), _ids(item["rules"], name="rule"), _ids(item["transitions"], name="transition"), _ids(item["outcomes"], name="outcome")))
    _check_ids("rule", [row.identifier for row in rules], identifiers["rule"])
    _check_ids("transition", [row.identifier for row in transitions], identifiers["transition"])
    _check_ids("outcome", [row.identifier for row in outcomes], identifiers["outcome"])
    for rule in rules:
        if rule.transition not in identifiers["transition"] or rule.outcome not in identifiers["outcome"]:
            _refuse(E_SG_UNKNOWN_ID, f"rule {rule.identifier} references an unknown transition or outcome")
    if len({target.path for target in targets}) != len(targets):
        _refuse(E_SG_DUPLICATE, "duplicate target path")
    for target in targets:
        for kind, values in (("rule", target.rules), ("transition", target.transitions), ("outcome", target.outcomes)):
            if not set(values) <= identifiers[kind]:
                _refuse(E_SG_UNKNOWN_ID, f"target {target.path} references an unknown {kind}")
    covered_rules = {item for target in targets for item in target.rules}
    covered_outcomes = {item for target in targets for item in target.outcomes}
    if covered_rules != identifiers["rule"] or covered_outcomes != identifiers["outcome"]:
        _refuse(E_SG_COVERAGE, "every A rule and outcome needs a protected target")
    provenance = packet["oracle_provenance"]
    assert isinstance(provenance, dict)
    for outcome in identifiers["outcome"]:
        if provenance.get(outcome) not in {"human", "domain-rule", "requirement"}:
            _refuse(E_SG_PROSE_ONLY, f"outcome {outcome} has no approval-backed oracle")
    return Scenario(str(packet["domain"]), str(packet["task"]), tuple(sorted(rules, key=lambda row: row.identifier)), tuple(sorted(transitions, key=lambda row: row.identifier)), tuple(sorted(outcomes, key=lambda row: row.identifier)), tuple(sorted(targets, key=lambda row: row.path)), tuple(sorted(identifiers["test"])), tuple(sorted(identifiers["mapping"])))


def _list(value: object, name: str) -> list[object]:
    if not isinstance(value, list) or not value:
        _refuse(E_SG_DSL_SHAPE, f"{name} must be a nonempty list")
    return value


def _check_ids(kind: str, found: list[str], intended: set[str]) -> None:
    if len(set(found)) != len(found):
        _refuse(E_SG_DUPLICATE, f"duplicate DSL {kind} ID")
    if set(found) != intended:
        _refuse(E_SG_UNMAPPED, f"DSL {kind} IDs do not exactly cover A")
