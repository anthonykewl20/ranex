# Agent report artifacts — 2026-07-30

Raw output from independent model runs against this repository. Preserved because
these were produced in a session-scoped temporary directory and would otherwise
have been lost.

**These are inputs, not conclusions.** Nothing here carries authority. A finding
in these files is a claim by a model, and models are susceptible to assumption in
the same way humans are. The `Verification` column below records what was
independently reproduced by the orchestrator against `path:line` evidence and
what was not. Unverified rows must be treated as unverified.

## Reports

| File | Model | Subject | Bytes | Verification |
|---|---|---|---|---|
| `kernel-hy3.md` | `openrouter/tencent/hy3` high | Adversarial audit of the kernel R&D tracer | 93,167 | Top findings reproduced at cited lines. **Its BLOCKER F1 was later disproved** — see Corrections |
| `kernel-codex.md` | Codex `gpt-5.6-sol` | Independent code review, same kernel | 227,935 | Convergent findings reproduced. **Its BLOCKER 9 was overstated** — see Corrections |
| `grok-kernel.md` | `openrouter/x-ai/grok-4.5` (default effort) | Same brief as `kernel-hy3.md`, run as a graded probe | 36,252 | Found every ground-truth finding; its §8.3 discovery independently verified verbatim |
| `verify13-mimo.md` | `mimo-v2.5-pro` | Full-row fidelity audit of ADR-0013 v1.4.0 | 10,595 | Row counts and the single-change claim spot-checked; verdict accepted |
| `rigor-hy3.md` | `openrouter/tencent/hy3` high | Review-schema rigour: how a worthless finding validates | 121,926 | Both suspected defects confirmed at source; empty-instance claim reproduced |
| `rungraph-hy3.md` | `openrouter/tencent/hy3` high | Adversarial review of the run-graph visualization proposal | 333,872 | Blocking owner decision and the `elkjs` dual-licence finding independently verified |
| `stack-hy3.md` | `openrouter/tencent/hy3` high | Full technology-stack derivation and classification | 123,009 | Its licensing-manifest finding verified: zero entries exist. Drove ADR-0014 v1.1.0 |
| `priorart-A.md` | Codex | Prior art: findings, controls, provenance, tamper-evident logs | 325,077 | RFC 9943 existence verified; hash-chain truncation weakness reproduced in code |
| `priorart-B.md` | Codex | Prior art: deterministic replay, journal/snapshot agreement, crash testing | 477,289 | Not yet line-verified beyond the four-controls answer |
| `priorart-C.md` | `openrouter/x-ai/grok-4.5` (default effort) | Prior art: policy-as-code, architecture fitness, doc traceability | 176,723 | Not yet independently verified |
| `priorart-D.md` | `openrouter/tencent/hy3` high | Adversarial audit of RFC-0003's first draft | 30,634 | `cog --check` verified by execution; `AGENTS.md` adoption verified at source |
| `variant-*.md` | `openrouter/x-ai/grok-4.5` | Reasoning-effort cost comparison on a fixed tiny brief | small | Cost measured from the OpenRouter credits endpoint |

## Corrections — claims that did not survive

Recorded because a report that was wrong is more instructive than one that was
right, and because these were relayed before being checked.

1. **`kernel-hy3.md` F1 (BLOCKER) is wrong.** It claimed the state-authority
   principle is "declared nowhere." `grok-kernel.md` F-003 found
   `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §8.3, which
   declares a *dual* model: the current row is the operational read source, the
   ordered journal is the replay and audit oracle, snapshots never replace the
   journal, and **a current-row/journal mismatch is corruption that blocks
   advancement**. Verified verbatim. The defect is therefore not an undeclared
   inference — the code **violates a declared obligation** by implementing half of
   §8.3 and omitting the mismatch gate entirely. Four independent readers
   (HY3, Codex, a prior session, and the orchestrator) concluded "declared
   nowhere"; all four were wrong.
2. **`kernel-codex.md` finding 9 was overstated as a BLOCKER.** Its scenario
   required `exit_code=False` and `artifact_verified="yes"` reaching a decision.
   `EvidenceRecord.__post_init__` already rejects both by type. The finding
   survives only for duck-typed objects bypassing the dataclass — real, but not a
   BLOCKER.
3. **A grep suggested five reports contained rate-limit evidence.** Reading the
   matched lines showed the only hit was `429` inside a SHA-256 hash. No report
   contains rate-limit evidence. Recorded because the false positive agreed with
   a hypothesis under test, which is when confirmation is most dangerous.

## Method notes affecting how these should be read

- **Briefs withheld the orchestrator's own conclusions** to avoid contamination,
  following the prior probe's finding that a planted assumption returns as a
  finding. Where a model independently reached a withheld conclusion, that is
  corroboration; where it did not, that is informative about the conclusion.
- **`grok-kernel.md` and `priorart-C.md` ran at default reasoning effort**, not
  `--variant high`, while every HY3 run used `high`. The comparison was therefore
  tilted against Grok.
- **Report size is not quality.** `grok-kernel.md` is a quarter the length of
  `kernel-hy3.md` on the identical brief and missed none of its findings, while
  adding an executed exploit and the §8.3 discovery.
- **One model executed rather than reasoned.** `grok-kernel.md` F-001 forged the
  SQLite snapshot and called `load()`, which returned the forged terminal state.
  That is empirical proof; the others reached the same conclusion analytically.
