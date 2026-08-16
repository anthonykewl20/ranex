"""Frozen SLICE-031 acceptance boundary; implementation follows this red suite."""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import (
    SpecificationABCError,
    canonical_payload_bytes,
    validate_generated_artifact_manifest,
)
from ranex.specification_generation.projection import (
    E_SG_ARTIFACT_PATH_COLLISION,
    E_SG_INTEGRITY,
    E_SG_STALE,
    ProjectionError,
    generate_projections,
    trace_comment,
    trace_projection_descriptor,
    trace_projection_digest,
    verify_projection,
)
from ranex.specification_generation.scenario import (
    E_SG_COVERAGE,
    E_SG_DSL_ABSENT,
    E_SG_DSL_CANONICAL,
    E_SG_DSL_SHAPE,
    E_SG_DUPLICATE,
    E_SG_EMPTY_VOCABULARY,
    E_SG_PATH,
    E_SG_PROSE_ONLY,
    E_SG_SYMBOL,
    E_SG_UNKNOWN_ID,
    E_SG_UNMAPPED,
    E_SG_UNSUPPORTED,
    parse_scenario,
)

VECTORS = json.loads(
    (Path(__file__).parents[1] / "contract/fixtures/specification/projection-v1-vectors.json").read_text(
        "utf-8"
    )
)


def _packet() -> dict[str, object]:
    return copy.deepcopy(VECTORS["packet"])


def _dsl(packet: dict[str, object]) -> dict[str, object]:
    semantics = packet["semantics"]
    assert isinstance(semantics, list)
    entry = semantics[0]
    assert isinstance(entry, str)
    return json.loads(entry.removeprefix("ranex-scenario-v1:"))


def _set_dsl(packet: dict[str, object], value: dict[str, object]) -> None:
    semantics = packet["semantics"]
    assert isinstance(semantics, list)
    semantics[0] = "ranex-scenario-v1:" + canonical_payload_bytes(value).decode("utf-8")


def _mutate_dsl(packet: dict[str, object], mutate: Callable[[dict[str, object]], None]) -> None:
    value = _dsl(packet)
    mutate(value)
    _set_dsl(packet, value)


def _artifact_bytes(result: object, path: str, category: str) -> bytes:
    artifacts = getattr(result, category)
    return next(item.bytes for item in artifacts if item.path == path)


def test_projection_vector_is_repeatable_and_pins_real_bytes() -> None:
    packet = _packet()
    expected = VECTORS["expected"]
    first = generate_projections(packet)
    second = generate_projections(packet)

    assert first == second
    assert first.a_digest == expected["a_digest"]
    assert first.pseudocode == expected["pseudocode_utf8"].encode()
    assert first.flowchart == expected["flowchart_utf8"].encode()
    assert first.manifest["artifacts"] == expected["manifest_rows"]

    scenario = parse_scenario(packet)
    python_target = next(target for target in scenario.targets if target.language == "python")
    sidecar_target = next(target for target in scenario.targets if target.language == "sidecar-json")
    python_trace_path = python_target.path + ".ranex-trace"
    sidecar_trace_path = sidecar_target.path + ".ranex-trace"
    assert trace_comment(python_target) == expected["trace_comment_utf8"].encode()
    assert trace_projection_descriptor(python_target) == json.loads(expected["descriptor_utf8"])
    assert trace_projection_digest(python_target) == expected["descriptor_digest"]
    assert _artifact_bytes(first, python_trace_path, "trace_projections") == expected[
        "descriptor_utf8"
    ].encode()
    assert _artifact_bytes(first, python_trace_path, "trace_projections") == canonical_payload_bytes(
        trace_projection_descriptor(python_target)
    )
    assert expected["trace_comment_utf8"].encode() in _artifact_bytes(
        first, python_target.path, "files"
    )
    assert _artifact_bytes(first, sidecar_target.path + ".ranex-trace.json", "sidecars") == expected[
        "sidecar_utf8"
    ].encode()
    sidecar = json.loads(_artifact_bytes(first, sidecar_target.path + ".ranex-trace.json", "sidecars"))
    assert sidecar["projection"] == trace_projection_digest(sidecar_target)
    assert _artifact_bytes(first, sidecar_trace_path, "trace_projections") == canonical_payload_bytes(
        trace_projection_descriptor(sidecar_target)
    )
    assert b"# ranex-gauge: placeholder-until-execution-slice" in _artifact_bytes(
        first, python_target.path, "files"
    )


def _two_dsl_entries(packet: dict[str, object]) -> None:
    semantics = packet["semantics"]
    assert isinstance(semantics, list)
    semantics.append(semantics[0])


