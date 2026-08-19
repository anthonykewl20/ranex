# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-057 opened)
**Active slice:** docs/slices/SLICE-057-real-e2e-execution-family.md

## Where we stopped

SLICE-057 (#37, execution family) is open and RED-frozen. Opened at
61753dc84 (slice file, ADR-032 link, host-gating strategy, STATE/README
synced, `in-progress` claimed). Worker A froze the three test files red
at 7bdcae8b2 — per-file: test_run_real 3F/2P, test_confinement_real
1F/1P/5S (named `ranex-prereq:qualified_host:` skips — this host's
build closure drifts), test_suite_freeze_real 4F/2P (the real-tree
round-trip named its drift: +18 IDs, run_exit=1). Total 8F/5P/5S. Every
kernel behavior asserted was prototyped against e84b5176a in
/tmp/opencode (run journey, drift arm, real-tree freeze byte-stable,
dirty/hand-edit refusals); the strict-local arms are frozen from
SLICE-046/017/018-proven shapes and first execute on a qualified host.
Goldens are absent on purpose — the implementation lane captures them.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-057 (open, red-frozen)
Worker B implements: capture the three goldens from the real journeys,
post AC2's traced event stream + AC3's sabotage red output on #37, run
the registration ceremony (18 new IDs; the five confinement skips
declare context-tier per the slice's strategy). The register's open
follow-ups stand: the P3 mirror-pin test for `_journal_first_broken_row`,
and the SLICE-055 follow-ups queued in its done slice file.

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` and SLICE-008 bounded-fanout timing can flake under full-suite load (both pass isolated / on `origin/main`).
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape
  (subprocess-heavy tests vs the in-process trampoline; observability
  mutants remain unchecked — mutation evidence not obtained, disclosed).
- The journal does not detect rollback/truncation (SLICE-056
  characterized it; the ADR-032 fold-in landed at 8a5ed3837).
