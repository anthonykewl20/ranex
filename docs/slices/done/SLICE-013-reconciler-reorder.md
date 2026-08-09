# SLICE-013 — reconciler reorder: a crash with an empty inbox stops stranding tools

**Status:** done
**Closed:** 2026-08-08 — all seven criteria met; landed in ranex-harness a8bc7bdf35. (corrected: the previously cited `9eeda0bf5d` is an unrelated merge commit, not the feat landing.)
**Opened:** 2026-08-07
**ADR:** `docs/adr/ADR-015-durable-execution-watchdog-first.md` — accepted 2026-08-07.
**Gated by:** `docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`,
claim 2. The compiled gate in `tests/contract/test_docs_discipline.py` refuses this
slice if that record stops being GREEN or digest-bound.
**Linked issue:** #3 "Reconciler reorder: hoist failInterruptedTools above the
eligible-input guard + startup sweep" on `anthonykewl20/ranex-harness`, milestone #1.

## The defect

As found at the start of this slice: `packages/core/src/session/runner/llm.ts:459`
returned on the eligible-input guard — `if (!input.force && !hasSteer && !hasQueue)
return` — and `failInterruptedTools` sat at `:460`, after it. A crash with an
**empty inbox** therefore left tools projected `running` forever: nothing
reconciled them, because the guard returned first.

No `reconcile` capability existed on `SessionRunner`; the prototype's was scratch
and was never shipped.

*This section describes the defect the slice was opened against and is not
rewritten as work lands — the done criteria below carry progress. A defect
statement edited into the past tense destroys the record of why the slice exists.*

SLICE-011 claim 2 proved the fix: RED reproduces `Expected: "error" / Received:
"running"`, the hoist closes it, and reconciling twice produces exactly one
`Tool.Failed`. Two reviewers approved it. **That prototype ships nothing** —
`proto/s011-reconciler` (`0350a25422`) is disposable reference, and nothing keeps
it correct as the harness moves.

## Design

Per ADR-015 and the claim-2 record.

- **Hoist.** `failInterruptedTools` runs before the guard returns, so an
  empty-inbox `run()` still reconciles. It only touches projected *tool* context,
  never `SessionInput`, so `hasSteer`/`hasQueue` and their steer-priority
  short-circuit are unchanged.
- **Startup sweep.** A `reconcile` capability on `SessionRunner` that reconciles
  without scheduling a provider turn, **wired at process start over all
  sessions**. The prototype left this as a capability nobody called; that is the
  half that actually recovers the headline case.
- **Serialization.** Per-session reconcile must be serialized before the sweep is
  wired — see criterion 5.

## Done criteria

Each is met only when a test in the harness proves it, red-then-green, and the
gates below are green on disk — not in a session's summary.

1. **The unsafe baseline is reproduced before it is refused.** A crash (graph
   teardown) with an empty inbox leaves a tool projected `running`. Asserted
   negatively — *the tool is still `running` after `run({force:false})`* — not
   merely printed. The fixture must assert the inbox is empty for **both** steer
   and queue first; a pending steer masks the bug entirely.
2. **The hoist is green.** The same crash now marks the tool interrupted, and the
   eligible-input short-circuit behaves identically for every other input state.
3. **The startup sweep is wired, not merely available.** Process start reconciles
   stranded tools across **all** sessions with no `run()` call and no provider
   turn scheduled. A test must cover the case the prototype could not: crash with
   an empty inbox, nobody calls `run()`, recovery happens anyway.
4. **Idempotency.** Running reconciliation twice produces no second message, no
   second attempt, and no second effect — exactly one durable `Tool.Failed`, and
   the projected end state unchanged.
5. **Concurrent reconcile is serialized.** The deferred TOCTOU from claim 2
   becomes reachable the moment the sweep exists: `reconcile()` and `run()` can
   both read a tool as `running` and both publish. Two independent reviewers
   agreed `run()`-vs-`run()` is impossible by construction — the
   `SessionRunCoordinator` same-session join contract prevents it — so
   `reconcile()`-vs-`run()` is the **only** reachable surface, and it must be
   closed by a per-session mutex or `BEGIN IMMEDIATE`, with a test that
   reproduces the race before the fix.
