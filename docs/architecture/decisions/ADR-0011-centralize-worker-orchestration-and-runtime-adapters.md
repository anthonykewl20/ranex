# ADR-0011: Centralize Worker Orchestration and Use Role-Scoped Official Runtime Adapters

| Field | Value |
|---|---|
| ADR ID | `ADR-0011` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-29 |
| Effective revision | Working tree based on `4baad4a758f70d39af6a21e73488c61db5f82f32`; executable projection and runtime evidence pending |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `governed_execution`, `agent_collaboration`, `routing`, `module_governance`, `resource_governance`, `qualification`, `workspace`, `identity_access`, `policy`, `assurance`, `process_assurance`, `compatibility`, and `provenance_compliance` |
| RFC | Not required; records the human owner's explicit worker-control, de-commercialization, and performance decision after primary-source reconciliation |
| Supersedes | ADR-0005 model/provider-routing fallback, worker-topology coordinator, and model-controlled orchestration clauses; strengthens `DEC-RANEX-017`, `DEC-RANEX-025`, `DEC-RANEX-026`, and `DEC-RANEX-027` without renumbering them |
| Review/expiry date | On any worker role, tool surface, runtime adapter, provider/auth route, session-reuse, or orchestration-boundary change |
| Compatibility/migration class | Strangler replacement of Hermes-agent inference/orchestration and terminal-skill dispatch; no dual authority |
| Security/data class | Public architecture decision; credentials, prompts, source, sessions, and runtime evidence retain their own classification |

## Decision

Ranex control services are the sole orchestrator, dispatcher, scheduler,
coordinator, fan-out owner, and join owner. Every model, coding harness, review
harness, and provider runtime is a leaf worker behind a Ranex-owned typed
adapter. A leaf worker:

- receives one immutable assignment, role profile, effective tool grant,
  workspace, route lock, budget, lease, and fencing epoch;
- may produce structured events, artifacts, evidence, and proposals;
- cannot create assignments, spawn or delegate to another model worker,
  coordinate a fleet, choose a successor, widen its role or tools, switch its
  model/route, approve its own output, or land a change; and
- returns control to Ranex at completion, cancellation, timeout, failure, or an
  explicit checkpoint.

“Sole orchestrator” means sole **cross-worker and control-plane orchestrator**.
An official harness may execute its bounded in-role model/tool loop inside one
assignment. That local loop cannot create another worker/assignment, expose a
new tool, widen an effect/path/network grant, change route/model, or survive its
lease.

Ranex compiles a deterministic, bounded fan-out/join graph before dispatch.
Model-generated decomposition is an untrusted proposal. Only the Ranex
scheduler can validate it, reserve capacity, create child assignments, and
record their dependencies. A provider's built-in subagent, team, delegation,
advisor, fallback, or auxiliary-model facility is disabled for a worker
assignment.

Each registered role owns an immutable **maximum** tool/capability envelope.
Each assignment compiles the exact task-minimal effective subset of that
ceiling. Empty is the default. A role ceiling is not a grant; a prompt,
provider allow-list, prior session, ambient user configuration, or worker
request cannot broaden the effective set. Every attempted tool call is
observed; every effectful call crosses policy and `CapabilityBus`; the OS
sandbox, workspace/path guard, network policy, and process-tree limit remain
independent enforcement layers.

Every assignment binds exactly one explicit provider, model, transport, runtime
adapter/version, auth subject/mode, and route lock. Adapter fallback, provider
fallback, model fallback, and auxiliary model calls are disabled. Failure is a
typed result returned to Ranex. Only Ranex may create a new assignment with a
new explicit route after policy, qualification, budget, and owner constraints
are re-evaluated.

## Runtime boundary

The hot path is:

```text
Ranex governed_execution + agent_collaboration
  -> typed WorkerRuntime port
  -> Ranex-owned release-pinned runtime adapter
  -> official provider runtime and structured protocol
  -> one leaf worker
  -> structured events/result back to Ranex
```

The target does not put a Hermes `AIAgent`, Nous model, Markdown skill,
model-authored shell command, PTY, terminal scraper, or `tmux` keystroke loop
between the Ranex scheduler and a worker. Shell/PTY/tmux may appear only in
diagnostic or compatibility evidence outside the qualified product hot path;
they cannot be an active runtime adapter.

The initial official-runtime boundaries are:

