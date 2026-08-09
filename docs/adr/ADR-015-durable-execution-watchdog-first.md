# ADR-015 — durable execution, watchdog first: at-most-once recovery for the harness

**Status:** accepted
**Date:** 2026-08-06
**Decision-makers:** repo owner
**Slice:** `docs/slices/SLICE-011-durable-execution-prototype.md`

## Context and Problem Statement

The harness fork defers provider timeout and post-crash continuation recovery by design (`specs/v2/session.md:153,165`), yet several verified defects strand work without an owner. A stalled provider stream hangs `Stream.runForEach` forever (`packages/core/src/session/runner/llm.ts:232-275`), so the coordinator Deferred never settles and `sessions.active()` reports busy until manual interrupt. The reconciler returns on the eligible-input guard before reconciling interrupted tools (`runner/llm.ts:389` before `:390`), so a crash with an empty inbox leaves tools projected `running` forever. Retry is process-local recursive state (`packages/llm/src/route/executor.ts:345-364`) while the durable `session.next.retried` event already exists with its projector commented out (`packages/schema/src/session-event.ts:387`; `packages/core/src/session/projector.ts:394`). Permission and question waits are in-memory Deferred maps (`packages/core/src/permission.ts:103-118`, `packages/core/src/question.ts:65-80`). Execution ownership is an in-memory Map (`packages/core/src/session/run-coordinator.ts:24-35`) over a globally shared database (`packages/core/src/database/database.ts:53`), so two live processes can double-drain one Session. Upstream issue #36347 confirms the user-visible blocker loss.

## Decision Drivers

- A hung provider must reach a terminal state without manual interrupt.
- Crash recovery must never blind-replay tool side effects; spec:50 forbids it.
- The durability unit is one SQLite transaction; new machinery must not add steady-state writes to the single WAL writer lock.
- Ownership must prevent two live processes draining one Session, without slowing single-process crash recovery.
- Retry state must survive restart, or every restart defeats a rate limit.
- Durable blockers must survive restart, stay replyable once, and never re-run the tool that created them.
- The Session model has no durable drain identity; a fence is Session-ID scoped, not execution scoped (spec:165).
- Prototype every claim red-first before production (ADR-013).
- Durability claims are scoped to process crash unless the pragma changes.
- Subagent recovery waits until V2 ports the `task` tool.

## Prior art

- Searched: GitHub API `gh api -X GET search/repositories` for "durable execution lease heartbeat stalled job recovery" and "agent workflow checkpoint pending writes sqlite".
- Searched: `gh api -X GET search/repositories -f q='oh-my-openagent'` and fetched its `LICENSE.md` to confirm the SUL-1.0 restriction on commercial distribution.

- **BullMQ** (taskforcesh/bullmq), commit `46880af9629e9aee9abbc2782074a3e76d17b924`, `src/classes/lock-manager.ts` — the lease pattern this program weighed: periodic lock renewal, renewal-failure reporting, per-job and global cancellation, and stalled-job recovery by another worker:
  <https://github.com/taskforcesh/bullmq/blob/46880af9629e9aee9abbc2782074a3e76d17b924/src/classes/lock-manager.ts>
  License: MIT.
  Weakness: designed for Redis and many distributed workers; a heartbeat lease adds steady-state writes to one SQLite writer lock and gates crash recovery behind lease expiry, which is slower than the immediate reconciliation this codebase already performs.
  Vendored: docs/adr/prior-art/ADR-015/bullmq-lock-manager.ts blob:2c2e711a85a9961aa350c2734be3c33bce84ee96

- **LangGraphJS** (langchain-ai/langgraphjs), commit `f6a6d26b7e69003c4fa052f3cd3319f3e72f0f8f`, `libs/checkpoint-sqlite/src/index.ts` — the checkpoint/pending-write contract: WAL mode, separate `checkpoints` and `writes` tables, parent checkpoint references, composite primary keys, and pending writes reconstructed on load:
  <https://github.com/langchain-ai/langgraphjs/blob/f6a6d26b7e69003c4fa052f3cd3319f3e72f0f8f/libs/checkpoint-sqlite/src/index.ts>
  License: MIT.
  Weakness: the checkpoint is an opaque serialized blob, not a per-field audit record; pending writes are reconstructed in memory rather than transactionally fenced with the checkpoint.
  Vendored: docs/adr/prior-art/ADR-015/langgraph-checkpoint-sqlite.ts blob:b4610053fc33a6c47bfc007cf44f92e24adbbd42

- Rejected: https://github.com/temporalio/temporal A full Durable Workflow server with activities, signals, and heartbeats; running a server for a local-first single-owner SQLite product adds a deployment and a trust boundary while the semantics are expressible with the existing EventV2 owner claims and flock.
- Rejected: https://github.com/code-yeongyu/oh-my-openagent Its startup resume pass and explicit state transitions are the right shape, but its Sustainable Use License forbids commercial derivative distribution and its code never enters this tree, converted or not.
- Rejected: https://github.com/celery/celery Worker-local reserved/active state with no durable fencing; two resurrected workers both run the same task, which is the double-drain failure this program must refuse.

