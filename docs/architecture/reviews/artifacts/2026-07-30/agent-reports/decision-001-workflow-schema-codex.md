Reading additional input from stdin...
OpenAI Codex v0.146.0
--------
workdir: /home/soultransit/devtony/ranex
model: gpt-5.6-sol
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: high
reasoning summaries: none
session id: 019fb32e-6994-7c31-8b4c-2fa840170dee
--------
user
# Recommend the concrete workflow and event schema + upcaster policy for Ranex

This resolves `HERMES-OWNER-DECISION-001` (ADR-0013:823-834), which blocks
`IMPLEMENTATION_START` and defaults to BLOCK. The required artifact is an accepted
ADR with predeclared acceptance tests, so your output must be specific enough to
become one.

**Premise: this is not novel.** The corpus already classifies it as "MATURE
PATTERN / R&D schema" (`docs/research/hermes-core-architecture-research-2026-07-27.md:786`)
and names the five required properties: immutable definitions, interpreter
version, event-schema version, upcaster compatibility, and replay checks. Line
2023-2024 adds: "pin interpreter/event versions; test upcasters against frozen old
histories." Your job is to bring the **proven concrete form** from production
systems, not to design one.

## The question, in one sentence

What exactly is a Ranex workflow definition made of, what does a persisted event
look like, and what is the rule for changing either without breaking runs already
recorded in the old format?

## Read these first

- `docs/research/hermes-core-architecture-research-2026-07-27.md` lines 780-800 and
  2015-2035, and 2125 (the decision's cited source).
- `docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md` §8.3 and the
  surrounding state/journal sections.
- `docs/architecture/decisions/ADR-0013-...md` provisions 058-065 (accepted kernel
  obligations) and `HERMES-OWNER-DECISION-001`, `-002`, `-020`.
- `docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md` —
  already-verified prior art on replay and journal/snapshot agreement. Build on
  it; do not redo it.
- The kernel tracer in worktree `.claude/worktrees/kernel-tracer` (branch
  `feature/kernel-tracer`, untracked `src/`): its `Execution` aggregate carries
  only an opaque `workflow_request_ref: str` and no definition, node identity, or
  version pins. Note precisely what is missing.

## Prior art to verify and compare

Temporal (workflow versioning, patching, and replay-safety guarantees), Axon
Framework (event upcasters), Marten and EventStoreDB (event schema evolution),
Argo Workflows and Airflow (immutable definition versioning), plus the
event-versioning literature — Greg Young's *Versioning in an Event Sourced
System* and the relevant chapters of Kleppmann's *Designing Data-Intensive
Applications* and Richardson's *Microservices Patterns*. Report each strategy's
name, how it handles old histories, and its failure modes.

The central comparison to settle: **weak schema / tolerant reader, versioned event
types, upcasting on read, lazy in-place migration, or copy-and-transform** — which
does Ranex need given that it must replay frozen old histories deterministically
and prove that replay reproduces the snapshot?

## Required output

1. **Recommendation** — one concrete choice per element: workflow definition
   fields, node identity scheme, event envelope fields, version pin locations,
   and upcaster policy. Specific enough to implement.
2. **Why this and not the alternatives**, with the failure mode each rejected
   option would introduce here.
3. **What it costs** — what becomes harder or impossible under this choice.
4. **Predeclared acceptance tests** — how the decision is proven satisfied,
   including a frozen-old-history replay test.
5. **Interaction with accepted obligations** — cite `HERMES-PROMOTION-058` to
   `-065` and §8.3, and confirm nothing conflicts. A conflict is a finding.
6. **What remains genuinely the owner's choice** after your recommendation, and
   the specific question they should answer.

## Non-negotiables

- Verify externally; cite a URL per external claim, with version or date. Mark
  anything unverifiable as `UNVERIFIED` rather than asserting it.
- Cite `path:line` for every claim about this repository.
- Read-only. Do not modify, create, or delete any file.
- Report every inference separately, marked as inference.
- Do not recommend a new bounded context, artifact type, or dependency unless you
  show why an existing one is insufficient.
codex
I’ll trace the accepted repository obligations and the kernel-tracer gap first, then verify the named production strategies against primary sources. I’ll keep repository facts, external facts, and inferences explicitly separated so the result can be lifted into an ADR without hiding assumptions.
  → Inspect cited repository sections, ADR provisions, and kernel-tracer worktree
  • Verify named prior art and evolution strategies from primary/authoritative sources
  • Compare alternatives and formulate concrete Ranex schema/versioning policy
  • Draft predeclared acceptance tests, obligation mapping, costs, and owner choice
  • Audit every repository claim for path:line citations and every external claim for URL/date/version
exec
/bin/bash -lc "rg --files docs/architecture/decisions docs/architecture/reviews/artifacts/2026-07-30/agent-reports docs/research | rg 'ADR-0013|priorart-B|hermes-core-architecture-research-2026-07-27' && rg -n \"HERMES-OWNER-DECISION-(001|002|020)|HERMES-PROMOTION-0(58|59|60|61|62|63|64|65)|§8\\.3|8\\.3\" docs/architecture/decisions docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
docs/research/hermes-core-architecture-research-2026-07-27.md
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470:### 8.3 State versus journal
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:26:- **DEFECT 9** — `HERMES-PROMOTION-059` claimed that *every* Execution
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:47:  normative changes to `HERMES-PROMOTION-058` and
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:48:  `HERMES-PROMOTION-059`.
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:61:  1.3.0)** — `HERMES-PROMOTION-058` renamed
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:65:  `HERMES-PROMOTION-059` replaced “whose state evolution is computed by a pure
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:88:  `HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`, rather than by an
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:101:`HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`:
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:114:It also adds `HERMES-OWNER-DECISION-020` as an
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742:  - provision_id: "HERMES-PROMOTION-058"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:752:  - provision_id: "HERMES-PROMOTION-059"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:762:  - provision_id: "HERMES-PROMOTION-060"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:772:  - provision_id: "HERMES-PROMOTION-061"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:782:  - provision_id: "HERMES-PROMOTION-062"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:792:  - provision_id: "HERMES-PROMOTION-063"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:802:  - provision_id: "HERMES-PROMOTION-064"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:812:  - provision_id: "HERMES-PROMOTION-065"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:823:  - provision_id: "HERMES-OWNER-DECISION-001"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:835:  - provision_id: "HERMES-OWNER-DECISION-002"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1051:  - provision_id: "HERMES-OWNER-DECISION-020"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1150:| `FF-HERMES-OWNER-DECISION-001` | Every genuine owner choice is `OWNER_DECISION_REQUIRED`, has no default or synthetic decision reference, and blocks activation or progression while the exact accepted owner decision is absent. |

exec
/bin/bash -lc "nl -ba docs/research/hermes-core-architecture-research-2026-07-27.md | sed -n '780,800p;2015,2035p;2118,2130p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   780	### Bake directly into the Ranex product kernel
   781	
   782	| Product-core responsibility | Layer | Exact ownership | Maturity |
   783	|---|---|---|---|
   784	| Canonical subject and execution identity | Pure domain/shared kernel | Project, work item, run, activity, packet, workspace, commits, principal, and correlation IDs. | **MATURE PATTERN** |
   785	| Execution aggregate and pure reducer | Pure domain | Legal workflow state, transition invariants, terminality, cancellation, waits, retries, and ordered event application. | **MATURE PATTERN / R&D schema** |
   786	| Workflow definition compatibility | Pure domain | Immutable definitions, interpreter version, event-schema version, upcaster compatibility, and replay checks. | **MATURE PATTERN / R&D schema** |
   787	| Policy and authorization semantics | Pure domain | Typed decisions, default-deny invariants, subject/grant/risk inputs, and current-policy requirements. | **MATURE** |
   788	| Policy enforcement point | Application control | Complete mediation and current-policy recheck before effects; invokes the decision adapter and converts faults into denial. | **MATURE** |
   789	| Constitutional invariants | Pure domain | No self-approval, no undeclared transition, no cross-project grant, no effect without authority. | **Core-domain requirement** |
   790	| Capability/effect broker | Application control | Typed activity request, declared effects, capability grant, idempotency identity, dispatch, and result validation. | **MATURE PATTERN / R&D contract** |
   791	| Evidence and claim contract | Pure domain | Exact subject binding, provenance, freshness, content digest, evaluator identity, and raw evidence references. | **MATURE PATTERN / R&D schema** |
   792	| Gate semantics | Pure domain | Canonical outcomes and rules for which results may advance a blocking transition. | **Core-domain requirement** |
   793	| Human decision and waiver contract | Pure domain | Exact scope, reason, principal, expiry, policy revision, and non-equivalence to `PASS`. | **MATURE PATTERN / R&D schema** |
   794	| Permit semantics | Pure domain | Exact-subject, single-use, expiring authority and compare-and-swap consumption rules. | **Core-domain requirement** |
   795	| Transaction, journal, and outbox coordinator | Application control | Commit aggregate version, audit/domain record, consumed authority, and outbound intent in one unit of work. | **MATURE** |
   796	| Module qualification and capability semantics | Pure domain | Descriptor identity, compatibility, activation lifecycle, grants, conflicts, qualification, and quarantine state. | **MATURE PATTERN / R&D contract** |
   797	| Module construction/loading | Bootstrap/infrastructure | Explicit catalog, factories, dependency injection, migrations, and process boundaries. | **MATURE PATTERN** |
   798	| Core ports | Public contracts | Journal/unit of work, clock, ID source, policy evaluator, evidence store, activity transport, secret reference, telemetry sink. | **MATURE** |
   799	
   800	The product core owns contracts, decisions, and nonbypassable application
  2015	- changed module digest forces requalification;
  2016	- incompatible interface fails before construction.
  2017	
  2018	### Reducer and replay tests
  2019	
  2020	- property-test every state/event combination;
  2021	- reject undeclared transitions;
  2022	- replay normal, blocked, cancelled, retried, waived, and recovered histories;
  2023	- pin interpreter/event versions;
  2024	- test upcasters against frozen old histories;
  2025	- snapshots accelerate replay but never replace the journal;
  2026	- inject time/random/network calls and prove the reducer rejects or lacks them.
  2027	- treat failure of replay, timer, signal, cancellation, upgrade, or crash
  2028	  semantics as a P0 trigger to evaluate a mature durable runtime rather than
  2029	  expanding a home-grown engine without an ADR.
  2030	
  2031	### Authority tests
  2032	
  2033	- default-deny every unknown action/role/capability;
  2034	- policy adapter throws, times out, returns malformed data, or disappears;
  2035	- module attempts self-grant/self-activation;
  2118	| Hermes provider profiles | **MATURING** | Explicit catalog, collision policy, qualification, no import side effects. |
  2119	| Process/container/WASM adapter isolation | **MATURE tools / FOGGY Ranex profile** | Threat-model-specific denial and escape tests on the target host. |
  2120	| DBOS or Restate adapter | **PROMISING** | Must beat the local baseline on recovery/operations without weakening local-first goals. |
  2121	| LangGraph definition module | **PROMISING for some agent flows** | Must use kernel activities/gates and never become authority. |
  2122	
  2123	### Foggy / R&D
  2124	
  2125	1. The canonical Ranex workflow/event schema and upcaster policy.
  2126	2. Whether the local runner passes enough crash/recovery tests or Temporal is
  2127	   justified.
  2128	3. Exact transaction ownership across execution, evidence, permit, and work
  2129	   projections.
  2130	4. Atlas's supported-language coverage and what produces `UNKNOWN`.

exec
/bin/bash -lc "nl -ba docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '400,530p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   400	| T2 | Reviewed first-party context/module | packet compiler, checkers, repository intelligence, routing, delivery | In-process only when pure; otherwise isolated |
   401	| T3 | Effect adapter | provider, terminal, GitHub, browser, sandbox, storage | Capability-scoped; isolated as threat model requires |
   402	| T4 | Legacy compatibility | inherited Hermes compatibility process, migration reader, legacy plugin bridge | Separate constrained non-inference process; no provider/credential/network route or authority database access |
   403	| T5 | External extension | separately installed integration | Out-of-process narrow protocol; never registers a PEP, gate, state writer, or permit issuer |
   404	
   405	## 8. Canonical consistency boundary
   406	
   407	### 8.1 The Governed Execution Authority Cell
   408	
   409	`governed_execution` is one bounded consistency cell with four cohesive
   410	subdomains:
   411	
   412	1. run/workflow lifecycle;
   413	2. exact authorization and gate-decision snapshots;
   414	3. permits and human-decision consumption; and
   415	4. activity/effect intent, result, retry, and reconciliation.
   416	
   417	These responsibilities are separate domain files and types, but they participate
   418	in one invariant and one SQLite transaction. They are not persisted as four
   419	independent authorities.
   420	
   421	Policy definitions, evidence artifacts, checker qualification, and module/route
   422	catalogs are owned by other contexts. Before a transition, their immutable
   423	decisions and digests are copied or bound into the authority transaction. A
   424	later change cannot rewrite the historical snapshot, while every new effect
   425	still requires current-policy re-evaluation.
   426	
   427	`work_management` owns the separate `WorkItem` aggregate and Core-SDLC
   428	transition history. It does not join the run transaction. It consumes
   429	`governed_execution` integration events and submits idempotent commands through
   430	public APIs; failure is retried/reconciled and never simulated as
   431	cross-context atomicity.
   432	
   433	`policy` owns the authenticated, append-only `HumanDecisionRecord`.
   434	`governed_execution` owns the exact-subject `ConsumableAuthorityGrant` created
   435	from an eligible decision snapshot. The policy table is never mutated by the
   436	run transaction; grant issuance/consumption and permit issuance/consumption
   437	inside the authority cell are compare-and-swap protected.
   438	
   439	### 8.2 Atomic authority transaction
   440	
   441	One successful authority command atomically:
   442	
   443	```text
   444	compare expected run aggregate version
   445	  -> compare bound policy/module/route/workspace/evidence currency tokens
   446	  -> append ordered run/domain/audit event
   447	  -> update canonical current run row and version
   448	  -> bind exact gate/evidence/policy/module snapshots
   449	  -> issue or consume exact-subject authority grant/permit when required
   450	  -> insert zero or more outbound effect intents in the effect outbox
   451	  -> commit
   452	```
   453	
   454	If any write fails, none of them become visible. No external effect runs inside
   455	the database transaction. The outbox relay dispatches after commit using the
   456	recorded idempotency key.
   457	
   458	Gate evaluation and permit issuance are explicit state-only authority commands
   459	and normally create zero effects. An authorized workflow transition may create
   460	`0..N` effect intents, each with its own identity, arguments, destination,
   461	capabilities, idempotency semantics, and reconciliation policy. “Every
   462	transition creates one effect” is forbidden.
   463	
   464	Immediately before dispatch, the PEP rechecks the current policy activation,
   465	module/profile grant, route lock, workspace/base/candidate identity, evidence
   466	freshness, permit status, deadline, destination, and expected run version. A
   467	changed token denies dispatch or triggers re-authorization; it never inherits
   468	the stale intent's authority.
   469	
   470	### 8.3 State versus journal
   471	
   472	- The current row is the operational read source.
   473	- The ordered journal is the replay and audit oracle.
   474	- Snapshots may accelerate replay but never replace the journal.
   475	- A current-row/journal mismatch is corruption and blocks advancement; code
   476	  does not choose whichever source is convenient.
   477	- Other context projections are rebuilt or reconciled from canonical events.
   478	
   479	### 8.4 Reliable events outside governed execution
   480	
   481	Every stateful context commits its aggregate update, local audit event, and
   482	integration-event outbox row in its own unit of work. The governed-execution
   483	effect outbox is not the event-publication mechanism for `policy`,
   484	`work_management`, `module_governance`, `routing`, `identity_access`,
   485	`release_management`, or any other owner.
   486	
   487	Consumers are idempotent and record source context, aggregate ID/version,
   488	event ID/schema, correlation/causation IDs, and processed outcome. Cross-context
   489	delivery is at least once; duplicates and out-of-order messages are tested.
   490	
   491	## 9. Complete bounded-context ownership map
   492	
   493	### 9.1 Nonreplaceable authority contexts
   494	
   495	| Context | Owns | Public API | Persistence authority |
   496	|---|---|---|---|
   497	| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
   498	| `policy` | Roles, authorization-eligibility rules, risk-lane derivation, policy packages, activation, authorization snapshots, waivers and authenticated human-decision records | Authorization request/decision, active-policy and human-decision snapshots | Policy definitions and append-only decision history; never issues or consumes execution grants/permits |
   499	| `assurance` | Claims, evidence envelopes, qualified checker results, exact-subject evidence snapshots, and `GateEvaluation` | Evidence ingestion/query, checker result, snapshot and gate-evaluation APIs | Sole evidence/gate-evaluation record owner; does not own review observations, qualify components, bind a run gate, or commit run state |
   500	| `module_governance` | Module catalog, descriptors, capability vocabulary, grants, compatibility, activation lifecycle | Module/grant/profile snapshots | Module and grant authority |
   501	| `identity_access` | Human/service identities, authentication, sessions, nonces, remote decision authentication, data classification, destination facts, secret references | Principal/session/secret-handle and destination-fact APIs | Identity and access authority; policy decides and the egress adapter enforces |
   502	
   503	### 9.2 Product and development contexts
   504	
   505	| Context | Owns | Attachment points |
   506	|---|---|---|
   507	| `product_definition` | Actors, problems/needs, hypotheses, product capabilities, requirements, acceptance examples, outcome measures, validation decisions, `CapabilityStatus` | Discovery/user research, product decisions, work intake, outcome review |
   508	| `work_management` | Projects, canonical `WorkItemStatus`, work class, portfolio/queues/WIP, dependencies/risks/issues, technical-debt records, accountable work roles, external issue mapping, Kanban projections | Core-SDLC transition API, GitHub intake, product/requirement links, governed-run/evidence integration |
   509	| `service_management` | Service catalog, service/capability ownership, supported versions, SLIs/SLOs/error budgets, support/escalation, maintenance and retirement triggers | Operations evidence, release catalog, product capability lifecycle |
   510	| `configuration_management` | Configuration-item registry, content-addressed baselines, status accounting, bidirectional traceability graph, functional/physical configuration audits | Product requirements, source/build/test/docs, release manifests, assurance evidence |
   511	| `supplier_governance` | Supplier/dependency adoption and reuse decisions, shared responsibility, version/support/vulnerability monitoring, concentration/exit plans | Packages, toolchains, providers, APIs, extensions, hosted services, Hermes upstream |
   512	| `resource_governance` | Local capacity, hierarchical cost/token/tool/output/network budgets, parent/child reservations, quotas, transitive usage attribution and provider-limit facts | Policy, routing, scheduling, agent runs, operations; never commercial billing |
   513	| `interaction_history` | User conversation/thread/message identity, continuity, search lifecycle, classification, retention, export and deletion | Delivery channels, context compilation, legacy session import |
   514	| `process_assurance` | SDLC policy conformance, tailoring profiles, human-role competence, process audits/nonconformance/corrective action, process improvement evidence, fleet experiment and calibration records | Core SDLC, work records, metrics, training/qualification and measurement-harness evidence |
   515	| `workspace` | Repository identity, worktree plans, branch/head validation, landing and cleanup | Git adapter, sandbox mounts |
   516	| `instruction_registry` | Atomic versioned instructions, precedence, applicability, checker bindings | Policy and packet compilation |
   517	| `context_compilation` | Resolved source manifests, packet compilation, context budget, conflicts, provenance | Deterministic and recorded stochastic retrieval |
   518	| `analytical_review` | Review specifications, requests, attempts, observations, verdicts, parsing and independence evaluations | Native and tool-bearing review transports; publishes immutable review references to assurance |
   519	| `routing` | Provider/model/transport/runtime/auth identities, one-route assignment locks, health, failure and governed-redispatch facts | Official runtime and provider adapters; no fallback chain |
   520	| `qualification` | Checker, module, route, and isolation-profile qualification | Frozen fixtures, canaries, holdouts |
   521	| `effectiveness` | Whole-workflow paired evaluation, causal ablations, owner-facing scorecards | Evaluation runners and artifacts |
   522	| `agent_collaboration` | Typed worker assignments/offers, atomic claims, fenced leases, heartbeats/liveness, mailboxes, Ranex-owned dispatch graphs and fan-out/join, role separation, worker attempts, results and handoffs | Official leaf runtime adapters; workers cannot delegate or coordinate and the context never owns `RunStatus`, work state, gate, permit, effect, merge, or release |
   523	| `repository_intelligence` | Source graph/index, language coverage, freshness, unsupported-analysis states | Atlas/tree-sitter or simpler index strategies |
   524	| `knowledge` | Skills, project memory, learned records, quarantine, sanitization, transfer approvals | Packet sources and explicitly scoped worker reads |
   525	| `scheduling` | Schedules, authenticated triggers, catch-up rules, trigger lifecycle | Cron, webhooks, external timers |
   526	| `delivery` | Channel-neutral messages, commands, decision challenges, rendering, delivery receipts | CLI, TUI, web, phone, GitHub adapters |
   527	| `artifact_management` | Content-addressed blobs, classification, access, retention, legal hold, expiry, purge | Filesystem/object-store adapters |
   528	
   529	### 9.3 Operations, evolution, and boundary contexts
   530	