1. **Claude:** a Ranex adapter owns the official Claude Agent SDK
   `ClaudeSDKClient`, which owns the Claude runtime subprocess and structured
   stream. The adapter owns route/session binding, event normalization,
   capability callbacks, cancellation, checkpoint/resume policy, usage
   settlement, and lifecycle. `allowed_tools` is only an auto-approval rule,
   not a tool-surface restriction. The effective surface is enforced using the
   actual `tools` set, its deny complement in `disallowed_tools`, deterministic
   `PreToolUse`/SDK-custom-tool gateways, `strict_mcp_config`, isolated
   assignment configuration/home and working directory, no setting/skill/
   plugin/auto-memory sources, the Ranex sandbox, and `CapabilityBus`.
   `can_use_tool` is an ask-path fallback, not universal mediation: calls
   already resolved by permission mode or allow rules may not reach it. The
   strict route uses `dontAsk`, never the model-classified `auto` mode. The
   adapter supplies no `agents` definitions and removes `Agent` (including the
   older `Task` alias), `Workflow`, `SendMessage`, `ToolSearch`,
   `Cron`/`RemoteTrigger`, `EnterWorktree`, and background-capable surfaces
   unless a narrower accepted role explicitly requires a nondelegating
   equivalent. Any nested `parent_tool_use_id` is a containment violation.
   If `Bash` is granted, shell startup files, environment, network, filesystem,
   process tree, and project working directory are independently isolated.
   Ranex uses the SDK's lifecycle rather than reimplementing private subprocess
   PIDs: interrupt, drain correlated events to a deadline, call SDK disconnect
   (whose pinned implementation must prove its bounded close/terminate/kill
   behavior), then verify cleanup through the outer supervisor/container.
2. **Codex:** a Ranex adapter owns the official Codex SDK or stable Codex
   app-server JSON-RPC/JSONL stdio boundary. It binds one thread/turn to the
   assignment, streams typed notifications, handles approvals through Ranex
   policy, interrupts through the official protocol, disables experimental
   APIs unless separately qualified, and denies ambient apps, plugins, MCP
   servers, skills, dynamic tools, nested agents, and ungranted shell/process
   paths.

Another provider or harness may be added only by an accepted catalog revision
and qualification evidence proving the same leaf-only, exact-route,
task-minimal-tool, structured-event, cancellation, fencing, and no-fallback
contract. A local OpenCode session used for advisory architecture review is not
thereby a qualified Ranex product runtime adapter.

## Session and performance policy

Ranex may maintain a bounded set of connected runtime clients to avoid
avoidable startup and discovery work. Reuse is legal only for the same exact
assignment and logical session under the complete reuse key in the catalog.
There is no generic cross-task or cross-project conversation pool. A connected
client is terminated rather than reassigned when any key component changes or
clean-state semantics are unproven.

Preconnect is permitted only after the assignment, lease, route, auth, role,
tool, sandbox, configuration, and workspace affinity key exists. One-shot SDK
calls may still create a new process/session. Therefore “SDK” or “preconnected”
alone is not evidence of warm execution. Qualification compares cold one-shot,
cold managed-client, and same-session connected-client paths and records time to
first structured event, time to first model content, total latency, process
spawn count, provider/model call count, tool-call amplification, CPU, peak
memory, cancellation latency, and result correctness. No threshold is invented
before measurement. Warm reuse ships only after an owner-accepted threshold
shows a latency benefit that exceeds its memory/isolation cost without context
leakage.

## Authentication, entitlement, and distribution

Authentication is an explicit route fact, not inferred from an installed CLI or
friendly account label.

- A local user may select an official personal subscription-backed runtime only
  when current vendor terms permit that exact use and the adapter verifies the
  effective auth path before dispatch.
- An environment API key may take precedence over subscription authentication;
  the effective route must therefore be observed and bound, not guessed.
- A distributed Ranex product uses customer-owned API credentials or another
  vendor-approved commercial integration. It does not offer a vendor consumer
  login or route a user's personal-plan credentials on their behalf without
  explicit vendor approval.
- Credentials remain opaque handles and cannot be copied from a provider
  credential file into a Ranex-native HTTP impersonation path.

The route lock separates (a) configured auth intent, (b) adapter-observed
effective auth source and account/tenant subject, and (c) vendor-internal facts
the adapter cannot observe. An unobservable vendor fact is `UNKNOWN`, never
filled from an account label. Environment precedence is sanitized before
startup and attested from the initialized runtime.

