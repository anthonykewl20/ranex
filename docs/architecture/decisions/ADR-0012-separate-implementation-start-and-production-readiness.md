# ADR-0012: Separate Implementation-Start and Production Readiness

| Field | Value |
|---|---|
| ADR ID | `ADR-0012` |
| Version | `1.1.0` |
| Status | `ACCEPTED` |
| Decision owner | Human owner |
| Decision date | 2026-07-29 |
| Effective revision | Definition-only working tree; no readiness assessment or authorization is claimed |
| Content binding | Exact digest is recorded externally in each immutable review/release source manifest |
| Affected contexts | `process_assurance`, `assurance`, `policy`, `work_management`, `governed_execution`, `configuration_management`, `provenance_compliance`, `migration`, `release_management`, `operations`, and every context supplying readiness evidence |
| RFC | Not required; resolves the human owner's readiness-language and bootstrap-authority decision |
| Supersedes | Ambiguous uses of “build ready,” “enterprise build ready,” and “runtime ready” in earlier documents; it does not weaken any evidence, authority, security, recovery, or production gate |
| Review/expiry date | Review on any readiness tier, gate, evidence role, reviewer route, architecture-rule denominator, production-admission, or authority-boundary change |
| Compatibility/migration class | New typed readiness namespace; historical unqualified readiness statements become nonauthoritative prose until mapped to this contract |
| Security/data class | Public decision and gate metadata; referenced source, review, security, operational, and production evidence retains its own classification |

## Revision history

| Version | Date | Change and rationale |
|---|---|---|
| `1.1.0` | 2026-07-29 | Reconciled the readiness lifecycle with the shared state/transition conventions: registered `READINESS-STATE-1.0` in the main state catalog, changed guard identifiers to underscore form, and bound transition facts to the standard `architecture/contracts/states.json` catalog. This corrects the prior cross-contract incompatibility without changing or versioning `TransitionEventV1` and declares no readiness tier. |
| `1.0.0` | 2026-07-29 | Initial accepted definition-only readiness contract. |

## Decision

Ranex has two noncompensating readiness tiers with different authority and
evidence boundaries:

| Canonical machine state | Documentation label | What it permits | What it does not claim |
|---|---|---|---|
| `IMPLEMENTATION_START_READY` | `DESIGN_DEFINITION_READY` | Admission of staged product implementation under the normal per-work-item packet, gate, grant, permit, TDD, review, and landing controls | Enacted product runtime, production safety, operational effectiveness, mature capability scores, release, deployment, or user impact |
| `PRODUCTION_READY` | `ENTERPRISE_RUNTIME_READY` | Eligibility to request the normal exact-subject release/deployment authority chain after runtime and operational readiness passes | A deployment effect, release permit, waiver, permanent qualification, or proof of healthy operation after change |

The documentation labels are explanatory labels, not additional states or
accepted aliases. Machine records use only the canonical states. A document
that says only “build ready,” “enterprise ready,” or “runtime ready” grants no
authority.

`IMPLEMENTATION_START_READY` is deliberately attainable before full runtime
enactment. Runtime rule results and capability effectiveness may remain
`NOT_ASSESSED`, but that fact must be explicit, cannot be represented as
`PASS`, and cannot be omitted from the assessment. This prevents absent runtime
evidence from circularly blocking the start of staged implementation while
also preventing a paper contract from masquerading as a production system.

`PRODUCTION_READY` requires enacted runtime producers, complete current rule
results, operational and recovery evidence, applicable evidence-bound
capability assessments, and the normal human authority chain. An
implementation-start result cannot compensate for any missing production
evidence.

Neither tier is currently declared. This ADR accepts the vocabulary,
state machine, gate contracts, and authority boundary only.

## Bootstrap without circular authority

Before `IMPLEMENTATION_START_READY`, one bounded
`PRE_READINESS_TOOLING_TRACER` lane may create only the evidence needed to
evaluate that tier:

- compiler, generator, validator, schema, fixture, manifest, and deterministic
  review-harness changes on registered architecture/tooling paths;
- fork-preservation, provenance, clean-worktree, and source-manifest work;
- one real current-subject ADR-0008 cycle and its separately produced
  `SUCCEEDED` `LandingRecord` and sealing evidence; and
- read-only review and finding-reconciliation artifacts.

Every tracer change still needs an exact work item, bounded task packet,
ordinary path/effect authority, tests, review, and human-controlled landing.
The lane cannot implement a product capability, activate a product runtime,
process production/user data, deploy, release, grant itself readiness, relax a
gate, or become a reusable bypass. Failure, expiry, scope growth, or an
unregistered path ends the tracer without a readiness transition.

## Exact machine contract

The following marked YAML block is the sole semantic source for the readiness
tier catalog, state axis, assessment schema, resolver, and synthetic fixture
denominators. Generated projections preserve the complete mapping without
semantic edits.

<!-- BEGIN ADR12 READINESS TIER CONTRACT -->

