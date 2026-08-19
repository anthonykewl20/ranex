# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-19 (SLICE-055 complete)
**Active slice:** none

## Where we stopped

SLICE-055 (#35) is delivered and closed. ADR-032 is accepted and revised
(two review panels plus arbitration remediation); the frame — probes,
cross-check, normalizer, subprocess coverage, entrypoint — is green
through every frozen arm (68/68 across the two contract files). The
manifest's expected skips carry the two-grammar classification (the
first artifact's reclassification remedied one misclassified
declaration: prereq 4 → 3, only signing_key ×3 hard-tier, as recorded
on #35). The entrypoint artifact at 41bb4fef6: rc 0, coverage 16.70%
(report 17%) ≥ fail_under 15. Full suite at the pre-close-out SHA:
1297 passed / 40 skipped / 0 failed.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-056
Next work item: SLICE-056 (verdict family e2e) per tracker #33 — the
frame's first family customer; the follow-ups register in the done
SLICE-055 slice file goes to the next test-author round.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; passes isolated and on `origin/main`.
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape
  (subprocess-heavy tests vs the in-process trampoline; exclusion set
  extended twice by sanction, blocked finally by test_observability.py's own
  child-import shape); observability mutants therefore remain unchecked —
  mutation evidence not obtained this session, disclosed as partial.
- SLICE-055 follow-ups (dodge-refusal sample arms, fail_under derivation
  automation + branch=true decision, hook-shadow decoy arm) are registered
  in the done slice file for the next test-author round.
