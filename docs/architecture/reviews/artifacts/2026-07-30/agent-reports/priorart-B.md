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
session id: 019fb2c5-36b3-7583-8275-0e950a874841
--------
user
# Prior-art sweep B — deterministic execution and run visualization

Ranex is a governance harness that runs AI agents under enforced constraints, on
a single host, with SQLite as its transactional authority. The working premise of
this task: **Ranex is not novel. Established standards and production systems
already solve most of what it does.** Find them, and report precisely what Ranex
should adopt, adapt, or deliberately diverge from — and where it truly has no
prior art.

Do not design anything. Find what exists.

## Your assigned layers

1. **Deterministic workflow execution and replay** — how production systems
   guarantee that replaying a recorded history reproduces the same state and the
   same commands, and how they version workflow definitions so old runs stay
   replayable.
2. **Durable state + event journal + outbox in one transaction** — the
   transactional-outbox and event-journal patterns, how real systems avoid
   split-brain between a current-state snapshot and an append-only log, and
   **how they detect or prevent the two disagreeing**.
3. **Crash-boundary and replay testing** — how these systems actually *test*
   crash recovery and replay determinism, as opposed to asserting it. What does a
   credible crash test look like in practice?
4. **Run-graph visualization** — how CI and workflow systems render a live
   execution graph derived from server-side state, including how they transport
   live updates and how they avoid the browser inferring state.

Known starting points, to verify and go beyond rather than accept from me:
Temporal, Cadence, DBOS, Argo Workflows, Apache Airflow, Dagster, Kestra,
GitHub Actions, Netflix Conductor, transactional outbox pattern, event sourcing
with snapshots. Find others, including anything SQLite-specific.

## What Ranex currently does — read it, cite it

- `docs/architecture/decisions/ADR-0013-...md` provisions
  `HERMES-PROMOTION-058` through `HERMES-PROMOTION-065` — the accepted kernel
  obligations, including the one-SQLite-unit-of-work requirement.
- The kernel R&D tracer is in a **separate worktree**:
  `.claude/worktrees/kernel-tracer`, branch `feature/kernel-tracer`, with
  untracked `src/` and `tests/`. Read especially
  `src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py`,
  `src/ranex/governed_execution/domain/execution.py`, its
  `migrations/001_execution_kernel.sql`, and the tests under `tests/replay/` and
  `tests/resilience/`.
- `docs/research/deterministic-run-graph-visualization-research-2026-07-30.md` —
  an existing internal proposal for the run graph. Treat its technology claims as
  claims to verify, not as conclusions.

Two known open defects, given as context you must account for — not as things to
re-find: the journal and the state snapshot can disagree with nothing detecting
it, and the existing replay test compares the production reducer against itself.

## Required output — one row per layer or sub-layer

| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |

`Verdict` is exactly one of **ADOPT**, **ADAPT**, **DIVERGE** (with the reason it
must differ), or **NOVEL** (state what you searched).

`Specific delta` must be actionable. "Look at Temporal" is useless. "Temporal
proves replay determinism by re-executing history against the current definition
and failing on non-determinism, which the test at
`tests/replay/...:59-66` cannot do because both sides consume the same in-memory
events" is useful.

Answer these directly, with citations:
- How do production systems make a snapshot and a journal provably agree?
- What is the accepted way to test crash recovery, concretely?
- Is one-SQLite-unit-of-work a recognized pattern with known limits, or unusual?

## Non-negotiables

- **Verify externally.** Use web search/fetch for every external claim; if those
  tools are unavailable, use `curl`. Cite a URL per claim. Mark anything you
  could not verify as `UNVERIFIED` rather than asserting it. Recalled knowledge
  stated as fact is a failure of this task.
- **Licence check.** For anything recommended for adoption, report its licence
  and whether it is compatible with a source-available, all-rights-reserved
  product preserving future commercial optionality (`LICENSE-RANEX.md`). Flag
  copyleft or commercially encumbered terms — this applies to libraries and to
  any front-end graph library the run-graph proposal names.
- **Read-only.** Do not modify, create, or delete any file in the repository.
- **Report inferences** in a separate section, marked as inference.
- **Maturity matters.** Prefer production systems with named adopters. State the
  adoption evidence.

## Output sections

`Mapping table`, `Adopt shortlist` (ranked, with licence), `Answers to the three
direct questions`, `Genuinely novel`, `Inferences`, `Search coverage`.
codex
I’ll audit the cited Ranex artifacts first, pin every current-state claim to exact lines, then verify each comparison against primary documentation, source repositories, licences, and adopter evidence. I’ll keep the repository strictly read-only and label any unsupported point `UNVERIFIED`.
  → Inspect Ranex ADR, tracer implementation/tests, graph proposal, and licence with exact line references
  • Research deterministic replay/versioning and concrete crash-test practices in primary sources
  • Research atomic state+journal+outbox consistency, including SQLite patterns and limits
  • Research live run-graph state transport/rendering, named adopters, and licences
  • Synthesize mapping table, shortlist, direct answers, novelty, inferences, and search coverage
exec
/bin/bash -lc "pwd && rg --files docs/architecture/decisions docs/research .claude/worktrees/kernel-tracer 2>/dev/null | rg '(ADR-0013|deterministic-run-graph|execution_store\\.py|execution\\.py|001_execution_kernel\\.sql|tests/(replay|resilience)|LICENSE-RANEX)'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
/home/soultransit/devtony/ranex
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py
.claude/worktrees/kernel-tracer/LICENSE-RANEX.md
.claude/worktrees/kernel-tracer/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql

exec
/bin/bash -lc 'nl -ba docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md' in /home/soultransit/devtony/ranex
exec
/bin/bash -lc 'wc -l docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md docs/research/deterministic-run-graph-visualization-research-2026-07-30.md LICENSE-RANEX.md 2>/dev/null || true' in /home/soultransit/devtony/ranex
exec
/bin/bash -lc 'wc -l .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql .claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py .claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
  1187 docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md
   736 docs/research/deterministic-run-graph-visualization-research-2026-07-30.md
    95 LICENSE-RANEX.md
  2018 total

 succeeded in 0ms:
  420 .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py
  237 .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py
   73 .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql
   66 .claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py
   98 .claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py
  894 total

 succeeded in 0ms:
     1	# ADR-0013: Promote Hermes Research Obligations into a Closed Audit Contract
     2	
     3	| Field | Value |
     4	|---|---|
     5	| ADR ID | `ADR-0013` |
     6	| Version | `1.4.0` |
     7	| Status | `ACCEPTED` |
     8	| Decision owner | Human owner |
     9	| Decision date | 2026-07-29 |
    10	| Effective revision | Working tree based on `a66267776c`; executable documentation projection generated and runtime evidence pending |
    11	| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
    12	| Affected contexts | `configuration_management`, `governed_execution`, `policy`, `assurance`, `module_governance`, `compatibility`, `migration`, `provenance_compliance`, `release_management`, and `process_assurance` |
    13	| RFC | Not required; direct owner requirement to make already accepted Hermes-research obligations line-auditable and fail closed |
    14	| Supersedes | No fixed decision; adds a closed, line-bound projection of obligations already accepted through ADR-0003, ADR-0005, ADR-0006, and ADR-0011 |
    15	| Review/expiry date | On any source-research correction, promoted-provision change, owner-choice resolution, or de-commercialization/legal-control change |
    16	| Compatibility/migration class | Additive executable documentation contract; runtime implementation remains unassessed |
    17	| Security/data class | Public architecture decision; legal, credential, package, runtime, and release evidence retain their own classification |
    18	
    19	## Revision history
    20	
    21	### 1.4.0 — 2026-07-30
    22	
    23	This revision repairs one unsupported qualifier found by a post-1.3.0
    24	fidelity audit after three earlier repair rounds had missed it.
    25	
    26	- **DEFECT 9** — `HERMES-PROMOTION-059` claimed that *every* Execution
    27	  state transition is computed by the pure reducer, while the cited
    28	  research line 1902 supports only "Implement an `Execution` aggregate
    29	  and pure reducer." The unsupported `every` qualifier is removed; the
    30	  provision now states that Execution state transitions are computed by
    31	  the aggregate's pure reducer, without a universal-coverage claim the
    32	  research does not make.
    33	
    34	### 1.3.0 — 2026-07-30
    35	
    36	This revision records the second full-row fidelity audit and closes the
    37	remaining unpinned-row blind spot.
    38	
    39	- **DEFECT 6** — `HERMES-PROMOTION-002` now states only that the new
    40	  dependency-clean kernel is built beside Hermes; `HERMES-PROMOTION-004`
    41	  removes the unsupported `only` exclusivity; `HERMES-PROMOTION-009` removes
    42	  the unsupported `replaceable` qualifier; `HERMES-PROMOTION-014` restores
    43	  first-party module access to application/kernel public APIs; and
    44	  `HERMES-PROMOTION-017` uses the cited side-effect-free requirement without
    45	  an invented example list.
    46	- **DEFECT 7** — The 1.2.0 history now records its previously omitted
    47	  normative changes to `HERMES-PROMOTION-058` and
    48	  `HERMES-PROMOTION-059`.
    49	- **DEFECT 8** — Exact-text fidelity pins now cover all 65 promoted
    50	  provisions, all 20 owner-decision subjects, and all 13 research-only
    51	  dispositions. Any paraphrase of a pinned text fails generation and
    52	  validation.
    53	
    54	### 1.2.0 — 2026-07-29
    55	
    56	This revision records the result of placing every promoted provision beside
    57	its cited research excerpt and comparing obligation class, scope, and
    58	specificity.
    59	
    60	- **Previously omitted 1.2.0 normative changes (recorded retroactively in
    61	  1.3.0)** — `HERMES-PROMOTION-058` renamed
    62	  `SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION_DEFINE_KERNEL_RECORDS` to
    63	  `CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION` and
    64	  removed the unsupported `kernel records` scope.
    65	  `HERMES-PROMOTION-059` replaced “whose state evolution is computed by a pure
    66	  reducer without observable side effects” with “every Execution state
    67	  transition is computed by its pure reducer.”
    68	- **DEFECT 1** — `HERMES-PROMOTION-011` again requires removal of the Nous
    69	  commercial subsystem, and `HERMES-PROMOTION-041` again requires removal of
    70	  Hermes/Nous branding. Neither action is represented as an asserted
    71	  absent-state.
    72	- **DEFECT 2** — `HERMES-PROMOTION-040` restores rebranding as the specific
    73	  context that does not authorize erasing legal notices or Git history.
    74	- **DEFECT 3** — `HERMES-PROMOTION-041` restores package metadata, remote
    75	  endpoints, headers, telemetry tags, help text, screenshots, generated
    76	  assets, and defaults as eight separately checkable surfaces. The same
    77	  row-by-row specificity check restores the cited item-level terms in
    78	  `HERMES-PROMOTION-037`, `HERMES-PROMOTION-038`,
    79	  `HERMES-PROMOTION-044`, `HERMES-PROMOTION-045`,
    80	  `HERMES-PROMOTION-050`, `HERMES-PROMOTION-051`,
    81	  `HERMES-PROMOTION-053`, `HERMES-PROMOTION-054`, and
    82	  `HERMES-PROMOTION-057`.
    83	- **DEFECT 4** — `HERMES-PROMOTION-005`, `HERMES-PROMOTION-010`,
    84	  `HERMES-PROMOTION-012`, and `HERMES-PROMOTION-018` remove the unsupported
    85	  `governed`, `accepted`, generalized domain-package, and `authority`
    86	  qualifiers and restore their exact cited scopes.
    87	- **DEFECT 5** — Phase 1 lines 1899–1912 remain represented by
    88	  `HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`, rather than by an
    89	  exclusion-equivalence claim. Phase 0/0A activity and Phase 2–6 sequencing
    90	  and exit material remain research-only and are not represented by promoted
    91	  gates.
    92	
    93	### 1.1.0 — 2026-07-29
    94	
    95	By owner decision, this revision overturns the prior “implementation
    96	sequencing, not fixed authority” exclusion for Phase 1. Research lines
    97	1899–1912 define the clean kernel's binding structural inventory and behavior,
    98	not a delivery schedule.
    99	
   100	This revision adds eight promoted provisions,
   101	`HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`:
   102	
   103	1. shared identity and canonical serialization;
   104	2. the `Execution` aggregate and pure reducer;
   105	3. canonical relational execution state and version;
   106	4. the append-only transition/audit journal and outbox in one SQLite unit of
   107	   work;
   108	5. the evidence-gated, `Execution`-only event-sourcing boundary;
   109	6. the fail-closed application-control PEP, pure domain decisions, and
   110	   deterministic policy adapter;
   111	7. architecture import tests before feature code; and
   112	8. the replay, crash-boundary, and no-Hermes-import exit gate.
   113	
   114	It also adds `HERMES-OWNER-DECISION-020` as an
   115	`OWNER_DECISION_REQUIRED` row for whether qualified `Execution` event sourcing
   116	is activated, narrows `HERMES-RESEARCH-ONLY-008` to Phases 0/0A, and
   117	adds `HERMES-RESEARCH-ONLY-013` for Phases 2–6.
   118	Phase 1 is no longer included in a research-only sequencing disposition.
   119	
   120	### 1.0.0 — 2026-07-29
   121	
   122	Established the initial line-bound Hermes-research promotion catalog,
   123	owner-decision register, and research-only dispositions.
   124	
   125	## Decision
   126	
   127	The Hermes architecture research is advisory evidence, not authority by itself.
   128	This ADR promotes only the closed set below into an accepted documentation
   129	contract. Each promoted provision names one exact research line, one
   130	underscore-only guard, a deterministic check class, and the stage that must
   131	block when the check does not pass.
   132	
   133	The licensing, copyright, provenance, attribution, and history-preservation
   134	provision is an external-obligation boundary. No owner, model, waiver, feature
   135	flag, profile, or passing unrelated check may compensate for it.
   136	
   137	Phase 1 is a binding clean-kernel inventory. Its heading is phased migration
   138	context, but lines 1901–1911 define required parts, required behavior,
   139	construction precedence, and a falsifiable gate. They are not treated as a
   140	calendar, delivery estimate, or optional schedule.
   141	
   142	`OWNER_DECISION_REQUIRED` has one precise meaning here: the choice is registered
   143	but not selected by this ADR. Its `owner_decision_ref` and `default` remain
   144	null, absence yields `BLOCK`, and activation without the exact accepted
   145	decision is `DENIED`. The documentation-contract validator passes when that
   146	fail-closed definition is intact; it does not convert an unresolved owner
   147	choice into a runtime or release pass.
   148	
   149	Later architecture material may discuss the same subject, but topical overlap
   150	is not treated as an exact owner-decision binding. Satisfying one of these rows
   151	requires a catalog revision that names the accepted decision and its
   152	predeclared acceptance test; until then the reference remains null and the
   153	named stage blocks.
   154	
   155	The following YAML block is the one canonical source for the generated
   156	promotion registry. The compiler and validator require the exact denominators,
   157	field sets, source lines, source-excerpt digests, guard syntax, guard
   158	uniqueness, and fail-closed outcomes. Runtime evidence begins
   159	`NOT_ASSESSED`.
   160	
   161	```yaml
   162	schema_version: "hermes-research-promotion-catalog/v1"
   163	catalog_id: "RANEX-HERMES-RESEARCH-PROMOTIONS"
   164	catalog_version: "1.4.0"
   165	catalog_status: "DEFINITION_ONLY"
   166	governing_adr: "ADR-0013"
   167	research_source: "docs/research/hermes-core-architecture-research-2026-07-27.md"
   168	promoted_provision_count: 65
   169	owner_decision_count: 20
   170	research_only_count: 13
   171	promoted_provisions:
   172	  - provision_id: "HERMES-PROMOTION-001"
   173	    status: "PROMOTED"
   174	    guard_id: "GOVERNED_EXECUTION_IS_CORE_DOMAIN"
   175	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2264"
   176	    source_end_line: 2265
   177	    check_class: "ARCHITECTURE_CONTRACT"
   178	    blocking_stage: "IMPLEMENTATION_START"
   179	    provision: "Ranex defines its core domain as governed deterministic execution rather than the agent loop."
   180	    required_result: "PASS"
   181	    failure_outcome: "BLOCK"
   182	  - provision_id: "HERMES-PROMOTION-002"
   183	    status: "PROMOTED"
   184	    guard_id: "DEPENDENCY_CLEAN_KERNEL_EXISTS_BESIDE_HERMES"
   185	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2266"
   186	    source_end_line: 2266
   187	    check_class: "ARCHITECTURE_CONTRACT"
   188	    blocking_stage: "IMPLEMENTATION_START"
   189	    provision: "A new dependency-clean kernel is built beside Hermes."
   190	    required_result: "PASS"
   191	    failure_outcome: "BLOCK"
   192	  - provision_id: "HERMES-PROMOTION-003"
   193	    status: "PROMOTED"
   194	    guard_id: "WORKFLOW_REDUCER_IS_KERNEL_RESPONSIBILITY"
   195	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2267"
   196	    source_end_line: 2268
   197	    check_class: "ARCHITECTURE_CONTRACT"
   198	    blocking_stage: "IMPLEMENTATION_START"
   199	    provision: "Workflow semantics and the execution reducer are first-class kernel responsibilities."
   200	    required_result: "PASS"
   201	    failure_outcome: "BLOCK"
   202	  - provision_id: "HERMES-PROMOTION-004"
   203	    status: "PROMOTED"
   204	    guard_id: "HERMES_IS_REPLACEABLE_PROPOSAL_DRIVER"
   205	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2269"
   206	    source_end_line: 2270
   207	    check_class: "RUNTIME_FITNESS"
   208	    blocking_stage: "PRODUCTION_READY"
   209	    provision: "Hermes is contained as a replaceable worker and evolves into a typed action-proposal driver."
   210	    required_result: "PASS"
   211	    failure_outcome: "BLOCK"
   212	  - provision_id: "HERMES-PROMOTION-005"
   213	    status: "PROMOTED"
   214	    guard_id: "FAIL_CLOSED_CAPABILITY_BUS_MEDIATES_EVERY_EFFECT"
   215	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2271"
   216	    source_end_line: 2271
   217	    check_class: "AUTHORITY_FITNESS"
   218	    blocking_stage: "EFFECT_DISPATCH"
   219	    provision: "One fail-closed capability bus mediates every effect."
   220	    required_result: "PASS"
   221	    failure_outcome: "BLOCK"
   222	  - provision_id: "HERMES-PROMOTION-006"
   223	    status: "PROMOTED"
   224	    guard_id: "AUTHORITY_EVIDENCE_PERMITS_MODULES_AND_ATOMIC_STATE_ARE_KERNEL_OWNED"
   225	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2272"
   226	    source_end_line: 2273
   227	    check_class: "ARCHITECTURE_CONTRACT"
   228	    blocking_stage: "IMPLEMENTATION_START"
   229	    provision: "Policy enforcement, evidence and gate semantics, permit authority, module governance, and atomic event/outbox state remain kernel-owned."
   230	    required_result: "PASS"
   231	    failure_outcome: "BLOCK"
   232	  - provision_id: "HERMES-PROMOTION-007"
   233	    status: "PROMOTED"
   234	    guard_id: "REQUIRED_CAPABILITIES_ARE_QUALIFIED_FIRST_PARTY_MODULES"
   235	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2274"
   236	    source_end_line: 2275
   237	    check_class: "MODULE_FITNESS"
   238	    blocking_stage: "MODULE_ACTIVATION"
   239	    provision: "Required capabilities ship as qualified first-party modules in one product release."
   240	    required_result: "PASS"
   241	    failure_outcome: "BLOCK"
   242	  - provision_id: "HERMES-PROMOTION-008"
   243	    status: "PROMOTED"
   244	    guard_id: "LEGACY_PLUGINS_STAY_BEHIND_CONSTRAINED_COMPATIBILITY"
   245	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2276"
   246	    source_end_line: 2276
   247	    check_class: "MODULE_FITNESS"
   248	    blocking_stage: "MODULE_ACTIVATION"
   249	    provision: "Legacy Hermes plugins execute only behind a constrained compatibility boundary."
   250	    required_result: "PASS"
   251	    failure_outcome: "BLOCK"
   252	  - provision_id: "HERMES-PROMOTION-009"
   253	    status: "PROMOTED"
   254	    guard_id: "LOCAL_TRACER_RETAINS_WORKFLOW_RUNTIME_PORT"
   255	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2277"
   256	    source_end_line: 2277
   257	    check_class: "ARCHITECTURE_CONTRACT"
   258	    blocking_stage: "IMPLEMENTATION_START"
   259	    provision: "Ranex starts with a small SQLite-backed tracer and retains a workflow-runtime port."
   260	    required_result: "PASS"
   261	    failure_outcome: "BLOCK"
   262	  - provision_id: "HERMES-PROMOTION-010"
   263	    status: "PROMOTED"
   264	    guard_id: "IMPORT_AND_RUNTIME_FITNESS_TESTS_ENFORCE_ARCHITECTURE"
   265	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2278"
   266	    source_end_line: 2278
   267	    check_class: "STATIC_FITNESS"
   268	    blocking_stage: "IMPLEMENTATION_START"
   269	    provision: "Import and runtime fitness tests enforce the architecture."
   270	    required_result: "PASS"
   271	    failure_outcome: "BLOCK"
   272	  - provision_id: "HERMES-PROMOTION-011"
   273	    status: "PROMOTED"
   274	    guard_id: "NOUS_COMMERCIAL_SUBSYSTEM_ABSENT_PROVIDER_NEUTRAL_COST_RETAINED"
   275	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2279"
   276	    source_end_line: 2281
   277	    check_class: "RELEASE_FITNESS"
   278	    blocking_stage: "RELEASE"
   279	    provision: "Remove the Nous commercial model provider and all account, credit, subscription, payment, entitlement, Portal, and promotional infrastructure; retain only provider-neutral cost and budget measurement."
   280	    required_result: "PASS"
   281	    failure_outcome: "BLOCK"
   282	  - provision_id: "HERMES-PROMOTION-012"
   283	    status: "PROMOTED"
   284	    guard_id: "DOMAIN_IMPORTS_EXCLUDE_TECHNICAL_AND_HERMES_PACKAGES"
   285	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1811"
   286	    source_end_line: 1812
   287	    check_class: "STATIC_FITNESS"
   288	    blocking_stage: "IMPLEMENTATION_START"
   289	    provision: "`ranex.*.domain` cannot import Hermes, CLI, gateway, database, provider, filesystem, HTTP, or tool packages."
   290	    required_result: "PASS"
   291	    failure_outcome: "BLOCK"
   292	  - provision_id: "HERMES-PROMOTION-013"
   293	    status: "PROMOTED"
   294	    guard_id: "CROSS_CONTEXT_IMPORTS_USE_PUBLIC_API_ONLY"
   295	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1813"
   296	    source_end_line: 1813
   297	    check_class: "STATIC_FITNESS"
   298	    blocking_stage: "IMPLEMENTATION_START"
   299	    provision: "A bounded context imports another context only through its public API."
   300	    required_result: "PASS"
   301	    failure_outcome: "BLOCK"
   302	  - provision_id: "HERMES-PROMOTION-014"
   303	    status: "PROMOTED"
   304	    guard_id: "KERNEL_NEVER_DEPENDS_ON_FIRST_PARTY_MODULES"
   305	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1814"
   306	    source_end_line: 1815
   307	    check_class: "STATIC_FITNESS"
   308	    blocking_stage: "IMPLEMENTATION_START"
   309	    provision: "First-party modules may depend on application/kernel public APIs, but the kernel cannot depend on modules."
   310	    required_result: "PASS"
   311	    failure_outcome: "BLOCK"
   312	  - provision_id: "HERMES-PROMOTION-015"
   313	    status: "PROMOTED"
   314	    guard_id: "ADAPTERS_ARE_CONSTRUCTED_ONLY_AT_COMPOSITION_ROOT"
   315	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1816"
   316	    source_end_line: 1817
   317	    check_class: "STATIC_FITNESS"
   318	    blocking_stage: "IMPLEMENTATION_START"
   319	    provision: "Domain and application code do not import adapters; the composition root alone constructs them."
   320	    required_result: "PASS"
   321	    failure_outcome: "BLOCK"
   322	  - provision_id: "HERMES-PROMOTION-016"
   323	    status: "PROMOTED"
   324	    guard_id: "MODULE_DEPENDENCY_GRAPH_IS_ACYCLIC_AND_MANIFEST_BOUND"
   325	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1818"
   326	    source_end_line: 1818
   327	    check_class: "STATIC_FITNESS"
   328	    blocking_stage: "IMPLEMENTATION_START"
   329	    provision: "The module dependency graph is acyclic and equals a checked-in manifest."
   330	    required_result: "PASS"
   331	    failure_outcome: "BLOCK"
   332	  - provision_id: "HERMES-PROMOTION-017"
   333	    status: "PROMOTED"
   334	    guard_id: "MODULE_IMPORT_HAS_NO_SIDE_EFFECT"
   335	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1819"
   336	    source_end_line: 1819
   337	    check_class: "STATIC_FITNESS"
   338	    blocking_stage: "IMPLEMENTATION_START"
   339	    provision: "Importing any module is side-effect free."
   340	    required_result: "PASS"
   341	    failure_outcome: "BLOCK"
   342	  - provision_id: "HERMES-PROMOTION-018"
   343	    status: "PROMOTED"
   344	    guard_id: "CANONICAL_WRITES_OCCUR_ONLY_IN_AUTHORITY_UNIT_OF_WORK"
   345	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1820"
   346	    source_end_line: 1820
   347	    check_class: "AUTHORITY_FITNESS"
   348	    blocking_stage: "EFFECT_DISPATCH"
   349	    provision: "No direct canonical-state writes occur outside the unit of work."
   350	    required_result: "PASS"
   351	    failure_outcome: "BLOCK"
   352	  - provision_id: "HERMES-PROMOTION-019"
   353	    status: "PROMOTED"
   354	    guard_id: "EFFECT_REQUIRES_GRANT_AND_RECORDED_ACTIVITY_IDENTITY"
   355	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1821"
   356	    source_end_line: 1822
   357	    check_class: "AUTHORITY_FITNESS"
   358	    blocking_stage: "EFFECT_DISPATCH"
   359	    provision: "No external effect occurs without a capability grant and recorded activity identity."
   360	    required_result: "PASS"
   361	    failure_outcome: "BLOCK"
   362	  - provision_id: "HERMES-PROMOTION-020"
   363	    status: "PROMOTED"
   364	    guard_id: "MODULE_CATALOG_CANNOT_OVERRIDE_PERMIT_ISSUER_OR_POLICY_PEP"
   365	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1823"
   366	    source_end_line: 1823
   367	    check_class: "AUTHORITY_FITNESS"
   368	    blocking_stage: "MODULE_ACTIVATION"
   369	    provision: "The module catalog cannot override a permit issuer or policy enforcement point."
   370	    required_result: "PASS"
   371	    failure_outcome: "BLOCK"
   372	  - provision_id: "HERMES-PROMOTION-021"
   373	    status: "PROMOTED"
   374	    guard_id: "INELIGIBLE_MODULE_CANNOT_REGISTER_MIGRATE_RECEIVE_TRAFFIC_OR_EFFECT"
   375	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1824"
   376	    source_end_line: 1825
   377	    check_class: "MODULE_FITNESS"
   378	    blocking_stage: "MODULE_ACTIVATION"
   379	    provision: "A disabled, incompatible, unqualified, or quarantined module cannot register, migrate, receive traffic, or perform an effect."
   380	    required_result: "PASS"
   381	    failure_outcome: "BLOCK"
   382	  - provision_id: "HERMES-PROMOTION-022"
   383	    status: "PROMOTED"
   384	    guard_id: "EXECUTION_KERNEL_ALONE_SELECTS_CANONICAL_NEXT_STATE"
   385	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1839"
   386	    source_end_line: 1839
   387	    check_class: "AUTHORITY_FITNESS"
   388	    blocking_stage: "PRODUCTION_READY"
   389	    provision: "Only the execution kernel chooses a legal next canonical state."
   390	    required_result: "PASS"
   391	    failure_outcome: "BLOCK"
   392	  - provision_id: "HERMES-PROMOTION-023"
   393	    status: "PROMOTED"
   394	    guard_id: "NONREPLACEABLE_PEP_ALONE_AUTHORIZES_AND_DISPATCHES_EFFECTS"
   395	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1840"
   396	    source_end_line: 1841
   397	    check_class: "AUTHORITY_FITNESS"
   398	    blocking_stage: "EFFECT_DISPATCH"
   399	    provision: "Only nonreplaceable application control authorizes and dispatches capabilities and effects using domain authorization decisions."
   400	    required_result: "PASS"
   401	    failure_outcome: "BLOCK"
   402	  - provision_id: "HERMES-PROMOTION-024"
   403	    status: "PROMOTED"
   404	    guard_id: "EVERY_EFFECT_IS_COMPLETELY_MEDIATED"
   405	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1842"
   406	    source_end_line: 1842
   407	    check_class: "RUNTIME_FITNESS"
   408	    blocking_stage: "PRODUCTION_READY"
   409	    provision: "Every target-mode effect is completely mediated and no special agent-tool bypass exists."
   410	    required_result: "PASS"
   411	    failure_outcome: "BLOCK"
   412	  - provision_id: "HERMES-PROMOTION-025"
   413	    status: "PROMOTED"
   414	    guard_id: "POLICY_OR_CHECKER_FAILURE_DENIES_BLOCKING_ACTION"
   415	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1843"
   416	    source_end_line: 1843
   417	    check_class: "AUTHORITY_FITNESS"
   418	    blocking_stage: "GATE_ADVANCE"
   419	    provision: "Policy or checker unavailability and error deny a blocking action."
   420	    required_result: "PASS"
   421	    failure_outcome: "BLOCK"
   422	  - provision_id: "HERMES-PROMOTION-026"
   423	    status: "PROMOTED"
   424	    guard_id: "MAKER_CANNOT_APPROVE_OWN_SUBJECT"
   425	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1844"
   426	    source_end_line: 1844
   427	    check_class: "AUTHORITY_FITNESS"
   428	    blocking_stage: "GATE_ADVANCE"
   429	    provision: "A maker cannot approve its own subject."
   430	    required_result: "PASS"
   431	    failure_outcome: "BLOCK"
   432	  - provision_id: "HERMES-PROMOTION-027"
   433	    status: "PROMOTED"
   434	    guard_id: "EVIDENCE_AND_APPROVAL_BIND_EXACT_EXECUTION_SUBJECT"
   435	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1845"
   436	    source_end_line: 1846
   437	    check_class: "EVIDENCE_FITNESS"
   438	    blocking_stage: "GATE_ADVANCE"
   439	    provision: "Evidence and approval bind the exact project, run, packet, commits, workflow version, and policy activation."
   440	    required_result: "PASS"
   441	    failure_outcome: "BLOCK"
   442	  - provision_id: "HERMES-PROMOTION-028"
   443	    status: "PROMOTED"
   444	    guard_id: "PERMIT_IS_SINGLE_USE_SCOPED_EXPIRING_AND_CHANGE_INVALIDATED"
   445	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1847"
   446	    source_end_line: 1848
   447	    check_class: "AUTHORITY_FITNESS"
   448	    blocking_stage: "EFFECT_DISPATCH"
   449	    provision: "An approval or permit is single-use, scoped, expiring, and invalidated by material change."
   450	    required_result: "PASS"
   451	    failure_outcome: "BLOCK"
   452	  - provision_id: "HERMES-PROMOTION-029"
   453	    status: "PROMOTED"
   454	    guard_id: "STATE_AUDIT_PERMIT_AND_OUTBOX_COMMIT_ATOMICALLY"
   455	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1849"
   456	    source_end_line: 1850
   457	    check_class: "RUNTIME_FITNESS"
   458	    blocking_stage: "PRODUCTION_READY"
   459	    provision: "Canonical state and version, audit or domain record, permit consumption, and outbox intent commit atomically."
   460	    required_result: "PASS"
   461	    failure_outcome: "BLOCK"
   462	  - provision_id: "HERMES-PROMOTION-030"
   463	    status: "PROMOTED"
   464	    guard_id: "RETRY_REUSES_LOGICAL_IDEMPOTENCY_IDENTITY"
   465	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1851"
   466	    source_end_line: 1851
   467	    check_class: "RUNTIME_FITNESS"
   468	    blocking_stage: "PRODUCTION_READY"
   469	    provision: "Every retry uses the same logical idempotency identity."
   470	    required_result: "PASS"
   471	    failure_outcome: "BLOCK"
   472	  - provision_id: "HERMES-PROMOTION-031"
   473	    status: "PROMOTED"
   474	    guard_id: "REDUCER_HAS_NO_HIDDEN_NONDETERMINISM"
   475	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1852"
   476	    source_end_line: 1852
   477	    check_class: "RUNTIME_FITNESS"
   478	    blocking_stage: "PRODUCTION_READY"
   479	    provision: "The reducer has no hidden nondeterministic dependency."
   480	    required_result: "PASS"
   481	    failure_outcome: "BLOCK"
   482	  - provision_id: "HERMES-PROMOTION-032"
   483	    status: "PROMOTED"
   484	    guard_id: "REPLAY_IS_DETERMINISTIC_FOR_PINNED_DEFINITION_VERSION_AND_HISTORY"
   485	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1853"
   486	    source_end_line: 1854
   487	    check_class: "RUNTIME_FITNESS"
   488	    blocking_stage: "PRODUCTION_READY"
   489	    provision: "Replay of the same definition, version, and history yields the same state and commands."
   490	    required_result: "PASS"
   491	    failure_outcome: "BLOCK"
   492	  - provision_id: "HERMES-PROMOTION-033"
   493	    status: "PROMOTED"
   494	    guard_id: "HISTORY_REMAINS_EXPLAINABLE_AND_NEW_EFFECTS_USE_FRESH_AUTHORITY"
   495	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1855"
   496	    source_end_line: 1855
   497	    check_class: "AUTHORITY_FITNESS"
   498	    blocking_stage: "EFFECT_DISPATCH"
   499	    provision: "Historical decisions remain explainable and new effects use fresh authority."
   500	    required_result: "PASS"
   501	    failure_outcome: "BLOCK"
   502	  - provision_id: "HERMES-PROMOTION-034"
   503	    status: "PROMOTED"
   504	    guard_id: "MODULE_CANNOT_WRITE_CANONICAL_STATE_OR_SELF_GRANT"
   505	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1856"
   506	    source_end_line: 1856
   507	    check_class: "AUTHORITY_FITNESS"
   508	    blocking_stage: "MODULE_ACTIVATION"
   509	    provision: "Module code cannot write canonical state or grant itself capability."
   510	    required_result: "PASS"
   511	    failure_outcome: "BLOCK"
   512	  - provision_id: "HERMES-PROMOTION-035"
   513	    status: "PROMOTED"
   514	    guard_id: "PLUGIN_FAILURE_CANNOT_WEAKEN_GATE"
   515	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1857"
   516	    source_end_line: 1857
   517	    check_class: "MODULE_FITNESS"
   518	    blocking_stage: "GATE_ADVANCE"
   519	    provision: "External plugin failure cannot weaken a gate."
   520	    required_result: "PASS"
   521	    failure_outcome: "BLOCK"
   522	  - provision_id: "HERMES-PROMOTION-036"
   523	    status: "PROMOTED"
   524	    guard_id: "HUMAN_WAIVER_NEVER_BECOMES_MACHINE_PASS"
   525	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1858"
   526	    source_end_line: 1858
   527	    check_class: "EVIDENCE_FITNESS"
   528	    blocking_stage: "GATE_ADVANCE"
   529	    provision: "A human waiver remains visible as a waiver and never becomes machine PASS."
   530	    required_result: "PASS"
   531	    failure_outcome: "BLOCK"
   532	  - provision_id: "HERMES-PROMOTION-037"
   533	    status: "PROMOTED"
   534	    guard_id: "LEGACY_COMMERCIAL_READER_IS_OFFLINE_AND_NONACTIVATING"
   535	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1604"
   536	    source_end_line: 1607
   537	    check_class: "MIGRATION_FITNESS"
   538	    blocking_stage: "MIGRATION"
   539	    provision: "Any legacy migration reader must be standalone and time-bounded, may recognize old Nous provider/account fields only to warn, redact, or translate a user to an explicit BYOK provider, must not be imported by normal startup, and cannot refresh a token or contact a Portal."
   540	    required_result: "PASS"
   541	    failure_outcome: "BLOCK"
   542	  - provision_id: "HERMES-PROMOTION-038"
   543	    status: "PROMOTED"
   544	    guard_id: "LEGACY_NOUS_AUTH_IS_QUARANTINED_AND_NEVER_SILENTLY_TRANSFERRED"
   545	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1608"
   546	    source_end_line: 1613
   547	    check_class: "MIGRATION_FITNESS"
   548	    blocking_stage: "MIGRATION"
   549	    provision: "Legacy `$HERMES_HOME/auth.json` entries (`providers.nous`, `credential_pool.nous`, `active_provider=\"nous\"`), shared `nous_auth.json`, and model/recommendation caches remain quarantined metadata. The reader reports “unsupported legacy provider,” offers explicit secret deletion, requires a new provider selection, and never silently moves an OAuth token into Ranex."
   550	    required_result: "PASS"
   551	    failure_outcome: "BLOCK"
   552	  - provision_id: "HERMES-PROMOTION-039"
   553	    status: "PROMOTED"
   554	    guard_id: "COMMERCIAL_ACCOUNT_AND_PAYMENT_DATA_IS_NEVER_MIGRATED"
   555	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1614"
   556	    source_end_line: 1615
   557	    check_class: "MIGRATION_FITNESS"
   558	    blocking_stage: "MIGRATION"
   559	    provision: "Payment methods, subscriptions, balances, entitlements, and billing authorization data are never copied into Ranex."
   560	    required_result: "PASS"
   561	    failure_outcome: "BLOCK"
   562	  - provision_id: "HERMES-PROMOTION-040"
   563	    status: "PROMOTED"
   564	    guard_id: "LICENSE_COPYRIGHT_PROVENANCE_ATTRIBUTION_AND_HISTORY_ARE_PRESERVED"
   565	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1616"
   566	    source_end_line: 1617
   567	    check_class: "LEGAL_COMPLIANCE_FITNESS"
   568	    blocking_stage: "RELEASE"
   569	    provision: "Preserve license, copyright, provenance, and required upstream attribution. Rebranding does not authorize erasing legal notices or Git history."
   570	    required_result: "PASS"
   571	    failure_outcome: "BLOCK"
   572	  - provision_id: "HERMES-PROMOTION-041"
   573	    status: "PROMOTED"
   574	    guard_id: "PRODUCT_SURFACES_ARE_REBRANDED_WITH_LEGAL_AND_RESEARCH_EXCEPTIONS"
   575	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1618"
   576	    source_end_line: 1621
   577	    check_class: "RELEASE_FITNESS"
   578	    blocking_stage: "RELEASE"
   579	    provision: "Remove Hermes/Nous branding from all Ranex product surfaces and, as separately checkable items, from package metadata; remote endpoints; headers; telemetry tags; help text; screenshots; generated assets; and defaults. Historical research citations and legally required attribution are exceptions."
   580	    required_result: "PASS"
   581	    failure_outcome: "BLOCK"
   582	  - provision_id: "HERMES-PROMOTION-042"
   583	    status: "PROMOTED"
   584	    guard_id: "CLEAN_HOST_MAKES_NO_NOUS_NETWORK_REQUEST"
   585	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1670"
   586	    source_end_line: 1671
   587	    check_class: "RELEASE_FITNESS"
   588	    blocking_stage: "RELEASE"
   589	    provision: "A clean-host Ranex run makes no DNS or HTTP request to a Nous, Portal, or Nous inference host."
   590	    required_result: "PASS"
   591	    failure_outcome: "BLOCK"
   592	  - provision_id: "HERMES-PROMOTION-043"
   593	    status: "PROMOTED"
   594	    guard_id: "NOUS_IDENTIFIERS_DO_NOT_RESOLVE_AS_RUNTIME_PROVIDER_OR_CATALOG_OWNER"
   595	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1672"
   596	    source_end_line: 1673
   597	    check_class: "RELEASE_FITNESS"
   598	    blocking_stage: "RELEASE"
   599	    provision: "nous, nous-portal, and nousresearch do not resolve as a runtime provider or model-catalog owner."
   600	    required_result: "PASS"
   601	    failure_outcome: "BLOCK"
   602	  - provision_id: "HERMES-PROMOTION-044"
   603	    status: "PROMOTED"
   604	    guard_id: "COMMERCIAL_COMMANDS_RPCS_SCHEMAS_AND_PROXY_ROUTES_ARE_UNREGISTERED"
   605	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1674"
   606	    source_end_line: 1675
   607	    check_class: "RELEASE_FITNESS"
   608	    blocking_stage: "RELEASE"
   609	    provision: "`/topup` and `/subscription` commands, billing and subscription RPCs, checkout, card, and auto-reload schemas, and Portal proxy routes are unregistered."
   610	    required_result: "PASS"
   611	    failure_outcome: "BLOCK"
   612	  - provision_id: "HERMES-PROMOTION-045"
   613	    status: "PROMOTED"
   614	    guard_id: "RUNTIME_PACKAGES_EXCLUDE_NOUS_CREDIT_OAUTH_ENTITLEMENT_AND_PRODUCT_TAGS"
   615	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1676"
   616	    source_end_line: 1678
   617	    check_class: "RELEASE_FITNESS"
   618	    blocking_stage: "RELEASE"
   619	    provision: "Runtime packages exclude `x-nous-credits-*`, `billing:manage`, `providers.nous`, Portal OAuth scopes, managed tool-pool entitlement, and `product=hermes-agent` request tags."
   620	    required_result: "PASS"
   621	    failure_outcome: "BLOCK"
   622	  - provision_id: "HERMES-PROMOTION-046"
   623	    status: "PROMOTED"
   624	    guard_id: "REMOTE_CATALOG_CANNOT_ADD_OR_ACTIVATE_UNPINNED_MODEL"
   625	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1679"
   626	    source_end_line: 1680
   627	    check_class: "RELEASE_FITNESS"
   628	    blocking_stage: "RELEASE"
   629	    provision: "A remote model catalog cannot introduce or activate a model outside the release-pinned Ranex catalog and qualification record."
   630	    required_result: "PASS"
   631	    failure_outcome: "BLOCK"
   632	  - provision_id: "HERMES-PROMOTION-047"
   633	    status: "PROMOTED"
   634	    guard_id: "CANONICAL_DATA_AND_BACKUPS_EXCLUDE_COMMERCIAL_AND_NOUS_AUTH_STATE"
   635	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1681"
   636	    source_end_line: 1682
   637	    check_class: "RELEASE_FITNESS"
   638	    blocking_stage: "RELEASE"
   639	    provision: "Sessions, canonical databases, exports, and backups contain no payment method, subscription, commercial balance, Portal entitlement, or Nous auth token."
   640	    required_result: "PASS"
   641	    failure_outcome: "BLOCK"
   642	  - provision_id: "HERMES-PROMOTION-048"
   643	    status: "PROMOTED"
   644	    guard_id: "DISTRIBUTION_AND_SBOM_EXCLUDE_COMMERCIAL_IMPLEMENTATION"
   645	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1683"
   646	    source_end_line: 1685
   647	    check_class: "SUPPLY_CHAIN_FITNESS"
   648	    blocking_stage: "RELEASE"
   649	    provision: "The wheel, container, and SBOM exclude dedicated billing UI, purchase clients, Nous provider plugins, generated billing bundles, and monetization-only dependencies."
   650	    required_result: "PASS"
   651	    failure_outcome: "BLOCK"
   652	  - provision_id: "HERMES-PROMOTION-049"
   653	    status: "PROMOTED"
   654	    guard_id: "ROUTE_CENSUS_FINDS_NO_REACTIVATION_PATH"
   655	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1686"
   656	    source_end_line: 1688
   657	    check_class: "RELEASE_FITNESS"
   658	    blocking_stage: "RELEASE"
   659	    provision: "Static and runtime route-census tests find no hidden import, command, hook, RPC, environment variable, URL, or feature flag that can reactivate the commercial subsystem."
   660	    required_result: "PASS"
   661	    failure_outcome: "BLOCK"
   662	  - provision_id: "HERMES-PROMOTION-050"
   663	    status: "PROMOTED"
   664	    guard_id: "MISSING_DIRECT_TOOL_CREDENTIAL_NEVER_FALLS_BACK_TO_NOUS_GATEWAY"
   665	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1689"
   666	    source_end_line: 1691
   667	    check_class: "RUNTIME_FITNESS"
   668	    blocking_stage: "EFFECT_DISPATCH"
   669	    provision: "A configured tool without direct credentials becomes unavailable and never attempts a Nous managed gateway or checks a commercial subscription."
   670	    required_result: "PASS"
   671	    failure_outcome: "BLOCK"
   672	  - provision_id: "HERMES-PROMOTION-051"
   673	    status: "PROMOTED"
   674	    guard_id: "MODEL_FAILURE_NEVER_FALLS_BACK_TO_NOUS"
   675	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1692"
   676	    source_end_line: 1693
   677	    check_class: "RUNTIME_FITNESS"
   678	    blocking_stage: "EFFECT_DISPATCH"
   679	    provision: "An auxiliary or model fallback never selects Nous when the configured provider is missing or fails; missing configuration fails closed."
   680	    required_result: "PASS"
   681	    failure_outcome: "BLOCK"
   682	  - provision_id: "HERMES-PROMOTION-052"
   683	    status: "PROMOTED"
   684	    guard_id: "LEGACY_AUTH_LOAD_HAS_NO_LOGIN_REFRESH_KEY_MINT_OR_NETWORK_EFFECT"
   685	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1694"
   686	    source_end_line: 1695
   687	    check_class: "MIGRATION_FITNESS"
   688	    blocking_stage: "MIGRATION"
   689	    provision: "Legacy auth and config loading remains quarantined and cannot load a token, refresh credentials, log in, mint a key, or send network traffic."
   690	    required_result: "PASS"
   691	    failure_outcome: "BLOCK"
   692	  - provision_id: "HERMES-PROMOTION-053"
   693	    status: "PROMOTED"
   694	    guard_id: "FUZZED_NOUS_HEADERS_HAVE_NO_STATE_OR_POLICY_EFFECT"
   695	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1696"
   696	    source_end_line: 1697
   697	    check_class: "RUNTIME_FITNESS"
   698	    blocking_stage: "PRODUCTION_READY"
   699	    provision: "Fuzzed `x-nous-*` headers cannot create state, notices, prompt content, tier selection, or tool gating."
   700	    required_result: "PASS"
   701	    failure_outcome: "BLOCK"
   702	  - provision_id: "HERMES-PROMOTION-054"
   703	    status: "PROMOTED"
   704	    guard_id: "BUILT_ARTIFACTS_EXCLUDE_COMMERCIAL_FILES_BUNDLES_PLUGINS_AND_UI_PACKAGE"
   705	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1698"
   706	    source_end_line: 1699
   707	    check_class: "SUPPLY_CHAIN_FITNESS"
   708	    blocking_stage: "RELEASE"
   709	    provision: "Built wheel, npm bundle, and container scans find no dedicated commercial file, generated billing bundle, provider plugin, or `@nous-research/ui` package."
   710	    required_result: "PASS"
   711	    failure_outcome: "BLOCK"
   712	  - provision_id: "HERMES-PROMOTION-055"
   713	    status: "PROMOTED"
   714	    guard_id: "PROVIDER_NEUTRAL_COST_AND_BUDGET_TELEMETRY_SURVIVES_REMOVAL"
   715	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1700"
   716	    source_end_line: 1701
   717	    check_class: "RUNTIME_FITNESS"
   718	    blocking_stage: "PRODUCTION_READY"
   719	    provision: "Provider-neutral token, cost, and budget telemetry continues to work after commercial deletion."
   720	    required_result: "PASS"
   721	    failure_outcome: "BLOCK"
   722	  - provision_id: "HERMES-PROMOTION-056"
   723	    status: "PROMOTED"
   724	    guard_id: "LICENSE_AND_ATTRIBUTION_VERIFICATION_PASSES"
   725	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1702"
   726	    source_end_line: 1702
   727	    check_class: "LEGAL_COMPLIANCE_FITNESS"
   728	    blocking_stage: "RELEASE"
   729	    provision: "License and attribution verification passes."
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
   856	    default: null
   857	    absence_outcome: "BLOCK"
   858	    activation_without_decision: "DENIED"
   859	  - provision_id: "HERMES-OWNER-DECISION-004"
   860	    status: "OWNER_DECISION_REQUIRED"
   861	    guard_id: "OWNER_DECIDES_ATLAS_COVERAGE_AND_UNKNOWN_BOUNDARY"
   862	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2130"
   863	    source_end_line: 2130
   864	    blocking_stage: "MODULE_ACTIVATION"
   865	    decision_subject: "Atlas supported-language coverage and the conditions that produce UNKNOWN."
   866	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   867	    owner_decision_ref: null
   868	    default: null
   869	    absence_outcome: "BLOCK"
   870	    activation_without_decision: "DENIED"
   871	  - provision_id: "HERMES-OWNER-DECISION-005"
   872	    status: "OWNER_DECISION_REQUIRED"
   873	    guard_id: "OWNER_DECIDES_PARALLELISM_MAP_AND_COMPENSATION_SEMANTICS"
   874	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2131"
   875	    source_end_line: 2131
   876	    blocking_stage: "MODULE_ACTIVATION"
   877	    decision_subject: "Dynamic parallelism, map or fan-out, and compensation semantics."
   878	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   879	    owner_decision_ref: null
   880	    default: null
   881	    absence_outcome: "BLOCK"
   882	    activation_without_decision: "DENIED"
   883	  - provision_id: "HERMES-OWNER-DECISION-006"
   884	    status: "OWNER_DECISION_REQUIRED"
   885	    guard_id: "OWNER_DECIDES_HOT_ACTIVATION_DURING_ACTIVE_EXECUTIONS"
   886	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2132"
   887	    source_end_line: 2132
   888	    blocking_stage: "MODULE_ACTIVATION"
   889	    decision_subject: "Whether and how hot module activation is allowed while executions are running."
   890	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   891	    owner_decision_ref: null
   892	    default: null
   893	    absence_outcome: "BLOCK"
   894	    activation_without_decision: "DENIED"
   895	  - provision_id: "HERMES-OWNER-DECISION-007"
   896	    status: "OWNER_DECISION_REQUIRED"
   897	    guard_id: "OWNER_DECIDES_ACTIVE_MODULE_STATE_MIGRATION_AND_ROLLBACK"
   898	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2133"
   899	    source_end_line: 2133
   900	    blocking_stage: "MIGRATION"
   901	    decision_subject: "State migration and rollback for active module versions."
   902	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   903	    owner_decision_ref: null
   904	    default: null
   905	    absence_outcome: "BLOCK"
   906	    activation_without_decision: "DENIED"
   907	  - provision_id: "HERMES-OWNER-DECISION-008"
   908	    status: "OWNER_DECISION_REQUIRED"
   909	    guard_id: "OWNER_DECIDES_EXTERNAL_EXTENSION_PROTOCOL_AND_CAPABILITIES"
   910	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2134"
   911	    source_end_line: 2134
   912	    blocking_stage: "MODULE_ACTIVATION"
   913	    decision_subject: "Secure external-extension protocol and capability vocabulary."
   914	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   915	    owner_decision_ref: null
   916	    default: null
   917	    absence_outcome: "BLOCK"
   918	    activation_without_decision: "DENIED"
   919	  - provision_id: "HERMES-OWNER-DECISION-009"
   920	    status: "OWNER_DECISION_REQUIRED"
   921	    guard_id: "OWNER_DECIDES_POLICY_AUTHORING_LANGUAGE"
   922	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2135"
   923	    source_end_line: 2135
   924	    blocking_stage: "MODULE_ACTIVATION"
   925	    decision_subject: "Policy authoring language, including typed Python or JSON rules versus OPA or Cedar."
   926	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   927	    owner_decision_ref: null
   928	    default: null
   929	    absence_outcome: "BLOCK"
   930	    activation_without_decision: "DENIED"
   931	  - provision_id: "HERMES-OWNER-DECISION-010"
   932	    status: "OWNER_DECISION_REQUIRED"
   933	    guard_id: "OWNER_DECIDES_REVIEWER_INDEPENDENCE_AND_JUDGE_THRESHOLDS"
   934	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2136"
   935	    source_end_line: 2136
   936	    blocking_stage: "GATE_ADVANCE"
   937	    decision_subject: "Reviewer independence and calibrated model-judge thresholds."
   938	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   939	    owner_decision_ref: null
   940	    default: null
   941	    absence_outcome: "BLOCK"
   942	    activation_without_decision: "DENIED"
   943	  - provision_id: "HERMES-OWNER-DECISION-011"
   944	    status: "OWNER_DECISION_REQUIRED"
   945	    guard_id: "OWNER_DECIDES_HOST_ISOLATION_PROFILE_AND_PERFORMANCE"
   946	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2137"
   947	    source_end_line: 2137
   948	    blocking_stage: "PRODUCTION_READY"
   949	    decision_subject: "Host isolation profile and acceptable performance."
   950	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   951	    owner_decision_ref: null
   952	    default: null
   953	    absence_outcome: "BLOCK"
   954	    activation_without_decision: "DENIED"
   955	  - provision_id: "HERMES-OWNER-DECISION-012"
   956	    status: "OWNER_DECISION_REQUIRED"
   957	    guard_id: "OWNER_DECIDES_RETAINED_HERMES_SESSION_AND_SEARCH_SCOPE"
   958	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2138"
   959	    source_end_line: 2138
   960	    blocking_stage: "MIGRATION"
   961	    decision_subject: "How much inherited Hermes session and search behavior Ranex retains."
   962	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   963	    owner_decision_ref: null
   964	    default: null
   965	    absence_outcome: "BLOCK"
   966	    activation_without_decision: "DENIED"
   967	  - provision_id: "HERMES-OWNER-DECISION-013"
   968	    status: "OWNER_DECISION_REQUIRED"
   969	    guard_id: "OWNER_DECIDES_KANBAN_PROJECTION_OR_TABLE_ADAPTER"
   970	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:758"
   971	    source_end_line: 761
   972	    blocking_stage: "IMPLEMENTATION_START"
   973	    decision_subject: "Whether Kanban is a projection of canonical state or selected tables are adapted behind work management."
   974	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   975	    owner_decision_ref: null
   976	    default: null
   977	    absence_outcome: "BLOCK"
   978	    activation_without_decision: "DENIED"
   979	  - provision_id: "HERMES-OWNER-DECISION-014"
   980	    status: "OWNER_DECISION_REQUIRED"
   981	    guard_id: "OWNER_DECIDES_FUTURE_PROVIDER_NEUTRAL_OPEN_WEIGHT_MODEL"
   982	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1568"
   983	    source_end_line: 1572
   984	    blocking_stage: "MODULE_ACTIVATION"
   985	    decision_subject: "Whether a future release qualifies an independently hosted open-weight model originally published by Nous through a provider-neutral catalog."
   986	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   987	    owner_decision_ref: null
   988	    default: null
   989	    absence_outcome: "BLOCK"
   990	    activation_without_decision: "DENIED"
   991	  - provision_id: "HERMES-OWNER-DECISION-015"
   992	    status: "OWNER_DECISION_REQUIRED"
   993	    guard_id: "OWNER_DECIDES_UNRELATED_PAYMENT_TOOL_SCOPE"
   994	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1597"
   995	    source_end_line: 1600
   996	    blocking_stage: "MODULE_ACTIVATION"
   997	    decision_subject: "Whether an unrelated third-party payment-system tool belongs in Ranex product scope and risk policy."
   998	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
   999	    owner_decision_ref: null
  1000	    default: null
  1001	    absence_outcome: "BLOCK"
  1002	    activation_without_decision: "DENIED"
  1003	  - provision_id: "HERMES-OWNER-DECISION-016"
  1004	    status: "OWNER_DECISION_REQUIRED"
  1005	    guard_id: "OWNER_DECIDES_VOICE_REQUIREMENT_BEFORE_MEDIA_ACTIVATION"
  1006	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1753"
  1007	    source_end_line: 1755
  1008	    blocking_stage: "MODULE_ACTIVATION"
  1009	    decision_subject: "Whether voice becomes an explicit requirement and therefore permits a separately qualified TTS or STT delivery adapter."
  1010	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1011	    owner_decision_ref: null
  1012	    default: null
  1013	    absence_outcome: "BLOCK"
  1014	    activation_without_decision: "DENIED"
  1015	  - provision_id: "HERMES-OWNER-DECISION-017"
  1016	    status: "OWNER_DECISION_REQUIRED"
  1017	    guard_id: "OWNER_DECIDES_DESKTOP_OR_LOCAL_WEB_TUI_PRODUCT_PATH"
  1018	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1771"
  1019	    source_end_line: 1772
  1020	    blocking_stage: "IMPLEMENTATION_START"
  1021	    decision_subject: "Whether Electron and desktop bootstrap applications remain after selection of the local web or TUI product path."
  1022	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1023	    owner_decision_ref: null
  1024	    default: null
  1025	    absence_outcome: "BLOCK"
  1026	    activation_without_decision: "DENIED"
  1027	  - provision_id: "HERMES-OWNER-DECISION-018"
  1028	    status: "OWNER_DECISION_REQUIRED"
  1029	    guard_id: "OWNER_DECIDES_TIME_BOUNDED_HERMES_CLI_MIGRATION_SHIM"
  1030	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1787"
  1031	    source_end_line: 1789
  1032	    blocking_stage: "MIGRATION"
  1033	    decision_subject: "Whether an existing-user transition requires a time-bounded hermes CLI migration shim."
  1034	    required_decision_artifact: "ACCEPTED_ADR_WITH_PREDECLARED_ACCEPTANCE_TEST"
  1035	    owner_decision_ref: null
  1036	    default: null
  1037	    absence_outcome: "BLOCK"
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
  1071	    status: "RESEARCH_ONLY"
  1072	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:343"
  1073	    source_end_line: 358
  1074	    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
  1075	    reason: "The reusable-seam assessments guide characterization and extraction, but each retained asset still needs exact-version qualification."
  1076	  - provision_id: "HERMES-RESEARCH-ONLY-003"
  1077	    status: "RESEARCH_ONLY"
  1078	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1129"
  1079	    source_end_line: 1154
  1080	    reason_code: "ILLUSTRATIVE_NONCANONICAL"
  1081	    reason: "The research explicitly labels the execution-state sketch illustrative and not the canonical enum."
  1082	  - provision_id: "HERMES-RESEARCH-ONLY-004"
  1083	    status: "RESEARCH_ONLY"
  1084	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1218"
  1085	    source_end_line: 1279
  1086	    reason_code: "SUPERSEDED_LAYOUT"
  1087	    reason: "The suggested layout is a research map; ADR-0007 now owns the exact canonical repository topology."
  1088	  - provision_id: "HERMES-RESEARCH-ONLY-005"
  1089	    status: "RESEARCH_ONLY"
  1090	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1551"
  1091	    source_end_line: 1590
  1092	    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
  1093	    reason: "Exact upstream file deletion and salvage rows are pinned-revision migration inputs; the promoted release gates check outcomes without assuming those paths still exist."
  1094	  - provision_id: "HERMES-RESEARCH-ONLY-006"
  1095	    status: "RESEARCH_ONLY"
  1096	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1729"
  1097	    source_end_line: 1758
  1098	    reason_code: "OWNER_SCOPE_NOT_SELECTED"
  1099	    reason: "The broad first-release profile list mixes accepted exclusions with conditional product-scope candidates and cannot be promoted as one blanket rule."
  1100	  - provision_id: "HERMES-RESEARCH-ONLY-007"
  1101	    status: "RESEARCH_ONLY"
  1102	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1760"
  1103	    source_end_line: 1783
  1104	    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
  1105	    reason: "Archive and source-removal candidates depend on compatibility windows and parity evidence that do not yet exist."
  1106	  - provision_id: "HERMES-RESEARCH-ONLY-008"
  1107	    status: "RESEARCH_ONLY"
  1108	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1860"
  1109	    source_end_line: 1898
  1110	    reason_code: "CONDITIONAL_MIGRATION_GUIDANCE"
  1111	    reason: "The Phase 0 and Phase 0A freeze, characterization, and commercial-removal activities remain migration planning; the owner explicitly removed Phase 1 lines 1899-1912 from this disposition."
  1112	  - provision_id: "HERMES-RESEARCH-ONLY-009"
  1113	    status: "RESEARCH_ONLY"
  1114	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2006"
  1115	    source_end_line: 2090
  1116	    reason_code: "NONQUANTIFIED_RECOMMENDATION"
  1117	    reason: "The validation inventory is a test-design source; exact executable fixtures require an enacted runtime subject and are not fabricated by the documentation validator."
  1118	  - provision_id: "HERMES-RESEARCH-ONLY-010"
  1119	    status: "RESEARCH_ONLY"
  1120	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2092"
  1121	    source_end_line: 2155
  1122	    reason_code: "MATURITY_ASSESSMENT_NOT_CONTROL"
  1123	    reason: "Maturity labels and rejected foundations are advisory assessment; the genuine choices are separately registered as OWNER_DECISION_REQUIRED."
  1124	  - provision_id: "HERMES-RESEARCH-ONLY-011"
  1125	    status: "RESEARCH_ONLY"
  1126	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2157"
  1127	    source_end_line: 2258
  1128	    reason_code: "ADVISORY_MODEL_EVIDENCE"
  1129	    reason: "Limitations, HY3 execution facts, and reviewer-model maturity are provenance and evidence, not deterministic Ranex authority."
  1130	  - provision_id: "HERMES-RESEARCH-ONLY-012"
  1131	    status: "RESEARCH_ONLY"
  1132	    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2283"
  1133	    source_end_line: 2310
  1134	    reason_code: "OWNER_SCOPE_NOT_SELECTED"
  1135	    reason: "Deferred capabilities and remove-from-core guidance do not authorize source deletion or activation; later scope ADRs and module contracts govern them."
  1136	  - provision_id: "HERMES-RESEARCH-ONLY-013"
  1137	    status: "RESEARCH_ONLY"
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
  1161	
  1162	Those rows are a closed denominator of material disposition classes, not a
  1163	claim that every explanatory or bibliographic line is itself a provision.
  1164	Research text not named by a promoted or owner-decision row remains advisory
  1165	under the Source of Truth policy; omission from this catalog cannot promote it
  1166	by implication.
  1167	
  1168	## Consequences
  1169	
  1170	- Missing or reordered catalog rows, drifted citations, and malformed guards
  1171	  fail architecture validation.
  1172	- Phase 1 cannot be reclassified as mere sequencing or removed from the
  1173	  clean-kernel inventory without a superseding owner-accepted ADR and catalog
  1174	  revision.
  1175	- An unresolved owner choice cannot be activated by configuration, convention,
  1176	  model output, or a generator default.
  1177	- `PASS` from `validate_contracts.py` means the documentation contract is
  1178	  closed and faithful; all runtime and release evidence remains
  1179	  `NOT_ASSESSED`.
  1180	- Legal and attribution obligations remain outside owner waiver authority.
  1181	
  1182	## Human approval
  1183	
  1184	The human owner required these research-backed obligations to become
  1185	line-auditable and fail closed. This ADR records that direction. It is not
  1186	runtime evidence, a release permit, or a substitute for counsel where a legal
  1187	question requires legal advice.

