# ADR-0008: Make TDD the Default Development Discipline

| Field | Value |
|---|---|
| ADR ID | `ADR-0008` |
| Version | `1.0.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-28 |
| Effective revision | Working tree based on `4baad4a67843b02d5970f442fb54aed8d6525dda`; executable projection and enactment pending |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | All production code, schemas, migrations, generators, adapters, configuration behavior, and their verification |
| Supersedes | None |
| Review/expiry date | First implementation tracer, first flaky-test quarantine, then quarterly |
| Compatibility/migration class | Default construction discipline with bounded recorded exceptions |
| Security/data class | Public policy; test subjects/data/evidence retain source classification |

## Decision

Test-driven development is Ranex's default construction discipline:

```text
acceptance + risk + failure model
  -> RED: prove a relevant test fails for the intended reason
  -> GREEN: make the smallest production change that satisfies it
  -> REFACTOR: improve structure while preserving behavior
  -> ARCHITECTURE CHECK: re-run boundary, contract, security and fitness rules
```

The loop applies at a useful behavior/invariant boundary, not mechanically once
per method. It is subordinate to requirements, architecture, risk,
independent verification, release, and operations. TDD does not make its author
an approver and cannot replace acceptance, integration, security, resilience,
recovery, performance, or production evidence.

Each implementation handoff records the exact requirement/risk/failure-matrix
references, base and candidate subject digests, failing RED result, GREEN
result, refactor/architecture-check result, test/fixture/seed versions, and any
exception. A test that was already green or failed only because the harness was
broken is not RED evidence.

## Production-path and build-once invariant

Deterministic tests exercise actual production code:

- the same public APIs, composition root, domain/application code, authority
  reducer/UoW, policy/gate code, schemas, migrations, and adapter
  implementations used by the release;
- no test-only business branch, alternate reducer, weakened authentication,
  gate/policy bypass flag, hidden service locator, or mock of the subject under
  test;
- one release candidate is built once, content-digested, and every gate-bearing
  contract/integration/acceptance/system/e2e/security/performance/resilience
  lane installs or invokes that same artifact and release profile;
- fast source-checkout unit loops are advisory until the same tests pass
  against the built candidate where applicable; and
- test observability emits the same structured events/metrics/audit fields as
  production, with a test subject/profile marker rather than a separate code
  path.

Determinism enters only through declared ports for clock, monotonic time,
randomness, ID generation, network, filesystem, provider/tool transport, and
external effects. Seeds, clocks, fixtures, schedules, and fault programs are
recorded. External effects may be replaced at a port; the domain/application/
authority/policy subject may not.

Every fake has adapter-to-fake contract/parity tests and representative
real-adapter integration/failure tests. Persistence lanes use ephemeral real
SQLite databases created by the production migrations and UoW; in-memory
dictionaries cannot prove SQLite constraints, locking, crash behavior, or
migration correctness.

Synthetic evidence proves only the bounded property exercised. It cannot claim
a production outcome, provider behavior, operating SLO, restore success, or
real sandbox denial.

## Acceptance- and risk-first test selection

Before RED, the packet maps each owned requirement, invariant, acceptance/
rejection example, quality attribute, threat, migration, external effect, and
operating risk to the lowest-cost convincing test lane. Higher-risk seams retain
representative real integration and system proof even when unit tests are
excellent.

Happy-path-only evidence is invalid. Every capability maintains a versioned
failure-mode/edge-case matrix. At minimum it evaluates applicability for:

1. every declared command and state transition, including legal and illegal
   transition pairs;
2. validation rejection and authentication/authorization/policy denial;
3. stale, missing, malformed, conflicting, wrong-subject, or unavailable proof;
4. minimum/maximum, empty/null, Unicode, size, time/deadline/clock-jump, and
   resource boundaries;
5. duplicate, reordered, replayed, retried, and idempotency-key operations;
6. crash points before/after durable boundaries, timeouts, cancellation, and
   acknowledgement loss;
7. concurrency races, double claim, lease expiry, pauses, reclaim, and stale
   fencing epochs at the resource/effect sink;
8. storage full, lock contention, corruption, migration failure/rollback,
   snapshot/replay mismatch, and version incompatibility;
9. network/provider/tool failure, route/identity mismatch, malformed/oversized
   responses, partial external effects, and reconciliation;
10. backup/restore and restored-state/external-effect reconciliation;
11. privacy deletion, retention/expiry/legal hold, log/telemetry redaction, and
    test-data disposal;
12. supplier/package/schema/route/provenance mismatch; and
13. every declared recovery, backward, rollback, block/resume, cancel, and
    terminal path.

For each applicable row the matrix records exact subject, precondition, fault/
input, expected error, event, resulting state/version, explicitly absent
effect, recovery/reconciliation, test lane, evidence, and owner. A material
`UNKNOWN` blocks the relevant gate. `NOT_APPLICABLE` requires a registered rule
and evidence; omission is not N/A.

Finite registries/state machines require exhaustive registered transition-pair
coverage, including prohibited pairs. Open input spaces require declared
partitions/properties/invariants plus property/model-based tests, deterministic
fuzz seeds/corpus, shrinking/reproduction data, mutation/negative tests, and
fault injection proportionate to risk. Reports name the explored domain and
remaining unknowns; they never claim “all conceivable edge cases.”

## Canonical test taxonomy

These are the only top-level `tests/` roots. Specialized roots remain subject
to the same production-path and exact-subject rules.

| Root | Purpose |
|---|---|
| `tests/unit/<context>/domain/` | Pure aggregate/value-object/domain-rule examples and properties |
| `tests/unit/<context>/application/` | Use-case behavior through owned ports |
| `tests/contract/<context>/` | Public API, schema, port, fake/real-adapter parity and compatibility |
| `tests/integration/<context>/` | Real adapter, SQLite, process, provider sandbox, and cross-boundary integration |
| `tests/architecture/` | Path/ownership/import/cycle/composition/discovery/generated-drift fitness |
| `tests/acceptance/<capability>/` | Executable owned acceptance/rejection examples |
| `tests/system/` | Complete local product/profile behavior across contexts |
| `tests/e2e/` | Production-shaped entry-to-effect/outcome tracer across delivery edges |
| `tests/security/` | Authentication, authorization, policy/gate, secret, sandbox, provenance and abuse denial |
| `tests/performance/` | Versioned workload/load/latency/capacity distributions |
| `tests/resilience/` | Crash, timeout, cancellation, race, fault injection, recovery and reconciliation |
| `tests/migration/<context>/` | Forward/backward/upcast/rollback/version and dirty-data behavior |
| `tests/replay/<context>/` | Reducer/event/snapshot/digest repeatability and erasure semantics |
| `tests/operations/` | Backup/restore, install/update/rollback, runbook and observability checks |
| `tests/qualification/` | Checker/module/route/isolation qualification fixtures |
| `tests/effectiveness/` | Whole-workflow comparative outcome/guardrail experiments |
| `tests/evaluation/` | Frozen/hidden evaluation harnesses separated from makers |
| `tests/fixtures/<owner>/` | Immutable external/golden/fault corpora with provenance/classification |
| `tests/builders/<context>/` | Owned deterministic object/packet builders without alternate business rules |

`tests/persistence/` moves to the owning context's `integration` or `migration`
lane. `tests/crash/` moves to `resilience`. A test path must identify its
context/capability/owner in metadata even when the root is cross-cutting.

Tests name public behavior, invariant, scenario, or regression—not the fact that
a method exists. Tests may inspect durable events/state needed by the public
contract, but avoid brittle assertions about private call order or internal
shape unless that shape is itself a registered architecture invariant.

## Seams, fakes, fixtures, and data

- Boundary fakes implement the same owner-defined port as the real adapter and
  model failures, time, cancellation, retries, limits, and idempotency relevant
  to their declared scope.
- Do not mock the aggregate, use case, reducer, policy decision, gate evaluator,
  migration, schema validator, or composition logic being verified.
- Contract/parity suites run against every fake and supported real adapter.
  Representative real-adapter integration remains mandatory.
- Context-local builders/fixtures stay with the context owner. Shared corpora
  require a named owner and stable semantic contract; copy/paste fixture
  variants and mutable global fixtures are prohibited.
- Snapshots are bounded to stable public/serialized contracts, human-reviewable,
  normalized, size-limited, and updated only with an explained behavior change.
  Unbounded UI/log/object snapshots cannot replace assertions.
- Test data is synthetic or lawfully approved, minimized, classified,
  secret-scanned, access-controlled, and expired/purged under retention policy.
  Production personal data and credentials are prohibited by default.

## Flakiness, obsolete tests, generated code, and lanes

A nondeterministic test is an evidence-integrity defect:

- it is never retried into `PASS`; all attempts remain visible;
- quarantine requires owner, exact test/subject, observed failure distribution,
  suspected cause, affected gate/risk, alternate evidence, work item, expiry,
  and removal criteria;
- quarantine cannot waive a blocking invariant; material uncovered risk remains
  `UNKNOWN` and blocks;
- expiry automatically restores blocking status unless a new accountable
  decision exists; and
- time/random/network dependence is moved behind declared ports rather than
  hidden with sleeps or broad retries.

Obsolete tests are deleted when the owned requirement/behavior is deliberately
removed and traceability, fixtures, generated artifacts, compatibility, and
risk records are updated. A hard-to-maintain failing test is not obsolete.

Generated output is exempt from line-by-line RED/GREEN work. Its generator,
canonical schema/input, generated API behavior, compatibility, golden fixtures,
and drift are tested; generated files remain non-hand-edited.

Fast deterministic unit/contract/architecture lanes run on each candidate.
Real SQLite/integration/acceptance/security lanes run before verification.
System/e2e/resilience/migration/operations and performance lanes run according
to risk and release profile. A slow label changes scheduling only; it cannot
waive a required gate or run against a different artifact.

Mutation testing is selective by risk for authority, policy/gate, reducer,
validation, idempotency, migration, security, and other critical assertions.
Surviving mutations identify missing falsifiers; mutation percentage is neither
an overall quality score nor a universal release threshold.

## Noncompensating quality signals

Line/branch coverage, test counts, pyramid ratios, mutation scores, snapshot
counts, suite speed, and green-run rate are diagnostic distributions. None can
compensate for a missing acceptance example, untested material failure,
surviving critical mutation, flaky blocking test, real-seam gap, security/
recovery failure, stale subject, or `UNKNOWN`.

There is no universal coverage percentage, fixed unit/integration ratio,
one-test-per-method requirement, or interaction-mock quota. The decision rule
is risk and falsification strength on the exact production subject.

## Machine-checkable TDD rules

```yaml
tdd_rule_set: "RANEX-TDD-1.0"
allowed_test_roots:
  - unit
  - contract
  - integration
  - architecture
  - acceptance
  - system
  - e2e
  - security
  - performance
  - resilience
  - migration
  - replay
  - operations
  - qualification
  - effectiveness
  - evaluation
  - fixtures
  - builders
