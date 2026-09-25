"""Frozen antislop expectations and the seam-B reduction over the census.

An antislop claim's frozen universe is not a file set but the per-test
effective-assert counts of the approved tree. The reduction keeps the closed
suite-summary shape `verdict.py` already decides on, so `evaluate()` and the
envelope learn nothing; the manifest is a trust root read from the governing
commit exactly like a scan manifest (ADR-060 seam C).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.foundation.antislop import antislop_sarif_bytes
from ranex.foundation.antislop_results import (
    ANTISLOP_REPORTERS,
    antislop_expectations_digest,
    antislop_expected_ids,
    antislop_expected_skips,
    antislop_results_from_sarif,
    freeze_antislop_expectations,
    load_antislop_expectations_bytes,
    validate_antislop_expectations,
)
from ranex.foundation.canonical import canonical_json_bytes

APPROVED = {
    "test_six.py": (
        "def test_add_doc():\n"
        "    assert add_doc(1) == '1'\n"
        "\n"
        "def test_integer_types():\n"
        "    assert add_doc(1) == '1'\n"
        "    assert add_doc(-1) == '-1'\n"
        "    assert add_doc(0) == '0'\n"
        "    assert add_doc(1.0) == '1.0'\n"
    )
}


def build(tmp_path: Path, files: dict[str, str]) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp_path


def frozen(tmp_path: Path, files: dict[str, str]) -> dict[str, object]:
    root = build(tmp_path / "approved", files)
    return freeze_antislop_expectations(
        antislop_sarif_bytes(root), subject_root=root
    )


def reduce_against(
    tmp_path: Path, manifest: dict[str, object], files: dict[str, str]
) -> dict[str, object]:
    candidate = build(tmp_path / "candidate", files)
    return antislop_results_from_sarif(
        antislop_sarif_bytes(candidate), manifest, subject_root=candidate
    )


# --- the manifest: exact canonical bytes, a closed universe ------------------


def test_freeze_records_the_approved_census(tmp_path: Path) -> None:
    manifest = frozen(tmp_path, APPROVED)
    assert manifest == {
        "scope": ["test_six.py"],
        "tests": {
            "test_six.py::test_add_doc": 1,
            "test_six.py::test_integer_types": 4,
        },
    }
    assert load_antislop_expectations_bytes(canonical_json_bytes(manifest)) == manifest


def test_manifest_bytes_must_be_exact_canonical_json(tmp_path: Path) -> None:
    manifest = frozen(tmp_path, APPROVED)
    with pytest.raises(ValueError, match="exact canonical JSON"):
        load_antislop_expectations_bytes(
            json.dumps(manifest, indent=1).encode("utf-8")
        )


def test_manifest_shape_is_refused_where_it_is_wrong(tmp_path: Path) -> None:
    good = frozen(tmp_path, APPROVED)
    with pytest.raises(ValueError, match="exactly"):
        validate_antislop_expectations({**good, "accepted": {}})
    with pytest.raises(ValueError, match="sorted and unique"):
        validate_antislop_expectations(
            {**good, "scope": ["test_six.py", "test_six.py"]}
        )
    with pytest.raises(ValueError, match="sorted"):
        validate_antislop_expectations(
            {
                "scope": ["test_six.py"],
                "tests": {
                    "test_six.py::test_integer_types": 4,
                    "test_six.py::test_add_doc": 1,
                },
            }
        )
    with pytest.raises(ValueError, match="inside the frozen scope"):
        validate_antislop_expectations(
            {"scope": ["test_six.py"], "tests": {"test_other.py::test_add_doc": 1}}
        )
    with pytest.raises(ValueError, match="non-negative"):
        validate_antislop_expectations(
            {"scope": ["test_six.py"], "tests": {"test_six.py::test_add_doc": -1}}
        )
    with pytest.raises(ValueError, match="about nothing"):
        validate_antislop_expectations({"scope": [], "tests": {}})


def test_expected_ids_carry_both_families(tmp_path: Path) -> None:
    manifest = frozen(tmp_path, APPROVED)
    assert antislop_expected_ids(manifest) == (
        "test_six.py",
        "test_six.py::test_add_doc",
        "test_six.py::test_integer_types",
    )
    assert antislop_expected_skips(manifest) == {}
    assert antislop_expectations_digest(manifest).startswith("sha256:")
    assert ANTISLOP_REPORTERS == frozenset({"antislop-sarif-2.1.0"})


def test_freeze_refuses_a_tree_that_already_carries_violations(
    tmp_path: Path,
) -> None:
    root = build(tmp_path, {"test_six.py": "def test_taut():\n    assert True\n"})
    with pytest.raises(ValueError, match="already carries antislop violations"):
        freeze_antislop_expectations(antislop_sarif_bytes(root), subject_root=root)


# --- the reduction: the closed summary, decided against the freeze -----------


def test_an_unchanged_tree_passes(tmp_path: Path) -> None:
    result = reduce_against(tmp_path, frozen(tmp_path, APPROVED), APPROVED)
    assert result["counts"]["failed"] == 0
    assert result["missing"] == []
    assert result["non_passed"] == []
    assert result["extra_count"] == 0
    assert result["manifest_digest"] == antislop_expectations_digest(
        frozen(tmp_path, APPROVED)
    )


def test_three_repeats_are_byte_identical(tmp_path: Path) -> None:
    manifest = frozen(tmp_path, APPROVED)
    digests = {
        json.dumps(reduce_against(tmp_path, manifest, APPROVED), sort_keys=True)
        for _ in range(3)
    }
    assert len(digests) == 1


def test_assert_commented_fails_the_test_that_did_less(tmp_path: Path) -> None:
    weakened = {
        "test_six.py": (
            "def test_add_doc():\n"
            "    assert add_doc(1) == '1'\n"
            "\n"
            "def test_integer_types():\n"
            "    assert add_doc(1) == '1'\n"
            "    assert add_doc(-1) == '-1'\n"
            "    # assert add_doc(0) == '0'\n"
            "    assert add_doc(1.0) == '1.0'\n"
        )
    }
    result = reduce_against(tmp_path, frozen(tmp_path, APPROVED), weakened)
    assert result["non_passed"] == [["test_six.py::test_integer_types", "failed"]]
    assert result["counts"]["failed"] == 1


def test_body_removed_fails_both_ways(tmp_path: Path) -> None:
    gutted = {
        "test_six.py": (
            "def test_add_doc():\n"
            "    pass\n"
            "\n"
            "def test_integer_types():\n"
            "    assert add_doc(1) == '1'\n"
            "    assert add_doc(-1) == '-1'\n"
            "    assert add_doc(0) == '0'\n"
            "    assert add_doc(1.0) == '1.0'\n"
        )
    }
    result = reduce_against(tmp_path, frozen(tmp_path, APPROVED), gutted)
    failed = {identifier for identifier, _ in result["non_passed"]}
    # The census shortfall (0 < 1) and the structural pass-body both land.
    assert "test_six.py::test_add_doc" in failed
    assert any(
        identifier.startswith("test_six.py::ranex/antislop-pass-body::")
        for identifier, _ in result["non_passed"]
    )


def test_tautology_fails_the_file_and_the_test(tmp_path: Path) -> None:
    slop = {
        "test_six.py": (
            "def test_add_doc():\n"
            "    assert True\n"
            "\n"
            "def test_integer_types():\n"
            "    assert add_doc(1) == '1'\n"
            "    assert add_doc(-1) == '-1'\n"
            "    assert add_doc(0) == '0'\n"
            "    assert add_doc(1.0) == '1.0'\n"
        )
    }
    result = reduce_against(tmp_path, frozen(tmp_path, APPROVED), slop)
    failed = {identifier for identifier, _ in result["non_passed"]}
    assert "test_six.py" in failed
    assert "test_six.py::test_add_doc" in failed
    assert any(
        identifier.startswith("test_six.py::ranex/antislop-tautology::")
        for identifier, _ in result["non_passed"]
    )


def test_a_deleted_test_is_missing_and_blocks(tmp_path: Path) -> None:
    deleted = {
        "test_six.py": (
            "def test_add_doc():\n"
            "    assert add_doc(1) == '1'\n"
        )
    }
    result = reduce_against(tmp_path, frozen(tmp_path, APPROVED), deleted)
    assert result["missing"] == ["test_six.py::test_integer_types"]


def test_an_empty_artifact_is_all_missing_not_a_pass(tmp_path: Path) -> None:
    """The absence check that makes the census self-arming: a producer that
    reports nothing at all has removed every frozen test from observation."""

    manifest = frozen(tmp_path, APPROVED)
    empty = {
        "version": "2.1.0",
        "runs": [
            {
                "tool": {"driver": {"name": "ranex-antislop", "rules": []}},
                "invocations": [{"executionSuccessful": True}],
                "artifacts": [],
                "results": [],
            }
        ],
    }
    result = antislop_results_from_sarif(
        canonical_json_bytes(empty),
        manifest,
        subject_root=build(tmp_path / "candidate", APPROVED),
    )
    # The file itself stays guarded by the family's existence/witness rule
    # (an empty witness list is no witness, as for ruff); the census is what
    # cannot be quietly emptied — every frozen test became a miss.
    assert result["missing"] == [
        "test_six.py::test_add_doc",
        "test_six.py::test_integer_types",
    ]


def test_a_new_test_is_extra_not_missing(tmp_path: Path) -> None:
    extended = {
        "test_six.py": APPROVED["test_six.py"]
        + "def test_new():\n    assert new() is None\n",
        "test_more.py": "def test_more():\n    assert more() == 2\n",
    }
    manifest = frozen(tmp_path, APPROVED)
    result = reduce_against(tmp_path, manifest, extended)
    assert result["missing"] == []
    assert result["extra_count"] == 2  # the two census entries no freeze names
    assert result["counts"]["failed"] == 0


def test_more_assertions_than_frozen_still_pass(tmp_path: Path) -> None:
    strengthened = {
        "test_six.py": APPROVED["test_six.py"] + "    assert add_doc(2) == '2'\n"
    }
    result = reduce_against(tmp_path, frozen(tmp_path, APPROVED), strengthened)
    assert result["non_passed"] == []


def test_the_universe_cannot_be_swapped_by_the_subject(tmp_path: Path) -> None:
    """The manifest the reduction compares against is the caller's frozen
    bytes; a candidate tree carrying its own weakened copy has no effect the
    reduction could observe."""

    manifest = frozen(tmp_path, APPROVED)
    candidate = build(tmp_path / "candidate", APPROVED)
    weakened = {"scope": ["test_six.py"], "tests": {}}
    (candidate / "governance" / "antislop").mkdir(parents=True)
    (candidate / "governance" / "antislop" / "expectations.json").write_bytes(
        canonical_json_bytes(weakened)
    )
    result = antislop_results_from_sarif(
        antislop_sarif_bytes(candidate), manifest, subject_root=candidate
    )
    assert result["counts"]["failed"] == 0
    assert result["manifest_digest"] == antislop_expectations_digest(manifest)