exec
/bin/bash -lc 'git -C .claude/worktrees/kernel-tracer status --short --branch' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
## feature/kernel-tracer
 M .gitignore
?? pyproject.toml
?? src/
?? tests/
?? uv.lock

exec
/bin/bash -lc 'nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql' in /home/soultransit/devtony/ranex
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

exec
/bin/bash -lc 'nl -ba .claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	from ranex.foundation.identity import Identity
     4	from ranex.governed_execution.domain.events import (
     5	    ExecutionCreated,
     6	    ExecutionMarkedReady,
     7	    ExecutionStarted,
     8	    ExecutionSucceeded,
     9	)
    10	from ranex.governed_execution.domain.execution import (
    11	    reduce_execution,
    12	    replay_execution,
    13	)
    14	from ranex.governed_execution.domain.status import ExecutionStatus
    15	
    16	
    17	def identity(prefix: str, suffix: str) -> Identity:
    18	    return Identity.parse(
    19	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    20	        expected_prefix=prefix,
    21	    )
    22	
    23	
    24	def test_replay_reproduces_identical_final_state_and_version() -> None:
    25	    run_id = identity("run", "a01")
    26	    events = (
    27	        ExecutionCreated(
    28	            event_id=identity("transition", "b01"),
    29	            execution_id=run_id,
    30	            expected_version=0,
    31	            occurred_at="2026-07-29T01:00:00Z",
    32	            work_item_id=identity("work", "a02"),
    33	            created_by_principal_id=identity("principal", "a03"),
    34	            workflow_request_ref="workflow-request:sha256:one",
    35	        ),
    36	        ExecutionMarkedReady(
    37	            event_id=identity("transition", "b02"),
    38	            execution_id=run_id,
    39	            expected_version=1,
    40	            occurred_at="2026-07-29T01:00:01Z",
    41	            readiness_snapshot_ref="snapshot:sha256:ready",
    42	        ),
    43	        ExecutionStarted(
    44	            event_id=identity("transition", "b03"),
    45	            execution_id=run_id,
    46	            expected_version=2,
    47	            occurred_at="2026-07-29T01:00:02Z",
    48	            authorization_ref="authorization:sha256:start",
    49	        ),
    50	        ExecutionSucceeded(
    51	            event_id=identity("transition", "b04"),
    52	            execution_id=run_id,
    53	            expected_version=3,
    54	            occurred_at="2026-07-29T01:00:03Z",
    55	            outcome_ref="outcome:sha256:success",
    56	        ),
    57	    )
    58	
    59	    direct = None
    60	    for event in events:
    61	        direct = reduce_execution(direct, event)
    62	    replayed = replay_execution(events)
    63	
    64	    assert replayed == direct
    65	    assert replayed.status is ExecutionStatus.SUCCEEDED
    66	    assert replayed.version == len(events) == 4

exec
/bin/bash -lc 'nl -ba .claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import sqlite3
     4	from pathlib import Path
     5	
     6	import pytest
     7	
     8	from ranex.foundation.identity import Identity
     9	from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
    10	    SQLiteExecutionStore,
    11	)
    12	from ranex.governed_execution.domain.events import (
    13	    ExecutionCreated,
    14	    ExecutionMarkedReady,
    15	)
    16	from ranex.governed_execution.domain.status import ExecutionStatus
    17	
    18	RUN_ID = Identity.parse(
    19	    "run_01890f47-25a1-7a11-98b3-5f5f6bb25af7",
    20	    expected_prefix="run",
    21	)
    22	
    23	
    24	def identity(prefix: str, suffix: str) -> Identity:
    25	    return Identity.parse(
    26	        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
    27	        expected_prefix=prefix,
    28	    )
    29	
    30	
    31	def test_failure_between_journal_and_outbox_leaves_no_partial_state(
    32	    tmp_path: Path,
    33	) -> None:
    34	    database_path = tmp_path / "crash-boundary.sqlite3"
    35	    store = SQLiteExecutionStore(database_path)
    36	    store.initialize()
    37	    store.append(
    38	        ExecutionCreated(
    39	            event_id=identity("transition", "a12"),
    40	            execution_id=RUN_ID,
    41	            expected_version=0,
    42	            occurred_at="2026-07-29T03:00:00Z",
    43	            work_item_id=identity("work", "a13"),
    44	            created_by_principal_id=identity("principal", "a14"),
    45	            workflow_request_ref="workflow-request:sha256:crash",
    46	        )
    47	    )
    48	
    49	    with sqlite3.connect(database_path) as connection:
    50	        connection.executescript(
    51	            """
    52	            CREATE TRIGGER simulate_crash_before_outbox
    53	            BEFORE INSERT ON execution_outbox
    54	            WHEN NEW.aggregate_version = 2
    55	            BEGIN
    56	                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
    57	            END;
    58	            """
    59	        )
    60	
    61	    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
    62	        store.append(
    63	            ExecutionMarkedReady(
    64	                event_id=identity("transition", "a15"),
    65	                execution_id=RUN_ID,
    66	                expected_version=1,
    67	                occurred_at="2026-07-29T03:00:01Z",
    68	                readiness_snapshot_ref="snapshot:sha256:crash-ready",
    69	            )
    70	        )
    71	
    72	    unchanged = store.load(RUN_ID)
    73	    assert unchanged is not None
    74	    assert unchanged.status is ExecutionStatus.PROPOSED
    75	    assert unchanged.version == 1
    76	    assert unchanged.last_event_id == identity("transition", "a12")
    77	    assert store.count_journal_entries(RUN_ID) == 1
    78	    assert store.count_outbox_entries(RUN_ID) == 1
    79	
    80	    with sqlite3.connect(database_path) as connection:
    81	        absent_everywhere = connection.execute(
    82	            """
    83	            SELECT
    84	                (SELECT COUNT(*) FROM execution_state
    85	                 WHERE last_event_id = ?) +
    86	                (SELECT COUNT(*) FROM execution_journal
    87	                 WHERE event_id = ?) +
    88	                (SELECT COUNT(*) FROM execution_outbox
    89	                 WHERE event_id = ?)
    90	            """,
    91	            (
    92	                str(identity("transition", "a15")),
    93	                str(identity("transition", "a15")),
    94	                str(identity("transition", "a15")),
    95	            ),
    96	        ).fetchone()
    97	
    98	    assert absent_everywhere == (0,)