For Claude specifically, Ranex does not use Hermes' native Anthropic adapter
with Claude Code OAuth identity headers, system-prefix imitation, or credential
file extraction. It uses the official Agent SDK/runtime boundary for an
eligible local subscription route and an official API/BYOK route for a
distributed product unless Anthropic grants different written approval.

## Hermes and Nous disposition

Hermes remains only:

- attributed upstream provenance;
- a frozen compatibility and characterization source during strangler
  migration;
- a reference for behavior worth reimplementing through Ranex-owned ports; and
- a quarantined legacy process when a separately accepted migration slice still
  requires it.

Ranex has no live Hermes/Nous inference route, parent-agent model loop, Nous
Portal/model service, Hermes model catalog, Hermes/Nous credential or
entitlement path, billing, credits, subscription sale, purchase path, managed
tool pool, promotional path, or hidden fallback. Compatibility cannot invoke a
model or dispatch another worker. Any retained legacy process returns only
characterization/translation results under a no-network, no-provider,
no-credential profile.

## Canonical machine catalog

The following strict fenced YAML block is the sole semantic source for
`architecture/contracts/worker-role-profiles.json` and
`architecture/contracts/runtime-adapters.json`. The compiler must reject
unknown fields, duplicate IDs, a role grant outside its ceiling, an adapter
that permits delegation/fallback/auxiliary calls, an incomplete reuse key, or a
projection mismatch. The catalog is **definition-only**. `DEFINED_NOT_QUALIFIED`
does not claim implementation, activation, runtime enforcement, performance, or
vendor entitlement.

