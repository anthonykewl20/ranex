# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-04
**Phase:** SLICE-006 — every criterion met including 14; close-out is next.
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md`
(ADR-007, and ADR-009 for criterion 14). **No second slice.**

## Where we stopped

Criterion 14 is met: `materialise_subject` builds a fresh single-commit
repository around the verified tree (ADR-009 — fixed identity, epoch
timestamp, no reflog, refusal unless the sample's `HEAD^{tree}` equals the
governed ref's tree). All three strict `xfail` markers are removed; stages
08b and cold-start 9 pass against real PyPI, and inside the sealed sample
448 tests pass, the recorded exit is 0, and `gate evaluate` answers PASS —
Ranex gates a clone of Ranex through the unchanged catalog command.

A ninth journey defect was found and fixed landing this: the cold-start
journey re-entered itself inside the sample, because its environment guard
cannot survive an environment built from empty. It now recognises the
sample by its deterministic synthetic commit identity and skips loudly.

Suite 518 passed / 1 skipped (stage 12, on the operator's signing key).
`diff-cover` 100% on the criterion-14 change. mutmut not yet rerun since
the change — that is part of close-out, not yet done.

## Next

1. **Close SLICE-006:** rerun `uv run --frozen mutmut run` against the new
   materialisation code, confirm criterion 15 still holds on the full slice
   diff, then archive the slice to `docs/slices/done/`.
2. Stage 12 (self-gate with the operator's own key and populated store)
   skips loudly by name until the operator provides both.
3. Backlog: turn MAP §4.6 into a gate rule (start with "a skip is absence,
   not success"). ADR-006/Landlock still proposed and deferred; its
   `SLICE-005` reference is dangling by design. Handbooks and
   first-delegation unstarted.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` and dropped the
  epoch, breaking derivation — measured, not theoretical.
- Dependencies are trusted computing base: an approved wheel chooses the exit
  code (ADR-007 s.p. 17-19), demonstrated executably.
- The sample repository is writable by the observed command (ADR-009 s.p. 6)
  — vandalism dies with it; the fingerprint check still refuses edits.
- `approver_id` unauthenticated (`RISK-07`); same-uid key theft (`RISK-06`).
- The journal detects an edited row but not a removed one.
