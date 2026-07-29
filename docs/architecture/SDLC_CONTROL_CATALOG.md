# Ranex SDLC Control Catalog

| Field | Value |
|---|---|
| Catalog ID | `CAT-SDLC-001` |
| Version | `1.6.0` |
| Status | `ACCEPTED`; implementation maturity is `R_AND_D` until adoption gates pass |
| Effective date | 2026-07-27 |
| Repository snapshot basis | `bootstrap/pre-upstream`; exact digest/revision is supplied by the review or release source manifest |
| Owner | Human governor |
| Parent policy | [Ranex Core SDLC Operating Model](./CORE_SDLC_OPERATING_MODEL.md) |
| Research | [Real-world SDLC operating model research](../research/real-world-sdlc-operating-model-research-2026-07-27.md) |
| Compatibility/migration class | New control catalog; older phases are inputs to a versioned crosswalk |
| Security/data class | Public control metadata; referenced evidence retains its own classification |

## 1. Purpose

This catalog makes the core operating model executable. It supplies stable
control IDs, common evidence systems, complete stage contracts, rejection
routes, tailoring rules, and source/evidence classifications.

`ACCEPTED` means the human owner selected the policy. It does not claim that
Ranex implements it, conforms to ISO/CMMI, or has completed an external
appraisal. Adoption-gate evidence reports implementation maturity separately.

## 2. Evidence classification

| Code | Meaning |
|---|---|
| `STD` | International consensus standard used as structural guidance |
| `GOV` | Government standard/handbook/recommendation |
| `OBS` | Repeated observational industry research |
| `PRAC` | Mature practitioner guidance and cases |
| `MODEL` | Capability/maturity assessment model |
| `OWNER` | Ranex owner requirement or design choice |

Major controls cite one or more classes. Evidence-informed does not mean
scientifically proven.

## 3. Cross-lifecycle control systems

### SDLC-PM-001 — Project management

Across every material work item or release:

```text
PLAN -> EXECUTE -> ASSESS_AND_CONTROL -> CLOSE
          ^                  |
          +---- correct/reforecast
```

The integrated plan contains scope, assumptions, estimate range, milestone
forecast, capacity/resources, dependencies, risk reserve, configuration,
quality, measurement, acceptance, delivery and closure criteria. The delivery
owner records actual-versus-plan variance, forecast-to-complete, corrective
action, owner/date, and risks/issues/decisions. A material scope, schedule,
capacity, cost, requirement or risk change requires human recommitment.
Closure records acceptance, handover, archive, residual risk and lessons.

Estimates express uncertainty and inform decisions. Point estimates and story
points are optional; individual estimate accuracy is not a performance measure.

Evidence basis: `STD` ISO/IEC 29110 Basic profile; `GOV` NASA-HDBK-2203;
`OWNER` Ranex tailoring.

### SDLC-EST-001 — Estimate and commitment separation

An estimate is an immutable uncertainty observation, never a promise. It names
one exact subject, unit, range, assumptions, method, evidence, and the capacity
and dependency snapshots under which the range was prepared. It has no
work-item-state, gate, decision, authority-grant, permit, landing, release, or
effect authority. A point value may appear only as the most-likely member of a
nonempty range; it cannot replace the range or erase uncertainty.

A delivery commitment exists only when an authenticated accountable human
records an `APPROVED` `HumanDecisionRecord` for the exact
`DELIVERY_COMMITMENT_SUBJECT_V1`. That subject binds the work item, integrated
plan and scope, every supporting estimate, capacity, dependencies, risk,
acceptance basis, accountable owner, commitment window, and the complete
recommit-trigger set. An estimate, forecast, plan, task packet, model response,
board date, chat message, or state transition cannot synthesize that decision.
The decision is an accountable planning choice; it does not itself turn a
failed gate into `PASS`, transition a work item, issue a grant or permit, or
prove delivery.

The exact recommit triggers are `SCOPE_CHANGED`, `ESTIMATE_BINDING_CHANGED`,
`ESTIMATE_EXPIRED`, `CAPACITY_CHANGED`, `DEPENDENCY_CHANGED`, `RISK_CHANGED`,
`ACCEPTANCE_BASIS_CHANGED`, and `COMMITMENT_WINDOW_EXPIRED`. Any trigger
invalidates the prior commitment for future reliance. Continuing requires a
new exact subject and a new authenticated human decision; editing a prior
estimate or decision is prohibited. This is noncompensating: no quantity of
other passing controls can make a missing, stale, cross-subject, expired,
revoked, denied, or superseded commitment current.

<!-- BEGIN SDLC ESTIMATE COMMITMENT CONTROL -->

