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

## Independent runtime review

A fresh tool-less HY3 review audited the published adoption, isolated runtime,
configuration boundary, baseline claims, and immediate development readiness at
revision `beee3cdc431e38b6e82ec5628263f743932022e4`.

- Review verdict: `PASS`
- Readiness: `READY_WITH_REQUIRED_REMEDIATIONS`
- Immediate blockers: none
- Preserved phase state: Phase 0A `PARTIAL`, Phase 1 `PARTIAL`, Phase 2 `PASS`,
  Phase 3 `PARTIAL`

The [full unedited verdict and execution metadata](reviews/2026-07-27-hy3-runtime-bootstrap-final-review.md)
and [frozen review packet](reviews/artifacts/2026-07-27-hy3-runtime-bootstrap-review-packet.md)
are retained in the repository. HY3 is advisory evidence; it did not receive
gate authority or rerun the baseline suites.

The three inherited failures now have stable comparison identities in
[`BASELINE_DEFECTS.md`](BASELINE_DEFECTS.md). Phase 0A and the deferred primary
checkout switch remain visibly `PARTIAL`.

After the frozen review, Hermes' own config migrator updated the isolated
configuration from schema version `0` to `33`. A subsequent configuration check
passed and reconfirmed `openai-codex` / `gpt-5.6-sol`. No optional API key was
added. A live no-provider/no-model-override smoke then resolved those persistent
defaults and returned `RANEX_HERMES_CONFIG_OK`.

The first local dashboard build was then exercised successfully. The generated
web UI serves HTTP `200` on loopback at `http://127.0.0.1:9119`.

At the owner's subsequent request, the dashboard was installed as the
`ranex-hermes-dashboard.service` systemd user unit. It is enabled under
`default.target`, active, and restricted to `127.0.0.1:9119`. User lingering is
enabled, so the service starts after a reboot without requiring an open
terminal. The machine-local unit is stored at
`~/.config/systemd/user/ranex-hermes-dashboard.service`.

## Runtime selection

- Provider: `openai-codex`
- Default model: `gpt-5.6-sol`
- Credential boundary: Hermes uses its own device login under the isolated
  Ranex application home; it does not import or mutate Codex/VS Code
  authentication.

## Active objective

Use the verified Hermes runtime from the isolated development checkout to
drive bounded Ranex implementation work. The separate OpenAI Codex device
login and a one-call `gpt-5.6-sol` smoke have passed.

## Recorded deviation

On 2026-07-27, the owner explicitly directed implementation to begin while
Codex and VS Code were active and their deferred cleanup remained incomplete.
This is a human-approved sequencing waiver, not a claim that the Phase 0A
cleanup gate passed. The deferred cleanup remains tracked separately and does
not authorize an automated shutdown or state deletion.

## Next implementation slices

1. Build the brand/integration inventory.
2. Start the compatibility-first public rebrand from a bounded branch based on
   `develop`.

Authoritative architecture and lifecycle rules are indexed from
`docs/architecture/README.md`.
