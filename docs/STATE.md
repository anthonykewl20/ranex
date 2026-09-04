# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (SLICE-080 and SLICE-081 closed)
**Active slice:** none

## Where we stopped

Week 2 identity and evidence work, two slices done.

SLICE-080 / ADR-047 — the trust root says what a principal is permitted
to be. `governance/producers.yaml` carries an additive `principals:`
block: identity, one role, rotating keys with active/retired status.
Nothing consumes it yet; SLICE-082 is where an approver proves identity
by signature instead of by a typed name.

SLICE-081 / ADR-048 — evidence binds the rulebook it ran under. Domain
v4 to v5; `envelope_type`, `gate_id` and `catalog_digest` are inside the
exact signed set. Editing `governance/gates.yaml` after a green run now
refuses that run's evidence as `policy-context-mismatch` — its own
reason, never forgery and never absence. Absence is recorded, not
refused: a run with no committed catalog says `catalog-absent`, which
blocks at the verdict (ADR-011), because `run` is not only the gating
path.

The kernel did not move for either. `KERNEL_DIGEST` unchanged.

## Next

SLICE-082 — anti-replay: a nonce and a journal head anchor, which needs
`--journal` on `run` and also closes F-005 item 1. Until it lands, old
evidence is refused when the code or the rules changed, but a straight
replay under unchanged rules is not yet detected. ADR-048 records that.

Then the approver signature that SLICE-080 made possible. An approver
principal needs key material the owner generates; none is committed.

## Governance

ADR-047 and ADR-048 accepted. Manifest re-frozen at 1730 IDs,
`expected_skips` byte-identical at 166. The frozen approved-batch fixture
set was re-keyed (ADR-048): it was sealed with a key absent from this
repository and hard-coded the v4 evidence shape, so it blocked any
envelope change. Its new private key is stored beside the vectors.

## Known limits

The catalog binds keys to principals, never principals to humans. No
replay detection yet. Otherwise as before: trainer labels host-relative,
no journal head anchor, mutmut UNVERIFIED.
