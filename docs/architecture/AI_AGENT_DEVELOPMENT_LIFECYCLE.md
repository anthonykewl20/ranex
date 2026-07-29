# Ranex AI-Agent Development Lifecycle

| Field | Value |
|---|---|
| Policy ID | `POL-AI-LIFECYCLE-001` |
| Version | `1.1.0` |
| Status | Normative supporting policy |
| Effective date | 2026-07-27 |
| Repository snapshot basis | `bootstrap/pre-upstream`; exact digest/revision is supplied by the review or release source manifest |
| Applies to | All architecture, code, configuration, migration, security, release, and documentation work |
| Architecture | [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Parent operating model | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Fleet control | [AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md) |
| Authority policy | [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md) |
| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md); [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md) |
| Final authority | Human governor |
| Compatibility/migration class | New worker-control policy; historical agent runs remain evidence and require versioned mappings |
| Security/data class | Public policy metadata; packets and run artifacts are classified independently |
| Review trigger | Any role/authority/gate change, failed independence control, or first two end-to-end tracers |

## 1. Objective

Ranex is designed for development by changing fleets of AI agents. The stable
unit is therefore not a long-lived model persona. The stable unit is a
versioned process with exact inputs, constrained authority, independent review,
deterministic gates, and durable evidence.

The software-development method is not supplied by those agents. The accepted
Core SDLC and control catalog define the work; this document only constrains how
an AI worker may assist or execute an assigned activity inside that work.

This lifecycle is the governed execution subprocess of the
[Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md). The parent
model owns the full human product-to-production loop: problem discovery,
requirements, service outcomes, release operation, and improvement. Entry into
this lifecycle does not prove that upstream product and design work is complete;
L0 must bind the parent work item and its current accepted artifacts. Completion
of this lifecycle returns evidence to the parent `OPERATING`,
`OUTCOME_REVIEW`, and `CLOSED` states rather than treating merge as product
completion.

This lifecycle governs the complete development path:

```text
intake
  -> research
  -> architecture/decision
  -> packet compilation
  -> isolated implementation
  -> submission
  -> independent review
  -> deterministic verification
  -> exact-subject decision and permit
  -> human-controlled landing
  -> post-landing verification
  -> operations evidence and learning quarantine
```

The lifecycle applies to tiny changes and system-wide changes. Risk changes the
depth of evidence and review, not the authority boundary.

## 2. Role model

Roles describe responsibilities and separation constraints. A model name is
never a role ID.

| Role | Responsibility | Prohibited authority |
|---|---|---|
| `human-governor` | Product scope, architecture, risk, credentials, waivers, destructive decisions, landing | Cannot rewrite evidence or bypass subject binding |
| `architecture-synthesizer` | Reconcile research, contracts, reviews, and full-map impact | Cannot self-accept an ADR |
| `architecture-specialist` | Produce or challenge bounded contexts, APIs, state ownership, and file structure | Cannot count as independent approval of its own proposal |
| `planner` | Decompose accepted work into dependency-aware packets | Cannot implement or approve its plan in the same execution identity when independence is required |
| `implementation-worker` | Make bounded changes in one assigned worktree | Cannot lower risk, change its packet, approve, merge, or issue a permit |
| `process-reviewer` | Verify method, scope, dependency, and policy conformance | Cannot edit the reviewed subject |
| `outcome-reviewer` | Evaluate semantic quality and acceptance criteria | Produces observations/evidence, not gate authority |
| `adversarial-reviewer` | Search for boundary, security, concurrency, recovery, and test weaknesses | Cannot mutate or approve the subject |
| `deterministic-verifier` | Run qualified checks and normalize results | Cannot reinterpret a failing checker as pass |
| `release-operator` | Execute an authorized release, rollback, restore, or upstream-sync procedure | Cannot create its own authority or skip gates |

### 2.1 DeepSeek V4 Pro and HY3

For architecture and file-structure work:

- DeepSeek V4 Pro is the primary specialist/co-designer.
- HY3 receives the same frozen evidence independently and acts as the
  cross-family challenger.
- The architecture synthesizer reconciles findings against primary evidence.
- DeepSeek V4 Pro may receive one bounded response round for unresolved
  architecture/file-structure findings.
- HY3 checks the reconciled subject, not the co-designer's confidence.
- Material unresolved disagreement becomes `CONFLICT`.
- The human governor accepts, rejects, or requests another experiment.

