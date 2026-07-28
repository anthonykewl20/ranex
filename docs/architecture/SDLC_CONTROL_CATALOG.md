# Ranex SDLC Control Catalog

| Field | Value |
|---|---|
| Catalog ID | `CAT-SDLC-001` |
| Version | `1.4.0` |
| Status | `ACCEPTED`; implementation maturity is `R_AND_D` until adoption gates pass |
| Effective date | 2026-07-27 |
| Repository snapshot basis | `bootstrap/pre-upstream`; exact digest/revision is supplied by the review or release source manifest |
| Owner | Human governor |
| Parent policy | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Research | [Real-world SDLC operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md) |
| Compatibility/migration class | New control catalog; older phases are inputs to a versioned crosswalk |
| Security/data class | Public control metadata; referenced evidence retains its own classification |

## 1. Purpose

This catalog makes the core operating model executable. It supplies stable
control IDs, common evidence systems, complete stage contracts, rejection
routes, tailoring rules, and source/evidence classifications.

`ACCEPTED` means the human owner selected the policy. It does not claim that
Ranex implements it, conforms to ISO/CMMI, or has completed an external
appraisal. Adoption-gate evidence reports implementation maturity separately.

## 2. Evidence classification

| Code | Meaning |
|---|---|
| `STD` | International consensus standard used as structural guidance |
| `GOV` | Government standard/handbook/recommendation |
| `OBS` | Repeated observational industry research |
| `PRAC` | Mature practitioner guidance and cases |
| `MODEL` | Capability/maturity assessment model |
| `OWNER` | Ranex owner requirement or design choice |

Major controls cite one or more classes. Evidence-informed does not mean
scientifically proven.

## 3. Cross-lifecycle control systems

### SDLC-PM-001 — Project management

Across every material work item or release:

```text
PLAN -> EXECUTE -> ASSESS_AND_CONTROL -> CLOSE
          ^                  |
          +---- correct/reforecast
```

The integrated plan contains scope, assumptions, estimate range, milestone
forecast, capacity/resources, dependencies, risk reserve, configuration,
quality, measurement, acceptance, delivery and closure criteria. The delivery
owner records actual-versus-plan variance, forecast-to-complete, corrective
action, owner/date, and risks/issues/decisions. A material scope, schedule,
capacity, cost, requirement or risk change requires human recommitment.
Closure records acceptance, handover, archive, residual risk and lessons.

Estimates express uncertainty and inform decisions. Point estimates and story
points are optional; individual estimate accuracy is not a performance measure.

Evidence basis: `STD` ISO/IEC 29110 Basic profile; `GOV` NASA-HDBK-2203;
`OWNER` Ranex tailoring.

### SDLC-CM-001 — Configuration management

Configuration items include, where applicable:

- needs, requirements, decisions, ADRs and contracts;
- source, generated code, schemas and migrations;
- prompts, model/route specifications and provider catalogs;
- tests, test data, expected results and qualified tools;
- dependencies, lockfiles, toolchains and build instructions;
- deployment/installation configuration and environment descriptions;
- runbooks, user/operator documentation, findings and waivers; and
- artifacts, manifests, SBOMs, attestations and release/retirement records.

The configuration manager/build custodian:

1. identifies item, owner, system of record and retention;
2. establishes named content-addressed baselines;
3. applies authorized change control;
4. maintains configuration status accounting;
5. proves reproducible build and detects environment/configuration drift;
6. performs functional and physical configuration audits;
7. archives and retrieves exact released/retired baselines; and
8. reconciles emergency changes into normal control.

`RELEASE_READY` requires evidence that requirements, source, build inputs,
artifact, configuration, tests/results, documentation, defects/waivers and
release record are mutually consistent.

Evidence basis: `GOV` NASA-HDBK-2203; `GOV` NIST SSDF; `OWNER`.

### SDLC-TR-001 — Bidirectional traceability

Required links:

```text
need/outcome <-> software requirement
requirement <-> risk/hazard/misuse control
requirement <-> design component
design <-> code/configuration item
requirement <-> verification and validation evidence
requirement <-> defect/nonconformance/waiver
```

Definition, Design, Verification and Release Ready run orphan and unjustified
extra-element checks. Changing a source marks dependent links/evidence stale
until impact analysis and re-verification complete.

Evidence basis: `GOV` NASA-HDBK-2203; `OWNER`.

### SDLC-VV-001 — Verification, validation and acceptance

- **Verification** proves specified requirements/design were implemented
  correctly.
- **Validation** shows representative use satisfies intended user need/context.

Every record names need/requirement, exact subject, verifier, method,
environment/configuration baseline, test data, expected/actual result,
anomaly/waiver, date and durable evidence. Acceptance names the version,
conditions/deviations, human authority and date.

| Lane | Minimum independence |
|---|---|
| Standard | Fresh reviewer who did not make the change |
| Enhanced | Different maker and independent V&V/test authority |
| Critical | Independent qualified specialist; maker/implementation owner cannot accept critical security, data, authority or recovery V&V |
| Emergency | Independent check when available, then full lane-appropriate V&V after mitigation |

The V&V authority may reject the environment/baseline, require anomaly
resolution or regression expansion, veto a factual pass, and escalate. It
cannot accept product/risk value for the human owner. No waiver turns a factual
failure into `PASS`.

Evidence basis: `GOV` NASA-HDBK-2203; `PRAC` Google Engineering Practices;
`OWNER`.

### SDLC-SUP-001 — Supplier and dependency governance

Applies to packages, toolchains, models, APIs, providers, plugins/extensions,
hosted services and Hermes upstream. A supplier owner records:

- make/buy/adopt/reuse decision and alternatives;
- functionality, quality, security, privacy, license/provenance, support and
  exit requirements;
- viability, concentration, transitive and lock-in risks;
- acceptance tests and shared-responsibility matrix;
- pinned/version/update and vulnerability/end-of-life monitoring;
- incident notification/escalation;
- contingency, replacement, export/deletion and termination; and
- reassessment date and residual-risk authority.

An SBOM is evidence, not acceptance by itself.

Evidence basis: `GOV` NIST SSDF; `GOV` NASA-HDBK-2203; `OWNER`.

### SDLC-DEBT-001 — Technical debt

Any accepted shortcut, exception, temporary flag, compatibility shim, skipped
automation, degraded test or deferred cleanup creates a debt record. It names
affected configuration items, type/cause, remediation estimate range, observed
or expected interest, risk, owner, review/expiry and trigger.

