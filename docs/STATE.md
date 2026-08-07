# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-07
**Active slice:** docs/slices/SLICE-012-provider-watchdog.md

## Where we stopped

SLICE-011 closed (`e0b9886d9`): five durability claims proven red-to-green,
two-reviewer consensus each, consolidated into a digest-bound record at
`docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`.
ADR-015 accepted 2026-08-07 — its Confirmation is built, not asserted.
SLICE-012 is open: the production provider watchdog, the first of the five and
the only one needing no schema change. Work happens in the harness repo.

## Decisions

- ADR-015 **accepted** 2026-08-07, its Confirmation built: at-most-once +
  explicit interruption; watchdog first; no lease/heartbeat/session_execution/
  tool_attempt columns. That bars a parallel execution-state store, not a
  projection over a durable event.
- Claim 3: RED stays executor-level; `retry_attempt`/`retry_next_attempt_at`
  are a projection over the durable event, not a counter table. Both
  supervisor-signed-off, the second independently ruled sound by review.
- The gate resolves the **prototype** record in `docs/slices/` *and*
  `docs/slices/done/`. Deriving it from the open slice was wrong: it refused
  production slices for lacking a record they never carry.

## Next

1. SLICE-012 red-first in the harness: stall a real provider stream inside
   the runner, then refuse it. Idle and absolute must be demonstrated
   independently — two reviewers missed that in the prototype.
2. Replace the prototype's mutable module singleton with real configuration,
   and cover a stall with a tool call in flight (uncovered by claim 1).
3. SLICE-013+ take the remaining four claims, one at a time.

## Known limits

- Prototype code is preserved on five isolated `proto/s011-*` branches in
  `ranex-harness`, never merged into `ranex-trim`. Reference only —
  SLICE-012+ reimplements from the record. Delete when done:
  `git push origin --delete proto/s011-{watchdog,reconciler,retry,blockers,fencing}`.
  The local worktrees were removed 2026-08-07; the branches are the copy.
- The gate checks the record is present, well-formed, GREEN and digest-bound.
  It can NEVER re-verify the bytes — another repo, disposable. Lint with
  teeth, not proof.
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
