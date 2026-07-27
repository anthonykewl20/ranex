# Ranex Implementation Status

Last updated: 2026-07-27 (Asia/Manila)

## Current baseline

- Upstream repository: `NousResearch/hermes-agent`
- Upstream baseline: `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`
- Upstream version at adoption: `0.19.0`
- Recovery branch: `bootstrap/pre-upstream`
- Adoption branch: `phase/1-adopt-upstream`
- Public origin: `anthonykewl20/ranex` (standalone and empty before adoption)

The adoption candidate is based directly on upstream history. Ranex
architecture, research, legal, and governance records are layered onto that
history without merging the bootstrap repository's unrelated root.

The Phase 2 development-environment example was deliberately pulled into the
adoption candidate so the first upstream-based checkout can be launched
immediately. It is an inert example, contains no host-specific secret, and
does not claim that the remaining Phase 2 acceptance criteria have passed.

## Active objective

Install and verify this development checkout with isolated state under
`~/.local/share/ranex`, then use Hermes itself to drive bounded Ranex
implementation work.

## Recorded deviation

On 2026-07-27, the owner explicitly directed implementation to begin while
Codex and VS Code were active and their deferred cleanup remained incomplete.
This is a human-approved sequencing waiver, not a claim that the Phase 0A
cleanup gate passed. The deferred cleanup remains tracked separately and does
not authorize an automated shutdown or state deletion.

## Next implementation slices

1. Verify the upstream Hermes CLI against the isolated Ranex application home.
2. Capture the unmodified runtime and test baseline.
3. Build the brand/integration inventory.
4. Start the compatibility-first public rebrand on `develop`.

Authoritative architecture and lifecycle rules are indexed from
`docs/architecture/README.md`.
