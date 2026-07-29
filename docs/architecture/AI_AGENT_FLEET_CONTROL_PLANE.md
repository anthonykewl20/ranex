# Ranex AI-Worker Fleet Control-Plane Specification

| Field | Value |
|---|---|
| Specification ID | `SPEC-AI-FLEET-001` |
| Version | `1.2.0` |
| Status | `ACCEPTED` normative supporting target |
| Runtime maturity | `NOT_VALIDATED` until the selected adoption gates pass |
| Scope | Complete control-plane map for multiple AI workers used to develop, verify, operate, or extend Ranex |
| Owner | Human governor |
| Effective date | 2026-07-29 |
| Repository snapshot basis | `bootstrap/pre-upstream`; exact revision and content digest are supplied by review/release manifests |
| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Parent architecture | [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Worker lifecycle | [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md) |
| Contract policy | [AI-Work Artifact Contract Specification](./AI_ARTIFACT_CONTRACTS.md) |
| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md); [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md); [ADR-0011](./decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md) |
| Research addendum | [Kimi Agent-Fleet Research Reconciliation](./reviews/2026-07-27-kimi-agent-fleet-research-reconciliation.md) |
| Runtime reconciliation | [Claude Runtime, Hermes, and OpenCode HY3 Reconciliation](./reviews/2026-07-29-claude-runtime-hermes-opencode-reconciliation.md) |
| Security/data class | Public specification metadata; packets, prompts, workspaces, secrets, and evidence retain their own classification |
| Review trigger | Authority/state change, new topology, fleet-size increase, harness or model-route change, material verifier drift, or failed fleet adoption gate |

> **This is a worker-control specification, not an AI-native software-
> development method.**
>
> The established Core SDLC decides what work exists, which state it is in,
> what evidence is required, and which human role owns each decision. This
> document only defines how one or more probabilistic workers may safely execute
> bounded assignments inside that process.

## 1. Purpose

Ranex needs a stable way to employ changing models, harnesses, and parallel
workers without turning model behavior into project governance. A fleet is
therefore treated as a constrained distributed execution subsystem:

- work is admitted by the Core SDLC;
- exact assignments are compiled from accepted work and policy;
- Ranex control services alone schedule, dispatch, fan out, and join workers;
- workers claim time-bounded leases rather than owning tasks;
- every model/harness is a leaf at the cross-worker boundary;
- a role defines a maximum envelope and each assignment receives an exact
  task-minimal proper subset;
- each assignment binds one explicit model/runtime/auth route with no
  adapter/provider/model fallback or auxiliary model call;
- every model and tool action is governed, metered, and attributable;
- mutable writes are isolated and landing is serialized;
- results are immutable proposals and evidence;
- qualified verification constrains usable concurrency; and
- humans retain the decision rights assigned by the Core SDLC.

Prompt instructions remain useful configuration. They are not concurrency
control, access control, authorization, durable state, or proof.

A leaf official harness may run the bounded in-role model/tool loop needed to
complete its one assignment. “Leaf” means it cannot create or coordinate
workers, widen tools/effects, or mutate route/topology; it does not prohibit
the assigned tool loop itself.

## 2. Scope and non-scope

This specification covers two deployments of the same control concepts:

| Deployment | Meaning | Present maturity |
|---|---|---|
| `DEVELOPMENT_FLEET` | External agents and harnesses used to change the Ranex repository | Process/templates and host controls until Ranex can self-govern |
| `PRODUCT_WORKER_FLEET` | Analytical, coding, review, tool, and delivery workers invoked by the Ranex product | Target architecture; implementation and runtime proof pending |

The same identity, packet, lease, budget, evidence, and separation rules apply
to both. The current development environment must not be described as enforcing
controls that exist only in the target.

This document does not:

- replace discovery, requirements, architecture, planning, configuration
  management, V&V, release, operation, maintenance, or retirement;
- create a second `WorkItemStatus` or `RunStatus`;
- authorize an agent to approve, waive, merge, release, or close work;
- authorize a worker, provider subagent/team, or model-native scheduler to
  create/delegate/coordinate assignments;
- allow a generic full-tool role, hidden fallback, auxiliary model call,
  ambient configuration, or generic cross-task conversation pool;
- require a multi-agent topology when one worker is safer or more effective;
- prescribe an agent count from vendor or benchmark claims;
- make token throughput, commits, or agent utilization a success measure;
- expose hidden verification material to a worker; or
- create a desktop control application.

## 3. Authority hierarchy

```text
authenticated human decisions and accepted ADRs
                         |
                         v
              Core SDLC + control catalog
              WorkItem, risk, roles, gates
                         |
                         v
             exact TaskPacket / ReviewRequest
                         |
                         v
      Ranex scheduler: role ceiling -> exact minimal grant
      + one runtime/model/auth route + assignment graph
                         |
                         v
        agent_collaboration assignment + fenced lease
                         |
                         v
           governed_execution Run + governor
                         |
             +-----------+-----------+
             |                       |
             v                       v
 official typed leaf worker       CapabilityBus
 bounded in-role loop        policy eligibility
                                  -> governed permit/effect
             |
             v
      assurance + qualified verification
             |
             v
       accountable human/transition service
```

An `AgentAssignment` may schedule worker effort. It cannot transition the
`WorkItem`, issue a `Permit`, or commit a `Run` transition. A `Run` may record
execution truth. It cannot declare product acceptance. A human decision can
accept risk or direction but cannot manufacture missing empirical evidence.
Only Ranex services create an `AgentAssignment`; a worker has no command,
tool, or provider-native surface for doing so.

## 4. Context ownership

| Concern | Canonical owner | Important boundary |
|---|---|---|
| Product work, priority, readiness, and `WorkItemStatus` | `work_management` | Agent queues and boards are projections |
| Assignment, offer, claim, lease, heartbeat, mailbox, Ranex dispatch graph/fan-out/join, role profile, effective grant, and handoff | `agent_collaboration` | Workers cannot delegate/coordinate; no gate, permit, effect, merge, or release authority |
| `RunStatus`, workflow node, cancellation, governor decision, gate binding, grants/permits, and effect intent/outcome/reconciliation | `governed_execution` | Sole run/permit/effect-transition authority; cannot author `GateEvaluation` |
| Risk derivation, authorization rules, and human-decision record | `policy` | Models cannot lower risk or issue decisions |
| Identity, session, authentication, and secret handles | `identity_access` | Workers never receive raw standing credentials |
| Hierarchical budget, reservation, quota, and attributed usage | `resource_governance` | Ranex-created descendant work is charged transitively to every ancestor reservation |
| Workspace, worktree, branch, head, path ownership, and landing plan | `workspace` | A worker cannot choose or broaden its writable scope |
| Claims, evidence, qualified checker outputs, exact-subject snapshots, and `GateEvaluation` | `assurance` | `analytical_review` owns review observations; governed execution only binds a fresh evaluation |
| Harness, model, checker, sandbox, and route qualification evidence | `qualification` | The subject owner changes lifecycle state |
| Process conformance, fleet experiments, calibration, and corrective action | `process_assurance` | Measurements advise policy; they do not silently change it |
| Health observations, alerting, and incident coordination | `operations` | The owning context performs state recovery |
| Explicit provider/model/runtime/auth selection and route failure facts | `routing` | A friendly alias is never identity proof; no fallback chain exists |

