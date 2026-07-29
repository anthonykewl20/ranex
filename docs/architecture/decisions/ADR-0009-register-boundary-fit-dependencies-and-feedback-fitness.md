# ADR-0009: Register Boundary Fit, Dependencies, Coupling, and Feedback Fitness

| Field | Value |
|---|---|
| ADR ID | `ADR-0009` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a67843b02d5970f442fb54aed8d6525dda`; executable projection and runtime evidence pending |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | All 34 registered contexts; source dependencies; `governed_execution`; test/build feedback lanes |
| Supersedes | No ADR; completes evidence obligations in ADR-0007 and ADR-0008 |
| Review/expiry date | First clean source tracer, first 20-change coupling window, first 30-candidate feedback window, then quarterly or on a trigger |
| Compatibility/migration class | Additive definition contract; no source/runtime migration is claimed |
| Security/data class | Public design metadata; measured evidence inherits its subject classification |

## Decision

Ranex records boundary quality as a falsifiable hypothesis, not as a conclusion
derived from folder count. It also records every allowed cross-context source
dependency explicitly. The actual import graph must be a subset of that
approved graph, must remain acyclic, and may cross a context only through its
public `api`.

The central `governed_execution` authority is retained because one atomic
authority cell is an explicit consistency requirement. Centrality is not a
waiver from coupling control: responsibility, fan-in, fan-out, interaction
coupling, and change coupling are measured against review/split triggers.

TDD feedback speed is a governed quality attribute. Fast feedback may be
deterministically selected, sharded, cached, and parallelized, but no latency
objective can suppress a required lane, turn flaky/unknown evidence into
`PASS`, or compensate for a failed invariant.

This ADR defines paper contracts and initial falsification thresholds. Every
runtime/source observation starts `NOT_ASSESSED`.

## Canonical projections

The contract compiler projects this ADR to:

```text
architecture/contracts/
├── context-dependency-edges.json
├── context-boundary-fitness.json
├── context-coupling-policy.json
└── feedback-fitness.json

