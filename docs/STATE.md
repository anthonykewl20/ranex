# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-21 (SLICE-059 closed; public architecture docs refreshed under #41)
**Active slice:** none

## Where we stopped

SLICE-059 (#39, task family — milestone 4's last family slice) is done
and archived (docs/slices/done/SLICE-059-*): dispatch→work→`run`→judge,
the tampered-evidence/self-approval/moved-base/digest-mismatch refusals,
the clean PUBLISHED merge, worktree-residue detection, and the real
delegated model run — three goldens captured from the real journeys
(sha256 dbe923e7…/f7ff1f74…/cac49c48…), red controls dirty, fanout arm
skipped-with-name until #19. The byte-exact re-run blocker was ruled
Option 1 (DECISION issuecomment-5359345600): C-4's clause is a written
owner risk-acceptance; zero frozen-test changes. Ceremony 56c445a1f:
FROZEN tests=1397 expected_skips=136 run_exit=0 (sealed 1262/135/0);
round-trip 6/6; cross-check exit 0 honest; fail_under 16.68 → 14.
G-1 12/2/0, G-2 clean, G-3/G-5 at the final SHA — tails in the
close-time EVIDENCE on #39 (status:review).

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-036
Milestone 4's family work is complete (tracker #33 closure is the
validator's act); milestone 3 resumes at SLICE-036 (#19, MAP §0.24),
which also un-gates the fanout assertions' follow-up change. Carried
follow-ups unchanged: the argument-filtered clone decision and the
writable-tree full-mask EXECUTE residual (security-review-owned), the
mirror-pin test for `_journal_first_broken_row` (SLICE-056), and
SLICE-060's review-named pair (cross-claim-set duplication;
newline-bearing IDs).

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2 (MAP §0.24: milestone 4 is P0's proof substrate)

## Known limits

- CI's `test` job is green again on main after the CI-debt fixes (3f900d027, 9243bea41, eb1c1e413/8dc685cca), merged into issue/39 at 0344644ff; confinement suites still fail on hosted runners (ld.so.cache drift, userns EACCES).
- MAP §4.7 rows for SLICE-054..058/060 remain absent (tracker #33 Phase-2 cure applied to SLICE-059 only, via CCR-1; the others wait on their own owner acts).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest; trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed); the journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags); writable trees carry full-mask Landmark EXECUTE — SLICE-057's recorded residuals, review-owned.
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (E-C18-HOST-DRIFT next session); concurrent sessions in one delegated scope interfere (serialize).
- SLICE-059 residual (owner-accepted, DECISION issuecomment-5359345600): the free model's note-line content is nondeterministic — a credentialed re-run of the delegation journey gets a content coin-flip and the byte-exact golden fails on the content lines alone; canonical entrypoint and G-1 unaffected.
