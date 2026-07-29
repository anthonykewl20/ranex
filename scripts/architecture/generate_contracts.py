#!/usr/bin/env python3
"""Generate the Ranex Wave-1 executable documentation-contract baseline.

The generator is intentionally deterministic. It reads accepted architecture
documents and authoring templates, then writes only generated contract,
schema, fixture, and assessment paths owned by Wave 1.
"""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

import rfc8785
import yaml
import jsonschema

from contract_tree_lock import contract_tree_lock


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "architecture" / "contracts"
SCHEMAS = ROOT / "schemas"
ASSESSMENTS = ROOT / "docs" / "architecture" / "assessments"
TEMPLATES = ROOT / "docs" / "architecture" / "templates"
GENERATOR_WRITER = "scripts/architecture/generate_contracts.py"
VALIDATOR_WRITER = "scripts/architecture/validate_contracts.py"
LEGAL_MANIFEST_PATH = "legal/licensing-manifest.json"
LEGAL_MANIFEST = ROOT / LEGAL_MANIFEST_PATH
LICENSING_POLICY_RANEX_ORIGINAL = (
    "GENERATED_RANEX_ORIGINAL"
)
LICENSING_POLICY_CURATED_RESEARCH = (
    "GENERATED_CURATED_RESEARCH_NOASSERTION"
)
CURATED_RESEARCH_GENERATED_OUTPUT_PATHS = frozenset(
    {
        "architecture/contracts/architecture-elements.json",
        (
            "architecture/contracts/"
            "engineering-practice-profiles.json"
        ),
        "architecture/contracts/engineering-practices.json",
    }
)
READINESS_FRESHNESS_BOUNDARY_SUBCASES = [
    {
        "subcase_id": (
            "gate_expiry_equal_assessment_observation_rejects"
        ),
        "expected_outcome": "REJECT",
    },
    {
        "subcase_id": (
            "gate_expiry_before_assessment_observation_rejects"
        ),
        "expected_outcome": "REJECT",
    },
    {
        "subcase_id": (
            "gate_observation_after_assessment_observation_rejects"
        ),
        "expected_outcome": "REJECT",
    },
    {
        "subcase_id": (
            "gate_observation_equal_assessment_observation_accepts"
        ),
        "expected_outcome": "PASS",
    },
    {
        "subcase_id": (
            "assessment_expiry_equal_window_end_accepts"
        ),
        "expected_outcome": "PASS",
    },
    {
        "subcase_id": (
            "assessment_expiry_after_window_end_rejects"
        ),
        "expected_outcome": "REJECT",
    },
]
GENERATED_OUTPUT_PATHS: set[str] = set()
ARCH_DOC = ROOT / "docs" / "architecture" / "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md"
ARTIFACT_DOC = ROOT / "docs" / "architecture" / "AI_ARTIFACT_CONTRACTS.md"
CONTROL_DOC = ROOT / "docs" / "architecture" / "SDLC_CONTROL_CATALOG.md"
REFERENCE_MAP = ROOT / "docs" / "architecture" / "ENGINEERING_REFERENCE_APPLICATION_MAP.md"
FIXED_DECISION_ADR = (
    ROOT
    / "docs"
    / "architecture"
    / "decisions"
    / "ADR-0006-register-fixed-decisions-and-fitness-crosswalk.md"
)
WORKER_RUNTIME_ADR = (
    ROOT
    / "docs"
    / "architecture"
    / "decisions"
    / "ADR-0011-centralize-worker-orchestration-and-runtime-adapters.md"
)
READINESS_ADR = (
    ROOT
    / "docs"
    / "architecture"
    / "decisions"
    / "ADR-0012-separate-implementation-start-and-production-readiness.md"
)
ADR12_SOURCE_SHA256 = (
    "2707cfe0b1b4111f5b9ec1e41f9c71f0fbf75ac7f438c6df2d0829ea2ff54d02"
)
ADR12_MACHINE_BLOCK_SHA256 = (
    "90690d00db63ef4a6f9d8008f78532b36cf94a3d75290c98766cf020fe36042d"
)
TOPOLOGY_ADR = ROOT / "docs" / "architecture" / "decisions" / "ADR-0007-establish-modular-ddd-repository-organization.md"
TDD_ADR = ROOT / "docs" / "architecture" / "decisions" / "ADR-0008-make-tdd-the-default-development-discipline.md"
BOUNDARY_FITNESS_ADR = (
    ROOT
    / "docs"
    / "architecture"
    / "decisions"
    / "ADR-0009-register-boundary-fit-dependencies-and-feedback-fitness.md"
)
LEGACY_TEST_LAYOUT_ADR = (
    ROOT
    / "docs"
    / "architecture"
    / "decisions"
    / "ADR-0010-bound-inherited-hermes-test-layout-migration.md"
)
ADR10_SOURCE_SHA256 = (
    "45dcd9c90a3a40eb150b826030b211f42f8f53728e9acc749fde17c7df553beb"
)
ADR10_MACHINE_BLOCK_SHA256 = (
    "de5ed30d02ffac788574b319ac9afcc4c1246212b0b015251ac055bd7ef17472"
)
ADR10_BEHAVIOR_TEMPLATE_SHA256 = (
    "dde30eac076f48629f7002532704b8a14db254e7ad61680f7cc4f8b8a10216ce"
)
ADR10_CLASSIFICATION_TEMPLATE_SHA256 = (
    "ff0b7b0f6bbb0bf2ac35672963f22ebb96b8fcfcd5ca1cd09c55c462ddad58f9"
)
ADR10_IMMUTABLE_V1_INPUT_PATHS = frozenset(
    {
        "architecture/contracts/legacy-test-layout-policy-v1.json",
        "architecture/contracts/legacy-test-layout-policy.json",
        "architecture/contracts/legacy-test-layout-records-v1.json",
        "architecture/contracts/legacy-test-layout-records.json",
        (
            "schemas/common/"
            "legacy-test-change-exception-v1.schema.json"
        ),
        (
            "schemas/common/"
            "legacy-test-cutover-removal-record-v1.schema.json"
        ),
        "schemas/common/legacy-test-layout-policy-v1.schema.json",
        (
            "schemas/common/"
            "legacy-test-migration-record-v1.schema.json"
        ),
        "schemas/execution/landing-record-v1.schema.json",
    }
)
LEGACY_TEST_RECORD_ROOT = (
    ROOT / "architecture" / "records" / "legacy-test-layout"
)
LEGACY_TEST_CLASSIFICATION_ROOT = (
    LEGACY_TEST_RECORD_ROOT / "direct-source-classifications"
)
TEST_BEHAVIOR_AUTHORITY_ROOT = (
    ROOT
    / "architecture"
    / "records"
    / "test-governance"
    / "behavior-authorities"
)
LEGACY_TEST_RECORD_DIRECTORIES = {
    "CHANGE_EXCEPTION": LEGACY_TEST_RECORD_ROOT / "change-exceptions",
    "MIGRATION_RECORD": LEGACY_TEST_RECORD_ROOT / "migration-records",
    "CUTOVER_REMOVAL_RECORD": (
        LEGACY_TEST_RECORD_ROOT / "cutover-removal-records"
    ),
}
TEST_HEALTH_RECORD_ROOT = (
    ROOT / "architecture" / "records" / "test-health"
)
TEST_HEALTH_RECORD_CLASSES: dict[str, dict[str, str]] = {
    "tdd_cycle": {
        "directory": "tdd-cycles",
        "id_key": "cycle_id",
        "schema_path": (
            "schemas/common/tdd-cycle-record-v1.schema.json"
        ),
        "registry_filename": "tdd-cycle-records.json",
        "registry_id": "REG-TDD-CYCLE-RECORDS-001",
    },
    "tdd_exception": {
        "directory": "tdd-exceptions",
        "id_key": "exception_id",
        "schema_path": (
            "schemas/common/tdd-exception-record-v1.schema.json"
        ),
        "registry_filename": "tdd-exception-records.json",
        "registry_id": "REG-TDD-EXCEPTION-RECORDS-001",
    },
    "test_quarantine": {
        "directory": "quarantines",
        "id_key": "quarantine_id",
        "schema_path": (
            "schemas/common/test-quarantine-record-v1.schema.json"
        ),
        "registry_filename": "test-quarantine-records.json",
        "registry_id": "REG-TEST-QUARANTINE-RECORDS-001",
    },
    "test_deletion": {
        "directory": "obsolete-test-deletions",
        "id_key": "deletion_id",
        "schema_path": (
            "schemas/common/test-deletion-record-v1.schema.json"
        ),
        "registry_filename": "test-deletion-records.json",
        "registry_id": "REG-TEST-DELETION-RECORDS-001",
    },
}
ARCHITECTURE_PRACTICE_PROFILE = (
    ROOT / "docs" / "research" / "ranex-architecture-practice-application-profile.json"
)
SOURCE_OF_TRUTH = (
    ROOT / "docs" / "architecture" / "SOURCE_OF_TRUTH.md"
)
FIXED_TIME = "2026-07-28T00:00:00Z"
ESTIMATE_COMMITMENT_BLOCK_SHA256 = (
    "32ea9ac7d8eae9c37a887cfdfc2916b5ffc88e1030069844260d0f3f376728f5"
)
SDLC_CONTROL_CATALOG_SHA256 = (
    "22316ad927b94b890341442d6d27940b7696e369dcbcf56d277aface504d7805"
)
ARCHITECTURE_PRACTICE_PROFILE_SHA256 = (
    "f24995ddf5c5516fa685396e74f6c138068da1e6578764b0320e1f44c3e507a6"
)


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

GENERATED_ARTIFACT_SCHEMAS: tuple[dict[str, str], ...] = (
    {
        "artifact_type": "artifact_legal_hold_fact",
        "schema_path": (
            "schemas/artifacts/"
            "artifact-legal-hold-fact-v1.schema.json"
        ),
        "canonical_producer": "artifact_legal_hold_service",
        "owner_context": "artifact_management",
        "generation_contract_ref": (
            "docs/architecture/"
            "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md"
            "#161-exact-axis-kind-and-lifecycle-transition-contract"
        ),
    },
    {
        "artifact_type": "checker_execution_subject",
        "schema_path": (
            "schemas/assurance/"
            "checker-execution-subject-v1.schema.json"
        ),
        "canonical_producer": "assurance",
        "owner_context": "assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0008-make-tdd-the-default-development-discipline.md"
            "#canonical-test-health-authorities"
        ),
    },
    {
        "artifact_type": "tdd_cycle_subject",
        "schema_path": (
            "schemas/common/tdd-cycle-subject-v1.schema.json"
        ),
        "canonical_producer": "process_assurance",
        "owner_context": "process_assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0008-make-tdd-the-default-development-discipline.md"
            "#canonical-test-health-authorities"
        ),
    },
    {
        "artifact_type": "tdd_exception_subject",
        "schema_path": (
            "schemas/common/tdd-exception-subject-v1.schema.json"
        ),
        "canonical_producer": "process_assurance",
        "owner_context": "process_assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0008-make-tdd-the-default-development-discipline.md"
            "#canonical-test-health-authorities"
        ),
    },
    {
        "artifact_type": "test_deletion_subject",
        "schema_path": (
            "schemas/common/test-deletion-subject-v1.schema.json"
        ),
        "canonical_producer": "process_assurance",
        "owner_context": "process_assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0008-make-tdd-the-default-development-discipline.md"
            "#canonical-test-health-authorities"
        ),
    },
    {
        "artifact_type": "test_quarantine_subject",
        "schema_path": (
            "schemas/common/test-quarantine-subject-v1.schema.json"
        ),
        "canonical_producer": "process_assurance",
        "owner_context": "process_assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0008-make-tdd-the-default-development-discipline.md"
            "#canonical-test-health-authorities"
        ),
    },
    {
        "artifact_type": "readiness_subject",
        "schema_path": (
            "schemas/assurance/readiness-subject-v1.schema.json"
        ),
        "canonical_producer": "process_assurance",
        "owner_context": "process_assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0012-separate-implementation-start-and-production-readiness.md"
            "#exact-machine-contract"
        ),
    },
    {
        "artifact_type": "readiness_subject_manifest",
        "schema_path": (
            "schemas/assurance/"
            "readiness-subject-manifest-v1.schema.json"
        ),
        "canonical_producer": "configuration_management",
        "owner_context": "configuration_management",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0012-separate-implementation-start-and-production-readiness.md"
            "#exact-machine-contract"
        ),
    },
    {
        "artifact_type": "readiness_evidence_binding",
        "schema_path": (
            "schemas/assurance/"
            "readiness-evidence-binding-v1.schema.json"
        ),
        "canonical_producer": "assurance",
        "owner_context": "assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0012-separate-implementation-start-and-production-readiness.md"
            "#exact-machine-contract"
        ),
    },
    {
        "artifact_type": "readiness_assessment",
        "schema_path": (
            "schemas/assurance/readiness-assessment-v1.schema.json"
        ),
        "canonical_producer": "process_assurance",
        "owner_context": "process_assurance",
        "generation_contract_ref": (
            "docs/architecture/decisions/"
            "ADR-0012-separate-implementation-start-and-production-readiness.md"
            "#exact-machine-contract"
        ),
    },
)


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


STATE_AXIS_CATALOG: dict[str, Any]
STATE_AXES: dict[str, dict[str, Any]]
STATE_AXIS_CONTRACT_REFS: dict[str, str]


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


class DuplicateKeyLoader(yaml.SafeLoader):
    """YAML loader that rejects duplicate mapping keys."""


def _construct_unique_yaml_mapping(
    loader: DuplicateKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


DuplicateKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_yaml_mapping,
)


def load_yaml_text_strict(text: str) -> Any:
    return yaml.load(text, Loader=DuplicateKeyLoader)


def reject_duplicate_json_object(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    return json.loads(
        read(path),
        object_pairs_hook=reject_duplicate_json_object,
    )


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
    relative = str(path.relative_to(ROOT))
    if relative in ADR10_IMMUTABLE_V1_INPUT_PATHS:
        raise ValueError(
            "ADR-0010 immutable V1 writer attempt: " + relative
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    GENERATED_OUTPUT_PATHS.add(relative)


def write_generated_text(path: Path, value: str) -> None:
    relative = str(path.relative_to(ROOT))
    if relative in ADR10_IMMUTABLE_V1_INPUT_PATHS:
        raise ValueError(
            "ADR-0010 immutable V1 writer attempt: " + relative
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    GENERATED_OUTPUT_PATHS.add(relative)


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


def parse_state_axis_catalog(text: str) -> dict[str, Any]:
    """Parse and structurally prove the normative HERMES state catalog."""

    matching: list[dict[str, Any]] = []
    for block in re.findall(
        r"```yaml\s*\n(.*?)\n```",
        text,
        flags=re.DOTALL,
    ):
        candidate = load_yaml_text_strict(block)
        if (
            isinstance(candidate, dict)
            and candidate.get("schema_version") == "state-axis-contract/v1"
        ):
            matching.append(candidate)
    if len(matching) != 1:
        raise ValueError(
            "Expected exactly one state-axis-contract/v1 YAML catalog"
        )
    catalog = matching[0]
    expected_catalog_keys = {
        "schema_version",
        "catalog_id",
        "axis_count",
        "lifecycle_axis_count",
        "classifier_axis_count",
        "value_count",
        "transition_notation",
        "transition_fact_ref",
        "rejection_policy",
        "axes",
    }
    if set(catalog) != expected_catalog_keys:
        raise ValueError("State-axis catalog has unknown or missing fields")
    if catalog.get("catalog_id") != "STATE-AXIS-CONTRACT-1.0":
        raise ValueError("Unexpected state-axis catalog_id")
    if catalog.get("transition_notation") != "FROM>TO@GUARD_ID":
        raise ValueError("Unexpected state transition notation")
    if (
        catalog.get("transition_fact_ref")
        != "schemas/work/transition-event-v1.schema.json"
    ):
        raise ValueError("Unexpected state transition fact schema")
    rejection = catalog.get("rejection_policy")
    if not isinstance(rejection, dict):
        raise ValueError("State rejection policy is missing")
    if set(rejection) != {"policy_id", "result", "causes"}:
        raise ValueError("State rejection policy is not a closed object")
    if (
        rejection.get("policy_id")
        != "STATE-REJECTION-FAIL-CLOSED-1.0"
        or rejection.get("result")
        != "REJECT_NO_MUTATION_NO_TRANSITION_FACT_NO_OUTBOX_EVENT"
    ):
        raise ValueError("State rejection policy is not fail-closed")
    expected_rejection_causes = {
        "UNKNOWN_AXIS_OR_VALUE",
        "WRONG_OWNER_OR_AUTHORITY",
        "STALE_AGGREGATE_VERSION",
        "ILLEGAL_EDGE",
        "UNSATISFIED_GUARD",
        "WRONG_RECORDED_PRIOR_STATE",
        "MISSING_OR_STALE_EVIDENCE",
    }
    if set(rejection.get("causes", [])) != expected_rejection_causes:
        raise ValueError("State rejection-cause set is incomplete")

    axes = catalog.get("axes")
    if not isinstance(axes, list):
        raise ValueError("State axes must be a list")
    axis_ids: set[str] = set()
    lifecycle_count = 0
    classifier_count = 0
    value_count = 0
    required_common = {
        "axis_id",
        "axis_kind",
        "axis_version",
        "contract_ref",
        "owner_context",
        "transition_authority",
        "values",
        "initial_values",
        "terminal_values",
        "emitted_fact",
        "integration_events",
        "rejection_policy_ref",
        "transitions",
    }
    lifecycle_semantics = {
        "retry_semantics",
        "backward_semantics",
        "expiry_semantics",
        "cancellation_semantics",
        "revocation_semantics",
        "recovery_semantics",
    }
    transition_pattern = re.compile(
        r"^([A-Z][A-Z0-9_]*)>([A-Z][A-Z0-9_]*)@"
        r"([A-Z][A-Z0-9_]*)$"
    )
    for axis in axes:
        if not isinstance(axis, dict) or not required_common <= set(axis):
            raise ValueError("State axis row is not closed enough to compile")
        axis_id = axis["axis_id"]
        if (
            not isinstance(axis_id, str)
            or not re.fullmatch(
                r"(?:[A-Z][A-Za-z0-9]*|"
                r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*(?:\.[0-9]+)+)",
                axis_id,
            )
            or axis_id in axis_ids
        ):
            raise ValueError(f"Invalid or duplicate state axis: {axis_id}")
        axis_ids.add(axis_id)
        values = axis["values"]
        initial_values = axis["initial_values"]
        terminal_values = axis["terminal_values"]
        transitions = axis["transitions"]
        if (
            not isinstance(values, list)
            or not values
            or len(values) != len(set(values))
            or not all(
                isinstance(value, str)
                and re.fullmatch(r"[A-Z][A-Z0-9_]*", value)
                for value in values
            )
        ):
            raise ValueError(f"Invalid value catalog for {axis_id}")
        if (
            not isinstance(initial_values, list)
            or len(initial_values) != len(set(initial_values))
            or not set(initial_values) <= set(values)
            or not isinstance(terminal_values, list)
            or len(terminal_values) != len(set(terminal_values))
            or not set(terminal_values) <= set(values)
            or not isinstance(transitions, list)
        ):
            raise ValueError(f"Invalid state sets for {axis_id}")
        if axis["rejection_policy_ref"] != rejection["policy_id"]:
            raise ValueError(f"Wrong rejection policy for {axis_id}")
        event_refs = [
            *axis["integration_events"],
            *axis.get("referencing_events", []),
        ]
        if (
            not isinstance(axis["integration_events"], list)
            or not isinstance(axis.get("referencing_events", []), list)
            or len(event_refs) != len(set(event_refs))
            or not all(
                isinstance(event_name, str)
                and re.fullmatch(r"[A-Z][A-Za-z0-9]*", event_name)
                for event_name in event_refs
            )
        ):
            raise ValueError(f"Invalid integration-event set for {axis_id}")

        if axis["axis_kind"] == "CLASSIFIER":
            classifier_count += 1
            if set(axis) not in (
                required_common | {"transition_semantics"},
                required_common
                | {"transition_semantics", "referencing_events"},
            ):
                raise ValueError(
                    f"Classifier {axis_id} has unknown or missing fields"
                )
            if (
                initial_values
                or terminal_values
                or transitions
                or axis["transition_authority"] != "NONE"
                or axis["emitted_fact"] != "NOT_APPLICABLE"
                or not str(axis.get("transition_semantics", "")).startswith(
                    "NOT_APPLICABLE:"
                )
            ):
                raise ValueError(
                    f"Classifier {axis_id} claims lifecycle semantics"
                )
        elif axis["axis_kind"] == "LIFECYCLE":
            lifecycle_count += 1
            allowed_lifecycle_fields = (
                required_common
                | lifecycle_semantics
                | {
                    "nonterminal",
                    "outward_event_policy",
                    "referencing_events",
                }
            )
            if (
                not set(axis) <= allowed_lifecycle_fields
                or not required_common | lifecycle_semantics <= set(axis)
            ):
                raise ValueError(
                    f"Lifecycle {axis_id} has unknown or missing fields"
                )
            nonterminal = axis.get("nonterminal") is True
            if (
                (
                    "nonterminal" in axis
                    and axis["nonterminal"] is not True
                )
                or nonterminal == bool(terminal_values)
            ):
                raise ValueError(
                    f"Invalid terminality declaration for {axis_id}"
                )
            if (
                not lifecycle_semantics <= set(axis)
                or not initial_values
                or not transitions
                or axis["transition_authority"] == "NONE"
                or axis["emitted_fact"]
                != f"TransitionEventV1(axis_id={axis_id})"
            ):
                raise ValueError(
                    f"Lifecycle {axis_id} is not definition-complete"
                )
            edges: list[tuple[str, str]] = []
            edge_pairs: set[tuple[str, str]] = set()
            for transition in transitions:
                if not isinstance(transition, str):
                    raise ValueError(
                        f"Non-string transition in {axis_id}"
                    )
                match = transition_pattern.fullmatch(transition)
                if match is None:
                    raise ValueError(
                        f"Invalid transition notation {axis_id}:{transition}"
                    )
                source, target, _ = match.groups()
                pair = (source, target)
                if (
                    source not in values
                    or target not in values
                    or pair in edge_pairs
                    or source in terminal_values
                ):
                    raise ValueError(
                        f"Invalid lifecycle edge {axis_id}:{transition}"
                    )
                edge_pairs.add(pair)
                edges.append(pair)

            reachable = set(initial_values)
            while True:
                expanded = reachable | {
                    target
                    for source, target in edges
                    if source in reachable
                }
                if expanded == reachable:
                    break
                reachable = expanded
            if reachable != set(values):
                missing = ",".join(sorted(set(values) - reachable))
                raise ValueError(
                    f"Unreachable lifecycle values {axis_id}:{missing}"
                )
            if not nonterminal:
                can_reach_terminal = set(terminal_values)
                while True:
                    expanded = can_reach_terminal | {
                        source
                        for source, target in edges
                        if target in can_reach_terminal
                    }
                    if expanded == can_reach_terminal:
                        break
                    can_reach_terminal = expanded
                if can_reach_terminal != set(values):
                    missing = ",".join(
                        sorted(set(values) - can_reach_terminal)
                    )
                    raise ValueError(
                        f"No terminal route for {axis_id}:{missing}"
                    )
        else:
            raise ValueError(f"Unknown axis_kind for {axis_id}")
        value_count += len(values)

    declared = (
        catalog.get("axis_count"),
        catalog.get("lifecycle_axis_count"),
        catalog.get("classifier_axis_count"),
        catalog.get("value_count"),
    )
    actual = (
        len(axes),
        lifecycle_count,
        classifier_count,
        value_count,
    )
    if declared != actual:
        raise ValueError(
            f"State catalog denominator mismatch: {declared=} {actual=}"
        )
    return catalog


STATE_AXIS_CATALOG = parse_state_axis_catalog(read(ARCH_DOC))
STATE_AXES = {
    axis["axis_id"]: {
        "owner": axis["owner_context"],
        "values": copy.deepcopy(axis["values"]),
        "terminal": copy.deepcopy(axis["terminal_values"]),
        "axis_kind": axis["axis_kind"],
        "axis_version": axis["axis_version"],
        "contract_ref": axis["contract_ref"],
    }
    for axis in STATE_AXIS_CATALOG["axes"]
}
STATE_AXIS_CONTRACT_REFS = {
    axis["axis_id"]: axis["contract_ref"]
    for axis in STATE_AXIS_CATALOG["axes"]
}


def parse_marked_yaml_contract(
    text: str,
    begin_marker: str,
    end_marker: str,
    schema_version: str,
) -> dict[str, Any]:
    try:
        block = section(text, begin_marker, end_marker)
    except ValueError as exc:
        raise ValueError(
            f"Missing marked YAML contract: {schema_version}"
        ) from exc
    candidates = [
        load_yaml_text_strict(candidate)
        for candidate in re.findall(
            r"```yaml\s*\n(.*?)\n```",
            block,
            flags=re.DOTALL,
        )
    ]
    matching = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("schema_version") == schema_version
    ]
    if len(matching) != 1:
        raise ValueError(
            f"Expected one marked {schema_version} contract"
        )
    return matching[0]


def parse_transition_fact_contract(text: str) -> dict[str, Any]:
    contract = parse_marked_yaml_contract(
        text,
        "TRANSITION_FACT_CONTRACT_BEGIN",
        "TRANSITION_FACT_CONTRACT_END",
        "transition-fact-contract/v1",
    )
    if set(contract) != {
        "schema_version",
        "contract_id",
        "schema_ref",
        "canonicalization",
        "digest_algorithm",
        "additional_properties",
        "required_fields",
        "semantic_invariants",
        "idempotency_and_replay",
    }:
        raise ValueError("Transition-fact contract is not closed")
    if (
        contract["contract_id"] != "TRANSITION-EVENT-V1"
        or contract["schema_ref"]
        != "schemas/work/transition-event-v1.schema.json"
        or contract["canonicalization"] != "RFC8785"
        or contract["digest_algorithm"] != "SHA-256"
        or contract["additional_properties"] is not False
    ):
        raise ValueError("Transition-fact contract identity drift")
    field_rows = contract["required_fields"]
    if (
        not isinstance(field_rows, list)
        or not field_rows
        or any(set(row) != {"name", "type"} for row in field_rows)
        or len({row["name"] for row in field_rows})
        != len(field_rows)
        or not contract["semantic_invariants"]
    ):
        raise ValueError("Transition-fact field contract drift")
    replay = contract["idempotency_and_replay"]
    if (
        set(replay)
        != {
            "identity",
            "uniqueness",
            "replay_order",
            "version_rule",
            "gap_policy",
            "forbidden_field",
        }
        or replay["replay_order"]
        != [
            "owner_context",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version_after",
            "transition_id",
        ]
        or "transition_sequence" not in replay["forbidden_field"]
        or "before + 1" not in replay["version_rule"]
        or "need not be gap-free" not in replay["gap_policy"]
    ):
        raise ValueError("Transition-fact replay contract drift")
    return contract


def parse_artifact_legal_hold_contract(text: str) -> dict[str, Any]:
    contract = parse_marked_yaml_contract(
        text,
        "ARTIFACT_LEGAL_HOLD_CONTRACT_BEGIN",
        "ARTIFACT_LEGAL_HOLD_CONTRACT_END",
        "artifact-legal-hold-fact-contract/v1",
    )
    if set(contract) != {
        "schema_version",
        "contract_id",
        "schema_ref",
        "canonicalization",
        "digest_algorithm",
        "additional_properties",
        "required_fields",
        "semantic_invariants",
        "fixture_denominator",
    }:
        raise ValueError("Artifact legal-hold contract is not closed")
    if (
        contract["contract_id"] != "ARTIFACT-LEGAL-HOLD-FACT-V1"
        or contract["schema_ref"]
        != "schemas/artifacts/artifact-legal-hold-fact-v1.schema.json"
        or contract["canonicalization"] != "RFC8785"
        or contract["digest_algorithm"] != "SHA-256"
        or contract["additional_properties"] is not False
    ):
        raise ValueError("Artifact legal-hold contract identity drift")
    fields = contract["required_fields"]
    if (
        not isinstance(fields, list)
        or len(fields) != 16
        or len({field["name"] for field in fields}) != len(fields)
        or any(set(field) != {"name", "type"} for field in fields)
        or not contract["semantic_invariants"]
    ):
        raise ValueError("Artifact legal-hold field contract drift")
    denominator = contract["fixture_denominator"]
    expected_dimensions = [
        "APPLIED_WITH_PRIOR",
        "TERMINAL_WITHOUT_PRIOR",
        "PRIOR_NOT_CURRENT_APPLIED",
        "PRIOR_HOLD_MISMATCH",
        "PRIOR_ARTIFACT_ID_MISMATCH",
        "PRIOR_ARTIFACT_DIGEST_MISMATCH",
        "DUPLICATE_TERMINAL",
        "ACTION_ON_PURGED",
        "WRONG_OWNER",
        "WRONG_PRODUCER",
        "MISSING_OR_STALE_HUMAN_DECISION",
        "MISSING_OR_CONSUMED_AUTHORITY_GRANT",
        "PURGE_WHILE_HOLD_ACTIVE",
        "CONCURRENT_APPLY_PURGE_RACE",
        "HOLD_ACTION_MUTATES_ARTIFACT_STATUS",
    ]
    if (
        set(denominator)
        != {
            "valid_action_shapes",
            "required_field_omission_negative",
            "wrong_field_type_negative",
            "additional_property_negative",
            "semantic_negative",
            "semantic_negative_dimensions",
            "exact_case_count",
        }
        or denominator["valid_action_shapes"] != 3
        or denominator["required_field_omission_negative"]
        != len(fields)
        or denominator["wrong_field_type_negative"] != len(fields)
        or denominator["additional_property_negative"] != 1
        or denominator["semantic_negative_dimensions"]
        != expected_dimensions
        or denominator["semantic_negative"] != len(expected_dimensions)
        or denominator["exact_case_count"]
        != (
            denominator["valid_action_shapes"]
            + denominator["required_field_omission_negative"]
            + denominator["wrong_field_type_negative"]
            + denominator["additional_property_negative"]
            + denominator["semantic_negative"]
        )
    ):
        raise ValueError(
            "Artifact legal-hold fixture denominator drift"
        )
    return contract


def parse_state_event_fixture_denominator(text: str) -> dict[str, Any]:
    candidates = [
        load_yaml_text_strict(candidate)
        for candidate in re.findall(
            r"```yaml\s*\n(.*?)\n```",
            text,
            flags=re.DOTALL,
        )
    ]
    matching = [
        candidate
        for candidate in candidates
        if isinstance(candidate, dict)
        and candidate.get("schema_version")
        == "state-event-fixture-denominator/v1"
    ]
    if len(matching) != 1:
        raise ValueError(
            "Expected one state-event-fixture-denominator/v1 contract"
        )
    contract = matching[0]
    expected_top = {
        "schema_version",
        "state_catalog_shape",
        "transition_request_suite",
        "transition_fact_suite",
        "outward_edge_event_suite",
        "initial_state_event_suite",
        "reference_only_event_suite",
        "total_exact_cases",
    }
    if set(contract) != expected_top:
        raise ValueError("State/event fixture denominator is not closed")
    expected_sections = {
        "state_catalog_shape": {
            "lifecycle_axes",
            "classifier_axes",
            "ordered_nonself_lifecycle_pairs",
            "allowed_edges",
            "prohibited_pairs",
        },
        "transition_request_suite": {
            "allowed_edge_positive",
            "allowed_edge_unsatisfied_guard_negative",
            "prohibited_pair_negative",
            "wrong_owner_negative",
            "wrong_authority_negative",
            "stale_aggregate_version_negative",
            "missing_evidence_negative",
            "stale_evidence_negative",
            "wrong_recorded_prior_negative",
            "unknown_axis_negative",
            "unknown_lifecycle_from_value_negative",
            "unknown_lifecycle_to_value_negative",
            "classifier_mutation_negative",
            "exact_case_count",
        },
        "transition_fact_suite": {
            "schema_valid_positive",
            "wrong_axis_negative",
            "wrong_guard_negative",
            "wrong_catalog_digest_negative",
            "nonincrementing_aggregate_version_negative",
            "wrong_fact_digest_negative",
            "prohibited_pair_fact_negative",
            "wrong_recorded_prior_fact_negative",
            "required_field_omission_negative",
            "wrong_field_type_negative",
            "additional_property_negative",
            "exact_case_count",
        },
        "outward_edge_event_suite": {
            "valid_edge_binding_combinations",
            "wrong_axis_negative_per_valid_combination",
            "wrong_guard_negative_per_valid_combination",
            "wrong_transition_fact_ref_negative_per_valid_combination",
            "wrong_catalog_digest_negative_per_valid_combination",
            "aggregate_version_mismatch_negative_per_valid_combination",
            "wrong_binding_cardinality_negative_per_valid_combination",
            "event_specific_unlisted_pair_negative",
            "exact_case_count",
        },
        "initial_state_event_suite": {
            "valid_event_instances",
            "noninitial_value_negative",
            "wrong_axis_catalog_or_version_negative",
            "missing_required_binding_negative",
            "exact_case_count",
        },
        "reference_only_event_suite": {
            "valid_event_instances",
            "injected_initial_binding_negative",
            "injected_edge_binding_negative",
            "exact_case_count",
        },
    }
    for section_name, expected_fields in expected_sections.items():
        section_value = contract[section_name]
        if (
            not isinstance(section_value, dict)
            or set(section_value) != expected_fields
            or any(
                not isinstance(value, int) or value < 0
                for value in section_value.values()
            )
        ):
            raise ValueError(
                "State/event fixture denominator section drift: "
                + section_name
            )
    section_totals = [
        contract[name]["exact_case_count"]
        for name in (
            "transition_request_suite",
            "transition_fact_suite",
            "outward_edge_event_suite",
            "initial_state_event_suite",
            "reference_only_event_suite",
        )
    ]
    if (
        not isinstance(contract["total_exact_cases"], int)
        or contract["total_exact_cases"] != sum(section_totals)
    ):
        raise ValueError("State/event fixture total denominator drift")
    return contract


def parse_event_state_binding_catalog(
    text: str,
    state_catalog: dict[str, Any] | None = None,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    catalog = parse_marked_yaml_contract(
        text,
        "EVENT_STATE_BINDING_CONTRACT_BEGIN",
        "EVENT_STATE_BINDING_CONTRACT_END",
        "event-state-binding-contract/v1",
    )
    if set(catalog) != {
        "schema_version",
        "catalog_id",
        "event_count",
        "state_catalog_ref",
        "coverage_policy",
        "payload_overlays",
        "nested_types",
        "event_bindings",
        "validation_invariants",
    }:
        raise ValueError("Event-state binding catalog is not closed")
    if (
        catalog["catalog_id"] != "EVENT-STATE-BINDING-1.0"
        or catalog["state_catalog_ref"]
        != "architecture/contracts/states.json"
        or set(catalog["payload_overlays"])
        != {"INITIAL_STATE_FACT", "EDGE_EVENT", "REFERENCE_ONLY"}
        or set(catalog["nested_types"])
        != {"StateInitialBindingV1", "StateEdgeBindingRefV1"}
        or not catalog["validation_invariants"]
    ):
        raise ValueError("Event-state binding catalog identity drift")
    state_catalog = (
        parse_state_axis_catalog(text)
        if state_catalog is None
        else state_catalog
    )
    events = parse_event_catalog(text) if events is None else events
    axes = {
        axis["axis_id"]: axis for axis in state_catalog["axes"]
    }
    events_by_name = {
        event["event_name"]: event for event in events
    }
    bindings = catalog["event_bindings"]
    if (
        not isinstance(bindings, list)
        or len(bindings) != catalog["event_count"]
        or len(bindings) != len(events)
        or len({row["event_name"] for row in bindings})
        != len(bindings)
        or {row["event_name"] for row in bindings}
        != set(events_by_name)
    ):
        raise ValueError("Event-state event denominator drift")
    allowed_binding_fields = {
        "INITIAL_STATE_FACT": {
            "event_name",
            "binding_kind",
            "initial_bindings",
        },
        "EDGE_EVENT": {
            "event_name",
            "binding_kind",
            "edge_bindings",
        },
        "REFERENCE_ONLY": {
            "event_name",
            "binding_kind",
            "referenced_axis_ids",
        },
    }
    seen_edge_bindings: set[tuple[str, str, str]] = set()
    for binding in bindings:
        event_name = binding["event_name"]
        kind = binding["binding_kind"]
        if (
            kind not in allowed_binding_fields
            or set(binding) != allowed_binding_fields[kind]
        ):
            raise ValueError(
                "Event-state binding row is not closed: " + event_name
            )
        event_owner = events_by_name[event_name]["owner_context"]
        if kind == "INITIAL_STATE_FACT":
            rows = binding["initial_bindings"]
            if not rows:
                raise ValueError(
                    "Initial-state event has no binding: " + event_name
                )
            for row in rows:
                if set(row) != {
                    "axis_id",
                    "axis_version",
                    "initial_value",
                }:
                    raise ValueError(
                        "Initial-state binding is not closed: "
                        + event_name
                    )
                axis = axes.get(row["axis_id"])
                if (
                    axis is None
                    or axis["axis_kind"] != "LIFECYCLE"
                    or axis["axis_version"] != row["axis_version"]
                    or row["initial_value"]
                    not in axis["initial_values"]
                    or event_name not in axis["integration_events"]
                    or event_owner != axis["owner_context"]
                ):
                    raise ValueError(
                        "Invalid initial-state event binding: "
                        + event_name
                    )
        elif kind == "EDGE_EVENT":
            rows = binding["edge_bindings"]
            if not rows:
                raise ValueError(
                    "Edge event has no binding: " + event_name
                )
            for row in rows:
                if set(row) != {
                    "axis_id",
                    "axis_version",
                    "binding_cardinality",
                    "allowed_edges",
                }:
                    raise ValueError(
                        "Edge-event binding is not closed: "
                        + event_name
                    )
                axis = axes.get(row["axis_id"])
                if (
                    axis is None
                    or axis["axis_kind"] != "LIFECYCLE"
                    or axis["axis_version"] != row["axis_version"]
                    or row["binding_cardinality"] != "EXACTLY_ONE"
                    or not row["allowed_edges"]
                    or len(row["allowed_edges"])
                    != len(set(row["allowed_edges"]))
                    or not set(row["allowed_edges"])
                    <= set(axis["transitions"])
                    or event_name not in axis["integration_events"]
                    or event_owner != axis["owner_context"]
                ):
                    raise ValueError(
                        "Invalid edge-event binding: " + event_name
                    )
                for edge in row["allowed_edges"]:
                    binding_key = (event_name, row["axis_id"], edge)
                    if binding_key in seen_edge_bindings:
                        raise ValueError(
                            "Duplicate event-edge binding: "
                            + event_name
                        )
                    seen_edge_bindings.add(binding_key)
        else:
            referenced_axis_ids = binding["referenced_axis_ids"]
            if len(referenced_axis_ids) != len(
                set(referenced_axis_ids)
            ):
                raise ValueError(
                    "Duplicate reference-only axis: " + event_name
                )
            for axis_id in referenced_axis_ids:
                if (
                    axis_id not in axes
                    or event_name
                    not in axes[axis_id].get("referencing_events", [])
                ):
                    raise ValueError(
                        "Invalid reference-only event binding: "
                        + event_name
                        + ":"
                        + axis_id
                    )

    for axis in axes.values():
        for event_name in axis["integration_events"]:
            binding = next(
                row
                for row in bindings
                if row["event_name"] == event_name
            )
            if binding["binding_kind"] == "INITIAL_STATE_FACT":
                covered = {
                    row["axis_id"]
                    for row in binding["initial_bindings"]
                }
            elif binding["binding_kind"] == "EDGE_EVENT":
                covered = {
                    row["axis_id"]
                    for row in binding["edge_bindings"]
                }
            else:
                covered = set()
            if axis["axis_id"] not in covered:
                raise ValueError(
                    "Axis integration event lacks binding: "
                    + axis["axis_id"]
                    + ":"
                    + event_name
                )
        for event_name in axis.get("referencing_events", []):
            binding = next(
                row
                for row in bindings
                if row["event_name"] == event_name
            )
            if (
                binding["binding_kind"] != "REFERENCE_ONLY"
                or axis["axis_id"]
                not in binding["referenced_axis_ids"]
            ):
                raise ValueError(
                    "Axis referencing event lacks binding: "
                    + axis["axis_id"]
                    + ":"
                    + event_name
                )
    return catalog


def kebab_case(value: str) -> str:
    return re.sub(
        r"(?<=[a-z0-9])(?=[A-Z])",
        "-",
        value,
    ).lower()


def parse_event_enum_catalog(text: str) -> list[dict[str, Any]]:
    rows = markdown_table(
        section(
            text,
            "| Event enum name | Canonical axis/version and owner |",
            "`ALLOWED` is the only authorization value",
        )
    )
    if (
        len(rows) != 9
        or len({row[0] for row in rows}) != len(rows)
    ):
        raise ValueError("HERMES event enum catalog denominator/name drift")
    result: list[dict[str, Any]] = []
    for enum_name, binding_cell, values_cell in rows:
        owner_match = re.search(r";\s*([a-z_]+)\s*$", binding_cell)
        if owner_match is None:
            raise ValueError(
                "HERMES event enum owner missing: " + enum_name
            )
        owner_context = owner_match.group(1)
        if binding_cell.startswith("reuse states.json#"):
            binding_match = re.fullmatch(
                r"reuse (states\.json#([A-Za-z0-9]+)@([0-9.]+)); "
                r"([a-z_]+)",
                binding_cell,
            )
            if binding_match is None:
                raise ValueError(
                    "HERMES reused event enum binding malformed: "
                    + enum_name
                )
            binding_kind = "REUSED_STATE_AXIS"
            binding_ref = binding_match.group(1)
            axis_id = binding_match.group(2)
            axis_version = binding_match.group(3)
        else:
            binding_match = re.fullmatch(
                r"(ENUM-[A-Z0-9-]+-([0-9.]+)); ([a-z_]+)",
                binding_cell,
            )
            if binding_match is None:
                raise ValueError(
                    "HERMES new event enum binding malformed: "
                    + enum_name
                )
            binding_kind = "CANONICAL_EVENT_AXIS"
            binding_ref = binding_match.group(1)
            axis_id = enum_name
            axis_version = binding_match.group(2)
        values = re.findall(
            r"\b[A-Z][A-Z0-9_]*\b",
            values_cell.split(";", 1)[0],
        )
        if not values or len(values) != len(set(values)):
            raise ValueError(
                "HERMES event enum values missing/duplicated: " + enum_name
            )
        if axis_id not in STATE_AXES:
            raise ValueError(
                "HERMES event enum axis is not registered: " + axis_id
            )
        if not set(values) <= set(STATE_AXES[axis_id]["values"]):
            raise ValueError(
                "HERMES event enum contains unknown state values: "
                + enum_name
            )
        if (
            binding_kind == "CANONICAL_EVENT_AXIS"
            and values != STATE_AXES[axis_id]["values"]
        ):
            raise ValueError(
                "HERMES event enum/state registry value drift: " + enum_name
            )
        if STATE_AXES[axis_id]["owner"] != owner_context:
            raise ValueError(
                "HERMES event enum/state owner drift: " + enum_name
            )
        expected_binding_ref = STATE_AXIS_CONTRACT_REFS.get(
            axis_id,
            f"states.json#{axis_id}@1.0.0",
        )
        if binding_ref != expected_binding_ref:
            raise ValueError(
                "HERMES event enum canonical binding drift: " + enum_name
            )
        result.append(
            {
                "enum_name": enum_name,
                "binding_kind": binding_kind,
                "binding_ref": binding_ref,
                "axis_id": axis_id,
                "axis_version": axis_version,
                "owner_context": owner_context,
                "values": values,
                "source": (
                    "docs/architecture/"
                    "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#171-canonical-event-envelope-and-delivery-contract"
                ),
            }
        )
    return result


def parse_event_payload_fields(payload_cell: str) -> list[dict[str, Any]]:
    matches = list(
        re.finditer(
            r"`([a-z][a-z0-9_]*:[^`]+)`",
            payload_cell,
        )
    )
    if not matches:
        raise ValueError("HERMES event payload field list is empty")
    fields: list[dict[str, Any]] = []
    for index, match in enumerate(matches):
        field_spec = match.group(1)
        field_name, raw_type_expression = field_spec.split(":", 1)
        tail_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(payload_cell)
        )
        constraint_text = payload_cell[match.end():tail_end].strip(" ,")
        restriction_match = re.search(
            r"restricted by `([A-Za-z0-9]+)`",
            constraint_text,
        )
        restriction_enum_name = (
            restriction_match.group(1)
            if restriction_match is not None
            else None
        )
        type_expression = raw_type_expression
        constant: str | None = None
        if "=" in type_expression:
            type_expression, constant = type_expression.rsplit("=", 1)
            if re.fullmatch(r"[A-Z][A-Z0-9_]*", constant) is None:
                raise ValueError(
                    "HERMES event field constant malformed: " + field_spec
                )
        nullable = type_expression.endswith("?")
        if nullable:
            type_expression = type_expression[:-1]
        allow_empty_set = type_expression.endswith("[0..N]")
        if allow_empty_set:
            type_expression = type_expression[:-6]
        generic = re.fullmatch(
            r"(Id|Ref|Set|Enum)<([A-Za-z0-9]+)>",
            type_expression,
        )
        if generic is not None:
            type_kind = generic.group(1)
            type_parameter = generic.group(2)
        elif type_expression in {
            "ArtifactRef",
            "String",
            "Utc",
            "UInt",
            "Sha256",
            "Boolean",
        } or type_expression.endswith("Id"):
            type_kind = type_expression
            type_parameter = None
        else:
            raise ValueError(
                "HERMES event field type is unknown: " + field_spec
            )
        if allow_empty_set and type_kind != "Set":
            raise ValueError(
                "HERMES [0..N] marker is only legal on Set<T>: "
                + field_spec
            )
        fields.append(
            {
                "field_name": field_name,
                "source_type_expression": raw_type_expression,
                "type_kind": type_kind,
                "type_parameter": type_parameter,
                "nullable": nullable,
                "constant": constant,
                "allow_empty_set": allow_empty_set,
                "restriction_enum_name": restriction_enum_name,
                "source_constraint_text": constraint_text,
            }
        )
    field_names = [field["field_name"] for field in fields]
    if len(field_names) != len(set(field_names)):
        raise ValueError("HERMES event payload field name duplicated")
    return fields


def parse_event_catalog(text: str) -> list[dict[str, Any]]:
    block = section(
        text,
        "| Event ID / name | Owner / producer; consumers |",
        "The compiler projects these rows without semantic edits",
    )
    rows: list[dict[str, Any]] = []
    for line in block.splitlines():
        if not line.startswith("| `EVENT-"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 4:
            raise ValueError("HERMES event catalog row width drift")
        identity_match = re.fullmatch(
            r"`(EVENT-[A-Z0-9]+)` / `([A-Za-z0-9]+)`",
            cells[0],
        )
        if identity_match is None:
            raise ValueError("HERMES event identity cell malformed")
        event_id, event_name = identity_match.groups()
        if event_id != "EVENT-" + slug(event_name):
            raise ValueError("HERMES event ID/name mismatch: " + event_id)
        owner_tokens = re.findall(r"`([^`]+)`", cells[1])
        if len(owner_tokens) < 3:
            raise ValueError(
                "HERMES event owner/producer/consumer cell malformed: "
                + event_id
            )
        owner_context, producer_service_id, *consumer_contexts = owner_tokens
        aggregate_match = re.match(r"`([^`]+)`;\s*(.+)", cells[2])
        if aggregate_match is None:
            raise ValueError(
                "HERMES event aggregate/trigger cell malformed: " + event_id
            )
        rows.append(
            {
                "event_id": event_id,
                "event_name": event_name,
                "event_version": 1,
                "owner_context": owner_context,
                "producer_service_id": producer_service_id,
                "consumer_contexts": consumer_contexts,
                "aggregate_type": aggregate_match.group(1),
                "trigger_and_preconditions": aggregate_match.group(2),
                "required_payload_fields": parse_event_payload_fields(
                    cells[3]
                ),
                "source_catalog_cells": {
                    "event_id_and_name": cells[0],
                    "owner_producer_and_consumers": cells[1],
                    "aggregate_trigger_and_preconditions": cells[2],
                    "required_payload_fields": cells[3],
                },
            }
        )
    if len(rows) != 40:
        raise ValueError(
            f"HERMES event catalog denominator drift: {len(rows)}"
        )
    ids = [row["event_id"] for row in rows]
    names = [row["event_name"] for row in rows]
    if len(ids) != len(set(ids)) or len(names) != len(set(names)):
        raise ValueError("HERMES event catalog ID/name duplication")
    return rows


def event_nonempty_string_schema(*, max_length: int = 1024) -> dict[str, Any]:
    return {
        "type": "string",
        "minLength": 1,
        "maxLength": max_length,
        "pattern": r".*\S.*",
    }


def event_id_schema(id_type: str) -> dict[str, Any]:
    return {
        "type": "string",
        "minLength": 1,
        "maxLength": 255,
        "pattern": r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
        "x-ranex-id-type": id_type,
        "x-ranex-registered-opaque-id": True,
    }


def event_ref_schema(ref_type: str) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "id": event_id_schema(ref_type),
            "digest": {
                "type": "string",
                "pattern": r"^sha256:[0-9a-f]{64}$",
            },
        },
        "required": ["id", "digest"],
        "additionalProperties": False,
        "x-ranex-ref-type": ref_type,
    }


def event_payload_base_type_schema(
    type_name: str,
) -> dict[str, Any]:
    if type_name == "String":
        return event_nonempty_string_schema()
    if type_name == "Utc":
        return {
            "type": "string",
            "format": "date-time",
            "pattern": (
                r"^\d{4}-\d{2}-\d{2}T"
                r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
            ),
        }
    if type_name == "UInt":
        return {"type": "integer", "minimum": 0}
    if type_name == "Sha256":
        return {
            "type": "string",
            "pattern": r"^sha256:[0-9a-f]{64}$",
        }
    if type_name == "Boolean":
        return {"type": "boolean"}
    if type_name == "ArtifactRef":
        return event_ref_schema("Artifact")
    if type_name.endswith("Id"):
        return event_id_schema(type_name[:-2])
    raise ValueError("Unknown event payload base type: " + type_name)


def event_payload_field_schema(
    field: dict[str, Any],
    enum_catalog: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    type_kind = field["type_kind"]
    type_parameter = field["type_parameter"]
    if type_kind == "Id":
        schema = event_id_schema(type_parameter)
    elif type_kind == "Ref":
        schema = event_ref_schema(type_parameter)
    elif type_kind == "Set":
        item_schema = event_payload_base_type_schema(type_parameter)
        schema = {
            "type": "array",
            "items": item_schema,
            "minItems": 0 if field["allow_empty_set"] else 1,
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        }
    elif type_kind == "Enum":
        enum_name = field["restriction_enum_name"] or type_parameter
        if enum_name in enum_catalog:
            binding = enum_catalog[enum_name]
            if (
                field["restriction_enum_name"] is not None
                and binding["axis_id"] != type_parameter
            ):
                raise ValueError(
                    "Restricted event enum does not reuse named axis: "
                    + field["field_name"]
                )
            values = binding["values"]
            binding_ref = binding["binding_ref"]
        elif type_parameter in STATE_AXES:
            values = STATE_AXES[type_parameter]["values"]
            binding_ref = "states.json#" + type_parameter + "@1.0.0"
        else:
            raise ValueError(
                "Unknown event enum reference: " + type_parameter
            )
        schema = {
            "type": "string",
            "enum": values,
            "x-ranex-enum-binding": binding_ref,
        }
    else:
        schema = event_payload_base_type_schema(type_kind)
    if field["constant"] is not None:
        if schema.get("enum") is None or field["constant"] not in schema["enum"]:
            raise ValueError(
                "Event enum constant is not in the bound axis: "
                + field["field_name"]
                + "="
                + field["constant"]
            )
        schema = {
            **schema,
            "const": field["constant"],
        }
    if field["nullable"]:
        schema = {
            "oneOf": [
                schema,
                {"type": "null"},
            ]
        }
    return schema


def state_initial_binding_schema(
    state_registry: dict[str, Any],
) -> dict[str, Any]:
    lifecycle_axes = [
        axis
        for axis in state_registry["entries"]
        if axis["axis_kind"] == "LIFECYCLE"
    ]
    return {
        "type": "object",
        "properties": {
            "axis_id": {
                "type": "string",
                "enum": [axis["axis_id"] for axis in lifecycle_axes],
            },
            "axis_version": {
                "type": "string",
                "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$",
            },
            "state_catalog_digest": {
                "type": "string",
                "pattern": r"^sha256:[0-9a-f]{64}$",
            },
            "initial_value": {
                "type": "string",
                "enum": sorted(
                    {
                        value
                        for axis in lifecycle_axes
                        for value in axis["values"]
                    }
                ),
            },
            "aggregate_type": event_nonempty_string_schema(
                max_length=255
            ),
            "aggregate_id": event_id_schema("Aggregate"),
            "aggregate_version": {"type": "integer", "minimum": 0},
        },
        "required": [
            "axis_id",
            "axis_version",
            "state_catalog_digest",
            "initial_value",
            "aggregate_type",
            "aggregate_id",
            "aggregate_version",
        ],
        "additionalProperties": False,
        "x-ranex-nested-type": "StateInitialBindingV1",
    }


def state_edge_binding_ref_schema(
    state_registry: dict[str, Any],
) -> dict[str, Any]:
    lifecycle_axes = [
        axis
        for axis in state_registry["entries"]
        if axis["axis_kind"] == "LIFECYCLE"
    ]
    lifecycle_axis_pattern = "(?:" + "|".join(
        re.escape(axis["axis_id"]) for axis in lifecycle_axes
    ) + ")"
    return {
        "type": "object",
        "properties": {
            "axis_id": {
                "type": "string",
                "enum": [axis["axis_id"] for axis in lifecycle_axes],
            },
            "axis_version": {
                "type": "string",
                "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$",
            },
            "state_catalog_digest": {
                "type": "string",
                "pattern": r"^sha256:[0-9a-f]{64}$",
            },
            "edge_id": {
                "type": "string",
                "pattern": (
                    "^" + lifecycle_axis_pattern + ":"
                    r"[0-9]+\.[0-9]+\.[0-9]+:"
                    r"[A-Z][A-Z0-9_]*>[A-Z][A-Z0-9_]*@"
                    r"[A-Z][A-Z0-9_]*$"
                ),
            },
            "transition_fact_ref": event_ref_schema(
                "TransitionEvent"
            ),
        },
        "required": [
            "axis_id",
            "axis_version",
            "state_catalog_digest",
            "edge_id",
            "transition_fact_ref",
        ],
        "additionalProperties": False,
        "x-ranex-nested-type": "StateEdgeBindingRefV1",
    }


def event_payload_schema(
    event: dict[str, Any],
    enum_catalog: dict[str, dict[str, Any]],
    binding: dict[str, Any],
    state_registry: dict[str, Any],
) -> dict[str, Any]:
    properties = {
        field["field_name"]: event_payload_field_schema(
            field,
            enum_catalog,
        )
        for field in event["required_payload_fields"]
    }
    if binding["binding_kind"] == "INITIAL_STATE_FACT":
        properties["state_initial_bindings"] = {
            "type": "array",
            "items": state_initial_binding_schema(state_registry),
            "minItems": 1,
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        }
    elif binding["binding_kind"] == "EDGE_EVENT":
        properties["state_edge_bindings"] = {
            "type": "array",
            "items": state_edge_binding_ref_schema(state_registry),
            "minItems": 1,
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        }
    elif binding["binding_kind"] != "REFERENCE_ONLY":
        raise ValueError(
            "Unknown event-state binding kind: "
            + binding["binding_kind"]
        )
    owner_context = event["owner_context"]
    event_name = event["event_name"]
    relative = (
        "events/"
        + owner_context
        + "/"
        + kebab_case(event_name)
        + "-v1.schema.json"
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://schemas.ranex.dev/" + relative,
        "title": event_name + " event payload v1",
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
        "x-ranex-event-id": event["event_id"],
        "x-ranex-event-name": event_name,
        "x-ranex-event-version": 1,
        "x-ranex-payload-schema-ref": (
            "ranex:event-payload:" + event_name + ":v1"
        ),
        "x-ranex-state-binding": copy.deepcopy(binding),
        "x-ranex-state-binding-digest": (
            "sha256:" + sha256_bytes(canonical_bytes(binding))
        ),
        "x-ranex-source": (
            "docs/architecture/"
            "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#172-exact-initial-event-payload-catalog"
        ),
    }


def domain_event_envelope_schema(
    events: list[dict[str, Any]],
    payload_schemas: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    digest_schema = {
        "type": "string",
        "pattern": r"^sha256:[0-9a-f]{64}$",
    }
    nonempty = event_nonempty_string_schema()
    utc = event_payload_base_type_schema("Utc")
    properties: dict[str, Any] = {
        "schema_version": {"const": "domain-event-envelope/v1"},
        "event_id": nonempty,
        "event_name": nonempty,
        "event_version": {"const": 1},
        "event_instance_id": {
            "type": "string",
            "pattern": (
                r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
                r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
            ),
        },
        "owner_context": nonempty,
        "producer_service_id": nonempty,
        "producer_release_digest": digest_schema,
        "aggregate_type": nonempty,
        "aggregate_id": event_id_schema("Aggregate"),
        "source_aggregate_version": {"type": "integer", "minimum": 0},
        "aggregate_version": {"type": "integer", "minimum": 0},
        "aggregate_event_sequence": {"type": "integer", "minimum": 1},
        "subject_ref": nonempty,
        "subject_digest": digest_schema,
        "correlation_id": nonempty,
        "causation_id": nonempty,
        "idempotency_key": nonempty,
        "occurred_at": utc,
        "recorded_at": utc,
        "payload_schema_ref": nonempty,
        "payload_schema_digest": digest_schema,
        "payload": {"type": "object"},
        "data_classification": nonempty,
        "retention_policy_id": nonempty,
        "digest": digest_schema,
    }
    variants: list[dict[str, Any]] = []
    for event in events:
        relative = (
            "events/"
            + event["owner_context"]
            + "/"
            + kebab_case(event["event_name"])
            + "-v1.schema.json"
        )
        payload_schema = payload_schemas[relative]
        payload_digest = (
            "sha256:"
            + sha256_bytes(canonical_bytes(payload_schema))
        )
        variants.append(
            {
                "properties": {
                    "event_id": {"const": event["event_id"]},
                    "event_name": {"const": event["event_name"]},
                    "event_version": {"const": 1},
                    "owner_context": {
                        "const": event["owner_context"]
                    },
                    "producer_service_id": {
                        "const": event["producer_service_id"]
                    },
                    "aggregate_type": {
                        "const": event["aggregate_type"]
                    },
                    "payload_schema_ref": {
                        "const": (
                            "ranex:event-payload:"
                            + event["event_name"]
                            + ":v1"
                        )
                    },
                    "payload_schema_digest": {
                        "const": payload_digest
                    },
                    "payload": {
                        key: copy.deepcopy(payload_schema[key])
                        for key in (
                            "type",
                            "properties",
                            "required",
                            "additionalProperties",
                        )
                    },
                },
                "required": [
                    "event_id",
                    "event_name",
                    "event_version",
                    "owner_context",
                    "producer_service_id",
                    "aggregate_type",
                    "payload_schema_ref",
                    "payload_schema_digest",
                    "payload",
                ],
            }
        )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/events/"
            "domain-event-envelope-v1.schema.json"
        ),
        "title": "Ranex DomainEventEnvelopeV1",
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
        "allOf": [{"oneOf": variants}],
        "x-ranex-catalog-event-count": 40,
        "x-ranex-semantic-invariants": [
            "aggregate_version > source_aggregate_version",
            "occurred_at <= recorded_at",
            (
                "aggregate_event_sequence is gap-free under "
                "(owner_context,aggregate_type,aggregate_id)"
            ),
            (
                "event_instance_id is globally unique, immutable, "
                "and never reused"
            ),
            "digest is RFC8785 SHA-256 excluding digest",
            (
                "every Set<T> payload value is bytewise-sorted "
                "by its RFC8785 encoding"
            ),
            (
                "authenticated producer is owned by the exact "
                "catalog owner_context"
            ),
            (
                "data_classification is the maximum registered "
                "classification of subject and payload"
            ),
        ],
    }


def event_contract_schemas(
    state_registry: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    text = read(ARCH_DOC)
    events = parse_event_catalog(text)
    state_registry = (
        build_state_registry()
        if state_registry is None
        else state_registry
    )
    state_catalog = parse_state_axis_catalog(text)
    binding_catalog = parse_event_state_binding_catalog(
        text,
        state_catalog,
        events,
    )
    bindings_by_event = {
        row["event_name"]: row
        for row in binding_catalog["event_bindings"]
    }
    enum_rows = parse_event_enum_catalog(text)
    enum_catalog = {row["enum_name"]: row for row in enum_rows}
    payload_schemas: dict[str, dict[str, Any]] = {}
    for event in events:
        relative = (
            "events/"
            + event["owner_context"]
            + "/"
            + kebab_case(event["event_name"])
            + "-v1.schema.json"
        )
        payload_schemas[relative] = event_payload_schema(
            event,
            enum_catalog,
            bindings_by_event[event["event_name"]],
            state_registry,
        )
    envelope = domain_event_envelope_schema(events, payload_schemas)
    return {
        "events/domain-event-envelope-v1.schema.json": envelope,
        **payload_schemas,
    }


def build_event_registry(
    state_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = read(ARCH_DOC)
    events = parse_event_catalog(text)
    state_registry = (
        build_state_registry()
        if state_registry is None
        else state_registry
    )
    binding_catalog = parse_event_state_binding_catalog(
        text,
        parse_state_axis_catalog(text),
        events,
    )
    bindings_by_event = {
        row["event_name"]: row
        for row in binding_catalog["event_bindings"]
    }
    enum_bindings = parse_event_enum_catalog(text)
    schemas = event_contract_schemas(state_registry)
    envelope_path = "schemas/events/domain-event-envelope-v1.schema.json"
    envelope_schema = schemas[
        "events/domain-event-envelope-v1.schema.json"
    ]
    envelope_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(envelope_schema))
    )
    source_digest = "sha256:" + sha256_file(ARCH_DOC)
    entries: list[dict[str, Any]] = []
    for parsed in events:
        payload_relative = (
            "events/"
            + parsed["owner_context"]
            + "/"
            + kebab_case(parsed["event_name"])
            + "-v1.schema.json"
        )
        payload_schema = schemas[payload_relative]
        row = {
            "schema_version": "domain-event-contract/v1",
            **parsed,
            "state_binding": copy.deepcopy(
                bindings_by_event[parsed["event_name"]]
            ),
            "state_binding_digest": (
                "sha256:"
                + sha256_bytes(
                    canonical_bytes(
                        bindings_by_event[parsed["event_name"]]
                    )
                )
            ),
            "state_catalog_ref": binding_catalog[
                "state_catalog_ref"
            ],
            "state_catalog_digest": state_registry["digest"],
            "schema_status": "DEFINED_CONTRACT",
            "envelope_schema_ref": envelope_path,
            "envelope_schema_id": envelope_schema["$id"],
            "envelope_schema_digest": envelope_digest,
            "payload_schema_ref": (
                "ranex:event-payload:"
                + parsed["event_name"]
                + ":v1"
            ),
            "payload_schema_path": "schemas/" + payload_relative,
            "payload_schema_id": payload_schema["$id"],
            "payload_schema_digest": (
                "sha256:"
                + sha256_bytes(canonical_bytes(payload_schema))
            ),
            "delivery_contract": {
                "state_event_outbox_atomicity": "REQUIRED",
                "delivery": (
                    "AT_LEAST_ONCE_LOCAL_TRANSACTIONAL_OUTBOX"
                ),
                "durable_inbox_key": "event_instance_id",
                "duplicate_policy": (
                    "SAME_ID_SAME_BYTES_IDEMPOTENT_OTHERWISE_CONFLICT"
                ),
                "retry_identity_policy": (
                    "REUSE_SAME_EVENT_ID_AND_BYTES"
                ),
                "conflict_disposition": (
                    "QUARANTINE_AND_BLOCK_PROJECTION"
                ),
            },
            "ordering_contract": {
                "scope": (
                    "OWNER_CONTEXT_AGGREGATE_TYPE_AGGREGATE_ID"
                ),
                "sequence_field": "aggregate_event_sequence",
                "sequence_policy": "POSITIVE_GAP_FREE",
                "global_order_claim": "NONE",
            },
            "privacy_contract": {
                "classification_mode": "SUBJECT_DERIVED",
                "raw_secret_or_personal_content": "FORBIDDEN",
                "default_retention_policy_id": "RET-AUDIT-CONTROL-001",
                "stricter_registered_retention_overrides_default": True,
                "erasure_tombstone": (
                    "MINIMUM_NONIDENTIFYING_IDEMPOTENCY_AUDIT_FACT"
                ),
            },
            "compatibility_contract": {
                "version_1_payload": "IMMUTABLE",
                "compatible_change_requires": [
                    "FROZEN_OLD_AND_NEW_FIXTURES",
                    "TOTAL_DETERMINISTIC_UPCASTER",
                    "PRESERVED_EVENT_ID_AND_TERMINAL_MEANING",
                    "PRESERVED_AUTHORITY_CLASSIFICATION_EVIDENCE",
                ],
                "breaking_change_requires": "ADR_AND_NEW_EVENT_ID",
                "failed_upcast_disposition": "UNKNOWN_BLOCKING",
            },
            "replay_contract": {
                "aggregate_replay": "DETERMINISTIC",
                "external_effect_redispatch": "FORBIDDEN",
                "effect_dispatch_authority": (
                    "SEPARATE_PERMIT_AND_COMMITTED_INTENT"
                ),
                "failed_replay_disposition": "UNKNOWN_BLOCKING",
            },
            "runtime_emission_status": "NOT_ASSESSED",
            "runtime_delivery_status": "NOT_ASSESSED",
            "runtime_consumer_status": "NOT_ASSESSED",
            "runtime_upcast_status": "NOT_ASSESSED",
            "runtime_replay_status": "NOT_ASSESSED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": (
                "docs/architecture/"
                "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#172-exact-initial-event-payload-catalog"
            ),
            "source_file_digest": source_digest,
        }
        row["digest"] = digest_value(row)
        entries.append(row)
    return registry(
        "REG-EVENTS-001",
        "1.0.0",
        entries,
        event_count=40,
        schema_status="DEFINED_CONTRACT",
        envelope_schema_ref=envelope_path,
        envelope_schema_digest=envelope_digest,
        state_binding_catalog_id=binding_catalog["catalog_id"],
        state_binding_catalog_digest=(
            "sha256:"
            + sha256_bytes(canonical_bytes(binding_catalog))
        ),
        state_catalog_ref=binding_catalog["state_catalog_ref"],
        state_catalog_digest=state_registry["digest"],
        event_enum_bindings=enum_bindings,
        runtime_validation_status="NOT_ASSESSED",
    )


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
    if (
        not rules
        or len(rules)
        != len({rule["rule_id"] for rule in rules})
    ):
        raise ValueError(
            f"{prefix} machine-rule set is empty or duplicated"
        )
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
    fitness_block = section(
        text,
        "## Fitness evidence",
        "## Definition-freeze",
    )
    fitness_refs = re.findall(
        r"^\| `(FF-TDD-\d{3})` \|",
        fitness_block,
        flags=re.MULTILINE,
    )
    if (
        not fitness_refs
        or len(fitness_refs) != len(set(fitness_refs))
    ):
        raise ValueError(
            "ADR-0008 fitness IDs are empty or duplicated"
        )
    return {
        "rule_set_id": re.search(r'tdd_rule_set: "([^"]+)"', text).group(1),
        "allowed_root_names": roots,
        "rules": parse_inline_rule_set(TDD_ADR, "TDD"),
        "exception_classes": [
            {"exception_class": row[0], "required_substitution": row[1]}
            for row in exception_rows
        ],
        "fitness_refs": sorted(fitness_refs),
        "decision_binding": decision_binding(TDD_ADR, "ADR-0008"),
    }


def parse_tdd_health_contracts() -> dict[str, Any]:
    text = read(TDD_ADR)
    matching_blocks = [
        block
        for block in re.findall(
            r"```text\n(.*?)\n```",
            text,
            flags=re.DOTALL,
        )
        if "TddCycleRecordV1:" in block
    ]
    if len(matching_blocks) != 1:
        raise ValueError("ADR-0008 test-health contract block drift")
    contracts = yaml.safe_load(matching_blocks[0])
    expected = {
        "TddCycleRecordV1",
        "TddExceptionRecordV1",
        "TestQuarantineRecordV1",
        "TestDeletionRecordV1",
    }
    if set(contracts) != expected:
        raise ValueError("ADR-0008 test-health record class drift")
    for name, contract in contracts.items():
        fields = contract.get("fields")
        if (
            not isinstance(fields, list)
            or not fields
            or len(fields) != len(set(fields))
        ):
            raise ValueError(
                "ADR-0008 test-health field-set drift: " + name
            )
    return contracts


def parse_tdd_nested_type_catalog() -> dict[str, Any]:
    text = read(TDD_ADR)
    matching: list[dict[str, Any]] = []
    for block in re.findall(
        r"```yaml\s*\n(.*?)\n```",
        text,
        flags=re.DOTALL,
    ):
        parsed = load_yaml_text_strict(block)
        if (
            isinstance(parsed, dict)
            and parsed.get("schema_version")
            == "test-health-nested-type-catalog/v1"
        ):
            matching.append(parsed)
    if len(matching) != 1:
        raise ValueError(
            "Expected one ADR-0008 nested-type catalog"
        )
    catalog = matching[0]
    expected_keys = {
        "schema_version",
        "catalog_id",
        "additional_properties",
        "freshness_values",
        "change_profile_contract",
        "landing_record_status_authority",
        "cycle_landing_receipt_contract",
        "types",
        "top_level_record_types",
        "artifact_resolvers",
        "subject_projection_contract",
        "checker_result_dual_subject_contract",
        "reference_subject_roles",
        "record_field_bindings",
        "record_cross_field_invariants",
    }
    if (
        set(catalog) != expected_keys
        or catalog["catalog_id"] != "TDD-NESTED-TYPES-1.1"
        or catalog["additional_properties"] is not False
        or catalog["freshness_values"]
        != ["CURRENT", "STALE", "NOT_ASSESSED"]
    ):
        raise ValueError("ADR-0008 nested-type catalog drift")
    expected_profiles = {
        "BEHAVIOR_CHANGE": {
            "no_refactor_needed_false": [
                "RED",
                "GREEN",
                "REFACTOR",
                "ARCHITECTURE_CHECK",
            ],
            "no_refactor_needed_true": [
                "RED",
                "GREEN",
                "ARCHITECTURE_CHECK",
            ],
            "required_exception_class": None,
        },
        "DEFECT_FIX": {
            "no_refactor_needed_false": [
                "RED",
                "GREEN",
                "REFACTOR",
                "ARCHITECTURE_CHECK",
            ],
            "no_refactor_needed_true": [
                "RED",
                "GREEN",
                "ARCHITECTURE_CHECK",
            ],
            "required_exception_class": None,
        },
        "REFACTOR_ONLY": {
            "no_refactor_needed_false": [
                "BASELINE_GREEN",
                "REFACTOR",
                "ARCHITECTURE_CHECK",
            ],
            "no_refactor_needed_true": None,
            "required_exception_class": None,
        },
        "GENERATED_OUTPUT": {
            "no_refactor_needed_false": [
                "GENERATE",
                "VALIDATE",
                "ARCHITECTURE_CHECK",
            ],
            "no_refactor_needed_true": None,
            "required_exception_class": "GENERATED_OUTPUT",
        },
        "EMERGENCY_CONTAINMENT": {
            "no_refactor_needed_false": [
                "EMERGENCY_FIX",
                "VALIDATE",
                "ARCHITECTURE_CHECK",
            ],
            "no_refactor_needed_true": None,
            "required_exception_class": "EMERGENCY_CONTAINMENT",
        },
        "NON_EXECUTABLE_DOCUMENTATION": {
            "no_refactor_needed_false": [
                "DOCUMENTATION_CHECK",
                "ARCHITECTURE_CHECK",
            ],
            "no_refactor_needed_true": None,
            "required_exception_class": (
                "NON_EXECUTABLE_DOCUMENTATION"
            ),
        },
    }
    change_profiles = catalog["change_profile_contract"]
    if (
        set(change_profiles)
        != {"profile_count", "profiles", "invariants"}
        or change_profiles["profile_count"] != len(expected_profiles)
        or change_profiles["profiles"] != expected_profiles
        or not change_profiles["invariants"]
    ):
        raise ValueError("ADR-0008 change-profile contract drift")
    landing_contract = catalog["cycle_landing_receipt_contract"]
    landing_status_authority = catalog[
        "landing_record_status_authority"
    ]
    landing_fixtures = landing_contract.get(
        "fixture_requirements",
        {},
    )
    if (
        set(landing_contract)
        != {
            "contract_id",
            "cycle_schema_ref",
            "landing_schema_ref",
            "landing_status_authority_ref",
            "pre_landing_statuses",
            "gated_result",
            "derived_status",
            "prohibited_cycle_fields",
            "required_bindings",
            "invariants",
            "fixture_requirements",
        }
        or landing_contract["contract_id"]
        != "TDD-CYCLE-LANDING-RECEIPT-1.0"
        or landing_contract["cycle_schema_ref"]
        != "schemas/common/tdd-cycle-record-v1.schema.json"
        or landing_contract["landing_schema_ref"]
        != "schemas/execution/landing-record-v1.schema.json"
        or landing_contract["landing_status_authority_ref"]
        != landing_status_authority.get("authority_id")
        or set(landing_status_authority)
        != {
            "authority_id",
            "allowed_values",
            "success_literal",
            "schema_rule",
            "consumer_rule",
        }
        or landing_status_authority.get("authority_id")
        != "LANDING-RECORD-STATUS-1.0"
        or landing_status_authority.get("allowed_values")
        != ["SUCCEEDED"]
        or landing_status_authority.get("success_literal")
        != "SUCCEEDED"
        or not landing_status_authority.get("schema_rule")
        or not landing_status_authority.get("consumer_rule")
        or landing_contract["pre_landing_statuses"]
        != ["PROPOSED", "GATED", "REJECTED"]
        or landing_contract["gated_result"] != "PASS"
        or landing_contract["derived_status"] != "ACCEPTED"
        or landing_contract["prohibited_cycle_fields"]
        != ["landing_record_ref", "accepted_at", "landed_commit"]
        or not landing_contract["required_bindings"]
        or not landing_contract["invariants"]
        or set(landing_fixtures)
        != {
            "valid_join",
            "prohibited_cycle_field_negative",
            "missing_receipt_negative",
            "duplicate_receipt_negative",
            "failed_receipt_negative",
            "stale_receipt_negative",
            "wrong_subject_schema_negative",
            "wrong_subject_ref_negative",
            "wrong_subject_digest_negative",
            "wrong_candidate_negative",
            "pre_gate_time_negative",
            "wrong_legacy_landed_literal_negative",
            "null_status_negative",
            "unknown_status_negative",
            "nonterminal_status_negative",
            "exact_case_count",
        }
        or landing_fixtures["exact_case_count"]
        != sum(
            count
            for key, count in landing_fixtures.items()
            if key != "exact_case_count"
        )
    ):
        raise ValueError(
            "ADR-0008 cycle/landing receipt contract drift"
        )
    types = catalog["types"]
    if (
        not isinstance(types, list)
        or len(types) != 21
        or len({row["type_id"] for row in types}) != len(types)
    ):
        raise ValueError("ADR-0008 nested type IDs are invalid")
    known_type_ids = {row["type_id"] for row in types}
    primitive_type_ids = {
        "nonempty_string",
        "nonempty_versioned_schema_id",
        "safe_id",
        "safe_id_or_registered_urn",
        "safe_path",
        "semver",
        "sha1",
        "sha256",
        "sha256_without_prefix",
        "strict_utc",
        "uint",
    }
    for row in types:
        if set(row) != {
            "type_id",
            "type_version",
            "fields",
            "field_types",
            "cardinality",
            "invariants",
        }:
            raise ValueError(
                "ADR-0008 nested type row is not closed: "
                + str(row.get("type_id"))
            )
        fields = row["fields"]
        if (
            not isinstance(fields, list)
            or not fields
            or len(fields) != len(set(fields))
            or set(fields) != set(row["field_types"])
            or set(fields) != set(row["cardinality"])
            or not isinstance(row["invariants"], list)
            or not row["invariants"]
        ):
            raise ValueError(
                "ADR-0008 nested type fields drift: "
                + row["type_id"]
            )
        for field_name, field_type in row["field_types"].items():
            if isinstance(field_type, dict):
                if set(field_type) not in (
                    {"enum"},
                    {"integer"},
                    {"const"},
                    {"array_items_enum"},
                    {"enum_or_null"},
                ):
                    raise ValueError(
                        "ADR-0008 nested inline field type drift: "
                        + row["type_id"]
                        + "."
                        + field_name
                    )
                continue
            if not isinstance(field_type, str):
                raise ValueError(
                    "ADR-0008 nested field type is invalid: "
                    + row["type_id"]
                    + "."
                    + field_name
                )
            base_type = re.sub(
                r"(?:\[[^\]]*\]|\|null)$",
                "",
                field_type,
            )
            if (
                base_type not in known_type_ids
                and base_type not in primitive_type_ids
            ):
                raise ValueError(
                    "ADR-0008 nested field type is unknown: "
                    + field_type
                )
        if not all(
            cardinality
            in {"1", "0..1", "0..N", "1..N", "2..N", "1..4"}
            for cardinality in row["cardinality"].values()
        ):
            raise ValueError(
                "ADR-0008 nested cardinality drift: " + row["type_id"]
            )
    top_level_rows = catalog["top_level_record_types"]
    expected_record_contracts = parse_tdd_health_contracts()
    if (
        not isinstance(top_level_rows, list)
        or len(top_level_rows) != 4
        or len({row["type_id"] for row in top_level_rows})
        != len(top_level_rows)
        or {row["type_id"] for row in top_level_rows}
        != set(expected_record_contracts)
    ):
        raise ValueError("ADR-0008 top-level record denominator drift")
    top_by_id = {row["type_id"]: row for row in top_level_rows}
    for row in top_level_rows:
        if set(row) != {
            "type_id",
            "type_version",
            "additional_properties",
            "fields",
            "field_types",
            "cardinality",
            "invariants",
        }:
            raise ValueError(
                "ADR-0008 top-level record is not closed: "
                + str(row.get("type_id"))
            )
        fields = row["fields"]
        if (
            row["additional_properties"] is not False
            or not isinstance(fields, list)
            or not fields
            or len(fields) != len(set(fields))
            or fields
            != expected_record_contracts[row["type_id"]]["fields"]
            or set(fields) != set(row["field_types"])
            or set(fields) != set(row["cardinality"])
            or not row["invariants"]
        ):
            raise ValueError(
                "ADR-0008 top-level record field drift: "
                + row["type_id"]
            )
        for field_name, field_type in row["field_types"].items():
            if isinstance(field_type, dict):
                if set(field_type) not in (
                    {"enum"},
                    {"integer"},
                    {"const"},
                    {"array_items_enum"},
                    {"enum_or_null"},
                ):
                    raise ValueError(
                        "ADR-0008 top-level inline type drift: "
                        + row["type_id"]
                        + "."
                        + field_name
                    )
                continue
            if not isinstance(field_type, str):
                raise ValueError(
                    "ADR-0008 top-level field type invalid: "
                    + row["type_id"]
                    + "."
                    + field_name
                )
            base_type = re.sub(
                r"(?:\[[^\]]*\]|\|null)$",
                "",
                field_type,
            )
            if (
                base_type not in known_type_ids
                and base_type not in primitive_type_ids
            ):
                raise ValueError(
                    "ADR-0008 top-level field type unknown: "
                    + field_type
                )
        if not all(
            cardinality
            in {"1", "0..1", "0..N", "1..N", "2..N", "1..4"}
            for cardinality in row["cardinality"].values()
        ):
            raise ValueError(
                "ADR-0008 top-level cardinality drift: "
                + row["type_id"]
            )
    if sum(len(row["fields"]) for row in top_level_rows) != 159:
        raise ValueError("ADR-0008 top-level field denominator drift")

    projection_contract = catalog["subject_projection_contract"]
    if set(projection_contract) != {
        "contract_id",
        "canonicalization",
        "digest_algorithm",
        "digest_encoding",
        "projection_rule",
        "output_type_rule",
        "canonicalization_example",
        "nested_projection_types",
        "projections",
        "fixture_requirements",
    }:
        raise ValueError("ADR-0008 subject projection is not closed")
    if (
        projection_contract["contract_id"]
        != "TDD-CANONICAL-SUBJECT-PROJECTIONS-1.1"
        or projection_contract["canonicalization"] != "RFC8785"
        or projection_contract["digest_algorithm"] != "SHA-256"
        or projection_contract["output_type_rule"].get(
            "additional_properties"
        )
        is not False
        or not projection_contract["projection_rule"]
    ):
        raise ValueError("ADR-0008 subject projection identity drift")
    nested_projection_types = projection_contract[
        "nested_projection_types"
    ]
    if set(nested_projection_types) != {"TddCycleStepClaimV1"}:
        raise ValueError(
            "ADR-0008 nested subject projection type drift"
        )
    step_claim = nested_projection_types["TddCycleStepClaimV1"]
    cycle_step = next(
        row for row in types if row["type_id"] == "TddCycleStepV1"
    )
    if (
        set(step_claim)
        != {
            "additional_properties",
            "fields",
            "source_fields",
            "excluded_source_fields",
            "invariant",
        }
        or step_claim["additional_properties"] is not False
        or step_claim["fields"] != step_claim["source_fields"]
        or set(step_claim["source_fields"])
        | set(step_claim["excluded_source_fields"])
        != set(cycle_step["fields"])
        or set(step_claim["source_fields"])
        & set(step_claim["excluded_source_fields"])
    ):
        raise ValueError(
            "ADR-0008 nested subject projection partition drift"
        )
    projections = projection_contract["projections"]
    if (
        not isinstance(projections, list)
        or len(projections) != 4
        or len({row["projection_id"] for row in projections}) != 4
        or {row["source_record_type"] for row in projections}
        != set(top_by_id)
    ):
        raise ValueError("ADR-0008 subject projection denominator drift")
    expected_projection_fields = {
        "projection_id",
        "subject_schema",
        "schema_ref",
        "source_record_type",
        "subject_ref_rule",
        "output_fields",
        "direct_included_source_fields",
        "transformed_source_fields",
        "excluded_source_fields",
    }
    for projection in projections:
        record_type = projection["source_record_type"]
        if set(projection) != expected_projection_fields:
            raise ValueError(
                "ADR-0008 projection row is not closed: "
                + projection["projection_id"]
            )
        direct = projection["direct_included_source_fields"]
        transformed = projection["transformed_source_fields"]
        excluded = projection["excluded_source_fields"]
        transformed_sources = [
            source
            for transform in transformed.values()
            for source in transform["sources"]
        ]
        partitions = [*direct, *transformed_sources, *excluded]
        if (
            projection["output_fields"][:2]
            != ["subject_schema", "subject_ref"]
            or set(projection["output_fields"][2:])
            != set(direct) | set(transformed)
            or len(projection["output_fields"])
            != len(set(projection["output_fields"]))
            or len(partitions) != len(set(partitions))
            or set(partitions) != set(top_by_id[record_type]["fields"])
            or not projection["schema_ref"].startswith(
                "schemas/common/"
            )
        ):
            raise ValueError(
                "ADR-0008 projection source/output partition drift: "
                + projection["projection_id"]
            )
        for output_field, transform in transformed.items():
            if set(transform) != {
                "sources",
                "transform",
                "output_type",
                "output_cardinality",
            }:
                raise ValueError(
                    "ADR-0008 transformed projection drift: "
                    + projection["projection_id"]
                    + "."
                    + output_field
                )
    fixtures = projection_contract["fixture_requirements"]
    if (
        set(fixtures)
        != {
            "projection_ids",
            "per_projection",
            "validator_requirement",
        }
        or fixtures["projection_ids"]
        != [row["projection_id"] for row in projections]
        or not fixtures["per_projection"]
    ):
        raise ValueError(
            "ADR-0008 projection fixture denominator drift"
        )

    checker_contract = catalog[
        "checker_result_dual_subject_contract"
    ]
    expected_checker_keys = {
        "contract_id",
        "reference_path_expansion",
        "checker_result_top_level_additional_properties",
        "checker_result_top_level_fields",
        "top_level_claim_fields",
        "failure_fingerprint_field",
        "execution_subject_path",
        "execution_subject_schema_ref",
        "execution_subject_additional_properties",
        "execution_subject_required_fields",
        "execution_fields",
        "commit_resolver",
        "global_invariants",
        "role_predicates",
        "negative_fixture_requirements",
    }
    if (
        set(checker_contract) != expected_checker_keys
        or checker_contract["contract_id"]
        != "CHECKER-CLAIM-EXECUTION-SUBJECT-1.1"
        or checker_contract[
            "checker_result_top_level_additional_properties"
        ]
        is not False
        or checker_contract[
            "execution_subject_additional_properties"
        ]
        is not False
        or checker_contract["execution_subject_path"] != "/subject"
        or checker_contract["execution_subject_schema_ref"]
        != "schemas/assurance/checker-execution-subject-v1.schema.json"
        or set(checker_contract["top_level_claim_fields"])
        != {"subject_schema", "subject_ref", "subject_digest"}
        or checker_contract["failure_fingerprint_field"]
        != {
            "path": "/failure_fingerprint",
            "type": "ExpectedFailureFingerprintV1|null",
            "cardinality": "0..1",
            "red_rule": (
                "nonnull and exactly equal to the containing RED "
                "step expected_failure_fingerprint"
            ),
            "non_red_rule": "null",
        }
        or len(checker_contract["checker_result_top_level_fields"])
        != 21
        or len(checker_contract["execution_subject_required_fields"])
        != 32
        or not checker_contract["global_invariants"]
    ):
        raise ValueError("ADR-0008 checker dual-subject drift")
    checker_template = load_yaml_text_strict(
        read(TEMPLATES / "CHECKER_RESULT.yaml")
    )
    if (
        list(checker_template)
        != checker_contract["checker_result_top_level_fields"]
        or list(checker_template["subject"])
        != checker_contract["execution_subject_required_fields"]
    ):
        raise ValueError(
            "CHECKER_RESULT template does not project the exact "
            "ADR-0008 dual-subject field manifests"
        )
    roles = checker_contract["role_predicates"]
    role_fields = {
        "role_id",
        "record_type",
        "reference_paths",
        "claim_subject",
        "execution_base_commit",
        "execution_candidate_commit",
        "execution_artifact_digest",
        "execution_test_profile",
        "execution_release_profile",
    }
    if (
        len(roles) != 6
        or len({role["role_id"] for role in roles}) != 6
        or any(
            set(role) != role_fields
            or role["record_type"] not in top_by_id
            or not role["reference_paths"]
            for role in roles
        )
        or not checker_contract["negative_fixture_requirements"]
    ):
        raise ValueError(
            "ADR-0008 checker role predicate denominator drift"
        )
    artifact_types: set[str] = set()
    for resolver in catalog["artifact_resolvers"]:
        if set(resolver) != {
            "artifact_type",
            "schema_path",
            "artifact_id_pointer",
            "digest_pointer",
            "subject_pointers",
            "producer_pointers",
            "time_pointers",
            "eligibility",
        }:
            raise ValueError("ADR-0008 artifact resolver is not closed")
        artifact_type = resolver["artifact_type"]
        if artifact_type in artifact_types:
            raise ValueError(
                "ADR-0008 duplicate artifact resolver: "
                + artifact_type
            )
        artifact_types.add(artifact_type)
        if (
            set(resolver["subject_pointers"])
            != {"subject_schema", "subject_ref", "subject_digest"}
            or not resolver["eligibility"]
        ):
            raise ValueError(
                "ADR-0008 artifact resolver subject drift: "
                + artifact_type
            )
    if artifact_types != {
        "checker_result",
        "evidence_snapshot",
        "gate_evaluation",
        "human_decision",
        "review_verdict",
    }:
        raise ValueError("ADR-0008 artifact resolver set drift")
    record_types = set(parse_tdd_health_contracts())
    reference_roles = catalog["reference_subject_roles"]
    if len(reference_roles) != 7:
        raise ValueError(
            "ADR-0008 reference-role denominator drift"
        )
    for role in reference_roles:
        if (
            set(role)
            != {"record_type", "reference_role", "expected_subject"}
            or role["record_type"] not in record_types
        ):
            raise ValueError("ADR-0008 reference-role drift")
    record_bindings = catalog["record_field_bindings"]
    if (
        len(record_bindings) != 4
        or {
            binding.get("record_type")
            for binding in record_bindings
        }
        != record_types
    ):
        raise ValueError(
            "ADR-0008 record-field binding denominator drift"
        )
    for binding in record_bindings:
        if (
            set(binding) != {"record_type", "fields"}
            or binding["record_type"] not in record_types
            or not isinstance(binding["fields"], dict)
        ):
            raise ValueError("ADR-0008 record-field binding drift")
        for type_spec in binding["fields"].values():
            base_type = re.sub(
                r"(?:\[[^\]]+\]|\|null)$",
                "",
                type_spec,
            )
            if base_type not in known_type_ids:
                raise ValueError(
                    "ADR-0008 record field uses unknown type: "
                    + type_spec
                )
    if not catalog["record_cross_field_invariants"]:
        raise ValueError("ADR-0008 cross-field invariants are empty")
    return catalog


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


def parse_adr10_legacy_record_contract() -> dict[str, Any]:
    if sha256_file(LEGACY_TEST_LAYOUT_ADR) != ADR10_SOURCE_SHA256:
        raise ValueError("ADR-0010 source digest drift")
    text = read(LEGACY_TEST_LAYOUT_ADR)
    matches = re.findall(
        (
            r"<!-- BEGIN ADR10 LEGACY TEST RECORD CONTRACT -->"
            r"\s*```yaml\n(.*?)\n```\s*"
            r"<!-- END ADR10 LEGACY TEST RECORD CONTRACT -->"
        ),
        text,
        flags=re.DOTALL,
    )
    if len(matches) != 1:
        raise ValueError(
            "ADR-0010 marked legacy-record contract count drift"
        )
    if (
        hashlib.sha256(matches[0].encode("utf-8")).hexdigest()
        != ADR10_MACHINE_BLOCK_SHA256
    ):
        raise ValueError("ADR-0010 marked contract digest drift")
    wrapper = load_yaml_text_strict(matches[0])
    if set(wrapper) != {"legacy_test_record_contract"}:
        raise ValueError(
            "ADR-0010 marked legacy-record contract wrapper drift"
        )
    contract = wrapper["legacy_test_record_contract"]
    expected_keys = {
        "contract_id",
        "contract_version",
        "canonicalization",
        "digest_algorithm",
        "digest_encoding",
        "source_record_encoding",
        "additional_properties",
        "inherited_type_authority",
        "scalar_types",
        "cardinality_rule",
        "set_order_rule",
        "compatibility_impact",
        "nested_types",
        "record_catalog",
        "subject_projection_contract",
        "artifact_role_resolvers",
        "nonartifact_reference_resolvers",
        "landing_record_role",
        "sealing_validation_role",
        "self_reference_prohibition",
        "chronology_freshness_and_authority",
        "sibling_bindings",
    }
    if (
        set(contract) != expected_keys
        or contract["contract_id"]
        != "ADR10-LEGACY-TEST-RECORDS-2.0"
        or contract["contract_version"] != "2.0.0"
        or contract["canonicalization"] != "RFC8785"
        or contract["digest_algorithm"] != "SHA-256"
        or contract["additional_properties"] is not False
    ):
        raise ValueError("ADR-0010 marked contract identity drift")
    compatibility = contract["compatibility_impact"]
    if (
        compatibility.get("predecessor_contract_id")
        != "ADR10-LEGACY-TEST-RECORDS-1.0"
        or compatibility.get("predecessor_contract_version") != "1.0.0"
        or compatibility.get("change_class") != "BREAKING_MAJOR"
        or len(compatibility.get("breaking_bindings", [])) != 14
    ):
        raise ValueError(
            "ADR-0010 breaking-major compatibility drift"
        )
    nested = contract["nested_types"]
    expected_nested_type_ids = {
        "LegacyChangeRowV1",
        "LegacyDestinationRowV1",
        "ClassificationAuthorityBindingV1",
        "DirectSourceClassificationV2",
        "TestBehaviorAuthorityRowV1",
        "DirectSourceClassificationAuthorityRowV1",
        "LegacyMemberManifestRowV2",
        "LegacyTestScopeAuthorityRowV2",
        "LegacyRecordSourceManifestRowV1",
        "LegacyDispositionStateRowV1",
        "LegacyResultingTestRowV1",
        "LegacyOrderedMigrationSubsetRowV2",
        "LegacyTestLineageRowV1",
        "LegacyDeltaContentRowV1",
        "LegacyTestsDeltaRowV1",
    }
    if (
        len(nested) != 15
        or {row["type_id"] for row in nested}
        != expected_nested_type_ids
    ):
        raise ValueError("ADR-0010 nested-type denominator drift")
    for row in nested:
        if (
            row.get("additional_properties") is not False
            or not row.get("fields")
            or len(row["fields"]) != len(set(row["fields"]))
            or set(row["fields"]) != set(row["field_types"])
            or not set(row.get("nullable_fields", []))
            <= set(row["fields"])
            or not set(row.get("array_cardinalities", {}))
            <= set(row["fields"])
        ):
            raise ValueError(
                "ADR-0010 nested-type field drift: "
                + str(row.get("type_id"))
            )
    scope_row = next(
        row
        for row in nested
        if row["type_id"] == "LegacyTestScopeAuthorityRowV2"
    )
    expected_scope_row_fields = [
        "policy_id",
        "policy_version",
        "baseline_id",
        "baseline_file_manifest_sha256",
        "affected_scope_id",
        "scope_kind",
        "source_match_kind",
        "source_root",
        "source_population_digest",
        "destination_rule_kind",
        "destination_root",
        "compatibility_owner",
        "migration_owner",
        "test_governance_owner",
        "expires_at",
    ]
    if (
        scope_row["fields"] != expected_scope_row_fields
        or scope_row["nullable_fields"] != ["destination_root"]
        or scope_row["array_cardinalities"]
        or len(scope_row.get("invariants", [])) != 2
        or scope_row["field_types"]["destination_root"]
        != "safe_path|null"
        or scope_row["field_types"]["source_population_digest"]
        != "sha256"
    ):
        raise ValueError("ADR-0010 scope-authority row drift")
    record_counts = {
        "TestBehaviorAuthorityV1": 23,
        "DirectSourceClassificationAuthorityV1": 30,
        "LegacyTestChangeExceptionV2": 45,
        "LegacyTestMigrationRecordV2": 59,
        "LegacyTestCutoverRemovalRecordV2": 44,
    }
    records = contract["record_catalog"]
    if (
        {row["type_id"]: len(row["fields"]) for row in records}
        != record_counts
    ):
        raise ValueError("ADR-0010 record denominator drift")
    for row in records:
        fields = row["fields"]
        if (
            row.get("additional_properties") is not False
            or len(fields) != len(set(fields))
            or set(fields) != set(row["field_types"])
            or not set(row.get("nullable_fields", [])) <= set(fields)
            or not set(row.get("array_cardinalities", {}))
            <= set(fields)
        ):
            raise ValueError(
                "ADR-0010 record field drift: " + row["type_id"]
            )
    change_record = next(
        row
        for row in records
        if row["type_id"] == "LegacyTestChangeExceptionV2"
    )
    if (
        "direct_source_classification"
        not in change_record["fields"]
        or change_record["field_types"][
            "direct_source_classification"
        ]
        != "DirectSourceClassificationV2|null"
        or "direct_source_classification"
        not in change_record["nullable_fields"]
        or not any(
            "nonnull exactly for LEGACY-TEST-TOPLEVEL-001"
            in invariant
            and "null for every fixed-root" in invariant
            for invariant in change_record.get("invariants", [])
        )
    ):
        raise ValueError(
            "ADR-0010 change direct-classification branch drift"
        )
    projection_counts = {
        "TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1": 15,
        "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1": 22,
        "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2": 33,
        "LEGACY_TEST_MIGRATION_MEMBER_SUBJECT_V2": 37,
        "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2": 24,
        "LEGACY_TEST_CUTOVER_SUBJECT_V2": 25,
    }
    projections = contract["subject_projection_contract"][
        "projections"
    ]
    if {
        row["projection_id"]: len(row["output_fields"])
        for row in projections
    } != projection_counts:
        raise ValueError("ADR-0010 projection denominator drift")
    change_projection = next(
        row
        for row in projections
        if row["projection_id"]
        == "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2"
    )
    if (
        change_projection.get("transformed_source_fields") != {}
        or "direct_source_classification"
        not in change_projection["output_fields"]
        or "direct_source_classification"
        not in change_projection["direct_included_source_fields"]
        or "direct_source_classification"
        in change_projection["excluded_source_fields"]
    ):
        raise ValueError(
            "ADR-0010 change subject classification projection drift"
        )
    artifact_roles = contract["artifact_role_resolvers"]["roles"]
    if (
        len(artifact_roles) != 30
        or len(
            {
                (
                    row["record_type"],
                    row["reference_path"],
                    row["role"],
                )
                for row in artifact_roles
            }
        )
        != 30
        or not all(
            any(
                all(row.get(key) == value for key, value in expected.items())
                for row in artifact_roles
            )
            for expected in (
                {
                    "record_type": "TestBehaviorAuthorityV1",
                    "reference_path": "/owner_decision_ref",
                    "artifact_type": "human_decision",
                    "expected_subject": "TEST_BEHAVIOR_AUTHORITY_SUBJECT_V1",
                    "role": "TEST_BEHAVIOR_OWNER",
                    "action": "REGISTER_TEST_BEHAVIOR",
                    "outcome": "ALLOW",
                    "active_cardinality": "1",
                },
                {
                    "record_type": "DirectSourceClassificationAuthorityV1",
                    "reference_path": "/classification_decision_ref",
                    "artifact_type": "human_decision",
                    "expected_subject": (
                        "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY_SUBJECT_V1"
                    ),
                    "role": "TEST_CLASSIFICATION_OWNER",
                    "action": "ALLOW_DIRECT_LEGACY_TEST_CLASSIFICATION",
                    "outcome": "ALLOW",
                    "active_cardinality": "1",
                },
            )
        )
    ):
        raise ValueError("ADR-0010 artifact-role denominator drift")
    nonartifact = contract["nonartifact_reference_resolvers"]
    classification_authority = nonartifact.get(
        "direct_source_classification_authority"
    )
    scope_authority = nonartifact.get("scope_destination_authority")
    expected_classification_authority_keys = {
        "authority_id",
        "authority_record_type",
        "authority_subject_projection",
        "authority_source_pattern",
        "authority_registry",
        "authority_catalog_row_type",
        "behavior_record_type",
        "behavior_subject_projection",
        "behavior_source_pattern",
        "behavior_registry",
        "behavior_catalog_row_type",
        "live_initial_behavior_population",
        "authoring_templates",
        "source_bijection",
        "authority_bindings",
        "subject_and_decision",
        "cardinality",
        "lifecycle",
        "compatibility",
        "call_path_invariant",
        "positive_fixture_requirements",
        "negative_fixture_requirements",
    }
    expected_classification_cardinality_keys = {
        "behavior_row",
        "authority_source",
        "authority_for_scope_source_at_observation",
        "decision",
        "landing_record",
        "direct_change_resolution",
        "direct_migration_member_resolution",
    }
    expected_classification_positive_ids = {
        "active_landed_behavior_and_direct_change_authority",
        "active_landed_behavior_and_direct_migration_authority",
        (
            "active_superseding_authority_invalidates_predecessor_"
            "and_authorizes_successor"
        ),
    }
    expected_classification_negative_ids = {
        "missing_authority_source",
        "duplicate_authority_source",
        "wrong_authority_source_path_or_filename",
        "authority_source_digest_mismatch",
        "authority_registry_source_bijection_failure",
        "wrong_baseline_scope_or_source",
        "missing_behavior_row",
        "wrong_or_stale_behavior_version",
        "behavior_source_or_row_digest_mismatch",
        "behavior_expired_revoked_or_superseded",
        "missing_behavior_decision",
        "behavior_decision_wrong_subject",
        "behavior_decision_wrong_role_action_or_outcome",
        "behavior_decision_digest_ref_mismatch",
        "missing_binding_role",
        "duplicate_binding_role",
        "authority_binding_order_wrong",
        "wrong_registry_id_version_or_ref",
        "registry_digest_mismatch",
        "row_ref_missing_or_wrong",
        "row_digest_mismatch",
        "context_behavior_mismatch",
        "capability_behavior_mismatch",
        "ownership_context_mismatch",
        "lane_category_mismatch",
        "test_lane_bound_to_profile_not_taxonomy_registry",
        "taxonomy_mirror_pattern_mismatch",
        "nondeterministic_destination_root",
        "missing_classification_decision",
        "decision_wrong_subject",
        "decision_wrong_role_action_or_outcome",
        "classification_decision_digest_ref_mismatch",
        "decision_not_approved_revoked_or_superseded",
        "decision_or_authority_expired_or_not_yet_valid",
        "conflicting_or_superseding_classification",
        "behavior_authority_landing_omitted",
        "classification_authority_landing_omitted_or_failed",
        "classification_authority_landing_wrong_subject",
        "sealing_behavior_registry_digest_wrong_or_omitted",
        "sealing_classification_registry_digest_wrong_or_omitted",
        "transition_mapping_or_authority_digest_mismatch",
        "direct_change_resolver_omitted",
        "direct_migration_resolver_omitted",
        "synthetic_fixture_claimed_as_live_authority",
    }
    classification_positive_requirements = (
        classification_authority.get(
            "positive_fixture_requirements",
            {},
        )
        if isinstance(classification_authority, dict)
        else {}
    )
    classification_positive_counts = {
        key: value
        for key, value in classification_positive_requirements.items()
        if key != "exact_positive_case_count"
    }
    classification_negative_requirements = (
        classification_authority.get(
            "negative_fixture_requirements",
            {},
        )
        if isinstance(classification_authority, dict)
        else {}
    )
    classification_negative_counts = {
        key: value
        for key, value in classification_negative_requirements.items()
        if key != "exact_negative_case_count"
    }
    expected_scope_authority_keys = {
        "authority_id",
        "source_authority",
        "normalized_row_type",
        "subject_schema",
        "subject_ref_rule",
        "subject_digest_rule",
        "cardinality",
        "freshness",
        "predicates",
        "positive_fixture_requirements",
        "negative_fixture_requirements",
    }
    expected_scope_cardinality_keys = {
        "scope_row_per_affected_scope_id",
        "scope_match_per_baseline_source_path",
        "change_source_path",
        "migration_source_path_per_member",
        "fixed_destination_root",
        "classification_destination_root",
        "destination_rows",
    }
    expected_scope_negative_ids = {
        "unknown_scope_id",
        "missing_scope_row",
        "duplicate_scope_row",
        "wrong_scope_for_source_path",
        "overlapping_scope_match",
        "baseline_population_digest_mismatch",
        "stale_or_wrong_policy_binding",
        "expired_scope",
        "fixed_destination_outside_root",
        "migration_missing_or_wrong_classification_root",
        "change_missing_classification",
        "change_wrong_classification_root",
        "change_stale_classification",
        "change_cross_subject_classification",
        "noncanonical_or_non_py_destination",
        "path_traversal_or_legacy_recontamination",
        "duplicate_or_conflicting_destination",
    }
    expected_scope_positive_ids = {
        "direct_top_level_change_exact_landed_classification_authority",
        "direct_top_level_migration_exact_landed_classification_authority",
        "fixed_root_change_null_classification",
        "fixed_root_migration_null_classification",
    }
    scope_positive_requirements = (
        scope_authority.get("positive_fixture_requirements", {})
        if isinstance(scope_authority, dict)
        else {}
    )
    scope_positive_counts = {
        key: value
        for key, value in scope_positive_requirements.items()
        if key != "exact_positive_case_count"
    }
    scope_negative_requirements = (
        scope_authority.get("negative_fixture_requirements", {})
        if isinstance(scope_authority, dict)
        else {}
    )
    scope_negative_counts = {
        key: value
        for key, value in scope_negative_requirements.items()
        if key != "exact_negative_case_count"
    }
    role_path_sets = [
        tuple(row.get("reference_paths", []))
        for row in nonartifact.get("roles", [])
        if isinstance(row, dict)
    ]
    if (
        set(nonartifact)
        != {
            "common_failure_rule",
            "direct_source_classification_authority",
            "scope_destination_authority",
            "roles",
        }
        or not nonartifact["common_failure_rule"]
        or not isinstance(classification_authority, dict)
        or set(classification_authority)
        != expected_classification_authority_keys
        or classification_authority["authority_id"]
        != "DIRECT-SOURCE-CLASSIFICATION-AUTHORITY-1.0"
        or classification_authority["authority_record_type"]
        != "DirectSourceClassificationAuthorityV1"
        or classification_authority["behavior_record_type"]
        != "TestBehaviorAuthorityV1"
        or classification_authority["live_initial_behavior_population"]
        != "EMPTY_FAIL_CLOSED"
        or set(classification_authority["cardinality"])
        != expected_classification_cardinality_keys
        or not all(classification_authority["cardinality"].values())
        or set(classification_positive_counts)
        != expected_classification_positive_ids
        or any(
            value != 1
            for value in classification_positive_counts.values()
        )
        or classification_positive_requirements.get(
            "exact_positive_case_count"
        )
        != 3
        or sum(classification_positive_counts.values()) != 3
        or set(classification_negative_counts)
        != expected_classification_negative_ids
        or any(
            value != 1
            for value in classification_negative_counts.values()
        )
        or classification_negative_requirements.get(
            "exact_negative_case_count"
        )
        != 44
        or sum(classification_negative_counts.values()) != 44
        or not isinstance(scope_authority, dict)
        or set(scope_authority) != expected_scope_authority_keys
        or scope_authority["authority_id"]
        != "LEGACY-TEST-SCOPE-DESTINATION-AUTHORITY-2.0"
        or scope_authority["normalized_row_type"]
        != "LegacyTestScopeAuthorityRowV2"
        or scope_authority["subject_schema"]
        != "legacy-test-scope-authority-subject/v2"
        or set(scope_authority["cardinality"])
        != expected_scope_cardinality_keys
        or not all(scope_authority["cardinality"].values())
        or len(scope_authority["freshness"]) != 2
        or len(scope_authority["predicates"]) != 5
        or set(scope_positive_counts) != expected_scope_positive_ids
        or any(
            value != 1 for value in scope_positive_counts.values()
        )
        or scope_positive_requirements.get(
            "exact_positive_case_count"
        )
        != 4
        or sum(scope_positive_counts.values()) != 4
        or set(scope_negative_counts) != expected_scope_negative_ids
        or any(value != 1 for value in scope_negative_counts.values())
        or scope_negative_requirements.get(
            "exact_negative_case_count"
        )
        != 17
        or sum(scope_negative_counts.values()) != 17
        or len(nonartifact["roles"]) != 12
        or len(role_path_sets) != len(set(role_path_sets))
        or (
            "/affected_scope_id",
            "/baseline_row/path",
            "/current_row/path",
            "/baseline_source_row/path",
            "/current_source_row/path",
        )
        not in role_path_sets
        or (
            "/canonical_destination",
            "/destination_rows/*/path",
        )
        not in role_path_sets
        or any(
            set(row) != {"reference_paths", "authority", "predicate"}
            or not row["reference_paths"]
            or not row["authority"]
            or not row["predicate"]
            for row in nonartifact["roles"]
        )
    ):
        raise ValueError(
            "ADR-0010 nonartifact resolver denominator drift"
        )
    landing = contract["landing_record_role"]
    landing_authority = parse_tdd_nested_type_catalog()[
        "landing_record_status_authority"
    ]
    if (
        len(landing["fields"]) != 21
        or len(landing["fields"]) != len(set(landing["fields"]))
        or set(landing["fields"]) != set(landing["field_types"])
        or landing["additional_properties"] is not False
        or landing["nullable_fields"]
        or landing["status_authority_ref"]
        != "ADR-0008 " + landing_authority["authority_id"]
        or landing["field_types"]["status"]
        != {"const": landing_authority["success_literal"]}
    ):
        raise ValueError("ADR-0010 LandingRecord role drift")
    sealing = contract["sealing_validation_role"]
    if (
        len(sealing["closed_binding_fields"]) != 17
        or len(sealing["closed_binding_fields"])
        != len(set(sealing["closed_binding_fields"]))
        or set(sealing["closed_binding_fields"])
        != set(sealing["field_types"])
        or sealing["nullable_fields"]
    ):
        raise ValueError("ADR-0010 sealing role drift")
    self_reference = contract["self_reference_prohibition"]
    prohibited = set(
        self_reference["prohibited_source_record_fields"]
    )
    if (
        any(prohibited & set(row["fields"]) for row in records)
        or len(self_reference["digest_dag"]) != 18
        or len(self_reference["digest_dag"])
        != len(set(self_reference["digest_dag"]))
        or not self_reference["reason"]
    ):
        raise ValueError(
            "ADR-0010 source-record self-reference drift"
        )
    active_paths = compatibility["active_projection_paths"]
    if active_paths != {
        "policy": (
            "architecture/contracts/legacy-test-layout-policy-v2.json"
        ),
        "record_manifest": (
            "architecture/contracts/legacy-test-layout-records-v2.json"
        ),
        "policy_schema": (
            "schemas/common/legacy-test-layout-policy-v2.schema.json"
        ),
        "policy_schema_id": "legacy-test-layout-policy/v2",
        "policy_id": "RANEX-LEGACY-TEST-LAYOUT-2.0",
        "policy_version": "2.0.0",
        "record_manifest_id_version": (
            "REG-LEGACY-TEST-LAYOUT-RECORDS-001@2.0.0"
        ),
        "rule": active_paths.get("rule"),
    } or not active_paths["rule"]:
        raise ValueError("ADR-0010 active V2 projection path drift")
    live_v1 = compatibility["live_v1_precondition"]
    if (
        live_v1.get("expected_active_change_record_count") != 0
        or live_v1.get("expected_accepted_migration_record_count")
        != 0
        or live_v1.get("expected_accepted_cutover_record_count") != 0
        or not live_v1.get("authority")
        or not live_v1.get("failure")
    ):
        raise ValueError("ADR-0010 live V1 precondition drift")
    historical = compatibility["historical_artifact_authority"]
    expected_historical_paths = {
        "architecture/contracts/legacy-test-layout-policy-v1.json",
        "architecture/contracts/legacy-test-layout-policy.json",
        "architecture/contracts/legacy-test-layout-records-v1.json",
        "architecture/contracts/legacy-test-layout-records.json",
        "schemas/common/legacy-test-change-exception-v1.schema.json",
        (
            "schemas/common/"
            "legacy-test-cutover-removal-record-v1.schema.json"
        ),
        "schemas/common/legacy-test-layout-policy-v1.schema.json",
        "schemas/common/legacy-test-migration-record-v1.schema.json",
        "schemas/execution/landing-record-v1.schema.json",
    }
    historical_rows = historical.get("rows", [])
    historical_paths = [row.get("path") for row in historical_rows]
    if (
        set(historical)
        != {
            "manifest_id",
            "exact_artifact_count",
            "owner_class",
            "provenance_kind",
            "licensing_classification",
            "license_id",
            "repository_inclusion",
            "manifest_digest_rule",
            "writer_authority",
            "rows",
            "verification_policy",
        }
        or historical["manifest_id"]
        != "ADR10-HISTORICAL-V1-ARTIFACTS-001"
        or historical["exact_artifact_count"] != 9
        or historical["owner_class"]
        != "ADR10_PREDECESSOR_CONTRACT_1_0"
        or historical["provenance_kind"]
        != "PROJECT_AUTHORED_ARCHITECTURE_TOOLING"
        or historical["licensing_classification"]
        != "RANEX_ORIGINAL"
        or historical["license_id"]
        != "LicenseRef-Ranex-Personal-Use-1.0"
        or historical["repository_inclusion"] != "PUBLIC_SAFE"
        or historical_paths
        != sorted(historical_paths, key=lambda value: value.encode("utf-8"))
        or set(historical_paths) != expected_historical_paths
        or len(historical_rows) != 9
        or any(
            set(row)
            != {
                "path",
                "sha256",
                "artifact_class",
                "disposition",
                "superseded_by",
            }
            for row in historical_rows
        )
    ):
        raise ValueError("ADR-0010 historical artifact manifest drift")
    writer_authority = historical["writer_authority"]
    if (
        set(writer_authority)
        != {
            "canonical_writer",
            "generator_role",
            "tree_lock_class",
            "output_exclusion",
            "change_rule",
        }
        or writer_authority["canonical_writer"]
        != "NONE_IMMUTABLE_COMMITTED_INPUT"
        or writer_authority["generator_role"]
        != "VERIFY_ONLY_NO_CREATE_UPDATE_DELETE_REFORMAT"
        or writer_authority["tree_lock_class"]
        != "ADR10_IMMUTABLE_V1_INPUT"
        or not writer_authority["output_exclusion"]
        or not writer_authority["change_rule"]
    ):
        raise ValueError("ADR-0010 historical writer authority drift")
    for row in historical_rows:
        path = ROOT / row["path"]
        if (
            not path.is_file()
            or "sha256:" + sha256_file(path) != row["sha256"]
        ):
            raise ValueError(
                "ADR-0010 immutable historical artifact drift: "
                + row["path"]
            )
    historical_by_path = {
        row["path"]: row for row in historical_rows
    }
    for alias, explicit in (
        (
            "architecture/contracts/legacy-test-layout-policy.json",
            "architecture/contracts/legacy-test-layout-policy-v1.json",
        ),
        (
            "architecture/contracts/legacy-test-layout-records.json",
            "architecture/contracts/legacy-test-layout-records-v1.json",
        ),
    ):
        if (
            historical_by_path[alias]["sha256"]
            != historical_by_path[explicit]["sha256"]
        ):
            raise ValueError(
                "ADR-0010 frozen V1 alias byte identity drift"
            )
    fixtures = compatibility["fixture_requirements"]
    if (
        set(fixtures)
        != {
            "positive",
            "negative",
            "exact_positive_case_count",
            "exact_negative_case_count",
        }
        or fixtures["exact_positive_case_count"] != 5
        or fixtures["exact_negative_case_count"] != 20
        or {
            row.get("case_id") for row in fixtures["positive"]
        }
        != {
            f"ADR10-COMPAT-V2-POS-{index:03d}"
            for index in range(1, 6)
        }
        or {
            row.get("case_id") for row in fixtures["negative"]
        }
        != {
            f"ADR10-COMPAT-V2-NEG-{index:03d}"
            for index in range(1, 21)
        }
        or any(
            set(row) != {"case_id", "proves"}
            or not row["proves"]
            for row in [
                *fixtures["positive"],
                *fixtures["negative"],
            ]
        )
    ):
        raise ValueError("ADR-0010 compatibility fixture drift")
    templates = classification_authority["authoring_templates"]
    if (
        templates
        != {
            "behavior": (
                "docs/architecture/templates/"
                "TEST_BEHAVIOR_AUTHORITY.yaml"
            ),
            "classification": (
                "docs/architecture/templates/"
                "DIRECT_SOURCE_CLASSIFICATION_AUTHORITY.yaml"
            ),
        }
        or sha256_file(ROOT / templates["behavior"])
        != ADR10_BEHAVIOR_TEMPLATE_SHA256
        or sha256_file(ROOT / templates["classification"])
        != ADR10_CLASSIFICATION_TEMPLATE_SHA256
    ):
        raise ValueError("ADR-0010 authority template drift")
    return contract


def parse_adr12_readiness_contract() -> dict[str, Any]:
    """Parse the complete closed readiness contract from accepted ADR-0012."""

    if sha256_file(READINESS_ADR) != ADR12_SOURCE_SHA256:
        raise ValueError("ADR-0012 source digest drift")
    matches = re.findall(
        (
            r"<!-- BEGIN ADR12 READINESS TIER CONTRACT -->"
            r"\s*```yaml\n(.*?)\n```\s*"
            r"<!-- END ADR12 READINESS TIER CONTRACT -->"
        ),
        read(READINESS_ADR),
        flags=re.DOTALL,
    )
    if len(matches) != 1:
        raise ValueError("ADR-0012 marked readiness contract count drift")
    if (
        hashlib.sha256(matches[0].encode("utf-8")).hexdigest()
        != ADR12_MACHINE_BLOCK_SHA256
    ):
        raise ValueError("ADR-0012 marked contract digest drift")
    wrapper = load_yaml_text_strict(matches[0])
    if set(wrapper) != {"readiness_tier_contract"}:
        raise ValueError("ADR-0012 marked contract wrapper drift")
    contract = wrapper["readiness_tier_contract"]
    expected_keys = {
        "contract_id",
        "contract_version",
        "schema_version",
        "catalog_id",
        "catalog_version",
        "catalog_status",
        "governing_adr",
        "canonicalization",
        "digest_algorithm",
        "digest_encoding",
        "additional_properties",
        "noncompensating",
        "source_projection_ref",
        "assessment_registry_ref",
        "subject_schema_ref",
        "subject_manifest_schema_ref",
        "evidence_binding_schema_ref",
        "assessment_schema_ref",
        "inherited_type_authority",
        "scalar_types",
        "runtime_assessment_status_contract",
        "state_axis",
        "transition_fact_contract",
        "exact_subject_projection",
        "readiness_subject_manifest_projection",
        "nested_types",
        "assessment_record",
        "tiers",
        "gates",
        "evidence_bridge_contract",
        "human_decision_contract",
        "reviewer_contract",
        "bootstrap_lane",
        "resolver_contract",
        "sad_path_transitions",
        "fixture_contract",
        "current_standing",
    }
    if (
        not isinstance(contract, dict)
        or set(contract) != expected_keys
        or contract["contract_id"]
        != "RANEX-READINESS-TIER-CONTROL-1.0"
        or contract["contract_version"] != "1.0.0"
        or contract["schema_version"] != "readiness-tier-contract/v1"
        or contract["catalog_id"] != "RANEX-READINESS-TIERS-001"
        or contract["catalog_version"] != "1.0.0"
        or contract["catalog_status"]
        != "DEFINITION_ONLY_NOT_ASSESSED"
        or contract["governing_adr"] != "ADR-0012"
        or contract["canonicalization"] != "RFC8785"
        or contract["digest_algorithm"] != "SHA-256"
        or contract["additional_properties"] is not False
        or contract["noncompensating"] is not True
    ):
        raise ValueError("ADR-0012 readiness contract identity drift")
    expected_refs = {
        "source_projection_ref": (
            "architecture/contracts/readiness-tiers.json"
        ),
        "assessment_registry_ref": (
            "architecture/contracts/readiness-assessments.json"
        ),
        "subject_schema_ref": (
            "schemas/assurance/readiness-subject-v1.schema.json"
        ),
        "subject_manifest_schema_ref": (
            "schemas/assurance/"
            "readiness-subject-manifest-v1.schema.json"
        ),
        "evidence_binding_schema_ref": (
            "schemas/assurance/"
            "readiness-evidence-binding-v1.schema.json"
        ),
        "assessment_schema_ref": (
            "schemas/assurance/readiness-assessment-v1.schema.json"
        ),
    }
    if any(contract[key] != value for key, value in expected_refs.items()):
        raise ValueError("ADR-0012 readiness projection reference drift")

    tier_ids = [
        "READINESS-TIER-IMPLEMENTATION-START-001",
        "READINESS-TIER-PRODUCTION-001",
    ]
    tiers = contract["tiers"]
    gates = contract["gates"]
    if (
        [row.get("tier_id") for row in tiers] != tier_ids
        or len(gates) != 21
        or len({row.get("gate_id") for row in gates}) != len(gates)
        or any(row.get("noncompensating") is not True for row in gates)
        or any(row.get("required_result") != "PASS" for row in gates)
    ):
        raise ValueError("ADR-0012 readiness tier/gate denominator drift")
    gates_by_tier = {
        tier_id: sorted(
            row["gate_id"]
            for row in gates
            if row["tier_id"] == tier_id
        )
        for tier_id in tier_ids
    }
    if any(
        tier["exact_gate_ids"] != gates_by_tier[tier["tier_id"]]
        for tier in tiers
    ) or [len(gates_by_tier[tier_id]) for tier_id in tier_ids] != [11, 10]:
        raise ValueError("ADR-0012 exact tier gate-set drift")
    bridge_rows = contract["evidence_bridge_contract"][
        "bridge_rule_by_gate"
    ]
    if (
        set(bridge_rows) != {row["gate_id"] for row in gates}
        or any(
            bridge_rows[row["gate_id"]]["bridge_rule_id"]
            != row["bridge_rule_id"]
            for row in gates
        )
        or len(
            {
                row["bridge_rule_id"]
                for row in gates
            }
        )
        != len(gates)
    ):
        raise ValueError("ADR-0012 evidence bridge population drift")

    nested = {
        row.get("type_id"): row for row in contract["nested_types"]
    }
    if set(nested) != {
        "ReadinessSubjectManifestEntryV1",
        "ReadinessEvidenceBindingV1",
        "ReadinessGateResultV1",
    }:
        raise ValueError("ADR-0012 nested type denominator drift")
    type_rows = [
        contract["exact_subject_projection"],
        contract["readiness_subject_manifest_projection"],
        *contract["nested_types"],
        contract["assessment_record"],
    ]
    for row in type_rows:
        fields = row.get("fields", row.get("output_fields"))
        if (
            row.get("additional_properties") is not False
            or not isinstance(fields, list)
            or len(fields) != len(set(fields))
            or set(fields) != set(row.get("field_types", {}))
            or not set(row.get("nullable_fields", [])) <= set(fields)
            or not set(row.get("array_cardinalities", {})) <= set(fields)
        ):
            raise ValueError(
                "ADR-0012 closed type field drift: "
                + str(
                    row.get(
                        "type_id",
                        row.get("projection_id"),
                    )
                )
            )
    runtime_status = contract["runtime_assessment_status_contract"]
    if runtime_status["values"] != [
        "NOT_ASSESSED",
        "UNKNOWN",
        "ASSESSED_PASS",
        "ASSESSED_FAIL",
        "CONFLICT",
    ]:
        raise ValueError("ADR-0012 runtime status axis drift")
    state_axis = contract["state_axis"]
    registered_state_axes = [
        axis
        for axis in STATE_AXIS_CATALOG["axes"]
        if axis["axis_id"] == state_axis.get("axis_id")
    ]
    if (
        state_axis["axis_id"] != "READINESS-STATE-1.0"
        or state_axis["axis_version"] != "1.0.0"
        or state_axis["owner_context"] != "process_assurance"
        or state_axis["state_catalog_ref"]
        != "architecture/contracts/states.json"
        or state_axis["initial_state"] != "NOT_ASSESSED"
        or len(state_axis["values"]) != 7
        or len(state_axis["transitions"]) != 13
        or len(state_axis["forbidden_transitions"]) != 6
        or any(
            re.fullmatch(
                r"[A-Z][A-Z0-9_]*>[A-Z][A-Z0-9_]*@"
                r"[A-Z][A-Z0-9_]*",
                transition,
            )
            is None
            for transition in state_axis["transitions"]
        )
        or len(registered_state_axes) != 1
        or registered_state_axes[0]["axis_version"]
        != state_axis["axis_version"]
        or registered_state_axes[0]["owner_context"]
        != state_axis["owner_context"]
        or registered_state_axes[0]["values"] != state_axis["values"]
        or registered_state_axes[0]["initial_values"]
        != [state_axis["initial_state"]]
        or registered_state_axes[0]["terminal_values"] != []
        or registered_state_axes[0].get("nonterminal") is not True
        or registered_state_axes[0]["transitions"]
        != state_axis["transitions"]
    ):
        raise ValueError("ADR-0012 readiness state axis drift")
    standing = contract["current_standing"]
    if standing != {
        "assessment_record_count": 0,
        "subject_manifest_count": 0,
        "evidence_binding_count": 0,
        "transition_fact_count": 0,
        "implementation_start_state": "NOT_ASSESSED",
        "production_state": "NOT_ASSESSED",
        "implementation_start_authorized": False,
        "production_authorized": False,
        "runtime_validation_status": "NOT_ASSESSED",
        "capability_score": None,
    }:
        raise ValueError("ADR-0012 current standing overclaim or drift")
    fixture = contract["fixture_contract"]
    if (
        fixture["positive_case_requirements"].get(
            "exact_positive_case_count"
        )
        != 4
        or fixture["negative_case_requirements"].get(
            "exact_negative_case_count"
        )
        != 28
        or any(
            value != 1
            for key, value in fixture[
                "positive_case_requirements"
            ].items()
            if key != "exact_positive_case_count"
        )
        or any(
            value != 1
            for key, value in fixture[
                "negative_case_requirements"
            ].items()
            if key != "exact_negative_case_count"
        )
    ):
        raise ValueError("ADR-0012 fixture denominator drift")
    return contract


def build_readiness_registries() -> dict[str, dict[str, Any]]:
    contract = parse_adr12_readiness_contract()
    source_path = str(READINESS_ADR.relative_to(ROOT))
    source_digest = "sha256:" + sha256_file(READINESS_ADR)
    contract_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(contract))
    )
    tier_projection = {
        **copy.deepcopy(contract),
        "generated_by": GENERATOR_WRITER,
        "source_path": source_path,
        "source_digest": source_digest,
        "source_contract_digest": contract_digest,
    }
    assessment_projection = {
        "registry_id": "REG-READINESS-ASSESSMENTS-001",
        "version": contract["contract_version"],
        "status": contract["catalog_status"],
        "generated_by": GENERATOR_WRITER,
        "contract_id": contract["contract_id"],
        "contract_version": contract["contract_version"],
        "governing_adr": contract["governing_adr"],
        "source_path": source_path,
        "source_digest": source_digest,
        "source_contract_digest": contract_digest,
        "tier_catalog_ref": contract["source_projection_ref"],
        "subject_schema_ref": contract["subject_schema_ref"],
        "subject_manifest_schema_ref": (
            contract["subject_manifest_schema_ref"]
        ),
        "evidence_binding_schema_ref": (
            contract["evidence_binding_schema_ref"]
        ),
        "record_schema_ref": contract["assessment_schema_ref"],
        "record_count": 0,
        "entries": [],
        "current_standing": copy.deepcopy(
            contract["current_standing"]
        ),
    }
    return {
        "readiness-tiers.json": tier_projection,
        "readiness-assessments.json": assessment_projection,
    }


def parse_legacy_test_layout_decision() -> dict[str, Any]:
    text = read(LEGACY_TEST_LAYOUT_ADR)
    marked_contract_pattern = (
        r"<!-- BEGIN ADR10 LEGACY TEST RECORD CONTRACT -->"
        r".*?"
        r"<!-- END ADR10 LEGACY TEST RECORD CONTRACT -->"
    )
    unmarked_text = re.sub(
        marked_contract_pattern,
        "",
        text,
        flags=re.DOTALL,
    )
    yaml_blocks = [
        load_yaml_text_strict(block)
        for block in re.findall(
            r"```yaml\n(.*?)\n```",
            unmarked_text,
            flags=re.DOTALL,
        )
    ]
    if len(yaml_blocks) != 4:
        raise ValueError(
            f"ADR-0010 YAML block drift: expected=4 actual={len(yaml_blocks)}"
        )
    baseline = yaml_blocks[0]["legacy_test_baseline"]
    row_policy = yaml_blocks[1]["row_policy"]
    directory_exceptions = yaml_blocks[2]["directory_exceptions"]
    direct_and_canonical = yaml_blocks[3]
    rule_rows = markdown_table(
        section(
            text,
            "| Rule ID | Blocking obligation |",
            "| Fitness ID | Required check |",
        )
    )
    fitness_rows = markdown_table(
        section(
            text,
            "| Fitness ID | Required check |",
            "The ten rule assessments",
        )
    )
    return {
        "policy_id": "RANEX-LEGACY-TEST-LAYOUT-2.0",
        "baseline": baseline,
        "row_policy": row_policy,
        "directory_exceptions": directory_exceptions,
        "direct_top_level_exception": direct_and_canonical[
            "direct_top_level_exception"
        ],
        "inherited_canonical_scopes": direct_and_canonical[
            "inherited_files_already_under_canonical_roots"
        ],
        "record_contract": parse_adr10_legacy_record_contract(),
        "rules": [
            {
                "rule_id": row[0],
                "enforcement": "BLOCKING",
                "invariant": row[1],
                "definition_status": "DEFINED",
                "runtime_evidence_status": "NOT_ASSESSED",
                "source": str(LEGACY_TEST_LAYOUT_ADR.relative_to(ROOT)),
            }
            for row in rule_rows
        ],
        "fitness_obligations": [
            {
                "fitness_id": row[0],
                "required_evidence": row[1],
                "result": "NOT_ASSESSED",
                "evidence_refs": [],
                "noncompensating": True,
                "source": str(LEGACY_TEST_LAYOUT_ADR.relative_to(ROOT)),
            }
            for row in fitness_rows
        ],
        "decision_binding": decision_binding(
            LEGACY_TEST_LAYOUT_ADR,
            "ADR-0010",
        ),
    }


def read_git_blob_bytes(blob_oids: list[str]) -> dict[str, bytes]:
    unique_oids = sorted(set(blob_oids))
    process = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{oid}\n" for oid in unique_oids).encode("ascii"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode != 0:
        raise ValueError(
            f"ADR-0010 Git blob read failed ({process.returncode}): "
            + process.stderr.decode("utf-8", errors="replace")
        )
    output = memoryview(process.stdout)
    cursor = 0
    blobs: dict[str, bytes] = {}
    for requested_oid in unique_oids:
        newline = process.stdout.find(b"\n", cursor)
        if newline < 0:
            raise ValueError(
                f"ADR-0010 Git blob header truncated for {requested_oid}"
            )
        header = bytes(output[cursor:newline]).split()
        cursor = newline + 1
        if len(header) != 3:
            raise ValueError(
                f"ADR-0010 Git blob header invalid for {requested_oid}: {header!r}"
            )
        actual_oid, object_type, raw_size = header
        if (
            actual_oid.decode("ascii") != requested_oid
            or object_type != b"blob"
        ):
            raise ValueError(
                f"ADR-0010 Git object mismatch for {requested_oid}: {header!r}"
            )
        size = int(raw_size)
        content = bytes(output[cursor : cursor + size])
        cursor += size
        if len(content) != size or bytes(output[cursor : cursor + 1]) != b"\n":
            raise ValueError(f"ADR-0010 Git blob truncated: {requested_oid}")
        cursor += 1
        blobs[requested_oid] = content
    if cursor != len(output):
        raise ValueError("ADR-0010 Git blob batch returned trailing bytes")
    return blobs


def legacy_file_manifest_digest(rows: list[dict[str, str]]) -> str:
    serialized = "".join(
        (
            f"{row['path']}\t{row['mode']}\t"
            f"{row['git_blob_oid_sha1']}\t{row['content_sha256']}\n"
        )
        for row in sorted(rows, key=lambda item: item["path"].encode("utf-8"))
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def legacy_test_policy_rows_for_fixture(
    policy: dict[str, Any],
) -> list[dict[str, str]]:
    rows = [
        file_row
        for exception in policy["directory_exceptions"]
        for file_row in exception["baseline_files"]
    ]
    rows.extend(policy["direct_top_level_exception"]["baseline_files"])
    for scope in policy["inherited_canonical_scopes"]:
        rows.extend(scope["baseline_files"])
    return sorted(rows, key=lambda item: item["path"].encode("utf-8"))


def existing_legacy_policy_file_rows() -> list[dict[str, str]]:
    policy_path = CONTRACTS / "legacy-test-layout-policy-v1.json"
    if not policy_path.is_file():
        raise ValueError(
            "ADR-0010 baseline Git object is unavailable and no prior "
            "legacy-test-layout-policy-v1.json projection exists"
        )
    policy = load_json_strict(policy_path)
    return legacy_test_policy_rows_for_fixture(policy)


def materialize_legacy_baseline_files(
    baseline: dict[str, Any],
) -> tuple[list[dict[str, str]], bytes | None]:
    commit = baseline["source_commit_sha1"]
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("ADR-0010 baseline commit is not a SHA-1 object ID")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if probe.returncode != 0:
        rows = existing_legacy_policy_file_rows()
        return rows, None

    listing = subprocess.run(
        ["git", "ls-tree", "-r", "--full-tree", commit, "--", "tests"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    if hashlib.sha256(listing).hexdigest() != baseline[
        "ls_tree_exact_stdout_sha256"
    ]:
        raise ValueError("ADR-0010 full tests ls-tree digest drift")
    metadata_rows: list[tuple[str, str, str]] = []
    for raw_line in listing.decode("utf-8").splitlines():
        metadata, path = raw_line.split("\t", 1)
        mode, object_type, oid = metadata.split()
        if object_type != "blob":
            raise ValueError(f"ADR-0010 non-blob baseline row: {path}")
        metadata_rows.append((path, mode, oid))
    blobs = read_git_blob_bytes([row[2] for row in metadata_rows])
    rows = [
        {
            "path": path,
            "mode": mode,
            "git_blob_oid_sha1": oid,
            "content_sha256": hashlib.sha256(blobs[oid]).hexdigest(),
        }
        for path, mode, oid in metadata_rows
    ]
    return rows, listing


def build_legacy_test_layout_policy(
    decision: dict[str, Any],
) -> dict[str, Any]:
    baseline = decision["baseline"]
    expected_baseline = {
        "baseline_id": "HERMES-TEST-BASELINE-001",
        "source_commit_sha1": "0533e1eaf50ace0eb84435a5c3de05e939fd4daa",
        "tests_tree_oid_sha1": "e331f2ea8d5233ed74ca42d2380c1c6fd4e58c67",
        "file_count": 2444,
        "mode_counts": {"100644": 2444},
        "ls_tree_exact_stdout_sha256": (
            "cab0556790b9ddcb7cabcd6c1d7ff6d8ca6a9065a391e06a17239cfb5f36a076"
        ),
        "file_manifest_sha256": (
            "e550a598da0e226a94a7b15c9a0ace9c48a58e04df146bbe044a7cedcc41e463"
        ),
        "directory_exception_file_count": 2294,
        "direct_top_level_file_count": 134,
        "inherited_canonical_file_count": 16,
        "partition_equation": "2294 + 134 + 16 = 2444",
        "evidence_status": "BASELINE_BOUND_NOT_MIGRATED",
    }
    for key, value in expected_baseline.items():
        if baseline.get(key) != value:
            raise ValueError(f"ADR-0010 baseline drift: {key}")

    expected_rule_ids = {
        "LEGACYTEST-BASELINE-001",
        "LEGACYTEST-ROOTSET-001",
        "LEGACYTEST-TOPLEVEL-001",
        "LEGACYTEST-NOEXPAND-001",
        "LEGACYTEST-CHANGE-001",
        "LEGACYTEST-CANONICAL-001",
        "LEGACYTEST-MIGRATION-001",
        "LEGACYTEST-EXPIRY-001",
        "LEGACYTEST-CUTOVER-001",
        "LEGACYTEST-NONCOMP-001",
    }
    expected_fitness_ids = {
        f"FF-LEGACYTEST-{index:03d}" for index in range(1, 10)
    }
    if {row["rule_id"] for row in decision["rules"]} != expected_rule_ids:
        raise ValueError("ADR-0010 rule-set drift")
    if {
        row["fitness_id"] for row in decision["fitness_obligations"]
    } != expected_fitness_ids:
        raise ValueError("ADR-0010 fitness-set drift")

    rows, raw_listing = materialize_legacy_baseline_files(baseline)
    if len(rows) != 2444:
        raise ValueError(f"ADR-0010 file denominator drift: {len(rows)}")
    paths = [row["path"] for row in rows]
    if (
        paths != sorted(paths, key=lambda path: path.encode("utf-8"))
        or len(paths) != len(set(paths))
        or any(
            row["mode"] != "100644"
            or not re.fullmatch(r"[0-9a-f]{40}", row["git_blob_oid_sha1"])
            or not re.fullmatch(r"[0-9a-f]{64}", row["content_sha256"])
            for row in rows
        )
    ):
        raise ValueError("ADR-0010 file row ordering, uniqueness, or digest drift")
    if legacy_file_manifest_digest(rows) != baseline["file_manifest_sha256"]:
        raise ValueError("ADR-0010 file-manifest digest drift")

    row_policy = decision["row_policy"]
    expected_row_policy = {
        "allowed_inherited_scope": "EXACT_BASELINE_FILES_ONLY",
        "change_exception_scope": (
            "IN_PLACE_CONTENT_ONLY_ON_EXISTING_BASELINE_PATH"
        ),
        "legacy_addition_policy": "FAIL_REQUIRES_SUPERSEDING_ADR",
        "move_rename_policy": (
            "CANONICAL_DESTINATION_WITH_MIGRATION_PROOF_ONLY"
        ),
        "compatibility_owner": "compatibility",
        "migration_owner": "migration",
        "test_governance_owner": "process_assurance",
        "migration_trigger": (
            "FIRST_PATH_OR_CONTENT_CHANGE_OR_RANEX_DEPENDENCY_TOUCH"
        ),
        "expires_at": "2026-10-31T23:59:59Z",
        "removal_proof_profile": "LEGACY_TEST_MIGRATION_PROOF_V2",
    }
    if row_policy != expected_row_policy:
        raise ValueError("ADR-0010 common row-policy drift")

    directory_rows = decision["directory_exceptions"]
    expected_exception_ids = {
        f"LEGACY-TEST-ROOT-{index:03d}" for index in range(1, 30)
    }
    if (
        len(directory_rows) != 29
        or {row["exception_id"] for row in directory_rows}
        != expected_exception_ids
        or len({row["legacy_root"] for row in directory_rows}) != 29
        or sum(row["file_count"] for row in directory_rows) != 2294
    ):
        raise ValueError("ADR-0010 directory exception denominator drift")

    rows_by_path = {row["path"]: row for row in rows}
    listing_lines = raw_listing.splitlines(keepends=True) if raw_listing else []

    def rows_under(root: str) -> list[dict[str, str]]:
        prefix = root.rstrip("/") + "/"
        return [
            rows_by_path[path]
            for path in paths
            if path.startswith(prefix)
        ]

    def listing_digest_for(root: str) -> str | None:
        if not listing_lines:
            return None
        prefix = root.rstrip("/") + "/"
        selected = b"".join(
            line
            for line in listing_lines
            if line.split(b"\t", 1)[1].decode("utf-8").startswith(prefix)
        )
        return hashlib.sha256(selected).hexdigest()

    commit = baseline["source_commit_sha1"]
    git_available = raw_listing is not None
    if git_available:
        tests_tree_oid = subprocess.run(
            ["git", "rev-parse", f"{commit}:tests"],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()
        if tests_tree_oid != baseline["tests_tree_oid_sha1"]:
            raise ValueError("ADR-0010 tests tree OID drift")

    expanded_directories = []
    for row in directory_rows:
        baseline_files = rows_under(row["legacy_root"])
        if len(baseline_files) != row["file_count"]:
            raise ValueError(
                f"ADR-0010 directory file-count drift: {row['exception_id']}"
            )
        listing_digest = listing_digest_for(row["legacy_root"])
        if (
            listing_digest is not None
            and listing_digest != row["ls_tree_listing_sha256"]
        ):
            raise ValueError(
                f"ADR-0010 directory listing drift: {row['exception_id']}"
            )
        if git_available:
            subtree_oid = subprocess.run(
                ["git", "rev-parse", f"{commit}:{row['legacy_root']}"],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            if subtree_oid != row["subtree_oid_sha1"]:
                raise ValueError(
                    f"ADR-0010 subtree OID drift: {row['exception_id']}"
                )
        expanded_directories.append(
            {
                **row,
                **row_policy,
                "baseline_files": baseline_files,
                "migration_status": "NOT_MIGRATED",
                "runtime_validation_status": "NOT_ASSESSED",
            }
        )

    top_level = decision["direct_top_level_exception"]
    direct_files = [row for row in rows if row["path"].count("/") == 1]
    if (
        top_level["exception_id"] != "LEGACY-TEST-TOPLEVEL-001"
        or len(direct_files) != top_level["file_count"]
        or top_level["file_count"] != 134
    ):
        raise ValueError("ADR-0010 direct top-level denominator drift")
    if raw_listing is not None:
        direct_listing = b"".join(
            line
            for line in listing_lines
            if line.split(b"\t", 1)[1].decode("utf-8").count("/") == 1
        )
        if (
            hashlib.sha256(direct_listing).hexdigest()
            != top_level["ls_tree_listing_sha256"]
        ):
            raise ValueError("ADR-0010 direct top-level listing drift")
    expanded_top_level = {
        **top_level,
        "baseline_files": direct_files,
        "migration_status": "NOT_MIGRATED",
        "runtime_validation_status": "NOT_ASSESSED",
    }

    canonical_scopes = decision["inherited_canonical_scopes"]
    if {
        row["scope_id"] for row in canonical_scopes
    } != {
        "LEGACY-TEST-CANONICAL-E2E-001",
        "LEGACY-TEST-CANONICAL-INTEGRATION-001",
    }:
        raise ValueError("ADR-0010 canonical inherited scope-set drift")
    expanded_canonical = []
    for scope in canonical_scopes:
        baseline_files = rows_under(scope["root"])
        if len(baseline_files) != scope["file_count"]:
            raise ValueError(
                f"ADR-0010 canonical file-count drift: {scope['scope_id']}"
            )
        listing_digest = listing_digest_for(scope["root"])
        if (
            listing_digest is not None
            and listing_digest != scope["ls_tree_listing_sha256"]
        ):
            raise ValueError(
                f"ADR-0010 canonical listing drift: {scope['scope_id']}"
            )
        if git_available:
            subtree_oid = subprocess.run(
                ["git", "rev-parse", f"{commit}:{scope['root']}"],
                cwd=ROOT,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout.strip()
            if subtree_oid != scope["subtree_oid_sha1"]:
                raise ValueError(
                    f"ADR-0010 canonical subtree drift: {scope['scope_id']}"
                )
        expanded_canonical.append(
            {
                **scope,
                "allowed_inherited_scope": "EXACT_BASELINE_FILES_ONLY",
                "baseline_files": baseline_files,
                "migration_status": "NOT_MIGRATED",
                "runtime_validation_status": "NOT_ASSESSED",
            }
        )

    partitioned_paths = {
        file_row["path"]
        for exception in expanded_directories
        for file_row in exception["baseline_files"]
    } | {
        file_row["path"]
        for file_row in expanded_top_level["baseline_files"]
    } | {
        file_row["path"]
        for scope in expanded_canonical
        for file_row in scope["baseline_files"]
    }
    if partitioned_paths != set(paths):
        raise ValueError("ADR-0010 baseline partition coverage drift")

    allowed_record_paths: set[Path] = set()
    expected_child_directories = set(
        LEGACY_TEST_RECORD_DIRECTORIES.values()
    ) | {LEGACY_TEST_CLASSIFICATION_ROOT}
    if LEGACY_TEST_RECORD_ROOT.exists():
        if (
            LEGACY_TEST_RECORD_ROOT.is_symlink()
            or not LEGACY_TEST_RECORD_ROOT.is_dir()
        ):
            raise ValueError("ADR-0010 record root is not a directory")
        for child in LEGACY_TEST_RECORD_ROOT.iterdir():
            if child.name == "README.md":
                if child.is_symlink() or not child.is_file():
                    raise ValueError(
                        "ADR-0010 record README is not a regular file"
                    )
                continue
            if child not in expected_child_directories:
                raise ValueError(
                    "ADR-0010 unexpected record-root entry: "
                    + str(child.relative_to(ROOT))
                )
            if child.is_symlink() or not child.is_dir():
                raise ValueError(
                    "ADR-0010 record child is not a directory: "
                    + str(child.relative_to(ROOT))
                )
            for record_path in child.iterdir():
                if record_path.name == "README.md":
                    if (
                        record_path.is_symlink()
                        or not record_path.is_file()
                    ):
                        raise ValueError(
                            "ADR-0010 child README is not regular: "
                            + str(record_path.relative_to(ROOT))
                        )
                    continue
                if (
                    record_path.is_symlink()
                    or not record_path.is_file()
                    or record_path.suffix != ".json"
                ):
                    raise ValueError(
                        "ADR-0010 noncanonical record entry: "
                        + str(record_path.relative_to(ROOT))
                    )
                allowed_record_paths.add(record_path)
        readme_path = LEGACY_TEST_RECORD_ROOT / "README.md"
        if readme_path.is_symlink() or not readme_path.is_file():
            raise ValueError("ADR-0010 record README is missing")
    record_id_keys = {
        "CHANGE_EXCEPTION": "change_exception_id",
        "MIGRATION_RECORD": "proof_id",
        "CUTOVER_REMOVAL_RECORD": "cutover_removal_record_id",
    }
    record_instances: dict[str, list[dict[str, Any]]] = {}
    for record_kind, directory in LEGACY_TEST_RECORD_DIRECTORIES.items():
        source_paths = (
            sorted(directory.glob("*.json"))
            if directory.is_dir()
            else []
        )
        records = [load_json_strict(path) for path in source_paths]
        id_key = record_id_keys[record_kind]
        for source_path, record in zip(source_paths, records, strict=True):
            if source_path.name != f"{record[id_key]}.json":
                raise ValueError(
                    "ADR-0010 record filename/ID mismatch: "
                    + str(source_path.relative_to(ROOT))
                )
        record_instances[record_kind] = records

    return {
        "schema_version": "legacy-test-layout-policy/v2",
        "policy_id": decision["policy_id"],
        "version": "2.0.0",
        "exception_class": "LEGACY_TEST_ROOT_EXCEPTION",
        "baseline": baseline,
        "row_policy": row_policy,
        "directory_exceptions": expanded_directories,
        "direct_top_level_exception": expanded_top_level,
        "inherited_canonical_scopes": expanded_canonical,
        "change_exception_type": "LEGACY_TEST_CHANGE_EXCEPTION",
        "change_exceptions": record_instances["CHANGE_EXCEPTION"],
        "migration_proof_type": "LEGACY_TEST_MIGRATION_PROOF_V2",
        "migration_proofs": record_instances["MIGRATION_RECORD"],
        "cutover_removal_record_type": (
            "LEGACY_TEST_CUTOVER_REMOVAL_RECORD_V2"
        ),
        "cutover_removal_records": record_instances[
            "CUTOVER_REMOVAL_RECORD"
        ],
        "rules": decision["rules"],
        "fitness_obligations": decision["fitness_obligations"],
        "decision_binding": decision["decision_binding"],
        "current_status": (
            "CUTOVER_REMOVAL_RECORD_REGISTERED"
            if record_instances["CUTOVER_REMOVAL_RECORD"]
            else "MIGRATION_EXCEPTION_ACTIVE"
        ),
        "canonical_test_topology_status": (
            "CUTOVER_NOT_RUNTIME_VALIDATED"
            if record_instances["CUTOVER_REMOVAL_RECORD"]
            else "NOT_MIGRATED"
        ),
        "runtime_validation_status": "NOT_ASSESSED",
        "noncompensating": True,
    }


def build_adr10_authority_catalogs() -> dict[str, dict[str, Any]]:
    contract = parse_adr10_legacy_record_contract()
    nested_by_type = {
        row["type_id"]: row for row in contract["nested_types"]
    }
    catalog_specs = (
        {
            "root": TEST_BEHAVIOR_AUTHORITY_ROOT,
            "record_type": "TestBehaviorAuthorityV1",
            "row_type": "TestBehaviorAuthorityRowV1",
            "registry_filename": "test-behaviors.json",
            "registry_id": "REG-TEST-BEHAVIORS-001",
            "id_fields": ("behavior_id", "behavior_version"),
        },
        {
            "root": LEGACY_TEST_CLASSIFICATION_ROOT,
            "record_type": "DirectSourceClassificationAuthorityV1",
            "row_type": "DirectSourceClassificationAuthorityRowV1",
            "registry_filename": (
                "legacy-test-direct-source-classifications.json"
            ),
            "registry_id": (
                "REG-LEGACY-TEST-DIRECT-SOURCE-CLASSIFICATIONS-001"
            ),
            "id_fields": ("classification_id",),
        },
    )
    catalogs: dict[str, dict[str, Any]] = {}
    for spec in catalog_specs:
        root = spec["root"]
        if root.is_symlink() or not root.is_dir():
            raise ValueError(
                "ADR-0010 canonical authority root missing: "
                + str(root.relative_to(ROOT))
            )
        readme = root / "README.md"
        if readme.is_symlink() or not readme.is_file():
            raise ValueError(
                "ADR-0010 canonical authority README missing: "
                + str(readme.relative_to(ROOT))
            )
        source_paths: list[Path] = []
        for child in root.iterdir():
            if child == readme:
                continue
            if (
                child.is_symlink()
                or not child.is_file()
                or child.suffix != ".json"
            ):
                raise ValueError(
                    "ADR-0010 noncanonical authority source: "
                    + str(child.relative_to(ROOT))
                )
            source_paths.append(child)
        source_paths.sort(
            key=lambda path: str(path.relative_to(ROOT)).encode("utf-8")
        )
        source_schema = legacy_test_record_schema(
            (
                "test_behavior_authorities"
                if spec["record_type"] == "TestBehaviorAuthorityV1"
                else "direct_source_classification_authorities"
            ),
            (
                "test-behavior-authority-v1.schema.json"
                if spec["record_type"] == "TestBehaviorAuthorityV1"
                else (
                    "direct-source-classification-"
                    "authority-v1.schema.json"
                )
            ),
            spec["record_type"],
        )
        row_schema = adr10_closed_object_schema(
            nested_by_type[spec["row_type"]],
            nested_by_type,
            {
                row["type_id"]: row
                for row in parse_tdd_nested_type_catalog()["types"]
            },
        )
        rows: list[dict[str, Any]] = []
        seen_ids: set[tuple[str, ...]] = set()
        for source_path in source_paths:
            source = load_json_strict(source_path)
            jsonschema.Draft202012Validator(
                source_schema,
                format_checker=jsonschema.FormatChecker(),
            ).validate(source)
            identity = tuple(source[field] for field in spec["id_fields"])
            if identity in seen_ids:
                raise ValueError(
                    "ADR-0010 duplicate authority identity: "
                    + ":".join(identity)
                )
            seen_ids.add(identity)
            expected_name = (
                source["behavior_id"]
                + "@"
                + source["behavior_version"]
                + ".json"
                if spec["record_type"] == "TestBehaviorAuthorityV1"
                else source["classification_id"] + ".json"
            )
            if source_path.name != expected_name:
                raise ValueError(
                    "ADR-0010 authority filename identity drift: "
                    + str(source_path.relative_to(ROOT))
                )
            source_relative = str(source_path.relative_to(ROOT))
            row = {
                field: (
                    source_relative
                    if field == "source_path"
                    else (
                        "sha256:" + sha256_file(source_path)
                        if field == "source_digest"
                        else source[field]
                    )
                )
                for field in nested_by_type[spec["row_type"]]["fields"]
            }
            jsonschema.Draft202012Validator(
                row_schema,
                format_checker=jsonschema.FormatChecker(),
            ).validate(row)
            rows.append(row)
        catalogs[spec["registry_filename"]] = registry(
            spec["registry_id"],
            "1.0.0",
            rows,
            source_pattern=next(
                row["source_pattern"]
                for row in contract["record_catalog"]
                if row["type_id"] == spec["record_type"]
            ),
            source_count=len(source_paths),
            entry_count=len(rows),
            active_entry_count=sum(
                row["status"] == "ACTIVE" for row in rows
            ),
            source_bijection_status="PASS",
            runtime_authority_resolution_status="NOT_ASSESSED",
        )
    return catalogs


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


def architecture_adr_path(adr_id: str) -> Path:
    matches = sorted(
        (
            ROOT / "docs" / "architecture" / "decisions"
        ).glob(f"{adr_id}-*.md")
    )
    if len(matches) != 1:
        raise ValueError(
            f"Fixed decision governing ADR resolution failed: "
            f"{adr_id}:{len(matches)}"
        )
    return matches[0]


def parse_accepted_adr_catalog() -> tuple[
    list[dict[str, str]],
    dict[str, str],
]:
    """Parse the complete accepted-ADR authority as a closed source set."""

    source_of_truth_text = read(SOURCE_OF_TRUTH)
    owner_rows = re.findall(
        r"^\| Owner decisions \| (.+) \|$",
        source_of_truth_text,
        flags=re.MULTILINE,
    )
    if len(owner_rows) != 1:
        raise ValueError(
            "SOURCE_OF_TRUTH Owner decisions row cardinality drift"
        )
    owner_cell = owner_rows[0]
    owner_links = re.findall(
        r"\[(ADR-\d{4})\]\((\./decisions/[^)]+\.md)\)",
        owner_cell,
    )
    reconstructed_cell = "; ".join(
        f"[{adr_id}]({relative_path})"
        for adr_id, relative_path in owner_links
    )
    if not owner_links or owner_cell != reconstructed_cell:
        raise ValueError(
            "SOURCE_OF_TRUTH Owner decisions row contains "
            "noncanonical, empty, or unparsed content"
        )
    expected_ids: set[str] = set()
    expected_paths: set[str] = set()
    for linked_id, relative_path in owner_links:
        linked_path = (
            SOURCE_OF_TRUTH.parent / relative_path
        ).resolve()
        try:
            normalized = str(linked_path.relative_to(ROOT.resolve()))
        except ValueError as exc:
            raise ValueError(
                "SOURCE_OF_TRUTH Owner decision link escapes repository"
            ) from exc
        filename_match = re.fullmatch(
            r"(ADR-\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md",
            linked_path.name,
        )
        if (
            filename_match is None
            or linked_id != filename_match.group(1)
        ):
            raise ValueError(
                "SOURCE_OF_TRUTH Owner decision label/path mismatch: "
                + linked_id
            )
        if linked_id in expected_ids or normalized in expected_paths:
            raise ValueError(
                "SOURCE_OF_TRUTH Owner decision link duplicated: "
                + linked_id
            )
        expected_ids.add(linked_id)
        expected_paths.add(normalized)

    decision_root = ROOT / "docs" / "architecture" / "decisions"
    paths = sorted(decision_root.glob("ADR-*.md"))
    rows: list[dict[str, str]] = []
    titles: dict[str, str] = {}
    observed_paths: set[str] = set()
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ValueError(
                "Accepted ADR source is not a regular file: "
                + str(path.relative_to(ROOT))
            )
        filename_match = re.fullmatch(
            r"(ADR-\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md",
            path.name,
        )
        if filename_match is None:
            raise ValueError(
                "Accepted ADR filename is not canonical: "
                + str(path.relative_to(ROOT))
            )
        filename_id = filename_match.group(1)
        text = read(path)
        heading_matches = re.findall(
            r"^# (ADR-\d{4}): ([^\n]+)$",
            text,
            flags=re.MULTILINE,
        )
        if len(heading_matches) != 1:
            raise ValueError(
                "Accepted ADR must have exactly one canonical H1: "
                + filename_id
            )
        heading_id, title = heading_matches[0]

        def exact_header(field: str, pattern: str) -> str:
            matches = re.findall(
                rf"^\| {re.escape(field)} \| `({pattern})` \|$",
                text,
                flags=re.MULTILINE,
            )
            if len(matches) != 1:
                raise ValueError(
                    "Accepted ADR header field cardinality drift: "
                    + filename_id
                    + ":"
                    + field
                )
            return matches[0]

        header_id = exact_header("ADR ID", r"ADR-\d{4}")
        version = exact_header(
            "Version",
            r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)",
        )
        status = exact_header("Status", r"[A-Z][A-Z_]*")
        if not filename_id == heading_id == header_id:
            raise ValueError(
                "Accepted ADR filename/heading/header ID mismatch: "
                + filename_id
            )
        if status != "ACCEPTED":
            raise ValueError(
                "Accepted ADR source status is not ACCEPTED: "
                + filename_id
            )
        source_path = str(path.relative_to(ROOT))
        if filename_id in titles or source_path in observed_paths:
            raise ValueError(
                "Accepted ADR ID/path is duplicated: " + filename_id
            )
        titles[filename_id] = title
        observed_paths.add(source_path)
        rows.append(
            {
                "adr_id": filename_id,
                "version": version,
                "status": status,
                "source_path": source_path,
                "source_digest": "sha256:" + sha256_file(path),
            }
        )

    observed_ids = {row["adr_id"] for row in rows}
    if (
        observed_ids != expected_ids
        or observed_paths != expected_paths
        or len(rows) != len(expected_ids)
    ):
        raise ValueError(
            "Accepted ADR source denominator/set drift: "
            + ",".join(sorted(observed_ids ^ expected_ids))
        )
    return (
        sorted(rows, key=lambda row: row["adr_id"]),
        titles,
    )


def architecture_adr_definition(path: Path) -> dict[str, str]:
    """Parse one ADR for callers resolving an already-registered ID."""

    rows, titles = parse_accepted_adr_catalog()
    source_path = str(path.relative_to(ROOT))
    matches = [row for row in rows if row["source_path"] == source_path]
    if len(matches) != 1:
        raise ValueError(
            "Accepted ADR path resolution failed: " + source_path
        )
    row = matches[0]
    return {
        **row,
        "name": titles[row["adr_id"]],
        "source": row["source_path"],
    }


def fixed_decision_fitness_definitions() -> dict[str, dict[str, str]]:
    """Resolve the fitness namespace explicitly named by ADR-0006.

    ADR-0006 delegates baseline functions to ADR-0003 through ADR-0005 and
    defines the remaining registry-level functions itself. Later ADRs may
    define additional fitness namespaces, but they cannot silently redefine
    this fixed-register namespace.
    """

    definitions: dict[str, dict[str, str]] = {}
    for adr_id in (
        "ADR-0003",
        "ADR-0004",
        "ADR-0005",
        "ADR-0006",
        "ADR-0011",
    ):
        path = architecture_adr_path(adr_id)
        for fitness_id, required_result in re.findall(
            r"^\| `(FF-[A-Z0-9-]+)` \| ([^|\n]+) \|$",
            read(path),
            flags=re.MULTILINE,
        ):
            if fitness_id in definitions:
                raise ValueError(
                    "Fixed decision fitness definition duplicated: "
                    + fitness_id
                )
            definitions[fitness_id] = {
                "fitness_id": fitness_id,
                "required_result": required_result.strip(),
                "source": str(path.relative_to(ROOT)),
            }
    if not definitions:
        raise ValueError("Fixed decision fitness definitions missing")
    return definitions


def parse_fixed_decision_register() -> tuple[
    list[dict[str, Any]],
    dict[str, dict[str, str]],
]:
    text = read(FIXED_DECISION_ADR)
    candidates: list[dict[str, Any]] = []
    for block in re.findall(
        r"```yaml\s*\n(.*?)\n```",
        text,
        flags=re.DOTALL,
    ):
        parsed = load_yaml_text_strict(block)
        if (
            isinstance(parsed, dict)
            and parsed.get("register_id") == "RANEX-FIXED-DECISIONS"
        ):
            candidates.append(parsed)
    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one RANEX-FIXED-DECISIONS YAML register"
        )
    register = candidates[0]
    if set(register) != {
        "schema_version",
        "register_id",
        "required_count",
        "decisions",
    }:
        raise ValueError("Fixed decision register fields drift")
    if (
        register["schema_version"] != "1.0.0"
        or register["required_count"] != 29
        or not isinstance(register["decisions"], list)
        or len(register["decisions"]) != 29
    ):
        raise ValueError("Fixed decision register denominator drift")

    expected_ids = [
        f"DEC-RANEX-{index:03d}" for index in range(1, 30)
    ]
    row_fields = {
        "decision_id",
        "name",
        "selected",
        "owner",
        "governing_adr",
        "alternatives",
        "fitness_functions",
        "status",
    }
    observed_ids: list[str] = []
    decisions: list[dict[str, Any]] = []
    fitness_definitions = fixed_decision_fitness_definitions()
    source_digest = "sha256:" + sha256_file(FIXED_DECISION_ADR)
    for row in register["decisions"]:
        if not isinstance(row, dict) or set(row) != row_fields:
            raise ValueError("Fixed decision row fields drift")
        decision_id = row["decision_id"]
        observed_ids.append(decision_id)
        scalar_fields = (
            "decision_id",
            "name",
            "selected",
            "owner",
            "governing_adr",
            "status",
        )
        if any(
            not isinstance(row[field], str) or not row[field].strip()
            for field in scalar_fields
        ):
            raise ValueError(
                f"Fixed decision blank scalar: {decision_id}"
            )
        for field in ("alternatives", "fitness_functions"):
            values = row[field]
            if (
                not isinstance(values, list)
                or not values
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in values
                )
                or len(values) != len(set(values))
            ):
                raise ValueError(
                    f"Fixed decision invalid {field}: {decision_id}"
                )
        if row["selected"] in row["alternatives"]:
            raise ValueError(
                f"Fixed decision selected alternative repeated: {decision_id}"
            )
        if row["status"] != "ACCEPTED":
            raise ValueError(
                f"Fixed decision not accepted: {decision_id}"
            )
        governing_path = architecture_adr_path(row["governing_adr"])
        status_match = re.search(
            r"^\| Status \| `?([A-Z_]+)`? \|$",
            read(governing_path),
            flags=re.MULTILINE,
        )
        if status_match is None or status_match.group(1) != "ACCEPTED":
            raise ValueError(
                "Fixed decision governing ADR not accepted: "
                + decision_id
            )
        unknown_fitness = (
            set(row["fitness_functions"]) - set(fitness_definitions)
        )
        if unknown_fitness:
            raise ValueError(
                "Fixed decision fitness closure failed: "
                f"{decision_id}:"
                + ",".join(sorted(unknown_fitness))
            )
        decisions.append(
            {
                **copy.deepcopy(row),
                "source": str(FIXED_DECISION_ADR.relative_to(ROOT)),
                "source_digest": source_digest,
                "governing_adr_source": str(
                    governing_path.relative_to(ROOT)
                ),
                "governing_adr_digest": (
                    "sha256:" + sha256_file(governing_path)
                ),
            }
        )
    if (
        observed_ids != expected_ids
        or len(observed_ids) != len(set(observed_ids))
    ):
        raise ValueError(
            "Fixed decision ID range/order/uniqueness drift"
        )
    return decisions, fitness_definitions


def parse_worker_runtime_catalog() -> dict[str, Any]:
    text = read(WORKER_RUNTIME_ADR)
    candidates: list[dict[str, Any]] = []
    for block in re.findall(
        r"```yaml\s*\n(.*?)\n```",
        text,
        flags=re.DOTALL,
    ):
        parsed = load_yaml_text_strict(block)
        if (
            isinstance(parsed, dict)
            and parsed.get("catalog_id")
            == "RANEX-WORKER-RUNTIME-CATALOG"
        ):
            candidates.append(parsed)
    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one RANEX-WORKER-RUNTIME-CATALOG YAML block"
        )
    catalog = candidates[0]
    if set(catalog) != {
        "schema_version",
        "catalog_id",
        "catalog_version",
        "catalog_status",
        "governing_adr",
        "fixed_decision_count",
        "assignment_defaults",
        "role_profiles",
        "runtime_adapters",
    }:
        raise ValueError("Worker runtime catalog fields drift")
    if (
        catalog["schema_version"] != "worker-runtime-catalog/v1"
        or catalog["catalog_version"] != "1.0.0"
        or catalog["catalog_status"] != "DEFINITION_ONLY"
        or catalog["governing_adr"] != "ADR-0011"
        or catalog["fixed_decision_count"] != 29
    ):
        raise ValueError("Worker runtime catalog metadata drift")

    defaults = catalog["assignment_defaults"]
    expected_default_fields = {
        "effective_tool_ids",
        "effective_capability_ids",
        "leaf_worker",
        "worker_spawn",
        "worker_delegation",
        "worker_coordination",
        "adapter_fallback",
        "provider_fallback",
        "model_fallback",
        "auxiliary_model_calls",
        "nested_worker_lineage",
        "in_role_tool_loop",
        "ambient_user_settings",
        "ambient_project_settings",
        "ambient_local_settings",
        "ambient_mcp_servers",
        "ambient_plugins",
        "ambient_skills",
        "effect_path",
        "task_narrowing_required",
    }
    if (
        not isinstance(defaults, dict)
        or set(defaults) != expected_default_fields
        or defaults["effective_tool_ids"] != []
        or defaults["effective_capability_ids"] != []
        or defaults["leaf_worker"] is not True
        or defaults["worker_spawn"] != "DENIED"
        or defaults["worker_delegation"] != "DENIED"
        or defaults["worker_coordination"] != "DENIED"
        or defaults["adapter_fallback"] != "DISABLED"
        or defaults["provider_fallback"] != "DISABLED"
        or defaults["model_fallback"] != "DISABLED"
        or defaults["auxiliary_model_calls"] != "DISABLED"
        or defaults["nested_worker_lineage"] != "DENIED"
        or defaults["in_role_tool_loop"]
        != "BOUNDED_ALLOWED_WITHIN_EFFECTIVE_GRANT"
        or any(
            defaults[field] is not False
            for field in (
                "ambient_user_settings",
                "ambient_project_settings",
                "ambient_local_settings",
                "ambient_mcp_servers",
                "ambient_plugins",
                "ambient_skills",
            )
        )
        or defaults["effect_path"] != "POLICY_THEN_CAPABILITY_BUS"
        or defaults["task_narrowing_required"] is not True
    ):
        raise ValueError("Worker runtime assignment defaults unsafe")

    role_fields = {
        "role_profile_id",
        "version",
        "lifecycle",
        "role_class",
        "maximum_tool_ids",
        "maximum_capability_ids",
        "permanently_denied_capability_ids",
        "write_policy",
        "network_policy",
        "assignment_must_compile_strict_subset",
    }
    roles = catalog["role_profiles"]
    expected_role_ids = {
        "ROLEPROFILE-RESEARCH-READONLY-001",
        "ROLEPROFILE-IMPLEMENTATION-WORKER-001",
        "ROLEPROFILE-INDEPENDENT-REVIEWER-001",
    }
    if (
        not isinstance(roles, list)
        or len(roles) != 3
        or {row.get("role_profile_id") for row in roles}
        != expected_role_ids
    ):
        raise ValueError("Worker role profile denominator/ID drift")
    mandatory_denials = {
        "CAP-AUXILIARY-MODEL-CALL",
        "CAP-CANONICAL-AUTHORITY-WRITE",
        "CAP-CREDENTIAL-EXPORT",
        "CAP-LANDING",
        "CAP-ROUTE-MUTATE",
        "CAP-WORKER-COORDINATE",
        "CAP-WORKER-DELEGATE",
        "CAP-WORKER-SPAWN",
    }
    for row in roles:
        role_id = row["role_profile_id"]
        if set(row) != role_fields:
            raise ValueError(f"Worker role fields drift: {role_id}")
        for field in (
            "maximum_tool_ids",
            "maximum_capability_ids",
            "permanently_denied_capability_ids",
        ):
            values = row[field]
            if (
                not isinstance(values, list)
                or not values
                or values != sorted(values)
                or len(values) != len(set(values))
            ):
                raise ValueError(
                    f"Worker role invalid {field}: {role_id}"
                )
        if (
            row["version"] != "1.0.0"
            or row["lifecycle"] != "DEFINED_NOT_QUALIFIED"
            or row["assignment_must_compile_strict_subset"] is not True
            or not mandatory_denials
            <= set(row["permanently_denied_capability_ids"])
            or set(row["maximum_capability_ids"])
            & set(row["permanently_denied_capability_ids"])
        ):
            raise ValueError(f"Worker role safety drift: {role_id}")

    adapter_fields = {
        "runtime_adapter_id",
        "version",
        "lifecycle",
        "provider_family",
        "official_runtime",
        "protocol",
        "official_source",
        "exact_model_required",
        "exact_full_model_id_required",
        "leaf_worker_only",
        "worker_spawn",
        "worker_delegation",
        "adapter_fallback",
        "provider_fallback",
        "model_fallback",
        "auxiliary_model_calls",
        "ambient_configuration",
        "tool_surface_enforcement",
        "allowed_tools_semantics",
        "startup_attestation",
        "structured_events",
        "event_correlation",
        "nested_parent_tool_use_id",
        "cancellation",
        "resume",
        "preconnect",
        "auth_policy",
        "warm_reuse",
    }
    adapters = catalog["runtime_adapters"]
    expected_adapter_ids = {
        "RUNTIME-CLAUDE-AGENT-SDK-001",
        "RUNTIME-CODEX-APP-SERVER-001",
    }
    required_startup = {
        "ACTUAL_TOOL_SURFACE_EQUALS_EFFECTIVE_TOOL_GRANT",
        "AMBIENT_SOURCE_SET_EMPTY",
        "PINNED_SDK_AND_RUNTIME_DIGESTS_MATCH",
        "EFFECTIVE_AUTH_AND_ROUTE_MATCH_ROUTE_LOCK",
    }
    required_reuse_key = {
        "runtime_adapter_id",
        "runtime_adapter_version",
        "route_lock_digest",
        "effective_auth_subject_digest",
        "role_profile_digest",
        "effective_tool_grant_digest",
        "sandbox_profile_digest",
        "workspace_id",
        "assignment_id",
        "session_id",
    }
    if (
        not isinstance(adapters, list)
        or len(adapters) != 2
        or {row.get("runtime_adapter_id") for row in adapters}
        != expected_adapter_ids
    ):
        raise ValueError("Runtime adapter denominator/ID drift")
    for row in adapters:
        adapter_id = row["runtime_adapter_id"]
        expected_fields = set(adapter_fields)
        if adapter_id == "RUNTIME-CLAUDE-AGENT-SDK-001":
            expected_fields.add("forbidden_runtime_tool_names")
        if set(row) != expected_fields:
            raise ValueError(f"Runtime adapter fields drift: {adapter_id}")
        auth_policy = row["auth_policy"]
        warm_reuse = row["warm_reuse"]
        if (
            row["version"] != "1.0.0"
            or row["lifecycle"] != "DEFINED_NOT_QUALIFIED"
            or row["exact_model_required"] is not True
            or row["exact_full_model_id_required"] is not True
            or row["leaf_worker_only"] is not True
            or row["worker_spawn"] != "DENIED"
            or row["worker_delegation"] != "DENIED"
            or row["adapter_fallback"] != "DISABLED"
            or row["provider_fallback"] != "DISABLED"
            or row["model_fallback"] != "DISABLED"
            or row["auxiliary_model_calls"] != "DISABLED"
            or row["ambient_configuration"] != "DISABLED"
            or row["structured_events"] is not True
            or row["nested_parent_tool_use_id"]
            != "CONTAINMENT_VIOLATION"
            or not required_startup
            <= set(row["startup_attestation"])
            or len(row["startup_attestation"])
            != len(set(row["startup_attestation"]))
            or not isinstance(row["tool_surface_enforcement"], list)
            or not row["tool_surface_enforcement"]
            or len(row["tool_surface_enforcement"])
            != len(set(row["tool_surface_enforcement"]))
            or set(auth_policy)
            != {
                "local_individual_subscription",
                "product_api_or_cloud",
                "environment_precedence",
                "credential_file_extraction",
            }
            or auth_policy["environment_precedence"]
            != "SANITIZE_AND_ATTEST_BEFORE_DISPATCH"
            or auth_policy["credential_file_extraction"] != "DENIED"
            or row["preconnect"]
            != "ONLY_AFTER_COMPLETE_ASSIGNMENT_LEASE_AFFINITY_KEY_EXISTS"
            or set(warm_reuse)
            != {
                "scope",
                "cross_assignment",
                "cross_project",
                "key_fields",
            }
            or warm_reuse["scope"]
            != "SAME_ASSIGNMENT_AND_LOGICAL_SESSION_ONLY"
            or warm_reuse["cross_assignment"] is not False
            or warm_reuse["cross_project"] is not False
            or set(warm_reuse["key_fields"]) != required_reuse_key
            or len(warm_reuse["key_fields"]) != len(required_reuse_key)
        ):
            raise ValueError(f"Runtime adapter safety drift: {adapter_id}")
        tool_rules = set(row["tool_surface_enforcement"])
        if adapter_id == "RUNTIME-CLAUDE-AGENT-SDK-001":
            required_claude_rules = {
                "TOOLS_EXACT_EFFECTIVE_SET",
                "DISALLOWED_TOOLS_COMPLEMENT",
                "PERMISSION_MODE_DONT_ASK_NEVER_AUTO",
                "PRE_TOOL_USE_OR_SDK_CUSTOM_TOOL_GATEWAY_FOR_EVERY_ATTEMPT",
                "CAN_USE_TOOL_ASK_PATH_FALLBACK_ONLY",
                "NO_AGENT_DEFINITIONS_OR_AGENT_TEAM_DELEGATION_TOOLS",
                "STRICT_MCP_CONFIG",
                "SETTING_SOURCES_EMPTY",
                "AUTO_MEMORY_DISABLED",
                "EMPTY_SKILLS_AND_PLUGINS",
                "PER_ASSIGNMENT_CONFIG_HOME_AND_CWD",
                "BACKGROUND_EXECUTION_DISABLED",
                "RANEX_SANDBOX_AND_PATH_GUARD",
            }
            forbidden_tools = row["forbidden_runtime_tool_names"]
            if (
                tool_rules != required_claude_rules
                or not isinstance(forbidden_tools, list)
                or set(forbidden_tools)
                != {
                    "Agent",
                    "Task",
                    "Workflow",
                    "SendMessage",
                    "ToolSearch",
                    "Cron",
                    "RemoteTrigger",
                    "EnterWorktree",
                }
                or len(forbidden_tools) != len(set(forbidden_tools))
                or row["allowed_tools_semantics"]
                != "AUTO_APPROVAL_ONLY_NOT_RESTRICTION"
            ):
                raise ValueError(
                    f"Claude runtime tool policy drift: {adapter_id}"
                )
        else:
            required_codex_rules = {
                "STABLE_API_ONLY",
                "NO_DYNAMIC_TOOLS",
                "NO_NESTED_AGENT_OR_DELEGATION_SURFACE",
                "NO_AMBIENT_APPS_PLUGINS_MCP_OR_SKILLS",
                "NO_BACKGROUND_EXECUTION_SURFACE",
                "DENY_UNGRANTED_SERVER_APPROVAL_REQUESTS",
                "RANEX_CAPABILITY_CALLBACK",
                "RANEX_SANDBOX_AND_PATH_GUARD",
            }
            if (
                tool_rules != required_codex_rules
                or row["allowed_tools_semantics"]
                != "RANEX_EFFECTIVE_SET_IS_AUTHORITATIVE"
            ):
                raise ValueError(
                    f"Codex runtime tool policy drift: {adapter_id}"
                )
    return catalog


def parse_architecture() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    text = read(ARCH_DOC)
    contexts: list[dict[str, Any]] = []
    for heading, end, table_kind, source_fragment in [
        (
            "### 9.1",
            "### 9.2",
            "AUTHORITY",
            "91-nonreplaceable-authority-contexts",
        ),
        (
            "### 9.2",
            "### 9.3",
            "PRODUCT_DEVELOPMENT",
            "92-product-and-development-contexts",
        ),
        (
            "### 9.3",
            "## 10.",
            "OPERATIONS_BOUNDARY",
            "93-operations-evolution-and-boundary-contexts",
        ),
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
                    "source": (
                        "docs/architecture/"
                        "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#"
                        + source_fragment
                    ),
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
                "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#10-full-capability-attachment-matrix",
            }
        )

    decisions, _ = parse_fixed_decision_register()

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


def parse_estimate_commitment_control() -> dict[str, Any]:
    if sha256_file(CONTROL_DOC) != SDLC_CONTROL_CATALOG_SHA256:
        raise ValueError("SDLC control catalog pinned digest drift")
    matches = re.findall(
        (
            r"<!-- BEGIN SDLC ESTIMATE COMMITMENT CONTROL -->"
            r"\s*```yaml\n(.*?)\n```\s*"
            r"<!-- END SDLC ESTIMATE COMMITMENT CONTROL -->"
        ),
        read(CONTROL_DOC),
        flags=re.DOTALL,
    )
    if len(matches) != 1:
        raise ValueError(
            "Estimate/commitment marked control count drift"
        )
    if (
        hashlib.sha256(matches[0].encode("utf-8")).hexdigest()
        != ESTIMATE_COMMITMENT_BLOCK_SHA256
    ):
        raise ValueError(
            "Estimate/commitment marked control digest drift"
        )
    wrapper = load_yaml_text_strict(matches[0])
    if set(wrapper) != {"estimate_commitment_control"}:
        raise ValueError(
            "Estimate/commitment marked control wrapper drift"
        )
    contract = wrapper["estimate_commitment_control"]
    expected_keys = {
        "control_id",
        "control_version",
        "contract_id",
        "contract_version",
        "contract_projection_ref",
        "contract_projection_id",
        "contract_projection_contract",
        "applicability_rule_id",
        "owner_context",
        "decision_owner_context",
        "canonicalization",
        "digest_algorithm",
        "digest_encoding",
        "additional_properties",
        "noncompensating",
        "inherited_type_authority",
        "scalar_types",
        "cardinality_rule",
        "set_order_rule",
        "nested_types",
        "estimate_record",
        "commitment_subject_projection",
        "commitment_decision_role",
        "resolver_contract",
        "fixture_contract",
        "source_authority_contract",
    }
    if (
        set(contract) != expected_keys
        or contract["control_id"] != "SDLC-EST-001"
        or contract["control_version"] != "1.1.0"
        or contract["contract_id"]
        != "ESTIMATE-COMMITMENT-SEPARATION-1.1"
        or contract["contract_version"] != "1.1.0"
        or contract["canonicalization"] != "RFC8785"
        or contract["digest_algorithm"] != "SHA-256"
        or contract["additional_properties"] is not False
        or contract["noncompensating"] is not True
    ):
        raise ValueError(
            "Estimate/commitment marked control identity drift"
        )
    nested_rows = contract["nested_types"]
    if {
        row["type_id"]: len(row["fields"]) for row in nested_rows
    } != {
        "ContentAddressBindingV1": 2,
        "EstimateSourceEnvelopeAttestationV1": 18,
        "EstimateEvidenceBindingV1": 2,
        "EstimateBindingV1": 4,
    }:
        raise ValueError(
            "Estimate/commitment nested denominator drift"
        )
    estimate = contract["estimate_record"]
    projection = contract["commitment_subject_projection"]
    for row in [*nested_rows, estimate]:
        fields = row["fields"]
        if (
            row.get("additional_properties") is not False
            or len(fields) != len(set(fields))
            or set(fields) != set(row["field_types"])
            or not set(row.get("nullable_fields", [])) <= set(fields)
            or not set(row.get("array_cardinalities", {}))
            <= set(fields)
        ):
            raise ValueError(
                "Estimate/commitment type field drift: "
                + str(row.get("type_id"))
            )
    if (
        estimate["type_id"] != "EstimateObservationV1"
        or len(estimate["fields"]) != 25
        or estimate["schema_ref"]
        != "schemas/planning/estimate-observation-v1.schema.json"
        or "record_type" not in estimate["fields"]
        or "artifact_type" in estimate["fields"]
        or projection["projection_id"]
        != "DELIVERY_COMMITMENT_SUBJECT_V1"
        or len(projection["output_fields"]) != 20
        or len(projection["output_fields"])
        != len(set(projection["output_fields"]))
        or set(projection["output_fields"])
        != set(projection["field_types"])
        or projection["schema_ref"]
        != (
            "schemas/planning/"
            "delivery-commitment-subject-v1.schema.json"
        )
        or projection["additional_properties"] is not False
        or contract["contract_projection_ref"]
        != "architecture/contracts/estimate-commitment-control.json"
        or contract["contract_projection_id"]
        != "REG-ESTIMATE-COMMITMENT-CONTROL-001"
    ):
        raise ValueError(
            "Estimate/commitment record or projection drift"
        )
    resolver = contract["resolver_contract"]
    contract_projection = contract["contract_projection_contract"]
    if (
        contract_projection["additional_properties"] is not False
        or contract_projection["envelope_fields"]
        != [
            "registry_id",
            "version",
            "status",
            "source_path",
            "source_fragment",
            "source_digest",
            "generated_by",
            "entries",
        ]
        or set(contract_projection["envelope_fields"])
        != set(contract_projection["field_types"])
        or contract_projection["nullable_fields"]
        or contract_projection["array_cardinalities"]
        != {"entries": "exactly 1"}
    ):
        raise ValueError(
            "Estimate/commitment projection envelope drift"
        )
    if (
        resolver["resolver_id"]
        != "ESTIMATE-COMMITMENT-RESOLVER-1.1"
        or len(resolver["required_sources"]) != 11
        or len(resolver["evaluation_order"]) != 13
        or len(resolver["production_callers"]) != 2
        or resolver["optional_or_fixture_only_bypass"] is not False
    ):
        raise ValueError(
            "Estimate/commitment resolver denominator drift"
        )
    fixture = contract["fixture_contract"]
    positive_ids = fixture["positive_case_ids"]
    negative_by_boundary = fixture["negative_case_ids_by_boundary"]
    negative_ids = [
        case_id
        for rows in negative_by_boundary.values()
        for case_id in rows
    ]
    if (
        fixture["positive_suite_id"]
        != "SDLC_ESTIMATE_COMMITMENT_POSITIVE_V2"
        or fixture["negative_suite_id"]
        != "SDLC_ESTIMATE_COMMITMENT_NEGATIVE_V2"
        or len(positive_ids) != len(set(positive_ids))
        or len(positive_ids) != 6
        or positive_ids
        != sorted(positive_ids, key=lambda value: value.encode("utf-8"))
        or set(negative_by_boundary)
        != {
            "source_envelope_and_migration",
            "estimate_identity_and_history",
            "method_evidence_and_preparer",
            "estimate_value_and_currentness",
            "plan_population_and_window",
            "business_role_authorities",
            "owner_trace_and_time",
            "decision_authority",
            "authority_boundary",
        }
        or len(negative_ids) != len(set(negative_ids))
        or len(negative_ids) != 213
        or fixture["exact_positive_case_count"] != 6
        or fixture["exact_negative_case_count"] != 213
    ):
        raise ValueError(
            "Estimate/commitment fixture denominator drift"
        )
    source_authority = contract["source_authority_contract"]
    if (
        source_authority["source_contract_id"]
        != "ESTIMATE-COMMITMENT-SOURCE-AUTHORITY-2.0"
        or source_authority["source_contract_version"] != "2.0.0"
        or source_authority["compatibility_class"]
        != "BREAKING_SOURCE_ENVELOPE"
        or len(source_authority["role_authorities"]) != 11
        or len(source_authority["registry_shapes"]) != 11
        or len(source_authority["record_types"]) != 18
        or len(
            source_authority["supersession_pointer_catalog"]
        )
        != 15
    ):
        raise ValueError(
            "Estimate/commitment source authority denominator drift"
        )
    return contract


def build_state_registry() -> dict[str, Any]:
    text = read(ARCH_DOC)
    catalog = parse_state_axis_catalog(text)
    events_by_name = {
        event["event_name"]: event
        for event in parse_event_catalog(text)
    }
    event_names = set(events_by_name)
    enum_bindings = parse_event_enum_catalog(text)

    prose_axis_rows: list[tuple[str, str]] = []
    for line in section(
        text,
        "## 16. Canonical state axes",
        "`WorkflowNodeId`",
    ).splitlines():
        match = re.match(r"^\| `([^`]+)` \| (.*) \|$", line)
        if match is not None:
            prose_axis_rows.append((match.group(1), match.group(2)))
    prose_axis_ids = [axis_id for axis_id, _ in prose_axis_rows]
    enum_axis_ids = [binding["axis_id"] for binding in enum_bindings]
    catalog_axis_ids = [axis["axis_id"] for axis in catalog["axes"]]
    if (
        len(prose_axis_ids) != len(set(prose_axis_ids))
        or set(catalog_axis_ids)
        != set(prose_axis_ids) | set(enum_axis_ids)
    ):
        raise ValueError("State catalog drifts from §16/§17 axis sets")
    catalog_by_id = {
        axis["axis_id"]: axis for axis in catalog["axes"]
    }
    for axis_id, prose_cell in prose_axis_rows:
        positions = [
            prose_cell.find(f"`{value}`")
            for value in catalog_by_id[axis_id]["values"]
        ]
        if any(position < 0 for position in positions) or positions != sorted(
            positions
        ):
            raise ValueError(
                f"State catalog value/order drifts from §16: {axis_id}"
            )
    for axis in catalog["axes"]:
        unknown_events = (
            set(axis["integration_events"])
            | set(axis.get("referencing_events", []))
        ) - event_names
        if unknown_events:
            raise ValueError(
                "State catalog references unknown §17 events: "
                + axis["axis_id"]
                + ":"
                + ",".join(sorted(unknown_events))
            )
        wrong_owner_events = [
            event_name
            for event_name in axis["integration_events"]
            if events_by_name[event_name]["owner_context"]
            != axis["owner_context"]
        ]
        if wrong_owner_events:
            raise ValueError(
                "State integration event is not emitted by axis owner: "
                + axis["axis_id"]
                + ":"
                + ",".join(sorted(wrong_owner_events))
            )

    transition_pattern = re.compile(
        r"^([A-Z][A-Z0-9_]*)>([A-Z][A-Z0-9_]*)@"
        r"([A-Z][A-Z0-9_]*)$"
    )
    entries: list[dict[str, Any]] = []
    for source_axis in catalog["axes"]:
        transitions: list[dict[str, str]] = []
        for source_transition in source_axis["transitions"]:
            match = transition_pattern.fullmatch(source_transition)
            if match is None:
                raise ValueError(
                    "State parser accepted an invalid transition"
                )
            source, target, guard_id = match.groups()
            transitions.append(
                {
                    "from": source,
                    "to": target,
                    "guard_id": guard_id,
                }
            )
        entry = {
            **{
                key: copy.deepcopy(value)
                for key, value in source_axis.items()
                if key != "transitions"
            },
            "transitions": transitions,
            "transition_definition_status": (
                "DEFINED"
                if source_axis["axis_kind"] == "LIFECYCLE"
                else "NOT_APPLICABLE"
            ),
            "runtime_validation_status": "NOT_ASSESSED",
            "source": (
                "docs/architecture/"
                "HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#161-exact-axis-kind-and-lifecycle-transition-contract"
            ),
            "source_catalog_row_digest": (
                "sha256:"
                + sha256_bytes(canonical_bytes(source_axis))
            ),
        }
        entry["digest"] = digest_value(entry)
        entries.append(entry)

    transition_count = sum(
        len(axis["transitions"]) for axis in catalog["axes"]
    )
    result = registry(
        "REG-STATES-001",
        "1.0.0",
        entries,
        catalog_schema_version=catalog["schema_version"],
        catalog_id=catalog["catalog_id"],
        axis_count=catalog["axis_count"],
        lifecycle_axis_count=catalog["lifecycle_axis_count"],
        classifier_axis_count=catalog["classifier_axis_count"],
        value_count=catalog["value_count"],
        transition_count=transition_count,
        transition_notation=catalog["transition_notation"],
        transition_fact_ref=catalog["transition_fact_ref"],
        rejection_policy=copy.deepcopy(catalog["rejection_policy"]),
        source_path=str(ARCH_DOC.relative_to(ROOT)),
        source_digest="sha256:" + sha256_file(ARCH_DOC),
        source_catalog_digest=(
            "sha256:" + sha256_bytes(canonical_bytes(catalog))
        ),
        runtime_validation_status="NOT_ASSESSED",
    )
    result["digest"] = digest_value(result)
    return result


def transition_event_schema(
    state_registry: dict[str, Any],
) -> dict[str, Any]:
    """Compile TRANSITION-EVENT-V1 without moving catalog semantics into JSON Schema."""

    contract = parse_transition_fact_contract(read(ARCH_DOC))
    template = load_yaml_text_strict(
        read(TEMPLATES / "TRANSITION_EVENT.yaml")
    )
    field_names = [row["name"] for row in contract["required_fields"]]
    if list(template) != field_names:
        raise ValueError(
            "TRANSITION_EVENT template does not project the exact "
            "transition-fact field order"
        )
    lifecycle_axes = [
        axis
        for axis in state_registry["entries"]
        if axis["axis_kind"] == "LIFECYCLE"
    ]
    lifecycle_values = sorted(
        {
            value
            for axis in lifecycle_axes
            for value in axis["values"]
        }
    )
    lifecycle_axis_pattern = "(?:" + "|".join(
        re.escape(axis["axis_id"]) for axis in lifecycle_axes
    ) + ")"
    sha = {
        "type": "string",
        "pattern": r"^sha256:[0-9a-f]{64}$",
    }
    nonempty = {
        "type": "string",
        "minLength": 1,
        "maxLength": 1024,
        "pattern": r".*\S.*",
    }
    identifier = {
        "type": "string",
        "minLength": 1,
        "maxLength": 255,
        "pattern": r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,254}$",
    }
    artifact_ref = copy.deepcopy(nonempty)
    authority_ref = copy.deepcopy(nonempty)
    properties: dict[str, Any] = {
        "schema_version": {"const": "1"},
        "artifact_type": {"const": "transition_event"},
        "transition_id": {
            **identifier,
            "x-ranex-id-type": "TransitionEvent",
        },
        "state_catalog_ref": {
            "const": "architecture/contracts/states.json"
        },
        "state_catalog_digest": copy.deepcopy(sha),
        "axis_id": {
            "type": "string",
            "enum": [axis["axis_id"] for axis in lifecycle_axes],
        },
        "axis_version": {
            "type": "string",
            "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$",
        },
        "edge_id": {
            "type": "string",
            "pattern": (
                "^" + lifecycle_axis_pattern + ":"
                r"[0-9]+\.[0-9]+\.[0-9]+:"
                r"[A-Z][A-Z0-9_]*>[A-Z][A-Z0-9_]*@"
                r"[A-Z][A-Z0-9_]*$"
            ),
        },
        "guard_id": {
            "type": "string",
            "pattern": r"^[A-Z][A-Z0-9_]*$",
        },
        "owner_context": {
            "type": "string",
            "pattern": r"^[a-z][a-z0-9_]*$",
        },
        "aggregate_type": copy.deepcopy(identifier),
        "aggregate_id": copy.deepcopy(identifier),
        "aggregate_version_before": {
            "type": "integer",
            "minimum": 0,
        },
        "aggregate_version_after": {
            "type": "integer",
            "minimum": 0,
        },
        "from_state": {
            "type": "string",
            "enum": lifecycle_values,
        },
        "to_state": {
            "type": "string",
            "enum": lifecycle_values,
        },
        "recorded_prior_state": {
            "oneOf": [
                {
                    "type": "string",
                    "enum": lifecycle_values,
                },
                {"type": "null"},
            ]
        },
        "reason_code": copy.deepcopy(identifier),
        "command_id": {
            **copy.deepcopy(identifier),
            "x-ranex-id-type": "Command",
        },
        "correlation_id": {
            **copy.deepcopy(identifier),
            "x-ranex-id-type": "Correlation",
        },
        "causation_id": {
            **copy.deepcopy(identifier),
            "x-ranex-id-type": "Causation",
        },
        "subject_schema": {
            "oneOf": [copy.deepcopy(nonempty), {"type": "null"}]
        },
        "subject_ref": artifact_ref,
        "subject_digest": copy.deepcopy(sha),
        "subject_manifest_digest": {
            "oneOf": [copy.deepcopy(sha), {"type": "null"}]
        },
        "core_sdlc_trace_ref": copy.deepcopy(nonempty),
        "policy_decision_digest": copy.deepcopy(sha),
        "authority_refs": {
            "type": "array",
            "items": authority_ref,
            "minItems": 1,
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        },
        "evidence_refs": {
            "type": "array",
            "items": copy.deepcopy(artifact_ref),
            "minItems": 0,
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        },
        "invalidated_artifact_refs": {
            "type": "array",
            "items": copy.deepcopy(artifact_ref),
            "minItems": 0,
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        },
        "occurred_at": {
            "type": "string",
            "format": "date-time",
            "pattern": (
                r"^\d{4}-\d{2}-\d{2}T"
                r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
            ),
        },
        "digest": copy.deepcopy(sha),
    }
    if list(properties) != field_names:
        raise ValueError(
            "Compiled transition-event schema field order drift"
        )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/"
            "work/transition-event-v1.schema.json"
        ),
        "title": "Ranex TransitionEventV1",
        "type": "object",
        "properties": properties,
        "required": field_names,
        "additionalProperties": False,
        "x-ranex-contract-id": contract["contract_id"],
        "x-ranex-state-catalog-ref": (
            "architecture/contracts/states.json"
        ),
        "x-ranex-state-catalog-digest": state_registry["digest"],
        "x-ranex-semantic-invariants": copy.deepcopy(
            contract["semantic_invariants"]
        ),
        "x-ranex-idempotency-and-replay": copy.deepcopy(
            contract["idempotency_and_replay"]
        ),
        "x-ranex-source-contract-digest": (
            "sha256:" + sha256_bytes(canonical_bytes(contract))
        ),
        "x-ranex-template": (
            "docs/architecture/templates/TRANSITION_EVENT.yaml"
        ),
        "x-ranex-canonical-producer": "owning_aggregate_uow",
        "x-ranex-runtime-semantics": (
            "scripts/architecture/validate_contracts.py"
        ),
    }


def artifact_legal_hold_fact_schema() -> dict[str, Any]:
    """Compile the closed ArtifactLegalHoldFact contract from HERMES."""

    contract = parse_artifact_legal_hold_contract(read(ARCH_DOC))
    field_names = [row["name"] for row in contract["required_fields"]]
    sha = {
        "type": "string",
        "pattern": r"^sha256:[0-9a-f]{64}$",
    }
    identifier = {
        "type": "string",
        "minLength": 1,
        "maxLength": 255,
        "pattern": r"^[A-Za-z][A-Za-z0-9._:-]{0,254}$",
    }
    nonempty = {
        "type": "string",
        "minLength": 1,
        "maxLength": 1024,
        "pattern": r".*\S.*",
    }

    def typed_ref(type_name: str) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "id": {
                    **copy.deepcopy(identifier),
                    "x-ranex-id-type": type_name,
                },
                "digest": copy.deepcopy(sha),
            },
            "required": ["id", "digest"],
            "additionalProperties": False,
            "x-ranex-ref-type": type_name,
        }

    properties: dict[str, Any] = {
        "schema_version": {"const": "1"},
        "artifact_type": {"const": "artifact_legal_hold_fact"},
        "fact_id": {
            **copy.deepcopy(identifier),
            "x-ranex-id-type": "ArtifactLegalHoldFact",
        },
        "legal_hold_id": {
            **copy.deepcopy(identifier),
            "x-ranex-id-type": "ArtifactLegalHold",
        },
        "artifact_id": {
            **copy.deepcopy(identifier),
            "x-ranex-id-type": "Artifact",
        },
        "artifact_digest": copy.deepcopy(sha),
        "owner_context": {"const": "artifact_management"},
        "producer_service_id": {
            "const": "artifact_legal_hold_service"
        },
        "action": {
            "type": "string",
            "enum": ["APPLIED", "RELEASED", "INVALIDATED"],
        },
        "expected_prior_fact_ref": {
            "oneOf": [
                typed_ref("ArtifactLegalHoldFact"),
                {"type": "null"},
            ]
        },
        "authority_grant_ref": typed_ref(
            "ConsumableAuthorityGrant"
        ),
        "human_decision_ref": typed_ref("HumanDecisionRecord"),
        "jurisdiction": copy.deepcopy(nonempty),
        "reason_code": copy.deepcopy(identifier),
        "recorded_at": {
            "type": "string",
            "format": "date-time",
            "pattern": (
                r"^\d{4}-\d{2}-\d{2}T"
                r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
            ),
        },
        "digest": copy.deepcopy(sha),
    }
    if list(properties) != field_names:
        raise ValueError(
            "Compiled ArtifactLegalHoldFact schema field order drift"
        )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/artifacts/"
            "artifact-legal-hold-fact-v1.schema.json"
        ),
        "title": "Ranex ArtifactLegalHoldFactV1",
        "type": "object",
        "properties": properties,
        "required": field_names,
        "additionalProperties": False,
        "x-ranex-contract-id": contract["contract_id"],
        "x-ranex-semantic-invariants": copy.deepcopy(
            contract["semantic_invariants"]
        ),
        "x-ranex-fixture-denominator": copy.deepcopy(
            contract["fixture_denominator"]
        ),
        "x-ranex-source-contract-digest": (
            "sha256:" + sha256_bytes(canonical_bytes(contract))
        ),
        "x-ranex-canonical-producer": (
            "artifact_legal_hold_service"
        ),
        "x-ranex-owner-context": "artifact_management",
        "x-ranex-runtime-semantics": (
            "scripts/architecture/validate_contracts.py"
        ),
    }


def artifact_legal_hold_ref(
    type_name: str,
    seed: str,
) -> dict[str, str]:
    prefixes = {
        "ArtifactLegalHoldFact": "artifact_legal_hold_fact",
        "ConsumableAuthorityGrant": "authority_grant",
        "HumanDecisionRecord": "human_decision",
    }
    return {
        "id": (
            prefixes[type_name]
            + "_"
            + deterministic_uuid7(seed)
        ),
        "digest": (
            "sha256:"
            + sha256_bytes((type_name + ":" + seed).encode("utf-8"))
        ),
    }


def artifact_legal_hold_fact(
    action: str,
    *,
    seed: str,
    prior_fact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    fact = {
        "schema_version": "1",
        "artifact_type": "artifact_legal_hold_fact",
        "fact_id": (
            "artifact_legal_hold_fact_"
            + deterministic_uuid7(seed + ":fact")
        ),
        "legal_hold_id": (
            "artifact_legal_hold_"
            + deterministic_uuid7(seed + ":hold")
        ),
        "artifact_id": (
            "art_" + deterministic_uuid7(seed + ":artifact")
        ),
        "artifact_digest": (
            "sha256:"
            + sha256_bytes((seed + ":artifact").encode("utf-8"))
        ),
        "owner_context": "artifact_management",
        "producer_service_id": "artifact_legal_hold_service",
        "action": action,
        "expected_prior_fact_ref": (
            {
                "id": prior_fact["fact_id"],
                "digest": prior_fact["digest"],
            }
            if prior_fact is not None
            else None
        ),
        "authority_grant_ref": artifact_legal_hold_ref(
            "ConsumableAuthorityGrant",
            seed + ":authority",
        ),
        "human_decision_ref": artifact_legal_hold_ref(
            "HumanDecisionRecord",
            seed + ":decision",
        ),
        "jurisdiction": "PH",
        "reason_code": (
            "LEGAL_HOLD_APPLIED"
            if action == "APPLIED"
            else "LEGAL_HOLD_" + action
        ),
        "recorded_at": FIXED_TIME,
        "digest": "",
    }
    fact["digest"] = digest_value(fact)
    return fact


def artifact_legal_hold_world(
    fact: dict[str, Any],
    *,
    prior_fact: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "artifact_status_before": "AVAILABLE",
        "artifact_status_after": "AVAILABLE",
        "resolved_prior_fact": copy.deepcopy(prior_fact),
        "prior_fact_is_current": prior_fact is not None,
        "chain_already_terminal": False,
        "human_decision": {
            "ref": copy.deepcopy(fact["human_decision_ref"]),
            "current": True,
            "subject_artifact_id": fact["artifact_id"],
            "subject_artifact_digest": fact["artifact_digest"],
            "action": fact["action"],
        },
        "authority_grant": {
            "ref": copy.deepcopy(fact["authority_grant_ref"]),
            "current": True,
            "consumed": False,
            "subject_artifact_id": fact["artifact_id"],
            "subject_artifact_digest": fact["artifact_digest"],
            "action": fact["action"],
        },
        "purge_requested": False,
        "effective_hold_at_purge_recheck": False,
        "concurrent_apply_purge_serialized": True,
        "purge_tombstone": None,
    }


def build_artifact_legal_hold_fixture_suite() -> dict[str, Any]:
    """Build every case in the source-declared 51-case denominator."""

    contract = parse_artifact_legal_hold_contract(read(ARCH_DOC))
    cases: list[dict[str, Any]] = []

    applied = artifact_legal_hold_fact(
        "APPLIED",
        seed="legal-hold-valid-applied",
    )
    applied_world = artifact_legal_hold_world(applied)
    cases.append(
        {
            "case_id": "LEGAL-HOLD-VALID-APPLIED",
            "category": "valid_action_shapes",
            "expected_result": "PASS",
            "fact": applied,
            "world": applied_world,
        }
    )
    for action in ("RELEASED", "INVALIDATED"):
        seed = "legal-hold-valid-" + action.lower()
        prior = artifact_legal_hold_fact("APPLIED", seed=seed)
        terminal = artifact_legal_hold_fact(
            action,
            seed=seed,
            prior_fact=prior,
        )
        terminal["legal_hold_id"] = prior["legal_hold_id"]
        terminal["artifact_id"] = prior["artifact_id"]
        terminal["artifact_digest"] = prior["artifact_digest"]
        terminal["digest"] = digest_value(terminal)
        cases.append(
            {
                "case_id": "LEGAL-HOLD-VALID-" + action,
                "category": "valid_action_shapes",
                "expected_result": "PASS",
                "fact": terminal,
                "world": artifact_legal_hold_world(
                    terminal,
                    prior_fact=prior,
                ),
            }
        )

    schema_sample = copy.deepcopy(applied)
    for field_name in contract["required_fields"]:
        mutated = copy.deepcopy(schema_sample)
        del mutated[field_name["name"]]
        cases.append(
            {
                "case_id": (
                    "LEGAL-HOLD-OMIT-"
                    + slug(field_name["name"])
                ),
                "category": "required_field_omission_negative",
                "expected_error": (
                    "ARTIFACT_LEGAL_HOLD_FACT_SCHEMA_INVALID"
                ),
                "fact": mutated,
                "world": copy.deepcopy(applied_world),
            }
        )

    wrong_types: dict[str, Any] = {
        "schema_version": 1,
        "artifact_type": False,
        "fact_id": 7,
        "legal_hold_id": 7,
        "artifact_id": 7,
        "artifact_digest": 7,
        "owner_context": 7,
        "producer_service_id": 7,
        "action": 7,
        "expected_prior_fact_ref": [],
        "authority_grant_ref": "not-a-ref",
        "human_decision_ref": "not-a-ref",
        "jurisdiction": 7,
        "reason_code": 7,
        "recorded_at": 7,
        "digest": 7,
    }
    for field_name in contract["required_fields"]:
        name = field_name["name"]
        mutated = copy.deepcopy(schema_sample)
        mutated[name] = copy.deepcopy(wrong_types[name])
        cases.append(
            {
                "case_id": "LEGAL-HOLD-WRONG-TYPE-" + slug(name),
                "category": "wrong_field_type_negative",
                "expected_error": (
                    "ARTIFACT_LEGAL_HOLD_FACT_SCHEMA_INVALID"
                ),
                "fact": mutated,
                "world": copy.deepcopy(applied_world),
            }
        )

    additional = copy.deepcopy(schema_sample)
    additional["forged_unknown_field"] = True
    cases.append(
        {
            "case_id": "LEGAL-HOLD-ADDITIONAL-PROPERTY",
            "category": "additional_property_negative",
            "expected_error": (
                "ARTIFACT_LEGAL_HOLD_FACT_SCHEMA_INVALID"
            ),
            "fact": additional,
            "world": copy.deepcopy(applied_world),
        }
    )

    def semantic_case(
        dimension: str,
        fact: dict[str, Any],
        world: dict[str, Any],
    ) -> None:
        fact["digest"] = digest_value(fact)
        cases.append(
            {
                "case_id": "LEGAL-HOLD-SEMANTIC-" + dimension,
                "category": "semantic_negative",
                "semantic_dimension": dimension,
                "expected_error": dimension,
                "fact": fact,
                "world": world,
            }
        )

    fact = copy.deepcopy(applied)
    prior = artifact_legal_hold_fact(
        "APPLIED",
        seed="legal-hold-semantic-applied-with-prior",
    )
    fact["expected_prior_fact_ref"] = {
        "id": prior["fact_id"],
        "digest": prior["digest"],
    }
    semantic_case(
        "APPLIED_WITH_PRIOR",
        fact,
        artifact_legal_hold_world(fact, prior_fact=prior),
    )

    for dimension in (
        "TERMINAL_WITHOUT_PRIOR",
        "PRIOR_NOT_CURRENT_APPLIED",
        "PRIOR_HOLD_MISMATCH",
        "PRIOR_ARTIFACT_ID_MISMATCH",
        "PRIOR_ARTIFACT_DIGEST_MISMATCH",
        "DUPLICATE_TERMINAL",
    ):
        seed = "legal-hold-semantic-" + dimension.lower()
        prior = artifact_legal_hold_fact("APPLIED", seed=seed)
        fact = artifact_legal_hold_fact(
            "RELEASED",
            seed=seed,
            prior_fact=prior,
        )
        fact["legal_hold_id"] = prior["legal_hold_id"]
        fact["artifact_id"] = prior["artifact_id"]
        fact["artifact_digest"] = prior["artifact_digest"]
        world = artifact_legal_hold_world(fact, prior_fact=prior)
        if dimension == "TERMINAL_WITHOUT_PRIOR":
            fact["expected_prior_fact_ref"] = None
            world["resolved_prior_fact"] = None
            world["prior_fact_is_current"] = False
        elif dimension == "PRIOR_NOT_CURRENT_APPLIED":
            world["prior_fact_is_current"] = False
        elif dimension == "PRIOR_HOLD_MISMATCH":
            prior["legal_hold_id"] = (
                "artifact_legal_hold_"
                + deterministic_uuid7(seed + ":other-hold")
            )
            prior["digest"] = digest_value(prior)
            fact["expected_prior_fact_ref"] = {
                "id": prior["fact_id"],
                "digest": prior["digest"],
            }
            world["resolved_prior_fact"] = prior
        elif dimension == "PRIOR_ARTIFACT_ID_MISMATCH":
            prior["artifact_id"] = (
                "art_" + deterministic_uuid7(seed + ":other-artifact")
            )
            prior["digest"] = digest_value(prior)
            fact["expected_prior_fact_ref"] = {
                "id": prior["fact_id"],
                "digest": prior["digest"],
            }
            world["resolved_prior_fact"] = prior
        elif dimension == "PRIOR_ARTIFACT_DIGEST_MISMATCH":
            prior["artifact_digest"] = (
                "sha256:"
                + sha256_bytes(
                    (seed + ":other-digest").encode("utf-8")
                )
            )
            prior["digest"] = digest_value(prior)
            fact["expected_prior_fact_ref"] = {
                "id": prior["fact_id"],
                "digest": prior["digest"],
            }
            world["resolved_prior_fact"] = prior
        elif dimension == "DUPLICATE_TERMINAL":
            world["chain_already_terminal"] = True
        semantic_case(dimension, fact, world)

    for dimension in (
        "ACTION_ON_PURGED",
        "WRONG_OWNER",
        "WRONG_PRODUCER",
        "MISSING_OR_STALE_HUMAN_DECISION",
        "MISSING_OR_CONSUMED_AUTHORITY_GRANT",
        "PURGE_WHILE_HOLD_ACTIVE",
        "CONCURRENT_APPLY_PURGE_RACE",
        "HOLD_ACTION_MUTATES_ARTIFACT_STATUS",
    ):
        fact = artifact_legal_hold_fact(
            "APPLIED",
            seed="legal-hold-semantic-" + dimension.lower(),
        )
        world = artifact_legal_hold_world(fact)
        if dimension == "ACTION_ON_PURGED":
            world["artifact_status_before"] = "PURGED"
            world["artifact_status_after"] = "PURGED"
        elif dimension == "WRONG_OWNER":
            fact["owner_context"] = "policy"
        elif dimension == "WRONG_PRODUCER":
            fact["producer_service_id"] = "artifact_service"
        elif dimension == "MISSING_OR_STALE_HUMAN_DECISION":
            world["human_decision"]["current"] = False
        elif dimension == "MISSING_OR_CONSUMED_AUTHORITY_GRANT":
            world["authority_grant"]["consumed"] = True
        elif dimension == "PURGE_WHILE_HOLD_ACTIVE":
            world["purge_requested"] = True
            world["effective_hold_at_purge_recheck"] = True
        elif dimension == "CONCURRENT_APPLY_PURGE_RACE":
            world["purge_requested"] = True
            world["concurrent_apply_purge_serialized"] = False
        elif dimension == "HOLD_ACTION_MUTATES_ARTIFACT_STATUS":
            world["artifact_status_after"] = "QUARANTINED"
        semantic_case(dimension, fact, world)

    category_counts = Counter(case["category"] for case in cases)
    denominator = contract["fixture_denominator"]
    for category in (
        "valid_action_shapes",
        "required_field_omission_negative",
        "wrong_field_type_negative",
        "additional_property_negative",
        "semantic_negative",
    ):
        if category_counts[category] != denominator[category]:
            raise ValueError(
                "Artifact legal-hold fixture category drift: "
                + category
            )
    if len(cases) != denominator["exact_case_count"]:
        raise ValueError("Artifact legal-hold exact fixture drift")
    if [
        case["semantic_dimension"]
        for case in cases
        if case["category"] == "semantic_negative"
    ] != denominator["semantic_negative_dimensions"]:
        raise ValueError(
            "Artifact legal-hold semantic dimension drift"
        )
    return {
        "fixture_suite": "ARTIFACT_LEGAL_HOLD_FACT_CONTRACT",
        "schema_ref": contract["schema_ref"],
        "source_contract_digest": (
            "sha256:" + sha256_bytes(canonical_bytes(contract))
        ),
        "denominator": copy.deepcopy(denominator),
        "cases": cases,
    }


def build_state_transition_fixture_suite() -> dict[str, Any]:
    catalog = parse_state_axis_catalog(read(ARCH_DOC))
    positive_edges: list[dict[str, Any]] = []
    unsatisfied_guard_edges: list[dict[str, Any]] = []
    prohibited_pairs: list[dict[str, Any]] = []
    classifier_pairs: list[dict[str, Any]] = []
    for axis in catalog["axes"]:
        if axis["axis_kind"] == "CLASSIFIER":
            for source in axis["values"]:
                for target in axis["values"]:
                    if source == target:
                        continue
                    classifier_pairs.append(
                        {
                            "case_id": (
                                "STATE-CLASSIFIER-DENY-"
                                + slug(axis["axis_id"])
                                + "-"
                                + source
                                + "-"
                                + target
                            ),
                            "axis_id": axis["axis_id"],
                            "from": source,
                            "to": target,
                            "expected_error": (
                                "CLASSIFIER_TRANSITION_FORBIDDEN"
                            ),
                        }
                    )
            continue
        allowed_pairs: set[tuple[str, str]] = set()
        for transition in axis["transitions"]:
            source_target, guard_id = transition.split("@", 1)
            source, target = source_target.split(">", 1)
            allowed_pairs.add((source, target))
            case_suffix = (
                slug(axis["axis_id"])
                + "-"
                + source
                + "-"
                + target
            )
            positive_edges.append(
                {
                    "case_id": "STATE-ALLOW-" + case_suffix,
                    "axis_id": axis["axis_id"],
                    "from": source,
                    "to": target,
                    "guard_id": guard_id,
                    "expected_result": "ACCEPT",
                }
            )
            unsatisfied_guard_edges.append(
                {
                    "case_id": (
                        "STATE-DENY-UNSATISFIED-GUARD-"
                        + case_suffix
                    ),
                    "axis_id": axis["axis_id"],
                    "from": source,
                    "to": target,
                    "guard_id": guard_id,
                    "expected_error": "UNSATISFIED_GUARD",
                }
            )
        for source in axis["values"]:
            for target in axis["values"]:
                if source == target or (source, target) in allowed_pairs:
                    continue
                prohibited_pairs.append(
                    {
                        "case_id": (
                            "STATE-DENY-PAIR-"
                            + slug(axis["axis_id"])
                            + "-"
                            + source
                            + "-"
                            + target
                        ),
                        "axis_id": axis["axis_id"],
                        "from": source,
                        "to": target,
                        "expected_error": "ILLEGAL_EDGE",
                    }
                )
    if not positive_edges:
        raise ValueError("State transition fixture source has no edge")
    base_case_id = positive_edges[0]["case_id"]
    recorded_prior_case_id = next(
        case["case_id"]
        for case in positive_edges
        if case["from"] == "BLOCKED"
        and (
            "RESUME" in case["guard_id"]
            or "RESOLVED_TO_RECORDED" in case["guard_id"]
        )
    )
    rejection_cases = [
        {
            "case_id": "STATE-DENY-UNKNOWN-AXIS",
            "base_case_id": base_case_id,
            "mutation": "UNKNOWN_AXIS",
            "expected_error": "UNKNOWN_AXIS_OR_VALUE",
        },
        {
            "case_id": "STATE-DENY-UNKNOWN-VALUE",
            "base_case_id": base_case_id,
            "mutation": "UNKNOWN_VALUE",
            "expected_error": "UNKNOWN_AXIS_OR_VALUE",
        },
        {
            "case_id": "STATE-DENY-WRONG-OWNER",
            "base_case_id": base_case_id,
            "mutation": "WRONG_OWNER_OR_AUTHORITY",
            "expected_error": "WRONG_OWNER_OR_AUTHORITY",
        },
        {
            "case_id": "STATE-DENY-STALE-AXIS-VERSION",
            "base_case_id": base_case_id,
            "mutation": "STALE_AXIS_VERSION",
            "expected_error": "STALE_AGGREGATE_VERSION",
        },
        {
            "case_id": "STATE-DENY-STALE-AGGREGATE-VERSION",
            "base_case_id": base_case_id,
            "mutation": "STALE_AGGREGATE_VERSION",
            "expected_error": "STALE_AGGREGATE_VERSION",
        },
        {
            "case_id": "STATE-DENY-WRONG-PRIOR-STATE",
            "base_case_id": recorded_prior_case_id,
            "mutation": "WRONG_RECORDED_PRIOR_STATE",
            "expected_error": "WRONG_RECORDED_PRIOR_STATE",
        },
        {
            "case_id": "STATE-DENY-MISSING-EVIDENCE",
            "base_case_id": base_case_id,
            "mutation": "MISSING_EVIDENCE",
            "expected_error": "MISSING_OR_STALE_EVIDENCE",
        },
        {
            "case_id": "STATE-DENY-STALE-EVIDENCE",
            "base_case_id": base_case_id,
            "mutation": "STALE_EVIDENCE",
            "expected_error": "MISSING_OR_STALE_EVIDENCE",
        },
        {
            "case_id": "STATE-DENY-CROSS-SUBJECT-EVIDENCE",
            "base_case_id": base_case_id,
            "mutation": "CROSS_SUBJECT_EVIDENCE",
            "expected_error": "MISSING_OR_STALE_EVIDENCE",
        },
        {
            "case_id": "STATE-DENY-MISSING-GUARD",
            "base_case_id": base_case_id,
            "mutation": "MISSING_GUARD",
            "expected_error": "UNSATISFIED_GUARD",
        },
    ]
    first_lifecycle = next(
        axis
        for axis in catalog["axes"]
        if axis["axis_kind"] == "LIFECYCLE"
    )
    first_classifier = next(
        axis
        for axis in catalog["axes"]
        if axis["axis_kind"] == "CLASSIFIER"
    )
    registry_mutation_cases = [
        {
            "case_id": "STATE-REGISTRY-DUPLICATE-AXIS",
            "mutation": "DUPLICATE_AXIS",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_AXIS_DUPLICATE",
        },
        {
            "case_id": "STATE-REGISTRY-VALUE-ORDER-DRIFT",
            "mutation": "SWAP_FIRST_TWO_VALUES",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_VALUE_ORDER_DRIFT",
        },
        {
            "case_id": "STATE-REGISTRY-OWNER-DRIFT",
            "mutation": "OWNER_DRIFT",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_AXIS_IDENTITY_DRIFT",
        },
        {
            "case_id": "STATE-REGISTRY-VERSION-DRIFT",
            "mutation": "AXIS_VERSION_DRIFT",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_AXIS_IDENTITY_DRIFT",
        },
        {
            "case_id": "STATE-REGISTRY-CONTRACT-REF-DRIFT",
            "mutation": "CONTRACT_REF_DRIFT",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_AXIS_IDENTITY_DRIFT",
        },
        {
            "case_id": "STATE-REGISTRY-CLASSIFIER-TRANSITION",
            "mutation": "ADD_CLASSIFIER_TRANSITION",
            "axis_id": first_classifier["axis_id"],
            "expected_error": "STATE_CLASSIFIER_TRANSITION",
        },
        {
            "case_id": "STATE-REGISTRY-TERMINAL-OUTGOING",
            "mutation": "ADD_TERMINAL_OUTGOING",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_TERMINAL_OUTGOING",
        },
        {
            "case_id": "STATE-REGISTRY-PLACEHOLDER-STATUS",
            "mutation": "VALUES_ONLY_PLACEHOLDER",
            "axis_id": first_lifecycle["axis_id"],
            "expected_error": "STATE_TRANSITION_PLACEHOLDER",
        },
    ]
    stale_terminal_values = {
        "CapabilityAssessmentStatus": "COMPLETE",
        "HumanDecisionRecordStatus": "APPROVED",
        "MigrationStatus": "FAILED",
        "SyncCandidateStatus": "ROLLED_BACK",
    }
    catalog_by_id = {
        axis["axis_id"]: axis for axis in catalog["axes"]
    }
    for axis_id, stale_value in stale_terminal_values.items():
        if (
            axis_id in catalog_by_id
            and stale_value in catalog_by_id[axis_id]["values"]
        ):
            registry_mutation_cases.append(
                {
                    "case_id": (
                        "STATE-REGISTRY-STALE-TERMINAL-"
                        + slug(axis_id)
                        + "-"
                        + stale_value
                    ),
                    "mutation": "TOGGLE_TERMINAL_VALUE",
                    "axis_id": axis_id,
                    "value": stale_value,
                    "expected_error": "STATE_TERMINAL_SET_DRIFT",
                }
            )
    events_by_name = {
        event["event_name"]: event
        for event in parse_event_catalog(read(ARCH_DOC))
    }
    cross_owner_reference = next(
        (axis, event_name)
        for axis in catalog["axes"]
        for event_name in axis.get("referencing_events", [])
        if events_by_name[event_name]["owner_context"]
        != axis["owner_context"]
    )
    registry_mutation_cases.append(
        {
            "case_id": "STATE-REGISTRY-CROSS-OWNER-EMISSION",
            "mutation": "MOVE_REFERENCE_TO_INTEGRATION",
            "axis_id": cross_owner_reference[0]["axis_id"],
            "event_name": cross_owner_reference[1],
            "expected_error": "STATE_EVENT_OWNER_MISMATCH",
        }
    )
    stream_cases = [
        {
            "case_id": "STATE-STREAM-IDEMPOTENT-REPLAY",
            "mutation": "DUPLICATE_SAME_ID_SAME_BYTES",
            "expected_result": "IDEMPOTENT_REPLAY",
        },
        {
            "case_id": "STATE-STREAM-ID-REUSE-DIFFERENT-BYTES",
            "mutation": "DUPLICATE_SAME_ID_DIFFERENT_BYTES",
            "expected_error": "TRANSITION_FACT_ID_CONFLICT",
        },
        {
            "case_id": "STATE-STREAM-OUT-OF-ORDER",
            "mutation": "OUT_OF_ORDER_SEQUENCE",
            "expected_error": "TRANSITION_SEQUENCE_OUT_OF_ORDER",
        },
        {
            "case_id": "STATE-STREAM-SEQUENCE-GAP",
            "mutation": "SEQUENCE_GAP",
            "expected_error": "TRANSITION_SEQUENCE_GAP",
        },
    ]
    lifecycle_pair_count = sum(
        len(axis["values"]) * (len(axis["values"]) - 1)
        for axis in catalog["axes"]
        if axis["axis_kind"] == "LIFECYCLE"
    )
    return {
        "fixture_suite": "STATE_AXIS_TRANSITION_CONTRACT",
        "catalog_id": catalog["catalog_id"],
        "source_catalog_digest": (
            "sha256:" + sha256_bytes(canonical_bytes(catalog))
        ),
        "axis_count": len(catalog["axes"]),
        "lifecycle_axis_count": sum(
            axis["axis_kind"] == "LIFECYCLE"
            for axis in catalog["axes"]
        ),
        "classifier_axis_count": sum(
            axis["axis_kind"] == "CLASSIFIER"
            for axis in catalog["axes"]
        ),
        "lifecycle_ordered_nonself_pair_count": lifecycle_pair_count,
        "allowed_pair_count": len(positive_edges),
        "prohibited_pair_count": len(prohibited_pairs),
        "classifier_ordered_nonself_pair_count": len(classifier_pairs),
        "positive_edges": positive_edges,
        "unsatisfied_guard_edges": unsatisfied_guard_edges,
        "prohibited_pairs": prohibited_pairs,
        "classifier_pairs": classifier_pairs,
        "rejection_cases": rejection_cases,
        "registry_mutation_cases": registry_mutation_cases,
        "stream_cases": stream_cases,
    }


def split_state_edge(edge: str) -> tuple[str, str, str]:
    pair, guard_id = edge.split("@", 1)
    source, target = pair.split(">", 1)
    return source, target, guard_id


def canonical_state_edge_id(
    axis_id: str,
    axis_version: str,
    source: str,
    target: str,
    guard_id: str,
) -> str:
    return (
        f"{axis_id}:{axis_version}:{source}>{target}@{guard_id}"
    )


def transition_recorded_prior(
    source: str,
    target: str,
) -> str | None:
    if target == "BLOCKED":
        return source
    if source == "BLOCKED":
        return target
    return None


def canonical_transition_request(
    axis: dict[str, Any],
    source: str,
    target: str,
    guard_id: str,
    case_id: str,
) -> dict[str, Any]:
    subject_ref = (
        "state-subject:"
        + axis["axis_id"]
        + ":"
        + source
        + ":"
        + target
    )
    subject_digest = (
        "sha256:"
        + sha256_bytes(
            canonical_bytes(
                {
                    "axis_id": axis["axis_id"],
                    "from_state": source,
                    "to_state": target,
                }
            )
        )
    )
    return {
        "request_id": "transition-request:" + slug(case_id),
        "state_catalog_ref": "architecture/contracts/states.json",
        "axis_id": axis["axis_id"],
        "axis_version": axis["axis_version"],
        "owner_context": axis["owner_context"],
        "authenticated_transition_authority": axis[
            "transition_authority"
        ],
        "aggregate_type": axis["axis_id"] + "Aggregate",
        "aggregate_id": "aggregate:" + slug(case_id),
        "expected_aggregate_version": 7,
        "persisted_aggregate_version": 7,
        "persisted_current_state": source,
        "from_state": source,
        "to_state": target,
        "recorded_prior_state": transition_recorded_prior(
            source,
            target,
        ),
        "guard_id": guard_id,
        "guard_satisfied": True,
        "subject_ref": subject_ref,
        "subject_digest": subject_digest,
        "authority_refs": ["authority:" + slug(case_id)],
        "evidence": [
            {
                "evidence_ref": "evidence:" + slug(case_id),
                "subject_ref": subject_ref,
                "subject_digest": subject_digest,
                "freshness_status": "CURRENT",
            }
        ],
        "requested_at": FIXED_TIME,
    }


def canonical_transition_fact(
    state_registry: dict[str, Any],
    axis: dict[str, Any],
    source: str,
    target: str,
    guard_id: str,
    case_id: str,
    *,
    aggregate_type: str | None = None,
    aggregate_id: str | None = None,
    aggregate_version_before: int = 7,
) -> dict[str, Any]:
    request = canonical_transition_request(
        axis,
        source,
        target,
        guard_id,
        case_id,
    )
    fact = {
        "schema_version": "1",
        "artifact_type": "transition_event",
        "transition_id": (
            "transition_"
            + sha256_bytes(case_id.encode("utf-8"))[:32]
        ),
        "state_catalog_ref": "architecture/contracts/states.json",
        "state_catalog_digest": state_registry["digest"],
        "axis_id": axis["axis_id"],
        "axis_version": axis["axis_version"],
        "edge_id": canonical_state_edge_id(
            axis["axis_id"],
            axis["axis_version"],
            source,
            target,
            guard_id,
        ),
        "guard_id": guard_id,
        "owner_context": axis["owner_context"],
        "aggregate_type": (
            aggregate_type
            if aggregate_type is not None
            else request["aggregate_type"]
        ),
        "aggregate_id": (
            aggregate_id
            if aggregate_id is not None
            else request["aggregate_id"]
        ),
        "aggregate_version_before": aggregate_version_before,
        "aggregate_version_after": aggregate_version_before + 1,
        "from_state": source,
        "to_state": target,
        "recorded_prior_state": transition_recorded_prior(
            source,
            target,
        ),
        "reason_code": "FIXTURE_TRANSITION",
        "command_id": "command:" + slug(case_id),
        "correlation_id": "correlation:" + slug(case_id),
        "causation_id": "causation:" + slug(case_id),
        "subject_schema": None,
        "subject_ref": request["subject_ref"],
        "subject_digest": request["subject_digest"],
        "subject_manifest_digest": None,
        "core_sdlc_trace_ref": "trace:" + slug(case_id),
        "policy_decision_digest": "sha256:" + "4" * 64,
        "authority_refs": request["authority_refs"],
        "evidence_refs": [
            evidence["evidence_ref"]
            for evidence in request["evidence"]
        ],
        "invalidated_artifact_refs": [],
        "occurred_at": FIXED_TIME,
    }
    fact["digest"] = digest_value(fact)
    return fact


def fixture_schema_sample(schema: dict[str, Any]) -> Any:
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    if "enum" in schema:
        return copy.deepcopy(schema["enum"][0])
    if "oneOf" in schema:
        non_null = [
            choice
            for choice in schema["oneOf"]
            if choice.get("type") != "null"
        ]
        return fixture_schema_sample(
            non_null[0] if non_null else schema["oneOf"][0]
        )
    schema_type = schema.get("type")
    if schema_type == "object":
        return {
            key: fixture_schema_sample(schema["properties"][key])
            for key in schema.get("required", [])
        }
    if schema_type == "array":
        count = max(schema.get("minItems", 0), 1)
        values = [
            fixture_schema_sample(schema["items"])
            for _ in range(count)
        ]
        return sorted(values, key=canonical_bytes)
    if schema_type == "integer":
        return max(schema.get("minimum", 0), 1)
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        pattern = schema.get("pattern", "")
        if "sha256:" in pattern:
            return "sha256:" + "1" * 64
        if "\\d{4}-\\d{2}" in pattern:
            return FIXED_TIME
        if "-7[0-9a-f]" in pattern:
            return deterministic_uuid7("fixture-schema-sample")
        if schema.get("x-ranex-id-type"):
            return "id_sample"
        return "sample"
    raise ValueError(
        "Cannot construct fixture sample for schema: "
        + json.dumps(schema, sort_keys=True)
    )


def closed_schema_fixture_value(
    schema: dict[str, Any],
    seed: str,
) -> Any:
    if "const" in schema:
        return copy.deepcopy(schema["const"])
    if "enum" in schema:
        return copy.deepcopy(schema["enum"][0])
    if "oneOf" in schema:
        if any(
            choice.get("type") == "null"
            for choice in schema["oneOf"]
        ):
            return None
        return closed_schema_fixture_value(schema["oneOf"][0], seed)
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        if "null" in schema_type:
            return None
        schema_type = schema_type[0]
    if schema_type == "object":
        return {
            field_name: closed_schema_fixture_value(
                schema["properties"][field_name],
                seed + "-" + field_name,
            )
            for field_name in schema.get("required", [])
        }
    if schema_type == "array":
        count = schema.get("minItems", 0)
        values = [
            closed_schema_fixture_value(
                schema["items"],
                seed + f"-{index}",
            )
            for index in range(count)
        ]
        if schema.get("x-ranex-bytewise-sorted"):
            values.sort(key=canonical_bytes)
        return values
    if schema_type == "integer":
        return schema.get("minimum", 0)
    if schema_type == "boolean":
        return True
    if schema_type == "string":
        pattern = schema.get("pattern", "")
        seed_digest = hashlib.sha256(
            seed.encode("utf-8")
        ).hexdigest()
        if "sha256:" in pattern:
            return "sha256:" + seed_digest
        if "{64}" in pattern:
            return seed_digest
        if "{40}" in pattern:
            return seed_digest[:40]
        if "[0-9]+" in pattern and r"\." in pattern:
            return "1.0.0"
        if "/v[1-9]" in pattern:
            return "fixture/v1"
        if "urn:" in pattern:
            return "urn:ranex:fixture:" + seed_digest[:16]
        if (
            schema.get("format") == "date-time"
            or r"\d{4}" in pattern
        ):
            return FIXED_TIME
        if schema.get(
            "x-ranex-normalized-repository-relative-posix-path"
        ):
            return "tests/unit/" + seed_digest[:16] + ".py"
        return "Fixture-" + seed_digest[:16]
    raise ValueError(
        "Cannot construct closed-schema fixture value: "
        + json.dumps(schema, sort_keys=True)
    )


def set_payload_state_fields(
    payload: dict[str, Any],
    payload_schema: dict[str, Any],
    *,
    source: str | None = None,
    target: str | None = None,
    initial: str | None = None,
) -> None:
    candidates = {
        "initial_status": initial,
        "from_status": source,
        "prior_status": source,
        "to_status": target,
        "outcome": target,
        "resolution": target,
        "proven_outcome": target,
    }
    for field_name, value in candidates.items():
        if value is None or field_name not in payload:
            continue
        field_schema = payload_schema["properties"][field_name]
        allowed = field_schema.get("enum")
        if allowed is None and "oneOf" in field_schema:
            allowed = next(
                (
                    choice["enum"]
                    for choice in field_schema["oneOf"]
                    if "enum" in choice
                ),
                None,
            )
        if allowed is None or value in allowed:
            payload[field_name] = value


def canonical_domain_event_fixture(
    event_row: dict[str, Any],
    schemas: dict[str, dict[str, Any]],
    case_id: str,
    *,
    state_initial_bindings: list[dict[str, Any]] | None = None,
    state_edge_bindings: list[dict[str, Any]] | None = None,
    source: str | None = None,
    target: str | None = None,
    initial: str | None = None,
) -> dict[str, Any]:
    payload_schema = schemas[
        event_row["payload_schema_path"].removeprefix("schemas/")
    ]
    payload = fixture_schema_sample(payload_schema)
    if state_initial_bindings is not None:
        payload["state_initial_bindings"] = sorted(
            state_initial_bindings,
            key=canonical_bytes,
        )
    if state_edge_bindings is not None:
        payload["state_edge_bindings"] = sorted(
            state_edge_bindings,
            key=canonical_bytes,
        )
    set_payload_state_fields(
        payload,
        payload_schema,
        source=source,
        target=target,
        initial=initial,
    )
    event = {
        "schema_version": "domain-event-envelope/v1",
        "event_id": event_row["event_id"],
        "event_name": event_row["event_name"],
        "event_version": 1,
        "event_instance_id": deterministic_uuid7(case_id),
        "owner_context": event_row["owner_context"],
        "producer_service_id": event_row["producer_service_id"],
        "producer_release_digest": "sha256:" + "2" * 64,
        "aggregate_type": event_row["aggregate_type"],
        "aggregate_id": "aggregate:" + slug(case_id),
        "source_aggregate_version": 0,
        "aggregate_version": 1,
        "aggregate_event_sequence": 1,
        "subject_ref": "subject:" + slug(case_id),
        "subject_digest": "sha256:" + "3" * 64,
        "correlation_id": "correlation:" + slug(case_id),
        "causation_id": "causation:" + slug(case_id),
        "idempotency_key": "idempotency:" + slug(case_id),
        "occurred_at": FIXED_TIME,
        "recorded_at": FIXED_TIME,
        "payload_schema_ref": event_row["payload_schema_ref"],
        "payload_schema_digest": event_row["payload_schema_digest"],
        "payload": payload,
        "data_classification": "INTERNAL",
        "retention_policy_id": "RET-AUDIT-CONTROL-001",
    }
    event["digest"] = digest_value(event)
    return event


def mutate_and_redigest(
    value: dict[str, Any],
    mutation: Any,
) -> dict[str, Any]:
    result = copy.deepcopy(value)
    mutation(result)
    if "digest" in result:
        result["digest"] = digest_value(result)
    return result


def build_state_event_fixture_suite(
    registries: dict[str, Any],
) -> dict[str, Any]:
    """Generate the source-declared exhaustive state/event test matrix."""

    text = read(ARCH_DOC)
    catalog = parse_state_axis_catalog(text)
    denominator = parse_state_event_fixture_denominator(text)
    state_registry = registries["states.json"]
    event_registry = registries["events.json"]
    events = parse_event_catalog(text)
    binding_catalog = parse_event_state_binding_catalog(
        text,
        catalog,
        events,
    )
    schemas = event_contract_schemas(state_registry)
    axis_by_id = {axis["axis_id"]: axis for axis in catalog["axes"]}
    registry_axis_by_id = {
        axis["axis_id"]: axis for axis in state_registry["entries"]
    }
    event_by_name = {
        row["event_name"]: row
        for row in event_registry["entries"]
    }
    lifecycle_axes = [
        axis
        for axis in catalog["axes"]
        if axis["axis_kind"] == "LIFECYCLE"
    ]
    classifier_axes = [
        axis
        for axis in catalog["axes"]
        if axis["axis_kind"] == "CLASSIFIER"
    ]
    allowed_edges: list[tuple[dict[str, Any], str, str, str]] = []
    prohibited_pairs: list[tuple[dict[str, Any], str, str]] = []
    recorded_prior_edges: list[
        tuple[dict[str, Any], str, str, str]
    ] = []
    for axis in lifecycle_axes:
        allowed_pairs: set[tuple[str, str]] = set()
        for edge in axis["transitions"]:
            source, target, guard_id = split_state_edge(edge)
            allowed_pairs.add((source, target))
            edge_tuple = (axis, source, target, guard_id)
            allowed_edges.append(edge_tuple)
            if source == "BLOCKED" or target == "BLOCKED":
                recorded_prior_edges.append(edge_tuple)
        for source in axis["values"]:
            for target in axis["values"]:
                if source != target and (source, target) not in allowed_pairs:
                    prohibited_pairs.append((axis, source, target))

    transition_requests: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in (
            "allowed_edge_positive",
            "allowed_edge_unsatisfied_guard_negative",
            "prohibited_pair_negative",
            "wrong_owner_negative",
            "wrong_authority_negative",
            "stale_aggregate_version_negative",
            "missing_evidence_negative",
            "stale_evidence_negative",
            "wrong_recorded_prior_negative",
            "unknown_axis_negative",
            "unknown_lifecycle_from_value_negative",
            "unknown_lifecycle_to_value_negative",
            "classifier_mutation_negative",
        )
    }

    def request_case(
        category: str,
        case_id: str,
        request: dict[str, Any],
        expected: str,
    ) -> None:
        transition_requests[category].append(
            {
                "case_id": case_id,
                "falsified_dimension": (
                    None if expected == "ACCEPT" else category
                ),
                "request": request,
                (
                    "expected_result"
                    if expected == "ACCEPT"
                    else "expected_error"
                ): expected,
            }
        )

    for axis, source, target, guard_id in allowed_edges:
        suffix = f"{axis['axis_id']}-{source}-{target}"
        base = canonical_transition_request(
            axis,
            source,
            target,
            guard_id,
            "REQUEST-" + suffix,
        )
        request_case(
            "allowed_edge_positive",
            "REQUEST-ALLOW-" + suffix,
            base,
            "ACCEPT",
        )
        request_case(
            "allowed_edge_unsatisfied_guard_negative",
            "REQUEST-DENY-GUARD-" + suffix,
            mutate_and_redigest(
                base,
                lambda request: request.__setitem__(
                    "guard_satisfied",
                    False,
                ),
            ),
            "UNSATISFIED_GUARD",
        )
        request_case(
            "wrong_owner_negative",
            "REQUEST-DENY-OWNER-" + suffix,
            mutate_and_redigest(
                base,
                lambda request: request.__setitem__(
                    "owner_context",
                    "wrong_owner",
                ),
            ),
            "WRONG_OWNER",
        )
        request_case(
            "wrong_authority_negative",
            "REQUEST-DENY-AUTHORITY-" + suffix,
            mutate_and_redigest(
                base,
                lambda request: request.__setitem__(
                    "authenticated_transition_authority",
                    "forged_transition_authority",
                ),
            ),
            "WRONG_AUTHORITY",
        )
        request_case(
            "stale_aggregate_version_negative",
            "REQUEST-DENY-STALE-VERSION-" + suffix,
            mutate_and_redigest(
                base,
                lambda request: request.__setitem__(
                    "persisted_aggregate_version",
                    request["expected_aggregate_version"] + 1,
                ),
            ),
            "STALE_AGGREGATE_VERSION",
        )
        request_case(
            "missing_evidence_negative",
            "REQUEST-DENY-MISSING-EVIDENCE-" + suffix,
            mutate_and_redigest(
                base,
                lambda request: request.__setitem__("evidence", []),
            ),
            "MISSING_EVIDENCE",
        )
        request_case(
            "stale_evidence_negative",
            "REQUEST-DENY-STALE-EVIDENCE-" + suffix,
            mutate_and_redigest(
                base,
                lambda request: request["evidence"][0].__setitem__(
                    "freshness_status",
                    "STALE",
                ),
            ),
            "STALE_EVIDENCE",
        )
    for axis, source, target in prohibited_pairs:
        case_id = f"REQUEST-DENY-PAIR-{axis['axis_id']}-{source}-{target}"
        request_case(
            "prohibited_pair_negative",
            case_id,
            canonical_transition_request(
                axis,
                source,
                target,
                "PROHIBITED_EDGE_GUARD",
                case_id,
            ),
            "ILLEGAL_EDGE",
        )
    for axis, source, target, guard_id in recorded_prior_edges:
        case_id = (
            f"REQUEST-DENY-PRIOR-{axis['axis_id']}-{source}-{target}"
        )
        request = canonical_transition_request(
            axis,
            source,
            target,
            guard_id,
            case_id,
        )
        request["recorded_prior_state"] = next(
            value
            for value in axis["values"]
            if value != request["recorded_prior_state"]
        )
        request_case(
            "wrong_recorded_prior_negative",
            case_id,
            request,
            "WRONG_RECORDED_PRIOR_STATE",
        )
    base_axis, base_source, base_target, base_guard = allowed_edges[0]
    unknown_axis_request = canonical_transition_request(
        base_axis,
        base_source,
        base_target,
        base_guard,
        "REQUEST-DENY-UNKNOWN-AXIS",
    )
    unknown_axis_request["axis_id"] = "UnknownStateAxis"
    request_case(
        "unknown_axis_negative",
        "REQUEST-DENY-UNKNOWN-AXIS",
        unknown_axis_request,
        "UNKNOWN_AXIS",
    )
    for axis in lifecycle_axes:
        source, target, guard_id = split_state_edge(
            axis["transitions"][0]
        )
        unknown_from = canonical_transition_request(
            axis,
            source,
            target,
            guard_id,
            "REQUEST-DENY-UNKNOWN-FROM-" + axis["axis_id"],
        )
        unknown_from["from_state"] = "UNKNOWN_VALUE"
        request_case(
            "unknown_lifecycle_from_value_negative",
            "REQUEST-DENY-UNKNOWN-FROM-" + axis["axis_id"],
            unknown_from,
            "UNKNOWN_FROM_VALUE",
        )
        unknown_to = canonical_transition_request(
            axis,
            source,
            target,
            guard_id,
            "REQUEST-DENY-UNKNOWN-TO-" + axis["axis_id"],
        )
        unknown_to["to_state"] = "UNKNOWN_VALUE"
        request_case(
            "unknown_lifecycle_to_value_negative",
            "REQUEST-DENY-UNKNOWN-TO-" + axis["axis_id"],
            unknown_to,
            "UNKNOWN_TO_VALUE",
        )
    for axis in classifier_axes:
        source, target = axis["values"][:2]
        case_id = "REQUEST-DENY-CLASSIFIER-" + axis["axis_id"]
        request_case(
            "classifier_mutation_negative",
            case_id,
            canonical_transition_request(
                axis,
                source,
                target,
                "CLASSIFIER_MUTATION_FORBIDDEN",
                case_id,
            ),
            "CLASSIFIER_MUTATION_FORBIDDEN",
        )

    transition_facts: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in (
            "schema_valid_positive",
            "wrong_axis_negative",
            "wrong_guard_negative",
            "wrong_catalog_digest_negative",
            "nonincrementing_aggregate_version_negative",
            "wrong_fact_digest_negative",
            "prohibited_pair_fact_negative",
            "wrong_recorded_prior_fact_negative",
            "required_field_omission_negative",
            "wrong_field_type_negative",
            "additional_property_negative",
        )
    }

    def fact_case(
        category: str,
        case_id: str,
        fact: dict[str, Any],
        expected: str,
    ) -> None:
        transition_facts[category].append(
            {
                "case_id": case_id,
                "falsified_dimension": (
                    None if expected == "ACCEPT" else category
                ),
                "fact": fact,
                (
                    "expected_result"
                    if expected == "ACCEPT"
                    else "expected_error"
                ): expected,
            }
        )

    valid_facts: list[dict[str, Any]] = []
    for index, (axis, source, target, guard_id) in enumerate(
        allowed_edges
    ):
        suffix = f"{axis['axis_id']}-{source}-{target}"
        fact = canonical_transition_fact(
            state_registry,
            axis,
            source,
            target,
            guard_id,
            "FACT-" + suffix,
        )
        valid_facts.append(fact)
        fact_case(
            "schema_valid_positive",
            "FACT-ALLOW-" + suffix,
            fact,
            "ACCEPT",
        )
        other_axis = next(
            candidate
            for candidate in lifecycle_axes
            if candidate["axis_id"] != axis["axis_id"]
            and candidate["owner_context"] != axis["owner_context"]
        )
        wrong_axis = copy.deepcopy(fact)
        wrong_axis["axis_id"] = other_axis["axis_id"]
        wrong_axis["edge_id"] = canonical_state_edge_id(
            other_axis["axis_id"],
            fact["axis_version"],
            source,
            target,
            guard_id,
        )
        wrong_axis["digest"] = digest_value(wrong_axis)
        fact_case(
            "wrong_axis_negative",
            "FACT-DENY-AXIS-" + suffix,
            wrong_axis,
            "TRANSITION_FACT_AXIS_MISMATCH",
        )
        wrong_guard = copy.deepcopy(fact)
        wrong_guard["guard_id"] = "FORGED_GUARD"
        wrong_guard["edge_id"] = canonical_state_edge_id(
            axis["axis_id"],
            axis["axis_version"],
            source,
            target,
            wrong_guard["guard_id"],
        )
        wrong_guard["digest"] = digest_value(wrong_guard)
        fact_case(
            "wrong_guard_negative",
            "FACT-DENY-GUARD-" + suffix,
            wrong_guard,
            "TRANSITION_FACT_GUARD_MISMATCH",
        )
        wrong_catalog = copy.deepcopy(fact)
        wrong_catalog["state_catalog_digest"] = "sha256:" + "0" * 64
        wrong_catalog["digest"] = digest_value(wrong_catalog)
        fact_case(
            "wrong_catalog_digest_negative",
            "FACT-DENY-CATALOG-" + suffix,
            wrong_catalog,
            "TRANSITION_FACT_CATALOG_DIGEST",
        )
        nonincrementing = copy.deepcopy(fact)
        nonincrementing["aggregate_version_after"] = nonincrementing[
            "aggregate_version_before"
        ]
        nonincrementing["digest"] = digest_value(nonincrementing)
        fact_case(
            "nonincrementing_aggregate_version_negative",
            "FACT-DENY-VERSION-" + suffix,
            nonincrementing,
            "TRANSITION_FACT_VERSION_INCREMENT",
        )
        wrong_digest = copy.deepcopy(fact)
        wrong_digest["digest"] = "sha256:" + "0" * 64
        fact_case(
            "wrong_fact_digest_negative",
            "FACT-DENY-DIGEST-" + suffix,
            wrong_digest,
            "TRANSITION_FACT_DIGEST",
        )
    for axis, source, target in prohibited_pairs:
        case_id = f"FACT-DENY-PAIR-{axis['axis_id']}-{source}-{target}"
        fact_case(
            "prohibited_pair_fact_negative",
            case_id,
            canonical_transition_fact(
                state_registry,
                axis,
                source,
                target,
                "PROHIBITED_EDGE_GUARD",
                case_id,
            ),
            "TRANSITION_FACT_ILLEGAL_EDGE",
        )
    for axis, source, target, guard_id in recorded_prior_edges:
        case_id = f"FACT-DENY-PRIOR-{axis['axis_id']}-{source}-{target}"
        fact = canonical_transition_fact(
            state_registry,
            axis,
            source,
            target,
            guard_id,
            case_id,
        )
        fact["recorded_prior_state"] = next(
            value
            for value in axis["values"]
            if value != fact["recorded_prior_state"]
        )
        fact["digest"] = digest_value(fact)
        fact_case(
            "wrong_recorded_prior_fact_negative",
            case_id,
            fact,
            "TRANSITION_FACT_RECORDED_PRIOR",
        )
    transition_contract = parse_transition_fact_contract(text)
    canonical_fact = valid_facts[0]
    for field in [
        row["name"] for row in transition_contract["required_fields"]
    ]:
        omitted = copy.deepcopy(canonical_fact)
        del omitted[field]
        if "digest" in omitted:
            omitted["digest"] = digest_value(omitted)
        fact_case(
            "required_field_omission_negative",
            "FACT-DENY-OMIT-" + slug(field),
            omitted,
            "TRANSITION_FACT_SCHEMA_REQUIRED",
        )
        wrong_type = copy.deepcopy(canonical_fact)
        value = wrong_type[field]
        if isinstance(value, list):
            wrong_type[field] = "not-an-array"
        elif isinstance(value, int):
            wrong_type[field] = "not-an-integer"
        elif value is None:
            wrong_type[field] = {}
        else:
            wrong_type[field] = []
        if field != "digest":
            wrong_type["digest"] = digest_value(wrong_type)
        fact_case(
            "wrong_field_type_negative",
            "FACT-DENY-TYPE-" + slug(field),
            wrong_type,
            "TRANSITION_FACT_SCHEMA_TYPE",
        )
    extra = copy.deepcopy(canonical_fact)
    extra["undeclared_field"] = True
    extra["digest"] = digest_value(extra)
    fact_case(
        "additional_property_negative",
        "FACT-DENY-ADDITIONAL-PROPERTY",
        extra,
        "TRANSITION_FACT_SCHEMA_ADDITIONAL_PROPERTY",
    )

    outward: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in (
            "valid_edge_binding_combinations",
            "wrong_axis_negative_per_valid_combination",
            "wrong_guard_negative_per_valid_combination",
            "wrong_transition_fact_ref_negative_per_valid_combination",
            "wrong_catalog_digest_negative_per_valid_combination",
            "aggregate_version_mismatch_negative_per_valid_combination",
            "wrong_binding_cardinality_negative_per_valid_combination",
            "event_specific_unlisted_pair_negative",
        )
    }

    def event_case(
        target_suite: dict[str, list[dict[str, Any]]],
        category: str,
        case_id: str,
        event: dict[str, Any],
        facts: list[dict[str, Any]],
        expected: str,
    ) -> None:
        target_suite[category].append(
            {
                "case_id": case_id,
                "falsified_dimension": (
                    None if expected == "ACCEPT" else category
                ),
                "event": event,
                "transition_facts": facts,
                (
                    "expected_result"
                    if expected == "ACCEPT"
                    else "expected_error"
                ): expected,
            }
        )

    for binding in binding_catalog["event_bindings"]:
        if binding["binding_kind"] != "EDGE_EVENT":
            continue
        event_row = event_by_name[binding["event_name"]]
        choices = [
            row["allowed_edges"] for row in binding["edge_bindings"]
        ]
        for combination_index, selected_edges in enumerate(
            itertools.product(*choices),
            start=1,
        ):
            case_id = (
                f"EVENT-EDGE-{binding['event_name']}-"
                f"{combination_index:03d}"
            )
            facts: list[dict[str, Any]] = []
            edge_refs: list[dict[str, Any]] = []
            first_source: str | None = None
            first_target: str | None = None
            for binding_row, edge in zip(
                binding["edge_bindings"],
                selected_edges,
            ):
                axis = axis_by_id[binding_row["axis_id"]]
                source, target, guard_id = split_state_edge(edge)
                first_source = (
                    source if first_source is None else first_source
                )
                first_target = (
                    target if first_target is None else first_target
                )
                fact = canonical_transition_fact(
                    state_registry,
                    axis,
                    source,
                    target,
                    guard_id,
                    case_id + "-" + axis["axis_id"],
                    aggregate_type=event_row["aggregate_type"],
                    aggregate_id="aggregate:" + slug(case_id),
                    aggregate_version_before=0,
                )
                fact["subject_ref"] = "subject:" + slug(case_id)
                fact["subject_digest"] = "sha256:" + "3" * 64
                fact["digest"] = digest_value(fact)
                facts.append(fact)
                edge_refs.append(
                    {
                        "axis_id": axis["axis_id"],
                        "axis_version": axis["axis_version"],
                        "state_catalog_digest": state_registry["digest"],
                        "edge_id": fact["edge_id"],
                        "transition_fact_ref": {
                            "id": fact["transition_id"],
                            "digest": fact["digest"],
                        },
                    }
                )
            event = canonical_domain_event_fixture(
                event_row,
                schemas,
                case_id,
                state_edge_bindings=edge_refs,
                source=first_source,
                target=first_target,
            )
            event_case(
                outward,
                "valid_edge_binding_combinations",
                case_id,
                event,
                facts,
                "ACCEPT",
            )
            first_ref = event["payload"]["state_edge_bindings"][0]
            wrong_axis_event = copy.deepcopy(event)
            other_axis = next(
                axis
                for axis in lifecycle_axes
                if axis["axis_id"] != first_ref["axis_id"]
            )
            wrong_axis_event["payload"]["state_edge_bindings"][0][
                "axis_id"
            ] = other_axis["axis_id"]
            wrong_axis_event["digest"] = digest_value(wrong_axis_event)
            event_case(
                outward,
                "wrong_axis_negative_per_valid_combination",
                case_id + "-DENY-AXIS",
                wrong_axis_event,
                facts,
                "EVENT_STATE_AXIS_MISMATCH",
            )
            wrong_guard_event = copy.deepcopy(event)
            old_edge_id = wrong_guard_event["payload"][
                "state_edge_bindings"
            ][0]["edge_id"]
            wrong_guard_event["payload"]["state_edge_bindings"][0][
                "edge_id"
            ] = old_edge_id.rsplit("@", 1)[0] + "@FORGED_GUARD"
            wrong_guard_event["digest"] = digest_value(
                wrong_guard_event
            )
            event_case(
                outward,
                "wrong_guard_negative_per_valid_combination",
                case_id + "-DENY-GUARD",
                wrong_guard_event,
                facts,
                "EVENT_STATE_GUARD_MISMATCH",
            )
            wrong_ref_event = copy.deepcopy(event)
            wrong_ref_event["payload"]["state_edge_bindings"][0][
                "transition_fact_ref"
            ]["id"] = "transition_missing"
            wrong_ref_event["digest"] = digest_value(wrong_ref_event)
            event_case(
                outward,
                "wrong_transition_fact_ref_negative_per_valid_combination",
                case_id + "-DENY-FACT-REF",
                wrong_ref_event,
                facts,
                "EVENT_TRANSITION_FACT_REF",
            )
            wrong_catalog_event = copy.deepcopy(event)
            wrong_catalog_event["payload"]["state_edge_bindings"][0][
                "state_catalog_digest"
            ] = "sha256:" + "0" * 64
            wrong_catalog_event["digest"] = digest_value(
                wrong_catalog_event
            )
            event_case(
                outward,
                "wrong_catalog_digest_negative_per_valid_combination",
                case_id + "-DENY-CATALOG",
                wrong_catalog_event,
                facts,
                "EVENT_STATE_CATALOG_DIGEST",
            )
            mismatch_event = copy.deepcopy(event)
            mismatch_event["aggregate_version"] = 2
            mismatch_event["digest"] = digest_value(mismatch_event)
            event_case(
                outward,
                "aggregate_version_mismatch_negative_per_valid_combination",
                case_id + "-DENY-AGGREGATE-VERSION",
                mismatch_event,
                facts,
                "EVENT_TRANSITION_AGGREGATE_VERSION",
            )
            cardinality_event = copy.deepcopy(event)
            cardinality_event["payload"]["state_edge_bindings"].pop(0)
            cardinality_event["digest"] = digest_value(
                cardinality_event
            )
            event_case(
                outward,
                "wrong_binding_cardinality_negative_per_valid_combination",
                case_id + "-DENY-CARDINALITY",
                cardinality_event,
                facts,
                "EVENT_STATE_BINDING_CARDINALITY",
            )
        for binding_index, binding_row in enumerate(
            binding["edge_bindings"],
            start=1,
        ):
            axis = axis_by_id[binding_row["axis_id"]]
            allowed_for_event = set(binding_row["allowed_edges"])
            catalog_guard_by_pair = {
                (source, target): guard
                for source, target, guard in (
                    split_state_edge(edge)
                    for edge in axis["transitions"]
                )
            }
            for source in axis["values"]:
                for target in axis["values"]:
                    if source == target:
                        continue
                    pair_guard = catalog_guard_by_pair.get(
                        (source, target),
                        "PROHIBITED_EDGE_GUARD",
                    )
                    edge = f"{source}>{target}@{pair_guard}"
                    if edge in allowed_for_event:
                        continue
                    case_id = (
                        f"EVENT-UNLISTED-{binding['event_name']}-"
                        f"{binding_index}-{source}-{target}"
                    )
                    pseudo_fact = canonical_transition_fact(
                        state_registry,
                        axis,
                        source,
                        target,
                        pair_guard,
                        case_id,
                        aggregate_type=event_row["aggregate_type"],
                        aggregate_id="aggregate:" + slug(case_id),
                        aggregate_version_before=0,
                    )
                    pseudo_fact["subject_ref"] = (
                        "subject:" + slug(case_id)
                    )
                    pseudo_fact["subject_digest"] = "sha256:" + "3" * 64
                    pseudo_fact["digest"] = digest_value(pseudo_fact)
                    edge_ref = {
                        "axis_id": axis["axis_id"],
                        "axis_version": axis["axis_version"],
                        "state_catalog_digest": state_registry["digest"],
                        "edge_id": pseudo_fact["edge_id"],
                        "transition_fact_ref": {
                            "id": pseudo_fact["transition_id"],
                            "digest": pseudo_fact["digest"],
                        },
                    }
                    complete_refs = [edge_ref]
                    complete_facts = [pseudo_fact]
                    for other_index, other_row in enumerate(
                        binding["edge_bindings"],
                        start=1,
                    ):
                        if other_index == binding_index:
                            continue
                        other_axis = axis_by_id[other_row["axis_id"]]
                        (
                            other_source,
                            other_target,
                            other_guard,
                        ) = split_state_edge(other_row["allowed_edges"][0])
                        other_fact = canonical_transition_fact(
                            state_registry,
                            other_axis,
                            other_source,
                            other_target,
                            other_guard,
                            case_id + "-" + other_axis["axis_id"],
                            aggregate_type=event_row["aggregate_type"],
                            aggregate_id=(
                                "aggregate:" + slug(case_id)
                            ),
                            aggregate_version_before=0,
                        )
                        other_fact["subject_ref"] = (
                            "subject:" + slug(case_id)
                        )
                        other_fact["subject_digest"] = (
                            "sha256:" + "3" * 64
                        )
                        other_fact["digest"] = digest_value(other_fact)
                        complete_facts.append(other_fact)
                        complete_refs.append(
                            {
                                "axis_id": other_axis["axis_id"],
                                "axis_version": other_axis[
                                    "axis_version"
                                ],
                                "state_catalog_digest": state_registry[
                                    "digest"
                                ],
                                "edge_id": other_fact["edge_id"],
                                "transition_fact_ref": {
                                    "id": other_fact["transition_id"],
                                    "digest": other_fact["digest"],
                                },
                            }
                        )
                    event = canonical_domain_event_fixture(
                        event_row,
                        schemas,
                        case_id,
                        state_edge_bindings=complete_refs,
                    )
                    event_case(
                        outward,
                        "event_specific_unlisted_pair_negative",
                        case_id,
                        event,
                        complete_facts,
                        "EVENT_STATE_EDGE_UNLISTED",
                    )

    initial_events: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in (
            "valid_event_instances",
            "noninitial_value_negative",
            "wrong_axis_catalog_or_version_negative",
            "missing_required_binding_negative",
        )
    }
    reference_events: dict[str, list[dict[str, Any]]] = {
        name: []
        for name in (
            "valid_event_instances",
            "injected_initial_binding_negative",
            "injected_edge_binding_negative",
        )
    }
    for binding in binding_catalog["event_bindings"]:
        event_row = event_by_name[binding["event_name"]]
        if binding["binding_kind"] == "INITIAL_STATE_FACT":
            case_id = "EVENT-INITIAL-" + binding["event_name"]
            initial_bindings: list[dict[str, Any]] = []
            for row in binding["initial_bindings"]:
                initial_bindings.append(
                    {
                        "axis_id": row["axis_id"],
                        "axis_version": row["axis_version"],
                        "state_catalog_digest": state_registry["digest"],
                        "initial_value": row["initial_value"],
                        "aggregate_type": event_row["aggregate_type"],
                        "aggregate_id": (
                            "aggregate:" + slug(case_id)
                        ),
                        "aggregate_version": 1,
                    }
                )
            event = canonical_domain_event_fixture(
                event_row,
                schemas,
                case_id,
                state_initial_bindings=initial_bindings,
                initial=binding["initial_bindings"][0][
                    "initial_value"
                ],
            )
            event_case(
                initial_events,
                "valid_event_instances",
                case_id,
                event,
                [],
                "ACCEPT",
            )
            for binding_index, row in enumerate(
                binding["initial_bindings"]
            ):
                axis = axis_by_id[row["axis_id"]]
                for value in axis["values"]:
                    if value in axis["initial_values"]:
                        continue
                    mutated = copy.deepcopy(event)
                    mutated["payload"]["state_initial_bindings"][
                        binding_index
                    ]["initial_value"] = value
                    mutated["digest"] = digest_value(mutated)
                    event_case(
                        initial_events,
                        "noninitial_value_negative",
                        (
                            case_id
                            + "-DENY-NONINITIAL-"
                            + axis["axis_id"]
                            + "-"
                            + value
                        ),
                        mutated,
                        [],
                        "EVENT_STATE_NONINITIAL_VALUE",
                    )
                other_axis = next(
                    other
                    for other in lifecycle_axes
                    if other["axis_id"] != axis["axis_id"]
                )
                mutations = [
                    (
                        "AXIS",
                        "EVENT_STATE_INITIAL_AXIS",
                        lambda item, other_axis=other_axis: item.__setitem__(
                            "axis_id",
                            other_axis["axis_id"],
                        ),
                    ),
                    (
                        "VERSION",
                        "EVENT_STATE_INITIAL_VERSION",
                        lambda item: item.__setitem__(
                            "axis_version",
                            "0.0.0",
                        ),
                    ),
                    (
                        "CATALOG",
                        "EVENT_STATE_CATALOG_DIGEST",
                        lambda item: item.__setitem__(
                            "state_catalog_digest",
                            "sha256:" + "0" * 64,
                        ),
                    ),
                ]
                for mutation_name, error, mutate in mutations:
                    mutated = copy.deepcopy(event)
                    mutate(
                        mutated["payload"]["state_initial_bindings"][
                            binding_index
                        ]
                    )
                    mutated["digest"] = digest_value(mutated)
                    event_case(
                        initial_events,
                        "wrong_axis_catalog_or_version_negative",
                        (
                            case_id
                            + "-DENY-"
                            + mutation_name
                            + "-"
                            + str(binding_index + 1)
                        ),
                        mutated,
                        [],
                        error,
                    )
                missing = copy.deepcopy(event)
                missing["payload"]["state_initial_bindings"].pop(
                    binding_index
                )
                missing["digest"] = digest_value(missing)
                event_case(
                    initial_events,
                    "missing_required_binding_negative",
                    (
                        case_id
                        + "-DENY-MISSING-"
                        + str(binding_index + 1)
                    ),
                    missing,
                    [],
                    "EVENT_STATE_BINDING_CARDINALITY",
                )
        elif binding["binding_kind"] == "REFERENCE_ONLY":
            case_id = "EVENT-REFERENCE-" + binding["event_name"]
            event = canonical_domain_event_fixture(
                event_row,
                schemas,
                case_id,
            )
            event_case(
                reference_events,
                "valid_event_instances",
                case_id,
                event,
                [],
                "ACCEPT",
            )
            injected_initial = copy.deepcopy(event)
            injected_initial["payload"]["state_initial_bindings"] = [
                {
                    "axis_id": lifecycle_axes[0]["axis_id"],
                    "axis_version": lifecycle_axes[0]["axis_version"],
                    "state_catalog_digest": state_registry["digest"],
                    "initial_value": lifecycle_axes[0][
                        "initial_values"
                    ][0],
                    "aggregate_type": event_row["aggregate_type"],
                    "aggregate_id": "aggregate:" + slug(case_id),
                    "aggregate_version": 1,
                }
            ]
            injected_initial["digest"] = digest_value(injected_initial)
            event_case(
                reference_events,
                "injected_initial_binding_negative",
                case_id + "-DENY-INJECT-INITIAL",
                injected_initial,
                [],
                "EVENT_STATE_BINDING_FORBIDDEN",
            )
            sample_fact = valid_facts[0]
            injected_edge = copy.deepcopy(event)
            injected_edge["payload"]["state_edge_bindings"] = [
                {
                    "axis_id": sample_fact["axis_id"],
                    "axis_version": sample_fact["axis_version"],
                    "state_catalog_digest": state_registry["digest"],
                    "edge_id": sample_fact["edge_id"],
                    "transition_fact_ref": {
                        "id": sample_fact["transition_id"],
                        "digest": sample_fact["digest"],
                    },
                }
            ]
            injected_edge["digest"] = digest_value(injected_edge)
            event_case(
                reference_events,
                "injected_edge_binding_negative",
                case_id + "-DENY-INJECT-EDGE",
                injected_edge,
                [sample_fact],
                "EVENT_STATE_BINDING_FORBIDDEN",
            )

    computed = {
        "schema_version": denominator["schema_version"],
        "state_catalog_shape": {
            "lifecycle_axes": len(lifecycle_axes),
            "classifier_axes": len(classifier_axes),
            "ordered_nonself_lifecycle_pairs": sum(
                len(axis["values"]) * (len(axis["values"]) - 1)
                for axis in lifecycle_axes
            ),
            "allowed_edges": len(allowed_edges),
            "prohibited_pairs": len(prohibited_pairs),
        },
    }
    for section_name, suites in (
        ("transition_request_suite", transition_requests),
        ("transition_fact_suite", transition_facts),
        ("outward_edge_event_suite", outward),
        ("initial_state_event_suite", initial_events),
        ("reference_only_event_suite", reference_events),
    ):
        computed[section_name] = {
            category: len(cases)
            for category, cases in suites.items()
        }
        computed[section_name]["exact_case_count"] = sum(
            len(cases) for cases in suites.values()
        )
    computed["total_exact_cases"] = sum(
        computed[section_name]["exact_case_count"]
        for section_name in (
            "transition_request_suite",
            "transition_fact_suite",
            "outward_edge_event_suite",
            "initial_state_event_suite",
            "reference_only_event_suite",
        )
    )
    if computed != denominator:
        raise ValueError(
            "Source-derived state/event fixture denominator drift: "
            + json.dumps(
                {"declared": denominator, "computed": computed},
                sort_keys=True,
            )
        )
    readiness_axis = axis_by_id["READINESS-STATE-1.0"]
    readiness_acceptance_fact = canonical_transition_fact(
        state_registry,
        readiness_axis,
        "NOT_ASSESSED",
        "IMPLEMENTATION_START_EVALUATING",
        "READINESS_ASSESSMENT_OPENED",
        "FIXTURE-READINESS-ASSESSMENT-OPENED",
        aggregate_type="RepositoryReadiness",
        aggregate_id="ranex",
        aggregate_version_before=0,
    )
    readiness_acceptance_fact["reason_code"] = (
        "READINESS_ASSESSMENT_OPENED"
    )
    readiness_acceptance_fact["digest"] = digest_value(
        readiness_acceptance_fact
    )
    declared_axis_negative_cases = [
        {
            "case_id": (
                "DECLARED-AXIS-DENY-UNREGISTERED-READINESS"
            ),
            "mutation": (
                "REMOVE_DECLARED_AXIS_FROM_STATE_REGISTRY"
            ),
            "axis_id": "READINESS-STATE-1.0",
            "expected_error": "DECLARED_STATE_AXIS_UNREGISTERED",
        },
        {
            "case_id": (
                "DECLARED-AXIS-DENY-EMPTY-TERMINALS-"
                "WITHOUT-NONTERMINAL"
            ),
            "mutation": "REMOVE_NONTERMINAL_DECLARATION",
            "axis_id": "READINESS-STATE-1.0",
            "expected_error": (
                "STATE_SOURCE_TERMINALITY_DECLARATION"
            ),
        },
        {
            "case_id": (
                "DECLARED-AXIS-DENY-NONTERMINAL-"
                "UNREACHABLE-VALUE"
            ),
            "mutation": (
                "REMOVE_INCOMING_TRANSITIONS_TO_VALUE"
            ),
            "axis_id": "READINESS-STATE-1.0",
            "value": "PRODUCTION_READY",
            "expected_error": "STATE_SOURCE_UNREACHABLE_VALUE",
        },
    ]
    if len(declared_axis_negative_cases) != 3:
        raise ValueError(
            "Declared-axis seam negative-case denominator drift"
        )
    return {
        "fixture_suite": "HERMES_STATE_EVENT_EXHAUSTIVE_V1",
        "source_catalog_id": catalog["catalog_id"],
        "source_catalog_digest": state_registry["digest"],
        "event_binding_catalog_id": binding_catalog["catalog_id"],
        "event_binding_catalog_digest": (
            "sha256:"
            + sha256_bytes(canonical_bytes(binding_catalog))
        ),
        "declared_denominator": denominator,
        "computed_denominator": computed,
        "transition_requests": transition_requests,
        "transition_facts": transition_facts,
        "outward_edge_events": outward,
        "initial_state_events": initial_events,
        "reference_only_events": reference_events,
        "declared_axis_transition_seam": {
            "fixture_id": (
                "FIXTURE-READINESS-TRANSITION-SCHEMA-SEAM-001"
            ),
            "evidence_scope": "SYNTHETIC_CONTRACT_FIXTURE_ONLY",
            "live_evidence": False,
            "readiness_tier_declared": False,
            "acceptance_case_count": 1,
            "negative_case_count": 3,
            "transition_fact": copy.deepcopy(
                readiness_acceptance_fact
            ),
            "negative_cases": declared_axis_negative_cases,
        },
    }


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
        if key in {"process_tree_empty_after_cleanup"}:
            return {"type": ["boolean", "null"]}
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


def tdd_primitive_schema(type_name: str) -> dict[str, Any]:
    if type_name == "nonempty_string":
        return {
            "type": "string",
            "minLength": 1,
            "maxLength": 1024,
            "pattern": r".*\S.*",
        }
    if type_name == "nonempty_versioned_schema_id":
        return {
            "type": "string",
            "pattern": r"^[a-z][a-z0-9-]*/v[1-9][0-9]*$",
        }
    if type_name == "safe_id":
        return {
            "type": "string",
            "pattern": r"^[A-Za-z][A-Za-z0-9._:-]{0,254}$",
        }
    if type_name == "safe_id_or_registered_urn":
        return {
            "type": "string",
            "minLength": 1,
            "maxLength": 1024,
            "pattern": (
                r"^(?:[A-Za-z][A-Za-z0-9._:-]{0,254}|"
                r"urn:[^\s]{1,1020})$"
            ),
        }
    if type_name == "safe_path":
        return {
            "type": "string",
            "minLength": 1,
            "maxLength": 1024,
            "pattern": r"^(?!/)(?!.*(?:^|/)\.\.?(?:/|$))(?!.*\\).+$",
            "x-ranex-normalized-repository-relative-posix-path": True,
        }
    if type_name == "semver":
        return {
            "type": "string",
            "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$",
        }
    if type_name == "sha1":
        return {"type": "string", "pattern": r"^[0-9a-f]{40}$"}
    if type_name == "sha256":
        return {
            "type": "string",
            "pattern": r"^sha256:[0-9a-f]{64}$",
        }
    if type_name == "sha256_without_prefix":
        return {"type": "string", "pattern": r"^[0-9a-f]{64}$"}
    if type_name == "strict_utc":
        return {
            "type": "string",
            "format": "date-time",
            "pattern": (
                r"^\d{4}-\d{2}-\d{2}T"
                r"\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
            ),
        }
    if type_name == "uint":
        return {"type": "integer", "minimum": 0}
    raise ValueError("Unknown ADR-0008 primitive type: " + type_name)


def tdd_inline_schema(spec: dict[str, Any]) -> dict[str, Any]:
    if set(spec) == {"enum"}:
        values = spec["enum"]
        if values and all(
            isinstance(value, bool) for value in values
        ):
            value_type = "boolean"
        elif values and all(
            isinstance(value, str) for value in values
        ):
            value_type = "string"
        elif values and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            for value in values
        ):
            value_type = "integer"
        else:
            raise ValueError(
                "ADR-0008 inline enum has mixed/unsupported types"
            )
        return {
            "type": value_type,
            "enum": copy.deepcopy(values),
        }
    if set(spec) == {"const"}:
        return {"const": copy.deepcopy(spec["const"])}
    if set(spec) == {"integer"}:
        return {"type": "integer", **copy.deepcopy(spec["integer"])}
    if set(spec) == {"array_items_enum"}:
        return {
            "type": "array",
            "items": {
                "type": "string",
                "enum": copy.deepcopy(spec["array_items_enum"]),
            },
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        }
    if set(spec) == {"exact_set"}:
        values = copy.deepcopy(spec["exact_set"])
        return {
            "type": "array",
            "const": values,
            "items": {
                "type": "string",
                "enum": values,
            },
            "minItems": len(values),
            "maxItems": len(values),
            "uniqueItems": True,
            "x-ranex-bytewise-sorted": True,
        }
    if set(spec) == {"enum_or_null"}:
        return {
            "oneOf": [
                {
                    "type": "string",
                    "enum": copy.deepcopy(spec["enum_or_null"]),
                },
                {"type": "null"},
            ]
        }
    raise ValueError("Unknown ADR-0008 inline type")


def tdd_type_schema(
    spec: Any,
    cardinality: str,
    type_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(spec, dict):
        result = tdd_inline_schema(spec)
    else:
        if not isinstance(spec, str):
            raise ValueError("ADR-0008 field type must be scalar/object")
        nullable = spec.endswith("|null")
        unwrapped = spec[:-5] if nullable else spec
        array_match = re.fullmatch(r"(.+)\[([^\]]*)\]", unwrapped)
        if array_match is not None:
            base_type = array_match.group(1)
            item_schema = tdd_type_schema(
                base_type,
                "1",
                type_rows,
            )
            result = {
                "type": "array",
                "items": item_schema,
                "uniqueItems": True,
                "x-ranex-bytewise-sorted": True,
            }
        elif unwrapped in type_rows:
            row = type_rows[unwrapped]
            result = {
                "type": "object",
                "properties": {
                    field_name: tdd_type_schema(
                        row["field_types"][field_name],
                        row["cardinality"][field_name],
                        type_rows,
                    )
                    for field_name in row["fields"]
                },
                "required": copy.deepcopy(row["fields"]),
                "additionalProperties": False,
                "x-ranex-type-id": row["type_id"],
                "x-ranex-type-version": row["type_version"],
                "x-ranex-semantic-invariants": copy.deepcopy(
                    row["invariants"]
                ),
            }
            sequence_ordered_fields = {
                "TddSubjectTransitionManifestV1": {
                    "step_subjects",
                    "edges",
                },
                "TddCycleJournalBindingV1": {
                    "phase_activity_ids",
                },
            }.get(row["type_id"], set())
            for ordered_field in sequence_ordered_fields:
                ordered_schema = result["properties"][ordered_field]
                ordered_schema.pop(
                    "x-ranex-bytewise-sorted",
                    None,
                )
                ordered_schema[
                    "x-ranex-sequence-order"
                ] = True
            if row["type_id"] == "TddSubjectTransitionManifestV1":
                result["properties"]["step_subjects"].pop(
                    "uniqueItems",
                    None,
                )
        else:
            result = tdd_primitive_schema(unwrapped)
        if nullable:
            result = {"oneOf": [result, {"type": "null"}]}
    if result.get("type") == "array":
        bounds = {
            "0..N": (0, None),
            "1..N": (1, None),
            "2..N": (2, None),
            "1..4": (1, 4),
        }
        if cardinality in bounds:
            minimum, maximum = bounds[cardinality]
            result["minItems"] = minimum
            if maximum is not None:
                result["maxItems"] = maximum
    return result


def tdd_health_contract_schemas() -> dict[str, dict[str, Any]]:
    catalog = parse_tdd_nested_type_catalog()
    nested = {row["type_id"]: row for row in catalog["types"]}
    top_rows = {
        row["type_id"]: row
        for row in catalog["top_level_record_types"]
    }
    record_paths = {
        "TddCycleRecordV1": (
            "common/tdd-cycle-record-v1.schema.json"
        ),
        "TddExceptionRecordV1": (
            "common/tdd-exception-record-v1.schema.json"
        ),
        "TestQuarantineRecordV1": (
            "common/test-quarantine-record-v1.schema.json"
        ),
        "TestDeletionRecordV1": (
            "common/test-deletion-record-v1.schema.json"
        ),
    }
    result: dict[str, dict[str, Any]] = {}
    for type_id, relative in record_paths.items():
        row = top_rows[type_id]
        result[relative] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/" + relative,
            "title": type_id,
            "type": "object",
            "properties": {
                field_name: tdd_type_schema(
                    row["field_types"][field_name],
                    row["cardinality"][field_name],
                    nested,
                )
                for field_name in row["fields"]
            },
            "required": copy.deepcopy(row["fields"]),
            "additionalProperties": False,
            "x-ranex-type-id": type_id,
            "x-ranex-type-version": row["type_version"],
            "x-ranex-semantic-invariants": copy.deepcopy(
                row["invariants"]
            ),
            "x-ranex-source-catalog-digest": (
                "sha256:" + sha256_bytes(canonical_bytes(catalog))
            ),
        }
        if type_id == "TddCycleRecordV1":
            result[relative]["properties"]["steps"].pop(
                "x-ranex-bytewise-sorted",
                None,
            )
            result[relative]["properties"]["steps"][
                "x-ranex-sequence-order"
            ] = True

    projection_contract = catalog["subject_projection_contract"]
    for projection in projection_contract["projections"]:
        source_row = top_rows[projection["source_record_type"]]
        properties: dict[str, Any] = {}
        for output_name in projection["output_fields"]:
            if output_name == "subject_schema":
                properties[output_name] = {
                    "const": projection["subject_schema"]
                }
            elif output_name == "subject_ref":
                properties[output_name] = {
                    "type": "string",
                    "pattern": r"^urn:ranex:[^\s]+$",
                }
            elif output_name in projection[
                "direct_included_source_fields"
            ]:
                properties[output_name] = tdd_type_schema(
                    source_row["field_types"][output_name],
                    source_row["cardinality"][output_name],
                    nested,
                )
            else:
                transform = projection["transformed_source_fields"][
                    output_name
                ]
                output_type = transform["output_type"]
                if output_type.startswith("TddCycleStepClaimV1"):
                    if transform["output_cardinality"] != "1..4":
                        raise ValueError(
                            "ADR-0008 step-claim projection cardinality "
                            "must be 1..4"
                        )
                    step_claim = projection_contract[
                        "nested_projection_types"
                    ]["TddCycleStepClaimV1"]
                    step_row = nested["TddCycleStepV1"]
                    claim_item = {
                        "type": "object",
                        "properties": {
                            field_name: tdd_type_schema(
                                step_row["field_types"][field_name],
                                step_row["cardinality"][field_name],
                                nested,
                            )
                            for field_name in step_claim["fields"]
                        },
                        "required": copy.deepcopy(
                            step_claim["fields"]
                        ),
                        "additionalProperties": False,
                        "x-ranex-type-id": "TddCycleStepClaimV1",
                    }
                    properties[output_name] = {
                        "type": "array",
                        "items": claim_item,
                        "minItems": 1,
                        "maxItems": 4,
                        "uniqueItems": True,
                    }
                else:
                    properties[output_name] = tdd_type_schema(
                        output_type,
                        transform["output_cardinality"],
                        nested,
                    )
        relative = projection["schema_ref"].removeprefix("schemas/")
        result[relative] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/" + relative,
            "title": projection["projection_id"],
            "type": "object",
            "properties": properties,
            "required": copy.deepcopy(projection["output_fields"]),
            "additionalProperties": False,
            "x-ranex-projection-contract-id": projection_contract[
                "contract_id"
            ],
            "x-ranex-projection": copy.deepcopy(projection),
            "x-ranex-source-catalog-digest": (
                "sha256:" + sha256_bytes(canonical_bytes(catalog))
            ),
        }
    return result


def checker_execution_subject_schema() -> dict[str, Any]:
    catalog = parse_tdd_nested_type_catalog()
    contract = catalog["checker_result_dual_subject_contract"]
    template = load_yaml_text_strict(
        read(TEMPLATES / "CHECKER_RESULT.yaml")
    )["subject"]
    fields = contract["execution_subject_required_fields"]
    if list(template) != fields:
        raise ValueError(
            "Checker execution subject template field drift"
        )
    sha = {
        "type": "string",
        "pattern": r"^sha256:[0-9a-f]{64}$",
    }
    sha1 = {"type": "string", "pattern": r"^[0-9a-f]{40}$"}
    semver = {
        "type": "string",
        "pattern": r"^[0-9]+\.[0-9]+\.[0-9]+$",
    }
    nonempty = {"type": "string", "minLength": 1}
    nullable_nonempty = {
        "oneOf": [copy.deepcopy(nonempty), {"type": "null"}]
    }
    nullable_sha = {
        "oneOf": [copy.deepcopy(sha), {"type": "null"}]
    }
    nullable_semver = {
        "oneOf": [copy.deepcopy(semver), {"type": "null"}]
    }
    properties: dict[str, Any] = {}
    for field_name in fields:
        if field_name == "subject_schema":
            schema = {"const": "checker-execution-subject/v1"}
        elif field_name in {"base_commit", "candidate_commit"}:
            schema = copy.deepcopy(sha1)
        elif field_name in {
            "activity_id",
            "effect_id",
            "route_lock_id",
        }:
            schema = copy.deepcopy(nullable_nonempty)
        elif field_name in {
            "artifact_digest",
            "release_profile_digest",
        }:
            schema = copy.deepcopy(nullable_sha)
        elif field_name.endswith("_digest"):
            schema = copy.deepcopy(sha)
        elif field_name in {
            "test_practice_profile_version",
        }:
            schema = copy.deepcopy(semver)
        elif field_name == "release_profile_version":
            schema = copy.deepcopy(nullable_semver)
        elif field_name == "release_profile_id":
            schema = copy.deepcopy(nullable_nonempty)
        elif field_name == "expected_run_aggregate_version":
            schema = {"type": "integer", "minimum": 0}
        else:
            schema = copy.deepcopy(nonempty)
        properties[field_name] = schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/assurance/"
            "checker-execution-subject-v1.schema.json"
        ),
        "title": "CheckerExecutionSubjectV1",
        "type": "object",
        "properties": properties,
        "required": copy.deepcopy(fields),
        "additionalProperties": False,
        "x-ranex-contract-id": contract["contract_id"],
        "x-ranex-source-catalog-digest": (
            "sha256:" + sha256_bytes(canonical_bytes(catalog))
        ),
    }


def project_tdd_record_subject(
    record: dict[str, Any],
    projection: dict[str, Any],
    projection_contract: dict[str, Any],
) -> dict[str, Any]:
    id_fields = {
        "TddCycleRecordV1": "cycle_id",
        "TddExceptionRecordV1": "exception_id",
        "TestQuarantineRecordV1": "quarantine_id",
        "TestDeletionRecordV1": "deletion_id",
    }
    source_type = projection["source_record_type"]
    subject = {
        "subject_schema": projection["subject_schema"],
        "subject_ref": (
            "urn:ranex:"
            + projection["subject_schema"].removesuffix("/v1")
            + ":"
            + record[id_fields[source_type]]
        ),
    }
    for field_name in projection["direct_included_source_fields"]:
        subject[field_name] = copy.deepcopy(record[field_name])
    for output_name, transform in projection[
        "transformed_source_fields"
    ].items():
        if (
            transform["output_type"]
            == "TddCycleStepClaimV1[]"
        ):
            claim_fields = projection_contract[
                "nested_projection_types"
            ]["TddCycleStepClaimV1"]["fields"]
            subject[output_name] = [
                {
                    field_name: copy.deepcopy(step[field_name])
                    for field_name in claim_fields
                }
                for step in record["steps"]
            ]
        elif transform["output_type"] == "SubjectBindingV1":
            source_names = transform["sources"]
            subject[output_name] = {
                field_name: copy.deepcopy(record[field_name])
                for field_name in source_names
            }
        else:
            raise ValueError(
                "Unsupported TDD subject fixture transform: "
                + transform["output_type"]
            )
    output_fields = projection["output_fields"]
    if (
        len(output_fields) != len(set(output_fields))
        or set(output_fields) != set(subject)
    ):
        raise ValueError(
            "Invalid authoritative TDD projection field-order manifest: "
            + projection["projection_id"]
        )
    return {
        field_name: subject[field_name]
        for field_name in output_fields
    }


def build_tdd_definition_tracer_fixture(
    registries: dict[str, Any],
) -> dict[str, Any]:
    catalog = parse_tdd_nested_type_catalog()
    projection_contract = catalog["subject_projection_contract"]
    projection_by_source = {
        row["source_record_type"]: row
        for row in projection_contract["projections"]
    }
    record_schema_paths = {
        "TddCycleRecordV1": (
            "schemas/common/tdd-cycle-record-v1.schema.json"
        ),
        "TddExceptionRecordV1": (
            "schemas/common/tdd-exception-record-v1.schema.json"
        ),
        "TestQuarantineRecordV1": (
            "schemas/common/test-quarantine-record-v1.schema.json"
        ),
        "TestDeletionRecordV1": (
            "schemas/common/test-deletion-record-v1.schema.json"
        ),
    }
    record_schemas = {
        type_id: load_json_strict(ROOT / schema_path)
        for type_id, schema_path in record_schema_paths.items()
    }
    record_samples = {
        type_id: closed_schema_fixture_value(
            schema,
            "tdd-record-" + type_id,
        )
        for type_id, schema in record_schemas.items()
    }
    cycle = record_samples["TddCycleRecordV1"]
    cycle.update(
        {
            "cycle_id": "TDD-CYCLE-DEFINITION-TRACER-001",
            "test_practice_profile_id": (
                "TESTPROFILE-WAVE1-DEFINITION-001"
            ),
            "test_practice_profile_version": "1.0.0",
            "test_practice_profile_digest": registries[
                "test-practice-profiles.json"
            ]["entries"][0]["digest"],
            "work_item_id": "WORK-TDD-TRACER-001",
            "task_packet_id": "TASKPACKET-TDD-TRACER-001",
            "task_packet_digest": (
                "sha256:" + hashlib.sha256(b"tracer-packet").hexdigest()
            ),
            "change_profile": "BEHAVIOR_CHANGE",
            "no_refactor_needed": False,
            "built_artifact_digest": (
                "sha256:"
                + hashlib.sha256(
                    b"tdd-tracer-built-artifact"
                ).hexdigest()
            ),
            "built_artifact_evidence_ref": {
                "artifact_type": "checker_result",
                "artifact_ref": "CHECKER-TDD-BUILT-ARTIFACT-001",
                "artifact_digest": "sha256:" + "0" * 64,
            },
            "release_profile_id": None,
            "release_profile_version": None,
            "release_profile_digest": None,
            "tdd_exception_ids": [],
            "quarantine_ids": [],
            "recorded_at": "2026-07-28T00:11:00Z",
            "result": "PASS",
            "status": "GATED",
            "gated_at": "2026-07-28T00:10:00Z",
        }
    )

    exact_subject_schema = load_json_strict(
        SCHEMAS / "common" / "exact-subject-v1.schema.json"
    )
    subject_commit_by_label = {
        "base": "1" * 40,
        "red": "2" * 40,
        "green": "3" * 40,
        "candidate": "4" * 40,
    }
    subject_parent_by_label = {
        "base": "0" * 40,
        "red": "1" * 40,
        "green": "2" * 40,
        "candidate": "3" * 40,
    }
    subject_registry_rows: list[dict[str, Any]] = []

    def binding(label: str) -> dict[str, str]:
        document = closed_schema_fixture_value(
            exact_subject_schema,
            "tdd-subject-document-" + label,
        )
        document.update(
            {
                "project_id": "PROJECT-TDD-TRACER",
                "work_item_id": "WORK-TDD-TRACER-001",
                "run_id": "RUN-TDD-TRACER-001",
                "base_commit": "1" * 40,
                "candidate_commit": subject_commit_by_label[label],
                "artifact_digest": (
                    cycle["built_artifact_digest"]
                    if label == "candidate"
                    else None
                ),
            }
        )
        document_digest = (
            "sha256:" + sha256_bytes(canonical_bytes(document))
        )
        binding_value = {
            "subject_schema": "exact-subject/v1",
            "subject_ref": "urn:ranex:exact-subject:" + label,
            "subject_digest": document_digest,
        }
        subject_registry_rows.append(
            {
                **binding_value,
                "schema_path": (
                    "schemas/common/exact-subject-v1.schema.json"
                ),
                "document": document,
                "commit_sha1": subject_commit_by_label[label],
                "parent_commit_sha1": subject_parent_by_label[label],
                "tree_digest": (
                    "sha256:"
                    + hashlib.sha256(
                        ("tree-" + label).encode("utf-8")
                    ).hexdigest()
                ),
                "artifact_digest": (
                    cycle["built_artifact_digest"]
                    if label == "candidate"
                    else None
                ),
                "test_practice_profile_id": cycle[
                    "test_practice_profile_id"
                ],
                "test_practice_profile_version": cycle[
                    "test_practice_profile_version"
                ],
                "test_practice_profile_digest": cycle[
                    "test_practice_profile_digest"
                ],
                "freshness_status": "CURRENT",
            }
        )
        return binding_value

    base_subject = binding("base")
    red_subject = binding("red")
    green_subject = binding("green")
    candidate_subject = binding("candidate")
    cycle["base_subject"] = base_subject
    cycle["candidate_subject"] = candidate_subject
    subject_sequence = [
        red_subject,
        green_subject,
        candidate_subject,
        candidate_subject,
    ]
    step_kinds = [
        "RED",
        "GREEN",
        "REFACTOR",
        "ARCHITECTURE_CHECK",
    ]
    fingerprint_schema = record_schemas["TddCycleRecordV1"][
        "properties"
    ]["steps"]["items"]["properties"][
        "expected_failure_fingerprint"
    ]["oneOf"][0]
    failure_fingerprint = closed_schema_fixture_value(
        fingerprint_schema,
        "tdd-red-fingerprint",
    )
    failure_fingerprint.update(
        {
            "stable_test_id": "TEST-TDD-TRACER-001",
            "criterion_id": "CRITERION-TDD-TRACER-001",
            "failure_denominator_row_id": (
                "FAILURE-ROW-TDD-TRACER-001"
            ),
            "expected_failure_code": "EXPECTED-ASSERTION-FAILURE",
        }
    )
    steps: list[dict[str, Any]] = []
    for index, (step_kind, step_subject) in enumerate(
        zip(step_kinds, subject_sequence, strict=True),
        start=1,
    ):
        is_red = step_kind == "RED"
        steps.append(
            {
                "step_kind": step_kind,
                "sequence": index,
                "step_subject": copy.deepcopy(step_subject),
                "step_snapshot_digest": step_subject[
                    "subject_digest"
                ],
                "checker_result_ref": {
                    "artifact_type": "checker_result",
                    "artifact_ref": (
                        f"CHECKER-TDD-TRACER-{index:03d}"
                    ),
                    "artifact_digest": "sha256:" + "0" * 64,
                },
                "expected_outcome": (
                    "EXPECTED_FAILURE" if is_red else "PASS"
                ),
                "expected_failure_fingerprint": (
                    copy.deepcopy(failure_fingerprint)
                    if is_red
                    else None
                ),
                "started_at": (
                    f"2026-07-28T00:{index * 2 - 1:02d}:00Z"
                ),
                "finished_at": (
                    f"2026-07-28T00:{index * 2:02d}:00Z"
                ),
            }
        )
    cycle["steps"] = steps
    edges: list[dict[str, Any]] = []
    prior_subject = base_subject
    for index, (step_kind, step_subject) in enumerate(
        zip(step_kinds, subject_sequence, strict=True),
        start=1,
    ):
        edge = {
            "edge_sequence": index,
            "from_subject": copy.deepcopy(prior_subject),
            "to_subject": copy.deepcopy(step_subject),
            "to_step_kind": step_kind,
            "relation": (
                "VALIDATION_ONLY"
                if prior_subject == step_subject
                else "SOURCE_CHANGE"
            ),
            "digest": "",
        }
        edge["digest"] = digest_value(edge)
        edges.append(edge)
        prior_subject = step_subject
    transition_manifest = {
        "manifest_id": "TDD-TRANSITION-MANIFEST-001",
        "base_subject": copy.deepcopy(base_subject),
        "step_subjects": copy.deepcopy(subject_sequence),
        "candidate_subject": copy.deepcopy(candidate_subject),
        "edges": edges,
        "digest": "",
    }
    transition_manifest["digest"] = digest_value(
        transition_manifest
    )
    cycle["subject_transition_manifest"] = transition_manifest
    subject_registry = subject_registry_rows
    subject_registry_by_ref = {
        row["subject_ref"]: row for row in subject_registry
    }

    test_denominator = {
        "schema_version": "1.0.0",
        "manifest_id": "TEST-DENOMINATOR-TDD-TRACER-001",
        "rows": [
            {
                "stable_test_id": "TEST-TDD-TRACER-001",
                "criterion_ids": ["CRITERION-TDD-TRACER-001"],
                "test_path": (
                    "tests/unit/tdd/test_definition_contract.py"
                ),
                "test_definition_digest": (
                    "sha256:"
                    + hashlib.sha256(
                        b"tdd-definition-contract-test"
                    ).hexdigest()
                ),
            }
        ],
        "digest": "",
    }
    test_denominator["digest"] = digest_value(test_denominator)
    failure_denominator_row = {
        "row_id": "FAILURE-ROW-TDD-TRACER-001",
        "stable_test_id": "TEST-TDD-TRACER-001",
        "criterion_id": "CRITERION-TDD-TRACER-001",
        "failure_class": "ASSERTION_FAILURE",
        "expected_failure_code": "EXPECTED-ASSERTION-FAILURE",
    }
    failure_denominator_row_digest = (
        "sha256:"
        + sha256_bytes(canonical_bytes(failure_denominator_row))
    )
    failure_denominator = {
        "schema_version": "1.0.0",
        "manifest_id": "FAILURE-DENOMINATOR-TDD-TRACER-001",
        "rows": [
            {
                **failure_denominator_row,
                "row_digest": failure_denominator_row_digest,
            }
        ],
        "digest": "",
    }
    failure_denominator["digest"] = digest_value(
        failure_denominator
    )
    matcher = {
        "schema_version": "1.0.0",
        "matcher_schema": "tdd-failure-matcher/v1",
        "matcher_ref": "urn:ranex:tdd-failure-matcher:red-001",
        "predicate": {
            "outcome": "EXPECTED_FAILURE",
            "failure_class": "ASSERTION_FAILURE",
            "failure_code": "EXPECTED-ASSERTION-FAILURE",
            "stable_test_id": "TEST-TDD-TRACER-001",
            "criterion_id": "CRITERION-TDD-TRACER-001",
            "harness_failure_exclusion": True,
        },
    }
    matcher_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(matcher))
    )
    raw_failure_observation = {
        "schema_version": "1.0.0",
        "observation_id": "RAW-FAILURE-TDD-TRACER-001",
        "checker_result_id": "CHECKER-TDD-TRACER-001",
        "stable_test_id": "TEST-TDD-TRACER-001",
        "criterion_id": "CRITERION-TDD-TRACER-001",
        "outcome": "EXPECTED_FAILURE",
        "failure_class": "ASSERTION_FAILURE",
        "failure_code": "EXPECTED-ASSERTION-FAILURE",
        "harness_failure": False,
        "errored": False,
        "timed_out": False,
        "cancelled": False,
        "matcher_ref": matcher["matcher_ref"],
    }
    oracle_source = {
        "schema_version": "1.0.0",
        "oracle_source_schema": "tdd-oracle-source/v1",
        "oracle_source_ref": "urn:ranex:tdd-oracle:criterion-001",
        "authority_basis_id": "REQUIREMENT-TDD-TRACER-001",
        "criterion_id": "CRITERION-TDD-TRACER-001",
        "expected_result": "ASSERTION_FAILURE_UNTIL_BEHAVIOR_EXISTS",
        "implementation_derived": False,
        "independently_reviewed": True,
    }
    oracle_source_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(oracle_source))
    )
    authority_basis = {
        "schema_version": "1.0.0",
        "authority_basis_id": "REQUIREMENT-TDD-TRACER-001",
        "authority_kind": "REQUIREMENT",
        "criterion_ids": ["CRITERION-TDD-TRACER-001"],
        "status": "ACTIVE",
    }
    reproducibility_manifests = {}
    for manifest_kind in (
        "seed_manifest",
        "input_manifest",
        "rule_version_manifest",
        "journal_capture_policy",
    ):
        manifest = {
            "schema_version": "1.0.0",
            "manifest_kind": manifest_kind,
            "manifest_id": (
                manifest_kind.upper().replace("_", "-")
                + "-TDD-TRACER-001"
            ),
            "entries": [
                {
                    "key": manifest_kind + "-entry",
                    "value_digest": (
                        "sha256:"
                        + hashlib.sha256(
                            manifest_kind.encode("utf-8")
                        ).hexdigest()
                    ),
                }
            ],
        }
        reproducibility_manifests[manifest_kind] = {
            "document": manifest,
            "digest": (
                "sha256:" + sha256_bytes(canonical_bytes(manifest))
            ),
        }
    definition_stores = {
        "test_denominator": test_denominator,
        "failure_denominator": failure_denominator,
        "matcher": {
            "document": matcher,
            "digest": matcher_digest,
        },
        "raw_failure_observation": raw_failure_observation,
        "oracle_source": {
            "document": oracle_source,
            "digest": oracle_source_digest,
        },
        "authority_basis": authority_basis,
        "reproducibility_manifests": reproducibility_manifests,
    }
    cycle["test_denominator_manifest_digest"] = test_denominator[
        "digest"
    ]
    cycle["failure_denominator_manifest_digest"] = (
        failure_denominator["digest"]
    )
    failure_fingerprint.update(
        {
            "failure_denominator_row_digest": (
                failure_denominator_row_digest
            ),
            "matcher_schema": matcher["matcher_schema"],
            "matcher_ref": matcher["matcher_ref"],
            "matcher_digest": matcher_digest,
            "harness_failure_exclusion": True,
        }
    )
    steps[0]["expected_failure_fingerprint"] = copy.deepcopy(
        failure_fingerprint
    )
    rule_registry = registries[
        "architecture-rule-assessments.json"
    ]
    rule_ids = sorted(
        entry["rule_id"] for entry in rule_registry["entries"]
    )
    coverage_rows = [
        {"rule_id": rule_id, "disposition": "APPLICABLE"}
        for rule_id in rule_ids
    ]
    cycle["architecture_rule_coverage"].update(
        {
            "rule_registry_id": rule_registry["registry_id"],
            "rule_registry_version": rule_registry["version"],
            "rule_registry_digest": (
                "sha256:"
                + sha256_bytes(canonical_bytes(rule_registry))
            ),
            "applicable_rule_ids": rule_ids,
            "not_applicable_rule_ids": [],
            "coverage_manifest_digest": (
                "sha256:"
                + sha256_bytes(canonical_bytes(coverage_rows))
            ),
        }
    )
    cycle["architecture_rule_not_applicable_proofs"] = []
    cycle["oracle_provenance"] = {
        "oracle_source_schema": oracle_source[
            "oracle_source_schema"
        ],
        "oracle_source_ref": oracle_source["oracle_source_ref"],
        "oracle_source_digest": oracle_source_digest,
        "authority_basis_id": authority_basis[
            "authority_basis_id"
        ],
        "independence_class": "INDEPENDENT_PRIMARY",
    }
    cycle["reproducibility_envelope"]["tier"] = "TIER_1"
    cycle["reproducibility_envelope"].update(
        {
            "seed_manifest_digest": reproducibility_manifests[
                "seed_manifest"
            ]["digest"],
            "input_manifest_digest": reproducibility_manifests[
                "input_manifest"
            ]["digest"],
            "rule_version_manifest_digest": (
                reproducibility_manifests[
                    "rule_version_manifest"
                ]["digest"]
            ),
            "journal_capture_policy_digest": (
                reproducibility_manifests[
                    "journal_capture_policy"
                ]["digest"]
            ),
        }
    )
    for nullable_field in [
        "image_digest",
        "toolchain_manifest_digest",
        "network_policy_digest",
        "filesystem_policy_digest",
        "dependency_lock_digest",
        "execution_capability_profile_digest",
    ]:
        cycle["reproducibility_envelope"][nullable_field] = None

    checker_schema = load_json_strict(
        SCHEMAS / "assurance" / "checker-result-v1.schema.json"
    )
    artifacts: dict[str, dict[str, Any]] = {}
    for index, step in enumerate(steps, start=1):
        checker = closed_schema_fixture_value(
            checker_schema,
            f"tdd-tracer-checker-{index}",
        )
        checker_id = f"CHECKER-TDD-TRACER-{index:03d}"
        checker.update(
            {
                "checker_result_id": checker_id,
                "core_sdlc_trace_ref": "TRACE-TDD-TRACER-001",
                "subject_schema": step["step_subject"][
                    "subject_schema"
                ],
                "subject_ref": step["step_subject"]["subject_ref"],
                "subject_digest": step["step_subject"][
                    "subject_digest"
                ],
                "status": "COMPLETED",
                "outcome": step["expected_outcome"],
                "failure_code": (
                    failure_fingerprint["expected_failure_code"]
                    if step["step_kind"] == "RED"
                    else None
                ),
                "failure_fingerprint": copy.deepcopy(
                    step["expected_failure_fingerprint"]
                ),
                "evidence_refs": (
                    [
                        test_denominator["manifest_id"],
                        failure_denominator["manifest_id"],
                        matcher["matcher_ref"],
                    ]
                    if step["step_kind"] == "RED"
                    else []
                ),
                "raw_artifact_refs": (
                    [raw_failure_observation["observation_id"]]
                    if step["step_kind"] == "RED"
                    else []
                ),
                "coverage": (
                    rule_ids
                    if step["step_kind"] == "ARCHITECTURE_CHECK"
                    else ["TDD_CYCLE_STEP_CHECKER"]
                ),
                "limitations": [],
                "started_at": step["started_at"],
                "finished_at": step["finished_at"],
                "digest": "",
            }
        )
        checker["checker"].update(
            {
                "checker_id": "CHECKER-TDD-DEFINITION",
                "checker_version": "1.0.0",
                "code_digest": "sha256:" + "5" * 64,
                "fixture_suite_digest": "sha256:" + "6" * 64,
                "qualification_id": "QUALIFICATION-TDD-001",
            }
        )
        checker["subject"].update(
            {
                "base_commit": "1" * 40,
                "candidate_commit": subject_registry_by_ref[
                    step["step_subject"]["subject_ref"]
                ]["commit_sha1"],
                "artifact_digest": None,
                "test_practice_profile_id": cycle[
                    "test_practice_profile_id"
                ],
                "test_practice_profile_version": cycle[
                    "test_practice_profile_version"
                ],
                "test_practice_profile_digest": cycle[
                    "test_practice_profile_digest"
                ],
                "release_profile_id": None,
                "release_profile_version": None,
                "release_profile_digest": None,
            }
        )
        checker["digest"] = digest_value(checker)
        artifacts[checker_id] = checker
        step["checker_result_ref"]["artifact_digest"] = checker[
            "digest"
        ]

    built_checker = closed_schema_fixture_value(
        checker_schema,
        "tdd-tracer-built-artifact-checker",
    )
    built_checker_id = "CHECKER-TDD-BUILT-ARTIFACT-001"
    built_checker.update(
        {
            "checker_result_id": built_checker_id,
            "core_sdlc_trace_ref": "TRACE-TDD-TRACER-001",
            "subject_schema": candidate_subject["subject_schema"],
            "subject_ref": candidate_subject["subject_ref"],
            "subject_digest": candidate_subject["subject_digest"],
            "status": "COMPLETED",
            "outcome": "PASS",
            "failure_code": None,
            "failure_fingerprint": None,
            "evidence_refs": [],
            "raw_artifact_refs": [],
            "coverage": ["TDD_CYCLE_BUILT_ARTIFACT_CHECKER"],
            "limitations": [],
            "started_at": "2026-07-28T00:06:05Z",
            "finished_at": "2026-07-28T00:06:20Z",
            "digest": "",
        }
    )
    built_checker["checker"].update(
        {
            "checker_id": "CHECKER-TDD-BUILT-ARTIFACT",
            "checker_version": "1.0.0",
            "code_digest": "sha256:" + "a" * 64,
            "fixture_suite_digest": "sha256:" + "b" * 64,
            "qualification_id": "QUALIFICATION-TDD-BUILD-001",
        }
    )
    built_checker["subject"].update(
        {
            "base_commit": subject_registry_by_ref[
                base_subject["subject_ref"]
            ]["commit_sha1"],
            "candidate_commit": subject_registry_by_ref[
                candidate_subject["subject_ref"]
            ]["commit_sha1"],
            "artifact_digest": cycle["built_artifact_digest"],
            "test_practice_profile_id": cycle[
                "test_practice_profile_id"
            ],
            "test_practice_profile_version": cycle[
                "test_practice_profile_version"
            ],
            "test_practice_profile_digest": cycle[
                "test_practice_profile_digest"
            ],
            "release_profile_id": None,
            "release_profile_version": None,
            "release_profile_digest": None,
        }
    )
    built_checker["digest"] = digest_value(built_checker)
    artifacts[built_checker_id] = built_checker
    cycle["built_artifact_evidence_ref"] = {
        "artifact_type": "checker_result",
        "artifact_ref": built_checker_id,
        "artifact_digest": built_checker["digest"],
    }
    architecture_checker = artifacts[
        steps[-1]["checker_result_ref"]["artifact_ref"]
    ]
    architecture_rule_results = [
        {
            "result_id": (
                "ARCH-RULE-RESULT-" + f"{index:03d}"
            ),
            "rule_id": rule_id,
            "checker_result_id": architecture_checker[
                "checker_result_id"
            ],
            "subject": copy.deepcopy(candidate_subject),
            "outcome": "PASS",
        }
        for index, rule_id in enumerate(rule_ids, start=1)
    ]

    journal_ref = "urn:ranex:journal:tdd-tracer-001"
    journal_run_id = "RUN-TDD-TRACER-001"
    journal_activities: list[dict[str, Any]] = []
    journal_events: list[dict[str, Any]] = []
    journal_facts: list[dict[str, Any]] = []
    phase_activity_manifest: list[dict[str, Any]] = []
    event_sequence = 0
    for step in steps:
        activity_id = (
            f"ACTIVITY-TDD-TRACER-{step['sequence']:03d}"
        )
        event_ids: list[str] = []
        fact_ids: list[str] = []
        started_minute = step["sequence"] * 2 - 1
        finished_minute = step["sequence"] * 2
        event_specs = [
            (
                "REQUEST",
                f"2026-07-28T00:{started_minute:02d}:00Z",
            ),
            (
                "DISPATCH",
                f"2026-07-28T00:{started_minute:02d}:10Z",
            ),
            (
                "RESOLUTION",
                f"2026-07-28T00:{started_minute:02d}:50Z",
            ),
            (
                "CHECKER_BINDING",
                f"2026-07-28T00:{finished_minute:02d}:00Z",
            ),
        ]
        for event_kind, occurred_at in event_specs:
            event_sequence += 1
            event_id = (
                f"EVENT-TDD-TRACER-{event_sequence:03d}"
            )
            fact_id = f"FACT-TDD-TRACER-{event_sequence:03d}"
            checker_ref = (
                copy.deepcopy(step["checker_result_ref"])
                if event_kind == "CHECKER_BINDING"
                else None
            )
            event = {
                "event_id": event_id,
                "journal_sequence": event_sequence,
                "event_kind": event_kind,
                "run_id": journal_run_id,
                "journal_ref": journal_ref,
                "activity_id": activity_id,
                "owner_cycle_id": cycle["cycle_id"],
                "step_sequence": step["sequence"],
                "step_kind": step["step_kind"],
                "subject": copy.deepcopy(step["step_subject"]),
                "checker_result_ref": checker_ref,
                "occurred_at": occurred_at,
            }
            fact = {
                "fact_id": fact_id,
                "event_id": event_id,
                "event_kind": event_kind,
                "run_id": journal_run_id,
                "journal_ref": journal_ref,
                "activity_id": activity_id,
                "owner_cycle_id": cycle["cycle_id"],
                "subject": copy.deepcopy(step["step_subject"]),
                "checker_result_ref": copy.deepcopy(checker_ref),
                "recorded_at": occurred_at,
            }
            journal_events.append(event)
            journal_facts.append(fact)
            event_ids.append(event_id)
            fact_ids.append(fact_id)
        activity = {
            "activity_id": activity_id,
            "owner_cycle_id": cycle["cycle_id"],
            "run_id": journal_run_id,
            "journal_ref": journal_ref,
            "step_sequence": step["sequence"],
            "step_kind": step["step_kind"],
            "subject": copy.deepcopy(step["step_subject"]),
            "request_event_id": event_ids[0],
            "dispatch_event_id": event_ids[1],
            "resolution_event_id": event_ids[2],
            "checker_binding_event_id": event_ids[3],
            "started_at": event_specs[0][1],
            "finished_at": event_specs[-1][1],
        }
        journal_activities.append(activity)
        phase_activity_manifest.append(
            {
                "activity_id": activity_id,
                "step_sequence": step["sequence"],
                "step_kind": step["step_kind"],
                "subject": copy.deepcopy(step["step_subject"]),
                "event_ids": event_ids,
                "fact_ids": fact_ids,
                "checker_result_ref": copy.deepcopy(
                    step["checker_result_ref"]
                ),
            }
        )
    phase_activity_manifest_digest = (
        "sha256:"
        + sha256_bytes(canonical_bytes(phase_activity_manifest))
    )
    journal_slice = {
        "schema_version": "1.0.0",
        "journal_ref": journal_ref,
        "run_id": journal_run_id,
        "owner_cycle_id": cycle["cycle_id"],
        "journal_start_sequence": 1,
        "journal_end_sequence": event_sequence,
        "activities": journal_activities,
        "events": journal_events,
        "facts": journal_facts,
    }
    journal_manifest_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(journal_slice))
    )
    journal_fixture = {
        **journal_slice,
        "phase_activity_manifest": phase_activity_manifest,
        "phase_activity_manifest_digest": (
            phase_activity_manifest_digest
        ),
        "journal_manifest_digest": journal_manifest_digest,
    }
    cycle["cycle_journal_binding"] = {
        "run_id": journal_run_id,
        "journal_ref": journal_ref,
        "journal_start_sequence": 1,
        "journal_end_sequence": event_sequence,
        "phase_activity_ids": [
            row["activity_id"] for row in journal_activities
        ],
        "phase_activity_manifest_digest": (
            phase_activity_manifest_digest
        ),
        "journal_manifest_digest": journal_manifest_digest,
    }

    cycle_projection = projection_by_source["TddCycleRecordV1"]
    cycle_subject = project_tdd_record_subject(
        cycle,
        cycle_projection,
        projection_contract,
    )
    cycle_subject_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(cycle_subject))
    )
    cycle["exact_subject_ref"] = cycle_subject["subject_ref"]
    cycle["exact_subject_digest"] = cycle_subject_digest
    candidate_row = subject_registry_by_ref[
        candidate_subject["subject_ref"]
    ]
    landing_candidate_tuple = {
        key: copy.deepcopy(candidate_row[key])
        for key in (
            "subject_schema",
            "subject_ref",
            "subject_digest",
            "commit_sha1",
            "tree_digest",
            "artifact_digest",
            "test_practice_profile_id",
            "test_practice_profile_version",
            "test_practice_profile_digest",
            "freshness_status",
        )
    }
    authority_stores = {
        "tdd_exceptions": {
            "store_id": "STORE-TDD-EXCEPTIONS-001",
            "entries": [],
        },
        "test_quarantines": {
            "store_id": "STORE-TEST-QUARANTINES-001",
            "entries": [],
        },
    }

    snapshot_schema = load_json_strict(
        SCHEMAS / "assurance" / "evidence-snapshot-v1.schema.json"
    )
    snapshot = closed_schema_fixture_value(
        snapshot_schema,
        "tdd-tracer-evidence-snapshot",
    )
    snapshot_id = "SNAPSHOT-TDD-TRACER-001"
    checker_ids = [
        step["checker_result_ref"]["artifact_ref"] for step in steps
    ] + [built_checker_id]
    snapshot.update(
        {
            "snapshot_id": snapshot_id,
            "subject_schema": cycle_subject["subject_schema"],
            "subject_ref": cycle_subject["subject_ref"],
            "subject_digest": cycle_subject_digest,
            "subject_manifest_digest": (
                "sha256:"
                + sha256_bytes(canonical_bytes(cycle_subject))
            ),
            "core_sdlc_trace_ref": "TRACE-TDD-TRACER-001",
            "required_claim_ids": checker_ids,
            "eligible_evidence_refs": checker_ids,
            "ineligible_evidence": [],
            "freshness_cutoff": "2026-07-28T00:00:00Z",
            "coverage": checker_ids,
            "missing_claim_ids": [],
            "conflicts": [],
            "created_by_service_id": "ASSURANCE-SNAPSHOT-SERVICE",
            "created_at": "2026-07-28T00:08:30Z",
            "digest": "",
        }
    )
    snapshot["digest"] = digest_value(snapshot)
    artifacts[snapshot_id] = snapshot

    gate_schema = load_json_strict(
        SCHEMAS / "assurance" / "gate-evaluation-v1.schema.json"
    )
    gate = closed_schema_fixture_value(
        gate_schema,
        "tdd-tracer-gate",
    )
    gate_id = "GATE-TDD-TRACER-001"
    gate.update(
        {
            "gate_evaluation_id": gate_id,
            "gate_namespace": "TDD",
            "gate_definition_id": "TDD-CYCLE-GATE",
            "gate_definition_version": "1.0.0",
            "evaluator_id": "TDD-GATE-EVALUATOR",
            "evaluator_version": "1.0.0",
            "evaluator_code_digest": "sha256:" + "7" * 64,
            "qualification_id": "QUALIFICATION-TDD-GATE-001",
            "subject_schema": cycle_subject["subject_schema"],
            "subject_ref": cycle_subject["subject_ref"],
            "subject_digest": cycle_subject_digest,
            "subject_manifest_digest": None,
            "core_sdlc_trace_ref": "TRACE-TDD-TRACER-001",
            "evidence_snapshot_id": snapshot_id,
            "evidence_snapshot_digest": snapshot["digest"],
            "required_claim_ids": checker_ids,
            "observed_claim_ids": checker_ids,
            "checker_result_refs": checker_ids,
            "review_verdict_refs": [],
            "applicability_proof_refs": [],
            "freshness_evaluation": [],
            "coverage": rule_ids,
            "missing_claim_ids": [],
            "conflicts": [],
            "outcome": "PASS",
            "reason_codes": [],
            "evaluated_at": "2026-07-28T00:09:00Z",
            "digest": "",
        }
    )
    gate["digest"] = digest_value(gate)
    artifacts[gate_id] = gate
    cycle["evidence_snapshot_ref"] = {
        "artifact_type": "evidence_snapshot",
        "artifact_ref": snapshot_id,
        "artifact_digest": snapshot["digest"],
    }
    cycle["cycle_gate_evaluation_ref"] = {
        "artifact_type": "gate_evaluation",
        "artifact_ref": gate_id,
        "artifact_digest": gate["digest"],
    }

    landing_schema = load_json_strict(
        SCHEMAS / "execution" / "landing-record-v1.schema.json"
    )
    landing = closed_schema_fixture_value(
        landing_schema,
        "tdd-cycle-landing",
    )
    landing.update(
        {
            "landing_id": "LANDING-TDD-TRACER-001",
            "subject_schema": cycle_subject["subject_schema"],
            "subject_ref": cycle_subject["subject_ref"],
            "subject_digest": cycle_subject_digest,
            "subject_manifest_digest": (
                "sha256:"
                + sha256_bytes(canonical_bytes(cycle_subject))
            ),
            "core_sdlc_trace_ref": "TRACE-TDD-TRACER-001",
            "candidate_commit": "4" * 40,
            "target_branch": "main",
            "target_head_before": "1" * 40,
            "landed_commit": "8" * 40,
            "landing_strategy": "FAST_FORWARD",
            "permit_id": "PERMIT-TDD-TRACER-001",
            "actor_principal_id": "LANDING-SERVICE",
            "provider_receipt_ref": "RECEIPT-TDD-TRACER-001",
            "started_at": "2026-07-28T00:12:00Z",
            "finished_at": "2026-07-28T00:13:00Z",
            "status": catalog["landing_record_status_authority"][
                "success_literal"
            ],
            "evidence_refs": [gate_id],
            "digest": "",
        }
    )
    landing["digest"] = digest_value(landing)

    schema_samples = {}
    for type_id, record in record_samples.items():
        if type_id == "TddCycleRecordV1":
            record = cycle
        schema_samples[type_id] = {
            "schema_path": record_schema_paths[type_id],
            "instance": record,
        }
    projection_samples = {
        type_id: project_tdd_record_subject(
            sample["instance"],
            projection_by_source[type_id],
            projection_contract,
        )
        for type_id, sample in schema_samples.items()
    }
    projection_field_order_cases: list[dict[str, Any]] = []
    for projection in projection_contract["projections"]:
        canonical_fields = projection["output_fields"]
        permutation = copy.deepcopy(canonical_fields)
        permutation[0], permutation[1] = permutation[1], permutation[0]
        mutations = [
            ("PERMUTED", permutation),
            (
                "DUPLICATE",
                [
                    canonical_fields[0],
                    canonical_fields[0],
                    *canonical_fields[1:],
                ],
            ),
            ("OMITTED", canonical_fields[:-1]),
            (
                "INJECTED",
                [*canonical_fields, "forged_output_field"],
            ),
            (
                "SELF_REFERENTIAL",
                [*canonical_fields, "exact_subject_digest"],
            ),
        ]
        for mutation, output_fields in mutations:
            projection_field_order_cases.append(
                {
                    "fixture_id": (
                        projection["projection_id"]
                        + "-FIELD-ORDER-"
                        + mutation
                    ),
                    "projection_id": projection["projection_id"],
                    "mutation": mutation,
                    "output_fields": output_fields,
                    "expected_error": (
                        "TDD_PROJECTION_FIELD_ORDER_MANIFEST"
                    ),
                }
            )
    profile_cases: list[dict[str, Any]] = []
    for profile_name, profile in catalog[
        "change_profile_contract"
    ]["profiles"].items():
        for branch_name in [
            "no_refactor_needed_false",
            "no_refactor_needed_true",
        ]:
            sequence = profile[branch_name]
            profile_cases.append(
                {
                    "profile": profile_name,
                    "no_refactor_needed": (
                        branch_name == "no_refactor_needed_true"
                    ),
                    "step_kinds": copy.deepcopy(sequence),
                    "expected_result": (
                        "PASS" if sequence is not None else "REJECT"
                    ),
                }
            )
    landing_cases = [
        {
            "fixture_id": "TDD-LANDING-VALID-JOIN",
            "mutation": "NONE",
            "expected_result": "ACCEPTED",
        },
        *[
            {
                "fixture_id": (
                    "TDD-LANDING-PROHIBITED-CYCLE-FIELD-"
                    + field_name.upper()
                ),
                "mutation": "ADD_PROHIBITED_CYCLE_FIELD",
                "field": field_name,
                "expected_error": "TDD_CYCLE_SCHEMA_INVALID",
            }
            for field_name in catalog[
                "cycle_landing_receipt_contract"
            ]["prohibited_cycle_fields"]
        ],
        {
            "fixture_id": "TDD-LANDING-MISSING-RECEIPT",
            "mutation": "MISSING_RECEIPT",
            "expected_error": "TDD_LANDING_MISSING",
        },
        {
            "fixture_id": "TDD-LANDING-DUPLICATE-RECEIPT",
            "mutation": "DUPLICATE_RECEIPT",
            "expected_error": "TDD_LANDING_DUPLICATE",
        },
        {
            "fixture_id": "TDD-LANDING-FAILED-RECEIPT",
            "mutation": "FAILED_RECEIPT",
            "expected_error": "TDD_LANDING_STATUS",
        },
        {
            "fixture_id": "TDD-LANDING-STALE-RECEIPT",
            "mutation": "STALE_RECEIPT",
            "expected_error": "TDD_LANDING_STALE",
        },
        {
            "fixture_id": "TDD-LANDING-WRONG-SUBJECT-SCHEMA",
            "mutation": "WRONG_SUBJECT_SCHEMA",
            "expected_error": "TDD_LANDING_SUBJECT_SCHEMA",
        },
        {
            "fixture_id": "TDD-LANDING-WRONG-SUBJECT-REF",
            "mutation": "WRONG_SUBJECT_REF",
            "expected_error": "TDD_LANDING_SUBJECT_REF",
        },
        {
            "fixture_id": "TDD-LANDING-WRONG-SUBJECT-DIGEST",
            "mutation": "WRONG_SUBJECT_DIGEST",
            "expected_error": "TDD_LANDING_SUBJECT_DIGEST",
        },
        {
            "fixture_id": "TDD-LANDING-WRONG-CANDIDATE",
            "mutation": "WRONG_CANDIDATE",
            "expected_error": "TDD_LANDING_CANDIDATE",
        },
        {
            "fixture_id": "TDD-LANDING-PRE-GATE-TIME",
            "mutation": "PRE_GATE_TIME",
            "expected_error": "TDD_LANDING_PRE_GATE_TIME",
        },
        {
            "fixture_id": "TDD-LANDING-LEGACY-LANDED-STATUS",
            "mutation": "LEGACY_LANDED_STATUS",
            "expected_error": "TDD_LANDING_STATUS",
        },
        {
            "fixture_id": "TDD-LANDING-NULL-STATUS",
            "mutation": "NULL_STATUS",
            "expected_error": "TDD_LANDING_STATUS",
        },
        {
            "fixture_id": "TDD-LANDING-UNKNOWN-STATUS",
            "mutation": "UNKNOWN_STATUS",
            "expected_error": "TDD_LANDING_STATUS",
        },
        {
            "fixture_id": "TDD-LANDING-NONTERMINAL-STATUS",
            "mutation": "NONTERMINAL_STATUS",
            "expected_error": "TDD_LANDING_STATUS",
        },
    ]
    landing_candidate_cases = [
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-VALID",
            "mutation": "NONE",
            "expected_result": "RESOLVED",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-MISSING",
            "mutation": "MISSING_ROW",
            "expected_error": "TDD_SUBJECT_REGISTRY_MISSING",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-DUPLICATE",
            "mutation": "DUPLICATE_ROW",
            "expected_error": "TDD_SUBJECT_REGISTRY_DUPLICATE",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-MISMATCH",
            "mutation": "REGISTRY_CANDIDATE_MISMATCH",
            "expected_error": "TDD_SUBJECT_REGISTRY_BINDING",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-WRONG-TREE",
            "mutation": "WRONG_TREE",
            "expected_error": "TDD_LANDING_CANDIDATE",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-WRONG-ARTIFACT",
            "mutation": "WRONG_ARTIFACT",
            "expected_error": "TDD_LANDING_CANDIDATE",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-WRONG-PROFILE",
            "mutation": "WRONG_PROFILE",
            "expected_error": "TDD_LANDING_CANDIDATE",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-STALE",
            "mutation": "STALE",
            "expected_error": "TDD_LANDING_CANDIDATE",
        },
        {
            "fixture_id": "TDD-CANDIDATE-RESOLVER-ALTERNATE-COMMIT",
            "mutation": "COHERENT_ALTERNATE_COMMIT",
            "expected_result": "RESOLVED",
        },
    ]
    cycle_semantic_cases = [
        {
            "fixture_id": "TDD-CYCLE-GATED-GATE-AFTER-GATED",
            "mutation": "GATE_AFTER_GATED_AT",
            "expected_error": "TDD_CYCLE_GATE_CHRONOLOGY",
        },
        {
            "fixture_id": "TDD-CYCLE-GATED-AFTER-RECORDED",
            "mutation": "GATED_AFTER_RECORDED_AT",
            "expected_error": "TDD_CYCLE_GATE_CHRONOLOGY",
        },
        *[
            {
                "fixture_id": (
                    "TDD-CYCLE-PROPOSED-NONNULL-"
                    + field_name.upper()
                ),
                "mutation": "PROPOSED_NONNULL_FIELD",
                "field": field_name,
                "expected_error": "TDD_CYCLE_PROPOSED_NULL_STATE",
            }
            for field_name in [
                "evidence_snapshot_ref",
                "cycle_gate_evaluation_ref",
                "gated_at",
            ]
        ],
        {
            "fixture_id": "TDD-CYCLE-REJECTED-NONNULL-GATED",
            "mutation": "REJECTED_NONNULL_GATED_AT",
            "expected_error": "TDD_CYCLE_REJECTED_NULL_STATE",
        },
    ]
    journal_cases = [
        {
            "fixture_id": "TDD-JOURNAL-MISSING-EVENT",
            "mutation": "MISSING_EVENT",
            "expected_error": "TDD_JOURNAL_SEQUENCE_POPULATION",
        },
        {
            "fixture_id": "TDD-JOURNAL-EXTRA-EVENT",
            "mutation": "EXTRA_EVENT",
            "expected_error": "TDD_JOURNAL_SEQUENCE_POPULATION",
        },
        {
            "fixture_id": "TDD-JOURNAL-REUSED-ACTIVITY",
            "mutation": "REUSED_ACTIVITY",
            "expected_error": "TDD_JOURNAL_ACTIVITY_POPULATION",
        },
        {
            "fixture_id": "TDD-JOURNAL-CURSOR-GAP",
            "mutation": "CURSOR_GAP",
            "expected_error": "TDD_JOURNAL_SEQUENCE_POPULATION",
        },
        {
            "fixture_id": "TDD-JOURNAL-WRONG-RUN",
            "mutation": "WRONG_RUN",
            "expected_error": "TDD_JOURNAL_RUN_BINDING",
        },
        {
            "fixture_id": "TDD-JOURNAL-WRONG-CAUSAL-ORDER",
            "mutation": "WRONG_CAUSAL_ORDER",
            "expected_error": "TDD_JOURNAL_CAUSAL_ORDER",
        },
        {
            "fixture_id": "TDD-JOURNAL-PHASE-DIGEST-MISMATCH",
            "mutation": "PHASE_DIGEST_MISMATCH",
            "expected_error": "TDD_JOURNAL_PHASE_DIGEST",
        },
        {
            "fixture_id": "TDD-JOURNAL-SLICE-DIGEST-MISMATCH",
            "mutation": "SLICE_DIGEST_MISMATCH",
            "expected_error": "TDD_JOURNAL_SLICE_DIGEST",
        },
        {
            "fixture_id": "TDD-JOURNAL-POST-HOC-EVIDENCE",
            "mutation": "POST_HOC_EVIDENCE",
            "expected_error": "TDD_JOURNAL_PROHIBITED_FACT",
        },
        {
            "fixture_id": "TDD-JOURNAL-GATE-BEFORE-ARCH-CHECK",
            "mutation": "GATE_BEFORE_ARCH_CHECK",
            "expected_error": "TDD_JOURNAL_GATE_CHRONOLOGY",
        },
    ]
    definition_store_cases = [
        {
            "fixture_id": "TDD-STORE-MISSING-TEST-ROW",
            "mutation": "MISSING_TEST_ROW",
            "expected_error": "TDD_TEST_DENOMINATOR_RESOLUTION",
        },
        {
            "fixture_id": "TDD-STORE-WRONG-TEST-CRITERION",
            "mutation": "WRONG_TEST_CRITERION",
            "expected_error": "TDD_TEST_DENOMINATOR_RESOLUTION",
        },
        {
            "fixture_id": "TDD-STORE-TEST-MANIFEST-BYTES-TAMPER",
            "mutation": "TEST_MANIFEST_BYTES_TAMPER",
            "expected_error": "TDD_TEST_DENOMINATOR_DIGEST",
        },
        {
            "fixture_id": "TDD-STORE-MISSING-FAILURE-ROW",
            "mutation": "MISSING_FAILURE_ROW",
            "expected_error": "TDD_FAILURE_DENOMINATOR_RESOLUTION",
        },
        {
            "fixture_id": "TDD-STORE-DUPLICATE-FAILURE-ROW",
            "mutation": "DUPLICATE_FAILURE_ROW",
            "expected_error": "TDD_FAILURE_DENOMINATOR_RESOLUTION",
        },
        {
            "fixture_id": "TDD-STORE-WRONG-FAILURE-ROW-DIGEST",
            "mutation": "WRONG_FAILURE_ROW_DIGEST",
            "expected_error": "TDD_FAILURE_DENOMINATOR_ROW",
        },
        *[
            {
                "fixture_id": "TDD-STORE-" + mutation,
                "mutation": mutation,
                "expected_error": "TDD_RED_MATCHER_RESOLUTION",
            }
            for mutation in (
                "MATCHER_BYTES_TAMPER",
                "WRONG_MATCHER_SCHEMA",
                "WRONG_MATCHER_REF",
                "WRONG_MATCHER_DIGEST",
            )
        ],
        *[
            {
                "fixture_id": "TDD-STORE-" + mutation,
                "mutation": mutation,
                "expected_error": (
                    "TDD_RED_OBSERVED_ASSERTION_FAILURE"
                ),
            }
            for mutation in (
                "RAW_HARNESS_FAILURE",
                "RAW_ERROR",
                "RAW_TIMEOUT",
                "RAW_CANCELLATION",
                "RAW_WRONG_STABLE_TEST",
                "RAW_WRONG_CRITERION",
                "RAW_WRONG_FAILURE_CODE",
            )
        ],
        *[
            {
                "fixture_id": "TDD-STORE-" + mutation,
                "mutation": mutation,
                "expected_error": "TDD_ORACLE_SOURCE_RESOLUTION",
            }
            for mutation in (
                "ORACLE_BYTES_TAMPER",
                "WRONG_ORACLE_SCHEMA",
                "WRONG_ORACLE_REF",
                "WRONG_ORACLE_AUTHORITY",
            )
        ],
        {
            "fixture_id": "TDD-STORE-MISSING-REPRO-MANIFEST",
            "mutation": "MISSING_REPRO_MANIFEST",
            "expected_error": "TDD_REPRO_MANIFEST_POPULATION",
        },
        {
            "fixture_id": "TDD-STORE-WRONG-REPRO-DIGEST",
            "mutation": "WRONG_REPRO_DIGEST",
            "expected_error": "TDD_REPRO_MANIFEST_DIGEST",
        },
    ]
    subject_transition_cases = [
        {
            "fixture_id": "TDD-SUBJECT-STORE-MISSING-ROW",
            "mutation": "MISSING_SUBJECT_ROW",
            "expected_error": "TDD_SUBJECT_REGISTRY_MISSING",
        },
        {
            "fixture_id": "TDD-SUBJECT-STORE-DUPLICATE-ROW",
            "mutation": "DUPLICATE_SUBJECT_ROW",
            "expected_error": "TDD_SUBJECT_REGISTRY_DUPLICATE",
        },
        {
            "fixture_id": "TDD-SUBJECT-STORE-DOCUMENT-TAMPER",
            "mutation": "DOCUMENT_DIGEST_TAMPER",
            "expected_error": "TDD_SUBJECT_DOCUMENT_BINDING",
        },
        {
            "fixture_id": "TDD-SUBJECT-STORE-SCHEMA-INVALID",
            "mutation": "DOCUMENT_SCHEMA_INVALID",
            "expected_error": "TDD_SUBJECT_DOCUMENT_SCHEMA",
        },
        {
            "fixture_id": "TDD-SUBJECT-STORE-PARENT-SKIP",
            "mutation": "UNBOUND_INTERMEDIATE_WRITE",
            "expected_error": "TDD_SUBJECT_SOURCE_ANCESTRY",
        },
        {
            "fixture_id": "TDD-SUBJECT-STORE-ORPHAN-ROW",
            "mutation": "ORPHAN_SUBJECT_ROW",
            "expected_error": "TDD_SUBJECT_REGISTRY_POPULATION",
        },
    ]
    authority_store_cases = [
        {
            "fixture_id": "TDD-AUTHORITY-STORE-VALID-EMPTY",
            "mutation": "NONE",
            "expected_result": "PASS",
        },
        {
            "fixture_id": "TDD-AUTHORITY-MISSING-EXCEPTION",
            "mutation": "MISSING_APPLICABLE_EXCEPTION",
            "expected_error": "TDD_AUTHORITY_EXCEPTION_POPULATION",
        },
        {
            "fixture_id": "TDD-AUTHORITY-MISSING-QUARANTINE",
            "mutation": "MISSING_APPLICABLE_QUARANTINE",
            "expected_error": "TDD_AUTHORITY_QUARANTINE_POPULATION",
        },
        {
            "fixture_id": "TDD-AUTHORITY-ORPHAN-EXCEPTION",
            "mutation": "ORPHAN_EXCEPTION",
            "expected_error": "TDD_AUTHORITY_EXCEPTION_POPULATION",
        },
        {
            "fixture_id": "TDD-AUTHORITY-ORPHAN-QUARANTINE",
            "mutation": "ORPHAN_QUARANTINE",
            "expected_error": "TDD_AUTHORITY_QUARANTINE_POPULATION",
        },
        {
            "fixture_id": "TDD-AUTHORITY-CROSS-SUBJECT",
            "mutation": "CROSS_SUBJECT_EXCEPTION",
            "expected_error": "TDD_AUTHORITY_RECORD_BINDING",
        },
        {
            "fixture_id": "TDD-AUTHORITY-STALE",
            "mutation": "STALE_QUARANTINE",
            "expected_error": "TDD_AUTHORITY_RECORD_BINDING",
        },
    ]
    rule_coverage_cases = [
        {
            "fixture_id": "TDD-RULE-OMITTED",
            "mutation": "OMITTED_RULE",
            "expected_error": "TDD_RULE_COVERAGE_PARTITION",
        },
        {
            "fixture_id": "TDD-RULE-DUPLICATE",
            "mutation": "DUPLICATE_RULE",
            "expected_error": "TDD_RULE_COVERAGE_PARTITION",
        },
        {
            "fixture_id": "TDD-RULE-UNKNOWN-EXTRA",
            "mutation": "UNKNOWN_EXTRA_RULE",
            "expected_error": "TDD_RULE_COVERAGE_PARTITION",
        },
        *[
            {
                "fixture_id": "TDD-RULE-" + mutation,
                "mutation": mutation,
                "expected_error": (
                    "TDD_RULE_COVERAGE_REGISTRY_BINDING"
                ),
            }
            for mutation in (
                "WRONG_REGISTRY_ID",
                "WRONG_REGISTRY_VERSION",
                "WRONG_REGISTRY_DIGEST",
            )
        ],
        {
            "fixture_id": "TDD-RULE-WRONG-COVERAGE-MANIFEST",
            "mutation": "WRONG_COVERAGE_MANIFEST",
            "expected_error": "TDD_RULE_COVERAGE_MANIFEST",
        },
        {
            "fixture_id": "TDD-RULE-OVERLAP",
            "mutation": "OVERLAP_APPLICABLE_NA",
            "expected_error": "TDD_RULE_COVERAGE_PARTITION",
        },
        {
            "fixture_id": "TDD-RULE-CHECKER-UNCOVERED",
            "mutation": "ARCH_CHECK_UNCOVERED",
            "expected_error": (
                "TDD_ARCHITECTURE_RULE_RESULT_POPULATION"
            ),
        },
        {
            "fixture_id": "TDD-RULE-RESULT-MISSING",
            "mutation": "ARCH_RESULT_MISSING",
            "expected_error": (
                "TDD_ARCHITECTURE_RULE_RESULT_POPULATION"
            ),
        },
        {
            "fixture_id": "TDD-RULE-RESULT-FAILED",
            "mutation": "ARCH_RESULT_FAILED",
            "expected_error": (
                "TDD_ARCHITECTURE_RULE_RESULT_POPULATION"
            ),
        },
    ]
    built_artifact_cases = [
        {
            "fixture_id": "TDD-BUILD-MISSING-DIGEST",
            "mutation": "MISSING_BUILT_DIGEST",
            "expected_error": "TDD_BUILT_ARTIFACT_EVIDENCE_REQUIRED",
        },
        {
            "fixture_id": "TDD-BUILD-MISSING-REFERENCE",
            "mutation": "MISSING_BUILT_REFERENCE",
            "expected_error": "TDD_BUILT_ARTIFACT_EVIDENCE_REQUIRED",
        },
        *[
            {
                "fixture_id": "TDD-BUILD-" + mutation,
                "mutation": mutation,
                "expected_error": "TYPED_ARTIFACT_SUBJECT_MISMATCH",
            }
            for mutation in (
                "WRONG_CLAIM_SCHEMA",
                "WRONG_CLAIM_REF",
                "WRONG_CLAIM_DIGEST",
            )
        ],
        *[
            {
                "fixture_id": "TDD-BUILD-" + mutation,
                "mutation": mutation,
                "expected_error": (
                    "TDD_BUILT_ARTIFACT_CHECKER_BINDING"
                ),
            }
            for mutation in (
                "WRONG_BASE_COMMIT",
                "WRONG_CANDIDATE_COMMIT",
                "WRONG_ARTIFACT_DIGEST",
                "WRONG_TEST_PROFILE_ID",
                "WRONG_TEST_PROFILE_VERSION",
                "WRONG_TEST_PROFILE_DIGEST",
                "FAILED_CHECKER",
                "WRONG_ROLE_COVERAGE",
            )
        ],
    ]
    red_fingerprint_cases = [
        *[
            {
                "fixture_id": (
                    "TDD-RED-FINGERPRINT-OMIT-" + field_name.upper()
                ),
                "mutation": "OMIT_RED_FINGERPRINT_FIELD",
                "field": field_name,
                "expected_error": "TDD_RED_FINGERPRINT_BINDING",
            }
            for field_name in fingerprint_schema["required"]
        ],
        *[
            {
                "fixture_id": (
                    "TDD-RED-FINGERPRINT-FORGE-" + field_name.upper()
                ),
                "mutation": "FORGE_RED_FINGERPRINT_FIELD",
                "field": field_name,
                "expected_error": "TDD_RED_FINGERPRINT_BINDING",
            }
            for field_name in fingerprint_schema["required"]
        ],
        *[
            {
                "fixture_id": (
                    "TDD-RED-FINGERPRINT-INJECT-" + step_kind
                ),
                "mutation": "INJECT_NON_RED_FINGERPRINT",
                "step_kind": step_kind,
                "expected_error": "TDD_RED_FINGERPRINT_BINDING",
            }
            for step_kind in (
                "GREEN",
                "REFACTOR",
                "ARCHITECTURE_CHECK",
            )
        ],
    ]
    na_cycle = copy.deepcopy(cycle)
    na_rule_id = rule_ids[-1]
    na_cycle["architecture_rule_coverage"][
        "applicable_rule_ids"
    ] = rule_ids[:-1]
    na_cycle["architecture_rule_coverage"][
        "not_applicable_rule_ids"
    ] = [na_rule_id]
    na_coverage_rows = [
        {
            "rule_id": rule_id,
            "disposition": (
                "NOT_APPLICABLE"
                if rule_id == na_rule_id
                else "APPLICABLE"
            ),
        }
        for rule_id in rule_ids
    ]
    na_cycle["architecture_rule_coverage"][
        "coverage_manifest_digest"
    ] = "sha256:" + sha256_bytes(canonical_bytes(na_coverage_rows))
    na_cycle.update(
        {
            "evidence_snapshot_ref": None,
            "cycle_gate_evaluation_ref": None,
            "gated_at": None,
            "result": "UNKNOWN",
            "status": "PROPOSED",
        }
    )
    na_subject = project_tdd_record_subject(
        na_cycle,
        cycle_projection,
        projection_contract,
    )
    na_subject_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(na_subject))
    )
    na_cycle["exact_subject_ref"] = na_subject["subject_ref"]
    na_cycle["exact_subject_digest"] = na_subject_digest
    review_schema = load_json_strict(
        SCHEMAS / "review" / "review-verdict-v1.schema.json"
    )
    na_proof_artifact = closed_schema_fixture_value(
        review_schema,
        "tdd-rule-na-proof",
    )
    na_proof_id = "VERDICT-TDD-RULE-NA-001"
    na_proof_artifact.update(
        {
            "verdict_id": na_proof_id,
            "review_request_id": "REVIEW-TDD-RULE-NA-001",
            "observation_ids": [],
            "independence_evaluation_id": (
                "INDEPENDENCE-TDD-RULE-NA-001"
            ),
            "subject_schema": na_subject["subject_schema"],
            "subject_ref": na_subject["subject_ref"],
            "subject_digest": na_subject_digest,
            "subject_manifest_digest": None,
            "core_sdlc_trace_ref": "TRACE-TDD-TRACER-NA-001",
            "verdict": "ACCEPTABLE",
            "open_finding_refs": [],
            "resolved_finding_refs": [],
            "reconciliation_refs": [],
            "evidence_refs": [na_rule_id],
            "limitations": [],
            "producer_service_id": "REVIEW-SERVICE",
            "produced_at": "2026-07-28T00:08:45Z",
            "digest": "",
        }
    )
    na_proof_artifact["digest"] = digest_value(na_proof_artifact)
    na_cycle["architecture_rule_not_applicable_proofs"] = [
        {
            "rule_id": na_rule_id,
            "proof_ref": {
                "artifact_type": "review_verdict",
                "artifact_ref": na_proof_id,
                "artifact_digest": na_proof_artifact["digest"],
            },
        }
    ]
    return {
        "fixture_suite": (
            "ADR0008_SYNTHETIC_DEFINITION_CONTRACT_SATISFIABILITY"
        ),
        "evidence_scope": (
            "CONTRACT_SATISFIABILITY_FIXTURE_ONLY"
        ),
        "runtime_claim": "NOT_ASSESSED",
        "satisfies_exit_criterion_4": False,
        "catalog_id": catalog["catalog_id"],
        "projection_contract_id": projection_contract["contract_id"],
        "checker_contract_id": catalog[
            "checker_result_dual_subject_contract"
        ]["contract_id"],
        "record_schema_samples": schema_samples,
        "projection_samples": projection_samples,
        "projection_field_order_cases": (
            projection_field_order_cases
        ),
        "subject_registry": subject_registry,
        "subject_transition_cases": subject_transition_cases,
        "definition_stores": definition_stores,
        "definition_store_cases": definition_store_cases,
        "authority_stores": authority_stores,
        "authority_store_cases": authority_store_cases,
        "journal_fixture": journal_fixture,
        "journal_cases": journal_cases,
        "architecture_rule_results": architecture_rule_results,
        "rule_coverage_cases": rule_coverage_cases,
        "built_artifact_cases": built_artifact_cases,
        "red_fingerprint_cases": red_fingerprint_cases,
        "artifacts": artifacts,
        "cycle_subject": cycle_subject,
        "landing_record": landing,
        "landing_candidate_tuple": landing_candidate_tuple,
        "landing_candidate_cases": landing_candidate_cases,
        "landing_freshness_status": "CURRENT",
        "profile_cases": profile_cases,
        "landing_cases": landing_cases,
        "cycle_semantic_cases": cycle_semantic_cases,
        "not_applicable_rule_case": {
            "cycle": na_cycle,
            "cycle_subject": na_subject,
            "proof_artifacts": {
                na_proof_id: na_proof_artifact,
            },
            "negative_mutations": [
                {
                    "mutation": "MISSING_PROOF",
                    "expected_error": (
                        "TDD_RULE_COVERAGE_PROOF_POPULATION"
                    ),
                },
                {
                    "mutation": "STALE_PROOF_DIGEST",
                    "expected_error": (
                        "TYPED_ARTIFACT_DIGEST_MISMATCH"
                    ),
                },
                {
                    "mutation": "WRONG_PROOF_SUBJECT",
                    "expected_error": (
                        "TYPED_ARTIFACT_SUBJECT_MISMATCH"
                    ),
                },
                {
                    "mutation": "WRONG_PROOF_RULE",
                    "expected_error": (
                        "TDD_RULE_COVERAGE_PROOF_POPULATION"
                    ),
                },
            ],
        },
        "checker_role_ids": [
            row["role_id"]
            for row in catalog[
                "checker_result_dual_subject_contract"
            ]["role_predicates"]
        ],
        "reference_role_count": len(
            catalog["reference_subject_roles"]
        ),
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
                    "minItems": 10,
                    "maxItems": 10,
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
            "tdd_cycle_ids": {
                "type": "array",
                "items": nonempty,
                "uniqueItems": True,
            },
            "tdd_exception_ids": {
                "type": "array",
                "items": nonempty,
                "uniqueItems": True,
            },
            "quarantine_ids": {
                "type": "array",
                "items": nonempty,
                "uniqueItems": True,
            },
            "obsolete_test_deletion_ids": {
                "type": "array",
                "items": nonempty,
                "uniqueItems": True,
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
            "tdd_cycle_ids",
            "tdd_exception_ids",
            "quarantine_ids",
            "obsolete_test_deletion_ids",
            "unit_lane_policy",
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
                "pattern": "^(ORG|TDD|ARCH|ARCH9|LEGACYTEST)-[A-Z0-9-]+$",
            },
            "rule_family": {"enum": ["ORG", "TDD", "ADR9", "ADR10"]},
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


def architecture_element_assessment_schema() -> dict[str, Any]:
    digest = {"type": "string", "pattern": "^sha256:[0-9a-f]{64}$"}
    nonempty = {"type": "string", "minLength": 1}
    string_array = {
        "type": "array",
        "items": nonempty,
        "uniqueItems": True,
    }
    nullable_nonempty = {"type": ["string", "null"], "minLength": 1}
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/common/"
            "architecture-element-assessment-v1.schema.json"
        ),
        "title": "Ranex per-element architecture assessment",
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "architecture-element-assessment/v1"
            },
            "assessment_id": nonempty,
            "element_id": nonempty,
            "element_kind": nonempty,
            "element_name": nonempty,
            "owner_contexts": {
                **string_array,
                "minItems": 1,
            },
            "element_definition_digest": digest,
            "definition_contract_ref": nonempty,
            "definition_contract_digest": digest,
            "definition_source_path": nonempty,
            "definition_source_digest": digest,
            "parent_element_refs": string_array,
            "parent_definition_bindings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "element_id": nonempty,
                        "definition_digest": digest,
                    },
                    "required": [
                        "element_id",
                        "definition_digest",
                    ],
                    "additionalProperties": False,
                },
                "uniqueItems": True,
            },
            "parent_definition_manifest_digest": digest,
            "resolved_element_definition_digest": digest,
            "exact_subject_ref": nonempty,
            "exact_subject_digest": digest,
            "definition_status": {
                "enum": ["DEFINED", "DEFINED_NAME_ONLY"]
            },
            "design_assessment_status": {
                "enum": ["DEFINED", "UNKNOWN"]
            },
            "design_evidence_refs": {
                **string_array,
                "minItems": 1,
            },
            "design_blocking_unknown": {"type": "boolean"},
            "practice_disposition": {
                "enum": [
                    "DIRECT",
                    "INHERITED_FROM_PROFILE",
                    "INHERITED_FROM_RULE",
                    "INHERITED_FROM_OWNER",
                    "NOT_APPLICABLE",
                    "UNKNOWN",
                ]
            },
            "disposition_rule_id": nonempty,
            "direct_practice_ids": string_array,
            "inherited_profile_refs": string_array,
            "inheritance_rule_refs": string_array,
            "owner_context_refs": string_array,
            "inheritance_depth": {
                "type": "integer",
                "minimum": 0,
                "maximum": 2,
            },
            "claim_scope": {
                "enum": [
                    "ELEMENT_SPECIFIC_DESIGN_APPLICATION",
                    "GOVERNANCE_APPLICABILITY_ONLY",
                    "NOT_APPLICABLE",
                    "UNKNOWN_BLOCKING",
                ]
            },
            "not_applicable_rule_id": nullable_nonempty,
            "not_applicable_reason": nullable_nonempty,
            "not_applicable_evidence_refs": string_array,
            "not_applicable_approval_ref": nullable_nonempty,
            "practice_unknown_reason": nullable_nonempty,
            "applicable_control_refs": string_array,
            "applicable_rule_refs": string_array,
            "applicability_resolution": {
                "enum": [
                    "EXACT_MATCH",
                    "NO_ELEMENT_SPECIFIC_CONTROL",
                ]
            },
            "runtime_result": {"const": "NOT_ASSESSED"},
            "runtime_subject_ref": {"type": "null"},
            "runtime_subject_digest": {"type": "null"},
            "runtime_evidence_refs": {
                "type": "array",
                "maxItems": 0,
            },
            "observed_at": {"type": "null"},
            "expires_at": {"type": "null"},
            "freshness_status": {"const": "NOT_ASSESSED"},
            "numeric_score": {"type": "null"},
            "noncompensating": {"const": True},
            "pass_authority": {"const": False},
            "digest": digest,
        },
        "required": [
            "schema_version",
            "assessment_id",
            "element_id",
            "element_kind",
            "element_name",
            "owner_contexts",
            "element_definition_digest",
            "definition_contract_ref",
            "definition_contract_digest",
            "definition_source_path",
            "definition_source_digest",
            "parent_element_refs",
            "parent_definition_bindings",
            "parent_definition_manifest_digest",
            "resolved_element_definition_digest",
            "exact_subject_ref",
            "exact_subject_digest",
            "definition_status",
            "design_assessment_status",
            "design_evidence_refs",
            "design_blocking_unknown",
            "practice_disposition",
            "disposition_rule_id",
            "direct_practice_ids",
            "inherited_profile_refs",
            "inheritance_rule_refs",
            "owner_context_refs",
            "inheritance_depth",
            "claim_scope",
            "not_applicable_rule_id",
            "not_applicable_reason",
            "not_applicable_evidence_refs",
            "not_applicable_approval_ref",
            "practice_unknown_reason",
            "applicable_control_refs",
            "applicable_rule_refs",
            "applicability_resolution",
            "runtime_result",
            "runtime_subject_ref",
            "runtime_subject_digest",
            "runtime_evidence_refs",
            "observed_at",
            "expires_at",
            "freshness_status",
            "numeric_score",
            "noncompensating",
            "pass_authority",
            "digest",
        ],
        "allOf": [
            {
                "if": {
                    "properties": {
                        "practice_disposition": {"const": "DIRECT"}
                    },
                    "required": ["practice_disposition"],
                },
                "then": {
                    "properties": {
                        "direct_practice_ids": {"minItems": 1},
                        "inherited_profile_refs": {"maxItems": 0},
                        "inheritance_rule_refs": {"maxItems": 0},
                        "owner_context_refs": {"maxItems": 0},
                        "inheritance_depth": {"const": 0},
                        "claim_scope": {
                            "const": (
                                "ELEMENT_SPECIFIC_DESIGN_APPLICATION"
                            )
                        },
                        "not_applicable_rule_id": {"type": "null"},
                        "not_applicable_reason": {"type": "null"},
                        "not_applicable_evidence_refs": {
                            "maxItems": 0
                        },
                        "not_applicable_approval_ref": {"type": "null"},
                        "practice_unknown_reason": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "practice_disposition": {
                            "const": "INHERITED_FROM_PROFILE"
                        }
                    },
                    "required": ["practice_disposition"],
                },
                "then": {
                    "properties": {
                        "direct_practice_ids": {"maxItems": 0},
                        "inherited_profile_refs": {"minItems": 1},
                        "inheritance_rule_refs": {"maxItems": 0},
                        "owner_context_refs": {"maxItems": 0},
                        "inheritance_depth": {"const": 1},
                        "claim_scope": {
                            "const": "GOVERNANCE_APPLICABILITY_ONLY"
                        },
                        "not_applicable_rule_id": {"type": "null"},
                        "not_applicable_reason": {"type": "null"},
                        "not_applicable_evidence_refs": {
                            "maxItems": 0
                        },
                        "not_applicable_approval_ref": {"type": "null"},
                        "practice_unknown_reason": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "practice_disposition": {
                            "const": "INHERITED_FROM_RULE"
                        }
                    },
                    "required": ["practice_disposition"],
                },
                "then": {
                    "properties": {
                        "direct_practice_ids": {"maxItems": 0},
                        "inherited_profile_refs": {"maxItems": 0},
                        "inheritance_rule_refs": {"minItems": 1},
                        "owner_context_refs": {"maxItems": 0},
                        "inheritance_depth": {
                            "minimum": 1,
                            "maximum": 2,
                        },
                        "claim_scope": {
                            "const": "GOVERNANCE_APPLICABILITY_ONLY"
                        },
                        "not_applicable_rule_id": {"type": "null"},
                        "not_applicable_reason": {"type": "null"},
                        "not_applicable_evidence_refs": {
                            "maxItems": 0
                        },
                        "not_applicable_approval_ref": {"type": "null"},
                        "practice_unknown_reason": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "practice_disposition": {
                            "const": "INHERITED_FROM_OWNER"
                        }
                    },
                    "required": ["practice_disposition"],
                },
                "then": {
                    "properties": {
                        "direct_practice_ids": {"maxItems": 0},
                        "inherited_profile_refs": {"maxItems": 0},
                        "inheritance_rule_refs": {"maxItems": 0},
                        "owner_context_refs": {"minItems": 1},
                        "inheritance_depth": {"const": 1},
                        "claim_scope": {
                            "const": "GOVERNANCE_APPLICABILITY_ONLY"
                        },
                        "not_applicable_rule_id": {"type": "null"},
                        "not_applicable_reason": {"type": "null"},
                        "not_applicable_evidence_refs": {
                            "maxItems": 0
                        },
                        "not_applicable_approval_ref": {"type": "null"},
                        "practice_unknown_reason": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "practice_disposition": {
                            "const": "NOT_APPLICABLE"
                        }
                    },
                    "required": ["practice_disposition"],
                },
                "then": {
                    "properties": {
                        "direct_practice_ids": {"maxItems": 0},
                        "inherited_profile_refs": {"maxItems": 0},
                        "inheritance_rule_refs": {"maxItems": 0},
                        "owner_context_refs": {"maxItems": 0},
                        "inheritance_depth": {"const": 0},
                        "claim_scope": {"const": "NOT_APPLICABLE"},
                        "not_applicable_rule_id": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "not_applicable_reason": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "not_applicable_evidence_refs": {
                            "minItems": 1
                        },
                        "not_applicable_approval_ref": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "practice_unknown_reason": {"type": "null"},
                    }
                },
            },
            {
                "if": {
                    "properties": {
                        "practice_disposition": {"const": "UNKNOWN"}
                    },
                    "required": ["practice_disposition"],
                },
                "then": {
                    "properties": {
                        "direct_practice_ids": {"maxItems": 0},
                        "inherited_profile_refs": {"maxItems": 0},
                        "inheritance_rule_refs": {"maxItems": 0},
                        "owner_context_refs": {"maxItems": 0},
                        "inheritance_depth": {"const": 0},
                        "claim_scope": {"const": "UNKNOWN_BLOCKING"},
                        "not_applicable_rule_id": {"type": "null"},
                        "not_applicable_reason": {"type": "null"},
                        "not_applicable_evidence_refs": {
                            "maxItems": 0
                        },
                        "not_applicable_approval_ref": {"type": "null"},
                        "practice_unknown_reason": {
                            "type": "string",
                            "minLength": 1,
                        },
                    }
                },
            },
        ],
        "additionalProperties": False,
    }
    return schema


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
            "element_disposition_policy": {
                "type": "object",
                "properties": {
                    "policy_id": {
                        "const": (
                            "RANEX-ELEMENT-PRACTICE-"
                            "DISPOSITION-1.0"
                        )
                    },
                    "allowed_dispositions": {
                        "type": "array",
                        "const": [
                            "DIRECT",
                            "INHERITED_FROM_PROFILE",
                            "INHERITED_FROM_RULE",
                            "INHERITED_FROM_OWNER",
                            "NOT_APPLICABLE",
                            "UNKNOWN",
                        ],
                    },
                    "max_inheritance_depth": {"const": 2},
                    "transitive_union_prohibited": {"const": True},
                    "inherited_element_specific_claim_prohibited": {
                        "const": True
                    },
                    "exactly_one_non_unknown_parent_required": {
                        "const": True
                    },
                    "acyclic": {"const": True},
                    "rules": {
                        "type": "array",
                        "minItems": 16,
                        "maxItems": 16,
                        "items": {
                            "type": "object",
                            "properties": {
                                "rule_id": nonempty,
                                "disposition": {
                                    "enum": [
                                        "DIRECT",
                                        "INHERITED_FROM_PROFILE",
                                        "INHERITED_FROM_RULE",
                                        "INHERITED_FROM_OWNER",
                                        "NOT_APPLICABLE",
                                        "UNKNOWN",
                                    ]
                                },
                                "eligible_kinds": {
                                    **string_array,
                                    "minItems": 1,
                                },
                                "profile_field_or_parent_kind": (
                                    nonempty
                                ),
                                "claim_scope": {
                                    "enum": [
                                        (
                                            "ELEMENT_SPECIFIC_"
                                            "DESIGN_APPLICATION"
                                        ),
                                        (
                                            "GOVERNANCE_"
                                            "APPLICABILITY_ONLY"
                                        ),
                                        "NOT_APPLICABLE",
                                        "UNKNOWN_BLOCKING",
                                    ]
                                },
                            },
                            "required": [
                                "rule_id",
                                "disposition",
                                "eligible_kinds",
                                "profile_field_or_parent_kind",
                                "claim_scope",
                            ],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": [
                    "policy_id",
                    "allowed_dispositions",
                    "max_inheritance_depth",
                    "transitive_union_prohibited",
                    "inherited_element_specific_claim_prohibited",
                    "exactly_one_non_unknown_parent_required",
                    "acyclic",
                    "rules",
                ],
                "additionalProperties": False,
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
            "element_disposition_policy",
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


def legacy_test_layout_policy_schema() -> dict[str, Any]:
    nonempty = {"type": "string", "minLength": 1}
    sha1 = {"type": "string", "pattern": "^[0-9a-f]{40}$"}
    sha256 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    prefixed_sha256 = {
        "type": "string",
        "pattern": "^sha256:[0-9a-f]{64}$",
    }
    test_path = {
        "type": "string",
        "pattern": "^tests(?:/[^/]+)+$",
    }
    safe_record_id = {
        "type": "string",
        "pattern": "^(?!.*\\.\\.)[A-Za-z0-9][A-Za-z0-9._-]*$",
    }
    refs = {
        "type": "array",
        "minItems": 1,
        "uniqueItems": True,
        "items": nonempty,
    }

    row_policy_properties = {
        "allowed_inherited_scope": {"const": "EXACT_BASELINE_FILES_ONLY"},
        "change_exception_scope": {
            "const": "IN_PLACE_CONTENT_ONLY_ON_EXISTING_BASELINE_PATH"
        },
        "legacy_addition_policy": {
            "const": "FAIL_REQUIRES_SUPERSEDING_ADR"
        },
        "move_rename_policy": {
            "const": "CANONICAL_DESTINATION_WITH_MIGRATION_PROOF_ONLY"
        },
        "compatibility_owner": {"const": "compatibility"},
        "migration_owner": {"const": "migration"},
        "test_governance_owner": {"const": "process_assurance"},
        "migration_trigger": {
            "const": "FIRST_PATH_OR_CONTENT_CHANGE_OR_RANEX_DEPENDENCY_TOUCH"
        },
        "expires_at": {"type": "string", "format": "date-time"},
        "removal_proof_profile": {
            "const": "LEGACY_TEST_MIGRATION_PROOF_V2"
        },
    }
    row_policy_required = list(row_policy_properties)
    baseline_file = {
        "type": "object",
        "properties": {
            "path": test_path,
            "mode": {"const": "100644"},
            "git_blob_oid_sha1": sha1,
            "content_sha256": sha256,
        },
        "required": [
            "path",
            "mode",
            "git_blob_oid_sha1",
            "content_sha256",
        ],
        "additionalProperties": False,
    }
    path_content_row = {
        "type": "object",
        "properties": {
            "path": test_path,
            "mode": {"enum": ["100644", "100755"]},
            "content_sha256": sha256,
        },
        "required": ["path", "mode", "content_sha256"],
        "additionalProperties": False,
    }
    rule = {
        "type": "object",
        "properties": {
            "rule_id": {
                "type": "string",
                "pattern": "^LEGACYTEST-[A-Z0-9-]+$",
            },
            "enforcement": {"const": "BLOCKING"},
            "invariant": nonempty,
            "definition_status": {"const": "DEFINED"},
            "runtime_evidence_status": {"const": "NOT_ASSESSED"},
            "source": {
                "const": (
                    "docs/architecture/decisions/"
                    "ADR-0010-bound-inherited-hermes-test-layout-migration.md"
                )
            },
        },
        "required": [
            "rule_id",
            "enforcement",
            "invariant",
            "definition_status",
            "runtime_evidence_status",
            "source",
        ],
        "additionalProperties": False,
    }
    fitness = {
        "type": "object",
        "properties": {
            "fitness_id": {
                "type": "string",
                "pattern": "^FF-LEGACYTEST-[0-9]{3}$",
            },
            "required_evidence": nonempty,
            "result": {"const": "NOT_ASSESSED"},
            "evidence_refs": {
                "type": "array",
                "maxItems": 0,
            },
            "noncompensating": {"const": True},
            "source": {
                "const": (
                    "docs/architecture/decisions/"
                    "ADR-0010-bound-inherited-hermes-test-layout-migration.md"
                )
            },
        },
        "required": [
            "fitness_id",
            "required_evidence",
            "result",
            "evidence_refs",
            "noncompensating",
            "source",
        ],
        "additionalProperties": False,
    }
    change_exception = {
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "legacy-test-change-exception/v2"
            },
            "change_exception_id": safe_record_id,
            "exception_type": {"const": "LEGACY_TEST_CHANGE_EXCEPTION"},
            "policy_id": {"const": "RANEX-LEGACY-TEST-LAYOUT-2.0"},
            "policy_version": {"const": "2.0.0"},
            "baseline_id": {"const": "HERMES-TEST-BASELINE-001"},
            "transition_sequence": {"const": 1},
            "predecessor_transition_id": {
                "const": "HERMES-TEST-BASELINE-001"
            },
            "causation_ref": nonempty,
            "landing_record_ref": {
                "type": "string",
                "pattern": (
                    "^landing_[0-9a-f]{8}-[0-9a-f]{4}-"
                    "7[0-9a-f]{3}-[89ab][0-9a-f]{3}-"
                    "[0-9a-f]{12}$"
                ),
            },
            "before_commit_sha1": sha1,
            "after_commit_sha1": sha1,
            "before_tests_snapshot_digest": prefixed_sha256,
            "after_tests_snapshot_digest": prefixed_sha256,
            "baseline_row": path_content_row,
            "current_row": path_content_row,
            "affected_scope_id": nonempty,
            "rationale": nonempty,
            "compatibility_owner": {"const": "compatibility"},
            "migration_owner": {"const": "migration"},
            "test_governance_owner": {"const": "process_assurance"},
            "independent_migration_reviewer": nonempty,
            "approval_ref": nonempty,
            "expires_at": {"type": "string", "format": "date-time"},
            "canonical_destination": test_path,
            "replacement_plan_ref": nonempty,
            "new_ranex_behavior_forbidden": {"const": True},
            "exact_subject_ref": nonempty,
            "exact_subject_digest": prefixed_sha256,
            "status": {"const": "ACTIVE"},
        },
        "required": [
            "schema_version",
            "change_exception_id",
            "exception_type",
            "policy_id",
            "policy_version",
            "baseline_id",
            "transition_sequence",
            "predecessor_transition_id",
            "causation_ref",
            "landing_record_ref",
            "before_commit_sha1",
            "after_commit_sha1",
            "before_tests_snapshot_digest",
            "after_tests_snapshot_digest",
            "baseline_row",
            "current_row",
            "affected_scope_id",
            "rationale",
            "compatibility_owner",
            "migration_owner",
            "test_governance_owner",
            "independent_migration_reviewer",
            "approval_ref",
            "expires_at",
            "canonical_destination",
            "replacement_plan_ref",
            "new_ranex_behavior_forbidden",
            "exact_subject_ref",
            "exact_subject_digest",
            "status",
        ],
        "additionalProperties": False,
    }
    migration_proof = {
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "legacy-test-migration-record/v2"
            },
            "proof_id": safe_record_id,
            "record_type": {"const": "LEGACY_TEST_MIGRATION_RECORD"},
            "proof_type": {"const": "LEGACY_TEST_MIGRATION_PROOF_V2"},
            "policy_id": {"const": "RANEX-LEGACY-TEST-LAYOUT-2.0"},
            "policy_version": {"const": "2.0.0"},
            "baseline_id": {"const": "HERMES-TEST-BASELINE-001"},
            "transition_sequence": {"type": "integer", "minimum": 1},
            "predecessor_transition_id": nonempty,
            "causation_ref": nonempty,
            "landing_record_ref": {
                "type": "string",
                "pattern": (
                    "^landing_[0-9a-f]{8}-[0-9a-f]{4}-"
                    "7[0-9a-f]{3}-[89ab][0-9a-f]{3}-"
                    "[0-9a-f]{12}$"
                ),
            },
            "before_commit_sha1": sha1,
            "after_commit_sha1": sha1,
            "before_tests_snapshot_digest": prefixed_sha256,
            "after_tests_snapshot_digest": prefixed_sha256,
            "before_disposition_digest": prefixed_sha256,
            "after_disposition_digest": prefixed_sha256,
            "migration_group_id": safe_record_id,
            "group_member_index": {"type": "integer", "minimum": 1},
            "group_member_count": {"type": "integer", "minimum": 1},
            "baseline_source_row": baseline_file,
            "current_source_row": path_content_row,
            "source_state_kind": {
                "enum": [
                    "IMMUTABLE_BASELINE",
                    "AUTHORIZED_CHANGE_EXCEPTION",
                ]
            },
            "source_change_exception_id": {
                "oneOf": [safe_record_id, {"type": "null"}]
            },
            "source_change_exception_source_digest": {
                "oneOf": [prefixed_sha256, {"type": "null"}]
            },
            "source_change_exception_exact_subject_digest": {
                "oneOf": [prefixed_sha256, {"type": "null"}]
            },
            "closes_change_exception_id": {
                "oneOf": [safe_record_id, {"type": "null"}]
            },
            "affected_scope_id": nonempty,
            "disposition": {"enum": ["MIGRATED", "RETIRED"]},
            "destination_rows": {
                "type": "array",
                "uniqueItems": True,
                "items": {
                    "type": "object",
                    "properties": {
                        "path": test_path,
                        "mode": {"enum": ["100644", "100755"]},
                        "content_sha256": sha256,
                        "test_id": nonempty,
                    },
                    "required": [
                        "path",
                        "mode",
                        "content_sha256",
                        "test_id",
                    ],
                    "additionalProperties": False,
                },
            },
            "retirement_rationale": {"type": "string"},
            "behavior_evidence_refs": refs,
            "built_artifact_evidence_refs": refs,
            "adr0008_check_refs": refs,
            "architecture_check_refs": refs,
            "residual_reference_scan_refs": refs,
            "compatibility_owner_acceptance_ref": nonempty,
            "migration_owner_acceptance_ref": nonempty,
            "process_assurance_owner_acceptance_ref": nonempty,
            "independent_migration_review_ref": nonempty,
            "exact_subject_ref": nonempty,
            "exact_subject_digest": prefixed_sha256,
            "result": {"const": "PASS"},
            "status": {"const": "ACCEPTED"},
        },
        "required": [
            "schema_version",
            "proof_id",
            "record_type",
            "proof_type",
            "policy_id",
            "policy_version",
            "baseline_id",
            "transition_sequence",
            "predecessor_transition_id",
            "causation_ref",
            "landing_record_ref",
            "before_commit_sha1",
            "after_commit_sha1",
            "before_tests_snapshot_digest",
            "after_tests_snapshot_digest",
            "before_disposition_digest",
            "after_disposition_digest",
            "migration_group_id",
            "group_member_index",
            "group_member_count",
            "baseline_source_row",
            "current_source_row",
            "source_state_kind",
            "source_change_exception_id",
            "source_change_exception_source_digest",
            "source_change_exception_exact_subject_digest",
            "closes_change_exception_id",
            "affected_scope_id",
            "disposition",
            "destination_rows",
            "retirement_rationale",
            "behavior_evidence_refs",
            "built_artifact_evidence_refs",
            "adr0008_check_refs",
            "architecture_check_refs",
            "residual_reference_scan_refs",
            "compatibility_owner_acceptance_ref",
            "migration_owner_acceptance_ref",
            "process_assurance_owner_acceptance_ref",
            "independent_migration_review_ref",
            "exact_subject_ref",
            "exact_subject_digest",
            "result",
            "status",
        ],
        "allOf": [
            {
                "if": {
                    "properties": {
                        "source_state_kind": {
                            "const": "IMMUTABLE_BASELINE"
                        }
                    },
                    "required": ["source_state_kind"],
                },
                "then": {
                    "properties": {
                        "source_change_exception_id": {
                            "type": "null"
                        },
                        "source_change_exception_source_digest": {
                            "type": "null"
                        },
                        "source_change_exception_exact_subject_digest": {
                            "type": "null"
                        },
                        "closes_change_exception_id": {
                            "type": "null"
                        },
                    }
                },
                "else": {
                    "properties": {
                        "source_change_exception_id": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "source_change_exception_source_digest": (
                            prefixed_sha256
                        ),
                        (
                            "source_change_exception_"
                            "exact_subject_digest"
                        ): prefixed_sha256,
                        "closes_change_exception_id": {
                            "type": "string",
                            "minLength": 1,
                        },
                    }
                },
            },
            {
                "if": {
                    "properties": {"disposition": {"const": "MIGRATED"}},
                    "required": ["disposition"],
                },
                "then": {
                    "properties": {
                        "destination_rows": {"minItems": 1},
                        "retirement_rationale": {"maxLength": 0},
                    }
                },
                "else": {
                    "properties": {
                        "destination_rows": {"maxItems": 0},
                        "retirement_rationale": {"minLength": 1},
                    }
                },
            }
        ],
        "additionalProperties": False,
    }
    cutover_removal_record = {
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "legacy-test-cutover-removal-record/v2"
            },
            "cutover_removal_record_id": {
                "const": "LEGACY-TEST-CUTOVER-001"
            },
            "record_type": {
                "const": "LEGACY_TEST_CUTOVER_REMOVAL_RECORD_V2"
            },
            "policy_id": {"const": "RANEX-LEGACY-TEST-LAYOUT-2.0"},
            "policy_version": {"const": "2.0.0"},
            "baseline_id": {"const": "HERMES-TEST-BASELINE-001"},
            "baseline_file_manifest_sha256": sha256,
            "exact_subject_ref": nonempty,
            "exact_subject_digest": prefixed_sha256,
            "baseline_disposition_count": {"const": 2444},
            "remaining_inherited_file_count": {"const": 0},
            "open_change_exception_count": {"const": 0},
            "resulting_test_snapshot_digest": prefixed_sha256,
            "migration_transition_count": {
                "type": "integer",
                "minimum": 0,
            },
            "ordered_migration_subset_digest": prefixed_sha256,
            "runner_import_configuration_scan_refs": refs,
            "destination_test_evidence_refs": refs,
            "adr0008_gate_evidence_refs": refs,
            "architecture_gate_evidence_refs": refs,
            "compatibility_owner_acceptance_ref": nonempty,
            "migration_owner_acceptance_ref": nonempty,
            "process_assurance_owner_acceptance_ref": nonempty,
            "independent_migration_review_ref": nonempty,
            "recorded_at": {"type": "string", "format": "date-time"},
            "result": {"const": "PASS"},
            "status": {"const": "ACCEPTED"},
        },
        "required": [
            "schema_version",
            "cutover_removal_record_id",
            "record_type",
            "policy_id",
            "policy_version",
            "baseline_id",
            "baseline_file_manifest_sha256",
            "exact_subject_ref",
            "exact_subject_digest",
            "baseline_disposition_count",
            "remaining_inherited_file_count",
            "open_change_exception_count",
            "resulting_test_snapshot_digest",
            "migration_transition_count",
            "ordered_migration_subset_digest",
            "runner_import_configuration_scan_refs",
            "destination_test_evidence_refs",
            "adr0008_gate_evidence_refs",
            "architecture_gate_evidence_refs",
            "compatibility_owner_acceptance_ref",
            "migration_owner_acceptance_ref",
            "process_assurance_owner_acceptance_ref",
            "independent_migration_review_ref",
            "recorded_at",
            "result",
            "status",
        ],
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": (
            "https://schemas.ranex.dev/common/"
            "legacy-test-layout-policy-v2.schema.json"
        ),
        "title": "Ranex bound inherited Hermes test-layout migration policy",
        "type": "object",
        "properties": {
            "schema_version": {"const": "legacy-test-layout-policy/v2"},
            "policy_id": {"const": "RANEX-LEGACY-TEST-LAYOUT-2.0"},
            "version": {"const": "2.0.0"},
            "exception_class": {"const": "LEGACY_TEST_ROOT_EXCEPTION"},
            "baseline": {
                "type": "object",
                "properties": {
                    "baseline_id": {"const": "HERMES-TEST-BASELINE-001"},
                    "source_commit_sha1": sha1,
                    "tests_tree_oid_sha1": sha1,
                    "file_count": {"const": 2444},
                    "mode_counts": {"const": {"100644": 2444}},
                    "ls_tree_command": nonempty,
                    "ls_tree_exact_stdout_sha256": sha256,
                    "file_manifest_serialization": nonempty,
                    "file_manifest_sha256": sha256,
                    "directory_exception_file_count": {"const": 2294},
                    "direct_top_level_file_count": {"const": 134},
                    "inherited_canonical_file_count": {"const": 16},
                    "partition_equation": {"const": "2294 + 134 + 16 = 2444"},
                    "evidence_status": {
                        "const": "BASELINE_BOUND_NOT_MIGRATED"
                    },
                },
                "required": [
                    "baseline_id",
                    "source_commit_sha1",
                    "tests_tree_oid_sha1",
                    "file_count",
                    "mode_counts",
                    "ls_tree_command",
                    "ls_tree_exact_stdout_sha256",
                    "file_manifest_serialization",
                    "file_manifest_sha256",
                    "directory_exception_file_count",
                    "direct_top_level_file_count",
                    "inherited_canonical_file_count",
                    "partition_equation",
                    "evidence_status",
                ],
                "additionalProperties": False,
            },
            "row_policy": {
                "type": "object",
                "properties": row_policy_properties,
                "required": row_policy_required,
                "additionalProperties": False,
            },
            "directory_exceptions": {
                "type": "array",
                "minItems": 29,
                "maxItems": 29,
                "items": {
                    "type": "object",
                    "properties": {
                        "exception_id": {
                            "type": "string",
                            "pattern": "^LEGACY-TEST-ROOT-[0-9]{3}$",
                        },
                        "legacy_root": {
                            "type": "string",
                            "pattern": "^tests/[^/]+$",
                        },
                        "exception_kind": {
                            "enum": [
                                "PATH_AND_SEMANTIC_LAYOUT",
                                "SEMANTIC_LAYOUT_ONLY",
                            ]
                        },
                        "file_count": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "subtree_oid_sha1": sha1,
                        "ls_tree_listing_sha256": sha256,
                        "destination_root": test_path,
                        "row_policy_ref": {"const": "row_policy"},
                        **row_policy_properties,
                        "baseline_files": {
                            "type": "array",
                            "minItems": 1,
                            "items": baseline_file,
                        },
                        "migration_status": {"const": "NOT_MIGRATED"},
                        "runtime_validation_status": {
                            "const": "NOT_ASSESSED"
                        },
                    },
                    "required": [
                        "exception_id",
                        "legacy_root",
                        "exception_kind",
                        "file_count",
                        "subtree_oid_sha1",
                        "ls_tree_listing_sha256",
                        "destination_root",
                        "row_policy_ref",
                        *row_policy_required,
                        "baseline_files",
                        "migration_status",
                        "runtime_validation_status",
                    ],
                    "additionalProperties": False,
                },
            },
            "direct_top_level_exception": {
                "type": "object",
                "properties": {
                    "exception_id": {"const": "LEGACY-TEST-TOPLEVEL-001"},
                    "legacy_root": {"const": "tests/"},
                    "match": {"const": "direct files only"},
                    "file_count": {"const": 134},
                    "ls_tree_listing_sha256": sha256,
                    **row_policy_properties,
                    "destination_rule": nonempty,
                    "baseline_files": {
                        "type": "array",
                        "minItems": 134,
                        "maxItems": 134,
                        "items": baseline_file,
                    },
                    "migration_status": {"const": "NOT_MIGRATED"},
                    "runtime_validation_status": {"const": "NOT_ASSESSED"},
                },
                "required": [
                    "exception_id",
                    "legacy_root",
                    "match",
                    "file_count",
                    "ls_tree_listing_sha256",
                    *row_policy_required,
                    "destination_rule",
                    "baseline_files",
                    "migration_status",
                    "runtime_validation_status",
                ],
                "additionalProperties": False,
            },
            "inherited_canonical_scopes": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": {
                    "type": "object",
                    "properties": {
                        "scope_id": nonempty,
                        "root": {
                            "enum": ["tests/e2e", "tests/integration"]
                        },
                        "file_count": {"type": "integer", "minimum": 1},
                        "subtree_oid_sha1": sha1,
                        "ls_tree_listing_sha256": sha256,
                        "evidence_status": {
                            "const": "INHERITED_BASELINE_NOT_RANEX_PROOF"
                        },
                        "allowed_inherited_scope": {
                            "const": "EXACT_BASELINE_FILES_ONLY"
                        },
                        "baseline_files": {
                            "type": "array",
                            "minItems": 1,
                            "items": baseline_file,
                        },
                        "migration_status": {"const": "NOT_MIGRATED"},
                        "runtime_validation_status": {
                            "const": "NOT_ASSESSED"
                        },
                    },
                    "required": [
                        "scope_id",
                        "root",
                        "file_count",
                        "subtree_oid_sha1",
                        "ls_tree_listing_sha256",
                        "evidence_status",
                        "allowed_inherited_scope",
                        "baseline_files",
                        "migration_status",
                        "runtime_validation_status",
                    ],
                    "additionalProperties": False,
                },
            },
            "change_exception_type": {
                "const": "LEGACY_TEST_CHANGE_EXCEPTION"
            },
            "change_exceptions": {
                "type": "array",
                "items": change_exception,
            },
            "migration_proof_type": {
                "const": "LEGACY_TEST_MIGRATION_PROOF_V2"
            },
            "migration_proofs": {
                "type": "array",
                "items": migration_proof,
            },
            "cutover_removal_record_type": {
                "const": "LEGACY_TEST_CUTOVER_REMOVAL_RECORD_V2"
            },
            "cutover_removal_records": {
                "type": "array",
                "items": cutover_removal_record,
            },
            "rules": {
                "type": "array",
                "minItems": 10,
                "maxItems": 10,
                "items": rule,
            },
            "fitness_obligations": {
                "type": "array",
                "minItems": 9,
                "maxItems": 9,
                "items": fitness,
            },
            "decision_binding": {
                "type": "object",
                "properties": {
                    "decision_id": {"const": "ADR-0010"},
                    "path": {
                        "const": (
                            "docs/architecture/decisions/"
                            "ADR-0010-bound-inherited-hermes-test-layout-migration.md"
                        )
                    },
                    "digest": prefixed_sha256,
                    "status": {"const": "ACCEPTED_PAPER_DECISION"},
                    "runtime_enactment_status": {"const": "NOT_ASSESSED"},
                },
                "required": [
                    "decision_id",
                    "path",
                    "digest",
                    "status",
                    "runtime_enactment_status",
                ],
                "additionalProperties": False,
            },
            "current_status": {
                "enum": [
                    "MIGRATION_EXCEPTION_ACTIVE",
                    "CUTOVER_REMOVAL_RECORD_REGISTERED",
                ]
            },
            "canonical_test_topology_status": {
                "enum": [
                    "NOT_MIGRATED",
                    "CUTOVER_NOT_RUNTIME_VALIDATED",
                ]
            },
            "runtime_validation_status": {"const": "NOT_ASSESSED"},
            "noncompensating": {"const": True},
        },
        "required": [
            "schema_version",
            "policy_id",
            "version",
            "exception_class",
            "baseline",
            "row_policy",
            "directory_exceptions",
            "direct_top_level_exception",
            "inherited_canonical_scopes",
            "change_exception_type",
            "change_exceptions",
            "migration_proof_type",
            "migration_proofs",
            "cutover_removal_record_type",
            "cutover_removal_records",
            "rules",
            "fitness_obligations",
            "decision_binding",
            "current_status",
            "canonical_test_topology_status",
            "runtime_validation_status",
            "noncompensating",
        ],
        "additionalProperties": False,
    }


def adr10_primitive_schema(type_name: str) -> dict[str, Any]:
    if type_name == "ed25519_signature_base64url":
        return {
            "type": "string",
            "pattern": r"^[A-Za-z0-9_-]{86}$",
        }
    if type_name == "git_mode":
        return {"const": "100644"}
    if type_name == "hex_sha256":
        return {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        }
    if type_name == "positive_integer":
        return {"type": "integer", "minimum": 1}
    if type_name == "nonnegative_integer":
        return {"type": "integer", "minimum": 0}
    if type_name == "nonnegative_number":
        return {"type": "number", "minimum": 0}
    return tdd_primitive_schema(type_name)


def adr10_field_schema(
    type_spec: Any,
    nested_rows: dict[str, dict[str, Any]],
    adr8_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(type_spec, dict):
        return tdd_inline_schema(type_spec)
    if not isinstance(type_spec, str):
        raise ValueError("ADR-0010 field type is not closed")
    if type_spec.endswith("|null"):
        return {
            "oneOf": [
                adr10_field_schema(
                    type_spec.removesuffix("|null"),
                    nested_rows,
                    adr8_rows,
                ),
                {"type": "null"},
            ]
        }
    if type_spec.endswith("[]"):
        return {
            "type": "array",
            "items": adr10_field_schema(
                type_spec.removesuffix("[]"),
                nested_rows,
                adr8_rows,
            ),
        }
    if type_spec in nested_rows:
        return adr10_closed_object_schema(
            nested_rows[type_spec],
            nested_rows,
            adr8_rows,
        )
    if type_spec in adr8_rows:
        return tdd_type_schema(
            type_spec,
            "1",
            adr8_rows,
        )
    if type_spec in {"HumanDecisionRecord", "CoreSdlcTrace"}:
        template_name = {
            "HumanDecisionRecord": "HUMAN_DECISION.yaml",
            "CoreSdlcTrace": "CORE_SDLC_TRACE.yaml",
        }[type_spec]
        template = yaml.safe_load(read(TEMPLATES / template_name))
        return infer_schema(
            template,
            "",
            template["artifact_type"],
        )
    return adr10_primitive_schema(type_spec)


def contract_row_invariants(row: dict[str, Any]) -> list[str]:
    plural = row.get("invariants")
    if plural is not None:
        return copy.deepcopy(plural)
    singular = row.get("invariant")
    return [singular] if isinstance(singular, str) and singular else []


def adr10_closed_object_schema(
    row: dict[str, Any],
    nested_rows: dict[str, dict[str, Any]],
    adr8_rows: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    properties = {
        field_name: adr10_field_schema(
            row["field_types"][field_name],
            nested_rows,
            adr8_rows,
        )
        for field_name in row["fields"]
    }
    for field_name, raw_cardinality in row.get(
        "array_cardinalities", {}
    ).items():
        cardinality = raw_cardinality.split(";", 1)[0].strip()
        if cardinality == "0..N":
            properties[field_name]["minItems"] = 0
        elif cardinality == "1..N":
            properties[field_name]["minItems"] = 1
        elif match := re.fullmatch(r"exactly ([1-9][0-9]*)", cardinality):
            properties[field_name]["minItems"] = int(match.group(1))
            properties[field_name]["maxItems"] = int(match.group(1))
        else:
            raise ValueError(
                "ADR-0010 unsupported array cardinality: "
                + raw_cardinality
            )
        properties[field_name]["uniqueItems"] = True
    return {
        "type": "object",
        "properties": properties,
        "required": copy.deepcopy(row["fields"]),
        "additionalProperties": False,
        "x-ranex-type-id": row.get("type_id"),
        "x-ranex-semantic-invariants": contract_row_invariants(row),
    }


def legacy_test_record_schema(
    collection_key: str,
    schema_id: str,
    title: str,
) -> dict[str, Any]:
    record_type_by_collection = {
        "test_behavior_authorities": "TestBehaviorAuthorityV1",
        "direct_source_classification_authorities": (
            "DirectSourceClassificationAuthorityV1"
        ),
        "change_exceptions": "LegacyTestChangeExceptionV2",
        "migration_proofs": "LegacyTestMigrationRecordV2",
        "cutover_removal_records": (
            "LegacyTestCutoverRemovalRecordV2"
        ),
    }
    contract = parse_adr10_legacy_record_contract()
    record_rows = {
        row["type_id"]: row for row in contract["record_catalog"]
    }
    nested_rows = {
        row["type_id"]: row for row in contract["nested_types"]
    }
    adr8_rows = {
        row["type_id"]: row
        for row in parse_tdd_nested_type_catalog()["types"]
    }
    record_type = record_type_by_collection[collection_key]
    item_schema = adr10_closed_object_schema(
        record_rows[record_type],
        nested_rows,
        adr8_rows,
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://schemas.ranex.dev/common/{schema_id}",
        "title": title,
        "x-ranex-source-contract-id": contract["contract_id"],
        **item_schema,
    }


def estimate_commitment_contract_schemas() -> dict[str, dict[str, Any]]:
    contract = parse_estimate_commitment_control()
    nested_rows: dict[str, dict[str, Any]] = {
        row["type_id"]: row for row in contract["nested_types"]
    }
    estimate = contract["estimate_record"]
    source_authority = contract["source_authority_contract"]
    for row in source_authority["record_types"]:
        nested_rows[row["type_id"]] = row
    nested_rows[estimate["type_id"]] = estimate

    publication = source_authority["registry_publication_fields"]
    common_registry = source_authority[
        "common_closed_registry_fields"
    ]
    role_authorities = {
        row["registry_type"]: row
        for row in source_authority["role_authorities"]
    }

    def normalized_registry_row(
        shape: dict[str, Any],
    ) -> dict[str, Any]:
        if set(shape.get("field_types", {})) == set(shape["fields"]):
            return {
                "type_id": shape["type_id"],
                "fields": copy.deepcopy(shape["fields"]),
                "field_types": copy.deepcopy(shape["field_types"]),
                "nullable_fields": copy.deepcopy(
                    shape.get("nullable_fields", [])
                ),
                "array_cardinalities": copy.deepcopy(
                    shape.get("array_cardinalities", {})
                ),
                "invariants": contract_row_invariants(shape),
            }
        field_types = copy.deepcopy(publication["field_types"])
        constants = shape["constants"]
        field_types["schema_version"] = {
            "const": constants["schema_version"]
        }
        field_types["record_type"] = {
            "const": constants["record_type"]
        }
        if "row_type" in shape:
            field_types["rows"] = shape["row_type"] + "[]"
        field_types.update(copy.deepcopy(shape.get("field_types", {})))
        return {
            "type_id": shape["type_id"],
            "fields": copy.deepcopy(shape["fields"]),
            "field_types": {
                field: field_types[field]
                for field in shape["fields"]
            },
            "nullable_fields": copy.deepcopy(
                common_registry["nullable_fields"]
            ),
            "array_cardinalities": (
                {"rows": shape["row_cardinality"]}
                if "row_type" in shape
                else copy.deepcopy(
                    shape.get("array_cardinalities", {})
                )
            ),
            "invariants": [
                common_registry["invariant"],
                *contract_row_invariants(shape),
            ],
        }

    registry_rows: dict[str, dict[str, Any]] = {}
    for shape in source_authority["registry_shapes"]:
        normalized = normalized_registry_row(shape)
        registry_rows[normalized["type_id"]] = normalized
        nested_rows[normalized["type_id"]] = normalized
    replay_shape = normalized_registry_row(
        source_authority["source_trust_registry_shape"]
    )
    registry_rows[replay_shape["type_id"]] = replay_shape
    nested_rows[replay_shape["type_id"]] = replay_shape
    sources_object = source_authority["sources_object"]
    nested_rows[sources_object["type_id"]] = sources_object

    estimate_schema = adr10_closed_object_schema(
        estimate,
        nested_rows,
        {},
    )
    projection = contract["commitment_subject_projection"]
    projection_row = {
        "type_id": projection["projection_id"],
        "fields": projection["output_fields"],
        "field_types": projection["field_types"],
        "nullable_fields": projection["nullable_fields"],
        "array_cardinalities": projection["array_cardinalities"],
        "invariants": projection["invariants"],
    }
    projection_schema = adr10_closed_object_schema(
        projection_row,
        nested_rows,
        {},
    )
    result: dict[str, dict[str, Any]] = {}
    for source_row, schema, title in (
        (
            estimate,
            estimate_schema,
            "Ranex immutable estimate observation",
        ),
        (
            projection,
            projection_schema,
            "Ranex exact delivery commitment subject",
        ),
    ):
        relative_path = source_row["schema_ref"]
        filename = Path(relative_path).name
        result[str(Path(relative_path).relative_to("schemas"))] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://schemas.ranex.dev/planning/" + filename
            ),
            "title": title,
            "x-ranex-source-contract-id": contract["contract_id"],
            "x-ranex-source-control-id": contract["control_id"],
            **schema,
        }

    source_rows: list[tuple[dict[str, Any], str]] = [
        *[
            (row, row["schema_ref"])
            for row in source_authority["record_types"]
        ],
        (
            source_authority["source_envelope"],
            source_authority["source_envelope"]["schema_ref"],
        ),
        *[
            (
                row,
                role_authorities[row["type_id"]]["schema_ref"],
            )
            for row in registry_rows.values()
            if row["type_id"] in role_authorities
        ],
        (
            replay_shape,
            source_authority["source_trust_registry_shape"][
                "schema_ref"
            ],
        ),
    ]
    for source_row, schema_ref in source_rows:
        source_schema = adr10_closed_object_schema(
            source_row,
            nested_rows,
            {},
        )
        relative = str(Path(schema_ref).relative_to("schemas"))
        result[relative] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://schemas.ranex.dev/" + relative,
            "title": source_row["type_id"],
            "x-ranex-source-contract-id": contract["contract_id"],
            "x-ranex-source-control-id": contract["control_id"],
            "x-ranex-source-authority-contract-id": (
                source_authority["source_contract_id"]
            ),
            **source_schema,
        }
    expected_schema_refs = {
        estimate["schema_ref"],
        projection["schema_ref"],
        source_authority["source_envelope"]["schema_ref"],
        source_authority["source_trust_registry_shape"][
            "schema_ref"
        ],
        *[
            row["schema_ref"]
            for row in source_authority["record_types"]
        ],
        *[
            row["schema_ref"]
            for row in source_authority["role_authorities"]
        ],
    }
    actual_schema_refs = {"schemas/" + path for path in result}
    if actual_schema_refs != expected_schema_refs:
        raise ValueError(
            "Estimate/commitment schema projection set drift: "
            + ",".join(
                sorted(actual_schema_refs ^ expected_schema_refs)
            )
        )
    return result


def readiness_scalar_schema(
    type_spec: Any,
    named_types: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if isinstance(type_spec, dict):
        if set(type_spec) == {"const"}:
            return {"const": type_spec["const"]}
        if set(type_spec) == {"enum"}:
            return {"enum": copy.deepcopy(type_spec["enum"])}
        if set(type_spec) == {"enum_ref"}:
            if (
                type_spec["enum_ref"]
                != "ENUM-READINESS-RUNTIME-ASSESSMENT-STATUS-1.0"
            ):
                raise ValueError(
                    "ADR-0012 unknown enum reference: "
                    + type_spec["enum_ref"]
                )
            return {
                "enum": copy.deepcopy(
                    parse_adr12_readiness_contract()[
                        "runtime_assessment_status_contract"
                    ]["values"]
                )
            }
        raise ValueError(
            "ADR-0012 unsupported inline type: " + repr(type_spec)
        )
    if not isinstance(type_spec, str):
        raise ValueError(
            "ADR-0012 non-string field type: " + repr(type_spec)
        )
    if type_spec.endswith("[]"):
        member = type_spec[:-2]
        return {
            "type": "array",
            "items": readiness_scalar_schema(member, named_types),
        }
    if type_spec.endswith("|null"):
        return {
            "oneOf": [
                readiness_scalar_schema(type_spec[:-5], named_types),
                {"type": "null"},
            ]
        }
    if type_spec in named_types:
        return readiness_closed_object_schema(
            named_types[type_spec],
            named_types,
        )
    scalars = {
        "safe_id": {
            "type": "string",
            "minLength": 1,
            "maxLength": 256,
            "pattern": r"^[A-Za-z0-9][A-Za-z0-9._-]*$",
        },
        "safe_ref": {
            "type": "string",
            "minLength": 1,
            "maxLength": 1024,
            "pattern": (
                r"^(?:[A-Za-z0-9][A-Za-z0-9._-]*|"
                r"urn:ranex:[A-Za-z0-9._:-]+)$"
            ),
        },
        "sha1": {
            "type": "string",
            "pattern": r"^[0-9a-f]{40}$",
        },
        "sha256": {
            "type": "string",
            "pattern": r"^sha256:[0-9a-f]{64}$",
        },
        "strict_utc": {
            "type": "string",
            "format": "date-time",
            "pattern": (
                r"^[0-9]{4}-(?:0[1-9]|1[0-2])-"
                r"(?:0[1-9]|[12][0-9]|3[01])T"
                r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:"
                r"[0-5][0-9](?:\.[0-9]+)?Z$"
            ),
        },
        "nonempty_string": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4096,
            "pattern": r".*\S.*",
        },
    }
    if type_spec not in scalars:
        raise ValueError(
            "ADR-0012 unsupported scalar type: " + type_spec
        )
    return copy.deepcopy(scalars[type_spec])


def readiness_closed_object_schema(
    row: dict[str, Any],
    named_types: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    fields = row.get("fields", row.get("output_fields"))
    properties = {
        field: readiness_scalar_schema(
            row["field_types"][field],
            named_types,
        )
        for field in fields
    }
    for field, cardinality in row.get(
        "array_cardinalities", {}
    ).items():
        schema = properties[field]
        if schema.get("type") != "array":
            raise ValueError(
                "ADR-0012 non-array cardinality field: " + field
            )
        if cardinality == "0..N":
            schema["minItems"] = 0
        elif cardinality == "1..N":
            schema["minItems"] = 1
        elif cardinality.startswith("exactly 7 for Tier 1"):
            # Tier-specific cardinality and role order are added below.
            pass
        else:
            raise ValueError(
                "ADR-0012 unsupported array cardinality: "
                + cardinality
            )
        schema["uniqueItems"] = True
    return {
        "type": "object",
        "properties": properties,
        "required": copy.deepcopy(fields),
        "additionalProperties": False,
        "x-ranex-type-id": row.get(
            "type_id",
            row.get("projection_id"),
        ),
        "x-ranex-semantic-invariants": copy.deepcopy(
            row.get("invariants", [])
        ),
    }


def readiness_contract_schemas() -> dict[str, dict[str, Any]]:
    contract = parse_adr12_readiness_contract()
    named_types = {
        row["type_id"]: row for row in contract["nested_types"]
    }
    subject = readiness_closed_object_schema(
        contract["exact_subject_projection"],
        named_types,
    )
    tier1_id = "READINESS-TIER-IMPLEMENTATION-START-001"
    tier2_id = "READINESS-TIER-PRODUCTION-001"
    tier_subject_fields = [
        "tier_evidence_subject_schema",
        "tier_evidence_subject_ref",
        "tier_evidence_subject_digest",
        "tier_evidence_subject_manifest_digest",
    ]
    subject["allOf"] = [
        {
            "if": {
                "properties": {"tier_id": {"const": tier1_id}},
                "required": ["tier_id"],
            },
            "then": {
                "properties": {
                    field: {"type": "null"}
                    for field in tier_subject_fields
                }
            },
        },
        {
            "if": {
                "properties": {"tier_id": {"const": tier2_id}},
                "required": ["tier_id"],
            },
            "then": {
                "properties": {
                    "tier_evidence_subject_schema": (
                        readiness_scalar_schema(
                            "nonempty_string",
                            named_types,
                        )
                    ),
                    "tier_evidence_subject_ref": readiness_scalar_schema(
                        "safe_ref",
                        named_types,
                    ),
                    "tier_evidence_subject_digest": (
                        readiness_scalar_schema(
                            "sha256",
                            named_types,
                        )
                    ),
                }
            },
        },
    ]

    manifest_contract = contract[
        "readiness_subject_manifest_projection"
    ]
    manifest = readiness_closed_object_schema(
        manifest_contract,
        named_types,
    )
    manifest_conditions = []
    for tier_id, roles in manifest_contract[
        "exact_entry_roles_by_tier"
    ].items():
        entry_base = manifest["properties"]["entries"]["items"]
        manifest_conditions.append(
            {
                "if": {
                    "properties": {"tier_id": {"const": tier_id}},
                    "required": ["tier_id"],
                },
                "then": {
                    "properties": {
                        "entries": {
                            "type": "array",
                            "minItems": len(roles),
                            "maxItems": len(roles),
                            "prefixItems": [
                                {
                                    "allOf": [
                                        copy.deepcopy(entry_base),
                                        {
                                            "properties": {
                                                "role": {
                                                    "const": role
                                                }
                                            }
                                        },
                                    ]
                                }
                                for role in roles
                            ],
                            "items": False,
                        }
                    }
                },
            }
        )
    manifest["allOf"] = manifest_conditions

    evidence = readiness_closed_object_schema(
        named_types["ReadinessEvidenceBindingV1"],
        named_types,
    )
    assessment = readiness_closed_object_schema(
        contract["assessment_record"],
        named_types,
    )
    assessment["allOf"] = [
        {
            "if": {
                "properties": {
                    "runtime_assessment_status": {
                        "const": "NOT_ASSESSED"
                    }
                },
                "required": ["runtime_assessment_status"],
            },
            "then": {
                "properties": {
                    "runtime_assessment_ref": {"type": "null"},
                    "runtime_assessment_digest": {"type": "null"},
                }
            },
            "else": {
                "properties": {
                    "runtime_assessment_ref": readiness_scalar_schema(
                        "safe_ref",
                        named_types,
                    ),
                    "runtime_assessment_digest": (
                        readiness_scalar_schema(
                            "sha256",
                            named_types,
                        )
                    ),
                }
            },
        },
        {
            "if": {
                "properties": {"result": {"const": "PASS"}},
                "required": ["result"],
            },
            "then": {
                "properties": {
                    "human_decision_ref": readiness_scalar_schema(
                        "safe_ref",
                        named_types,
                    ),
                    "human_decision_digest": readiness_scalar_schema(
                        "sha256",
                        named_types,
                    ),
                }
            },
        },
        {
            "if": {
                "properties": {"tier_id": {"const": tier2_id}},
                "required": ["tier_id"],
            },
            "then": {
                "properties": {
                    "runtime_assessment_status": {
                        "const": "ASSESSED_PASS"
                    }
                }
            },
        },
    ]
    source_id = contract["contract_id"]
    schemas = {
        "assurance/readiness-subject-v1.schema.json": subject,
        (
            "assurance/readiness-subject-manifest-v1.schema.json"
        ): manifest,
        (
            "assurance/readiness-evidence-binding-v1.schema.json"
        ): evidence,
        "assurance/readiness-assessment-v1.schema.json": assessment,
    }
    titles = {
        "assurance/readiness-subject-v1.schema.json": (
            "Ranex exact readiness subject"
        ),
        "assurance/readiness-subject-manifest-v1.schema.json": (
            "Ranex closed readiness subject manifest"
        ),
        "assurance/readiness-evidence-binding-v1.schema.json": (
            "Ranex readiness native-subject evidence binding"
        ),
        "assurance/readiness-assessment-v1.schema.json": (
            "Ranex immutable readiness assessment"
        ),
    }
    for relative, schema in schemas.items():
        schema.update(
            {
                "$schema": (
                    "https://json-schema.org/draft/2020-12/schema"
                ),
                "$id": "https://schemas.ranex.dev/" + relative,
                "title": titles[relative],
                "x-ranex-source-contract-id": source_id,
                "x-ranex-source-adr": "ADR-0012",
                "x-ranex-runtime-semantics": (
                    "scripts/architecture/validate_contracts.py"
                ),
            }
        )
    return schemas


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
        "tdd_cycle_ids": [],
        "tdd_exception_ids": [],
        "quarantine_ids": [],
        "obsolete_test_deletion_ids": [],
        "unit_lane_policy": {
            "network_forbidden": True,
            "wall_clock_forbidden": True,
            "ambient_randomness_forbidden": True,
            "declared_seed_required": True,
            "injected_clock_required": True,
            "deterministic_id_source_required": True,
        },
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
    legacy_test_layout_policy: dict[str, Any],
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
            decision_binding(LEGACY_TEST_LAYOUT_ADR, "ADR-0010"),
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
                legacy_test_layout_policy,
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
    ] + [
        (
            "ADR10",
            rule,
            legacy_test_layout_policy["decision_binding"]["path"],
        )
        for rule in legacy_test_layout_policy["rules"]
    ]
    entries = []
    rule_family_counts: Counter[str] = Counter()
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
        rule_family_counts[family] += 1
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
        expected_rule_count=len(entries),
        org_rule_count=rule_family_counts["ORG"],
        tdd_rule_count=rule_family_counts["TDD"],
        adr9_rule_count=rule_family_counts["ADR9"],
        adr10_rule_count=rule_family_counts["ADR10"],
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


def build_architecture_element_assessment_registry(
    elements: list[dict[str, Any]],
    architecture_practice_profile: dict[str, Any],
    architecture_practice_profile_digest: str,
    paths_registry: dict[str, Any],
) -> dict[str, Any]:
    disposition_policy = architecture_practice_profile[
        "element_disposition_policy"
    ]
    disposition_rules = {
        rule["rule_id"]: rule for rule in disposition_policy["rules"]
    }
    path_contracts = {
        path["path_id"]: path for path in paths_registry["entries"]
    }
    boundary_fit_by_owner = {
        element["owner_contexts"][0]: element["element_id"]
        for element in elements
        if element["kind"] == "CONTEXT_BOUNDARY_FIT"
    }
    owner_rule_by_kind = {
        "ARTIFACT_TYPE": "ELEM-PRACTICE-OWNER-ARTIFACT-001",
        "CAPABILITY_ZONE": "ELEM-PRACTICE-OWNER-ZONE-001",
        "EFFECT_FAMILY": "ELEM-PRACTICE-OWNER-EFFECT-001",
        "EVENT": "ELEM-PRACTICE-OWNER-EVENT-001",
        "STATE_AXIS": "ELEM-PRACTICE-OWNER-STATE-AXIS-001",
        "STATE_VALUE": "ELEM-PRACTICE-OWNER-STATE-VALUE-001",
    }
    inherited_rule_by_kind = {
        "CONTEXT_DEPENDENCY_EDGE": (
            "ELEM-PRACTICE-RULE-DEPENDENCY-EDGE-001"
        ),
        "FILE_PATTERN": "ELEM-PRACTICE-RULE-FILE-PATTERN-001",
        "PUBLIC_BOUNDARY": "ELEM-PRACTICE-RULE-PUBLIC-BOUNDARY-001",
        "TEST_CATEGORY": "ELEM-PRACTICE-RULE-TEST-CATEGORY-001",
        "TEST_PRACTICE": "ELEM-PRACTICE-RULE-TEST-PRACTICE-001",
    }
    elements_by_id = {
        element["element_id"]: element for element in elements
    }
    if len(elements_by_id) != len(elements):
        raise ValueError("Architecture element ID duplication")
    local_definition_digests: dict[str, str] = {}
    for element in elements:
        definition_subject = {
            key: value
            for key, value in element.items()
            if key
            not in {
                "engineering_practice_profile_id",
                "engineering_practice_profile_digest",
                "engineering_practice_application_status",
                "engineering_practice_applications",
                "runtime_validation_status",
            }
        }
        local_definition_digests[element["element_id"]] = (
            "sha256:"
            + sha256_bytes(canonical_bytes(definition_subject))
        )
        unknown_parents = (
            set(element["parent_element_refs"]) - set(elements_by_id)
        )
        if unknown_parents:
            raise ValueError(
                "Architecture element parent is unknown: "
                + element["element_id"]
                + ":"
                + ",".join(sorted(unknown_parents))
            )
    resolved_definition_digests: dict[str, str] = {}
    parent_definition_bindings_by_id: dict[
        str,
        list[dict[str, str]],
    ] = {}
    parent_manifest_digests: dict[str, str] = {}
    resolving: set[str] = set()

    def resolve_definition_graph(element_id: str) -> str:
        if element_id in resolved_definition_digests:
            return resolved_definition_digests[element_id]
        if element_id in resolving:
            raise ValueError(
                "Architecture element definition parent cycle: "
                + element_id
            )
        resolving.add(element_id)
        element = elements_by_id[element_id]
        bindings = [
            {
                "element_id": parent_id,
                "definition_digest": resolve_definition_graph(parent_id),
            }
            for parent_id in sorted(
                element["parent_element_refs"],
                key=lambda value: value.encode("utf-8"),
            )
        ]
        manifest_digest = (
            "sha256:" + sha256_bytes(canonical_bytes(bindings))
        )
        resolved_digest = (
            "sha256:"
            + sha256_bytes(
                canonical_bytes(
                    {
                        "element_definition_digest": (
                            local_definition_digests[element_id]
                        ),
                        "parent_definition_manifest_digest": (
                            manifest_digest
                        ),
                    }
                )
            )
        )
        parent_definition_bindings_by_id[element_id] = bindings
        parent_manifest_digests[element_id] = manifest_digest
        resolved_definition_digests[element_id] = resolved_digest
        resolving.remove(element_id)
        return resolved_digest

    for element_id in sorted(
        elements_by_id,
        key=lambda value: value.encode("utf-8"),
    ):
        resolve_definition_graph(element_id)
    entries: list[dict[str, Any]] = []
    for element in elements:
        direct_practice_ids = sorted(
            {
                application["practice_id"]
                for application in element[
                    "engineering_practice_applications"
                ]
            }
        )
        inherited_profile_refs: list[str] = []
        inheritance_rule_refs: list[str] = []
        owner_context_refs: list[str] = []
        if direct_practice_ids:
            practice_disposition = "DIRECT"
            disposition_rule_id = "ELEM-PRACTICE-DIRECT-001"
            inheritance_depth = 0
            claim_scope = "ELEMENT_SPECIFIC_DESIGN_APPLICATION"
        elif element["kind"] == "BOUNDED_CONTEXT":
            practice_disposition = "INHERITED_FROM_PROFILE"
            disposition_rule_id = (
                "ELEM-PRACTICE-PROFILE-CONTEXT-FIT-001"
            )
            inherited_profile_refs = [
                boundary_fit_by_owner[element["owner_contexts"][0]]
            ]
            inheritance_depth = 1
            claim_scope = "GOVERNANCE_APPLICABILITY_ONLY"
        elif element["kind"] in {"ADR", "DECISION"}:
            practice_disposition = "INHERITED_FROM_PROFILE"
            disposition_rule_id = (
                "ELEM-PRACTICE-PROFILE-DECISION-GOVERNANCE-001"
            )
            inherited_profile_refs = [
                (
                    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-"
                    "STYLE-AND-ADR"
                )
            ]
            inheritance_depth = 1
            claim_scope = "GOVERNANCE_APPLICABILITY_ONLY"
        elif element["kind"] in inherited_rule_by_kind:
            practice_disposition = "INHERITED_FROM_RULE"
            disposition_rule_id = inherited_rule_by_kind[element["kind"]]
            if element["kind"] == "CONTEXT_DEPENDENCY_EDGE":
                inheritance_rule_refs = [
                    "RANEX-CONTEXT-DEPENDENCIES-1.0"
                ]
                inheritance_depth = 1
            elif element["kind"] == "FILE_PATTERN":
                path_contract = path_contracts[element["element_id"]]
                inheritance_rule_refs = sorted(
                    set(path_contract["topology_rule_ids"])
                    | set(path_contract["tdd_rule_ids"])
                )
                inheritance_depth = 2
            elif element["kind"] == "PUBLIC_BOUNDARY":
                inheritance_rule_refs = [
                    "ORG-PUBLIC-001",
                    "RANEX-CONTEXT-DEPENDENCIES-1.0",
                ]
                inheritance_depth = 1
            elif element["kind"] == "TEST_CATEGORY":
                inheritance_rule_refs = [
                    "RANEX-TDD-1.0",
                    "TDD-LANES-001",
                ]
                inheritance_depth = 1
            else:
                inheritance_rule_refs = ["RANEX-TDD-1.0"]
                inheritance_depth = 1
            claim_scope = "GOVERNANCE_APPLICABILITY_ONLY"
        elif element["kind"] in owner_rule_by_kind:
            practice_disposition = "INHERITED_FROM_OWNER"
            disposition_rule_id = owner_rule_by_kind[element["kind"]]
            owner_context_refs = sorted(set(element["owner_contexts"]))
            inheritance_depth = 1
            claim_scope = "GOVERNANCE_APPLICABILITY_ONLY"
        else:
            practice_disposition = "UNKNOWN"
            disposition_rule_id = (
                "ELEM-PRACTICE-UNKNOWN-BLOCKING-001"
            )
            inheritance_depth = 0
            claim_scope = "UNKNOWN_BLOCKING"
        selected_rule = disposition_rules[disposition_rule_id]
        if (
            selected_rule["disposition"] != practice_disposition
            or element["kind"] not in selected_rule["eligible_kinds"]
            or selected_rule["claim_scope"] != claim_scope
        ):
            raise ValueError(
                "Architecture element disposition rule mismatch: "
                + element["element_id"]
            )
        element_definition_digest = local_definition_digests[
            element["element_id"]
        ]
        parent_definition_bindings = (
            parent_definition_bindings_by_id[element["element_id"]]
        )
        parent_definition_manifest_digest = (
            parent_manifest_digests[element["element_id"]]
        )
        resolved_element_definition_digest = (
            resolved_definition_digests[element["element_id"]]
        )
        applicable_rule_refs: list[str] = []
        if element["kind"] == "FILE_PATTERN":
            path_contract = path_contracts[element["element_id"]]
            applicable_rule_refs = sorted(
                set(path_contract["topology_rule_ids"])
                | set(path_contract["tdd_rule_ids"])
            )
        elif element["kind"] == "PUBLIC_BOUNDARY":
            applicable_rule_refs = ["ORG-PUBLIC-001"]
        elif element["kind"] == "TEST_CATEGORY":
            applicable_rule_refs = ["TDD-LANES-001"]
        elif element["kind"] in {
            "TOPOLOGY_RULE",
            "TEST_PRACTICE",
            "BOUNDARY_FITNESS_RULE",
            "LEGACY_TEST_LAYOUT_RULE",
        }:
            applicable_rule_refs = [element["element_id"]]
        applicability_resolution = (
            "EXACT_MATCH"
            if applicable_rule_refs
            else "NO_ELEMENT_SPECIFIC_CONTROL"
        )
        exact_subject = {
            "kind": "ARCHITECTURE_ELEMENT_DESIGN_SUBJECT_V1",
            "element_id": element["element_id"],
            "element_kind": element["kind"],
            "element_definition_digest": element_definition_digest,
            "definition_contract_ref": element[
                "definition_contract_ref"
            ],
            "definition_contract_digest": element[
                "definition_contract_digest"
            ],
            "definition_source_path": element[
                "definition_source_path"
            ],
            "definition_source_digest": element[
                "definition_source_digest"
            ],
            "parent_element_refs": element["parent_element_refs"],
            "parent_definition_bindings": parent_definition_bindings,
            "parent_definition_manifest_digest": (
                parent_definition_manifest_digest
            ),
            "resolved_element_definition_digest": (
                resolved_element_definition_digest
            ),
            "profile_id": architecture_practice_profile["profile_id"],
            "profile_digest": architecture_practice_profile_digest,
            "disposition_rule_id": disposition_rule_id,
            "practice_disposition": practice_disposition,
            "direct_practice_ids": direct_practice_ids,
            "inherited_profile_refs": inherited_profile_refs,
            "inheritance_rule_refs": inheritance_rule_refs,
            "owner_context_refs": owner_context_refs,
            "inheritance_depth": inheritance_depth,
            "claim_scope": claim_scope,
            "applicable_control_refs": [],
            "applicable_rule_refs": applicable_rule_refs,
            "applicability_resolution": applicability_resolution,
        }
        design_unknown = element["definition_status"] != "DEFINED"
        record = {
            "schema_version": "architecture-element-assessment/v1",
            "assessment_id": (
                "element_assessment_"
                + deterministic_uuid7(element["element_id"])
            ),
            "element_id": element["element_id"],
            "element_kind": element["kind"],
            "element_name": element["name"],
            "owner_contexts": element["owner_contexts"],
            "element_definition_digest": element_definition_digest,
            "definition_contract_ref": element[
                "definition_contract_ref"
            ],
            "definition_contract_digest": element[
                "definition_contract_digest"
            ],
            "definition_source_path": element[
                "definition_source_path"
            ],
            "definition_source_digest": element[
                "definition_source_digest"
            ],
            "parent_element_refs": element["parent_element_refs"],
            "parent_definition_bindings": parent_definition_bindings,
            "parent_definition_manifest_digest": (
                parent_definition_manifest_digest
            ),
            "resolved_element_definition_digest": (
                resolved_element_definition_digest
            ),
            "exact_subject_ref": (
                "architecture-element:" + element["element_id"]
            ),
            "exact_subject_digest": (
                "sha256:" + sha256_bytes(canonical_bytes(exact_subject))
            ),
            "definition_status": element["definition_status"],
            "design_assessment_status": (
                "UNKNOWN" if design_unknown else "DEFINED"
            ),
            "design_evidence_refs": [element["source"]],
            "design_blocking_unknown": design_unknown,
            "practice_disposition": practice_disposition,
            "disposition_rule_id": disposition_rule_id,
            "direct_practice_ids": direct_practice_ids,
            "inherited_profile_refs": inherited_profile_refs,
            "inheritance_rule_refs": inheritance_rule_refs,
            "owner_context_refs": owner_context_refs,
            "inheritance_depth": inheritance_depth,
            "claim_scope": claim_scope,
            "not_applicable_rule_id": None,
            "not_applicable_reason": None,
            "not_applicable_evidence_refs": [],
            "not_applicable_approval_ref": None,
            "practice_unknown_reason": (
                (
                    "No direct or eligible bounded inheritance rule "
                    "resolved this element."
                )
                if practice_disposition == "UNKNOWN"
                else None
            ),
            "applicable_control_refs": [],
            "applicable_rule_refs": applicable_rule_refs,
            "applicability_resolution": applicability_resolution,
            "runtime_result": "NOT_ASSESSED",
            "runtime_subject_ref": None,
            "runtime_subject_digest": None,
            "runtime_evidence_refs": [],
            "observed_at": None,
            "expires_at": None,
            "freshness_status": "NOT_ASSESSED",
            "numeric_score": None,
            "noncompensating": True,
            "pass_authority": False,
            "digest": "",
        }
        record["digest"] = digest_value(record)
        entries.append(record)
    entries.sort(key=lambda item: item["element_id"].encode("utf-8"))
    counts_by_disposition = Counter(
        entry["practice_disposition"] for entry in entries
    )
    allowed_dispositions = [
        "DIRECT",
        "INHERITED_FROM_PROFILE",
        "INHERITED_FROM_RULE",
        "INHERITED_FROM_OWNER",
        "NOT_APPLICABLE",
        "UNKNOWN",
    ]
    expected_counts = {
        key: counts_by_disposition.get(key, 0)
        for key in allowed_dispositions
    }
    if (
        set(counts_by_disposition) - set(allowed_dispositions)
        or sum(expected_counts.values()) != len(entries)
        or expected_counts["NOT_APPLICABLE"] != 0
        or expected_counts["UNKNOWN"] != 0
    ):
        raise ValueError(
            "Architecture element disposition denominator drift: "
            + str(dict(counts_by_disposition))
        )
    return registry(
        "REG-ARCHITECTURE-ELEMENT-ASSESSMENTS-001",
        "1.0.0",
        entries,
        record_schema_path=(
            "schemas/common/"
            "architecture-element-assessment-v1.schema.json"
        ),
        inventory_registry_id="REG-ARCHITECTURE-ELEMENTS-001",
        inventory_element_count=len(entries),
        element_disposition_policy_id=disposition_policy["policy_id"],
        element_disposition_profile_id=(
            architecture_practice_profile["profile_id"]
        ),
        element_disposition_profile_digest=(
            architecture_practice_profile_digest
        ),
        counts_by_disposition=expected_counts,
        noncompensating_summary={
            "derivation": (
                "No arithmetic aggregation. Every inventory element has "
                "one precedence-resolved practice disposition, while "
                "runtime PASS remains unavailable without separate current "
                "exact-subject evidence."
            ),
            "runtime_result": "NOT_ASSESSED",
            "numeric_score": None,
            "pass_authority": False,
            "design_blocking_unknown_element_ids": [
                entry["element_id"]
                for entry in entries
                if entry["design_blocking_unknown"]
            ],
            "runtime_not_assessed_element_ids": [
                entry["element_id"] for entry in entries
            ],
        },
    )


def bind_architecture_element_definitions(
    elements: list[dict[str, Any]],
    registries: dict[str, Any],
) -> None:
    bindings: dict[str, tuple[str, Any, list[str], str]] = {}

    def add(
        element_id: str,
        contract_ref: str,
        definition_row: Any,
        *,
        parents: list[str] | None = None,
        definition_status: str = "DEFINED",
    ) -> None:
        if element_id in bindings:
            raise ValueError(
                "Duplicate architecture element definition binding: "
                + element_id
            )
        bindings[element_id] = (
            contract_ref,
            definition_row,
            sorted(set(parents or [])),
            definition_status,
        )

    contexts_registry = registries["contexts.json"]
    for context in contexts_registry["entries"]:
        context_id = context["context_id"]
        context_element_id = f"CTX-{slug(context_id)}"
        contract_ref = (
            "architecture/contracts/contexts.json#entries/"
            + context_id
        )
        add(
            context_element_id,
            contract_ref,
            context,
            definition_status=context["definition_status"],
        )
        add(
            f"API-{slug(context_id)}",
            contract_ref,
            context,
            parents=[context_element_id],
            definition_status=context["definition_status"],
        )
    for zone in contexts_registry["capability_zones"]:
        add(
            zone["zone_id"],
            (
                "architecture/contracts/contexts.json#capability_zones/"
                + zone["zone_id"]
            ),
            zone,
            parents=[
                f"CTX-{slug(owner)}"
                for owner in zone["owners"]
                if any(
                    context["context_id"] == owner
                    for context in contexts_registry["entries"]
                )
            ],
            definition_status=zone["definition_status"],
        )

    states_registry = registries["states.json"]
    for axis in states_registry["entries"]:
        axis_element_id = f"STATE-AXIS-{slug(axis['axis_id'])}"
        contract_ref = (
            "architecture/contracts/states.json#entries/"
            + axis["axis_id"]
        )
        add(axis_element_id, contract_ref, axis)
        for value in axis["values"]:
            add(
                f"STATE-{slug(axis['axis_id'])}-{value}",
                contract_ref,
                axis,
                parents=[axis_element_id],
            )

    context_ids = {
        context["context_id"]
        for context in contexts_registry["entries"]
    }
    event_enum_bindings = {
        row["enum_name"]: row
        for row in registries["events.json"]["event_enum_bindings"]
    }
    for event in registries["events.json"]["entries"]:
        enum_axis_ids = {
            (
                event_enum_bindings[field["restriction_enum_name"]][
                    "axis_id"
                ]
                if field["restriction_enum_name"] is not None
                else field["type_parameter"]
            )
            for field in event["required_payload_fields"]
            if field["type_kind"] == "Enum"
        }
        add(
            event["event_id"],
            (
                "architecture/contracts/events.json#entries/"
                + event["event_id"]
            ),
            event,
            parents=[
                f"CTX-{slug(event['owner_context'])}",
                *[
                    f"STATE-AXIS-{slug(axis_id)}"
                    for axis_id in sorted(enum_axis_ids)
                ],
            ],
            definition_status=(
                "DEFINED"
                if event["schema_status"] == "DEFINED_CONTRACT"
                else "DEFINED_NAME_ONLY"
            ),
        )
    for effect in registries["effects.json"]["entries"]:
        add(
            effect["effect_family_id"],
            (
                "architecture/contracts/effects.json#entries/"
                + effect["effect_family_id"]
            ),
            effect,
        )
    for path in registries["paths.json"]["entries"]:
        owner = path["owner_context"]
        add(
            path["path_id"],
            (
                "architecture/contracts/paths.json#entries/"
                + path["path_id"]
            ),
            path,
            parents=(
                [f"CTX-{slug(owner)}"] if owner in context_ids else []
            ),
            definition_status=path["definition_status"],
        )
    for rule in registries["topology-rules.json"]["entries"]:
        add(
            rule["rule_id"],
            (
                "architecture/contracts/topology-rules.json#entries/"
                + rule["rule_id"]
            ),
            rule,
            definition_status=rule["definition_status"],
        )

    test_registry = registries["test-practices.json"]
    for practice in test_registry["entries"]:
        add(
            practice["practice_id"],
            (
                "architecture/contracts/test-practices.json#entries/"
                + practice["practice_id"]
            ),
            practice,
            definition_status=practice["definition_status"],
        )
    for category in test_registry["taxonomy"]:
        element_id = f"TEST-CATEGORY-{category['category_id']}"
        add(
            element_id,
            (
                "architecture/contracts/test-practices.json#taxonomy/"
                + category["category_id"]
            ),
            category,
        )

    dependency_registry = registries["context-dependency-edges.json"]
    graph_id = dependency_registry["dependency_graph_id"]
    add(
        graph_id,
        (
            "architecture/contracts/context-dependency-edges.json#"
            + graph_id
        ),
        dependency_registry,
    )
    for edge in dependency_registry["entries"]:
        add(
            edge["edge_id"],
            (
                "architecture/contracts/context-dependency-edges.json#"
                "entries/"
                + edge["edge_id"]
            ),
            edge,
            parents=[
                graph_id,
                f"CTX-{slug(edge['caller'])}",
                f"CTX-{slug(edge['callee'])}",
            ],
            definition_status=edge["definition_status"],
        )

    boundary_registry = registries["context-boundary-fitness.json"]
    boundary_set_id = boundary_registry["boundary_fit_set_id"]
    add(
        boundary_set_id,
        (
            "architecture/contracts/context-boundary-fitness.json#"
            + boundary_set_id
        ),
        boundary_registry,
    )
    for boundary in boundary_registry["entries"]:
        element_id = f"BOUNDARYFIT-{slug(boundary['context_id'])}"
        add(
            element_id,
            (
                "architecture/contracts/context-boundary-fitness.json#"
                "entries/"
                + boundary["context_id"]
            ),
            boundary,
            parents=[
                boundary_set_id,
                f"CTX-{slug(boundary['context_id'])}",
            ],
            definition_status=boundary["definition_status"],
        )
    boundary_rule_set_id = boundary_registry["rule_set_id"]
    add(
        boundary_rule_set_id,
        (
            "architecture/contracts/context-boundary-fitness.json#"
            + boundary_rule_set_id
        ),
        boundary_registry,
    )
    for rule in boundary_registry["rules"]:
        add(
            rule["rule_id"],
            (
                "architecture/contracts/context-boundary-fitness.json#"
                "rules/"
                + rule["rule_id"]
            ),
            rule,
            parents=[boundary_rule_set_id],
            definition_status=rule["definition_status"],
        )
    for fitness in boundary_registry["fitness_obligations"]:
        add(
            fitness["fitness_id"],
            (
                "architecture/contracts/context-boundary-fitness.json#"
                "fitness_obligations/"
                + fitness["fitness_id"]
            ),
            fitness,
            parents=[boundary_rule_set_id],
        )

    coupling_policy = registries["context-coupling-policy.json"]
    coupling_id = coupling_policy["coupling_policy_id"]
    add(
        coupling_id,
        (
            "architecture/contracts/context-coupling-policy.json#"
            + coupling_id
        ),
        coupling_policy,
    )
    for measure in coupling_policy["measures"]:
        add(
            measure["measure_id"],
            (
                "architecture/contracts/context-coupling-policy.json#"
                "measures/"
                + measure["measure_id"]
            ),
            measure,
            parents=[coupling_id],
        )
    feedback_policy = registries["feedback-fitness.json"]
    feedback_id = feedback_policy["feedback_policy_id"]
    add(
        feedback_id,
        (
            "architecture/contracts/feedback-fitness.json#"
            + feedback_id
        ),
        feedback_policy,
    )
    for objective in feedback_policy["objectives"]:
        add(
            objective["objective_id"],
            (
                "architecture/contracts/feedback-fitness.json#objectives/"
                + objective["objective_id"]
            ),
            objective,
            parents=[feedback_id],
        )

    legacy_policy = registries["legacy-test-layout-policy-v2.json"]
    legacy_policy_id = legacy_policy["policy_id"]
    add(
        legacy_policy_id,
        (
            "architecture/contracts/legacy-test-layout-policy-v2.json#"
            + legacy_policy_id
        ),
        legacy_policy,
    )
    baseline = legacy_policy["baseline"]
    add(
        baseline["baseline_id"],
        (
            "architecture/contracts/legacy-test-layout-policy-v2.json#baseline/"
            + baseline["baseline_id"]
        ),
        baseline,
        parents=[legacy_policy_id],
    )
    for rule in legacy_policy["rules"]:
        add(
            rule["rule_id"],
            (
                "architecture/contracts/legacy-test-layout-policy-v2.json#rules/"
                + rule["rule_id"]
            ),
            rule,
            parents=[legacy_policy_id],
            definition_status=rule["definition_status"],
        )
    for fitness in legacy_policy["fitness_obligations"]:
        add(
            fitness["fitness_id"],
            (
                "architecture/contracts/legacy-test-layout-policy-v2.json#"
                "fitness_obligations/"
                + fitness["fitness_id"]
            ),
            fitness,
            parents=[legacy_policy_id],
        )

    for artifact in registries["artifact-types.json"]["entries"]:
        element_id = f"ARTIFACT-{slug(artifact['artifact_type'])}"
        add(
            element_id,
            (
                "architecture/contracts/artifact-types.json#entries/"
                + artifact["artifact_type"]
            ),
            artifact,
            definition_status=artifact["authority_status"],
        )
    for adr in registries["accepted-adrs.json"]["entries"]:
        add(
            adr["adr_id"],
            (
                "architecture/contracts/accepted-adrs.json#entries/"
                + adr["adr_id"]
            ),
            adr,
        )
    for decision in registries["decisions.json"]["entries"]:
        add(
            decision["decision_id"],
            (
                "architecture/contracts/decisions.json#entries/"
                + decision["decision_id"]
            ),
            decision,
        )

    element_ids = {element["element_id"] for element in elements}
    if element_ids != set(bindings):
        raise ValueError(
            "Architecture element definition binding coverage drift: "
            + ",".join(sorted(element_ids ^ set(bindings)))
        )
    for element in elements:
        (
            contract_ref,
            definition_row,
            parent_refs,
            definition_status,
        ) = bindings[element["element_id"]]
        unknown_parents = set(parent_refs) - element_ids
        if unknown_parents:
            raise ValueError(
                "Architecture element definition parent missing: "
                + element["element_id"]
                + ":"
                + ",".join(sorted(unknown_parents))
            )
        source_path = element["source"].split("#", 1)[0]
        source_file = ROOT / source_path
        if not source_file.is_file():
            raise ValueError(
                "Architecture element definition source missing: "
                + source_path
            )
        element.update(
            {
                "definition_contract_ref": contract_ref,
                "definition_contract_digest": (
                    "sha256:"
                    + sha256_bytes(canonical_bytes(definition_row))
                ),
                "definition_source_path": source_path,
                "definition_source_digest": (
                    "sha256:" + sha256_file(source_file)
                ),
                "parent_element_refs": parent_refs,
                "definition_status": definition_status,
            }
        )


def build_test_health_registries() -> dict[str, dict[str, Any]]:
    expected_directories = {
        spec["directory"] for spec in TEST_HEALTH_RECORD_CLASSES.values()
    }
    if TEST_HEALTH_RECORD_ROOT.exists():
        if (
            TEST_HEALTH_RECORD_ROOT.is_symlink()
            or not TEST_HEALTH_RECORD_ROOT.is_dir()
        ):
            raise ValueError(
                "Test-health record root is not a directory"
            )
        readme_path = TEST_HEALTH_RECORD_ROOT / "README.md"
        if readme_path.is_symlink() or not readme_path.is_file():
            raise ValueError("Test-health record README is missing")
        for child in TEST_HEALTH_RECORD_ROOT.iterdir():
            if child.name == "README.md":
                continue
            if child.name not in expected_directories:
                raise ValueError(
                    "Unexpected test-health record-root entry: "
                    + str(child.relative_to(ROOT))
                )
            if child.is_symlink() or not child.is_dir():
                raise ValueError(
                    "Test-health record child is not a directory: "
                    + str(child.relative_to(ROOT))
                )
    claimed_ids: set[str] = set()
    result: dict[str, dict[str, Any]] = {}
    for record_class, spec in TEST_HEALTH_RECORD_CLASSES.items():
        directory = TEST_HEALTH_RECORD_ROOT / spec["directory"]
        source_paths: list[Path] = []
        if directory.exists():
            for path in directory.iterdir():
                if (
                    path.is_symlink()
                    or not path.is_file()
                    or path.suffix != ".json"
                    or path.name.startswith(".")
                ):
                    raise ValueError(
                        "Noncanonical test-health record entry: "
                        + str(path.relative_to(ROOT))
                    )
                source_paths.append(path)
        source_paths.sort(
            key=lambda path: str(path.relative_to(ROOT)).encode("utf-8")
        )
        entries: list[dict[str, Any]] = []
        for source_path in source_paths:
            record = load_json_strict(source_path)
            record_id = record.get(spec["id_key"])
            if (
                not isinstance(record_id, str)
                or re.fullmatch(
                    r"[A-Z0-9][A-Z0-9-]{0,127}",
                    record_id,
                )
                is None
                or source_path.name != record_id + ".json"
            ):
                raise ValueError(
                    "Test-health record filename/ID mismatch: "
                    + str(source_path.relative_to(ROOT))
                )
            if record_id in claimed_ids:
                raise ValueError(
                    "Test-health record ID is globally reused: "
                    + record_id
                )
            claimed_ids.add(record_id)
            entries.append(
                {
                    "record_id": record_id,
                    "record_class": record_class,
                    "source_path": str(source_path.relative_to(ROOT)),
                    "source_digest": (
                        "sha256:" + sha256_file(source_path)
                    ),
                    "record": record,
                }
            )
        result[spec["registry_filename"]] = registry(
            spec["registry_id"],
            "1.0.0",
            entries,
            record_class=record_class,
            record_schema_path=spec["schema_path"],
            canonical_record_root=str(directory.relative_to(ROOT)),
            record_count=len(entries),
            runtime_validation_status="NOT_ASSESSED",
        )
    return result


def generate_registries() -> dict[str, Any]:
    contexts, zones, decisions, file_patterns = parse_architecture()
    accepted_adrs, accepted_adr_titles = parse_accepted_adr_catalog()
    worker_runtime_catalog = parse_worker_runtime_catalog()
    vital_tuples, applicability_rules = parse_vital_profile()
    source_registry_path = ROOT / "docs" / "research" / "engineering-reference-practice-registry.json"
    source_registry = load_json_strict(source_registry_path)
    source_families = [entry["source_family_id"] for entry in source_registry["source_families"]]
    topology_decision = parse_topology_decision()
    tdd_decision = parse_tdd_decision()
    boundary_decision = parse_boundary_fitness_decision()
    legacy_test_decision = parse_legacy_test_layout_decision()
    legacy_test_policy = build_legacy_test_layout_policy(
        legacy_test_decision
    )
    adr10_authority_catalogs = build_adr10_authority_catalogs()
    worker_runtime_source = str(WORKER_RUNTIME_ADR.relative_to(ROOT))
    worker_runtime_source_digest = (
        "sha256:" + sha256_file(WORKER_RUNTIME_ADR)
    )
    worker_runtime_catalog_digest = (
        "sha256:"
        + sha256_bytes(canonical_bytes(worker_runtime_catalog))
    )
    assignment_defaults = copy.deepcopy(
        worker_runtime_catalog["assignment_defaults"]
    )
    assignment_defaults_digest = (
        "sha256:" + sha256_bytes(canonical_bytes(assignment_defaults))
    )
    worker_role_profiles: list[dict[str, Any]] = []
    for source_row in worker_runtime_catalog["role_profiles"]:
        row = {
            **copy.deepcopy(source_row),
            "catalog_id": worker_runtime_catalog["catalog_id"],
            "catalog_version": worker_runtime_catalog["catalog_version"],
            "catalog_status": worker_runtime_catalog["catalog_status"],
            "source": worker_runtime_source,
            "source_digest": worker_runtime_source_digest,
            "runtime_validation_status": "NOT_ASSESSED",
        }
        row["digest"] = digest_value(row)
        worker_role_profiles.append(row)
    runtime_adapters: list[dict[str, Any]] = []
    for source_row in worker_runtime_catalog["runtime_adapters"]:
        row = {
            **copy.deepcopy(source_row),
            "catalog_id": worker_runtime_catalog["catalog_id"],
            "catalog_version": worker_runtime_catalog["catalog_version"],
            "catalog_status": worker_runtime_catalog["catalog_status"],
            "source": worker_runtime_source,
            "source_digest": worker_runtime_source_digest,
            "runtime_validation_status": "NOT_ASSESSED",
        }
        row["digest"] = digest_value(row)
        runtime_adapters.append(row)
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
        "FF-BOUNDARYFIT-001",
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
    readiness_paths = [
        {
            "path_id": "PATH-READINESS-TIER-CATALOG",
            "owner_context": "process_assurance",
            "path_pattern": "architecture/contracts/readiness-tiers.json",
            "responsibility_class": "READINESS_DEFINITION_CATALOG",
        },
        {
            "path_id": "PATH-READINESS-ASSESSMENT-REGISTRY",
            "owner_context": "process_assurance",
            "path_pattern": (
                "architecture/contracts/readiness-assessments.json"
            ),
            "responsibility_class": "READINESS_ASSESSMENT_REGISTRY",
        },
        {
            "path_id": "PATH-READINESS-RECORDS",
            "owner_context": "process_assurance",
            "path_pattern": "architecture/records/readiness/**",
            "responsibility_class": "READINESS_RECORD_ROOT",
        },
        {
            "path_id": "PATH-READINESS-SCHEMAS",
            "owner_context": "configuration_management",
            "path_pattern": (
                "schemas/assurance/readiness-*.schema.json"
            ),
            "responsibility_class": "EXECUTABLE_SCHEMA",
        },
    ]
    readiness_paths = [
        {
            **entry,
            "definition_status": "DEFINED",
            "runtime_validation_status": "NOT_ASSESSED",
            "source": str(READINESS_ADR.relative_to(ROOT)),
        }
        for entry in readiness_paths
    ]
    topology_engineering_practice_ids = referenced_practice_ids(TOPOLOGY_ADR, source_registry)
    tdd_engineering_practice_ids = referenced_practice_ids(TDD_ADR, source_registry)
    legacy_test_engineering_practice_ids = referenced_practice_ids(
        LEGACY_TEST_LAYOUT_ADR,
        source_registry,
    )

    states = build_state_registry()
    event_registry = build_event_registry(states)
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
    legacy_record_entries = []
    legacy_record_specs = [
        (
            "CHANGE_EXCEPTION",
            "change_exceptions",
            "change_exception_id",
            "schemas/common/legacy-test-change-exception-v2.schema.json",
            LEGACY_TEST_RECORD_DIRECTORIES["CHANGE_EXCEPTION"],
        ),
        (
            "MIGRATION_RECORD",
            "migration_proofs",
            "proof_id",
            "schemas/common/legacy-test-migration-record-v2.schema.json",
            LEGACY_TEST_RECORD_DIRECTORIES["MIGRATION_RECORD"],
        ),
        (
            "CUTOVER_REMOVAL_RECORD",
            "cutover_removal_records",
            "cutover_removal_record_id",
            (
                "schemas/common/"
                "legacy-test-cutover-removal-record-v2.schema.json"
            ),
            LEGACY_TEST_RECORD_DIRECTORIES["CUTOVER_REMOVAL_RECORD"],
        ),
    ]
    for record_kind, policy_key, id_key, schema_ref, directory in (
        legacy_record_specs
    ):
        source_paths = (
            sorted(directory.glob("*.json")) if directory.is_dir() else []
        )
        records = legacy_test_policy[policy_key]
        if len(source_paths) != len(records):
            raise ValueError(
                f"ADR-0010 record projection drift: {record_kind}"
            )
        for source_path, record in zip(source_paths, records, strict=True):
            legacy_record_entries.append(
                {
                    "record_kind": record_kind,
                    "record_id": record[id_key],
                    "source_path": str(source_path.relative_to(ROOT)),
                    "source_digest": "sha256:" + sha256_file(source_path),
                    "schema_ref": schema_ref,
                    "exact_subject_ref": record["exact_subject_ref"],
                    "exact_subject_digest": record["exact_subject_digest"],
                }
            )
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
            capability_zones=zones,
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
            + readiness_paths
            + [
                {"path_id": "PATH-CONTRACT-REGISTRIES", "owner_context": "configuration_management", "path_pattern": "architecture/contracts/**", "responsibility_class": "CANONICAL_REGISTRY", "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/AI_ARTIFACT_CONTRACTS.md#12-executable-schema-tree"},
                {"path_id": "PATH-CONTRACT-SCHEMAS", "owner_context": "configuration_management", "path_pattern": "schemas/**", "responsibility_class": "EXECUTABLE_SCHEMA", "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/AI_ARTIFACT_CONTRACTS.md#12-executable-schema-tree"},
                {"path_id": "PATH-CONTRACT-ASSESSMENTS", "owner_context": "process_assurance", "path_pattern": "docs/architecture/assessments/**", "responsibility_class": "CAPABILITY_ASSESSMENT", "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/SDLC_CONTROL_CATALOG.md#3-cross-lifecycle-control-systems"},
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
                legacy_test_decision["decision_binding"],
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
        "legacy-test-layout-policy-v2.json": legacy_test_policy,
        "legacy-test-layout-records-v2.json": registry(
            "REG-LEGACY-TEST-LAYOUT-RECORDS-001",
            "2.0.0",
            legacy_record_entries,
            change_exception_count=len(
                legacy_test_policy["change_exceptions"]
            ),
            migration_record_count=len(
                legacy_test_policy["migration_proofs"]
            ),
            cutover_removal_record_count=len(
                legacy_test_policy["cutover_removal_records"]
            ),
            canonical_record_root=str(
                LEGACY_TEST_RECORD_ROOT.relative_to(ROOT)
            ),
            runtime_validation_status="NOT_ASSESSED",
        ),
        "effects.json": registry(
            "REG-EFFECTS-001",
            "1.0.0",
            [
                {"effect_family_id": f"EFFECT-{slug(name)}", "name": name, "authority_owner": "governed_execution", "adapter_owner": adapter, "reconciliation_required_for_unknown_outcome": True, "runtime_validation_status": "NOT_ASSESSED", "source": "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md#19-effects-idempotency-and-reconciliation"}
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
        "worker-role-profiles.json": registry(
            "REG-WORKER-ROLE-PROFILES-001",
            "1.0.0",
            worker_role_profiles,
            catalog_id=worker_runtime_catalog["catalog_id"],
            catalog_version=worker_runtime_catalog["catalog_version"],
            catalog_status=worker_runtime_catalog["catalog_status"],
            catalog_digest=worker_runtime_catalog_digest,
            governing_adr=worker_runtime_catalog["governing_adr"],
            fixed_decision_count=worker_runtime_catalog[
                "fixed_decision_count"
            ],
            assignment_defaults=assignment_defaults,
            assignment_defaults_digest=assignment_defaults_digest,
            source=worker_runtime_source,
            source_digest=worker_runtime_source_digest,
            role_profile_count=len(worker_role_profiles),
            runtime_validation_status="NOT_ASSESSED",
        ),
        "runtime-adapters.json": registry(
            "REG-RUNTIME-ADAPTERS-001",
            "1.0.0",
            runtime_adapters,
            catalog_id=worker_runtime_catalog["catalog_id"],
            catalog_version=worker_runtime_catalog["catalog_version"],
            catalog_status=worker_runtime_catalog["catalog_status"],
            catalog_digest=worker_runtime_catalog_digest,
            governing_adr=worker_runtime_catalog["governing_adr"],
            fixed_decision_count=worker_runtime_catalog[
                "fixed_decision_count"
            ],
            assignment_defaults=copy.deepcopy(assignment_defaults),
            assignment_defaults_digest=assignment_defaults_digest,
            source=worker_runtime_source,
            source_digest=worker_runtime_source_digest,
            runtime_adapter_count=len(runtime_adapters),
            runtime_validation_status="NOT_ASSESSED",
        ),
        "events.json": event_registry,
        "accepted-adrs.json": registry(
            "REG-ACCEPTED-ADRS-001",
            "1.0.0",
            accepted_adrs,
            required_count=len(accepted_adrs),
            source=str(SOURCE_OF_TRUTH.relative_to(ROOT)),
            source_digest="sha256:" + sha256_file(SOURCE_OF_TRUTH),
        ),
        "decisions.json": registry(
            "REG-DECISIONS-001",
            "2.0.0",
            decisions,
            source_register_id="RANEX-FIXED-DECISIONS",
            source_schema_version="1.0.0",
            required_count=29,
            source=str(FIXED_DECISION_ADR.relative_to(ROOT)),
            source_digest="sha256:" + sha256_file(FIXED_DECISION_ADR),
            referenced_fitness_function_count=len(
                {
                    fitness_id
                    for decision in decisions
                    for fitness_id in decision["fitness_functions"]
                }
            ),
        ),
        "applicability-rules.json": registry("APPLICABILITY-SDLC-001", "1.1.0", [{"rule_id": key, "meaning": value} for key, value in applicability_rules.items()]),
        "priority-rules.json": registry("PRIORITY-SDLC-001", "1.0.0", [{"tier": tier, "precedence": index, "trigger_codes": codes} for index, (tier, codes) in enumerate(PRIORITY_TRIGGERS.items())]),
        "vital-profile.json": registry("VITAL-SDLC-001", "1.2.0", vital_tuples, tuple_count=len(vital_tuples), domain_count=len({row["domain_id"] for row in vital_tuples})),
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
                {
                    "decision_id": "ADR-0010",
                    "decision_digest": legacy_test_decision[
                        "decision_binding"
                    ]["digest"],
                    "practice_ids": (
                        legacy_test_engineering_practice_ids
                    ),
                    "application_status": (
                        "DEFINED_MIGRATION_EXCEPTION_ACTIVE_NOT_RUNTIME_ASSESSED"
                    ),
                },
            ],
        ),
    }
    estimate_commitment_contract = (
        parse_estimate_commitment_control()
    )
    estimate_projection = estimate_commitment_contract[
        "contract_projection_contract"
    ]
    estimate_projection_values = {
        "registry_id": estimate_commitment_contract[
            "contract_projection_id"
        ],
        "version": estimate_commitment_contract["contract_version"],
        "status": "DEFINED_RUNTIME_NOT_ASSESSED",
        "source_path": (
            "docs/architecture/SDLC_CONTROL_CATALOG.md"
        ),
        "source_fragment": "SDLC ESTIMATE COMMITMENT CONTROL",
        "source_digest": (
            "sha256:" + ESTIMATE_COMMITMENT_BLOCK_SHA256
        ),
        "generated_by": GENERATOR_WRITER,
        "entries": [estimate_commitment_contract],
    }
    if (
        list(estimate_projection_values)
        != estimate_projection["envelope_fields"]
    ):
        raise ValueError(
            "Estimate/commitment projection field order drift"
        )
    registries.update(adr10_authority_catalogs)
    registries.update(build_readiness_registries())
    registries["estimate-commitment-control.json"] = (
        estimate_projection_values
    )
    registries.update(build_test_health_registries())

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
            legacy_test_decision["decision_binding"],
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
        legacy_test_engineering_practice_ids=(
            legacy_test_engineering_practice_ids
        ),
        legacy_test_layout_policy_ref=(
            "architecture/contracts/legacy-test-layout-policy-v2.json"
        ),
        legacy_test_layout_policy_id=legacy_test_policy["policy_id"],
        legacy_test_layout_policy_digest=(
            "sha256:"
            + sha256_bytes(canonical_bytes(legacy_test_policy))
        ),
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
        registries["legacy-test-layout-policy-v2.json"],
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
                "owner_context": producer,
                "projection_kind": "AUTHORING_TEMPLATE",
                "generation_contract_ref": None,
                "authority_status": "DEFINED",
                "runtime_producer_validation_status": "NOT_ASSESSED",
            }
        )
    for generated in GENERATED_ARTIFACT_SCHEMAS:
        artifact_entries.append(
            {
                **copy.deepcopy(generated),
                "template_path": None,
                "projection_kind": "GENERATED_PROJECTION",
                "authority_status": "DEFINED",
                "runtime_producer_validation_status": "NOT_ASSESSED",
            }
        )
    registries["artifact-types.json"] = registry(
        "REG-ARTIFACT-TYPES-001",
        "1.0.0",
        artifact_entries,
        artifact_type_count=len(artifact_entries),
        authoring_template_count=len(ARTIFACT_SCHEMAS),
        generated_projection_count=len(GENERATED_ARTIFACT_SCHEMAS),
    )

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
        elements.append(
            {
                "element_id": event["event_id"],
                "kind": "EVENT",
                "name": event["event_name"],
                "owner_contexts": [event["owner_context"]],
                "definition_status": (
                    "DEFINED"
                    if event["schema_status"] == "DEFINED_CONTRACT"
                    else "DEFINED_NAME_ONLY"
                ),
                "runtime_validation_status": "NOT_ASSESSED",
                "source": event["source"],
            }
        )
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
    elements.extend(
        [
            {
                "element_id": legacy_test_policy["policy_id"],
                "kind": "LEGACY_TEST_LAYOUT_POLICY",
                "name": "Bound inherited Hermes test-layout migration policy",
                "owner_contexts": [
                    "compatibility",
                    "migration",
                    "process_assurance",
                ],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": str(LEGACY_TEST_LAYOUT_ADR.relative_to(ROOT)),
            },
            {
                "element_id": legacy_test_policy["baseline"]["baseline_id"],
                "kind": "IMMUTABLE_TEST_BASELINE",
                "name": "Hermes inherited test byte baseline",
                "owner_contexts": ["compatibility", "migration"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": str(LEGACY_TEST_LAYOUT_ADR.relative_to(ROOT)),
            },
        ]
    )
    for item in legacy_test_policy["rules"]:
        elements.append(
            {
                "element_id": item["rule_id"],
                "kind": "LEGACY_TEST_LAYOUT_RULE",
                "name": item["invariant"],
                "owner_contexts": ["process_assurance"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": item["source"],
            }
        )
    for item in legacy_test_policy["fitness_obligations"]:
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
        elements.append(
            {
                "element_id": (
                    f"ARTIFACT-{slug(item['artifact_type'])}"
                ),
                "kind": "ARTIFACT_TYPE",
                "name": item["artifact_type"],
                "owner_contexts": [item["owner_context"]],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": (
                    item["template_path"]
                    or item["generation_contract_ref"]
                ),
            }
        )
    for adr in accepted_adrs:
        elements.append(
            {
                "element_id": adr["adr_id"],
                "kind": "ADR",
                "name": accepted_adr_titles[adr["adr_id"]],
                "owner_contexts": ["human_governor"],
                "definition_status": "DEFINED",
                "runtime_validation_status": "NOT_ASSESSED",
                "source": adr["source_path"],
            }
        )
    for item in decisions:
        elements.append({"element_id": item["decision_id"], "kind": "DECISION", "name": item["name"], "owner_contexts": ["human_governor"], "definition_status": "DEFINED", "runtime_validation_status": "NOT_ASSESSED", "source": item["source"]})
    bind_architecture_element_definitions(elements, registries)
    architecture_practice_profile = load_json_strict(
        ARCHITECTURE_PRACTICE_PROFILE
    )
    if (
        sha256_file(ARCHITECTURE_PRACTICE_PROFILE)
        != ARCHITECTURE_PRACTICE_PROFILE_SHA256
    ):
        raise ValueError(
            "Architecture practice profile pinned digest drift"
        )
    expected_normative_source_refs = [
        "docs/architecture/HERMES_GROUND_ZERO_FULL_SYSTEM_ARCHITECTURE.md",
        "docs/architecture/README.md",
        "docs/architecture/SOURCE_OF_TRUTH.md",
        "docs/architecture/SDLC_CONTROL_CATALOG.md",
        *[row["source_path"] for row in accepted_adrs],
    ]
    if (
        architecture_practice_profile["subject"][
            "normative_source_refs"
        ]
        != expected_normative_source_refs
        or len(expected_normative_source_refs)
        != len(set(expected_normative_source_refs))
    ):
        raise ValueError(
            "Architecture practice profile normative accepted-ADR "
            "source set/order drift"
        )
    if "ARCHDEC-" in read(ARCHITECTURE_PRACTICE_PROFILE):
        raise ValueError(
            "Architecture practice profile retains legacy decision alias"
        )
    architecture_practice_profile_digest = (
        "sha256:" + sha256_file(ARCHITECTURE_PRACTICE_PROFILE)
    )
    element_ids = {item["element_id"] for item in elements}
    typed_element_fields = [
        "architecture_element_ids",
        "adr_ids",
        "decision_ids",
        "org_rule_ids",
        "tdd_rule_ids",
    ]
    explicitly_mapped_ids = {
        element_id
        for application in architecture_practice_profile[
            "practice_applications"
        ]
        for field in typed_element_fields
        for element_id in application[field]
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
        for field in typed_element_fields:
            for element_id in application[field]:
                applications_by_element[element_id].append(
                    {
                        "profile_id": (
                            architecture_practice_profile["profile_id"]
                        ),
                        "practice_id": application["practice_id"],
                        "profile_field": field,
                        "disposition": application["disposition"],
                        "design_application_status": application[
                            "design_application_status"
                        ],
                        "material_unknown": application[
                            "material_unknown"
                        ],
                        "runtime_enactment_status": application[
                            "runtime_enactment_status"
                        ],
                    }
                )
    for item in elements:
        applications = sorted(
            applications_by_element[item["element_id"]],
            key=lambda row: (
                row["practice_id"],
                row["profile_field"],
            ),
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
            "mapping_policy": (
                "EXPLICIT_TYPED_REFERENCES_ONLY_NO_TRANSITIVE_INFERENCE"
            ),
            "sealing_eligible": architecture_practice_profile["summary"][
                "sealing_eligible"
            ],
            "runtime_claim": architecture_practice_profile["runtime_claim"],
        },
        counts_by_kind={kind: sum(1 for item in elements if item["kind"] == kind) for kind in sorted({item["kind"] for item in elements})},
    )
    registries["architecture-element-assessments.json"] = (
        build_architecture_element_assessment_registry(
            elements,
            architecture_practice_profile,
            architecture_practice_profile_digest,
            registries["paths.json"],
        )
    )

    for filename, content in registries.items():
        write_json(CONTRACTS / filename, content)
    return registries


def generate_schemas(registries: dict[str, Any]) -> None:
    schemas = {**common_schemas(), **build_subject_schemas()}
    schemas.update(estimate_commitment_contract_schemas())
    schemas.update(readiness_contract_schemas())
    worker_role_schema = infer_schema(
        registries["worker-role-profiles.json"]["entries"][0],
        "",
        "worker_role_profile",
    )
    worker_role_schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://schemas.ranex.dev/common/"
                "worker-role-profile-v1.schema.json"
            ),
            "title": "Ranex worker role maximum-ceiling profile",
            "x-ranex-source-registry": (
                "architecture/contracts/worker-role-profiles.json"
            ),
            "x-ranex-runtime-semantics": (
                "scripts/architecture/validate_contracts.py"
            ),
        }
    )
    schemas[
        "common/worker-role-profile-v1.schema.json"
    ] = worker_role_schema
    runtime_adapter_schema = infer_schema(
        next(
            row
            for row in registries["runtime-adapters.json"]["entries"]
            if row["runtime_adapter_id"]
            == "RUNTIME-CLAUDE-AGENT-SDK-001"
        ),
        "",
        "runtime_adapter",
    )
    runtime_adapter_schema["required"].remove(
        "forbidden_runtime_tool_names"
    )
    runtime_adapter_schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": (
                "https://schemas.ranex.dev/common/"
                "runtime-adapter-v1.schema.json"
            ),
            "title": "Ranex official leaf-worker runtime adapter",
            "x-ranex-source-registry": (
                "architecture/contracts/runtime-adapters.json"
            ),
            "x-ranex-runtime-semantics": (
                "scripts/architecture/validate_contracts.py"
            ),
        }
    )
    schemas[
        "common/runtime-adapter-v1.schema.json"
    ] = runtime_adapter_schema
    schemas.update(tdd_health_contract_schemas())
    schemas[
        "artifacts/artifact-legal-hold-fact-v1.schema.json"
    ] = artifact_legal_hold_fact_schema()
    schemas[
        "assurance/checker-execution-subject-v1.schema.json"
    ] = checker_execution_subject_schema()
    state_registry = registries["states.json"]
    schemas.update(event_contract_schemas(state_registry))
    schemas["common/test-practice-profile-v1.schema.json"] = test_practice_profile_schema()
    schemas["common/architecture-rule-assessment-v1.schema.json"] = architecture_rule_assessment_schema()
    schemas[
        "common/architecture-element-assessment-v1.schema.json"
    ] = architecture_element_assessment_schema()
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
    authoritative_legacy_record_schemas = {
        "test_behavior_authorities": legacy_test_record_schema(
            "test_behavior_authorities",
            "test-behavior-authority-v1.schema.json",
            "Ranex governed test-behavior authority",
        ),
        "direct_source_classification_authorities": (
            legacy_test_record_schema(
                "direct_source_classification_authorities",
                "direct-source-classification-authority-v1.schema.json",
                "Ranex direct legacy-test source classification authority",
            )
        ),
        "change_exceptions": legacy_test_record_schema(
            "change_exceptions",
            "legacy-test-change-exception-v2.schema.json",
            "Ranex legacy-test in-place change exception",
        ),
        "migration_proofs": legacy_test_record_schema(
            "migration_proofs",
            "legacy-test-migration-record-v2.schema.json",
            "Ranex legacy-test canonical migration record",
        ),
        "cutover_removal_records": legacy_test_record_schema(
            "cutover_removal_records",
            "legacy-test-cutover-removal-record-v2.schema.json",
            "Ranex legacy-test cutover and removal record",
        ),
    }
    legacy_policy_schema = legacy_test_layout_policy_schema()
    for collection_key in (
        "change_exceptions",
        "migration_proofs",
        "cutover_removal_records",
    ):
        record_schema = authoritative_legacy_record_schemas[
            collection_key
        ]
        legacy_policy_schema["properties"][collection_key]["items"] = {
            key: copy.deepcopy(value)
            for key, value in record_schema.items()
            if not key.startswith("$") and key != "title"
        }
    schemas["common/legacy-test-layout-policy-v2.schema.json"] = (
        legacy_policy_schema
    )
    schemas["common/legacy-test-change-exception-v2.schema.json"] = (
        authoritative_legacy_record_schemas["change_exceptions"]
    )
    schemas["common/test-behavior-authority-v1.schema.json"] = (
        authoritative_legacy_record_schemas[
            "test_behavior_authorities"
        ]
    )
    schemas[
        "common/direct-source-classification-authority-v1.schema.json"
    ] = authoritative_legacy_record_schemas[
        "direct_source_classification_authorities"
    ]
    schemas["common/legacy-test-migration-record-v2.schema.json"] = (
        authoritative_legacy_record_schemas["migration_proofs"]
    )
    schemas[
        "common/legacy-test-cutover-removal-record-v2.schema.json"
    ] = authoritative_legacy_record_schemas[
        "cutover_removal_records"
    ]
    for template_name, (relative_schema, producer) in ARTIFACT_SCHEMAS.items():
        if (
            "schemas/" + relative_schema
            in ADR10_IMMUTABLE_V1_INPUT_PATHS
        ):
            historical_schema_path = SCHEMAS / relative_schema
            schemas[relative_schema] = load_json_strict(
                historical_schema_path
            )
            continue
        if template_name == "TRANSITION_EVENT.yaml":
            schemas[relative_schema] = transition_event_schema(
                state_registry
            )
            continue
        template = yaml.safe_load(read(TEMPLATES / template_name))
        artifact_type = template["artifact_type"]
        schema = infer_schema(template, "", artifact_type)
        if template_name == "CHECKER_RESULT.yaml":
            nested_rows = {
                row["type_id"]: row
                for row in parse_tdd_nested_type_catalog()["types"]
            }
            schema["properties"]["failure_fingerprint"] = (
                tdd_type_schema(
                    "ExpectedFailureFingerprintV1|null",
                    "0..1",
                    nested_rows,
                )
            )
        if template_name == "LANDING_RECORD.yaml":
            landing_authority = parse_tdd_nested_type_catalog()[
                "landing_record_status_authority"
            ]
            adr10_contract = parse_adr10_legacy_record_contract()
            landing_role = adr10_contract["landing_record_role"]
            schema = adr10_closed_object_schema(
                {
                    "type_id": "LandingRecordV1",
                    "fields": landing_role["fields"],
                    "field_types": landing_role["field_types"],
                    "array_cardinalities": landing_role[
                        "array_cardinalities"
                    ],
                    "invariants": landing_role["role_predicates"],
                },
                {
                    row["type_id"]: row
                    for row in adr10_contract["nested_types"]
                },
                {
                    row["type_id"]: row
                    for row in parse_tdd_nested_type_catalog()["types"]
                },
            )
            schema["x-ranex-status-authority"] = (
                landing_authority["authority_id"]
            )
            schema["x-ranex-source-contract-id"] = (
                adr10_contract["contract_id"]
            )
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
        if "schemas/" + relative in ADR10_IMMUTABLE_V1_INPUT_PATHS:
            continue
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


def build_worker_runtime_semantic_world(
    registries: dict[str, Any],
) -> dict[str, Any]:
    role_registry = registries["worker-role-profiles.json"]
    adapter_registry = registries["runtime-adapters.json"]
    role = next(
        row
        for row in role_registry["entries"]
        if row["role_profile_id"]
        == "ROLEPROFILE-IMPLEMENTATION-WORKER-001"
    )
    adapter = next(
        row
        for row in adapter_registry["entries"]
        if row["runtime_adapter_id"]
        == "RUNTIME-CLAUDE-AGENT-SDK-001"
    )
    effective_tool_ids = [
        "TOOL-PATCH-APPLY",
        "TOOL-WORKSPACE-READ",
    ]
    effective_runtime_tool_names = ["Edit", "Read"]
    effective_capability_ids = ["CAP-WORKSPACE-READ"]
    tool_grant_digest = (
        "sha256:"
        + sha256_bytes(
            canonical_bytes(
                {
                    "kind": "EFFECTIVE_TOOL_GRANT",
                    "ids": effective_tool_ids,
                }
            )
        )
    )
    capability_grant_digest = (
        "sha256:"
        + sha256_bytes(
            canonical_bytes(
                {
                    "kind": "EFFECTIVE_CAPABILITY_GRANT",
                    "ids": effective_capability_ids,
                }
            )
        )
    )
    runtime_tool_mapping_digest = (
        "sha256:"
        + sha256_bytes(
            canonical_bytes(
                {
                    "TOOL-PATCH-APPLY": "Edit",
                    "TOOL-WORKSPACE-READ": "Read",
                }
            )
        )
    )
    route_lock_digest = (
        "sha256:" + sha256_bytes(b"fixture-route-lock")
    )
    auth_subject_digest = (
        "sha256:" + sha256_bytes(b"fixture-auth-subject")
    )
    sandbox_digest = (
        "sha256:" + sha256_bytes(b"fixture-sandbox")
    )
    configuration_digest = (
        "sha256:" + sha256_bytes(b"fixture-configuration")
    )
    process_profile_digest = (
        "sha256:" + sha256_bytes(b"fixture-process-profile")
    )
    assignment_id = "assignment_fixture_worker_runtime"
    project_id = "prj_fixture_worker_runtime"
    workspace_id = "wsp_fixture_worker_runtime"
    session_id = "session_fixture_worker_runtime"
    full_model_id = "claude-fixture-full-model-id"
    common = {
        "worker_runtime_catalog_digest": role_registry["catalog_digest"],
        "role_profile_id": role["role_profile_id"],
        "role_profile_digest": role["digest"],
        "runtime_adapter_id": adapter["runtime_adapter_id"],
        "runtime_adapter_version": adapter["version"],
        "runtime_adapter_digest": adapter["digest"],
        "provider_id": "ANTHROPIC",
        "full_model_id": full_model_id,
        "transport_id": adapter["protocol"],
        "route_lock_id": "route_fixture_worker_runtime",
        "route_lock_digest": route_lock_digest,
        "auth_route_class": "LOCAL_INDIVIDUAL_SUBSCRIPTION",
        "subscription_runtime_requested": True,
        "effective_auth_subject_digest": auth_subject_digest,
        "effective_tool_ids": effective_tool_ids,
        "effective_runtime_tool_names": effective_runtime_tool_names,
        "effective_tool_grant_digest": tool_grant_digest,
        "tool_name_mapping_digest": runtime_tool_mapping_digest,
        "effective_capability_ids": effective_capability_ids,
        "effective_capability_grant_digest": capability_grant_digest,
        "sandbox_profile_id": "sandbox_fixture_worker_runtime",
        "sandbox_profile_digest": sandbox_digest,
        "configuration_profile_digest": configuration_digest,
        "controlled_process_profile_digest": process_profile_digest,
    }
    limits = {
        "strict_role_subset_required": True,
        "route_cardinality": 1,
        "worker_spawn_limit": 0,
        "worker_delegation_limit": 0,
        "worker_coordination_limit": 0,
        "adapter_fallback_limit": 0,
        "provider_fallback_limit": 0,
        "model_fallback_limit": 0,
        "auxiliary_model_call_limit": 0,
        "nested_worker_lineage_limit": 0,
        "effect_path": "POLICY_THEN_CAPABILITY_BUS",
        "credential_export_allowed": False,
        "direct_token_http_allowed": False,
        "bare_mode_allowed": False,
        "consumer_login_brokering_allowed": False,
        "hermes_nous_model_route_allowed": False,
    }
    affinity = {
        "project_id": project_id,
        "assignment_id": assignment_id,
        "workspace_id": workspace_id,
        "session_id": session_id,
        "runtime_adapter_id": adapter["runtime_adapter_id"],
        "runtime_adapter_version": adapter["version"],
        "route_lock_digest": route_lock_digest,
        "effective_auth_subject_digest": auth_subject_digest,
        "role_profile_digest": role["digest"],
        "effective_tool_grant_digest": tool_grant_digest,
        "sandbox_profile_digest": sandbox_digest,
        "digest": "",
    }
    affinity["digest"] = digest_value(affinity)
    packet_requirements = {
        **copy.deepcopy(common),
        **copy.deepcopy(limits),
        "ambient": {
            "user_settings": False,
            "project_settings": False,
            "local_settings": False,
            "mcp_servers": [],
            "plugins": [],
            "skills": [],
            "apps": [],
            "network_destinations": [],
            "secret_handles": [],
            "process_executables": [],
        },
    }
    assignment_binding = {
        **copy.deepcopy(common),
        "permission_mode": "DONT_ASK",
        "tool_attempt_gateway": (
            "PRE_TOOL_USE_OR_SDK_CUSTOM_TOOL"
        ),
        "strict_mcp_config": True,
        "settings_sources": [],
        "skills": [],
        "plugins": [],
        "apps": [],
        "mcp_servers": [],
        "agent_definitions": [],
        "auto_memory_enabled": False,
        "background_execution_enabled": False,
        "assignment_config_home_ref": (
            "lease-local-config://fixture"
        ),
        "assignment_cwd": "/fixture/worktree",
        "ambient_network_destinations": [],
        "ambient_secret_handles": [],
        "ambient_process_executables": [],
        **copy.deepcopy(limits),
        "session_affinity": copy.deepcopy(affinity),
    }
    attempt_binding = {
        **copy.deepcopy(common),
        "session_affinity_digest": affinity["digest"],
    }
    observation = {
        "configured_full_model_id": full_model_id,
        "observed_full_model_id": full_model_id,
        "model_observation_status": "OBSERVED_EXACT",
        "observed_provider_id": "ANTHROPIC",
        "observed_transport_id": adapter["protocol"],
        "observed_route_lock_id": "route_fixture_worker_runtime",
        "observed_route_lock_digest": route_lock_digest,
        "runtime_adapter_id": adapter["runtime_adapter_id"],
        "runtime_adapter_version": adapter["version"],
        "sdk_package_digest": (
            "sha256:" + sha256_bytes(b"fixture-sdk-package")
        ),
        "runtime_executable_digest": (
            "sha256:" + sha256_bytes(b"fixture-runtime-executable")
        ),
        "init_reported_runtime_tool_names": (
            copy.deepcopy(effective_runtime_tool_names)
        ),
        "normalized_effective_tool_ids": copy.deepcopy(
            effective_tool_ids
        ),
        "tool_name_mapping_digest": runtime_tool_mapping_digest,
        "init_cwd": "/fixture/worktree",
        "init_permission_mode": "DONT_ASK",
        "init_mcp_servers": [],
        "init_agent_definitions": [],
        "init_skills": [],
        "init_plugins": [],
        "init_apps": [],
        "init_cli_version": "fixture-release-pinned",
        "init_api_key_source": "NONE_SUBSCRIPTION_AUTH",
        "active_auth_source_count": 1,
        "observed_auth_route_class": (
            "LOCAL_INDIVIDUAL_SUBSCRIPTION"
        ),
        "auth_environment_sanitized": True,
        "official_subscription_runtime_observed": True,
        "provider_api_key_environment_present": False,
        "bare_mode_observed": False,
        "consumer_login_brokering_observed": False,
        "credential_file_export_observed": False,
        "direct_token_http_observed": False,
        "hermes_nous_model_route_observed": False,
        "ambient_user_settings": [],
        "ambient_project_settings": [],
        "ambient_local_settings": [],
        "ambient_network_destinations": [],
        "ambient_secret_handles": [],
        "ambient_process_executables": [],
        "auto_memory_enabled": False,
        "background_execution_enabled": False,
        "route_count": 1,
        "worker_spawn_count": 0,
        "worker_delegation_count": 0,
        "worker_coordination_count": 0,
        "adapter_fallback_count": 0,
        "provider_fallback_count": 0,
        "model_fallback_count": 0,
        "auxiliary_model_call_count": 0,
        "nested_worker_lineage_count": 0,
        "parent_tool_use_ids": [],
        "model_usage_model_ids": [full_model_id],
        "observed_provider_model_call_count": 1,
        "num_turns": 1,
        "task_tool_count": 0,
        "retry_count": 0,
        "compaction_count": 0,
        "tool_attempt_count": 2,
        "pre_tool_gateway_observation_count": 2,
        "capability_bus_effect_count": 1,
        "event_correlation_complete": True,
        "event_correlation_evidence_ref": (
            "evidence://fixture/correlated-events"
        ),
        "interrupt_requested_at": "2026-07-29T00:00:00Z",
        "terminal_event_drained_at": "2026-07-29T00:00:01Z",
        "sdk_disconnected_at": "2026-07-29T00:00:02Z",
        "supervisor_cleanup_verified_at": (
            "2026-07-29T00:00:03Z"
        ),
        "process_tree_empty_after_cleanup": True,
        "post_cancel_event_count": 0,
        "post_cancel_quarantined": False,
        "session_affinity": copy.deepcopy(affinity),
    }
    result_evidence = {
        "role_profile_id": role["role_profile_id"],
        "role_profile_digest": role["digest"],
        "runtime_adapter_id": adapter["runtime_adapter_id"],
        "runtime_adapter_version": adapter["version"],
        "runtime_adapter_digest": adapter["digest"],
        "full_model_id_configured": full_model_id,
        "full_model_id_observed": full_model_id,
        "model_observation_status": "OBSERVED_EXACT",
        "route_lock_id": common["route_lock_id"],
        "route_lock_digest": route_lock_digest,
        "auth_route_class": common["auth_route_class"],
        "official_subscription_runtime_observed": True,
        "effective_auth_subject_digest": auth_subject_digest,
        "effective_tool_ids": copy.deepcopy(effective_tool_ids),
        "effective_runtime_tool_names": copy.deepcopy(
            effective_runtime_tool_names
        ),
        "effective_tool_grant_digest": tool_grant_digest,
        "effective_capability_ids": copy.deepcopy(
            effective_capability_ids
        ),
        "effective_capability_grant_digest": (
            capability_grant_digest
        ),
        "sandbox_profile_digest": sandbox_digest,
        "session_affinity_digest": affinity["digest"],
        "observed_route_count": 1,
        "observed_worker_spawn_count": 0,
        "observed_worker_delegation_count": 0,
        "observed_worker_coordination_count": 0,
        "observed_adapter_fallback_count": 0,
        "observed_provider_fallback_count": 0,
        "observed_model_fallback_count": 0,
        "observed_auxiliary_model_call_count": 0,
        "observed_nested_worker_lineage_count": 0,
        "observed_provider_model_call_count": 1,
        "model_usage_model_ids": [full_model_id],
        "num_turns": 1,
        "task_tool_count": 0,
        "retry_count": 0,
        "compaction_count": 0,
        "tool_attempt_count": 2,
        "pre_tool_gateway_observation_count": 2,
        "capability_bus_effect_count": 1,
        "cancellation_terminal_event_drained": True,
        "sdk_disconnected": True,
        "supervisor_cleanup_verified": True,
        "process_tree_empty_after_cleanup": True,
        "post_cancel_event_count": 0,
        "post_cancel_quarantined": False,
        "evidence_refs": [
            "evidence://fixture/correlated-events"
        ],
    }
    return {
        "packet": {
            "project_id": project_id,
            "workspace_id": workspace_id,
            "worker_runtime_requirements": packet_requirements,
        },
        "assignment": {
            "assignment_id": assignment_id,
            "workspace_id": workspace_id,
            "worker_runtime_binding": assignment_binding,
        },
        "attempt": {
            "assignment_id": assignment_id,
            "workspace_id": workspace_id,
            "session_id": session_id,
            "worker_runtime_binding": attempt_binding,
            "runtime_observation": observation,
        },
        "result": {
            "worker_runtime_evidence": result_evidence,
        },
    }


def generate_fixtures(registries: dict[str, Any]) -> None:
    golden_dir = SCHEMAS / "fixtures" / "canonical"
    negative_dir = SCHEMAS / "fixtures" / "negative"
    semantic_dir = SCHEMAS / "fixtures" / "semantic"
    for directory in (golden_dir, negative_dir, semantic_dir):
        if directory.exists():
            for path in directory.iterdir():
                if path.is_file():
                    path.unlink()
    readiness = parse_adr12_readiness_contract()
    readiness_fixture = readiness["fixture_contract"]
    readiness_positive_ids = [
        key
        for key in readiness_fixture[
            "positive_case_requirements"
        ]
        if key != "exact_positive_case_count"
    ]
    readiness_negative_ids = [
        key
        for key in readiness_fixture[
            "negative_case_requirements"
        ]
        if key != "exact_negative_case_count"
    ]
    write_json(
        semantic_dir / "readiness-tier-contract-cases.json",
        {
            "fixture_suite": "ADR0012_READINESS_TIER_CONTRACT_V1",
            "contract_id": readiness["contract_id"],
            "evidence_scope": readiness_fixture["evidence_scope"],
            "runtime_claim": readiness_fixture["runtime_claim"],
            "positive_cases": [
                {
                    "fixture_id": case_id,
                    "scenario": case_id,
                    "expected_result": "PASS",
                    "authority_effects": [],
                }
                for case_id in readiness_positive_ids
            ],
            "negative_cases": [
                {
                    "fixture_id": case_id,
                    "mutation": case_id,
                    "expected_error": (
                        "READINESS_"
                        + case_id.upper().replace("-", "_")
                    ),
                    "authority_effects": [],
                    **(
                        {
                            "executed_subcases": copy.deepcopy(
                                READINESS_FRESHNESS_BOUNDARY_SUBCASES
                            ),
                            "executed_subcase_count": len(
                                READINESS_FRESHNESS_BOUNDARY_SUBCASES
                            ),
                        }
                        if case_id
                        == "stale_or_expired_evidence"
                        else {}
                    ),
                }
                for case_id in readiness_negative_ids
            ],
            "exact_positive_case_count": len(
                readiness_positive_ids
            ),
            "exact_negative_case_count": len(
                readiness_negative_ids
            ),
        },
    )
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
    estimate_contract = parse_estimate_commitment_control()
    estimate_fixture_contract = estimate_contract["fixture_contract"]
    write_json(
        ROOT / estimate_fixture_contract["positive_fixture_ref"],
        {
            "fixture_suite": estimate_fixture_contract[
                "positive_suite_id"
            ],
            "contract_id": estimate_contract["contract_id"],
            "coverage_status": (
                "DECLARED_DEFINITION_COVERAGE_NOT_EXECUTED"
            ),
            "semantic_execution_count": 0,
            "schema_matrix_status": "NOT_EXECUTED",
            "runtime_validation_status": "NOT_ASSESSED",
            "cases": [
                {
                    "case_id": case_id,
                    "source_envelope_version": "2.0.0",
                    "query_kind": (
                        "COMMITMENT"
                        if (
                            "COMMITMENT" in case_id
                            or "RECOMMIT" in case_id
                        )
                        and "NO-COMMITMENT" not in case_id
                        else "ESTIMATE_ONLY"
                    ),
                    "mutation": "NONE",
                    "expected_result": (
                        "CURRENT_DELIVERY_COMMITMENT"
                        if (
                            "COMMITMENT" in case_id
                            or "RECOMMIT" in case_id
                        )
                        and "NO-COMMITMENT" not in case_id
                        else "ESTIMATE_ONLY_NON_AUTHORITATIVE"
                    ),
                    "expected_failure_code": None,
                    "expected_authority_effects": (
                        ["DELIVERY_COMMITMENT_FACT_ONLY"]
                        if (
                            "COMMITMENT" in case_id
                            or "RECOMMIT" in case_id
                        )
                        and "NO-COMMITMENT" not in case_id
                        else []
                    ),
                }
                for case_id in estimate_fixture_contract[
                    "positive_case_ids"
                ]
            ],
        },
    )
    estimate_negative_ids = sorted(
        (
            case_id
            for rows in estimate_fixture_contract[
                "negative_case_ids_by_boundary"
            ].values()
            for case_id in rows
        ),
        key=lambda value: value.encode("utf-8"),
    )
    write_json(
        ROOT / estimate_fixture_contract["negative_fixture_ref"],
        {
            "fixture_suite": estimate_fixture_contract[
                "negative_suite_id"
            ],
            "contract_id": estimate_contract["contract_id"],
            "coverage_status": (
                "DECLARED_DEFINITION_COVERAGE_NOT_EXECUTED"
            ),
            "semantic_execution_count": 0,
            "schema_matrix_status": "NOT_EXECUTED",
            "runtime_validation_status": "NOT_ASSESSED",
            "cases": [
                {
                    "case_id": case_id,
                    "source_envelope_version": "2.0.0",
                    "query_kind": "COMMITMENT",
                    "mutation": case_id,
                    "expected_result": "REJECTED_ZERO_AUTHORITY",
                    "expected_failure_code": case_id,
                    "expected_authority_effects": [],
                }
                for case_id in estimate_negative_ids
            ],
        },
    )
    adr10_compatibility = parse_adr10_legacy_record_contract()[
        "compatibility_impact"
    ]["fixture_requirements"]
    write_json(
        semantic_dir / "adr10-compatibility-v2-positive-cases.json",
        {
            "fixture_suite": "ADR10_COMPATIBILITY_V2_POSITIVE",
            "contract_id": "ADR10-LEGACY-TEST-RECORDS-2.0",
            "cases": [
                {
                    **copy.deepcopy(case),
                    "expected_result": "ELIGIBLE_ZERO_WRITE_PREFLIGHT",
                }
                for case in adr10_compatibility["positive"]
            ],
        },
    )
    write_json(
        negative_dir / "adr10-compatibility-v2-negative-cases.json",
        {
            "fixture_suite": "ADR10_COMPATIBILITY_V2_NEGATIVE",
            "contract_id": "ADR10-LEGACY-TEST-RECORDS-2.0",
            "cases": [
                {
                    **copy.deepcopy(case),
                    "expected_result": "REJECTED_ZERO_WRITE",
                }
                for case in adr10_compatibility["negative"]
            ],
        },
    )
    adr10_resolvers = parse_adr10_legacy_record_contract()[
        "nonartifact_reference_resolvers"
    ]
    authority_requirements = adr10_resolvers[
        "direct_source_classification_authority"
    ]
    authority_positive_scenarios = [
        key
        for key in authority_requirements[
            "positive_fixture_requirements"
        ]
        if key != "exact_positive_case_count"
    ]
    authority_negative_scenarios = [
        key
        for key in authority_requirements[
            "negative_fixture_requirements"
        ]
        if key != "exact_negative_case_count"
    ]
    authority_negative_errors = {
        "missing_authority_source": "ADR10_AUTHORITY_SOURCE_MISSING",
        "duplicate_authority_source": "ADR10_AUTHORITY_SOURCE_DUPLICATE",
        "wrong_authority_source_path_or_filename": "ADR10_AUTHORITY_SOURCE_PATH",
        "authority_source_digest_mismatch": "ADR10_AUTHORITY_SOURCE_DIGEST",
        "authority_registry_source_bijection_failure": "ADR10_AUTHORITY_SOURCE_BIJECTION",
        "wrong_baseline_scope_or_source": "ADR10_AUTHORITY_BASELINE_BINDING",
        "missing_behavior_row": "ADR10_AUTHORITY_BEHAVIOR_ROW_MISSING",
        "wrong_or_stale_behavior_version": "ADR10_AUTHORITY_BEHAVIOR_VERSION",
        "behavior_source_or_row_digest_mismatch": "ADR10_AUTHORITY_BEHAVIOR_DIGEST",
        "behavior_expired_revoked_or_superseded": "ADR10_AUTHORITY_BEHAVIOR_LIFECYCLE",
        "missing_behavior_decision": "ADR10_AUTHORITY_BEHAVIOR_DECISION_MISSING",
        "behavior_decision_wrong_subject": "ADR10_AUTHORITY_BEHAVIOR_DECISION_SUBJECT",
        "behavior_decision_wrong_role_action_or_outcome": "ADR10_AUTHORITY_BEHAVIOR_DECISION_ROLE",
        "behavior_decision_digest_ref_mismatch": "ADR10_AUTHORITY_BEHAVIOR_DECISION_DIGEST",
        "missing_binding_role": "ADR10_AUTHORITY_BINDING_MISSING",
        "duplicate_binding_role": "ADR10_AUTHORITY_BINDING_DUPLICATE",
        "authority_binding_order_wrong": "ADR10_AUTHORITY_BINDING_ORDER",
        "wrong_registry_id_version_or_ref": "ADR10_AUTHORITY_REGISTRY_IDENTITY",
        "registry_digest_mismatch": "ADR10_AUTHORITY_REGISTRY_DIGEST",
        "row_ref_missing_or_wrong": "ADR10_AUTHORITY_ROW_REF",
        "row_digest_mismatch": "ADR10_AUTHORITY_ROW_DIGEST",
        "context_behavior_mismatch": "ADR10_AUTHORITY_CONTEXT_BEHAVIOR",
        "capability_behavior_mismatch": "ADR10_AUTHORITY_CAPABILITY_BEHAVIOR",
        "ownership_context_mismatch": "ADR10_AUTHORITY_OWNERSHIP_CONTEXT",
        "lane_category_mismatch": "ADR10_AUTHORITY_LANE_CATEGORY",
        "test_lane_bound_to_profile_not_taxonomy_registry": "ADR10_AUTHORITY_LANE_REGISTRY",
        "taxonomy_mirror_pattern_mismatch": "ADR10_AUTHORITY_MIRROR_PATTERN",
        "nondeterministic_destination_root": "ADR10_AUTHORITY_DESTINATION_NONDETERMINISTIC",
        "missing_classification_decision": "ADR10_AUTHORITY_CLASSIFICATION_DECISION_MISSING",
        "decision_wrong_subject": "ADR10_AUTHORITY_CLASSIFICATION_DECISION_SUBJECT",
        "decision_wrong_role_action_or_outcome": "ADR10_AUTHORITY_CLASSIFICATION_DECISION_ROLE",
        "classification_decision_digest_ref_mismatch": "ADR10_AUTHORITY_CLASSIFICATION_DECISION_DIGEST",
        "decision_not_approved_revoked_or_superseded": "ADR10_AUTHORITY_CLASSIFICATION_DECISION_STATE",
        "decision_or_authority_expired_or_not_yet_valid": "ADR10_AUTHORITY_CLASSIFICATION_LIFECYCLE",
        "conflicting_or_superseding_classification": "ADR10_AUTHORITY_CLASSIFICATION_CONFLICT",
        "behavior_authority_landing_omitted": "ADR10_AUTHORITY_BEHAVIOR_LANDING",
        "classification_authority_landing_omitted_or_failed": "ADR10_AUTHORITY_CLASSIFICATION_LANDING",
        "classification_authority_landing_wrong_subject": "ADR10_AUTHORITY_CLASSIFICATION_LANDING_SUBJECT",
        "sealing_behavior_registry_digest_wrong_or_omitted": "ADR10_AUTHORITY_SEAL_BEHAVIOR_REGISTRY",
        "sealing_classification_registry_digest_wrong_or_omitted": "ADR10_AUTHORITY_SEAL_CLASSIFICATION_REGISTRY",
        "transition_mapping_or_authority_digest_mismatch": "ADR10_AUTHORITY_TRANSITION_MAPPING",
        "direct_change_resolver_omitted": "ADR10_AUTHORITY_CHANGE_CALL_PATH",
        "direct_migration_resolver_omitted": "ADR10_AUTHORITY_MIGRATION_CALL_PATH",
        "synthetic_fixture_claimed_as_live_authority": "ADR10_AUTHORITY_SYNTHETIC_LIVE",
    }
    if set(authority_negative_scenarios) != set(
        authority_negative_errors
    ):
        raise ValueError(
            "ADR-0010 authority semantic fixture mapping drift"
        )
    write_json(
        semantic_dir / "adr10-authority-positive-cases.json",
        {
            "fixture_suite": "ADR10_DIRECT_AUTHORITY_POSITIVE_V1",
            "contract_id": "ADR10-LEGACY-TEST-RECORDS-2.0",
            "cases": [
                {
                    "fixture_id": f"ADR10-AUTH-POS-{index:03d}",
                    "scenario": scenario,
                    "expected_result": "AUTHORITY_RESOLVED",
                }
                for index, scenario in enumerate(
                    authority_positive_scenarios, start=1
                )
            ],
        },
    )
    write_json(
        negative_dir / "adr10-authority-negative-cases.json",
        {
            "fixture_suite": "ADR10_DIRECT_AUTHORITY_NEGATIVE_V1",
            "contract_id": "ADR10-LEGACY-TEST-RECORDS-2.0",
            "cases": [
                {
                    "fixture_id": f"ADR10-AUTH-NEG-{index:03d}",
                    "scenario": scenario,
                    "expected_error": authority_negative_errors[
                        scenario
                    ],
                }
                for index, scenario in enumerate(
                    authority_negative_scenarios, start=1
                )
            ],
        },
    )
    scope_requirements = adr10_resolvers[
        "scope_destination_authority"
    ]
    scope_positive_scenarios = [
        key
        for key in scope_requirements[
            "positive_fixture_requirements"
        ]
        if key != "exact_positive_case_count"
    ]
    scope_negative_scenarios = [
        key
        for key in scope_requirements[
            "negative_fixture_requirements"
        ]
        if key != "exact_negative_case_count"
    ]
    scope_negative_errors = {
        "unknown_scope_id": "LEGACY_TEST_SCOPE_ROW_MISSING",
        "missing_scope_row": "LEGACY_TEST_SCOPE_ROW_MISSING",
        "duplicate_scope_row": "LEGACY_TEST_SCOPE_ROW_DUPLICATE",
        "wrong_scope_for_source_path": "LEGACY_TEST_SCOPE_SOURCE_BINDING",
        "overlapping_scope_match": "LEGACY_TEST_SCOPE_SOURCE_OVERLAP",
        "baseline_population_digest_mismatch": "LEGACY_TEST_SCOPE_POPULATION_DIGEST",
        "stale_or_wrong_policy_binding": "LEGACY_TEST_SCOPE_POLICY_BINDING",
        "expired_scope": "LEGACY_TEST_SCOPE_EXPIRED",
        "fixed_destination_outside_root": "LEGACY_TEST_SCOPE_DESTINATION_PATH",
        "migration_missing_or_wrong_classification_root": "LEGACY_TEST_SCOPE_CLASSIFICATION_MISSING",
        "change_missing_classification": "LEGACY_TEST_SCOPE_CLASSIFICATION_MISSING",
        "change_wrong_classification_root": "LEGACY_TEST_SCOPE_CLASSIFICATION_BINDING",
        "change_stale_classification": "ADR10_AUTHORITY_CLASSIFICATION_LIFECYCLE",
        "change_cross_subject_classification": "ADR10_AUTHORITY_CLASSIFICATION_DECISION_SUBJECT",
        "noncanonical_or_non_py_destination": "LEGACY_TEST_SCOPE_DESTINATION_PATH",
        "path_traversal_or_legacy_recontamination": "LEGACY_TEST_SCOPE_DESTINATION_PATH",
        "duplicate_or_conflicting_destination": "LEGACY_TEST_SCOPE_DESTINATION_CONFLICT",
    }
    if set(scope_negative_scenarios) != set(
        scope_negative_errors
    ):
        raise ValueError(
            "ADR-0010 scope semantic fixture mapping drift"
        )
    write_json(
        semantic_dir / "adr10-scope-positive-cases.json",
        {
            "fixture_suite": "ADR10_SCOPE_DESTINATION_POSITIVE_V2",
            "contract_id": "ADR10-LEGACY-TEST-RECORDS-2.0",
            "cases": [
                {
                    "fixture_id": f"ADR10-SCOPE-POS-{index:03d}",
                    "scenario": scenario,
                    "expected_result": "SCOPE_DESTINATION_RESOLVED",
                }
                for index, scenario in enumerate(
                    scope_positive_scenarios, start=1
                )
            ],
        },
    )
    write_json(
        negative_dir / "adr10-scope-negative-cases.json",
        {
            "fixture_suite": "ADR10_SCOPE_DESTINATION_NEGATIVE_V2",
            "contract_id": "ADR10-LEGACY-TEST-RECORDS-2.0",
            "cases": [
                {
                    "fixture_id": f"ADR10-SCOPE-NEG-{index:03d}",
                    "scenario": scenario,
                    "expected_error": scope_negative_errors[scenario],
                }
                for index, scenario in enumerate(
                    scope_negative_scenarios, start=1
                )
            ],
        },
    )
    write_json(
        negative_dir / "worker-runtime-contract-cases.json",
        {
            "fixture_suite": "WORKER_RUNTIME_CONTAINMENT_V1",
            "base_world": build_worker_runtime_semantic_world(
                registries
            ),
            "cases": [
                {
                    "fixture_id": "WORKER-ROLE-CEILING-WIDENED",
                    "mutation": "ADD_TOOL_OUTSIDE_ROLE_CEILING",
                    "expected_error": "WORKER_EFFECTIVE_TOOL_NOT_ROLE_SUBSET",
                },
                {
                    "fixture_id": "WORKER-ROLE-CEILING-AS-GRANT",
                    "mutation": "GRANT_COMPLETE_ROLE_TOOL_CEILING",
                    "expected_error": "WORKER_EFFECTIVE_TOOL_NOT_STRICT_SUBSET",
                },
                {
                    "fixture_id": "WORKER-INIT-EXTRA-TOOL",
                    "mutation": "INIT_REPORTS_EXTRA_TOOL",
                    "expected_error": "WORKER_INIT_TOOL_SURFACE_MISMATCH",
                },
                {
                    "fixture_id": "WORKER-INIT-AGENT-ALIAS",
                    "mutation": "INIT_REPORTS_TASK_ALIAS",
                    "expected_error": "WORKER_FORBIDDEN_RUNTIME_TOOL",
                },
                {
                    "fixture_id": "WORKER-AMBIENT-MCP",
                    "mutation": "ENABLE_AMBIENT_MCP",
                    "expected_error": "WORKER_AMBIENT_SURFACE",
                },
                {
                    "fixture_id": "WORKER-AGENT-DEFINITION",
                    "mutation": "ADD_AGENT_DEFINITION",
                    "expected_error": "WORKER_AGENT_DEFINITION_PRESENT",
                },
                {
                    "fixture_id": "WORKER-AUTO-PERMISSION",
                    "mutation": "SET_PERMISSION_MODE_AUTO",
                    "expected_error": "WORKER_PERMISSION_MODE",
                },
                {
                    "fixture_id": "WORKER-UNGATED-TOOL-ATTEMPT",
                    "mutation": "DROP_PRE_TOOL_GATE_OBSERVATION",
                    "expected_error": "WORKER_TOOL_ATTEMPT_GATE_COVERAGE",
                },
                {
                    "fixture_id": "WORKER-SPAWNED-CHILD",
                    "mutation": "OBSERVE_WORKER_SPAWN",
                    "expected_error": "WORKER_LEAF_CONTAINMENT",
                },
                {
                    "fixture_id": "WORKER-MODEL-FALLBACK",
                    "mutation": "OBSERVE_MODEL_FALLBACK",
                    "expected_error": "WORKER_FALLBACK_OR_AUXILIARY_CALL",
                },
                {
                    "fixture_id": "WORKER-AUXILIARY-MODEL",
                    "mutation": "OBSERVE_AUXILIARY_MODEL_CALL",
                    "expected_error": "WORKER_FALLBACK_OR_AUXILIARY_CALL",
                },
                {
                    "fixture_id": "WORKER-SECOND-ROUTE",
                    "mutation": "OBSERVE_SECOND_ROUTE",
                    "expected_error": "WORKER_ROUTE_CARDINALITY",
                },
                {
                    "fixture_id": "WORKER-HERMES-ROUTE",
                    "mutation": "OBSERVE_HERMES_ROUTE",
                    "expected_error": "WORKER_HERMES_NOUS_ROUTE",
                },
                {
                    "fixture_id": "WORKER-AUTH-PRECEDENCE",
                    "mutation": "OBSERVE_TWO_AUTH_SOURCES",
                    "expected_error": "WORKER_AUTH_SOURCE_CARDINALITY",
                },
                {
                    "fixture_id": "WORKER-CREDENTIAL-EXPORT",
                    "mutation": "OBSERVE_CREDENTIAL_EXPORT",
                    "expected_error": "WORKER_CREDENTIAL_IMPERSONATION",
                },
                {
                    "fixture_id": "WORKER-DIRECT-TOKEN-HTTP",
                    "mutation": "OBSERVE_DIRECT_TOKEN_HTTP",
                    "expected_error": "WORKER_CREDENTIAL_IMPERSONATION",
                },
                {
                    "fixture_id": "WORKER-BARE-SUBSCRIPTION-MODE",
                    "mutation": "OBSERVE_BARE_SUBSCRIPTION_MODE",
                    "expected_error": "WORKER_SUBSCRIPTION_RUNTIME_AUTH",
                },
                {
                    "fixture_id": "WORKER-CROSS-PROJECT-REUSE",
                    "mutation": "CHANGE_ATTEMPT_AFFINITY_PROJECT",
                    "expected_error": "WORKER_SESSION_AFFINITY",
                },
                {
                    "fixture_id": "WORKER-MODEL-IDENTITY-DRIFT",
                    "mutation": "OBSERVE_DIFFERENT_MODEL",
                    "expected_error": "WORKER_MODEL_IDENTITY",
                },
                {
                    "fixture_id": "WORKER-MODEL-USAGE-DRIFT",
                    "mutation": "ADD_OTHER_MODEL_USAGE",
                    "expected_error": "WORKER_MODEL_USAGE_ROUTE",
                },
                {
                    "fixture_id": "WORKER-CANCEL-CLEANUP-MISSING",
                    "mutation": "DROP_SUPERVISOR_CLEANUP",
                    "expected_error": "WORKER_CANCELLATION_LIFECYCLE",
                },
                {
                    "fixture_id": "WORKER-POST-CANCEL-UNQUARANTINED",
                    "mutation": "ADD_UNQUARANTINED_POST_CANCEL_EVENT",
                    "expected_error": "WORKER_POST_CANCEL_EVENT",
                },
            ],
        },
    )
    write_json(
        negative_dir / "event-contract-mutations.json",
        {
            "fixture_suite": "DOMAIN_EVENT_CONTRACT_SEMANTICS",
            "cases": [
                {
                    "fixture_id": "EVENT-CROSS-CONTRACT-SWAP",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "SWAP_PAYLOAD_REF_DIGEST_AND_BODY",
                    "other_event_id": "EVENT-WORKFLOWPINNED",
                    "expected_error": "EVENT_ENVELOPE_SCHEMA_INVALID",
                },
                {
                    "fixture_id": "EVENT-INVALID-ENUM-CONSTANT",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "INVALID_ENUM_CONSTANT",
                    "expected_error": "EVENT_ENVELOPE_SCHEMA_INVALID",
                },
                {
                    "fixture_id": "EVENT-UNDECLARED-PAYLOAD-FIELD",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "ADD_UNDECLARED_PAYLOAD_FIELD",
                    "expected_error": "EVENT_ENVELOPE_SCHEMA_INVALID",
                },
                {
                    "fixture_id": "EVENT-NULL-NONNULLABLE-FIELD",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "NULL_NONNULLABLE_FIELD",
                    "expected_error": "EVENT_ENVELOPE_SCHEMA_INVALID",
                },
                {
                    "fixture_id": "EVENT-UNSORTED-SET",
                    "event_id": "EVENT-AUTHORIZATIONEVALUATED",
                    "mutation": "UNSORTED_SET",
                    "expected_error": "EVENT_SET_NOT_BYTEWISE_SORTED",
                },
                {
                    "fixture_id": "EVENT-FORGED-DIGEST",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "FORGE_ENVELOPE_DIGEST",
                    "expected_error": "EVENT_ENVELOPE_DIGEST",
                },
                {
                    "fixture_id": "EVENT-NONINCREASING-VERSION",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "NONINCREASING_AGGREGATE_VERSION",
                    "expected_error": "EVENT_AGGREGATE_VERSION_ORDER",
                },
                {
                    "fixture_id": "EVENT-RECORDED-BEFORE-OCCURRED",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "RECORDED_BEFORE_OCCURRED",
                    "expected_error": "EVENT_TIME_ORDER",
                },
                {
                    "fixture_id": "EVENT-ID-REUSED-DIFFERENT-BYTES",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "EVENT_ID_REUSE_DIFFERENT_BYTES",
                    "expected_error": "EVENT_INSTANCE_ID_CONFLICT",
                },
                {
                    "fixture_id": "EVENT-SEQUENCE-GAP",
                    "event_id": "EVENT-RUNCREATED",
                    "mutation": "AGGREGATE_SEQUENCE_GAP",
                    "expected_error": "EVENT_AGGREGATE_SEQUENCE_GAP",
                },
            ],
        },
    )
    write_json(
        negative_dir / "state-transition-contract-cases.json",
        build_state_event_fixture_suite(registries),
    )
    write_json(
        negative_dir / "import-resolution-cases.json",
        {
            "fixture_suite": "PYTHON_IMPORT_RESOLUTION",
            "cases": [
                {
                    "fixture_id": "IMPORT-ABSOLUTE-CANONICAL-TEST",
                    "path": (
                        "tests/unit/work_management/"
                        "test_absolute_import.py"
                    ),
                    "source": (
                        "from ranex.policy.api import "
                        "AuthorizationSnapshot\n"
                    ),
                    "expected_modules": ["ranex.policy.api"],
                },
                {
                    "fixture_id": "IMPORT-ABSOLUTE-LEGACY-ROOT",
                    "path": "tests/acp/test_absolute_import.py",
                    "source": "import ranex.assurance.api\n",
                    "expected_modules": ["ranex.assurance.api"],
                },
                {
                    "fixture_id": "IMPORT-RELATIVE-SOURCE-SIBLING",
                    "path": (
                        "src/ranex/work_management/application/"
                        "relative_import.py"
                    ),
                    "source": "from ..domain import WorkItem\n",
                    "expected_modules": ["ranex.work_management.domain"],
                },
                {
                    "fixture_id": "IMPORT-RELATIVE-NAMESPACE-BOUNDARY",
                    "path": (
                        "src/ranex/work_management/application/"
                        "namespace_import.py"
                    ),
                    "source": "from ...shared import Identifier\n",
                    "expected_modules": ["ranex.shared"],
                },
                {
                    "fixture_id": "IMPORT-RELATIVE-ALIAS-MODULE",
                    "path": (
                        "src/ranex/work_management/application/"
                        "alias_import.py"
                    ),
                    "source": "from . import handlers\n",
                    "expected_modules": [
                        "ranex.work_management.application.handlers"
                    ],
                },
                {
                    "fixture_id": "IMPORT-RELATIVE-TEST-UNRESOLVED",
                    "path": (
                        "tests/unit/work_management/"
                        "test_relative_import.py"
                    ),
                    "source": "from .fixtures import sample\n",
                    "expected_error": (
                        "IMPORT_RELATIVE_PACKAGE_UNRESOLVED"
                    ),
                },
                {
                    "fixture_id": "IMPORT-RELATIVE-SOURCE-TRAVERSAL",
                    "path": "src/ranex/context/application/escape.py",
                    "source": "from .....outside import forged\n",
                    "expected_error": "IMPORT_RELATIVE_TRAVERSAL",
                },
                {
                    "fixture_id": "IMPORT-PATH-TRAVERSAL",
                    "path": "../outside_repository.py",
                    "source": "import ranex.policy.api\n",
                    "expected_error": "IMPORT_PATH_OUTSIDE_REPOSITORY",
                },
                {
                    "fixture_id": "IMPORT-SOURCE-TEST-NAME-COLLISION",
                    "path": "tests/unit/ranex/policy.py",
                    "source": (
                        "import ranex.policy\n"
                        "from ranex.policy.api import Policy\n"
                    ),
                    "expected_modules": [
                        "ranex.policy",
                        "ranex.policy.api",
                    ],
                },
            ],
        },
    )
    write_json(
        negative_dir / "artifact-legal-hold-fact-cases.json",
        build_artifact_legal_hold_fixture_suite(),
    )
    write_json(
        semantic_dir
        / "adr0008-synthetic-definition-contract.json",
        build_tdd_definition_tracer_fixture(registries),
    )
    write_json(
        negative_dir / "architecture-element-parent-mutations.json",
        {
            "fixture_suite": (
                "ARCHITECTURE_ELEMENT_PARENT_DEFINITION_BINDINGS"
            ),
            "cases": [
                {
                    "fixture_id": (
                        "ELEMENT-PARENT-SAME-ID-DEFINITION-DRIFT"
                    ),
                    "mutation": "PARENT_DIGEST_DRIFT",
                    "element_id": "EVENT-RUNCREATED",
                    "expected_error": (
                        "ELEMENT_PARENT_DEFINITION_BINDING"
                    ),
                },
                {
                    "fixture_id": "ELEMENT-PARENT-ORPHAN",
                    "mutation": "PARENT_ORPHAN",
                    "expected_error": "ELEMENT_DEFINITION_PARENT_ORPHAN",
                },
                {
                    "fixture_id": "ELEMENT-PARENT-CYCLE",
                    "mutation": "PARENT_CYCLE",
                    "expected_error": "ELEMENT_DEFINITION_PARENT_CYCLE",
                },
            ],
        },
    )
    write_generated_text(
        negative_dir / "duplicate-key.yaml",
        "# expected_error: DUPLICATE_KEY\nschema_version: \"1\"\nartifact_type: work_intake\nartifact_type: forged_override\n",
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

    authority_subject_ref = (
        "art_" + deterministic_uuid7("test-health-authority-subject")
    )
    authority_subject_digest = (
        "sha256:" + sha256_bytes(b"test-health-authority-subject")
    )
    authority_profile = {
        "profile_id": "TESTPROFILE-AUTHORITY-FIXTURE-001",
        "profile_version": "1.0.0",
        "digest": "sha256:" + sha256_bytes(b"authority-profile"),
        "subject_ref": authority_subject_ref,
        "subject_digest": authority_subject_digest,
        "derived_result": "UNKNOWN",
        "tdd_cycle_ids": ["TDD-CYCLE-AUTHORITY-001"],
        "tdd_exception_ids": ["TDD-EXCEPTION-AUTHORITY-001"],
        "quarantine_ids": ["QUARANTINE-AUTHORITY-001"],
        "obsolete_test_deletion_ids": ["TEST-DELETION-AUTHORITY-001"],
    }
    authority_specs = {
        "tdd_cycle": (
            "cycle_id",
            "TDD-CYCLE-AUTHORITY-001",
            "PROPOSED",
        ),
        "tdd_exception": (
            "exception_id",
            "TDD-EXCEPTION-AUTHORITY-001",
            "ACTIVE",
        ),
        "test_quarantine": (
            "quarantine_id",
            "QUARANTINE-AUTHORITY-001",
            "ACTIVE",
        ),
        "test_deletion": (
            "deletion_id",
            "TEST-DELETION-AUTHORITY-001",
            "ACCEPTED",
        ),
    }
    authority_registries: dict[str, Any] = {}
    for record_class, (
        id_key,
        record_id,
        status,
    ) in authority_specs.items():
        record = {
            id_key: record_id,
            "test_practice_profile_id": authority_profile["profile_id"],
            "test_practice_profile_version": authority_profile[
                "profile_version"
            ],
            "test_practice_profile_digest": authority_profile["digest"],
            "exact_subject_ref": authority_subject_ref,
            "exact_subject_digest": authority_subject_digest,
            "status": status,
        }
        if record_class == "test_quarantine":
            record["opened_at"] = "2026-07-27T00:00:00Z"
            record["expires_at"] = "2026-07-29T00:00:00Z"
        authority_registries[record_class] = {
            "record_class": record_class,
            "entries": [
                {
                    "record_id": record_id,
                    "record_class": record_class,
                    "source_path": (
                        "fixture://test-health/" + record_id
                    ),
                    "source_digest": (
                        "sha256:" + sha256_bytes(canonical_bytes(record))
                    ),
                    "record": record,
                }
            ],
        }
    write_json(
        negative_dir
        / "test-health-authority-population-cases.json",
        {
            "fixture_suite": (
                "TEST_HEALTH_AUTHORITY_POPULATION_RECONCILIATION"
            ),
            "validation_observed_at": FIXED_TIME,
            "base_profile": authority_profile,
            "base_registries": authority_registries,
            "cases": [
                {
                    "fixture_id": "AUTHORITY-POPULATION-EXACT-POSITIVE",
                    "mutation": "NONE",
                    "expected_result": "PASS",
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-MISSING",
                    "mutation": "REMOVE_APPLICABLE_QUARANTINE_ID",
                    "expected_error": (
                        "TEST_PROFILE_AUTHORITY_POPULATION_MISMATCH"
                    ),
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-ORPHAN",
                    "mutation": "ADD_ORPHAN_QUARANTINE_ID",
                    "expected_error": (
                        "TEST_PROFILE_AUTHORITY_ID_DANGLING"
                    ),
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-DUPLICATE",
                    "mutation": "DUPLICATE_QUARANTINE_ID",
                    "expected_error": (
                        "TEST_PROFILE_AUTHORITY_ID_DUPLICATE"
                    ),
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-CROSS-SUBJECT",
                    "mutation": "MOVE_QUARANTINE_TO_OTHER_SUBJECT",
                    "expected_error": (
                        "TEST_PROFILE_AUTHORITY_WRONG_SUBJECT"
                    ),
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-STALE",
                    "mutation": "STALE_QUARANTINE_PROFILE_DIGEST",
                    "expected_error": (
                        "TEST_PROFILE_AUTHORITY_STALE_RECORD"
                    ),
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-EXPIRED",
                    "mutation": "EXPIRE_ACTIVE_QUARANTINE",
                    "expected_error": (
                        "TEST_PROFILE_QUARANTINE_EXPIRED_UNCLOSED"
                    ),
                },
                {
                    "fixture_id": "AUTHORITY-POPULATION-BLOCKED-PASS",
                    "mutation": "CLAIM_PASS_WITH_ACTIVE_QUARANTINE",
                    "expected_error": (
                        "TEST_PROFILE_QUARANTINE_BLOCKS_PASS"
                    ),
                },
            ],
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

    write_generated_text(
        negative_dir / "forbidden-test-bypass.py",
        "# expected_error: TEST_BYPASS\n"
        "def authorize(subject, *, bypass_policy=False):\n"
        "    return True if bypass_policy else subject.is_authorized\n",
    )
    write_generated_text(
        negative_dir / "forbidden-test-only-production-branch.py",
        "# expected_error: TEST_ONLY_PRODUCTION_BRANCH\n"
        "import os\n\n"
        "def active_reducer():\n"
        "    if os.environ.get(\"RANEX_TEST_MODE\"):\n"
        "        return \"alternate_test_reducer\"\n"
        "    return \"production_reducer\"\n",
    )
    write_generated_text(
        negative_dir / "forbidden-cross-context-private-import.py",
        "# expected_error: TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT\n"
        "from ranex.policy.domain.roles import Role\n\n"
        "def use_private_role(role: Role) -> Role:\n"
        "    return role\n",
    )
    write_generated_text(
        negative_dir / "unregistered-public-api-import.py",
        "# expected_error: TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE\n"
        "from ranex.knowledge.api import KnowledgeView\n\n"
        "def use_knowledge(view: KnowledgeView) -> KnowledgeView:\n"
        "    return view\n",
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

    legacy_policy = registries["legacy-test-layout-policy-v2.json"]
    policy_mutations = [
        {
            "fixture_id": "LEGACY-POLICY-SUBTREE-OID-TAMPER",
            "expected_error": "LEGACY_TEST_SUBTREE_OID_BINDING",
            "path": ["directory_exceptions", 0, "subtree_oid_sha1"],
            "value": "0" * 40,
        },
        {
            "fixture_id": "LEGACY-POLICY-DESTINATION-TAMPER",
            "expected_error": "LEGACY_TEST_DESTINATION_BINDING",
            "path": ["directory_exceptions", 0, "destination_root"],
            "value": "tests/contract/compatibility/tampered",
        },
        {
            "fixture_id": "LEGACY-POLICY-EXCEPTION-KIND-TAMPER",
            "expected_error": "LEGACY_TEST_EXCEPTION_KIND_BINDING",
            "path": ["directory_exceptions", 0, "exception_kind"],
            "value": "SEMANTIC_LAYOUT_ONLY",
        },
    ]
    write_json(
        negative_dir / "legacy-test-policy-mutations.json",
        {
            "fixture_suite": "ADR0010_POLICY_TAMPERING",
            "cases": policy_mutations,
            "source_path_cases": [
                {
                    "fixture_id": "LEGACY-RECORD-SOURCE-AT-ROOT",
                    "expected_error": "LEGACY_TEST_RECORD_SOURCE_BINDING",
                    "record_kind": "CHANGE_EXCEPTION",
                    "record_id": "LEGACY-CHANGE-FIXTURE-001",
                    "source_path": (
                        "architecture/records/legacy-test-layout/"
                        "LEGACY-CHANGE-FIXTURE-001.json"
                    ),
                },
                {
                    "fixture_id": "LEGACY-RECORD-SOURCE-UNKNOWN-CHILD",
                    "expected_error": "LEGACY_TEST_RECORD_SOURCE_BINDING",
                    "record_kind": "MIGRATION_RECORD",
                    "record_id": "LEGACY-MIGRATION-FIXTURE-001",
                    "source_path": (
                        "architecture/records/legacy-test-layout/"
                        "unknown/LEGACY-MIGRATION-FIXTURE-001.json"
                    ),
                },
                {
                    "fixture_id": "LEGACY-RECORD-SOURCE-NESTED",
                    "expected_error": "LEGACY_TEST_RECORD_SOURCE_BINDING",
                    "record_kind": "CUTOVER_REMOVAL_RECORD",
                    "record_id": "LEGACY-TEST-CUTOVER-001",
                    "source_path": (
                        "architecture/records/legacy-test-layout/"
                        "cutover-removal-records/nested/"
                        "LEGACY-TEST-CUTOVER-001.json"
                    ),
                },
                {
                    "fixture_id": "LEGACY-RECORD-SOURCE-ID-MISMATCH",
                    "expected_error": "LEGACY_TEST_RECORD_SOURCE_BINDING",
                    "record_kind": "CHANGE_EXCEPTION",
                    "record_id": "LEGACY-CHANGE-FIXTURE-001",
                    "source_path": (
                        "architecture/records/legacy-test-layout/"
                        "change-exceptions/WRONG-ID.json"
                    ),
                },
            ],
        },
    )

    baseline_snapshot = [
        {
            "path": row["path"],
            "mode": row["mode"],
            "content_sha256": row["content_sha256"],
        }
        for row in legacy_test_policy_rows_for_fixture(legacy_policy)
    ]
    baseline_snapshot_by_path = {
        row["path"]: row for row in baseline_snapshot
    }

    def apply_snapshot_operations(
        operations: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        current = copy.deepcopy(baseline_snapshot_by_path)
        for operation in operations:
            action = operation["operation"]
            if action == "REMOVE_ALL":
                current = {}
                continue
            path = operation.get("path") or operation.get("old_path")
            if action in {"REMOVE", "MOVE"}:
                current.pop(path, None)
            if action in {"ADD", "CHANGE"}:
                source = operation.get("source")
                content_sha256 = (
                    hashlib.sha256(source.encode("utf-8")).hexdigest()
                    if source is not None
                    else operation["content_sha256"]
                )
                current[path] = {
                    "path": path,
                    "mode": operation.get("mode", "100644"),
                    "content_sha256": content_sha256,
                }
            elif action == "MOVE":
                new_path = operation["new_path"]
                current[new_path] = {
                    "path": new_path,
                    "mode": operation.get("mode", "100644"),
                    "content_sha256": operation["content_sha256"],
                }
        return sorted(
            current.values(),
            key=lambda row: row["path"].encode("utf-8"),
        )

    def snapshot_subject(
        operations: list[dict[str, Any]],
    ) -> tuple[str, str]:
        current = apply_snapshot_operations(operations)
        subject_digest = (
            "sha256:" + sha256_bytes(canonical_bytes(current))
        )
        return (
            "legacy-test-snapshot:"
            + subject_digest.removeprefix("sha256:"),
            subject_digest,
        )

    def fixture_subject_digest(value: Any) -> str:
        return "sha256:" + sha256_bytes(canonical_bytes(value))

    def fixture_change_transition_subject(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        keys = [
            "policy_id",
            "policy_version",
            "baseline_id",
            "change_exception_id",
            "transition_sequence",
            "predecessor_transition_id",
            "causation_ref",
            "affected_scope_id",
            "baseline_row",
            "current_row",
            "before_subject_ref",
            "before_subject_digest",
            "after_subject_ref",
            "after_subject_digest",
            "canonical_destination",
        ]
        return {
            "kind": "LEGACY_TEST_CHANGE_TRANSITION_SUBJECT_V2",
            **{key: record[key] for key in keys},
        }

    def fixture_migration_transition_subject(
        record: dict[str, Any],
    ) -> dict[str, Any]:
        keys = [
            "policy_id",
            "policy_version",
            "baseline_id",
            "proof_id",
            "migration_group_id",
            "group_member_index",
            "group_member_count",
            "transition_sequence",
            "predecessor_transition_id",
            "causation_ref",
            "affected_scope_id",
            "baseline_source_row",
            "current_source_row",
            "disposition",
            "destination_rows",
            "retirement_rationale",
            "before_subject_ref",
            "before_subject_digest",
            "after_subject_ref",
            "after_subject_digest",
        ]
        return {
            "kind": "LEGACY_TEST_MIGRATION_TRANSITION_SUBJECT_V2",
            **{key: record[key] for key in keys},
        }

    baseline_policy_rows = legacy_test_policy_rows_for_fixture(
        legacy_policy
    )
    baseline_policy_by_path = {
        row["path"]: row for row in baseline_policy_rows
    }

    def initial_disposition_state() -> dict[str, dict[str, Any]]:
        return {
            row["path"]: {
                "old_path": row["path"],
                "old_content_sha256": row["content_sha256"],
                "disposition": "INHERITED",
                "migration_group_id": None,
                "proof_id": None,
                "destination_test_ids": [],
            }
            for row in baseline_policy_rows
        }

    def make_migration_group(
        source_paths: list[str],
        destination_rows: list[dict[str, str]],
        *,
        group_id: str,
        sequence: int,
        predecessor: str,
        state: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        before_state = sorted(
            copy.deepcopy(state).values(),
            key=lambda row: row["old_path"].encode("utf-8"),
        )
        before_digest = fixture_subject_digest(before_state)
        after_state_by_path = copy.deepcopy(state)
        destination_test_ids = sorted(
            {row["test_id"] for row in destination_rows}
        )
        proof_ids = [
            f"LEGACY-MIGRATION-FIXTURE-{group_id}-{index:03d}"
            for index in range(1, len(source_paths) + 1)
        ]
        for path, proof_id in zip(source_paths, proof_ids, strict=True):
            after_state_by_path[path] = {
                "old_path": path,
                "old_content_sha256": baseline_policy_by_path[path][
                    "content_sha256"
                ],
                "disposition": "MIGRATED",
                "migration_group_id": group_id,
                "proof_id": proof_id,
                "destination_test_ids": destination_test_ids,
            }
        after_state = sorted(
            after_state_by_path.values(),
            key=lambda row: row["old_path"].encode("utf-8"),
        )
        after_digest = fixture_subject_digest(after_state)
        proofs = []
        for index, (path, proof_id) in enumerate(
            zip(source_paths, proof_ids, strict=True),
            start=1,
        ):
            baseline_source_row = baseline_policy_by_path[path]
            proof = {
                "schema_version": "legacy-test-migration-record/v2",
                "proof_id": proof_id,
                "record_type": "LEGACY_TEST_MIGRATION_RECORD",
                "proof_type": "LEGACY_TEST_MIGRATION_PROOF_V2",
                "policy_id": legacy_policy["policy_id"],
                "policy_version": legacy_policy["version"],
                "baseline_id": legacy_policy["baseline"]["baseline_id"],
                "migration_group_id": group_id,
                "group_member_index": index,
                "group_member_count": len(source_paths),
                "transition_sequence": sequence,
                "predecessor_transition_id": predecessor,
                "causation_ref": f"CAUSE-{group_id}",
                "before_subject_ref": f"DISPOSITION-BEFORE-{group_id}",
                "before_subject_digest": before_digest,
                "after_subject_ref": f"DISPOSITION-AFTER-{group_id}",
                "after_subject_digest": after_digest,
                "baseline_source_row": baseline_source_row,
                "current_source_row": {
                    "path": path,
                    "mode": baseline_source_row["mode"],
                    "content_sha256": baseline_source_row[
                        "content_sha256"
                    ],
                },
                "affected_scope_id": next(
                    exception["exception_id"]
                    for exception in legacy_policy["directory_exceptions"]
                    if any(
                        row["path"] == path
                        for row in exception["baseline_files"]
                    )
                ),
                "disposition": "MIGRATED",
                "destination_rows": destination_rows,
                "retirement_rationale": "",
                "behavior_evidence_refs": [
                    f"EVIDENCE-BEHAVIOR-{group_id}"
                ],
                "built_artifact_evidence_refs": [
                    f"EVIDENCE-BUILT-{group_id}"
                ],
                "adr0008_check_refs": [f"CHECK-ADR0008-{group_id}"],
                "architecture_check_refs": [
                    f"CHECK-ARCHITECTURE-{group_id}"
                ],
                "residual_reference_scan_refs": [
                    f"SCAN-RESIDUAL-{group_id}"
                ],
                "compatibility_owner_acceptance_ref": (
                    f"ACCEPT-COMPATIBILITY-{group_id}"
                ),
                "migration_owner_acceptance_ref": (
                    f"ACCEPT-MIGRATION-{group_id}"
                ),
                "process_assurance_owner_acceptance_ref": (
                    f"ACCEPT-PROCESS-{group_id}"
                ),
                "independent_migration_review_ref": (
                    f"REVIEW-MIGRATION-{group_id}"
                ),
                "exact_subject_ref": f"TRANSITION-{proof_id}",
                "exact_subject_digest": "",
                "result": "PASS",
                "status": "ACCEPTED",
            }
            proof["exact_subject_digest"] = fixture_subject_digest(
                fixture_migration_transition_subject(proof)
            )
            proofs.append(proof)
        return proofs, after_state_by_path

    legacy_change_path = next(
        row["path"]
        for row in baseline_snapshot
        if row["path"].startswith("tests/acp/")
        and row["path"].endswith(".py")
    )
    changed_source = "# governed inherited maintenance change\n"
    change_operations = [
        {
            "operation": "CHANGE",
            "path": legacy_change_path,
            "source": changed_source,
        }
    ]
    valid_change_scenario = {
        "change_exception_id": "LEGACY-CHANGE-FIXTURE-001",
        "baseline_path": legacy_change_path,
        "rationale": "Exercise exact in-place maintenance authorization.",
        "expires_at": "2026-09-30T23:59:59Z",
        "canonical_destination": (
            "tests/contract/agent_collaboration/acp/"
            + Path(legacy_change_path).name
        ),
        "replacement_plan_ref": "PLAN-LEGACY-MIGRATION-FIXTURE-001",
    }
    stale_change_scenario = {
        **valid_change_scenario,
        "change_exception_id": "LEGACY-CHANGE-FIXTURE-STALE",
        "expires_at": "2026-07-01T00:00:00Z",
    }
    forged_subject_change_scenario = {
        **valid_change_scenario,
        "change_exception_id": "LEGACY-CHANGE-FIXTURE-FORGED-SUBJECT",
    }
    ranex_change_source = "from ranex.policy.api import AuthorizationSnapshot\n"
    ranex_change_operations = [
        {
            "operation": "CHANGE",
            "path": legacy_change_path,
            "source": ranex_change_source,
        }
    ]
    ranex_change_scenario = {
        **valid_change_scenario,
        "change_exception_id": "LEGACY-CHANGE-FIXTURE-RANEX-CORE",
    }

    legacy_move_path = next(
        row["path"]
        for row in baseline_snapshot
        if row["path"].startswith("tests/acp_adapter/")
    )
    canonical_move_path = (
        "tests/integration/agent_collaboration/acp_adapter/"
        + Path(legacy_move_path).name
    )
    migration_test_id = "TEST-LEGACY-MIGRATION-FIXTURE-001"
    migration_destination_source = (
        f"# ranex-test-id: {migration_test_id}\n"
        "def test_migrated_legacy_behavior():\n"
        "    pass\n"
    )
    move_operations = [
        {
            "operation": "MOVE",
            "old_path": legacy_move_path,
            "new_path": canonical_move_path,
            "source": migration_destination_source,
            "content_sha256": hashlib.sha256(
                migration_destination_source.encode("utf-8")
            ).hexdigest(),
        }
    ]
    valid_migration_scenario = {
        "proof_id": "LEGACY-MIGRATION-FIXTURE-001",
        "old_path": legacy_move_path,
        "new_test_ids": [migration_test_id],
        "new_paths": [canonical_move_path],
    }
    bad_destination_migration_scenario = {
        **valid_migration_scenario,
        "proof_id": "LEGACY-MIGRATION-FIXTURE-BAD-DESTINATION",
        "new_paths": ["legacy/not-present.py"],
    }
    forged_subject_migration_scenario = {
        **valid_migration_scenario,
        "proof_id": "LEGACY-MIGRATION-FIXTURE-FORGED-SUBJECT",
    }
    wrong_kind_migration_scenario = {
        **valid_migration_scenario,
        "proof_id": "LEGACY-MIGRATION-FIXTURE-WRONG-KIND",
    }
    standing_cutover_scenario = {
        "scenario_id": "LEGACY-CUTOVER-FIXTURE-STANDING",
    }
    snapshot_cases = [
        {
            "fixture_id": "LEGACY-SNAPSHOT-ADD-IN-LEGACY-ROOT",
            "expected_error": "LEGACY_TEST_BASELINE_EXPANSION",
            "operations": [
                {
                    "operation": "ADD",
                    "path": "tests/acp/test_new_legacy.py",
                    "source": "def test_new(): pass\n",
                }
            ],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-RANEX-CORE-IN-LEGACY-ROOT",
            "expected_error": "LEGACY_TEST_NEW_RANEX_DEPENDENCY",
            "operations": [
                {
                    "operation": "ADD",
                    "path": "tests/acp/test_new_ranex.py",
                    "source": "from ranex.policy.api import AuthorizationSnapshot\n",
                }
            ],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-DIRECT-ADDITION",
            "expected_error": "LEGACY_TEST_DIRECT_ADDITION",
            "operations": [
                {
                    "operation": "ADD",
                    "path": "tests/test_new_direct.py",
                    "source": "def test_new(): pass\n",
                }
            ],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-UNREGISTERED-ROOT",
            "expected_error": "LEGACY_TEST_UNREGISTERED_ROOT",
            "operations": [
                {
                    "operation": "ADD",
                    "path": "tests/unregistered/test_new.py",
                    "source": "def test_new(): pass\n",
                }
            ],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-UNAUTHORIZED-CHANGE",
            "expected_error": "LEGACY_TEST_UNAUTHORIZED_CONTENT_CHANGE",
            "operations": change_operations,
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-STALE-CHANGE-EXCEPTION",
            "expected_error": "LEGACY_TEST_CHANGE_EXCEPTION_EXPIRED",
            "operations": change_operations,
            "change_scenarios": [stale_change_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-FORGED-CHANGE-SUBJECT",
            "expected_error": "LEGACY_TEST_CHANGE_EXCEPTION_SUBJECT",
            "operations": change_operations,
            "change_scenarios": [forged_subject_change_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-VALID-IN-PLACE-CHANGE",
            "expected_result": "MIGRATION_EXCEPTION_ACTIVE",
            "operations": change_operations,
            "change_scenarios": [valid_change_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-VALID-RECORD-RANEX-CORE-REJECTED",
            "expected_error": "LEGACY_TEST_NEW_RANEX_DEPENDENCY",
            "operations": ranex_change_operations,
            "change_scenarios": [ranex_change_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-MOVE-WITHOUT-PROOF",
            "expected_error": "LEGACY_TEST_MIGRATION_PROOF_MISSING",
            "operations": move_operations,
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-BAD-MIGRATION-DESTINATION",
            "expected_error": "LEGACY_TEST_MIGRATION_DESTINATION",
            "operations": move_operations,
            "migration_scenarios": [bad_destination_migration_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-FORGED-MIGRATION-SUBJECT",
            "expected_error": "LEGACY_TEST_MIGRATION_PROOF_SUBJECT",
            "operations": move_operations,
            "migration_scenarios": [forged_subject_migration_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-WRONG-MIGRATION-KIND",
            "expected_error": "LEGACY_TEST_MIGRATION_RECORD_SCHEMA",
            "operations": move_operations,
            "migration_scenarios": [wrong_kind_migration_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-VALID-MIGRATION-RECORD",
            "expected_result": "MIGRATION_EXCEPTION_ACTIVE",
            "operations": move_operations,
            "migration_scenarios": [valid_migration_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-EXPIRED-POLICY",
            "expected_error": "LEGACY_TEST_POLICY_EXPIRED",
            "operations": [],
            "now": "2026-11-01T00:00:00Z",
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-COUNT-ONLY-CUTOVER",
            "expected_error": "LEGACY_TEST_MIGRATION_PROOF_MISSING",
            "operations": [{"operation": "REMOVE_ALL"}],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-NONCOMPENSATING",
            "expected_error": "LEGACY_TEST_UNAUTHORIZED_CONTENT_CHANGE",
            "operations": change_operations,
            "other_rule_pass_count": 56,
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-UNUSED-CHANGE-EXCEPTION",
            "expected_error": "LEGACY_TEST_STANDING_CHANGE_EXCEPTION",
            "operations": [],
            "change_scenarios": [valid_change_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-UNUSED-MIGRATION-PROOF",
            "expected_error": "LEGACY_TEST_STANDING_MIGRATION_PROOF",
            "operations": [
                {
                    "operation": "ADD",
                    "path": canonical_move_path,
                    "source": migration_destination_source,
                }
            ],
            "migration_scenarios": [valid_migration_scenario],
        },
        {
            "fixture_id": "LEGACY-SNAPSHOT-UNUSED-CUTOVER-RECORD",
            "expected_error": "LEGACY_TEST_STANDING_CUTOVER_RECORD",
            "operations": [],
            "cutover_scenarios": [standing_cutover_scenario],
        },
    ]
    write_json(
        negative_dir / "legacy-test-snapshot-mutations.json",
        {
            "fixture_suite": "ADR0010_SNAPSHOT_AND_RECORD_SEMANTICS",
            "cases": snapshot_cases,
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
            "artifact_schemas": len(
                registries["artifact-types.json"]["entries"]
            ),
            "common_schemas": len(list((SCHEMAS / "common").glob("*.schema.json"))),
            "capability_zones": registries["architecture-elements.json"]["counts_by_kind"]["CAPABILITY_ZONE"],
            "vital_control_tuples": len(tuples),
            "capability_assessments": len(assessments),
            "domain_projections": len(domains),
            "architecture_elements": len(registries["architecture-elements.json"]["entries"]),
            "fixed_decisions": len(
                registries["decisions.json"]["entries"]
            ),
            "worker_role_profiles": len(
                registries["worker-role-profiles.json"]["entries"]
            ),
            "runtime_adapters": len(
                registries["runtime-adapters.json"]["entries"]
            ),
            "worker_runtime_negative_cases": 22,
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
            "adr10_rules": len(
                registries["legacy-test-layout-policy-v2.json"]["rules"]
            ),
            "adr10_fitness_obligations": len(
                registries["legacy-test-layout-policy-v2.json"][
                    "fitness_obligations"
                ]
            ),
            "legacy_test_baseline_files": registries[
                "legacy-test-layout-policy-v2.json"
            ]["baseline"]["file_count"],
            "legacy_test_directory_exceptions": len(
                registries["legacy-test-layout-policy-v2.json"][
                    "directory_exceptions"
                ]
            ),
            "legacy_test_active_records": len(
                registries["legacy-test-layout-records-v2.json"]["entries"]
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
            "The architecture-design profile applies all ten source families and 38 practices without a numeric score; task/runtime enactment and behavioral effectiveness remain NOT_ASSESSED.",
            "Human AI-G2 acceptance remains outstanding.",
            "Runtime producer ownership, hidden-fixture isolation, schema package generation, and cross-language RFC 8785 parity remain unproven.",
            "ADR-0007 topology, ADR-0008 TDD, ADR-0009 boundary/coupling/feedback, and ADR-0010 inherited-test migration rules are executable paper contracts; actual source/import/test/runtime enactment remains NOT_ASSESSED.",
            "ADR-0011 worker roles and runtime adapters are definition-only; implementation, containment, entitlement, performance, and runtime enforcement remain NOT_ASSESSED.",
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
| Fixed decisions / role profiles / runtime adapters | {summary['counts']['fixed_decisions']} / {summary['counts']['worker_role_profiles']} / {summary['counts']['runtime_adapters']} |
| Worker-runtime negative semantic cases | {summary['counts']['worker_runtime_negative_cases']} |
| ADR-0007 topology rules | {summary['counts']['topology_rules']} |
| ADR-0008 allowed roots / TDD rules | {summary['counts']['allowed_test_roots']} / {summary['counts']['tdd_rules']} |
| Definition-only per-rule assessments | {summary['counts']['architecture_rule_assessments']} |
| Declared context edges / boundary-fit rows | {summary['counts']['declared_context_dependency_edges']} / {summary['counts']['context_boundary_fit_rows']} |
| ADR-0009 rules / fitness obligations | {summary['counts']['adr9_rules']} / {summary['counts']['adr9_fitness_obligations']} |
| ADR-0010 rules / fitness obligations | {summary['counts']['adr10_rules']} / {summary['counts']['adr10_fitness_obligations']} |
| ADR-0010 inherited files / directory exceptions / active records | {summary['counts']['legacy_test_baseline_files']} / {summary['counts']['legacy_test_directory_exceptions']} / {summary['counts']['legacy_test_active_records']} |
| Coupling measures / feedback objectives | {summary['counts']['coupling_measures']} / {summary['counts']['feedback_objectives']} |
| Negative semantic fixtures | {summary['counts']['negative_fixtures']} |
| Positive semantic fixtures | {summary['counts']['semantic_fixtures']} |

All {summary['counts']['capability_assessments']} control records are `NOT_ASSESSED` with separately recorded
`definition_status: DEFINED`. All ten domain projections derive `UNKNOWN`
because applicability and runtime evidence are unresolved. No numeric maturity
score is fabricated.

Run `uv run --project scripts/architecture python
scripts/architecture/validate_contracts.py` for the deterministic result.
"""
    write_generated_text(ASSESSMENTS / "COMPLETENESS_REPORT.md", md)


def generated_output_class(path: str) -> str:
    if path.startswith("architecture/contracts/"):
        return "CONTRACT_REGISTRY"
    if path.startswith("schemas/fixtures/"):
        return "CONTRACT_FIXTURE"
    if path.startswith("schemas/"):
        return "JSON_SCHEMA"
    if path.startswith(
        "docs/architecture/assessments/controls/"
    ):
        return "CONTROL_ASSESSMENT"
    if path.startswith(
        "docs/architecture/assessments/domains/"
    ):
        return "DOMAIN_PROJECTION"
    if path == (
        "docs/architecture/assessments/validation-report.json"
    ):
        return "VALIDATION_REPORT"
    if path.startswith("docs/architecture/assessments/"):
        return "ASSESSMENT_SUPPORT"
    raise ValueError("Unclassified generated output path: " + path)


def generated_output_licensing_policies(
    paths: set[str],
) -> dict[str, str]:
    manifest = load_json_strict(LEGAL_MANIFEST)
    rows = manifest.get("files")
    if not isinstance(rows, list):
        raise ValueError(
            "Legal manifest files must be an array: "
            + LEGAL_MANIFEST_PATH
        )
    legal_by_path: dict[str, dict[str, Any]] = {}
    for row in rows:
        path = row.get("path") if isinstance(row, dict) else None
        if not isinstance(path, str) or path in legal_by_path:
            raise ValueError(
                "Legal manifest path missing or duplicated: "
                + str(path)
            )
        legal_by_path[path] = row

    policies: dict[str, str] = {}
    for path in paths:
        row = legal_by_path.get(path)
        if row is None:
            raise ValueError(
                "Generated output lacks an explicit legal policy row: "
                + path
            )
        if (
            row.get("classification") == "CURATED_RESEARCH"
            and row.get("license") == "NOASSERTION"
            and row.get("provenance_kind")
            == "DETERMINISTIC_GENERATED_RESEARCH_PROJECTION"
        ):
            policy_id = LICENSING_POLICY_CURATED_RESEARCH
        elif (
            row.get("classification") == "RANEX_ORIGINAL"
            and row.get("license")
            == "LicenseRef-Ranex-Personal-Use-1.0"
            and row.get("provenance_kind")
            == "DETERMINISTIC_GENERATED_PROJECTION"
        ):
            policy_id = LICENSING_POLICY_RANEX_ORIGINAL
        else:
            raise ValueError(
                "Generated output legal policy is unrecognized: "
                + path
            )
        policies[path] = policy_id

    research_paths = {
        path
        for path, policy_id in policies.items()
        if policy_id == LICENSING_POLICY_CURATED_RESEARCH
    }
    if research_paths != CURATED_RESEARCH_GENERATED_OUTPUT_PATHS:
        raise ValueError(
            "Curated-research generated-output partition drift: "
            + "missing="
            + ",".join(
                sorted(
                    CURATED_RESEARCH_GENERATED_OUTPUT_PATHS
                    - research_paths
                )
            )
            + ";unexpected="
            + ",".join(
                sorted(
                    research_paths
                    - CURATED_RESEARCH_GENERATED_OUTPUT_PATHS
                )
            )
        )
    return policies


def generate_output_authority() -> set[str]:
    authority_path = (
        "architecture/contracts/generated-output-authority.json"
    )
    registry_manifest_path = (
        "architecture/contracts/registry-manifest.json"
    )
    generator_paths = GENERATED_OUTPUT_PATHS | {
        authority_path,
        registry_manifest_path,
    }
    validator_paths = {
        "docs/architecture/assessments/validation-report.json"
    }
    adr10_contract = parse_adr10_legacy_record_contract()
    historical = adr10_contract["compatibility_impact"][
        "historical_artifact_authority"
    ]
    historical_writer = historical["writer_authority"]
    writer_by_path = {
        **{path: GENERATOR_WRITER for path in generator_paths},
        **{path: VALIDATOR_WRITER for path in validator_paths},
    }
    licensing_policy_by_path = (
        generated_output_licensing_policies(set(writer_by_path))
    )
    entries = [
        {
            "path": path,
            "writer": writer_by_path[path],
            "output_class": generated_output_class(path),
            "licensing_policy_id": licensing_policy_by_path[path],
            "licensing_projection_required": True,
        }
        for path in sorted(
            writer_by_path,
            key=lambda value: value.encode("utf-8"),
        )
    ]
    immutable_inputs = [
        {
            "path": row["path"],
            "writer": historical_writer["canonical_writer"],
            "input_class": historical_writer["tree_lock_class"],
            "generator_role": historical_writer["generator_role"],
            "owner_class": historical["owner_class"],
            "provenance_kind": historical["provenance_kind"],
            "licensing_classification": historical[
                "licensing_classification"
            ],
            "license_id": historical["license_id"],
            "repository_inclusion": historical[
                "repository_inclusion"
            ],
            "sha256": row["sha256"],
            "artifact_class": row["artifact_class"],
            "disposition": row["disposition"],
            "superseded_by": row["superseded_by"],
            "legal_manifest_binding_required": True,
        }
        for row in historical["rows"]
    ]
    write_json(
        ROOT / authority_path,
        {
            "registry_id": "REG-GENERATED-OUTPUT-AUTHORITY-001",
            "version": "2.1.0",
            "status": "ACTIVE_DOCUMENTATION_CONTRACT",
            "generated_by": GENERATOR_WRITER,
            "generator_writer": GENERATOR_WRITER,
            "validator_writer": VALIDATOR_WRITER,
            "licensing_policy_source_path": LEGAL_MANIFEST_PATH,
            "licensing_policy_source_digest": (
                "sha256:" + sha256_file(LEGAL_MANIFEST)
            ),
            "licensing_policy_ids": sorted(
                {
                    LICENSING_POLICY_RANEX_ORIGINAL,
                    LICENSING_POLICY_CURATED_RESEARCH,
                }
            ),
            "licensing_policy_counts": dict(
                sorted(
                    Counter(
                        licensing_policy_by_path.values()
                    ).items()
                )
            ),
            "output_count": len(entries),
            "generator_output_count": len(generator_paths),
            "validator_output_count": len(validator_paths),
            "entries": entries,
            "immutable_input_count": len(immutable_inputs),
            "immutable_inputs": immutable_inputs,
        },
    )
    return generator_paths


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
    GENERATED_OUTPUT_PATHS.clear()
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
    expected_generator_paths = generate_output_authority()
    generate_manifests()
    if GENERATED_OUTPUT_PATHS != expected_generator_paths:
        raise ValueError(
            "Generated output writer tracking drift: "
            + "missing="
            + ",".join(
                sorted(
                    expected_generator_paths
                    - GENERATED_OUTPUT_PATHS
                )
            )
            + ";orphan="
            + ",".join(
                sorted(
                    GENERATED_OUTPUT_PATHS
                    - expected_generator_paths
                )
            )
        )
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


ISOLATED_CANDIDATE_ENV = "RANEX_CONTRACT_ISOLATED_CANDIDATE"
GENERATED_PUBLICATION_ROOTS = (
    "architecture/contracts/",
    "schemas/",
    "docs/architecture/assessments/",
)


def validated_generated_output_relative(value: str) -> Path:
    relative = Path(value)
    if (
        not value
        or relative.is_absolute()
        or relative.as_posix() != value
        or any(part in {"", ".", ".."} for part in relative.parts)
        or not value.startswith(GENERATED_PUBLICATION_ROOTS)
        or value in ADR10_IMMUTABLE_V1_INPUT_PATHS
    ):
        raise ValueError(
            "Unsafe generated publication path: " + value
        )
    return relative


def generator_paths_from_output_authority(
    repository: Path,
) -> set[str]:
    authority_path = (
        repository
        / "architecture"
        / "contracts"
        / "generated-output-authority.json"
    )
    if not authority_path.is_file() or authority_path.is_symlink():
        raise ValueError(
            "Generated output authority missing or nonregular: "
            + str(authority_path)
        )
    authority = json.loads(
        authority_path.read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicate_json_object,
    )
    entries = authority.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Generated output authority entries malformed")
    paths = {
        row["path"]
        for row in entries
        if isinstance(row, dict)
        and row.get("writer") == GENERATOR_WRITER
        and isinstance(row.get("path"), str)
    }
    if (
        len(paths)
        != authority.get("generator_output_count")
        or len(paths)
        != sum(
            isinstance(row, dict)
            and row.get("writer") == GENERATOR_WRITER
            for row in entries
        )
    ):
        raise ValueError(
            "Generated output authority generator denominator drift"
        )
    for value in paths:
        validated_generated_output_relative(value)
    return paths


def copy_isolated_candidate_repository(
    candidate_root: Path,
) -> None:
    for relative in (
        Path("architecture"),
        Path("docs"),
        Path("schemas"),
        Path("legal"),
        Path("scripts/architecture"),
    ):
        source = ROOT / relative
        if not source.exists():
            continue
        shutil.copytree(
            source,
            candidate_root / relative,
            symlinks=False,
            ignore=shutil.ignore_patterns(
                ".venv",
                "__pycache__",
                "*.pyc",
                ".ranex-contract-candidate-*",
            ),
        )
    git_metadata = ROOT / ".git"
    if git_metadata.exists():
        os.symlink(
            git_metadata.resolve(),
            candidate_root / ".git",
            target_is_directory=git_metadata.is_dir(),
        )


def adr10_historical_byte_snapshot(
    repository: Path,
) -> dict[str, bytes]:
    contract = parse_adr10_legacy_record_contract()
    historical = contract["compatibility_impact"][
        "historical_artifact_authority"
    ]
    result: dict[str, bytes] = {}
    for row in historical["rows"]:
        relative = row["path"]
        path = repository / relative
        if (
            relative not in ADR10_IMMUTABLE_V1_INPUT_PATHS
            or path.is_symlink()
            or not path.is_file()
        ):
            raise ValueError(
                "ADR-0010 historical input missing or nonregular: "
                + relative
            )
        content = path.read_bytes()
        if (
            "sha256:" + hashlib.sha256(content).hexdigest()
            != row["sha256"]
        ):
            raise ValueError(
                "ADR-0010 historical input digest drift: "
                + relative
            )
        result[relative] = content
    if set(result) != set(ADR10_IMMUTABLE_V1_INPUT_PATHS):
        raise ValueError(
            "ADR-0010 historical input exact-set drift"
        )
    return result


def write_atomic_publication_file(
    destination: Path,
    content: bytes,
) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".ranex-contract-publication.",
        dir=destination.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        if temporary_path.exists():
            temporary_path.unlink()
        raise
    return temporary_path


def publish_isolated_candidate(
    candidate_root: Path,
    candidate_paths: set[str],
    historical_before: dict[str, bytes],
) -> None:
    current_authority = (
        ROOT
        / "architecture"
        / "contracts"
        / "generated-output-authority.json"
    )
    current_paths = (
        generator_paths_from_output_authority(ROOT)
        if current_authority.is_file()
        else set()
    )
    candidate_bytes: dict[str, bytes] = {}
    for value in candidate_paths:
        relative = validated_generated_output_relative(value)
        candidate = candidate_root / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise ValueError(
                "Candidate output missing or nonregular: " + value
            )
        candidate_bytes[value] = candidate.read_bytes()
    historical_after_candidate = {
        relative: (candidate_root / relative).read_bytes()
        for relative in historical_before
    }
    if historical_after_candidate != historical_before:
        raise ValueError(
            "ADR-0010 candidate mutated a historical V1 input"
        )
    publication_paths = current_paths | candidate_paths
    previous: dict[str, bytes | None] = {}
    for value in publication_paths:
        destination = ROOT / validated_generated_output_relative(
            value
        )
        if destination.is_symlink():
            raise ValueError(
                "Generated publication destination is a symlink: "
                + value
            )
        previous[value] = (
            destination.read_bytes()
            if destination.is_file()
            else None
        )
    staged: dict[str, Path] = {}
    try:
        for value in sorted(
            candidate_paths,
            key=lambda item: item.encode("utf-8"),
        ):
            destination = (
                ROOT / validated_generated_output_relative(value)
            )
            staged[value] = write_atomic_publication_file(
                destination,
                candidate_bytes[value],
            )
        for value in sorted(
            candidate_paths,
            key=lambda item: item.encode("utf-8"),
        ):
            destination = (
                ROOT / validated_generated_output_relative(value)
            )
            os.replace(staged.pop(value), destination)
        for value in sorted(
            current_paths - candidate_paths,
            key=lambda item: item.encode("utf-8"),
        ):
            stale = ROOT / validated_generated_output_relative(value)
            if stale.is_file():
                stale.unlink()
    except BaseException as publication_error:
        for temporary_path in staged.values():
            if temporary_path.exists():
                temporary_path.unlink()
        rollback_failures: list[str] = []
        for value in sorted(
            publication_paths,
            key=lambda item: item.encode("utf-8"),
        ):
            destination = (
                ROOT / validated_generated_output_relative(value)
            )
            try:
                original = previous[value]
                if original is None:
                    if destination.exists():
                        destination.unlink()
                else:
                    rollback_path = write_atomic_publication_file(
                        destination,
                        original,
                    )
                    os.replace(rollback_path, destination)
            except BaseException as rollback_error:
                rollback_failures.append(
                    f"{value}:{rollback_error}"
                )
        if rollback_failures:
            raise RuntimeError(
                "Contract publication failed and rollback was "
                "incomplete: "
                + ";".join(rollback_failures)
            ) from publication_error
        raise
    historical_after_publication = {
        relative: (ROOT / relative).read_bytes()
        for relative in historical_before
    }
    if historical_after_publication != historical_before:
        raise RuntimeError(
            "ADR-0010 historical bytes changed after publication"
        )


def generate_and_publish_isolated_candidate() -> str:
    historical_before = adr10_historical_byte_snapshot(ROOT)
    with tempfile.TemporaryDirectory(
        prefix="ranex-contract-candidate."
    ) as temporary_directory:
        candidate_root = Path(temporary_directory) / "ranex"
        candidate_root.mkdir()
        copy_isolated_candidate_repository(candidate_root)
        environment = os.environ.copy()
        environment[ISOLATED_CANDIDATE_ENV] = "1"
        completed = subprocess.run(
            [
                sys.executable,
                str(
                    candidate_root
                    / "scripts"
                    / "architecture"
                    / "generate_contracts.py"
                ),
            ],
            cwd=candidate_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise ValueError(
                "Isolated contract candidate rejected with zero "
                "publication: stdout="
                + completed.stdout[-4000:]
                + ";stderr="
                + completed.stderr[-4000:]
            )
        candidate_paths = generator_paths_from_output_authority(
            candidate_root
        )
        publish_isolated_candidate(
            candidate_root,
            candidate_paths,
            historical_before,
        )
        lines = [
            line
            for line in completed.stdout.splitlines()
            if line.strip()
        ]
        if not lines:
            raise ValueError(
                "Isolated contract candidate emitted no result"
            )
        return lines[-1]


def main() -> None:
    with contract_tree_lock(ROOT):
        if os.environ.get(ISOLATED_CANDIDATE_ENV) == "1":
            generate_contract_tree()
        else:
            print(generate_and_publish_isolated_candidate())


if __name__ == "__main__":
    main()
