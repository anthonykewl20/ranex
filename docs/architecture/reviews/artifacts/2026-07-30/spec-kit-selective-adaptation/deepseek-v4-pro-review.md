# Independent Architecture and Product-Fit Review

**Subject:** Whether Ranex should selectively adapt proven patterns from `github/spec-kit` (pinned at `f36634b`).
**Reviewer:** Independent read-only analysis against attached Ranex architecture corpus.
**Date:** 2026-07-30
**Scope:** All Spec Kit surfaces: constitution, specify, clarify, plan, tasks, checklist, analyze, implement, converge, taskstoissues, artifact evolution, integrations, extensions, presets, workflows, bundles, catalog/provenance, greenfield/brownfield use.

---

## 1. Verdict on Selective Adoption

**CONDITIONALLY ADOPT, with heavy modification.** Spec Kit is a well-structured prompt-and-template toolkit for AI-assisted development. It solves a real problem: bringing discipline to agent-driven coding through structured specification, planning, and task breakdown. However, its core mechanism — prompts read by the same agent they constrain — is precisely the failure mode Ranex was built to eliminate.

Ranex should not adopt Spec Kit's philosophy, architecture, or naming. It should selectively extract three utility patterns that fill genuine gaps, re-express them in Ranex-native semantics, and reject everything that would weaken its governance model.

The single most valuable contribution is the **workflow engine concept** (gated step sequences with human checkpoints), because Ranex currently defines its lifecycle declaratively in prose but has no executable sequencing primitive. The second is a **project/workspace initialization CLI**. The third is an **external issue-tracker output adapter**. Everything else either duplicates existing Ranex capability at lower rigor or directly conflicts with Ranex invariants.

---

## 2. ADOPT / MODIFY / REJECT / DEFER Matrix

### ADOPT (Ranex-native re-expression, not file copy)

| Pattern | Evidence (Spec Kit) | Ranex Fit | User Value | Implementation Effort | Governance/Security Risk |
|---|---|---|---|---|---|
| **Workflow engine primitive** (gated step sequences, human checkpoints, conditions) | `workflows.md`: `specify workflow run`, YAML-defined steps with `gate`/`command`/`if`/`switch`/`while`/`fan-out`/`fan-in` types, pause/resume, overlay composition | Fills a real gap: Ranex's Core SDLC defines stages declaratively in prose (CORE_SDLC_OPERATING_MODEL.md §3) and the AI lifecycle defines L0-L12 activities (AI_AGENT_DEVELOPMENT_LIFECYCLE.md §5), but no executable sequencing primitive exists. The workflow engine is the runtime projection of the state machine. | Operators and owners can compose governed pipelines (specify→review-gate→plan→review-gate→implement) without implementing the full transition service first. Enables SDLC-ADOPT-B/C tracers. | Medium. Requires a new `pipeline_execution` or `workflow_engine` bounded context with its own state machine, gate evaluator integration, and step-type adapters. Must be deterministic and evidence-bound. | Low if implemented as a deterministic projection of accepted ADR semantics. Risk: model-authored workflow steps must not carry authority. Every `command` step must resolve to an exact `TaskPacket`; every `gate` step must produce a typed `GateEvaluation`. |
| **Project initialization CLI** (`ranex init`) | `README.md`: `specify init my-project --integration copilot`, automatic directory structure, template resolution, `.specify/` scaffolding | Ranex has generator/validator scripts (`scripts/architecture/generate_contracts.py`, `validate_contracts.py`) but no project bootstrap command. A `ranex init` that creates the canonical directory layout, copies templates, and runs an initial contract generation would reduce friction. | Lowers the barrier to starting a governed Ranex workspace. Currently requires manual directory creation and script invocation. | Small. Wraps existing generator script with a project-scaffolding layer. | Very low. Initialization is read-only with respect to governance; it creates files, not authority. |
| **External issue-tracker output adapter** (`taskstoissues` equivalent) | `taskstoissues.md`: deduplicates against existing GitHub issues, creates issues with `T001: <description>` titles, MCP-based | Ranex has no bridge from governed work items to external tracking systems. The Core SDLC's `work_management` context owns `WorkItemStatus`; an output adapter that projects work items to GitHub issues (or other trackers) as read-only views is a legitimate adapter pattern. | Teams that already use GitHub Issues or Jira can keep their existing tracking while Ranex governs the real work state. The external issue is a projection, never authority. | Small. Read-only projection from `work_management` queries to external API. | Medium. Must guarantee that an external issue mutation never feeds back into Ranex authority. The adapter must be one-way (Ranex → external). An external issue close must not transition `WorkItemStatus`. |

