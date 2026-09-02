# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-03 (v0.1.0 released; all tracked issues closed)
**Active slice:** none

## Where we stopped

**v0.1.0 is released.** Every blocker on umbrella #66 closed with
commit SHA + command evidence on its issue (#63, #67, #60, #62, #56,
#64, #58, #65, #73); the late residuals #74 (session cgroup mutations
under the host-probe lock), #69 (suite_tail canary filtering with
consecutive-green stability), and #68 (detached mid-sync worktree
recovery) are fixed and closed the same way. The release gate reran
the public feature inventory from the installed operator CLI — the
parser surface now listed in README matches it exactly (the host
group was missing) — and the suite is sealed at **1657 IDs / 166
expected skips, run_exit=0**, with the full suite green at 1623
passed / 34 skipped on the release commit.

## Next

The 0.1.x line: whatever the field sends back. The dogfood loop
(tools/dogfood) keeps watch — iteration 005: 33/33 scenarios pass, no
findings, no drift.

## Governance

ADR-038: preserve epoch discipline—deliberate re-locks and builds pass
`--exclude-newer 2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per
ADR-009 and refuses governed subcommands outside its containing checkout.
ADR-039: coverage floor 64 comes from the enforcing pipeline; confinement-only
lines carry the pragma convention. The `anthony` producer key is absent
from this host; the sealed freeze is the proof.

## Known limits

- Kernel-only, source-run: governed subcommands anchor to their
  checkout (ADR-009); the wheel is not a deployed product.
- Strict-local requires a delegated cgroup scope; the `ranex host
  strict-local` wrapper establishes it, and the controller remains
  same-UID trusted infrastructure (ADR-044).
- Cross-batch locking remains journal discipline (ADR-046 scope).
- `mutmut` remains an UNVERIFIED residual: no negative control or
  consuming gate (MAP §1.5).
- The concurrent-CAS journal race family is documented, not fixed;
  verification cannot detect snapshot replacement (RISK-19 adjacent).