```yaml
schema_version: "worker-runtime-catalog/v1"
catalog_id: "RANEX-WORKER-RUNTIME-CATALOG"
catalog_version: "1.0.0"
catalog_status: "DEFINITION_ONLY"
governing_adr: "ADR-0011"
fixed_decision_count: 29
assignment_defaults:
  effective_tool_ids: []
  effective_capability_ids: []
  leaf_worker: true
  worker_spawn: "DENIED"
  worker_delegation: "DENIED"
  worker_coordination: "DENIED"
  adapter_fallback: "DISABLED"
  provider_fallback: "DISABLED"
  model_fallback: "DISABLED"
  auxiliary_model_calls: "DISABLED"
  nested_worker_lineage: "DENIED"
  in_role_tool_loop: "BOUNDED_ALLOWED_WITHIN_EFFECTIVE_GRANT"
  ambient_user_settings: false
  ambient_project_settings: false
  ambient_local_settings: false
  ambient_mcp_servers: false
  ambient_plugins: false
  ambient_skills: false
  effect_path: "POLICY_THEN_CAPABILITY_BUS"
  task_narrowing_required: true
role_profiles:
  - role_profile_id: "ROLEPROFILE-RESEARCH-READONLY-001"
    version: "1.0.0"
    lifecycle: "DEFINED_NOT_QUALIFIED"
    role_class: "RESEARCH_WORKER"
    maximum_tool_ids:
      - "TOOL-ARTIFACT-SUBMIT"
      - "TOOL-REPOSITORY-SEARCH"
      - "TOOL-WEB-FETCH"
      - "TOOL-WORKSPACE-READ"
    maximum_capability_ids:
      - "CAP-ARTIFACT-SUBMIT"
      - "CAP-NETWORK-READ-DECLARED-DESTINATIONS"
      - "CAP-WORKSPACE-READ"
    permanently_denied_capability_ids:
      - "CAP-AUXILIARY-MODEL-CALL"
      - "CAP-CANONICAL-AUTHORITY-WRITE"
      - "CAP-CREDENTIAL-EXPORT"
      - "CAP-LANDING"
      - "CAP-ROUTE-MUTATE"
      - "CAP-WORKER-COORDINATE"
      - "CAP-WORKER-DELEGATE"
      - "CAP-WORKER-SPAWN"
    write_policy: "ARTIFACT_SUBMISSION_ONLY"
    network_policy: "ASSIGNMENT_DESTINATION_ALLOWLIST"
    assignment_must_compile_strict_subset: true
  - role_profile_id: "ROLEPROFILE-IMPLEMENTATION-WORKER-001"
    version: "1.0.0"
    lifecycle: "DEFINED_NOT_QUALIFIED"
    role_class: "IMPLEMENTATION_WORKER"
    maximum_tool_ids:
      - "TOOL-ARTIFACT-SUBMIT"
      - "TOOL-GIT-READ"
      - "TOOL-PATCH-APPLY"
      - "TOOL-PROCESS-EXEC-BOUNDED"
      - "TOOL-REPOSITORY-SEARCH"
      - "TOOL-WORKSPACE-EDIT"
      - "TOOL-WORKSPACE-READ"
    maximum_capability_ids:
      - "CAP-ARTIFACT-SUBMIT"
      - "CAP-PROCESS-EXEC-BOUNDED"
      - "CAP-WORKSPACE-READ"
      - "CAP-WORKSPACE-WRITE-DECLARED-PATHS"
    permanently_denied_capability_ids:
      - "CAP-AUXILIARY-MODEL-CALL"
      - "CAP-CANONICAL-AUTHORITY-WRITE"
      - "CAP-CREDENTIAL-EXPORT"
      - "CAP-LANDING"
      - "CAP-ROUTE-MUTATE"
      - "CAP-WORKER-COORDINATE"
      - "CAP-WORKER-DELEGATE"
      - "CAP-WORKER-SPAWN"
    write_policy: "ISOLATED_WORKTREE_DECLARED_PATHS_ONLY"
    network_policy: "DENY_UNLESS_ASSIGNMENT_EXPLICIT"
    assignment_must_compile_strict_subset: true
  - role_profile_id: "ROLEPROFILE-INDEPENDENT-REVIEWER-001"
    version: "1.0.0"
    lifecycle: "DEFINED_NOT_QUALIFIED"
    role_class: "INDEPENDENT_REVIEWER"
    maximum_tool_ids:
      - "TOOL-ARTIFACT-SUBMIT"
      - "TOOL-GIT-READ"
      - "TOOL-PROCESS-EXEC-BOUNDED"
      - "TOOL-REPOSITORY-SEARCH"
      - "TOOL-WORKSPACE-READ"
    maximum_capability_ids:
      - "CAP-ARTIFACT-SUBMIT"
      - "CAP-PROCESS-EXEC-BOUNDED"
      - "CAP-WORKSPACE-READ"
    permanently_denied_capability_ids:
      - "CAP-AUXILIARY-MODEL-CALL"
      - "CAP-CANONICAL-AUTHORITY-WRITE"
      - "CAP-CREDENTIAL-EXPORT"
      - "CAP-LANDING"
      - "CAP-ROUTE-MUTATE"
      - "CAP-WORKER-COORDINATE"
      - "CAP-WORKER-DELEGATE"
      - "CAP-WORKER-SPAWN"
    write_policy: "ARTIFACT_SUBMISSION_ONLY"
    network_policy: "DENY_UNLESS_ASSIGNMENT_EXPLICIT"
    assignment_must_compile_strict_subset: true
runtime_adapters:
  - runtime_adapter_id: "RUNTIME-CLAUDE-AGENT-SDK-001"
    version: "1.0.0"
    lifecycle: "DEFINED_NOT_QUALIFIED"
    provider_family: "ANTHROPIC"
    official_runtime: "CLAUDE_AGENT_SDK_CLAUDE_SDK_CLIENT"
    protocol: "SDK_MANAGED_CLAUDE_SUBPROCESS_STRUCTURED_STDIO"
    official_source: "https://code.claude.com/docs/en/agent-sdk/overview"
    exact_model_required: true
    exact_full_model_id_required: true
    leaf_worker_only: true
    worker_spawn: "DENIED"
    worker_delegation: "DENIED"
    adapter_fallback: "DISABLED"
    provider_fallback: "DISABLED"
    model_fallback: "DISABLED"
    auxiliary_model_calls: "DISABLED"
    ambient_configuration: "DISABLED"
    tool_surface_enforcement:
      - "TOOLS_EXACT_EFFECTIVE_SET"
      - "DISALLOWED_TOOLS_COMPLEMENT"
      - "PERMISSION_MODE_DONT_ASK_NEVER_AUTO"
      - "PRE_TOOL_USE_OR_SDK_CUSTOM_TOOL_GATEWAY_FOR_EVERY_ATTEMPT"
      - "CAN_USE_TOOL_ASK_PATH_FALLBACK_ONLY"
      - "NO_AGENT_DEFINITIONS_OR_AGENT_TEAM_DELEGATION_TOOLS"
      - "STRICT_MCP_CONFIG"
      - "SETTING_SOURCES_EMPTY"
      - "AUTO_MEMORY_DISABLED"
      - "EMPTY_SKILLS_AND_PLUGINS"
      - "PER_ASSIGNMENT_CONFIG_HOME_AND_CWD"
      - "BACKGROUND_EXECUTION_DISABLED"
      - "RANEX_SANDBOX_AND_PATH_GUARD"
    forbidden_runtime_tool_names:
      - "Agent"
      - "Task"
      - "Workflow"
      - "SendMessage"
      - "ToolSearch"
      - "Cron"
      - "RemoteTrigger"
      - "EnterWorktree"
    allowed_tools_semantics: "AUTO_APPROVAL_ONLY_NOT_RESTRICTION"
    startup_attestation:
      - "ACTUAL_TOOL_SURFACE_EQUALS_EFFECTIVE_TOOL_GRANT"
      - "AMBIENT_SOURCE_SET_EMPTY"
      - "PINNED_SDK_AND_RUNTIME_DIGESTS_MATCH"
      - "EFFECTIVE_AUTH_AND_ROUTE_MATCH_ROUTE_LOCK"
      - "INIT_MODEL_CWD_MCP_PERMISSION_AGENTS_SKILLS_PLUGINS_AND_API_KEY_SOURCE_MATCH"
    structured_events: true
    event_correlation: "ASSIGNMENT_ATTEMPT_LEASE_EPOCH_SESSION_REQUEST_AND_TOOL_IDS"
    nested_parent_tool_use_id: "CONTAINMENT_VIOLATION"
    cancellation: "INTERRUPT_THEN_DRAIN_TO_DEADLINE_THEN_SDK_DISCONNECT_THEN_OUTER_SUPERVISOR_CLEANUP_VERIFICATION"
    resume: "EXACT_RECORDED_SESSION_ID_ONLY"
    preconnect: "ONLY_AFTER_COMPLETE_ASSIGNMENT_LEASE_AFFINITY_KEY_EXISTS"
    auth_policy:
      local_individual_subscription: "OFFICIAL_SUBSCRIPTION_WHEN_TERMS_AND_EFFECTIVE_AUTH_ALLOW"
      product_api_or_cloud: "API_BYOK_SUPPORTED_CLOUD_OR_WRITTEN_VENDOR_APPROVAL"
      environment_precedence: "SANITIZE_AND_ATTEST_BEFORE_DISPATCH"
      credential_file_extraction: "DENIED"
    warm_reuse:
      scope: "SAME_ASSIGNMENT_AND_LOGICAL_SESSION_ONLY"
      cross_assignment: false
      cross_project: false
      key_fields:
        - "runtime_adapter_id"
        - "runtime_adapter_version"
        - "route_lock_digest"
        - "effective_auth_subject_digest"
        - "role_profile_digest"
        - "effective_tool_grant_digest"
        - "sandbox_profile_digest"
        - "workspace_id"
        - "assignment_id"
        - "session_id"
  - runtime_adapter_id: "RUNTIME-CODEX-APP-SERVER-001"
    version: "1.0.0"
    lifecycle: "DEFINED_NOT_QUALIFIED"
    provider_family: "OPENAI"
    official_runtime: "CODEX_SDK_OR_STABLE_CODEX_APP_SERVER"
    protocol: "JSON_RPC_JSONL_STDIO"
    official_source: "https://learn.chatgpt.com/docs/app-server.md"
    exact_model_required: true
    exact_full_model_id_required: true
    leaf_worker_only: true
    worker_spawn: "DENIED"
    worker_delegation: "DENIED"
    adapter_fallback: "DISABLED"
    provider_fallback: "DISABLED"
    model_fallback: "DISABLED"
    auxiliary_model_calls: "DISABLED"
    ambient_configuration: "DISABLED"
    tool_surface_enforcement:
      - "STABLE_API_ONLY"
      - "NO_DYNAMIC_TOOLS"
      - "NO_NESTED_AGENT_OR_DELEGATION_SURFACE"
      - "NO_AMBIENT_APPS_PLUGINS_MCP_OR_SKILLS"
      - "NO_BACKGROUND_EXECUTION_SURFACE"
      - "DENY_UNGRANTED_SERVER_APPROVAL_REQUESTS"
      - "RANEX_CAPABILITY_CALLBACK"
      - "RANEX_SANDBOX_AND_PATH_GUARD"
    allowed_tools_semantics: "RANEX_EFFECTIVE_SET_IS_AUTHORITATIVE"
    startup_attestation:
      - "ACTUAL_TOOL_SURFACE_EQUALS_EFFECTIVE_TOOL_GRANT"
      - "AMBIENT_SOURCE_SET_EMPTY"
      - "PINNED_SDK_AND_RUNTIME_DIGESTS_MATCH"
      - "EFFECTIVE_AUTH_AND_ROUTE_MATCH_ROUTE_LOCK"
      - "INIT_MODEL_CWD_MCP_PERMISSION_AND_EXTENSION_FACTS_MATCH"
    structured_events: true
    event_correlation: "ASSIGNMENT_ATTEMPT_LEASE_EPOCH_THREAD_TURN_REQUEST_AND_ITEM_IDS"
    nested_parent_tool_use_id: "CONTAINMENT_VIOLATION"
    cancellation: "TURN_INTERRUPT_THEN_DRAIN_TO_DEADLINE_THEN_SDK_OR_APP_SERVER_DISCONNECT_THEN_OUTER_SUPERVISOR_CLEANUP_VERIFICATION"
    resume: "EXACT_RECORDED_THREAD_ID_ONLY"
    preconnect: "ONLY_AFTER_COMPLETE_ASSIGNMENT_LEASE_AFFINITY_KEY_EXISTS"
    auth_policy:
      local_individual_subscription: "OFFICIAL_USER_AUTH_WHEN_TERMS_AND_EFFECTIVE_AUTH_ALLOW"
      product_api_or_cloud: "API_BYOK_SUPPORTED_CLOUD_OR_WRITTEN_VENDOR_APPROVAL"
      environment_precedence: "SANITIZE_AND_ATTEST_BEFORE_DISPATCH"
      credential_file_extraction: "DENIED"
    warm_reuse:
      scope: "SAME_ASSIGNMENT_AND_LOGICAL_SESSION_ONLY"
      cross_assignment: false
      cross_project: false
      key_fields:
        - "runtime_adapter_id"
        - "runtime_adapter_version"
        - "route_lock_digest"
        - "effective_auth_subject_digest"
        - "role_profile_digest"
        - "effective_tool_grant_digest"
        - "sandbox_profile_digest"
        - "workspace_id"
        - "assignment_id"
        - "session_id"
```

