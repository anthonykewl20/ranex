"""Pure deterministic renderers and B construction for closed scenarios."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from pathlib import PurePosixPath

from ranex.foundation.specification_abc import (
    canonical_payload_bytes,
    payload_digest,
    validate_generated_artifact_manifest,
)
from ranex.specification_generation.scenario import (
    E_SG_PROSE_ONLY,
    ProjectionError,
    Scenario,
    Target,
    parse_scenario,
)

E_SG_STALE = "E-SG-010"
E_SG_INTEGRITY = "E-SG-011"
E_SG_ARTIFACT_PATH_COLLISION = "E-SG-015"
TRACE_PROJECTION_VERSION = "trace-projection-v1"


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


def _rows(items: tuple[GeneratedArtifact, ...] | list[GeneratedArtifact]) -> list[dict[str, str]]:
    return [{"path": item.path, "digest": item.digest} for item in sorted(items, key=lambda row: row.path)]


def trace_projection_descriptor(target: Target) -> dict[str, object]:
    """Return the closed, canonical trace-projection-v1 descriptor for a target."""
    return {
        "version": TRACE_PROJECTION_VERSION,
        "path": target.path,
        "language": target.language,
        "ids": {
            "rule": list(target.rules),
            "transition": list(target.transitions),
            "outcome": list(target.outcomes),
        },
        "anchor": {"symbol": target.symbol},
    }


def trace_projection_digest(target: Target) -> str:
    """Return raw SHA-256 of the canonical trace descriptor (never PAE-wrapped)."""
    return "sha256:" + hashlib.sha256(
        canonical_payload_bytes(trace_projection_descriptor(target))
    ).hexdigest()


def trace_comment(target: Target) -> bytes:
    """Render the exact SLICE-033 comment grammar for a comment-capable target."""
    prefixes = {"python": "#", "typescript": "//", "javascript": "//"}
    if target.language not in prefixes:
        raise ProjectionError(E_SG_PROSE_ONLY, "target language cannot carry a trace comment")
    ids = trace_projection_descriptor(target)["ids"]
    assert isinstance(ids, dict)
    return (
        f"{prefixes[target.language]} ranex-trace: rule={','.join(ids['rule'])} "
        f"transition={','.join(ids['transition'])} outcome={','.join(ids['outcome'])} "
        f"projection={trace_projection_digest(target)}\n"
    ).encode()


def _sidecar(target: Target) -> bytes:
    descriptor = trace_projection_descriptor(target)
    value = {
        "version": "trace-sidecar-v1",
        "projection": trace_projection_digest(target),
        "path": target.path,
        "symbol": target.symbol,
        "ids": descriptor["ids"],
    }
    return canonical_payload_bytes(value)


def _gauge(target: Target, scenario: Scenario, outcome_id: str, test_id: str, mapping_id: str) -> bytes:
    values = {item.identifier: item.value for item in scenario.outcomes}
    expected = values[outcome_id]
    if target.language == "python":
        return (
            b"# ranex-gauge: placeholder-until-execution-slice\n"
            + trace_comment(target)
            + f"def {target.symbol}():\n    assert {expected!r} == {expected!r}  # {test_id} {mapping_id}\n".encode()
        )
    if target.language in {"typescript", "javascript"}:
        return (
            b"// ranex-gauge: placeholder-until-execution-slice\n"
            + trace_comment(target)
            + f"export function {target.symbol}() {{ return {expected!r}; }} // {test_id} {mapping_id}\n".encode()
        )
    return _sidecar(target)


def _outcome_target(target: Target, outcome_id: str) -> Target:
    """Give every declared outcome its own deterministic executable artifact."""

    if len(target.outcomes) == 1:
        return target
    path = PurePosixPath(target.path)
    return replace(target, path=str(path.with_name(f"{path.stem}.{outcome_id}{path.suffix}")), outcomes=(outcome_id,))


def _refuse_artifact_path_collisions(*categories: tuple[GeneratedArtifact, ...]) -> None:
    paths = [artifact.path for category in categories for artifact in category]
    if len(paths) != len(set(paths)):
        raise ProjectionError(E_SG_ARTIFACT_PATH_COLLISION, "generated artifact paths collide")


def generate_projections(spec_packet: object) -> ProjectionResult:
    """Compile approved, canonical DSL data into views and a closed B manifest."""
    scenario = parse_scenario(spec_packet)
    a_digest = payload_digest(spec_packet)
    pseudocode = (f"SPEC {scenario.domain}:{scenario.task}\n" + "".join(f"RULE {row.identifier} WHEN {row.when} THEN {row.outcome}\n" for row in scenario.rules)).encode()
    outcome_values = {row.identifier: row.value for row in scenario.outcomes}
    transition_by_id = {row.identifier: row for row in scenario.transitions}
    flowchart = ("flowchart TD\n" + "".join(f"  {row.transition}[{transition_by_id[row.transition].source}] -->|{row.identifier}| {row.outcome}[{outcome_values[row.outcome]}]\n" for row in scenario.rules)).encode()
    gauge_targets = tuple(
        _outcome_target(target, outcome_id)
        for target in scenario.targets
        for outcome_id in target.outcomes
    )
    files = tuple(GeneratedArtifact(target.path, _gauge(target, scenario, target.outcomes[0], scenario.test_ids[index % len(scenario.test_ids)], scenario.mapping_ids[index % len(scenario.mapping_ids)])) for index, target in enumerate(gauge_targets))
    traces = tuple(
        GeneratedArtifact(
            target.path + ".ranex-trace",
            canonical_payload_bytes(trace_projection_descriptor(target)),
        )
        for target in gauge_targets
    )
    sidecars = tuple(GeneratedArtifact(target.path + ".ranex-trace.json", _sidecar(target)) for target in gauge_targets if target.language == "sidecar-json")
    expected = tuple(GeneratedArtifact(f"generated/expected/{row.identifier}.json", canonical_payload_bytes({row.identifier: row.value})) for row in scenario.outcomes)
    baselines = tuple(GeneratedArtifact(f"generated/baseline/{row.identifier}.json", canonical_payload_bytes({row.identifier: row.value})) for row in scenario.outcomes)
    controls = tuple(GeneratedArtifact(f"generated/negative/{row.identifier}.json", canonical_payload_bytes({row.identifier: row.value + "__wrong"})) for row in scenario.outcomes)
    pseudocode_flow = (GeneratedArtifact("projections/pseudocode.txt", pseudocode), GeneratedArtifact("projections/flowchart.mmd", flowchart))
    _refuse_artifact_path_collisions(
        pseudocode_flow,
        files,
        expected,
        baselines,
        controls,
        traces,
        sidecars,
    )
    manifest: dict[str, object] = {"version": "generated-artifact-manifest-v1", "domain": scenario.domain, "a_digest": a_digest, "artifacts": {"pseudocode_flow": _rows(pseudocode_flow), "protected": _rows(files), "invocation": {"argv": ["pytest", "-q", *[item.path for item in files]]}, "expected_values": _rows(expected), "baselines": _rows(baselines), "negative_controls": _rows(controls), "trace_projections": _rows(traces), "sidecars": _rows(sidecars)}, "exemptions": []}
    validate_generated_artifact_manifest(manifest, spec_packet=spec_packet)
    return ProjectionResult(a_digest, pseudocode, flowchart, files, traces, sidecars, manifest)


def verify_projection(result: ProjectionResult, spec_packet: object) -> None:
    """Refuse stale or byte-tampered projections by rebuilding their pure output."""
    current = payload_digest(spec_packet)
    if result.a_digest != current:
        raise ProjectionError(E_SG_STALE, "projection A digest is stale")
    expected = generate_projections(spec_packet)
    if result != expected:
        raise ProjectionError(E_SG_INTEGRITY, "projection bytes or manifest differ from deterministic output")