```yaml
estimate_commitment_control:
  control_id: "SDLC-EST-001"
  control_version: "1.1.0"
  contract_id: "ESTIMATE-COMMITMENT-SEPARATION-1.1"
  contract_version: "1.1.0"
  contract_projection_ref: "architecture/contracts/estimate-commitment-control.json"
  contract_projection_id: "REG-ESTIMATE-COMMITMENT-CONTROL-001"
  contract_projection_contract:
    additional_properties: false
    envelope_fields: ["registry_id", "version", "status", "source_path", "source_fragment", "source_digest", "generated_by", "entries"]
    field_types:
      registry_id: {const: "REG-ESTIMATE-COMMITMENT-CONTROL-001"}
      version: {const: "1.1.0"}
      status: {const: "DEFINED_RUNTIME_NOT_ASSESSED"}
      source_path: {const: "docs/architecture/SDLC_CONTROL_CATALOG.md"}
      source_fragment: {const: "SDLC ESTIMATE COMMITMENT CONTROL"}
      source_digest: "sha256"
      generated_by: {const: "scripts/architecture/generate_contracts.py"}
      entries: "EstimateCommitmentControlV1_1[]"
    nullable_fields: []
    array_cardinalities: {entries: "exactly 1"}
    entry_rule: "entries[0] is the complete estimate_commitment_control mapping from this marked source block, including this projection contract; source_digest is computed over the exact UTF-8 YAML payload between the markers and is therefore outside entries."
    ordering_rule: "The envelope field set is closed; canonical JSON ordering is RFC8785 and entries preserve exactly one source mapping."
  applicability_rule_id: "APP-STAGE-001"
  owner_context: "work_management"
  decision_owner_context: "policy"
  canonicalization: "RFC8785"
  digest_algorithm: "SHA-256"
  digest_encoding: "sha256:<64 lowercase hex>"
  additional_properties: false
  noncompensating: true
  inherited_type_authority:
    source: "AI_ARTIFACT_CONTRACTS.md, schemas/authority/human-decision-v1.schema.json, and schemas/common/core-sdlc-trace-v1.schema.json"
    types: ["HumanDecisionRecord", "CoreSdlcTrace"]
  scalar_types:
    safe_id: "nonempty registered identifier with no path traversal"
    safe_id_or_registered_urn: "safe_id or registered urn:ranex identifier"
    sha256: "sha256:<64 lowercase hexadecimal characters>"
    strict_utc: "RFC3339 UTC instant with Z and no leap second"
    nonempty_string: "nonempty UTF-8 string"
    nonnegative_number: "finite JSON number >= 0"
    nonnegative_integer: "JSON integer >= 0"
    positive_integer: "JSON integer >= 1"
    ed25519_signature_base64url: "RFC4648 base64url without equals padding, exactly 86 characters and decoding to exactly 64 bytes"
  cardinality_rule:
    undeclared_default: "FORBIDDEN"
    declared_nonnullable_scalar_or_object: "1"
    declared_nullable_scalar_or_object: "0..1 represented by an explicit value or JSON null"
    array: "the record-specific range; the JSON key is still required"
  set_order_rule: "Every array is explicitly declared as a set or an ordered sequence. Every set-like business/source array is duplicate-free and bytewise ordered by its declared key over UTF-8 bytes; a declared sequence must match its exact order. No producer or resolver may silently deduplicate, sort, coerce, or discard an input array. An unknown, omitted, extra, duplicate, or out-of-order member fails."

  nested_types:
    - type_id: "ContentAddressBindingV1"
      additional_properties: false
      fields: ["ref", "digest"]
      field_types:
        ref: "safe_id_or_registered_urn"
        digest: "sha256"
      nullable_fields: []
      array_cardinalities: {}
      row_order: "BYTEWISE_REF"

    - type_id: "EstimateSourceEnvelopeAttestationV1"
      additional_properties: false
      fields: ["adapter_id", "adapter_version", "authority_manifest_ref", "authority_manifest_digest", "source_payload_digest", "presentation_challenge_digest", "nonce_digest", "replay_registry_ref", "replay_registry_digest", "replay_reservation_ref", "replay_reservation_digest", "authenticated_at", "valid_until", "signature_algorithm", "signing_key_ref", "signing_key_digest", "signature", "digest"]
      field_types:
        adapter_id: {const: "work_management.estimate_commitment_source_adapter"}
        adapter_version: {const: "2.0.0"}
        authority_manifest_ref: "safe_id_or_registered_urn"
        authority_manifest_digest: "sha256"
        source_payload_digest: "sha256"
        presentation_challenge_digest: "sha256"
        nonce_digest: "sha256"
        replay_registry_ref: "safe_id_or_registered_urn"
        replay_registry_digest: "sha256"
        replay_reservation_ref: "safe_id_or_registered_urn"
        replay_reservation_digest: "sha256"
        authenticated_at: "strict_utc"
        valid_until: "strict_utc"
        signature_algorithm: {const: "ED25519"}
        signing_key_ref: "safe_id_or_registered_urn"
        signing_key_digest: "sha256"
        signature: "ed25519_signature_base64url"
        digest: "sha256"
      nullable_fields: []
      array_cardinalities: {}
      invariants:
        - "authority_manifest_ref/digest resolves the authenticated canonical adapter, all eleven role-owner bindings, the replay-registry owner/history anchor, and the current nonrevoked Ed25519 verification-key ref/digest. authenticated_at equals the selected trusted TIME instant and is less than valid_until."
        - "replay_registry_ref/digest equals the canonical current EstimateSourceReplayAuthorityRegistryV1 publication in the authority manifest. replay_reservation_ref/digest resolves exactly the envelope's row in that complete registry and binds adapter, envelope, payload, challenge, nonce, and consumption time. The challenge/nonce pair is globally nonreusable."
        - "signature is the Ed25519 signature over the domain-separated RFC8785 UTF-8 object containing every field except signature and digest. digest is RFC8785 SHA-256 over every field except digest and therefore also binds the verified signature."

    - type_id: "EstimateEvidenceBindingV1"
      additional_properties: false
      fields: ["evidence_ref", "evidence_digest"]
      field_types:
        evidence_ref: "safe_id_or_registered_urn"
        evidence_digest: "sha256"
      nullable_fields: []
      array_cardinalities: {}
      row_order: "BYTEWISE_EVIDENCE_REF"

    - type_id: "EstimateBindingV1"
      additional_properties: false
      fields: ["estimate_id", "estimate_digest", "estimate_kind", "unit"]
      field_types:
        estimate_id: "safe_id"
        estimate_digest: "sha256"
        estimate_kind: {enum: ["ELAPSED_TIME", "EFFORT", "COST", "CAPACITY", "OTHER"]}
        unit: "nonempty_string"
      nullable_fields: []
      array_cardinalities: {}
      row_order: "BYTEWISE_ESTIMATE_ID"

  estimate_record:
    type_id: "EstimateObservationV1"
    type_version: "1.0.0"
    schema_ref: "schemas/planning/estimate-observation-v1.schema.json"
    additional_properties: false
    fields: ["schema_version", "record_type", "estimate_id", "work_item_id", "subject_schema", "subject_ref", "subject_digest", "estimate_kind", "unit", "lower_bound", "most_likely", "upper_bound", "confidence", "method_ref", "assumptions", "evidence_bindings", "capacity_snapshot_ref", "capacity_snapshot_digest", "dependency_snapshot_ref", "dependency_snapshot_digest", "prepared_by_principal_id", "observed_at", "valid_until", "supersedes_estimate_id", "digest"]
    field_types:
      schema_version: {const: "1"}
      record_type: {const: "ESTIMATE_OBSERVATION"}
      estimate_id: "safe_id"
      work_item_id: "safe_id"
      subject_schema: {const: "work-item-scope/v1"}
      subject_ref: "safe_id_or_registered_urn"
      subject_digest: "sha256"
      estimate_kind: {enum: ["ELAPSED_TIME", "EFFORT", "COST", "CAPACITY", "OTHER"]}
      unit: "nonempty_string"
      lower_bound: "nonnegative_number"
      most_likely: "nonnegative_number|null"
      upper_bound: "nonnegative_number"
      confidence: {enum: ["UNKNOWN", "LOW", "MEDIUM", "HIGH"]}
      method_ref: "safe_id_or_registered_urn"
      assumptions: "nonempty_string[]"
      evidence_bindings: "EstimateEvidenceBindingV1[]"
      capacity_snapshot_ref: "safe_id_or_registered_urn"
      capacity_snapshot_digest: "sha256"
      dependency_snapshot_ref: "safe_id_or_registered_urn"
      dependency_snapshot_digest: "sha256"
      prepared_by_principal_id: "safe_id"
      observed_at: "strict_utc"
      valid_until: "strict_utc"
      supersedes_estimate_id: "safe_id|null"
      digest: "sha256"
    nullable_fields: ["most_likely", "supersedes_estimate_id"]
    array_cardinalities:
      assumptions: "1..N"
      evidence_bindings: "1..N"
    array_order:
      assumptions: "BYTEWISE_UTF8"
      evidence_bindings: "BYTEWISE_EVIDENCE_REF"
    invariants:
      - "lower_bound < upper_bound; most_likely is JSON null or lower_bound < most_likely < upper_bound; observed_at < valid_until. Equality at either bound fails."
      - "digest is RFC8785 SHA-256 of every field except digest; estimate_id and digest are immutable and globally nonreusable."
      - "subject_schema is exactly work-item-scope/v1 and subject_ref/digest resolve the exact ScopeAuthorityRowV1. A successor preserves work_item_id, subject schema/ref/digest, estimate_kind, and unit."
      - "Each root estimate defines an immutable derived series ID equal to its own estimate_id; every successor inherits that root series ID through supersedes_estimate_id. Multiple concurrent series and CURRENT heads are allowed for one work item, including alternative estimates with the same series signature, but every series has at most one CURRENT head and the plan includes all heads."
      - "An estimate is CURRENT at a trusted instant only when observed_at <= instant < valid_until and no later admitted estimate names it in supersedes_estimate_id. A non-null supersedes_estimate_id names exactly one earlier-admitted estimate in the same derived series and work_item; observation/admission time strictly increases and each series graph is single-predecessor, single-successor, and acyclic."
      - "assumptions and evidence_bindings are exact duplicate-free bytewise sets; their received order must already be canonical."
      - "subject, capacity, dependency, method, preparer provenance, and every evidence binding independently resolve by exact ref and digest for the same work item and observation time."
      - "No EstimateObservationV1 field or status has gate, decision, state-transition, grant, permit, landing, release, or effect authority."

  source_authority_contract:
    source_contract_id: "ESTIMATE-COMMITMENT-SOURCE-AUTHORITY-2.0"
    source_contract_version: "2.0.0"
    compatibility_class: "BREAKING_SOURCE_ENVELOPE"
    rationale: "The former ESTIMATE role was an ungoverned list of EstimateObservationV1 rows. V2 is a closed content-addressed registry that also carries the complete reservation history and exact method, evidence, and preparer authorities. No list-to-registry coercion is permitted."

    source_envelope:
      type_id: "EstimateCommitmentSourceEnvelopeV2"
      type_version: "2.0.0"
      schema_ref: "schemas/planning/estimate-commitment-source-envelope-v2.schema.json"
      additional_properties: false
      fields: ["schema_version", "record_type", "envelope_id", "query_kind", "work_item_id", "sources", "source_payload_digest", "replay_reservation", "source_attestation", "digest"]
      field_types:
        schema_version: {const: "2"}
        record_type: {const: "ESTIMATE_COMMITMENT_SOURCE_ENVELOPE"}
        envelope_id: "safe_id"
        query_kind: {enum: ["ESTIMATE_ONLY", "COMMITMENT"]}
        work_item_id: "safe_id"
        sources: "EstimateCommitmentSourcesV2"
        source_payload_digest: "sha256"
        replay_reservation: "EstimateSourceReplayReservationV1"
        source_attestation: "EstimateSourceEnvelopeAttestationV1"
        digest: "sha256"
      nullable_fields: []
      array_cardinalities: {}
      digest_rule: "source_payload_digest is RFC8785 SHA-256 over exactly schema_version, record_type, envelope_id, query_kind, work_item_id, and sources. replay_reservation and source_attestation both bind it. digest is RFC8785 SHA-256 over every envelope field except digest."
      construction_rule: "The authenticated canonical source adapter constructs the source payload, atomically consumes one globally new challenge/nonce pair in the canonical replay ledger, embeds that exact reservation, and signs the envelope. A query caller supplies query_kind and work_item_id only; it cannot supply an envelope, attestation, replay proof, authority manifest, or source rows, nor trim, reorder, default, or select them."

    sources_object:
      type_id: "EstimateCommitmentSourcesV2"
      additional_properties: false
      fields: ["ESTIMATE", "PLAN", "SCOPE", "CAPACITY", "DEPENDENCY", "RISK", "ACCEPTANCE", "OWNER", "DECISION", "TRACE", "TIME"]
      field_types:
        ESTIMATE: "EstimateAuthorityRegistryV2"
        PLAN: "IntegratedPlanAuthorityRegistryV1"
        SCOPE: "ScopeAuthorityRegistryV1"
        CAPACITY: "CapacityAuthorityRegistryV1"
        DEPENDENCY: "DependencyAuthorityRegistryV1"
        RISK: "RiskAuthorityRegistryV1"
        ACCEPTANCE: "AcceptanceAuthorityRegistryV1"
        OWNER: "AccountableOwnerAuthorityRegistryV1"
        DECISION: "CommitmentDecisionAuthorityRegistryV1"
        TRACE: "CoreSdlcTraceAuthorityRegistryV1"
        TIME: "TrustedTimeAuthorityRegistryV1"
      nullable_fields: []
      array_cardinalities: {}
      invariant: "All eleven keys are present even for ESTIMATE_ONLY. Every registry is schema-, digest-, and complete-history-validated and current heads are independently derived before the resolver may return the non-authoritative estimate receipt. Historical/superseded rows remain required history but cannot satisfy a CURRENT binding. An unknown, missing, extra, V1, mixed-version, partial, or caller-filtered source fails."

    role_authorities:
      - {role: "ESTIMATE", context: "work_management", registry_type: "EstimateAuthorityRegistryV2", schema_ref: "schemas/planning/estimate-authority-registry-v2.schema.json", business_row_types: ["EstimateEvidenceAuthorityRowV1", "EstimateIdReservationHistoryGenerationV1", "EstimateIdReservationHistoryV1", "EstimateIdReservationV1", "EstimateMethodAuthorityRowV1", "EstimateObservationV1", "EstimatePreparerProvenanceV1"]}
      - {role: "PLAN", context: "work_management", registry_type: "IntegratedPlanAuthorityRegistryV1", schema_ref: "schemas/planning/integrated-plan-authority-registry-v1.schema.json", business_row_types: ["IntegratedPlanAuthorityRowV1"]}
      - {role: "SCOPE", context: "work_management", registry_type: "ScopeAuthorityRegistryV1", schema_ref: "schemas/planning/scope-authority-registry-v1.schema.json", business_row_types: ["ScopeAuthorityRowV1"]}
      - {role: "CAPACITY", context: "work_management", registry_type: "CapacityAuthorityRegistryV1", schema_ref: "schemas/planning/capacity-authority-registry-v1.schema.json", business_row_types: ["CapacitySnapshotAuthorityRowV1"]}
      - {role: "DEPENDENCY", context: "work_management", registry_type: "DependencyAuthorityRegistryV1", schema_ref: "schemas/planning/dependency-authority-registry-v1.schema.json", business_row_types: ["DependencySnapshotAuthorityRowV1"]}
      - {role: "RISK", context: "risk", registry_type: "RiskAuthorityRegistryV1", schema_ref: "schemas/planning/risk-authority-registry-v1.schema.json", business_row_types: ["RiskSnapshotAuthorityRowV1"]}
      - {role: "ACCEPTANCE", context: "product_definition", registry_type: "AcceptanceAuthorityRegistryV1", schema_ref: "schemas/planning/acceptance-authority-registry-v1.schema.json", business_row_types: ["AcceptanceBasisAuthorityRowV1"]}
      - {role: "OWNER", context: "identity_access", registry_type: "AccountableOwnerAuthorityRegistryV1", schema_ref: "schemas/planning/accountable-owner-authority-registry-v1.schema.json", business_row_types: ["AccountableDeliveryOwnerAssignmentV1"]}
      - {role: "DECISION", context: "policy", registry_type: "CommitmentDecisionAuthorityRegistryV1", schema_ref: "schemas/planning/commitment-decision-authority-registry-v1.schema.json", business_row_types: ["HumanDecisionRecord", "DecisionAuthenticationBindingV1", "DecisionArtifactRegistryRowV1"]}
      - {role: "TRACE", context: "work_management", registry_type: "CoreSdlcTraceAuthorityRegistryV1", schema_ref: "schemas/planning/core-sdlc-trace-authority-registry-v1.schema.json", business_row_types: ["CoreSdlcTrace", "CoreSdlcTraceAuthorityBindingV1"]}
      - {role: "TIME", context: "identity_access", registry_type: "TrustedTimeAuthorityRegistryV1", schema_ref: "schemas/planning/trusted-time-authority-registry-v1.schema.json", business_row_types: ["TrustedTimeObservationV1"]}

    content_address_and_history_rules:
      row_digest: "Unless a type states a stricter inherited rule, digest is RFC8785 SHA-256 over every row field except the row's self-reference field and digest. The self-reference is then derived from the type, immutable identity, version, and digest. External refs have an explicit paired digest and both must resolve."
      registry_digest: "A registry digest is RFC8785 SHA-256 over every registry field except registry_ref and digest; registry_ref is then urn:ranex:estimate-authority-registry:<record_type>:<registry_id>:<generation_number>:<digest-without-prefix>. That self-hash is necessary but insufficient: the ref/digest must equal the authenticated current publication fetched from the named canonical role owner, never a caller-provided lookalike."
      complete_history: "Every registry array is the complete retained admitted history for its type, not only current rows. Generation 1 has prior_registry_digest JSON null and the exact externally pinned genesis history_anchor_ref/digest. Each later publication keeps registry_id and history anchor, strictly increments generation_number, uses a globally new generation_id, names the exact immutable prior registry digest, retains every prior row byte-for-byte, and appends only valid new rows. The canonical owner archive resolves every prior publication to the pinned genesis. Deletion, rewrite, renumber, re-rooting, identity reuse, and fork fail even when a mutated current object is internally self-consistent."
      currentness: "A business authority row declaring observed_at/valid_until is CURRENT at the exact TIME instant only when observed_at <= instant < valid_until, it is not revoked where revocation is defined, and no later admitted row in the same role/work-item lineage names it as the unique immediate predecessor. HumanDecisionRecord currentness additionally follows its issued/expires/revoked/supersedes fields; TrustedTimeObservationV1 follows its attestation/chain rule; immutable reservation/history rows are admitted facts rather than mutable CURRENT facts. Historical rows are expected in complete registries and are validated but never selected as CURRENT. Every supersession is same-work-item, strictly chronological, unique, and acyclic."
      array_rule: "All registry arrays and all business arrays are received already duplicate-free and bytewise ordered by their declared row key. Exact received bytes are validated; normalization is prohibited."
      admission_causality: "A row cannot be admitted before the observation, authentication, reservation, or external-artifact registration instants it binds. A commitment decision issued_at is strictly later than every predecision estimate/source observation, estimate admission, owner assignment, trace observation, and decision authentication instant and no later than the trusted TIME instant. Its own decision-artifact registration occurs at or after issued_at and no later than the trusted instant."
      nonauthority: "Registry membership, freshness, an estimate, a plan, a preparer authentication, or a source-envelope digest never itself grants commitment, gate, state-transition, permit, landing, release, or effect authority."

    registry_publication_fields:
      exact_prefix_fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at"]
      exact_suffix_field: "digest"
      field_types:
        schema_version: {const_from_shape: true}
        record_type: {const_from_shape: true}
        registry_id: "safe_id"
        registry_ref: "safe_id_or_registered_urn"
        generation_id: "safe_id"
        generation_number: "positive_integer"
        prior_registry_digest: "sha256|null"
        history_anchor_ref: "safe_id_or_registered_urn"
        history_anchor_digest: "sha256"
        published_at: "strict_utc"
        digest: "sha256"
      nullable_fields: ["prior_registry_digest"]
      authority_rule: "history_anchor_ref/digest resolves the immutable owner-specific registry genesis policy pinned by the signed source-adapter authority manifest. The manifest also names each role's canonical current registry ref/digest and generation; self-hash validation alone never establishes authority."

    supersession_pointer_catalog:
      - {type_id: "AcceptanceBasisAuthorityRowV1", pointer_field: "supersedes_acceptance_snapshot_id", predecessor_key: "acceptance_snapshot_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "AccountableDeliveryOwnerAssignmentV1", pointer_field: "supersedes_assignment_id", predecessor_key: "assignment_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "CapacitySnapshotAuthorityRowV1", pointer_field: "supersedes_capacity_snapshot_id", predecessor_key: "capacity_snapshot_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "CoreSdlcTraceAuthorityBindingV1", pointer_field: "supersedes_trace_binding_id", predecessor_key: "trace_binding_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "DependencySnapshotAuthorityRowV1", pointer_field: "supersedes_dependency_snapshot_id", predecessor_key: "dependency_snapshot_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "EstimateEvidenceAuthorityRowV1", pointer_field: "supersedes_evidence_row_digest", predecessor_key: "digest", partition_key: "work_item_id + evidence_id", chronology_field: "observed_at"}
      - {type_id: "EstimateIdReservationHistoryGenerationV1", pointer_field: "previous_generation_digest", predecessor_key: "digest", partition_key: "history_id", chronology_field: "generation_number"}
      - {type_id: "EstimateMethodAuthorityRowV1", pointer_field: "supersedes_method_row_digest", predecessor_key: "digest", partition_key: "work_item_id + method_id", chronology_field: "observed_at"}
      - {type_id: "EstimateObservationV1", pointer_field: "supersedes_estimate_id", predecessor_key: "estimate_id", partition_key: "work_item_id + derived root estimate series ID", chronology_field: "observed_at and reservation admitted_at"}
      - {type_id: "EstimateSourceReplayReservationV1", pointer_field: "prior_reservation_digest", predecessor_key: "digest", partition_key: "adapter_id", chronology_field: "consumed_at"}
      - {type_id: "HumanDecisionRecord", pointer_field: "supersedes", predecessor_key: "decision_id", partition_key: "subject work_item_id", chronology_field: "issued_at"}
      - {type_id: "IntegratedPlanAuthorityRowV1", pointer_field: "supersedes_plan_id", predecessor_key: "plan_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "RiskSnapshotAuthorityRowV1", pointer_field: "supersedes_risk_snapshot_id", predecessor_key: "risk_snapshot_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "ScopeAuthorityRowV1", pointer_field: "supersedes_scope_id", predecessor_key: "scope_id", partition_key: "work_item_id", chronology_field: "observed_at"}
      - {type_id: "TrustedTimeObservationV1", pointer_field: "previous_observation_digest", predecessor_key: "digest", partition_key: "trusted_source_id", chronology_field: "monotonic_counter and instant"}
    supersession_closed_graph_rule: "The pointer catalog is exhaustive. For each listed partition, a non-null pointer resolves exactly one earlier predecessor; at most one row points to a predecessor; roots alone use JSON null; a CURRENT head is unique; all rows are reachable from one root; and cycles, forks, joins, skips, orphan roots, cross-partition edges, and non-increasing chronology fail."

    registry_shapes:
      - type_id: "EstimateAuthorityRegistryV2"
        schema_version: {const: "2"}
        record_type: {const: "ESTIMATE_AUTHORITY_REGISTRY"}
        additional_properties: false
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "reservation_history", "method_rows", "evidence_rows", "preparer_rows", "estimate_rows", "digest"]
        field_types:
          schema_version: {const: "2"}
          record_type: {const: "ESTIMATE_AUTHORITY_REGISTRY"}
          registry_id: "safe_id"
          registry_ref: "safe_id_or_registered_urn"
          generation_id: "safe_id"
          generation_number: "positive_integer"
          prior_registry_digest: "sha256|null"
          history_anchor_ref: "safe_id_or_registered_urn"
          history_anchor_digest: "sha256"
          published_at: "strict_utc"
          reservation_history: "EstimateIdReservationHistoryV1"
          method_rows: "EstimateMethodAuthorityRowV1[]"
          evidence_rows: "EstimateEvidenceAuthorityRowV1[]"
          preparer_rows: "EstimatePreparerProvenanceV1[]"
          estimate_rows: "EstimateObservationV1[]"
          digest: "sha256"
        nullable_fields: ["prior_registry_digest"]
        array_cardinalities:
          method_rows: "1..N"
          evidence_rows: "1..N"
          preparer_rows: "1..N"
          estimate_rows: "1..N"
        array_order:
          method_rows: "BYTEWISE_METHOD_REF"
          evidence_rows: "BYTEWISE_EVIDENCE_REF"
          preparer_rows: "BYTEWISE_PREPARER_PROVENANCE_ID"
          estimate_rows: "BYTEWISE_ESTIMATE_ID"
        invariants:
          - "reservation_history has exactly one immutable reservation for every estimate_id in estimate_rows and has no reservation without its admitted estimate."
          - "For every estimate, reservation reserved_at <= estimate observed_at <= reservation admitted_at <= registry published_at. Each history generation's appended IDs have reservation prior_generation_digest equal to that generation's previous_generation_digest; generation 1 uses JSON null."
          - "Every EstimateObservationV1 resolves exactly one method row, one preparer row for prepared_by_principal_id, and every evidence binding from this same complete registry."
          - "The V2 object shape is mandatory. A raw EstimateObservationV1 array, a V1 wrapper, a mixed registry, or synthesized method/evidence/preparer/reservation authority fails."

      - type_id: "IntegratedPlanAuthorityRegistryV1"
        role: "PLAN"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "INTEGRATED_PLAN_AUTHORITY_REGISTRY"}
        row_type: "IntegratedPlanAuthorityRowV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_PLAN_REF"

      - type_id: "ScopeAuthorityRegistryV1"
        role: "SCOPE"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "SCOPE_AUTHORITY_REGISTRY"}
        row_type: "ScopeAuthorityRowV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_SCOPE_REF"

      - type_id: "CapacityAuthorityRegistryV1"
        role: "CAPACITY"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "CAPACITY_AUTHORITY_REGISTRY"}
        row_type: "CapacitySnapshotAuthorityRowV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_CAPACITY_SNAPSHOT_REF"

      - type_id: "DependencyAuthorityRegistryV1"
        role: "DEPENDENCY"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "DEPENDENCY_AUTHORITY_REGISTRY"}
        row_type: "DependencySnapshotAuthorityRowV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_DEPENDENCY_SNAPSHOT_REF"

      - type_id: "RiskAuthorityRegistryV1"
        role: "RISK"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "RISK_AUTHORITY_REGISTRY"}
        row_type: "RiskSnapshotAuthorityRowV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_RISK_SNAPSHOT_REF"

      - type_id: "AcceptanceAuthorityRegistryV1"
        role: "ACCEPTANCE"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "ACCEPTANCE_AUTHORITY_REGISTRY"}
        row_type: "AcceptanceBasisAuthorityRowV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_ACCEPTANCE_SNAPSHOT_REF"

      - type_id: "AccountableOwnerAuthorityRegistryV1"
        role: "OWNER"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "ACCOUNTABLE_OWNER_AUTHORITY_REGISTRY"}
        row_type: "AccountableDeliveryOwnerAssignmentV1"
        row_cardinality: "0..N"
        row_order: "BYTEWISE_ASSIGNMENT_REF"

      - type_id: "CommitmentDecisionAuthorityRegistryV1"
        role: "DECISION"
        additional_properties: false
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "decision_rows", "authentication_binding_rows", "artifact_registry_rows", "digest"]
        constants: {schema_version: "1", record_type: "COMMITMENT_DECISION_AUTHORITY_REGISTRY"}
        field_types:
          decision_rows: "HumanDecisionRecord[]"
          authentication_binding_rows: "DecisionAuthenticationBindingV1[]"
          artifact_registry_rows: "DecisionArtifactRegistryRowV1[]"
        nullable_fields: ["prior_registry_digest"]
        array_cardinalities:
          decision_rows: "0..N"
          authentication_binding_rows: "0..N"
          artifact_registry_rows: "0..N"
        array_order:
          decision_rows: "BYTEWISE_DECISION_ID"
          authentication_binding_rows: "BYTEWISE_AUTHENTICATION_BINDING_ID"
          artifact_registry_rows: "BYTEWISE_ARTIFACT_REGISTRY_ROW_ID"
        invariant: "The decision_id populations of decision_rows, authentication_binding_rows, and artifact_registry_rows are exactly equal; each decision has exactly one binding and one artifact row and no orphan binding or artifact row exists. ESTIMATE_ONLY may have no selected decision for its work item, but all retained decision history remains present."

      - type_id: "CoreSdlcTraceAuthorityRegistryV1"
        role: "TRACE"
        additional_properties: false
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "trace_rows", "trace_binding_rows", "digest"]
        constants: {schema_version: "1", record_type: "CORE_SDLC_TRACE_AUTHORITY_REGISTRY"}
        field_types:
          trace_rows: "CoreSdlcTrace[]"
          trace_binding_rows: "CoreSdlcTraceAuthorityBindingV1[]"
        nullable_fields: ["prior_registry_digest"]
        array_cardinalities:
          trace_rows: "0..N"
          trace_binding_rows: "0..N"
        array_order:
          trace_rows: "BYTEWISE_TRACE_ID"
          trace_binding_rows: "BYTEWISE_TRACE_BINDING_ID"
        invariant: "The trace_id populations of trace_rows and trace_binding_rows are exactly equal. Every binding resolves exactly one schema-valid CoreSdlcTrace with the same trace_id, work_item_id, and digest, and no orphan row or binding exists."

      - type_id: "TrustedTimeAuthorityRegistryV1"
        role: "TIME"
        fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
        constants: {schema_version: "1", record_type: "TRUSTED_TIME_AUTHORITY_REGISTRY"}
        row_type: "TrustedTimeObservationV1"
        row_cardinality: "1..N"
        row_order: "BYTEWISE_TIME_OBSERVATION_ID"

    common_closed_registry_fields:
      applies_to: "Every registry_shapes entry and source_trust_registry_shape; special multi-array registries replace only the rows field with their explicitly declared closed arrays."
      field_types:
        schema_version: {const_from_shape: true}
        record_type: {const_from_shape: true}
        registry_id: "safe_id"
        registry_ref: "safe_id_or_registered_urn"
        generation_id: "safe_id"
        generation_number: "positive_integer"
        prior_registry_digest: "sha256|null"
        history_anchor_ref: "safe_id_or_registered_urn"
        history_anchor_digest: "sha256"
        published_at: "strict_utc"
        rows: "<declared row_type>[]"
        digest: "sha256"
      nullable_fields: ["prior_registry_digest"]
      additional_properties: false
      invariant: "The rows array is the complete retained history, not a work-item-filtered response. The registry publication prefix and prior-publication/history-anchor rules apply exactly; published_at is no later than the trusted TIME instant."

    source_trust_registry_shape:
      type_id: "EstimateSourceReplayAuthorityRegistryV1"
      schema_ref: "schemas/planning/estimate-source-replay-authority-registry-v1.schema.json"
      owner_context: "identity_access"
      additional_properties: false
      fields: ["schema_version", "record_type", "registry_id", "registry_ref", "generation_id", "generation_number", "prior_registry_digest", "history_anchor_ref", "history_anchor_digest", "published_at", "rows", "digest"]
      constants: {schema_version: "1", record_type: "ESTIMATE_SOURCE_REPLAY_AUTHORITY_REGISTRY"}
      row_type: "EstimateSourceReplayReservationV1"
      row_cardinality: "1..N"
      row_order: "BYTEWISE_REPLAY_RESERVATION_REF"
      nullable_fields: ["prior_registry_digest"]
      invariants:
        - "The registry publication prefix, content address, prior-publication chain, and externally pinned history anchor follow registry_publication_fields and content_address_and_history_rules exactly."
        - "rows is the complete immutable adapter replay history. Challenge digests, nonce digests, reservation IDs/refs, envelope IDs, and source payload digests are each globally unique; every row forms one complete linear prior_reservation_digest chain and no consumed row can be reused."
        - "The source authority manifest names this exact current registry ref/digest and generation. The envelope reservation is an exact member, and registry published_at equals its consumed_at and the selected trusted TIME instant."

    record_types:
      - type_id: "EstimateSourceReplayReservationV1"
        schema_ref: "schemas/planning/estimate-source-replay-reservation-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "adapter_id", "reservation_id", "reservation_ref", "envelope_id", "source_payload_digest", "presentation_challenge_digest", "nonce_digest", "reserved_at", "consumed_at", "expires_at", "prior_reservation_digest", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_SOURCE_REPLAY_RESERVATION"}
          adapter_id: {const: "work_management.estimate_commitment_source_adapter"}
          reservation_id: "safe_id"
          reservation_ref: "safe_id_or_registered_urn"
          envelope_id: "safe_id"
          source_payload_digest: "sha256"
          presentation_challenge_digest: "sha256"
          nonce_digest: "sha256"
          reserved_at: "strict_utc"
          consumed_at: "strict_utc"
          expires_at: "strict_utc"
          prior_reservation_digest: "sha256|null"
          digest: "sha256"
        nullable_fields: ["prior_reservation_digest"]
        array_cardinalities: {}
        self_reference_rule: "reservation_ref equals urn:ranex:estimate-source-replay:<adapter_id>:<reservation_id>:<digest-without-prefix>; digest excludes reservation_ref and digest."
        invariants:
          - "reserved_at <= consumed_at < expires_at; consumed_at equals source_attestation.authenticated_at and the selected trusted TIME instant."
          - "envelope_id and source_payload_digest equal the containing envelope; presentation challenge and nonce digests equal the attestation. Each identity and digest is immutable and globally nonreusable even after expiry."
          - "The first adapter row has prior_reservation_digest JSON null. Every successor names the exact immediately prior row digest and strictly increases consumed_at; the complete graph is linear and acyclic."

      - type_id: "EstimateIdReservationV1"
        schema_ref: "schemas/planning/estimate-id-reservation-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "reservation_id", "estimate_id", "work_item_id", "reserved_at", "admitted_at", "admitted_estimate_digest", "prior_generation_digest", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_ID_RESERVATION"}
          reservation_id: "safe_id"
          estimate_id: "safe_id"
          work_item_id: "safe_id"
          reserved_at: "strict_utc"
          admitted_at: "strict_utc"
          admitted_estimate_digest: "sha256"
          prior_generation_digest: "sha256|null"
          digest: "sha256"
        nullable_fields: ["prior_generation_digest"]
        array_cardinalities: {}
        invariants:
          - "reserved_at <= the bound EstimateObservationV1 observed_at <= admitted_at, and admitted_estimate_digest equals that immutable estimate digest for estimate_id and work_item_id."
          - "estimate_id, reservation_id, and their binding are globally immutable and nonreusable, including after expiry or supersession."

      - type_id: "EstimateIdReservationHistoryV1"
        schema_ref: "schemas/planning/estimate-id-reservation-history-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "history_id", "generation_rows", "reservation_rows", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_ID_RESERVATION_HISTORY"}
          history_id: "safe_id"
          generation_rows: "EstimateIdReservationHistoryGenerationV1[]"
          reservation_rows: "EstimateIdReservationV1[]"
          digest: "sha256"
        nullable_fields: []
        array_cardinalities:
          generation_rows: "1..N"
          reservation_rows: "1..N"
        array_order:
          generation_rows: "BYTEWISE_GENERATION_ID"
          reservation_rows: "BYTEWISE_ESTIMATE_ID"
        invariants:
          - "digest covers the complete generation_rows and reservation_rows sets. Each publication retains every prior row byte-for-byte and appends exactly one new generation containing only globally new estimate IDs."
          - "The final generation cumulative_estimate_ids equals the exact estimate_id population of reservation_rows. Missing, rewritten, duplicated, reused, forked, or orphaned reservations or generations fail."

      - type_id: "EstimateIdReservationHistoryGenerationV1"
        schema_ref: "schemas/planning/estimate-id-reservation-history-generation-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "history_id", "generation_id", "generation_number", "previous_generation_digest", "appended_estimate_ids", "cumulative_estimate_ids", "published_at", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_ID_RESERVATION_HISTORY_GENERATION"}
          history_id: "safe_id"
          generation_id: "safe_id"
          generation_number: "positive_integer"
          previous_generation_digest: "sha256|null"
          appended_estimate_ids: "safe_id[]"
          cumulative_estimate_ids: "safe_id[]"
          published_at: "strict_utc"
          digest: "sha256"
        nullable_fields: ["previous_generation_digest"]
        array_cardinalities:
          appended_estimate_ids: "1..N"
          cumulative_estimate_ids: "1..N"
        array_order:
          appended_estimate_ids: "BYTEWISE_ESTIMATE_ID"
          cumulative_estimate_ids: "BYTEWISE_ESTIMATE_ID"
        invariants:
          - "Generation 1 has previous_generation_digest JSON null, generation_number 1, and cumulative_estimate_ids equal appended_estimate_ids."
          - "Every later row has the immediately prior generation number and digest, a disjoint appended_estimate_ids set, and cumulative_estimate_ids equal the exact bytewise union of the prior cumulative set and appended set. Generation IDs are immutable/nonreusable and the chain is complete, linear, chronological, and acyclic."

      - type_id: "EstimateMethodAuthorityRowV1"
        schema_ref: "schemas/planning/estimate-method-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "method_id", "method_version", "method_ref", "work_item_id", "method_definition_ref", "method_definition_digest", "observed_at", "valid_until", "supersedes_method_row_digest", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_METHOD_AUTHORITY"}
          method_id: "safe_id"
          method_version: "positive_integer"
          method_ref: "safe_id_or_registered_urn"
          work_item_id: "safe_id"
          method_definition_ref: "safe_id_or_registered_urn"
          method_definition_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_method_row_digest: "sha256|null"
          digest: "sha256"
        nullable_fields: ["supersedes_method_row_digest"]
        array_cardinalities: {}
        self_reference_rule: "method_ref equals urn:ranex:estimate-method:<method_id>:<method_version>:<method_definition_digest-without-prefix>:<digest-without-prefix>; digest excludes method_ref and digest, thereby non-circularly binding the method ID, exact version, definition digest, and row digest."
        invariant: "An estimate method_ref resolves exactly this row for the same work item and estimate observed_at. A successor keeps method_id, strictly increases method_version and observed_at, and names the immediate prior row digest. No resolver may invent, auto-register, or upgrade a method."

      - type_id: "EstimateEvidenceAuthorityRowV1"
        schema_ref: "schemas/planning/estimate-evidence-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "evidence_id", "evidence_version", "evidence_ref", "work_item_id", "artifact_ref", "artifact_digest", "media_type", "observed_at", "valid_until", "supersedes_evidence_row_digest", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_EVIDENCE_AUTHORITY"}
          evidence_id: "safe_id"
          evidence_version: "positive_integer"
          evidence_ref: "safe_id_or_registered_urn"
          work_item_id: "safe_id"
          artifact_ref: "safe_id_or_registered_urn"
          artifact_digest: "sha256"
          media_type: "nonempty_string"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_evidence_row_digest: "sha256|null"
          digest: "sha256"
        nullable_fields: ["supersedes_evidence_row_digest"]
        array_cardinalities: {}
        self_reference_rule: "evidence_ref equals urn:ranex:estimate-evidence:<evidence_id>:<evidence_version>:<artifact_digest-without-prefix>:<digest-without-prefix>; digest excludes evidence_ref and digest."
        invariant: "EstimateEvidenceBindingV1.evidence_digest equals this row digest, not merely artifact_digest. The row and artifact must be exact and valid for the same work item at estimate observed_at. A successor keeps evidence_id, strictly increases evidence_version and observed_at, and names the immediate prior row digest."

      - type_id: "EstimatePreparerProvenanceV1"
        schema_ref: "schemas/planning/estimate-preparer-provenance-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "provenance_id", "principal_id", "work_item_id", "identity_ref", "identity_digest", "authentication_context_ref", "authentication_context_digest", "authenticated_at", "valid_until", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ESTIMATE_PREPARER_PROVENANCE"}
          provenance_id: "safe_id"
          principal_id: "safe_id"
          work_item_id: "safe_id"
          identity_ref: "safe_id_or_registered_urn"
          identity_digest: "sha256"
          authentication_context_ref: "safe_id_or_registered_urn"
          authentication_context_digest: "sha256"
          authenticated_at: "strict_utc"
          valid_until: "strict_utc"
          digest: "sha256"
        nullable_fields: []
        array_cardinalities: {}
        invariants:
          - "prepared_by_principal_id resolves exactly one row for the same work item, and authenticated_at <= estimate observed_at < valid_until."
          - "This is exact authorship provenance only. A preparer is not thereby the accountable owner and receives no commitment or execution authority."

      - type_id: "IntegratedPlanAuthorityRowV1"
        schema_ref: "schemas/planning/integrated-plan-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "plan_id", "plan_version", "work_item_id", "plan_ref", "scope_ref", "scope_digest", "estimate_ids", "capacity_snapshot_ref", "capacity_snapshot_digest", "dependency_snapshot_ref", "dependency_snapshot_digest", "risk_snapshot_ref", "risk_snapshot_digest", "acceptance_snapshot_ref", "acceptance_snapshot_digest", "owner_assignment_ref", "owner_assignment_digest", "commitment_window_start", "commitment_window_end", "observed_at", "valid_until", "supersedes_plan_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "INTEGRATED_PLAN_AUTHORITY"}
          plan_id: "safe_id"
          plan_version: "positive_integer"
          work_item_id: "safe_id"
          plan_ref: "safe_id_or_registered_urn"
          scope_ref: "safe_id_or_registered_urn"
          scope_digest: "sha256"
          estimate_ids: "safe_id[]"
          capacity_snapshot_ref: "safe_id_or_registered_urn"
          capacity_snapshot_digest: "sha256"
          dependency_snapshot_ref: "safe_id_or_registered_urn"
          dependency_snapshot_digest: "sha256"
          risk_snapshot_ref: "safe_id_or_registered_urn"
          risk_snapshot_digest: "sha256"
          acceptance_snapshot_ref: "safe_id_or_registered_urn"
          acceptance_snapshot_digest: "sha256"
          owner_assignment_ref: "safe_id_or_registered_urn"
          owner_assignment_digest: "sha256"
          commitment_window_start: "strict_utc"
          commitment_window_end: "strict_utc"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_plan_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_plan_id"]
        array_cardinalities:
          estimate_ids: "1..N"
        array_order:
          estimate_ids: "BYTEWISE_ESTIMATE_ID"
        self_reference_rule: "plan_ref equals urn:ranex:integrated-plan:<plan_id>:<plan_version>:<digest-without-prefix>; digest excludes plan_ref and digest."
        invariants:
          - "plan_id identifies one immutable plan row and is nonreusable. Within a work item, a successor has a globally new plan_id, strictly increases plan_version and observed_at, and supersedes_plan_id names the immediate prior plan_id."
          - "The one CURRENT plan for work_item_id declares the complete exact set of CURRENT admitted estimate IDs for that work item at the trusted instant. It cannot omit, add, duplicate, reorder, cross-bind, or delegate this set to a caller."
          - "commitment_window_start and commitment_window_end are business authority fields: observed_at <= commitment_window_start < commitment_window_end <= valid_until. No resolver, fixture, default, or policy constant may substitute or clamp them."
          - "Every paired scope, capacity, dependency, risk, acceptance, and owner ref/digest resolves one CURRENT same-work-item authority row."

      - type_id: "ScopeAuthorityRowV1"
        schema_ref: "schemas/planning/scope-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "scope_id", "scope_version", "work_item_id", "scope_ref", "requirement_ids", "acceptance_criterion_ids", "included_configuration_item_bindings", "excluded_configuration_item_bindings", "scope_definition_ref", "scope_definition_digest", "observed_at", "valid_until", "supersedes_scope_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "SCOPE_AUTHORITY"}
          scope_id: "safe_id"
          scope_version: "positive_integer"
          work_item_id: "safe_id"
          scope_ref: "safe_id_or_registered_urn"
          requirement_ids: "safe_id[]"
          acceptance_criterion_ids: "safe_id[]"
          included_configuration_item_bindings: "ContentAddressBindingV1[]"
          excluded_configuration_item_bindings: "ContentAddressBindingV1[]"
          scope_definition_ref: "safe_id_or_registered_urn"
          scope_definition_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_scope_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_scope_id"]
        array_cardinalities:
          requirement_ids: "1..N"
          acceptance_criterion_ids: "1..N"
          included_configuration_item_bindings: "0..N"
          excluded_configuration_item_bindings: "0..N"
        array_order:
          requirement_ids: "BYTEWISE_ID"
          acceptance_criterion_ids: "BYTEWISE_ID"
          included_configuration_item_bindings: "BYTEWISE_REF"
          excluded_configuration_item_bindings: "BYTEWISE_REF"
        self_reference_rule: "scope_ref equals urn:ranex:scope:<scope_id>:<scope_version>:<digest-without-prefix>; digest excludes scope_ref and digest."
        invariants:
          - "scope_id identifies one immutable scope row and is nonreusable. Within a work item, a successor has a globally new scope_id, strictly increases scope_version and observed_at, and supersedes_scope_id names the immediate prior scope_id."
          - "Included and excluded configuration-item sets are disjoint; requirement, acceptance, content-addressed configuration-item, and definition bindings are exact business scope, not descriptive shell metadata."

      - type_id: "CapacitySnapshotAuthorityRowV1"
        schema_ref: "schemas/planning/capacity-snapshot-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "capacity_snapshot_id", "work_item_id", "capacity_snapshot_ref", "capacity_unit", "resource_pool_ids", "resource_pool_catalog_ref", "resource_pool_catalog_digest", "available_capacity", "reserved_capacity", "calendar_ref", "calendar_digest", "observed_at", "valid_until", "supersedes_capacity_snapshot_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "CAPACITY_SNAPSHOT_AUTHORITY"}
          capacity_snapshot_id: "safe_id"
          work_item_id: "safe_id"
          capacity_snapshot_ref: "safe_id_or_registered_urn"
          capacity_unit: "nonempty_string"
          resource_pool_ids: "safe_id[]"
          resource_pool_catalog_ref: "safe_id_or_registered_urn"
          resource_pool_catalog_digest: "sha256"
          available_capacity: "nonnegative_number"
          reserved_capacity: "nonnegative_number"
          calendar_ref: "safe_id_or_registered_urn"
          calendar_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_capacity_snapshot_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_capacity_snapshot_id"]
        array_cardinalities:
          resource_pool_ids: "1..N"
        array_order:
          resource_pool_ids: "BYTEWISE_ID"
        self_reference_rule: "capacity_snapshot_ref equals urn:ranex:capacity-snapshot:<capacity_snapshot_id>:<digest-without-prefix>; digest excludes capacity_snapshot_ref and digest."
        invariant: "reserved_capacity <= available_capacity; unit, resource-pool population and its exact catalog digest, quantities, and calendar binding are exact business payload."

      - type_id: "DependencySnapshotAuthorityRowV1"
        schema_ref: "schemas/planning/dependency-snapshot-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "dependency_snapshot_id", "work_item_id", "dependency_snapshot_ref", "dependency_ids", "predecessor_work_item_ids", "external_dependency_bindings", "dependency_basis_ref", "dependency_basis_digest", "observed_at", "valid_until", "supersedes_dependency_snapshot_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "DEPENDENCY_SNAPSHOT_AUTHORITY"}
          dependency_snapshot_id: "safe_id"
          work_item_id: "safe_id"
          dependency_snapshot_ref: "safe_id_or_registered_urn"
          dependency_ids: "safe_id[]"
          predecessor_work_item_ids: "safe_id[]"
          external_dependency_bindings: "ContentAddressBindingV1[]"
          dependency_basis_ref: "safe_id_or_registered_urn"
          dependency_basis_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_dependency_snapshot_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_dependency_snapshot_id"]
        array_cardinalities:
          dependency_ids: "0..N"
          predecessor_work_item_ids: "0..N"
          external_dependency_bindings: "0..N"
        array_order:
          dependency_ids: "BYTEWISE_ID"
          predecessor_work_item_ids: "BYTEWISE_ID"
          external_dependency_bindings: "BYTEWISE_REF"
        self_reference_rule: "dependency_snapshot_ref equals urn:ranex:dependency-snapshot:<dependency_snapshot_id>:<digest-without-prefix>; digest excludes dependency_snapshot_ref and digest."
        invariant: "The three dependency populations and basis artifact are complete exact business payload; a missing-dependency representation is an explicit empty array, never an omitted or defaulted field."

      - type_id: "RiskSnapshotAuthorityRowV1"
        schema_ref: "schemas/planning/risk-snapshot-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "risk_snapshot_id", "work_item_id", "risk_snapshot_ref", "risk_ids", "risk_lane", "total_risk_reserve", "reserve_unit", "risk_register_ref", "risk_register_digest", "observed_at", "valid_until", "supersedes_risk_snapshot_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "RISK_SNAPSHOT_AUTHORITY"}
          risk_snapshot_id: "safe_id"
          work_item_id: "safe_id"
          risk_snapshot_ref: "safe_id_or_registered_urn"
          risk_ids: "safe_id[]"
          risk_lane: {enum: ["STANDARD", "ELEVATED", "CRITICAL"]}
          total_risk_reserve: "nonnegative_number"
          reserve_unit: "nonempty_string"
          risk_register_ref: "safe_id_or_registered_urn"
          risk_register_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_risk_snapshot_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_risk_snapshot_id"]
        array_cardinalities:
          risk_ids: "0..N"
        array_order:
          risk_ids: "BYTEWISE_ID"
        self_reference_rule: "risk_snapshot_ref equals urn:ranex:risk-snapshot:<risk_snapshot_id>:<digest-without-prefix>; digest excludes risk_snapshot_ref and digest."
        invariant: "Risk population, lane, reserve quantity/unit, and risk-register artifact are exact business payload."

      - type_id: "AcceptanceBasisAuthorityRowV1"
        schema_ref: "schemas/planning/acceptance-basis-authority-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "acceptance_snapshot_id", "work_item_id", "acceptance_snapshot_ref", "acceptance_criterion_ids", "verification_method_ids", "acceptance_owner_principal_id", "acceptance_owner_assignment_ref", "acceptance_owner_assignment_digest", "acceptance_definition_ref", "acceptance_definition_digest", "observed_at", "valid_until", "supersedes_acceptance_snapshot_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ACCEPTANCE_BASIS_AUTHORITY"}
          acceptance_snapshot_id: "safe_id"
          work_item_id: "safe_id"
          acceptance_snapshot_ref: "safe_id_or_registered_urn"
          acceptance_criterion_ids: "safe_id[]"
          verification_method_ids: "safe_id[]"
          acceptance_owner_principal_id: "safe_id"
          acceptance_owner_assignment_ref: "safe_id_or_registered_urn"
          acceptance_owner_assignment_digest: "sha256"
          acceptance_definition_ref: "safe_id_or_registered_urn"
          acceptance_definition_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_acceptance_snapshot_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_acceptance_snapshot_id"]
        array_cardinalities:
          acceptance_criterion_ids: "1..N"
          verification_method_ids: "1..N"
        array_order:
          acceptance_criterion_ids: "BYTEWISE_ID"
          verification_method_ids: "BYTEWISE_ID"
        self_reference_rule: "acceptance_snapshot_ref equals urn:ranex:acceptance-basis:<acceptance_snapshot_id>:<digest-without-prefix>; digest excludes acceptance_snapshot_ref and digest."
        invariant: "Criterion population, verification methods, accountable acceptance owner plus exact assignment ref/digest, and definition artifact are exact business payload; criteria equal the current scope acceptance_criterion_ids."

      - type_id: "AccountableDeliveryOwnerAssignmentV1"
        schema_ref: "schemas/planning/accountable-delivery-owner-assignment-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "assignment_id", "assignment_ref", "work_item_id", "principal_id", "role_id", "identity_ref", "identity_digest", "role_policy_ref", "role_policy_digest", "observed_at", "valid_until", "supersedes_assignment_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "ACCOUNTABLE_DELIVERY_OWNER_ASSIGNMENT"}
          assignment_id: "safe_id"
          assignment_ref: "safe_id_or_registered_urn"
          work_item_id: "safe_id"
          principal_id: "safe_id"
          role_id: {const: "ACCOUNTABLE_DELIVERY_OWNER"}
          identity_ref: "safe_id_or_registered_urn"
          identity_digest: "sha256"
          role_policy_ref: "safe_id_or_registered_urn"
          role_policy_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_assignment_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_assignment_id"]
        array_cardinalities: {}
        self_reference_rule: "assignment_ref equals urn:ranex:accountable-delivery-owner:<assignment_id>:<digest-without-prefix>; digest excludes assignment_ref and digest."
        invariant: "Exactly one CURRENT same-work-item assignment with exact role_id ACCOUNTABLE_DELIVERY_OWNER binds the plan and decision principal. Similar role names, preparer provenance, group identity, or implicit ownership fail."

      - type_id: "DecisionAuthenticationBindingV1"
        schema_ref: "schemas/planning/decision-authentication-binding-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "authentication_binding_id", "authentication_context_id", "decision_id", "decision_digest", "principal_id", "authenticator_ref", "authenticator_digest", "presentation_challenge_digest", "nonce_digest", "authenticated_at", "valid_until", "revoked_at", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "DECISION_AUTHENTICATION_BINDING"}
          authentication_binding_id: "safe_id"
          authentication_context_id: "safe_id"
          decision_id: "safe_id"
          decision_digest: "sha256"
          principal_id: "safe_id"
          authenticator_ref: "safe_id_or_registered_urn"
          authenticator_digest: "sha256"
          presentation_challenge_digest: "sha256"
          nonce_digest: "sha256"
          authenticated_at: "strict_utc"
          valid_until: "strict_utc"
          revoked_at: "strict_utc|null"
          digest: "sha256"
        nullable_fields: ["revoked_at"]
        array_cardinalities: {}
        invariant: "The HumanDecisionRecord authentication_context_id, decision_id/digest, principal_id, presentation_challenge_digest, and SHA-256 of the exact UTF-8 nonce all match. authenticated_at < decision issued_at < valid_until, the binding is unrevoked at the trusted instant, and the authenticator ref/digest is exact."

      - type_id: "DecisionArtifactRegistryRowV1"
        schema_ref: "schemas/planning/decision-artifact-registry-row-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "artifact_registry_row_id", "artifact_type", "artifact_id", "artifact_ref", "artifact_digest", "work_item_id", "registered_at", "registry_authority_ref", "registry_authority_digest", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "DECISION_ARTIFACT_REGISTRY_ROW"}
          artifact_registry_row_id: "safe_id"
          artifact_type: {const: "human_decision"}
          artifact_id: "safe_id"
          artifact_ref: "safe_id_or_registered_urn"
          artifact_digest: "sha256"
          work_item_id: "safe_id"
          registered_at: "strict_utc"
          registry_authority_ref: "safe_id_or_registered_urn"
          registry_authority_digest: "sha256"
          digest: "sha256"
        nullable_fields: []
        array_cardinalities: {}
        invariant: "artifact_id/digest identify the exact HumanDecisionRecord; artifact_ref is content-addressed by artifact_type, artifact_id, and artifact_digest; registered_at is no earlier than decision issued_at and no later than the trusted instant."

      - type_id: "CoreSdlcTraceAuthorityBindingV1"
        schema_ref: "schemas/planning/core-sdlc-trace-authority-binding-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "trace_binding_id", "trace_id", "trace_digest", "work_item_id", "trace_registry_ref", "trace_registry_digest", "observed_at", "valid_until", "supersedes_trace_binding_id", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "CORE_SDLC_TRACE_AUTHORITY_BINDING"}
          trace_binding_id: "safe_id"
          trace_id: "safe_id"
          trace_digest: "sha256"
          work_item_id: "safe_id"
          trace_registry_ref: "safe_id_or_registered_urn"
          trace_registry_digest: "sha256"
          observed_at: "strict_utc"
          valid_until: "strict_utc"
          supersedes_trace_binding_id: "safe_id|null"
          digest: "sha256"
        nullable_fields: ["supersedes_trace_binding_id"]
        array_cardinalities: {}
        invariant: "trace_id/digest resolve an exact schemas/common/core-sdlc-trace-v1.schema.json row for work_item_id. HumanDecisionRecord.core_sdlc_trace_ref equals trace_id and the binding is CURRENT."

      - type_id: "TrustedTimeObservationV1"
        schema_ref: "schemas/planning/trusted-time-observation-v1.schema.json"
        additional_properties: false
        fields: ["schema_version", "record_type", "time_observation_id", "trusted_source_id", "source_ref", "source_digest", "instant", "uncertainty_milliseconds", "maximum_age_milliseconds", "monotonic_counter", "previous_observation_digest", "attested_at", "digest"]
        field_types:
          schema_version: {const: "1"}
          record_type: {const: "TRUSTED_TIME_OBSERVATION"}
          time_observation_id: "safe_id"
          trusted_source_id: "safe_id"
          source_ref: "safe_id_or_registered_urn"
          source_digest: "sha256"
          instant: "strict_utc"
          uncertainty_milliseconds: "nonnegative_integer"
          maximum_age_milliseconds: "positive_integer"
          monotonic_counter: "nonnegative_integer"
          previous_observation_digest: "sha256|null"
          attested_at: "strict_utc"
          digest: "sha256"
        nullable_fields: ["previous_observation_digest"]
        array_cardinalities: {}
        invariants:
          - "source_ref/digest resolves a registered trusted-time policy; maximum_age_milliseconds comes from that authority and cannot be caller- or fixture-selected. attested_at <= instant and instant minus attested_at is no greater than maximum_age_milliseconds."
          - "The accepted row is the unique latest row for trusted_source_id; monotonic_counter and instant strictly increase, previous_observation_digest names the unique immediate predecessor, and the chain is complete, single-successor, and acyclic."
          - "Temporal eligibility is conservative over the closed uncertainty interval [instant - uncertainty_milliseconds, instant + uncertainty_milliseconds]: a required not-before predicate must hold at the lower endpoint and every current/not-expired predicate must hold at the upper endpoint. An interval crossing a boundary fails closed."

    compatibility_and_migration:
      predecessor_source_shape: "ESTIMATE role as EstimateObservationV1[] inside an unversioned or V1 source envelope"
      successor_source_shape: "ESTIMATE role as EstimateAuthorityRegistryV2 inside EstimateCommitmentSourceEnvelopeV2"
      public_record_compatibility: "EstimateObservationV1 and DELIVERY_COMMITMENT_SUBJECT_V1 remain at V1; the breaking change is limited to source authority/envelope representation and semantics."
      live_precondition: "No production commitment record exists and runtime adoption remains zero; therefore no dual-read compatibility path is authorized."
      live_rules:
        - "A V1, raw-list, unversioned, mixed V1/V2, or partially migrated source is rejected. There is no automatic wrapping, best-effort fallback, dual read, default row, or fixture-only bypass."
        - "New Method, Evidence, Preparer, Reservation, Plan, Scope, Capacity, Dependency, Risk, Acceptance, Owner, Authentication, Trace-binding, and Time records begin at V1 because no predecessor schema for those rows existed."
      offline_migration:
        migration_id: "ESTIMATE-SOURCE-V1-TO-V2-001"
        mode: "EXPLICIT_OFFLINE_VALIDATED_NO_LIVE_DUAL_READ"
        rules:
          - "Preserve every EstimateObservationV1 byte-for-byte and preserve each estimate_id/digest."
          - "Obtain method, evidence, preparer, reservation-history, and every role authority row from its canonical owner. A migrator cannot infer or synthesize them from an estimate."
          - "A preserved estimate migrates only when its existing method_ref and evidence bindings already resolve the exact new authority rows without changing a byte. Otherwise the migrator retains that row as non-authoritative history and a human-authorized producer issues a new EstimateObservationV1 with a globally new reserved estimate_id; silent ref or digest rewriting is forbidden."
          - "Publish complete content-addressed registries, validate every binding and history invariant, then atomically publish one V2 envelope. Partial publication fails and leaves V1 non-authoritative."
          - "After V2 publication, V1 input remains rejected and immutable migration evidence is retained."

  commitment_subject_projection:
    projection_id: "DELIVERY_COMMITMENT_SUBJECT_V1"
    subject_schema: "delivery-commitment-subject/v1"
    schema_ref: "schemas/planning/delivery-commitment-subject-v1.schema.json"
    digest_rule: "RFC8785 SHA-256 over exactly the output fields in listed order as a canonical JSON object"
    additional_properties: false
    output_fields: ["subject_schema", "subject_ref", "work_item_id", "plan_ref", "plan_digest", "scope_ref", "scope_digest", "estimate_bindings", "capacity_snapshot_ref", "capacity_snapshot_digest", "dependency_snapshot_ref", "dependency_snapshot_digest", "risk_snapshot_ref", "risk_snapshot_digest", "acceptance_snapshot_ref", "acceptance_snapshot_digest", "commitment_owner_id", "commitment_window_start", "commitment_window_end", "recommit_trigger_ids"]
    field_types:
      subject_schema: {const: "delivery-commitment-subject/v1"}
      subject_ref: "safe_id_or_registered_urn"
      work_item_id: "safe_id"
      plan_ref: "safe_id_or_registered_urn"
      plan_digest: "sha256"
      scope_ref: "safe_id_or_registered_urn"
      scope_digest: "sha256"
      estimate_bindings: "EstimateBindingV1[]"
      capacity_snapshot_ref: "safe_id_or_registered_urn"
      capacity_snapshot_digest: "sha256"
      dependency_snapshot_ref: "safe_id_or_registered_urn"
      dependency_snapshot_digest: "sha256"
      risk_snapshot_ref: "safe_id_or_registered_urn"
      risk_snapshot_digest: "sha256"
      acceptance_snapshot_ref: "safe_id_or_registered_urn"
      acceptance_snapshot_digest: "sha256"
      commitment_owner_id: "safe_id"
      commitment_window_start: "strict_utc"
      commitment_window_end: "strict_utc"
      recommit_trigger_ids:
        exact_set: ["ACCEPTANCE_BASIS_CHANGED", "CAPACITY_CHANGED", "COMMITMENT_WINDOW_EXPIRED", "DEPENDENCY_CHANGED", "ESTIMATE_BINDING_CHANGED", "ESTIMATE_EXPIRED", "RISK_CHANGED", "SCOPE_CHANGED"]
    nullable_fields: []
    array_cardinalities:
      estimate_bindings: "1..N"
      recommit_trigger_ids: "exactly 8"
    array_order:
      estimate_bindings: "BYTEWISE_ESTIMATE_ID"
      recommit_trigger_ids: "BYTEWISE_ENUM"
    subject_ref_rule: "subject_ref equals urn:ranex:delivery-commitment:<work_item_id>:<plan_digest-without-prefix>"
    invariants:
      - "commitment_window_start < commitment_window_end."
      - "plan_ref/digest resolve the unique CURRENT IntegratedPlanAuthorityRowV1 for work_item_id. scope, capacity, dependency, risk, acceptance, commitment window, and owner are copied exactly from that row and independently re-resolved; the resolver cannot accept caller-supplied replacements."
      - "estimate_bindings are derived from, and have exactly the same ID population as, the plan's duplicate-free bytewise estimate_ids. That population equals every CURRENT admitted estimate for work_item_id in the complete EstimateAuthorityRegistryV2; omitted, extra, stale, superseded, cross-plan, cross-work-item, duplicate, or reordered rows fail."
      - "Every estimate is CURRENT, has this work_item_id, has subject_ref/digest equal to scope_ref/digest, has capacity and dependency refs/digests equal to this projection, and independently equals its exact immutable row digest and reservation."
      - "Plan, scope, capacity, dependency, risk, acceptance, and owner refs each resolve exactly one CURRENT immutable row whose digest equals the paired digest and whose work_item_id equals work_item_id."
      - "commitment_window_end is no later than valid_until for every bound estimate, plan, scope, capacity, dependency, risk, acceptance, owner assignment, and trace binding. A commitment cannot knowingly outlive a supporting authority row."
      - "commitment_owner_id is the principal_id of the exact CURRENT AccountableDeliveryOwnerAssignmentV1 bound by the plan; its role_id is exactly ACCOUNTABLE_DELIVERY_OWNER."
      - "commitment_window_start/end are copied byte-for-byte from the plan's business-authoritative window. No fixed duration, constant date, fixture value, caller override, or resolver default is normative."
      - "The eight recommit triggers are a closed exact set; an unknown, missing, duplicate, or reordered trigger fails."

  commitment_decision_role:
    schema_ref: "schemas/authority/human-decision-v1.schema.json"
    artifact_type: "human_decision"
    status: "APPROVED"
    decision_kind: "WORK_TRANSITION"
    outcome: "APPROVED"
    action_type: "COMMIT_DELIVERY_SCOPE"
    expected_subject_projection: "DELIVERY_COMMITMENT_SUBJECT_V1"
    cardinality: "exactly one CURRENT eligible decision per exact subject; at most one CURRENT decision per work_item_id, and no two CURRENT decisions may have overlapping commitment windows"
    exact_bindings:
      - "subject.subject_schema equals delivery-commitment-subject/v1; subject.subject_ref and subject.subject_digest equal the independently derived exact projection."
      - "The subject.subject_manifest_digest key is present and its JSON value is exactly null; omission, string \"null\", empty string, or a digest fails. The complete closed subject is carried by subject.subject_digest."
      - "action.canonical_argument_digest equals subject.subject_digest; action.destination equals work_item_id; action.adapter_id equals policy; action.adapter_version equals 1.0.0."
      - "principal_id equals commitment_owner_id and resolves an authenticated accountable delivery-owner assignment current for the work item."
      - "scope is the duplicate-free bytewise-sorted exact set whose members are work_item_id, plan_ref, and scope_ref; conditions is the duplicate-free bytewise-sorted exact eight-item recommit_trigger_ids set."
      - "core_sdlc_trace_ref resolves an exact CURRENT CoreSdlcTrace and binding for the same work_item_id."
      - "issued_at is at or after commitment_window_start, strictly later than every predecision bound estimate observed/admitted instant and source observation, owner assignment, trace observation, and authentication instant, and no later than the accepted trusted TIME instant; its artifact registration is at or after issued_at and no later than that trusted instant. expires_at equals commitment_window_end and revoked_at is JSON null."
      - "supersedes is JSON null for the first commitment. A recommitment names exactly the unique immediate prior decision for the same work_item_id invalidated by the changed subject; issued_at is strictly later, and the complete supersession graph is chronological, single-predecessor, single-successor, same-work-item, and acyclic. Cross-work-item, skipped-prior, forked, orphaned, cyclic, or nonchronological supersession fails."
      - "digest is independently recomputed from the complete HumanDecisionRecord; authentication context, presentation challenge, nonce, and artifact-registry row are current and exact."
    authority_boundary:
      - "An eligible decision establishes only the accountable delivery commitment for this exact subject and window."
      - "It cannot change a WorkItem state, manufacture gate PASS, issue an AuthorityGrant or Permit, waive evidence, land code, release, or prove delivery."
      - "Any changed bound digest or fired recommit trigger makes the prior decision ineligible for future reliance and requires a new exact subject and HumanDecisionRecord."

  resolver_contract:
    resolver_id: "ESTIMATE-COMMITMENT-RESOLVER-1.1"
    accepted_source_envelope: "EstimateCommitmentSourceEnvelopeV2 only"
    envelope_trust_sources:
      - {role: "SOURCE_ADAPTER_AUTHORITY", source: "signed current adapter/role-owner/key/history-anchor authority manifest"}
      - {role: "SOURCE_REPLAY", source: "complete content-addressed EstimateSourceReplayAuthorityRegistryV1 and exact reservation"}
      - {role: "SOURCE_SIGNATURE", source: "verified EstimateSourceEnvelopeAttestationV1 over the exact payload and replay binding"}
    query_requirement_matrix:
      ESTIMATE_ONLY:
        registry_requirements: "All eleven closed authenticated registry objects and their complete histories are present and valid."
        selected_row_requirements: ["CAPACITY", "DEPENDENCY", "ESTIMATE", "SCOPE", "TIME"]
        permitted_absence_for_work_item: ["ACCEPTANCE", "DECISION", "OWNER", "PLAN", "RISK", "TRACE"]
        result: "ESTIMATE_ONLY_NON_AUTHORITATIVE"
        authority_effects: []
      COMMITMENT:
        registry_requirements: "All eleven closed authenticated registry objects and their complete histories are present and valid."
        selected_row_requirements: ["ACCEPTANCE", "CAPACITY", "DECISION", "DEPENDENCY", "ESTIMATE", "OWNER", "PLAN", "RISK", "SCOPE", "TIME", "TRACE"]
        permitted_absence_for_work_item: []
        result: "CURRENT_DELIVERY_COMMITMENT"
        authority_effects: ["DELIVERY_COMMITMENT_FACT_ONLY"]
      rule: "The matrix prevents a circular requirement for a plan or decision before an estimate can be inspected while still validating the estimate's exact scope, capacity, dependency, method, evidence, preparer, reservation, and time authorities. Permitted absence means no selected row for this work item; it never permits a missing registry, malformed history, stale selected estimate binding, or favorable caller subset."
    required_sources:
      - {role: "ESTIMATE", source: "complete content-addressed EstimateAuthorityRegistryV2"}
      - {role: "PLAN", source: "complete content-addressed IntegratedPlanAuthorityRegistryV1"}
      - {role: "SCOPE", source: "complete content-addressed ScopeAuthorityRegistryV1"}
      - {role: "CAPACITY", source: "complete content-addressed CapacityAuthorityRegistryV1"}
      - {role: "DEPENDENCY", source: "complete content-addressed DependencyAuthorityRegistryV1"}
      - {role: "RISK", source: "complete content-addressed RiskAuthorityRegistryV1"}
      - {role: "ACCEPTANCE", source: "complete content-addressed AcceptanceAuthorityRegistryV1"}
      - {role: "OWNER", source: "complete content-addressed AccountableOwnerAuthorityRegistryV1"}
      - {role: "DECISION", source: "complete content-addressed CommitmentDecisionAuthorityRegistryV1"}
      - {role: "TRACE", source: "complete content-addressed CoreSdlcTraceAuthorityRegistryV1"}
      - {role: "TIME", source: "complete content-addressed TrustedTimeAuthorityRegistryV1"}
    fail_closed_on:
      - "untrusted adapter/key, invalid signature, absent/stale/reused challenge or nonce, replay-ledger drift, authority-manifest drift, history-anchor drift, prior-publication mismatch, deleted history, or re-rooted registry"
      - "missing, duplicate, unknown, malformed, stale, expired, revoked, denied, superseded, wrong-subject, wrong-work-item, digest-drifted, cross-snapshot, unauthenticated, or unresolved selected/current binding; retained historical rows remain mandatory but cannot satisfy a current binding"
      - "V1, unversioned, raw-list, mixed-version, partial-history, caller-filtered, defaulted, synthesized, or auto-migrated source input"
      - "plan estimate population differs from the complete CURRENT same-work-item estimate population"
      - "estimate presented where a commitment decision is required"
      - "any fired recommit trigger without a newly resolved exact-subject decision"
    evaluation_order: ["V2_ENVELOPE_SCHEMA", "SOURCE_ADAPTER_SIGNATURE_REPLAY_AND_AUTHORITY_MANIFEST", "ALL_ROLE_REGISTRY_DIGESTS_PRIOR_PUBLICATIONS_AND_COMPLETE_HISTORY", "TRUSTED_TIME", "ESTIMATE_RESERVATION_METHOD_EVIDENCE_PREPARER", "DERIVE_CURRENT_HEADS_AND_VALIDATE_SELECTED_ROW_CAUSALITY", "PLAN_COMPLETE_ESTIMATE_POPULATION", "SUBJECT_PROJECTION", "AUTHENTICATION_AND_EXACT_OWNER_ROLE", "DECISION_CURRENTNESS_AND_SUPERSESSION", "RECOMMIT_INVALIDATION", "AUTHORITY_BOUNDARY", "ESTIMATE_ONLY_NONAUTHORITY_OR_COMMITMENT_RECEIPT"]
    early_return_rule: "No ESTIMATE_ONLY or other receipt is returned until the adapter signature, replay reservation/ledger, authority manifest, every source schema/digest/prior-publication chain/complete history, current-head derivation, selected-row causality, binding, and authority-boundary step succeeds."
    production_callers:
      - "SDLC-PLN-001 READY exit evaluation"
      - "any policy query that reports or relies on a delivery commitment"
    optional_or_fixture_only_bypass: false

  fixture_contract:
    positive_suite_id: "SDLC_ESTIMATE_COMMITMENT_POSITIVE_V2"
    positive_fixture_ref: "schemas/fixtures/semantic/estimate-commitment-positive-cases.json"
    negative_suite_id: "SDLC_ESTIMATE_COMMITMENT_NEGATIVE_V2"
    negative_fixture_ref: "schemas/fixtures/negative/estimate-commitment-negative-cases.json"
    case_id_order: "BYTEWISE_CASE_ID"
    fixture_shape_rule: "Each fixture is a closed object with case_id, source_envelope_version, query_kind, one named mutation or NONE, expected_result, expected_failure_code or JSON null, and expected_authority_effects. IDs and mutations are unique; every required ID appears exactly once; no unregistered case counts toward the denominator."
    positive_case_ids:
      - "POS-COMMITMENT-CURRENT-EXACT-V2"
      - "POS-ESTIMATE-ONLY-NONAUTHORITATIVE-COMPLETE-V2"
      - "POS-ESTIMATE-ONLY-NONAUTHORITATIVE-NO-COMMITMENT-ROWS-V2"
      - "POS-MOST-LIKELY-NULL-STRICT-RANGE-V2"
      - "POS-OFFLINE-V1-TO-V2-MIGRATION-VALIDATED"
      - "POS-RECOMMIT-CURRENT-CHANGED-BINDING-V2"
    exact_positive_case_count: 6
    negative_case_ids_by_boundary:
      source_envelope_and_migration:
        - "NEG-SOURCE-ATTESTATION-CHALLENGE-REUSE"
        - "NEG-SOURCE-ATTESTATION-DIGEST-MISMATCH"
        - "NEG-SOURCE-ATTESTATION-EXPIRED"
        - "NEG-SOURCE-ATTESTATION-KEY-DIGEST-MISMATCH"
        - "NEG-SOURCE-ATTESTATION-MISSING"
        - "NEG-SOURCE-ATTESTATION-SIGNATURE-INVALID"
        - "NEG-SOURCE-ATTESTATION-UNTRUSTED-ADAPTER"
        - "NEG-SOURCE-AUTOMATIC-V1-WRAP"
        - "NEG-SOURCE-CALLER-FILTERED-REGISTRY"
        - "NEG-SOURCE-CALLER-SUPPLIED-ENVELOPE"
        - "NEG-SOURCE-EXTRA-ROLE"
        - "NEG-SOURCE-FUTURE-REGISTRY-PUBLICATION"
        - "NEG-SOURCE-MISSING-ROLE"
        - "NEG-SOURCE-MIXED-V1-V2"
        - "NEG-SOURCE-PARTIAL-MIGRATION"
        - "NEG-SOURCE-PARTIAL-REGISTRY-HISTORY"
        - "NEG-SOURCE-RAW-V1-ESTIMATE-LIST"
        - "NEG-SOURCE-REGISTRY-DIGEST-DRIFT"
        - "NEG-SOURCE-REGISTRY-GENERATION-REGRESSION"
        - "NEG-SOURCE-REGISTRY-HISTORY-ANCHOR-MISMATCH"
        - "NEG-SOURCE-REGISTRY-PRIOR-PUBLICATION-DIGEST-MISMATCH"
        - "NEG-SOURCE-REGISTRY-RE-ROOTED-HISTORY"
        - "NEG-SOURCE-REGISTRY-ROW-DELETION"
        - "NEG-SOURCE-REPLAY-LEDGER-DIGEST-DRIFT"
        - "NEG-SOURCE-REPLAY-PRIOR-RESERVATION-DIGEST-MISMATCH"
        - "NEG-SOURCE-REPLAY-RESERVATION-MISSING"
        - "NEG-SOURCE-REPLAY-RESERVATION-REUSE"
        - "NEG-SOURCE-REPLAY-STALE-CURRENT-REGISTRY"
        - "NEG-SOURCE-UNKNOWN-ROLE"
        - "NEG-SOURCE-UNVERSIONED-ENVELOPE"
        - "NEG-SOURCE-V1-ENVELOPE"
      estimate_identity_and_history:
        - "NEG-ESTID-ADMISSION-BEFORE-RESERVATION"
        - "NEG-ESTID-ADMITTED-DIGEST-MISMATCH"
        - "NEG-ESTID-DUPLICATE-RESERVATION"
        - "NEG-ESTID-HISTORY-CYCLE"
        - "NEG-ESTID-HISTORY-DELETION"
        - "NEG-ESTID-HISTORY-FORK"
        - "NEG-ESTID-HISTORY-ORPHAN-GENERATION"
        - "NEG-ESTID-HISTORY-PRIOR-DIGEST-MISMATCH"
        - "NEG-ESTID-HISTORY-REWRITE"
        - "NEG-ESTID-MISSING-RESERVATION"
        - "NEG-ESTID-ORPHAN-RESERVATION"
        - "NEG-ESTID-RESERVED-AFTER-ESTIMATE-OBSERVATION"
        - "NEG-ESTID-REUSE-CROSS-WORK-ITEM"
        - "NEG-ESTID-REUSE-SAME-WORK-ITEM"
      method_evidence_and_preparer:
        - "NEG-EVIDENCE-ARTIFACT-DIGEST-MISMATCH"
        - "NEG-EVIDENCE-BINDING-DUPLICATE"
        - "NEG-EVIDENCE-BINDING-OUT-OF-ORDER"
        - "NEG-EVIDENCE-CROSS-LINEAGE-ID"
        - "NEG-EVIDENCE-CROSS-WORK-ITEM"
        - "NEG-EVIDENCE-MISSING-AUTHORITY-ROW"
        - "NEG-EVIDENCE-REF-VERSION-MISMATCH"
        - "NEG-EVIDENCE-ROW-DIGEST-MISMATCH"
        - "NEG-EVIDENCE-STALE-AT-ESTIMATE-OBSERVATION"
        - "NEG-METHOD-CROSS-LINEAGE-ID"
        - "NEG-METHOD-CROSS-WORK-ITEM"
        - "NEG-METHOD-DEFINITION-DIGEST-MISMATCH"
        - "NEG-METHOD-MISSING-AUTHORITY-ROW"
        - "NEG-METHOD-REF-VERSION-MISMATCH"
        - "NEG-METHOD-ROW-DIGEST-MISMATCH"
        - "NEG-METHOD-STALE-AT-ESTIMATE-OBSERVATION"
        - "NEG-METHOD-SYNTHESIZED-BY-RESOLVER"
        - "NEG-PREPARER-AUTHORITY-ESCALATION"
        - "NEG-PREPARER-CROSS-WORK-ITEM"
        - "NEG-PREPARER-MISSING-PROVENANCE"
        - "NEG-PREPARER-PRINCIPAL-MISMATCH"
        - "NEG-PREPARER-STALE-AUTHENTICATION"
        - "NEG-PREPARER-UNAUTHENTICATED"
      estimate_value_and_currentness:
        - "NEG-ESTIMATE-ASSUMPTIONS-DUPLICATE"
        - "NEG-ESTIMATE-ASSUMPTIONS-EMPTY"
        - "NEG-ESTIMATE-ASSUMPTIONS-OUT-OF-ORDER"
        - "NEG-ESTIMATE-DIGEST-MISMATCH"
        - "NEG-ESTIMATE-EVIDENCE-BINDINGS-DUPLICATE"
        - "NEG-ESTIMATE-EVIDENCE-BINDINGS-EMPTY"
        - "NEG-ESTIMATE-EVIDENCE-BINDINGS-OUT-OF-ORDER"
        - "NEG-ESTIMATE-EXPIRED"
        - "NEG-ESTIMATE-FUTURE-OBSERVATION"
        - "NEG-ESTIMATE-INVALID-VALIDITY-INTERVAL"
        - "NEG-ESTIMATE-LOWER-EQUAL-UPPER"
        - "NEG-ESTIMATE-LOWER-GREATER-UPPER"
        - "NEG-ESTIMATE-MOST-LIKELY-ABOVE-UPPER"
        - "NEG-ESTIMATE-MOST-LIKELY-BELOW-LOWER"
        - "NEG-ESTIMATE-MOST-LIKELY-EQUAL-LOWER"
        - "NEG-ESTIMATE-MOST-LIKELY-EQUAL-UPPER"
        - "NEG-ESTIMATE-MOST-LIKELY-STRING-NULL"
        - "NEG-ESTIMATE-STALE-SUPERSEDED"
        - "NEG-ESTIMATE-SUBJECT-SCHEMA-NOT-WORK-ITEM-SCOPE-V1"
        - "NEG-ESTIMATE-SUPERSESSION-CROSS-SERIES-SIGNATURE"
        - "NEG-ESTIMATE-SUPERSESSION-CROSS-WORK-ITEM"
        - "NEG-ESTIMATE-SUPERSESSION-CYCLE"
        - "NEG-ESTIMATE-SUPERSESSION-FORK"
        - "NEG-ESTIMATE-SUPERSESSION-NONCHRONOLOGICAL"
      plan_population_and_window:
        - "NEG-PLAN-BOUND-SOURCE-VALIDITY-END-BEFORE-WINDOW"
        - "NEG-PLAN-CALLER-OVERRIDDEN-WINDOW"
        - "NEG-PLAN-CROSS-WORK-ITEM"
        - "NEG-PLAN-DIGEST-DRIFT"
        - "NEG-PLAN-DUPLICATE-ESTIMATE-ID"
        - "NEG-PLAN-ESTIMATE-ID-OUT-OF-ORDER"
        - "NEG-PLAN-EXPIRED"
        - "NEG-PLAN-EXTRA-ESTIMATE-ID"
        - "NEG-PLAN-HARDCODED-WINDOW"
        - "NEG-PLAN-MISSING-CURRENT-PLAN"
        - "NEG-PLAN-MULTIPLE-CURRENT-PLANS"
        - "NEG-PLAN-OMITTED-CURRENT-ESTIMATE-ID"
        - "NEG-PLAN-PROJECTION-WINDOW-NOT-EXACT-COPY"
        - "NEG-PLAN-STALE"
        - "NEG-PLAN-WINDOW-END-AFTER-VALID-UNTIL"
        - "NEG-PLAN-WINDOW-EQUAL-ENDPOINTS"
        - "NEG-PLAN-WINDOW-REVERSED"
        - "NEG-PLAN-WRONG-OWNER-BINDING"
        - "NEG-PLAN-WRONG-ROLE-BINDING-DIGEST"
      business_role_authorities:
        - "NEG-ACCEPTANCE-CRITERIA-NOT-EQUAL-SCOPE"
        - "NEG-ACCEPTANCE-CROSS-WORK-ITEM"
        - "NEG-ACCEPTANCE-DEFINITION-DIGEST-DRIFT"
        - "NEG-ACCEPTANCE-MISSING-CURRENT-ROW"
        - "NEG-ACCEPTANCE-STALE"
        - "NEG-ACCEPTANCE-VERIFICATION-POPULATION-MALFORMED"
        - "NEG-CAPACITY-BUSINESS-PAYLOAD-MISMATCH"
        - "NEG-CAPACITY-CROSS-WORK-ITEM"
        - "NEG-CAPACITY-DIGEST-DRIFT"
        - "NEG-CAPACITY-ESTIMATE-BINDING-MISMATCH"
        - "NEG-CAPACITY-MISSING-CURRENT-ROW"
        - "NEG-CAPACITY-STALE"
        - "NEG-DEPENDENCY-BUSINESS-PAYLOAD-MISMATCH"
        - "NEG-DEPENDENCY-CROSS-WORK-ITEM"
        - "NEG-DEPENDENCY-DIGEST-DRIFT"
        - "NEG-DEPENDENCY-ESTIMATE-BINDING-MISMATCH"
        - "NEG-DEPENDENCY-MISSING-CURRENT-ROW"
        - "NEG-DEPENDENCY-STALE"
        - "NEG-RISK-BUSINESS-PAYLOAD-MISMATCH"
        - "NEG-RISK-CROSS-WORK-ITEM"
        - "NEG-RISK-DIGEST-DRIFT"
        - "NEG-RISK-MISSING-CURRENT-ROW"
        - "NEG-RISK-STALE"
        - "NEG-SCOPE-BUSINESS-POPULATION-MISMATCH"
        - "NEG-SCOPE-CROSS-WORK-ITEM"
        - "NEG-SCOPE-DEFINITION-DIGEST-DRIFT"
        - "NEG-SCOPE-MISSING-CURRENT-ROW"
        - "NEG-SCOPE-STALE"
      owner_trace_and_time:
        - "NEG-OWNER-CROSS-WORK-ITEM"
        - "NEG-OWNER-DIGEST-DRIFT"
        - "NEG-OWNER-MISSING-CURRENT-ASSIGNMENT"
        - "NEG-OWNER-MULTIPLE-CURRENT-ASSIGNMENTS"
        - "NEG-OWNER-PRINCIPAL-MISMATCH"
        - "NEG-OWNER-STALE"
        - "NEG-OWNER-WRONG-ROLE-ID"
        - "NEG-TIME-CHAIN-FORK"
        - "NEG-TIME-DIGEST-DRIFT"
        - "NEG-TIME-INSTANT-NONMONOTONIC"
        - "NEG-TIME-MISSING-CURRENT-OBSERVATION"
        - "NEG-TIME-MONOTONIC-COUNTER-REGRESSION"
        - "NEG-TIME-PREVIOUS-DIGEST-MISMATCH"
        - "NEG-TIME-STALE-AT-EVALUATION"
        - "NEG-TIME-UNTRUSTED-SOURCE"
        - "NEG-TRACE-CROSS-WORK-ITEM"
        - "NEG-TRACE-DIGEST-DRIFT"
        - "NEG-TRACE-MISSING-CURRENT-BINDING"
        - "NEG-TRACE-SCHEMA-MISMATCH"
        - "NEG-TRACE-STALE"
      decision_authority:
        - "NEG-DECISION-ACTION-ADAPTER-ID"
        - "NEG-DECISION-ACTION-ADAPTER-VERSION"
        - "NEG-DECISION-ACTION-CANONICAL-ARGUMENT-DIGEST"
        - "NEG-DECISION-ACTION-DESTINATION"
        - "NEG-DECISION-ACTION-TYPE"
        - "NEG-DECISION-ARTIFACT-DIGEST-MISMATCH"
        - "NEG-DECISION-ARTIFACT-MISSING"
        - "NEG-DECISION-ARTIFACT-REGISTERED-BEFORE-ISSUE"
        - "NEG-DECISION-AUTHENTICATION-CONTEXT-MISMATCH"
        - "NEG-DECISION-AUTHENTICATION-EXPIRED"
        - "NEG-DECISION-AUTHENTICATOR-DIGEST-MISMATCH"
        - "NEG-DECISION-AUTHENTICATOR-REVOKED"
        - "NEG-DECISION-CHALLENGE-DIGEST-MISMATCH"
        - "NEG-DECISION-CHANGED-BINDING-WITHOUT-RECOMMIT"
        - "NEG-DECISION-CONDITIONS-DUPLICATE"
        - "NEG-DECISION-CONDITIONS-EXTRA"
        - "NEG-DECISION-CONDITIONS-MISSING"
        - "NEG-DECISION-CONDITIONS-OUT-OF-ORDER"
        - "NEG-DECISION-DUPLICATE-CURRENT"
        - "NEG-DECISION-ESTIMATE-USED-AS-COMMITMENT"
        - "NEG-DECISION-EXPIRED"
        - "NEG-DECISION-EXPIRES-AT-NOT-PLAN-WINDOW-END"
        - "NEG-DECISION-ISSUED-AFTER-TRUSTED-TIME"
        - "NEG-DECISION-ISSUED-BEFORE-BOUND-AUTHORITY"
        - "NEG-DECISION-ISSUED-BEFORE-PLAN-WINDOW"
        - "NEG-DECISION-MISSING"
        - "NEG-DECISION-NONCE-DIGEST-MISMATCH"
        - "NEG-DECISION-OUTCOME-NOT-APPROVED"
        - "NEG-DECISION-OVERLAPPING-CURRENT-WINDOW"
        - "NEG-DECISION-PRINCIPAL-NOT-OWNER"
        - "NEG-DECISION-REVOKED"
        - "NEG-DECISION-SCOPE-DUPLICATE"
        - "NEG-DECISION-SCOPE-EXTRA"
        - "NEG-DECISION-SCOPE-MISSING"
        - "NEG-DECISION-SCOPE-OUT-OF-ORDER"
        - "NEG-DECISION-STATUS-NOT-APPROVED"
        - "NEG-DECISION-SUBJECT-DIGEST-MISMATCH"
        - "NEG-DECISION-SUBJECT-MANIFEST-DIGEST-MISSING"
        - "NEG-DECISION-SUBJECT-MANIFEST-DIGEST-NONNULL"
        - "NEG-DECISION-SUBJECT-REF-MISMATCH"
        - "NEG-DECISION-SUPERSEDED-PRIOR-PRESENTED"
        - "NEG-DECISION-SUPERSESSION-CROSS-WORK-ITEM"
        - "NEG-DECISION-SUPERSESSION-CYCLE"
        - "NEG-DECISION-SUPERSESSION-FORK"
        - "NEG-DECISION-SUPERSESSION-NONCHRONOLOGICAL"
        - "NEG-DECISION-SUPERSESSION-SKIPS-IMMEDIATE-PRIOR"
        - "NEG-DECISION-TRACE-MISMATCH"
        - "NEG-DECISION-WRONG-KIND"
      authority_boundary:
        - "NEG-AUTHORITY-ESCALATION-GATE-PASS"
        - "NEG-AUTHORITY-ESCALATION-GRANT"
        - "NEG-AUTHORITY-ESCALATION-LANDING"
        - "NEG-AUTHORITY-ESCALATION-PERMIT"
        - "NEG-AUTHORITY-ESCALATION-RELEASE"
        - "NEG-AUTHORITY-ESCALATION-STATE-TRANSITION"
    exact_negative_case_count: 213
    invariant_matrix_rule: "In addition to the named semantic cases, schema mutation tests omit every required field once, substitute every disallowed type/null once, add one unknown field at every closed object level, and mutate every const/enum once. These matrix cases are reported separately and do not inflate the named semantic denominator."
```

