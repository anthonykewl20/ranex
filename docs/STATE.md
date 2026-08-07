# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-07
**Active slice:** none — SLICE-012 closed; SLICE-013 not yet opened.

## Where we stopped

SLICE-012 closed: the provider watchdog is **in production** in the harness
(`fe7a8901de`). A stalled provider stream now reaches a terminal state on its
own; before, it hung forever and reported the session busy until someone
intervened. Idle 30s (inter-chunk silence only), absolute 1800s, both failing
as a typed non-retryable error. packages/core 1100 pass / 0 fail, tsgo 0.
Four of ADR-015's five claims remain unbuilt in production.

## Decisions

- **Full rebrand rename approved (2026-08-07), to run next.** `@opencode-ai/*`
  → `@ranex/*` across 12 packages and ~800 import sites; `packages/opencode/`
  and `.opencode/` renamed. Sequenced after SLICE-012 deliberately: it would
  have collided with every file the watchdog touched.
- Idle does not cover time-to-first-token; the first pull runs untimed. Inter-
  chunk gaps (~10-100ms) and TTFT (seconds to minutes) are different
  distributions and one number cannot serve both.
- Absolute stays 1800s, diverging from the 600s the latency research
  suggested: it is the loose whole-turn backstop, and tightening it would
  false-cut a long legitimate stream that idle correctly ignores.

## Next

1. The rebrand sweep, on its own branch, then docs and GitHub issues/
   milestones updated to match. Note `.opencode/` is the config directory the
   harness reads — renaming it is behavioural, not cosmetic, and needs a
   fallback or a migration note.
2. SLICE-013 — reconciler reorder, the second ADR-015 claim. Gated by the
   SLICE-011 prototype record, like every durability production slice.

## Known limits

- A provider that connects and never sends a first chunk is bounded only by
  the absolute budget — up to 30 minutes. Recorded in the closed slice; the
  proper fix is a third first-chunk budget, not a tuned number.
- Prototype code is preserved on five isolated `proto/s011-*` branches in
  `ranex-harness`, never merged. Reference only. Delete when done:
  `git push origin --delete proto/s011-{watchdog,reconciler,retry,blockers,fencing}`.
- The harness `bun.lock` is stale against `package.json` (bin name), so every
  `bun install` dirties it. The rebrand sweep should settle it.
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