def _noncanonical_dsl(packet: dict[str, object]) -> None:
    value = _dsl(packet)
    version = value.pop("version")
    semantics = packet["semantics"]
    assert isinstance(semantics, list)
    semantics[0] = "ranex-scenario-v1:" + json.dumps(
        {"version": version, **value}, separators=(",", ":")
    )


def _extra_dsl_field(packet: dict[str, object]) -> None:
    _mutate_dsl(packet, lambda value: value.__setitem__("unexpected", "x"))


def _unknown_language(packet: dict[str, object]) -> None:
    _mutate_dsl(packet, lambda value: value["targets"][0].__setitem__("language", "rust"))  # type: ignore[index,union-attr]


def _duplicate_target(packet: dict[str, object]) -> None:
    def mutate(value: dict[str, object]) -> None:
        targets = value["targets"]
        assert isinstance(targets, list)
        targets.append(copy.deepcopy(targets[0]))

    _mutate_dsl(packet, mutate)


def _unmapped_outcome(packet: dict[str, object]) -> None:
    _mutate_dsl(packet, lambda value: value["outcomes"][0].__setitem__("id", "O-2"))  # type: ignore[index,union-attr]


def _unknown_target_id(packet: dict[str, object]) -> None:
    _mutate_dsl(packet, lambda value: value["targets"][0].__setitem__("rules", ["R-9"]))  # type: ignore[index,union-attr]


def _uncovered_outcome(packet: dict[str, object]) -> None:
    def mutate(value: dict[str, object]) -> None:
        outcomes = value["outcomes"]
        assert isinstance(outcomes, list)
        outcomes.append({"id": "O-2", "value": "rejected"})

    ids = packet["ids"]
    provenance = packet["oracle_provenance"]
    assert isinstance(ids, dict) and isinstance(provenance, dict)
    ids["outcome"] = ["O-1", "O-2"]
    provenance["O-2"] = "requirement"
    _mutate_dsl(packet, mutate)


def _prose_only(packet: dict[str, object]) -> None:
    packet["semantics"] = ["prose only"]


def _empty_vocabulary(packet: dict[str, object]) -> None:
    ids = packet["ids"]
    assert isinstance(ids, dict)
    ids["test"] = []


def _empty_mapping_vocabulary(packet: dict[str, object]) -> None:
    ids = packet["ids"]
    assert isinstance(ids, dict)
    ids["mapping"] = []


def _unsafe_path(packet: dict[str, object]) -> None:
    _mutate_dsl(packet, lambda value: value["targets"][0].__setitem__("path", "../unsafe.py"))  # type: ignore[index,union-attr]


def _unsafe_symbol(packet: dict[str, object]) -> None:
    _mutate_dsl(packet, lambda value: value["targets"][0].__setitem__("symbol", "bad-name"))  # type: ignore[index,union-attr]


def _unsafe_outcome(packet: dict[str, object], identifier: str) -> None:
    ids = packet["ids"]
    provenance = packet["oracle_provenance"]
    assert isinstance(ids, dict) and isinstance(provenance, dict)
    ids["outcome"] = [identifier]
    value = provenance.pop("O-1")
    provenance[identifier] = value

    def mutate(dsl: dict[str, object]) -> None:
        dsl["outcomes"][0]["id"] = identifier  # type: ignore[index]
        dsl["rules"][0]["outcome"] = identifier  # type: ignore[index]
        dsl["targets"][0]["outcomes"] = [identifier]  # type: ignore[index]

    _mutate_dsl(packet, mutate)


def _artifact_collision(packet: dict[str, object]) -> None:
    def mutate(value: dict[str, object]) -> None:
        targets = value["targets"]
        assert isinstance(targets, list)
        target = copy.deepcopy(targets[0])
        assert isinstance(target, dict)
        target["path"] = "tests/generated/test_acceptance.py.ranex-trace"
        target["symbol"] = "test_acceptance_trace"
        targets.append(target)

    _mutate_dsl(packet, mutate)


def _stale_projection(packet: dict[str, object]) -> None:
    packet["revision"] = 2


