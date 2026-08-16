# ADR-028 — closed DSL projections

**Status:** accepted
**Date:** 2026-08-16
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-031-closed-dsl-projections.md`

## Context and Problem Statement

ADR-017 requires generated views and executable gauges to be derived from an
approved SpecPacket, but prose cannot safely become an oracle. A projection
must be reproducible, bind its bytes in B, and refuse unknown or uncovered
semantics rather than guessing a test from source observation.

## Decision Drivers

- Compile only a small, closed scenario/oracle grammar encoded in A semantics.
- Sort every order-irrelevant collection before rendering or hashing.
- Bind comments and sidecars to exact IDs and a raw canonical projection digest.
- Make every rule and outcome protected by a gauge or an explicit B exemption.

## Prior art

- Searched: GitHub code search for deterministic state-machine traversal,
  executable scenario grammars, and code-generator output ordering.
- [XState adjacency traversal at commit c25dba07a2b68565edbe83d83c5d679dd85e00b2](https://github.com/statelyai/xstate/blob/c25dba07a2b68565edbe83d83c5d679dd85e00b2/packages/core/src/graph/adjacency.ts)
  bounds queue traversal and derives edges from declared transitions.
  License: MIT.
  Weakness: it accepts executable machine logic and therefore
  cannot distinguish approved intent from observed behavior.
  Vendored: docs/adr/prior-art/ADR-028/xstate-adjacency.ts blob:0bbe6c3c0f878e0839374d7ad7a6617cc5404d6c
- [Gherkin token matcher at v36.0.0](https://github.com/cucumber/gherkin/blob/v36.0.0/javascript/src/GherkinClassicTokenMatcher.ts)
  recognizes a finite scenario vocabulary and resolves ambiguous steps explicitly.
  License: MIT.
  Weakness: natural-language feature text and dialects remain too
  broad to compile Ranex acceptance gauges without a separately closed oracle.
  Vendored: docs/adr/prior-art/ADR-028/gherkin-token-matcher.ts blob:0aeec9ff00170cd5e5c1ef9c3f57df8e7b9e1f29
- Rejected: https://github.com/OpenAPITools/openapi-generator Its broad template
  and language-plugin surface permits output policy outside the approved packet,
  so it cannot be the small deterministic acceptance-gauge boundary required here.
- Rejected: https://github.com/mermaid-js/mermaid Its renderer is valuable for
  display but accepts a broad diagram language and browser rendering variance,
  rather than defining the canonical graph bytes which B must bind.

## Considered Options

1. A closed JSON-in-string scenario DSL with sorted rendering: chosen.
2. Compile arbitrary semantic prose: rejected; prose is not an acceptance oracle.
3. Use source observation to infer gauges: rejected; it preserves existing defects.
4. Store rendered views as independent authority: rejected; A remains authority.

## Decision Outcome

One A `semantics` string has prefix `ranex-scenario-v1:` followed by canonical
JSON. Its closed object declares `rules`, `transitions`, `outcomes`, and
`targets`; all rule/transition/outcome IDs in A occur exactly once in this DSL.
Targets name a path, symbol, language, and nonempty rule/transition/outcome IDs.
Only `python`, `typescript`, `javascript`, and `sidecar-json` are supported.

The generator sorts rows by ID/path, emits pseudocode and Mermaid flow text,
gauge, expected-value, baseline, negative-control, trace, and sidecar bytes,
then constructs B from their SHA-256 digests. A trace object is exactly
`{"version":"trace-projection-v1","path":str,"language":str,"ids":{"rule":[str],"transition":[str],"outcome":[str]},"anchor":{"symbol":str}}`.
Its digest is raw SHA-256 of `canonical_payload_bytes(object)`, not a PAE digest.

### Consequences

- Python traces use `#`; TypeScript and JavaScript traces use `//`.
- Sidecar-json targets use the closed approved sidecar JSON shape.
- Comments and sidecars are coverage claims, not acceptance evidence.
- A changed A digest makes an older projection object stale and refuses it.
- `TRACE_PROJECTION_VERSION`, `trace_projection_descriptor(target)`, and
  `trace_projection_digest(target)` are the exported v1 trace contract for
  SLICE-033 and its tests. Every target emits a `.ranex-trace` artifact whose
  bytes are the canonical descriptor; its artifact digest is the comment
  projection value. A sidecar-json target also has that trace row with
  `language: "sidecar-json"`, and its sidecar `projection` carries the same
  digest.

### Confirmation

`tests/unit/test_specification_generation.py` freezes positive goldens, repeated
generation, DSL refusals, coverage, stale/tamper controls, and B validation.
`tests/contract/fixtures/specification/projection-v1-vectors.json` carries exact
bytes and digests. SLICE-033 consumes the trace and sidecar shapes verbatim.

## Improvements on the prior art

XState's declared-edge traversal is retained, but input is data rather than a
runtime machine. Gherkin's closed-token lesson is retained, but its prose and
dialect surface is replaced with canonical JSON and an explicit oracle value.

## Architecture surface

`specification_generation.scenario` owns parsing and closed-vocabulary refusal.
`specification_generation.projection` owns render bytes, traces, sidecars, and B
construction. Foundation A/B validation remains unchanged; no lifecycle, CLI,
approval, journal, harness, or judge code is introduced.

## Scope and threat delta

This removes output-order drift, unbound trace IDs, prose-derived oracles,
unprotected outcomes, stale projections, and byte-tampered protected artifacts.
It does not verify source coverage, execute generated gauges, approve semantics,
or authorize a worker; those remain later slices.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Determinism | same A twice | byte-identical projection bytes and B |
| Integrity | one artifact byte changes | B digest changes |
| Auditability | trace readback | exact IDs and raw projection digest |

## Reversibility

Door: two-way

A future grammar version uses a new prefix and projection version. v1 bytes and
their digest meanings remain immutable; deleting the generator removes no A/B
historical evidence.

## Sad paths

- 1. No DSL string or two DSL strings: refuse ambiguity.
- 2. Noncanonical DSL JSON: refuse before interpretation.
- 3. Unknown language or extra DSL field: refuse.
- 4. Duplicate ID in A or DSL: refuse.
- 5. A rule, transition, or outcome lacks DSL backing: refuse.
- 6. A target refers to an unknown ID: refuse.
- 7. A rule or outcome has no protected target/exemption: refuse.
- 8. Prose-only assertion attempts a gauge: refuse.
- 9. Old A digest is supplied with a projection: refuse stale.
- 10. One protected byte changes: resulting B differs and verification fails.

## Test strategy

Golden vectors pin canonical DSL normalization, pseudocode, flowchart, artifact
bytes, comments, sidecars, B, and digest values. `tests/unit/test_specification_generation.py`
alters an outcome, A digest, and protected byte, verifies stable typed codes for
each refusal class, and calls the frozen B validator against source A.

## Code review checklist

- Are all DSL shapes and vocabularies closed before rendering?
- Are unordered arrays sorted and required ordered arrays retained as declared?
- Does each comment exactly use the SLICE-033 trace grammar?
- Can prose or observed-only input create a gauge?
- Does B bind every emitted protected byte and exact A digest?

## More Information

Vendored bytes prove they were obtained, not that they came from the cited URL.
The parser accepts no user templates, providers, source readers, or filesystem
writes; callers decide where returned deterministic bytes are materialized.
