#!/usr/bin/env python3
"""Generate the Ranex Wave-1 executable documentation-contract baseline.

The generator is intentionally deterministic. It reads accepted architecture
documents and authoring templates, then writes only generated contract,
schema, fixture, and assessment paths owned by Wave 1.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import rfc8785
import yaml

from contract_tree_lock import contract_tree_lock


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "architecture" / "contracts"
SCHEMAS = ROOT / "schemas"
ASSESSMENTS = ROOT / "docs" / "architecture" / "assessments"
TEMPLATES = ROOT / "docs" / "architecture" / "templates"
ARCH_DOC = ROOT / "docs" / "architecture" / "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md"
ARTIFACT_DOC = ROOT / "docs" / "architecture" / "AI_ARTIFACT_CONTRACTS.md"
CONTROL_DOC = ROOT / "docs" / "architecture" / "SDLC_CONTROL_CATALOG.md"
REFERENCE_MAP = ROOT / "docs" / "architecture" / "ENGINEERING_REFERENCE_APPLICATION_MAP.md"
TOPOLOGY_ADR = ROOT / "docs" / "architecture" / "decisions" / "ADR-0007-establish-modular-ddd-repository-organization.md"
TDD_ADR = ROOT / "docs" / "architecture" / "decisions" / "ADR-0008-make-tdd-the-default-development-discipline.md"
BOUNDARY_FITNESS_ADR = (
    ROOT
    / "docs"
    / "architecture"
    / "decisions"
    / "ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
)
ARCHITECTURE_PRACTICE_PROFILE = (
    ROOT / "docs" / "research" / "ranex-architecture-practice-application-profile.json"
)
FIXED_TIME = "2026-07-28T00:00:00Z"


ARTIFACT_SCHEMAS: dict[str, tuple[str, str]] = {
    "AGENT_ASSIGNMENT.yaml": ("fleet/assignment-v1.schema.json", "agent_collaboration"),
    "AI_HANDOFF.yaml": ("execution/agent-handoff-v1.schema.json", "agent_collaboration"),
    "AI_TASK_PACKET.yaml": ("work/task-packet-v1.schema.json", "context_compilation"),
    "ANALYSIS_ATTEMPT.yaml": ("review/analysis-attempt-v1.schema.json", "analytical_review"),
    "ARCHITECTURE_PROPOSAL.yaml": ("architecture/proposal-v1.schema.json", "analytical_review"),
    "ARCHITECTURE_RECONCILIATION.yaml": ("architecture/reconciliation-v1.schema.json", "analytical_review"),
    "ARCHITECTURE_REVIEW_PACKET.yaml": ("architecture/review-packet-v1.schema.json", "context_compilation"),
    "AUTHORITY_GRANT.yaml": ("authority/authority-grant-v1.schema.json", "governed_execution"),
    "CAPABILITY_ASSESSMENT.yaml": ("process/capability-assessment-v1.schema.json", "process_assurance"),
    "CAPABILITY_DOMAIN_PROJECTION.yaml": ("process/capability-domain-projection-v1.schema.json", "process_assurance"),
    "CHECKER_RESULT.yaml": ("assurance/checker-result-v1.schema.json", "assurance"),
    "CORE_SDLC_TRACE.yaml": ("common/core-sdlc-trace-v1.schema.json", "configuration_management"),
    "DISPATCH_OFFER.yaml": ("fleet/dispatch-offer-v1.schema.json", "agent_collaboration"),
    "EVIDENCE_SNAPSHOT.yaml": ("assurance/evidence-snapshot-v1.schema.json", "assurance"),
    "FLEET_EXPERIMENT.yaml": ("fleet/fleet-experiment-v1.schema.json", "process_assurance"),
    "GATE_EVALUATION.yaml": ("assurance/gate-evaluation-v1.schema.json", "assurance"),
    "HUMAN_DECISION.yaml": ("authority/human-decision-v1.schema.json", "policy"),
    "INDEPENDENCE_EVALUATION.yaml": ("review/independence-evaluation-v1.schema.json", "analytical_review"),
    "LANDING_RECORD.yaml": ("execution/landing-record-v1.schema.json", "workspace"),
    "MAILBOX_ENVELOPE.yaml": ("fleet/mailbox-envelope-v1.schema.json", "agent_collaboration"),
    "OPERATION_EVIDENCE.yaml": ("lifecycle/operation-evidence-v1.schema.json", "operations"),
    "OUTCOME_REVIEW.yaml": ("lifecycle/outcome-review-v1.schema.json", "product_definition"),
    "PERMIT.yaml": ("authority/permit-v1.schema.json", "governed_execution"),
    "POST_LANDING_VERIFICATION.yaml": ("execution/post-landing-verification-v1.schema.json", "assurance"),
    "RELEASE_EVIDENCE.yaml": ("lifecycle/release-evidence-v1.schema.json", "release_management"),
    "RESEARCH_PACKET.yaml": ("research/research-packet-v1.schema.json", "product_definition"),
    "RESOURCE_RESERVATION.yaml": ("resources/resource-reservation-v1.schema.json", "resource_governance"),
    "REVIEW_OBSERVATION.yaml": ("review/review-observation-v1.schema.json", "analytical_review"),
    "REVIEW_RECORD.yaml": ("review/review-record-projection-v1.schema.json", "analytical_review"),
    "REVIEW_REQUEST.yaml": ("review/review-request-v1.schema.json", "analytical_review"),
    "REVIEW_VERDICT.yaml": ("review/review-verdict-v1.schema.json", "analytical_review"),
    "RUN_RESULT.yaml": ("execution/run-result-v1.schema.json", "agent_collaboration"),
    "TRANSITION_EVENT.yaml": ("work/transition-event-v1.schema.json", "owning_aggregate_uow"),
    "WORKER_ATTEMPT.yaml": ("fleet/worker-attempt-v1.schema.json", "agent_collaboration"),
    "WORKER_LEASE.yaml": ("fleet/lease-v1.schema.json", "agent_collaboration"),
    "WORK_INTAKE.yaml": ("work/work-intake-v1.schema.json", "work_management"),
}


IDENTITY_PREFIXES = {
    "repository": "repo_",
    "project": "prj_",
    "work_item": "work_",
    "run": "run_",
    "activity": "act_",
    "effect": "eff_",
    "workspace": "wsp_",
    "packet": "pkt_",
    "intake": "intake_",
    "research": "research_",
    "requirement": "req_",
    "criterion": "criterion_",
    "measure": "measure_",
    "core_sdlc_trace": "trace_",
    "evidence": "evd_",
    "snapshot": "snapshot_",
    "artifact": "art_",
    "checker_result": "check_",
    "architecture_review_packet": "archpkt_",
    "architecture_proposal": "proposal_",
    "architecture_reconciliation": "archreconcile_",
    "review_request": "review_",
    "analysis_attempt": "attempt_",
    "review_observation": "observation_",
    "review_verdict": "verdict_",
    "review_projection": "review_projection_",
    "independence_evaluation": "independence_",
    "finding": "finding_",
    "reconciliation": "reconcile_",
    "decision": "dec_",
    "authority_grant": "grant_",
    "permit": "permit_",
    "gate": "gate_",
    "handoff": "handoff_",
    "result": "result_",
    "landing": "landing_",
    "transition": "transition_",
    "release": "release_",
    "incident": "incident_",
    "service": "svc_",
    "capability": "cap_",
    "assignment": "assignment_",
    "offer": "offer_",
    "worker_attempt": "wattempt_",
    "lease": "lease_",
    "mailbox": "message_",
    "reservation": "reservation_",
    "fleet_experiment": "fleetexp_",
    "capability_assessment": "capability_assessment_",
    "capability_domain_projection": "capability_domain_projection_",
}


STATE_AXES: dict[str, dict[str, Any]] = {
    "WorkItemStatus": {
        "owner": "work_management",
        "values": ["FUNNEL", "TRIAGE", "DISCOVERY", "DEFINITION", "DESIGN", "READY", "IN_PROGRESS", "VERIFICATION", "RELEASE_READY", "RELEASING", "OPERATING", "OUTCOME_REVIEW", "CLOSED", "BLOCKED", "CANCELLED", "ROLLED_BACK"],
        "terminal": ["CLOSED", "CANCELLED"],
    },
    "RunStatus": {
        "owner": "governed_execution",
        "values": ["PROPOSED", "READY", "RUNNING", "WAITING", "BLOCKED", "SUCCEEDED", "FAILED", "CANCELLED"],
        "terminal": ["SUCCEEDED", "FAILED", "CANCELLED"],
    },
    "WorkClass": {"owner": "work_management", "values": ["PRODUCT", "DEFECT", "RELIABILITY", "SECURITY_PRIVACY", "ARCHITECTURE_PLATFORM", "COMPLIANCE_PROVENANCE", "UPSTREAM_SYNC", "MAINTENANCE", "RETIREMENT", "INCIDENT_RESPONSE"], "terminal": []},
    "RiskLane": {"owner": "policy", "values": ["STANDARD", "ENHANCED", "CRITICAL", "EMERGENCY"], "terminal": []},
    "AssignmentStatus": {"owner": "agent_collaboration", "values": ["PENDING", "OFFERED", "CLAIMED", "RUNNING", "HANDOFF_READY", "COMPLETED", "FAILED", "EXPIRED", "CANCELLED"], "terminal": ["COMPLETED", "FAILED", "EXPIRED", "CANCELLED"]},
    "DispatchOfferStatus": {"owner": "agent_collaboration", "values": ["OPEN", "CLAIMED", "EXPIRED", "REVOKED"], "terminal": ["CLAIMED", "EXPIRED", "REVOKED"]},
    "LeaseStatus": {"owner": "agent_collaboration", "values": ["ACTIVE", "RELEASED", "EXPIRED", "REVOKED"], "terminal": ["RELEASED", "EXPIRED", "REVOKED"]},
    "MailboxDeliveryStatus": {"owner": "agent_collaboration", "values": ["QUEUED", "DELIVERED", "ACKNOWLEDGED", "DEAD_LETTERED", "EXPIRED"], "terminal": ["ACKNOWLEDGED", "DEAD_LETTERED", "EXPIRED"]},
    "ReservationStatus": {"owner": "resource_governance", "values": ["PENDING", "ACTIVE", "EXHAUSTED", "RELEASED", "EXPIRED", "REVOKED", "SETTLED"], "terminal": ["SETTLED"]},
    "IntakeStatus": {"owner": "work_management", "values": ["PROPOSED", "ACCEPTED", "REJECTED", "DUPLICATE", "WITHDRAWN"], "terminal": ["ACCEPTED", "REJECTED", "DUPLICATE", "WITHDRAWN"]},
    "PacketStatus": {"owner": "packet_producer", "values": ["DRAFT", "SEALED", "SUPERSEDED", "INVALIDATED"], "terminal": ["SUPERSEDED", "INVALIDATED"]},
    "FleetExperimentStatus": {"owner": "process_assurance", "values": ["DRAFT", "REGISTERED", "RUNNING", "COMPLETED", "STOPPED", "INVALIDATED"], "terminal": ["COMPLETED", "STOPPED", "INVALIDATED"]},
    "CapabilityAssessmentStatus": {"owner": "process_assurance", "values": ["NOT_ASSESSED", "IN_PROGRESS", "COMPLETE", "SUPERSEDED"], "terminal": ["COMPLETE", "SUPERSEDED"]},
    "ActivityStatus": {"owner": "governed_execution", "values": ["REQUESTED", "DISPATCHED", "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_PERMANENT", "TIMED_OUT", "CANCELLED", "DENIED", "OUTCOME_UNKNOWN"], "terminal": ["SUCCEEDED", "FAILED_PERMANENT", "TIMED_OUT", "CANCELLED", "DENIED"]},
    "GateOutcome": {"owner": "assurance", "values": ["PASS", "FAIL", "UNKNOWN", "CONFLICT", "NOT_APPLICABLE", "CHECKER_FAULT"], "terminal": []},
    "ObservationState": {"owner": "analytical_review", "values": ["OPINION_PRODUCED", "NO_OPINION", "OPINION_UNUSABLE", "EVALUATION_INCOMPLETE"], "terminal": []},
    "PermitStatus": {"owner": "governed_execution", "values": ["ISSUED", "CONSUMED", "EXPIRED", "REVOKED"], "terminal": ["CONSUMED", "EXPIRED", "REVOKED"]},
    "HumanDecisionRecordStatus": {"owner": "policy", "values": ["PENDING", "APPROVED", "DENIED", "EXPIRED", "REVOKED"], "terminal": ["APPROVED", "DENIED", "EXPIRED", "REVOKED"]},
    "AuthorityGrantStatus": {"owner": "governed_execution", "values": ["ISSUED", "CONSUMED", "EXPIRED", "REVOKED"], "terminal": ["CONSUMED", "EXPIRED", "REVOKED"]},
    "EffectStatus": {"owner": "governed_execution", "values": ["INTENDED", "DISPATCHED", "SUCCEEDED", "FAILED_RETRYABLE", "FAILED_PERMANENT", "DENIED", "OUTCOME_UNKNOWN"], "terminal": ["SUCCEEDED", "FAILED_PERMANENT", "DENIED"]},
    "ReconciliationStatus": {"owner": "governed_execution", "values": ["NOT_REQUIRED", "PENDING", "RUNNING", "RESOLVED", "UNRESOLVED"], "terminal": ["NOT_REQUIRED", "RESOLVED", "UNRESOLVED"]},
    "IncidentStatus": {"owner": "operations", "values": ["DETECTED", "ACKNOWLEDGED", "MITIGATING", "MITIGATED", "RECOVERY_VERIFIED", "REVIEWED", "ACTIONS_TRACKED", "CLOSED"], "terminal": ["CLOSED"]},
    "ReleaseStatus": {"owner": "release_management", "values": ["PLANNED", "BUILT", "VERIFIED", "RELEASE_READY", "RELEASING", "OPERATING", "ROLLED_BACK", "WITHDRAWN"], "terminal": ["OPERATING", "ROLLED_BACK", "WITHDRAWN"]},
    "CapabilityStatus": {"owner": "product_definition", "values": ["PROPOSED", "SUPPORTED", "DEPRECATED", "RETIRE_READY", "RETIRING", "RETIRED"], "terminal": ["RETIRED"]},
    "ModuleStatus": {"owner": "module_governance", "values": ["PACKAGED", "DISABLED", "QUALIFIED", "CANARY", "ACTIVE", "RESTRICTED", "QUARANTINED", "RETIRED"], "terminal": ["RETIRED"]},
    "RouteStatus": {"owner": "routing", "values": ["UNCONFIGURED", "AUTHENTICATED", "SMOKE_TESTED", "PROBATION", "APPROVED", "RESTRICTED", "SUSPENDED", "RETIRED"], "terminal": ["RETIRED"]},
    "ExtensionStatus": {"owner": "extension_host", "values": ["DISCOVERED", "QUARANTINED", "REVIEWED", "QUALIFIED", "PINNED", "ENABLED", "SUSPENDED", "RETIRED"], "terminal": ["RETIRED"]},
    "CompatibilityStatus": {"owner": "service_management", "values": ["SUPPORTED", "DEPRECATED", "READ_ONLY", "REMOVED"], "terminal": ["REMOVED"]},
    "InstructionStatus": {"owner": "instruction_registry", "values": ["DRAFT", "ACTIVE", "DEPRECATED", "RETIRED"], "terminal": ["RETIRED"]},
    "ArtifactStatus": {"owner": "artifact_management", "values": ["INGESTED", "QUARANTINED", "AVAILABLE", "EXPIRED", "LEGAL_HOLD", "PURGED"], "terminal": ["PURGED"]},
    "MigrationStatus": {"owner": "migration", "values": ["PLANNED", "TESTED", "APPLIED", "VERIFIED", "ROLLED_BACK", "FAILED"], "terminal": ["VERIFIED", "ROLLED_BACK", "FAILED"]},
    "SyncCandidateStatus": {"owner": "upstream_sync", "values": ["OBSERVED", "FETCHED", "PINNED", "CLASSIFIED", "DISPOSITIONED", "PORTING", "PORT_CANDIDATE", "VERIFIED", "RELEASED", "BASELINE_RECORDED", "REJECTED", "DEFERRED", "BLOCKED", "ROLLED_BACK"], "terminal": ["BASELINE_RECORDED", "REJECTED", "DEFERRED"]},
    "UpdateStatus": {"owner": "release_management", "values": ["CHECKED", "DOWNLOADED", "VERIFIED", "SNAPSHOTTED", "STAGED", "MIGRATED", "ACTIVATED", "HEALTH_VERIFIED", "COMPLETED", "ROLLED_BACK", "RECOVERY_VERIFIED"], "terminal": ["COMPLETED", "RECOVERY_VERIFIED"]},
    "CutoverStatus": {"owner": "migration", "values": ["BOOTSTRAP", "LEGACY_BASELINE", "TRANSITIONAL_DUAL_RUN", "TARGET_SHADOW", "TARGET_LIMITED", "TARGET_DEFAULT", "LEGACY_FROZEN", "LEGACY_REMOVED"], "terminal": ["LEGACY_REMOVED"]},
}


PRIORITY_TRIGGERS = {
    "P0_CONTROL_NOW": ["ACTIVE_HARM", "NONTAILORABLE_INVARIANT_BREACH", "NONTAILORABLE_TRUTH_BREACH", "NONTAILORABLE_AUTHORITY_BREACH", "NONTAILORABLE_EVIDENCE_BREACH", "NONTAILORABLE_RECOVERY_BREACH"],
    "P1_IMPROVE_NEXT": ["RESULT_NOT_ASSESSED", "RESULT_UNKNOWN", "LEVEL_0", "LEVEL_1", "OVERDUE_CRITICAL_OBLIGATION", "REPEATED_ESCAPE", "HIGH_EXPOSURE_DOWNSTREAM_BLOCKAGE", "LOW_CONFIDENCE_INSTRUMENTATION"],
    "P2_IMPROVE_DELIBERATELY": ["LEVEL_2", "EFFECTIVENESS_UNKNOWN", "EFFECTIVENESS_REGRESSING", "EFFECTIVENESS_MIXED", "MATERIAL_FLOW_QUALITY_OUTCOME_HARM", "P3_CRITERIA_UNPROVEN"],
    "P3_SUSTAIN": ["P3_ALL_CRITERIA_PROVEN"],
}

MODULAR_DDD_LAYERS = ["api", "domain", "application", "application/ports", "adapters"]

TEST_TAXONOMY = [
    {
        "category_id": "UNIT",
        "root": "tests/unit",
        "purpose": "Pure context domain and application behavior through owned ports.",
    },
    {
        "category_id": "CONTRACT",
        "root": "tests/contract",
        "purpose": "Public API, schema, port, fake/real-adapter parity, and compatibility.",
    },
    {
        "category_id": "INTEGRATION",
        "root": "tests/integration",
        "purpose": "Real adapter, SQLite, process, provider sandbox, and cross-boundary integration.",
    },
    {
        "category_id": "ARCHITECTURE",
        "root": "tests/architecture",
        "purpose": "Path, ownership, import, cycle, composition, discovery, and generated-drift fitness.",
    },
    {
        "category_id": "ACCEPTANCE",
        "root": "tests/acceptance",
        "purpose": "Executable owned acceptance and rejection examples.",
    },
    {
        "category_id": "SYSTEM",
        "root": "tests/system",
        "purpose": "Complete local product and release-profile behavior across contexts.",
    },
    {
        "category_id": "E2E",
        "root": "tests/e2e",
        "purpose": "Production-shaped entry-to-effect/outcome tracing across delivery edges.",
    },
    {
        "category_id": "SECURITY",
        "root": "tests/security",
        "purpose": "Authentication, authorization, policy, gate, secret, sandbox, provenance, and abuse denial.",
    },
    {
        "category_id": "PERFORMANCE",
        "root": "tests/performance",
        "purpose": "Versioned workload, load, latency, and capacity distributions.",
    },
    {
        "category_id": "RESILIENCE",
        "root": "tests/resilience",
        "purpose": "Crash, timeout, cancellation, race, fault injection, recovery, and reconciliation.",
    },
    {
        "category_id": "MIGRATION",
        "root": "tests/migration",
        "purpose": "Forward, backward, upcast, rollback, version, and dirty-data behavior.",
    },
    {
        "category_id": "REPLAY",
        "root": "tests/replay",
        "purpose": "Reducer, event, snapshot, digest repeatability, and erasure semantics.",
    },
    {
        "category_id": "OPERATIONS",
        "root": "tests/operations",
        "purpose": "Backup, restore, install, update, rollback, runbook, and observability checks.",
    },
    {
        "category_id": "QUALIFICATION",
        "root": "tests/qualification",
        "purpose": "Checker, module, route, and isolation qualification fixtures.",
    },
    {
        "category_id": "EFFECTIVENESS",
        "root": "tests/effectiveness",
        "purpose": "Whole-workflow comparative outcome and guardrail experiments.",
    },
    {
        "category_id": "EVALUATION",
        "root": "tests/evaluation",
        "purpose": "Frozen and hidden evaluation harnesses separated from makers.",
    },
    {
        "category_id": "FIXTURES",
        "root": "tests/fixtures",
        "purpose": "Immutable owner-scoped external, golden, and fault corpora with provenance and classification.",
    },
    {
        "category_id": "BUILDERS",
        "root": "tests/builders",
        "purpose": "Owned deterministic object and packet builders without alternate business rules.",
    },
]

TEST_LANE_SHAPES = [
    {
        "category_id": "UNIT",
        "semantic_owner_parameter": "CONTEXT",
        "path_patterns": [
            "tests/unit/<context>/domain/**",
            "tests/unit/<context>/application/**",
        ],
        "mirrored_source_layers": ["domain", "application"],
        "shape_rule": "Mirror owned domain and application behavior; reach dependencies only through owned ports.",
    },
    {
        "category_id": "CONTRACT",
        "semantic_owner_parameter": "CONTEXT",
        "path_patterns": ["tests/contract/<context>/**"],
        "mirrored_source_layers": ["api", "application/ports", "adapters"],
        "shape_rule": "Bind public API, port, schema, fake, real-adapter, and compatibility contracts to one context.",
    },
    {
        "category_id": "INTEGRATION",
        "semantic_owner_parameter": "CONTEXT",
        "path_patterns": ["tests/integration/<context>/**"],
        "mirrored_source_layers": ["application/ports", "adapters"],
        "shape_rule": "Exercise real owned adapters and ports with production-shaped local dependencies.",
    },
    {
        "category_id": "ARCHITECTURE",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/architecture/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind each fitness check to exact registry, rule, path, import, or generated-projection metadata.",
    },
    {
        "category_id": "ACCEPTANCE",
        "semantic_owner_parameter": "CAPABILITY",
        "path_patterns": ["tests/acceptance/<capability>/**"],
        "mirrored_source_layers": ["api", "application"],
        "shape_rule": "Organize executable acceptance and rejection examples by owned capability.",
    },
    {
        "category_id": "SYSTEM",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/system/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind a complete local product profile and its participating contexts explicitly.",
    },
    {
        "category_id": "E2E",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/e2e/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind entry-to-effect/outcome journeys to exact capabilities and delivery edges.",
    },
    {
        "category_id": "SECURITY",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/security/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind each denial, abuse, secret, provenance, and sandbox case to its context and risk.",
    },
    {
        "category_id": "PERFORMANCE",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/performance/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind versioned workloads and distributions to a capability, resource, and quality objective.",
    },
    {
        "category_id": "RESILIENCE",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/resilience/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind faults, crashes, cancellation, recovery, and reconciliation to exact state/effect owners.",
    },
    {
        "category_id": "MIGRATION",
        "semantic_owner_parameter": "CONTEXT",
        "path_patterns": ["tests/migration/<context>/**"],
        "mirrored_source_layers": ["adapters"],
        "shape_rule": "Organize context-local persistence migrations by owner; cross-context ordering is explicit metadata.",
    },
    {
        "category_id": "REPLAY",
        "semantic_owner_parameter": "CONTEXT",
        "path_patterns": ["tests/replay/<context>/**"],
        "mirrored_source_layers": ["domain", "application", "adapters"],
        "shape_rule": "Bind event/state/upcaster/digest replay fixtures to the owning context.",
    },
    {
        "category_id": "OPERATIONS",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/operations/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind install, backup, restore, upgrade, rollback, and recovery procedures to an operational owner.",
    },
    {
        "category_id": "QUALIFICATION",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/qualification/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind tool, checker, provider, route, model, and extension qualification to an exact subject.",
    },
    {
        "category_id": "EFFECTIVENESS",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/effectiveness/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind outcome and guardrail evaluation to a capability and qualified measure.",
    },
    {
        "category_id": "EVALUATION",
        "semantic_owner_parameter": "EXACT_TEST_METADATA",
        "path_patterns": ["tests/evaluation/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Bind benchmark, rubric, judge, and regression evaluation to exact model and dataset versions.",
    },
    {
        "category_id": "FIXTURES",
        "semantic_owner_parameter": "OWNER",
        "path_patterns": ["tests/fixtures/<owner>/**"],
        "mirrored_source_layers": [],
        "shape_rule": "Store shared fixtures under one declared semantic owner and classification.",
    },
    {
        "category_id": "BUILDERS",
        "semantic_owner_parameter": "CONTEXT",
        "path_patterns": ["tests/builders/<context>/**"],
        "mirrored_source_layers": ["domain", "application"],
        "shape_rule": "Keep test-data builders with the context whose invariants and data they construct.",
    },
]

FAILURE_MODE_CLASSES = [
    "COMMANDS_AND_STATE_TRANSITIONS",
    "VALIDATION_AND_AUTH_POLICY_DENIAL",
    "PROOF_INTEGRITY_AND_AVAILABILITY",
    "VALUE_TIME_RESOURCE_BOUNDARIES",
    "DUPLICATE_REORDER_REPLAY_RETRY_IDEMPOTENCY",
    "CRASH_TIMEOUT_CANCEL_ACK_LOSS",
    "CONCURRENCY_LEASE_FENCING",
    "STORAGE_CORRUPTION_MIGRATION_REPLAY_VERSION",
    "PROVIDER_NETWORK_TOOL_PARTIAL_EFFECT_RECONCILIATION",
    "BACKUP_RESTORE_EXTERNAL_EFFECT_RECONCILIATION",
    "PRIVACY_RETENTION_REDACTION_DATA_DISPOSAL",
    "SUPPLIER_PACKAGE_SCHEMA_ROUTE_PROVENANCE_MISMATCH",
    "RECOVERY_BACKWARD_ROLLBACK_BLOCK_RESUME_CANCEL_TERMINAL",
]

EXPECTED_FAILURE_ASSERTIONS = [
    "EXPECTED_ERROR",
    "EXPECTED_EVENT",
    "EXPECTED_STATE",
    "NO_EFFECT",
    "RECOVERY",
]

EDGE_CASE_PARTITIONS = [
    {
        "partition_id": "FINITE_STATE_TRANSITIONS",
        "space_kind": "FINITE",
        "required_methods": ["EXHAUSTIVE_TRANSITION_TABLE"],
    },
    {
        "partition_id": "FINITE_BOUNDARY_CLASSES",
        "space_kind": "FINITE",
        "required_methods": ["BOUNDARY_PARTITION"],
    },
    {
        "partition_id": "OPEN_INPUT_AND_SEQUENCE_SPACE",
        "space_kind": "OPEN",
        "required_methods": ["PROPERTY", "MODEL", "FUZZ"],
    },
    {
        "partition_id": "OPEN_IMPLEMENTATION_FAULT_SPACE",
        "space_kind": "OPEN",
        "required_methods": ["MUTATION", "FAULT_INJECTION"],
    },
]

PRODUCTION_EVIDENCE_OBLIGATIONS = [
    {
        "obligation_id": "BUILT_ARTIFACT_AND_COMPOSITION_IDENTITY",
        "required_evidence_fields": [
            "built_artifact_refs",
            "composition_identity_refs",
        ],
        "task_selection_rule": "ALWAYS_WHEN_TASK_RESULT_IS_PASS",
    },
    {
        "obligation_id": "MOCK_TARGET_CLASSIFICATION",
        "required_evidence_fields": ["mock_target_classification_refs"],
        "task_selection_rule": "APPLICABLE_WHEN_ANY_TEST_DOUBLE_IS_USED",
    },
    {
        "obligation_id": "FAKE_REAL_ADAPTER_PARITY",
        "required_evidence_fields": ["adapter_fake_contract_refs"],
        "task_selection_rule": "APPLICABLE_WHEN_AN_EXTERNAL_PORT_OR_FAKE_IS_USED",
    },
    {
        "obligation_id": "REAL_SQLITE_AND_MIGRATION",
        "required_evidence_fields": ["persistence_migration_refs"],
        "task_selection_rule": "APPLICABLE_WHEN_PERSISTENCE_OR_SCHEMA_CHANGES",
    },
    {
        "obligation_id": "REPLAY_DIGEST_STABILITY",
        "required_evidence_fields": ["replay_digest_refs"],
        "task_selection_rule": "APPLICABLE_WHEN_EVENTS_STATE_UPCASTERS_OR_REPLAY_CHANGE",
    },
    {
        "obligation_id": "NEGATIVE_MUTATION_AND_FAULT_EVIDENCE",
        "required_evidence_fields": [
            "negative_test_refs",
            "mutation_evidence_refs",
            "fault_injection_evidence_refs",
        ],
        "task_selection_rule": "RISK_AND_EXACT_SUBJECT_SELECTED",
    },
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    return rfc8785.dumps(value)


def digest_value(value: dict[str, Any]) -> str:
    unsigned = {key: val for key, val in value.items() if key != "digest"}
    return "sha256:" + sha256_bytes(canonical_bytes(unsigned))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def slug(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "-", value.upper()).strip("-")


def snake(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def deterministic_uuid7(name: str) -> str:
    raw = bytearray(hashlib.sha256(name.encode("utf-8")).digest()[:16])
    timestamp_ms = 1785196800000  # 2026-07-28T00:00:00Z
    raw[:6] = timestamp_ms.to_bytes(6, "big")
    raw[6] = (raw[6] & 0x0F) | 0x70
    raw[8] = (raw[8] & 0x3F) | 0x80
    h = raw.hex()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def section(text: str, start: str, end: str | None) -> str:
    start_at = text.index(start)
    end_at = text.index(end, start_at) if end else len(text)
    return text[start_at:end_at]


def markdown_table(block: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip().replace("`", "") for cell in line.strip("|").split("|")]
        if not cells or all(re.fullmatch(r":?-+:?", cell or "-") for cell in cells):
            continue
        rows.append(cells)
    return rows[1:] if rows else []


def parse_inline_rule_set(path: Path, prefix: str) -> list[dict[str, str]]:
    rules = [
        {
            "rule_id": rule_id,
            "enforcement": enforcement,
            "invariant": invariant,
            "definition_status": "DEFINED",
            "runtime_evidence_status": "NOT_ASSESSED",
            "source": str(path.relative_to(ROOT)),
        }
        for rule_id, enforcement, invariant in re.findall(
            rf'\{{id: "({re.escape(prefix)}-[A-Z0-9-]+)", enforcement: "([A-Z_]+)", invariant: "([^"]+)"\}}',
            read(path),
        )
    ]
    return rules


def decision_binding(path: Path, decision_id: str) -> dict[str, str]:
    return {
        "decision_id": decision_id,
        "path": str(path.relative_to(ROOT)),
        "digest": "sha256:" + sha256_file(path),
        "status": "ACCEPTED_PAPER_DECISION",
        "runtime_enactment_status": "NOT_ASSESSED",
    }


def parse_topology_decision() -> dict[str, Any]:
    text = read(TOPOLOGY_ADR)
    exception_rows = markdown_table(
        section(
            text,
            "Allowed exception classes are only:",
            "An exception records",
        )
    )
    return {
        "rule_set_id": re.search(r'topology_rule_set: "([^"]+)"', text).group(1),
        "rules": parse_inline_rule_set(TOPOLOGY_ADR, "ORG"),
        "exception_classes": [
            {"exception_class": row[0], "scope": row[1]}
            for row in exception_rows
        ],
        "fitness_refs": sorted(set(re.findall(r"`(FF-ORG-\d{3})`", text))),
        "decision_binding": decision_binding(TOPOLOGY_ADR, "ADR-0007"),
    }


def parse_tdd_decision() -> dict[str, Any]:
    text = read(TDD_ADR)
    rule_block = section(text, "tdd_rule_set:", "rules:")
    roots = re.findall(r"^  - ([a-z0-9_]+)$", rule_block, flags=re.MULTILINE)
    exception_rows = markdown_table(
        section(
            text,
            "Allowed TDD exception classes:",
            "Every exception records",
        )
    )
    return {
        "rule_set_id": re.search(r'tdd_rule_set: "([^"]+)"', text).group(1),
        "allowed_root_names": roots,
        "rules": parse_inline_rule_set(TDD_ADR, "TDD"),
        "exception_classes": [
            {"exception_class": row[0], "required_substitution": row[1]}
            for row in exception_rows
        ],
        "fitness_refs": sorted(set(re.findall(r"`(FF-TDD-\d{3})`", text))),
        "decision_binding": decision_binding(TDD_ADR, "ADR-0008"),
    }


def parse_boundary_fitness_decision() -> dict[str, Any]:
    text = read(BOUNDARY_FITNESS_ADR)
    yaml_blocks = [
        yaml.safe_load(block)
        for block in re.findall(r"```yaml\n(.*?)\n```", text, flags=re.DOTALL)
    ]
    if len(yaml_blocks) != 5:
        raise ValueError(
            f"ADR-0009 YAML block drift: expected=5 actual={len(yaml_blocks)}"
        )
    dependency_graph, boundary_fitness, coupling_policy, feedback_policy, rule_set = (
        yaml_blocks
    )
    rules = [
        {
            "rule_id": row["id"],
            "enforcement": row["enforcement"],
            "invariant": row["invariant"],
            "definition_status": "DEFINED",
            "runtime_evidence_status": "NOT_ASSESSED",
            "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
        }
        for row in rule_set["rules"]
    ]
    fitness_rows = markdown_table(
        section(
            text,
            "| Fitness ID | Required evidence |",
            "Every result is currently",
        )
    )
    fitness_obligations = [
        {
            "fitness_id": row[0],
            "required_evidence": row[1],
            "result": "NOT_ASSESSED",
            "evidence_refs": [],
            "noncompensating": True,
            "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
        }
        for row in fitness_rows
    ]
    return {
        "dependency_graph": dependency_graph,
        "boundary_fitness": boundary_fitness,
        "coupling_policy": coupling_policy,
        "feedback_policy": feedback_policy,
        "rule_set_id": rule_set["boundary_fitness_rule_set"],
        "rules": rules,
        "fitness_obligations": fitness_obligations,
        "decision_binding": decision_binding(BOUNDARY_FITNESS_ADR, "ADR-0009"),
    }


def referenced_practice_ids(path: Path, source_registry: dict[str, Any]) -> list[str]:
    stable_ids = {entry["practice_id"] for entry in source_registry["practices"]}
    cited = set(re.findall(r"ENGREF-[A-Z0-9][A-Z0-9-]+", read(path)))
    return sorted(stable_ids & cited)


def dependency_pairs_have_cycle(pairs: set[tuple[str, str]]) -> bool:
    graph: dict[str, set[str]] = {}
    for caller, callee in pairs:
        graph.setdefault(caller, set()).add(callee)
    active: set[str] = set()
    complete: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in complete:
            return False
        active.add(node)
        if any(visit(target) for target in graph.get(node, set())):
            return True
        active.remove(node)
        complete.add(node)
        return False

    return any(visit(node) for node in sorted(graph))


def parse_architecture() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    text = read(ARCH_DOC)
    contexts: list[dict[str, Any]] = []
    for heading, end, table_kind in [
        ("### 9.1", "### 9.2", "AUTHORITY"),
        ("### 9.2", "### 9.3", "PRODUCT_DEVELOPMENT"),
        ("### 9.3", "## 10.", "OPERATIONS_BOUNDARY"),
    ]:
        for row in markdown_table(section(text, heading, end)):
            name = row[0]
            contexts.append(
                {
                    "context_id": name.split()[0],
                    "kind": table_kind,
                    "owns": row[1],
                    "public_boundary": row[2],
                    "persistence_authority": row[3] if len(row) > 3 else "CONTEXT_OWNED_TABLES_ONLY",
                    "definition_status": "DEFINED",
                    "runtime_validation_status": "NOT_ASSESSED",
                    "source": f"docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#{heading.split()[1]}",
                }
            )

    zones: list[dict[str, Any]] = []
    for row in markdown_table(section(text, "## 10.", "## 11.")):
        owner_contexts = [
            context["context_id"]
            for context in contexts
            if re.search(rf"\b{re.escape(context['context_id'])}\b", row[1])
        ]
        zones.append(
            {
                "zone_id": f"ZONE-{slug(row[0])}",
                "name": row[0],
                "owners": owner_contexts,
                "effect_adapter_family": row[2],
                "lifecycle_owner": row[3],
                "canonical_output": row[4],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#10",
            }
        )

    decisions: list[dict[str, Any]] = []
    for row in markdown_table(section(text, "## 3. Fixed decisions", "## 4.")):
        decisions.append(
            {
                "decision_id": f"ARCHDEC-{slug(row[0])}",
                "name": row[0],
                "canonical_position": row[1],
                "status": "ACCEPTED_TARGET",
                "authority": "HUMAN_GOVERNOR",
                "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#3",
            }
        )
    for adr in sorted((ROOT / "docs" / "architecture" / "decisions").glob("ADR-*.md")):
        decisions.append(
            {
                "decision_id": adr.stem.split("-")[0] + "-" + adr.stem.split("-")[1],
                "name": read(adr).splitlines()[0].lstrip("# "),
                "canonical_position": "See immutable ADR.",
                "status": "ACCEPTED",
                "authority": "HUMAN_GOVERNOR",
                "source": str(adr.relative_to(ROOT)),
                "source_digest": "sha256:" + sha256_file(adr),
            }
        )

    files: list[dict[str, Any]] = []
    for row in markdown_table(section(text, "### 12.1", "### 12.2")):
        context = row[0].split()[0]
        for cell_kind, cell in (("DOMAIN_API", row[1]), ("APPLICATION_PORT", row[2])):
            for pattern in re.findall(r"`([^`]+)`", cell):
                files.append(
                    {
                        "path_id": f"PATH-{slug(context)}-{cell_kind}-{len(files)+1:03d}",
                        "owner_context": context,
                        "path_pattern": f"src/ranex/{context}/{pattern}",
                        "responsibility_class": cell_kind,
                        "definition_status": "DEFINED",
                        "runtime_validation_status": "NOT_ASSESSED",
                        "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#12.1",
                    }
                )
    return contexts, zones, decisions, files


def parse_vital_profile() -> tuple[list[dict[str, str]], dict[str, str]]:
    rows = re.findall(
        r"^\| `(CAP-[^`\n]+)` \| ([^|\n]+) \| `(SDLC-[^`\n]+)` \| `(APP-[^`\n]+)` \|$",
        read(CONTROL_DOC),
        flags=re.MULTILINE,
    )
    tuples = [
        {"domain_id": domain, "domain_name": name.strip(), "control_id": control, "applicability_rule_id": rule}
        for domain, name, control, rule in rows
    ]
    rules: dict[str, str] = {}
    for rule, meaning in re.findall(r"^\| `(APP-[^`\n]+)` \| ([^|\n]+) \|$", read(CONTROL_DOC), flags=re.MULTILINE):
        rules[rule] = meaning.strip()
    return tuples, rules


def work_item_transitions() -> list[dict[str, str]]:
    main = ["FUNNEL", "TRIAGE", "DISCOVERY", "DEFINITION", "DESIGN", "READY", "IN_PROGRESS", "VERIFICATION", "RELEASE_READY", "RELEASING", "OPERATING", "OUTCOME_REVIEW", "CLOSED"]
    transitions = [{"from": a, "to": b, "guard_id": "NORMAL_EVIDENCE_AND_AUTHORITY"} for a, b in zip(main, main[1:])]
    transitions.extend(
        {"from": "VERIFICATION", "to": target, "guard_id": "VERIFICATION_REJECTION"}
        for target in ["DEFINITION", "DESIGN", "IN_PROGRESS"]
    )
    transitions.extend(
        [
            {"from": "RELEASING", "to": "ROLLED_BACK", "guard_id": "ROLLOUT_HEALTH_BREACH"},
            {"from": "ROLLED_BACK", "to": "TRIAGE", "guard_id": "SAFE_STATE_VERIFIED_AND_RETRIAGE_LINKED"},
            {"from": "OUTCOME_REVIEW", "to": "DISCOVERY", "guard_id": "OUTCOME_FALSIFIED"},
            {"from": "OUTCOME_REVIEW", "to": "DEFINITION", "guard_id": "OUTCOME_REQUIRES_REDEFINITION"},
        ]
    )
    active = [v for v in STATE_AXES["WorkItemStatus"]["values"] if v not in {"CLOSED", "CANCELLED", "BLOCKED", "ROLLED_BACK"}]
    transitions.extend({"from": value, "to": "BLOCKED", "guard_id": "TYPED_BLOCKER_RECORDED"} for value in active)
    transitions.extend(
        {"from": "BLOCKED", "to": value, "guard_id": "RESUME_TO_RECORDED_PRIOR_STATE_WITH_REFRESHED_EVIDENCE"}
        for value in active
    )
    pre_release = ["FUNNEL", "TRIAGE", "DISCOVERY", "DEFINITION", "DESIGN", "READY", "IN_PROGRESS", "VERIFICATION", "RELEASE_READY", "BLOCKED"]
    transitions.extend({"from": value, "to": "CANCELLED", "guard_id": "AUTHORIZED_PRE_RELEASE_CANCELLATION"} for value in pre_release)
    return transitions


def run_transitions() -> list[dict[str, str]]:
    pairs = [
        ("PROPOSED", "READY", "PACKET_AND_POLICY_VALID"),
        ("READY", "RUNNING", "AUTHORIZED_START"),
        ("READY", "BLOCKED", "BLOCKER_RECORDED"),
        ("READY", "CANCELLED", "AUTHORIZED_CANCELLATION"),
        ("RUNNING", "WAITING", "DURABLE_WAIT_ENTERED"),
        ("RUNNING", "BLOCKED", "BLOCKER_RECORDED"),
        ("RUNNING", "SUCCEEDED", "TERMINAL_SUCCESS_EVIDENCE"),
        ("RUNNING", "FAILED", "TERMINAL_FAILURE_EVIDENCE"),
        ("RUNNING", "CANCELLED", "AUTHORIZED_CANCELLATION"),
        ("WAITING", "RUNNING", "SIGNAL_OR_TIMER_RESOLVED"),
        ("WAITING", "BLOCKED", "BLOCKER_RECORDED"),
        ("WAITING", "FAILED", "WAIT_FAILED"),
        ("WAITING", "CANCELLED", "AUTHORIZED_CANCELLATION"),
        ("BLOCKED", "RUNNING", "BLOCKER_RESOLVED"),
        ("BLOCKED", "FAILED", "TERMINAL_FAILURE_EVIDENCE"),
        ("BLOCKED", "CANCELLED", "AUTHORIZED_CANCELLATION"),
    ]
    return [{"from": a, "to": b, "guard_id": guard} for a, b, guard in pairs]


def sequential_transitions(values: list[str]) -> list[dict[str, str]]:
    return [{"from": a, "to": b, "guard_id": "OWNER_POLICY_AND_EVIDENCE"} for a, b in zip(values, values[1:])]


def build_state_registry() -> dict[str, Any]:
    axes = []
    for name, spec in STATE_AXES.items():
        transitions: list[dict[str, str]]
        if name == "WorkItemStatus":
            transitions = work_item_transitions()
        elif name == "RunStatus":
            transitions = run_transitions()
        elif name == "ReconciliationStatus":
            transitions = [
                {"from": "PENDING", "to": "RUNNING", "guard_id": "RECONCILIATION_STARTED"},
                {"from": "RUNNING", "to": "RESOLVED", "guard_id": "OUTCOME_PROVEN"},
                {"from": "RUNNING", "to": "UNRESOLVED", "guard_id": "OUTCOME_NOT_PROVEN"},
            ]
        elif name in {"CompatibilityStatus", "ExtensionStatus", "UpdateStatus", "CutoverStatus"}:
            transitions = sequential_transitions(spec["values"])
        elif name == "SyncCandidateStatus":
            transitions = sequential_transitions(spec["values"][:5])
            transitions.extend(
                [
                    {"from": "DISPOSITIONED", "to": "REJECTED", "guard_id": "DISPOSITION_REJECT"},
                    {"from": "DISPOSITIONED", "to": "DEFERRED", "guard_id": "DISPOSITION_DEFER"},
                    {"from": "DISPOSITIONED", "to": "PORTING", "guard_id": "DISPOSITION_PORT"},
                    {"from": "PORTING", "to": "PORT_CANDIDATE", "guard_id": "PORT_COMPLETE"},
                    {"from": "PORT_CANDIDATE", "to": "VERIFIED", "guard_id": "PORT_VERIFIED"},
                    {"from": "VERIFIED", "to": "RELEASED", "guard_id": "RELEASED_PORT_SET"},
                    {"from": "RELEASED", "to": "BASELINE_RECORDED", "guard_id": "BASELINE_EVIDENCE_RECORDED"},
                    {"from": "RELEASED", "to": "ROLLED_BACK", "guard_id": "AUTHORIZED_ROLLBACK"},
                ]
            )
        else:
            transitions = []
        axes.append(
            {
                "axis_id": name,
                "owner_context": spec["owner"],
                "values": spec["values"],
                "terminal_values": spec["terminal"],
                "transitions": transitions,
                "transition_definition_status": "DEFINED" if transitions else "VALUES_ONLY_WAVE_2",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#16",
            }
        )
    return registry("REG-STATES-001", "1.0.0", axes)


def registry(registry_id: str, version: str, entries: Any, **extra: Any) -> dict[str, Any]:
    return {
        "registry_id": registry_id,
        "version": version,
        "status": "ACTIVE_DOCUMENTATION_CONTRACT",
        "generated_by": "scripts/architecture/generate_contracts.py",
        "entries": entries,
        **extra,
    }


def scalar_schema(key: str, value: Any, artifact_type: str) -> dict[str, Any]:
    if value is None:
        if key.endswith(("_count", "_seconds", "_budget")) or key in {"level", "cost", "tokens", "tool_calls", "output_bytes", "worker_attempts", "replication_count"}:
            return {"type": ["integer", "null"], "minimum": 0}
        if key.endswith("_at") or key in {"absolute_deadline", "expires_at"}:
            return {"type": ["string", "null"], "format": "date-time"}
        return {"type": ["string", "null"]}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, int):
        return {"type": "integer", "minimum": 0}
    if isinstance(value, float):
        return {"type": "number"}
    if key == "artifact_type":
        return {"const": artifact_type}
    if key == "schema_version":
        return {"const": value}
    result: dict[str, Any] = {"type": "string"}
    if key == "digest" or key.endswith("_digest"):
        result["x-ranex-runtime-pattern"] = "^sha256:[0-9a-f]{64}$"
    if key.endswith("_at") or key in {"absolute_deadline", "expires_at", "window_start", "window_end"}:
        result["x-ranex-runtime-format"] = "date-time"
    return result


def infer_schema(value: Any, key: str, artifact_type: str) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "type": "object",
            "properties": {name: infer_schema(child, name, artifact_type) for name, child in value.items()},
            "required": list(value.keys()),
            "additionalProperties": False,
        }
    if isinstance(value, list):
        return {"type": "array", "items": infer_schema(value[0], key, artifact_type) if value else {}}
    return scalar_schema(key, value, artifact_type)


def common_schemas() -> dict[str, dict[str, Any]]:
    digest = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    id_pattern = "^[a-z][a-z0-9_]*_[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    subject_variants = ["work-subject/v1", "exact-subject/v1", "architecture-subject/v1", "research-subject/v1", "resource-subject/v1"]
    return {
        "common/canonical-digest.schema.json": {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "https://schemas.ranex.dev/common/canonical-digest.schema.json", "title": "CanonicalDigest", **digest},
        "common/identifiers.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/common/identifiers.schema.json",
            "title": "Ranex prefixed UUIDv7 identifier",
            "type": "string",
            "pattern": id_pattern,
        },
        "common/subject-binding-v1.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/common/subject-binding-v1.schema.json",
            "type": "object",
            "properties": {
                "subject_schema": {"enum": subject_variants},
                "subject_ref": {"type": "string", "minLength": 1},
                "subject_digest": digest,
                "subject_manifest_digest": {"oneOf": [digest, {"type": "null"}]},
            },
            "required": ["subject_schema", "subject_ref", "subject_digest", "subject_manifest_digest"],
            "additionalProperties": False,
        },
        "common/evidence-ref.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/common/evidence-ref.schema.json",
            "type": "object",
            "properties": {"evidence_ref": {"type": "string", "minLength": 1}, "evidence_digest": digest},
            "required": ["evidence_ref", "evidence_digest"],
            "additionalProperties": False,
        },
    }


def subject_schema(name: str, required: list[str], properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://schemas.ranex.dev/common/{name}.schema.json",
        "title": name,
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def build_subject_schemas() -> dict[str, dict[str, Any]]:
    digest = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    nonempty = {"type": "string", "minLength": 1}
    commit = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
    nullable_digest = {"oneOf": [digest, {"type": "null"}]}
    nullable_commit = {"oneOf": [commit, {"type": "null"}]}
    shared_work = {
        "subject_schema": {"const": "work-subject/v1"},
        "project_id": nonempty,
        "work_item_id": nonempty,
        "repository_id": nonempty,
        "repository_uri_digest": digest,
        "base_revision": commit,
        "work_baseline_manifest_digest": digest,
        "signal_evidence_digest": digest,
        "requirements_baseline_digest": nullable_digest,
        "design_baseline_digest": nullable_digest,
        "observed_at": {"type": "string", "format": "date-time"},
    }
    exact = {
        "subject_schema": {"const": "exact-subject/v1"},
        **{key: nonempty for key in ["project_id", "work_item_id", "run_id", "workspace_id", "repository_id", "packet_id", "workflow_definition_id", "workflow_interpreter_version", "policy_activation_id", "module_profile_id", "schema_registry_version"]},
        "activity_id": {"type": ["string", "null"]},
        "effect_id": {"type": ["string", "null"]},
        "repository_uri_digest": digest,
        "base_commit": commit,
        "candidate_commit": nullable_commit,
        "artifact_digest": nullable_digest,
        **{key: digest for key in ["packet_digest", "workflow_definition_digest", "policy_activation_manifest_digest", "policy_decision_digest", "module_profile_digest", "capability_grant_digest"]},
        "route_lock_id": {"type": ["string", "null"]},
        "expected_run_aggregate_version": {"type": "integer", "minimum": 0},
    }
    architecture = {
        "subject_schema": {"const": "architecture-subject/v1"},
        **{key: nonempty for key in ["project_id", "work_item_id", "repository_id", "architecture_document_path"]},
        "repository_uri_digest": digest,
        "base_revision": commit,
        "candidate_revision": nullable_commit,
        "working_tree_digest": nullable_digest,
        **{key: digest for key in ["architecture_document_digest", "architecture_subject_manifest_digest", "contract_and_template_manifest_digest", "accepted_adr_registry_digest", "review_prompt_digest"]},
        "research_manifest_digests": {"type": "array", "items": digest},
    }
    research = {
        "subject_schema": {"const": "research-subject/v1"},
        **{key: nonempty for key in ["project_id", "work_item_id", "repository_id"]},
        "repository_uri_digest": digest,
        "base_revision": commit,
        **{key: digest for key in ["question_digest", "scope_digest", "source_manifest_digest", "research_prompt_digest"]},
        "observed_at": {"type": "string", "format": "date-time"},
    }
    resource = {
        "subject_schema": {"const": "resource-subject/v1"},
        "scope_kind": {"enum": ["PROJECT", "RELEASE", "WORK_ITEM", "RUN", "WORKER_ATTEMPT", "ACTIVITY", "EFFECT"]},
        **{key: {"type": ["string", "null"]} for key in ["project_id", "release_id", "work_item_id", "run_id", "worker_attempt_id", "activity_id", "effect_id", "parent_subject_ref"]},
        "repository_id": nonempty,
        "repository_uri_digest": digest,
        "base_revision": commit,
        "scope_manifest_digest": digest,
        "parent_subject_digest": nullable_digest,
    }
    return {
        "common/work-subject-v1.schema.json": subject_schema("work-subject-v1", list(shared_work), shared_work),
        "common/exact-subject-v1.schema.json": subject_schema("exact-subject-v1", list(exact), exact),
        "common/architecture-subject-v1.schema.json": subject_schema("architecture-subject-v1", list(architecture), architecture),
        "common/research-subject-v1.schema.json": subject_schema("research-subject-v1", list(research), research),
        "common/resource-subject-v1.schema.json": subject_schema("resource-subject-v1", list(resource), resource),
        "common/engineering-practice-profile-v1.schema.json": {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/common/engineering-practice-profile-v1.schema.json",
            "type": "object",
            "properties": {
                "schema_version": {"const": "engineering-practice-profile/v1"},
                "profile_id": nonempty,
                "registry_version": nonempty,
                "registry_digest": digest,
                "source_coverage": {
                    "type": "array",
                    "minItems": 9,
                    "maxItems": 9,
                    "uniqueItems": True,
                    "items": {
                        "type": "object",
                        "properties": {
                            "source_family_id": nonempty,
                            "applicability": {"enum": ["APPLICABLE", "NOT_APPLICABLE", "UNKNOWN"]},
                            "reason": {"type": "string"},
                            "evidence_refs": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["source_family_id", "applicability", "reason", "evidence_refs"],
                        "additionalProperties": False,
                    },
                },
                "sealing_eligible": {"type": "boolean"},
                "digest": digest,
            },
            "required": ["schema_version", "profile_id", "registry_version", "registry_digest", "source_coverage", "sealing_eligible", "digest"],
            "additionalProperties": False,
        },
    }


def test_practice_profile_schema() -> dict[str, Any]:
    digest = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    nonempty = {"type": "string", "minLength": 1}
    nullable_nonempty = {"oneOf": [nonempty, {"type": "null"}]}
    nullable_digest = {"oneOf": [digest, {"type": "null"}]}
    disposition = {
        "type": "object",
        "properties": {
            "result": {"enum": ["APPLICABLE", "NOT_APPLICABLE", "UNKNOWN"]},
            "rule_id": {"type": "string"},
            "reason": {"type": "string"},
            "evidence_refs": {"type": "array", "items": nonempty, "uniqueItems": True},
            "approval_ref": {"type": "string"},
        },
        "required": ["result", "rule_id", "reason", "evidence_refs", "approval_ref"],
        "additionalProperties": False,
    }
    evidence_refs = {"type": "array", "items": nonempty, "uniqueItems": True}
    execution_status = {
        "enum": ["NOT_ASSESSED", "NOT_APPLICABLE", "PASS", "FAIL", "UNKNOWN"]
    }
    fixture_record = {
        "type": "object",
        "properties": {
            "fixture_id": nonempty,
            "canonical_path": nonempty,
            "semantic_owner_id": nonempty,
            "provenance_ref": nonempty,
            "version": nonempty,
            "classification": {
                "enum": [
                    "PUBLIC",
                    "INTERNAL",
                    "CONFIDENTIAL",
                    "SECRET",
                    "INHERITS_SUBJECT",
                ]
            },
            "mutation_authority_id": nonempty,
            "hidden_from_maker": {"type": "boolean"},
            "subject_kinds": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "status": {"enum": ["ACTIVE", "RETIRED"]},
        },
        "required": [
            "fixture_id",
            "canonical_path",
            "semantic_owner_id",
            "provenance_ref",
            "version",
            "classification",
            "mutation_authority_id",
            "hidden_from_maker",
            "subject_kinds",
            "status",
        ],
        "additionalProperties": False,
    }
    quarantine_record = {
        "type": "object",
        "properties": {
            "quarantine_id": nonempty,
            "test_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "subject_ref": nonempty,
            "subject_digest": digest,
            "observed_failure_distribution": {
                "type": "object",
                "properties": {
                    "window_start": {"type": "string", "format": "date-time"},
                    "window_end": {"type": "string", "format": "date-time"},
                    "total_runs": {"type": "integer", "minimum": 1},
                    "passes": {"type": "integer", "minimum": 0},
                    "failures": {"type": "integer", "minimum": 1},
                    "infrastructure_errors": {"type": "integer", "minimum": 0},
                    "retries": {"type": "integer", "minimum": 0},
                    "retry_passes": {"type": "integer", "minimum": 0},
                    "failure_signatures": {
                        "type": "array",
                        "minItems": 1,
                        "items": nonempty,
                        "uniqueItems": True,
                    },
                },
                "required": [
                    "window_start",
                    "window_end",
                    "total_runs",
                    "passes",
                    "failures",
                    "infrastructure_errors",
                    "retries",
                    "retry_passes",
                    "failure_signatures",
                ],
                "additionalProperties": False,
            },
            "affected_gate_ids": {
                **evidence_refs,
                "minItems": 1,
            },
            "affected_risk_ids": {
                **evidence_refs,
                "minItems": 1,
            },
            "alternate_evidence_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "alternate_evidence_noncompensating": {"const": True},
            "gate_disposition": {"enum": ["BLOCKED", "UNKNOWN"]},
            "retry_passes_non_authoritative": {"const": True},
            "owner_id": nonempty,
            "linked_work_item_id": nonempty,
            "reason": nonempty,
            "opened_at": {"type": "string", "format": "date-time"},
            "expires_at": {"type": "string", "format": "date-time"},
            "removal_criteria": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "restoration_plan_ref": nonempty,
            "backfill_test_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "status": {"enum": ["ACTIVE", "REMOVED"]},
            "removal_evidence_refs": evidence_refs,
        },
        "required": [
            "quarantine_id",
            "test_refs",
            "subject_ref",
            "subject_digest",
            "observed_failure_distribution",
            "affected_gate_ids",
            "affected_risk_ids",
            "alternate_evidence_refs",
            "alternate_evidence_noncompensating",
            "gate_disposition",
            "retry_passes_non_authoritative",
            "owner_id",
            "linked_work_item_id",
            "reason",
            "opened_at",
            "expires_at",
            "removal_criteria",
            "restoration_plan_ref",
            "backfill_test_refs",
            "status",
            "removal_evidence_refs",
        ],
        "additionalProperties": False,
    }
    trace_disposition = {
        "type": "object",
        "properties": {
            "trace_id": nonempty,
            "disposition": {
                "enum": ["REPLACED", "RETIRED", "NOT_APPLICABLE"]
            },
            "decision_ref": nonempty,
        },
        "required": ["trace_id", "disposition", "decision_ref"],
        "additionalProperties": False,
    }
    obsolete_test_deletion = {
        "type": "object",
        "properties": {
            "deletion_id": nonempty,
            "test_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "requirement_trace_dispositions": {
                "type": "array",
                "minItems": 1,
                "items": trace_disposition,
            },
            "risk_trace_dispositions": {
                "type": "array",
                "minItems": 1,
                "items": trace_disposition,
            },
            "replacement_evidence_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "fixture_cleanup_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "snapshot_cleanup_refs": {
                **evidence_refs,
                "minItems": 1,
            },
            "owner_id": nonempty,
            "approval_ref": nonempty,
            "rationale": nonempty,
            "deleted_at": {"type": "string", "format": "date-time"},
            "resulting_gap_status": {"const": "NONE"},
        },
        "required": [
            "deletion_id",
            "test_refs",
            "requirement_trace_dispositions",
            "risk_trace_dispositions",
            "replacement_evidence_refs",
            "fixture_cleanup_refs",
            "snapshot_cleanup_refs",
            "owner_id",
            "approval_ref",
            "rationale",
            "deleted_at",
            "resulting_gap_status",
        ],
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/test-practice-profile-v1.schema.json",
        "title": "Ranex test-practice profile",
        "type": "object",
        "properties": {
            "schema_version": {"const": "test-practice-profile/v1"},
            "profile_id": nonempty,
            "profile_kind": {"enum": ["DEFINITION_BASELINE", "TASK"]},
            "profile_version": nonempty,
            "policy_version": nonempty,
            "registry_id": {"const": "REG-TEST-PRACTICES-001"},
            "registry_version": nonempty,
            "registry_digest": digest,
            "subject_ref": nullable_nonempty,
            "subject_digest": nullable_digest,
            "created_at": {"type": "string", "format": "date-time"},
            "applicability": disposition,
            "material_unknowns": {"type": "array", "items": nonempty, "uniqueItems": True},
            "test_roots": {
                "type": "array",
                "minItems": len(TEST_TAXONOMY),
                "maxItems": len(TEST_TAXONOMY),
                "uniqueItems": True,
                "items": {"enum": [row["root"] for row in TEST_TAXONOMY]},
            },
            "category_coverage": {
                "type": "array",
                "minItems": len(TEST_TAXONOMY),
                "maxItems": len(TEST_TAXONOMY),
                "items": {
                    "type": "object",
                    "properties": {
                        "category_id": {"enum": [row["category_id"] for row in TEST_TAXONOMY]},
                        "root": {"enum": [row["root"] for row in TEST_TAXONOMY]},
                        "applicability": disposition,
                        "task_selection_rule": {
                            "const": "RISK_AND_EXACT_SUBJECT_SELECTED"
                        },
                        "execution_status": execution_status,
                        "evidence_refs": evidence_refs,
                    },
                    "required": [
                        "category_id",
                        "root",
                        "applicability",
                        "task_selection_rule",
                        "execution_status",
                        "evidence_refs",
                    ],
                    "additionalProperties": False,
                },
            },
            "context_layer_mirroring": {
                "type": "object",
                "properties": {
                    "policy": {"const": "LANE_SPECIFIC_SUBJECT_SHAPES"},
                    "lane_shapes": {
                        "type": "array",
                        "minItems": len(TEST_TAXONOMY),
                        "maxItems": len(TEST_TAXONOMY),
                        "items": {
                            "type": "object",
                            "properties": {
                                "category_id": {
                                    "enum": [
                                        row["category_id"]
                                        for row in TEST_TAXONOMY
                                    ]
                                },
                                "semantic_owner_parameter": {
                                    "enum": [
                                        "CONTEXT",
                                        "CAPABILITY",
                                        "OWNER",
                                        "EXACT_TEST_METADATA",
                                    ]
                                },
                                "path_patterns": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": nonempty,
                                    "uniqueItems": True,
                                },
                                "mirrored_source_layers": {
                                    "type": "array",
                                    "items": {"enum": MODULAR_DDD_LAYERS},
                                    "uniqueItems": True,
                                },
                                "shape_rule": nonempty,
                            },
                            "required": [
                                "category_id",
                                "semantic_owner_parameter",
                                "path_patterns",
                                "mirrored_source_layers",
                                "shape_rule",
                            ],
                            "additionalProperties": False,
                        },
                    },
                    "exceptions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "context_id": nonempty,
                                "omitted_layers": {
                                    "type": "array",
                                    "minItems": 1,
                                    "uniqueItems": True,
                                    "items": {"enum": MODULAR_DDD_LAYERS},
                                },
                                "reason": nonempty,
                                "decision_ref": nonempty,
                                "expires_at": {"type": "string", "format": "date-time"},
                            },
                            "required": ["context_id", "omitted_layers", "reason", "decision_ref", "expires_at"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["policy", "lane_shapes", "exceptions"],
                "additionalProperties": False,
            },
            "architecture_checks": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": nonempty,
            },
            "fixture_ownership": {
                "type": "object",
                "properties": {
                    "owner_required": {"const": True},
                    "canonical_root_required": {"const": True},
                    "classification_required": {"const": True},
                    "mutation_authority_required": {"const": True},
                    "hidden_fixture_separation_required": {"const": True},
                },
                "required": [
                    "owner_required",
                    "canonical_root_required",
                    "classification_required",
                    "mutation_authority_required",
                    "hidden_fixture_separation_required",
                ],
                "additionalProperties": False,
            },
            "fixture_records": {
                "type": "array",
                "items": fixture_record,
            },
            "quarantine_policy": {
                "type": "object",
                "properties": {
                    "metadata_required": {"const": True},
                    "owner_required": {"const": True},
                    "reason_required": {"const": True},
                    "expiry_required": {"const": True},
                    "linked_work_item_required": {"const": True},
                    "silent_skip_forbidden": {"const": True},
                },
                "required": [
                    "metadata_required",
                    "owner_required",
                    "reason_required",
                    "expiry_required",
                    "linked_work_item_required",
                    "silent_skip_forbidden",
                ],
                "additionalProperties": False,
            },
            "quarantine_records": {
                "type": "array",
                "items": quarantine_record,
            },
            "obsolete_test_deletions": {
                "type": "array",
                "items": obsolete_test_deletion,
            },
            "unit_lane_policy": {
                "type": "object",
                "properties": {
                    "network_forbidden": {"const": True},
                    "wall_clock_forbidden": {"const": True},
                    "ambient_randomness_forbidden": {"const": True},
                    "declared_seed_required": {"const": True},
                    "injected_clock_required": {"const": True},
                    "deterministic_id_source_required": {"const": True},
                },
                "required": [
                    "network_forbidden",
                    "wall_clock_forbidden",
                    "ambient_randomness_forbidden",
                    "declared_seed_required",
                    "injected_clock_required",
                    "deterministic_id_source_required",
                ],
                "additionalProperties": False,
            },
            "generated_code_test_exceptions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path_pattern": nonempty,
                        "generator_manifest_ref": nonempty,
                        "source_contract_test_ref": nonempty,
                        "reason": nonempty,
                        "approval_ref": nonempty,
                        "expires_at": {"type": "string", "format": "date-time"},
                    },
                    "required": [
                        "path_pattern",
                        "generator_manifest_ref",
                        "source_contract_test_ref",
                        "reason",
                        "approval_ref",
                        "expires_at",
                    ],
                    "additionalProperties": False,
                },
            },
            "production_path_parity": {
                "type": "object",
                "properties": {
                    "same_artifact_contracts_required": {"const": True},
                    "same_public_apis_required": {"const": True},
                    "same_composition_root_required": {"const": True},
                    "test_only_production_conditionals_forbidden": {"const": True},
                    "bypass_flags_forbidden": {"const": True},
                    "alternate_policy_or_reducer_paths_forbidden": {"const": True},
                    "mocks_only_at_declared_external_ports": {"const": True},
                    "adapter_fake_contract_parity_required": {"const": True},
                    "real_migrations_and_sqlite_required_for_persistence": {"const": True},
                    "replay_digest_stability_required": {"const": True},
                },
                "required": [
                    "same_artifact_contracts_required",
                    "same_public_apis_required",
                    "same_composition_root_required",
                    "test_only_production_conditionals_forbidden",
                    "bypass_flags_forbidden",
                    "alternate_policy_or_reducer_paths_forbidden",
                    "mocks_only_at_declared_external_ports",
                    "adapter_fake_contract_parity_required",
                    "real_migrations_and_sqlite_required_for_persistence",
                    "replay_digest_stability_required",
                ],
                "additionalProperties": False,
            },
            "failure_mode_matrix": {
                "type": "array",
                "minItems": len(FAILURE_MODE_CLASSES),
                "maxItems": len(FAILURE_MODE_CLASSES),
                "items": {
                    "type": "object",
                    "properties": {
                        "failure_mode_class": {"enum": FAILURE_MODE_CLASSES},
                        "applicability": disposition,
                        "required_assertions": {
                            "type": "array",
                            "minItems": len(EXPECTED_FAILURE_ASSERTIONS),
                            "maxItems": len(EXPECTED_FAILURE_ASSERTIONS),
                            "uniqueItems": True,
                            "items": {"enum": EXPECTED_FAILURE_ASSERTIONS},
                        },
                        "transition_ids": {"type": "array", "items": nonempty, "uniqueItems": True},
                        "precondition_refs": evidence_refs,
                        "fault_input_refs": evidence_refs,
                        "test_lanes": {
                            "type": "array",
                            "uniqueItems": True,
                            "items": {"enum": [row["category_id"] for row in TEST_TAXONOMY]},
                        },
                        "owner_id": {"type": "string"},
                        "execution_status": execution_status,
                        "evidence_refs": evidence_refs,
                    },
                    "required": [
                        "failure_mode_class",
                        "applicability",
                        "required_assertions",
                        "transition_ids",
                        "precondition_refs",
                        "fault_input_refs",
                        "test_lanes",
                        "owner_id",
                        "execution_status",
                        "evidence_refs",
                    ],
                    "additionalProperties": False,
                },
            },
            "edge_case_partitions": {
                "type": "array",
                "minItems": len(EDGE_CASE_PARTITIONS),
                "maxItems": len(EDGE_CASE_PARTITIONS),
                "items": {
                    "type": "object",
                    "properties": {
                        "partition_id": {"enum": [row["partition_id"] for row in EDGE_CASE_PARTITIONS]},
                        "space_kind": {"enum": ["FINITE", "OPEN"]},
                        "required_methods": {
                            "type": "array",
                            "minItems": 1,
                            "uniqueItems": True,
                            "items": {"enum": ["EXHAUSTIVE_TRANSITION_TABLE", "BOUNDARY_PARTITION", "PROPERTY", "MODEL", "FUZZ", "MUTATION", "FAULT_INJECTION"]},
                        },
                        "applicability": disposition,
                        "seed_refs": evidence_refs,
                        "corpus_refs": evidence_refs,
                        "property_ids": evidence_refs,
                        "invariant_ids": evidence_refs,
                        "shrinking_reproduction_refs": evidence_refs,
                        "remaining_unknowns": evidence_refs,
                        "execution_status": execution_status,
                        "evidence_refs": evidence_refs,
                    },
                    "required": [
                        "partition_id",
                        "space_kind",
                        "required_methods",
                        "applicability",
                        "seed_refs",
                        "corpus_refs",
                        "property_ids",
                        "invariant_ids",
                        "shrinking_reproduction_refs",
                        "remaining_unknowns",
                        "execution_status",
                        "evidence_refs",
                    ],
                    "additionalProperties": False,
                },
            },
            "production_evidence_obligations": {
                "type": "array",
                "minItems": len(PRODUCTION_EVIDENCE_OBLIGATIONS),
                "maxItems": len(PRODUCTION_EVIDENCE_OBLIGATIONS),
                "items": {
                    "type": "object",
                    "properties": {
                        "obligation_id": {
                            "enum": [
                                row["obligation_id"]
                                for row in PRODUCTION_EVIDENCE_OBLIGATIONS
                            ]
                        },
                        "required_evidence_fields": {
                            "type": "array",
                            "minItems": 1,
                            "items": nonempty,
                            "uniqueItems": True,
                        },
                        "task_selection_rule": nonempty,
                        "applicability": disposition,
                        "execution_status": execution_status,
                        "evidence_refs": evidence_refs,
                    },
                    "required": [
                        "obligation_id",
                        "required_evidence_fields",
                        "task_selection_rule",
                        "applicability",
                        "execution_status",
                        "evidence_refs",
                    ],
                    "additionalProperties": False,
                },
            },
            "traceability": {
                "type": "object",
                "properties": {
                    "requirement_ids": evidence_refs,
                    "risk_ids": evidence_refs,
                    "practice_ids": evidence_refs,
                    "transition_ids": evidence_refs,
                },
                "required": ["requirement_ids", "risk_ids", "practice_ids", "transition_ids"],
                "additionalProperties": False,
            },
            "evidence": {
                "type": "object",
                "properties": {
                    "built_artifact_refs": evidence_refs,
                    "composition_identity_refs": evidence_refs,
                    "mock_target_classification_refs": evidence_refs,
                    "negative_test_refs": evidence_refs,
                    "mutation_evidence_refs": evidence_refs,
                    "fault_injection_evidence_refs": evidence_refs,
                    "adapter_fake_contract_refs": evidence_refs,
                    "persistence_migration_refs": evidence_refs,
                    "replay_digest_refs": evidence_refs,
                },
                "required": [
                    "built_artifact_refs",
                    "composition_identity_refs",
                    "mock_target_classification_refs",
                    "negative_test_refs",
                    "mutation_evidence_refs",
                    "fault_injection_evidence_refs",
                    "adapter_fake_contract_refs",
                    "persistence_migration_refs",
                    "replay_digest_refs",
                ],
                "additionalProperties": False,
            },
            "evidence_bindings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "evidence_ref": nonempty,
                        "subject_ref": nonempty,
                        "subject_digest": digest,
                        "freshness_status": {"enum": ["CURRENT", "STALE", "UNKNOWN"]},
                        "result": {"enum": ["PASS", "FAIL", "UNKNOWN"]},
                    },
                    "required": [
                        "evidence_ref",
                        "subject_ref",
                        "subject_digest",
                        "freshness_status",
                        "result",
                    ],
                    "additionalProperties": False,
                },
            },
            "evidence_scope": {"enum": ["NONE", "SYNTHETIC", "RUNTIME", "MIXED"]},
            "runtime_evidence_status": {"enum": ["NOT_ASSESSED", "PASS", "FAIL", "UNKNOWN"]},
            "derived_result": {"enum": ["NOT_ASSESSED", "UNKNOWN", "NOT_APPLICABLE", "PASS", "FAIL"]},
            "sealing_eligible": {"type": "boolean"},
            "digest": digest,
        },
        "required": [
            "schema_version",
            "profile_id",
            "profile_kind",
            "profile_version",
            "policy_version",
            "registry_id",
            "registry_version",
            "registry_digest",
            "subject_ref",
            "subject_digest",
            "created_at",
            "applicability",
            "material_unknowns",
            "test_roots",
            "category_coverage",
            "context_layer_mirroring",
            "architecture_checks",
            "fixture_ownership",
            "fixture_records",
            "quarantine_policy",
            "quarantine_records",
            "obsolete_test_deletions",
            "unit_lane_policy",
            "generated_code_test_exceptions",
            "production_path_parity",
            "failure_mode_matrix",
            "edge_case_partitions",
            "production_evidence_obligations",
            "traceability",
            "evidence",
            "evidence_bindings",
            "evidence_scope",
            "runtime_evidence_status",
            "derived_result",
            "sealing_eligible",
            "digest",
        ],
        "additionalProperties": False,
    }


def architecture_rule_assessment_schema() -> dict[str, Any]:
    digest = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    nonempty = {"type": "string", "minLength": 1}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/architecture-rule-assessment-v1.schema.json",
        "title": "Ranex per-rule architecture assessment",
        "type": "object",
        "properties": {
            "schema_version": {"const": "architecture-rule-assessment/v1"},
            "assessment_id": nonempty,
            "rule_id": {
                "type": "string",
                "pattern": "^(ORG|TDD|ARCH|ARCH9)-[A-Z0-9-]+$",
            },
            "rule_family": {"enum": ["ORG", "TDD", "ADR9"]},
            "rule_definition_digest": digest,
            "subject_schema": {"const": "architecture-subject/v1"},
            "subject_scope": {"const": "DEFINITION_CONTRACT_ONLY"},
            "subject_ref": nonempty,
            "subject_digest": digest,
            "subject_manifest_digest": digest,
            "runtime_subject_ref": {"type": "null"},
            "runtime_subject_digest": {"type": "null"},
            "rule_owner_id": nonempty,
            "assessor_id": nonempty,
            "applicability": {
                "type": "object",
                "properties": {
                    "result": {"enum": ["APPLICABLE", "NOT_APPLICABLE", "UNKNOWN"]},
                    "rule_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "evidence_refs": {
                        "type": "array",
                        "items": nonempty,
                        "uniqueItems": True,
                    },
                    "approval_ref": {"type": "string"},
                },
                "required": ["result", "rule_id", "reason", "evidence_refs", "approval_ref"],
                "additionalProperties": False,
            },
            "result": {"enum": ["NOT_ASSESSED", "UNKNOWN", "NOT_APPLICABLE", "EVALUATED"]},
            "outcome": {"type": ["string", "null"], "enum": ["PASS", "FAIL", None]},
            "numeric_score": {"type": "null"},
            "definition_evidence_refs": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "runtime_evidence_refs": {
                "type": "array",
                "items": nonempty,
                "uniqueItems": True,
            },
            "recorded_at": {"type": "string", "format": "date-time"},
            "observed_at": {"type": ["string", "null"], "format": "date-time"},
            "expires_at": {"type": ["string", "null"], "format": "date-time"},
            "freshness_status": {"enum": ["NOT_ASSESSED", "CURRENT", "STALE", "UNKNOWN"]},
            "noncompensating": {"const": True},
            "runtime_evidence_status": {"enum": ["NOT_ASSESSED", "PASS", "FAIL", "UNKNOWN"]},
            "digest": digest,
        },
        "required": [
            "schema_version",
            "assessment_id",
            "rule_id",
            "rule_family",
            "rule_definition_digest",
            "subject_schema",
            "subject_scope",
            "subject_ref",
            "subject_digest",
            "subject_manifest_digest",
            "runtime_subject_ref",
            "runtime_subject_digest",
            "rule_owner_id",
            "assessor_id",
            "applicability",
            "result",
            "outcome",
            "numeric_score",
            "definition_evidence_refs",
            "runtime_evidence_refs",
            "recorded_at",
            "observed_at",
            "expires_at",
            "freshness_status",
            "noncompensating",
            "runtime_evidence_status",
            "digest",
        ],
        "additionalProperties": False,
    }


def architecture_practice_application_profile_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    string_array = {
        "type": "array",
        "items": nonempty,
        "uniqueItems": True,
    }
    disposition = {"enum": ["APPLICABLE", "NOT_APPLICABLE", "UNKNOWN"]}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/common/"
            "architecture-practice-application-profile-v1.schema.json"
        ),
        "title": "Ranex architecture practice application profile",
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "architecture-practice-application-profile/v1"
            },
            "profile_id": nonempty,
            "version": nonempty,
            "status": nonempty,
            "subject": {
                "type": "object",
                "properties": {
                    "subject_id": nonempty,
                    "subject_kind": {"const": "ARCHITECTURE_DESIGN"},
                    "basis_revision": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{40}$",
                    },
                    "working_tree_status": nonempty,
                    "normative_source_refs": {
                        **string_array,
                        "minItems": 1,
                    },
                    "runtime_subject_included": {"type": "boolean"},
                },
                "required": [
                    "subject_id",
                    "subject_kind",
                    "basis_revision",
                    "working_tree_status",
                    "normative_source_refs",
                    "runtime_subject_included",
                ],
                "additionalProperties": False,
            },
            "source_registry_binding": {
                "type": "object",
                "properties": {
                    "path": nonempty,
                    "registry_id": nonempty,
                    "version": nonempty,
                    "sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                    "required_source_family_count": {
                        "type": "integer",
                        "minimum": 1,
                    },
                    "required_practice_count": {
                        "type": "integer",
                        "minimum": 1,
                    },
                },
                "required": [
                    "path",
                    "registry_id",
                    "version",
                    "sha256",
                    "required_source_family_count",
                    "required_practice_count",
                ],
                "additionalProperties": False,
            },
            "disposition_policy": {
                "type": "object",
                "properties": {
                    "allowed_dispositions": {
                        "type": "array",
                        "items": disposition,
                        "minItems": 3,
                        "maxItems": 3,
                        "uniqueItems": True,
                    },
                    "not_applicable_requires_rationale": {"const": True},
                    "unknown_requires_materiality_and_blocking_effect": {
                        "const": True
                    },
                    "design_application_does_not_imply_runtime_enactment": {
                        "const": True
                    },
                    "runtime_pass_requires_separate_exact_subject_evidence": {
                        "const": True
                    },
                    "arithmetic_aggregation_prohibited": {"const": True},
                },
                "required": [
                    "allowed_dispositions",
                    "not_applicable_requires_rationale",
                    "unknown_requires_materiality_and_blocking_effect",
                    "design_application_does_not_imply_runtime_enactment",
                    "runtime_pass_requires_separate_exact_subject_evidence",
                    "arithmetic_aggregation_prohibited",
                ],
                "additionalProperties": False,
            },
            "family_dispositions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "source_family_id": nonempty,
                        "disposition": disposition,
                        "practice_ids": string_array,
                        "rationale": nonempty,
                        "runtime_verification_required": {"type": "boolean"},
                    },
                    "required": [
                        "source_family_id",
                        "disposition",
                        "practice_ids",
                        "rationale",
                        "runtime_verification_required",
                    ],
                    "additionalProperties": False,
                },
            },
            "material_unknowns": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "unknown_id": nonempty,
                        "practice_ids": {
                            **string_array,
                            "minItems": 1,
                        },
                        "detail": nonempty,
                        "blocking_effect": nonempty,
                    },
                    "required": [
                        "unknown_id",
                        "practice_ids",
                        "detail",
                        "blocking_effect",
                    ],
                    "additionalProperties": False,
                },
            },
            "practice_applications": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "practice_id": nonempty,
                        "source_family_id": nonempty,
                        "disposition": disposition,
                        "design_application_status": {
                            "enum": [
                                "APPLIED",
                                "PARTIAL",
                                "NOT_APPLICABLE",
                                "UNKNOWN",
                            ]
                        },
                        "material_unknown": {"type": "boolean"},
                        "design_behavior": nonempty,
                        "architecture_element_ids": string_array,
                        "adr_ids": string_array,
                        "decision_ids": string_array,
                        "org_rule_ids": string_array,
                        "tdd_rule_ids": string_array,
                        "source_locators": {
                            **string_array,
                            "minItems": 1,
                        },
                        "design_evidence_refs": {
                            **string_array,
                            "minItems": 1,
                        },
                        "limitation_or_conflict": {"type": "string"},
                        "not_applicable_rationale": {"type": "string"},
                        "runtime_verification_required": {"type": "boolean"},
                        "runtime_enactment_status": {
                            "enum": [
                                "NOT_ASSESSED",
                                "NOT_APPLICABLE",
                                "UNKNOWN",
                                "PASS",
                                "FAIL",
                            ]
                        },
                    },
                    "required": [
                        "practice_id",
                        "source_family_id",
                        "disposition",
                        "design_application_status",
                        "material_unknown",
                        "design_behavior",
                        "architecture_element_ids",
                        "adr_ids",
                        "decision_ids",
                        "org_rule_ids",
                        "tdd_rule_ids",
                        "source_locators",
                        "design_evidence_refs",
                        "limitation_or_conflict",
                        "not_applicable_rationale",
                        "runtime_verification_required",
                        "runtime_enactment_status",
                    ],
                    "additionalProperties": False,
                },
            },
            "summary": {
                "type": "object",
                "properties": {
                    "source_family_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "practice_count": {"type": "integer", "minimum": 0},
                    "applicable_count": {"type": "integer", "minimum": 0},
                    "not_applicable_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "unknown_applicability_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "design_applied_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "design_partial_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "material_unknown_practice_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "runtime_not_assessed_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "runtime_not_applicable_count": {
                        "type": "integer",
                        "minimum": 0,
                    },
                    "sealing_eligible": {"type": "boolean"},
                    "arithmetic_score": {"type": "null"},
                },
                "required": [
                    "source_family_count",
                    "practice_count",
                    "applicable_count",
                    "not_applicable_count",
                    "unknown_applicability_count",
                    "design_applied_count",
                    "design_partial_count",
                    "material_unknown_practice_count",
                    "runtime_not_assessed_count",
                    "runtime_not_applicable_count",
                    "sealing_eligible",
                    "arithmetic_score",
                ],
                "additionalProperties": False,
            },
            "runtime_claim": nonempty,
        },
        "required": [
            "schema_version",
            "profile_id",
            "version",
            "status",
            "subject",
            "source_registry_binding",
            "disposition_policy",
            "family_dispositions",
            "material_unknowns",
            "practice_applications",
            "summary",
            "runtime_claim",
        ],
        "additionalProperties": False,
    }


def path_contract_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/path-contract-v1.schema.json",
        "title": "Ranex governed path contract",
        "type": "object",
        "properties": {
            "path_id": nonempty,
            "owner_context": nonempty,
            "governance_owner_context": nonempty,
            "semantic_owner_kind": {
                "enum": [
                    "EXACT_CONTEXT",
                    "PARAMETERIZED_CONTEXT",
                    "PARAMETERIZED_TEST_SUBJECT_OWNER",
                    "FIXED_CROSS_CONTEXT_OWNER",
                ]
            },
            "semantic_owner_context": {"type": ["string", "null"]},
            "semantic_owner_resolution": nonempty,
            "accountable_human_role": nonempty,
            "required_reviewer_role": nonempty,
            "path_pattern": nonempty,
            "responsibility_class": nonempty,
            "applicability": {"type": "string"},
            "allowed_dependency_targets": {
                "type": "array",
                "items": nonempty,
                "uniqueItems": True,
            },
            "dependency_direction": nonempty,
            "data_ownership_refs": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "data_classification": {"enum": ["PUBLIC", "INHERITS_SUBJECT_CLASSIFICATION"]},
            "content_status": {"enum": ["MANUAL", "GENERATED", "LEGACY", "MIXED"]},
            "topology_rule_ids": {
                "type": "array",
                "minItems": 1,
                "items": {"type": "string", "pattern": "^ORG-[A-Z0-9-]+$"},
                "uniqueItems": True,
            },
            "tdd_rule_ids": {
                "type": "array",
                "items": {"type": "string", "pattern": "^TDD-[A-Z0-9-]+$"},
                "uniqueItems": True,
            },
            "exception_metadata": {
                "type": "object",
                "properties": {
                    "required": {"type": "boolean"},
                    "allowed_classes": {
                        "type": "array",
                        "items": nonempty,
                        "uniqueItems": True,
                    },
                    "current_exception_ids": {
                        "type": "array",
                        "items": nonempty,
                        "uniqueItems": True,
                    },
                },
                "required": ["required", "allowed_classes", "current_exception_ids"],
                "additionalProperties": False,
            },
            "required_exception_class": {"type": "string"},
            "definition_status": {"const": "DEFINED"},
            "runtime_validation_status": {"const": "NOT_ASSESSED"},
            "source": nonempty,
        },
        "required": [
            "path_id",
            "owner_context",
            "governance_owner_context",
            "semantic_owner_kind",
            "semantic_owner_context",
            "semantic_owner_resolution",
            "accountable_human_role",
            "required_reviewer_role",
            "path_pattern",
            "responsibility_class",
            "applicability",
            "allowed_dependency_targets",
            "dependency_direction",
            "data_ownership_refs",
            "data_classification",
            "content_status",
            "topology_rule_ids",
            "tdd_rule_ids",
            "exception_metadata",
            "definition_status",
            "runtime_validation_status",
            "source",
        ],
        "additionalProperties": False,
    }


def context_dependency_edge_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/context-dependency-edge-v1.schema.json",
        "title": "Ranex declared context dependency edge",
        "type": "object",
        "properties": {
            "schema_version": {"const": "context-dependency-edge/v1"},
            "edge_id": nonempty,
            "caller": nonempty,
            "callee": nonempty,
            "caller_owner": nonempty,
            "callee_owner": nonempty,
            "rationale": nonempty,
            "interaction": {
                "enum": ["SYNC_QUERY", "SYNC_COMMAND", "ASYNC_EVENT"]
            },
            "consistency": {
                "enum": [
                    "READ_ONLY_SNAPSHOT",
                    "CALLEE_TRANSACTION_ONLY",
                    "EVENTUAL_OUTBOX",
                ]
            },
            "failure": {"const": "FAIL_CLOSED_REQUIRED"},
            "recovery": {
                "enum": [
                    "REFRESH_REEVALUATE",
                    "IDEMPOTENT_RETRY_RECONCILE",
                    "OUTBOX_REPLAY_RECONCILE",
                ]
            },
            "definition_status": {"const": "DEFINED"},
            "runtime_validation_status": {"const": "NOT_ASSESSED"},
            "source": nonempty,
        },
        "required": [
            "schema_version",
            "edge_id",
            "caller",
            "callee",
            "caller_owner",
            "callee_owner",
            "rationale",
            "interaction",
            "consistency",
            "failure",
            "recovery",
            "definition_status",
            "runtime_validation_status",
            "source",
        ],
        "additionalProperties": False,
    }


def context_boundary_fit_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/context-boundary-fit-v1.schema.json",
        "title": "Ranex context boundary-fit hypothesis",
        "type": "object",
        "properties": {
            "schema_version": {"const": "context-boundary-fit/v1"},
            "context_id": nonempty,
            "owner": nonempty,
            "consistency_hypothesis": nonempty,
            "failure_hypothesis": nonempty,
            "ownership_hypothesis": nonempty,
            "change_locality_hypothesis": nonempty,
            "merge_candidate": nonempty,
            "split_candidate": nonempty,
            "tracer_falsifier": nonempty,
            "accountable_human_role": nonempty,
            "required_reviewer_role": nonempty,
            "definition_status": {"const": "DEFINED"},
            "tracer_result": {"const": "NOT_ASSESSED"},
            "boundary_decision_status": {"const": "NOT_ASSESSED"},
            "runtime_validation_status": {"const": "NOT_ASSESSED"},
            "source": nonempty,
        },
        "required": [
            "schema_version",
            "context_id",
            "owner",
            "consistency_hypothesis",
            "failure_hypothesis",
            "ownership_hypothesis",
            "change_locality_hypothesis",
            "merge_candidate",
            "split_candidate",
            "tracer_falsifier",
            "accountable_human_role",
            "required_reviewer_role",
            "definition_status",
            "tracer_result",
            "boundary_decision_status",
            "runtime_validation_status",
            "source",
        ],
        "additionalProperties": False,
    }


def context_coupling_policy_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    evidence_refs = {
        "type": "array",
        "items": nonempty,
        "uniqueItems": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/context-coupling-policy-v1.schema.json",
        "title": "Ranex governed-execution coupling policy",
        "type": "object",
        "properties": {
            "schema_version": {"const": "context-coupling-policy/v1"},
            "coupling_policy_id": nonempty,
            "version": nonempty,
            "subject_context": nonempty,
            "measurement_owner": nonempty,
            "decision_owner": nonempty,
            "reference_windows": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "declared_static_fan_out": {
                "type": "integer",
                "minimum": 0,
            },
            "declared_static_fan_in": {
                "type": "integer",
                "minimum": 0,
            },
            "measures": {
                "type": "array",
                "minItems": 6,
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "properties": {
                        "measure_id": nonempty,
                        "definition": nonempty,
                        "cadence": nonempty,
                        "review_trigger": nonempty,
                        "rationale": nonempty,
                        "owner_id": nonempty,
                        "result": {"const": "NOT_ASSESSED"},
                        "evidence_refs": evidence_refs,
                    },
                    "required": [
                        "measure_id",
                        "definition",
                        "cadence",
                        "review_trigger",
                        "rationale",
                        "owner_id",
                        "result",
                        "evidence_refs",
                    ],
                    "additionalProperties": False,
                },
            },
            "responses": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "rule_ids": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "fitness_ids": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "noncompensating": {"const": True},
            "decision_binding": {"type": "object"},
            "runtime_validation_status": {"const": "NOT_ASSESSED"},
            "source": nonempty,
        },
        "required": [
            "schema_version",
            "coupling_policy_id",
            "version",
            "subject_context",
            "measurement_owner",
            "decision_owner",
            "reference_windows",
            "declared_static_fan_out",
            "declared_static_fan_in",
            "measures",
            "responses",
            "rule_ids",
            "fitness_ids",
            "noncompensating",
            "decision_binding",
            "runtime_validation_status",
            "source",
        ],
        "additionalProperties": False,
    }


def feedback_fitness_policy_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    evidence_refs = {
        "type": "array",
        "items": nonempty,
        "uniqueItems": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/feedback-fitness-policy-v1.schema.json",
        "title": "Ranex TDD feedback-fitness policy",
        "type": "object",
        "properties": {
            "schema_version": {"const": "feedback-fitness-policy/v1"},
            "feedback_policy_id": nonempty,
            "version": nonempty,
            "measurement_owner": nonempty,
            "candidate_manifest_owner": nonempty,
            "remediation_owner": nonempty,
            "reference_host_profile_status": {"const": "NOT_ASSESSED"},
            "objectives": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        "objective_id": nonempty,
                        "lane": {"enum": ["FAST_LOOP", "PRE_VERIFICATION"]},
                        "measure": nonempty,
                        "statistic": {"enum": ["p50", "p95"]},
                        "target": nonempty,
                        "window": nonempty,
                        "cadence": nonempty,
                        "rationale": nonempty,
                        "owner_id": nonempty,
                        "result": {"const": "NOT_ASSESSED"},
                        "evidence_refs": evidence_refs,
                    },
                    "required": [
                        "objective_id",
                        "lane",
                        "measure",
                        "statistic",
                        "target",
                        "window",
                        "cadence",
                        "rationale",
                        "owner_id",
                        "result",
                        "evidence_refs",
                    ],
                    "additionalProperties": False,
                },
            },
            "selection": {
                "type": "object",
                "properties": {
                    "manifest_required": {"const": True},
                    "rule": nonempty,
                    "omission_status": {"const": "UNKNOWN_BLOCKING"},
                },
                "required": [
                    "manifest_required",
                    "rule",
                    "omission_status",
                ],
                "additionalProperties": False,
            },
            "sharding": {
                "type": "object",
                "properties": {
                    "rule": nonempty,
                    "recorded_fields": {
                        "type": "array",
                        "minItems": 1,
                        "items": nonempty,
                        "uniqueItems": True,
                    },
                    "determinism_required": {"const": True},
                },
                "required": [
                    "rule",
                    "recorded_fields",
                    "determinism_required",
                ],
                "additionalProperties": False,
            },
            "escalation": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "rule_ids": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "fitness_ids": {
                "type": "array",
                "minItems": 1,
                "items": nonempty,
                "uniqueItems": True,
            },
            "noncompensating": {"const": True},
            "decision_binding": {"type": "object"},
            "runtime_validation_status": {"const": "NOT_ASSESSED"},
            "source": nonempty,
        },
        "required": [
            "schema_version",
            "feedback_policy_id",
            "version",
            "measurement_owner",
            "candidate_manifest_owner",
            "remediation_owner",
            "reference_host_profile_status",
            "objectives",
            "selection",
            "sharding",
            "escalation",
            "rule_ids",
            "fitness_ids",
            "noncompensating",
            "decision_binding",
            "runtime_validation_status",
            "source",
        ],
        "additionalProperties": False,
    }


def topology_exception_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    nonempty_refs = {
        "type": "array",
        "minItems": 1,
        "items": nonempty,
        "uniqueItems": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/common/topology-exception-v1.schema.json",
        "title": "Ranex exact topology exception",
        "type": "object",
        "properties": {
            "schema_version": {"const": "topology-exception/v1"},
            "exception_id": nonempty,
            "exception_class": {
                "enum": [
                    "FOUNDATION_PRIMITIVE",
                    "BOOTSTRAP_COMPOSITION",
                    "HOST_EDGE_ADAPTER",
                    "GENERATED_PROJECTION",
                    "COMPATIBILITY_QUARANTINE",
                ]
            },
            "exact_path": nonempty,
            "rule_ids": nonempty_refs,
            "scope": nonempty,
            "owner_context": nonempty,
            "accountable_human_role": nonempty,
            "rationale": nonempty,
            "allowed_dependency_edges": nonempty_refs,
            "security_data_constraints": nonempty_refs,
            "approval_ref": nonempty,
            "review_expires_at": {
                "type": "string",
                "format": "date-time",
            },
            "required_test_refs": nonempty_refs,
            "removal_criteria": nonempty_refs,
            "status": {"const": "ACTIVE"},
            "source": nonempty,
        },
        "required": [
            "schema_version",
            "exception_id",
            "exception_class",
            "exact_path",
            "rule_ids",
            "scope",
            "owner_context",
            "accountable_human_role",
            "rationale",
            "allowed_dependency_edges",
            "security_data_constraints",
            "approval_ref",
            "review_expires_at",
            "required_test_refs",
            "removal_criteria",
            "status",
            "source",
        ],
        "additionalProperties": False,
    }


def enrich_path_contract(entry: dict[str, Any], context_ids: set[str]) -> dict[str, Any]:
    item = copy.deepcopy(entry)
    owner_context = item["owner_context"]
    responsibility = item["responsibility_class"]
    parameterized_context = "<context>" in item["path_pattern"]
    is_test_root = responsibility == "ALLOWED_TEST_ROOT"
    if is_test_root:
        semantic_owner_kind = "PARAMETERIZED_TEST_SUBJECT_OWNER"
        semantic_owner_context = None
        semantic_owner_resolution = (
            "Each leaf test must declare exactly one context, capability, fixture, or builder owner; "
            "the process_assurance root owner is governance-only."
        )
        human_role = "HUMAN_TEST_POLICY_OWNER"
        data_refs = ["architecture/contracts/contexts.json", "architecture/contracts/test-practices.json"]
        dependency_targets = ["SAME_OR_STRICTER_THAN_PRODUCTION_SUBJECT"]
        dependency_direction = "MIRRORS_PRODUCTION_INWARD_AND_PUBLIC_API_RULES"
        data_classification = "INHERITS_SUBJECT_CLASSIFICATION"
    elif parameterized_context:
        semantic_owner_kind = "PARAMETERIZED_CONTEXT"
        semantic_owner_context = None
        semantic_owner_resolution = "Resolve <context> to exactly one registered context before use."
        human_role = "HUMAN_CONTEXT_OWNER"
        data_refs = ["architecture/contracts/contexts.json", "architecture/contracts/data-ownership.json"]
        dependency_targets = ["RESOLVED_CONTEXT_OWNED_LAYER"]
        dependency_direction = "INWARD_ONLY"
        data_classification = "INHERITS_SUBJECT_CLASSIFICATION"
    elif owner_context in context_ids:
        semantic_owner_kind = "EXACT_CONTEXT"
        semantic_owner_context = owner_context
        semantic_owner_resolution = "The exact registered context is both governance and semantic leaf owner."
        human_role = "HUMAN_CONTEXT_OWNER"
        data_refs = [
            f"architecture/contracts/contexts.json#{owner_context}",
            f"architecture/contracts/data-ownership.json#{owner_context}",
        ]
        layer_targets = {
            "DOMAIN_MODEL": ["ranex.foundation", f"ranex.{owner_context}.domain"],
            "APPLICATION_USE_CASES": [
                "ranex.foundation",
                f"ranex.{owner_context}.domain",
                f"ranex.{owner_context}.application.ports",
                "ranex.<registered_context>.api",
            ],
            "OWNER_DEFINED_PORTS": ["ranex.foundation", f"ranex.{owner_context}.domain"],
            "PUBLIC_API_ONLY_CROSS_CONTEXT_SURFACE": [
                "ranex.foundation",
                f"ranex.{owner_context}.api",
                f"ranex.{owner_context}.domain",
            ],
            "CONTEXT_EXCLUSIVE_ADAPTERS": [
                "ranex.foundation",
                f"ranex.{owner_context}.api",
                f"ranex.{owner_context}.application.ports",
                "ranex.<registered_context>.api",
            ],
        }
        dependency_targets = layer_targets.get(responsibility, ["DECLARED_CONTEXT_LAYER_RULES"])
        dependency_direction = "INWARD_ONLY_AND_CROSS_CONTEXT_API_ONLY"
        data_classification = "INHERITS_SUBJECT_CLASSIFICATION"
    else:
        semantic_owner_kind = "FIXED_CROSS_CONTEXT_OWNER"
        semantic_owner_context = owner_context
        semantic_owner_resolution = "The fixed registry owner governs the cross-context or generated path."
        human_role = "HUMAN_CONFIGURATION_OWNER"
        data_refs = ["architecture/contracts/paths.json", "architecture/contracts/data-ownership.json"]
        dependency_targets = ["DECLARED_PUBLIC_OR_GENERATOR_INPUTS_ONLY"]
        dependency_direction = "REGISTERED_ONLY"
        data_classification = "PUBLIC"

    if responsibility in {"GENERATED_PROJECTION", "EXECUTABLE_SCHEMA"}:
        content_status = "GENERATED"
    elif responsibility == "COMPATIBILITY_QUARANTINE":
        content_status = "LEGACY"
    elif responsibility in {"BOUNDED_CONTEXT_ROOT", "MULTI_CONTEXT_OR_HOST_EDGE_ADAPTER"}:
        content_status = "MIXED"
    else:
        content_status = "MANUAL"
    topology_rule_ids = sorted(
        set(item.get("topology_rule_ids", []))
        | {"ORG-PATH-001", "ORG-OWNERSHIP-001", "ORG-EXEMPTION-001"}
    )
    required_exception = item.get("required_exception_class", "")
    item.update(
        {
            "governance_owner_context": owner_context,
            "semantic_owner_kind": semantic_owner_kind,
            "semantic_owner_context": semantic_owner_context,
            "semantic_owner_resolution": semantic_owner_resolution,
            "accountable_human_role": human_role,
            "required_reviewer_role": "INDEPENDENT_ARCHITECTURE_REVIEWER",
            "applicability": item.get("applicability", "REQUIRED_BY_REGISTERED_SCOPE"),
            "allowed_dependency_targets": dependency_targets,
            "dependency_direction": dependency_direction,
            "data_ownership_refs": data_refs,
            "data_classification": data_classification,
            "content_status": content_status,
            "topology_rule_ids": topology_rule_ids,
            "tdd_rule_ids": sorted(set(item.get("tdd_rule_ids", []))),
            "exception_metadata": {
                "required": bool(required_exception),
                "allowed_classes": [required_exception] if required_exception else [],
                "current_exception_ids": [],
            },
        }
    )
    return item


def test_taxonomy_projection() -> list[dict[str, Any]]:
    shapes = {row["category_id"]: row for row in TEST_LANE_SHAPES}
    return [
        {
            **entry,
            "semantic_leaf_owner_parameter": shapes[entry["category_id"]][
                "semantic_owner_parameter"
            ],
            "mirror_patterns": shapes[entry["category_id"]]["path_patterns"],
            "mirrored_source_layers": shapes[entry["category_id"]][
                "mirrored_source_layers"
            ],
            "shape_rule": shapes[entry["category_id"]]["shape_rule"],
            "root_governance_owner": "process_assurance",
            "root_owner_is_not_leaf_semantic_owner": True,
        }
        for entry in TEST_TAXONOMY
    ]


def build_test_practices(tdd_decision: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "practice_id": rule["rule_id"],
            "requirement": rule["invariant"],
            "enforcement": rule["enforcement"],
            "material": rule["enforcement"] in {"BLOCK", "REQUIRED"},
            "applicability_rule_id": "TDD-DEFAULT-ALL-PRODUCTION-CHANGES",
            "definition_status": rule["definition_status"],
            "runtime_evidence_status": rule["runtime_evidence_status"],
            "source": rule["source"],
        }
        for rule in tdd_decision["rules"]
    ]


def build_test_definition_profile(test_registry: dict[str, Any]) -> dict[str, Any]:
    practice_ids = [entry["practice_id"] for entry in test_registry["entries"]]
    registry_digest = "sha256:" + sha256_bytes(canonical_bytes(test_registry))
    applicable = {
        "result": "APPLICABLE",
        "rule_id": "TDD-DEFAULT-ALL-PRODUCTION-CHANGES",
        "reason": "The definition baseline applies the test contract to every production change; task-specific execution evidence remains unassessed.",
        "evidence_refs": [entry["source"] for entry in test_registry["entries"][:1]],
        "approval_ref": test_registry["decision_bindings"][0]["decision_id"],
    }
    profile = {
        "schema_version": "test-practice-profile/v1",
        "profile_id": "TESTPROFILE-WAVE1-DEFINITION-001",
        "profile_kind": "DEFINITION_BASELINE",
        "profile_version": "1.0.0",
        "policy_version": "1.0.0",
        "registry_id": test_registry["registry_id"],
        "registry_version": test_registry["version"],
        "registry_digest": registry_digest,
        "subject_ref": None,
        "subject_digest": None,
        "created_at": FIXED_TIME,
        "applicability": applicable,
        "material_unknowns": [],
        "test_roots": [entry["root"] for entry in test_registry["taxonomy"]],
        "category_coverage": [
            {
                "category_id": entry["category_id"],
                "root": entry["root"],
                "applicability": {
                    **copy.deepcopy(applicable),
                    "reason": (
                        "The category is registered and must receive a "
                        "task-specific disposition; this definition baseline "
                        "does not require every task to execute the lane."
                    ),
                },
                "task_selection_rule": "RISK_AND_EXACT_SUBJECT_SELECTED",
                "execution_status": "NOT_ASSESSED",
                "evidence_refs": [],
            }
            for entry in test_registry["taxonomy"]
        ],
        "context_layer_mirroring": {
            "policy": "LANE_SPECIFIC_SUBJECT_SHAPES",
            "lane_shapes": copy.deepcopy(TEST_LANE_SHAPES),
            "exceptions": [],
        },
        "architecture_checks": test_registry["topology_rule_ids"],
        "fixture_ownership": {
            "owner_required": True,
            "canonical_root_required": True,
            "classification_required": True,
            "mutation_authority_required": True,
            "hidden_fixture_separation_required": True,
        },
        "fixture_records": [],
        "quarantine_policy": {
            "metadata_required": True,
            "owner_required": True,
            "reason_required": True,
            "expiry_required": True,
            "linked_work_item_required": True,
            "silent_skip_forbidden": True,
        },
        "quarantine_records": [],
        "obsolete_test_deletions": [],
        "unit_lane_policy": {
            "network_forbidden": True,
            "wall_clock_forbidden": True,
            "ambient_randomness_forbidden": True,
            "declared_seed_required": True,
            "injected_clock_required": True,
            "deterministic_id_source_required": True,
        },
        "generated_code_test_exceptions": [],
        "production_path_parity": {
            "same_artifact_contracts_required": True,
            "same_public_apis_required": True,
            "same_composition_root_required": True,
            "test_only_production_conditionals_forbidden": True,
            "bypass_flags_forbidden": True,
            "alternate_policy_or_reducer_paths_forbidden": True,
            "mocks_only_at_declared_external_ports": True,
            "adapter_fake_contract_parity_required": True,
            "real_migrations_and_sqlite_required_for_persistence": True,
            "replay_digest_stability_required": True,
        },
        "failure_mode_matrix": [
            {
                "failure_mode_class": failure_mode,
                "applicability": copy.deepcopy(applicable),
                "required_assertions": EXPECTED_FAILURE_ASSERTIONS,
                "transition_ids": [],
                "precondition_refs": [],
                "fault_input_refs": [],
                "test_lanes": [],
                "owner_id": "",
                "execution_status": "NOT_ASSESSED",
                "evidence_refs": [],
            }
            for failure_mode in FAILURE_MODE_CLASSES
        ],
        "edge_case_partitions": [
            {
                **partition,
                "applicability": copy.deepcopy(applicable),
                "seed_refs": [],
                "corpus_refs": [],
                "property_ids": [],
                "invariant_ids": [],
                "shrinking_reproduction_refs": [],
                "remaining_unknowns": [],
                "execution_status": "NOT_ASSESSED",
                "evidence_refs": [],
            }
            for partition in EDGE_CASE_PARTITIONS
        ],
        "production_evidence_obligations": [
            {
                **copy.deepcopy(obligation),
                "applicability": copy.deepcopy(applicable),
                "execution_status": "NOT_ASSESSED",
                "evidence_refs": [],
            }
            for obligation in PRODUCTION_EVIDENCE_OBLIGATIONS
        ],
        "traceability": {
            "requirement_ids": [],
            "risk_ids": [],
            "practice_ids": practice_ids,
            "transition_ids": [],
        },
        "evidence": {
            "built_artifact_refs": [],
            "composition_identity_refs": [],
            "mock_target_classification_refs": [],
            "negative_test_refs": [],
            "mutation_evidence_refs": [],
            "fault_injection_evidence_refs": [],
            "adapter_fake_contract_refs": [],
            "persistence_migration_refs": [],
            "replay_digest_refs": [],
        },
        "evidence_bindings": [],
        "evidence_scope": "NONE",
        "runtime_evidence_status": "NOT_ASSESSED",
        "derived_result": "NOT_ASSESSED",
        "sealing_eligible": False,
        "digest": "",
    }
    profile["digest"] = digest_value(profile)
    return profile


def build_architecture_rule_assessment_registry(
    topology_registry: dict[str, Any],
    test_registry: dict[str, Any],
    boundary_fitness_registry: dict[str, Any],
    dependency_edge_registry: dict[str, Any],
    coupling_policy: dict[str, Any],
    feedback_policy: dict[str, Any],
    contexts_registry: dict[str, Any],
    paths_registry: dict[str, Any],
) -> dict[str, Any]:
    subject_manifest = {
        "manifest_id": "ARCHITECTURE-RULE-DEFINITION-SUBJECT-001",
        "scope": "DEFINITION_CONTRACT_ONLY",
        "sources": [
            decision_binding(TOPOLOGY_ADR, "ADR-0007"),
            decision_binding(TDD_ADR, "ADR-0008"),
            decision_binding(BOUNDARY_FITNESS_ADR, "ADR-0009"),
            {
                "path": str(ARCH_DOC.relative_to(ROOT)),
                "digest": "sha256:" + sha256_file(ARCH_DOC),
            },
        ],
        "registry_digests": [
            {
                "registry_id": (
                    item.get("registry_id")
                    or item.get("coupling_policy_id")
                    or item.get("feedback_policy_id")
                ),
                "digest": "sha256:" + sha256_bytes(canonical_bytes(item)),
            }
            for item in [
                topology_registry,
                test_registry,
                boundary_fitness_registry,
                dependency_edge_registry,
                coupling_policy,
                feedback_policy,
                contexts_registry,
                paths_registry,
            ]
        ],
    }
    subject_manifest_digest = "sha256:" + sha256_bytes(canonical_bytes(subject_manifest))
    subject = {
        "subject_schema": "architecture-subject/v1",
        "subject_scope": "DEFINITION_CONTRACT_ONLY",
        "subject_ref": "art_" + deterministic_uuid7("architecture-rule-definition-subject"),
        "subject_manifest_digest": subject_manifest_digest,
    }
    subject_digest = "sha256:" + sha256_bytes(canonical_bytes(subject))
    rule_rows = [
        ("ORG", rule, topology_registry["decision_bindings"][0]["path"])
        for rule in topology_registry["entries"]
    ] + [
        ("TDD", rule, test_registry["decision_bindings"][0]["path"])
        for rule in test_registry["entries"]
    ] + [
        (
            "ADR9",
            rule,
            boundary_fitness_registry["decision_binding"]["path"],
        )
        for rule in boundary_fitness_registry["rules"]
    ]
    entries = []
    for family, rule, definition_ref in rule_rows:
        rule_id = (
            rule["practice_id"]
            if family == "TDD"
            else rule["rule_id"]
        )
        record = {
            "schema_version": "architecture-rule-assessment/v1",
            "assessment_id": "rule_assessment_" + deterministic_uuid7(rule_id),
            "rule_id": rule_id,
            "rule_family": family,
            "rule_definition_digest": "sha256:" + sha256_bytes(canonical_bytes(rule)),
            "subject_schema": "architecture-subject/v1",
            "subject_scope": "DEFINITION_CONTRACT_ONLY",
            "subject_ref": subject["subject_ref"],
            "subject_digest": subject_digest,
            "subject_manifest_digest": subject_manifest_digest,
            "runtime_subject_ref": None,
            "runtime_subject_digest": None,
            "rule_owner_id": "human_governor",
            "assessor_id": "UNASSIGNED_WAVE_2",
            "applicability": {
                "result": "UNKNOWN",
                "rule_id": "RUNTIME-SUBJECT-REQUIRED",
                "reason": "The paper rule is defined, but no enacted runtime/source subject exists for applicability evaluation.",
                "evidence_refs": [],
                "approval_ref": "",
            },
            "result": "NOT_ASSESSED",
            "outcome": None,
            "numeric_score": None,
            "definition_evidence_refs": [definition_ref],
            "runtime_evidence_refs": [],
            "recorded_at": FIXED_TIME,
            "observed_at": None,
            "expires_at": None,
            "freshness_status": "NOT_ASSESSED",
            "noncompensating": True,
            "runtime_evidence_status": "NOT_ASSESSED",
            "digest": "",
        }
        record["digest"] = digest_value(record)
        entries.append(record)
    entries.sort(key=lambda item: item["rule_id"])
    return registry(
        "REG-ARCHITECTURE-RULE-ASSESSMENTS-001",
        "1.0.0",
        entries,
        record_schema_path="schemas/common/architecture-rule-assessment-v1.schema.json",
        assessment_subject={
            **subject,
            "subject_digest": subject_digest,
            "manifest": subject_manifest,
        },
        expected_rule_count=47,
        org_rule_count=18,
        tdd_rule_count=19,
        adr9_rule_count=10,
        noncompensating_summary={
            "derivation": "No arithmetic aggregation. PASS is possible only when every applicable rule is EVALUATED/PASS with current exact-subject evidence; any FAIL, UNKNOWN, NOT_ASSESSED, stale, or unsupported N/A blocks.",
            "result": "NOT_ASSESSED",
            "outcome": None,
            "numeric_score": None,
            "pass_authority": False,
            "not_assessed_rule_ids": [entry["rule_id"] for entry in entries],
            "unknown_rule_ids": [],
            "failed_rule_ids": [],
            "not_applicable_rule_ids": [],
        },
        runtime_subject_status="NOT_ASSESSED",
        runtime_enactment_status="NOT_ASSESSED",
    )


def generate_registries() -> dict[str, Any]:
    contexts, zones, decisions, file_patterns = parse_architecture()
    vital_tuples, applicability_rules = parse_vital_profile()
    source_registry_path = ROOT / "docs" / "research" / "engineering-reference-practice-registry.json"
    source_registry = json.loads(read(source_registry_path))
    source_families = [entry["source_family_id"] for entry in source_registry["source_families"]]
    topology_decision = parse_topology_decision()
    tdd_decision = parse_tdd_decision()
    boundary_decision = parse_boundary_fitness_decision()
    context_ids = {context["context_id"] for context in contexts}
    expected_adr9_rule_ids = {
        "ARCH-EDGE-001",
        "ARCH-EDGE-002",
        "ARCH-EDGE-003",
        "ARCH-BOUNDARY-001",
        "ARCH-BOUNDARY-002",
        "ARCH-COUPLING-001",
        "ARCH-COUPLING-002",
        "TDD-FEEDBACK-001",
        "TDD-FEEDBACK-002",
        "ARCH9-NONCOMP-001",
    }
    expected_adr9_fitness_ids = {
        "FF-EDGE-001",
        "FF-EDGE-002",
        "FF-BOUNDARY-001",
        "FF-BOUNDARY-002",
        "FF-COUPLING-001",
        "FF-COUPLING-002",
        "FF-FEEDBACK-001",
        "FF-FEEDBACK-002",
        "FF-ARCH9-NONCOMP-001",
    }
    if {row["rule_id"] for row in boundary_decision["rules"]} != expected_adr9_rule_ids:
        raise ValueError("ADR-0009 rule-set drift")
    if {
        row["fitness_id"] for row in boundary_decision["fitness_obligations"]
    } != expected_adr9_fitness_ids:
        raise ValueError("ADR-0009 fitness-set drift")
    raw_edges = boundary_decision["dependency_graph"]["edges"]
    if len(raw_edges) != 67:
        raise ValueError(f"ADR-0009 edge denominator drift: {len(raw_edges)}")
    edge_ids = [row["edge_id"] for row in raw_edges]
    edge_pairs = {(row["caller"], row["callee"]) for row in raw_edges}
    if len(edge_ids) != len(set(edge_ids)) or len(edge_pairs) != len(raw_edges):
        raise ValueError("ADR-0009 duplicate edge ID or caller/callee pair")
    if any(
        row["caller"] not in context_ids
        or row["callee"] not in context_ids
        or row["caller_owner"] != row["caller"]
        or row["callee_owner"] != row["callee"]
        for row in raw_edges
    ):
        raise ValueError("ADR-0009 unknown context or owner mismatch")
    if dependency_pairs_have_cycle(edge_pairs):
        raise ValueError("ADR-0009 declared dependency graph is cyclic")
    boundary_rows = boundary_decision["boundary_fitness"]["rows"]
    if (
        len(boundary_rows) != 34
        or {row["context_id"] for row in boundary_rows} != context_ids
        or any(row["owner"] != row["context_id"] for row in boundary_rows)
    ):
        raise ValueError("ADR-0009 boundary-fit context denominator drift")
    declared_ge_fan_out = sum(
        row["caller"] == "governed_execution" for row in raw_edges
    )
    declared_ge_fan_in = sum(
        row["callee"] == "governed_execution" for row in raw_edges
    )
    if (declared_ge_fan_out, declared_ge_fan_in) != (10, 3):
        raise ValueError(
            "ADR-0009 governed_execution fan counts drift: "
            f"{declared_ge_fan_out}/{declared_ge_fan_in}"
        )
    edge_entries = [
        {
            "schema_version": "context-dependency-edge/v1",
            **row,
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
        }
        for row in raw_edges
    ]
    boundary_entries = [
        {
            "schema_version": "context-boundary-fit/v1",
            **row,
            "accountable_human_role": "HUMAN_CONTEXT_OWNER",
            "required_reviewer_role": "INDEPENDENT_ARCHITECTURE_REVIEWER",
            "definition_status": "DEFINED",
            "tracer_result": "NOT_ASSESSED",
            "boundary_decision_status": "NOT_ASSESSED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
        }
        for row in boundary_rows
    ]
    boundary_engineering_practice_ids = referenced_practice_ids(
        BOUNDARY_FITNESS_ADR,
        source_registry,
    )
    if not any(decision["decision_id"] == "ADR-0009" for decision in decisions):
        decisions.append(
            {
                "decision_id": "ADR-0009",
                "name": (
                    "ADR-0009: Register Boundary Fit, Dependencies, "
                    "Coupling, and Feedback Fitness"
                ),
                "canonical_position": "See immutable ADR.",
                "status": "ACCEPTED",
                "authority": "HUMAN_GOVERNOR",
                "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
                "source_digest": (
                    "sha256:" + sha256_file(BOUNDARY_FITNESS_ADR)
                ),
            }
        )
    projected_test_roots = [entry["root"].split("/", 1)[1] for entry in TEST_TAXONOMY]
    if tdd_decision["allowed_root_names"] != projected_test_roots:
        raise ValueError(
            "ADR-0008 allowed-test-root drift: "
            f"decision={tdd_decision['allowed_root_names']} projection={projected_test_roots}"
        )

    for context in contexts:
        context.update(
            {
                "topology_rule_set_id": topology_decision["rule_set_id"],
                "canonical_root": f"src/ranex/{context['context_id']}/",
                "public_api_path": f"src/ranex/{context['context_id']}/api/",
                "port_path": f"src/ranex/{context['context_id']}/application/ports/",
                "context_adapter_path": f"src/ranex/{context['context_id']}/adapters/<technology>/",
                "layer_enactment_status": "NOT_ASSESSED",
                "declared_dependency_graph_status": "DEFINED",
                "topology_exception_ids": [],
            }
        )

    context_layer_paths = [
        {
            "path_id": f"PATH-CONTEXT-{slug(context['context_id'])}-{slug(layer)}",
            "owner_context": context["context_id"],
            "path_pattern": f"src/ranex/{context['context_id']}/{layer}/**",
            "responsibility_class": {
                "api": "PUBLIC_API_ONLY_CROSS_CONTEXT_SURFACE",
                "domain": "DOMAIN_MODEL",
                "application": "APPLICATION_USE_CASES",
                "application/ports": "OWNER_DEFINED_PORTS",
                "adapters": "CONTEXT_EXCLUSIVE_ADAPTERS",
            }[layer],
            "applicability": "REQUIRED" if layer == "api" else "CONDITIONAL_ON_ENACTED_BEHAVIOR",
            "topology_rule_ids": ["ORG-PATH-001", "ORG-LAYER-001", "ORG-PUBLIC-001"],
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(TOPOLOGY_ADR.relative_to(ROOT)),
        }
        for context in contexts
        for layer in MODULAR_DDD_LAYERS
    ]
    test_root_paths = [
        {
            "path_id": f"PATH-TEST-{slug(entry['category_id'])}",
            "owner_context": "process_assurance",
            "path_pattern": f"{entry['root']}/**",
            "responsibility_class": "ALLOWED_TEST_ROOT",
            "semantic_owner_resolution": "REQUIRED_FROM_TEST_METADATA",
            "tdd_rule_ids": ["TDD-TAXONOMY-001", "TDD-LANES-001"],
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(TDD_ADR.relative_to(ROOT)),
        }
        for entry in TEST_TAXONOMY
    ]
    special_paths = [
        {
            "path_id": "PATH-BOOTSTRAP-COMPOSITION",
            "owner_context": "configuration_management",
            "path_pattern": "src/ranex/bootstrap/composition.py",
            "responsibility_class": "SOLE_PRODUCT_COMPOSITION_ROOT",
            "topology_rule_ids": ["ORG-COMPOSE-001"],
        },
        {
            "path_id": "PATH-HOST-EDGE-ADAPTERS",
            "owner_context": "configuration_management",
            "path_pattern": "src/ranex/adapters/<boundary>/<technology>/**",
            "responsibility_class": "MULTI_CONTEXT_OR_HOST_EDGE_ADAPTER",
            "required_exception_class": "HOST_EDGE_ADAPTER",
            "semantic_owner_resolution": "REQUIRED_BY_HOST_EDGE_ADAPTER_EXCEPTION",
            "topology_rule_ids": ["ORG-LAYER-001", "ORG-EXEMPTION-001"],
        },
        {
            "path_id": "PATH-CONTEXT-SQLITE-MIGRATIONS",
            "owner_context": "configuration_management",
            "path_pattern": "src/ranex/<context>/adapters/persistence/sqlite/migrations/**",
            "responsibility_class": "CONTEXT_OWNED_MIGRATION",
            "semantic_owner_resolution": "REQUIRED_FROM_CONTEXT_PLACEHOLDER",
            "topology_rule_ids": ["ORG-PERSIST-001", "ORG-MIGRATION-001"],
        },
        {
            "path_id": "PATH-CROSS-CONTEXT-MIGRATION",
            "owner_context": "migration",
            "path_pattern": "src/ranex/migration/**",
            "responsibility_class": "CROSS_CONTEXT_MIGRATION_ORDERING",
            "topology_rule_ids": ["ORG-MIGRATION-001"],
        },
        {
            "path_id": "PATH-GENERATED-ARCHITECTURE",
            "owner_context": "configuration_management",
            "path_pattern": "architecture/generated/**",
            "responsibility_class": "GENERATED_PROJECTION",
            "topology_rule_ids": ["ORG-GENERATED-001"],
        },
        {
            "path_id": "PATH-GENERATED-CONTRACT-BINDINGS",
            "owner_context": "configuration_management",
            "path_pattern": "packages/generated-contracts/**",
            "responsibility_class": "GENERATED_PROJECTION",
            "topology_rule_ids": ["ORG-GENERATED-001"],
        },
        {
            "path_id": "PATH-LEGACY-HERMES",
            "owner_context": "compatibility",
            "path_pattern": "legacy/hermes/**",
            "responsibility_class": "COMPATIBILITY_QUARANTINE",
            "topology_rule_ids": ["ORG-LEGACY-001"],
        },
    ]
    special_paths = [
        {
            **entry,
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(TOPOLOGY_ADR.relative_to(ROOT)),
        }
        for entry in special_paths
    ]
    topology_engineering_practice_ids = referenced_practice_ids(TOPOLOGY_ADR, source_registry)
    tdd_engineering_practice_ids = referenced_practice_ids(TDD_ADR, source_registry)

    states = build_state_registry()
    dependency_edge_registry = registry(
        "REG-CONTEXT-DEPENDENCY-EDGES-001",
        "1.0.0",
        edge_entries,
        dependency_graph_id=boundary_decision["dependency_graph"][
            "dependency_graph_id"
        ],
        default_policy=boundary_decision["dependency_graph"]["default_policy"],
        expected_edge_count=67,
        declared_cycle_result="PASS",
        actual_import_scan_status="NOT_ASSESSED",
        actual_import_pairs=[],
        actual_subset_result="NOT_ASSESSED",
        actual_cycle_result="NOT_ASSESSED",
        record_schema_path=(
            "schemas/common/context-dependency-edge-v1.schema.json"
        ),
        decision_binding=boundary_decision["decision_binding"],
        runtime_validation_status="NOT_ASSESSED",
    )
    boundary_fitness_registry = registry(
        "REG-CONTEXT-BOUNDARY-FITNESS-001",
        "1.0.0",
        boundary_entries,
        boundary_fit_set_id=boundary_decision["boundary_fitness"][
            "boundary_fit_set_id"
        ],
        expected_context_count=34,
        rule_set_id=boundary_decision["rule_set_id"],
        rules=boundary_decision["rules"],
        fitness_obligations=boundary_decision["fitness_obligations"],
        engineering_practice_ids=boundary_engineering_practice_ids,
        record_schema_path="schemas/common/context-boundary-fit-v1.schema.json",
        decision_binding=boundary_decision["decision_binding"],
        runtime_validation_status="NOT_ASSESSED",
    )
    raw_coupling = boundary_decision["coupling_policy"]
    coupling_policy = {
        "schema_version": "context-coupling-policy/v1",
        "coupling_policy_id": raw_coupling["coupling_policy_id"],
        "version": "1.0.0",
        "subject_context": raw_coupling["subject_context"],
        "measurement_owner": "process_assurance",
        "decision_owner": "human_governor",
        "reference_windows": [
            "first clean source tracer",
            "each candidate",
            "rolling 20 accepted changes",
            "rolling 30 authority transitions",
            "rolling 3 releases",
        ],
        "declared_static_fan_out": declared_ge_fan_out,
        "declared_static_fan_in": declared_ge_fan_in,
        "measures": [
            {
                **row,
                "rationale": (
                    "This falsification measure triggers review; it is not a "
                    "maturity score or automatic split decision."
                ),
                "owner_id": "process_assurance",
                "result": "NOT_ASSESSED",
                "evidence_refs": [],
            }
            for row in raw_coupling["measures"]
        ],
        "responses": raw_coupling["responses"],
        "rule_ids": [
            "ARCH-COUPLING-001",
            "ARCH-COUPLING-002",
            "ARCH9-NONCOMP-001",
        ],
        "fitness_ids": [
            "FF-COUPLING-001",
            "FF-COUPLING-002",
            "FF-ARCH9-NONCOMP-001",
        ],
        "noncompensating": raw_coupling["noncompensating"],
        "decision_binding": boundary_decision["decision_binding"],
        "runtime_validation_status": "NOT_ASSESSED",
        "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
    }
    raw_feedback = boundary_decision["feedback_policy"]
    feedback_policy = {
        "schema_version": "feedback-fitness-policy/v1",
        "feedback_policy_id": raw_feedback["feedback_policy_id"],
        "version": "1.0.0",
        "measurement_owner": "process_assurance",
        "candidate_manifest_owner": "configuration_management",
        "remediation_owner": "HUMAN_TECHNICAL_OWNER",
        "reference_host_profile_status": "NOT_ASSESSED",
        "objectives": [
            {
                **row,
                "rationale": (
                    "Bound feedback latency without omitting, suppressing, "
                    "or compensating for a required result."
                ),
                "owner_id": "process_assurance",
                "result": "NOT_ASSESSED",
                "evidence_refs": [],
            }
            for row in raw_feedback["objectives"]
        ],
        "selection": raw_feedback["selection"],
        "sharding": raw_feedback["sharding"],
        "escalation": raw_feedback["escalation"],
        "rule_ids": [
            "TDD-FEEDBACK-001",
            "TDD-FEEDBACK-002",
            "ARCH9-NONCOMP-001",
        ],
        "fitness_ids": [
            "FF-FEEDBACK-001",
            "FF-FEEDBACK-002",
            "FF-ARCH9-NONCOMP-001",
        ],
        "noncompensating": raw_feedback["noncompensating"],
        "decision_binding": boundary_decision["decision_binding"],
        "runtime_validation_status": "NOT_ASSESSED",
        "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
    }
    registries: dict[str, Any] = {
        "identities.json": registry("REG-IDENTITIES-001", "1.0.0", [{"type": key, "prefix": value, "generation": "UUIDV7"} for key, value in IDENTITY_PREFIXES.items()]),
        "states.json": states,
        "contexts.json": registry(
            "REG-CONTEXTS-001",
            "1.1.0",
            contexts,
            context_count=len(contexts),
            topology_rule_set_id=topology_decision["rule_set_id"],
            topology_decision_binding=topology_decision["decision_binding"],
            canonical_context_root_template="src/ranex/<context>/",
            port_path_template="src/ranex/<context>/application/ports/",
            context_adapter_path_template="src/ranex/<context>/adapters/<technology>/",
            host_edge_adapter_path_template="src/ranex/adapters/<boundary>/<technology>/",
            topology_exceptions=[],
            runtime_enactment_status="NOT_ASSESSED",
        ),
        "data-ownership.json": registry("REG-DATA-OWNERSHIP-001", "1.0.0", [{"owner_context": c["context_id"], "owned_data": c["owns"], "persistence_authority": c["persistence_authority"], "source": c["source"]} for c in contexts]),
        "paths.json": registry(
            "REG-PATHS-001",
            "1.1.0",
            file_patterns
            + [
                {
                    "path_id": f"PATH-CONTEXT-{slug(context['context_id'])}",
                    "owner_context": context["context_id"],
                    "path_pattern": f"src/ranex/{context['context_id']}/**",
                    "responsibility_class": "BOUNDED_CONTEXT_ROOT",
                    "definition_status": "DEFINED",
                    "runtime_validation_status": "NOT_ASSESSED",
                    "source": context["source"],
                }
                for context in contexts
            ]
            + context_layer_paths
            + test_root_paths
            + special_paths
            + [
                {"path_id": "PATH-CONTRACT-REGISTRIES", "owner_context": "configuration_management", "path_pattern": "architecture/contracts/**", "responsibility_class": "CANONICAL_REGISTRY", "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/AI_ARTIFACT_CONTRACTS.md#12"},
                {"path_id": "PATH-CONTRACT-SCHEMAS", "owner_context": "configuration_management", "path_pattern": "schemas/**", "responsibility_class": "EXECUTABLE_SCHEMA", "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/AI_ARTIFACT_CONTRACTS.md#12"},
                {"path_id": "PATH-CONTRACT-ASSESSMENTS", "owner_context": "process_assurance", "path_pattern": "docs/architecture/assessments/**", "responsibility_class": "CAPABILITY_ASSESSMENT", "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/SDLC_CONTROL_CATALOG.md#3"},
            ],
            topology_rule_set_id=topology_decision["rule_set_id"],
            tdd_rule_set_id=tdd_decision["rule_set_id"],
            topology_decision_binding=topology_decision["decision_binding"],
            tdd_decision_binding=tdd_decision["decision_binding"],
            path_enactment_status="NOT_ASSESSED",
        ),
        "topology-rules.json": registry(
            "REG-TOPOLOGY-RULES-001",
            "1.0.0",
            topology_decision["rules"],
            rule_set_id=topology_decision["rule_set_id"],
            decision_bindings=[
                topology_decision["decision_binding"],
                tdd_decision["decision_binding"],
                boundary_decision["decision_binding"],
            ],
            exception_classes=topology_decision["exception_classes"],
            exceptions=[],
            exception_record_schema_path=(
                "schemas/common/topology-exception-v1.schema.json"
            ),
            fitness_refs=topology_decision["fitness_refs"],
            layout_profile={
                "canonical_context_root": "src/ranex/<context>/",
                "required_metadata": ["__init__.py", "README.md", "contract.yaml"],
                "layer_paths": [
                    {
                        "path": layer,
                        "applicability": "REQUIRED"
                        if layer == "api"
                        else "CONDITIONAL_ON_ENACTED_BEHAVIOR",
                    }
                    for layer in MODULAR_DDD_LAYERS
                ],
                "ports_path": "src/ranex/<context>/application/ports/",
                "sibling_ports_forbidden": True,
                "context_adapter_path": "src/ranex/<context>/adapters/<technology>/",
                "host_edge_adapter_path": "src/ranex/adapters/<boundary>/<technology>/",
                "host_edge_adapter_exception_class": "HOST_EDGE_ADAPTER",
                "composition_root": "src/ranex/bootstrap/composition.py",
                "public_api_only_cross_context_imports": True,
                "acyclic_declared_and_actual_graphs": True,
                "tiny_context_policy": {
                    "empty_optional_directories_forbidden": True,
                    "optional_layer_omission_requires_non_applicability": True,
                    "topology_rule_exemption_still_requires_registered_exception": True,
                    "current_exemption_count": 0,
                },
            },
            dependency_graph={
                "declaration_status": "DEFINED",
                "registry_ref": "architecture/contracts/context-dependency-edges.json",
                "registry_id": dependency_edge_registry["registry_id"],
                "registry_digest": (
                    "sha256:"
                    + sha256_bytes(canonical_bytes(dependency_edge_registry))
                ),
                "declared_edge_count": 67,
                "edges": [],
                "default_cross_context_policy": "DENY_UNLESS_EXACT_EDGE_REGISTERED",
                "source_scan_status": "NOT_ASSESSED",
                "private_import_result": "NOT_ASSESSED",
                "cycle_result": "NOT_ASSESSED",
            },
            source_dependency_graph_status="NOT_ASSESSED",
            runtime_enactment_status="NOT_ASSESSED",
        ),
        "context-dependency-edges.json": dependency_edge_registry,
        "context-boundary-fitness.json": boundary_fitness_registry,
        "context-coupling-policy.json": coupling_policy,
        "feedback-fitness.json": feedback_policy,
        "effects.json": registry(
            "REG-EFFECTS-001",
            "1.0.0",
            [
                {"effect_family_id": f"EFFECT-{slug(name)}", "name": name, "authority_owner": "governed_execution", "adapter_owner": adapter, "reconciliation_required_for_unknown_outcome": True, "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#19"}
                for name, adapter in [
                    ("GIT", "workspace"),
                    ("GITHUB", "delivery"),
                    ("MESSAGING", "delivery"),
                    ("PROVIDER", "routing"),
                    ("FILESYSTEM", "workspace"),
                    ("DATABASE", "owning_context_repository"),
                ]
            ],
        ),
        "events.json": registry(
            "REG-EVENTS-001",
            "1.0.0",
            [
                {"event_id": f"EVENT-{slug(event)}", "event_name": event, "owner_context": owner, "schema_status": "DEFINED_NAME_ONLY", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#17"}
                for owner, events in {
                    "governed_execution": ["RunCreated", "WorkflowPinned", "PacketBound", "RunMarkedReady", "ActivityRequested", "AuthorizationEvaluated", "ActivityDispatched", "ActivityResolved", "EvidenceSnapshotBound", "GateEvaluated", "HumanDecisionSnapshotBound", "PermitIssued", "PermitConsumed", "EffectIntentRecorded", "EffectDispatched", "EffectResolved", "EffectOutcomeMarkedUnknown", "EffectReconciled", "RunBlocked", "RunUnblocked", "RunCancelled", "RunSucceeded", "RunFailed", "PolicyChangeBlockedRun", "SourceDivergenceDetected"],
                    "work_management": ["WorkItemCreated", "WorkItemClassified", "RiskLaneBound", "OutcomeRequirementRefsBound", "WorkItemTransitioned", "WorkItemBlocked", "WorkItemUnblocked", "WorkItemCancelled", "RunRequestedForWorkItem", "RunEvidenceLinked", "ReleaseEvidenceLinked", "OperationalEvidenceLinked", "OutcomeDecisionLinked", "FollowUpWorkLinked", "WorkItemClosed"],
                }.items()
                for event in events
            ],
        ),
        "decisions.json": registry("REG-DECISIONS-001", "1.0.0", decisions),
        "applicability-rules.json": registry("APPLICABILITY-SDLC-001", "1.1.0", [{"rule_id": key, "meaning": value} for key, value in applicability_rules.items()]),
        "priority-rules.json": registry("PRIORITY-SDLC-001", "1.0.0", [{"tier": tier, "precedence": index, "trigger_codes": codes} for index, (tier, codes) in enumerate(PRIORITY_TRIGGERS.items())]),
        "vital-profile.json": registry("VITAL-SDLC-001", "1.1.0", vital_tuples, tuple_count=len(vital_tuples), domain_count=len({row["domain_id"] for row in vital_tuples})),
        "engineering-practices.json": registry(
            "REG-ENGINEERING-PRACTICES-001",
            "1.0.0",
            [
                {
                    **practice,
                    "source_binding_status": "STABLE_SOURCE_RECONCILED_NOT_APPLIED",
                    "application_status": "NOT_ASSESSED",
                    "runtime_validation_status": "NOT_ASSESSED",
                }
                for practice in source_registry["practices"]
            ],
            source_families=source_registry["source_families"],
            required_source_family_count=len(source_families),
            stable_practice_id_count=len(source_registry["practices"]),
            reference_map_digest="sha256:" + sha256_file(REFERENCE_MAP),
            source_registry_path=str(source_registry_path.relative_to(ROOT)),
            source_registry_digest="sha256:" + sha256_file(source_registry_path),
            source_corpus=source_registry["corpus"],
            source_profile_rule=source_registry["profile_rule"],
            decision_application_bindings=[
                {
                    "decision_id": "ADR-0007",
                    "decision_digest": topology_decision["decision_binding"]["digest"],
                    "practice_ids": topology_engineering_practice_ids,
                    "application_status": "DEFINED_NOT_RUNTIME_ASSESSED",
                },
                {
                    "decision_id": "ADR-0008",
                    "decision_digest": tdd_decision["decision_binding"]["digest"],
                    "practice_ids": tdd_engineering_practice_ids,
                    "application_status": "DEFINED_NOT_RUNTIME_ASSESSED",
                },
                {
                    "decision_id": "ADR-0009",
                    "decision_digest": boundary_decision["decision_binding"][
                        "digest"
                    ],
                    "practice_ids": boundary_engineering_practice_ids,
                    "application_status": "DEFINED_NOT_RUNTIME_ASSESSED",
                },
            ],
        ),
    }

    registries["paths.json"]["entries"] = [
        enrich_path_contract(entry, {context["context_id"] for context in contexts})
        for entry in registries["paths.json"]["entries"]
    ]
    registries["paths.json"]["path_contract_schema"] = "schemas/common/path-contract-v1.schema.json"

    practice_registry_unsigned = registries["engineering-practices.json"]
    practice_digest = "sha256:" + sha256_bytes(canonical_bytes(practice_registry_unsigned))
    profile = {
        "schema_version": "engineering-practice-profile/v1",
        "profile_id": "ENGPROFILE-WAVE1-UNRESOLVED-001",
        "registry_version": "1.0.0",
        "registry_digest": practice_digest,
        "source_coverage": [{"source_family_id": family, "applicability": "UNKNOWN", "reason": "Stable practice IDs are imported; applicability and behavioral evidence remain unresolved.", "evidence_refs": []} for family in source_families],
        "sealing_eligible": False,
        "digest": "",
    }
    profile["digest"] = digest_value(profile)
    registries["engineering-practice-profiles.json"] = registry("REG-ENGINEERING-PRACTICE-PROFILES-001", "1.0.0", [profile])

    test_registry = registry(
        "REG-TEST-PRACTICES-001",
        "1.0.0",
        build_test_practices(tdd_decision),
        rule_set_id=tdd_decision["rule_set_id"],
        taxonomy=test_taxonomy_projection(),
        decision_bindings=[
            tdd_decision["decision_binding"],
            topology_decision["decision_binding"],
            boundary_decision["decision_binding"],
        ],
        topology_rule_ids=[rule["rule_id"] for rule in topology_decision["rules"]],
        exception_classes=tdd_decision["exception_classes"],
        exceptions=[],
        fitness_refs=tdd_decision["fitness_refs"],
        feedback_fitness_refs=[
            "FF-FEEDBACK-001",
            "FF-FEEDBACK-002",
            "FF-ARCH9-NONCOMP-001",
        ],
        engineering_practice_ids=tdd_engineering_practice_ids,
        failure_mode_classes=FAILURE_MODE_CLASSES,
        expected_failure_assertions=EXPECTED_FAILURE_ASSERTIONS,
        edge_case_partition_policy=EDGE_CASE_PARTITIONS,
        production_evidence_obligation_policy=(
            PRODUCTION_EVIDENCE_OBLIGATIONS
        ),
        deprecated_root_migrations=[
            {
                "deprecated_root": "tests/persistence",
                "replacement_roots": ["tests/integration/<context>", "tests/migration/<context>"],
            },
            {
                "deprecated_root": "tests/crash",
                "replacement_roots": ["tests/resilience"],
            },
        ],
        profile_schema_path="schemas/common/test-practice-profile-v1.schema.json",
        runtime_enactment_status="NOT_ASSESSED",
    )
    registries["test-practices.json"] = test_registry
    test_definition_profile = build_test_definition_profile(test_registry)
    registries["test-practice-profiles.json"] = registry(
        "REG-TEST-PRACTICE-PROFILES-001",
        "1.0.0",
        [test_definition_profile],
        definition_profile_count=1,
        runtime_profile_count=0,
        runtime_enactment_status="NOT_ASSESSED",
    )
    registries["architecture-rule-assessments.json"] = build_architecture_rule_assessment_registry(
        registries["topology-rules.json"],
        registries["test-practices.json"],
        registries["context-boundary-fitness.json"],
        registries["context-dependency-edges.json"],
        registries["context-coupling-policy.json"],
        registries["feedback-fitness.json"],
        registries["contexts.json"],
        registries["paths.json"],
    )

    artifact_entries = []
    for template_name, (schema_path, producer) in ARTIFACT_SCHEMAS.items():
        template = yaml.safe_load(read(TEMPLATES / template_name))
        artifact_entries.append(
            {
                "artifact_type": template["artifact_type"],
                "template_path": f"docs/architecture/templates/{template_name}",
                "schema_path": f"schemas/{schema_path}",
                "canonical_producer": producer,
                "authority_status": "DEFINED",
                "runtime_producer_validation_status": "NOT_ASSESSED",
            }
        )
    registries["artifact-types.json"] = registry("REG-ARTIFACT-TYPES-001", "1.0.0", artifact_entries, artifact_type_count=len(artifact_entries))

    elements: list[dict[str, Any]] = []
    for context in contexts:
        elements.append({"element_id": f"CTX-{slug(context['context_id'])}", "kind": "BOUNDED_CONTEXT", "name": context["context_id"], "owner_contexts": [context["context_id"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": context["source"]})
        elements.append({"element_id": f"API-{slug(context['context_id'])}", "kind": "PUBLIC_BOUNDARY", "name": context["public_boundary"], "owner_contexts": [context["context_id"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": context["source"]})
    for zone in zones:
        elements.append({"element_id": zone["zone_id"], "kind": "CAPABILITY_ZONE", "name": zone["name"], "owner_contexts": zone["owners"], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": zone["source"]})
    for axis in states["entries"]:
        elements.append({"element_id": f"STATE-AXIS-{slug(axis['axis_id'])}", "kind": "STATE_AXIS", "name": axis["axis_id"], "owner_contexts": [axis["owner_context"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": axis["source"]})
        for value in axis["values"]:
            elements.append({"element_id": f"STATE-{slug(axis['axis_id'])}-{value}", "kind": "STATE_VALUE", "name": value, "owner_contexts": [axis["owner_context"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": axis["source"]})
    for event in registries["events.json"]["entries"]:
        elements.append({"element_id": event["event_id"], "kind": "EVENT", "name": event["event_name"], "owner_contexts": [event["owner_context"]], "definition_status": event["schema_status"], "runtime_validation_status": "NOT_ASSESSED", "source": event["source"]})
    for effect in registries["effects.json"]["entries"]:
        elements.append({"element_id": effect["effect_family_id"], "kind": "EFFECT_FAMILY", "name": effect["name"], "owner_contexts": [effect["authority_owner"], effect["adapter_owner"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": effect["source"]})
    for item in registries["paths.json"]["entries"]:
        elements.append({"element_id": item["path_id"], "kind": "FILE_PATTERN", "name": item["path_pattern"], "owner_contexts": [item["owner_context"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": item["source"]})
    for item in registries["topology-rules.json"]["entries"]:
        elements.append({"element_id": item["rule_id"], "kind": "TOPOLOGY_RULE", "name": item["invariant"], "owner_contexts": ["configuration_management"], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": item["source"]})
    for item in registries["test-practices.json"]["entries"]:
        elements.append({"element_id": item["practice_id"], "kind": "TEST_PRACTICE", "name": item["requirement"], "owner_contexts": ["process_assurance"], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": item["source"]})
    for item in registries["test-practices.json"]["taxonomy"]:
        elements.append({"element_id": f"TEST-CATEGORY-{item['category_id']}", "kind": "TEST_CATEGORY", "name": item["root"], "owner_contexts": ["process_assurance"], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": str(TDD_ADR.relative_to(ROOT))})
    elements.append(
        {
            "element_id": dependency_edge_registry["dependency_graph_id"],
            "kind": "CONTEXT_DEPENDENCY_GRAPH",
            "name": "Declared cross-context public-API dependency graph",
            "owner_contexts": ["configuration_management"],
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
        }
    )
    for item in dependency_edge_registry["entries"]:
        elements.append(
            {
                "element_id": item["edge_id"],
                "kind": "CONTEXT_DEPENDENCY_EDGE",
                "name": f"{item['caller']} -> {item['callee']}.api",
                "owner_contexts": [item["caller"], item["callee"]],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": item["source"],
            }
        )
    elements.append(
        {
            "element_id": boundary_fitness_registry["boundary_fit_set_id"],
            "kind": "CONTEXT_BOUNDARY_FIT_SET",
            "name": "Exact canonical context boundary-fit hypotheses",
            "owner_contexts": ["configuration_management"],
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
        }
    )
    for item in boundary_fitness_registry["entries"]:
        elements.append(
            {
                "element_id": f"BOUNDARYFIT-{slug(item['context_id'])}",
                "kind": "CONTEXT_BOUNDARY_FIT",
                "name": item["context_id"],
                "owner_contexts": [item["owner"]],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": item["source"],
            }
        )
    elements.extend(
        [
            {
                "element_id": boundary_fitness_registry["rule_set_id"],
                "kind": "BOUNDARY_FITNESS_RULE_SET",
                "name": "Boundary, dependency, coupling, and feedback rule set",
                "owner_contexts": ["configuration_management"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": str(BOUNDARY_FITNESS_ADR.relative_to(ROOT)),
            },
            {
                "element_id": coupling_policy["coupling_policy_id"],
                "kind": "COUPLING_POLICY",
                "name": "governed_execution coupling policy",
                "owner_contexts": ["process_assurance"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": coupling_policy["source"],
            },
            {
                "element_id": feedback_policy["feedback_policy_id"],
                "kind": "FEEDBACK_FITNESS_POLICY",
                "name": "TDD feedback fitness policy",
                "owner_contexts": ["process_assurance"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": feedback_policy["source"],
            },
        ]
    )
    for item in coupling_policy["measures"]:
        elements.append(
            {
                "element_id": item["measure_id"],
                "kind": "COUPLING_MEASURE",
                "name": item["definition"],
                "owner_contexts": [item["owner_id"]],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": coupling_policy["source"],
            }
        )
    for item in feedback_policy["objectives"]:
        elements.append(
            {
                "element_id": item["objective_id"],
                "kind": "FEEDBACK_OBJECTIVE",
                "name": item["measure"],
                "owner_contexts": [item["owner_id"]],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": feedback_policy["source"],
            }
        )
    for item in boundary_fitness_registry["rules"]:
        elements.append(
            {
                "element_id": item["rule_id"],
                "kind": "BOUNDARY_FITNESS_RULE",
                "name": item["invariant"],
                "owner_contexts": ["configuration_management"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": item["source"],
            }
        )
    for item in boundary_fitness_registry["fitness_obligations"]:
        elements.append(
            {
                "element_id": item["fitness_id"],
                "kind": "FITNESS_OBLIGATION",
                "name": item["required_evidence"],
                "owner_contexts": ["process_assurance"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": item["source"],
            }
        )
    for item in artifact_entries:
        elements.append({"element_id": f"ARTIFACT-{slug(item['artifact_type'])}", "kind": "ARTIFACT_TYPE", "name": item["artifact_type"], "owner_contexts": [item["canonical_producer"]], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": item["template_path"]})
    for item in decisions:
        elements.append({"element_id": item["decision_id"], "kind": "DECISION", "name": item["name"], "owner_contexts": ["human_governor"], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": item["source"]})
    architecture_practice_profile = json.loads(
        read(ARCHITECTURE_PRACTICE_PROFILE)
    )
    architecture_practice_profile_digest = (
        "sha256:" + sha256_file(ARCHITECTURE_PRACTICE_PROFILE)
    )
    element_ids = {item["element_id"] for item in elements}
    explicitly_mapped_ids = {
        element_id
        for application in architecture_practice_profile[
            "practice_applications"
        ]
        for element_id in application["architecture_element_ids"]
    }
    unknown_mapped_ids = explicitly_mapped_ids - element_ids
    if unknown_mapped_ids:
        raise ValueError(
            "Architecture practice profile references unknown elements: "
            + ",".join(sorted(unknown_mapped_ids))
        )
    applications_by_element: dict[str, list[dict[str, Any]]] = {
        element_id: [] for element_id in element_ids
    }
    for application in architecture_practice_profile["practice_applications"]:
        for element_id in application["architecture_element_ids"]:
            applications_by_element[element_id].append(
                {
                    "profile_id": architecture_practice_profile["profile_id"],
                    "practice_id": application["practice_id"],
                    "disposition": application["disposition"],
                    "design_application_status": application[
                        "design_application_status"
                    ],
                    "material_unknown": application["material_unknown"],
                    "runtime_enactment_status": application[
                        "runtime_enactment_status"
                    ],
                }
            )
    for item in elements:
        applications = sorted(
            applications_by_element[item["element_id"]],
            key=lambda row: row["practice_id"],
        )
        item.update(
            {
                "engineering_practice_profile_id": (
                    architecture_practice_profile["profile_id"]
                ),
                "engineering_practice_profile_digest": (
                    architecture_practice_profile_digest
                ),
                "engineering_practice_application_status": (
                    "EXPLICIT_MAPPINGS_PRESENT"
                    if applications
                    else "NO_EXPLICIT_MAPPING"
                ),
                "engineering_practice_applications": applications,
            }
        )
    registries["architecture-elements.json"] = registry(
        "REG-ARCHITECTURE-ELEMENTS-001",
        "1.0.0",
        elements,
        engineering_practice_profile_binding={
            "path": str(ARCHITECTURE_PRACTICE_PROFILE.relative_to(ROOT)),
            "profile_id": architecture_practice_profile["profile_id"],
            "digest": architecture_practice_profile_digest,
            "mapping_policy": "EXPLICIT_ELEMENT_IDS_ONLY_NO_TRANSITIVE_INFERENCE",
            "sealing_eligible": architecture_practice_profile["summary"][
                "sealing_eligible"
            ],
            "runtime_claim": architecture_practice_profile["runtime_claim"],
        },
        counts_by_kind={kind: sum(1 for item in elements if item["kind"] == kind) for kind in sorted({item["kind"] for item in elements})},
    )

    for filename, content in registries.items():
        write_json(CONTRACTS / filename, content)
    return registries


def generate_schemas(registries: dict[str, Any]) -> None:
    schemas = {**common_schemas(), **build_subject_schemas()}
    schemas["common/test-practice-profile-v1.schema.json"] = test_practice_profile_schema()
    schemas["common/architecture-rule-assessment-v1.schema.json"] = architecture_rule_assessment_schema()
    schemas[
        "common/architecture-practice-application-profile-v1.schema.json"
    ] = architecture_practice_application_profile_schema()
    schemas["common/path-contract-v1.schema.json"] = path_contract_schema()
    schemas[
        "common/context-dependency-edge-v1.schema.json"
    ] = context_dependency_edge_schema()
    schemas[
        "common/context-boundary-fit-v1.schema.json"
    ] = context_boundary_fit_schema()
    schemas[
        "common/context-coupling-policy-v1.schema.json"
    ] = context_coupling_policy_schema()
    schemas[
        "common/feedback-fitness-policy-v1.schema.json"
    ] = feedback_fitness_policy_schema()
    schemas["common/topology-exception-v1.schema.json"] = (
        topology_exception_schema()
    )
    for template_name, (relative_schema, producer) in ARTIFACT_SCHEMAS.items():
        template = yaml.safe_load(read(TEMPLATES / template_name))
        artifact_type = template["artifact_type"]
        schema = infer_schema(template, "", artifact_type)
        schema.update(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": f"https://schemas.ranex.dev/{relative_schema}",
                "title": artifact_type,
                "x-ranex-template": f"docs/architecture/templates/{template_name}",
                "x-ranex-canonical-producer": producer,
                "x-ranex-runtime-semantics": "scripts/architecture/validate_contracts.py",
            }
        )
        schemas[relative_schema] = schema

    for relative, schema in schemas.items():
        write_json(SCHEMAS / relative, schema)

    entries = []
    for relative in sorted(schemas):
        entries.append(
            {
                "schema_id": schemas[relative]["$id"],
                "path": f"schemas/{relative}",
                "digest": "sha256:" + sha256_file(SCHEMAS / relative),
                "draft": "2020-12",
                "status": "ACTIVE_DOCUMENTATION_CONTRACT",
            }
        )
    write_json(CONTRACTS / "schema-registry.json", registry("REG-SCHEMAS-001", "1.0.0", entries, schema_count=len(entries)))


def generate_fixtures(registries: dict[str, Any]) -> None:
    golden_dir = SCHEMAS / "fixtures" / "canonical"
    negative_dir = SCHEMAS / "fixtures" / "negative"
    semantic_dir = SCHEMAS / "fixtures" / "semantic"
    for directory in (golden_dir, negative_dir, semantic_dir):
        if directory.exists():
            for path in directory.iterdir():
                if path.is_file():
                    path.unlink()
    golden_values = [
        {"fixture_id": "RFC8785-ORDER-UTF8-001", "value": {"z": 3, "a": "é", "nested": {"b": True, "a": None}, "array": [3, 2, 1]}},
        {"fixture_id": "RFC8785-DIGEST-EXCLUSION-001", "value": {"artifact_type": "fixture", "schema_version": "1", "subject_digest": "sha256:" + "1" * 64}},
    ]
    fixtures = []
    for item in golden_values:
        canonical = canonical_bytes(item["value"])
        fixtures.append(
            {
                "fixture_id": item["fixture_id"],
                "input": item["value"],
                "canonical_utf8": canonical.decode("utf-8"),
                "sha256": sha256_bytes(canonical),
            }
        )
    write_json(golden_dir / "rfc8785-golden.json", {"algorithm": "RFC8785+SHA-256", "fixtures": fixtures})
    (negative_dir / "duplicate-key.yaml").parent.mkdir(parents=True, exist_ok=True)
    (negative_dir / "duplicate-key.yaml").write_text(
        "# expected_error: DUPLICATE_KEY\nschema_version: \"1\"\nartifact_type: work_intake\nartifact_type: forged_override\n",
        encoding="utf-8",
    )
    write_json(
        negative_dir / "unknown-field.json",
        {"expected_error": "UNKNOWN_FIELD", "schema_path": "schemas/work/work-intake-v1.schema.json", "instance": {**yaml.safe_load(read(TEMPLATES / "WORK_INTAKE.yaml")), "forged_unknown_field": True}},
    )
    write_json(
        negative_dir / "forged-digest.json",
        {"expected_error": "DIGEST_MISMATCH", "instance": {"artifact_type": "fixture", "schema_version": "1", "claim": "unchanged", "digest": "sha256:" + "0" * 64}},
    )
    write_json(
        negative_dir / "permit-reuse.json",
        {"expected_error": "PERMIT_REUSED", "permit_id": "permit_" + deterministic_uuid7("fixture-permit"), "permit_status": "CONSUMED", "consumption_transition_ids": ["transition_" + deterministic_uuid7("consume-1"), "transition_" + deterministic_uuid7("consume-2")]},
    )
    write_json(
        negative_dir / "subject-mismatch.json",
        {"expected_error": "SUBJECT_MISMATCH", "parent": {"subject_ref": "art_" + deterministic_uuid7("subject-parent"), "subject_digest": "sha256:" + "1" * 64}, "child": {"subject_ref": "art_" + deterministic_uuid7("subject-parent"), "subject_digest": "sha256:" + "2" * 64}},
    )
    write_json(
        negative_dir / "stale-subject.json",
        {"expected_error": "STALE_SUBJECT", "expected_run_aggregate_version": 7, "observed_run_aggregate_version": 8},
    )
    test_profile = registries["test-practice-profiles.json"]["entries"][0]
    happy_path_only = copy.deepcopy(test_profile)
    happy_path_only["profile_id"] = "TESTPROFILE-NEGATIVE-HAPPY-PATH-ONLY"
    happy_path_only["category_coverage"] = [
        row for row in happy_path_only["category_coverage"] if row["category_id"] == "E2E"
    ]
    happy_path_only["test_roots"] = ["tests/e2e"]
    happy_path_only["failure_mode_matrix"] = happy_path_only["failure_mode_matrix"][:1]
    write_json(
        negative_dir / "happy-path-only-test-profile.json",
        {"expected_error": "TEST_PROFILE_HAPPY_PATH_ONLY", "instance": happy_path_only},
    )

    material_unknown = copy.deepcopy(test_profile)
    material_unknown["profile_id"] = "TESTPROFILE-NEGATIVE-MATERIAL-UNKNOWN"
    material_unknown["material_unknowns"] = ["Unresolved authority-denial behavior"]
    material_unknown["category_coverage"][0]["applicability"]["result"] = "UNKNOWN"
    write_json(
        negative_dir / "material-unknown-test-profile.json",
        {"expected_error": "TEST_PROFILE_MATERIAL_UNKNOWN", "instance": material_unknown},
    )

    unsupported_na = copy.deepcopy(test_profile)
    unsupported_na["profile_id"] = "TESTPROFILE-NEGATIVE-UNSUPPORTED-NA"
    unsupported_na["category_coverage"][0]["applicability"] = {
        "result": "NOT_APPLICABLE",
        "rule_id": "",
        "reason": "",
        "evidence_refs": [],
        "approval_ref": "",
    }
    write_json(
        negative_dir / "unsupported-na-test-profile.json",
        {"expected_error": "TEST_PROFILE_UNSUPPORTED_NOT_APPLICABLE", "instance": unsupported_na},
    )

    synthetic_promotion = copy.deepcopy(test_profile)
    synthetic_promotion["profile_id"] = "TESTPROFILE-NEGATIVE-SYNTHETIC-PROMOTION"
    synthetic_promotion["evidence_scope"] = "SYNTHETIC"
    synthetic_promotion["runtime_evidence_status"] = "PASS"
    write_json(
        negative_dir / "synthetic-runtime-promotion-test-profile.json",
        {"expected_error": "TEST_PROFILE_SYNTHETIC_RUNTIME_PROMOTION", "instance": synthetic_promotion},
    )

    valid_stateless_task = copy.deepcopy(test_profile)
    valid_stateless_task["profile_id"] = "TESTPROFILE-SEMANTIC-STATELESS-001"
    valid_stateless_task["profile_kind"] = "TASK"
    valid_stateless_task["subject_ref"] = (
        "art_" + deterministic_uuid7("stateless-task-subject")
    )
    valid_stateless_task["subject_digest"] = "sha256:" + sha256_bytes(
        b"stateless-task-subject"
    )
    valid_stateless_task["traceability"]["requirement_ids"] = [
        "REQ-STATELESS-001"
    ]
    valid_stateless_task["traceability"]["risk_ids"] = ["RISK-STATELESS-001"]
    valid_stateless_task["traceability"]["transition_ids"] = []
    valid_stateless_task["fixture_records"] = [
        {
            "fixture_id": "FIXTURE-STATELESS-SUBJECT-001",
            "canonical_path": "tests/fixtures/work_management/stateless-subject.json",
            "semantic_owner_id": "work_management",
            "provenance_ref": "REQ-STATELESS-001",
            "version": "1.0.0",
            "classification": "INTERNAL",
            "mutation_authority_id": "HUMAN_TEST_DATA_OWNER",
            "hidden_from_maker": False,
            "subject_kinds": ["STATELESS_COMMAND"],
            "status": "ACTIVE",
        }
    ]
    supported_stateless_na = {
        "result": "NOT_APPLICABLE",
        "rule_id": "TDD-STATELESS-SUBJECT-NA",
        "reason": "The exact task subject has no state machine or transition surface.",
        "evidence_refs": ["FIXTURE-STATELESS-SUBJECT-001"],
        "approval_ref": "ADR-0008",
    }
    for failure_row in valid_stateless_task["failure_mode_matrix"]:
        if failure_row["failure_mode_class"] == "COMMANDS_AND_STATE_TRANSITIONS":
            failure_row["applicability"] = copy.deepcopy(
                supported_stateless_na
            )
            failure_row["execution_status"] = "NOT_APPLICABLE"
            failure_row["transition_ids"] = []
            continue
        failure_row["precondition_refs"] = ["REQ-STATELESS-001"]
        failure_row["fault_input_refs"] = [
            f"FAULT-{failure_row['failure_mode_class']}"
        ]
        failure_row["test_lanes"] = ["UNIT"]
        failure_row["owner_id"] = "HUMAN_TEST_OWNER"
    for edge_row in valid_stateless_task["edge_case_partitions"]:
        edge_row["applicability"] = {
            **copy.deepcopy(supported_stateless_na),
            "rule_id": f"TDD-EDGE-NA-{edge_row['partition_id']}",
            "reason": (
                "The bounded stateless subject has no applicable "
                f"{edge_row['partition_id']} exploration space."
            ),
        }
        edge_row["execution_status"] = "NOT_APPLICABLE"
    valid_stateless_task["digest"] = digest_value(valid_stateless_task)
    write_json(
        semantic_dir / "valid-stateless-task-profile.json",
        {"expected_result": "PASS", "instance": valid_stateless_task},
    )

    unjustified_edge_na = copy.deepcopy(valid_stateless_task)
    unjustified_edge_na["profile_id"] = "TESTPROFILE-NEGATIVE-UNJUSTIFIED-EDGE-NA"
    unjustified_edge_na["edge_case_partitions"][0]["applicability"] = {
        "result": "NOT_APPLICABLE",
        "rule_id": "",
        "reason": "",
        "evidence_refs": [],
        "approval_ref": "",
    }
    write_json(
        negative_dir / "unjustified-edge-na-test-profile.json",
        {
            "expected_error": "TEST_PROFILE_UNSUPPORTED_NOT_APPLICABLE",
            "instance": unjustified_edge_na,
        },
    )

    forced_transition_boilerplate = copy.deepcopy(valid_stateless_task)
    forced_transition_boilerplate["profile_id"] = (
        "TESTPROFILE-NEGATIVE-FORCED-TRANSITION-BOILERPLATE"
    )
    transition_row = next(
        row
        for row in forced_transition_boilerplate["failure_mode_matrix"]
        if row["failure_mode_class"] == "COMMANDS_AND_STATE_TRANSITIONS"
    )
    transition_row["transition_ids"] = ["TRANSITION-NOT-APPLICABLE-001"]
    forced_transition_boilerplate["traceability"]["transition_ids"] = [
        "TRANSITION-NOT-APPLICABLE-001"
    ]
    write_json(
        negative_dir / "forced-transition-boilerplate-test-profile.json",
        {
            "expected_error": "TEST_PROFILE_NA_TRANSITION_BOILERPLATE",
            "instance": forced_transition_boilerplate,
        },
    )

    forged_pass_missing_production_evidence = copy.deepcopy(
        valid_stateless_task
    )
    forged_pass_missing_production_evidence["profile_id"] = (
        "TESTPROFILE-NEGATIVE-PASS-MISSING-PRODUCTION-EVIDENCE"
    )
    for row in (
        forged_pass_missing_production_evidence["category_coverage"]
        + forged_pass_missing_production_evidence["failure_mode_matrix"]
        + forged_pass_missing_production_evidence[
            "production_evidence_obligations"
        ]
    ):
        if row["applicability"]["result"] == "APPLICABLE":
            row["execution_status"] = "PASS"
            row["evidence_refs"] = [
                f"EVIDENCE-{slug(row.get('category_id') or row.get('failure_mode_class') or row.get('obligation_id'))}"
            ]
    forged_pass_missing_production_evidence["derived_result"] = "PASS"
    forged_pass_missing_production_evidence[
        "runtime_evidence_status"
    ] = "PASS"
    forged_pass_missing_production_evidence["evidence_scope"] = "RUNTIME"
    forged_pass_missing_production_evidence["sealing_eligible"] = True
    write_json(
        negative_dir / "forged-pass-missing-production-evidence.json",
        {
            "expected_error": "TEST_PROFILE_PRODUCTION_EVIDENCE_MISSING",
            "instance": forged_pass_missing_production_evidence,
        },
    )
    forged_pass_unbound_production_evidence = copy.deepcopy(
        forged_pass_missing_production_evidence
    )
    forged_pass_unbound_production_evidence["profile_id"] = (
        "TESTPROFILE-NEGATIVE-PASS-UNBOUND-PRODUCTION-EVIDENCE"
    )
    for evidence_field in forged_pass_unbound_production_evidence["evidence"]:
        forged_pass_unbound_production_evidence["evidence"][
            evidence_field
        ] = [f"GLOBAL-{slug(evidence_field)}-001"]
    row_evidence_refs = {
        ref
        for row in (
            forged_pass_unbound_production_evidence["category_coverage"]
            + forged_pass_unbound_production_evidence["failure_mode_matrix"]
            + forged_pass_unbound_production_evidence[
                "production_evidence_obligations"
            ]
        )
        if row["applicability"]["result"] == "APPLICABLE"
        for ref in row["evidence_refs"]
    }
    forged_pass_unbound_production_evidence["evidence_bindings"] = [
        {
            "evidence_ref": ref,
            "subject_ref": forged_pass_unbound_production_evidence[
                "subject_ref"
            ],
            "subject_digest": forged_pass_unbound_production_evidence[
                "subject_digest"
            ],
            "freshness_status": "CURRENT",
            "result": "PASS",
        }
        for ref in sorted(row_evidence_refs)
    ]
    write_json(
        negative_dir / "forged-pass-unbound-production-evidence.json",
        {
            "expected_error": "TEST_PROFILE_PASS_BINDING_INCOMPLETE",
            "instance": forged_pass_unbound_production_evidence,
        },
    )

    quarantine_record = {
        "quarantine_id": "QUARANTINE-EXPIRED-001",
        "test_refs": ["tests/integration/work_management/test_example.py"],
        "subject_ref": "art_" + deterministic_uuid7("quarantine-subject"),
        "subject_digest": "sha256:" + sha256_bytes(b"quarantine-subject"),
        "observed_failure_distribution": {
            "window_start": "2026-07-20T00:00:00Z",
            "window_end": "2026-07-21T00:00:00Z",
            "total_runs": 10,
            "passes": 4,
            "failures": 5,
            "infrastructure_errors": 1,
            "retries": 3,
            "retry_passes": 2,
            "failure_signatures": ["SIG-TIMEOUT"],
        },
        "affected_gate_ids": ["AI-G2"],
        "affected_risk_ids": ["RISK-FLAKE-001"],
        "alternate_evidence_refs": ["evd_" + deterministic_uuid7("alternate")],
        "alternate_evidence_noncompensating": True,
        "gate_disposition": "BLOCKED",
        "retry_passes_non_authoritative": True,
        "owner_id": "HUMAN_TEST_OWNER",
        "linked_work_item_id": "work_" + deterministic_uuid7("quarantine-work"),
        "reason": "Repeated timeout signature requires root-cause repair.",
        "opened_at": "2026-07-22T00:00:00Z",
        "expires_at": "2026-07-27T00:00:00Z",
        "removal_criteria": ["Twenty consecutive clean production-shaped runs"],
        "restoration_plan_ref": "PLAN-RESTORE-TEST-001",
        "backfill_test_refs": ["TEST-BACKFILL-001"],
        "status": "ACTIVE",
        "removal_evidence_refs": [],
    }
    expired_quarantine = copy.deepcopy(test_profile)
    expired_quarantine["profile_id"] = "TESTPROFILE-NEGATIVE-EXPIRED-QUARANTINE"
    expired_quarantine["quarantine_records"] = [quarantine_record]
    write_json(
        negative_dir / "expired-quarantine-test-profile.json",
        {
            "expected_error": "TEST_PROFILE_QUARANTINE_EXPIRED",
            "instance": expired_quarantine,
        },
    )

    retry_to_pass = copy.deepcopy(test_profile)
    retry_to_pass["profile_id"] = "TESTPROFILE-NEGATIVE-RETRY-TO-PASS"
    retry_to_pass_record = copy.deepcopy(quarantine_record)
    retry_to_pass_record["quarantine_id"] = "QUARANTINE-RETRY-PASS-001"
    retry_to_pass_record["expires_at"] = "2099-01-01T00:00:00Z"
    retry_to_pass_record["gate_disposition"] = "PASS"
    retry_to_pass["quarantine_records"] = [retry_to_pass_record]
    write_json(
        negative_dir / "retry-to-pass-quarantine-test-profile.json",
        {
            "expected_error": "TEST_PROFILE_QUARANTINE_RETRY_TO_PASS",
            "instance": retry_to_pass,
        },
    )

    incomplete_deletion = copy.deepcopy(test_profile)
    incomplete_deletion["profile_id"] = "TESTPROFILE-NEGATIVE-INCOMPLETE-DELETION"
    incomplete_deletion["obsolete_test_deletions"] = [
        {
            "deletion_id": "TEST-DELETION-INCOMPLETE-001",
            "test_refs": ["tests/unit/work_management/test_obsolete.py"],
            "requirement_trace_dispositions": [
                {
                    "trace_id": "REQ-OBSOLETE-001",
                    "disposition": "REPLACED",
                    "decision_ref": "ADR-0008",
                }
            ],
            "risk_trace_dispositions": [
                {
                    "trace_id": "RISK-OBSOLETE-001",
                    "disposition": "RETIRED",
                    "decision_ref": "ADR-0008",
                }
            ],
            "fixture_cleanup_refs": ["FIXTURE-OBSOLETE-001"],
            "snapshot_cleanup_refs": ["SNAPSHOT-OBSOLETE-001"],
            "owner_id": "HUMAN_TEST_OWNER",
            "approval_ref": "ADR-0008",
            "rationale": "The behavior was replaced.",
            "deleted_at": FIXED_TIME,
            "resulting_gap_status": "NONE",
        }
    ]
    write_json(
        negative_dir / "incomplete-obsolete-test-deletion.json",
        {
            "expected_error": "TEST_PROFILE_OBSOLETE_DELETION_INCOMPLETE",
            "instance": incomplete_deletion,
        },
    )

    forged_task_pass = copy.deepcopy(test_profile)
    forged_task_pass["profile_id"] = "TESTPROFILE-NEGATIVE-FORGED-TASK-PASS"
    forged_task_pass["profile_kind"] = "TASK"
    forged_task_pass["runtime_evidence_status"] = "PASS"
    forged_task_pass["derived_result"] = "PASS"
    forged_task_pass["evidence_scope"] = "RUNTIME"
    forged_task_pass["sealing_eligible"] = True
    write_json(
        negative_dir / "forged-task-aggregate-pass.json",
        {"expected_error": "TEST_PROFILE_TASK_SUBJECT_MISSING", "instance": forged_task_pass},
    )

    blanket_test_owner = copy.deepcopy(
        next(
            entry
            for entry in registries["paths.json"]["entries"]
            if entry["responsibility_class"] == "ALLOWED_TEST_ROOT"
        )
    )
    blanket_test_owner["semantic_owner_kind"] = "EXACT_CONTEXT"
    blanket_test_owner["semantic_owner_context"] = "process_assurance"
    write_json(
        negative_dir / "blanket-test-root-owner.json",
        {"expected_error": "PATH_TEST_BLANKET_SEMANTIC_OWNER", "instance": blanket_test_owner},
    )

    (negative_dir / "forbidden-test-bypass.py").write_text(
        "# expected_error: TEST_BYPASS\n"
        "def authorize(subject, *, bypass_policy=False):\n"
        "    return True if bypass_policy else subject.is_authorized\n",
        encoding="utf-8",
    )
    (negative_dir / "forbidden-test-only-production-branch.py").write_text(
        "# expected_error: TEST_ONLY_PRODUCTION_BRANCH\n"
        "import os\n\n"
        "def active_reducer():\n"
        "    if os.environ.get(\"RANEX_TEST_MODE\"):\n"
        "        return \"alternate_test_reducer\"\n"
        "    return \"production_reducer\"\n",
        encoding="utf-8",
    )
    (negative_dir / "forbidden-cross-context-private-import.py").write_text(
        "# expected_error: TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT\n"
        "from ranex.policy.domain.roles import Role\n\n"
        "def use_private_role(role: Role) -> Role:\n"
        "    return role\n",
        encoding="utf-8",
    )
    (negative_dir / "unregistered-public-api-import.py").write_text(
        "# expected_error: TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE\n"
        "from ranex.knowledge.api import KnowledgeView\n\n"
        "def use_knowledge(view: KnowledgeView) -> KnowledgeView:\n"
        "    return view\n",
        encoding="utf-8",
    )
    write_json(
        negative_dir / "broad-host-edge-exception.json",
        {
            "expected_error": "TOPOLOGY_EXCEPTION_WHOLE_LAYER_WILDCARD",
            "instance": {
                "schema_version": "topology-exception/v1",
                "exception_id": "TOPOLOGY-EXCEPTION-BROAD-HOST-EDGE-001",
                "exception_class": "HOST_EDGE_ADAPTER",
                "exact_path": "src/ranex/adapters/**",
                "rule_ids": ["ORG-LAYER-001", "ORG-EXEMPTION-001"],
                "scope": "All host adapters.",
                "owner_context": "configuration_management",
                "accountable_human_role": "HUMAN_ARCHITECTURE_OWNER",
                "rationale": "Negative fixture proving whole-layer grants fail.",
                "allowed_dependency_edges": ["EDGE-GE-ARTIFACT"],
                "security_data_constraints": ["INHERIT_EXACT_SUBJECT"],
                "approval_ref": "ADR-0007",
                "review_expires_at": "2099-01-01T00:00:00Z",
                "required_test_refs": ["tests/architecture/test_host_edges.py"],
                "removal_criteria": ["Move each adapter to its owning context."],
                "status": "ACTIVE",
                "source": str(TOPOLOGY_ADR.relative_to(ROOT)),
            },
        },
    )
    write_json(
        negative_dir / "cyclic-context-imports.json",
        {
            "expected_error": "TOPOLOGY_CONTEXT_IMPORT_CYCLE",
            "modules": [
                {
                    "path": "src/ranex/work_management/application/example.py",
                    "source": "from ranex.policy.api import AuthorizationSnapshot\n",
                },
                {
                    "path": "src/ranex/policy/application/example.py",
                    "source": "from ranex.work_management.api import WorkItemView\n",
                },
            ],
        },
    )


def assessment_subject(vital_digest: str) -> dict[str, Any]:
    source_manifest = {
        "manifest_id": "ASSESSMENT-SOURCE-MANIFEST-001",
        "files": [
            {"path": str(path.relative_to(ROOT)), "digest": "sha256:" + sha256_file(path)}
            for path in [CONTROL_DOC, ARTIFACT_DOC, CONTRACTS / "vital-profile.json", CONTRACTS / "states.json"]
        ],
    }
    write_json(ASSESSMENTS / "assessment-source-manifest.json", source_manifest)
    manifest_digest = "sha256:" + sha256_bytes(canonical_bytes(source_manifest))
    subject = {
        "subject_schema": "research-subject/v1",
        "project_id": "prj_" + deterministic_uuid7("ranex-project"),
        "work_item_id": "work_" + deterministic_uuid7("wave1-contracting"),
        "repository_id": "repo_" + deterministic_uuid7("ranex-repository"),
        "repository_uri_digest": "sha256:" + sha256_bytes(b"local:ranex"),
        "base_revision": "0" * 40,
        "question_digest": "sha256:" + sha256_bytes(b"Wave 1 capability definition and runtime evidence baseline"),
        "scope_digest": vital_digest,
        "source_manifest_digest": manifest_digest,
        "research_prompt_digest": "sha256:" + sha256_bytes(b"Deterministic generated assessment baseline"),
        "observed_at": FIXED_TIME,
    }
    subject_record = {
        "subject_id": "art_" + deterministic_uuid7("wave1-assessment-subject"),
        "subject": subject,
        "digest": "sha256:" + sha256_bytes(canonical_bytes(subject)),
    }
    write_json(ASSESSMENTS / "assessment-subject.json", subject_record)
    return subject_record


def fill_assessment(template: dict[str, Any], row: dict[str, str], subject: dict[str, Any], registry_digests: dict[str, str]) -> dict[str, Any]:
    item = copy.deepcopy(template)
    control_id = row["control_id"]
    domain_id = row["domain_id"]
    item.update(
        {
            "assessment_id": "capability_assessment_" + deterministic_uuid7(control_id),
            "revision": 1,
            "status": "NOT_ASSESSED",
            "definition_status": "DEFINED",
            "definition_evidence_refs": [f"docs/architecture/SDLC_CONTROL_CATALOG.md#{control_id.lower()}"],
            "subject_schema": "research-subject/v1",
            "subject_ref": subject["subject_id"],
            "subject_digest": subject["digest"],
            "subject_manifest_digest": subject["subject"]["source_manifest_digest"],
            "core_sdlc_trace_ref": "",
        }
    )
    item["scope"].update(
        {
            "capability_id": domain_id,
            "control_id": control_id,
            "service_ids": ["RANEX_TARGET"],
            "value_stream_ids": ["ARCHITECTURE_CONTRACTING"],
            "work_classes": STATE_AXES["WorkClass"]["values"],
            "risk_lanes": STATE_AXES["RiskLane"]["values"],
            "window_start": FIXED_TIME,
            "window_end": FIXED_TIME,
        }
    )
    item["scope"]["scope_digest"] = "sha256:" + sha256_bytes(canonical_bytes({k: v for k, v in item["scope"].items() if k != "scope_digest"}))
    item["assessment_authority"] = {
        "assessor_id": "UNASSIGNED_WAVE_2",
        "approver_id": "UNASSIGNED_WAVE_2",
        "independence_evidence_ref": "",
        "conflicts": ["No runtime population, independent assessor, or approval evidence exists."],
    }
    item["applicability"].update(
        {
            "registry_digest": registry_digests["applicability-rules.json"],
            "rule_id": row["applicability_rule_id"],
            "result": "UNKNOWN",
            "not_applicable_reason": "",
        }
    )
    item["population"]["joint_strata"] = [
        {"work_class": work_class, "risk_lane": risk_lane, "eligible": 0, "included": 0, "excluded": 0}
        for work_class in STATE_AXES["WorkClass"]["values"]
        for risk_lane in STATE_AXES["RiskLane"]["values"]
    ]
    item["population"]["exclusions"] = []
    item["population"]["sampling_method"] = "NOT_ASSESSED"
    item["evidence"].update(
        {
            "artifact_and_provenance_refs": item["definition_evidence_refs"],
            "limitations": ["Definition evidence exists; enacted runtime, rejection-path, population, outcome, and guardrail evidence do not."],
        }
    )
    item["capability_rating"].update(
        {
            "result": "NOT_ASSESSED",
            "level": None,
            "label": "",
            "criterion_evidence": [],
        }
    )
    item["gap_register"]["entries"] = [
        {"gap_id": f"GAP-{control_id}-{dimension}", "source_dimension": dimension, "source_ref": "", "materiality": "UNKNOWN", "disposition": "OPEN", "disposition_evidence_ref": ""}
        for dimension in ["EVIDENCE", "POPULATION", "COVERAGE", "MEASUREMENT", "APPLICABILITY"]
    ]
    item["gap_register"]["reconciliation"]["unresolved_material_gap_refs"] = [entry["gap_id"] for entry in item["gap_register"]["entries"]]
    item["confidence"].update(
        {
            "derived_level": "LOW",
            "derivation_result": "NOT_CHECKED",
            "rationale": "No qualified runtime population or measurement evidence exists.",
        }
    )
    trigger_codes = [code for codes in PRIORITY_TRIGGERS.values() for code in codes]
    item["priority"].update(
        {
            "priority_rule_digest": registry_digests["priority-rules.json"],
            "result": "NOT_EVALUATED",
            "evaluated_trigger_results": [{"trigger_code": code, "result": "NOT_CHECKED", "evidence_refs": []} for code in trigger_codes],
            "matched_trigger_codes": [],
            "decisive_trigger_code": "",
            "derived_tier": None,
            "derivation_result": "NOT_CHECKED",
        }
    )
    item["created_at"] = FIXED_TIME
    item["digest"] = digest_value(item)
    return item


def fill_projection(template: dict[str, Any], domain_id: str, rows: list[dict[str, str]], assessments: dict[str, dict[str, Any]], subject: dict[str, Any], registry_digests: dict[str, str]) -> dict[str, Any]:
    item = copy.deepcopy(template)
    item.update(
        {
            "projection_id": "capability_domain_projection_" + deterministic_uuid7(domain_id),
            "revision": 1,
            "status": "NOT_ASSESSED",
            "definition_status": "DEFINED",
            "definition_evidence_refs": ["architecture/contracts/vital-profile.json"],
            "subject_schema": "research-subject/v1",
            "subject_ref": subject["subject_id"],
            "subject_digest": subject["digest"],
            "subject_manifest_digest": subject["subject"]["source_manifest_digest"],
            "core_sdlc_trace_ref": "",
        }
    )
    item["scope"].update(
        {
            "domain_id": domain_id,
            "service_ids": ["RANEX_TARGET"],
            "value_stream_ids": ["ARCHITECTURE_CONTRACTING"],
            "work_classes": STATE_AXES["WorkClass"]["values"],
            "risk_lanes": STATE_AXES["RiskLane"]["values"],
            "window_start": FIXED_TIME,
            "window_end": FIXED_TIME,
        }
    )
    item["scope"]["scope_digest"] = "sha256:" + sha256_bytes(canonical_bytes({k: v for k, v in item["scope"].items() if k != "scope_digest"}))
    item["vital_profile"].update(
        {
            "profile_digest": registry_digests["vital-profile.json"],
            "applicability_registry_digest": registry_digests["applicability-rules.json"],
        }
    )
    members = []
    for row in rows:
        assessment = assessments[row["control_id"]]
        members.append(
            {
                "domain_id": domain_id,
                "control_id": row["control_id"],
                "applicability_rule_id": row["applicability_rule_id"],
                "assessment_ref": f"docs/architecture/assessments/controls/{row['control_id']}.json",
                "assessment_revision": assessment["revision"],
                "assessment_digest": assessment["digest"],
                "assessment_scope_digest": assessment["scope"]["scope_digest"],
                "applicability_result": "UNKNOWN",
                "rating_result": "NOT_ASSESSED",
                "level": None,
                "priority_tier": None,
            }
        )
    item["members"] = members
    item["validation"].update(
        {
            "exact_tuple_set_result": "PASS",
            "no_duplicate_or_extra_member_result": "PASS",
            "identical_scope_and_window_result": "PASS",
            "immutable_binding_result": "PASS",
            "applicability_rating_consistency_result": "PASS",
            "validation_evidence_refs": ["scripts/architecture/validate_contracts.py"],
        }
    )
    item["derivation"].update(
        {
            "registered_member_count": len(rows),
            "bound_member_count": len(rows),
            "applicable_member_count": 0,
            "not_applicable_member_count": 0,
            "begun_applicable_member_count": 0,
            "scored_applicable_member_count": 0,
            "derived_result": "UNKNOWN",
            "derived_level": None,
            "lowest_control_ids": [],
        }
    )
    item["priority_projection"].update(
        {
            "priority_rule_digest": registry_digests["priority-rules.json"],
            "result": "NOT_EVALUATED",
            "derived_tier": None,
            "decisive_control_ids": [],
        }
    )
    item["assessment_authority"] = {"projector_id": "scripts/architecture/generate_contracts.py", "approver_id": "UNASSIGNED_WAVE_2", "independence_evidence_ref": ""}
    item["created_at"] = FIXED_TIME
    item["digest"] = digest_value(item)
    return item


def generate_assessments(registries: dict[str, Any]) -> None:
    tuples = registries["vital-profile.json"]["entries"]
    registry_digests = {name: "sha256:" + sha256_file(CONTRACTS / name) for name in registries}
    registry_digests["schema-registry.json"] = "sha256:" + sha256_file(CONTRACTS / "schema-registry.json")
    subject = assessment_subject(registry_digests["vital-profile.json"])
    assessment_template = yaml.safe_load(read(TEMPLATES / "CAPABILITY_ASSESSMENT.yaml"))
    projection_template = yaml.safe_load(read(TEMPLATES / "CAPABILITY_DOMAIN_PROJECTION.yaml"))
    assessments: dict[str, dict[str, Any]] = {}
    for row in tuples:
        assessment = fill_assessment(assessment_template, row, subject, registry_digests)
        assessments[row["control_id"]] = assessment
        write_json(ASSESSMENTS / "controls" / f"{row['control_id']}.json", assessment)
    domains = sorted({row["domain_id"] for row in tuples})
    for domain_id in domains:
        rows = [row for row in tuples if row["domain_id"] == domain_id]
        projection = fill_projection(projection_template, domain_id, rows, assessments, subject, registry_digests)
        write_json(ASSESSMENTS / "domains" / f"{domain_id}.json", projection)

    summary = {
        "report_id": "RANEX-WAVE1-CONTRACT-COMPLETENESS-001",
        "status": "GENERATED_VALIDATION_REQUIRED",
        "contract_scope": "EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY",
        "runtime_claim": "NOT_ASSESSED",
        "counts": {
            "governed_yaml_templates": len(ARTIFACT_SCHEMAS),
            "artifact_schemas": len(ARTIFACT_SCHEMAS),
            "common_schemas": len(list((SCHEMAS / "common").glob("*.schema.json"))),
            "capability_zones": registries["architecture-elements.json"]["counts_by_kind"]["CAPABILITY_ZONE"],
            "vital_control_tuples": len(tuples),
            "capability_assessments": len(assessments),
            "domain_projections": len(domains),
            "architecture_elements": len(registries["architecture-elements.json"]["entries"]),
            "negative_fixtures": len(list((SCHEMAS / "fixtures" / "negative").glob("*"))),
            "topology_rules": len(registries["topology-rules.json"]["entries"]),
            "allowed_test_roots": len(registries["test-practices.json"]["taxonomy"]),
            "tdd_rules": len(registries["test-practices.json"]["entries"]),
            "test_definition_profiles": len(registries["test-practice-profiles.json"]["entries"]),
            "architecture_rule_assessments": len(
                registries["architecture-rule-assessments.json"]["entries"]
            ),
            "declared_context_dependency_edges": len(
                registries["context-dependency-edges.json"]["entries"]
            ),
            "context_boundary_fit_rows": len(
                registries["context-boundary-fitness.json"]["entries"]
            ),
            "adr9_rules": len(
                registries["context-boundary-fitness.json"]["rules"]
            ),
            "adr9_fitness_obligations": len(
                registries["context-boundary-fitness.json"][
                    "fitness_obligations"
                ]
            ),
            "coupling_measures": len(
                registries["context-coupling-policy.json"]["measures"]
            ),
            "feedback_objectives": len(
                registries["feedback-fitness.json"]["objectives"]
            ),
            "semantic_fixtures": len(
                list((SCHEMAS / "fixtures" / "semantic").glob("*"))
            ),
        },
        "honesty_invariants": {
            "runtime_scores_fabricated": 0,
            "all_control_ratings": "NOT_ASSESSED",
            "all_definition_statuses": "DEFINED",
            "all_domain_results": "UNKNOWN",
            "reason": "Runtime population, enacted paths, qualified measures, and independent approval evidence do not exist.",
        },
        "residual_cross_wave_inputs": [
            "The architecture-design profile applies all nine source families and 34 practices without a numeric score; task/runtime enactment and behavioral effectiveness remain NOT_ASSESSED.",
            "Human AI-G2 acceptance remains outstanding.",
            "Runtime producer ownership, hidden-fixture isolation, schema package generation, and cross-language RFC 8785 parity remain unproven.",
            "ADR-0007 topology, ADR-0008 TDD, and ADR-0009 boundary/coupling/feedback rules are executable paper contracts; actual source/import/test/runtime enactment remains NOT_ASSESSED.",
            "Fork ancestry preflight SDLC-FORK-000 remains outside this Wave 1 contract scope.",
        ],
    }
    write_json(ASSESSMENTS / "completeness-report.json", summary)
    md = f"""# Wave 1 architecture-contract completeness report

