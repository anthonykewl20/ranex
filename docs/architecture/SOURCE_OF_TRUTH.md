# Ranex Source of Truth and Decision Policy

| Field | Value |
|---|---|
| Status | Normative supporting policy |
| Owner | Human governor |
| Applies to | Architecture, implementation, AI-agent work, review, release, and operations |
| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Parent architecture | [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Owner decision | [ADR-0001: Established Software-Development Lifecycle Governs AI Work](./decisions/ADR-0001-established-sdlc-governs-ai-work.md) |

## 1. Purpose

Ranex will be built by multiple AI agents, models, tools, and humans across many
sessions. Stable development therefore cannot depend on a model remembering the
project or deciding which document “looks current.”

This policy defines:

- which artifact is authoritative for each kind of decision;
- how evidence differs from authority;
- how conflicts block work;
- how architecture changes are proposed and accepted;
- which documents an agent must receive;
- which material is generated from machine contracts; and
- how a full-system map remains intact while implementation proceeds in slices.

## 2. Two separate hierarchies

Authority and empirical truth are not the same hierarchy.

### 2.1 Scoped normative authority

Human decision is the highest accountable authority, but the remaining sources
govern different subjects rather than forming a misleading total ordering:

| Authority source | Governing scope | Cannot do |
|---|---|---|
| Authenticated human decision and accepted ADR | Exact product, architecture, risk, policy, release, or effect decision | Rewrite empirical evidence or bypass exact-subject rules |
| [Core SDLC](./CORE_SDLC_OPERATING_MODEL.md) and [control catalog](./SDLC_CONTROL_CATALOG.md) | Product-to-production process, work-item lifecycle, roles, assurance, traceability, release/operate/improve semantics | Define target package ownership or claim a runtime fact |
| Full-system architecture and accepted architecture ADRs | Product boundaries, bounded contexts, source layout, state/effect ownership, dependencies, trust and migration | Redefine the core SDLC or claim implementation proof |
| Active policy/instruction package | Risk derivation, authorization and required controls within the accepted SDLC and architecture | Relax a higher owner requirement or manufacture evidence |
| Machine-validated contract registry | Exact executable IDs, enums, schemas, mappings and compatibility projections of accepted policy/architecture | Semantically override its normative source; mismatch is `CONFLICT` |
| Exact task packet | Narrow, exact work authorization compiled from all sources above | Expand scope or create new process/architecture authority |
| Run result, handoff and implementation note | What a worker did, observed or proposes | Approve, waive, transition, merge, release, or close |

Within each scope, a narrower/lower artifact cannot override its source. Where
scopes intersect, the registered mapping must satisfy both. An unresolved
process-versus-architecture or prose-versus-contract mismatch is `CONFLICT` and
blocks progression.

### 2.2 Empirical evidence hierarchy

From strongest to weakest for a claim about the current system:

1. exact-revision executable source and reproduced runtime behavior;
2. exact-version deterministic test output and inspectable artifacts;
3. official specification or primary upstream source;
4. reproducible research tied to exact revisions;
5. advisory model review;
6. prose assertion without matching evidence.

An authoritative human may accept risk or choose a direction. That decision does
not turn weak empirical evidence into strong evidence.

## 3. Canonical artifact graph

```text
Human owner decisions
        |
        +--> Core SDLC + control catalog --------+
        |      work-item flow and decision roles |
        |                                        v
        +--> Full-system architecture + ADRs --> machine contract registries
                                                   |
                                                   v
                                      generated schemas/mappings/views
                                                   |
                                                   v
                                      exact task packet for one SDLC activity
                                                   |
                                                   v
                          bounded AI worker -> independent review -> gate evidence
                                                   |
                                     human decision/permit where required
                                                   |
                                                   v
                           landing -> release -> operate -> outcome/improvement
                                      (all remain Core-SDLC governed)
```

Research feeds RFCs and architecture review. It does not directly change a
runtime contract.

### 3.1 Relationship to `RANEX_IMPLEMENTATION_GUIDE.md`

The implementation guide remains a capability checklist, host/bootstrap
playbook, and source of operational requirements. It is not allowed to override
this full-system architecture with an older plugin-first layout, conflicting
role/state/path examples, or phase ordering that consumes a permit before the
gate/authority seam exists.

Until the guide is regenerated or amended:

- this architecture controls target ownership, boundaries, source layout,
  dependency direction, state, authority, evidence, effects, migration, and
  product exclusions;
- accepted ADRs and machine contracts control their exact executable
  vocabulary;
- the guide supplies applicable operational detail that does not conflict with
  those higher sources; and
- a conflict is recorded as `CONFLICT`, not resolved by choosing whichever
  document is easier for the current task.

## 4. Document classes

| Class | Purpose | May be normative? | Change mechanism |
|---|---|---:|---|
| Core SDLC policy/control | Product-to-production process, state, roles and assurance | Yes | Human-accepted superseding ADR and versioned migration |
| Architecture | Full target shape, ownership, boundaries, dependencies | Yes | RFC, independent review, human-accepted ADR |
| Machine contract | Exact IDs, enums, schemas, ownership, paths, lifecycles | Yes | Versioned contract change and compatibility proof |
| ADR | Accepted architecture decision and consequences | Yes | New superseding ADR; never rewrite history silently |
| RFC | Explores a decision and alternatives | No until accepted | Review and human decision |
| Policy/instruction | Active operational requirement | Yes within declared scope | Versioned activation and owner approval |
| Task packet | Exact bounded work contract | Yes for its run | Recompile on material input change |
| Research | Evidence, analysis, unknowns, recommendations | No | New immutable snapshot or explicit correction |
| Review | Advisory finding bound to an exact subject | No by itself | Resolution record or human decision |
| Run evidence | What occurred during one execution | Evidence | Append-only correction; no destructive rewrite |
| Generated view | Human-readable projection of canonical contracts | Derived | Regenerate; hand editing is prohibited |
| Runbook | Operator procedure | Normative only where linked by active policy | Tested revision and owner approval |

## 5. Canonical status vocabulary

Every normative or decision artifact carries one status:

| Status | Meaning |
|---|---|
| `OWNER_REQUIREMENT` | Fixed product direction; implementation still requires proof |
| `ACCEPTED` | Human-approved and currently normative |
| `CONDITIONALLY_ACCEPTED` | Target is accepted but named blocking validation remains |
| `PROPOSAL` | Candidate direction, not authority |
| `R_AND_D` | Attachment point is mapped; implementation choice requires an experiment |
| `UNKNOWN` | Evidence is insufficient |
| `CONFLICT` | Authoritative-looking inputs disagree; progression is blocked |
| `DEPRECATED` | Still understood for compatibility but no longer selected |
| `SUPERSEDED` | Replaced by a named newer artifact |
| `REJECTED` | Explicitly outside the selected direction |

“Deferred” is scheduling metadata, not an architecture status. A postponed
capability still needs a mapped final boundary or an explicit `REJECTED` product
decision.

## 6. Required metadata

Every normative artifact includes:

- stable ID and schema/version;
- title and artifact type;
- status;
- human owner;
- exact repository revision;
- effective date and review/expiry date when applicable;
- parent and source references;
- supersedes/superseded-by links;
- content digest;
- affected bounded contexts;
- compatibility and migration classification;
- security and data-classification impact; and
- approval or decision record.

Every research or review artifact additionally states:

- evidence corpus and exact revisions/digests;
- method;
- model/provider/transport identity if a model participated;
- limitations;
- file mutations, if any; and
- which claims are fact, inference, proposal, owner requirement, or unknown.

## 7. Machine contract registry

Before feature implementation, these registries become the executable source of
truth:

```text
architecture/contracts/
├── identities.yaml
├── states.yaml
├── roles.yaml
├── work-classes.yaml
├── risk-lanes.yaml
├── capabilities.yaml
├── module-graph.yaml
├── state-ownership.yaml
├── path-ownership.yaml
├── lifecycles.yaml
├── lifecycle-crosswalks.yaml
├── gate-namespaces.yaml
├── invalidation-graph.yaml
├── event-registry.yaml
├── authority-matrix.yaml
├── schema-compatibility.yaml
└── source-precedence.yaml
```

They resolve the previously documented conflicts:

1. `WorkItemStatus`, `RunStatus`, `IncidentStatus`, `ReleaseStatus`,
   `CapabilityStatus`, `WorkflowNodeId`, and derived `RuleStage` are different
   fields with one owner each.
2. Role IDs are domain-neutral and presentation aliases never grant authority.
3. repository configuration and `$RANEX_HOME` runtime state have one ownership
   map.
4. all writing work uses one validated worktree lifecycle.
5. gates and exact-subject decisions precede permit issuance and completion
   effects.
6. `governed_execution` owns the one atomic authority transaction.
7. profile schema creation and provider binding are separate idempotent
   operations.
8. internal run IDs are opaque strings; external numeric IDs are typed external
   references.
9. qualification uses predeclared, paired, repeated, holdout-based evidence and
   calibrated graders.
10. `STANDARD`, `ENHANCED`, `CRITICAL`, and `EMERGENCY` are registered risk
    lanes; the policy engine may raise but a worker cannot lower them.
11. `SDLC-*`, `AI-G*`, `MAP-*`, `SDLC-ADOPT-*`, runtime `GateOutcome`, and
    human decision points are distinct typed namespaces.
12. L0–L12 are worker-protocol activities mapped to the core SDLC; they are not
    a parallel work-item lifecycle.

Prose examples are generated from or validated against these registries. An
example cannot create a new state, role, path, or capability.

## 8. Source precedence and conflict behavior

For any packet or decision:

1. collect candidate sources;
2. bind their revision, digest, status, owner, and observation time;
3. apply the registered source-precedence rule;
4. evaluate freshness;
5. expose unresolved disagreement as `CONFLICT`;
6. expose missing required material as `UNKNOWN`;
7. block when the active policy marks the unknown/conflict as blocking; and
8. require a human decision or a corrected source.

Agents must not:

- choose the newest-looking file by filename alone;
- silently merge incompatible definitions;
- convert uncertainty into an assumption without recording it;
- treat the longest document as the strongest authority;
- infer current runtime behavior from a design proposal; or
- use a model vote to resolve a source conflict.

## 9. RFC and ADR workflow

Use an RFC when a decision is still being explored. Use an ADR to record the
accepted decision.

```text
RFC:
  DRAFT
    -> SPECIALIST_REVIEW
    -> INDEPENDENT_REVIEW
    -> OWNER_DECISION
    -> ACCEPTED | REJECTED | EXPIRED

ADR:
  PROPOSED -> ACCEPTED -> SUPERSEDED
```

An RFC/ADR is required for changes to:

- bounded contexts, ownership, or the full repository map;
- public internal APIs or dependency direction;
- canonical identity, state, events, evidence, gates, permits, or human
  decisions;
- the atomic transaction/outbox boundary;
- capability vocabulary or trust tiers;
- workflow semantics or workflow runtime;
- policy language or authorization behavior;
- isolation, secrets, authentication, or egress;
- persistence, artifact, backup, or retention models;
- provider/route identity or fallback authority;
- schema compatibility, migration, or destructive data change;
- compatibility/upstream-sync strategy;
- extension protocol;
- product inclusions or exclusions; or
- a new critical dependency.

Every ADR records alternatives, state/effect ownership, consequences, migration,
rollback, security, acceptance tests, evidence, remaining unknowns, owner, and
review date.

Code may not silently diverge from an accepted ADR. Discovery of a required
divergence stops the task and opens a replacement RFC.

## 10. Full-map preservation rule

The implementation plan may select one route through the architecture, but it
must retain the full destination map.

Every task packet names:

- bounded contexts it may change;
- public APIs it may change;
- allowed and forbidden dependency edges;
- state/effect ownership affected;
- mapped future attachment points that must remain intact;
- explicit exclusions it must not reintroduce; and
- architecture fitness tests that prove the slice did not wall off later
  capability zones.

A narrow implementation is acceptable. A narrow architecture document that
pretends unmapped territory does not exist is not.

## 11. Change and supersession policy

- Accepted artifacts are not rewritten to hide an old decision.
- Correct typographical errors in place only when semantics do not change.
- Semantic changes require a new revision and decision link.
- A superseded artifact remains available for historical replay.
- Generated artifacts carry the source contract digest.
- Research corrections name the original claim and why it changed.
- Historical model reviews remain advisory records even if the selected model
  later changes.

## 12. AI-agent reading contract

Before architecture or implementation work, an agent receives:

1. the exact task packet;
2. the applicable Core-SDLC state/control/risk-lane projection;
3. this source-of-truth policy;
4. the full-system architecture;
5. applicable accepted ADRs;
6. applicable machine contract revisions;
7. applicable policy/instruction records;
8. only the research required by the packet;
9. exact repository/workspace identity; and
10. output and evidence schemas.

The packet manifest proves what was delivered. It does not prove attention or
compliance; behavior and evidence are evaluated separately.

## 13. Human authority

The human owner is the final authority for:

- product scope;
- architecture acceptance;
- governance and risk;
- policy and waiver changes;
- credentials, provider spend, and external egress;
- destructive operations;
- irreversible migrations;
- release and upstream-sync acceptance; and
- unresolved material conflicts.

Routine legal transitions may be performed by deterministic code under accepted
policy. Human authority does not justify bypassing the same subject binding,
authentication, expiry, replay protection, audit, and data-classification rules.
