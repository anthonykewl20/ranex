# ADR-0008: Make TDD the Default Development Discipline

| Field | Value |
|---|---|
| ADR ID | `ADR-0008` |
| Version | `1.6.0` |
| Status | `ACCEPTED` |
| Implementation-start readiness | `NOT_ASSESSED`; governed by ADR-0012 |
| Runtime evidence status | `NOT_ASSESSED` |
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

Test-driven development is Ranex's default construction discipline for
behavior changes and defect fixes:

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

A task does not self-assert its sequence. Every executable `TaskPacket` names
one governed `TddCycleRecordV1`; its `TestPracticeProfile` references the same
cycle ID. The cycle binds the work item and task-packet digest, one immutable
base subject, one immutable final candidate subject, and exactly one declared
change profile. The profile determines the only legal ordered step sequence:

| Change profile | Exact step sequence |
|---|---|
| `BEHAVIOR_CHANGE` | `RED -> GREEN -> REFACTOR -> ARCHITECTURE_CHECK`, or `RED -> GREEN -> ARCHITECTURE_CHECK` only when `no_refactor_needed: true` |
| `DEFECT_FIX` | `RED -> GREEN -> REFACTOR -> ARCHITECTURE_CHECK`, or `RED -> GREEN -> ARCHITECTURE_CHECK` only when `no_refactor_needed: true` |
| `REFACTOR_ONLY` | `BASELINE_GREEN -> REFACTOR -> ARCHITECTURE_CHECK` |
| `GENERATED_OUTPUT` | `GENERATE -> VALIDATE -> ARCHITECTURE_CHECK` plus one active exact-subject `GENERATED_OUTPUT` exception |
| `EMERGENCY_CONTAINMENT` | `EMERGENCY_FIX -> VALIDATE -> ARCHITECTURE_CHECK` plus one active exact-subject `EMERGENCY_CONTAINMENT` exception and its governed backfill |
| `NON_EXECUTABLE_DOCUMENTATION` | `DOCUMENTATION_CHECK -> ARCHITECTURE_CHECK` plus one active exact-subject `NON_EXECUTABLE_DOCUMENTATION` exception |

No phase is invented to satisfy a schema. `REFACTOR_ONLY` starts from a
qualified green baseline and never fabricates RED evidence. A
`no_refactor_needed` decision means GREEN already satisfies the registered
structure rules; it is a machine-visible outcome, not an empty REFACTOR step.

Each step has an immutable step-snapshot digest, a typed checker reference,
and observed start/finish time. RED must be a completed expected failure
matching one closed `ExpectedFailureFingerprintV1`, not a launch, unrelated
failure, timeout, cancellation, error, or harness failure. The fingerprint
binds the exact stable test, acceptance/risk criterion, failure-denominator
row, and canonical matcher definition. Passing steps must be completed passes
on their named snapshots; the final architecture-check snapshot equals the
single candidate subject. Step and artifact times are strictly causal. A
missing, extra, reordered, reused, wrong-subject, or post-hoc step blocks.

The cycle binds one exact slice of the governed run journal. That slice names
the run, inclusive journal cursors, one activity ID per declared step, the
phase-activity manifest digest, and the journal manifest digest. Generic
`ActivityRequested`, `ActivityDispatched`, `ActivityResolved`,
`EvidenceSnapshotBound`, and `GateEvaluated` facts remain the causal
authorities; TDD does not create a second lifecycle or an unowned event
family.

The cycle also partitions the complete current architecture-rule registry
into applicable and governed `NOT_APPLICABLE` IDs. The architecture-check
result must cover every applicable ID exactly once; every N/A ID requires a
current exact-subject applicability proof. An opt-out string, a partial
checker coverage list, or a rule added after the bound registry digest makes
the cycle stale and blocking.

The same record binds:

- one bytewise canonical test-denominator manifest for the owned requirement,
  risk, invariant, transition, acceptance/rejection, and regression test IDs;
- one complete failure-denominator manifest with exactly one disposition for
  every required failure-mode category and every applicable closed transition
  pair;
- exactly one built artifact digest and one release-profile ID/version/digest
  for all gate-bearing lanes; and
- the exact active TDD-exception IDs, if any, with the cycle result derived
  noncompensatingly from every applicable obligation.

Changing any denominator, subject, step, artifact, profile, or exception makes
the prior cycle stale; an aggregate test count or prose handoff cannot repair
it.

`TddCycleRecordV1` is a pre-landing fact with logical status
`PROPOSED -> GATED | REJECTED`. It never contains a landing ID, landing time,
or post-landing acceptance assertion. `GATED` requires a qualified passing
cycle gate on the exact cycle subject; it does not mean the candidate landed.
The existing landing authority then emits the canonical `LandingRecord` as the
post-landing receipt, with its subject tuple equal to
`TDD_CYCLE_SUBJECT_V1`, its candidate commit equal to the cycle candidate, and
its landed commit proven by the ordinary commit-preserving landing contract.
The read model may derive `ACCEPTED` only by joining one immutable `GATED`
cycle with one eligible `SUCCEEDED` landing receipt. Neither producer updates or
embeds the other producer's fact, so gating cannot depend on a future landing
and landing cannot rewrite gate history.

Every cycle declares a closed reproducibility envelope. Tier 1 always binds
deterministic seed, input, rule-version, and journal-capture manifests. Tier 2
additionally binds the image, toolchain, network policy, filesystem policy,
dependency lock, and execution-capability profile. Tier selection is declared
by policy before execution, recorded in the run journal, and cannot be
downgraded after a failure. High-risk, seam, quarantine, security, migration,
recovery, and release-bearing lanes require Tier 2; other lanes may use Tier 1
only when the applicable profile explicitly permits it.

RED-bearing profiles bind `OracleProvenanceV1` to the immutable requirement,
acceptance criterion, risk, invariant, contract, or incident characterization
that defines the expected result. Tier 2 always requires oracle provenance;
Tier 1 non-RED profiles may omit it only when the applicability profile proves
that no behavior oracle exists. The oracle declaration records its authority
basis and independence class. A value derived only from the production code
under test, a generated snapshot blessed by the same change, or an
unreviewed circular expectation cannot authorize RED or PASS.

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

### Canonical test-health authorities

Four record classes are the sole instance authorities for TDD cycles,
exceptions, flaky-test quarantine, and obsolete-test retirement:

```text
architecture/records/test-health/
├── tdd-cycles/
│   └── <cycle_id>.json
├── tdd-exceptions/
│   └── <exception_id>.json
├── quarantines/
│   └── <quarantine_id>.json
└── obsolete-test-deletions/
    └── <deletion_id>.json

schemas/common/tdd-cycle-record-v1.schema.json
schemas/common/tdd-exception-record-v1.schema.json
schemas/common/test-quarantine-record-v1.schema.json
schemas/common/test-deletion-record-v1.schema.json

architecture/contracts/tdd-cycle-records.json
  registry_id: REG-TDD-CYCLE-RECORDS-001
architecture/contracts/tdd-exception-records.json
  registry_id: REG-TDD-EXCEPTION-RECORDS-001
architecture/contracts/test-quarantine-records.json
  registry_id: REG-TEST-QUARANTINE-RECORDS-001
architecture/contracts/test-deletion-records.json
  registry_id: REG-TEST-DELETION-RECORDS-001
```

The exact classes are `TddCycleRecordV1` (`tdd-cycle-record/v1`,
`TDD_CYCLE_RECORD_V1`), `TddExceptionRecordV1`
(`tdd-exception-record/v1`, `TDD_EXCEPTION_RECORD_V1`),
`TestQuarantineRecordV1` (`test-quarantine-record/v1`,
`TEST_QUARANTINE_RECORD_V1`), and
`TestDeletionRecordV1` (`test-deletion-record/v1`,
`TEST_DELETION_RECORD_V1`). The compiler reads only direct canonical JSON
files whose filename equals the safe record ID, validates and byte-digests
each source, and projects the four separately content-bound registries. The
initial source sets and registries are empty.

`TestPracticeProfile` holds only `tdd_cycle_ids`, `tdd_exception_ids`,
`quarantine_ids`, and `obsolete_test_deletion_ids`; it cannot embed a competing
cycle, exception, quarantine, deletion, approval, or lifecycle authority.
Definition-only profiles may cite definition sources while remaining
`NOT_ASSESSED`; a runtime `PASS`, `NOT_APPLICABLE`, exception, quarantine, or
deletion claim requires governed runtime artifacts.

Those ID arrays are trace projections, never population authority. For the
exact task/candidate/test/gate/risk subject, the validator queries all four
canonical registries and reconciles the supplied IDs to the complete applicable
population, plus explicitly allowed immutable historical references. Omitting
an applicable cycle, active exception, active or expired-unclosed quarantine,
or deletion lineage cannot hide it; an extra, missing, duplicate, wrong-subject,
or stale ID blocks.

All runtime references use this exact object, never a bare string:

```text
TypedArtifactRefV1:
  fields: [artifact_type, artifact_ref, artifact_digest]
  artifact_type:
    evidence_snapshot | checker_result | gate_evaluation |
    human_decision | review_verdict
  artifact_digest: sha256:<64 lowercase hex>
```

The authoritative artifact/catalog resolver must load the referenced canonical
bytes, validate the registered schema and producer, require the artifact ID at
the per-kind path below to equal `artifact_ref`, recompute the RFC 8785 digest
of the artifact excluding its `digest` member, require both that value and the
artifact's own `digest` to equal `artifact_digest`, and extract the subject
through the per-kind paths below. It then compares the extracted tuple with the
exact subject required by the reference role, not one ambiguous global
subject.

`CheckerResultV1` therefore adds required top-level `subject_schema`,
`subject_ref`, and `subject_digest` claim-subject fields. Its existing closed
nested `subject` remains the exact execution/source manifest on which the
checker ran; it does not replace the claim-subject tuple. The checker
qualification binds both, and the role-specific subject below binds the
candidate/base/artifact facts in the execution manifest. This normalization is
required before the checker schema may support a runtime pass.

It also adds required nullable `failure_fingerprint`. A checker for a RED step
sets it to the complete `ExpectedFailureFingerprintV1` it evaluated and proves
that the resolved matcher accepted the observed qualified assertion failure.
Every non-RED checker sets it to null. A free-form coverage string or matching
`failure_code` alone cannot stand in for the stable-test, criterion,
failure-row, and matcher binding.

The nested execution subject also adds required
`test_practice_profile_id`, `test_practice_profile_version`, and
`test_practice_profile_digest`, plus nullable-as-a-complete-triple
`release_profile_id`, `release_profile_version`, and
`release_profile_digest`. These are closed schema fields, not free-form
coverage labels. The role predicates below bind every checker to the exact
base commit, candidate commit, built-artifact digest, test-practice profile,
and release profile that it actually executed.

The resolver also verifies qualified checker/evaluator route and code, required
claims and coverage, outcome, authentication and role, review independence,
issue/observation/expiry times, freshness, revocation, missing claims, and
conflicts. `CheckerResult` is the only direct checker outcome;
`EvidenceSnapshot` freezes eligible evidence; `GateEvaluation` must be
qualified and `PASS`; owner acceptance is an authenticated, unexpired
`HumanDecisionRecord` with status `APPROVED`; and an independent review is an
`ACCEPTABLE` `ReviewVerdict` backed by a passing independence evaluation and no
open blocking finding. Missing, dangling, bare string, wrong-type,
wrong-digest, wrong-subject, unqualified, self-produced, stale, expired,
revoked, or conflicting material is `UNKNOWN` and blocks. No artifact class
compensates for another.

The schemas use these exact closed field sets; nested `*_ref` evidence,
decision, gate, and review fields are `TypedArtifactRefV1` unless explicitly
described otherwise:

```text
TddCycleRecordV1:
  fields: [schema_version, record_type, cycle_id, policy_id, policy_version,
    test_practice_profile_id, test_practice_profile_version,
    test_practice_profile_digest, work_item_id, task_packet_id,
    task_packet_digest, change_profile, no_refactor_needed, base_subject,
    candidate_subject, subject_transition_manifest, steps,
    cycle_journal_binding, test_denominator_manifest_digest,
    failure_denominator_manifest_digest, architecture_rule_coverage,
    architecture_rule_not_applicable_proofs, oracle_provenance,
    reproducibility_envelope, built_artifact_digest, built_artifact_evidence_ref,
    release_profile_id, release_profile_version, release_profile_digest,
    tdd_exception_ids, quarantine_ids, evidence_snapshot_ref,
    cycle_gate_evaluation_ref, exact_subject_ref, exact_subject_digest,
    gated_at, recorded_at, result, status]
  subject_fields: [subject_schema, subject_ref, subject_digest]
  step_fields: [step_kind, sequence, step_subject, step_snapshot_digest,
    checker_result_ref, expected_outcome, expected_failure_fingerprint,
    started_at, finished_at]

TddExceptionRecordV1:
  fields: [schema_version, record_type, exception_id, exception_class,
    policy_id, policy_version, test_practice_profile_id,
    test_practice_profile_version, test_practice_profile_digest,
    applicable_cycle_ids, subject_schema, subject_ref, subject_digest,
    exact_paths, behavior_ids, skipped_steps, risk_trace_dispositions,
    external_obligation_dispositions, alternate_evidence_refs, owner_id,
    owner_decision_ref, work_item_id, backfill_work_item_id, created_at,
    expires_at, backfill_criteria, removal_criteria, closure_evidence_refs,
    landing_record_ref, exact_subject_ref, exact_subject_digest, accepted_at,
    recorded_at, status]

TestQuarantineRecordV1:
  fields: [schema_version, record_type, quarantine_id, policy_id,
    policy_version, test_practice_profile_id, test_practice_profile_version,
    test_practice_profile_digest, base_subject, candidate_subject,
    built_artifact_digest, release_profile_id, release_profile_version,
    release_profile_digest, affected_test_ids, affected_paths,
    observed_attempt_refs, observed_failure_distribution,
    affected_gate_ids, risk_trace_dispositions, alternate_evidence_refs,
    owner_id, owner_decision_ref, work_item_id, opened_at, expires_at,
    removal_criteria, restoration_backfill_evidence_refs,
    quarantine_evidence_snapshot_ref, quarantine_checker_result_refs,
    landing_record_ref, exact_subject_ref, exact_subject_digest, accepted_at,
    recorded_at, status]

TestDeletionRecordV1:
  fields: [schema_version, record_type, deletion_id, target_kind, policy_id,
    policy_version, tdd_rule_set_id, test_practice_profile_id,
    test_practice_profile_version, test_practice_profile_digest,
    profile_freshness_status, stable_test_id, source_migration_proof_ids,
    affected_scope_id, legacy_baseline_source_row, legacy_current_source_row,
    legacy_source_state_kind, source_change_exception_id,
    closes_change_exception_id, before_commit_sha1, after_commit_sha1,
    before_tests_tree_oid_sha1, after_tests_tree_oid_sha1,
    before_tests_snapshot_digest, after_tests_snapshot_digest,
    before_test_row, after_test_row, tests_delta_manifest_digest,
    requirement_trace_dispositions, risk_trace_dispositions, reason,
    fixture_cleanup_refs, snapshot_cleanup_refs, test_data_cleanup_refs,
    removal_checker_result_refs, retirement_evidence_snapshot_ref,
    retirement_gate_evaluation_ref, retirement_disposition,
    owner_id, owner_acceptance_ref,
    process_assurance_owner_acceptance_ref, independent_review_ref,
    landing_record_ref, exact_subject_ref, exact_subject_digest, accepted_at,
    recorded_at, resulting_gap_status, result, status]
```

