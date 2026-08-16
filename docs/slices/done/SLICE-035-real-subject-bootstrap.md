# SLICE-035 — real subject bootstrap

**Status:** done
**Opened:** 2026-08-16
**Priority:** P0 — SLICE-044 must not consume substitute subjects or controller credentials.
**ADR:** `docs/adr/ADR-026-real-subject-bootstrap.md`.

## Contract

Pin Ranex issue #10 and Arxic issue #109 exactly as ADR-017 specifies. The
controller-only Arxic broker resolves only the named keyring reference, uses
the identical process-local helper for HTTPS preflight and no-checkout clone,
and yields a credential-free object store or stable BLOCKED outcome. This is
e2e bootstrap evidence, not product implementation or provider orchestration.

## Exact owned paths

- `tests/e2e/specification/subjects.py`
- `tests/e2e/specification/ranex-subject-v1.json`
- `tests/e2e/specification/arxic-subject-v1.json`
- `tests/e2e/test_specification_subject_bootstrap.py`
- `docs/adr/ADR-026-real-subject-bootstrap.md` and `docs/adr/prior-art/ADR-026/`
- this slice file

## Deterministic acceptance gates

1. Pins, issues, MIT licences, lock digests, and exact command manifests are
   closed facts. `test_subject_manifests_bind_real_subject_facts`.
2. Wrong commit, moved issue, absent licence, lock drift, and unpinned package
   manager refuse with stable reasons. `test_checkout_fact_refusals_are_stable`.
3. Missing credential reference or non-keyring profile blocks before remote
   access. `test_credential_reference_refusal_is_stable`.
4. Preflight and clone have byte-identical process-local helpers; global helper,
   `gh repo clone`, embedded credential, or omission refuses. `test_broker_uses_only_identical_local_helper`.
5. Auth environment/FD forwarding, credential-bearing URL/config/log, dependency
   drift, and failed process refuse. `test_credential_hygiene_refusals_are_stable`.
6. Real Ranex and Arxic bootstrap run only where their hosts qualify; otherwise
   each records an explicit host-gated skip, and an attempted Arxic broker run
   records its actual BLOCKED outcome. `test_real_ranex_bootstrap_or_host_skip`
   and `test_real_arxic_bootstrap_or_host_skip`.
7. Repeated cleanup leaves no clone survivor. `test_broker_cleanup_leaves_no_survivor`.

## Not owned

Subject source, `src/`, other tests, suite manifest, governance, state, README,
harness, global Git/GitHub configuration, provider invocation, and publication.

## Stop conditions

Stop on any credential byte in output, config, URL, log, environment, or
evidence; unknown authority; cleanup doubt; changed pin; process failure; or a
request to substitute a fixture for real subject evidence.

## Verification commands

```text
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
uv run --frozen pytest -q tests/e2e/test_specification_subject_bootstrap.py
uv run --frozen pytest -q
```

## Closure

Focused suite: 17 passed / 2 host-gated skips. The real Ranex bootstrap ran
with `RANEX_SLICE035_REAL=1` and passed. The Arxic `reference-auth-app` path
remains an explicit BLOCKED outcome when its controller-only credential profile
is unavailable; it never substitutes a fixture. Manifest registration declares
both host-gated skips, fixing the P1 honest-skip regression found by the
repository self-gate.