<!-- END SDLC ESTIMATE COMMITMENT CONTROL -->

Evidence basis: `PRAC` *The Clean Coder* estimate-versus-commitment
distinction; `STD` ISO/IEC 29110 planning and control; `GOV`
NASA-HDBK-2203 project planning/control; `OWNER` Ranex exact-subject and
noncompensation policy.

### SDLC-CM-001 — Configuration management

Configuration items include, where applicable:

- needs, requirements, decisions, ADRs and contracts;
- source, generated code, schemas and migrations;
- prompts, model/route specifications and provider catalogs;
- tests, test data, expected results and qualified tools;
- dependencies, lockfiles, toolchains and build instructions;
- deployment/installation configuration and environment descriptions;
- runbooks, user/operator documentation, findings and waivers; and
- artifacts, manifests, SBOMs, attestations and release/retirement records.

The configuration manager/build custodian:

1. identifies item, owner, system of record and retention;
2. establishes named content-addressed baselines;
3. applies authorized change control;
4. maintains configuration status accounting;
5. proves reproducible build and detects environment/configuration drift;
6. performs functional and physical configuration audits;
7. archives and retrieves exact released/retired baselines; and
8. reconciles emergency changes into normal control.

`RELEASE_READY` requires evidence that requirements, source, build inputs,
artifact, configuration, tests/results, documentation, defects/waivers and
release record are mutually consistent.

