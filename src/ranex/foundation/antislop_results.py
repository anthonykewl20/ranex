"""Frozen antislop expectations and the reduction that judges the census.

The scan family freezes a universe of paths and accepts findings; the
antislop family freezes a universe of *tests with their effective-assert
counts*, because the slop it exists for — one assertion quietly deleted —
is invisible in any file-level shape. The reduction here stays inside the
closed suite-summary verdicts already decide on, so `evaluate()`, the
envelope and `verdict.py` learn nothing (ADR-060 seam B), and the
expectations file is a trust root read from the governing commit exactly
like a scan manifest (seam C): the subject tree can carry its own weakened
copy and no reader will open it.

What the frozen universe means:

  scope    the test files the claim covers — existence- and witness-guarded
           IDs, exactly as a scan manifest's scope paths are.
  tests    `<file>::[<class>::]<test>` -> the effective assert count the
           approved tree carried. There is no `accepted` map: unlike a scan
           finding, a slop shape or a count shortfall is never something
           review waves through, so the vocabulary has no word for it.

Judgement rules, all deterministic:

  * a census count below the frozen count fails that test — doing less than
    the approved tree promised is the finding;
  * a frozen test absent from the census, or a scope file the artifact never
    witnessed, is `missing` — and absence blocks, which is what makes an
    empty artifact a full miss rather than a clean pass;
  * every structural error finding fails its finding ID, the file that
    carries it and the test it names, whether or not that test was frozen —
    slop does not become legal by being new;
  * a census entry no freeze names is counted `extra`, never blocked: added
    tests are the suite's business, not the census's.

The census counts live in SARIF message text, which the #97 fingerprint
deliberately does not bind — a producer that forges counts has forged the
artifact itself, the same standing boundary every producer-signed results
file carries (F-012). What a producer cannot do is quietly drop a test from
observation: the freeze names every test, and absence blocks.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TypedDict, cast

from ranex.foundation.antislop import RULE_CENSUS
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import (
    _SARIF_VERSION,
    SARIF_LEVELS,
    _region_bytes,
    _subject_relative,
    fingerprint,
)
from ranex.foundation.suite_results import validate_suite_results

ANTISLOP_REPORTERS = frozenset({"antislop-sarif-2.1.0"})

_EXPECTATION_KEYS = {"scope", "tests"}
_CENSUS_MESSAGE = re.compile(r"^(?P<test_id>.+) effective_asserts=(?P<count>\d+)$")
_TEST_ID = re.compile(
    r"^(?P<path>[^\s:]+)::(?P<name>[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)*)$"
)


class AntislopExpectations(TypedDict):
    scope: list[str]
    tests: dict[str, int]


def _is_confined_relative(candidate: object) -> bool:
    if not isinstance(candidate, str) or not candidate or candidate != candidate.strip():
        return False
    path = Path(candidate)
    return not path.is_absolute() and not any(
        part in {"..", ""} for part in path.parts
    )


def validate_antislop_expectations(value: object) -> AntislopExpectations:
    """Return a canonical expectations manifest, or refuse its exact shape."""

    if not isinstance(value, dict) or set(value) != _EXPECTATION_KEYS:
        raise ValueError(
            f"antislop expectations must contain exactly {sorted(_EXPECTATION_KEYS)}"
        )

    scope = value["scope"]
    if not isinstance(scope, list) or not scope or any(
        not _is_confined_relative(path) for path in scope
    ):
        raise ValueError(
            "antislop expectations scope must be a non-empty list of relative "
            "paths confined below the subject; an empty scope is a claim about nothing"
        )
    if scope != sorted(scope) or len(scope) != len(set(scope)):
        raise ValueError("antislop expectations scope paths must be sorted and unique")

    tests = value["tests"]
    if not isinstance(tests, dict) or not tests:
        raise ValueError("antislop expectations tests must be a non-empty object")
    scope_paths = set(scope)
    for test_id, count in tests.items():
        if (
            not isinstance(test_id, str)
            or _TEST_ID.fullmatch(test_id) is None
            or test_id.split("::")[0] not in scope_paths
        ):
            raise ValueError(
                f"antislop expectations test ID {test_id!r} must be "
                "<file>::[<class>::]<test> naming a file inside the frozen scope"
            )
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError(
                f"antislop expectations count for {test_id!r} must be a "
                "non-negative integer"
            )
    if list(tests) != sorted(tests):
        raise ValueError("antislop expectations test IDs must be sorted")
    return cast(AntislopExpectations, value)


def load_antislop_expectations_bytes(raw: bytes) -> dict[str, object]:
    """Parse exact canonical JSON expectations bytes already selected."""

    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse antislop expectations: {exc}") from exc
    manifest = validate_antislop_expectations(value)
    if raw != canonical_json_bytes(manifest):
        raise ValueError("antislop expectations must contain exact canonical JSON bytes")
    return cast(dict[str, object], manifest)


def antislop_expectations_digest(manifest: Mapping[str, object]) -> str:
    """Digest the exact canonical expectations representation."""

    validated = validate_antislop_expectations(dict(manifest))
    return "sha256:" + hashlib.sha256(canonical_json_bytes(validated)).hexdigest()


def antislop_expected_ids(manifest: Mapping[str, object]) -> tuple[str, ...]:
    """The frozen ID universe: every scope file, plus every frozen test."""

    validated = validate_antislop_expectations(dict(manifest))
    return tuple(sorted({*validated["scope"], *validated["tests"]}))


def antislop_expected_skips(manifest: Mapping[str, object]) -> dict[str, str]:
    """No acceptance vocabulary exists in this family, by decision."""

    validate_antislop_expectations(dict(manifest))
    return {}


def _parse(
    sarif_bytes: bytes, subject_root: Path
) -> tuple[dict[str, int], list[tuple[str, str, str]], set[str]]:
    """`(census, findings, witnessed)` from one artifact, region-validated.

    The two region helpers are `scan_results`' own: one implementation of
    "a reported line is a line the subject really carries", shared with the
    scan family rather than forked.
    """

    if not isinstance(sarif_bytes, bytes):
        raise TypeError("sarif_bytes must be bytes")
    try:
        document = json.loads(sarif_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("SARIF artifact must use UTF-8 encoding") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse SARIF artifact: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("SARIF artifact must be a JSON object")
    if document.get("version") != _SARIF_VERSION:
        raise ValueError(f"SARIF artifact must declare version {_SARIF_VERSION}")
    runs = document.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF artifact carries no runs")

    census: dict[str, int] = {}
    findings: list[tuple[str, str, str]] = []
    witnessed: set[str] = set()
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("SARIF runs entries must be objects")
        invocations = run.get("invocations")
        if invocations is not None:
            if not isinstance(invocations, list) or not invocations:
                raise ValueError(
                    "SARIF invocations must be a non-empty list when present"
                )
            for invocation in invocations:
                if (
                    not isinstance(invocation, dict)
                    or invocation.get("executionSuccessful") is not True
                ):
                    raise ValueError(
                        "SARIF invocation did not report executionSuccessful; a scan "
                        "that declares its own failure is refused, and absence blocks"
                    )
        for artifact in run.get("artifacts", []) if isinstance(
            run.get("artifacts"), list
        ) else []:
            location = artifact.get("location") if isinstance(artifact, dict) else None
            if isinstance(location, dict):
                witnessed.add(_subject_relative(location.get("uri"), subject_root))

        results = run.get("results", [])
        if not isinstance(results, list):
            raise ValueError("SARIF runs[].results must be a list when present")
        for entry in results:
            if not isinstance(entry, dict):
                raise ValueError("SARIF results entries must be objects")
            rule_id = entry.get("ruleId")
            if not isinstance(rule_id, str) or not rule_id:
                raise ValueError("SARIF result carries no ruleId")
            level = entry.get("level")
            if level not in SARIF_LEVELS:
                raise ValueError(f"SARIF result carries an unknown level: {level!r}")
            message = entry.get("message")
            text = message.get("text") if isinstance(message, dict) else None
            if not isinstance(text, str) or not text:
                raise ValueError("SARIF result carries no message text")
            locations = entry.get("locations")
            if not isinstance(locations, list) or len(locations) != 1:
                raise ValueError(
                    "SARIF result must carry exactly one location; a finding with "
                    "none cannot be bound to the subject and one with several is "
                    "ambiguous"
                )
            physical = (
                locations[0].get("physicalLocation")
                if isinstance(locations[0], dict)
                else None
            )
            if not isinstance(physical, dict):
                raise ValueError("SARIF result location carries no physicalLocation")
            artifact_location = physical.get("artifactLocation")
            path = _subject_relative(
                artifact_location.get("uri")
                if isinstance(artifact_location, dict)
                else None,
                subject_root,
            )
            region = physical.get("region")
            if not isinstance(region, dict):
                raise ValueError(f"SARIF result for {path!r} carries no region")
            start_line = region.get("startLine")
            end_line = region.get("endLine", start_line)
            if not isinstance(start_line, int) or isinstance(start_line, bool):
                raise ValueError(
                    f"SARIF region for {path!r} carries no integer startLine"
                )
            if not isinstance(end_line, int) or isinstance(end_line, bool):
                raise ValueError(f"SARIF region for {path!r} carries a non-integer endLine")
            snippet = (
                region.get("snippet", {}).get("text")
                if isinstance(region.get("snippet"), dict)
                else None
            )
            material = _region_bytes(subject_root, path, start_line, end_line, snippet)
            identifier = fingerprint(rule_id, path, start_line, end_line, material)
            if rule_id == RULE_CENSUS:
                if level != "none":
                    raise ValueError(
                        "a census entry is an observation and never decides; its "
                        "level must be 'none'"
                    )
                parsed = _CENSUS_MESSAGE.fullmatch(text)
                if parsed is None:
                    raise ValueError(
                        "a census entry must read '<test_id> effective_asserts=<n>'; "
                        f"got {text!r}"
                    )
                if parsed.group("test_id") in census:
                    raise ValueError(
                        f"duplicate census entry for {parsed.group('test_id')!r}"
                    )
                census[parsed.group("test_id")] = int(parsed.group("count"))
            else:
                findings.append((f"{path}::{rule_id}::{identifier}", path, text))
    return census, findings, witnessed


def antislop_results_from_sarif(
    sarif_bytes: bytes,
    manifest: Mapping[str, object],
    *,
    subject_root: Path,
) -> dict[str, object]:
    """Summarise one antislop artifact against frozen expectations.

    The same summary a suite or a scan produces, over two ID families: the
    frozen scope files and the frozen tests, plus the finding IDs any
    structural error contributes. `evaluate()` blocks on `non_passed` and
    `missing` without being taught anything new.
    """

    validated = validate_antislop_expectations(dict(manifest))
    census, findings, witnessed = _parse(sarif_bytes, subject_root)
    scope = list(validated["scope"])
    frozen_tests = dict(validated["tests"])

    outcomes: dict[str, str] = {path: "passed" for path in scope}
    for test_id, frozen_count in frozen_tests.items():
        observed = census.get(test_id)
        if observed is not None and observed < frozen_count:
            outcomes[test_id] = "failed"
    for identifier, path, named in findings:
        outcomes[identifier] = "failed"
        # The named test failed regardless of its census count — `assert True`
        # counts as an assertion, so only the structural rule sees it.
        outcomes[named] = "failed"
        if path in outcomes:
            outcomes[path] = "failed"

    subject = subject_root.resolve()
    missing = sorted(
        path
        for path in scope
        if not (subject / path).is_file() or (witnessed and path not in witnessed)
    ) + sorted(test_id for test_id in frozen_tests if test_id not in census)
    expected = set(antislop_expected_ids(validated))
    observed_universe = set(census) | {identifier for identifier, _, _ in findings}
    counts = {
        "passed": sum(kind == "passed" for kind in outcomes.values()),
        "skipped": 0,
        "failed": sum(kind == "failed" for kind in outcomes.values()),
        "errors": 0,
        "xfailed": 0,
        "xpassed": 0,
    }
    ordered = dict(sorted(outcomes.items()))
    result: dict[str, object] = {
        "manifest_digest": antislop_expectations_digest(validated),
        "counts": counts,
        "non_passed": [
            [identifier, kind]
            for identifier, kind in ordered.items()
            if kind != "passed"
        ],
        "missing": missing,
        "extra_count": len(observed_universe - expected),
        "outcome_digest": "sha256:"
        + hashlib.sha256(canonical_json_bytes(ordered)).hexdigest(),
    }
    return validate_suite_results(result)


def freeze_antislop_expectations_observed(
    census: Mapping[str, int],
    findings: Sequence[tuple[str, str, str]],
    witnessed: set[str],
) -> dict[str, object]:
    """Freeze what a real run of the approved tree observed, already parsed.

    The universe is exactly what the run witnessed — every test file, every
    test, no narrowing flags — because a freeze that could declare less than
    the tree carries would be the narrowing slop this claim exists to catch.
    A tree that already carries structural violations is refused rather than
    frozen-around: expectations recorded over slop are expectations for it.
    """

    violations = sorted(identifier for identifier, _path, _named in findings)
    if violations:
        raise ValueError(
            "refusing to freeze antislop expectations around a tree that "
            "already carries antislop violations: " + ", ".join(violations)
        )
    manifest = {
        "scope": sorted(witnessed),
        "tests": dict(sorted(dict(census).items())),
    }
    return cast(dict[str, object], validate_antislop_expectations(manifest))


def freeze_antislop_expectations(
    sarif_bytes: bytes, *, subject_root: Path
) -> dict[str, object]:
    """Freeze the census a real artifact of the approved tree carries."""

    census, findings, witnessed = _parse(sarif_bytes, subject_root)
    return freeze_antislop_expectations_observed(census, findings, witnessed)


def parse_antislop_artifact(
    path: str | Path,
    manifest: Mapping[str, object],
    *,
    subject_root: Path,
) -> dict[str, object]:
    """Read a present antislop artifact no larger than 50 MiB and summarise."""

    from ranex.foundation.suite_results import read_results_artifact

    return antislop_results_from_sarif(
        read_results_artifact(path), manifest, subject_root=subject_root
    )