```yaml
readiness_tier_contract:
  contract_id: "RANEX-READINESS-TIER-CONTROL-1.0"
  contract_version: "1.0.0"
  schema_version: "readiness-tier-contract/v1"
  catalog_id: "RANEX-READINESS-TIERS-001"
  catalog_version: "1.0.0"
  catalog_status: "DEFINITION_ONLY_NOT_ASSESSED"
  governing_adr: "ADR-0012"
  canonicalization: "RFC8785"
  digest_algorithm: "SHA-256"
  digest_encoding: "sha256:<64 lowercase hex>"
  additional_properties: false
  noncompensating: true
  source_projection_ref: "architecture/contracts/readiness-tiers.json"
  assessment_registry_ref: "architecture/contracts/readiness-assessments.json"
  subject_schema_ref: "schemas/assurance/readiness-subject-v1.schema.json"
  subject_manifest_schema_ref: "schemas/assurance/readiness-subject-manifest-v1.schema.json"
  evidence_binding_schema_ref: "schemas/assurance/readiness-evidence-binding-v1.schema.json"
  assessment_schema_ref: "schemas/assurance/readiness-assessment-v1.schema.json"
  inherited_type_authority:
    source: "ADR-0008, AI_ARTIFACT_CONTRACTS.md, and their generated schemas"
    types:
      - "ArchitectureSubject"
      - "TddCycleRecordV1"
      - "LandingRecordV1"
      - "HumanDecisionRecord"
      - "ReviewVerdict"
      - "GateEvaluation"
      - "CapabilityAssessment"
      - "TransitionEventV1"
  scalar_types:
    safe_id: "nonempty registered identifier with no path traversal"
    safe_ref: "safe_id or registered urn:ranex identifier"
    sha1: "40 lowercase hexadecimal characters"
    sha256: "sha256:<64 lowercase hexadecimal characters>"
    strict_utc: "RFC3339 UTC instant with Z and no leap second"
    nonempty_string: "nonempty UTF-8 string"

  runtime_assessment_status_contract:
    enum_id: "ENUM-READINESS-RUNTIME-ASSESSMENT-STATUS-1.0"
    owner_context: "process_assurance"
    axis_kind: "CLASSIFIER"
    transition_authority: "NONE"
    values:
      - "NOT_ASSESSED"
      - "UNKNOWN"
      - "ASSESSED_PASS"
      - "ASSESSED_FAIL"
      - "CONFLICT"
    semantics:
      NOT_ASSESSED: "no runtime-assurance attempt exists; paired runtime assessment ref/digest are null"
      UNKNOWN: "an attempt exists but material required evidence is insufficient"
      ASSESSED_PASS: "one exact immutable runtime-assurance reconciliation satisfies its complete applicable contract"
      ASSESSED_FAIL: "one exact immutable runtime-assurance reconciliation has at least one blocking failure"
      CONFLICT: "one exact immutable runtime-assurance reconciliation contains unresolved contradictory authority or evidence"

  state_axis:
    axis_id: "READINESS-STATE-1.0"
    axis_kind: "LIFECYCLE"
    axis_version: "1.0.0"
    owner_context: "process_assurance"
    state_catalog_ref: "architecture/contracts/states.json"
    aggregate_type: "RepositoryReadiness"
    aggregate_id_rule: "aggregate_id equals repository_id"
    emitted_fact: "TransitionEventV1(axis_id=READINESS-STATE-1.0)"
    ready_transition_authority: "authenticated human governor after deterministic readiness resolver PASS"
    blocking_transition_authority: "deterministic process-assurance invalidation; no human may retain a stale ready state"
    initial_state: "NOT_ASSESSED"
    values:
      - "NOT_ASSESSED"
      - "IMPLEMENTATION_START_EVALUATING"
      - "IMPLEMENTATION_START_BLOCKED"
      - "IMPLEMENTATION_START_READY"
      - "PRODUCTION_EVALUATING"
      - "PRODUCTION_BLOCKED"
      - "PRODUCTION_READY"
    transition_notation: "FROM>TO@GUARD_ID"
    transitions:
      - "NOT_ASSESSED>IMPLEMENTATION_START_EVALUATING@READINESS_ASSESSMENT_OPENED"
      - "IMPLEMENTATION_START_EVALUATING>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_NOT_PASS"
      - "IMPLEMENTATION_START_EVALUATING>IMPLEMENTATION_START_READY@IMPLEMENTATION_START_EXACT_PASS_AND_HUMAN_DECISION"
      - "IMPLEMENTATION_START_BLOCKED>IMPLEMENTATION_START_EVALUATING@FRESH_EXACT_SUBJECT_REASSESSMENT"
      - "IMPLEMENTATION_START_READY>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_EVIDENCE_INVALIDATED"
      - "IMPLEMENTATION_START_READY>PRODUCTION_EVALUATING@PRODUCTION_ASSESSMENT_OPENED"
      - "PRODUCTION_EVALUATING>PRODUCTION_BLOCKED@PRODUCTION_NOT_PASS"
      - "PRODUCTION_EVALUATING>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_PREREQUISITE_INVALIDATED"
      - "PRODUCTION_EVALUATING>PRODUCTION_READY@PRODUCTION_EXACT_PASS_AND_HUMAN_DECISION"
      - "PRODUCTION_BLOCKED>PRODUCTION_EVALUATING@FRESH_EXACT_SUBJECT_REASSESSMENT"
      - "PRODUCTION_BLOCKED>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_PREREQUISITE_INVALIDATED"
      - "PRODUCTION_READY>PRODUCTION_BLOCKED@PRODUCTION_EVIDENCE_INVALIDATED"
      - "PRODUCTION_READY>IMPLEMENTATION_START_BLOCKED@IMPLEMENTATION_START_PREREQUISITE_INVALIDATED"
    forbidden_transitions:
      - "NOT_ASSESSED>IMPLEMENTATION_START_READY"
      - "NOT_ASSESSED>PRODUCTION_READY"
      - "IMPLEMENTATION_START_BLOCKED>IMPLEMENTATION_START_READY"
      - "IMPLEMENTATION_START_READY>PRODUCTION_READY"
      - "PRODUCTION_BLOCKED>PRODUCTION_READY"
      - "PRODUCTION_READY>IMPLEMENTATION_START_READY"
    rejection_result: "NO_STATE_CHANGE_NO_AUTHORIZATION_NO_TRANSITION_FACT"

  transition_fact_contract:
    schema_ref: "schemas/work/transition-event-v1.schema.json"
    additional_properties: false
    exact_bindings:
      - "state_catalog_ref, axis_id, axis_version, owner_context, aggregate_type, and aggregate_id equal the state_axis contract and repository_id"
      - "from_state equals the prior current state; to_state and guard_id name one exact allowed transition; aggregate_version_after equals aggregate_version_before plus one"
      - "subject schema/ref/digest/manifest digest equal the assessment exact readiness subject; evidence_refs include that immutable assessment and its gate bindings"
      - "A READY transition additionally binds the exact current authenticated human decision; a blocking transition binds the deterministic invalidation evidence"
      - "The transition fact is appended atomically after assessment resolution; rejection writes no state mutation, fact, authorization, grant, or permit"
    uniqueness: "at most one immutable transition fact exists for repository_id and aggregate_version_after"
    current_state_rule: "derive current state only from the complete append-only gap-free transition history; assessment bytes and prior facts are never edited"

  exact_subject_projection:
    projection_id: "READINESS_SUBJECT_V1"
    subject_schema: "readiness-subject/v1"
    schema_ref: "schemas/assurance/readiness-subject-v1.schema.json"
    additional_properties: false
    output_fields:
      - "subject_schema"
      - "subject_ref"
      - "readiness_subject_identity_digest"
      - "readiness_basis_digest"
      - "readiness_subject_manifest_digest"
      - "repository_id"
      - "readiness_contract_id"
      - "readiness_contract_version"
      - "tier_id"
      - "source_commit_sha1"
      - "source_tree_oid_sha1"
      - "source_manifest_digest"
      - "generated_manifest_digest"
      - "contract_validation_report_digest"
      - "architecture_subject_digest"
      - "architecture_subject_manifest_digest"
      - "fork_preflight_digest"
      - "tier_evidence_subject_schema"
      - "tier_evidence_subject_ref"
      - "tier_evidence_subject_digest"
      - "tier_evidence_subject_manifest_digest"
      - "assessment_window_end"
    field_types:
      subject_schema: {const: "readiness-subject/v1"}
      subject_ref: "safe_ref"
      readiness_subject_identity_digest: "sha256"
      readiness_basis_digest: "sha256"
      readiness_subject_manifest_digest: "sha256"
      repository_id: "safe_id"
      readiness_contract_id: {const: "RANEX-READINESS-TIER-CONTROL-1.0"}
      readiness_contract_version: {const: "1.0.0"}
      tier_id: {enum: ["READINESS-TIER-IMPLEMENTATION-START-001", "READINESS-TIER-PRODUCTION-001"]}
      source_commit_sha1: "sha1"
      source_tree_oid_sha1: "sha1"
      source_manifest_digest: "sha256"
      generated_manifest_digest: "sha256"
      contract_validation_report_digest: "sha256"
      architecture_subject_digest: "sha256"
      architecture_subject_manifest_digest: "sha256"
      fork_preflight_digest: "sha256"
      tier_evidence_subject_schema: "nonempty_string|null"
      tier_evidence_subject_ref: "safe_ref|null"
      tier_evidence_subject_digest: "sha256|null"
      tier_evidence_subject_manifest_digest: "sha256|null"
      assessment_window_end: "strict_utc"
    nullable_fields:
      - "tier_evidence_subject_schema"
      - "tier_evidence_subject_ref"
      - "tier_evidence_subject_digest"
      - "tier_evidence_subject_manifest_digest"
    array_cardinalities: {}
    field_semantics:
      source_commit_sha1: "the clean committed upstream-derived evaluation baseline from which Tier 1 admits staged implementation"
      source_tree_oid_sha1: "the complete Git tree at that evaluation baseline; retained as historical admission evidence rather than rebound to each later implementation commit"
      source_manifest_digest: "the exact bytewise governed architecture, policy, schema-source, generator, validator, and manifest-input path set at the evaluation baseline"
      tier_evidence_subject: "all four tier_evidence_subject_* fields are null for Tier 1; for Tier 2 schema/ref/digest bind one exact built-once runtime release subject and its manifest field follows that native schema's nullability rule"
    readiness_basis_digest_rule: "RFC8785 SHA-256 over exactly repository_id, readiness_contract_id, readiness_contract_version, source_commit_sha1, source_tree_oid_sha1, source_manifest_digest, generated_manifest_digest, contract_validation_report_digest, architecture_subject_digest, architecture_subject_manifest_digest, and fork_preflight_digest; tier, runtime release subject, assessment window, manifest digest, subject ref, and tier-specific subject digest are excluded"
    readiness_subject_identity_digest_rule: "RFC8785 SHA-256 over exactly readiness_basis_digest, tier_id, tier_evidence_subject_schema, tier_evidence_subject_ref, tier_evidence_subject_digest, tier_evidence_subject_manifest_digest, and assessment_window_end"
    subject_ref_rule: "urn:ranex:readiness:<repository_id>:<tier_id>:<readiness_subject_identity_digest-without-prefix>"
    manifest_binding_rule: "readiness_subject_manifest_digest equals the independently generated closed READINESS_SUBJECT_MANIFEST_V1 for this subject identity"
    descendant_validity_rule: "After Tier 1 admission, an ordinary authorized product implementation commit does not change this frozen evaluation subject. Future reliance requires a clean current head descended from source_commit_sha1 and byte-identical governed source-manifest paths; a non-descendant, dirty head, or governed-path change invalidates Tier 1."
    digest_rule: "RFC8785 SHA-256 over exactly the output fields"

  readiness_subject_manifest_projection:
    projection_id: "READINESS_SUBJECT_MANIFEST_V1"
    manifest_schema: "readiness-subject-manifest/v1"
    schema_ref: "schemas/assurance/readiness-subject-manifest-v1.schema.json"
    additional_properties: false
    output_fields:
      - "manifest_schema"
      - "manifest_ref"
      - "readiness_subject_ref"
      - "repository_id"
      - "readiness_contract_id"
      - "readiness_contract_version"
      - "tier_id"
      - "readiness_basis_digest"
      - "readiness_subject_identity_digest"
      - "source_commit_sha1"
      - "source_tree_oid_sha1"
      - "entries"
      - "digest"
    field_types:
      manifest_schema: {const: "readiness-subject-manifest/v1"}
      manifest_ref: "safe_ref"
      readiness_subject_ref: "safe_ref"
      repository_id: "safe_id"
      readiness_contract_id: {const: "RANEX-READINESS-TIER-CONTROL-1.0"}
      readiness_contract_version: {const: "1.0.0"}
      tier_id: {enum: ["READINESS-TIER-IMPLEMENTATION-START-001", "READINESS-TIER-PRODUCTION-001"]}
      readiness_basis_digest: "sha256"
      readiness_subject_identity_digest: "sha256"
      source_commit_sha1: "sha1"
      source_tree_oid_sha1: "sha1"
      entries: "ReadinessSubjectManifestEntryV1[]"
      digest: "sha256"
    nullable_fields: []
    array_cardinalities:
      entries: "exactly 7 for Tier 1; exactly 8 for Tier 2"
    array_order:
      entries: "BYTEWISE_ROLE"
    exact_entry_roles_by_tier:
      READINESS-TIER-IMPLEMENTATION-START-001:
        - "ARCHITECTURE_SUBJECT"
        - "ARCHITECTURE_SUBJECT_MANIFEST"
        - "COMMITTED_SOURCE_MANIFEST"
        - "CONTRACT_VALIDATION_REPORT"
        - "FORK_PREFLIGHT"
        - "GENERATED_OUTPUT_MANIFEST"
        - "READINESS_CONTRACT_SOURCE"
      READINESS-TIER-PRODUCTION-001:
        - "ARCHITECTURE_SUBJECT"
        - "ARCHITECTURE_SUBJECT_MANIFEST"
        - "COMMITTED_SOURCE_MANIFEST"
        - "CONTRACT_VALIDATION_REPORT"
        - "FORK_PREFLIGHT"
        - "GENERATED_OUTPUT_MANIFEST"
        - "READINESS_CONTRACT_SOURCE"
        - "TIER_EVIDENCE_SUBJECT"
    entry_binding_rules:
      ARCHITECTURE_SUBJECT: "digest equals exact_subject.architecture_subject_digest"
      ARCHITECTURE_SUBJECT_MANIFEST: "digest equals exact_subject.architecture_subject_manifest_digest"
      COMMITTED_SOURCE_MANIFEST: "digest equals exact_subject.source_manifest_digest"
      CONTRACT_VALIDATION_REPORT: "digest equals exact_subject.contract_validation_report_digest"
      FORK_PREFLIGHT: "digest equals exact_subject.fork_preflight_digest"
      GENERATED_OUTPUT_MANIFEST: "digest equals exact_subject.generated_manifest_digest"
      READINESS_CONTRACT_SOURCE: "artifact_ref is the registered ADR-0012 source URN and digest equals the exact committed ADR-0012 source-file digest carried by COMMITTED_SOURCE_MANIFEST"
      TIER_EVIDENCE_SUBJECT: "present only for Tier 2; schema/ref/digest/manifest binding equals the exact_subject tier_evidence_subject_* tuple"
    manifest_ref_rule: "urn:ranex:readiness-manifest:<repository_id>:<tier_id>:<readiness_subject_identity_digest-without-prefix>"
    digest_rule: "RFC8785 SHA-256 over exactly every output field except digest; the manifest never includes the final readiness subject digest, so derivation is noncircular"

  nested_types:
    - type_id: "ReadinessSubjectManifestEntryV1"
      additional_properties: false
      fields:
        - "role"
        - "artifact_schema"
        - "artifact_ref"
        - "artifact_digest"
        - "artifact_subject_manifest_digest"
      field_types:
        role: {enum: ["ARCHITECTURE_SUBJECT", "ARCHITECTURE_SUBJECT_MANIFEST", "COMMITTED_SOURCE_MANIFEST", "CONTRACT_VALIDATION_REPORT", "FORK_PREFLIGHT", "GENERATED_OUTPUT_MANIFEST", "READINESS_CONTRACT_SOURCE", "TIER_EVIDENCE_SUBJECT"]}
        artifact_schema: "nonempty_string"
        artifact_ref: "safe_ref"
        artifact_digest: "sha256"
        artifact_subject_manifest_digest: "sha256|null"
      nullable_fields:
        - "artifact_subject_manifest_digest"
      array_cardinalities: {}
    - type_id: "ReadinessEvidenceBindingV1"
      schema_ref: "schemas/assurance/readiness-evidence-binding-v1.schema.json"
      additional_properties: false
      fields:
        - "schema_version"
        - "record_type"
        - "gate_id"
        - "readiness_subject_ref"
        - "readiness_subject_digest"
        - "readiness_subject_manifest_digest"
        - "readiness_basis_digest"
        - "native_subject_schema"
        - "native_subject_ref"
        - "native_subject_digest"
        - "native_subject_manifest_digest"
        - "evidence_schema"
        - "evidence_ref"
        - "evidence_digest"
        - "bridge_rule_id"
        - "digest"
      field_types:
        schema_version: {const: "1"}
        record_type: {const: "READINESS_EVIDENCE_BINDING"}
        gate_id: "safe_id"
        readiness_subject_ref: "safe_ref"
        readiness_subject_digest: "sha256"
        readiness_subject_manifest_digest: "sha256"
        readiness_basis_digest: "sha256"
        native_subject_schema: "nonempty_string"
        native_subject_ref: "safe_ref"
        native_subject_digest: "sha256"
        native_subject_manifest_digest: "sha256|null"
        evidence_schema: "nonempty_string"
        evidence_ref: "safe_ref"
        evidence_digest: "sha256"
        bridge_rule_id: "safe_id"
        digest: "sha256"
      nullable_fields:
        - "native_subject_manifest_digest"
      array_cardinalities: {}
      invariants:
        - "digest is RFC8785 SHA-256 over every field except digest"
        - "the four readiness fields equal the containing assessment's independently resolved exact subject and basis"
        - "evidence_ref/digest resolves immutable bytes whose native subject tuple exactly equals the four native_subject_* fields"
        - "bridge_rule_id is the one registered rule for gate_id; the resolver independently proves its relation and rejects caller-selected relabeling"
    - type_id: "ReadinessGateResultV1"
      additional_properties: false
      fields:
        - "gate_id"
        - "result"
        - "evidence_binding"
        - "observed_at"
        - "valid_until"
      field_types:
        gate_id: "safe_id"
        result: {enum: ["PASS", "FAIL", "UNKNOWN", "CONFLICT", "NOT_APPLICABLE"]}
        evidence_binding: "ReadinessEvidenceBindingV1"
        observed_at: "strict_utc"
        valid_until: "strict_utc"
      nullable_fields: []
      array_cardinalities: {}
      invariants:
        - "observed_at < valid_until"
        - "evidence_binding.gate_id equals gate_id and resolves the exact per-gate native-subject bridge"

  assessment_record:
    type_id: "ReadinessAssessmentV1"
    type_version: "1.0.0"
    schema_ref: "schemas/assurance/readiness-assessment-v1.schema.json"
    additional_properties: false
    fields:
      - "schema_version"
      - "record_type"
      - "assessment_id"
      - "tier_id"
      - "contract_id"
      - "contract_version"
      - "exact_subject_schema"
      - "exact_subject_ref"
      - "exact_subject_digest"
      - "readiness_basis_digest"
      - "exact_subject_manifest_digest"
      - "core_sdlc_trace_ref"
      - "prior_state"
      - "proposed_state"
      - "gate_results"
      - "open_finding_refs"
      - "resolved_finding_refs"
      - "runtime_assessment_status"
      - "runtime_assessment_ref"
      - "runtime_assessment_digest"
      - "capability_assessment_refs"
      - "human_decision_ref"
      - "human_decision_digest"
      - "observed_at"
      - "valid_until"
      - "supersedes_assessment_id"
      - "result"
      - "digest"
    field_types:
      schema_version: {const: "1"}
      record_type: {const: "READINESS_ASSESSMENT"}
      assessment_id: "safe_id"
      tier_id: {enum: ["READINESS-TIER-IMPLEMENTATION-START-001", "READINESS-TIER-PRODUCTION-001"]}
      contract_id: {const: "RANEX-READINESS-TIER-CONTROL-1.0"}
      contract_version: {const: "1.0.0"}
      exact_subject_schema: {const: "readiness-subject/v1"}
      exact_subject_ref: "safe_ref"
      exact_subject_digest: "sha256"
      readiness_basis_digest: "sha256"
      exact_subject_manifest_digest: "sha256"
      core_sdlc_trace_ref: "safe_ref"
      prior_state: {enum: ["NOT_ASSESSED", "IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_BLOCKED", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY"]}
      proposed_state: {enum: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_BLOCKED", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY"]}
      gate_results: "ReadinessGateResultV1[]"
      open_finding_refs: "safe_ref[]"
      resolved_finding_refs: "safe_ref[]"
      runtime_assessment_status: {enum_ref: "ENUM-READINESS-RUNTIME-ASSESSMENT-STATUS-1.0"}
      runtime_assessment_ref: "safe_ref|null"
      runtime_assessment_digest: "sha256|null"
      capability_assessment_refs: "safe_ref[]"
      human_decision_ref: "safe_ref|null"
      human_decision_digest: "sha256|null"
      observed_at: "strict_utc"
      valid_until: "strict_utc"
      supersedes_assessment_id: "safe_id|null"
      result: {enum: ["PASS", "FAIL", "UNKNOWN", "CONFLICT"]}
      digest: "sha256"
    nullable_fields:
      - "runtime_assessment_ref"
      - "runtime_assessment_digest"
      - "human_decision_ref"
      - "human_decision_digest"
      - "supersedes_assessment_id"
    array_cardinalities:
      gate_results: "1..N"
      open_finding_refs: "0..N"
      resolved_finding_refs: "0..N"
      capability_assessment_refs: "0..N"
    array_order:
      gate_results: "BYTEWISE_GATE_ID"
      open_finding_refs: "BYTEWISE_UTF8"
      resolved_finding_refs: "BYTEWISE_UTF8"
      capability_assessment_refs: "BYTEWISE_UTF8"
    invariants:
      - "digest is RFC8785 SHA-256 over every field except digest; assessment_id and digest are immutable and nonreusable"
      - "observed_at < valid_until, valid_until is no later than the exact subject assessment_window_end, and every gate result is current at observed_at"
      - "exact_subject_schema/ref/digest/manifest digest and readiness_basis_digest resolve one complete READINESS_SUBJECT_V1 plus its exact closed READINESS_SUBJECT_MANIFEST_V1; missing, extra, duplicate, reordered, forged, or cross-subject manifest entries fail"
      - "gate_results is the exact gate set for tier_id with no duplicate, omission, extra, or reordered row; the production tier resolves its prerequisite through READY-IMPLEMENTATION-PREREQUISITE-001, whose exact current assessment independently contains the complete Tier 1 gate set"
      - "PASS requires every noncompensating gate PASS, no open P0/P1 finding, one exact authenticated human decision issued strictly after all non-human-decision gate evidence observation/admission instants, and the corresponding READY proposed_state"
      - "Any FAIL, UNKNOWN, CONFLICT, stale, wrong-subject, missing, or duplicate required input forbids a READY proposed_state"
      - "human_decision_ref and human_decision_digest are paired; PASS requires both nonnull and an exact APPROVED decision, while a non-PASS assessment may carry no decision or an exact denied/ineligible decision"
      - "readiness_basis_digest equals the independently derived exact-subject readiness_basis_digest"
      - "Tier 1 READY permits runtime_assessment_status only NOT_ASSESSED or ASSESSED_PASS; Tier 2 READY requires ASSESSED_PASS; UNKNOWN, ASSESSED_FAIL, or CONFLICT forbids any READY proposed_state"
      - "runtime_assessment_ref and runtime_assessment_digest are paired; NOT_ASSESSED requires both null, while every other status requires both to resolve one exact immutable runtime-assurance reconciliation whose derived status equals runtime_assessment_status"
      - "A production assessment resolves one CURRENT IMPLEMENTATION_START_READY assessment with the identical readiness_basis_digest; the two tier-specific subject refs and digests necessarily differ because tier_id differs"
      - "supersedes_assessment_id is null for the first assessment of this repository and tier and otherwise names the unique immediate prior assessment; the complete append-only chain is chronological, single-predecessor, single-successor, acyclic, and gap-free"
      - "CURRENT, SUPERSEDED, INVALIDATED, and current state are resolver-derived eligibility facts over immutable assessments plus TransitionEventV1 history; no assessment field or digest is edited"

  tiers:
    - tier_id: "READINESS-TIER-IMPLEMENTATION-START-001"
      canonical_state: "IMPLEMENTATION_START_READY"
      documentation_label: "DESIGN_DEFINITION_READY"
      prerequisite_tier_id: null
      runtime_assessment_policy: "NOT_ASSESSED_OR_ASSESSED_PASS_ALLOWED; UNKNOWN_ASSESSED_FAIL_OR_CONFLICT_BLOCK; ASSESSED_PASS_CANNOT_COMPENSATE"
      capability_score_policy: "NULL_OR_NOT_ASSESSED_ALLOWED_AND_NONAUTHORITATIVE"
      admission_effect: "ELIGIBLE_FOR_STAGED_PRODUCT_IMPLEMENTATION_UNDER_NORMAL_PER_WORK_CONTROLS"
      authority_boundary: "NO_WORK_STATE_MUTATION_NO_GRANT_NO_PERMIT_NO_LANDING_NO_RELEASE_NO_DEPLOYMENT"
      exact_gate_ids:
        - "READY-CONTRACT-VALIDATION-001"
        - "READY-DEEPSEEK-REVIEW-001"
        - "READY-FINDING-RECONCILIATION-001"
        - "READY-FORK-PREFLIGHT-001"
        - "READY-GENERATED-MANIFEST-001"
        - "READY-HUMAN-START-DECISION-001"
        - "READY-HY3-REVIEW-001"
        - "READY-LANDING-001"
        - "READY-SEALING-001"
        - "READY-SOURCE-MANIFEST-001"
        - "READY-TDD-CYCLE-001"
    - tier_id: "READINESS-TIER-PRODUCTION-001"
      canonical_state: "PRODUCTION_READY"
      documentation_label: "ENTERPRISE_RUNTIME_READY"
      prerequisite_tier_id: "READINESS-TIER-IMPLEMENTATION-START-001"
      runtime_assessment_policy: "ONLY_ASSESSED_PASS_ALLOWED; NOT_ASSESSED_UNKNOWN_ASSESSED_FAIL_OR_CONFLICT_BLOCK"
      capability_score_policy: "EVERY_APPLICABLE_REGISTERED_CONTROL_HAS_CURRENT_SCORED_OR_APPROVED_NOT_APPLICABLE_ASSESSMENT"
      admission_effect: "ELIGIBLE_TO_REQUEST_NORMAL_RELEASE_AND_DEPLOYMENT_AUTHORITY_CHAIN"
      authority_boundary: "NO_GRANT_NO_PERMIT_NO_RELEASE_NO_DEPLOYMENT_NO_HEALTH_OR_OUTCOME_CLAIM"
      exact_gate_ids:
        - "READY-ADOPTION-GATES-001"
        - "READY-AUTHORITY-CHAIN-001"
        - "READY-CAPABILITY-ASSESSMENTS-001"
        - "READY-HUMAN-PRODUCTION-DECISION-001"
        - "READY-IMPLEMENTATION-PREREQUISITE-001"
        - "READY-OPERATING-EVIDENCE-001"
        - "READY-RECOVERY-EVIDENCE-001"
        - "READY-RULE-RESULTS-001"
        - "READY-RUNTIME-PRODUCERS-001"
        - "READY-SECURITY-ISOLATION-001"

  gates:
    - {gate_id: "READY-SOURCE-MANIFEST-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_COMMITTED_SOURCE_MANIFEST", freshness_rule: "PINNED_CLEAN_EVALUATION_COMMIT_AND_UNCHANGED_GOVERNED_PATHS_ON_CLEAN_DESCENDANT_HEAD", bridge_rule_id: "BRIDGE-READY-SOURCE-MANIFEST-001", noncompensating: true}
    - {gate_id: "READY-GENERATED-MANIFEST-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_GENERATED_OUTPUT_MANIFEST", freshness_rule: "DERIVED_FROM_CURRENT_GOVERNED_SOURCE_MANIFEST", bridge_rule_id: "BRIDGE-READY-GENERATED-MANIFEST-001", noncompensating: true}
    - {gate_id: "READY-CONTRACT-VALIDATION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "DETERMINISTIC_COMPILER_VALIDATOR_REPORT", freshness_rule: "ZERO_VIOLATIONS_NO_STALE_OUTPUT_OR_DENOMINATOR", bridge_rule_id: "BRIDGE-READY-CONTRACT-VALIDATION-001", noncompensating: true}
    - {gate_id: "READY-FORK-PREFLIGHT-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "SDLC_FORK_000_GATE_EVALUATION", freshness_rule: "EVALUATION_COMMIT_CLEAN_UPSTREAM_DERIVED_AND_CURRENT_HEAD_CLEAN_DESCENDANT", bridge_rule_id: "BRIDGE-READY-FORK-PREFLIGHT-001", noncompensating: true}
    - {gate_id: "READY-TDD-CYCLE-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "REAL_TDD_CYCLE_RECORD_V1", freshness_rule: "CURRENT_NON_SYNTHETIC_GATED_PASS", bridge_rule_id: "BRIDGE-READY-TDD-CYCLE-001", noncompensating: true}
    - {gate_id: "READY-LANDING-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "SEPARATE_LANDING_RECORD_V1", freshness_rule: "EXACTLY_ONE_SUCCEEDED_FOR_TDD_CANDIDATE", bridge_rule_id: "BRIDGE-READY-LANDING-001", noncompensating: true}
    - {gate_id: "READY-SEALING-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "POST_LANDING_SEALING_VALIDATION", freshness_rule: "LANDED_EVALUATION_COMMIT_TREE_AND_ALL_GOVERNED_INPUT_DIGESTS_CURRENT", bridge_rule_id: "BRIDGE-READY-SEALING-001", noncompensating: true}
    - {gate_id: "READY-HY3-REVIEW-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "OPENCODE_HY3_FINAL_STRUCTURAL_REVIEW", freshness_rule: "POST_SEAL_READ_ONLY_CURRENT_ROUTE_AND_MODEL", bridge_rule_id: "BRIDGE-READY-HY3-REVIEW-001", noncompensating: true}
    - {gate_id: "READY-DEEPSEEK-REVIEW-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "OPENCODE_DEEPSEEK_V4_PRO_STRUCTURAL_REVIEW", freshness_rule: "POST_SEAL_READ_ONLY_CURRENT_ROUTE_AND_MODEL", bridge_rule_id: "BRIDGE-READY-DEEPSEEK-REVIEW-001", noncompensating: true}
    - {gate_id: "READY-FINDING-RECONCILIATION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "EXACT_REVIEW_FINDING_RECONCILIATION", freshness_rule: "NO_UNRESOLVED_P0_OR_P1_AND_ALL_P2_P3_RETAINED", bridge_rule_id: "BRIDGE-READY-FINDING-RECONCILIATION-001", noncompensating: true}
    - {gate_id: "READY-HUMAN-START-DECISION-001", tier_id: "READINESS-TIER-IMPLEMENTATION-START-001", required_result: "PASS", evidence_role: "AUTHENTICATED_IMPLEMENTATION_START_DECISION", freshness_rule: "ISSUED_AFTER_ALL_NON_DECISION_TIER_EVIDENCE_AND_NOT_REVOKED_OR_SUPERSEDED", bridge_rule_id: "BRIDGE-READY-HUMAN-START-DECISION-001", noncompensating: true}
    - {gate_id: "READY-IMPLEMENTATION-PREREQUISITE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "CURRENT_IMPLEMENTATION_START_READINESS_ASSESSMENT", freshness_rule: "CURRENT_TIER1_ASSESSMENT_WITH_IDENTICAL_READINESS_BASIS_DIGEST", bridge_rule_id: "BRIDGE-READY-IMPLEMENTATION-PREREQUISITE-001", noncompensating: true}
    - {gate_id: "READY-RUNTIME-PRODUCERS-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "ENACTED_RUNTIME_PRODUCER_AND_OWNERSHIP_EVIDENCE", freshness_rule: "ALL_ACTIVE_PRODUCERS_CURRENT_AND_CROSS_PRODUCER_FORGERY_DENIED", bridge_rule_id: "BRIDGE-READY-RUNTIME-PRODUCERS-001", noncompensating: true}
    - {gate_id: "READY-RULE-RESULTS-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "ARCHITECTURE_RULE_RESULT_RECONCILIATION", freshness_rule: "EXACT_64_ROWS_CURRENT_COMPLETE_AND_NO_BLOCKING_RESULT", bridge_rule_id: "BRIDGE-READY-RULE-RESULTS-001", noncompensating: true}
    - {gate_id: "READY-ADOPTION-GATES-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "PROCESS_AND_APPLICABLE_FLEET_ADOPTION_GATE_SET", freshness_rule: "SDLC_ADOPT_A_THROUGH_E_AND_EVERY_APPLICABLE_SPECIALIZED_GATE_PASS", bridge_rule_id: "BRIDGE-READY-ADOPTION-GATES-001", noncompensating: true}
    - {gate_id: "READY-SECURITY-ISOLATION-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "SECURITY_PRIVACY_SANDBOX_BYPASS_AND_INDEPENDENCE_EVIDENCE", freshness_rule: "TARGET_HOST_ROUTE_MODEL_TOOL_SANDBOX_AND_DATA_CLASS_CURRENT", bridge_rule_id: "BRIDGE-READY-SECURITY-ISOLATION-001", noncompensating: true}
    - {gate_id: "READY-OPERATING-EVIDENCE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "RELEASE_CANDIDATE_REHEARSAL_OBSERVATION_AND_SERVICE_ACCEPTANCE_EVIDENCE", freshness_rule: "QUALIFIED_TARGET_EQUIVALENT_ENVIRONMENT_AND_DECLARED_WINDOW", bridge_rule_id: "BRIDGE-READY-OPERATING-EVIDENCE-001", noncompensating: true}
    - {gate_id: "READY-RECOVERY-EVIDENCE-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "BACKUP_RESTORE_ROLLBACK_INCIDENT_AND_RECONCILIATION_EVIDENCE", freshness_rule: "QUALIFIED_TARGET_ENVIRONMENT_AND_CURRENT_RUNBOOKS", bridge_rule_id: "BRIDGE-READY-RECOVERY-EVIDENCE-001", noncompensating: true}
    - {gate_id: "READY-CAPABILITY-ASSESSMENTS-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "APPLICABLE_VITAL_CONTROL_AND_DOMAIN_ASSESSMENT_SET", freshness_rule: "EVERY_APPLICABLE_TUPLE_CURRENT_SCORED_OR_APPROVED_NOT_APPLICABLE_NO_UNKNOWN", bridge_rule_id: "BRIDGE-READY-CAPABILITY-ASSESSMENTS-001", noncompensating: true}
    - {gate_id: "READY-AUTHORITY-CHAIN-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "AUTHENTICATED_GOVERNANCE_DECISION_AND_AUTHORITY_QUALIFICATION_EVIDENCE", freshness_rule: "CURRENT_EXACT_SUBJECT_NO_SELF_APPROVAL_OR_BYPASS", bridge_rule_id: "BRIDGE-READY-AUTHORITY-CHAIN-001", noncompensating: true}
    - {gate_id: "READY-HUMAN-PRODUCTION-DECISION-001", tier_id: "READINESS-TIER-PRODUCTION-001", required_result: "PASS", evidence_role: "AUTHENTICATED_PRODUCTION_READINESS_DECISION", freshness_rule: "ISSUED_AFTER_ALL_NON_DECISION_PRODUCTION_EVIDENCE_AND_NOT_REVOKED_OR_SUPERSEDED", bridge_rule_id: "BRIDGE-READY-HUMAN-PRODUCTION-DECISION-001", noncompensating: true}

  evidence_bridge_contract:
    additional_properties: false
    exact_population_rule: "bridge_rule_by_gate keys equal the 21 gate IDs exactly; every gate bridge_rule_id equals its row and no rule is shared, omitted, duplicated, or caller-selected"
    native_subject_class_rules:
      ARCHITECTURE_SUBJECT: "native schema is architecture-subject/v1; ref/digest/manifest digest equal the independently resolved ARCHITECTURE_SUBJECT and ARCHITECTURE_SUBJECT_MANIFEST entries in the closed readiness manifest"
      TDD_EXACT_SUBJECT: "native schema is exact-subject/v1; ref/digest/manifest tuple equals the exact TddCycleRecordV1 subject and its schema-governed manifest nullability"
      TIER1_READINESS_SUBJECT: "native schema is readiness-subject/v1; native ref/digest/manifest resolve an independently valid Tier 1 subject and manifest"
      TIER2_READINESS_SUBJECT: "native schema is readiness-subject/v1; native ref/digest/manifest equal the containing Tier 2 readiness subject exactly"
      TIER2_RUNTIME_RELEASE_SUBJECT: "native schema is exact-subject/v1; native ref/digest/manifest equal all containing Tier 2 tier_evidence_subject_* fields and the closed manifest TIER_EVIDENCE_SUBJECT entry"
    bridge_rule_by_gate:
      READY-ADOPTION-GATES-001: {bridge_rule_id: "BRIDGE-READY-ADOPTION-GATES-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native schema/ref/digest/manifest equals all Tier 2 tier_evidence_subject_* fields; evidence is the complete exact adoption-gate reconciliation for that release subject"}
      READY-AUTHORITY-CHAIN-001: {bridge_rule_id: "BRIDGE-READY-AUTHORITY-CHAIN-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds only authority qualification, not a release grant or permit"}
      READY-CAPABILITY-ASSESSMENTS-001: {bridge_rule_id: "BRIDGE-READY-CAPABILITY-ASSESSMENTS-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence is a complete population reconciliation whose members bind the same scope, window, service, and value stream"}
      READY-CONTRACT-VALIDATION-001: {bridge_rule_id: "BRIDGE-READY-CONTRACT-VALIDATION-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence_digest equals contract_validation_report_digest and the report binds source_manifest_digest plus generated_manifest_digest"}
      READY-DEEPSEEK-REVIEW-001: {bridge_rule_id: "BRIDGE-READY-DEEPSEEK-REVIEW-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence is the exact post-seal DeepSeek V4 Pro verdict binding both manifests, validation report, evaluation commit/tree, route, and model"}
      READY-FINDING-RECONCILIATION-001: {bridge_rule_id: "BRIDGE-READY-FINDING-RECONCILIATION-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence reconciles the exact HY3 and DeepSeek verdict digests with complete open/resolved finding populations"}
      READY-FORK-PREFLIGHT-001: {bridge_rule_id: "BRIDGE-READY-FORK-PREFLIGHT-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence_digest equals fork_preflight_digest and proves evaluation commit/tree clean and upstream-derived plus current-head clean descendant ancestry"}
      READY-GENERATED-MANIFEST-001: {bridge_rule_id: "BRIDGE-READY-GENERATED-MANIFEST-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence_digest equals generated_manifest_digest and binds source_manifest_digest"}
      READY-HUMAN-PRODUCTION-DECISION-001: {bridge_rule_id: "BRIDGE-READY-HUMAN-PRODUCTION-DECISION-001", native_subject_class: "TIER2_READINESS_SUBJECT", relation_rule: "native schema/ref/digest/manifest equals the containing Tier 2 readiness subject exactly; evidence_digest equals the assessment human_decision_digest"}
      READY-HUMAN-START-DECISION-001: {bridge_rule_id: "BRIDGE-READY-HUMAN-START-DECISION-001", native_subject_class: "TIER1_READINESS_SUBJECT", relation_rule: "native schema/ref/digest/manifest equals the containing Tier 1 readiness subject exactly; evidence_digest equals the assessment human_decision_digest"}
      READY-HY3-REVIEW-001: {bridge_rule_id: "BRIDGE-READY-HY3-REVIEW-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence is the exact post-seal HY3 verdict binding both manifests, validation report, evaluation commit/tree, route, and model"}
      READY-IMPLEMENTATION-PREREQUISITE-001: {bridge_rule_id: "BRIDGE-READY-IMPLEMENTATION-PREREQUISITE-001", native_subject_class: "TIER1_READINESS_SUBJECT", relation_rule: "native subject is Tier 1 with all tier_evidence_subject_* fields null; its readiness_basis_digest equals the containing Tier 2 basis, its subject ref/digest necessarily differ, and evidence_digest equals the unique current Tier 1 PASS assessment digest"}
      READY-LANDING-001: {bridge_rule_id: "BRIDGE-READY-LANDING-001", native_subject_class: "TDD_EXACT_SUBJECT", relation_rule: "native exact subject equals the TDD cycle subject; candidate commit/tree equals source_commit_sha1/source_tree_oid_sha1 and evidence is the unique separate SUCCEEDED LandingRecord for that cycle"}
      READY-OPERATING-EVIDENCE-001: {bridge_rule_id: "BRIDGE-READY-OPERATING-EVIDENCE-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds the built-once artifact, intended destination, qualified target-equivalent environment, and declared observation window"}
      READY-RECOVERY-EVIDENCE-001: {bridge_rule_id: "BRIDGE-READY-RECOVERY-EVIDENCE-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds backup, restore, rollback, incident, and reconciliation results for that release subject"}
      READY-RULE-RESULTS-001: {bridge_rule_id: "BRIDGE-READY-RULE-RESULTS-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence contains exactly 18 ORG, 26 TDD, 10 ADR-0009, and 10 ADR-0010 current nonblocking rows"}
      READY-RUNTIME-PRODUCERS-001: {bridge_rule_id: "BRIDGE-READY-RUNTIME-PRODUCERS-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence covers every active registered producer and proves cross-producer forgery denial"}
      READY-SEALING-001: {bridge_rule_id: "BRIDGE-READY-SEALING-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence binds the unique landing, evaluation commit/tree, source/generated manifests, validation report, and all current input digests"}
      READY-SECURITY-ISOLATION-001: {bridge_rule_id: "BRIDGE-READY-SECURITY-ISOLATION-001", native_subject_class: "TIER2_RUNTIME_RELEASE_SUBJECT", relation_rule: "native tuple equals all Tier 2 tier_evidence_subject_* fields; evidence binds target host, route, model, tools, sandbox, bypass matrix, privacy, and data class"}
      READY-SOURCE-MANIFEST-001: {bridge_rule_id: "BRIDGE-READY-SOURCE-MANIFEST-001", native_subject_class: "ARCHITECTURE_SUBJECT", relation_rule: "native digest/manifest equals architecture_subject_digest/architecture_subject_manifest_digest; evidence_digest equals source_manifest_digest and proves bytewise exact governed paths at the evaluation commit and unchanged bytes on the clean descendant head"}
      READY-TDD-CYCLE-001: {bridge_rule_id: "BRIDGE-READY-TDD-CYCLE-001", native_subject_class: "TDD_EXACT_SUBJECT", relation_rule: "native subject is the real nonsynthetic TddCycleRecordV1 subject; candidate commit/tree equals source_commit_sha1/source_tree_oid_sha1 and cycle result is current GATED/PASS"}

  human_decision_contract:
    schema_ref: "schemas/authority/human-decision-v1.schema.json"
    artifact_type: "human_decision"
    status: "APPROVED"
    outcome: "APPROVED"
    exact_decision_kind_by_tier:
      READINESS-TIER-IMPLEMENTATION-START-001: "WORK_TRANSITION"
      READINESS-TIER-PRODUCTION-001: "RELEASE_OR_MIGRATION"
    exact_action_by_tier:
      READINESS-TIER-IMPLEMENTATION-START-001: "AUTHORIZE_STAGED_IMPLEMENTATION_START"
      READINESS-TIER-PRODUCTION-001: "APPROVE_PRODUCTION_READINESS"
    exact_bindings:
      - "subject schema/ref/digest and canonical_argument_digest equal the independently derived tier-specific READINESS_SUBJECT_V1; its readiness_basis_digest is independently recomputed"
      - "subject_manifest_digest equals the exact readiness subject manifest digest"
      - "destination equals repository_id; adapter_id equals policy; adapter_version is release-pinned"
      - "principal resolves one authenticated current human-governor assignment for this repository and tier"
      - "scope is the duplicate-free exact set of repository_id, tier_id, source_commit_sha1, and source_tree_oid_sha1"
      - "issued_at is strictly after every non-human-decision required gate evidence observation/admission instant; its own artifact registration and human-decision gate observation are at or after issued_at and no later than the assessment observed_at"
      - "expires_at equals the exact subject assessment_window_end, the assessment valid_until is no later than expires_at, and revoked_at is null"
      - "supersedes is null for the first decision and otherwise names the one prior same-repository, same-tier decision invalidated by this exact reassessment"
      - "digest, authentication context, presentation challenge, nonce, and artifact-registry row independently resolve and are current"
    denial_rule: "A denied, expired, revoked, superseded, wrong-subject, wrong-tier, wrong-role, noncausal, or duplicate decision produces no READY transition."
    effect_boundary: "Neither decision issues a work/effect grant or permit, lands code, releases, deploys, waives a gate, or proves an outcome."

  reviewer_contract:
    required_roles:
      - reviewer_role_id: "OPENCODE_HY3_FINAL_STRUCTURAL_REVIEW"
        independence: "READ_ONLY_NO_CANONICAL_WRITE_NO_LANDING_DISTINCT_ATTEMPT"
        route_binding: "exact provider route and full model identity recorded"
      - reviewer_role_id: "OPENCODE_DEEPSEEK_V4_PRO_STRUCTURAL_REVIEW"
        independence: "READ_ONLY_NO_CANONICAL_WRITE_NO_LANDING_DISTINCT_ATTEMPT"
        route_binding: "exact provider route and full model identity recorded"
    common_predicates:
      - "Both reviews occur after sealing and bind the identical source manifest, generated manifest, validation report, commit, tree, architecture subject, and readiness subject."
      - "A review generated before any bound byte, digest, route, or subject change is stale."
      - "Reviewer agreement cannot compensate for failed deterministic evidence or create authority."
      - "Every observation has a stable severity, exact source location, invariant, consequence, and disposition."
      - "No unresolved P0 or P1 remains; every P2/P3 stays visible and owned."

  bootstrap_lane:
    lane_id: "PRE_READINESS_TOOLING_TRACER"
    current_authorization: "NOT_GRANTED_BY_THIS_DEFINITION"
    allowed_scope:
      - "CONTRACT_COMPILER_GENERATOR_VALIDATOR_SCHEMA_FIXTURE_AND_MANIFEST"
      - "FORK_PRESERVATION_PROVENANCE_AND_CLEAN_SUBJECT_PREPARATION"
      - "ONE_REAL_CURRENT_SUBJECT_TDD_LANDING_AND_SEALING_TRACER"
      - "READ_ONLY_REVIEW_AND_FINDING_RECONCILIATION"
    forbidden_scope:
      - "PRODUCT_CAPABILITY_IMPLEMENTATION"
      - "PRODUCT_RUNTIME_ACTIVATION"
      - "PRODUCTION_OR_USER_DATA"
      - "RELEASE_OR_DEPLOYMENT"
      - "READINESS_SELF_APPROVAL"
      - "GATE_OR_AUTHORITY_BYPASS"
    termination: "SUCCESS_FAILURE_EXPIRY_SCOPE_DRIFT_OR_UNREGISTERED_PATH_ENDS_THE_TRACER"

  resolver_contract:
    resolver_id: "READINESS-TIER-RESOLVER-1.0"
    required_sources:
      - {role: "CATALOG", source: "exact ADR-0012 source projection"}
      - {role: "SUBJECT", source: "independently derived READINESS_SUBJECT_V1"}
      - {role: "SUBJECT_MANIFEST", source: "independently derived closed READINESS_SUBJECT_MANIFEST_V1"}
      - {role: "EVIDENCE_BINDINGS", source: "complete exact per-gate ReadinessEvidenceBindingV1 population"}
      - {role: "SOURCE_MANIFEST", source: "configuration-management governed-path manifest at the clean evaluation commit and current clean descendant head"}
      - {role: "GENERATED_MANIFEST", source: "compiler-owned exact generated-output manifest"}
      - {role: "VALIDATION", source: "deterministic compiler and validator report"}
      - {role: "FORK", source: "SDLC-FORK-000 exact gate evaluation"}
      - {role: "TDD_LANDING_SEAL", source: "ADR-0008 cycle, separate LandingRecord, and post-landing seal"}
      - {role: "REVIEWS", source: "both required read-only structural review verdicts"}
      - {role: "FINDINGS", source: "complete exact finding and reconciliation registry"}
      - {role: "RUNTIME_ASSURANCE", source: "one canonical runtime status plus exact runtime evidence when status is ASSESSED_PASS, ASSESSED_FAIL, or CONFLICT"}
      - {role: "CAPABILITY_ASSESSMENTS", source: "applicable control/domain assessment registries"}
      - {role: "TRACE", source: "same-subject Core SDLC trace"}
      - {role: "DECISION", source: "authenticated HumanDecisionRecord and artifact registry"}
      - {role: "STATE_HISTORY", source: "complete append-only readiness assessment, supersession, and TransitionEventV1 history"}
      - {role: "TIME", source: "trusted UTC clock"}
    evaluation_order:
      - "SCHEMA_AND_EXACT_SET"
      - "SUBJECT_BASIS_IDENTITY_AND_MANIFEST_DERIVATION"
      - "NATIVE_SUBJECT_EVIDENCE_BRIDGES"
      - "SOURCE_GENERATED_AND_VALIDATION"
      - "FORK_TDD_LANDING_AND_SEAL"
      - "INDEPENDENT_REVIEWS_AND_FINDINGS"
      - "TIER_PREREQUISITE_BASIS_AND_RUNTIME_ASSURANCE"
      - "CAPABILITY_AND_OPERATIONAL_ASSURANCE"
      - "HUMAN_DECISION"
      - "FRESHNESS_AND_INVALIDATION"
      - "ASSESSMENT_SUPERSESSION_AND_STATE_HISTORY"
      - "ATOMIC_TRANSITION_FACT"
      - "AUTHORITY_BOUNDARY"
    fail_closed_on:
      - "missing, extra, duplicate, reordered, unknown, malformed, stale, expired, revoked, superseded, wrong-subject, wrong-native-subject, wrong-bridge, wrong-manifest, wrong-version, wrong-digest, dirty, uncommitted, non-descendant, synthetic-as-live, noncausal, self-approved, or unresolved input"
      - "an unresolved P0 or P1 finding"
      - "runtime UNKNOWN, ASSESSED_FAIL, or CONFLICT for Tier 1; runtime anything except ASSESSED_PASS for Tier 2"
      - "a missing, edited, forked, cyclic, duplicate-version, or gap-bearing assessment/supersession/transition history"
      - "an attempt to use a readiness result as a work transition, grant, permit, landing, release, deployment, waiver, or outcome"
    optional_or_fixture_only_bypass: false

  sad_path_transitions:
    - {condition: "TIER1_REQUIRED_INPUT_NOT_PASS", from_states: ["IMPLEMENTATION_START_EVALUATING"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
    - {condition: "DIRTY_UNCOMMITTED_OR_WRONG_ANCESTRY", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
    - {condition: "SYNTHETIC_TDD_OR_MISSING_SEPARATE_SUCCEEDED_LANDING_OR_SEAL", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
    - {condition: "MISSING_STALE_OR_NONINDEPENDENT_REQUIRED_REVIEW", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
    - {condition: "UNRESOLVED_P0_OR_P1", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
    - {condition: "RUNTIME_NOT_ASSESSED_AT_TIER1", from_states: ["IMPLEMENTATION_START_EVALUATING"], to_state: "IMPLEMENTATION_START_EVALUATING", effect: "EXPLICIT_NONPASS_RUNTIME_FACT_RETAINED"}
    - {condition: "TIER1_RUNTIME_UNKNOWN_ASSESSED_FAIL_OR_CONFLICT", from_states: ["IMPLEMENTATION_START_EVALUATING", "IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "NO_AUTHORIZATION"}
    - {condition: "TIER2_RUNTIME_NOT_ASSESSED_UNKNOWN_ASSESSED_FAIL_OR_CONFLICT", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
    - {condition: "RULE_RESULT_DENOMINATOR_NOT_EXACTLY_64_OR_ANY_BLOCKING_RESULT", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
    - {condition: "RUNTIME_PRODUCER_MISSING_WRONG_OWNER_OR_CROSS_PRODUCER_FORGERY", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
    - {condition: "OPERATIONAL_RECOVERY_SECURITY_SCORE_OR_AUTHORITY_EVIDENCE_INCOMPLETE", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "NO_RELEASE_OR_DEPLOYMENT_ELIGIBILITY"}
    - {condition: "IMPLEMENTATION_START_PREREQUISITE_INVALIDATED", from_states: ["PRODUCTION_EVALUATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "BOTH_TIERS_INELIGIBLE"}
    - {condition: "TIER1_GOVERNED_BASELINE_MANIFEST_BRIDGE_OR_BOUND_DIGEST_CHANGED", from_states: ["IMPLEMENTATION_START_READY", "PRODUCTION_EVALUATING", "PRODUCTION_BLOCKED", "PRODUCTION_READY"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "BOTH_TIERS_REQUIRE_FRESH_REASSESSMENT"}
    - {condition: "TIER2_ONLY_SUBJECT_MANIFEST_BRIDGE_OR_BOUND_DIGEST_CHANGED", from_states: ["PRODUCTION_READY"], to_state: "PRODUCTION_BLOCKED", effect: "PRODUCTION_TIER_REQUIRES_FRESH_REASSESSMENT"}
    - {condition: "BOOTSTRAP_TRACER_SCOPE_DRIFT_OR_EXPIRY", from_states: ["NOT_ASSESSED", "IMPLEMENTATION_START_EVALUATING"], to_state: "IMPLEMENTATION_START_BLOCKED", effect: "TRACER_TERMINATED_NO_AUTHORIZATION"}

  fixture_contract:
    evidence_scope: "SYNTHETIC_CONTRACT_SATISFIABILITY_ONLY"
    runtime_claim: "NOT_ASSESSED"
    positive_case_requirements:
      tier1_exact_pass_with_explicit_runtime_not_assessed: 1
      tier1_retained_after_authorized_clean_descendant_product_landing_with_unchanged_governed_manifest: 1
      tier2_exact_pass_after_current_tier1_and_complete_runtime_evidence: 1
      invalidated_tier_reassessed_on_new_exact_subject: 1
      exact_positive_case_count: 4
    negative_case_requirements:
      missing_gate: 1
      extra_gate: 1
      duplicate_or_reordered_gate: 1
      wrong_subject_or_manifest: 1
      stale_or_expired_evidence: 1
      dirty_or_uncommitted_fork: 1
      fork_preflight_not_pass: 1
      synthetic_tdd_claimed_as_live: 1
      tdd_not_gated_or_not_pass: 1
      landing_missing_duplicate_or_not_succeeded: 1
      sealing_missing_or_wrong_landed_tree: 1
      hy3_review_missing_stale_or_wrong_subject: 1
      deepseek_review_missing_stale_or_wrong_subject: 1
      reviewer_not_independent_or_has_write_authority: 1
      unresolved_p0_or_p1: 1
      human_decision_missing_wrong_subject_noncausal_revoked_or_superseded: 1
      direct_not_assessed_to_ready_transition: 1
      production_without_current_tier1: 1
      production_runtime_not_assessed_or_unknown: 1
      production_rule_denominator_or_result_failure: 1
      production_runtime_producer_or_ownership_failure: 1
      production_operational_recovery_security_or_score_failure: 1
      readiness_used_as_grant_permit_release_or_deployment: 1
      bootstrap_tracer_scope_escalation: 1
      cross_subject_or_wrong_native_evidence_bridge: 1
      readiness_subject_manifest_missing_extra_duplicate_reordered_or_forged: 1
      runtime_status_unknown_invalid_or_tier_ineligible: 1
      edited_forked_cyclic_duplicate_version_or_gap_bearing_state_history: 1
      exact_negative_case_count: 28

  current_standing:
    assessment_record_count: 0
    subject_manifest_count: 0
    evidence_binding_count: 0
    transition_fact_count: 0
    implementation_start_state: "NOT_ASSESSED"
    production_state: "NOT_ASSESSED"
    implementation_start_authorized: false
    production_authorized: false
    runtime_validation_status: "NOT_ASSESSED"
    capability_score: null
```