DeepSeek V4 Pro's co-design cannot count as independent approval. HY3's review is
also advisory and cannot replace deterministic tests or human authority.

## 3. Independence contract

A review is independent only when the record proves the required properties:

- reviewer execution identity differs from maker identity;
- reviewer did not edit the subject;
- reviewer received the exact candidate commit or artifact digest;
- reviewer saw no implementer rationale before its initial verdict when blind
  review is required;
- reviewer used a separately compiled review packet;
- reviewer had no write or merge capability;
- reviewer model/provider/transport diversity meets active policy;
- hidden fixtures or answer keys remained inaccessible;
- reviewer output and parser versions are recorded; and
- no earlier review is mislabeled as independent after being shown to the
  reviewer.

A fresh chat session alone is not independence.

## 4. Immutable artifacts per handoff

At contract-readiness gate `AI-G2`, each stage produces one machine-schema-valid
artifact. Until the registries and schemas in the target architecture exist,
the files under `templates/` are provisional field specifications, not proof of
schema validation. A tracer must report that control as `UNKNOWN`/not
implemented rather than treating YAML parsing as contract validity.

| Stage | Required artifact |
|---|---|
| Intake | `WorkIntake` |
| Research | `ResearchPacket` and claim/evidence register |
| Architecture | `ArchitectureReviewPacket`, `ArchitectureProposal`, independent challenge, `ArchitectureReconciliation`, ADR |
| Planning | `TaskPacket` |
| Worker allocation | `AgentAssignment`, expiring `DispatchOffer`, immutable `WorkerAttempt`, fenced `WorkerLease`, hierarchical `ResourceReservation`, and durable `MailboxEnvelope` when coordination is used |
| Implementation | `RunResult` and candidate commit |
| Handoff | `AgentHandoff` |
| Review | `ReviewRequest`, one or more `AnalysisAttempt`/`ReviewObservation`, deterministic `IndependenceEvaluation`, `ReviewVerdict` |
| Verification | deterministic `CheckerResult` set, `EvidenceSnapshot`, `GateEvaluation` |
| Human authority | `HumanDecisionRecord`, then governed `ConsumableAuthorityGrant` when executable |
| Transition | `Permit` and `TransitionEvent` |
| Landing | `LandingRecord` |
| Post-landing | `PostLandingVerification` |
| Operations | `ReleaseEvidence`, `OperationEvidence`, `OutcomeReview`, backup/restore/incident/sync evidence |
| Process/fleet calibration | `CapabilityAssessment` plus `FleetExperiment` with controls, uncertainty, raw evidence, limitations, and human decision reference |

No hidden chain-of-thought is required or stored. Agents provide findings,
decisions proposed, evidence, limitations, assumptions, and unknowns.

Artifact ownership is non-overlapping: `analytical_review` owns the review
request/attempt/observation/verdict/independence records; `assurance` owns
claims, evidence envelopes, qualified checker results, exact-subject snapshots,
and `GateEvaluation`; `policy` owns rules/risk/authorization snapshots and
human-decision requirements; `governed_execution` alone owns `RunStatus`,
authority grants, permits, gate binding, transitions, and effects. A consumer
holds an immutable reference, never a second authoritative copy.

## 5. Lifecycle

### 5.0 Mapping to the governing Core SDLC

L0–L12 are activities/protocol phases, not a second state machine. The canonical
work-item state remains owned by `work_management`.

