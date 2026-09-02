# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-02 (issue #65 closed, #73 filed)
**Active slice:** none

## Where we stopped

Issue #65 is CLOSED: the full owner authority path ran live on main
@ 28cdf2e75 — fresh `ranex keygen` owner key, A/B/C authored and
validated through `ranex specification draft|advance`, C signed by
`ranex specification approve` (ADR-045), and a real 3-child × 2-flow
batch qualified under a delegated cgroup scope with the committed
static worker (`--pool 1`, exit 0, journal append). Eight-case
fail-closed matrix green; `ranex task batch verify` PASS; journal
chain=verified; judge/merge refused with the golden-pinned
E-BATCH-PUBLICATION-REFUSED. Evidence on the issue.

Issue #73 filed from that run: parallel child qualification
(`--pool 2`) refuses E-C18-GATE in a freshly delegated scope — the
unlocked v3 verifier probe races the locked cgroup drain in
host_confinement.py. Tracker #66 now blocks on #73 only.

## Next

Issue #73 (p0, v0.1.0 milestone); umbrella #66 last; #68/#69 remain
open follow-ups from #56.

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
- Batch qualification at `--pool 2` under a freshly delegated scope
  refuses E-C18-GATE (#73); `--pool 1` is the proven lane.
- Strict-local requires a delegated cgroup scope; the `ranex host
  strict-local` wrapper establishes it, and the controller remains
  same-UID trusted infrastructure (ADR-044).
- `mutmut` remains an UNVERIFIED residual: no negative control or
  consuming gate (MAP §1.5).
- The concurrent-CAS journal race family is documented, not fixed;
  verification cannot detect snapshot replacement (RISK-19 adjacent).
