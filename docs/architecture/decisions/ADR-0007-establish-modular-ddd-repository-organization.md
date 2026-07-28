# ADR-0007: Establish Modular-DDD Repository Organization

| Field | Value |
|---|---|
| ADR ID | `ADR-0007` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a67843b02d5970f442fb54aed8d6525dda`; executable projection and enactment pending |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | Entire repository, every bounded context, adapters, tests, schemas, migrations, deployment, tooling, documentation, and compatibility code |
| Supersedes | No ADR; narrows and completes architecture §§11–13 |
| Review/expiry date | First contract-registry projection, first target context tracer, then on topology/ownership change |
| Compatibility/migration class | Target organization with strangler quarantine for inherited Hermes layout |
| Security/data class | Public architecture decision |

## Decision

Ranex uses a modular monolith whose primary organizing unit is the owned
bounded context, not a framework, adapter technology, horizontal “services”
folder, or model/tool vendor. The canonical context path remains:

```text
src/ranex/<context>/
```

The package name makes product/domain intent visible. The architecture
registries, not directory inference, decide which names are bounded contexts.
Folder count does not prove modularity, and every context does not need every
optional folder.

## Canonical repository topology

```text
ranex/
├── src/ranex/
│   ├── foundation/                 # semantics-light shared primitives
│   ├── <context>/                  # one registered bounded context
│   ├── modules/                    # first-party capability modules
│   ├── adapters/                   # multi-context/host-edge adapters only
│   ├── compatibility/              # anti-corruption boundary only
│   ├── bootstrap/                  # composition root and startup
│   └── migration/                  # cross-context migration ordering
├── apps/                           # delivery applications; no authority rules
├── architecture/contracts/         # owner-authored semantic registries
├── architecture/generated/         # generated projections; never hand edited
├── schemas/<owning-area>/           # canonical wire/artifact schemas
├── packages/generated-contracts/   # generated language bindings
├── tests/                           # ADR-0008 taxonomy, mirroring owners
├── config/                          # release-pinned declarative profiles
├── deploy/                          # declarative packaging/install/host assets
├── docs/
│   ├── architecture/               # normative architecture and specifications
│   │   ├── decisions/              # ADRs
│   │   └── rfcs/                   # non-accepted proposals
│   ├── research/                   # evidence/advice, never authority
│   └── operations/                 # tested runbooks
├── scripts/                        # thin public-API operator/CI clients
├── tools/                          # build, contract generation, validation
├── legacy/hermes/                  # optional post-parity frozen source home
└── legal/                          # license, provenance, SBOM policy
```

Production domain/application behavior lives only below `src/ranex`. `apps`,
`scripts`, `deploy`, and `tools` cannot become alternate business-rule homes.
Configuration that changes behavior remains versioned, schema-validated, owned,
and tested.

## Bounded-context internal contract

```text
src/ranex/<context>/
├── __init__.py
├── README.md                 # vocabulary, owner, invariants, navigation
├── contract.yaml             # generated/validated context-registry projection
├── api/                      # sole cross-context import surface
├── domain/                   # aggregates, value objects, domain events/rules
├── application/              # use cases, command/query handlers
│   └── ports/                # repositories and external capability protocols
└── adapters/                 # optional context-exclusive port implementations
```

Only folders required by enacted behavior are created. `contract.yaml` is a
projection of the canonical registries, not a second hand-maintained source.
A context that has no local adapter does not receive an empty `adapters/`;
shared host mechanics do not justify identical boilerplate in every context.

### Placement rules

| Concept | Canonical placement | Rule |
|---|---|---|
| Aggregate/root/entity | `<context>/domain/<domain_concept>.py` or a cohesive domain subpackage | Aggregate root owns invariants and legal mutation; one aggregate transaction does not imply cross-context atomicity |
| Value object | Co-located with its sole aggregate or `<context>/domain/<concept>.py` when reused inside that context | Immutable and validated at construction; never a database/wire model |
| Domain service | `<context>/domain/<named_domain_operation>.py` | Pure domain decision spanning concepts; no I/O, repository, clock read, policy client, or orchestration |
| Application use case | `<context>/application/<verb_noun>.py` or a cohesive use-case subpackage | Orchestrates domain objects and ports; owns no adapter/framework rule |
| Repository/capability port | `<context>/application/ports/<owned_capability>.py` | Protocol expressed in owner language; application owns it, adapter implements it |
| Public command/query/event/view | `<context>/api/` | Stable, versioned, immutable boundary type; the only source import permitted from another context |
| Context-exclusive adapter | `<context>/adapters/<technology>/` | Translates external/ORM/wire types and implements one or more named local ports |
| Multi-context or host-edge adapter | `src/ranex/adapters/<boundary>/<technology>/` | Allowed only when the integration is genuinely shared or is a delivery/composition edge; contains no domain rule |
| Persistence row/ORM model | Owning persistence adapter | Never imported by domain/API consumers |
| Integration event/outbox mapping | Owner API plus owner persistence adapter | Event schema is public; durable mapping/outbox mechanics remain adapter-owned |

A “domain service” is not a home for miscellaneous logic. A use case is not a
god orchestrator. Split a module when it has multiple owners/reasons to change,
mixes public/private responsibilities, creates a forbidden dependency, or
cannot be tested through a narrow contract. Ranex adopts no arbitrary
lines-per-file, classes-per-folder, or one-type-per-file gate.

## Dependency and import rules

Allowed source dependencies point inward:

```text
foundation
    ^
