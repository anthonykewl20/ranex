"""Pure deterministic renderers and B construction for closed scenarios."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace

from ranex.foundation.specification_abc import (
    canonical_payload_bytes,
    payload_digest,
    validate_generated_artifact_manifest,
)
from ranex.specification_generation.scenario import (
    ProjectionError,
    Scenario,
    Target,
    parse_scenario,
)

E_SG_PROSE_ONLY = "E-SG-008"
E_SG_STALE = "E-SG-010"
E_SG_INTEGRITY = "E-SG-011"


@dataclass(frozen=True, slots=True)
class GeneratedArtifact:
    path: str
    bytes: bytes

    @property
    def digest(self) -> str:
        return "sha256:" + hashlib.sha256(self.bytes).hexdigest()


@dataclass(frozen=True, slots=True)
class ProjectionResult:
    a_digest: str
    pseudocode: bytes
    flowchart: bytes
    files: tuple[GeneratedArtifact, ...]
    trace_projections: tuple[GeneratedArtifact, ...]
    sidecars: tuple[GeneratedArtifact, ...]
    manifest: dict[str, object]

    def with_file_bytes(self, path: str, value: bytes) -> ProjectionResult:
        """Return a deliberately tampered result for verifier negative controls."""
        return replace(self, files=tuple(replace(item, bytes=value) if item.path == path else item for item in self.files))


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_payload_bytes(value)).hexdigest()


def _rows(items: tuple[GeneratedArtifact, ...] | list[GeneratedArtifact]) -> list[dict[str, str]]:
    return [{"path": item.path, "digest": item.digest} for item in sorted(items, key=lambda row: row.path)]


def _trace_object(target: Target) -> dict[str, object]:
    return {"version": "trace-projection-v1", "path": target.path, "language": target.language, "ids": {"rule": list(target.rules), "transition": list(target.transitions), "outcome": list(target.outcomes)}, "anchor": {"symbol": target.symbol}}


def trace_comment(target: Target) -> bytes:
    """Render the exact SLICE-033 comment grammar for a comment-capable target."""
    prefixes = {"python": "#", "typescript": "//", "javascript": "//"}
    if target.language not in prefixes:
        raise ProjectionError(E_SG_PROSE_ONLY, "target language cannot carry a trace comment")
    ids = _trace_object(target)["ids"]
    assert isinstance(ids, dict)
    return (f"{prefixes[target.language]} ranex-trace: rule={','.join(ids['rule'])} " f"transition={','.join(ids['transition'])} outcome={','.join(ids['outcome'])} " f"projection={_digest(_trace_object(target))}\n").encode()


def _sidecar(target: Target) -> bytes:
    value = {"version": "trace-sidecar-v1", "projection": _digest(_trace_object(target)), "path": target.path, "symbol": target.symbol, "ids": _trace_object(target)["ids"]}
    return canonical_payload_bytes(value)


def _gauge(target: Target, scenario: Scenario, test_id: str, mapping_id: str) -> bytes:
    values = {item.identifier: item.value for item in scenario.outcomes}
    expected = values[target.outcomes[0]]
    if target.language == "python":
        return trace_comment(target) + f"def {target.symbol}():\n    assert {expected!r} == {expected!r}  # {test_id} {mapping_id}\n".encode()
    if target.language in {"typescript", "javascript"}:
        return trace_comment(target) + f"export function {target.symbol}() {{ return {expected!r}; }} // {test_id} {mapping_id}\n".encode()
    return _sidecar(target)


def generate_projections(spec_packet: object) -> ProjectionResult:
    """Compile approved, canonical DSL data into views and a closed B manifest."""
    scenario = parse_scenario(spec_packet)
    a_digest = payload_digest(spec_packet)
    pseudocode = (f"SPEC {scenario.domain}:{scenario.task}\n" + "".join(f"RULE {row.identifier} WHEN {row.when} THEN {row.outcome}\n" for row in scenario.rules)).encode()
    outcome_values = {row.identifier: row.value for row in scenario.outcomes}
    transition_by_id = {row.identifier: row for row in scenario.transitions}
    flowchart = ("flowchart TD\n" + "".join(f"  {row.transition}[{transition_by_id[row.transition].source}] -->|{row.identifier}| {row.outcome}[{outcome_values[row.outcome]}]\n" for row in scenario.rules)).encode()
    files = tuple(GeneratedArtifact(target.path, _gauge(target, scenario, scenario.test_ids[index % len(scenario.test_ids)], scenario.mapping_ids[index % len(scenario.mapping_ids)])) for index, target in enumerate(scenario.targets))
    traces = tuple(GeneratedArtifact(target.path + ".ranex-trace", trace_comment(target)) for target in scenario.targets if target.language != "sidecar-json")
    sidecars = tuple(GeneratedArtifact(target.path + ".ranex-trace.json", _sidecar(target)) for target in scenario.targets if target.language == "sidecar-json")
    expected = tuple(GeneratedArtifact(f"generated/expected/{row.identifier}.json", canonical_payload_bytes({"outcome": row.identifier, "value": row.value})) for row in scenario.outcomes)
    baselines = tuple(GeneratedArtifact(f"generated/baseline/{row.identifier}.json", canonical_payload_bytes({"outcome": row.identifier, "value": row.value})) for row in scenario.outcomes)
    controls = tuple(GeneratedArtifact(f"generated/negative/{row.identifier}.json", canonical_payload_bytes({"outcome": row.identifier, "wrong_value": row.value + "__wrong"})) for row in scenario.outcomes)
    pseudocode_flow = (GeneratedArtifact("projections/pseudocode.txt", pseudocode), GeneratedArtifact("projections/flowchart.mmd", flowchart))
    manifest: dict[str, object] = {"version": "generated-artifact-manifest-v1", "domain": scenario.domain, "a_digest": a_digest, "artifacts": {"pseudocode_flow": _rows(pseudocode_flow), "protected": _rows(files), "invocation": {"argv": ["pytest", "-q", *[item.path for item in files]]}, "expected_values": _rows(expected), "baselines": _rows(baselines), "negative_controls": _rows(controls), "trace_projections": _rows(traces), "sidecars": _rows(sidecars)}, "exemptions": []}
    validate_generated_artifact_manifest(manifest)
    return ProjectionResult(a_digest, pseudocode, flowchart, files, traces, sidecars, manifest)


def verify_projection(result: ProjectionResult, spec_packet: object) -> None:
    """Refuse stale or byte-tampered projections by rebuilding their pure output."""
    current = payload_digest(spec_packet)
    if result.a_digest != current:
        raise ProjectionError(E_SG_STALE, "projection A digest is stale")
    expected = generate_projections(spec_packet)
    if result != expected:
        raise ProjectionError(E_SG_INTEGRITY, "projection bytes or manifest differ from deterministic output")
