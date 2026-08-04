# State

<!-- Rewrite this file. Do not append to it. Keep it at most 50 lines. -->

**Updated:** 2026-08-04
**Phase:** SLICE-006 — every criterion met except 14, which is next.
**Active slice:** `docs/slices/SLICE-006-gating-a-real-test-suite.md`
(ADR-007, and ADR-009 for criterion 14). **No second slice** — criterion 14 is
this slice's remaining work.

## Where we stopped

Provisioning works end to end against real PyPI: `deps fetch` derives the lock
clean under pinned inputs and byte-compares it, `deps approve` records the
named delta, `run` proves derivation, approval and every wheel out of the
SHA-256 store before spawning into a sealed, offline root. Criterion 13 is
done — an approved, hash-correct wheel demonstrably forces a passing verdict,
labelled **not caught**, with a control proving the suite really ran.

Three journeys now drive the real CLI: `test_gating_real_suite.py` (15 stages,
operator path), `test_cold_start_journey.py` (9 stages, a new person from zero
state, which also pins the README against the commands it documents), and the
malicious-wheel demonstration. **Eight defects found this session — every one
by running the real thing, none by unit tests.** MAP §4.6 records why.

Suite 508 passed / 1 skipped / 2 xfailed. `diff-cover` 100% on the change;
mutmut 4673 mutants, 2945 killed — survivors are message text and equivalent
mutants, weak evidence per the recorded convention.

## Next

1. **Criterion 14, against accepted ADR-009:** build the fresh single-commit
   repository inside the materialisation. Measured: the tree hash is unchanged
   (`1d8aa022…`), so the subject digest does not move. Done when all three
   strict `xfail` markers are removed and the gate accepts.
2. Then close SLICE-006 and rerun mutmut.
3. Backlog: turn MAP §4.6 into a gate rule (start with "a skip is absence, not
   success" — a fully skipped suite exits 0 and the gate accepts it today).
   ADR-006/Landlock still proposed and deferred; its `SLICE-005` reference is
   dangling by design. Handbooks and first-delegation unstarted.

## Known limits

- Always `uv run --frozen`. Plain `uv run` rewrote `uv.lock` and dropped the
  epoch, breaking derivation — measured, not theoretical.
- Dependencies are trusted computing base: an approved wheel chooses the exit
  code (ADR-007 s.p. 17-19), demonstrated executably.
- `approver_id` unauthenticated (`RISK-07`); same-uid key theft (`RISK-06`).
- The journal detects an edited row but not a removed one.
