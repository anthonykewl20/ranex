# Real-world software-development operating model research for Ranex

| Field | Value |
|---|---|
| Research ID | `RES-SDLC-001` |
| Date | 2026-07-27 |
| Status | Curated research and adopted evidence basis; not normative by itself |
| Owner | Human governor |
| Subject | The end-to-end process by which Ranex work moves from an idea to an operated and improved product |
| Ranex revision inspected | Working tree based on `fee61eb61d8f2df2f28adbe3a59cf8c2340ab5f4` |
| Upstream | [NousResearch/hermes-agent](https://github.com/nousresearch/hermes-agent) |
| Companion normative policy | [Ranex Core SDLC Operating Model](../architecture/CORE_SDLC_OPERATING_MODEL.md) |
| Owner decision | [ADR-0001: Established Software-Development Lifecycle Governs AI Work](../architecture/decisions/ADR-0001-established-sdlc-governs-ai-work.md) |
| File mutations | This research report, its companion policy/control catalog, and documentation links |

## Executive recommendation

Ranex should adopt one product-to-production operating model as its core
development process:

```text
govern
  -> shape
  -> discover
  -> specify
  -> design
  -> plan
  -> build
  -> verify
  -> release
  -> operate
  -> learn
  -> govern again
```

This is a continuous value stream, not a waterfall. A small, reversible change
may move through several stages in hours; a security-, data-, architecture-, or
migration-sensitive change requires deeper artifacts and independent gates.
Every change uses the same state model and traceability chain. Risk controls the
depth of work, never whether essential work is visible.

The existing
[AI-Agent Development Lifecycle](../architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md)
is strong from qualified intake through implementation, review, landing, and
operations evidence. It should remain the execution protocol inside the broader
SDLC, not serve as the whole product lifecycle. The missing outer loop is the
human-world product practice:

- deciding which problem is worth solving;
- learning from users before committing to a solution;
- expressing outcomes, requirements, constraints, and service expectations;
- making product, engineering, security, operations, and release readiness
  explicit;
- observing whether the shipped change produced the intended outcome; and
- feeding evidence back into priorities, architecture, and working methods.

The core invariant is:

> Every production behavior must trace backward to an owned need and forward to
> verification and operational evidence.

## 1. Research question

How can Ranex apply a practical, real-world software-development process,
engineering playbook, and SDLC operating model from idea through requirements,
design, implementation, verification, release, operation, and improvement,
while remaining:

- a governed fork of Hermes Agent;
- suitable for human and AI-agent collaboration;
- proportionate for changes of different risk;
- secure and auditable without becoming ceremony-heavy;
- compatible with frequent, small, reversible delivery; and
- capable of improving itself from evidence without allowing models to grant
  themselves authority?

## 2. Method and limitations

### 2.1 Local evidence

The research reconciles these Ranex documents:

- `RANEX_IMPLEMENTATION_GUIDE.md`;
- `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md`;
- `docs/architecture/SOURCE_OF_TRUTH.md`;
- `docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md`;
- `docs/research/gemini-research.md`;
- `docs/research/hermes-core-architecture-research-2026-07-27.md`; and
- `docs/research/hermes-core-architecture-hy3-review-2026-07-27.md`;
- `docs/research/cookbook-alignment-research-2026-07-27.md`; and
- `docs/research/ocask-alignment-research-2026-07-27.md`.

The local architecture already establishes exact-subject evidence, human
authority, machine contracts, isolated implementation, independent review,
deterministic gates, release/rollback, operations, and upstream synchronization.
This report does not replace those controls. It supplies the product and
engineering value stream around them.

### 2.2 External evidence

Primary and official sources were preferred:

- [ISO/IEC/IEEE 12207:2017](https://www.iso.org/standard/63712.html)
  for the complete software-life-cycle process frame and process-improvement
  attachment points;
- [SWEBOK Guide V4.0a](https://www.computer.org/education/bodies-of-knowledge/software-engineering)
  for consensus-driven software-engineering knowledge areas spanning
  requirements, architecture, construction, testing, operations, maintenance,
  configuration, management, process, quality, security, and economics;
- [ISO/IEC 29110-5-1-2:2025](https://www.iso.org/standard/82669.html)
  for a small-team process spine consisting of project management and software
  implementation;
- [NASA Software Engineering Handbook, NASA-HDBK-2203](https://standards.nasa.gov/standard/NASA/NASA-HDBK-2203)
  for detailed engineering, assurance, configuration, traceability,
  verification/validation, delivery, and record practices;
- [NIST Secure Software Development Framework (SSDF)](https://csrc.nist.gov/projects/ssdf)
  for organization preparation, software protection, secure production, and
  vulnerability response;
- [NIST SP 800-218](https://doi.org/10.6028/NIST.SP.800-218) for secure
  development practices across an SDLC;
- [DORA software-delivery performance metrics](https://dora.dev/guides/dora-metrics/)
  for delivery throughput and instability measures;
- [DORA capability catalog](https://dora.dev/capabilities/) for small batches,
  WIP limits, CI/CD, test automation, security, observability, and visible
  value-stream work;
- [DORA guidance for generative AI in software delivery](https://dora.dev/guides/how-to-innovate-with-generative-ai/)
  for treating AI as a change to delivery capability whose effect is measured
  against the existing delivery system;
- [Google Engineering Practices](https://google.github.io/eng-practices/review/)
  for small changes and code-review responsibilities;
- [Google SRE Workbook: Canarying Releases](https://sre.google/workbook/canarying-releases/)
  for progressive exposure and release evaluation;
- [Google SRE Workbook: Error Budget Policy](https://sre.google/workbook/error-budget-policy/)
  for balancing reliability and change;
- [Google SRE Workbook: Postmortem Culture](https://sre.google/workbook/postmortem-culture/)
  for learning from incidents;
- [The Scrum Guide](https://scrumguides.org/scrum-guide.html) for empirical,
  iterative inspection and adaptation; and
- [Agile Manifesto principles](https://agilemanifesto.org/principles.html) for
  frequent delivery, feedback, technical excellence, and adapting to change;
  and
- [CMMI capability and maturity levels](https://cmmiinstitute.com/learning/appraisals/levels)
  for assessing whether processes are managed, defined, measured, and improved.

These sources support practices, not a branded framework Ranex must copy.

### 2.3 Source appraisal and adopted use

No source is universal scientific proof. The selected synthesis is:

> Ranex uses ISO/IEC/IEEE 12207 and SWEBOK as the full lifecycle and engineering
> knowledge map; tailors ISO/IEC 29110's two-process Basic-profile structure as
> its small-team execution spine; enriches it with NASA assurance/record
> discipline and NIST SSDF security outcomes; calibrates delivery and
> reliability using DORA and Google evidence; and uses CMMI only to test whether
> the process is governed, enabled, measured, and improved.

| Source | Authority/evidence type | Adopted use | Limitation |
|---|---|---|---|
| ISO/IEC/IEEE 12207:2017 | International consensus standard | Full software-life-cycle process map and process-improvement frame | Process descriptions require tailoring; no conformity claim |
| SWEBOK V4.0a | IEEE consensus-driven body of knowledge | Coverage check for the complete software-engineering discipline | Knowledge map, not a prescriptive project lifecycle |
| ISO/IEC 29110-5-1-2:2025 | International consensus standard | Project management plus software-implementation spine | Official scope is one product/one team in a very small entity and excludes safety-critical software; no conformity claim |
| NASA-HDBK-2203 | Active government technical handbook and high-assurance practitioner guidance | Assurance, traceability, V&V, configuration and delivery control library | Guidance, not a NASA-mandatory standard; down-tailored for ordinary Ranex work |
| NIST SP 800-218 | Federal recommendation synthesized from secure-development practices | Security preparation, protection, secure production and vulnerability-response overlay | Not a complete lifecycle or certification |
| DORA | Repeated large-scale observational research | Small batches, flow, CI/CD capabilities and delivery measures | Association, not controlled universal causation; context matters |
| Google Engineering Practices/SRE | Mature practitioner guidance and cases | Change/review, SLO, release, incident and learning practices | Organization-derived and must be adapted |
| CMMI | Capability/maturity model plus organizational case evidence | Process institutionalization and improvement audit lens | Not a daily SDLC; no appraisal, compliance or maturity-level claim |
| Scrum/Agile | Consensus and practitioner principles | Iteration, inspection, adaptation and feedback | Not a complete assurance/operations model |

### 2.4 Limitations

- Ranex runtime implementation does not yet exist, so this is a target operating
  model rather than evidence of process performance.
- Team size, release cadence, user population, and service-level objectives are
  not yet empirically established.
- Current Hermes upstream behavior was already pinned and analyzed by the
  architecture research; this report does not repeat that source audit.
- Numeric thresholds in the companion policy are initial defaults. They require
  calibration from Ranex delivery and operational data.
- ISO/IEC 29110 is copyrighted and most detail is paywalled. Ranex uses its
  official scope and an independently authored structure; an authorized copy is
  required before claiming detailed clause coverage.
- Evidence strength varies. Consensus standards, government/practitioner
  guidance, observational association, case evidence, and Ranex owner decisions
  are deliberately not described as interchangeable or “proven.”

## 3. Findings

### 3.1 A lifecycle is not a queue of specialist handoffs

Real software work is uncertain. Requirements, design, implementation, and
operation expose information that can invalidate earlier assumptions. A process
that permits only forward movement creates hidden rework; one that permits
unrecorded backtracking loses control.

Ranex therefore needs explicit feedback transitions:

```text
discovery <-> specification <-> design <-> implementation
                         verification -> any earlier state
release/operation -> incident, problem, experiment, or improvement intake
```

A backward transition creates a reason, owner, and changed artifact. It does not
erase history.

### 3.2 Product outcomes and engineering outputs need separate tests

A feature can be correctly built and still fail to help users. Ranex should
separate:

- **product validation:** is this a worthwhile problem and did the change
  improve the intended outcome?
- **engineering verification:** does the implementation satisfy its specified
  behavior and quality constraints?

Both must be represented in the work item before commitment. Product outcome
evidence may arrive after release; engineering evidence must be sufficient
before release.

### 3.3 One process needs proportional assurance lanes

A typo and a credential-boundary migration should not carry the same ceremony.
Allowing teams to invent a process per change, however, makes evidence
incomparable and invites bypasses.

Use one state machine with four risk lanes:

| Lane | Typical change | Required assurance |
|---|---|---|
| Standard | Documentation, isolated low-risk correction | Peer review, relevant deterministic checks, reversible landing |
| Enhanced | User-visible feature, dependency, persistent state | Full requirements/design, independent review, broader tests, release and rollback plan |
| Critical | Auth, secrets, policy, data loss, migration, authority, supply chain | Threat model, ADR, specialist and adversarial review, recovery proof, explicit human release authority |
| Emergency | Active incident or exploited vulnerability | Time-boxed exception, two-person authorization where possible, smallest mitigation, retrospective full evidence |

Risk is derived from facts and policy. A maker cannot choose a lower lane.

### 3.4 Small batches and continuous integration improve control

The safest unit is a thin, independently verifiable change tied to one outcome.
Long-lived branches, broad rewrites, and combined migrations/features expand the
uncertainty surface. Ranex should optimize for:

- short-lived isolated worktrees;
- one bounded change and one reviewable subject;
- trunk-compatible integration;
- always-releasable main;
- feature exposure separated from binary deployment when practical; and
- migrations that expand, migrate, verify, then contract.

### 3.5 “Done” has multiple boundaries

Teams commonly call work done when code is merged. That omits release,
operability, outcome measurement, cleanup, and learning. Ranex needs distinct
definitions:

| Boundary | Meaning |
|---|---|
| Ready | The item is safe and clear enough to enter committed delivery |
| Built | Code/config/docs and developer tests are complete |
| Verified | The exact candidate satisfies its acceptance and quality evidence |
| Released | The approved artifact is deployed/installed with rollback available |
| Operated | Health, support, recovery, and ownership are proven for the observation window |
| Outcome reviewed | Product and operational results were compared with the hypothesis |
| Closed | Evidence, follow-ups, documentation, and decisions are reconciled |

### 3.6 Security, reliability, and operations belong inside the stream

NIST SSDF groups preparation, protection, production, and vulnerability
response across the lifecycle. Google SRE practices make reliability targets,
safe rollout, incident response, and learning part of engineering rather than a
post-development department. Ranex should therefore reject a “build, then hand
to security/operations” model.

For every material change:

- security requirements and misuse cases are requirements;
- observability and support are design concerns;
- rollback and recovery are implementation concerns;
- deployment evaluation is verification;
- incidents and vulnerabilities return to normal governed intake; and
- postmortem actions compete visibly with feature work.

### 3.7 Metrics must describe the system, not rank people

DORA’s current delivery measures provide a useful system view:

- change lead time;
- deployment frequency;
- failed deployment recovery time;
- change fail rate; and
- deployment rework rate.

Ranex also needs flow, quality, reliability, security, and product measures.
None should be used to score individuals or reward output volume. That creates
gaming, larger hidden batches, weak tests, and suppressed incidents.

### 3.8 A fork needs a second change stream

Ranex has product work and upstream intake. Upstream commits are untrusted change
candidates, not automatic updates. Each must be pinned, classified, provenance
checked, mapped to Ranex bounded contexts, selectively ported, and passed
through the same verification and release controls. This is a specialization of
the core SDLC, not an informal maintenance chore.

### 3.9 AI agents change execution capacity, not accountability

Agents can research, refine requirements, propose designs, implement, test,
review, and summarize evidence. They do not own product outcomes, accept risk,
waive missing evidence, or authorize merge/release. The stable system is the
artifact/state/evidence chain. Model conversation is ephemeral working material.

### 3.10 The process needs institutional controls

The initial lifecycle synthesis was directionally complete but not executable
enough. ISO/IEC 29110 and NASA guidance expose missing cross-cutting controls:

- a project-management loop of plan, execute, assess/control and close;
- estimate ranges, forecasts, dependencies, risk reserves and reforecast
  authority;
- bidirectional requirements/design/code/test/finding traceability;
- configuration-item identification, baselines, status accounting and audits;
- verification separated from validation and user/product acceptance;
- supplier/dependency adoption, monitoring, shared responsibility and exit;
- competence, process assurance, nonconformance and corrective action; and
- controlled maintenance and retirement.

These are now specified in the
[SDLC Control Catalog](../architecture/SDLC_CONTROL_CATALOG.md).

### 3.11 Fork-specific reconciliation is mandatory

Fleet inspection found several contradictions that must be resolved before the
operating model is implemented:

1. `RANEX_IMPLEMENTATION_GUIDE.md` currently uses a second “canonical” work
   vocabulary and closes work at merge. `POL-SDLC-001` must become authoritative;
   `RESEARCHED`, `PLAN_APPROVED`, `REVIEWED`, `TESTED`,
   `CUSTOMER_VALIDATED`, and `APPROVED_FOR_MERGE` should become evidence/gate
   milestones. `MERGED` is a landing event, not `CLOSED`.
2. The guide's proposed authoritative office plugin and separate office
   database conflict with the accepted `src/ranex` core and single authority
   transaction boundary. A plugin may be a transitional
   projection/compatibility adapter, never the final authority owner.
3. Every inherited Hermes surface needs a disposition ledger:
   `RETAIN_AS_IS | WRAP | EXTRACT | REIMPLEMENT | REMOVE | QUARANTINE | DEFER`,
   bound to upstream commit/path/symbol/behavior, owner, compatibility test,
   legal/commercial class, expiry/removal trigger and replacement work.
4. Upstream sync needs one specialized lifecycle:
   `OBSERVED -> FETCHED -> PINNED -> CLASSIFIED -> DISPOSITIONED ->
   PORTING -> PORT_CANDIDATE -> VERIFIED -> RELEASED -> BASELINE_RECORDED`,
   with `REJECTED`, `DEFERRED`, `BLOCKED` and `ROLLED_BACK` branches.
5. Releases must promote immutable approved artifacts. The inherited Hermes
   source-pull/update/reset behavior is not a Ranex rollback model; source reset
   does not reverse data/schema or external effects.
6. Compatibility needs `SUPPORTED -> DEPRECATED -> READ_ONLY -> REMOVED` for
   the legacy CLI, home/config/session/tool names, plugins and providers.
7. Plugins, providers, MCP/catalog entries and model routes need
   `DISCOVERED -> QUARANTINED -> REVIEWED -> QUALIFIED -> PINNED -> ENABLED ->
   SUSPENDED | RETIRED`. Mutable Git installs/updates, optional manifests,
   last-writer-wins provider overrides, environment-presence auto-selection and
   import-time authority registration are forbidden in target mode.
8. Operational cutover needs
   `BOOTSTRAP -> LEGACY_BASELINE -> TRANSITIONAL_DUAL_RUN -> TARGET_SHADOW ->
   TARGET_LIMITED -> TARGET_DEFAULT -> LEGACY_FROZEN -> LEGACY_REMOVED`, with
   exactly one canonical writer in every mode.
9. Self-development must use an immutable controller release to govern the next
   candidate (`N` controls `N+1`) through release, operation and outcome review.
   A merged documentation tracer proves only the manual adoption gate.

Required fork artifacts are a phase-to-SDLC migration matrix, exact-subject
invalidation graph, inherited-behavior disposition ledger, and compatibility
matrix across upstream baseline, Ranex release, state schema, platform,
plugin protocol and provider catalog.

Primary upstream evidence includes the current
[Hermes CLI command reference](https://github.com/nousresearch/hermes-agent/blob/main/website/docs/reference/cli-commands.md),
[update procedure](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/getting-started/updating.md),
[provider-plugin guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/model-provider-plugin.md),
and [provider-layer guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/developer-guide/adding-providers.md).

## 4. Selected operating model

### 4.1 The three nested loops

```text
Outcome loop (weeks/months)
  govern -> shape -> discover -> outcome review

Delivery loop (hours/weeks)
  specify -> design -> plan -> build -> verify -> release

Reliability loop (continuous)
  observe -> respond -> recover -> learn -> improve
```

The loops share one work-item identity and one traceability graph. Planning
cadences do not replace continuous intake; operational work does not wait for a
sprint boundary.

### 4.2 Canonical flow

| State | Primary question | Minimum output | Exit authority |
|---|---|---|---|
| Funnel | Is the signal recorded? | Idea/problem/incident/vulnerability record | Intake owner |
| Triage | Is it ours and how urgent/risky is it? | Classification, owner, severity, risk lane | Product/duty owner |
| Discovery | Is the problem real and worth solving? | Evidence, users, current behavior, hypothesis | Product owner |
| Definition | What must be true? | Outcome, requirements, constraints, acceptance examples, measures | Product + engineering + affected owner |
| Design | How can it be changed safely? | Design record, threat/ops/data impact, test and rollout strategy | Technical owner; ADR authority if material |
| Ready | Can we responsibly commit? | Sized vertical slices, dependencies, capacity and evidence plan | Delivery owner |
| In progress | Is one bounded subject being built? | Task packet, code/tests/docs, run evidence | Implementation protocol |
| Verification | Does the exact subject meet the contract? | Review and deterministic evidence | Qualified gates + human decision where required |
| Release ready | Can this artifact safely reach users? | Signed/pinned artifact, runbook, rollback, comms, approvals | Release authority |
| Releasing | Is progressive exposure healthy? | Deployment events and evaluation evidence | Release operator under permit |
| Operating | Is it healthy and supported? | Telemetry, SLO/support/security evidence | Service owner |
| Outcome review | Did it help, and what changed? | Results vs hypothesis; keep/change/remove decision | Product owner |
| Closed | Is the evidence and follow-up complete? | Reconciled record and owned follow-ups | Work owner |

Maintenance, incident, release/update, compatibility, extension, operational
mode, and retirement statuses belong to linked lifecycles with their own
namespaces. They create or link canonical work items through typed events; they
are not additional `WorkItemStatus` values.

### 4.3 Minimum traceability chain

```text
signal/problem
  -> desired outcome and measure
  -> requirement + acceptance example
  -> design decision + risk controls
  -> delivery slice + exact commit
  -> test/review/security evidence
  -> release artifact + deployment
  -> telemetry/support/outcome evidence
  -> learning or follow-up
```

Every link is queryable. A document may be concise, but no link may exist only
in a chat transcript.

### 4.4 Full-spec Mermaid diagram

This diagram is the complete operating-model view. The thick center is the
normal value stream. Dashed arrows are evidence, governance, or feedback
relationships. A failed gate returns the work to the earliest state whose
assumption is no longer valid; it never changes failure into pass.

```mermaid
flowchart TB
  %% ---------- Inputs ----------
  subgraph INPUTS["Signals entering Ranex"]
    direction LR
    USER["User or stakeholder need"]
    OPS_SIGNAL["Defect, incident, SLO, or support signal"]
    SEC_SIGNAL["Security, privacy, or compliance signal"]
    STRATEGY["Strategy, architecture, debt, or improvement"]
    HERMES["Pinned Hermes upstream change"]
  end

  %% ---------- Main lifecycle ----------
  subgraph VALUE["One canonical work-item lifecycle"]
    direction TB

    subgraph SHAPE["Shape the right work"]
      direction LR
      FUNNEL["FUNNEL<br/>Record the signal"]
      TRIAGE["TRIAGE<br/>Own, classify, prioritize"]
      DISCOVERY["DISCOVERY<br/>Prove the problem"]
      DEFINITION["DEFINITION<br/>Define outcome and requirements"]
      FUNNEL --> TRIAGE --> DISCOVERY --> DEFINITION
    end

    subgraph DELIVER["Design and deliver safely"]
      direction LR
      DESIGN["DESIGN<br/>Choose boundaries and controls"]
      READY["READY<br/>Commit a feasible vertical slice"]
      BUILD["IN_PROGRESS<br/>Build in an isolated worktree"]
      VERIFY["VERIFICATION<br/>Independent review, V&V, and gates"]
      RELEASE_READY["RELEASE_READY<br/>Immutable artifact and rollback"]
      RELEASING["RELEASING<br/>Stage, migrate, expose, observe"]
      DESIGN --> READY --> BUILD --> VERIFY --> RELEASE_READY --> RELEASING
    end

    subgraph RUN["Run, learn, and close the work item"]
      direction LR
      OPERATING["OPERATING<br/>Own health, support, and recovery"]
      OUTCOME["OUTCOME_REVIEW<br/>Compare result with hypothesis"]
      CLOSED["CLOSED<br/>Reconcile evidence and follow-ups"]
      RELEASING --> OPERATING --> OUTCOME -->|outcome decision recorded| CLOSED
    end
  end

  USER --> FUNNEL
  OPS_SIGNAL --> TRIAGE
  SEC_SIGNAL --> TRIAGE
  STRATEGY --> FUNNEL
  DEFINITION --> DESIGN

  %% ---------- Rejection, feedback, and recovery ----------
  subgraph RECOVERY["Feedback, failure, and recovery"]
    direction LR
    ACTIVE_RULE["ROUTING RULE — NOT A STATE<br/>Any active WorkItemStatus"]
    BLOCKED["BLOCKED<br/>Owner + reason + next decision"]
    RESUME_RULE["ROUTING RULE — NOT A STATE<br/>Resume an allowed prior state or terminal disposition"]
    PRE_RELEASE_RULE["ROUTING RULE — NOT A STATE<br/>Any pre-release WorkItemStatus"]
    CANCELLED["CANCELLED<br/>Reason and durable history"]
    ROLLED_BACK["ROLLED_BACK<br/>Restore and reconcile"]
    INCIDENT["IncidentStatus: INCIDENT<br/>Command, mitigate, communicate"]
    RECOVERY_VERIFIED["IncidentStatus: RECOVERY_VERIFIED<br/>Health and state proven"]
    IMPROVEMENT["IMPROVEMENT_INTAKE<br/>Owned corrective work"]
    ACTIVE_RULE -->|dependency, conflict, or evidence gap| BLOCKED --> RESUME_RULE
    PRE_RELEASE_RULE -->|authorized cancellation| CANCELLED
    INCIDENT --> RECOVERY_VERIFIED --> IMPROVEMENT
  end

  TRIAGE -->|not valuable or not ours| CANCELLED
  DISCOVERY -->|evidence insufficient| FUNNEL
  DEFINITION -->|problem or requirement unclear| DISCOVERY
  DESIGN -->|need must change| DEFINITION
  READY -->|plan infeasible| DESIGN
  BUILD -->|blocked| BLOCKED
  VERIFY -->|implementation fails| BUILD
  VERIFY -->|design fails| DESIGN
  VERIFY -->|requirement fails| DEFINITION
  RELEASE_READY -->|not releasable| VERIFY
  RELEASING -->|health threshold breached| ROLLED_BACK
  ROLLED_BACK --> RECOVERY_VERIFIED
  ROLLED_BACK -->|user impact| INCIDENT
  ROLLED_BACK -->|safe prior state verified; new attempt linked| TRIAGE
  OPERATING -->|material impact| INCIDENT
  RETIRING -->|retirement fails| RECOVERY_VERIFIED
  RECOVERY_VERIFIED --> OPERATING
  IMPROVEMENT --> TRIAGE
  OUTCOME -->|hypothesis falsified| DISCOVERY
  OUTCOME -->|contract must change| DEFINITION

  %% ---------- Linked capability lifecycles ----------
  subgraph SERVICE_LIFECYCLES["Linked service lifecycles — separate status namespaces"]
    direction LR
    MAINT_TRIGGER["CapabilityStatus: MAINTENANCE TRIGGER<br/>defect · dependency · vulnerability · debt"]
    MAINT_WORK["LINKED MAINTENANCE WORK<br/>normal WorkItemStatus lifecycle"]
    RETIRE_READY["CapabilityStatus: RETIRE_READY<br/>consumer, data, access, and rollback plan"]
    RETIRING["CapabilityStatus: RETIRING<br/>migrate, revoke, archive, tear down"]
    RETIRED["CapabilityStatus: RETIRED<br/>audit absence and residual ownership"]
    MAINT_TRIGGER --> MAINT_WORK
    RETIRE_READY --> RETIRING --> RETIRED
  end

  OPERATING -.-> MAINT_TRIGGER
  MAINT_WORK -.-> TRIAGE
  OUTCOME -.->|remove decision| RETIRE_READY
  RETIRING -->|retirement failure| RECOVERY_VERIFIED
  RETIRED -.-> CLOSED

  %% ---------- Risk and decision authority ----------
  subgraph AUTHORITY["Assurance and decision authority"]
    direction LR
    RISK["Derived risk lane<br/>STANDARD · ENHANCED · CRITICAL · EMERGENCY"]
    MODELS["Humans and AI agents<br/>research, propose, make, review"]
    CHECKERS["Qualified deterministic gates<br/>check exact-subject evidence"]
    OWNERS["Named human owners<br/>accept value, architecture, and risk"]
    PERMIT["Single-use exact-subject permit<br/>authorizes landing/release/effect"]
    RISK --> CHECKERS
    MODELS --> CHECKERS
    CHECKERS --> OWNERS --> PERMIT
  end

  RISK -.-> TRIAGE
  RISK -.-> DESIGN
  RISK -.-> VERIFY
  CHECKERS -.-> VERIFY
  OWNERS -.-> DEFINITION
  OWNERS -.-> DESIGN
  PERMIT -.-> RELEASING

  %% ---------- Cross-lifecycle controls ----------
  subgraph CONTROLS["Controls that travel with every work item"]
    direction LR
    PM["PM<br/>Plan · execute · assess/control · close"]
    TRACE["Traceability<br/>Need ↔ requirement ↔ design ↔ code ↔ proof"]
    CM["Configuration<br/>Baselines · status · reproducibility · audits"]
    VV["V&V<br/>Verify specification · validate intended use"]
    SSDF["Security<br/>Prepare · protect · produce · respond"]
    SUPPLIER["Suppliers<br/>Adopt · monitor · accept · replace/exit"]
    DEBT["Debt and tailoring<br/>Owner · trigger · expiry · controls"]
    MEASURE["Measurement<br/>Outcome · flow · stability · quality"]
    ASSURE["Process assurance<br/>Competence · audit · improve"]
  end

  PM -.-> READY
  TRACE -.-> DEFINITION
  TRACE -.-> VERIFY
  CM -.-> RELEASE_READY
  VV -.-> VERIFY
  SSDF -.-> DESIGN
  SSDF -.-> OPERATING
  SUPPLIER -.-> DESIGN
  SUPPLIER -.-> MAINT_WORK
  DEBT -.-> TRIAGE
  MEASURE -.-> OUTCOME
  ASSURE -.-> CLOSED

  %% ---------- Durable evidence chain ----------
  subgraph EVIDENCE["One durable traceability and evidence chain"]
    direction LR
    E_SIGNAL["Signal / problem"]
    E_OUTCOME["Outcome + measure"]
    E_REQ["Requirement + example"]
    E_DESIGN["Decision + risk controls"]
    E_SUBJECT["Task packet + exact commit"]
    E_PROOF["Review + test + security evidence"]
    E_RELEASE["Artifact + manifest + deployment"]
    E_OPERATION["Health + support + outcome"]
    E_LEARNING["Learning + follow-up"]
    E_SIGNAL --> E_OUTCOME --> E_REQ --> E_DESIGN --> E_SUBJECT
    E_SUBJECT --> E_PROOF --> E_RELEASE --> E_OPERATION --> E_LEARNING
  end

  FUNNEL -.-> E_SIGNAL
  DEFINITION -.-> E_REQ
  DESIGN -.-> E_DESIGN
  BUILD -.-> E_SUBJECT
  VERIFY -.-> E_PROOF
  RELEASING -.-> E_RELEASE
  OUTCOME -.-> E_OPERATION
  CLOSED -.-> E_LEARNING

  %% ---------- Hermes fork specialization ----------
  subgraph FORK["Hermes-to-Ranex fork lane"]
    direction TB
    subgraph UPSYNC["Upstream synchronization"]
      direction LR
      U_OBS["OBSERVED"] --> U_FETCH["FETCHED"] --> U_PIN["PINNED"]
      U_PIN --> U_CLASS["CLASSIFIED"] --> U_DISP["DISPOSITIONED"]
      U_DISP -->|port planned| U_PORT["PORTING"] --> U_CAND["PORT CANDIDATE"]
      U_CAND --> U_VERIFY["VERIFIED"] --> U_RELEASE["RELEASED"]
      U_RELEASE --> U_BASE["BASELINE RECORDED"]
      U_DISP -->|reject| U_REJECT["REJECTED"]
      U_DISP -->|not scheduled| U_DEFER["DEFERRED"]
    end

    subgraph LEGACY["Inherited behavior and compatibility"]
      direction LR
      DISPOSITION["Behavior disposition<br/>retain · wrap · extract · reimplement<br/>remove · quarantine · defer"]
      SUPPORTED["SUPPORTED"] --> DEPRECATED["DEPRECATED"]
      DEPRECATED --> READ_ONLY["READ ONLY"] --> REMOVED["REMOVED"]
      DISPOSITION -.-> SUPPORTED
    end

    subgraph EXTENSIONS["Plugins, providers, MCP, and routes"]
      direction LR
      X_DISC["DISCOVERED"] --> X_QUAR["QUARANTINED"] --> X_REVIEW["REVIEWED"]
      X_REVIEW --> X_QUAL["QUALIFIED"] --> X_PIN["PINNED"] --> X_ENABLE["ENABLED"]
      X_ENABLE --> X_SUSPEND["SUSPENDED / RETIRED"]
    end

    subgraph CUTOVER["One-writer operational cutover"]
      direction LR
      C_BOOT["BOOTSTRAP"] --> C_BASE["LEGACY BASELINE"] --> C_DUAL["TRANSITIONAL DUAL RUN"]
      C_DUAL --> C_SHADOW["TARGET SHADOW"] --> C_LIMITED["TARGET LIMITED"]
      C_LIMITED --> C_DEFAULT["TARGET DEFAULT"] --> C_FROZEN["LEGACY FROZEN"]
      C_FROZEN --> C_REMOVED["LEGACY REMOVED"]
    end

    subgraph UPDATE["Release/update lifecycle — source reset is not rollback"]
      direction LR
      UP_CHECK["CHECKED"] --> UP_DOWNLOAD["DOWNLOADED"] --> UP_VERIFIED["VERIFIED"]
      UP_VERIFIED --> UP_SNAPSHOT["SNAPSHOTTED"] --> UP_STAGE["STAGED"]
      UP_STAGE --> UP_MIGRATE["MIGRATED"] --> UP_ACTIVATE["ACTIVATED"]
      UP_ACTIVATE --> UP_HEALTH["HEALTH_VERIFIED"] --> UP_COMPLETE["COMPLETED"]
      UP_STAGE -->|post-snapshot failure| UP_ROLLBACK["ROLLED_BACK"]
      UP_MIGRATE -->|failure| UP_ROLLBACK
      UP_ACTIVATE -->|failure| UP_ROLLBACK
      UP_HEALTH -->|failure| UP_ROLLBACK
      UP_ROLLBACK --> UP_RECOVERY["RECOVERY_VERIFIED"]
    end
  end

  HERMES --> U_OBS
  U_DISP -.-> DISPOSITION
  U_CAND -.-> DESIGN
  U_RELEASE -.-> RELEASE_READY
  X_ENABLE -.-> SUPPLIER
  C_DEFAULT -.-> OPERATING

  %% ---------- Safe self-development ----------
  subgraph SELFDEV["Safe Ranex self-development"]
    direction LR
    RELEASE_N["Immutable controller<br/>Ranex release N"]
    GOVERN_N1["governs work on"]
    CANDIDATE_N1["Candidate<br/>Ranex release N+1"]
    HUMAN_RELEASE["Independent human release permit"]
    OBSERVE_N1["Rollback drill + post-release observation"]
    RELEASE_N --> GOVERN_N1 --> CANDIDATE_N1 --> HUMAN_RELEASE --> OBSERVE_N1
  end

  OPERATING -.-> RELEASE_N
  CANDIDATE_N1 -.-> BUILD
  HUMAN_RELEASE -.-> RELEASING
  OBSERVE_N1 -.-> OUTCOME

  %% ---------- Text-and-line-style legend ----------
  subgraph LEGEND["Legend — labels and line styles carry meaning; color is secondary"]
    direction LR
    LEG_STATE["WorkItemStatus<br/>solid border"]
    LEG_GATE["Gate / permit<br/>gold solid border"]
    LEG_RISK["Failure / risk<br/>red solid border"]
    LEG_LINKED["Linked lifecycle<br/>dashed purple border"]
    LEG_EVIDENCE["Evidence<br/>green solid border"]
    LEG_TERMINAL["Terminal / disposition<br/>gray solid border"]
    LEG_SOLID["solid arrow = lifecycle transition"]
    LEG_DASH["dashed arrow = evidence, guard, or typed-event link"]
  end

  classDef state fill:#e8f1ff,stroke:#2457a7,color:#10254a,stroke-width:1.5px;
  classDef gate fill:#fff4cf,stroke:#9b6b00,color:#4d3500,stroke-width:1.5px;
  classDef risk fill:#ffe8e8,stroke:#a83232,color:#4f1717,stroke-width:1.5px;
  classDef evidence fill:#e8f8ef,stroke:#247247,color:#123d27,stroke-width:1.5px;
  classDef fork fill:#f3eaff,stroke:#6941a5,color:#321d56,stroke-width:1.5px;
  classDef linked fill:#faf6ff,stroke:#6941a5,color:#321d56,stroke-width:2px,stroke-dasharray:6 4;
  classDef terminal fill:#eef0f3,stroke:#4f5965,color:#222831,stroke-width:1.5px;

  class FUNNEL,TRIAGE,DISCOVERY,DEFINITION,DESIGN,READY,BUILD,OPERATING,OUTCOME state;
  class VERIFY,RELEASE_READY,RELEASING,CHECKERS,OWNERS,PERMIT gate;
  class RISK,BLOCKED,ROLLED_BACK risk;
  class INCIDENT,RECOVERY_VERIFIED,IMPROVEMENT,MAINT_TRIGGER,MAINT_WORK,RETIRE_READY,RETIRING,RETIRED linked;
  class E_SIGNAL,E_OUTCOME,E_REQ,E_DESIGN,E_SUBJECT,E_PROOF,E_RELEASE,E_OPERATION,E_LEARNING evidence;
  class U_OBS,U_FETCH,U_PIN,U_CLASS,U_DISP,U_PORT,U_CAND,U_VERIFY,U_RELEASE,U_BASE,DISPOSITION,SUPPORTED,DEPRECATED,READ_ONLY,X_DISC,X_QUAR,X_REVIEW,X_QUAL,X_PIN,X_ENABLE,C_BOOT,C_BASE,C_DUAL,C_SHADOW,C_LIMITED,C_DEFAULT,C_FROZEN,UP_CHECK,UP_DOWNLOAD,UP_VERIFIED,UP_SNAPSHOT,UP_STAGE,UP_MIGRATE,UP_ACTIVATE,UP_HEALTH,UP_COMPLETE,UP_ROLLBACK,UP_RECOVERY fork;
  class CLOSED,CANCELLED,U_REJECT,U_DEFER,REMOVED,X_SUSPEND,C_REMOVED terminal;
```

### 4.5 Full-spec ASCII diagram

The same model in a terminal-safe form:

```text
 SIGNALS
 user need        incident/SLO        security/privacy       strategy/debt
     \                 |                    |                     /
      +----------------+--------------------+--------------------+
                               |
                               v
 +---------+   +--------+   +-----------+   +------------+
 | FUNNEL  |-->| TRIAGE |-->| DISCOVERY |-->| DEFINITION |
 | record  |   | own +  |   | prove the |   | outcome +  |
 | signal  |   | classify|  | problem   |   | requirement|
 +---------+   +--------+   +-----------+   +------------+
     ^                            | bad evidence     | unclear need
     +----------------------------+<-----------------+
                                                     |
                                                     v
 +--------+   +-------+   +-------------+   +--------------+   +---------------+
 | DESIGN |-->| READY |-->| IN_PROGRESS |-->| VERIFICATION |-->| RELEASE_READY |
 | safe   |   | commit|   | build one   |   | review + V&V |   | immutable     |
 | choice |   | slice |   | exact change|   | + exact gates|   | artifact      |
 +--------+   +-------+   +-------------+   +--------------+   +---------------+
     ^            |              ^            |    |    |             |
     | infeasible-+              +--code fail-+    |    |             |
     +-----------------------------design fail-----+    |             |
     +-----------------------requirement fail-----------+             |
     |                                                                v
     |                                                        +---------------+
     |                                                        | RELEASING     |
     |                                                        | stage/migrate |
     |                                                        | expose/observe|
     |                                                        +---------------+
     |                                                           |         |
     |                                                     healthy|         |threshold fail
     |                                                           v         v
     |                                                     +-----------+  +-------------+
     +------------------------------------------------------ | OPERATING |  | ROLLED_BACK |
                                                            | own health|  | restore +   |
                                                            +-----------+  | reconcile   |
                                                                           +-------------+
                                                                  |             |
                                                                  v             v
                                                           +----------------+  +------------------+
                                                           | OUTCOME_REVIEW |  | RECOVERY_VERIFIED|
                                                           | did it help?   |  +------------------+
                                                           +----------------+          |
                                                              |        |               |
                                                      goal met|        |false          |
                                                              v        v               |
                                                         +--------+  DISCOVERY <--------+
                                                         | CLOSED |
                                                         +--------+

 INCIDENT LOOP
   OPERATING / ROLLED_BACK / FAILED RETIREMENT
          -> INCIDENT -> MITIGATE -> RECOVERY_VERIFIED
          -> IMPROVEMENT_INTAKE -> TRIAGE

 CANONICAL RE-ENTRY
   ROLLED_BACK --safe prior state verified; linked new attempt--> TRIAGE
   OUTCOME_REVIEW --learn more--> DISCOVERY
   OUTCOME_REVIEW --change the contract--> DEFINITION
   any active WorkItemStatus --recorded blocker--> BLOCKED
   any pre-release WorkItemStatus --authorized reason--> CANCELLED

 LINKED SERVICE LIFECYCLES (separate status namespaces)
   maintenance trigger (defect/dependency/vulnerability/debt)
      -> linked maintenance work item -> TRIAGE -> normal lifecycle

   OUTCOME_REVIEW --remove decision--> RETIRE_READY -> RETIRING -> RETIRED
                                         |                |
                                         +--failure------> RECOVERY VERIFIED
   RETIRED --verified residual owner and evidence--> CLOSED

 ASSURANCE DEPTH                    DECISION SEPARATION
   STANDARD                         humans + agents: propose and make
   ENHANCED        --drives-->      qualified gates: verify exact evidence
   CRITICAL                         named humans: accept value/architecture/risk
   EMERGENCY                        permit: authorizes one exact effect

 CONTROLS TRAVEL WITH THE WORK
   [PM: plan/execute/control/close] [need <-> requirement <-> design <-> code <-> proof]
   [configuration baselines/audits] [verification + validation] [NIST SSDF security]
   [supplier/dependency governance] [debt + tailoring] [metrics] [process assurance]

 DURABLE EVIDENCE CHAIN
   signal -> outcome -> requirement -> design/risk -> task/exact commit
          -> review/test/security proof -> artifact/deployment
          -> health/support/outcome -> learning/follow-up

 HERMES FORK LANE
   upstream:
     OBSERVED -> FETCHED -> PINNED -> CLASSIFIED -> DISPOSITIONED
       -> REJECTED | DEFERRED | PORTING -> PORT CANDIDATE
       -> VERIFIED -> RELEASED -> BASELINE RECORDED

   inherited behavior:
     RETAIN | WRAP | EXTRACT | REIMPLEMENT | REMOVE | QUARANTINE | DEFER
     SUPPORTED -> DEPRECATED -> READ ONLY -> REMOVED

   plugins/providers/MCP/routes:
     DISCOVERED -> QUARANTINED -> REVIEWED -> QUALIFIED
       -> PINNED -> ENABLED -> SUSPENDED / RETIRED

   one-writer cutover:
     BOOTSTRAP -> LEGACY BASELINE -> TRANSITIONAL DUAL RUN -> TARGET SHADOW
       -> TARGET LIMITED -> TARGET DEFAULT -> LEGACY FROZEN -> LEGACY REMOVED

   immutable release/update:
     CHECKED -> DOWNLOADED -> VERIFIED -> SNAPSHOTTED -> STAGED -> MIGRATED
       -> ACTIVATED -> HEALTH_VERIFIED -> COMPLETED
     any post-snapshot failure -> ROLLED_BACK -> RECOVERY_VERIFIED
     source reset is not product rollback

 SAFE SELF-DEVELOPMENT
   immutable Ranex release N
      --governs--> candidate N+1
      --independent human permit--> release
      --rollback drill + observation--> outcome review
```

### 4.6 How to read both diagrams

- Follow the center line for normal delivery.
- Follow arrows pointing backward when evidence changes an earlier assumption.
- Treat the red/recovery path as normal controlled behavior, not process
  failure to hide.
- The control and evidence rails apply to every state even where a line is not
  drawn to avoid an unreadable graph.
- Canonical enum names use underscores. Short natural-language text beneath
  them is explanatory, not a second state vocabulary.
- Linked incident, maintenance, retirement, update, compatibility, extension,
  and cutover nodes use separate namespaces and communicate through typed
  events or linked work. They are not extra `WorkItemStatus` values.
- The policy is `ACCEPTED`; implementation maturity remains `R_AND_D` until
  adoption gates `SDLC-ADOPT-A` through `SDLC-ADOPT-E` pass. The diagram is a
  target specification, not proof that Ranex implements it today.
- `MERGED` is intentionally absent as a lifecycle state. It is one authorized
  landing event between verification and release readiness.
- “Dual run” in the fork lane never permits dual authority: exactly one
  canonical writer exists in every operating mode.
- The HTML companion presents the same model with shorter wording:
  [Ranex SDLC Visual Guide](./ranex-sdlc-visual-guide.html).

## 5. Roles and accountabilities

One person may hold several roles in a small project, but conflicting authority
must remain separated for enhanced and critical changes.

| Role | Accountable for |
|---|---|
| Human governor | Product direction, policy, architecture/risk acceptance, critical permits |
| Product owner | Problem selection, user outcome, ordering, outcome review |
| Technical owner | System design, engineering quality, maintainability, technical risk |
| Service owner | Operability, SLOs, incidents, recovery, support readiness |
| Security/data owner | Security/privacy requirements, threat and data decisions |
| Delivery owner | Flow, dependency/risk visibility, readiness and closure hygiene |
| Maker | Bounded implementation and truthful evidence |
| Independent reviewer | Fresh evaluation of the exact subject |
| Release operator | Authorized rollout, observation, halt, rollback |
| Incident commander | Incident coordination and recovery priorities |

`Product owner` decides value; `technical owner` decides engineering fitness;
`service owner` decides operational fitness; deterministic controls decide
machine-verifiable conformance; the human governor owns exceptions and critical
risk. No single model fills all five.

## 6. Required artifacts by change class

Artifacts should be fields in a connected work record, not necessarily separate
long documents.

| Artifact | Standard | Enhanced | Critical |
|---|:---:|:---:|:---:|
| Problem/outcome statement | ✓ | ✓ | ✓ |
| Acceptance examples | ✓ | ✓ | ✓ |
| Risk classification | ✓ | ✓ | ✓ |
| Research/discovery evidence | as needed | ✓ | ✓ |
| Architecture/design record | note | ✓ | ✓ + ADR |
| Threat/data review | if affected | if affected | ✓ |
| Test strategy | focused | ✓ | ✓ + adversarial/recovery |
| Observability/SLO impact | if affected | ✓ | ✓ |
| Migration and rollback | if affected | ✓ | ✓ + rehearsal |
| Independent review | peer | ✓ | multiple/specialist |
| Release plan | simple | ✓ | ✓ + progressive gates |
| Outcome review | sampled | ✓ | ✓ |

## 7. Cadence

Cadence supplies regular decisions without forcing work into artificial batches.

| Cadence | Purpose |
|---|---|
| Continuous | Intake, incident/security response, CI, review, release evidence |
| Daily or per active session | Flow check: blockers, aging work, WIP, operational health |
| Weekly | Replenishment/commitment, dependency and risk review, upstream intake |
| Per release | Readiness, deployment evaluation, rollback decision |
| Fortnightly or monthly | Product outcome review, architecture debt, security/reliability posture |
| Quarterly | Strategy, roadmap, SLO/error budget, capacity allocation, process health |
| Per incident | Response, recovery, learning review and action tracking |

The process needs decisions, not mandatory meetings. An asynchronous,
schema-valid record may satisfy a cadence.

## 8. Metrics and guardrails

Use a balanced dashboard:

| Dimension | Measures |
|---|---|
| Outcome | Adoption, task success, user-reported value, hypothesis result |
| Flow | End-to-end idea lead time, committed lead time, cycle time, WIP, work age, blocked time |
| Delivery | Deployment frequency, change lead time |
| Stability | Change fail rate, deployment rework rate, failed deployment recovery time |
| Quality | Escaped defects, reopen rate, flaky checks, rollback rate |
| Reliability | SLI/SLO attainment, error-budget consumption, incident recurrence |
| Security | Vulnerability age by severity, remediation time, provenance failures, exception age |
| Process | Gate wait time, evidence completeness, review latency, exception rate |
| Fork health | Upstream lag, candidate aging, rejected/reworked ports, sync regression rate |

Guardrails:

- measure teams/value streams and services, not individual productivity;
- pair speed with quality/stability and outcome;
- publish definitions and derive measures from event timestamps;
- never use story points as productivity;
- investigate trends and distributions rather than rewarding a target number;
- include unsuccessful work and rollbacks; and
- review whether a metric is changing behavior in harmful ways.

## 9. Alternatives rejected

### 9.1 Pure waterfall

Rejected as the default because it delays feedback and treats requirements as
stable. Sequential assurance may still be required for a regulated or
irreversible change, but feedback and traceability remain active.

### 9.2 Scrum as the complete operating model

Scrum is useful for empirical planning and review but does not specify
architecture governance, secure development, release engineering, incident
management, SLOs, supply chain, or fork synchronization. Ranex may use its
events selectively; sprints are not the core state machine.

### 9.3 Ticket-to-code automation

Rejected because a ticket rarely proves that the problem, requirement, design,
security posture, operability, or outcome is understood. Automated execution
begins only from a qualified packet.

### 9.4 Merge equals done

Rejected because users receive released and operated behavior, not commits.

### 9.5 One heavyweight template for every change

Rejected because it encourages performative paperwork and bypasses. The same
states and controls apply with risk-proportionate artifact depth.

### 9.6 Model consensus as a gate

Rejected because correlated model opinions are not empirical proof or human
authority.

## 10. Application to the Hermes-to-Ranex fork

The model changes how the fork is rebuilt:

1. Treat each architecture tracer as a product hypothesis and vertical slice,
   not as a horizontal framework layer.
2. Maintain separate queues for product outcomes, platform/architecture work,
   reliability/security work, and upstream candidates; order them in one
   portfolio using explicit capacity policy.
3. Map inherited Hermes behavior to an owned requirement, compatibility
   obligation, migration decision, or explicit rejection.
4. Never copy an upstream change directly into the product branch. Create an
   upstream candidate with exact commit, license/provenance evidence, behavioral
   impact, bounded-context mapping, and a selective-port decision.
5. Require a deployable vertical slice to contain code, tests, security,
   observability, migration, rollback, operator guidance, and outcome measures
   in proportion to risk.
6. Use the existing AI-agent lifecycle for packet compilation through
   post-landing evidence.
7. Do not activate Ranex self-development until its workflow can prove the same
   separation of maker, reviewer, gate, permit, and human authority demanded of
   external work.

## 11. Adoption plan

### Phase A — Declare and model

- Accept the companion core policy.
- Add canonical work-item states, transition events, risk lanes, artifact
  schemas, reason codes, and responsibility rules to the contract registries.
- Map the implementation guide phases into the new states without renumbering
  or losing history.

### Phase B — Prove on documentation and one tracer

- Run one documentation change and one thin runtime tracer end to end.
- Capture timestamps, evidence gaps, blocked transitions, review findings, and
  operator burden.
- Test backward transitions and invalidation when requirements or exact subject
  change.

### Phase C — Automate controls

- Generate packets and traceability views from canonical records.
- Automate state transition validation, CI evidence ingestion, review subject
  binding, release manifests, and post-release observation.
- Keep product, technical, service, security, and human risk decisions explicit.

### Phase D — Operate and calibrate

- Establish initial SLIs/SLOs and error-budget policy after real baselines exist.
- Review flow and stability monthly.
- Tune thresholds by accepted policy change, never by silent workflow edits.
- Retire redundant legacy process prose only after compatibility mapping.

## 12. Acceptance tests for the operating model

The model is ready to become Ranex’s executable process only when:

1. one work item can be traced from signal through operated outcome;
2. each transition rejects a missing owner, subject, required artifact, or gate;
3. standard, enhanced, critical, and emergency lanes exercise different
   assurance depth without different state semantics;
4. a changed requirement invalidates affected downstream evidence;
5. a changed commit invalidates exact-subject review and verification;
6. release can halt or roll back from predeclared health criteria;
7. an incident produces normal governed improvement work without rewriting its
   record;
8. an upstream candidate cannot bypass provenance, architecture, compatibility,
   and release gates;
9. a model cannot approve its own output, lower risk, issue a permit, or close
   missing evidence; and
10. the dashboard can derive flow and stability measures from event evidence
    without manual storytelling.

## 13. Final decision

**OWNER REQUIREMENT:** The product-to-production lifecycle described here is the
core process for building, releasing, operating, and improving Ranex.

**RECOMMENDATION:** Accept and implement the companion
[Ranex Core SDLC Operating Model](../architecture/CORE_SDLC_OPERATING_MODEL.md)
as the normative policy. Keep the AI-agent lifecycle as its governed execution
subprocess, the source-of-truth policy as its authority system, and the
full-system architecture as its product map.