exec
/bin/bash -lc "rg -n -A14 -B3 'HERMES-PROMOTION-05[8-9]|HERMES-PROMOTION-06[0-5]' docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
23-This revision repairs one unsupported qualifier found by a post-1.3.0
24-fidelity audit after three earlier repair rounds had missed it.
25-
26:- **DEFECT 9** — `HERMES-PROMOTION-059` claimed that *every* Execution
27-  state transition is computed by the pure reducer, while the cited
28-  research line 1902 supports only "Implement an `Execution` aggregate
29-  and pure reducer." The unsupported `every` qualifier is removed; the
30-  provision now states that Execution state transitions are computed by
31-  the aggregate's pure reducer, without a universal-coverage claim the
32-  research does not make.
33-
34-### 1.3.0 — 2026-07-30
35-
36-This revision records the second full-row fidelity audit and closes the
37-remaining unpinned-row blind spot.
38-
39-- **DEFECT 6** — `HERMES-PROMOTION-002` now states only that the new
40-  dependency-clean kernel is built beside Hermes; `HERMES-PROMOTION-004`
--
44-  `HERMES-PROMOTION-017` uses the cited side-effect-free requirement without
45-  an invented example list.
46-- **DEFECT 7** — The 1.2.0 history now records its previously omitted
47:  normative changes to `HERMES-PROMOTION-058` and
48:  `HERMES-PROMOTION-059`.
49-- **DEFECT 8** — Exact-text fidelity pins now cover all 65 promoted
50-  provisions, all 20 owner-decision subjects, and all 13 research-only
51-  dispositions. Any paraphrase of a pinned text fails generation and
52-  validation.
53-
54-### 1.2.0 — 2026-07-29
55-
56-This revision records the result of placing every promoted provision beside
57-its cited research excerpt and comparing obligation class, scope, and
58-specificity.
59-
60-- **Previously omitted 1.2.0 normative changes (recorded retroactively in
61:  1.3.0)** — `HERMES-PROMOTION-058` renamed
62-  `SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION_DEFINE_KERNEL_RECORDS` to
63-  `CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION` and
64-  removed the unsupported `kernel records` scope.
65:  `HERMES-PROMOTION-059` replaced “whose state evolution is computed by a pure
66-  reducer without observable side effects” with “every Execution state
67-  transition is computed by its pure reducer.”
68-- **DEFECT 1** — `HERMES-PROMOTION-011` again requires removal of the Nous
69-  commercial subsystem, and `HERMES-PROMOTION-041` again requires removal of
70-  Hermes/Nous branding. Neither action is represented as an asserted
71-  absent-state.
72-- **DEFECT 2** — `HERMES-PROMOTION-040` restores rebranding as the specific
73-  context that does not authorize erasing legal notices or Git history.
74-- **DEFECT 3** — `HERMES-PROMOTION-041` restores package metadata, remote
75-  endpoints, headers, telemetry tags, help text, screenshots, generated
76-  assets, and defaults as eight separately checkable surfaces. The same
77-  row-by-row specificity check restores the cited item-level terms in
78-  `HERMES-PROMOTION-037`, `HERMES-PROMOTION-038`,
79-  `HERMES-PROMOTION-044`, `HERMES-PROMOTION-045`,
--
85-  `governed`, `accepted`, generalized domain-package, and `authority`
86-  qualifiers and restore their exact cited scopes.
87-- **DEFECT 5** — Phase 1 lines 1899–1912 remain represented by
88:  `HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`, rather than by an
89-  exclusion-equivalence claim. Phase 0/0A activity and Phase 2–6 sequencing
90-  and exit material remain research-only and are not represented by promoted
91-  gates.
92-
93-### 1.1.0 — 2026-07-29
94-
95-By owner decision, this revision overturns the prior “implementation
96-sequencing, not fixed authority” exclusion for Phase 1. Research lines
97-1899–1912 define the clean kernel's binding structural inventory and behavior,
98-not a delivery schedule.
99-
100-This revision adds eight promoted provisions,
101:`HERMES-PROMOTION-058` through `HERMES-PROMOTION-065`:
102-
103-1. shared identity and canonical serialization;
104-2. the `Execution` aggregate and pure reducer;
105-3. canonical relational execution state and version;
106-4. the append-only transition/audit journal and outbox in one SQLite unit of
107-   work;
108-5. the evidence-gated, `Execution`-only event-sourcing boundary;
109-6. the fail-closed application-control PEP, pure domain decisions, and
110-   deterministic policy adapter;
111-7. architecture import tests before feature code; and
112-8. the replay, crash-boundary, and no-Hermes-import exit gate.
113-
114-It also adds `HERMES-OWNER-DECISION-020` as an
115-`OWNER_DECISION_REQUIRED` row for whether qualified `Execution` event sourcing
--
739-    provision: "No product-facing package name, CLI command, config root, header, telemetry tag, help screen, screenshot, generated asset, or default presents Hermes/Nous branding outside an explicit migration warning or legally required attribution."
740-    required_result: "PASS"
741-    failure_outcome: "BLOCK"
742:  - provision_id: "HERMES-PROMOTION-058"
743-    status: "PROMOTED"
744-    guard_id: "CLEAN_KERNEL_PROVIDES_SHARED_IDENTITY_AND_CANONICAL_SERIALIZATION"
745-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1901"
746-    source_end_line: 1901
747-    check_class: "ARCHITECTURE_CONTRACT"
748-    blocking_stage: "IMPLEMENTATION_START"
749-    provision: "The clean kernel contains a shared-identity facility that provides shared identity and a canonical-serialization facility that provides canonical serialization."
750-    required_result: "PASS"
751-    failure_outcome: "BLOCK"
752:  - provision_id: "HERMES-PROMOTION-059"
753-    status: "PROMOTED"
754-    guard_id: "EXECUTION_AGGREGATE_TRANSITIONS_THROUGH_PURE_REDUCER"
755-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1902"
756-    source_end_line: 1902
757-    check_class: "RUNTIME_FITNESS"
758-    blocking_stage: "GATE_ADVANCE"
759-    provision: "The clean kernel contains an Execution aggregate, and Execution state transitions are computed by its pure reducer."
760-    required_result: "PASS"
761-    failure_outcome: "BLOCK"
762:  - provision_id: "HERMES-PROMOTION-060"
763-    status: "PROMOTED"
764-    guard_id: "CANONICAL_RELATIONAL_EXECUTION_STATE_HAS_EXPLICIT_VERSION"
765-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
766-    source_end_line: 1903
767-    check_class: "ARCHITECTURE_CONTRACT"
768-    blocking_stage: "GATE_ADVANCE"
769-    provision: "The clean kernel persists canonical execution state and its associated version in relational storage."
770-    required_result: "PASS"
771-    failure_outcome: "BLOCK"
772:  - provision_id: "HERMES-PROMOTION-061"
773-    status: "PROMOTED"
774-    guard_id: "TRANSITION_AUDIT_JOURNAL_AND_OUTBOX_SHARE_ONE_SQLITE_UNIT_OF_WORK"
775-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1903"
776-    source_end_line: 1904
777-    check_class: "AUTHORITY_FITNESS"
778-    blocking_stage: "GATE_ADVANCE"
779-    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
780-    required_result: "PASS"
781-    failure_outcome: "BLOCK"
782:  - provision_id: "HERMES-PROMOTION-062"
783-    status: "PROMOTED"
784-    guard_id: "EVENT_SOURCING_IS_EXECUTION_ONLY_AND_REPLAY_MIGRATION_QUALIFIED"
785-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1904"
786-    source_end_line: 1906
787-    check_class: "MIGRATION_FITNESS"
788-    blocking_stage: "GATE_ADVANCE"
789-    provision: "The clean kernel permits event sourcing only for the Execution aggregate and only if its replay and migration tests justify that choice; every other module remains outside that event-sourcing scope."
790-    required_result: "PASS"
791-    failure_outcome: "BLOCK"
792:  - provision_id: "HERMES-PROMOTION-063"
793-    status: "PROMOTED"
794-    guard_id: "FAIL_CLOSED_APPLICATION_CONTROL_PEP_USES_PURE_DECISIONS_AND_DETERMINISTIC_POLICY"
795-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1907"
796-    source_end_line: 1908
797-    check_class: "AUTHORITY_FITNESS"
798-    blocking_stage: "GATE_ADVANCE"
799-    provision: "The clean kernel contains an application-control policy-enforcement point that is fail-closed, uses pure domain decisions, and invokes a simple deterministic policy adapter."
800-    required_result: "PASS"
801-    failure_outcome: "BLOCK"
802:  - provision_id: "HERMES-PROMOTION-064"
803-    status: "PROMOTED"
804-    guard_id: "ARCHITECTURE_IMPORT_TESTS_PRECEDE_FEATURE_CODE"
805-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1909"
806-    source_end_line: 1909
807-    check_class: "STATIC_FITNESS"
808-    blocking_stage: "IMPLEMENTATION_START"
809-    provision: "Architecture import tests are part of the clean-kernel contract and must be present and passing before feature code is admitted."
810-    required_result: "PASS"
811-    failure_outcome: "BLOCK"
812:  - provision_id: "HERMES-PROMOTION-065"
813-    status: "PROMOTED"
814-    guard_id: "CLEAN_KERNEL_EXIT_REQUIRES_REPLAY_CRASH_TESTS_WITHOUT_HERMES_IMPORT"
815-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:1911"
816-    source_end_line: 1911
817-    check_class: "RUNTIME_FITNESS"
818-    blocking_stage: "GATE_ADVANCE"
819-    provision: "The clean-kernel gate advances only when reducer replay tests and crash-boundary tests pass and the tested kernel has no Hermes import."
820-    required_result: "PASS"
821-    failure_outcome: "BLOCK"
822-owner_decisions:
823-  - provision_id: "HERMES-OWNER-DECISION-001"
824-    status: "OWNER_DECISION_REQUIRED"
825-    guard_id: "OWNER_DECIDES_WORKFLOW_EVENT_SCHEMA_AND_UPCASTER_POLICY"
826-    source_ref: "docs/research/hermes-core-architecture-research-2026-07-27.md:2125"

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '1,460p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
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
   128	def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
   129	    document: dict[str, object] = {
   130	        "schema_version": "execution-event/v1",
   131	        "event_type": type(event).__name__,
   132	        "event_id": str(event.event_id),
   133	        "execution_id": str(event.execution_id),
   134	        "expected_version": event.expected_version,
   135	        "occurred_at": event.occurred_at,
   136	    }
   137	    if isinstance(event, ExecutionCreated):
   138	        document.update(
   139	            {
   140	                "work_item_id": str(event.work_item_id),
   141	                "created_by_principal_id": str(event.created_by_principal_id),
   142	                "workflow_request_ref": event.workflow_request_ref,
   143	            }
   144	        )
   145	    elif isinstance(event, ExecutionMarkedReady):
   146	        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
   147	    elif isinstance(event, ExecutionStarted):
   148	        document["authorization_ref"] = event.authorization_ref
   149	    elif isinstance(event, ExecutionWaited):
   150	        document["wait_reason_code"] = event.wait_reason_code
   151	    elif isinstance(event, ExecutionResumed):
   152	        document["signal_ref"] = event.signal_ref
   153	    elif isinstance(event, ExecutionBlocked):
   154	        document.update(
   155	            {
   156	                "block_reason_code": event.block_reason_code,
   157	                "blocking_refs": list(event.blocking_refs),
   158	            }
   159	        )
   160	    elif isinstance(event, ExecutionUnblocked):
   161	        document.update(
   162	            {
   163	                "target_status": event.target_status.value,
   164	                "refreshed_evidence_ref": event.refreshed_evidence_ref,
   165	            }
   166	        )
   167	    elif isinstance(event, ExecutionSucceeded):
   168	        document["outcome_ref"] = event.outcome_ref
   169	    elif isinstance(event, ExecutionFailed):
   170	        document.update(
   171	            {
   172	                "failure_reason_code": event.failure_reason_code,
   173	                "evidence_ref": event.evidence_ref,
   174	            }
   175	        )
   176	    elif isinstance(event, ExecutionCancelled):
   177	        document["decision_ref"] = event.decision_ref
   178	    else:
   179	        raise TypeError(f"unsupported execution event: {type(event).__name__}")
   180	    return document
   181	
   182	
   183	class SQLiteExecutionStore(ExecutionRepository):
   184	    """State, audit journal, and outbox committed in one SQLite transaction."""
   185	
   186	    def __init__(self, path: Path) -> None:
   187	        self._path = path
   188	
   189	    def _connect(self) -> sqlite3.Connection:
   190	        connection = sqlite3.connect(
   191	            self._path,
   192	            isolation_level=None,
   193	            timeout=5.0,
   194	        )
   195	        connection.row_factory = sqlite3.Row
   196	        connection.execute("PRAGMA foreign_keys = ON")
   197	        connection.execute("PRAGMA synchronous = FULL")
   198	        return connection
   199	
   200	    def initialize(self) -> None:
   201	        self._path.parent.mkdir(parents=True, exist_ok=True)
   202	        migration = _MIGRATION.read_text(encoding="utf-8")
   203	        connection = self._connect()
   204	        try:
   205	            connection.executescript(migration)
   206	        finally:
   207	            connection.close()
   208	        self._path.chmod(0o600)
   209	
   210	    def load(self, execution_id: Identity) -> Execution | None:
   211	        self._require_run_id(execution_id)
   212	        with closing(self._connect()) as connection:
   213	            row = connection.execute(
   214	                """
   215	                SELECT execution_id, canonical_state_json, version, last_event_id
   216	                FROM execution_state
   217	                WHERE execution_id = ?
   218	                """,
   219	                (str(execution_id),),
   220	            ).fetchone()
   221	        return None if row is None else self._decode_state_row(row)
   222	
   223	    def append(self, event: ExecutionEvent) -> Execution:
   224	        connection = self._connect()
   225	        connection.execute("BEGIN IMMEDIATE")
   226	        try:
   227	            current_row = connection.execute(
   228	                """
   229	                SELECT execution_id, canonical_state_json, version, last_event_id
   230	                FROM execution_state
   231	                WHERE execution_id = ?
   232	                """,
   233	                (str(event.execution_id),),
   234	            ).fetchone()
   235	            current = (
   236	                None if current_row is None else self._decode_state_row(current_row)
   237	            )
   238	            next_state = reduce_execution(current, event)
   239	            next_document = _execution_to_document(next_state)
   240	            next_json = canonical_json(next_document)
   241	
   242	            if current is None:
   243	                connection.execute(
   244	                    """
   245	                    INSERT INTO execution_state(
   246	                        execution_id,
   247	                        canonical_state_json,
   248	                        version,
   249	                        last_event_id,
   250	                        updated_at
   251	                    ) VALUES (?, ?, ?, ?, ?)
   252	                    """,
   253	                    (
   254	                        str(next_state.execution_id),
   255	                        next_json,
   256	                        next_state.version,
   257	                        str(next_state.last_event_id),
   258	                        next_state.updated_at,
   259	                    ),
   260	                )
   261	                previous_json = None
   262	                previous_version = 0
   263	            else:
   264	                assert current_row is not None
   265	                previous_json = str(current_row["canonical_state_json"])
   266	                previous_version = current.version
   267	                cursor = connection.execute(
   268	                    """
   269	                    UPDATE execution_state
   270	                    SET canonical_state_json = ?,
   271	                        version = ?,
   272	                        last_event_id = ?,
   273	                        updated_at = ?
   274	                    WHERE execution_id = ?
   275	                      AND version = ?
   276	                      AND canonical_state_json = ?
   277	                    """,
   278	                    (
   279	                        next_json,
   280	                        next_state.version,
   281	                        str(next_state.last_event_id),
   282	                        next_state.updated_at,
   283	                        str(next_state.execution_id),
   284	                        current.version,
   285	                        previous_json,
   286	                    ),
   287	                )
   288	                if cursor.rowcount != 1:
   289	                    raise ConcurrentExecutionWriteError(
   290	                        "canonical execution compare-and-swap failed"
   291	                    )
   292	
   293	            event_document = _event_to_document(event)
   294	            event_json = canonical_json(event_document)
   295	            resulting_digest = canonical_sha256(next_document)
   296	            previous_digest = (
   297	                None
   298	                if previous_json is None
   299	                else canonical_sha256(json.loads(previous_json))
   300	            )
   301	            connection.execute(
   302	                """
   303	                INSERT INTO execution_journal(
   304	                    event_id,
   305	                    execution_id,
   306	                    event_type,
   307	                    previous_version,
   308	                    resulting_version,
   309	                    event_json,
   310	                    previous_state_sha256,
   311	                    resulting_state_sha256,
   312	                    resulting_state_json,
   313	                    recorded_at
   314	                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   315	                """,
   316	                (
   317	                    str(event.event_id),
   318	                    str(event.execution_id),
   319	                    type(event).__name__,
   320	                    previous_version,
   321	                    next_state.version,
   322	                    event_json,
   323	                    previous_digest,
   324	                    resulting_digest,
   325	                    next_json,
   326	                    event.occurred_at,
   327	                ),
   328	            )
   329	
   330	            outbox_document = {
   331	                "schema_version": "execution-outbox/v1",
   332	                "event_id": str(event.event_id),
   333	                "event_type": type(event).__name__,
   334	                "execution_id": str(event.execution_id),
   335	                "aggregate_version": next_state.version,
   336	                "occurred_at": event.occurred_at,
   337	                "event": event_document,
   338	            }
   339	            connection.execute(
   340	                """
   341	                INSERT INTO execution_outbox(
   342	                    event_id,
   343	                    execution_id,
   344	                    aggregate_version,
   345	                    payload_json,
   346	                    created_at
   347	                ) VALUES (?, ?, ?, ?, ?)
   348	                """,
   349	                (
   350	                    str(event.event_id),
   351	                    str(event.execution_id),
   352	                    next_state.version,
   353	                    canonical_json(outbox_document),
   354	                    event.occurred_at,
   355	                ),
   356	            )
   357	            connection.execute("COMMIT")
   358	            return next_state
   359	        except BaseException:
   360	            if connection.in_transaction:
   361	                connection.execute("ROLLBACK")
   362	            raise
   363	        finally:
   364	            connection.close()
   365	
   366	    def count_journal_entries(self, execution_id: Identity) -> int:
   367	        return self._count_rows("execution_journal", execution_id)
   368	
   369	    def count_outbox_entries(self, execution_id: Identity) -> int:
   370	        return self._count_rows("execution_outbox", execution_id)
   371	
   372	    def _count_rows(self, table: str, execution_id: Identity) -> int:
   373	        self._require_run_id(execution_id)
   374	        if table not in {"execution_journal", "execution_outbox"}:
   375	            raise ValueError("unsupported execution table")
   376	        with closing(self._connect()) as connection:
   377	            row = connection.execute(
   378	                f"SELECT COUNT(*) AS count FROM {table} WHERE execution_id = ?",
   379	                (str(execution_id),),
   380	            ).fetchone()
   381	        assert row is not None
   382	        return int(row["count"])
   383	
   384	    @staticmethod
   385	    def _require_run_id(execution_id: Identity) -> None:
   386	        if not isinstance(execution_id, Identity) or execution_id.prefix != "run":
   387	            raise ValueError("execution_id must be a canonical run identity")
   388	
   389	    @staticmethod
   390	    def _decode_state_row(row: sqlite3.Row) -> Execution:
   391	        raw = str(row["canonical_state_json"])
   392	        try:
   393	            document = json.loads(raw)
   394	        except json.JSONDecodeError as exc:
   395	            raise ExecutionPersistenceIntegrityError(
   396	                "canonical execution state is not JSON"
   397	            ) from exc
   398	        if not isinstance(document, dict) or canonical_json(document) != raw:
   399	            raise ExecutionPersistenceIntegrityError(
   400	                "execution state is not canonically serialized"
   401	            )
   402	        try:
   403	            state = _execution_from_document(document)
   404	        except (TypeError, ValueError) as exc:
   405	            raise ExecutionPersistenceIntegrityError(
   406	                "canonical execution state is invalid"
   407	            ) from exc
   408	        if int(row["version"]) != state.version:
   409	            raise ExecutionPersistenceIntegrityError(
   410	                "relational version disagrees with canonical state version"
   411	            )
   412	        if str(row["last_event_id"]) != str(state.last_event_id):
   413	            raise ExecutionPersistenceIntegrityError(
   414	                "relational last event disagrees with canonical state"
   415	            )
   416	        if str(row["execution_id"]) != str(state.execution_id):
   417	            raise ExecutionPersistenceIntegrityError(
   418	                "relational identity disagrees with canonical state identity"
   419	            )
   420	        return state