Evidence basis: `GOV` NASA-HDBK-2203; `GOV` NIST SSDF; `OWNER`.

### SDLC-TR-001 — Bidirectional traceability

Required links:

```text
need/outcome <-> software requirement
requirement <-> risk/hazard/misuse control
requirement <-> design component
design <-> code/configuration item
requirement <-> verification and validation evidence
requirement <-> defect/nonconformance/waiver
```

Definition, Design, Verification and Release Ready run orphan and unjustified
extra-element checks. Changing a source marks dependent links/evidence stale
until impact analysis and re-verification complete.

Evidence basis: `GOV` NASA-HDBK-2203; `OWNER`.

### SDLC-VV-001 — Verification, validation and acceptance

- **Verification** proves specified requirements/design were implemented
  correctly.
- **Validation** shows representative use satisfies intended user need/context.

Every record names need/requirement, exact subject, verifier, method,
environment/configuration baseline, test data, expected/actual result,
anomaly/waiver, date and durable evidence. Acceptance names the version,
conditions/deviations, human authority and date.

| Lane | Minimum independence |
|---|---|
| Standard | Fresh reviewer who did not make the change |
| Enhanced | Different maker and independent V&V/test authority |
| Critical | Independent qualified specialist; maker/implementation owner cannot accept critical security, data, authority or recovery V&V |
| Emergency | Independent check when available, then full lane-appropriate V&V after mitigation |

