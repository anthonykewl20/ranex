# Ranex Architecture Documentation

This directory is the normative architecture base for rebuilding Hermes into
Ranex.

The target architecture is accepted as a paper construction contract by
[ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md).
That is neither of the readiness claims defined by
[ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md).
`IMPLEMENTATION_START_READY` still requires the exact source/generated
contract, clean committed fork, real cycle/landing/seal, current independent
reviews, finding closure, and human decision. `PRODUCTION_READY` additionally
requires enacted runtime, rule, security, recovery, operational, score, and
authority evidence. Neither tier is currently declared.
After a Tier 1 pass, ordinary authorized product commits may advance on a
clean descendant without circularly revoking admission only while the governed
design/control manifest remains byte-identical; every such commit still uses
the normal per-work controls.

## Read in this order

1. [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md)<br>
   The core product-to-production process: governance, discovery,
   requirements, design, planning, implementation, verification, release,
   operation, improvement, risk lanes, decision rights, measurable flow, and
   evidence-bound capability assessment and improvement priority.
   Its executable stage contracts and stable controls are in the
   [SDLC Control Catalog](./SDLC_CONTROL_CATALOG.md).
   The owner decision making this established SDLC primary and AI work
   subordinate is [ADR-0001](./decisions/ADR-0001-established-sdlc-governs-ai-work.md).

2. [Ranex Engineering Reference Application Map](./ENGINEERING_REFERENCE_APPLICATION_MAP.md)<br>
   Makes SWEBOK and every frozen saved engineering book a major, named input to
   requirements, architecture, file structure, construction, verification,
   operation, and improvement while preserving the Core-SDLC authority
   hierarchy. Applicable practices must change the work and its verification,
   not merely appear in a citation list.

3. [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md)<br>
   The complete target map: product boundaries, bounded contexts, ownership,
   source tree, dependencies, state, effects, security, operations, migration,
   upstream sync, exclusions, and acceptance gates.
   Its accepted closure is recorded by
   [ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md);
   initial quality/SLO/RPO/RTO/security/retention targets by
   [ADR-0004](./decisions/ADR-0004-establish-initial-quality-attribute-baselines.md);
   local/static defaults and substitution gates by
   [ADR-0005](./decisions/ADR-0005-select-local-static-orchestration-defaults.md);
   and the machine-checkable 29-decision crosswalk by
   [ADR-0006](./decisions/ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md).
   The canonical modular-DDD repository organization is fixed by
   [ADR-0007](./decisions/ADR-0007-establish-modular-ddd-repository-organization.md),
   and production-path TDD is the default through
   [ADR-0008](./decisions/ADR-0008-make-tdd-the-default-development-discipline.md).
   Exact dependency edges, per-context boundary fit, governed-execution
   coupling triggers, and feedback fitness are fixed by
   [ADR-0009](./decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md).
   The exact inherited Hermes test baseline, its no-expansion compatibility
   boundary, file-by-file migration proof, expiry, and cutover gate are fixed by
   [ADR-0010](./decisions/ADR-0010-bound-inherited-hermes-test-layout-migration.md).
   Ranex-only cross-worker orchestration, role-scoped task-minimal grants,
   leaf-only official runtime adapters, one explicit no-fallback route, strict
   session affinity, and Hermes/Nous inference decommissioning are fixed by
   [ADR-0011](./decisions/ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md).
   The noncompensating separation between implementation-start and production
   readiness, including the bounded pre-readiness tooling tracer, is fixed by
   [ADR-0012](./decisions/ADR-0012-separate-implementation-start-and-production-readiness.md).
   The exact line-bound promotion of Hermes architecture research obligations,
   blocking owner-choice records, and research-only dispositions is fixed by
   [ADR-0013](./decisions/ADR-0013-promote-hermes-research-obligations.md).
   The implementation language, the required static type-checking gate, and the
   measured-budget-breach path for compiled components are fixed by
   [ADR-0014](./decisions/ADR-0014-fix-the-implementation-language-and-performance-escape-hatch.md).

4. [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md)<br>
   Defines authority, evidence, machine contracts, conflicts, RFC/ADR changes,
   and how sliced delivery preserves the full map.

5. [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md)<br>
   Defines roles, packets, handoffs, independent review, verification, permits,
   landing, post-landing checks, and definition of done. It is the governed
   execution subprocess inside the core SDLC.

