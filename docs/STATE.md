# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-31 (checked-out-worktree coherence enforced, issue #56 closing)
**Active slice:** none

## Where we stopped

Issue #56 implemented — ADR-042's checked-out-worktree coherence. `task merge`
into a checked-out branch refuses BEFORE the ref moves when the worktree's
dirty set intersects the candidate diff (`sad-path-23 worktree-conflict`, max
3 paths shown); the scan covers `--untracked-files=all`, rename/copy
pre-images, and ignored files at candidate-changed paths (ff-merge silently
replaces ignored files in the way). Disjoint operator changes are preserved.
Otherwise the ref moves and the worktree is synchronized
(`checkout --detach` → `merge --ff-only` → `symbolic-ref HEAD`; the detach
avoids a post-CAS "Already up to date" no-op), and `PUBLISHED` prints only
after sync succeeds. Sync failure after the ref moved journals an ABORTED
outcome naming the exact state plus a shlex-quoted fast-forward repair
command, exits nonzero, never prints PUBLISHED; retrying merge refuses as
sad-path-9 tip-mismatch. Crash recovery stays honest: INFERRED when the
candidate is at the ref, appending the stale-worktree fact and the same repair
to the journaled detail when the checkout's HEAD is stale, degrading to the
ref-only detail when inspection fails, never printing PUBLISHED. Documented
residual: skip-worktree/assume-unchanged files are reported clean by git and
are not detected. Suite 1579 tests, 157 expected skips (issue #56 closing
evidence). Work landed across c433360f7, 541134538, 593a1cb5c plus further
hardening uncommitted on disk at writing. ADR-042 recorded; ADR-012, README,
and MAP synced.

## Next

Issue #58, then #64 and #65; umbrella #66 last.

## Governance

ADR-038: preserve epoch discipline—deliberate re-locks and builds pass
`--exclude-newer 2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per
ADR-009 and refuses governed subcommands outside its containing checkout.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
Framework closed: SLICE-055 closed 2026-08-19
ADR-039: coverage floor 64 comes from the enforcing pipeline; confinement-only
lines carry the pragma convention.

## Known limits

- Version stays 0.0.0 until the release-gate slice (#66).
