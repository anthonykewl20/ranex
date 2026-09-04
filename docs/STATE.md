# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (SLICE-083 closed, pushed; no open slice)
**Active slice:** none

## Where we stopped

SLICE-083 / ADR-050 done — second slice of the GitHub acceptance loop.
The Ranex GitHub App's publisher exists: `ranex github check publish`
binds a PR head (SLICE-082), reads the committed verdict signer at HEAD,
and publishes the `ranex/acceptance` check whose conclusion is reachable
from exactly one place — a VERIFIED+PASS record. Everything else is
louder: FAIL → failure, absent → action_required, rejected → failure
naming the reader state, API error → `E-GITHUB-API-REFUSED` (one POST,
no retry). RS256 JWT on the pinned `cryptography` primitive, stdlib
transport, no new dependency; arms verify the JWT with the test's own
key and grep every emitted line for secrets. Sealed green at 1774/166.

One operational note carried from SLICE-082's close: a dogfood
iteration-011 dirt left by another lane was preserved in labelled
stashes; that lane has since committed its own artifacts.

## Next

The loop's last slice: receive. `ranex github listen` — stdlib
`http.server` on localhost, HMAC-SHA256 delivery validation (the docs'
own test vector pinned), delivery-ID dedupe, installation/repository
allowlist, event grammar closed to `pull_request`
opened/synchronize/reopened; pipeline = fetch → bind → resolve →
publish. The App creation and ruleset documentation lands in README with
it (docs set stays closed). Then the deferred slices: anti-replay
(nonce, journal head anchor, F-005 item 1) and the approver signature
SLICE-080 made possible.

Still open: F-004; interval-honest wording; nightly divergence with an
absolute `--out`; more permissive external repos.

## Governance

ADR-047/048/049/050 accepted. Manifest re-frozen at 1774 IDs,
`expected_skips` byte-identical at 166 (the publisher arms skip
nothing). The live one-shot against the real API is UNVERIFIED until
the App exists — the receiver slice wires that journey.

## Known limits

The catalog binds keys to principals, never principals to humans. No
replay detection yet. Trainer labels host-relative, no journal head
anchor, mutmut UNVERIFIED.