6. [AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md)<br>
   Defines the Ranex-owned scheduler/dispatcher, typed leaf assignments,
   immutable role ceilings and exact task-minimal grants, one locked
   provider/model/runtime/auth route, official typed runtime adapters,
   session-affine reuse, fenced leases, liveness, cancellation, actual
   tool-surface enforcement, handoffs, measurement, and recovery. Workers
   cannot spawn, delegate to, coordinate, or reroute another model worker.

7. [Claude Runtime, Hermes, and OpenCode HY3 Reconciliation](./reviews/2026-07-29-claude-runtime-hermes-opencode-reconciliation.md)<br>
   Separates pinned Hermes implementation facts from current official Claude
   and Codex runtime/auth/legal facts, records the adversarial HY3 review, and
   identifies which conclusions are accepted owner decisions, evidence-backed
   facts, inferences, or still unqualified unknowns.

8. [AI-Work Artifact Contract Specification](./AI_ARTIFACT_CONTRACTS.md)<br>
   Defines exact subjects, Core-SDLC traceability, canonical digests, review
   separation, gate/decision/permit ordering, artifact producers, and the full
   target schema family.

9. [DeepSeek V4 Pro and HY3 Full-Map Review](./reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md)<br>
   Records the model collaboration, evidence corpus, limitations, and material
   changes introduced through reconciliation.

10. [Kimi Agent-Fleet Research Reconciliation](./reviews/2026-07-27-kimi-agent-fleet-research-reconciliation.md)<br>
   Records the complete 89-file addendum inventory, evidence defects, and the
   accepted, translated, rejected, or R&D-only disposition of its fleet
   recommendations.

11. [Foundational Reference Corpus Reconciliation](./reviews/2026-07-27-foundational-reference-corpus-reconciliation.md)<br>
    Records how the six saved software-engineering works were inspected and
    applied as major references, their extraction limits, and the
    public-distribution blocker on the twelve local full-text artifacts.

12. [Hermes Initial Runtime Acceptance](./reviews/2026-07-28-hermes-initial-runtime-acceptance.md)<br>
    Records the exact installed Hermes source/configuration subject, real
    route and browser evidence, independent reviews, backup/restore proof,
    bounded-use acceptance, non-claims, and the next authority-contract closure
    sprint. It is historical exact-subject evidence, not authority for a live
    Hermes/Nous inference route after ADR-0011.

13. [SDLC-FORK-000 deterministic preflight](./reviews/2026-07-28-sdlc-fork-000-preflight.md)<br>
    Binds current remotes, refs, ancestry, license/provenance, worktree, and
    hosting facts. Its current exact-subject result is `BLOCKED`; the bootstrap
    subject is not upstream-derived and is not a runtime implementation base.

14. [`templates/`](./templates/)<br>
   Provisional example shapes for architecture, task, handoff, review,
   evidence, authority, per-control capability assessment, immutable domain
   projection, release/operation, RFC, and ADR contracts. They do not become
   executable schemas until `AI-G2` passes.

## Scope rule

The architecture is a full-system specification, not an MVP or prototype map.
Implementation slices are routes through the architecture. They may leave mapped
capabilities inactive, but they may not leave their final owners and attachment
points undefined.

## Authority rule

The accepted Core SDLC governs how work moves from need to operated outcome.
The full-system architecture and ADRs govern what Ranex is and where authority
lives. Machine contracts are executable projections of both and cannot
semantically override either. AI agents are bounded workers; model output is
advisory. Runtime claims require runtime evidence.

Ranex control services are the only cross-worker orchestrator, scheduler,
dispatcher, fan-out owner, and join owner. Each model or harness is one leaf
worker on one immutable assignment. The assignment starts with no tools and
binds an exact task-minimal proper subset of its role ceiling plus one explicit
provider/model/transport/runtime/auth route; fallback, auxiliary model calls,
provider subagents, worker delegation, and route mutation are disabled. The
qualified hot path uses a release-pinned official typed runtime adapter, not a
Hermes parent-agent loop, Markdown terminal skill, shell/PTY/tmux scraper, or
native credential imitation. Connected-client reuse is restricted to the same
complete assignment/session-affinity key and remains unqualified until measured.
Hermes is provenance, frozen characterization, and non-inference compatibility
input only.

The only canonical bounded-context path is `src/ranex/<context>/`.
`src/ranex/contexts/<context>/` is not an alternative layout.
Ports live only in `src/ranex/<context>/application/ports/`.
Context-exclusive adapters live below that context; central
`src/ranex/adapters/<boundary>/<technology>/` paths require a registered
`HOST_EDGE_ADAPTER` exception. Empty layers and copied boilerplate do not prove
modularity.

