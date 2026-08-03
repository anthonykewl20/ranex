# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-04
**Phase:** SLICE-006 built and green except criterion 14, which is blocked on
an owner decision.
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md` (ADR-007).

## Where we stopped

Provisioning works end to end. `ranex deps fetch` derives the lock clean under
pinned inputs and byte-compares it, `deps approve` records the named delta, and
`run` proves derivation, approval and every wheel out of the SHA-256 store
before spawning into a sealed, offline root. The real-world journey
(`tests/e2e/test_gating_real_suite.py`, 14 operator stages against a clone of
this repository) is green: 13 pass, 1 strict xfail, 1 skips on the operator key.
It found four real defects, all fixed and recorded in the slice.

**Criterion 14 is the open miss.** 362 of this suite's tests pass inside the
sealed environment; five fail because they need a git checkout and ADR-005's
materialisation has no `.git`. Relaxing them is refused — `_tracked_by_git`
documents failing closed there as deliberate.

## Next

1. **Owner decides:** should the materialisation be a git repository whose HEAD
   carries the subject tree? It amends ADR-005, so it needs ADR-009. Nothing
   else in SLICE-006 is blocked.
2. Operator setup, one command: `sudo install -m 0755 ~/.local/bin/uv
   /usr/local/bin/uv`. Until then every real-world stage skips loudly.
3. Then close SLICE-006: diff-cover to 100% on the change, mutmut, README.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` and dropped the
  epoch, breaking derivation — measured, not theoretical.
- Dependencies remain trusted computing base: an approved wheel's code runs
  inside the measured command and can choose its exit (ADR-007 s.p. 17-19).
- `ranex-harness` is a local sibling clone; machines without it skip its fork
  tests loudly.
- `approver_id` unauthenticated (`RISK-07`); same-uid key theft (`RISK-06`);
  confinement (`ADR-006`) unbuilt and deliberately deferred.
- The journal detects an edited row but not a removed one.
