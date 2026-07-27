# Ranex Core SDLC Operating Model

| Field | Value |
|---|---|
| Policy ID | `POL-SDLC-001` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Effective date | 2026-07-27 |
| Owner and final authority | Human governor |
| Owner decision | [ADR-0001: Established Software-Development Lifecycle Governs AI Work](./decisions/ADR-0001-established-sdlc-governs-ai-work.md) |
| Applies to | Every Ranex product, architecture, code, configuration, data, security, release, operation, documentation, and upstream-sync change |
| Research basis | [Real-world SDLC operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md) |
| Architecture | [Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Authority | [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md) |
| Execution subprocess | [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md) |
| Normative control catalog | [SDLC Control Catalog](./SDLC_CONTROL_CATALOG.md) |
| Compatibility | New core policy; existing phase and lifecycle records remain valid and must be mapped |
| Review cycle | After the first two end-to-end trials, then quarterly |

## 1. Policy decision

This operating model is Ranex’s core process. All work moves through one
evidence-bound value stream from signal to outcome:

```text
GOVERN
  -> SHAPE
  -> DISCOVER
  -> SPECIFY
  -> DESIGN
  -> PLAN
  -> BUILD
  -> VERIFY
  -> RELEASE
  -> OPERATE
  -> MAINTAIN OR RETIRE
  -> IMPROVE
  -> GOVERN
```

The process is iterative and risk-proportionate. Stages state what must become
true; they are not departments, mandatory meetings, or fixed-duration phases.
Feedback may return work to an earlier state with a recorded reason and
downstream invalidation.

The existing AI-agent lifecycle is the mandatory execution protocol from
qualified work intake through landing and post-landing evidence. This policy
adds the human product, service, and learning loop around it.

AI agents are workers inside this process. They may perform bounded activities
for a named role, but they do not supply a replacement software-development
method, own the lifecycle, or replace accountable product, engineering,
security, service, and release decisions.

## 2. Non-negotiable invariants

1. Every change has one stable work-item ID, owner, exact subject, desired
   outcome, risk lane, and current state.
2. Every production behavior traces backward to an owned need and forward to
   verification and operational evidence.
3. Product validation and engineering verification are separate and both are
   visible.
4. Security, privacy, reliability, accessibility, operability, provenance, and
   upstream compatibility are lifecycle concerns, not final review add-ons.
5. Work is sliced into the smallest valuable, testable, reversible vertical
   increment.
6. Main is kept releasable. Deployment, feature exposure, data migration, and
   destructive cleanup are separately governed effects where practical.
7. A state transition is made only from required evidence and authority. A
   board movement, comment, model verdict, or meeting does not create authority.
8. Risk changes assurance depth, not truthfulness, traceability, or authority.
9. A material input or exact-subject change invalidates dependent evidence.
10. Models may propose and execute bounded work; they may not own outcomes,
    lower risk, waive controls, accept architecture/risk, merge, release, or
    close their own missing evidence.
11. Incidents, vulnerabilities, defects, user feedback, and upstream changes
    re-enter the same governed stream.
12. Metrics improve the value stream and product. They must not rank people.

## 3. Canonical work-item state machine

```text
FUNNEL
  -> TRIAGE
  -> DISCOVERY
  -> DEFINITION
  -> DESIGN
  -> READY
  -> IN_PROGRESS
  -> VERIFICATION
  -> RELEASE_READY
  -> RELEASING
  -> OPERATING
  -> OUTCOME_REVIEW
  -> CLOSED

Any active state -> BLOCKED
Any pre-release state -> CANCELLED
VERIFICATION -> DEFINITION | DESIGN | IN_PROGRESS
RELEASING -> OPERATING | ROLLED_BACK
OPERATING -> OUTCOME_REVIEW
ROLLED_BACK -> TRIAGE
OUTCOME_REVIEW -> CLOSED | DISCOVERY | DEFINITION
```

`BLOCKED`, `CANCELLED`, and `ROLLED_BACK` require reason codes, owner, time, and
evidence. History is append-only. Reopening creates a new attempt linked to the
earlier one.

Incident, release/deployment, supported-capability, maintenance, and retirement
lifecycles are separate axes with separate owners. An incident, maintenance
need, or retirement trigger creates a linked work item in `FUNNEL` or `TRIAGE`;
it does not add an undeclared state to this work-item aggregate.

### 3.1 State contracts

| State | Required entry | Required exit evidence | Accountable authority |
|---|---|---|---|
| `FUNNEL` | A signal exists | Source, summary, reporter, observed date | Intake owner |
| `TRIAGE` | Signal is recorded | Ownership, class, urgency, initial risk, disposition | Product/duty owner |
| `DISCOVERY` | Problem merits investigation | Users/actors, current behavior, evidence, hypothesis, unknowns | Product owner |
| `DEFINITION` | Problem is sufficiently supported | Outcome measure, requirements, non-goals, constraints, acceptance examples | Product + technical owner |
| `DESIGN` | Defined need is feasible to explore | Design, alternatives, interfaces, data/security/ops impact, test/release/rollback strategy | Technical owner; ADR authority when required |
| `READY` | Design is accepted at required depth | Vertical slices, dependencies, capacity, task/decision inputs, Definition of Ready | Delivery owner |
| `IN_PROGRESS` | One slice is committed | Exact task packet, implementation, tests/docs, run result and handoff | Maker within granted authority |
| `VERIFICATION` | Exact candidate exists | Independent review, required checks, resolved findings, candidate evidence | Deterministic gate + named human authority where required |
| `RELEASE_READY` | Candidate is verified | Immutable artifact, manifest/SBOM, migration, rollback, runbook, comms, observation gates | Release authority |
| `RELEASING` | Valid release permit exists | Deployment/installation events, progressive evaluation, completion or rollback | Release operator |
| `OPERATING` | Release is live/installed | Health, SLO/support/security/recovery evidence for the observation window | Service owner |
| `OUTCOME_REVIEW` | Enough outcome evidence exists or deadline reached | Actual vs expected result, side effects, keep/change/remove decision | Product owner |
| `CLOSED` | Product and operational decision made | Reconciled records, owned follow-ups, docs and decision status current | Work owner |
| `BLOCKED` | A blocking dependency, decision, conflict, or evidence gap exists | Blocker resolved or an allowed terminal disposition is authorized | Work owner |
| `CANCELLED` | Authorized pre-release cancellation | Reason, impact, retained evidence, cleanup and follow-up ownership | Product/work owner |
| `ROLLED_BACK` | Release rollback was initiated | Prior safe state verified, impact bounded, new triage item linked | Release + service owner |

### 3.2 Aggregate and gate namespaces

The core work-item state machine and the execution runtime are different
aggregates:

| Namespace | Owner | Meaning |
|---|---|---|
| `WorkItemStatus` | `work_management` | Product-to-production lifecycle above |
| `RunStatus` | `governed_execution` | One bounded execution attempt serving a work item |
| `IncidentStatus` | `operations` | Detection, mitigation, recovery, review, and action tracking |
| `ReleaseStatus` | `release_management` | Build, readiness, rollout, rollback, operation, withdrawal |
| `CapabilityStatus` | Product/service owner through `work_management` | Supported, deprecated, retirement, and retired product capability |
| `L0`–`L12` | AI-agent lifecycle policy | Activity protocol inside applicable work-item states; never canonical work state |
| `SDLC-*` | Core SDLC control catalog | Per-work and cross-lifecycle controls |
| `AI-G0`–`AI-G10` | AI-agent lifecycle | Evidence gates for an agent-assisted execution |
| `MAP-*` | Full-system architecture | Architecture-map completeness gates |
| `SDLC-ADOPT-*` | This policy | Gates for implementing and calibrating the process itself |

A work item may own many runs. A successful run does not by itself make the
work item `VERIFICATION`, `RELEASE_READY`, `OPERATING`, or `CLOSED`.
`governed_execution` emits exact-subject execution facts; an authorized
`work_management` transition evaluates those facts plus the applicable product,
technical, security, service, release, and human decisions.

Cross-aggregate updates use typed integration events and idempotent commands.
They do not pretend to be one distributed transaction. Failure leaves the
receiving aggregate unchanged and enters visible retry/reconciliation.

## 4. Work classes and service policy

Each item has exactly one primary class:

| Class | Starts from | Special obligation |
|---|---|---|
| Product | User, stakeholder, strategy, experiment | Measurable user/product outcome |
| Defect | Expected behavior differs from observed behavior | Reproduction and regression evidence |
| Reliability | SLO, incident, capacity, toil, recovery gap | Service impact and reliability measure |
| Security/privacy | Threat, vulnerability, policy or data gap | Restricted handling, severity and response policy |
| Architecture/platform | Fitness failure, dependency, capability or enablement need | Named consumer/outcome; ADR when material |
| Compliance/provenance | License, SBOM, attribution, supply-chain requirement | Evidence-bound compliance decision |
| Upstream sync | Pinned Hermes upstream candidate | Provenance, classification, selective port and anti-recontamination |
| Emergency | Active material impact needing immediate mitigation | Emergency lane, retrospective evidence and follow-up |
| Maintenance | Supported capability, dependency, vulnerability, defect or debt | Supported-version and regression policy |
| Retirement | Product/capability/version end of life | Consumer, data, access, archive and residual-risk disposition |

Classes affect routing, not priority automatically. Priority is an explicit
decision using impact, urgency, risk reduction, cost of delay, dependencies,
evidence confidence, and capacity.

## 5. Risk and assurance lanes

The policy engine derives the lane. The maker may only propose a higher lane.

### 5.1 Critical signals

Any of these normally makes work `CRITICAL`:

- identity, authorization, permits, secrets, sandbox, or trust boundary;
- destructive or irreversible user/data effect;
- schema migration with material loss or rollback risk;
- personal/sensitive data or new data egress;
- release/update, provenance, signing, installer, or supply-chain authority;
- workflow/evidence/gate semantics or canonical state ownership;
- backup, restore, reconciliation, or disaster recovery;
- untrusted extension gaining capability;
- public compatibility break or broad upstream port; or
- active exploited vulnerability.

### 5.2 Lane controls

| Control | Standard | Enhanced | Critical | Emergency |
|---|---|---|---|---|
| Requirements | Outcome + acceptance examples | Full requirement set | Full + misuse/failure/recovery cases | Mitigation objective |
| Design | Inline note if non-obvious | Design record | RFC/ADR + threat/data/ops analysis | Minimal safe design |
| Review | Peer/fresh review | Independent review | Independent + specialist/adversarial | Second person when available |
| Verification | Focused deterministic checks | Relevant full suites + seams | Recovery/security/migration/real-seam proof | Targeted safety checks |
| Release | Reversible standard path | Release and rollback plan | Explicit human permit + progressive gates | Incident authority + time limit |
| Follow-up | Sampled outcome review | Required | Required | Mandatory retrospective normalization |

Emergency handling never changes facts to `PASS`. Any temporarily missing
evidence becomes a time-bounded exception owned by a human and a new critical
follow-up item.

## 6. Definitions

### 6.1 Definition of Ready

An item may enter `READY` only when:

- its problem, target users/actors, outcome, owner, and non-goals are clear;
- requirements and acceptance examples are testable;
- risk lane and affected bounded contexts are derived;
- material unknowns have experiments or are explicitly accepted;
- security, data, accessibility, reliability, operations, provenance, and
  upstream impact are addressed in proportion to risk;
- design/ADR obligations are satisfied;
- dependencies and rollout/rollback approach are understood;
- the item is a bounded vertical slice; and
- the required decision and evidence authorities are named.

### 6.2 Definition of Verified

An exact candidate is `VERIFIED` only when:

- requirements trace to tests or explicit evidence;
- required code, configuration, contracts, migrations, tests, docs, telemetry,
  runbooks, and generated artifacts agree;
- independent review requirements are met;
- security, architecture, data, compatibility, and provenance gates pass;
- test selection is non-empty, relevant, and bound to the exact subject;
- findings are resolved or explicitly human-accepted within policy;
- rollback/recovery claims have appropriate proof; and
- no maker self-approval is counted.

### 6.3 Definition of Released

A version is `RELEASED` only when:

- the released artifact is the verified artifact;
- manifest, provenance, dependency and SBOM evidence are bound to it;
- migration, install/update and rollback instructions are executable;
- release notes and operator/user communication are ready;
- credentials and destinations are correct without exposing secrets;
- progressive exposure or observation gates pass; and
- canonical release state records completion or rollback.

### 6.4 Definition of Closed

An item is `CLOSED` only when:

- post-release health and support obligations are satisfied;
- expected and actual outcomes were compared or a dated measurement owner is
  recorded;
- incidents, defects, debt, cleanup, experiment removal, and documentation
  follow-ups have owners and priorities;
- architecture/contracts/ADRs reflect reality;
- temporary permissions, flags, compatibility paths, and worktrees are
  reconciled; and
- evidence is durable and queryable.

Merge alone satisfies none of `RELEASED`, `OPERATING`, or `CLOSED`.

## 7. Requirements and design playbook

### 7.1 Product definition

Each material item records:

- problem and evidence;
- affected user/actor and current journey;
- desired outcome and baseline;
- hypothesis and earliest falsifying evidence;
- functional behavior as examples;
- quality attributes and service expectations;
- constraints, dependencies and non-goals;
- misuse, failure and recovery cases;
- telemetry and outcome measurement;
- rollout, compatibility and removal strategy; and
- unknowns with owners and expiry.

Prefer executable examples:

```text
Given <starting state and authority>
When <actor performs behavior>
Then <observable result>
And <state/effect/evidence invariant>
```

### 7.2 Design record

A design must cover, at required depth:

- bounded context and public API;
- state and effect owner;
- dependency direction;
- data classification, retention and migration;
- threat model and authority path;
- failure, retry, idempotency, cancellation and reconciliation;
- observability, SLI/SLO and support;
- alternatives and rejected trade-offs;
- test architecture and real seams;
- deployment, feature exposure, rollback and removal; and
- Hermes upstream/compatibility impact.

An accepted ADR is required when the source-of-truth policy says so. Design
prose cannot silently override a machine contract.

## 8. Planning and flow policy

1. Maintain one visible portfolio with separate classes of service.
2. Replenish `READY` from evidence and capacity, not stakeholder volume.
3. Limit work in progress. Initial default: one implementation item per maker
   and no more than two active items per accountable technical owner.
4. Split by user-visible behavior and risk boundary, not repository layer.
5. Prefer a change independently releasable within days. Larger work uses a
   parent outcome with separately verified vertical slices.
6. Aging work is reviewed before new work is started.
7. Blocked time and cause are recorded; a blocked item does not disappear from
   WIP reporting.
8. Reserve explicit capacity for reliability, security, architecture health,
   maintenance, and upstream sync. The human governor sets percentages after
   observing demand; agents do not borrow protected capacity silently.
9. Sprints or milestones may be planning projections. Canonical state comes
   from evidence-backed work events.

## 9. Build and integration playbook

- Use an isolated named worktree and exact base.
- Keep each candidate bounded and reviewable.
- Integrate continuously against current main; requalify stale candidates.
- Tests are changed with behavior. Weakening a test requires an accepted
  requirement or defect in the test.
- Use deterministic formatting, generation, schema and dependency checks.
- Pin and verify dependencies; record provenance and licenses.
- Protect secrets and development infrastructure under NIST SSDF-aligned
  controls.
- Use expand/migrate/verify/contract for incompatible data/schema changes.
- Separate code deployment from feature activation when doing so reduces risk.
- Do not mix unrelated cleanup into a feature or emergency change.
- Record actual commands, failures, limitations and omissions.

The detailed maker, handoff, review, verification, permit and landing rules are
defined by the AI-Agent Development Lifecycle.

## 10. Verification strategy

Verification uses a risk-based test portfolio:

| Layer | Purpose |
|---|---|
| Static/contracts | Syntax, types, schemas, generated views, dependencies, policy and provenance |
| Unit/property | Domain rules, invariants, boundaries and broad input behavior |
| Integration/contract | Ports, adapters, storage, providers and compatibility |
| System/journey | User and operator behavior across the assembled release |
| Security/adversarial | Misuse, capability denial, injection, secret/data and trust boundaries |
| Resilience/recovery | Timeout, retry, crash, cancellation, replay, backup, restore, rollback |
| Migration/update | Upgrade/downgrade, upcasting, compatibility and selective upstream porting |
| Release/production | Smoke, canary/progressive evaluation, telemetry and rollback trigger |

Quality gates must be fast enough for their feedback purpose. Slow suites may be
staged, but no required suite is relabeled optional merely because it is slow.
Flaky tests are defects; they cannot create trusted pass evidence.

## 11. Release and change-management playbook

1. Build once from a pinned commit; promote the same immutable artifact.
2. Bind manifest, configuration schema, dependencies, provenance, SBOM,
   migrations, release notes and evidence.
3. Predeclare health, halt and rollback criteria.
4. Back up and prove the required recovery point before a risky migration.
5. Use the smallest safe initial exposure; compare candidate and control where
   applicable.
6. Separate install/deploy success from service and product success.
7. Expand exposure only from observed evidence.
8. Halt automatically on deterministic safety thresholds; permit human halt at
   any time.
9. Rollback or roll forward using the predeclared strategy. Never improvise a
   destructive recovery without new authority.
10. Verify the released subject and reconcile canonical state after completion.

For the initial one-host Ranex deployment, “progressive” may mean a disposable
project, shadow/dry-run mode, a feature flag, a limited profile, or a
time-bounded operator trial rather than traffic percentage.

## 12. Operate, incident, and improve playbook

### 12.1 Service ownership

Every released capability has:

- a service/capability owner and backup;
- user journey and critical dependency map;
- SLIs and initial SLO or an explicit `UNKNOWN` with a measurement plan;
- dashboards and actionable alerts;
- support and escalation path;
- incident, backup, restore and reconciliation runbooks;
- capacity, cost and provider-limit view; and
- end-of-life/removal path.

### 12.2 Incident flow

```text
DETECTED
  -> ACKNOWLEDGED
  -> MITIGATING
  -> MITIGATED
  -> RECOVERY_VERIFIED
  -> REVIEWED
  -> ACTIONS_TRACKED
```

During an incident, protect people and users first: establish command, bound
impact, preserve evidence, communicate, mitigate, recover, and verify. Root
cause analysis follows stabilization.

Reviews are blameless about people and exact about system and process
conditions. Actions must have owners, due policy, verification, and linkage to
normal work. Recurrence and action aging are reviewed.

### 12.3 Reliability policy

After real baselines exist, each material service adopts SLIs, SLOs, and an
error-budget policy. Until then:

- label reliability targets `UNKNOWN` or `PROPOSAL`, never invented fact;
- collect user-centered availability, correctness, latency and durability
  signals;
- freeze nonessential risky releases when evidence shows the service is
  unstable;
- prioritize recovery, observability and defect work when repeated releases
  cause harm; and
- record the human decision that resumes normal release flow.

### 12.4 Improvement loop

Improvement sources include outcome reviews, incidents, defects, security
findings, support, flow metrics, architecture fitness, dependency changes,
upstream changes and retrospectives.

Every proposed lesson is quarantined until:

- source evidence and scope are known;
- privacy/secrets are removed;
- the lesson is reviewed;
- a policy, architecture, test, runbook, or backlog change is named; and
- the appropriate human accepts it.

No model automatically changes prompts, policy, gates, knowledge, or routing
from production telemetry.

## 13. Upstream Hermes synchronization

Upstream synchronization is a specialized core-SDLC work class:

```text
observe upstream
  -> pin candidate commit/range
  -> classify provenance, license, security and behavior
  -> map to Ranex owner and compatibility obligation
  -> accept, reject, defer scheduling, or selectively port
  -> implement in isolated sync worktree
  -> run architecture, de-commercialization, compatibility and regression gates
  -> release through the normal path
  -> record new upstream baseline and disposition
```

No upstream merge, dependency update, generated artifact, or commercial/
privileged behavior bypasses normal review and release authority. Retain upstream
history and attribution.

## 14. Decision rights

| Decision | Accountable authority |
|---|---|
| Problem priority and desired product outcome | Product owner/human governor |
| Requirement acceptance | Product owner + affected technical/service owner |
| Architecture and machine-contract change | Human governor through RFC/ADR policy |
| Risk lane | Policy engine; human governor resolves exceptional ambiguity |
| Implementation approach within accepted boundaries | Maker/technical owner |
| Deterministic conformance | Qualified checker/gate |
| Review finding validity | Review lifecycle plus evidence/human escalation |
| Security/data risk acceptance | Human governor and named affected owner |
| Merge/landing | Human-controlled authority under active policy |
| Release/rollback | Human release authority; operator acts under permit |
| Incident priorities | Incident commander within policy |
| Outcome continuation/change/removal | Product owner/human governor |
| Process-policy change | Human governor through versioned policy/ADR |

## 15. Metrics

The canonical event stream derives:

- end-to-end idea lead time and committed change lead time;
- cycle time, work age, WIP, blocked time and flow efficiency;
- deployment frequency;
- change fail rate and deployment rework rate;
- failed deployment recovery time;
- escaped defect and rollback rate;
- SLO/error-budget performance when established;
- incident recurrence and action age;
- vulnerability age and remediation time;
- evidence completeness, exception age, review/gate wait;
- user outcome and adoption measures; and
- upstream lag, candidate age and sync regression rate.

Report distributions and trends by value stream and risk lane. Do not use commit
count, lines changed, story points, token use, agent runs, review comments, or
hours online as measures of individual productivity.

## 16. Process conformance and exceptions

A transition service must eventually enforce:

- allowed source/target state;
- required roles and separation;
- risk-lane artifacts and gates;
- exact-subject and evidence freshness;
- invalidation dependencies;
- human decisions and permits;
- reason codes, deadlines and exception expiry; and
- append-only transition evidence.

Until that service exists, templates and human review apply the same policy.

An exception:

- names the exact requirement being waived;
- cannot convert missing/failing evidence into a pass;
- states reason, scope, risk, compensating control, owner and expiry;
- is unavailable for legal falsehood, secret exposure, cross-project access or
  forged evidence;
- creates follow-up work where residual risk remains; and
- is reviewed at expiry.

## 17. Cadence and process ownership

Minimum cadence:

- continuous intake, CI, security and incident response;
- active-flow check at least each working day;
- weekly replenishment, dependency/risk and upstream review;
- readiness and observation for every release;
- monthly product outcome, architecture, security, reliability and flow review;
- quarterly strategy, SLO/error-budget, capacity and process review; and
- learning review after material incidents.

Records may be asynchronous. Meetings are required only when synchronous human
judgment materially improves the decision.

The human governor owns this policy. The delivery owner maintains its operation.
Product, technical, service, security/data and release owners maintain their
respective controls. Proposed changes use the source-of-truth RFC/ADR workflow.

## 18. Process-adoption gates

These `SDLC-ADOPT-*` gates govern adoption of this operating model. They are not
per-work quality gates and do not share IDs with `AI-G*`, `MAP-*`, runtime gate
outcomes, or human decision points.

### SDLC-ADOPT-A — Contract

- Register work classes, states, transitions, risk lanes, reason codes, roles,
  artifacts and invalidation rules.
- Validate that no agent role owns its own acceptance or release.

### SDLC-ADOPT-B — Manual tracer

- Complete one bounded documentation change through the full record.
- Exercise rejection and a backward transition.

### SDLC-ADOPT-C — Runtime tracer

- Complete one small Ranex runtime behavior from problem to operated outcome.
- Prove exact-subject evidence, rollback, observation and outcome review.

### SDLC-ADOPT-D — Automation

- Enforce transitions, ingest evidence and generate traceability views.
- Prove fail-closed behavior for missing, stale, wrong-subject and conflicting
  inputs.

### SDLC-ADOPT-E — Calibration

- Establish baselines from actual work.
- Accept initial WIP, SLO/error-budget, review, aging and exception policies.
- Review this policy after both tracers and record changes through an ADR.

## 19. Process definition of done

This operating model is implemented—not merely documented—when:

- all included Ranex work enters through the canonical state machine;
- required artifacts and decision rights are machine-registered;
- a query can trace need to code, evidence, release, health and outcome;
- risk lanes demonstrably change assurance depth;
- downstream evidence invalidates when its source changes;
- product, AI-agent execution, release, operation and learning use one work ID;
- incidents, vulnerabilities and upstream candidates follow governed re-entry;
- metrics derive from durable events and include failures;
- exceptions expire and cannot forge pass evidence; and
- the human governor accepts end-to-end tracer evidence.
