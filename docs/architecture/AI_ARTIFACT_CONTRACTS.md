# Ranex AI-Work Artifact Contract Specification

| Field | Value |
|---|---|
| Specification ID | `SPEC-AI-ARTIFACTS-001` |
| Version | `1.3.0` |
| Status | Normative executable documentation-contract baseline; runtime producer enforcement is `NOT_ASSESSED` and human `AI-G2` acceptance is pending |
| Owner | Human governor |
| Effective date | 2026-07-27 |
| Repository snapshot basis | `bootstrap/pre-upstream`; exact digest/revision is supplied by the review or release source manifest |
| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Worker protocol | [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md) |
| Fleet control | [AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md) |
| Architecture | [Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0002](./decisions/ADR-0002-retire-legacy-implementation-guide.md); [ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md) |
| Compatibility/migration class | New contract family; later breaking changes require upcasters and compatibility fixtures |
| Security/data class | Public specification metadata; artifact instances are classified independently |
| Review trigger | `AI-G2`, schema/canonicalization change, or any artifact-authority change |

## 1. Standing

This document specifies the complete artifact family used to drive and verify
AI workers inside the established Core SDLC. It defines target fields,
producers, authority boundaries, canonicalization, and schema locations.

Files under [`templates/`](./templates/) are reviewable authoring skeletons.
Their executable JSON Schemas are registered under
[`../../schemas/`](../../schemas/), canonical vocabularies are registered under
[`../../architecture/contracts/`](../../architecture/contracts/), and
`scripts/architecture/validate_contracts.py` validates them together with
canonicalization, forgery, reuse, and subject-binding fixtures. Empty authoring
placeholders remain invalid for a sealed runtime artifact.

This executable documentation-contract baseline does not by itself establish
`AI-G2: PASS`. That gate additionally requires the exact-revision validation
report, generated consumer packages, qualified runtime producers, isolation
evidence, and authenticated human acceptance.

## 2. Canonical encoding and digest

The contract registry declares one canonical wire representation:

1. accept JSON or YAML only at an ingress adapter;
2. parse with duplicate-key rejection and schema-selected scalar types;
3. normalize to the versioned JSON data model;
4. reject unknown fields unless that schema version explicitly reserves them;
5. encode using RFC 8785 JSON Canonicalization Scheme;
6. compute SHA-256 over the UTF-8 canonical bytes with the top-level `digest`
   field absent;
7. serialize `digest` as `sha256:<64 lowercase hex>`;
8. preserve the original submitted bytes as a separate artifact when required;
   and
9. never use display YAML bytes, map insertion order, local paths, timestamps,
   or a redacted projection to recompute the canonical digest.

Times are RFC 3339 UTC with explicit `Z`. Durations and budgets are integer
base units declared by schema. Floating-point values are forbidden in authority
and evidence identity. Empty string is not a substitute for absent/unknown;
required unknown facts use the typed epistemic state.

## 3. Shared identifiers and vocabulary

All generated identifiers use the prefixes registered in `identities.yaml`.
Minimum prefixes include:

| Type | Prefix |
|---|---|
| Repository | `repo_` |
| Project / work / run / activity / effect | `prj_`, `work_`, `run_`, `act_`, `eff_` |
| Workspace / packet / intake / research | `wsp_`, `pkt_`, `intake_`, `research_` |
| Requirement / criterion / outcome measure | `req_`, `criterion_`, `measure_` |
| Core-SDLC trace block | `trace_` |
| Evidence / snapshot / artifact / checker result | `evd_`, `snapshot_`, `art_`, `check_` |
| Architecture review packet / proposal / reconciliation | `archpkt_`, `proposal_`, `archreconcile_` |
| Review request / attempt / observation / verdict | `review_`, `attempt_`, `observation_`, `verdict_` |
| Review-record projection | `review_projection_` |
| Independence evaluation / finding / reconciliation | `independence_`, `finding_`, `reconcile_` |
| Decision / authority grant / permit / gate | `dec_`, `grant_`, `permit_`, `gate_` |
| Handoff / result / landing / transition | `handoff_`, `result_`, `landing_`, `transition_` |
| Release / incident / service / capability | `release_`, `incident_`, `svc_`, `cap_` |
| Post-landing / release / operation / outcome evidence | `postlanding_`, `release_evidence_`, `operation_evidence_`, `outcome_review_` |
| Assignment / offer / worker attempt / lease / mailbox | `assignment_`, `offer_`, `wattempt_`, `lease_`, `message_` |
| Resource reservation / fleet experiment | `reservation_`, `fleetexp_` |
| Capability assessment / domain projection | `capability_assessment_`, `capability_domain_projection_` |

