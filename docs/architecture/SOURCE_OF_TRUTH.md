# Ranex Source of Truth and Decision Policy

| Field | Value |
|---|---|
| Policy ID | `POL-SOT-001` |
| Version | `1.10.0` |
| Status | Normative supporting policy |
| Owner | Human governor |
| Effective date | 2026-07-29 |
| Repository snapshot basis | `bootstrap/pre-upstream`; release/review manifests bind the exact revision and file digest |
| Applies to | Architecture, implementation, AI-agent work, review, release, and operations |
| Parent process | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Parent architecture | [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Owner decisions | [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md); [ADR-0002](./decisions/ADR-0002-retire-legacy-implementation-guide.md); [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md); [ADR-0004](./decisions/ADR-0004-establish-initial-quality-attribute-baselines.md); [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md); [ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md); [ADR-0007](./decisions/ADR-0007-establish-modular-ddd-repository-organization.md); [ADR-0008](./decisions/ADR-0008-make-tdd-the-default-development-discipline.md); [ADR-0009](./decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md); [ADR-0010](./decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md); [ADR-0011](./decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md); [ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md); [ADR-0013](./decisions/ADR-0013-promote-hermes-research-obligations.md); [ADR-0014](./decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md); [ADR-0015](./decisions/ADR-0015-canonical-workflow-and-event-schema-and-upcaster-policy.md); [ADR-0016](./decisions/ADR-0016-resolve-five-implementation-start-owner-decisions.md); [ADR-0017](./decisions/ADR-0017-record-resolved-owner-decisions.md); [ADR-0018](./decisions/ADR-0018-select-the-static-type-checker.md); [ADR-0019](./decisions/ADR-0019-declare-uv-as-the-python-toolchain-manager.md); [ADR-0020](./decisions/ADR-0020-declare-the-record-freshness-self-check.md) |
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
- how worker roles, exact tool grants, runtime adapters, and route locks are
  compiled without delegating control to a model; and
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

For planning authority,
[`SDLC-EST-001`](./SDLC_CONTROL_CATALOG.md#sdlc-est-001--estimate-and-commitment-separation)
is the canonical estimate/commitment boundary. An estimate is evidence about
uncertainty and has no decision, state, gate, grant, permit, landing, release,
or effect authority. A delivery commitment exists only through a current
authenticated `HumanDecisionRecord` for the exact closed commitment subject.
Any changed scope, estimate binding, capacity, dependency, risk, acceptance
basis, or expired window invalidates reliance and requires a fresh subject and
decision. No projection, model output, task packet, board date, or passing
unrelated control can compensate.

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
                           role ceiling -> exact task-minimal grant
                           one route/runtime/auth lock + affinity key
                           typed assignment + fenced lease
                           governor/budget/isolation profile
                                                   |
                                                   v
                   one leaf worker -> independent leaf review -> gate evidence
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

Ranex control services alone create assignments and own cross-worker
orchestration, scheduling, dispatch, bounded fan-out, and join. An official
runtime may execute a bounded model/tool loop inside one assignment, but a
worker cannot spawn, delegate to, coordinate, or route another model worker;
widen its route, role, or grant; or turn a model proposal into control-plane
authority.

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
| Worker role/runtime catalog | Immutable role ceilings, exact-grant compilation rules, leaf-only official-runtime adapters, route locks, and session affinity | Yes only as a machine projection of accepted ADR semantics | Superseding ADR, strict catalog revision, regeneration, and qualification evidence |
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
| `OWNER_DECISION_REQUIRED` | A genuine owner choice is unresolved; no default applies and the affected progression remains blocked |
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
├── accepted-adrs.json
├── applicability-rules.json
├── architecture-element-assessments.json
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
├── estimate-commitment-control.json
├── events.json
├── feedback-fitness.json
├── generated-output-authority.json
├── identities.json
├── legacy-test-direct-source-classifications.json
├── legacy-test-layout-policy-v1.json
├── legacy-test-layout-policy-v2.json
├── legacy-test-layout-policy.json
├── legacy-test-layout-records-v1.json
├── legacy-test-layout-records-v2.json
├── legacy-test-layout-records.json
├── paths.json
├── priority-rules.json
├── readiness-assessments.json
├── readiness-tiers.json
├── registry-manifest.json
├── runtime-adapters.json
├── schema-registry.json
├── states.json
├── tdd-cycle-records.json
├── tdd-exception-records.json
├── test-behaviors.json
├── test-deletion-records.json
├── test-practice-profiles.json
├── test-practices.json
├── test-quarantine-records.json
├── topology-rules.json
├── vital-profile.json
└── worker-role-profiles.json
```

The artifact schemas and canonicalization rules are specified in
[Ranex AI-Work Artifact Contract Specification](./AI_ARTIFACT_CONTRACTS.md).
The manifest content-binds every registry except itself to avoid a circular
digest. `generated-output-authority.json` declares every generator- or
validator-owned output and separately identifies the immutable ADR-0010
predecessor inputs. Its per-path licensing-policy partition is projected from
the hand-maintained legal manifest and content-binds that source; generation
does not assign or expand ownership. The validator independently requires the
three engineering-reference projections to remain
`CURATED_RESEARCH`/`NOASSERTION`. `accepted-adrs.json` is the exact
accepted-decision projection. The unversioned and `-v1` legacy layout files are immutable
predecessor/compatibility inputs, not active generator-owned policy.
`legacy-test-layout-policy-v2.json`,
`legacy-test-layout-records-v2.json`,
`legacy-test-direct-source-classifications.json`, and
`test-behaviors.json` are the active ADR-0010 projections.
`estimate-commitment-control.json` is the exact `SDLC-EST-001` source
projection and remains `DEFINED_RUNTIME_NOT_ASSESSED`. Its 33 source-declared
schemas and exact six-positive/213-negative V2 case catalogs currently prove
definition coverage only: semantic execution is zero, the schema mutation
matrix is `NOT_EXECUTED`, and runtime validation is `NOT_ASSESSED`.
`readiness-tiers.json` and `readiness-assessments.json` project ADR-0012;
both tiers currently remain `NOT_ASSESSED`, with zero assessment records and
no authorization.

Enactment of this documentation-contract layer does not make runtime
producers, generated consumers, repository topology, tests, or `AI-G2` pass.
`engineering-practice-profiles.json` projects the exact
[`ENGPROFILE-RANEX-ARCHITECTURE-DESIGN-001`](../research/ranex-architecture-practice-application-profile.json):
all ten source families and 38 practices are dispositioned for the design,
while all 37 applicable runtime outcomes remain `NOT_ASSESSED` and the profile
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
16. ADR-0008 fixes production-path TDD, one exact base/candidate cycle and built
    artifact/profile, ordered RED/GREEN/REFACTOR/architecture-check transitions,
    exact test/failure denominators, allowed roots, deterministic seams,
    fake/real parity, ephemeral SQLite, the full failure-mode matrix,
    closed-transition exhaustiveness, open-space exploration,
    fixture/data/generated/migration/lane/observability/mutation rules, and four
    canonical cycle/exception/quarantine/deletion authorities with typed
    evidence, complete-population reconciliation, lifecycle, and
    noncompensating signals.
17. ADR-0009 fixes the exact deny-by-default public-API edge ledger, one
    falsifiable boundary-fit record per registered context, governed-execution
    coupling measures/triggers, exact-host feedback objectives, deterministic
    selection/sharding/escalation, and noncompensating review behavior.
18. ADR-0010 binds the exact 2,444-file inherited Hermes test baseline, 29
    directory exceptions, 134 direct files, 16 inherited canonical-path files,
    no-expansion/change controls, destinations/owners, expiry, per-file
    migration proof, and the complete cutover gate without claiming migration.
19. ADR-0011 fixes Ranex as the sole cross-worker orchestrator, every
    model/harness as a leaf worker, immutable role ceilings narrowed to an
    exact task-minimal proper subset, one explicit no-fallback route per
    assignment, typed official runtime adapters, actual tool-surface
    enforcement, same-assignment/session-affine reuse, and the removal of
    Hermes/Nous inference, monetization, credential, and fallback routes.
20. ADR-0012 separates `IMPLEMENTATION_START_READY` from `PRODUCTION_READY`.
    The first requires an exact committed source/generated subject, deterministic
    validation, clean fork preflight, one real current TDD/landing/sealing
    tracer, two fresh independent structural reviews, finding closure, and a
    causal human decision while permitting explicit runtime `NOT_ASSESSED`.
    The second additionally requires enacted runtime producers, exactly 64
    current architecture-rule results, operational/recovery/security evidence,
    applicable capability assessments, and a separate human decision.

The contract compiler projects, without semantic edits, the fenced YAML
decision register in
[ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md)
into `decisions.json` and `architecture-elements.json`, and projects ADR-0004
baselines into those owned records. It projects ADR-0007 through
`contexts.json`, `paths.json`, and `topology-rules.json`; it projects ADR-0008
through `test-practices.json`, `test-practice-profiles.json`, and
`schemas/common/test-practice-profile-v1.schema.json`; its canonical runtime
instances project from `architecture/records/test-health/` to
`tdd-cycle-records.json`, `tdd-exception-records.json`,
`test-quarantine-records.json`, and `test-deletion-records.json`, validated by
the corresponding `schemas/common/*-record-v1.schema.json` schemas. ADR-0009 projects to
`context-dependency-edges.json`, `context-boundary-fitness.json`,
`context-coupling-policy.json`, and `feedback-fitness.json`. ADR-0010 projects
to `legacy-test-layout-policy-v2.json`,
`legacy-test-layout-records-v2.json`,
`legacy-test-direct-source-classifications.json`, `test-behaviors.json`,
`schemas/common/legacy-test-layout-policy-v2.schema.json`,
`schemas/common/legacy-test-change-exception-v2.schema.json`,
`schemas/common/legacy-test-migration-record-v2.schema.json`,
`schemas/common/legacy-test-cutover-removal-record-v2.schema.json`,
`schemas/common/direct-source-classification-authority-v1.schema.json`, and
`schemas/common/test-behavior-authority-v1.schema.json`. The corresponding
unversioned and `-v1` contract files remain immutable verify-only inputs and
are never regenerated. ADR-0011
projects its strict fenced YAML catalog, without semantic edits, to
`worker-role-profiles.json` and `runtime-adapters.json`; both remain
definition-only until separately implemented and qualified. ADR-0012 projects
its strict readiness contract to `readiness-tiers.json`,
`readiness-assessments.json`, and
`schemas/assurance/readiness-subject-v1.schema.json`,
`schemas/assurance/readiness-subject-manifest-v1.schema.json`,
`schemas/assurance/readiness-evidence-binding-v1.schema.json`, and
`schemas/assurance/readiness-assessment-v1.schema.json`; those definition-only
projections start with both tiers `NOT_ASSESSED` and grant no authorization.
The exact 64
rule-level evaluation records live in `architecture-rule-assessments.json` and validate
against `schemas/common/architecture-rule-assessment-v1.schema.json`; its
`noncompensating_summary` has no score or independent `PASS` authority. A
missing rule, changed meaning, duplicate owner, invalid exception, unregistered
test root, or other projection mismatch is `CONFLICT`.

HERMES §17 projects all 40 initial event rows to `events.json` and their
`DomainEventEnvelopeV1` plus closed payload schemas under `schemas/events/`.
`DEFINED_NAME_ONLY` is blocking; generated schema presence does not claim
runtime emission/delivery/replay.

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

Runtime TDD authority is never embedded in a profile. The sole source patterns
are:

```text
architecture/records/test-health/
├── tdd-cycles/<cycle_id>.json
├── tdd-exceptions/<exception_id>.json
├── quarantines/<quarantine_id>.json
└── obsolete-test-deletions/<deletion_id>.json
```

They project respectively to registries
`REG-TDD-CYCLE-RECORDS-001`, `REG-TDD-EXCEPTION-RECORDS-001`,
`REG-TEST-QUARANTINE-RECORDS-001`, and
`REG-TEST-DELETION-RECORDS-001`. Profiles contain ID projections only; the
validator queries the four canonical registries and reconciles the complete
applicable population for the exact task/candidate/test/gate/risk. Each runtime
reference is a typed `{artifact_type, artifact_ref, artifact_digest}` resolved
to qualified exact-subject evidence, gate, review, or authenticated human
decision bytes. Bare strings, inline approval, omission, wrong subject,
unqualified/stale evidence, dirty committed-subject mixing, or noncausal
chronology blocks. Initial source/registry sets are empty, so no runtime TDD
cycle, exception, quarantine, or deletion is claimed.

`architecture-rule-assessments.json.entries` contains exactly one row for every
one of the 18 `ORG-*`, 26 `TDD-*`, ten ADR-0009, and ten ADR-0010 rules: 64
total. Each row
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

For all four ADRs, accepted prose owns meaning and the registries own exact
executable vocabulary. Neither may silently repair the other. Mismatch is
`CONFLICT`; absent or insufficient material proof is `UNKNOWN`; either blocks
the applicable gate. A `NOT_APPLICABLE` result needs a registered rule and
evidence. Documentation acceptance and registry generation do not establish
source-tree conformance, TDD enactment, runtime correctness, or an overall
quality score.

### 7.4 Inherited Hermes test-layout projection

[ADR-0010](./decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md)
is the semantic owner for time-bounded coexistence of the accepted Hermes test
tree. `legacy-test-layout-policy-v2.json` embeds the immutable source
commit/tree, the exact `git ls-tree` digest, and all 2,444 bytewise
path-sorted file rows with mode, Git blob OID, and content SHA-256. It expands
exactly
`LEGACY-TEST-ROOT-001..029`, `LEGACY-TEST-TOPLEVEL-001`, and the two inherited
canonical scopes with their owners, destinations, trigger, expiry, and removal
proof.

The sole active/accepted instance sources are bytewise-sorted JSON records
under
`architecture/records/legacy-test-layout/{change-exceptions,migration-records,cutover-removal-records}/`.
They project to `legacy-test-layout-records-v2.json`
(`REG-LEGACY-TEST-LAYOUT-RECORDS-001`) and are also embedded in the policy;
the global manifest content-binds both projections. Landed bytes are immutable;
closure/removal occurs only through a governed commit with Git and landing
evidence retaining the prior bytes/digest. The initial empty set authorizes
nothing. Retirement is not duplicated here: accepted
`TestDeletionRecordV1` instances resolve only through
`test-deletion-records.json`. The validator loads all records from one named
committed Git subject, rejects dirty/staged/untracked mixing, unused
exceptions/proofs, retained derived-closed active sources, and omitted
applicable deletion lineage, and independently recomputes source and cutover
state. The unversioned and `-v1` layout files are retained byte-for-byte as
immutable predecessor/compatibility inputs under the generated-output
authority; they are not the active projection and cannot be rewritten by the
generator.

Change-exception subjects are exact path transitions. Accepted migration
records are MIGRATED-only and form one contiguous predecessor-linked sequence
of complete atomic groups over the derived inherited-disposition state. A
legacy source or later canonical migrated test retires only through the
canonical deletion authority. Before every event, the full committed legacy
ledger must match; the after-before `tests` delta contains only the named
change/group/deletion operations, preventing unrelated changes and temporary
reintroduction. Each event binds causal full Git commits, complete tree/blob/
mode snapshots and delta manifests, strict evidence/decision/landing
chronology, typed exact-subject qualified artifacts/roles, and a successful
commit-preserving `LandingRecord`. One group may dispose many old sources into
one shared canonical test, but every source is accounted exactly once.

The cutover is a zero-test-delta immutable event-time subject with causal
before/after commits, complete ledger/lineage/snapshot and ordered-migration
digests, typed evidence/decisions, and one successful landing. It does not
freeze later ordinary ADR-0008 canonical evolution; current validation still
recomputes zero legacy, no active exception/recontamination, global retired-ID
nonreuse, and ACTIVE-or-governed-RETIRED lineage terminals.

The baseline is `BASELINE_BOUND_NOT_MIGRATED`. Unchanged files may execute as
nonsealing inherited regression evidence; they cannot establish Ranex TDD,
architecture, or gate conformance. A new direct/legacy-root test, unregistered
path/content change, expired authorization, incomplete migration record, or
count-only cutover claim is a blocking failure. New Ranex tests remain limited
to ADR-0008's 18 canonical roots, and one failed/unknown/conflicting/expired
`LEGACYTEST-*` row keeps the whole legacy-layout summary nonsealing.
Every change/migration/cutover acceptance and successful landing must finish by
2026-10-31T23:59:59Z. Post-expiry migration/cutover cannot retroactively cure
the lapse. Only a complete independently accepted and landed
`LEGACY-TEST-CUTOVER-001` from on/before expiry remains valid historical proof
afterward.

### 7.5 Worker-role and runtime-adapter projection

[ADR-0011](./decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md)
is the sole semantic owner for the initial worker-role and runtime-adapter
catalog. Its strict fenced YAML block projects without semantic editing to
`worker-role-profiles.json` and `runtime-adapters.json`. The projection
preserves `catalog_status: DEFINITION_ONLY`; every role and adapter remains
`DEFINED_NOT_QUALIFIED`. Registry presence proves neither implementation,
activation, runtime containment, performance, vendor entitlement, nor effective
authentication.

A role profile is an immutable maximum envelope, not an assignment grant. Each
assignment starts empty and binds an exact task-minimal proper subset of both
the role's tool ceiling and capability ceiling. The grant compiler cannot add a
tool or capability because a runtime exposes it, an ambient configuration names
it, a prompt requests it, or a prior session used it. Every effectful operation
still crosses policy and `CapabilityBus`; the workspace/path, OS process,
network, and resource controls remain independent enforcement layers.

The initial catalog defines three roles:
`ROLEPROFILE-RESEARCH-READONLY-001`,
`ROLEPROFILE-IMPLEMENTATION-WORKER-001`, and
`ROLEPROFILE-INDEPENDENT-REVIEWER-001`. It defines two official-runtime
boundaries: `RUNTIME-CLAUDE-AGENT-SDK-001` owns the release-pinned Claude Agent
SDK managed-client stream, and `RUNTIME-CODEX-APP-SERVER-001` owns the
release-pinned Codex stable app-server JSON-RPC/JSONL stdio boundary. A provider
or harness absent from the accepted catalog is not a qualified product runtime.

Every assignment binds one provider, full model ID, transport, runtime adapter
and version, configured auth intent, adapter-observed effective auth
source/subject, route lock, workspace, role, effective grant, lease, and
fencing epoch. Adapter, provider, and model fallback and auxiliary model calls
are disabled. Vendor-internal entitlement facts that the initialized official
runtime cannot expose remain `UNKNOWN`. Ranex may redispatch only through a new
assignment after policy, qualification, budget, and route checks; that is not
fallback inside the failed assignment.

Actual runtime surfaces, not prompt prose or auto-approval lists, define
containment. The Claude adapter therefore uses the exact `tools` set, its deny
complement, strict MCP/config isolation, a deterministic catch-all
`PreToolUse` or SDK custom-tool gateway, and independent effect controls;
`allowed_tools` is not a restriction and `can_use_tool` is only an ask-path
fallback. Agent/team/delegation, scheduler/trigger, tool-discovery,
worktree-entry, and background-capable surfaces are absent. The Codex adapter
likewise denies ambient apps, plugins, MCP servers, skills, dynamic tools,
nested agents, and ungranted shell/process paths. Startup attestation must
match the initialized runtime surface and effective route to the assignment.

Client reuse is allowed only under the catalog's complete
assignment/session-affinity key. A changed key, expired lease, unproven clean
state, or cancellation terminates reuse. Lifecycle uses the official SDK or
protocol: interrupt, drain correlated events to a deadline, disconnect through
the pinned runtime, then verify outer-supervisor cleanup. Qualification measures
cold one-shot, cold managed-client, and same-session connected-client paths
before any performance threshold is accepted.

Hermes remains provenance, frozen characterization, and non-inference
compatibility input only. Neither Hermes nor Nous is a live inference,
orchestration, provider, model, credential, entitlement, monetization, or
fallback route. Compatibility code cannot dispatch a model worker.

ADR-0011's eight `FF-*` obligations are noncompensating and initially
`NOT_ASSESSED`. They do not change the separate 64-rule assessment denominator
projected from ADR-0007 through ADR-0010; generator output or accepted prose
cannot claim the runtime, containment, auth, decommissioning, or performance
results.

### 7.6 Readiness-tier projection and authority

[ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md)
is the sole semantic owner of the readiness namespace. Its documentation labels
`DESIGN_DEFINITION_READY` and `ENTERPRISE_RUNTIME_READY` explain, but do not
alias, the canonical machine states `IMPLEMENTATION_START_READY` and
`PRODUCTION_READY`. An unqualified “build ready,” “enterprise ready,” or
“runtime ready” statement has no authority effect.

Tier 1 permits only admission of staged implementation under ordinary
per-work-item state, packet, gate, grant, permit, TDD, review, and landing
controls. It is attainable with an explicit runtime `NOT_ASSESSED` fact because
it does not claim runtime enactment, score, release, deployment, or operational
effectiveness. Before Tier 1, only ADR-0012's bounded
`PRE_READINESS_TOOLING_TRACER` may produce the evidence needed to assess that
tier; it cannot implement product capability or activate product runtime.
Its exact closed subject manifest and per-gate evidence bindings preserve each
TDD, landing, review, decision, prerequisite, and runtime artifact's native
subject; a bridge proves the relation but never relabels evidence. An ordinary
authorized product commit on a clean descendant retains Tier 1 only while the
governed design/control manifest is byte-identical and all per-work controls
still apply.

Tier 2 requires the current shared readiness basis from Tier 1 plus enacted
runtime producers, the separate exact 64-rule result set, required adoption,
security, operational, recovery, and capability evidence, and its own
authenticated human decision. A readiness assessment is a prerequisite fact:
neither tier issues an authority grant or permit, mutates work, lands code,
releases, deploys, waives a gate, or proves an outcome. Both tiers currently
remain `NOT_ASSESSED` and unauthorized.

### 7.7 Event and architecture-element exactness

`events.json` contains exactly the HERMES §17 catalog contract for each event:
owner/producer/consumers, trigger/preconditions, aggregate/source versions,
closed envelope and payload schema, correlation/causation/idempotency,
ordering/delivery, privacy/retention, compatibility/upcast, and failure/replay.
Each is `DEFINED_CONTRACT` but runtime evidence remains `NOT_ASSESSED`.
`DEFINED_NAME_ONLY` blocks `IMPLEMENTATION_START_READY`. A complete definition
may contribute to that tier, but explicit runtime `NOT_ASSESSED` still blocks
`PRODUCTION_READY`.

Every current `architecture-elements.json` row additionally carries
`definition_contract_ref`, RFC 8785
`canonical_definition_row_digest`, `source_ref`, `source_file_digest`, and
resolved `parent_element_refs`. State values bind their parent axis; artifacts
bind their schema/artifact row; paths, edges, boundaries, events, rules, and
other generated children bind their complete canonical definition row and
semantic parents. `DEFINED` cannot mean only name/owner/source path.
`architecture-element-assessments.json` exact-subjects those complete
bindings; any row/source/parent change stales the assessment. The 1,008 current
elements include 43 state axes and 278 state values; the canonical §16
`RuleEnforcementClass`, `RuleStage`, and `SyncDisposition` axes are included.
The matching current assessment registry resolves 191 `DIRECT`, 30
`INHERITED_FROM_PROFILE`, 346 `INHERITED_FROM_RULE`, and 441
`INHERITED_FROM_OWNER` dispositions. In the element registry, 191 elements
carry 533 explicit typed engineering-practice mappings and 817 carry
`NO_EXPLICIT_MAPPING`. That latter value is not `NOT_APPLICABLE`, a runtime
result, or a compensating score. All parent references and complete definition
bindings validate, and all runtime outcomes remain `NOT_ASSESSED`.

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
- provider/model/runtime/auth route identity, no-fallback semantics, or
  Ranex-owned redispatch authority;
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
- the exact role-profile ID/version/digest and a task-minimal effective tool
  and capability grant that is a proper subset of its immutable ceiling;
- the single provider/model/transport/runtime-adapter/auth route lock, with
  fallback and auxiliary model calls disabled;
- the workspace/session-affinity key, cancellation deadline, event-correlation
  fields, and cleanup obligations;
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
8. the applicable fleet assignment, role-profile ceiling, exact effective
   tool/capability grant, single route lock, runtime adapter, session-affinity
   key, lease, fencing, budget, isolation, cancellation, and topology profile
   when a worker is dispatched;
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
- credentials, provider spend, effective authentication route, vendor
  entitlement/terms acceptance, and external egress;
- destructive operations;
- irreversible migrations;
- release and upstream-sync acceptance; and
- unresolved material conflicts.

Routine legal transitions may be performed by deterministic code under accepted
policy. Human authority does not justify bypassing the same subject binding,
authentication, expiry, replay protection, audit, and data-classification rules.
