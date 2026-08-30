# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-30 (specification lifecycle registered, issue #60 closing)
**Active slice:** none

## Where we stopped

Issues #63 and #67 are both closed. #63 installed the operator CLI (chain
`9eceda8..2b8aae9`). #67 fixed all 33 pyrefly errors and restored fully green
CI for the first time since 2026-08-25 (run 33306193214 at `fe09b53`: ruff,
pyrefly 0 errors, pytest 1434 passed / 121 skipped on the runner,
changed-lines coverage 100%). The fix also un-masked and repaired three
environment/fixture breakages: runner userns restriction lifted via sysctl;
two governed-copy fixtures set `PYTHONDONTWRITEBYTECODE`; sigkill tests
prereq-gate the pinned resolver; and git `%aI` is compared as parsed instants.
ADR-039 and coverage floor 64 landed en route.
Issue #60 implemented — `ranex specification` registered (ADR-040, schema evt
3, manifest 1560), full suite 1531/29 green, acceptance evidence on the issue.

## Next

Issue #62, #56, #58, #64, #65; umbrella #66 last.

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
