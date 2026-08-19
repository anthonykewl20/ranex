# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-19 (SLICE-055 opened; frame contract tests frozen red)
**Active slice:** docs/slices/SLICE-055-real-e2e-suite-framework.md

## Where we stopped

SLICE-055 (#35) is open per ADR-032 (accepted; two-panel remediation on
record) and tracker #33 phase order — Phase-2 production. Worker A froze
the frame's two contract test files RED before any implementation:
probe honesty, declared-skip cross-check (both directions), and the
golden normalizer grammar in tests/contract/test_prereq_gates.py;
README entrypoint, subprocess-coverage harness (--keep idempotence,
loud no-data scoped to wired children), and the joint trace+coverage
case in tests/contract/test_real_suite_entrypoint.py. Worker B implements
to green inside issue #35's exact ownership (tests/e2e/_prereqs.py, conftest
extensions, coverage/sitecustomize.py, pyproject [tool.coverage], README
entrypoint section); the frozen tests are read-only to the implementer. The
pinned interface is spelled in both files' docstrings and in the slice file.

## Next

Next slice: SLICE-054
Next work item: SLICE-055 implementation (Worker B), then the entrypoint
run captured as milestone 4's proof artifact. (The literal line above is
held by tests/contract/test_docs_discipline.py until STATE records
"Framework closed: SLICE-055 closed <date>".)

## Governance (owner, 2026-08-17)

Build order: milestone 4 → milestone 3 → milestone 2
Recorded in `docs/MAP.md` §0.24: milestone 4 is P0's proof substrate.

## Known limits

- CI confinement suites fail on hosted runners (ld.so.cache drift, userns EACCES).
- cgroup-observer `OSError(19)` can flake under load.
- SLICE-008 bounded-fanout timing can flake under full-suite load; passes isolated and on `origin/main`.
- About 125 legacy test IDs remain unregistered in the frozen manifest.
- Trace fd targets persist O_NONBLOCK on the operator's descriptor after exit (disclosed; slice file records the trade-off).
- mutmut: the stats phase cannot complete on the current suite shape
  (subprocess-heavy tests vs the in-process trampoline; exclusion set
  extended twice by sanction, blocked finally by test_observability.py's own
  child-import shape); observability mutants therefore remain unchecked —
  mutation evidence not obtained this session, disclosed as partial.
- SLICE-055's frozen tests are red by design until the frame lands; their
  IDs enter governance/suite_manifest.json only at the post-implementation
  suite-freeze ceremony (frozen criterion 8).