## Considered Options

1. Add a durable `session_execution` lease table with heartbeat and generation. Rejected: it invents a durable drain identity the Session model refuses (spec:165), writes into the single WAL lock, and gates recovery behind lease expiry.
2. Persist executor-level retry counters. Rejected: the wrong layer — `retryStatusFailures` only wraps the pre-stream phase (`executor.ts:353-364`).
3. Add a `tool_attempt` table with a `replayPolicy` column. Rejected: it enables silent replay of unsandboxed `bash`, against spec:50.
4. Reuse the existing `effect-flock` and EventV2 owner claims for Session-ID fencing. Chosen.
5. Publish the existing `session.next.retried` event and uncomment its projector. Chosen.
6. Persist pending permission/question requests as durable rows and rehydrate on restart. Chosen.
7. Provider watchdog (inactivity + absolute timeout) first, schema-free. Chosen.
8. Subagent completion recovery now. Rejected: V2 has no `task` tool yet (`packages/core/src/tool/builtins.ts:27`).

## Decision Outcome

In the context of a harness whose stalled streams hang forever and whose ownership, retry, and blockers die with the process, facing a spec that refuses a durable drain identity and forbids silent side-effect replay, we chose a provider watchdog plus reuse of the harness's existing flock and EventV2 owner claims, to reach a provable no-false-busy and no-blind-replay invariant without a new execution table, accepting that cross-model failover and subagent recovery stay deferred. Concretely: (1) inactivity and absolute timeout around `llm.stream`; (2) hoist interrupted-tool reconciliation above the eligible-input guard and add a startup sweep; (3) publish `session.next.retried` and uncomment its projector; (4) persist blockers as durable rows with one-reply semantics; (5) fence each Session with the existing flock plus `EventSequenceTable.owner_id`. All five are prototype-gated red-first per ADR-013 before any production slice.

### Consequences

- Good: every stalled run reaches a terminal state within budget without manual interrupt.
- Good: a crash with an empty inbox no longer strands `running` tools.
- Good: retry state survives restart; the durable event schema already exists.
- Good: blockers survive restart and remain replyable exactly once.
- Good: no new durable execution identity; spec:165 is honoured.
- Bad: the reconciler fix and watchdog are harness changes that must land and be tested in the fork.
- Bad: durability is claimed for process crash only at `synchronous = NORMAL` (`database.ts:28`).
- Bad: cross-model failover remains under-specified and stays deferred.
- Not closed: subagent completion recovery, V2 `task` tool, cluster fencing, host-crash durability.

### Confirmation

The compiled gate is an extension of `tests/contract/test_docs_discipline.py`: a durability production slice (SLICE-012+) is refused unless the ADR-015 prototype exit record — digest-bound, in the scratch worktree — is green for every claim it names. The prototype suite is the confirmation authority, not a summary. Harness-side claims are proven from `packages/core/test` and `packages/ranex/test` with bun; the ranex side runs the contract test. No production durability slice opens with a missing or merely described criterion.

## Improvements on the prior art

1. BullMQ's lease invariant — renewal failure and stalled recovery are detectible — is kept; its Redis heartbeat table is rejected for a single local SQLite owner.
2. LangGraph's checkpoint/writes split is kept as a mapping; its opaque blob is rejected in favour of the existing per-field session event log.
3. Ownership reuses the harness's own `effect-flock` and EventV2 `owner_id` instead of adding a third mechanism.
4. Durable retry publishes an event that already exists rather than adding a counter table.
5. The reconciler defect is a reorder, not a new subsystem.
6. The at-most-once contract replaces the at-least-once-plus-idempotency framing the proposal borrowed.
7. The watchdog is schema-free and lands first so every later failure test becomes writable.
8. Prototype-first (ADR-013) gates all five claims before production.

## Architecture surface

Harness only. Files: `packages/core/src/session/runner/llm.ts` (watchdog, reconciler order, startup sweep), `packages/schema/src/session-event.ts` (Retried publish), `packages/core/src/session/projector.ts` (uncomment), `packages/core/src/permission.ts` and `packages/core/src/question.ts` (durable blocker rows), `packages/core/src/database/schema.gen.ts` (new blocker tables, regenerated), and `packages/core/src/util/effect-flock.ts` (already exists, unchanged). No kernel, verdict, or `evaluate()` change.

## Scope and threat delta

Governs harness execution lifetime. STRIDE: Denial of service (a stalled or wrongly-busy run is a hang) and Integrity (ownership prevents double side effects). In scope: the five claims and their tests. Out of scope: cross-model failover, subagent/task recovery, cluster fencing, host-crash durability. Non-goal: a green prototype is not proof of production integration; durability is claimed for process crash only unless `synchronous` changes.

## Quality attributes

