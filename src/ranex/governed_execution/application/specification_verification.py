"""Independent composition of A/B/C identity, trace coverage, and outcome ports."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.specification_abc import (
    SpecificationABCError,
    assert_abc_chain,
)
from ranex.governed_execution.domain.specification_trace import (
    E_TRACE_AUTHORITY,
    E_TRACE_CROSS_TASK,
    E_TRACE_OUTCOME,
    E_TRACE_PROTECTED,
    E_TRACE_REASONLESS,
    TraceFact,
    TraceVerificationError,
    verify_trace_coverage,
)


@dataclass(frozen=True, slots=True)
class OutcomeFact:
    outcome_id: str
    expected: str
    actual: str | None
    passed: bool

    def as_record(self) -> dict[str, object]:
        return {"code": "OUTCOME-PASS" if self.passed else "OUTCOME-FAIL", "outcome_id": self.outcome_id, "expected": self.expected, "actual": self.actual, "passed": self.passed}


@dataclass(frozen=True, slots=True)
class SpecificationVerificationFacts:
    trace: TraceFact
    outcomes: tuple[OutcomeFact, ...]

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes({"trace": self.trace.as_record(), "outcomes": [outcome.as_record() for outcome in self.outcomes]})


def _refuse(code: str, detail: str, *, facts: object | None = None) -> NoReturn:
    raise TraceVerificationError(code, detail, facts=facts)


def _file(root: Path, path: object) -> Path:
    if not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts:
        _refuse(E_TRACE_PROTECTED, "protected artifact path is invalid")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        _refuse(E_TRACE_PROTECTED, f"protected artifact is absent: {path}")
    return resolved


def _check_artifacts(manifest: Mapping[str, object], candidate: Path) -> None:
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, Mapping):
        _refuse(E_TRACE_AUTHORITY, "manifest artifacts are malformed")
    for kind in ("protected", "expected_values", "baselines", "negative_controls", "trace_projections"):
        rows = artifacts.get(kind)
        if not isinstance(rows, list):
            _refuse(E_TRACE_AUTHORITY, f"manifest {kind} rows are malformed")
        for row in rows:
            if not isinstance(row, Mapping) or not isinstance(row.get("digest"), str):
                _refuse(E_TRACE_AUTHORITY, f"manifest {kind} row is malformed")
            actual = "sha256:" + hashlib.sha256(_file(candidate, row.get("path")).read_bytes()).hexdigest()
            if actual != row["digest"]:
                _refuse(E_TRACE_PROTECTED, f"protected {kind} bytes differ from B")


def _approved_values(manifest: Mapping[str, object], candidate: Path) -> Mapping[str, str]:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        _refuse(E_TRACE_AUTHORITY, "manifest artifacts are malformed")
    rows = artifacts.get("expected_values")
    if not isinstance(rows, list):
        _refuse(E_TRACE_AUTHORITY, "manifest expected_values rows are malformed")
    expected: dict[str, str] = {}
    for row in rows:  # validated by _check_artifacts
        if not isinstance(row, Mapping):
            _refuse(E_TRACE_AUTHORITY, "manifest expected_values row is malformed")
        path = row.get("path")
        try:
            value = json.loads(_file(candidate, path).read_bytes())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TraceVerificationError(E_TRACE_PROTECTED, "approved expected values are not JSON") from exc
        if not isinstance(value, dict) or any(not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()):
            _refuse(E_TRACE_PROTECTED, "approved expected values are not a string mapping")
        for key, item in value.items():
            if key in expected:
                _refuse(E_TRACE_PROTECTED, "approved outcome appears in multiple value files")
            expected[key] = item
    return expected


def _approved_outcome_artifacts(manifest: Mapping[str, object], candidate: Path) -> Mapping[str, str]:
    """Index the B-approved per-outcome projection artifacts by outcome ID."""

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        _refuse(E_TRACE_AUTHORITY, "manifest artifacts are malformed")
    projections = artifacts.get("trace_projections")
    if not isinstance(projections, list):
        _refuse(E_TRACE_AUTHORITY, "manifest outcome artifacts are malformed")

    bindings: dict[str, str] = {}
    bound_paths: set[str] = set()
    for row in projections:
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            _refuse(E_TRACE_AUTHORITY, "manifest trace projection row is malformed")
        try:
            descriptor = json.loads(_file(candidate, row["path"]).read_bytes())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TraceVerificationError(E_TRACE_AUTHORITY, "trace projection descriptor is not JSON") from exc
        if not isinstance(descriptor, Mapping):
            _refuse(E_TRACE_AUTHORITY, "trace projection descriptor is malformed")
        path = descriptor.get("path")
        ids = descriptor.get("ids")
        outcomes = ids.get("outcome") if isinstance(ids, Mapping) else None
        if (
            not isinstance(path, str)
            or not isinstance(outcomes, list)
            or len(outcomes) != 1
            or not isinstance(outcomes[0], str)
        ):
            continue
        outcome_id = outcomes[0]
        if path not in bound_paths:
            bindings.setdefault(outcome_id, path)
            bound_paths.add(path)
    return bindings


def verify_specification(
    a: Mapping[str, object],
    b: Mapping[str, object],
    c: Mapping[str, object],
    base: Path,
    candidate: Path,
    gauge_results: Mapping[str, str],
    invocation: Sequence[str],
    *,
    exemptions: Sequence[tuple[str, str, str]] = (),
) -> SpecificationVerificationFacts:
    """Refuse identity/protected drift before independently judging trace and outcomes."""

    raw_exemptions = b.get("exemptions")
    if isinstance(raw_exemptions, list) and any(
        isinstance(row, Mapping) and row.get("reason") == "" for row in raw_exemptions
    ):
        _refuse(E_TRACE_REASONLESS, "B contains a reasonless exemption")
    try:
        assert_abc_chain(a, b, c)
    except SpecificationABCError as exc:
        _refuse(E_TRACE_CROSS_TASK, f"A/B/C chain refused: {exc.code}")

    packet = a
    manifest = b

    _check_artifacts(manifest, candidate)
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping):
        _refuse(E_TRACE_AUTHORITY, "manifest artifacts are malformed")
    approved_invocation = artifacts.get("invocation")
    if not isinstance(approved_invocation, Mapping):
        _refuse(E_TRACE_AUTHORITY, "manifest invocation is malformed")
    argv = approved_invocation.get("argv")
    if not isinstance(argv, list) or any(not isinstance(arg, str) for arg in argv):
        _refuse(E_TRACE_AUTHORITY, "manifest invocation argv is malformed")
    if tuple(argv) != tuple(invocation):
        _refuse(E_TRACE_PROTECTED, "observed invocation differs from B")
    trace = verify_trace_coverage(packet, manifest, base, candidate, exemption_claims=exemptions)

    expected = _approved_values(manifest, candidate)
    packet_ids = packet.get("ids")
    if not isinstance(packet_ids, Mapping):
        _refuse(E_TRACE_AUTHORITY, "A IDs are malformed")
    approved_outcomes = packet_ids.get("outcome")
    if not isinstance(approved_outcomes, list) or any(not isinstance(item, str) for item in approved_outcomes):
        _refuse(E_TRACE_AUTHORITY, "A outcome IDs are malformed")
    outcome_artifacts = _approved_outcome_artifacts(manifest, candidate)
    if (
        set(expected) != set(approved_outcomes)
        or set(gauge_results) != set(approved_outcomes)
        or set(outcome_artifacts) != set(approved_outcomes)
    ):
        _refuse(E_TRACE_OUTCOME, "approved outcome observations do not exactly match A")
    outcomes = tuple(
        OutcomeFact(outcome_id, expected[outcome_id], gauge_results.get(outcome_id), gauge_results.get(outcome_id) == expected[outcome_id])
        for outcome_id in sorted(expected)
    )
    facts = SpecificationVerificationFacts(trace, outcomes)
    if not outcomes or any(not outcome.passed for outcome in outcomes):
        _refuse(E_TRACE_OUTCOME, "an approved executable outcome did not match", facts=facts)
    return facts
