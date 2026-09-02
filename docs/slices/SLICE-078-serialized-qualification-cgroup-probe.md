# SLICE-078 — serialized qualification cgroup-probe topology

**Status:** open
**Opened:** 2026-09-02
**Priority:** P0 — production blocker (issue #73)
**Issue:** #73
**ADR:** docs/adr/ADR-046-cgroup-probe-serialization.md

## Contract

Issue #73 acceptance criteria (verbatim):

- Root cause pinned by a deterministic red test (parallel qualifies in a
  fresh delegated scope) — no sleep-based flake.
- Fix lands (probe under the same lock, or drain/enable ordering that
  keeps sibling-visible controllers intact) with the frozen-suite gates.
- pool=2 batch qualification re-run green inside a delegated scope with
  evidence attached to the issue.

## Owned paths

- Modify: `src/ranex/cli/host_confinement.py` —
  `_runtime_v3_verifier_isolation_probe` acquires `_host_probe_lock()`
  around its body (ADR-046). No other product file changes.
- Tests: `tests/e2e/test_delegated_probe_serialization.py` (new, frozen
  red before the fix).
- Governance: `governance/suite_manifest.json` re-freeze after the new
  test IDs land green.
- Docs close-out: this slice file, `docs/STATE.md`, README, `docs/MAP.md`.

## Done criteria

1. `tests/e2e/test_delegated_probe_serialization.py::test_v3_verifier_probe_blocks_while_the_host_probe_lock_is_held`
   fails deterministically on unmodified main (the probe completes while
   the lock is held) and passes after the fix (the probe blocks on the
   flock, completes only after release).
2. After the fix's fork/verify dance, the driving process's
   `/proc/self/cgroup` is the scope root again and no `ranex-ctl-*` /
   `ranex-slice018-*` leaves remain under it — proven by the same test.
3. `tests/e2e/test_delegated_probe_serialization.py::test_parallel_qualifies_in_one_fresh_delegated_scope_both_qualify`
   runs two real `host_confinement qualify` provisions concurrently in
   one freshly delegated scope and both exit 0 with `qualified=true`.
4. The existing batch-qualification journey
   (`tests/e2e/test_specification_batch_qualification.py`) is green —
   single-pool behavior unchanged.
5. Full suite green and the manifest re-frozen with the new IDs;
   `tests/contract/test_docs_discipline.py` green; ruff and pyrefly
   clean on the touched files.
6. The #65 owner-authority batch re-qualified `--pool 2` inside a
   delegated scope; transcript, exit codes, and event stream attached
   to issue #73.

## Tranche plan

- T0 (this tranche): governed docs — ADR-046 with vendored prior art,
  this slice opened, STATE/README repointed; frozen red test committed.
- T1: the one-function fix; red→green; full gates; manifest re-freeze.
- T2: pool=2 delegated-scope acceptance re-run; evidence on issue #73.
- T3: docs close-out — slice to `docs/slices/done/`, STATE/README/MAP
  updated; issue #73 closed with commit SHA and command output.

## Evidence

(to be recorded per tranche)

## Non-goals

- No cross-batch or session-vs-qualify locking (journal discipline
  already serializes batches; ADR-046 scope note).
- No change to the drain/enable ordering inside `_real_cgroup_probe` or
  `_create_worker_cgroup`.
- No new CLI surface, report field, refusal code, or schema number.
