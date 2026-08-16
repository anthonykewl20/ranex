# SLICE-029 — A/B/C contract freeze

**Status:** done
**Opened:** 2026-08-16
**Priority:** P0 — ADR-017 approval authority needs fixed bytes before lifecycle work.
**ADRs:** `docs/adr/ADR-025-abc-contract-freeze.md`.

## Contract

A is a closed approved semantic SpecPacket with scope, answers, outcomes,
non-goals, oracle provenance, and stable question/rule/transition/outcome/error/
test/mapping IDs; it has no generated hash. B is a closed manifest binding exact
protected artifact bytes, invocation, values, controls, projections, sidecars,
and exemption rows. C is a closed approval payload inside a detached-signature
envelope that binds ADR-017 context, capability bounds, journal-order window,
and four profile digests. Strict raw parsing precedes canonicality and shape;
DSSEv1 PAE supplies domain separation.

## Exact owned paths

- `governance/schemas/specification/spec-packet-v1.schema.json`
- `governance/schemas/specification/generated-artifact-manifest-v1.schema.json`
- `governance/schemas/specification/approval-envelope-v1.schema.json`
- `governance/schemas/specification/error-registry-v1.json`
- `tests/contract/fixtures/specification/abc-v1-vectors.json`
- `src/ranex/foundation/specification_abc.py`
- `tests/contract/test_specification_abc_v1.py`
- `docs/adr/ADR-025-abc-contract-freeze.md` and `docs/adr/prior-art/ADR-025/`
- `docs/slices/SLICE-029-abc-contract-freeze.md`

## Deterministic acceptance gates

1. Frozen positive vectors reproduce byte-identical canonical values and
   digests. `test_positive_vectors_are_canonical_and_digest_stable`.
2. Frozen parser negatives select the exact registry code. `test_negative_vectors_select_registry_codes`.
3. B tampering and C context changes alter identity. `test_bound_identity_changes_when_b_or_c_changes`.
4. Vector goldens are independently recomputed. `test_recorded_vector_digests_recompute`.
5. PAE domain substitution, nonce reuse, and signature tampering refuse.
   `test_envelope_signature_domain_and_nonce_controls`.
6. A/B/C schemas are closed and carry the specified vocabulary.
   `test_closed_payload_shapes_refuse_extra_members`.

## Not owned

- Journal API, chain-row storage, revocation execution, or batch liveness enforcement.
- Lifecycle/grant/admission/CLI integration, suite manifest, harness, and TypeScript mirror.
- Any changes outside the exact owned paths.

## Stop conditions

Stop on an unresolved ADR-017 conflict, a need to alter frozen test expectations,
an inability to keep an error registry authoritative, or a full-suite failure
outside these paths. Do not add a dependency or alter journal behavior.

## Verification commands

```text
uv run --frozen pytest -q tests/contract/test_specification_abc_v1.py tests/contract/test_docs_discipline.py
uv run --frozen pytest -q
```

## Closure

Kernel-side A/B/C contracts merged locally at `b30c6c819`. Frozen vector digests
were corrected pre-review in `3cf4e4e62`; the corrected recorded expectations are
disclosed here because the suite manifest freezes IDs, not vector bodies.

Manifest registration adds only this slice's 20 contract-test IDs. Under
`RANEX_HARNESS_DIR=/tmp/opencode/ranex-harness-absent`, the final suite was
1035 passed / 33 skipped; with the worktree harness configuration it was 1060
passed / 8 skipped. Two independent reviewer families completed three
remediation rounds; all findings are closed. The TypeScript schema/vector mirror
remains a harness-lane follow-up for #12 closure.