| Core `WorkItemStatus` | Permitted AI lifecycle activity | Required parent authority/output |
|---|---|---|
| `FUNNEL`, `TRIAGE` | L0 may structure an already-authorized intake; L1 may gather bounded facts | Human/duty owner creates/classifies the work item and risk signals |
| `DISCOVERY` | L1 research and bounded experiments | Product owner decides whether the problem is supported |
| `DEFINITION` | L1 requirements evidence; L2 only for decision-shaping exploration | Product/technical/affected owners accept outcome, requirements, constraints and examples |
| `DESIGN` | L1 and L2 architecture/design work | Technical/ADR authority accepts design, risk controls, test/release/rollback strategy |
| `READY` | L3 packet compilation | Delivery owner accepts Definition of Ready; dispatch transition is separately authorized |
| `IN_PROGRESS` | L3 recompilation after invalidation; L4 implementation; L5 submission | Maker produces candidate/evidence but cannot advance the work item |
| `VERIFICATION` | L6 independent review; L7 specialist escalation; L8 checks; L9 gate/decision; L10 landing; L11 landed-subject verification | Qualified gates and named human/V&V authorities decide; landing is an event, not completion |
| `RELEASE_READY`, `RELEASING` | L9 release decision/permit and bounded L12 release-operation evidence | Release authority/operator owns promotion, halt and rollback |
| `OPERATING` | L12 operational evidence, incident/recovery assistance and learning quarantine | Service owner accepts the observation window; incidents use their own aggregate and linked work |
| `OUTCOME_REVIEW` | L12 may prepare product/operational analysis | Product owner makes keep/change/remove decision |
| `CLOSED` | No execution authority; archival/retrieval assistance only | Work owner closes only after evidence and follow-ups reconcile |
| `BLOCKED`, `CANCELLED`, `ROLLED_BACK` | Only explicitly authorized diagnosis, cleanup, recovery or new-packet activity | `BLOCKED` resumes only to its recorded prior state after refreshed proof; terminal/recovery routes remain Core-SDLC-owned |

One work item may invoke many AI runs, and one run may implement only one
activity. `RunStatus=SUCCEEDED`, a merge, or an `AI-G*` pass never implies a
Core-SDLC state transition.

### 5.1 L0 — Intake and qualification

Record:

- project and work-item identity;
- current Core-SDLC work-item state, work class, and derived risk-lane decision;
- requester and decision owner;
- product, technical, service, security/data, delivery, V&V, configuration, and
  release owners when applicable;
- exact base revision;
- objective and user outcome;
- outcome-measure, requirement, acceptance-criterion, and traceability IDs;
- explicit non-goals;
- affected capabilities and data classes;
- reversibility and external effects;
- initial risk signals;
- required decisions;
- target full-map zones; and
- acceptance criteria.

The system derives risk from policy, affected capability, data classification,
deployment surface, dependency/migration impact, reversibility, and
uncertainty. Worker-provided risk is advisory only.

Exit gate:

- subject is exact;
- project exists and is isolated;
- objective/non-goals are unambiguous enough to research;
- required human decisions are identified; and
- no forbidden or destructive action has been implicitly authorized.

### 5.2 L1 — Research

Research order:

1. inspect exact local source and runtime evidence;
2. inspect accepted architecture, contracts, and ADRs;
3. inspect exact upstream/pinned source;
4. consult official specifications and primary sources;
5. use secondary synthesis only when primary evidence is unavailable; and
6. ask advisory models to challenge, not manufacture, evidence.

Every material claim is labeled:

- `FACT`;
- `INFERENCE`;
- `PROPOSAL`;
- `UNKNOWN`; or
- `OWNER_REQUIREMENT`.

Research records contradictions, negative results, missing evidence, maturity,
and the acceptance test needed to close each unknown.

Exit gate:

- source corpus and exact revisions are bound;
- decision-critical claims have evidence;
- unknowns and conflicts are visible;
- the full-map impact is identified; and
- research did not modify the implementation subject unless separately
  authorized.

### 5.3 L2 — Architecture and decision

Required for a boundary-changing task:

1. compile a frozen `ArchitectureReviewPacket`;
2. obtain the primary architecture/file-structure proposal;
3. obtain blind independent challenge;
4. produce an evidence-linked reconciliation matrix;
5. resolve or explicitly retain every finding;
6. write the RFC/ADR;
7. predeclare architecture and behavioral acceptance tests; and
8. obtain human decision.

The architecture packet includes:

- exact research/source digests;
- exact architecture-document digest and complete architecture-subject manifest
  digest, including every contract example in review scope;
- current and target repository trees;
- affected bounded contexts;
- current public APIs and dependency graph;
- state, effect, and data owners;
- security/trust boundaries;
- compatibility/upstream-sync constraints;
- alternatives and known failures;
- full-map attachment points that must remain intact; and
- required output schema.

Exit gate:

- accepted decision or explicit `CONFLICT`;
- no unmapped capability zone;
- no unowned state or effect;
- no new god object or ambient context;
- migration and rollback are specified; and
- the human governor accepts the ADR.

### 5.4 L3 — Task packet compilation

The task packet binds:

- project, work item, run, workspace, and base commit;
- parent Core-SDLC state, work class, derived risk lane, and readiness evidence;
- accepted outcome, requirement, acceptance-criterion, design, configuration
  baseline, and traceability references/digests;
- objective, scope, non-goals, and acceptance criteria;
- accepted ADR and machine-contract digests;
- Engineering Reference Application Map revision/digest plus an exact
  engineering-practice profile that evaluates all ten source families, binds
  applicable practice IDs to required behavior and verification, and records
  non-applicability, unknowns, and authorized deviations;
- the deterministic rule-activation manifest: instruction-registry
  version/digest, applicable project/role/stage/technology/risk/task/trigger
  rules, typed excluded-rule decisions/evidence, conflicts, and rule/context
  budget;
- bounded contexts/public APIs allowed to change;
- allowed and forbidden paths;
- allowed and forbidden dependency edges;
- affected state/effect ownership;
- tool, network, provider, cost, time, and output grants;
- data classification and egress;
- required tests/evidence;
- requirement/criterion-to-check mappings and invalidation dependencies;
- known facts, assumptions, unknowns, and conflicts;
- escalation triggers;
- migration and rollback obligations; and
- result/handoff schemas.

The compiler:

- resolves source precedence and freshness;
- blocks cross-project sources;
- exposes conflicts;
- refuses silent truncation;
- records omissions and budget consumption;
- binds any recorded stochastic retrieval result; and
- emits a deterministic manifest/digest over resolved inputs.

A material source, contract, base commit, policy, risk, grant, or scope change
invalidates the packet and requires recompilation.

#### 5.4.1 Worker assignment and fleet compilation

Packet readiness does not let a model seize work. `agent_collaboration` creates
a typed assignment and issues an expiring, compare-and-swap lease only after
principal/session, role, route, workspace, capability, budget, and independence
eligibility pass.

One worker is the default. A planner may propose parallel decomposition, but
the deterministic scheduler admits it only when reads are independent or
writes have disjoint registered ownership and isolated worktrees. The plan must
also fit qualified verifier, integration, and human-decision capacity.

Every attempt carries a monotonically increasing fencing epoch. Expired,
revoked, cancelled, or superseded attempts are denied at model, tool, write,
mailbox, result, and effect boundaries. Child-worker/model/tool use is charged
transitively to the parent reservation. Full lease, liveness, governor,
topology, backpressure, and recovery rules are defined in the
[fleet control-plane specification](./AI_AGENT_FLEET_CONTROL_PLANE.md).

### 5.5 L4 — Isolated implementation

One implementation worker receives:

- one task packet;
- one typed assignment and current fenced lease;
- one validated worktree;
- one capability profile;
- one deadline/budget;
- one expected output contract; and
- no gate, permit, merge, release, or unrelated-project authority.

Implementation rules:

- inspect before editing;
- preserve unrelated user changes;
- modify only allowed paths;
- call another context only through its public API;
- make imports side-effect free;
- use adapters only through declared ports;
- add or update tests with behavior;
- never weaken a test to make the change pass without an accepted requirement;
- record deviations immediately;
- stop on a material architecture conflict; and
- do not perform an externally irreversible action without a separate effect
  permit;
- heartbeat only through the coordinator protocol and never treat liveness as
  progress; and
- stop submitting work when the lease epoch is stale or revoked.

The worker may make multiple local commits if the packet permits it. The final
candidate commit and clean/dirty state are explicit. Parallel workers never
self-merge; integration is a separately packeted proposal and landing remains
human-controlled.

### 5.6 L5 — Submission and handoff

The `RunResult` and handoff include:

- producer role and actual provider/model/transport/session identity;
- input packet ID/digest;
- exact base and candidate commits;
- completed scope;
- deliberately uncompleted scope;
- changed files and dependency edges;
- migrations and generated files;
- commands and tests actually executed;
- raw artifact/evidence references;
- claims and evidence;
- assumptions, unknowns, conflicts, and deviations;
- security, data, compatibility, and upstream-sync impact;
- rollback procedure;
- file mutation summary; and
- requested next action.

An implementation summary is never accepted as proof that tests ran or behavior
works.

### 5.7 L6 — Independent review

The review packet contains the exact subject and only the context required by
the review role.

Review order:

1. validate exact commit/workspace/packet identity;
2. inspect the diff and relevant surrounding code;
3. verify architecture and ownership rules;
4. inspect tests for relevance and non-vacuity;
5. check security, concurrency, failure, recovery, and migration behavior;
6. reproduce required deterministic checks when authorized;
7. state findings with severity, path/line/evidence, impact, and required action;
8. distinguish opinion, no opinion, unusable output, and incomplete evaluation;
9. declare limitations and independence facts; and
10. submit `ReviewObservation`.

The kernel validates eligible observations into a review verdict. No model emits
an accepted `GateOutcome`.

### 5.8 L7 — Specialist escalation

Escalate to DeepSeek V4 Pro when a finding concerns:

- bounded-context or file-tree placement;
- transaction/outbox atomicity;
- concurrency, cancellation, or reconciliation;
- security/authority bypass;
- migration/upcaster correctness;
- subtle test inadequacy; or
- disagreement that cannot be resolved from deterministic evidence.

Escalate to HY3 for independent challenge of:

- hidden coupling or god objects;
- evidence-versus-verdict collapse;
- inherited Hermes bypass paths;
- split sources of truth;
- packet/subject determinism;
- module/route identity or qualification; and
- full-map omissions.

An escalation is a new attempt with a new route lock and budget. It does not
silently replace the original reviewer.

### 5.9 L8 — Deterministic verification

Run the task packet's required set from these families:

- schema and generated-artifact consistency;
- architecture/import/dependency fitness;
- unit/property tests;
- contract/golden/upcaster tests;
- reducer replay and nondeterminism injection;
- persistence and crash-boundary tests;
- capability/policy default-deny tests;
- exact-subject evidence/gate/permit tests;
- packet determinism and project-leakage canaries;
- checker mutation/non-vacuity tests;
- real sandbox and real-harness denial tests;
- concurrency/idempotency/reconciliation tests;
- migration/rollback tests;
- compatibility/upstream-sync tests;
- de-commercialization/provenance/SBOM tests;
- end-to-end tracer tests; and
- backup/restore tests when affected.

Missing, stale, wrong-target, empty-selection, malformed, timed-out, or broken
blocking checks cannot become pass.

### 5.10 L9 — Decision, gate, and permit

The qualified `assurance` gate evaluator evaluates:

- exact subject;
- active policy and risk;
- packet and contract versions;
- checker qualification;
- evidence freshness/completeness;
- independent review;
- unresolved findings/conflicts;
- migration/rollback readiness; and
- required human decisions.

Only a qualified exact-subject `PASS` satisfies a blocking gate automatically.
A scoped human waiver is recorded separately.

`assurance` creates the immutable `GateEvaluation`. `policy` evaluates
requirements and grant eligibility. `governed_execution` atomically binds the
fresh evaluation, issues/consumes the `ConsumableAuthorityGrant` and `Permit`,
and records the transition/effect. None may author the preceding owner's
record.

A permit is:

- exact-subject;
- action- and argument-bound;
- destination/adapter-bound;
- policy/evidence/grant-bound;
- single-use;
- expiring;
- nonce-bearing; and
- consumed using compare-and-swap on expected run version.

### 5.11 L10 — Landing

Landing is human-controlled under the current policy.

Before landing:

- candidate head has not changed;
- required checks refer to that head;
- permit remains valid;
- branch/worktree policy is satisfied;
- no unreviewed generated or migration change exists;
- release/upstream/compliance gates apply when relevant; and
- rollback is executable.

The merge/landing effect is a separate authorized activity. A Kanban button,
agent tool, or GitHub comment cannot substitute for the permit.

### 5.12 L11 — Post-landing verification

Verify the landed commit, not merely the candidate:

- required tests on landed revision;
- generated files and schemas clean;
- projections reconciled;
- no orphan permits/outbox records;
- deployment/release state correct;
- rollback point available;
- evidence and transition journal complete;
- worktree cleaned under policy; and
- work item projection updated from canonical state.

Failure creates a new governed remediation or rollback run.

### 5.13 L12 — Operations and learning

After release or operational use:

- record incidents, route/checker drift, cost/latency, recovery, and human
  intervention;
- isolate test, probe, evaluation, and production telemetry;
- perform backup/restore and upstream-sync drills;
- requalify changed module/route/isolation tuples;
- quarantine learned patterns;
- sanitize and review any proposed reusable knowledge;
- never let an agent promote its own lesson; and
- update policy/architecture only through the normal RFC/ADR path.