`assignment_must_compile_strict_subset: true` means the effective set must be a
proper subset of the role ceiling. If a task genuinely requires the whole
ceiling, the role profile is too coarse and must be split or a narrower
versioned profile accepted before dispatch. This prevents a maximum profile
from becoming a routine grant.

## Stable fixed-decision inventory

The fixed register remains exactly 29 IDs. ADR-0011 does not create a separate
thirtieth product dimension; it supersedes incomplete selections already
represented by `DEC-RANEX-017` (fleet), `025` (providers/runtime), `026`
(Nous/Hermes de-commercialization), and `027` (catalog/route activation). IDs
remain stable for evidence, migration, and historical replay. ADR-0006 points
those four rows to this ADR and adds the fitness obligations below. Expanding
or renumbering the register would create duplicate meanings and invalidate
existing exact-subject references.

## Noncompensating fitness functions

| ID | Required result |
|---|---|
| `FF-FLEET-LEAF-001` | Provider/harness workers receive no agent definitions or Agent/team/delegation/scheduler tools; they cannot create assignments, spawn/delegate/coordinate workers, call a nested model, alter topology, or bypass deterministic Ranex fan-out/join; any nested provider lineage is detected and denied. |
| `FF-ROLE-TOOLS-001` | For every assignment, the effective tool/capability sets are exact proper subsets of the immutable role ceiling; empty defaults, startup-attested actual tool-surface removal, deterministic pre-tool/custom-tool mediation, no ambient settings/MCP/plugins/skills/auto-memory, isolated config/cwd, sandbox denial, and `CapabilityBus` effects all pass positive and negative tests. |
| `FF-RUNTIME-001` | Each active adapter uses its release-pinned official typed runtime/protocol, startup-attests model/cwd/tool/MCP/permission/extension/auth facts, emits correlated structured identity/events/usage, supports interrupt, terminal-event drain, SDK disconnect plus outer-supervisor cleanup verification and exact recorded resume, and contains no skill-authored shell, PTY, terminal scraping, or tmux hot path. |
| `FF-NO-FALLBACK-001` | Model/provider/adapter fallback, auxiliary model calls, provider subagents, and route mutation are absent in configuration and remain denied under outage, overload, malformed output, cancellation, and adversarial tool requests. |
| `FF-SESSION-001` | A connected runtime is reused only when every reuse-key field matches the same assignment/session; cross-assignment/project reuse, stale auth/profile/tool/workspace reuse, and unproven reset are denied and leak tests pass. |
| `FF-DISPATCH-PERF-001` | Equal-subject cold and warm benchmarks record first-event/content latency, total latency, process/model/tool amplification, CPU, peak memory, cancellation, correctness, and isolation; no latency claim or warm default ships without accepted thresholds and exact evidence. |
| `FF-AUTH-ROUTE-001` | Effective auth/provider/model identity is observed before dispatch; local subscription use and distributed-product credentials satisfy current vendor terms; credential extraction/impersonation and unauthorized consumer-login brokering are denied. |
| `FF-DECOMM-001` | Static, package, runtime, credential, network, and SBOM evidence proves no Hermes/Nous inference, Portal, credential/entitlement, monetization, managed-tool, purchase, or fallback route. |