Status: **GENERATED — RUN VALIDATOR**

This baseline covers executable documentation contracts only. It makes no
runtime, producer-enforcement, isolation, or production-readiness claim.

| Denominator | Count |
|---|---:|
| Governed YAML artifact templates/schemas | {summary['counts']['artifact_schemas']} |
| Capability zones | {summary['counts']['capability_zones']} |
| VITAL control tuples / assessments | {summary['counts']['vital_control_tuples']} / {summary['counts']['capability_assessments']} |
| Capability domains / projections | {len(domains)} / {summary['counts']['domain_projections']} |
| Architecture elements inventoried | {summary['counts']['architecture_elements']} |
| ADR-0007 topology rules | {summary['counts']['topology_rules']} |
| ADR-0008 allowed roots / TDD rules | {summary['counts']['allowed_test_roots']} / {summary['counts']['tdd_rules']} |
| Definition-only per-rule assessments | {summary['counts']['architecture_rule_assessments']} |
| Declared context edges / boundary-fit rows | {summary['counts']['declared_context_dependency_edges']} / {summary['counts']['context_boundary_fit_rows']} |
| ADR-0009 rules / fitness obligations | {summary['counts']['adr9_rules']} / {summary['counts']['adr9_fitness_obligations']} |
| Coupling measures / feedback objectives | {summary['counts']['coupling_measures']} / {summary['counts']['feedback_objectives']} |
| Negative semantic fixtures | {summary['counts']['negative_fixtures']} |
| Positive semantic fixtures | {summary['counts']['semantic_fixtures']} |

