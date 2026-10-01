"""A SARIF artifact decides only what a frozen scan manifest says it decides.

Every property here is one the kernel already enforces for a suite, restated
for a scanner: absence blocks, the manifest is the universe, evidence is bound
to its subject, and a report producer is never taken at its word about where it
looked. The last one is the F-012 family (ADR-060) in this reporter: a scanner
that can name a line it never read can also stay silent about one it did.
"""

from __future__ import annotations

import json
import subprocess
import sys
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
    # This fixture declares its actual subject file, independently of whatever
    # frozen scope a particular test asks the reducer to enforce.
    run.setdefault("artifacts", [{"location": {"uri": SUBJECT}}])
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


@pytest.mark.parametrize("successful_invocation", [False, True])
def test_absent_path_coverage_is_missing_even_when_scope_exists(subject, manifest, successful_invocation):
    document = json.loads(sarif([]))
    document["runs"][0].pop("artifacts")
    if successful_invocation:
        document["runs"][0]["invocations"] = [{"executionSuccessful": True}]
    summary = scan_results_from_sarif(json.dumps(document).encode(), manifest, subject_root=subject)
    assert summary["missing"] == [SUBJECT]


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



@pytest.mark.parametrize("old_binding,require_review", [
    pytest.param("legacy", False, id="legacy"),
    pytest.param("previous-v2", False, id="previous-v2"),
    pytest.param("previous-review-required", False, id="previous-review-required"),
    pytest.param("previous-coverage", False, id="previous-coverage"),
    pytest.param("previous-coverage", True, id="previous-coverage-required-review"),
])
def test_signed_legacy_scan_summary_cannot_satisfy_versioned_expectations(
    subject: Path, manifest: dict[str, object], old_binding: str, require_review: bool,
) -> None:
    from ranex.foundation.canonical import canonical_sha256
    from ranex.foundation.signing import ENVELOPE_TYPE, generate_keypair, sign_evidence
    from ranex.governed_execution.domain.admission import admit
    from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate

    raw = sarif([])
    if require_review:
        from ranex.foundation.delegated_review import (
            build_packet,
            empty_handbook_digest,
            packet_bytes,
            packet_digest,
        )

        packet = build_packet(subject_digest="sha256:" + "a" * 64,
                              range_base="b" * 40, range_head="c" * 40,
                              handbook_digest=empty_handbook_digest(), chapters=[])
        (subject / "governance").mkdir()
        (subject / "governance/review-packet.json").write_bytes(packet_bytes(packet))
        document = json.loads(raw)
        document["runs"][0]["properties"] = {"packet_digest": packet_digest(packet)}
        raw = json.dumps(document).encode()
    current = scan_results_from_sarif(raw, manifest, subject_root=subject, require_review=require_review)
    old_digest = "sha256:" + canonical_sha256(manifest)
    if old_binding in {"previous-v2", "previous-review-required"}:
        old_digest = "sha256:" + canonical_sha256({
            "schema": "ranex-scan-expectations-binding-v2",
            "semantics": {
                "review_identity": "excerpt-category-occurrence-v1",
                "review_severity": "explicit-then-driver-default-v1",
                "review_category": "rule-id-then-properties-category-v1",
                "review_packet": "all-declarations-bound-v1",
                "coverage": "explicit-witness-required-v1",
                "generic_identity": "subject-region-v1",
            }, "manifest": manifest,
        })
    if old_binding == "previous-review-required":
        old_digest = "sha256:" + canonical_sha256({
            "schema": "ranex-scan-expectations-binding-v2",
            "semantics": {
                "review_identity": "excerpt-category-occurrence-v1",
                "review_severity": "explicit-then-driver-default-v1",
                "review_category": "rule-id-then-properties-category-v1",
                "review_packet": "trusted-required-dispatch-v2",
                "review_required": False,
                "coverage": "explicit-witness-required-v1",
                "generic_identity": "subject-region-v1",
            }, "manifest": manifest,
        })
    if old_binding == "previous-coverage":
        old_digest = "sha256:" + canonical_sha256({
            "schema": "ranex-scan-expectations-binding-v2",
            "semantics": {
                "review_identity": "excerpt-category-occurrence-v1",
                "review_severity": "explicit-then-driver-default-v1",
                "review_category": "rule-id-then-properties-category-v1",
                "review_packet": "trusted-required-dispatch-v2",
                "review_required": require_review,
                "ingestion_core": "strict-interpreted-structure-v3-confined-subject-reads",
                "coverage": "explicit-witness-required-v1",
                "generic_identity": "subject-region-v1",
            }, "manifest": manifest,
        })
    legacy = {**current, "manifest_digest": old_digest}
    reporter = "delegated-review-sarif-2.1.0" if require_review else "sarif-2.1.0"
    digest, ids, skips = claim_expectations(canonical_json_bytes(manifest), reporter)
    private, public = generate_keypair()
    command_digest = "sha256:" + "c" * 64
    subject_digest = "sha256:" + "a" * 64
    gate = Gate("landing", "SCAN_CLEAN", (Claim(
        "scan", command_digest, results_required=True,
        manifest_digest=digest, expected_ids=ids, expected_skips=skips,
    ),), blocking=True)
    for summary, expected in ((legacy, "FAIL"), (current, "PASS")):
        content = {
            "claim_id": "scan", "subject_digest": subject_digest,
            "producer_id": "scanner", "command": "scanner",
            "command_digest": command_digest, "executable_path": "/usr/bin/scanner",
            "exit_code": 0, "suite_results": summary,
            "confinement_result_digest": None, "confinement_profile_digest": None,
            "envelope_type": ENVELOPE_TYPE, "gate_id": "landing",
            "catalog_digest": "sha256:" + "b" * 64,
        }
        admission = admit(
            [{**content, "signature": sign_evidence(content, private)}], {"scanner": public}
        )
        assert admission.rejections == ()
        verdict = evaluate(gate, admission.evidence,
                           subject_digest=subject_digest, approver_id="reviewer")
        assert str(verdict.verdict) == expected