Expired or triggered debt returns to triage. Track age, interest signals,
expired items and remediation throughput—not raw count or people.

Evidence basis: `OWNER`, supported by `OBS` DORA maintainability/flow guidance.

### SDLC-TAIL-001 — Tailoring

Each project or material change binds a baseline profile and records invoked,
omitted or modified controls, rationale, compensating controls, approver,
expiry and review triggers.

Truthfulness, exact-subject evidence, traceability, evidence integrity, legal
and secret protection, cross-project isolation, human risk authority, and the
ban on maker self-approval are not tailorable. Risk lanes are pre-approved
assurance profiles; tailoring is not an emergency waiver.

Evidence basis: `STD` ISO/IEC 29110 scope; `GOV` NASA tailoring; `MODEL` CMMI;
`OWNER`.

### SDLC-MEA-001 — Measurement

Before a metric governs a decision, specify: goal and question served,
construct, operational definition/formula, entity and unit, event source,
population, start/stop events, exclusions, data-quality and uncertainty checks,
owner, cadence, baseline/control limit, paired guardrail, retention, triggered
decision and anti-gaming risk. Remove a metric that serves no decision.

Accepted specifications live in versioned registry `METRIC-SDLC-001`. Each
`MetricSpec` has `DRAFT`, `ACCEPTED`, or `SUPERSEDED` status, a stable ID, the
fields above, an owner, an approver, and a correction history. The listed
measure families below are candidate coverage, not a claim that their
operational specifications or baselines already exist.

The catalog covers outcome, flow, DORA delivery measures, requirement
volatility, defect leakage, estimate calibration distributions, review/test
effectiveness, configuration drift, dependencies/maintenance, supplier
incidents, debt age/interest, retirement exceptions and V&V escaped defects.
`SDLC-ADOPT-A/E` must register the actual specifications before they govern a
decision.

A measurement harness or query system has a version/configuration digest,
qualification evidence, repeatability/data-quality tests, and an
infrastructure-error ledger. Level-`3`/`4` claims cannot rely on an unqualified
measurement system.

Evidence basis: `OBS` DORA; `MODEL` CMMI; `OWNER`.

### SDLC-MEA-002 — Capability assessment and improvement selection

This section defines capability rubric `SDLC-MEA-002`, version `3.0.0`.

Capability assessment is diagnostic and evidence-bound. The assessment unit is
one normative control or named capability for a declared value stream/service,
work class, risk-lane set, policy/rubric version and review window. A work-item
gate outcome remains separate and can never borrow authority from a historical
process score.

Each versioned `CapabilityAssessment` reports:

- result: `NOT_ASSESSED`, `UNKNOWN`, `NOT_APPLICABLE`, or `SCORED`; only
  `SCORED` has a level: `0` `ABSENT`, `1` `DEFINED`, `2` `OPERATED`, `3`
  `CONTROLLED`, or `4` `IMPROVING`;
- effectiveness: `UNKNOWN`, `REGRESSING`, `MIXED`, or `MEETS_TARGET`;
- coverage: eligible/included/excluded counts and percentage by work class and
  risk lane; and
- confidence: `LOW`, `MEDIUM`, or `HIGH`, with sample, duration,
  representativeness, missingness, authenticity and data-quality rationale.

When result is not `SCORED`, level is absent. The levels are ordinal labels.
Ordering and counts by label inside one value stream/profile over time are
allowed; arithmetic distance, addition, weighting, means, ratios, cross-team
league tables, and a process-wide overall score are prohibited.

A numeric level requires criterion evidence for that level and every lower
level. Documentation alone cannot exceed `1`. Representative level-`2`
evidence includes a normal path and at least one rejection, invalidation,
exception, or backward path actually traversed and bound to durable events;
documenting a possible path is insufficient. Level `3` requires governed
operation over declared windows with visible distributions, false passes,
misses, exceptions and triggered responses, plus qualified metric/query
evidence. Level `4` requires a prospectively frozen improvement experiment
whose sustained benefit clears declared uncertainty/local noise over more than
one review window, whose counter-metrics survive independent review, and whose
infrastructure faults are reported separately from subject failures.

Evidence is evaluated across enacted practice, durable artifact/provenance, and
outcome/guardrail behavior. Proxy counts such as coverage, documents, lines of
code or entity counts are diagnostic locators, not direct success measures.
Failed required tests and disabled safeguards remain non-compensating findings.

`NOT_ASSESSED` and `UNKNOWN` are not numeric zero and are not passes.
`NOT_APPLICABLE` requires a rule in applicability registry
`APPLICABILITY-SDLC-001`, an immutable eligible-population query, reason, and
accountable approval. It is invalid when eligible work or a qualifying trigger
exists in-window; applicability ambiguity produces `UNKNOWN`. Profiles publish
N/A counts/rates by domain, work class and lane. Independent assurance samples
N/A dispositions and the breadth of their rules.

Applicability registry `APPLICABILITY-SDLC-001`, version `1.1.0`, contains:

| Rule | Meaning |
|---|---|
| `APP-CROSS-001` | Cross-lifecycle control applies to every material in-scope work item |
| `APP-STAGE-001` | Stage control applies when eligible work entered or should have entered that canonical state |
| `APP-TRIGGER-001` | Linked maintenance, retirement, exception, rollback, supplier, or similar control applies when its declared trigger exists |
| `APP-FORK-BASE-001` | Persistent fork ancestry, inherited-behavior, compatibility/integration-surface, and reconciliation controls apply to Ranex in every review window |
| `APP-FORK-SYNC-001` | Upstream-sync control applies when an observation/cadence obligation, candidate, classification, disposition, port, or baseline decision is due or exists in-window |
| `APP-FORK-UPDATE-001` | Release/update control applies when an update obligation, candidate, staged change, activation, or recovery exists in-window |
| `APP-FORK-CUTOVER-001` | Cutover/self-development control applies when an operating-mode, canonical-writer, controller/candidate, or cutover obligation/change exists in-window |
| `APP-AIW-001` | AI-worker fleet controls apply whenever more than one agent/worker is dispatched or fleet machinery affects evidence, selection, landing, or authority |

Vital-control profile `VITAL-SDLC-001`, version `1.1.0`, is owned by the human
governor. Assessment authors cannot alter it. A change requires a new profile
version and governed policy/ADR decision.