Every stateful context commits its aggregate mutation and integration-outbox
record in one local transaction. Cross-context consumers are idempotent. No
fleet protocol assumes a distributed transaction.

## 5. Canonical fleet identities and typed state

The machine registries must define at least:

```text
AssignmentId       assignment_<uuidv7>
DispatchOfferId    offer_<uuidv7>
WorkerAttemptId    wattempt_<uuidv7>
WorkerLeaseId      lease_<uuidv7>
MailboxEnvelopeId  message_<uuidv7>
HandoffId          handoff_<uuidv7>
ReservationId      reservation_<uuidv7>
FleetExperimentId  fleetexp_<uuidv7>
RoleProfileId      ROLEPROFILE-<stable-name>-<sequence>
ToolGrantId        toolgrant_<uuidv7>
RuntimeAdapterId   RUNTIME-<stable-name>-<sequence>
RuntimeSessionId   runtimesession_<uuidv7>
```

These IDs are subordinate references. They never replace `ProjectId`,
`WorkItemId`, `RunId`, `ActivityId`, `WorkspaceId`, or exact subject identity.

### 5.1 `AssignmentStatus`

Owned by `agent_collaboration`:

```text
PENDING -> OFFERED -> CLAIMED -> RUNNING -> HANDOFF_READY -> COMPLETED
                     |           |              |
                     |           +-----------> FAILED
                     +-----------------------> EXPIRED

PENDING | OFFERED | CLAIMED | RUNNING -> CANCELLED
```

- `COMPLETED` means the bounded assignment produced an eligible immutable
  result reference.
- It does not mean the `Run`, `WorkItem`, review, gate, release, or outcome is
  complete.
- `EXPIRED` fences the old attempt; it does not prove the process is dead.
- Retry creates a new `WorkerAttemptId` and lease epoch linked to the prior
  attempt.

### 5.2 `DispatchOfferStatus`

Owned by `agent_collaboration`:

```text
OPEN -> CLAIMED
OPEN -> EXPIRED
OPEN -> REVOKED
```

An offer is an expiring eligibility invitation, not a grant or assignment
claim. `CLAIMED` records the winning atomic claim. Expiry or revocation cannot
change a claimed assignment or invalidate an issued lease except through the
lease and assignment protocols. Assignment `OFFERED` is reconciled against its
open offers; a projection cannot invent offer currency.

### 5.3 `LeaseStatus`

Owned by `agent_collaboration`:

```text
ACTIVE -> RELEASED
ACTIVE -> EXPIRED
ACTIVE -> REVOKED
```

Only the trusted coordinator clock establishes lease currency. Worker clocks
are observations. A lease contains an immutable assignment, attempt, principal,
identity session, route lock, workspace, issued time, expiry, role-ceiling
digest, exact effective tool/capability grant, runtime adapter and logical
runtime session, heartbeat policy, monotonically increasing fencing epoch, and
aggregate version.

### 5.4 `MailboxDeliveryStatus`

Owned by `agent_collaboration`:

```text
QUEUED -> DELIVERED -> ACKNOWLEDGED
QUEUED | DELIVERED -> DEAD_LETTERED
QUEUED | DELIVERED -> EXPIRED
```

A mailbox envelope carries references and typed coordination facts. It cannot
carry authority by assertion. Delivery and acknowledgment do not imply that a
command was accepted or executed.

### 5.5 `ReservationStatus`

Owned by `resource_governance`:

```text
PENDING -> ACTIVE -> SETTLED
                  -> EXHAUSTED -> SETTLED
PENDING | ACTIVE -> EXPIRED -> SETTLED
PENDING | ACTIVE -> REVOKED -> SETTLED
PENDING | ACTIVE -> RELEASED -> SETTLED
```

`SETTLED` means admitted descendant usage and late provider receipts were
reconciled to the reservation tree. It is not a refund or success assertion.
No non-`ACTIVE` reservation admits new work. A child cannot outlive or increase
the effective limits of any ancestor.

### 5.6 Termination causes

Termination is an event/cause on the owned `Run` or assignment, not a generic
status:

```text
GOAL_REACHED
HUMAN_CANCELLED
POLICY_DENIED
DEADLINE_EXCEEDED
BUDGET_EXHAUSTED
TURN_LIMIT
TOOL_LIMIT
OUTPUT_LIMIT
CONSECUTIVE_FAILURE_LIMIT
LOOP_DETECTED
LEASE_EXPIRED
WORKSPACE_INVALIDATED
SUBJECT_INVALIDATED
HARNESS_FAILURE
PROVIDER_FAILURE
SECURITY_VIOLATION
```

## 6. Assignment, claim, lease, and liveness protocol

### 6.1 Assignment admission

An assignment is eligible only when:

1. a registered Core-SDLC activity permits agent work;
2. the parent `WorkItemId` and current `WorkItemStatus` are exact;
3. a schema-valid task/review packet exists and is current;
4. deterministic policy derived the risk lane;
5. the role ceiling and runtime adapter resolve to accepted ADR-0011 catalog
   rows, and the assignment compiles an exact task-minimal proper subset;
6. one full provider/model/runtime/auth route lock, with all fallbacks and
   auxiliary/nested model calls disabled, is qualified;
7. a valid workspace and allowed-path plan exist for writing work;
8. resource reservations exist for the full Ranex-created assignment ancestry;
   and
9. maker/checker separation remains satisfiable.

The packet compiler, not a planner model, decides whether these facts are
present. A model may propose decomposition; the scheduler validates it against
accepted requirements, ownership, dependency, risk, budget, and path contracts.
Only that deterministic Ranex scheduler may create the resulting assignments
and fan-out/join edges.

### 6.2 Atomic claim

Claiming is one local `agent_collaboration` transaction:

```text
validate assignment status/version and offer currency
  -> validate principal/session/route/workspace eligibility
  -> compare-and-swap PENDING|OFFERED -> CLAIMED
  -> create WorkerAttempt
  -> issue WorkerLease with new fencing epoch and expiry
  -> append transition/journal record
  -> insert integration-outbox record
  -> commit
```

Two workers racing for one assignment cannot both commit a claim. A database
constraint binds one active lease to an assignment. Optimistic conflict is
visible and is not counted as worker failure.

### 6.3 Heartbeat and renewal

A heartbeat includes assignment, attempt, lease, fencing epoch, principal,
session, last accepted activity/event, and nonce. Renewal:

- uses the coordinator's trusted time;
- compare-and-swaps the active lease version;
- cannot extend past the packet's absolute deadline;
- cannot expand capability, path, route, budget, or subject;
- is denied after cancellation, revocation, invalidation, or expiry; and
- writes a rate-limited liveness event without logging raw prompt content.

Heartbeats prove recent protocol contact, not useful progress or correct work.
The initial release-pinned profile is a 60-second lease, 15-second heartbeat,
renewal no later than 30 seconds remaining, and 15-second post-expiry reclaim
grace, as selected by ADR-0005. A profile change follows `SUB-LEASE-001`.

### 6.4 Expiry, reclaim, and fencing

Expiry is a two-stage protocol:

1. the liveness monitor records `SUSPECTED_STALE` as an observation;
2. `agent_collaboration` rechecks lease version, deadline, heartbeat grace,
   coordinator health, and cancellation state, then records `EXPIRED`.

Reclaim creates a new attempt and higher fencing epoch. Every worker-facing
write, result submission, mailbox acknowledgment, model call, and tool request
must carry the current epoch. A stale worker can continue computing locally but
cannot mutate canonical state, consume budget, submit an eligible result, or
request an effect.

The previous attempt's artifacts remain retained and labeled `LATE` or
`ORPHANED`; they are never silently merged into the new attempt.

### 6.5 Completion and handoff

The worker:

1. seals its `RunResult` and artifacts;
2. submits only content-addressed references plus the exact current lease;
3. stops requesting new mutable capabilities;
4. releases the lease or allows the coordinator to release it atomically with
   assignment completion; and
5. emits an immutable `AgentHandoff` reference.

The receiving service validates packet, candidate, workspace, route, attempt,
lease epoch, evidence, and artifact digests. Worker prose cannot convert
missing evidence into completion.

## 7. Execution governor

Every worker attempt is wrapped by a deterministic governor owned by
`governed_execution`. Its active profile is release-pinned and exact-subject
bound.

### 7.1 Required ceilings

The profile may impose:

- absolute deadline and per-activity timeout;
- model request, reasoning-token, output-token, and response-byte budgets;
- tool-call, process, filesystem-output, and network-byte budgets;
- worker-created assignment count, provider-subagent count, and nesting depth,
  all fixed to zero;
- concurrent-process and concurrent-worker ceilings;
- retry and consecutive-failure limits; adapter/provider/model fallback and
  auxiliary-model limits are fixed to zero;
- artifact/log growth and context-compilation budgets; and
- human-response expiry.

The caller owns one absolute budget tree. A Ranex-created descendant assignment
has its own lease/governor and cannot outlive or exceed any ancestor. The leaf
worker cannot create that descendant.

### 7.2 Result-aware loop detection

Loop detection uses a bounded window of normalized action type, exact subject,
canonical arguments, result class, state version, and progress evidence. It
detects:

- identical tool/action repetitions without state change;
- alternating action cycles;
- repeated retries against an unchanged failure;
- mailbox polling without new sequence;
- repeated planning/decomposition of an unchanged packet; and
- growing output without acceptance-criterion progress.

The response ladder is:

```text
observe -> warn -> reduce capability/rate -> require checkpoint
        -> suspend -> escalate or terminate
```

A model cannot mark its own repetition productive. A false-positive dispute is
an observation and corrective-action input, not permission to bypass the
governor.

### 7.3 Cancellation and hard stop

Cancellation is cooperative first, then enforced:

1. stop new offers, model calls, and tool permits;
2. request checkpoint and bounded cleanup;
3. revoke lease and capability projection;
4. terminate the sandbox/process tree after grace;
5. reconcile worktree, artifacts, budget, mailbox, outbox, and external
   effects; and
6. record the final cause and unknown outcomes.

No cleanup step receives broader authority than the original attempt.

## 8. Topology and concurrency policy

Fleet size and topology are derived from work structure and measured verifier
capacity. They are not product goals.

### 8.1 Default

The default is one bounded worker. Parallelism requires a recorded reason:

- independent read-only research;
- disjoint, contract-defined work with isolated worktrees;
- independent review lenses;
- repeated sampling behind a qualified verifier; or
- separate projects with independent mutable state.

### 8.2 Permitted topology classes

| Class | Permitted use | Constraint |
|---|---|---|
| `SINGLE_WORKER` | Default implementation or analysis | All normal packet and review rules |
| `STAR_READ` | Ranex scheduler dispatches independent read-only leaf workers | Coordinator is a deterministic Ranex service; artifacts are immutable |
| `PARTITIONED_WRITE` | Disjoint path/API partitions in separate worktrees | Path ownership and dependency order validated before dispatch |
| `STAGED_CHAIN` | Untrusted planner proposal → Ranex-created implementer assignment → Ranex-created verifier assignment | Each worker is leaf-only; every stage has a new packet/attempt and required independence |
| `REPEATED_SAMPLE` | Multiple candidate analyses/patches for one subject | Qualified selector/verifier; equal-budget evidence; no majority-as-truth |
| `CROSS_FAMILY_REVIEW` | Separate maker and challenger routes | Blind initial observation and actual route-fact comparison |

A peer mesh over shared mutable repository or authority state is prohibited.
Workers do not address or coordinate other workers. A worker submits immutable
artifacts and handoff facts to Ranex; only Ranex creates the next assignment and
delivers its durable envelope/references.

### 8.3 Read parallel, isolate write, serialize landing

- Read-only work may fan out within source and data-classification policy.
- Writing workers receive separate validated worktrees and disjoint declared
  ownership unless an accepted integration plan states the dependency.
- Shared files are assigned to one writer at a time.
- Integration/rebase is a distinct bounded assignment with exact inputs.
- Landing is serialized through the human-controlled landing authority.
- No worker self-merges, regardless of worker count.
- A reconciler model may propose a conflict resolution patch; it cannot decide
  which semantic behavior wins or land the result.

### 8.4 Backpressure