Every nested object used by those records is closed by the following
machine-readable catalog. A type's `type_version` versions its shape; it is not
an additional instance field unless listed in `fields`. `nonempty_string`
means a trimmed UTF-8 string of 1..1024 code points; `safe_id` means
`^[A-Za-z][A-Za-z0-9._:-]{0,254}$`; `safe_path` is a normalized repository
relative POSIX path with no empty, `.`, `..`, absolute, NUL, or backslash
segment; `sha1` is 40 lowercase hex; `sha256` is
`sha256:<64 lowercase hex>`; and `strict_utc` is an RFC 3339 UTC instant ending
in `Z`. Every array is ordered, duplicate-free, and bytewise canonical unless
the type says otherwise.

```yaml
schema_version: "test-health-nested-type-catalog/v1"
catalog_id: "TDD-NESTED-TYPES-1.1"
additional_properties: false
freshness_values: ["CURRENT", "STALE", "NOT_ASSESSED"]
change_profile_contract:
  profile_count: 6
  profiles:
    BEHAVIOR_CHANGE:
      no_refactor_needed_false: ["RED", "GREEN", "REFACTOR", "ARCHITECTURE_CHECK"]
      no_refactor_needed_true: ["RED", "GREEN", "ARCHITECTURE_CHECK"]
      required_exception_class: null
    DEFECT_FIX:
      no_refactor_needed_false: ["RED", "GREEN", "REFACTOR", "ARCHITECTURE_CHECK"]
      no_refactor_needed_true: ["RED", "GREEN", "ARCHITECTURE_CHECK"]
      required_exception_class: null
    REFACTOR_ONLY:
      no_refactor_needed_false: ["BASELINE_GREEN", "REFACTOR", "ARCHITECTURE_CHECK"]
      no_refactor_needed_true: null
      required_exception_class: null
    GENERATED_OUTPUT:
      no_refactor_needed_false: ["GENERATE", "VALIDATE", "ARCHITECTURE_CHECK"]
      no_refactor_needed_true: null
      required_exception_class: "GENERATED_OUTPUT"
    EMERGENCY_CONTAINMENT:
      no_refactor_needed_false: ["EMERGENCY_FIX", "VALIDATE", "ARCHITECTURE_CHECK"]
      no_refactor_needed_true: null
      required_exception_class: "EMERGENCY_CONTAINMENT"
    NON_EXECUTABLE_DOCUMENTATION:
      no_refactor_needed_false: ["DOCUMENTATION_CHECK", "ARCHITECTURE_CHECK"]
      no_refactor_needed_true: null
      required_exception_class: "NON_EXECUTABLE_DOCUMENTATION"
  invariants:
    - "the containing steps equal exactly one selected sequence with contiguous sequence values starting at 1"
    - "a nonnull required_exception_class resolves exactly one active current exact-cycle-subject TddExceptionRecordV1 of that class"
    - "a profile with no no_refactor_needed_true sequence rejects no_refactor_needed true"
    - "no omitted, additional, duplicate, empty, or synthesized phase is legal"
landing_record_status_authority:
  authority_id: "LANDING-RECORD-STATUS-1.0"
  allowed_values: ["SUCCEEDED"]
  success_literal: "SUCCEEDED"
  schema_rule: "LandingRecord.status is required, nonnull, and const SUCCEEDED; failed, cancelled, nonterminal, or outcome-unknown attempts use their governed execution/effect records and cannot masquerade as a LandingRecord."
  consumer_rule: "Every LandingRecord schema, template, resolver, and acceptance join imports this literal; no consumer-local synonym is permitted."
cycle_landing_receipt_contract:
  contract_id: "TDD-CYCLE-LANDING-RECEIPT-1.0"
  cycle_schema_ref: "schemas/common/tdd-cycle-record-v1.schema.json"
  landing_schema_ref: "schemas/execution/landing-record-v1.schema.json"
  landing_status_authority_ref: "LANDING-RECORD-STATUS-1.0"
  pre_landing_statuses: ["PROPOSED", "GATED", "REJECTED"]
  gated_result: "PASS"
  derived_status: "ACCEPTED"
  prohibited_cycle_fields: ["landing_record_ref", "accepted_at", "landed_commit"]
  required_bindings:
    - "LandingRecord.subject_schema == tdd-cycle-subject/v1"
    - "LandingRecord.subject_ref == TddCycleRecordV1.exact_subject_ref"
    - "LandingRecord.subject_digest == TddCycleRecordV1.exact_subject_digest"
    - "LandingRecord.candidate_commit == commit_sha1(TddCycleRecordV1.candidate_subject)"
    - "LandingRecord.status == SUCCEEDED"
    - "LandingRecord.started_at >= TddCycleRecordV1.gated_at"
  invariants:
    - "a GATED cycle is not accepted without one separately produced eligible LandingRecord"
    - "the cycle producer cannot issue, embed, update, or backdate the LandingRecord"
    - "a LandingRecord does not rewrite cycle bytes, checker results, journal facts, gate result, or gated_at"
    - "zero, duplicate, failed, stale, wrong-subject, wrong-candidate, pre-gate, or future receipts derive no accepted status"
  fixture_requirements:
    valid_join: 1
    prohibited_cycle_field_negative: 3
    missing_receipt_negative: 1
    duplicate_receipt_negative: 1
    failed_receipt_negative: 1
    stale_receipt_negative: 1
    wrong_subject_schema_negative: 1
    wrong_subject_ref_negative: 1
    wrong_subject_digest_negative: 1
    wrong_candidate_negative: 1
    pre_gate_time_negative: 1
    wrong_legacy_landed_literal_negative: 1
    null_status_negative: 1
    unknown_status_negative: 1
    nonterminal_status_negative: 1
    exact_case_count: 17
types:
  - type_id: "TypedArtifactRefV1"
    type_version: "1.0.0"
    fields: ["artifact_type", "artifact_ref", "artifact_digest"]
    field_types:
      artifact_type: {enum: ["evidence_snapshot", "checker_result", "gate_evaluation", "human_decision", "review_verdict"]}
      artifact_ref: "safe_id"
      artifact_digest: "sha256"
    cardinality: {artifact_type: "1", artifact_ref: "1", artifact_digest: "1"}
    invariants:
      - "artifact_ref equals the resolved artifact's per-kind ID"
      - "artifact_digest equals both the resolved digest field and RFC8785 SHA-256 of canonical artifact bytes excluding digest"

  - type_id: "SubjectBindingV1"
    type_version: "1.0.0"
    fields: ["subject_schema", "subject_ref", "subject_digest"]
    field_types:
      subject_schema: "nonempty_versioned_schema_id"
      subject_ref: "safe_id_or_registered_urn"
      subject_digest: "sha256"
    cardinality: {subject_schema: "1", subject_ref: "1", subject_digest: "1"}
    invariants:
      - "subject_ref resolves through the canonical subject registry"
      - "subject_digest equals RFC8785 SHA-256 of the resolved subject bytes"
      - "resolved bytes validate against subject_schema"

  - type_id: "TddSubjectTransitionEdgeV1"
    type_version: "1.0.0"
    fields: ["edge_sequence", "from_subject", "to_subject", "to_step_kind", "relation", "digest"]
    field_types:
      edge_sequence: {integer: {minimum: 1, maximum: 4}}
      from_subject: "SubjectBindingV1"
      to_subject: "SubjectBindingV1"
      to_step_kind: {enum: ["RED", "GREEN", "BASELINE_GREEN", "REFACTOR", "GENERATE", "VALIDATE", "EMERGENCY_FIX", "DOCUMENTATION_CHECK", "ARCHITECTURE_CHECK"]}
      relation: {enum: ["SOURCE_CHANGE", "VALIDATION_ONLY"]}
      digest: "sha256"
    cardinality: {edge_sequence: "1", from_subject: "1", to_subject: "1", to_step_kind: "1", relation: "1", digest: "1"}
    invariants:
      - "digest is RFC8785 SHA-256 of the complete edge excluding digest"
      - "SOURCE_CHANGE requires unequal subject digests and registered causal source ancestry with no unbound intermediate write"
      - "VALIDATION_ONLY requires identical from_subject and to_subject and cannot conceal a source, fixture, rule, profile, or environment change"

  - type_id: "TddSubjectTransitionManifestV1"
    type_version: "1.0.0"
    fields: ["manifest_id", "base_subject", "step_subjects", "candidate_subject", "edges", "digest"]
    field_types:
      manifest_id: "safe_id"
      base_subject: "SubjectBindingV1"
      step_subjects: "SubjectBindingV1[]"
      candidate_subject: "SubjectBindingV1"
      edges: "TddSubjectTransitionEdgeV1[]"
      digest: "sha256"
    cardinality: {manifest_id: "1", base_subject: "1", step_subjects: "1..4", candidate_subject: "1", edges: "1..4", digest: "1"}
    invariants:
      - "step_subjects and edges are ordered by containing step sequence, overriding the default bytewise array order, and their counts equal the containing steps count"
      - "base_subject equals the containing cycle base_subject; step_subjects equal the containing step subjects in order; candidate_subject equals both the containing candidate_subject and final ARCHITECTURE_CHECK subject"
      - "edge 1 starts at base_subject, every edge target equals its step_subject, and each later edge starts at the prior edge target"
      - "edge_sequence is contiguous from 1 and to_step_kind equals the corresponding containing step_kind"
      - "digest is RFC8785 SHA-256 of the complete manifest excluding digest"

  - type_id: "ExpectedFailureFingerprintV1"
    type_version: "1.0.0"
    fields: ["stable_test_id", "criterion_id", "failure_denominator_row_id", "failure_denominator_row_digest", "matcher_schema", "matcher_ref", "matcher_digest", "expected_failure_code", "harness_failure_exclusion"]
    field_types:
      stable_test_id: "safe_id"
      criterion_id: "safe_id"
      failure_denominator_row_id: "safe_id"
      failure_denominator_row_digest: "sha256"
      matcher_schema: "nonempty_versioned_schema_id"
      matcher_ref: "safe_id_or_registered_urn"
      matcher_digest: "sha256"
      expected_failure_code: "safe_id"
      harness_failure_exclusion: {const: true}
    cardinality: {stable_test_id: "1", criterion_id: "1", failure_denominator_row_id: "1", failure_denominator_row_digest: "1", matcher_schema: "1", matcher_ref: "1", matcher_digest: "1", expected_failure_code: "1", harness_failure_exclusion: "1"}
    invariants:
      - "stable_test_id and criterion_id resolve in the cycle test-denominator manifest"
      - "failure_denominator_row_id resolves exactly once in the cycle failure-denominator manifest and its RFC8785 SHA-256 equals failure_denominator_row_digest"
      - "matcher_ref resolves immutable bytes validating matcher_schema and hashing to matcher_digest"
      - "the matcher is a closed structural predicate over qualified checker outcome and raw artifacts, not an unbounded prose or substring assertion"
      - "the checker failure_code equals expected_failure_code and the resolved matcher accepts the observed assertion failure"
      - "ERROR, TIMEOUT, CANCELLATION, HARNESS_FAILURE, launch failure, missing result, or a failure from another stable_test_id or criterion_id never satisfies the fingerprint"

  - type_id: "TddCycleJournalBindingV1"
    type_version: "1.0.0"
    fields: ["run_id", "journal_ref", "journal_start_sequence", "journal_end_sequence", "phase_activity_ids", "phase_activity_manifest_digest", "journal_manifest_digest"]
    field_types:
      run_id: "safe_id"
      journal_ref: "safe_id_or_registered_urn"
      journal_start_sequence: "uint"
      journal_end_sequence: "uint"
      phase_activity_ids: "safe_id[]"
      phase_activity_manifest_digest: "sha256"
      journal_manifest_digest: "sha256"
    cardinality: {run_id: "1", journal_ref: "1", journal_start_sequence: "1", journal_end_sequence: "1", phase_activity_ids: "1..4", phase_activity_manifest_digest: "1", journal_manifest_digest: "1"}
    invariants:
      - "journal_start_sequence is at or before journal_end_sequence and both resolve in one append-only governed run journal"
      - "phase_activity_ids are distinct and ordered by containing step sequence, overriding the default bytewise array order"
      - "there is exactly one phase activity for every containing cycle step and no activity is shared with another cycle"
      - "the journal slice contains each phase activity's request, dispatch when applicable, resolution, and checker/evidence binding in causal order; cycle gate evaluation follows the closed slice"
      - "the slice excludes the cycle-level EvidenceSnapshot, GateEvaluation, LandingRecord, and any fact whose subject digest depends on the containing cycle exact subject"
      - "phase_activity_manifest_digest binds the ordered activity/event/fact references and journal_manifest_digest binds the complete immutable slice"

  - type_id: "ArchitectureRuleCoverageV1"
    type_version: "1.0.0"
    fields: ["rule_registry_id", "rule_registry_version", "rule_registry_digest", "applicable_rule_ids", "not_applicable_rule_ids", "coverage_manifest_digest"]
    field_types:
      rule_registry_id: "safe_id"
      rule_registry_version: "semver"
      rule_registry_digest: "sha256"
      applicable_rule_ids: "safe_id[]"
      not_applicable_rule_ids: "safe_id[]"
      coverage_manifest_digest: "sha256"
    cardinality: {rule_registry_id: "1", rule_registry_version: "1", rule_registry_digest: "1", applicable_rule_ids: "1..N", not_applicable_rule_ids: "0..N", coverage_manifest_digest: "1"}
    invariants:
      - "applicable_rule_ids and not_applicable_rule_ids are disjoint, sorted, duplicate-free, and their union equals the complete bound rule registry"
      - "coverage_manifest_digest is RFC8785 SHA-256 of one ordered APPLICABLE or NOT_APPLICABLE row per registry rule"
      - "every NOT_APPLICABLE row has one current exact-subject ArchitectureRuleNotApplicableProofV1 in the containing architecture_rule_not_applicable_proofs"
      - "the architecture-check checker coverage equals applicable_rule_ids exactly and reports each rule independently"
      - "a registry digest change makes the coverage and cycle stale"

  - type_id: "ArchitectureRuleNotApplicableProofV1"
    type_version: "1.0.0"
    fields: ["rule_id", "proof_ref"]
    field_types:
      rule_id: "safe_id"
      proof_ref: "TypedArtifactRefV1"
    cardinality: {rule_id: "1", proof_ref: "1"}
    invariants:
      - "rule_id occurs exactly once in the containing architecture_rule_coverage.not_applicable_rule_ids"
      - "proof_ref resolves a current eligible artifact bound to TDD_CYCLE_SUBJECT_V1 whose coverage names rule_id and proves its registered N/A rule"
      - "proof_ref cannot be the containing cycle, an inline assertion, or a maker-only self-approval"

  - type_id: "OracleProvenanceV1"
    type_version: "1.0.0"
    fields: ["oracle_source_schema", "oracle_source_ref", "oracle_source_digest", "authority_basis_id", "independence_class"]
    field_types:
      oracle_source_schema: "nonempty_versioned_schema_id"
      oracle_source_ref: "safe_id_or_registered_urn"
      oracle_source_digest: "sha256"
      authority_basis_id: "safe_id"
      independence_class: {enum: ["INDEPENDENT_PRIMARY", "INDEPENDENT_SECONDARY", "DERIVED_WITH_INDEPENDENT_REVIEW"]}
    cardinality: {oracle_source_schema: "1", oracle_source_ref: "1", oracle_source_digest: "1", authority_basis_id: "1", independence_class: "1"}
    invariants:
      - "the source resolves immutable bytes validating oracle_source_schema and hashing to oracle_source_digest"
      - "authority_basis_id resolves the requirement, acceptance, risk, invariant, contract, or incident authority for the expected result"
      - "the oracle is not computed solely from the production implementation under test or a snapshot blessed only by the same change"
      - "DERIVED_WITH_INDEPENDENT_REVIEW requires an eligible review artifact in the containing cycle evidence snapshot"

  - type_id: "ReproducibilityEnvelopeV1"
    type_version: "1.0.0"
    fields: ["tier", "seed_manifest_digest", "input_manifest_digest", "rule_version_manifest_digest", "journal_capture_policy_digest", "image_digest", "toolchain_manifest_digest", "network_policy_digest", "filesystem_policy_digest", "dependency_lock_digest", "execution_capability_profile_digest"]
    field_types:
      tier: {enum: ["TIER_1", "TIER_2"]}
      seed_manifest_digest: "sha256"
      input_manifest_digest: "sha256"
      rule_version_manifest_digest: "sha256"
      journal_capture_policy_digest: "sha256"
      image_digest: "sha256|null"
      toolchain_manifest_digest: "sha256|null"
      network_policy_digest: "sha256|null"
      filesystem_policy_digest: "sha256|null"
      dependency_lock_digest: "sha256|null"
      execution_capability_profile_digest: "sha256|null"
    cardinality: {tier: "1", seed_manifest_digest: "1", input_manifest_digest: "1", rule_version_manifest_digest: "1", journal_capture_policy_digest: "1", image_digest: "0..1", toolchain_manifest_digest: "0..1", network_policy_digest: "0..1", filesystem_policy_digest: "0..1", dependency_lock_digest: "0..1", execution_capability_profile_digest: "0..1"}
    invariants:
      - "Tier 1 requires the four base manifests and all six Tier-2-only fields null"
      - "Tier 2 requires all fields nonnull"
      - "tier is selected by the applicable policy before the first phase activity and equals the journal declaration"
      - "a failed Tier 1 run may recommend a new Tier 2 cycle but cannot rewrite or upgrade the original envelope"
      - "high-risk, seam, quarantine, security, migration, recovery, and release-bearing lanes require Tier 2"

  - type_id: "TddCycleStepV1"
    type_version: "1.1.0"
    fields: ["step_kind", "sequence", "step_subject", "step_snapshot_digest", "checker_result_ref", "expected_outcome", "expected_failure_fingerprint", "started_at", "finished_at"]
    field_types:
      step_kind: {enum: ["RED", "GREEN", "BASELINE_GREEN", "REFACTOR", "GENERATE", "VALIDATE", "EMERGENCY_FIX", "DOCUMENTATION_CHECK", "ARCHITECTURE_CHECK"]}
      sequence: {integer: {minimum: 1, maximum: 4}}
      step_subject: "SubjectBindingV1"
      step_snapshot_digest: "sha256"
      checker_result_ref: "TypedArtifactRefV1"
      expected_outcome: {enum: ["EXPECTED_FAILURE", "PASS"]}
      expected_failure_fingerprint: "ExpectedFailureFingerprintV1|null"
      started_at: "strict_utc"
      finished_at: "strict_utc"
    cardinality: {step_kind: "1", sequence: "1", step_subject: "1", step_snapshot_digest: "1", checker_result_ref: "1", expected_outcome: "1", expected_failure_fingerprint: "0..1", started_at: "1", finished_at: "1"}
    invariants:
      - "step_snapshot_digest equals step_subject.subject_digest"
      - "checker_result_ref.artifact_type is checker_result and resolves to step_subject"
      - "started_at is strictly before finished_at"
      - "RED has EXPECTED_FAILURE and one nonnull ExpectedFailureFingerprintV1"
      - "every non-RED step has PASS and null expected_failure_fingerprint"
      - "the containing cycle steps use the exact declared profile sequence with contiguous sequence values starting at 1 and no duplicate step kind"
      - "ARCHITECTURE_CHECK step_subject equals the containing cycle candidate_subject"

  - type_id: "RiskTraceDispositionV1"
    type_version: "1.0.0"
    fields: ["disposition_id", "risk_id", "subject", "status", "rationale", "evidence_refs", "authority_ref", "freshness_status", "observed_at", "expires_at"]
    field_types:
      disposition_id: "safe_id"
      risk_id: "safe_id"
      subject: "SubjectBindingV1"
      status: {enum: ["MITIGATED", "ACCEPTED_RESIDUAL", "NOT_APPLICABLE", "UNKNOWN", "FAILED"]}
      rationale: "nonempty_string"
      evidence_refs: "TypedArtifactRefV1[]"
      authority_ref: "TypedArtifactRefV1|null"
      freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
      observed_at: "strict_utc"
      expires_at: "strict_utc|null"
    cardinality: {disposition_id: "1", risk_id: "1", subject: "1", status: "1", rationale: "1", evidence_refs: "0..N", authority_ref: "0..1", freshness_status: "1", observed_at: "1", expires_at: "0..1"}
    invariants:
      - "MITIGATED requires CURRENT and one or more typed evidence_refs"
      - "ACCEPTED_RESIDUAL or NOT_APPLICABLE requires CURRENT, one or more evidence_refs, and authority_ref.artifact_type human_decision resolving APPROVED for this subject"
      - "UNKNOWN has null authority_ref and is blocking"
      - "FAILED is blocking and requires one or more evidence_refs"
      - "STALE or NOT_ASSESSED is blocking regardless of status"
      - "when expires_at is nonnull, observed_at is strictly before expires_at and evaluation occurs before expires_at"

  - type_id: "RequirementTraceDispositionV1"
    type_version: "1.0.0"
    fields: ["disposition_id", "requirement_id", "subject", "status", "rationale", "successor_test_ids", "evidence_refs", "authority_ref", "freshness_status", "observed_at", "expires_at"]
    field_types:
      disposition_id: "safe_id"
      requirement_id: "safe_id"
      subject: "SubjectBindingV1"
      status: {enum: ["PRESERVED_BY_SUCCESSOR", "NO_LONGER_REQUIRED_OR_APPLICABLE", "UNKNOWN", "FAILED"]}
      rationale: "nonempty_string"
      successor_test_ids: "safe_id[]"
      evidence_refs: "TypedArtifactRefV1[]"
      authority_ref: "TypedArtifactRefV1|null"
      freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
      observed_at: "strict_utc"
      expires_at: "strict_utc|null"
    cardinality: {disposition_id: "1", requirement_id: "1", subject: "1", status: "1", rationale: "1", successor_test_ids: "0..N", evidence_refs: "0..N", authority_ref: "0..1", freshness_status: "1", observed_at: "1", expires_at: "0..1"}
    invariants:
      - "PRESERVED_BY_SUCCESSOR requires CURRENT, one or more successor_test_ids, one or more evidence_refs, and null authority_ref"
      - "NO_LONGER_REQUIRED_OR_APPLICABLE requires CURRENT, zero successor_test_ids, one or more evidence_refs, and an APPROVED human_decision authority_ref"
      - "UNKNOWN or FAILED is blocking; UNKNOWN has null authority_ref"
      - "STALE or NOT_ASSESSED is blocking regardless of status"

  - type_id: "ExternalObligationDispositionV1"
    type_version: "1.0.0"
    fields: ["disposition_id", "obligation_id", "obligation_registry_ref", "subject", "status", "rationale", "evidence_refs", "authority_ref", "freshness_status", "observed_at", "expires_at"]
    field_types:
      disposition_id: "safe_id"
      obligation_id: "safe_id"
      obligation_registry_ref: "nonempty_string"
      subject: "SubjectBindingV1"
      status: {enum: ["SATISFIED_BY_ALTERNATE_EVIDENCE", "NOT_APPLICABLE", "UNKNOWN", "FAILED"]}
      rationale: "nonempty_string"
      evidence_refs: "TypedArtifactRefV1[]"
      authority_ref: "TypedArtifactRefV1|null"
      freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
      observed_at: "strict_utc"
      expires_at: "strict_utc|null"
    cardinality: {disposition_id: "1", obligation_id: "1", obligation_registry_ref: "1", subject: "1", status: "1", rationale: "1", evidence_refs: "0..N", authority_ref: "0..1", freshness_status: "1", observed_at: "1", expires_at: "0..1"}
    invariants:
      - "SATISFIED_BY_ALTERNATE_EVIDENCE requires CURRENT and one or more evidence_refs"
      - "NOT_APPLICABLE requires CURRENT, one or more evidence_refs, and an APPROVED human_decision authority_ref whose scope names the obligation"
      - "UNKNOWN or FAILED is blocking; UNKNOWN has null authority_ref"
      - "no exception may set an external obligation to SATISFIED or NOT_APPLICABLE by self-assertion"

  - type_id: "ObservedOutcomeCountsV1"
    type_version: "1.0.0"
    fields: ["passed", "failed", "errored", "timed_out", "cancelled", "harness_failed"]
    field_types:
      passed: "uint"
      failed: "uint"
      errored: "uint"
      timed_out: "uint"
      cancelled: "uint"
      harness_failed: "uint"
    cardinality: {passed: "1", failed: "1", errored: "1", timed_out: "1", cancelled: "1", harness_failed: "1"}
    invariants: ["sum of all six counts equals the containing attempt_count"]

  - type_id: "FailureSignatureCountV1"
    type_version: "1.0.0"
    fields: ["failure_class", "signature_digest", "count"]
    field_types:
      failure_class: {enum: ["ASSERTION_FAILURE", "ERROR", "TIMEOUT", "CANCELLATION", "HARNESS_FAILURE"]}
      signature_digest: "sha256"
      count: {integer: {minimum: 1}}
    cardinality: {failure_class: "1", signature_digest: "1", count: "1"}
    invariants: ["failure_class plus signature_digest is unique within one distribution"]

  - type_id: "ObservedFailureDistributionV1"
    type_version: "1.0.0"
    fields: ["distribution_id", "subject", "sample_policy_id", "sample_policy_version", "attempt_count", "attempt_manifest_digest", "outcome_counts", "failure_signatures", "status", "rationale", "producer_service_id", "qualification_id", "evidence_refs", "freshness_status", "window_started_at", "window_finished_at"]
    field_types:
      distribution_id: "safe_id"
      subject: "SubjectBindingV1"
      sample_policy_id: "safe_id"
      sample_policy_version: "semver"
      attempt_count: {integer: {minimum: 2}}
      attempt_manifest_digest: "sha256"
      outcome_counts: "ObservedOutcomeCountsV1"
      failure_signatures: "FailureSignatureCountV1[]"
      status: {enum: ["FLAKY_PROVEN", "CONSISTENT_FAILURE", "HARNESS_FAULT", "INSUFFICIENT_SAMPLE"]}
      rationale: "nonempty_string"
      producer_service_id: "safe_id"
      qualification_id: "safe_id"
      evidence_refs: "TypedArtifactRefV1[]"
      freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
      window_started_at: "strict_utc"
      window_finished_at: "strict_utc"
    cardinality: {distribution_id: "1", subject: "1", sample_policy_id: "1", sample_policy_version: "1", attempt_count: "1", attempt_manifest_digest: "1", outcome_counts: "1", failure_signatures: "1..N", status: "1", rationale: "1", producer_service_id: "1", qualification_id: "1", evidence_refs: "2..N", freshness_status: "1", window_started_at: "1", window_finished_at: "1"}
    invariants:
      - "every evidence_ref has artifact_type checker_result, is unique, resolves to subject, and the complete ordered set hashes to attempt_manifest_digest"
      - "evidence_refs count equals attempt_count and their outcomes exactly reproduce outcome_counts and failure_signatures"
      - "window_started_at is at or before every attempt start and every attempt finish is at or before window_finished_at"
      - "FLAKY_PROVEN requires CURRENT, at least one passed and at least one failed/errored/timed_out/cancelled, and zero harness_failed"
      - "CONSISTENT_FAILURE requires CURRENT, zero passed, one or more non-harness failures, and zero harness_failed"
      - "HARNESS_FAULT requires one or more harness_failed and cannot support quarantine or PASS"
      - "INSUFFICIENT_SAMPLE, STALE, or NOT_ASSESSED is blocking"
      - "retries preserve all attempts; no selected final attempt replaces this distribution"

  - type_id: "TestRowV1"
    type_version: "1.0.0"
    fields: ["path", "mode", "git_blob_oid_sha1", "content_sha256", "stable_test_id", "marker_count"]
    field_types:
      path: "safe_path"
      mode: {enum: ["100644", "100755"]}
      git_blob_oid_sha1: "sha1"
      content_sha256: "sha256_without_prefix"
      stable_test_id: "safe_id"
      marker_count: {const: 1}
    cardinality: {path: "1", mode: "1", git_blob_oid_sha1: "1", content_sha256: "1", stable_test_id: "1", marker_count: "1"}
    invariants:
      - "path is a canonical test .py path under one ADR-0008 test root"
      - "Git blob bytes recompute both digests and contain exactly one line '# ranex-test-id: <stable_test_id>'"

  - type_id: "LegacyBaselineSourceRowV1"
    type_version: "1.0.0"
    fields: ["path", "mode", "git_blob_oid_sha1", "content_sha256"]
    field_types: {path: "safe_path", mode: {enum: ["100644", "100755"]}, git_blob_oid_sha1: "sha1", content_sha256: "sha256_without_prefix"}
    cardinality: {path: "1", mode: "1", git_blob_oid_sha1: "1", content_sha256: "1"}
    invariants: ["row equals the immutable ADR-0010 baseline source row and Git blob bytes"]

  - type_id: "LegacyCurrentSourceRowV1"
    type_version: "1.0.0"
    fields: ["path", "mode", "content_sha256"]
    field_types: {path: "safe_path", mode: {enum: ["100644", "100755"]}, content_sha256: "sha256_without_prefix"}
    cardinality: {path: "1", mode: "1", content_sha256: "1"}
    invariants: ["row equals the authorized ADR-0010 event-time current source row and before-commit Git bytes"]

  - type_id: "RetirementDispositionV1"
    type_version: "1.0.0"
    fields: ["disposition_id", "subject", "status", "rationale", "successor_test_ids", "successor_evidence_refs", "no_longer_applicable_decision_ref", "no_longer_applicable_evidence_refs", "freshness_status", "decided_at"]
    field_types:
      disposition_id: "safe_id"
      subject: "SubjectBindingV1"
      status: {enum: ["SUCCESSOR_TESTS", "NO_LONGER_REQUIRED_OR_APPLICABLE"]}
      rationale: "nonempty_string"
      successor_test_ids: "safe_id[]"
      successor_evidence_refs: "TypedArtifactRefV1[]"
      no_longer_applicable_decision_ref: "TypedArtifactRefV1|null"
      no_longer_applicable_evidence_refs: "TypedArtifactRefV1[]"
      freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
      decided_at: "strict_utc"
    cardinality: {disposition_id: "1", subject: "1", status: "1", rationale: "1", successor_test_ids: "0..N", successor_evidence_refs: "0..N", no_longer_applicable_decision_ref: "0..1", no_longer_applicable_evidence_refs: "0..N", freshness_status: "1", decided_at: "1"}
    invariants:
      - "SUCCESSOR_TESTS requires CURRENT, one or more distinct successor_test_ids, one or more successor_evidence_refs, and null/empty no-longer-applicable fields"
      - "NO_LONGER_REQUIRED_OR_APPLICABLE requires CURRENT, zero successor fields, one or more no_longer_applicable_evidence_refs, and an APPROVED human_decision no_longer_applicable_decision_ref"
      - "all typed references resolve to the containing TEST_DELETION_SUBJECT_V1"
      - "STALE or NOT_ASSESSED blocks acceptance"

top_level_record_types:
  - type_id: "TddCycleRecordV1"
    type_version: "1.1.0"
    additional_properties: false
    fields: ["schema_version", "record_type", "cycle_id", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "work_item_id", "task_packet_id", "task_packet_digest", "change_profile", "no_refactor_needed", "base_subject", "candidate_subject", "subject_transition_manifest", "steps", "cycle_journal_binding", "test_denominator_manifest_digest", "failure_denominator_manifest_digest", "architecture_rule_coverage", "architecture_rule_not_applicable_proofs", "oracle_provenance", "reproducibility_envelope", "built_artifact_digest", "built_artifact_evidence_ref", "release_profile_id", "release_profile_version", "release_profile_digest", "tdd_exception_ids", "quarantine_ids", "evidence_snapshot_ref", "cycle_gate_evaluation_ref", "exact_subject_ref", "exact_subject_digest", "gated_at", "recorded_at", "result", "status"]
    field_types:
      schema_version: {const: "1"}
      record_type: {const: "TDD_CYCLE_RECORD_V1"}
      cycle_id: "safe_id"
      policy_id: {const: "RANEX-TDD-1.0"}
      policy_version: {const: "1.0.0"}
      test_practice_profile_id: "safe_id"
      test_practice_profile_version: "semver"
      test_practice_profile_digest: "sha256"
      work_item_id: "safe_id"
      task_packet_id: "safe_id"
      task_packet_digest: "sha256"
      change_profile: {enum: ["BEHAVIOR_CHANGE", "DEFECT_FIX", "REFACTOR_ONLY", "GENERATED_OUTPUT", "EMERGENCY_CONTAINMENT", "NON_EXECUTABLE_DOCUMENTATION"]}
      no_refactor_needed: {enum: [true, false]}
      base_subject: "SubjectBindingV1"
      candidate_subject: "SubjectBindingV1"
      subject_transition_manifest: "TddSubjectTransitionManifestV1"
      steps: "TddCycleStepV1[]"
      cycle_journal_binding: "TddCycleJournalBindingV1"
      test_denominator_manifest_digest: "sha256"
      failure_denominator_manifest_digest: "sha256"
      architecture_rule_coverage: "ArchitectureRuleCoverageV1"
      architecture_rule_not_applicable_proofs: "ArchitectureRuleNotApplicableProofV1[]"
      oracle_provenance: "OracleProvenanceV1|null"
      reproducibility_envelope: "ReproducibilityEnvelopeV1"
      built_artifact_digest: "sha256|null"
      built_artifact_evidence_ref: "TypedArtifactRefV1|null"
      release_profile_id: "safe_id|null"
      release_profile_version: "semver|null"
      release_profile_digest: "sha256|null"
      tdd_exception_ids: "safe_id[]"
      quarantine_ids: "safe_id[]"
      evidence_snapshot_ref: "TypedArtifactRefV1|null"
      cycle_gate_evaluation_ref: "TypedArtifactRefV1|null"
      exact_subject_ref: "safe_id_or_registered_urn"
      exact_subject_digest: "sha256"
      gated_at: "strict_utc|null"
      recorded_at: "strict_utc"
      result: {enum: ["PASS", "FAIL", "UNKNOWN"]}
      status: {enum: ["PROPOSED", "GATED", "REJECTED"]}
    cardinality: {schema_version: "1", record_type: "1", cycle_id: "1", policy_id: "1", policy_version: "1", test_practice_profile_id: "1", test_practice_profile_version: "1", test_practice_profile_digest: "1", work_item_id: "1", task_packet_id: "1", task_packet_digest: "1", change_profile: "1", no_refactor_needed: "1", base_subject: "1", candidate_subject: "1", subject_transition_manifest: "1", steps: "1..4", cycle_journal_binding: "1", test_denominator_manifest_digest: "1", failure_denominator_manifest_digest: "1", architecture_rule_coverage: "1", architecture_rule_not_applicable_proofs: "0..N", oracle_provenance: "0..1", reproducibility_envelope: "1", built_artifact_digest: "0..1", built_artifact_evidence_ref: "0..1", release_profile_id: "0..1", release_profile_version: "0..1", release_profile_digest: "0..1", tdd_exception_ids: "0..N", quarantine_ids: "0..N", evidence_snapshot_ref: "0..1", cycle_gate_evaluation_ref: "0..1", exact_subject_ref: "1", exact_subject_digest: "1", gated_at: "0..1", recorded_at: "1", result: "1", status: "1"}
    invariants:
      - "base_subject differs from candidate_subject and subject_transition_manifest exactly binds base, every adjacent step subject/relation, and final candidate with no unbound intermediate write"
      - "steps equal the exact change-profile sequence; BEHAVIOR_CHANGE or DEFECT_FIX may omit only REFACTOR when no_refactor_needed is true, and every other profile requires no_refactor_needed false"
      - "no_refactor_needed true requires the GREEN subject equal candidate_subject, the final ARCHITECTURE_CHECK be VALIDATION_ONLY on that subject, and TDD-PROFILE-001 independently pass"
      - "cycle_journal_binding contains exactly one ordered activity per step and the final ARCHITECTURE_CHECK step_subject equals candidate_subject"
      - "RED-bearing profiles require nonnull oracle_provenance; Tier 2 always requires nonnull oracle_provenance"
      - "architecture_rule_not_applicable_proofs map every architecture_rule_coverage NOT_APPLICABLE ID to exactly one eligible exact-cycle-subject proof and contain no extra or duplicate rule ID"
      - "architecture-check checker coverage equals architecture_rule_coverage.applicable_rule_ids and every row passes independently"
      - "built_artifact_digest, built_artifact_evidence_ref, and the release-profile triple are all nonnull for every build- or release-bearing profile and all-null only when an active exact-subject exception explicitly proves no build applies"
      - "a nonnull built_artifact_digest is the one build-once candidate digest for every gate-bearing lane"
      - "GATED requires result PASS, nonnull evidence_snapshot_ref, cycle_gate_evaluation_ref, and gated_at, with every referenced artifact eligible and no blocking exception, quarantine, or unknown"
      - "GATED requires the journal slice finish before cycle evidence/gate evaluation and the resolved GateEvaluation.evaluated_at <= gated_at <= recorded_at"
      - "PROPOSED requires result UNKNOWN and null evidence_snapshot_ref, cycle_gate_evaluation_ref, and gated_at; REJECTED requires null gated_at and cannot carry result PASS"
      - "the record contains no landing ID or post-landing time; derived ACCEPTED requires a separate eligible LandingRecord bound to TDD_CYCLE_SUBJECT_V1"

  - type_id: "TddExceptionRecordV1"
    type_version: "1.0.0"
    additional_properties: false
    fields: ["schema_version", "record_type", "exception_id", "exception_class", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "applicable_cycle_ids", "subject_schema", "subject_ref", "subject_digest", "exact_paths", "behavior_ids", "skipped_steps", "risk_trace_dispositions", "external_obligation_dispositions", "alternate_evidence_refs", "owner_id", "owner_decision_ref", "work_item_id", "backfill_work_item_id", "created_at", "expires_at", "backfill_criteria", "removal_criteria", "closure_evidence_refs", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]
    field_types:
      schema_version: {const: "1"}
      record_type: {const: "TDD_EXCEPTION_RECORD_V1"}
      exception_id: "safe_id"
      exception_class: {enum: ["GENERATED_OUTPUT", "EMERGENCY_CONTAINMENT", "NON_EXECUTABLE_DOCUMENTATION"]}
      policy_id: {const: "RANEX-TDD-1.0"}
      policy_version: {const: "1.0.0"}
      test_practice_profile_id: "safe_id"
      test_practice_profile_version: "semver"
      test_practice_profile_digest: "sha256"
      applicable_cycle_ids: "safe_id[]"
      subject_schema: "nonempty_versioned_schema_id"
      subject_ref: "safe_id_or_registered_urn"
      subject_digest: "sha256"
      exact_paths: "safe_path[]"
      behavior_ids: "safe_id[]"
      skipped_steps: {array_items_enum: ["RED", "GREEN", "REFACTOR", "ARCHITECTURE_CHECK"]}
      risk_trace_dispositions: "RiskTraceDispositionV1[]"
      external_obligation_dispositions: "ExternalObligationDispositionV1[]"
      alternate_evidence_refs: "TypedArtifactRefV1[]"
      owner_id: "safe_id"
      owner_decision_ref: "TypedArtifactRefV1|null"
      work_item_id: "safe_id"
      backfill_work_item_id: "safe_id|null"
      created_at: "strict_utc"
      expires_at: "strict_utc"
      backfill_criteria: "nonempty_string"
      removal_criteria: "nonempty_string"
      closure_evidence_refs: "TypedArtifactRefV1[]"
      landing_record_ref: "safe_id"
      exact_subject_ref: "safe_id_or_registered_urn"
      exact_subject_digest: "sha256"
      accepted_at: "strict_utc|null"
      recorded_at: "strict_utc"
      status: {enum: ["PROPOSED", "ACTIVE", "CLOSED", "REVOKED", "EXPIRED"]}
    cardinality: {schema_version: "1", record_type: "1", exception_id: "1", exception_class: "1", policy_id: "1", policy_version: "1", test_practice_profile_id: "1", test_practice_profile_version: "1", test_practice_profile_digest: "1", applicable_cycle_ids: "1..N", subject_schema: "1", subject_ref: "1", subject_digest: "1", exact_paths: "1..N", behavior_ids: "1..N", skipped_steps: "1..4", risk_trace_dispositions: "1..N", external_obligation_dispositions: "0..N", alternate_evidence_refs: "1..N", owner_id: "1", owner_decision_ref: "0..1", work_item_id: "1", backfill_work_item_id: "0..1", created_at: "1", expires_at: "1", backfill_criteria: "1", removal_criteria: "1", closure_evidence_refs: "0..N", landing_record_ref: "1", exact_subject_ref: "1", exact_subject_digest: "1", accepted_at: "0..1", recorded_at: "1", status: "1"}
    invariants:
      - "created_at < expires_at and all applicable cycles resolve the same subject/profile tuple named by this record"
      - "ACTIVE requires current owner_decision_ref, landing_record_ref, accepted_at, alternate evidence, and complete risk/external-obligation dispositions"
      - "CLOSED requires one or more closure_evidence_refs and governed removal of the active source/profile projection"
      - "REVOKED or EXPIRED grants no substitution; PROPOSED has null accepted_at"

  - type_id: "TestQuarantineRecordV1"
    type_version: "1.0.0"
    additional_properties: false
    fields: ["schema_version", "record_type", "quarantine_id", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "base_subject", "candidate_subject", "built_artifact_digest", "release_profile_id", "release_profile_version", "release_profile_digest", "affected_test_ids", "affected_paths", "observed_attempt_refs", "observed_failure_distribution", "affected_gate_ids", "risk_trace_dispositions", "alternate_evidence_refs", "owner_id", "owner_decision_ref", "work_item_id", "opened_at", "expires_at", "removal_criteria", "restoration_backfill_evidence_refs", "quarantine_evidence_snapshot_ref", "quarantine_checker_result_refs", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]
    field_types:
      schema_version: {const: "1"}
      record_type: {const: "TEST_QUARANTINE_RECORD_V1"}
      quarantine_id: "safe_id"
      policy_id: {const: "RANEX-TDD-1.0"}
      policy_version: {const: "1.0.0"}
      test_practice_profile_id: "safe_id"
      test_practice_profile_version: "semver"
      test_practice_profile_digest: "sha256"
      base_subject: "SubjectBindingV1"
      candidate_subject: "SubjectBindingV1"
      built_artifact_digest: "sha256|null"
      release_profile_id: "safe_id"
      release_profile_version: "semver"
      release_profile_digest: "sha256"
      affected_test_ids: "safe_id[]"
      affected_paths: "safe_path[]"
      observed_attempt_refs: "TypedArtifactRefV1[]"
      observed_failure_distribution: "ObservedFailureDistributionV1"
      affected_gate_ids: "safe_id[]"
      risk_trace_dispositions: "RiskTraceDispositionV1[]"
      alternate_evidence_refs: "TypedArtifactRefV1[]"
      owner_id: "safe_id"
      owner_decision_ref: "TypedArtifactRefV1|null"
      work_item_id: "safe_id"
      opened_at: "strict_utc"
      expires_at: "strict_utc"
      removal_criteria: "nonempty_string"
      restoration_backfill_evidence_refs: "TypedArtifactRefV1[]"
      quarantine_evidence_snapshot_ref: "TypedArtifactRefV1|null"
      quarantine_checker_result_refs: "TypedArtifactRefV1[]"
      landing_record_ref: "safe_id"
      exact_subject_ref: "safe_id_or_registered_urn"
      exact_subject_digest: "sha256"
      accepted_at: "strict_utc|null"
      recorded_at: "strict_utc"
      status: {enum: ["PROPOSED", "ACTIVE", "CLOSED", "REVOKED", "EXPIRED"]}
    cardinality: {schema_version: "1", record_type: "1", quarantine_id: "1", policy_id: "1", policy_version: "1", test_practice_profile_id: "1", test_practice_profile_version: "1", test_practice_profile_digest: "1", base_subject: "1", candidate_subject: "1", built_artifact_digest: "0..1", release_profile_id: "1", release_profile_version: "1", release_profile_digest: "1", affected_test_ids: "1..N", affected_paths: "1..N", observed_attempt_refs: "2..N", observed_failure_distribution: "1", affected_gate_ids: "0..N", risk_trace_dispositions: "1..N", alternate_evidence_refs: "0..N", owner_id: "1", owner_decision_ref: "0..1", work_item_id: "1", opened_at: "1", expires_at: "1", removal_criteria: "1", restoration_backfill_evidence_refs: "0..N", quarantine_evidence_snapshot_ref: "0..1", quarantine_checker_result_refs: "1..N", landing_record_ref: "1", exact_subject_ref: "1", exact_subject_digest: "1", accepted_at: "0..1", recorded_at: "1", status: "1"}
    invariants:
      - "base_subject differs from candidate_subject; observed attempts execute that exact transition and optional built_artifact_digest"
      - "opened_at < expires_at and observed_failure_distribution exactly reconciles observed_attempt_refs"
      - "ACTIVE requires FLAKY_PROVEN, current owner_decision_ref, quarantine evidence/checkers, landing_record_ref, and accepted_at before expires_at"
      - "CLOSED requires current restoration_backfill_evidence_refs and governed removal; REVOKED or EXPIRED grants nothing"

  - type_id: "TestDeletionRecordV1"
    type_version: "1.0.0"
    additional_properties: false
    fields: ["schema_version", "record_type", "deletion_id", "target_kind", "policy_id", "policy_version", "tdd_rule_set_id", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "profile_freshness_status", "stable_test_id", "source_migration_proof_ids", "affected_scope_id", "legacy_baseline_source_row", "legacy_current_source_row", "legacy_source_state_kind", "source_change_exception_id", "closes_change_exception_id", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_test_row", "after_test_row", "tests_delta_manifest_digest", "requirement_trace_dispositions", "risk_trace_dispositions", "reason", "fixture_cleanup_refs", "snapshot_cleanup_refs", "test_data_cleanup_refs", "removal_checker_result_refs", "retirement_evidence_snapshot_ref", "retirement_gate_evaluation_ref", "retirement_disposition", "owner_id", "owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_review_ref", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "resulting_gap_status", "result", "status"]
    field_types:
      schema_version: {const: "1"}
      record_type: {const: "TEST_DELETION_RECORD_V1"}
      deletion_id: "safe_id"
      target_kind: {enum: ["LEGACY_SOURCE", "CANONICAL_TEST"]}
      policy_id: {const: "RANEX-TEST-DELETION-1.0"}
      policy_version: {const: "1.0.0"}
      tdd_rule_set_id: {const: "RANEX-TDD-1.0"}
      test_practice_profile_id: "safe_id"
      test_practice_profile_version: "semver"
      test_practice_profile_digest: "sha256"
      profile_freshness_status: {enum: ["CURRENT", "STALE", "NOT_ASSESSED"]}
      stable_test_id: "safe_id|null"
      source_migration_proof_ids: "safe_id[]"
      affected_scope_id: "safe_id"
      legacy_baseline_source_row: "LegacyBaselineSourceRowV1|null"
      legacy_current_source_row: "LegacyCurrentSourceRowV1|null"
      legacy_source_state_kind: {enum_or_null: ["IMMUTABLE_BASELINE", "AUTHORIZED_CHANGE_EXCEPTION"]}
      source_change_exception_id: "safe_id|null"
      closes_change_exception_id: "safe_id|null"
      before_commit_sha1: "sha1"
      after_commit_sha1: "sha1"
      before_tests_tree_oid_sha1: "sha1"
      after_tests_tree_oid_sha1: "sha1"
      before_tests_snapshot_digest: "sha256"
      after_tests_snapshot_digest: "sha256"
      before_test_row: "TestRowV1|null"
      after_test_row: "TestRowV1|null"
      tests_delta_manifest_digest: "sha256"
      requirement_trace_dispositions: "RequirementTraceDispositionV1[]"
      risk_trace_dispositions: "RiskTraceDispositionV1[]"
      reason: "nonempty_string"
      fixture_cleanup_refs: "TypedArtifactRefV1[]"
      snapshot_cleanup_refs: "TypedArtifactRefV1[]"
      test_data_cleanup_refs: "TypedArtifactRefV1[]"
      removal_checker_result_refs: "TypedArtifactRefV1[]"
      retirement_evidence_snapshot_ref: "TypedArtifactRefV1"
      retirement_gate_evaluation_ref: "TypedArtifactRefV1"
      retirement_disposition: "RetirementDispositionV1"
      owner_id: "safe_id"
      owner_acceptance_ref: "TypedArtifactRefV1"
      process_assurance_owner_acceptance_ref: "TypedArtifactRefV1"
      independent_review_ref: "TypedArtifactRefV1"
      landing_record_ref: "safe_id"
      exact_subject_ref: "safe_id_or_registered_urn"
      exact_subject_digest: "sha256"
      accepted_at: "strict_utc|null"
      recorded_at: "strict_utc"
      resulting_gap_status: {enum: ["NONE", "UNKNOWN", "GAP"]}
      result: {enum: ["PASS", "FAIL", "UNKNOWN"]}
      status: {enum: ["PROPOSED", "ACCEPTED", "REJECTED"]}
    cardinality: {schema_version: "1", record_type: "1", deletion_id: "1", target_kind: "1", policy_id: "1", policy_version: "1", tdd_rule_set_id: "1", test_practice_profile_id: "1", test_practice_profile_version: "1", test_practice_profile_digest: "1", profile_freshness_status: "1", stable_test_id: "0..1", source_migration_proof_ids: "0..N", affected_scope_id: "1", legacy_baseline_source_row: "0..1", legacy_current_source_row: "0..1", legacy_source_state_kind: "0..1", source_change_exception_id: "0..1", closes_change_exception_id: "0..1", before_commit_sha1: "1", after_commit_sha1: "1", before_tests_tree_oid_sha1: "1", after_tests_tree_oid_sha1: "1", before_tests_snapshot_digest: "1", after_tests_snapshot_digest: "1", before_test_row: "0..1", after_test_row: "0..1", tests_delta_manifest_digest: "1", requirement_trace_dispositions: "1..N", risk_trace_dispositions: "1..N", reason: "1", fixture_cleanup_refs: "0..N", snapshot_cleanup_refs: "0..N", test_data_cleanup_refs: "0..N", removal_checker_result_refs: "1..N", retirement_evidence_snapshot_ref: "1", retirement_gate_evaluation_ref: "1", retirement_disposition: "1", owner_id: "1", owner_acceptance_ref: "1", process_assurance_owner_acceptance_ref: "1", independent_review_ref: "1", landing_record_ref: "1", exact_subject_ref: "1", exact_subject_digest: "1", accepted_at: "0..1", recorded_at: "1", resulting_gap_status: "1", result: "1", status: "1"}
    invariants:
      - "before_commit_sha1 is the direct parent of after_commit_sha1 and every Git tree/blob/delta digest recomputes"
      - "target_kind branch fields satisfy record_cross_field_invariants and no retired ID is reused"
      - "ACCEPTED requires CURRENT, resulting_gap_status NONE, result PASS, nonnull landing_record_ref and accepted_at, and every typed artifact eligible"
      - "PROPOSED has null accepted_at; REJECTED cannot carry result PASS"

artifact_resolvers:
  - artifact_type: "checker_result"
    schema_path: "schemas/assurance/checker-result-v1.schema.json"
    artifact_id_pointer: "/checker_result_id"
    digest_pointer: "/digest"
    subject_pointers: {subject_schema: "/subject_schema", subject_ref: "/subject_ref", subject_digest: "/subject_digest"}
    producer_pointers: {producer_id: "/checker/checker_id", producer_version: "/checker/checker_version", code_digest: "/checker/code_digest", fixture_digest: "/checker/fixture_suite_digest", qualification_id: "/checker/qualification_id"}
    time_pointers: {started_at: "/started_at", finished_at: "/finished_at", expires_at: null}
    eligibility:
      - "checker registry row, version, code digest, fixture digest, qualification, route, and isolation profile are current"
      - "status is COMPLETED; outcome and failure_code equal the exact reference-role expectation"
      - "started_at is strictly before finished_at and profile freshness TTL has not elapsed"
      - "coverage contains every role-required claim and no limitation invalidates one"

  - artifact_type: "evidence_snapshot"
    schema_path: "schemas/assurance/evidence-snapshot-v1.schema.json"
    artifact_id_pointer: "/snapshot_id"
    digest_pointer: "/digest"
    subject_pointers: {subject_schema: "/subject_schema", subject_ref: "/subject_ref", subject_digest: "/subject_digest"}
    producer_pointers: {producer_id: "/created_by_service_id", qualification_id: "/created_by_service_id"}
    time_pointers: {issued_at: "/created_at", freshness_cutoff: "/freshness_cutoff", expires_at: null}
    eligibility:
      - "producer is the registered assurance evidence-snapshot service"
      - "required_claim_ids exactly equal the role denominator; missing_claim_ids and conflicts are empty"
      - "every required eligible evidence item is observed no earlier than freshness_cutoff and remains current"

  - artifact_type: "gate_evaluation"
    schema_path: "schemas/assurance/gate-evaluation-v1.schema.json"
    artifact_id_pointer: "/gate_evaluation_id"
    digest_pointer: "/digest"
    subject_pointers: {subject_schema: "/subject_schema", subject_ref: "/subject_ref", subject_digest: "/subject_digest"}
    producer_pointers: {producer_id: "/evaluator_id", producer_version: "/evaluator_version", code_digest: "/evaluator_code_digest", qualification_id: "/qualification_id"}
    time_pointers: {issued_at: "/evaluated_at", expires_at: null}
    eligibility:
      - "evaluator registry row/version/code/qualification and gate definition are current"
      - "outcome is PASS; required_claim_ids and observed_claim_ids are equal sets; missing_claim_ids and conflicts are empty"
      - "bound evidence_snapshot_id/digest resolves to an eligible same-subject snapshot"
      - "profile freshness TTL has not elapsed"

  - artifact_type: "human_decision"
    schema_path: "schemas/authority/human-decision-v1.schema.json"
    artifact_id_pointer: "/decision_id"
    digest_pointer: "/digest"
    subject_pointers: {subject_schema: "/subject/subject_schema", subject_ref: "/subject/subject_ref", subject_digest: "/subject/subject_digest"}
    producer_pointers: {producer_id: "/principal_id", authentication_context_id: "/authentication_context_id", challenge_digest: "/presentation_challenge_digest"}
    time_pointers: {issued_at: "/issued_at", expires_at: "/expires_at", revoked_at: "/revoked_at"}
    eligibility:
      - "principal is authenticated and has the exact role/action/scope authority at issued_at and evaluation time"
      - "status is APPROVED, outcome is the role-required approval, issued_at is at or before evaluation time and evaluation time is strictly before expires_at"
      - "revoked_at is null; supersession, policy change, or subject drift makes the decision ineligible"

  - artifact_type: "review_verdict"
    schema_path: "schemas/review/review-verdict-v1.schema.json"
    artifact_id_pointer: "/verdict_id"
    digest_pointer: "/digest"
    subject_pointers: {subject_schema: "/subject_schema", subject_ref: "/subject_ref", subject_digest: "/subject_digest"}
    producer_pointers: {producer_id: "/producer_service_id", independence_evaluation_id: "/independence_evaluation_id"}
    time_pointers: {issued_at: "/produced_at", expires_at: null}
    eligibility:
      - "producer is the registered review application service and not the maker"
      - "independence_evaluation_id resolves to PASS for the exact maker/reviewer/subject"
      - "verdict is ACCEPTABLE and no open_finding_ref resolves to a blocking finding"
      - "profile review-freshness TTL has not elapsed and no finding/evidence was invalidated"

subject_projection_contract:
  contract_id: "TDD-CANONICAL-SUBJECT-PROJECTIONS-1.1"
  canonicalization: "RFC8785"
  digest_algorithm: "SHA-256"
  digest_encoding: "sha256:<64 lowercase hex>"
  projection_rule:
    - "construct exactly the declared output_fields from canonical source-record values and transforms"
    - "retain declared nulls; sequence arrays retain their type-declared order, while set-like arrays remain bytewise sorted and duplicate-free"
    - "reject a missing/extra field, unresolved subject, noncanonical value, or source field not classified exactly once"
    - "RFC8785-canonicalize the projection object, then SHA-256 those bytes"
    - "record exact_subject_ref must equal the derived subject_ref and exact_subject_digest must equal the computed digest"
    - "artifact/evidence/decision/gate/review/landing refs and lifecycle/result metadata are excluded to prevent circular authorization"
  output_type_rule:
    subject_schema: "required const equal to the projection row subject_schema"
    subject_ref: "required registered_urn equal to the projection row subject_ref_rule"
    direct_field: "required key with the exact field type and value cardinality from source_record_type, including an explicit null where that source type is nullable"
    transformed_field: "required key with the row's output_type and output_cardinality"
    additional_properties: false
  canonicalization_example:
    projection_object: {subject_schema: "example/v1", subject_ref: "urn:ranex:example:x", value: 1}
    canonical_utf8: "{\"subject_ref\":\"urn:ranex:example:x\",\"subject_schema\":\"example/v1\",\"value\":1}"
    expected_digest: "sha256:a29aa78ecb67189a323179b6d1edcca8def27be3f7a40b4fbb76103b126496fd"
  nested_projection_types:
    TddCycleStepClaimV1:
      additional_properties: false
      fields: ["step_kind", "sequence", "step_subject", "step_snapshot_digest", "expected_outcome", "expected_failure_fingerprint", "started_at", "finished_at"]
      source_fields: ["step_kind", "sequence", "step_subject", "step_snapshot_digest", "expected_outcome", "expected_failure_fingerprint", "started_at", "finished_at"]
      excluded_source_fields: ["checker_result_ref"]
      invariant: "the source TddCycleStepV1 field set is partitioned exactly between source_fields and excluded_source_fields"
  projections:
    - projection_id: "TDD_CYCLE_SUBJECT_V1"
      subject_schema: "tdd-cycle-subject/v1"
      schema_ref: "schemas/common/tdd-cycle-subject-v1.schema.json"
      source_record_type: "TddCycleRecordV1"
      subject_ref_rule: "urn:ranex:tdd-cycle-subject:<cycle_id>"
      output_fields: ["subject_schema", "subject_ref", "cycle_id", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "work_item_id", "task_packet_id", "task_packet_digest", "change_profile", "no_refactor_needed", "base_subject", "candidate_subject", "subject_transition_manifest", "step_claims", "cycle_journal_binding", "test_denominator_manifest_digest", "failure_denominator_manifest_digest", "architecture_rule_coverage", "oracle_provenance", "reproducibility_envelope", "built_artifact_digest", "release_profile_id", "release_profile_version", "release_profile_digest", "tdd_exception_ids", "quarantine_ids"]
      direct_included_source_fields: ["cycle_id", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "work_item_id", "task_packet_id", "task_packet_digest", "change_profile", "no_refactor_needed", "base_subject", "candidate_subject", "subject_transition_manifest", "cycle_journal_binding", "test_denominator_manifest_digest", "failure_denominator_manifest_digest", "architecture_rule_coverage", "oracle_provenance", "reproducibility_envelope", "built_artifact_digest", "release_profile_id", "release_profile_version", "release_profile_digest", "tdd_exception_ids", "quarantine_ids"]
      transformed_source_fields:
        step_claims:
          sources: ["steps"]
          transform: "project every source step through TddCycleStepClaimV1 in contiguous sequence order"
          output_type: "TddCycleStepClaimV1[]"
          output_cardinality: "1..4"
      excluded_source_fields: ["schema_version", "record_type", "architecture_rule_not_applicable_proofs", "built_artifact_evidence_ref", "evidence_snapshot_ref", "cycle_gate_evaluation_ref", "exact_subject_ref", "exact_subject_digest", "gated_at", "recorded_at", "result", "status"]

    - projection_id: "TDD_EXCEPTION_SUBJECT_V1"
      subject_schema: "tdd-exception-subject/v1"
      schema_ref: "schemas/common/tdd-exception-subject-v1.schema.json"
      source_record_type: "TddExceptionRecordV1"
      subject_ref_rule: "urn:ranex:tdd-exception-subject:<exception_id>"
      output_fields: ["subject_schema", "subject_ref", "exception_id", "exception_class", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "applicable_cycle_ids", "exception_target", "exact_paths", "behavior_ids", "skipped_steps", "owner_id", "work_item_id", "backfill_work_item_id", "created_at", "expires_at", "backfill_criteria", "removal_criteria"]
      direct_included_source_fields: ["exception_id", "exception_class", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "applicable_cycle_ids", "exact_paths", "behavior_ids", "skipped_steps", "owner_id", "work_item_id", "backfill_work_item_id", "created_at", "expires_at", "backfill_criteria", "removal_criteria"]
      transformed_source_fields:
        exception_target:
          sources: ["subject_schema", "subject_ref", "subject_digest"]
          transform: "construct one closed SubjectBindingV1"
          output_type: "SubjectBindingV1"
          output_cardinality: "1"
      excluded_source_fields: ["schema_version", "record_type", "risk_trace_dispositions", "external_obligation_dispositions", "alternate_evidence_refs", "owner_decision_ref", "closure_evidence_refs", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]

    - projection_id: "TEST_QUARANTINE_SUBJECT_V1"
      subject_schema: "test-quarantine-subject/v1"
      schema_ref: "schemas/common/test-quarantine-subject-v1.schema.json"
      source_record_type: "TestQuarantineRecordV1"
      subject_ref_rule: "urn:ranex:test-quarantine-subject:<quarantine_id>"
      output_fields: ["subject_schema", "subject_ref", "quarantine_id", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "base_subject", "candidate_subject", "built_artifact_digest", "release_profile_id", "release_profile_version", "release_profile_digest", "affected_test_ids", "affected_paths", "affected_gate_ids", "owner_id", "work_item_id", "opened_at", "expires_at", "removal_criteria"]
      direct_included_source_fields: ["quarantine_id", "policy_id", "policy_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "base_subject", "candidate_subject", "built_artifact_digest", "release_profile_id", "release_profile_version", "release_profile_digest", "affected_test_ids", "affected_paths", "affected_gate_ids", "owner_id", "work_item_id", "opened_at", "expires_at", "removal_criteria"]
      transformed_source_fields: {}
      excluded_source_fields: ["schema_version", "record_type", "observed_attempt_refs", "observed_failure_distribution", "risk_trace_dispositions", "alternate_evidence_refs", "owner_decision_ref", "restoration_backfill_evidence_refs", "quarantine_evidence_snapshot_ref", "quarantine_checker_result_refs", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "status"]

    - projection_id: "TEST_DELETION_SUBJECT_V1"
      subject_schema: "test-deletion-subject/v1"
      schema_ref: "schemas/common/test-deletion-subject-v1.schema.json"
      source_record_type: "TestDeletionRecordV1"
      subject_ref_rule: "urn:ranex:test-deletion-subject:<deletion_id>"
      output_fields: ["subject_schema", "subject_ref", "deletion_id", "target_kind", "policy_id", "policy_version", "tdd_rule_set_id", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "profile_freshness_status", "stable_test_id", "source_migration_proof_ids", "affected_scope_id", "legacy_baseline_source_row", "legacy_current_source_row", "legacy_source_state_kind", "source_change_exception_id", "closes_change_exception_id", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_test_row", "after_test_row", "tests_delta_manifest_digest", "reason", "owner_id"]
      direct_included_source_fields: ["deletion_id", "target_kind", "policy_id", "policy_version", "tdd_rule_set_id", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "profile_freshness_status", "stable_test_id", "source_migration_proof_ids", "affected_scope_id", "legacy_baseline_source_row", "legacy_current_source_row", "legacy_source_state_kind", "source_change_exception_id", "closes_change_exception_id", "before_commit_sha1", "after_commit_sha1", "before_tests_tree_oid_sha1", "after_tests_tree_oid_sha1", "before_tests_snapshot_digest", "after_tests_snapshot_digest", "before_test_row", "after_test_row", "tests_delta_manifest_digest", "reason", "owner_id"]
      transformed_source_fields: {}
      excluded_source_fields: ["schema_version", "record_type", "requirement_trace_dispositions", "risk_trace_dispositions", "fixture_cleanup_refs", "snapshot_cleanup_refs", "test_data_cleanup_refs", "removal_checker_result_refs", "retirement_evidence_snapshot_ref", "retirement_gate_evaluation_ref", "retirement_disposition", "owner_acceptance_ref", "process_assurance_owner_acceptance_ref", "independent_review_ref", "landing_record_ref", "exact_subject_ref", "exact_subject_digest", "accepted_at", "recorded_at", "resulting_gap_status", "result", "status"]
  fixture_requirements:
    projection_ids: ["TDD_CYCLE_SUBJECT_V1", "TDD_EXCEPTION_SUBJECT_V1", "TEST_QUARANTINE_SUBJECT_V1", "TEST_DELETION_SUBJECT_V1"]
    per_projection:
      - "one complete positive record with independently stored projection bytes and expected digest"
      - "one source-key-order permutation that produces identical projection bytes/digest"
      - "one mutation of every included or transformed leaf that changes the digest"
      - "one mutation of every excluded evidence/lifecycle field that leaves the digest unchanged but still undergoes its separate eligibility validation"
      - "one injected circular artifact/decision/landing reference rejected as an extra projection field"
      - "one mismatched exact_subject_ref and one mismatched exact_subject_digest rejection"
    validator_requirement: "recompute from the canonical source record; never trust stored projection bytes or digest"

checker_result_dual_subject_contract:
  contract_id: "CHECKER-CLAIM-EXECUTION-SUBJECT-1.1"
  reference_path_expansion: "The compiler recursively expands each typed record field through record_field_bindings and the closed nested types; 'every TypedArtifactRefV1 path' means that finite emitted JSON-Pointer set, never an untyped string search or runtime heuristic."
  checker_result_top_level_additional_properties: false
  checker_result_top_level_fields: ["schema_version", "artifact_type", "checker_result_id", "core_sdlc_trace_ref", "checker", "subject_schema", "subject_ref", "subject_digest", "subject", "status", "outcome", "failure_code", "failure_fingerprint", "applicability_proof_ref", "evidence_refs", "raw_artifact_refs", "coverage", "limitations", "started_at", "finished_at", "digest"]
  top_level_claim_fields:
    subject_schema: {type: "nonempty_versioned_schema_id", cardinality: "1"}
    subject_ref: {type: "safe_id_or_registered_urn", cardinality: "1"}
    subject_digest: {type: "sha256", cardinality: "1"}
  failure_fingerprint_field:
    path: "/failure_fingerprint"
    type: "ExpectedFailureFingerprintV1|null"
    cardinality: "0..1"
    red_rule: "nonnull and exactly equal to the containing RED step expected_failure_fingerprint"
    non_red_rule: "null"
  execution_subject_path: "/subject"
  execution_subject_schema_ref: "schemas/assurance/checker-execution-subject-v1.schema.json"
  execution_subject_additional_properties: false
  execution_subject_required_fields: ["subject_schema", "project_id", "work_item_id", "run_id", "activity_id", "effect_id", "workspace_id", "repository_id", "repository_uri_digest", "base_commit", "candidate_commit", "artifact_digest", "packet_id", "packet_digest", "workflow_definition_id", "workflow_definition_digest", "workflow_interpreter_version", "policy_activation_id", "policy_activation_manifest_digest", "policy_decision_digest", "module_profile_id", "module_profile_digest", "capability_grant_digest", "route_lock_id", "schema_registry_version", "expected_run_aggregate_version", "test_practice_profile_id", "test_practice_profile_version", "test_practice_profile_digest", "release_profile_id", "release_profile_version", "release_profile_digest"]
  execution_fields:
    base_commit: {type: "sha1", cardinality: "1"}
    candidate_commit: {type: "sha1", cardinality: "1"}
    artifact_digest: {type: "sha256|null", cardinality: "0..1"}
    test_practice_profile_id: {type: "safe_id", cardinality: "1"}
    test_practice_profile_version: {type: "semver", cardinality: "1"}
    test_practice_profile_digest: {type: "sha256", cardinality: "1"}
    release_profile_id: {type: "safe_id|null", cardinality: "0..1"}
    release_profile_version: {type: "semver|null", cardinality: "0..1"}
    release_profile_digest: {type: "sha256|null", cardinality: "0..1"}
  commit_resolver: "SubjectBindingV1 must resolve a registered immutable Git subject whose exact commit_sha1 pointer is declared by its subject-schema registry row"
  global_invariants:
    - "the top-level claim tuple equals the role claim_subject below"
    - "the nested execution tuple equals every role predicate below; a correct claim over a different execution tuple is ineligible"
    - "all three test-practice-profile fields equal the containing record"
    - "release-profile fields are all null or all nonnull and exact"
    - "checker qualification binds both top-level claim fields and every nested execution field"
    - "a RED step is eligible only when outcome EXPECTED_FAILURE, failure_code and failure_fingerprint exactly equal ExpectedFailureFingerprintV1, the canonical matcher accepts the observed raw artifact, and no harness/error/timeout/cancellation outcome is present"
    - "an ARCHITECTURE_CHECK step is eligible only when checker coverage equals architecture_rule_coverage.applicable_rule_ids exactly and every listed rule independently passes"
  role_predicates:
    - role_id: "TDD_CYCLE_STEP_CHECKER"
      record_type: "TddCycleRecordV1"
      reference_paths: ["/steps/*/checker_result_ref"]
      claim_subject: "the referenced step's step_subject"
      execution_base_commit: "commit_sha1(base_subject)"
      execution_candidate_commit: "commit_sha1(the referenced step's step_subject)"
      execution_artifact_digest: null
      execution_test_profile: "record test_practice_profile_id/version/digest"
      execution_release_profile: "record all-null or all-nonnull release_profile_id/version/digest"

    - role_id: "TDD_CYCLE_BUILT_ARTIFACT_CHECKER"
      record_type: "TddCycleRecordV1"
      reference_paths: ["/built_artifact_evidence_ref when artifact_type=checker_result"]
      claim_subject: "candidate_subject"
      execution_base_commit: "commit_sha1(base_subject)"
      execution_candidate_commit: "commit_sha1(candidate_subject)"
      execution_artifact_digest: "built_artifact_digest"
      execution_test_profile: "record test_practice_profile_id/version/digest"
      execution_release_profile: "record release_profile_id/version/digest"

    - role_id: "TDD_EXCEPTION_CHECKER"
      record_type: "TddExceptionRecordV1"
      reference_paths: ["every TypedArtifactRefV1 path when artifact_type=checker_result"]
      claim_subject: "TDD_EXCEPTION_SUBJECT_V1 exact_subject_ref/exact_subject_digest"
      execution_base_commit: "the identical base commit resolved from every applicable_cycle_id"
      execution_candidate_commit: "the identical candidate commit resolved from every applicable_cycle_id and exception_target"
      execution_artifact_digest: "the identical built_artifact_digest resolved from every applicable cycle, or null only when the exception class declares no build"
      execution_test_profile: "record test_practice_profile_id/version/digest"
      execution_release_profile: "the identical release profile resolved from every applicable cycle"

    - role_id: "TEST_QUARANTINE_ATTEMPT_CHECKER"
      record_type: "TestQuarantineRecordV1"
      reference_paths: ["/observed_attempt_refs/*"]
      claim_subject: "candidate_subject"
      execution_base_commit: "commit_sha1(base_subject)"
      execution_candidate_commit: "commit_sha1(candidate_subject)"
      execution_artifact_digest: "built_artifact_digest"
      execution_test_profile: "record test_practice_profile_id/version/digest"
      execution_release_profile: "record release_profile_id/version/digest"

    - role_id: "TEST_QUARANTINE_CONTROL_CHECKER"
      record_type: "TestQuarantineRecordV1"
      reference_paths: ["every other TypedArtifactRefV1 path when artifact_type=checker_result"]
      claim_subject: "TEST_QUARANTINE_SUBJECT_V1 exact_subject_ref/exact_subject_digest"
      execution_base_commit: "commit_sha1(base_subject)"
      execution_candidate_commit: "commit_sha1(candidate_subject)"
      execution_artifact_digest: "built_artifact_digest"
      execution_test_profile: "record test_practice_profile_id/version/digest"
      execution_release_profile: "record release_profile_id/version/digest"

    - role_id: "TEST_DELETION_CHECKER"
      record_type: "TestDeletionRecordV1"
      reference_paths: ["every TypedArtifactRefV1 path when artifact_type=checker_result"]
      claim_subject: "TEST_DELETION_SUBJECT_V1 exact_subject_ref/exact_subject_digest"
      execution_base_commit: "before_commit_sha1"
      execution_candidate_commit: "after_commit_sha1"
      execution_artifact_digest: null
      execution_test_profile: "record test_practice_profile_id/version/digest"
      execution_release_profile: null
  negative_fixture_requirements:
    - "for every role, one valid dual-subject checker result"
    - "for every role, independently forge claim schema, claim ref, claim digest, base commit, candidate commit, artifact digest, test-profile ID/version/digest, and each nonnull release-profile field"
    - "for the TDD_CYCLE_STEP_CHECKER role, independently omit or forge each RED failure_fingerprint field, inject it into every non-RED step result, and prove rejection"
    - "for every role, swap a checker result from another valid record/cycle with the same outcome and prove rejection"
    - "for exception multi-cycle roles, vary one cycle's base/candidate/artifact/release profile and prove the exception ineligible"
    - "no fixture may change two dimensions at once or stop at JSON-schema validation when testing semantic binding"

reference_subject_roles:
  - {record_type: "TddCycleRecordV1", reference_role: "steps[*].checker_result_ref", expected_subject: "the containing TddCycleStepV1.step_subject"}
  - {record_type: "TddCycleRecordV1", reference_role: "built_artifact_evidence_ref", expected_subject: "candidate_subject"}
  - {record_type: "TddCycleRecordV1", reference_role: "architecture_rule_not_applicable_proofs[*].proof_ref|evidence_snapshot_ref|cycle_gate_evaluation_ref", expected_subject: "TDD_CYCLE_SUBJECT_V1 at exact_subject_ref/exact_subject_digest"}
  - {record_type: "TddExceptionRecordV1", reference_role: "all TypedArtifactRefV1 fields", expected_subject: "TDD_EXCEPTION_SUBJECT_V1 at exact_subject_ref/exact_subject_digest"}
  - {record_type: "TestQuarantineRecordV1", reference_role: "observed_attempt_refs", expected_subject: "candidate_subject"}
  - {record_type: "TestQuarantineRecordV1", reference_role: "all other TypedArtifactRefV1 fields", expected_subject: "TEST_QUARANTINE_SUBJECT_V1 at exact_subject_ref/exact_subject_digest"}
  - {record_type: "TestDeletionRecordV1", reference_role: "all TypedArtifactRefV1 fields including those inside RetirementDispositionV1", expected_subject: "TEST_DELETION_SUBJECT_V1 at exact_subject_ref/exact_subject_digest"}

record_field_bindings:
  - {record_type: "TddCycleRecordV1", fields: {base_subject: "SubjectBindingV1", candidate_subject: "SubjectBindingV1", subject_transition_manifest: "TddSubjectTransitionManifestV1", steps: "TddCycleStepV1[1..4]", cycle_journal_binding: "TddCycleJournalBindingV1", architecture_rule_coverage: "ArchitectureRuleCoverageV1", architecture_rule_not_applicable_proofs: "ArchitectureRuleNotApplicableProofV1[0..N]", oracle_provenance: "OracleProvenanceV1|null", reproducibility_envelope: "ReproducibilityEnvelopeV1"}}
  - {record_type: "TddExceptionRecordV1", fields: {risk_trace_dispositions: "RiskTraceDispositionV1[1..N]", external_obligation_dispositions: "ExternalObligationDispositionV1[0..N]"}}
  - {record_type: "TestQuarantineRecordV1", fields: {base_subject: "SubjectBindingV1", candidate_subject: "SubjectBindingV1", observed_attempt_refs: "TypedArtifactRefV1[2..N]", observed_failure_distribution: "ObservedFailureDistributionV1", risk_trace_dispositions: "RiskTraceDispositionV1[1..N]"}}
  - {record_type: "TestDeletionRecordV1", fields: {legacy_baseline_source_row: "LegacyBaselineSourceRowV1|null", legacy_current_source_row: "LegacyCurrentSourceRowV1|null", before_test_row: "TestRowV1|null", after_test_row: "TestRowV1|null", requirement_trace_dispositions: "RequirementTraceDispositionV1[1..N]", risk_trace_dispositions: "RiskTraceDispositionV1[1..N]", retirement_disposition: "RetirementDispositionV1"}}

record_cross_field_invariants:
  - "All disposition arrays are complete against their bound denominator manifest and contain exactly one row per registered ID."
  - "All nested subjects equal their containing role's expected subject; no nested object may self-authorize."
  - "TestQuarantineRecordV1 observed_attempt_refs exactly equal ObservedFailureDistributionV1.evidence_refs in order and digest."
  - "For TestDeletionRecordV1 target_kind CANONICAL_TEST: stable_test_id is nonnull, legacy rows and legacy source/exception fields are null, before_test_row is nonnull with the same stable_test_id, and after_test_row is null."
  - "For TestDeletionRecordV1 target_kind LEGACY_SOURCE: stable_test_id and both test rows are null, both legacy rows are nonnull for one identical path, and ADR-0010 source-state/exception rules apply."
  - "RetirementDispositionV1 is the sole successor/NLA branch; TestDeletionRecordV1 has no duplicate top-level successor or no-longer-applicable fields."
  - "Every exact_paths, behavior_ids, affected_test_ids, affected_gate_ids, criterion-ID, cleanup-ref, typed-ref, exception-ID, quarantine-ID, and migration-proof array is complete, bytewise sorted, and duplicate-free; 0..N is permitted only where the bound denominator proves zero applicable rows."
```