The V&V authority may reject the environment/baseline, require anomaly
resolution or regression expansion, veto a factual pass, and escalate. It
cannot accept product/risk value for the human owner. No waiver turns a factual
failure into `PASS`.

Evidence basis: `GOV` NASA-HDBK-2203; `PRAC` Google Engineering Practices;
`OWNER`.

### SDLC-SUP-001 — Supplier and dependency governance

Applies to packages, toolchains, models, APIs, providers, plugins/extensions,
hosted services and Hermes upstream. A supplier owner records:

- make/buy/adopt/reuse decision and alternatives;
- functionality, quality, security, privacy, license/provenance, support and
  exit requirements;
- viability, concentration, transitive and lock-in risks;
- acceptance tests and shared-responsibility matrix;
- pinned/version/update and vulnerability/end-of-life monitoring;
- incident notification/escalation;
- contingency, replacement, export/deletion and termination; and
- reassessment date and residual-risk authority.

An SBOM is evidence, not acceptance by itself.

Evidence basis: `GOV` NIST SSDF; `GOV` NASA-HDBK-2203; `OWNER`.

### SDLC-DEBT-001 — Technical debt

Any accepted shortcut, exception, temporary flag, compatibility shim, skipped
automation, degraded test or deferred cleanup creates a debt record. It names
affected configuration items, type/cause, remediation estimate range, observed
or expected interest, risk, owner, review/expiry and trigger.