Each result is assessed independently for the exact adapter version, runtime
binary/package digest, host, auth mode, route, model, role profile, effective
tool grant, sandbox, workspace, and assignment class. A pass elsewhere cannot
compensate for a failed, stale, `UNKNOWN`, or `CONFLICT` row. All results begin
`NOT_ASSESSED`.

## Alternatives considered

1. **Keep Hermes as the parent model and ask it to call worker CLIs.** Rejected
   because it adds an unneeded inference/tool-decision layer, permits hidden
   orchestration, and makes route/tool/session control prompt-dependent.
2. **Wrap `claude -p` or interactive `tmux` commands directly.** Rejected as the
   target hot path because the official Agent SDK exposes structured lifecycle,
   session, interrupt, callback, and tool controls without shell quoting or
   terminal scraping.
3. **Allow workers to spawn specialist subagents within a parent budget.**
   Rejected because transitive charging does not restore Ranex's lost control
   over role separation, exact tools, route identity, topology, evidence, or
   cancellation.
4. **Use one generic full-tool role and rely on prompts.** Rejected because a
   maximum permission set is not task-minimal enforcement and prompt text is
   not an authorization boundary.
5. **Pool stateful clients across unrelated work for lower latency.** Rejected
   because conversation, settings, tools, auth, and workspace state can leak;
   measured same-assignment/session reuse captures the safe optimization.