For exception, quarantine, and deletion records, `landing_record_ref` is
always a preallocated opaque `landing_<uuidv7>` string resolved through the
canonical `LandingRecord` service, never a path or typed evidence substitute.
The pre-landing `TddCycleRecordV1` deliberately has no such field; its
post-landing receipt is a separately resolved `LandingRecord` whose subject is
the cycle subject. All safe record IDs are globally claimed through the
authoritative artifact/landing registry and never reused. `recorded_at` and Git
commit times are metadata. For an accepted or derived-accepted instance,
evidence/check/review finishes before any required decision, which precedes
`LandingRecord.started_at <= LandingRecord.finished_at <=
validation_observed_at`; the named validation commit descends the landed
candidate and the committed source/registry bytes match. A lifecycle-specific
expiry adds an earlier upper bound. Staged, unstaged, untracked, noncausal,
chronology-inverted, or byte/digest-mismatched state cannot authorize.

`TddCycleRecordV1` binds `RANEX-TDD-1.0`, the exact profile ID/version/digest,
task packet and work item, change profile, base and candidate subjects, ordered
profile-specific step claims, exact journal slice, test/failure denominators,
complete architecture-rule coverage, oracle/reproducibility declarations,
optional build/release tuple, exception IDs, typed step/check/snapshot/gate
artifacts, chronology, and derived result. Its canonical
`TDD_CYCLE_SUBJECT_V1` excludes artifact references so those artifacts can all
bind the same precomputed subject without circularity. A cycle is
`PROPOSED -> GATED | REJECTED`; only the derived join of a `GATED` cycle and
one separately produced eligible `LandingRecord` may support an accepted
runtime TDD result.