Expired or triggered debt returns to triage. Track age, interest signals,
expired items and remediation throughput—not raw count or people.

Evidence basis: `OWNER`, supported by `OBS` DORA maintainability/flow guidance.

### SDLC-TAIL-001 — Tailoring

Each project or material change binds a baseline profile and records invoked,
omitted or modified controls, rationale, compensating controls, approver,
expiry and review triggers.

Truthfulness, exact-subject evidence, traceability, evidence integrity, legal
and secret protection, cross-project isolation, human risk authority, and the
ban on maker self-approval are not tailorable. Risk lanes are pre-approved
assurance profiles; tailoring is not an emergency waiver.

Evidence basis: `STD` ISO/IEC 29110 scope; `GOV` NASA tailoring; `MODEL` CMMI;
`OWNER`.

### SDLC-MEA-001 — Measurement

Before a metric governs a decision, specify: goal and question served,
construct, operational definition/formula, entity and unit, event source,
population, start/stop events, exclusions, data-quality and uncertainty checks,
owner, cadence, baseline/control limit, paired guardrail, retention, triggered
decision and anti-gaming risk. Remove a metric that serves no decision.

Accepted specifications live in versioned registry `METRIC-SDLC-001`. Each
`MetricSpec` has `DRAFT`, `ACCEPTED`, or `SUPERSEDED` status, a stable ID, the
fields above, an owner, an approver, and a correction history. The listed
measure families below are candidate coverage, not a claim that their
operational specifications or baselines already exist.

The catalog covers outcome, flow, DORA delivery measures, requirement
volatility, defect leakage, estimate calibration distributions, review/test
effectiveness, configuration drift, dependencies/maintenance, supplier
incidents, debt age/interest, retirement exceptions and V&V escaped defects.
`SDLC-ADOPT-A/E` must register the actual specifications before they govern a
decision.

A measurement harness or query system has a version/configuration digest,
qualification evidence, repeatability/data-quality tests, and an
infrastructure-error ledger. Level-`3`/`4` claims cannot rely on an unqualified
measurement system.

Evidence basis: `OBS` DORA; `MODEL` CMMI; `OWNER`.

### SDLC-MEA-002 — Capability assessment and improvement selection

This section defines capability rubric `SDLC-MEA-002`, version `3.0.0`.

Capability assessment is diagnostic and evidence-bound. The assessment unit is
one normative control or named capability for a declared value stream/service,
work class, risk-lane set, policy/rubric version and review window. A work-item
gate outcome remains separate and can never borrow authority from a historical
process score.

Each versioned `CapabilityAssessment` reports:

- result: `NOT_ASSESSED`, `UNKNOWN`, `NOT_APPLICABLE`, or `SCORED`; only
  `SCORED` has a level: `0` `ABSENT`, `1` `DEFINED`, `2` `OPERATED`, `3`
  `CONTROLLED`, or `4` `IMPROVING`;
- effectiveness: `UNKNOWN`, `REGRESSING`, `MIXED`, or `MEETS_TARGET`;
- coverage: eligible/included/excluded counts and percentage by work class and
  risk lane; and
- confidence: `LOW`, `MEDIUM`, or `HIGH`, with sample, duration,
  representativeness, missingness, authenticity and data-quality rationale.

When result is not `SCORED`, level is absent. The levels are ordinal labels.
Ordering and counts by label inside one value stream/profile over time are
allowed; arithmetic distance, addition, weighting, means, ratios, cross-team
league tables, and a process-wide overall score are prohibited.

A numeric level requires criterion evidence for that level and every lower
level. Documentation alone cannot exceed `1`. Representative level-`2`
evidence includes a normal path and at least one rejection, invalidation,
exception, or backward path actually traversed and bound to durable events;
documenting a possible path is insufficient. Level `3` requires governed
operation over declared windows with visible distributions, false passes,
misses, exceptions and triggered responses, plus qualified metric/query
evidence. Level `4` requires a prospectively frozen improvement experiment
whose sustained benefit clears declared uncertainty/local noise over more than
one review window, whose counter-metrics survive independent review, and whose
infrastructure faults are reported separately from subject failures.

Evidence is evaluated across enacted practice, durable artifact/provenance, and
outcome/guardrail behavior. Proxy counts such as coverage, documents, lines of
code or entity counts are diagnostic locators, not direct success measures.
Failed required tests and disabled safeguards remain non-compensating findings.

`NOT_ASSESSED` and `UNKNOWN` are not numeric zero and are not passes.
`NOT_APPLICABLE` requires a rule in applicability registry
`APPLICABILITY-SDLC-001`, an immutable eligible-population query, reason, and
accountable approval. It is invalid when eligible work or a qualifying trigger
exists in-window; applicability ambiguity produces `UNKNOWN`. Profiles publish
N/A counts/rates by domain, work class and lane. Independent assurance samples
N/A dispositions and the breadth of their rules.

Applicability registry `APPLICABILITY-SDLC-001`, version `1.1.0`, contains:

| Rule | Meaning |
|---|---|
| `APP-CROSS-001` | Cross-lifecycle control applies to every material in-scope work item |
| `APP-STAGE-001` | Stage control applies when eligible work entered or should have entered that canonical state |
| `APP-TRIGGER-001` | Linked maintenance, retirement, exception, rollback, supplier, or similar control applies when its declared trigger exists |
| `APP-FORK-BASE-001` | Persistent fork ancestry, inherited-behavior, compatibility/integration-surface, and reconciliation controls apply to Ranex in every review window |
| `APP-FORK-SYNC-001` | Upstream-sync control applies when an observation/cadence obligation, candidate, classification, disposition, port, or baseline decision is due or exists in-window |
| `APP-FORK-UPDATE-001` | Release/update control applies when an update obligation, candidate, staged change, activation, or recovery exists in-window |
| `APP-FORK-CUTOVER-001` | Cutover/self-development control applies when an operating-mode, canonical-writer, controller/candidate, or cutover obligation/change exists in-window |
| `APP-AIW-001` | AI-worker fleet controls apply whenever more than one agent/worker is dispatched or fleet machinery affects evidence, selection, landing, or authority |

Vital-control profile `VITAL-SDLC-001`, version `1.2.0`, is owned by the human
governor. Assessment authors cannot alter it. A change requires a new profile
version and governed policy/ADR decision.

The profile is a set of exact
`(domain_id, control_id, applicability_rule_id)` tuples. Each tuple has exactly
one rule, so assessment authors never choose an `AND`/`OR` interpretation.
Applicability rules may be changed only by versioning the registry and profile.

| Domain ID | Capability domain | Control ID | Applicability rule |
|---|---|---|---|
| `CAP-INTAKE-TRIAGE` | Intake and triage | `SDLC-INT-001` | `APP-STAGE-001` |
| `CAP-INTAKE-TRIAGE` | Intake and triage | `SDLC-TRI-001` | `APP-STAGE-001` |
| `CAP-DISCOVERY-DEFINITION` | Discovery and definition | `SDLC-DIS-001` | `APP-STAGE-001` |
| `CAP-DISCOVERY-DEFINITION` | Discovery and definition | `SDLC-DEF-001` | `APP-STAGE-001` |
| `CAP-DESIGN-READINESS` | Design and readiness | `SDLC-DES-001` | `APP-STAGE-001` |
| `CAP-DESIGN-READINESS` | Design and readiness | `SDLC-PLN-001` | `APP-STAGE-001` |
| `CAP-DESIGN-READINESS` | Design and readiness | `SDLC-EST-001` | `APP-STAGE-001` |
| `CAP-BUILD-FLOW` | Build and flow | `SDLC-BLD-001` | `APP-STAGE-001` |
| `CAP-BUILD-FLOW` | Build and flow | `SDLC-BLK-001` | `APP-TRIGGER-001` |
| `CAP-VERIFY-VALIDATE` | Verification and validation | `SDLC-VV-001` | `APP-CROSS-001` |
| `CAP-VERIFY-VALIDATE` | Verification and validation | `SDLC-VER-001` | `APP-STAGE-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-CM-001` | `APP-CROSS-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-RDY-001` | `APP-STAGE-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-REL-001` | `APP-STAGE-001` |
| `CAP-RELEASE-RECOVERY` | Release and recovery | `SDLC-RBK-001` | `APP-TRIGGER-001` |
| `CAP-OPERATE-MAINTAIN` | Operation, incident, and maintenance | `SDLC-OPS-001` | `APP-STAGE-001` |
| `CAP-OPERATE-MAINTAIN` | Operation, incident, and maintenance | `SDLC-MNT-001` | `APP-TRIGGER-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-OUT-001` | `APP-STAGE-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-CLS-001` | `APP-STAGE-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-CAN-001` | `APP-TRIGGER-001` |
| `CAP-OUTCOME-CLOSE-RETIRE` | Outcome, closure, and retirement | `SDLC-RET-001` | `APP-TRIGGER-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-TR-001` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-TAIL-001` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-MEA-001` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-MEA-002` | `APP-CROSS-001` |
| `CAP-GOVERN-EVIDENCE` | Evidence, measurement, authority, and exceptions | `SDLC-PA-001` | `APP-CROSS-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-000` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-001` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-002` | `APP-FORK-SYNC-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-003` | `APP-FORK-UPDATE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-004` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-005` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-006` | `APP-FORK-CUTOVER-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-FORK-007` | `APP-FORK-BASE-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-001` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-002` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-003` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-004` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-005` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-006` | `APP-AIW-001` |
| `CAP-HERMES-AI-HEALTH` | Hermes fork and AI-worker health | `SDLC-AIW-007` | `APP-AIW-001` |

