# SLICE-011 — durable execution prototype: watchdog-first, red-to-green

**Status:** open
**Opened:** 2026-08-06
**ADR:** `docs/adr/ADR-015-durable-execution-watchdog-first.md` — proposed 2026-08-06.
**Linked milestone:** #1 "Durable execution, failover, and recovery" on
`anthonykewl20/ranex-harness`; issues #1-#9 carry the production plan.
**Closes:** ADR-015's Confirmation — the compiled gate that refuses a durability
production slice without a green, digest-bound prototype record.

## The defect

The harness fork (specs/v2/session.md:153,165) defers provider timeout and
post-crash continuation recovery. Five claims are unproven and two are known
broken: a stalled provider stream hangs `Stream.runForEach` forever
(`packages/core/src/session/runner/llm.ts:232-275`); the reconciler returns on
the eligible-input guard before reconciling interrupted tools
(`runner/llm.ts:389` before `:390`), stranding `running` tools after a crash
with an empty inbox; retry is process-local though the durable
`session.next.retried` event exists with its projector commented out
(`packages/schema/src/session-event.ts:387`; `projector.ts:394`); permission
and question waits are in-memory Deferred maps (`permission.ts:103-118`,
`question.ts:65-80`); ownership is an in-memory Map (`run-coordinator.ts:24-35`)
over a globally shared database (`database.ts:53`). A proposal was reviewed
against these findings; ADR-015 records the validated verdict and the
at-most-once contract.

## Design

Per `docs/adr/ADR-015-durable-execution-watchdog-first.md`. This slice is the
disposable prototype only — it ships nothing. It runs in a scratch harness
worktree (per ADR-013) and validates five claims red-first, each with a
negative control, against the real harness code:

1. **Watchdog.** Inactivity and absolute timeout around `llm.stream`; a stalled
   provider reaches a terminal state within budget without manual interrupt.
2. **Reconciler reorder.** Hoist interrupted-tool reconciliation above the
   eligible-input guard (`runner/llm.ts:389`) and add a startup sweep; a crash
   with an empty inbox reconciles stranded running tools.
3. **Durable retry.** Publish `session.next.retried` and uncomment its
   projector; attempt state survives a restart during the retry delay.
4. **Durable blockers.** Persist pending permission/question requests as
   durable rows; the same blocker ID stays listed and replyable exactly once
   across graph teardown, without re-running the creating tool.
5. **Session-ID fencing.** Two processes draining one Session are refused by
   the existing `effect-flock` and `EventSequenceTable.owner_id`; first prove
   the double-drain is real, then prove the fence.

The harness tool surface is unchanged: no `session_execution` table, no
`tool_attempt` replay column, no heartbeat, no subagent work (V2 has no `task`
tool yet — `tool/builtins.ts:27`).

## Done criteria

Each criterion is met only when the prototype's scratch suite proves it, and
the exit record is digest-bound.

1. **The unsafe baselines are measured before they are refused.** Each of the
   five claims starts red against the current harness behavior: a stalled
   stream hangs; an empty-inbox crash strands a running tool; a restart resets
   the retry counter; a blocker disappears on graph teardown; a second process
   double-drains. Each red is observed, not asserted.
2. **Watchdog claim is green.** A fake provider that sends one SSE chunk then
   stalls causes the run to reach a terminal state within the configured
   budget. The negative control (no watchdog) still hangs. Absolute timeout and
   stream-idle timeout are distinct; a healthy slow stream is not falsely cut.
3. **Reconciler claim is green.** A crash (graph teardown) with an empty inbox
   leaves a tool projected `running` today; the reordered reconciler plus
   startup sweep marks it interrupted. Running reconciliation twice produces no
   second message, attempt, or effect (ADR-015 s.p. 2, 8).
4. **Durable retry claim is green.** A provider returns 503; retry is scheduled;
   the graph is torn down during the delay; a fresh graph continues from the
   persisted attempt count and `next_attempt_at` rather than resetting (ADR-015
   s.p. 3, 10).
5. **Durable blocker claim is green.** A permission or question wait survives
   graph teardown; the same blocker ID is listed and accepts exactly one reply;
   the creating tool's pre-permission work is not re-run (ADR-015 s.p. 5, 6).
   Permission rejection and question cancellation are covered.
6. **Ownership claim is green.** After the double-drain baseline is reproduced,
   the existing flock plus `EventSequenceTable.owner_id` refuses the second
   owner. The negative control (no fence) double-drains. No session remains
   busy with no valid owner (ADR-015 s.p. 7).
7. **The exit record is green and digest-bound.** `EXIT_RECORD.json` in the
   scratch worktree enumerates each claim, command, fixture, observed refusal,
   artifact digest, and reviewer decision. reviewer-hy3 and reviewer-deepseek
   both approve it.
8. **The compiled gate exists.** `tests/contract/test_docs_discipline.py` is
   extended to refuse a durability production slice (SLICE-012+) whose ADR-015
   exit criteria lack a green, digest-bound record. The extension is
   red-then-green itself.
9. **The docs stay aligned.** `docs/STATE.md` records the expiry decision, and
   the harness `specs/v2/session.md` follow-ups reference the accepted contract.

## The controls most likely to become decoration

1. **First: a "watchdog" test that never makes the stream stall.** The red
   baseline must actually hang a provider stream inside the runner, not stub
   around it. A test that asserts a timeout helper's return value proves nothing
   about `llm.stream`.
2. **Second: a reconciler test that never crashes with an empty inbox.** The
   stranding bug is specifically the empty-inbox path (`runner/llm.ts:389`).
   A reconciliation test that runs with a pending steer will pass even with the
   bug present.
3. **Third: a retry test that re-admits instead of resuming.** The point is the
   persisted attempt counter and `next_attempt_at`; a test that lets the new
   process start a fresh drain proves nothing about the delay being honoured.
4. **Fourth: a blocker test that serializes the Deferred.** The failure mode is
   a process-local continuation. Persisting the request payload and replaying
   it into a fresh Deferred is decoration unless the same blocker ID accepts
   exactly one reply after teardown.
5. **Fifth: an ownership test that never reproduces the double-drain.** The
   flock is only justified if the concurrent-drain baseline is proven first.
   Testing the fence without the baseline is testing a hypothesis nobody
   demonstrated.

## What this slice does not close

- **Production durability.** This slice ships nothing; SLICE-012+ implement
  the five claims in the harness, each gated by the digest-bound record.
- **Cross-model failover.** ADR-015 defers it; the safe-boundary design is a
  separate decision.
- **Subagent completion recovery.** V2 has no `task` tool; deferred (ADR-015
  s.p. 12).
- **Host-crash durability.** Claims are process-crash only at
  `synchronous = NORMAL` (ADR-015 s.p. 9).
- **The `synchronous = FULL` cost.** Not measured; the pragma is unchanged.
- **Issue #36804 in V2.** Whether the parallel-dispatch loss reproduces under
  the V2 runner is unverified; the prototype may add a provider-level fixture
  only as a bonus, never as a gate.