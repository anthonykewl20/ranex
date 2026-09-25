# ADR-063 — the BASE freeze and the promotion gate

**Status:** accepted
**Date:** 2026-09-25
**Decision-makers:** repo owner (captain DIRECT 004/008; firstmate P1 spec)
**Issue:** oracle-science report §5/§8 SLICE-D — "a promotion gate that
refuses any future 'improvement' claim not citing a freeze id and paired
MARGINALs"

## Context and Problem Statement

The oracle-science scout report (2026-09-24/25) measured BASE — the current
acceptance physics — on two pinned subjects and graded five candidate
treatments as paired MARGINAL deltas against it, preregistered before any
treatment data. That protocol is only scientific if the instrument it
grades against is *frozen*: a self-evolving policy (handbook, catalog,
harness, dogfood driver, scored proposal) that can regenerate its own
baseline can grade itself, and "improvement" degenerates to assertion. The
report's own rejected candidate is the cautionary tale: L3's preregistered
calibration constant τ=0.80 exceeded the honestly measured kill-rate (0.60)
and would have false-FAILed every honest suite — a threshold with no
measured origin is a bug wearing a gavel.

The problem: where does the frozen instrument live, what may bind it, and
what refuses an improvement claim that does not cite it?

## Decision Drivers

- ADR-016 (measure before learning): promotion is evidence-bound, stale-base
  checked and monotonic; this ADR is its frozen-instrument half.
- ADR-060 rule 2: a new policy file is a trust root or it is a hole. The
  freeze decides gradability, so it is read committed at the ref being
  judged, through the same `committed_trust_root` discipline as the catalog.
- Gauge non-contamination (report §5): the freeze is *read* by promotion
  judgment and *written* by nothing a treatment can reach. Freeze artifacts
  are minted by promote ships (captain DIRECT 008 FINAL), never by the
  graded run.
- The kernel does not move: no new verdict path, no model in any decision,
  `verdict.py`/`KERNEL_DIGEST` untouched. A promotion decision is not a
  gate verdict over a subject tree; it is a refusal of an unevidenced
  *claim about* a treatment.
- No new runtime dependency.

## Decision

### 1. `governance/calibration/` is a committed, append-only gauge class

`governance/calibration/base-freeze-vN.json` (schema `ranex-base-freeze-v1`,
canonical JSON bytes, closed key set, additive versioning — a v2 is a new
file and a new validator, never a widening of v1) binds, per the report's
§5 smallest durable format:

- kernel identity: `kernel_commit` (where BASE was measured) and
  `kernel_digest` (sha256 of `verdict.py` bytes — checkable at any future
  HEAD without the commit object);
- `vendored_src_tree` (the F-003 lab identity) and per-subject pins:
  six@1.17.0's commit, its frozen suite-manifest digest and the control
  bank digest; the ranex-handbook oracle subject;
- `reference_metrics`: the measured BASE numbers (raw and honest false-PASS,
  KG false-FAIL, suite kill rates, cycle seconds, and the τ bound
  `tau_max_honest_kill_rate`), each citable as the axis
  `<subject>.<metric>`;
- `receipts_digest` (the scout's receipts appendix) and
  `source_prereg_digest` (the frozen analysis plan), so every number in the
  freeze traces to durable evidence;
- `mint_receipts_digest` and `journal_head_at_freeze`: the mint's own
  derivation receipt and the mint lab's verified journal head.

Two values the scout's discarded lab did not retain (its six manifest bytes
and journal head) are re-derived at mint by a live governed lab of the same
construction (200 frozen IDs, 15 operator-approved platform skips, three
byte-identical derivations), and the re-derivation receipt is what
`mint_receipts_digest` binds. The reference metrics remain the scout's
measurements, cited by digest, never re-measured.

### 2. `ranex promotion evaluate` judges citation discipline

`--claim` names a claim document (schema `ranex-promotion-claim-v1`:
claim_id, treatment, base_freeze citation, marginal deltas, optional τ
entries, evidence receipts digest). The command reads the claim from disk as
it stands — its job is to judge what was claimed — and the cited freeze
committed at `--ref` (default HEAD) through `committed_trust_root`: an
uncommitted gauge edit is an operational refusal, the same seam-C pinning an
edited catalog gets. ADMITTED requires every rule below; anything less is
REFUSED with a named cause, canonical decision bytes, exit 1:

- **citation**: a safe freeze id the committed calibration directory
  answers (`no-freeze-citation`, `freeze-mismatch`,
  `freeze-malformed`);
- **marginals**: non-empty paired deltas, each on an axis the freeze names
  (`no-marginal-deltas`, `unknown-axis`), each baseline *equal to the
  freeze's own number* (`unpaired-baseline` — the invented-baseline
  refusal), each reconciling treatment − base = delta (`delta-arithmetic`);
- **τ**: any calibration threshold in the claim must equal the freeze's
  derived number for its cited axis (`tau-not-derived-from-freeze`). L3
  stays rejected; nothing from it is encoded except its headstone;
- **evidence**: a receipts digest binding the claimed measurements
  (`no-evidence-binding`).

The decision is pure over (claim, freeze bytes): identical inputs yield
byte-identical canonical decisions, `--json` emits them, and the module
(`governed_execution/promotion_gate.py`) imports no signing, admission or
journal code — a promotion decision is never evidence and never a verdict.

### 3. What this ADR refuses

- No promotion decision writes anything: no journal row, no verdict, no
  freeze. Judging a claim and recording a governance event are different
  powers, and the second is not granted here.
- The freeze is never a default gauge: a claim citing no freeze is refused
  on citation grounds, and the freeze-dependent checks are skipped, not
  answered from nothing.
- A τ constant anywhere in the promotion path is a defect; the only τ this
  package answers is `derived_tau(freeze, axis)`, which raises on any axis
  the freeze does not carry.

## Alternatives Considered

- **A kernel claim family** (`Claim` gains promotion semantics): refused —
  it would move `verdict.py` for a judgment that is not about a subject
  tree, and ADR-060 keeps new observation kinds out of the kernel.
- **Dogfood-only tooling** (seam E measurement): refused — measurement
  never decides; the whole point is a *refusal* surface, so it ships as a
  command with committed-gauge discipline instead.
- **Recording τ=0.80 as data with a warning**: refused — L3's rejection is
  unconditional; the gate refuses the constant rather than flagging it.

## Consequences

- Every future promotion claim in this repository must cite a freeze id and
  carry paired marginals on that freeze's axes or it is REFUSED — the
  report's §8 SLICE-D contract, now executable.
- Minting `base-freeze-v2` is a deliberate act: new file, new validator, an
  ADR or slice that says why, and a fresh mint receipt. Rewriting v1 is
  refused by the ordinary committed-bytes discipline and made visible by
  the receipt digest binding (`tests/contract/test_base_freeze.py`).
- The freeze's reference metrics carry the scout's external-validity bound
  (the mutant bank is a census of the operator's defect model, not a random
  defect sample); quoting a freeze number inherits that bound.

## Evidence

Mint + proof executed 2026-09-25 on this host against the installed kernel:
`tools/dogfood/audits/2026-09-25-base-freeze/` (instrument derivation ×3
byte-identical; gate negative controls — no-freeze-citation, constant-τ,
invented-baseline, uncommitted-gauge-tamper — all refused; the report's own
C4 composition marginal ADMITTED against v1; decision bytes identical ×3;
`tests/contract/test_kernel_unchanged.py` passing). Scout evidence:
firstmate data `ranex-kernel-oracle-science/report.md` §2/§3/§5 with
`receipts-appendix.json` (digest bound inside the freeze as
`receipts_digest`).
