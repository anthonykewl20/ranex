# SLICE-060 — gate-evaluate presentation dedup

**Status:** open
**Opened:** 2026-08-20
**Priority:** P2 — a mixed FAIL verdict misreports itself: one problem reads
as two in the surface operators act on, and the doubled sentence is the
absence one — the exact wording ADR-020 reserves for work never done.
**ADR:** `docs/adr/ADR-020-cause-is-structure-not-prose.md` (accepted). This
slice is a presentation repair inside that ADR's recorded contract — its
driver "`reason` must stay byte-identical: humans read it and the journal
records it" is the invariant here; the structured-cause renderer it queues
behind BOARD-05 is untouched.
**Issue:** #40

## Contract

`cmd_gate_evaluate`'s FAIL block prints its own partition of the missing
claims (refused / unattributable-absent / absent), then the kernel's recorded
`result.reason`. The reason joins every clause with `"; "`. The existing
guard withheld the reason only when EVERY missing claim was genuinely absent,
so in a mixed verdict — one claim's evidence bound to a different subject
digest, another claim with no evidence at all — the absence sentence printed
twice.

After this slice: the block records each sentence it prints, verbatim, and
drops from the reason only exact clause repeats. Every clause the partition
cannot express still prints. A clause naming a different claim set is not a
repeat and survives. The reason string itself — the recorded diagnosis the
journal and the verdict record carry — is byte-identical before and after.

## Exact owned paths

Product implementation may change only:

- `src/ranex/cli/main.py` (the FAIL presentation block in
  `cmd_gate_evaluate` only)
- `tests/e2e/test_gate_evaluate_mixed_cli.py` (new, frozen at the red
  commit; authored by a fresh-context agent from this spec, not by the
  implementer)
- `tests/integration/test_slice017_native_launcher.py` (`MAIN_PY_SHA256`
  refreshed by the implementer, one comment line added to the pin's history)
- `governance/suite_manifest.json` and
  `tests/e2e/expected/suite-freeze-manifest.out` (the standing close
  ceremony via `ranex suite freeze`, no hand edits)
- `docs/STATE.md`, `README.md`, `docs/slices/` (lifecycle docs)

## Deterministic acceptance gates

1. A mixed stale+absent verdict prints the absence sentence exactly once,
   and prints the stale clause. **Red at the freeze commit.**
   `tests/e2e/test_gate_evaluate_mixed_cli.py::test_mixed_verdict_prints_the_absence_sentence_once`
2. The stale clause survives the dedup in the mixed verdict (guard, green at
   freeze — it must stay green through the fix).
   `tests/e2e/test_gate_evaluate_mixed_cli.py::test_mixed_verdict_still_prints_the_stale_clause`
3. The recorded reason is untouched by presentation: the journal record for
   the mixed verdict carries both clauses, `"; "`-joined, in `_diagnosis`
   order (guard, green at freeze).
   `tests/e2e/test_gate_evaluate_mixed_cli.py::test_recorded_reason_carries_both_clauses_untouched`
4. An all-absent verdict still prints the absence sentence exactly once
   (guard, green at freeze — the case the old guard covered must not
   regress).
   `tests/e2e/test_gate_evaluate_mixed_cli.py::test_all_absent_verdict_prints_the_absence_sentence_once`
5. `MAIN_PY_SHA256` matches the shipped `main.py`.
   `tests/integration/test_slice017_native_launcher.py::test_gate10_production_entrypoint_adr_and_risk_remain_frozen`
6. Full frozen suite, including the suite-freeze golden after the standing
   ceremony, is green.

## Not owned

- `_diagnosis()` in `verdict.py`: reason wording, clause order, the cause
  structure — all recorded diagnosis, all out of scope.
- Evidence admission, projection, `presentation_partition`, and verdict
  semantics.
- The structured cause renderer (BOARD-05) and any cross-claim-set dedup —
  a reason clause whose claim set differs from the printed sentence is out
  of scope by design and survives.
- `tests/e2e/test_gate_evaluate_cli.py`, `test_gate_evaluate_real.py`, and
  the `gate-evaluate-fail.out` golden (all green against the fix; not
  edited).

## Stop conditions

Stop rather than: change a byte of `result.reason` or `_diagnosis()`, weaken
or rewrite a frozen test, dedup clauses by similarity instead of exact
equality, touch a non-owned path, or hand-edit the suite manifest or the
freeze golden outside the `ranex suite freeze` ceremony.

## Verification commands

```text
uv run --frozen pytest -q tests/contract/test_docs_discipline.py
PYTHONPATH=src uv run --frozen pytest -q tests/e2e/test_gate_evaluate_mixed_cli.py
PYTHONPATH=src uv run --frozen pytest -q tests/e2e/test_gate_evaluate_cli.py tests/e2e/test_gate_evaluate_real.py
uv run --frozen pytest -q
```