Canonical enum values are uppercase. Lowercase values in display examples are
invalid after `AI-G2`. The authoritative registries own:

- `WorkItemStatus`, `WorkClass`, `RiskLane`, `RunStatus`, `ActivityStatus`,
  `IntakeStatus`, `PacketStatus`, `AssignmentStatus`, `DispatchOfferStatus`,
  `LeaseStatus`, `MailboxDeliveryStatus`, `ReservationStatus`,
  `FleetExperimentStatus`, `CapabilityAssessmentStatus`, `EffectStatus`, and
  `ReconciliationStatus`;
- `IncidentStatus`, `ReleaseStatus`, `CapabilityStatus`, `ModuleStatus`,
  `RouteStatus`, `ExtensionStatus`, and `CompatibilityStatus`;
- observation, finding, review-verdict, checker, gate, decision, grant, permit,
  artifact, migration, sync, update, and cutover states;
- role IDs and incompatible-role combinations; and
- `SDLC-*`, `AI-G*`, `MAP-*`, and `SDLC-ADOPT-*` gate namespaces.

## 4. Subject binding

A child artifact either embeds one full discriminated subject or references one
through `SubjectBindingV1`:

```yaml
subject_schema: work-subject/v1 # or exact/architecture/research/resource subject
subject_ref: art_<uuidv7>
subject_digest: sha256:<hex>
subject_manifest_digest: null
```

`subject_schema` selects the conditional subject contract. `subject_ref`
identifies the immutable stored subject; it is never overloaded with the schema
ID. `subject_digest` binds the canonical subject bytes.
`subject_manifest_digest` is required for architecture/research subjects and is
required when a resource subject binds a scope manifest. It is `null` only when
the selected subject has no separate manifest. Missing, conflicting, or
variant-incompatible bindings fail closed.

### 4.1 `WorkSubjectV1`

Core-SDLC work exists before an execution run, workspace, or task packet.
Intake, definition, and design may therefore bind:

```yaml
subject_schema: work-subject/v1
project_id: prj_<uuidv7>
work_item_id: work_<uuidv7>
repository_id: repo_<uuidv7>
repository_uri_digest: sha256:<hex>
base_revision: <40-hex>
work_baseline_manifest_digest: sha256:<hex>
signal_evidence_digest: sha256:<hex>
requirements_baseline_digest: null
design_baseline_digest: null
observed_at: <RFC3339>
```

The subject advances only through an owned Core-SDLC transition or baseline
change. A later execution subject references the same project/work item and
the accepted baselines; it does not erase this earlier work identity.

### 4.2 `ExactSubjectV1`

Every evidence, decision, gate, permit, run, review, and effect contract embeds
or references one immutable subject:

```yaml
subject_schema: exact-subject/v1
project_id: prj_<uuidv7>
work_item_id: work_<uuidv7>
run_id: run_<uuidv7>
activity_id: null
effect_id: null
workspace_id: wsp_<uuidv7>
repository_id: repo_<uuidv7>
repository_uri_digest: sha256:<hex>
base_commit: <40-hex>
candidate_commit: <40-hex-or-null>
artifact_digest: null
packet_id: pkt_<uuidv7>
packet_digest: sha256:<hex>
workflow_definition_id: <stable-id>
workflow_definition_digest: sha256:<hex>
workflow_interpreter_version: <semver-or-content-id>
policy_activation_id: <stable-id>
policy_activation_manifest_digest: sha256:<hex>
policy_decision_digest: sha256:<hex>
module_profile_id: <stable-id>
module_profile_digest: sha256:<hex>
capability_grant_digest: sha256:<hex>
route_lock_id: route_<uuidv7-or-null>
schema_registry_version: <immutable-version>
expected_run_aggregate_version: <nonnegative-integer>
```