The profile is a set of exact
`(domain_id, control_id, applicability_rule_id)` tuples. Each tuple has exactly
one rule, so assessment authors never choose an `AND`/`OR` interpretation.
Applicability rules may be changed only by versioning the registry and profile.

| Domain ID | Capability domain | Control ID | Applicability rule |
|---|---|---|---|
| `CAP-INTAKE-TRIAGE` | Intake and triage | `SDLC-INT-001` | `APP-STAGE-001` |
| `CAP-INTAKE-TRIAGE` | Intake and triage | `SDLC-TRI-001` | `APP-STAGE-001` |
| `CAP-DISCOVERY-DEFINITION` | Discovery and definition | `SDLC-DIS-001` | `APP-STAGE-001` |
| `CAP-DISCOVERY-DEFINITION` | Discovery and definition | `SDLC-DEF-001` | `APP-STAGE-001` |
| `CAP-DESIGN-READINESS` | Design and readiness | `SDLC-DES-001` | `APP-STAGE-001` |
| `CAP-DESIGN-READINESS` | Design and readiness | `SDLC-PLN-001` | `APP-STAGE-001` |
| `CAP-BUILD-FLOW` | Build and flow | `SDLC-BLD-001` | `APP-STAGE-001` |
| `CAP-BUILD-FLOW` | Build and flow | `SDLC-BLK-001` | `APP-TRIGGER-001` |
| `CAP-VERIFY-VALIDATE` | Verification and validation | `SDLC-VV-001` | `APP-CROSS-001` |
| `CAP-VERIFY-VALIDATE` | Verification and validation | `SDLC-VER-001` | `APP-STAGE-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-CM-001` | `APP-CROSS-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-RDY-001` | `APP-STAGE-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-REL-001` | `APP-STAGE-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-RBK-001` | `APP-TRIGGER-001` |
| `CAP-OPERATE-MAINTAIN` | Operation, incident, and maintenance | `SDLC-OPS-001` | `APP-STAGE-001` |
| `CAP-OPERATE-MAINTAIN` | Operation, incident, and maintenance | `SDLC-MNT-001` | `APP-TRIGGER-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-OUT-001` | `APP-STAGE-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-CLS-001` | `APP-STAGE-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-CAN-001` | `APP-TRIGGER-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-RET-001` | `APP-TRIGGER-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-TR-001` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-TAIL-001` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-MEA-001` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-MEA-002` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-PA-001` | `APP-CROSS-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-000` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-001` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-002` | `APP-FORK-SYNC-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-003` | `APP-FORK-UPDATE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-004` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-005` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-006` | `APP-FORK-CUTOVER-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-007` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-001` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-002` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-003` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-004` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-005` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-006` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-007` | `APP-AIW-001` |

A domain projection binds one immutable assessment ID, revision, and digest for
every registered tuple in that domain, all for the identical service/value
stream, work-class and risk-lane scope, policy/rubric versions, and review
window. Missing, extra, duplicate, rule-mismatched, stale, or cross-scope rows
invalidate the projection; the result and priority are derived, never authored.
Use the executable authoring skeleton
[`CAPABILITY_DOMAIN_PROJECTION.yaml`](./templates/CAPABILITY_DOMAIN_PROJECTION.yaml)
whose registered schema is
[`capability_domain_projection.schema.json`](../../schemas/artifacts/capability_domain_projection.schema.json).

For projection derivation, an **applicable member** is a registered tuple whose
applicability result resolved to `APPLICABLE`. A valid
`NOT_APPLICABLE` member remains in the complete tuple set but is not an
applicable member and never enters the level floor. An applicable assessment
has begun when at least one applicable member rating is no longer
`NOT_ASSESSED`.

For a valid projection, a domain result is deterministic:

1. Unresolved applicability or an invalid N/A disposition produces `UNKNOWN`.
2. If every registered tuple is validly `NOT_APPLICABLE`, the domain is
   `NOT_APPLICABLE` and has no level or priority tier.
3. With at least one applicable member, the domain is `NOT_ASSESSED` only when
   every applicable member rating is `NOT_ASSESSED`.
4. Once at least one applicable member rating is no longer `NOT_ASSESSED`, any
   applicable member rated `UNKNOWN` or `NOT_ASSESSED` makes the domain
   `UNKNOWN`.
5. The domain is `SCORED` if and only if every applicable member is `SCORED`;
   its level is the lowest supported level among those members.

There is no arithmetic aggregation.

Confidence requires a versioned adequacy rule and recorded test results. `HIGH`
requires all declared sample, duration, representativeness, authenticity,
freshness, missingness, and data-quality tests to pass plus independent
assurance sign-off. Without an approved adequacy rule, confidence is at most
`MEDIUM`; a material unresolved population/evidence gap forces `LOW`. One gap
register inventories evidence, applicability, population, coverage and
measurement gaps. Every known gap needs a materiality and resolution
disposition; `HIGH` additionally requires a complete inventory and no
unresolved material gap. Any unresolved material gap makes the capability
rating `UNKNOWN` with no level and confidence `LOW`; it cannot coexist with a
`SCORED` result.

All population and coverage values derive from one immutable population
snapshot. Joint work-class/risk-lane strata are complete for the declared
scope, including zero-count strata. In each stratum and in total,
`eligible = included + excluded`; strata sum to totals and itemized exclusions
sum to the excluded count. Coverage percentage is derived from those totals,
not independently entered. Applicability and coverage reference that same
snapshot/query by pointer; they cannot carry competing copies.

Adverse populations use versioned typed predicates rather than one mixed
“class” list. At minimum they distinguish failed control/execution outcomes,
`BLOCKED`/`CANCELLED`/`ROLLED_BACK` status history, reopened attempt history,
and the `EMERGENCY` risk lane. Every category records immutable query digest
and eligible/included/excluded counts. A category passes only when no eligible
subject exists or every eligible subject is included with zero exclusions. A
`SCORED` record is invalid if any required applicable adverse category fails.

Priority registry `PRIORITY-SDLC-001`, version `1.0.0`, is total for every
applicable assessment. Evaluate tiers in `P0 -> P1 -> P2 -> P3` order; the
first matching tier wins:

- `P0 CONTROL_NOW` for active harm or a non-tailorable
  invariant/truth/authority/evidence/recovery breach;
- `P1 IMPROVE_NEXT` for result `NOT_ASSESSED`/`UNKNOWN`, level `0`/`1`, an
  overdue critical obligation, repeated escape, high-exposure downstream
  blockage, or `LOW`-confidence instrumentation need;
- `P2 IMPROVE_DELIBERATELY`, only absent P0/P1, for level `2`,
  `UNKNOWN`/`REGRESSING`/`MIXED` effectiveness, material
  flow/quality/outcome harm, or any remaining unproven P3 criterion; and
- `P3 SUSTAIN`, only absent P0–P2, for level `3`/`4`,
  `MEETS_TARGET`, passing coverage/adverse-population reconciliation, healthy
  guardrails, no adverse trend, and confidence above `LOW`.

The trigger-code registry is:

| Tier | Trigger codes |
|---|---|
| `P0` | `ACTIVE_HARM`, `NONTAILORABLE_INVARIANT_BREACH`, `NONTAILORABLE_TRUTH_BREACH`, `NONTAILORABLE_AUTHORITY_BREACH`, `NONTAILORABLE_EVIDENCE_BREACH`, `NONTAILORABLE_RECOVERY_BREACH` |
| `P1` | `RESULT_NOT_ASSESSED`, `RESULT_UNKNOWN`, `LEVEL_0`, `LEVEL_1`, `OVERDUE_CRITICAL_OBLIGATION`, `REPEATED_ESCAPE`, `HIGH_EXPOSURE_DOWNSTREAM_BLOCKAGE`, `LOW_CONFIDENCE_INSTRUMENTATION` |
| `P2` | `LEVEL_2`, `EFFECTIVENESS_UNKNOWN`, `EFFECTIVENESS_REGRESSING`, `EFFECTIVENESS_MIXED`, `MATERIAL_FLOW_QUALITY_OUTCOME_HARM`, `P3_CRITERIA_UNPROVEN` |
| `P3` | `P3_ALL_CRITERIA_PROVEN` |

Every trigger code is recorded exactly once as match/no-match for an applicable
assessment. `P3_CRITERIA_UNPROVEN` and `P3_ALL_CRITERIA_PROVEN` are mutually
exclusive and make the final branch total. The derived tier is the
highest-precedence tier containing any match; it cannot be typed manually.

Within a tier, consequence, exposure, recurrence, downstream blocking and
capability gap determine order. `LOW` confidence selects P1 and requires a
linked instrumentation/sampling action. A valid all-N/A assessment has no
priority tier. Domain priority is the highest-precedence member tier, never a
numeric average.

The per-control assessment record includes assessor/approver independence,
scope digest, applicability rule and immutable population snapshot; reconciled
totals and joint work-class/risk-lane strata; typed adverse-category query
digests and counts; N/A disposition/audit; event/evidence digest; criterion
evidence; measures/baseline/comparator; all seven named confidence-adequacy
tests and sign-off; invariant findings; exceptions; derived priority;
prior/superseded record; and correction reason. A separate immutable domain
projection binds every registry tuple and derives the floor and
highest-precedence member priority.

A linked improvement record names causal stage/control, hypothesis, bounded
change, and one immutable measurement-design reference. That design binds the
versioned metric specification, fixed comparator, primary measure, paired
guardrails, prospectively frozen decision rule, minimum meaningful/detectable
effect, declared uncertainty/local noise, and qualified harness ID/version/
configuration digest. The design also carries the separate
infrastructure-error ledger where relevant and is the sole owner of that
reference; the improvement record cannot restate a competing ledger. The
improvement record carries its owner, evidence window, stop/revert criteria and
retain/change/revert decision. Use the executable authoring skeletons
[`CAPABILITY_ASSESSMENT.yaml`](./templates/CAPABILITY_ASSESSMENT.yaml) and
[`CAPABILITY_DOMAIN_PROJECTION.yaml`](./templates/CAPABILITY_DOMAIN_PROJECTION.yaml)
with the registered
[`capability-assessment-v1.schema.json`](../../schemas/process/capability-assessment-v1.schema.json)
and
[`capability-domain-projection-v1.schema.json`](../../schemas/process/capability-domain-projection-v1.schema.json)
schemas.

For a level-`4` claim, the metric specification, fixed comparator,
prospectively frozen decision rule, uncertainty and analysis method,
decision-rule evaluation, harness qualification, and infrastructure-error
ledger are mandatory and bound by the measurement-design digest. Local noise
cannot default to zero. An established zero floor requires method evidence and
independent claim-specific approval. `NOT_APPLICABLE` uncertainty requires a
deterministic measure plus the exact approved uncertainty-N/A rule and
approval.

Ratings may open improvement work. They may not authorize a transition, issue a
permit, waive a control, lower risk, convert missing/failing evidence into
`PASS`, or evaluate individual performance. Independent assurance samples raw
events and audits exclusions, lane changes, exception growth, incident
suppression, delayed timestamps, threshold clustering and split/reopen
behavior.

#### Executable Wave 1 bindings

The documentation-contract baseline binds this rubric to:

- [`applicability-rules.json`](../../architecture/contracts/applicability-rules.json),
  [`priority-rules.json`](../../architecture/contracts/priority-rules.json), and
  [`vital-profile.json`](../../architecture/contracts/vital-profile.json);
- [`topology-rules.json`](../../architecture/contracts/topology-rules.json),
  [`paths.json`](../../architecture/contracts/paths.json),
  [`test-practices.json`](../../architecture/contracts/test-practices.json),
  and
  [`test-practice-profiles.json`](../../architecture/contracts/test-practice-profiles.json);
- ADR-0009 projections for declared dependency edges, boundary fit, coupling,
  and feedback fitness in
  [`context-dependency-edges.json`](../../architecture/contracts/context-dependency-edges.json),
  [`context-boundary-fitness.json`](../../architecture/contracts/context-boundary-fitness.json),
  [`context-coupling-policy.json`](../../architecture/contracts/context-coupling-policy.json),
  and [`feedback-fitness.json`](../../architecture/contracts/feedback-fitness.json);
- one exact-subject, non-compensating definition record for each of the 18
  topology, 19 TDD, and ten boundary/feedback rules in
  [`architecture-rule-assessments.json`](../../architecture/contracts/architecture-rule-assessments.json);
- the 40 generated per-control records and ten deterministic domain projections
  under [`assessments/`](./assessments/); and
- the schema registry and semantic validator described by
  [`AI_ARTIFACT_CONTRACTS.md`](./AI_ARTIFACT_CONTRACTS.md).

Generator and validator execution is serialized by one repository-scoped
interprocess lock held across the complete read/cleanup/write or read/check/
report transaction. The disposable concurrency regression proves that a
validator cannot observe an empty assessment denominator, that a second writer
waits, and that the final generated-tree digest remains deterministic.

Every generated control record separates `definition_status: DEFINED` from the
runtime `capability_rating.result: NOT_ASSESSED`. Every generated projection is
`UNKNOWN` while applicability and runtime evidence remain unresolved. These
records prove tuple coverage and derivation mechanics; they are not maturity
scores, operating evidence, or adoption-gate passes. Runtime producer
enforcement and human `AI-G2` acceptance remain unassessed. The same honesty
rule applies to the 47 architecture-rule records: inventory coverage is
complete, but a paper definition cannot be promoted into an enacted-source,
behavioral, or maturity score.

Evidence basis: `OBS` DORA system measures; `MODEL` CMMI assessment lens;
`GOV` NASA/NIST assurance; `OWNER`.

### SDLC-PA-001 — Process assurance and competence

The process is itself controlled:

```text
proposal -> pilot -> evidence review -> human approval
  -> versioned rollout/training -> conformance/effectiveness review
  -> retain, improve, or retire
