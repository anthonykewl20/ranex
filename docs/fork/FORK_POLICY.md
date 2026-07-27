# Ranex Fork Policy

Ranex is a standalone public software fork of
[`NousResearch/hermes-agent`](https://github.com/NousResearch/hermes-agent).
Its Git history retains the upstream commits, and the `upstream` remote records
that relationship. Ranex is not represented as an official Nous Research
product or as a GitHub network fork.

## Repository boundaries

- `origin` is `https://github.com/anthonykewl20/ranex.git`.
- `upstream` fetches from
  `https://github.com/NousResearch/hermes-agent.git`; its push URL is disabled.
- Upstream `LICENSE` remains unchanged.
- `LICENSE-RANEX.md` applies only to original Ranex Material owned by Anthony
  Garces.
- `NOTICE.md` and `legal/licensing-manifest.json` define provenance and
  file-level licensing scope.
- Upstream trademarks, logos, service identities, and credentials are not
  Ranex assets merely because their code remains in the compatibility
  baseline.

## Change policy

- Stable releases land on `main`; implementation integrates through `develop`.
- `upstream-sync` remains a clean upstream tracking branch.
- Feature work uses bounded `feature/<issue>-<slug>` branches and named
  worktrees.
- Agents do not force-push, rewrite published history, or implement directly
  on `main`.
- Compatibility-preserving changes are preferred until a replacement has
  tests, migration evidence, and rollback behavior.
- Each modified upstream file and each original Ranex file must be classified
  in the licensing manifest before publication.

## Human authority

The owner is the final authority for public releases, destructive operations,
credential use, policy waivers, and changes to the locked Ranex identity.
Implementation may continue under a recorded waiver, but a waived gate remains
visible as debt until its original acceptance criteria are satisfied.