The schema uses conditional requirements. An architecture/process decision may
bind a normative artifact revision/digest instead of a run/activity/effect; an
effect permit requires all effect fields. A `TaskPacket` omits its own
`packet_id`/`packet_digest` from the embedded subject to avoid a recursive hash;
its top-level ID and digest become required in every downstream subject.
Adapters cannot silently fill an inapplicable field with an empty string.
`policy_activation_manifest_digest` binds the deterministic included/excluded
rule set, instruction-registry version, applicability evidence, conflicts,
enforcement classes, resolution requirements, and context budget compiled for
the subject. It is not a prompt receipt. The exact subject is the sole field
home for activation ID/digest; a task packet embeds the manifest components in
its authority block, and the semantic validator canonicalizes that block and
requires its hash to equal the subject digest before `SEALED`. Any material
rule, scope, project, role, stage, technology, risk, task, trigger, or budget
change invalidates the packet and every downstream subject.

#### 4.2.1 `EngineeringPracticeProfileV1`

Every `TaskPacket` embeds one immutable engineering-practice profile compiled
from the exact `engineering-practices.json` registry and
Engineering Reference Application Map revision. The profile:

- binds the registry version/digest and application-map revision/digest;
- evaluates all ten registered source families as `APPLICABLE`,
  `NOT_APPLICABLE`, or `UNKNOWN`;
- binds applicable practice IDs to required behavior and verification refs;
- requires reason/evidence for non-applicability;
- records deliberate deviations with consequence and decision reference;
- blocks sealing when a material applicability decision is `UNKNOWN`; and
- has its own canonical digest included in the task-packet digest.

The semantic validator requires exactly one source-coverage entry for each
registered source-family ID and rejects missing, duplicate, unknown, or
unregistered IDs. The profile carries public-safe Ranex synthesis and stable
locators, never unauthorized full-text book content. A practice label or
quotation is not verification evidence.

### 4.3 `ArchitectureSubjectV1`

Architecture/process review is bound to an explicit normative subject rather
than overloading a runtime `Run` tuple:

```yaml
subject_schema: architecture-subject/v1
project_id: prj_<uuidv7>
work_item_id: work_<uuidv7>
repository_id: repo_<uuidv7>
repository_uri_digest: sha256:<hex>
base_revision: <40-hex>
candidate_revision: <40-hex-or-null>
working_tree_digest: sha256:<hex-or-null>
architecture_document_path: docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
architecture_document_digest: sha256:<hex>
architecture_subject_manifest_digest: sha256:<hex>
research_manifest_digests: [sha256:<hex>]
contract_and_template_manifest_digest: sha256:<hex>
accepted_adr_registry_digest: sha256:<hex>
review_prompt_digest: sha256:<hex>
```

`architecture_subject_manifest_digest` binds the sorted path/digest inventory
of every architecture, policy, contract example, research manifest, and other
artifact declared in scope. The reconciliation records both the reviewed
subject digest and the resulting architecture/manifest digests. A later edit
cannot be mislabeled as reviewed merely because the branch name or document
version stayed the same.

### 4.4 `ResearchSubjectV1`

Research that is not one runtime execution still binds one immutable,
discriminated subject:

```yaml
subject_schema: research-subject/v1
project_id: prj_<uuidv7>
work_item_id: work_<uuidv7>
repository_id: repo_<uuidv7>
repository_uri_digest: sha256:<hex>
base_revision: <40-hex>
question_digest: sha256:<hex>
scope_digest: sha256:<hex>
source_manifest_digest: sha256:<hex>
research_prompt_digest: sha256:<hex>
observed_at: <RFC3339>
```

The source manifest freezes local paths and external snapshots actually used.
Changing the question, scope, prompt, repository revision, or source manifest
creates a new subject. A directory name or live glob is not a research subject.

