# SLICE-076 — retained, redacted execution logs

**Status:** open
**Opened:** 2026-08-31
**Priority:** P0 — production blocker (issue #58)
**Issue:** #58
**ADR:** docs/adr/ADR-043-retained-redacted-execution-logs.md

## Contract

Issue #58 acceptance criteria (verbatim):

- Real delegate and fanout runs retain operator-readable stdout/stderr or an
  equivalent structured transcript.
- Durable outcomes contain stable references and integrity digests for
  retained logs.
- Credentials, signing material, private environment values, and configured
  sensitive fields are redacted before persistence.
- Truncation is explicit, bounded, deterministic, and does not erase the
  terminal failure reason.
- Retention and cleanup behavior is documented and configurable within safe
  bounds.
- Acceptance includes real success and failure runs, a redaction challenge
  using real secret injection, and attached retained artifacts.

## Owned paths

- New: `src/ranex/execution/__init__.py`, `src/ranex/execution/log_redaction.py`,
  `src/ranex/execution/retained_logs.py`
- Modify: `src/ranex/cli/delegation.py`, `src/ranex/cli/fanout.py`,
  `src/ranex/cli/main.py`
- Tests: `tests/unit/test_execution_log_redaction.py`,
  `tests/unit/test_retained_logs.py`, additions to
  `tests/integration/test_delegation_command.py`,
  `tests/e2e/test_execution_log_retention_real.py`,
  `tests/security/test_delegate_log_secret_scrubbing.py`
- Docs close-out: this slice file, `docs/STATE.md`, README (later tranche)

## Done criteria

1. Delegate and fanout runs persist bounded, redacted per-stream logs beside
   their outcome files, at the layout ADR-043 fixes.
2. Outcomes carry the additive `logs` block (or the explicit
   `retained: false` block under `--log-retention off`), digest-bound to the
   retained bytes.
3. The redaction passes (ambient env, `--redact-env`, PEM, credential-URL)
   run in fixed order before truncation; a security test injects a real
   secret and proves it never appears outside its `[REDACTED:*]` marker.
4. Truncation is bounded by `--log-max-bytes` (default 262144, bounds
   [4096, 8388608]), preserves the tail, and prepends a deterministic marker.
5. `--log-retention keep|replace|off` behave exactly as ADR-043 states,
   including the `keep`-collision and OSError refusals.
6. Fanout forwards the new flags to each child delegate and persists its own
   parent transcript and manifest.
7. All new/modified tests listed under Owned paths pass; the frozen suite
   manifest is re-frozen to include their IDs.

## Tranche plan

- T0 (this tranche): governed docs — ADR-043 accepted with vendored prior
  art, this slice opened, STATE/README active-slice pointers flipped.
- T1: implementation tranche — `src/ranex/execution/` modules, CLI wiring,
  new tests frozen red then proven green (owned by a separate agent working
  concurrently in `src/` and `tests/`).
- T2: real-data acceptance evidence — real success and failure delegate/
  fanout runs, a real secret-injection redaction challenge, retained
  artifacts attached to issue #58.
- T3: docs close-out — slice moved to `docs/slices/done/`, STATE/README
  updated, suite manifest re-frozen.

## Evidence

- `tests/unit/test_execution_log_redaction.py`,
  `tests/unit/test_retained_logs.py`,
  `tests/integration/test_delegation_command.py`,
  `tests/e2e/test_execution_log_retention_real.py`,
  `tests/security/test_delegate_log_secret_scrubbing.py` (to be added/
  extended by T1).
- Acceptance transcript (real runs, real secret-injection challenge, and
  attached retained artifacts) to be attached to issue #58 at T2.

## Non-goals

- Extending the hash-chained Journal's record grammar to carry log
  references (deferred; see ADR-043 Reversibility).
- Age-based automatic log deletion — retention/cleanup stays operator-owned.
- `task batch qualify` child logs — that path is non-publishable and
  unchanged by this slice.
