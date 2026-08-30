# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-30 (task authority contract unified, issue #62 closing)
**Active slice:** none

## Where we stopped

Issue #62 implemented — ADR-041's single authority contract (dispatch/judge
default journals, worktree-relative evidence, merge reads the dispatched
worktree's evidence with governed fallback); the composed dispatch → run →
judge → merge flow publishes with zero file movement; full suite 1538 passed /
29 skipped (1567 IDs / 157 declared skips, run_exit=0); refusals sad-path-5/11
pinned.
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

Issue #56 — publication must leave the checked-out worktree coherent (merge
advances the ref without updating the worktree; same `cmd_task_merge` path just
stabilized by #62); then #58, #64, #65; umbrella #66 last.

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