### 4.5 `ResourceSubjectV1`

Hierarchical resource reservations may begin above a runtime work item. They
therefore use a distinct conditional subject:

```yaml
subject_schema: resource-subject/v1
scope_kind: PROJECT # PROJECT | RELEASE | WORK_ITEM | RUN | WORKER_ATTEMPT | ACTIVITY | EFFECT
project_id: prj_<uuidv7>
release_id: null
work_item_id: null
run_id: null
worker_attempt_id: null
activity_id: null
effect_id: null
repository_id: repo_<uuidv7>
repository_uri_digest: sha256:<hex>
base_revision: <40-hex>
scope_manifest_digest: sha256:<hex>
parent_subject_ref: null
parent_subject_digest: null
```

The executable schema requires the IDs implied by `scope_kind`, forbids
lower-level IDs at a higher-level root, and requires the immediate parent
subject for every non-root scope. A `CoreSDLCTrace` is required from
`WORK_ITEM` downward and is `null` only for a legitimate `PROJECT` or
`RELEASE` root. This subject carries no authority by itself.

## 5. Core-SDLC trace block

Every intake, task, run, review, gate, capability assessment/domain projection,
landing, release, operation, and outcome record embeds or content-addresses one
immutable `CoreSDLCTraceV1`:

```text
WorkItemStatus at dispatch/observation
WorkClass
RiskLane + risk decision reference/digest
product, technical, service, security/data, delivery, V&V,
  configuration, supplier and release owner references as applicable
outcome-measure IDs
requirement IDs
acceptance-criterion IDs
configuration baseline ID/digest
Definition-of-Ready evidence snapshot
requirement/criterion -> checker/evidence links
invalidation dependency IDs
```

The trace binds a discriminated subject reference: `work-subject/v1`,
`exact-subject/v1`, `architecture-subject/v1`, `research-subject/v1`, or a
`resource-subject/v1` whose scope is `WORK_ITEM` or lower. Its subject digest
and, when the variant has one, subject-manifest digest must match the child
record. A resource trace's `WorkItemId` must match the resource subject.
Project/release root reservations have no Core trace. An architecture or
process trace is therefore not forced into a fake runtime run/activity tuple.

These are references, not duplicate product/work authority. A changed source
marks dependent artifacts stale through `invalidation-graph.yaml`.
If a child artifact uses `core_sdlc_trace_ref` instead of embedding the block,
the referenced trace digest is part of the child's canonical digest and must
bind the same `WorkItemId` and exact subject. Empty or mismatched references
fail closed.

## 6. Artifact family and producer authority

