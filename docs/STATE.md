# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-18 (SLICE-054 complete through remediation; go-live pending)
**Active slice:** none

## Where we stopped

SLICE-054 (#34) implementation complete — ADR-031 substrate landed (emitter,
schema freeze, SID chain, ambient strip, controller seam) with two adversarial
review rounds remediated (dual security + test-layer, then final-gate
cumulative; findings D1-D5/S1-S5a and N1-N6 all closed, records on #34).
Full suite 1229 passed / 38 skipped / 0 failed at the pre-close-out SHA.
Off-state overhead measured: ~1.3-1.6 ms import cumulative, ~84-114 ns
disabled emission. Known residual: the host-gated strict-local confinement
e2e arm (SID tree through a real controller) is skip-declared — needs a
delegated cgroup-v2 host; in-process seams green.

## Next

Next slice: SLICE-054
Next work item: go-live push of the SLICE-054 range, then SLICE-055 — the
real-e2e suite framework; its Phase-0 ADR is still to be written/accepted
per tracker #33. (The literal line above is held by
tests/contract/test_docs_discipline.py until STATE records
"Framework closed: SLICE-055 closed <date>".)

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; passes isolated and on `origin/main`.
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- mutmut: the stats phase cannot complete on the current suite shape
  (subprocess-heavy tests vs the in-process trampoline; exclusion set
  extended twice by sanction, blocked finally by test_observability.py's own
  child-import shape); observability mutants therefore remain unchecked —
  mutation evidence not obtained this session, disclosed as partial.
