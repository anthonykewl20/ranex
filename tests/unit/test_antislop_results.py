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
    ANTISLOP_STRUCTURAL_ID,
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


def kernel_verdict(manifest: dict[str, object], result: dict[str, object]) -> str:
    from ranex.foundation.scan_results import claim_expectations
    from ranex.governed_execution.domain.verdict import Claim, Evidence, Gate, evaluate

    digest, expected_ids, expected_skips = claim_expectations(
        canonical_json_bytes(manifest), "antislop-sarif-2.1.0"
    )
    command_digest = "sha256:" + "c" * 64
    subject_digest = "sha256:" + "a" * 64
    claim = Claim(
        "antislop", command_digest, results_required=True,
        manifest_digest=digest, expected_ids=expected_ids,
        expected_skips=expected_skips,
    )
    observation = Evidence(
        "antislop", subject_digest, "scanner", "ranex antislop",
        command_digest, "/usr/bin/ranex", 0, suite_results=result,
    )
    verdict = evaluate(
        Gate("landing", "ANTISLOP_SANE", (claim,), blocking=True),
        (observation,), subject_digest=subject_digest, approver_id="reviewer",
    )
    return str(verdict.verdict)


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
        ANTISLOP_STRUCTURAL_ID,
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
    # An explicit empty witness reports no files; both the file inventory
    # and every omitted census entry must block admission.
    assert result["missing"] == [
        "test_six.py",
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


@pytest.mark.parametrize(
    ("new_test", "expected_verdict"),
    [
        ("def test_new():\n    assert True\n", "FAIL"),
        ("def test_new():\n    pass\n", "FAIL"),
        ("def test_new():\n    assert operation() == 2\n", "PASS"),
    ],
)
def test_new_file_structural_findings_reach_the_pinned_kernel(
    tmp_path: Path, new_test: str, expected_verdict: str
) -> None:
    manifest = frozen(tmp_path, APPROVED)
    result = reduce_against(
        tmp_path, manifest, {**APPROVED, "test_added.py": new_test}
    )
    assert kernel_verdict(manifest, result) == expected_verdict
    assert result["manifest_digest"] == antislop_expectations_digest(manifest)
    assert "test_added.py" not in manifest["scope"]


def test_uncalled_assertion_cannot_replace_a_frozen_parent_assertion(
    tmp_path: Path,
) -> None:
    manifest = frozen(tmp_path, APPROVED)
    weakened = {
        "test_six.py": APPROVED["test_six.py"].replace(
            "    assert add_doc(1) == '1'\n",
            "    def hidden_assertion():\n        assert False\n",
            1,
        )
    }
    namespace = {}
    exec(compile(weakened["test_six.py"], "nested-control", "exec"), namespace)
    assert namespace["test_add_doc"]() is None
    result = reduce_against(tmp_path, manifest, weakened)
    assert result["non_passed"] == [["test_six.py::test_add_doc", "failed"]]
    assert kernel_verdict(manifest, result) == "FAIL"


@pytest.mark.parametrize("old_binding", ["legacy", "previous-v2"])
def test_signed_legacy_summary_cannot_satisfy_the_repaired_claim(
    tmp_path: Path, old_binding: str,
) -> None:
    from ranex.foundation.canonical import canonical_sha256
    from ranex.foundation.scan_results import claim_expectations
    from ranex.foundation.signing import ENVELOPE_TYPE, generate_keypair, sign_evidence
    from ranex.governed_execution.domain.admission import admit
    from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate

    manifest = frozen(tmp_path, APPROVED)
    result = reduce_against(tmp_path, manifest, APPROVED)
    digest, expected_ids, expected_skips = claim_expectations(
        canonical_json_bytes(manifest), "antislop-sarif-2.1.0"
    )
    legacy = {
        **result,
        "manifest_digest": "sha256:" + canonical_sha256(manifest),
        "counts": {**result["counts"], "passed": len(manifest["scope"])},
        "outcome_digest": "sha256:" + canonical_sha256(
            {path: "passed" for path in manifest["scope"]}
        ),
    }
    if old_binding == "previous-v2":
        legacy = {**result, "manifest_digest": "sha256:" + canonical_sha256({
            "schema": "ranex-antislop-expectations-binding-v2",
            "expectations": manifest,
            "required_structural_id": "ranex/antislop-structural-integrity",
        })}
    private, public = generate_keypair()
    command_digest = "sha256:" + "c" * 64
    subject_digest = "sha256:" + "a" * 64
    claim = Claim(
        "antislop", command_digest, results_required=True,
        manifest_digest=digest, expected_ids=expected_ids,
        expected_skips=expected_skips,
    )
    gate = Gate("landing", "ANTISLOP_SANE", (claim,), blocking=True)
    for summary, expected_verdict in ((legacy, "FAIL"), (result, "PASS")):
        content = {
            "claim_id": "antislop",
            "subject_digest": subject_digest,
            "producer_id": "scanner",
            "command": "ranex antislop",
            "command_digest": command_digest,
            "executable_path": "/usr/bin/ranex",
            "exit_code": 0,
            "suite_results": summary,
            "confinement_result_digest": None,
            "confinement_profile_digest": None,
            "envelope_type": ENVELOPE_TYPE,
            "gate_id": "landing",
            "catalog_digest": "sha256:" + "b" * 64,
        }
        admission = admit(
            [{**content, "signature": sign_evidence(content, private)}],
            {"scanner": public},
        )
        assert admission.rejections == ()
        verdict = evaluate(
            gate, admission.evidence,
            subject_digest=subject_digest, approver_id="reviewer",
        )
        assert str(verdict.verdict) == expected_verdict


@pytest.mark.parametrize("retained", ["test_a.py", "test_z.py"])
def test_missing_files_and_tests_are_one_sorted_union(
    tmp_path: Path, retained: str,
) -> None:
    approved = {
        "test_a.py": "def test_a():\n    assert operation() == 1\n",
        "test_z.py": "def test_z():\n    assert operation() == 2\n",
    }
    manifest = frozen(tmp_path, approved)
    # The retained file is witnessed, but both frozen tests disappeared.
    result = reduce_against(tmp_path, manifest, {retained: "# test removed\n"})
    removed = next(path for path in approved if path != retained)
    assert result["missing"] == sorted({
        removed, "test_a.py::test_a", "test_z.py::test_z",
    })
    assert kernel_verdict(manifest, result) == "FAIL"


def test_missing_scope_and_test_overlap_is_deduplicated(tmp_path: Path) -> None:
    manifest = {
        "scope": ["test_a.py", "test_a.py::test_a"],
        "tests": {"test_a.py::test_a": 1},
    }
    # Scope path spellings are currently allowed to include colons. Even
    # when one overlaps a frozen test ID, missing outcomes remain a set.
    result = reduce_against(tmp_path, manifest, {"test_a.py": "# removed\n"})
    assert result["missing"] == ["test_a.py::test_a"]
    assert kernel_verdict(manifest, result) == "FAIL"


def test_explicit_empty_artifacts_does_not_certify_antislop_scope(tmp_path):
    root = build(tmp_path / "subject", APPROVED)
    raw = antislop_sarif_bytes(root)
    manifest = freeze_antislop_expectations(raw, subject_root=root)
    document = json.loads(raw)
    document["runs"][0]["artifacts"] = []
    result = antislop_results_from_sarif(canonical_json_bytes(document), manifest, subject_root=root)
    assert result["missing"] == ["test_six.py"]
    assert kernel_verdict(manifest, result) == "FAIL"


@pytest.mark.parametrize("artifacts", [None, {}, [None], [{"location": {}}]])
def test_antislop_malformed_artifact_witness_is_refused(tmp_path, artifacts):
    root = build(tmp_path / "subject", APPROVED)
    raw = antislop_sarif_bytes(root)
    manifest = freeze_antislop_expectations(raw, subject_root=root)
    document = json.loads(raw)
    document["runs"][0]["artifacts"] = artifacts
    with pytest.raises(ValueError, match="artifacts|location|URI"):
        antislop_results_from_sarif(canonical_json_bytes(document), manifest, subject_root=root)
