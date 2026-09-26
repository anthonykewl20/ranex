# SLICE-094 — the antislop claim: a test-integrity census

**Status:** done

DIRECT 004/009 (P2), science report §3.3 + §8 proposal B, wave-1 promotion
ruling. The C3 anti-slop structural gate, shipped as the third SARIF-family
claim (`antislop-sarif-2.1.0`, ADR-063): an AST scanner that censuses every
test's effective-assert count and greps the structural slop shapes, reduced
at seam B against per-test expectations frozen from the approved tree at
seam C. `evaluate()`, `verdict.py` and the evidence envelope untouched; no
new runtime dependencies (stdlib `ast` only); the scan family's discipline
inherited whole (canonical argv, no script operand, digest-bound manifest,
absence blocks, no self-approval — and no acceptance vocabulary at all,
because a slop shape is never something review waves through).

## Shape

- Scanner `src/ranex/foundation/antislop.py` (`ranex antislop`, exit 0
  through findings): four `error` rules — constant-truth asserts
  (`assert True`, `assert not False`), pass-only bodies, snapshot-blind
  updates (the flag/kwarg spellings), input-range narrowing
  (`max_examples` below the floor, point `integers()` ranges) — plus one
  `none`-level census entry per test (`<id> effective_asserts=<n>`),
  assertion-equivalent calls counted (`pytest.raises`, unittest `assert*`),
  class-qualified IDs, #97 fingerprints over the subject's bytes.
- Expectations manifest `{scope, tests}` (`governance/antislop/…` for
  whoever wires a self-gate): canonical JSON, seam-C trust root through
  `claim_expectations`' reporter dispatch; loader/refusals in
  `src/ranex/foundation/antislop_results.py` with the seam-B reduction to
  the closed suite summary. Count below frozen ⇒ the test fails; census
  absence ⇒ `missing`; structural findings fail file + named test even
  when new; unnamed tests are `extra`, never blocked.
- Freeze (`suite freeze --results-reporter antislop-sarif-2.1.0`): freezes
  exactly what the run observed — no narrowing flags exist, and a tree
  already carrying violations is refused.
- Wiring: `slice_gate_loader` (known reporters, canonical argv, required
  manifest), `cmd_run`/`cmd_gate_evaluate` manifest dispatch and artifact
  readers, `task judge` via `claim_expectations`, delegation refuses the
  family as it refuses scan claims.

## Proof (#95 protocol)

The science bank (SLOP a/b/c + KG 01–06) plus the two wave-1 plants
(snapshot-blind-update, input-range-narrowing), replayed live as in-place
edits of the pinned `benjaminp/six` tree against a freeze of the pristine
tree: 3× identical run→evaluate cycles per arm, digest-tamper and
freeze-refusal negative controls, the detector-bug regression
(`test_print_exceptions`, pytest.raises-only, frozen count ≥ 1) checked on
the real subject. Receipts under `tools/dogfood/audits/2026-09-25-antislop/`;
the same bank replayed in the unit suite
(`test_antislop_scanner.py`, `test_antislop_results.py`) and the claim
surface pinned in `tests/contract/test_antislop_claim.py`.

## Out of scope

This repo's own landing gate (wiring `governance/antislop/expectations.json`
against `tests/` is the owner's standing-refreeze burden to take on
deliberately), the BASE freeze file (P1), the differential reporter (P3),
and any model judgment anywhere near the scanner.
