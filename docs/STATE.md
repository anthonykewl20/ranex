# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (SLICE-080 closed, pushed; SLICE-081 open)
**Active slice:** docs/slices/SLICE-081-evidence-envelope-v1.md

## Where we stopped

SLICE-080 / ADR-047 done. The committed trust root now says *what a
principal is permitted to be*, not only *is this key ours*.
`governance/producers.yaml` carries an additive `principals:` block —
identity, one role (ADR-030's vocabulary plus `service`), and an ordered
key list with `active`/`retired` status. `principal_catalog.py` resolves
a key to its principal and refuses: one key under two principals, a
respelled key, two roles, a retired key as signer, and the two blocks
disagreeing about who owns a key. Nothing consumes it yet — that is
SLICE-081/082. The kernel did not move; `KERNEL_DIGEST` untouched.

Two defects the full suite caught that targeted runs could not: the
trust root must be committed before it decides a verdict (the tool
refused its own author), and four arms asserting "this repository has a
catalog" failed inside journeys that clone the repo and replace its
keyring. Both fixed; sealed 1715/166, `pytest -q` 1681 passed.

## Next

Week 2 continues. SLICE-081 — Evidence Envelope v1: bump the signing
domain v4 to v5, add `payload_type`, and bind the policy context
(`catalog_digest`, `gate_id`) evidence does not carry today, so a changed
gate catalog can no longer reuse old evidence. `run` already knows both.
Admission resolves `producer_id` through the catalog. `SIGNED_FIELDS` is
exact, so ~27 test files that build evidence by hand move with it.

Then SLICE-082 — anti-replay: nonce plus a journal head anchor (needs
`--journal` on `run`), which also closes F-005 item 1.

Still open: F-004; interval-honest wording; nightly divergence with an
absolute `--out`; more permissive external repos.

## Governance

ADR-047 accepted; ADR-038/009/030/025 unchanged. Manifest re-frozen at
1715 IDs, `expected_skips` byte-identical at 166.

## Known limits

The catalog binds keys to principals, never principals to humans: one
operator can add a second principal and approve their own work. ADR-047
records it; review of the committed diff is the control. Otherwise as before:
trainer labels host-relative, no journal head anchor, mutmut UNVERIFIED.
