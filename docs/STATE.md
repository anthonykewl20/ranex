# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-07
**Active slice:** docs/slices/SLICE-011-durable-execution-prototype.md

## Where we stopped

SLICE-010 is closed and committed (15614e6fc). SLICE-011 prototyped its five
claims in parallel, one scratch harness worktree each
(`../ranex-harness-wt1..5-*`), per ADR-013/ADR-015. Claims 1-4 (watchdog,
reconciler, durable retry, durable blockers) are red-to-green with negative
controls and digest-bound `EXIT_RECORD.json`s, every gate re-run against disk
by the supervisor. Claim 5 proves the fence but its fixture is unstable.

## Decisions

- ADR-015 decisions stand: at-most-once + explicit interruption; watchdog
  first; no lease/heartbeat/session_execution/tool_attempt columns.
- Kernel-repo agent-manager issues renumbered SLICE-020-028 (2026-08-07) to
  clear the collision with the durability track; `blocked-slice-010` labels
  dropped. ADR-014 predates the renumbering and cites the old numbers.
- Claim 3: RED stays executor-level (no session-layer retry state exists
  pre-GREEN); `retry_attempt`/`retry_next_attempt_at` are a projection over
  the durable event, not a counter table. Both supervisor-signed-off.

## Next

1. Claim 5: `PRAGMA busy_timeout` before `journal_mode` in the fixture
   worker, surface worker stderr, re-run the full suite 20x, correct the
   record's stability claim.
2. Consolidate the five per-claim records into one digest-bound SLICE-011
   record committed to THIS repo — the worktrees are disposable.
3. Extend `tests/contract/test_docs_discipline.py` (criterion 8): refuse a
   durability production slice without a green, digest-bound record.
4. Milestone #1 on `anthonykewl20/ranex-harness` (issues #1-#9) carries the
   production plan; production slices SLICE-012+ open one at a time.

## Known limits

- **Never `git worktree remove`/`prune` the five harness worktrees.** Every
  prototype and all five EXIT_RECORDs are uncommitted and untracked there.
- Claim 5 flakes ~12% (2/16 full runs): the fixture worker sets busy_timeout
  after journal_mode, so concurrent spawns hit "database is locked". Fence
  semantics are unaffected.
- Claims 2 and 3 carry reviewer-hy3 only; cross-family consensus is open,
  disclosed in both records (done-criterion 7).
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
- Both repos have unpushed commits — push only on the owner's word.
