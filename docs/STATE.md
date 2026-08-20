# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-060 closed through the standing ceremony)
**Active slice:** none

## Where we stopped

SLICE-060 (#40, gate-evaluate presentation dedup) is done and archived
(docs/slices/done/SLICE-060-*): a mixed stale+absent verdict no longer
prints the absence sentence twice. The dedup is anchored — exact
suffix comparison against the partition's own sentence — and steps
aside whenever a missing claim ID contains "; " (round 1's confirmed
blocker: a split-based fix truncated adversarial claim IDs). Reason
bytes untouched (ADR-020). 5 frozen arms (2 red→green), ceremonies
7c99838fa/8cda414af (FROZEN tests=1383 expected_skips=134 run_exit=0),
full suite 1365/18/0 at 8cda414af, two non-author APPROVEs (round-2
fuzz: 789,672 cases, zero violations); evidence on #40.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-059
Milestone 4's last family slice (#39): the task family — real
dispatch/judge/merge/delegate journeys plus the fanout qualification,
riding ADR-032's frame as the fourth family customer (spec opens via
idea-refine/spec-prd on owner-confirmed intent). Carried follow-ups:
the argument-filtered clone decision and the writable-tree full-mask
EXECUTE residual (security-review-owned), the mirror-pin test for
`_journal_first_broken_row` (SLICE-056), the SLICE-055 items, and
SLICE-060's review-named pair — cross-claim-set duplication (refused
restated as absence; slice candidate) and newline-bearing claim IDs.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2 (MAP §0.24: milestone 4 is P0's proof substrate)

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed).
- The journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags) — SLICE-057's recorded residual; contained by the inheritance facts, review-owned.
- Writable trees carry full-mask Landlock EXECUTE — live since the execveat admission (321cb524d's first pinned filter admitted openat+execveat, so self-written binaries were executable by fd BEFORE e1e6dc8a7; e1e6dc8a7's execve widened the surface to plain pathname exec) — self-written binaries exec in-sandbox; contained by inheritance; SLICE-057 MINOR-4, review-owned.
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (next session refuses E-C18-HOST-DRIFT); concurrent sessions in one delegated scope interfere (serialize).
- The hermetic seal's netns starts `lo` DOWN and the seal's exec drops CAP_NET_ADMIN, so loopback-only fixtures skip inside the seal (SLICE-058's ruled option-A fallback; the two local-index arms run outside it).