### MODIFY (Adopt the concept, re-express with Ranex semantics)

| Pattern | Evidence (Spec Kit) | Ranex Fit | What Changes | User Value | Implementation Effort | Governance/Security Risk |
|---|---|---|---|---|---|---|
| **Extension/Preset architecture** (pluggable commands, template overrides, catalog discovery, priority stacking) | `extensions.md`, `presets.md`: command registration, template resolution stack (project overrides → presets → extensions → core), priority-based composition, catalog search/install | Ranex has a sophisticated adapter architecture (ports, HOST_EDGE_ADAPTER exceptions, bounded contexts) but no user-facing package/catalog system for third-party contributions. The concept of discoverable, versioned, composable extensions is valuable for an ecosystem. | Must use Ranex-native authority model: extensions are registered `context` additions with exact ADR authority, not prompt files. Catalog entries must carry content digests and provenance. Template resolution must be deterministic and digest-bound. Priority stacking must be explicit, not implicit. | Enables community contributions of governed worker profiles, runtime adapters, checkers, and practice profiles without forking the core. | Large. Requires a new `extension_registry` context, catalog infrastructure, deterministic composition rules, and integration with the existing adapter architecture. | High if extensions can carry authority. Must enforce: (1) extensions cannot redefine `governed_execution`, `policy`, `assurance`, or `identity_access` semantics; (2) all extension commands must resolve through `CapabilityBus`; (3) catalog entries require content digests and provenance manifests. |
| **Checklist concept as pre-contract validation** ("unit tests for English") | `checklist.md`: requirements quality validation items (completeness, clarity, consistency, measurability, coverage), prohibition on implementation-testing items | Ranex already requires machine-readable contracts and deterministic verification. However, there is a gap between a human's natural-language intent and the machine contract. A structured ambiguity-detection pass before contract compilation could reduce downstream rework. | Must NOT be a prompt-based checklist that an agent self-grades. Instead: a deterministic lint pass over requirements prose that flags undefined terms, missing measurable criteria, unbound references, and ambiguous adjectives. Output is a structured finding list, not a checkbox file. | Catches spec defects before they become machine contracts, reducing the cost of downstream invalidation. | Small-Medium. A linter with a defined rule set, not an LLM call. | Very low. Deterministic, read-only, no authority. |
| **Artifact evolution models** (flow-forward, living, flow-back) | `evolving-specs.md`: three evolution strategies with explicit workflows for each | Ranex's Source of Truth policy (§11) covers change and supersession. The Core SDLC state machine covers discovery→definition→design iteration. However, the three evolution models provide useful conceptual framing for how a feature's artifact set relates to its implementation over time. | Formalize as three registered compatibility classes under the existing change policy, not as new workflow primitives. "Flow-forward" maps to `SUPERSEDED` with retained history. "Living" maps to in-place revision with digest change. "Flow-back" maps to implementation-driven requirements update with explicit reconciliation gate. | Gives owners and workers a shared vocabulary for how a feature directory should evolve. | Small. Documentation + registry entries only. | Very low. These are classification labels, not new authority. |
| **Constitution phase-gate pattern** (pre-implementation gates that check architectural principles before work proceeds) | `plan-template.md` §"Phase -1: Pre-Implementation Gates", `spec-driven.md` §"Constitutional Enforcement Through Templates": simplicity gate, anti-abstraction gate, integration-first gate | Ranex's architecture fitness tests and MAP-* assertions serve a similar purpose but are post-hoc. A pre-flight gate that checks a task packet against registered architectural constraints before dispatch is a useful addition. | Express as a new `AI-G*` gate or `SDLC-*` control that runs before `IN_PROGRESS`. The gate checks: allowed paths, allowed dependency edges, bounded context ownership, engineering practice applicability, and risk-lane artifacts. It is deterministic and evidence-bound, not a prompt checklist. | Catches architecture violations before an agent starts work, reducing wasted cycles and review burden. | Medium. Requires integration with the packet compiler and the existing architecture registries (context-dependency-edges.json, paths.json, topology-rules.json). | Low. Deterministic check against registered contracts. |

