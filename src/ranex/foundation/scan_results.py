"""SARIF 2.1.0 scan artifacts reduced to the kernel's existing summary.

A deterministic scanner — ruff, semgrep, govulncheck, bandit — already speaks
an ecosystem format. Nothing here teaches the kernel a second vocabulary: a
SARIF run is reduced to exactly the summary `verdict.py` already decides on
(`manifest_digest`, `counts`, `non_passed`, `missing`, `extra_count`,
`outcome_digest`), so `evaluate()` is untouched and no model, tool or prose
enters the decision.

What a scan manifest freezes is the universe the claim is about:

  scope             the paths this claim covers. They are the IDs that pass or
                    fail, exactly as test IDs are for a suite manifest, because
                    a finding's own ID cannot be frozen before the finding
                    exists.
  rules             the reviewed rule universe. A finding outside it still
                    blocks — a violation is never waved through for being
                    unfamiliar — but nothing outside it can be *accepted*.
  blocking_levels   which SARIF levels decide. `error` alone, unless review
                    says otherwise.
  accepted          finding ID -> reason. The expected-skip of a scan: a known
                    finding that review has already answered for.

A finding ID is `<path>::<ruleId>::<fingerprint>` and the fingerprint is taken
over the ruleId, the path, the region's line bounds and **the subject's own
bytes at that region** — never over the scanner's message, which is free text a
producer may reword between runs and which would make an ID unstable exactly
when it mattered. Binding the fingerprint to the materialised subject is also
what makes acceptance safe: an accepted ID stops applying the moment the code
under it changes.

Region validation is the F-012 answer in this family. A scanner is a report
producer, and a report producer that can name a line it never read can also
name a clean line. So every reported region is checked against the materialised
subject at run time: a region past the end of the file, or a snippet the file
does not carry there, makes the artifact malformed — refused, and absence
blocks. Nothing is relocated and nothing is guessed.

The coverage boundary, recorded rather than papered over: SARIF's own coverage
witnesses are `runs[].artifacts[]` and `runs[].invocations[]`, and a producer
may emit neither — ruff 0.16.2 emits neither. When a witness is present it is
enforced; when it is absent, a scope path is proved only to *exist* in the
subject, and "the scanner exited 0 having read nothing" is caught by the run's
exit code and by nothing else in the artifact. That residual is a GAP in the
#95 vocabulary, not a pass.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any, TypedDict, cast
from urllib.parse import unquote, urlparse

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.suite_results import validate_suite_results

SCAN_REPORTERS = frozenset({"sarif-2.1.0"})

#: SARIF 2.1.0 §3.27.10. `none` is a level a result may carry; it decides
#: nothing unless a manifest says it does.
SARIF_LEVELS = frozenset({"error", "warning", "note", "none"})

_SCAN_MANIFEST_KEYS = {"scope", "rules", "blocking_levels", "accepted"}
_FINDING_ID = re.compile(r"^(?P<path>[^\n]+?)::(?P<rule>[^:\n]+)::(?P<fingerprint>[0-9a-f]{64})$")
_SARIF_VERSION = "2.1.0"


class ScanManifest(TypedDict):
    scope: list[str]
    rules: list[str]
    blocking_levels: list[str]
    accepted: dict[str, str]


def _is_confined_relative(candidate: object) -> bool:
    """A scope path names something inside the subject, and only that."""

    if not isinstance(candidate, str) or not candidate or candidate != candidate.strip():
        return False
    path = Path(candidate)
    return not path.is_absolute() and not any(part in {"..", ""} for part in path.parts)


def validate_scan_manifest(value: object) -> ScanManifest:
    """Return a canonical scan manifest, or refuse its exact nested shape."""

    if not isinstance(value, dict) or set(value) != _SCAN_MANIFEST_KEYS:
        raise ValueError(f"scan manifest must contain exactly {sorted(_SCAN_MANIFEST_KEYS)}")

    scope = value["scope"]
    if not isinstance(scope, list) or not scope or any(
        not _is_confined_relative(path) for path in scope
    ):
        raise ValueError(
            "scan manifest scope must be a non-empty list of relative paths confined "
            "below the subject; an empty scope is a claim about nothing"
        )
    if scope != sorted(scope) or len(scope) != len(set(scope)):
        raise ValueError("scan manifest scope paths must be sorted and unique")

    rules = value["rules"]
    if not isinstance(rules, list) or any(
        not isinstance(rule, str) or not rule or rule != rule.strip() for rule in rules
    ):
        raise ValueError("scan manifest rules must be a list of non-empty rule IDs")
    if rules != sorted(rules) or len(rules) != len(set(rules)):
        raise ValueError("scan manifest rule IDs must be sorted and unique")

    levels = value["blocking_levels"]
    if not isinstance(levels, list) or not levels or any(
        level not in SARIF_LEVELS for level in levels
    ):
        raise ValueError(
            f"scan manifest blocking_levels must be a non-empty subset of {sorted(SARIF_LEVELS)}; "
            "a manifest that blocks on no level is a gate that cannot block"
        )
    if levels != sorted(levels) or len(levels) != len(set(levels)):
        raise ValueError("scan manifest blocking_levels must be sorted and unique")

    accepted = value["accepted"]
    if not isinstance(accepted, dict):
        raise ValueError("scan manifest accepted must be an object")
    scope_paths, rule_ids = set(scope), set(rules)
    for finding, reason in accepted.items():
        parsed = _FINDING_ID.fullmatch(finding) if isinstance(finding, str) else None
        if parsed is None:
            raise ValueError(
                f"accepted ID {finding!r} must be <path>::<ruleId>::<64-hex fingerprint>"
            )
        if parsed.group("path") not in scope_paths:
            raise ValueError(f"accepted ID {finding!r} names a path outside the frozen scope")
        if parsed.group("rule") not in rule_ids:
            raise ValueError(
                f"accepted ID {finding!r} names a rule outside the reviewed rule universe; "
                "a finding may block under an unreviewed rule but may never be accepted under one"
            )
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError("accepted reasons must be non-empty strings")
    return cast(ScanManifest, value)


def load_scan_manifest_bytes(raw: bytes) -> dict[str, object]:
    """Parse exact canonical JSON scan-manifest bytes already selected by a caller."""

    try:
        value: Any = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot parse scan manifest: {exc}") from exc
    manifest = validate_scan_manifest(value)
    if raw != canonical_json_bytes(manifest):
        raise ValueError("scan manifest must contain exact canonical JSON bytes")
    return cast(dict[str, object], manifest)


def scan_manifest_digest(manifest: Mapping[str, object]) -> str:
    """Digest the exact canonical scan-manifest representation."""

    validated = validate_scan_manifest(dict(manifest))
    return "sha256:" + hashlib.sha256(canonical_json_bytes(validated)).hexdigest()


def scan_expected_ids(manifest: Mapping[str, object]) -> tuple[str, ...]:
    """The frozen ID universe: every scope path, plus every accepted finding."""

    validated = validate_scan_manifest(dict(manifest))
    return tuple(sorted({*validated["scope"], *validated["accepted"]}))


def scan_expected_skips(manifest: Mapping[str, object]) -> dict[str, str]:
    """Accepted findings are a scan's expected skips, reason and all."""

    return dict(validate_scan_manifest(dict(manifest))["accepted"])