def test_explicit_empty_cli_coverage_is_missing_and_blocks(subject, manifest, tmp_path) -> None:
    from ranex.governed_execution.domain.verdict import Claim, Evidence, Gate, evaluate

    empty = tmp_path / "empty"
    empty.mkdir()
    artifact = tmp_path / "empty.sarif"
    completed = subprocess.run(
        [sys.executable, "-m", "ranex.foundation.markers", "--root", str(empty),
         "--output-file", str(artifact)],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(artifact.read_bytes())["runs"][0]["artifacts"] == []
    summary = scan_results_from_sarif(artifact.read_bytes(), manifest, subject_root=subject)
    assert summary["missing"] == [SUBJECT]
    digest, ids, skips = claim_expectations(canonical_json_bytes(manifest), "sarif-2.1.0")
    command_digest = "sha256:" + "c" * 64
    subject_digest = "sha256:" + "a" * 64
    claim = Claim("scan", command_digest, results_required=True,
                  manifest_digest=digest, expected_ids=ids, expected_skips=skips)
    observation = Evidence("scan", subject_digest, "scanner", "scanner", command_digest,
                           "/usr/bin/scanner", 0, suite_results=summary)
    verdict = evaluate(Gate("landing", "SCAN_CLEAN", (claim,), blocking=True),
                       (observation,), subject_digest=subject_digest, approver_id="reviewer")
    assert str(verdict.verdict) == "FAIL"


@pytest.mark.parametrize("artifacts", [None, {}, [None], [{}], [{"location": {}}],
                                      [{"location": "mod.py"}]])
def test_malformed_explicit_coverage_is_refused(subject, manifest, artifacts) -> None:
    with pytest.raises(ValueError, match="artifacts|artifact"):
        scan_results_from_sarif(sarif([], artifacts=artifacts), manifest, subject_root=subject)
