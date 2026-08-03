# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-03
**Phase:** SLICE-007 closed — the fork is built and bridged to the kernel.
**Active slice:** none. The next slice opens against an owner decision.

## Where we stopped

**SLICE-007 closed** (archived in `docs/slices/done/`): opencode forked at
`v1.18.11` (`012c2f57`), trimmed to the keep-set, plugin surface locked to
compiled-in built-ins, startup fails closed unbridged, and the kernel gained
`task dispatch|judge` (commit-then-materialise). The `§17.5` gear-mesh e2e is
green: dispatch → bridged loop (`ranex-noop/noop`, zero credentials) → bridge
commit + emission → kernel cross-check, materialise, journal `CANDIDATE` —
no PASS minted, approval stays out-of-band. Fork: six commits on `ranex-trim`
in the sibling repo `ranex-harness`. Suite: 355 passed. Mutmut: 3006 mutants,
1685 killed, 1011 survived — the task CLI is subprocess-driven and excluded
from mutation like e2e; treat as weak evidence, per the recorded convention.

## Next

1. **Owner decides the next slice:** unpark `SLICE-006` (Ranex gates a real
   suite, ADR-007) or open first-delegation (`§0.14` build order). Do not
   start either without the decision.
2. The `§17.4` horsepower/fuel baseline was handed to the fork slice and is
   still unmeasured — carry it into the next fork-facing slice.
3. Handbooks unstarted. `RISK-06` and `RISK-07` remain open.

## Known limits

- `ranex-harness` is a local sibling clone; machines without it skip its 21
  fork tests loudly (CI prints the skips via `-rs`).
- `approver_id` unauthenticated (`RISK-07`); same-uid key theft (`RISK-06`);
  confinement (`ADR-006`) unbuilt — the bridge run is unconfined.
- The journal detects an edited row but not a removed one.
- The trim must stay rebaseable; every upstream release costs a measured rebase.
