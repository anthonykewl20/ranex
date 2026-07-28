#!/usr/bin/env python3
"""Fail-closed validation for Ranex Wave-1 documentation contracts."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
import rfc8785
import yaml

from contract_tree_lock import contract_tree_lock


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "architecture" / "contracts"
SCHEMAS = ROOT / "schemas"
ASSESSMENTS = ROOT / "docs" / "architecture" / "assessments"
TEMPLATES = ROOT / "docs" / "architecture" / "templates"
ARCHITECTURE_PRACTICE_PROFILE = (
    ROOT / "docs" / "research" / "ranex-architecture-practice-application-profile.json"
)
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
EXPECTED_ORG_RULE_IDS = {
    "ORG-PATH-001",
    "ORG-CONTEXT-001",
    "ORG-LAYER-001",
    "ORG-PUBLIC-001",
    "ORG-DEPENDENCY-001",
    "ORG-CYCLE-001",
    "ORG-IMPORT-001",
    "ORG-COMPOSE-001",
    "ORG-MESSAGE-001",
    "ORG-PERSIST-001",
    "ORG-TEST-MIRROR-001",
    "ORG-GENERATED-001",
    "ORG-MIGRATION-001",
    "ORG-LEGACY-001",
    "ORG-OWNERSHIP-001",
    "ORG-DISCOVERY-001",
    "ORG-NAV-001",
    "ORG-EXEMPTION-001",
}
EXPECTED_TOPOLOGY_EXCEPTION_CLASSES = {
    "FOUNDATION_PRIMITIVE",
    "BOOTSTRAP_COMPOSITION",
    "HOST_EDGE_ADAPTER",
    "GENERATED_PROJECTION",
    "COMPATIBILITY_QUARANTINE",
}
EXPECTED_TDD_RULE_IDS = {
    "TDD-LOOP-001",
    "TDD-PROD-001",
    "TDD-ARTIFACT-001",
    "TDD-SEAM-001",
    "TDD-SQLITE-001",
    "TDD-TAXONOMY-001",
    "TDD-FAILURE-001",
    "TDD-STATE-001",
    "TDD-OPEN-001",
    "TDD-FIXTURE-001",
    "TDD-FLAKE-001",
    "TDD-GENERATED-001",
    "TDD-MIGRATION-001",
    "TDD-DATA-001",
    "TDD-LANES-001",
    "TDD-MUTATION-001",
    "TDD-OBS-001",
    "TDD-NONCOMP-001",
    "TDD-EXEMPTION-001",
}
EXPECTED_TEST_ROOTS = {
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "tests/architecture",
    "tests/acceptance",
    "tests/system",
    "tests/e2e",
    "tests/security",
    "tests/performance",
    "tests/resilience",
    "tests/migration",
    "tests/replay",
    "tests/operations",
    "tests/qualification",
    "tests/effectiveness",
    "tests/evaluation",
    "tests/fixtures",
    "tests/builders",
}
EXPECTED_TDD_EXCEPTION_CLASSES = {
    "GENERATED_OUTPUT",
    "EMERGENCY_CONTAINMENT",
    "NON_EXECUTABLE_DOCUMENTATION",
}
EXPECTED_FAILURE_MODE_CLASSES = {
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
}
EXPECTED_ADR0007_PRACTICE_IDS = {
    "ENGREF-CLEAN-ARCHITECTURE-1E-USE-CASE-VISIBLE",
    "ENGREF-CLEAN-ARCHITECTURE-1E-DEPENDENCY-RULE",
    "ENGREF-CLEAN-ARCHITECTURE-1E-BOUNDARY-OPTIONS",
    "ENGREF-CLEAN-ARCHITECTURE-1E-ENCAPSULATION-AND-TESTABILITY",
    "ENGREF-CLEAN-CODE-THIRD-PARTY-BOUNDARY",
    "ENGREF-CLEAN-CODE-SEPARATE-CONSTRUCTION-RUNTIME",
    "ENGREF-CODE-COMPLETE-CH5-INFORMATION-HIDING",
    "ENGREF-CODE-COMPLETE-CH5-MANAGE-COMPLEXITY",
    "ENGREF-PRAGMATIC-PROGRAMMER-1E-ORTHOGONALITY",
    "ENGREF-PRAGMATIC-PROGRAMMER-1E-DRY-AUTHORITATIVE-KNOWLEDGE",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-BOUNDARY-QUANTA",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-ORCHESTRATION-COUPLING",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-STYLE-AND-ADR",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS",
}
EXPECTED_ADR0008_PRACTICE_IDS = {
    "ENGREF-CLEAN-CODER-ACCEPTANCE-EXAMPLES",
    "ENGREF-CLEAN-CODER-RISK-LAYERED-TESTING",
    "ENGREF-CLEAN-CODE-VERIFIED-REFACTORING",
    "ENGREF-CLEAN-CODE-THIRD-PARTY-BOUNDARY",
    "ENGREF-CLEAN-CODE-SEPARATE-CONSTRUCTION-RUNTIME",
    "ENGREF-CODE-COMPLETE-CH5-INFORMATION-HIDING",
    "ENGREF-PRAGMATIC-PROGRAMMER-1E-ORTHOGONALITY",
    "ENGREF-PRAGMATIC-PROGRAMMER-1E-TRACER-ROUTE",
    "ENGREF-SWEBOK-V4A-TRACE-CHANGE-QUALITY",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS",
    "ENGREF-CLEAN-ARCHITECTURE-1E-ENCAPSULATION-AND-TESTABILITY",
    "ENGREF-DDIA-1E-ER6-MONOTONIC-TIMEOUTS",
    "ENGREF-DDIA-1E-ER6-FENCING-AT-RESOURCE",
    "ENGREF-DDIA-1E-ER6-ATOMIC-OUTBOX-AND-DERIVATIONS",
    "ENGREF-DDIA-1E-ER6-COMMAND-EVENT-REPLAY",
    "ENGREF-DDIA-1E-ER6-IDEMPOTENT-EFFECTS",
}
EXPECTED_ADR0009_RULE_IDS = {
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
EXPECTED_ADR0009_FITNESS_IDS = {
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
EXPECTED_ADR0009_PRACTICE_IDS = {
    "ENGREF-PRAGMATIC-PROGRAMMER-1E-ORTHOGONALITY",
    "ENGREF-CLEAN-ARCHITECTURE-1E-DEPENDENCY-RULE",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-BOUNDARY-QUANTA",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-ORCHESTRATION-COUPLING",
    "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-FITNESS-FUNCTIONS",
}


class ContractFailure(Exception):
    pass


class DuplicateKeyLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: DuplicateKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ContractFailure(f"DUPLICATE_KEY:{key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


DuplicateKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=DuplicateKeyLoader)


def canonical_bytes(value: Any) -> bytes:
    return rfc8785.dumps(value)


def digest(value: dict[str, Any]) -> str:
    unsigned = {key: val for key, val in value.items() if key != "digest"}
    return "sha256:" + hashlib.sha256(canonical_bytes(unsigned)).hexdigest()


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise ContractFailure(f"{code}:{detail}")


def unique(items: list[Any], key: str, code: str) -> None:
    values = [item[key] for item in items]
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    require(not duplicates, code, ",".join(duplicates))


def validate_decision_binding(binding: dict[str, Any]) -> None:
    path = ROOT / binding["path"]
    require(path.is_file(), "DECISION_BINDING_SOURCE_MISSING", binding["path"])
    require(file_digest(path) == binding["digest"], "DECISION_BINDING_DIGEST_DRIFT", binding["path"])
    require(binding["status"] == "ACCEPTED_PAPER_DECISION", "DECISION_BINDING_STATUS", binding["decision_id"])
    require(
        binding["runtime_enactment_status"] == "NOT_ASSESSED",
        "DECISION_RUNTIME_OVERCLAIM",
        binding["decision_id"],
    )


def validate_path_contract_semantics(item: dict[str, Any]) -> None:
    require(
        item["governance_owner_context"] == item["owner_context"],
        "PATH_GOVERNANCE_OWNER_ALIAS",
        item["path_id"],
    )
    if item["responsibility_class"] == "ALLOWED_TEST_ROOT":
        require(
            item["governance_owner_context"] == "process_assurance",
            "PATH_TEST_GOVERNANCE_OWNER",
            item["path_id"],
        )
        require(
            item["semantic_owner_kind"] == "PARAMETERIZED_TEST_SUBJECT_OWNER",
            "PATH_TEST_BLANKET_SEMANTIC_OWNER",
            item["path_id"],
        )
        require(
            item["semantic_owner_context"] is None,
            "PATH_TEST_BLANKET_SEMANTIC_OWNER",
            item["path_id"],
        )
        require(
            item["semantic_owner_resolution"].startswith("Each leaf test must declare exactly one"),
            "PATH_TEST_LEAF_OWNER_RULE",
            item["path_id"],
        )
    elif item["semantic_owner_kind"] == "EXACT_CONTEXT":
        require(
            item["semantic_owner_context"] == item["owner_context"],
            "PATH_EXACT_SEMANTIC_OWNER",
            item["path_id"],
        )
    require(item["accountable_human_role"], "PATH_HUMAN_OWNER_MISSING", item["path_id"])
    require(item["required_reviewer_role"], "PATH_REVIEWER_MISSING", item["path_id"])
    require(item["data_ownership_refs"], "PATH_DATA_OWNER_REF_MISSING", item["path_id"])
    require(
        item["exception_metadata"]["required"]
        == bool(item.get("required_exception_class", "")),
        "PATH_EXCEPTION_REQUIREMENT_MISMATCH",
        item["path_id"],
    )


def validate_topology_exception_semantics(item: dict[str, Any]) -> None:
    require(
        not any(token in item["exact_path"] for token in ("*", "?", "[", "]")),
        "TOPOLOGY_EXCEPTION_WHOLE_LAYER_WILDCARD",
        item["exception_id"],
    )
    require(
        not item["exact_path"].startswith("/")
        and ".." not in Path(item["exact_path"]).parts,
        "TOPOLOGY_EXCEPTION_PATH_NOT_REPOSITORY_RELATIVE",
        item["exception_id"],
    )
    expires_at = datetime.fromisoformat(
        item["review_expires_at"].replace("Z", "+00:00")
    )
    require(
        expires_at > datetime.now(timezone.utc),
        "TOPOLOGY_EXCEPTION_EXPIRED",
        item["exception_id"],
    )


def validate_architecture_practice_profile(
    schemas: dict[str, dict[str, Any]],
    source_registry: dict[str, Any],
    element_ids: set[str],
    org_rule_ids: set[str],
    tdd_rule_ids: set[str],
    decision_ids: set[str],
    checks: Counter[str],
) -> dict[str, Any]:
    profile = load_json(ARCHITECTURE_PRACTICE_PROFILE)
    schema = schemas[
        "schemas/common/"
        "architecture-practice-application-profile-v1.schema.json"
    ]
    jsonschema.Draft202012Validator(schema).validate(profile)

    binding = profile["source_registry_binding"]
    source_path = ROOT / binding["path"]
    require(source_path.is_file(), "ARCH_PRACTICE_SOURCE_MISSING", binding["path"])
    require(
        hashlib.sha256(source_path.read_bytes()).hexdigest() == binding["sha256"],
        "ARCH_PRACTICE_SOURCE_DIGEST",
        binding["path"],
    )
    require(
        binding["registry_id"] == source_registry["registry_id"],
        "ARCH_PRACTICE_SOURCE_REGISTRY_ID",
        binding["registry_id"],
    )
    require(
        binding["version"] == source_registry["version"],
        "ARCH_PRACTICE_SOURCE_VERSION",
        binding["version"],
    )

    source_families = {
        row["source_family_id"]: row for row in source_registry["source_families"]
    }
    source_practices = {
        row["practice_id"]: row for row in source_registry["practices"]
    }
    require(
        len(source_families) == len(source_registry["source_families"]),
        "ARCH_PRACTICE_SOURCE_FAMILY_DUPLICATE",
        "",
    )
    require(
        len(source_practices) == len(source_registry["practices"]),
        "ARCH_PRACTICE_SOURCE_ID_DUPLICATE",
        "",
    )
    require(
        binding["required_source_family_count"] == len(source_families),
        "ARCH_PRACTICE_REQUIRED_FAMILY_COUNT",
        "",
    )
    require(
        binding["required_practice_count"] == len(source_practices),
        "ARCH_PRACTICE_REQUIRED_PRACTICE_COUNT",
        "",
    )
    require(
        set(profile["disposition_policy"]["allowed_dispositions"])
        == set(source_registry["profile_rule"]["required_family_dispositions"]),
        "ARCH_PRACTICE_DISPOSITION_POLICY",
        "",
    )

    family_rows = profile["family_dispositions"]
    unique(family_rows, "source_family_id", "ARCH_PRACTICE_FAMILY_DUPLICATE")
    require(
        {row["source_family_id"] for row in family_rows} == set(source_families),
        "ARCH_PRACTICE_FAMILY_SET",
        "",
    )
    applications = profile["practice_applications"]
    unique(applications, "practice_id", "ARCH_PRACTICE_ID_DUPLICATE")
    require(
        {row["practice_id"] for row in applications} == set(source_practices),
        "ARCH_PRACTICE_ID_SET",
        "",
    )
    applications_by_id = {row["practice_id"]: row for row in applications}
    for family_row in family_rows:
        family_id = family_row["source_family_id"]
        expected_ids = {
            practice_id
            for practice_id, practice in source_practices.items()
            if practice["source_family_id"] == family_id
        }
        require(
            set(family_row["practice_ids"]) == expected_ids,
            "ARCH_PRACTICE_FAMILY_PRACTICE_SET",
            family_id,
        )

    for row in applications:
        practice_id = row["practice_id"]
        require(
            row["source_family_id"]
            == source_practices[practice_id]["source_family_id"],
            "ARCH_PRACTICE_SOURCE_FAMILY_MISMATCH",
            practice_id,
        )
        require(
            set(row["architecture_element_ids"]) <= element_ids,
            "ARCH_PRACTICE_ELEMENT_UNKNOWN",
            practice_id,
        )
        require(
            set(row["adr_ids"]) <= decision_ids,
            "ARCH_PRACTICE_ADR_UNKNOWN",
            practice_id,
        )
        require(
            set(row["decision_ids"]) <= decision_ids,
            "ARCH_PRACTICE_DECISION_UNKNOWN",
            practice_id,
        )
        require(
            set(row["org_rule_ids"]) <= org_rule_ids,
            "ARCH_PRACTICE_ORG_RULE_UNKNOWN",
            practice_id,
        )
        require(
            set(row["tdd_rule_ids"]) <= tdd_rule_ids,
            "ARCH_PRACTICE_TDD_RULE_UNKNOWN",
            practice_id,
        )
        if row["disposition"] == "APPLICABLE":
            require(
                row["design_application_status"] in {"APPLIED", "PARTIAL"},
                "ARCH_PRACTICE_APPLICABLE_DESIGN_STATUS",
                practice_id,
            )
            require(
                row["runtime_enactment_status"] == "NOT_ASSESSED",
                "ARCH_PRACTICE_RUNTIME_OVERCLAIM",
                practice_id,
            )
            require(
                row["runtime_verification_required"] is True,
                "ARCH_PRACTICE_RUNTIME_VERIFICATION_MISSING",
                practice_id,
            )
            require(
                row["not_applicable_rationale"] == "",
                "ARCH_PRACTICE_APPLICABLE_NA_RATIONALE",
                practice_id,
            )
        elif row["disposition"] == "NOT_APPLICABLE":
            require(
                row["not_applicable_rationale"],
                "ARCH_PRACTICE_NA_RATIONALE_MISSING",
                practice_id,
            )
            require(
                row["design_application_status"] == "NOT_APPLICABLE"
                and row["runtime_enactment_status"] == "NOT_APPLICABLE",
                "ARCH_PRACTICE_NA_STATUS",
                practice_id,
            )
        else:
            require(
                row["material_unknown"] is True,
                "ARCH_PRACTICE_UNKNOWN_NOT_MATERIAL",
                practice_id,
            )
            require(
                row["design_application_status"] == "UNKNOWN",
                "ARCH_PRACTICE_UNKNOWN_DESIGN_STATUS",
                practice_id,
            )
        require(
            row["runtime_enactment_status"] not in {"PASS", "FAIL"},
            "ARCH_PRACTICE_RUNTIME_RESULT_FORGED",
            practice_id,
        )
        checks["architecture_practice_applications"] += 1

    unknown_rows = profile["material_unknowns"]
    unique(unknown_rows, "unknown_id", "ARCH_PRACTICE_UNKNOWN_ID_DUPLICATE")
    unknown_practice_ids = [
        practice_id
        for unknown in unknown_rows
        for practice_id in unknown["practice_ids"]
    ]
    require(
        len(unknown_practice_ids) == len(set(unknown_practice_ids)),
        "ARCH_PRACTICE_UNKNOWN_PRACTICE_DUPLICATE",
        "",
    )
    material_application_ids = {
        row["practice_id"] for row in applications if row["material_unknown"]
    }
    require(
        set(unknown_practice_ids) == material_application_ids,
        "ARCH_PRACTICE_UNKNOWN_PRACTICE_SET",
        "",
    )
    require(
        all(applications_by_id[practice_id]["disposition"] != "NOT_APPLICABLE"
            for practice_id in unknown_practice_ids),
        "ARCH_PRACTICE_NA_MARKED_UNKNOWN",
        "",
    )

    summary = profile["summary"]
    dispositions = Counter(row["disposition"] for row in applications)
    design_statuses = Counter(
        row["design_application_status"] for row in applications
    )
    runtime_statuses = Counter(
        row["runtime_enactment_status"] for row in applications
    )
    expected_summary = {
        "source_family_count": len(source_families),
        "practice_count": len(source_practices),
        "applicable_count": dispositions["APPLICABLE"],
        "not_applicable_count": dispositions["NOT_APPLICABLE"],
        "unknown_applicability_count": dispositions["UNKNOWN"],
        "design_applied_count": design_statuses["APPLIED"],
        "design_partial_count": design_statuses["PARTIAL"],
        "material_unknown_practice_count": len(material_application_ids),
        "runtime_not_assessed_count": runtime_statuses["NOT_ASSESSED"],
        "runtime_not_applicable_count": runtime_statuses["NOT_APPLICABLE"],
    }
    for key, expected_value in expected_summary.items():
        require(
            summary[key] == expected_value,
            "ARCH_PRACTICE_SUMMARY_DERIVATION",
            key,
        )
    require(
        summary["arithmetic_score"] is None,
        "ARCH_PRACTICE_ARITHMETIC_SCORE",
        "",
    )
    require(
        summary["sealing_eligible"] is False,
        "ARCH_PRACTICE_UNSUPPORTED_SEAL",
        "",
    )
    require(
        profile["subject"]["runtime_subject_included"] is False,
        "ARCH_PRACTICE_RUNTIME_SUBJECT_FORGED",
        "",
    )
    checks["architecture_practice_families"] = len(family_rows)
    checks["architecture_practice_material_unknowns"] = len(
        material_application_ids
    )
    checks["architecture_practice_mapped_elements"] = len(
        {
            element_id
            for row in applications
            for element_id in row["architecture_element_ids"]
        }
    )
    return profile


def require_supported_disposition(disposition: dict[str, Any], location: str) -> None:
    result = disposition["result"]
    require(result != "UNKNOWN", "TEST_PROFILE_MATERIAL_UNKNOWN", location)
    if result == "NOT_APPLICABLE":
        require(
            all(
                [
                    disposition["rule_id"],
                    disposition["reason"],
                    disposition["evidence_refs"],
                    disposition["approval_ref"],
                ]
            ),
            "TEST_PROFILE_UNSUPPORTED_NOT_APPLICABLE",
            location,
        )


def validate_test_profile_semantics(
    profile: dict[str, Any],
    practice_registry: dict[str, Any],
    *,
    fixture_mode: bool = False,
) -> None:
    if profile["profile_kind"] == "TASK":
        require(
            profile["subject_ref"] is not None,
            "TEST_PROFILE_TASK_SUBJECT_MISSING",
            profile["profile_id"],
        )
        require(
            profile["subject_digest"] is not None,
            "TEST_PROFILE_TASK_SUBJECT_MISSING",
            profile["profile_id"],
        )
    expected_categories = {
        (entry["category_id"], entry["root"])
        for entry in practice_registry["taxonomy"]
    }
    actual_categories = {
        (entry["category_id"], entry["root"])
        for entry in profile["category_coverage"]
    }
    require(
        len(actual_categories) == len(profile["category_coverage"]),
        "TEST_PROFILE_CATEGORY_DUPLICATE",
        profile["profile_id"],
    )
    require(
        actual_categories == expected_categories,
        "TEST_PROFILE_HAPPY_PATH_ONLY",
        profile["profile_id"],
    )
    require(
        set(profile["test_roots"]) == {entry["root"] for entry in practice_registry["taxonomy"]},
        "TEST_PROFILE_ROOT_SET",
        profile["profile_id"],
    )
    require(not profile["material_unknowns"], "TEST_PROFILE_MATERIAL_UNKNOWN", profile["profile_id"])
    require_supported_disposition(profile["applicability"], f"{profile['profile_id']}:profile")
    for row in profile["category_coverage"]:
        require_supported_disposition(
            row["applicability"],
            f"{profile['profile_id']}:category:{row['category_id']}",
        )
        if row["applicability"]["result"] == "NOT_APPLICABLE":
            require(
                row["execution_status"] == "NOT_APPLICABLE",
                "TEST_PROFILE_NA_EXECUTION_STATUS",
                row["category_id"],
            )
        else:
            require(
                row["execution_status"] != "NOT_APPLICABLE",
                "TEST_PROFILE_APPLICABLE_EXECUTION_STATUS",
                row["category_id"],
            )

    expected_lane_shapes = {
        row["category_id"]: {
            "category_id": row["category_id"],
            "semantic_owner_parameter": row["semantic_leaf_owner_parameter"],
            "path_patterns": row["mirror_patterns"],
            "mirrored_source_layers": row["mirrored_source_layers"],
            "shape_rule": row["shape_rule"],
        }
        for row in practice_registry["taxonomy"]
    }
    actual_lane_shapes = {
        row["category_id"]: row
        for row in profile["context_layer_mirroring"]["lane_shapes"]
    }
    require(
        len(actual_lane_shapes)
        == len(profile["context_layer_mirroring"]["lane_shapes"]),
        "TEST_PROFILE_LANE_SHAPE_DUPLICATE",
        profile["profile_id"],
    )
    require(
        actual_lane_shapes == expected_lane_shapes,
        "TEST_PROFILE_LANE_SHAPE_DRIFT",
        profile["profile_id"],
    )

    fixture_records = profile["fixture_records"]
    unique(fixture_records, "fixture_id", "TEST_PROFILE_FIXTURE_ID_DUPLICATE")
    unique(
        fixture_records,
        "canonical_path",
        "TEST_PROFILE_FIXTURE_PATH_DUPLICATE",
    )
    quarantine_records = profile["quarantine_records"]
    unique(
        quarantine_records,
        "quarantine_id",
        "TEST_PROFILE_QUARANTINE_ID_DUPLICATE",
    )
    validation_time = datetime.now(timezone.utc)
    for quarantine in quarantine_records:
        distribution = quarantine["observed_failure_distribution"]
        require(
            distribution["passes"]
            + distribution["failures"]
            + distribution["infrastructure_errors"]
            == distribution["total_runs"],
            "TEST_PROFILE_QUARANTINE_DISTRIBUTION",
            quarantine["quarantine_id"],
        )
        require(
            distribution["retry_passes"] <= distribution["retries"],
            "TEST_PROFILE_QUARANTINE_RETRY_COUNT",
            quarantine["quarantine_id"],
        )
        opened_at = datetime.fromisoformat(
            quarantine["opened_at"].replace("Z", "+00:00")
        )
        expires_at = datetime.fromisoformat(
            quarantine["expires_at"].replace("Z", "+00:00")
        )
        window_start = datetime.fromisoformat(
            distribution["window_start"].replace("Z", "+00:00")
        )
        window_end = datetime.fromisoformat(
            distribution["window_end"].replace("Z", "+00:00")
        )
        require(
            window_start <= window_end <= opened_at,
            "TEST_PROFILE_QUARANTINE_WINDOW",
            quarantine["quarantine_id"],
        )
        if quarantine["status"] == "ACTIVE":
            require(
                expires_at > validation_time,
                "TEST_PROFILE_QUARANTINE_EXPIRED",
                quarantine["quarantine_id"],
            )
            require(
                not quarantine["removal_evidence_refs"],
                "TEST_PROFILE_ACTIVE_QUARANTINE_REMOVAL_EVIDENCE",
                quarantine["quarantine_id"],
            )
        else:
            require(
                quarantine["removal_evidence_refs"],
                "TEST_PROFILE_REMOVED_QUARANTINE_EVIDENCE",
                quarantine["quarantine_id"],
            )
        require(
            quarantine["gate_disposition"] in {"BLOCKED", "UNKNOWN"}
            and quarantine["retry_passes_non_authoritative"] is True
            and quarantine["alternate_evidence_noncompensating"] is True,
            "TEST_PROFILE_QUARANTINE_RETRY_TO_PASS",
            quarantine["quarantine_id"],
        )

    deletion_records = profile["obsolete_test_deletions"]
    unique(
        deletion_records,
        "deletion_id",
        "TEST_PROFILE_DELETION_ID_DUPLICATE",
    )
    for deletion in deletion_records:
        for trace_key in (
            "requirement_trace_dispositions",
            "risk_trace_dispositions",
        ):
            trace_ids = [row["trace_id"] for row in deletion[trace_key]]
            require(
                len(trace_ids) == len(set(trace_ids)),
                "TEST_PROFILE_DELETION_TRACE_DUPLICATE",
                deletion["deletion_id"],
            )

    expected_failure_modes = set(practice_registry["failure_mode_classes"])
    actual_failure_modes = {row["failure_mode_class"] for row in profile["failure_mode_matrix"]}
    require(
        len(actual_failure_modes) == len(profile["failure_mode_matrix"]),
        "TEST_PROFILE_FAILURE_MODE_DUPLICATE",
        profile["profile_id"],
    )
    require(
        actual_failure_modes == expected_failure_modes,
        "TEST_PROFILE_HAPPY_PATH_ONLY",
        f"{profile['profile_id']}:failure_mode_matrix",
    )
    expected_assertions = set(practice_registry["expected_failure_assertions"])
    for row in profile["failure_mode_matrix"]:
        require_supported_disposition(
            row["applicability"],
            f"{profile['profile_id']}:failure:{row['failure_mode_class']}",
        )
        if row["applicability"]["result"] == "NOT_APPLICABLE":
            require(
                row["execution_status"] == "NOT_APPLICABLE",
                "TEST_PROFILE_NA_EXECUTION_STATUS",
                row["failure_mode_class"],
            )
        else:
            require(
                row["execution_status"] != "NOT_APPLICABLE",
                "TEST_PROFILE_APPLICABLE_EXECUTION_STATUS",
                row["failure_mode_class"],
            )
        require(
            set(row["required_assertions"]) == expected_assertions,
            "TEST_PROFILE_ASSERTION_COVERAGE",
            row["failure_mode_class"],
        )
        if profile["profile_kind"] == "TASK" and row["applicability"]["result"] == "APPLICABLE":
            require(row["precondition_refs"], "TEST_PROFILE_PRECONDITION_MISSING", row["failure_mode_class"])
            require(row["fault_input_refs"], "TEST_PROFILE_FAULT_INPUT_MISSING", row["failure_mode_class"])
            require(row["test_lanes"], "TEST_PROFILE_TEST_LANE_MISSING", row["failure_mode_class"])
            require(row["owner_id"], "TEST_PROFILE_OWNER_MISSING", row["failure_mode_class"])

    expected_partitions = {
        entry["partition_id"]: (entry["space_kind"], set(entry["required_methods"]))
        for entry in practice_registry["edge_case_partition_policy"]
    }
    actual_partitions = {entry["partition_id"]: entry for entry in profile["edge_case_partitions"]}
    require(
        len(actual_partitions) == len(profile["edge_case_partitions"]),
        "TEST_PROFILE_EDGE_PARTITION_DUPLICATE",
        profile["profile_id"],
    )
    require(
        set(actual_partitions) == set(expected_partitions),
        "TEST_PROFILE_EDGE_PARTITION_SET",
        profile["profile_id"],
    )
    for partition_id, (space_kind, methods) in expected_partitions.items():
        actual = actual_partitions[partition_id]
        require(actual["space_kind"] == space_kind, "TEST_PROFILE_EDGE_SPACE_KIND", partition_id)
        require(set(actual["required_methods"]) == methods, "TEST_PROFILE_EDGE_METHODS", partition_id)
        require_supported_disposition(
            actual["applicability"],
            f"{profile['profile_id']}:edge:{partition_id}",
        )
        if actual["applicability"]["result"] == "NOT_APPLICABLE":
            require(
                actual["execution_status"] == "NOT_APPLICABLE",
                "TEST_PROFILE_NA_EXECUTION_STATUS",
                partition_id,
            )
            require(
                not any(
                    actual[key]
                    for key in (
                        "seed_refs",
                        "corpus_refs",
                        "property_ids",
                        "invariant_ids",
                        "shrinking_reproduction_refs",
                        "remaining_unknowns",
                        "evidence_refs",
                    )
                ),
                "TEST_PROFILE_NA_EDGE_BOILERPLATE",
                partition_id,
            )
        else:
            require(
                actual["execution_status"] != "NOT_APPLICABLE",
                "TEST_PROFILE_APPLICABLE_EXECUTION_STATUS",
                partition_id,
            )
        if (
            profile["profile_kind"] == "TASK"
            and actual["applicability"]["result"] == "APPLICABLE"
        ):
            require(actual["property_ids"], "TEST_PROFILE_EDGE_PROPERTIES_MISSING", partition_id)
            require(actual["invariant_ids"], "TEST_PROFILE_EDGE_INVARIANTS_MISSING", partition_id)
            if space_kind == "OPEN":
                require(actual["seed_refs"], "TEST_PROFILE_EDGE_SEEDS_MISSING", partition_id)
                require(actual["corpus_refs"], "TEST_PROFILE_EDGE_CORPUS_MISSING", partition_id)
                require(
                    actual["shrinking_reproduction_refs"],
                    "TEST_PROFILE_EDGE_REPRODUCTION_MISSING",
                    partition_id,
                )

    expected_production_obligations = {
        row["obligation_id"]: row
        for row in practice_registry[
            "production_evidence_obligation_policy"
        ]
    }
    actual_production_obligations = {
        row["obligation_id"]: row
        for row in profile["production_evidence_obligations"]
    }
    require(
        len(actual_production_obligations)
        == len(profile["production_evidence_obligations"]),
        "TEST_PROFILE_PRODUCTION_OBLIGATION_DUPLICATE",
        profile["profile_id"],
    )
    require(
        set(actual_production_obligations)
        == set(expected_production_obligations),
        "TEST_PROFILE_PRODUCTION_OBLIGATION_SET",
        profile["profile_id"],
    )
    for obligation_id, expected_obligation in (
        expected_production_obligations.items()
    ):
        actual_obligation = actual_production_obligations[obligation_id]
        require(
            actual_obligation["required_evidence_fields"]
            == expected_obligation["required_evidence_fields"]
            and actual_obligation["task_selection_rule"]
            == expected_obligation["task_selection_rule"],
            "TEST_PROFILE_PRODUCTION_OBLIGATION_DRIFT",
            obligation_id,
        )
        require_supported_disposition(
            actual_obligation["applicability"],
            f"{profile['profile_id']}:production:{obligation_id}",
        )
        if actual_obligation["applicability"]["result"] == "NOT_APPLICABLE":
            require(
                actual_obligation["execution_status"] == "NOT_APPLICABLE",
                "TEST_PROFILE_NA_EXECUTION_STATUS",
                obligation_id,
            )
        else:
            require(
                actual_obligation["execution_status"] != "NOT_APPLICABLE",
                "TEST_PROFILE_APPLICABLE_EXECUTION_STATUS",
                obligation_id,
            )
    if (
        profile["profile_kind"] == "TASK"
        and profile["applicability"]["result"] == "APPLICABLE"
    ):
        require(
            actual_production_obligations[
                "BUILT_ARTIFACT_AND_COMPOSITION_IDENTITY"
            ]["applicability"]["result"]
            == "APPLICABLE",
            "TEST_PROFILE_BUILT_ARTIFACT_OBLIGATION_NA",
            profile["profile_id"],
        )

    practice_ids = {entry["practice_id"] for entry in practice_registry["entries"]}
    require(
        set(profile["traceability"]["practice_ids"]) == practice_ids,
        "TEST_PROFILE_PRACTICE_TRACE",
        profile["profile_id"],
    )
    require(
        not (
            profile["evidence_scope"] == "SYNTHETIC"
            and profile["runtime_evidence_status"] == "PASS"
        ),
        "TEST_PROFILE_SYNTHETIC_RUNTIME_PROMOTION",
        profile["profile_id"],
    )
    require(
        not (
            profile["runtime_evidence_status"] == "NOT_ASSESSED"
            and profile["sealing_eligible"]
        ),
        "TEST_PROFILE_UNASSESSED_SEALING",
        profile["profile_id"],
    )
    if profile["profile_kind"] == "TASK":
        for key in ("requirement_ids", "risk_ids", "practice_ids"):
            require(profile["traceability"][key], "TEST_PROFILE_TRACEABILITY_MISSING", key)
        transition_row = next(
            row
            for row in profile["failure_mode_matrix"]
            if row["failure_mode_class"] == "COMMANDS_AND_STATE_TRANSITIONS"
        )
        require(
            transition_row["transition_ids"] == profile["traceability"]["transition_ids"],
            "TEST_PROFILE_TRANSITION_TRACE_MISMATCH",
            profile["profile_id"],
        )
        if transition_row["applicability"]["result"] == "APPLICABLE":
            require(
                transition_row["transition_ids"],
                "TEST_PROFILE_FINITE_TRANSITION_COVERAGE_MISSING",
                profile["profile_id"],
            )
        else:
            require(
                not transition_row["transition_ids"],
                "TEST_PROFILE_NA_TRANSITION_BOILERPLATE",
                profile["profile_id"],
            )
        applicable_rows = [
            row
            for row in profile["category_coverage"] + profile["failure_mode_matrix"]
            if row["applicability"]["result"] == "APPLICABLE"
        ] + [
            row
            for row in profile["edge_case_partitions"]
            if row["applicability"]["result"] == "APPLICABLE"
        ] + [
            row
            for row in profile["production_evidence_obligations"]
            if row["applicability"]["result"] == "APPLICABLE"
        ]
        statuses = [row["execution_status"] for row in applicable_rows]
        if profile["applicability"]["result"] == "NOT_APPLICABLE":
            derived_result = "NOT_APPLICABLE"
        elif statuses and all(status == "NOT_ASSESSED" for status in statuses):
            derived_result = "NOT_ASSESSED"
        elif any(status == "FAIL" for status in statuses):
            derived_result = "FAIL"
        elif any(status in {"UNKNOWN", "NOT_ASSESSED"} for status in statuses):
            derived_result = "UNKNOWN"
        elif statuses and all(status == "PASS" for status in statuses):
            derived_result = "PASS"
        else:
            derived_result = "UNKNOWN"
        require(
            profile["derived_result"] == derived_result,
            "TEST_PROFILE_DERIVED_RESULT_MISMATCH",
            profile["profile_id"],
        )
        if derived_result == "PASS":
            require(
                profile["runtime_evidence_status"] == "PASS",
                "TEST_PROFILE_PASS_RUNTIME_STATUS",
                profile["profile_id"],
            )
            require(
                profile["evidence_scope"] in {"RUNTIME", "MIXED"},
                "TEST_PROFILE_PASS_EVIDENCE_SCOPE",
                profile["profile_id"],
            )
            for row in applicable_rows:
                require(row["evidence_refs"], "TEST_PROFILE_PASS_ROW_EVIDENCE_MISSING", profile["profile_id"])
            required_global_evidence_refs: set[str] = set()
            for obligation in profile["production_evidence_obligations"]:
                if obligation["applicability"]["result"] != "APPLICABLE":
                    continue
                for evidence_field in obligation[
                    "required_evidence_fields"
                ]:
                    require(
                        profile["evidence"][evidence_field],
                        "TEST_PROFILE_PRODUCTION_EVIDENCE_MISSING",
                        f"{obligation['obligation_id']}:{evidence_field}",
                    )
                    required_global_evidence_refs.update(
                        profile["evidence"][evidence_field]
                    )
            require(profile["evidence_bindings"], "TEST_PROFILE_PASS_BINDINGS_MISSING", profile["profile_id"])
            bound_refs = {binding["evidence_ref"] for binding in profile["evidence_bindings"]}
            required_refs = {
                ref
                for row in applicable_rows
                for ref in row["evidence_refs"]
            } | required_global_evidence_refs
            require(required_refs <= bound_refs, "TEST_PROFILE_PASS_BINDING_INCOMPLETE", profile["profile_id"])
            for binding in profile["evidence_bindings"]:
                require(binding["subject_ref"] == profile["subject_ref"], "TEST_PROFILE_EVIDENCE_SUBJECT_REF", binding["evidence_ref"])
                require(binding["subject_digest"] == profile["subject_digest"], "TEST_PROFILE_EVIDENCE_SUBJECT_DIGEST", binding["evidence_ref"])
                require(binding["freshness_status"] == "CURRENT", "TEST_PROFILE_EVIDENCE_STALE", binding["evidence_ref"])
                require(binding["result"] == "PASS", "TEST_PROFILE_EVIDENCE_NOT_PASS", binding["evidence_ref"])
            require(profile["sealing_eligible"] is True, "TEST_PROFILE_PASS_NOT_SEALABLE", profile["profile_id"])
        else:
            require(profile["runtime_evidence_status"] != "PASS", "TEST_PROFILE_NONPASS_RUNTIME_PASS", profile["profile_id"])
            require(profile["sealing_eligible"] is False, "TEST_PROFILE_NONPASS_SEALING", profile["profile_id"])
    if not fixture_mode:
        require(digest(profile) == profile["digest"], "TEST_PROFILE_DIGEST_MISMATCH", profile["profile_id"])


def forbidden_test_constructs(source: str) -> set[str]:
    tree = ast.parse(source)
    violations: set[str] = set()
    test_condition = re.compile(
        r"\b(TESTING|TEST_MODE|UNIT_TEST|PYTEST_CURRENT_TEST|RANEX_TEST[A-Z0-9_]*)\b",
        flags=re.IGNORECASE,
    )
    bypass_name = re.compile(
        r"^(?:test_)?(?:bypass|skip)_(?:policy|authorization|permit|gate|reducer|transition|evidence)$",
        flags=re.IGNORECASE,
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and test_condition.search(ast.unparse(node.test)):
            violations.add("TEST_ONLY_PRODUCTION_BRANCH")
        if isinstance(node, ast.keyword) and node.arg and bypass_name.fullmatch(node.arg):
            violations.add("TEST_BYPASS")
        if isinstance(node, (ast.Name, ast.arg)) and bypass_name.fullmatch(node.id if isinstance(node, ast.Name) else node.arg):
            violations.add("TEST_BYPASS")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if bypass_name.fullmatch(node.value):
                violations.add("TEST_BYPASS")
    return violations


def imported_modules(path: Path, source: str) -> set[tuple[str, ...]]:
    tree = ast.parse(source)
    relative = path.relative_to(ROOT / "src").with_suffix("")
    module_parts = list(relative.parts)
    package_parts = module_parts if path.name == "__init__.py" else module_parts[:-1]
    imports: set[tuple[str, ...]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(tuple(alias.name.split(".")) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                keep = max(0, len(package_parts) - (node.level - 1))
                base = package_parts[:keep]
                target = base + (node.module.split(".") if node.module else [])
            else:
                target = node.module.split(".") if node.module else []
            if target:
                imports.add(tuple(target))
    return imports


def graph_has_cycle(edges: dict[str, set[str]]) -> bool:
    active: set[str] = set()
    complete: set[str] = set()

    def visit(node: str) -> bool:
        if node in active:
            return True
        if node in complete:
            return False
        active.add(node)
        if any(visit(target) for target in edges.get(node, set())):
            return True
        active.remove(node)
        complete.add(node)
        return False

    return any(visit(node) for node in sorted(edges))


def validate_adr9_projections(
    schemas: dict[str, dict[str, Any]],
    context_ids: set[str],
    checks: Counter[str],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    dependency_registry = load_json(
        CONTRACTS / "context-dependency-edges.json"
    )
    require(
        dependency_registry["dependency_graph_id"]
        == "RANEX-CONTEXT-DEPENDENCIES-1.0",
        "ADR9_DEPENDENCY_GRAPH_ID",
        "",
    )
    require(
        dependency_registry["default_policy"]
        == "DENY_UNLESS_EXACT_EDGE_REGISTERED",
        "ADR9_DEPENDENCY_DEFAULT_POLICY",
        "",
    )
    require(
        dependency_registry["expected_edge_count"] == 67,
        "ADR9_DEPENDENCY_DECLARED_COUNT",
        "",
    )
    edges = dependency_registry["entries"]
    require(len(edges) == 67, "ADR9_DEPENDENCY_EDGE_COUNT", str(len(edges)))
    unique(edges, "edge_id", "ADR9_DEPENDENCY_EDGE_ID_DUPLICATE")
    pairs = [(row["caller"], row["callee"]) for row in edges]
    require(
        len(pairs) == len(set(pairs)),
        "ADR9_DEPENDENCY_PAIR_DUPLICATE",
        "",
    )
    edge_schema = schemas[
        "schemas/common/context-dependency-edge-v1.schema.json"
    ]
    declared_graph: dict[str, set[str]] = defaultdict(set)
    for row in edges:
        jsonschema.Draft202012Validator(edge_schema).validate(row)
        require(
            row["caller"] in context_ids and row["callee"] in context_ids,
            "ADR9_DEPENDENCY_CONTEXT_UNKNOWN",
            row["edge_id"],
        )
        require(
            row["caller_owner"] == row["caller"]
            and row["callee_owner"] == row["callee"],
            "ADR9_DEPENDENCY_OWNER_MISMATCH",
            row["edge_id"],
        )
        declared_graph[row["caller"]].add(row["callee"])
        checks["declared_context_dependency_edges"] += 1
    require(
        not graph_has_cycle(declared_graph),
        "ADR9_DECLARED_DEPENDENCY_CYCLE",
        "",
    )
    require(
        dependency_registry["declared_cycle_result"] == "PASS",
        "ADR9_DECLARED_CYCLE_RESULT",
        "",
    )
    require(
        dependency_registry["actual_import_scan_status"] == "NOT_ASSESSED"
        and dependency_registry["actual_import_pairs"] == []
        and dependency_registry["actual_subset_result"] == "NOT_ASSESSED"
        and dependency_registry["actual_cycle_result"] == "NOT_ASSESSED",
        "ADR9_ACTUAL_IMPORT_OVERCLAIM",
        "",
    )
    require(
        dependency_registry["runtime_validation_status"] == "NOT_ASSESSED",
        "ADR9_DEPENDENCY_RUNTIME_OVERCLAIM",
        "",
    )
    validate_decision_binding(dependency_registry["decision_binding"])

    boundary_registry = load_json(
        CONTRACTS / "context-boundary-fitness.json"
    )
    require(
        boundary_registry["boundary_fit_set_id"]
        == "RANEX-CONTEXT-BOUNDARY-FIT-1.0",
        "ADR9_BOUNDARY_SET_ID",
        "",
    )
    require(
        boundary_registry["expected_context_count"] == 34,
        "ADR9_BOUNDARY_DECLARED_COUNT",
        "",
    )
    boundary_rows = boundary_registry["entries"]
    require(
        len(boundary_rows) == 34,
        "ADR9_BOUNDARY_ROW_COUNT",
        str(len(boundary_rows)),
    )
    unique(boundary_rows, "context_id", "ADR9_BOUNDARY_CONTEXT_DUPLICATE")
    require(
        {row["context_id"] for row in boundary_rows} == context_ids,
        "ADR9_BOUNDARY_CONTEXT_SET",
        "",
    )
    boundary_schema = schemas[
        "schemas/common/context-boundary-fit-v1.schema.json"
    ]
    for row in boundary_rows:
        jsonschema.Draft202012Validator(boundary_schema).validate(row)
        require(
            row["owner"] == row["context_id"],
            "ADR9_BOUNDARY_OWNER_MISMATCH",
            row["context_id"],
        )
        checks["context_boundary_fit_rows"] += 1
    adr9_rules = boundary_registry["rules"]
    unique(adr9_rules, "rule_id", "ADR9_RULE_DUPLICATE")
    require(
        {row["rule_id"] for row in adr9_rules}
        == EXPECTED_ADR0009_RULE_IDS,
        "ADR9_RULE_SET",
        "",
    )
    require(
        boundary_registry["rule_set_id"]
        == "RANEX-BOUNDARY-FITNESS-1.0",
        "ADR9_RULE_SET_ID",
        "",
    )
    for row in adr9_rules:
        require(
            row["definition_status"] == "DEFINED"
            and row["runtime_evidence_status"] == "NOT_ASSESSED",
            "ADR9_RULE_RUNTIME_OVERCLAIM",
            row["rule_id"],
        )
        checks["adr9_rules"] += 1
    fitness_rows = boundary_registry["fitness_obligations"]
    unique(fitness_rows, "fitness_id", "ADR9_FITNESS_DUPLICATE")
    require(
        {row["fitness_id"] for row in fitness_rows}
        == EXPECTED_ADR0009_FITNESS_IDS,
        "ADR9_FITNESS_SET",
        "",
    )
    for row in fitness_rows:
        require(
            row["result"] == "NOT_ASSESSED"
            and row["evidence_refs"] == []
            and row["noncompensating"] is True,
            "ADR9_FITNESS_OVERCLAIM",
            row["fitness_id"],
        )
        checks["adr9_fitness_obligations"] += 1
    require(
        set(boundary_registry["engineering_practice_ids"])
        == EXPECTED_ADR0009_PRACTICE_IDS,
        "ADR9_ENGINEERING_PRACTICE_SET",
        "",
    )
    require(
        boundary_registry["runtime_validation_status"] == "NOT_ASSESSED",
        "ADR9_BOUNDARY_RUNTIME_OVERCLAIM",
        "",
    )
    validate_decision_binding(boundary_registry["decision_binding"])

    coupling_policy = load_json(CONTRACTS / "context-coupling-policy.json")
    jsonschema.Draft202012Validator(
        schemas["schemas/common/context-coupling-policy-v1.schema.json"]
    ).validate(coupling_policy)
    require(
        coupling_policy["coupling_policy_id"] == "RANEX-GE-COUPLING-1.0"
        and coupling_policy["subject_context"] == "governed_execution",
        "ADR9_COUPLING_POLICY_ID",
        "",
    )
    expected_measures = {
        "GE-RESPONSIBILITY-COUNT",
        "GE-STATIC-FAN-OUT",
        "GE-STATIC-FAN-IN",
        "GE-INTERACTION-COUPLING",
        "GE-CHANGE-COUPLING",
        "GE-OWNERSHIP-CONCENTRATION",
    }
    unique(coupling_policy["measures"], "measure_id", "ADR9_COUPLING_MEASURE_DUPLICATE")
    require(
        {row["measure_id"] for row in coupling_policy["measures"]}
        == expected_measures,
        "ADR9_COUPLING_MEASURE_SET",
        "",
    )
    require(
        coupling_policy["declared_static_fan_out"] == 10
        and coupling_policy["declared_static_fan_in"] == 3,
        "ADR9_COUPLING_STATIC_COUNTS",
        "",
    )
    require(
        all(
            row["result"] == "NOT_ASSESSED"
            and row["evidence_refs"] == []
            for row in coupling_policy["measures"]
        ),
        "ADR9_COUPLING_RUNTIME_OVERCLAIM",
        "",
    )
    require(
        set(coupling_policy["rule_ids"])
        == {
            "ARCH-COUPLING-001",
            "ARCH-COUPLING-002",
            "ARCH9-NONCOMP-001",
        },
        "ADR9_COUPLING_RULE_SET",
        "",
    )
    require(
        set(coupling_policy["fitness_ids"])
        == {
            "FF-COUPLING-001",
            "FF-COUPLING-002",
            "FF-ARCH9-NONCOMP-001",
        },
        "ADR9_COUPLING_FITNESS_SET",
        "",
    )
    validate_decision_binding(coupling_policy["decision_binding"])
    checks["coupling_measures"] = len(coupling_policy["measures"])

    feedback_policy = load_json(CONTRACTS / "feedback-fitness.json")
    jsonschema.Draft202012Validator(
        schemas["schemas/common/feedback-fitness-policy-v1.schema.json"]
    ).validate(feedback_policy)
    require(
        feedback_policy["feedback_policy_id"] == "RANEX-TDD-FEEDBACK-1.0",
        "ADR9_FEEDBACK_POLICY_ID",
        "",
    )
    expected_objectives = {
        "TDD-FEEDBACK-FAST-P50",
        "TDD-FEEDBACK-FAST-P95",
        "TDD-FEEDBACK-PREVERIFY-P50",
        "TDD-FEEDBACK-PREVERIFY-P95",
    }
    unique(feedback_policy["objectives"], "objective_id", "ADR9_FEEDBACK_OBJECTIVE_DUPLICATE")
    require(
        {row["objective_id"] for row in feedback_policy["objectives"]}
        == expected_objectives,
        "ADR9_FEEDBACK_OBJECTIVE_SET",
        "",
    )
    require(
        all(
            row["result"] == "NOT_ASSESSED"
            and row["evidence_refs"] == []
            for row in feedback_policy["objectives"]
        )
        and feedback_policy["reference_host_profile_status"]
        == "NOT_ASSESSED",
        "ADR9_FEEDBACK_RUNTIME_OVERCLAIM",
        "",
    )
    require(
        feedback_policy["selection"]["manifest_required"] is True
        and feedback_policy["selection"]["omission_status"]
        == "UNKNOWN_BLOCKING"
        and feedback_policy["sharding"]["determinism_required"] is True,
        "ADR9_FEEDBACK_SELECTION_SHARDING",
        "",
    )
    require(
        set(feedback_policy["rule_ids"])
        == {
            "TDD-FEEDBACK-001",
            "TDD-FEEDBACK-002",
            "ARCH9-NONCOMP-001",
        },
        "ADR9_FEEDBACK_RULE_SET",
        "",
    )
    require(
        set(feedback_policy["fitness_ids"])
        == {
            "FF-FEEDBACK-001",
            "FF-FEEDBACK-002",
            "FF-ARCH9-NONCOMP-001",
        },
        "ADR9_FEEDBACK_FITNESS_SET",
        "",
    )
    validate_decision_binding(feedback_policy["decision_binding"])
    checks["feedback_objectives"] = len(feedback_policy["objectives"])
    return (
        dependency_registry,
        boundary_registry,
        coupling_policy,
        feedback_policy,
    )


def validate_cross_context_import_target(
    path: Path,
    target: tuple[str, ...],
    current_context: str | None,
    context_ids: set[str],
) -> str | None:
    if not (
        current_context
        and len(target) >= 2
        and target[0] == "ranex"
        and target[1] in context_ids
        and target[1] != current_context
    ):
        return None
    target_layer = target[2] if len(target) > 2 else ""
    require(
        target_layer == "api",
        "TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT",
        f"{path.relative_to(ROOT)}:{'.'.join(target)}",
    )
    return target[1]


def validate_production_topology(checks: Counter[str]) -> None:
    source_root = ROOT / "src" / "ranex"
    tests_root = ROOT / "tests"
    context_registry = load_json(CONTRACTS / "contexts.json")
    context_ids = {entry["context_id"] for entry in context_registry["entries"]}
    topology = load_json(CONTRACTS / "topology-rules.json")
    test_practices = load_json(CONTRACTS / "test-practices.json")
    allowed_test_roots = {entry["root"].split("/", 1)[1] for entry in test_practices["taxonomy"]}

    if tests_root.is_dir():
        observed_roots = {
            path.name
            for path in tests_root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        }
        require(observed_roots <= allowed_test_roots, "TDD_TEST_ROOT_FORBIDDEN", ",".join(sorted(observed_roots - allowed_test_roots)))
        require("persistence" not in observed_roots, "TDD_PERSISTENCE_ROOT_FORBIDDEN", "")
        require("crash" not in observed_roots, "TDD_CRASH_ROOT_FORBIDDEN", "")
        checks["observed_test_roots"] = len(observed_roots)
    else:
        checks["observed_test_roots"] = 0

    if not source_root.is_dir():
        checks["production_topology_files_scanned"] = 0
        return

    composition_root = ROOT / topology["layout_profile"]["composition_root"]
    require(composition_root.is_file(), "TOPOLOGY_COMPOSITION_ROOT_MISSING", str(composition_root.relative_to(ROOT)))
    central_adapters = source_root / "adapters"
    central_adapter_files = (
        sorted(central_adapters.rglob("*.py"))
        if central_adapters.is_dir()
        else []
    )
    host_edge_exceptions = [
        item
        for item in topology["exceptions"]
        if item["exception_class"] == "HOST_EDGE_ADAPTER"
    ]
    for central_adapter_file in central_adapter_files:
        relative_adapter_path = str(central_adapter_file.relative_to(ROOT))
        matching_exceptions = [
            item
            for item in host_edge_exceptions
            if item["exact_path"] == relative_adapter_path
        ]
        require(
            len(matching_exceptions) == 1,
            "TOPOLOGY_HOST_EDGE_EXCEPTION_EXACT_BINDING",
            relative_adapter_path,
        )

    edges: dict[str, set[str]] = defaultdict(set)
    source_files = sorted(source_root.rglob("*.py"))
    for path in source_files:
        relative = path.relative_to(source_root)
        parts = relative.parts
        current_context = parts[0] if parts and parts[0] in context_ids else None
        if current_context and len(parts) > 1 and parts[1] == "ports":
            raise ContractFailure(f"TOPOLOGY_SIBLING_PORTS_FORBIDDEN:{path.relative_to(ROOT)}")
        source = path.read_text(encoding="utf-8")
        imports = imported_modules(path, source)
        for target in imports:
            if target[0] in {"legacy", "hermes"} and current_context != "compatibility":
                raise ContractFailure(f"TOPOLOGY_LEGACY_IMPORT_FORBIDDEN:{path.relative_to(ROOT)}:{'.'.join(target)}")
            if not (len(target) >= 2 and target[0] == "ranex" and target[1] in context_ids):
                continue
            target_context = target[1]
            target_layer = target[2] if len(target) > 2 else ""
            cross_context_target = validate_cross_context_import_target(
                path,
                target,
                current_context,
                context_ids,
            )
            if cross_context_target:
                edges[current_context].add(cross_context_target)
            if current_context and len(parts) > 1 and parts[1] == "domain":
                require(
                    target_context == current_context and target_layer == "domain",
                    "TOPOLOGY_DOMAIN_IMPORT_FORBIDDEN",
                    f"{path.relative_to(ROOT)}:{'.'.join(target)}",
                )
            if (
                target_layer == "adapters"
                and path != composition_root
                and not (current_context == target_context and len(parts) > 1 and parts[1] == "adapters")
            ):
                raise ContractFailure(
                    f"TOPOLOGY_ADAPTER_WIRING_OUTSIDE_COMPOSITION:{path.relative_to(ROOT)}:{'.'.join(target)}"
                )
        checks["production_topology_files_scanned"] += 1
    declared_pairs = {
        (edge["caller"], edge["callee"])
        for edge in load_json(
            CONTRACTS / "context-dependency-edges.json"
        )["entries"]
    }
    actual_pairs = {
        (source, target)
        for source, targets in edges.items()
        for target in targets
    }
    require(
        actual_pairs <= declared_pairs,
        "TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE",
        ",".join(f"{source}->{target}" for source, target in sorted(actual_pairs - declared_pairs)),
    )
    require(not graph_has_cycle(edges), "TOPOLOGY_CONTEXT_IMPORT_CYCLE", "")


def validate_schema_documents(checks: Counter[str]) -> dict[str, dict[str, Any]]:
    schema_files = sorted(SCHEMAS.rglob("*.schema.json"))
    require(len(schema_files) >= 46, "SCHEMA_DENOMINATOR", str(len(schema_files)))
    schemas: dict[str, dict[str, Any]] = {}
    ids: list[str] = []
    for path in schema_files:
        schema = load_json(path)
        jsonschema.Draft202012Validator.check_schema(schema)
        require(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", "SCHEMA_DRAFT", str(path))
        require("$id" in schema, "SCHEMA_ID_MISSING", str(path))
        ids.append(schema["$id"])
        schemas[str(path.relative_to(ROOT))] = schema
        checks["schema_documents"] += 1
    require(len(ids) == len(set(ids)), "SCHEMA_ID_DUPLICATE", "duplicate $id")
    return schemas


def validate_templates(schemas: dict[str, dict[str, Any]], checks: Counter[str]) -> dict[str, str]:
    artifact_registry = load_json(CONTRACTS / "artifact-types.json")
    entries = artifact_registry["entries"]
    require(len(entries) == 36, "ARTIFACT_TYPE_DENOMINATOR", str(len(entries)))
    unique(entries, "artifact_type", "ARTIFACT_TYPE_DUPLICATE")
    unique(entries, "template_path", "ARTIFACT_TEMPLATE_DUPLICATE")
    unique(entries, "schema_path", "ARTIFACT_SCHEMA_DUPLICATE")
    seen: dict[str, str] = {}
    for entry in entries:
        template_path = ROOT / entry["template_path"]
        schema_path = entry["schema_path"]
        require(template_path.exists(), "TEMPLATE_MISSING", entry["template_path"])
        require(schema_path in schemas, "ARTIFACT_SCHEMA_MISSING", schema_path)
        instance = load_yaml(template_path)
        jsonschema.Draft202012Validator(schemas[schema_path]).validate(instance)
        require(instance["artifact_type"] == entry["artifact_type"], "ARTIFACT_TYPE_MISMATCH", entry["template_path"])
        require(entry["canonical_producer"] != "", "PRODUCER_MISSING", entry["artifact_type"])
        seen[entry["artifact_type"]] = schema_path
        checks["governed_templates"] += 1
    require(len(seen) == 36, "TEMPLATE_DENOMINATOR", str(len(seen)))
    return seen


def validate_registry_manifest(checks: Counter[str]) -> None:
    manifest = load_json(CONTRACTS / "registry-manifest.json")
    paths = [entry["path"] for entry in manifest["entries"]]
    require("architecture/contracts/registry-manifest.json" not in paths, "MANIFEST_SELF_REFERENCE", "registry manifest lists itself")
    require(paths == sorted(paths), "MANIFEST_NOT_SORTED", "registry entries")
    unique(manifest["entries"], "path", "MANIFEST_DUPLICATE_PATH")
    expected_files = sorted(
        str(path.relative_to(ROOT))
        for path in CONTRACTS.glob("*.json")
        if path.name != "registry-manifest.json"
    )
    require(paths == expected_files, "MANIFEST_INCOMPLETE", f"expected={len(expected_files)} actual={len(paths)}")
    for entry in manifest["entries"]:
        require(file_digest(ROOT / entry["path"]) == entry["digest"], "MANIFEST_DIGEST_MISMATCH", entry["path"])
        checks["registry_manifest_entries"] += 1


def validate_registries(
    schemas: dict[str, dict[str, Any]],
    checks: Counter[str],
) -> tuple[list[dict[str, str]], list[str]]:
    context_registry = load_json(CONTRACTS / "contexts.json")
    contexts = context_registry["entries"]
    context_ids = {entry["context_id"] for entry in contexts}
    unique(contexts, "context_id", "CONTEXT_DUPLICATE")
    require(len(contexts) == 34, "CONTEXT_DENOMINATOR", str(len(contexts)))
    require(context_registry["context_count"] == len(contexts), "CONTEXT_DECLARED_COUNT", "")
    require(
        context_registry["topology_rule_set_id"] == "RANEX-TOPOLOGY-1.0",
        "CONTEXT_TOPOLOGY_RULE_SET",
        "",
    )
    validate_decision_binding(context_registry["topology_decision_binding"])
    require(context_registry["topology_exceptions"] == [], "CONTEXT_EXCEPTION_FABRICATED", "")
    require(
        context_registry["runtime_enactment_status"] == "NOT_ASSESSED",
        "CONTEXT_RUNTIME_OVERCLAIM",
        "",
    )
    for context in contexts:
        context_id = context["context_id"]
        require(
            context["canonical_root"] == f"src/ranex/{context_id}/",
            "CONTEXT_CANONICAL_ROOT",
            context_id,
        )
        require(
            context["public_api_path"] == f"src/ranex/{context_id}/api/",
            "CONTEXT_PUBLIC_API_PATH",
            context_id,
        )
        require(
            context["port_path"] == f"src/ranex/{context_id}/application/ports/",
            "CONTEXT_PORT_PATH",
            context_id,
        )
        require(
            context["context_adapter_path"] == f"src/ranex/{context_id}/adapters/<technology>/",
            "CONTEXT_ADAPTER_PATH",
            context_id,
        )
        require(context["layer_enactment_status"] == "NOT_ASSESSED", "CONTEXT_LAYER_OVERCLAIM", context_id)
        require(
            context["declared_dependency_graph_status"] == "DEFINED",
            "CONTEXT_DEPENDENCY_DEFINITION_STATUS",
            context_id,
        )
        require(context["topology_exception_ids"] == [], "CONTEXT_EXCEPTION_FABRICATED", context_id)

    topology = load_json(CONTRACTS / "topology-rules.json")
    topology_rules = topology["entries"]
    unique(topology_rules, "rule_id", "TOPOLOGY_RULE_DUPLICATE")
    require(
        {rule["rule_id"] for rule in topology_rules} == EXPECTED_ORG_RULE_IDS,
        "TOPOLOGY_RULE_SET",
        "",
    )
    require(topology["rule_set_id"] == "RANEX-TOPOLOGY-1.0", "TOPOLOGY_RULE_SET_ID", "")
    require(
        {item["exception_class"] for item in topology["exception_classes"]}
        == EXPECTED_TOPOLOGY_EXCEPTION_CLASSES,
        "TOPOLOGY_EXCEPTION_CLASS_SET",
        "",
    )
    require(
        topology["exception_record_schema_path"]
        == "schemas/common/topology-exception-v1.schema.json",
        "TOPOLOGY_EXCEPTION_SCHEMA_PATH",
        "",
    )
    topology_exception_schema = schemas[
        "schemas/common/topology-exception-v1.schema.json"
    ]
    unique(topology["exceptions"], "exception_id", "TOPOLOGY_EXCEPTION_ID_DUPLICATE")
    unique(topology["exceptions"], "exact_path", "TOPOLOGY_EXCEPTION_PATH_DUPLICATE")
    for exception in topology["exceptions"]:
        jsonschema.Draft202012Validator(topology_exception_schema).validate(
            exception
        )
        validate_topology_exception_semantics(exception)
        require(
            set(exception["rule_ids"]) <= EXPECTED_ORG_RULE_IDS,
            "TOPOLOGY_EXCEPTION_RULE_UNKNOWN",
            exception["exception_id"],
        )
    require(topology["fitness_refs"] == [f"FF-ORG-{index:03d}" for index in range(1, 9)], "TOPOLOGY_FITNESS_SET", "")
    for binding in topology["decision_bindings"]:
        validate_decision_binding(binding)
    layout = topology["layout_profile"]
    require(layout["ports_path"] == "src/ranex/<context>/application/ports/", "TOPOLOGY_PORT_PATH", "")
    require(layout["sibling_ports_forbidden"] is True, "TOPOLOGY_SIBLING_PORTS", "")
    require(
        layout["context_adapter_path"] == "src/ranex/<context>/adapters/<technology>/",
        "TOPOLOGY_CONTEXT_ADAPTER_PATH",
        "",
    )
    require(
        layout["host_edge_adapter_path"] == "src/ranex/adapters/<boundary>/<technology>/",
        "TOPOLOGY_HOST_EDGE_PATH",
        "",
    )
    require(
        layout["host_edge_adapter_exception_class"] == "HOST_EDGE_ADAPTER",
        "TOPOLOGY_HOST_EDGE_EXCEPTION",
        "",
    )
    require(layout["composition_root"] == "src/ranex/bootstrap/composition.py", "TOPOLOGY_COMPOSITION_ROOT", "")
    require(layout["tiny_context_policy"]["current_exemption_count"] == 0, "TOPOLOGY_TINY_EXCEPTION_COUNT", "")
    dependency_graph = topology["dependency_graph"]
    require(
        dependency_graph["default_cross_context_policy"] == "DENY_UNLESS_EXACT_EDGE_REGISTERED",
        "TOPOLOGY_DEPENDENCY_DEFAULT",
        "",
    )
    require(
        dependency_graph["declaration_status"] == "DEFINED",
        "TOPOLOGY_DEPENDENCY_DECLARATION_STATUS",
        "",
    )
    require(
        dependency_graph["registry_ref"]
        == "architecture/contracts/context-dependency-edges.json",
        "TOPOLOGY_DEPENDENCY_REGISTRY_REF",
        "",
    )
    require(
        dependency_graph["registry_id"]
        == "REG-CONTEXT-DEPENDENCY-EDGES-001",
        "TOPOLOGY_DEPENDENCY_REGISTRY_ID",
        "",
    )
    require(
        dependency_graph["declared_edge_count"] == 67,
        "TOPOLOGY_DEPENDENCY_EDGE_COUNT",
        "",
    )
    require(dependency_graph["edges"] == [], "TOPOLOGY_DEPENDENCY_EDGE_FABRICATED", "")
    require(dependency_graph["source_scan_status"] == "NOT_ASSESSED", "TOPOLOGY_SOURCE_SCAN_OVERCLAIM", "")
    require(dependency_graph["cycle_result"] == "NOT_ASSESSED", "TOPOLOGY_CYCLE_OVERCLAIM", "")
    require(topology["runtime_enactment_status"] == "NOT_ASSESSED", "TOPOLOGY_RUNTIME_OVERCLAIM", "")
    (
        dependency_edge_registry,
        boundary_fitness_registry,
        coupling_policy,
        feedback_policy,
    ) = validate_adr9_projections(schemas, context_ids, checks)
    require(
        dependency_graph["registry_digest"]
        == "sha256:"
        + hashlib.sha256(canonical_bytes(dependency_edge_registry)).hexdigest(),
        "TOPOLOGY_DEPENDENCY_REGISTRY_DIGEST",
        "",
    )
    declared_edge_ids = {
        row["edge_id"] for row in dependency_edge_registry["entries"]
    }
    for exception in topology["exceptions"]:
        require(
            set(exception["allowed_dependency_edges"]) <= declared_edge_ids,
            "TOPOLOGY_EXCEPTION_EDGE_UNKNOWN",
            exception["exception_id"],
        )
        require(
            exception["owner_context"] in context_ids,
            "TOPOLOGY_EXCEPTION_OWNER_UNKNOWN",
            exception["exception_id"],
        )

    paths_registry = load_json(CONTRACTS / "paths.json")
    paths = paths_registry["entries"]
    unique(paths, "path_id", "PATH_ID_DUPLICATE")
    path_schema = schemas["schemas/common/path-contract-v1.schema.json"]
    for item in paths:
        jsonschema.Draft202012Validator(path_schema).validate(item)
        validate_path_contract_semantics(item)
        require(
            set(item["topology_rule_ids"]) <= EXPECTED_ORG_RULE_IDS,
            "PATH_TOPOLOGY_RULE_UNKNOWN",
            item["path_id"],
        )
        require(
            set(item["tdd_rule_ids"]) <= EXPECTED_TDD_RULE_IDS,
            "PATH_TDD_RULE_UNKNOWN",
            item["path_id"],
        )
        require(
            item["governance_owner_context"] == item["owner_context"],
            "PATH_GOVERNANCE_OWNER_ALIAS",
            item["path_id"],
        )
        if item["responsibility_class"] == "ALLOWED_TEST_ROOT":
            require(
                item["governance_owner_context"] == "process_assurance",
                "PATH_TEST_GOVERNANCE_OWNER",
                item["path_id"],
            )
            require(
                item["semantic_owner_kind"] == "PARAMETERIZED_TEST_SUBJECT_OWNER",
                "PATH_TEST_BLANKET_SEMANTIC_OWNER",
                item["path_id"],
            )
            require(item["semantic_owner_context"] is None, "PATH_TEST_BLANKET_SEMANTIC_OWNER", item["path_id"])
            require(
                item["semantic_owner_resolution"].startswith("Each leaf test must declare exactly one"),
                "PATH_TEST_LEAF_OWNER_RULE",
                item["path_id"],
            )
        elif item["semantic_owner_kind"] == "EXACT_CONTEXT":
            require(
                item["semantic_owner_context"] == item["owner_context"],
                "PATH_EXACT_SEMANTIC_OWNER",
                item["path_id"],
            )
        require(item["accountable_human_role"], "PATH_HUMAN_OWNER_MISSING", item["path_id"])
        require(item["required_reviewer_role"], "PATH_REVIEWER_MISSING", item["path_id"])
        require(item["data_ownership_refs"], "PATH_DATA_OWNER_REF_MISSING", item["path_id"])
        checks["path_rows_schema_validated"] += 1
    for context_id in context_ids:
        expected_layers = {
            f"src/ranex/{context_id}/api/**",
            f"src/ranex/{context_id}/domain/**",
            f"src/ranex/{context_id}/application/**",
            f"src/ranex/{context_id}/application/ports/**",
            f"src/ranex/{context_id}/adapters/**",
        }
        actual_layers = {
            item["path_pattern"]
            for item in paths
            if item["owner_context"] == context_id
        }
        require(expected_layers <= actual_layers, "PATH_CONTEXT_LAYER_SET", context_id)
        require(
            f"src/ranex/{context_id}/ports/**" not in actual_layers,
            "PATH_SIBLING_PORTS_FORBIDDEN",
            context_id,
        )
    test_paths = {
        item["path_pattern"][:-3]
        for item in paths
        if item["responsibility_class"] == "ALLOWED_TEST_ROOT"
    }
    require(test_paths == EXPECTED_TEST_ROOTS, "PATH_TEST_ROOT_SET", "")
    host_edge = next(item for item in paths if item["path_id"] == "PATH-HOST-EDGE-ADAPTERS")
    require(host_edge["required_exception_class"] == "HOST_EDGE_ADAPTER", "PATH_HOST_EDGE_EXCEPTION", "")
    require(paths_registry["path_enactment_status"] == "NOT_ASSESSED", "PATH_RUNTIME_OVERCLAIM", "")
    checks["topology_rules"] = len(topology_rules)
    checks["path_contracts"] = len(paths)

    states = load_json(CONTRACTS / "states.json")["entries"]
    unique(states, "axis_id", "STATE_AXIS_DUPLICATE")
    for axis in states:
        require(len(axis["values"]) == len(set(axis["values"])), "STATE_VALUE_DUPLICATE", axis["axis_id"])
        values = set(axis["values"])
        require(set(axis["terminal_values"]) <= values, "STATE_TERMINAL_UNKNOWN", axis["axis_id"])
        pairs: set[tuple[str, str]] = set()
        for transition in axis["transitions"]:
            require(transition["from"] in values and transition["to"] in values, "TRANSITION_STATE_UNKNOWN", axis["axis_id"])
            pair = (transition["from"], transition["to"])
            require(pair not in pairs, "TRANSITION_DUPLICATE", f"{axis['axis_id']}:{pair}")
            pairs.add(pair)
            require(transition["guard_id"] != "", "TRANSITION_GUARD_MISSING", f"{axis['axis_id']}:{pair}")
            checks["state_transitions"] += 1
        checks["state_axes"] += 1
    by_axis = {axis["axis_id"]: axis for axis in states}
    require(len(by_axis["WorkItemStatus"]["values"]) == 16, "WORK_STATUS_DENOMINATOR", "must be 16")
    require(len(by_axis["RunStatus"]["values"]) == 8, "RUN_STATUS_DENOMINATOR", "must be 8")
    require(by_axis["WorkItemStatus"]["owner_context"] == "work_management", "WORK_STATUS_OWNER", "wrong owner")
    require(by_axis["RunStatus"]["owner_context"] == "governed_execution", "RUN_STATUS_OWNER", "wrong owner")
    require(by_axis["WorkItemStatus"]["transitions"], "WORK_TRANSITIONS_EMPTY", "")
    require(by_axis["RunStatus"]["transitions"], "RUN_TRANSITIONS_EMPTY", "")

    elements_registry = load_json(CONTRACTS / "architecture-elements.json")
    elements = elements_registry["entries"]
    unique(elements, "element_id", "ARCHITECTURE_ELEMENT_DUPLICATE")
    element_ids = {item["element_id"] for item in elements}
    required_adr9_element_ids = (
        EXPECTED_ADR0009_RULE_IDS
        | EXPECTED_ADR0009_FITNESS_IDS
        | {
            "RANEX-CONTEXT-DEPENDENCIES-1.0",
            "RANEX-CONTEXT-BOUNDARY-FIT-1.0",
            "RANEX-BOUNDARY-FITNESS-1.0",
            "RANEX-GE-COUPLING-1.0",
            "RANEX-TDD-FEEDBACK-1.0",
            "GE-RESPONSIBILITY-COUNT",
            "GE-STATIC-FAN-OUT",
            "GE-STATIC-FAN-IN",
            "GE-INTERACTION-COUPLING",
            "GE-CHANGE-COUPLING",
            "GE-OWNERSHIP-CONCENTRATION",
            "TDD-FEEDBACK-FAST-P50",
            "TDD-FEEDBACK-FAST-P95",
            "TDD-FEEDBACK-PREVERIFY-P50",
            "TDD-FEEDBACK-PREVERIFY-P95",
        }
        | {f"BOUNDARYFIT-{context_id.replace('_', '-').upper()}" for context_id in context_ids}
    )
    require(
        required_adr9_element_ids <= element_ids,
        "ARCHITECTURE_ADR9_ELEMENT_SET",
        ",".join(sorted(required_adr9_element_ids - element_ids)),
    )
    zone_count = sum(item["kind"] == "CAPABILITY_ZONE" for item in elements)
    require(zone_count == 36, "CAPABILITY_ZONE_DENOMINATOR", str(zone_count))
    architecture_practice_profile = load_json(
        ARCHITECTURE_PRACTICE_PROFILE
    )
    architecture_practice_profile_digest = file_digest(
        ARCHITECTURE_PRACTICE_PROFILE
    )
    expected_applications_by_element: dict[str, list[dict[str, Any]]] = {
        element_id: [] for element_id in element_ids
    }
    for application in architecture_practice_profile["practice_applications"]:
        for element_id in application["architecture_element_ids"]:
            require(
                element_id in element_ids,
                "ARCH_PRACTICE_ELEMENT_UNKNOWN",
                element_id,
            )
            expected_applications_by_element[element_id].append(
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
    boundary_quanta = next(
        row
        for row in architecture_practice_profile["practice_applications"]
        if row["practice_id"]
        == "ENGREF-FUNDAMENTALS-SOFTWARE-ARCHITECTURE-1E-BOUNDARY-QUANTA"
    )
    expected_boundary_ids = {
        f"BOUNDARYFIT-{context_id.replace('_', '-').upper()}"
        for context_id in context_ids
    }
    require(
        expected_boundary_ids
        <= set(boundary_quanta["architecture_element_ids"])
        and "RANEX-CONTEXT-BOUNDARY-FIT-1.0"
        in boundary_quanta["architecture_element_ids"],
        "ARCH_PRACTICE_BOUNDARY_QUANTA_DENOMINATOR",
        "",
    )
    allowed_pseudo_owners = {
        "human_governor",
        "owning_aggregate_uow",
        "owning_context_repository",
        "packet_producer",
        "respective owner",
        "module + grant lifecycle",
        "schedule lifecycle",
        "channel config lifecycle",
        "retention lifecycle",
    }
    for item in elements:
        require(item["definition_status"] in {"DEFINED", "DEFINED_NAME_ONLY"}, "ELEMENT_DEFINITION_STATUS", item["element_id"])
        require(item["runtime_validation_status"] == "NOT_ASSESSED", "ELEMENT_RUNTIME_OVERCLAIM", item["element_id"])
        require(item["source"] != "", "ELEMENT_SOURCE_MISSING", item["element_id"])
        expected_applications = sorted(
            expected_applications_by_element[item["element_id"]],
            key=lambda row: row["practice_id"],
        )
        require(
            item["engineering_practice_profile_id"]
            == architecture_practice_profile["profile_id"]
            and item["engineering_practice_profile_digest"]
            == architecture_practice_profile_digest,
            "ELEMENT_PRACTICE_PROFILE_BINDING",
            item["element_id"],
        )
        require(
            item["engineering_practice_applications"]
            == expected_applications,
            "ELEMENT_PRACTICE_APPLICATION_PROJECTION",
            item["element_id"],
        )
        require(
            item["engineering_practice_application_status"]
            == (
                "EXPLICIT_MAPPINGS_PRESENT"
                if expected_applications
                else "NO_EXPLICIT_MAPPING"
            ),
            "ELEMENT_PRACTICE_APPLICATION_STATUS",
            item["element_id"],
        )
        for owner in item["owner_contexts"]:
            # Some capability rows intentionally preserve compound prose. The
            # concrete context registry remains the source for exact owners.
            if owner in context_ids or owner in allowed_pseudo_owners:
                continue
            require(" owns " in owner or " for " in owner or owner == "respective owner", "ELEMENT_OWNER_UNKNOWN", f"{item['element_id']}:{owner}")
        checks["architecture_elements"] += 1
    profile_binding = elements_registry[
        "engineering_practice_profile_binding"
    ]
    require(
        profile_binding["profile_id"]
        == architecture_practice_profile["profile_id"]
        and profile_binding["digest"]
        == architecture_practice_profile_digest
        and profile_binding["mapping_policy"]
        == "EXPLICIT_ELEMENT_IDS_ONLY_NO_TRANSITIVE_INFERENCE",
        "ELEMENT_PRACTICE_REGISTRY_BINDING",
        "",
    )

    vital = load_json(CONTRACTS / "vital-profile.json")
    tuples = vital["entries"]
    require(len(tuples) == 40, "VITAL_TUPLE_DENOMINATOR", str(len(tuples)))
    tuple_keys = [(row["domain_id"], row["control_id"], row["applicability_rule_id"]) for row in tuples]
    require(len(tuple_keys) == len(set(tuple_keys)), "VITAL_TUPLE_DUPLICATE", "")
    domains = sorted({row["domain_id"] for row in tuples})
    require(len(domains) == 10, "VITAL_DOMAIN_DENOMINATOR", str(len(domains)))
    rules = {entry["rule_id"] for entry in load_json(CONTRACTS / "applicability-rules.json")["entries"]}
    for row in tuples:
        require(row["applicability_rule_id"] in rules, "VITAL_RULE_UNKNOWN", row["control_id"])
        checks["vital_tuples"] += 1

    practices = load_json(CONTRACTS / "engineering-practices.json")
    families = practices["source_families"]
    practice_entries = practices["entries"]
    source_registry_path = ROOT / practices["source_registry_path"]
    require(source_registry_path.is_file(), "PRACTICE_SOURCE_REGISTRY_MISSING", str(source_registry_path))
    require(
        file_digest(source_registry_path) == practices["source_registry_digest"],
        "PRACTICE_SOURCE_REGISTRY_DRIFT",
        practices["source_registry_path"],
    )
    source_registry = load_json(source_registry_path)
    require(practices["source_corpus"] == source_registry["corpus"], "PRACTICE_CORPUS_BINDING_DRIFT", "")
    require(practices["source_profile_rule"] == source_registry["profile_rule"], "PRACTICE_PROFILE_RULE_DRIFT", "")
    corpus_manifest_path = ROOT / practices["source_corpus"]["manifest_path"]
    require(corpus_manifest_path.is_file(), "PRACTICE_CORPUS_MANIFEST_MISSING", str(corpus_manifest_path))
    require(
        file_digest(corpus_manifest_path) == "sha256:" + practices["source_corpus"]["manifest_sha256"],
        "PRACTICE_CORPUS_MANIFEST_DRIFT",
        practices["source_corpus"]["manifest_path"],
    )
    require(len(families) == 9, "PRACTICE_FAMILY_DENOMINATOR", str(len(families)))
    require(len(practice_entries) == 34, "PRACTICE_ID_DENOMINATOR", str(len(practice_entries)))
    unique(families, "source_family_id", "PRACTICE_FAMILY_DUPLICATE")
    unique(practice_entries, "practice_id", "PRACTICE_ID_DUPLICATE")
    family_ids = {family["source_family_id"] for family in families}
    for practice in practice_entries:
        require(practice["source_family_id"] in family_ids, "PRACTICE_FAMILY_UNKNOWN", practice["practice_id"])
        require(practice["source_binding_status"] == "STABLE_SOURCE_RECONCILED_NOT_APPLIED", "PRACTICE_BINDING_OVERCLAIM", practice["practice_id"])
        require(practice["application_status"] == "NOT_ASSESSED", "PRACTICE_APPLICATION_OVERCLAIM", practice["practice_id"])
    stable_practice_ids = {practice["practice_id"] for practice in practice_entries}
    decision_bindings = practices["decision_application_bindings"]
    require(
        {binding["decision_id"] for binding in decision_bindings}
        == {"ADR-0007", "ADR-0008", "ADR-0009"},
        "PRACTICE_DECISION_BINDING_SET",
        "",
    )
    for binding in decision_bindings:
        expected_practices = {
            "ADR-0007": EXPECTED_ADR0007_PRACTICE_IDS,
            "ADR-0008": EXPECTED_ADR0008_PRACTICE_IDS,
            "ADR-0009": EXPECTED_ADR0009_PRACTICE_IDS,
        }[binding["decision_id"]]
        require(
            set(binding["practice_ids"]) == expected_practices,
            "PRACTICE_DECISION_BINDING_SET",
            binding["decision_id"],
        )
        require(expected_practices <= stable_practice_ids, "PRACTICE_DECISION_UNKNOWN_ID", binding["decision_id"])
        decision = next(
            item
            for item in topology["decision_bindings"]
            if item["decision_id"] == binding["decision_id"]
        )
        require(
            binding["decision_digest"] == decision["digest"],
            "PRACTICE_DECISION_DIGEST",
            binding["decision_id"],
        )
        require(
            binding["application_status"] == "DEFINED_NOT_RUNTIME_ASSESSED",
            "PRACTICE_DECISION_OVERCLAIM",
            binding["decision_id"],
        )
    profile = load_json(CONTRACTS / "engineering-practice-profiles.json")["entries"][0]
    require(len(profile["source_coverage"]) == 9, "PRACTICE_PROFILE_COVERAGE", "")
    require(all(row["applicability"] == "UNKNOWN" for row in profile["source_coverage"]), "PRACTICE_PROFILE_OVERCLAIM", "")
    require(profile["sealing_eligible"] is False, "PRACTICE_PROFILE_SEALING", "")
    require(digest(profile) == profile["digest"], "PRACTICE_PROFILE_DIGEST", "")

    test_practices = load_json(CONTRACTS / "test-practices.json")
    test_rules = test_practices["entries"]
    unique(test_rules, "practice_id", "TDD_RULE_DUPLICATE")
    require(
        {rule["practice_id"] for rule in test_rules} == EXPECTED_TDD_RULE_IDS,
        "TDD_RULE_SET",
        "",
    )
    require(test_practices["rule_set_id"] == "RANEX-TDD-1.0", "TDD_RULE_SET_ID", "")
    require(
        {entry["root"] for entry in test_practices["taxonomy"]} == EXPECTED_TEST_ROOTS,
        "TDD_TAXONOMY_ROOT_SET",
        "",
    )
    expected_leaf_owner_parameters = {
        "UNIT": "CONTEXT",
        "CONTRACT": "CONTEXT",
        "INTEGRATION": "CONTEXT",
        "ACCEPTANCE": "CAPABILITY",
        "MIGRATION": "CONTEXT",
        "REPLAY": "CONTEXT",
        "FIXTURES": "OWNER",
        "BUILDERS": "CONTEXT",
    }
    expected_mirrored_layers = {
        "UNIT": {"domain", "application"},
        "CONTRACT": {"api", "application/ports", "adapters"},
        "INTEGRATION": {"application/ports", "adapters"},
        "ACCEPTANCE": {"api", "application"},
        "MIGRATION": {"adapters"},
        "REPLAY": {"domain", "application", "adapters"},
        "BUILDERS": {"domain", "application"},
    }
    expected_mirror_patterns = {
        "UNIT": {
            "tests/unit/<context>/domain/**",
            "tests/unit/<context>/application/**",
        },
        "CONTRACT": {"tests/contract/<context>/**"},
        "INTEGRATION": {"tests/integration/<context>/**"},
        "ARCHITECTURE": {"tests/architecture/**"},
        "ACCEPTANCE": {"tests/acceptance/<capability>/**"},
        "SYSTEM": {"tests/system/**"},
        "E2E": {"tests/e2e/**"},
        "SECURITY": {"tests/security/**"},
        "PERFORMANCE": {"tests/performance/**"},
        "RESILIENCE": {"tests/resilience/**"},
        "MIGRATION": {"tests/migration/<context>/**"},
        "REPLAY": {"tests/replay/<context>/**"},
        "OPERATIONS": {"tests/operations/**"},
        "QUALIFICATION": {"tests/qualification/**"},
        "EFFECTIVENESS": {"tests/effectiveness/**"},
        "EVALUATION": {"tests/evaluation/**"},
        "FIXTURES": {"tests/fixtures/<owner>/**"},
        "BUILDERS": {"tests/builders/<context>/**"},
    }
    for taxonomy_row in test_practices["taxonomy"]:
        category_id = taxonomy_row["category_id"]
        require(
            taxonomy_row["root_governance_owner"] == "process_assurance",
            "TDD_ROOT_GOVERNANCE_OWNER",
            category_id,
        )
        require(
            taxonomy_row["root_owner_is_not_leaf_semantic_owner"] is True,
            "TDD_ROOT_BLANKET_SEMANTIC_OWNER",
            category_id,
        )
        require(
            taxonomy_row["semantic_leaf_owner_parameter"]
            == expected_leaf_owner_parameters.get(category_id, "EXACT_TEST_METADATA"),
            "TDD_LEAF_OWNER_PARAMETER",
            category_id,
        )
        require(taxonomy_row["mirror_patterns"], "TDD_MIRROR_PATTERN_MISSING", category_id)
        require(
            set(taxonomy_row["mirror_patterns"])
            == expected_mirror_patterns[category_id],
            "TDD_MIRROR_PATTERN_DRIFT",
            category_id,
        )
        require(
            set(taxonomy_row["mirrored_source_layers"])
            == expected_mirrored_layers.get(category_id, set()),
            "TDD_MIRRORED_LAYER_DRIFT",
            category_id,
        )
        require(
            taxonomy_row["shape_rule"],
            "TDD_LANE_SHAPE_RULE_MISSING",
            category_id,
        )
    unit_taxonomy = next(
        row for row in test_practices["taxonomy"] if row["category_id"] == "UNIT"
    )
    require(
        set(unit_taxonomy["mirror_patterns"])
        == {
            "tests/unit/<context>/domain/**",
            "tests/unit/<context>/application/**",
        },
        "TDD_UNIT_MIRROR_PATTERN",
        "",
    )
    require(
        {entry["exception_class"] for entry in test_practices["exception_classes"]}
        == EXPECTED_TDD_EXCEPTION_CLASSES,
        "TDD_EXCEPTION_CLASS_SET",
        "",
    )
    require(test_practices["exceptions"] == [], "TDD_EXCEPTION_FABRICATED", "")
    require(
        test_practices["fitness_refs"] == [f"FF-TDD-{index:03d}" for index in range(1, 9)],
        "TDD_FITNESS_SET",
        "",
    )
    require(
        set(test_practices["topology_rule_ids"]) == EXPECTED_ORG_RULE_IDS,
        "TDD_TOPOLOGY_BINDING_SET",
        "",
    )
    require(
        set(test_practices["failure_mode_classes"]) == EXPECTED_FAILURE_MODE_CLASSES,
        "TDD_FAILURE_MODE_CLASS_SET",
        "",
    )
    require(
        test_practices["runtime_enactment_status"] == "NOT_ASSESSED",
        "TDD_RUNTIME_OVERCLAIM",
        "",
    )
    for binding in test_practices["decision_bindings"]:
        validate_decision_binding(binding)
    deprecated = {
        entry["deprecated_root"]: set(entry["replacement_roots"])
        for entry in test_practices["deprecated_root_migrations"]
    }
    require(
        deprecated["tests/persistence"]
        == {"tests/integration/<context>", "tests/migration/<context>"},
        "TDD_PERSISTENCE_ROOT_MIGRATION",
        "",
    )
    require(
        deprecated["tests/crash"] == {"tests/resilience"},
        "TDD_CRASH_ROOT_MIGRATION",
        "",
    )
    require(
        set(test_practices["engineering_practice_ids"]) == EXPECTED_ADR0008_PRACTICE_IDS,
        "TDD_ENGINEERING_PRACTICE_SET",
        "",
    )

    test_profile_registry = load_json(CONTRACTS / "test-practice-profiles.json")
    require(test_profile_registry["definition_profile_count"] == 1, "TDD_PROFILE_DEFINITION_COUNT", "")
    require(test_profile_registry["runtime_profile_count"] == 0, "TDD_PROFILE_RUNTIME_COUNT", "")
    require(
        test_profile_registry["runtime_enactment_status"] == "NOT_ASSESSED",
        "TDD_PROFILE_RUNTIME_OVERCLAIM",
        "",
    )
    test_profiles = test_profile_registry["entries"]
    require(len(test_profiles) == 1, "TDD_PROFILE_DENOMINATOR", str(len(test_profiles)))
    test_profile_schema = schemas["schemas/common/test-practice-profile-v1.schema.json"]
    for test_profile in test_profiles:
        jsonschema.Draft202012Validator(test_profile_schema).validate(test_profile)
        require(
            test_profile["registry_digest"]
            == "sha256:" + hashlib.sha256(canonical_bytes(test_practices)).hexdigest(),
            "TDD_PROFILE_REGISTRY_DIGEST",
            test_profile["profile_id"],
        )
        validate_test_profile_semantics(test_profile, test_practices)
        require(test_profile["profile_kind"] == "DEFINITION_BASELINE", "TDD_PROFILE_KIND", "")
        require(test_profile["runtime_evidence_status"] == "NOT_ASSESSED", "TDD_PROFILE_EVIDENCE_OVERCLAIM", "")
        checks["test_definition_profiles"] += 1
    checks["allowed_test_roots"] = len(test_practices["taxonomy"])
    checks["tdd_rules"] = len(test_rules)
    checks["failure_mode_classes"] = len(test_practices["failure_mode_classes"])

    rule_assessments = load_json(CONTRACTS / "architecture-rule-assessments.json")
    assessment_entries = rule_assessments["entries"]
    unique(assessment_entries, "assessment_id", "RULE_ASSESSMENT_ID_DUPLICATE")
    unique(assessment_entries, "rule_id", "RULE_ASSESSMENT_RULE_DUPLICATE")
    expected_rule_ids = (
        EXPECTED_ORG_RULE_IDS
        | EXPECTED_TDD_RULE_IDS
        | EXPECTED_ADR0009_RULE_IDS
    )
    require(len(assessment_entries) == 47, "RULE_ASSESSMENT_DENOMINATOR", str(len(assessment_entries)))
    require(
        {entry["rule_id"] for entry in assessment_entries} == expected_rule_ids,
        "RULE_ASSESSMENT_RULE_SET",
        "",
    )
    require(rule_assessments["expected_rule_count"] == 47, "RULE_ASSESSMENT_DECLARED_COUNT", "")
    require(rule_assessments["org_rule_count"] == 18, "RULE_ASSESSMENT_ORG_COUNT", "")
    require(rule_assessments["tdd_rule_count"] == 19, "RULE_ASSESSMENT_TDD_COUNT", "")
    require(rule_assessments["adr9_rule_count"] == 10, "RULE_ASSESSMENT_ADR9_COUNT", "")
    assessment_schema = schemas["schemas/common/architecture-rule-assessment-v1.schema.json"]
    definition_rules = {
        **{entry["rule_id"]: entry for entry in topology_rules},
        **{entry["practice_id"]: entry for entry in test_rules},
        **{
            entry["rule_id"]: entry
            for entry in boundary_fitness_registry["rules"]
        },
    }
    subject = rule_assessments["assessment_subject"]
    manifest_digest = "sha256:" + hashlib.sha256(canonical_bytes(subject["manifest"])).hexdigest()
    require(
        subject["subject_manifest_digest"] == manifest_digest,
        "RULE_ASSESSMENT_SUBJECT_MANIFEST_DIGEST",
        "",
    )
    subject_digest_input = {
        "subject_schema": subject["subject_schema"],
        "subject_scope": subject["subject_scope"],
        "subject_ref": subject["subject_ref"],
        "subject_manifest_digest": subject["subject_manifest_digest"],
    }
    require(
        subject["subject_digest"]
        == "sha256:" + hashlib.sha256(canonical_bytes(subject_digest_input)).hexdigest(),
        "RULE_ASSESSMENT_SUBJECT_DIGEST",
        "",
    )
    for entry in assessment_entries:
        jsonschema.Draft202012Validator(assessment_schema).validate(entry)
        require(
            entry["rule_definition_digest"]
            == "sha256:" + hashlib.sha256(canonical_bytes(definition_rules[entry["rule_id"]])).hexdigest(),
            "RULE_ASSESSMENT_DEFINITION_DIGEST",
            entry["rule_id"],
        )
        require(entry["subject_scope"] == "DEFINITION_CONTRACT_ONLY", "RULE_ASSESSMENT_SUBJECT_SCOPE", entry["rule_id"])
        require(entry["subject_ref"] == subject["subject_ref"], "RULE_ASSESSMENT_SUBJECT_REF", entry["rule_id"])
        require(entry["subject_digest"] == subject["subject_digest"], "RULE_ASSESSMENT_SUBJECT_DIGEST", entry["rule_id"])
        require(entry["runtime_subject_ref"] is None, "RULE_ASSESSMENT_RUNTIME_SUBJECT_FORGED", entry["rule_id"])
        require(entry["runtime_subject_digest"] is None, "RULE_ASSESSMENT_RUNTIME_SUBJECT_FORGED", entry["rule_id"])
        require(entry["result"] == "NOT_ASSESSED", "RULE_ASSESSMENT_RESULT_OVERCLAIM", entry["rule_id"])
        require(entry["outcome"] is None, "RULE_ASSESSMENT_OUTCOME_OVERCLAIM", entry["rule_id"])
        require(entry["numeric_score"] is None, "RULE_ASSESSMENT_NUMERIC_SCORE", entry["rule_id"])
        require(entry["runtime_evidence_refs"] == [], "RULE_ASSESSMENT_EVIDENCE_FORGED", entry["rule_id"])
        require(entry["observed_at"] is None, "RULE_ASSESSMENT_OBSERVATION_FORGED", entry["rule_id"])
        require(entry["freshness_status"] == "NOT_ASSESSED", "RULE_ASSESSMENT_FRESHNESS_OVERCLAIM", entry["rule_id"])
        require(entry["noncompensating"] is True, "RULE_ASSESSMENT_COMPENSATING", entry["rule_id"])
        require(entry["runtime_evidence_status"] == "NOT_ASSESSED", "RULE_ASSESSMENT_RUNTIME_OVERCLAIM", entry["rule_id"])
        require(digest(entry) == entry["digest"], "RULE_ASSESSMENT_DIGEST", entry["rule_id"])
        checks["architecture_rule_assessments"] += 1
    summary = rule_assessments["noncompensating_summary"]
    require(summary["result"] == "NOT_ASSESSED", "RULE_ASSESSMENT_SUMMARY_OVERCLAIM", "")
    require(summary["outcome"] is None, "RULE_ASSESSMENT_SUMMARY_OUTCOME", "")
    require(summary["numeric_score"] is None, "RULE_ASSESSMENT_SUMMARY_SCORE", "")
    require(summary["pass_authority"] is False, "RULE_ASSESSMENT_SUMMARY_AUTHORITY", "")
    require(
        set(summary["not_assessed_rule_ids"]) == expected_rule_ids,
        "RULE_ASSESSMENT_SUMMARY_SET",
        "",
    )

    effects = load_json(CONTRACTS / "effects.json")["entries"]
    unique(effects, "effect_family_id", "EFFECT_DUPLICATE")
    for effect in effects:
        require(effect["authority_owner"] == "governed_execution", "EFFECT_AUTHORITY_OWNER", effect["effect_family_id"])
        require(effect["reconciliation_required_for_unknown_outcome"] is True, "EFFECT_RECONCILIATION", effect["effect_family_id"])

    decisions = load_json(CONTRACTS / "decisions.json")["entries"]
    unique(decisions, "decision_id", "DECISION_DUPLICATE")
    require(
        {"ADR-0001", "ADR-0002", "ADR-0007", "ADR-0008", "ADR-0009"}
        <= {item["decision_id"] for item in decisions},
        "ADR_REGISTRY_INCOMPLETE",
        "",
    )
    for decision in decisions:
        require(decision["authority"] == "HUMAN_GOVERNOR", "DECISION_AUTHORITY", decision["decision_id"])

    validate_architecture_practice_profile(
        schemas,
        source_registry,
        {item["element_id"] for item in elements},
        {item["rule_id"] for item in topology_rules},
        {item["practice_id"] for item in test_rules},
        {item["decision_id"] for item in decisions},
        checks,
    )

    return tuples, domains


def validate_assessments(tuples: list[dict[str, str]], domains: list[str], schemas: dict[str, dict[str, Any]], checks: Counter[str]) -> None:
    control_files = sorted((ASSESSMENTS / "controls").glob("*.json"))
    domain_files = sorted((ASSESSMENTS / "domains").glob("*.json"))
    require(len(control_files) == 40, "ASSESSMENT_DENOMINATOR", str(len(control_files)))
    require(len(domain_files) == 10, "PROJECTION_DENOMINATOR", str(len(domain_files)))
    expected_controls = {row["control_id"]: row for row in tuples}
    assessments: dict[str, dict[str, Any]] = {}
    assessment_schema = schemas["schemas/process/capability-assessment-v1.schema.json"]
    for path in control_files:
        item = load_json(path)
        jsonschema.Draft202012Validator(assessment_schema).validate(item)
        control_id = item["scope"]["control_id"]
        require(control_id in expected_controls, "ASSESSMENT_CONTROL_UNKNOWN", control_id)
        require(path.stem == control_id, "ASSESSMENT_FILENAME", str(path))
        require(item["definition_status"] == "DEFINED", "ASSESSMENT_DEFINITION_STATUS", control_id)
        require(item["capability_rating"]["result"] == "NOT_ASSESSED", "ASSESSMENT_SCORE_FABRICATED", control_id)
        require(item["capability_rating"]["level"] is None, "ASSESSMENT_LEVEL_FABRICATED", control_id)
        require(item["effectiveness"]["result"] == "UNKNOWN", "ASSESSMENT_EFFECTIVENESS_OVERCLAIM", control_id)
        require(item["applicability"]["result"] == "UNKNOWN", "ASSESSMENT_APPLICABILITY_OVERCLAIM", control_id)
        require(item["confidence"]["derived_level"] == "LOW", "ASSESSMENT_CONFIDENCE_OVERCLAIM", control_id)
        require(item["priority"]["result"] == "NOT_EVALUATED", "ASSESSMENT_PRIORITY_OVERCLAIM", control_id)
        require(len(item["population"]["joint_strata"]) == 40, "ASSESSMENT_STRATA_DENOMINATOR", control_id)
        require(digest(item) == item["digest"], "ASSESSMENT_DIGEST_MISMATCH", control_id)
        assessments[control_id] = item
        checks["capability_assessments"] += 1
    require(set(assessments) == set(expected_controls), "ASSESSMENT_CONTROL_SET", "")

    by_domain: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in tuples:
        by_domain[row["domain_id"]].append(row)
    projection_schema = schemas["schemas/process/capability-domain-projection-v1.schema.json"]
    observed_domains: set[str] = set()
    for path in domain_files:
        item = load_json(path)
        jsonschema.Draft202012Validator(projection_schema).validate(item)
        domain_id = item["scope"]["domain_id"]
        observed_domains.add(domain_id)
        require(path.stem == domain_id, "PROJECTION_FILENAME", str(path))
        expected = {(row["domain_id"], row["control_id"], row["applicability_rule_id"]) for row in by_domain[domain_id]}
        actual = {(row["domain_id"], row["control_id"], row["applicability_rule_id"]) for row in item["members"]}
        require(actual == expected, "PROJECTION_TUPLE_SET", domain_id)
        require(len(item["members"]) == len(actual), "PROJECTION_MEMBER_DUPLICATE", domain_id)
        require(item["derivation"]["registered_member_count"] == len(expected), "PROJECTION_REGISTERED_COUNT", domain_id)
        require(item["derivation"]["bound_member_count"] == len(expected), "PROJECTION_BOUND_COUNT", domain_id)
        require(item["derivation"]["derived_result"] == "UNKNOWN", "PROJECTION_RESULT_OVERCLAIM", domain_id)
        require(item["derivation"]["derived_level"] is None, "PROJECTION_LEVEL_FABRICATED", domain_id)
        require(item["priority_projection"]["result"] == "NOT_EVALUATED", "PROJECTION_PRIORITY_OVERCLAIM", domain_id)
        require(item["derivation"]["arithmetic_aggregation_prohibited"] is True, "PROJECTION_ARITHMETIC", domain_id)
        for member in item["members"]:
            source = assessments[member["control_id"]]
            require(member["assessment_digest"] == source["digest"], "PROJECTION_ASSESSMENT_DIGEST", member["control_id"])
            require(member["assessment_scope_digest"] == source["scope"]["scope_digest"], "PROJECTION_SCOPE_DIGEST", member["control_id"])
            require(member["rating_result"] == "NOT_ASSESSED", "PROJECTION_SCORE_FABRICATED", member["control_id"])
        require(digest(item) == item["digest"], "PROJECTION_DIGEST_MISMATCH", domain_id)
        checks["domain_projections"] += 1
    require(observed_domains == set(domains), "PROJECTION_DOMAIN_SET", "")


def validate_canonical_fixtures(checks: Counter[str]) -> None:
    golden = load_json(SCHEMAS / "fixtures" / "canonical" / "rfc8785-golden.json")
    for fixture in golden["fixtures"]:
        encoded = canonical_bytes(fixture["input"])
        require(encoded.decode("utf-8") == fixture["canonical_utf8"], "RFC8785_CANONICAL_MISMATCH", fixture["fixture_id"])
        require(hashlib.sha256(encoded).hexdigest() == fixture["sha256"], "RFC8785_DIGEST_MISMATCH", fixture["fixture_id"])
        checks["canonical_golden_fixtures"] += 1


def validate_negative_fixtures(schemas: dict[str, dict[str, Any]], checks: Counter[str]) -> None:
    negative = SCHEMAS / "fixtures" / "negative"
    expected_fixture_names = {
        "blanket-test-root-owner.json",
        "broad-host-edge-exception.json",
        "cyclic-context-imports.json",
        "duplicate-key.yaml",
        "expired-quarantine-test-profile.json",
        "forbidden-cross-context-private-import.py",
        "forbidden-test-bypass.py",
        "forbidden-test-only-production-branch.py",
        "forged-digest.json",
        "forged-pass-missing-production-evidence.json",
        "forged-pass-unbound-production-evidence.json",
        "forged-task-aggregate-pass.json",
        "forced-transition-boilerplate-test-profile.json",
        "happy-path-only-test-profile.json",
        "incomplete-obsolete-test-deletion.json",
        "material-unknown-test-profile.json",
        "permit-reuse.json",
        "retry-to-pass-quarantine-test-profile.json",
        "stale-subject.json",
        "subject-mismatch.json",
        "synthetic-runtime-promotion-test-profile.json",
        "unjustified-edge-na-test-profile.json",
        "unknown-field.json",
        "unregistered-public-api-import.py",
        "unsupported-na-test-profile.json",
    }
    actual_fixture_names = {
        path.name for path in negative.iterdir() if path.is_file()
    }
    require(
        actual_fixture_names == expected_fixture_names,
        "NEGATIVE_FIXTURE_ORPHAN_OR_MISSING",
        (
            f"missing={','.join(sorted(expected_fixture_names - actual_fixture_names))};"
            f"orphan={','.join(sorted(actual_fixture_names - expected_fixture_names))}"
        ),
    )
    try:
        load_yaml(negative / "duplicate-key.yaml")
    except ContractFailure as exc:
        require(str(exc).startswith("DUPLICATE_KEY:"), "NEGATIVE_DUPLICATE_WRONG_ERROR", str(exc))
    else:
        raise ContractFailure("NEGATIVE_DUPLICATE_ACCEPTED")
    checks["negative_fixtures"] += 1

    unknown = load_json(negative / "unknown-field.json")
    errors = list(jsonschema.Draft202012Validator(schemas[unknown["schema_path"]]).iter_errors(unknown["instance"]))
    require(any(error.validator == "additionalProperties" for error in errors), "NEGATIVE_UNKNOWN_FIELD_ACCEPTED", "")
    checks["negative_fixtures"] += 1

    forged = load_json(negative / "forged-digest.json")
    require(digest(forged["instance"]) != forged["instance"]["digest"], "NEGATIVE_FORGERY_ACCEPTED", "")
    checks["negative_fixtures"] += 1

    reused = load_json(negative / "permit-reuse.json")
    require(reused["permit_status"] == "CONSUMED" and len(set(reused["consumption_transition_ids"])) > 1, "NEGATIVE_PERMIT_REUSE_NOT_DETECTED", "")
    checks["negative_fixtures"] += 1

    mismatch = load_json(negative / "subject-mismatch.json")
    require(mismatch["parent"]["subject_ref"] == mismatch["child"]["subject_ref"], "NEGATIVE_SUBJECT_FIXTURE_REF", "")
    require(mismatch["parent"]["subject_digest"] != mismatch["child"]["subject_digest"], "NEGATIVE_SUBJECT_MISMATCH_NOT_DETECTED", "")
    checks["negative_fixtures"] += 1

    stale = load_json(negative / "stale-subject.json")
    require(stale["expected_run_aggregate_version"] != stale["observed_run_aggregate_version"], "NEGATIVE_STALE_NOT_DETECTED", "")
    checks["negative_fixtures"] += 1

    test_practices = load_json(CONTRACTS / "test-practices.json")
    profile_fixtures = [
        ("happy-path-only-test-profile.json", "TEST_PROFILE_HAPPY_PATH_ONLY"),
        ("material-unknown-test-profile.json", "TEST_PROFILE_MATERIAL_UNKNOWN"),
        ("unsupported-na-test-profile.json", "TEST_PROFILE_UNSUPPORTED_NOT_APPLICABLE"),
        ("synthetic-runtime-promotion-test-profile.json", "TEST_PROFILE_SYNTHETIC_RUNTIME_PROMOTION"),
        ("unjustified-edge-na-test-profile.json", "TEST_PROFILE_UNSUPPORTED_NOT_APPLICABLE"),
        ("forced-transition-boilerplate-test-profile.json", "TEST_PROFILE_NA_TRANSITION_BOILERPLATE"),
        ("expired-quarantine-test-profile.json", "TEST_PROFILE_QUARANTINE_EXPIRED"),
        (
            "forged-pass-missing-production-evidence.json",
            "TEST_PROFILE_PRODUCTION_EVIDENCE_MISSING",
        ),
        (
            "forged-pass-unbound-production-evidence.json",
            "TEST_PROFILE_PASS_BINDING_INCOMPLETE",
        ),
    ]
    for filename, expected_error in profile_fixtures:
        fixture = load_json(negative / filename)
        require(fixture["expected_error"] == expected_error, "NEGATIVE_TEST_PROFILE_EXPECTATION", filename)
        try:
            validate_test_profile_semantics(
                fixture["instance"],
                test_practices,
                fixture_mode=True,
            )
        except ContractFailure as exc:
            require(
                str(exc).startswith(expected_error + ":"),
                "NEGATIVE_TEST_PROFILE_WRONG_ERROR",
                f"{filename}:{exc}",
            )
        else:
            raise ContractFailure(f"NEGATIVE_TEST_PROFILE_ACCEPTED:{filename}")
        checks["negative_fixtures"] += 1

    test_profile_schema = schemas[
        "schemas/common/test-practice-profile-v1.schema.json"
    ]
    retry_to_pass = load_json(
        negative / "retry-to-pass-quarantine-test-profile.json"
    )
    require(
        retry_to_pass["expected_error"]
        == "TEST_PROFILE_QUARANTINE_RETRY_TO_PASS",
        "NEGATIVE_RETRY_PASS_EXPECTATION",
        "",
    )
    retry_errors = list(
        jsonschema.Draft202012Validator(test_profile_schema).iter_errors(
            retry_to_pass["instance"]
        )
    )
    require(
        any(
            error.validator == "enum"
            and list(error.absolute_path)[-1:] == ["gate_disposition"]
            for error in retry_errors
        ),
        "NEGATIVE_RETRY_TO_PASS_ACCEPTED",
        "",
    )
    checks["negative_fixtures"] += 1

    incomplete_deletion = load_json(
        negative / "incomplete-obsolete-test-deletion.json"
    )
    require(
        incomplete_deletion["expected_error"]
        == "TEST_PROFILE_OBSOLETE_DELETION_INCOMPLETE",
        "NEGATIVE_DELETION_EXPECTATION",
        "",
    )
    deletion_errors = list(
        jsonschema.Draft202012Validator(test_profile_schema).iter_errors(
            incomplete_deletion["instance"]
        )
    )
    require(
        any(
            error.validator == "required"
            and "replacement_evidence_refs" in error.message
            for error in deletion_errors
        ),
        "NEGATIVE_INCOMPLETE_DELETION_ACCEPTED",
        "",
    )
    checks["negative_fixtures"] += 1

    source_fixtures = [
        ("forbidden-test-bypass.py", "TEST_BYPASS"),
        ("forbidden-test-only-production-branch.py", "TEST_ONLY_PRODUCTION_BRANCH"),
    ]
    for filename, expected_error in source_fixtures:
        violations = forbidden_test_constructs((negative / filename).read_text(encoding="utf-8"))
        require(expected_error in violations, "NEGATIVE_SOURCE_POLICY_ACCEPTED", filename)
        checks["negative_fixtures"] += 1

    forged_task = load_json(negative / "forged-task-aggregate-pass.json")
    require(
        forged_task["expected_error"] == "TEST_PROFILE_TASK_SUBJECT_MISSING",
        "NEGATIVE_FORGED_TASK_EXPECTATION",
        "",
    )
    try:
        validate_test_profile_semantics(
            forged_task["instance"],
            test_practices,
            fixture_mode=True,
        )
    except ContractFailure as exc:
        require(
            str(exc).startswith("TEST_PROFILE_TASK_SUBJECT_MISSING:"),
            "NEGATIVE_FORGED_TASK_WRONG_ERROR",
            str(exc),
        )
    else:
        raise ContractFailure("NEGATIVE_FORGED_TASK_ACCEPTED")
    checks["negative_fixtures"] += 1

    blanket_owner = load_json(negative / "blanket-test-root-owner.json")
    require(
        blanket_owner["expected_error"] == "PATH_TEST_BLANKET_SEMANTIC_OWNER",
        "NEGATIVE_BLANKET_OWNER_EXPECTATION",
        "",
    )
    path_schema = schemas["schemas/common/path-contract-v1.schema.json"]
    jsonschema.Draft202012Validator(path_schema).validate(blanket_owner["instance"])
    try:
        validate_path_contract_semantics(blanket_owner["instance"])
    except ContractFailure as exc:
        require(
            str(exc).startswith("PATH_TEST_BLANKET_SEMANTIC_OWNER:"),
            "NEGATIVE_BLANKET_OWNER_WRONG_ERROR",
            str(exc),
        )
    else:
        raise ContractFailure("NEGATIVE_BLANKET_OWNER_ACCEPTED")
    checks["negative_fixtures"] += 1

    broad_exception = load_json(
        negative / "broad-host-edge-exception.json"
    )
    require(
        broad_exception["expected_error"]
        == "TOPOLOGY_EXCEPTION_WHOLE_LAYER_WILDCARD",
        "NEGATIVE_TOPOLOGY_EXCEPTION_EXPECTATION",
        "",
    )
    jsonschema.Draft202012Validator(
        schemas["schemas/common/topology-exception-v1.schema.json"]
    ).validate(broad_exception["instance"])
    try:
        validate_topology_exception_semantics(broad_exception["instance"])
    except ContractFailure as exc:
        require(
            str(exc).startswith(
                "TOPOLOGY_EXCEPTION_WHOLE_LAYER_WILDCARD:"
            ),
            "NEGATIVE_TOPOLOGY_EXCEPTION_WRONG_ERROR",
            str(exc),
        )
    else:
        raise ContractFailure("NEGATIVE_TOPOLOGY_EXCEPTION_ACCEPTED")
    checks["negative_fixtures"] += 1

    private_import_path = negative / "forbidden-cross-context-private-import.py"
    private_import_source = private_import_path.read_text(encoding="utf-8")
    require(
        private_import_source.splitlines()[0]
        == "# expected_error: TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT",
        "NEGATIVE_PRIVATE_IMPORT_EXPECTATION",
        "",
    )
    fixture_module_path = (
        ROOT / "src/ranex/work_management/application/private_import_fixture.py"
    )
    private_imports = imported_modules(fixture_module_path, private_import_source)
    context_ids = {
        entry["context_id"]
        for entry in load_json(CONTRACTS / "contexts.json")["entries"]
    }
    try:
        for private_target in private_imports:
            validate_cross_context_import_target(
                fixture_module_path,
                private_target,
                "work_management",
                context_ids,
            )
    except ContractFailure as exc:
        require(
            str(exc).startswith("TOPOLOGY_PRIVATE_CROSS_CONTEXT_IMPORT:"),
            "NEGATIVE_PRIVATE_IMPORT_WRONG_ERROR",
            str(exc),
        )
    else:
        raise ContractFailure("NEGATIVE_PRIVATE_IMPORT_ACCEPTED")
    checks["negative_fixtures"] += 1

    unregistered_import_path = (
        negative / "unregistered-public-api-import.py"
    )
    unregistered_source = unregistered_import_path.read_text(
        encoding="utf-8"
    )
    require(
        unregistered_source.splitlines()[0]
        == "# expected_error: TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE",
        "NEGATIVE_UNREGISTERED_EDGE_EXPECTATION",
        "",
    )
    unregistered_module_path = (
        ROOT / "src/ranex/work_management/application/unregistered_edge.py"
    )
    unregistered_targets = imported_modules(
        unregistered_module_path,
        unregistered_source,
    )
    observed_unregistered_pairs: set[tuple[str, str]] = set()
    for target in unregistered_targets:
        target_context = validate_cross_context_import_target(
            unregistered_module_path,
            target,
            "work_management",
            context_ids,
        )
        if target_context:
            observed_unregistered_pairs.add(
                ("work_management", target_context)
            )
    declared_pairs = {
        (row["caller"], row["callee"])
        for row in load_json(
            CONTRACTS / "context-dependency-edges.json"
        )["entries"]
    }
    try:
        require(
            observed_unregistered_pairs <= declared_pairs,
            "TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE",
            ",".join(
                f"{caller}->{callee}"
                for caller, callee in sorted(
                    observed_unregistered_pairs - declared_pairs
                )
            ),
        )
    except ContractFailure as exc:
        require(
            str(exc).startswith(
                "TOPOLOGY_UNREGISTERED_DEPENDENCY_EDGE:"
            ),
            "NEGATIVE_UNREGISTERED_EDGE_WRONG_ERROR",
            str(exc),
        )
    else:
        raise ContractFailure("NEGATIVE_UNREGISTERED_EDGE_ACCEPTED")
    checks["negative_fixtures"] += 1

    cycle_fixture = load_json(negative / "cyclic-context-imports.json")
    require(
        cycle_fixture["expected_error"] == "TOPOLOGY_CONTEXT_IMPORT_CYCLE",
        "NEGATIVE_CYCLE_EXPECTATION",
        "",
    )
    fixture_edges: dict[str, set[str]] = defaultdict(set)
    for module in cycle_fixture["modules"]:
        module_path = ROOT / module["path"]
        relative_parts = module_path.relative_to(ROOT / "src/ranex").parts
        source_context = relative_parts[0]
        require(
            source_context in context_ids,
            "NEGATIVE_CYCLE_SOURCE_CONTEXT",
            source_context,
        )
        for target in imported_modules(module_path, module["source"]):
            target_context = validate_cross_context_import_target(
                module_path,
                target,
                source_context,
                context_ids,
            )
            if target_context:
                fixture_edges[source_context].add(target_context)
    require(
        graph_has_cycle(fixture_edges),
        "NEGATIVE_CONTEXT_CYCLE_ACCEPTED",
        "",
    )
    checks["negative_fixtures"] += 1


def validate_semantic_fixtures(checks: Counter[str]) -> None:
    semantic = SCHEMAS / "fixtures" / "semantic"
    expected_names = {"valid-stateless-task-profile.json"}
    actual_names = {path.name for path in semantic.iterdir() if path.is_file()}
    require(
        actual_names == expected_names,
        "SEMANTIC_FIXTURE_ORPHAN_OR_MISSING",
        "",
    )
    fixture = load_json(semantic / "valid-stateless-task-profile.json")
    require(fixture["expected_result"] == "PASS", "SEMANTIC_FIXTURE_RESULT", "")
    validate_test_profile_semantics(
        fixture["instance"],
        load_json(CONTRACTS / "test-practices.json"),
        fixture_mode=True,
    )
    checks["semantic_fixtures"] += 1


def validate_production_test_constructs(checks: Counter[str]) -> None:
    source_root = ROOT / "src" / "ranex"
    source_files = sorted(source_root.rglob("*.py")) if source_root.is_dir() else []
    for path in source_files:
        violations = forbidden_test_constructs(path.read_text(encoding="utf-8"))
        require(
            not violations,
            "PRODUCTION_TEST_CONSTRUCT_FORBIDDEN",
            f"{path.relative_to(ROOT)}:{','.join(sorted(violations))}",
        )
        checks["production_source_files_scanned"] += 1
    if not source_files:
        checks["production_source_files_scanned"] = 0


def validate_completeness_report(checks: Counter[str]) -> None:
    report = load_json(ASSESSMENTS / "completeness-report.json")
    require(report["counts"]["governed_yaml_templates"] == 36, "REPORT_TEMPLATE_COUNT", "")
    require(report["counts"]["capability_zones"] == 36, "REPORT_ZONE_COUNT", "")
    require(report["counts"]["vital_control_tuples"] == 40, "REPORT_VITAL_COUNT", "")
    require(report["counts"]["capability_assessments"] == 40, "REPORT_ASSESSMENT_COUNT", "")
    require(report["counts"]["domain_projections"] == 10, "REPORT_PROJECTION_COUNT", "")
    require(report["counts"]["architecture_elements"] == 909, "REPORT_ELEMENT_COUNT", "")
    require(report["counts"]["topology_rules"] == 18, "REPORT_TOPOLOGY_RULE_COUNT", "")
    require(report["counts"]["allowed_test_roots"] == 18, "REPORT_TEST_ROOT_COUNT", "")
    require(report["counts"]["tdd_rules"] == 19, "REPORT_TDD_RULE_COUNT", "")
    require(
        report["counts"]["test_definition_profiles"] == 1,
        "REPORT_TEST_PROFILE_COUNT",
        "",
    )
    require(
        report["counts"]["architecture_rule_assessments"] == 47,
        "REPORT_RULE_ASSESSMENT_COUNT",
        "",
    )
    require(report["counts"]["negative_fixtures"] == 25, "REPORT_NEGATIVE_FIXTURE_COUNT", "")
    require(
        report["counts"]["semantic_fixtures"] == 1,
        "REPORT_SEMANTIC_FIXTURE_COUNT",
        "",
    )
    require(
        report["counts"]["declared_context_dependency_edges"] == 67,
        "REPORT_DECLARED_EDGE_COUNT",
        "",
    )
    require(
        report["counts"]["context_boundary_fit_rows"] == 34,
        "REPORT_BOUNDARY_FIT_COUNT",
        "",
    )
    require(report["counts"]["adr9_rules"] == 10, "REPORT_ADR9_RULE_COUNT", "")
    require(
        report["counts"]["adr9_fitness_obligations"] == 9,
        "REPORT_ADR9_FITNESS_COUNT",
        "",
    )
    require(
        report["counts"]["coupling_measures"] == 6,
        "REPORT_COUPLING_MEASURE_COUNT",
        "",
    )
    require(
        report["counts"]["feedback_objectives"] == 4,
        "REPORT_FEEDBACK_OBJECTIVE_COUNT",
        "",
    )
    require(report["honesty_invariants"]["runtime_scores_fabricated"] == 0, "REPORT_RUNTIME_OVERCLAIM", "")
    checks["completeness_report"] += 1


def validate_contract_tree() -> int:
    checks: Counter[str] = Counter()
    try:
        schemas = validate_schema_documents(checks)
        validate_templates(schemas, checks)
        validate_registry_manifest(checks)
        tuples, domains = validate_registries(schemas, checks)
        validate_assessments(tuples, domains, schemas, checks)
        validate_canonical_fixtures(checks)
        validate_negative_fixtures(schemas, checks)
        validate_semantic_fixtures(checks)
        validate_production_topology(checks)
        validate_production_test_constructs(checks)
        validate_completeness_report(checks)
    except (ContractFailure, jsonschema.ValidationError, jsonschema.SchemaError, yaml.YAMLError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc), "checks": dict(sorted(checks.items()))}, sort_keys=True))
        return 1
    result = {
        "report_id": "RANEX-WAVE1-CONTRACT-VALIDATION-001",
        "status": "PASS",
        "scope": "EXECUTABLE_DOCUMENTATION_CONTRACTS_ONLY",
        "runtime_validation": "NOT_ASSESSED",
        "source_topology_validation": (
            "PASS"
            if checks["production_topology_files_scanned"] > 0
            else "NOT_ASSESSED"
        ),
        "production_test_construct_validation": (
            "PASS"
            if checks["production_source_files_scanned"] > 0
            else "NOT_ASSESSED"
        ),
        "generator_path": "scripts/architecture/generate_contracts.py",
        "generator_digest": file_digest(
            ROOT / "scripts" / "architecture" / "generate_contracts.py"
        ),
        "validator_path": "scripts/architecture/validate_contracts.py",
        "validator_digest": file_digest(Path(__file__).resolve()),
        "contract_tree_lock_path": "scripts/architecture/contract_tree_lock.py",
        "contract_tree_lock_digest": file_digest(
            ROOT / "scripts" / "architecture" / "contract_tree_lock.py"
        ),
        "concurrency_regression_path": (
            "scripts/architecture/test_contract_concurrency.py"
        ),
        "concurrency_regression_digest": file_digest(
            ROOT / "scripts" / "architecture" / "test_contract_concurrency.py"
        ),
        "registry_manifest_digest": file_digest(CONTRACTS / "registry-manifest.json"),
        "schema_registry_digest": file_digest(CONTRACTS / "schema-registry.json"),
        "architecture_practice_profile_digest": file_digest(
            ARCHITECTURE_PRACTICE_PROFILE
        ),
        "assessment_subject_digest": load_json(ASSESSMENTS / "assessment-subject.json")["digest"],
        "checks": dict(sorted(checks.items())),
    }
    (ASSESSMENTS / "validation-report.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def main() -> int:
    with contract_tree_lock(ROOT):
        return validate_contract_tree()


if __name__ == "__main__":
    sys.exit(main())
