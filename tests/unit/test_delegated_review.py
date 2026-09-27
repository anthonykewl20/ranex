"""#102 — delegated-review packet, anchors, prose-free fingerprints.

Callers: pytest discovery under tests/unit/. Exercises
ranex.foundation.delegated_review and scan_results packet admission.
No production data; synthetic digests and tmp_path trees only.
"""

from __future__ import annotations

import hashlib
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
from ranex.foundation.scan_results import scan_results_from_sarif

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