A domain projection binds one immutable assessment ID, revision, and digest for
every registered tuple in that domain, all for the identical service/value
stream, work-class and risk-lane scope, policy/rubric versions, and review
window. Missing, extra, duplicate, rule-mismatched, stale, or cross-scope rows
invalidate the projection; the result and priority are derived, never authored.
Use the executable authoring skeleton
[`CAPABILITY_DOMAIN_PROJECTION.yaml`](./templates/CAPABILITY_DOMAIN_PROJECTION.yaml)
whose registered schema is
[`capability-domain-projection-v1.schema.json`](../../schemas/process/capability-domain-projection-v1.schema.json).

For projection derivation, an **applicable member** is a registered tuple whose
applicability result resolved to `APPLICABLE`. A valid
`NOT_APPLICABLE` member remains in the complete tuple set but is not an
applicable member and never enters the level floor. An applicable assessment
has begun when at least one applicable member rating is no longer
`NOT_ASSESSED`.

For a valid projection, a domain result is deterministic:

1. Unresolved applicability or an invalid N/A disposition produces `UNKNOWN`.
2. If every registered tuple is validly `NOT_APPLICABLE`, the domain is
   `NOT_APPLICABLE` and has no level or priority tier.
3. With at least one applicable member, the domain is `NOT_ASSESSED` only when
   every applicable member rating is `NOT_ASSESSED`.
4. Once at least one applicable member rating is no longer `NOT_ASSESSED`, any
   applicable member rated `UNKNOWN` or `NOT_ASSESSED` makes the domain
   `UNKNOWN`.
5. The domain is `SCORED` if and only if every applicable member is `SCORED`;
   its level is the lowest supported level among those members.

There is no arithmetic aggregation.

Confidence requires a versioned adequacy rule and recorded test results. `HIGH`
requires all declared sample, duration, representativeness, authenticity,
freshness, missingness, and data-quality tests to pass plus independent
assurance sign-off. Without an approved adequacy rule, confidence is at most
`MEDIUM`; a material unresolved population/evidence gap forces `LOW`. One gap
register inventories evidence, applicability, population, coverage and
measurement gaps. Every known gap needs a materiality and resolution
disposition; `HIGH` additionally requires a complete inventory and no
unresolved material gap. Any unresolved material gap makes the capability
rating `UNKNOWN` with no level and confidence `LOW`; it cannot coexist with a
`SCORED` result.

All population and coverage values derive from one immutable population
snapshot. Joint work-class/risk-lane strata are complete for the declared
scope, including zero-count strata. In each stratum and in total,
`eligible = included + excluded`; strata sum to totals and itemized exclusions
sum to the excluded count. Coverage percentage is derived from those totals,
not independently entered. Applicability and coverage reference that same
snapshot/query by pointer; they cannot carry competing copies.

Adverse populations use versioned typed predicates rather than one mixed
“class” list. At minimum they distinguish failed control/execution outcomes,
`BLOCKED`/`CANCELLED`/`ROLLED_BACK` status history, reopened attempt history,
and the `EMERGENCY` risk lane. Every category records immutable query digest
and eligible/included/excluded counts. A category passes only when no eligible
subject exists or every eligible subject is included with zero exclusions. A
`SCORED` record is invalid if any required applicable adverse category fails.

Priority registry `PRIORITY-SDLC-001`, version `1.0.0`, is total for every
applicable assessment. Evaluate tiers in `P0 -> P1 -> P2 -> P3` order; the
first matching tier wins:

- `P0 CONTROL_NOW` for active harm or a non-tailorable
  invariant/truth/authority/evidence/recovery breach;
- `P1 IMPROVE_NEXT` for result `NOT_ASSESSED`/`UNKNOWN`, level `0`/`1`, an
  overdue critical obligation, repeated escape, high-exposure downstream
  blockage, or `LOW`-confidence instrumentation need;
- `P2 IMPROVE_DELIBERATELY`, only absent P0/P1, for level `2`,
  `UNKNOWN`/`REGRESSING`/`MIXED` effectiveness, material
  flow/quality/outcome harm, or any remaining unproven P3 criterion; and
- `P3 SUSTAIN`, only absent P0–P2, for level `3`/`4`,
  `MEETS_TARGET`, passing coverage/adverse-population reconciliation, healthy
  guardrails, no adverse trend, and confidence above `LOW`.

The trigger-code registry is:

| Tier | Trigger codes |
|---|---|
| `P0` | `ACTIVE_HARM`, `NONTAILORABLE_INVARIANT_BREACH`, `NONTAILORABLE_TRUTH_BREACH`, `NONTAILORABLE_AUTHORITY_BREACH`, `NONTAILORABLE_EVIDENCE_BREACH`, `NONTAILORABLE_RECOVERY_BREACH` |
| `P1` | `RESULT_NOT_ASSESSED`, `RESULT_UNKNOWN`, `LEVEL_0`, `LEVEL_1`, `OVERDUE_CRITICAL_OBLIGATION`, `REPEATED_ESCAPE`, `HIGH_EXPOSURE_DOWNSTREAM_BLOCKAGE`, `LOW_CONFIDENCE_INSTRUMENTATION` |
| `P2` | `LEVEL_2`, `EFFECTIVENESS_UNKNOWN`, `EFFECTIVENESS_REGRESSING`, `EFFECTIVENESS_MIXED`, `MATERIAL_FLOW_QUALITY_OUTCOME_HARM`, `P3_CRITERIA_UNPROVEN` |
| `P3` | `P3_ALL_CRITERIA_PROVEN` |

Every trigger code is recorded exactly once as match/no-match for an applicable
assessment. `P3_CRITERIA_UNPROVEN` and `P3_ALL_CRITERIA_PROVEN` are mutually
exclusive and make the final branch total. The derived tier is the
highest-precedence tier containing any match; it cannot be typed manually.

Within a tier, consequence, exposure, recurrence, downstream blocking and
capability gap determine order. `LOW` confidence selects P1 and requires a
linked instrumentation/sampling action. A valid all-N/A assessment has no
priority tier. Domain priority is the highest-precedence member tier, never a
numeric average.

The per-control assessment record includes assessor/approver independence,
scope digest, applicability rule and immutable population snapshot; reconciled
totals and joint work-class/risk-lane strata; typed adverse-category query
digests and counts; N/A disposition/audit; event/evidence digest; criterion
evidence; measures/baseline/comparator; all seven named confidence-adequacy
tests and sign-off; invariant findings; exceptions; derived priority;
prior/superseded record; and correction reason. A separate immutable domain
projection binds every registry tuple and derives the floor and
highest-precedence member priority.

A linked improvement record names causal stage/control, hypothesis, bounded
change, and one immutable measurement-design reference. That design binds the
versioned metric specification, fixed comparator, primary measure, paired
guardrails, prospectively frozen decision rule, minimum meaningful/detectable
effect, declared uncertainty/local noise, and qualified harness ID/version/
configuration digest. The design also carries the separate
infrastructure-error ledger where relevant and is the sole owner of that
reference; the improvement record cannot restate a competing ledger. The
improvement record carries its owner, evidence window, stop/revert criteria and
retain/change/revert decision. Use the executable authoring skeletons
[`CAPABILITY_ASSESSMENT.yaml`](./templates/CAPABILITY_ASSESSMENT.yaml) and
[`CAPABILITY_DOMAIN_PROJECTION.yaml`](./templates/CAPABILITY_DOMAIN_PROJECTION.yaml)
with the registered
[`capability-assessment-v1.schema.json`](../../schemas/process/capability-assessment-v1.schema.json)
and
[`capability-domain-projection-v1.schema.json`](../../schemas/process/capability-domain-projection-v1.schema.json)
schemas.

For a level-`4` claim, the metric specification, fixed comparator,
prospectively frozen decision rule, uncertainty and analysis method,
decision-rule evaluation, harness qualification, and infrastructure-error
ledger are mandatory and bound by the measurement-design digest. Local noise
cannot default to zero. An established zero floor requires method evidence and
independent claim-specific approval. `NOT_APPLICABLE` uncertainty requires a
deterministic measure plus the exact approved uncertainty-N/A rule and
approval.

Ratings may open improvement work. They may not authorize a transition, issue a
permit, waive a control, lower risk, convert missing/failing evidence into
`PASS`, or evaluate individual performance. Independent assurance samples raw
events and audits exclusions, lane changes, exception growth, incident
suppression, delayed timestamps, threshold clustering and split/reopen
behavior.

#### Executable Wave 1 bindings

The documentation-contract baseline binds this rubric to:

- [`applicability-rules.json`](../../architecture/contracts/applicability-rules.json),
  [`priority-rules.json`](../../architecture/contracts/priority-rules.json), and
  [`vital-profile.json`](../../architecture/contracts/vital-profile.json);
- [`topology-rules.json`](../../architecture/contracts/topology-rules.json),
  [`paths.json`](../../architecture/contracts/paths.json),
  [`test-practices.json`](../../architecture/contracts/test-practices.json),
  and
  [`test-practice-profiles.json`](../../architecture/contracts/test-practice-profiles.json);
- ADR-0009 projections for declared dependency edges, boundary fit, coupling,
  and feedback fitness in
  [`context-dependency-edges.json`](../../architecture/contracts/context-dependency-edges.json),
  [`context-boundary-fitness.json`](../../architecture/contracts/context-boundary-fitness.json),
  [`context-coupling-policy.json`](../../architecture/contracts/context-coupling-policy.json),
  and [`feedback-fitness.json`](../../architecture/contracts/feedback-fitness.json);
- one exact-subject, non-compensating definition record for each of the 18
  topology, 26 TDD, ten boundary/feedback, and ten inherited-test-layout rules in
  [`architecture-rule-assessments.json`](../../architecture/contracts/architecture-rule-assessments.json);
- the 41 generated per-control records and ten deterministic domain projections
  under [`assessments/`](./assessments/); and
- the schema registry and semantic validator described by
  [`AI_ARTIFACT_CONTRACTS.md`](./AI_ARTIFACT_CONTRACTS.md).

Generator and validator execution is serialized by one repository-scoped
interprocess lock held across the complete read/cleanup/write or read/check/
report transaction. The disposable concurrency regression proves that a
validator cannot observe an empty assessment denominator, that a second writer
waits, and that the final generated-tree digest remains deterministic.

Every generated control record separates `definition_status: DEFINED` from the
runtime `capability_rating.result: NOT_ASSESSED`. Every generated projection is
`UNKNOWN` while applicability and runtime evidence remain unresolved. These
records prove tuple coverage and derivation mechanics; they are not maturity
scores, operating evidence, or adoption-gate passes. Runtime producer
enforcement and human `AI-G2` acceptance remain unassessed. The same honesty
rule applies to the 64 architecture-rule records: inventory coverage is
complete, but a paper definition cannot be promoted into an enacted-source,
behavioral, or maturity score.

Evidence basis: `OBS` DORA system measures; `MODEL` CMMI assessment lens;
`GOV` NASA/NIST assurance; `OWNER`.

### SDLC-PA-001 — Process assurance and competence

The process is itself controlled:

```text
proposal -> pilot -> evidence review -> human approval
  -> versioned rollout/training -> conformance/effectiveness review
  -> retain, improve, or retire
```

The process owner maintains versioned policies, schemas, templates, checks,
examples and migrations. An independent assurance role samples conformance and
artifact authenticity/completeness, records nonconformance, assigns corrective
action and verifies effectiveness. Quarterly management review examines
outcomes, flow, risk, exceptions, incidents, audits and improvement priorities.

Competence profiles and qualification evidence exist for maker, reviewer, V&V,
release, incident, security/data and configuration roles, with named backups
for critical duties. CMMI is an audit lens only; no maturity claim is made.

Evidence basis: `GOV` NASA assurance and NIST SSDF preparation; `MODEL` CMMI;
`OWNER`.

## 4. Complete stage contracts

Controls above apply to every row. `A` is accountable, `R` performs the work,
`C` must be consulted, and `I` is informed.