The scheduler stops admitting work when any configured limit is reached:

- qualified verifier queue/capacity;
- human decision or review queue;
- writable workspace/path contention;
- unresolved dependency frontier;
- provider, token, cost, output, or host-resource budget;
- stale-lease/dead-letter/error threshold;
- incident or security freeze; or
- release/configuration-management freeze.

Agent utilization is never a reason to bypass backpressure.

## 9. Workspace and write isolation

Every writing attempt receives:

- repository identity and exact base;
- dedicated worktree identity and canonical path;
- allowed, read-only, forbidden, and generated path sets;
- expected candidate branch/head;
- dependency and public-API constraints;
- secret-free environment projection;
- tool/process/network profile; and
- cleanup/retention policy.

Tool-boundary enforcement checks paths after symlink/canonical-path resolution.
It denies traversal, alternate worktree roots, authority database mounts,
unapproved `.git` mutations, hidden-fixture reads, and writes through generated
or temporary indirection.

A hook may deny or transform an attempted call only according to an active,
versioned policy. Hooks are enforcement adapters, not new business-rule owners.

## 10. Context and handoff

The durable handoff is an artifact graph, not a compressed conversation:

```text
TaskPacket / ReviewRequest
  -> exact source manifest
  -> immutable RunResult
  -> changed artifact and evidence references
  -> unresolved findings/unknowns
  -> requested next role/action
```

Worker-visible packets contain only the context required by the role. Hidden
fixtures, answer keys, expected secret results, independent-review observations,
and other holdouts remain in verifier-only storage.

Compaction may summarize transient reasoning. It cannot rewrite:

- requirements or acceptance criteria;
- exact-subject identity;
- decisions, permits, findings, deviations, or unknowns;
- source/evidence/artifact digests;
- rejected approaches with safety consequences; or
- budget, route, lease, and capability facts.

The next worker pulls referenced artifacts directly. A Ranex handoff summary is
a navigation aid, not a substitute for the source.

## 11. Budget and permission gateway

### 11.1 Hierarchical reservations

`resource_governance` maintains a reservation tree:

```text
project / release budget
  -> WorkItem budget
     -> Run budget
        -> WorkerAttempt budget
           -> model/tool/effect operation
```

Every charge is atomically attributed to its leaf and Ranex-created assignment
ancestry. Retry, review, polling, and generated output consume the same parent
budget unless a human-authorized new reservation is issued. Attempted worker
spawn, provider fallback, or auxiliary model use is denied rather than merely
charged.

The system records token/unit usage and provider-reported cost as separate
facts. A mutable rate card cannot rewrite already attributed usage.

`null` means a limit has not been established and blocks activation; it never
means unlimited. Zero denies the dimension. `NOT_APPLICABLE` requires a typed,
policy-backed decision and evidence. Every active reservation has an absolute
deadline plus all dimensions mandated by its work class/risk policy. A child
binds the parent digest and aggregate version used at admission, and current
parent `ACTIVE` state is rechecked by compare-and-swap.

### 11.2 Permission enforcement

Every model/tool request passes:

```text
authenticated attempt + current fencing epoch
  -> exact subject and workspace check
  -> active capability and policy check
  -> route/harness/sandbox qualification check
  -> budget reservation
  -> adapter-boundary enforcement
  -> result observation and usage settlement
```

Before the runtime starts, the role profile supplies only a maximum ceiling.
The assignment compiler begins from empty sets and emits exact effective tool
and capability IDs as a proper subset. Startup must attest that the initialized
runtime's actual model, working directory, tool surface, permission mode, MCP
servers, agents, skills, plugins/extensions, runtime version, and observed auth
source match the route lock and grant. A mismatch denies dispatch.

Provider allow rules are not treated as tool restrictions. For Claude,
`allowed_tools` only auto-approves; calls may also bypass `can_use_tool`.
Accordingly the strict adapter compiles the real `tools` set and deny
complement, uses `dontAsk` rather than model-classified `auto`, and places a
catch-all `PreToolUse` or SDK custom-tool gateway before every observed call.
The ask callback is a fallback, not the PEP. Agent/Task, Workflow, SendMessage,
ToolSearch, Cron/RemoteTrigger, EnterWorktree, provider team/delegation, and
background surfaces are absent. Nested provider event lineage is a containment
violation.

User/project/local setting sources, auto-memory, ambient MCP, apps/plugins,
skills, and agents are disabled. Each lease has an isolated configuration
directory and exact project cwd. If a bounded shell tool is granted, its startup
files, environment, filesystem, network, cwd, and process tree are separately
contained. The adapter still routes every effect through `CapabilityBus`;
provider permission semantics never replace Ranex policy.

External effects continue through the full
evidence → gate → human decision where required → consumable authority grant
→ permit → `CapabilityBus` path. A budget/permission gateway cannot shorten
that order.

## 12. Verification is the concurrency constraint

Ranex may increase worker concurrency only when qualified verification,
integration, and human decision capacity can bound false acceptance and
recovery risk.

The ordered verification preference is:

1. deterministic static/schema/architecture checks;
2. executable unit, property, contract, integration, security, migration, and
   recovery checks;
3. independent exact-subject review observations;
4. withheld and adversarial verification unavailable to the maker;
5. representative product/user validation; and
6. accountable human decisions required by risk and lifecycle.

An LLM judge is an untrusted checker candidate. It requires qualification,
calibration, order/randomness testing where applicable, exact route identity,
and deterministic or human escalation. Model consensus is never a gate.

Verifier overload triggers backpressure. It does not justify shallower review,
exposing holdouts, weakening tests, or allowing worker self-acceptance.

## 13. Measurement harness

The measurement harness is the first **fleet-scaling experiment instrument**
after the Core-SDLC contract, authority, evidence, identity, and isolation
skeletons exist. It is not the first Ranex authority artifact and cannot govern
ADR-0001.

### 13.1 Experiment contract

Each fleet experiment predeclares:

- exact task population, inclusion/exclusion, work classes, and risk lanes;
- single-worker, best-of-N, random/static-routing, and current-process controls;
- topology, worker count, exact model/route/runtime adapter, role ceiling,
  effective tool grant, session-affinity mode, prompts, budgets, and time
  limits;
- paired or blocked assignment and repeated seeds/runs;
- capability, regression, and hidden-anchor splits;
- verifier version, false-accept/false-reject calibration, and holdout access;
- primary outcome, guardrail outcomes, minimum detectable effect, analysis
  method, and stop rule;