```

The process owner maintains versioned policies, schemas, templates, checks,
examples and migrations. An independent assurance role samples conformance and
artifact authenticity/completeness, records nonconformance, assigns corrective
action and verifies effectiveness. Quarterly management review examines
outcomes, flow, risk, exceptions, incidents, audits and improvement priorities.

Competence profiles and qualification evidence exist for maker, reviewer, V&V,
release, incident, security/data and configuration roles, with named backups
for critical duties. CMMI is an audit lens only; no maturity claim is made.

Evidence basis: `GOV` NASA assurance and NIST SSDF preparation; `MODEL` CMMI;
`OWNER`.

## 4. Complete stage contracts

Controls above apply to every row. `A` is accountable, `R` performs the work,
`C` must be consulted, and `I` is informed.

| Control/state | Purpose and precondition | Required inputs | Mandatory activities | Required outputs/evidence | R / A / C / I | Automated + human exit gates | Rejection/recovery | Tailoring and measures | Basis |
|---|---|---|---|---|---|---|---|---|---|
| `SDLC-INT-001` `FUNNEL` | Preserve a signal; source exists | User/stakeholder feedback, alert, incident, vulnerability, strategy or upstream observation | Assign ID; capture source/date/scope without inventing facts | Immutable signal record | Intake / duty owner / affected owner / reporter | Schema/duplicate/privacy scan + owner acknowledgment | Malformed/sensitive input quarantined; out-of-scope routed or cancelled | Summary may be minimal; measure intake age/source | `STD`,`OWNER` |
| `SDLC-TRI-001` `TRIAGE` | Establish ownership/disposition; valid signal | Signal, portfolio, service map, severity/risk rules | Classify work, urgency, risk lane, impact, owner, disposition and response target | Triage decision, initial risks, reason code | Duty/product / product owner / technical, service, security / reporter | Policy-derived lane + human priority/ownership | Insufficient facts → Funnel/Discovery; not ours → routed; no value → Cancelled | No silent lane lowering; measure time-to-triage and overrides | `STD`,`GOV`,`OWNER` |
| `SDLC-DIS-001` `DISCOVERY` | Validate problem/value; triaged item | Signal, users/actors, current behavior, research access | Research current behavior/users, baseline, alternatives, hypothesis, unknowns and falsifier | Discovery packet and evidence register | Research/product / product owner / technical, service, data / stakeholders | Evidence/source/unknown checks + product decision | Weak evidence → Discovery/Funnel/Cancelled | Standard fixes may use reproduction as discovery; measure learning time/hypothesis yield | `PRAC`,`OBS`,`OWNER` |
| `SDLC-DEF-001` `DEFINITION` | State testable need; supported problem | Discovery packet, constraints, policies | Define outcome, requirements, examples, qualities, non-goals, failure/misuse/recovery, measures; validate with affected user/owner | Baselined requirements and traceability | Requirements role / product owner / technical, V&V, service, security/data / delivery | Schema/orphan/testability checks + product/affected-owner validation | Ambiguous/unverifiable → Discovery/Definition | Artifact length varies, traceability does not; volatility and validation defects | `STD`,`GOV`,`OWNER` |
| `SDLC-DES-001` `DESIGN` | Select safe solution; valid baseline | Requirements, architecture/contracts, risks, supplier facts | Evaluate alternatives; define boundaries, state/effects, data/threat/ops, CM, V&V, release, migration/rollback/retirement | Design record, ADR if required, V&V/config/release strategies | Architect/technical / technical owner or ADR authority / product, V&V, service, security/data, supplier / delivery | Architecture/trace/threat/dependency checks + required human ADR/risk decision | Unacceptable → Definition/Design; infeasible → Triage | Inline note allowed only by lane; measure design churn/late decision changes | `STD`,`GOV`,`OWNER` |
| `SDLC-PLN-001` `READY` | Make responsible commitment; accepted design | Integrated scope, design, estimates, capacity, dependencies/risks | Slice vertically; estimate range; forecast; resource; plan evidence/configuration/acceptance; bind tailoring | Integrated delivery plan, task/decision inputs, DoR proof | Delivery/planner / delivery owner / product, technical, V&V, service / stakeholders | Completeness/dependency/capacity checks + human commitment | Infeasible → Design/Triage; blocking dependency → Blocked | No mandatory points; lead time, forecast calibration, readiness escapes | `STD`,`MODEL`,`OWNER` |
| `SDLC-BLD-001` `IN_PROGRESS` | Produce bounded candidate; Ready item and exact base | Task packet, baselines, workspace, grants | Implement with tests/docs/telemetry; integrate small; manage config/dependencies; record truthfully | Exact candidate, run result, handoff, updated trace/config status | Maker / technical owner / reviewer, V&V, config / delivery | Path/dependency/schema/CI checks + maker handoff (not approval) | Failure → In Progress/Blocked/Design/Definition | One conceptual change; WIP, cycle time, build/rework | `STD`,`OBS`,`PRAC`,`OWNER` |
| `SDLC-VER-001` `VERIFICATION` | Verify and validate exact subject; candidate exists | Candidate, requirements/design, V&V plan, qualified environment | Independent review; test portfolio; security/data/compatibility/recovery; anomaly disposition; representative validation | Review, checker, V&V, acceptance and anomaly records | V&V/reviewers / independent V&V authority + product validator / maker, technical, service, security / release | Exact-subject deterministic gates + independent human/product acceptance by lane | Fail → Build/Design/Definition; environment invalid → re-run | Independence may only increase; effectiveness, leakage, flake, latency | `GOV`,`PRAC`,`OWNER` |
| `SDLC-RDY-001` `RELEASE_READY` | Prove safe promotion; verified candidate | Immutable candidate, audits, manifest, migration/rollback/runbook/comms | Build once; configuration audits; sign/attest; rehearsal; predeclare health/halt/rollback | Release candidate, manifest/SBOM, compatibility and readiness decision | Config/release / release authority / V&V, service, security/data / users/operators | Reproducibility/provenance/audit gates + human permit | Failure → Verification/Design; stale subject → requalify | Standard lane can use automated standard path; readiness failures/time | `GOV`,`PRAC`,`OWNER` |
| `SDLC-REL-001` `RELEASING` | Safely expose approved artifact; valid permit/recovery point | Artifact, destination, permit, baseline and criteria | Snapshot; stage; migrate; activate progressively; observe; halt/rollback/reconcile | Deployment events, health evaluation, completion or rollback | Release operator / release authority / service, incident, data / stakeholders | Destination/digest/health gates + human expansion/rollback where required | Threshold breach → work item `ROLLED_BACK`; open incident/recovery work when impact exists | Smallest applicable exposure; frequency, failure, recovery | `PRAC`,`OBS`,`OWNER` |
| `SDLC-OPS-001` `OPERATING` | Establish supported healthy service; released subject | Release record, SLO/measurement/support/runbooks | Observe window; support; reconcile; scan; backup/restore; capacity/cost review | Operational acceptance, health/security/support evidence | Service/operations / service owner / product, security, supplier / users | Telemetry/reconciliation/backup checks + service-owner acceptance | Failure opens an incident and linked `INCIDENT_RESPONSE` work; uncertainty extends observation | SLO may be Unknown with plan; reliability/support measures | `GOV`,`PRAC`,`OWNER` |
| `SDLC-OUT-001` `OUTCOME_REVIEW` | Decide whether change helped; observation due | Hypothesis/baseline, product and ops evidence | Compare expected/actual, side effects and segments; decide keep/change/remove | Outcome decision and follow-up work | Product analytics / product owner / technical, service, users / portfolio | Data-quality check + human product decision | Falsified → `DISCOVERY` or linked `MAINTENANCE`/`RETIREMENT` work | Sampled only for standard lane; outcome/side-effect measures | `OBS`,`PRAC`,`OWNER` |
| `SDLC-MNT-001` maintenance control | Keep a supported capability fit; maintenance trigger creates a linked work item | Supported-version policy, defects, debt, vulnerability/dependency/ops signals | Run corrective/adaptive/perfective/preventive work through `FUNNEL`–`CLOSED`; regress; patch; update docs/config baseline; release/observe normally | Maintained baseline, linked work item, disposition and release evidence | Maintenance / maintenance+service owner / product, V&V, supplier, security / users | Normal definition/design/V&V/release gates | Unsupported/unviable → linked retirement work; impact → incident record and emergency work item | No bypass for “existing” behavior; backlog age, freshness, debt interest | `STD`,`GOV`,`OWNER` |
| `SDLC-RET-001` retirement control | End capability use/data/access safely; approved trigger creates a linked work item | Consumer/dependency inventory, retention/legal/privacy, replacement/export, recovery | Run retirement work through `FUNNEL`–`CLOSED`; notify; migrate/export; archive; revoke; delete/retain; teardown; observe; audit absence and retrieval | Capability-state transition, retirement permit/events, disposition proofs, independent audit, residual owner | Retirement operator / human governor / product, service, data/security, config / users | Inventory/data/access/archive automated checks + human approval and final audit | Failure leaves capability active/deprecated and opens recovery/incident work; incomplete teardown cannot become `RETIRED` | Retirement depth not tailorable for affected data/access; completion/exceptions | `GOV`,`OWNER` |
| `SDLC-CLS-001` `CLOSED` | Reconcile work and release obligations; terminal evidence exists | Outcome/retirement decision, follow-ups, baselines | Verify ownership, archive, temporary access/flags/worktrees, debt and decisions; close project plan | Closure/acceptance record and retrievable evidence | Work/delivery / work owner / product, technical, service, config / stakeholders | Orphan/expiry/archive checks + accountable closure | Missing follow-up/evidence → prior state/Blocked | Merge never qualifies; end-to-end time, closure debt | `STD`,`MODEL`,`OWNER` |
| `SDLC-BLK-001` `BLOCKED` | Preserve truth when safe progress is impossible; active item has a blocker | Current state/baseline, typed blocker, affected evidence and dependencies | Record reason, owner, entered time, impact, invalidation, escalation and next-decision date; age and review the blocker | Append-only blocked transition and decision/recovery evidence | Work/delivery / work owner / dependency and affected owners / stakeholders | Schema/age/escalation checks + accountable resume/disposition decision | Resume only to an allowed state with refreshed evidence; unresolved/unsafe remains blocked or receives authorized cancellation | No hidden parked work; blocker age/share, repeat causes, missed decision dates | `STD`,`OWNER` |
| `SDLC-CAN-001` `CANCELLED` | End pre-release work without fabricating completion; authorized stop decision exists | Current state, reason, impact, evidence, temporary effects and obligations | Record authority/reason; preserve evidence; clean access/flags/worktrees; assign residual follow-up and notify affected owners | Cancellation decision, cleanup proof, retained record and owned follow-ups | Work/product / product or work owner / technical, service, security/data / stakeholders | Pre-release/state/authority/cleanup checks + human cancellation decision | Missing authority/cleanup → Blocked or prior state; rediscovery creates a linked new work item | Never reported as done/released; cancellation timing/reasons, residual cleanup and repeat discarded work | `STD`,`OWNER` |
| `SDLC-RBK-001` `ROLLED_BACK` | Record a release reversal and prove the prior safe state; rollback initiated | Release/permit, exact artifact/destination, rollback plan, health/impact evidence | Execute authorized rollback; verify safe state; reconcile config/data/access; bound impact; open incident when applicable; create linked re-triage | Rollback events, safe-state proof, impact/reconciliation evidence, linked `TRIAGE` item and incident/action refs | Release/service / release + service owner / incident, product, security/data, configuration / stakeholders | Destination/digest/safe-state/reconciliation checks + release/service acceptance | Unverified recovery remains incident/rollback work; never return directly to normal release without new triage and qualification | Recovery distribution, rollback recurrence, reconciliation/action age | `GOV`,`PRAC`,`OWNER` |

Recommended activities may be added to a stage checklist, but cannot be confused
with the mandatory outputs and gates above.

## 5. Gate failure and recovery semantics

| Failure | Destination |
|---|---|
| Insufficient discovery | `FUNNEL`, `DISCOVERY`, or `CANCELLED` |
| Ambiguous/unverifiable requirement | `DISCOVERY` or `DEFINITION` |
| Unacceptable design | `DEFINITION` or `DESIGN` |
| Infeasible commitment | `DESIGN` or `TRIAGE` |
| Build failure | `IN_PROGRESS` or `BLOCKED` |
| V&V failure | `IN_PROGRESS`, `DESIGN`, or `DEFINITION` |
| Release-readiness failure | `VERIFICATION` or `DESIGN` |
| Rollout health breach | Work item `ROLLED_BACK`; create an `Incident` and emergency work item when impact exists |
| Operational-window failure | Create an `Incident` and linked emergency/defect work item; block or roll back the affected work as policy requires |
| Falsified outcome | Return the work item to `DISCOVERY` or create linked maintenance/retirement work |
| Retirement failure | Keep capability active/deprecated; open recovery or incident work |
| Process nonconformance | Corrective action; evidence stays failed/missing |

Every rejection records reason code, authority, affected baselines, invalidated
evidence and next owner. Risk may be accepted within policy; factual failure,
forged/missing evidence and stale exact-subject proof cannot be overridden.

## 6. Roles and incompatible combinations

Additional accountable roles are:

- requirements owner/business analyst;
- V&V/test authority;
- configuration manager/build-release custodian;
- supplier/dependency owner;
- maintenance owner;
- retirement/data-disposition owner; and
- process owner/independent assurance auditor.

One human may fill roles in a small team, but:

- maker and V&V acceptance cannot combine for enhanced/critical work;
- maker and release/risk authority cannot combine;
- a process auditor cannot audit their own execution; and
- critical duties require a qualified backup or a recorded availability risk.

## 7. Source crosswalk

| Control family | Primary basis |
|---|---|
| Project management, implementation and closure | [ISO/IEC 29110-5-1-2:2025](https://www.iso.org/standard/82669.html) |
| Assurance, traceability, V&V, configuration, delivery/maintenance records | [NASA-HDBK-2203](https://standards.nasa.gov/standard/NASA/NASA-HDBK-2203) |
| Secure organization, environments, software, releases and vulnerability response | [NIST SP 800-218](https://doi.org/10.6028/NIST.SP.800-218) |
| Small batches, WIP, CI/CD, tests, observability and measures | [DORA capabilities](https://dora.dev/capabilities/) and [metrics](https://dora.dev/guides/dora-metrics/) |
| Change size and code review | [Google Engineering Practices](https://google.github.io/eng-practices/review/) |
| SLOs, rollout, incidents and learning | [Google SRE Workbook](https://sre.google/workbook/table-of-contents/) |
| Institutionalization/maturity audit lens | [CMMI levels](https://cmmiinstitute.com/learning/appraisals/levels) |

## 8. Hermes-fork specialized controls

### SDLC-FORK-000 — Fork ancestry and provenance preflight

No runtime implementation commit is accepted into the product branch until a
deterministic exact-subject gate proves:

- immutable preservation of the current Ranex documentation/bootstrap history;
- the pinned upstream repository, commit, verified tree, license/notices, tags,
  and pristine source manifest;
- an authenticated human decision selecting replay or provenance-complete
  import as the ancestry-adoption strategy;
- the resulting merge-base/ancestry proof and final branch/worktree topology;
- a fetch-only upstream remote;
- distinct observed, audited, incorporated, and latest-seen baselines;
- restored upstream license and per-file provenance/classification coverage;
  and
- the actual GitHub network-fork observation as a separate hosting fact.

The hosting flag may remain `false`; it is never used as a substitute for
software derivation, Git ancestry, or license evidence. Failure or missing
evidence keeps the gate `FAIL`, `UNKNOWN`, or `CONFLICT` and the architecture
label “fork target / ancestry adoption pending.”

### SDLC-FORK-001 — Inherited behavior disposition

Every inherited public or authority-relevant behavior is keyed by exact
upstream commit plus path/symbol/observable behavior and assigned:

```text
RETAIN_AS_IS | WRAP | EXTRACT | REIMPLEMENT | REMOVE | QUARANTINE | DEFER
```

The record includes owner, rationale, legal/commercial class, compatibility
contract/test, expiry/removal trigger and replacement work ID. It is required
at Definition/Design, upstream classification, compatibility verification and
release-manifest generation.

### SDLC-FORK-002 — Upstream synchronization

```text
OBSERVED -> FETCHED -> PINNED -> CLASSIFIED -> DISPOSITIONED
  -> disposition REJECT -> REJECTED
  -> disposition DEFER -> DEFERRED
  -> disposition PORT -> PORTING -> PORT_CANDIDATE -> VERIFIED
  -> RELEASED -> BASELINE_RECORDED
