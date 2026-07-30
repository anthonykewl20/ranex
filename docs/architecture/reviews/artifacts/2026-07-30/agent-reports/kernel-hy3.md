[0m
> build · tencent/hy3
[0m
[0m$ [0mgit status --short | head -50; git branch --show-current; pwd
M .gitignore
?? pyproject.toml
?? src/
?? tests/
?? uv.lock
feature/kernel-tracer
/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer
[0m
[0m✱ [0mGlob "src/ranex/**/*.py"[90m 47 matches[0m
[0m✱ [0mGlob "tests/**/*.py"[90m 15 matches[0m
[0m→ [0mRead docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
[0m
[0m$ [0msed -n '1880,1930p' docs/research/hermes-core-architecture-research-2026-07-27.md
- Extract neutral conversation context, provider-access failures, BYOK
  credential contracts, and cost normalization from mixed files.
- Remove Nous branches from auth, credential pool, runtime-provider, model
  setup, agent loop, auxiliary calls, tool configuration, gateway, session
  state, desktop, and TUI monoliths.
- Rename generic `billing_*` route fields to provider/cost terminology and
  migrate only operational usage data.
- Establish Ranex-owned package names, CLI entry point, configuration root,
  environment namespace, request attribution, and UI identity. Read old
  `HERMES_HOME` data only through the migration shim.
- Rebrand package/runtime surfaces while preserving required upstream
  licenses, copyright, provenance, and history.
- Run the zero-monetization route, package, schema, network, and SBOM gates.

**Exit:** a clean host can run a qualified non-Nous model route with token/cost
budgets, while no runtime or packaged path can resolve a Nous commercial
provider, contact its services, display a purchase surface, or deserialize
commercial account state.

### Phase 1 — create the clean kernel beside Hermes

- Implement shared identity and canonical serialization.
- Implement an `Execution` aggregate and pure reducer.
- Implement canonical relational execution state/version plus an append-only
  transition/audit journal and outbox in one SQLite unit of work. Event-source
  only the execution aggregate if its replay/migration tests justify that
  choice; do not event-source every module.
- Implement a fail-closed application-control PEP with pure domain decisions
  and a simple deterministic policy adapter.
- Add architecture import tests before feature code.

**Exit:** reducer replay and crash-boundary tests pass with no Hermes import.

### Phase 2 — central capability bus

- Define typed activity request/result/evidence schemas.
- Require capability grants and exact subject on dispatch.
- Move one low-risk file/test activity through the bus.
- Make old dispatch paths call the bus; reject direct canonical effects.

Flow:

```text
validate execution state
 -> evaluate policy; error means deny
 -> bind evidence/approval
 -> atomically record request + outbox
 -> execute adapter
 -> validate typed outcome
 -> record result/evidence
 -> reduce next state
[0m
[0m→ [0mRead src/ranex/governed_execution/domain/execution.py
[0m→ [0mRead src/ranex/governed_execution/application/application_control_pep.py
[0m→ [0mRead src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
Now let me read the core source files under audit.
[0m→ [0mRead src/ranex/governed_execution/domain/application_control.py
[0m→ [0mRead src/ranex/governed_execution/adapters/policy/deterministic.py
[0m→ [0mRead src/ranex/governed_execution/domain/events.py
[0m→ [0mRead src/ranex/governed_execution/application/gate_controller.py
[0m→ [0mRead src/ranex/policy/api/contracts.py
[0m→ [0mRead src/ranex/assurance/api/contracts.py
[0m→ [0mRead src/ranex/policy/domain/gates.py
[0m→ [0mRead src/ranex/foundation/identity.py
[0m→ [0mRead src/ranex/foundation/canonical.py
[0m→ [0mRead tests/replay/governed_execution/test_execution_replay.py
[0m→ [0mRead tests/resilience/test_execution_sqlite_crash_boundary.py
[0m✗ [0mGrep "canonical state authority|snapshot.*canonical|journal replay.*canonical|state authority" failed[90m in .[0m
[91m[1mError: [0mRipgrep JSON record exceeded 65536 bytes
[0m
[0m$ [0mrg -n --max-columns 200 "state authority|canonical state" --glob '!uv.lock' -g '!*.min.*' src tests docs 2>/dev/null | rg -i "snapshot|journal|authority" | head -40
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:195:> **Ranex owns control, cross-worker orchestration, authority, canonical state,
docs/architecture/reviews/2026-07-28-live-foundational-reference-corpus-reconciliation.md:226:- Are canonical state and local outbox/journal records atomic under actual
docs/architecture/reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md:69:- deterministic workflow and state authority;
docs/architecture/reviews/artifacts/2026-07-27/hy3-post-reconciliation-review.md:34:   - `compatibility` boundary package correctly has no canonical state authority.
[0m
[0m→ [0mRead tests/security/test_application_control_pep.py
[0m
[0m$ [0mrg -rn "relational snapshot" docs src tests 2>/dev/null; rg -n "not journal replay|journal replay" docs src tests 2>/dev/null | head; ls docs; ls docs/architecture 2>/dev/null
architecture
README.md
research
AI_AGENT_DEVELOPMENT_LIFECYCLE.md
AI_AGENT_FLEET_CONTROL_PLANE.md
AI_ARTIFACT_CONTRACTS.md
assessments
CORE_SDLC_OPERATING_MODEL.md
decisions
ENGINEERING_REFERENCE_APPLICATION_MAP.md
HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
README.md
reviews
rfcs
SDLC_CONTROL_CATALOG.md
SOURCE_OF_TRUTH.md
templates
[0m
[0m✱ [0mGlob "src/ranex/governed_execution/adapters/persistence/sqlite/migrations/*"[90m 1 match[0m
[0m
[0m$ [0mrg -n "canonical state authority" . --hidden -g '!.git' 2>/dev/null; rg -in "journal replay" . --hidden -g '!.git' 2>/dev/null | head -20
./docs/architecture/reviews/artifacts/2026-07-27/hy3-post-reconciliation-review.md:34:   - `compatibility` boundary package correctly has no canonical state authority.
[0m
[0m→ [0mRead src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
[0m→ [0mRead tests/integration/governed_execution/test_sqlite_execution_store.py
[0m→ [0mRead tests/architecture/test_kernel_imports.py
[0m→ [0mRead src/ranex/assurance/domain/gates.py
[0m
[0m$ [0mls architecture/contracts 2>/dev/null; cat architecture/contracts/context-dependency-edges.json 2>/dev/null
accepted-adrs.json
applicability-rules.json
architecture-element-assessments.json
architecture-elements.json
architecture-rule-assessments.json
artifact-types.json
context-boundary-fitness.json
context-coupling-policy.json
context-dependency-edges.json
contexts.json
data-ownership.json
decisions.json
effects.json
engineering-practice-profiles.json
engineering-practices.json
estimate-commitment-control.json
events.json
feedback-fitness.json
generated-output-authority.json
hermes-research-promotions.json
identities.json
legacy-test-direct-source-classifications.json
legacy-test-layout-policy.json
legacy-test-layout-policy-v1.json
legacy-test-layout-policy-v2.json
legacy-test-layout-records.json
legacy-test-layout-records-v1.json
legacy-test-layout-records-v2.json
paths.json
priority-rules.json
readiness-assessments.json
readiness-tiers.json
registry-manifest.json
runtime-adapters.json
schema-registry.json
states.json
tdd-cycle-records.json
tdd-exception-records.json
test-behaviors.json
test-deletion-records.json
test-practice-profiles.json
test-practices.json
test-quarantine-records.json
topology-rules.json
vital-profile.json
worker-role-profiles.json
{
  "actual_cycle_result": "NOT_ASSESSED",
  "actual_import_pairs": [],
  "actual_import_scan_status": "NOT_ASSESSED",
  "actual_subset_result": "NOT_ASSESSED",
  "decision_binding": {
    "decision_id": "ADR-0009",
    "digest": "sha256:16837df0d8647e7abaf0ecf630a52625aeb4d643763e15dd393ba2e53cb21b2b",
    "path": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md",
    "runtime_enactment_status": "NOT_ASSESSED",
    "status": "ACCEPTED_PAPER_DECISION"
  },
  "declared_cycle_result": "PASS",
  "default_policy": "DENY_UNLESS_EXACT_EDGE_REGISTERED",
  "dependency_graph_id": "RANEX-CONTEXT-DEPENDENCIES-1.0",
  "entries": [
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "policy",
      "caller_owner": "policy",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-POLICY-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Resolve authenticated principal/session facts for policy evaluation.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "resource_governance",
      "caller_owner": "resource_governance",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-RESOURCE-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind reservations and usage to an authenticated principal.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "interaction_history",
      "caller_owner": "interaction_history",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-HISTORY-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind thread access and retention decisions to identity facts.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "artifact_management",
      "caller_owner": "artifact_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-ARTIFACT-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Authorize classified artifact access through identity facts.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "product_definition",
      "callee_owner": "product_definition",
      "caller": "work_management",
      "caller_owner": "work_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-WORK-PRODUCT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Trace work to owned requirements, acceptance examples, and outcomes.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "policy",
      "callee_owner": "policy",
      "caller": "work_management",
      "caller_owner": "work_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-WORK-POLICY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Evaluate risk lane and required accountable decisions for work transitions.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "work_management",
      "caller_owner": "work_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-WORK-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind work to exact baselines and trace records.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "product_definition",
      "callee_owner": "product_definition",
      "caller": "service_management",
      "caller_owner": "service_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-SERVICE-PRODUCT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Map operated services to product capabilities and outcome owners.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "provenance_compliance",
      "callee_owner": "provenance_compliance",
      "caller": "supplier_governance",
      "caller_owner": "supplier_governance",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-SUPPLIER-PROVENANCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Use license, provenance, and SBOM policy facts in supplier decisions.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "instruction_registry",
      "caller_owner": "instruction_registry",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-INSTRUCTION-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind active instruction packages to configuration baselines.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "workspace",
      "callee_owner": "workspace",
      "caller": "repository_intelligence",
      "caller_owner": "repository_intelligence",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-REPO-WORKSPACE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Index only an exact repository/worktree/revision identity.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "artifact_management",
      "callee_owner": "artifact_management",
      "caller": "knowledge",
      "caller_owner": "knowledge",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-KNOWLEDGE-ARTIFACT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Store and retrieve classified knowledge payloads by immutable artifact reference.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "instruction_registry",
      "callee_owner": "instruction_registry",
      "caller": "context_compilation",
      "caller_owner": "context_compilation",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-CONTEXT-INSTRUCTION",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Resolve exact applicable instruction records into a packet.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "repository_intelligence",
      "callee_owner": "repository_intelligence",
      "caller": "context_compilation",
      "caller_owner": "context_compilation",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-CONTEXT-REPO",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Resolve exact source graph evidence for packet construction.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "knowledge",
      "callee_owner": "knowledge",
      "caller": "context_compilation",
      "caller_owner": "context_compilation",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-CONTEXT-KNOWLEDGE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Resolve approved knowledge records with provenance.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "context_compilation",
      "caller_owner": "context_compilation",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-CONTEXT-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind the packet to exact configuration and trace baselines.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "supplier_governance",
      "callee_owner": "supplier_governance",
      "caller": "routing",
      "caller_owner": "routing",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-ROUTING-SUPPLIER",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Filter routes by active supplier adoption/support facts.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "resource_governance",
      "callee_owner": "resource_governance",
      "caller": "routing",
      "caller_owner": "routing",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-ROUTING-RESOURCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Respect provider limits and reserved budgets during route choice.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "module_governance",
      "callee_owner": "module_governance",
      "caller": "qualification",
      "caller_owner": "qualification",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-QUAL-MODULE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Qualify an exact module descriptor/version.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "routing",
      "callee_owner": "routing",
      "caller": "qualification",
      "caller_owner": "qualification",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-QUAL-ROUTING",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Qualify an exact provider/model/transport route tuple.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "workspace",
      "callee_owner": "workspace",
      "caller": "qualification",
      "caller_owner": "qualification",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-QUAL-WORKSPACE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind trials to an exact isolated workspace subject.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "qualification",
      "callee_owner": "qualification",
      "caller": "assurance",
      "caller_owner": "assurance",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-ASSURANCE-QUAL",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Accept checker/module/route evidence only from a fresh qualification.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "routing",
      "callee_owner": "routing",
      "caller": "analytical_review",
      "caller_owner": "analytical_review",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-REVIEW-ROUTING",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind review attempts to an exact analytical transport route.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "artifact_management",
      "callee_owner": "artifact_management",
      "caller": "analytical_review",
      "caller_owner": "analytical_review",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-REVIEW-ARTIFACT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Persist immutable review request/response artifacts.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "qualification",
      "callee_owner": "qualification",
      "caller": "effectiveness",
      "caller_owner": "effectiveness",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-EFFECTIVENESS-QUAL",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Compare only qualified modules/routes/graders.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "analytical_review",
      "callee_owner": "analytical_review",
      "caller": "effectiveness",
      "caller_owner": "effectiveness",
      "consistency": "EVENTUAL_OUTBOX",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-EFFECTIVENESS-REVIEW",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "ASYNC_EVENT",
      "rationale": "Use independently recorded review observations in outcome experiments.",
      "recovery": "OUTBOX_REPLAY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "resource_governance",
      "callee_owner": "resource_governance",
      "caller": "agent_collaboration",
      "caller_owner": "agent_collaboration",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-COLLAB-RESOURCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Reserve and settle transitive worker budgets.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "workspace",
      "callee_owner": "workspace",
      "caller": "agent_collaboration",
      "caller_owner": "agent_collaboration",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-COLLAB-WORKSPACE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind assignments and leases to exact workspaces.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "policy",
      "callee_owner": "policy",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-POLICY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Evaluate immutable authorization/risk/decision requirements before transition.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "assurance",
      "callee_owner": "assurance",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-ASSURANCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind fresh exact-subject gate evaluations.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "module_governance",
      "callee_owner": "module_governance",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-MODULE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Resolve active qualified module descriptors and grants.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind subject, principal, destination, and secret-handle facts.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "resource_governance",
      "callee_owner": "resource_governance",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-RESOURCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Reserve and settle run/effect budgets.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "workspace",
      "callee_owner": "workspace",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-WORKSPACE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Validate exact repository/worktree/head before work and effects.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "context_compilation",
      "callee_owner": "context_compilation",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-CONTEXT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Obtain an immutable compiled packet for a run/activity.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "routing",
      "callee_owner": "routing",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-ROUTING",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Lock a qualified route tuple for worker activity.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "agent_collaboration",
      "callee_owner": "agent_collaboration",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-COLLAB",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Dispatch and fence typed worker assignments without transferring run authority.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "artifact_management",
      "callee_owner": "artifact_management",
      "caller": "governed_execution",
      "caller_owner": "governed_execution",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-GE-ARTIFACT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Persist and bind immutable run/effect artifacts by reference.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "delivery",
      "caller_owner": "delivery",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-DELIVERY-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Authenticate channel principals and destinations.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "work_management",
      "callee_owner": "work_management",
      "caller": "delivery",
      "caller_owner": "delivery",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-DELIVERY-WORK",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Submit/query canonical work through channel-neutral commands.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "governed_execution",
      "callee_owner": "governed_execution",
      "caller": "delivery",
      "caller_owner": "delivery",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-DELIVERY-GE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Submit run commands and render immutable run views.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "interaction_history",
      "callee_owner": "interaction_history",
      "caller": "delivery",
      "caller_owner": "delivery",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-DELIVERY-HISTORY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Append classified channel messages and continuity facts.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "governed_execution",
      "callee_owner": "governed_execution",
      "caller": "scheduling",
      "caller_owner": "scheduling",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-SCHEDULE-GE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Submit authenticated scheduled run commands.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "delivery",
      "callee_owner": "delivery",
      "caller": "scheduling",
      "caller_owner": "scheduling",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-SCHEDULE-DELIVERY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Deliver trigger receipts and operator challenges.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "work_management",
      "callee_owner": "work_management",
      "caller": "process_assurance",
      "caller_owner": "process_assurance",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-PROCESS-WORK",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind audits and corrective actions to canonical work.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "assurance",
      "callee_owner": "assurance",
      "caller": "process_assurance",
      "caller_owner": "process_assurance",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-PROCESS-ASSURANCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Use immutable product/gate evidence in process assessments.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "service_management",
      "callee_owner": "service_management",
      "caller": "process_assurance",
      "caller_owner": "process_assurance",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-PROCESS-SERVICE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Relate process findings to service objectives and improvement triggers.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "artifact_management",
      "callee_owner": "artifact_management",
      "caller": "backup_restore",
      "caller_owner": "backup_restore",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-BACKUP-ARTIFACT",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Persist encrypted backup/restore evidence and immutable manifests.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "backup_restore",
      "caller_owner": "backup_restore",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-BACKUP-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind backup and restore drills to exact configuration baselines.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "service_management",
      "callee_owner": "service_management",
      "caller": "operations",
      "caller_owner": "operations",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-OPERATIONS-SERVICE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Evaluate health/incidents against owned service objectives.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "backup_restore",
      "callee_owner": "backup_restore",
      "caller": "operations",
      "caller_owner": "operations",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-OPERATIONS-BACKUP",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Initiate and observe idempotent recovery commands.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "process_assurance",
      "callee_owner": "process_assurance",
      "caller": "operations",
      "caller_owner": "operations",
      "consistency": "EVENTUAL_OUTBOX",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-OPERATIONS-PROCESS",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "ASYNC_EVENT",
      "rationale": "Create process evidence/corrective-action inputs from incidents.",
      "recovery": "OUTBOX_REPLAY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "release_management",
      "caller_owner": "release_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-RELEASE-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Build only an exact accepted configuration baseline.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "provenance_compliance",
      "callee_owner": "provenance_compliance",
      "caller": "release_management",
      "caller_owner": "release_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-RELEASE-PROVENANCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Require license/provenance/SBOM compliance before packaging.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "supplier_governance",
      "callee_owner": "supplier_governance",
      "caller": "release_management",
      "caller_owner": "release_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-RELEASE-SUPPLIER",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Require supported and approved dependency facts.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "service_management",
      "callee_owner": "service_management",
      "caller": "release_management",
      "caller_owner": "release_management",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-RELEASE-SERVICE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Bind release/support/rollback records to an owned service.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "workspace",
      "callee_owner": "workspace",
      "caller": "upstream_sync",
      "caller_owner": "upstream_sync",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-UPSTREAM-WORKSPACE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Operate only in a dedicated exact sync worktree.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "upstream_sync",
      "caller_owner": "upstream_sync",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-UPSTREAM-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Record observed/audited/incorporated upstream baselines.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "provenance_compliance",
      "callee_owner": "provenance_compliance",
      "caller": "upstream_sync",
      "caller_owner": "upstream_sync",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-UPSTREAM-PROVENANCE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Classify license/provenance impact before accepting a port set.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "configuration_management",
      "callee_owner": "configuration_management",
      "caller": "migration",
      "caller_owner": "migration",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-MIGRATION-CONFIG",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Apply only a versioned ordered migration manifest.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "backup_restore",
      "callee_owner": "backup_restore",
      "caller": "migration",
      "caller_owner": "migration",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-MIGRATION-BACKUP",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Require and verify a recovery point around migration.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "identity_access",
      "callee_owner": "identity_access",
      "caller": "extension_host",
      "caller_owner": "extension_host",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-EXTENSION-IDENTITY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Authenticate extension principals and sessions.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "policy",
      "callee_owner": "policy",
      "caller": "extension_host",
      "caller_owner": "extension_host",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-EXTENSION-POLICY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Evaluate grants and requested capabilities fail closed.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "module_governance",
      "callee_owner": "module_governance",
      "caller": "extension_host",
      "caller_owner": "extension_host",
      "consistency": "READ_ONLY_SNAPSHOT",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-EXTENSION-MODULE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_QUERY",
      "rationale": "Map extension capabilities to registered host contracts.",
      "recovery": "REFRESH_REEVALUATE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "governed_execution",
      "callee_owner": "governed_execution",
      "caller": "compatibility",
      "caller_owner": "compatibility",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-COMPAT-GE",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Submit translated legacy requests without receiving authority.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "delivery",
      "callee_owner": "delivery",
      "caller": "compatibility",
      "caller_owner": "compatibility",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-COMPAT-DELIVERY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Translate legacy CLI/channel requests through canonical delivery commands.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    },
    {
      "callee": "interaction_history",
      "callee_owner": "interaction_history",
      "caller": "compatibility",
      "caller_owner": "compatibility",
      "consistency": "CALLEE_TRANSACTION_ONLY",
      "definition_status": "DEFINED",
      "edge_id": "EDGE-COMPAT-HISTORY",
      "failure": "FAIL_CLOSED_REQUIRED",
      "interaction": "SYNC_COMMAND",
      "rationale": "Import legacy session history through the owned public API.",
      "recovery": "IDEMPOTENT_RETRY_RECONCILE",
      "runtime_validation_status": "NOT_ASSESSED",
      "schema_version": "context-dependency-edge/v1",
      "source": "docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
    }
  ],
  "expected_edge_count": 67,
  "generated_by": "scripts/architecture/generate_contracts.py",
  "record_schema_path": "schemas/common/context-dependency-edge-v1.schema.json",
  "registry_id": "REG-CONTEXT-DEPENDENCY-EDGES-001",
  "runtime_validation_status": "NOT_ASSESSED",
  "status": "ACTIVE_DOCUMENTATION_CONTRACT",
  "version": "1.0.0"
}
[0m
[0m→ [0mRead tests/migration/governed_execution/test_execution_store_migration.py
[0m→ [0mRead src/ranex/governed_execution/application/ports/execution_repository.py
[0m→ [0mRead src/ranex/governed_execution/application/ports/application_control_policy.py
[0m
[0m$ [0muv run pytest -q 2>&1 | tail -15
........................................................................ [100%]
72 passed in 0.20s
[0m
[0m→ [0mRead src/ranex/governed_execution/domain/status.py
[0m→ [0mRead tests/unit/governed_execution/domain/test_execution.py
[0m→ [0mRead tests/unit/governed_execution/domain/test_application_control.py
[0m→ [0mRead tests/unit/governed_execution/application/test_gate_controller.py
[0m→ [0mRead src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py
[0m→ [0mRead src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py
[0m→ [0mRead src/ranex/work_management/domain/transitions.py
[0m→ [0mRead src/ranex/assurance/adapters/filesystem/artifact_verifier.py
[0m
[0m$ [0mgrep -n "Phase 1\|Exit:" docs/research/hermes-core-architecture-research-2026-07-27.md | sed -n '1,12p'; awk 'NR>=1899 && NR<=1912 {printf "%d: %s\n", NR, $0}' docs/research/hermes-core-architecture-research-2026-07-27.md
1871:**Exit:** one canonical contract registry and no undeclared aliases.
1894:**Exit:** a clean host can run a qualified non-Nous model route with token/cost
1899:### Phase 1 — create the clean kernel beside Hermes
1911:**Exit:** reducer replay and crash-boundary tests pass with no Hermes import.
1933:**Exit:** a bypass fixture cannot cause an effect.
1956:**Exit:** both conditions pass:
1983:**Exit:** one authorized run completes; every denial is typed and replayable.
1993:**Exit:** each context owns its schema/migrations and can be tested in
2004:**Exit:** the owner approves a measured Ranex distribution profile.
1899: ### Phase 1 — create the clean kernel beside Hermes
1900: 
1901: - Implement shared identity and canonical serialization.
1902: - Implement an `Execution` aggregate and pure reducer.
1903: - Implement canonical relational execution state/version plus an append-only
1904:   transition/audit journal and outbox in one SQLite unit of work. Event-source
1905:   only the execution aggregate if its replay/migration tests justify that
1906:   choice; do not event-source every module.
1907: - Implement a fail-closed application-control PEP with pure domain decisions
1908:   and a simple deterministic policy adapter.
1909: - Add architecture import tests before feature code.
1910: 
1911: **Exit:** reducer replay and crash-boundary tests pass with no Hermes import.
1912:
[0m
[0m$ [0mcat pyproject.toml; ls tests/unit/foundation/domain tests/contract/policy tests/integration/assurance 2>/dev/null; find tests src -name conftest.py -o -name "__init__.py" | head; find tests -name "*.py" | wc -l
[project]
name = "ranex-kernel-tracer"
version = "0.0.0"
description = "Non-authoritative R&D tracer for the proposed Ranex kernel"
requires-python = ">=3.11,<3.15"
dependencies = [
    "PyYAML>=6.0.2,<7",
]

[dependency-groups]
dev = [
    "pytest>=9.0.2,<10",
    "ruff>=0.15.10,<0.16",
]

[tool.uv]
package = false

[tool.pytest.ini_options]
addopts = [
    "--strict-config",
    "--strict-markers",
]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]
tests/contract/policy:
__pycache__
test_gate_policy_loader.py

tests/integration/assurance:
__pycache__
test_evidence_artifact_verifier.py
test_hash_chain_ledger.py

tests/unit/foundation/domain:
__pycache__
test_canonical.py
test_identity.py
src/ranex/work_management/api/__init__.py
src/ranex/work_management/domain/__init__.py
src/ranex/work_management/__init__.py
src/ranex/governed_execution/application/ports/__init__.py
src/ranex/governed_execution/application/__init__.py
src/ranex/governed_execution/domain/__init__.py
src/ranex/governed_execution/adapters/policy/__init__.py
src/ranex/governed_execution/adapters/__init__.py
src/ranex/governed_execution/adapters/persistence/sqlite/__init__.py
src/ranex/governed_execution/adapters/persistence/__init__.py
15
[0m
[0m$ [0mrg -n "ConcurrentExecutionWriteError|count_outbox|count_journal|replay_execution" src tests
tests/replay/governed_execution/test_execution_replay.py:12:    replay_execution,
tests/replay/governed_execution/test_execution_replay.py:62:    replayed = replay_execution(events)
tests/resilience/test_execution_sqlite_crash_boundary.py:77:    assert store.count_journal_entries(RUN_ID) == 1
tests/resilience/test_execution_sqlite_crash_boundary.py:78:    assert store.count_outbox_entries(RUN_ID) == 1
tests/integration/governed_execution/test_sqlite_execution_store.py:170:    assert store.count_journal_entries(RUN_ID) == 2
tests/integration/governed_execution/test_sqlite_execution_store.py:171:    assert store.count_outbox_entries(RUN_ID) == 2
tests/integration/governed_execution/test_sqlite_execution_store.py:249:    assert store.count_journal_entries(RUN_ID) == 2
tests/integration/governed_execution/test_sqlite_execution_store.py:250:    assert store.count_outbox_entries(RUN_ID) == 2
src/ranex/governed_execution/domain/execution.py:226:def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:54:class ConcurrentExecutionWriteError(RuntimeError):
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:289:                    raise ConcurrentExecutionWriteError(
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:366:    def count_journal_entries(self, execution_id: Identity) -> int:
src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:369:    def count_outbox_entries(self, execution_id: Identity) -> int:
[0m
[0m$ [0mfind src -name "__init__.py" -size +0c -exec wc -c {} +; echo ---; grep -rn "ExecutionUnblocked" tests/unit/governed_execution/domain/test_execution.py | head -3; grep -n "target_status" src/ranex/governed_execution/domain/execution.py
40 src/ranex/work_management/api/__init__.py
  41 src/ranex/work_management/domain/__init__.py
  65 src/ranex/work_management/__init__.py
  41 src/ranex/governed_execution/application/ports/__init__.py
  52 src/ranex/governed_execution/application/__init__.py
  44 src/ranex/governed_execution/domain/__init__.py
  46 src/ranex/governed_execution/adapters/policy/__init__.py
  53 src/ranex/governed_execution/adapters/__init__.py
  60 src/ranex/governed_execution/adapters/persistence/sqlite/__init__.py
  58 src/ranex/governed_execution/adapters/persistence/__init__.py
  74 src/ranex/governed_execution/__init__.py
  62 src/ranex/foundation/__init__.py
  34 src/ranex/assurance/api/__init__.py
  49 src/ranex/assurance/domain/__init__.py
  44 src/ranex/assurance/adapters/filesystem/__init__.py
  44 src/ranex/assurance/adapters/__init__.py
  40 src/ranex/assurance/adapters/persistence/jsonl/__init__.py
  38 src/ranex/assurance/adapters/persistence/__init__.py
  68 src/ranex/assurance/__init__.py
  31 src/ranex/policy/api/__init__.py
  32 src/ranex/policy/domain/__init__.py
  42 src/ranex/policy/adapters/configuration/yaml/__init__.py
  37 src/ranex/policy/adapters/configuration/__init__.py
  41 src/ranex/policy/adapters/__init__.py
  60 src/ranex/policy/__init__.py
 103 src/ranex/__init__.py
1299 total
---
17:    ExecutionUnblocked,
125:        ExecutionUnblocked(
74:    target_status: ExecutionStatus,
78:    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
82:        status=target_status,
184:            or current.blocked_from_status is not event.target_status
187:        return _advance(current, event, event.target_status)
[0m
# Adversarial Audit Report — kernel R&D tracer (`feature/kernel-tracer`)

Test suite executed read-only: `uv run pytest` → 72 passed in 0.20s.

---

## Findings

### F1 — BLOCKER — The declared state-authority inference is declared nowhere in the tree
**Claim:** The inference quoted by the session record — *"the relational snapshot, not journal replay, is canonical state authority"* — appears nowhere in `src/`, `tests/`, or the docs corpus; the code enacts it silently, which under the audit's own rule ("an unreported inference is a defect") is a finding.
**Evidence:** Exhaustive search for `"canonical state authority"`, `"relational snapshot"`, `"journal replay"` across the worktree returns one unrelated hit (`docs/architecture/reviews/artifacts/2026-07-27/hy3-post-reconciliation-review.md:34`, about the `compatibility` package). The inference is only *enacted*: `src/ranex/governed_execution/application/ports/execution_repository.py:12` ("Load the current canonical execution snapshot") and `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:210-221` (`load()` reads only `execution_state`, never `execution_journal`).
**Counter-argument:** ADR-0013 `HERMES-PROMOTION-060` (`docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:690-699`, "persists canonical execution state and its associated version in relational storage") combined with `HERMES-OWNER-DECISION-020` (`ADR-0013:979-990`, event sourcing registered but **not** activated, `absence_outcome: BLOCK`) jointly *entail* snapshot authority. **Counter fails:** entailment is not declaration; the specific "not journal replay" claim binds a load-time behavior (never reconstruct from journal) that no provision, docstring, or ADR sentence states, and OWNER-DECISION-020 being unresolved means the journal's evidentiary status is formally *undecided*, not "non-canonical."

### F2 — MAJOR — Journal and snapshot can silently disagree; no code path verifies their agreement
**Claim:** A self-consistent forged `execution_state` row is accepted as authority while the journal contradicts it, because integrity checks are intra-row only and journal hash-chain continuity is enforced nowhere.
**Evidence:**
- `load()` reads only the snapshot: `execution_store.py:210-221`.
- `_decode_state_row` checks only row-internal consistency (canonical form, version/last_event_id/execution_id columns vs the JSON document): `execution_store.py:398-419`. A forger who rewrites `canonical_state_json`, `version`, and `last_event_id` *together* passes all checks.
- Journal chain continuity (`previous_state_sha256` of row N vs `resulting_state_sha256` of row N−1) is checked by no Python code and no SQL constraint: `migrations/001_execution_kernel.sql:11-33` checks only `resulting_version = previous_version + 1` and digest *lengths*; `UNIQUE (execution_id, resulting_version)` does not require the new `previous_version` to equal the current chain head, so a forged snapshot at version 99 yields a journal gap 2→100 that nothing detects.
- The only journal readers in `src/` are row counters: `execution_store.py:366-382`. No reconciliation, no replay-from-journal (there is an event *encoder* `_event_to_document` at `execution_store.py:128-180` but no decoder anywhere).
- The tamper tests only cover *internally inconsistent* forgeries: `tests/integration/governed_execution/test_sqlite_execution_store.py:174-189` (version-column-only edit) and `:192-227` (JSON-only edit).
**Counter-argument:** An attacker with direct SQLite write access can also `DROP TRIGGER` the append-only guards (`001_execution_kernel.sql:47-69`), so DB-file tampering is arguably outside the threat model of a local R&D tracer. **Counter partially fails:** the store *chose* to implement and test tamper detection (`ExecutionPersistenceIntegrityError`, `execution_store.py:50-51, 398-419`), so the integrity model it advertises is real scope, and it detects only the naive half of forgeries; and disagreement need not be adversarial — any future bug writing `execution_state` outside `append()` is likewise invisible.

### F3 — MAJOR — The application-control PEP binds the policy verdict to the request by `request_id` alone; a buggy adapter reaches allow without a matching grant
**Claim:** `ApplicationControlPEP.decide` never cross-checks the evaluation's `gate_id`, action, `policy_digest`, `catalog_digest`, or `evidence_digest` against the request/evidence it forwarded, so a defective adapter (e.g., one returning a cached or mis-keyed `GateEvaluation` that is a genuine PASS for the same `request_id` but computed from different evidence or a different gate) produces `permitted=True` without an explicit grant for this subject.
**Evidence:** The only binding check is `application_control_pep.py:48` (`request_bound=evaluation.request_id == request.request_id`). The facts consumed at `:45-52` are `well_formed / request_bound / gate_passed / gate_authorized / reason_codes` — nothing else. `GateEvaluation` carries `gate_id`, `policy_digest`, `evidence_digest` (`src/ranex/assurance/domain/gates.py:80-91`) and the PEP holds the very evidence tuple it passed (`application_control_pep.py:35-38`), so it could recompute the evidence digest exactly as `gate_controller.py:73-77` does — it does not. `ApplicationControlRequest` does not bind `request_id` to `action` (`application_control.py:14-40`), so one `request_id` reused across two actions is accepted for both.
**Counter-argument:** The adapter is a constructor-injected trust root at the composition root (`application_control_pep.py:25-26`; consistent with `HERMES-PROMOTION-015`, ADR-0013:240-249), and a *malicious* adapter can fabricate a fully self-consistent PASS anyway (`GateEvaluation.__post_init__` at `gates.py:97-102` is satisfiable with arbitrary digests), so cross-checks cannot stop malice. **Counter partially fails:** cross-checks are not for malice but for bugs — the enumerated "ambiguous decision" defect class — and `HERMES-PROMOTION-063` (ADR-0013:720-729) demands the PEP itself be fail-closed, not fail-closed-modulo-adapter-correctness.

### F4 — MAJOR — The replay test is near-tautological and cannot evidence the Phase 1 exit criterion
**Claim:** `test_replay_reproduces_identical_final_state_and_version` compares `replay_execution(events)` against a manual fold of `reduce_execution` over the same in-memory events — but `replay_execution` *is* that fold — so the equality assertion compares the production reducer with itself and cannot detect nondeterminism, serialization drift, or journal/replay divergence.
**Evidence:** Assertions at `tests/replay/governed_execution/test_execution_replay.py:59-66`; `replay_execution` is a loop over `reduce_execution` at `src/ranex/governed_execution/domain/execution.py:226-237`. The test covers only the happy path PROPOSED→READY→RUNNING→SUCCEEDED (`:26-57`); no BLOCKED/WAITING/FAILED branch, no replay from persisted `execution_journal` rows (impossible today — no event decoder exists, F2), no serialization round-trip, and no "commands" comparison though `HERMES-PROMOTION-032` (ADR-0013:410-419) requires "same state and commands." `HERMES-PROMOTION-062` (ADR-0013:710-719) conditions event sourcing on replay/migration tests that "justify that choice"; an identity comparison justifies nothing.
**Counter-argument:** `HERMES-PROMOTION-065` (ADR-0013:740-749) literally requires only that "reducer replay tests … pass," and full-dataclass equality (`frozen` eq covers all nine fields, `execution.py:52-62`) is not a subset check; the second fold also proves inputs are not mutated. **Counter fails:** reading 065 so that a self-comparison satisfies it is exactly the "weakening a provision so the code passes" defect the audit charter forbids; the exit gate's purpose (research line `docs/research/hermes-core-architecture-research-2026-07-27.md:1911`) is qualification evidence, which this cannot provide.

### F5 — MAJOR — The crash-boundary test exercises a handled statement error, not a crash
**Claim:** The test simulates "crash" via a SQLite trigger `RAISE(ABORT)` whose cleanup is performed by the store's own graceful `except`-handler `ROLLBACK` — the code path a real crash would *never run* — and exercises exactly one failure point; SQLite's actual crash recovery (rollback-journal replay on next open after process death) is never tested.
**Evidence:** Trigger install at `tests/resilience/test_execution_sqlite_crash_boundary.py:50-59` (`BEFORE INSERT ON execution_outbox`); the "crash" surfaces as an exception caught and rolled back by application code at `execution_store.py:359-362`; post-conditions asserted at `test_execution_sqlite_crash_boundary.py:72-78` and `:80-98`. No crash point between `BEGIN IMMEDIATE` (`execution_store.py:225`) and the state UPDATE, none between state UPDATE (`:267-287`) and journal INSERT (`:301-328`), none during `COMMIT` (`:357`); no process kill, no fsync/torn-write scenario despite `PRAGMA synchronous = FULL` (`:197`) existing precisely for that case.
**Counter-argument:** Because all writes share one transaction, SQLite's ACID contract makes every intra-transaction crash point equivalent, and statement-abort + rollback verifies the same invariant ("no partial state") more cheaply. **Counter partially fails:** that equivalence is itself an untested assumption about SQLite journal-mode configuration (no `PRAGMA journal_mode` is ever set, `execution_store.py:189-198`), and the whole point of the Phase 1 exit gate ("crash-boundary tests pass," research line 1911; `HERMES-PROMOTION-065`) is to *demonstrate*, not assume, recovery. The test name over-claims relative to what its assertions establish.

### F6 — MINOR — The reducer's aggregate is freely constructible in illegal states, and the persistence loader accepts invariant-violating snapshots
**Claim:** `Execution` has no `__post_init__` validation, so state is reachable without the reducer (`Execution(status=SUCCEEDED, version=0, ...)`, or `dataclasses.replace` into any shape), and `_execution_from_document` reconstructs `Execution` without checking cross-field invariants — e.g., `blocked_from_status` set while `status != BLOCKED`, or a non-timestamp `updated_at`.
**Evidence:** `execution.py:52-62` (no validation, contrast with every event's `__post_init__`, `events.py:39-56` ff.); `execution_store.py:83-125` validates identities, enum values, and version positivity but not the `status`/`blocked_from_status` coupling nor `updated_at` format (`_require_string` only, `:123`), though events enforce canonical UTC (`events.py:20-29`).
**Counter-argument:** Python cannot seal constructors; `HERMES-PROMOTION-059` (ADR-0013:680-689) requires state *evolution* through the pure reducer, and the only persistence write path does route every transition through `reduce_execution` (`execution_store.py:238`). **Counter mostly wins for in-memory fabrication, fails for the loader:** the loader is a trust boundary that already validates aggressively; the missing invariants are an inconsistency in its own model, and a forged `blocked_from_status` changes which `ExecutionUnblocked` the reducer will subsequently accept (`execution.py:181-187`) — i.e., it steers future legal transitions.

### F7 — MINOR — `reduce_execution` rejects only reuse of the *immediately preceding* event identity
**Claim:** The single-step reducer's duplicate guard (`event.event_id == current.last_event_id`) accepts an event that reuses any *earlier* event's identity if its `expected_version` matches the current version.
**Evidence:** `execution.py:132-133`.
**Counter-argument:** Full-history duplicate detection is impossible in a pure single-step reducer without carrying the whole ID set in state; `replay_execution` rejects duplicates across the entire history (`execution.py:230-233`) and the journal enforces `event_id UNIQUE` (`001_execution_kernel.sql:13`). **Counter largely wins** (defense-in-depth exists at both outer layers), but the residual in-memory gap and the undocumented weakness of the reducer-level check keep this as MINOR rather than dissolved.

### F8 — MINOR — The fencing (CAS) failure path is dead code under the store's own locking and is asserted by no test
**Claim:** `ConcurrentExecutionWriteError` is raised only if the row changes between SELECT and UPDATE *inside* a `BEGIN IMMEDIATE` transaction — which the write lock prevents — and no test ever asserts it; the concurrency test accepts *any* exception, and the "stale event rolls back" test fails in the reducer before any write occurs, so no write rollback is exercised there.
**Evidence:** CAS raise at `execution_store.py:288-291`; `rg` confirms zero test references. `tests/integration/governed_execution/test_sqlite_execution_store.py:247` asserts only `isinstance(result, Exception)`; `:161-171` expects `ValueError, match="expected version"`, which is `InvalidExecutionTransition` raised at `execution.py:128-131` during `reduce_execution` — before the UPDATE/INSERTs at `execution_store.py:243-356`.
**Counter-argument:** `BEGIN IMMEDIATE` (`:225`) makes the CAS genuine defense-in-depth, and unreachable code that only *denies* cannot fail open. **Counter partially wins**; retained as MINOR because the test names ("one cas winner", "rolls back") claim verification of mechanisms the assertions do not reach.

### F9 — MINOR — GateController resolves PASS+UNKNOWN (and PASS+NOT_APPLICABLE) co-evidence permissively
**Claim:** A claim backed by one verified PASS plus an exact-subject record with outcome `UNKNOWN` or `NOT_APPLICABLE` still authorizes; only `FAIL`, `CONFLICT`, and `CHECKER_FAULT` veto, so ambiguity is treated inconsistently (CHECKER_FAULT vetoes, UNKNOWN does not).
**Evidence:** conflict set limited to `CONFLICT` or `PASS∧FAIL` at `gate_controller.py:159-161`; the "failed" test at `:177-181` checks only `FAIL or exit_code != 0`; satisfaction via non-empty `passing` at `:183-184`; PASS emitted at `:222`.
**Counter-argument:** An UNKNOWN record asserts absence of knowledge by *that* producer, not contradiction of the verified PASS; blocking on it would let any party veto by emitting UNKNOWN. **Counter is strong** but does not explain why `CHECKER_FAULT` (also non-contradictory) vetoes while UNKNOWN does not; the asymmetry is undocumented. MINOR.

### F10 — MINOR — SQLite database is world-readable for a window at creation
**Claim:** `initialize()` lets `sqlite3.connect`/`executescript` create the file under the process umask and applies `chmod(0o600)` only afterwards.
**Evidence:** `execution_store.py:200-208` (chmod at `:208`, after migration and close).
**Counter-argument:** Local single-user R&D tracer; contrast `hash_chain_ledger.py:145-146` which sets `touch(mode=0o600)` *before* writing — showing the codebase knows the correct pattern, which is why this stays a finding rather than dissolving.

### F11 — MINOR — The audit journal records no independent time; `recorded_at`/`created_at` are the caller's `occurred_at`
**Claim:** `execution_journal.recorded_at` and `execution_outbox.created_at` store the event's self-declared `occurred_at`, so a forged timestamp fully controls audit chronology and the column names misrepresent their content.
**Evidence:** `execution_store.py:326` and `:354` both bind `event.occurred_at`.
**Counter-argument:** Injecting wall-clock time in the adapter would not violate reducer purity (the adapter is outside the domain), so determinism provisions (`HERMES-PROMOTION-031`, ADR-0013:400-409) do not excuse it — the counter-argument actually *fails*; retained as MINOR only because the tracer claims no authority.

### F12 — MINOR — `catalog_digest` is an unverified attestation stamped into every gate evaluation
**Claim:** `DeterministicPolicyAdapter` accepts any well-formed sha256 string as `catalog_digest` without verifying it corresponds to the supplied catalog; the tests pass `"sha256:" + "d"*64` (a digest of nothing), and that value flows into every `GateEvaluation`.
**Evidence:** pattern-only check at `deterministic.py:27-28`; test fabrications at `tests/security/test_application_control_pep.py:126` and `:141`; contrast `gate_controller.py:74` which honestly *computes* `policy_digest` from the gate.
**Counter-argument:** The digest is provenance over the source *bytes* (`gate_catalog_loader.py:171-174`), unrecomputable from the parsed object; binding is the composition root's job. **Counter partially wins**; MINOR stands because nothing in the tree ever performs that binding and the security tests normalize fake digests.

### F13 — MINOR — Misattributed denial reason when the *evidence iterable* fails
**Claim:** `tuple(evidence)` executes inside the PEP's try-block, so an evidence iterable that raises is denied as `POLICY_ADAPTER_EXCEPTION`, corrupting the audit meaning of the reason code (fail-closed, but wrong attribution).
**Evidence:** `application_control_pep.py:34-40` (materialization at `:37`, catch at `:39`, reason at `:40`).
**Counter-argument:** Any deny is acceptable for fail-closed purposes. True for authorization; false for a system whose reason codes are audit artifacts (`deny_application_control` enforces non-empty reasons precisely because they carry meaning, `application_control.py:58-62`).

### F14 — MINOR — Migration test is structural only; the event-sourcing "justification" gate is vacuously satisfied
**Claim:** The sole migration test asserts table names and `PRAGMA user_version` — no data migration, upcasting, or schema-evolution scenario — while `HERMES-PROMOTION-062` conditions Execution event sourcing on "replay and migration tests justify that choice."
**Evidence:** `tests/migration/governed_execution/test_execution_store_migration.py:33-38`; provision at ADR-0013:710-719.
**Counter-argument:** Schema v1 has nothing to migrate from, and OWNER-DECISION-020 keeps event sourcing *inactive*, so no justification is yet owed. **Counter mostly wins**; retained MINOR because the journal already persists full event documents (`execution_store.py:301-328`) — i.e., event-sourcing-shaped data exists whose future migration is the very thing 062 wants qualified.

### F15 — MINOR — Domain-purity static tests are evadable by trivial aliasing
**Claim:** The forbidden-call detector matches literal dotted names (`time.time`, `datetime.now`, …), so `import time as t; t.time()` or `n = datetime.now; n()` in a domain module passes the architecture gate.
**Evidence:** name-literal matching at `tests/architecture/test_kernel_imports.py:36-52` and `:130-139`, `:306-320`. (Module-level import bans at `:231-249` do catch `import time as t`; the call check adds nothing for aliased *attribute* access like `from datetime import datetime` + local alias.)
**Counter-argument:** The import ban catches the dominant vector, `HERMES-PROMOTION-064` requires the tests exist and pass (they do), and no current domain file evades anything (verified: `execution.py`, `events.py`, `status.py`, `application_control.py`, `gates.py`, `transitions.py` are clean). Counter is strong; MINOR as a guard-strength note.

---

## Dissolved

### D1 — PEP catches `Exception`, not `BaseException`
Claim was that `KeyboardInterrupt`/`SystemExit` escape the deny path (`application_control_pep.py:39`). **Dissolved:** a propagating `BaseException` never reaches an allow outcome — the caller receives no decision at all — and swallowing `KeyboardInterrupt` into a deny would be worse practice. Fail-closed is preserved on every path.

### D2 — "Relational" state is actually a JSON document column, arguably violating `HERMES-PROMOTION-060`
Snapshot state is one `canonical_state_json TEXT` column (`001_execution_kernel.sql:5`) with only version/last_event_id/updated_at promoted to columns. **Dissolved:** the provision (ADR-0013:690-699) requires "canonical execution state and its associated version in relational storage," not normalization; the version is an explicit, CHECK-constrained relational column (`001:6`) cross-verified on load (`execution_store.py:408-411`). Insisting on column-per-field would be the reinterpretation defect in the other direction.

### D3 — Outbox lacks dispatch/consumption tracking
`execution_outbox` has no `dispatched_at`/consumer state (`001_execution_kernel.sql:35-45`). **Dissolved:** Phase 1 (research lines 1903-1904; `HERMES-PROMOTION-061`, ADR-0013:700-709) requires only that the outbox be persisted with state and journal in one SQLite unit of work — which `append()` does (`execution_store.py:225-357`); dispatch belongs to Phase 2 (research line ~1930, "atomically record request + outbox").

### D4 — Concurrent create race
Two simultaneous `ExecutionCreated` appends: second INSERT hits the `execution_id` PRIMARY KEY (`001:4`) inside `BEGIN IMMEDIATE` and raises → rollback → deny. **Dissolved:** fail-closed; no partial state possible (`execution_store.py:242-260, 359-362`).

### D5 — Replay equality checked on a subset of state
Suspected per audit brief. **Dissolved:** `Execution` is a frozen dataclass; `replayed == direct` (`test_execution_replay.py:64`) compares all nine fields including `blocked_from_status`, `last_event_id`, `updated_at`. The test's defect is tautology (F4), not subsetting.

### D6 — Hidden nondeterminism inside the reducer
Attack attempted: wall-clock, randomness, I/O, env, set/dict iteration order affecting output, input mutation, partial state on exception. **Dissolved with evidence:** `execution.py:1-20` imports only `dataclasses`, `collections.abc`, and sibling domain modules; timestamps come exclusively from `event.occurred_at` (`:85, :121`); new state is built by `replace()` on frozen inputs (`:80-87`) so exceptions can leave no partial state; `frozenset`s are used for membership only (`:78, :95`), never iterated into output; `replay_execution`'s `set` (`:229-233`) affects only rejection, not results. The architecture test independently bans effectful imports/calls in domain (`test_kernel_imports.py:18-52`). The reducer's purity holds; the exploitable surface is around it (F6, F7), not in it.

---

## Inferences

Every conclusion below is not literally stated in code or docs; evidence that prompted each is cited.

1. **Inference:** The quoted state-authority sentence originates from a session record outside this worktree; it is absent from the audited tree. Evidence: negative search results (F1); no session record file exists under the worktree (`git status` shows only `.gitignore`, `pyproject.toml`, `src/`, `tests/`, `uv.lock`).
2. **Inference:** Under `BEGIN IMMEDIATE`, the losing thread in `test_concurrent_same_version_transitions_have_one_cas_winner` fails with `InvalidExecutionTransition` (stale `expected_version` after re-SELECT), not `ConcurrentExecutionWriteError`. Evidence: lock acquisition at `execution_store.py:225` precedes the SELECT at `:227-234`; the loser blocks until commit, then reads the *new* state; the test's weak `isinstance(result, Exception)` assertion (`test_sqlite_execution_store.py:247`) cannot distinguish. Not verified by execution (verification would require writing a scratch script/DB, barred by the read-only constraint beyond the existing suite).
3. **Inference:** A `RAISE(ABORT)` trigger aborts the statement and surfaces as a Python exception; whole-transaction cleanup in the crash test is therefore performed by `execution_store.py:359-362`, not by SQLite crash recovery. Evidence: SQLite ABORT semantics + the store's explicit `ROLLBACK` handler; the test passes without any process restart (`test_execution_sqlite_crash_boundary.py:61-78`).
4. **Inference:** `replay_execution` vs. manual fold is a self-comparison. Evidence: `execution.py:234` calls `reduce_execution` per event — the identical function the test folds manually (`test_execution_replay.py:59-62`).
5. **Inference:** The policy adapter is inside the trust boundary by design (composition-root injection). Evidence: `application_control_pep.py:25-26`; `HERMES-PROMOTION-015` (ADR-0013:240-249). Used to weigh F3's severity.
6. **Inference:** ADR-0013 provisions 058-065 legitimately bind this untracked code despite `catalog_status: DEFINITION_ONLY` (ADR-0013:93) and `IMPLEMENTATION_START_READY` being undeclared — because the audit charter instructs it and ADR-0013:65-68 declares Phase 1 "a binding clean-kernel inventory."
7. **Inference:** No composition root exists in this tree; nothing constructs `SQLiteExecutionStore` + `ApplicationControlPEP` + `DeterministicPolicyAdapter` together outside tests. Evidence: all `__init__.py` files are ≤103 bytes (docstrings/empty; verified by size scan), and no `main`/wiring module appears in the `src/` file inventory. Consequence: several fail-closed properties (e.g., F3, F12 digest binding) are currently *only* exercised under test-controlled wiring.
8. **Inference:** The journal's full event documents (`execution_store.py:301-328`) constitute latent event-sourcing data whose replay/migration qualification (062) is owed *before* OWNER-DECISION-020 could ever be resolved; used in F14.
9. **Inference:** The absence of `PRAGMA journal_mode` means default rollback-journal (DELETE) mode; crash-recovery behavior therefore depends on an unpinned SQLite default. Evidence: `execution_store.py:189-198` sets only `foreign_keys` and `synchronous`.
10. **Inference:** `LEGAL_STATUS_TRANSITIONS` exhaustiveness test (`test_execution.py:206-232`) is a change-detector (it restates the constant literally), providing review friction but zero semantic verification. Evidence: byte-for-byte duplication of `execution.py:27-49`.

---

## Coverage

**Source examined in full (all lines):**
- `src/ranex/governed_execution/domain/execution.py` (1-237), `events.py` (1-197), `status.py` (1-23), `application_control.py` (1-77)
- `src/ranex/governed_execution/application/application_control_pep.py` (1-53), `gate_controller.py` (1-222), `ports/execution_repository.py` (1-17), `ports/application_control_policy.py` (1-19)
- `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py` (1-420), `migrations/001_execution_kernel.sql` (1-73), `adapters/policy/deterministic.py` (1-47)
- `src/ranex/foundation/identity.py` (1-53), `canonical.py` (1-26)
- `src/ranex/policy/domain/gates.py` (1-101), `policy/api/contracts.py` (1-15), `policy/adapters/configuration/yaml/gate_catalog_loader.py` (1-174)
- `src/ranex/assurance/domain/gates.py` (1-114), `assurance/api/contracts.py` (1-7), `assurance/adapters/filesystem/artifact_verifier.py` (1-128), `assurance/adapters/persistence/jsonl/hash_chain_ledger.py` (1-208)
- `src/ranex/work_management/domain/transitions.py` (1-74)
- All 26 `__init__.py` files size-checked for import side effects (≤103 bytes each; none flagged).

**Tests examined in full:** `tests/replay/governed_execution/test_execution_replay.py` (1-66), `tests/resilience/test_execution_sqlite_crash_boundary.py` (1-98), `tests/security/test_application_control_pep.py` (1-158), `tests/integration/governed_execution/test_sqlite_execution_store.py` (1-250), `tests/migration/governed_execution/test_execution_store_migration.py` (1-38), `tests/architecture/test_kernel_imports.py` (1-483), `tests/unit/governed_execution/domain/test_execution.py` (1-318), `test_application_control.py` (1-64), `tests/unit/governed_execution/application/test_gate_controller.py` (1-132). Present but not line-audited beyond enumeration: `tests/unit/foundation/domain/test_canonical.py`, `test_identity.py`, `tests/unit/work_management/domain/test_transitions.py`, `tests/contract/policy/test_gate_policy_loader.py`, `tests/integration/assurance/test_evidence_artifact_verifier.py`, `test_hash_chain_ledger.py` (outside the four named attack surfaces).

**Docs/contracts examined:** `ADR-0013` lines 1-1009 (full provision catalog 001-065, owner decisions 001-020, research-only rows through 003); research doc lines 1880-1930 (Phase 0Z exit, Phase 1 full text 1899-1912, Phase 2 head); `architecture/contracts/context-dependency-edges.json` (full — confirmed `governed_execution→policy` EDGE-GE-POLICY and `governed_execution→assurance` EDGE-GE-ASSURANCE are registered, so the kernel's cross-context imports are edge-covered); `pyproject.toml` (full). Corpus-wide regex sweeps for the state-authority declaration (F1).

**PEP path enumeration (surface 2, decision-line map):** missing/None policy → `AttributeError` → deny `application_control_pep.py:39-40` (closed); adapter exception → `:39-40` (closed); malformed non-`GateEvaluation` result → `:42-43` (closed); unknown action / missing gate / wrong project → `ValueError` from `gates.py:91-100` → `:39-40` (closed); ambiguous outcomes UNKNOWN/CONFLICT/CHECKER_FAULT/NOT_APPLICABLE → `gate_passed=False` → deny `application_control.py:73-74` (closed); PASS-with-reasons → deny `:75-76` (closed, unreachable via valid `GateEvaluation` per `gates.py:99-100`); the **only** allow is `application_control.py:77`, reachable solely with a well-formed authorized PASS bound by `request_id` — whose insufficiency as a binding is F3.

**Executed:** `uv run pytest` (72 passed). No files created, modified, or deleted; no write commands run (test-created artifacts confined to pytest `tmp_path`).