Cross-context code imports only the target context's public `api`; private
domain/application/port/adapter imports, dependency cycles, import-time
effects, shared-table shortcuts, and alternate composition roots are
prohibited. Tests mirror the owning context. Semantic path ownership is
machine registered and generates review/package-discovery projections;
CODEOWNERS is not semantic authority.

The 67 approved public-API source edges are deny-by-default and acyclic.
Actual imports must be their subset. Every one of the 34 registered contexts
has an owned boundary-fit hypothesis, merge/split alternative, and tracer
falsifier. `governed_execution` remains the atomic authority cell while six
responsibility/fan-in/fan-out/interaction/change/ownership measures trigger
review when central coupling grows; no trigger automatically mandates a
microservice or split.

## TDD rule

TDD is the default production discipline:
acceptance/risk/failure model → RED → GREEN → REFACTOR → architecture check.
Each task binds one canonical `TddCycleRecordV1` with one exact base/candidate,
ordered step snapshots/results, complete test/failure denominator manifests,
and one built content-digested artifact/profile for all gate-bearing lanes.
Test-only business branches, alternate reducers, weakened controls, subject
mocks, and bypass composition are invalid. Determinism enters only through
declared ports; every fake needs parity plus representative real adapter proof,
and persistence proof uses ephemeral real SQLite with production migrations.

Cycle, TDD-exception, flaky-quarantine, and obsolete-test deletion instances
come only from the four canonical stores under
`architecture/records/test-health/` and their separately content-bound
registries. Profiles contain reconciled IDs, not inline authority. Runtime
evidence, gate, review, and approval references are typed objects resolved to
qualified exact-subject canonical artifacts. Active or expired-unclosed
quarantine blocks; exception lifecycle and test retirement are causal,
expiring/governed, immutable-history transitions. A legacy source or canonical
test may retire only through `TestDeletionRecordV1`, with exact Git delta,
trace/risk/cleanup, successor-or-N/A lineage, and globally nonreused retired
IDs. The initial instance sets are empty.

The only top-level test roots are `unit`, `contract`, `integration`,
`architecture`, `acceptance`, `system`, `e2e`, `security`, `performance`,
`resilience`, `migration`, `replay`, `operations`, `qualification`,
`effectiveness`, `evaluation`, `fixtures`, and `builders`.
`tests/persistence` maps to an owning context's integration/migration lane;
`tests/crash` maps to resilience. Every capability evaluates the complete
ADR-0008 failure matrix; closed transition spaces are exhaustive, while open
spaces use declared partitions/properties and reproducible property/model/
fuzz/mutation/fault evidence. Material `UNKNOWN` blocks and
`NOT_APPLICABLE` requires evidence. Coverage, counts, ratios, mutation
percentages, and green rates never compensate for a missing or failed
obligation.

The accepted upstream-derived source also contains an explicitly bounded
inherited test layout; this is not a 19th taxonomy root or a silent exception.
ADR-0010 binds all 2,444 baseline file bytes, exactly 29 directory exception
rows, 134 direct files, and 16 inherited files already under canonical roots.
Those files may run unchanged as nonsealing regression evidence. No new Ranex
test or unregistered path/content change may enter their scope, and every
migration or retirement needs its separate exact authority. Expiry or any failed,
unknown, or conflicting legacy-test rule blocks construction verification.
Change, migration/removal, and cutover/removal source records live only under
the three ADR-0010 directories below
`architecture/records/legacy-test-layout/` and project to the content-bound
`legacy-test-layout-records.json`. The initial record set is empty. Only a
valid active/accepted record can authorize its exact subject, and the validator
rejects unused/omitted records and independently recomputes cutover.
Change subjects are path-local; migration proofs are immutable ordered
MIGRATED-only atomic groups over the inherited-disposition state; direct legacy
or later canonical retirement resolves through the ADR-0008 deletion registry.
Every event's before commit equals the full derived ledger and its exact
after-before `tests` delta contains only named operations. Evidence/decisions
are typed, current, role-qualified, causal, and bound with a successful
commit-preserving landing. Validation reads one committed Git subject and
rejects dirty-checkout mixing. Cutover freezes an event-time snapshot/lineage,
then later ordinary canonical evolution is allowed while current zero-legacy
and ACTIVE/RETIRED lineage remain valid. Every migration and cutover acceptance
and landing completes by policy expiry; post-expiry work cannot cure an
unfinished cutover. Only a cutover fully accepted and landed by expiry remains
valid historical proof afterward.

## Event and element exactness rule