```

`BLOCKED` and `ROLLED_BACK` are deterministic branches. Any nonterminal state
from `FETCHED` through `RELEASED` may enter `BLOCKED` only with the prior state,
reason, owner, required evidence, and review deadline; resolution returns only
to that prior state, while abandonment returns to `CLASSIFIED` for a new
`REJECT` or `DEFER` disposition. Only `RELEASED` may enter `ROLLED_BACK`;
reconciliation of product/schema/data/credential/package/external effects is
required before a new candidate revision re-enters `CLASSIFIED`. `REJECTED`,
`DEFERRED`, and `BASELINE_RECORDED` are terminal for one candidate revision.

Disposition is recorded per commit/path, not only per range. Baseline advances
only after a released port set and an explicit rejected/deferred ledger.
Emergency security work may use the emergency lane but cannot auto-merge.

### SDLC-FORK-003 — Release and update

Ranex never treats pulling a mutable branch and resetting source as product
rollback. Update states are:

```text
CHECKED -> DOWNLOADED -> VERIFIED -> SNAPSHOTTED -> STAGED
  -> MIGRATED -> ACTIVATED -> HEALTH_VERIFIED -> COMPLETED

Any post-snapshot state -> ROLLED_BACK -> RECOVERY_VERIFIED
```

The release binds artifact identity/digest and signature/attestation; policy,
workflow, schema, module and provider catalogs; disposition/compatibility
report; evidence digests; install target/platform matrix; configuration
migration; pre/post snapshot IDs; rollback compatibility limits; and
observation window. Refuse downgrade when schema/data/effects are not reversible
and require restore/reconciliation proof.

### SDLC-FORK-004 — Compatibility

Legacy surfaces use:

```text
SUPPORTED -> DEPRECATED -> READ_ONLY -> REMOVED
```

The registry covers `hermes` CLI, legacy home/config/session/tool identifiers,
plugins and providers, with version range, translation owner, parity tests,
privacy-safe usage evidence, notice, removal criteria and migration/rollback.
Compatibility cannot remain indefinite without a renewed human decision.

### SDLC-FORK-005 — Plugins, providers, MCP and routes

Subject state is not one generic lifecycle:

- external plugins/extensions use `ExtensionStatus`:
  `DISCOVERED -> QUARANTINED -> REVIEWED -> QUALIFIED -> PINNED -> ENABLED`,
  with `SUSPENDED | RETIRED`;
- first-party modules use `ModuleStatus`; and
- provider/model transports use `RouteStatus`.

`qualification` emits immutable trial/qualification evidence; only the owning
module, extension, or route context changes its subject state. Qualification
locks source and dependencies, manifest, protocol/schema, capability grants,
egress/secrets/data class, crash isolation and quarantine tests. Human
activation is required. Target mode forbids mutable Git update, unapproved
catalog install, optional manifest, user last-writer-wins override,
environment-presence route selection and import-time authority registration.

### SDLC-FORK-006 — Operational cutover and self-development

```text
BOOTSTRAP -> LEGACY_BASELINE -> TRANSITIONAL_DUAL_RUN
  -> TARGET_SHADOW -> TARGET_LIMITED -> TARGET_DEFAULT
  -> LEGACY_FROZEN -> LEGACY_REMOVED