rules:
  - {id: "TDD-LOOP-001", enforcement: "BLOCK", invariant: "Each implementation change binds RED, GREEN, REFACTOR and architecture-check evidence or a valid exception."}
  - {id: "TDD-PROD-001", enforcement: "BLOCK", invariant: "Tests execute production domain/application/authority/policy/schema/migration code with no test-only business branch or weakened control."}
  - {id: "TDD-ARTIFACT-001", enforcement: "BLOCK", invariant: "Gate-bearing lanes test one content-digested candidate artifact and release profile."}
  - {id: "TDD-SEAM-001", enforcement: "BLOCK", invariant: "Nondeterminism/external effects enter only through declared ports with recorded controls, and every fake has parity plus representative real-adapter evidence."}
  - {id: "TDD-SQLITE-001", enforcement: "BLOCK", invariant: "Persistence evidence uses ephemeral real SQLite, production migrations and the production UoW."}
  - {id: "TDD-TAXONOMY-001", enforcement: "BLOCK", invariant: "Every test resides in an allowed root and resolves to one context/capability owner, lane and exact subject."}
  - {id: "TDD-FAILURE-001", enforcement: "BLOCK", invariant: "Every capability has a complete versioned applicability/result row for each required failure-mode category."}
  - {id: "TDD-STATE-001", enforcement: "BLOCK", invariant: "Closed state/command/gate/effect registries have exhaustive legal and illegal transition-pair coverage."}
  - {id: "TDD-OPEN-001", enforcement: "BLOCK", invariant: "Open input spaces declare properties/partitions and reproducible property/model/fuzz/mutation/fault evidence plus remaining unknowns."}
  - {id: "TDD-FIXTURE-001", enforcement: "BLOCK", invariant: "Fixtures/builders have one owner, provenance/classification/version, deterministic semantics and no duplicate business rule."}
  - {id: "TDD-FLAKE-001", enforcement: "BLOCK", invariant: "Retries/quarantine never manufacture PASS; every quarantine is owned, expiring and preserves material UNKNOWN/blocking status."}
  - {id: "TDD-GENERATED-001", enforcement: "BLOCK", invariant: "Generated-code exceptions bind generator/schema/golden/compatibility/drift tests and prohibit hand edits."}
  - {id: "TDD-MIGRATION-001", enforcement: "BLOCK", invariant: "Migration/replay evidence covers forward/backward/rollback/crash/corruption/version/digest repeatability on production code."}
  - {id: "TDD-DATA-001", enforcement: "BLOCK", invariant: "Test data satisfies classification, minimization, provenance, secret, access, retention and deletion policy."}
  - {id: "TDD-LANES-001", enforcement: "BLOCK", invariant: "Risk/release policy schedules every required lane against the same subject; slow scheduling cannot waive it."}
  - {id: "TDD-MUTATION-001", enforcement: "REQUIRED", invariant: "Risk-selected critical logic receives mutation/negative assertion-strength evidence with survivor disposition."}
  - {id: "TDD-OBS-001", enforcement: "BLOCK", invariant: "Test paths emit production-equivalent structured observability with explicit test subject/profile identity."}
  - {id: "TDD-NONCOMP-001", enforcement: "BLOCK", invariant: "Proxy scores cannot compensate for missing, failed, stale, flaky or UNKNOWN required evidence."}
  - {id: "TDD-EXEMPTION-001", enforcement: "BLOCK", invariant: "Every TDD exception is typed, exact-scope, owned, risk-assessed, alternative-evidenced, expiring and backfilled."}
