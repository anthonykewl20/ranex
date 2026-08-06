# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-06
**Active slice:** docs/slices/SLICE-011-durable-execution-prototype.md

## Where we stopped

ADR-015 (durable execution, watchdog first) records the validated verdict
from a full harness audit: the diagnosis was mostly right, its fix misaimed.
Verified on code: a stalled provider stream hangs forever
(`runner/llm.ts:232-275`); the reconciler returns before reconciling broken
tools (`runner/llm.ts:389` before `:390`); retry is process-local even
though the durable `session.next.retried` event exists with its projector
commented out (`session-event.ts:387`, `projector.ts:394`); permission and
question waits are in-memory Deferreds; ownership is an in-memory Map over
the shared `~/.local/share/.../opencode.db`. reviewer-hy3 debate plus disk
verification on every load-bearing claim; GitHub-validated issues #36347,
#36349 (real, V2) and #36804 (V1-reported); prior-art licenses pinned.

## Decisions

- **At-most-once + explicit interruption**, not at-least-once/idempotent:
  unsandboxed `bash` cannot be idempotent; spec:50 forbids silent replay.
- **Watchdog first**, then reconciler reorder, then durable retry, then
  durable blockers, then Session-ID fencing via `effect-flock` + EventV2
  `owner_id`. **No lease/heartbeat/`session_execution`/`tool_attempt` cols.**
- Subagent recovery deferred until V2 ports `task`; cross-model failover
  deferred; durability claims are process-crash only at `synchronous = NORMAL`.
- SLICE-010 parked (archived in `done/`); its uncommitted WIP is undisturbed.

## Next

1. SLICE-011 prototype in a scratch harness worktree (ADR-013 style): five
   claims red-to-green with negative controls, digest-bound EXIT_RECORD,
   reviewed by reviewer-hy3 and reviewer-deepseek.
2. Extend `tests/contract/test_docs_discipline.py`: the compiled gate refuses
   a durability production slice without a green, digest-bound record.
3. Milestone #1 on `anthonykewl20/ranex-harness` (issues #1-#9) carries the
   production plan; production slices SLICE-012+ open one at a time.

## Known limits

- Harness repo has uncommitted WIP (`lildax.cjs`, `trigger.test.ts`) and ranex
  has uncommitted SLICE-010 WIP; neither was disturbed.
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
- Retry constants are 500ms base / 10s cap / 2 retries (`executor.ts:36-38`).
- Prototype is scratch under the harness worktree; ephemeral, ships nothing.
- Full ranex suite ~6 min; this session ran the docs-discipline contract only.