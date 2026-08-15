# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-15 (late)
**Active slice:** none (SLICE-047 closed; SLICE-029 next).

## Where we stopped

Security and CI hygiene closed clean. The Security tab's 109 stale osv-scanner
alerts (pre-rewrite lineage) are fixed: cryptography >=50.0.0,<51 with a
byte-identical epoch re-derivation, plus a contract-bound CI osv-scan job
(push + weekly) uploading under the tracked category — 0 open since. Lint/type
debt cleared (ruff + pyrefly pass on CI); upload-sarif on v4.37.7; SLICE-017/018
suites made honest on hosted runners via declared host-qualification skips and
exact-signature fail-closed refusal branches. CI fully green since f141ed128.

SLICE-047 (ADR-024) is closed: all 17 frozen tests are green (16 proved
red→green), and the SLICE-046 boundary remains 6 pass / 1 declared host skip.
Independent double review APPROVE found no P0–P2; its P3s are dispositioned in
the archived slice. The full-suite result is recorded at closure after Phase 3.

SLICE-048 is the next confinement follow-up: enforce confinement digests by
claim type in verdict/admission/loading. Dead LC_ALL/TZ descriptor fallback and
worker-cgroup-leaf reconciliation remain named follow-ups, not SLICE-047 work.

SLICE-029 opening design is consensus + upstream-validated: keep the code-point
canonicalizer, use a strict parse profile and DSSE-style framing, close
ApprovalPayloadV1, keep the error registry as data, use journal-order time,
chained-row revocation, and allow one live batch per subject+base. Harness lane:
merge worktree-provisioning when #61 lands; SLICE-021 then builds on EventV2.

## Next

SLICE-029 (#12): governance/schemas/specification/*.schema.json +
abc-v1-vectors.json per the pre-stage pack; one open slice at a time.

## Known limits

- Controller subprocess is same-uid trusted infrastructure; environment
  narrowing remains an ADR-023 follow-up.
- Confinement digests are signed but not yet enforced by claim type (SLICE-048).
- Frozen gate-1/3 real-session tests stay expected-skips without a delegated
  writable cgroup root; gate-3 passes under delegation.
- cgroup-observer OSError(19) flake under load remains.
- mutmut advisory not run this cycle.