- infrastructure-error, cancellation, timeout, and missing-result treatment;
- cost, latency, human effort, rework, and operational-risk accounting; and
- immutable raw evidence, analysis code, result, limitation, and decision refs.

### 13.2 Required measures

At minimum:

- task success with uncertainty interval;
- false-accept and false-reject rates;
- escaped defect and post-landing rework;
- wall time and end-to-end lead time;
- cold/warm time to initialized event, first structured event, first model
  content, and completion;
- runtime/CLI process spawn count, provider/model request count, tool-call
  amplification, interrupt-to-terminal latency, and cleanup latency;
- token, tool, network, output, host, and human-review cost;
- CPU, peak memory, connected-idle memory, and sandbox/supervisor overhead;
- assignment collision, stale lease, reclaim, duplicate attempt, and late
  result rate;
- mailbox delay, dead-letter, polling, and duplicate-delivery rate;
- loop termination, consecutive failure, cancellation, and orphan cleanup;
- write conflict, integration failure, and rollback rate;
- context omission/leakage and hidden-fixture tamper rate; and
- cross-session/assignment leakage, ambient-source discovery, unexpected tool,
  nested worker lineage, fallback, auxiliary call, and route-drift rate; and
- outcome by task class, risk lane, repository area, route, and topology.

Numeric thresholds from external research are hypotheses until reproduced on
Ranex's workload. A result below the local noise floor remains `UNKNOWN`, not
evidence for scaling.

### 13.3 Decision rule

More workers are permitted only when the exact configuration:

- improves the accepted product/process outcome over the strongest relevant
  control by more than measurement uncertainty;
- does not worsen safety, false acceptance, rework, or human burden beyond the
  accepted limit;
- fits verifier, integration, and resource capacity; and
- passes failure-injection and recovery tests.

Otherwise the selected topology remains one worker or a smaller measured
configuration.

## 14. Routing and learned orchestration

Static, explainable, release-pinned routing is the default. Route choice binds
one actual provider/model/transport/runtime adapter, configured auth intent,
observed effective auth source/subject, qualification, sandbox, role ceiling,
effective tool grant, context/output limit, and usage/price observation.
Vendor-internal auth/entitlement facts the adapter cannot observe are recorded
`UNKNOWN`, not inferred from a plan label.

The route lock has no adapter/provider/model fallback and no auxiliary model or
provider subagent. Runtime outage, overload, or malformed output terminates the
attempt with a typed failure. Only the Ranex scheduler may evaluate a new route
and create a separately authorized assignment. A local individual
subscription-backed route and a distributed-product API/BYOK/supported-cloud
route are different route classes and never share credentials or entitlement
assumptions.

A learned router, topology optimizer, prompt optimizer, or conductor is
quarantined R&D until:

1. deterministic contracts and a stable measurement harness exist;
2. training, validation, test, and hidden anchors are separated;
3. the reward is execution-grounded and tamper-resistant;
4. the optimizer cannot change authority, risk, permission, hidden data, or
   verification depth;
5. candidate policy is evaluated offline against strong controls;
6. rollback and drift detection are proven; and
7. a human accepts the exact policy/version for a bounded scope.

Learning may propose configuration. It never edits constitutional policy or
activates itself, enters a leaf runtime, supplies fallback, or dispatches a
worker.

## 15. Security and blast radius

### 15.1 Default worker posture

- ephemeral, least-privilege principal and session;
- one project, packet, workspace, assignment, attempt, and lease;
- one role ceiling, exact proper-subset grant, explicit runtime/model/auth route,
  and assignment-affine logical session;
- no authority database or operator-home mount;
- no raw standing credential;
- no worker spawn/delegation/team/coordinator tool, fallback, auxiliary model,
  ambient setting/MCP/app/plugin/skill/agent/memory, or background surface;
- deny-by-default filesystem, process, network, tool, model, and effect
  capabilities;
- explicit output and artifact limits;
- secret handles resolved only at the final authorized adapter edge; and
- complete structured observations with classified-content redaction.

“Full permissions” is not a fleet tier. A high-risk task receives a stronger
sandbox and narrower permit, not an unbounded worker.

### 15.2 Fleet-specific threats

Controls must address:

- duplicate workers racing on the same assignment;
- stale worker continuing after reclaim;
- mailbox spoofing, replay, dead letters, and recipient confusion;
- compromised planner widening decomposition or permissions;
- colluding maker/reviewer or shared-context bias;
- reward hacking, test deletion, new-file fixture collision, answer-key/history
  mining, and grader bypass;
- attempted budget laundering through hidden provider workers, fallback, or
  auxiliary model calls;
- prompt injection crossing from source/retrieval into tool calls;
- cross-project context or knowledge leakage;
- worker-created persistent hooks, startup files, services, or credentials; and
- stateful client reuse across assignments, projects, auth subjects, roles,
  grants, sandboxes, or workspaces; and
- compromised reconciler selecting or landing unsafe semantics.

Hidden verification is mounted only in a verifier environment the maker cannot
write or inspect. Candidate diffs are scanned for modification, shadowing, or
collision with verifier paths.

## 16. Durability, recovery, and reconciliation

Durable records include assignment transitions, offers, leases, heartbeats,
mailbox envelopes, attempts, run transitions, budgets, tool/model observations,
artifacts, handoffs, cancellation, and recovery decisions.

Crash recovery:

1. acquires the single-host recovery/maintenance lock;
2. validates database, journal, outbox, artifacts, release/schema, and active
   policy consistency;
3. reconstructs active assignments/runs without executing effects;
4. marks uncertain leases/runs for recheck rather than guessing;
5. reconciles sandboxes, process trees, worktrees, mailboxes, budgets, provider
   requests, and external effects;
6. fences expired/old attempts before redispatch;
7. resumes only exact workflow nodes whose replay contract permits it; and
8. records every disposition and remaining `OUTCOME_UNKNOWN`.

No restart blindly replays the last prompt, tool call, or effect. Replay is
typed and node-specific. External calls use documented at-least-once or
at-most-once attempt semantics plus idempotency/reconciliation; never
“exactly once.”

Cancellation first uses the official runtime interrupt, drains correlated
terminal events to a bounded deadline, then calls the pinned SDK/app-server
disconnect. The outer sandbox/supervisor verifies process-tree cleanup and
performs only its qualified containment action when cleanup is incomplete.
Ranex does not reimplement undocumented SDK child-PID behavior. A session is
resumed only by its exact recorded ID under the complete unchanged affinity
key; otherwise it is fenced and a fresh assignment is required.

## 17. Observability and operations

The control plane exposes structured, project-scoped views for:

- assignment/lease/attempt state and age;
- worker/harness/route identity and qualification;
- current workflow node, governor ceilings, and termination cause;
- budget reservation, usage, forecast, and denial;
- mailbox delivery/dead-letter state;
- workspace/head/path ownership and integration queue;
- verification capacity, queue age, false-accept/false-reject calibration;
- incident, cancellation, stale-worker, and orphan recovery;
- cold/warm runtime/model/tool/provider latency, spawn/call amplification,
  memory, errors, explicit no-fallback proof, auth/tool-surface attestation,
  nested-lineage violations, and drift; and
- fleet experiment subject, controls, uncertainty, and decision.

Raw prompts, source, reasoning, model output, and secrets are classified
artifacts. Routine telemetry carries references, sizes, result classes, timing,
and redacted error facts.

Operations may alert or initiate an idempotent recovery command. It cannot
mutate another context's state directly.

## 18. Target file and contract map

The full-system tree must reserve:

```text
architecture/contracts/
├── assignment-status.yaml
├── dispatch-offer-status.yaml
├── lease-status.yaml
├── mailbox-delivery-status.yaml
├── reservation-status.yaml
├── fleet-experiment-status.yaml
├── termination-causes.yaml
├── fleet-topologies.yaml
├── fleet-experiment-policy.yaml
├── fleet-control-crosswalk.yaml
├── worker-role-profiles.json
└── runtime-adapters.json

src/ranex/agent_collaboration/
├── api/
│   ├── commands.py
│   ├── queries.py
│   ├── events.py
│   └── views.py
├── domain/
│   ├── assignments.py
│   ├── dispatch_offers.py
│   ├── worker_attempts.py
│   ├── role_profiles.py
│   ├── effective_tool_grants.py
│   ├── leases.py
│   ├── heartbeats.py
│   ├── mailboxes.py
│   ├── handoffs.py
│   ├── dispatch_graphs.py
│   ├── fanout_join.py
│   └── invariants.py
└── application/
    ├── assignment_service.py
    ├── claim_service.py
    ├── liveness_service.py
    ├── mailbox_service.py
    ├── topology_service.py
    ├── fanout_join_service.py
    ├── handoff_service.py
    └── ports/
        ├── worker_dispatch.py
        ├── coordinator_clock.py
        └── collaboration_store.py

src/ranex/governed_execution/
├── domain/
│   ├── governor.py
│   ├── termination.py
│   └── progress_window.py
└── application/
    ├── cancellation_service.py
    └── ports/
        └── worker_runtime.py

src/ranex/resource_governance/
├── domain/
│   ├── reservation_tree.py
│   └── usage_settlement.py
└── application/
    └── budget_gateway.py

src/ranex/adapters/
├── harnesses/common/
│   ├── governor_bridge.py
│   ├── fencing_guard.py
│   ├── role_grant_compiler.py
│   ├── pre_tool_gateway.py
│   ├── runtime_manager.py
│   └── usage_meter.py
├── harnesses/claude_agent_sdk/
│   ├── runtime_adapter.py
│   ├── event_normalizer.py
│   └── lifecycle.py
├── harnesses/codex_app_server/
│   ├── runtime_adapter.py
│   ├── event_normalizer.py
│   └── lifecycle.py
├── process_assurance/
│   ├── fleet_measurement_reader.py
│   └── experiment_runner.py
└── workers/
    └── local_process/

tests/
├── contract/fleet_control/
├── integration/fleet_control/
├── unit/fleet_control/property/
├── resilience/fleet_control/
├── security/bypass_matrix/
└── evaluation/fleet_control/
    ├── baselines/
    ├── paired_trials/
    ├── hidden_anchors/
    └── reports/
```

`hidden_anchors/` is a verifier-only logical path in the evaluation environment,
not worker-visible repository content.

## 19. Public commands, queries, and events

### 19.1 Commands

```text
CreateAssignment
CompileEffectiveToolGrant
BindWorkerRuntimeRoute
OfferAssignment
ClaimAssignment
RenewLease
ReleaseLease
RevokeLease
RecordHeartbeat
EnqueueMailboxEnvelope
AcknowledgeMailboxEnvelope
SubmitWorkerResult
RecordHandoff
ExpireStaleLease
ReclaimAssignment
CancelAssignment
ReserveWorkerBudget
ActivateWorkerReservation
SettleWorkerUsage
ReleaseWorkerReservation
RevokeWorkerReservation
RequestWorkerRun
CancelWorkerRun
CloseWorkerRuntime
```

Every command carries command/correlation/causation ID, expected aggregate
version, exact parent references, authenticated principal/session, and the
fields required for idempotency.

### 19.2 Queries

```text
GetAssignment
GetRoleProfile
GetEffectiveToolGrant
GetRuntimeSession
GetCurrentLease
GetWorkerAttempt
GetMailboxFrontier
GetHandoff
GetFleetCapacity
GetVerifierBackpressure
GetBudgetTree
GetFleetExperiment
```

Views are projections and cannot authorize a transition.

### 19.3 Integration events

```text
AssignmentCreated
AssignmentOffered
DispatchOfferExpired
AssignmentClaimed
WorkerAttemptStarted
WorkerRuntimeAttested
WorkerRuntimeContainmentViolated
WorkerHeartbeatObserved
WorkerLeaseExpired
WorkerLeaseRevoked
WorkerAttemptFenced
WorkerRuntimeClosed
WorkerResultSubmitted
WorkerHandoffRecorded
AssignmentCompleted
AssignmentFailed
MailboxEnvelopeDeadLettered
FleetBackpressureActivated
WorkerReservationExhausted
WorkerReservationSettled
FleetExperimentCompleted
```

Events state what the owner recorded. Consumers still validate their own
preconditions and exact subject.

## 20. Failure-handling matrix

