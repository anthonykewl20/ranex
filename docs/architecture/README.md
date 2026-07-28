# Ranex Architecture Documentation

This directory is the normative architecture base for rebuilding Hermes into
Ranex.

The target architecture is accepted as a paper construction contract by
[ADR-0003](./decisions/ADR-0003-accept-target-architecture-and-authority-kernel.md).
That is not a build-readiness or runtime-pass claim: `SDLC-FORK-000`, executable
registries/schemas at `AI-G2`, exact-subject `MAP-*` evaluations, and the
applicable implementation, security, recovery, and operating gates remain
separate prerequisites.

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

4. [Source of Truth and Decision Policy](./SOURCE_OF_TRUTH.md)<br>
   Defines authority, evidence, machine contracts, conflicts, RFC/ADR changes,
   and how sliced delivery preserves the full map.

5. [AI-Agent Development Lifecycle](./AI_AGENT_DEVELOPMENT_LIFECYCLE.md)<br>
   Defines roles, packets, handoffs, independent review, verification, permits,
   landing, post-landing checks, and definition of done. It is the governed
   execution subprocess inside the core SDLC.

6. [AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md)<br>
   Defines typed assignment, fenced leases, liveness, governor limits,
   topology/concurrency, transitive budgets, tool-boundary enforcement,
   handoffs, verifier backpressure, measurement, and recovery. It controls
   workers without creating a second SDLC.

7. [AI-Work Artifact Contract Specification](./AI_ARTIFACT_CONTRACTS.md)<br>
   Defines exact subjects, Core-SDLC traceability, canonical digests, review
   separation, gate/decision/permit ordering, artifact producers, and the full
   target schema family.

8. [DeepSeek V4 Pro and HY3 Full-Map Review](./reviews/2026-07-27-deepseek-v4-pro-hy3-full-map-review.md)<br>
   Records the model collaboration, evidence corpus, limitations, and material
   changes introduced through reconciliation.

9. [Kimi Agent-Fleet Research Reconciliation](./reviews/2026-07-27-kimi-agent-fleet-research-reconciliation.md)<br>
   Records the complete 89-file addendum inventory, evidence defects, and the
   accepted, translated, rejected, or R&D-only disposition of its fleet
   recommendations.

10. [Foundational Reference Corpus Reconciliation](./reviews/2026-07-27-foundational-reference-corpus-reconciliation.md)<br>
    Records how the six saved software-engineering works were inspected and
    applied as major references, their extraction limits, and the
    public-distribution blocker on the twelve local full-text artifacts.

11. [Hermes Initial Runtime Acceptance](./reviews/2026-07-28-hermes-initial-runtime-acceptance.md)<br>
    Records the exact installed Hermes source/configuration subject, real
    route and browser evidence, independent reviews, backup/restore proof,
    bounded-use acceptance, non-claims, and the next authority-contract
    closure sprint.

12. [SDLC-FORK-000 deterministic preflight](./reviews/2026-07-28-sdlc-fork-000-preflight.md)<br>
    Binds current remotes, refs, ancestry, license/provenance, worktree, and
    hosting facts. Its current exact-subject result is `BLOCKED`; the bootstrap
    subject is not upstream-derived and is not a runtime implementation base.

13. [`templates/`](./templates/)<br>
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
Gate-bearing lanes test one built, content-digested production artifact and
profile. Test-only business branches, alternate reducers, weakened controls,
subject mocks, and bypass composition are invalid. Determinism enters only
through declared ports; every fake needs parity plus representative real
adapter proof, and persistence proof uses ephemeral real SQLite with
production migrations.

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

The six foundational works are operational practice inputs. At `AI-G2`, their
accepted synthesis becomes a machine-registered engineering-practice catalog.
Every architecture and implementation packet binds an exact applicability
profile, required behavior, deviations, and verification evidence. A packet
does not satisfy this rule by naming a book without demonstrating how an
applicable practice affected the work.

The exact
[architecture-design practice application profile](../research/ranex-architecture-practice-application-profile.json)
binds all nine registered source families and 34 practices: 33 applicable and
one scoped N/A, with every applicable design practice mapped and no arithmetic
score. It is deliberately nonsealing: all 33 applicable runtime outcomes
remain `NOT_ASSESSED`.

The reference map's §3, §5.1–§5.4, §6, §8, and §10 are the precise advisory
locators used by ADR-0003 through ADR-0009. Edition age, excerpt scope,
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
fitness obligations. ADR-0008 adds 19 separately evaluated `TDD-*` rules and
eight `FF-TDD-*` fitness obligations. ADR-0009 adds ten dependency/boundary/
coupling/feedback rules and nine fitness obligations. Each applicable item
needs its own exact subject, result, evidence, freshness, owner, and
exception/N/A basis; none may borrow a passing score from another item or from
book alignment. Their current source/runtime conformance is `NOT_ASSESSED`,
not “mostly ready,” and there is no architecture-wide percentage or maturity
average. The 47 rule rows are bound by
`architecture/contracts/architecture-rule-assessments.json` under
`schemas/common/architecture-rule-assessment-v1.schema.json`.
Its `noncompensating_summary` reports denominators/blocking states only and has
no independent score or `PASS` authority.

## Research inputs

Every file present in the content-addressed research manifests is a required
architecture input. This avoids the false claim that a live directory glob is
the same frozen subject when new files arrive during review. Research informs
the architecture but does not silently override it.
The evidence basis for the core process is
[Real-world software-development operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md).
The later Kimi fleet corpus is bound by
[`kimi-research-manifest.sha256`](./reviews/artifacts/2026-07-27/kimi-research-manifest.sha256).
The six saved foundational works, represented by twelve local PDF/Markdown
artifacts, are bound by
[`foundational-reference-corpus-manifest.sha256`](./reviews/artifacts/2026-07-27/foundational-reference-corpus-manifest.sha256)
and applied through the
[Engineering Reference Application Map](./ENGINEERING_REFERENCE_APPLICATION_MAP.md).
Those twelve full-text artifacts are consultation-only `LOCAL_ONLY` inputs and
must not enter the public Git index, package, or release without documented
rights; the manifest, lawful bibliographic links, original synthesis, and
non-reconstructive digests are the public-safe substitute.