6. **Reuse Claude Code OAuth credentials in a native HTTP adapter.** Rejected
   because it bypasses the official harness boundary, creates identity/header
   emulation and vendor-policy fragility, and is unnecessary for the selected
   SDK route.

## Consequences, migration, and rollback

Implementation removes Hermes/Nous live routes and introduces the
`WorkerRuntime` port, catalog projections, Claude and Codex adapters,
role-to-assignment grant compiler, event normalizer, bounded runtime manager,
and bypass/performance tests. Existing Hermes behavior is characterized before
removal, but no compatibility phase grants it orchestration or live inference.

The safe rollback is to the last qualified Ranex adapter/profile/version or to
deny dispatch. It is never rollback to Hermes/Nous inference, a terminal skill,
hidden fallback, broad tools, or cross-task session reuse. Adapter failure
preserves evidence and returns a typed failure to Ranex for an explicit new
owner-controlled routing decision.

## Evidence standing and remaining unknowns

The supporting
[2026-07-29 reconciliation](../reviews/2026-07-29-claude-runtime-hermes-opencode-reconciliation.md)
separates current official facts, pinned Hermes source facts, reviewer
observations, inferences, and unknowns. Primary sources establish the available
interfaces and the defects in the broad original claim; they do not establish
Ranex performance, isolation, entitlement, or implementation correctness.

Still unknown until measured or obtained from the vendor are:

- exact cold/warm latency and memory on the selected Ranex host and workload;
- whether every provider/runtime can remove its entire ungranted native tool
  surface without a second containment layer;
- long-term stability of current subscription-backed Agent SDK policy;
- any vendor approval for consumer-plan authentication in a distributed Ranex
  product; and
- the qualification status of future OpenCode, DeepSeek, HY3, or direct-provider
  runtime adapters.

The human owner accepts the boundary and construction direction. This ADR does
not claim that the catalog is generated, adapters exist, workers are contained,
vendor entitlement is available, or the performance target has passed.