```

Allowed TDD exception classes:

| Class | Required substitution |
|---|---|
| `GENERATED_OUTPUT` | Test canonical inputs/schema, generator, generated public behavior, compatibility, golden output and drift |
| `EMERGENCY_CONTAINMENT` | Authenticated emergency decision, failing characterization/monitor where feasible, exact risk/rollback evidence, and backfill before the next non-emergency release |
| `NON_EXECUTABLE_DOCUMENTATION` | Exact path/applicability proof plus link/render/schema/example checks; embedded executable/config behavior is not exempt |

Every exception records ID, class, exact paths/behavior, skipped loop steps,
risk, alternate proof, authority, work item, creation/expiry, backfill, and
removal evidence. Exceptions cannot waive subject binding, required
independent review, security/authority invariants, or external obligations.

## Fitness evidence

| ID | Required evidence |
|---|---|
| `FF-TDD-001` | A representative change preserves inspectable RED→GREEN→REFACTOR→architecture-check results tied to the exact candidate. |
| `FF-TDD-002` | Test-only branch/bypass and subject-mock probes fail; built-artifact lanes identify one digest/profile. |
| `FF-TDD-003` | Fake/real adapter parity, ephemeral SQLite/migration, and production-equivalent observability checks pass. |
| `FF-TDD-004` | Failure matrix coverage reconciles every required category and closed transition pair; missing/material unknowns block. |
| `FF-TDD-005` | Property/fuzz/fault evidence reproduces from recorded seeds/corpus and reports explored domain/shrinking/unknowns. |
| `FF-TDD-006` | Quarantine expiry/retry tests prove no flaky run can become gate PASS. |
| `FF-TDD-007` | Critical mutation/negative tests demonstrate that assertions detect representative wrong behavior. |
| `FF-TDD-008` | Migration/replay/crash/backup/restore/reconciliation tests use the production artifact and real durable seams. |

No current runtime enactment is claimed.

## Engineering-reference application and limitations

| Registered practice | Precise retained locator | Applied use |
|---|---|---|
| `ENGREF-CLEAN-CODER-ACCEPTANCE-EXAMPLES` | `ENGREF-CLEAN-CODER-MD`, “Acceptance Tests,” lines 2652–2674 | Requirement-bound executable accept/reject examples |
| `ENGREF-CLEAN-CODER-RISK-LAYERED-TESTING` | same representation, “Testing Strategies,” lines 2928–2998 | Risk/failure-mode selection across local through exploratory evidence |
| `ENGREF-CLEAN-CODE-VERIFIED-REFACTORING` | `ENGREF-CLEAN-CODE-MD`, lines 5210–5450 | Small behavior-preserving refactor step |
| `ENGREF-CLEAN-CODE-THIRD-PARTY-BOUNDARY` | same representation, Ch.8, lines 3128–3454 | Owned seams plus adapter contract/failure tests |
| `ENGREF-CLEAN-CODE-SEPARATE-CONSTRUCTION-RUNTIME` | same representation, Ch.11, lines 4098–4158 | One production composition path |
| `ENGREF-CODE-COMPLETE-CH5-INFORMATION-HIDING` | `ENGREF-CODE-COMPLETE-CH5-MD`, lines 1273–1395 | Narrow public contracts and volatile-boundary tests |
| `ENGREF-PRAGMATIC-PROGRAMMER-1E-ORTHOGONALITY` | `ENGREF-PRAGMATIC-PROGRAMMER-1E-MD`, lines 1393–1449 | Change-local tests and explicit necessary coupling |
| `ENGREF-PRAGMATIC-PROGRAMMER-1E-TRACER-ROUTE` | same representation, lines 1792–1842 | Production-shaped end-to-end falsification |
| `ENGREF-SWEBOK-V4A-TRACE-CHANGE-QUALITY` | `ENGREF-SWEBOK-V4A-MD`, lines 1580–1614 | Requirements-to-test/release/maintenance trace |
| `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS` | `ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-MD`, lines 700–716 | Exact-subject invariant/threshold/cadence/failure response |
| `ENGREF-CLEAN-ARCHITECTURE-1E-ENCAPSULATION-AND-TESTABILITY` | registered PDF, Ch.28 pp.192–193 and Ch.34 pp.230,235 | Protected, testable boundaries without production bypass |
| `ENGREF-DDIA-1E-ER6-MONOTONIC-TIMEOUTS` | `ENGREF-DDIA-1E-ER6-MD`, lines 6970–7005 | Clock-jump/suspend/timeout properties |
| `ENGREF-DDIA-1E-ER6-FENCING-AT-RESOURCE` | same representation, lines 7120–7306 | Stale-worker/sink fencing tests |
| `ENGREF-DDIA-1E-ER6-ATOMIC-OUTBOX-AND-DERIVATIONS` | same representation, lines 10420–10487 | Crash/duplicate/order/reconciliation tests |
| `ENGREF-DDIA-1E-ER6-COMMAND-EVENT-REPLAY` | same representation, lines 10505–10609 | Reducer/replay/snapshot/digest equivalence |
| `ENGREF-DDIA-1E-ER6-IDEMPOTENT-EFFECTS` | same representation, lines 10915–10942 | Duplicate/crash-after-effect/idempotency tests |

The registry contains no distinct practice ID that universally mandates the
RED/GREEN/REFACTOR mechanics, fixture factories, flaky quarantine, mutation
testing, one-test-per-method, or a mock style. Those are Ranex decisions or
risk-selected techniques, not book-proven universal laws. Fixed pyramid
percentages and coverage thresholds are explicitly rejected. Clean Code/TDD-era
heuristics are contextual; Clean Coder ratios are non-universal; Code Complete
evidence is retained Ch.5 only; Pragmatic tooling is dated; SWEBOK is a
knowledge map; DDIA examples do not supply Ranex security/privacy controls; FSA
fitness checks do not turn proxy metrics into quality scores.

## Alternatives considered

1. **Test after implementation.** Rejected as the default because the expected
   falsifier and production seam become too easy to retrofit around the code.
2. **TDD as the only verification layer.** Rejected because local examples do
   not prove integration, security, recovery, performance, or outcomes.
3. **Coverage/pyramid/mutation percentage gate.** Rejected because a proxy can
   be optimized while material behavior remains untested.
4. **Mock-heavy internal interaction tests.** Rejected because they can verify
   an invented implementation rather than production behavior.
5. **Retry flaky tests until green.** Rejected because it manufactures false
   confidence and destroys exact evidence.

## Consequences and adoption

Implementation packets become more explicit about behavior, risks, failure
models, production seams, and exact evidence. Some changes will take longer,
while faults should surface earlier and refactoring becomes safer. The contract
lane must project this ADR into machine test-policy/failure-mode registries and
validate it against the path registry before `AI-G2`. Existing tests are
classified/migrated incrementally; a file move alone is not evidence of TDD.

## Human approval

The human owner made TDD the non-negotiable default and required deterministic
tests through actual production paths plus comprehensive negative/failure
coverage. This ADR records the paper policy. It does not claim current tests or
runtime enact it.