### REJECT (Conflicts with Ranex invariants)

| Pattern | Evidence (Spec Kit) | Why Rejected | Ranex Invariant Violated |
|---|---|---|---|
| **Constitution as prompt-based governing document** | `constitution-template.md`: template with `[PRINCIPLE_N_NAME]` placeholders, filled by LLM, read by agent at runtime as `/memory/constitution.md` | Ranex's founding premise: "Rules an agent can read are suggestions. Rules compiled into code are constraints." (README.md §"The bet"). Treating a constitution as a prompt file the agent reads is the anti-pattern Ranex was built to reject. | "An agent never reads an enforced rule" (README.md). "AI agents are bounded workers; model output is advisory" (SOURCE_OF_TRUTH.md §Authority rule). |
| **Specifications as source of truth that generate code** | `spec-driven.md` §"The Power Inversion": "Specifications don't serve code—code serves specifications." "Specifications become executable, directly generating working implementations." | Ranex inverts this: architecture documents + machine contracts are the source of truth. Specifications inform work but do not generate code. The Core SDLC, not a spec, governs how work moves from need to outcome. | "The accepted Core SDLC governs how work moves from need to operated outcome. The full-system architecture and ADRs govern what Ranex is and where authority lives. Machine contracts are executable projections of both and cannot semantically override either." (SOURCE_OF_TRUTH.md §Authority rule). |
| **Template-driven quality with model self-grading** | `specify.md`: agent fills template, then self-validates against checklist items, self-corrects | Ranex requires independent review (AI_AGENT_DEVELOPMENT_LIFECYCLE.md §3, §5.7). No self-approval. The identity that produces work cannot validate it. | "No self-approval: The identity that produces work cannot approve it." (README.md). "Reviewer did not edit the subject" (AI_AGENT_DEVELOPMENT_LIFECYCLE.md §3). |
| **Model-driven ambiguity resolution without evidence bound** | `clarify.md`: agent asks user up to 5 clarification questions, integrates answers | Ranex requires unknowns to be labeled and evidence-bound (L1 Research). The clarification pattern itself is fine, but spec-kit's implementation puts the model in the position of deciding what's ambiguous and what's resolved — without evidence. | "Every material claim is labeled: FACT, INFERENCE, PROPOSAL, UNKNOWN, or OWNER_REQUIREMENT." (AI_AGENT_DEVELOPMENT_LIFECYCLE.md §5.2). "Absence blocks: NOT_ASSESSED is never a pass." (README.md). |
| **Library-first principle (Article I)** | `spec-driven.md` §"Article I: Library-First Principle": "Every feature MUST begin as a standalone library." | Conflicts with Ranex's bounded-context architecture. Not every feature is a library; some are domain logic within a context, some are cross-cutting concerns, some are infrastructure. | "The only canonical bounded-context path is `src/ranex/<context>/`." (SOURCE_OF_TRUTH.md §Authority rule). |
| **CLI interface mandate for all features (Article II)** | `spec-driven.md` §"Article II: CLI Interface Mandate": "Every library MUST expose functionality through CLI. Text in/out protocol." | Overly prescriptive for Ranex's 34 bounded contexts. Some contexts are internal domain logic, event consumers, or policy engines. Forcing CLI interfaces everywhere would create unnecessary adapters. | Architecture must be "a full-system specification, not an MVP or prototype map" (docs/architecture/README.md §Scope rule). Forcing one interface pattern on all contexts contradicts the domain-driven design. |
| **Integration-as-prompt-files model** | `integrations.md`: 30+ agent integrations install command files into agent-specific directories (`.claude/commands/`, `.github/agents/`, etc.) | Ranex's worker fleet control plane uses exact typed assignments with route locks, not prompt files placed in agent directories. A worker receives a compiled `TaskPacket`, not a Markdown file with `$ARGUMENTS` substitution. | "Ranex control services alone create assignments and own cross-worker orchestration." (AI_AGENT_FLEET_CONTROL_PLANE.md §1). "The packet compiler, not a planner model, decides whether these facts are present." (AI_AGENT_FLEET_CONTROL_PLANE.md §6.1). |
| **Constitution articles as fixed 9-article structure** | `spec-driven.md` §"The Nine Articles of Development": Articles I-IX with prescribed content (Library-First, CLI, Test-First, etc.) | Ranex's governance is expressed through 13 accepted ADRs, the Core SDLC, the Source of Truth policy, and the control catalog — not a fixed-number template. Forcing a 9-article structure would constrain what Ranex governs and how. | ADR process requires RFC → review → human decision (SOURCE_OF_TRUTH.md §9). Prescribing a fixed article count would bypass this. |
| **Task list as flat markdown with `[P]` markers** | `tasks-template.md`: `- [ ] T001 [P] [US1] Description with file path` | Ranex's task packets (L3) are compiled deterministically with exact subject binding, engineering practice profiles, risk derivations, and grant compilation. A flat markdown checklist is not an executable authority artifact. | Task packets "bind exact context, grants, dependencies, engineering practice profiles." (AI_AGENT_DEVELOPMENT_LIFECYCLE.md §5.4). |
| **"Full permissions" as a tier or absent concept** | Spec Kit has no capability sandbox for shell steps; `workflows.md` explicitly notes: "There is no capability sandbox." | Ranex requires least-privilege workers with exact task-minimal grants. Every tool call passes through `CapabilityBus`. | "Default worker posture: ephemeral, least-privilege principal and session; deny-by-default filesystem, process, network, tool, model, and effect capabilities." (AI_AGENT_FLEET_CONTROL_PLANE.md §15.1). |
| **Greenfield "generate from scratch" philosophy** | `spec-driven.md` §"0-to-1 Development (Greenfield)": "Generate from scratch," "Build production-ready applications" from high-level requirements | Ranex operates on an existing architecture with exact bounded contexts, dependency edges, and state ownership. A "generate from scratch" mode that doesn't respect the full-system map would violate the full-map preservation rule. | "The implementation plan may select one route through the architecture, but it must retain the full destination map." (SOURCE_OF_TRUTH.md §10). |