`TddExceptionRecordV1` binds `RANEX-TDD-1.0`, one of exactly
`GENERATED_OUTPUT`, `EMERGENCY_CONTAINMENT`, or
`NON_EXECUTABLE_DOCUMENTATION`, the exact cycle/subject, paths and behavior,
skipped steps, risk and external-obligation disposition, alternative proof,
accountable role, work/backfill item, creation/expiry, backfill/removal
criteria, and typed evidence/decision references. Its logical lifecycle is
`PROPOSED -> ACTIVE -> CLOSED | REVOKED | EXPIRED`. Only a canonical,
successfully landed, current, nonexpired `ACTIVE` source grants substitution.
Closure removes the active source and profile ID only in a governed landing
after typed backfill/removal proof; revocation or expiry grants nothing. The
authoritative artifact/landing registry retains the immutable history and
globally claims the exception ID, so cleanup never permits reuse.

`TestQuarantineRecordV1` binds `RANEX-TDD-1.0`, the exact test-practice and
release profiles, base/candidate subjects, optional built-artifact digest,
affected stable test IDs and paths, observed
failure distribution and raw attempts, gate/risk impact, alternate evidence,
owner, work item, strict-UTC `opened_at`/`expires_at`, removal criteria,
restoration/backfill evidence, typed owner `HumanDecisionRecord`, evidence
snapshot/checker references, preallocated `landing_record_ref`, and exact
quarantine subject ref/digest. Its logical lifecycle is
`PROPOSED -> ACTIVE -> CLOSED | REVOKED | EXPIRED`. Only a canonical,
successfully landed, current record may quarantine; retries preserve every
attempt and never manufacture a passing observation. Closure removes its
active profile ID/source only through a later committed landing after the
typed restoration/backfill check and owner decision pass. An `ACTIVE`
quarantine affecting the candidate, required gate, or material risk, and an
expired-but-unclosed quarantine, both block the derived cycle `PASS`.
Revocation restores ordinary blocking immediately. The authoritative
artifact/landing registry globally claims each quarantine ID, so cleanup never
allows reuse.