The 40 initial events are closed `DomainEventEnvelopeV1` contracts, not names:
each has one owner/producer, consumers, trigger/preconditions, typed/versioned
payload, aggregate/source version, correlation/causation/idempotency,
aggregate ordering and at-least-once inbox/outbox behavior,
privacy/retention, compatibility/upcast, and failure/replay semantics in
architecture §17. Their definitions are contract-ready; runtime emission and
replay remain `NOT_ASSESSED`. `DEFINED_NAME_ONLY` blocks
`IMPLEMENTATION_START_READY`; explicit runtime `NOT_ASSESSED` remains permitted
at that tier but blocks `PRODUCTION_READY`.

Every one of the 1,008 current architecture elements binds its complete canonical
definition row, RFC 8785 row digest, full source-file digest, and semantic
parent elements. State values bind their state axis; artifacts bind their
schema row; paths, edges, boundaries, events, and rules bind full registry
rows. Per-element assessments exact-subject those bindings. No name/owner-only
projection or numeric score can establish definition or runtime conformance.

Fast-loop objectives are p50 ≤ 60 seconds and p95 ≤ 180 seconds; required
pre-verification objectives are p50 ≤ 10 minutes and p95 ≤ 20 minutes on the
declared reference host and exact candidate artifact. Selection follows owner,
dependency closure, risk, failure matrix, and always-run authority/security
sets. Shards derive deterministically from test ID and suite version. Failure,
unknown, flake, changed edge, migration, or elevated risk only escalates lanes;
speed never authorizes omission.

The former root implementation guide was deleted and retired by
[ADR-0002](./decisions/ADR-0002-retire-legacy-implementation-guide.md). It must
not be restored or used from history, another branch, research quotations, or
review artifacts. New implementation sequencing comes from governed work items
and the routes in the full-system architecture.

## Engineering-practice rule

The ten manifested foundational works are operational practice inputs. At `AI-G2`, their
accepted synthesis becomes a machine-registered engineering-practice catalog.
Every architecture and implementation packet binds an exact applicability
profile, required behavior, deviations, and verification evidence. A packet
does not satisfy this rule by naming a book without demonstrating how an
applicable practice affected the work.

The exact
[architecture-design practice application profile](../research/ranex-architecture-practice-application-profile.json)
binds all ten registered source families and 38 practices: 37 applicable and
one scoped N/A, with every applicable design practice mapped and no arithmetic
score. It is deliberately nonsealing: all 37 applicable runtime outcomes
remain `NOT_ASSESSED`.

The reference map's §3, §5.1–§5.4, §6, §8, and §10 are the precise advisory
locators used by ADR-0003 through ADR-0011. Edition age, excerpt scope,
transcription quality, opinionated examples, and incomplete standards coverage
remain limitations. Only registered, manifested, reviewed references enter a
profile; new local book artifacts are excluded until provenance/rights, source
identity, limitations, and applicability are reviewed. No book is decision
authority.

## Assessment standing

The Core SDLC requires a separate immutable `CapabilityAssessment` for every
applicable control/capability and forbids a compensating overall score. The 29
fixed decisions have alternatives and fitness functions, not invented
achievement scores. Until schema-valid assessments bind enacted/runtime
evidence, their honest current result is `NOT_ASSESSED` (or `UNKNOWN` after an
insufficient evidence attempt), with no numeric level. Documentation alone
cannot exceed the rubric's `DEFINED` (`1`) level and does not award it
automatically.

ADR-0007 adds 18 separately evaluated `ORG-*` rules and eight `FF-ORG-*`
fitness obligations. ADR-0008 adds 26 separately evaluated `TDD-*` rules and
13 `FF-TDD-*` fitness obligations. ADR-0009 adds ten dependency/boundary/
coupling/feedback rules and nine fitness obligations. ADR-0010 adds ten
inherited-test-layout rules and nine fitness obligations for immutable
baseline binding, no expansion/drift, canonical placement, migration proof,
expiry, and cutover. ADR-0011 adds eight noncompensating fitness obligations
for leaf containment, task-minimal role grants, official structured runtimes,
no fallback/auxiliary calls, session affinity, measured dispatch performance,
effective auth-route verification, and Hermes/Nous decommissioning. Its role
and runtime registries are definition-only and do not add rows to the separate
64-rule ADR-0007–ADR-0010 assessment denominator. ADR-0012 adds six
readiness-tier fitness obligations and a separate 21-gate readiness catalog;
it does not silently add to or average the 64 runtime rule rows. Each applicable item needs
its own exact subject, result, evidence, freshness, owner, and
exception/N/A basis; none may borrow a passing score from another item or from
book alignment. Their current source/runtime conformance is `NOT_ASSESSED`,
not “mostly ready,” and there is no architecture-wide percentage or maturity
average. The 64 rule rows are bound by
`architecture/contracts/architecture-rule-assessments.json` under
`schemas/common/architecture-rule-assessment-v1.schema.json`.
Its `noncompensating_summary` reports denominators/blocking states only and has
no independent score or `PASS` authority.