| Control/state | Purpose and precondition | Required inputs | Mandatory activities | Required outputs/evidence | R / A / C / I | Automated + human exit gates | Rejection/recovery | Tailoring and measures | Basis |
|---|---|---|---|---|---|---|---|---|---|
| `SDLC-INT-001` `FUNNEL` | Preserve a signal; source exists | User/stakeholder feedback, alert, incident, vulnerability, strategy or upstream observation | Assign ID; capture source/date/scope without inventing facts | Immutable signal record | Intake / duty owner / affected owner / reporter | Schema/duplicate/privacy scan + owner acknowledgment | Malformed/sensitive input quarantined; out-of-scope routed or cancelled | Summary may be minimal; measure intake age/source | `STD`,`OWNER` |
| `SDLC-TRI-001` `TRIAGE` | Establish ownership/disposition; valid signal | Signal, portfolio, service map, severity/risk rules | Classify work, urgency, risk lane, impact, owner, disposition and response target | Triage decision, initial risks, reason code | Duty/product / product owner / technical, service, security / reporter | Policy-derived lane + human priority/ownership | Insufficient facts → Funnel/Discovery; not ours → routed; no value → Cancelled | No silent lane lowering; measure time-to-triage and overrides | `STD`,`GOV`,`OWNER` |
| `SDLC-DIS-001` `DISCOVERY` | Validate problem/value; triaged item | Signal, users/actors, current behavior, research access | Research current behavior/users, baseline, alternatives, hypothesis, unknowns and falsifier | Discovery packet and evidence register | Research/product / product owner / technical, service, data / stakeholders | Evidence/source/unknown checks + product decision | Weak evidence → Discovery/Funnel/Cancelled | Standard fixes may use reproduction as discovery; measure learning time/hypothesis yield | `PRAC`,`OBS`,`OWNER` |
| `SDLC-DEF-001` `DEFINITION` | State testable need; supported problem | Discovery packet, constraints, policies | Define outcome, requirements, examples, qualities, non-goals, failure/misuse/recovery, measures; validate with affected user/owner | Baselined requirements and traceability | Requirements role / product owner / technical, V&V, service, security/data / delivery | Schema/orphan/testability checks + product/affected-owner validation | Ambiguous/unverifiable → Discovery/Definition | Artifact length varies, traceability does not; volatility and validation defects | `STD`,`GOV`,`OWNER` |
| `SDLC-DES-001` `DESIGN` | Select safe solution; valid baseline | Requirements, architecture/contracts, risks, supplier facts | Evaluate alternatives; define boundaries, state/effects, data/threat/ops, CM, V&V, release, migration/rollback/retirement | Design record, ADR if required, V&V/config/release strategies | Architect/technical / technical owner or ADR authority / product, V&V, service, security/data, supplier / delivery | Architecture/trace/threat/dependency checks + required human ADR/risk decision | Unacceptable → Definition/Design; infeasible → Triage | Inline note allowed only by lane; measure design churn/late decision changes | `STD`,`GOV`,`OWNER` |
| `SDLC-PLN-001` `READY` | Make responsible commitment; accepted design | Integrated scope, design, estimates, capacity, dependencies/risks | Slice vertically; estimate range; forecast; resource; plan evidence/configuration/acceptance; bind tailoring | Integrated delivery plan, task/decision inputs, DoR proof | Delivery/planner / delivery owner / product, technical, V&V, service / stakeholders | Completeness/dependency/capacity checks + human commitment | Infeasible → Design/Triage; blocking dependency → Blocked | No mandatory points; lead time, forecast calibration, readiness escapes | `STD`,`MODEL`,`OWNER` |
| `SDLC-BLD-001` `IN_PROGRESS` | Produce bounded candidate; Ready item and exact base | Task packet, baselines, workspace, grants | Implement with tests/docs/telemetry; integrate small; manage config/dependencies; record truthfully | Exact candidate, run result, handoff, updated trace/config status | Maker / technical owner / reviewer, V&V, config / delivery | Path/dependency/schema/CI checks + maker handoff (not approval) | Failure → In Progress/Blocked/Design/Definition | One conceptual change; WIP, cycle time, build/rework | `STD`,`OBS`,`PRAC`,`OWNER` |
| `SDLC-VER-001` `VERIFICATION` | Verify and validate exact subject; candidate exists | Candidate, requirements/design, V&V plan, qualified environment | Independent review; test portfolio; security/data/compatibility/recovery; anomaly disposition; representative validation | Review, checker, V&V, acceptance and anomaly records | V&V/reviewers / independent V&V authority + product validator / maker, technical, service, security / release | Exact-subject deterministic gates + independent human/product acceptance by lane | Fail → Build/Design/Definition; environment invalid → re-run | Independence may only increase; effectiveness, leakage, flake, latency | `GOV`,`PRAC`,`OWNER` |
| `SDLC-RDY-001` `RELEASE_READY` | Prove safe promotion; verified candidate | Immutable candidate, audits, manifest, migration/rollback/runbook/comms | Build once; configuration audits; sign/attest; rehearsal; predeclare health/halt/rollback | Release candidate, manifest/SBOM, compatibility and readiness decision | Config/release / release authority / V&V, service, security/data / users/operators | Reproducibility/provenance/audit gates + human permit | Failure → Verification/Design; stale subject → requalify | Standard lane can use automated standard path; readiness failures/time | `GOV`,`PRAC`,`OWNER` |
| `SDLC-REL-001` `RELEASING` | Safely expose approved artifact; valid permit/recovery point | Artifact, destination, permit, baseline and criteria | Snapshot; stage; migrate; activate progressively; observe; halt/rollback/reconcile | Deployment events, health evaluation, completion or rollback | Release operator / release authority / service, incident, data / stakeholders | Destination/digest/health gates + human expansion/rollback where required | Threshold breach → work item `ROLLED_BACK`; open incident/recovery work when impact exists | Smallest applicable exposure; frequency, failure, recovery | `PRAC`,`OBS`,`OWNER` |
| `SDLC-OPS-001` `OPERATING` | Establish supported healthy service; released subject | Release record, SLO/measurement/support/runbooks | Observe window; support; reconcile; scan; backup/restore; capacity/cost review | Operational acceptance, health/security/support evidence | Service/operations / service owner / product, security, supplier / users | Telemetry/reconciliation/backup checks + service-owner acceptance | Failure opens an incident and linked `INCIDENT_RESPONSE` work; uncertainty extends observation | SLO may be Unknown with plan; reliability/support measures | `GOV`,`PRAC`,`OWNER` |
| `SDLC-OUT-001` `OUTCOME_REVIEW` | Decide whether change helped; observation due | Hypothesis/baseline, product and ops evidence | Compare expected/actual, side effects and segments; decide keep/change/remove | Outcome decision and follow-up work | Product analytics / product owner / technical, service, users / portfolio | Data-quality check + human product decision | Falsified → `DISCOVERY` or linked `MAINTENANCE`/`RETIREMENT` work | Sampled only for standard lane; outcome/side-effect measures | `OBS`,`PRAC`,`OWNER` |
| `SDLC-MNT-001` maintenance control | Keep a supported capability fit; maintenance trigger creates a linked work item | Supported-version policy, defects, debt, vulnerability/dependency/ops signals | Run corrective/adaptive/perfective/preventive work through `FUNNEL`–`CLOSED`; regress; patch; update docs/config baseline; release/observe normally | Maintained baseline, linked work item, disposition and release evidence | Maintenance / maintenance+service owner / product, V&V, supplier, security / users | Normal definition/design/V&V/release gates | Unsupported/unviable → linked retirement work; impact → incident record and emergency work item | No bypass for “existing” behavior; backlog age, freshness, debt interest | `STD`,`GOV`,`OWNER` |
| `SDLC-RET-001` retirement control | End capability use/data/access safely; approved trigger creates a linked work item | Consumer/dependency inventory, retention/legal/privacy, replacement/export, recovery | Run retirement work through `FUNNEL`–`CLOSED`; notify; migrate/export; archive; revoke; delete/retain; teardown; observe; audit absence and retrieval | Capability-state transition, retirement permit/events, disposition proofs, independent audit, residual owner | Retirement operator / human governor / product, service, data/security, config / users | Inventory/data/access/archive automated checks + human approval and final audit | Failure leaves capability active/deprecated and opens recovery/incident work; incomplete teardown cannot become `RETIRED` | Retirement depth not tailorable for affected data/access; completion/exceptions | `GOV`,`OWNER` |
| `SDLC-CLS-001` `CLOSED` | Reconcile work and release obligations; terminal evidence exists | Outcome/retirement decision, follow-ups, baselines | Verify ownership, archive, temporary access/flags/worktrees, debt and decisions; close project plan | Closure/acceptance record and retrievable evidence | Work/delivery / work owner / product, technical, service, config / stakeholders | Orphan/expiry/archive checks + accountable closure | Missing follow-up/evidence → prior state/Blocked | Merge never qualifies; end-to-end time, closure debt | `STD`,`MODEL`,`OWNER` |
| `SDLC-BLK-001` `BLOCKED` | Preserve truth when safe progress is impossible; active item has a blocker | Current state/baseline, typed blocker, affected evidence and dependencies | Record reason, owner, entered time, impact, invalidation, escalation and next-decision date; age and review the blocker | Append-only blocked transition and decision/recovery evidence | Work/delivery / work owner / dependency and affected owners / stakeholders | Schema/age/escalation checks + accountable resume/disposition decision | Resume only to an allowed state with refreshed evidence; unresolved/unsafe remains blocked or receives authorized cancellation | No hidden parked work; blocker age/share, repeat causes, missed decision dates | `STD`,`OWNER` |
| `SDLC-CAN-001` `CANCELLED` | End pre-release work without fabricating completion; authorized stop decision exists | Current state, reason, impact, evidence, temporary effects and obligations | Record authority/reason; preserve evidence; clean access/flags/worktrees; assign residual follow-up and notify affected owners | Cancellation decision, cleanup proof, retained record and owned follow-ups | Work/product / product or work owner / technical, service, security/data / stakeholders | Pre-release/state/authority/cleanup checks + human cancellation decision | Missing authority/cleanup → Blocked or prior state; rediscovery creates a linked new work item | Never reported as done/released; cancellation timing/reasons, residual cleanup and repeat discarded work | `STD`,`OWNER` |
| `SDLC-RBK-001` `ROLLED_BACK` | Record a release reversal and prove the prior safe state; rollback initiated | Release/permit, exact artifact/destination, rollback plan, health/impact evidence | Execute authorized rollback; verify safe state; reconcile config/data/access; bound impact; open incident when applicable; create linked re-triage | Rollback events, safe-state proof, impact/reconciliation evidence, linked `TRIAGE` item and incident/action refs | Release/service / release + service owner / incident, product, security/data, configuration / stakeholders | Destination/digest/safe-state/reconciliation checks + release/service acceptance | Unverified recovery remains incident/rollback work; never return directly to normal release without new triage and qualification | Recovery distribution, rollback recurrence, reconciliation/action age | `GOV`,`PRAC`,`OWNER` |

Recommended activities may be added to a stage checklist, but cannot be confused
with the mandatory outputs and gates above.

## 5. Gate failure and recovery semantics

| Failure | Destination |
|---|---|
| Insufficient discovery | `FUNNEL`, `DISCOVERY`, or `CANCELLED` |
| Ambiguous/unverifiable requirement | `DISCOVERY` or `DEFINITION` |
| Unacceptable design | `DEFINITION` or `DESIGN` |
| Infeasible commitment | `DESIGN` or `TRIAGE` |
| Build failure | `IN_PROGRESS` or `BLOCKED` |
| V&V failure | `IN_PROGRESS`, `DESIGN`, or `DEFINITION` |
| Release-readiness failure | `VERIFICATION` or `DESIGN` |
| Rollout health breach | Work item `ROLLED_BACK`; create an `Incident` and emergency work item when impact exists |
| Operational-window failure | Create an `Incident` and linked emergency/defect work item; block or roll back the affected work as policy requires |
| Falsified outcome | Return the work item to `DISCOVERY` or create linked maintenance/retirement work |
| Retirement failure | Keep capability active/deprecated; open recovery or incident work |
| Process nonconformance | Corrective action; evidence stays failed/missing |

Every rejection records reason code, authority, affected baselines, invalidated
evidence and next owner. Risk may be accepted within policy; factual failure,
forged/missing evidence and stale exact-subject proof cannot be overridden.

## 6. Roles and incompatible combinations

Additional accountable roles are:

- requirements owner/business analyst;
- V&V/test authority;
- configuration manager/build-release custodian;
- supplier/dependency owner;
- maintenance owner;
- retirement/data-disposition owner; and
- process owner/independent assurance auditor.

One human may fill roles in a small team, but:

- maker and V&V acceptance cannot combine for enhanced/critical work;
- maker and release/risk authority cannot combine;
- a process auditor cannot audit their own execution; and
- critical duties require a qualified backup or a recorded availability risk.

## 7. Source crosswalk

| Control family | Primary basis |
|---|---|
| Project management, implementation and closure | [ISO/IEC 29110-5-1-2:2025](https://www.iso.org/standard/82669.html) |
| Assurance, traceability, V&V, configuration, delivery/maintenance records | [NASA-HDBK-2203](https://standards.nasa.gov/standard/NASA/NASA-HDBK-2203) |
| Secure organization, environments, software, releases and vulnerability response | [NIST SP 800-218](https://doi.org/10.6028/NIST.SP.800-218) |
| Small batches, WIP, CI/CD, tests, observability and measures | [DORA capabilities](https://dora.dev/capabilities/) and [metrics](https://dora.dev/guides/dora-metrics/) |
| Change size and code review | [Google Engineering Practices](https://google.github.io/eng-practices/review/) |
| SLOs, rollout, incidents and learning | [Google SRE Workbook](https://sre.google/workbook/table-of-contents/) |
| Institutionalization/maturity audit lens | [CMMI levels](https://cmmiinstitute.com/learning/appraisals/levels) |

## 8. Hermes-fork specialized controls

### SDLC-FORK-000 — Fork ancestry and provenance preflight

No runtime implementation commit is accepted into the product branch until a
deterministic exact-subject gate proves:

- immutable preservation of the current Ranex documentation/bootstrap history;
- the pinned upstream repository, commit, verified tree, license/notices, tags,
  and pristine source manifest;
- an authenticated human decision selecting replay or provenance-complete
  import as the ancestry-adoption strategy;
- the resulting merge-base/ancestry proof and final branch/worktree topology;
- a fetch-only upstream remote;
- distinct observed, audited, incorporated, and latest-seen baselines;
- restored upstream license and per-file provenance/classification coverage;
  and
- the actual GitHub network-fork observation as a separate hosting fact.

The hosting flag may remain `false`; it is never used as a substitute for
software derivation, Git ancestry, or license evidence. Failure or missing
evidence keeps the gate `FAIL`, `UNKNOWN`, or `CONFLICT` and the architecture
label “fork target / ancestry adoption pending.”

### SDLC-FORK-001 — Inherited behavior disposition

Every inherited public or authority-relevant behavior is keyed by exact
upstream commit plus path/symbol/observable behavior and assigned:

```text
RETAIN_AS_IS | WRAP | EXTRACT | REIMPLEMENT | REMOVE | QUARANTINE | DEFER
```

The record includes owner, rationale, legal/commercial class, compatibility
contract/test, expiry/removal trigger and replacement work ID. It is required
at Definition/Design, upstream classification, compatibility verification and
release-manifest generation.

### SDLC-FORK-002 — Upstream synchronization

```text
OBSERVED -> FETCHED -> PINNED -> CLASSIFIED -> DISPOSITIONED
  -> disposition REJECT -> REJECTED
  -> disposition DEFER -> DEFERRED
  -> disposition PORT -> PORTING -> PORT_CANDIDATE -> VERIFIED
  -> RELEASED -> BASELINE_RECORDED
```

`BLOCKED` and `ROLLED_BACK` are deterministic branches. Any nonterminal state
from `FETCHED` through `RELEASED` may enter `BLOCKED` only with the prior state,
reason, owner, required evidence, and review deadline; resolution returns only
to that prior state, while abandonment returns to `CLASSIFIED` for a new
`REJECT` or `DEFER` disposition. Only `RELEASED` may enter `ROLLED_BACK`;
reconciliation of product/schema/data/credential/package/external effects is
required before a new candidate revision re-enters `CLASSIFIED`. `REJECTED`,
`DEFERRED`, and `BASELINE_RECORDED` are terminal for one candidate revision.

Disposition is recorded per commit/path, not only per range. Baseline advances
only after a released port set and an explicit rejected/deferred ledger.
Emergency security work may use the emergency lane but cannot auto-merge.

### SDLC-FORK-003 — Release and update

Ranex never treats pulling a mutable branch and resetting source as product
rollback. Update states are:

```text
CHECKED -> DOWNLOADED -> VERIFIED -> SNAPSHOTTED -> STAGED
  -> MIGRATED -> ACTIVATED -> HEALTH_VERIFIED -> COMPLETED

Any post-snapshot state -> ROLLED_BACK -> RECOVERY_VERIFIED
```

The release binds artifact identity/digest and signature/attestation; policy,
workflow, schema, module and provider catalogs; disposition/compatibility
report; evidence digests; install target/platform matrix; configuration
migration; pre/post snapshot IDs; rollback compatibility limits; and
observation window. Refuse downgrade when schema/data/effects are not reversible
and require restore/reconciliation proof.

### SDLC-FORK-004 — Compatibility

Legacy surfaces use:

```text
SUPPORTED -> DEPRECATED -> READ_ONLY -> REMOVED
```

The registry covers `hermes` CLI, legacy home/config/session/tool identifiers,
plugins and providers, with version range, translation owner, parity tests,
privacy-safe usage evidence, notice, removal criteria and migration/rollback.
Compatibility cannot remain indefinite without a renewed human decision.

### SDLC-FORK-005 — Plugins, providers, MCP and routes

Subject state is not one generic lifecycle:

- external plugins/extensions use `ExtensionStatus`:
  `DISCOVERED -> QUARANTINED -> REVIEWED -> QUALIFIED -> PINNED -> ENABLED`,
  with `SUSPENDED | RETIRED`;
- first-party modules use `ModuleStatus`; and
- provider/model transports use `RouteStatus`.

`qualification` emits immutable trial/qualification evidence; only the owning
module, extension, or route context changes its subject state. Qualification
locks source and dependencies, manifest, protocol/schema, capability grants,
egress/secrets/data class, crash isolation and quarantine tests. Human
activation is required. Target mode forbids mutable Git update, unapproved
catalog install, optional manifest, user last-writer-wins override,
environment-presence route selection and import-time authority registration.

### SDLC-FORK-006 — Operational cutover and self-development

```text
BOOTSTRAP -> LEGACY_BASELINE -> TRANSITIONAL_DUAL_RUN
  -> TARGET_SHADOW -> TARGET_LIMITED -> TARGET_DEFAULT
  -> LEGACY_FROZEN -> LEGACY_REMOVED
```

Each mode binds authority owner, permitted effect paths, sole canonical writer,
rollback target and exit evidence. “Dual run” never means dual authority.

Self-development uses an immutable controller release `N` to govern candidate
`N+1`. The controller cannot modify or restart itself during the run. Candidate
release requires independent human permit, rollback drill, post-release
observation and outcome review.

### SDLC-FORK-007 — Required machine-readable reconciliation

Before the runtime tracer, provide:

- an archival phase-to-SDLC mapping for any retained pre-`ADR-0002`
  guide-derived execution records, explicitly forbidden as an itinerary for
  new work;
- exact-subject invalidation graph covering upstream/base/candidate commits,
  release manifest, test evidence, route catalog and operational mode;
- inherited-Hermes behavior disposition ledger; and
- compatibility matrix across upstream baseline, Ranex release, state schema,
  Python/Node/platform, plugin protocol and provider catalog.

The deleted legacy implementation-guide lifecycle is historical vocabulary,
not a live migration or construction input. Its mapping exists only so old
records remain intelligible. It cannot create new work, ordering, requirements,
states, gates, or acceptance criteria. `MERGED` is a landing event. It never
substitutes for `RELEASED`, `OPERATING`, `OUTCOME_REVIEW`, or `CLOSED`.

## 9. AI-worker fleet specialized controls

These controls implement the
[AI-Worker Fleet Control-Plane Specification](./AI_AGENT_FLEET_CONTROL_PLANE.md)
inside this SDLC. They govern worker execution and never create another product
lifecycle.

### SDLC-AIW-001 — Assignment, lease, and liveness

Every worker attempt is admitted from an exact current packet and receives a
typed assignment, atomic compare-and-swap claim, expiring lease, and
monotonically increasing fencing epoch. Heartbeats use coordinator time and
prove only recent contact. Expired, revoked, cancelled, or superseded attempts
are denied at every write, model, tool, mailbox, result, and effect boundary.
Reclaim creates a new linked attempt; late artifacts remain preserved but
ineligible.

### SDLC-AIW-002 — Deterministic execution governor

One release-pinned governor enforces the absolute deadline; parent/child
budgets; turn/model/tool/process/network/output ceilings; retry and consecutive
failure limits; result-aware loop detection; cancellation; sandbox
termination; and cleanup/reconciliation. A worker cannot change its governor
profile or label repeated activity as progress.

### SDLC-AIW-003 — Parallelism, workspace, and landing

One worker is the default. Parallel reads use isolated context. Parallel writes
require disjoint registered ownership and separate validated worktrees. Shared
files have one writer at a time. Integration/reconciliation is a new bounded
assignment and worker output remains a proposal. Landing is serialized and
human-controlled for every worker count; self-merge is prohibited.

### SDLC-AIW-004 — Transitive resource and permission enforcement

Every child assignment/model/tool call consumes a reservation whose usage is
attributed to all parents. The tool boundary validates current lease epoch,
exact subject, workspace, capability, policy, qualification, sandbox, and
budget. External effects still require the normal evidence → gate → human
decision where applicable → authority grant → permit → `CapabilityBus` order.

### SDLC-AIW-005 — Verification capacity and hidden evidence

Fleet admission cannot exceed qualified deterministic, independent,
holdout-based, product-validation, and human-decision capacity. Overload causes
backpressure, not weaker assurance. Hidden fixtures, answer keys, expected
secret outcomes, and independent observations remain outside maker-visible
packets and mounts. Model consensus cannot produce a gate outcome.

### SDLC-AIW-006 — Measurement and topology selection

The measurement harness is the first fleet-scaling experiment instrument after
the Core-SDLC contracts and authority/evidence/isolation foundations exist.
Experiments predeclare tasks, controls, budgets, repeated assignments,
uncertainty, verifier calibration, failure treatment, costs, outcomes, and stop
rules. External fleet-size, performance, price, or accuracy thresholds remain
`R_AND_D` hypotheses until reproduced on Ranex work.

### SDLC-AIW-007 — Learned control quarantine

Learned routing, topology, prompt/role optimization, or conductor policy is
inactive until offline train/validation/test/hidden evaluation, tamper
resistance, drift, rollback, non-self-activation, and human-accepted exact
policy evidence pass. Learnable parameters can never include authority, risk,
permissions, hidden-data access, verification depth, or policy activation.