Opening and closure are evaluated only against one named committed candidate
and its committed canonical source/registry trees. For each landing, the
authoritative strict-UTC order is
`evidence/check finished_at <= owner decision issued_at <=
LandingRecord.started_at <= LandingRecord.finished_at <=
validation_observed_at`; opening also requires
`opened_at <= LandingRecord.started_at` and
`opened_at < expires_at`, and must land while its evidence/decision is current
and before `expires_at`. Closure uses a later causal landing, current typed
restoration/backfill evidence and decision, and removes the active source/ID
projection without erasing immutable registry/landing history. Record and Git
commit timestamps are metadata only. Post-expiry closure may resolve the
underlying defect and historical lifecycle, but it cannot retroactively
authorize or manufacture a prior `PASS`; the expired-unclosed interval remains
blocking evidence. Staged, unstaged, untracked, omitted, noncausal, or
chronology-inverted source/record state fails.

`TestDeletionRecordV1` is the only authority for deliberate obsolete-test
removal, including ADR-0010 legacy-source retirement. It binds policy
`RANEX-TEST-DELETION-1.0` version `1.0.0`, `RANEX-TDD-1.0`, exact profile
ID/version/digest and `CURRENT` freshness, and:

- `target_kind: LEGACY_SOURCE | CANONICAL_TEST`;
- one globally unique `deletion_id`; for `CANONICAL_TEST`, one stable
  `test_id` and the complete, possibly empty,
  `source_migration_proof_ids`; for `LEGACY_SOURCE`, the exact baseline/current
  source row, scope, and authorized-source state while `test_id` is null;
