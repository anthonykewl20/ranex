# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-08
**Active slice:** none — SLICE-013 closed; SLICE-014 not yet opened.

## Where we stopped

Three of ADR-015's five durability claims are in production (harness
`9eeda0bf5d`): the provider watchdog, the reconciler hoist, and a startup sweep
wired into the application graph. Durable blockers and Session-ID fencing
remain. The rebrand is finished; CI now keeps only the two workflows this fork
has a subject for.

## Decisions

- The reconcile sweep ships DB-global and is **unsafe under concurrent
  processes** — a second process marks a first's running tools interrupted.
  Accepted because the harness runs one daemon (ADR-014); the fencing slice
  must gate it on a durable owner claim first. Recorded in `reconcile.ts`.
- Fall back for state a human authored or that carries identity, never for
  cache the tool can rebuild. The `.opencode` config dir and the
  `.git/opencode` project store qualify; the skill-cache marker does not.
- `.git/ranex` replaces `.git/opencode` with a read-old-write-new migration:
  it lives in the user's repo, so no tool rename ever moved it.

## Next

1. SLICE-014 — durable retry, the third ADR-015 claim. Gated by the SLICE-011
   prototype record, like every durability production slice.
2. Then blockers, then fencing — and fencing **must** close the sweep hazard
   above before the harness is ever run as more than one process.

## Known limits

- A provider that connects and never sends a first chunk is bounded only by
  the absolute budget — up to 30 minutes. The fix is a third first-chunk
  budget, not a tuned number.
- CI keeps only `test.yml` and `typecheck.yml`; 24 workflows were deleted as
  having no subject in the fork's keep-set. `ranex-trim` has no branch
  protection, so none was a required check.
- `turbo.json` had scoped its test task to the pre-rebrand package name, so CI
  ran 1100 tests and silently skipped 2942. Fixed — check task scoping after
  any package rename.
- Prototype code is preserved on five `proto/s011-*` branches, never merged.
  `git push origin --delete proto/s011-{watchdog,reconciler,retry,blockers,fencing}`
