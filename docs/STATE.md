# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-17 (SLICE-054 phase-0 session)
**Active slice:** none.

## Where we stopped

Phase 0 of SLICE-054 (#34, tracker #33) is done: ADR-031
kernel-observability-framework landed on main (see git log for the exact
SHA; commit subject `spec(SLICE-054): phase-0 observability ADR`) as
`proposed`. Research vendored under `docs/adr/prior-art/ADR-031/` — git
trace2 v2.45.2 (tr2_dst.c, tr2_tgt_event.c, tr2_sid.c), pino v9.4.0
redaction.js, structlog 24.4.0 _native.py — all tag-pinned. Two
adversarial panels (fresh-context consensus + independent acceptance)
reviewed it; every finding remediated (review record in the ADR).

## Next

Next slice: SLICE-054
Next work item: tracker-#33 Phase 1 disposable prototype — emitter plus
one CLI stage, invariance spot-check in /tmp or a scratch worktree,
findings posted to #34 — then open the slice and freeze red tests.

Implementer must honor the acceptance panel's key ADR-031 decisions:
two independent trace targets (RANEX_TRACE / RANEX_TRACE_EVENT);
refusal-not-rotation cap with reserved refusal capacity; target
admission refusing governed outputs; open-once descriptors; PARENT_SID
seam = confinement-session controller only (frozen-test amendment at
slice time); strip RANEX_TRACE* from every observed-command environment.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate —
dependency order, not a competing priority. The slice opens only after
the Phase-1 prototype (ADR-013/ADR-016 precedent: ADR before slice).

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; passes isolated and on `origin/main`.
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- mutmut is advisory and was not run this session.
