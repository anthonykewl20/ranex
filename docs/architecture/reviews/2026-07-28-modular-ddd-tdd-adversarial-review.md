# Modular-DDD and TDD adversarial architecture review

| Field | Final value |
|---|---|
| Review ID | `RANEX-DDD-TDD-ADVERSARIAL-2026-07-28-001-FINAL` |
| Date | 2026-07-28 |
| Reviewer lane | Independent book-alignment / DDD / TDD adversarial lane |
| Subject | Architecture design and executable documentation-contract baseline in the unsealed working tree based on `4baad4a67843b02d5970f442fb54aed8d6525dda` |
| Decisions reviewed | `ADR-0007`, `ADR-0008`, and `ADR-0009`, reconciled with HERMES, architecture README, SOURCE OF TRUTH, and the engineering-reference practice registry |
| Frozen generated-tree digest | `843b342db9863a6f7f97e1868ac47d04e36aa45c1db050488c6648f8d1a7b900` |
| Executable validation scope | `EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY` |
| Former findings | 4 P0 and 5 P1, all `VERIFIED_CLOSED` |
| Open material design/book-alignment findings | **0** |
| Verdict | **PASS — READY FOR STAGED BUILD AT THE ARCHITECTURE-DESIGN/CONTRACT SCOPE** |

## Final verdict

The reviewed architecture is ready to enter a staged, production-shaped
implementation. No additional book research or architecture-document expansion
is a blocking prerequisite for beginning that build. The design applies the
registered engineering references without ceremonial DDD folder creation,
coverage-score substitution, hidden dependency inference, or test-only
production paths. The executable documentation-contract validation is `PASS`.

This is a scoped pass, not an unrestricted production-readiness claim:

- the selected DDD, modular-monolith, Clean Architecture, TDD, testing,
  evolutionary-fitness, and coupling practices are mature and proven ways of
  working;
- their Ranex-specific enactment, the fitness of the proposed 34 boundaries,
  and the system's runtime behavior are not yet empirically proven;
- all source, runtime, production-test, operational, security, recovery, and
  outcome claims remain separately evidence-gated; and
- `AI-G2` is not passed by this review. The contract baseline alone cannot pass
  that gate.

The correct build authorization is therefore: start with one narrow
production-shaped tracer under the established SDLC; generate runtime evidence
from the real source, artifact, composition, adapters, migrations, and test
lanes; then expand only while the noncompensating gates remain satisfied.

## Supersession

This final review supersedes the earlier checkpoint version of this same review.
Every former P0/P1 item was re-inspected against the frozen generated tree,
current generator, current validator, schemas, semantic/negative fixtures, and
the final validation report. None remains open.

## Former finding closure matrix

