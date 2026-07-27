# Ranex SDLC Control Catalog

| Field | Value |
|---|---|
| Catalog ID | `CAT-SDLC-001` |
| Version | `1.0.0` |
| Status | `ACCEPTED`; implementation maturity is `R_AND_D` until adoption gates pass |
| Owner | Human governor |
| Parent policy | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Research | [Real-world SDLC operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md) |

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

Before a metric governs a decision, specify: question served, formula, event
source, population/unit, start/stop events, exclusions, data-quality checks,
owner, cadence, baseline/control limit, retention, triggered decision and
anti-gaming risk.

The catalog covers outcome, flow, DORA delivery measures, requirement
volatility, defect leakage, estimate calibration distributions, review/test
effectiveness, configuration drift, dependencies/maintenance, supplier
incidents, debt age/interest, retirement exceptions and V&V escaped defects.

Evidence basis: `OBS` DORA; `MODEL` CMMI; `OWNER`.

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
OBSERVED -> FETCHED -> PINNED -> CLASSIFIED
  -> DISPOSITIONED (REJECTED | DEFERRED | PORT_PLANNED)
  -> PORTING -> PORT_CANDIDATE -> VERIFIED
  -> RELEASED -> BASELINE_RECORDED
```

`BLOCKED` and `ROLLED_BACK` are valid branches. Disposition is recorded per
commit/path, not only per range. Baseline advances only after a released port
set and an explicit rejected/deferred ledger. Emergency security work may use
the emergency lane but cannot auto-merge.

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

- phase-to-SDLC migration matrix;
- exact-subject invalidation graph covering upstream/base/candidate commits,
  release manifest, test evidence, route catalog and operational mode;
- inherited-Hermes behavior disposition ledger; and
- compatibility matrix across upstream baseline, Ranex release, state schema,
  Python/Node/platform, plugin protocol and provider catalog.

The older implementation-guide lifecycle is a migration input, not a second
canonical vocabulary. `MERGED` is a landing event. It never substitutes for
`RELEASED`, `OPERATING`, `OUTCOME_REVIEW`, or `CLOSED`.
