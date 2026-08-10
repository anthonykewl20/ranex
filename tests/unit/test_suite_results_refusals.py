"""Focused refusal and edge contracts for the suite-results parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from ranex.foundation import suite_results

DIGEST = "sha256:" + "a" * 64


def valid_results() -> dict[str, object]:
    return {
        "manifest_digest": DIGEST,
        "counts": {
            "passed": 1,
            "skipped": 0,
            "failed": 0,
            "errors": 0,
            "xfailed": 0,
            "xpassed": 0,
        },
        "non_passed": [],
        "missing": [],
        "extra_count": 0,
        "outcome_digest": DIGEST,
    }


def test_manifest_refuses_non_mapping_expected_skips() -> None:
    with pytest.raises(ValueError, match="expected_skips must be an object"):
        suite_results.manifest_digest({"suite": [], "expected_skips": []})


def test_manifest_refuses_a_blank_expected_skip_reason() -> None:
    with pytest.raises(
        ValueError,
        match="expected-skip reasons must be non-empty strings",
    ):
        suite_results.manifest_digest(
            {
                "suite": ["tests/test_sample.py::test_one"],
                "expected_skips": {"tests/test_sample.py::test_one": " "},
            }
        )


def test_suite_results_refuses_non_list_non_passed() -> None:
    value = valid_results()
    value["non_passed"] = ()

    with pytest.raises(ValueError, match="non_passed must be a list"):
        suite_results.validate_suite_results(value)


def test_suite_results_refuses_non_list_missing() -> None:
    value = valid_results()
    value["missing"] = ()

    with pytest.raises(
        ValueError,
        match="missing must be a list of non-empty test IDs",
    ):
        suite_results.validate_suite_results(value)


def test_junitxml_refuses_a_testcase_without_its_full_id() -> None:
    artifact = b'<testsuites><testcase classname="tests.test_sample"/></testsuites>'

    with pytest.raises(
        ValueError,
        match="testcase must carry classname and name",
    ):
        suite_results.freeze_manifest(artifact)


def test_junitxml_classifies_an_xpass_marked_skip_as_xpassed() -> None:
    artifact = (
        b'<testsuites><testcase classname="tests.test_sample" name="test_one">'
        b'<skipped type="XPASS"/></testcase></testsuites>'
    )
    manifest = {
        "suite": ["tests/test_sample.py::test_one"],
        "expected_skips": {},
    }

    parsed = suite_results.suite_results_from_junitxml(artifact, manifest)

    assert parsed["non_passed"] == [
        ["tests/test_sample.py::test_one", "xpassed"]
    ]
    assert parsed["counts"]["xpassed"] == 1


def test_junitxml_refuses_non_bytes_input() -> None:
    with pytest.raises(TypeError, match="junitxml_bytes must be bytes"):
        suite_results.freeze_manifest("<testsuites/>")  # type: ignore[arg-type]


def test_junitxml_refuses_a_non_utf8_encoding_declaration() -> None:
    artifact = b'<?xml version="1.0" encoding="latin-1"?><testsuites/>'

    with pytest.raises(ValueError, match="must declare UTF-8 encoding"):
        suite_results.freeze_manifest(artifact)


def test_manifest_bytes_refuse_malformed_json() -> None:
    with pytest.raises(ValueError, match="cannot parse suite manifest"):
        suite_results.load_manifest_bytes(b"{")


def test_results_artifact_reports_an_os_read_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    artifact = tmp_path / "results.xml"
    artifact.write_bytes(b"<testsuites/>")

    def refuse_read(descriptor: int, count: int) -> bytes:
        raise OSError("read denied")

    monkeypatch.setattr(suite_results.os, "read", refuse_read)

    with pytest.raises(ValueError, match="cannot read results artifact.*read denied"):
        suite_results.read_results_artifact(artifact)