| Artifact | Canonical producer | Purpose | Cannot authorize |
|---|---|---|---|
| `CoreSDLCTrace` | `configuration_management` traceability compiler | Content-address the accepted project/work/control/requirement/criterion/baseline and exact-subject bindings reused by child artifacts | Mutate its sources, change `WorkItemStatus`, lower risk, or authorize work/effects |
| `WorkIntake` | Work-intake service under duty/product owner | Capture signal and initial facts | Priority, lower risk, dispatch |
| `ResearchPacket` | Research activity | Bind sources, claims, contradictions, unknowns | Architecture/product decision |
| `ArchitectureReviewPacket` | Packet compiler | Freeze exact design-review subject | Acceptance |
| `ArchitectureProposal` | Specialist worker | Proposed boundaries/tree/trade-offs | Its own acceptance |
| `ArchitectureReconciliation` | Synthesizer plus finding records | Resolve proposal/challenge against evidence | Human ADR decision |
| `TaskPacket` | Deterministic packet compiler | Authorize one bounded worker run and bind its exact engineering-practice application profile | Expanded scope, book-derived authority, or merge/release |
| `AgentAssignment` | `agent_collaboration` | Bind eligible packet, role, workspace, topology, reservation, and deadline | Work/run transition or claim |
| `DispatchOffer` | `agent_collaboration` offer service | Bind one expiring eligibility invitation to an assignment, optional named principal, and immutable eligibility policy | Grant authority or claim an assignment outside atomic claim |
| `WorkerAttempt` | `agent_collaboration` attempt service | Bind one principal/session/route/harness/workspace/lease epoch to one assignment and immutable result lineage | Work/run transition, retry policy, or broader lease |
| `WorkerLease` | `agent_collaboration` atomic claim service | Time-bound one attempt with fencing epoch | Broader scope or authority |
| `MailboxEnvelope` | `agent_collaboration` mailbox service | Durable typed coordination reference | Recipient command acceptance or authority |
| `FleetExperiment` | `process_assurance` | Predeclare and retain fleet/control measurement | Change active topology/policy by itself |
| `ResourceReservation` | `resource_governance` | Bind hierarchical admitted limits and settled usage to an exact subject | Authorize an effect, exceed an ancestor, or declare work complete |
| `CapabilityAssessment` | `process_assurance` under accountable assessor/approver roles | Diagnose one exact capability/control scope with separate level, effectiveness, coverage, confidence, and improvement priority | Authorize a transition, average away a vital-control failure, or rank people |
| `CapabilityDomainProjection` | `process_assurance` deterministic projection service under accountable assessor/approver roles | Bind the exact registered control-tuple set for one domain/scope/window and derive result, lowest supported level, and highest-precedence priority | Author a member assessment, omit/duplicate/remap a registry tuple, arithmetically aggregate levels, or authorize a transition |
| `RunResult` | Worker harness normalization | Record actual work and evidence refs | Test/gate pass |
| `AgentHandoff` | Handoff service | Reference result and requested next role | Restate/change run evidence |
| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
| `ReviewObservation` | Reviewer/model normalization | Findings, uncertainty, limitations | Gate outcome |
| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
| `ReviewVerdict` | Review application service | Eligible review disposition and finding set | Runtime gate or human approval |
| `ReviewRecordProjection` | Projection builder | Read model joining immutable review records for navigation | Replace or mutate its source records |
| `CheckerResult` | Qualified deterministic checker wrapper | One reproducible check outcome | Aggregate gate alone |
| `EvidenceSnapshot` | Assurance service | Freeze exact eligible evidence set | Decision by itself |
| `GateEvaluation` | Qualified gate evaluator | Produce runtime `GateOutcome` | Human decision |
| `HumanDecisionRecord` | Policy after IAM authentication | Record accountable human choice | Direct effect execution |
| `ConsumableAuthorityGrant` | Governed execution | One-shot eligible decision snapshot | Broader/different action |
| `Permit` | Governed execution after gate/decision | One-shot exact effect/transition capability | Another subject/action |
| `LandingRecord` | Workspace/Git adapter normalization | Prove candidate-to-landed relation | Release/closure |
| `PostLandingVerification` | Assurance service | Verify landed subject | Product outcome |
| `ReleaseEvidence` | Release management | Build/promotion/rollback facts | Service/product acceptance |
| `OperationEvidence` | Operations/service evidence ingestion | Health/support/recovery facts | Product outcome |
| `OutcomeReview` | Product definition under product owner | Compare outcome and decide keep/change/remove | Rewrite engineering facts |
| `TransitionEvent` | Owning aggregate UoW | Durable accepted state fact | State owned by another aggregate |

## 7. Review separation

Review is five immutable records, not one mutable model response:

```text
ReviewRequest
  -> AnalysisAttempt[1..N]
  -> ReviewObservation[0..N]
  -> IndependenceEvaluation
  -> ReviewVerdict
  -> EvidenceSnapshot
  -> GateEvaluation
```

`ReviewRequest` records maker principal/run/session/role, exact subject,
separate review packet, required reviewer role, prohibited capabilities, blind
context manifest, diversity requirements expressed as actual route facts, and
qualification policy.

Each `AnalysisAttempt` records reviewer principal/role/session, actual
provider/model/transport/executable/parser/isolation identities, route lock,
input/output artifact digests, start/end/deadline/budget, granted capabilities,
write attempts, failures, usage, and relation to previous attempts.