| Failure | Detection | Required response | Forbidden response |
|---|---|---|---|
| Double claim | Unique constraint/CAS conflict | One winner; expose loser conflict | Let both proceed |
| Missing heartbeat | Liveness observation | Grace/recheck, expire, fence, reclaim | Assume completion |
| Stale worker returns | Epoch mismatch | Retain late artifact, reject eligibility | Merge late output |
| Polling storm | Mailbox/governor metrics | Backoff, notify, suspend | Spend until budget ends |
| Dead recipient | Delivery expiry/dead letter | Reassign/escalate with trace | Drop message silently |
| Repeated tool loop | Result-aware detector | Checkpoint, restrict, suspend/terminate | Prompt-only reminder |
| Worker/provider attempts nested delegation | Missing tool, pre-tool denial, nested lineage detector | Terminate/fence attempt; retain containment evidence | Merely charge the child budget |
| Effective tool grant exceeds role ceiling or actual startup surface drifts | Catalog/subset/startup attestation | Deny dispatch or terminate/fence | Trust prompt or `allowedTools` |
| Ambient setting/MCP/plugin/skill/agent/memory appears | Startup attestation and canary | Deny dispatch; quarantine adapter/profile | Continue with “harmless” ambient tools |
| Runtime attempts fallback, auxiliary model, or route mutation | Route/event/provider observation | Fail attempt; return control to Ranex | Let provider choose another model |
| Stateful client affinity mismatch | Complete reuse-key comparison | Disconnect/clean; require fresh assignment/session | Reset prompt and reuse conversation |
| Interrupt does not reach correlated terminal event | Drain deadline/supervisor observation | SDK disconnect, outer-supervisor cleanup, reconcile `OUTCOME_UNKNOWN` | Start the next turn on the same client |
| Descendant budget escape | Reservation-tree mismatch | Deny and incident/corrective action | Charge no ancestor |
| Workspace escape | Canonical-path/hook/sandbox denial | Stop attempt, preserve evidence | Trust worker apology |
| Hidden-fixture access | Mount/audit canary | Invalidate result and qualification | Treat pass as evidence |
| Reviewer correlation | Independence evaluator | Re-dispatch qualified independent attempt | Majority vote |
| Verifier overload | Queue/capacity threshold | Backpressure new work | Reduce required checks |
| Provider drift | Actual route mismatch | Probation and requalification | Keep friendly alias active |
| Effective auth differs from configured route | Sanitized environment plus initialized auth observation | Deny/fence; record configured/observed/unknown facts separately | Infer entitlement from account label |
| Merge conflict | Landing/integration check | Dedicated resolution packet and review | Agent self-arbitration |
| Process crash | Journal/outbox/lease recovery | Fence, replay eligible nodes, reconcile | Blindly repeat last call |
| External effect unknown | Missing/ambiguous receipt | `OUTCOME_UNKNOWN` and reconcile | Retry irreversible effect |

## 21. Adoption gates

These are process-adoption controls, not `WorkItemStatus`, `RunStatus`, or model
verdicts.

### `SDLC-ADOPT-FLEET-A` — Contract foundation

- Core SDLC and architecture contracts exist and agree.
- Assignment, lease, mailbox, termination, budget, path, role, route, and
  topology namespaces validate.
- ADR-0011's sole fenced catalog projects without drift to
  `worker-role-profiles.json` and `runtime-adapters.json`; role ceilings and
  assignment grants remain distinct.
- No agent owns approval, merge, release, or closure.
- No worker owns create/dispatch/fan-out/join, fallback, auxiliary-model, or
  route-mutation authority.

### `SDLC-ADOPT-FLEET-B` — Single-worker baseline

- One worker completes a bounded tracer through packet, lease, governor,
  evidence, independent review, human landing, and cleanup.
- The official runtime startup attests the exact full model, route/auth facts,
  role/minimal tool set, cwd, permission/MCP/extension surface, and no ambient
  or nested-worker surface.
- Denial, cancellation, expiry, late result, and stale-subject paths pass.
- Interrupt, correlated drain, SDK disconnect, outer-supervisor cleanup, exact
  resume, route-outage no-fallback, and stateful-affinity mismatch paths pass.
- The measurement harness establishes reproducible single-worker baselines.

### `SDLC-ADOPT-FLEET-C` — Concurrency safety

- Atomic double-claim, fencing, heartbeat, reclaim, dead-letter, worktree
  isolation, path collision, budget inheritance, and process-crash tests pass.
- Parallel read and partitioned write modes preserve one canonical writer.
- Ranex alone creates deterministic fan-out/join; every provider worker remains
  leaf-only and any nested provider lineage is denied.

### `SDLC-ADOPT-FLEET-D` — Verifier capacity

- False-accept, false-reject, tamper, and reviewer-drift calibration exists.
- Hidden anchors are inaccessible to makers.
- Admission backpressure activates before verification or human review is
  overloaded.

### `SDLC-ADOPT-FLEET-E` — Measured topology

- A predeclared, repeated, equal-budget experiment beats the strongest relevant
  control beyond the local uncertainty floor.
- Cold one-shot, cold managed-client, and same-assignment/session connected
  paths report first-event/content and total latency, process/model/tool
  amplification, CPU/memory, cancellation/cleanup, correctness, and leakage.
- Cost, rework, safety, and human burden remain within accepted policy.
- The exact topology/route profile is human accepted for a bounded scope.

### `SDLC-ADOPT-FLEET-F` — Learned control, if ever selected

- Offline candidate generation, hidden evaluation, tamper resistance, drift,
  rollback, and non-self-activation tests pass.
- A human-accepted ADR names the exact learnable parameters and permanent
  authority exclusions.
- Learned control remains outside leaf runtimes and cannot supply fallback,
  auxiliary calls, worker dispatch, or a broader role grant.

Failure of a later gate returns to the last proven configuration. It never
invalidates the full map or licenses a shortcut.

## 22. Kimi research disposition

The 89-file Kimi addendum is advisory research, not a governing process. Its
exact corpus and detailed reconciliation are recorded separately.

| Research proposition | Ranex disposition |
|---|---|
| Treat worker fleets as distributed systems | **Accepted** as an engineering lens |
| Atomic claims, expiring leases, heartbeats, reclaim, and fencing | **Accepted and strengthened** with typed ownership and exact-subject rules |
| Execution governor and result-aware loop detection | **Accepted** under `governed_execution` |
| Transitive budget and permission gateway | **Accepted** under `resource_governance`, policy, and the PEP |
| Tool-boundary hooks over prompt-only restrictions | **Accepted** as adapter enforcement |
| Durable event log and crash recovery | **Accepted** with per-context UoW/outbox and typed replay |
| Verification capacity bounds useful fleet size | **Accepted** without importing external numeric thresholds |
| Artifacts over transcript relay | **Accepted** under content-addressed packet/handoff contracts |
| Parallel reads, isolated writes, serialized integration | **Accepted** |
| Measurement harness as the first build artifact | **Resequenced**: first fleet-scaling instrument after constitutional/authority foundations |
| Generic task registry/status schema and `.fleet/` layout | **Rejected as canonical structure**; useful concepts map to typed Ranex contexts and registries |
| Operator approval directly authorizes a gateway action | **Rejected**; decision → grant → permit → effect order remains mandatory |
| “Full permissions” workers | **Rejected**; all workers are least-privilege and sandboxed |
| Worker self-merge or reconciler merge authority | **Rejected**; landing remains human-controlled |
| Worker/subagent-controlled delegation or model-native conductor | **Rejected**; only deterministic Ranex services create and coordinate assignments, while every provider harness is leaf-only |
| Role-wide maximum toolset as routine grant | **Rejected**; assignment compilation starts empty and emits a task-minimal proper subset with actual-surface attestation |
| Remove human code review behind holdouts | **Rejected for the accepted policy**; any future change requires evidence and a superseding human ADR |
| Fixed fleet sizes, thresholds, cost ratios, or model mix from external reports | **R_AND_D** until locally reproduced |
| Learned routing/topology/conductor | **Deferred as scheduling, mapped as R&D**; never architecture status or authority |

