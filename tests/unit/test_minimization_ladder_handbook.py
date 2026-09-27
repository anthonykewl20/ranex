"""#112 — adapted minimization ladder in governance/handbook.json.

Pytest discovers this module. Exercises parse_handbook_bytes / resolve_handbook
over governance/handbook.json. User: Ship #112 minimization ladder handbook.
"""

from __future__ import annotations

import json
from pathlib import Path

from ranex.policy.handbook import SYSTEM_LAYER, parse_handbook_bytes, resolve_handbook

REPO = Path(__file__).resolve().parents[2]


def test_handbook_json_parses_as_system_layer() -> None:
    raw = (REPO / "governance" / "handbook.json").read_bytes()
    entries = parse_handbook_bytes(SYSTEM_LAYER, raw)
    assert len(entries) == 1
    assert entries[0].path_glob == "**/*"


def test_ladder_amendments_are_present() -> None:
    text = json.loads((REPO / "governance" / "handbook.json").read_text())["entries"][0][
        "text"
    ]
    assert "already-approved" in text
    assert "deps fetch" in text
    assert "red first" in text
    assert "suite manifest" in text
    assert 'No "ask the user"' in text
    assert "lite/full/off" in text
    assert "trust boundaries" in text


def test_ladder_resolution_is_stable() -> None:
    raw = (REPO / "governance" / "handbook.json").read_bytes()
    entries = parse_handbook_bytes(SYSTEM_LAYER, raw)
    paths = ("backend/app/main.py", "frontend/src/main.tsx", "README.md")
    a = resolve_handbook(entries, (), paths, {})
    b = resolve_handbook(entries, (), paths, {})
    assert a.digest == b.digest
    assert a.digest != resolve_handbook((), (), paths, {}).digest