### DEFER (Valuable but not now)

| Pattern | Evidence (Spec Kit) | Why Deferred | When to Revisit |
|---|---|---|---|
| **Bundle system** (curated stacks of extensions + presets + workflows for role-based setups) | `bundles.md`: `bundle.yml` manifests, catalog discovery, version pinning, install/update/remove lifecycle | Requires the extension/preset architecture first (MODIFY above). Premature without that foundation. | After extension registry context exists and ≥3 community extensions are published. |
| **Fan-out/fan-in workflow steps** (`fan-out` dispatch, `fan-in` aggregation) | `workflows.md` §"Step Types": `fan-out` dispatches a step for each item in a list, `fan-in` aggregates results | Ranex's fleet control plane already handles parallel dispatch with `PARTITIONED_WRITE` and `STAR_READ` topologies. Adding fan-out/fan-in to a workflow engine duplicates this. Useful only if the workflow engine becomes the primary sequencing primitive. | After workflow engine is adopted and the relationship between workflow fan-out and fleet topology is resolved. |
| **Community catalog infrastructure** (public extension/preset/workflow registries with search, install, verified badges) | `extensions.md`, `presets.md`, `workflows.md`: catalog stack with project/user/built-in scopes, `search`, `info`, `add`, trust indicators | Requires: (1) extension architecture, (2) at least one stable Ranex release, (3) a community. Premature. | Post-PRODUCTION_READY, when Ranex has users who want to share governed configurations. |
| **Learned orchestration/conductor** | `spec-driven.md` mentions AI-native development; Spec Kit allows model-driven workflows | Ranex already defers learned orchestration to R&D quarantine (AI_AGENT_FLEET_CONTROL_PLANE.md §14, SDLC-ADOPT-FLEET-F). Spec Kit offers no additional insight here. | As already mapped: after deterministic contracts, measurement harness, hidden anchors, and human acceptance exist. |
| **Brownfield "modernization" workflows** | `spec-driven.md` §"Iterative Enhancement (Brownfield)": "Modernize legacy systems," "Adapt processes" | Ranex's upstream Hermes sync (UPSTREAM_SYNC work class) and migration controls (ADR-0010) already handle inherited code. Spec Kit's brownfield concept is generic; Ranex's is precise and governed. | Only if Ranex ever needs to ingest non-Hermes legacy codebases. |

