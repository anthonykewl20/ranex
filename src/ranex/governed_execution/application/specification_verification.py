"""Independent composition of A/B/C identity, trace coverage, and outcome ports."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.specification_abc import (
    SpecificationABCError,
    payload_digest,
    validate_approval_envelope,
    validate_generated_artifact_manifest,
    validate_spec_packet,
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


def _refuse(code: str, detail: str, *, facts: object | None = None) -> None:
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
    for kind in ("protected", "expected_values", "baselines", "negative_controls", "trace_projections", "sidecars"):
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
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, Mapping)
    expected: dict[str, str] = {}
    for row in artifacts["expected_values"]:  # validated by _check_artifacts
        assert isinstance(row, Mapping)
        try:
            value = json.loads(_file(candidate, row["path"]).read_bytes())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TraceVerificationError(E_TRACE_PROTECTED, "approved expected values are not JSON") from exc
        if not isinstance(value, dict) or any(not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()):
            _refuse(E_TRACE_PROTECTED, "approved expected values are not a string mapping")
        for key, item in value.items():
            if key in expected:
                _refuse(E_TRACE_PROTECTED, "approved outcome appears in multiple value files")
            expected[key] = item
    return expected


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
        packet = validate_spec_packet(dict(a))
        manifest = validate_generated_artifact_manifest(dict(b))
        envelope = validate_approval_envelope(dict(c))
    except SpecificationABCError as exc:
        _refuse(E_TRACE_AUTHORITY, f"A/B/C validation failed: {exc.code}")
    payload = envelope["payload"]
    assert isinstance(payload, Mapping)
    if envelope["key_id"] != payload["key"] or manifest["a_digest"] != payload_digest(packet):
        _refuse(E_TRACE_AUTHORITY, "A/B/C approval identities do not bind")
    if payload["a_digest"] != payload_digest(packet) or payload["b_digest"] != payload_digest(manifest):
        _refuse(E_TRACE_AUTHORITY, "C does not bind current A/B bytes")
    if payload["task"] != packet["task"] or payload["domain"] != packet["domain"] or payload["revision"] != packet["revision"]:
        _refuse(E_TRACE_CROSS_TASK, "C task identity differs from A")

    _check_artifacts(manifest, candidate)
    artifacts = manifest["artifacts"]
    assert isinstance(artifacts, Mapping)
    approved_invocation = artifacts["invocation"]
    assert isinstance(approved_invocation, Mapping)
    if tuple(approved_invocation["argv"]) != tuple(invocation):
        _refuse(E_TRACE_PROTECTED, "observed invocation differs from B")
    trace = verify_trace_coverage(packet, manifest, base, candidate, exemption_claims=exemptions)

    expected = _approved_values(manifest, candidate)
    approved_outcomes = packet["ids"]["outcome"]
    assert isinstance(approved_outcomes, list)
    if set(expected) != set(approved_outcomes) or set(gauge_results) != set(approved_outcomes):
        _refuse(E_TRACE_OUTCOME, "approved outcome observations do not exactly match A")
    outcomes = tuple(
        OutcomeFact(outcome_id, expected[outcome_id], gauge_results.get(outcome_id), gauge_results.get(outcome_id) == expected[outcome_id])
        for outcome_id in sorted(expected)
    )
    facts = SpecificationVerificationFacts(trace, outcomes)
    if not outcomes or any(not outcome.passed for outcome in outcomes):
        _refuse(E_TRACE_OUTCOME, "an approved executable outcome did not match", facts=facts)
    return facts