def fingerprint(rule_id: str, path: str, start_line: int, end_line: int, region: bytes) -> str:
    """Stable over reruns, bound to the subject's bytes, blind to prose."""

    material = canonical_json_bytes([rule_id, path, start_line, end_line])
    return hashlib.sha256(material + b"\n" + region).hexdigest()


def finding_id(rule_id: str, path: str, start_line: int, end_line: int, region: bytes) -> str:
    return f"{path}::{rule_id}::{fingerprint(rule_id, path, start_line, end_line, region)}"


def _driver_levels(run: Mapping[str, Any]) -> dict[str, str]:
    """`ruleId -> defaultConfiguration.level`, for results that omit a level."""

    driver = run.get("tool", {}).get("driver", {}) if isinstance(run.get("tool"), dict) else {}
    levels: dict[str, str] = {}
    for rule in driver.get("rules", []) if isinstance(driver.get("rules"), list) else []:
        if not isinstance(rule, dict):
            continue
        rule_id = rule.get("id")
        configuration = rule.get("defaultConfiguration")
        level = configuration.get("level") if isinstance(configuration, dict) else None
        if isinstance(rule_id, str) and isinstance(level, str) and level in SARIF_LEVELS:
            levels[rule_id] = level
    return levels


def _subject_relative(uri: object, subject_root: Path) -> str:
    """The path a location names, as a subject-relative path, or a refusal.

    A finding outside the materialised subject is not a finding about this
    subject. It is refused rather than dropped: silently ignoring locations is
    how a scanner's report and a verdict come to disagree about what was judged.
    """

    if not isinstance(uri, str) or not uri:
        raise ValueError("SARIF location carries no artifactLocation uri")
    parsed = urlparse(uri)
    if parsed.scheme and parsed.scheme != "file":
        raise ValueError(f"SARIF artifactLocation uri must be a file path or file: URI: {uri!r}")
    raw = unquote(parsed.path) if parsed.scheme == "file" else uri
    candidate = Path(raw)
    if candidate.is_absolute():
        try:
            relative = candidate.resolve().relative_to(subject_root.resolve())
        except ValueError as exc:
            raise ValueError(
                f"SARIF result names {uri!r}, which is outside the materialised subject"
            ) from exc
    else:
        relative = Path(raw)
        if any(part == ".." for part in relative.parts):
            raise ValueError(f"SARIF result names an escaping path: {uri!r}")
    return relative.as_posix()