```

Each mode binds authority owner, permitted effect paths, sole canonical writer,
rollback target and exit evidence. “Dual run” never means dual authority.

Self-development uses an immutable controller release `N` to govern candidate
`N+1`. The controller cannot modify or restart itself during the run. Candidate
release requires independent human permit, rollback drill, post-release
observation and outcome review.

### SDLC-FORK-007 — Required machine-readable reconciliation

Before the runtime tracer, provide:

- an archival phase-to-SDLC mapping for any retained pre-`ADR-0002`
  guide-derived execution records, explicitly forbidden as an itinerary for
  new work;
- exact-subject invalidation graph covering upstream/base/candidate commits,
  release manifest, test evidence, route catalog and operational mode;
- inherited-Hermes behavior disposition ledger; and
- compatibility matrix across upstream baseline, Ranex release, state schema,
  Python/Node/platform, plugin protocol and provider catalog.

The deleted legacy implementation-guide lifecycle is historical vocabulary,
not a live migration or construction input. Its mapping exists only so old
records remain intelligible. It cannot create new work, ordering, requirements,
states, gates, or acceptance criteria. `MERGED` is a landing event. It never
substitutes for `RELEASED`, `OPERATING`, `OUTCOME_REVIEW`, or `CLOSED`.

## 9. AI-worker fleet specialized controls

These controls implement the
[AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md)
inside this SDLC. They govern worker execution and never create another product
lifecycle.

### SDLC-AIW-001 — Assignment, lease, and liveness

Every worker attempt is admitted from an exact current packet and receives a
typed assignment, atomic compare-and-swap claim, expiring lease, and
monotonically increasing fencing epoch. Heartbeats use coordinator time and
prove only recent contact. Expired, revoked, cancelled, or superseded attempts
are denied at every write, model, tool, mailbox, result, and effect boundary.
Reclaim creates a new linked attempt; late artifacts remain preserved but
ineligible.

### SDLC-AIW-002 — Deterministic execution governor

One release-pinned governor enforces the absolute deadline; parent/child
budgets; turn/model/tool/process/network/output ceilings; retry and consecutive
failure limits; result-aware loop detection; cancellation; sandbox
termination; and cleanup/reconciliation. A worker cannot change its governor
profile or label repeated activity as progress.

### SDLC-AIW-003 — Parallelism, workspace, and landing

One worker is the default. Parallel reads use isolated context. Parallel writes
require disjoint registered ownership and separate validated worktrees. Shared
files have one writer at a time. Integration/reconciliation is a new bounded
assignment and worker output remains a proposal. Landing is serialized and
human-controlled for every worker count; self-merge is prohibited.

### SDLC-AIW-004 — Transitive resource and permission enforcement

Every child assignment/model/tool call consumes a reservation whose usage is
attributed to all parents. The tool boundary validates current lease epoch,
exact subject, workspace, capability, policy, qualification, sandbox, and
budget. External effects still require the normal evidence → gate → human
decision where applicable → authority grant → permit → `CapabilityBus` order.

### SDLC-AIW-005 — Verification capacity and hidden evidence

Fleet admission cannot exceed qualified deterministic, independent,
holdout-based, product-validation, and human-decision capacity. Overload causes
backpressure, not weaker assurance. Hidden fixtures, answer keys, expected
secret outcomes, and independent observations remain outside maker-visible
packets and mounts. Model consensus cannot produce a gate outcome.

### SDLC-AIW-006 — Measurement and topology selection

The measurement harness is the first fleet-scaling experiment instrument after
the Core-SDLC contracts and authority/evidence/isolation foundations exist.
Experiments predeclare tasks, controls, budgets, repeated assignments,
uncertainty, verifier calibration, failure treatment, costs, outcomes, and stop
rules. External fleet-size, performance, price, or accuracy thresholds remain
`R_AND_D` hypotheses until reproduced on Ranex work.

### SDLC-AIW-007 — Learned control quarantine

Learned routing, topology, prompt/role optimization, or conductor policy is
inactive until offline train/validation/test/hidden evaluation, tamper
resistance, drift, rollback, non-self-activation, and human-accepted exact
policy evidence pass. Learnable parameters can never include authority, risk,
permissions, hidden-data access, verification depth, or policy activation.
