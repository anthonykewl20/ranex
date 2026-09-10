"""A SARIF artifact decides only what a frozen scan manifest says it decides.

Every property here is one the kernel already enforces for a suite, restated
for a scanner: absence blocks, the manifest is the universe, evidence is bound
to its subject, and a report producer is never taken at its word about where it
looked. The last one is the F-012 family (ADR-060) in this reporter: a scanner
that can name a line it never read can also stay silent about one it did.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import (
    claim_expectations,
    finding_id,
    freeze_scan_manifest,
    load_scan_manifest_bytes,
    observed_findings,
    scan_expected_ids,
    scan_results_from_sarif,
    validate_scan_manifest,
)

SUBJECT = "pkg/mod.py"
BODY = "import os\n\n\ndef answer():\n    return 42\n"


def sarif(results: list[dict[str, object]], **run: object) -> bytes:
    document = {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "probe"}}, "results": results, **run}],
    }
    return json.dumps(document).encode("utf-8")


def result(line: int = 1, rule: str = "F401", level: str = "error",
           path: str = SUBJECT, snippet: str | None = None) -> dict[str, object]:
    region: dict[str, object] = {"startLine": line, "endLine": line}
    if snippet is not None:
        region["snippet"] = {"text": snippet}
    return {
        "ruleId": rule,
        "level": level,
        "message": {"text": "unused import"},
        "locations": [{"physicalLocation": {
            "artifactLocation": {"uri": path}, "region": region,
        }}],
    }


@pytest.fixture
def subject(tmp_path: Path) -> Path:
    (tmp_path / "pkg").mkdir()
    (tmp_path / SUBJECT).write_text(BODY, encoding="utf-8")
    return tmp_path


@pytest.fixture
def manifest() -> dict[str, object]:
    return dict(validate_scan_manifest({
        "scope": [SUBJECT],
        "rules": ["F401"],
        "blocking_levels": ["error"],
        "accepted": {},
    }))


def test_a_clean_scan_passes_every_scope_path(subject, manifest) -> None:
    summary = scan_results_from_sarif(sarif([]), manifest, subject_root=subject)
    assert summary["non_passed"] == []
    assert summary["missing"] == []
    assert summary["counts"]["passed"] == 1


def test_a_blocking_finding_fails_an_id_the_manifest_froze(subject, manifest) -> None:
    """The property the whole reduction exists for.

    `evaluate()` blocks on IDs the manifest declared, and a finding's own ID
    cannot be declared before the finding exists. So the scope path is what
    fails — and the finding ID rides beside it, signed and retained, rather
    than being the thing the kernel is asked to recognise and silently ignores.
    """

    summary = scan_results_from_sarif(sarif([result()]), manifest, subject_root=subject)
    failed = dict(summary["non_passed"])
    assert failed[SUBJECT] == "failed"
    identifier = next(k for k in failed if k != SUBJECT)
    assert identifier.startswith(f"{SUBJECT}::F401::") and failed[identifier] == "failed"
    assert SUBJECT in scan_expected_ids(manifest)


def test_a_finding_below_the_blocking_level_does_not_decide(subject, manifest) -> None:
    summary = scan_results_from_sarif(
        sarif([result(level="warning")]), manifest, subject_root=subject
    )
    assert summary["non_passed"] == []


def test_an_accepted_finding_is_an_expected_skip(subject, manifest) -> None:
    identifier = finding_id("F401", SUBJECT, 1, 1, b"import os\n")
    manifest = dict(validate_scan_manifest({**manifest, "accepted": {identifier: "reviewed"}}))
    summary = scan_results_from_sarif(sarif([result()]), manifest, subject_root=subject)
    assert summary["non_passed"] == [[identifier, "skipped"]]
    assert identifier in scan_expected_ids(manifest)
    _, _, skips = claim_expectations(canonical_json_bytes(manifest), "sarif-2.1.0")
    assert skips[identifier] == "reviewed"


def test_acceptance_lapses_when_the_accepted_code_changes(subject, manifest) -> None:
    """An accepted ID is bound to the bytes it was accepted over.

    Acceptance that survived an edit to the very line it excused would be a
    standing waiver, which is the one thing a frozen universe must not become.
    """

    identifier = finding_id("F401", SUBJECT, 1, 1, b"import os\n")
    manifest = dict(validate_scan_manifest({**manifest, "accepted": {identifier: "reviewed"}}))
    (subject / SUBJECT).write_text("import sys\n" + BODY.partition("\n")[2], encoding="utf-8")
    summary = scan_results_from_sarif(sarif([result()]), manifest, subject_root=subject)
    assert dict(summary["non_passed"])[SUBJECT] == "failed"


def test_a_region_the_subject_does_not_carry_is_refused(subject, manifest) -> None:
    with pytest.raises(ValueError, match="lies outside"):
        scan_results_from_sarif(sarif([result(line=99)]), manifest, subject_root=subject)


def test_a_snippet_the_subject_does_not_carry_there_is_refused(subject, manifest) -> None:
    with pytest.raises(ValueError, match="does not match the subject"):
        scan_results_from_sarif(
            sarif([result(line=5, snippet="import os")]), manifest, subject_root=subject
        )


def test_a_declared_failure_is_refused_even_with_no_findings(subject, manifest) -> None:
    """The silent-crash trap: a scan that says it failed never reads as clean."""

    with pytest.raises(ValueError, match="executionSuccessful"):
        scan_results_from_sarif(
            sarif([], invocations=[{"executionSuccessful": False}]),
            manifest,
            subject_root=subject,
        )


def test_a_witnessed_scope_path_that_was_not_scanned_is_missing(subject, manifest) -> None:
    """When a producer does witness its coverage, the witness is enforced."""

    manifest = dict(validate_scan_manifest({**manifest, "scope": ["other.py", SUBJECT]}))
    (subject / "other.py").write_text("x = 1\n", encoding="utf-8")
    summary = scan_results_from_sarif(
        sarif([], artifacts=[{"location": {"uri": SUBJECT}}]),
        manifest,
        subject_root=subject,
    )
    assert summary["missing"] == ["other.py"]


def test_a_scope_path_absent_from_the_subject_is_missing(subject, manifest) -> None:
    manifest = dict(validate_scan_manifest({**manifest, "scope": ["gone.py", SUBJECT]}))
    summary = scan_results_from_sarif(sarif([]), manifest, subject_root=subject)
    assert summary["missing"] == ["gone.py"]


def test_a_finding_outside_the_subject_is_refused(subject, manifest) -> None:
    with pytest.raises(ValueError, match="outside the materialised subject"):
        scan_results_from_sarif(
            sarif([result(path="file:///etc/passwd")]), manifest, subject_root=subject
        )


def test_the_same_input_reduces_to_the_same_digest(subject, manifest) -> None:
    first = scan_results_from_sarif(sarif([result()]), manifest, subject_root=subject)
    second = scan_results_from_sarif(sarif([result()]), manifest, subject_root=subject)
    assert first == second


def test_a_manifest_must_be_exact_canonical_bytes(manifest) -> None:
    raw = canonical_json_bytes(manifest)
    assert load_scan_manifest_bytes(raw) == manifest
    with pytest.raises(ValueError, match="exact canonical JSON bytes"):
        load_scan_manifest_bytes(b" " + raw)


def test_a_manifest_that_blocks_on_nothing_is_refused(manifest) -> None:
    """A gate that cannot block is refused at construction — here too."""

    with pytest.raises(ValueError, match="blocking_levels"):
        validate_scan_manifest({**manifest, "blocking_levels": []})


def test_acceptance_outside_the_reviewed_universe_is_refused(manifest) -> None:
    identifier = finding_id("S101", SUBJECT, 1, 1, b"import os\n")
    with pytest.raises(ValueError, match="outside the reviewed rule universe"):
        validate_scan_manifest({**manifest, "accepted": {identifier: "reviewed"}})
    outside = finding_id("F401", "elsewhere.py", 1, 1, b"import os\n")
    with pytest.raises(ValueError, match="outside the frozen scope"):
        validate_scan_manifest({**manifest, "accepted": {outside: "reviewed"}})


def test_a_freeze_refuses_to_accept_a_finding_nobody_observed(subject) -> None:
    """`--accepted` is checked against the run, as `--expected-skip` is."""

    findings = observed_findings(sarif([result()]), subject)
    identifier = findings[0][0]
    frozen = freeze_scan_manifest(
        findings, scope=[SUBJECT], rules=["F401"], blocking_levels=["error"],
        accepted={identifier: "reviewed"},
    )
    assert frozen["accepted"] == {identifier: "reviewed"}
    invented = finding_id("F401", SUBJECT, 1, 1, b"not the subject's bytes\n")
    with pytest.raises(ValueError, match="must name findings the frozen run observed"):
        freeze_scan_manifest(
            findings, scope=[SUBJECT], rules=["F401"], blocking_levels=["error"],
            accepted={invented: "reviewed"},
        )
