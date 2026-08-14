# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-15
**Active slice:** none (SLICE-046 closed; SLICE-029 unblocked and next).

## Where we stopped

SLICE-046 (issue #21) closed and pushed: cmd_run binds to the qualified
strict-local session via the subprocess controller (ADR-023); evidence
SIGNED_FIELDS 8->10 + domain v4; ADR-006 accepted, RISK-06 closed in MAP
11.5, ADR-017 accepted — SLICE-029 (#12) prerequisites now MET. Full
suite 1023 passed / 8 skipped at the pushed commit. Harness lane:
SLICE-020 (#1) implementation complete on branch worktree-provisioning
(a6c395926f, ranex-harness) — merge to ranex-trim pending the owner's
#61 session; SLICE-021 (#2) is next there and builds on its EventV2
foundations. SLICE-029 pre-stage pack (A/B/C field inventory, error
vocabulary, vector design, deferred-mechanism recommendations) lives in
this session's report.

Risk-closure session on top: CI lint/type debt cleared — the 9 findings
that pre-dated Aug 14 plus SLICE-046's four new main.py findings
(I001 imports, F841 dead binding, B009 constant-getattr, B904 cause
chain, pyrefly bad-return/bad-assignment), MAIN_PY_SHA256 refreshed per
the gate10 precedent; upload-sarif pinned to v4.37.7 (the v3 line
retires Dec 2026). Security tab: 0 open / 109 fixed; the weekly scan's
60-day inactivity disablement is documented in ci.yml.

## Next

Open SLICE-029 (#12): governance/schemas/specification/*.schema.json +
abc-v1-vectors.json per the pre-stage pack; one open slice at a time.
Owner: merge ranex-harness worktree-provisioning when #61 lands.

## Known limits

- SLICE-046 real-session test stays a declared host-gated skip (no
  delegated writable cgroup-v2 root); gate-3 passes under delegation.
- Controller subprocess is same-uid trusted infrastructure; env
  narrowing is a named follow-up (ADR-023 review).
- Confinement digests are signed but not yet enforced by claim type —
  ADR-017 follow-up work owns it.
- Frozen gate-1/3 real-session tests stay expected-skips (issue #21).
- cgroup-observer OSError(19) flake under load remains.
- mutmut advisory not run this cycle.
- Harness HEAD: event-manifest off-by-one pre-existing (53e5209f56);
  stale WorktreeFailed.data in generated SDK types.