schemas/common/
├── context-dependency-edge-v1.schema.json
├── context-boundary-fit-v1.schema.json
├── context-coupling-policy-v1.schema.json
└── feedback-fitness-policy-v1.schema.json
```

The source ADR owns meaning; the registries own exact executable vocabulary.
Projection mismatch is `CONFLICT`. Missing evidence is `NOT_ASSESSED` before
an attempt and `UNKNOWN` after an insufficient attempt.

## Declared public-API dependency graph

An edge authorizes only the named caller to import
`ranex.<callee>.api`. It grants no database, repository, domain, application,
port, adapter, composition, or effect authority. Edges are denied by default.
A new edge requires owner review, a cycle check, a boundary-fit update, and an
ADR when it changes consistency, authority, security, or a trigger threshold.

### Interaction, consistency, failure, and recovery policies

| ID | Exact meaning |
|---|---|
| `SYNC_QUERY` | Caller reads an immutable public view; callee owns evaluation and state. |
| `SYNC_COMMAND` | Caller submits an idempotent public command; callee alone mutates its state. |
| `ASYNC_EVENT` | Caller consumes a versioned integration event from the callee's transactional outbox. |
| `READ_ONLY_SNAPSHOT` | No shared transaction; caller acts only on an exact versioned snapshot. |
| `CALLEE_TRANSACTION_ONLY` | Command completes in the callee transaction; caller continuation is separate. |
| `EVENTUAL_OUTBOX` | At-least-once delivery with idempotent duplicate/out-of-order handling and reconciliation. |
| `FAIL_CLOSED_REQUIRED` | Timeout, malformed/stale result, denial, or unavailability yields no privileged continuation and a blocking `UNKNOWN`/failure as applicable. |
| `IDEMPOTENT_RETRY_RECONCILE` | Retry only with the same idempotency/subject binding; ambiguous outcome requires observation and reconciliation before another effect. |
| `REFRESH_REEVALUATE` | Fetch a fresh owned snapshot, re-evaluate all dependent decisions, and never reuse a stale permit. |
| `OUTBOX_REPLAY_RECONCILE` | Replay from the owner outbox, deduplicate at the consumer, and reconcile gaps/out-of-order delivery. |

```yaml
dependency_graph_id: "RANEX-CONTEXT-DEPENDENCIES-1.0"
default_policy: "DENY_UNLESS_EXACT_EDGE_REGISTERED"
runtime_validation_status: "NOT_ASSESSED"
edges:
  - {edge_id: "EDGE-POLICY-IDENTITY", caller: "policy", callee: "identity_access", caller_owner: "policy", callee_owner: "identity_access", rationale: "Resolve authenticated principal/session facts for policy evaluation.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-RESOURCE-IDENTITY", caller: "resource_governance", callee: "identity_access", caller_owner: "resource_governance", callee_owner: "identity_access", rationale: "Bind reservations and usage to an authenticated principal.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-HISTORY-IDENTITY", caller: "interaction_history", callee: "identity_access", caller_owner: "interaction_history", callee_owner: "identity_access", rationale: "Bind thread access and retention decisions to identity facts.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-ARTIFACT-IDENTITY", caller: "artifact_management", callee: "identity_access", caller_owner: "artifact_management", callee_owner: "identity_access", rationale: "Authorize classified artifact access through identity facts.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-WORK-PRODUCT", caller: "work_management", callee: "product_definition", caller_owner: "work_management", callee_owner: "product_definition", rationale: "Trace work to owned requirements, acceptance examples, and outcomes.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-WORK-POLICY", caller: "work_management", callee: "policy", caller_owner: "work_management", callee_owner: "policy", rationale: "Evaluate risk lane and required accountable decisions for work transitions.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-WORK-CONFIG", caller: "work_management", callee: "configuration_management", caller_owner: "work_management", callee_owner: "configuration_management", rationale: "Bind work to exact baselines and trace records.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-SERVICE-PRODUCT", caller: "service_management", callee: "product_definition", caller_owner: "service_management", callee_owner: "product_definition", rationale: "Map operated services to product capabilities and outcome owners.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-SUPPLIER-PROVENANCE", caller: "supplier_governance", callee: "provenance_compliance", caller_owner: "supplier_governance", callee_owner: "provenance_compliance", rationale: "Use license, provenance, and SBOM policy facts in supplier decisions.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-INSTRUCTION-CONFIG", caller: "instruction_registry", callee: "configuration_management", caller_owner: "instruction_registry", callee_owner: "configuration_management", rationale: "Bind active instruction packages to configuration baselines.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-REPO-WORKSPACE", caller: "repository_intelligence", callee: "workspace", caller_owner: "repository_intelligence", callee_owner: "workspace", rationale: "Index only an exact repository/worktree/revision identity.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-KNOWLEDGE-ARTIFACT", caller: "knowledge", callee: "artifact_management", caller_owner: "knowledge", callee_owner: "artifact_management", rationale: "Store and retrieve classified knowledge payloads by immutable artifact reference.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-CONTEXT-INSTRUCTION", caller: "context_compilation", callee: "instruction_registry", caller_owner: "context_compilation", callee_owner: "instruction_registry", rationale: "Resolve exact applicable instruction records into a packet.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-CONTEXT-REPO", caller: "context_compilation", callee: "repository_intelligence", caller_owner: "context_compilation", callee_owner: "repository_intelligence", rationale: "Resolve exact source graph evidence for packet construction.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-CONTEXT-KNOWLEDGE", caller: "context_compilation", callee: "knowledge", caller_owner: "context_compilation", callee_owner: "knowledge", rationale: "Resolve approved knowledge records with provenance.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-CONTEXT-CONFIG", caller: "context_compilation", callee: "configuration_management", caller_owner: "context_compilation", callee_owner: "configuration_management", rationale: "Bind the packet to exact configuration and trace baselines.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-ROUTING-SUPPLIER", caller: "routing", callee: "supplier_governance", caller_owner: "routing", callee_owner: "supplier_governance", rationale: "Filter routes by active supplier adoption/support facts.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-ROUTING-RESOURCE", caller: "routing", callee: "resource_governance", caller_owner: "routing", callee_owner: "resource_governance", rationale: "Respect provider limits and reserved budgets during route choice.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-QUAL-MODULE", caller: "qualification", callee: "module_governance", caller_owner: "qualification", callee_owner: "module_governance", rationale: "Qualify an exact module descriptor/version.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-QUAL-ROUTING", caller: "qualification", callee: "routing", caller_owner: "qualification", callee_owner: "routing", rationale: "Qualify an exact provider/model/transport route tuple.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-QUAL-WORKSPACE", caller: "qualification", callee: "workspace", caller_owner: "qualification", callee_owner: "workspace", rationale: "Bind trials to an exact isolated workspace subject.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-ASSURANCE-QUAL", caller: "assurance", callee: "qualification", caller_owner: "assurance", callee_owner: "qualification", rationale: "Accept checker/module/route evidence only from a fresh qualification.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-REVIEW-ROUTING", caller: "analytical_review", callee: "routing", caller_owner: "analytical_review", callee_owner: "routing", rationale: "Bind review attempts to an exact analytical transport route.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-REVIEW-ARTIFACT", caller: "analytical_review", callee: "artifact_management", caller_owner: "analytical_review", callee_owner: "artifact_management", rationale: "Persist immutable review request/response artifacts.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-EFFECTIVENESS-QUAL", caller: "effectiveness", callee: "qualification", caller_owner: "effectiveness", callee_owner: "qualification", rationale: "Compare only qualified modules/routes/graders.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-EFFECTIVENESS-REVIEW", caller: "effectiveness", callee: "analytical_review", caller_owner: "effectiveness", callee_owner: "analytical_review", rationale: "Use independently recorded review observations in outcome experiments.", interaction: "ASYNC_EVENT", consistency: "EVENTUAL_OUTBOX", failure: "FAIL_CLOSED_REQUIRED", recovery: "OUTBOX_REPLAY_RECONCILE"}
  - {edge_id: "EDGE-COLLAB-RESOURCE", caller: "agent_collaboration", callee: "resource_governance", caller_owner: "agent_collaboration", callee_owner: "resource_governance", rationale: "Reserve and settle transitive worker budgets.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-COLLAB-WORKSPACE", caller: "agent_collaboration", callee: "workspace", caller_owner: "agent_collaboration", callee_owner: "workspace", rationale: "Bind assignments and leases to exact workspaces.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-POLICY", caller: "governed_execution", callee: "policy", caller_owner: "governed_execution", callee_owner: "policy", rationale: "Evaluate immutable authorization/risk/decision requirements before transition.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-ASSURANCE", caller: "governed_execution", callee: "assurance", caller_owner: "governed_execution", callee_owner: "assurance", rationale: "Bind fresh exact-subject gate evaluations.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-MODULE", caller: "governed_execution", callee: "module_governance", caller_owner: "governed_execution", callee_owner: "module_governance", rationale: "Resolve active qualified module descriptors and grants.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-IDENTITY", caller: "governed_execution", callee: "identity_access", caller_owner: "governed_execution", callee_owner: "identity_access", rationale: "Bind subject, principal, destination, and secret-handle facts.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-RESOURCE", caller: "governed_execution", callee: "resource_governance", caller_owner: "governed_execution", callee_owner: "resource_governance", rationale: "Reserve and settle run/effect budgets.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-GE-WORKSPACE", caller: "governed_execution", callee: "workspace", caller_owner: "governed_execution", callee_owner: "workspace", rationale: "Validate exact repository/worktree/head before work and effects.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-CONTEXT", caller: "governed_execution", callee: "context_compilation", caller_owner: "governed_execution", callee_owner: "context_compilation", rationale: "Obtain an immutable compiled packet for a run/activity.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-GE-ROUTING", caller: "governed_execution", callee: "routing", caller_owner: "governed_execution", callee_owner: "routing", rationale: "Lock a qualified route tuple for worker activity.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-GE-COLLAB", caller: "governed_execution", callee: "agent_collaboration", caller_owner: "governed_execution", callee_owner: "agent_collaboration", rationale: "Dispatch and fence typed worker assignments without transferring run authority.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-GE-ARTIFACT", caller: "governed_execution", callee: "artifact_management", caller_owner: "governed_execution", callee_owner: "artifact_management", rationale: "Persist and bind immutable run/effect artifacts by reference.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-DELIVERY-IDENTITY", caller: "delivery", callee: "identity_access", caller_owner: "delivery", callee_owner: "identity_access", rationale: "Authenticate channel principals and destinations.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-DELIVERY-WORK", caller: "delivery", callee: "work_management", caller_owner: "delivery", callee_owner: "work_management", rationale: "Submit/query canonical work through channel-neutral commands.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-DELIVERY-GE", caller: "delivery", callee: "governed_execution", caller_owner: "delivery", callee_owner: "governed_execution", rationale: "Submit run commands and render immutable run views.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-DELIVERY-HISTORY", caller: "delivery", callee: "interaction_history", caller_owner: "delivery", callee_owner: "interaction_history", rationale: "Append classified channel messages and continuity facts.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-SCHEDULE-GE", caller: "scheduling", callee: "governed_execution", caller_owner: "scheduling", callee_owner: "governed_execution", rationale: "Submit authenticated scheduled run commands.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-SCHEDULE-DELIVERY", caller: "scheduling", callee: "delivery", caller_owner: "scheduling", callee_owner: "delivery", rationale: "Deliver trigger receipts and operator challenges.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-PROCESS-WORK", caller: "process_assurance", callee: "work_management", caller_owner: "process_assurance", callee_owner: "work_management", rationale: "Bind audits and corrective actions to canonical work.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-PROCESS-ASSURANCE", caller: "process_assurance", callee: "assurance", caller_owner: "process_assurance", callee_owner: "assurance", rationale: "Use immutable product/gate evidence in process assessments.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-PROCESS-SERVICE", caller: "process_assurance", callee: "service_management", caller_owner: "process_assurance", callee_owner: "service_management", rationale: "Relate process findings to service objectives and improvement triggers.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-BACKUP-ARTIFACT", caller: "backup_restore", callee: "artifact_management", caller_owner: "backup_restore", callee_owner: "artifact_management", rationale: "Persist encrypted backup/restore evidence and immutable manifests.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-BACKUP-CONFIG", caller: "backup_restore", callee: "configuration_management", caller_owner: "backup_restore", callee_owner: "configuration_management", rationale: "Bind backup and restore drills to exact configuration baselines.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-OPERATIONS-SERVICE", caller: "operations", callee: "service_management", caller_owner: "operations", callee_owner: "service_management", rationale: "Evaluate health/incidents against owned service objectives.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-OPERATIONS-BACKUP", caller: "operations", callee: "backup_restore", caller_owner: "operations", callee_owner: "backup_restore", rationale: "Initiate and observe idempotent recovery commands.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-OPERATIONS-PROCESS", caller: "operations", callee: "process_assurance", caller_owner: "operations", callee_owner: "process_assurance", rationale: "Create process evidence/corrective-action inputs from incidents.", interaction: "ASYNC_EVENT", consistency: "EVENTUAL_OUTBOX", failure: "FAIL_CLOSED_REQUIRED", recovery: "OUTBOX_REPLAY_RECONCILE"}
  - {edge_id: "EDGE-RELEASE-CONFIG", caller: "release_management", callee: "configuration_management", caller_owner: "release_management", callee_owner: "configuration_management", rationale: "Build only an exact accepted configuration baseline.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-RELEASE-PROVENANCE", caller: "release_management", callee: "provenance_compliance", caller_owner: "release_management", callee_owner: "provenance_compliance", rationale: "Require license/provenance/SBOM compliance before packaging.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-RELEASE-SUPPLIER", caller: "release_management", callee: "supplier_governance", caller_owner: "release_management", callee_owner: "supplier_governance", rationale: "Require supported and approved dependency facts.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-RELEASE-SERVICE", caller: "release_management", callee: "service_management", caller_owner: "release_management", callee_owner: "service_management", rationale: "Bind release/support/rollback records to an owned service.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-UPSTREAM-WORKSPACE", caller: "upstream_sync", callee: "workspace", caller_owner: "upstream_sync", callee_owner: "workspace", rationale: "Operate only in a dedicated exact sync worktree.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-UPSTREAM-CONFIG", caller: "upstream_sync", callee: "configuration_management", caller_owner: "upstream_sync", callee_owner: "configuration_management", rationale: "Record observed/audited/incorporated upstream baselines.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-UPSTREAM-PROVENANCE", caller: "upstream_sync", callee: "provenance_compliance", caller_owner: "upstream_sync", callee_owner: "provenance_compliance", rationale: "Classify license/provenance impact before accepting a port set.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-MIGRATION-CONFIG", caller: "migration", callee: "configuration_management", caller_owner: "migration", callee_owner: "configuration_management", rationale: "Apply only a versioned ordered migration manifest.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-MIGRATION-BACKUP", caller: "migration", callee: "backup_restore", caller_owner: "migration", callee_owner: "backup_restore", rationale: "Require and verify a recovery point around migration.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-EXTENSION-IDENTITY", caller: "extension_host", callee: "identity_access", caller_owner: "extension_host", callee_owner: "identity_access", rationale: "Authenticate extension principals and sessions.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-EXTENSION-POLICY", caller: "extension_host", callee: "policy", caller_owner: "extension_host", callee_owner: "policy", rationale: "Evaluate grants and requested capabilities fail closed.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-EXTENSION-MODULE", caller: "extension_host", callee: "module_governance", caller_owner: "extension_host", callee_owner: "module_governance", rationale: "Map extension capabilities to registered host contracts.", interaction: "SYNC_QUERY", consistency: "READ_ONLY_SNAPSHOT", failure: "FAIL_CLOSED_REQUIRED", recovery: "REFRESH_REEVALUATE"}
  - {edge_id: "EDGE-COMPAT-GE", caller: "compatibility", callee: "governed_execution", caller_owner: "compatibility", callee_owner: "governed_execution", rationale: "Submit translated legacy requests without receiving authority.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-COMPAT-DELIVERY", caller: "compatibility", callee: "delivery", caller_owner: "compatibility", callee_owner: "delivery", rationale: "Translate legacy CLI/channel requests through canonical delivery commands.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
  - {edge_id: "EDGE-COMPAT-HISTORY", caller: "compatibility", callee: "interaction_history", caller_owner: "compatibility", callee_owner: "interaction_history", rationale: "Import legacy session history through the owned public API.", interaction: "SYNC_COMMAND", consistency: "CALLEE_TRANSACTION_ONLY", failure: "FAIL_CLOSED_REQUIRED", recovery: "IDEMPOTENT_RETRY_RECONCILE"}
```

The compiler validates unique IDs and pairs, known owners, no self-edge, exact
public API target, and acyclicity. An actual source import not present above is
not an “emergent dependency”; it is a blocking architecture violation.

## Boundary-fit hypotheses for all registered contexts

Each row is a design hypothesis. `merge_candidate` and `split_candidate` are
alternatives to evaluate if the falsifier fires; neither is a scheduled
reorganization. Empty runtime evidence never makes a row pass. Its stable
architecture-element ID is exactly `BOUNDARYFIT-` followed by the upper-kebab
form of `context_id` (for example,
`BOUNDARYFIT-GOVERNED-EXECUTION`); the compiler derives and validates that
one-to-one mapping.

```yaml
boundary_fit_set_id: "RANEX-CONTEXT-BOUNDARY-FIT-1.0"
expected_context_count: 34
runtime_validation_status: "NOT_ASSESSED"
rows:
  - {context_id: "governed_execution", owner: "governed_execution", consistency_hypothesis: "One atomic run/transition/grant/permit/effect-intent transaction.", failure_hypothesis: "Failure halts privileged continuation and preserves replayable intent.", ownership_hypothesis: "Only this context owns run and execution authority.", change_locality_hypothesis: "Authority semantics change here; policy/evidence semantics remain in their owners.", merge_candidate: "none unless authority and policy become one consistency boundary", split_candidate: "effect ledger or process manager after a coupling trigger", tracer_falsifier: "crash/replay/permit reuse or a change requiring private knowledge from three owners"}
  - {context_id: "policy", owner: "policy", consistency_hypothesis: "One versioned policy/risk/decision snapshot.", failure_hypothesis: "Unavailable or malformed policy denies privileged continuation.", ownership_hypothesis: "Only policy owns eligibility/risk/waiver meaning.", change_locality_hypothesis: "Rule changes avoid execution-state edits.", merge_candidate: "identity_access only if policy and identity lifecycle prove inseparable", split_candidate: "policy package evaluation from human-decision records", tracer_falsifier: "one rule change repeatedly modifies governed_execution internals"}
  - {context_id: "assurance", owner: "assurance", consistency_hypothesis: "One exact-subject evidence snapshot and GateEvaluation.", failure_hypothesis: "Stale/missing/conflicting proof remains UNKNOWN and blocks.", ownership_hypothesis: "Only assurance converts eligible evidence into gate evaluation.", change_locality_hypothesis: "Checker/evidence changes avoid run-state edits.", merge_candidate: "qualification only if evidence and qualification lifecycle cannot be separated", split_candidate: "evidence catalog from gate evaluation after independent scaling pressure", tracer_falsifier: "wrong-subject or stale evidence can authorize a transition"}
  - {context_id: "module_governance", owner: "module_governance", consistency_hypothesis: "One module descriptor/grant/activation version.", failure_hypothesis: "Unknown or incompatible module remains inactive.", ownership_hypothesis: "Only this context owns module catalog and activation.", change_locality_hypothesis: "Module lifecycle changes avoid worker/run authority edits.", merge_candidate: "extension_host only if first- and third-party lifecycle converge", split_candidate: "catalog from activation after lifecycle divergence", tracer_falsifier: "import registration activates an undeclared module"}
  - {context_id: "identity_access", owner: "identity_access", consistency_hypothesis: "One authenticated principal/session/destination-fact snapshot.", failure_hypothesis: "Authentication or secret resolution failure denies access/effect.", ownership_hypothesis: "Only this context owns identity/session/secret handles.", change_locality_hypothesis: "Authentication changes do not alter policy rules.", merge_candidate: "policy only if lifecycle evidence demands it", split_candidate: "secret projection from authentication after security/isolation trigger", tracer_falsifier: "a stale session or raw secret crosses a public boundary"}
  - {context_id: "product_definition", owner: "product_definition", consistency_hypothesis: "One requirement/acceptance/outcome baseline.", failure_hypothesis: "Conflicting or unapproved need remains unresolved work input.", ownership_hypothesis: "Only this context owns product intent and acceptance meaning.", change_locality_hypothesis: "Requirement changes propagate by trace rather than private imports.", merge_candidate: "work_management only if intent and execution status cannot vary independently", split_candidate: "outcome validation from requirements after ownership divergence", tracer_falsifier: "work status silently changes product acceptance"}
  - {context_id: "work_management", owner: "work_management", consistency_hypothesis: "One canonical work item/status/queue transaction.", failure_hypothesis: "Invalid transition leaves work unchanged and auditable.", ownership_hypothesis: "Only this context owns WorkItemStatus and work queues.", change_locality_hypothesis: "Workflow changes avoid product/run state mutation.", merge_candidate: "product_definition only if discovery and delivery lifecycle collapse", split_candidate: "portfolio/queue projection from transactional work state", tracer_falsifier: "another context writes work status or a board becomes authority"}
  - {context_id: "service_management", owner: "service_management", consistency_hypothesis: "One service/objective/support lifecycle record.", failure_hypothesis: "Missing owner/SLO/support fact blocks release/operation decision.", ownership_hypothesis: "Only this context owns service catalog and objectives.", change_locality_hypothesis: "SLO/support changes avoid incident/release implementation edits.", merge_candidate: "operations only if service definition and incident state cannot diverge", split_candidate: "objective/error-budget policy from service catalog", tracer_falsifier: "release or operations invents its own service owner/SLO"}
  - {context_id: "configuration_management", owner: "configuration_management", consistency_hypothesis: "One content-addressed baseline/status-accounting transaction.", failure_hypothesis: "Digest/trace/audit mismatch blocks use.", ownership_hypothesis: "Only this context owns configuration baselines and trace graph.", change_locality_hypothesis: "New configuration item types avoid consumer-specific rules.", merge_candidate: "none; cross-cutting baseline authority remains explicit", split_candidate: "contract generation from baseline/audit after independent change pressure", tracer_falsifier: "two canonical paths or mutable baseline identity appear"}
  - {context_id: "supplier_governance", owner: "supplier_governance", consistency_hypothesis: "One supplier adoption/support/exit decision.", failure_hypothesis: "Unknown support/vulnerability/concentration blocks adoption or release.", ownership_hypothesis: "Only this context owns supplier acceptance and exit policy.", change_locality_hypothesis: "Supplier changes avoid route/release private rules.", merge_candidate: "provenance_compliance only if adoption and legal decisions share lifecycle", split_candidate: "monitoring from adoption decisions after cadence divergence", tracer_falsifier: "routing activates an unapproved supplier"}
  - {context_id: "resource_governance", owner: "resource_governance", consistency_hypothesis: "One hierarchical reservation/usage settlement transaction.", failure_hypothesis: "Capacity/budget ambiguity denies new allocation and reconciles usage.", ownership_hypothesis: "Only this context owns budgets, quotas, and usage attribution.", change_locality_hypothesis: "Budget rules change without worker/run state rewrites.", merge_candidate: "agent_collaboration only if leases and resource reservations prove one aggregate", split_candidate: "rate/usage catalog from reservations", tracer_falsifier: "child work exceeds parent reservation or usage lacks attribution"}
  - {context_id: "interaction_history", owner: "interaction_history", consistency_hypothesis: "One classified thread/message/retention append.", failure_hypothesis: "Failed append/access/delete remains explicit and retryable.", ownership_hypothesis: "Only this context owns conversation continuity and deletion.", change_locality_hypothesis: "Channel changes do not redefine history lifecycle.", merge_candidate: "delivery only if channel receipt and durable history cannot diverge", split_candidate: "search index projection from canonical history", tracer_falsifier: "delivery stores an authoritative parallel transcript"}
  - {context_id: "process_assurance", owner: "process_assurance", consistency_hypothesis: "One process assessment/audit/corrective-action record.", failure_hypothesis: "Missing/biased evidence remains UNKNOWN and cannot raise maturity.", ownership_hypothesis: "Only this context owns process conformance and improvement evidence.", change_locality_hypothesis: "Process metrics do not alter product gate authority.", merge_candidate: "assurance only if process/product evidence lifecycles converge", split_candidate: "fleet experiments from audits after independent cadence", tracer_falsifier: "an aggregate score hides one failed control"}
  - {context_id: "workspace", owner: "workspace", consistency_hypothesis: "One repository/worktree/head/landing identity plan.", failure_hypothesis: "Path/head/ancestry mismatch blocks writing or landing.", ownership_hypothesis: "Only this context owns workspace lifecycle and landing plan.", change_locality_hypothesis: "Git topology changes avoid domain state edits.", merge_candidate: "upstream_sync only if all workspace use becomes sync-specific", split_candidate: "landing from workspace allocation after concurrency pressure", tracer_falsifier: "a write lands outside the bound worktree/head"}
  - {context_id: "instruction_registry", owner: "instruction_registry", consistency_hypothesis: "One immutable instruction/version/precedence activation.", failure_hypothesis: "Conflict or missing applicability blocks packet sealing.", ownership_hypothesis: "Only this context owns instruction semantics and precedence.", change_locality_hypothesis: "Instruction edits avoid compiler/run authority changes.", merge_candidate: "context_compilation only if instructions have no independent lifecycle", split_candidate: "activation from immutable registry after cadence divergence", tracer_falsifier: "packet output depends on unregistered ambient instructions"}
  - {context_id: "context_compilation", owner: "context_compilation", consistency_hypothesis: "One exact resolved-source packet manifest/digest.", failure_hypothesis: "Conflict, missing source, budget overflow, or freshness failure blocks sealing.", ownership_hypothesis: "Only this context owns packet compilation and source resolution.", change_locality_hypothesis: "Source-provider changes stay behind ports.", merge_candidate: "instruction_registry only if compilation and instruction lifecycle collapse", split_candidate: "retrieval orchestration from canonical packet compiler", tracer_falsifier: "same resolved inputs produce different packet digest"}
  - {context_id: "analytical_review", owner: "analytical_review", consistency_hypothesis: "One immutable request/attempt/observation/verdict chain.", failure_hypothesis: "Parse/transport/independence failure remains an observation, never gate evidence by itself.", ownership_hypothesis: "Only this context owns analytical review records.", change_locality_hypothesis: "Provider changes stay in routing/adapters.", merge_candidate: "assurance only if analytical observation becomes gate authority", split_candidate: "transport attempts from normalized review semantics", tracer_falsifier: "model output directly authorizes a gate"}
  - {context_id: "routing", owner: "routing", consistency_hypothesis: "One release-pinned provider/model/transport route lock.", failure_hypothesis: "Unhealthy/mismatched route fails or follows declared fallback without identity substitution.", ownership_hypothesis: "Only this context owns route identity and fallback inputs.", change_locality_hypothesis: "Provider additions avoid domain/run rules.", merge_candidate: "qualification only if route lifecycle cannot vary independently", split_candidate: "health catalog from route policy", tracer_falsifier: "fallback silently changes model/transport identity"}
  - {context_id: "qualification", owner: "qualification", consistency_hypothesis: "One exact-tuple trial/calibration/expiry record.", failure_hypothesis: "Insufficient or expired evidence leaves subject unqualified.", ownership_hypothesis: "Only this context owns qualification lifecycle.", change_locality_hypothesis: "New trial types avoid module/routing authority edits.", merge_candidate: "effectiveness only if qualification and comparative outcomes share decisions", split_candidate: "grader calibration from subject qualification", tracer_falsifier: "qualification is reused for a different tuple/version"}
  - {context_id: "effectiveness", owner: "effectiveness", consistency_hypothesis: "One predeclared paired experiment/scorecard record.", failure_hypothesis: "Bias, attrition, grader drift, or insufficient sample remains inconclusive.", ownership_hypothesis: "Only this context owns comparative workflow-effectiveness conclusions.", change_locality_hypothesis: "Experiment changes do not alter qualification or runtime authority.", merge_candidate: "qualification only if comparative and minimum-threshold decisions converge", split_candidate: "scorecard reporting from experiment design", tracer_falsifier: "proxy score compensates for a failed guardrail"}
  - {context_id: "agent_collaboration", owner: "agent_collaboration", consistency_hypothesis: "One assignment/offer/lease/epoch/mailbox ownership transaction.", failure_hypothesis: "Lost/stale worker is fenced and reclaim is explicit.", ownership_hypothesis: "Only this context owns worker coordination state.", change_locality_hypothesis: "Harness/provider changes remain adapters.", merge_candidate: "resource_governance only if leases and reservations prove one aggregate", split_candidate: "mailbox delivery from lease lifecycle after scaling pressure", tracer_falsifier: "two workers hold valid ownership or a stale epoch writes"}
  - {context_id: "repository_intelligence", owner: "repository_intelligence", consistency_hypothesis: "One exact-revision source graph/index snapshot.", failure_hypothesis: "Unsupported/stale/partial analysis is explicit UNKNOWN.", ownership_hypothesis: "Only this context owns derived repository intelligence.", change_locality_hypothesis: "Parser changes remain adapters/qualified modules.", merge_candidate: "workspace only if index lifecycle cannot outlive workspace plans", split_candidate: "language parser qualification from index/query service", tracer_falsifier: "analysis claims coverage for unsupported files"}
  - {context_id: "knowledge", owner: "knowledge", consistency_hypothesis: "One provenance/classification/quarantine lifecycle record.", failure_hypothesis: "Untrusted/unsanitized knowledge remains quarantined.", ownership_hypothesis: "Only this context owns approved memory/learning records.", change_locality_hypothesis: "Backend changes stay behind ports.", merge_candidate: "context_compilation only if knowledge has no independent approval lifecycle", split_candidate: "sanitization/quarantine from retrieval after security pressure", tracer_falsifier: "unapproved learned content enters a sealed packet"}
  - {context_id: "scheduling", owner: "scheduling", consistency_hypothesis: "One schedule/trigger/authentication/catch-up lifecycle.", failure_hypothesis: "Duplicate/missed trigger is idempotently recorded and reconciled.", ownership_hypothesis: "Only this context owns schedule and trigger state.", change_locality_hypothesis: "Trigger technology remains adapter-local.", merge_candidate: "delivery only if scheduling has no independent lifecycle", split_candidate: "trigger authentication from schedule policy", tracer_falsifier: "duplicate trigger creates duplicate privileged effect"}
  - {context_id: "delivery", owner: "delivery", consistency_hypothesis: "One channel-neutral command/message/receipt record.", failure_hypothesis: "Channel failure preserves command idempotency and explicit delivery status.", ownership_hypothesis: "Only this context owns delivery rendering and receipts.", change_locality_hypothesis: "New channel changes adapters, not authority rules.", merge_candidate: "interaction_history only if receipt and history lifecycle converge", split_candidate: "rendering from command ingress after channel divergence", tracer_falsifier: "a channel bypasses canonical command/decision authority"}
  - {context_id: "artifact_management", owner: "artifact_management", consistency_hypothesis: "One content-addressed catalog/classification/retention record.", failure_hypothesis: "Ambiguous write/access/purge is reconciled without losing legal hold.", ownership_hypothesis: "Only this context owns artifact lifecycle metadata.", change_locality_hypothesis: "Blob backend changes stay behind ports.", merge_candidate: "backup_restore only if backup and general artifact lifecycle converge", split_candidate: "blob storage from catalog/retention after scale pressure", tracer_falsifier: "same digest resolves to different bytes or purge violates hold"}
  - {context_id: "operations", owner: "operations", consistency_hypothesis: "One incident/health/reconciliation scheduling record.", failure_hypothesis: "Unknown health or recovery outcome remains explicit and escalated.", ownership_hypothesis: "Only this context owns incident and operational response state.", change_locality_hypothesis: "Telemetry backend changes stay adapters.", merge_candidate: "service_management only if objective and incident lifecycle collapse", split_candidate: "alert ingestion from incident coordination", tracer_falsifier: "operator action mutates another context without public command"}
  - {context_id: "backup_restore", owner: "backup_restore", consistency_hypothesis: "One encrypted backup-set/recovery-point/restore verification record.", failure_hypothesis: "Unverified restore remains failed/unknown and unreleased.", ownership_hypothesis: "Only this context owns backup/restore lifecycle.", change_locality_hypothesis: "Storage backend changes stay behind ports.", merge_candidate: "artifact_management only if backup policy has no independent lifecycle", split_candidate: "backup creation from restore/reconciliation after risk divergence", tracer_falsifier: "restore reports success before external reconciliation"}
  - {context_id: "release_management", owner: "release_management", consistency_hypothesis: "One build/release/install/update/rollback manifest.", failure_hypothesis: "Digest/SBOM/provenance/install mismatch blocks promotion.", ownership_hypothesis: "Only this context owns release lifecycle.", change_locality_hypothesis: "Packaging technology stays adapters/tools.", merge_candidate: "configuration_management only if baseline and release lifecycle cannot diverge", split_candidate: "installer/updater operations from release decision", tracer_falsifier: "different artifact is tested and released"}
  - {context_id: "upstream_sync", owner: "upstream_sync", consistency_hypothesis: "One observed/audited/incorporated baseline and port-set decision.", failure_hypothesis: "Ancestry/provenance/conflict uncertainty blocks incorporation.", ownership_hypothesis: "Only this context owns upstream synchronization lifecycle.", change_locality_hypothesis: "Upstream layout changes remain classified at boundary.", merge_candidate: "workspace only if all workspace lifecycle becomes sync-specific", split_candidate: "diff classification from port execution after cadence pressure", tracer_falsifier: "unreviewed upstream code recontaminates authority core"}
  - {context_id: "migration", owner: "migration", consistency_hypothesis: "One ordered migration/upcaster/rollback/tombstone plan.", failure_hypothesis: "Partial/dirty/version-incompatible migration stops and restores/reconciles.", ownership_hypothesis: "Only this context owns cross-context migration ordering.", change_locality_hypothesis: "Context schema remains owner-local.", merge_candidate: "configuration_management only if migration ordering becomes baseline-only", split_candidate: "legacy import from schema/upcaster migration", tracer_falsifier: "one context writes another context schema or rollback is impossible"}
  - {context_id: "extension_host", owner: "extension_host", consistency_hypothesis: "One protocol session/capability grant/quarantine lifecycle.", failure_hypothesis: "Protocol/identity/policy violation terminates and quarantines extension.", ownership_hypothesis: "Only this context owns lower-trust extension sessions.", change_locality_hypothesis: "Extension implementations remain out of process.", merge_candidate: "module_governance only if trust/lifecycle become identical", split_candidate: "protocol transport from grant/quarantine decisions", tracer_falsifier: "extension imports host internals or gains undeclared capability"}
  - {context_id: "compatibility", owner: "compatibility", consistency_hypothesis: "No canonical state; one versioned translation/contained legacy-call result.", failure_hypothesis: "Legacy failure is contained and returned as typed result/proposal.", ownership_hypothesis: "Compatibility owns translation only, never product authority.", change_locality_hypothesis: "Legacy changes do not leak into Ranex domain.", merge_candidate: "none while strangler isolation is required", split_candidate: "legacy state/CLI/plugin translators when removal schedules diverge", tracer_falsifier: "new Ranex domain rule lands in legacy or legacy writes authority tables"}
  - {context_id: "provenance_compliance", owner: "provenance_compliance", consistency_hypothesis: "One file/license/notice/SBOM compliance decision.", failure_hypothesis: "Unknown or prohibited provenance blocks adoption/release.", ownership_hypothesis: "Only this context owns provenance/compliance classification.", change_locality_hypothesis: "Scanner changes remain adapters; policy meaning stays here.", merge_candidate: "supplier_governance only if legal and adoption lifecycle become one", split_candidate: "SBOM scanning from legal decision after tool/cadence divergence", tracer_falsifier: "unclassified file or prohibited dependency reaches release"}
```

## `governed_execution` coupling policy

The first measurement window is the first clean tracer and thereafter every
candidate plus a rolling 20 accepted-change window. `process_assurance` owns
measurement integrity; the architecture owner owns review/split decisions.

```yaml
coupling_policy_id: "RANEX-GE-COUPLING-1.0"
subject_context: "governed_execution"
runtime_validation_status: "NOT_ASSESSED"
measures:
  - {measure_id: "GE-RESPONSIBILITY-COUNT", definition: "Count distinct registered governed_execution responsibility clauses.", cadence: "each architecture change", review_trigger: "> 12 or +2 in one rolling 20-change window"}
  - {measure_id: "GE-STATIC-FAN-OUT", definition: "Count approved outgoing source-dependency edges.", cadence: "each edge/architecture change", review_trigger: "> 10"}
  - {measure_id: "GE-STATIC-FAN-IN", definition: "Count approved incoming source-dependency edges.", cadence: "each edge/architecture change", review_trigger: "> 8"}
  - {measure_id: "GE-INTERACTION-COUPLING", definition: "Distribution of distinct synchronous context calls per authority transition.", cadence: "each tracer/release; rolling 30 transitions", review_trigger: "p95 > 8 or > 25% of transitions call more than 4 contexts"}
  - {measure_id: "GE-CHANGE-COUPLING", definition: "Distribution of other contexts changed with governed_execution per accepted change.", cadence: "rolling 20 accepted changes", review_trigger: "> 35% of governed_execution changes require changes in 3 or more other contexts"}
  - {measure_id: "GE-OWNERSHIP-CONCENTRATION", definition: "Share of architecture-changing work items that touch governed_execution.", cadence: "each release; rolling 3 releases", review_trigger: "> 40% for 3 consecutive releases"}
responses:
  - "Inspect responsibility and edge records; reject hidden private knowledge."
  - "Evaluate moving orchestration-only behavior to an owner context or splitting an independently consistent ledger/process."
  - "Evaluate merging a false boundary when paired changes and shared invariants prove one owner."
  - "Record keep/split/merge decision and counterevidence in a superseding ADR."
noncompensating: true
```

A trigger requires review; it does not automatically force microservices,
decentralization, or a split. A low average cannot hide a high-tail transition
or repeatedly coupled change.

## Feedback-latency, selection, sharding, and escalation

Objectives are measured on the versioned reference local host profile and the
same built candidate artifact. `process_assurance` owns measurement policy;
`configuration_management` owns the candidate/test manifest; the technical
owner owns remediation. A host/profile change resets the baseline and cannot
silently claim improvement.

```yaml
feedback_policy_id: "RANEX-TDD-FEEDBACK-1.0"
runtime_validation_status: "NOT_ASSESSED"
objectives:
  - {objective_id: "TDD-FEEDBACK-FAST-P50", lane: "FAST_LOOP", measure: "candidate change ID to unit+contract+architecture result", statistic: "p50", target: "<= 60 seconds", window: "rolling 30 candidates", cadence: "every candidate"}
  - {objective_id: "TDD-FEEDBACK-FAST-P95", lane: "FAST_LOOP", measure: "candidate change ID to unit+contract+architecture result", statistic: "p95", target: "<= 180 seconds", window: "rolling 30 candidates", cadence: "every candidate"}
  - {objective_id: "TDD-FEEDBACK-PREVERIFY-P50", lane: "PRE_VERIFICATION", measure: "candidate artifact digest to all required SQLite/integration/acceptance/security results", statistic: "p50", target: "<= 10 minutes", window: "rolling 30 candidates", cadence: "every verification candidate"}
  - {objective_id: "TDD-FEEDBACK-PREVERIFY-P95", lane: "PRE_VERIFICATION", measure: "candidate artifact digest to all required SQLite/integration/acceptance/security results", statistic: "p95", target: "<= 20 minutes", window: "rolling 30 candidates", cadence: "every verification candidate"}
selection:
  manifest_required: true
  rule: "Required tests are selected from changed owner/context, declared dependency closure, risk lane, failure matrix, and always-run authority/security sets."
  omission_status: "UNKNOWN_BLOCKING"
sharding:
  rule: "sha256(test_id + suite_version) modulo declared shard_count"
  recorded_fields: ["suite_version", "test_manifest_digest", "shard_count", "test_id", "shard_id", "selection_reason"]
  determinism_required: true
escalation:
  - "Any FAIL, UNKNOWN, flake/quarantine, changed dependency edge, migration, authority/security path, or selection ambiguity adds the full affected lane; it never removes evidence."
  - "A CRITICAL/EMERGENCY risk profile runs every profile-required lane regardless of change selection."
  - "Three consecutive breached windows create an owned improvement work item: optimize fixtures/setup, remove accidental I/O, deterministically shard/parallelize, add capacity, or redesign a boundary."
  - "Moving a test to a later lane requires an accountable risk decision and preserves the same pre-release gate."
noncompensating: true
```

No suite-speed result compensates for a failed, flaky, stale, missing,
wrong-subject, or unknown behavior result.

## Machine-checkable rules and fitness evidence

```yaml
boundary_fitness_rule_set: "RANEX-BOUNDARY-FITNESS-1.0"
rules:
  - {id: "ARCH-EDGE-001", enforcement: "BLOCK", invariant: "Every allowed cross-context source dependency is one exact owned public-api edge with interaction, consistency, failure, and recovery semantics."}
  - {id: "ARCH-EDGE-002", enforcement: "BLOCK", invariant: "Actual cross-context imports are a subset of approved edges and target only the callee api package."}
  - {id: "ARCH-EDGE-003", enforcement: "BLOCK", invariant: "Declared and actual context dependency graphs are acyclic; missing or ambiguous edge identity blocks."}
  - {id: "ARCH-BOUNDARY-001", enforcement: "BLOCK", invariant: "Every registered context has exactly one boundary-fit row with all hypothesis, alternative, owner, and falsifier fields."}
  - {id: "ARCH-BOUNDARY-002", enforcement: "BLOCK", invariant: "A fired falsifier or material unknown blocks a mature/proven boundary claim until an owned keep, merge, or split decision."}
  - {id: "ARCH-COUPLING-001", enforcement: "BLOCK", invariant: "governed_execution responsibility, fan-in, fan-out, interaction, change, and ownership-concentration distributions are exact-subject measured at the declared cadence."}
  - {id: "ARCH-COUPLING-002", enforcement: "BLOCK", invariant: "A coupling trigger creates independent boundary review and cannot be dismissed by an average or central-authority necessity."}
  - {id: "TDD-FEEDBACK-001", enforcement: "REQUIRED", invariant: "Fast-loop and pre-verification latency distributions bind the declared host, artifact, manifest, window, owner, and cadence."}
  - {id: "TDD-FEEDBACK-002", enforcement: "BLOCK", invariant: "Selection, sharding, caching, and escalation are deterministic, recorded, risk-aware, and cannot omit a required lane."}
  - {id: "ARCH9-NONCOMP-001", enforcement: "BLOCK", invariant: "No boundary, coupling, or feedback metric compensates for another failed, stale, missing, or unknown obligation."}
```

| Fitness ID | Required evidence |
|---|---|
| `FF-EDGE-001` | Exact edge registry has unique known owners/pairs, complete semantics, and no unapproved/default edge. |
| `FF-EDGE-002` | Static import graph proves public-API-only actual ⊆ declared, no cycles, and no private/adapter/legacy leak. |
| `FF-BOUNDARYFIT-001` | Boundary registry has exactly the 34 canonical context IDs and every required fit field. |
| `FF-BOUNDARY-002` | Representative tracers attempt each applicable falsifier and bind keep/merge/split disposition without claiming exhaustive proof. |
| `FF-COUPLING-001` | Exact-subject static and rolling runtime/change distributions compute all six governed-execution measures. |
| `FF-COUPLING-002` | Threshold fixtures prove every trigger creates a blocking review record and no average suppresses it. |
| `FF-FEEDBACK-001` | Thirty-candidate reference-host distributions compute all four latency objectives without excluding failures/timeouts. |
| `FF-FEEDBACK-002` | Repeated generation produces identical selection/shards; changed dependency/risk/failure fixtures escalate and never reduce lanes. |
| `FF-ARCH9-NONCOMP-001` | A fixture with excellent latency/low coupling plus one failed/unknown rule remains nonsealing. |

Every result is currently `NOT_ASSESSED`. Initial numerical objectives and
triggers are owner-selected falsification thresholds, not book constants or
achievement claims. Evidence may justify a superseding ADR; silent threshold
drift is prohibited.

## Engineering-reference application and limits

| Practice ID | Retained locator | Applied use and strict limit |
|---|---|---|
| `ENGREF-PRAGMATIC-PROGRAMMER-1E-ORTHOGONALITY` | `ENGREF-PRAGMATIC-PROGRAMMER-1E-MD`, “Orthogonality,” lines 1393–1449 | Explicit dependency/change coupling. Perfect independence is neither possible nor required; necessary coupling must remain explicit. |
| `ENGREF-CLEAN-ARCHITECTURE-1E-DEPENDENCY-RULE` | Registered PDF, Ch.22, sequence pp.161–162 | Public inward dependencies. The rule must be reconciled with language, performance, data ownership, and operational constraints rather than applied ceremonially. |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-BOUNDARY-QUANTA` | `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-MD`, lines 2608–2635 | Per-context boundary hypotheses/falsifiers. More components or bounded contexts do not automatically mean better modularity. |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-ORCHESTRATION-COUPLING` | Same representation, lines 4416–4508 | Central-authority coupling distributions/triggers. Central authority can be necessary; the risk is unbounded responsibility and knowledge, not centrality by itself. |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS` | Same representation, lines 700–716 | Continuous dependency/boundary/coupling/feedback checks. A proxy count or one-time document check is not proof of sustained effectiveness. |
| `ENGREF-APOSD-1E-COMPLEXITY-SYMPTOMS` | Registered PDF, Ch.2, sequence pp.18–24 | Treat change amplification, cognitive load, and unknown unknowns as separate diagnostics backed by change and comprehension evidence, never additive points. |
| `ENGREF-APOSD-1E-DEEP-MODULES` | Same representation, Ch.4, sequence pp.31–39 | Evaluate public interface burden relative to useful complexity hidden while rejecting shallow indirection, god modules, and ambiguous authority. |
| `ENGREF-APOSD-1E-DESIGN-TWICE` | Same representation, Ch.11, sequence pp.99–101 | Preserve multiple viable shapes, tradeoffs, reversibility, and falsifiers for consequential boundary choices; no ceremonial alternatives for trivial reversible changes. |

## Alternatives considered

1. **Infer dependencies from imports.** Rejected because current code would
   define architecture and normalize accidental coupling.
2. **Require no cross-context dependencies.** Rejected because necessary
   collaboration would move into shared databases, global helpers, or hidden
   service locators.
3. **Split governed execution now.** Rejected because one atomic authority
   cell is required and no measured split evidence exists.
4. **Treat 34 folders as validated DDD.** Rejected because fit is an empirical
   change/consistency/failure/ownership claim.
5. **Use suite duration averages or skip slow tests.** Rejected because tails,
   omissions, failures, and selection integrity are material.

## Consequences and adoption

The dependency graph is more restrictive: an implementation cannot create a
cross-context import merely because both packages exist. Boundary rows make
merge/split alternatives and falsifiers inspectable without prematurely
choosing microservices. Coupling and feedback objectives create measurement
work in the first clean tracer and every declared window.

The contract lane must project this ADR and add its ten rule rows to the
noncompensating architecture-rule assessment registry. Those rows remain
`NOT_ASSESSED`; existing 37 rows cannot be averaged or promoted to cover them.

## Human approval

The human owner required explicit dependency, boundary-fit, central-coupling,
and feedback-latency closure before any claim that the architecture is mature,
proven, or build-ready. This ADR records the paper decision and falsification
plan. It does not claim source, test, runtime, operational, or outcome proof.
