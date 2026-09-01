# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-01 (issue #64 closed, SLICE-077 archived)
**Active slice:** none

## Where we stopped

Issue #64 is CLOSED: the operable strict-local host workflow shipped
(SLICE-077, ADR-044). The public `ranex host` group exposes six verbs
(`launcher-build`, `launcher-install`, `host-probe`, `qualify`,
`launcher-identity`, `strict-local`); `ranex host strict-local --version
v1|v2|v3` prepares/enters the delegated cgroup and runs without manual
systemd choreography. Suite re-frozen at 1675 IDs / 162 expected skips;
two independent sealed ceremonies green (1558 passed / 117 skipped,
byte-identical manifests, golden byte-matched). Real-host acceptance
5/5 arms: v1/v2/v3 confined runs in the delegated scope, prereq-failure
named check + corrective, cross-scope drift → E-C18-HOST-DRIFT exit 2.

## Next

Issue #65; umbrella #66 last.

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
- Strict-local requires a delegated cgroup scope; the `ranex host
  strict-local` wrapper establishes it, and the controller remains
  same-UID trusted infrastructure (ADR-044).
- `mutmut` remains an UNVERIFIED residual: no negative control or
  consuming gate (MAP §1.5).
- The concurrent-CAS journal race family is documented, not fixed;
  verification cannot detect snapshot replacement (RISK-19 adjacent).
