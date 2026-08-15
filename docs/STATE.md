# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-15 (session close)
**Active slice:** none (SLICE-046/047 closed; SLICE-029 next).

## Where we stopped

SLICE-046 + SLICE-047 landed on main (tip 02b09f6b): cmd_run is bound
to the qualified strict-local session (ADR-023; ADR-006 accepted,
RISK-06 closed, ADR-017 accepted), the confinement-result validator is
single-sourced in foundation/confinement_result.py, and the controller
subprocess runs on a fixed minimal env with bounded process-group kill
on timeout (ADR-024). Full suite 1040 passed / 8 skipped at the tip.

Harness lane: SLICE-020 (#1) MERGED to ranex-trim at 582d06d0 (merge of
worktree-provisioning; 41 pass / 1 skip / 0 fail on the merge; branch
deleted) — #1 closed with proof. The owner's parallel session parked the
dormant security sweep on secfix-snapshot and advanced the local main
checkout to 4f0965c7; local ranex-trim and origin (582d06d0) diverge on
disjoint files — reconcile by pull/merge when convenient. Harness #84
tracks the SDK codegen blocker (WorktreeFailed.data stale).

## Next

SLICE-029 (#12, unblocked): A/B/C schemas + canonical rules + error
registry + abc-v1-vectors.json + the TS mirror — design is frozen in
STATE history (02b09f6b) after consensus + upstream validation: keep
the code-point-order canonicalizer (NOT JCS UTF-16), strict parse
profile (duplicate-member/lone-surrogate/float/-0/lexical rejection,
ints <= 2^53-1), DSSE-style length-prefixed domain framing, closed
ApprovalPayloadV1 with detached signature, error registry + precedence
as normative data, journal-order-authoritative time, chained-row
revocation, one live batch per (subject, base). Then SLICE-048
(claim-type confinement-digest enforcement — design in SLICE-047's
closure). Harness: SLICE-021 (#2) builds on the merged EventV2 work.

## Known limits

- SLICE-046/047 real-session tests stay declared host-gated skips.
- CI: confinement suites fail on hosted runners (ld.so.cache drift,
  userns EACCES) — owner-decides; owner session added honest guards
  (f141ed128).
- Controller same-uid trust, worker-cgroup-leaf on SIGKILL, dead
  LC_ALL/TZ fallback: named follow-ups (ADR-024/047).
- cgroup-observer OSError(19) flake under load remains.
- mutmut advisory not run this cycle.
