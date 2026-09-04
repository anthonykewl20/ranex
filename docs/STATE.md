# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-04 (SLICE-080 authenticated principals, in progress)
**Active slice:** docs/slices/SLICE-080-authenticated-principals.md

## Where we stopped

SLICE-080 / ADR-047 — the committed trust root learns to say *what a
principal is permitted to be*, so a later slice can prove an approver by
signature instead of accepting `--approver <name>` as a bare string.

`governance/producers.yaml` gains an additive `principals:` block:
identity, exactly one role (ADR-030's vocabulary plus `service`), and an
ordered key list with `active`/`retired` status. New loader
`principal_catalog.py` resolves a key to its principal, refuses one key
under two principals, refuses a retired key as a signer, and refuses the
file if `producers:` and `principals:` disagree about who owns a key.
The kernel does not move: the catalog is an admission-layer input.

One unplanned edit: `load_trust_keyring_text` pinned the document to
exactly two blocks, so no additive block was possible until its closed
set admitted `principals`. Widened by one name, still closed, pinned.

## Next

Full suite green, then close SLICE-080 (file to `done/`, README row,
this file rewritten). Then SLICE-081 — Evidence Envelope v1: bump the
signing domain to v5 and bind policy context (`catalog_digest`,
`gate_id`) and anti-replay context (nonce, journal head anchor), which
also closes F-005 item 1. Then SLICE-082 — the approver signs, and
no-self-approval compares resolved principals.

Still open from before: F-004; interval-honest wording; an absolute
`--out` nightly divergence; more permissive external repos.

## Governance

ADR-047 added (accepted). ADR-038/009/030/025 unchanged. No kernel,
contract, or suite-manifest ID changes yet — SLICE-080 adds test IDs, so
`governance/suite_manifest.json` needs a re-freeze before the gate runs
against this tree.

## Known limits

The catalog binds keys to principals, never principals to humans: one
operator can add a second principal and approve their own work. ADR-047
records it; review of the committed diff is the control. Otherwise as
before: trainer labels host-relative, no journal head anchor, mutmut
UNVERIFIED.
