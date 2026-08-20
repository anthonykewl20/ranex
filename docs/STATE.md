# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-059 spec opened; task-family tests frozen red)
**Active slice:** SLICE-059 — docs/slices/SLICE-059-real-e2e-task-family.md

## Where we stopped

SLICE-059 (#39, the task family — milestone 4's last family slice) is
open per the frozen contract on #39 (status:ready 2026-08-20). The two
family files are committed red in the SLICE-056..058 pattern: 9 failed /
3 passed / 2 skipped at the freeze (the 9 = every golden arm naming its
missing golden; the skips = the fanout arm citing #19 and the delegation
journey's ranex-prereq:openrouter_key: — the key is absent on this
host). Every kernel behavior asserted was observed against 5e1ea681d in
/tmp/opencode prototypes before freezing.

## Next

Framework closed: SLICE-055 closed 2026-08-19
The implementation lane captures the three goldens, records their
sha256 digests in the slice file, posts AC-2's refusal artifacts on
#39, and runs G-4's real delegation (the owner exports the scoped
OpenRouter key; AC-3 evidence is the real run alone). G-3 re-derives
fail_under; the ceremony registers the family. Carried follow-ups
unchanged: the argument-filtered clone decision and the writable-tree
full-mask EXECUTE residual (security-review-owned), the mirror-pin
test for `_journal_first_broken_row` (SLICE-056), the SLICE-055 items,
and SLICE-060's review-named pair (cross-claim-set duplication;
newline-bearing claim IDs).

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2 (MAP §0.24: milestone 4 is P0's proof substrate)

## Known limits

- CI's `test` job is red on main at 5e1ea681d, pre-dating SLICE-059: `uvx ruff@0.16.2 check src tests` fails on nine findings in src/ranex and earlier slices' frozen test files (disclosed on #39; SLICE-059's surface denies them — owner-directed).
- Tracker #33's Phase-2 "MAP §4.7 row at open time" cannot be met inside #39's frozen surface (docs/MAP.md denied); no SLICE-054..060 row exists — owner to resolve (CCR or owner-directed governance commit).
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