`IndependenceEvaluation` is based on inspectable evidence references. Reviewer
self-assertion and a model-family label are insufficient. It compares maker and
reviewer identities/sessions, packet construction, write capability/activity,
blindness manifest, route/provider/transport facts, qualification, hidden
fixture isolation, and candidate identity.

`ReviewVerdict` values are `ACCEPTABLE`, `CHANGES_REQUIRED`, `INCOMPLETE`, or
`INELIGIBLE`. It records open finding IDs and reconciliation references. It is
not `GateOutcome`.

### 7.1 Deadline and budget null semantics

In draft templates, `null` means **not established**. It never means unlimited.
A packet cannot become `SEALED`, an offer cannot become `OPEN`, and a
reservation cannot become `ACTIVE` while a policy-required deadline or budget
dimension is null. Zero denies consumption of that dimension. A dimension may
be omitted only through a typed `NOT_APPLICABLE` decision with policy rule,
reason, accountable owner, and evidence reference.

Every activated execution/review reservation has an absolute deadline and all
transitive dimensions required by its risk/work-class policy. Child limits are
no later/larger than every ancestor. Canonical validation rejects negative,
ambiguous, unitless, floating-point, or “unlimited” sentinel values.

## 8. Finding lifecycle

Every finding has category, severity, confidence/epistemic status, exact
location, claim, impact, evidence, required action, owner, and state:

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

Only the review/finding application service changes finding state. A maker may
submit a resolution proposal but cannot mark its finding verified.

## 9. Gate, decision, grant, and permit order

The required order is:

```text
eligible evidence
  -> EvidenceSnapshot
  -> GateEvaluation
  -> authenticated HumanDecisionRecord when policy requires
  -> ConsumableAuthorityGrant
  -> Permit
  -> atomic permit consumption + effect intent
```

`GateEvaluation` binds gate ID/version, namespace, policy, required and observed
claims, checker qualifications/results, applicability proof, freshness,
coverage, conflicting/missing evidence, exact subject, evaluator code digest,
and one `GateOutcome`.

`HumanDecisionRecord` discriminates:

- `ARCHITECTURE_OR_PROCESS_ACCEPTANCE`;
- `RISK_ACCEPTANCE_OR_WAIVER`;
- `WORK_TRANSITION`;
- `RELEASE_OR_MIGRATION`;
- `DESTRUCTIVE_OR_EXTERNAL_EFFECT`; and
- `REVOCATION`.

It records explicit outcome, authenticated presentation/challenge digest,
conditions, scope, reason, issue/expiry/revocation, and normative artifact or
runtime subject. The decision record is not consumed. The derived authority
grant and permit are single-use and compare-and-swap protected.

## 10. Worker-visible versus withheld verification

The worker packet contains required public test families, commands, acceptance
criteria, and an opaque `withheld_verification_profile_id`. It never contains
hidden fixture paths, IDs, contents, expected results, answer keys, grader
internals, or secrets. Qualification/verifier packets hold those fields and are
unavailable to maker identities and workspaces.

## 11. Command and test evidence

Commands are structured records:

```text
argv[]                 exact arguments, never a reconstructed shell string
cwd_repository_relative
environment_allowlist_digest
tool/executable identity and digest
subject commit/workspace
start/end/deadline
exit status or typed launch/timeout/cancel failure
stdout/stderr artifact refs
redaction/classification status
```

`AgentHandoff` references immutable `RunResult`, test, evidence, finding, and
artifact IDs. Any human-readable duplication is a generated projection and must
match its source digest.

## 12. Executable schema tree

