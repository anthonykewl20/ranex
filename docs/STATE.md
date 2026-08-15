# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-15 (session close)
**Active slice:** none.

## Where we stopped

Security and CI hygiene closed clean. The Security tab's 109 stale osv-scanner
alerts (pre-rewrite lineage) are fixed: cryptography >=50.0.0,<51 with a
byte-identical epoch re-derivation, plus a contract-bound CI osv-scan job
(push + weekly) uploading under the tracked category — 0 open since. Lint/type
debt cleared (ruff + pyrefly pass on CI); upload-sarif on v4.37.7; SLICE-017/018
suites made honest on hosted runners via declared host-qualification skips and
exact-signature fail-closed refusal branches (suite_manifest 906 IDs / 113
expected-skips). CI fully green since f141ed128 — first time since Aug 7;
the qualified-host suite is unchanged at 1023 passed / 8 skipped.

Docs synced to that reality (README known-gaps/current-work/counts; MAP 3.5.5,
RISK-06 closure propagated throughout). Issue tracker audited: every completed
item's issue is already closed; the 26 open ones are unstarted program slices,
harness-lane work, or the living P0 tracker — none closable.

SLICE-047 (confinement hardening, ADR-024) is ACTIVE in worktree
ranex-wt-slice047 under another session (mid-QA at last check). Do not touch
that tree; it rebases over f141ed128 when it lands.

## Next

SLICE-029 (#12): governance/schemas/specification/*.schema.json +
abc-v1-vectors.json per the pre-stage pack; one open slice at a time.
Owner: merge ranex-harness worktree-provisioning when #61 lands.

## Known limits

- Controller subprocess is same-uid trusted infrastructure; env narrowing is
  a named follow-up (ADR-023 review).
- Confinement digests are signed but not yet enforced by claim type.
- Frozen gate-1/3 real-session tests stay expected-skips without a delegated
  writable cgroup root; gate-3 passes under delegation.
- cgroup-observer OSError(19) flake under load remains.
- mutmut advisory not run this cycle.
- Harness HEAD: event-manifest off-by-one pre-existing (53e5209f56); stale
  WorktreeFailed.data in generated SDK types; two harness CI runs queued ~18h.
