# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-18 (SLICE-054 opened; contract tests frozen red)
**Active slice:** docs/slices/SLICE-054-kernel-observability.md

## Where we stopped

SLICE-054 (#34, tracker #33 PHASE 2) is open with its contract tests frozen
RED on main. Phase 1's disposable prototype completed on
`prototype/slice054-phase1` (never merged; findings posted to #34); its
stale scratch-worktree registration was pruned. Slice-time decisions were
adopted per ADR-031's delegation and frozen by
tests/contract/test_trace_schema.py — recorded verbatim in the slice file.
Controller seam frozen: tracing on extends the four-variable controller
env by exactly the enabled trace target variable(s) plus
RANEX_TRACE_PARENT_SID.

Red tests (all error pre-implementation; summary in the test commit
message): tests/unit/test_observability.py,
tests/contract/test_trace_schema.py,
tests/contract/test_trace_invariance.py,
tests/security/test_trace_secret_scrubbing.py. docs-discipline green.

## Next

Next slice: SLICE-054
Next work item: implementation to green (Worker B): ranex.observability
modules, main.py stage boundary + ambient strip (including the
host-qualification ambient copy) + PARENT_SID seam at the
confinement-session controller, the session child's stage boundary, and
the two sanctioned frozen-test amendments in the slice file. Then
test-debug, review, QA gates, go-live; off-state overhead is measured at
slice close. The four frozen test files are read-only; never weaken one to
pass. The SID chain never rides an observed command; a trace problem never
crashes the governed run.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; passes isolated and on `origin/main`.
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- mutmut is advisory and was not run this session.
