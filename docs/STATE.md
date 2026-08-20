# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-057 closed; codex final gate remediated)
**Active slice:** none

## Where we stopped

SLICE-057 (#37, execution-family real e2e) is done, archived, corrected, and
past the codex final gate (done slice: docs/slices/done/SLICE-057-*). The
frozen survivor arm was VACUOUS (MS_NODEV /dev pre-exec kill, six-grant
Landlock EXECUTE, PID-1 pidns reaping); reframed c981074fd, rescoped 5510c7767
to test_shell_constructed_descendants_die_and_the_layers_are_pinned (layers
pinned to call sites, _stop shadow fixed); the real kill/drain proof lives in
the timeout arm. Families green: run 5/5 both contexts; confinement 7/7
delegated; freeze past the final ceremony b82c081c8 — 1363 IDs / 124 skips,
the rescoped ID exchanged in both maps, the five confinement declarations
reclassified ranex-context:host-capability per the slice's recorded strategy
(cross-check informational; lint green). Final suite: 1345 / 18 / 0 (794.45s).
Goldens: d8c363a9…, e688a37d…, c12033d6…. Kernel fixes 0013bf427, 128d13552,
e1e6dc8a7 (orchestrator-ruled amendments); the security review
(PASS-WITH-RESIDUALS) gates the range before push. Pins: ea17bcae…,
bcb4fef1…, 5c001f70…, e9b8df6b….

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-058
Per ADR-032's deferral note the next milestone-4 family slice is the provisioning family
(likely SLICE-058), opening through governance. Carried follow-ups: the argument-filtered
clone decision and the writable-tree full-mask EXECUTE residual (both security-review-owned),
the mirror-pin test for `_journal_first_broken_row` (SLICE-056), the SLICE-055 items.

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
- Writable trees carry full-mask Landlock EXECUTE — live since the execveat admission (321cb524d's first pinned filter admitted openat+execveat, so self-written binaries were executable by fd BEFORE e1e6dc8a7; e1e6dc8a7's execve widened the surface to plain pathname exec) — self-written binaries exec in-sandbox; contained by inheritance; SLICE-057 MINOR-4, review-owned.
- Availability, fail-closed (SLICE-057 MINOR-1/5): an enrollment/teardown crash wedges the controller leaf (next session refuses E-C18-HOST-DRIFT); concurrent sessions in one delegated scope interfere (serialize).
