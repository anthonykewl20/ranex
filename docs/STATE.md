# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-056 closed)
**Active slice:** none

## Where we stopped

SLICE-056 (#36, verdict-family real e2e) is done and archived
(docs/slices/done/SLICE-056-real-e2e-verdict-family.md). All eight
family arms green: four goldens captured from the real journeys
(2e6947e36), journal-verify row naming landed (8bdccb60d), the
truncation fixture's construction fixed per the Option-1 ruling
(b4e835c00). The suite-freeze ceremony at b4e835c00 (dabc91f68)
resolved the pre-registered hermetic UNKNOWN **hermetic-green** —
sealed run 1227 passed / 118 skipped / run_exit=0, exactly +8 over
the 41bb4fef6 baseline with the skip set unchanged, so no family arm
behaves differently sealed and the context-guard remedy was not
needed. Manifest: 1345 IDs (+8), expected_skips 119 byte-identical.
Full suite at close: 1305 passed / 40 skipped / 0 failed.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-057
SLICE-057 (#37, execution family — run + confinement + suite freeze
on a qualified host) is the next milestone-4 family slice per the
build order; it opens through governance (spec + ADR check) when
selected. The SLICE-056 carried follow-up — the ADR-032 fold-in of
the truncation blind spot — landed at 8a5ed3837; the register's open
item is the P3 mirror-pin test for _journal_first_broken_row. The
SLICE-055 follow-ups in its done slice file stay queued.

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
