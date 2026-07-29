# Ranex Engineering Reference Application Map

| Field | Value |
|---|---|
| Document ID | `MAP-ENG-REF-001` |
| Version | `1.3.0` |
| Status | `CONDITIONALLY_ACCEPTED` normative supporting map; runtime practice remains unvalidated |
| Date | 2026-07-28 |
| Owner and decision authority | Human governor |
| Scope | How the saved software-engineering books and SWEBOK materially shape the complete Ranex lifecycle, architecture, file structure, construction, verification, operation, and improvement system |
| Parent policy | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Parent architecture | [Hermes-to-Ranex Ground-Zero Full-System Architecture](./HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
| Control catalog | [Ranex SDLC Control Catalog](./SDLC_CONTROL_CATALOG.md) |
| Exact corpus | [Live foundational-reference corpus manifest](./reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus.sha256) and [work/representation index](./reviews/artifacts/foundational-reference-corpus/2026-07-28-live-corpus-index.json) |
| Corpus count/size | 18 files / 88,515,353 bytes; ten conceptual works, eight PDF/Markdown pairs, and two PDF-only works |
| Manifest SHA-256 | `638b0f70a0c84f54eee8e71e7ae3edd5253cf19eada2c707e3b1b4d13e6de7a0` |
| Corpus index SHA-256 | `54316a04405e47d96adbc9f80a4c2d30294ba886dd1f7923c74f0870e04d5b41` |
| Practice-source dataset | [Ten-family engineering-reference practice registry](../research/engineering-reference-practice-registry.json) |
| Authority rule | Standards and the owner-accepted SDLC govern; books are major engineering references; AI research governs neither lifecycle nor product authority |
| Rights class | `CURATED_RESEARCH`, `NOASSERTION`; local possession does not establish redistribution rights |
| Review trigger | A reference is added/replaced, a mapped rule changes, a contradiction is found, or runtime evidence falsifies an adopted practice |

> **The books are major references, not decoration.**
>
> They are used to close underspecified engineering work. They do not replace
> the established human software-development lifecycle, become executable
> authority, or turn one author's heuristic into a universal gate.

## 1. Governing hierarchy

Ranex applies evidence in this order:

1. **Human owner decisions and accepted ADRs** define internal product direction,
   decision rights, risk acceptance, and explicit inclusions/exclusions.
   They cannot waive applicable law, contract, license, privacy, third-party
   rights, or mandatory external obligations.
2. **Established lifecycle and engineering sources**—principally
   ISO/IEC/IEEE 12207:2026, SWEBOK, ISO/IEC 29110, NASA engineering guidance, and
   NIST SSDF—define the complete discipline coverage and control frame.
3. **The saved books are major practice references.** They deepen how design,
   construction, testing, collaboration, estimation, operation, and evolution
   are performed inside that frame.
4. **Hermes/upstream evidence** defines inherited behavior, compatibility,
   migration, provenance, and upstream-sync facts.
5. **AI-agent research** informs how probabilistic workers are bounded,
   measured, and verified. It cannot define the SDLC or transfer human
   authority.
6. **Runtime Ranex evidence** calibrates or falsifies a selected practice.

When sources disagree, Ranex does not average them. The owning role records the
conflict, applies the higher authority, tests material uncertainty, and records
the resolution in an RFC/ADR or process-assurance decision.

SWEBOK V4.0a was released before ISO/IEC/IEEE 12207:2026 and maps its knowledge
areas to the then-current 2017 edition. That internal crosswalk is historical;
Ranex must verify and version a 2026 mapping before claiming clause coverage.

## 2. Exact major-reference corpus

The current reference set has ten conceptual works represented by 18 stored
artifacts. Eight works have a PDF and a lossy Markdown extraction; *Clean
Architecture* and *A Philosophy of Software Design* are PDF-only.
Representations of one intellectual work share one source-family ID and are
never independent corroboration.

| Major reference | Primary Ranex use | Binding limitation |
|---|---|---|
| [SWEBOK Guide V4.0a](https://www.computer.org/education/bodies-of-knowledge/software-engineering/v4) | Consensus knowledge-area map and broad discipline-coverage check across requirements, architecture, design, construction, testing, operations, maintenance, configuration, management, process, quality, security, economics, and foundations | Non-comprehensive knowledge map, not a prescriptive Ranex lifecycle or conformity claim; 12207:2026 and other sources supply process coverage it does not directly map |
| [Code Complete, Second Edition — retained Chapter 5 excerpt](https://www.microsoftpressstore.com/articles/article.aspx?p=2222451) | Design during construction, complexity management, information hiding, coupling/cohesion, contracts, testability, binding time, iterative and proportionate design | The local PDF is a 120-page excerpt; only retained Chapter 5 is evidence, not the absent book chapters |
| [Clean Code](https://www.informit.com/store/clean-code-a-handbook-of-agile-software-craftsmanship-9780132350884) | Local construction discipline, boundary wrapping, startup/runtime separation, testability, expressive intent, small verified refactoring, concurrency cautions | Opinionated 2009 Java/TDD-era heuristics; code is not the sole authority in Ranex |
| [The Pragmatic Programmer, original first edition](https://www.informit.com/store/pragmatic-programmer-from-journeyman-to-master-9780201616224) | Responsibility, orthogonality, reversibility, contracts, tracer routes, plain-text/source-control discipline, automation, debugging, testing, and regression learning | Original 2000 text / local 25th printing from 2010; contextual guidance whose tracer work cannot shrink the full map or bypass gates |
| [System Design Interview: An Insider's Guide, Second Edition](https://openlibrary.org/works/OL21947791W/System_Design_Interview_-_an_Insider%27s_Guide) | Scope clarification, high-level decomposition, deep-dive selection, trade-off communication, back-of-envelope checks, failure/monitoring prompts, and a pattern catalogue | 2020 interview-preparation source with simplified web-scale patterns; not Ranex's reference architecture |
| [The Clean Coder](https://www.informit.com/store/clean-coder-a-code-of-conduct-for-professional-programmers-9780137081073) | Professional responsibility, explicit commitments, early risk/lateness disclosure, acceptance criteria, layered test strategy, sustainable work, collaboration, estimation, mentoring, and stable teams | One author's 2011 practice position; fixed coverage, TDD, staffing, time, or test-percentage rules are not universal Ranex mandates |
| [Designing Data-Intensive Applications](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/) | Reliability/scalability/maintainability vocabulary; clocks, leases and fencing; transaction and dual-write analysis; change streams, event derivation, idempotency, replay, and reconciliation | The local copy is the unfinished Sixth Early Release from 2016, not the completed first edition; it explicitly excludes security, deployment, operations, ethics, and management, so high-consequence claims require final-edition or primary-source confirmation |
| [Fundamentals of Software Architecture: An Engineering Approach](https://www.oreilly.com/library/view/fundamentals-of-software/9781492043447/) | Architecture characteristics, fitness functions, contextual trade-offs, component/consistency boundaries, topology selection, ADRs, and architecture governance | Experience-based first-edition guidance; generic star ratings and style preferences are prompts, never universal Ranex scores |
| [Clean Architecture: A Craftsman's Guide to Software Structure and Design](https://www.informit.com/store/clean-architecture-a-craftsmans-guide-to-software-structure-9780134494166) | Use-case-visible architecture, policy/detail boundaries, inward dependency direction, plugin/adaptor seams, enforceable encapsulation, and design for testability | Opinionated object/component guidance; “detail” language cannot erase data, security, reliability, performance, accessibility, or operational constraints, and the local artifact is a PDF-only Calibre conversion with unresolved provenance |
| [A Philosophy of Software Design, First Edition](https://web.stanford.edu/~ouster/cgi-bin/aposd.php) | Change amplification, cognitive load, unknown unknowns, deep module interfaces, information hiding/leakage, and comparative design for consequential choices | Opinionated experience-based Java/C++ design guidance; qualitative module depth and complexity symptoms require subject-specific evidence and cannot become a universal scalar score |

All ten references are **major** because each owns a named part of the
application map below. “Major” does not mean equal authority, current in every
technical detail, scientifically proven, or safe to redistribute.

### 2.1 Rights and public-repository blocker

The repository manifest says the target repository is public. The PDFs and
full/near-full Markdown derivatives carry restrictive or all-rights-reserved
notices; the local Pragmatic Programmer copy is visibly personalized for a
named third party. The DDIA copy is unfinished, and the Clean Architecture PDF
has Calibre metadata but no acquisition/conversion record. `CURATED_RESEARCH`
and `NOASSERTION` classify uncertainty; they do not create a license.

Accordingly:

- all eighteen full-text artifacts are `LOCAL_ONLY`;
- public-repository inclusion and release are
  `PROHIBITED_PENDING_RIGHTS`;
- they remain untracked or in access-controlled artifact storage unless a
  documented right-to-distribute decision says otherwise;
- a public Ranex deliverable may retain lawful bibliographic references,
  original paraphrases, claim-level notes, and non-reconstructive digests; and
- no human ADR or model review can waive copyright, contract, privacy, or
  third-party rights.

The repository enforces this separation by ignoring
`docs/research/books/`, classifying every local source path in the licensing
manifest, and requiring the release gate to reject any `LOCAL_ONLY` path found
in the Git index, release archive, package, mirror, or deployment input. The
public-safe map links lawful publisher/bibliographic pages and the
non-reconstructive digest manifest, never a required local full-text path.

This publication blocker does not demote the books as major design references.
It separates the right to consult a source from the right to redistribute it.

## 3. How an unclear area is closed

No developer or AI worker resolves architectural fog by improvising code. The
required ambiguity-closure protocol is:

```text
name the unclear decision and accountable owner
  -> bind current requirements, quality attributes, constraints, and exact subject
  -> locate applicable lifecycle/control obligations
  -> consult every relevant major reference
  -> identify facts, heuristics, conflicts, dated assumptions, and unknowns
  -> produce at least one viable alternative plus status quo
  -> map each alternative to owner, state, data, effect, API, file, failure, and recovery
  -> predeclare falsification and acceptance evidence
  -> obtain the required independent challenge and human decision
  -> implement a bounded route through the already-complete map
  -> retain operational/outcome evidence and revise through normal change control
```

An uncertainty may end in:

- an accepted architecture decision;
- a constrained implementation experiment;
- an explicitly inactive attachment point;
- an explicit product exclusion;
- a blocked item with named closure evidence; or
- rejection of the proposed capability.

“We will decide while coding” is acceptable only for a named local design
choice whose allowed boundary, invariants, evidence, and escalation condition
are already fixed. It is not acceptable for authority, state ownership,
security, data lifecycle, public API, compatibility, release, or recovery.

### 3.1 Proportionate supervision and fast feedback

The reference corpus rejects one maximum-weight workflow for every change:

- Code Complete calls for “enough design” based on project size, lifetime,
  team experience, and consequence, and says a simple familiar modification
  can proceed to construction.
- Clean Architecture treats boundaries as carrying implementation and
  maintenance cost; preserve options and introduce the full boundary when its
  measured value exceeds that cost.
- The Pragmatic Programmer favors a thin end-to-end tracer, immediate feedback,
  automation of repeatable work, and good-enough quality agreed with the user.
- Clean Code's FIRST test properties require fast, independent, repeatable,
  self-validating, timely feedback; they do not justify a slow universal suite.
- The Clean Coder favors small test increments, short meetings and planning,
  empirical resolution of technical disputes, and not assigning two people to
  trivial work.
- SWEBOK requires test selection under finite resources according to purpose
  and risk, with more independent estimates or assurance for high-consequence
  decisions.
- System Design Interview's useful sequence is clarify, high-level design, and
  deep-dive only critical areas inside a time box; its catalogue is not a
  requirement to over-engineer.
- Fundamentals of Software Architecture varies architectural control with
  experience, size, complexity, and duration, and favors automated fitness
  functions over recurring manual checklists.
- DDIA keeps a simpler topology until measured requirements justify distributed
  complexity while preserving reliability and operability evidence.
- A Philosophy of Software Design favors simple, deep interfaces and comparing
  alternatives for consequential design, but does not require ceremonial
  abstraction or repeated alternatives for trivial reversible choices.

Ranex therefore uses the Core SDLC operational paths:

| Path | Supervision rule | Feedback rule |
|---|---|---|
| `FAST` | One accountable implementer; no planner/reviewer chorus | Focused executable check and real consumer smoke; target minutes, not an hour |
| `STANDARD` | Optional one concise plan, one maker, one final fresh technical review when acceptance is being recommended | Small vertical slice, focused plus relevant regression/user proof |
| `CRITICAL` | One bounded plan when needed; independent technical and adversarial review of the final subject; human decision only for an actually unresolved value/risk choice | Triggered negative, security, data, migration, recovery, production, and user evidence |

Automatic routing selects only useful calibrated roles. It does not serialize
every available model. Unrelated dirty work, a generated-lock refresh, or an
owner decision already supplied cannot be converted into a proposal-only loop.

## 4. Full lifecycle application

| Core stage | Major-reference contribution | Required Ranex result |
|---|---|---|
| `GOVERN` | SWEBOK professional practice, process, quality, management, and economics; Clean Coder responsibility/commitments; Fundamentals characteristics, ADRs, and fitness governance | Named decision rights, policy, capability ownership, characteristics, conformance, competence, decision evidence, and improvement system |
| `SHAPE` | Pragmatic responsibility/value communication; Clean Coder explicit commitments; System Design scope questions; Clean Architecture use-case visibility | Owned need, user outcome, boundaries, non-goals, work class, and initial risk |
| `DISCOVER` | Pragmatic requirements exploration/reversibility; System Design clarification/scale prompts; DDIA fault/load vocabulary; Fundamentals characteristic discovery; APOSD comparative design | Current behavior, user/actor evidence, assumptions, unknowns, falsifiable hypothesis, quality priorities, scale envelope, and viable shapes for consequential choices |
| `SPECIFY` | SWEBOK requirements; Pragmatic contracts; Clean Coder executable acceptance examples; DDIA reliability/performance scenarios | Functional and quality requirements, misuse/failure cases, acceptance criteria, trace links, and change rules |
| `DESIGN` | All ten families: discipline coverage, complexity symptoms, deep modules, information hiding, boundaries, dependency direction, data/failure semantics, topology trade-offs, alternatives, ADRs, and fitness functions | Full owner/boundary/API/state/data/effect/file/failure/recovery map plus characteristics, alternatives, ADR, and falsifiers |
| `PLAN` | SWEBOK engineering management/economics; Clean Coder estimation-versus-commitment; Pragmatic reversible increments; Fundamentals trade-offs | Forecast range, dependencies, capacity, vertical routes, verification/release/rollback plan, and recommitment triggers |
| `BUILD` | Code Complete construction design; Clean Code, Clean Architecture, and APOSD boundaries/information hiding/testability; Pragmatic contracts/generation; DDIA exact state/effect semantics | Dependency-conforming code, tests, docs, generated contracts, immutable run evidence, and no hidden scope |
| `VERIFY` | SWEBOK testing/quality; Clean Coder layered testing/acceptance; Pragmatic regression learning; boundary/encapsulation/information-leakage fitness; APOSD change and comprehension challenge; DDIA crash/replay/stale-worker/duplicate tests | Exact-subject independent evidence, deterministic gates, failure-path proof, architecture fitness results, and no self-approval |
| `RELEASE` | SWEBOK configuration/operations; Pragmatic automation/reversibility; System Design monitoring/failure prompts; DDIA migration/encoding questions | Immutable artifact, SBOM/provenance, migration, progressive exposure, health stop, rollback, and permit |
| `OPERATE` | SWEBOK operations/maintenance; Pragmatic observability/debugging; System Design capacity/failure catalogue; DDIA reliability/lag/recovery; characteristic fitness distributions | Service ownership, SLI/SLO, telemetry, support, incident, reconciliation, backup/restore, and capacity evidence |
| `MAINTAIN_OR_RETIRE` | SWEBOK maintenance/configuration; Code Complete maintainability; Pragmatic reversibility; APOSD change amplification; DDIA history/retention/erasure tension | Controlled change or removal, consumer/data/access migration, compatibility evidence, and governed retained/erased history |
| `IMPROVE` | SWEBOK process/measurement; Clean Coder learning/mentoring; Pragmatic continuous learning; Fundamentals evolutionary fitness functions; APOSD complexity/alternative review | Evidence-bound capability assessment, bounded experiment, guardrails, corrective action, and human decision |

The table is one continuous, iterative system. It is not a queue of
book-defined departments.

## 5. Architecture decision workflow

Every material architecture question uses the following full workflow.

### 5.1 Frame the real problem

The owner records:

- actors and user/service outcome;
- present behavior and evidence;
- functional requirements;
- security, privacy, reliability, performance, accessibility, operability,
  maintainability, portability, provenance, compatibility, and cost
  attributes;
- expected load and uncertainty instead of unearned internet-scale assumptions;
- external systems and effects;
- retained Hermes behavior and upstream baseline;
- reversibility, recovery, and retirement needs; and
- explicit non-goals.

System Design Interview's clarification method is useful here. Its web-scale
defaults are not. Ranex remains a one-host modular monolith unless measured
requirements and an accepted product-scope ADR change that decision.
Fundamentals of Software Architecture additionally requires the selected
characteristics and their subject-specific fitness functions; a topology
without those characteristics, decisions, and principles is incomplete.

### 5.2 Produce a high-level decomposition

The design names:

- bounded contexts and one accountable owner for every state/effect;
- system and trust boundaries;
- user/operator/worker/external actors;
- public commands, queries, events, and views;
- synchronous and asynchronous interaction;
- canonical records versus projections;
- storage and transaction ownership;
- consistency/architecture-quantum boundaries and the measured benefit of each
  component boundary;
- failure domains and isolation;
- deployment/runtime topology; and
- final repository homes.

This is the complete map. No implementation itinerary is allowed to determine
its extent.

### 5.3 Deep-dive every authority-bearing seam

At minimum, deep dives cover:

- lifecycle states, legal transitions, invalidation, and re-entry;
- authentication, policy, human decision, authority grant, permit, effect, and
  reconciliation order;
- exact-subject and content-addressed evidence;
- transaction, outbox, concurrency, retry, idempotency, time, and fencing;
- enforcement of fencing epochs by every protected state/effect sink, not only
  by the lease-holding worker;
- command acceptance, immutable-event semantics, deterministic derivation,
  snapshots, replay, lag, correction, retention, and erasure;
- data classification, retention, backup, restore, migration, and purge;
- dependency direction and public API stability;
- sandbox, path, process, network, secret, and extension isolation;
- degraded modes, cancellation, rollback, incident, and disaster recovery;
- observability and support;
- upstream synchronization, compatibility, and de-commercialization; and
- construction, verification, release, operation, and retirement attachment
  points.

The deep dive selects the risk-bearing parts of the **whole design**. It does
not hide the rest of the map.

### 5.4 Compare alternatives

Every alternative is evaluated against:

- correctness and exact authority;
- essential versus accidental complexity;
- information hiding and coupling/cohesion;
- testability and observability;
- reversibility and migration;
- security and blast radius;
- operational failure/recovery;
- maintainability and cognitive load;
- boundary count, communication overhead, central-orchestration coupling, and
  consistency cost;
- compatibility/upstream cost;
- delivery and verification capacity;
- total lifecycle cost; and
- explicit evidence that could falsify the choice.

The status quo is always an alternative. A familiar pattern name, book
recommendation, model consensus, or fashionable topology is not evidence that
an alternative fits Ranex.

### 5.5 Record and govern the decision

The `ArchitectureReviewPacket` freezes the exact subject. DeepSeek V4 Pro may
serve as the primary architecture specialist and HY3 as an independent
challenger only when their actual routes are qualified and recorded. Their
proposals become findings/evidence. The human architecture authority accepts,
rejects, or defers through the normal RFC/ADR and Core-SDLC controls.

Every architecturally significant decision record names context/forces,
status quo and viable alternatives, the selected decision, business and
technical justification, positive and negative consequences, affected
characteristics, reversibility, and a manual or executable fitness/compliance
check. A fixed architecture table without this crosswalk is not sufficient
decision evidence.

## 6. File-structure rules derived from the major references

### 6.1 Organize around owned concepts

The target source tree is organized by bounded context and authority, not by
model provider, UI page, generic “manager,” or current implementation phase.
Each context has:

```text
context_name/
├── api/
│   ├── commands.py
│   ├── queries.py
│   ├── events.py
│   └── views.py
├── domain/
├── application/
│   └── ports/
└── infrastructure/  # only when the context owns an implementation detail
```

Adapters and applications remain outside domain authority. Composition code
wires implementations; it does not contain business rules.

This exact tree is a Ranex-owned synthesis, not a directory layout proved by a
book. Clean Architecture supports use-case visibility, inward dependencies,
and enforceable encapsulation; Fundamentals requires each component boundary
to justify its coupling, consistency, communication, and cognitive cost.
Language-level visibility and dependency fitness tests must make the intended
boundary real. A folder diagram alone is not architecture.

### 6.2 Make dependencies point inward

Allowed direction:

```text
apps/adapters -> application ports/services -> domain
                         |
                         +-> typed public API of another context
```

Forbidden direction:

```text
domain -> provider SDK / UI / filesystem / network / legacy Hermes
context internals -> another context's domain internals
worker harness -> authority database
adapter -> direct state mutation
generated contract -> handwritten semantic override
```

This applies Code Complete's complexity/information-hiding guidance, Clean
Code's boundary discipline, Pragmatic orthogonality, and Clean Architecture's
dependency rule without treating any one object-oriented idiom, ring count, or
package layout as mandatory.

### 6.3 Separate construction from runtime authority

Configuration discovery, dependency assembly, migration, startup validation,
and process launch live in composition/bootstrap packages. Runtime domain
objects receive already-validated ports and immutable configuration views.
Import-time registration, environment-presence auto-selection, and hidden
global mutation are forbidden.

### 6.4 Put volatile details behind narrow ports

Provider/model routes, Hermes harnesses, tool protocols, policy engines,
workflow runtimes, sandboxes, Git hosts, messaging channels, and storage
implementations attach through owned ports. Ports describe Ranex needs rather
than mirroring vendor SDKs.

### 6.5 Keep contracts and examples generated from one semantic source

Architecture registries define identities, state, ownership, dependencies,
events, authority, lifecycle crosswalks, invalidation, and compatibility.
Schemas validate artifacts. Generated Python/TypeScript types and examples are
projections. Hand-edited duplication fails CI.

### 6.6 Mirror risk in tests

Tests are organized by what they falsify:

```text
tests/
├── unit/          # pure domain rules
├── contract/      # schemas and public APIs
├── integration/   # owned adapter/context seams
├── property/      # invariants and state machines
├── resilience/    # crash, retry, restore, reconciliation
├── security/      # denial and bypass paths
├── migration/     # old/new state and cutover
├── compatibility/ # Hermes/upstream/public behavior
└── evaluation/    # route, harness, checker, fleet effectiveness
```

Coverage locates missing evidence. It is not a release verdict, capability
score, or substitute for boundary/failure tests.

Any privileged test-only API is compiled, deployed, and authorized as a
separate qualified test capability. Production absence or denial is tested;
testability guidance never creates a production security or authority bypass.

## 7. Construction and change discipline

For each bounded change:

1. Bind the accepted requirement/design/subject and allowed paths.
2. Establish a failing requirement-level, contract, property, or regression
   check where applicable.
3. Implement the smallest coherent vertical change inside the mapped
   boundary.
4. Keep domain decisions explicit and vendor/infrastructure details behind
   ports.
5. Run fast checks continuously; run risk-required integration, resilience,
   security, migration, compatibility, and evaluation checks before the
   corresponding gate.
6. Refactor only inside declared scope and only with preserved proof.
7. Record actual commands, changed files/dependencies, evidence, unknowns, and
   deviations.
8. Obtain independent review and deterministic gate evidence.
9. Land through human-controlled authority.
10. Verify the landed subject, operate it, and review outcome.

A vertical tracer is a production-shaped route through already-mapped
architecture. It is **not** an MVP, prototype, temporary architecture, excuse
for missing owners, or permission to leave interfaces undefined. Disposable
experiments are quarantined research artifacts and do not silently become the
product.

### 7.1 Engineering-practice application contract

The references are used through behavior, not ceremonial citation. The
public-safe
[`engineering-reference-practice-registry.json`](../research/engineering-reference-practice-registry.json)
now freezes ten source families and 38 stable practice-source IDs. Its status
is `SOURCE_RECONCILED_NOT_APPLIED`; it is source data, not an executable
contract or conformance result. At `AI-G2`, the accepted contract compiler
consumes that dataset into `architecture/contracts/engineering-practices.json`
under these source families:

```text
ENGREF-SWEBOK-V4A
ENGREF-CODE-COMPLETE-CH5
ENGREF-CLEAN-CODE
ENGREF-PRAGMATIC-PROGRAMMER-1E
ENGREF-SYSTEM-DESIGN-INTERVIEW-2E
ENGREF-CLEAN-CODER
ENGREF-DDIA-1E-ER6
ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E
ENGREF-CLEAN-ARCHITECTURE-1E
ENGREF-APOSD-1E
```

Each registered practice records:

- the source-family ID and public-safe section/page locator where reliable;
- original Ranex synthesis of the principle;
- applicable Core-SDLC stages, work classes, risk signals, and architecture
  concerns;
- known limits, dated assumptions, conflicts, and rejected overclaims;
- the behavior required when applicable;
- acceptable verification methods; and
- the accountable owner and change/expiry rule.

The compiler evaluates all ten source families when producing the accepted
practice registry. Each architecture or implementation packet then binds a
compact immutable `EngineeringPracticeProfileV1` projection containing only
the practices selected by work class, execution path, technology, and risk.
It does not ask a model to reread or summarize all ten works for every task.
The projection records `APPLICABLE`, `NOT_APPLICABLE`, or `UNKNOWN` with
evidence.
`APPLICABLE` entries name the exact practices, the expected effect on the work,
and verification references. `NOT_APPLICABLE` requires a reason; a material
`UNKNOWN` blocks readiness. Any deliberate deviation names the conflict,
alternative, consequence, and decision authority.

Fast work normally uses the frozen compact default—small scope, readable
cohesive change, no speculative abstraction, focused automated proof, final
scope inspection, and real consumer smoke when applicable. Standard work adds
only relevant projected practices. Critical/architecture work performs explicit
applicability analysis for its triggered seams.

The profile is a compact projection. It does not copy full-text books into
packets, prompts, logs, generated documentation, or public artifacts. Local
full-text material is consulted only when the packet authorizes it and the
rights/data policy permits it. The public-safe map and registered synthesis are
the normal worker inputs.

Reviewers test application rather than vocabulary. A finding such as “cites
information hiding” is not satisfied until the candidate demonstrates an
owned boundary, narrower coupling, and the required contract/dependency tests.
Process assurance samples profiles against code, decisions, tests, operational
evidence, and outcomes to detect empty compliance.

## 8. Verification strategy

The combined major-reference position is:

- acceptance examples clarify behavior but do not replace requirements;
- unit tests prove local rules but not integration or operation;
- component/contract tests prove stable boundaries;
- architecture fitness functions prove declared dependency, encapsulation,
  characteristic, and topology constraints on the exact subject;
- integration tests prove actual adapter interactions;
- property/state-machine tests challenge invariants and transitions;
- system/end-to-end tests prove representative journeys;
- security tests attempt denied routes and bypasses;
- resilience tests inject crash, timeout, replay, stale lease, partial
  external effect, duplicate/out-of-order delivery, clock jump, process pause,
  restore, and reconciliation conditions;
- fencing tests prove that every protected resource rejects a stale epoch even
  when the stale worker resumes after lease loss;
- compatibility tests bind inherited/upstream behavior and deprecation;
- exploratory evaluation finds classes of failure not captured by known
  assertions;
- operational validation proves health, support, recovery, and user outcome;
  and
- no worker's own test or favorable model review authorizes its change.

Fixed test pyramids, universal coverage percentages, or “QA should find
nothing” are rejected. Independent findings are useful system evidence, not
professional shame.

## 9. Professional work, estimation, and commitments

The Clean Coder is applied through the Core SDLC, not as personal mythology:

- distinguish an estimate distribution from an accepted commitment;
- commit only to actions within controlled scope and named dependencies;
- disclose uncertainty, risk, and lateness early with evidence;
- never trade away required verification to preserve a date;
- ask for and offer help without transferring accountability invisibly;
- keep work at a sustainable pace;
- preserve time for competence, mentoring, and process improvement; and
- treat Definition of Done as an organizational evidence contract, not a
  worker's private assertion.

No fixed workweek, overtime threshold, team size, coverage target, staffing
ratio, apprenticeship hierarchy, or development technique becomes mandatory
solely because a book recommends it.

## 10. Book-specific guardrails

| Reference proposition | Ranex disposition |
|---|---|
| Design is iterative/emergent | Accepted inside a stable full-map boundary; material discoveries re-enter design/change control |
| Manage complexity with decomposition and information hiding | Accepted and made enforceable through contexts, ports, ownership, dependency tests, and narrow public APIs |
| APOSD complexity symptoms | Accepted as separate change-amplification, cognitive-load, and unknown-unknown diagnostics with change/comprehension evidence; rejected as arithmetic points |
| Deep modules | Accepted as a simple, stable, complete interface relative to useful hidden complexity; rejected as permission for god modules, unbounded responsibility, or hidden failure/authority facts |
| Information hiding | Accepted as one semantic owner and leakage-resistant public contract; rejected when it conceals facts required for authority, denial, security, audit, recovery, or operation |
| Design it twice | Accepted proportionately for consequential architecture choices as status quo plus at least two viable shapes with tradeoffs and falsifiers; not required ceremonially for trivial reversible choices |
| Code is the only truth | Rejected; runtime behavior matters, but requirements, decisions, schemas, evidence, release records, and operational facts have distinct authority |
| Keep design simple | Accepted as minimizing accidental complexity, never as omitting essential authority, failure, security, or lifecycle behavior |
| Tracer bullets | Accepted as reversible vertical delivery routes through the full architecture; never relabeled MVP/prototype scope |
| DRY | Accepted for authoritative knowledge and needless duplication; rejected when it produces a shared database/god service or erases bounded-context ownership |
| Automate everything repeatable | Accepted where automation is observable, qualified, reversible, and governed; automation cannot self-approve |
| TDD or one testing style defines professionalism | Rejected; test technique is chosen by risk and subject, while required evidence remains mandatory |
| Web-scale cache/queue/shard patterns | Catalogue only; require measured need, one-host product compatibility, failure semantics, operations, and accepted ADR |
| Interview-style four-step design | Adapted into scope, complete high-level map, risk deep dives, and evidence-bound reconciliation; time-box advice is not policy |
| DDIA fencing tokens | Accepted only when every protected resource enforces the monotonically increasing epoch; client-side lease checks are insufficient, and hostile-worker security remains separate |
| DDIA event sourcing / retain all events | Adapted to selective Ranex journals with explicit command acceptance, reducer determinism, snapshot/current-row consistency, replay, correction, retention, and erasure |
| Exactly-once processing/effects | Rejected as an end-to-end claim; state exact atomicity, idempotency, fencing, retry, and reconciliation assumptions |
| One architecture style or generic star rating | Rejected; characteristics, domain, data, organization, process, alternatives, and exact-subject fitness evidence select the least-worst fit |
| More bounded contexts means better modularity | Rejected; measure coupling, consistency, communication, transaction, failure, and cognitive cost and merge/split when evidence requires |
| Central orchestration | Accepted only for the smallest necessary consistency authority; central business/technical knowledge and change coupling are measured and constrained |
| Database, web, UI, or framework is “just a detail” | Accepted only as dependency-direction guidance; data, security, reliability, performance, accessibility, migration, and operations remain first-class constraints |
| Clean Architecture layers/package tree | Adapted as inward dependencies, use-case visibility, and enforceable encapsulation; no universal ring count or directory layout |
| Privileged testing API | Permitted only in isolated qualified test support with production absence/denial proof; never a production authorization bypass |
| Fixed coverage/test-pyramid/team/velocity numbers | Rejected as universal gates; calibrate locally without weakening mandatory controls |
| Individual heroics under pressure | Rejected; transparent system-level planning, assistance, sustainable pace, and evidence-based recommitment govern |

## 11. Fog closed by this map

| Previously ambiguous area | Closed position |
|---|---|
| Full architecture versus iterative design | The destination is fully mapped; details evolve through governed feedback and ADRs |
| Ground zero versus fork | New authority/domain/application core, built through a strangler inside a provenance-proven Hermes-derived fork |
| Tracer versus MVP/prototype | A tracer is a narrow route and proof instrument; it does not define or shrink the target |
| Modular monolith versus distributed system | Product deployment is one-host modular monolith; worker coordination and external effects still require distributed-systems controls |
| Context granularity | A context boundary requires owned policy plus measured coupling/consistency/change benefit;  context count is not a quality score |
| Module depth | Consumer-facing surface is justified by useful complexity hidden and measured boundary fit; depth is not a scalar score and cannot excuse an unbounded owner |
| Synchronous versus asynchronous interaction | Local synchronous calls/transactions are the default; durable asynchronous derivation is chosen only for named isolation, integration, durability, or throughput needs |
| Lease versus fencing | Lease ownership alone is insufficient; every protected sink enforces the current monotonically increasing epoch |
| Journal versus current state | Commands, accepted events, reducer/current-row authority, snapshots, replay, lag, correction, retention, and erasure are separately specified and tested |
| Architecture decision evidence | Every significant choice records characteristics, status quo, viable alternatives, rationale, consequences, and a fitness/compliance check |
| File structure | Context/authority first, then API/domain/application/ports/adapters; composition and legacy boundaries are explicit |
| Provider/model placement | Replaceable adapter/route behind qualified ports; never a domain or authority owner |
| Review and acceptance | Observation, deterministic evidence/gate, accountable human decision, grant, permit, and effect are separate |
| Testing depth | Risk-based layered falsification, not unit-test or coverage monoculture |
| Estimation and promises | Estimates express uncertainty; commitments require accountable scope/dependency/capacity decisions |
| Operations | Health, SLO/support, incident, recovery, backup/restore, reconciliation, maintenance, and retirement are designed before release |
| Desktop | Electron desktop is excluded; CLI, TUI, loopback web, GitHub edge, and text-phone surfaces attach to shared application APIs |
| AI agents | Workers execute bounded roles; the human-established SDLC remains the method and authority frame |

## 12. Acceptance tests

This reference map is not complete merely because the books were listed. It is
falsified if:

1. a major architecture decision cannot trace to an owned requirement,
   applicable lifecycle/control, alternatives, and falsification evidence;
2. an architecture review omits owner, state, data, effect, API, file,
   failure, recovery, or lifecycle consequences;
3. an implementation route is used to justify an unmapped target area;
4. a book heuristic overrides an accepted control without an ADR;
5. AI research or model consensus changes human decision rights;
6. a vendor/web-scale pattern enters the target without measured need and
   operational/failure analysis;
7. a test percentage, model score, or process average hides a mandatory
   failure;
8. code bypasses a context public API, authority cell, `CapabilityBus`, or
   owned port;
9. a PDF/Markdown pair is counted as independent corroboration;
10. any saved reference remains absent from the frozen manifest and licensing
    classification;
11. a local full-text reference is published without a documented rights
    basis; or
12. a changed reference does not trigger impact review of the rules it
    supports;
13. a task bypasses the compiled ten-family registry, or its compact
    path/risk-specific projection fails to bind applicable practices to
    behavior and verification; or
14. a packet or review treats a book name, quotation, or principle label as
    proof that the practice was followed;
15. the unfinished DDIA early release is represented as the completed first
    edition or used for high-consequence claims without final/primary-source
    confirmation;
16. a component, context, service, layer, ring, directory, async boundary, or
    central orchestrator is justified only by a pattern name instead of
    characteristics, alternatives, costs, and fitness evidence;
17. a protected resource trusts a worker-side lease/fencing check instead of
    independently rejecting stale epochs; or
18. the practice-source registry is mistaken for a completed applicability
    profile, executable contract, implementation result, or conformance claim.

## 13. Current standing

The reference application map and source registry are a complete
**ten-family practice-source attachment set** for the exact manifested
snapshot. They do not prove that Ranex implements or follows the practices.
Runtime adoption requires executable machine contracts, subject-specific
applicability profiles, representative normal and rejection tracers,
independent verification, operations evidence, capability assessment, and the
human decisions defined by the Core SDLC. Contract readiness additionally
requires the compiler output and profile schema described in section 7.1.

The correct status is:

> **Ten works and eighteen representations frozen and source-mapped; rights,
> task-level applicability, architecture decision closure, executable
> contracts, and runtime conformance remain separate evidence.**
