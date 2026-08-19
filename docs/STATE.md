# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-057 closed + correction round)
**Active slice:** none

## Where we stopped

SLICE-057 (#37, execution-family real e2e) is done, archived, and corrected (done slice file:
docs/slices/done/SLICE-057-real-e2e-execution-family.md). The frozen survivor arm was VACUOUS
(its backgrounded worker never existed — empty-MS_NODEV-/dev pre-exec kill, six-grant Landlock
EXECUTE, PID-1 pidns reaping) and was reframed at c981074fd into the falsifiable containment-
by-construction arm (mutation-verified); the real kill/drain proof lives in the timeout arm.
All three families green: run 5/5 both contexts; confinement 7/7 delegated, plain sessions
skipping the five probe-gated arms on the live qualified_host reason (the reframed arm skip-
declared under its new ID); freeze green past the correction-round ceremony (manifest 1363 IDs
/ 124 expected skips, the survivor ID exchanged for the reframed arm's in both maps). Full
suite at the final state: 1345 passed / 18 skipped / 0 failed. Goldens: run-evidence d8c363a9…,
confinement-report e688a37d… (byte-equality re-verified at the final artifact), suite-freeze-
manifest c12033d6…. The journey forced three never-executed-code kernel fixes (enrollment
0013bf427, sleep 128d13552, process-creation e1e6dc8a7), all orchestrator-ruled amendments on
#37; the security review (PASS-WITH-RESIDUALS) gates the range before push. Pins: artifact ea17bcae…, build manifest bcb4fef1…, profile 5c001f70…, report e9b8df6b….

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-058
Per ADR-032's deferral note, the next milestone-4 family slice is the provisioning family
(likely SLICE-058); it opens through governance when selected. Carried follow-ups: the
argument-filtered clone decision and the writable-tree full-mask EXECUTE residual (both
security-review-owned), the mirror-pin test for `_journal_first_broken_row` (SLICE-056),
and the SLICE-055 items.

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
- Writable trees carry full-mask Landlock EXECUTE — live since the execve admission (self-written binaries exec in-sandbox; contained by inheritance; SLICE-057 MINOR-4, review-owned).
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (next session refuses E-C18-HOST-DRIFT); concurrent sessions in one delegated scope interfere (serialize).
