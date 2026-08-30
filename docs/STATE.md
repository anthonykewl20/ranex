# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-30 (green CI restored, issue #67)
**Active slice:** none

## Where we stopped

Issue #67 is closing: all 33 pre-existing pyrefly type errors are fixed
(chain `56b0192..HEAD`). The local CI replica is green: ruff exit 0, pyrefly
exit 0, full suite 1527 passed / 29 skipped, coverage xml exit 0 at floor 64,
and diff-cover 100%.
ADR-039 records the confinement-coverage boundary. The `subject.py`
first-iteration bug is fixed with a regression test. The suite manifest is at
1556 IDs / 157 declared skips.

## Next

Issue #60 (register the specification lifecycle — `build_parser` +
`observability/schema.py` `STAGES` + the frozen `CLI_DISPATCH_GROUPS` literal
edited together), then #62, #56, #58, #64, #65; umbrella #66 last.

## Governance

ADR-038 landed: hatchling builds under the frozen epoch; never run bare
`uv lock` — deliberate re-locks and builds always pass
`--exclude-newer 2026-08-04T00:00:00Z` (a bare lock silently strips the
epoch; now contract-tested in `test_packaging.py`). hatchling==1.31.0 is a
locked dev dependency; governed offline builds use
`UV_NO_BUILD_ISOLATION=1` with the provisioned backend. The CLI is
checkout-anchored per ADR-009: a wheel installed anywhere prints help but
refuses governed subcommands outside the checkout containing it.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
(superseded by the 2026-08-25 kernel-only scope reset).
Framework closed: SLICE-055 closed 2026-08-19
ADR-039: `fail_under` derives from the enforcing in-process pipeline (floor
64); confinement-only lines carry the pragma convention.

## Known limits

- Specification lifecycle unregistered (#60).
- Version stays 0.0.0 until the release-gate slice (#66).
