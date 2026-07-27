# Ranex AI-Work Artifact Contract Specification

| Field | Value |
|---|---|
| Specification ID | `SPEC-AI-ARTIFACTS-001` |
| Version | `1.0.0` |
| Status | Normative target specification; executable schemas are not yet implemented |
| Owner | Human governor |
| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Worker protocol | [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md) |
| Architecture | [Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Owner decision | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md) |

## 1. Standing

This document specifies the complete artifact family used to drive and verify
AI workers inside the established Core SDLC. It defines target fields,
producers, authority boundaries, canonicalization, and schema locations.

Files under [`templates/`](./templates/) are reviewable example instances of
these contracts. They are not executable schemas. Ranex may claim
`AI-G2: PASS` only after generated schemas, registries, examples, and
compatibility fixtures validate together at the exact release revision.

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
| Project / work / run / activity / effect | `prj_`, `work_`, `run_`, `act_`, `eff_` |
| Workspace / packet / intake / research | `wsp_`, `pkt_`, `intake_`, `research_` |
| Requirement / criterion / outcome measure | `req_`, `criterion_`, `measure_` |
| Evidence / snapshot / artifact / checker result | `evd_`, `snapshot_`, `art_`, `check_` |
| Review request / attempt / observation / verdict | `review_`, `attempt_`, `observation_`, `verdict_` |
| Independence evaluation / finding / reconciliation | `independence_`, `finding_`, `reconcile_` |
| Decision / authority grant / permit / gate | `dec_`, `grant_`, `permit_`, `gate_` |
| Handoff / result / landing / transition | `handoff_`, `result_`, `landing_`, `transition_` |
| Release / incident / service / capability | `release_`, `incident_`, `svc_`, `cap_` |

Canonical enum values are uppercase. Lowercase values in display examples are
invalid after `AI-G2`. The authoritative registries own:

- `WorkItemStatus`, `WorkClass`, `RiskLane`, `RunStatus`, `ActivityStatus`,
  `EffectStatus`, and `ReconciliationStatus`;
- `IncidentStatus`, `ReleaseStatus`, `CapabilityStatus`, `ModuleStatus`,
  `RouteStatus`, `ExtensionStatus`, and `CompatibilityStatus`;
- observation, finding, review-verdict, checker, gate, decision, grant, permit,
  artifact, migration, sync, update, and cutover states;
- role IDs and incompatible-role combinations; and
- `SDLC-*`, `AI-G*`, `MAP-*`, and `SDLC-ADOPT-*` gate namespaces.

## 4. `ExactSubjectV1`

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

## 5. Core-SDLC trace block

Every intake, task, run, review, gate, landing, release, operation, and outcome
record carries:

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

These are references, not duplicate product/work authority. A changed source
marks dependent artifacts stale through `invalidation-graph.yaml`.

## 6. Artifact family and producer authority

| Artifact | Canonical producer | Purpose | Cannot authorize |
|---|---|---|---|
| `WorkIntake` | Work-intake service under duty/product owner | Capture signal and initial facts | Priority, lower risk, dispatch |
| `ResearchPacket` | Research activity | Bind sources, claims, contradictions, unknowns | Architecture/product decision |
| `ArchitectureReviewPacket` | Packet compiler | Freeze exact design-review subject | Acceptance |
| `ArchitectureProposal` | Specialist worker | Proposed boundaries/tree/trade-offs | Its own acceptance |
| `ArchitectureReconciliation` | Synthesizer plus finding records | Resolve proposal/challenge against evidence | Human ADR decision |
| `TaskPacket` | Deterministic packet compiler | Authorize one bounded worker run | Expanded scope or merge/release |
| `RunResult` | Worker harness normalization | Record actual work and evidence refs | Test/gate pass |
| `AgentHandoff` | Handoff service | Reference result and requested next role | Restate/change run evidence |
| `ReviewRequest` | Review service | Bind subject, maker, role and independence requirements | Review result |
| `AnalysisAttempt` | Review transport wrapper | Record one actual route/session/attempt | Eligibility or verdict |
| `ReviewObservation` | Reviewer/model normalization | Findings, uncertainty, limitations | Gate outcome |
| `IndependenceEvaluation` | Deterministic independence validator | Evaluate maker/reviewer separation and evidence | Semantic acceptance |
| `ReviewVerdict` | Review application service | Eligible review disposition and finding set | Runtime gate or human approval |
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

## 12. Target schema tree

```text
schemas/
├── common/
│   ├── identifiers.schema.json
│   ├── exact-subject-v1.schema.json
│   ├── core-sdlc-trace-v1.schema.json
│   ├── evidence-ref.schema.json
│   └── canonical-digest.schema.json
├── work/
│   ├── work-intake-v1.schema.json
│   ├── task-packet-v1.schema.json
│   └── transition-event-v1.schema.json
├── research/
│   └── research-packet-v1.schema.json
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
│   └── review-verdict-v1.schema.json
├── assurance/
│   ├── checker-result-v1.schema.json
│   ├── evidence-snapshot-v1.schema.json
│   └── gate-evaluation-v1.schema.json
├── authority/
│   ├── human-decision-v1.schema.json
│   ├── authority-grant-v1.schema.json
│   └── permit-v1.schema.json
└── lifecycle/
    ├── release-evidence-v1.schema.json
    ├── operation-evidence-v1.schema.json
    └── outcome-review-v1.schema.json
```

Generated Python/TypeScript types, examples, documentation, and validators come
from these schemas and registries. Hand editing generated files fails CI.

## 13. Compatibility and completion

A schema change declares additive/breaking status, upcaster, old/new fixtures,
producer/consumer range, storage/replay effect, active-run policy, rollback, and
removal date. No upcaster changes historical authority meaning.

This specification is implementation-ready only when:

- every listed schema and enum registry exists and validates;
- all templates validate as examples without placeholders;
- canonical digest golden tests pass across Python and TypeScript;
- invalid/unknown/duplicate/stale/wrong-subject fixtures fail closed;
- every producer is the named context and no worker can forge its record;
- hidden-fixture isolation and review independence pass real harness tests; and
- the human owner accepts `AI-G2` evidence.
