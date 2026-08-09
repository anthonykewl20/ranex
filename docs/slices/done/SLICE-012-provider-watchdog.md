# SLICE-012 — provider watchdog: a stalled stream reaches a terminal state

**Status:** done
**Closed:** 2026-08-07 — all nine criteria met; landed in ranex-harness 23d6a5b4ee. (corrected: the previously cited `fe7a8901de` is a docs commit, not the feat landing.)
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
   watchdog disabled. Asserted negatively — *the run does not reach a terminal
   state within budget B* — not merely printed. A criterion with no assertion is
   not a gate.
2. **A stalled stream reaches a terminal state within budget**, with no manual
   interrupt, and `sessions.active()` no longer reports the session busy.
   **The timeout must be non-retryable, and a test must prove it is not
   retried.** `LLMError.retryable` delegates to `reason.retryable`
   (`packages/llm/src/schema/errors.ts:181`), and the reasons disagree:
   `ProviderInternalReason` is `true` (`:117`), `TransportReason` is `false`
   (`:129`). An implementer who picks a retryable reason gets a watchdog that
   fires, is retried, restarts the same stall, and hangs anyway — while every
   other criterion here still passes. The prototype avoided this by accident,
   not by decision.
3. **Idle and absolute are distinct and independently demonstrated.** One test
   feeds deltas shorter than the idle threshold so only the absolute budget can
   fire; another disables idle entirely and proves absolute alone still cuts a
   stall. Neither may pass by accident of the other.
4. **A healthy slow stream is not falsely cut — by either timeout.** Provider
   latency below the idle threshold completes normally, *and* a healthy long
   turn completes within the absolute budget. Guarding only idle leaves the
   absolute budget free to cut legitimate work. The margin is stated, not
   implied, and the defaults are justified against a real latency distribution —
   including time-to-first-token on a reasoning model, which a 400ms idle
   default would cut on every call.
5. **Configuration is real, and proven by behaviour.** The timeouts are
   configurable and bounded through the harness's own configuration surface —
   not a mutable module singleton, not a hardcoded constant. A **non-default
   value must observably change when the watchdog fires**; reading a constant
   back proves nothing. An out-of-bounds value is refused at load, not at use.
6. **The watchdog is correct with a tool call in flight.** The prototype used
   no-tool fixtures and explicitly did not cover this. Tools dispatch as fibers
   during stream consumption (`runner/llm.ts:271`), and the cleanup at `:295`
   fires only on `Cause.hasInterrupts` — a watchdog `Stream.fail(LLMError)` is an
   error, not an interrupt, so dispatched tool fibers are **not** cleared and
   `:296` then awaits them. The observable is therefore specific: the tool fiber
   terminates and the tool is recorded interrupted, rather than "the tool is not
   stranded" as a feeling.
7. **The failure is legible, by reason and not by message text.**
   `LLMError.reason` is a tagged union (`errors.ts:160-177`), so this needs no
   schema change. Both watchdog timeouts carry `TransportReason` — the honest
   non-retryable transport reason, consistent with criterion 2 — and separate on
   the pre-existing structured `kind` field: `watchdog-idle` and
   `watchdog-absolute`. Watchdog versus provider refusal separates on
   `reason._tag`. The prototype used one reason for both and separated them by
   prose, which an operator cannot switch on.

   **Amended 2026-08-07 — the original wording contradicted itself.** It demanded
   the distinction be structural *in the session's own record* while also
   forbidding a schema change, and those cannot both hold: the persisted
   `Assistant.error` is an `UnknownError` with no field for `reason._tag` or
   `kind`, so all three cases project to `{ type: "unknown", message }` and
   differ only by string. What is actually required, and what is met: the
   **live** failure is structurally switchable by `_tag`, `kind` and
   `retryable`; the **durable** transcript carries `reason.message` verbatim,
   proven by exact equality and proven to survive a full projection replay.
   Persisting structured error reasons is a change to every error type in the
   session schema, not a watchdog concern — it is out of scope here and named in
   "What this slice does not close". Do not over-read the guarantee.
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
   approved by two reviewers, and was flaky at ~12%. Any test touching timing is
   run repeatedly and the count reported — but repetition treats the symptom.
   **Drive time with `TestClock`, which the fork already provides**
   (`packages/core/test/lib/effect.ts` builds `testEnv` with `TestClock.layer()`,
   and the SLICE-011 retry prototype drove its 499ms/500ms assertions through
   `TestClock.adjust` deterministically). The watchdog prototype used a wall
   clock and inherited the flake risk for no reason. Wall-clock timing is
   permitted only where the thing under test is genuinely real-time, and then
   the headroom is stated.

## Amendments — 2026-08-07, from the pre-implementation review

Two independent reviewers read this slice before any code existed, and their
findings were checked against the harness on disk rather than accepted. Six
amendments landed above: the non-retryable requirement in criterion 2, absolute
false-cut coverage and default justification in 4, behavioural proof in 5, the
tool-fiber observable in 6, reason-level legibility in 7, a negative assertion
in 1, and `TestClock` in control 5.

Two reviewer claims were **rejected** after checking the code, and are recorded
so they are not raised again. `uninterruptibleMask` does not swallow the escape
hatch: `restore` is applied to the provider stream (`runner/llm.ts:279`), so
user interrupts propagate during streaming; the mask covers only post-stream
settlement, deliberately. And a provider stall during a tool round-trip is
*inside* the watched stream, not outside it — the tool-in-flight risk is the
uncleared fiber set at `:295`, not an unguarded region.

The retryability hole is the one worth remembering: every criterion in this
slice could have passed while the watchdog fired, was retried, restarted the
same stall, and hung anyway.

## What this slice does not close

- **The other four claims.** Reconciler reorder, durable retry, durable
  blockers and Session-ID fencing are SLICE-013+ and open one at a time.
- **Cross-model failover.** Deferred by ADR-015; a stalled provider is
  terminated here, not replaced.
- **Host-crash durability.** Process-crash only at `synchronous = NORMAL`.
- **Subagent recovery.** V2 has no `task` tool.
- **Structured error reasons in the durable transcript.** The persisted
  `Assistant.error` is an `UnknownError` carrying a message and no reason
  structure, so post-restart automation cannot switch on watchdog-vs-refusal
  the way live code can. Fixing that widens the session schema for every
  error type, not just this one, and is a separate decision (criterion 7).
- **A bounded time-to-first-token.** Idle deliberately does not cover the first
  chunk (see criterion 4), so a provider that accepts the connection and then
  never sends anything is bounded only by the absolute budget — up to 30
  minutes at the default. That is a real limitation, not a tuned value:
  absolute is the loose whole-turn backstop, and tightening it would false-cut
  a legitimately long streaming turn that idle correctly ignores. One knob
  cannot serve both distributions, which is the same argument that split idle
  from TTFT in the first place. The proper fix is a third first-chunk budget;
  it is out of scope here and named so the 1800s default is not mistaken for
  a researched number.
- **The permanent regression suite.** Harness issue #7's mid-stream-hang test
  becomes writable once this ships, but is not this slice.
