# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-20 (SLICE-057 opened)
**Active slice:** docs/slices/SLICE-057-real-e2e-execution-family.md

## Where we stopped

SLICE-057 (#37, execution family — run + confinement + suite freeze)
opened through governance: slice file written (ADR-032 link, the issue's
exact ownership, host-gating strategy recorded), STATE/README synced,
`in-progress` claimed on #37. Every kernel behavior the family asserts
was prototyped against e84b5176a in /tmp/opencode: the run journey with
stdlib digest recompute + openssl verification and both sabotage
refusals, the two-root launcher-build drift contract, the real-tree
freeze round-trip (byte-stable, 53931503…97139, run_exit=0), and the
dirty-tree/hand-edit refusals. This host is confinement-unqualified
(pinned build closure drifts, /etc/ld.so.cache), so the strict-local
arms ride the frame's `qualified_host` probe — named skips here,
assertions on a qualified host.

## Next

Framework closed: SLICE-055 closed 2026-08-19
Next slice: SLICE-057 (open now)
Worker A freezes the three red test files + golden contracts
(test_run_real, test_confinement_real, test_suite_freeze_real);
Worker B implements: capture the three goldens from the real journeys,
post AC2's traced event stream + AC3's sabotage red output, run the
registration ceremony. The register's open follow-ups stand: the P3
mirror-pin test for `_journal_first_broken_row`, and the SLICE-055
follow-ups queued in its done slice file.

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