exec
/bin/bash -lc "nl -ba docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | sed -n '730,855p;1038,1070p;1138,1160p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   730	    required_result: "PASS"
   731	    failure_outcome: "BLOCK"
   732	  - provision_id: "HERMES-PROMOTION-057"
   733	    status: "PROMOTED"
   734	    guard_id: "PRODUCT_IDENTITY_EXCLUDES_HERMES_AND_NOUS_BRANDING"
   735	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1703"
   736	    source_end_line: 1706
   737	    check_class: "RELEASE_FITNESS"
   738	    blocking_stage: "RELEASE"
   739	    provision: "No product-facing package name, CLI command, config root, header, telemetry tag, help screen, screenshot, generated asset, or default presents Hermes/Nous branding outside an explicit migration warning or legally required attribution."
   740	    required_result: "PASS"
   741	    failure_outcome: "BLOCK"
   742	  - provision_id: "HERMES-PROMOTION-058"
   743	    status: "PROMOTED"
   744	    guard_id: "CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION"
   745	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1901"
   746	    source_end_line: 1901
   747	    check_class: "ARCHITECTURE_CONTRACT"
   748	    blocking_stage: "IMPLEMENTATION_START"
   749	    provision: "The clean kernel contains a shared-identity facility that provides shared identity and a canonical-serialization facility that provides canonical serialization."
   750	    required_result: "PASS"
   751	    failure_outcome: "BLOCK"
   752	  - provision_id: "HERMES-PROMOTION-059"
   753	    status: "PROMOTED"
   754	    guard_id: "EXECUTION_AGGREGATE_TRANSITIONS_THROUGH_PURE_REDUCER"
   755	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1902"
   756	    source_end_line: 1902
   757	    check_class: "RUNTIME_FITNESS"
   758	    blocking_stage: "GATE_ADVANCE"
   759	    provision: "The clean kernel contains an Execution aggregate, and Execution state transitions are computed by its pure reducer."
   760	    required_result: "PASS"
   761	    failure_outcome: "BLOCK"
   762	  - provision_id: "HERMES-PROMOTION-060"
   763	    status: "PROMOTED"
   764	    guard_id: "CANONICAL_RELATIONAL_EXECUTION_STATE_HAS_EXPLICIT_VERSION"
   765	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
   766	    source_end_line: 1903
   767	    check_class: "ARCHITECTURE_CONTRACT"
   768	    blocking_stage: "GATE_ADVANCE"
   769	    provision: "The clean kernel persists canonical execution state and its associated version in relational storage."
   770	    required_result: "PASS"
   771	    failure_outcome: "BLOCK"
   772	  - provision_id: "HERMES-PROMOTION-061"
   773	    status: "PROMOTED"
   774	    guard_id: "TRANSITION_AUDIT_JOURNAL_AND_OUTBOX_SHARE_ONE_SQLITE_UNIT_OF_WORK"
   775	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
   776	    source_end_line: 1904
   777	    check_class: "AUTHORITY_FITNESS"
   778	    blocking_stage: "GATE_ADVANCE"
   779	    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
   780	    required_result: "PASS"
   781	    failure_outcome: "BLOCK"
   782	  - provision_id: "HERMES-PROMOTION-062"
   783	    status: "PROMOTED"
   784	    guard_id: "EVENT_SOURCING_IS_EXECUTION_ONLY_AND_REPLAY_MIGRATION_QUALIFIED"
   785	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
   786	    source_end_line: 1906
   787	    check_class: "MIGRATION_FITNESS"
   788	    blocking_stage: "GATE_ADVANCE"
   789	    provision: "The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope."
   790	    required_result: "PASS"
   791	    failure_outcome: "BLOCK"
   792	  - provision_id: "HERMES-PROMOTION-063"
   793	    status: "PROMOTED"
   794	    guard_id: "FAIL_CLOSED_APPLICATION_CONTROL_PEP_USES_PURE_DECISIONS_AND_DETERMINISTIC_POLICY"
   795	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1907"
   796	    source_end_line: 1908
   797	    check_class: "AUTHORITY_FITNESS"
   798	    blocking_stage: "GATE_ADVANCE"
   799	    provision: "The clean kernel contains an application-control policy-enforcement point that is fail-closed, uses pure domain decisions, and invokes a simple deterministic policy adapter."
   800	    required_result: "PASS"
   801	    failure_outcome: "BLOCK"
   802	  - provision_id: "HERMES-PROMOTION-064"
   803	    status: "PROMOTED"
   804	    guard_id: "ARCHITECTURE_IMPORT_TESTS_PRECEDE_FEATURE_CODE"
   805	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1909"
   806	    source_end_line: 1909
   807	    check_class: "STATIC_FITNESS"
   808	    blocking_stage: "IMPLEMENTATION_START"
   809	    provision: "Architecture import tests are part of the clean-kernel contract and must be present and passing before feature code is admitted."
   810	    required_result: "PASS"
   811	    failure_outcome: "BLOCK"
   812	  - provision_id: "HERMES-PROMOTION-065"
   813	    status: "PROMOTED"
   814	    guard_id: "CLEAN_KERNEL_EXIT_REQUIRES_REPLAY_CRASH_TESTS_WITHOUT_HERMES_IMPORT"
   815	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1911"
   816	    source_end_line: 1911
   817	    check_class: "RUNTIME_FITNESS"
   818	    blocking_stage: "GATE_ADVANCE"
   819	    provision: "The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import."
   820	    required_result: "PASS"
   821	    failure_outcome: "BLOCK"
   822	owner_decisions:
   823	  - provision_id: "HERMES-OWNER-DECISION-001"
   824	    status: "OWNER_DECISION_REQUIRED"
   825	    guard_id: "OWNER_DECIDES_WORKFLOW_EVENT_SCHEMA_AND_UPCASTER_POLICY"
   826	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2125"
   827	    source_end_line: 2125
   828	    blocking_stage: "IMPLEMENTATION_START"
   829	    decision_subject: "Canonical Ranex workflow and event schema and upcaster policy."
   830	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   831	    owner_decision_ref: null
   832	    default: null
   833	    absence_outcome: "BLOCK"
   834	    activation_without_decision: "DENIED"
   835	  - provision_id: "HERMES-OWNER-DECISION-002"
   836	    status: "OWNER_DECISION_REQUIRED"
   837	    guard_id: "OWNER_DECIDES_LOCAL_RUNNER_OR_MATURE_DURABLE_RUNTIME"
   838	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2126"
   839	    source_end_line: 2127
   840	    blocking_stage: "PRODUCTION_READY"
   841	    decision_subject: "Whether the local runner passes the required crash and recovery tests or a mature durable runtime is justified."
   842	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   843	    owner_decision_ref: null
   844	    default: null
   845	    absence_outcome: "BLOCK"
   846	    activation_without_decision: "DENIED"
   847	  - provision_id: "HERMES-OWNER-DECISION-003"
   848	    status: "OWNER_DECISION_REQUIRED"
   849	    guard_id: "OWNER_DECIDES_EXACT_AUTHORITY_TRANSACTION_OWNERSHIP"
   850	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2128"
   851	    source_end_line: 2129
   852	    blocking_stage: "IMPLEMENTATION_START"
   853	    decision_subject: "Exact transaction ownership across execution, evidence, permit, and work projections."
   854	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   855	    owner_decision_ref: null
  1038	    activation_without_decision: "DENIED"
  1039	  - provision_id: "HERMES-OWNER-DECISION-019"
  1040	    status: "OWNER_DECISION_REQUIRED"
  1041	    guard_id: "OWNER_DECIDES_STRONG_CONSISTENCY_CONTEXT_GROUPING"
  1042	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:865"
  1043	    source_end_line: 870
  1044	    blocking_stage: "IMPLEMENTATION_START"
  1045	    decision_subject: "Whether execution, gate, permit, and effect intent are submodules of one strong-consistency Governed Execution context or independently persistent contexts."
  1046	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1047	    owner_decision_ref: null
  1048	    default: null
  1049	    absence_outcome: "BLOCK"
  1050	    activation_without_decision: "DENIED"
  1051	  - provision_id: "HERMES-OWNER-DECISION-020"
  1052	    status: "OWNER_DECISION_REQUIRED"
  1053	    guard_id: "OWNER_DECIDES_EXECUTION_EVENT_SOURCING_AFTER_QUALIFICATION"
  1054	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
  1055	    source_end_line: 1906
  1056	    blocking_stage: "IMPLEMENTATION_START"
  1057	    decision_subject: "Whether to activate event sourcing for the Execution aggregate after its replay and migration tests justify that choice; the decision cannot authorize event sourcing for any other module."
  1058	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1059	    owner_decision_ref: null
  1060	    default: null
  1061	    absence_outcome: "BLOCK"
  1062	    activation_without_decision: "DENIED"
  1063	research_only:
  1064	  - provision_id: "HERMES-RESEARCH-ONLY-001"
  1065	    status: "RESEARCH_ONLY"
  1066	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:226"
  1067	    source_end_line: 341
  1068	    reason_code: "FACT_NOT_NORMATIVE"
  1069	    reason: "The pinned-source audit and scorecard are historical evidence about Hermes 0.19.0, not Ranex runtime obligations."
  1070	  - provision_id: "HERMES-RESEARCH-ONLY-002"
  1138	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1913"
  1139	    source_end_line: 2004
  1140	    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
  1141	    reason: "Phases 2 through 6 remain implementation planning in this revision; the owner decision promoting Phase 1 does not silently promote their sequencing or exit schedules."
  1142	```
  1143	
  1144	## Noncompensating fitness functions
  1145	
  1146	| ID | Required result |
  1147	|---|---|
  1148	| `FF-HERMES-PROMOTION-001` | The generated registry exactly projects all 65 promoted provisions, 20 owner-decision gates, and 13 research-only dispositions; every cited line and excerpt digest resolves to the immutable research source. |
  1149	| `FF-HERMES-GUARD-001` | Every promoted or owner-decision guard is unique and matches `^[A-Z][A-Z0-9_]*$`; a missing, malformed, duplicated, or hyphenated guard fails validation. |
  1150	| `FF-HERMES-OWNER-DECISION-001` | Every genuine owner choice is `OWNER_DECISION_REQUIRED`, has no default or synthetic decision reference, and blocks activation or progression while the exact accepted owner decision is absent. |
  1151	| `FF-HERMES-LEGAL-001` | License, copyright, provenance, required-attribution, legal-notice, and Git-history preservation are non-waivable release obligations; separate de-commercialization, package, network, credential, data, and branding checks remain noncompensating owner requirements rather than being mislabeled as law. |
  1152	| `FF-HERMES-KERNEL-001` | The clean-kernel inventory contains all eight Phase 1 provisions, binds only research lines 1901–1911, retains the one-SQLite-unit-of-work and Execution-only event-sourcing boundaries, requires import-test precedence, and cannot advance its gate without replay, crash-boundary, and no-Hermes-import proof. |
  1153	
  1154	## What remains research
  1155	
  1156	The thirteen `RESEARCH_ONLY` rows retain historical facts, advisory assessments,
  1157	illustrative shapes, conditional migration guidance, and unselected product
  1158	scope. They are not silently discarded. Promotion later requires a new accepted
  1159	ADR, an exact line binding, a deterministic checker contract, and migration or
  1160	compatibility treatment where applicable.

exec
/bin/bash -lc "nl -ba docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md | sed -n '1,260p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	Reading additional input from stdin...
     2	OpenAI Codex v0.146.0
     3	--------
     4	workdir: /home/soultransit/devtony/ranex
     5	model: gpt-5.6-sol
     6	provider: openai
     7	approval: never
     8	sandbox: danger-full-access
     9	reasoning effort: high
    10	reasoning summaries: none
    11	session id: 019fb2c5-36b3-7583-8275-0e950a874841
    12	--------
    13	user
    14	# Prior-art sweep B — deterministic execution and run visualization
    15	
    16	Ranex is a governance harness that runs AI agents under enforced constraints, on
    17	a single host, with SQLite as its transactional authority. The working premise of
    18	this task: **Ranex is not novel. Established standards and production systems
    19	already solve most of what it does.** Find them, and report precisely what Ranex
    20	should adopt, adapt, or deliberately diverge from — and where it truly has no
    21	prior art.
    22	
    23	Do not design anything. Find what exists.
    24	
    25	## Your assigned layers
    26	
    27	1. **Deterministic workflow execution and replay** — how production systems
    28	   guarantee that replaying a recorded history reproduces the same state and the
    29	   same commands, and how they version workflow definitions so old runs stay
    30	   replayable.
    31	2. **Durable state + event journal + outbox in one transaction** — the
    32	   transactional-outbox and event-journal patterns, how real systems avoid
    33	   split-brain between a current-state snapshot and an append-only log, and
    34	   **how they detect or prevent the two disagreeing**.
    35	3. **Crash-boundary and replay testing** — how these systems actually *test*
    36	   crash recovery and replay determinism, as opposed to asserting it. What does a
    37	   credible crash test look like in practice?
    38	4. **Run-graph visualization** — how CI and workflow systems render a live
    39	   execution graph derived from server-side state, including how they transport
    40	   live updates and how they avoid the browser inferring state.
    41	
    42	Known starting points, to verify and go beyond rather than accept from me:
    43	Temporal, Cadence, DBOS, Argo Workflows, Apache Airflow, Dagster, Kestra,
    44	GitHub Actions, Netflix Conductor, transactional outbox pattern, event sourcing
    45	with snapshots. Find others, including anything SQLite-specific.
    46	
    47	## What Ranex currently does — read it, cite it
    48	
    49	- `docs/architecture/decisions/ADR-0013-...md` provisions
    50	  `HERMES-PROMOTION-058` through `HERMES-PROMOTION-065` — the accepted kernel
    51	  obligations, including the one-SQLite-unit-of-work requirement.
    52	- The kernel R&D tracer is in a **separate worktree**:
    53	  `.claude/worktrees/kernel-tracer`, branch `feature/kernel-tracer`, with
    54	  untracked `src/` and `tests/`. Read especially
    55	  `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py`,
    56	  `src/ranex/governed_execution/domain/execution.py`, its
    57	  `migrations/001_execution_kernel.sql`, and the tests under `tests/replay/` and
    58	  `tests/resilience/`.
    59	- `docs/research/deterministic-run-graph-visualization-research-2026-07-30.md` —
    60	  an existing internal proposal for the run graph. Treat its technology claims as
    61	  claims to verify, not as conclusions.
    62	
    63	Two known open defects, given as context you must account for — not as things to
    64	re-find: the journal and the state snapshot can disagree with nothing detecting
    65	it, and the existing replay test compares the production reducer against itself.
    66	
    67	## Required output — one row per layer or sub-layer
    68	
    69	| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
    70	
    71	`Verdict` is exactly one of **ADOPT**, **ADAPT**, **DIVERGE** (with the reason it
    72	must differ), or **NOVEL** (state what you searched).
    73	
    74	`Specific delta` must be actionable. "Look at Temporal" is useless. "Temporal
    75	proves replay determinism by re-executing history against the current definition
    76	and failing on non-determinism, which the test at
    77	`tests/replay/...:59-66` cannot do because both sides consume the same in-memory
    78	events" is useful.
    79	
    80	Answer these directly, with citations:
    81	- How do production systems make a snapshot and a journal provably agree?
    82	- What is the accepted way to test crash recovery, concretely?
    83	- Is one-SQLite-unit-of-work a recognized pattern with known limits, or unusual?
    84	
    85	## Non-negotiables
    86	
    87	- **Verify externally.** Use web search/fetch for every external claim; if those
    88	  tools are unavailable, use `curl`. Cite a URL per claim. Mark anything you
    89	  could not verify as `UNVERIFIED` rather than asserting it. Recalled knowledge
    90	  stated as fact is a failure of this task.
    91	- **Licence check.** For anything recommended for adoption, report its licence
    92	  and whether it is compatible with a source-available, all-rights-reserved
    93	  product preserving future commercial optionality (`LICENSE-RANEX.md`). Flag
    94	  copyleft or commercially encumbered terms — this applies to libraries and to
    95	  any front-end graph library the run-graph proposal names.
    96	- **Read-only.** Do not modify, create, or delete any file in the repository.
    97	- **Report inferences** in a separate section, marked as inference.
    98	- **Maturity matters.** Prefer production systems with named adopters. State the
    99	  adoption evidence.
   100	
   101	## Output sections
   102	
   103	`Mapping table`, `Adopt shortlist` (ranked, with licence), `Answers to the three
   104	direct questions`, `Genuinely novel`, `Inferences`, `Search coverage`.
   105	codex
   106	I’ll audit the cited Ranex artifacts first, pin every current-state claim to exact lines, then verify each comparison against primary documentation, source repositories, licences, and adopter evidence. I’ll keep the repository strictly read-only and label any unsupported point `UNVERIFIED`.
   107	  → Inspect Ranex ADR, tracer implementation/tests, graph proposal, and licence with exact line references
   108	  • Research deterministic replay/versioning and concrete crash-test practices in primary sources
   109	  • Research atomic state+journal+outbox consistency, including SQLite patterns and limits
   110	  • Research live run-graph state transport/rendering, named adopters, and licences
   111	  • Synthesize mapping table, shortlist, direct answers, novelty, inferences, and search coverage
   112	exec
   113	/bin/bash -lc "pwd && rg --files docs/architecture/decisions docs/research .claude/worktrees/kernel-tracer 2>/dev/null | rg '(ADR-0013|deterministic-run-graph|execution_store\\.py|execution\\.py|001_execution_kernel\\.sql|tests/(replay|resilience)|LICENSE-RANEX)'" in /home/soultransit/devtony/ranex
   114	 succeeded in 0ms:
   115	/home/soultransit/devtony/ranex
   116	docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
   117	docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
   118	.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py
   119	.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py
   120	.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py
   121	.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py
   122	.claude/worktrees/kernel-tracer/LICENSE-RANEX.md
   123	.claude/worktrees/kernel-tracer/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
   124	.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py
   125	.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
   126	.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
   127	
   128	exec
   129	/bin/bash -lc 'nl -ba docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md' in /home/soultransit/devtony/ranex
   130	exec
   131	/bin/bash -lc 'wc -l docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md docs/research/deterministic-run-graph-visualization-research-2026-07-30.md LICENSE-RANEX.md 2>/dev/null || true' in /home/soultransit/devtony/ranex
   132	exec
   133	/bin/bash -lc 'wc -l .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql .claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py .claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py' in /home/soultransit/devtony/ranex
   134	 succeeded in 0ms:
   135	  1187 docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
   136	   736 docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
   137	    95 LICENSE-RANEX.md
   138	  2018 total
   139	
   140	 succeeded in 0ms:
   141	  420 .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
   142	  237 .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py
   143	   73 .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
   144	   66 .claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py
   145	   98 .claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py
   146	  894 total
   147	
   148	 succeeded in 0ms:
   149	     1	# ADR-0013: Promote Hermes Research Obligations into a Closed Audit Contract
   150	     2	
   151	     3	| Field | Value |
   152	     4	|---|---|
   153	     5	| ADR ID | `ADR-0013` |
   154	     6	| Version | `1.4.0` |
   155	     7	| Status | `ACCEPTED` |
   156	     8	| Decision owner | Human owner |
   157	     9	| Decision date | 2026-07-29 |
   158	    10	| Effective revision | Working tree based on `a66267776c`; executable documentation projection generated and runtime evidence pending |
   159	    11	| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
   160	    12	| Affected contexts | `configuration_management`, `governed_execution`, `policy`, `assurance`, `module_governance`, `compatibility`, `migration`, `provenance_compliance`, `release_management`, and `process_assurance` |
   161	    13	| RFC | Not required; direct owner requirement to make already accepted Hermes-research obligations line-auditable and fail closed |
   162	    14	| Supersedes | No fixed decision; adds a closed, line-bound projection of obligations already accepted through ADR-0003, ADR-0005, ADR-0006, and ADR-0011 |
   163	    15	| Review/expiry date | On any source-research correction, promoted-provision change, owner-choice resolution, or de-commercialization/legal-control change |
   164	    16	| Compatibility/migration class | Additive executable documentation contract; runtime implementation remains unassessed |
   165	    17	| Security/data class | Public architecture decision; legal, credential, package, runtime, and release evidence retain their own classification |
   166	    18	
   167	    19	## Revision history
   168	    20	
   169	    21	### 1.4.0 — 2026-07-30
   170	    22	
   171	    23	This revision repairs one unsupported qualifier found by a post-1.3.0
   172	    24	fidelity audit after three earlier repair rounds had missed it.
   173	    25	
   174	    26	- **DEFECT 9** — `HERMES-PROMOTION-059` claimed that *every* Execution
   175	    27	  state transition is computed by the pure reducer, while the cited
   176	    28	  research line 1902 supports only "Implement an `Execution` aggregate
   177	    29	  and pure reducer." The unsupported `every` qualifier is removed; the
   178	    30	  provision now states that Execution state transitions are computed by
   179	    31	  the aggregate's pure reducer, without a universal-coverage claim the
   180	    32	  research does not make.
   181	    33	
   182	    34	### 1.3.0 — 2026-07-30
   183	    35	
   184	    36	This revision records the second full-row fidelity audit and closes the
   185	    37	remaining unpinned-row blind spot.
   186	    38	
   187	    39	- **DEFECT 6** — `HERMES-PROMOTION-002` now states only that the new
   188	    40	  dependency-clean kernel is built beside Hermes; `HERMES-PROMOTION-004`
   189	    41	  removes the unsupported `only` exclusivity; `HERMES-PROMOTION-009` removes
   190	    42	  the unsupported `replaceable` qualifier; `HERMES-PROMOTION-014` restores
   191	    43	  first-party module access to application/kernel public APIs; and
   192	    44	  `HERMES-PROMOTION-017` uses the cited side-effect-free requirement without
   193	    45	  an invented example list.
   194	    46	- **DEFECT 7** — The 1.2.0 history now records its previously omitted
   195	    47	  normative changes to `HERMES-PROMOTION-058` and
   196	    48	  `HERMES-PROMOTION-059`.
   197	    49	- **DEFECT 8** — Exact-text fidelity pins now cover all 65 promoted
   198	    50	  provisions, all 20 owner-decision subjects, and all 13 research-only
   199	    51	  dispositions. Any paraphrase of a pinned text fails generation and
   200	    52	  validation.
   201	    53	
   202	    54	### 1.2.0 — 2026-07-29
   203	    55	
   204	    56	This revision records the result of placing every promoted provision beside
   205	    57	its cited research excerpt and comparing obligation class, scope, and
   206	    58	specificity.
   207	    59	
   208	    60	- **Previously omitted 1.2.0 normative changes (recorded retroactively in
   209	    61	  1.3.0)** — `HERMES-PROMOTION-058` renamed
   210	    62	  `SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION_DEFINE_KERNEL_RECORDS` to
   211	    63	  `CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION` and
   212	    64	  removed the unsupported `kernel records` scope.
   213	    65	  `HERMES-PROMOTION-059` replaced “whose state evolution is computed by a pure
   214	    66	  reducer without observable side effects” with “every Execution state
   215	    67	  transition is computed by its pure reducer.”
   216	    68	- **DEFECT 1** — `HERMES-PROMOTION-011` again requires removal of the Nous
   217	    69	  commercial subsystem, and `HERMES-PROMOTION-041` again requires removal of
   218	    70	  Hermes/Nous branding. Neither action is represented as an asserted
   219	    71	  absent-state.
   220	    72	- **DEFECT 2** — `HERMES-PROMOTION-040` restores rebranding as the specific
   221	    73	  context that does not authorize erasing legal notices or Git history.
   222	    74	- **DEFECT 3** — `HERMES-PROMOTION-041` restores package metadata, remote
   223	    75	  endpoints, headers, telemetry tags, help text, screenshots, generated
   224	    76	  assets, and defaults as eight separately checkable surfaces. The same
   225	    77	  row-by-row specificity check restores the cited item-level terms in
   226	    78	  `HERMES-PROMOTION-037`, `HERMES-PROMOTION-038`,
   227	    79	  `HERMES-PROMOTION-044`, `HERMES-PROMOTION-045`,
   228	    80	  `HERMES-PROMOTION-050`, `HERMES-PROMOTION-051`,
   229	    81	  `HERMES-PROMOTION-053`, `HERMES-PROMOTION-054`, and
   230	    82	  `HERMES-PROMOTION-057`.
   231	    83	- **DEFECT 4** — `HERMES-PROMOTION-005`, `HERMES-PROMOTION-010`,
   232	    84	  `HERMES-PROMOTION-012`, and `HERMES-PROMOTION-018` remove the unsupported
   233	    85	  `governed`, `accepted`, generalized domain-package, and `authority`
   234	    86	  qualifiers and restore their exact cited scopes.
   235	    87	- **DEFECT 5** — Phase 1 lines 1899–1912 remain represented by
   236	    88	  `HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`, rather than by an
   237	    89	  exclusion-equivalence claim. Phase 0/0A activity and Phase 2–6 sequencing
   238	    90	  and exit material remain research-only and are not represented by promoted
   239	    91	  gates.
   240	    92	
   241	    93	### 1.1.0 — 2026-07-29
   242	    94	
   243	    95	By owner decision, this revision overturns the prior “implementation
   244	    96	sequencing, not fixed authority” exclusion for Phase 1. Research lines
   245	    97	1899–1912 define the clean kernel's binding structural inventory and behavior,
   246	    98	not a delivery schedule.
   247	    99	
   248	   100	This revision adds eight promoted provisions,
   249	   101	`HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`:
   250	   102	
   251	   103	1. shared identity and canonical serialization;
   252	   104	2. the `Execution` aggregate and pure reducer;
   253	   105	3. canonical relational execution state and version;
   254	   106	4. the append-only transition/audit journal and outbox in one SQLite unit of
   255	   107	   work;
   256	   108	5. the evidence-gated, `Execution`-only event-sourcing boundary;
   257	   109	6. the fail-closed application-control PEP, pure domain decisions, and
   258	   110	   deterministic policy adapter;
   259	   111	7. architecture import tests before feature code; and
   260	   112	8. the replay, crash-boundary, and no-Hermes-import exit gate.

exec
/bin/bash -lc 'rg -n "''^Mapping table|''^## Mapping|''^Adopt shortlist|''^## Adopt|Answers to|snapshot|journal|Temporal|replay" docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md | tail -n 100' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
5922:    66	    assert replayed.version == len(events) == 4
5926:    31	def test_failure_between_journal_and_outbox_leaves_no_partial_state(
5963:    68	                readiness_snapshot_ref="snapshot:sha256:crash-ready",
5972:    77	    assert store.count_journal_entries(RUN_ID) == 1
5981:    86	                (SELECT COUNT(*) FROM execution_journal
6099:   146	        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
6192:   226	def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
6206:   132	- the same workflow/interpreter versions and ordered recorded inputs replay to
6246:   211	    A["governed_execution<br/>committed current rows + journal facts"]
6248:   213	    S["GET snapshot<br/>topology + current state"]
6277:   242	boundary. It must not replay raw events to discover canonical state.
6345:   402	The first response is always a complete snapshot. The snapshot and its cursor
6348:   405	replays every retained delta after it or requires a new snapshot. Each delta
6360:   417	untrusted deltas and refetches the full snapshot. Slow polling is an acceptable
6402:   523	- A cursor gap or digest mismatch causes a full snapshot refetch.
6403:   524	- The snapshot state and resumable cursor are captured atomically; a simulated
6422:   543	Projection replay/query results must agree with the canonical committed rows.
6484:   779	    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
6494:   789	    provision: "The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope."
6524:   819	    provision: "The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import."
6537:  1057	    decision_subject: "Whether to activate event sourcing for the Execution aggregate after its replay and migration tests justify that choice; the decision cannot authorize event sourcing for any other module."
6550:  1152	| `FF-HERMES-KERNEL-001` | The clean-kernel inventory contains all eight Phase 1 provisions, binds only research lines 1901–1911, retains the one-SQLite-unit-of-work and Execution-only event-sourcing boundaries, requires import-test precedence, and cannot advance its gate without replay, crash-boundary, and no-Hermes-import proof. |
6633:The run-graph proposal’s authority boundary is well supported, but its transport choice is not special: Airflow currently streams server-computed task summaries as NDJSON and then refreshes, while Kubernetes’ mature list/watch protocol supplies the stronger snapshot-cursor-gap semantics. SSE is therefore an adapter choice, not prior art for correctness.
6641:web search: Netflix Conductor deterministic replay workflow version history official docs ...
6647:  ✓ Verify deterministic replay and workflow-versioning prior art from primary sources
6648:  ✓ Verify transactional journal/snapshot/outbox and SQLite crash-testing prior art
6655:  ✓ Verify deterministic replay and workflow-versioning prior art from primary sources
6656:  ✓ Verify transactional journal/snapshot/outbox and SQLite crash-testing prior art
6663:- The SQLite transaction prevents torn writes but does not prove that journal and snapshot mean the same thing.
6669:## Mapping table
6673:| [ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742), [execution.py:226](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226), [replay test:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:59) | The ADR requires canonical events and a pure reducer. `replay_execution()` loops over events using the production reducer. The test manually loops over that same reducer and compares the two results. | Temporal reconstructs workflow state from append-only history and checks emitted commands during replay; SDK replay fails on non-determinism ([architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md), [Python replayer](https://github.com/temporalio/sdk-python)). Cadence replays actual production histories and supports production-history shadowing ([replay and shadowing](https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing)). | ADOPT | Replace the self-oracle with durable history fixtures containing expected command/outbox records. Run the current workflow implementation against those histories and fail at the first command mismatch. Include a mutation test that intentionally changes command order or payload and proves the replay test fails. |
6674:| [execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58), [graph research:250](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:250) | The persisted snapshot carries a `workflow_request_ref`, but not an immutable workflow-definition digest or interpreter version. The graph document proposes such pins; the tracer does not implement them. | Temporal’s `GetVersion` records a marker in history so old and new code paths remain replayable ([Go API](https://github.com/temporalio/sdk-go/blob/main/workflow/workflow.go)). Cadence uses the same marker model ([versioning](https://cadenceworkflow.io/docs/go-client/workflow-versioning)). Airflow DAG bundles record the exact bundle version, including Git commit, used by a run ([DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)). DBOS associates workflows with application versions and supports history patch markers ([versioning tutorial](https://docs.dbos.dev/golang/tutorials/upgrading-workflows)). GitHub reruns at the original commit SHA/ref ([rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)). | ADOPT | Persist immutable workflow-definition, policy, interpreter, and serialization-version identities when a run is created. Recovery must select a compatible worker/definition or fail explicitly; never silently execute an old history using an unmarked new definition. Keep compatibility paths until all affected runs have drained. |
6676:| [migration:1](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1), [execution_store.py:223](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223) | `BEGIN IMMEDIATE` encloses snapshot, journal, and outbox writes. An exception rolls the transaction back. | The transactional-outbox pattern writes business data and an outgoing-message record in the same database transaction ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). DBOS supports placing application data and workflow durability records in the same SQL transaction, including SQLite-backed `sql.DB` use ([DBOS transactions](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)). | ADOPT | Retain the one-database transaction. Treat it as atomicity only, not as replay or semantic-agreement proof. Ensure every state transition is forced through this unit of work and exercise rollback at each write boundary. |
6677:| [migration:3](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3), [execution_store.py:390](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390) | State stores `last_event_id`, version, and canonical JSON. Journal rows store resulting state/digests. Loading validates relational columns against JSON in the same state row, but does not validate the state against the journal head. No constraint makes the referenced event the actual head. | Temporal stores the latest history event ID in mutable state and regards mutable state as valid only when that event is reflected in history; persistence failure forces reload ([History Service consistency](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)). Event-sourced systems make the event stream authoritative and snapshots rebuildable ([Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)); Marten’s inline projections update with events in one ACID transaction ([projection lifecycle](https://martendb.io/tutorials/read-model-projections)). Axon discards incompatible/corrupt snapshots and replays the stream ([snapshotting](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)). | ADAPT | Define one recovery authority—normally the journal. On write and integrity scan, require the snapshot’s event ID/version/digest to equal the exact journal head and its recorded resulting-state digest. Periodically replay original journal bytes and compare the reconstructed state with the snapshot. If verification fails, quarantine or rebuild the snapshot rather than loading it as authoritative. |
6678:| [migration:35](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35) | The outbox is append-only and transactionally tied to the journal, but the scoped tracer has no durable dispatch/acknowledgement lifecycle. | AWS specifies a separate relay, ordered records, possible redelivery, and idempotent consumers ([transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). NServiceBus persists business data and outgoing messages in phase one, then sends and records dispatch completion in phase two; duplicate detection is based on stable message identity ([NServiceBus outbox](https://docs.particular.net/nservicebus/outbox/?version=core_9)). | ADOPT | Add a durable phase-two dispatch record or receipt keyed by the existing stable event/message ID. Test the crash windows before send, after send but before receipt, and after receipt. Consumers must be idempotent because exactly-once external delivery is not supplied by the SQLite transaction. |
6679:| [crash test:31](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31) | A trigger raises `ABORT` before an outbox insert. The same Python process catches the error, rolls back, and checks that old rows remain. | SQLite’s own crash harness has a parent spawn a writer child, kills it at varied points, reopens the database, requires the database to be wholly old or wholly new, runs `PRAGMA integrity_check`, and uses a special VFS to reorder or corrupt unsynced writes ([SQLite testing](https://sqlite.org/testing.html)). | ADOPT | Keep the trigger test as a rollback unit test, but do not call it a crash test. Add an external controller that kills a separate writer process at every state/journal/outbox/commit boundary, reopens from a fresh process, and asserts integrity plus an all-old-or-all-new semantic tuple. Add fault-injecting VFS tests if power-loss durability is claimed. |
6680:| [execution_store.py:183](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183) | Enables foreign keys and `synchronous=FULL`, but does not set or verify `journal_mode`. | SQLite documents the filesystem assumptions behind atomic commit ([atomic commit](https://www.sqlite.org/atomiccommit.html)); `FULL` has different guarantees in rollback-journal and WAL modes, while rollback mode may require `EXTRA` for power-loss durability ([synchronous](https://sqlite.org/pragma.html#pragma_synchronous)). WAL is same-host only, allows one writer, and does not make multi-attached-database transactions atomic as a set ([WAL limitations](https://www.sqlite.org/wal.html)). | ADAPT | Declare and verify a supported SQLite durability profile at startup: journal mode, synchronous mode, filesystem locality, and integrity settings. Run crash certification against exactly that profile. Refuse unsupported network filesystems or document the reduced guarantee. |
6682:| [graph research:383](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:383) | Proposes GET snapshot plus cursor-bearing SSE, with refetch after a gap. | Kubernetes List/Watch couples a snapshot with `resourceVersion`; watches begin strictly after that version, and `410 Gone` requires relisting ([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)). Airflow 3.2 streams server-computed grid summaries progressively while runs are pending ([release notes](https://airflow.apache.org/docs/apache-airflow/3.2.0/release_notes.html)). | ADAPT | Preserve snapshot-plus-monotonic-cursor, resumability, deduplication, and explicit gap/relist behavior. SSE is a suitable single-host transport, but correctness must be transport-independent so polling or WebSocket clients observe the same versioned projection. |
6686:## Adopt shortlist
6688:1. **Temporal/Cadence history replay semantics**
6690:   Adopt actual-history replay, command matching, non-determinism failure, and recorded version markers—not either server wholesale. Temporal is MIT ([licence](https://github.com/temporalio/temporal/blob/main/LICENSE)); Cadence is Apache-2.0 ([licence](https://github.com/cadence-workflow/cadence/blob/master/LICENSE)). Both are compatible with Ranex’s commercial optionality when notices and Apache patent terms are observed. Temporal reports more than 1,000 paying cloud customers including NVIDIA, Snap, Alaska Airlines, Retool, and Turo ([adoption evidence](https://temporal.io/news/temporal-surpasses-1-000-active-customers-milestone-in-just-over-a-year)).
6692:2. **SQLite-backed transactional state/journal/outbox**
6714:- **Restate:** useful corroboration because it explicitly reports an exact journal mismatch during replay and pins invocations to deployments ([errors](https://docs.restate.dev/references/errors), [versioning](https://docs.restate.dev/services/versioning)), but its server is BSL 1.1 with service-use restrictions before conversion to Apache-2.0 ([licence](https://github.com/restatedev/restate/blob/main/LICENSE)). Study the protocol; do not embed it without commercial/legal review.
6720:## Answers to the three direct questions
6722:### 1. How do production systems make a snapshot and a journal provably agree?
6726:1. **The event stream is the recovery authority.** A snapshot is a cache or materialized projection that can be discarded and rebuilt, not a second independent truth ([Microsoft Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing), [Axon snapshots](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)).
6728:2. **The snapshot identifies the precise journal position it represents.** Temporal stores the latest history event ID in mutable state and considers that state valid only when the event is reflected in history ([Temporal History Service](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)).
6732:4. **They verify or rebuild.** Replay from original event bytes must reproduce the snapshot, and a corrupt or incompatible snapshot falls back to full stream replay.
6734:Ranex currently has only item 3. One transaction proves that all three writes committed or none did; it does **not** prove that the snapshot was computed from the journal event it names. A shared implementation bug can atomically commit mutually inconsistent data.
6753:For Ranex, the semantic oracle must check the tuple together: state head, journal head, outbox intent/receipt, reconstructed reducer state, and stable message identities. Retrying after an ambiguous send must also demonstrate idempotency.
6764:- Durability depends on journal mode, synchronous settings, filesystem behavior, and hardware assumptions.
6773:The exact composition—single-host SQLite authority, AI-agent governance constraints, policy identities, deterministic replay, and a server-owned graph—may be Ranex-specific as a product package. Its constituent correctness mechanisms are established:
6775:- history replay and non-determinism detection;
6778:- event-sourced snapshots;
6782:- snapshot-plus-cursor live-update protocols.
6788:- **INFERENCE:** The normal store path probably writes a mutually consistent snapshot and journal because one reducer invocation produces both. A reducer bug, serialization bug, migration, or direct database write can nevertheless commit disagreement because no persisted cross-check rejects it.
6789:- **INFERENCE:** The active database’s journal mode is `UNVERIFIED`. The connection code does not set it; SQLite’s default is normally rollback journal, but journal mode is persistent and could have been changed externally.
6798:- Temporal, Cadence, DBOS, Restate and Azure Durable workflow versioning/replay.
6800:- Axon event upcasting/snapshots, Marten inline projections, Microsoft event sourcing.
6805:- Kubernetes List/Watch snapshot/cursor/gap semantics.
6807:- Named adoption evidence for Temporal, DBOS, Argo, and Airflow.
6811:- **Netflix/OSS Conductor:** current materials claim replay/rerun capabilities, but I did not verify a primary contract equivalent to Temporal’s “re-execute history and compare emitted commands.” The original Netflix repository is also archived. Deterministic replay equivalence is therefore **UNVERIFIED** for this report.
6812:- **Dagster:** snapshot/reexecution material was found, but it did not add a stronger result than the verified Temporal/Airflow/Argo evidence.
6813:- **Kestra:** flow revisions are verified ([revision documentation](https://kestra.io/docs/concepts/revision)), but no stronger command-by-command deterministic replay guarantee was verified.
6820:- The SQLite transaction prevents torn writes but does not prove that journal and snapshot mean the same thing.
6826:## Mapping table
6830:| [ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742), [execution.py:226](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226), [replay test:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:59) | The ADR requires canonical events and a pure reducer. `replay_execution()` loops over events using the production reducer. The test manually loops over that same reducer and compares the two results. | Temporal reconstructs workflow state from append-only history and checks emitted commands during replay; SDK replay fails on non-determinism ([architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md), [Python replayer](https://github.com/temporalio/sdk-python)). Cadence replays actual production histories and supports production-history shadowing ([replay and shadowing](https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing)). | ADOPT | Replace the self-oracle with durable history fixtures containing expected command/outbox records. Run the current workflow implementation against those histories and fail at the first command mismatch. Include a mutation test that intentionally changes command order or payload and proves the replay test fails. |
6831:| [execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58), [graph research:250](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:250) | The persisted snapshot carries a `workflow_request_ref`, but not an immutable workflow-definition digest or interpreter version. The graph document proposes such pins; the tracer does not implement them. | Temporal’s `GetVersion` records a marker in history so old and new code paths remain replayable ([Go API](https://github.com/temporalio/sdk-go/blob/main/workflow/workflow.go)). Cadence uses the same marker model ([versioning](https://cadenceworkflow.io/docs/go-client/workflow-versioning)). Airflow DAG bundles record the exact bundle version, including Git commit, used by a run ([DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)). DBOS associates workflows with application versions and supports history patch markers ([versioning tutorial](https://docs.dbos.dev/golang/tutorials/upgrading-workflows)). GitHub reruns at the original commit SHA/ref ([rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)). | ADOPT | Persist immutable workflow-definition, policy, interpreter, and serialization-version identities when a run is created. Recovery must select a compatible worker/definition or fail explicitly; never silently execute an old history using an unmarked new definition. Keep compatibility paths until all affected runs have drained. |
6833:| [migration:1](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1), [execution_store.py:223](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223) | `BEGIN IMMEDIATE` encloses snapshot, journal, and outbox writes. An exception rolls the transaction back. | The transactional-outbox pattern writes business data and an outgoing-message record in the same database transaction ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). DBOS supports placing application data and workflow durability records in the same SQL transaction, including SQLite-backed `sql.DB` use ([DBOS transactions](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)). | ADOPT | Retain the one-database transaction. Treat it as atomicity only, not as replay or semantic-agreement proof. Ensure every state transition is forced through this unit of work and exercise rollback at each write boundary. |
6834:| [migration:3](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3), [execution_store.py:390](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390) | State stores `last_event_id`, version, and canonical JSON. Journal rows store resulting state/digests. Loading validates relational columns against JSON in the same state row, but does not validate the state against the journal head. No constraint makes the referenced event the actual head. | Temporal stores the latest history event ID in mutable state and regards mutable state as valid only when that event is reflected in history; persistence failure forces reload ([History Service consistency](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)). Event-sourced systems make the event stream authoritative and snapshots rebuildable ([Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)); Marten’s inline projections update with events in one ACID transaction ([projection lifecycle](https://martendb.io/tutorials/read-model-projections)). Axon discards incompatible/corrupt snapshots and replays the stream ([snapshotting](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)). | ADAPT | Define one recovery authority—normally the journal. On write and integrity scan, require the snapshot’s event ID/version/digest to equal the exact journal head and its recorded resulting-state digest. Periodically replay original journal bytes and compare the reconstructed state with the snapshot. If verification fails, quarantine or rebuild the snapshot rather than loading it as authoritative. |
6835:| [migration:35](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35) | The outbox is append-only and transactionally tied to the journal, but the scoped tracer has no durable dispatch/acknowledgement lifecycle. | AWS specifies a separate relay, ordered records, possible redelivery, and idempotent consumers ([transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). NServiceBus persists business data and outgoing messages in phase one, then sends and records dispatch completion in phase two; duplicate detection is based on stable message identity ([NServiceBus outbox](https://docs.particular.net/nservicebus/outbox/?version=core_9)). | ADOPT | Add a durable phase-two dispatch record or receipt keyed by the existing stable event/message ID. Test the crash windows before send, after send but before receipt, and after receipt. Consumers must be idempotent because exactly-once external delivery is not supplied by the SQLite transaction. |
6836:| [crash test:31](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31) | A trigger raises `ABORT` before an outbox insert. The same Python process catches the error, rolls back, and checks that old rows remain. | SQLite’s own crash harness has a parent spawn a writer child, kills it at varied points, reopens the database, requires the database to be wholly old or wholly new, runs `PRAGMA integrity_check`, and uses a special VFS to reorder or corrupt unsynced writes ([SQLite testing](https://sqlite.org/testing.html)). | ADOPT | Keep the trigger test as a rollback unit test, but do not call it a crash test. Add an external controller that kills a separate writer process at every state/journal/outbox/commit boundary, reopens from a fresh process, and asserts integrity plus an all-old-or-all-new semantic tuple. Add fault-injecting VFS tests if power-loss durability is claimed. |
6837:| [execution_store.py:183](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183) | Enables foreign keys and `synchronous=FULL`, but does not set or verify `journal_mode`. | SQLite documents the filesystem assumptions behind atomic commit ([atomic commit](https://www.sqlite.org/atomiccommit.html)); `FULL` has different guarantees in rollback-journal and WAL modes, while rollback mode may require `EXTRA` for power-loss durability ([synchronous](https://sqlite.org/pragma.html#pragma_synchronous)). WAL is same-host only, allows one writer, and does not make multi-attached-database transactions atomic as a set ([WAL limitations](https://www.sqlite.org/wal.html)). | ADAPT | Declare and verify a supported SQLite durability profile at startup: journal mode, synchronous mode, filesystem locality, and integrity settings. Run crash certification against exactly that profile. Refuse unsupported network filesystems or document the reduced guarantee. |
6839:| [graph research:383](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:383) | Proposes GET snapshot plus cursor-bearing SSE, with refetch after a gap. | Kubernetes List/Watch couples a snapshot with `resourceVersion`; watches begin strictly after that version, and `410 Gone` requires relisting ([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)). Airflow 3.2 streams server-computed grid summaries progressively while runs are pending ([release notes](https://airflow.apache.org/docs/apache-airflow/3.2.0/release_notes.html)). | ADAPT | Preserve snapshot-plus-monotonic-cursor, resumability, deduplication, and explicit gap/relist behavior. SSE is a suitable single-host transport, but correctness must be transport-independent so polling or WebSocket clients observe the same versioned projection. |
6843:## Adopt shortlist
6845:1. **Temporal/Cadence history replay semantics**
6847:   Adopt actual-history replay, command matching, non-determinism failure, and recorded version markers—not either server wholesale. Temporal is MIT ([licence](https://github.com/temporalio/temporal/blob/main/LICENSE)); Cadence is Apache-2.0 ([licence](https://github.com/cadence-workflow/cadence/blob/master/LICENSE)). Both are compatible with Ranex’s commercial optionality when notices and Apache patent terms are observed. Temporal reports more than 1,000 paying cloud customers including NVIDIA, Snap, Alaska Airlines, Retool, and Turo ([adoption evidence](https://temporal.io/news/temporal-surpasses-1-000-active-customers-milestone-in-just-over-a-year)).
6849:2. **SQLite-backed transactional state/journal/outbox**
6871:- **Restate:** useful corroboration because it explicitly reports an exact journal mismatch during replay and pins invocations to deployments ([errors](https://docs.restate.dev/references/errors), [versioning](https://docs.restate.dev/services/versioning)), but its server is BSL 1.1 with service-use restrictions before conversion to Apache-2.0 ([licence](https://github.com/restatedev/restate/blob/main/LICENSE)). Study the protocol; do not embed it without commercial/legal review.
6877:## Answers to the three direct questions
6879:### 1. How do production systems make a snapshot and a journal provably agree?
6883:1. **The event stream is the recovery authority.** A snapshot is a cache or materialized projection that can be discarded and rebuilt, not a second independent truth ([Microsoft Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing), [Axon snapshots](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)).
6885:2. **The snapshot identifies the precise journal position it represents.** Temporal stores the latest history event ID in mutable state and considers that state valid only when the event is reflected in history ([Temporal History Service](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)).
6889:4. **They verify or rebuild.** Replay from original event bytes must reproduce the snapshot, and a corrupt or incompatible snapshot falls back to full stream replay.
6891:Ranex currently has only item 3. One transaction proves that all three writes committed or none did; it does **not** prove that the snapshot was computed from the journal event it names. A shared implementation bug can atomically commit mutually inconsistent data.
6910:For Ranex, the semantic oracle must check the tuple together: state head, journal head, outbox intent/receipt, reconstructed reducer state, and stable message identities. Retrying after an ambiguous send must also demonstrate idempotency.
6921:- Durability depends on journal mode, synchronous settings, filesystem behavior, and hardware assumptions.
6930:The exact composition—single-host SQLite authority, AI-agent governance constraints, policy identities, deterministic replay, and a server-owned graph—may be Ranex-specific as a product package. Its constituent correctness mechanisms are established:
6932:- history replay and non-determinism detection;
6935:- event-sourced snapshots;
6939:- snapshot-plus-cursor live-update protocols.
6945:- **INFERENCE:** The normal store path probably writes a mutually consistent snapshot and journal because one reducer invocation produces both. A reducer bug, serialization bug, migration, or direct database write can nevertheless commit disagreement because no persisted cross-check rejects it.
6946:- **INFERENCE:** The active database’s journal mode is `UNVERIFIED`. The connection code does not set it; SQLite’s default is normally rollback journal, but journal mode is persistent and could have been changed externally.
6955:- Temporal, Cadence, DBOS, Restate and Azure Durable workflow versioning/replay.
6957:- Axon event upcasting/snapshots, Marten inline projections, Microsoft event sourcing.
6962:- Kubernetes List/Watch snapshot/cursor/gap semantics.
6964:- Named adoption evidence for Temporal, DBOS, Argo, and Airflow.
6968:- **Netflix/OSS Conductor:** current materials claim replay/rerun capabilities, but I did not verify a primary contract equivalent to Temporal’s “re-execute history and compare emitted commands.” The original Netflix repository is also archived. Deterministic replay equivalence is therefore **UNVERIFIED** for this report.
6969:- **Dagster:** snapshot/reexecution material was found, but it did not add a stronger result than the verified Temporal/Airflow/Argo evidence.
6970:- **Kestra:** flow revisions are verified ([revision documentation](https://kestra.io/docs/concepts/revision)), but no stronger command-by-command deterministic replay guarantee was verified.

exec
/bin/bash -lc "nl -ba docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | sed -n '742,855p;1046,1068p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   742	  - provision_id: "HERMES-PROMOTION-058"
   743	    status: "PROMOTED"
   744	    guard_id: "CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION"
   745	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1901"
   746	    source_end_line: 1901
   747	    check_class: "ARCHITECTURE_CONTRACT"
   748	    blocking_stage: "IMPLEMENTATION_START"
   749	    provision: "The clean kernel contains a shared-identity facility that provides shared identity and a canonical-serialization facility that provides canonical serialization."
   750	    required_result: "PASS"
   751	    failure_outcome: "BLOCK"
   752	  - provision_id: "HERMES-PROMOTION-059"
   753	    status: "PROMOTED"
   754	    guard_id: "EXECUTION_AGGREGATE_TRANSITIONS_THROUGH_PURE_REDUCER"
   755	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1902"
   756	    source_end_line: 1902
   757	    check_class: "RUNTIME_FITNESS"
   758	    blocking_stage: "GATE_ADVANCE"
   759	    provision: "The clean kernel contains an Execution aggregate, and Execution state transitions are computed by its pure reducer."
   760	    required_result: "PASS"
   761	    failure_outcome: "BLOCK"
   762	  - provision_id: "HERMES-PROMOTION-060"
   763	    status: "PROMOTED"
   764	    guard_id: "CANONICAL_RELATIONAL_EXECUTION_STATE_HAS_EXPLICIT_VERSION"
   765	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
   766	    source_end_line: 1903
   767	    check_class: "ARCHITECTURE_CONTRACT"
   768	    blocking_stage: "GATE_ADVANCE"
   769	    provision: "The clean kernel persists canonical execution state and its associated version in relational storage."
   770	    required_result: "PASS"
   771	    failure_outcome: "BLOCK"
   772	  - provision_id: "HERMES-PROMOTION-061"
   773	    status: "PROMOTED"
   774	    guard_id: "TRANSITION_AUDIT_JOURNAL_AND_OUTBOX_SHARE_ONE_SQLITE_UNIT_OF_WORK"
   775	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
   776	    source_end_line: 1904
   777	    check_class: "AUTHORITY_FITNESS"
   778	    blocking_stage: "GATE_ADVANCE"
   779	    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
   780	    required_result: "PASS"
   781	    failure_outcome: "BLOCK"
   782	  - provision_id: "HERMES-PROMOTION-062"
   783	    status: "PROMOTED"
   784	    guard_id: "EVENT_SOURCING_IS_EXECUTION_ONLY_AND_REPLAY_MIGRATION_QUALIFIED"
   785	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
   786	    source_end_line: 1906
   787	    check_class: "MIGRATION_FITNESS"
   788	    blocking_stage: "GATE_ADVANCE"
   789	    provision: "The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope."
   790	    required_result: "PASS"
   791	    failure_outcome: "BLOCK"
   792	  - provision_id: "HERMES-PROMOTION-063"
   793	    status: "PROMOTED"
   794	    guard_id: "FAIL_CLOSED_APPLICATION_CONTROL_PEP_USES_PURE_DECISIONS_AND_DETERMINISTIC_POLICY"
   795	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1907"
   796	    source_end_line: 1908
   797	    check_class: "AUTHORITY_FITNESS"
   798	    blocking_stage: "GATE_ADVANCE"
   799	    provision: "The clean kernel contains an application-control policy-enforcement point that is fail-closed, uses pure domain decisions, and invokes a simple deterministic policy adapter."
   800	    required_result: "PASS"
   801	    failure_outcome: "BLOCK"
   802	  - provision_id: "HERMES-PROMOTION-064"
   803	    status: "PROMOTED"
   804	    guard_id: "ARCHITECTURE_IMPORT_TESTS_PRECEDE_FEATURE_CODE"
   805	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1909"
   806	    source_end_line: 1909
   807	    check_class: "STATIC_FITNESS"
   808	    blocking_stage: "IMPLEMENTATION_START"
   809	    provision: "Architecture import tests are part of the clean-kernel contract and must be present and passing before feature code is admitted."
   810	    required_result: "PASS"
   811	    failure_outcome: "BLOCK"
   812	  - provision_id: "HERMES-PROMOTION-065"
   813	    status: "PROMOTED"
   814	    guard_id: "CLEAN_KERNEL_EXIT_REQUIRES_REPLAY_CRASH_TESTS_WITHOUT_HERMES_IMPORT"
   815	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1911"
   816	    source_end_line: 1911
   817	    check_class: "RUNTIME_FITNESS"
   818	    blocking_stage: "GATE_ADVANCE"
   819	    provision: "The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import."
   820	    required_result: "PASS"
   821	    failure_outcome: "BLOCK"
   822	owner_decisions:
   823	  - provision_id: "HERMES-OWNER-DECISION-001"
   824	    status: "OWNER_DECISION_REQUIRED"
   825	    guard_id: "OWNER_DECIDES_WORKFLOW_EVENT_SCHEMA_AND_UPCASTER_POLICY"
   826	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2125"
   827	    source_end_line: 2125
   828	    blocking_stage: "IMPLEMENTATION_START"
   829	    decision_subject: "Canonical Ranex workflow and event schema and upcaster policy."
   830	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   831	    owner_decision_ref: null
   832	    default: null
   833	    absence_outcome: "BLOCK"
   834	    activation_without_decision: "DENIED"
   835	  - provision_id: "HERMES-OWNER-DECISION-002"
   836	    status: "OWNER_DECISION_REQUIRED"
   837	    guard_id: "OWNER_DECIDES_LOCAL_RUNNER_OR_MATURE_DURABLE_RUNTIME"
   838	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2126"
   839	    source_end_line: 2127
   840	    blocking_stage: "PRODUCTION_READY"
   841	    decision_subject: "Whether the local runner passes the required crash and recovery tests or a mature durable runtime is justified."
   842	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   843	    owner_decision_ref: null
   844	    default: null
   845	    absence_outcome: "BLOCK"
   846	    activation_without_decision: "DENIED"
   847	  - provision_id: "HERMES-OWNER-DECISION-003"
   848	    status: "OWNER_DECISION_REQUIRED"
   849	    guard_id: "OWNER_DECIDES_EXACT_AUTHORITY_TRANSACTION_OWNERSHIP"
   850	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2128"
   851	    source_end_line: 2129
   852	    blocking_stage: "IMPLEMENTATION_START"
   853	    decision_subject: "Exact transaction ownership across execution, evidence, permit, and work projections."
   854	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   855	    owner_decision_ref: null
  1046	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1047	    owner_decision_ref: null
  1048	    default: null
  1049	    absence_outcome: "BLOCK"
  1050	    activation_without_decision: "DENIED"
  1051	  - provision_id: "HERMES-OWNER-DECISION-020"
  1052	    status: "OWNER_DECISION_REQUIRED"
  1053	    guard_id: "OWNER_DECIDES_EXECUTION_EVENT_SOURCING_AFTER_QUALIFICATION"
  1054	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
  1055	    source_end_line: 1906
  1056	    blocking_stage: "IMPLEMENTATION_START"
  1057	    decision_subject: "Whether to activate event sourcing for the Execution aggregate after its replay and migration tests justify that choice; the decision cannot authorize event sourcing for any other module."
  1058	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1059	    owner_decision_ref: null
  1060	    default: null
  1061	    absence_outcome: "BLOCK"
  1062	    activation_without_decision: "DENIED"
  1063	research_only:
  1064	  - provision_id: "HERMES-RESEARCH-ONLY-001"
  1065	    status: "RESEARCH_ONLY"
  1066	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:226"
  1067	    source_end_line: 341
  1068	    reason_code: "FACT_NOT_NORMATIVE"

exec
/bin/bash -lc "nl -ba docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md | sed -n '6660,6800p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
  6660	The sweep found no genuinely novel mechanism in the four assigned layers. Ranex’s principal gaps are narrower and more concrete:
  6661	
  6662	- Replay currently has no independent oracle.
  6663	- The SQLite transaction prevents torn writes but does not prove that journal and snapshot mean the same thing.
  6664	- The resilience test exercises a caught SQLite error, not a process or power-loss crash.
  6665	- The graph proposal is aligned with production precedent, but its correctness contract matters more than SSE or the renderer.
  6666	
  6667	No repository files were modified.
  6668	
  6669	## Mapping table
  6670	
  6671	| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
  6672	|---|---|---|---|---|
  6673	| [ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742), [execution.py:226](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226), [replay test:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:59) | The ADR requires canonical events and a pure reducer. `replay_execution()` loops over events using the production reducer. The test manually loops over that same reducer and compares the two results. | Temporal reconstructs workflow state from append-only history and checks emitted commands during replay; SDK replay fails on non-determinism ([architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md), [Python replayer](https://github.com/temporalio/sdk-python)). Cadence replays actual production histories and supports production-history shadowing ([replay and shadowing](https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing)). | ADOPT | Replace the self-oracle with durable history fixtures containing expected command/outbox records. Run the current workflow implementation against those histories and fail at the first command mismatch. Include a mutation test that intentionally changes command order or payload and proves the replay test fails. |
  6674	| [execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58), [graph research:250](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:250) | The persisted snapshot carries a `workflow_request_ref`, but not an immutable workflow-definition digest or interpreter version. The graph document proposes such pins; the tracer does not implement them. | Temporal’s `GetVersion` records a marker in history so old and new code paths remain replayable ([Go API](https://github.com/temporalio/sdk-go/blob/main/workflow/workflow.go)). Cadence uses the same marker model ([versioning](https://cadenceworkflow.io/docs/go-client/workflow-versioning)). Airflow DAG bundles record the exact bundle version, including Git commit, used by a run ([DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)). DBOS associates workflows with application versions and supports history patch markers ([versioning tutorial](https://docs.dbos.dev/golang/tutorials/upgrading-workflows)). GitHub reruns at the original commit SHA/ref ([rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)). | ADOPT | Persist immutable workflow-definition, policy, interpreter, and serialization-version identities when a run is created. Recovery must select a compatible worker/definition or fail explicitly; never silently execute an old history using an unmarked new definition. Keep compatibility paths until all affected runs have drained. |
  6675	| [execution_store.py:128](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128) | Events have a strict schema version, but no verified upcaster or migration path for old event bytes. | Axon stores event revisions and applies ordered upcasters without rewriting immutable stored events ([event versioning](https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/)). Microsoft’s event-sourcing guidance likewise calls for versioned events/upcasting and sequence tracking ([Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)). | ADOPT | Introduce an explicit revision-to-current upcaster chain and permanent fixtures for every released event revision. Replay tests must begin from original stored bytes, not newly constructed current-version event objects. |
  6676	| [migration:1](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1), [execution_store.py:223](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223) | `BEGIN IMMEDIATE` encloses snapshot, journal, and outbox writes. An exception rolls the transaction back. | The transactional-outbox pattern writes business data and an outgoing-message record in the same database transaction ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). DBOS supports placing application data and workflow durability records in the same SQL transaction, including SQLite-backed `sql.DB` use ([DBOS transactions](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)). | ADOPT | Retain the one-database transaction. Treat it as atomicity only, not as replay or semantic-agreement proof. Ensure every state transition is forced through this unit of work and exercise rollback at each write boundary. |
  6677	| [migration:3](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3), [execution_store.py:390](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390) | State stores `last_event_id`, version, and canonical JSON. Journal rows store resulting state/digests. Loading validates relational columns against JSON in the same state row, but does not validate the state against the journal head. No constraint makes the referenced event the actual head. | Temporal stores the latest history event ID in mutable state and regards mutable state as valid only when that event is reflected in history; persistence failure forces reload ([History Service consistency](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)). Event-sourced systems make the event stream authoritative and snapshots rebuildable ([Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)); Marten’s inline projections update with events in one ACID transaction ([projection lifecycle](https://martendb.io/tutorials/read-model-projections)). Axon discards incompatible/corrupt snapshots and replays the stream ([snapshotting](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)). | ADAPT | Define one recovery authority—normally the journal. On write and integrity scan, require the snapshot’s event ID/version/digest to equal the exact journal head and its recorded resulting-state digest. Periodically replay original journal bytes and compare the reconstructed state with the snapshot. If verification fails, quarantine or rebuild the snapshot rather than loading it as authoritative. |
  6678	| [migration:35](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35) | The outbox is append-only and transactionally tied to the journal, but the scoped tracer has no durable dispatch/acknowledgement lifecycle. | AWS specifies a separate relay, ordered records, possible redelivery, and idempotent consumers ([transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). NServiceBus persists business data and outgoing messages in phase one, then sends and records dispatch completion in phase two; duplicate detection is based on stable message identity ([NServiceBus outbox](https://docs.particular.net/nservicebus/outbox/?version=core_9)). | ADOPT | Add a durable phase-two dispatch record or receipt keyed by the existing stable event/message ID. Test the crash windows before send, after send but before receipt, and after receipt. Consumers must be idempotent because exactly-once external delivery is not supplied by the SQLite transaction. |
  6679	| [crash test:31](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31) | A trigger raises `ABORT` before an outbox insert. The same Python process catches the error, rolls back, and checks that old rows remain. | SQLite’s own crash harness has a parent spawn a writer child, kills it at varied points, reopens the database, requires the database to be wholly old or wholly new, runs `PRAGMA integrity_check`, and uses a special VFS to reorder or corrupt unsynced writes ([SQLite testing](https://sqlite.org/testing.html)). | ADOPT | Keep the trigger test as a rollback unit test, but do not call it a crash test. Add an external controller that kills a separate writer process at every state/journal/outbox/commit boundary, reopens from a fresh process, and asserts integrity plus an all-old-or-all-new semantic tuple. Add fault-injecting VFS tests if power-loss durability is claimed. |
  6680	| [execution_store.py:183](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183) | Enables foreign keys and `synchronous=FULL`, but does not set or verify `journal_mode`. | SQLite documents the filesystem assumptions behind atomic commit ([atomic commit](https://www.sqlite.org/atomiccommit.html)); `FULL` has different guarantees in rollback-journal and WAL modes, while rollback mode may require `EXTRA` for power-loss durability ([synchronous](https://sqlite.org/pragma.html#pragma_synchronous)). WAL is same-host only, allows one writer, and does not make multi-attached-database transactions atomic as a set ([WAL limitations](https://www.sqlite.org/wal.html)). | ADAPT | Declare and verify a supported SQLite durability profile at startup: journal mode, synchronous mode, filesystem locality, and integrity settings. Run crash certification against exactly that profile. Refuse unsupported network filesystems or document the reduced guarantee. |
  6681	| [graph research:206](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:206), [graph research:227](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:227) | Proposes a server-side run projection and says the browser must not reconstruct workflow semantics from raw events. | Argo stores a server-side node map containing each node’s phase/status and retains the resolved workflow specification ([Argo fields](https://argoproj.github.io/argo-workflows/fields/)). Airflow’s graph loads versioned structure and attaches streamed server-produced task-instance summaries by node ID without recalculating layout semantics ([Airflow graph source](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx)). | ADOPT | Implement the proposal’s server ownership literally: server-assigned stable node/edge IDs, topology/version identity, node phase, attempts, and terminal reason. The browser may lay out, filter, and decorate this state, but must not derive execution phase, eligibility, or topology from event order. |
  6682	| [graph research:383](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:383) | Proposes GET snapshot plus cursor-bearing SSE, with refetch after a gap. | Kubernetes List/Watch couples a snapshot with `resourceVersion`; watches begin strictly after that version, and `410 Gone` requires relisting ([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)). Airflow 3.2 streams server-computed grid summaries progressively while runs are pending ([release notes](https://airflow.apache.org/docs/apache-airflow/3.2.0/release_notes.html)). | ADAPT | Preserve snapshot-plus-monotonic-cursor, resumability, deduplication, and explicit gap/relist behavior. SSE is a suitable single-host transport, but correctness must be transport-independent so polling or WebSocket clients observe the same versioned projection. |
  6683	| [graph research:425](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:425), [licence register:707](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:707) | Proposes React Flow with Dagre, and ELK as a possible upgrade. | React Flow is MIT-licensed and its base library permits commercial use ([repository/licence](https://github.com/xyflow/xyflow)); Dagre is MIT ([licence](https://github.com/dagrejs/dagre/blob/master/LICENSE).) | ADOPT | React Flow and Dagre are compatible with Ranex’s commercial optionality, subject to retaining MIT notices. Keep them as view/layout dependencies only; do not place authoritative execution logic in custom nodes or layout code. |
  6684	| [graph research:425](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:425), [licence register:717](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:717) | Names ELK as an upgrade and Dagu as a reference system. | `elkjs` is EPL-2.0 ([licence](https://github.com/kieler/elkjs/blob/master/LICENSE.md)); Dagu is GPL-3.0 ([licence](https://github.com/dagucloud/dagu/blob/main/LICENSE)). | DIVERGE | Do not copy or embed Dagu code in an all-rights-reserved product without a separate commercial licence. Treat ELK as an optional, legal-reviewed dependency because EPL-2.0 carries reciprocal source/notice obligations for the covered program; it should not be the unqualified default. Behavioral study of either system is not restricted. |
  6685	
  6686	## Adopt shortlist
  6687	
  6688	1. **Temporal/Cadence history replay semantics**
  6689	
  6690	   Adopt actual-history replay, command matching, non-determinism failure, and recorded version markers—not either server wholesale. Temporal is MIT ([licence](https://github.com/temporalio/temporal/blob/main/LICENSE)); Cadence is Apache-2.0 ([licence](https://github.com/cadence-workflow/cadence/blob/master/LICENSE)). Both are compatible with Ranex’s commercial optionality when notices and Apache patent terms are observed. Temporal reports more than 1,000 paying cloud customers including NVIDIA, Snap, Alaska Airlines, Retool, and Turo ([adoption evidence](https://temporal.io/news/temporal-surpasses-1-000-active-customers-milestone-in-just-over-a-year)).
  6691	
  6692	2. **SQLite-backed transactional state/journal/outbox**
  6693	
  6694	   Keep the current one-unit-of-work direction, adding explicit head agreement and delivery receipts. SQLite is public domain ([copyright](https://www.sqlite.org/copyright.html)); DBOS’s open-source SDK is MIT ([licence](https://github.com/dbos-inc/dbos-transact-py/blob/main/LICENSE)); the AWS outbox pattern itself is architecture guidance, not licensed library code. DBOS names Walmart, Notion, Roche, Yutori, and Bristol Myers Squibb as users/customers ([customer stories](https://www.dbos.dev/customer-stories)).
  6695	
  6696	3. **SQLite’s real crash-test model**
  6697	
  6698	   Adopt the parent/child crash loop, all-old-or-all-new oracle, integrity checks, and—where the guarantee warrants it—fault-injecting VFS. SQLite’s public-domain status is fully compatible. This is much stronger evidence than an application exception test.
  6699	
  6700	4. **Argo/Airflow server-owned graph projection plus Kubernetes cursor semantics**
  6701	
  6702	   Adopt the behavioral contracts, not necessarily their implementations. Argo, Airflow, and Kubernetes are Apache-2.0 and commercially compatible with notice/patent compliance ([Argo licence](https://github.com/argoproj/argo-workflows/blob/main/LICENSE), [Airflow licence](https://github.com/apache/airflow/blob/main/LICENSE), [Kubernetes licence](https://github.com/kubernetes/kubernetes)). Argo is CNCF graduated with reported production use by Adobe, BlackRock, Capital One, Google, Intuit, and Tesla ([CNCF evidence](https://www.cncf.io/announcements/2022/12/06/the-cloud-native-computing-foundation-announces-argo-has-graduated/)). Apache reported Airflow use across more than 200 organizations including Adobe, Airbnb, Etsy, Google, Lyft, PayPal, Reddit, and Twitter ([ASF evidence](https://news.apache.org/foundation/entry/the-apache-software-foundation-announces44)).
  6703	
  6704	5. **React Flow plus Dagre**
  6705	
  6706	   Both are MIT and compatible with the Ranex licence if notices are preserved. They are suitable view dependencies because their output need not be authoritative.
  6707	
  6708	6. **Axon-style event revisions and upcasters**
  6709	
  6710	   Adopt the revision/upcaster behavior and fixtures. Axon Framework is Apache-2.0 ([repository/licence](https://github.com/AxonIQ/AxonFramework)), compatible with future commercial use subject to normal Apache obligations.
  6711	
  6712	Licence caveats:
  6713	
  6714	- **Restate:** useful corroboration because it explicitly reports an exact journal mismatch during replay and pins invocations to deployments ([errors](https://docs.restate.dev/references/errors), [versioning](https://docs.restate.dev/services/versioning)), but its server is BSL 1.1 with service-use restrictions before conversion to Apache-2.0 ([licence](https://github.com/restatedev/restate/blob/main/LICENSE)). Study the protocol; do not embed it without commercial/legal review.
  6715	- **Dagu:** GPL-3.0; unsuitable for code incorporation into the present proprietary product without separate terms.
  6716	- **ELK:** EPL-2.0; potentially usable, but reciprocal obligations need legal review.
  6717	- **NServiceBus:** cited for its protocol, not recommended as a code dependency; it is a commercial product.
  6718	- This is an engineering compatibility assessment, not legal advice.
  6719	
  6720	## Answers to the three direct questions
  6721	
  6722	### 1. How do production systems make a snapshot and a journal provably agree?
  6723	
  6724	They use four complementary controls:
  6725	
  6726	1. **The event stream is the recovery authority.** A snapshot is a cache or materialized projection that can be discarded and rebuilt, not a second independent truth ([Microsoft Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing), [Axon snapshots](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)).
  6727	
  6728	2. **The snapshot identifies the precise journal position it represents.** Temporal stores the latest history event ID in mutable state and considers that state valid only when the event is reflected in history ([Temporal History Service](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)).
  6729	
  6730	3. **Events and synchronous projections are committed atomically.** Marten calls this an inline projection and updates it in the same ACID transaction as the events ([Marten projections](https://martendb.io/tutorials/read-model-projections)).
  6731	
  6732	4. **They verify or rebuild.** Replay from original event bytes must reproduce the snapshot, and a corrupt or incompatible snapshot falls back to full stream replay.
  6733	
  6734	Ranex currently has only item 3. One transaction proves that all three writes committed or none did; it does **not** prove that the snapshot was computed from the journal event it names. A shared implementation bug can atomically commit mutually inconsistent data.
  6735	
  6736	Hashes help detect byte disagreement, but they cannot prove that the reducer or command semantics were correct.
  6737	
  6738	### 2. What is the accepted way to test crash recovery, concretely?
  6739	
  6740	SQLite’s own method is the credible baseline:
  6741	
  6742	1. A parent process creates a known durable starting database.
  6743	2. A separate child performs the transition.
  6744	3. The parent kills the child at systematically varied write/commit points.
  6745	4. A fresh process reopens the real database file.
  6746	5. It runs `PRAGMA integrity_check` and relevant foreign-key checks.
  6747	6. It accepts only the complete old state or complete new state—never a mixture.
  6748	7. It repeats across crash points and compound failures.
  6749	8. For power-loss claims, a test VFS models lost, reordered, or corrupted unsynced writes.
  6750	
  6751	That procedure is documented by SQLite itself ([testing methodology](https://sqlite.org/testing.html)). Ranex’s trigger-induced `ABORT` is a useful rollback test, but no process dies, the application catches the exception, and the filesystem is never exposed to an interrupted commit.
  6752	
  6753	For Ranex, the semantic oracle must check the tuple together: state head, journal head, outbox intent/receipt, reconstructed reducer state, and stable message identities. Retrying after an ambiguous send must also demonstrate idempotency.
  6754	
  6755	### 3. Is one-SQLite-unit-of-work recognized, or unusual?
  6756	
  6757	It is a recognized local-authority form of the transactional-outbox/event-store pattern, not an unusual invention. DBOS explicitly supports colocating application changes with durable workflow records in one SQL transaction, including SQLite use ([DBOS transaction tutorial](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)); AWS documents the general same-database outbox pattern ([AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)).
  6758	
  6759	Its limits are well known:
  6760	
  6761	- SQLite serializes writers; WAL still has only one writer at a time.
  6762	- WAL is intended for processes on the same host, not a network filesystem.
  6763	- A transaction spanning multiple attached databases is not atomic as a set in WAL mode.
  6764	- Durability depends on journal mode, synchronous settings, filesystem behavior, and hardware assumptions.
  6765	- External effects cannot join the SQLite transaction. The outbox gives atomic intent plus at-least-once relay, requiring idempotent consumers.
  6766	
  6767	These limits are documented by SQLite’s [WAL](https://www.sqlite.org/wal.html), [synchronous pragma](https://sqlite.org/pragma.html#pragma_synchronous), and [atomic-commit assumptions](https://www.sqlite.org/atomiccommit.html).
  6768	
  6769	## Genuinely novel
  6770	
  6771	No row in the assigned layers merits **NOVEL**.
  6772	
  6773	The exact composition—single-host SQLite authority, AI-agent governance constraints, policy identities, deterministic replay, and a server-owned graph—may be Ranex-specific as a product package. Its constituent correctness mechanisms are established:
  6774	
  6775	- history replay and non-determinism detection;
  6776	- workflow-definition/version pinning;
  6777	- event revisions and upcasters;
  6778	- event-sourced snapshots;
  6779	- transactional outbox;
  6780	- SQLite crash certification;
  6781	- server-owned graph projections;
  6782	- snapshot-plus-cursor live-update protocols.
  6783	
  6784	The Ranex-specific governance vocabulary and policy semantics may contain original product work, but that falls outside proof that these execution, storage, recovery, or visualization mechanisms lack prior art.
  6785	
  6786	## Inferences
  6787	
  6788	- **INFERENCE:** The normal store path probably writes a mutually consistent snapshot and journal because one reducer invocation produces both. A reducer bug, serialization bug, migration, or direct database write can nevertheless commit disagreement because no persisted cross-check rejects it.
  6789	- **INFERENCE:** The active database’s journal mode is `UNVERIFIED`. The connection code does not set it; SQLite’s default is normally rollback journal, but journal mode is persistent and could have been changed externally.
  6790	- **INFERENCE:** The scoped tracer demonstrates outbox persistence, not a complete relay protocol. No durable publisher/receipt implementation was found in the requested tracer paths.
  6791	- **INFERENCE:** The graph document is a proposal, not evidence of a functioning server projection or cursor protocol.
  6792	- **INFERENCE:** SSE is operationally appropriate for a single-host, server-to-browser feed, but it is not what makes the feed correct. The version/cursor/relist contract does.
  6793	
  6794	## Search coverage
  6795	
  6796	Verified from primary documentation or source:
  6797	
  6798	- Temporal, Cadence, DBOS, Restate and Azure Durable workflow versioning/replay.
  6799	- Airflow DAG bundles, GitHub Actions commit pinning, and Kestra flow revisions.
  6800	- Axon event upcasting/snapshots, Marten inline projections, Microsoft event sourcing.

exec
/bin/bash -lc "git -C .claude/worktrees/kernel-tracer status --short --branch && nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py | sed -n '1,260p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
## feature/kernel-tracer
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	from dataclasses import dataclass, replace
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.events import (
     8	    ExecutionBlocked,
     9	    ExecutionCancelled,
    10	    ExecutionCreated,
    11	    ExecutionEvent,
    12	    ExecutionFailed,
    13	    ExecutionMarkedReady,
    14	    ExecutionResumed,
    15	    ExecutionStarted,
    16	    ExecutionSucceeded,
    17	    ExecutionUnblocked,
    18	    ExecutionWaited,
    19	)
    20	from ranex.governed_execution.domain.status import ExecutionStatus
    21	
    22	
    23	class InvalidExecutionTransition(ValueError):
    24	    """An event cannot evolve the supplied execution state."""
    25	
    26	
    27	LEGAL_STATUS_TRANSITIONS = frozenset(
    28	    {
    29	        (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
    30	        (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
    31	        (ExecutionStatus.READY, ExecutionStatus.RUNNING),
    32	        (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
    33	        (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
    34	        (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
    35	        (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
    36	        (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
    37	        (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
    38	        (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    39	        (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
    40	        (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
    41	        (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
    42	        (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
    43	        (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
    44	        (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
    45	        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
    46	        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
    47	        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    48	    }
    49	)
    50	
    51	
    52	@dataclass(frozen=True, slots=True)
    53	class Execution:
    54	    execution_id: Identity
    55	    work_item_id: Identity
    56	    created_by_principal_id: Identity
    57	    workflow_request_ref: str
    58	    status: ExecutionStatus
    59	    version: int
    60	    last_event_id: Identity
    61	    updated_at: str
    62	    blocked_from_status: ExecutionStatus | None = None
    63	
    64	
    65	def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    66	    return InvalidExecutionTransition(
    67	        f"{state.status.value} cannot apply {type(event).__name__}"
    68	    )
    69	
    70	
    71	def _advance(
    72	    state: Execution,
    73	    event: ExecutionEvent,
    74	    target_status: ExecutionStatus,
    75	    *,
    76	    blocked_from_status: ExecutionStatus | None = None,
    77	) -> Execution:
    78	    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
    79	        raise _invalid(state, event)
    80	    return replace(
    81	        state,
    82	        status=target_status,
    83	        version=state.version + 1,
    84	        last_event_id=event.event_id,
    85	        updated_at=event.occurred_at,
    86	        blocked_from_status=blocked_from_status,
    87	    )
    88	
    89	
    90	def _require_source(
    91	    state: Execution,
    92	    event: ExecutionEvent,
    93	    allowed: frozenset[ExecutionStatus],
    94	) -> None:
    95	    if state.status not in allowed:
    96	        raise _invalid(state, event)
    97	
    98	
    99	def reduce_execution(
   100	    current: Execution | None,
   101	    event: ExecutionEvent,
   102	) -> Execution:
   103	    """Purely compute the next immutable Execution from one event."""
   104	    if current is None:
   105	        if not isinstance(event, ExecutionCreated):
   106	            raise InvalidExecutionTransition(
   107	                f"no execution can apply {type(event).__name__}"
   108	            )
   109	        if event.expected_version != 0:
   110	            raise InvalidExecutionTransition(
   111	                "ExecutionCreated expected version must be zero"
   112	            )
   113	        return Execution(
   114	            execution_id=event.execution_id,
   115	            work_item_id=event.work_item_id,
   116	            created_by_principal_id=event.created_by_principal_id,
   117	            workflow_request_ref=event.workflow_request_ref,
   118	            status=ExecutionStatus.PROPOSED,
   119	            version=1,
   120	            last_event_id=event.event_id,
   121	            updated_at=event.occurred_at,
   122	        )
   123	
   124	    if isinstance(event, ExecutionCreated):
   125	        raise _invalid(current, event)
   126	    if event.execution_id != current.execution_id:
   127	        raise InvalidExecutionTransition("event targets a different execution")
   128	    if event.expected_version != current.version:
   129	        raise InvalidExecutionTransition(
   130	            "event expected version does not match execution version"
   131	        )
   132	    if event.event_id == current.last_event_id:
   133	        raise InvalidExecutionTransition("last event cannot be applied twice")
   134	
   135	    if isinstance(event, ExecutionMarkedReady):
   136	        _require_source(
   137	            current,
   138	            event,
   139	            frozenset({ExecutionStatus.PROPOSED}),
   140	        )
   141	        return _advance(current, event, ExecutionStatus.READY)
   142	    if isinstance(event, ExecutionStarted):
   143	        _require_source(
   144	            current,
   145	            event,
   146	            frozenset({ExecutionStatus.READY}),
   147	        )
   148	        return _advance(current, event, ExecutionStatus.RUNNING)
   149	    if isinstance(event, ExecutionWaited):
   150	        _require_source(
   151	            current,
   152	            event,
   153	            frozenset({ExecutionStatus.RUNNING}),
   154	        )
   155	        return _advance(current, event, ExecutionStatus.WAITING)
   156	    if isinstance(event, ExecutionResumed):
   157	        _require_source(
   158	            current,
   159	            event,
   160	            frozenset({ExecutionStatus.WAITING}),
   161	        )
   162	        return _advance(current, event, ExecutionStatus.RUNNING)
   163	    if isinstance(event, ExecutionBlocked):
   164	        _require_source(
   165	            current,
   166	            event,
   167	            frozenset(
   168	                {
   169	                    ExecutionStatus.READY,
   170	                    ExecutionStatus.RUNNING,
   171	                    ExecutionStatus.WAITING,
   172	                }
   173	            ),
   174	        )
   175	        return _advance(
   176	            current,
   177	            event,
   178	            ExecutionStatus.BLOCKED,
   179	            blocked_from_status=current.status,
   180	        )
   181	    if isinstance(event, ExecutionUnblocked):
   182	        if (
   183	            current.status is not ExecutionStatus.BLOCKED
   184	            or current.blocked_from_status is not event.target_status
   185	        ):
   186	            raise _invalid(current, event)
   187	        return _advance(current, event, event.target_status)
   188	    if isinstance(event, ExecutionSucceeded):
   189	        _require_source(
   190	            current,
   191	            event,
   192	            frozenset({ExecutionStatus.RUNNING}),
   193	        )
   194	        return _advance(current, event, ExecutionStatus.SUCCEEDED)
   195	    if isinstance(event, ExecutionFailed):
   196	        _require_source(
   197	            current,
   198	            event,
   199	            frozenset(
   200	                {
   201	                    ExecutionStatus.RUNNING,
   202	                    ExecutionStatus.WAITING,
   203	                    ExecutionStatus.BLOCKED,
   204	                }
   205	            ),
   206	        )
   207	        return _advance(current, event, ExecutionStatus.FAILED)
   208	    if isinstance(event, ExecutionCancelled):
   209	        _require_source(
   210	            current,
   211	            event,
   212	            frozenset(
   213	                {
   214	                    ExecutionStatus.PROPOSED,
   215	                    ExecutionStatus.READY,
   216	                    ExecutionStatus.RUNNING,
   217	                    ExecutionStatus.WAITING,
   218	                    ExecutionStatus.BLOCKED,
   219	                }
   220	            ),
   221	        )
   222	        return _advance(current, event, ExecutionStatus.CANCELLED)
   223	    raise TypeError(f"unsupported execution event: {type(event).__name__}")
   224	
   225	
   226	def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
   227	    """Replay an ordered history through the same production reducer."""
   228	    state: Execution | None = None
   229	    seen_event_ids: set[Identity] = set()
   230	    for event in events:
   231	        if event.event_id in seen_event_ids:
   232	            raise InvalidExecutionTransition("event identity is duplicated in history")
   233	        seen_event_ids.add(event.event_id)
   234	        state = reduce_execution(state, event)
   235	    if state is None:
   236	        raise InvalidExecutionTransition("execution history must not be empty")
   237	    return state

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql | sed -n '1,100p'; nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '1,130p;210,350p;380,425p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	BEGIN IMMEDIATE;
     2	
     3	CREATE TABLE IF NOT EXISTS execution_state (
     4	    execution_id TEXT PRIMARY KEY,
     5	    canonical_state_json TEXT NOT NULL,
     6	    version INTEGER NOT NULL CHECK (version >= 1),
     7	    last_event_id TEXT NOT NULL UNIQUE,
     8	    updated_at TEXT NOT NULL
     9	);
    10	
    11	CREATE TABLE IF NOT EXISTS execution_journal (
    12	    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    13	    event_id TEXT NOT NULL UNIQUE,
    14	    execution_id TEXT NOT NULL,
    15	    event_type TEXT NOT NULL,
    16	    previous_version INTEGER NOT NULL CHECK (previous_version >= 0),
    17	    resulting_version INTEGER NOT NULL,
    18	    event_json TEXT NOT NULL,
    19	    previous_state_sha256 TEXT,
    20	    resulting_state_sha256 TEXT NOT NULL,
    21	    resulting_state_json TEXT NOT NULL,
    22	    recorded_at TEXT NOT NULL,
    23	    FOREIGN KEY (execution_id)
    24	        REFERENCES execution_state(execution_id),
    25	    UNIQUE (execution_id, resulting_version),
    26	    CHECK (resulting_version = previous_version + 1),
    27	    CHECK (
    28	        (previous_version = 0 AND previous_state_sha256 IS NULL)
    29	        OR
    30	        (previous_version > 0 AND length(previous_state_sha256) = 64)
    31	    ),
    32	    CHECK (length(resulting_state_sha256) = 64)
    33	);
    34	
    35	CREATE TABLE IF NOT EXISTS execution_outbox (
    36	    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    37	    event_id TEXT NOT NULL UNIQUE,
    38	    execution_id TEXT NOT NULL,
    39	    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 1),
    40	    payload_json TEXT NOT NULL,
    41	    created_at TEXT NOT NULL,
    42	    FOREIGN KEY (event_id)
    43	        REFERENCES execution_journal(event_id),
    44	    UNIQUE (execution_id, aggregate_version)
    45	);
    46	
    47	CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
    48	BEFORE UPDATE ON execution_journal
    49	BEGIN
    50	    SELECT RAISE(ABORT, 'execution_journal is append-only');
    51	END;
    52	
    53	CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
    54	BEFORE DELETE ON execution_journal
    55	BEGIN
    56	    SELECT RAISE(ABORT, 'execution_journal is append-only');
    57	END;
    58	
    59	CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
    60	BEFORE UPDATE ON execution_outbox
    61	BEGIN
    62	    SELECT RAISE(ABORT, 'execution_outbox is append-only');
    63	END;
    64	
    65	CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
    66	BEFORE DELETE ON execution_outbox
    67	BEGIN
    68	    SELECT RAISE(ABORT, 'execution_outbox is append-only');
    69	END;
    70	
    71	PRAGMA user_version = 1;
    72	
    73	COMMIT;
     1	from __future__ import annotations
     2	
     3	import json
     4	import sqlite3
     5	from collections.abc import Mapping
     6	from contextlib import closing
     7	from pathlib import Path
     8	
     9	from ranex.foundation.canonical import canonical_json, canonical_sha256
    10	from ranex.foundation.identity import Identity
    11	from ranex.governed_execution.application.ports.execution_repository import (
    12	    ExecutionRepository,
    13	)
    14	from ranex.governed_execution.domain.events import (
    15	    ExecutionBlocked,
    16	    ExecutionCancelled,
    17	    ExecutionCreated,
    18	    ExecutionEvent,
    19	    ExecutionFailed,
    20	    ExecutionMarkedReady,
    21	    ExecutionResumed,
    22	    ExecutionStarted,
    23	    ExecutionSucceeded,
    24	    ExecutionUnblocked,
    25	    ExecutionWaited,
    26	)
    27	from ranex.governed_execution.domain.execution import (
    28	    Execution,
    29	    reduce_execution,
    30	)
    31	from ranex.governed_execution.domain.status import ExecutionStatus
    32	
    33	_MIGRATION = Path(__file__).with_name("migrations") / "001_execution_kernel.sql"
    34	_STATE_FIELDS = frozenset(
    35	    {
    36	        "schema_version",
    37	        "execution_id",
    38	        "work_item_id",
    39	        "created_by_principal_id",
    40	        "workflow_request_ref",
    41	        "status",
    42	        "version",
    43	        "last_event_id",
    44	        "updated_at",
    45	        "blocked_from_status",
    46	    }
    47	)
    48	
    49	
    50	class ExecutionPersistenceIntegrityError(RuntimeError):
    51	    """Stored execution bytes disagree with their relational metadata."""
    52	
    53	
    54	class ConcurrentExecutionWriteError(RuntimeError):
    55	    """The expected canonical execution version changed before commit."""
    56	
    57	
    58	def _execution_to_document(execution: Execution) -> dict[str, object]:
    59	    return {
    60	        "schema_version": "execution-state/v1",
    61	        "execution_id": str(execution.execution_id),
    62	        "work_item_id": str(execution.work_item_id),
    63	        "created_by_principal_id": str(execution.created_by_principal_id),
    64	        "workflow_request_ref": execution.workflow_request_ref,
    65	        "status": execution.status.value,
    66	        "version": execution.version,
    67	        "last_event_id": str(execution.last_event_id),
    68	        "updated_at": execution.updated_at,
    69	        "blocked_from_status": (
    70	            execution.blocked_from_status.value
    71	            if execution.blocked_from_status is not None
    72	            else None
    73	        ),
    74	    }
    75	
    76	
    77	def _require_string(value: object, field: str) -> str:
    78	    if not isinstance(value, str) or not value:
    79	        raise ValueError(f"{field} must be a non-empty string")
    80	    return value
    81	
    82	
    83	def _execution_from_document(document: Mapping[str, object]) -> Execution:
    84	    if set(document) != _STATE_FIELDS:
    85	        raise ValueError("canonical execution state has unexpected fields")
    86	    if document["schema_version"] != "execution-state/v1":
    87	        raise ValueError("unsupported execution state schema version")
    88	    version = document["version"]
    89	    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
    90	        raise ValueError("execution state version must be a positive integer")
    91	    blocked_from_value = document["blocked_from_status"]
    92	    blocked_from = (
    93	        None
    94	        if blocked_from_value is None
    95	        else ExecutionStatus(_require_string(blocked_from_value, "blocked_from_status"))
    96	    )
    97	    return Execution(
    98	        execution_id=Identity.parse(
    99	            _require_string(document["execution_id"], "execution_id"),
   100	            expected_prefix="run",
   101	        ),
   102	        work_item_id=Identity.parse(
   103	            _require_string(document["work_item_id"], "work_item_id"),
   104	            expected_prefix="work",
   105	        ),
   106	        created_by_principal_id=Identity.parse(
   107	            _require_string(
   108	                document["created_by_principal_id"],
   109	                "created_by_principal_id",
   110	            ),
   111	            expected_prefix="principal",
   112	        ),
   113	        workflow_request_ref=_require_string(
   114	            document["workflow_request_ref"],
   115	            "workflow_request_ref",
   116	        ),
   117	        status=ExecutionStatus(_require_string(document["status"], "status")),
   118	        version=version,
   119	        last_event_id=Identity.parse(
   120	            _require_string(document["last_event_id"], "last_event_id"),
   121	            expected_prefix="transition",
   122	        ),
   123	        updated_at=_require_string(document["updated_at"], "updated_at"),
   124	        blocked_from_status=blocked_from,
   125	    )
   126	
   127	
   128	_EVENT_TYPES: Mapping[str, type[ExecutionEvent]] = {
   129	    "ExecutionCreated": ExecutionCreated,
   130	    "ExecutionMarkedReady": ExecutionMarkedReady,
   210	    }
   211	    if isinstance(event, ExecutionCreated):
   212	        document.update(
   213	            {
   214	                "work_item_id": str(event.work_item_id),
   215	                "created_by_principal_id": str(event.created_by_principal_id),
   216	                "workflow_request_ref": event.workflow_request_ref,
   217	            }
   218	        )
   219	    elif isinstance(event, ExecutionMarkedReady):
   220	        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
   221	    elif isinstance(event, ExecutionStarted):
   222	        document["authorization_ref"] = event.authorization_ref
   223	    elif isinstance(event, ExecutionWaited):
   224	        document["wait_reason_code"] = event.wait_reason_code
   225	    elif isinstance(event, ExecutionResumed):
   226	        document["signal_ref"] = event.signal_ref
   227	    elif isinstance(event, ExecutionBlocked):
   228	        document.update(
   229	            {
   230	                "block_reason_code": event.block_reason_code,
   231	                "blocking_refs": list(event.blocking_refs),
   232	            }
   233	        )
   234	    elif isinstance(event, ExecutionUnblocked):
   235	        document.update(
   236	            {
   237	                "target_status": event.target_status.value,
   238	                "refreshed_evidence_ref": event.refreshed_evidence_ref,
   239	            }
   240	        )
   241	    elif isinstance(event, ExecutionSucceeded):
   242	        document["outcome_ref"] = event.outcome_ref
   243	    elif isinstance(event, ExecutionFailed):
   244	        document.update(
   245	            {
   246	                "failure_reason_code": event.failure_reason_code,
   247	                "evidence_ref": event.evidence_ref,
   248	            }
   249	        )
   250	    elif isinstance(event, ExecutionCancelled):
   251	        document["decision_ref"] = event.decision_ref
   252	    else:
   253	        raise TypeError(f"unsupported execution event: {type(event).__name__}")
   254	    return document
   255	
   256	
   257	class SQLiteExecutionStore(ExecutionRepository):
   258	    """State, audit journal, and outbox committed in one SQLite transaction."""
   259	
   260	    def __init__(self, path: Path) -> None:
   261	        self._path = path
   262	
   263	    def _connect(self) -> sqlite3.Connection:
   264	        connection = sqlite3.connect(
   265	            self._path,
   266	            isolation_level=None,
   267	            timeout=5.0,
   268	        )
   269	        connection.row_factory = sqlite3.Row
   270	        connection.execute("PRAGMA foreign_keys = ON")
   271	        connection.execute("PRAGMA synchronous = FULL")
   272	        return connection
   273	
   274	    def initialize(self) -> None:
   275	        self._path.parent.mkdir(parents=True, exist_ok=True)
   276	        migration = _MIGRATION.read_text(encoding="utf-8")
   277	        connection = self._connect()
   278	        try:
   279	            connection.executescript(migration)
   280	        finally:
   281	            connection.close()
   282	        self._path.chmod(0o600)
   283	
   284	    def load(self, execution_id: Identity) -> Execution | None:
   285	        self._require_run_id(execution_id)
   286	        with closing(self._connect()) as connection:
   287	            row = connection.execute(
   288	                """
   289	                SELECT execution_id, canonical_state_json, version, last_event_id
   290	                FROM execution_state
   291	                WHERE execution_id = ?
   292	                """,
   293	                (str(execution_id),),
   294	            ).fetchone()
   295	            if row is None:
   296	                return None
   297	            state = self._decode_state_row(row)
   298	            self._require_journal_agreement(connection, row, state)
   299	        return state
   300	
   301	    @staticmethod
   302	    def _require_journal_agreement(
   303	        connection: sqlite3.Connection,
   304	        row: sqlite3.Row,
   305	        state: Execution,
   306	    ) -> None:
   307	        """Reject a snapshot that disagrees with the append-only journal.
   308	
   309	        The architecture declares a dual model: the current row is the
   310	        operational read source and the ordered journal is the replay and
   311	        audit oracle, snapshots never replace the journal, and a
   312	        current-row/journal mismatch is corruption that blocks advancement
   313	        (HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md section 8.3).
   314	
   315	        Row-internal checks in `_decode_state_row` cannot satisfy that
   316	        obligation: a forger who rewrites `canonical_state_json`, `version`
   317	        and `last_event_id` together passes every one of them. Agreement is
   318	        only demonstrable against the journal, which independently records
   319	        the resulting version, the canonical state digest and the event
   320	        identity for each transition.
   321	        """
   322	        head = connection.execute(
   323	            """
   324	            SELECT resulting_version, resulting_state_sha256, event_id
   325	            FROM execution_journal
   326	            WHERE execution_id = ?
   327	            ORDER BY resulting_version DESC
   328	            LIMIT 1
   329	            """,
   330	            (str(state.execution_id),),
   331	        ).fetchone()
   332	        if head is None:
   333	            raise ExecutionPersistenceIntegrityError(
   334	                "execution state has no journal history"
   335	            )
   336	        if int(head["resulting_version"]) != state.version:
   337	            raise ExecutionPersistenceIntegrityError(
   338	                "execution state version disagrees with journal head version"
   339	            )
   340	        if str(head["event_id"]) != str(state.last_event_id):
   341	            raise ExecutionPersistenceIntegrityError(
   342	                "execution state last event disagrees with journal head event"
   343	            )
   344	        snapshot_digest = canonical_sha256(
   345	            json.loads(str(row["canonical_state_json"]))
   346	        )
   347	        if str(head["resulting_state_sha256"]) != snapshot_digest:
   348	            raise ExecutionPersistenceIntegrityError(
   349	                "execution state digest disagrees with journal head digest"
   350	            )
   380	                ORDER BY resulting_version ASC
   381	                """,
   382	                (str(execution_id),),
   383	            ).fetchall()
   384	        if not rows:
   385	            raise ExecutionPersistenceIntegrityError(
   386	                "execution has no journal history to replay"
   387	            )
   388	        state: Execution | None = None
   389	        for expected_version, row in enumerate(rows, start=1):
   390	            if int(row["resulting_version"]) != expected_version:
   391	                raise ExecutionPersistenceIntegrityError(
   392	                    "journal history has a version gap"
   393	                )
   394	            event = _event_from_document(json.loads(str(row["event_json"])))
   395	            state = reduce_execution(state, event)
   396	            if canonical_sha256(_execution_to_document(state)) != str(
   397	                row["resulting_state_sha256"]
   398	            ):
   399	                raise ExecutionPersistenceIntegrityError(
   400	                    "replayed state digest disagrees with journal digest"
   401	                )
   402	        assert state is not None
   403	        return state
   404	
   405	    def append(self, event: ExecutionEvent) -> Execution:
   406	        connection = self._connect()
   407	        connection.execute("BEGIN IMMEDIATE")
   408	        try:
   409	            current_row = connection.execute(
   410	                """
   411	                SELECT execution_id, canonical_state_json, version, last_event_id
   412	                FROM execution_state
   413	                WHERE execution_id = ?
   414	                """,
   415	                (str(event.execution_id),),
   416	            ).fetchone()
   417	            current = (
   418	                None if current_row is None else self._decode_state_row(current_row)
   419	            )
   420	            next_state = reduce_execution(current, event)
   421	            next_document = _execution_to_document(next_state)
   422	            next_json = canonical_json(next_document)
   423	
   424	            if current is None:
   425	                connection.execute(

codex
The repository boundary is now clear: the accepted architecture already makes the ordered journal the replay/audit oracle and treats a row/journal mismatch as blocking corruption. The tracer’s aggregate still pins only `workflow_request_ref`; I’m now checking the event classes and persisted bytes so the proposed fields address the actual omissions rather than an abstract model.
exec
/bin/bash -lc "git -C .claude/worktrees/kernel-tracer status --short --branch; nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py | sed -n '1,145p'; nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py | sed -n '1,280p'; nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '125,215p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
## feature/kernel-tracer
     1	from __future__ import annotations
     2	
     3	from collections.abc import Iterable
     4	from dataclasses import dataclass, replace
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.events import (
     8	    ExecutionBlocked,
     9	    ExecutionCancelled,
    10	    ExecutionCreated,
    11	    ExecutionEvent,
    12	    ExecutionFailed,
    13	    ExecutionMarkedReady,
    14	    ExecutionResumed,
    15	    ExecutionStarted,
    16	    ExecutionSucceeded,
    17	    ExecutionUnblocked,
    18	    ExecutionWaited,
    19	)
    20	from ranex.governed_execution.domain.status import ExecutionStatus
    21	
    22	
    23	class InvalidExecutionTransition(ValueError):
    24	    """An event cannot evolve the supplied execution state."""
    25	
    26	
    27	LEGAL_STATUS_TRANSITIONS = frozenset(
    28	    {
    29	        (ExecutionStatus.PROPOSED, ExecutionStatus.READY),
    30	        (ExecutionStatus.PROPOSED, ExecutionStatus.CANCELLED),
    31	        (ExecutionStatus.READY, ExecutionStatus.RUNNING),
    32	        (ExecutionStatus.READY, ExecutionStatus.BLOCKED),
    33	        (ExecutionStatus.READY, ExecutionStatus.CANCELLED),
    34	        (ExecutionStatus.RUNNING, ExecutionStatus.WAITING),
    35	        (ExecutionStatus.RUNNING, ExecutionStatus.BLOCKED),
    36	        (ExecutionStatus.RUNNING, ExecutionStatus.SUCCEEDED),
    37	        (ExecutionStatus.RUNNING, ExecutionStatus.FAILED),
    38	        (ExecutionStatus.RUNNING, ExecutionStatus.CANCELLED),
    39	        (ExecutionStatus.WAITING, ExecutionStatus.RUNNING),
    40	        (ExecutionStatus.WAITING, ExecutionStatus.BLOCKED),
    41	        (ExecutionStatus.WAITING, ExecutionStatus.FAILED),
    42	        (ExecutionStatus.WAITING, ExecutionStatus.CANCELLED),
    43	        (ExecutionStatus.BLOCKED, ExecutionStatus.READY),
    44	        (ExecutionStatus.BLOCKED, ExecutionStatus.RUNNING),
    45	        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
    46	        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
    47	        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    48	    }
    49	)
    50	
    51	
    52	@dataclass(frozen=True, slots=True)
    53	class Execution:
    54	    execution_id: Identity
    55	    work_item_id: Identity
    56	    created_by_principal_id: Identity
    57	    workflow_request_ref: str
    58	    status: ExecutionStatus
    59	    version: int
    60	    last_event_id: Identity
    61	    updated_at: str
    62	    blocked_from_status: ExecutionStatus | None = None
    63	
    64	
    65	def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    66	    return InvalidExecutionTransition(
    67	        f"{state.status.value} cannot apply {type(event).__name__}"
    68	    )
    69	
    70	
    71	def _advance(
    72	    state: Execution,
    73	    event: ExecutionEvent,
    74	    target_status: ExecutionStatus,
    75	    *,
    76	    blocked_from_status: ExecutionStatus | None = None,
    77	) -> Execution:
    78	    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
    79	        raise _invalid(state, event)
    80	    return replace(
    81	        state,
    82	        status=target_status,
    83	        version=state.version + 1,
    84	        last_event_id=event.event_id,
    85	        updated_at=event.occurred_at,
    86	        blocked_from_status=blocked_from_status,
    87	    )
    88	
    89	
    90	def _require_source(
    91	    state: Execution,
    92	    event: ExecutionEvent,
    93	    allowed: frozenset[ExecutionStatus],
    94	) -> None:
    95	    if state.status not in allowed:
    96	        raise _invalid(state, event)
    97	
    98	
    99	def reduce_execution(
   100	    current: Execution | None,
   101	    event: ExecutionEvent,
   102	) -> Execution:
   103	    """Purely compute the next immutable Execution from one event."""
   104	    if current is None:
   105	        if not isinstance(event, ExecutionCreated):
   106	            raise InvalidExecutionTransition(
   107	                f"no execution can apply {type(event).__name__}"
   108	            )
   109	        if event.expected_version != 0:
   110	            raise InvalidExecutionTransition(
   111	                "ExecutionCreated expected version must be zero"
   112	            )
   113	        return Execution(
   114	            execution_id=event.execution_id,
   115	            work_item_id=event.work_item_id,
   116	            created_by_principal_id=event.created_by_principal_id,
   117	            workflow_request_ref=event.workflow_request_ref,
   118	            status=ExecutionStatus.PROPOSED,
   119	            version=1,
   120	            last_event_id=event.event_id,
   121	            updated_at=event.occurred_at,
   122	        )
   123	
   124	    if isinstance(event, ExecutionCreated):
   125	        raise _invalid(current, event)
   126	    if event.execution_id != current.execution_id:
   127	        raise InvalidExecutionTransition("event targets a different execution")
   128	    if event.expected_version != current.version:
   129	        raise InvalidExecutionTransition(
   130	            "event expected version does not match execution version"
   131	        )
   132	    if event.event_id == current.last_event_id:
   133	        raise InvalidExecutionTransition("last event cannot be applied twice")
   134	
   135	    if isinstance(event, ExecutionMarkedReady):
   136	        _require_source(
   137	            current,
   138	            event,
   139	            frozenset({ExecutionStatus.PROPOSED}),
   140	        )
   141	        return _advance(current, event, ExecutionStatus.READY)
   142	    if isinstance(event, ExecutionStarted):
   143	        _require_source(
   144	            current,
   145	            event,
     1	from __future__ import annotations
     2	
     3	from dataclasses import dataclass
     4	from datetime import UTC, datetime
     5	
     6	from ranex.foundation.identity import Identity
     7	from ranex.governed_execution.domain.status import ExecutionStatus
     8	
     9	
    10	def _require_text(value: str, *, field: str) -> None:
    11	    if not isinstance(value, str) or not value.strip():
    12	        raise ValueError(f"{field} must be a non-empty string")
    13	
    14	
    15	def _require_identity(value: Identity, *, prefix: str, field: str) -> None:
    16	    if not isinstance(value, Identity) or value.prefix != prefix:
    17	        raise ValueError(f"{field} must be a canonical {prefix!r} identity")
    18	
    19	
    20	def _require_utc_timestamp(value: str) -> None:
    21	    _require_text(value, field="occurred_at")
    22	    if not value.endswith("Z"):
    23	        raise ValueError("occurred_at must use canonical UTC Z notation")
    24	    try:
    25	        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    26	    except ValueError as exc:
    27	        raise ValueError("occurred_at must be a valid UTC timestamp") from exc
    28	    if parsed.tzinfo != UTC:
    29	        raise ValueError("occurred_at must be UTC")
    30	
    31	
    32	@dataclass(frozen=True, slots=True, kw_only=True)
    33	class ExecutionEventMetadata:
    34	    event_id: Identity
    35	    execution_id: Identity
    36	    expected_version: int
    37	    occurred_at: str
    38	
    39	    def __post_init__(self) -> None:
    40	        _require_identity(
    41	            self.event_id,
    42	            prefix="transition",
    43	            field="event_id",
    44	        )
    45	        _require_identity(
    46	            self.execution_id,
    47	            prefix="run",
    48	            field="execution_id",
    49	        )
    50	        if (
    51	            isinstance(self.expected_version, bool)
    52	            or not isinstance(self.expected_version, int)
    53	            or self.expected_version < 0
    54	        ):
    55	            raise ValueError("expected_version must be a non-negative integer")
    56	        _require_utc_timestamp(self.occurred_at)
    57	
    58	
    59	@dataclass(frozen=True, slots=True, kw_only=True)
    60	class ExecutionCreated(ExecutionEventMetadata):
    61	    work_item_id: Identity
    62	    created_by_principal_id: Identity
    63	    workflow_request_ref: str
    64	
    65	    def __post_init__(self) -> None:
    66	        super().__post_init__()
    67	        _require_identity(
    68	            self.work_item_id,
    69	            prefix="work",
    70	            field="work_item_id",
    71	        )
    72	        _require_identity(
    73	            self.created_by_principal_id,
    74	            prefix="principal",
    75	            field="created_by_principal_id",
    76	        )
    77	        _require_text(self.workflow_request_ref, field="workflow_request_ref")
    78	
    79	
    80	@dataclass(frozen=True, slots=True, kw_only=True)
    81	class ExecutionMarkedReady(ExecutionEventMetadata):
    82	    readiness_snapshot_ref: str
    83	
    84	    def __post_init__(self) -> None:
    85	        super().__post_init__()
    86	        _require_text(
    87	            self.readiness_snapshot_ref,
    88	            field="readiness_snapshot_ref",
    89	        )
    90	
    91	
    92	@dataclass(frozen=True, slots=True, kw_only=True)
    93	class ExecutionStarted(ExecutionEventMetadata):
    94	    authorization_ref: str
    95	
    96	    def __post_init__(self) -> None:
    97	        super().__post_init__()
    98	        _require_text(self.authorization_ref, field="authorization_ref")
    99	
   100	
   101	@dataclass(frozen=True, slots=True, kw_only=True)
   102	class ExecutionWaited(ExecutionEventMetadata):
   103	    wait_reason_code: str
   104	
   105	    def __post_init__(self) -> None:
   106	        super().__post_init__()
   107	        _require_text(self.wait_reason_code, field="wait_reason_code")
   108	
   109	
   110	@dataclass(frozen=True, slots=True, kw_only=True)
   111	class ExecutionResumed(ExecutionEventMetadata):
   112	    signal_ref: str
   113	
   114	    def __post_init__(self) -> None:
   115	        super().__post_init__()
   116	        _require_text(self.signal_ref, field="signal_ref")
   117	
   118	
   119	@dataclass(frozen=True, slots=True, kw_only=True)
   120	class ExecutionBlocked(ExecutionEventMetadata):
   121	    block_reason_code: str
   122	    blocking_refs: tuple[str, ...]
   123	
   124	    def __post_init__(self) -> None:
   125	        super().__post_init__()
   126	        _require_text(self.block_reason_code, field="block_reason_code")
   127	        if not self.blocking_refs:
   128	            raise ValueError("blocking_refs must not be empty")
   129	        if any(not reference.strip() for reference in self.blocking_refs):
   130	            raise ValueError("blocking_refs must contain non-empty references")
   131	        if self.blocking_refs != tuple(sorted(set(self.blocking_refs))):
   132	            raise ValueError("blocking_refs must be unique and canonically sorted")
   133	
   134	
   135	@dataclass(frozen=True, slots=True, kw_only=True)
   136	class ExecutionUnblocked(ExecutionEventMetadata):
   137	    target_status: ExecutionStatus
   138	    refreshed_evidence_ref: str
   139	
   140	    def __post_init__(self) -> None:
   141	        super().__post_init__()
   142	        if self.target_status not in {
   143	            ExecutionStatus.READY,
   144	            ExecutionStatus.RUNNING,
   145	            ExecutionStatus.WAITING,
   146	        }:
   147	            raise ValueError("unblock target must be READY, RUNNING, or WAITING")
   148	        _require_text(
   149	            self.refreshed_evidence_ref,
   150	            field="refreshed_evidence_ref",
   151	        )
   152	
   153	
   154	@dataclass(frozen=True, slots=True, kw_only=True)
   155	class ExecutionSucceeded(ExecutionEventMetadata):
   156	    outcome_ref: str
   157	
   158	    def __post_init__(self) -> None:
   159	        super().__post_init__()
   160	        _require_text(self.outcome_ref, field="outcome_ref")
   161	
   162	
   163	@dataclass(frozen=True, slots=True, kw_only=True)
   164	class ExecutionFailed(ExecutionEventMetadata):
   165	    failure_reason_code: str
   166	    evidence_ref: str
   167	
   168	    def __post_init__(self) -> None:
   169	        super().__post_init__()
   170	        _require_text(
   171	            self.failure_reason_code,
   172	            field="failure_reason_code",
   173	        )
   174	        _require_text(self.evidence_ref, field="evidence_ref")
   175	
   176	
   177	@dataclass(frozen=True, slots=True, kw_only=True)
   178	class ExecutionCancelled(ExecutionEventMetadata):
   179	    decision_ref: str
   180	
   181	    def __post_init__(self) -> None:
   182	        super().__post_init__()
   183	        _require_text(self.decision_ref, field="decision_ref")
   184	
   185	
   186	ExecutionEvent = (
   187	    ExecutionCreated
   188	    | ExecutionMarkedReady
   189	    | ExecutionStarted
   190	    | ExecutionWaited
   191	    | ExecutionResumed
   192	    | ExecutionBlocked
   193	    | ExecutionUnblocked
   194	    | ExecutionSucceeded
   195	    | ExecutionFailed
   196	    | ExecutionCancelled
   197	)
   125	    )
   126	
   127	
   128	_EVENT_TYPES: Mapping[str, type[ExecutionEvent]] = {
   129	    "ExecutionCreated": ExecutionCreated,
   130	    "ExecutionMarkedReady": ExecutionMarkedReady,
   131	    "ExecutionStarted": ExecutionStarted,
   132	    "ExecutionWaited": ExecutionWaited,
   133	    "ExecutionResumed": ExecutionResumed,
   134	    "ExecutionBlocked": ExecutionBlocked,
   135	    "ExecutionUnblocked": ExecutionUnblocked,
   136	    "ExecutionSucceeded": ExecutionSucceeded,
   137	    "ExecutionFailed": ExecutionFailed,
   138	    "ExecutionCancelled": ExecutionCancelled,
   139	}
   140	
   141	_EVENT_IDENTITY_FIELDS: Mapping[str, str] = {
   142	    "work_item_id": "work",
   143	    "created_by_principal_id": "principal",
   144	}
   145	
   146	
   147	def _event_from_document(document: Mapping[str, object]) -> ExecutionEvent:
   148	    """Rebuild an event from its persisted canonical document.
   149	
   150	    The inverse of `_event_to_document`. Without it a replay test cannot read
   151	    the journal at all, which is why the previous replay test could only fold
   152	    the same in-memory events through the same reducer and compare the result
   153	    with itself. Replay of persisted bytes is the only form that can detect
   154	    encoder loss, field drift, or a broken digest chain.
   155	    """
   156	    if document.get("schema_version") != "execution-event/v1":
   157	        raise ExecutionPersistenceIntegrityError(
   158	            "journal event has an unsupported schema version"
   159	        )
   160	    event_type = document.get("event_type")
   161	    if not isinstance(event_type, str) or event_type not in _EVENT_TYPES:
   162	        raise ExecutionPersistenceIntegrityError(
   163	            "journal event has an unknown event type"
   164	        )
   165	    cls = _EVENT_TYPES[event_type]
   166	    payload: dict[str, object] = {
   167	        "event_id": Identity.parse(
   168	            str(document["event_id"]), expected_prefix="transition"
   169	        ),
   170	        "execution_id": Identity.parse(
   171	            str(document["execution_id"]), expected_prefix="run"
   172	        ),
   173	        "expected_version": document["expected_version"],
   174	        "occurred_at": document["occurred_at"],
   175	    }
   176	    known = set(payload) | {"schema_version", "event_type"}
   177	    for name, value in document.items():
   178	        if name in known:
   179	            continue
   180	        if name in _EVENT_IDENTITY_FIELDS:
   181	            payload[name] = Identity.parse(
   182	                str(value), expected_prefix=_EVENT_IDENTITY_FIELDS[name]
   183	            )
   184	        elif name == "target_status":
   185	            payload[name] = ExecutionStatus(str(value))
   186	        elif name == "blocking_refs":
   187	            if not isinstance(value, list):
   188	                raise ExecutionPersistenceIntegrityError(
   189	                    "journal event blocking_refs is not a list"
   190	                )
   191	            payload[name] = tuple(str(item) for item in value)
   192	        else:
   193	            payload[name] = value
   194	    try:
   195	        return cls(**payload)  # type: ignore[arg-type]
   196	    except (TypeError, ValueError) as exc:
   197	        raise ExecutionPersistenceIntegrityError(
   198	            "journal event does not satisfy its event contract"
   199	        ) from exc
   200	
   201	
   202	def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
   203	    document: dict[str, object] = {
   204	        "schema_version": "execution-event/v1",
   205	        "event_type": type(event).__name__,
   206	        "event_id": str(event.event_id),
   207	        "execution_id": str(event.execution_id),
   208	        "expected_version": event.expected_version,
   209	        "occurred_at": event.occurred_at,
   210	    }
   211	    if isinstance(event, ExecutionCreated):
   212	        document.update(
   213	            {
   214	                "work_item_id": str(event.work_item_id),
   215	                "created_by_principal_id": str(event.created_by_principal_id),

web search: 
web search: site:docs.temporal.io workflow versioning patching replay nondeterminism workflow history official ...
web search: 
web search: Temporal docs patching workflow code versioning replay behavior change ID official 2026 ...
web search: 
web search: site:developers.eventstore.com "event versioning" ...
web search: 
web search: site:docs.kurrent.io clients append event EventData event id type data metadata official ...
web search: 
web search: site:argo-workflows.readthedocs.io workflow spec immutable stored archived workflow definition version official ...
web search: 
web search: site:argo-workflows.readthedocs.io/en/latest workflow archive stored spec workflow metadata immutable resubmit ...
exec
/bin/bash -lc 'rg -n "workflow_definition|WorkflowDefinition|workflow definition|definition_digest|interpreter_version|event_schema|node_id|node_key|pinned workflow" docs .claude/worktrees/kernel-tracer/src .claude/worktrees/kernel-tracer/tests | head -n 300' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1442:workflow definition + interpreter version
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1494:`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2771:| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3114:in the workflow definition.
docs/architecture/AI_ARTIFACT_CONTRACTS.md:164:workflow_definition_id: <stable-id>
docs/architecture/AI_ARTIFACT_CONTRACTS.md:165:workflow_definition_digest: sha256:<hex>
docs/architecture/AI_ARTIFACT_CONTRACTS.md:166:workflow_interpreter_version: <semver-or-content-id>
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/deepseek-v4-pro-review.md:75:2. **Define one workflow YAML** — A Ranex-native workflow definition (not spec-kit's format) that chains four steps:
docs/architecture/reviews/artifacts/2026-07-30/spec-kit-selective-adaptation/deepseek-v4-pro-review.md:179:2. If a workflow is defined in YAML, how is its digest computed? The workflow definition is itself an artifact that must be subject-bound.
docs/architecture/templates/AI_TASK_PACKET.yaml:20:  workflow_definition_id: ""
docs/architecture/templates/AI_TASK_PACKET.yaml:21:  workflow_definition_digest: ""
docs/architecture/templates/AI_TASK_PACKET.yaml:22:  workflow_interpreter_version: ""
docs/architecture/templates/CHECKER_RESULT.yaml:33:  workflow_definition_id: ""
docs/architecture/templates/CHECKER_RESULT.yaml:34:  workflow_definition_digest: ""
docs/architecture/templates/CHECKER_RESULT.yaml:35:  workflow_interpreter_version: ""
docs/architecture/templates/PERMIT.yaml:26:  workflow_definition_id: ""
docs/architecture/templates/PERMIT.yaml:27:  workflow_definition_digest: ""
docs/architecture/templates/PERMIT.yaml:28:  workflow_interpreter_version: ""
docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md:92:  immutable approved workflow definitions, human/evidence gates, retry,
docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md:94:  activate workflow definitions;
docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md:146:([pinned workflow reference](https://github.com/github/spec-kit/blob/f36634b5c1463d3592382e863cd5e7b8a94d9c9a/docs/reference/workflows.md#L465-L481)).
docs/architecture/reviews/2026-07-30-spec-kit-selective-adaptation-reconciliation.md:247:| Workflows | **MODIFY authoring UX; REJECT runtime mechanics** | A friendly authoring view may compile into existing immutable approved workflow definitions and governed activities/effects. | No competing workflow owner, raw shell step, plain untrusted interpolation, advisory “permission,” or model activation. |
docs/architecture/templates/RUN_RESULT.yaml:30:  workflow_definition_id: ""
docs/architecture/templates/RUN_RESULT.yaml:31:  workflow_definition_digest: ""
docs/architecture/templates/RUN_RESULT.yaml:32:  workflow_interpreter_version: ""
docs/architecture/SDLC_CONTROL_CATALOG.md:642:        fields: ["schema_version", "record_type", "method_id", "method_version", "method_ref", "work_item_id", "method_definition_ref", "method_definition_digest", "observed_at", "valid_until", "supersedes_method_row_digest", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:651:          method_definition_digest: "sha256"
docs/architecture/SDLC_CONTROL_CATALOG.md:658:        self_reference_rule: "method_ref equals urn:ranex:estimate-method:<method_id>:<method_version>:<method_definition_digest-without-prefix>:<digest-without-prefix>; digest excludes method_ref and digest, thereby non-circularly binding the method ID, exact version, definition digest, and row digest."
docs/architecture/SDLC_CONTROL_CATALOG.md:752:        fields: ["schema_version", "record_type", "scope_id", "scope_version", "work_item_id", "scope_ref", "requirement_ids", "acceptance_criterion_ids", "included_configuration_item_bindings", "excluded_configuration_item_bindings", "scope_definition_ref", "scope_definition_digest", "observed_at", "valid_until", "supersedes_scope_id", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:765:          scope_definition_digest: "sha256"
docs/architecture/SDLC_CONTROL_CATALOG.md:878:        fields: ["schema_version", "record_type", "acceptance_snapshot_id", "work_item_id", "acceptance_snapshot_ref", "acceptance_criterion_ids", "verification_method_ids", "acceptance_owner_principal_id", "acceptance_owner_assignment_ref", "acceptance_owner_assignment_digest", "acceptance_definition_ref", "acceptance_definition_digest", "observed_at", "valid_until", "supersedes_acceptance_snapshot_id", "digest"]
docs/architecture/SDLC_CONTROL_CATALOG.md:891:          acceptance_definition_digest: "sha256"
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/stack-hy3.md:519:497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:1953:   164	workflow_definition_id: <stable-id>
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:1954:   165	workflow_definition_digest: sha256:<hex>
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:1955:   166	workflow_interpreter_version: <semver-or-content-id>
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-A.md:3352:docs/architecture/SDLC_CONTROL_CATALOG.md:752:        fields: ["schema_version", "record_type", "scope_id", "scope_version", "work_item_id", "scope_ref", "requirement_ids", "acceptance_criterion_ids", "included_configuration_item_bindings", "excluded_configuration_item_bindings", "scope_definition_ref", "scope_definition_digest", "observed_at", "valid_until", "supersedes_scope_id", "digest"]
docs/research/hermes-core-architecture-research-2026-07-27.md:582:        workflow_definition_version,
docs/research/hermes-core-architecture-research-2026-07-27.md:634:- Pin the workflow definition, interpreter version, event schema, task packet,
docs/research/hermes-core-architecture-research-2026-07-27.md:874:   - workflow definition/version;
docs/research/hermes-core-architecture-research-2026-07-27.md:1232:│   │   ├── workflow_definition.py
docs/research/hermes-core-architecture-research-2026-07-27.md:1392:    workflow_definition
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rigor-hy3.md:48:7781:def transition_event_schema(
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:97:The following is an illustrative rendering, not a new workflow definition and
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:128:- `governed_execution` alone owns run transitions, pinned workflows,
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:130:- one run pins an approved workflow definition, interpreter version, and policy
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:135:- workflow definitions are immutable approved data; a model may draft one but
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:191:1. Keep the workflow definition/topology separate from run status.
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:210:    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:232:- the exact pinned workflow definition;
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:259:- `workflow_definition_ref` and content digest;
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:260:- `workflow_interpreter_version`;
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:262:- sorted, stable `workflow_node_id` and edge IDs;
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:304:  "workflow_definition_ref": "ArtifactRef",
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:305:  "workflow_definition_digest": "sha256:...",
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:306:  "workflow_interpreter_version": "SemVer",
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:391:GET /api/runs/{run_id}/nodes/{workflow_node_id}
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:519:- A changed workflow definition or interpreter cannot reuse the old topology
docs/architecture/rfcs/RFC-0002-selective-spec-kit-adaptation.md:296:- workflow authoring compiles to existing approved workflow definitions;
docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:1323:  execution_subject_required_fields: ["subject_schema", "project_id", "work_item_id", "run_id", "activity_id", "effect_id", "workspace_id", "repository_id", "repository_uri_digest", "base_commit", "candidate_commit", "artifact_digest", "packet_id", "packet_digest", "workflow_definition_id", "workflow_definition_digest", "workflow_interpreter_version", "policy_activation_id", "policy_activation_manifest_digest", "policy_decision_digest", "module_profile_id", "module_profile_digest", "capability_grant_digest", "route_lock_id", "schema_registry_version", "expected_run_aggregate_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "release_profile_id", "release_profile_version", "release_profile_digest"]
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:574:497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:594:2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:597:2771:| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1024:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1190:[0m$ [0mgrep -n "OUTCOME_UNKNOWN" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -30; echo ===; grep -n "WorkflowDefinition\|workflow definition" docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | head -40
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1209:1442:workflow definition + interpreter version
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1210:1494:`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1211:2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1212:3114:in the workflow definition.
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1254:in the workflow definition.
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1315:workflow definition + interpreter version
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:1367:`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3353:  "workflow_definition_ref": {
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3365:     "x-ranex-id-type": "WorkflowDefinition",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3374:   "x-ranex-ref-type": "WorkflowDefinition"
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3376:  "workflow_interpreter_version": {
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3551:{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-30T10:30:24Z | stars: 27509
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3555:{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-29T21:22:50Z | stars: 15916
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3557:{'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} | archived: False | pushed: 2026-07-30T09:13:48Z | stars: 57120
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3559:{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-30T10:26:46Z | stars: 46323
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3561:{'key': 'apache-2.0', 'name': 'Apache License 2.0', 'spdx_id': 'Apache-2.0', 'url': 'https://api.github.com/licenses/apache-2.0', 'node_id': 'MDc6TGljZW5zZTI='} | archived: False | pushed: 2026-07-30T10:25:58Z | stars: 16858
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3563:{'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} | archived: False | pushed: 2026-07-30T09:59:22Z | stars: 37856
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3565:{'key': 'mit', 'name': 'MIT License', 'spdx_id': 'MIT', 'url': 'https://api.github.com/licenses/mit', 'node_id': 'MDc6TGljZW5zZTEz'} | archived: False | pushed: 2026-03-22T16:17:24Z | stars: 5737
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3567:{'key': 'other', 'name': 'Other', 'spdx_id': 'NOASSERTION', 'url': None, 'node_id': 'MDc6TGljZW5zZTA='} | archived: False | pushed: 2026-07-25T21:46:47Z | stars: 2680
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:3589:dagucloud/dagu {'key': 'gpl-3.0', 'name': 'GNU General Public License v3.0', 'spdx_id': 'GPL-3.0', 'url': 'https://api.github.com/licenses/gpl-3.0', 'node_id': 'MDc6TGljZW5zZTk='} | archived: False | pushed: 2026-07-30T03:25:53Z
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:4682:497:| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:4750:2768:| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:4751:2771:| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:4754:import json;d=json.load(open('schemas/events/governed_execution/activity-requested-v1.schema.json'));print(json.dumps(d['properties'].get('workflow_node_id'),indent=1))"
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:5051:[0m$ [0mcd /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer && grep -rIl "workflow_definition\|WorkflowDefinition" src/ranex/governed_execution 2>/dev/null; echo "---STATUS ENUMS---"; grep -rIn "class RunStatus\|class ActivityStatus\|class GateOutcome\|class EffectStatus\|RunStatus\b" src/ranex/governed_execution 2>/dev/null | head -40
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:5054:[0m$ [0mcd /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer && ls src/ranex/governed_execution/domain 2>/dev/null; echo "---"; find src/ranex/governed_execution -iname "*workflow*" 2>/dev/null; echo "---PINNED/INTERPRETER---"; grep -rIn "interpreter_version\|pinned\|workflow_definition_digest" src/ranex/governed_execution 2>/dev/null | head
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:5067:[0m$ [0mcd /home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer && grep -rIn "workflow\|Workflow\|interpreter\|pinned\|WorkflowDefinition" src/ranex 2>/dev/null | head -30; echo "===EXECUTION.PY head==="; sed -n '1,80p' src/ranex/governed_execution/domain/execution.py 2>/dev/null
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:5167:The `feature/kernel-tracer` worktree models execution as one flat aggregate (`Execution`, `execution.py:46-66`) holding only `workflow_request_ref: str` and `ExecutionStatus` (`status.py:6`). There is no `WorkflowDefinition`, no Activity/Gate/Permit/Effect/reconciliation sub-records, no stable node IDs, no digest, no interpreter version. §7.1/§7.2 assume all of these as join inputs.
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:5210:| Canonical `WorkflowDefinition` w/ stable node IDs, kinds, choice conditions | NOT IMPLEMENTED | `execution.py:46-66`; no workflow_definition module |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/rungraph-hy3.md:5211:| `workflow_definition_digest` / `workflow_interpreter_version` pins | NOT IMPLEMENTED (opaque `workflow_request_ref: str`) | `execution.py:57`; `status.py` |
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:29:   same commands, and how they version workflow definitions so old runs stay
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:2223:130:- one run pins an approved workflow definition, interpreter version, and policy
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:2247:210:    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:2256:260:- `workflow_interpreter_version`;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:2264:306:  "workflow_interpreter_version": "SemVer",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:2303:519:- A changed workflow definition or interpreter cannot reuse the old topology
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3643:    97	The following is an illustrative rendering, not a new workflow definition and
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3674:   128	- `governed_execution` alone owns run transitions, pinned workflows,
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3676:   130	- one run pins an approved workflow definition, interpreter version, and policy
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3681:   135	- workflow definitions are immutable approved data; a model may draft one but
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3737:   191	1. Keep the workflow definition/topology separate from run status.
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3756:   210	    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3778:   232	- the exact pinned workflow definition;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3810:   259	- `workflow_definition_ref` and content digest;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3811:   260	- `workflow_interpreter_version`;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3813:   262	- sorted, stable `workflow_node_id` and edge IDs;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3855:   304	  "workflow_definition_ref": "ArtifactRef",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3856:   305	  "workflow_definition_digest": "sha256:...",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3857:   306	  "workflow_interpreter_version": "SemVer",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:3942:   391	GET /api/runs/{run_id}/nodes/{workflow_node_id}
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4070:   519	- A changed workflow definition or interpreter cannot reuse the old topology
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4775:   391	GET /api/runs/{run_id}/nodes/{workflow_node_id}
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4903:   519	- A changed workflow definition or interpreter cannot reuse the old topology
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4919:   130	- one run pins an approved workflow definition, interpreter version, and policy
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4924:   135	- workflow definitions are immutable approved data; a model may draft one but
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4980:   191	1. Keep the workflow definition/topology separate from run status.
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:4999:   210	    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5021:   232	- the exact pinned workflow definition;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5048:   259	- `workflow_definition_ref` and content digest;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5049:   260	- `workflow_interpreter_version`;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5051:   262	- sorted, stable `workflow_node_id` and edge IDs;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5093:   304	  "workflow_definition_ref": "ArtifactRef",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5094:   305	  "workflow_definition_digest": "sha256:...",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:5095:   306	  "workflow_interpreter_version": "SemVer",
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6204:   130	- one run pins an approved workflow definition, interpreter version, and policy
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6209:   135	- workflow definitions are immutable approved data; a model may draft one but
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6245:   210	    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6267:   232	- the exact pinned workflow definition;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6294:   259	- `workflow_definition_ref` and content digest;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6295:   260	- `workflow_interpreter_version`;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6297:   262	- sorted, stable `workflow_node_id` and edge IDs;
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6334:   391	GET /api/runs/{run_id}/nodes/{workflow_node_id}
docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6398:   519	- A changed workflow definition or interpreter cannot reuse the old topology

exec
/bin/bash -lc "nl -ba docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '1400,1520p;2758,2782p;3100,3120p'; nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '120,145p;185,200p;252,270p;294,330p;510,525p'; nl -ba docs/architecture/AI_ARTIFACT_CONTRACTS.md | sed -n '150,180p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
  1400	RequirementId    req_<uuidv7>
  1401	CapabilityId     cap_<uuidv7>
  1402	ServiceId        svc_<uuidv7>
  1403	ConfigurationId  ci_<uuidv7>
  1404	BaselineId       baseline_<uuidv7>
  1405	RunId            run_<uuidv7>
  1406	ActivityId       act_<uuidv7>
  1407	EffectId         eff_<uuidv7>
  1408	WorkspaceId      wsp_<uuidv7>
  1409	PacketId         pkt_<uuidv7>
  1410	EvidenceId       evd_<uuidv7>
  1411	ArtifactId       art_<content-digest or uuidv7>
  1412	GateId           gate_<uuidv7>
  1413	PermitId         permit_<uuidv7>
  1414	DecisionId       dec_<uuidv7>
  1415	PrincipalId      principal_<uuidv7>
  1416	ModuleId         stable dotted identifier
  1417	RouteLockId      route_<uuidv7>
  1418	MigrationId      mig_<uuidv7>
  1419	IncidentId       incident_<uuidv7>
  1420	ReleaseId        release_<uuidv7>
  1421	ThreadId         thread_<uuidv7>
  1422	SupplierId       supplier_<uuidv7>
  1423	ReservationId    reservation_<uuidv7>
  1424	```
  1425	
  1426	`ExecutionSubject`, `AuthorizationSubject`, `EvidenceSubject`, and
  1427	`ArtifactSubject` are separate immutable views. The full command-boundary
  1428	envelope is not ambient state and contains no service handles.
  1429	
  1430	The minimum exact-subject tuple is:
  1431	
  1432	```text
  1433	project_id
  1434	work_item_id
  1435	run_id
  1436	activity/effect identity when applicable
  1437	workspace_id
  1438	repository identity
  1439	base commit
  1440	candidate commit or artifact digest
  1441	task-packet digest
  1442	workflow definition + interpreter version
  1443	policy/rule activation manifest + decision digest
  1444	module profile + grant digest
  1445	schema registry version
  1446	expected run aggregate version
  1447	```
  1448	
  1449	## 16. Canonical state axes
  1450	
  1451	One overloaded “office stage” is prohibited.
  1452	
  1453	| Axis | Canonical values |
  1454	|---|---|
  1455	| `WorkItemStatus` | `FUNNEL`, `TRIAGE`, `DISCOVERY`, `DEFINITION`, `DESIGN`, `READY`, `IN_PROGRESS`, `VERIFICATION`, `RELEASE_READY`, `RELEASING`, `OPERATING`, `OUTCOME_REVIEW`, `CLOSED`, `BLOCKED`, `CANCELLED`, `ROLLED_BACK` |
  1456	| `WorkClass` | `PRODUCT`, `DEFECT`, `RELIABILITY`, `SECURITY_PRIVACY`, `ARCHITECTURE_PLATFORM`, `COMPLIANCE_PROVENANCE`, `UPSTREAM_SYNC`, `MAINTENANCE`, `RETIREMENT`, `INCIDENT_RESPONSE` |
  1457	| `RiskLane` | `STANDARD`, `ENHANCED`, `CRITICAL`, `EMERGENCY` |
  1458	| `RunStatus` | `PROPOSED`, `READY`, `RUNNING`, `WAITING`, `BLOCKED`, `SUCCEEDED`, `FAILED`, `CANCELLED` |
  1459	| `AssignmentStatus` | `PENDING`, `OFFERED`, `CLAIMED`, `RUNNING`, `HANDOFF_READY`, `COMPLETED`, `FAILED`, `EXPIRED`, `CANCELLED`; owned by `agent_collaboration` and never a work/run completion alias |
  1460	| `DispatchOfferStatus` | `OPEN`, `CLAIMED`, `EXPIRED`, `REVOKED`; owned by `agent_collaboration`; invitation currency only |
  1461	| `LeaseStatus` | `ACTIVE`, `RELEASED`, `EXPIRED`, `REVOKED`; owned by `agent_collaboration` with a monotonically increasing fencing epoch |
  1462	| `MailboxDeliveryStatus` | `QUEUED`, `DELIVERED`, `ACKNOWLEDGED`, `DEAD_LETTERED`, `EXPIRED`; coordination delivery only, never authority |
  1463	| `ReservationStatus` | `PENDING`, `ACTIVE`, `EXHAUSTED`, `RELEASED`, `EXPIRED`, `REVOKED`, `SETTLED`; owned by `resource_governance`; never work completion or authority beyond its ancestor tree |
  1464	| `IntakeStatus` | `PROPOSED`, `ACCEPTED`, `REJECTED`, `DUPLICATE`, `WITHDRAWN`; owned by `work_management`; it does not alias `WorkItemStatus` |
  1465	| `PacketStatus` | `DRAFT`, `SEALED`, `SUPERSEDED`, `INVALIDATED`; owned by each packet producer under the shared schema; only `SEALED` is dispatch/review eligible |
  1466	| `FleetExperimentStatus` | `DRAFT`, `REGISTERED`, `RUNNING`, `COMPLETED`, `STOPPED`, `INVALIDATED`; owned by `process_assurance`; completion cannot activate policy |
  1467	| `CapabilityAssessmentStatus` | `NOT_ASSESSED`, `IN_PROGRESS`, `COMPLETE`, `SUPERSEDED`; owned by `process_assurance` and shared by immutable control assessments and domain projections; neither acts as a gate |
  1468	| `READINESS-STATE-1.0` | `NOT_ASSESSED`, `IMPLEMENTATION_START_EVALUATING`, `IMPLEMENTATION_START_BLOCKED`, `IMPLEMENTATION_START_READY`, `PRODUCTION_EVALUATING`, `PRODUCTION_BLOCKED`, `PRODUCTION_READY`; owned by `process_assurance`; definition-only and governed by ADR-0012 |
  1469	| `RuleEnforcementClass` | `ADVISORY`, `REQUIRED`, `BLOCKING`, `EXPERIMENTAL`; `STATE-RULE-ENFORCEMENT-CLASS-1.0`, owned by `policy`; separate `DETERMINISTIC` or `HUMAN_DECISION_REQUIRED` resolution metadata prevents human authority from being overloaded as severity |
  1470	| `RuleStage` | Derived policy classifier `STATE-RULE-STAGE-1.0`, owned by `policy`: `GOVERNANCE`, `DISCOVERY`, `REQUIREMENTS`, `DESIGN`, `PLANNING`, `IMPLEMENTATION`, `VERIFICATION`, `RELEASE`, `OPERATIONS`, `OUTCOME_REVIEW`, `MAINTENANCE`, `RETIREMENT` |
  1471	| `IncidentStatus` | `DETECTED`, `ACKNOWLEDGED`, `MITIGATING`, `MITIGATED`, `RECOVERY_VERIFIED`, `REVIEWED`, `ACTIONS_TRACKED`, `CLOSED` |
  1472	| `ReleaseStatus` | `PLANNED`, `BUILT`, `VERIFIED`, `RELEASE_READY`, `RELEASING`, `OPERATING`, `ROLLED_BACK`, `WITHDRAWN` |
  1473	| `CapabilityStatus` | `PROPOSED`, `SUPPORTED`, `DEPRECATED`, `RETIRE_READY`, `RETIRING`, `RETIRED` |
  1474	| `ActivityStatus` | `REQUESTED`, `DISPATCHED`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
  1475	| `GateOutcome` | `PASS`, `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, `CHECKER_FAULT` |
  1476	| `ObservationState` | `OPINION_PRODUCED`, `NO_OPINION`, `OPINION_UNUSABLE`, `EVALUATION_INCOMPLETE` |
  1477	| `PermitStatus` | `ISSUED`, `CONSUMED`, `EXPIRED`, `REVOKED` |
  1478	| `HumanDecisionRecordStatus` | `PENDING`, `APPROVED`, `DENIED`, `EXPIRED`, `REVOKED` |
  1479	| `AuthorityGrantStatus` | `ISSUED`, `CONSUMED`, `EXPIRED`, `REVOKED` |
  1480	| `EffectStatus` | `INTENDED`, `DISPATCHED`, `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `DENIED`, `OUTCOME_UNKNOWN` |
  1481	| `ReconciliationStatus` | `NOT_REQUIRED`, `PENDING`, `RUNNING`, `RESOLVED`, `UNRESOLVED` with preserved discovered effect disposition |
  1482	| `ModuleStatus` | `PACKAGED`, `DISABLED`, `QUALIFIED`, `CANARY`, `ACTIVE`, `RESTRICTED`, `QUARANTINED`, `RETIRED` |
  1483	| `RouteStatus` | `UNCONFIGURED`, `AUTHENTICATED`, `SMOKE_TESTED`, `PROBATION`, `APPROVED`, `RESTRICTED`, `SUSPENDED`, `RETIRED` |
  1484	| `ExtensionStatus` | `DISCOVERED`, `QUARANTINED`, `REVIEWED`, `QUALIFIED`, `PINNED`, `ENABLED`, `SUSPENDED`, `RETIRED` |
  1485	| `CompatibilityStatus` | `SUPPORTED`, `DEPRECATED`, `READ_ONLY`, `REMOVED`; owned by `service_management` for each registered legacy surface |
  1486	| `InstructionStatus` | `DRAFT`, `ACTIVE`, `DEPRECATED`, `RETIRED` |
  1487	| `ArtifactStatus` | `INGESTED`, `QUARANTINED`, `AVAILABLE`, `EXPIRED`, `PURGED`; legal hold is an orthogonal append-only fact, never an availability state |
  1488	| `MigrationStatus` | `PLANNED`, `TESTED`, `APPLIED`, `VERIFIED`, `ROLLED_BACK`, `FAILED` |
  1489	| `SyncCandidateStatus` | `OBSERVED`, `FETCHED`, `PINNED`, `CLASSIFIED`, `DISPOSITIONED`, `PORTING`, `PORT_CANDIDATE`, `VERIFIED`, `RELEASED`, `BASELINE_RECORDED`, `REJECTED`, `DEFERRED`, `BLOCKED`, `ROLLED_BACK` |
  1490	| `SyncDisposition` | `REJECT`, `DEFER`, `PORT`; `STATE-SYNC-DISPOSITION-1.0`, owned by `upstream_sync`; a decision value recorded at `DISPOSITIONED`, never an overloaded status |
  1491	| `UpdateStatus` | `CHECKED`, `DOWNLOADED`, `VERIFIED`, `SNAPSHOTTED`, `STAGED`, `MIGRATED`, `ACTIVATED`, `HEALTH_VERIFIED`, `COMPLETED`, `ROLLED_BACK`, `RECOVERY_VERIFIED` |
  1492	| `CutoverStatus` | `BOOTSTRAP`, `LEGACY_BASELINE`, `TRANSITIONAL_DUAL_RUN`, `TARGET_SHADOW`, `TARGET_LIMITED`, `TARGET_DEFAULT`, `LEGACY_FROZEN`, `LEGACY_REMOVED`, `ABANDONED` |
  1493	
  1494	`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
  1495	not another run-status enum. A waiver is a `HumanDecision`, not a gate outcome.
  1496	
  1497	`RunStatus` has one legal transition graph:
  1498	
  1499	```text
  1500	PROPOSED -> READY | CANCELLED
  1501	READY -> RUNNING | BLOCKED | CANCELLED
  1502	RUNNING -> WAITING | BLOCKED | SUCCEEDED | FAILED | CANCELLED
  1503	WAITING -> RUNNING | BLOCKED | FAILED | CANCELLED
  1504	BLOCKED -> <recorded blocked_from_status> | FAILED | CANCELLED
  1505	```
  1506	
  1507	Entering `BLOCKED` records the prior nonterminal state, reason, owner, time,
  1508	blocking evidence/dependency, invalidated inputs, and review deadline. Resume
  1509	is permitted only to that recorded state after fresh policy/evidence confirms
  1510	the blocker is resolved; it is not a generic jump. `SUCCEEDED`, `FAILED`, and
  1511	`CANCELLED` are terminal for one run attempt. Retry creates a new `RunId`
  1512	linked to the prior attempt. A terminal run remains only input to the
  1513	independently owned work-item transition.
  1514	
  1515	### 16.1 Exact axis-kind and lifecycle-transition contract
  1516	
  1517	The value table above is not sufficient by itself. Every axis is classified
  1518	exactly once as either `LIFECYCLE`, meaning independently writable state with
  1519	one closed guarded transition graph, or `CLASSIFIER`, meaning a value selected
  1520	or derived for an immutable decision/snapshot and never mutated as a
  2758	version needs frozen old/new fixtures and a total deterministic upcaster that
  2759	preserves event ID, aggregate/source versions, causation, authority, terminal
  2760	meaning, classification, and evidence digests. Otherwise it is a breaking ADR
  2761	and a new event ID. Failed upcast or replay is `UNKNOWN` and blocks.
  2762	
  2763	### 17.2 Exact initial event payload catalog
  2764	
  2765	| Event ID / name | Owner / producer; consumers | Aggregate; trigger and preconditions | Required payload fields |
  2766	|---|---|---|---|
  2767	| `EVENT-RUNCREATED` / `RunCreated` | `governed_execution` / `run_service`; `work_management`, `process_assurance` | `Run`; accepted unique run request, work item not terminal | `run_id:Id<Run>`, `work_item_id:Id<WorkItem>`, `initial_status:Enum<RunStatus>=PROPOSED`, `created_by_principal_id:Id<Principal>`, `workflow_request_ref:Ref<WorkflowRequest>` |
  2768	| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
  2769	| `EVENT-PACKETBOUND` / `PacketBound` | `governed_execution` / `packet_binding_service`; `agent_collaboration`, `assurance` | `Run`; workflow pinned, packet sealed for same work/subject | `run_id:Id<Run>`, `task_packet_ref:Ref<TaskPacket>`, `test_practice_profile_ref:Ref<TestPracticeProfile>`, `engineering_practice_profile_ref:Ref<EngineeringPracticeProfile>` |
  2770	| `EVENT-RUNMARKEDREADY` / `RunMarkedReady` | `governed_execution` / `run_lifecycle_service`; `agent_collaboration`, `work_management` | `Run`; workflow/packet/profiles bound, reservation and policy current | `run_id:Id<Run>`, `from_status:Enum<RunStatus>`, `to_status:Enum<RunStatus>=READY`, `readiness_snapshot_ref:Ref<EvidenceSnapshot>` |
  2771	| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
  2772	| `EVENT-AUTHORIZATIONEVALUATED` / `AuthorizationEvaluated` | `governed_execution` / `authorization_service`; `policy`, `assurance` | `Activity`; requested activity has current identity/policy/subject | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `authorization_snapshot_ref:Ref<AuthorizationSnapshot>`, `decision:Enum<AuthorizationOutcome>`, `reason_codes:Set<String>` |
  2773	| `EVENT-ACTIVITYDISPATCHED` / `ActivityDispatched` | `governed_execution` / `dispatch_service`; `agent_collaboration`, `resource_governance` | `Activity`; authorization allowed, assignment/lease/reservation current | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `assignment_ref:Ref<AgentAssignment>`, `worker_attempt_id:Id<WorkerAttempt>`, `lease_ref:Ref<WorkerLease>`, `dispatch_attempt:UInt` |
  2774	| `EVENT-ACTIVITYRESOLVED` / `ActivityResolved` | `governed_execution` / `activity_resolution_service`; `assurance`, `work_management` | `Activity`; typed result normalized and every required effect has the attempt disposition/reconciliation required by the selected activity edge | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `run_result_ref:Ref<RunResult>`, `resolution:Enum<ActivityStatus>` restricted by `ActivityResolution`, `required_effect_ids:Set<EffectId>[0..N]` (empty exactly for a declared pure zero-effect activity), `resolved_at:Utc` |
  2775	| `EVENT-EVIDENCESNAPSHOTBOUND` / `EvidenceSnapshotBound` | `governed_execution` / `evidence_binding_service`; `assurance` | `Run`; eligible fresh snapshot resolves to exact run subject | `run_id:Id<Run>`, `gate_id:Id<Gate>`, `evidence_snapshot_ref:Ref<EvidenceSnapshot>`, `required_claim_ids:Set<ClaimId>`, `freshness_cutoff:Utc` |
  2776	| `EVENT-GATEEVALUATED` / `GateEvaluated` | `governed_execution` / `gate_binding_service`; `assurance`, `work_management` | `Run`; qualified gate evaluation matches bound snapshot/subject | `run_id:Id<Run>`, `gate_evaluation_ref:Ref<GateEvaluation>`, `gate_id:Id<Gate>`, `outcome:Enum<GateOutcome>`, `reason_codes:Set<String>[0..N]` (empty only for a qualified warning-free `PASS`; every other outcome has at least one reason) |
  2777	| `EVENT-HUMANDECISIONSNAPSHOTBOUND` / `HumanDecisionSnapshotBound` | `governed_execution` / `decision_binding_service`; `policy`, `assurance` | `Run`; policy requires human choice and authenticated decision is current/exact | `run_id:Id<Run>`, `decision_ref:Ref<HumanDecisionRecord>`, `decision_kind:Enum<HumanDecisionKind>`, `decision_status:Enum<HumanDecisionRecordStatus>=APPROVED`, `decision_snapshot_digest:Sha256` |
  2778	| `EVENT-PERMITISSUED` / `PermitIssued` | `governed_execution` / `permit_service`; `policy`, `operations` | `Run`; fresh gate pass and required decision produce eligible one-shot grant | `run_id:Id<Run>`, `permit_ref:Ref<Permit>`, `authority_grant_ref:Ref<ConsumableAuthorityGrant>`, `action_type:String`, `expires_at:Utc` |
  2779	| `EVENT-PERMITCONSUMED` / `PermitConsumed` | `governed_execution` / `permit_service`; `operations`, `process_assurance` | `Run`; atomic compare-and-swap consumes unused current permit once | `run_id:Id<Run>`, `permit_id:Id<Permit>`, `consumed_for_effect_id:Id<Effect>`, `consumption_version:UInt`, `consumed_at:Utc` |
  2780	| `EVENT-EFFECTINTENTRECORDED` / `EffectIntentRecorded` | `governed_execution` / `effect_service`; `operations`, `artifact_management` | `Effect`; permit consumption and durable intent occur in one UoW | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `effect_id:Id<Effect>`, `permit_id:Id<Permit>`, `effect_type:String`, `destination_fact_ref:Ref<DestinationFact>`, `argument_digest:Sha256` |
  2781	| `EVENT-EFFECTDISPATCHED` / `EffectDispatched` | `governed_execution` / `effect_dispatch_service`; `operations` | `Effect`; committed intent leased, deadline/retry policy allows attempt | `effect_id:Id<Effect>`, `dispatch_attempt:UInt`, `adapter_id:String`, `adapter_version:String`, `provider_request_id:String`, `dispatched_at:Utc` |
  2782	| `EVENT-EFFECTRESOLVED` / `EffectResolved` | `governed_execution` / `effect_resolution_service`; `operations`, `assurance` | `Effect`; typed provider result proves a known disposition for the completed attempt | `effect_id:Id<Effect>`, `outcome:Enum<EffectStatus>` restricted by `EffectKnownOutcome`, `provider_receipt_ref:Ref<ProviderReceipt>`, `result_artifact_ref:Ref<Artifact>`, `resolved_at:Utc` |
  3100	extension points under `governed_execution.domain.workflow`, but cannot gain
  3101	authority until their ordering, cancellation, retry, compensation, and replay
  3102	semantics are specified and tested.
  3103	
  3104	Workflow definitions are immutable release- or project-approved data. Models may
  3105	draft definitions, never activate them.
  3106	
  3107	## 19. Effects, idempotency, and reconciliation
  3108	
  3109	An `Activity` is one logical unit of workflow work. It may be pure, invoke a
  3110	worker, or request `0..N` external `Effect` records. Each effect has its own
  3111	identity, destination, authority, idempotency/retry policy, result, and
  3112	reconciliation history. An activity resolves only when its required effects
  3113	have acceptable terminal facts; optional effects and compensation are declared
  3114	in the workflow definition.
  3115	
  3116	Every `ActivityRequest` declares:
  3117	
  3118	- exact subject;
  3119	- activity/effect type;
  3120	- canonical argument digest;
   120	decision.
   121	
   122	## 4. Ranex constraints this proposal must preserve
   123	
   124	The accepted architecture already establishes the important boundaries:
   125	
   126	- `work_management` alone owns canonical `WorkItemStatus`;
   127	- boards and dashboards are projections, never completion authorities;
   128	- `governed_execution` alone owns run transitions, pinned workflows,
   129	  activities, gate bindings, permits, effects, and reconciliation;
   130	- one run pins an approved workflow definition, interpreter version, and policy
   131	  activation;
   132	- the same workflow/interpreter versions and ordered recorded inputs replay to
   133	  the same state and commands;
   134	- `OUTCOME_UNKNOWN` is a first-class result and must enter reconciliation;
   135	- workflow definitions are immutable approved data; a model may draft one but
   136	  cannot activate it; and
   137	- sequence, deterministic choice, activity, evidence gate, durable wait/timer,
   138	  classified retry, cancellation, compensation request, reconciliation wait,
   139	  and terminal results are the initial workflow semantics. Parallel fan-out,
   140	  maps, and dynamic graph mutation are extension points, not silently available
   141	  semantics.
   142	
   143	Therefore the visualization cannot:
   144	
   145	- implement or duplicate a transition table in TypeScript;
   185	not a new orchestration core.
   186	
   187	## 6. Synthesis of the proven approach
   188	
   189	The common architecture across the strongest examples is:
   190	
   191	1. Keep the workflow definition/topology separate from run status.
   192	2. Give every node a stable identifier.
   193	3. Compute layout only when topology or grouping changes.
   194	4. Stream or poll status and merge it by node ID.
   195	5. Make nodes selectable for details and logs.
   196	6. Keep the graph read-only during execution.
   197	7. Degrade intentionally for large graphs.
   198	
   199	Airflow is especially relevant. Its graph obtains structure and layout, then
   200	adds streamed task-instance summaries “without having to recalculate how the
   252	Pixel coordinates are presentation data. The authoritative deterministic claim
   253	is the workflow topology and execution reduction, not a particular screen
   254	position.
   255	
   256	Every run graph must bind:
   257	
   258	- `run_id`;
   259	- `workflow_definition_ref` and content digest;
   260	- `workflow_interpreter_version`;
   261	- `workflow_policy_ref`;
   262	- sorted, stable `workflow_node_id` and edge IDs;
   263	- a `topology_digest` over the canonical topology, excluding live status;
   264	- `run_aggregate_version`;
   265	- a monotonically ordered projection version or cursor; and
   266	- the layout algorithm ID/version used by the client build.
   267	
   268	The server alone computes `topology_digest` as SHA-256 over an RFC 8785
   269	canonical JSON topology contract. Its closed input includes the workflow
   270	definition digest, interpreter version, stable node IDs and semantic kinds, and
   294	This is a research sketch, not a registered schema:
   295	
   296	```json
   297	{
   298	  "schema_version": "execution-graph-projection/v1",
   299	  "project_id": "ProjectId",
   300	  "work_item_id": "WorkItemId",
   301	  "run_id": "RunId",
   302	  "run_status": "RUNNING",
   303	  "run_aggregate_version": 14,
   304	  "workflow_definition_ref": "ArtifactRef",
   305	  "workflow_definition_digest": "sha256:...",
   306	  "workflow_interpreter_version": "SemVer",
   307	  "workflow_policy_ref": "ArtifactRef",
   308	  "topology_digest": "sha256:...",
   309	  "projection_version": 37,
   310	  "last_event_sequence": 92,
   311	  "consistency": "CURRENT",
   312	  "nodes": [],
   313	  "edges": []
   314	}
   315	```
   316	
   317	A node should contain only presentation-safe fields and references:
   318	
   319	| Field group | Proposed content |
   320	|---|---|
   321	| Identity | workflow node ID, node kind, label, optional activity/gate/effect ID |
   322	| State | server-derived visual state, display-only canonical source axis/value, attempt, start/end/duration |
   323	| Explanation | reason codes, safe summary, blocked/waiting cause |
   324	| Proof links | evidence, gate evaluation, policy/rule activation, human decision, artifact/log, permit/effect/reconciliation refs |
   325	| Safety | classification, redaction state, detail availability |
   326	
   327	An edge should identify source, target, semantic kind, defined condition/outcome,
   328	and server-reported traversal disposition. “Not traversed,” “not applicable,”
   329	and “unknown” are different facts.
   330	
   510	
   511	## 14. Acceptance and falsification tests
   512	
   513	### 14.1 Determinism
   514	
   515	- The same pinned definition and interpreter produce identical stable node IDs,
   516	  edge IDs, canonical ordering, and topology digest.
   517	- Shuffled database/query order does not change canonical topology or layout
   518	  input.
   519	- A changed workflow definition or interpreter cannot reuse the old topology
   520	  binding silently.
   521	- Status-only updates do not change coordinates.
   522	- Duplicate and out-of-order deltas are ignored or cause a safe resync.
   523	- A cursor gap or digest mismatch causes a full snapshot refetch.
   524	- The snapshot state and resumable cursor are captured atomically; a simulated
   525	  write between them cannot disappear.
   150	subject_schema: exact-subject/v1
   151	project_id: prj_<uuidv7>
   152	work_item_id: work_<uuidv7>
   153	run_id: run_<uuidv7>
   154	activity_id: null
   155	effect_id: null
   156	workspace_id: wsp_<uuidv7>
   157	repository_id: repo_<uuidv7>
   158	repository_uri_digest: sha256:<hex>
   159	base_commit: <40-hex>
   160	candidate_commit: <40-hex-or-null>
   161	artifact_digest: null
   162	packet_id: pkt_<uuidv7>
   163	packet_digest: sha256:<hex>
   164	workflow_definition_id: <stable-id>
   165	workflow_definition_digest: sha256:<hex>
   166	workflow_interpreter_version: <semver-or-content-id>
   167	policy_activation_id: <stable-id>
   168	policy_activation_manifest_digest: sha256:<hex>
   169	policy_decision_digest: sha256:<hex>
   170	module_profile_id: <stable-id>
   171	module_profile_digest: sha256:<hex>
   172	capability_grant_digest: sha256:<hex>
   173	route_lock_id: route_<uuidv7-or-null>
   174	schema_registry_version: <immutable-version>
   175	expected_run_aggregate_version: <nonnegative-integer>
   176	```
   177	
   178	The schema uses conditional requirements. An architecture/process decision may
   179	bind a normative artifact revision/digest instead of a run/activity/effect; an
   180	effect permit requires all effect fields. A `TaskPacket` omits its own

exec
/bin/bash -lc "nl -ba docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '2680,2765p;3060,3110p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
  2680	| `source_aggregate_version`, `aggregate_version` | nonnegative integers; resulting version is greater than source version |
  2681	| `aggregate_event_sequence` | positive gap-free integer under `(owner_context, aggregate_type, aggregate_id)` |
  2682	| `subject_ref`, `subject_digest` | governed immutable subject ref and RFC 8785 SHA-256 |
  2683	| `correlation_id` | nonempty trace/workflow ID retained across the whole causal operation |
  2684	| `causation_id` | exact command/event/decision ID that directly caused this event |
  2685	| `idempotency_key` | nonempty stable logical-operation key; same key plus different subject/payload is a conflict |
  2686	| `occurred_at`, `recorded_at` | strict UTC instants with `occurred_at <= recorded_at` |
  2687	| `payload_schema_ref`, `payload_schema_digest` | exact per-row `ranex:event-payload:<EventName>:v1` schema and RFC 8785 SHA-256 |
  2688	| `payload` | closed object matching the row below; no undeclared or nullable-by-omission field |
  2689	| `data_classification`, `retention_policy_id` | maximum classification of subject/payload and exact applicable retention rule |
  2690	| `digest` | RFC 8785 SHA-256 of the complete envelope excluding `digest` |
  2691	
  2692	Catalog payload notation is exact: `Id<T>` is a registered opaque nonempty ID
  2693	of type `T`; `Ref<T>` is the closed object
  2694	`{id: Id<T>, digest: sha256:<64 lowercase hex>}`; `Set<T>` is a bytewise-sorted
  2695	unique nonempty array unless explicitly `[]` is allowed; `Utc` is a strict UTC
  2696	instant; `UInt` is a nonnegative integer; `Sha256` is
  2697	`sha256:<64 lowercase hex>`; `Boolean` is a JSON boolean; `ArtifactRef` is
  2698	`Ref<Artifact>`; and `Enum<X>` is one value from the named canonical registry.
  2699	Every listed payload field is required. A `?` permits exactly `null` in
  2700	addition to the named type; `=VALUE` fixes a constant; and
  2701	`Set<T>[0..N]` explicitly overrides the nonempty default. Strings are nonempty
  2702	and bounded by the generated schema. Each payload schema path is deterministically
  2703	`schemas/events/<owner_context>/<kebab-case-event-name>-v1.schema.json`, and its
  2704	schema `$id` is `https://schemas.ranex.dev/events/<owner_context>/<kebab-case-event-name>-v1.schema.json`.
  2705	
  2706	The event schemas resolve every enum through these exact versioned axes:
  2707	
  2708	| Event enum name | Canonical axis/version and owner | Exact values / binding |
  2709	|---|---|---|
  2710	| `AuthorizationOutcome` | `ENUM-AUTHORIZATION-OUTCOME-1.0`; `policy` | `ALLOWED`, `DENIED`, `HUMAN_DECISION_REQUIRED`, `UNKNOWN`, `CONFLICT` |
  2711	| `ActivityResolution` | reuse `states.json#ActivityStatus@1.0.0`; `governed_execution` | restricted to `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
  2712	| `HumanDecisionKind` | `ENUM-HUMAN-DECISION-KIND-1.0`; `policy` | `ARCHITECTURE_OR_PROCESS_ACCEPTANCE`, `RISK_ACCEPTANCE_OR_WAIVER`, `WORK_TRANSITION`, `RELEASE_OR_MIGRATION`, `DESTRUCTIVE_OR_EXTERNAL_EFFECT`, `REVOCATION` |
  2713	| `HumanDecisionOutcome` | reuse `states.json#HumanDecisionRecordStatus@1.0.0`; `policy` | restricted to `APPROVED`, `DENIED`, `EXPIRED`, `REVOKED`; a bound eligible snapshot requires `APPROVED` |
  2714	| `EffectKnownOutcome` | reuse `states.json#EffectStatus@1.0.0`; `governed_execution` | restricted to known attempt dispositions `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `DENIED`; `FAILED_RETRYABLE` is nonterminal for the effect lifecycle |
  2715	| `SourceDivergenceClass` | `ENUM-SOURCE-DIVERGENCE-CLASS-1.0`; `configuration_management` | `BASE_COMMIT_CHANGED`, `CANDIDATE_COMMIT_CHANGED`, `WORKTREE_CHANGED`, `ARTIFACT_DIGEST_CHANGED`, `POLICY_OR_PROFILE_CHANGED`, `SCHEMA_OR_REGISTRY_CHANGED`, `SUBJECT_MISSING` |
  2716	| `EvidenceRelation` | `ENUM-EVIDENCE-RELATION-1.0`; `work_management` | `SUPPORTS`, `INVALIDATES`, `SUPERSEDES`, `CONTEXTUALIZES` |
  2717	| `ProductOutcomeDecision` | `ENUM-PRODUCT-OUTCOME-DECISION-1.0`; `product_definition` | `KEEP`, `CHANGE`, `REMOVE` |
  2718	| `WorkRelation` | `ENUM-WORK-RELATION-1.0`; `work_management` | `CONTINUES`, `REMEDIATES`, `INVESTIGATES`, `REPLACES`, `ROLLS_BACK` |
  2719	
  2720	`ALLOWED` is the only authorization value that permits dispatch;
  2721	`HUMAN_DECISION_REQUIRED`, `UNKNOWN`, and `CONFLICT` block until their exact
  2722	resolution, and `DENIED` blocks terminally for that evaluation. Evidence
  2723	relations are directed from the work item to the referenced evidence:
  2724	`SUPPORTS` contributes eligible proof, `INVALIDATES` makes the prior evidence
  2725	ineligible, `SUPERSEDES` names a newer authoritative evidence subject, and
  2726	`CONTEXTUALIZES` is nonsealing. Work relations are directed from the current
  2727	item to the follow-up: continue scope, remediate a finding, investigate an
  2728	unknown, replace the selected solution, or implement rollback. Product outcome
  2729	values are the authenticated keep/change/remove choices; insufficient evidence
  2730	emits no decision-link event and remains `UNKNOWN`.
  2731	
  2732	Each new enum axis is a canonical parent architecture element owned by its
  2733	named context; every value is a subordinate element whose
  2734	`parent_element_refs` contains that axis. Reused axes retain their existing
  2735	parents. An unknown value/version fails schema validation and is quarantined,
  2736	never mapped to a default. Adding, removing, splitting, or changing a value
  2737	versions the axis and every affected payload schema, requires exhaustive
  2738	consumer/upcast fixtures, and cannot change historical meaning; a nonpreserving
  2739	change requires an ADR/new event version.
  2740	
  2741	The aggregate UoW stores state, event, and outbox row atomically. Delivery is
  2742	at least once through the local transactional outbox, ordered only by the
  2743	aggregate key and `aggregate_event_sequence`; there is no claimed global order.
  2744	Consumers use a durable inbox keyed by `event_instance_id`, verify the complete
  2745	digest/schema/producer/version/sequence, and make the same event idempotent.
  2746	A duplicate with different bytes, sequence gap, wrong owner, unknown schema,
  2747	or invalid classification is quarantined as `CONFLICT` and blocks that
  2748	projection; it is never skipped into success. Retry reuses the same event ID
  2749	and bytes. Aggregate replay is deterministic and never redispatches an external
  2750	effect; effect dispatch requires its separate permit/intent path.
  2751	
  2752	All payloads use `SUBJECT_DERIVED` classification: the envelope records the
  2753	maximum classification of referenced material, contains opaque references
  2754	instead of secrets/raw personal content, and applies
  2755	`RET-AUDIT-CONTROL-001` unless a stricter registered legal/privacy retention
  2756	rule is named. Erasure tombstones retain only the minimum nonidentifying
  2757	idempotency/audit fact. Version 1 payloads are immutable. A new compatible
  2758	version needs frozen old/new fixtures and a total deterministic upcaster that
  2759	preserves event ID, aggregate/source versions, causation, authority, terminal
  2760	meaning, classification, and evidence digests. Otherwise it is a breaking ADR
  2761	and a new event ID. Failed upcast or replay is `UNKNOWN` and blocks.
  2762	
  2763	### 17.2 Exact initial event payload catalog
  2764	
  2765	| Event ID / name | Owner / producer; consumers | Aggregate; trigger and preconditions | Required payload fields |
  3060	validation_invariants:
  3061	  - "all 40 §17 event names appear exactly once"
  3062	  - "every INITIAL_STATE_FACT binding names an allowed initial value"
  3063	  - "every EDGE_EVENT edge is present verbatim in the named lifecycle row"
  3064	  - "every state_edge_bindings item resolves the exact referenced TransitionEventV1 and catalog digest"
  3065	  - "payload fixed from/to/status/outcome fields equal the resolved edge; implicit endpoints are derived only from the referenced transition fact"
  3066	  - "an event cannot bind an edge owned by another context unless its catalog row explicitly declares the same causal owner transaction"
  3067	  - "integration_events owner equals axis owner; referencing_events never authorize emission or a transition"
  3068	  - "wrong axis, version, digest, guard, edge, transition fact, aggregate version, or cardinality rejects before outbox insertion"
  3069	```
  3070	<!-- EVENT_STATE_BINDING_CONTRACT_END -->
  3071	
  3072	The compiler projects these rows without semantic edits to `events.json`; each
  3073	row has `schema_status: DEFINED_CONTRACT`, its envelope/payload schema refs and
  3074	digests, owner/producer/consumer set, aggregate/trigger, delivery/privacy/
  3075	compatibility/replay contracts, canonical row digest, and source-file digest.
  3076	Runtime emission, delivery, consumer handling, upcast, and replay evidence all
  3077	remain `NOT_ASSESSED`. Product, service, configuration, supplier, resource,
  3078	interaction, process, incident, release, migration, and upstream-sync contexts
  3079	may add events only through the same catalog decision; generic
  3080	`StatusChanged`, `Updated`, untyped payloads, or name-only additions are
  3081	blocking.
  3082	
  3083	## 18. Workflow semantics
  3084	
  3085	The target interpreter supports:
  3086	
  3087	- sequence;
  3088	- deterministic choice;
  3089	- activity request/result;
  3090	- evidence gate;
  3091	- durable signal wait;
  3092	- durable timer;
  3093	- classified retry;
  3094	- cancellation;
  3095	- compensation request;
  3096	- reconciliation wait; and
  3097	- terminal success/failure.
  3098	
  3099	Parallel/fan-out, map, dynamic graph mutation, and richer authoring remain mapped
  3100	extension points under `governed_execution.domain.workflow`, but cannot gain
  3101	authority until their ordering, cancellation, retry, compensation, and replay
  3102	semantics are specified and tested.
  3103	
  3104	Workflow definitions are immutable release- or project-approved data. Models may
  3105	draft definitions, never activate them.
  3106	
  3107	## 19. Effects, idempotency, and reconciliation
  3108	
  3109	An `Activity` is one logical unit of workflow work. It may be pure, invoke a
  3110	worker, or request `0..N` external `Effect` records. Each effect has its own

exec
/bin/bash -lc "nl -ba docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '2640,2695p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
  2640	
  2641	`RuleStage` is derived from the owning lifecycle state solely to select
  2642	applicable policy. It is not independently writable.
  2643	
  2644	### 16.3 Gate namespaces
  2645	
  2646	| Namespace | Meaning | Authority |
  2647	|---|---|---|
  2648	| `SDLC-*` | Core-SDLC stage/cross-lifecycle controls, including `SDLC-FORK-000` preflight | Owning SDLC roles plus deterministic requirements |
  2649	| `AI-G0`–`AI-G10` | Exact-subject evidence gates for one agent-assisted execution | `assurance` creates `GateEvaluation`; `governed_execution` only binds a fresh pass |
  2650	| `MAP-*` | Architecture-map completeness assertions over one `ArchitectureSubject` | `assurance` records qualified deterministic evaluation; architecture owner accepts/rejects |
  2651	| `SDLC-ADOPT-*` | Adoption/calibration of the process itself, including `SDLC-ADOPT-FLEET-*` | Process owner/human governor |
  2652	| `GateOutcome` | Runtime exact-subject result | Qualified deterministic gate |
  2653	| Human decision point | Product, architecture, risk, release, destructive or exception authority | Authenticated named human |
  2654	
  2655	IDs never cross namespaces by alias, and no passing namespace implies another
  2656	one passed.
  2657	
  2658	## 17. Command, event, and effect vocabulary
  2659	
  2660	Commands request work; events state facts that already occurred. They are
  2661	different types and cannot share one generic payload. A name without an
  2662	envelope, payload, owner/producer, trigger, consumer, ordering, delivery,
  2663	privacy, compatibility, and replay contract is `DEFINED_NAME_ONLY` and blocks
  2664	`IMPLEMENTATION_START_READY`.
  2665	
  2666	### 17.1 Canonical event envelope and delivery contract
  2667	
  2668	All 40 initially registered events use `DomainEventEnvelopeV1`, projected to
  2669	`schemas/events/domain-event-envelope-v1.schema.json`. Every field below is
  2670	required unless marked nullable:
  2671	
  2672	| Field | Exact type/invariant |
  2673	|---|---|
  2674	| `schema_version` | constant `domain-event-envelope/v1` |
  2675	| `event_id`, `event_name`, `event_version` | exact catalog ID/name and integer `1` |
  2676	| `event_instance_id` | globally unique UUIDv7; immutable and never reused |
  2677	| `owner_context`, `producer_service_id` | exact catalog values; authenticated producer must be owned by that context |
  2678	| `producer_release_digest` | `sha256:<64 lowercase hex>` of the emitting release |
  2679	| `aggregate_type`, `aggregate_id` | exact catalog aggregate and its registered opaque nonempty ID |
  2680	| `source_aggregate_version`, `aggregate_version` | nonnegative integers; resulting version is greater than source version |
  2681	| `aggregate_event_sequence` | positive gap-free integer under `(owner_context, aggregate_type, aggregate_id)` |
  2682	| `subject_ref`, `subject_digest` | governed immutable subject ref and RFC 8785 SHA-256 |
  2683	| `correlation_id` | nonempty trace/workflow ID retained across the whole causal operation |
  2684	| `causation_id` | exact command/event/decision ID that directly caused this event |
  2685	| `idempotency_key` | nonempty stable logical-operation key; same key plus different subject/payload is a conflict |
  2686	| `occurred_at`, `recorded_at` | strict UTC instants with `occurred_at <= recorded_at` |
  2687	| `payload_schema_ref`, `payload_schema_digest` | exact per-row `ranex:event-payload:<EventName>:v1` schema and RFC 8785 SHA-256 |
  2688	| `payload` | closed object matching the row below; no undeclared or nullable-by-omission field |
  2689	| `data_classification`, `retention_policy_id` | maximum classification of subject/payload and exact applicable retention rule |
  2690	| `digest` | RFC 8785 SHA-256 of the complete envelope excluding `digest` |
  2691	
  2692	Catalog payload notation is exact: `Id<T>` is a registered opaque nonempty ID
  2693	of type `T`; `Ref<T>` is the closed object
  2694	`{id: Id<T>, digest: sha256:<64 lowercase hex>}`; `Set<T>` is a bytewise-sorted
  2695	unique nonempty array unless explicitly `[]` is allowed; `Utc` is a strict UTC

web search: 
web search: site:docs.temporal.io "Patching" "Workflow" determinism ...
web search: 
web search: https://docs.temporal.io/develop/python/versioning
web search: 
web search: 'Pinned Workflows'
web search: 
web search: 
web search: 
web search: https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/
web search: 
web search: 
web search: 
web search: 
web search: 
web search: 
web search: 
web search: https://ar5iv.labs.arxiv.org/html/2104.01146
web search: 
web search: Martin Kleppmann Designing Data-Intensive Applications schema evolution event sourcing chapter official author site ...
web search: 
web search: site:microservices.io/patterns/data/event-sourcing.html Chris Richardson Event sourcing pattern event store ...
web search: 
web search: "Microservices Patterns" "Evolving the event schema" ...
web search: 
web search: 
web search: 
web search: AWS Step Functions Amazon States Language specification StartAt States Version official ...
web search: 
web search: 
web search: 
web search: 'If a running Workflow's underlying WorkflowTemplate changes'
web search: 
web search: 
context compacted
codex
The repository already contains more of the answer than the decision wording suggests: §8.3 and the event contract effectively preselect an immutable journal and constrained read-time compatibility. I’m now checking the remaining prior-art alternatives and making sure the recommendation does not silently revise the accepted `WorkflowPinned` payload.
web search: 
web search: https://leanpub.com/read/esversioning/leanpub-auto-copy-and-replace
web search: 
web search: 
exec
/bin/bash -lc "sed -n '780,800p;2015,2035p;2121,2128p' docs/research/hermes-core-architecture-research-2026-07-27.md
sed -n '470,500p;2658,2761p;3070,3115p' docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md
sed -n '742,846p;1051,1062p' docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
### Bake directly into the Ranex product kernel

| Product-core responsibility | Layer | Exact ownership | Maturity |
|---|---|---|---|
| Canonical subject and execution identity | Pure domain/shared kernel | Project, work item, run, activity, packet, workspace, commits, principal, and correlation IDs. | **MATURE PATTERN** |
| Execution aggregate and pure reducer | Pure domain | Legal workflow state, transition invariants, terminality, cancellation, waits, retries, and ordered event application. | **MATURE PATTERN / R&D schema** |
| Workflow definition compatibility | Pure domain | Immutable definitions, interpreter version, event-schema version, upcaster compatibility, and replay checks. | **MATURE PATTERN / R&D schema** |
| Policy and authorization semantics | Pure domain | Typed decisions, default-deny invariants, subject/grant/risk inputs, and current-policy requirements. | **MATURE** |
| Policy enforcement point | Application control | Complete mediation and current-policy recheck before effects; invokes the decision adapter and converts faults into denial. | **MATURE** |
| Constitutional invariants | Pure domain | No self-approval, no undeclared transition, no cross-project grant, no effect without authority. | **Core-domain requirement** |
| Capability/effect broker | Application control | Typed activity request, declared effects, capability grant, idempotency identity, dispatch, and result validation. | **MATURE PATTERN / R&D contract** |
| Evidence and claim contract | Pure domain | Exact subject binding, provenance, freshness, content digest, evaluator identity, and raw evidence references. | **MATURE PATTERN / R&D schema** |
| Gate semantics | Pure domain | Canonical outcomes and rules for which results may advance a blocking transition. | **Core-domain requirement** |
| Human decision and waiver contract | Pure domain | Exact scope, reason, principal, expiry, policy revision, and non-equivalence to `PASS`. | **MATURE PATTERN / R&D schema** |
| Permit semantics | Pure domain | Exact-subject, single-use, expiring authority and compare-and-swap consumption rules. | **Core-domain requirement** |
| Transaction, journal, and outbox coordinator | Application control | Commit aggregate version, audit/domain record, consumed authority, and outbound intent in one unit of work. | **MATURE** |
| Module qualification and capability semantics | Pure domain | Descriptor identity, compatibility, activation lifecycle, grants, conflicts, qualification, and quarantine state. | **MATURE PATTERN / R&D contract** |
| Module construction/loading | Bootstrap/infrastructure | Explicit catalog, factories, dependency injection, migrations, and process boundaries. | **MATURE PATTERN** |
| Core ports | Public contracts | Journal/unit of work, clock, ID source, policy evaluator, evidence store, activity transport, secret reference, telemetry sink. | **MATURE** |

The product core owns contracts, decisions, and nonbypassable application
- changed module digest forces requalification;
- incompatible interface fails before construction.

### Reducer and replay tests

- property-test every state/event combination;
- reject undeclared transitions;
- replay normal, blocked, cancelled, retried, waived, and recovered histories;
- pin interpreter/event versions;
- test upcasters against frozen old histories;
- snapshots accelerate replay but never replace the journal;
- inject time/random/network calls and prove the reducer rejects or lacks them.
- treat failure of replay, timer, signal, cancellation, upgrade, or crash
  semantics as a P0 trigger to evaluate a mature durable runtime rather than
  expanding a home-grown engine without an ADR.

### Authority tests

- default-deny every unknown action/role/capability;
- policy adapter throws, times out, returns malformed data, or disappears;
- module attempts self-grant/self-activation;
| LangGraph definition module | **PROMISING for some agent flows** | Must use kernel activities/gates and never become authority. |

### Foggy / R&D

1. The canonical Ranex workflow/event schema and upcaster policy.
2. Whether the local runner passes enough crash/recovery tests or Temporal is
   justified.
3. Exact transaction ownership across execution, evidence, permit, and work
### 8.3 State versus journal

- The current row is the operational read source.
- The ordered journal is the replay and audit oracle.
- Snapshots may accelerate replay but never replace the journal.
- A current-row/journal mismatch is corruption and blocks advancement; code
  does not choose whichever source is convenient.
- Other context projections are rebuilt or reconciled from canonical events.

### 8.4 Reliable events outside governed execution

Every stateful context commits its aggregate update, local audit event, and
integration-event outbox row in its own unit of work. The governed-execution
effect outbox is not the event-publication mechanism for `policy`,
`work_management`, `module_governance`, `routing`, `identity_access`,
`release_management`, or any other owner.

Consumers are idempotent and record source context, aggregate ID/version,
event ID/schema, correlation/causation IDs, and processed outcome. Cross-context
delivery is at least once; duplicates and out-of-order messages are tested.

## 9. Complete bounded-context ownership map

### 9.1 Nonreplaceable authority contexts

| Context | Owns | Public API | Persistence authority |
|---|---|---|---|
| `governed_execution` | Run, pinned workflow, activities, gate bindings, consumable authority grants, permit issuance/consumption, effect intents/outcomes, reconciliation | Commands, queries, integration events, immutable views | Sole run/execution-transition authority |
| `policy` | Roles, authorization-eligibility rules, risk-lane derivation, policy packages, activation, authorization snapshots, waivers and authenticated human-decision records | Authorization request/decision, active-policy and human-decision snapshots | Policy definitions and append-only decision history; never issues or consumes execution grants/permits |
| `assurance` | Claims, evidence envelopes, qualified checker results, exact-subject evidence snapshots, and `GateEvaluation` | Evidence ingestion/query, checker result, snapshot and gate-evaluation APIs | Sole evidence/gate-evaluation record owner; does not own review observations, qualify components, bind a run gate, or commit run state |
| `module_governance` | Module catalog, descriptors, capability vocabulary, grants, compatibility, activation lifecycle | Module/grant/profile snapshots | Module and grant authority |
## 17. Command, event, and effect vocabulary

Commands request work; events state facts that already occurred. They are
different types and cannot share one generic payload. A name without an
envelope, payload, owner/producer, trigger, consumer, ordering, delivery,
privacy, compatibility, and replay contract is `DEFINED_NAME_ONLY` and blocks
`IMPLEMENTATION_START_READY`.

### 17.1 Canonical event envelope and delivery contract

All 40 initially registered events use `DomainEventEnvelopeV1`, projected to
`schemas/events/domain-event-envelope-v1.schema.json`. Every field below is
required unless marked nullable:

| Field | Exact type/invariant |
|---|---|
| `schema_version` | constant `domain-event-envelope/v1` |
| `event_id`, `event_name`, `event_version` | exact catalog ID/name and integer `1` |
| `event_instance_id` | globally unique UUIDv7; immutable and never reused |
| `owner_context`, `producer_service_id` | exact catalog values; authenticated producer must be owned by that context |
| `producer_release_digest` | `sha256:<64 lowercase hex>` of the emitting release |
| `aggregate_type`, `aggregate_id` | exact catalog aggregate and its registered opaque nonempty ID |
| `source_aggregate_version`, `aggregate_version` | nonnegative integers; resulting version is greater than source version |
| `aggregate_event_sequence` | positive gap-free integer under `(owner_context, aggregate_type, aggregate_id)` |
| `subject_ref`, `subject_digest` | governed immutable subject ref and RFC 8785 SHA-256 |
| `correlation_id` | nonempty trace/workflow ID retained across the whole causal operation |
| `causation_id` | exact command/event/decision ID that directly caused this event |
| `idempotency_key` | nonempty stable logical-operation key; same key plus different subject/payload is a conflict |
| `occurred_at`, `recorded_at` | strict UTC instants with `occurred_at <= recorded_at` |
| `payload_schema_ref`, `payload_schema_digest` | exact per-row `ranex:event-payload:<EventName>:v1` schema and RFC 8785 SHA-256 |
| `payload` | closed object matching the row below; no undeclared or nullable-by-omission field |
| `data_classification`, `retention_policy_id` | maximum classification of subject/payload and exact applicable retention rule |
| `digest` | RFC 8785 SHA-256 of the complete envelope excluding `digest` |

Catalog payload notation is exact: `Id<T>` is a registered opaque nonempty ID
of type `T`; `Ref<T>` is the closed object
`{id: Id<T>, digest: sha256:<64 lowercase hex>}`; `Set<T>` is a bytewise-sorted
unique nonempty array unless explicitly `[]` is allowed; `Utc` is a strict UTC
instant; `UInt` is a nonnegative integer; `Sha256` is
`sha256:<64 lowercase hex>`; `Boolean` is a JSON boolean; `ArtifactRef` is
`Ref<Artifact>`; and `Enum<X>` is one value from the named canonical registry.
Every listed payload field is required. A `?` permits exactly `null` in
addition to the named type; `=VALUE` fixes a constant; and
`Set<T>[0..N]` explicitly overrides the nonempty default. Strings are nonempty
and bounded by the generated schema. Each payload schema path is deterministically
`schemas/events/<owner_context>/<kebab-case-event-name>-v1.schema.json`, and its
schema `$id` is `https://schemas.ranex.dev/events/<owner_context>/<kebab-case-event-name>-v1.schema.json`.

The event schemas resolve every enum through these exact versioned axes:

| Event enum name | Canonical axis/version and owner | Exact values / binding |
|---|---|---|
| `AuthorizationOutcome` | `ENUM-AUTHORIZATION-OUTCOME-1.0`; `policy` | `ALLOWED`, `DENIED`, `HUMAN_DECISION_REQUIRED`, `UNKNOWN`, `CONFLICT` |
| `ActivityResolution` | reuse `states.json#ActivityStatus@1.0.0`; `governed_execution` | restricted to `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `TIMED_OUT`, `CANCELLED`, `DENIED`, `OUTCOME_UNKNOWN` |
| `HumanDecisionKind` | `ENUM-HUMAN-DECISION-KIND-1.0`; `policy` | `ARCHITECTURE_OR_PROCESS_ACCEPTANCE`, `RISK_ACCEPTANCE_OR_WAIVER`, `WORK_TRANSITION`, `RELEASE_OR_MIGRATION`, `DESTRUCTIVE_OR_EXTERNAL_EFFECT`, `REVOCATION` |
| `HumanDecisionOutcome` | reuse `states.json#HumanDecisionRecordStatus@1.0.0`; `policy` | restricted to `APPROVED`, `DENIED`, `EXPIRED`, `REVOKED`; a bound eligible snapshot requires `APPROVED` |
| `EffectKnownOutcome` | reuse `states.json#EffectStatus@1.0.0`; `governed_execution` | restricted to known attempt dispositions `SUCCEEDED`, `FAILED_RETRYABLE`, `FAILED_PERMANENT`, `DENIED`; `FAILED_RETRYABLE` is nonterminal for the effect lifecycle |
| `SourceDivergenceClass` | `ENUM-SOURCE-DIVERGENCE-CLASS-1.0`; `configuration_management` | `BASE_COMMIT_CHANGED`, `CANDIDATE_COMMIT_CHANGED`, `WORKTREE_CHANGED`, `ARTIFACT_DIGEST_CHANGED`, `POLICY_OR_PROFILE_CHANGED`, `SCHEMA_OR_REGISTRY_CHANGED`, `SUBJECT_MISSING` |
| `EvidenceRelation` | `ENUM-EVIDENCE-RELATION-1.0`; `work_management` | `SUPPORTS`, `INVALIDATES`, `SUPERSEDES`, `CONTEXTUALIZES` |
| `ProductOutcomeDecision` | `ENUM-PRODUCT-OUTCOME-DECISION-1.0`; `product_definition` | `KEEP`, `CHANGE`, `REMOVE` |
| `WorkRelation` | `ENUM-WORK-RELATION-1.0`; `work_management` | `CONTINUES`, `REMEDIATES`, `INVESTIGATES`, `REPLACES`, `ROLLS_BACK` |

`ALLOWED` is the only authorization value that permits dispatch;
`HUMAN_DECISION_REQUIRED`, `UNKNOWN`, and `CONFLICT` block until their exact
resolution, and `DENIED` blocks terminally for that evaluation. Evidence
relations are directed from the work item to the referenced evidence:
`SUPPORTS` contributes eligible proof, `INVALIDATES` makes the prior evidence
ineligible, `SUPERSEDES` names a newer authoritative evidence subject, and
`CONTEXTUALIZES` is nonsealing. Work relations are directed from the current
item to the follow-up: continue scope, remediate a finding, investigate an
unknown, replace the selected solution, or implement rollback. Product outcome
values are the authenticated keep/change/remove choices; insufficient evidence
emits no decision-link event and remains `UNKNOWN`.

Each new enum axis is a canonical parent architecture element owned by its
named context; every value is a subordinate element whose
`parent_element_refs` contains that axis. Reused axes retain their existing
parents. An unknown value/version fails schema validation and is quarantined,
never mapped to a default. Adding, removing, splitting, or changing a value
versions the axis and every affected payload schema, requires exhaustive
consumer/upcast fixtures, and cannot change historical meaning; a nonpreserving
change requires an ADR/new event version.

The aggregate UoW stores state, event, and outbox row atomically. Delivery is
at least once through the local transactional outbox, ordered only by the
aggregate key and `aggregate_event_sequence`; there is no claimed global order.
Consumers use a durable inbox keyed by `event_instance_id`, verify the complete
digest/schema/producer/version/sequence, and make the same event idempotent.
A duplicate with different bytes, sequence gap, wrong owner, unknown schema,
or invalid classification is quarantined as `CONFLICT` and blocks that
projection; it is never skipped into success. Retry reuses the same event ID
and bytes. Aggregate replay is deterministic and never redispatches an external
effect; effect dispatch requires its separate permit/intent path.

All payloads use `SUBJECT_DERIVED` classification: the envelope records the
maximum classification of referenced material, contains opaque references
instead of secrets/raw personal content, and applies
`RET-AUDIT-CONTROL-001` unless a stricter registered legal/privacy retention
rule is named. Erasure tombstones retain only the minimum nonidentifying
idempotency/audit fact. Version 1 payloads are immutable. A new compatible
version needs frozen old/new fixtures and a total deterministic upcaster that
preserves event ID, aggregate/source versions, causation, authority, terminal
meaning, classification, and evidence digests. Otherwise it is a breaking ADR
and a new event ID. Failed upcast or replay is `UNKNOWN` and blocks.
<!-- EVENT_STATE_BINDING_CONTRACT_END -->

The compiler projects these rows without semantic edits to `events.json`; each
row has `schema_status: DEFINED_CONTRACT`, its envelope/payload schema refs and
digests, owner/producer/consumer set, aggregate/trigger, delivery/privacy/
compatibility/replay contracts, canonical row digest, and source-file digest.
Runtime emission, delivery, consumer handling, upcast, and replay evidence all
remain `NOT_ASSESSED`. Product, service, configuration, supplier, resource,
interaction, process, incident, release, migration, and upstream-sync contexts
may add events only through the same catalog decision; generic
`StatusChanged`, `Updated`, untyped payloads, or name-only additions are
blocking.

## 18. Workflow semantics

The target interpreter supports:

- sequence;
- deterministic choice;
- activity request/result;
- evidence gate;
- durable signal wait;
- durable timer;
- classified retry;
- cancellation;
- compensation request;
- reconciliation wait; and
- terminal success/failure.

Parallel/fan-out, map, dynamic graph mutation, and richer authoring remain mapped
extension points under `governed_execution.domain.workflow`, but cannot gain
authority until their ordering, cancellation, retry, compensation, and replay
semantics are specified and tested.

Workflow definitions are immutable release- or project-approved data. Models may
draft definitions, never activate them.

## 19. Effects, idempotency, and reconciliation

An `Activity` is one logical unit of workflow work. It may be pure, invoke a
worker, or request `0..N` external `Effect` records. Each effect has its own
identity, destination, authority, idempotency/retry policy, result, and
reconciliation history. An activity resolves only when its required effects
have acceptable terminal facts; optional effects and compensation are declared
in the workflow definition.

  - provision_id: "HERMES-PROMOTION-058"
    status: "PROMOTED"
    guard_id: "CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1901"
    source_end_line: 1901
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "The clean kernel contains a shared-identity facility that provides shared identity and a canonical-serialization facility that provides canonical serialization."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-059"
    status: "PROMOTED"
    guard_id: "EXECUTION_AGGREGATE_TRANSITIONS_THROUGH_PURE_REDUCER"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1902"
    source_end_line: 1902
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel contains an Execution aggregate, and Execution state transitions are computed by its pure reducer."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-060"
    status: "PROMOTED"
    guard_id: "CANONICAL_RELATIONAL_EXECUTION_STATE_HAS_EXPLICIT_VERSION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
    source_end_line: 1903
    check_class: "ARCHITECTURE_CONTRACT"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel persists canonical execution state and its associated version in relational storage."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-061"
    status: "PROMOTED"
    guard_id: "TRANSITION_AUDIT_JOURNAL_AND_OUTBOX_SHARE_ONE_SQLITE_UNIT_OF_WORK"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
    source_end_line: 1904
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-062"
    status: "PROMOTED"
    guard_id: "EVENT_SOURCING_IS_EXECUTION_ONLY_AND_REPLAY_MIGRATION_QUALIFIED"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
    source_end_line: 1906
    check_class: "MIGRATION_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-063"
    status: "PROMOTED"
    guard_id: "FAIL_CLOSED_APPLICATION_CONTROL_PEP_USES_PURE_DECISIONS_AND_DETERMINISTIC_POLICY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1907"
    source_end_line: 1908
    check_class: "AUTHORITY_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean kernel contains an application-control policy-enforcement point that is fail-closed, uses pure domain decisions, and invokes a simple deterministic policy adapter."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-064"
    status: "PROMOTED"
    guard_id: "ARCHITECTURE_IMPORT_TESTS_PRECEDE_FEATURE_CODE"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1909"
    source_end_line: 1909
    check_class: "STATIC_FITNESS"
    blocking_stage: "IMPLEMENTATION_START"
    provision: "Architecture import tests are part of the clean-kernel contract and must be present and passing before feature code is admitted."
    required_result: "PASS"
    failure_outcome: "BLOCK"
  - provision_id: "HERMES-PROMOTION-065"
    status: "PROMOTED"
    guard_id: "CLEAN_KERNEL_EXIT_REQUIRES_REPLAY_CRASH_TESTS_WITHOUT_HERMES_IMPORT"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1911"
    source_end_line: 1911
    check_class: "RUNTIME_FITNESS"
    blocking_stage: "GATE_ADVANCE"
    provision: "The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import."
    required_result: "PASS"
    failure_outcome: "BLOCK"
owner_decisions:
  - provision_id: "HERMES-OWNER-DECISION-001"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_WORKFLOW_EVENT_SCHEMA_AND_UPCASTER_POLICY"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2125"
    source_end_line: 2125
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Canonical Ranex workflow and event schema and upcaster policy."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-002"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_LOCAL_RUNNER_OR_MATURE_DURABLE_RUNTIME"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2126"
    source_end_line: 2127
    blocking_stage: "PRODUCTION_READY"
    decision_subject: "Whether the local runner passes the required crash and recovery tests or a mature durable runtime is justified."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"
  - provision_id: "HERMES-OWNER-DECISION-020"
    status: "OWNER_DECISION_REQUIRED"
    guard_id: "OWNER_DECIDES_EXECUTION_EVENT_SOURCING_AFTER_QUALIFICATION"
    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
    source_end_line: 1906
    blocking_stage: "IMPLEMENTATION_START"
    decision_subject: "Whether to activate event sourcing for the Execution aggregate after its replay and migration tests justify that choice; the decision cannot authorize event sourcing for any other module."
    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
    owner_decision_ref: null
    default: null
    absence_outcome: "BLOCK"
    activation_without_decision: "DENIED"

exec
/bin/bash -lc "git -C .claude/worktrees/kernel-tracer status --short --branch
nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py | sed -n '45,130p;220,242p'
nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py | sed -n '25,82p;180,202p'
nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/infrastructure/execution_store.py | sed -n '50,82p;120,168p;195,216p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
## feature/kernel-tracer
    45	        (ExecutionStatus.BLOCKED, ExecutionStatus.WAITING),
    46	        (ExecutionStatus.BLOCKED, ExecutionStatus.FAILED),
    47	        (ExecutionStatus.BLOCKED, ExecutionStatus.CANCELLED),
    48	    }
    49	)
    50	
    51	
    52	@dataclass(frozen=True, slots=True)
    53	class Execution:
    54	    execution_id: Identity
    55	    work_item_id: Identity
    56	    created_by_principal_id: Identity
    57	    workflow_request_ref: str
    58	    status: ExecutionStatus
    59	    version: int
    60	    last_event_id: Identity
    61	    updated_at: str
    62	    blocked_from_status: ExecutionStatus | None = None
    63	
    64	
    65	def _invalid(state: Execution, event: ExecutionEvent) -> InvalidExecutionTransition:
    66	    return InvalidExecutionTransition(
    67	        f"{state.status.value} cannot apply {type(event).__name__}"
    68	    )
    69	
    70	
    71	def _advance(
    72	    state: Execution,
    73	    event: ExecutionEvent,
    74	    target_status: ExecutionStatus,
    75	    *,
    76	    blocked_from_status: ExecutionStatus | None = None,
    77	) -> Execution:
    78	    if (state.status, target_status) not in LEGAL_STATUS_TRANSITIONS:
    79	        raise _invalid(state, event)
    80	    return replace(
    81	        state,
    82	        status=target_status,
    83	        version=state.version + 1,
    84	        last_event_id=event.event_id,
    85	        updated_at=event.occurred_at,
    86	        blocked_from_status=blocked_from_status,
    87	    )
    88	
    89	
    90	def _require_source(
    91	    state: Execution,
    92	    event: ExecutionEvent,
    93	    allowed: frozenset[ExecutionStatus],
    94	) -> None:
    95	    if state.status not in allowed:
    96	        raise _invalid(state, event)
    97	
    98	
    99	def reduce_execution(
   100	    current: Execution | None,
   101	    event: ExecutionEvent,
   102	) -> Execution:
   103	    """Purely compute the next immutable Execution from one event."""
   104	    if current is None:
   105	        if not isinstance(event, ExecutionCreated):
   106	            raise InvalidExecutionTransition(
   107	                f"no execution can apply {type(event).__name__}"
   108	            )
   109	        if event.expected_version != 0:
   110	            raise InvalidExecutionTransition(
   111	                "ExecutionCreated expected version must be zero"
   112	            )
   113	        return Execution(
   114	            execution_id=event.execution_id,
   115	            work_item_id=event.work_item_id,
   116	            created_by_principal_id=event.created_by_principal_id,
   117	            workflow_request_ref=event.workflow_request_ref,
   118	            status=ExecutionStatus.PROPOSED,
   119	            version=1,
   120	            last_event_id=event.event_id,
   121	            updated_at=event.occurred_at,
   122	        )
   123	
   124	    if isinstance(event, ExecutionCreated):
   125	        raise _invalid(current, event)
   126	    if event.execution_id != current.execution_id:
   127	        raise InvalidExecutionTransition("event targets a different execution")
   128	    if event.expected_version != current.version:
   129	        raise InvalidExecutionTransition(
   130	            "event expected version does not match execution version"
   220	            ),
   221	        )
   222	        return _advance(current, event, ExecutionStatus.CANCELLED)
   223	    raise TypeError(f"unsupported execution event: {type(event).__name__}")
   224	
   225	
   226	def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
   227	    """Replay an ordered history through the same production reducer."""
   228	    state: Execution | None = None
   229	    seen_event_ids: set[Identity] = set()
   230	    for event in events:
   231	        if event.event_id in seen_event_ids:
   232	            raise InvalidExecutionTransition("event identity is duplicated in history")
   233	        seen_event_ids.add(event.event_id)
   234	        state = reduce_execution(state, event)
   235	    if state is None:
   236	        raise InvalidExecutionTransition("execution history must not be empty")
   237	    return state
    25	        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    26	    except ValueError as exc:
    27	        raise ValueError("occurred_at must be a valid UTC timestamp") from exc
    28	    if parsed.tzinfo != UTC:
    29	        raise ValueError("occurred_at must be UTC")
    30	
    31	
    32	@dataclass(frozen=True, slots=True, kw_only=True)
    33	class ExecutionEventMetadata:
    34	    event_id: Identity
    35	    execution_id: Identity
    36	    expected_version: int
    37	    occurred_at: str
    38	
    39	    def __post_init__(self) -> None:
    40	        _require_identity(
    41	            self.event_id,
    42	            prefix="transition",
    43	            field="event_id",
    44	        )
    45	        _require_identity(
    46	            self.execution_id,
    47	            prefix="run",
    48	            field="execution_id",
    49	        )
    50	        if (
    51	            isinstance(self.expected_version, bool)
    52	            or not isinstance(self.expected_version, int)
    53	            or self.expected_version < 0
    54	        ):
    55	            raise ValueError("expected_version must be a non-negative integer")
    56	        _require_utc_timestamp(self.occurred_at)
    57	
    58	
    59	@dataclass(frozen=True, slots=True, kw_only=True)
    60	class ExecutionCreated(ExecutionEventMetadata):
    61	    work_item_id: Identity
    62	    created_by_principal_id: Identity
    63	    workflow_request_ref: str
    64	
    65	    def __post_init__(self) -> None:
    66	        super().__post_init__()
    67	        _require_identity(
    68	            self.work_item_id,
    69	            prefix="work",
    70	            field="work_item_id",
    71	        )
    72	        _require_identity(
    73	            self.created_by_principal_id,
    74	            prefix="principal",
    75	            field="created_by_principal_id",
    76	        )
    77	        _require_text(self.workflow_request_ref, field="workflow_request_ref")
    78	
    79	
    80	@dataclass(frozen=True, slots=True, kw_only=True)
    81	class ExecutionMarkedReady(ExecutionEventMetadata):
    82	    readiness_snapshot_ref: str
   180	
   181	    def __post_init__(self) -> None:
   182	        super().__post_init__()
   183	        _require_text(self.decision_ref, field="decision_ref")
   184	
   185	
   186	ExecutionEvent = (
   187	    ExecutionCreated
   188	    | ExecutionMarkedReady
   189	    | ExecutionStarted
   190	    | ExecutionWaited
   191	    | ExecutionResumed
   192	    | ExecutionBlocked
   193	    | ExecutionUnblocked
   194	    | ExecutionSucceeded
   195	    | ExecutionFailed
   196	    | ExecutionCancelled
   197	)
nl: .claude/worktrees/kernel-tracer/src/ranex/governed_execution/infrastructure/execution_store.py: No such file or directory

exec
/bin/bash -lc "rg --files .claude/worktrees/kernel-tracer/src | sort | rg 'store|migration|execution'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/application_control_pep.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/application_control_policy.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/execution_repository.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/__init__.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/status.py

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '50,82p;120,168p;195,216p'
nl -ba docs/architecture/AI_ARTIFACT_CONTRACTS.md | sed -n '150,178p'
nl -ba docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '1400,1450p;1488,1515p;2763,2775p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
    50	class ExecutionPersistenceIntegrityError(RuntimeError):
    51	    """Stored execution bytes disagree with their relational metadata."""
    52	
    53	
    54	class ConcurrentExecutionWriteError(RuntimeError):
    55	    """The expected canonical execution version changed before commit."""
    56	
    57	
    58	def _execution_to_document(execution: Execution) -> dict[str, object]:
    59	    return {
    60	        "schema_version": "execution-state/v1",
    61	        "execution_id": str(execution.execution_id),
    62	        "work_item_id": str(execution.work_item_id),
    63	        "created_by_principal_id": str(execution.created_by_principal_id),
    64	        "workflow_request_ref": execution.workflow_request_ref,
    65	        "status": execution.status.value,
    66	        "version": execution.version,
    67	        "last_event_id": str(execution.last_event_id),
    68	        "updated_at": execution.updated_at,
    69	        "blocked_from_status": (
    70	            execution.blocked_from_status.value
    71	            if execution.blocked_from_status is not None
    72	            else None
    73	        ),
    74	    }
    75	
    76	
    77	def _require_string(value: object, field: str) -> str:
    78	    if not isinstance(value, str) or not value:
    79	        raise ValueError(f"{field} must be a non-empty string")
    80	    return value
    81	
    82	
   120	            _require_string(document["last_event_id"], "last_event_id"),
   121	            expected_prefix="transition",
   122	        ),
   123	        updated_at=_require_string(document["updated_at"], "updated_at"),
   124	        blocked_from_status=blocked_from,
   125	    )
   126	
   127	
   128	_EVENT_TYPES: Mapping[str, type[ExecutionEvent]] = {
   129	    "ExecutionCreated": ExecutionCreated,
   130	    "ExecutionMarkedReady": ExecutionMarkedReady,
   131	    "ExecutionStarted": ExecutionStarted,
   132	    "ExecutionWaited": ExecutionWaited,
   133	    "ExecutionResumed": ExecutionResumed,
   134	    "ExecutionBlocked": ExecutionBlocked,
   135	    "ExecutionUnblocked": ExecutionUnblocked,
   136	    "ExecutionSucceeded": ExecutionSucceeded,
   137	    "ExecutionFailed": ExecutionFailed,
   138	    "ExecutionCancelled": ExecutionCancelled,
   139	}
   140	
   141	_EVENT_IDENTITY_FIELDS: Mapping[str, str] = {
   142	    "work_item_id": "work",
   143	    "created_by_principal_id": "principal",
   144	}
   145	
   146	
   147	def _event_from_document(document: Mapping[str, object]) -> ExecutionEvent:
   148	    """Rebuild an event from its persisted canonical document.
   149	
   150	    The inverse of `_event_to_document`. Without it a replay test cannot read
   151	    the journal at all, which is why the previous replay test could only fold
   152	    the same in-memory events through the same reducer and compare the result
   153	    with itself. Replay of persisted bytes is the only form that can detect
   154	    encoder loss, field drift, or a broken digest chain.
   155	    """
   156	    if document.get("schema_version") != "execution-event/v1":
   157	        raise ExecutionPersistenceIntegrityError(
   158	            "journal event has an unsupported schema version"
   159	        )
   160	    event_type = document.get("event_type")
   161	    if not isinstance(event_type, str) or event_type not in _EVENT_TYPES:
   162	        raise ExecutionPersistenceIntegrityError(
   163	            "journal event has an unknown event type"
   164	        )
   165	    cls = _EVENT_TYPES[event_type]
   166	    payload: dict[str, object] = {
   167	        "event_id": Identity.parse(
   168	            str(document["event_id"]), expected_prefix="transition"
   195	        return cls(**payload)  # type: ignore[arg-type]
   196	    except (TypeError, ValueError) as exc:
   197	        raise ExecutionPersistenceIntegrityError(
   198	            "journal event does not satisfy its event contract"
   199	        ) from exc
   200	
   201	
   202	def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
   203	    document: dict[str, object] = {
   204	        "schema_version": "execution-event/v1",
   205	        "event_type": type(event).__name__,
   206	        "event_id": str(event.event_id),
   207	        "execution_id": str(event.execution_id),
   208	        "expected_version": event.expected_version,
   209	        "occurred_at": event.occurred_at,
   210	    }
   211	    if isinstance(event, ExecutionCreated):
   212	        document.update(
   213	            {
   214	                "work_item_id": str(event.work_item_id),
   215	                "created_by_principal_id": str(event.created_by_principal_id),
   216	                "workflow_request_ref": event.workflow_request_ref,
   150	subject_schema: exact-subject/v1
   151	project_id: prj_<uuidv7>
   152	work_item_id: work_<uuidv7>
   153	run_id: run_<uuidv7>
   154	activity_id: null
   155	effect_id: null
   156	workspace_id: wsp_<uuidv7>
   157	repository_id: repo_<uuidv7>
   158	repository_uri_digest: sha256:<hex>
   159	base_commit: <40-hex>
   160	candidate_commit: <40-hex-or-null>
   161	artifact_digest: null
   162	packet_id: pkt_<uuidv7>
   163	packet_digest: sha256:<hex>
   164	workflow_definition_id: <stable-id>
   165	workflow_definition_digest: sha256:<hex>
   166	workflow_interpreter_version: <semver-or-content-id>
   167	policy_activation_id: <stable-id>
   168	policy_activation_manifest_digest: sha256:<hex>
   169	policy_decision_digest: sha256:<hex>
   170	module_profile_id: <stable-id>
   171	module_profile_digest: sha256:<hex>
   172	capability_grant_digest: sha256:<hex>
   173	route_lock_id: route_<uuidv7-or-null>
   174	schema_registry_version: <immutable-version>
   175	expected_run_aggregate_version: <nonnegative-integer>
   176	```
   177	
   178	The schema uses conditional requirements. An architecture/process decision may
  1400	RequirementId    req_<uuidv7>
  1401	CapabilityId     cap_<uuidv7>
  1402	ServiceId        svc_<uuidv7>
  1403	ConfigurationId  ci_<uuidv7>
  1404	BaselineId       baseline_<uuidv7>
  1405	RunId            run_<uuidv7>
  1406	ActivityId       act_<uuidv7>
  1407	EffectId         eff_<uuidv7>
  1408	WorkspaceId      wsp_<uuidv7>
  1409	PacketId         pkt_<uuidv7>
  1410	EvidenceId       evd_<uuidv7>
  1411	ArtifactId       art_<content-digest or uuidv7>
  1412	GateId           gate_<uuidv7>
  1413	PermitId         permit_<uuidv7>
  1414	DecisionId       dec_<uuidv7>
  1415	PrincipalId      principal_<uuidv7>
  1416	ModuleId         stable dotted identifier
  1417	RouteLockId      route_<uuidv7>
  1418	MigrationId      mig_<uuidv7>
  1419	IncidentId       incident_<uuidv7>
  1420	ReleaseId        release_<uuidv7>
  1421	ThreadId         thread_<uuidv7>
  1422	SupplierId       supplier_<uuidv7>
  1423	ReservationId    reservation_<uuidv7>
  1424	```
  1425	
  1426	`ExecutionSubject`, `AuthorizationSubject`, `EvidenceSubject`, and
  1427	`ArtifactSubject` are separate immutable views. The full command-boundary
  1428	envelope is not ambient state and contains no service handles.
  1429	
  1430	The minimum exact-subject tuple is:
  1431	
  1432	```text
  1433	project_id
  1434	work_item_id
  1435	run_id
  1436	activity/effect identity when applicable
  1437	workspace_id
  1438	repository identity
  1439	base commit
  1440	candidate commit or artifact digest
  1441	task-packet digest
  1442	workflow definition + interpreter version
  1443	policy/rule activation manifest + decision digest
  1444	module profile + grant digest
  1445	schema registry version
  1446	expected run aggregate version
  1447	```
  1448	
  1449	## 16. Canonical state axes
  1450	
  1488	| `MigrationStatus` | `PLANNED`, `TESTED`, `APPLIED`, `VERIFIED`, `ROLLED_BACK`, `FAILED` |
  1489	| `SyncCandidateStatus` | `OBSERVED`, `FETCHED`, `PINNED`, `CLASSIFIED`, `DISPOSITIONED`, `PORTING`, `PORT_CANDIDATE`, `VERIFIED`, `RELEASED`, `BASELINE_RECORDED`, `REJECTED`, `DEFERRED`, `BLOCKED`, `ROLLED_BACK` |
  1490	| `SyncDisposition` | `REJECT`, `DEFER`, `PORT`; `STATE-SYNC-DISPOSITION-1.0`, owned by `upstream_sync`; a decision value recorded at `DISPOSITIONED`, never an overloaded status |
  1491	| `UpdateStatus` | `CHECKED`, `DOWNLOADED`, `VERIFIED`, `SNAPSHOTTED`, `STAGED`, `MIGRATED`, `ACTIVATED`, `HEALTH_VERIFIED`, `COMPLETED`, `ROLLED_BACK`, `RECOVERY_VERIFIED` |
  1492	| `CutoverStatus` | `BOOTSTRAP`, `LEGACY_BASELINE`, `TRANSITIONAL_DUAL_RUN`, `TARGET_SHADOW`, `TARGET_LIMITED`, `TARGET_DEFAULT`, `LEGACY_FROZEN`, `LEGACY_REMOVED`, `ABANDONED` |
  1493	
  1494	`WorkflowNodeId` is a versioned node from the pinned workflow definition; it is
  1495	not another run-status enum. A waiver is a `HumanDecision`, not a gate outcome.
  1496	
  1497	`RunStatus` has one legal transition graph:
  1498	
  1499	```text
  1500	PROPOSED -> READY | CANCELLED
  1501	READY -> RUNNING | BLOCKED | CANCELLED
  1502	RUNNING -> WAITING | BLOCKED | SUCCEEDED | FAILED | CANCELLED
  1503	WAITING -> RUNNING | BLOCKED | FAILED | CANCELLED
  1504	BLOCKED -> <recorded blocked_from_status> | FAILED | CANCELLED
  1505	```
  1506	
  1507	Entering `BLOCKED` records the prior nonterminal state, reason, owner, time,
  1508	blocking evidence/dependency, invalidated inputs, and review deadline. Resume
  1509	is permitted only to that recorded state after fresh policy/evidence confirms
  1510	the blocker is resolved; it is not a generic jump. `SUCCEEDED`, `FAILED`, and
  1511	`CANCELLED` are terminal for one run attempt. Retry creates a new `RunId`
  1512	linked to the prior attempt. A terminal run remains only input to the
  1513	independently owned work-item transition.
  1514	
  1515	### 16.1 Exact axis-kind and lifecycle-transition contract
  2763	### 17.2 Exact initial event payload catalog
  2764	
  2765	| Event ID / name | Owner / producer; consumers | Aggregate; trigger and preconditions | Required payload fields |
  2766	|---|---|---|---|
  2767	| `EVENT-RUNCREATED` / `RunCreated` | `governed_execution` / `run_service`; `work_management`, `process_assurance` | `Run`; accepted unique run request, work item not terminal | `run_id:Id<Run>`, `work_item_id:Id<WorkItem>`, `initial_status:Enum<RunStatus>=PROPOSED`, `created_by_principal_id:Id<Principal>`, `workflow_request_ref:Ref<WorkflowRequest>` |
  2768	| `EVENT-WORKFLOWPINNED` / `WorkflowPinned` | `governed_execution` / `workflow_service`; `assurance`, `process_assurance` | `Run`; run `PROPOSED`, definition approved and compatible | `run_id:Id<Run>`, `workflow_definition_ref:Ref<WorkflowDefinition>`, `workflow_interpreter_version:String`, `workflow_policy_ref:Ref<PolicyActivation>` |
  2769	| `EVENT-PACKETBOUND` / `PacketBound` | `governed_execution` / `packet_binding_service`; `agent_collaboration`, `assurance` | `Run`; workflow pinned, packet sealed for same work/subject | `run_id:Id<Run>`, `task_packet_ref:Ref<TaskPacket>`, `test_practice_profile_ref:Ref<TestPracticeProfile>`, `engineering_practice_profile_ref:Ref<EngineeringPracticeProfile>` |
  2770	| `EVENT-RUNMARKEDREADY` / `RunMarkedReady` | `governed_execution` / `run_lifecycle_service`; `agent_collaboration`, `work_management` | `Run`; workflow/packet/profiles bound, reservation and policy current | `run_id:Id<Run>`, `from_status:Enum<RunStatus>`, `to_status:Enum<RunStatus>=READY`, `readiness_snapshot_ref:Ref<EvidenceSnapshot>` |
  2771	| `EVENT-ACTIVITYREQUESTED` / `ActivityRequested` | `governed_execution` / `workflow_service`; `agent_collaboration`, `policy` | `Activity`; active run reaches one enabled immutable workflow node | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `activity_type:String`, `workflow_node_id:String`, `argument_digest:Sha256`, `deadline_at:Utc`, `budget_snapshot_ref:Ref<ResourceReservation>` |
  2772	| `EVENT-AUTHORIZATIONEVALUATED` / `AuthorizationEvaluated` | `governed_execution` / `authorization_service`; `policy`, `assurance` | `Activity`; requested activity has current identity/policy/subject | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `authorization_snapshot_ref:Ref<AuthorizationSnapshot>`, `decision:Enum<AuthorizationOutcome>`, `reason_codes:Set<String>` |
  2773	| `EVENT-ACTIVITYDISPATCHED` / `ActivityDispatched` | `governed_execution` / `dispatch_service`; `agent_collaboration`, `resource_governance` | `Activity`; authorization allowed, assignment/lease/reservation current | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `assignment_ref:Ref<AgentAssignment>`, `worker_attempt_id:Id<WorkerAttempt>`, `lease_ref:Ref<WorkerLease>`, `dispatch_attempt:UInt` |
  2774	| `EVENT-ACTIVITYRESOLVED` / `ActivityResolved` | `governed_execution` / `activity_resolution_service`; `assurance`, `work_management` | `Activity`; typed result normalized and every required effect has the attempt disposition/reconciliation required by the selected activity edge | `run_id:Id<Run>`, `activity_id:Id<Activity>`, `run_result_ref:Ref<RunResult>`, `resolution:Enum<ActivityStatus>` restricted by `ActivityResolution`, `required_effect_ids:Set<EffectId>[0..N]` (empty exactly for a declared pure zero-effect activity), `resolved_at:Utc` |
  2775	| `EVENT-EVIDENCESNAPSHOTBOUND` / `EvidenceSnapshotBound` | `governed_execution` / `evidence_binding_service`; `assurance` | `Run`; eligible fresh snapshot resolves to exact run subject | `run_id:Id<Run>`, `gate_id:Id<Gate>`, `evidence_snapshot_ref:Ref<EvidenceSnapshot>`, `required_claim_ids:Set<ClaimId>`, `freshness_cutoff:Utc` |

exec
/bin/bash -lc "nl -ba docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md | sed -n '6658,6682p'
nl -ba docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | sed -n '1142,1154p'
nl -ba docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md | sed -n '505,530p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
  6658	  ✓ Synthesize the required mapping table and direct conclusions with citations
  6659	codex
  6660	The sweep found no genuinely novel mechanism in the four assigned layers. Ranex’s principal gaps are narrower and more concrete:
  6661	
  6662	- Replay currently has no independent oracle.
  6663	- The SQLite transaction prevents torn writes but does not prove that journal and snapshot mean the same thing.
  6664	- The resilience test exercises a caught SQLite error, not a process or power-loss crash.
  6665	- The graph proposal is aligned with production precedent, but its correctness contract matters more than SSE or the renderer.
  6666	
  6667	No repository files were modified.
  6668	
  6669	## Mapping table
  6670	
  6671	| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
  6672	|---|---|---|---|---|
  6673	| [ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742), [execution.py:226](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226), [replay test:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:59) | The ADR requires canonical events and a pure reducer. `replay_execution()` loops over events using the production reducer. The test manually loops over that same reducer and compares the two results. | Temporal reconstructs workflow state from append-only history and checks emitted commands during replay; SDK replay fails on non-determinism ([architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md), [Python replayer](https://github.com/temporalio/sdk-python)). Cadence replays actual production histories and supports production-history shadowing ([replay and shadowing](https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing)). | ADOPT | Replace the self-oracle with durable history fixtures containing expected command/outbox records. Run the current workflow implementation against those histories and fail at the first command mismatch. Include a mutation test that intentionally changes command order or payload and proves the replay test fails. |
  6674	| [execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58), [graph research:250](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:250) | The persisted snapshot carries a `workflow_request_ref`, but not an immutable workflow-definition digest or interpreter version. The graph document proposes such pins; the tracer does not implement them. | Temporal’s `GetVersion` records a marker in history so old and new code paths remain replayable ([Go API](https://github.com/temporalio/sdk-go/blob/main/workflow/workflow.go)). Cadence uses the same marker model ([versioning](https://cadenceworkflow.io/docs/go-client/workflow-versioning)). Airflow DAG bundles record the exact bundle version, including Git commit, used by a run ([DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)). DBOS associates workflows with application versions and supports history patch markers ([versioning tutorial](https://docs.dbos.dev/golang/tutorials/upgrading-workflows)). GitHub reruns at the original commit SHA/ref ([rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)). | ADOPT | Persist immutable workflow-definition, policy, interpreter, and serialization-version identities when a run is created. Recovery must select a compatible worker/definition or fail explicitly; never silently execute an old history using an unmarked new definition. Keep compatibility paths until all affected runs have drained. |
  6675	| [execution_store.py:128](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128) | Events have a strict schema version, but no verified upcaster or migration path for old event bytes. | Axon stores event revisions and applies ordered upcasters without rewriting immutable stored events ([event versioning](https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/)). Microsoft’s event-sourcing guidance likewise calls for versioned events/upcasting and sequence tracking ([Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)). | ADOPT | Introduce an explicit revision-to-current upcaster chain and permanent fixtures for every released event revision. Replay tests must begin from original stored bytes, not newly constructed current-version event objects. |
  6676	| [migration:1](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1), [execution_store.py:223](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223) | `BEGIN IMMEDIATE` encloses snapshot, journal, and outbox writes. An exception rolls the transaction back. | The transactional-outbox pattern writes business data and an outgoing-message record in the same database transaction ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). DBOS supports placing application data and workflow durability records in the same SQL transaction, including SQLite-backed `sql.DB` use ([DBOS transactions](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)). | ADOPT | Retain the one-database transaction. Treat it as atomicity only, not as replay or semantic-agreement proof. Ensure every state transition is forced through this unit of work and exercise rollback at each write boundary. |
  6677	| [migration:3](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3), [execution_store.py:390](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390) | State stores `last_event_id`, version, and canonical JSON. Journal rows store resulting state/digests. Loading validates relational columns against JSON in the same state row, but does not validate the state against the journal head. No constraint makes the referenced event the actual head. | Temporal stores the latest history event ID in mutable state and regards mutable state as valid only when that event is reflected in history; persistence failure forces reload ([History Service consistency](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)). Event-sourced systems make the event stream authoritative and snapshots rebuildable ([Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)); Marten’s inline projections update with events in one ACID transaction ([projection lifecycle](https://martendb.io/tutorials/read-model-projections)). Axon discards incompatible/corrupt snapshots and replays the stream ([snapshotting](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)). | ADAPT | Define one recovery authority—normally the journal. On write and integrity scan, require the snapshot’s event ID/version/digest to equal the exact journal head and its recorded resulting-state digest. Periodically replay original journal bytes and compare the reconstructed state with the snapshot. If verification fails, quarantine or rebuild the snapshot rather than loading it as authoritative. |
  6678	| [migration:35](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35) | The outbox is append-only and transactionally tied to the journal, but the scoped tracer has no durable dispatch/acknowledgement lifecycle. | AWS specifies a separate relay, ordered records, possible redelivery, and idempotent consumers ([transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). NServiceBus persists business data and outgoing messages in phase one, then sends and records dispatch completion in phase two; duplicate detection is based on stable message identity ([NServiceBus outbox](https://docs.particular.net/nservicebus/outbox/?version=core_9)). | ADOPT | Add a durable phase-two dispatch record or receipt keyed by the existing stable event/message ID. Test the crash windows before send, after send but before receipt, and after receipt. Consumers must be idempotent because exactly-once external delivery is not supplied by the SQLite transaction. |
  6679	| [crash test:31](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31) | A trigger raises `ABORT` before an outbox insert. The same Python process catches the error, rolls back, and checks that old rows remain. | SQLite’s own crash harness has a parent spawn a writer child, kills it at varied points, reopens the database, requires the database to be wholly old or wholly new, runs `PRAGMA integrity_check`, and uses a special VFS to reorder or corrupt unsynced writes ([SQLite testing](https://sqlite.org/testing.html)). | ADOPT | Keep the trigger test as a rollback unit test, but do not call it a crash test. Add an external controller that kills a separate writer process at every state/journal/outbox/commit boundary, reopens from a fresh process, and asserts integrity plus an all-old-or-all-new semantic tuple. Add fault-injecting VFS tests if power-loss durability is claimed. |
  6680	| [execution_store.py:183](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183) | Enables foreign keys and `synchronous=FULL`, but does not set or verify `journal_mode`. | SQLite documents the filesystem assumptions behind atomic commit ([atomic commit](https://www.sqlite.org/atomiccommit.html)); `FULL` has different guarantees in rollback-journal and WAL modes, while rollback mode may require `EXTRA` for power-loss durability ([synchronous](https://sqlite.org/pragma.html#pragma_synchronous)). WAL is same-host only, allows one writer, and does not make multi-attached-database transactions atomic as a set ([WAL limitations](https://www.sqlite.org/wal.html)). | ADAPT | Declare and verify a supported SQLite durability profile at startup: journal mode, synchronous mode, filesystem locality, and integrity settings. Run crash certification against exactly that profile. Refuse unsupported network filesystems or document the reduced guarantee. |
  6681	| [graph research:206](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:206), [graph research:227](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:227) | Proposes a server-side run projection and says the browser must not reconstruct workflow semantics from raw events. | Argo stores a server-side node map containing each node’s phase/status and retains the resolved workflow specification ([Argo fields](https://argoproj.github.io/argo-workflows/fields/)). Airflow’s graph loads versioned structure and attaches streamed server-produced task-instance summaries by node ID without recalculating layout semantics ([Airflow graph source](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx)). | ADOPT | Implement the proposal’s server ownership literally: server-assigned stable node/edge IDs, topology/version identity, node phase, attempts, and terminal reason. The browser may lay out, filter, and decorate this state, but must not derive execution phase, eligibility, or topology from event order. |
  6682	| [graph research:383](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:383) | Proposes GET snapshot plus cursor-bearing SSE, with refetch after a gap. | Kubernetes List/Watch couples a snapshot with `resourceVersion`; watches begin strictly after that version, and `410 Gone` requires relisting ([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)). Airflow 3.2 streams server-computed grid summaries progressively while runs are pending ([release notes](https://airflow.apache.org/docs/apache-airflow/3.2.0/release_notes.html)). | ADAPT | Preserve snapshot-plus-monotonic-cursor, resumability, deduplication, and explicit gap/relist behavior. SSE is a suitable single-host transport, but correctness must be transport-independent so polling or WebSocket clients observe the same versioned projection. |
  1142	```
  1143	
  1144	## Noncompensating fitness functions
  1145	
  1146	| ID | Required result |
  1147	|---|---|
  1148	| `FF-HERMES-PROMOTION-001` | The generated registry exactly projects all 65 promoted provisions, 20 owner-decision gates, and 13 research-only dispositions; every cited line and excerpt digest resolves to the immutable research source. |
  1149	| `FF-HERMES-GUARD-001` | Every promoted or owner-decision guard is unique and matches `^[A-Z][A-Z0-9_]*$`; a missing, malformed, duplicated, or hyphenated guard fails validation. |
  1150	| `FF-HERMES-OWNER-DECISION-001` | Every genuine owner choice is `OWNER_DECISION_REQUIRED`, has no default or synthetic decision reference, and blocks activation or progression while the exact accepted owner decision is absent. |
  1151	| `FF-HERMES-LEGAL-001` | License, copyright, provenance, required-attribution, legal-notice, and Git-history preservation are non-waivable release obligations; separate de-commercialization, package, network, credential, data, and branding checks remain noncompensating owner requirements rather than being mislabeled as law. |
  1152	| `FF-HERMES-KERNEL-001` | The clean-kernel inventory contains all eight Phase 1 provisions, binds only research lines 1901–1911, retains the one-SQLite-unit-of-work and Execution-only event-sourcing boundaries, requires import-test precedence, and cannot advance its gate without replay, crash-boundary, and no-Hermes-import proof. |
  1153	
  1154	## What remains research
   505	| Context | Owns | Attachment points |
   506	|---|---|---|
   507	| `product_definition` | Actors, problems/needs, hypotheses, product capabilities, requirements, acceptance examples, outcome measures, validation decisions, `CapabilityStatus` | Discovery/user research, product decisions, work intake, outcome review |
   508	| `work_management` | Projects, canonical `WorkItemStatus`, work class, portfolio/queues/WIP, dependencies/risks/issues, technical-debt records, accountable work roles, external issue mapping, Kanban projections | Core-SDLC transition API, GitHub intake, product/requirement links, governed-run/evidence integration |
   509	| `service_management` | Service catalog, service/capability ownership, supported versions, SLIs/SLOs/error budgets, support/escalation, maintenance and retirement triggers | Operations evidence, release catalog, product capability lifecycle |
   510	| `configuration_management` | Configuration-item registry, content-addressed baselines, status accounting, bidirectional traceability graph, functional/physical configuration audits | Product requirements, source/build/test/docs, release manifests, assurance evidence |
   511	| `supplier_governance` | Supplier/dependency adoption and reuse decisions, shared responsibility, version/support/vulnerability monitoring, concentration/exit plans | Packages, toolchains, providers, APIs, extensions, hosted services, Hermes upstream |
   512	| `resource_governance` | Local capacity, hierarchical cost/token/tool/output/network budgets, parent/child reservations, quotas, transitive usage attribution and provider-limit facts | Policy, routing, scheduling, agent runs, operations; never commercial billing |
   513	| `interaction_history` | User conversation/thread/message identity, continuity, search lifecycle, classification, retention, export and deletion | Delivery channels, context compilation, legacy session import |
   514	| `process_assurance` | SDLC policy conformance, tailoring profiles, human-role competence, process audits/nonconformance/corrective action, process improvement evidence, fleet experiment and calibration records | Core SDLC, work records, metrics, training/qualification and measurement-harness evidence |
   515	| `workspace` | Repository identity, worktree plans, branch/head validation, landing and cleanup | Git adapter, sandbox mounts |
   516	| `instruction_registry` | Atomic versioned instructions, precedence, applicability, checker bindings | Policy and packet compilation |
   517	| `context_compilation` | Resolved source manifests, packet compilation, context budget, conflicts, provenance | Deterministic and recorded stochastic retrieval |
   518	| `analytical_review` | Review specifications, requests, attempts, observations, verdicts, parsing and independence evaluations | Native and tool-bearing review transports; publishes immutable review references to assurance |
   519	| `routing` | Provider/model/transport/runtime/auth identities, one-route assignment locks, health, failure and governed-redispatch facts | Official runtime and provider adapters; no fallback chain |
   520	| `qualification` | Checker, module, route, and isolation-profile qualification | Frozen fixtures, canaries, holdouts |
   521	| `effectiveness` | Whole-workflow paired evaluation, causal ablations, owner-facing scorecards | Evaluation runners and artifacts |
   522	| `agent_collaboration` | Typed worker assignments/offers, atomic claims, fenced leases, heartbeats/liveness, mailboxes, Ranex-owned dispatch graphs and fan-out/join, role separation, worker attempts, results and handoffs | Official leaf runtime adapters; workers cannot delegate or coordinate and the context never owns `RunStatus`, work state, gate, permit, effect, merge, or release |
   523	| `repository_intelligence` | Source graph/index, language coverage, freshness, unsupported-analysis states | Atlas/tree-sitter or simpler index strategies |
   524	| `knowledge` | Skills, project memory, learned records, quarantine, sanitization, transfer approvals | Packet sources and explicitly scoped worker reads |
   525	| `scheduling` | Schedules, authenticated triggers, catch-up rules, trigger lifecycle | Cron, webhooks, external timers |
   526	| `delivery` | Channel-neutral messages, commands, decision challenges, rendering, delivery receipts | CLI, TUI, web, phone, GitHub adapters |
   527	| `artifact_management` | Content-addressed blobs, classification, access, retention, legal hold, expiry, purge | Filesystem/object-store adapters |
   528	
   529	### 9.3 Operations, evolution, and boundary contexts
   530	

web search: 
web search: https://docs.temporal.io/develop/python/workflows/versioning
web search: 
web search: 
web search: 
web search: https://argo-workflows.readthedocs.io/en/latest/workflow-restrictions/
web search: 
web search: 
web search: 
web search: https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/copyright-page01.html
web search: 
web search: 'October 2018'
web search: 
web search: https://livebook.manning.com/book/microservices-patterns/chapter-6
web search: 
web search: 
web search: 
web search: 
web search: 
web search: '7.1. Versioned Events'
web search: 
web search: https://docs.temporal.io/develop/python/best-practices/testing-suite
web search: 
web search: https://docs.aws.amazon.com/step-functions/latest/dg/statemachine-structure.html
Repository contracts and the kernel-tracer gap are now line-verified. External comparison is complete across the requested workflow systems, event frameworks/stores, and literature; synthesis is in progress.
  ✓ Inspect the cited repository contracts, ADR provisions, prior-art report, and kernel-tracer gap
  ✓ Verify the requested external prior art with dated/versioned primary sources
  → Compare the five evolution strategies and select one Ranex policy
  • Specify the workflow/event contracts, acceptance tests, and obligation mapping
  • Audit every repository claim/citation and deliver the ADR-ready recommendation
web search: 
web search: site:argo-workflows.readthedocs.io storedWorkflowTemplateSpec stored workflow template spec future execution ...
codex
The comparison has converged on a strict hybrid: immutable versioned definitions, immutable versioned event bytes, and deterministic one-to-one upcasting only in the read pipeline. The important boundary is that workflow definitions themselves are never upcast for a recorded run; their exact interpreter remains pinned.
The recommendation, alternative analysis, acceptance tests, and obligation/conflict audit are complete. Repository citations and external source version/date labels have been checked.
  ✓ Inspect the cited repository contracts, ADR provisions, prior-art report, and kernel-tracer gap
  ✓ Verify the requested external prior art with dated/versioned primary sources
  ✓ Compare the five evolution strategies and select one Ranex policy
  ✓ Specify the workflow/event contracts, acceptance tests, and obligation mapping
  ✓ Audit every repository claim/citation and deliver the ADR-ready recommendation
codex
# Proposed ADR: Canonical workflow definition, event schema, and upcaster policy

**Status:** Proposed — owner acceptance required  
**Resolves:** `HERMES-OWNER-DECISION-001` only when accepted  
**Decision:** Use immutable, content-addressed workflow definitions; retain `DomainEventEnvelopeV1`; pin exact definition/interpreter/schema identities per run; and evolve events through deterministic one-to-one upcasting on read without rewriting stored history.

This matches the corpus’s five required properties—immutable definitions, interpreter version, event-schema version, upcaster compatibility, and replay checks—classified as mature pattern with an R&D schema ([docs/research/hermes-core-architecture-research-2026-07-27.md:786](/home/soultransit/devtony/ranex/docs/research/hermes-core-architecture-research-2026-07-27.md:786)). The required frozen-history tests are already stated explicitly ([docs/research/hermes-core-architecture-research-2026-07-27.md:2020](/home/soultransit/devtony/ranex/docs/research/hermes-core-architecture-research-2026-07-27.md:2020)).

## 1. Decision

### 1.1 `WorkflowDefinitionV1`

A workflow definition is a closed RFC 8785 JSON document:

```json
{
  "schema_version": "workflow-definition/v1",
  "workflow_definition_id": "stable-logical-id",
  "workflow_definition_version": 7,
  "workflow_interpreter_version":
    "ranex.workflow-interpreter/1.0.0@sha256:<64-hex>",
  "event_contract": {
    "envelope_schema_version": "domain-event-envelope/v1",
    "schema_registry_version":
      "ranex.schema-registry/2026-07-30@sha256:<64-hex>"
  },
  "input_schema_ref": {
    "id": "schema-id",
    "digest": "sha256:<64-hex>"
  },
  "output_schema_ref": {
    "id": "schema-id",
    "digest": "sha256:<64-hex>"
  },
  "entry_node_key": "collect-evidence",
  "run_policy": {
    "timeout_ms": 86400000,
    "cancellation_mode": "WAIT_FOR_RECORDED_OUTCOME"
  },
  "nodes": {
    "collect-evidence": {
      "kind": "activity",
      "label": "Collect evidence",
      "bindings": {},
      "output_schema_ref": {
        "id": "schema-id",
        "digest": "sha256:<64-hex>"
      },
      "config": {}
    }
  },
  "edges": {
    "evidence-collected": {
      "from": "collect-evidence",
      "on": "SUCCEEDED",
      "to": "evaluate-gate"
    }
  },
  "digest": "sha256:<RFC-8785 document excluding digest>"
}
```

Rules:

- The document and every nested object are closed: unknown fields fail validation.
- `workflow_definition_id` identifies the logical workflow family. `workflow_definition_version` is a positive, monotonically increasing integer within that family.
- `(workflow_definition_id, workflow_definition_version)` may resolve to exactly one digest. Reusing that pair with different bytes is a conflict.
- `workflow_interpreter_version` is an exact content identity, never a range, tag, alias, or bare `latest`. The existing exact-subject contract permits a semver or content ID; this ADR chooses content ID ([docs/architecture/AI_ARTIFACT_CONTRACTS.md:164](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:164)).
- `event_contract` pins both the envelope revision and immutable schema-registry version. The exact subject already requires the schema-registry version ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1430](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1430)).
- `input_schema_ref`, `output_schema_ref`, and all other references use the existing closed `{id,digest}` form ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2692](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2692)).
- `nodes` and `edges` are JSON maps rather than position-sensitive arrays. RFC 8785 canonical property ordering makes source ordering immaterial; RFC 8785 was published June 2020 specifically to produce repeatable hashable JSON representations ([RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785)).
- Any change—including a label, binding, retry rule, edge, or node configuration—creates a new definition version and digest. Old bytes remain immutable and addressable.
- Definition approval is not embedded in the definition digest. Eligibility is checked when `WorkflowPinned` is recorded, using its existing `workflow_policy_ref`; its catalog precondition already requires an approved compatible definition ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2767](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2767)).
- This reuses the existing `WorkflowDefinition` reference and `artifact_management` content-addressed storage; it does not introduce a new artifact or bounded context ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:527](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:527), [docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768)).

### 1.2 Node and edge contract

`node_key` is author-assigned, unique within the definition, and matches:

```text
^[a-z][a-z0-9._-]{0,63}$
```

It is never derived from array position, display label, or layout.

The allowed `kind` values in `WorkflowDefinitionV1` are:

```text
activity
choice
evidence_gate
signal_wait
timer
compensation
reconciliation_wait
terminal
```

Sequence is represented by edges. Retry and cancellation are policies, not nodes. This covers the currently authorized semantics while excluding parallel/fan-out, map, and dynamic graph mutation, which are explicitly barred pending further semantics and tests ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3083](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3083)).

Every node contains:

- `kind`
- `label`
- `bindings`
- `output_schema_ref`
- closed, kind-specific `config`

A binding is exactly one of:

```json
{"source": "literal", "value": "<any valid JSON value>"}
{"source": "workflow_input", "path": "/json/pointer"}
{"source": "node_output", "node_key": "prior-node", "path": "/json/pointer"}
```

Paths use [RFC 6901 JSON Pointer (April 2013)](https://www.rfc-editor.org/rfc/rfc6901), avoiding an executable expression language.

Activity configuration contains:

- `activity_type`
- sorted `required_capability_ids`
- `timeout_ms`
- `retry: {max_attempts, delays_ms, retryable_outcomes}`
- `effects`, keyed by stable `effect_key`, with `effect_type`, `required`, `capability_id`, and nullable `compensation_node_key`

Required versus optional effects and compensation are already definition-owned concepts ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3109](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3109)).

Choice edges contain either a `when` predicate or `default: true`. The closed predicate grammar is:

```text
exists(path)
eq|ne|lt|lte|gt|gte(path, JSON scalar)
all(predicate...)
any(predicate...)
not(predicate)
```

Exactly one condition may match. If multiple match, or none match without a default, interpretation returns `UNKNOWN` and blocks. It never chooses by map order.

### 1.3 Runtime `WorkflowNodeId`

The runtime node identity is:

```text
wfnode_<lowercase-base32-no-padding(
  SHA-256(
    RFC8785({
      "workflow_definition_id": ...,
      "workflow_definition_version": ...,
      "workflow_definition_digest": ...,
      "node_key": ...
    })
  )
)>
```

Consequences:

- Reordering or relabeling source material cannot accidentally change identity without changing the definition digest.
- The same `node_key` in a new workflow version has a different `WorkflowNodeId`.
- Cross-version lineage is expressed through the stable `node_key`, not by treating two runtime nodes as identical.
- Every `workflow_node_id` in an event must recompute from the run’s pinned definition.

This specializes the already-accepted rule that `WorkflowNodeId` is a versioned node from the pinned definition ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1494](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1494)).

### 1.4 Version-pin locations

| Location | Required pins |
|---|---|
| Workflow definition | Definition schema version, definition ID/version/digest, exact interpreter content ID, event-envelope version, schema-registry content ID |
| `WorkflowPinned` journal event | Existing `workflow_definition_ref`, exact content-valued `workflow_interpreter_version`, existing `workflow_policy_ref` |
| Event subject | Workflow definition ID/digest, interpreter content ID, schema-registry version, expected aggregate version |
| Canonical current row | Denormalized copy of the run’s definition ref/digest, interpreter content ID, schema-registry version and current node ID |
| Snapshot header | Same pins plus journal-head event instance ID, aggregate version, sequence and digest |

No fields are added to the already-closed `WorkflowPinned` v1 payload. The definition digest is carried by its existing `Ref<WorkflowDefinition>`; the interpreter field contains the exact content ID; and the schema-registry version is carried by the immutable exact subject ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768), [docs/architecture/AI_ARTIFACT_CONTRACTS.md:164](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:164)).

Alias or “current” resolution is allowed only before `WorkflowPinned`. Once recorded, recovery must either load that exact definition/interpreter/schema combination or block before producing an effect or outbox intent.

Workflow definitions are **not upcast for an existing run**. A new definition schema requires a new definition revision and compatible interpreter content ID; old runs continue using the old bytes and interpreter.

### 1.5 Persisted event

Keep `DomainEventEnvelopeV1` unchanged:

```json
{
  "schema_version": "domain-event-envelope/v1",
  "event_id": "EVENT-ACTIVITYREQUESTED",
  "event_name": "ActivityRequested",
  "event_version": 1,
  "event_instance_id": "<uuidv7>",
  "owner_context": "governed_execution",
  "producer_service_id": "<registered-service-id>",
  "producer_release_digest": "sha256:<64-hex>",
  "aggregate_type": "Run",
  "aggregate_id": "run_<uuidv7>",
  "source_aggregate_version": 4,
  "aggregate_version": 5,
  "aggregate_event_sequence": 5,
  "subject_ref": "<immutable-subject-ref>",
  "subject_digest": "sha256:<64-hex>",
  "correlation_id": "<nonempty-id>",
  "causation_id": "<exact-command-or-event-id>",
  "idempotency_key": "<stable-logical-operation-key>",
  "occurred_at": "<strict-UTC>",
  "recorded_at": "<strict-UTC>",
  "payload_schema_ref":
    "ranex:event-payload:ActivityRequested:v1",
  "payload_schema_digest": "sha256:<64-hex>",
  "payload": {
    "...": "closed event-specific payload"
  },
  "data_classification": "<registered-classification>",
  "retention_policy_id": "<registered-policy>",
  "digest": "sha256:<RFC-8785 envelope excluding digest>"
}
```

These fields and invariants are already exact architecture, including gap-free per-aggregate sequence, closed payloads, schema digest, classification, retention, and whole-envelope digest ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2666](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2666)).

`event_version` is the semantic payload-schema revision for that catalog event. It is distinct from:

- `schema_version`: envelope revision;
- `aggregate_version`: resulting aggregate revision;
- `aggregate_event_sequence`: ordered journal position;
- `producer_release_digest`: writer software identity.

The journal stores the original canonical envelope bytes and digest, not JSON reconstructed later from an object or relational columns. Extracted columns may index the envelope but are not a replacement authority.

### 1.6 Event upcaster policy

Choose **explicit event versions plus deterministic upcasting on read**.

The read pipeline is:

```text
stored canonical bytes
  → verify original envelope digest/schema/producer/order
  → select chain by (event_id, event_version, payload_schema_digest)
  → apply adjacent one-to-one pure upcasters
  → produce ephemeral current ReducerEvent
  → pure Execution reducer
```

Rules:

1. The writer emits only the current registered event version. It never double-writes old and new versions.
2. Every released old version has exactly one adjacent path `vN → vN+1 → … → current`.
3. Chains may not contain gaps, branches, cycles, zero-output transformations, splits, or merges.
4. An upcaster is a total pure function over the old payload and immutable envelope metadata. It may not use time, randomness, filesystem, network, mutable configuration, or database lookups.
5. It may change only the ephemeral payload, `event_version`, and payload-schema reference/digest.
6. It must preserve:
   - catalog `event_id`;
   - `event_instance_id`;
   - aggregate type/ID and both aggregate versions;
   - aggregate sequence;
   - subject, correlation, causation and idempotency identities;
   - occurrence/recording times;
   - producer identity;
   - authority, terminal meaning, classification, retention, and evidence digests.
7. The original envelope and its digest remain unchanged. The upcast result is an `UpcastedEventView`, not a newly persisted `DomainEventEnvelopeV1`.
8. If a change cannot preserve those invariants, it is a new event catalog ID under a breaking ADR, not an upcast.
9. Missing, ambiguous, impure, or failed upcasting is `UNKNOWN`, quarantines the history, and blocks advancement.
10. Upcasters and their frozen fixtures remain deployable for at least as long as any retained history depends on them.
11. Replay never dispatches external effects. A successful replay may write a new cache snapshot, but may not update or delete journal rows.

These constraints refine the existing rule that compatible evolution requires frozen fixtures and a total deterministic upcaster preserving identity, versions, causation, authority, terminal meaning, classification, and evidence digests ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2752](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2752)).

## 2. Current kernel-tracer gap

The current aggregate contains `workflow_request_ref: str`, but no definition reference/digest, interpreter pin, event-contract pin, current node identity, or definition version ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:52](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:52)). `ExecutionCreated` likewise carries only the opaque request reference ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:59)).

The current persisted state repeats that opaque string ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58)). Its event document contains only a local schema version, Python class name, event/execution IDs, expected version and occurrence time; decoding rejects anything except `execution-event/v1` and has no compatibility chain ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:147](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:147), [.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:202](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:202)).

Therefore the exact missing implementation surface is:

- immutable `WorkflowDefinition` resolution by ref/digest;
- definition and interpreter pins in state/recovery;
- stable `WorkflowNodeId`;
- `WorkflowPinned` and node-level events;
- full `DomainEventEnvelopeV1` persistence;
- original-byte preservation;
- upcaster registry and chains;
- frozen old histories with an independent replay oracle.

This builds directly on the existing prior-art finding that replay currently lacks an independent oracle and that the tracer lacks definition/interpreter pins and an upcaster path ([docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6660](/home/soultransit/devtony/ranex/docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6660)).

## 3. Verified production precedent

External verification was performed on 2026-07-30.

| System/literature | Strategy and old-history handling | Failure/cost |
|---|---|---|
| Temporal, current 2026 docs; Server ≥1.29.1 | Pinned Workflow executions run entirely on one worker deployment version. Patching writes markers to history and retains old/new branches until old executions leave retention. Replay CI runs representative open and closed histories. [Worker Versioning](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning), [patching](https://docs.temporal.io/develop/python/workflows/versioning), [replay testing](https://docs.temporal.io/develop/python/best-practices/testing-suite). | Marker mismatch causes replay failure; pinned deployments must be retained until executions drain. |
| Axon Framework 4.13 | Stores event type plus revision and applies ordered `x → x+1` upcasters without altering history. Payload/type/metadata may change; aggregate ID, timestamp and similar envelope facts are intentionally not adjustable. [Axon 4.13 event versioning](https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/). | Upcaster ordering is critical. Axon permits zero/many output and context-aware transforms; Ranex deliberately rejects those forms. |
| Marten current docs, accessed 2026-07-30; exact product version **UNVERIFIED** | Performs old-JSON-to-current transformations on every read so projections handle only the latest schema; functions can be pure and contract-tested. [Marten event versioning](https://martendb.io/events/versioning). | Raw JSON transforms can become stringly typed; repeated upcasting costs read time; mapped renames can silently break JSON-field queries. |
| EventStoreDB/Kurrent Node client v1.1 | Persists `eventId`, stable string `eventType`, data and metadata bytes; explicitly discourages using code class names because that couples storage to code and complicates later versioning. [Kurrent/EventStoreDB appending events](https://docs.kurrent.io/clients/node/v1.1/appending-events). | A built-in EventStoreDB upcaster policy is **UNVERIFIED** in this source; schema/upcaster ownership remains application-side. |
| Argo Workflows documentation set listing v4.1.0, 2026-07-22 | A Workflow contains both spec and state; `storedWorkflowTemplateSpec` retains a resolved template spec. Secure template referencing errors if the referenced template changes during a run. [Argo core concepts](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/), [field reference](https://argoproj.github.io/argo-workflows/fields/), [restrictions](https://argo-workflows.readthedocs.io/en/latest/workflow-restrictions/). | A live mutable reference can halt a run. Ranex avoids this by pinning exact bytes/digest before execution. |
| Airflow 3.3.0 | Versioned DAG bundles keep one code version for the whole run; Git bundles record the commit and rerun against that exact code. [Airflow 3.3.0 DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html). | Unversioned local/S3/GCS bundles always use latest; processor and workers can temporarily see different DAG versions. |
| AWS Step Functions, current docs accessed 2026-07-30 | JSON state machines have one `StartAt`, a keyed `States` object, typed states and explicit transitions. A qualified version ARN associates the execution with that version at start. [State-machine structure](https://docs.aws.amazon.com/step-functions/latest/dg/statemachine-structure.html), [execution/version association](https://docs.aws.amazon.com/step-functions/latest/dg/execution-alias-version-associate.html). | Starting with an unqualified ARN does not associate the execution with a version. |
| Greg Young, *Versioning in an Event Sourced System*; publication version/date **UNVERIFIED**, accessed 2026-07-30 | Versioned types retain old handlers; convertible versions can be upcast on read. Weak schema ignores unknown fields/defaults missing fields. Copy-replace creates transformed streams. [Type versioning](https://leanpub.com/read/esversioning/leanpub-auto-basic-type-based-versioning), [weak schema](https://leanpub.com/read/esversioning/leanpub-auto-weak-schema), [copy-replace](https://leanpub.com/read/esversioning/leanpub-auto-copy-and-replace). | Type versions produce handler explosion; weak schema cannot safely rename fields; double-write breaks projection replay; copy-replace is described as the “nuclear option” because consumers and projections can see different histories. |
| Overeem et al., JSS 178, 2021 | Empirical study of 19 systems/25 engineers identifies the exact five strategies. It recommends upcasting when simple versioning/weak schema are insufficient, copy-transform only for experienced performance/maintenance pressure, and in-place only without immutability/audit requirements. [2021 paper](https://arxiv.org/pdf/2104.01146). | Upcasting adds read cost and multiple schemas; copy-transform is expensive; in-place loses immutability. |
| Kleppmann, *DDIA*, first edition, March 2017 | Verified scope: chapter 4 covers Encoding and Evolution; chapter 11 covers event sourcing, state, streams and immutability. [Official O’Reilly contents](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/copyright-page01.html). | A detailed prescription selecting Ranex’s upcaster strategy is **UNVERIFIED** in the public preview. |
| Richardson, *Microservices Patterns*, October 2018 | Verified scope: chapter 6 covers event-sourced business logic, event stores and saga orchestration; Richardson’s public pattern describes append/replay and snapshots. [Manning chapter 6](https://livebook.manning.com/book/microservices-patterns/chapter-6), [public Event Sourcing pattern](https://microservices.io/patterns/data/event-sourcing.html). | A detailed event-schema-evolution or upcaster prescription is **UNVERIFIED** in the public excerpt. |

## 4. Why this, not the five alternatives

| Alternative | Ranex disposition |
|---|---|
| Weak schema / tolerant reader | **Reject as the compatibility policy.** **INFERENCE — failure:** ignoring unknown fields or inserting defaults can silently change authority, terminal meaning, or routing while replay still “succeeds.” It also cannot safely represent renames, splits, or semantic changes and conflicts with the existing closed-payload/unknown-version quarantine rule ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2732](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2732)). |
| Versioned event types only | **Use version metadata, reject multiple reducer handlers.** **INFERENCE — failure:** permanent `ApplyV1`, `ApplyV2`, … handlers pollute the pure reducer and allow old branches to drift. Greg Young documents the resulting method explosion. |
| Upcasting on read | **Accept**, with immutable bytes and one-to-one adjacent pure functions. It keeps compatibility code outside the reducer and preserves the journal oracle. |
| Lazy in-place migration | **Reject.** **INFERENCE — failure:** rewriting an event after reading invalidates its stored envelope digest, append-only audit meaning and any frozen snapshot comparison; a crash can leave only part of the history migrated. This conflicts directly with the append-only oracle in §8.3 ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470)). |
| Copy-and-transform | **Reject as ordinary evolution; reserve for a future breaking ADR.** **INFERENCE — failure:** a transformed stream creates two histories and a cutover problem; split/merge changes event identity and sequence, while projections and snapshots may have observed different histories. It is incompatible with using the frozen original journal as the single replay oracle unless both histories and their relationship become independently governed. |

**INFERENCE — workflow consequence:** Temporal patch markers are valuable for code-defined long-running workflows, but Ranex already treats workflows as immutable approved data. Patching would add version branches inside the interpreter and weaken the simple proof “this run used these exact bytes with this exact interpreter.” Exact definition pinning is therefore the narrower production pattern for Ranex.

## 5. Costs and constraints

- **INFERENCE — retention cost:** every definition, interpreter build, upcaster and frozen fixture remains available for the lifetime of dependent histories. With permanent audit retention, compatibility code may also be permanent.
- **INFERENCE — deployment cost:** a producer cannot emit version `N+1` until all readers that may receive it have the registered upcaster/current schema.
- **INFERENCE — performance cost:** old streams pay the upcasting cost on every full replay. Snapshots reduce frequency but cannot replace or rewrite the journal.
- **INFERENCE — correction cost:** historical facts cannot be edited. Corrections require a compensating event or a new run/definition, preserving the erroneous fact in history.
- **INFERENCE — live-change constraint:** an active run cannot acquire a changed topology, new node meaning or interpreter bug fix by alias movement. It must drain, block/cancel, or undergo a separately governed migration.
- **INFERENCE — expressiveness cost:** one-to-one upcasters cannot delete, split, merge or reorder events. Such a need means the alleged “new version” is semantically a new event or requires a breaking migration ADR.
- **INFERENCE — authoring cost:** even cosmetic definition edits produce a new version/digest because the entire approved document is immutable.
- **INFERENCE — operational failure mode:** loss of an old interpreter or an upcaster is a blocking integrity incident, not something recoverable by using `latest`.

## 6. Predeclared acceptance tests

| Test | Required fixture/action | Pass condition |
|---|---|---|
| `WF-DEF-001-CLOSED` | Validate every node kind, binding, edge and predicate; inject unknown fields, unsupported kinds, missing targets, duplicate/default choice branches and fan-out/map nodes. | Valid document passes; every injected defect fails before activation. |
| `WF-DEF-002-CANONICAL` | Serialize semantically identical documents with randomized object-key order. Change one semantic value while retaining ID/version. | Equivalent documents produce identical RFC 8785 bytes/digest. Changed bytes with reused ID/version are rejected. |
| `WF-NODE-001-IDENTITY` | Reorder source, retain exact definition; then create a new definition version with the same `node_key`. | First ID remains identical; new definition produces a different `WorkflowNodeId`; every recorded ID resolves against the pinned digest. |
| `WF-PIN-001-EXACT` | Start through an alias, move alias afterward, restart recovery, remove or corrupt each pinned component in turn. | Recovery uses the originally pinned definition/interpreter/schema. Missing or mismatched pins block before effect/outbox creation. |
| `EVT-ENV-001-EXACT` | Round-trip canonical `DomainEventEnvelopeV1`; mutate every required field, payload schema digest, sequence, timestamp, classification and whole-envelope digest. | Exact bytes round-trip; each mutation is rejected or quarantined. No document is reconstructed as authoritative from index columns. |
| `UPCAST-001-REGISTRY` | Enumerate all released `(event_id, version, payload_schema_digest)` entries. Inject a gap, branch, cycle and obsolete writer. | Exactly one adjacent path reaches current; all invalid graphs fail startup/qualification; writer emits current only. |
| `UPCAST-002-PURITY` | Execute every old fixture repeatedly in fresh processes while varying clock, locale, randomness and network availability. | Every result is byte-identical. Any attempted external dependency fails the test. Original journal bytes remain unchanged. |
| `UPCAST-003-INVARIANTS` | Mutation-test every protected envelope field and attempt zero/many output. | Upcaster qualification fails on the first identity, order, authority, classification, terminal-meaning or evidence change. |
| `MIGRATION-001-NO-REWRITE` | Replay/upcast an old SQLite history while tracing writes and hashing the journal before/after. | No journal `UPDATE`/`DELETE`; row count and canonical bytes/digests are identical before and after. |
| `SNAPSHOT-001-ORACLE` | Corrupt snapshot head ID/version/digest; then delete the snapshot and replay from the journal. | Corruption blocks. Full replay reconstructs the same canonical current state and may regenerate only a cache snapshot. |
| `COMPAT-NEG-001-FAIL-CLOSED` | Supply unknown envelope, event, definition, interpreter and schema-registry versions, plus a missing upcaster. | All yield `UNKNOWN`/quarantine and no effect dispatch. |
| `REPLAY-FROZEN-001` | Commit frozen original bytes for `WorkflowDefinitionV1`, interpreter content ID, old event envelopes, expected snapshot/current row and expected logical command/outbox records. Include normal, blocked, cancelled, linked-retry, waived and recovered histories, as required by research ([docs/research/hermes-core-architecture-research-2026-07-27.md:2020](/home/soultransit/devtony/ranex/docs/research/hermes-core-architecture-research-2026-07-27.md:2020)). | Current code verifies original digests, upcasts, reduces without dispatch, and reproduces byte-identical canonical state, journal head, aggregate version, sequence and expected command/outbox records. A second replay is identical. Removing/changing an upcaster, changing interpreter behavior, or mutating command order/payload must fail at the first mismatch. |
| `REPLAY-CORPUS-001` | In CI, replay a representative sample of retained open and closed histories in addition to permanent fixtures, following Temporal’s tested-history practice. | Any replay incompatibility fails CI. |

The frozen fixture must be captured from original persisted bytes, not recreated through current constructors. This addresses the prior report’s independent-oracle finding ([docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6673](/home/soultransit/devtony/ranex/docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6673)).

## 7. Accepted-obligation interaction and conflict audit

| Obligation | Interaction |
|---|---|
| `HERMES-PROMOTION-058` | Definition/event/node hashing uses the shared identity and canonical-serialization facilities; no competing serializer is introduced ([ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742)). |
| `-059` | The reducer consumes only normalized current `ReducerEvent` values and remains pure. Upcasting is a separate pure pre-reducer stage ([ADR-0013:752](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:752)). |
| `-060` | The relational current row remains canonical operational state with explicit version; pins are denormalized into it for recovery checks ([ADR-0013:762](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:762)). |
| `-061` | Original event, new state/version and outbox remain one SQLite unit of work. The upcaster never rewrites that journal ([ADR-0013:772](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:772)). |
| `-062` | This schema qualifies compatibility for `Execution` only. It does not authorize event sourcing for another aggregate or activate event sourcing by itself ([ADR-0013:782](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:782)). |
| `-063` | Unknown/missing compatibility blocks fail-closed. Replay does not bypass the policy-enforcement point or dispatch effects ([ADR-0013:792](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:792)). |
| `-064` | Identity, serializer, schema and upcaster APIs remain kernel contracts subject to the pre-feature import tests ([ADR-0013:802](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:802)). |
| `-065` | Frozen replay strengthens, but does not replace, the separately required crash-boundary and no-Hermes-import tests ([ADR-0013:812](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:812)). |
| §8.3 | The ordered journal stays the replay/audit oracle; current row is operational; snapshots are accelerators; mismatch blocks ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470)). |

**INFERENCE — conflict audit:** No conflict was found. In particular, the recommendation does not add fields to the closed `WorkflowPinned` payload, does not replace `DomainEventEnvelopeV1`, does not rewrite history, and does not expand event sourcing beyond `Execution`.

`HERMES-OWNER-DECISION-002` remains separate because runner-versus-durable-runtime selection is a production-readiness decision ([ADR-0013:835](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:835)). `HERMES-OWNER-DECISION-020` also remains separate because only it may activate Execution event sourcing after qualification ([ADR-0013:1051](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1051)).

## 8. Exact owner decision still required

`HERMES-OWNER-DECISION-001` has no default and remains blocking until an accepted ADR exists ([ADR-0013:823](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:823), [ADR-0013:1150](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1150)).

**INFERENCE — remaining choice:** there is no technical selector left inside this recommendation. The genuine owner choice is whether to accept its operational cost and fail-closed behavior as one indivisible compatibility policy.

The question to record is:

> Do you ACCEPT immutable content-addressed `WorkflowDefinitionV1` documents with digest-derived versioned node IDs; exact per-run definition/interpreter/schema pins; unchanged `DomainEventEnvelopeV1`; and deterministic one-to-one read-time upcasting over immutable original event bytes, with failures blocking and frozen-old-history replay as a mandatory acceptance test?

An answer of “yes,” captured in an accepted ADR with the tests above, resolves `HERMES-OWNER-DECISION-001`. An answer of “no” must name a replacement for each of the five elements and explicitly accept the corresponding replay/audit failure modes.

No repository files were modified.
tokens used
469,226
# Proposed ADR: Canonical workflow definition, event schema, and upcaster policy

**Status:** Proposed — owner acceptance required  
**Resolves:** `HERMES-OWNER-DECISION-001` only when accepted  
**Decision:** Use immutable, content-addressed workflow definitions; retain `DomainEventEnvelopeV1`; pin exact definition/interpreter/schema identities per run; and evolve events through deterministic one-to-one upcasting on read without rewriting stored history.

This matches the corpus’s five required properties—immutable definitions, interpreter version, event-schema version, upcaster compatibility, and replay checks—classified as mature pattern with an R&D schema ([docs/research/hermes-core-architecture-research-2026-07-27.md:786](/home/soultransit/devtony/ranex/docs/research/hermes-core-architecture-research-2026-07-27.md:786)). The required frozen-history tests are already stated explicitly ([docs/research/hermes-core-architecture-research-2026-07-27.md:2020](/home/soultransit/devtony/ranex/docs/research/hermes-core-architecture-research-2026-07-27.md:2020)).

## 1. Decision

### 1.1 `WorkflowDefinitionV1`

A workflow definition is a closed RFC 8785 JSON document:

```json
{
  "schema_version": "workflow-definition/v1",
  "workflow_definition_id": "stable-logical-id",
  "workflow_definition_version": 7,
  "workflow_interpreter_version":
    "ranex.workflow-interpreter/1.0.0@sha256:<64-hex>",
  "event_contract": {
    "envelope_schema_version": "domain-event-envelope/v1",
    "schema_registry_version":
      "ranex.schema-registry/2026-07-30@sha256:<64-hex>"
  },
  "input_schema_ref": {
    "id": "schema-id",
    "digest": "sha256:<64-hex>"
  },
  "output_schema_ref": {
    "id": "schema-id",
    "digest": "sha256:<64-hex>"
  },
  "entry_node_key": "collect-evidence",
  "run_policy": {
    "timeout_ms": 86400000,
    "cancellation_mode": "WAIT_FOR_RECORDED_OUTCOME"
  },
  "nodes": {
    "collect-evidence": {
      "kind": "activity",
      "label": "Collect evidence",
      "bindings": {},
      "output_schema_ref": {
        "id": "schema-id",
        "digest": "sha256:<64-hex>"
      },
      "config": {}
    }
  },
  "edges": {
    "evidence-collected": {
      "from": "collect-evidence",
      "on": "SUCCEEDED",
      "to": "evaluate-gate"
    }
  },
  "digest": "sha256:<RFC-8785 document excluding digest>"
}
```

Rules:

- The document and every nested object are closed: unknown fields fail validation.
- `workflow_definition_id` identifies the logical workflow family. `workflow_definition_version` is a positive, monotonically increasing integer within that family.
- `(workflow_definition_id, workflow_definition_version)` may resolve to exactly one digest. Reusing that pair with different bytes is a conflict.
- `workflow_interpreter_version` is an exact content identity, never a range, tag, alias, or bare `latest`. The existing exact-subject contract permits a semver or content ID; this ADR chooses content ID ([docs/architecture/AI_ARTIFACT_CONTRACTS.md:164](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:164)).
- `event_contract` pins both the envelope revision and immutable schema-registry version. The exact subject already requires the schema-registry version ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1430](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1430)).
- `input_schema_ref`, `output_schema_ref`, and all other references use the existing closed `{id,digest}` form ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2692](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2692)).
- `nodes` and `edges` are JSON maps rather than position-sensitive arrays. RFC 8785 canonical property ordering makes source ordering immaterial; RFC 8785 was published June 2020 specifically to produce repeatable hashable JSON representations ([RFC 8785](https://datatracker.ietf.org/doc/html/rfc8785)).
- Any change—including a label, binding, retry rule, edge, or node configuration—creates a new definition version and digest. Old bytes remain immutable and addressable.
- Definition approval is not embedded in the definition digest. Eligibility is checked when `WorkflowPinned` is recorded, using its existing `workflow_policy_ref`; its catalog precondition already requires an approved compatible definition ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2767](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2767)).
- This reuses the existing `WorkflowDefinition` reference and `artifact_management` content-addressed storage; it does not introduce a new artifact or bounded context ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:527](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:527), [docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768)).

### 1.2 Node and edge contract

`node_key` is author-assigned, unique within the definition, and matches:

```text
^[a-z][a-z0-9._-]{0,63}$
```

It is never derived from array position, display label, or layout.

The allowed `kind` values in `WorkflowDefinitionV1` are:

```text
activity
choice
evidence_gate
signal_wait
timer
compensation
reconciliation_wait
terminal
```

Sequence is represented by edges. Retry and cancellation are policies, not nodes. This covers the currently authorized semantics while excluding parallel/fan-out, map, and dynamic graph mutation, which are explicitly barred pending further semantics and tests ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3083](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3083)).

Every node contains:

- `kind`
- `label`
- `bindings`
- `output_schema_ref`
- closed, kind-specific `config`

A binding is exactly one of:

```json
{"source": "literal", "value": "<any valid JSON value>"}
{"source": "workflow_input", "path": "/json/pointer"}
{"source": "node_output", "node_key": "prior-node", "path": "/json/pointer"}
```

Paths use [RFC 6901 JSON Pointer (April 2013)](https://www.rfc-editor.org/rfc/rfc6901), avoiding an executable expression language.

Activity configuration contains:

- `activity_type`
- sorted `required_capability_ids`
- `timeout_ms`
- `retry: {max_attempts, delays_ms, retryable_outcomes}`
- `effects`, keyed by stable `effect_key`, with `effect_type`, `required`, `capability_id`, and nullable `compensation_node_key`

Required versus optional effects and compensation are already definition-owned concepts ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3109](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:3109)).

Choice edges contain either a `when` predicate or `default: true`. The closed predicate grammar is:

```text
exists(path)
eq|ne|lt|lte|gt|gte(path, JSON scalar)
all(predicate...)
any(predicate...)
not(predicate)
```

Exactly one condition may match. If multiple match, or none match without a default, interpretation returns `UNKNOWN` and blocks. It never chooses by map order.

### 1.3 Runtime `WorkflowNodeId`

The runtime node identity is:

```text
wfnode_<lowercase-base32-no-padding(
  SHA-256(
    RFC8785({
      "workflow_definition_id": ...,
      "workflow_definition_version": ...,
      "workflow_definition_digest": ...,
      "node_key": ...
    })
  )
)>
```

Consequences:

- Reordering or relabeling source material cannot accidentally change identity without changing the definition digest.
- The same `node_key` in a new workflow version has a different `WorkflowNodeId`.
- Cross-version lineage is expressed through the stable `node_key`, not by treating two runtime nodes as identical.
- Every `workflow_node_id` in an event must recompute from the run’s pinned definition.

This specializes the already-accepted rule that `WorkflowNodeId` is a versioned node from the pinned definition ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1494](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:1494)).

### 1.4 Version-pin locations

| Location | Required pins |
|---|---|
| Workflow definition | Definition schema version, definition ID/version/digest, exact interpreter content ID, event-envelope version, schema-registry content ID |
| `WorkflowPinned` journal event | Existing `workflow_definition_ref`, exact content-valued `workflow_interpreter_version`, existing `workflow_policy_ref` |
| Event subject | Workflow definition ID/digest, interpreter content ID, schema-registry version, expected aggregate version |
| Canonical current row | Denormalized copy of the run’s definition ref/digest, interpreter content ID, schema-registry version and current node ID |
| Snapshot header | Same pins plus journal-head event instance ID, aggregate version, sequence and digest |

No fields are added to the already-closed `WorkflowPinned` v1 payload. The definition digest is carried by its existing `Ref<WorkflowDefinition>`; the interpreter field contains the exact content ID; and the schema-registry version is carried by the immutable exact subject ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2768), [docs/architecture/AI_ARTIFACT_CONTRACTS.md:164](/home/soultransit/devtony/ranex/docs/architecture/AI_ARTIFACT_CONTRACTS.md:164)).

Alias or “current” resolution is allowed only before `WorkflowPinned`. Once recorded, recovery must either load that exact definition/interpreter/schema combination or block before producing an effect or outbox intent.

Workflow definitions are **not upcast for an existing run**. A new definition schema requires a new definition revision and compatible interpreter content ID; old runs continue using the old bytes and interpreter.

### 1.5 Persisted event

Keep `DomainEventEnvelopeV1` unchanged:

```json
{
  "schema_version": "domain-event-envelope/v1",
  "event_id": "EVENT-ACTIVITYREQUESTED",
  "event_name": "ActivityRequested",
  "event_version": 1,
  "event_instance_id": "<uuidv7>",
  "owner_context": "governed_execution",
  "producer_service_id": "<registered-service-id>",
  "producer_release_digest": "sha256:<64-hex>",
  "aggregate_type": "Run",
  "aggregate_id": "run_<uuidv7>",
  "source_aggregate_version": 4,
  "aggregate_version": 5,
  "aggregate_event_sequence": 5,
  "subject_ref": "<immutable-subject-ref>",
  "subject_digest": "sha256:<64-hex>",
  "correlation_id": "<nonempty-id>",
  "causation_id": "<exact-command-or-event-id>",
  "idempotency_key": "<stable-logical-operation-key>",
  "occurred_at": "<strict-UTC>",
  "recorded_at": "<strict-UTC>",
  "payload_schema_ref":
    "ranex:event-payload:ActivityRequested:v1",
  "payload_schema_digest": "sha256:<64-hex>",
  "payload": {
    "...": "closed event-specific payload"
  },
  "data_classification": "<registered-classification>",
  "retention_policy_id": "<registered-policy>",
  "digest": "sha256:<RFC-8785 envelope excluding digest>"
}
```

These fields and invariants are already exact architecture, including gap-free per-aggregate sequence, closed payloads, schema digest, classification, retention, and whole-envelope digest ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2666](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2666)).

`event_version` is the semantic payload-schema revision for that catalog event. It is distinct from:

- `schema_version`: envelope revision;
- `aggregate_version`: resulting aggregate revision;
- `aggregate_event_sequence`: ordered journal position;
- `producer_release_digest`: writer software identity.

The journal stores the original canonical envelope bytes and digest, not JSON reconstructed later from an object or relational columns. Extracted columns may index the envelope but are not a replacement authority.

### 1.6 Event upcaster policy

Choose **explicit event versions plus deterministic upcasting on read**.

The read pipeline is:

```text
stored canonical bytes
  → verify original envelope digest/schema/producer/order
  → select chain by (event_id, event_version, payload_schema_digest)
  → apply adjacent one-to-one pure upcasters
  → produce ephemeral current ReducerEvent
  → pure Execution reducer
```

Rules:

1. The writer emits only the current registered event version. It never double-writes old and new versions.
2. Every released old version has exactly one adjacent path `vN → vN+1 → … → current`.
3. Chains may not contain gaps, branches, cycles, zero-output transformations, splits, or merges.
4. An upcaster is a total pure function over the old payload and immutable envelope metadata. It may not use time, randomness, filesystem, network, mutable configuration, or database lookups.
5. It may change only the ephemeral payload, `event_version`, and payload-schema reference/digest.
6. It must preserve:
   - catalog `event_id`;
   - `event_instance_id`;
   - aggregate type/ID and both aggregate versions;
   - aggregate sequence;
   - subject, correlation, causation and idempotency identities;
   - occurrence/recording times;
   - producer identity;
   - authority, terminal meaning, classification, retention, and evidence digests.
7. The original envelope and its digest remain unchanged. The upcast result is an `UpcastedEventView`, not a newly persisted `DomainEventEnvelopeV1`.
8. If a change cannot preserve those invariants, it is a new event catalog ID under a breaking ADR, not an upcast.
9. Missing, ambiguous, impure, or failed upcasting is `UNKNOWN`, quarantines the history, and blocks advancement.
10. Upcasters and their frozen fixtures remain deployable for at least as long as any retained history depends on them.
11. Replay never dispatches external effects. A successful replay may write a new cache snapshot, but may not update or delete journal rows.

These constraints refine the existing rule that compatible evolution requires frozen fixtures and a total deterministic upcaster preserving identity, versions, causation, authority, terminal meaning, classification, and evidence digests ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2752](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2752)).

## 2. Current kernel-tracer gap

The current aggregate contains `workflow_request_ref: str`, but no definition reference/digest, interpreter pin, event-contract pin, current node identity, or definition version ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:52](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:52)). `ExecutionCreated` likewise carries only the opaque request reference ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:59)).

The current persisted state repeats that opaque string ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58)). Its event document contains only a local schema version, Python class name, event/execution IDs, expected version and occurrence time; decoding rejects anything except `execution-event/v1` and has no compatibility chain ([.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:147](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:147), [.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:202](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:202)).

Therefore the exact missing implementation surface is:

- immutable `WorkflowDefinition` resolution by ref/digest;
- definition and interpreter pins in state/recovery;
- stable `WorkflowNodeId`;
- `WorkflowPinned` and node-level events;
- full `DomainEventEnvelopeV1` persistence;
- original-byte preservation;
- upcaster registry and chains;
- frozen old histories with an independent replay oracle.

This builds directly on the existing prior-art finding that replay currently lacks an independent oracle and that the tracer lacks definition/interpreter pins and an upcaster path ([docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6660](/home/soultransit/devtony/ranex/docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6660)).

## 3. Verified production precedent

External verification was performed on 2026-07-30.

| System/literature | Strategy and old-history handling | Failure/cost |
|---|---|---|
| Temporal, current 2026 docs; Server ≥1.29.1 | Pinned Workflow executions run entirely on one worker deployment version. Patching writes markers to history and retains old/new branches until old executions leave retention. Replay CI runs representative open and closed histories. [Worker Versioning](https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning), [patching](https://docs.temporal.io/develop/python/workflows/versioning), [replay testing](https://docs.temporal.io/develop/python/best-practices/testing-suite). | Marker mismatch causes replay failure; pinned deployments must be retained until executions drain. |
| Axon Framework 4.13 | Stores event type plus revision and applies ordered `x → x+1` upcasters without altering history. Payload/type/metadata may change; aggregate ID, timestamp and similar envelope facts are intentionally not adjustable. [Axon 4.13 event versioning](https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/). | Upcaster ordering is critical. Axon permits zero/many output and context-aware transforms; Ranex deliberately rejects those forms. |
| Marten current docs, accessed 2026-07-30; exact product version **UNVERIFIED** | Performs old-JSON-to-current transformations on every read so projections handle only the latest schema; functions can be pure and contract-tested. [Marten event versioning](https://martendb.io/events/versioning). | Raw JSON transforms can become stringly typed; repeated upcasting costs read time; mapped renames can silently break JSON-field queries. |
| EventStoreDB/Kurrent Node client v1.1 | Persists `eventId`, stable string `eventType`, data and metadata bytes; explicitly discourages using code class names because that couples storage to code and complicates later versioning. [Kurrent/EventStoreDB appending events](https://docs.kurrent.io/clients/node/v1.1/appending-events). | A built-in EventStoreDB upcaster policy is **UNVERIFIED** in this source; schema/upcaster ownership remains application-side. |
| Argo Workflows documentation set listing v4.1.0, 2026-07-22 | A Workflow contains both spec and state; `storedWorkflowTemplateSpec` retains a resolved template spec. Secure template referencing errors if the referenced template changes during a run. [Argo core concepts](https://argo-workflows.readthedocs.io/en/latest/workflow-concepts/), [field reference](https://argoproj.github.io/argo-workflows/fields/), [restrictions](https://argo-workflows.readthedocs.io/en/latest/workflow-restrictions/). | A live mutable reference can halt a run. Ranex avoids this by pinning exact bytes/digest before execution. |
| Airflow 3.3.0 | Versioned DAG bundles keep one code version for the whole run; Git bundles record the commit and rerun against that exact code. [Airflow 3.3.0 DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html). | Unversioned local/S3/GCS bundles always use latest; processor and workers can temporarily see different DAG versions. |
| AWS Step Functions, current docs accessed 2026-07-30 | JSON state machines have one `StartAt`, a keyed `States` object, typed states and explicit transitions. A qualified version ARN associates the execution with that version at start. [State-machine structure](https://docs.aws.amazon.com/step-functions/latest/dg/statemachine-structure.html), [execution/version association](https://docs.aws.amazon.com/step-functions/latest/dg/execution-alias-version-associate.html). | Starting with an unqualified ARN does not associate the execution with a version. |
| Greg Young, *Versioning in an Event Sourced System*; publication version/date **UNVERIFIED**, accessed 2026-07-30 | Versioned types retain old handlers; convertible versions can be upcast on read. Weak schema ignores unknown fields/defaults missing fields. Copy-replace creates transformed streams. [Type versioning](https://leanpub.com/read/esversioning/leanpub-auto-basic-type-based-versioning), [weak schema](https://leanpub.com/read/esversioning/leanpub-auto-weak-schema), [copy-replace](https://leanpub.com/read/esversioning/leanpub-auto-copy-and-replace). | Type versions produce handler explosion; weak schema cannot safely rename fields; double-write breaks projection replay; copy-replace is described as the “nuclear option” because consumers and projections can see different histories. |
| Overeem et al., JSS 178, 2021 | Empirical study of 19 systems/25 engineers identifies the exact five strategies. It recommends upcasting when simple versioning/weak schema are insufficient, copy-transform only for experienced performance/maintenance pressure, and in-place only without immutability/audit requirements. [2021 paper](https://arxiv.org/pdf/2104.01146). | Upcasting adds read cost and multiple schemas; copy-transform is expensive; in-place loses immutability. |
| Kleppmann, *DDIA*, first edition, March 2017 | Verified scope: chapter 4 covers Encoding and Evolution; chapter 11 covers event sourcing, state, streams and immutability. [Official O’Reilly contents](https://www.oreilly.com/library/view/designing-data-intensive-applications/9781491903063/copyright-page01.html). | A detailed prescription selecting Ranex’s upcaster strategy is **UNVERIFIED** in the public preview. |
| Richardson, *Microservices Patterns*, October 2018 | Verified scope: chapter 6 covers event-sourced business logic, event stores and saga orchestration; Richardson’s public pattern describes append/replay and snapshots. [Manning chapter 6](https://livebook.manning.com/book/microservices-patterns/chapter-6), [public Event Sourcing pattern](https://microservices.io/patterns/data/event-sourcing.html). | A detailed event-schema-evolution or upcaster prescription is **UNVERIFIED** in the public excerpt. |

## 4. Why this, not the five alternatives

| Alternative | Ranex disposition |
|---|---|
| Weak schema / tolerant reader | **Reject as the compatibility policy.** **INFERENCE — failure:** ignoring unknown fields or inserting defaults can silently change authority, terminal meaning, or routing while replay still “succeeds.” It also cannot safely represent renames, splits, or semantic changes and conflicts with the existing closed-payload/unknown-version quarantine rule ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2732](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:2732)). |
| Versioned event types only | **Use version metadata, reject multiple reducer handlers.** **INFERENCE — failure:** permanent `ApplyV1`, `ApplyV2`, … handlers pollute the pure reducer and allow old branches to drift. Greg Young documents the resulting method explosion. |
| Upcasting on read | **Accept**, with immutable bytes and one-to-one adjacent pure functions. It keeps compatibility code outside the reducer and preserves the journal oracle. |
| Lazy in-place migration | **Reject.** **INFERENCE — failure:** rewriting an event after reading invalidates its stored envelope digest, append-only audit meaning and any frozen snapshot comparison; a crash can leave only part of the history migrated. This conflicts directly with the append-only oracle in §8.3 ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470)). |
| Copy-and-transform | **Reject as ordinary evolution; reserve for a future breaking ADR.** **INFERENCE — failure:** a transformed stream creates two histories and a cutover problem; split/merge changes event identity and sequence, while projections and snapshots may have observed different histories. It is incompatible with using the frozen original journal as the single replay oracle unless both histories and their relationship become independently governed. |

**INFERENCE — workflow consequence:** Temporal patch markers are valuable for code-defined long-running workflows, but Ranex already treats workflows as immutable approved data. Patching would add version branches inside the interpreter and weaken the simple proof “this run used these exact bytes with this exact interpreter.” Exact definition pinning is therefore the narrower production pattern for Ranex.

## 5. Costs and constraints

- **INFERENCE — retention cost:** every definition, interpreter build, upcaster and frozen fixture remains available for the lifetime of dependent histories. With permanent audit retention, compatibility code may also be permanent.
- **INFERENCE — deployment cost:** a producer cannot emit version `N+1` until all readers that may receive it have the registered upcaster/current schema.
- **INFERENCE — performance cost:** old streams pay the upcasting cost on every full replay. Snapshots reduce frequency but cannot replace or rewrite the journal.
- **INFERENCE — correction cost:** historical facts cannot be edited. Corrections require a compensating event or a new run/definition, preserving the erroneous fact in history.
- **INFERENCE — live-change constraint:** an active run cannot acquire a changed topology, new node meaning or interpreter bug fix by alias movement. It must drain, block/cancel, or undergo a separately governed migration.
- **INFERENCE — expressiveness cost:** one-to-one upcasters cannot delete, split, merge or reorder events. Such a need means the alleged “new version” is semantically a new event or requires a breaking migration ADR.
- **INFERENCE — authoring cost:** even cosmetic definition edits produce a new version/digest because the entire approved document is immutable.
- **INFERENCE — operational failure mode:** loss of an old interpreter or an upcaster is a blocking integrity incident, not something recoverable by using `latest`.

## 6. Predeclared acceptance tests

| Test | Required fixture/action | Pass condition |
|---|---|---|
| `WF-DEF-001-CLOSED` | Validate every node kind, binding, edge and predicate; inject unknown fields, unsupported kinds, missing targets, duplicate/default choice branches and fan-out/map nodes. | Valid document passes; every injected defect fails before activation. |
| `WF-DEF-002-CANONICAL` | Serialize semantically identical documents with randomized object-key order. Change one semantic value while retaining ID/version. | Equivalent documents produce identical RFC 8785 bytes/digest. Changed bytes with reused ID/version are rejected. |
| `WF-NODE-001-IDENTITY` | Reorder source, retain exact definition; then create a new definition version with the same `node_key`. | First ID remains identical; new definition produces a different `WorkflowNodeId`; every recorded ID resolves against the pinned digest. |
| `WF-PIN-001-EXACT` | Start through an alias, move alias afterward, restart recovery, remove or corrupt each pinned component in turn. | Recovery uses the originally pinned definition/interpreter/schema. Missing or mismatched pins block before effect/outbox creation. |
| `EVT-ENV-001-EXACT` | Round-trip canonical `DomainEventEnvelopeV1`; mutate every required field, payload schema digest, sequence, timestamp, classification and whole-envelope digest. | Exact bytes round-trip; each mutation is rejected or quarantined. No document is reconstructed as authoritative from index columns. |
| `UPCAST-001-REGISTRY` | Enumerate all released `(event_id, version, payload_schema_digest)` entries. Inject a gap, branch, cycle and obsolete writer. | Exactly one adjacent path reaches current; all invalid graphs fail startup/qualification; writer emits current only. |
| `UPCAST-002-PURITY` | Execute every old fixture repeatedly in fresh processes while varying clock, locale, randomness and network availability. | Every result is byte-identical. Any attempted external dependency fails the test. Original journal bytes remain unchanged. |
| `UPCAST-003-INVARIANTS` | Mutation-test every protected envelope field and attempt zero/many output. | Upcaster qualification fails on the first identity, order, authority, classification, terminal-meaning or evidence change. |
| `MIGRATION-001-NO-REWRITE` | Replay/upcast an old SQLite history while tracing writes and hashing the journal before/after. | No journal `UPDATE`/`DELETE`; row count and canonical bytes/digests are identical before and after. |
| `SNAPSHOT-001-ORACLE` | Corrupt snapshot head ID/version/digest; then delete the snapshot and replay from the journal. | Corruption blocks. Full replay reconstructs the same canonical current state and may regenerate only a cache snapshot. |
| `COMPAT-NEG-001-FAIL-CLOSED` | Supply unknown envelope, event, definition, interpreter and schema-registry versions, plus a missing upcaster. | All yield `UNKNOWN`/quarantine and no effect dispatch. |
| `REPLAY-FROZEN-001` | Commit frozen original bytes for `WorkflowDefinitionV1`, interpreter content ID, old event envelopes, expected snapshot/current row and expected logical command/outbox records. Include normal, blocked, cancelled, linked-retry, waived and recovered histories, as required by research ([docs/research/hermes-core-architecture-research-2026-07-27.md:2020](/home/soultransit/devtony/ranex/docs/research/hermes-core-architecture-research-2026-07-27.md:2020)). | Current code verifies original digests, upcasts, reduces without dispatch, and reproduces byte-identical canonical state, journal head, aggregate version, sequence and expected command/outbox records. A second replay is identical. Removing/changing an upcaster, changing interpreter behavior, or mutating command order/payload must fail at the first mismatch. |
| `REPLAY-CORPUS-001` | In CI, replay a representative sample of retained open and closed histories in addition to permanent fixtures, following Temporal’s tested-history practice. | Any replay incompatibility fails CI. |

The frozen fixture must be captured from original persisted bytes, not recreated through current constructors. This addresses the prior report’s independent-oracle finding ([docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6673](/home/soultransit/devtony/ranex/docs/architecture/reviews/artifacts/2026-07-30/agent-reports/priorart-B.md:6673)).

## 7. Accepted-obligation interaction and conflict audit

| Obligation | Interaction |
|---|---|
| `HERMES-PROMOTION-058` | Definition/event/node hashing uses the shared identity and canonical-serialization facilities; no competing serializer is introduced ([ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742)). |
| `-059` | The reducer consumes only normalized current `ReducerEvent` values and remains pure. Upcasting is a separate pure pre-reducer stage ([ADR-0013:752](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:752)). |
| `-060` | The relational current row remains canonical operational state with explicit version; pins are denormalized into it for recovery checks ([ADR-0013:762](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:762)). |
| `-061` | Original event, new state/version and outbox remain one SQLite unit of work. The upcaster never rewrites that journal ([ADR-0013:772](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:772)). |
| `-062` | This schema qualifies compatibility for `Execution` only. It does not authorize event sourcing for another aggregate or activate event sourcing by itself ([ADR-0013:782](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:782)). |
| `-063` | Unknown/missing compatibility blocks fail-closed. Replay does not bypass the policy-enforcement point or dispatch effects ([ADR-0013:792](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:792)). |
| `-064` | Identity, serializer, schema and upcaster APIs remain kernel contracts subject to the pre-feature import tests ([ADR-0013:802](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:802)). |
| `-065` | Frozen replay strengthens, but does not replace, the separately required crash-boundary and no-Hermes-import tests ([ADR-0013:812](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:812)). |
| §8.3 | The ordered journal stays the replay/audit oracle; current row is operational; snapshots are accelerators; mismatch blocks ([docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470](/home/soultransit/devtony/ranex/docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md:470)). |

**INFERENCE — conflict audit:** No conflict was found. In particular, the recommendation does not add fields to the closed `WorkflowPinned` payload, does not replace `DomainEventEnvelopeV1`, does not rewrite history, and does not expand event sourcing beyond `Execution`.

`HERMES-OWNER-DECISION-002` remains separate because runner-versus-durable-runtime selection is a production-readiness decision ([ADR-0013:835](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:835)). `HERMES-OWNER-DECISION-020` also remains separate because only it may activate Execution event sourcing after qualification ([ADR-0013:1051](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1051)).

## 8. Exact owner decision still required

`HERMES-OWNER-DECISION-001` has no default and remains blocking until an accepted ADR exists ([ADR-0013:823](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:823), [ADR-0013:1150](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1150)).

**INFERENCE — remaining choice:** there is no technical selector left inside this recommendation. The genuine owner choice is whether to accept its operational cost and fail-closed behavior as one indivisible compatibility policy.

The question to record is:

> Do you ACCEPT immutable content-addressed `WorkflowDefinitionV1` documents with digest-derived versioned node IDs; exact per-run definition/interpreter/schema pins; unchanged `DomainEventEnvelopeV1`; and deterministic one-to-one read-time upcasting over immutable original event bytes, with failures blocking and frozen-old-history replay as a mandatory acceptance test?

An answer of “yes,” captured in an accepted ADR with the tests above, resolves `HERMES-OWNER-DECISION-001`. An answer of “no” must name a replacement for each of the five elements and explicitly accept the corresponding replay/audit failure modes.

No repository files were modified.
