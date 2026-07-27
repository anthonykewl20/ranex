# Ranex Implementation Status

Last updated: 2026-07-27 (Asia/Manila)

## Current baseline

- Upstream repository: `NousResearch/hermes-agent`
- Upstream baseline: `d71033a4077a6dfdcdb42c9e9eeab4c41e4a7012`
- Upstream version at adoption: `0.19.0`
- Ranex adoption commit: `9be6bd9443e447b205ad265d44238436910dfbce`
- Recovery branch: `bootstrap/pre-upstream`
- Adoption branch: `phase/1-adopt-upstream`
- Runtime branch: `phase/2-runtime-bootstrap`
- Public origin: `anthonykewl20/ranex` (standalone; verified empty before adoption)

The published adoption commit is based directly on upstream history. Ranex
architecture, research, legal, and governance records are layered onto that
history without merging the bootstrap repository's unrelated root.

Remote `main` and the initial `develop` point at the adoption commit.
`upstream-sync` points at the unmodified upstream baseline. Local `main`
tracks `origin/main`, and the annotated local tag
`upstream-baseline-20260727` resolves to the upstream SHA.

The primary checkout intentionally remains on `bootstrap/pre-upstream` while
another Codex/VS Code session has active documentation changes. Only its
checkout switch to `main` is deferred; the public and local policy refs are
already aligned.

## Phase results

| Phase | Result | Evidence |
|---|---|---|
| Phase 0A cleanup | `PARTIAL` | Explicit owner sequencing waiver; active Codex/VS Code state remains protected |
| Phase 1 upstream adoption | `PARTIAL` | Publication, ancestry, remotes, licensing, and manifest passed; the primary checkout switch is deferred to protect active documentation work |
| Phase 2 isolated environment | `PASS` | External Python 3.11 environment, locked editable install, Node dependencies, CLI/config checks |
| Phase 3 upstream baseline | `PARTIAL` | 48,519 Python passes with 3 classified upstream host-sensitive failures; 4,826 JavaScript passes with zero failures |

The detailed test and warning record is
[`UPSTREAM_BASELINE.md`](UPSTREAM_BASELINE.md).

## Active objective

Complete the separate OpenAI Codex device login and one-shot model smoke, then
use Hermes itself from the isolated development checkout to drive bounded
Ranex implementation work.

## Recorded deviation

On 2026-07-27, the owner explicitly directed implementation to begin while
Codex and VS Code were active and their deferred cleanup remained incomplete.
This is a human-approved sequencing waiver, not a claim that the Phase 0A
cleanup gate passed. The deferred cleanup remains tracked separately and does
not authorize an automated shutdown or state deletion.

## Next implementation slices

1. Complete and record the live model smoke.
2. Integrate the runtime-bootstrap evidence into `develop`.
3. Build the brand/integration inventory.
4. Start the compatibility-first public rebrand from a bounded branch based on
   `develop`.

Authoritative architecture and lifecycle rules are indexed from
`docs/architecture/README.md`.
