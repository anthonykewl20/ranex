# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-06
**Active slice:** docs/slices/SLICE-011-durable-execution-prototype.md

## Where we stopped

SLICE-010 (the kernel merges, ADR-012) is closed. `ranex task merge`
publishes a judged candidate only through ordered journalled checks
(policy/approval, ancestry, merge-range, digest/evidence, expected-old CAS);
all fourteen done criteria are proven by tests, the full suite is green
(827 passed / 2 skipped), diff-cover is 100% on the change, and the mutmut
kernel-scope run completed (survivors are review input). The closed approval
envelope binds C, D, R, T, the catalog digest, and the CANDIDATE row hash.

## Decisions

- The SLICE-010 close is complete but UNCOMMITTED in the working tree
  (implementation, tests, manifest entry, slice header); commit is pending
  the owner's word.
- The harness-side suite blocker (trigger.test.ts typecheck) was fixed in
  the sibling ranex-harness repo and committed there as f7f822ff5e.
- ADR-015 decisions stand: at-most-once + explicit interruption; watchdog
  first; no lease/heartbeat/session_execution/tool_attempt columns.

## Next

1. Commit the SLICE-010 close when the owner confirms.
2. SLICE-011 prototype in a scratch harness worktree (ADR-013 style): five
   claims red-to-green with negative controls, digest-bound EXIT_RECORD,
   reviewed by reviewer-hy3 and reviewer-deepseek.
3. Extend `tests/contract/test_docs_discipline.py`: the compiled gate refuses
   a durability production slice without a green, digest-bound record.
4. Milestone #1 on `anthonykewl20/ranex-harness` (issues #1-#9) carries the
   production plan; production slices SLICE-012+ open one at a time.

## Known limits

- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
- Retry constants are 500ms base / 10s cap / 2 retries (`executor.ts:36-38`).
- SLICE-011 prototype is scratch under the harness worktree; ephemeral.
- Concurrent crash-recovery can double-append INFERRED outcomes for one
  orphaned intent; the chain stays verifiable (review note, not a blocker).
- approval.py mutmut survivors are error-text and redundant-length mutants.
