# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-07
**Active slice:** docs/slices/SLICE-011-durable-execution-prototype.md

## Where we stopped

SLICE-011's five durability claims are all proven red-to-green with negative
controls, one disposable harness worktree per claim at an identical HEAD.
Every gate was re-run against disk by the supervisor, never read from the
session that produced it. The five per-claim records are consolidated,
embedded and hash-bound in
`docs/slices/SLICE-011-durable-execution-prototype.exit-record.json`
(`5bf20ac0c`). Criteria 1-7 and 9 are met; criterion 8 keeps the slice open.

## Decisions

- ADR-015 stands and stays `proposed`: at-most-once + explicit interruption;
  watchdog first; no lease/heartbeat/session_execution/tool_attempt columns.
- Claim 3: RED stays executor-level (no session-layer retry state exists
  pre-GREEN); `retry_attempt`/`retry_next_attempt_at` are a projection over
  the durable event, not a counter table. Both supervisor-signed-off.
- The consolidated record lives beside the slice as
  `<slice-stem>.exit-record.json` — a `.json`, so outside the markdown docs
  cap. Criterion 8's gate derives its path from the active slice.

## Next

1. Criterion 8, red-then-green: extend `tests/contract/test_docs_discipline.py`
   to refuse a durability production slice (SLICE-012+) without a green,
   digest-bound record. Then close SLICE-011.
2. SLICE-012+ implement the five claims in the harness, one slice at a time,
   each gated by that record. Milestone #1 on `anthonykewl20/ranex-harness`
   (issues #1-#9) carries the plan.

## Known limits

- The prototype **diffs** are not preserved — only the records. Deleting the
  five worktrees loses the implementations; SLICE-012+ reimplements from the
  record. That is ADR-013's design; confirm before pruning.
- A kernel gate can check the record is present, well-formed, green and
  digest-bound. It can NEVER re-verify the bytes — another repo, disposable.
- Open before SLICE-012+: claims 2 and 3 have reviewer-hy3 only; claim 5's
  approvals predate its own fix; claim 4 lacks a positive control; claim 2's
  sweep is unwired; claim 5 has no owner-release path.
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
