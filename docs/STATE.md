# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->
**Updated:** 2026-08-29 (real-data production acceptance, issue #55)
**Active slice:** none

## Where we stopped

The repository is a pre-release, source-run Python kernel. Its public CLI covers
gate, journal, run, suite, deps, keygen, serial/prototype tasks, and batch qualification.

The code implements deterministic gates, signed subject/command-bound evidence,
committed-tree execution, hash-chained SQLite, suite-ID freezing, dependencies,
serial publication, external delegation/fanout prototypes, internal A/B/C APIs,
non-publishable batch qualification, signed verdicts, and strict-local confinement.

Real-data acceptance passed the core self-gate (1,441 passed, 109 declared
skips), live PyPI provisioning, signed verdicts, real-model delegation/fanout,
and delegated-service strict-local v2/v3. Ranex is not yet an end-to-end human
production product; see GitHub issue #55.

There is no installed harness, main-CLI specification lifecycle, owner intake,
task board, deployment, built-in model, or end-to-end A/B/C mutation workflow.

## Next
Framework closed: SLICE-055 closed 2026-08-19
Next slice: none scheduled; the owner must choose any new product-code scope.

## Governance
Kernel-only initial release; no implementation slice is active.
Historical note — Build order: milestone 4 → milestone 3 → milestone 2
(superseded by the 2026-08-25 kernel-only scope reset).
Documentation capability claims must cite current source and executable tests;
archived slices and prior prose are history, not the source of truth.

## Known limits

- `task delegate` records a nonzero suite exit but returns orchestration success
  after a completed delegation; only a gate evaluation issues a verdict.
- Free-prompt fanout has no A/B/C child admission; batch qualification cannot
  publish.
- The source CLI needs `PYTHONPATH=src`; no installed command is available.
- Task publication needs a manual candidate-evidence handoff, and successful
  ref publication can leave a checked-out worktree dirty.
- Delegation outcomes do not retain inspectable harness/session logs.
- `evidence.json` replaces same-claim/same-producer rows; it is not append-only.
- The suite manifest freezes IDs and skip reasons, not test bodies.
- Journal verification cannot detect an internally consistent older snapshot.
- Strict-local requires an operator-retained delegated cgroup on this host and
  trusts a same-UID controller; direct ordinary v1 use did not pass acceptance.