## 23. Highest-value falsification tests

1. Two workers race for one assignment; exactly one active lease exists.
2. A reclaimed stale worker attempts every write/tool/result path; the old
   fencing epoch is denied everywhere.
3. A worker/provider attempts to spawn, delegate, coordinate, or emit nested
   lineage; the surface is absent, the attempt is denied/fenced, and no child
   assignment or model charge is admitted.
4. A worker writes outside its canonical path through symlink, alternate Git
   worktree, generated path, subprocess, and helper tool; every route is denied.
5. A model repeats semantically identical failed actions with syntactic
   variation; result-aware loop detection suspends it within policy.
6. A maker attempts to read, overwrite, shadow, or predict hidden verification;
   access is denied and the candidate is invalidated.
7. A planner proposes overlapping writers and broader capabilities; the
   deterministic Ranex scheduler rejects the plan and the planner cannot create
   either assignment.
8. A reconciler produces a plausible conflict patch and attempts self-landing;
   it can submit only a proposal and human-controlled landing remains required.
9. The coordinator crashes at every claim/heartbeat/completion/outbox boundary;
   recovery yields no double assignment, lost result, or blind replay.
10. Verifier or human-review capacity is exhausted; admission backpressure
    stops new work without reducing assurance.
11. Provider/model/auth/tool facts drift behind a stable alias; startup/event
    attestation fails and the route and dependent assignments enter
    probation/invalidation without fallback.
12. A parallel configuration appears faster but increases false acceptance,
    rework, or human burden within uncertainty; the experiment cannot authorize
    scaling.
13. A role ceiling contains seven tools but the task needs two; the runtime
    initializes with exactly two. A ceiling-wide or equal-to-ceiling grant,
    unknown tool, `allowedTools`-only restriction, or startup mismatch is denied.
14. User/project settings, auto-memory, MCP, apps/plugins, skills, agents,
    background execution, shell startup files, or a changed cwd are injected;
    startup/pre-tool/sandbox controls deny every ambient path.
15. The primary model is unavailable and the provider offers a fallback,
    advisor, or auxiliary model; the attempt fails visibly and only Ranex may
    admit a new explicitly locked assignment.
16. A connected client is offered an unrelated assignment, workspace, auth
    subject, role, grant, sandbox, or project; affinity rejects reuse and leak
    canaries remain absent in a fresh session.
17. Cancellation races a tool event; Ranex interrupts, drains by correlated
    IDs, calls SDK disconnect, verifies outer-supervisor cleanup, and never
    starts the next turn on an ambiguous client.
18. Cold one-shot, cold managed-client, and assignment-affine connected-client
    trials record all ADR-0011 latency/call/process/memory/correctness/leakage
    measures; no unmeasured “blazing fast” claim can pass.

## 24. Selected defaults and substitution gates

ADR-0005 selects one-worker default, explicit read-only fan-out, isolated write
worktrees, serialized human landing, the release-pinned lease profile, and
inactive learned control. ADR-0011 supersedes its incomplete routing/topology
wording: Ranex alone orchestrates, all provider/harness workers are leaf-only,
roles define ceilings and assignments exact proper subsets, and one explicit
official runtime/model/auth route has no fallback or auxiliary call. Connected
reuse is same-assignment/session-affine only. Poll/push dispatch and reviewer
route are deterministic release-profile fields selected from registered
task/risk facts, not worker discretion.

Alternatives may replace a default only through the corresponding `SUB-*`
evidence gate and a superseding owner-accepted ADR. Fleet experiments can
recommend a change; they cannot activate it or reduce the Core-SDLC risk lane
or human-review requirement. No alternative may reintroduce Hermes/Nous live
inference, worker delegation, broad tools, fallback, or cross-task state. No
selected default is claimed implemented until
the applicable `SDLC-ADOPT-FLEET-*` evidence passes.

## 25. Definition of done

The fleet-control map is documented when:

- every aggregate, state, command, event, owner, port, adapter, path, failure,
  security boundary, metric, gate, and R&D attachment point above is represented
  in the machine-contract plan;
- ADR-0011's single catalog projects exact role ceilings and runtime adapters,
  with assignment narrowing, leaf/no-fallback rules, auth classes, affinity
  keys, lifecycle, and definition-only status intact;
- its terminology is cross-walked to Core SDLC, `Run`, artifacts, and the
  full-system architecture;
- Kimi, DeepSeek V4 Pro, HY3, and other research findings have explicit
  dispositions; and
- every source and generated review artifact has an exact manifest and
  provenance classification.

The fleet control plane is implemented only when:

- all `SDLC-ADOPT-FLEET-A` through the selected deployment gate pass;
- real harness/tool paths pass the bypass and fencing matrix;
- Ranex is the only cross-worker orchestrator; official runtimes remain
  leaf-only and no nested lineage, provider delegation, fallback, auxiliary
  model, or route mutation succeeds;
- every assignment's exact actual tool surface is a startup-attested proper
  subset of its role ceiling, with no ambient source and every effect through
  `CapabilityBus`;
- crash, cancellation, stale-worker, budget, mailbox, and recovery tests pass;
- interrupt/drain/SDK-disconnect/supervisor cleanup, exact resume, and
  assignment/session affinity tests pass;
- verifier capacity and uncertainty are measured from Ranex work;
- cold/warm latency, call/process amplification, CPU/memory, correctness, and
  leakage are measured against owner-accepted thresholds;
- local subscription and product API/BYOK/cloud routes pass current vendor
  terms and effective-auth attestation, and no Hermes/Nous route exists;
- no worker can approve, merge, release, or create an external effect outside
  the normal authority path; and
- the human governor accepts the exact evidence and active profile.

Until then the correct statement is:

> **Full AI-worker fleet-control target mapped; runtime enforcement and measured
> scaling remain unproven.**
