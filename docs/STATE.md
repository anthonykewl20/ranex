# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-29 (installed operator CLI closed, issue #63)
**Active slice:** none

## Where we stopped

SLICE-075 is complete and issue #63 is closing. The implementation chain
9eceda8 → 1394c24 delivered the frozen checkout install (`uv sync --frozen`
builds ranex editable plus the `ranex` console script), the hatchling build
system under the frozen epoch, and the re-frozen governance catalog. The
full suite is green at 1394c24: 1,526 passed / 29 skipped; ruff green.
Installed-CLI and wheel-boundary evidence is captured in issue #63.

The repository remains a pre-release governance kernel (see issue #55 for
the real-data acceptance baseline); its public CLI covers gate, journal,
run, suite, deps, keygen, and task commands.

## Next

Issue #67 (restore green CI — pyrefly is red on main), then issue #60
(specification lifecycle registration). T4 of SLICE-075 (coverage-floor
re-derivation) lands as its own pyproject commit.

## Governance

ADR-038 landed: hatchling builds under the frozen epoch; never run bare
`uv lock` — deliberate re-locks and builds always pass
`--exclude-newer 2026-08-04T00:00:00Z` (a bare lock silently strips the
epoch; now contract-tested in test_packaging.py). hatchling==1.31.0 is a
locked dev dependency; governed offline builds use
`UV_NO_BUILD_ISOLATION=1` with the provisioned backend. The CLI is
checkout-anchored per ADR-009: a wheel installed anywhere prints help but
refuses governed subcommands outside the checkout containing it.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
(superseded by the 2026-08-25 kernel-only scope reset).
Framework closed: SLICE-055 closed 2026-08-19

## Known limits

- Pyrefly is red on main (issue #67) — pre-existing, not SLICE-075.
- The specification lifecycle is unregistered in the main CLI (issue #60).
- Version stays 0.0.0 until the release-gate slice (umbrella #66).
