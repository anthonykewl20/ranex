# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-059: two local goldens captured; delegation golden gated on the owner's key)
**Active slice:** SLICE-059 — docs/slices/SLICE-059-real-e2e-task-family.md

## Where we stopped

SLICE-059 (#39, milestone 4's last family slice) is mid-implementation
on issue/39. The two LOCAL goldens are captured at 7b134fbe9 from real
runs of the frozen journeys (digests, stability and sabotage record in
the slice file); the task family is fully green (10 passed / 1 fanout
skip, #19). The delegation file's three ungated golden arms stay red:
`delegation-diff.out` needs the owner's OPENROUTER_API_KEY (C-4/G-4),
so G-1 holds at exit 1 (3 failed / 9 passed / 2 skipped) and the
ceremony waits (precedent ceremonies seal green). CCR-1 (#39
issuecomment-5354660541, approved) added the MAP §4.7 SLICE-059 row.

## Next

Framework closed: SLICE-055 closed 2026-08-19
The owner exports the scoped OpenRouter key, then G-4's real run
captures `delegation-diff.out` (digest into the slice file), G-1 exits
0 with only the two named skips, G-3 re-derives fail_under, the
ceremony registers the family and re-captures the freeze golden, and
EVIDENCE + validator close follow per the contract. Carried follow-ups
unchanged: the argument-filtered clone decision and the writable-tree
full-mask EXECUTE residual (security-review-owned), the mirror-pin
test for `_journal_first_broken_row` (SLICE-056), and SLICE-060's
review-named pair (cross-claim-set duplication; newline-bearing IDs).

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2 (MAP §0.24: milestone 4 is P0's proof substrate)

## Known limits

- CI's `test` job is red on main at 5e1ea681d, pre-dating SLICE-059: `uvx ruff@0.16.2 check src tests` fails on nine findings in src/ranex and earlier slices' frozen test files (disclosed on #39; SLICE-059's surface denies them — owner-directed).
- MAP §4.7 rows for SLICE-054..058/060 remain absent (tracker #33 Phase-2 cure applied to SLICE-059 only, via CCR-1; the others wait on their own owner acts).
- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed).
- The journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags) — SLICE-057's recorded residual; contained by the inheritance facts, review-owned.
- Writable trees carry full-mask Landmark EXECUTE — live since the execveat admission (SLICE-057 MINOR-4, review-owned).
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (next session refuses E-C18-HOST-DRIFT); concurrent sessions in one delegated scope interfere (serialize).
- The hermetic seal's netns starts `lo` DOWN and the seal's exec drops CAP_NET_ADMIN, so loopback-only fixtures skip inside the seal (SLICE-058's ruled option-A fallback; the two local-index arms run outside it).
