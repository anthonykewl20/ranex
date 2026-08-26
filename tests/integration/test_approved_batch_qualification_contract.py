"""Frozen RED contract for SLICE-036 approved-batch qualification.

The successor pair below is the frozen E2E subject fixture.  The real E2E
reconstructs it deterministically from the public parent, committed owner key,
and every child input.  It is not a production restriction: implementation
must accept a separately approved future pair and never substitute a mutable
ref name.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ranex.cli.fanout import cmd_task_fanout
from ranex.cli.main import build_parser
from ranex.foundation.signing import SIGNED_FIELDS
from ranex.foundation.specification_abc import assert_abc_chain, payload_digest
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.specification_approval import (
    PolicyCapabilities,
    intersect_capabilities,
)

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests/contract/fixtures/specification"
VECTOR_PATH = FIXTURES / "approved-batch-v1-vectors.json"
VECTORS = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
DESCRIPTOR = json.loads((FIXTURES / "approved-batch-v1.json").read_text(encoding="utf-8"))
SCHEMA = json.loads(
    (ROOT / "governance/schemas/specification/approved-batch-v1.schema.json").read_text(
        encoding="utf-8"
    )
)
QUALIFICATION_SCHEMA = json.loads(
    (
        ROOT
        / "governance/schemas/specification/batch-qualification-v1.schema.json"
    ).read_text(encoding="utf-8")
)
ROWS = tuple(
    json.loads(line)
    for line in (FIXTURES / "approved-batch-child-requests-v1.jsonl")
    .read_text(encoding="utf-8")
    .splitlines()
    if line
)
FLOW = json.loads((FIXTURES / "approved-batch-pseudocode-flow-v1.json").read_text())
EXPECTED_VALUES = json.loads(
    (FIXTURES / "approved-batch-expected-values-v1.json").read_text()
)
BASELINE = json.loads((FIXTURES / "approved-batch-baseline-v1.json").read_text())
NEGATIVE_CONTROLS = json.loads(
    (FIXTURES / "approved-batch-negative-controls-v1.json").read_text()
)
FIXTURE_PARENT_COMMIT = "6d8e690f959305922c3a65d93216c46143a3232d"
BASE_COMMIT = "faed9b4c04d3c71e17342380e650fb4725d2a8d8"
SUBJECT_DIGEST = "sha256:81d874f118d23480e34787f1edf506b5603c0908e8528d9c1c1a8d2af9d457a3"
OWNER_PUBLIC_KEY = "ed25519:A6EHv/POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg="


def envelope() -> dict[str, object]:
    triple = VECTORS["triple"]
    return {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": triple["c_payload"],
        "key_id": triple["key_id"],
        "signature": triple["signature"],
    }


def file_digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def journal_snapshot(path: Path) -> tuple[int, str | None]:
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    try:
        row = connection.execute(
            "SELECT COUNT(*) AS count, "
            "(SELECT link FROM evaluations ORDER BY seq DESC LIMIT 1) AS head "
            "FROM evaluations"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    return int(row[0]), row[1]


def test_signed_authority_closes_schema_descriptor_children_and_every_oracle_fixture() -> None:
    triple = VECTORS["triple"]
    assert VECTORS["version"] == "approved-batch-v1-vectors-16"
    assert triple["a"]["revision"] == triple["c_payload"]["revision"] == 14
    assert triple["c_payload"]["nonce"] == "slice036-approved-batch-v16"
    assert_abc_chain(triple["a"], triple["b"], envelope())
    assert payload_digest(triple["a"]) == triple["a_digest"]
    assert payload_digest(triple["b"]) == triple["b_digest"]
    assert payload_digest(triple["c_payload"]) == triple["c_digest"]

    protected = {
        row["path"]: row["digest"]
        for row in triple["b"]["artifacts"]["protected"]
    }
    assert set(protected) == set(VECTORS["paths"].values())
    for name, relative in VECTORS["paths"].items():
        expected = VECTORS["digests"][name]
        assert protected[relative] == expected
        assert file_digest(ROOT / relative) == expected

    artifacts = triple["b"]["artifacts"]
    for category in (
        "pseudocode_flow",
        "expected_values",
        "baselines",
        "negative_controls",
    ):
        assert artifacts[category], f"B must bind populated {category} oracle bytes"
    references = DESCRIPTOR["oracle"]["protected_artifacts"]
    assert set(references) == {
        "baseline",
        "expected_values",
        "negative_controls",
        "pseudocode_flow",
    }
    assert len({row["path"] for row in references.values()}) == 4
    for name, row in references.items():
        vector_name = name
        assert row == {
            "path": VECTORS["paths"][vector_name],
            "digest": VECTORS["digests"][vector_name],
        }

    assert len(FLOW["steps"]) == 10 and len(FLOW["flows"]) == 2
    assert EXPECTED_VALUES["canonical_results"] == list(DESCRIPTOR["children"])
    assert BASELINE["journal"] == {"head": None, "rows": 0}
    assert BASELINE["target_ref"]["oid"] == BASE_COMMIT
    assert BASELINE["repository_identity"] == "same-governed-checkout"
    assert BASELINE["development_source_in_repository"] is False
    assert len(NEGATIVE_CONTROLS["controls"]) >= 10
    assert all(control["input_refs"] for control in NEGATIVE_CONTROLS["controls"])

    category_paths = {
        category: {row["path"] for row in artifacts[category]}
        for category in (
            "pseudocode_flow",
            "expected_values",
            "baselines",
            "negative_controls",
        )
    }
    assert category_paths["pseudocode_flow"] == {VECTORS["paths"]["pseudocode_flow"]}
    assert VECTORS["paths"]["expected_values"] in category_paths["expected_values"]
    assert category_paths["baselines"] == {VECTORS["paths"]["baseline"]}
    assert VECTORS["paths"]["negative_controls"] in category_paths["negative_controls"]
    assert VECTORS["paths"]["descriptor"] not in set().union(*category_paths.values())
    output = DESCRIPTOR["qualification_output"]
    assert output == {
        "claim_id": "approved-batch-qualified",
        "path": "batch-qualification.json",
        "producer_id": "owner",
        "publication_allowed": False,
        "schema": {
            "path": VECTORS["paths"]["qualification_schema"],
            "digest": VECTORS["digests"]["qualification_schema"],
        },
        "signature_primitive": "ranex-evidence-v4",
    }
    assert QUALIFICATION_SCHEMA["properties"]["payload"]["properties"][
        "publication_allowed"
    ] == {"const": False}
    assert QUALIFICATION_SCHEMA["properties"]["attestation"]["$ref"] == (
        "#/$defs/evidence"
    )
    assert set(QUALIFICATION_SCHEMA["properties"]["payload"]["required"]) == {
        "a_digest",
        "b_digest",
        "base_commit",
        "base_digest",
        "batch_digest",
        "c_digest",
        "child_requests_digest",
        "child_results_digest",
        "descriptor_digest",
        "producer_id",
        "publication_allowed",
        "qualification_journal",
        "qualification_record_digest",
        "version",
    }
    assert set(QUALIFICATION_SCHEMA["$defs"]["evidence"]["required"]) == {
        *SIGNED_FIELDS,
        "signature",
    }


def test_fixture_uses_exact_base_subject_and_provenanced_runtime_evidence_contract() -> None:
    assert DESCRIPTOR["base_commit"] == BASE_COMMIT
    assert DESCRIPTOR["subject_digest"] == SUBJECT_DIGEST
    assert VECTORS["triple"]["c_payload"]["base_digest"] == SUBJECT_DIGEST
    assert VECTORS["triple"]["c_payload"]["subject_digest"] == SUBJECT_DIGEST
    successor = EXPECTED_VALUES["fixture_successor"]
    assert {key: successor[key] for key in successor if key != "committed_paths"} == {
        "author_email": "fixture@ranex.invalid",
        "author_name": "Ranex Fixture",
        "commit": BASE_COMMIT,
        "commit_date": "2000-01-01T00:00:00 +0000",
        "message": "test(SLICE-036): materialize governed static-worker fixture",
        "parent": FIXTURE_PARENT_COMMIT,
        "subject_digest": SUBJECT_DIGEST,
    }
    assert len(successor["committed_paths"]) == 29
    assert "governance/qualification/worker/slice036-worker" in successor["committed_paths"]
    published_authority = EXPECTED_VALUES["published_v2_authority"]
    assert published_authority == {
        "commit": FIXTURE_PARENT_COMMIT,
        "launcher_manifest": {
            "digest": "sha256:58371a372609d9a33d6de450cf5e0e094cefd4fa98a2d5fc393f372be828ac14",
            "path": "governance/confinement/native-launcher-build-v1.json",
        },
        "launcher_source": {
            "digest": "sha256:ea6143f3b468546e8e6119c58909572247a0c1077660a911f18a1404b3dc141a",
            "path": "native/ranex-worker-launcher/launcher.c",
        },
        "profile": {
            "digest": "sha256:cf1610a7de909503a508f33ac328ced303c304478166636c59e0da2b8e01b1da",
            "path": "governance/confinement/strict-local-host-v1.json",
        },
    }
    for identity in ("launcher_manifest", "launcher_source", "profile"):
        record = published_authority[identity]
        observed = subprocess.run(
            ["git", "show", f"{FIXTURE_PARENT_COMMIT}:{record['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        assert "sha256:" + hashlib.sha256(observed).hexdigest() == record[
            "digest"
        ]
    assert EXPECTED_VALUES["committed_keyring_observers"] == {
        "admission": "existing load_keyring_text plus admit",
        "descriptor_role": "cross-check-only-never-trust-root",
        "path": "governance/producers.yaml",
        "producer_id": "owner",
        "public_key": OWNER_PUBLIC_KEY,
        "snapshots": ["base_commit", "candidate_commit", "target_tip"],
    }
    invocation = VECTORS["triple"]["b"]["artifacts"]["invocation"]["argv"]
    assert invocation[invocation.index("--target") + 1] == "."
    assert invocation[invocation.index("--journal") + 1] == (
        "governance/journal.sqlite3"
    )
    assert EXPECTED_VALUES["repository_continuity"] == {
        "ref": "refs/heads/main",
        "repository": "same-governed-checkout",
        "stages": [
            "qualify",
            "batch-qualified-journal",
            "qualification-artifact",
            "dispatch",
            "judge-refusal",
            "merge-refusal",
        ],
    }
    assert EXPECTED_VALUES["development_source_observer"] == {
        "cwd_repository": "governed",
        "manifest": (
            "sha256 over canonical path/raw-sha256 entries for every src/ranex file"
        ),
        "module": "ranex.cli.main",
        "pythonpath": "absolute-development-worktree-src",
        "source_in_governed_repository": False,
    }
    parent_policy = PolicyCapabilities.from_record(DESCRIPTOR["policy"])
    assert parent_policy.executable == "/ranex/toolchain/bin/slice036-worker"
    assert parent_policy.digest == VECTORS["triple"]["c_payload"][
        "profile_digests"
    ]["policy"]

    required = set(SCHEMA["$defs"]["childRequest"]["required"])
    assert all(set(row) == required for row in ROWS)
    assert len(ROWS) == 6
    assert [row["depends_on"] for row in ROWS] == [
        [], [], [], [],
        ["SLICE-036-child-A", "SLICE-036-child-B"],
        ["SLICE-036-child-A", "SLICE-036-child-B"],
    ]
    full_invocations: set[tuple[str, ...]] = set()
    wrapped_invocations: set[tuple[str, ...]] = set()
    for row in ROWS:
        assert row["base_commit"] == BASE_COMMIT
        assert row["worktree"] == "disposable" and row["publication"] is False
        assert row["invocation"]["confinement"] == "strict-local"
        assert row["invocation"]["argv"][:4] == [
            "python",
            "-m",
            "ranex.cli.main",
            "run",
        ]
        assert "--confinement" in row["invocation"]["argv"]
        assert "strict-local" in row["invocation"]["argv"]
        full_invocations.add(tuple(row["invocation"]["argv"]))
        assert row["capability_request"]["argv"] == ["--task"]
        assert row["capability_request"]["executable"] == "/ranex/toolchain/bin/slice036-worker"
        separator = row["invocation"]["argv"].index("--")
        wrapped_invocations.add(tuple(row["invocation"]["argv"][separator + 1 :]))
        assert row["invocation"]["argv"][separator + 1 :] == [
            "/ranex/toolchain/bin/slice036-worker",
            "--task",
        ]
        assert row["capability_request"]["cwd"] == "."
        assert row["capability_request"]["environment"] == {
            "allow": ["LC_ALL", "TZ"]
        }
        child_policy = PolicyCapabilities.from_record(row["capability_request"])
        intersection = intersect_capabilities(
            parent_policy,
            child_policy,
            child=True,
        )
        assert intersection.argv == child_policy.argv
        assert intersection.cwd == child_policy.cwd == "."
        assert intersection.roots == child_policy.roots
        assert intersection.environment_allow == ("LC_ALL", "TZ")
        assert "RANEX_BATCH_TASK_ID" not in json.dumps(row)
        runtime = row["runtime_input"]
        expected_input = (
            f"governance/qualification/inputs/{row['task_id']}/"
            f"{runtime['flow_id']}/attempt-{row['attempt']}"
        )
        assert row["invocation"]["runtime_input_path"] == expected_input
        assert row["invocation"]["toolchain_root"] == (
            "governance/qualification/worker"
        )
        assert row["invocation"]["argv"][separator - 4 : separator] == [
            "--runtime-input-path", expected_input,
            "--toolchain-root", "governance/qualification/worker",
        ]
        authority_root = f"governance/qualification/inputs/{row['task_id']}"
        assert authority_root in row["scope"]["roots"]
        assert authority_root in row["capability_request"]["roots"]
        assert row["checks"] == [
            {
                "check_id": "slice036-network-process-and-exit",
                "command": [
                    "/ranex/toolchain/bin/slice036-worker",
                    *row["capability_request"]["argv"],
                ],
            }
        ]
        for evidence in row["evidence"]:
            assert set(evidence) == {"check_id", "claim", "path"}
            assert evidence["claim"] == "slice036-child-check"
            assert evidence["check_id"] == "slice036-network-process-and-exit"
            assert not Path(evidence["path"]).is_absolute()
            assert ".." not in Path(evidence["path"]).parts
            assert "digest" not in evidence
        assert runtime["mode"] == "normal"
        assert runtime["task_id"] == row["task_id"]
        assert runtime["loopback_ports"] == {"start": 46120, "end": 46135}
        assert set(runtime) == {
            "delay_ms",
            "flow_id",
            "loopback_ports",
            "mode",
            "task_id",
        }
    assert len(full_invocations) == 6
    assert wrapped_invocations == {("/ranex/toolchain/bin/slice036-worker", "--task")}
    for flow_id in ("a-before-b", "b-before-a"):
        flow_rows = [
            row for row in ROWS if row["runtime_input"]["flow_id"] == flow_id
        ]
        assert [row["task_id"] for row in flow_rows] == list(DESCRIPTOR["children"])
        flow_scopes = [
            {
                (root, action)
                for root in row["scope"]["roots"]
                for action in row["scope"]["actions"]
            }
            for row in flow_rows
        ]
        assert all(
            left.isdisjoint(right)
            for ordinal, left in enumerate(flow_scopes)
            for right in flow_scopes[ordinal + 1 :]
        )
    golden_events = [
        json.loads(line)
        for line in (ROOT / VECTORS["paths"]["qualification_golden"])
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    source_events = [
        event for event in golden_events if event["event"] == "batch.child.sources"
    ]
    assert [
        (event["flow_id"], event["task_id"], event["runtime_input_path"])
        for event in source_events
    ] == sorted(
        (
            row["runtime_input"]["flow_id"],
            row["task_id"],
            row["invocation"]["runtime_input_path"],
        )
        for row in ROWS
    )
    assert all(
        event["input"] == "/ranex/input/task.json"
        and event["toolchain"] == "/ranex/toolchain"
        and event["toolchain_root"] == "governance/qualification/worker"
        for event in source_events
    )
    serialized = json.dumps(ROWS)
    assert "aaaaaaaaaaaaaaaa" not in serialized
    assert "bbbbbbbbbbbbbbbb" not in serialized
    assert "cccccccccccccccc" not in serialized
    assert SCHEMA["$defs"]["childRequest"]["properties"]["attempt"] == {
        "maximum": 6,
        "minimum": 0,
        "type": "integer",
    }
    runtime_schema = SCHEMA["$defs"]["runtimeInput"]
    assert set(runtime_schema["required"]) == {
        "delay_ms",
        "flow_id",
        "loopback_ports",
        "mode",
        "task_id",
    }
    assert runtime_schema["properties"]["delay_ms"] == {
        "minimum": 0,
        "type": "integer",
    }
    assert SCHEMA["$defs"]["capability"]["properties"]["environment"][
        "properties"
    ]["allow"] == {
        "maxItems": 2,
        "minItems": 2,
        "prefixItems": [{"const": "LC_ALL"}, {"const": "TZ"}],
        "type": "array",
        "uniqueItems": True,
    }
    assert SCHEMA["$defs"]["childRequest"]["properties"]["invocation"][
        "properties"
    ]["runtime_input_path"]["pattern"] == (
        r"^governance/qualification/inputs/[A-Za-z0-9-]+/[a-z0-9-]+/attempt-[0-6]$"
    )
    assert SCHEMA["$defs"]["childRequest"]["properties"]["invocation"][
        "properties"
    ]["toolchain_root"] == {
        "const": "governance/qualification/worker",
        "type": "string",
    }
    assert EXPECTED_VALUES["child_input_geometry"] == {
        "embedded_attempt_flow_task_must_match": True,
        "input_path": "governance/qualification/inputs/<task-id>/<flow-id>/attempt-<n>",
        "mounted_file": "/ranex/input/task.json",
        "selection": "exact signed public runtime-input-path selector",
        "task_id_source": "tracked-base-committed-task-json",
        "tracked_at_started_base": True,
        "worker_environment": ["LC_ALL", "TZ"],
        "worktree_clean_before_run": True,
    }
    provisioning = EXPECTED_VALUES["child_provisioning"]
    assert provisioning["controller"] == [
        "uv",
        "run",
        "--frozen",
        "python",
        "-m",
        "ranex.cli.host_confinement",
    ]
    assert [command[0] for command in provisioning["commands"]] == [
        "launcher-build",
        "launcher-install",
        "qualify",
    ]
    assert provisioning["before"] == "ranex run --confinement strict-local"
    assert provisioning["manual_local_copy"] is False
    assert provisioning["application_events_trusted"] is False
    assert provisioning["observer"] == "strace-execve-chdir-v1"
    assert provisioning["outer_command_prefix"] == [
        "/usr/bin/strace",
        "-f",
        "--detach-on=execve",
        "-s",
        "8192",
    ]
    assert provisioning["controller_target"] == (
        "resolved-absolute-development-python-direct-never-uv"
    )
    assert provisioning["sibling_observation"] == [
        "sequential",
        "concurrent-siblings",
    ]
    assert provisioning["run_argv_source"] == (
        "B-bound-flow-specific-full-child-invocation"
    )
    assert provisioning["dependency_admission"] == {
        "commands": [
            ["deps", "fetch", "--repository", "."],
            [
                "deps",
                "approve",
                "--repository",
                ".",
                "--approver",
                "slice036-observer-calibration",
            ],
            ["journal", "verify", "--repository", "."],
        ],
        "controller": [
            "uv",
            "run",
            "--frozen",
            "python",
            "-m",
            "ranex.cli.main",
        ],
        "development_source": False,
        "phase": "observer-calibration-before-trace",
    }
    assert provisioning["canonical_verifier"] == {
        "accepted_self_test_outcomes": ["passed"],
        "actual_batch_success_separate": True,
        "current_preimplementation_refusal": (
            "missing-public-v2-run-source-selector-parser"
        ),
        "expected_progression": [
            "public v2 run source selectors parse and validate",
            "batch parser/application seams are RED",
            "batch parser/application lands",
            "frozen journey succeeds",
        ],
        "invocation": "exact-full-B-bound-ranex-run-argv",
        "owner": "ranex run --confinement strict-local",
    }
    assert provisioning["observer_tool"] == {
        "path": "/usr/bin/strace",
        "sha256": (
            "sha256:28f957c227012de0b18d1bd7fff2d396"
            "cb693ea60ed8013be68de071e84b5001"
        ),
        "version": "strace -- version 6.8",
    }
    assert provisioning["provenance_path"] == "outside-governed-repository"
    assert provisioning["release_invariant"] == (
        "each clean child independently runs exact public launcher-build "
        "launcher-install and qualify commands in its own cwd before run and "
        "its final launcher report and qualified state are independently verified"
    )
    assert provisioning["transient_copy_absence_required"] is False
    assert set(provisioning["required_observations"]) == {
        "canonical_public_host_verifier",
        "canonical_verifier_outcome_closed",
        "child_cwd_geometry",
        "clean_initial_qualification_state",
        "closed_child_exec_multiset",
        "command_order_before_run",
        "controller_python_absolute",
        "controller_target_not_uv",
        "dependency_derivation_approval_verified",
        "exact_exec_argv",
        "exact_full_run_argv",
        "exact_public_commands",
        "final_child_launcher_digest",
        "final_child_report_digest",
        "final_child_qualified_state",
        "observer_tool_digest",
        "observer_tool_version",
        "run_count",
        "sequential_and_concurrent_siblings",
        "step_count",
    }


def test_static_worker_build_is_reproducible_and_bound(tmp_path: Path) -> None:
    static = EXPECTED_VALUES["static_worker"]
    manifest = json.loads((ROOT / static["build_manifest"]).read_bytes())
    source = ROOT / static["source"]
    assert file_digest(source) == static["source_sha256"]
    compiler = Path(manifest["build"]["compiler"]["path"])
    assert file_digest(compiler) == "sha256:" + manifest["build"]["compiler"]["sha256"]
    for item in manifest["build"]["inputs"]:
        assert file_digest(Path(item["path"])) == "sha256:" + item["sha256"]
    artifacts = []
    for ordinal in range(2):
        output = tmp_path / f"worker-{ordinal}"
        flags = [
            token.replace("<ABS_REPO_ROOT>", str(ROOT.resolve()))
            .replace("<output>", str(output))
            .replace("<source>", str(source))
            for token in manifest["build"]["flags"]
        ]
        completed = subprocess.run(
            [str(compiler), *flags],
            cwd=ROOT,
            env=manifest["build"]["environment"],
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr.decode()
        artifacts.append(output.read_bytes())
    assert artifacts[0] == artifacts[1]
    assert hashlib.sha256(artifacts[0]).hexdigest() == manifest["artifact"]["sha256"]


def test_static_worker_noexec_calibration_is_input_selected_and_discriminating() -> None:
    calibration = EXPECTED_VALUES["subject_noexec_calibration"]
    assert calibration == {
        "expected_exit_code": 80,
        "exec_result_channel": "MAP_SHARED|MAP_ANONYMOUS errno cell",
        "forbidden_output": "/ranex/output/result.json",
        "input": "tests/e2e/fixtures/slice070-noexec/task.json",
        "input_sha256": file_digest(
            ROOT / "tests/e2e/fixtures/slice070-noexec/task.json"
        ),
        "mode": "subject-noexec",
        "other_errno_exit_code": 82,
        "outputs": {"bytes": 0, "files": [], "inodes": 0},
        "subject_executable": "/ranex/subject/.local/subject-worker",
        "successful_exec_exit_code": 81,
        "supervision_failure_exit_code": 83,
        "top_level_argv": [
            "/ranex/toolchain/bin/slice036-worker",
            "--task",
        ],
    }
    assert len(
        {
            calibration["expected_exit_code"],
            calibration["successful_exec_exit_code"],
            calibration["other_errno_exit_code"],
            calibration["supervision_failure_exit_code"],
        }
    ) == 4


def test_b_bound_negative_inputs_plant_each_public_cli_control_in_child_rows() -> None:
    controls = {row["control_id"]: row for row in NEGATIVE_CONTROLS["controls"]}
    protected = {
        row["path"]: row["digest"]
        for row in VECTORS["triple"]["b"]["artifacts"]["protected"]
    }
    for control in controls.values():
        for reference in control["input_refs"]:
            assert protected[reference["path"]] == reference["digest"]

    def read_rows(name: str) -> list[dict[str, object]]:
        return [
            json.loads(line)
            for line in (ROOT / VECTORS["paths"][name])
            .read_text(encoding="utf-8")
            .splitlines()
        ]

    unapproved = read_rows("unapproved_rows")
    overlap = read_rows("overlap_rows")
    network = read_rows("network_rows")
    survivor = read_rows("survivor_rows")
    mismatch = read_rows("oracle_mismatch_rows")
    input_mismatch = read_rows("input_mismatch_rows")
    assert [row["task_id"] for row in unapproved][-1] == "SLICE-036-child-D"
    assert set(overlap[0]["scope"]["roots"]) & set(
        overlap[1]["scope"]["roots"]
    ) == {"governance/qualification/worker/slice036-worker.c"}
    assert overlap[0]["invocation"]["runtime_input_path"] != overlap[1][
        "invocation"
    ]["runtime_input_path"]
    assert network[0]["runtime_input"]["mode"] == "network-control"
    assert survivor[0]["runtime_input"]["mode"] == "survivor"
    assert mismatch[2]["runtime_input"]["mode"] == "oracle-mismatch"
    assert input_mismatch[0]["task_id"] == "SLICE-036-child-A"
    assert input_mismatch[0]["attempt"] == 6
    assert input_mismatch[0]["invocation"]["runtime_input_path"] == (
        "governance/qualification/inputs/SLICE-036-child-B/"
        "input-mismatch-control/attempt-6"
    )
    for row in input_mismatch[1:]:
        assert row["invocation"]["runtime_input_path"] == (
            f"governance/qualification/inputs/{row['task_id']}/"
            f"input-mismatch-control/attempt-6"
        )
    selector_controls = {
        control_id
        for control_id in controls
        if control_id.startswith("selector-")
    }
    assert selector_controls == {
        "selector-absolute",
        "selector-digest-drift",
        "selector-dirty",
        "selector-dynamic-elf",
        "selector-extra",
        "selector-held-overlap",
        "selector-host-executable",
        "selector-intermediate-symlink-alias",
        "selector-manifest-drift",
        "selector-missing-pair",
        "selector-remote",
        "selector-symlink-alias",
        "selector-traversal",
        "selector-untracked",
        "selector-wrong-base",
    }
    assert all(controls[name]["pre_journal"] for name in selector_controls)
    executable_refusals = EXPECTED_VALUES["public_run_source_selectors"][
        "executable_refusal_controls"
    ]
    assert executable_refusals == {
        "selector-digest-drift": (
            "E-C18-GATE: toolchain worker digest differs from its build manifest"
        ),
        "selector-dirty": "E-C18-GATE: runtime input selector differs from started_at",
        "selector-dynamic-elf": (
            "E-C18-GATE: v2 worker requests an unsupported dynamic runtime closure"
        ),
        "selector-held-overlap": (
            "E-C18-PATH-ALIAS: input and toolchain source objects overlap"
        ),
        "selector-intermediate-symlink-alias": (
            "E-C18-PATH-ALIAS: runtime input selector contains a symlink"
        ),
        "selector-manifest-drift": (
            "E-C18-GATE: toolchain source digest differs from its build manifest"
        ),
        "selector-symlink-alias": (
            "E-C18-PATH-ALIAS: runtime input selector contains a symlink"
        ),
        "selector-untracked": (
            "E-C18-GATE: runtime input selector is not tracked at started_at"
        ),
        "selector-wrong-base": (
            "E-C18-GATE: runtime input selector is absent from started_at"
        ),
    }
    for control_id, refusal in executable_refusals.items():
        assert controls[control_id]["plant"]["refusal"] == refusal
        assert controls[control_id]["plant"]["observation"].startswith(
            "public cmd_run returns EXIT_USAGE with exact refusal"
        )
    selector_security = VECTORS["paths"]["selector_security"]
    assert selector_security == "tests/security/test_slice036_run_source_selectors.py"
    assert protected[selector_security] == file_digest(ROOT / selector_security)
    assert network[0]["checks"][0]["command"] == [
        "/ranex/toolchain/bin/slice036-worker",
        "--task",
    ]
    static_worker = EXPECTED_VALUES["static_worker"]
    assert file_digest(ROOT / static_worker["source"]) == static_worker["source_sha256"]
    assert file_digest(ROOT / static_worker["build_manifest"]) == static_worker[
        "build_manifest_sha256"
    ]


def test_separate_batch_qualify_parser_preserves_the_exact_legacy_fanout_surface() -> None:
    parser = build_parser()
    legacy = parser.parse_args(
        [
            "task",
            "fanout",
            "--tasks",
            "tasks.jsonl",
            "--target",
            "target.git",
            "--journal",
            "journal.sqlite3",
            "--harness",
            "harness",
            "--model",
            "model",
            "--timeout",
            "900",
            "--suite",
            "pytest -q",
            "--outcome-dir",
            "outcomes",
            "--pool",
            "1",
        ]
    )
    assert legacy.action == "fanout"
    assert legacy.func is cmd_task_fanout
    assert not hasattr(legacy, "spec_packet")

    approved = parser.parse_args(
        [
            "task",
            "batch",
            "qualify",
            "--spec-packet",
            "spec-packet.json",
            "--artifact-manifest",
            "artifact-manifest.json",
            "--approval-envelope",
            "approval-envelope.json",
            "--descriptor",
            VECTORS["paths"]["descriptor"],
            "--tasks",
            VECTORS["paths"]["children"],
            "--target",
            ".",
            "--journal",
            "journal.sqlite3",
            "--outcome-dir",
            "outcomes",
            "--pool",
            "2",
        ]
    )
    assert approved.action == "batch"
    assert approved.batch_action == "qualify"


def test_public_run_parser_owns_paired_strict_local_source_selectors_only() -> None:
    parser = build_parser()
    row = ROWS[0]
    argv = row["invocation"]["argv"][3:]
    parsed = parser.parse_args(argv)
    assert parsed.confinement == "strict-local"
    assert parsed.runtime_input_path == row["invocation"]["runtime_input_path"]
    assert parsed.toolchain_root == "governance/qualification/worker"
    assert parsed.command == ["--", "/ranex/toolchain/bin/slice036-worker", "--task"]

    separator = argv.index("--")
    without_toolchain = argv[:]
    start = without_toolchain.index("--toolchain-root")
    del without_toolchain[start : start + 2]
    with pytest.raises(SystemExit):
        parser.parse_args(without_toolchain)

    duplicated = argv[:separator]
    duplicated.extend(["--runtime-input-path", row["invocation"]["runtime_input_path"]])
    duplicated.extend(argv[separator:])
    with pytest.raises(SystemExit):
        parser.parse_args(duplicated)

    ordinary = argv[:]
    confinement = ordinary.index("--confinement")
    del ordinary[confinement : separator + 1]
    with pytest.raises(SystemExit):
        parser.parse_args(ordinary)


def test_batch_qualification_flag_is_additive_to_legacy_judge_and_merge() -> None:
    parser = build_parser()
    judge_argv = [
        "task",
        "judge",
        "--task-id",
        "SLICE-036-child-A",
        "--emitted-worktree",
        "worktree",
        "--emitted-commit",
        BASE_COMMIT,
        "--gate",
        "landing",
        "--gate-catalog",
        "governance/gates.yaml",
        "--evidence",
        "evidence.json",
        "--producers",
        "governance/producers.yaml",
        "--journal",
        "governance/journal.sqlite3",
    ]
    merge_argv = [
        "task",
        "merge",
        "--task-id",
        "SLICE-036-child-A",
        "--target-ref",
        "refs/heads/main",
        "--candidate",
        BASE_COMMIT,
        "--approval",
        "approval.json",
    ]
    assert getattr(parser.parse_args(judge_argv), "batch_qualification", None) is None
    assert getattr(parser.parse_args(merge_argv), "batch_qualification", None) is None

    artifact = "outcomes/batch-qualification.json"
    batch_judge = parser.parse_args([*judge_argv, "--batch-qualification", artifact])
    batch_merge = parser.parse_args([*merge_argv, "--batch-qualification", artifact])
    assert batch_judge.batch_qualification == artifact
    assert batch_merge.batch_qualification == artifact


def test_signed_plan_has_both_completion_orders_canonical_results_and_c_join() -> None:
    from ranex.governed_execution.application.specification_batch import (
        plan_qualification,
    )

    plan = plan_qualification(DESCRIPTOR, ROWS)
    assert plan.ready_sets == (
        ("SLICE-036-child-A", "SLICE-036-child-B"),
        ("SLICE-036-child-C",),
    )
    assert tuple(flow.completion_order for flow in plan.flows) == (
        ("SLICE-036-child-A", "SLICE-036-child-B", "SLICE-036-child-C"),
        ("SLICE-036-child-B", "SLICE-036-child-A", "SLICE-036-child-C"),
    )
    assert all(
        flow.canonical_results
        == ("SLICE-036-child-A", "SLICE-036-child-B", "SLICE-036-child-C")
        for flow in plan.flows
    )
    assert all(flow.join_released == "SLICE-036-child-C" for flow in plan.flows)


def test_append_if_head_is_one_begin_immediate_cas_and_stale_reentry_is_stable(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.sqlite3"
    journal = Journal(path)

    class Evaluation:
        def __init__(self, operation: str) -> None:
            self.operation = operation

        def as_record(self) -> dict[str, str]:
            return {"operation": self.operation, "type": "batch-qualified"}

    first = journal.append_if_head(None, Evaluation("first"))
    assert first.position == 1
    assert first.head.startswith("sha256:")
    assert journal_snapshot(path) == (1, first.head)

    def race(name: str) -> tuple[str, object]:
        try:
            return "accepted", Journal(path).append_if_head(
                first.head, Evaluation(name)
            )
        except ValueError as exc:
            return "refused", str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = tuple(pool.map(race, ("second-a", "second-b")))
    assert [kind for kind, _ in outcomes].count("accepted") == 1
    assert [kind for kind, _ in outcomes].count("refused") == 1
    refusal = next(value for kind, value in outcomes if kind == "refused")
    assert str(refusal).startswith("E-BATCH-STALE-BASE:")
    rows, head = journal_snapshot(path)
    assert rows == 2
    assert head == next(
        value.head for kind, value in outcomes if kind == "accepted"
    )

    before = journal_snapshot(path)
    with pytest.raises(ValueError, match=r"^E-BATCH-STALE-BASE:"):
        journal.append_if_head(None, Evaluation("blind-replay"))
    assert journal_snapshot(path) == before
