# SLICE-079 — serialized strict-local session cgroup mutations

**Status:** open
**Opened:** 2026-09-03
**Priority:** P1 — named residual risk (issue #74)
**Issue:** #74
**ADR:** docs/adr/ADR-046-cgroup-probe-serialization.md (2026-09-03 addendum)

## Contract

Issue #74 acceptance criteria (verbatim):

- Deterministic red test reproducing a session-vs-qualify interleaving
  refusal in one delegated scope (no sleep-based flake).
- Fix at the session call sites, or an ADR-recorded alternative; no
  deadlock against qualification probes. Frozen-suite gates.
- Evidence on this issue.

The red shape is the ADR-recorded alternative the issue itself allows:
the interleaving refusal is a load race (ADR-046 panel), so the frozen
red pins the serialization contract — a real session's cgroup mutations
(create AND release) must not complete while another process holds the
host-probe lock.

## Owned paths

- Modify: `src/ranex/cli/host_confinement.py` — the
  `_create_worker_cgroup` call site and the `_release_controller_leaf`
  call site inside `confinement_session` acquire `_host_probe_lock()`.
  The shared helpers stay lock-free (self-deadlock; ADR-046).
- Tests: `tests/e2e/test_delegated_session_serialization.py` (new,
  frozen red before the fix).
- Governance: `governance/suite_manifest.json` re-freeze after the new
  test IDs land green, with their delegated-scope skip declarations.
- Docs close-out: this slice file (to `docs/slices/done/`),
  `docs/STATE.md`, README completed-slices row.

## Done criteria

1. `test_session_cgroup_mutations_block_while_the_host_probe_lock_is_held`
   fails deterministically on unmodified main (the session completes
   exit 0 under a held lock) and passes after the fix (the session
   blocks, then completes green; scope root restored; no `ranex-*`
   residue).
2. `test_session_and_qualify_concurrently_in_one_fresh_delegated_scope_both_succeed`
   pins the steady state: established qualification, then a fresh
   qualify and a real session concurrently — both exit 0.
3. No deadlock: the existing full-session families (confinement_real
   journey, strict-local IO, host workflow) stay green.
4. Full suite green on the final commit; manifest re-frozen with the
   new IDs and their `ranex-context:delegated-scope:` declarations;
   docs discipline green; ruff clean on touched files.
5. Closing comment on #74 with commit SHA + command evidence.

## Tranche plan

- T0: this slice opened + the ADR-046 addendum + the frozen red test
  committed against unmodified main.
- T1: the two call-site wraps; red→green; full gates; re-freeze.
- T2: docs close-out; issue #74 closed with evidence.

## Non-goals

- No lock inside `_create_worker_cgroup` / `_release_controller_leaf`
  (self-deadlock against the qualified probe; hard constraint).
- No cross-batch or journal-level locking (single-operator discipline).
- No new CLI surface, report field, refusal code, or schema number.
