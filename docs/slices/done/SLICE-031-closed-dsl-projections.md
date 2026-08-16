# SLICE-031 — closed DSL projections and protected test manifest

**Status:** done
**Opened:** 2026-08-16
**Priority:** P0 — compile approved semantic A into deterministic views and B.
**ADR:** `docs/adr/ADR-028-closed-dsl-projections.md`.

## Contract

This slice accepts only the `ranex-scenario-v1:` closed scenario/oracle DSL in
A semantics. It returns deterministic pseudocode, flowchart, gauges, traces,
sidecars, and exact generated-artifact-manifest v1 B. Prose is carried in A but
cannot become a gauge. Unknown IDs, ambiguous DSL, uncovered rules/outcomes,
or stale projections are typed refusals.

## Exact owned paths

- `src/ranex/specification_generation/__init__.py`
- `src/ranex/specification_generation/scenario.py`
- `src/ranex/specification_generation/projection.py`
- `tests/unit/test_specification_generation.py`
- `tests/contract/fixtures/specification/projection-v1-vectors.json`

## Deterministic acceptance gates

1. Canonical DSL and repeat/subprocess generation produce byte-identical
   pseudocode, flowchart, IDs, mappings, traces, invocation, and B —
   `test_projection_vector_is_repeatable`.
2. Ambiguous, noncanonical, unsupported, duplicate, unmapped, and prose-only
   inputs refuse with stable module codes — `test_closed_dsl_refusals`.
3. Every intended rule/outcome has a protected gauge or recorded exemption —
   `test_projection_requires_protected_coverage`.
4. Wrong outcome, stale A digest, and protected-byte tampering fail —
   `test_negative_controls_stale_and_tampered_bytes_refuse`.
5. Constructed B validates against source A — `test_generated_manifest_validates`.

## Not owned

SLICE-029 A/B/C schemas and validators; lifecycle, approval, grant, persistence,
harness, provider, subject, judge, merge, CLI integration, source coverage, and
SLICE-033 trace verification are explicitly outside this slice.

## Stop conditions

Stop rather than edit SLICE-029-owned files, infer an oracle from prose or
source, widen the closed grammar, change the bound trace/sidecar shapes, or
introduce filesystem, lifecycle, or CLI behavior.

## Verification commands

```text
PYTHONPATH=src uv run --frozen pytest -q tests/unit/test_specification_generation.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen ruff check src/ranex/specification_generation tests/unit/test_specification_generation.py
uv run --frozen pytest -q
```

## Closure

Focused verification: 19 passed. Full suite under the absent-harness
configuration: 1068 passed / 33 skipped. Independent review completed; its
trace-projection remediation landed in `09b6c3435` before integration.