All 40 control records are `NOT_ASSESSED` with separately recorded
`definition_status: DEFINED`. All ten domain projections derive `UNKNOWN`
because applicability and runtime evidence are unresolved. No numeric maturity
score is fabricated.

Run `uv run --project scripts/architecture python
scripts/architecture/validate_contracts.py` for the deterministic result.
"""
    (ASSESSMENTS / "COMPLETENESS_REPORT.md").write_text(md, encoding="utf-8")


def generate_manifests() -> None:
    registry_files = sorted(path for path in CONTRACTS.glob("*.json") if path.name != "registry-manifest.json")
    manifest = {
        "manifest_id": "RANEX-CONTRACT-REGISTRY-MANIFEST-001",
        "version": "1.0.0",
        "self_listing_rule": "This manifest excludes itself to avoid a circular digest.",
        "entries": [{"path": str(path.relative_to(ROOT)), "digest": "sha256:" + sha256_file(path)} for path in registry_files],
    }
    write_json(CONTRACTS / "registry-manifest.json", manifest)


def generate_contract_tree() -> None:
    # These directories contain generator-owned immutable baselines. Remove
    # only prior JSON outputs so a changed denominator cannot leave stale or
    # empty filenames behind.
    for directory in (ASSESSMENTS / "controls", ASSESSMENTS / "domains"):
        if directory.exists():
            for path in directory.glob("*.json"):
                path.unlink()
    registries = generate_registries()
    generate_schemas(registries)
    generate_fixtures(registries)
    generate_assessments(registries)
    generate_manifests()
    print(
        json.dumps(
            {
                "registries": len(list(CONTRACTS.glob("*.json"))),
                "schemas": len(list(SCHEMAS.rglob("*.schema.json"))),
                "assessments": len(list((ASSESSMENTS / "controls").glob("*.json"))),
                "projections": len(list((ASSESSMENTS / "domains").glob("*.json"))),
            },
            sort_keys=True,
        )
    )


def main() -> None:
    with contract_tree_lock(ROOT):
        generate_contract_tree()


if __name__ == "__main__":
    main()