## 6. Quality gates

| Gate | Name | Required proof |
|---|---|---|
| `AI-G0` | Source readiness | Exact subject, source precedence, no blocking unknown/conflict |
| `AI-G1` | Architecture readiness for this run | Accepted target/ADR plus current `MAP-*` evaluations for one immutable `ArchitectureSubject` covering the run; no implied executable/runtime pass |
| `AI-G2` | Contract readiness | Canonical IDs, states, roles, paths, capabilities, engineering practices/profiles, lifecycles, mappings and executable schemas validate |
| `AI-G3` | Packet readiness | Deterministic exact packet, bounded scope/grants, current inputs |
| `AI-G4` | Submission readiness | Exact candidate, allowed paths/edges, schema-valid result, raw evidence |
| `AI-G5` | Review readiness | Independently validated exact-subject review; no maker contamination or write access |
| `AI-G6` | Verification | Required deterministic, real-seam, recovery, and compatibility checks pass |
| `AI-G7` | Transition readiness | Gate evaluation precedes any permit; no unresolved blocker; authenticated decisions and eligible grant |
| `AI-G8` | Landing readiness | Same head, human-controlled landing, rollback and migration ready |
| `AI-G9` | Post-landing | Landed revision verified; state/effects/projections reconciled |
| `AI-G10` | Operational readiness | Backup/restore, incident, route drift, release, and upstream-sync evidence |

These IDs are distinct from `SDLC-*`, `MAP-*`, `SDLC-ADOPT-*`, runtime
`GateOutcome`, and human decision points.

`MAP-*` evaluates paper-map assertions. `AI-G1` consumes those exact-subject
results for a run; it does not recreate them. `AI-G2` separately proves that
the accepted prose is projected into executable registries and schemas.
`AI-G6` onward supplies implementation/runtime evidence. No pass implies
another namespace passed.

## 7. Review finding lifecycle

```text
OPEN
  -> ACCEPTED
  -> FIXED_PENDING_VERIFICATION
  -> VERIFIED

OPEN
  -> DISPUTED
  -> SPECIALIST_REVIEW
  -> ACCEPTED | REJECTED_WITH_EVIDENCE | HUMAN_ACCEPTED_RISK
```

No agent resolves a finding merely by replying that it disagrees. Resolution
links the exact fix, evidence, reviewer, and subject revision.

## 8. Failure and retry contract

Every attempt records:

- failure domain: request, policy, capability, credential, transport, provider,
  model output, parser, evidence, cancellation, budget, internal;
- retry class: never, same-attempt-safe, new-attempt-idempotent,
  human-decision-required;
- observation state: reply received, absent, unusable, incomplete;
- attribution confidence: entailed, inferred, unknown;
- originating and wrapper failures;
- actual route and transport;
- elapsed/remaining deadline and budget;
- artifact references; and
- outcome uncertainty.

The caller owns one absolute deadline and cost/token/output/tool budgets across
all nested attempts. A route/model/transport change is a new attempt and cannot
inherit qualification implicitly.

The `RunStatus` transition graph is defined by the full-system architecture.
`SUCCEEDED`, `FAILED`, and `CANCELLED` are terminal for one `RunId`; retry uses
a linked new run. A blocked run stores its prior nonterminal status and may
resume only there after refreshed policy/evidence, or terminate as failed/
cancelled. Run completion never advances `WorkItemStatus`.

## 9. AI-execution completion criteria

These criteria close the named AI-assisted execution scope. They never replace
the Core SDLC definitions of Ready, Verified, Released, Operated,
Outcome-Reviewed, or Closed.

### 9.1 Architecture task

Done only when:

- full-map impact is explicit;
- boundaries, APIs, ownership, source placement, dependencies, trust, lifecycle,
  migration, rollback, and tests are defined;
- DeepSeek V4 Pro specialist input and independent HY3 challenge are recorded
  when required;
- every blocker is resolved or human-decided;
- machine contracts and generated views are synchronized; and
- the accepted ADR exists.

### 9.2 Implementation task or pull request

Done only when:

- exact packet and decisions are identified;
- scope/path/dependency constraints hold;
- required code, tests, docs, schemas, migrations, and generated artifacts are
  complete;