6. **No regression.** `packages/core` and `packages/ranex` suites green, `tsgo
   --noEmit` exit 0, and the **kernel** contract suite green (838 passed /
   2 skipped). The kernel runs cross-repo tests against this fork's structure;
   harness-green is not green.
7. **The docs stay aligned.** `specs/v2/session.md:165`'s deferral is rewritten to
   describe what now exists; `docs/STATE.md` and the MAP durability row move.

## Where it stands — closed 2026-08-08

| # | Criterion | Standing |
|---|---|---|
| 1 | Unsafe baseline reproduced | met — `Expected: "error" / Received: "running"`, inbox asserted empty for both steer and queue |
| 2 | Hoist green | met — empty-inbox `run()` reconciles with `streamCallCount === 0` |
| 3 | Sweep **wired**, not merely available | met — `SessionReconcile.sweepNode` in the application graph; recovery with nobody calling `run()` |
| 4 | Idempotency | met — 1 durable `Tool.Failed` row, still 1 after a second reconcile plus a `run()` |
| 5 | Concurrent reconcile serialized | met — race reproduced first (`Expected: 1 / Received: 2`), closed by a per-session semaphore |
| 6 | No regression | met — core 1112/0, ranex 2944/0, tsgo 0, kernel 838 passed / 2 skipped |
| 7 | Docs aligned | met — `specs/v2/session.md`, and this repository |

The race test is only a test because `Effect.all` defaults to sequential in this
Effect beta (`concurrency ?? 1`). Without an explicit `concurrency: 2` it would
have passed against the unfixed code — decoration control 4, caught in flight.

## The hazard this slice introduced, accepted knowingly

The sweep is DB-global over a process-wide shared database, so a second process
booting marks tools a first live process is actively running as interrupted.
SLICE-011 claim 5 reproduced that two-process case before refusing it, so the
precondition is demonstrated rather than assumed. A reviewer raised it as a
blocker; it is accepted as scope because the harness runs one daemon in normal
operation (ADR-014) and closing it properly requires the durable owner claim the
fencing slice owns. **The fencing slice must gate this sweep on ownership before
the harness is run as more than one process against one database.** Recorded in
`session/reconcile.ts` and `specs/v2/session.md`, not only here.

## The controls most likely to become decoration

1. **First: a crash test with something in the inbox.** The stranding bug is
   specifically the empty-inbox path. A reconciliation test that runs with a
   pending steer passes even with the bug fully present — this was decoration
   warning 2 in SLICE-011 and it is unchanged.
2. **Second: a sweep that is only a capability.** Criterion 3 is about *wiring*.
   A `reconcile` function nobody calls at boot satisfies the prototype and leaves
   the production defect exactly where it was.
3. **Third: an idempotency test that counts projections, not events.** The
   projector re-checks the same guard, so projected state is idempotent even
   under a duplicate event. Counting the durable `Tool.Failed` rows is what
   catches a double publish; counting tool status does not.
4. **Fourth: proving serialization with a sequential test.** Criterion 5 needs a
   genuine concurrent reproduction. A test that awaits one call before starting
   the next demonstrates nothing about a race.
5. **Fifth: wall-clock timing.** Drive time with `TestClock`
   (`packages/core/test/lib/effect.ts` provides it). SLICE-011's claim 5 was
   reported stable, approved by two reviewers, and was flaky at ~12%.

## What this slice does not close

- **The remaining three claims.** Durable retry, durable blockers and Session-ID
  fencing are SLICE-014+ and open one at a time.
- **Host-crash durability.** Process-crash only at `synchronous = NORMAL`.
- **Cross-model failover** and **subagent recovery.** Deferred by ADR-015.
- **The permanent regression suite.** Harness issue #7's empty-inbox test becomes
  writable once this ships, but is not this slice.