domain
    ^
application + application/ports
    ^
api and adapters
    ^
bootstrap/apps
```

More precisely:

1. `foundation` uses the standard library and semantics-light registered
   primitives only. Moving knowledge there requires consumer/ownership review.
2. A context's `domain` imports only its own domain and `foundation`.
3. Its `application` imports its own `domain`, `application/ports`,
   `foundation`, and another context's public `api` only when the registered
   dependency permits it.
4. Its `api` may expose owner-defined DTOs/enums and immutable views; it does
   not export domain mutability, ORM objects, adapter types, or service
   locators.
5. Adapters import their implemented port and public owner types. An adapter
   never imports another adapter.
6. Cross-context imports target exactly `ranex.<other>.api...`; private
   `domain`, `application`, `ports`, and `adapters` imports are forbidden.
7. The actual import graph and declared context graph are acyclic. A necessary
   interaction cycle is broken through an owned integration event, a query/API
   redesign, or an explicit higher-level orchestration context—not a hidden
   private import.
8. Imports perform no network, database, filesystem mutation, process spawn,
   registration, migration, environment-dependent decision, or other effect.
9. `bootstrap/composition.py` is the sole product composition root that reads
   the active release profile and constructs concrete implementations. Context
   factories may assemble internal objects but cannot select global policy,
   routes, credentials, or alternate business behavior.

No test, script, module, extension, or compatibility path receives a broader
dependency rule than production code.

## Cross-context state and messaging

- A context owns its aggregates, tables, migrations, public contracts, and
  integration events even when SQLite is physically shared.
- Synchronous calls use the owning context's public API and remain outside the
  callee's transaction.
- State-change propagation uses versioned integration events, a transactional
  owner outbox, idempotent consumers, correlation/causation IDs, and explicit
  duplicate/out-of-order/reconciliation behavior.
- Cross-context database reads/writes, foreign repository use, shared mutable
  models, and distributed-transaction assumptions are prohibited.
- `governed_execution` remains the specifically documented authority-cell
  consistency boundary; its centrality does not authorize knowledge or writes
  owned by another context.

## Tests, schemas, generated artifacts, and migrations

- Tests mirror source ownership under the ADR-0008 roots. Unit paths include
  `tests/unit/<context>/domain/` and
  `tests/unit/<context>/application/`; contract/integration paths name the
  owning context and port/adapter.
- Canonical semantic registries live in `architecture/contracts`; JSON Schema
  lives once under `schemas/<owning-area>`; generated bindings live under
  `packages/generated-contracts`; generated documentation lives under
  `architecture/generated` or an explicitly generated docs subtree.
- Generated outputs carry generator/input digests and are not hand edited.
  Drift, duplicate definitions, missing owner, and schema/API incompatibility
  fail validation.
- Context-owned SQLite migrations live with the owning persistence adapter,
  normally
  `src/ranex/<context>/adapters/persistence/sqlite/migrations/`.
  `src/ranex/migration` owns only ordering, compatibility, application,
  verification, and rollback across those manifests.
- Shared SQLite connection/transaction mechanics may live in a named platform
  adapter; they cannot own context table definitions or silently coordinate
  cross-context writes.

## Operations, deployment, tooling, and documentation

- `deploy/` contains declarative package/install/service/host-profile assets.
  Runtime behavior remains in production adapters and release management.
- `docs/operations/` contains versioned runbooks linked to tested commands and
  recovery evidence.
- `scripts/` contains thin authenticated clients of public APIs; no repository,
  adapter, secret, migration, or authority shortcut is permitted.
- `tools/` contains developer/build/codegen/validation programs and fixtures;
  it is not installed as product authority unless explicitly packaged behind a
  production port.
- Accepted decisions live only in `docs/architecture/decisions/`. RFCs live in
  `docs/architecture/rfcs/` and remain non-normative until an ADR accepts them.

## Ownership, discovery, naming, and navigation

The path registry assigns every governed path pattern:

- one semantic owner/context;
- one accountable human owner role and required reviewer role;
- allowed dependency edges and data classification;
- generated/manual/legacy status; and
- applicable topology/test rules.

That registry generates a CODEOWNERS-ready projection. CODEOWNERS may request
review but never becomes semantic ownership or transition authority.
Overlapping patterns with different owners are `CONFLICT`.

Python packaging discovers only explicit packages below `src/ranex`; tests,
docs, tools, `legacy`, worktrees, and generated TypeScript are excluded.
Context packages use `snake_case` registry IDs and explicit `__init__.py`
files. Import-time scanning/registration is prohibited; the release catalog
discovers modules/adapters from manifests at the composition root.

Names use domain or use-case language. Unqualified dumping grounds such as
`utils.py`, `common.py`, `helpers.py`, `manager.py`, and `service.py` fail
review unless the registry records one narrow responsibility. Every context
README links owner, vocabulary, public API, invariants, dependency diagram,
data/migrations, operations, and tests; it does not duplicate canonical
contracts.

## Compatibility and legacy quarantine

Inherited Hermes source remains in its upstream layout during the strangler.
Only `ranex.compatibility.hermes_legacy` may import it. After parity and
upstream-sync-cost evidence, a frozen subset may move to `legacy/hermes/`.
Neither location is part of package discovery for new Ranex code. New domain
rules, schemas, migrations, or shared helpers may not be added to legacy.

## Machine-checkable topology rules

The contract lane projects this exact rule set into the path/context
registries. `BLOCK` means a violating exact subject cannot pass architecture or
contract readiness.

```yaml
topology_rule_set: "RANEX-TOPOLOGY-1.0"
rules:
  - {id: "ORG-PATH-001", enforcement: "BLOCK", invariant: "Each registered context root is exactly src/ranex/<context>/."}
  - {id: "ORG-CONTEXT-001", enforcement: "BLOCK", invariant: "Every context has one owner, public API, contract projection, and no second semantic home."}
  - {id: "ORG-LAYER-001", enforcement: "BLOCK", invariant: "Domain/application/port/adapter files match the placement and inward-dependency rules."}
  - {id: "ORG-PUBLIC-001", enforcement: "BLOCK", invariant: "Cross-context source imports resolve only through the target context api package."}
  - {id: "ORG-DEPENDENCY-001", enforcement: "BLOCK", invariant: "Actual imports are a subset of registered allowed edges."}
  - {id: "ORG-CYCLE-001", enforcement: "BLOCK", invariant: "The context graph and source import graph are acyclic."}
  - {id: "ORG-IMPORT-001", enforcement: "BLOCK", invariant: "Imports are effect-free and do not perform runtime registration or configuration decisions."}
  - {id: "ORG-COMPOSE-001", enforcement: "BLOCK", invariant: "Only bootstrap/composition.py selects and wires concrete product implementations."}
  - {id: "ORG-MESSAGE-001", enforcement: "BLOCK", invariant: "Cross-context state propagation uses public APIs or registered integration events/outboxes, never table/repository sharing."}
  - {id: "ORG-PERSIST-001", enforcement: "BLOCK", invariant: "Each table and migration has one context owner; shared persistence mechanics own no domain schema."}
  - {id: "ORG-TEST-MIRROR-001", enforcement: "BLOCK", invariant: "Every production owner has tests in an ADR-0008 allowed root with matching context/layer metadata."}
  - {id: "ORG-GENERATED-001", enforcement: "BLOCK", invariant: "Schemas and generated artifacts have one semantic source, generator/input digests, and zero hand-edit drift."}
  - {id: "ORG-MIGRATION-001", enforcement: "BLOCK", invariant: "Context migrations are owner-local and cross-context ordering is explicit, tested, and reversible."}
  - {id: "ORG-LEGACY-001", enforcement: "BLOCK", invariant: "Only the compatibility boundary imports inherited/legacy roots; new Ranex packages never do."}
  - {id: "ORG-OWNERSHIP-001", enforcement: "BLOCK", invariant: "Every governed path resolves to one CODEOWNERS-ready semantic owner and required reviewer."}
  - {id: "ORG-DISCOVERY-001", enforcement: "BLOCK", invariant: "Package/module discovery is manifest-driven, side-effect-free, and excludes tests/docs/tools/legacy."}
  - {id: "ORG-NAV-001", enforcement: "REQUIRED", invariant: "Context README and registry links make owner, API, invariants, data, dependencies, operations, and tests findable."}
  - {id: "ORG-EXEMPTION-001", enforcement: "BLOCK", invariant: "Every topology exception is exact-path, exact-rule, owned, justified, time-bounded, and non-transitive."}