- causal `before_commit_sha1` and `after_commit_sha1`, exact before/after
  `tests` tree OIDs and RFC 8785 Git-snapshot digests, before/nullable-after
  test rows, and an exact tests-delta manifest;
- requirement and risk trace dispositions, reason, fixture/snapshot/test-data
  cleanup, residual and marker-removal checks, and `resulting_gap_status:
  NONE`;
- exactly one retirement branch: nonempty distinct `successor_test_ids` with
  active unique-marker evidence, or a governed
  `NO_LONGER_REQUIRED_OR_APPLICABLE` human decision and evidence; and
- owner and process-assurance human decisions, independent review, evidence
  snapshot, qualified checker results, `PASS` retirement gate, preallocated
  opaque `landing_record_ref`, exact deletion subject ref/digest,
  `accepted_at`, `recorded_at`, `result: PASS`, and `status: ACCEPTED`.

The deletion event commit is the direct child of its before commit and its
after-before `tests` delta equals only the named target, successor, and
cleanup-manifest operations. A following record commit adds only the finalized
canonical deletion record; one successful commit-preserving `LandingRecord`
binds the full stack to `TEST_DELETION_SUBJECT_V1`. For a canonical target, the
before tree has exactly one regular canonical `.py` marker
`# ranex-test-id: <test_id>` and the after tree has none. For a legacy target,
the before row equals the one still-authorized inherited ledger row and the
after tree lacks it. Every successor has exactly one active canonical marker.
The validator reads commits, trees, modes, blobs, snapshot/delta manifests,
record bytes, landing, artifacts, and decisions independently.

