# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-057 closed)
**Active slice:** none

## Where we stopped

SLICE-057 (#37, execution-family real e2e) is done and archived
(docs/slices/done/SLICE-057-real-e2e-execution-family.md). All three
families green: run 5/5 both contexts; confinement 7/7 in the
delegated scope (survivor arm green at e1e6dc8a7) with plain sessions
skipping the five probe-gated arms on the live qualified_host reason;
freeze green past the 59479a1e7 ceremony (manifest 1363 IDs / 124
expected skips, sealed run 1260/103/run_exit=0). Full suite at close:
1345 passed / 18 skipped / 0 failed (912.10s). Goldens: run-evidence
d8c363a9…, confinement-report e688a37d… (kept at the final artifact),
suite-freeze-manifest c12033d6…. The journey forced three
never-executed-code kernel fixes (enrollment 0013bf427, sleep
128d13552, process-creation e1e6dc8a7), all orchestrator-ruled
amendments on #37; the security review gates the range
0013bf427…e1e6dc8a7 before push. Final pins: artifact ea17bcae…,
build manifest bcb4fef1…, profile 5c001f70…, report e9b8df6b….

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-058
Per ADR-032's deferral note, the next milestone-4 family slice is the
provisioning family (likely SLICE-058) — the in-process stdlib server
fixture, ephemeral-port binding, and the goldens' masked <PORT> tokens
the frame deferred; it opens through governance when selected.Carried follow-ups: the argument-filtered clone decision
(security-review-owned), the mirror-pin test for
`_journal_first_broken_row` (SLICE-056), and the SLICE-055 items.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape (subprocess-heavy tests vs the in-process trampoline; disclosed).
- The journal does not detect rollback/truncation (SLICE-056 characterized; fold-in at 8a5ed3837).
- default-deny-v1 admits `clone` nr-only (any flags) — SLICE-057's recorded residual; contained by the inheritance facts, review-owned.
