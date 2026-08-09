# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-09
**Active slice:** `docs/slices/SLICE-017-confinement-of-the-bound-command.md` — qualify strict-local host/build/launcher; single open slice.

## Where we stopped

Two of ADR-015's five durability claims are in production (harness default
branch tip `9eeda0bf5d21...`): the provider watchdog and the reconciler hoist
with its startup sweep. Durable retry, durable blockers, and Session-ID fencing
remain. The rebrand is finished; CI now keeps only the two workflows this fork
has a subject for. That durability sequence is parked/subordinate to P0. ADR-006
confinement is active first: SLICE-017 qualifies host/launcher, then planned
SLICE-018 owns lifecycle and SLICE-019 alone wires `cmd_run`.

## Decisions

- The reconcile sweep ships DB-global and is **unsafe under concurrent
  processes** — a second process marks a first's running tools interrupted.
  Accepted because the harness runs one daemon (ADR-014); the fencing slice
  must gate it on a durable owner claim first. Recorded in `reconcile.ts`.
- Fall back for human-authored/identity state, not rebuildable cache:
  `.opencode` config and `.git/opencode` qualify; skill-cache does not.
- `.git/ranex` reads old then writes new because the tool rename never moved it.
- Bounded read-only research/review fanout is allowed now. Current `task fanout`
  is prototype-only; SLICE-036 qualifies disposable mutation with publication
  blocked and SLICE-044 alone authorizes production. Until then, one writer.

## Next

1. Close SLICE-017 / issue #10; it qualifies only and cannot accept ADR-006.
2. Open issue #21 / SLICE-018, then issue #22 / SLICE-019; only 019 binds
   `cmd_run`, accepts ADR-006 and closes RISK-06.
3. Then open SLICE-029; later P0 slices open one at a time through SLICE-044.
4. Resume parked durability only after P0 unless its exit needs a dependency;
   fencing must still close the multi-process sweep hazard.
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
