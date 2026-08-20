# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-21 (SLICE-059: comparator blocker ruled — final phase executing)
**Active slice:** SLICE-059 — docs/slices/SLICE-059-real-e2e-task-family.md

## Where we stopped

SLICE-059 (#39) is in its final phase on issue/39 @ bbc4e4d0d + the
close commits. The real G-4 journey ran green end-to-end (CCR-2 store-
read credential, CCR-3 seeded GitHub-tool deny; harness HEAD 9b9b521c61cb,
bun 1.3.14): `delegation-diff.out` captured from it (sha256 cac49c48…),
G-1 at contract shape green (12/2/0). The byte-exact re-run blocker was
ruled Option 1 — bless the contract-shaped close (DECISION
issuecomment-5359345600): C-4's re-run clause is unsatisfiable with the
free model (six runs, three note-line forms) and is a written owner
risk-acceptance; zero frozen-test changes; CCR-4 shape-golden text
drafted for any future owner. fail_under re-derived: measured 16.68 →
14 (floor − 2, baseline convention). Remaining: ceremony (+14 IDs,
fanout + operator-action declarations), G-1..G-5 at the final SHA,
docs close-out, EVIDENCE + status:review.

## Next

Framework closed: SLICE-055 closed 2026-08-19
After #39 validates and closes: milestone 3 resumes at SLICE-036 (#19,
MAP §0.24) — which also un-gates the fanout assertions' follow-up
governed change. Carried follow-ups unchanged: the argument-filtered
clone decision and the writable-tree full-mask EXECUTE residual
(security-review-owned), the mirror-pin test for
`_journal_first_broken_row` (SLICE-056), and SLICE-060's review-named
pair (cross-claim-set duplication; newline-bearing IDs).

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2 (MAP §0.24: milestone 4 is P0's proof substrate)

## Known limits

- CI's `test` job is green again on main after the CI-debt fixes (3f900d027, 9243bea41, eb1c1e413/8dc685cca), merged into issue/39 at 0344644ff.
- MAP §4.7 rows for SLICE-054..058/060 remain absent (tracker #33 Phase-2 cure applied to SLICE-059 only, via CCR-1; the others wait on their own owner acts).
- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES); cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest; trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed).
- The journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags); writable trees carry full-mask Landmark EXECUTE — SLICE-057's recorded residuals, review-owned.
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (next session refuses E-C18-HOST-DRIFT); concurrent sessions in one delegated scope interfere (serialize).
- The hermetic seal's netns starts `lo` DOWN and the seal's exec drops CAP_NET_ADMIN, so loopback-only fixtures skip inside the seal (SLICE-058's ruled option-A fallback; the two local-index arms run outside it).
- SLICE-059 residual (owner-accepted, DECISION issuecomment-5359345600): the free model's note-line content is nondeterministic — a credentialed host re-running the delegation journey gets a content coin-flip and the byte-exact golden fails on the content lines alone; canonical entrypoint and G-1 unaffected.