```

Allowed exception classes are only:

| Class | Scope |
|---|---|
| `FOUNDATION_PRIMITIVE` | Named semantics-light primitive with multiple valid context consumers |
| `BOOTSTRAP_COMPOSITION` | Concrete construction/configuration at the sole composition root |
| `HOST_EDGE_ADAPTER` | Genuinely multi-context delivery/platform adapter implementing named ports |
| `GENERATED_PROJECTION` | Non-hand-edited output with canonical source/generator digests |
| `COMPATIBILITY_QUARANTINE` | Exact inherited import required by the strangler, with removal trigger |

An exception records `exception_id`, exact paths/globs, rule IDs, owner,
rationale, allowed edges, security/data impact, approval, review/expiry, tests,
and removal condition. Wildcards that cover a whole layer, “temporary”
exceptions without expiry, and transitive exemptions are invalid.

### Examples

```text
ALLOWED:
ranex.work_management.application.transition_service
  -> ranex.policy.api.AuthorizationSnapshot

ALLOWED:
ranex.work_management.adapters.persistence.sqlite.WorkRepository
  implements ranex.work_management.application.ports.WorkRepository

FORBIDDEN:
ranex.delivery -> ranex.governed_execution.domain.run
ranex.policy.domain -> sqlalchemy
ranex.assurance.application -> ranex.routing.adapters.openrouter
tests -> alternate_test_only_reducer
```

## Fitness evidence

| ID | Required evidence |
|---|---|
| `FF-ORG-001` | Registered and actual paths agree; unknown/duplicate owners and misplaced packages fail. |
| `FF-ORG-002` | Static import graph proves allowed inward/public edges, no cycles/private imports, and no legacy leak. |
| `FF-ORG-003` | Import probes prove no filesystem/network/database/process/configuration side effect. |
| `FF-ORG-004` | Composition tests build each release profile from the sole root and reject missing/extra/ambiguous bindings. |
| `FF-ORG-005` | Contract and failure tests prove public API/event translation, duplicate/out-of-order handling, and no shared-table shortcut. |
| `FF-ORG-006` | Migration inventory maps every table/version to one owner and passes ordering, replay, rollback, and restore checks. |
| `FF-ORG-007` | Registry-to-CODEOWNERS/package-discovery/generated-doc projections are reproducible and drift-free. |
| `FF-ORG-008` | Representative changes remain local to the declared owner or expose an explicit architecture decision instead of hidden coupling. |

These are obligations. No current source tree or build is declared conformant.

## Engineering-reference application and limitations

This decision applies, without copying book text:

- `ENGREF-CLEAN-ARCHITECTURE-1E-USE-CASE-VISIBLE`,
  `ENGREF-CLEAN-ARCHITECTURE-1E-DEPENDENCY-RULE`,
  `ENGREF-CLEAN-ARCHITECTURE-1E-BOUNDARY-OPTIONS`, and
  `ENGREF-CLEAN-ARCHITECTURE-1E-ENCAPSULATION-AND-TESTABILITY` (the latter at
  the registered Clean Architecture representation, Ch.28 pp.192–193 and
  Ch.34 pp.230,235);
- `ENGREF-CLEAN-CODE-THIRD-PARTY-BOUNDARY` (Ch.8, lines 3128–3454) and
  `ENGREF-CLEAN-CODE-SEPARATE-CONSTRUCTION-RUNTIME` (Ch.11,
  lines 4098–4158);
- `ENGREF-CODE-COMPLETE-CH5-INFORMATION-HIDING` (retained Ch.5,
  lines 1273–1395) and
  `ENGREF-CODE-COMPLETE-CH5-MANAGE-COMPLEXITY`;
- `ENGREF-PRAGMATIC-PROGRAMMER-1E-ORTHOGONALITY` (lines 1393–1449) and
  `ENGREF-PRAGMATIC-PROGRAMMER-1E-DRY-AUTHORITATIVE-KNOWLEDGE`;
- `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-BOUNDARY-QUANTA`
  (lines 2608–2635),
  `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-ORCHESTRATION-COUPLING`
  (lines 4416–4508),
  `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-STYLE-AND-ADR`
  (lines 4740–4872 and 5044–5128), and
  `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS`
  (lines 700–716).

The references advise intent-visible boundaries, information hiding,
orthogonality, trade-off analysis, and continuous fitness checks. They do not
prove one folder taxonomy, DDD correctness, the selected context count, or a
microservice boundary. Clean Architecture needs explicit quality-attribute
trade-offs; FSA ratings are not Ranex scores; the retained Code Complete source
is Ch.5 only; Clean Code and Pragmatic examples are contextual and
edition-sensitive. Ownership, dependency, consistency, change-locality,
failure, security, data, and runtime evidence remain decisive.

## Alternatives considered

1. **Framework-first horizontal layers.** Rejected because product ownership
   and change locality disappear behind controllers/services/repositories.
2. **A universal deep template in every context.** Rejected because empty
   boilerplate and cargo-cult abstractions impede navigation.
3. **One shared domain/common package.** Rejected because semantic ownership
   and consistency boundaries become ambiguous.
4. **Package-per-microservice.** Rejected because process count is unrelated to
   the local-first quality attributes and adds distributed failure.
5. **Let tests/import conventions enforce structure without a registry.**
   Rejected because allowed exceptions and semantic ownership would be implicit.

## Consequences and migration

New target work uses this topology. Existing inherited paths remain quarantined
during the strangler. Existing Ranex files move only through an owned,
behavior-preserving migration with import/schema/test updates; no big-bang
cosmetic shuffle is required. Contract generation must validate this ADR
against the path/context registry before `AI-G2`. Until then the decision is
paper-contracted, not enacted.

## Human approval

The human owner required enterprise-grade modular-DDD organization without
framework cargo cult or needless boilerplate. This ADR records that target. It
is not runtime conformance evidence.
