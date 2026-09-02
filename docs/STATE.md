# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-03 (rules simplification sealed; host loader-cache re-pinned)
**Active slice:** none

## Where we stopped

Issue #73's fix is fully landed and evidenced on the issue (chain
8f7f59fa4..f9482ff05 on main); the issue itself still awaits closing. The
rules simplification (f932f9d09) took the frozen suite to **1653 IDs /
164 expected skips**; golden and this file now say 1653. The dogfood loop
(tools/dogfood) landed with its four interface docs admitted by the docs
cap as a closed set.

Host drift, handled: the 2026-09-03 01:00 +0800 unattended libc-bin
upgrade regenerated /etc/ld.so.cache, breaking the pinned launcher build
closure (E-C17-BUILD-INPUT-DRIFT). Only that input drifted; the rebuilt
launcher is byte-identical to the pinned artifact digest (f3e1e1e9…), so
the loader-cache sha256 was re-recorded deliberately (7489d8c0…) and
launcher-build/install re-verified green.

## Next

Close #73 (evidence posted). Issue #74 (session-path cgroup mutations
unlocked; serialization goes at the session call sites — never inside the
shared helpers, which would self-deadlock); then umbrella #66 (release
gate, v0.1.0); #68/#69 remain open follow-ups from #56.

## Governance

ADR-038: preserve epoch discipline—deliberate re-locks and builds pass
`--exclude-newer 2026-08-04T00:00:00Z`; the CLI remains checkout-anchored per
ADR-009 and refuses governed subcommands outside its containing checkout.
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
