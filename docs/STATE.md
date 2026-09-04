# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (SLICE-084 closed, pushed; the loop is complete)
**Active slice:** none

## Where we stopped

The GitHub acceptance loop is complete, three slices in three days of
commits: bind (SLICE-082 — a PR head SHA derives the verdict subject
through the local object store), publish (SLICE-083 — the
`ranex/acceptance` check from the Ranex GitHub App, fail-closed
conclusion mapping), receive (SLICE-084 — `ranex github listen`, the
bounded localhost listener with HMAC-proven deliveries). The kernel
never moved; no signed surface changed; no dependency was added.

What an operator can do now: run the receiver beside a clone, let a
`gate evaluate` run produce signed verdicts, and require the
`ranex/acceptance` check from the Ranex App in a repository ruleset
(the recipe, including `integration_id` pinning, is in README).

## Next

Deferred by owner decision, in order: anti-replay (nonce, journal head
anchor, F-005 item 1 — a straight replay under unchanged rules is still
undetected, and webhook anti-replay beyond delivery-ID dedupe belongs
there), then the approver signature SLICE-080 made possible (key
material the owner generates; none is committed).

Still open: F-004; interval-honest wording; nightly divergence with an
absolute `--out`; more permissive external repos.

## Governance

ADR-047/048/049/050/051 accepted. Manifest re-frozen at 1795 IDs,
`expected_skips` byte-identical at 166 (the receiver arms skip
nothing). UNVERIFIED: the live journey — App creation, installation, a
real PR receiving its check — needs GitHub-side credentials that do not
exist yet; the arms cover the full pipeline against the fake.

## Known limits

The catalog binds keys to principals, never principals to humans. No
replay detection yet. Trainer labels host-relative, no journal head
anchor, mutmut UNVERIFIED.