---

## 3. Smallest First End-to-End Slice

A single tracer that proves the adoption hypothesis without building infrastructure first:

**Slice: `ranex init` + governed `specify→plan→tasks→implement` pipeline using a workflow engine**

1. **`ranex init <project>`** — Creates the canonical directory layout (`src/ranex/`, `docs/architecture/`, `architecture/contracts/`, `schemas/`), copies templates, runs initial contract generation and validation. Output: a clean, governed workspace.

2. **Define one workflow YAML** — A Ranex-native workflow definition (not spec-kit's format) that chains four steps:
   - `specify`: Compiles a `WorkIntake` and `ResearchPacket` from a natural-language description
   - `gate: review-spec`: Human checkpoint — gate step that pauses for owner review
   - `plan`: Compiles an `ArchitectureReviewPacket` and `TaskPacket`
   - `gate: review-plan`: Human checkpoint
   - `tasks`: Generates governed task breakdown into `tasks.md` projection
   - `implement`: Dispatches one leaf worker with exact task-minimal grant

3. **Execute this pipeline for a trivial change** — e.g., "Add a `--version` flag to the `generate_contracts.py` script." This exercises the full governed path: intake → research → packet compilation → implementation → independent review → human landing.

4. **Prove the tracer** — The output is: one completed SDLC-ADOPT-B tracer (manual), one workflow engine primitive validated, one project init CLI validated. Zero new infrastructure beyond a workflow runner that is a deterministic projection of existing Core SDLC states.

This slice requires no extension architecture, no catalog, no bundle system. It exercises exactly the ADOPT and MODIFY items above. Estimated effort: 3-5 governed work items.

---

## 4. Patterns That Conflict with Ranex Invariants

These are structural incompatibilities, not mere differences in taste:

### 4.1 The Authority Inversion

**Spec Kit:** Specifications → generate code. Spec is primary artifact. Code is expression.

**Ranex:** Architecture → compile contracts → enforce → agents propose → gate evaluates → human decides. The architecture governs; code is the governed output.

**Conflict:** If Ranex adopts spec-kit's "specify generates implementation" philosophy, it breaks the gate between proposal and authorization. In Ranex, a spec is a proposal; in spec-kit, a spec is the source. Ranex cannot have two contradictory authority hierarchies.

### 4.2 Prompt-as-Control vs. Code-as-Control

**Spec Kit:** Constitution, templates, and checklists are Markdown files read by the agent. Quality is enforced by the agent self-checking against prose criteria.

**Ranex:** Rules are compiled into JSON Schemas, registries, and executable checks. The checker does not ask the agent anything. Quality is enforced by a deterministic validator that cannot be talked out of a verdict.

**Conflict:** These are mutually exclusive mechanisms. Ranex cannot both "compile rules into code" and "trust the agent to read a constitution." The latter is the failure mode Ranex's README explicitly cites as motivation.

### 4.3 Self-Approval

**Spec Kit:** The same agent that writes the spec also validates it against the checklist. The same agent that implements marks tasks complete. There is no structural separation between producer and reviewer.

**Ranex:** Independence contract requires separate execution identity, no subject editing, separate review packet, no write capability for reviewer. No self-approval.

**Conflict:** Spec Kit's workflow is fundamentally self-referential. Ranex would need to insert an independent review gate between every spec-kit step, which would transform it into something unrecognizable.

### 4.4 Artifact Fidelity

**Spec Kit:** Artifacts are Markdown files with prose. `[NEEDS CLARIFICATION]` markers are resolved by asking the user. `TODO` markers are acceptable. A spec is "complete" when a checklist passes.

**Ranex:** Artifacts are machine-validated JSON with RFC 8785 canonicalization and SHA-256 digests. `NOT_ASSESSED` is a blocking state. `UNKNOWN` is not a pass. A spec is "defined" only when it has exact subject binding, schema validation, and registered evidence.

**Conflict:** Spec Kit's artifact model is informal prose. Ranex's is formal contracts. Adopting spec-kit's artifact model would degrade Ranex's assurance guarantees. Adopting Ranex's artifact model would make spec-kit unrecognizable.

### 4.5 Worker Model

**Spec Kit:** The agent is a general-purpose coding assistant with access to the filesystem, shell, and network. There is no capability sandbox, no lease, no fencing, no governor. The agent can modify any file.

**Ranex:** Every worker is a leaf with an exact task-minimal grant, fenced lease, isolated worktree, and governor. Tool calls pass through `CapabilityBus`. Write scope is bounded by path contracts.

**Conflict:** Spec Kit's "full access" model is exactly what Ranex's fleet control plane prohibits. Adopting spec-kit's integrations would require wrapping every agent in a Ranex governor, which defeats the purpose of the lightweight integration.

---

## 5. Commercial-Value Hypotheses (Separated from Facts)

These are hypotheses, not architectural conclusions. They require market validation.

| Hypothesis | Confidence | Validation Required |
|---|---|---|
| **H1: A workflow engine with human gates will accelerate adoption of governed development** by making the Core SDLC tangible to operators who currently see it as documentation. | Medium | Test: Time-to-first-tracer with vs. without workflow engine. Measure: number of governed work items completed in first 30 days. |
| **H2: A CLI (`ranex init`, `ranex generate`, `ranex validate`) will lower the barrier to entry** enough to convert architecture-curious visitors into users. | Medium | Test: Abandonment rate at each step of the current "Verify it yourself" flow (README.md). Measure: successful `ranex init` → `ranex validate` completions. |
| **H3: An extension ecosystem will create network effects** where third-party runtime adapters, checkers, and worker profiles compound the value of the core. | Low (requires critical mass first) | Test: Developer survey on willingness to publish governed extensions. Measure: extension count, not GitHub stars. |
| **H4: An external issue-tracker bridge will reduce friction for teams that already use GitHub Issues/Jira**, making Ranex compatible with existing workflows rather than requiring replacement. | Medium-High | Test: Teams with existing issue trackers report reduced context-switching when Ranex projects work items to their tracker. |
| **H5: Spec-kit's template-driven approach to requirements will improve the quality of Ranex work intake** by catching ambiguities before they become machine contracts. | Low-Medium | Test: A/B comparison of work items created with vs. without a pre-contract ambiguity linter. Measure: downstream invalidation rate, rework cycles. |

**Fact:** Ranex currently has zero product code, zero runtime enforcement, and neither readiness tier declared. (README.md §"Current state"). Any commercial-value hypothesis is subordinate to the fact that the product does not yet exist at runtime.

---

## 6. Unresolved Questions and Required RFC/ADR Decisions

### 6.1 Questions Requiring Owner Decision

| # | Question | Why It Matters | Blocked Work |
|---|---|---|---|
| Q1 | Should Ranex have a user-facing CLI at all, or is it purely a library/engine embedded in other tools? | Determines whether `ranex init`, `ranex workflow run`, etc. are built or whether Ranex is always invoked programmatically. | ADOPT items (CLI, workflow engine UX). |
| Q2 | Should the workflow engine be a new bounded context (`pipeline_execution`) or a capability of the existing `governed_execution` context? | Affects ownership, dependency edges, and the atomic authority boundary. `governed_execution` already owns `RunStatus`, gate binding, grants, and permits. | Workflow engine implementation. |
| Q3 | Should the workflow engine use a YAML/JSON DSL (like spec-kit's `workflow.yml`) or a programmatic API? | A DSL enables composition by non-programmers but requires a parser, validator, and schema. A programmatic API is more flexible but less accessible. | Workflow engine design. |
| Q4 | Should extension contributions require an accepted ADR per extension, or can they be registered under a general extension policy? | Per-extension ADRs provide maximum governance but create friction. A general policy risks extensions that weaken invariants. | Extension architecture design. |
| Q5 | Is the "pre-contract ambiguity linter" a gate (`AI-G*`) or a non-blocking advisory tool? | If it's a gate, it blocks work intake. If advisory, it may be ignored. | Requirements lint implementation. |
| Q6 | Should Ranex ever adopt Spec Kit's "specification as executable artifact" philosophy for any work class (e.g., PRODUCT), or is that philosophy permanently rejected? | If PRODUCT-class work can use lighter-weight spec-driven development while CRITICAL/SECURITY work requires full architecture governance, Ranex needs a tiered process. Currently, all work classes go through the same Core SDLC. | Core SDLC tailoring rules. |

### 6.2 Decisions Requiring Formal RFC/ADR

| RFC/ADR Topic | Scope | Why RFC/ADR Required |
|---|---|---|
| **ADR-0014: Adopt a workflow execution engine as a projection of the Core SDLC state machine** | New bounded context or capability of `governed_execution`. Defines: step types, gate integration, human checkpoint protocol, pause/resume semantics, overlay/composition rules. | Changes the execution subprocess. Affects `governed_execution` atomic boundary. Requires compatibility proof with existing AI lifecycle (L0-L12). |
| **ADR-0015: Establish a project initialization and CLI tooling policy** | Defines the `ranex` CLI surface, project scaffolding contract, template resolution rules, and relationship to generated contracts. | Creates a new user-facing surface. Must define which operations require authentication, which are read-only, and how the CLI relates to the existing `scripts/architecture/` tools. |
| **ADR-0016: Define an extension and third-party contribution governance model** | Defines how external code enters the Ranex ecosystem: registration, catalog discovery, provenance requirements, authority boundaries, compatibility guarantees, and revocation. | Introduces untrusted code into a governed system. Must prevent extensions from weakening invariants (no self-approval, no prompt-as-control, no authority bypass). |
| **ADR-0017: Establish an external-system projection adapter policy** | Defines read-only output adapters (GitHub Issues, Jira, linear, etc.) and their one-way authority boundary. | Must guarantee that external system mutations never feed back into Ranex authority. Defines the projection schema, freshness rules, and reconciliation when external state diverges. |
| **RFC-001: Explore whether Ranex should adopt a tiered process model** | Investigates whether PRODUCT-class work can use lighter-weight governance while CRITICAL/SECURITY work retains full architecture governance. Evaluates risks of process fragmentation. | This is a strategic product decision that affects every work class. It should be explored as an RFC before becoming an ADR. |

### 6.3 Open Technical Questions (Do Not Block Adoption, But Need Answers)

1. How does a workflow engine's `gate` step produce a `GateEvaluation`? Does it reuse the existing `assurance` gate evaluator, or does it have its own evaluation logic?
2. If a workflow is defined in YAML, how is its digest computed? The workflow definition is itself an artifact that must be subject-bound.
3. Can a workflow step dispatch a worker (creating an `AgentAssignment`), or are workflow steps always local/Ranex-service operations?
4. How does workflow pause/resume interact with lease expiry? If a workflow pauses at a human gate for 3 days, the underlying lease expires. On resume, is it the same `RunId` or a new one?
5. Should the `ranex` CLI be implemented in Python (matching the existing scripts) or in Rust/Go (for performance and distribution as a single binary)?

---

## Summary

Ranex should adopt **three utility patterns** from spec-kit (workflow engine, project init CLI, external issue tracker bridge), **modify four concepts** (extensions, pre-contract linting, artifact evolution models, pre-flight architecture gates), **reject ten patterns** that conflict with core invariants, and **defer five patterns** that depend on not-yet-built infrastructure.

The critical principle: **nothing adopted from spec-kit may introduce prompt-based governance, self-approval, or unbound artifacts.** Every adaptation must be re-expressed in Ranex-native semantics: deterministic, evidence-bound, subject-pinned, and independently verifiable.

The smallest viable first step is a workflow engine that chains governed steps with human gates, exercised through a single end-to-end tracer. This requires one ADR (workflow engine), one RFC (tiered process model optional), and approximately 3-5 governed work items.