def _region_bytes(
    subject_root: Path, path: str, start_line: int, end_line: int, snippet: object
) -> bytes:
    """The subject's own bytes at a reported region — or the artifact is malformed.

    This is the check that keeps a report producer honest about where it looked.
    A region past the end of the file, or a snippet the file does not carry
    there, is a claim about a line that was never read.
    """

    subject_file = subject_root / path
    try:
        raw = subject_file.read_bytes()
    except OSError as exc:
        raise ValueError(
            f"SARIF result names {path!r}, which the materialised subject does not carry"
        ) from exc
    lines = raw.splitlines(keepends=True)
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        raise ValueError(
            f"SARIF region {start_line}-{end_line} lies outside {path!r} "
            f"({len(lines)} lines); no relocation is attempted"
        )
    region = b"".join(lines[start_line - 1 : end_line])
    if snippet is not None:
        if not isinstance(snippet, str):
            raise ValueError(f"SARIF region snippet for {path!r} must be text")
        observed = region.decode("utf-8", errors="replace").rstrip("\n")
        if snippet.rstrip("\n") != observed:
            raise ValueError(
                f"SARIF region snippet for {path!r} lines {start_line}-{end_line} does "
                "not match the subject at that region"
            )
    return region


def _findings(
    sarif: Mapping[str, Any], subject_root: Path
) -> tuple[list[tuple[str, str, str]], set[str]]:
    """Every result as `(finding_id, path, level)`, plus the witnessed paths."""

    if sarif.get("version") != _SARIF_VERSION:
        raise ValueError(f"SARIF artifact must declare version {_SARIF_VERSION}")
    runs = sarif.get("runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("SARIF artifact carries no runs")

    findings: list[tuple[str, str, str]] = []
    witnessed: set[str] = set()
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("SARIF runs entries must be objects")
        invocations = run.get("invocations")
        if invocations is not None:
            if not isinstance(invocations, list) or not invocations:
                raise ValueError("SARIF invocations must be a non-empty list when present")
            for invocation in invocations:
                if not isinstance(invocation, dict) or invocation.get(
                    "executionSuccessful"
                ) is not True:
                    # The silent-crash trap: a scanner that reports its own
                    # failure and still exits 0 must never read as clean.
                    raise ValueError(
                        "SARIF invocation did not report executionSuccessful; a scan that "
                        "declares its own failure is refused, and absence blocks"
                    )
        for artifact in run.get("artifacts", []) if isinstance(run.get("artifacts"), list) else []:
            location = artifact.get("location") if isinstance(artifact, dict) else None
            if isinstance(location, dict):
                witnessed.add(_subject_relative(location.get("uri"), subject_root))

        levels = _driver_levels(run)
        results = run.get("results", [])
        if not isinstance(results, list):
            raise ValueError("SARIF runs[].results must be a list when present")
        for result in results:
            if not isinstance(result, dict):
                raise ValueError("SARIF results entries must be objects")
            rule_id = result.get("ruleId")
            if not isinstance(rule_id, str) or not rule_id:
                raise ValueError("SARIF result carries no ruleId")
            level = result.get("level", levels.get(rule_id, "warning"))
            if level not in SARIF_LEVELS:
                raise ValueError(f"SARIF result carries an unknown level: {level!r}")
            locations = result.get("locations")
            if not isinstance(locations, list) or len(locations) != 1:
                raise ValueError(
                    "SARIF result must carry exactly one location; a finding with none "
                    "cannot be bound to the subject and one with several is ambiguous"
                )
            physical = locations[0].get("physicalLocation") if isinstance(locations[0], dict) else None
            if not isinstance(physical, dict):
                raise ValueError("SARIF result location carries no physicalLocation")
            artifact_location = physical.get("artifactLocation")
            path = _subject_relative(
                artifact_location.get("uri") if isinstance(artifact_location, dict) else None,
                subject_root,
            )
            region = physical.get("region")
            if not isinstance(region, dict):
                raise ValueError(f"SARIF result for {path!r} carries no region")
            start_line = region.get("startLine")
            end_line = region.get("endLine", start_line)
            if not isinstance(start_line, int) or isinstance(start_line, bool):
                raise ValueError(f"SARIF region for {path!r} carries no integer startLine")
            if not isinstance(end_line, int) or isinstance(end_line, bool):
                raise ValueError(f"SARIF region for {path!r} carries a non-integer endLine")
            snippet = region.get("snippet", {}).get("text") if isinstance(
                region.get("snippet"), dict
            ) else None
            material = _region_bytes(subject_root, path, start_line, end_line, snippet)
            findings.append(
                (finding_id(rule_id, path, start_line, end_line, material), path, level)
            )
    return findings, witnessed


def scan_results_from_sarif(
    sarif_bytes: bytes,
    manifest: Mapping[str, object],
    *,
    subject_root: Path,
) -> dict[str, object]:
    """Summarise one SARIF artifact against a previously frozen scan manifest.

    The reduction is deliberately the same summary a suite produces, because the
    kernel already knows how to decide on that and learning a second shape is
    how a second decision procedure gets written.

    Scope paths are the IDs that pass and fail: a blocking finding fails the
    path that carries it, which is an ID the manifest froze, so `evaluate()`
    blocks on it without being taught anything. The finding's own ID is
    recorded beside it — signed, retained, and named by the publisher — but it
    is not what the kernel counts, because an ID nobody could have frozen
    cannot be what a frozen universe is compared against.
    """

    validated = validate_scan_manifest(dict(manifest))
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

    findings, witnessed = _findings(document, subject_root)
    scope = list(validated["scope"])
    accepted = dict(validated["accepted"])
    blocking = set(validated["blocking_levels"])

    outcomes: dict[str, str] = {path: "passed" for path in scope}
    for identifier, path, level in findings:
        if level not in blocking:
            continue
        if identifier in accepted:
            outcomes[identifier] = "skipped"
            continue
        outcomes[identifier] = "failed"
        if path in outcomes:
            outcomes[path] = "failed"

    subject = subject_root.resolve()
    missing = sorted(
        path
        for path in scope
        if not (subject / path).is_file() or (witnessed and path not in witnessed)
    )
    expected = set(scan_expected_ids(validated))
    observed = set(outcomes)
    counts = {
        "passed": sum(kind == "passed" for kind in outcomes.values()),
        "skipped": sum(kind == "skipped" for kind in outcomes.values()),
        "failed": sum(kind == "failed" for kind in outcomes.values()),
        "errors": 0,
        "xfailed": 0,
        "xpassed": 0,
    }
    ordered = dict(sorted(outcomes.items()))
    result: dict[str, object] = {
        "manifest_digest": scan_manifest_digest(validated),
        "counts": counts,
        "non_passed": [
            [identifier, kind] for identifier, kind in ordered.items() if kind != "passed"
        ],
        "missing": missing,
        "extra_count": len(observed - expected),
        "outcome_digest": "sha256:" + hashlib.sha256(canonical_json_bytes(ordered)).hexdigest(),
    }
    return validate_suite_results(result)


def parse_scan_artifact(
    path: str | Path,
    manifest: Mapping[str, object],
    *,
    subject_root: Path,
) -> dict[str, object]:
    """Read a present SARIF artifact no larger than 50 MiB and summarise it."""

    from ranex.foundation.suite_results import read_results_artifact

    return scan_results_from_sarif(
        read_results_artifact(path), manifest, subject_root=subject_root
    )


def claim_expectations(
    raw: bytes, reporter: str
) -> tuple[str, tuple[str, ...], dict[str, str]]:
    """One claim's frozen universe: `(manifest_digest, expected_ids, expected_skips)`.

    Both manifest kinds answer the same three questions, and the kernel asks
    only those three. Resolving the reporter here keeps every Gate-construction
    site — the composition root, `task judge`, the receiver — asking one
    question instead of each learning both shapes and drifting apart.
    """

    if reporter in SCAN_REPORTERS:
        manifest = validate_scan_manifest(load_scan_manifest_bytes(raw))
        return (
            scan_manifest_digest(manifest),
            scan_expected_ids(manifest),
            scan_expected_skips(manifest),
        )
    from ranex.foundation.suite_results import load_manifest_bytes, manifest_digest

    suite = load_manifest_bytes(raw)
    return (
        manifest_digest(suite),
        tuple(cast(list[str], suite["suite"])),
        dict(cast(dict[str, str], suite["expected_skips"])),
    )


def observed_findings(
    sarif_bytes: bytes, subject_root: Path
) -> tuple[tuple[str, str, str], ...]:
    """Every finding a run reported, as `(finding_id, path, level)`.

    The freeze needs the IDs a real run produced for the same reason
    `--expected-skip` must name tests the suite carries: a declaration about a
    finding nobody observed is a declaration about nothing, and it would sit in
    the trust root looking like review had happened.
    """

    try:
        document = json.loads(sarif_bytes.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ValueError("SARIF artifact must use UTF-8 encoding") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"cannot parse SARIF artifact: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("SARIF artifact must be a JSON object")
    findings, _ = _findings(document, subject_root)
    return tuple(findings)


def freeze_scan_manifest(
    findings: tuple[tuple[str, str, str], ...],
    *,
    scope: list[str],
    rules: list[str],
    blocking_levels: list[str],
    accepted: dict[str, str],
) -> dict[str, object]:
    """Freeze the declared universe, checked against what the run really saw."""

    observed = {identifier for identifier, _, _ in findings}
    unknown = sorted(set(accepted) - observed)
    if unknown:
        raise ValueError(
            "accepted IDs must name findings the frozen run observed: "
            + ", ".join(unknown)
        )
    manifest = {
        "scope": sorted(set(scope)),
        "rules": sorted(set(rules)),
        "blocking_levels": sorted(set(blocking_levels)),
        "accepted": dict(sorted(accepted.items())),
    }
    return cast(dict[str, object], validate_scan_manifest(manifest))
