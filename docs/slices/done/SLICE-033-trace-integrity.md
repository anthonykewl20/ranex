# SLICE-033 — Trace-reference integrity and independent verifier ports

**Status:** done
**Opened:** 2026-08-16
**Priority:** P0 — approved specifications need independently checked references.
**ADRs:** `docs/adr/ADR-029-trace-integrity.md`.

## Contract

Given frozen A/B/C, base and candidate trees, and independent gauge observations,
refuse every changed in-scope source hunk unless exactly one current generated
comment or approved sidecar covers it, or its exact signed B exemption applies.
Trace facts never imply an executable outcome; an approved outcome observation
must separately match protected expected-value bytes.

## Exact owned paths

- `src/ranex/governed_execution/domain/specification_trace.py`
- `src/ranex/governed_execution/application/specification_verification.py`
- `tests/unit/test_specification_trace.py`
- `tests/integration/test_specification_verification.py`
- `docs/adr/ADR-029-trace-integrity.md` and `docs/adr/prior-art/ADR-029/`
- `docs/slices/SLICE-033-trace-integrity.md`

## Deterministic acceptance gates

1. Exact comments/exemptions cover every changed source hunk. `test_comment_and_exact_exemption_cover_changed_hunks`.
2. Distinct refusal codes cover malformed reference/exemption partitions. `test_reference_refusals_have_distinct_stable_codes`.
3. Approved sidecars work; unapproved or mismatched sidecars refuse. `test_sidecar_approval_and_mismatch_refusals`.
4. Exemption path/class/reason drift and moved changes refuse. `test_exemption_drift_and_moved_change_refuse`.
5. Protected bytes and invocation refuse before outcomes. `test_protected_artifact_and_invocation_precede_outcome_evaluation`.
6. Wrong explicit gauge result refuses despite valid coverage/exemption. `test_wrong_outcome_refuses_despite_current_trace_or_exemption`.
7. Equal inputs produce equal fact bytes and codes. `test_verification_facts_are_byte_identical_for_identical_inputs`.

## Not owned

- Generator, A/B/C schemas or registry, approval/grants, persistence, judge,
  CLI, harness, providers, merge, E2E integration, suite manifest, README, and
  STATE.

## Stop conditions

Stop if this requires altering SLICE-029's A/B/C contract, adding wildcard
matching, altering frozen red tests, or making trace markers semantic oracles.

## Closure

Focused verification: 23 verifier tests passed; the generator-to-verifier E2E
passed for Python, TypeScript, and JavaScript plus a protected-byte refusal.
The frozen red cases landed in `fa9e363cb`; reviewer remediation landed in
`76c57d24c`, `7ec7acd9e`, and `29526807f`, before merge `8620cc3c5`.

Integration adjudications retained strict comment-to-symbol adjacency: gauges
now emit their placeholder before the anchor; JavaScript is source-discovered;
and the verifier recognizes the generator's `export function name(` form. The
generated expected-value mapping now keys values by the approved outcome ID.
SLICE-036 owns later CAS/persistence and SpecificationEvent wiring; no trace
anchor is executable-outcome authority.

## Verification commands

```text
uv run --frozen pytest -q tests/unit/test_specification_trace.py tests/integration/test_specification_verification.py
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen ruff check src/ranex/governed_execution tests/unit/test_specification_trace.py tests/integration/test_specification_verification.py
uv run --frozen pytest -q
```
