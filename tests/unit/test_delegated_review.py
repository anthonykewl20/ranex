"""#102 — delegated-review packet, anchors, prose-free fingerprints.

Callers: pytest discovery under tests/unit/. Exercises
ranex.foundation.delegated_review and scan_results packet admission.
No production data; synthetic digests and tmp_path trees only.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.delegated_review import (
    build_packet,
    delegated_review_results_from_sarif,
    empty_handbook_digest,
    finding_id,
    packet_digest,
    prose_free_fingerprint,
    rederive_findings,
    resolve_anchor,
)
from ranex.foundation.scan_results import observed_findings, scan_results_from_sarif

SUBJECT = "sha256:" + "a" * 64
BASE = "b" * 40
HEAD = "c" * 40


def _packet(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "subject_digest": SUBJECT,
        "range_base": BASE,
        "range_head": HEAD,
        "handbook_digest": empty_handbook_digest(),
        "chapters": (),
    }
    base.update(overrides)
    return build_packet(**base)  # type: ignore[arg-type]


def test_packet_digest_is_byte_identical_across_repeats() -> None:
    assert packet_digest(_packet()) == packet_digest(_packet())


def test_packet_digest_moves_when_any_field_moves() -> None:
    assert packet_digest(_packet()) != packet_digest(_packet(range_head="d" * 40))


def test_prose_free_fingerprint_ignores_message_prose() -> None:
    assert prose_free_fingerprint("pkg/a.py", "cat", "x = 1") == prose_free_fingerprint(
        "pkg/a.py", "cat", "x = 1"
    )
    assert prose_free_fingerprint("pkg/a.py", "cat", "x = 1") != prose_free_fingerprint(
        "pkg/a.py", "cat", "x = 2"
    )


def test_occurrence_disambiguates_duplicate_base_fingerprints() -> None:
    assert finding_id("pkg/a.py", "cat", "x = 1", occurrence=0) != finding_id(
        "pkg/a.py", "cat", "x = 1", occurrence=1
    )


def test_resolve_anchor_derives_lines_from_excerpt(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    assert resolve_anchor(tmp_path, "mod.py", "beta") == (2, 2)


def test_resolve_anchor_refuses_ambiguous_excerpt(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("x = 1\ny = 2\nx = 1\n", encoding="utf-8")
    assert resolve_anchor(tmp_path, "mod.py", "x = 1") is None


def test_unresolvable_anchor_refuses_admission(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("ok = True\n", encoding="utf-8")
    packet = _packet()
    digest = packet_digest(packet)
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "properties": {"packet_digest": digest},
                "tool": {"driver": {"name": "t", "rules": [{"id": "r"}]}},
                "results": [
                    {
                        "ruleId": "r",
                        "level": "warning",
                        "message": {"text": "prose"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "mod.py"},
                                    "region": {
                                        "startLine": 99,
                                        "endLine": 99,
                                        "snippet": {"text": "missing excerpt"},
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }
    manifest = {
        "scope": ["mod.py"],
        "rules": ["r"],
        "blocking_levels": ["error"],
        "accepted": {},
    }
    with pytest.raises(ValueError, match="unresolvable"):
        delegated_review_results_from_sarif(
            canonical_json_bytes(sarif),
            manifest,
            subject_root=tmp_path,
            expected_packet_digest=digest,
        )


def test_packet_substitution_refused(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("value = 1\n", encoding="utf-8")
    digest = packet_digest(_packet())
    other = packet_digest(_packet(range_head="e" * 40))
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "properties": {"packet_digest": other},
                "tool": {"driver": {"name": "t", "rules": [{"id": "r"}]}},
                "results": [],
            }
        ],
    }
    manifest = {
        "scope": ["mod.py"],
        "rules": ["r"],
        "blocking_levels": ["error"],
        "accepted": {},
    }
    with pytest.raises(ValueError, match="substitution refused"):
        delegated_review_results_from_sarif(
            canonical_json_bytes(sarif),
            manifest,
            subject_root=tmp_path,
            expected_packet_digest=digest,
        )


def test_forged_line_numbers_are_rederived(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("first\nsecond\nthird\n", encoding="utf-8")
    packet = _packet()
    digest = packet_digest(packet)
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance" / "review-packet.json").write_bytes(
        canonical_json_bytes(packet)
    )
    sarif = {
        "version": "2.1.0",
        "runs": [
            {
                "properties": {"packet_digest": digest},
                "tool": {"driver": {"name": "t", "rules": [{"id": "r"}]}},
                "results": [
                    {
                        "ruleId": "r",
                        "level": "warning",
                        "message": {"text": "anything"},
                        "locations": [
                            {
                                "physicalLocation": {
                                    "artifactLocation": {"uri": "mod.py"},
                                    "region": {
                                        "startLine": 99,
                                        "endLine": 99,
                                        "snippet": {"text": "second"},
                                    },
                                }
                            }
                        ],
                    }
                ],
            }
        ],
    }
    assert len(rederive_findings(sarif, tmp_path)) == 1
    summary = scan_results_from_sarif(
        canonical_json_bytes(sarif),
        {
            "scope": ["mod.py"],
            "rules": ["r"],
            "blocking_levels": ["error"],
            "accepted": {},
        },
        subject_root=tmp_path,
    )
    assert summary["counts"]["passed"] == 1


def test_fingerprint_stable_under_message_rewrite() -> None:
    a = finding_id("mod.py", "r", "target = True")
    assert a == finding_id("mod.py", "r", "target = True")
    assert a.split("::")[-1] == hashlib.sha256(
        canonical_json_bytes(
            {
                "path": "mod.py",
                "category": "r",
                "excerpt": "target = True",
                "occurrence": 0,
            }
        )
    ).hexdigest()



def worker_cli_artifact(tmp_path: Path) -> bytes:
    (tmp_path / "mod.py").write_text("target = True\n", encoding="utf-8")
    (tmp_path / "governance").mkdir()
    packet = _packet()
    (tmp_path / "governance" / "review-packet.json").write_bytes(
        canonical_json_bytes(packet)
    )
    artifact = tmp_path / "worker.sarif"
    completed = subprocess.run(
        [sys.executable, "-m", "ranex.foundation.delegated_review", "--root",
         str(tmp_path), "--output-format", "sarif", "--output-file", str(artifact),
         "--path", "mod.py", "--excerpt", "target = True", "--category", "r",
         "--level", "error", "--forge-lines", "99:99"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return artifact.read_bytes()


def test_worker_cli_identity_survives_freeze_acceptance_and_duplicate_reduction(
    tmp_path: Path,
) -> None:
    raw = worker_cli_artifact(tmp_path)
    identifier = finding_id("mod.py", "r", "target = True")
    assert observed_findings(raw, tmp_path) == ((identifier, "mod.py", "error"),)
    manifest = {"scope": ["mod.py"], "rules": ["r"],
                "blocking_levels": ["error"], "accepted": {identifier: "reviewed"}}
    summary = scan_results_from_sarif(raw, manifest, subject_root=tmp_path)
    assert summary["non_passed"] == [[identifier, "skipped"]]
    doc = json.loads(raw)
    doc["runs"][0]["results"].append(doc["runs"][0]["results"][0].copy())
    second = finding_id("mod.py", "r", "target = True", occurrence=1)
    summary = scan_results_from_sarif(
        canonical_json_bytes(doc), {**manifest, "accepted": {}}, subject_root=tmp_path
    )
    assert summary["non_passed"] == sorted([
        ["mod.py", "failed"], [identifier, "failed"], [second, "failed"]
    ])
    # Anchors move and message prose changes without replacing finding identity.
    (tmp_path / "mod.py").write_text("# preface\ntarget = True\n", encoding="utf-8")
    doc["runs"][0]["results"][0]["message"] = {"text": "rewritten prose"}
    assert {item[0] for item in observed_findings(canonical_json_bytes(doc), tmp_path)} == {
        identifier, second
    }


@pytest.mark.parametrize("consumer", ["generic", "delegated"])
@pytest.mark.parametrize("contradiction", ["later_run", "top_level", "malformed_run"])
def test_all_review_packet_declarations_must_match(
    tmp_path: Path, consumer: str, contradiction: str
) -> None:
    doc = json.loads(worker_cli_artifact(tmp_path))
    if contradiction == "top_level":
        doc["properties"] = {"packet_digest": "sha256:" + "e" * 64}
    else:
        digest = "not-a-digest" if contradiction == "malformed_run" else "sha256:" + "e" * 64
        doc["runs"].append({"properties": {"packet_digest": digest}, "results": []})
    manifest = {"scope": ["mod.py"], "rules": ["r"],
                "blocking_levels": ["error"], "accepted": {}}
    with pytest.raises(ValueError, match="packet_digest"):
        if consumer == "generic":
            scan_results_from_sarif(canonical_json_bytes(doc), manifest, subject_root=tmp_path)
        else:
            delegated_review_results_from_sarif(
                canonical_json_bytes(doc), manifest, subject_root=tmp_path,
                expected_packet_digest=packet_digest(_packet()),
            )


def test_packet_on_later_run_dispatches_review_anchor_validation(tmp_path: Path) -> None:
    doc = json.loads(worker_cli_artifact(tmp_path))
    doc["runs"].insert(0, {"tool": {"driver": {"name": "empty-worker"}}, "results": []})
    identifier = finding_id("mod.py", "r", "target = True")
    assert observed_findings(canonical_json_bytes(doc), tmp_path) == (
        (identifier, "mod.py", "error"),
    )
    summary = scan_results_from_sarif(
        canonical_json_bytes(doc),
        {"scope": ["mod.py"], "rules": ["r"], "blocking_levels": ["error"],
         "accepted": {identifier: "reviewed"}}, subject_root=tmp_path,
    )
    assert summary["non_passed"] == [[identifier, "skipped"]]


@pytest.mark.parametrize("explicit_level, accepted, expected", [
    (None, False, "failed"), (None, True, "skipped"), ("warning", False, "passed")
])
def test_review_rule_default_level_applies_unless_explicitly_overridden(
    tmp_path: Path, explicit_level: str | None, accepted: bool, expected: str,
) -> None:
    doc = json.loads(worker_cli_artifact(tmp_path))
    run = doc["runs"][0]
    run["tool"]["driver"]["rules"][0]["defaultConfiguration"] = {"level": "error"}
    entry = run["results"][0]
    entry.pop("level")
    if explicit_level is not None:
        entry["level"] = explicit_level
    identifier = finding_id("mod.py", "r", "target = True")
    manifest = {"scope": ["mod.py"], "rules": ["r"], "blocking_levels": ["error"],
                "accepted": {identifier: "reviewed"} if accepted else {}}
    summary = scan_results_from_sarif(canonical_json_bytes(doc), manifest, subject_root=tmp_path)
    if expected == "passed":
        assert summary["non_passed"] == []
    else:
        assert dict(summary["non_passed"])[identifier] == expected


@pytest.mark.parametrize("rule_id", [None, "r"])
def test_review_category_fallback_is_the_effective_rule_id(
    tmp_path: Path, rule_id: str | None,
) -> None:
    doc = json.loads(worker_cli_artifact(tmp_path))
    entry = doc["runs"][0]["results"][0]
    if rule_id is None:
        entry.pop("ruleId")
    entry["properties"] = {"category": "r" if rule_id is None else "ignored-category"}
    identifier = finding_id("mod.py", "r", "target = True")
    assert observed_findings(canonical_json_bytes(doc), tmp_path) == (
        (identifier, "mod.py", "error"),
    )
    summary = scan_results_from_sarif(
        canonical_json_bytes(doc),
        {"scope": ["mod.py"], "rules": ["r"], "blocking_levels": ["error"],
         "accepted": {identifier: "reviewed"}}, subject_root=tmp_path,
    )
    assert summary["non_passed"] == [[identifier, "skipped"]]
    if rule_id is None:
        # Ordinary scanner artifacts retain their ruleId requirement.
        entry["locations"][0]["physicalLocation"]["region"]["startLine"] = 1
        entry["locations"][0]["physicalLocation"]["region"]["endLine"] = 1
        doc["runs"][0].pop("properties")
        with pytest.raises(ValueError, match="ruleId"):
            observed_findings(canonical_json_bytes(doc), tmp_path)


@pytest.mark.parametrize("mode", ["explicit", "required", "freeze", "reader", "freeze_reader"])
def test_required_review_cannot_downgrade_when_packet_metadata_is_removed(tmp_path, mode):
    from ranex.cli.main import _scan_artifact_reader, _scan_freeze_reader
    from ranex.foundation.delegated_review import packet_bytes
    (tmp_path / "mod.py").write_text("value = 1\n")
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance/review-packet.json").write_bytes(packet_bytes(_packet()))
    raw = canonical_json_bytes({"version": "2.1.0", "runs": [{
        "tool": {"driver": {"name": "worker"}}, "results": []}]})
    manifest = {"scope": ["mod.py"], "rules": ["r"], "blocking_levels": ["error"], "accepted": {}}
    path = tmp_path / "governance/scan.sarif"
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="packet_digest"):
        if mode == "explicit":
            scan_results_from_sarif(raw, manifest, subject_root=tmp_path,
                                    expected_packet_digest=packet_digest(_packet()))
        elif mode == "required":
            scan_results_from_sarif(raw, manifest, subject_root=tmp_path, require_review=True)
        elif mode == "freeze":
            observed_findings(raw, tmp_path, require_review=True)
        elif mode == "reader":
            _scan_artifact_reader(manifest, Path("governance/scan.sarif"),
                                  reporter="delegated-review-sarif-2.1.0")(path)
        else:
            _scan_freeze_reader(Path("governance/scan.sarif"),
                                reporter="delegated-review-sarif-2.1.0")(path)
    # A packet beside an ordinary scanner does not impose review semantics.
    assert scan_results_from_sarif(raw, manifest, subject_root=tmp_path)["counts"]["passed"] == 1


def test_review_reporter_expectations_cannot_reuse_generic_signed_summary():
    from ranex.foundation.scan_results import claim_expectations
    raw = canonical_json_bytes({"scope": ["mod.py"], "rules": ["r"],
                               "blocking_levels": ["error"], "accepted": {}})
    generic = claim_expectations(raw, "sarif-2.1.0")
    review = claim_expectations(raw, "delegated-review-sarif-2.1.0")
    assert review[1:] == generic[1:]
    assert review[0] != generic[0]


@pytest.mark.parametrize("state", ["missing", "malformed", "substituted"])
def test_required_review_validates_subject_packet_before_reduction(tmp_path, state):
    from ranex.foundation.delegated_review import packet_bytes
    (tmp_path / "mod.py").write_text("value = 1\n")
    (tmp_path / "governance").mkdir()
    path = tmp_path / "governance/review-packet.json"
    if state == "malformed":
        path.write_bytes(b"{}")
    elif state == "substituted":
        path.write_bytes(packet_bytes(_packet(range_head="d" * 40)))
    raw = canonical_json_bytes({"version": "2.1.0", "runs": [{
        "properties": {"packet_digest": packet_digest(_packet())},
        "tool": {"driver": {"name": "worker"}}, "results": []}]})
    manifest = {"scope": ["mod.py"], "rules": ["r"], "blocking_levels": ["error"], "accepted": {}}
    with pytest.raises(ValueError):
        scan_results_from_sarif(raw, manifest, subject_root=tmp_path, require_review=True)
    with pytest.raises(ValueError):
        observed_findings(raw, tmp_path, require_review=True)


@pytest.mark.parametrize("scope,missing", [(["mod.py"], []), (["mod.py", "unread.py"], ["unread.py"])])
def test_worker_cli_witnesses_only_the_file_it_actually_reads(
    tmp_path: Path, scope: list[str], missing: list[str],
) -> None:
    """Real worker output qualifies one path without claiming an unread second path."""
    (tmp_path / "mod.py").write_text("target = True\n", encoding="utf-8")
    (tmp_path / "unread.py").write_text("unreviewed = True\n", encoding="utf-8")
    (tmp_path / "governance").mkdir()
    (tmp_path / "governance/review-packet.json").write_bytes(canonical_json_bytes(_packet()))
    artifact = tmp_path / "worker.sarif"
    completed = subprocess.run(
        [sys.executable, "-m", "ranex.foundation.delegated_review", "--root", str(tmp_path),
         "--output-format", "sarif", "--output-file", str(artifact), "--path", "mod.py",
         "--excerpt", "target = True", "--category", "r", "--level", "warning"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    raw = artifact.read_bytes()
    assert json.loads(raw)["runs"][0].get("artifacts") == [{"location": {"uri": "mod.py"}}]
    manifest = {"scope": scope, "rules": ["r"], "blocking_levels": ["error"], "accepted": {}}
    summary = scan_results_from_sarif(raw, manifest, subject_root=tmp_path, require_review=True)
    assert summary["counts"]["failed"] == 0
    assert summary["non_passed"] == []
    assert summary["missing"] == missing
    forged = json.loads(raw)
    region = forged["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]
    region.update(startLine=99, endLine=99, snippet={"text": "absent excerpt"})
    with pytest.raises(ValueError, match="unresolvable"):
        scan_results_from_sarif(
            canonical_json_bytes(forged), manifest, subject_root=tmp_path, require_review=True,
        )
