"""Frozen generator-to-verifier contract across the SLICE-031/033 boundary."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import (
    canonical_payload_bytes,
    payload_digest,
    sign_approval_payload,
)
from ranex.governed_execution.application.specification_verification import verify_specification
from ranex.governed_execution.domain.specification_trace import TraceVerificationError
from ranex.specification_generation import generate_projections

_PRIVATE_KEY = "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
_FIXTURES = Path(__file__).parents[1] / "contract/fixtures/specification"


def _packet() -> dict[str, object]:
    packet = json.loads((_FIXTURES / "projection-v1-vectors.json").read_text("utf-8"))["packet"]
    packet["scope"] = {"include": ["src"], "exclude": []}
    packet["semantics"] = [
        "ranex-scenario-v1:"
        + canonical_payload_bytes(
            {
                "version": "ranex-scenario-v1",
                "rules": [{"id": "R-1", "when": "request.valid", "transition": "T-1", "outcome": "O-1"}],
                "transitions": [{"id": "T-1", "from": "request", "to": "accepted"}],
                "outcomes": [{"id": "O-1", "value": "accepted"}],
                "targets": [
                    {"path": "src/generated/accept.py", "language": "python", "symbol": "accept", "rules": ["R-1"], "transitions": ["T-1"], "outcomes": ["O-1"]},
                    {"path": "src/generated/accept.ts", "language": "typescript", "symbol": "accept", "rules": ["R-1"], "transitions": ["T-1"], "outcomes": ["O-1"]},
                    {"path": "src/generated/accept.js", "language": "javascript", "symbol": "accept", "rules": ["R-1"], "transitions": ["T-1"], "outcomes": ["O-1"]},
                ],
            }
        ).decode("utf-8")
    ]
    return packet


def _approval(a: dict[str, object], b: dict[str, object]) -> dict[str, object]:
    template = copy.deepcopy(json.loads((_FIXTURES / "abc-v1-vectors.json").read_text("utf-8"))["triple"])
    payload = template["c_payload"]
    assert isinstance(payload, dict)
    payload["task"] = a["task"]
    payload["a_digest"] = payload_digest(a)
    payload["b_digest"] = payload_digest(b)
    return {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": payload,
        "key_id": payload["key"],
        "signature": sign_approval_payload(payload, _PRIVATE_KEY),
    }


def _write(candidate: Path, path: str, value: bytes) -> None:
    output = candidate / path
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(value)


def _candidate_from(result: object, candidate: Path) -> None:
    for category in ("files", "trace_projections", "sidecars"):
        for artifact in getattr(result, category):
            _write(candidate, artifact.path, artifact.bytes)
    _write(candidate, "generated/expected/O-1.json", canonical_payload_bytes({"O-1": "accepted"}))
    _write(candidate, "generated/baseline/O-1.json", canonical_payload_bytes({"O-1": "accepted"}))
    _write(candidate, "generated/negative/O-1.json", canonical_payload_bytes({"O-1": "accepted__wrong"}))


def test_generated_python_typescript_and_javascript_traces_verify_and_tampering_refuses(tmp_path: Path) -> None:
    a = _packet()
    result = generate_projections(a)
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    base = tmp_path / "base"
    base.mkdir()
    _candidate_from(result, candidate)
    b = result.manifest
    c = _approval(a, b)
    invocation = tuple(b["artifacts"]["invocation"]["argv"])  # type: ignore[index]

    facts = verify_specification(a, b, c, base, candidate, {"O-1": "accepted"}, invocation)
    assert facts.trace.covered == 3
    assert any(anchor.path == "src/generated/accept.js" and anchor.form == "comment" for anchor in facts.trace.anchors)

    artifact = candidate / "src/generated/accept.py"
    artifact.write_bytes(artifact.read_bytes() + b"# tampered\n")
    with pytest.raises(TraceVerificationError, match="E-TRACE-015"):
        verify_specification(a, b, c, base, candidate, {"O-1": "accepted"}, invocation)