| Former finding | Final status | Exact closure evidence |
|---|---|---|
| `DDDTDD-P0-001` — incomplete path ownership and test-mirror semantics | `VERIFIED_CLOSED` | ADR-0007 defines the complete ownership contract at `docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md:206-218`. The strict path-record schema is generated at `scripts/architecture/generate_contracts.py:2225-2325`; enrichment resolves governance versus semantic ownership, accountable/reviewer roles, data/dependency/rule/lifecycle facts, and exception metadata at `2741-2849`. `validate_path_contract_semantics` enforces parameterized leaf ownership for broad test roots and complete owner facts at `scripts/architecture/validate_contracts.py:254-295`. The blanket-test-owner adversarial fixture is generated at `scripts/architecture/generate_contracts.py:4500-4512`. Final validation schema-checks all `232/232` path rows, including 18 governed test roots. |
| `DDDTDD-P0-002` — no declared dependency graph or exact host-edge exception proof | `VERIFIED_CLOSED` | ADR-0009 makes actual imports a public-API-only subset of an explicit deny-by-default graph at `docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:20-24,61-67,84-160`. `architecture/contracts/context-dependency-edges.json` contains 67 unique declared edges. ADR-0007 defines exact, owned, expiring, non-transitive exceptions at `docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md:267-283`. The exception schema is generated at `scripts/architecture/generate_contracts.py:2675-2738`; wildcard and expiry semantics are enforced at `scripts/architecture/validate_contracts.py:298-317`. Production topology validates `actual_pairs <= declared_pairs` at `scripts/architecture/validate_contracts.py:1465-1572`. Private-import, undeclared-public-import, broad-host-edge, and cyclic-import negatives are generated at `scripts/architecture/generate_contracts.py:4529-4575` and validated in the 25-fixture negative corpus. |
| `DDDTDD-P0-003` — task aggregate could forge PASS without exact-subject production evidence | `VERIFIED_CLOSED` | ADR-0008 requires exact handoff subjects, one built artifact, production paths, real seams, and nonpromotion of synthetic evidence at `docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:36-75`. Six typed production-evidence obligations begin at `scripts/architecture/generate_contracts.py:469-505`; the task profile schema and definition baseline project them at `1692-1819` and `2886-3038`. `validate_test_profile_semantics` requires task subject ref/digest at `scripts/architecture/validate_contracts.py:600-616`, derives applicable category/failure/edge/production rows, and requires exact-subject current PASS bindings before sealing at `900-1067`. Forged missing-evidence, unbound-evidence, and missing-subject PASS fixtures are generated at `scripts/architecture/generate_contracts.py:4317-4390,4488-4498` and are rejected. |
| `DDDTDD-P0-004` — individual rule assessments not materialized | `VERIFIED_CLOSED` | `scripts/architecture/generate_contracts.py:3041-3178` creates the exact 47-row registry: 18 ADR-0007 rules, 19 ADR-0008 rules, and 10 ADR-0009 rules. `scripts/architecture/validate_contracts.py:2305-2394` validates exact set equality, definition and subject digests, per-row semantics, no numeric scores, and the derived noncompensating summary. `architecture/contracts/architecture-rule-assessments.json` has exactly 47 rows; all 47 honestly remain `NOT_ASSESSED`, with `numeric_score: null`, `outcome: null`, and `pass_authority: false`. |
| `DDDTDD-P1-001` — generic test mirroring would create cargo-cult suites and force transitions | `VERIFIED_CLOSED` | ADR-0007 prohibits empty optional folders at `docs/architecture/decisions/ADR-0007-establish-modular-ddd-repository-organization.md:28-31,84-87`; ADR-0008 defines lane-specific roots at `docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:123-152`. `TEST_LANE_SHAPES` is lane-specific at `scripts/architecture/generate_contracts.py:290-467`, and the profile projects `LANE_SPECIFIC_SUBJECT_SHAPES` at `2930-2932`. The validator checks the exact shape projection at `scripts/architecture/validate_contracts.py:660-684` and applicability-aware edge/transition semantics at `816-992`. The supported stateless N/A fixture and forced-transition negative are generated at `scripts/architecture/generate_contracts.py:4214-4315`. An allowed root is therefore a governed option, not a requirement to instantiate every lane. |
| `DDDTDD-P1-002` — fixtures, quarantine, and obsolete deletion lacked typed instance contracts | `VERIFIED_CLOSED` | ADR-0008 specifies fixture/data, quarantine, retry, expiry, and deletion duties at `docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:159-195`. Typed fixture, quarantine, and deletion records are in the generated profile schema at `scripts/architecture/generate_contracts.py:1504-1819`; instance semantics are enforced at `scripts/architecture/validate_contracts.py:686-773`. Expired-quarantine, retry-to-PASS, and incomplete-deletion negatives are generated at `scripts/architecture/generate_contracts.py:4392-4486` and rejected. Empty instance arrays in the definition-only baseline do not claim runtime instances exist. |
| `DDDTDD-P1-003` — feedback speed was prose rather than a fitness function | `VERIFIED_CLOSED` | ADR-0009 defines four p50/p95 fast-loop and pre-verification objectives, reference-host ownership, deterministic selection/sharding, blocking omissions, and escalation at `docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:242-275`. `architecture/contracts/feedback-fitness.json` projects exactly four objectives; `validate_adr9_projections` validates its exact set and noncompensating semantics at `scripts/architecture/validate_contracts.py:1136-1320`. The objectives remain initial falsification thresholds and runtime `NOT_ASSESSED`, not achievement claims or compensating quality scores. |
| `DDDTDD-P1-004` — 34 boundaries and central orchestration lacked falsifiable fit/coupling evidence contracts | `VERIFIED_CLOSED` | ADR-0009 defines one hypothesis/falsifier row per canonical context at `docs/architecture/decisions/ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md:162-211` and six `governed_execution` coupling measures and review triggers at `213-240`. The generated `context-boundary-fitness.json` has exactly 34 rows and `context-coupling-policy.json` exactly six measures; `scripts/architecture/validate_contracts.py:1136-1320` checks exact projections, IDs, owners, alternatives, triggers, and runtime-status honesty. Fired falsifiers may lead to keep, merge, or split; they do not force microservices or decentralization. |
| `DDDTDD-P1-005` — AST guardrail was being mistaken for production-path parity | `VERIFIED_CLOSED` | ADR-0008's parity obligation is explicit at `docs/architecture/decisions/ADR-0008-make-tdd-the-default-development-discipline.md:42-75`. The six production-evidence obligations require built-artifact/composition identity always for task PASS and conditionally require mock classification, fake/real parity, SQLite/migrations, replay, and negative/mutation/fault evidence (`scripts/architecture/generate_contracts.py:469-505`). Exact-subject binding and noncompensating derivation are enforced at `scripts/architecture/validate_contracts.py:900-1067`; forged PASS negatives are at `scripts/architecture/generate_contracts.py:4317-4390`. Static bypass detection remains only a supplemental negative guardrail. With zero production files scanned, the final report correctly leaves production-path validation `NOT_ASSESSED`. |

