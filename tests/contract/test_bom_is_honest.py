"""The first-thread bill of materials must describe observable reality.

The BOM is deliberately data rather than another plan.  A built part without a
passing gauge is only an assertion, and an unresolved dependency is not a
roadmap.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
BOM = REPO_ROOT / "governance" / "bom.yaml"

EXPECTED_IDS = tuple(f"FT-{number:02d}" for number in range(1, 16))
REQUIRED_FIELDS = frozenset({"id", "stage", "abb", "sbb", "gauge", "status", "depends_on"})
STAGES = frozenset({"specify", "freeze", "execute", "result"})
STATUSES = frozenset({"missing", "specified", "built", "calibrated"})
_CALIBRATION_RESULT = re.compile(r"(?:mutation|negative[_-]control)", re.IGNORECASE)


def _parts() -> list[dict[str, object]]:
    """Load the one top-level BOM list without supplying any defaults."""

    document = yaml.safe_load(BOM.read_text(encoding="utf-8"))
    assert isinstance(document, dict), "governance/bom.yaml must be a mapping"
    assert set(document) == {"parts"}, "the BOM has exactly one top-level 'parts' list"
    parts = document["parts"]
    assert isinstance(parts, list), "BOM 'parts' must be a list"
    return parts


def _gauge_file(gauge: str) -> Path:
    """Extract a test file from a pytest node id, if a calibrated row uses one."""

    return REPO_ROOT / gauge.split("::", 1)[0]


def test_bom_is_honest() -> None:
    """Enforce MAP CR-06 and the first thread's fixed, ordered scope."""

    parts = _parts()
    assert len(parts) == len(EXPECTED_IDS), "the BOM covers exactly the first thread's 15 parts"

    ids: list[str] = []
    dependencies: list[tuple[str, list[object]]] = []
    for position, part in enumerate(parts, start=1):
        assert isinstance(part, dict), f"row {position} must be a mapping"
        assert set(part) == REQUIRED_FIELDS, (
            f"row {position} must have exactly {sorted(REQUIRED_FIELDS)}, got {sorted(part)}"
        )

        part_id = part["id"]
        assert isinstance(part_id, str) and part_id, f"row {position} has no id"
        ids.append(part_id)

        assert part["stage"] in STAGES, f"{part_id}: unknown stage {part['stage']!r}"
        assert part["status"] in STATUSES, f"{part_id}: unknown status {part['status']!r}"
        assert isinstance(part["abb"], str) and part["abb"].strip(), f"{part_id}: ABB is required"
        assert part["sbb"] is None or isinstance(part["sbb"], str), f"{part_id}: SBB must be text or null"

        gauge = part["gauge"]
        status = part["status"]
        assert gauge is None or isinstance(gauge, str), f"{part_id}: gauge must be a path or null"
        assert gauge is not None or status not in {"built", "calibrated"}, (
            f"{part_id}: {status} requires a gauge; use null only for a non-built part"
        )
        if gauge is not None:
            assert gauge.startswith("tests/"), f"{part_id}: gauge must name a test path"
            assert _gauge_file(gauge).is_file(), f"{part_id}: gauge does not exist: {gauge}"
        if status == "built":
            assert gauge is not None, f"{part_id}: built parts name a passing test"
        if status == "calibrated":
            assert gauge is not None and _CALIBRATION_RESULT.search(gauge), (
                f"{part_id}: calibrated parts name a mutation or negative-control result"
            )

        depends_on = part["depends_on"]
        assert isinstance(depends_on, list), f"{part_id}: depends_on must be a list"
        dependencies.append((part_id, depends_on))

    assert tuple(ids) == EXPECTED_IDS, f"BOM ids and order must be {EXPECTED_IDS}"
    assert len(ids) == len(set(ids)), "BOM ids must be unique"
    known_ids = set(ids)
    for part_id, depends_on in dependencies:
        unknown = [dependency for dependency in depends_on if dependency not in known_ids]
        assert not unknown, f"{part_id}: unresolved dependencies: {unknown}"
