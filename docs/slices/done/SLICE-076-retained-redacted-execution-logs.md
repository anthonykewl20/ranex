# SLICE-076 — retained, redacted execution logs

**Status:** done
**Opened:** 2026-08-31
**Closed:** 2026-09-01
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

- `tests/unit/test_execution_log_redaction.py` (14 IDs) — env-grammar,
  forced `--redact-env`, PEM-block, and credential-URL redaction; marker
  forms; fixed pass order before truncation.
- `tests/unit/test_retained_logs.py` (18 IDs) — log layout beside outcomes,
  manifest, `keep|replace|off` retention semantics, collision and OSError
  refusals, additive digest-bound outcome `logs` block.
- `tests/integration/test_delegation_command.py` — CLI wiring of the four
  flags and fanout forwarding.
- `tests/e2e/test_execution_log_retention_real.py` (6 IDs) — real retained
  transcripts on this host.
- `tests/security/test_delegate_log_secret_scrubbing.py` (2 IDs) — injected
  real secrets never appear outside their `[REDACTED:*]` markers.
- Suite re-frozen at **1619 IDs** (was 1579; +40), 157 expected skips
  unchanged, freeze golden byte-matched. Full suite: 1588 passed /
  29 skipped; the only failures were the documented concurrent-CAS race
  flake family (nested-journey wrappers, zero branch diff on those files,
  green in isolation — gating file 17 passed, freeze file 6 passed).
- Quality gates: ruff 0.16.2 clean; pyrefly 1.2.0 zero errors; diff-cover
  100% on changed lines.
- Real-host acceptance (transcript attached to issue #58 at
  `/tmp/opencode/issue58-acceptance/acceptance-transcript.txt`): real
  success run (digests verified, canonical outcomes, 0444); real failure +
  truncation (`[ranex truncated: policy=tail dropped=958 retained=4096
  original=5054]`, FINAL reason survives, byte-identical reruns); real
  fanout (3 tasks, pool 2, one failing, parent + child transcripts
  retained); real redaction challenge (Ed25519 PKCS8 PEM, nonce bearer
  token, credential URL, hostile JSON injected into a real leaking harness
  via env + `--redact-env`; `grep -rF PROOF` zero hits for every marker;
  sentinel non-secret line survives; manifest redaction counts recorded).

## Non-goals

- Extending the hash-chained Journal's record grammar to carry log
  references (deferred; see ADR-043 Reversibility).
- Age-based automatic log deletion — retention/cleanup stays operator-owned.
- `task batch qualify` child logs — that path is non-publishable and
  unchanged by this slice.
