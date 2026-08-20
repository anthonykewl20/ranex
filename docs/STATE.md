# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-21 (SLICE-059: delegation golden captured from the real G-4 run; BLOCKED on the owner's comparator ruling)
**Active slice:** SLICE-059 — docs/slices/SLICE-059-real-e2e-task-family.md

## Where we stopped

SLICE-059 (#39) is BLOCKED at the owner-decision point (issuecomment
5359180442), branch issue/39 @ 5fe0d3849 (pushed). CCR-2 + CCR-3 fixed
the G-4 environment: the wrappers hit the real bridge entry
(packages/ranex/src/index.ts) and seed the harness-native deny for the
GitHub tool family whose union schemas the free model's upstream
rejects; the run reads the owner's existing OpenRouter credential from
the owner's store (run env only, never printed, store untouched). The
real delegated journey then ran green end-to-end and
`delegation-diff.out` is captured from it (sha256 cac49c48…). G-1 at
its contract shape (credential unset, SP-1 skip) is green: 12 passed /
2 skipped / 0 failed. The blocker: the free model's note-line content
is nondeterministic (six runs, three forms, temperature 0 included), so
the frozen byte-exact comparator fails repeated credential-bearing runs
— the owner must pick: bless the contract-shaped close (G-4 evidenced
by the capture run; residual disclosed), CCR-4 shape-golden, retry
budget, or a model change.

## Next

The owner's ruling on #39 unblocks mechanically: ceremony re-freeze
(+14 IDs, fanout + operator-action declarations), G-2/G-3/G-5 at the
final SHA, fail_under re-derivation, docs close-out, EVIDENCE,
status:review. Carried follow-ups unchanged: the argument-filtered
clone decision and the writable-tree full-mask EXECUTE residual
(security-review-owned), the mirror-pin test for
`_journal_first_broken_row` (SLICE-056), and SLICE-060's review-named
pair (cross-claim-set duplication; newline-bearing IDs).

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
- SLICE-059 (2026-08-21): the free model's note-line content is nondeterministic across runs — the frozen byte-exact delegation comparator fails repeated credential-bearing runs; owner ruling pending (#39 issuecomment 5359180442).