```text
schemas/
├── common/
│   ├── identifiers.schema.json
│   ├── subject-binding-v1.schema.json
│   ├── work-subject-v1.schema.json
│   ├── exact-subject-v1.schema.json
│   ├── architecture-subject-v1.schema.json
│   ├── research-subject-v1.schema.json
│   ├── resource-subject-v1.schema.json
│   ├── core-sdlc-trace-v1.schema.json
│   ├── engineering-practice-profile-v1.schema.json
│   ├── test-practice-profile-v1.schema.json
│   ├── architecture-rule-assessment-v1.schema.json
│   ├── architecture-practice-application-profile-v1.schema.json
│   ├── path-contract-v1.schema.json
│   ├── context-dependency-edge-v1.schema.json
│   ├── context-boundary-fit-v1.schema.json
│   ├── context-coupling-policy-v1.schema.json
│   ├── feedback-fitness-policy-v1.schema.json
│   ├── topology-exception-v1.schema.json
│   ├── evidence-ref.schema.json
│   └── canonical-digest.schema.json
├── work/
│   ├── work-intake-v1.schema.json
│   ├── task-packet-v1.schema.json
│   └── transition-event-v1.schema.json
├── research/
│   └── research-packet-v1.schema.json
├── process/
│   ├── capability-assessment-v1.schema.json
│   └── capability-domain-projection-v1.schema.json
├── architecture/
│   ├── review-packet-v1.schema.json
│   ├── proposal-v1.schema.json
│   └── reconciliation-v1.schema.json
├── execution/
│   ├── run-result-v1.schema.json
│   ├── agent-handoff-v1.schema.json
│   ├── landing-record-v1.schema.json
│   └── post-landing-verification-v1.schema.json
├── review/
│   ├── review-request-v1.schema.json
│   ├── analysis-attempt-v1.schema.json
│   ├── review-observation-v1.schema.json
│   ├── independence-evaluation-v1.schema.json
│   ├── review-verdict-v1.schema.json
│   └── review-record-projection-v1.schema.json
├── assurance/
│   ├── checker-result-v1.schema.json
│   ├── evidence-snapshot-v1.schema.json
│   └── gate-evaluation-v1.schema.json
├── authority/
│   ├── human-decision-v1.schema.json
│   ├── authority-grant-v1.schema.json
│   └── permit-v1.schema.json
├── fleet/
│   ├── assignment-v1.schema.json
│   ├── dispatch-offer-v1.schema.json
│   ├── worker-attempt-v1.schema.json
│   ├── lease-v1.schema.json
│   ├── mailbox-envelope-v1.schema.json
│   └── fleet-experiment-v1.schema.json
├── resources/
│   └── resource-reservation-v1.schema.json
└── lifecycle/
    ├── release-evidence-v1.schema.json
    ├── operation-evidence-v1.schema.json
    └── outcome-review-v1.schema.json
```

This tree now exists and is indexed by
`architecture/contracts/schema-registry.json`. The 36 governed YAML artifact
types have one schema and one canonical producer entry each. Common subject,
identifier, evidence-reference, engineering-practice-profile,
test-practice-profile, path-contract, per-rule architecture-assessment, and
canonical-digest schemas are executable Draft 2020-12 contracts. Schema
validation is necessary but not sufficient: the deterministic validator also
enforces registry closure, exact VITAL, topology, TDD, path, and fixture
denominators, digest integrity, single-use permits, subject equality,
cross-context import and cycle policy, test/production-path parity, and scoring
honesty.

This remains the detailed artifact-contract subset of the full `schemas/`
namespace map in the system architecture. The system map additionally reserves
product, service, configuration, supplier, interaction, module, route,
operation, and other future domain-schema namespaces. It is a superset, not a
competing tree.

Generated Python/TypeScript types, examples, documentation, and validators come
from these schemas and registries. Hand editing generated files fails CI.

Contract generation and validation are one serialized publication protocol.
Both tools acquire the same repository-scoped interprocess lock before reading,
cleaning, writing, or validating any generated tree. The lock lives outside
all generator-owned paths. A validator or second generator therefore waits for
the complete publication and can never treat the intentional cleanup window as
an empty denominator. The disposable
`scripts/architecture/test_contract_concurrency.py` regression stages exactly
that window, proves both contenders wait, restores the prior complete tree,
and requires the final generated-tree digest to equal its baseline.

## 13. Compatibility and completion

A schema change declares additive/breaking status, upcaster, old/new fixtures,
producer/consumer range, storage/replay effect, active-run policy, rollback, and
removal date. No upcaster changes historical authority meaning.

