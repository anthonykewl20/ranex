# ADR-016 — measure before learning

**Status:** accepted
**Date:** 2026-08-09 (accepted, owner; proposed 2026-08-08)
**Decision-makers:** repo owner
**Slice:** `n/a — future measurement-local M0/F1..F4 are parked behind ADR-017 P0; no measurement slice is next`

**Disposition:** accepted 2026-08-09 (owner). This ADR sets the source-backed, prototype-gated measurement design only; measurement slices are future work. It does **not** block ADR-014 — there is no dependency between them.

## Context and Problem Statement
Ranex needs evidence to grade revisions of handbooks, rules, processes, workflows, models, skills, and their harnesses. MAP §11.3 must say that a frozen target is an outcome instrument, not a fixed treatment: every run may record an observation, but only a preregistered controlled paired trial produces a comparative grade. Candidate proposals are untrusted and never authorization. This ADR defines an accepted source-backed design only; it claims no implementation.

## Decision Drivers
- Preserve the kernel/model wall and leave `evaluate()` unchanged.
- Bind claims to frozen subjects, target outcomes, treatments, and fault evidence.
- Make ordinary monitoring useful without allowing it to grade.
- Make promotion owner-authorized, stale-base checked, monotonic, and reversible.

## Prior art
Searched: GitHub REST repository/code searches; `git ls-remote`; pinned clones; opensrc cache; and independent reviewer-hy3 validation. These methods were used across provenance, exact statistics, rollout analysis, trial state, and anti-rollback implementations.
Searched: targeted GitHub, CRAN, Julia, Java, Go, and C++ searches for exact paired-binary McNemar power/sample-size code; no mature permissive implementation was found.
- [in-toto provenance](https://github.com/in-toto/attestation/blob/df02077bf97218a8860a5c534eff1f1381f56984/go/predicates/provenance/v1/provenance.go). Tests are upstream `go/predicates/provenance/v1/provenance_test.go`. Adopt validation and field taxonomy only.
  License: Apache-2.0.
  Weakness: generated/protobuf coupling.
  Vendored: `docs/adr/prior-art/ADR-016/in-toto-provenance.go` blob:fede80504522ac8b619aa354e0eafe3702198389
- [SciPy binomial test](https://github.com/scipy/scipy/blob/44e4ebaac992fde33f04638b99629d23973cb9b2/scipy/stats/_binomtest.py) (v1.13.1). Tests are upstream `scipy/stats/tests/test_morestats.py` binomtest vectors. Adopt exact binomial and Clopper-Pearson behavior, not the dependency.
  License: BSD-3-Clause.
  Weakness: numerical solver and distribution coupling.
  Vendored: `docs/adr/prior-art/ADR-016/scipy-binomtest.py` blob:bdf21117383374e730ab052fcbb0b5b7fca029c1
- [statsmodels contingency tables](https://github.com/statsmodels/statsmodels/blob/40e6a84d26ac74623c6b94b718f0987ef0351c53/statsmodels/stats/contingency_tables.py) (v0.14.6). Tests are upstream `statsmodels/stats/tests/test_contingency_tables.py` McNemar cases. Adopt the exact McNemar algorithm and derive its R reference result from those upstream test vectors; do not adopt the dependency.
  License: BSD-3-Clause.
  Weakness: general table and floating-point/statistical-library coupling.
  Vendored: `docs/adr/prior-art/ADR-016/statsmodels-contingency-tables.py` blob:d67da2aa8014dc6d9b825d6288d431449dd159ad
- [Argo Rollouts analysis types](https://github.com/argoproj/argo-rollouts/blob/b6bd3bcf8f60d717a98763d26acc983db7f97cb0/pkg/apis/rollouts/v1alpha1/analysis_types.go) (v1.9.1). Tests are upstream analysis API tests for phase values and limits. Adopt Successful/Failed/Inconclusive/Error and separate limits only; do not claim worst-status propagation from this file.
  License: Apache-2.0.
  Weakness: this file does not establish aggregate propagation semantics.
  Vendored: `docs/adr/prior-art/ADR-016/argo-analysis-types.go` blob:6997aa711bb669fb3dc8a7a10f278139e40d8dc3
- [Optuna trial state](https://github.com/optuna/optuna/blob/4db42e31c24b200e52595df9d4c00e2cdeefea2b/optuna/trial/_state.py) (v4.9.0). Tests are upstream trial-state tests for enum values and completion. Adopt the state enum and terminal predicate only; the Ranex journal supplies immutability.
  License: MIT.
  Weakness: state alone provides no journal or authorization.
  Vendored: `docs/adr/prior-art/ADR-016/optuna-trial-state.py` blob:492153405f1a3753854aac7ca8cac5ebe83bc8a0
- [TUF trusted metadata set](https://github.com/theupdateframework/python-tuf/blob/353bdb767db56fd4667c9bcf56b710d50fdc2ac0/tuf/ngclient/_internal/trusted_metadata_set.py) (v7.0.0). Tests are upstream `tests/test_trusted_metadata_set.py` rollback cases. Adopt monotonic anti-rollback checks.
  License: Apache-2.0 OR MIT.
  Weakness: TUF roles and signatures are too heavy for this boundary.
  Vendored: `docs/adr/prior-art/ADR-016/tuf-trusted-metadata-set.py` blob:689eef01de665280434e4c3d8ccdc63f4431b67b
Rejected: [Prime Agent](https://github.com/PrimeIntellect-ai/prime-agent) is recent and model rationale or direct state mutation is not independent proof of an outcome.
Rejected: [DSPy](https://github.com/stanfordnlp/dspy) and [GEPA](https://github.com/gepa-ai/gepa) make candidate generation useful, but have no independent promotion proof and the reviewed DSPy release has a direct orchestration-test gap.
Rejected: [GrowthBook](https://github.com/growthbook/growthbook) combines FNV hashing with a mixed enterprise boundary; its gate behavior is redundant here.
Rejected: [PlanOut](https://github.com/facebookarchive/planout) is archived and carries SHA-1 behavior; it is a reference pattern only.
Rejected: [Hydra](https://github.com/facebookresearch/hydra) has a capture pattern, but that pattern is redundant with the Ranex resolver.
Rejected: [Helm](https://github.com/helm/helm) offers a forward-append rollback reference, but the exact property is thinly tested.
Rejected: [pyDOE3](https://github.com/relf/pyDOE3) is deferred for a later multi-factor design; first scope is one binary candidate.
Rejected: [exact2x2](https://github.com/cran/exact2x2) and [pwrss](https://github.com/metinbulus/pwrss) implement paired-proportion power, but both are GPL-3 and cannot enter this MIT tree.
Rejected: incompatible [Unleash](https://github.com/Unleash/unleash) and [Flipt](https://github.com/flipt-io/flipt) are excluded for license reasons.

## Considered Options
- Treat every run as a grade: rejected because monitoring lacks a counterfactual and invites post-hoc treatment changes.
- Import an experiment platform: rejected because it adds dependencies and authorization surfaces without proving Ranex integration.
- Adopt the separate frozen corpus, resolved treatment, observation, grade, and promotion boundaries below: selected.

## Decision Outcome
Define a frozen `TargetCorpus` and a fully resolved `TreatmentManifest` with external, internal, and resolved dependencies plus model, harness, handbook, rules, process, workflow, prompt, skills, tools, budgets, and provider metadata. One Python authority hashes both before dispatch; an alias is non-reproducible and ineligible unless the provider exposes an immutable concrete version that the owner approves.

`ExperimentObservation` binds experiment, pair, arm, subject, target, treatment, and outcome digests plus fault classification. It lives in a separate experiment record namespace; an ordinary observation structurally cannot grade. A paired A/B trial uses the same frozen corpus, deterministic counterbalanced order, and a fresh worktree/session. Shared provider correlation is a named limit.

Trial lifecycle adapts Optuna's explicit state and terminal predicate, without adaptive pruning: `WAITING` → `RUNNING` → `COMPLETE` or `VOID`; no terminal record mutates.

The first scope has exactly one candidate and one binary PASS/FAIL primary endpoint. Preregister fixed corpus N, alpha, practical effect threshold, minimum discordant count, and fault policy. Use exact McNemar on discordant pairs and an exact Clopper-Pearson interval for discordant-win probability. No Holm or multiplicity correction; secondary metrics are descriptive and ineligible. Exact power/sample-size design is UNVERIFIED because no permissive mature exact McNemar power code was found.

Let `wins` mean candidate PASS/control FAIL and `losses` the reverse. `SUPERIOR` requires `wins > losses`, `wins + losses` at least the registered minimum, exact two-sided `p <= alpha`, and `(wins - losses) / N` at least the registered practical margin; `INFERIOR` is symmetric, `FAULT` means the grader or registered fault limit failed, and every other complete result is `INCONCLUSIVE`. The exact interval is reported, never substituted for those frozen rules.

### Consequences
- Corpus freezes before proposal; a candidate cannot mutate it. Visible corpus proves conformance to that corpus, not generalization.
- Treatment-attributable failures remain outcomes. Only preclassified infrastructure/checker faults void pairs and are counted; unknown classification blocks and is inconclusive.
- Grade is `SUPERIOR`, `INFERIOR`, `INCONCLUSIVE`, or `FAULT`; absent evidence never promotes.
- Promotion is separate: authenticated owner approval, existing stale-base CAS, monotonic version n+1, and RISK-06/07/19 preconditions. Rollback is a new n+1 promotion restoring old content; Helm is reference only and Ranex must prove it.

### Confirmation
Measurement-local M0 is one disposable, two-week prototype under ADR-013. It opens only after ADR-017 P0 permits it, uses scratch worktrees/branches at pinned identical HEAD, ships nothing, and merges no prototype code. Its required success output is one GREEN digest-bound exit record; a RED record followed by drop or supersession is legal. Four claims are attempted: (1) a pure grader matches source-derived exact McNemar/Clopper-Pearson vectors and every grade branch; (2) schema separation plus corpus/treatment immutability refuses ordinary-observation grading, corpus drift, and unresolved treatment; (3) one real paired integration seam through a fresh worktree/session hashes the manifest and target and classifies faults, without claiming generalization or provider independence; (4) scratch promotion/rollback reuses ADR-012 CAS and refuses self-approval, stale base, non-n+1, and version reuse. RISK-06/07/19 need not close for scratch simulation, but block production F4.

M0 adds a red-first docs contract gate keyed ADR-016: M0 is exempt, but F1+ is refused unless the record is GREEN, digest-bound, and resolvable from open or done locations. The record mirrors proven SLICE-011 practice: commands, artifacts, fixtures and digests per claim; red and green runs; negative controls; review findings; and residuals. Two cross-family model reviewers provide defect-finding input only; the supervisor reruns recorded commands on disk. The repo owner authorizes ADR acceptance and time-box decisions; authenticated owner identity is mandatory for production promotion. Acceptance is never gated on prototype evidence: the owner may accept before M0, and green M0 gates production, not ADR acceptance. Evidence may later cause this ADR to be dropped or superseded. The two-week clock starts when the owner authorizes M0; expiry must record polish-and-extend, drop/supersede, or permission to open F1 when the record is GREEN. Silence is not an outcome.

## Improvements on the prior art
Ranex separates outcome instrumentation from treatment comparison, binds both to digests, and makes candidate generation pluggable and untrusted. No Prime, DSPy, or GEPA code is proof-bearing. The kernel judges; the harness collects; neither model output nor proposal authorizes promotion.

The dependency-ordered future sequence is measurement-local M0 prototype; F1 `TreatmentManifest` + `TargetCorpus` + monitoring-only observations; F2 pure paired grader and source vectors; F3 paired runner/lifecycle/fault capture; F4 promotion/rollback. F1+ is gated by the M0 record. Production reimplements at current HEAD with frozen red-first tests and never merges prototype code. No automated proposal/refinement exists before F4; it remains an untrusted UI outside the proof core.

## Architecture surface
Keep the ordinary verdict domain and `evaluate()` unchanged. Future experiment modules and records are a separate pure grading function and namespace, named conceptually here without prescribing filenames. The kernel/model wall remains.

## Scope and threat delta
This decision addresses post-hoc grading, corpus drift, treatment ambiguity, rollback, and self-authorized promotion. It does not solve provider correlation, generalization, exact power, candidate quality, model honesty, or whole-composition correctness.

## Quality attributes
The design is deterministic at hashing, pairing, ordering, and grading boundaries; auditable through append-only records; conservative under absence and unknown faults; and reproducible only when all model/provider versions are pinned.

## Reversibility
Door: two-way
Changing the first endpoint or statistical rule requires a new preregistered experiment design, not reinterpretation of old observations. Promotion rollback is content restoration at a new monotonic version.

## Sad paths
- 1. Corpus changes after freezing: reject the proposal and do not grade.
- 2. Candidate changes the corpus: reject as unauthorized.
- 3. Model alias lacks a provider-issued immutable version: mark the treatment ineligible.
- 4. Treatment dependency cannot resolve: reject the treatment before dispatch.
- 5. One arm lacks an observation: no comparative grade.
- 6. Unknown fault classification: block and return `INCONCLUSIVE`.
- 7. Checker or infrastructure fault is discovered: count it and void the pair.
- 8. Shared provider correlation is present: retain the named limit; do not claim independence.
- 9. Discordant count is below the preregistered minimum: inconclusive.
- 10. Evidence digest mismatches the subject: reject the observation.
- 11. Owner approval is absent or unauthenticated: refuse promotion.
- 12. Promotion base is stale or version is not n+1: fail CAS and refuse promotion.
- 13. Rollback tries to reuse a version: refuse; restore through a new n+1.
- 14. Secondary metric improves while the primary endpoint fails: do not grade superior.
- 15. Candidate generator recommends a change: treat it as untrusted input, never authorization.

## Test strategy
Future red-first tests must cover source-vector differential tests; property/boundary tests; an unsafe baseline and load-bearing negative control before implementation; fault injection; attacks for drift, self-approval, stale CAS, downgrade, and version reuse; crash/restart where relevant; provider drift/correlation disclosure; CAS races; rollback/truncation; no-model-credential grading; and delta coverage of refusal branches. Mutmut survivors are review input, not an automatic blocker. Deterministic controls need a discriminating red-first run and ordinary-suite repetition. Nondeterministic controls must reproduce the unsafe baseline, predeclare a soak/repetition budget sufficient for the observed rate (>=20 when no estimate exists), include the negative control each run, and disclose that finite green runs do not prove a zero flake rate.

F4 is a hard gate: no second approval or promotion surface; reuse ADR-012 CAS; RISK-06/07/19 must be closed; authenticated owner approval, a green M0 record, and green attack/fault controls are required; rollback forward-appends n+1. Exact power, URL provenance, generalization, provider independence, and candidate quality are explicitly excluded from M0 exit criteria because they are unprovable today. Existing contract coverage is `tests/contract/test_docs_discipline.py`; no implementation is claimed by this ADR.

## Code review checklist
- Verify `evaluate()` and ordinary verdict records are unchanged.
- Verify corpus freeze precedes candidate proposal and dispatch hashing.
- Verify no ordinary observation can produce a grade.
- Verify exact formulas, preregistered limits, and fault policy are pure.
- Verify owner approval, stale-base CAS, n+1 versions, and rollback evidence.
- Verify no candidate generator or model output is authorization.

## More Information
This accepted ADR corrects MAP §11.3: the frozen target fixes the outcome instrument, not the treatment. Acceptance preceded M0; later evidence may still drop or supersede it. `docs/STATE.md` keeps ADR-017 P0 first; a flywheel prototype pointer is recorded only when M0 opens. F4 has no scheduled unblock path while RISK-06/07/19 remain open. The six vendored files and `NOTICE.md` are internal evidence of fetched source bytes; their hashes do not prove URL provenance without an independent fetch.
