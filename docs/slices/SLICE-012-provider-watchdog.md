# SLICE-012 — provider watchdog: a stalled stream reaches a terminal state

**Status:** open
**Opened:** 2026-08-07
**ADR:** `docs/adr/ADR-015-durable-execution-watchdog-first.md` — accepted 2026-08-07.
**Gated by:** `docs/slices/done/SLICE-011-durable-execution-prototype.exit-record.json`,
claim 1. The compiled gate in `tests/contract/test_docs_discipline.py` refuses this
slice if that record stops being GREEN or digest-bound.
**Linked issue:** #2 "Provider watchdog: inactivity + absolute timeout on llm.stream"
on `anthonykewl20/ranex-harness`, milestone #1.

## The defect

A stalled provider socket hangs `Stream.runForEach` forever
(`packages/core/src/session/runner/llm.ts:232-275`). The coordinator Deferred
never settles, so `sessions.active()` reports busy until someone interrupts by
hand. No timeout of any kind exists in the harness today. This is the first of
ADR-015's five claims and the only one that needs no schema change.

SLICE-011 proved the fix works in a disposable prototype: RED hangs past budget,
GREEN reaches a terminal state in 437ms, the negative control still hangs, a
healthy slow stream is not cut, and idle and absolute timeouts fire
independently of one another. **That prototype ships nothing.** This slice
writes the production implementation, and the prototype is reference, not a
source of truth — `proto/s011-watchdog` (`79093b3064`) is disposable and nothing
keeps it correct as the harness moves.

## Design

Per ADR-015 and the claim-1 record. Two distinct timeouts around `llm.stream`:

- **Stream-idle** — a per-pull deadline that resets on every chunk, via
  `Stream.timeoutOrElse`. Fires when a provider goes quiet mid-stream.
- **Absolute** — a whole-turn budget raced against the consumer, via
  `Effect.raceFirst`, which interrupts the blocked consumer when the turn
  overruns regardless of chunk activity.

Both must fail as typed `LLMError` so existing failure handling maps them to a
terminal run state without introducing a new error channel. Validated against
installed `effect@4.0.0-beta.83`: `Stream.timeoutOrElse` is per-pull and
resetting; `raceFirst` interrupts the loser through `fiberInterruptAll`.

The prototype's configuration is **not** shippable and this slice must replace
it: `ProviderWatchdogConfig` was a mutable module singleton, adequate for a
scratch fixture and wrong for production.

## Done criteria

Each is met only when a test in the harness proves it, red-then-green, and the
gates below are green on disk — not in a session's summary.

1. **The unsafe baseline is reproduced before it is refused.** A fake provider
   that sends one SSE chunk then stalls hangs the run past budget with the
   watchdog disabled. Observed, not asserted.
2. **A stalled stream reaches a terminal state within budget**, with no manual
   interrupt, and `sessions.active()` no longer reports the session busy.
3. **Idle and absolute are distinct and independently demonstrated.** One test
   feeds deltas shorter than the idle threshold so only the absolute budget can
   fire; another disables idle entirely and proves absolute alone still cuts a
   stall. Neither may pass by accident of the other.
4. **A healthy slow stream is not falsely cut.** Provider latency below the idle
   threshold completes normally. The margin is stated, not implied.
5. **Configuration is real.** The timeouts are configurable and bounded through
   the harness's own configuration surface — not a mutable module singleton, not
   a hardcoded constant. Defaults are justified in the slice or the issue.
6. **The watchdog is correct with a tool call in flight.** The prototype used
   no-tool fixtures and explicitly did not cover this. A stall during a tool
   round-trip must reach the same terminal state without stranding the tool.
7. **The failure is legible.** A watchdog termination is distinguishable from a
   provider error in the session's own record — an operator can tell "the model
   went quiet" from "the model refused".
8. **No regression.** `packages/core` suite green, `tsgo --noEmit` exit 0, and
   the ranex contract suite still green (baseline 838 passed / 2 skipped).
9. **The docs stay aligned.** `specs/v2/session.md:153`'s deferral is rewritten
   to describe what now exists; `docs/STATE.md` and the MAP durability row move
   from "nothing built in production" to what is built.

## The controls most likely to become decoration

1. **First: a test that never stalls a real stream.** The baseline must hang a
   provider stream inside the runner. Asserting a timeout helper returns a value
   proves nothing about `llm.stream` — this was decoration warning 1 in
   SLICE-011 and it applies unchanged.
2. **Second: idle and absolute proven by the same fixture.** If every stall is
   silent, idle always fires first and absolute is never exercised. Two
   independent reviewers missed exactly this in the prototype, and it was only
   caught because the absolute branch had been source-verified and never run.
3. **Third: a slow-stream test with no margin.** "Not falsely cut" needs a
   stated headroom. The prototype's was 2.67× on a real clock; a test that
   passes at 1.05× is measuring the machine, not the watchdog.
4. **Fourth: a config test that asserts the default.** Configurability means a
   non-default value changes behaviour observably, not that a constant can be
   read back.
5. **Fifth: declaring stability from one run.** Claim 5 was reported stable,
   approved by two reviewers, and was flaky at ~12%. Any test touching timing
   here is run repeatedly, and the count is reported.

## What this slice does not close

- **The other four claims.** Reconciler reorder, durable retry, durable
  blockers and Session-ID fencing are SLICE-013+ and open one at a time.
- **Cross-model failover.** Deferred by ADR-015; a stalled provider is
  terminated here, not replaced.
- **Host-crash durability.** Process-crash only at `synchronous = NORMAL`.
- **Subagent recovery.** V2 has no `task` tool.
- **The permanent regression suite.** Harness issue #7's mid-stream-hang test
  becomes writable once this ships, but is not this slice.