An accepted deletion transitions that target lineage from `ACTIVE` to
`RETIRED` exactly once. Retired IDs are globally nonreusable as a marker,
migration destination, deletion target, or successor; the validator scans the
causal committed lineage and the authoritative ID registry, not just the
current tree. Successor edges are acyclic and are followed recursively until
each terminal is one current unique `ACTIVE` marker or a governed
no-longer-required/applicable disposition. Missing, forged, wrong-subject,
duplicate, cyclic, reused-retired-ID, incomplete-cleanup, or bare-string
records block. Ordinary test deletion without this authority is an
unexplained evidence gap.

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
  - {id: "TDD-LOOP-001", enforcement: "BLOCK", invariant: "Each implementation change has one canonical TDD cycle that binds its exact base/candidate, declared change profile, exact profile-specific step sequence, denominators, typed evidence and any valid exception."}
  - {id: "TDD-PROFILE-001", enforcement: "BLOCK", invariant: "The change profile and no_refactor_needed flag select exactly one legal sequence; REFACTOR_ONLY and bounded exception profiles never manufacture RED or an empty REFACTOR step."}
  - {id: "TDD-RED-001", enforcement: "BLOCK", invariant: "Every RED step matches one exact stable-test/criterion/failure-row/matcher fingerprint and excludes launch, unrelated, timeout, cancellation, error and harness failure."}
  - {id: "TDD-JOURNAL-001", enforcement: "BLOCK", invariant: "Every cycle binds one immutable governed run-journal slice with exactly one distinct causally ordered activity per declared step."}
  - {id: "TDD-ARCH-COVERAGE-001", enforcement: "BLOCK", invariant: "Every cycle partitions the complete bound architecture-rule registry; its architecture checker covers every applicable rule exactly once and every N/A rule has current exact-subject proof."}
  - {id: "TDD-LANDING-001", enforcement: "BLOCK", invariant: "TddCycleRecord is pre-landing GATED or REJECTED and contains no landing assertion; accepted TDD status derives only from a separate eligible LandingRecord bound to the exact cycle subject and candidate."}
  - {id: "TDD-REPRO-001", enforcement: "BLOCK", invariant: "Every cycle binds its predeclared Tier-1 or Tier-2 reproducibility envelope, and high-risk/seam/quarantine/security/migration/recovery/release lanes cannot use Tier 1."}
  - {id: "TDD-ORACLE-001", enforcement: "BLOCK", invariant: "RED-bearing and Tier-2 cycles bind an authoritative non-tautological oracle source; missing, implementation-derived, same-change-blessed or circular expectations block."}
  - {id: "TDD-PROD-001", enforcement: "BLOCK", invariant: "Tests execute production domain/application/authority/policy/schema/migration code with no test-only business branch or weakened control."}
  - {id: "TDD-ARTIFACT-001", enforcement: "BLOCK", invariant: "Gate-bearing lanes test one content-digested candidate artifact and release profile."}
  - {id: "TDD-SEAM-001", enforcement: "BLOCK", invariant: "Nondeterminism/external effects enter only through declared ports with recorded controls, and every fake has parity plus representative real-adapter evidence."}
  - {id: "TDD-SQLITE-001", enforcement: "BLOCK", invariant: "Persistence evidence uses ephemeral real SQLite, production migrations and the production UoW."}
  - {id: "TDD-TAXONOMY-001", enforcement: "BLOCK", invariant: "Every test resides in an allowed root and resolves to one context/capability owner, lane and exact subject."}
  - {id: "TDD-FAILURE-001", enforcement: "BLOCK", invariant: "Every capability has a complete versioned applicability/result row for each required failure-mode category."}
  - {id: "TDD-STATE-001", enforcement: "BLOCK", invariant: "Closed state/command/gate/effect registries have exhaustive legal and illegal transition-pair coverage."}
  - {id: "TDD-OPEN-001", enforcement: "BLOCK", invariant: "Open input spaces declare properties/partitions and reproducible property/model/fuzz/mutation/fault evidence plus remaining unknowns."}
  - {id: "TDD-FIXTURE-001", enforcement: "BLOCK", invariant: "Fixtures/builders have one owner, provenance/classification/version, deterministic semantics and no duplicate business rule."}
  - {id: "TDD-FLAKE-001", enforcement: "BLOCK", invariant: "Retries/quarantine never manufacture PASS; every quarantine has governed exact-subject evidence and approval, is owned and expiring, and preserves material UNKNOWN/blocking status."}
  - {id: "TDD-GENERATED-001", enforcement: "BLOCK", invariant: "Generated-code exceptions bind generator/schema/golden/compatibility/drift tests and prohibit hand edits."}
  - {id: "TDD-MIGRATION-001", enforcement: "BLOCK", invariant: "Migration/replay evidence covers forward/backward/rollback/crash/corruption/version/digest repeatability on production code."}
  - {id: "TDD-DATA-001", enforcement: "BLOCK", invariant: "Test data satisfies classification, minimization, provenance, secret, access, retention and deletion policy."}
  - {id: "TDD-LANES-001", enforcement: "BLOCK", invariant: "Risk/release policy schedules every required lane against the same subject; slow scheduling cannot waive it."}
  - {id: "TDD-MUTATION-001", enforcement: "REQUIRED", invariant: "Risk-selected critical logic receives mutation/negative assertion-strength evidence with survivor disposition."}
  - {id: "TDD-OBS-001", enforcement: "BLOCK", invariant: "Test paths emit production-equivalent structured observability with explicit test subject/profile identity."}
  - {id: "TDD-NONCOMP-001", enforcement: "BLOCK", invariant: "Proxy scores cannot compensate for missing, failed, stale, flaky or UNKNOWN required evidence."}
  - {id: "TDD-EXEMPTION-001", enforcement: "BLOCK", invariant: "Every TDD exception is a canonical typed lifecycle instance with exact scope/subject, governed approval, risk and alternative proof, expiry, backfill and globally nonreused identity."}
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
Quarantine and applicability/`NOT_APPLICABLE` rows likewise use governed typed
artifact references bound to the exact subject, decision time, producer, and
authorized role; an inline string or the enclosing profile cannot approve
itself.

