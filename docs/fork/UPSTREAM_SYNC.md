# Upstream Sync

Ranex imports upstream history without unrelated-history merges or force
pushes. The clean `upstream-sync` branch is the reviewable boundary between
Hermes Agent and Ranex customization.

## Remote safety

```bash
git remote get-url origin
git remote get-url upstream
git remote get-url --push upstream
```

Expected values are the Ranex public origin, the official Hermes Agent fetch
URL, and `DISABLED` for upstream pushes.

## Refresh procedure

Run the sync in a dedicated worktree checked out on `upstream-sync`:

```bash
git fetch upstream --prune --tags
git merge --ff-only upstream/main
git push origin upstream-sync
```

If the fast-forward fails, stop and investigate the divergence. Never repair it
with a force push or an automatic merge.

## Integration procedure

1. Freeze and record the upstream candidate SHA.
2. Classify changes that can reintroduce upstream branding, hosted services,
   telemetry, installers, credentials, or state paths.
3. Run the upstream baseline and Ranex compatibility suites.
4. Open a reviewed change from `upstream-sync` into `develop`.
5. Resolve Ranex customizations deliberately; do not accept conflicts by side.
6. Record the accepted upstream baseline and release provenance.

The previous upstream baseline remains the rollback point until the integrated
candidate passes verification.
