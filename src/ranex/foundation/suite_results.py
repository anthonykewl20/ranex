"""Canonical frozen-suite manifests and bounded junitxml summaries."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict, cast

from ranex.foundation.canonical import canonical_json_bytes

MAX_RESULTS_BYTES = 50 * 1024 * 1024

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_MANIFEST_KEYS = {"suite", "expected_skips"}
_RESULT_KEYS = {
    "manifest_digest",
    "counts",
    "non_passed",
    "missing",
    "extra_count",
    "outcome_digest",
}
_COUNT_KEYS = {
    "passed",
    "skipped",
    "failed",
    "errors",
    "xfailed",
    "xpassed",
}
_OUTCOME_KINDS = {"passed", "skipped", "failed", "error", "xfailed", "xpassed"}
_NON_PASSING_KINDS = _OUTCOME_KINDS - {"passed"}


class SuiteManifest(TypedDict):
    suite: list[str]
    expected_skips: dict[str, str]


def _is_non_negative_integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_manifest(value: object) -> SuiteManifest:
    if not isinstance(value, dict) or set(value) != _MANIFEST_KEYS:
        raise ValueError("suite manifest must contain exactly suite and expected_skips")

    suite = value["suite"]
    if not isinstance(suite, list) or any(
        not isinstance(test_id, str) or not test_id for test_id in suite
    ):
        raise ValueError("suite manifest suite must be a list of non-empty test IDs")
    if suite != sorted(suite) or len(suite) != len(set(suite)):
        raise ValueError("suite manifest test IDs must be sorted and unique")

    expected_skips = value["expected_skips"]
    if not isinstance(expected_skips, dict):
        raise ValueError("suite manifest expected_skips must be an object")
    suite_ids = set(suite)
    for test_id, reason in expected_skips.items():
        if not isinstance(test_id, str) or test_id not in suite_ids:
            raise ValueError("expected-skip IDs must name tests in suite")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("expected-skip reasons must be non-empty strings")
    return cast(SuiteManifest, value)


def validate_suite_results(value: object) -> dict[str, object]:
    """Return a canonical suite summary, or refuse its exact nested shape."""

    if not isinstance(value, dict) or set(value) != _RESULT_KEYS:
        raise ValueError(f"suite_results must contain exactly {sorted(_RESULT_KEYS)}")
    for field in ("manifest_digest", "outcome_digest"):
        digest = value[field]
        if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
            raise ValueError(f"suite_results {field} must be a canonical sha256 digest")

    counts = value["counts"]
    if not isinstance(counts, dict) or set(counts) != _COUNT_KEYS:
        raise ValueError(f"suite_results counts must contain exactly {sorted(_COUNT_KEYS)}")
    if any(not _is_non_negative_integer(count) for count in counts.values()):
        raise ValueError("suite_results counts must be non-negative integers")
    if not _is_non_negative_integer(value["extra_count"]):
        raise ValueError("suite_results extra_count must be a non-negative integer")

    raw_non_passed = value["non_passed"]
    if not isinstance(raw_non_passed, list):
        raise ValueError("suite_results non_passed must be a list")
    non_passed: list[list[str]] = []
    for item in raw_non_passed:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], str)
            or not item[0]
            or item[1] not in _NON_PASSING_KINDS
        ):
            raise ValueError("suite_results non_passed entries must be [test_id, outcome]")
        non_passed.append(item)
    if non_passed != sorted(non_passed) or len({item[0] for item in non_passed}) != len(
        non_passed
    ):
        raise ValueError("suite_results non_passed entries must be sorted and unique")

    missing = value["missing"]
    if not isinstance(missing, list) or any(
        not isinstance(test_id, str) or not test_id for test_id in missing
    ):
        raise ValueError("suite_results missing must be a list of non-empty test IDs")
    if missing != sorted(missing) or len(missing) != len(set(missing)):
        raise ValueError("suite_results missing IDs must be sorted and unique")
    return value


def _test_id(testcase: ET.Element) -> str:
    classname = testcase.get("classname")
    name = testcase.get("name")
    if not classname or not name:
        raise ValueError("junitxml testcase must carry classname and name")
    parts = classname.split(".")
    if "tests" in parts:
        parts = parts[parts.index("tests") :]
    return f"{'/'.join(parts)}.py::{name}"


def _outcome(testcase: ET.Element) -> str:
    outcome_children = [
        child for child in testcase if child.tag.rsplit("}", 1)[-1] in {"skipped", "failure", "error"}
    ]
    if len(outcome_children) > 1:
        raise ValueError("junitxml testcase carries multiple outcome children")
    if not outcome_children:
        return "passed"
    child = outcome_children[0]
    kind = child.tag.rsplit("}", 1)[-1]
    marker = f"{child.get('type', '')} {child.get('message', '')}".lower()
    if kind == "error":
        return "error"
    if kind == "failure":
        return "xpassed" if "xpass" in marker else "failed"
    if "xfail" in marker:
        return "xfailed"
    if "xpass" in marker:
        return "xpassed"
    return "skipped"


def _outcomes(junitxml_bytes: bytes) -> dict[str, str]:
    if not isinstance(junitxml_bytes, bytes):
        raise TypeError("junitxml_bytes must be bytes")
    try:
        xml_text = junitxml_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        # The byte-level declaration scan this replaces was bypassable with
        # UTF-16.  Pytest emits UTF-8; accepting another encoding would require
        # decoding it before we can safely decide whether a DTD is present.
        raise ValueError("junitxml must use UTF-8 encoding") from exc
    declaration = re.match(r"\ufeff?<\?xml\s+([^?]+)\?>", xml_text, re.IGNORECASE)
    if declaration is not None:
        encoding = re.search(
            r"\bencoding\s*=\s*(['\"])([^'\"]+)\1",
            declaration.group(1),
            re.IGNORECASE,
        )
        if encoding is not None and encoding.group(2).lower() not in {"utf-8", "utf8"}:
            raise ValueError("junitxml must declare UTF-8 encoding")
    if re.search(r"<!\s*(?:doctype|entity)\b", xml_text, re.IGNORECASE):
        raise ValueError("junitxml DTD and entity declarations are refused")
    try:
        root = ET.fromstring(junitxml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"cannot parse junitxml: {exc}") from exc

    outcomes: dict[str, str] = {}
    for testcase in root.iter():
        if testcase.tag.rsplit("}", 1)[-1] != "testcase":
            continue
        test_id = _test_id(testcase)
        if test_id in outcomes:
            raise ValueError(f"duplicate test ID in junitxml: {test_id}")
        outcomes[test_id] = _outcome(testcase)
    return dict(sorted(outcomes.items()))


def freeze_manifest(
    junitxml_bytes: bytes,
    *,
    expected_skips: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Freeze only the observed ID set; test outcomes never enter the manifest."""

    outcomes = _outcomes(junitxml_bytes)
    manifest: dict[str, object] = {
        "suite": sorted(outcomes),
        "expected_skips": {} if expected_skips is None else dict(expected_skips),
    }
    return cast(dict[str, object], _validate_manifest(manifest))


