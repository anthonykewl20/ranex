"""Frozen RED contract for SLICE-036 approved-batch qualification.

The 5586d68/34fa pair below is the frozen E2E subject fixture.  It is not a
production restriction: the implementation must accept a separately approved
future exact base/subject pair and must never substitute a mutable ref name.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from ranex.cli.fanout import cmd_task_fanout
from ranex.cli.main import build_parser, subject_digest_for
from ranex.foundation.signing import SIGNED_FIELDS
from ranex.foundation.specification_abc import assert_abc_chain, payload_digest
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.domain.specification_approval import PolicyCapabilities

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
BASE_COMMIT = "5586d68b0936f554759022caabe847087f1d03ef"
SUBJECT_DIGEST = "sha256:34fa645d616fc0b0383d424573d60a447ddd829e8891b7f992b809be9a783953"


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
    assert VECTORS["version"] == "approved-batch-v1-vectors-4"
    assert triple["a"]["revision"] == triple["c_payload"]["revision"] == 2
    assert triple["c_payload"]["nonce"] == "slice036-approved-batch-v4"
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

    assert len(FLOW["steps"]) == 9 and len(FLOW["flows"]) == 2
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
    assert subject_digest_for(ROOT, BASE_COMMIT) == SUBJECT_DIGEST
    assert VECTORS["triple"]["c_payload"]["base_digest"] == SUBJECT_DIGEST
    assert VECTORS["triple"]["c_payload"]["subject_digest"] == SUBJECT_DIGEST
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
    assert (
        PolicyCapabilities.from_record(DESCRIPTOR["policy"]).digest
        == VECTORS["triple"]["c_payload"]["profile_digests"]["policy"]
    )

    required = set(SCHEMA["$defs"]["childRequest"]["required"])
    assert all(set(row) == required for row in ROWS)
    assert [row["depends_on"] for row in ROWS] == [
        [],
        [],
        ["SLICE-036-child-A", "SLICE-036-child-B"],
    ]
    sibling_pairs: set[tuple[str, str]] = set()
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
        assert row["checks"] == [
            {
                "check_id": "slice036-network-process-and-exit",
                "command": ["python", *row["capability_request"]["argv"]],
            }
        ]
        for evidence in row["evidence"]:
            assert set(evidence) == {"check_id", "claim", "path"}
            assert evidence["claim"] == "slice036-child-check"
            assert evidence["check_id"] == "slice036-network-process-and-exit"
            assert not Path(evidence["path"]).is_absolute()
            assert ".." not in Path(evidence["path"]).parts
            assert "digest" not in evidence
        sibling_pairs.update(
            (root, action)
            for root in row["scope"]["roots"]
            for action in row["scope"]["actions"]
        )
        runtime = row["runtime_input"]
        assert runtime["mode"] == "normal"
        assert runtime["task_id"] == row["task_id"]
        assert runtime["loopback_ports"] == {"start": 46120, "end": 46135}
    assert len(sibling_pairs) == sum(
        len(row["scope"]["roots"]) * len(row["scope"]["actions"])
        for row in ROWS
    )
    serialized = json.dumps(ROWS)
    assert "aaaaaaaaaaaaaaaa" not in serialized
    assert "bbbbbbbbbbbbbbbb" not in serialized
    assert "cccccccccccccccc" not in serialized


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
    assert [row["task_id"] for row in unapproved][-1] == "SLICE-036-child-D"
    assert overlap[0]["scope"]["roots"] == overlap[1]["scope"]["roots"]
    assert network[0]["runtime_input"]["mode"] == "network-control"
    assert survivor[0]["runtime_input"]["mode"] == "survivor"
    assert mismatch[2]["runtime_input"]["mode"] == "oracle-mismatch"
    exact_argv = "\n".join(network[0]["invocation"]["argv"])
    assert "socket.create_connection" in exact_argv
    assert "ranex-slice036-survivor-control-v1" in "\n".join(
        survivor[0]["invocation"]["argv"]
    )


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