## Exact denominators and noncompensating disposition

The final executable report is
`docs/architecture/assessments/validation-report.json`, status `PASS`, scope
`EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY`. Its relevant exact denominators are:

| Governed surface | Exact final disposition |
|---|---|
| Engineering-reference application | 9 source families; 34 practices; 33 applicable and design-`APPLIED`; 1 scoped design `NOT_APPLICABLE`; 0 partial; 0 material unknown |
| Rule assessments | 47 separate rows = 18 topology + 19 TDD + 10 boundary/feedback; all runtime `NOT_ASSESSED`; no numeric score |
| Architecture inventory | 909 elements; the practice profile maps 106 elements |
| Path ownership | 232 path contracts; 232 schema/semantic validated; 18 allowed test roots |
| Dependency and boundary fit | 67 declared context edges; 34 boundary-fit rows; 6 coupling measures |
| TDD failure and feedback model | 13 failure-mode classes; 4 feedback objectives; 6 production-evidence obligations |
| Executable contract corpus | 36 governed templates; 55 schemas; 25 negative fixtures; 2 canonical golden fixtures; 1 semantic fixture |
| Production observation | 0 production source files, 0 production topology files, and 0 observed test roots; runtime/source topology/production-test validation all `NOT_ASSESSED` |

The one scoped design N/A is
`ENGREF-CLEAN-CODER-ESTIMATE-VERSUS-COMMITMENT`: a static architecture design
contains no forecast, capacity promise, date, or delivery commitment. That N/A
does not carry into work-item planning.

There is deliberately no arithmetic “architecture score.” Every material rule
is assessed separately. A single applicable failed, unknown, stale,
wrong-subject, unsupported-N/A, or not-assessed obligation blocks a runtime
pass; a strong score elsewhere cannot compensate. This is the book-aligned
answer to “score every nut and bolt”: all design practices have an explicit
individual disposition, all 47 executable rules have an individual runtime
assessment row, and runtime scoring has honestly not started because the
runtime subject does not exist.

