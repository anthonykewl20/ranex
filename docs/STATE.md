# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-07
**Active slice:** none — SLICE-011 closed; SLICE-012 not yet opened.

## Where we stopped

SLICE-011 is closed: all nine done criteria met. Five durability claims proven
red-to-green with negative controls, one disposable harness worktree each, all
five with two-reviewer consensus, consolidated into a digest-bound record at
`docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`.
Criterion 8's compiled gate now refuses a durability production slice unless
that prototype record is present, GREEN and digest-bound.

## Decisions

- ADR-015 stands and stays `proposed`: at-most-once + explicit interruption;
  watchdog first; no lease/heartbeat/session_execution/tool_attempt columns.
- Claim 3: RED stays executor-level; `retry_attempt`/`retry_next_attempt_at`
  are a projection over the durable event, not a counter table. Both
  supervisor-signed-off, the second independently ruled sound by review.
- The gate resolves the **prototype** record in `docs/slices/` *and*
  `docs/slices/done/`. Deriving it from the open slice was wrong: it refused
  production slices for lacking a record they never carry.

## Next

1. Open SLICE-012 — the first production durability slice, one at a time,
   gated by the record. Milestone #1 on `anthonykewl20/ranex-harness`
   (issues #2-#6) carries the plan; watchdog (#2) is the highest-value start.
2. Before any of it ships, work the `open_before_slice_012` list in the
   record: unwired startup sweep, no owner-release path, no blocker
   migration, projector tx handle, and the ADR-015 wording carry-forward.

## Known limits

- The prototype **diffs** are not preserved — only the records. Deleting the
  five worktrees loses the implementations; SLICE-012+ reimplements from the
  record. That is ADR-013's design; confirm before pruning.
- The gate checks the record is present, well-formed, GREEN and digest-bound.
  It can NEVER re-verify the bytes — another repo, disposable. Lint with
  teeth, not proof.
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
