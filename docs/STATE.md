# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-060 opened)
**Active slice:** `docs/slices/SLICE-060-gate-evaluate-presentation-dedup.md`

## Where we stopped

SLICE-060 (#40) is open: `cmd_gate_evaluate`'s FAIL block prints the
absence sentence twice in a mixed stale+absent verdict (observed
2026-08-20 against a real journey — the ranex-video ep02 demo). The
repair dedups presentation only — the block records what it said and
drops exact clause repeats from the printed reason; the recorded
reason bytes are untouched (ADR-020's invariant). Spec is open; next
is the red freeze of `tests/e2e/test_gate_evaluate_mixed_cli.py`
(fresh-context author), then the fix (hand-verified candidate at
099698769 on `fix/duplicate-absence-sentence`, re-landed through this
slice) with the `MAIN_PY_SHA256` refresh, then the standing ceremony
(+4 IDs), qa-gate on the full publish range, automatic go-live.
SLICE-058 closed 2026-08-20 (ceremony 81d63d495; details on #38).

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-059
Milestone 4's last family slice (#39): the task family — real
dispatch/judge/merge/delegate journeys plus the fanout qualification,
riding ADR-032's frame as the fourth family customer (spec opens via
idea-refine/spec-prd on owner-confirmed intent). Carried follow-ups:
the argument-filtered clone decision and the writable-tree full-mask
EXECUTE residual (security-review-owned), the mirror-pin test for
`_journal_first_broken_row` (SLICE-056), the SLICE-055 items.

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
