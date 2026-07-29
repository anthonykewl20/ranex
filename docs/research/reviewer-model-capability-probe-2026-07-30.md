# Reviewer-model capability probe

**Date:** 2026-07-30
**Decision status:** observational evidence; no routing decision is made or implied
**Ranex revision probed:** ADR-0013 `v1.3.0` on `bootstrap/pre-upstream`
**Models probed:** `openrouter/tencent/hy3` (high variant), `opencode-go/deepseek-v4-pro`,
`openrouter/xiaomi/mimo-v2.5-pro`
**Independent review of this document:** none yet

## Why this exists

Ranex fixes one static, explainable, release-pinned route per assignment
([ADR-0005](../architecture/decisions/ADR-0005-select-local-static-orchestration-defaults.md),
strengthened by [ADR-0011](../architecture/decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md)).
Substituting that default requires `SUB-ROUTING-001`, whose gate demands a candidate that "wins
repeated holdouts, remains policy bounded, supports hidden evaluation/drift/rollback, cannot
self-activate, and preserves explicit no-fallback assignment semantics."

Two of the twenty-one readiness gates — `READY-HY3-REVIEW-001` and `READY-DEEPSEEK-REVIEW-001` —
name specific reviewer models. Nothing in the corpus records *why* those models, or what evidence
would justify changing them.

This document records one day of observed reviewer behaviour. It is not a holdout, it does not
satisfy any substitution gate, and it authorizes nothing. It exists so that a future routing
decision starts from recorded evidence rather than from impressions.

## Method

Reviewers were given identical adversarial briefs against the same subject, and their claims were
independently verified against the repository by the orchestrator. A claim that could not be
reproduced was discarded regardless of the confidence with which it was stated.

Ground truth was available because the subject had already been audited twice: defects found in
earlier rounds were known, and a later reviewer's ability to find them — or to find drift the
earlier rounds had missed — was checkable.

**This is a probe, not an evaluation.** Sample sizes are one to three per model, conditions were
not held constant, and the briefs were written by the orchestrator whose own framing is a known
contaminant (see Limitations).

## Observed findings

### Findings that survived independent verification

| Finding | Found by | Verified |
|---|---|---|
| Reclaim/fencing ambiguity permitting two live writers on one subject | HY3 | Confirmed against `states.json`: `AssignmentStatus.EXPIRED` is terminal with zero outbound transitions |
| Global terminal-path invariant silently made skippable; 1 of 31 axes benefited | DeepSeek | Confirmed by diff; the benefiting axis was added in the same commit |
| Obligation weakened from action to assertion (`Remove` → `are absent`) | DeepSeek | Confirmed against research `:2279-2281` |
| Rebranding-specific legal gate dropped from a preservation clause | DeepSeek | Confirmed against research `:1616-1617` |
| Residual drift in four rows no earlier round had sampled | HY3 | Confirmed; one silently narrowed a stated permission |
| Two normative edits absent from the revision history | HY3 | Confirmed by catalog diff |
| Fidelity pinning covered 24 of 65 rows | HY3 | Confirmed by counting pins |
| Unsupported scope qualifier surviving three repair rounds (`every`) | MiMo | Confirmed: absent from research `:1902` |

### Claims that did not survive

| Claim | Made by | Outcome |
|---|---|---|
| The fidelity pin is an exact-string blacklist and therefore weak | DeepSeek | **Refuted.** It is an equality allowlist against corrected text; a paraphrase fails closed. Settled by reading `validate_contracts.py:1356-1361` |
| The generated tree was unrecoverable | DeepSeek | **Refuted.** The publisher is transactional with rollback. The claim originated in the orchestrator's own prompt and was returned as a finding |
| The prototype tree could not be safely regenerated | DeepSeek | **Refuted** by the same mechanism |

## Behavioural observations

**HY3 (high variant).** Produced the two findings nothing else approached — the reclaim/fencing
hole and the silent invariant relaxation. Performs systematic passes when asked and finds drift in
rows earlier sampling missed. Verbose (2,000–2,800 lines) and slow. Read a mechanism correctly
that another reviewer inverted. Distinguishes "supportable interpretation" from "unsupported
addition" rather than collapsing both into a defect.

**MiMo-V2.5-Pro.** Performed a full 65-row systematic pass unprompted and found the one remaining
drift after three repair rounds. Verified a coverage claim structurally — tracing key-set checks
to six line numbers and explaining why deletion fails — rather than accepting the stated number.
Concise (226 lines). Applied the stricter reading on a disputed row: a qualifier absent from the
*cited* line is drift, even where corroborating lines exist elsewhere.