<!-- END ADR12 READINESS TIER CONTRACT -->

## Resolver and authority rules

The resolver independently derives the readiness subject and gate population;
the caller cannot supply a favorable state or omit an unfavorable row. All
evidence, reviews, findings, and decisions bind the tier's exact subject. A
prior-tier assessment has its necessarily different tier-specific subject but
must bind the identical independently derived `readiness_basis_digest`.
Evidence from a dirty checkout, a different commit/tree, an uncommitted
generated output, a synthetic fixture, or an earlier review subject cannot be
relabeled as current unless its native subject and exact relation are the ones
required by that gate's registered bridge rule. A Tier 2 runtime subject and a
Tier 1 TDD/landing subject therefore retain their own identities; the bridge
does not rewrite them into a readiness subject.

A `PASS` assessment is a prerequisite fact, not an effect capability:

- `IMPLEMENTATION_START_READY` allows `work_management` to admit staged
  implementation work only through the normal state, packet, gate, authority,
  TDD, review, and landing path.
- `PRODUCTION_READY` allows the release path to evaluate a release/deployment
  request. It does not issue an `AuthorityGrant`, `Permit`, release, deployment,
  or operational acceptance.
- A readiness decision cannot change a failed gate, waive a security or
  recovery requirement, convert `NOT_ASSESSED` to `PASS`, or establish a
  capability score.

