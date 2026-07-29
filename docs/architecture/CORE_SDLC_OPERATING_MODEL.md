# Ranex Core SDLC Operating Model

| Field | Value |
|---|---|
| Policy ID | `POL-SDLC-001` |
| Version | `1.5.0` |
| Status | `ACCEPTED` |
| Effective date | 2026-07-27 |
| Repository snapshot basis | `bootstrap/pre-upstream`; exact digest/revision is supplied by the review or release source manifest |
| Owner and final authority | Human governor |
| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md); [ADR-0004](./decisions/ADR-0004-establish-initial-quality-attribute-baselines.md); [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md); [ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md) |
| Applies to | Every Ranex product, architecture, code, configuration, data, security, release, operation, documentation, and upstream-sync change |
| Research basis | [Real-world SDLC operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md) |
| Major engineering references | [Ranex Engineering Reference Application Map](./ENGINEERING_REFERENCE_APPLICATION_MAP.md) |
| Architecture | [Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Authority | [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md) |
| Execution subprocess | [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md) |
| Worker control plane | [AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md) |
| Normative control catalog | [SDLC Control Catalog](./SDLC_CONTROL_CATALOG.md) |
| Compatibility | New core policy; existing phase and lifecycle records remain valid and must be mapped |
| Security/data class | Public policy metadata; work/evidence records retain their own classification |
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

The AI-agent lifecycle is the mandatory worker-execution protocol from
qualified work intake through landing and post-landing evidence. Its fleet
control plane governs assignment, leases, liveness, concurrency, budgets,
isolation, handoff, and measurement. Neither is a parallel lifecycle. This
policy remains the parent human product, service, and learning loop.

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
13. Capability ratings diagnose process improvement only. They never authorize
    work or average away a mandatory control, unknown evidence, or active harm.
14. One AI worker is the default. Parallel workers require fenced leases,
    isolated mutable state, verifier backpressure, local measurement, and the
    same human-controlled landing authority.

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
BLOCKED -> <recorded blocked_from_status>
Any pre-release state -> CANCELLED
VERIFICATION -> DEFINITION | DESIGN | IN_PROGRESS
RELEASING -> OPERATING | ROLLED_BACK
OPERATING -> OUTCOME_REVIEW
ROLLED_BACK -> TRIAGE
OUTCOME_REVIEW -> CLOSED | DISCOVERY | DEFINITION
```

Entering `BLOCKED` records `blocked_from_status`, reason code, owner, time,
blocking dependency/evidence, invalidated inputs, and review deadline. Resume
returns only to that recorded nonterminal state after the blocker is resolved
and affected policy/evidence is refreshed; `BLOCKED` is not a generic jump.
Pre-release work may instead be authorized to `CANCELLED`. Release/operating
work uses the release, rollback, or incident lifecycle rather than cancellation
to conceal an active effect. `CANCELLED` and `CLOSED` are terminal for the work
attempt; reopening creates a linked new attempt. History is append-only.

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
| `BLOCKED` | A blocking dependency, decision, conflict, or evidence gap exists; prior state and invalidation set are recorded | Fresh proof resolves the blocker and authorizes return only to `blocked_from_status`, or an allowed terminal/recovery disposition | Work owner |
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
| `CapabilityStatus` | `product_definition` with accountable product/service owner | Supported, deprecated, retirement, and retired product capability |
| `L0`–`L12` | AI-agent lifecycle policy | Activity protocol inside applicable work-item states; never canonical work state |
| `SDLC-*` | Core SDLC control catalog | Per-work and cross-lifecycle controls |
| `AI-G0`–`AI-G10` | AI-agent lifecycle | Exact-subject execution evidence gates; `assurance` owns their `GateEvaluation` records |
| `MAP-*` | Full-system architecture | Map assertions over one immutable `ArchitectureSubject`; no implied `AI-G2` or runtime pass |
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
| `PRODUCT` | User, stakeholder, strategy, experiment | Measurable user/product outcome |
| `DEFECT` | Expected behavior differs from observed behavior | Reproduction and regression evidence |
| `RELIABILITY` | SLO, capacity, toil, recovery gap | Service impact and reliability measure |
| `SECURITY_PRIVACY` | Threat, vulnerability, policy or data gap | Restricted handling, severity and response policy |
| `ARCHITECTURE_PLATFORM` | Fitness failure, dependency, capability or enablement need | Named consumer/outcome; ADR when material |
| `COMPLIANCE_PROVENANCE` | License, SBOM, attribution, supply-chain requirement | Evidence-bound compliance decision |
| `UPSTREAM_SYNC` | Pinned Hermes upstream candidate | Provenance, classification, selective port and anti-recontamination |
| `MAINTENANCE` | Supported capability, dependency, vulnerability, defect or debt | Supported-version and regression policy |
| `RETIREMENT` | Product/capability/version end of life | Consumer, data, access, archive and residual-risk disposition |
| `INCIDENT_RESPONSE` | Active or recent operating impact | Incident linkage, mitigation/recovery evidence and follow-up |

Classes affect routing, not priority automatically. Priority is an explicit
decision using impact, urgency, risk reduction, cost of delay, dependencies,
evidence confidence, and capacity.

`EMERGENCY` is a risk/assurance and service lane, not a work class. An incident
response item may be `EMERGENCY`, `CRITICAL`, or another policy-derived lane.

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

### 5.3 Operational execution paths

Risk lane and execution path are separate. Risk determines assurance depth;
the path determines how much coordination is useful. “Material” does not by
itself require a plan, a Kanban graph, every lifecycle stage, or several model
reviews.

| Path | Eligibility | Minimum engineering flow |
|---|---|---|
| `FAST` | Explicit acceptance; exact local target; reversible; one component; normally at most three files; focused proof exists; no Enhanced/Critical trigger | Direct BUILD, focused deterministic VERIFY, final scope inspection, and real consumer smoke when configuration or visible behavior changes |
| `STANDARD` | Bounded work needing a dependency/API/external-seam/cross-module/design/test-harness choice, without a Critical signal | Optional one concise plan, one implementation owner, focused and applicable regression proof, final fresh technical review only for an acceptance recommendation, and user-level acceptance when visible |
| `CRITICAL` | Any Critical signal in section 5.1 or an Emergency item | Optional one bounded complex plan, smallest implementation slice, triggered negative/real-seam/recovery proof, then independent technical and adversarial review of the same final frozen candidate |
| `QUALIFY` | Missing acceptance or exact target, a conflicting target edit, or a genuinely unresolved owner choice | Resolve only the missing input; do not start BUILD or a planning chain |

`FAST` is a Standard-assurance shortcut, not weakened truth. It is promoted
once when scope grows, proof fails, or a risk signal appears. A generated lock,
checksum, index, or manifest is a derived integrity artifact; when its source
change is authorized, the artifact is regenerated in the same change rather
than treated as a higher decision authority. Unrelated dirty files never block
work. Understood target edits become the current byte-level base; only a real
overlap conflict requires qualification.

For Fast work, goal mode, model planning, graph decomposition, specialist
review, evidence-packet normalization, and release-packet assembly are
prohibited overhead. A Standard task skips planning when acceptance, paths,
and checks already make implementation obvious. Critical HY3 and adversarial
reviews start only after the final candidate is frozen and may run in parallel.
One focused correction/review cycle is the default maximum before escalation.

The initial Fast service target is first useful action within 20 seconds,
median completion within 60 seconds, provisional p95 within 120 seconds, and a
240-second hard stop. These remain calibration targets until the declared
sample threshold is reached; quality and safety qualify a route before speed.

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
- the compiled engineering-practice profile loads only practices applicable to
  the work class, execution path, technology, and risk; Fast work uses the
  accepted compact default rather than repeating a nine-book review, while a
  material applicable `UNKNOWN` still blocks the affected claim;
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
- applicable engineering practices are demonstrated by the exact candidate
  and evidence rather than citation alone, and authorized deviations are
  recorded;
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

The detailed method for applying SWEBOK and every frozen major book reference
to unclear requirements, workflow, architecture, file-structure,
construction, verification, and operations questions is the
[Engineering Reference Application Map](./ENGINEERING_REFERENCE_APPLICATION_MAP.md).
Those references deepen this accepted lifecycle; they do not replace or outrank
it.

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
10. Planning is optional engineering work, not a ritual. A clear Fast change
    executes directly; a clear single-worker Standard item receives a direct
    assignment; only rough multi-stage outcomes are decomposed.
11. An explicit owner decision is direction for implementation within its
    scope. It is not sent to another model for permission. Replanning occurs
    only when requirements, subject, risk, or executed evidence materially
    changes.

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

Select the smallest test set that can falsify the scoped claim at its actual
risk. A literal configuration or documentation change need not invent a new
test harness when parsing, schema/content assertions, and the real consuming
CLI/service provide more direct proof. Test-first development is preferred for
behavior that can be expressed cheaply; it is not a reason to delay a simple
literal correction.

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

The initial service objectives, recovery targets, security baseline, and
retention periods are accepted construction targets in
[ADR-0004](./decisions/ADR-0004-establish-initial-quality-attribute-baselines.md).
Until exact-subject runtime baselines exist:

- label the accepted values `TARGET_NOT_MEASURED`, never achieved fact;
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
- AI-worker false-accept/false-reject calibration, escaped rework, stale lease,
  duplicate assignment, loop termination, mailbox failure, integration
  conflict, and verifier-capacity/backpressure measures;
- user outcome and adoption measures; and
- upstream lag, candidate age and sync regression rate.

Report distributions and trends by value stream and risk lane. Do not use commit
count, lines changed, story points, token use, agent runs, review comments, or
hours online as measures of individual productivity.

Before a measure can affect a decision, its versioned specification records:
goal and question, construct, operational definition/formula, entity and unit,
event source, population, window, exclusions, refresh cadence, data-quality and
uncertainty checks, paired guardrail, owner, threshold/tolerance, and the exact
decision or action it can trigger. A measure with no decision use is removed.

### 15.1 Capability assessment

Ranex assesses each applicable normative control or named capability for one
declared value stream/service, work class, risk-lane set, policy/rubric version,
and review window. It does not publish one compensating process-maturity score.

Each assessment reports four separate fields:

1. **Capability rating:** `result` is `NOT_ASSESSED`, `UNKNOWN`,
   `NOT_APPLICABLE`, or `SCORED`; only `SCORED` has a `level` from `0`–`4`.
2. **Effectiveness:** `UNKNOWN`, `REGRESSING`, `MIXED`, or `MEETS_TARGET`.
3. **Coverage:** included/eligible counts and percentage, stratified by work
   class and risk lane.
4. **Confidence:** `LOW`, `MEDIUM`, or `HIGH`, with evidence-quality rationale.

When `result` is not `SCORED`, `level` is absent. `NOT_ASSESSED` and `UNKNOWN`
have no numeric value and are never passes.
`NOT_APPLICABLE` requires a predeclared applicability rule, reason, and
accountable approval; it is invalid when eligible work or a qualifying trigger
exists in the review window. Ambiguous applicability produces `UNKNOWN`, not
`NOT_APPLICABLE`.
Published profiles expose N/A counts/rates and independent assurance samples
their dispositions. Capability, effectiveness, coverage, and confidence must
not be averaged together.

The `0`–`4` levels are ordinal labels. Ordering and counts by label are allowed;
addition, arithmetic distance, weighting, means, standard deviations, ratios,
and a process-wide “overall score” are not. Counts and ordering may describe one
value stream/profile over time; they cannot become cross-team league tables.

| Level | Label | Minimum evidence anchor |
|---:|---|---|
| `0` | `ABSENT` | Assessment proves that the required owner, contract, behavior, or trustworthy evidence is absent or unsafe |
| `1` | `DEFINED` | Versioned purpose, owner, scope, entry/exit, evidence, authority, failure route, tailoring, exception, and metric definitions exist |
| `2` | `OPERATED` | Representative real work produces durable exact-subject evidence; at least one rejection, invalidation, exception, or backward path was actually traversed and recorded rather than merely documented |
| `3` | `CONTROLLED` | Declared lanes/windows are governed; coverage, distributions, false passes, misses, exceptions, and triggered responses are reviewed |
| `4` | `IMPROVING` | A prospectively frozen experiment shows sustained benefit above declared uncertainty/local measurement noise across more than one review window without degrading paired guardrails; infrastructure faults are separated from subject failures |

A level is awarded only when that level and every lower anchor are supported.
Documentation alone cannot exceed `1`. Profile `VITAL-SDLC-001` is a versioned
set of exact `(domain, control, applicability rule)` tuples owned by the human
governor; the tuple table is normative in `SDLC-MEA-002`. A team cannot add,
remove, remap, or reclassify a tuple inside an assessment.

Every applicable control and architecture capability receives its own immutable
assessment row; there is no compensating “overall architecture score.” Until a
schema-valid `CapabilityAssessment` and complete domain projection bind real
evidence, the honest result is `NOT_ASSESSED` (or `UNKNOWN` where evidence was
attempted but remains insufficient), with no numeric level. The accepted ADRs
and prose can support at most a future `DEFINED` (`1`) result; they do not award
that result by themselves.

A domain projection binds one immutable assessment ID, revision, and digest for
every tuple, all at an identical scope and review window. Missing, duplicate,
extra, rule-mismatched, stale, or cross-scope rows invalidate the projection.
An applicable member is a tuple whose applicability resolved to `APPLICABLE`;
a valid N/A tuple remains in the complete projection but is excluded from the
floor. For a valid projection, unresolved applicability produces `UNKNOWN`; all
registered controls validly N/A produces `NOT_APPLICABLE`; all applicable
member ratings `NOT_ASSESSED` produces `NOT_ASSESSED`; after any begins, one
applicable `UNKNOWN`/`NOT_ASSESSED` member produces `UNKNOWN`; and a domain is
`SCORED` if and only if every applicable member is `SCORED`. Its level is the
lowest supported applicable-member level. Report the complete projection and
weakest capabilities, never an average that can conceal a mandatory failure.

Assessors require evidence of enacted practice, durable artifact/provenance,
and outcome/guardrail behavior in proportion to the claimed level. A favorable
outcome without the control does not prove capability. Test coverage, document
count, lines of code, class size, and similar proxy counts locate questions;
they are not direct quality or release verdicts. Failed required tests and
disabled safeguards remain non-compensating findings.

All population and coverage values come from one immutable population
snapshot. Joint work-class/risk-lane strata—including zero-count strata—must
cover the declared scope. In every stratum and in total,
`eligible = included + excluded`; strata sum to totals, and itemized exclusions
sum to the excluded count. Applicability and coverage point to that same
snapshot/query and cannot carry separate, contradictory copies.

Adverse populations are typed predicates, not a mixed “class” field: failed
control/execution outcomes, `BLOCKED`/`CANCELLED`/`ROLLED_BACK` status history,
reopened attempt history, and the `EMERGENCY` risk lane remain distinct. Each
records an immutable query digest and eligible/included/excluded counts. An
assessment cannot become `SCORED` unless every applicable adverse category
includes all eligible subjects with zero exclusions.

Confidence follows a versioned adequacy rule, not free text alone. `HIGH`
requires all predeclared sample, duration, representativeness, authenticity,
freshness, missingness, and data-quality tests to pass plus independent
assurance sign-off. Missing an approved adequacy rule caps confidence at
`MEDIUM`; a material unresolved evidence or population gap makes it `LOW`.
One complete gap register gives every known evidence, applicability,
population, coverage and measurement gap a materiality and resolution
disposition; `HIGH` is invalid if the inventory is incomplete or a material
gap is unresolved. Any unresolved material gap forces capability result
`UNKNOWN`, no level, and confidence `LOW`; it cannot coexist with `SCORED`.

Capability ratings diagnose the process only. They cannot authorize a work-item
transition, issue a permit, waive a control, lower a risk lane, change a gate
outcome, or rank an individual/team. Exact-work evidence and named authority
remain decisive.

### 15.2 Improvement selection

Improvement priority is non-compensating:

| Priority | Trigger | Response |
|---|---|---|
| `P0 — CONTROL_NOW` | Active harm or a non-tailorable invariant/truth/authority/evidence/recovery breach | Stop or contain the effect, restore control, preserve evidence, and open corrective work |
| `P1 — IMPROVE_NEXT` | Result `NOT_ASSESSED`/`UNKNOWN`; level `0`/`1`; overdue critical obligation; repeated escape; high-exposure downstream blockage; or `LOW`-confidence instrumentation need | Assign an accountable owner and begin bounded corrective or instrumentation work |
| `P2 — IMPROVE_DELIBERATELY` | Absent P0/P1: level `2`; `UNKNOWN`/`REGRESSING`/`MIXED` effectiveness; material queueing/rework/instability/outcome harm; or another unproven P3 condition | Run a measured experiment in the earliest causal stage |
| `P3 — SUSTAIN` | Absent P0–P2: level `3`/`4`, `MEETS_TARGET`, passing coverage/adverse-population reconciliation, healthy guardrails, no adverse trend, and confidence above `LOW` | Monitor, simplify, share learning, and prevent regression |

Priority follows `PRIORITY-SDLC-001`: evaluate `P0 -> P1 -> P2 -> P3`, and the
first matching tier wins. Within a tier, order by consequence, exposure,
recurrence, downstream blocking, and then capability gap. `LOW` confidence
selects P1 and requires an instrumentation/sampling work item; it never lowers
priority or supports `P3`. A valid all-N/A assessment has no tier. A domain
projection takes the highest-precedence member tier, never a numeric average.

Every improvement is a linked governed work item that records the causal stage
and control, evidence and baseline, hypothesis, bounded change, versioned metric
specification, fixed comparator, primary measure, paired guardrails,
prospectively frozen decision rule, owner, evidence window, minimum meaningful
and detectable effect, declared uncertainty/local noise, harness/configuration
version, separate infrastructure-error count where relevant, stop/revert
criteria, and retain/change/revert decision. An action is complete only after
effectiveness is checked. An unresolved or below-noise result cannot raise the
capability level.

The measurement system is itself assessed through `SDLC-MEA-001`,
`SDLC-MEA-002`, and `SDLC-PA-001`. A level-`3` or level-`4` claim requires one
immutable measurement-design digest that binds the metric specification and
qualified harness ID, version, configuration digest, and qualification
evidence. An experiment supporting level `4` references the same exact design
or another equally complete immutable design; duplicated unbound fields cannot
substitute for that reference. Local noise may never be silently assumed to be
zero: an established zero floor needs method evidence and independent
claim-specific approval. `NOT_APPLICABLE` uncertainty is limited to a
deterministic measure and needs the exact approved uncertainty-N/A rule and
approval.

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

Adoption gates are binary evidence claims, not percentages. `SDLC-ADOPT-A` can
support level `1` for registered controls; `SDLC-ADOPT-B/C` can support level
`2` only for capabilities actually demonstrated; `SDLC-ADOPT-D` plus repeated
real operation can support level `3`; `SDLC-ADOPT-E` calibrates that operation.
Level `4` additionally requires a later verified improvement experiment.

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
- Complete the first evidence-bound capability profile without converting
  `NOT_ASSESSED` or `UNKNOWN` into zero/pass.
- Bind every immutable per-control assessment into an exact,
  same-scope/same-window `VITAL-SDLC-001` domain projection; prove tuple
  completeness, N/A rules, population/stratum reconciliation, typed adverse
  queries, and all seven confidence-adequacy tests.
- Apply `PRIORITY-SDLC-001` and register the highest-precedence bounded
  corrective, instrumentation, or improvement work.
- Register its operational metric definitions, comparator, prospective decision
  rule, immutable measurement-design digest, harness ID/version/configuration
  qualification, uncertainty/noise method and approvals, and
  infrastructure-error accounting.
- Review this policy after both tracers and record changes through an ADR.

### SDLC-ADOPT-FLEET-A through F — AI-worker scaling profile

The fleet-control profile is subordinate to Gates A–E. It proves, in order:

1. typed assignment/lease/budget/topology contracts;
2. one-worker packet-to-cleanup behavior and measurement baseline;
3. atomic claim, fencing, liveness, isolation, budget, mailbox, and crash
   safety;
4. verifier/hidden-evidence capacity and backpressure;
5. a locally measured topology that beats the strongest relevant control
   beyond uncertainty; and
6. learned-control quarantine and non-self-activation if learned orchestration
   is ever selected.

The detailed evidence contracts are in the
[AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md).
Failure returns to the last proven configuration; it does not justify weaker
assurance or redefine the Core SDLC.

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
- capability assessments expose rating result/level, effectiveness, coverage,
  rule-derived confidence, and a complete immutable domain projection of the
  owner-registered vital controls without a compensating overall score;
- eligible work cannot be hidden through N/A, population exclusions, or
  self-asserted confidence, and aggregate/stratum/adverse counts reconcile;
- decision-bearing measures have operational definitions and named decisions;
- prioritized improvements have a hypothesis, fixed comparator, prospectively
  frozen decision rule, immutable qualified-harness design, uncertainty/noise
  method and required approval, guardrail, owner, review window, separate
  infrastructure-error accounting where relevant, and checked effectiveness;
- exceptions expire and cannot forge pass evidence; and
- the human governor accepts end-to-end tracer evidence.
