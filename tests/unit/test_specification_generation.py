"""Frozen SLICE-031 acceptance boundary; implementation follows this red suite."""

from __future__ import annotations

import pytest

from ranex.foundation.specification_abc import validate_generated_artifact_manifest
from ranex.specification_generation.projection import (
    E_SG_PROSE_ONLY,
    ProjectionError,
    generate_projections,
    verify_projection,
)
from ranex.specification_generation.scenario import parse_scenario


def _packet(*, semantics: list[str] | None = None) -> dict[str, object]:
    scenario = (
        '{"outcomes":[{"id":"O-1","value":"accepted"}],"rules":'
        '[{"id":"R-1","outcome":"O-1","transition":"T-1","when":'
        '"request.valid"}],"targets":[{"language":"python","outcomes":'
        '["O-1"],"path":"tests/generated/test_acceptance.py","rules":'
        '["R-1"],"symbol":"test_acceptance","transitions":["T-1"]}],'
        '"transitions":[{"from":"request","id":"T-1","to":"accepted"}],'
        '"version":"ranex-scenario-v1"}'
    )
    return {
        "version": "spec-packet-v1", "domain": "kernel", "task": "SLICE-031",
        "revision": 1, "semantics": semantics or ["ranex-scenario-v1:" + scenario],
        "scope": {"include": ["src"], "exclude": []}, "answers": {},
        "observable_outcomes": ["accepted"], "non_goals": ["prose"],
        "oracle_provenance": {"O-1": "requirement"},
        "ids": {"question": [], "rule": ["R-1"], "transition": ["T-1"],
                "outcome": ["O-1"], "error": [], "test": ["TEST-1"],
                "mapping": ["M-1"]},
    }


def test_projection_vector_is_repeatable() -> None:
    first = generate_projections(_packet())
    second = generate_projections(_packet())
    assert first == second
    assert first.pseudocode == b"SPEC kernel:SLICE-031\nRULE R-1 WHEN request.valid THEN O-1\n"
    assert first.flowchart == b"flowchart TD\n  T-1[request] -->|R-1| O-1[accepted]\n"
    assert first.trace_projections[0].bytes.startswith(b"# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection=sha256:")


def test_closed_dsl_refusals() -> None:
    with pytest.raises(ProjectionError, match=E_SG_PROSE_ONLY):
        parse_scenario(_packet(semantics=["prose only"]))


def test_projection_requires_protected_coverage() -> None:
    packet = _packet()
    packet["ids"] = {**packet["ids"], "outcome": ["O-1", "O-2"]}  # type: ignore[arg-type]
    with pytest.raises(ProjectionError):
        generate_projections(packet)


def test_negative_controls_stale_and_tampered_bytes_refuse() -> None:
    result = generate_projections(_packet())
    with pytest.raises(ProjectionError):
        verify_projection(result, {**_packet(), "revision": 2})
    tampered = result.with_file_bytes("tests/generated/test_acceptance.py", b"x")
    with pytest.raises(ProjectionError):
        verify_projection(tampered, _packet())


def test_generated_manifest_validates() -> None:
    packet = _packet()
    result = generate_projections(packet)
    validate_generated_artifact_manifest(result.manifest)
    verify_projection(result, packet)
