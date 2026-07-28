# Ranex Source of Truth and Decision Policy

| Field | Value |
|---|---|
| Policy ID | `POL-SOT-001` |
| Version | `1.3.0` |
| Status | Normative supporting policy |
| Owner | Human governor |
| Effective date | 2026-07-27 |
| Repository snapshot basis | `bootstrap/pre-upstream`; release/review manifests bind the exact revision and file digest |
| Applies to | Architecture, implementation, AI-agent work, review, release, and operations |
| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Parent architecture | [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0002](./decisions/ADR-0002-retire-legacy-implementation-guide.md); [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md); [ADR-0004](./decisions/ADR-0004-establish-initial-quality-attribute-baselines.md); [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md); [ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md); [ADR-0007](./decisions/ADR-0007-establish-modular-ddd-repository-organization.md); [ADR-0008](./decisions/ADR-0008-make-tdd-the-default-development-discipline.md); [ADR-0009](./decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md) |
| Compatibility/migration class | New governing policy; older source precedence is mapped, never silently discarded |
| Security/data class | Public policy metadata; attached evidence retains its own classification |
| Review trigger | First two end-to-end tracers, then quarterly or on authority/source-precedence change |

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

For internal product decisions, authenticated human decision is the highest
accountable authority within applicable law, contract, license, privacy, and
third-party rights. The remaining sources govern different subjects rather
than forming a misleading total ordering:

| Authority source | Governing scope | Cannot do |
|---|---|---|
| Authenticated human decision and accepted ADR | Exact product, architecture, risk, policy, release, or effect decision | Rewrite empirical evidence, bypass exact-subject rules, or waive applicable external obligations |
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
                                  typed assignment + fenced lease
                                  governor/budget/isolation profile
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
runtime contract. A research directory is never an implicit live subject:
reviews bind explicit sorted path/digest manifests, including separate addendum
manifests when files arrive after a review freeze.

### 3.1 Retired legacy implementation guide

The owner removed the former root implementation guide through
[ADR-0002](./decisions/ADR-0002-retire-legacy-implementation-guide.md). It is
not a capability checklist, bootstrap playbook, operational-requirement source,
construction input, or migration plan for new work.

- Agents must not restore or use the deleted guide from Git history, another
  branch, a review bundle, a source manifest, quoted research, or prior model
  context.
- Historical research, review records, manifests, and phase records may name
  it only to preserve what was actually inspected or executed at that time.
  Such a reference grants no present authority.
- A still-useful observation from the retired guide must be re-observed,
  reconciled against the current Core SDLC and architecture, and accepted as a
  new requirement, control, RFC/ADR, runbook, or machine contract before use.
- New implementation itineraries are derived from the Core SDLC, this policy,
  the full-system architecture, the Engineering Reference Application Map,
  accepted ADRs, and machine contracts.

The older plugin-first layout, duplicate role/state/path vocabularies, separate
office authority model, and pre-authority phase ordering are rejected
construction sources. They cannot be revived through a lower-precedence
artifact.

## 4. Document classes

| Class | Purpose | May be normative? | Change mechanism |
|---|---|---:|---|
| Core SDLC policy/control | Product-to-production process, state, roles and assurance | Yes | Human-accepted superseding ADR and versioned migration |
| Architecture | Full target shape, ownership, boundaries, dependencies | Yes | RFC, independent review, human-accepted ADR |
| Worker/fleet control | Assignment, liveness, fencing, governor, topology, budget, isolation, handoff, measurement | Yes only as a subordinate projection of Core SDLC/architecture | RFC/ADR plus exact contract and adoption-gate evidence |
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

Normative status and proof maturity are separate fields. The full-system target
is `ACCEPTED` by ADR-0003 while executable-contract maturity remains pending
`AI-G2` and runtime qualification remains unvalidated. No document may encode
those three facts in one ambiguous status or infer a gate result from an
accepted decision.

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

The content digest and exact repository revision are stored in the immutable
review/release source manifest rather than in the artifact's own digest-bearing
body. This avoids a self-referential digest and the false claim that a commit
containing the document can name itself. A display table may name the
repository snapshot basis, but the manifest is the exact machine binding.

Every research or review artifact additionally states:

- evidence corpus and exact revisions/digests;
- method;
- model/provider/transport identity if a model participated;
- limitations;
- file mutations, if any; and
- which claims are fact, inference, proposal, owner requirement, or unknown.

## 7. Machine contract registry

The executable documentation-contract baseline uses these canonical JSON
registries:

```text
architecture/contracts/
├── applicability-rules.json
├── architecture-elements.json
├── architecture-rule-assessments.json
├── artifact-types.json
├── context-boundary-fitness.json
├── context-coupling-policy.json
├── context-dependency-edges.json
├── contexts.json
├── data-ownership.json
├── decisions.json
├── effects.json
├── engineering-practice-profiles.json
├── engineering-practices.json
├── events.json
├── feedback-fitness.json
├── identities.json
├── paths.json
├── priority-rules.json
├── schema-registry.json
├── states.json
├── test-practice-profiles.json
├── test-practices.json
├── topology-rules.json
├── vital-profile.json
└── registry-manifest.json
```

The artifact schemas and canonicalization rules are specified in
[Ranex AI-Work Artifact Contract Specification](./AI_ARTIFACT_CONTRACTS.md).
The manifest content-binds every registry except itself to avoid a circular
digest. Enactment of this documentation-contract layer does not make runtime
producers, generated consumers, repository topology, tests, or `AI-G2` pass.
`engineering-practice-profiles.json` projects the exact
[`ENGPROFILE-RANEX-ARCHITECTURE-DESIGN-001`](../research/ranex-architecture-practice-application-profile.json):
all nine source families and 34 practices are dispositioned for the design,
while all 33 applicable runtime outcomes remain `NOT_ASSESSED` and the profile
remains nonsealing.

They resolve the previously documented conflicts:

1. `WorkItemStatus`, `RunStatus`, `AssignmentStatus`, `LeaseStatus`,
   `MailboxDeliveryStatus`, `IncidentStatus`, `ReleaseStatus`,
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
13. agent assignment, lease, heartbeat, mailbox, governor termination, and
    fleet experiment records cannot alias work/run/gate/decision authority.
14. the ADR-0006 register contains exactly the contiguous 29 fixed decision IDs,
    their alternatives, owners, governing ADRs, and fitness functions.
15. ADR-0007 fixes the sole context root, internal layer/port/adapter placement,
    public-import/dependency/cycle/composition/messaging/persistence rules,
    tests/source mirroring, schema/generated/migration/legacy rules,
    ownership/navigation/package discovery, and exact exception protocol.
16. ADR-0008 fixes production-path TDD, one built exact artifact, allowed test
    roots, declared deterministic seams, fake/real parity, ephemeral SQLite,
    the full failure-mode matrix, closed-transition exhaustiveness,
    open-space exploration, fixture/data/flakiness/generated/migration/lane/
    observability/mutation/exception rules, and noncompensating signals.
17. ADR-0009 fixes the exact deny-by-default public-API edge ledger, one
    falsifiable boundary-fit record per registered context, governed-execution
    coupling measures/triggers, exact-host feedback objectives, deterministic
    selection/sharding/escalation, and noncompensating review behavior.

The contract compiler projects, without semantic edits, the fenced YAML
decision register in
[ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md)
into `decisions.json` and `architecture-elements.json`, and projects ADR-0004
baselines into those owned records. It projects ADR-0007 through
`contexts.json`, `paths.json`, and `topology-rules.json`; it projects ADR-0008
through `test-practices.json`, `test-practice-profiles.json`, and
`schemas/common/test-practice-profile-v1.schema.json`. ADR-0009 projects to
`context-dependency-edges.json`, `context-boundary-fitness.json`,
`context-coupling-policy.json`, and `feedback-fitness.json`. The exact 47
rule-level evaluation records live in `architecture-rule-assessments.json` and validate
against `schemas/common/architecture-rule-assessment-v1.schema.json`; its
`noncompensating_summary` has no score or independent `PASS` authority. A
missing rule, changed meaning, duplicate owner, invalid exception, unregistered
test root, or other projection mismatch is `CONFLICT`.

### 7.1 Single-owner authority records

| Record/transition | Sole source owner | Allowed downstream use |
|---|---|---|
| `WorkItemStatus` | `work_management` | Other contexts consume immutable work facts and request transitions |
| `RunStatus`, gate binding, grant/permit, effect intent/outcome/reconciliation | `governed_execution` | Adapters execute only a valid, exact-subject permit |
| Rule/risk/authorization snapshot and `HumanDecisionRecord` requirements | `policy` | Governed execution evaluates eligibility; policy does not issue/consume permits |
| Principal/session/challenge/secret handle | `identity_access` | Policy and adapters consume authenticated facts/opaque handles |
| Claim, evidence envelope, checker result, snapshot, `GateEvaluation` | `assurance` | Governed execution binds a fresh immutable evaluation |
| Review request/attempt/observation/verdict/independence evaluation | `analytical_review` | Assurance ingests immutable references; it does not rewrite them |
| Process audit/capability assessment/fleet experiment | `process_assurance` | Improvement input only; never runtime gate authority |