Wave 1 establishes the executable documentation-contract baseline:

- every governed YAML template has one strict structural schema and canonical
  producer registry entry;
- identities, states/transitions, contexts, data/path ownership, events,
  effects, artifact types, decisions, applicability, priority, VITAL controls,
  engineering practices/profiles, and architecture elements are registered;
- all 18 ADR-0007 topology rules, all 26 ADR-0008 TDD rules, all ten ADR-0009
  boundary/feedback rules, all ten ADR-0010 inherited-test-layout rules, all
  18 allowed test roots, all 232 path contracts,
  and all 1,008 inventoried architecture elements have explicit generated
  denominators;
- all 67 declared context edges, all 34 boundary-fit hypotheses, all six
  governed-execution coupling measures, all four feedback objectives, and all
  nine ADR-0009 fitness obligations are exact-set projections;
- each of the 64 topology/TDD/boundary/inherited-layout rules has one exact
  definition-subject assessment
  record. Every record and the non-compensating summary remain
  `NOT_ASSESSED`, with no numeric score, because no runtime/source subject or
  current behavioral evidence exists;
- all ten stable source-family IDs and 38 stable practice-source IDs are
  imported from the public-safe reconciled registry, while applicability and
  behavioral evidence remain `UNKNOWN`/`NOT_ASSESSED`;
- RFC 8785/SHA-256 golden fixtures pass; and
- the authority-bound negative-fixture directory contains exactly 35 files.
  Executed suites reject duplicate keys, unknown fields, forged digests,
  permit reuse, wrong/stale subjects, incomplete or forged test profiles,
  blanket test-root ownership, test-only production bypasses, private and
  undeclared cross-context imports, cyclic context imports, broad topology
  exceptions, unjustified N/A, forced boilerplate, expired quarantine,
  retry-to-pass, incomplete deletion, and unbound production evidence.
  ADR-0012 separately executes 28 declared negative scenarios plus six
  freshness boundary subcases. The 213 estimate-commitment V2 case rows remain
  a declared, unexecuted definition catalog, so 35 is a file denominator
  rather than a claim that every catalog row executed. Missing or orphan
  fixture files fail validation.

[ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md)
governs two separate readiness tiers.

`IMPLEMENTATION_START_READY` still requires:

- authoring placeholders to be resolved before any instance becomes `SEALED`;
- generated Python and TypeScript consumer packages and cross-language
  canonicalization parity;
- exact-revision compatibility/upcaster fixtures for every breaking change;
- deterministic validation of the exact committed source and generated
  manifests plus the closed readiness subject manifest and every native-
  subject evidence bridge, with no stale output, denominator, or conflict;
- a clean, committed, upstream-derived `SDLC-FORK-000: PASS` subject;
- one real current-subject non-synthetic ADR-0008 cycle, its separate
  `SUCCEEDED` landing, and post-landing seal;
- fresh same-subject OpenCode HY3 and DeepSeek V4 Pro structural reviews with
  no unresolved P0/P1 finding; and
- an authenticated causal human implementation-start decision.

Runtime producer enforcement, runtime rule results, and capability scores may
remain explicitly `NOT_ASSESSED`/null at this tier. Before it passes, only the
bounded `PRE_READINESS_TOOLING_TRACER` may produce its architecture/tooling
evidence; it cannot implement product capability or activate product runtime.
After it passes, an ordinary authorized product commit may retain the admitted
baseline only on a clean descendant with byte-identical governed
design/control paths; the commit's own normal controls are never inherited
from readiness.

`PRODUCTION_READY` additionally requires:

- every runtime producer to be its registered context and unable to forge
  another producer's record;
- hidden-fixture isolation and review independence through a real harness;
- an enacted `src/ranex` tree plus representative test roots and exactly 64
  current ADR-0007–ADR-0010 rule results before source topology, import-cycle,
  production/test-path parity, or TDD conformance can pass;
- qualified runtime, security, recovery, operational, adoption, and applicable
  capability-assessment evidence; and
- authenticated human acceptance of the resulting exact-subject `AI-G2` and
  production-readiness evidence.
