# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-03 (issue #73 closed, SLICE-078 archived)
**Active slice:** none

## Where we stopped

Issue #73 is CLOSED: the v3 verifier isolation probe now runs its
whole cgroup topology dance (reads included) under `_host_probe_lock`
(ADR-046, SLICE-078), and the lock's directory fd gained an at-fork
guard so forked children cannot wedge it. The deterministic frozen red
reproduced the exact `E-C18-GATE lacks the pids controller` refusal
before the fix; the sealed freeze re-landed at 1653 IDs / 164 expected
skips (run_exit=0); and the #65 owner authority re-qualified the batch
`--pool 2` inside a fresh delegated scope — exit 0, verify PASS,
journal chain=verified (transcript on #73).

Follow-up filed from the panel: #74 (session-path cgroup mutations
still unlocked; serialization, when taken, goes at the session call
sites — never inside the shared helpers, which would self-deadlock).

## Next

Issue #74; then umbrella #66 (release gate); #68/#69 remain open
follow-ups from #56.

## Governance

ADR-038: preserve epoch discipline—deliberate re-locks and builds pass
`--exclude-newer 2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per
ADR-009 and refuses governed subcommands outside its containing checkout.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
Framework closed: SLICE-055 closed 2026-08-19
ADR-039: coverage floor 64 comes from the enforcing pipeline; confinement-only
lines carry the pragma convention. Governed self-gate note: the `anthony`
producer key is absent from this host; the sealed freeze is the proof.

## Known limits

- Version stays 0.0.0 until the release-gate slice (#66).
- Strict-local sessions mutate cgroup topology without the host-probe
  lock (#74); the supported batch flow never overlaps them.
- Strict-local requires a delegated cgroup scope; the `ranex host
  strict-local` wrapper establishes it, and the controller remains
  same-UID trusted infrastructure (ADR-044).
- `mutmut` remains an UNVERIFIED residual: no negative control or
  consuming gate (MAP §1.5).
- The concurrent-CAS journal race family is documented, not fixed;
  verification cannot detect snapshot replacement (RISK-19 adjacent).