**DeepSeek-V4-Pro.** Found real defects in round one, including two that materially weakened
obligations. Also: constructed a malformed absolute path and lost a run to auto-rejection; ran
five hours producing zero bytes on another; sampled where a systematic pass was required; and
inverted the reading of a check mechanism. Useful as a third opinion that forces a resolvable
disagreement.

## Operational observations

**Concurrency has a cliff, not a slope.** Three concurrent high-variant runs against one provider
produced *zero* output across all three for 24–52 minutes, while a run on a different provider
completed in seven. Throughput did not degrade gracefully; it stopped. Provider diversity matters
for availability, not only for cost.

**Silent hangs are indistinguishable from slow work.** One run produced zero bytes for five hours
before anyone noticed. Nothing signalled the difference between "reasoning" and "dead."

## What this suggests, and what it does not

**Suggests** — different reviewer work has different requirements. Deep adversarial reading of an
unfamiliar seam, systematic full-corpus comparison, and tiebreak second opinions are distinct
tasks, and observed performance differed by task rather than uniformly by model.

**Does not suggest** any model is better. One to three samples under unequal conditions cannot
support that, and this probe was not designed to.

**Does not authorize** a routing change. `SUB-ROUTING-001` requires repeated equal-budget
holdouts, hidden evaluation, drift alarms, rollback, and human activation. None of that happened
here.

## Applicability to Ranex

Three properties of this probe are reusable inside the product rather than merely about it:

1. **A finding must be checkable or it is an opinion.** Every claim that survived was verifiable
   at `path:line`. Every claim that dissolved was framing. This is already partially enforced —
   `review-observation-v1.schema.json` requires `evidence_refs` per finding — but `minItems` is
   unset, so an empty array satisfies the requirement.
2. **Reviewer disagreement is more informative than reviewer consensus, provided it is
   resolvable.** Two reviewers contradicted each other on the pin mechanism; three lines of code
   settled it. A gate that collects agreeing signatures proves less than one that surfaces a
   disagreement with a test attached.
3. **Prompt contamination defeats independent review.** An assumption placed in a brief was
   returned as a finding with a citation. `review-request-v1.schema.json` already carries
   `blind_context_manifest_digest` and `independence-evaluation-v1.schema.json` carries
   `blind_context_satisfied` — the mechanism exists; this probe is evidence for why it matters.

## Addendum — session-warmth latency probe

A separate probe on the same day asked whether Hermes' Nous keepalive removes a capability Ranex
must rebuild. Four conditions, 20 runs each, interleaved, on `openai-codex`:

| Condition | n | median | p95 | runs > 6s |
|---|---:|---:|---:|---:|
| `safe-mode` (all customisation off) | 20 | 4.01 s | 5.22 s | **0** |
| `--ignore-rules` | 20 | 4.13 s | 5.60 s | 1 |
| warm | 20 | 4.21 s | 7.16 s | 5 |
| cold (caches cleared) | 20 | 4.62 s | 9.70 s | 3 |

**Robust finding:** customisation, not cache state, drives the latency tail. Medians differ by
0.6 s across all four conditions, but `safe-mode` never exceeded 6 s in 20 runs while warm
sessions with full skills and persona loaded did so five times, peaking at 10.7 s. The ~11.6 k
tokens of skills injection is a latency-variance cost, not only a token cost.

**Implication for de-commercialization:** session warmth was not the mechanism. Cold and warm
medians differ by 0.4 s. Deleting the Nous keepalive does not remove a capability worth
rebuilding.

**Discarded finding:** the harness printed a verdict on a `cold − warm` gap of `+2.54 s` at p95.
That is not trustworthy. At n=20, p95 is effectively the second-slowest observation, and warm's
own p95 (7.16 s) sits far above its median (4.21 s) — the tail is fat in both conditions. The
decision rule was applied to a statistic that is unstable at this sample size. Recorded as a
design error in the harness, not as a result.

The p95 question remains `EFFECTIVENESS_UNKNOWN`. Settling it needs n≈100 and time-to-first-token
instrumentation rather than wall-clock timing.

## Limitations

- One to three samples per model. No repetition, no holdout, no hidden evaluation.
- Conditions were not held constant: one model ran without provider contention while others
  queued.
- All briefs were authored by the orchestrator, whose framing demonstrably contaminated at least
  one result.
- The orchestrator also verified the results. There was no independent check of the verification.
- Ground truth came from prior audit rounds, not from an authored answer key.
- No cost or token accounting was captured.
