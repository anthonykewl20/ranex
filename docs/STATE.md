# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-01 (issue #64 claimed, ADR-044 accepted, SLICE-077 open)
**Active slice:** docs/slices/SLICE-077-operable-strict-local-host-workflow.md

## Where we stopped

T0 governed docs of the strict-local host-workflow slice (issue #64, P0):
ADR-044 accepted with vendored prior art (systemd v257 systemd-run.xml;
linux v6.12 cgroup-v2 delegation excerpt) and SLICE-077 opened; the
implementation tranche (src/ranex/cli/host_workflow.py, `ranex host`
parser wiring, contract/integration/e2e tests) is owned by concurrent
agents. Truth fix over the previous STATE: the freeze golden
(tests/e2e/expected/suite-freeze-manifest.out) says the suite is
re-frozen at 1644 IDs with 157 expected skips byte-matched — the
stale "1619" figure is retired.

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
- Strict-local direct use outside the planned `ranex host strict-local`
  wrapper remains unqualified on plain terminals until the wrapper ships
  (ADR-044; truthful interim state, not a regression).
