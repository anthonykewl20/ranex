# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (SLICE-082 closed, pushed; SLICE-083 open)
**Active slice:** docs/slices/SLICE-083-github-check-publisher-v1.md

## Where we stopped

SLICE-082 / ADR-049 done — first slice of the GitHub acceptance loop. A
pull-request head SHA, resolved through the local git object store, derives
the exact subject every signed verdict already names (`github bind`, pure
derivation, no network), and `resolve_acceptance` maps every verdict-reader
state onto a closed outward outcome: only `VERIFIED` is publishable,
absence is named as absence, every rejection names its state. No new
signed surface; the kernel did not move. Sealed green at 1754/166.

One operational note: a dogfood iteration-011 dirt (modified
`tools/dogfood/backlog.json`, untracked `iterations/iteration-011.json`)
was left in the tree by another lane mid-close-out; it is preserved in a
labelled stash (`git stash list`) and is not part of any slice here.

## Next

The loop continues, two slices: publish (the `ranex/acceptance` check from
the Ranex GitHub App — JWT on the pinned `cryptography` primitive, stdlib
transport, fail-closed conclusion mapping), then receive (the webhook
listener, localhost-bound, HMAC-validated, and the App + ruleset
documentation in README). Then the deferred slices: anti-replay (nonce,
journal head anchor, F-005 item 1) and the approver signature SLICE-080
made possible.

Still open: F-004; interval-honest wording; nightly divergence with an
absolute `--out`; more permissive external repos.

## Governance

ADR-047/048/049 accepted. Manifest re-frozen at 1754 IDs, `expected_skips`
byte-identical at 166 (the SLICE-082 arms skip nothing). The frozen
approved-batch fixture set remains re-keyed (ADR-048), key beside the
vectors.

## Known limits

The catalog binds keys to principals, never principals to humans. No
replay detection yet. Trainer labels host-relative, no journal head
anchor, mutmut UNVERIFIED.