Every ready assessment is invalidated for future reliance when any bound
governed-baseline source or generated byte, subject, manifest, validation
report, fork/ancestry fact, evidence bridge, cycle, landing, seal, review,
finding, runtime producer, rule result, environment, capability assessment,
authority record, or validity window changes. An ordinary authorized product
implementation commit on a clean descendant does not invalidate Tier 1 while
the governed design/control manifest remains byte-identical; that work remains
subject to its own packet, TDD, gate, authority, review, and landing controls.
A changed Tier 2 runtime-release subject invalidates Tier 2 without erasing an
otherwise current Tier 1 result. Reassessment creates a new immutable record,
decision, and transition fact; prior bytes remain historical.

## Sad paths and recovery

Failure is visible and tier-specific:

- a Tier 1 defect moves or keeps the subject at
  `IMPLEMENTATION_START_BLOCKED`; no staged product implementation is
  authorized;
- a runtime-only Tier 2 defect moves or keeps the subject at
  `PRODUCTION_BLOCKED`; staged implementation may continue only while the
  identical Tier 1 result remains current;
- invalidation of the Tier 1 prerequisite makes both tiers ineligible;
- missing or insufficient evidence is `UNKNOWN` or `FAIL`, never zero, pass,
  or “mostly ready”; and
- recovery always opens a fresh exact-subject assessment. Editing, backdating,
  or reusing the prior assessment or human decision is forbidden.