| characteristic | scenario | measure |
|---|---|---|
| Reliability | a provider stalls mid-stream | run reaches a terminal state within budget |
| Reliability | crash with an empty inbox | stranded running tools reconciled at startup |
| Recoverability | process dies during retry delay | `next_attempt_at` honoured; no early retry |
| Recoverability | permission/question pending | same blocker ID listed and replyable once |
| Integrity | two processes drain one Session | flock refuses the second |
| Performance | steady state | no heartbeat writes; p95 turn overhead < 5% |

## Reversibility

Door: two-way

The prototype is scratch and deleted at the decision point. Production changes are small and revert independently: the watchdog is a timeout wrapper, the reconciler is a reorder plus a sweep, retry reuses an existing event, blockers are durable rows with a drop migration, and fencing reuses the existing flock. No durable execution identity is introduced, so nothing needs format migration.

## Sad paths

Derived by state-transition analysis over the five claims and boundary-value analysis on the timeout and retry-delay arithmetic.

| # | Failure | Required behaviour |
|---|---|---|
| 1 | Provider stalls mid-stream | watchdog interrupts; terminal state within budget |
| 2 | Crash with an empty inbox | startup sweep reconciles stranded running tools |
| 3 | Crash during retry delay | persisted `next_attempt_at` holds; no early retry |
| 4 | Crash after a tool side effect | tool marked interrupted; never replayed |
| 5 | Permission pending across restart | same blocker ID listed; one reply accepted |
| 6 | Question pending across restart | same form ID listed; one answer accepted |
| 7 | Two processes drain one Session | flock refuses the second owner |
| 8 | Reconciler runs twice | no duplicate messages, attempts, or effects |
| 9 | SIGKILL at `synchronous = NORMAL` | recovery proven for process crash; host crash unclaimed |
| 10 | Retried projection double-fires | idempotent projection; no duplicate event |
| 11 | Watchdog fires on a healthy slow stream | idle threshold exceeds provider latency; no false cut |
| 12 | V2 `task` tool absent | subagent recovery stays deferred, not silently built |

## Test strategy

Levels: contract (ranex) and prototype (harness worktree). `tests/contract/test_docs_discipline.py` guards this ADR's structure, citations, licences, and digests, and is extended by SLICE-011 to refuse durability production slices without a green, digest-bound prototype record. `tests/security/test_refusal_coverage.py` keeps every refusal branch reachable once production slices land. `tests/contract/test_kernel_unchanged.py` pins the kernel unchanged. Harness-side claims are proven in the scratch worktree by the harness's own bun suite (`packages/core/test/session-runner.test.ts`, `packages/ranex/test/recovery/`), which this repository cannot resolve; the ranex gate is the digest-bound exit record, not the harness tests. Red-then-green per claim; no global coverage percentage.

## Code review checklist

- Does every prototype begin with an observed red unsafe control?
- Is the negative control independent of the implementation under test?
- Does the watchdog distinguish absolute timeout from stream-idle timeout?
- Is the reconciler reorder proven against an empty-inbox crash fixture?
- Does durable retry reuse the existing event and projector rather than a new table?
- Are blockers durable rows with one-reply semantics, not serialized Deferreds?
- Is ownership the existing flock plus `owner_id`, with no third mechanism?
- Does the prototype claim only process-crash durability at `synchronous = NORMAL`?

## More Information

Parent decisions: ADR-008 (the harness fork), ADR-013 (prototype gate), ADR-014 (per-member bridge). Upstream evidence: anomalyco/opencode issues #36347 (blocker persistence), #36349 (subagent completion), #36804 (parallel dispatch loss, V1-reported). Tracked in milestone #1 "Durable execution, failover, and recovery" on anthonykewl20/ranex-harness; SLICE-011 is the prototype slice. Open: whether #36804 reproduces in V2; the `synchronous = FULL` cost; cross-model failover design.

**Accepted 2026-08-07.** The Confirmation above is satisfied, not asserted: SLICE-011 closed with all nine criteria met (`e0b9886d9`), all five claims proven red-first with negative controls and two-reviewer consensus, and the compiled gate now refuses a durability production slice whose prototype record is missing, not GREEN, or not digest-bound. The record is `docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`.

Two clarifications the prototype earned, recorded here because a later reader will otherwise re-litigate them. First: "no `session_execution` lease table, no `tool_attempt` replay column" rules out a **parallel execution-state store**, not a materialised read model. Claim 3's `retry_attempt` and `retry_next_attempt_at` on `SessionTable`, written by a projector from the durable `session.next.retried` event, are a projection over an event that remains the source of truth — the same shape as every other projector in the fork. Reviewed independently and ruled sound. Second: the gate proves a record was recorded and bound, never that the runs happened or that the bytes came from where the record says; the digests point into disposable harness worktrees in another repository. That is the limit ADR-003 already accepts for vendored prior art, and it is written into the gate's own failure message.

What the prototype does **not** license is production confidence. Nothing durable is built. The record's `open_before_slice_012` list names seven items a production slice may not skip — including that ownership fencing has no owner-release path, so a drained session stays fenced against every later owner.