- all required checks pass on the exact candidate;
- evidence is inspectable and complete;
- independent review is bound to the exact candidate;
- findings are resolved;
- security, compatibility, provenance, and rollback obligations pass;
- a valid exact-subject permit exists;
- the human lands the change; and
- the landed commit passes post-landing verification.

### 9.3 Rebuild milestone

Done only when the full target architecture—not just one tracer—has:

- implemented owners and public APIs for every included capability zone;
- no unmapped or duplicate authority;
- a dependency-clean core;
- contained or extracted inherited Hermes behavior;
- complete real-adapter mediation for target mode;
- qualified providers, harnesses, checkers, modules, and isolation profiles;
- operational delivery, backup/restore, release/update, migration, and upstream
  sync;
- clean de-commercialization and provenance gates;
- proven concurrency, crash recovery, reconciliation, and project isolation;
- explicit handling for inactive mapped capabilities and exclusions; and
- human acceptance of the final evidence set.

## 10. Required templates

The target contract is
[AI-Work Artifact Contract Specification](./AI_ARTIFACT_CONTRACTS.md). Until
`AI-G2` passes, use these as field examples and never label them validated
schemas:

The 36 YAML templates map one-to-one to the 36 artifact/value-object producer
rows in the contract specification: 35 have artifact-specific target schemas,
while `CoreSDLCTrace` is the shared embedded trace schema. The ADR and RFC
Markdown templates below are governance-document forms, not two additional
runtime artifact-schema claims.

- [Work intake](./templates/WORK_INTAKE.yaml);
- [Research packet](./templates/RESEARCH_PACKET.yaml);
- [Architecture review packet](./templates/ARCHITECTURE_REVIEW_PACKET.yaml);
- [Architecture proposal](./templates/ARCHITECTURE_PROPOSAL.yaml);
- [Architecture reconciliation](./templates/ARCHITECTURE_RECONCILIATION.yaml);
- [AI task packet](./templates/AI_TASK_PACKET.yaml);
- [Agent assignment](./templates/AGENT_ASSIGNMENT.yaml);
- [Dispatch offer](./templates/DISPATCH_OFFER.yaml);
- [Worker attempt](./templates/WORKER_ATTEMPT.yaml);
- [Worker lease](./templates/WORKER_LEASE.yaml);
- [Resource reservation](./templates/RESOURCE_RESERVATION.yaml);
- [Mailbox envelope](./templates/MAILBOX_ENVELOPE.yaml);
- [Fleet experiment](./templates/FLEET_EXPERIMENT.yaml);
- [Capability assessment](./templates/CAPABILITY_ASSESSMENT.yaml);
- [Capability domain projection](./templates/CAPABILITY_DOMAIN_PROJECTION.yaml);
- [Core-SDLC trace block](./templates/CORE_SDLC_TRACE.yaml);
- [Run result](./templates/RUN_RESULT.yaml);
- [AI handoff](./templates/AI_HANDOFF.yaml);
- [Review request](./templates/REVIEW_REQUEST.yaml);
- [Analysis attempt](./templates/ANALYSIS_ATTEMPT.yaml);
- [Review observation](./templates/REVIEW_OBSERVATION.yaml);
- [Independence evaluation](./templates/INDEPENDENCE_EVALUATION.yaml);
- [Review verdict](./templates/REVIEW_VERDICT.yaml);
- [Generated review projection](./templates/REVIEW_RECORD.yaml);
- [Checker result](./templates/CHECKER_RESULT.yaml);
- [Evidence snapshot](./templates/EVIDENCE_SNAPSHOT.yaml);
- [Gate evaluation](./templates/GATE_EVALUATION.yaml);
- [Human decision](./templates/HUMAN_DECISION.yaml);
- [Consumable authority grant](./templates/AUTHORITY_GRANT.yaml);
- [Permit](./templates/PERMIT.yaml);
- [Landing record](./templates/LANDING_RECORD.yaml);
- [Post-landing verification](./templates/POST_LANDING_VERIFICATION.yaml);
- [Release evidence](./templates/RELEASE_EVIDENCE.yaml);
- [Operation evidence](./templates/OPERATION_EVIDENCE.yaml);
- [Outcome review](./templates/OUTCOME_REVIEW.yaml);
- [Transition event](./templates/TRANSITION_EVENT.yaml);
- [RFC](./templates/RFC.md); and
- [ADR](./templates/ADR.md).