@pytest.mark.parametrize(
    ("code", "mutate", "entry_point"),
    [
        (E_SG_DSL_ABSENT, _two_dsl_entries, parse_scenario),
        (E_SG_DSL_CANONICAL, _noncanonical_dsl, parse_scenario),
        (E_SG_DSL_SHAPE, _extra_dsl_field, parse_scenario),
        (E_SG_UNSUPPORTED, _unknown_language, parse_scenario),
        (E_SG_DUPLICATE, _duplicate_target, parse_scenario),
        (E_SG_UNMAPPED, _unmapped_outcome, parse_scenario),
        (E_SG_UNKNOWN_ID, _unknown_target_id, parse_scenario),
        (E_SG_PROSE_ONLY, _prose_only, parse_scenario),
        (E_SG_COVERAGE, _uncovered_outcome, parse_scenario),
        (E_SG_EMPTY_VOCABULARY, _empty_vocabulary, parse_scenario),
        (E_SG_EMPTY_VOCABULARY, _empty_mapping_vocabulary, parse_scenario),
        (E_SG_PATH, _unsafe_path, parse_scenario),
        (E_SG_SYMBOL, _unsafe_symbol, parse_scenario),
        (E_SG_ARTIFACT_PATH_COLLISION, _artifact_collision, generate_projections),
    ],
)
def test_closed_dsl_refusals(
    code: str,
    mutate: Callable[[dict[str, object]], None],
    entry_point: Callable[[object], object],
) -> None:
    packet = _packet()
    mutate(packet)
    with pytest.raises(ProjectionError) as refused:
        entry_point(packet)
    assert refused.value.code == code


@pytest.mark.parametrize("identifier", ("O/2", r"O\2", "..", " "))
def test_outcome_ids_that_cannot_be_filenames_refuse_as_projection_errors(identifier: str) -> None:
    packet = _packet()
    _unsafe_outcome(packet, identifier)
    with pytest.raises(ProjectionError):
        parse_scenario(packet)


@pytest.mark.parametrize("code", [E_SG_STALE, E_SG_INTEGRITY])
def test_projection_staleness_and_integrity_refusals(code: str) -> None:
    packet = _packet()
    result = generate_projections(packet)
    if code == E_SG_INTEGRITY:
        result = result.with_file_bytes("tests/generated/test_acceptance.py", b"x")
    else:
        _stale_projection(packet)
    with pytest.raises(ProjectionError) as refused:
        verify_projection(result, packet)
    assert refused.value.code == code


def test_manifest_binds_to_source_packet_and_rejects_tampered_a_digest() -> None:
    packet = _packet()
    result = generate_projections(packet)
    validate_generated_artifact_manifest(result.manifest, spec_packet=packet)
    tampered = copy.deepcopy(result.manifest)
    tampered["a_digest"] = "sha256:" + "f" * 64
    with pytest.raises(SpecificationABCError) as refused:
        validate_generated_artifact_manifest(tampered, spec_packet=packet)
    assert refused.value.code == "E-ABC-017"


def test_multi_outcome_target_emits_one_gauge_and_expected_value_per_outcome() -> None:
    packet = _packet()
    def add_outcome(value: dict[str, object]) -> None:
        value["outcomes"].append({"id": "O-2", "value": "rejected"})  # type: ignore[index,union-attr]
        value["targets"][0]["outcomes"].append("O-2")  # type: ignore[index,union-attr]
    ids = packet["ids"]; provenance = packet["oracle_provenance"]
    assert isinstance(ids, dict) and isinstance(provenance, dict)
    ids["outcome"].append("O-2"); provenance["O-2"] = "requirement"
    _mutate_dsl(packet, add_outcome)
    result = generate_projections(packet)
    expected = result.manifest["artifacts"]["expected_values"]  # type: ignore[index]
    assert {row["path"] for row in expected} == {"generated/expected/O-1.json", "generated/expected/O-2.json"}
    assert len(result.files) == 3


def test_cross_process_generation_is_byte_identical() -> None:
    script = """
import base64
import json
import sys
from ranex.foundation.specification_abc import canonical_payload_bytes
from ranex.specification_generation.projection import generate_projections

result = generate_projections(json.loads(sys.stdin.read()))
value = {
    "pseudocode": base64.b64encode(result.pseudocode).decode(),
    "flowchart": base64.b64encode(result.flowchart).decode(),
    "files": [(item.path, base64.b64encode(item.bytes).decode()) for item in result.files],
    "traces": [(item.path, base64.b64encode(item.bytes).decode()) for item in result.trace_projections],
    "sidecars": [(item.path, base64.b64encode(item.bytes).decode()) for item in result.sidecars],
    "manifest": result.manifest,
}
sys.stdout.buffer.write(canonical_payload_bytes(value))
"""
    source = Path(__file__).parents[2] / "src"
    environment = {**os.environ, "PYTHONPATH": str(source)}
    command = [sys.executable, "-c", script]
    first = subprocess.run(
        command,
        input=json.dumps(_packet()),
        text=True,
        capture_output=True,
        check=True,
        env=environment,
    )
    second = subprocess.run(
        command,
        input=json.dumps(_packet()),
        text=True,
        capture_output=True,
        check=True,
        env=environment,
    )
    assert first.stdout.encode() == second.stdout.encode()
