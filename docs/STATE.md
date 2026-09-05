# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-09-05 (owner-requested release audit, issue #81)
**Active slice:** none

## Where we stopped

Release audit and real reproducers retained in tools/dogfood/audits/2026-09-05/.
Start at audit.json; FINDINGS.md explains F-001 through F-018.
53 external-repository controls cover v0.1.0 and corrected source separately;
16 real receiver controls reproduce nine defenses and seven gaps.
52 independently refetched prior-art sources match their vendored bytes.

## Corrections

Guardian argv[0] names its resolved interpreter; execution still uses the
verified fd. The Python 3.11 real execution-family check passes all seven tests.
Host-workflow acceptance now invokes each provisioned clone's CLI. Its same
seven real checks pass with no skips; 22 other direct host checks also pass.
Suite manifest, dependency lock, signing domain, and verdict kernel unchanged.

## Validation

The single closing comment on #81 records the final clean commit's exact SHA
and `uv run --frozen pytest -q` result. Detailed pre-commit results are in the
audit archive; failures and named skips are preserved alongside successes.
The released full-run aggregate is exploratory; isolated cold start confirms
8 passed, 1 failed. Live historical bootstrap and an extra tooling guard fail.
An observed journal contention timeout did not recur in its isolated rerun.

## Next

Fix receiver bounded reads and durable delivery/retry state (F-007/008/009).
Wire principal retirement into admission; reconcile XPASS/collection claims.
Repair bootstrap, benchmark attribution, and nested host integration.
Independent reporter truth and anchored replay/history remain explicit limits.

## Known limits

UNVERIFIED: live GitHub App/PR/ruleset and credentialed provider journeys,
unexecuted host/platform branches, and complete nested-host failure causes.
A hostile pytest reporter can receive authentic signed PASS for broken code.
Journal truncation/rewrite and ordinary evidence replay remain accepted.
