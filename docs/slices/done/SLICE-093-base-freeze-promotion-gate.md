# SLICE-093 — The BASE freeze and the promotion gate (P1)

**Status:** done
**Origin:** oracle-science report §5/§8 SLICE-D; captain DIRECT 004+009;
ADR-063.

## Contract

"Improved" is a measurement claim, and a measurement claim is gradable only
against a frozen instrument. This slice lands that instrument and the gate
that enforces citing it:

- `governance/calibration/base-freeze-v1.json` — the committed, canonical-
  bytes BASE freeze per the report's §5 smallest durable format: kernel
  identity (`kernel_commit` 638f7d8 where BASE was measured +
  `kernel_digest` = sha256 of `verdict.py`, byte-identical from that commit
  to HEAD), `vendored_src_tree`, subject pins (six@1.17.0 @ ebd9b3af with
  its suite-manifest and control-bank digests; ranex-handbook), the
  measured `reference_metrics` (six: raw false-PASS 0.625 / honest 0.025 /
  KG false-FAIL 0.0 / behavior-changing kill 0.875 / cycle 1.5 s / τ bound
  0.60; ranex-handbook: false-PASS 0.25, kill 0.75), and the evidence
  bindings (scout `receipts_digest`, `source_prereg_digest`, mint
  `mint_receipts_digest`, `journal_head_at_freeze`).
- `governed_execution/promotion_gate.py` — the deterministic judge. A
  promotion claim (schema `ranex-promotion-claim-v1`) is ADMITTED only
  with: a safe freeze citation the committed calibration directory answers;
  non-empty paired marginal deltas on axes that freeze names, each baseline
  equal to the freeze's own number, each delta reconciling; any τ equal to
  the freeze's derived number for its axis (L3 stays rejected — its
  τ=0.80-vs-measured-0.60 failure is the refused cause, not an option);
  and an evidence receipts digest. Pure over (claim, freeze bytes);
  imports no signing/admission/journal code; never evidence, never a
  verdict.
- `ranex promotion evaluate --claim C [--ref HEAD] [--json]` — the command.
  The claim is read from disk as it stands; the cited freeze is read
  committed at the ref through `committed_trust_root` (seam C: an
  uncommitted gauge edit is an operational refusal, exactly like an edited
  catalog). REFUSED prints named causes (`no-freeze-citation`,
  `freeze-mismatch`, `freeze-malformed`, `no-marginal-deltas`,
  `unknown-axis`, `unpaired-baseline`, `delta-arithmetic`,
  `tau-not-derived-from-freeze`, `no-evidence-binding`, `claim-schema`,
  `malformed-delta`) and exits 1; ADMITTED exits 0; `--json` emits the
  canonical decision record.
- Two values the scout's discarded lab did not retain (its six manifest
  bytes and journal head) are re-derived at mint by a live governed lab of
  the same construction and bound through the mint receipt — the freeze
  never silently substitutes this ship's measurements for the scout's; the
  reference metrics stay the report's, cited by digest.

Kernel untouched: `verdict.py`/`KERNEL_DIGEST` do not move, `evaluate()`
purity unchanged, no new runtime dependency, no new signing domain.

## Non-goals

C3 anti-slop scanner (P2), C4 differential reporter (P3), any L3
kill-rate calibration (rejected on its own data), any change to
`evaluate()` or the frozen probes, no journal/verdict writes from promotion
decisions.

## Validation

Red-first unit tests (`tests/unit/test_promotion_gate.py`, 26 rows),
command-surface integration tests (`tests/integration/test_promotion_command.py`,
10 rows incl. the tamper/uncommitted-gauge refusals), and
`tests/contract/test_base_freeze.py` pinning the committed gauge (canonical
bytes, kernel-digest binding, receipt-digest binding, standing negative and
positive controls through the real CLI).

Real-data receipt at `tools/dogfood/audits/2026-09-25-base-freeze/`
(`base_freeze_proof.py`): instrument derivation on pinned six@1.17.0 (three
freezes byte-identical, cycle PASS, journal chain verified), the
re-derivation equals the frozen manifest digest, committed-freeze and
kernel checks, the four gate negative controls (uncited, constant τ,
invented baseline, tampered gauge), the positive control — the report's own
C4 composition marginal, paired on named axes against v1, ADMITTED — and
decision bytes identical ×3.
