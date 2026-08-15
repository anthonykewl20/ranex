# SLICE-047 — confinement hardening

**Status:** open
**Opened:** 2026-08-15
**Priority:** P0 — SLICE-046's signer-to-controller boundary presently permits
ambient authority and duplicate result validation.
**ADRs:** `docs/adr/ADR-023-the-confinement-session-is-invoked-as-a-subprocess.md`
and `docs/adr/ADR-024-single-source-confinement-validation-and-least-authority-invocation.md`.

## Contract

`ranex-confinement-result-v1` has one strict validator for both in-memory
emission and raw-byte consumption: exact schema, canonical bytes, complete
teardown, three lower-case SHA-256 profile digests, and an `int` (not `bool`)
command exit code. `E-C18-RESULT` remains both a ValueError message in `main`
and an E-C18-prefixed `HostConfinementError` in the controller.

The controller receives exactly `PATH`, `PYTHONPATH`, `LC_ALL`, and `TZ`. On a
30-second timeout, its process group is killed and reaped before
`E-C46-CONTROLLER` refuses with no evidence. null confinement digests record an
unconfined run — explicit absence, never forged presence.

## Exact owned paths

Product implementation may change only:

- `src/ranex/foundation/confinement_result.py` (new shared validator)
- `src/ranex/cli/main.py` (shared call, fixed environment, Popen timeout path)
- `src/ranex/cli/host_confinement.py` (delegating emitter and error mapping)
- `tests/unit/test_confinement_result.py` and
  `tests/security/test_slice047_confinement_hardening.py`
- `tests/integration/test_slice017_native_launcher.py` (`MAIN_PY_SHA256`
  refreshed by the implementer)
- `tests/security/test_slice046_cmd_run_confinement.py` (declared Popen-shim
  re-aim retaining its existing binding scenarios)

## Deterministic acceptance gates

1. The shared validator accepts the frozen good sample and rejects all closed
   contract partitions with `E-C18-RESULT`.
   `tests/unit/test_confinement_result.py`.
2. Producer emission rejects a non-hex digest before bytes leave the controller.
   `tests/unit/test_confinement_result.py` and gate8's
   `tests/integration/test_slice018_confinement_session.py`.
3. Strict-local CLI invocation exposes exactly four environment keys and never
   the injected signing key. `tests/security/test_slice047_confinement_hardening.py`.
4. Timeout and kill-race paths refuse as `E-C46-CONTROLLER` without evidence.
   `tests/security/test_slice047_confinement_hardening.py`.
5. The six SLICE-046 scenarios remain green plus one declared host skip:
   `tests/security/test_slice046_cmd_run_confinement.py`.
6. Full frozen suite including `tests/contract/test_docs_discipline.py` is green.

## Not owned

- Claim-type enforcement of confinement digests in `verdict.py`, admission, or
  loaders; it is explicitly deferred to SLICE-048.
- `governance/gates.yaml`, CI workflow, suite semantics, and the owner's open
  CI skip/fail decision.
- Harness files, evidence format, signing fields, journal schema, and gate8
  lifecycle semantics.
- Active reconciliation of a worker cgroup leaf left by a SIGKILLed controller.

## Stop conditions

Stop rather than inherit an ambient variable, weaken validation, rename an
existing E-C18 code, edit frozen tests outside declared re-aim/hash work, change
a non-owned path, or add claim-type enforcement. A future environment need is a
loud failure requiring an ADR-backed allowlist change.

## Verification commands

```text
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
PYTHONPATH=src uv run --frozen pytest -q tests/unit/test_confinement_result.py tests/security/test_slice047_confinement_hardening.py
PYTHONPATH=src uv run --frozen pytest -q tests/security/test_slice046_cmd_run_confinement.py
uv run --frozen pytest -q
```

## Review disposition

- Post-kill reaping is capped at 5s and fails closed if a descendant survives.
- The import guard now rejects every direct host-confinement import form.
- Dead LC_ALL/TZ fallback is a named follow-up, not removed to avoid descriptor-producer churn.

## Closure

- Done criteria met: 17 frozen tests green (16 red→green); SLICE-046 remains 6 pass / 1 skip.
- Independent double review APPROVE: 0 P0–P2; P3s dispositioned above.
- Full-suite result: 1040 passed, 8 skipped (verified after rebase).
- Follow-ups: SLICE-048 claim-type digest enforcement; dead LC_ALL/TZ fallback; worker-cgroup-leaf reconciliation remains out of scope.