## Compatibility and documentation migration

Existing documents are migrated as follows:

- “paper construction contract,” “definition freeze,” and “contract ready”
  describe inputs to `IMPLEMENTATION_START_READY`; they are not readiness
  states by themselves.
- Earlier “enterprise build ready” language that required enacted runtime
  evidence is mapped to `PRODUCTION_READY`.
- A bounded readiness tooling tracer is allowed before Tier 1 only under this
  ADR's narrow bootstrap rule. It is not product implementation readiness.
- The 64 ADR-0007–ADR-0010 architecture-rule assessment rows remain the exact
  runtime rule denominator for Tier 2. ADR-0012 readiness gates are a separate
  prerequisite set and do not silently change that denominator.
- Historical review prose is not rewritten into a pass. New assessments cite
  the historical record and record the new canonical state.

## Noncompensating fitness functions

| ID | Required result |
|---|---|
| `FF-READINESS-NAMESPACE-001` | Every readiness statement resolves exactly one canonical ADR-0012 state; ambiguous “build/enterprise/runtime ready” text has no machine or authority effect. |
| `FF-READINESS-TIER1-001` | Tier 1 accepts only one exact clean committed governed source/generated baseline with a closed subject manifest, deterministic zero-drift validation, `SDLC-FORK-000: PASS`, one real current GATED/PASS TDD cycle, one separate `SUCCEEDED` landing, a current seal, both required same-subject read-only reviews, exact native-subject bridges, zero unresolved P0/P1, and one causal authenticated human decision. |
| `FF-READINESS-TIER2-001` | Tier 2 accepts only a current Tier 1 result with the identical readiness-basis digest plus one exact runtime-release subject, enacted producer enforcement, exactly 64 reconciled rule results, all required adoption/security/operational/recovery evidence, native-subject bridges, applicable capability assessments and authority, and one causal authenticated production-readiness decision. |
| `FF-READINESS-INVALIDATION-001` | Any bound governed baseline, subject, manifest, bridge, finding, validity, producer, rule, environment, score, or authority change invalidates the affected tier and requires a new immutable assessment/transition; no cached, edited, or cross-subject pass survives. An ordinary clean descendant product commit with unchanged governed baseline remains under per-work controls and does not circularly revoke Tier 1. |
| `FF-READINESS-AUTHORITY-001` | Tier 1 only admits normally governed staged implementation and Tier 2 only admits evaluation of the normal release path; neither result can mutate work, issue a grant/permit, land, release, deploy, waive evidence, or claim outcome. |
| `FF-READINESS-BOOTSTRAP-001` | Before Tier 1, only a bounded architecture/tooling readiness tracer is possible under ordinary task/effect controls; product implementation, runtime activation, production data, release, deployment, self-approval, and scope drift are denied. |