The profile derives its result row by row. Every material `UNKNOWN`, conflict,
stale or failed obligation remains blocking. Every active quarantine and TDD
exception remains explicitly represented; an active or expired-unclosed
quarantine blocks, while an exception follows its exact policy-determined
substitution and residual risk. None may be omitted, averaged away, or turned
into `PASS` by totals elsewhere.

## Fitness evidence

| ID | Required evidence |
|---|---|
| `FF-TDD-001` | Canonical fixtures for all six change profiles preserve the exact base/candidate, legal profile-specific steps, strict chronology, denominator manifests, and applicable build/release tuple without manufactured phases. |
| `FF-TDD-002` | Test-only branch/bypass and subject-mock probes fail; built-artifact lanes identify one digest/profile. |
| `FF-TDD-003` | Fake/real adapter parity, ephemeral SQLite/migration, and production-equivalent observability checks pass. |
| `FF-TDD-004` | Failure matrix coverage reconciles every required category and closed transition pair; missing/material unknowns block. |
| `FF-TDD-005` | Property/fuzz/fault evidence reproduces from recorded seeds/corpus and reports explored domain/shrinking/unknowns. |
| `FF-TDD-006` | Canonical quarantine expiry/retry/closure and TDD-exception lifecycle tests prove active/expired-unclosed or omitted quarantine, expiry laundering, inline authority, stale/forged/wrong-subject/unqualified refs, chronology inversion, or ID reuse cannot become gate PASS; a timely opening and later valid typed restoration closure is the positive path. |
| `FF-TDD-007` | Critical mutation/negative tests demonstrate that assertions detect representative wrong behavior. |
| `FF-TDD-008` | Migration/replay/crash/backup/restore/reconciliation tests use the production artifact and real durable seams; obsolete-test fixtures prove canonical/legacy retirement, successor/N/A lineage, cleanup, and retired-ID nonreuse. |
| `FF-TDD-009` | RED fingerprint fixtures independently falsify stable-test ID, criterion ID, failure-row ID/digest, matcher schema/ref/digest, expected failure code, and harness-failure exclusion; every mismatch blocks. |
| `FF-TDD-010` | Journal fixtures prove one ordered activity per profile step and reject missing/extra/reused activity, cursor gap, wrong run, wrong manifest digest, post-hoc evidence, or gate-before-architecture-check. |
| `FF-TDD-011` | Architecture-rule fixtures reconcile the full bound registry, independently reject one omitted/duplicated/uncovered applicable rule and every missing/stale/wrong-subject N/A proof, and become stale on registry change. |
| `FF-TDD-012` | Landing fixtures prove a GATED pre-landing cycle has no landing assertion, cannot self-accept, and derives acceptance only from one separately produced eligible `SUCCEEDED` LandingRecord for the exact cycle subject/candidate; legacy `LANDED`, null, unknown, nonterminal, failed, wrong, missing, future, or duplicate receipts block. |
| `FF-TDD-013` | Tier fixtures enforce Tier-1/Tier-2 field closure and activation policy; oracle fixtures reject missing Tier-2/RED provenance and implementation-derived, same-change-blessed, circular, wrong-digest, or unauthorized oracle sources. |

No current runtime enactment is claimed.

## Definition-freeze and implementation-start readiness exit

`ACCEPTED` records the human normative decision. It is not a claim that this
revision is definition-frozen, executable, or
`IMPLEMENTATION_START_READY`. Under
[ADR-0012](./ADR-0012-separate-implementation-start-and-production-readiness.md),
the first readiness tier remains `NOT_ASSESSED` until one exact source subject
satisfies all of the following without waivers:

1. `SDLC-FORK-000` passes for the exact clean, committed, upstream-derived
   evaluation commit/tree and worktree;
2. the contract compiler emits every closed record, nested type, subject,
   checker, legal-hold, registry, manifest, and negative-fixture projection;
3. the deterministic validator returns zero violations against those exact
   source and generated digests, with no stale generated file or denominator;
4. fixtures exercise all six profile sequences, both
   `no_refactor_needed` branches, every fingerprint dimension, journal/rule
   coverage, both reproducibility tiers, oracle requirements, and the
   pre-/post-landing split;
5. one bounded readiness tooling tracer produces a real, nonsynthetic,
   current-subject `BEHAVIOR_CHANGE` cycle from RED
   through architecture check, `GATED`, and a separate successful
   `SUCCEEDED` `LandingRecord`, followed by a current seal over the landed
   commit/tree and all bound inputs;
6. fresh read-only OpenCode HY3 and DeepSeek V4 Pro reviews retain their exact
   architecture subject and bind it to the same
   source/generated/validation/evaluation-commit readiness subject through
   ADR-0012's registered native-subject bridges; and
7. exact finding reconciliation leaves no unresolved P0/P1 and an
   authenticated human decision approves staged implementation only after all
   prior evidence.

That exact pass authorizes staged implementation through ordinary per-work
controls. It does not require runtime results or maturity scores to exist;
those remain explicitly `NOT_ASSESSED`/null and cannot be called pass. Before
the tier passes, only ADR-0012's bounded `PRE_READINESS_TOOLING_TRACER` may
produce readiness evidence; it cannot implement a product capability or
activate runtime.

The admitted evaluation baseline remains valid across ordinary authorized
product landings only while the current head is a clean descendant and every
governed design/control-manifest byte is unchanged. Such product work remains
fully subject to its own packet, TDD, gate, review, authority, and landing
controls. A non-descendant, dirty head, governed-path change, expired window,
or invalidated bound input blocks Tier 1 and requires a fresh immutable
assessment; every prior assessment and transition fact remains historical.

`PRODUCTION_READY` is the second, separate tier. It remains blocked while
runtime producers are unenacted, the exact 64 ADR-0007–ADR-0010 rule results
are incomplete or blocking, or applicable adoption, security, recovery,
operational, score, and authority evidence is absent. No numeric proxy,
document-only pass, or implementation-start result can compensate.

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
6. **A second TDD lifecycle or TDD-only event family.** Rejected because the
   governed run journal and existing Activity/Evidence/Gate facts already own
   causal execution. `TddCycleJournalBindingV1` closes and digests the exact
   cycle slice; a future convenience event may project that fact for queries
   but cannot become another authority or a freeze prerequisite.

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