The canonical readiness states are `IMPLEMENTATION_START_READY` (documentation
label `DESIGN_DEFINITION_READY`) and `PRODUCTION_READY` (documentation label
`ENTERPRISE_RUNTIME_READY`). Runtime results and maturity scores may remain
explicitly `NOT_ASSESSED`/null for the first tier; they block the second.
Each gate retains its native evidence subject through an exact ADR-0012 bridge
to a closed readiness subject and manifest; cross-subject relabeling is
forbidden. Neither state has a current assessment or authorization.

The separate architecture-element ledger covers all 1,008 current elements.
Definition dispositions describe book/practice traceability and exact
definition closure: 191 `DIRECT`, 30 `INHERITED_FROM_PROFILE`, 346
`INHERITED_FROM_RULE`, and 441 `INHERITED_FROM_OWNER`, with zero
`NOT_APPLICABLE`, `UNKNOWN`, unclassified, cyclic, or multiply parented rows.
They are not achievement scores. Every runtime result is still
`NOT_ASSESSED`.

## Research inputs

Every file present in the content-addressed research manifests is a required
architecture input. This avoids the false claim that a live directory glob is
the same frozen subject when new files arrive during review. Research informs
the architecture but does not silently override it.
The current worker-runtime boundary and Hermes claims are reconciled in
[Claude Runtime, Hermes, and OpenCode HY3 Reconciliation](./reviews/2026-07-29-claude-runtime-hermes-opencode-reconciliation.md),
which binds the pinned Hermes source subject and current official Claude/Codex
documentation while keeping model review advisory.
The evidence basis for the core process is
[Real-world software-development operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md).
The later Kimi fleet corpus is bound by
[`kimi-research-manifest.sha256`](./reviews/artifacts/2026-07-27/kimi-research-manifest.sha256).
The historical 2026-07-27 six-work snapshot, represented by twelve local
PDF/Markdown artifacts, is bound by
[`foundational-reference-corpus-manifest.sha256`](./reviews/artifacts/2026-07-27/foundational-reference-corpus-manifest.sha256)
and remains an immutable prior review subject. The current live corpus contains
ten works represented by 18 artifacts and is bound by the
[`2026-07-28 live-corpus manifest`](./reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus.sha256)
and
[`work/representation index`](./reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus-index.json).
It is applied through the
[Engineering Reference Application Map](./ENGINEERING_REFERENCE_APPLICATION_MAP.md).
The full-text artifacts are consultation-only `LOCAL_ONLY` inputs and must not
enter the public Git index, package, or release without documented rights; the
manifest, lawful bibliographic links, original synthesis, and non-reconstructive
digests are the public-safe substitute.

### Non-normative research addenda

The
[Spec Kit selective-adaptation reconciliation](./reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md)
compares pinned `github/spec-kit` interaction, workflow, ecosystem, and
artifact-evolution patterns with Ranex's accepted attachment points. It
preserves the raw independent HY3/DeepSeek reviews while correcting their
claims against primary sources. It recommends a measured Ranex-native
intake-to-convergence experiment, but adopts no feature, artifact, integration,
extension, workflow, authority, runtime claim, or commercial-value claim.
[RFC-0002](./rfcs/RFC-0002-selective-spec-kit-adaptation.md) is the corresponding
`DRAFT` proposal and remains non-authoritative.

The
[APOSD, agent-rule, and codebase-design assessment](../research/aposd-agent-rules-codebase-design-assessment-2026-07-28.md)
and its
[advisory reconciliation](./reviews/2026-07-28-aposd-agent-rules-skills-reconciliation.md)
are content-addressed `RESEARCH_ONLY` inputs. Their
[addendum manifest](./reviews/artifacts/2026-07-28/aposd-agent-rules-skills/research-addendum-manifest.sha256)
binds the public-safe assessment and `DRAFT` experiment artifacts. The separate
live-corpus reconciliation registers the primary APOSD book as the tenth source
family with four definition-layer practices, bringing the design registry to
38. The addendum does not install or activate either third-party skill/rule
pack, register the seven-question treatment, establish runtime
conformance/effectiveness, or authorize construction, merge, or release.
