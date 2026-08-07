# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-07
**Active slice:** docs/slices/SLICE-013-reconciler-reorder.md

## Where we stopped

SLICE-012 closed: the provider watchdog is **in production** (`fe7a8901de`) —
idle 30s, absolute 1800s, typed non-retryable. The rebrand is finished
(`a4da8a8d28`..`3dfe9ee562`). Four of ADR-015's five claims remain unbuilt.

SLICE-013 has hoisted reconciliation above the eligible-input guard in
`runner/llm.ts:459` — `failInterruptedTools` now runs before the guard returns,
so an empty-inbox `run()` still reconciles. The startup sweep and per-session
serialization are not yet wired.

## Decisions

- `.opencode` stays a discovered *legacy* config directory; `.ranex` wins
  where both exist. Silently ignoring a working config is the worse failure.
- Gateway attribution headers now say `ranex`. They are OpenRouter app
  attribution ("used to track API usage per application"), not an interop
  contract — keeping `opencode` attributed our traffic to the upstream fork.
- Idle does not cover time-to-first-token; the first pull runs untimed.
  Inter-chunk gaps and TTFT are different distributions.

## Next

1. SLICE-013 is open: **wire** a startup sweep — the prototype left it a capability
   nobody called, which is the half that actually recovers the headline case.
   Serialize per-session reconcile first.
2. Decide which upstream CI workflows this fork keeps (see Known limits).
3. Resolve whether `.opencode-version` and the `opencode` store file get a
   real migration. One reviewer called keeping them lazy; unresolved.

## Known limits

- **This fork's CI is broken independent of the rebrand.** Four live jobs set
  working directories that do not exist: `packages/app`, `packages/client`,
  `./github`, `./sdks/vscode`. Only three workflows are gated on the upstream
  repo; twenty-two run here.
- A provider that connects and never sends a first chunk is bounded only by
  the absolute budget — up to 30 minutes. The fix is a third first-chunk
  budget, not a tuned number.
- Prototype code is preserved on five isolated `proto/s011-*` branches in
  `ranex-harness`, never merged. Reference only. Delete when done:
  `git push origin --delete proto/s011-{watchdog,reconciler,retry,blockers,fencing}`.
- Whether #36804 (parallel dispatch loss) reproduces in V2 is unverified.