Duplicate or missing owners fail the applicable `contexts.json`,
`data-ownership.json`, and `paths.json` closure checks. A model, board, worker,
review transport, delivery channel, generated view, or adapter is never an
authority owner.

Prose examples are generated from or validated against these registries. An
example cannot create a new state, role, path, or capability.

### 7.2 Repository-organization and TDD projections

[ADR-0007](./decisions/ADR-0007-establish-modular-ddd-repository-organization.md)
is the semantic owner for modular-DDD organization. Its canonical port path is
only `src/ranex/<context>/application/ports/`. Context-exclusive adapters live
under `src/ranex/<context>/adapters/<technology>/`; central
`src/ranex/adapters/<boundary>/<technology>/` paths require an exact
`HOST_EDGE_ADAPTER` exception. `topology-rules.json` owns the executable rule
IDs, allowed exception classes/record shape, ownership/reviewer constraints,
and package-discovery constraints. `contexts.json` and `paths.json` project
registered instances; every path row validates against
`schemas/common/path-contract-v1.schema.json`. A generated CODEOWNERS view
requests review but never owns semantics.

[ADR-0008](./decisions/ADR-0008-make-tdd-the-default-development-discipline.md)
is the semantic owner for test-first construction and verification policy.
The only top-level test roots are `unit`, `contract`, `integration`,
`architecture`, `acceptance`, `system`, `e2e`, `security`, `performance`,
`resilience`, `migration`, `replay`, `operations`, `qualification`,
`effectiveness`, `evaluation`, `fixtures`, and `builders`.
`test-practices.json` projects the complete `TDD-*` and `FF-TDD-*` policy;
`test-practice-profiles.json` binds applicability profiles; the common schema
validates those profiles. `tests/persistence` and `tests/crash` are not
alternate roots.

`architecture-rule-assessments.json.entries` contains exactly one row for every
one of the 18 `ORG-*`, 19 `TDD-*`, and ten ADR-0009 rules: 47 total. Each row
carries its own exact subject, applicability/result, evidence,
observation/freshness, owner, and N/A/exception basis under the common
assessment schema. The
`noncompensating_summary` may report denominators and blocking-state counts
only; it cannot average, score, promote, or override a row.

### 7.3 Boundary-fit, dependency, coupling, and feedback projections

[ADR-0009](./decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md)
owns the exact 67-edge deny-by-default public-API graph, 34 boundary-fit
hypotheses, six governed-execution coupling measures/triggers, four
reference-host feedback objectives, deterministic selection/sharding/
escalation, and ten noncompensating rule definitions. Its four registries
validate against the exact `context-dependency-edge-v1`,
`context-boundary-fit-v1`, `context-coupling-policy-v1`, and
`feedback-fitness-policy-v1` schemas under `schemas/common/`.

Every edge names caller/callee owners, rationale, interaction, consistency,
failure, and recovery; actual imports must be a public-API-only subset and
acyclic. Every canonical context has one stable `BOUNDARYFIT-*` element,
merge/split alternatives, and a tracer falsifier. Coupling and feedback
thresholds trigger owned review/remediation; they neither force a service
split nor compensate for another failed/unknown rule.

For all three ADRs, accepted prose owns meaning and the registries own exact
executable vocabulary. Neither may silently repair the other. Mismatch is
`CONFLICT`; absent or insufficient material proof is `UNKNOWN`; either blocks
the applicable gate. A `NOT_APPLICABLE` result needs a registered rule and
evidence. Documentation acceptance and registry generation do not establish
source-tree conformance, TDD enactment, runtime correctness, or an overall
quality score.

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
- the exact engineering-practice registry and application profile, including
  applicable practices, explicit non-applicability decisions, required
  behavior, deviations, and verification evidence;
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
5. the applicable projection of the Engineering Reference Application Map and
   its machine-registered engineering-practice profile;
6. applicable accepted ADRs;
7. applicable machine contract revisions;
8. the applicable fleet assignment, lease, fencing, budget, isolation, and
   topology profile when a worker is dispatched;
9. applicable policy/instruction records;
10. only the research required by the packet;
11. exact repository/workspace identity; and
12. output and evidence schemas.

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
