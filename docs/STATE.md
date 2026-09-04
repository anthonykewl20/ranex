# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (SLICE-081 closed, pushed; SLICE-082 open)
**Active slice:** docs/slices/SLICE-082-pr-head-binding-v1.md

## Where we stopped

Week 2 identity and evidence work landed. SLICE-080 / ADR-047: the trust
root says what a principal is permitted to be (`principals:` block, roles,
active/retired keys). SLICE-081 / ADR-048: evidence binds the rulebook it
ran under — domain v5, `envelope_type`/`gate_id`/`catalog_digest` inside
the exact signed set, a foreign rulebook refused as
`policy-context-mismatch`. Kernel unmoved for either; sealed 1730/166.

Now open, by owner decision: the GitHub acceptance loop, three slices —
SLICE-082 (bind: a PR head SHA derives the verdict subject through the
local object store; ADR-049), then publish (the `ranex/acceptance` check
from the Ranex GitHub App), then receive (webhook listener; the ruleset
documentation lands in README with it). Host-side only; the kernel and the
signed surface do not move.

## Next

Finish the loop (publish, receive). Then the deferred slices in order:
anti-replay (nonce, journal head anchor, F-005 item 1 — ADR-048 records
that a straight replay under unchanged rules is not yet detected), and the
approver signature SLICE-080 made possible (key material the owner
generates; none is committed).

Still open: F-004; interval-honest wording; nightly divergence with an
absolute `--out`; more permissive external repos.

## Governance

ADR-047/048 accepted; ADR-049 accepted with SLICE-082. Manifest frozen at
1730 IDs / 166 skips; the loop's slices re-freeze as their arms land. The
frozen approved-batch fixture set is re-keyed (ADR-048); its new private
key lives beside the vectors.

## Known limits

The catalog binds keys to principals, never principals to humans. No replay
detection yet. Trainer labels host-relative, no journal head anchor, mutmut
UNVERIFIED.
