# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-16 (SLICE-032 archived and registered locally)
**Active slice:** none.

## Where we stopped

Kernel slices SLICE-029 through SLICE-033 and SLICE-035 are merged, archived,
and registered locally. A/B/C schemas, lifecycle, approval/revocation and
intersected grants, deterministic projections, independent trace verification,
and real-subject bootstrap are complete. The real Ranex subject ran; Arxic
credential absence records BLOCKED. Push remains pending final review.

SLICE-046 + SLICE-047 remain landed: `cmd_run` is bound to the qualified
strict-local session (ADR-023; ADR-006 accepted, RISK-06 closed, ADR-017
accepted), the confinement-result validator is single-sourced, and the
controller subprocess uses a fixed minimal environment with bounded kill.

Harness lane: SLICE-020 (#1) merged to ranex-trim at `582d06d0` (41 pass /
1 skip / 0 fail); the local harness main and origin diverge on disjoint files
and need reconciliation. Harness #84 tracks the SDK codegen blocker
(`WorktreeFailed.data` stale). The TypeScript mirror for #12 remains there.

## Next

#12 still needs the TypeScript schema/vector mirror in the harness lane.
SLICE-036 owns CAS/persistence and the SpecificationEvent atomicity contract.
SLICE-048 (claim-type confinement-digest enforcement) remains after those
slices; SLICE-021 (#2) builds on merged EventV2 work in the harness lane.

## Known limits

- SLICE-046/047 real-session tests stay declared host-gated skips.
- CI: confinement suites fail on hosted runners (ld.so.cache drift,
  userns EACCES) — owner-decides; owner session added honest guards
  (f141ed128).
- Controller same-uid trust, worker-cgroup-leaf on SIGKILL, dead
  LC_ALL/TZ fallback: named follow-ups (ADR-024/047).
- cgroup-observer OSError(19) flake under load remains.
- mutmut advisory not run this cycle.