def load_manifest_bytes(raw: bytes) -> dict[str, object]:
    """Parse exact canonical JSON manifest bytes already selected by a caller."""

    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse suite manifest: {exc}") from exc
    manifest = _validate_manifest(value)
    if raw != canonical_json_bytes(manifest):
        raise ValueError("suite manifest must contain exact canonical JSON bytes")
    return cast(dict[str, object], manifest)


def load_manifest(path: str | Path) -> dict[str, object]:
    """Load only exact canonical JSON bytes with the frozen manifest shape."""

    return load_manifest_bytes(Path(path).read_bytes())


def manifest_digest(manifest: Mapping[str, object]) -> str:
    """Digest the exact canonical manifest representation."""

    validated = _validate_manifest(dict(manifest))
    return "sha256:" + hashlib.sha256(canonical_json_bytes(validated)).hexdigest()


def suite_results_from_junitxml(
    junitxml_bytes: bytes,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """Summarise one junitxml artifact against a previously frozen manifest."""

    validated_manifest = _validate_manifest(dict(manifest))
    outcomes = _outcomes(junitxml_bytes)
    expected_ids = set(validated_manifest["suite"])
    observed_ids = set(outcomes)
    counts = {
        "passed": sum(kind == "passed" for kind in outcomes.values()),
        "skipped": sum(kind == "skipped" for kind in outcomes.values()),
        "failed": sum(kind == "failed" for kind in outcomes.values()),
        "errors": sum(kind == "error" for kind in outcomes.values()),
        "xfailed": sum(kind == "xfailed" for kind in outcomes.values()),
        "xpassed": sum(kind == "xpassed" for kind in outcomes.values()),
    }
    result: dict[str, object] = {
        "manifest_digest": manifest_digest(validated_manifest),
        "counts": counts,
        "non_passed": [
            [test_id, kind]
            for test_id, kind in outcomes.items()
            if kind != "passed"
        ],
        "missing": sorted(expected_ids - observed_ids),
        "extra_count": len(observed_ids - expected_ids),
        "outcome_digest": "sha256:"
        + hashlib.sha256(canonical_json_bytes(outcomes)).hexdigest(),
    }
    return validate_suite_results(result)


def parse_results_artifact(
    path: str | Path,
    manifest: Mapping[str, object],
) -> dict[str, object]:
    """Read a present junitxml artifact no larger than 50 MiB and summarise it."""

    raw = read_results_artifact(path)
    return suite_results_from_junitxml(raw, manifest)


def read_results_artifact(path: str | Path) -> bytes:
    """Read one regular, non-symlink artifact through a single bounded fd."""

    artifact = Path(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    if nofollow:
        flags |= nofollow
    else:  # pragma: no cover - Linux supplies O_NOFOLLOW; safe fallback elsewhere
        try:
            if stat.S_ISLNK(os.lstat(artifact).st_mode):
                raise ValueError(f"results artifact must not be a symlink: {artifact}")
        except FileNotFoundError as exc:
            raise ValueError(f"results artifact is absent: {artifact}") from exc

    descriptor: int | None = None
    try:
        descriptor = os.open(artifact, flags)
    except FileNotFoundError as exc:
        raise ValueError(f"results artifact is absent: {artifact}") from exc
    except OSError as exc:
        raise ValueError(f"cannot open results artifact {artifact}: {exc}") from exc

    try:
        identity = os.fstat(descriptor)
        if not stat.S_ISREG(identity.st_mode):
            raise ValueError(f"results artifact is not a regular file: {artifact}")

        remaining = MAX_RESULTS_BYTES + 1
        chunks: list[bytes] = []
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) > MAX_RESULTS_BYTES:
            raise ValueError("results artifact exceeds the 50 MB limit")
        return raw
    except OSError as exc:
        raise ValueError(f"cannot read results artifact {artifact}: {exc}") from exc
    finally:
        os.close(descriptor)