exec
/bin/bash -lc "rg -n -i 'React Flow|Cytoscape|D3|Mermaid|SSE|WebSocket|poll|server|browser|infer|graph|license|Dagre|ELK|JointJS|Rete|Temporal|Argo|Airflow|Dagster|Kestra|Conductor|Actions' docs/research/deterministic-run-graph-visualization-research-2026-07-30.md" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
1:# Deterministic run-graph visualization research and architecture proposal
5:| Research ID | `RES-EXEC-GRAPH-001` |
15:| Runtime evidence | None; Ranex runtime remains `NOT_ASSESSED` |
17:## 1. Answer in one paragraph
23:its nodes. The server, inside the `governed_execution` boundary, derives a
24:versioned `ExecutionGraphProjection`; the browser renders that projection and
25:never infers transitions, evaluates rules, or advances the work item. For a
28:[`@dagrejs/dagre`](https://github.com/dagrejs/dagre) for the initial
29:left-to-right layout. Airflow, Argo Workflows, Gitea, GitLab, Kestra, and
30:Dagster demonstrate the underlying pattern in production open-source systems.
38:A run graph answers five questions without requiring the user to understand
43:3. What already passed, failed, or was not taken?
48:The main graph stays simple. A node shows an icon, short name, state, duration,
64:There can be many runs for one work item. The server must identify eligible or
65:active runs and the user must be able to select the exact run. The browser must
68:If exactly one current run is explicitly linked by the server-owned work-item
82:  -> read-only graph
87:**View execution** action. A full graph inside every card would make the board
95:## 3. The simple user-facing graph
100:```mermaid
130:- one run pins an approved workflow definition, interpreter version, and policy
132:- the same workflow/interpreter versions and ordered recorded inputs replay to
140:  maps, and dynamic graph mutation are extension points, not silently available
146:- evaluate a gate or rule in the browser;
147:- infer that a path was skipped merely because another path is active;
159:[GitHub Actions](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui)
160:generates a real-time graph for each workflow run and lets a user inspect job
167:dependency views. Its documented UX includes fan-out/fan-in graphs, grouped
170:large or repeated graphs.
174:| System | Proven implementation pattern | What Ranex should learn | License posture |
176:| [Gitea](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.vue) | Native SVG workflow graph with pan/zoom, status cards, duration, click-through details, grouped jobs, and path highlighting | Closest open implementation to the requested GitHub Actions experience; its [typed graph model](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.utils.ts) and [tests](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.utils.test.ts) are valuable test references. The component is Vue; it is a behavior precedent, not a React reuse candidate | MIT; copied code would require preserving its notice |
177:| [Apache Airflow](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx) | React Flow graph, ELK layout, generated API queries, and a streamed task-status overlay | Strongest direct precedent for a React implementation; it lays out structure separately, then merges live task instances without recalculating topology | Apache-2.0; use the pattern or comply with attribution/NOTICE duties for copied code |
178:| [Argo Workflows](https://github.com/argoproj/argo-workflows/blob/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/widgets/workflow-graph.tsx) | Watched workflow status plus a DAG viewer; [Dagre computes LR/TB coordinates](https://github.com/argoproj/argo-workflows/blob/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/shared/components/graph/pretty-layout.ts) | Dagre is sufficient for a mature workflow product's straightforward DAG view | Apache-2.0 |
179:| [Kestra](https://github.com/kestra-io/kestra/tree/e03a4f351328f294e67f62be60af0553401fad7a/ui/packages/topology) | Reusable Vue Flow topology package with Dagre, custom nodes/edges, collapsing, orientation, fit/zoom, and execution progress | Confirms that a flow renderer plus Dagre works beyond React and can remain a reusable presentation package | Apache-2.0 |
180:| [Dagster](https://github.com/dagster-io/dagster/blob/014641bc1bdb71ea2c7f40371691103bbff5c9c7/js_modules/dagster-ui/packages/ui-core/src/graph/layout.ts) | Dagre-backed layout with a custom SVG viewport, ports, parent graphs, pan/zoom, and keyboard navigation | A custom renderer is possible, but its code and accessibility burden are larger than Ranex needs for the first slice | Apache-2.0 |
181:| [Dagu](https://github.com/dagu-org/dagu/blob/3fd7eeff69e2df281cd8bd8f47348baf8d3462be/ui/src/features/dags/components/visualization/Graph.tsx) | Mermaid strings rebuilt with runtime status classes and interaction hooks | Useful evidence for a very small implementation, but repeated Mermaid rendering and DOM patching are a weaker live-UI foundation | GPL-3.0; do not copy into Ranex without a deliberate compatibility decision |
183:This is enough evidence to avoid inventing a graph framework or importing
194:4. Stream or poll status and merge it by node ID.
196:6. Keep the graph read-only during execution.
197:7. Degrade intentionally for large graphs.
199:Airflow is especially relevant. Its graph obtains structure and layout, then
201:graph is laid out.” It also renders only visible elements and removes a minimap
202:for very large graphs. Gitea supplies useful algorithms and tests for
208:```mermaid
210:    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
212:    P["ExecutionGraphProjection builder<br/>server-owned, versioned, deterministic"]
214:    E["SSE status deltas<br/>cursor + expected version"]
215:    U["Read-only dashboard graph<br/>React Flow + Dagre candidate"]
229:`ExecutionGraphProjection` is an immutable application query/view owned by
240:The projection is not a new aggregate, workflow interpreter, or event store.
241:The dashboard receives facts already interpreted by the owning server
246:its generated client/server contracts, and a fitness test that prevents
256:Every run graph must bind:
260:- `workflow_interpreter_version`;
268:The server alone computes `topology_digest` as SHA-256 over an RFC 8785
270:definition digest, interpreter version, stable node IDs and semantic kinds, and
276:For the same pinned definition and supported interpreter version:
285:Dagre output also depends on node insertion order and library behavior.
288:Dynamic graph mutation is out of scope until the workflow architecture
290:condition, never an invitation for the browser to improvise topology.
298:  "schema_version": "execution-graph-projection/v1",
306:  "workflow_interpreter_version": "SemVer",
322:| State | server-derived visual state, display-only canonical source axis/value, attempt, start/end/duration |
328:and server-reported traversal disposition. “Not traversed,” “not applicable,”
333:are supplied by the server's generated projection contract.
343:  human decision, authorized effect, reconciliation, or terminal is a graph
373:This proposed vocabulary is a server-derived read model, not a replacement for
375:one closed, total, generated, server-owned function and contract-tested for
389:GET /api/runs/{run_id}/graph
390:GET /api/runs/{run_id}/graph/events?after={cursor}
394:Server-Sent Events are the leading live-update candidate because this feature
397:redaction. SSE is not registered by the current architecture; selecting it
399:reconnect, resource, and shutdown behavior. Snapshot plus authenticated polling
404:transaction. A subscriber starts strictly after that cursor; the server either
415:On a cursor gap, version mismatch, topology mismatch, server restart, invalid
416:payload, or reconnect outside the retention window, the client discards
417:untrusted deltas and refetches the full snapshot. Slow polling is an acceptable
418:fallback. Airflow's newline-delimited stream is a viable alternative if the
419:existing transport layer standardizes on it; WebSocket is unnecessary for the
429:| React Flow + Dagre | Read-only custom nodes, pan/zoom/fit, selection, keyboard/screen-reader affordances, simple directed layout; both MIT | **Recommended first implementation if React is retained** |
430:| React Flow + ELK | Better compound graphs, ports, cross-hierarchy routing, and complex layout; Airflow proves the combination | Hold as an upgrade path; more configuration, worker/bundle complexity, and EPL-2.0 qualification |
432:| Mermaid runtime | Very small static proof of concept | Suitable for this research document, not the live authority-facing UI |
433:| Import Airflow/Argo/Kestra/Dagu as an engine | Rich existing workflow products | Reject; Ranex already owns different workflow and authority semantics |
435:[React Flow's layout guide](https://reactflow.dev/learn/layouting/layouting)
436:explicitly treats layout as a separate concern and describes Dagre as a simple
437:choice for directed trees, with ELK for more configurable cases. Its
443:`supplier_governance` adoption process, including license compatibility,
445:exit/upgrade plan. The maintained `@dagrejs/dagre` package must not be confused
446:with legacy Dagre packages. No package is adopted by this research.
453:apps/web-dashboard/src/features/runs/execution-graph/
463:them. The graph feature must not import canonical transition tables or policy
466:The corresponding server query/projection code belongs inside:
483:- run page shows one read-only, left-to-right graph;
489:- terminal graphs can be regenerated for audit from canonical retained facts,
490:  subject to artifact and legal-retention policy; and
494:Graph and ordered/table views are two presentations of the same projection and
495:the user can switch between them. The requested graph remains the default
503:- run commands such as retry/cancel embedded in graph nodes;
507:- user-defined graph themes;
515:- The same pinned definition and interpreter produce identical stable node IDs,
519:- A changed workflow definition or interpreter cannot reuse the old topology
554:  target size, contrast, and assistive-technology fixtures for the graph,
560:  because a graph node exists.
563:  and reconciliation link; possession of a graph reference grants no access.
574:| Graph looks authoritative while stale | Show consistency/cursor state; refetch on gaps; never retain green certainty after invalidation |
575:| UI duplicates business rules | Server-owned closed projection mapping; architecture test forbids authority imports |
577:| Multiple runs are confused | Always show exact `RunId`, attempt, workflow digest/version, and explicit selector; auto-open only a unique server-linked current run |
579:| Large graph becomes unusable | Collapse supported groups, render visible elements, add search; qualify ELK only when real fixtures demand it |
581:| Upstream code is copied casually | Prefer libraries and original adapters; record provenance and license obligations for any copied fragment |
583:| Cached graph outlives canonical retention | Treat it as a disposable derived view; regenerate only from facts still legally available and preserve redaction/purge outcomes |
593:- A visual graph makes waiting, blocking, gate, permit, effect, and
604:- uses the graph library as the workflow interpreter;
613:The last point must be tested with users. A graph is justified when branching,
616:table. The graph prototype and table must use the same fixtures and be compared
641:- Define `topology_digest` with server-only canonicalization and golden
645:- Make the visual-state mapping total, server-owned, non-transitionable, and
652:- Treat terminal graphs as regenerated derived views under canonical retention,
660:  each deterministic run. The reconciled direction keeps a graph prototype and
664:  unnecessary: deltas support reconnect, while the graph is regenerated from
675:- DeepSeek stated that the maintained Dagre repository had not released since
677:  [`@dagrejs/dagre` v2.0.0](https://github.com/dagrejs/dagre/releases/tag/v2.0.0)
680:- Airflow using ELK does not contradict Dagre for a simple first graph. Argo,
681:  Kestra, and Dagster establish Dagre precedent; Airflow establishes the
682:  upgrade pattern when compound graphs and routing require ELK.
696:3. Run a user-facing graph/table prototype using synthetic, non-authoritative
699:   renderer, layout engine, dependency licenses, and quality thresholds.
702:6. Implement server projection tests before the visual component.
705:8. Do not claim runtime conformance until applicable readiness evidence passes.
707:## 19. Source and license register
712:| Source | Frozen revision or authoritative page | License / use |
714:| GitHub Actions workflow monitoring | [GitHub Docs](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui), accessed 2026-07-30 | Product behavior/documentation reference |
715:| GitHub Actions workflow model | [GitHub Docs](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows?learn=getting_started&learnproduct=actions), accessed 2026-07-30 | Product behavior/documentation reference |
716:| GitLab pipeline graph | [GitLab Docs](https://docs.gitlab.com/ci/pipelines/), accessed 2026-07-30 | Product behavior/documentation reference |
717:| Gitea workflow graph | [`e80a62f5552cad07bf79b2f31687cf5a9b93f1fc`](https://github.com/go-gitea/gitea/tree/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc) | MIT; code inspection only |
718:| Apache Airflow graph | [`f781f8b8785496d68c9d9ae725a004764bbc9f1d`](https://github.com/apache/airflow/tree/f781f8b8785496d68c9d9ae725a004764bbc9f1d) | Apache-2.0; code inspection only |
719:| Argo Workflows graph | [`d98d7b7d73d1b24dd7258153453ea612dbb70092`](https://github.com/argoproj/argo-workflows/tree/d98d7b7d73d1b24dd7258153453ea612dbb70092) | Apache-2.0; code inspection only |
720:| Kestra topology | [`e03a4f351328f294e67f62be60af0553401fad7a`](https://github.com/kestra-io/kestra/tree/e03a4f351328f294e67f62be60af0553401fad7a) | Apache-2.0; code inspection only |
721:| Dagster graph layout | [`014641bc1bdb71ea2c7f40371691103bbff5c9c7`](https://github.com/dagster-io/dagster/tree/014641bc1bdb71ea2c7f40371691103bbff5c9c7) | Apache-2.0; code inspection only |
722:| React Flow / XYFlow | [`360f5b13e2bc6899ea06b4be1a49b068d86926cf`](https://github.com/xyflow/xyflow/tree/360f5b13e2bc6899ea06b4be1a49b068d86926cf) and [official docs](https://reactflow.dev/) | MIT; candidate dependency, not adopted |
723:| Dagre | [DagreJS repository](https://github.com/dagrejs/dagre), inspected 2026-07-30 | MIT; candidate dependency, not adopted |
724:| ELK / elkjs | [ELK layered algorithm](https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html) and [elkjs](https://github.com/kieler/elkjs) | EPL-2.0; upgrade candidate requiring qualification |
725:| Dagu graph | [`3fd7eeff69e2df281cd8bd8f47348baf8d3462be`](https://github.com/dagu-org/dagu/tree/3fd7eeff69e2df281cd8bd8f47348baf8d3462be) | GPL-3.0; behavior observation only, no code reuse proposed |
726:| WCAG 2.2 | [W3C Recommendation](https://www.w3.org/TR/WCAG22/), accessed 2026-07-30 | Proposed accessibility baseline; not yet adopted by Ranex |
734:trustworthy graph needs. The safest proven implementation is a server-owned,
736:graph remains an explanation of authority, never authority itself.

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py | sed -n '1,280p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
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
/bin/bash -lc "nl -ba LICENSE-RANEX.md | sed -n '1,130p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	# Ranex Personal-Use Source License 1.0
     2	
     3	Copyright (c) 2026 Anthony Garces. All rights reserved.
     4	
     5	This is a source-available license. It is not an open-source license.
     6	
     7	## 1. Scope
     8	
     9	This license applies only to original Ranex code, documentation, configuration,
    10	artwork, and modifications owned by Anthony Garces (the "Ranex Material").
    11	
    12	It does not apply to Hermes Agent material or any other third-party material.
    13	Those portions remain governed by their own licenses. When Hermes Agent
    14	material is adopted in Phase 1, its MIT License is retained in `LICENSE`.
    15	
    16	## 2. Personal-use permission
    17	
    18	Subject to every condition below, an individual may view, copy, run, study, and
    19	privately modify the Ranex Material solely for personal learning,
    20	experimentation, or evaluation.
    21	
    22	This permission is personal, limited, non-exclusive, and non-transferable. All
    23	copyright, license, attribution, and source notices must remain intact.
    24	
    25	## 3. Restrictions
    26	
    27	Except for the limited GitHub-platform rights in section 4, and unless Anthony
    28	Garces gives prior written permission, you may not:
    29	
    30	1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
    31	   or otherwise provide the Ranex Material or a modified version to anyone;
    32	2. make the Ranex Material available through a public or shared repository,
    33	   download, package, service, hosted application, network endpoint, or device;
    34	3. use the Ranex Material for any commercial, business, employment,
    35	   professional, institutional, revenue-generating, or client purpose;
    36	4. use the Ranex Material to operate, support, develop, or improve a product,
    37	   service, organization, or business process;
    38	5. remove, hide, or alter a copyright, license, provenance, or attribution
    39	   notice;
    40	6. claim authorship or ownership of Ranex Material created by Anthony Garces,
    41	   or present that material as your own work;
    42	7. use the Ranex name, logo, or branding to imply endorsement, affiliation, or
    43	   ownership; or
    44	8. grant another person rights that this license does not grant to you.
    45	
    46	You may identify original changes that you created privately, but that does not
    47	give you ownership of the underlying Ranex Material or permission to
    48	redistribute the combined work.
    49	
    50	## 4. Public GitHub repository
    51	
    52	While the repository is public, GitHub's Terms of Service grant GitHub users
    53	limited permission to use, display, perform, and reproduce repository content
    54	through GitHub's service as its features allow, including by forking it. This
    55	license does not restrict those platform rights.
    56	
    57	Those platform permissions do not grant permission to redistribute the Ranex
    58	Material outside GitHub's service, use it for business, remove its notices, or
    59	claim it as your own.
    60	
    61	## 5. Ownership and third-party rights
    62	
    63	The Ranex Material is licensed, not sold. Anthony Garces retains all rights
    64	not expressly granted here.
    65	
    66	No term in this license reduces a right granted directly by the MIT License or
    67	another applicable third-party license. When a file contains both upstream
    68	material and original Ranex modifications, each portion remains governed by
    69	its applicable license.
    70	
    71	## 6. Termination
    72	
    73	Your permission under this license ends automatically when you violate it.
    74	After termination, you must stop using the Ranex Material and delete copies in
    75	your possession or control, except copies GitHub retains under its Terms of
    76	Service or copies the law requires you to preserve.
    77	
    78	## 7. No warranty
    79	
    80	THE RANEX MATERIAL IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    81	OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
    82	PURPOSE, TITLE, AND NON-INFRINGEMENT.
    83	
    84	TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE COPYRIGHT HOLDER WILL NOT BE LIABLE
    85	FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM THE RANEX MATERIAL OR
    86	ITS USE.
    87	
    88	## 8. Other rights
    89	
    90	This license does not limit fair use, fair dealing, or another right that
    91	applicable law does not allow a license to restrict.
    92	
    93	For redistribution, business use, sublicensing, or another exception, obtain
    94	prior written permission from Anthony Garces through the `anthonykewl20`
    95	GitHub account.

exec
/bin/bash -lc "rg -n 'def test_|integrity|journal|outbox|state|replay|crash|rollback|transaction|foreign_key|WAL|quick_check' .claude/worktrees/kernel-tracer/tests .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3:CREATE TABLE IF NOT EXISTS execution_state (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:5:    canonical_state_json TEXT NOT NULL,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:11:CREATE TABLE IF NOT EXISTS execution_journal (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:19:    previous_state_sha256 TEXT,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:20:    resulting_state_sha256 TEXT NOT NULL,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:21:    resulting_state_json TEXT NOT NULL,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:24:        REFERENCES execution_state(execution_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:28:        (previous_version = 0 AND previous_state_sha256 IS NULL)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:30:        (previous_version > 0 AND length(previous_state_sha256) = 64)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:32:    CHECK (length(resulting_state_sha256) = 64)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35:CREATE TABLE IF NOT EXISTS execution_outbox (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:43:        REFERENCES execution_journal(event_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:48:BEFORE UPDATE ON execution_journal
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:50:    SELECT RAISE(ABORT, 'execution_journal is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:53:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:54:BEFORE DELETE ON execution_journal
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:56:    SELECT RAISE(ABORT, 'execution_journal is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:59:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:60:BEFORE UPDATE ON execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:62:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:65:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:66:BEFORE DELETE ON execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:68:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:60:        "schema_version": "execution-state/v1",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:85:        raise ValueError("canonical execution state has unexpected fields")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:86:    if document["schema_version"] != "execution-state/v1":
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:87:        raise ValueError("unsupported execution state schema version")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:90:        raise ValueError("execution state version must be a positive integer")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:184:    """State, audit journal, and outbox committed in one SQLite transaction."""
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:196:        connection.execute("PRAGMA foreign_keys = ON")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:215:                SELECT execution_id, canonical_state_json, version, last_event_id
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:216:                FROM execution_state
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:221:        return None if row is None else self._decode_state_row(row)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:229:                SELECT execution_id, canonical_state_json, version, last_event_id
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:230:                FROM execution_state
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:236:                None if current_row is None else self._decode_state_row(current_row)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:238:            next_state = reduce_execution(current, event)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:239:            next_document = _execution_to_document(next_state)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:245:                    INSERT INTO execution_state(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:247:                        canonical_state_json,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:254:                        str(next_state.execution_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:256:                        next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:257:                        str(next_state.last_event_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:258:                        next_state.updated_at,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:265:                previous_json = str(current_row["canonical_state_json"])
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:269:                    UPDATE execution_state
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:270:                    SET canonical_state_json = ?,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:276:                      AND canonical_state_json = ?
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:280:                        next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:281:                        str(next_state.last_event_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:282:                        next_state.updated_at,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:283:                        str(next_state.execution_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:303:                INSERT INTO execution_journal(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:310:                    previous_state_sha256,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:311:                    resulting_state_sha256,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:312:                    resulting_state_json,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:321:                    next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:330:            outbox_document = {
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:331:                "schema_version": "execution-outbox/v1",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:335:                "aggregate_version": next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:341:                INSERT INTO execution_outbox(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:352:                    next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:353:                    canonical_json(outbox_document),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:358:            return next_state
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:360:            if connection.in_transaction:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:366:    def count_journal_entries(self, execution_id: Identity) -> int:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:367:        return self._count_rows("execution_journal", execution_id)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:369:    def count_outbox_entries(self, execution_id: Identity) -> int:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:370:        return self._count_rows("execution_outbox", execution_id)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:374:        if table not in {"execution_journal", "execution_outbox"}:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390:    def _decode_state_row(row: sqlite3.Row) -> Execution:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:391:        raw = str(row["canonical_state_json"])
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:396:                "canonical execution state is not JSON"
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:400:                "execution state is not canonically serialized"
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:403:            state = _execution_from_document(document)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:406:                "canonical execution state is invalid"
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:408:        if int(row["version"]) != state.version:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:410:                "relational version disagrees with canonical state version"
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:412:        if str(row["last_event_id"]) != str(state.last_event_id):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:414:                "relational last event disagrees with canonical state"
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:416:        if str(row["execution_id"]) != str(state.execution_id):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:418:                "relational identity disagrees with canonical state identity"
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:420:        return state
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:37:def test_loader_parses_closed_secure_policy_contract() -> None:
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:48:def test_loader_rejects_duplicate_yaml_keys() -> None:
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:58:def test_loader_rejects_unsafe_yaml_tag() -> None:
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:68:def test_loader_returns_digest_of_exact_policy_bytes(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31:def test_failure_between_journal_and_outbox_leaves_no_partial_state(
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:34:    database_path = tmp_path / "crash-boundary.sqlite3"
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:45:            workflow_request_ref="workflow-request:sha256:crash",
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:52:            CREATE TRIGGER simulate_crash_before_outbox
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:53:            BEFORE INSERT ON execution_outbox
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:56:                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:61:    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:68:                readiness_snapshot_ref="snapshot:sha256:crash-ready",
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:77:    assert store.count_journal_entries(RUN_ID) == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:78:    assert store.count_outbox_entries(RUN_ID) == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:84:                (SELECT COUNT(*) FROM execution_state
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:86:                (SELECT COUNT(*) FROM execution_journal
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:88:                (SELECT COUNT(*) FROM execution_outbox
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:379:def test_kernel_imports_follow_layering_and_have_no_hermes_reachability() -> None:
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:384:def test_kernel_import_graph_is_acyclic() -> None:
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:389:def test_checker_rejects_private_cross_context_import(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:405:def test_checker_rejects_relative_private_cross_context_import(
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:423:def test_checker_rejects_hermes_import(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:434:def test_checker_rejects_dynamic_hermes_import(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:448:def test_checker_rejects_domain_environment_dependency(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:462:def test_checker_allows_api_to_expose_immutable_domain_types(
.claude/worktrees/kernel-tracer/tests/architecture/test_kernel_imports.py:476:def test_importing_entire_kernel_graph_loads_no_hermes_dependency() -> None:
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:103:def test_pep_fails_closed_when_policy_adapter_raises() -> None:
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:113:def test_pep_fails_closed_on_malformed_policy_result() -> None:
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:123:def test_deterministic_policy_adapter_and_pep_produce_same_decision() -> None:
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:138:def test_pep_denies_when_deterministic_policy_has_no_evidence() -> None:
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:153:def test_deterministic_policy_adapter_rejects_noncanonical_digest() -> None:
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:11:def test_initial_migration_is_repeatable_and_records_schema_version(
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:35:        "execution_state",
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:36:        "execution_journal",
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:37:        "execution_outbox",
.claude/worktrees/kernel-tracer/tests/unit/foundation/domain/test_canonical.py:10:def test_canonical_json_is_compact_sorted_and_unicode_preserving() -> None:
.claude/worktrees/kernel-tracer/tests/unit/foundation/domain/test_canonical.py:23:def test_canonical_json_rejects_non_finite_numbers(value: float) -> None:
.claude/worktrees/kernel-tracer/tests/unit/foundation/domain/test_identity.py:10:def test_identity_parses_canonical_prefixed_uuid7() -> None:
.claude/worktrees/kernel-tracer/tests/unit/foundation/domain/test_identity.py:27:def test_identity_rejects_wrong_kind_or_noncanonical_value(
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:12:    replay_execution,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:24:def test_replay_reproduces_identical_final_state_and_version() -> None:
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:62:    replayed = replay_execution(events)
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:64:    assert replayed == direct
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:65:    assert replayed.status is ExecutionStatus.SUCCEEDED
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:66:    assert replayed.version == len(events) == 4
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:42:def test_verifier_hashes_safe_descriptor_and_marks_record_verified(
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:60:def test_verifier_rejects_symlink_and_digest_mismatch(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:80:def test_verifier_rejects_paths_outside_trusted_root(
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_application_control.py:20:def test_application_control_decision_is_pure_and_deterministic() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_application_control.py:36:def test_application_control_decision_denies_malformed_facts() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_application_control.py:51:def test_application_control_request_rejects_noncanonical_actor_order() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:89:def test_gate_controller_fails_closed_when_evidence_is_missing() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:98:def test_gate_controller_accepts_verified_exact_subject_evidence() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:108:def test_gate_controller_rejects_conflict_and_nonindependent_producer() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:123:def test_gate_controller_rejects_wrong_subject_and_unverified_artifact() -> None:
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:79:def test_transition_commits_canonical_state_version_journal_and_outbox_together(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:94:        state_row = connection.execute(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:96:            SELECT canonical_state_json, version, last_event_id
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:97:            FROM execution_state
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:102:        journal_rows = connection.execute(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:105:                   event_json, resulting_state_json
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:106:            FROM execution_journal
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:110:        outbox_rows = connection.execute(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:113:            FROM execution_outbox
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:118:    assert state_row is not None
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:119:    state_document = json.loads(state_row["canonical_state_json"])
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:120:    assert state_row["canonical_state_json"] == canonical_json(state_document)
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:121:    assert state_row["version"] == state_document["version"] == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:122:    assert state_row["last_event_id"] == str(event_id(2))
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:126:        for row in journal_rows
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:133:        and row["resulting_state_json"]
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:134:        == canonical_json(json.loads(row["resulting_state_json"]))
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:135:        for row in journal_rows
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:138:    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:144:        for row in outbox_rows
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:148:def test_journal_is_database_enforced_append_only(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:156:            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:158:            connection.execute("DELETE FROM execution_journal")
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:161:def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:170:    assert store.count_journal_entries(RUN_ID) == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:171:    assert store.count_outbox_entries(RUN_ID) == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:174:def test_load_rejects_relational_and_canonical_version_disagreement(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:181:            "UPDATE execution_state SET version = 99 WHERE execution_id = ?",
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:192:def test_load_rejects_relational_and_canonical_identity_disagreement(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:200:            SELECT canonical_state_json
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:201:            FROM execution_state
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:216:            UPDATE execution_state
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:217:            SET canonical_state_json = ?
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:230:def test_concurrent_same_version_transitions_have_one_cas_winner(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:249:    assert store.count_journal_entries(RUN_ID) == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:250:    assert store.count_outbox_entries(RUN_ID) == 2
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:15:def test_hash_chain_ledger_appends_and_verifies(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:32:def test_hash_chain_ledger_detects_edit_and_refuses_append(
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:50:def test_hash_chain_idempotency_key_cannot_change_record(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:53:    replay = ledger.append_once({"decision": "PASS"}, key="request-1")
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:55:    assert replay == first
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:19:def test_work_transition_request_owns_work_item_transition_subject() -> None:
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:37:def test_work_transition_request_rejects_noop_and_bad_commit() -> None:
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:56:def test_work_transition_request_rejects_noncanonical_actor_order() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:78:def test_creation_is_a_reducer_transition_from_no_state() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:79:    state = reduce_execution(None, created())
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:81:    assert state.execution_id == RUN_ID
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:82:    assert state.work_item_id == WORK_ITEM_ID
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:83:    assert state.status is ExecutionStatus.PROPOSED
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:84:    assert state.version == 1
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:85:    assert state.last_event_id == transition_id(1)
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:88:def test_reducer_is_deterministic_and_does_not_mutate_input() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:103:def test_block_and_unblock_restore_the_recorded_prior_status() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:140:def test_illegal_transition_fails_without_changing_state() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:162:def test_reducer_rejects_wrong_execution_and_stale_version() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:175:def test_event_type_cannot_impersonate_a_different_legal_edge() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:177:    ready_state = reduce_execution(proposed, ready())
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:178:    running = reduce_execution(ready_state, started())
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:193:            ready_state,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:206:def test_registered_execution_transition_set_is_exhaustive() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:236:    ("build_state", "event_type", "target"),
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:251:def test_reducer_computes_each_non_blocking_transition_family(
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:252:    build_state: str,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:256:    states = _states_for_transition_examples()
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:257:    state = states[build_state]
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:258:    event = _event_for(event_type, state.version)
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:260:    assert reduce_execution(state, event).status is target
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:263:def _states_for_transition_examples() -> dict[str, object]:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:265:    ready_state = reduce_execution(proposed, ready())
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:266:    running = reduce_execution(ready_state, started())
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:290:        "ready": ready_state,

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '210,430p'" in /home/soultransit/devtony/ranex
exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py | sed -n '1,250p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   210	    def load(self, execution_id: Identity) -> Execution | None:
   211	        self._require_run_id(execution_id)
   212	        with closing(self._connect()) as connection:
   213	            row = connection.execute(
   214	                """
   215	                SELECT execution_id, canonical_state_json, version, last_event_id
   216	                FROM execution_state
   217	                WHERE execution_id = ?
   218	                """,
   219	                (str(execution_id),),
   220	            ).fetchone()
   221	        return None if row is None else self._decode_state_row(row)
   222	
   223	    def append(self, event: ExecutionEvent) -> Execution:
   224	        connection = self._connect()
   225	        connection.execute("BEGIN IMMEDIATE")
   226	        try:
   227	            current_row = connection.execute(
   228	                """
   229	                SELECT execution_id, canonical_state_json, version, last_event_id
   230	                FROM execution_state
   231	                WHERE execution_id = ?
   232	                """,
   233	                (str(event.execution_id),),
   234	            ).fetchone()
   235	            current = (
   236	                None if current_row is None else self._decode_state_row(current_row)
   237	            )
   238	            next_state = reduce_execution(current, event)
   239	            next_document = _execution_to_document(next_state)
   240	            next_json = canonical_json(next_document)
   241	
   242	            if current is None:
   243	                connection.execute(
   244	                    """
   245	                    INSERT INTO execution_state(
   246	                        execution_id,
   247	                        canonical_state_json,
   248	                        version,
   249	                        last_event_id,
   250	                        updated_at
   251	                    ) VALUES (?, ?, ?, ?, ?)
   252	                    """,
   253	                    (
   254	                        str(next_state.execution_id),
   255	                        next_json,
   256	                        next_state.version,
   257	                        str(next_state.last_event_id),
   258	                        next_state.updated_at,
   259	                    ),
   260	                )
   261	                previous_json = None
   262	                previous_version = 0
   263	            else:
   264	                assert current_row is not None
   265	                previous_json = str(current_row["canonical_state_json"])
   266	                previous_version = current.version
   267	                cursor = connection.execute(
   268	                    """
   269	                    UPDATE execution_state
   270	                    SET canonical_state_json = ?,
   271	                        version = ?,
   272	                        last_event_id = ?,
   273	                        updated_at = ?
   274	                    WHERE execution_id = ?
   275	                      AND version = ?
   276	                      AND canonical_state_json = ?
   277	                    """,
   278	                    (
   279	                        next_json,
   280	                        next_state.version,
   281	                        str(next_state.last_event_id),
   282	                        next_state.updated_at,
   283	                        str(next_state.execution_id),
   284	                        current.version,
   285	                        previous_json,
   286	                    ),
   287	                )
   288	                if cursor.rowcount != 1:
   289	                    raise ConcurrentExecutionWriteError(
   290	                        "canonical execution compare-and-swap failed"
   291	                    )
   292	
   293	            event_document = _event_to_document(event)
   294	            event_json = canonical_json(event_document)
   295	            resulting_digest = canonical_sha256(next_document)
   296	            previous_digest = (
   297	                None
   298	                if previous_json is None
   299	                else canonical_sha256(json.loads(previous_json))
   300	            )
   301	            connection.execute(
   302	                """
   303	                INSERT INTO execution_journal(
   304	                    event_id,
   305	                    execution_id,
   306	                    event_type,
   307	                    previous_version,
   308	                    resulting_version,
   309	                    event_json,
   310	                    previous_state_sha256,
   311	                    resulting_state_sha256,
   312	                    resulting_state_json,
   313	                    recorded_at
   314	                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   315	                """,
   316	                (
   317	                    str(event.event_id),
   318	                    str(event.execution_id),
   319	                    type(event).__name__,
   320	                    previous_version,
   321	                    next_state.version,
   322	                    event_json,
   323	                    previous_digest,
   324	                    resulting_digest,
   325	                    next_json,
   326	                    event.occurred_at,
   327	                ),
   328	            )
   329	
   330	            outbox_document = {
   331	                "schema_version": "execution-outbox/v1",
   332	                "event_id": str(event.event_id),
   333	                "event_type": type(event).__name__,
   334	                "execution_id": str(event.execution_id),
   335	                "aggregate_version": next_state.version,
   336	                "occurred_at": event.occurred_at,
   337	                "event": event_document,
   338	            }
   339	            connection.execute(
   340	                """
   341	                INSERT INTO execution_outbox(
   342	                    event_id,
   343	                    execution_id,
   344	                    aggregate_version,
   345	                    payload_json,
   346	                    created_at
   347	                ) VALUES (?, ?, ?, ?, ?)
   348	                """,
   349	                (
   350	                    str(event.event_id),
   351	                    str(event.execution_id),
   352	                    next_state.version,
   353	                    canonical_json(outbox_document),
   354	                    event.occurred_at,
   355	                ),
   356	            )
   357	            connection.execute("COMMIT")
   358	            return next_state
   359	        except BaseException:
   360	            if connection.in_transaction:
   361	                connection.execute("ROLLBACK")
   362	            raise
   363	        finally:
   364	            connection.close()
   365	
   366	    def count_journal_entries(self, execution_id: Identity) -> int:
   367	        return self._count_rows("execution_journal", execution_id)
   368	
   369	    def count_outbox_entries(self, execution_id: Identity) -> int:
   370	        return self._count_rows("execution_outbox", execution_id)
   371	
   372	    def _count_rows(self, table: str, execution_id: Identity) -> int:
   373	        self._require_run_id(execution_id)
   374	        if table not in {"execution_journal", "execution_outbox"}:
   375	            raise ValueError("unsupported execution table")
   376	        with closing(self._connect()) as connection:
   377	            row = connection.execute(
   378	                f"SELECT COUNT(*) AS count FROM {table} WHERE execution_id = ?",
   379	                (str(execution_id),),
   380	            ).fetchone()
   381	        assert row is not None
   382	        return int(row["count"])
   383	
   384	    @staticmethod
   385	    def _require_run_id(execution_id: Identity) -> None:
   386	        if not isinstance(execution_id, Identity) or execution_id.prefix != "run":
   387	            raise ValueError("execution_id must be a canonical run identity")
   388	
   389	    @staticmethod
   390	    def _decode_state_row(row: sqlite3.Row) -> Execution:
   391	        raw = str(row["canonical_state_json"])
   392	        try:
   393	            document = json.loads(raw)
   394	        except json.JSONDecodeError as exc:
   395	            raise ExecutionPersistenceIntegrityError(
   396	                "canonical execution state is not JSON"
   397	            ) from exc
   398	        if not isinstance(document, dict) or canonical_json(document) != raw:
   399	            raise ExecutionPersistenceIntegrityError(
   400	                "execution state is not canonically serialized"
   401	            )
   402	        try:
   403	            state = _execution_from_document(document)
   404	        except (TypeError, ValueError) as exc:
   405	            raise ExecutionPersistenceIntegrityError(
   406	                "canonical execution state is invalid"
   407	            ) from exc
   408	        if int(row["version"]) != state.version:
   409	            raise ExecutionPersistenceIntegrityError(
   410	                "relational version disagrees with canonical state version"
   411	            )
   412	        if str(row["last_event_id"]) != str(state.last_event_id):
   413	            raise ExecutionPersistenceIntegrityError(
   414	                "relational last event disagrees with canonical state"
   415	            )
   416	        if str(row["execution_id"]) != str(state.execution_id):
   417	            raise ExecutionPersistenceIntegrityError(
   418	                "relational identity disagrees with canonical state identity"
   419	            )
   420	        return state

 succeeded in 0ms:
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
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py | sed -n '70,270p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
    70	
    71	
    72	@pytest.fixture
    73	def store(database_path: Path) -> SQLiteExecutionStore:
    74	    execution_store = SQLiteExecutionStore(database_path)
    75	    execution_store.initialize()
    76	    return execution_store
    77	
    78	
    79	def test_transition_commits_canonical_state_version_journal_and_outbox_together(
    80	    store: SQLiteExecutionStore,
    81	    database_path: Path,
    82	) -> None:
    83	    proposed = store.append(create_event())
    84	    ready = store.append(ready_event())
    85	
    86	    assert proposed.status is ExecutionStatus.PROPOSED
    87	    assert proposed.version == 1
    88	    assert ready.status is ExecutionStatus.READY
    89	    assert ready.version == 2
    90	    assert store.load(RUN_ID) == ready
    91	
    92	    with sqlite3.connect(database_path) as connection:
    93	        connection.row_factory = sqlite3.Row
    94	        state_row = connection.execute(
    95	            """
    96	            SELECT canonical_state_json, version, last_event_id
    97	            FROM execution_state
    98	            WHERE execution_id = ?
    99	            """,
   100	            (str(RUN_ID),),
   101	        ).fetchone()
   102	        journal_rows = connection.execute(
   103	            """
   104	            SELECT event_id, previous_version, resulting_version,
   105	                   event_json, resulting_state_json
   106	            FROM execution_journal
   107	            ORDER BY sequence
   108	            """
   109	        ).fetchall()
   110	        outbox_rows = connection.execute(
   111	            """
   112	            SELECT event_id, aggregate_version, payload_json
   113	            FROM execution_outbox
   114	            ORDER BY sequence
   115	            """
   116	        ).fetchall()
   117	
   118	    assert state_row is not None
   119	    state_document = json.loads(state_row["canonical_state_json"])
   120	    assert state_row["canonical_state_json"] == canonical_json(state_document)
   121	    assert state_row["version"] == state_document["version"] == 2
   122	    assert state_row["last_event_id"] == str(event_id(2))
   123	
   124	    assert [
   125	        (row["event_id"], row["previous_version"], row["resulting_version"])
   126	        for row in journal_rows
   127	    ] == [
   128	        (str(event_id(1)), 0, 1),
   129	        (str(event_id(2)), 1, 2),
   130	    ]
   131	    assert all(
   132	        row["event_json"] == canonical_json(json.loads(row["event_json"]))
   133	        and row["resulting_state_json"]
   134	        == canonical_json(json.loads(row["resulting_state_json"]))
   135	        for row in journal_rows
   136	    )
   137	
   138	    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
   139	        (str(event_id(1)), 1),
   140	        (str(event_id(2)), 2),
   141	    ]
   142	    assert all(
   143	        row["payload_json"] == canonical_json(json.loads(row["payload_json"]))
   144	        for row in outbox_rows
   145	    )
   146	
   147	
   148	def test_journal_is_database_enforced_append_only(
   149	    store: SQLiteExecutionStore,
   150	    database_path: Path,
   151	) -> None:
   152	    store.append(create_event())
   153	
   154	    with sqlite3.connect(database_path) as connection:
   155	        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
   156	            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
   157	        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
   158	            connection.execute("DELETE FROM execution_journal")
   159	
   160	
   161	def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
   162	    store: SQLiteExecutionStore,
   163	) -> None:
   164	    store.append(create_event())
   165	    store.append(ready_event())
   166	
   167	    with pytest.raises(ValueError, match="expected version"):
   168	        store.append(ready_event())
   169	
   170	    assert store.count_journal_entries(RUN_ID) == 2
   171	    assert store.count_outbox_entries(RUN_ID) == 2
   172	
   173	
   174	def test_load_rejects_relational_and_canonical_version_disagreement(
   175	    store: SQLiteExecutionStore,
   176	    database_path: Path,
   177	) -> None:
   178	    store.append(create_event())
   179	    with sqlite3.connect(database_path) as connection:
   180	        connection.execute(
   181	            "UPDATE execution_state SET version = 99 WHERE execution_id = ?",
   182	            (str(RUN_ID),),
   183	        )
   184	
   185	    with pytest.raises(
   186	        ExecutionPersistenceIntegrityError,
   187	        match="version disagrees",
   188	    ):
   189	        store.load(RUN_ID)
   190	
   191	
   192	def test_load_rejects_relational_and_canonical_identity_disagreement(
   193	    store: SQLiteExecutionStore,
   194	    database_path: Path,
   195	) -> None:
   196	    store.append(create_event())
   197	    with sqlite3.connect(database_path) as connection:
   198	        raw = connection.execute(
   199	            """
   200	            SELECT canonical_state_json
   201	            FROM execution_state
   202	            WHERE execution_id = ?
   203	            """,
   204	            (str(RUN_ID),),
   205	        ).fetchone()
   206	        assert raw is not None
   207	        document = json.loads(raw[0])
   208	        document["execution_id"] = str(
   209	            Identity.parse(
   210	                "run_01890f47-25a1-7e09-98b3-5f5f6bb25af7",
   211	                expected_prefix="run",
   212	            )
   213	        )
   214	        connection.execute(
   215	            """
   216	            UPDATE execution_state
   217	            SET canonical_state_json = ?
   218	            WHERE execution_id = ?
   219	            """,
   220	            (canonical_json(document), str(RUN_ID)),
   221	        )
   222	
   223	    with pytest.raises(
   224	        ExecutionPersistenceIntegrityError,
   225	        match="identity disagrees",
   226	    ):
   227	        store.load(RUN_ID)
   228	
   229	
   230	def test_concurrent_same_version_transitions_have_one_cas_winner(
   231	    store: SQLiteExecutionStore,
   232	) -> None:
   233	    store.append(create_event())
   234	    barrier = Barrier(2)
   235	
   236	    def attempt() -> Execution | Exception:
   237	        barrier.wait()
   238	        try:
   239	            return store.append(ready_event())
   240	        except Exception as exc:
   241	            return exc
   242	
   243	    with ThreadPoolExecutor(max_workers=2) as executor:
   244	        results = tuple(executor.map(lambda _index: attempt(), range(2)))
   245	
   246	    assert sum(isinstance(result, Execution) for result in results) == 1
   247	    assert sum(isinstance(result, Exception) for result in results) == 1
   248	    assert store.load(RUN_ID).version == 2  # type: ignore[union-attr]
   249	    assert store.count_journal_entries(RUN_ID) == 2
   250	    assert store.count_outbox_entries(RUN_ID) == 2

exec
/bin/bash -lc "nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '1,240p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	# Deterministic run-graph visualization research and architecture proposal
     2	
     3	| Field | Value |
     4	|---|---|
     5	| Research ID | `RES-EXEC-GRAPH-001` |
     6	| Version | `0.2.0` |
     7	| Date | 2026-07-30 |
     8	| Status | **REVIEWED DRAFT RESEARCH PROPOSAL — NON-NORMATIVE; NOT IMPLEMENTATION AUTHORITY** |
     9	| Question | How should Ranex show the deterministic workflow of a governed run started for a Kanban work item? |
    10	| Ranex subject | `bootstrap/pre-upstream@a573502a87e0599cf6e5f9456c348bf1a7686382` |
    11	| Primary architecture | [`ARCH-RANEX-001` v2.10.0](../architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md) |
    12	| Decision effect | None. Adoption requires an accepted RFC/ADR, dependency qualification, schemas, tests, and applicable readiness gates |
    13	| Reviewed draft | v0.1.0, SHA-256 `2b5e4476defd01ece67bbf0f62b60dcd47a09f5932eeee55ae0d5ae32257dc0d` |
    14	| Advisory model review | DeepSeek V4 Pro and HY3 both returned `FIT_WITH_CHANGES`; findings are reconciled in §17 |
    15	| Runtime evidence | None; Ranex runtime remains `NOT_ASSESSED` |
    16	
    17	## 1. Answer in one paragraph
    18	
    19	This feature is a good conceptual fit for Ranex if it is implemented as a
    20	**read-only visualization of one already-governed run**, not as a second
    21	workflow engine or a source of state. Open a Kanban work item, select one of its
    22	runs, and display the immutable workflow topology with live status overlaid on
    23	its nodes. The server, inside the `governed_execution` boundary, derives a
    24	versioned `ExecutionGraphProjection`; the browser renders that projection and
    25	never infers transitions, evaluates rules, or advances the work item. For a
    26	React dashboard, the leading implementation candidate is
    27	[`@xyflow/react`](https://github.com/xyflow/xyflow) with
    28	[`@dagrejs/dagre`](https://github.com/dagrejs/dagre) for the initial
    29	left-to-right layout. Airflow, Argo Workflows, Gitea, GitLab, Kestra, and
    30	Dagster demonstrate the underlying pattern in production open-source systems.
    31	An ordered/table presentation of the same projection remains an equal,
    32	non-spatial way to inspect every run.
    33	
    34	## 2. What, when, and where
    35	
    36	### 2.1 What the user sees
    37	
    38	A run graph answers five questions without requiring the user to understand
    39	Ranex internals:
    40	
    41	1. What process was selected for this run?
    42	2. Which step is active now?
    43	3. What already passed, failed, or was not taken?
    44	4. Where is the run waiting or blocked, and why?
    45	5. What evidence, rule, decision, permit, effect, or reconciliation record
    46	   supports that state?
    47	
    48	The main graph stays simple. A node shows an icon, short name, state, duration,
    49	and attempt count. Selecting it opens a details drawer with reason codes and
    50	opaque references to evidence, rules, decisions, logs, artifacts, permits, and
    51	effects.
    52	
    53	### 2.2 When it appears
    54	
    55	The feature is used:
    56	
    57	- after a governed run has been requested for a Kanban work item;
    58	- while that run is `READY`, `RUNNING`, `WAITING`, or `BLOCKED`;
    59	- after it reaches `SUCCEEDED`, `FAILED`, or `CANCELLED`, as an audit and
    60	  debugging record; and
    61	- on reconnect, when the user needs to establish whether the displayed state is
    62	  current.
    63	
    64	There can be many runs for one work item. The server must identify eligible or
    65	active runs and the user must be able to select the exact run. The browser must
    66	not silently equate “newest” with “authoritative.”
    67	
    68	If exactly one current run is explicitly linked by the server-owned work-item
    69	projection, **View execution** may open that exact `RunId`. If there is no
    70	unique current link, the action opens the run selector. Creation time alone is
    71	never a default-selection rule.
    72	
    73	### 2.3 Where it lives
    74	
    75	The proposed dashboard journey is:
    76	
    77	```text
    78	Kanban board
    79	  -> open work-item card
    80	  -> Runs / Execution tab
    81	  -> select exact RunId
    82	  -> read-only graph
    83	  -> select node for evidence and diagnostics
    84	```
    85	
    86	The board card should show only a compact run summary and a
    87	**View execution** action. A full graph inside every card would make the board
    88	unusable and would blur `WorkItemStatus` with `RunStatus`.
    89	
    90	The proposed UI home is the architecture's target
    91	`apps/web-dashboard/src/features/runs/` boundary; that directory does not yet
    92	exist in this branch. The dashboard framework is still an adoption decision.
    93	The projection and API proposed here are framework-independent.
    94	
    95	## 3. The simple user-facing graph
    96	
    97	The following is an illustrative rendering, not a new workflow definition and
    98	not a state machine:
    99	
   100	```mermaid
   101	flowchart LR
   102	    A["Prepare inputs<br/>SUCCEEDED"] --> B["Agent activity<br/>RUNNING"]
   103	    B --> C{"Evidence gate<br/>NOT_STARTED"}
   104	    C -->|PASS| D["Human decision<br/>WAITING"]
   105	    C -->|FAIL / UNKNOWN| X["Blocked<br/>reason + evidence"]
   106	    D --> E["Authorized effect<br/>NOT_STARTED"]
   107	    E --> F["Reconcile outcome<br/>NOT_STARTED"]
   108	    F --> G["Run complete<br/>NOT_STARTED"]
   109	```
   110	
   111	The same run still belongs to a separately governed work item:
   112	
   113	```text
   114	WorkItemStatus = IN_PROGRESS       RunStatus = RUNNING
   115	         work_management       governed_execution
   116	```
   117	
   118	A run becoming `SUCCEEDED` must not move the work item. The normal
   119	work-management transition still requires its own exact evidence, gate, and
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
   146	- evaluate a gate or rule in the browser;
   147	- infer that a path was skipped merely because another path is active;
   148	- turn missing, conflicting, stale, or malformed data into a green state;
   149	- mutate the workflow through drag-and-drop;
   150	- issue a permit or invoke an effect;
   151	- automatically transition the Kanban card; or
   152	- treat a Hermes session, worker process, or provider response as canonical
   153	  run state.
   154	
   155	## 5. Prior art: the wheel already exists
   156	
   157	### 5.1 Product behavior
   158	
   159	[GitHub Actions](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui)
   160	generates a real-time graph for each workflow run and lets a user inspect job
   161	and step status and logs. Its workflow files define jobs and dependency edges,
   162	and a run uses a particular workflow revision. The transferable idea is not
   163	GitHub's private implementation; it is the separation of a versioned workflow
   164	definition from one live run of that definition.
   165	
   166	[GitLab CI/CD](https://docs.gitlab.com/ci/pipelines/) offers both stage and
   167	dependency views. Its documented UX includes fan-out/fan-in graphs, grouped
   168	similar jobs, expand/collapse behavior, visible failure reasons, and
   169	click-through logs. Those are useful interaction precedents, particularly for
   170	large or repeated graphs.
   171	
   172	### 5.2 Open-source implementations
   173	
   174	| System | Proven implementation pattern | What Ranex should learn | License posture |
   175	|---|---|---|---|
   176	| [Gitea](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.vue) | Native SVG workflow graph with pan/zoom, status cards, duration, click-through details, grouped jobs, and path highlighting | Closest open implementation to the requested GitHub Actions experience; its [typed graph model](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.utils.ts) and [tests](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.utils.test.ts) are valuable test references. The component is Vue; it is a behavior precedent, not a React reuse candidate | MIT; copied code would require preserving its notice |
   177	| [Apache Airflow](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx) | React Flow graph, ELK layout, generated API queries, and a streamed task-status overlay | Strongest direct precedent for a React implementation; it lays out structure separately, then merges live task instances without recalculating topology | Apache-2.0; use the pattern or comply with attribution/NOTICE duties for copied code |
   178	| [Argo Workflows](https://github.com/argoproj/argo-workflows/blob/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/widgets/workflow-graph.tsx) | Watched workflow status plus a DAG viewer; [Dagre computes LR/TB coordinates](https://github.com/argoproj/argo-workflows/blob/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/shared/components/graph/pretty-layout.ts) | Dagre is sufficient for a mature workflow product's straightforward DAG view | Apache-2.0 |
   179	| [Kestra](https://github.com/kestra-io/kestra/tree/e03a4f351328f294e67f62be60af0553401fad7a/ui/packages/topology) | Reusable Vue Flow topology package with Dagre, custom nodes/edges, collapsing, orientation, fit/zoom, and execution progress | Confirms that a flow renderer plus Dagre works beyond React and can remain a reusable presentation package | Apache-2.0 |
   180	| [Dagster](https://github.com/dagster-io/dagster/blob/014641bc1bdb71ea2c7f40371691103bbff5c9c7/js_modules/dagster-ui/packages/ui-core/src/graph/layout.ts) | Dagre-backed layout with a custom SVG viewport, ports, parent graphs, pan/zoom, and keyboard navigation | A custom renderer is possible, but its code and accessibility burden are larger than Ranex needs for the first slice | Apache-2.0 |
   181	| [Dagu](https://github.com/dagu-org/dagu/blob/3fd7eeff69e2df281cd8bd8f47348baf8d3462be/ui/src/features/dags/components/visualization/Graph.tsx) | Mermaid strings rebuilt with runtime status classes and interaction hooks | Useful evidence for a very small implementation, but repeated Mermaid rendering and DOM patching are a weaker live-UI foundation | GPL-3.0; do not copy into Ranex without a deliberate compatibility decision |
   182	
   183	This is enough evidence to avoid inventing a graph framework or importing
   184	another workflow engine. Ranex needs a small projection adapter and renderer,
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
   201	graph is laid out.” It also renders only visible elements and removes a minimap
   202	for very large graphs. Gitea supplies useful algorithms and tests for
   203	topological levels, transitive-edge reduction, grouping, cycles, stable paths,
   204	and ancestor/descendant highlighting.
   205	
   206	## 7. Proposed Ranex architecture
   207	
   208	```mermaid
   209	flowchart LR
   210	    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
   211	    A["governed_execution<br/>committed current rows + journal facts"]
   212	    P["ExecutionGraphProjection builder<br/>server-owned, versioned, deterministic"]
   213	    S["GET snapshot<br/>topology + current state"]
   214	    E["SSE status deltas<br/>cursor + expected version"]
   215	    U["Read-only dashboard graph<br/>React Flow + Dagre candidate"]
   216	    D["Node detail drawer<br/>references, reasons, logs"]
   217	
   218	    W --> P
   219	    A --> P
   220	    P --> S
   221	    P --> E
   222	    S --> U
   223	    E --> U
   224	    U --> D
   225	```
   226	
   227	### 7.1 Authority boundary
   228	
   229	`ExecutionGraphProjection` is an immutable application query/view owned by
   230	`governed_execution`. It joins:
   231	
   232	- the exact pinned workflow definition;
   233	- current committed Run, Activity, Gate, Permit, Effect, and reconciliation
   234	  facts;
   235	- safe references to separately owned policy, assurance, artifact, and human
   236	  decision records; and
   237	- projection metadata that lets a client detect stale, missing, or reordered
   238	  updates.
   239	
   240	The projection is not a new aggregate, workflow interpreter, or event store.

exec
/bin/bash -lc "nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '240,520p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   240	The projection is not a new aggregate, workflow interpreter, or event store.
   241	The dashboard receives facts already interpreted by the owning server
   242	boundary. It must not replay raw events to discover canonical state.
   243	
   244	Before implementation, an RFC/ADR must register the projection as a
   245	`governed_execution` query capability, its schema under `schemas/execution/`,
   246	its generated client/server contracts, and a fitness test that prevents
   247	`work_management` or the dashboard from publishing a competing execution
   248	truth.
   249	
   250	### 7.2 Deterministic topology contract
   251	
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
   271	stable edge IDs, sources, targets, kinds, and defined choice conditions. It
   272	excludes all run status, timestamps, durations, labels localized for display,
   273	viewport state, layout coordinates, and client theme data. The exact closed
   274	field set requires a versioned schema and golden fixtures before adoption.
   275	
   276	For the same pinned definition and supported interpreter version:
   277	
   278	- node and edge identity is identical;
   279	- canonical ordering is identical;
   280	- the topology digest is identical;
   281	- deterministic-choice alternatives exist in the definition before execution;
   282	- live state changes never move, add, or delete a node; and
   283	- a topology mismatch is visible and triggers a complete refetch.
   284	
   285	Dagre output also depends on node insertion order and library behavior.
   286	Therefore Ranex must sort canonical inputs and release-pin the layout package.
   287	
   288	Dynamic graph mutation is out of scope until the workflow architecture
   289	formally defines it. An unknown node or edge is a visible unsupported/unknown
   290	condition, never an invitation for the browser to improvise topology.
   291	
   292	### 7.3 Proposed projection shape
   293	
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
   331	The canonical source axis/value is present for explanation and diagnostics. The
   332	client must not map it to color, eligibility, traversal, or visual state; those
   333	are supplied by the server's generated projection contract.
   334	
   335	## 8. Rules, gates, and process nodes
   336	
   337	Rendering every rule as a node would turn even a small run into unreadable
   338	spaghetti and confuse policy evaluation with process execution.
   339	
   340	Use this rule:
   341	
   342	- a workflow activity, durable wait, deterministic choice, evidence gate,
   343	  human decision, authorized effect, reconciliation, or terminal is a graph
   344	  node when the workflow can advance, wait, block, or terminate there;
   345	- applicable policies and individual rule/checker results appear as badges and
   346	  counts on the relevant node; and
   347	- selecting the node reveals exact rule activation, evaluation, evidence, and
   348	  reason references.
   349	
   350	An expandable gate group can be considered later if users regularly need to
   351	compare many checker results. It should not be part of the simple first slice.
   352	
   353	## 9. Visual-state semantics
   354	
   355	The UI needs a small projection vocabulary, but it must preserve distinctions
   356	from canonical states.
   357	
   358	| Visual state | Meaning |
   359	|---|---|
   360	| `NOT_STARTED` | Defined in the pinned topology and not yet enabled |
   361	| `ACTIVE` | Requested or dispatched work is currently executing |
   362	| `WAITING` | Waiting for a durable signal, timer, human decision, or retry time |
   363	| `BLOCKED` | A named blocker prevents legal progress |
   364	| `SUCCEEDED` | Required node outcome is proven successful/pass |
   365	| `FAILED` | A terminal classified failure is recorded |
   366	| `CANCELLED` | The node/run was cancelled under the canonical lifecycle |
   367	| `NOT_APPLICABLE` | Qualified evaluation says the node/check does not apply |
   368	| `UNKNOWN` | Required truth is missing, stale, malformed, unsupported, or unavailable |
   369	| `CONFLICT` | Authoritative inputs disagree |
   370	| `CHECKER_FAULT` | The checker failed rather than proving subject failure |
   371	| `OUTCOME_UNKNOWN` | An attempted effect may or may not have happened and requires reconciliation |
   372	
   373	This proposed vocabulary is a server-derived read model, not a replacement for
   374	`RunStatus`, `ActivityStatus`, `GateOutcome`, or `EffectStatus`. Mapping must be
   375	one closed, total, generated, server-owned function and contract-tested for
   376	every source value. An unmapped canonical state resolves to `UNKNOWN`. A visual
   377	state is never accepted as a command input, never becomes a transitionable
   378	axis, and never aliases or extends a canonical state registry.
   379	
   380	Every state uses icon, text, and shape/border treatment as well as color.
   381	Animating an active node is optional and must respect reduced-motion settings.
   382	
   383	## 10. Snapshot and live-update transport
   384	
   385	Proposed read APIs:
   386	
   387	```text
   388	GET /api/work-items/{work_item_id}/runs
   389	GET /api/runs/{run_id}/graph
   390	GET /api/runs/{run_id}/graph/events?after={cursor}
   391	GET /api/runs/{run_id}/nodes/{workflow_node_id}
   392	```
   393	
   394	Server-Sent Events are the leading live-update candidate because this feature
   395	is a one-way read stream and the accepted dashboard target is loopback-only.
   396	Loopback does not waive authentication, authorization, origin checks, or
   397	redaction. SSE is not registered by the current architecture; selecting it
   398	requires the RFC/ADR to register a web transport port/adapter and its security,
   399	reconnect, resource, and shutdown behavior. Snapshot plus authenticated polling
   400	is the compatible first tracer.
   401	
   402	The first response is always a complete snapshot. The snapshot and its cursor
   403	must be read from the same `governed_execution` consistency cell and read
   404	transaction. A subscriber starts strictly after that cursor; the server either
   405	replays every retained delta after it or requires a new snapshot. Each delta
   406	includes:
   407	
   408	- event/cursor ID;
   409	- run ID;
   410	- topology digest;
   411	- expected previous and new projection versions;
   412	- affected stable node/edge IDs; and
   413	- the complete replacement state for those affected records.
   414	
   415	On a cursor gap, version mismatch, topology mismatch, server restart, invalid
   416	payload, or reconnect outside the retention window, the client discards
   417	untrusted deltas and refetches the full snapshot. Slow polling is an acceptable
   418	fallback. Airflow's newline-delimited stream is a viable alternative if the
   419	existing transport layer standardizes on it; WebSocket is unnecessary for the
   420	read-only first slice.
   421	
   422	Status deltas update node data without rerunning layout. Only a changed
   423	topology digest, grouping selection, or orientation may trigger layout.
   424	
   425	## 11. Technology choice
   426	
   427	| Candidate | Fit | Decision |
   428	|---|---|---|
   429	| React Flow + Dagre | Read-only custom nodes, pan/zoom/fit, selection, keyboard/screen-reader affordances, simple directed layout; both MIT | **Recommended first implementation if React is retained** |
   430	| React Flow + ELK | Better compound graphs, ports, cross-hierarchy routing, and complex layout; Airflow proves the combination | Hold as an upgrade path; more configuration, worker/bundle complexity, and EPL-2.0 qualification |
   431	| Native SVG based on Gitea | Maximum control and a close visual precedent | Do not start here; Ranex would inherit viewport, focus, keyboard, ARIA, routing, and performance work |
   432	| Mermaid runtime | Very small static proof of concept | Suitable for this research document, not the live authority-facing UI |
   433	| Import Airflow/Argo/Kestra/Dagu as an engine | Rich existing workflow products | Reject; Ranex already owns different workflow and authority semantics |
   434	
   435	[React Flow's layout guide](https://reactflow.dev/learn/layouting/layouting)
   436	explicitly treats layout as a separate concern and describes Dagre as a simple
   437	choice for directed trees, with ELK for more configurable cases. Its
   438	[accessibility guide](https://reactflow.dev/learn/advanced-use/accessibility)
   439	documents keyboard and screen-reader behavior. Those capabilities reduce work;
   440	they do not make a custom Ranex node accessible automatically.
   441	
   442	Dependency versions must be selected and pinned by the normal
   443	`supplier_governance` adoption process, including license compatibility,
   444	support/maintenance and vulnerability evidence, concentration risk, and an
   445	exit/upgrade plan. The maintained `@dagrejs/dagre` package must not be confused
   446	with legacy Dagre packages. No package is adopted by this research.
   447	
   448	## 12. Suggested source placement
   449	
   450	If an implementation ADR selects React, a cohesive feature slice would be:
   451	
   452	```text
   453	apps/web-dashboard/src/features/runs/execution-graph/
   454	  api/
   455	  components/
   456	  model/
   457	  layout/
   458	  accessibility/
   459	  __tests__/
   460	```
   461	
   462	Generated transport types belong in `generated-contracts`; the feature imports
   463	them. The graph feature must not import canonical transition tables or policy
   464	evaluators.
   465	
   466	The corresponding server query/projection code belongs inside:
   467	
   468	```text
   469	src/ranex/governed_execution/application/
   470	```
   471	
   472	That path is part of the accepted target tree; no main-branch implementation is
   473	claimed to exist.
   474	
   475	Technology-specific streaming delivery belongs behind the applicable Ranex
   476	transport adapter, not in the domain or reducer.
   477	
   478	## 13. MVP boundary
   479	
   480	The first useful slice is deliberately small:
   481	
   482	- Kanban card shows the selected/active run summary and **View execution**;
   483	- run page shows one read-only, left-to-right graph;
   484	- custom nodes show name, icon, state, duration, and attempts;
   485	- click/keyboard activation opens a details drawer;
   486	- pan, zoom, reset, and fit are available;
   487	- status updates live without moving nodes;
   488	- a reconnecting/stale/unknown banner is explicit;
   489	- terminal graphs can be regenerated for audit from canonical retained facts,
   490	  subject to artifact and legal-retention policy; and
   491	- an accessible ordered/table view exposes the same nodes, edges, states, and
   492	  details without requiring spatial navigation.
   493	
   494	Graph and ordered/table views are two presentations of the same projection and
   495	the user can switch between them. The requested graph remains the default
   496	prototype view. Representative linear and branching fixtures must establish
   497	whether a compact list should become the default for simple workflows; this
   498	research does not invent a node-count threshold.
   499	
   500	Not in the first slice:
   501	
   502	- workflow authoring or drag-and-drop;
   503	- run commands such as retry/cancel embedded in graph nodes;
   504	- cross-run comparison;
   505	- a timeline/Gantt view;
   506	- minimap;
   507	- user-defined graph themes;
   508	- parallel/map/dynamic topology before those semantics are authoritative; or
   509	- automatic work-item transitions.
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

exec
/bin/bash -lc "nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '520,760p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   520	  binding silently.
   521	- Status-only updates do not change coordinates.
   522	- Duplicate and out-of-order deltas are ignored or cause a safe resync.
   523	- A cursor gap or digest mismatch causes a full snapshot refetch.
   524	- The snapshot state and resumable cursor are captured atomically; a simulated
   525	  write between them cannot disappear.
   526	
   527	### 14.2 Semantic fidelity
   528	
   529	Fixtures cover:
   530	
   531	- linear success;
   532	- deterministic choice with taken, not-taken, and unknown dispositions;
   533	- retry and final attempt;
   534	- evidence `PASS`, `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, and
   535	  `CHECKER_FAULT`;
   536	- human wait;
   537	- run block/unblock;
   538	- cancellation and compensation request;
   539	- effect `OUTCOME_UNKNOWN` followed by reconciliation;
   540	- terminal failure and success; and
   541	- a successful run whose work item remains unchanged.
   542	
   543	Projection replay/query results must agree with the canonical committed rows.
   544	Any unmapped state, missing required reference, or disagreement is visibly
   545	`UNKNOWN` or `CONFLICT`, never green.
   546	
   547	### 14.3 Usability, accessibility, security, and performance
   548	
   549	- Keyboard users can traverse/select nodes and open/close details.
   550	- A screen reader receives a run summary, current state announcement, and a
   551	  non-spatial table/list alternative.
   552	- The implementation RFC proposes [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
   553	  Level AA as the dashboard baseline and defines role/name/value, focus order,
   554	  target size, contrast, and assistive-technology fixtures for the graph,
   555	  drawer, and ordered view.
   556	- State is never conveyed by color alone; reduced motion is honored.
   557	- Classified node content is replaced by authorized safe summaries and opaque
   558	  references.
   559	- Raw prompts, source, model output, credentials, and secrets never appear just
   560	  because a graph node exists.
   561	- Authorization and classification/redaction are independently enforced when
   562	  dereferencing every evidence, log, artifact, rule, decision, permit, effect,
   563	  and reconciliation link; possession of a graph reference grants no access.
   564	- Authorization is enforced for snapshot, stream, detail, and dereference
   565	  endpoints.
   566	- Layout/status performance is measured with representative small, medium, and
   567	  boundary-size fixtures; thresholds are set by an accepted quality-attribute
   568	  decision rather than invented in this research.
   569	
   570	## 15. Risks and failure modes
   571	
   572	| Risk | Required response |
   573	|---|---|
   574	| Graph looks authoritative while stale | Show consistency/cursor state; refetch on gaps; never retain green certainty after invalidation |
   575	| UI duplicates business rules | Server-owned closed projection mapping; architecture test forbids authority imports |
   576	| Rules overwhelm the flow | Keep rules in badges/details; make only process-stopping gates first-class nodes |
   577	| Multiple runs are confused | Always show exact `RunId`, attempt, workflow digest/version, and explicit selector; auto-open only a unique server-linked current run |
   578	| Layout jumps on every event | Split topology from status; cache layout by topology digest and grouping/orientation |
   579	| Large graph becomes unusable | Collapse supported groups, render visible elements, add search; qualify ELK only when real fixtures demand it |
   580	| Accessibility is treated as a library feature | Add Ranex-specific keyboard, ARIA, table fallback, contrast, and assistive-technology tests |
   581	| Upstream code is copied casually | Prefer libraries and original adapters; record provenance and license obligations for any copied fragment |
   582	| Unsupported dynamic nodes appear | Fail visibly as unknown/unsupported and refetch; do not synthesize topology |
   583	| Cached graph outlives canonical retention | Treat it as a disposable derived view; regenerate only from facts still legally available and preserve redaction/purge outcomes |
   584	
   585	## 16. Is it a good fit for Ranex?
   586	
   587	### 16.1 Why it fits
   588	
   589	- Ranex already models a run as a versioned deterministic workflow.
   590	- The journal, current rows, stable IDs, and exact subject bindings provide
   591	  better provenance than a generic task-progress widget.
   592	- The dashboard is already defined as a presentation-only authority view.
   593	- A visual graph makes waiting, blocking, gate, permit, effect, and
   594	  reconciliation states understandable to a non-technical owner.
   595	- Mature open-source projects prove the renderer/layout/live-overlay pattern.
   596	- The first slice is local, read-only, and reversible; it does not require a new
   597	  workflow engine.
   598	
   599	### 16.2 Conditions that would make it a bad fit
   600	
   601	It is a bad fit if implementation:
   602	
   603	- begins before the run/workflow projection contract is closed;
   604	- uses the graph library as the workflow interpreter;
   605	- allows the client to decide state or eligibility;
   606	- presents probabilistic agent progress as canonical workflow progress;
   607	- hides unknown/conflict/reconciliation states behind generic pending/failed
   608	  colors;
   609	- adds editing before versioning and activation governance exist; or
   610	- consumes more complexity than a compact ordered step list for the workflows
   611	  Ranex actually runs.
   612	
   613	The last point must be tested with users. A graph is justified when branching,
   614	waiting, gates, retries, or reconciliation make a list hard to understand. A
   615	linear three-step run should still be readable as a compact list and accessible
   616	table. The graph prototype and table must use the same fixtures and be compared
   617	before the renderer dependency is adopted.
   618	
   619	## 17. DeepSeek and HY3 review reconciliation
   620	
   621	Both reviewers received the unchanged v0.1.0 draft with digest
   622	`2b5e4476defd01ece67bbf0f62b60dcd47a09f5932eeee55ae0d5ae32257dc0d`.
   623	They ran sequentially, read-only, and neither saw the other's result.
   624	
   625	| Reviewer | Route / variant | Local session | Verdict |
   626	|---|---|---|---|
   627	| DeepSeek V4 Pro | `opencode-go/deepseek-v4-pro`, `high` | `ses_04e188329ffemvBenGw0MKQBwi` | `FIT_WITH_CHANGES` |
   628	| HY3 | `openrouter/tencent/hy3`, `high` | `ses_04e138bf8ffehwkokIuiXgPeJ3` | `FIT_WITH_CHANGES` |
   629	
   630	These are advisory model observations, not independent approval, a readiness
   631	gate, or runtime proof.
   632	
   633	The session IDs are local provenance, and raw provider output is not included
   634	in this repository. This section is a primary-source-checked reconciliation,
   635	not independently reproducible evidence of the complete model responses.
   636	
   637	### 17.1 Findings accepted
   638	
   639	- Register the projection, schema, generated contracts, transport, and fitness
   640	  boundary through an RFC/ADR before implementation.
   641	- Define `topology_digest` with server-only canonicalization and golden
   642	  fixtures; do not claim deterministic pixels.
   643	- Capture snapshot state and cursor from one consistency cell/read transaction,
   644	  and refetch safely on any gap.
   645	- Make the visual-state mapping total, server-owned, non-transitionable, and
   646	  fail-closed.
   647	- State plainly that the dashboard/source paths and React choice are targets,
   648	  not current main-branch implementation.
   649	- Qualify the renderer and layout packages through supplier governance.
   650	- Extend authorization and redaction through every referenced detail endpoint.
   651	- Define an accessibility baseline and preserve a complete non-spatial view.
   652	- Treat terminal graphs as regenerated derived views under canonical retention,
   653	  not as separately immortal audit artifacts.
   654	- Define exact run selection; never guess solely from recency.
   655	
   656	### 17.2 Findings accepted with modification
   657	
   658	- Both reviewers argued that a list might be simpler. That is a valid
   659	  falsification test, but the owner explicitly confirmed the need to visualize
   660	  each deterministic run. The reconciled direction keeps a graph prototype and
   661	  makes the ordered/table view coequal; representative fixtures decide defaults
   662	  before dependency adoption.
   663	- HY3 proposed retaining projection deltas for the whole audit period. That is
   664	  unnecessary: deltas support reconnect, while the graph is regenerated from
   665	  canonical facts retained by their owning policies.
   666	- HY3 proposed removing canonical source state from the payload. The
   667	  reconciliation retains it as display-only diagnostic truth and forbids the
   668	  client from deriving visual or transition semantics from it.
   669	
   670	### 17.3 Findings rejected or refuted
   671	
   672	- HY3 called loopback deployment unestablished. `ARCH-RANEX-001` fixes the web
   673	  dashboard as loopback-only. Its security conclusion still stands:
   674	  loopback is not an authentication or redaction exemption.
   675	- DeepSeek stated that the maintained Dagre repository had not released since
   676	  2019. The official project lists
   677	  [`@dagrejs/dagre` v2.0.0](https://github.com/dagrejs/dagre/releases/tag/v2.0.0)
   678	  from 2025. Supplier qualification remains required, but that maintenance
   679	  premise is false.
   680	- Airflow using ELK does not contradict Dagre for a simple first graph. Argo,
   681	  Kestra, and Dagster establish Dagre precedent; Airflow establishes the
   682	  upgrade pattern when compound graphs and routing require ELK.
   683	
   684	### 17.4 Reconciled verdict
   685	
   686	**FIT WITH ARCHITECTURE WORK BEFORE IMPLEMENTATION.** The feature belongs in
   687	Ranex because it explains an existing deterministic governed run to the user.
   688	It is not ready to build from this research alone because the projection,
   689	transport, accessibility baseline, supplier decisions, and quality thresholds
   690	are not yet accepted contracts.
   691	
   692	## 18. Recommended decision and delivery sequence
   693	
   694	1. Accept this only as research.
   695	2. Preserve §17 as advisory review evidence, not decision authority.
   696	3. Run a user-facing graph/table prototype using synthetic, non-authoritative
   697	   linear, branching, waiting, gate, retry, and reconciliation fixtures.
   698	4. Record an RFC/ADR choosing the projection owner, contract, transport,
   699	   renderer, layout engine, dependency licenses, and quality thresholds.
   700	5. Add versioned projection/delta schemas and generated TypeScript/Python
   701	   contracts.
   702	6. Implement server projection tests before the visual component.
   703	7. Implement the read-only MVP and run accessibility, security, replay,
   704	   resilience, and performance checks.
   705	8. Do not claim runtime conformance until applicable readiness evidence passes.
   706	
   707	## 19. Source and license register
   708	
   709	All findings above are original Ranex synthesis and paraphrase, including the
   710	review reconciliation. No upstream code is copied into this document.
   711	
   712	| Source | Frozen revision or authoritative page | License / use |
   713	|---|---|---|
   714	| GitHub Actions workflow monitoring | [GitHub Docs](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui), accessed 2026-07-30 | Product behavior/documentation reference |
   715	| GitHub Actions workflow model | [GitHub Docs](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows?learn=getting_started&learnproduct=actions), accessed 2026-07-30 | Product behavior/documentation reference |
   716	| GitLab pipeline graph | [GitLab Docs](https://docs.gitlab.com/ci/pipelines/), accessed 2026-07-30 | Product behavior/documentation reference |
   717	| Gitea workflow graph | [`e80a62f5552cad07bf79b2f31687cf5a9b93f1fc`](https://github.com/go-gitea/gitea/tree/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc) | MIT; code inspection only |
   718	| Apache Airflow graph | [`f781f8b8785496d68c9d9ae725a004764bbc9f1d`](https://github.com/apache/airflow/tree/f781f8b8785496d68c9d9ae725a004764bbc9f1d) | Apache-2.0; code inspection only |
   719	| Argo Workflows graph | [`d98d7b7d73d1b24dd7258153453ea612dbb70092`](https://github.com/argoproj/argo-workflows/tree/d98d7b7d73d1b24dd7258153453ea612dbb70092) | Apache-2.0; code inspection only |
   720	| Kestra topology | [`e03a4f351328f294e67f62be60af0553401fad7a`](https://github.com/kestra-io/kestra/tree/e03a4f351328f294e67f62be60af0553401fad7a) | Apache-2.0; code inspection only |
   721	| Dagster graph layout | [`014641bc1bdb71ea2c7f40371691103bbff5c9c7`](https://github.com/dagster-io/dagster/tree/014641bc1bdb71ea2c7f40371691103bbff5c9c7) | Apache-2.0; code inspection only |
   722	| React Flow / XYFlow | [`360f5b13e2bc6899ea06b4be1a49b068d86926cf`](https://github.com/xyflow/xyflow/tree/360f5b13e2bc6899ea06b4be1a49b068d86926cf) and [official docs](https://reactflow.dev/) | MIT; candidate dependency, not adopted |
   723	| Dagre | [DagreJS repository](https://github.com/dagrejs/dagre), inspected 2026-07-30 | MIT; candidate dependency, not adopted |
   724	| ELK / elkjs | [ELK layered algorithm](https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html) and [elkjs](https://github.com/kieler/elkjs) | EPL-2.0; upgrade candidate requiring qualification |
   725	| Dagu graph | [`3fd7eeff69e2df281cd8bd8f47348baf8d3462be`](https://github.com/dagu-org/dagu/tree/3fd7eeff69e2df281cd8bd8f47348baf8d3462be) | GPL-3.0; behavior observation only, no code reuse proposed |
   726	| WCAG 2.2 | [W3C Recommendation](https://www.w3.org/TR/WCAG22/), accessed 2026-07-30 | Proposed accessibility baseline; not yet adopted by Ranex |
   727	
   728	## 20. Provisional conclusion
   729	
   730	Proceed to an RFC and synthetic prototype, not directly to product
   731	implementation. DeepSeek and HY3 both concluded that the concept fits with
   732	changes, and primary-source reconciliation supports that verdict. A governed
   733	run already has the deterministic structure and authoritative state that a
   734	trustworthy graph needs. The safest proven implementation is a server-owned,
   735	digest-bound projection rendered read-only with a mature flow library; the
   736	graph remains an explanation of authority, never authority itself.

exec
/bin/bash -lc "nl -ba LICENSE-RANEX.md | sed -n '1,120p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	# Ranex Personal-Use Source License 1.0
     2	
     3	Copyright (c) 2026 Anthony Garces. All rights reserved.
     4	
     5	This is a source-available license. It is not an open-source license.
     6	
     7	## 1. Scope
     8	
     9	This license applies only to original Ranex code, documentation, configuration,
    10	artwork, and modifications owned by Anthony Garces (the "Ranex Material").
    11	
    12	It does not apply to Hermes Agent material or any other third-party material.
    13	Those portions remain governed by their own licenses. When Hermes Agent
    14	material is adopted in Phase 1, its MIT License is retained in `LICENSE`.
    15	
    16	## 2. Personal-use permission
    17	
    18	Subject to every condition below, an individual may view, copy, run, study, and
    19	privately modify the Ranex Material solely for personal learning,
    20	experimentation, or evaluation.
    21	
    22	This permission is personal, limited, non-exclusive, and non-transferable. All
    23	copyright, license, attribution, and source notices must remain intact.
    24	
    25	## 3. Restrictions
    26	
    27	Except for the limited GitHub-platform rights in section 4, and unless Anthony
    28	Garces gives prior written permission, you may not:
    29	
    30	1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
    31	   or otherwise provide the Ranex Material or a modified version to anyone;
    32	2. make the Ranex Material available through a public or shared repository,
    33	   download, package, service, hosted application, network endpoint, or device;
    34	3. use the Ranex Material for any commercial, business, employment,
    35	   professional, institutional, revenue-generating, or client purpose;
    36	4. use the Ranex Material to operate, support, develop, or improve a product,
    37	   service, organization, or business process;
    38	5. remove, hide, or alter a copyright, license, provenance, or attribution
    39	   notice;
    40	6. claim authorship or ownership of Ranex Material created by Anthony Garces,
    41	   or present that material as your own work;
    42	7. use the Ranex name, logo, or branding to imply endorsement, affiliation, or
    43	   ownership; or
    44	8. grant another person rights that this license does not grant to you.
    45	
    46	You may identify original changes that you created privately, but that does not
    47	give you ownership of the underlying Ranex Material or permission to
    48	redistribute the combined work.
    49	
    50	## 4. Public GitHub repository
    51	
    52	While the repository is public, GitHub's Terms of Service grant GitHub users
    53	limited permission to use, display, perform, and reproduce repository content
    54	through GitHub's service as its features allow, including by forking it. This
    55	license does not restrict those platform rights.
    56	
    57	Those platform permissions do not grant permission to redistribute the Ranex
    58	Material outside GitHub's service, use it for business, remove its notices, or
    59	claim it as your own.
    60	
    61	## 5. Ownership and third-party rights
    62	
    63	The Ranex Material is licensed, not sold. Anthony Garces retains all rights
    64	not expressly granted here.
    65	
    66	No term in this license reduces a right granted directly by the MIT License or
    67	another applicable third-party license. When a file contains both upstream
    68	material and original Ranex modifications, each portion remains governed by
    69	its applicable license.
    70	
    71	## 6. Termination
    72	
    73	Your permission under this license ends automatically when you violate it.
    74	After termination, you must stop using the Ranex Material and delete copies in
    75	your possession or control, except copies GitHub retains under its Terms of
    76	Service or copies the law requires you to preserve.
    77	
    78	## 7. No warranty
    79	
    80	THE RANEX MATERIAL IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    81	OR IMPLIED, INCLUDING WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
    82	PURPOSE, TITLE, AND NON-INFRINGEMENT.
    83	
    84	TO THE MAXIMUM EXTENT PERMITTED BY LAW, THE COPYRIGHT HOLDER WILL NOT BE LIABLE
    85	FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY ARISING FROM THE RANEX MATERIAL OR
    86	ITS USE.
    87	
    88	## 8. Other rights
    89	
    90	This license does not limit fair use, fair dealing, or another right that
    91	applicable law does not allow a license to restrict.
    92	
    93	For redistribution, business use, sublicensing, or another exception, obtain
    94	prior written permission from Anthony Garces through the `anthonykewl20`
    95	GitHub account.

codex
The local audit confirms the two defects are structural, not cosmetic: the state row validates only against its own JSON fields, while the journal stores hashes and resulting JSON that no load-time or database constraint ties back to that state row; and the “crash” fixture is a normal SQLite statement abort in the same process, not a process/power-loss boundary. I’m now checking how mature engines close those exact gaps.
exec
/bin/bash -lc 'nl -ba .claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py' in /home/soultransit/devtony/ranex
 succeeded in 0ms:
     1	from __future__ import annotations
     2	
     3	import sqlite3
     4	from pathlib import Path
     5	
     6	from ranex.governed_execution.adapters.persistence.sqlite.execution_store import (
     7	    SQLiteExecutionStore,
     8	)
     9	
    10	
    11	def test_initial_migration_is_repeatable_and_records_schema_version(
    12	    tmp_path: Path,
    13	) -> None:
    14	    database_path = tmp_path / "migration.sqlite3"
    15	    store = SQLiteExecutionStore(database_path)
    16	
    17	    store.initialize()
    18	    store.initialize()
    19	
    20	    with sqlite3.connect(database_path) as connection:
    21	        user_version = connection.execute("PRAGMA user_version").fetchone()
    22	        tables = {
    23	            row[0]
    24	            for row in connection.execute(
    25	                """
    26	                SELECT name
    27	                FROM sqlite_schema
    28	                WHERE type = 'table' AND name LIKE 'execution_%'
    29	                """
    30	            )
    31	        }
    32	
    33	    assert user_version == (1,)
    34	    assert tables == {
    35	        "execution_state",
    36	        "execution_journal",
    37	        "execution_outbox",
    38	    }

exec
/bin/bash -lc "rg -n 'snapshot|journal|outbox|replay|upcast|workflow|definition|digest|version|crash|power|kill' .claude/worktrees/kernel-tracer/src .claude/worktrees/kernel-tracer/tests | head -n 300" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:11:    load_gate_catalog_with_digest,
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:19:schema_version: "1"
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:68:def test_loader_returns_digest_of_exact_policy_bytes(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:72:    catalog, digest = load_gate_catalog_with_digest(policy_path)
.claude/worktrees/kernel-tracer/tests/contract/policy/test_gate_policy_loader.py:75:    assert digest == "sha256:" + hashlib.sha256(POLICY).hexdigest()
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:11:def test_initial_migration_is_repeatable_and_records_schema_version(
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:21:        user_version = connection.execute("PRAGMA user_version").fetchone()
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:33:    assert user_version == (1,)
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:36:        "execution_journal",
.claude/worktrees/kernel-tracer/tests/migration/governed_execution/test_execution_store_migration.py:37:        "execution_outbox",
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:12:    replay_execution,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:24:def test_replay_reproduces_identical_final_state_and_version() -> None:
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:30:            expected_version=0,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:34:            workflow_request_ref="workflow-request:sha256:one",
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:39:            expected_version=1,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:41:            readiness_snapshot_ref="snapshot:sha256:ready",
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:46:            expected_version=2,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:53:            expected_version=3,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:62:    replayed = replay_execution(events)
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:64:    assert replayed == direct
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:65:    assert replayed.status is ExecutionStatus.SUCCEEDED
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:66:    assert replayed.version == len(events) == 4
.claude/worktrees/kernel-tracer/src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py:70:                "schema_version",
.claude/worktrees/kernel-tracer/src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py:81:    if raw.get("schema_version") != "1":
.claude/worktrees/kernel-tracer/src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py:82:        raise ValueError("unsupported policy schema_version")
.claude/worktrees/kernel-tracer/src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py:171:def load_gate_catalog_with_digest(path: Path) -> tuple[GateCatalog, str]:
.claude/worktrees/kernel-tracer/src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py:173:    digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
.claude/worktrees/kernel-tracer/src/ranex/policy/adapters/configuration/yaml/gate_catalog_loader.py:174:    return load_gate_catalog_bytes(content), digest
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31:def test_failure_between_journal_and_outbox_leaves_no_partial_state(
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:34:    database_path = tmp_path / "crash-boundary.sqlite3"
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:41:            expected_version=0,
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:45:            workflow_request_ref="workflow-request:sha256:crash",
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:52:            CREATE TRIGGER simulate_crash_before_outbox
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:53:            BEFORE INSERT ON execution_outbox
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:54:            WHEN NEW.aggregate_version = 2
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:56:                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:61:    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:66:                expected_version=1,
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:68:                readiness_snapshot_ref="snapshot:sha256:crash-ready",
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:75:    assert unchanged.version == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:77:    assert store.count_journal_entries(RUN_ID) == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:78:    assert store.count_outbox_entries(RUN_ID) == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:86:                (SELECT COUNT(*) FROM execution_journal
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:88:                (SELECT COUNT(*) FROM execution_outbox
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:46:        expected_version=1,
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:59:        subject_version=1,
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:126:        catalog_digest="sha256:" + "d" * 64,
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:141:        catalog_digest="sha256:" + "d" * 64,
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:153:def test_deterministic_policy_adapter_rejects_noncanonical_digest() -> None:
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:154:    with pytest.raises(ValueError, match="catalog_digest"):
.claude/worktrees/kernel-tracer/tests/security/test_application_control_pep.py:157:            catalog_digest="sha256:" + "z" * 64,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:6:    version INTEGER NOT NULL CHECK (version >= 1),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:11:CREATE TABLE IF NOT EXISTS execution_journal (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:16:    previous_version INTEGER NOT NULL CHECK (previous_version >= 0),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:17:    resulting_version INTEGER NOT NULL,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:25:    UNIQUE (execution_id, resulting_version),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:26:    CHECK (resulting_version = previous_version + 1),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:28:        (previous_version = 0 AND previous_state_sha256 IS NULL)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:30:        (previous_version > 0 AND length(previous_state_sha256) = 64)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35:CREATE TABLE IF NOT EXISTS execution_outbox (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:39:    aggregate_version INTEGER NOT NULL CHECK (aggregate_version >= 1),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:43:        REFERENCES execution_journal(event_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:44:    UNIQUE (execution_id, aggregate_version)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:48:BEFORE UPDATE ON execution_journal
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:50:    SELECT RAISE(ABORT, 'execution_journal is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:53:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:54:BEFORE DELETE ON execution_journal
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:56:    SELECT RAISE(ABORT, 'execution_journal is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:59:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:60:BEFORE UPDATE ON execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:62:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:65:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:66:BEFORE DELETE ON execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:68:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:71:PRAGMA user_version = 1;
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:36:        "schema_version",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:40:        "workflow_request_ref",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:42:        "version",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:55:    """The expected canonical execution version changed before commit."""
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:60:        "schema_version": "execution-state/v1",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:64:        "workflow_request_ref": execution.workflow_request_ref,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:66:        "version": execution.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:86:    if document["schema_version"] != "execution-state/v1":
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:87:        raise ValueError("unsupported execution state schema version")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:88:    version = document["version"]
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:89:    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:90:        raise ValueError("execution state version must be a positive integer")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:113:        workflow_request_ref=_require_string(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:114:            document["workflow_request_ref"],
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:115:            "workflow_request_ref",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:118:        version=version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:130:        "schema_version": "execution-event/v1",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:134:        "expected_version": event.expected_version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:142:                "workflow_request_ref": event.workflow_request_ref,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:146:        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:184:    """State, audit journal, and outbox committed in one SQLite transaction."""
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:215:                SELECT execution_id, canonical_state_json, version, last_event_id
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:229:                SELECT execution_id, canonical_state_json, version, last_event_id
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:248:                        version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:256:                        next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:262:                previous_version = 0
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:266:                previous_version = current.version
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:271:                        version = ?,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:275:                      AND version = ?
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:280:                        next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:284:                        current.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:295:            resulting_digest = canonical_sha256(next_document)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:296:            previous_digest = (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:303:                INSERT INTO execution_journal(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:307:                    previous_version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:308:                    resulting_version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:320:                    previous_version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:321:                    next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:323:                    previous_digest,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:324:                    resulting_digest,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:330:            outbox_document = {
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:331:                "schema_version": "execution-outbox/v1",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:335:                "aggregate_version": next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:341:                INSERT INTO execution_outbox(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:344:                    aggregate_version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:352:                    next_state.version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:353:                    canonical_json(outbox_document),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:366:    def count_journal_entries(self, execution_id: Identity) -> int:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:367:        return self._count_rows("execution_journal", execution_id)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:369:    def count_outbox_entries(self, execution_id: Identity) -> int:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:370:        return self._count_rows("execution_outbox", execution_id)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:374:        if table not in {"execution_journal", "execution_outbox"}:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:408:        if int(row["version"]) != state.version:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:410:                "relational version disagrees with canonical state version"
.claude/worktrees/kernel-tracer/tests/unit/foundation/domain/test_identity.py:15:    assert identity.uuid.version == 7
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:23:    previous_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:24:    record_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:25:    entry_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:34:    head_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:39:    return hashlib.sha256(value.encode("utf-8")).hexdigest()
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:42:def _entry_digest(
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:45:    previous_digest: str,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:46:    record_digest: str,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:51:                "previous_digest": previous_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:52:                "record_digest": record_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:66:        previous_digest = _GENESIS_DIGEST
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:71:                record_digest = _sha256_text(canonical_json(record))
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:72:                computed_entry_digest = _entry_digest(
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:74:                    previous_digest=previous_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:75:                    record_digest=record_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:79:                    and raw["previous_digest"] == previous_digest
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:80:                    and raw["record_digest"] == record_digest
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:81:                    and raw["entry_digest"] == computed_entry_digest
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:85:                computed_entry_digest = previous_digest
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:91:                    head_digest=previous_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:94:            previous_digest = computed_entry_digest
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:99:            head_digest=previous_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:108:                head_digest=_GENESIS_DIGEST,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:119:                head_digest=_GENESIS_DIGEST,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:173:                            previous_digest=raw["previous_digest"],
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:174:                            record_digest=raw["record_digest"],
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:175:                            entry_digest=raw["entry_digest"],
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:180:            record_digest = _sha256_text(canonical_json(stored_record))
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:181:            entry_digest = _entry_digest(
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:183:                previous_digest=verification.head_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:184:                record_digest=record_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:188:                previous_digest=verification.head_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:189:                record_digest=record_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:190:                entry_digest=entry_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:198:                        "previous_digest": entry.previous_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:199:                        "record_digest": entry.record_digest,
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/persistence/jsonl/hash_chain_ledger.py:200:                        "entry_digest": entry.entry_digest,
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:24:def record(digest: str) -> EvidenceRecord:
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:32:        subject_version=1,
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:38:        artifact_sha256="sha256:" + digest,
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:49:    evidence = record(hashlib.sha256(content).hexdigest())
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:60:def test_verifier_rejects_symlink_and_digest_mismatch(tmp_path: Path) -> None:
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:67:            record(hashlib.sha256(b"target").hexdigest()),
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_evidence_artifact_verifier.py:71:    with pytest.raises(EvidenceArtifactError, match="digest"):
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_application_control.py:61:            expected_version=0,
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:25:    assert second.previous_digest == first.entry_digest
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:28:    assert verification.head_digest == second.entry_digest
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:53:    replay = ledger.append_once({"decision": "PASS"}, key="request-1")
.claude/worktrees/kernel-tracer/tests/integration/assurance/test_hash_chain_ledger.py:55:    assert replay == first
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:28:        expected_version=7,
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:34:    assert request.expected_version == 7
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:46:        "expected_version": 0,
.claude/worktrees/kernel-tracer/tests/unit/work_management/domain/test_transitions.py:66:            expected_version=0,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/execution_repository.py:12:        """Load the current canonical execution snapshot."""
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:50:        expected_version=0,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:54:        workflow_request_ref="workflow-request:sha256:created",
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:58:def ready(*, version: int = 1, sequence: int = 2) -> ExecutionMarkedReady:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:62:        expected_version=version,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:64:        readiness_snapshot_ref="snapshot:sha256:ready",
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:68:def started(*, version: int = 2, sequence: int = 3) -> ExecutionStarted:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:72:        expected_version=version,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:84:    assert state.version == 1
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:100:    assert first.version == 2
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:113:            expected_version=3,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:128:            expected_version=4,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:131:            refreshed_evidence_ref="snapshot:sha256:refreshed",
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:137:    assert unblocked.version == 5
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:153:                expected_version=1,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:162:def test_reducer_rejects_wrong_execution_and_stale_version() -> None:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:171:    with pytest.raises(InvalidExecutionTransition, match="expected version"):
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:172:        reduce_execution(proposed, replace(ready(), expected_version=99))
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:184:            expected_version=3,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:197:                expected_version=2,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:203:        reduce_execution(blocked, started(version=4, sequence=5))
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:258:    event = _event_for(event_type, state.version)
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:272:            expected_version=3,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:282:            expected_version=3,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:297:def _event_for(event_type: type, version: int) -> object:
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:299:        "event_id": transition_id(version + 1),
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:301:        "expected_version": version,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/domain/test_execution.py:302:        "occurred_at": f"2026-07-29T00:00:{version + 1:02d}Z",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py:25:        catalog_digest: str,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py:27:        if _SHA256_PATTERN.fullmatch(catalog_digest) is None:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py:28:            raise ValueError("catalog_digest must be canonical SHA-256")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py:30:        self._catalog_digest = catalog_digest
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py:46:            catalog_digest=self._catalog_digest,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:21:def _digest(value: object) -> str:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:50:        "subject_version": record.subject_version,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:71:        catalog_digest: str,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:74:        policy_digest = _digest(_gate_document(gate))
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:77:        evidence_digest = _digest(documents)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:94:                catalog_digest=catalog_digest,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:95:                policy_digest=policy_digest,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:96:                evidence_digest=evidence_digest,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:148:                    and record.subject_version == request.expected_version
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:31:def _require_digest(value: str, field: str) -> None:
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:44:    subject_version: int
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:67:            isinstance(self.subject_version, bool)
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:68:            or not isinstance(self.subject_version, int)
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:69:            or self.subject_version < 0
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:71:            raise ValueError("subject_version must be a non-negative integer")
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:74:        _require_digest(self.artifact_sha256, "artifact_sha256")
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:88:    catalog_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:89:    policy_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:90:    evidence_digest: str
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:112:        _require_digest(self.catalog_digest, "catalog_digest")
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:113:        _require_digest(self.policy_digest, "policy_digest")
.claude/worktrees/kernel-tracer/src/ranex/assurance/domain/gates.py:114:        _require_digest(self.evidence_digest, "evidence_digest")
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:38:        expected_version=2,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:68:        subject_version=2,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:85:        catalog_digest="sha256:" + "b" * 64,
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:104:    assert decision.policy_digest.startswith("sha256:")
.claude/worktrees/kernel-tracer/tests/unit/governed_execution/application/test_gate_controller.py:105:    assert decision.evidence_digest.startswith("sha256:")
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:74:    digest = hashlib.sha256()
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:77:        digest.update(chunk)
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:79:    return digest.hexdigest(), before, after
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:117:        observed_digest, before, after = _sha256_descriptor(artifact_fd)
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:124:    expected_digest = evidence.artifact_sha256.removeprefix("sha256:")
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:125:    if not hmac.compare_digest(observed_digest, expected_digest):
.claude/worktrees/kernel-tracer/src/ranex/assurance/adapters/filesystem/artifact_verifier.py:126:        raise EvidenceArtifactError("artifact digest does not match evidence record")
.claude/worktrees/kernel-tracer/src/ranex/foundation/identity.py:27:        if self.uuid.version != 7 or self.uuid.variant != uuid.RFC_4122:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:36:    expected_version: int
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:51:            isinstance(self.expected_version, bool)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:52:            or not isinstance(self.expected_version, int)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:53:            or self.expected_version < 0
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:55:            raise ValueError("expected_version must be a non-negative integer")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:63:    workflow_request_ref: str
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:77:        _require_text(self.workflow_request_ref, field="workflow_request_ref")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:82:    readiness_snapshot_ref: str
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:87:            self.readiness_snapshot_ref,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:88:            field="readiness_snapshot_ref",
.claude/worktrees/kernel-tracer/src/ranex/foundation/canonical.py:26:    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:19:    expected_version: int
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:31:            isinstance(self.expected_version, bool)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:32:            or not isinstance(self.expected_version, int)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:33:            or self.expected_version < 0
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:35:            raise ValueError("expected_version must be a non-negative integer")
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:45:    expected_version: int
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:65:            isinstance(self.expected_version, bool)
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:66:            or not isinstance(self.expected_version, int)
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:67:            or self.expected_version < 0
.claude/worktrees/kernel-tracer/src/ranex/work_management/domain/transitions.py:69:            raise ValueError("expected_version must be a non-negative integer")
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:49:        expected_version=0,
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:53:        workflow_request_ref="workflow-request:sha256:sqlite",
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:61:        expected_version=1,
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:63:        readiness_snapshot_ref="snapshot:sha256:sqlite-ready",
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:79:def test_transition_commits_canonical_state_version_journal_and_outbox_together(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:87:    assert proposed.version == 1
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:89:    assert ready.version == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:96:            SELECT canonical_state_json, version, last_event_id
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:102:        journal_rows = connection.execute(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:104:            SELECT event_id, previous_version, resulting_version,
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:106:            FROM execution_journal
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:110:        outbox_rows = connection.execute(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:112:            SELECT event_id, aggregate_version, payload_json
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:113:            FROM execution_outbox
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:121:    assert state_row["version"] == state_document["version"] == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:125:        (row["event_id"], row["previous_version"], row["resulting_version"])
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:126:        for row in journal_rows
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:135:        for row in journal_rows
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:138:    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:144:        for row in outbox_rows
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:148:def test_journal_is_database_enforced_append_only(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:156:            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:158:            connection.execute("DELETE FROM execution_journal")
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:161:def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:167:    with pytest.raises(ValueError, match="expected version"):
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:170:    assert store.count_journal_entries(RUN_ID) == 2
.claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py:171:    assert store.count_outbox_entries(RUN_ID) == 2

exec
/bin/bash -lc "nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '360,530p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
   360	| `NOT_STARTED` | Defined in the pinned topology and not yet enabled |
   361	| `ACTIVE` | Requested or dispatched work is currently executing |
   362	| `WAITING` | Waiting for a durable signal, timer, human decision, or retry time |
   363	| `BLOCKED` | A named blocker prevents legal progress |
   364	| `SUCCEEDED` | Required node outcome is proven successful/pass |
   365	| `FAILED` | A terminal classified failure is recorded |
   366	| `CANCELLED` | The node/run was cancelled under the canonical lifecycle |
   367	| `NOT_APPLICABLE` | Qualified evaluation says the node/check does not apply |
   368	| `UNKNOWN` | Required truth is missing, stale, malformed, unsupported, or unavailable |
   369	| `CONFLICT` | Authoritative inputs disagree |
   370	| `CHECKER_FAULT` | The checker failed rather than proving subject failure |
   371	| `OUTCOME_UNKNOWN` | An attempted effect may or may not have happened and requires reconciliation |
   372	
   373	This proposed vocabulary is a server-derived read model, not a replacement for
   374	`RunStatus`, `ActivityStatus`, `GateOutcome`, or `EffectStatus`. Mapping must be
   375	one closed, total, generated, server-owned function and contract-tested for
   376	every source value. An unmapped canonical state resolves to `UNKNOWN`. A visual
   377	state is never accepted as a command input, never becomes a transitionable
   378	axis, and never aliases or extends a canonical state registry.
   379	
   380	Every state uses icon, text, and shape/border treatment as well as color.
   381	Animating an active node is optional and must respect reduced-motion settings.
   382	
   383	## 10. Snapshot and live-update transport
   384	
   385	Proposed read APIs:
   386	
   387	```text
   388	GET /api/work-items/{work_item_id}/runs
   389	GET /api/runs/{run_id}/graph
   390	GET /api/runs/{run_id}/graph/events?after={cursor}
   391	GET /api/runs/{run_id}/nodes/{workflow_node_id}
   392	```
   393	
   394	Server-Sent Events are the leading live-update candidate because this feature
   395	is a one-way read stream and the accepted dashboard target is loopback-only.
   396	Loopback does not waive authentication, authorization, origin checks, or
   397	redaction. SSE is not registered by the current architecture; selecting it
   398	requires the RFC/ADR to register a web transport port/adapter and its security,
   399	reconnect, resource, and shutdown behavior. Snapshot plus authenticated polling
   400	is the compatible first tracer.
   401	
   402	The first response is always a complete snapshot. The snapshot and its cursor
   403	must be read from the same `governed_execution` consistency cell and read
   404	transaction. A subscriber starts strictly after that cursor; the server either
   405	replays every retained delta after it or requires a new snapshot. Each delta
   406	includes:
   407	
   408	- event/cursor ID;
   409	- run ID;
   410	- topology digest;
   411	- expected previous and new projection versions;
   412	- affected stable node/edge IDs; and
   413	- the complete replacement state for those affected records.
   414	
   415	On a cursor gap, version mismatch, topology mismatch, server restart, invalid
   416	payload, or reconnect outside the retention window, the client discards
   417	untrusted deltas and refetches the full snapshot. Slow polling is an acceptable
   418	fallback. Airflow's newline-delimited stream is a viable alternative if the
   419	existing transport layer standardizes on it; WebSocket is unnecessary for the
   420	read-only first slice.
   421	
   422	Status deltas update node data without rerunning layout. Only a changed
   423	topology digest, grouping selection, or orientation may trigger layout.
   424	
   425	## 11. Technology choice
   426	
   427	| Candidate | Fit | Decision |
   428	|---|---|---|
   429	| React Flow + Dagre | Read-only custom nodes, pan/zoom/fit, selection, keyboard/screen-reader affordances, simple directed layout; both MIT | **Recommended first implementation if React is retained** |
   430	| React Flow + ELK | Better compound graphs, ports, cross-hierarchy routing, and complex layout; Airflow proves the combination | Hold as an upgrade path; more configuration, worker/bundle complexity, and EPL-2.0 qualification |
   431	| Native SVG based on Gitea | Maximum control and a close visual precedent | Do not start here; Ranex would inherit viewport, focus, keyboard, ARIA, routing, and performance work |
   432	| Mermaid runtime | Very small static proof of concept | Suitable for this research document, not the live authority-facing UI |
   433	| Import Airflow/Argo/Kestra/Dagu as an engine | Rich existing workflow products | Reject; Ranex already owns different workflow and authority semantics |
   434	
   435	[React Flow's layout guide](https://reactflow.dev/learn/layouting/layouting)
   436	explicitly treats layout as a separate concern and describes Dagre as a simple
   437	choice for directed trees, with ELK for more configurable cases. Its
   438	[accessibility guide](https://reactflow.dev/learn/advanced-use/accessibility)
   439	documents keyboard and screen-reader behavior. Those capabilities reduce work;
   440	they do not make a custom Ranex node accessible automatically.
   441	
   442	Dependency versions must be selected and pinned by the normal
   443	`supplier_governance` adoption process, including license compatibility,
   444	support/maintenance and vulnerability evidence, concentration risk, and an
   445	exit/upgrade plan. The maintained `@dagrejs/dagre` package must not be confused
   446	with legacy Dagre packages. No package is adopted by this research.
   447	
   448	## 12. Suggested source placement
   449	
   450	If an implementation ADR selects React, a cohesive feature slice would be:
   451	
   452	```text
   453	apps/web-dashboard/src/features/runs/execution-graph/
   454	  api/
   455	  components/
   456	  model/
   457	  layout/
   458	  accessibility/
   459	  __tests__/
   460	```
   461	
   462	Generated transport types belong in `generated-contracts`; the feature imports
   463	them. The graph feature must not import canonical transition tables or policy
   464	evaluators.
   465	
   466	The corresponding server query/projection code belongs inside:
   467	
   468	```text
   469	src/ranex/governed_execution/application/
   470	```
   471	
   472	That path is part of the accepted target tree; no main-branch implementation is
   473	claimed to exist.
   474	
   475	Technology-specific streaming delivery belongs behind the applicable Ranex
   476	transport adapter, not in the domain or reducer.
   477	
   478	## 13. MVP boundary
   479	
   480	The first useful slice is deliberately small:
   481	
   482	- Kanban card shows the selected/active run summary and **View execution**;
   483	- run page shows one read-only, left-to-right graph;
   484	- custom nodes show name, icon, state, duration, and attempts;
   485	- click/keyboard activation opens a details drawer;
   486	- pan, zoom, reset, and fit are available;
   487	- status updates live without moving nodes;
   488	- a reconnecting/stale/unknown banner is explicit;
   489	- terminal graphs can be regenerated for audit from canonical retained facts,
   490	  subject to artifact and legal-retention policy; and
   491	- an accessible ordered/table view exposes the same nodes, edges, states, and
   492	  details without requiring spatial navigation.
   493	
   494	Graph and ordered/table views are two presentations of the same projection and
   495	the user can switch between them. The requested graph remains the default
   496	prototype view. Representative linear and branching fixtures must establish
   497	whether a compact list should become the default for simple workflows; this
   498	research does not invent a node-count threshold.
   499	
   500	Not in the first slice:
   501	
   502	- workflow authoring or drag-and-drop;
   503	- run commands such as retry/cancel embedded in graph nodes;
   504	- cross-run comparison;
   505	- a timeline/Gantt view;
   506	- minimap;
   507	- user-defined graph themes;
   508	- parallel/map/dynamic topology before those semantics are authoritative; or
   509	- automatic work-item transitions.
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
   526	
   527	### 14.2 Semantic fidelity
   528	
   529	Fixtures cover:
   530	

exec
/bin/bash -lc "nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '130,360p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
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
   146	- evaluate a gate or rule in the browser;
   147	- infer that a path was skipped merely because another path is active;
   148	- turn missing, conflicting, stale, or malformed data into a green state;
   149	- mutate the workflow through drag-and-drop;
   150	- issue a permit or invoke an effect;
   151	- automatically transition the Kanban card; or
   152	- treat a Hermes session, worker process, or provider response as canonical
   153	  run state.
   154	
   155	## 5. Prior art: the wheel already exists
   156	
   157	### 5.1 Product behavior
   158	
   159	[GitHub Actions](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui)
   160	generates a real-time graph for each workflow run and lets a user inspect job
   161	and step status and logs. Its workflow files define jobs and dependency edges,
   162	and a run uses a particular workflow revision. The transferable idea is not
   163	GitHub's private implementation; it is the separation of a versioned workflow
   164	definition from one live run of that definition.
   165	
   166	[GitLab CI/CD](https://docs.gitlab.com/ci/pipelines/) offers both stage and
   167	dependency views. Its documented UX includes fan-out/fan-in graphs, grouped
   168	similar jobs, expand/collapse behavior, visible failure reasons, and
   169	click-through logs. Those are useful interaction precedents, particularly for
   170	large or repeated graphs.
   171	
   172	### 5.2 Open-source implementations
   173	
   174	| System | Proven implementation pattern | What Ranex should learn | License posture |
   175	|---|---|---|---|
   176	| [Gitea](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.vue) | Native SVG workflow graph with pan/zoom, status cards, duration, click-through details, grouped jobs, and path highlighting | Closest open implementation to the requested GitHub Actions experience; its [typed graph model](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.utils.ts) and [tests](https://github.com/go-gitea/gitea/blob/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc/web_src/js/components/WorkflowGraph.utils.test.ts) are valuable test references. The component is Vue; it is a behavior precedent, not a React reuse candidate | MIT; copied code would require preserving its notice |
   177	| [Apache Airflow](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx) | React Flow graph, ELK layout, generated API queries, and a streamed task-status overlay | Strongest direct precedent for a React implementation; it lays out structure separately, then merges live task instances without recalculating topology | Apache-2.0; use the pattern or comply with attribution/NOTICE duties for copied code |
   178	| [Argo Workflows](https://github.com/argoproj/argo-workflows/blob/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/widgets/workflow-graph.tsx) | Watched workflow status plus a DAG viewer; [Dagre computes LR/TB coordinates](https://github.com/argoproj/argo-workflows/blob/d98d7b7d73d1b24dd7258153453ea612dbb70092/ui/src/shared/components/graph/pretty-layout.ts) | Dagre is sufficient for a mature workflow product's straightforward DAG view | Apache-2.0 |
   179	| [Kestra](https://github.com/kestra-io/kestra/tree/e03a4f351328f294e67f62be60af0553401fad7a/ui/packages/topology) | Reusable Vue Flow topology package with Dagre, custom nodes/edges, collapsing, orientation, fit/zoom, and execution progress | Confirms that a flow renderer plus Dagre works beyond React and can remain a reusable presentation package | Apache-2.0 |
   180	| [Dagster](https://github.com/dagster-io/dagster/blob/014641bc1bdb71ea2c7f40371691103bbff5c9c7/js_modules/dagster-ui/packages/ui-core/src/graph/layout.ts) | Dagre-backed layout with a custom SVG viewport, ports, parent graphs, pan/zoom, and keyboard navigation | A custom renderer is possible, but its code and accessibility burden are larger than Ranex needs for the first slice | Apache-2.0 |
   181	| [Dagu](https://github.com/dagu-org/dagu/blob/3fd7eeff69e2df281cd8bd8f47348baf8d3462be/ui/src/features/dags/components/visualization/Graph.tsx) | Mermaid strings rebuilt with runtime status classes and interaction hooks | Useful evidence for a very small implementation, but repeated Mermaid rendering and DOM patching are a weaker live-UI foundation | GPL-3.0; do not copy into Ranex without a deliberate compatibility decision |
   182	
   183	This is enough evidence to avoid inventing a graph framework or importing
   184	another workflow engine. Ranex needs a small projection adapter and renderer,
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
   201	graph is laid out.” It also renders only visible elements and removes a minimap
   202	for very large graphs. Gitea supplies useful algorithms and tests for
   203	topological levels, transitive-edge reduction, grouping, cycles, stable paths,
   204	and ancestor/descendant highlighting.
   205	
   206	## 7. Proposed Ranex architecture
   207	
   208	```mermaid
   209	flowchart LR
   210	    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
   211	    A["governed_execution<br/>committed current rows + journal facts"]
   212	    P["ExecutionGraphProjection builder<br/>server-owned, versioned, deterministic"]
   213	    S["GET snapshot<br/>topology + current state"]
   214	    E["SSE status deltas<br/>cursor + expected version"]
   215	    U["Read-only dashboard graph<br/>React Flow + Dagre candidate"]
   216	    D["Node detail drawer<br/>references, reasons, logs"]
   217	
   218	    W --> P
   219	    A --> P
   220	    P --> S
   221	    P --> E
   222	    S --> U
   223	    E --> U
   224	    U --> D
   225	```
   226	
   227	### 7.1 Authority boundary
   228	
   229	`ExecutionGraphProjection` is an immutable application query/view owned by
   230	`governed_execution`. It joins:
   231	
   232	- the exact pinned workflow definition;
   233	- current committed Run, Activity, Gate, Permit, Effect, and reconciliation
   234	  facts;
   235	- safe references to separately owned policy, assurance, artifact, and human
   236	  decision records; and
   237	- projection metadata that lets a client detect stale, missing, or reordered
   238	  updates.
   239	
   240	The projection is not a new aggregate, workflow interpreter, or event store.
   241	The dashboard receives facts already interpreted by the owning server
   242	boundary. It must not replay raw events to discover canonical state.
   243	
   244	Before implementation, an RFC/ADR must register the projection as a
   245	`governed_execution` query capability, its schema under `schemas/execution/`,
   246	its generated client/server contracts, and a fitness test that prevents
   247	`work_management` or the dashboard from publishing a competing execution
   248	truth.
   249	
   250	### 7.2 Deterministic topology contract
   251	
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
   271	stable edge IDs, sources, targets, kinds, and defined choice conditions. It
   272	excludes all run status, timestamps, durations, labels localized for display,
   273	viewport state, layout coordinates, and client theme data. The exact closed
   274	field set requires a versioned schema and golden fixtures before adoption.
   275	
   276	For the same pinned definition and supported interpreter version:
   277	
   278	- node and edge identity is identical;
   279	- canonical ordering is identical;
   280	- the topology digest is identical;
   281	- deterministic-choice alternatives exist in the definition before execution;
   282	- live state changes never move, add, or delete a node; and
   283	- a topology mismatch is visible and triggers a complete refetch.
   284	
   285	Dagre output also depends on node insertion order and library behavior.
   286	Therefore Ranex must sort canonical inputs and release-pin the layout package.
   287	
   288	Dynamic graph mutation is out of scope until the workflow architecture
   289	formally defines it. An unknown node or edge is a visible unsupported/unknown
   290	condition, never an invitation for the browser to improvise topology.
   291	
   292	### 7.3 Proposed projection shape
   293	
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
   331	The canonical source axis/value is present for explanation and diagnostics. The
   332	client must not map it to color, eligibility, traversal, or visual state; those
   333	are supplied by the server's generated projection contract.
   334	
   335	## 8. Rules, gates, and process nodes
   336	
   337	Rendering every rule as a node would turn even a small run into unreadable
   338	spaghetti and confuse policy evaluation with process execution.
   339	
   340	Use this rule:
   341	
   342	- a workflow activity, durable wait, deterministic choice, evidence gate,
   343	  human decision, authorized effect, reconciliation, or terminal is a graph
   344	  node when the workflow can advance, wait, block, or terminate there;
   345	- applicable policies and individual rule/checker results appear as badges and
   346	  counts on the relevant node; and
   347	- selecting the node reveals exact rule activation, evaluation, evidence, and
   348	  reason references.
   349	
   350	An expandable gate group can be considered later if users regularly need to
   351	compare many checker results. It should not be part of the simple first slice.
   352	
   353	## 9. Visual-state semantics
   354	
   355	The UI needs a small projection vocabulary, but it must preserve distinctions
   356	from canonical states.
   357	
   358	| Visual state | Meaning |
   359	|---|---|
   360	| `NOT_STARTED` | Defined in the pinned topology and not yet enabled |

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/tests/integration/governed_execution/test_sqlite_execution_store.py | sed -n '79,260p'" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
    79	def test_transition_commits_canonical_state_version_journal_and_outbox_together(
    80	    store: SQLiteExecutionStore,
    81	    database_path: Path,
    82	) -> None:
    83	    proposed = store.append(create_event())
    84	    ready = store.append(ready_event())
    85	
    86	    assert proposed.status is ExecutionStatus.PROPOSED
    87	    assert proposed.version == 1
    88	    assert ready.status is ExecutionStatus.READY
    89	    assert ready.version == 2
    90	    assert store.load(RUN_ID) == ready
    91	
    92	    with sqlite3.connect(database_path) as connection:
    93	        connection.row_factory = sqlite3.Row
    94	        state_row = connection.execute(
    95	            """
    96	            SELECT canonical_state_json, version, last_event_id
    97	            FROM execution_state
    98	            WHERE execution_id = ?
    99	            """,
   100	            (str(RUN_ID),),
   101	        ).fetchone()
   102	        journal_rows = connection.execute(
   103	            """
   104	            SELECT event_id, previous_version, resulting_version,
   105	                   event_json, resulting_state_json
   106	            FROM execution_journal
   107	            ORDER BY sequence
   108	            """
   109	        ).fetchall()
   110	        outbox_rows = connection.execute(
   111	            """
   112	            SELECT event_id, aggregate_version, payload_json
   113	            FROM execution_outbox
   114	            ORDER BY sequence
   115	            """
   116	        ).fetchall()
   117	
   118	    assert state_row is not None
   119	    state_document = json.loads(state_row["canonical_state_json"])
   120	    assert state_row["canonical_state_json"] == canonical_json(state_document)
   121	    assert state_row["version"] == state_document["version"] == 2
   122	    assert state_row["last_event_id"] == str(event_id(2))
   123	
   124	    assert [
   125	        (row["event_id"], row["previous_version"], row["resulting_version"])
   126	        for row in journal_rows
   127	    ] == [
   128	        (str(event_id(1)), 0, 1),
   129	        (str(event_id(2)), 1, 2),
   130	    ]
   131	    assert all(
   132	        row["event_json"] == canonical_json(json.loads(row["event_json"]))
   133	        and row["resulting_state_json"]
   134	        == canonical_json(json.loads(row["resulting_state_json"]))
   135	        for row in journal_rows
   136	    )
   137	
   138	    assert [(row["event_id"], row["aggregate_version"]) for row in outbox_rows] == [
   139	        (str(event_id(1)), 1),
   140	        (str(event_id(2)), 2),
   141	    ]
   142	    assert all(
   143	        row["payload_json"] == canonical_json(json.loads(row["payload_json"]))
   144	        for row in outbox_rows
   145	    )
   146	
   147	
   148	def test_journal_is_database_enforced_append_only(
   149	    store: SQLiteExecutionStore,
   150	    database_path: Path,
   151	) -> None:
   152	    store.append(create_event())
   153	
   154	    with sqlite3.connect(database_path) as connection:
   155	        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
   156	            connection.execute("UPDATE execution_journal SET event_type = 'forged'")
   157	        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
   158	            connection.execute("DELETE FROM execution_journal")
   159	
   160	
   161	def test_stale_event_rolls_back_without_extra_journal_or_outbox_rows(
   162	    store: SQLiteExecutionStore,
   163	) -> None:
   164	    store.append(create_event())
   165	    store.append(ready_event())
   166	
   167	    with pytest.raises(ValueError, match="expected version"):
   168	        store.append(ready_event())
   169	
   170	    assert store.count_journal_entries(RUN_ID) == 2
   171	    assert store.count_outbox_entries(RUN_ID) == 2
   172	
   173	
   174	def test_load_rejects_relational_and_canonical_version_disagreement(
   175	    store: SQLiteExecutionStore,
   176	    database_path: Path,
   177	) -> None:
   178	    store.append(create_event())
   179	    with sqlite3.connect(database_path) as connection:
   180	        connection.execute(
   181	            "UPDATE execution_state SET version = 99 WHERE execution_id = ?",
   182	            (str(RUN_ID),),
   183	        )
   184	
   185	    with pytest.raises(
   186	        ExecutionPersistenceIntegrityError,
   187	        match="version disagrees",
   188	    ):
   189	        store.load(RUN_ID)
   190	
   191	
   192	def test_load_rejects_relational_and_canonical_identity_disagreement(
   193	    store: SQLiteExecutionStore,
   194	    database_path: Path,
   195	) -> None:
   196	    store.append(create_event())
   197	    with sqlite3.connect(database_path) as connection:
   198	        raw = connection.execute(
   199	            """
   200	            SELECT canonical_state_json
   201	            FROM execution_state
   202	            WHERE execution_id = ?
   203	            """,
   204	            (str(RUN_ID),),
   205	        ).fetchone()
   206	        assert raw is not None
   207	        document = json.loads(raw[0])
   208	        document["execution_id"] = str(
   209	            Identity.parse(
   210	                "run_01890f47-25a1-7e09-98b3-5f5f6bb25af7",
   211	                expected_prefix="run",
   212	            )
   213	        )
   214	        connection.execute(
   215	            """
   216	            UPDATE execution_state
   217	            SET canonical_state_json = ?
   218	            WHERE execution_id = ?
   219	            """,
   220	            (canonical_json(document), str(RUN_ID)),
   221	        )
   222	
   223	    with pytest.raises(
   224	        ExecutionPersistenceIntegrityError,
   225	        match="identity disagrees",
   226	    ):
   227	        store.load(RUN_ID)
   228	
   229	
   230	def test_concurrent_same_version_transitions_have_one_cas_winner(
   231	    store: SQLiteExecutionStore,
   232	) -> None:
   233	    store.append(create_event())
   234	    barrier = Barrier(2)
   235	
   236	    def attempt() -> Execution | Exception:
   237	        barrier.wait()
   238	        try:
   239	            return store.append(ready_event())
   240	        except Exception as exc:
   241	            return exc
   242	
   243	    with ThreadPoolExecutor(max_workers=2) as executor:
   244	        results = tuple(executor.map(lambda _index: attempt(), range(2)))
   245	
   246	    assert sum(isinstance(result, Execution) for result in results) == 1
   247	    assert sum(isinstance(result, Exception) for result in results) == 1
   248	    assert store.load(RUN_ID).version == 2  # type: ignore[union-attr]
   249	    assert store.count_journal_entries(RUN_ID) == 2
   250	    assert store.count_outbox_entries(RUN_ID) == 2

web search: 
web search: site:docs.temporal.io workflow replay nondeterminism patching versioning worker versioning replay tests history ...
web search: 
web search: Temporal documentation deterministic workflow replay event history nondeterminism replay test official ...
web search: 
web search: site:github.com/temporalio/documentation replay workflow history Replayer patching GetVersion ...
web search: 
web search: site:docs.dbos.dev workflow recovery exactly once transactions crash testing official ...
web search: 
web search: site:sqlite.org atomic commit transactions power failure testing VFS crash simulation ...
web search: 
web search: official documentation event sourcing snapshot stream revision validate snapshot journal consistency ...
web search: 
web search: transactional outbox pattern official reliable messages database transaction Debezium docs ...
web search: 
web search: site:github.com/dbos-inc/dbos-transact-py test crash recovery kill process workflow ...
web search: 
web search: durable execution crash testing kill process checkpoint recovery official documentation ...
web search: 
web search: site:github.com/apache/airflow Graph.tsx useTaskInstanceStream React Flow ELK streamed task status ...
web search: 
web search: https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx
web search: 
web search: "useGridTiSummariesStream" Airflow ...
web search: 
web search: Temporal customers Snap Box official case study production adopters ...
web search: 
web search: site:github.com/xyflow/xyflow LICENSE MIT ...
web search: 
web search: https://github.com/kieler/elkjs/blob/master/LICENSE.md
web search: 
web search: 
web search: 
web search: site:github.com/dagu-org/dagu license GPL-3.0 ...
web search: 
web search: https://github.com/dagu-org/dagu
web search: 
web search: GitHub Actions workflow run uses workflow file from commit SHA rerun official docs ...
web search: 
web search: site:github.com/argoproj/argo-workflows "watchWorkflows" UI ...
codex
The strongest direct analogue for Ranex’s missing consistency proof is Temporal’s own persistence contract: mutable state and tasks are transactional, mutable state records the latest history event it reflects, and an event is valid only through that linkage. Atomicity alone is explicitly not the whole proof. For graph updates, I’m also checking Kubernetes’ list/watch cursor protocol because it supplies the exact “snapshot + resume token + relist on gap” precedent the internal proposal currently treats as a fresh design.
web search: 
web search: site:kubernetes.io/docs api concepts resourceVersion list watch 410 Gone relist consistent snapshot ...
web search: 
web search: site:docs.axoniq.io event upcasting revision old events official ...
context compacted
codex
The local audit is complete. I’m now closing the evidence gaps around definition versioning, cross-checkable journal heads, crash injection, and graph update protocols; the key distinction emerging is between “atomic together” and “provably semantically consistent.”
Local Ranex and tracer audit is complete; external primary-source verification is underway.
  ✓ Audit Ranex ADR, tracer implementation/tests, graph proposal, and licence
  → Verify deterministic replay and definition-versioning prior art
  • Verify journal/snapshot/outbox consistency and crash-testing prior art
  • Verify live run-graph transport/rendering and licences
  • Synthesize verdict table, shortlist, direct answers, novelty, inferences, and search coverage
web search: 
web search: site:docs.particular.net nservicebus outbox atomic business data outgoing messages transaction official ...
exec
/bin/bash -lc "rg -n \"class|outbox|journal|load\\(|BEGIN IMMEDIATE|synchronous|workflow_request_ref|replay_execution|reduce_execution\" .claude/worktrees/kernel-tracer/src/ranex/governed_execution .claude/worktrees/kernel-tracer/tests/replay .claude/worktrees/kernel-tracer/tests/resilience docs/research/deterministic-run-graph-visualization-research-2026-07-30.md docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md LICENSE-RANEX.md" in /home/soultransit/devtony/ranex
 succeeded in 0ms:
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:134:- `OUTCOME_UNKNOWN` is a first-class result and must enter reconciliation;
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:138:  classified retry, cancellation, compensation request, reconciliation wait,
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:181:| [Dagu](https://github.com/dagu-org/dagu/blob/3fd7eeff69e2df281cd8bd8f47348baf8d3462be/ui/src/features/dags/components/visualization/Graph.tsx) | Mermaid strings rebuilt with runtime status classes and interaction hooks | Useful evidence for a very small implementation, but repeated Mermaid rendering and DOM patching are a weaker live-UI foundation | GPL-3.0; do not copy into Ranex without a deliberate compatibility decision |
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:211:    A["governed_execution<br/>committed current rows + journal facts"]
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:325:| Safety | classification, redaction state, detail availability |
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:365:| `FAILED` | A terminal classified failure is recorded |
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:561:- Authorization and classification/redaction are independently enforced when
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:576:| Rules overwhelm the flow | Keep rules in badges/details; make only process-stopping gates first-class nodes |
docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:590:- The journal, current rows, stable IDs, and exact subject bindings provide
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:16:| Compatibility/migration class | Additive executable documentation contract; runtime implementation remains unassessed |
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:17:| Security/data class | Public architecture decision; legal, credential, package, runtime, and release evidence retain their own classification |
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:57:its cited research excerpt and comparing obligation class, scope, and
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:106:4. the append-only transition/audit journal and outbox in one SQLite unit of
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:130:underscore-only guard, a deterministic check class, and the stage that must
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:177:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:187:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:197:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:199:    provision: "Workflow semantics and the execution reducer are first-class kernel responsibilities."
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:207:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:217:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:227:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:229:    provision: "Policy enforcement, evidence and gate semantics, permit authority, module governance, and atomic event/outbox state remain kernel-owned."
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:237:    check_class: "MODULE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:247:    check_class: "MODULE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:257:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:267:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:277:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:287:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:297:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:307:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:317:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:327:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:337:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:347:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:357:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:367:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:377:    check_class: "MODULE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:387:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:397:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:407:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:417:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:427:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:437:    check_class: "EVIDENCE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:447:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:457:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:459:    provision: "Canonical state and version, audit or domain record, permit consumption, and outbox intent commit atomically."
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:467:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:477:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:487:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:497:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:507:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:517:    check_class: "MODULE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:527:    check_class: "EVIDENCE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:537:    check_class: "MIGRATION_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:547:    check_class: "MIGRATION_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:557:    check_class: "MIGRATION_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:567:    check_class: "LEGAL_COMPLIANCE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:577:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:587:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:597:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:607:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:617:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:627:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:637:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:647:    check_class: "SUPPLY_CHAIN_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:657:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:667:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:677:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:687:    check_class: "MIGRATION_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:697:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:707:    check_class: "SUPPLY_CHAIN_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:717:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:727:    check_class: "LEGAL_COMPLIANCE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:737:    check_class: "RELEASE_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:747:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:757:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:767:    check_class: "ARCHITECTURE_CONTRACT"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:777:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:779:    provision: "The clean kernel contains an append-only transition and audit journal and an outbox, and persists them with canonical execution state and version through one SQLite unit of work."
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:787:    check_class: "MIGRATION_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:797:    check_class: "AUTHORITY_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:807:    check_class: "STATIC_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:817:    check_class: "RUNTIME_FITNESS"
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1162:Those rows are a closed denominator of material disposition classes, not a
docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:1172:- Phase 1 cannot be reclassified as mere sequencing or removed from the
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:11:    reduce_execution,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:12:    replay_execution,
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:34:            workflow_request_ref="workflow-request:sha256:one",
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:61:        direct = reduce_execution(direct, event)
.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:62:    replayed = replay_execution(events)
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31:def test_failure_between_journal_and_outbox_leaves_no_partial_state(
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:45:            workflow_request_ref="workflow-request:sha256:crash",
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:52:            CREATE TRIGGER simulate_crash_before_outbox
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:53:            BEFORE INSERT ON execution_outbox
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:56:                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:72:    unchanged = store.load(RUN_ID)
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:77:    assert store.count_journal_entries(RUN_ID) == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:78:    assert store.count_outbox_entries(RUN_ID) == 1
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:86:                (SELECT COUNT(*) FROM execution_journal
.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:88:                (SELECT COUNT(*) FROM execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:3:from dataclasses import dataclass
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:32:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:33:class ExecutionEventMetadata:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:59:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:60:class ExecutionCreated(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:63:    workflow_request_ref: str
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:77:        _require_text(self.workflow_request_ref, field="workflow_request_ref")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:80:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:81:class ExecutionMarkedReady(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:92:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:93:class ExecutionStarted(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:101:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:102:class ExecutionWaited(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:110:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:111:class ExecutionResumed(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:119:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:120:class ExecutionBlocked(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:135:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:136:class ExecutionUnblocked(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:154:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:155:class ExecutionSucceeded(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:163:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:164:class ExecutionFailed(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:177:@dataclass(frozen=True, slots=True, kw_only=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/events.py:178:class ExecutionCancelled(ExecutionEventMetadata):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:4:from dataclasses import dataclass, replace
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:23:class InvalidExecutionTransition(ValueError):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:52:@dataclass(frozen=True, slots=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:53:class Execution:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:57:    workflow_request_ref: str
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:99:def reduce_execution(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:117:            workflow_request_ref=event.workflow_request_ref,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226:def replay_execution(events: Iterable[ExecutionEvent]) -> Execution:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:234:        state = reduce_execution(state, event)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1:BEGIN IMMEDIATE;
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:11:CREATE TABLE IF NOT EXISTS execution_journal (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35:CREATE TABLE IF NOT EXISTS execution_outbox (
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:43:        REFERENCES execution_journal(event_id),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:47:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_update
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:48:BEFORE UPDATE ON execution_journal
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:50:    SELECT RAISE(ABORT, 'execution_journal is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:53:CREATE TRIGGER IF NOT EXISTS execution_journal_reject_delete
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:54:BEFORE DELETE ON execution_journal
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:56:    SELECT RAISE(ABORT, 'execution_journal is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:59:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_update
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:60:BEFORE UPDATE ON execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:62:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:65:CREATE TRIGGER IF NOT EXISTS execution_outbox_reject_delete
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:66:BEFORE DELETE ON execution_outbox
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:68:    SELECT RAISE(ABORT, 'execution_outbox is append-only');
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/status.py:6:class ExecutionStatus(StrEnum):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:29:    reduce_execution,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:40:        "workflow_request_ref",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:50:class ExecutionPersistenceIntegrityError(RuntimeError):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:54:class ConcurrentExecutionWriteError(RuntimeError):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:64:        "workflow_request_ref": execution.workflow_request_ref,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:113:        workflow_request_ref=_require_string(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:114:            document["workflow_request_ref"],
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:115:            "workflow_request_ref",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:142:                "workflow_request_ref": event.workflow_request_ref,
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183:class SQLiteExecutionStore(ExecutionRepository):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:184:    """State, audit journal, and outbox committed in one SQLite transaction."""
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:197:        connection.execute("PRAGMA synchronous = FULL")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:210:    def load(self, execution_id: Identity) -> Execution | None:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:225:        connection.execute("BEGIN IMMEDIATE")
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:238:            next_state = reduce_execution(current, event)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:303:                INSERT INTO execution_journal(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:330:            outbox_document = {
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:331:                "schema_version": "execution-outbox/v1",
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:341:                INSERT INTO execution_outbox(
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:353:                    canonical_json(outbox_document),
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:366:    def count_journal_entries(self, execution_id: Identity) -> int:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:367:        return self._count_rows("execution_journal", execution_id)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:369:    def count_outbox_entries(self, execution_id: Identity) -> int:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:370:        return self._count_rows("execution_outbox", execution_id)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:374:        if table not in {"execution_journal", "execution_outbox"}:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:3:from dataclasses import dataclass
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:13:@dataclass(frozen=True, slots=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:14:class ApplicationControlRequest:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:43:@dataclass(frozen=True, slots=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:44:class ApplicationControlFacts:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:52:@dataclass(frozen=True, slots=True)
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/application_control.py:53:class ApplicationControlDecision:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/application_control_pep.py:22:class ApplicationControlPEP:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/execution_repository.py:10:class ExecutionRepository(Protocol):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/execution_repository.py:11:    def load(self, execution_id: Identity) -> Execution | None:
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/ports/application_control_policy.py:11:class ApplicationControlPolicy(Protocol):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/policy/deterministic.py:18:class DeterministicPolicyAdapter(ApplicationControlPolicy):
.claude/worktrees/kernel-tracer/src/ranex/governed_execution/application/gate_controller.py:61:class GateController:

web search: 
web search: site:temporal.io customers NVIDIA Snap Alaska Airlines Temporal 1000 customers ...
web search: 
web search: site:news.apache.org "Apache Airflow" Adobe Airbnb Etsy Google ING Lyft PayPal Reddit Twitter United Airlines ...
web search: 
web search: https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx
web search: 
web search: 'resourceVersion'
web search: 
web search: repo:apache/airflow "useGridTiSummariesStream" ...
web search: 
web search: https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md
web search: 
web search: 'latest History Event'
web search: 
web search: https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing
web search: 
web search: 'permanently associated'
web search: 
web search: https://docs.dbos.dev/golang/tutorials/transaction-tutorial
web search: 
web search: site:docs.dbos.dev "ApplicationVersion" workflow version DBOS ...
web search: 
web search: https://sqlite.org/testing.html
web search: 
web search: 'network filesystem'
web search: 
web search: https://github.com/temporalio/temporal/blob/main/LICENSE
web search: 
web search: https://github.com/xyflow/xyflow/blob/main/LICENSE
web search: 
web search: 'GNU GENERAL PUBLIC LICENSE'
web search: 
web search: https://github.com/restatedev/restate/blob/main/LICENSE
web search: 
web search: 'RT0016'
web search: 
web search: https://martendb.io/tutorials/read-model-projections
exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql | sed -n '1,72p'
nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '183,365p'
nl -ba .claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py | sed -n '20,72p'
nl -ba .claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py | sed -n '28,102p'" in /home/soultransit/devtony/ranex
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
   183	class SQLiteExecutionStore(ExecutionRepository):
   184	    """State, audit journal, and outbox committed in one SQLite transaction."""
   185	
   186	    def __init__(self, path: Path) -> None:
   187	        self._path = path
   188	
   189	    def _connect(self) -> sqlite3.Connection:
   190	        connection = sqlite3.connect(
   191	            self._path,
   192	            isolation_level=None,
   193	            timeout=5.0,
   194	        )
   195	        connection.row_factory = sqlite3.Row
   196	        connection.execute("PRAGMA foreign_keys = ON")
   197	        connection.execute("PRAGMA synchronous = FULL")
   198	        return connection
   199	
   200	    def initialize(self) -> None:
   201	        self._path.parent.mkdir(parents=True, exist_ok=True)
   202	        migration = _MIGRATION.read_text(encoding="utf-8")
   203	        connection = self._connect()
   204	        try:
   205	            connection.executescript(migration)
   206	        finally:
   207	            connection.close()
   208	        self._path.chmod(0o600)
   209	
   210	    def load(self, execution_id: Identity) -> Execution | None:
   211	        self._require_run_id(execution_id)
   212	        with closing(self._connect()) as connection:
   213	            row = connection.execute(
   214	                """
   215	                SELECT execution_id, canonical_state_json, version, last_event_id
   216	                FROM execution_state
   217	                WHERE execution_id = ?
   218	                """,
   219	                (str(execution_id),),
   220	            ).fetchone()
   221	        return None if row is None else self._decode_state_row(row)
   222	
   223	    def append(self, event: ExecutionEvent) -> Execution:
   224	        connection = self._connect()
   225	        connection.execute("BEGIN IMMEDIATE")
   226	        try:
   227	            current_row = connection.execute(
   228	                """
   229	                SELECT execution_id, canonical_state_json, version, last_event_id
   230	                FROM execution_state
   231	                WHERE execution_id = ?
   232	                """,
   233	                (str(event.execution_id),),
   234	            ).fetchone()
   235	            current = (
   236	                None if current_row is None else self._decode_state_row(current_row)
   237	            )
   238	            next_state = reduce_execution(current, event)
   239	            next_document = _execution_to_document(next_state)
   240	            next_json = canonical_json(next_document)
   241	
   242	            if current is None:
   243	                connection.execute(
   244	                    """
   245	                    INSERT INTO execution_state(
   246	                        execution_id,
   247	                        canonical_state_json,
   248	                        version,
   249	                        last_event_id,
   250	                        updated_at
   251	                    ) VALUES (?, ?, ?, ?, ?)
   252	                    """,
   253	                    (
   254	                        str(next_state.execution_id),
   255	                        next_json,
   256	                        next_state.version,
   257	                        str(next_state.last_event_id),
   258	                        next_state.updated_at,
   259	                    ),
   260	                )
   261	                previous_json = None
   262	                previous_version = 0
   263	            else:
   264	                assert current_row is not None
   265	                previous_json = str(current_row["canonical_state_json"])
   266	                previous_version = current.version
   267	                cursor = connection.execute(
   268	                    """
   269	                    UPDATE execution_state
   270	                    SET canonical_state_json = ?,
   271	                        version = ?,
   272	                        last_event_id = ?,
   273	                        updated_at = ?
   274	                    WHERE execution_id = ?
   275	                      AND version = ?
   276	                      AND canonical_state_json = ?
   277	                    """,
   278	                    (
   279	                        next_json,
   280	                        next_state.version,
   281	                        str(next_state.last_event_id),
   282	                        next_state.updated_at,
   283	                        str(next_state.execution_id),
   284	                        current.version,
   285	                        previous_json,
   286	                    ),
   287	                )
   288	                if cursor.rowcount != 1:
   289	                    raise ConcurrentExecutionWriteError(
   290	                        "canonical execution compare-and-swap failed"
   291	                    )
   292	
   293	            event_document = _event_to_document(event)
   294	            event_json = canonical_json(event_document)
   295	            resulting_digest = canonical_sha256(next_document)
   296	            previous_digest = (
   297	                None
   298	                if previous_json is None
   299	                else canonical_sha256(json.loads(previous_json))
   300	            )
   301	            connection.execute(
   302	                """
   303	                INSERT INTO execution_journal(
   304	                    event_id,
   305	                    execution_id,
   306	                    event_type,
   307	                    previous_version,
   308	                    resulting_version,
   309	                    event_json,
   310	                    previous_state_sha256,
   311	                    resulting_state_sha256,
   312	                    resulting_state_json,
   313	                    recorded_at
   314	                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
   315	                """,
   316	                (
   317	                    str(event.event_id),
   318	                    str(event.execution_id),
   319	                    type(event).__name__,
   320	                    previous_version,
   321	                    next_state.version,
   322	                    event_json,
   323	                    previous_digest,
   324	                    resulting_digest,
   325	                    next_json,
   326	                    event.occurred_at,
   327	                ),
   328	            )
   329	
   330	            outbox_document = {
   331	                "schema_version": "execution-outbox/v1",
   332	                "event_id": str(event.event_id),
   333	                "event_type": type(event).__name__,
   334	                "execution_id": str(event.execution_id),
   335	                "aggregate_version": next_state.version,
   336	                "occurred_at": event.occurred_at,
   337	                "event": event_document,
   338	            }
   339	            connection.execute(
   340	                """
   341	                INSERT INTO execution_outbox(
   342	                    event_id,
   343	                    execution_id,
   344	                    aggregate_version,
   345	                    payload_json,
   346	                    created_at
   347	                ) VALUES (?, ?, ?, ?, ?)
   348	                """,
   349	                (
   350	                    str(event.event_id),
   351	                    str(event.execution_id),
   352	                    next_state.version,
   353	                    canonical_json(outbox_document),
   354	                    event.occurred_at,
   355	                ),
   356	            )
   357	            connection.execute("COMMIT")
   358	            return next_state
   359	        except BaseException:
   360	            if connection.in_transaction:
   361	                connection.execute("ROLLBACK")
   362	            raise
   363	        finally:
   364	            connection.close()
   365	
    20	        expected_prefix=prefix,
    21	    )
    22	
    23	
    24	def test_replay_reproduces_identical_final_state_and_version() -> None:
    25	    run_id = identity("run", "a01")
    26	    events = (
    27	        ExecutionCreated(
    28	            event_id=identity("transition", "b01"),
    29	            execution_id=run_id,
    30	            expected_version=0,
    31	            occurred_at="2026-07-29T01:00:00Z",
    32	            work_item_id=identity("work", "a02"),
    33	            created_by_principal_id=identity("principal", "a03"),
    34	            workflow_request_ref="workflow-request:sha256:one",
    35	        ),
    36	        ExecutionMarkedReady(
    37	            event_id=identity("transition", "b02"),
    38	            execution_id=run_id,
    39	            expected_version=1,
    40	            occurred_at="2026-07-29T01:00:01Z",
    41	            readiness_snapshot_ref="snapshot:sha256:ready",
    42	        ),
    43	        ExecutionStarted(
    44	            event_id=identity("transition", "b03"),
    45	            execution_id=run_id,
    46	            expected_version=2,
    47	            occurred_at="2026-07-29T01:00:02Z",
    48	            authorization_ref="authorization:sha256:start",
    49	        ),
    50	        ExecutionSucceeded(
    51	            event_id=identity("transition", "b04"),
    52	            execution_id=run_id,
    53	            expected_version=3,
    54	            occurred_at="2026-07-29T01:00:03Z",
    55	            outcome_ref="outcome:sha256:success",
    56	        ),
    57	    )
    58	
    59	    direct = None
    60	    for event in events:
    61	        direct = reduce_execution(direct, event)
    62	    replayed = replay_execution(events)
    63	
    64	    assert replayed == direct
    65	    assert replayed.status is ExecutionStatus.SUCCEEDED
    66	    assert replayed.version == len(events) == 4
    28	    )
    29	
    30	
    31	def test_failure_between_journal_and_outbox_leaves_no_partial_state(
    32	    tmp_path: Path,
    33	) -> None:
    34	    database_path = tmp_path / "crash-boundary.sqlite3"
    35	    store = SQLiteExecutionStore(database_path)
    36	    store.initialize()
    37	    store.append(
    38	        ExecutionCreated(
    39	            event_id=identity("transition", "a12"),
    40	            execution_id=RUN_ID,
    41	            expected_version=0,
    42	            occurred_at="2026-07-29T03:00:00Z",
    43	            work_item_id=identity("work", "a13"),
    44	            created_by_principal_id=identity("principal", "a14"),
    45	            workflow_request_ref="workflow-request:sha256:crash",
    46	        )
    47	    )
    48	
    49	    with sqlite3.connect(database_path) as connection:
    50	        connection.executescript(
    51	            """
    52	            CREATE TRIGGER simulate_crash_before_outbox
    53	            BEFORE INSERT ON execution_outbox
    54	            WHEN NEW.aggregate_version = 2
    55	            BEGIN
    56	                SELECT RAISE(ABORT, 'simulated crash before outbox insert');
    57	            END;
    58	            """
    59	        )
    60	
    61	    with pytest.raises(sqlite3.DatabaseError, match="simulated crash"):
    62	        store.append(
    63	            ExecutionMarkedReady(
    64	                event_id=identity("transition", "a15"),
    65	                execution_id=RUN_ID,
    66	                expected_version=1,
    67	                occurred_at="2026-07-29T03:00:01Z",
    68	                readiness_snapshot_ref="snapshot:sha256:crash-ready",
    69	            )
    70	        )
    71	
    72	    unchanged = store.load(RUN_ID)
    73	    assert unchanged is not None
    74	    assert unchanged.status is ExecutionStatus.PROPOSED
    75	    assert unchanged.version == 1
    76	    assert unchanged.last_event_id == identity("transition", "a12")
    77	    assert store.count_journal_entries(RUN_ID) == 1
    78	    assert store.count_outbox_entries(RUN_ID) == 1
    79	
    80	    with sqlite3.connect(database_path) as connection:
    81	        absent_everywhere = connection.execute(
    82	            """
    83	            SELECT
    84	                (SELECT COUNT(*) FROM execution_state
    85	                 WHERE last_event_id = ?) +
    86	                (SELECT COUNT(*) FROM execution_journal
    87	                 WHERE event_id = ?) +
    88	                (SELECT COUNT(*) FROM execution_outbox
    89	                 WHERE event_id = ?)
    90	            """,
    91	            (
    92	                str(identity("transition", "a15")),
    93	                str(identity("transition", "a15")),
    94	                str(identity("transition", "a15")),
    95	            ),
    96	        ).fetchone()
    97	
    98	    assert absent_everywhere == (0,)

exec
/bin/bash -lc "nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '50,180p'
nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py | sed -n '386,430p'
nl -ba .claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py | sed -n '52,68p;220,240p'
nl -ba docs/research/deterministic-run-graph-visualization-research-2026-07-30.md | sed -n '130,166p;206,290p;383,446p;511,546p;707,727p'
nl -ba docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md | sed -n '742,822p;1048,1065p;1148,1160p'
nl -ba LICENSE-RANEX.md | sed -n '1,72p'" in /home/soultransit/devtony/ranex
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
   128	def _event_to_document(event: ExecutionEvent) -> dict[str, object]:
   129	    document: dict[str, object] = {
   130	        "schema_version": "execution-event/v1",
   131	        "event_type": type(event).__name__,
   132	        "event_id": str(event.event_id),
   133	        "execution_id": str(event.execution_id),
   134	        "expected_version": event.expected_version,
   135	        "occurred_at": event.occurred_at,
   136	    }
   137	    if isinstance(event, ExecutionCreated):
   138	        document.update(
   139	            {
   140	                "work_item_id": str(event.work_item_id),
   141	                "created_by_principal_id": str(event.created_by_principal_id),
   142	                "workflow_request_ref": event.workflow_request_ref,
   143	            }
   144	        )
   145	    elif isinstance(event, ExecutionMarkedReady):
   146	        document["readiness_snapshot_ref"] = event.readiness_snapshot_ref
   147	    elif isinstance(event, ExecutionStarted):
   148	        document["authorization_ref"] = event.authorization_ref
   149	    elif isinstance(event, ExecutionWaited):
   150	        document["wait_reason_code"] = event.wait_reason_code
   151	    elif isinstance(event, ExecutionResumed):
   152	        document["signal_ref"] = event.signal_ref
   153	    elif isinstance(event, ExecutionBlocked):
   154	        document.update(
   155	            {
   156	                "block_reason_code": event.block_reason_code,
   157	                "blocking_refs": list(event.blocking_refs),
   158	            }
   159	        )
   160	    elif isinstance(event, ExecutionUnblocked):
   161	        document.update(
   162	            {
   163	                "target_status": event.target_status.value,
   164	                "refreshed_evidence_ref": event.refreshed_evidence_ref,
   165	            }
   166	        )
   167	    elif isinstance(event, ExecutionSucceeded):
   168	        document["outcome_ref"] = event.outcome_ref
   169	    elif isinstance(event, ExecutionFailed):
   170	        document.update(
   171	            {
   172	                "failure_reason_code": event.failure_reason_code,
   173	                "evidence_ref": event.evidence_ref,
   174	            }
   175	        )
   176	    elif isinstance(event, ExecutionCancelled):
   177	        document["decision_ref"] = event.decision_ref
   178	    else:
   179	        raise TypeError(f"unsupported execution event: {type(event).__name__}")
   180	    return document
   386	        if not isinstance(execution_id, Identity) or execution_id.prefix != "run":
   387	            raise ValueError("execution_id must be a canonical run identity")
   388	
   389	    @staticmethod
   390	    def _decode_state_row(row: sqlite3.Row) -> Execution:
   391	        raw = str(row["canonical_state_json"])
   392	        try:
   393	            document = json.loads(raw)
   394	        except json.JSONDecodeError as exc:
   395	            raise ExecutionPersistenceIntegrityError(
   396	                "canonical execution state is not JSON"
   397	            ) from exc
   398	        if not isinstance(document, dict) or canonical_json(document) != raw:
   399	            raise ExecutionPersistenceIntegrityError(
   400	                "execution state is not canonically serialized"
   401	            )
   402	        try:
   403	            state = _execution_from_document(document)
   404	        except (TypeError, ValueError) as exc:
   405	            raise ExecutionPersistenceIntegrityError(
   406	                "canonical execution state is invalid"
   407	            ) from exc
   408	        if int(row["version"]) != state.version:
   409	            raise ExecutionPersistenceIntegrityError(
   410	                "relational version disagrees with canonical state version"
   411	            )
   412	        if str(row["last_event_id"]) != str(state.last_event_id):
   413	            raise ExecutionPersistenceIntegrityError(
   414	                "relational last event disagrees with canonical state"
   415	            )
   416	        if str(row["execution_id"]) != str(state.execution_id):
   417	            raise ExecutionPersistenceIntegrityError(
   418	                "relational identity disagrees with canonical state identity"
   419	            )
   420	        return state
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
   146	- evaluate a gate or rule in the browser;
   147	- infer that a path was skipped merely because another path is active;
   148	- turn missing, conflicting, stale, or malformed data into a green state;
   149	- mutate the workflow through drag-and-drop;
   150	- issue a permit or invoke an effect;
   151	- automatically transition the Kanban card; or
   152	- treat a Hermes session, worker process, or provider response as canonical
   153	  run state.
   154	
   155	## 5. Prior art: the wheel already exists
   156	
   157	### 5.1 Product behavior
   158	
   159	[GitHub Actions](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui)
   160	generates a real-time graph for each workflow run and lets a user inspect job
   161	and step status and logs. Its workflow files define jobs and dependency edges,
   162	and a run uses a particular workflow revision. The transferable idea is not
   163	GitHub's private implementation; it is the separation of a versioned workflow
   164	definition from one live run of that definition.
   165	
   166	[GitLab CI/CD](https://docs.gitlab.com/ci/pipelines/) offers both stage and
   206	## 7. Proposed Ranex architecture
   207	
   208	```mermaid
   209	flowchart LR
   210	    W["Approved WorkflowDefinition<br/>ref + digest + interpreter version"]
   211	    A["governed_execution<br/>committed current rows + journal facts"]
   212	    P["ExecutionGraphProjection builder<br/>server-owned, versioned, deterministic"]
   213	    S["GET snapshot<br/>topology + current state"]
   214	    E["SSE status deltas<br/>cursor + expected version"]
   215	    U["Read-only dashboard graph<br/>React Flow + Dagre candidate"]
   216	    D["Node detail drawer<br/>references, reasons, logs"]
   217	
   218	    W --> P
   219	    A --> P
   220	    P --> S
   221	    P --> E
   222	    S --> U
   223	    E --> U
   224	    U --> D
   225	```
   226	
   227	### 7.1 Authority boundary
   228	
   229	`ExecutionGraphProjection` is an immutable application query/view owned by
   230	`governed_execution`. It joins:
   231	
   232	- the exact pinned workflow definition;
   233	- current committed Run, Activity, Gate, Permit, Effect, and reconciliation
   234	  facts;
   235	- safe references to separately owned policy, assurance, artifact, and human
   236	  decision records; and
   237	- projection metadata that lets a client detect stale, missing, or reordered
   238	  updates.
   239	
   240	The projection is not a new aggregate, workflow interpreter, or event store.
   241	The dashboard receives facts already interpreted by the owning server
   242	boundary. It must not replay raw events to discover canonical state.
   243	
   244	Before implementation, an RFC/ADR must register the projection as a
   245	`governed_execution` query capability, its schema under `schemas/execution/`,
   246	its generated client/server contracts, and a fitness test that prevents
   247	`work_management` or the dashboard from publishing a competing execution
   248	truth.
   249	
   250	### 7.2 Deterministic topology contract
   251	
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
   271	stable edge IDs, sources, targets, kinds, and defined choice conditions. It
   272	excludes all run status, timestamps, durations, labels localized for display,
   273	viewport state, layout coordinates, and client theme data. The exact closed
   274	field set requires a versioned schema and golden fixtures before adoption.
   275	
   276	For the same pinned definition and supported interpreter version:
   277	
   278	- node and edge identity is identical;
   279	- canonical ordering is identical;
   280	- the topology digest is identical;
   281	- deterministic-choice alternatives exist in the definition before execution;
   282	- live state changes never move, add, or delete a node; and
   283	- a topology mismatch is visible and triggers a complete refetch.
   284	
   285	Dagre output also depends on node insertion order and library behavior.
   286	Therefore Ranex must sort canonical inputs and release-pin the layout package.
   287	
   288	Dynamic graph mutation is out of scope until the workflow architecture
   289	formally defines it. An unknown node or edge is a visible unsupported/unknown
   290	condition, never an invitation for the browser to improvise topology.
   383	## 10. Snapshot and live-update transport
   384	
   385	Proposed read APIs:
   386	
   387	```text
   388	GET /api/work-items/{work_item_id}/runs
   389	GET /api/runs/{run_id}/graph
   390	GET /api/runs/{run_id}/graph/events?after={cursor}
   391	GET /api/runs/{run_id}/nodes/{workflow_node_id}
   392	```
   393	
   394	Server-Sent Events are the leading live-update candidate because this feature
   395	is a one-way read stream and the accepted dashboard target is loopback-only.
   396	Loopback does not waive authentication, authorization, origin checks, or
   397	redaction. SSE is not registered by the current architecture; selecting it
   398	requires the RFC/ADR to register a web transport port/adapter and its security,
   399	reconnect, resource, and shutdown behavior. Snapshot plus authenticated polling
   400	is the compatible first tracer.
   401	
   402	The first response is always a complete snapshot. The snapshot and its cursor
   403	must be read from the same `governed_execution` consistency cell and read
   404	transaction. A subscriber starts strictly after that cursor; the server either
   405	replays every retained delta after it or requires a new snapshot. Each delta
   406	includes:
   407	
   408	- event/cursor ID;
   409	- run ID;
   410	- topology digest;
   411	- expected previous and new projection versions;
   412	- affected stable node/edge IDs; and
   413	- the complete replacement state for those affected records.
   414	
   415	On a cursor gap, version mismatch, topology mismatch, server restart, invalid
   416	payload, or reconnect outside the retention window, the client discards
   417	untrusted deltas and refetches the full snapshot. Slow polling is an acceptable
   418	fallback. Airflow's newline-delimited stream is a viable alternative if the
   419	existing transport layer standardizes on it; WebSocket is unnecessary for the
   420	read-only first slice.
   421	
   422	Status deltas update node data without rerunning layout. Only a changed
   423	topology digest, grouping selection, or orientation may trigger layout.
   424	
   425	## 11. Technology choice
   426	
   427	| Candidate | Fit | Decision |
   428	|---|---|---|
   429	| React Flow + Dagre | Read-only custom nodes, pan/zoom/fit, selection, keyboard/screen-reader affordances, simple directed layout; both MIT | **Recommended first implementation if React is retained** |
   430	| React Flow + ELK | Better compound graphs, ports, cross-hierarchy routing, and complex layout; Airflow proves the combination | Hold as an upgrade path; more configuration, worker/bundle complexity, and EPL-2.0 qualification |
   431	| Native SVG based on Gitea | Maximum control and a close visual precedent | Do not start here; Ranex would inherit viewport, focus, keyboard, ARIA, routing, and performance work |
   432	| Mermaid runtime | Very small static proof of concept | Suitable for this research document, not the live authority-facing UI |
   433	| Import Airflow/Argo/Kestra/Dagu as an engine | Rich existing workflow products | Reject; Ranex already owns different workflow and authority semantics |
   434	
   435	[React Flow's layout guide](https://reactflow.dev/learn/layouting/layouting)
   436	explicitly treats layout as a separate concern and describes Dagre as a simple
   437	choice for directed trees, with ELK for more configurable cases. Its
   438	[accessibility guide](https://reactflow.dev/learn/advanced-use/accessibility)
   439	documents keyboard and screen-reader behavior. Those capabilities reduce work;
   440	they do not make a custom Ranex node accessible automatically.
   441	
   442	Dependency versions must be selected and pinned by the normal
   443	`supplier_governance` adoption process, including license compatibility,
   444	support/maintenance and vulnerability evidence, concentration risk, and an
   445	exit/upgrade plan. The maintained `@dagrejs/dagre` package must not be confused
   446	with legacy Dagre packages. No package is adopted by this research.
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
   526	
   527	### 14.2 Semantic fidelity
   528	
   529	Fixtures cover:
   530	
   531	- linear success;
   532	- deterministic choice with taken, not-taken, and unknown dispositions;
   533	- retry and final attempt;
   534	- evidence `PASS`, `FAIL`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`, and
   535	  `CHECKER_FAULT`;
   536	- human wait;
   537	- run block/unblock;
   538	- cancellation and compensation request;
   539	- effect `OUTCOME_UNKNOWN` followed by reconciliation;
   540	- terminal failure and success; and
   541	- a successful run whose work item remains unchanged.
   542	
   543	Projection replay/query results must agree with the canonical committed rows.
   544	Any unmapped state, missing required reference, or disagreement is visibly
   545	`UNKNOWN` or `CONFLICT`, never green.
   546	
   707	## 19. Source and license register
   708	
   709	All findings above are original Ranex synthesis and paraphrase, including the
   710	review reconciliation. No upstream code is copied into this document.
   711	
   712	| Source | Frozen revision or authoritative page | License / use |
   713	|---|---|---|
   714	| GitHub Actions workflow monitoring | [GitHub Docs](https://docs.github.com/en/actions/how-tos/monitor-workflows?tool=webui), accessed 2026-07-30 | Product behavior/documentation reference |
   715	| GitHub Actions workflow model | [GitHub Docs](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows?learn=getting_started&learnproduct=actions), accessed 2026-07-30 | Product behavior/documentation reference |
   716	| GitLab pipeline graph | [GitLab Docs](https://docs.gitlab.com/ci/pipelines/), accessed 2026-07-30 | Product behavior/documentation reference |
   717	| Gitea workflow graph | [`e80a62f5552cad07bf79b2f31687cf5a9b93f1fc`](https://github.com/go-gitea/gitea/tree/e80a62f5552cad07bf79b2f31687cf5a9b93f1fc) | MIT; code inspection only |
   718	| Apache Airflow graph | [`f781f8b8785496d68c9d9ae725a004764bbc9f1d`](https://github.com/apache/airflow/tree/f781f8b8785496d68c9d9ae725a004764bbc9f1d) | Apache-2.0; code inspection only |
   719	| Argo Workflows graph | [`d98d7b7d73d1b24dd7258153453ea612dbb70092`](https://github.com/argoproj/argo-workflows/tree/d98d7b7d73d1b24dd7258153453ea612dbb70092) | Apache-2.0; code inspection only |
   720	| Kestra topology | [`e03a4f351328f294e67f62be60af0553401fad7a`](https://github.com/kestra-io/kestra/tree/e03a4f351328f294e67f62be60af0553401fad7a) | Apache-2.0; code inspection only |
   721	| Dagster graph layout | [`014641bc1bdb71ea2c7f40371691103bbff5c9c7`](https://github.com/dagster-io/dagster/tree/014641bc1bdb71ea2c7f40371691103bbff5c9c7) | Apache-2.0; code inspection only |
   722	| React Flow / XYFlow | [`360f5b13e2bc6899ea06b4be1a49b068d86926cf`](https://github.com/xyflow/xyflow/tree/360f5b13e2bc6899ea06b4be1a49b068d86926cf) and [official docs](https://reactflow.dev/) | MIT; candidate dependency, not adopted |
   723	| Dagre | [DagreJS repository](https://github.com/dagrejs/dagre), inspected 2026-07-30 | MIT; candidate dependency, not adopted |
   724	| ELK / elkjs | [ELK layered algorithm](https://eclipse.dev/elk/reference/algorithms/org-eclipse-elk-layered.html) and [elkjs](https://github.com/kieler/elkjs) | EPL-2.0; upgrade candidate requiring qualification |
   725	| Dagu graph | [`3fd7eeff69e2df281cd8bd8f47348baf8d3462be`](https://github.com/dagu-org/dagu/tree/3fd7eeff69e2df281cd8bd8f47348baf8d3462be) | GPL-3.0; behavior observation only, no code reuse proposed |
   726	| WCAG 2.2 | [W3C Recommendation](https://www.w3.org/TR/WCAG22/), accessed 2026-07-30 | Proposed accessibility baseline; not yet adopted by Ranex |
   727	
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
     1	# Ranex Personal-Use Source License 1.0
     2	
     3	Copyright (c) 2026 Anthony Garces. All rights reserved.
     4	
     5	This is a source-available license. It is not an open-source license.
     6	
     7	## 1. Scope
     8	
     9	This license applies only to original Ranex code, documentation, configuration,
    10	artwork, and modifications owned by Anthony Garces (the "Ranex Material").
    11	
    12	It does not apply to Hermes Agent material or any other third-party material.
    13	Those portions remain governed by their own licenses. When Hermes Agent
    14	material is adopted in Phase 1, its MIT License is retained in `LICENSE`.
    15	
    16	## 2. Personal-use permission
    17	
    18	Subject to every condition below, an individual may view, copy, run, study, and
    19	privately modify the Ranex Material solely for personal learning,
    20	experimentation, or evaluation.
    21	
    22	This permission is personal, limited, non-exclusive, and non-transferable. All
    23	copyright, license, attribution, and source notices must remain intact.
    24	
    25	## 3. Restrictions
    26	
    27	Except for the limited GitHub-platform rights in section 4, and unless Anthony
    28	Garces gives prior written permission, you may not:
    29	
    30	1. publish, distribute, redistribute, share, sublicense, sell, rent, transfer,
    31	   or otherwise provide the Ranex Material or a modified version to anyone;
    32	2. make the Ranex Material available through a public or shared repository,
    33	   download, package, service, hosted application, network endpoint, or device;
    34	3. use the Ranex Material for any commercial, business, employment,
    35	   professional, institutional, revenue-generating, or client purpose;
    36	4. use the Ranex Material to operate, support, develop, or improve a product,
    37	   service, organization, or business process;
    38	5. remove, hide, or alter a copyright, license, provenance, or attribution
    39	   notice;
    40	6. claim authorship or ownership of Ranex Material created by Anthony Garces,
    41	   or present that material as your own work;
    42	7. use the Ranex name, logo, or branding to imply endorsement, affiliation, or
    43	   ownership; or
    44	8. grant another person rights that this license does not grant to you.
    45	
    46	You may identify original changes that you created privately, but that does not
    47	give you ownership of the underlying Ranex Material or permission to
    48	redistribute the combined work.
    49	
    50	## 4. Public GitHub repository
    51	
    52	While the repository is public, GitHub's Terms of Service grant GitHub users
    53	limited permission to use, display, perform, and reproduce repository content
    54	through GitHub's service as its features allow, including by forking it. This
    55	license does not restrict those platform rights.
    56	
    57	Those platform permissions do not grant permission to redistribute the Ranex
    58	Material outside GitHub's service, use it for business, remove its notices, or
    59	claim it as your own.
    60	
    61	## 5. Ownership and third-party rights
    62	
    63	The Ranex Material is licensed, not sold. Anthony Garces retains all rights
    64	not expressly granted here.
    65	
    66	No term in this license reduces a right granted directly by the MIT License or
    67	another applicable third-party license. When a file contains both upstream
    68	material and original Ranex modifications, each portion remains governed by
    69	its applicable license.
    70	
    71	## 6. Termination
    72	

codex
The run-graph proposal’s authority boundary is well supported, but its transport choice is not special: Airflow currently streams server-computed task summaries as NDJSON and then refreshes, while Kubernetes’ mature list/watch protocol supplies the stronger snapshot-cursor-gap semantics. SSE is therefore an adapter choice, not prior art for correctness.
web search: 
web search: https://www.sqlite.org/copyright.html
web search: 
web search: https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows
web search: 
web search: workflow run topology digest definition hash execution graph ...
web search: 
web search: Netflix Conductor deterministic replay workflow version history official docs ...
context compacted
codex
The evidence is now broad enough to answer the novelty question: none of the four assigned mechanisms lacks prior art. I’m consolidating the distinctions that matter—especially atomicity versus semantic agreement, and exception rollback versus a real crash test—and checking that every adoption recommendation carries a licence disposition.
Repository audit and external verification are complete. Consolidating the evidence into the required mapping, licence shortlist, direct answers, novelty assessment, inferences, and search coverage.
  ✓ Audit the Ranex ADR, tracer implementation/tests, graph proposal, and licence without modifying files
  ✓ Verify deterministic replay and workflow-versioning prior art from primary sources
  ✓ Verify transactional journal/snapshot/outbox and SQLite crash-testing prior art
  ✓ Verify live run-graph state, update transport, licences, and adoption evidence
  → Synthesize the required mapping table and direct conclusions with citations
web search: 
web search: site:github.com/AxonFramework/AxonFramework LICENSE Apache 2.0 ...
The evidence has been consolidated, including actionable deltas, licence compatibility, adoption evidence, and explicit separation of verified facts from inferences.
  ✓ Audit the Ranex ADR, tracer implementation/tests, graph proposal, and licence without modifying files
  ✓ Verify deterministic replay and workflow-versioning prior art from primary sources
  ✓ Verify transactional journal/snapshot/outbox and SQLite crash-testing prior art
  ✓ Verify live run-graph state, update transport, licences, and adoption evidence
  ✓ Synthesize the required mapping table and direct conclusions with citations
codex
The sweep found no genuinely novel mechanism in the four assigned layers. Ranex’s principal gaps are narrower and more concrete:

- Replay currently has no independent oracle.
- The SQLite transaction prevents torn writes but does not prove that journal and snapshot mean the same thing.
- The resilience test exercises a caught SQLite error, not a process or power-loss crash.
- The graph proposal is aligned with production precedent, but its correctness contract matters more than SSE or the renderer.

No repository files were modified.

## Mapping table

| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
|---|---|---|---|---|
| [ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742), [execution.py:226](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226), [replay test:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:59) | The ADR requires canonical events and a pure reducer. `replay_execution()` loops over events using the production reducer. The test manually loops over that same reducer and compares the two results. | Temporal reconstructs workflow state from append-only history and checks emitted commands during replay; SDK replay fails on non-determinism ([architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md), [Python replayer](https://github.com/temporalio/sdk-python)). Cadence replays actual production histories and supports production-history shadowing ([replay and shadowing](https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing)). | ADOPT | Replace the self-oracle with durable history fixtures containing expected command/outbox records. Run the current workflow implementation against those histories and fail at the first command mismatch. Include a mutation test that intentionally changes command order or payload and proves the replay test fails. |
| [execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58), [graph research:250](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:250) | The persisted snapshot carries a `workflow_request_ref`, but not an immutable workflow-definition digest or interpreter version. The graph document proposes such pins; the tracer does not implement them. | Temporal’s `GetVersion` records a marker in history so old and new code paths remain replayable ([Go API](https://github.com/temporalio/sdk-go/blob/main/workflow/workflow.go)). Cadence uses the same marker model ([versioning](https://cadenceworkflow.io/docs/go-client/workflow-versioning)). Airflow DAG bundles record the exact bundle version, including Git commit, used by a run ([DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)). DBOS associates workflows with application versions and supports history patch markers ([versioning tutorial](https://docs.dbos.dev/golang/tutorials/upgrading-workflows)). GitHub reruns at the original commit SHA/ref ([rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)). | ADOPT | Persist immutable workflow-definition, policy, interpreter, and serialization-version identities when a run is created. Recovery must select a compatible worker/definition or fail explicitly; never silently execute an old history using an unmarked new definition. Keep compatibility paths until all affected runs have drained. |
| [execution_store.py:128](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128) | Events have a strict schema version, but no verified upcaster or migration path for old event bytes. | Axon stores event revisions and applies ordered upcasters without rewriting immutable stored events ([event versioning](https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/)). Microsoft’s event-sourcing guidance likewise calls for versioned events/upcasting and sequence tracking ([Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)). | ADOPT | Introduce an explicit revision-to-current upcaster chain and permanent fixtures for every released event revision. Replay tests must begin from original stored bytes, not newly constructed current-version event objects. |
| [migration:1](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1), [execution_store.py:223](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223) | `BEGIN IMMEDIATE` encloses snapshot, journal, and outbox writes. An exception rolls the transaction back. | The transactional-outbox pattern writes business data and an outgoing-message record in the same database transaction ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). DBOS supports placing application data and workflow durability records in the same SQL transaction, including SQLite-backed `sql.DB` use ([DBOS transactions](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)). | ADOPT | Retain the one-database transaction. Treat it as atomicity only, not as replay or semantic-agreement proof. Ensure every state transition is forced through this unit of work and exercise rollback at each write boundary. |
| [migration:3](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3), [execution_store.py:390](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390) | State stores `last_event_id`, version, and canonical JSON. Journal rows store resulting state/digests. Loading validates relational columns against JSON in the same state row, but does not validate the state against the journal head. No constraint makes the referenced event the actual head. | Temporal stores the latest history event ID in mutable state and regards mutable state as valid only when that event is reflected in history; persistence failure forces reload ([History Service consistency](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)). Event-sourced systems make the event stream authoritative and snapshots rebuildable ([Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)); Marten’s inline projections update with events in one ACID transaction ([projection lifecycle](https://martendb.io/tutorials/read-model-projections)). Axon discards incompatible/corrupt snapshots and replays the stream ([snapshotting](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)). | ADAPT | Define one recovery authority—normally the journal. On write and integrity scan, require the snapshot’s event ID/version/digest to equal the exact journal head and its recorded resulting-state digest. Periodically replay original journal bytes and compare the reconstructed state with the snapshot. If verification fails, quarantine or rebuild the snapshot rather than loading it as authoritative. |
| [migration:35](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35) | The outbox is append-only and transactionally tied to the journal, but the scoped tracer has no durable dispatch/acknowledgement lifecycle. | AWS specifies a separate relay, ordered records, possible redelivery, and idempotent consumers ([transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). NServiceBus persists business data and outgoing messages in phase one, then sends and records dispatch completion in phase two; duplicate detection is based on stable message identity ([NServiceBus outbox](https://docs.particular.net/nservicebus/outbox/?version=core_9)). | ADOPT | Add a durable phase-two dispatch record or receipt keyed by the existing stable event/message ID. Test the crash windows before send, after send but before receipt, and after receipt. Consumers must be idempotent because exactly-once external delivery is not supplied by the SQLite transaction. |
| [crash test:31](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31) | A trigger raises `ABORT` before an outbox insert. The same Python process catches the error, rolls back, and checks that old rows remain. | SQLite’s own crash harness has a parent spawn a writer child, kills it at varied points, reopens the database, requires the database to be wholly old or wholly new, runs `PRAGMA integrity_check`, and uses a special VFS to reorder or corrupt unsynced writes ([SQLite testing](https://sqlite.org/testing.html)). | ADOPT | Keep the trigger test as a rollback unit test, but do not call it a crash test. Add an external controller that kills a separate writer process at every state/journal/outbox/commit boundary, reopens from a fresh process, and asserts integrity plus an all-old-or-all-new semantic tuple. Add fault-injecting VFS tests if power-loss durability is claimed. |
| [execution_store.py:183](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183) | Enables foreign keys and `synchronous=FULL`, but does not set or verify `journal_mode`. | SQLite documents the filesystem assumptions behind atomic commit ([atomic commit](https://www.sqlite.org/atomiccommit.html)); `FULL` has different guarantees in rollback-journal and WAL modes, while rollback mode may require `EXTRA` for power-loss durability ([synchronous](https://sqlite.org/pragma.html#pragma_synchronous)). WAL is same-host only, allows one writer, and does not make multi-attached-database transactions atomic as a set ([WAL limitations](https://www.sqlite.org/wal.html)). | ADAPT | Declare and verify a supported SQLite durability profile at startup: journal mode, synchronous mode, filesystem locality, and integrity settings. Run crash certification against exactly that profile. Refuse unsupported network filesystems or document the reduced guarantee. |
| [graph research:206](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:206), [graph research:227](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:227) | Proposes a server-side run projection and says the browser must not reconstruct workflow semantics from raw events. | Argo stores a server-side node map containing each node’s phase/status and retains the resolved workflow specification ([Argo fields](https://argoproj.github.io/argo-workflows/fields/)). Airflow’s graph loads versioned structure and attaches streamed server-produced task-instance summaries by node ID without recalculating layout semantics ([Airflow graph source](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx)). | ADOPT | Implement the proposal’s server ownership literally: server-assigned stable node/edge IDs, topology/version identity, node phase, attempts, and terminal reason. The browser may lay out, filter, and decorate this state, but must not derive execution phase, eligibility, or topology from event order. |
| [graph research:383](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:383) | Proposes GET snapshot plus cursor-bearing SSE, with refetch after a gap. | Kubernetes List/Watch couples a snapshot with `resourceVersion`; watches begin strictly after that version, and `410 Gone` requires relisting ([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)). Airflow 3.2 streams server-computed grid summaries progressively while runs are pending ([release notes](https://airflow.apache.org/docs/apache-airflow/3.2.0/release_notes.html)). | ADAPT | Preserve snapshot-plus-monotonic-cursor, resumability, deduplication, and explicit gap/relist behavior. SSE is a suitable single-host transport, but correctness must be transport-independent so polling or WebSocket clients observe the same versioned projection. |
| [graph research:425](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:425), [licence register:707](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:707) | Proposes React Flow with Dagre, and ELK as a possible upgrade. | React Flow is MIT-licensed and its base library permits commercial use ([repository/licence](https://github.com/xyflow/xyflow)); Dagre is MIT ([licence](https://github.com/dagrejs/dagre/blob/master/LICENSE).) | ADOPT | React Flow and Dagre are compatible with Ranex’s commercial optionality, subject to retaining MIT notices. Keep them as view/layout dependencies only; do not place authoritative execution logic in custom nodes or layout code. |
| [graph research:425](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:425), [licence register:717](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:717) | Names ELK as an upgrade and Dagu as a reference system. | `elkjs` is EPL-2.0 ([licence](https://github.com/kieler/elkjs/blob/master/LICENSE.md)); Dagu is GPL-3.0 ([licence](https://github.com/dagucloud/dagu/blob/main/LICENSE)). | DIVERGE | Do not copy or embed Dagu code in an all-rights-reserved product without a separate commercial licence. Treat ELK as an optional, legal-reviewed dependency because EPL-2.0 carries reciprocal source/notice obligations for the covered program; it should not be the unqualified default. Behavioral study of either system is not restricted. |

## Adopt shortlist

1. **Temporal/Cadence history replay semantics**

   Adopt actual-history replay, command matching, non-determinism failure, and recorded version markers—not either server wholesale. Temporal is MIT ([licence](https://github.com/temporalio/temporal/blob/main/LICENSE)); Cadence is Apache-2.0 ([licence](https://github.com/cadence-workflow/cadence/blob/master/LICENSE)). Both are compatible with Ranex’s commercial optionality when notices and Apache patent terms are observed. Temporal reports more than 1,000 paying cloud customers including NVIDIA, Snap, Alaska Airlines, Retool, and Turo ([adoption evidence](https://temporal.io/news/temporal-surpasses-1-000-active-customers-milestone-in-just-over-a-year)).

2. **SQLite-backed transactional state/journal/outbox**

   Keep the current one-unit-of-work direction, adding explicit head agreement and delivery receipts. SQLite is public domain ([copyright](https://www.sqlite.org/copyright.html)); DBOS’s open-source SDK is MIT ([licence](https://github.com/dbos-inc/dbos-transact-py/blob/main/LICENSE)); the AWS outbox pattern itself is architecture guidance, not licensed library code. DBOS names Walmart, Notion, Roche, Yutori, and Bristol Myers Squibb as users/customers ([customer stories](https://www.dbos.dev/customer-stories)).

3. **SQLite’s real crash-test model**

   Adopt the parent/child crash loop, all-old-or-all-new oracle, integrity checks, and—where the guarantee warrants it—fault-injecting VFS. SQLite’s public-domain status is fully compatible. This is much stronger evidence than an application exception test.

4. **Argo/Airflow server-owned graph projection plus Kubernetes cursor semantics**

   Adopt the behavioral contracts, not necessarily their implementations. Argo, Airflow, and Kubernetes are Apache-2.0 and commercially compatible with notice/patent compliance ([Argo licence](https://github.com/argoproj/argo-workflows/blob/main/LICENSE), [Airflow licence](https://github.com/apache/airflow/blob/main/LICENSE), [Kubernetes licence](https://github.com/kubernetes/kubernetes)). Argo is CNCF graduated with reported production use by Adobe, BlackRock, Capital One, Google, Intuit, and Tesla ([CNCF evidence](https://www.cncf.io/announcements/2022/12/06/the-cloud-native-computing-foundation-announces-argo-has-graduated/)). Apache reported Airflow use across more than 200 organizations including Adobe, Airbnb, Etsy, Google, Lyft, PayPal, Reddit, and Twitter ([ASF evidence](https://news.apache.org/foundation/entry/the-apache-software-foundation-announces44)).

5. **React Flow plus Dagre**

   Both are MIT and compatible with the Ranex licence if notices are preserved. They are suitable view dependencies because their output need not be authoritative.

6. **Axon-style event revisions and upcasters**

   Adopt the revision/upcaster behavior and fixtures. Axon Framework is Apache-2.0 ([repository/licence](https://github.com/AxonIQ/AxonFramework)), compatible with future commercial use subject to normal Apache obligations.

Licence caveats:

- **Restate:** useful corroboration because it explicitly reports an exact journal mismatch during replay and pins invocations to deployments ([errors](https://docs.restate.dev/references/errors), [versioning](https://docs.restate.dev/services/versioning)), but its server is BSL 1.1 with service-use restrictions before conversion to Apache-2.0 ([licence](https://github.com/restatedev/restate/blob/main/LICENSE)). Study the protocol; do not embed it without commercial/legal review.
- **Dagu:** GPL-3.0; unsuitable for code incorporation into the present proprietary product without separate terms.
- **ELK:** EPL-2.0; potentially usable, but reciprocal obligations need legal review.
- **NServiceBus:** cited for its protocol, not recommended as a code dependency; it is a commercial product.
- This is an engineering compatibility assessment, not legal advice.

## Answers to the three direct questions

### 1. How do production systems make a snapshot and a journal provably agree?

They use four complementary controls:

1. **The event stream is the recovery authority.** A snapshot is a cache or materialized projection that can be discarded and rebuilt, not a second independent truth ([Microsoft Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing), [Axon snapshots](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)).

2. **The snapshot identifies the precise journal position it represents.** Temporal stores the latest history event ID in mutable state and considers that state valid only when the event is reflected in history ([Temporal History Service](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)).

3. **Events and synchronous projections are committed atomically.** Marten calls this an inline projection and updates it in the same ACID transaction as the events ([Marten projections](https://martendb.io/tutorials/read-model-projections)).

4. **They verify or rebuild.** Replay from original event bytes must reproduce the snapshot, and a corrupt or incompatible snapshot falls back to full stream replay.

Ranex currently has only item 3. One transaction proves that all three writes committed or none did; it does **not** prove that the snapshot was computed from the journal event it names. A shared implementation bug can atomically commit mutually inconsistent data.

Hashes help detect byte disagreement, but they cannot prove that the reducer or command semantics were correct.

### 2. What is the accepted way to test crash recovery, concretely?

SQLite’s own method is the credible baseline:

1. A parent process creates a known durable starting database.
2. A separate child performs the transition.
3. The parent kills the child at systematically varied write/commit points.
4. A fresh process reopens the real database file.
5. It runs `PRAGMA integrity_check` and relevant foreign-key checks.
6. It accepts only the complete old state or complete new state—never a mixture.
7. It repeats across crash points and compound failures.
8. For power-loss claims, a test VFS models lost, reordered, or corrupted unsynced writes.

That procedure is documented by SQLite itself ([testing methodology](https://sqlite.org/testing.html)). Ranex’s trigger-induced `ABORT` is a useful rollback test, but no process dies, the application catches the exception, and the filesystem is never exposed to an interrupted commit.

For Ranex, the semantic oracle must check the tuple together: state head, journal head, outbox intent/receipt, reconstructed reducer state, and stable message identities. Retrying after an ambiguous send must also demonstrate idempotency.

### 3. Is one-SQLite-unit-of-work recognized, or unusual?

It is a recognized local-authority form of the transactional-outbox/event-store pattern, not an unusual invention. DBOS explicitly supports colocating application changes with durable workflow records in one SQL transaction, including SQLite use ([DBOS transaction tutorial](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)); AWS documents the general same-database outbox pattern ([AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)).

Its limits are well known:

- SQLite serializes writers; WAL still has only one writer at a time.
- WAL is intended for processes on the same host, not a network filesystem.
- A transaction spanning multiple attached databases is not atomic as a set in WAL mode.
- Durability depends on journal mode, synchronous settings, filesystem behavior, and hardware assumptions.
- External effects cannot join the SQLite transaction. The outbox gives atomic intent plus at-least-once relay, requiring idempotent consumers.

These limits are documented by SQLite’s [WAL](https://www.sqlite.org/wal.html), [synchronous pragma](https://sqlite.org/pragma.html#pragma_synchronous), and [atomic-commit assumptions](https://www.sqlite.org/atomiccommit.html).

## Genuinely novel

No row in the assigned layers merits **NOVEL**.

The exact composition—single-host SQLite authority, AI-agent governance constraints, policy identities, deterministic replay, and a server-owned graph—may be Ranex-specific as a product package. Its constituent correctness mechanisms are established:

- history replay and non-determinism detection;
- workflow-definition/version pinning;
- event revisions and upcasters;
- event-sourced snapshots;
- transactional outbox;
- SQLite crash certification;
- server-owned graph projections;
- snapshot-plus-cursor live-update protocols.

The Ranex-specific governance vocabulary and policy semantics may contain original product work, but that falls outside proof that these execution, storage, recovery, or visualization mechanisms lack prior art.

## Inferences

- **INFERENCE:** The normal store path probably writes a mutually consistent snapshot and journal because one reducer invocation produces both. A reducer bug, serialization bug, migration, or direct database write can nevertheless commit disagreement because no persisted cross-check rejects it.
- **INFERENCE:** The active database’s journal mode is `UNVERIFIED`. The connection code does not set it; SQLite’s default is normally rollback journal, but journal mode is persistent and could have been changed externally.
- **INFERENCE:** The scoped tracer demonstrates outbox persistence, not a complete relay protocol. No durable publisher/receipt implementation was found in the requested tracer paths.
- **INFERENCE:** The graph document is a proposal, not evidence of a functioning server projection or cursor protocol.
- **INFERENCE:** SSE is operationally appropriate for a single-host, server-to-browser feed, but it is not what makes the feed correct. The version/cursor/relist contract does.

## Search coverage

Verified from primary documentation or source:

- Temporal, Cadence, DBOS, Restate and Azure Durable workflow versioning/replay.
- Airflow DAG bundles, GitHub Actions commit pinning, and Kestra flow revisions.
- Axon event upcasting/snapshots, Marten inline projections, Microsoft event sourcing.
- AWS transactional outbox, NServiceBus outbox protocol, and Debezium outbox routing.
- SQLite atomic commit, WAL, synchronous modes, public-domain status, and crash-test methodology.
- Argo server-side workflow nodes and resolved specs.
- Airflow graph source and progressive server summaries.
- Kubernetes List/Watch snapshot/cursor/gap semantics.
- React Flow, Dagre, ELK, Dagu, and all recommended-project licences.
- Named adoption evidence for Temporal, DBOS, Argo, and Airflow.

Searched but not used as dispositive evidence:

- **Netflix/OSS Conductor:** current materials claim replay/rerun capabilities, but I did not verify a primary contract equivalent to Temporal’s “re-execute history and compare emitted commands.” The original Netflix repository is also archived. Deterministic replay equivalence is therefore **UNVERIFIED** for this report.
- **Dagster:** snapshot/reexecution material was found, but it did not add a stronger result than the verified Temporal/Airflow/Argo evidence.
- **Kestra:** flow revisions are verified ([revision documentation](https://kestra.io/docs/concepts/revision)), but no stronger command-by-command deterministic replay guarantee was verified.
- **Debezium:** its CDC outbox router is production prior art ([documentation](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)), but it is not a natural fit for a single-process SQLite authority and therefore is not recommended.
tokens used
536,707
The sweep found no genuinely novel mechanism in the four assigned layers. Ranex’s principal gaps are narrower and more concrete:

- Replay currently has no independent oracle.
- The SQLite transaction prevents torn writes but does not prove that journal and snapshot mean the same thing.
- The resilience test exercises a caught SQLite error, not a process or power-loss crash.
- The graph proposal is aligned with production precedent, but its correctness contract matters more than SSE or the renderer.

No repository files were modified.

## Mapping table

| Ranex element (`path:line`) | What Ranex does now | Prior art (name + URL) | Verdict | Specific delta |
|---|---|---|---|---|
| [ADR-0013:742](/home/soultransit/devtony/ranex/docs/architecture/decisions/ADR-0013-promote-hermes-research-obligations.md:742), [execution.py:226](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/domain/execution.py:226), [replay test:59](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/replay/governed_execution/test_execution_replay.py:59) | The ADR requires canonical events and a pure reducer. `replay_execution()` loops over events using the production reducer. The test manually loops over that same reducer and compares the two results. | Temporal reconstructs workflow state from append-only history and checks emitted commands during replay; SDK replay fails on non-determinism ([architecture](https://github.com/temporalio/temporal/blob/main/docs/architecture/README.md), [Python replayer](https://github.com/temporalio/sdk-python)). Cadence replays actual production histories and supports production-history shadowing ([replay and shadowing](https://cadenceworkflow.io/docs/go-client/workflow-replay-shadowing)). | ADOPT | Replace the self-oracle with durable history fixtures containing expected command/outbox records. Run the current workflow implementation against those histories and fail at the first command mismatch. Include a mutation test that intentionally changes command order or payload and proves the replay test fails. |
| [execution_store.py:58](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:58), [graph research:250](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:250) | The persisted snapshot carries a `workflow_request_ref`, but not an immutable workflow-definition digest or interpreter version. The graph document proposes such pins; the tracer does not implement them. | Temporal’s `GetVersion` records a marker in history so old and new code paths remain replayable ([Go API](https://github.com/temporalio/sdk-go/blob/main/workflow/workflow.go)). Cadence uses the same marker model ([versioning](https://cadenceworkflow.io/docs/go-client/workflow-versioning)). Airflow DAG bundles record the exact bundle version, including Git commit, used by a run ([DAG bundles](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/dag-bundles.html)). DBOS associates workflows with application versions and supports history patch markers ([versioning tutorial](https://docs.dbos.dev/golang/tutorials/upgrading-workflows)). GitHub reruns at the original commit SHA/ref ([rerun semantics](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/re-run-workflows-and-jobs)). | ADOPT | Persist immutable workflow-definition, policy, interpreter, and serialization-version identities when a run is created. Recovery must select a compatible worker/definition or fail explicitly; never silently execute an old history using an unmarked new definition. Keep compatibility paths until all affected runs have drained. |
| [execution_store.py:128](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:128) | Events have a strict schema version, but no verified upcaster or migration path for old event bytes. | Axon stores event revisions and applies ordered upcasters without rewriting immutable stored events ([event versioning](https://docs.axoniq.io/axon-framework-reference/4.13/events/event-versioning/)). Microsoft’s event-sourcing guidance likewise calls for versioned events/upcasting and sequence tracking ([Event Sourcing pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)). | ADOPT | Introduce an explicit revision-to-current upcaster chain and permanent fixtures for every released event revision. Replay tests must begin from original stored bytes, not newly constructed current-version event objects. |
| [migration:1](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:1), [execution_store.py:223](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:223) | `BEGIN IMMEDIATE` encloses snapshot, journal, and outbox writes. An exception rolls the transaction back. | The transactional-outbox pattern writes business data and an outgoing-message record in the same database transaction ([AWS guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). DBOS supports placing application data and workflow durability records in the same SQL transaction, including SQLite-backed `sql.DB` use ([DBOS transactions](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)). | ADOPT | Retain the one-database transaction. Treat it as atomicity only, not as replay or semantic-agreement proof. Ensure every state transition is forced through this unit of work and exercise rollback at each write boundary. |
| [migration:3](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:3), [execution_store.py:390](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:390) | State stores `last_event_id`, version, and canonical JSON. Journal rows store resulting state/digests. Loading validates relational columns against JSON in the same state row, but does not validate the state against the journal head. No constraint makes the referenced event the actual head. | Temporal stores the latest history event ID in mutable state and regards mutable state as valid only when that event is reflected in history; persistence failure forces reload ([History Service consistency](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)). Event-sourced systems make the event stream authoritative and snapshots rebuildable ([Microsoft](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)); Marten’s inline projections update with events in one ACID transaction ([projection lifecycle](https://martendb.io/tutorials/read-model-projections)). Axon discards incompatible/corrupt snapshots and replays the stream ([snapshotting](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)). | ADAPT | Define one recovery authority—normally the journal. On write and integrity scan, require the snapshot’s event ID/version/digest to equal the exact journal head and its recorded resulting-state digest. Periodically replay original journal bytes and compare the reconstructed state with the snapshot. If verification fails, quarantine or rebuild the snapshot rather than loading it as authoritative. |
| [migration:35](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/migrations/001_execution_kernel.sql:35) | The outbox is append-only and transactionally tied to the journal, but the scoped tracer has no durable dispatch/acknowledgement lifecycle. | AWS specifies a separate relay, ordered records, possible redelivery, and idempotent consumers ([transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)). NServiceBus persists business data and outgoing messages in phase one, then sends and records dispatch completion in phase two; duplicate detection is based on stable message identity ([NServiceBus outbox](https://docs.particular.net/nservicebus/outbox/?version=core_9)). | ADOPT | Add a durable phase-two dispatch record or receipt keyed by the existing stable event/message ID. Test the crash windows before send, after send but before receipt, and after receipt. Consumers must be idempotent because exactly-once external delivery is not supplied by the SQLite transaction. |
| [crash test:31](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/tests/resilience/test_execution_sqlite_crash_boundary.py:31) | A trigger raises `ABORT` before an outbox insert. The same Python process catches the error, rolls back, and checks that old rows remain. | SQLite’s own crash harness has a parent spawn a writer child, kills it at varied points, reopens the database, requires the database to be wholly old or wholly new, runs `PRAGMA integrity_check`, and uses a special VFS to reorder or corrupt unsynced writes ([SQLite testing](https://sqlite.org/testing.html)). | ADOPT | Keep the trigger test as a rollback unit test, but do not call it a crash test. Add an external controller that kills a separate writer process at every state/journal/outbox/commit boundary, reopens from a fresh process, and asserts integrity plus an all-old-or-all-new semantic tuple. Add fault-injecting VFS tests if power-loss durability is claimed. |
| [execution_store.py:183](/home/soultransit/devtony/ranex/.claude/worktrees/kernel-tracer/src/ranex/governed_execution/adapters/persistence/sqlite/execution_store.py:183) | Enables foreign keys and `synchronous=FULL`, but does not set or verify `journal_mode`. | SQLite documents the filesystem assumptions behind atomic commit ([atomic commit](https://www.sqlite.org/atomiccommit.html)); `FULL` has different guarantees in rollback-journal and WAL modes, while rollback mode may require `EXTRA` for power-loss durability ([synchronous](https://sqlite.org/pragma.html#pragma_synchronous)). WAL is same-host only, allows one writer, and does not make multi-attached-database transactions atomic as a set ([WAL limitations](https://www.sqlite.org/wal.html)). | ADAPT | Declare and verify a supported SQLite durability profile at startup: journal mode, synchronous mode, filesystem locality, and integrity settings. Run crash certification against exactly that profile. Refuse unsupported network filesystems or document the reduced guarantee. |
| [graph research:206](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:206), [graph research:227](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:227) | Proposes a server-side run projection and says the browser must not reconstruct workflow semantics from raw events. | Argo stores a server-side node map containing each node’s phase/status and retains the resolved workflow specification ([Argo fields](https://argoproj.github.io/argo-workflows/fields/)). Airflow’s graph loads versioned structure and attaches streamed server-produced task-instance summaries by node ID without recalculating layout semantics ([Airflow graph source](https://github.com/apache/airflow/blob/f781f8b8785496d68c9d9ae725a004764bbc9f1d/airflow-core/src/airflow/ui/src/layouts/Details/Graph/Graph.tsx)). | ADOPT | Implement the proposal’s server ownership literally: server-assigned stable node/edge IDs, topology/version identity, node phase, attempts, and terminal reason. The browser may lay out, filter, and decorate this state, but must not derive execution phase, eligibility, or topology from event order. |
| [graph research:383](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:383) | Proposes GET snapshot plus cursor-bearing SSE, with refetch after a gap. | Kubernetes List/Watch couples a snapshot with `resourceVersion`; watches begin strictly after that version, and `410 Gone` requires relisting ([API concepts](https://kubernetes.io/docs/reference/using-api/api-concepts/)). Airflow 3.2 streams server-computed grid summaries progressively while runs are pending ([release notes](https://airflow.apache.org/docs/apache-airflow/3.2.0/release_notes.html)). | ADAPT | Preserve snapshot-plus-monotonic-cursor, resumability, deduplication, and explicit gap/relist behavior. SSE is a suitable single-host transport, but correctness must be transport-independent so polling or WebSocket clients observe the same versioned projection. |
| [graph research:425](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:425), [licence register:707](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:707) | Proposes React Flow with Dagre, and ELK as a possible upgrade. | React Flow is MIT-licensed and its base library permits commercial use ([repository/licence](https://github.com/xyflow/xyflow)); Dagre is MIT ([licence](https://github.com/dagrejs/dagre/blob/master/LICENSE).) | ADOPT | React Flow and Dagre are compatible with Ranex’s commercial optionality, subject to retaining MIT notices. Keep them as view/layout dependencies only; do not place authoritative execution logic in custom nodes or layout code. |
| [graph research:425](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:425), [licence register:717](/home/soultransit/devtony/ranex/docs/research/deterministic-run-graph-visualization-research-2026-07-30.md:717) | Names ELK as an upgrade and Dagu as a reference system. | `elkjs` is EPL-2.0 ([licence](https://github.com/kieler/elkjs/blob/master/LICENSE.md)); Dagu is GPL-3.0 ([licence](https://github.com/dagucloud/dagu/blob/main/LICENSE)). | DIVERGE | Do not copy or embed Dagu code in an all-rights-reserved product without a separate commercial licence. Treat ELK as an optional, legal-reviewed dependency because EPL-2.0 carries reciprocal source/notice obligations for the covered program; it should not be the unqualified default. Behavioral study of either system is not restricted. |

## Adopt shortlist

1. **Temporal/Cadence history replay semantics**

   Adopt actual-history replay, command matching, non-determinism failure, and recorded version markers—not either server wholesale. Temporal is MIT ([licence](https://github.com/temporalio/temporal/blob/main/LICENSE)); Cadence is Apache-2.0 ([licence](https://github.com/cadence-workflow/cadence/blob/master/LICENSE)). Both are compatible with Ranex’s commercial optionality when notices and Apache patent terms are observed. Temporal reports more than 1,000 paying cloud customers including NVIDIA, Snap, Alaska Airlines, Retool, and Turo ([adoption evidence](https://temporal.io/news/temporal-surpasses-1-000-active-customers-milestone-in-just-over-a-year)).

2. **SQLite-backed transactional state/journal/outbox**

   Keep the current one-unit-of-work direction, adding explicit head agreement and delivery receipts. SQLite is public domain ([copyright](https://www.sqlite.org/copyright.html)); DBOS’s open-source SDK is MIT ([licence](https://github.com/dbos-inc/dbos-transact-py/blob/main/LICENSE)); the AWS outbox pattern itself is architecture guidance, not licensed library code. DBOS names Walmart, Notion, Roche, Yutori, and Bristol Myers Squibb as users/customers ([customer stories](https://www.dbos.dev/customer-stories)).

3. **SQLite’s real crash-test model**

   Adopt the parent/child crash loop, all-old-or-all-new oracle, integrity checks, and—where the guarantee warrants it—fault-injecting VFS. SQLite’s public-domain status is fully compatible. This is much stronger evidence than an application exception test.

4. **Argo/Airflow server-owned graph projection plus Kubernetes cursor semantics**

   Adopt the behavioral contracts, not necessarily their implementations. Argo, Airflow, and Kubernetes are Apache-2.0 and commercially compatible with notice/patent compliance ([Argo licence](https://github.com/argoproj/argo-workflows/blob/main/LICENSE), [Airflow licence](https://github.com/apache/airflow/blob/main/LICENSE), [Kubernetes licence](https://github.com/kubernetes/kubernetes)). Argo is CNCF graduated with reported production use by Adobe, BlackRock, Capital One, Google, Intuit, and Tesla ([CNCF evidence](https://www.cncf.io/announcements/2022/12/06/the-cloud-native-computing-foundation-announces-argo-has-graduated/)). Apache reported Airflow use across more than 200 organizations including Adobe, Airbnb, Etsy, Google, Lyft, PayPal, Reddit, and Twitter ([ASF evidence](https://news.apache.org/foundation/entry/the-apache-software-foundation-announces44)).

5. **React Flow plus Dagre**

   Both are MIT and compatible with the Ranex licence if notices are preserved. They are suitable view dependencies because their output need not be authoritative.

6. **Axon-style event revisions and upcasters**

   Adopt the revision/upcaster behavior and fixtures. Axon Framework is Apache-2.0 ([repository/licence](https://github.com/AxonIQ/AxonFramework)), compatible with future commercial use subject to normal Apache obligations.

Licence caveats:

- **Restate:** useful corroboration because it explicitly reports an exact journal mismatch during replay and pins invocations to deployments ([errors](https://docs.restate.dev/references/errors), [versioning](https://docs.restate.dev/services/versioning)), but its server is BSL 1.1 with service-use restrictions before conversion to Apache-2.0 ([licence](https://github.com/restatedev/restate/blob/main/LICENSE)). Study the protocol; do not embed it without commercial/legal review.
- **Dagu:** GPL-3.0; unsuitable for code incorporation into the present proprietary product without separate terms.
- **ELK:** EPL-2.0; potentially usable, but reciprocal obligations need legal review.
- **NServiceBus:** cited for its protocol, not recommended as a code dependency; it is a commercial product.
- This is an engineering compatibility assessment, not legal advice.

## Answers to the three direct questions

### 1. How do production systems make a snapshot and a journal provably agree?

They use four complementary controls:

1. **The event stream is the recovery authority.** A snapshot is a cache or materialized projection that can be discarded and rebuilt, not a second independent truth ([Microsoft Event Sourcing](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing), [Axon snapshots](https://docs.axoniq.io/axon-framework-reference/development/tuning/snapshotting/)).

2. **The snapshot identifies the precise journal position it represents.** Temporal stores the latest history event ID in mutable state and considers that state valid only when the event is reflected in history ([Temporal History Service](https://github.com/temporalio/temporal/blob/main/docs/architecture/history-service.md)).

3. **Events and synchronous projections are committed atomically.** Marten calls this an inline projection and updates it in the same ACID transaction as the events ([Marten projections](https://martendb.io/tutorials/read-model-projections)).

4. **They verify or rebuild.** Replay from original event bytes must reproduce the snapshot, and a corrupt or incompatible snapshot falls back to full stream replay.

Ranex currently has only item 3. One transaction proves that all three writes committed or none did; it does **not** prove that the snapshot was computed from the journal event it names. A shared implementation bug can atomically commit mutually inconsistent data.

Hashes help detect byte disagreement, but they cannot prove that the reducer or command semantics were correct.

### 2. What is the accepted way to test crash recovery, concretely?

SQLite’s own method is the credible baseline:

1. A parent process creates a known durable starting database.
2. A separate child performs the transition.
3. The parent kills the child at systematically varied write/commit points.
4. A fresh process reopens the real database file.
5. It runs `PRAGMA integrity_check` and relevant foreign-key checks.
6. It accepts only the complete old state or complete new state—never a mixture.
7. It repeats across crash points and compound failures.
8. For power-loss claims, a test VFS models lost, reordered, or corrupted unsynced writes.

That procedure is documented by SQLite itself ([testing methodology](https://sqlite.org/testing.html)). Ranex’s trigger-induced `ABORT` is a useful rollback test, but no process dies, the application catches the exception, and the filesystem is never exposed to an interrupted commit.

For Ranex, the semantic oracle must check the tuple together: state head, journal head, outbox intent/receipt, reconstructed reducer state, and stable message identities. Retrying after an ambiguous send must also demonstrate idempotency.

### 3. Is one-SQLite-unit-of-work recognized, or unusual?

It is a recognized local-authority form of the transactional-outbox/event-store pattern, not an unusual invention. DBOS explicitly supports colocating application changes with durable workflow records in one SQL transaction, including SQLite use ([DBOS transaction tutorial](https://docs.dbos.dev/golang/tutorials/transaction-tutorial)); AWS documents the general same-database outbox pattern ([AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)).

Its limits are well known:

- SQLite serializes writers; WAL still has only one writer at a time.
- WAL is intended for processes on the same host, not a network filesystem.
- A transaction spanning multiple attached databases is not atomic as a set in WAL mode.
- Durability depends on journal mode, synchronous settings, filesystem behavior, and hardware assumptions.
- External effects cannot join the SQLite transaction. The outbox gives atomic intent plus at-least-once relay, requiring idempotent consumers.

These limits are documented by SQLite’s [WAL](https://www.sqlite.org/wal.html), [synchronous pragma](https://sqlite.org/pragma.html#pragma_synchronous), and [atomic-commit assumptions](https://www.sqlite.org/atomiccommit.html).

## Genuinely novel

No row in the assigned layers merits **NOVEL**.

The exact composition—single-host SQLite authority, AI-agent governance constraints, policy identities, deterministic replay, and a server-owned graph—may be Ranex-specific as a product package. Its constituent correctness mechanisms are established:

- history replay and non-determinism detection;
- workflow-definition/version pinning;
- event revisions and upcasters;
- event-sourced snapshots;
- transactional outbox;
- SQLite crash certification;
- server-owned graph projections;
- snapshot-plus-cursor live-update protocols.

The Ranex-specific governance vocabulary and policy semantics may contain original product work, but that falls outside proof that these execution, storage, recovery, or visualization mechanisms lack prior art.

## Inferences

- **INFERENCE:** The normal store path probably writes a mutually consistent snapshot and journal because one reducer invocation produces both. A reducer bug, serialization bug, migration, or direct database write can nevertheless commit disagreement because no persisted cross-check rejects it.
- **INFERENCE:** The active database’s journal mode is `UNVERIFIED`. The connection code does not set it; SQLite’s default is normally rollback journal, but journal mode is persistent and could have been changed externally.
- **INFERENCE:** The scoped tracer demonstrates outbox persistence, not a complete relay protocol. No durable publisher/receipt implementation was found in the requested tracer paths.
- **INFERENCE:** The graph document is a proposal, not evidence of a functioning server projection or cursor protocol.
- **INFERENCE:** SSE is operationally appropriate for a single-host, server-to-browser feed, but it is not what makes the feed correct. The version/cursor/relist contract does.

## Search coverage

Verified from primary documentation or source:

- Temporal, Cadence, DBOS, Restate and Azure Durable workflow versioning/replay.
- Airflow DAG bundles, GitHub Actions commit pinning, and Kestra flow revisions.
- Axon event upcasting/snapshots, Marten inline projections, Microsoft event sourcing.
- AWS transactional outbox, NServiceBus outbox protocol, and Debezium outbox routing.
- SQLite atomic commit, WAL, synchronous modes, public-domain status, and crash-test methodology.
- Argo server-side workflow nodes and resolved specs.
- Airflow graph source and progressive server summaries.
- Kubernetes List/Watch snapshot/cursor/gap semantics.
- React Flow, Dagre, ELK, Dagu, and all recommended-project licences.
- Named adoption evidence for Temporal, DBOS, Argo, and Airflow.

Searched but not used as dispositive evidence:

- **Netflix/OSS Conductor:** current materials claim replay/rerun capabilities, but I did not verify a primary contract equivalent to Temporal’s “re-execute history and compare emitted commands.” The original Netflix repository is also archived. Deterministic replay equivalence is therefore **UNVERIFIED** for this report.
- **Dagster:** snapshot/reexecution material was found, but it did not add a stronger result than the verified Temporal/Airflow/Argo evidence.
- **Kestra:** flow revisions are verified ([revision documentation](https://kestra.io/docs/concepts/revision)), but no stronger command-by-command deterministic replay guarantee was verified.
- **Debezium:** its CDC outbox router is production prior art ([documentation](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)), but it is not a natural fit for a single-process SQLite authority and therefore is not recommended.