## Alternatives considered

1. **Use one `BUILD_READY` boolean.** Rejected because it conflates paper
   definition, permission to begin staged construction, runtime enactment, and
   production safety.
2. **Require full runtime evidence before any implementation starts.**
   Rejected as circular: runtime evidence cannot exist before bounded
   implementation, yet absent evidence must remain visible.
3. **Let document validation alone authorize product implementation.**
   Rejected because clean fork provenance, one real cycle/landing/seal,
   independent review, finding closure, and human authority are
   noncompensating Tier 1 requirements.
4. **Treat Tier 1 as a partial production score.** Rejected. It has no
   production or maturity meaning and may explicitly retain runtime
   `NOT_ASSESSED`.
5. **Allow the readiness assessment to issue permits or deploy.** Rejected
   because readiness evidence and effect authority must remain separate.

## Consequences and evidence standing

The compiler must project the exact catalog, closed subject manifest,
native-subject bridge contract, assessment schema, empty initial assessment
registry, append-only transition contract, state transitions, gate set, and
fixture denominators.
The validator must reject every forbidden transition and mutation listed
above. The accepted-ADR registry, architecture-element inventory, source of
truth, practice profile, licensing manifest, and readiness terminology must
include this ADR without implying a readiness pass.

The current repository has no `ReadinessAssessmentV1` record. The catalog's
initial standing is therefore authoritative:

- `IMPLEMENTATION_START_READY`: `NOT_ASSESSED`, not authorized;
- `PRODUCTION_READY`: `NOT_ASSESSED`, not authorized; and
- runtime/capability score: `NOT_ASSESSED` / null.

The human owner accepts this separation and its bootstrap boundary. This
decision does not declare definition freeze, implementation-start readiness,
runtime enactment, production readiness, release eligibility, deployment
authority, or operational effectiveness.