## Adversarial surface final disposition

| Surface | Final design/contract disposition |
|---|---|
| Empty/cargo-cult DDD folders | `PASS`: enacted-behavior-only folders plus lane-specific test shapes |
| Boundary ownership and public seams | `PASS`: exact context owners, public API surfaces, deny-by-default declared edges, exact exceptions |
| Hidden dependencies and cycles | `PASS` for declared graph and validators; actual source graph remains `NOT_ASSESSED` |
| Test-only paths, weak subject mocks, alternate reducers | `PASS` for prohibitions, production-evidence obligations, derivation, and negative fixtures; runtime parity remains `NOT_ASSESSED` |
| Happy-path bias and edge cases | `PASS` for exact 13-class denominator, applicability, assertions, and open/finite-space policies; execution remains `NOT_ASSESSED` |
| Fixtures, quarantine, retry, deletion | `PASS` for typed records and adversarial rejection; runtime instances remain `NOT_ASSESSED` |
| Feedback-loop ergonomics | `PASS` for the four objective contracts and deterministic scheduling policy; observed distributions remain `NOT_ASSESSED` |
| Boundary quanta and central coupling | `PASS` for 34 falsifiable boundary hypotheses and six coupling measures; empirical boundary fit remains `NOT_ASSESSED` |
| Book/source coverage | `PASS`: exact 9-family/34-practice design profile, no material design unknown |

## Build boundary and remaining proof obligations

These are implementation/verification obligations, not unresolved architecture
research:

1. enact `src/ranex`, the sole composition root, representative allowed test
   roots, generated Python/TypeScript consumers, and qualified runtime
   producers;
2. prove actual imports are a public-API-only subset of the 67-edge graph, with
   no private, adapter, legacy, exception, or cycle leakage;
3. exercise representative tracers against every applicable boundary falsifier
   and collect all six coupling measures;
4. measure all four feedback objectives on the declared reference host and
   candidate manifest without excluding failures or timeouts;
5. produce exact-subject task profiles proving the built artifact, composition,
   mocks/fakes, real adapters, SQLite/migrations, replay, failures, security,
   recovery, operations, and effectiveness required by risk; and
6. complete the distinct SDLC/MAP/AI gates and authenticated human acceptance.

`docs/architecture/AI_ARTIFACT_CONTRACTS.md:34-38` explicitly says this baseline
does not establish `AI-G2: PASS`; its remaining readiness work is enumerated at
`644-656`. `docs/architecture/AI_AGENT_DEVELOPMENT_LIFECYCLE.md:552-575`
separates architecture/contract readiness from `AI-G6` runtime verification and
forbids one namespace's pass from implying another's.

## Frozen evidence integrity

| Artifact | SHA-256 |
|---|---|
| Generated architecture tree | `843b342db9863a6f7f97e1868ac47d04e36aa45c1db050488c6648f8d1a7b900` |
| Registry manifest | `402b8e36755b59645ccbde78c89be1a2912c1d12831a02aeffeac19fc49bb592` |
| Final validation report | `6a27f29d70a58676a57f1b82e7d7584d67eb684c36c14e51d715a5d639df5962` |
| Architecture-practice application profile | `0c694d80fe20a5b266d6dcd22cada9764a42e661e6afa27db9c15a4c488800f7` |
| ADR-0009 | `727ac9b9be3d5b560967d4ce43504bd12c0e91cdb028988a16b23ef55c500041` |

Generation and validation share the repository-scoped lock documented at
`scripts/architecture/README.md:24-34`. The concurrency regression passed twice,
and two shared generate/validate runs produced the same frozen tree. The lock
and regression mechanism prevents a validator or second generator from
observing a partially cleaned or partially published contract tree. This review
does not convert that deterministic documentation-contract result into a
runtime or release seal.
