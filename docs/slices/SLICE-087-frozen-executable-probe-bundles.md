# SLICE-087 — Frozen executable probe bundles

**Status:** open
**Issue:** #116
**ADR:** docs/adr/ADR-061-live-acceptance-before-completion.md

## Contract

`ranex specification freeze-probes` reads actual committed probe files from
complete selected roots in a clean repository. It produces an external bundle
whose existing B manifest binds A, the literal argv, the descriptor and copied
probe bytes. The descriptor pins membership, Git modes and base commit.
No acceptance process runs during this artifact freeze.

`ranex specification check-probes` requires an independently trusted B digest.
It checks the bundle and a clean candidate's probe roots. Product changes outside
those roots are allowed. Success is PROBES-UNCHANGED, never product PASS.

Reject changed/deleted/added probes, mode changes, symlinks and nonregular files,
bundle tampering, invocation drift, dirty candidates, internal/worktree outputs,
overwrites and known SLICE-031 placeholder gauges. Literal roots are portable
relative names; duplicate/overlapping/empty roots refuse. No runtime dependency
growth, and verdict.py remains unchanged.

## Boundaries

The operator must enumerate all support inputs. No static dependency inference
or general mock detection is claimed. Bundle identity is not C approval, runtime
isolation, live execution, calibration or verdict evidence. A same-UID worker
still requires the forthcoming confinement composition. The remaining pivot
exits are named in ADR-061, not declared complete by this slice.

## Validation

Real CLI journeys in tests/integration/test_probe_bundle_cli.py. New cases were
observed red before implementation; candidate and bundle mode attacks included.
Full suite and committed-tree refreeze are required before the closing comment.
