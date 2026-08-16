"""Pure, fail-closed trace-reference parsing and candidate-tree coverage."""

from __future__ import annotations

import difflib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from ranex.foundation.canonical import canonical_json_bytes

E_TRACE_GRAMMAR = "E-TRACE-001"
E_TRACE_STALE = "E-TRACE-002"
E_TRACE_AUTHORITY = "E-TRACE-003"
E_TRACE_UNKNOWN = "E-TRACE-004"
E_TRACE_DUPLICATE = "E-TRACE-005"
E_TRACE_UNCOVERED = "E-TRACE-006"
E_TRACE_CROSS_TASK = "E-TRACE-007"
E_TRACE_AMBIGUOUS = "E-TRACE-008"
E_TRACE_WILDCARD = "E-TRACE-009"
E_TRACE_INVENTED = "E-TRACE-010"
E_TRACE_EXEMPTION_WILDCARD = "E-TRACE-011"
E_TRACE_REASONLESS = "E-TRACE-012"
E_TRACE_SIDECAR = "E-TRACE-013"
E_TRACE_EXEMPTION = "E-TRACE-014"
E_TRACE_PROTECTED = "E-TRACE-015"
E_TRACE_OUTCOME = "E-TRACE-016"

_COMMENT = re.compile(
    r"(?:#|//) ranex-trace: rule=([^\s]+) transition=([^\s]+) "
    r"outcome=([^\s]+) projection=(sha256:[0-9a-f]{64})\Z"
)
_SYMBOL = re.compile(r"^\s*(?:def|class|function)\s+([A-Za-z_$][\w$]*)")
_SOURCE_SUFFIXES = {".py", ".ts"}


class TraceVerificationError(ValueError):
    """A stable, typed refusal from the independent trace verifier."""

    def __init__(self, code: str, detail: str, *, facts: object | None = None) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.facts = facts


@dataclass(frozen=True, slots=True)
class TraceAnchor:
    path: str
    symbol: str
    ids: tuple[str, str, str]
    projection: str
    form: str


@dataclass(frozen=True, slots=True)
class TraceFact:
    covered: int
    exempted: int
    anchors: tuple[TraceAnchor, ...]

    def as_record(self) -> dict[str, object]:
        return {
            "code": "TRACE-COVERAGE-PASS",
            "covered": self.covered,
            "exempted": self.exempted,
            "anchors": [
                {
                    "path": anchor.path,
                    "symbol": anchor.symbol,
                    "ids": list(anchor.ids),
                    "projection": anchor.projection,
                    "form": anchor.form,
                }
                for anchor in self.anchors
            ],
        }

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.as_record())


@dataclass(frozen=True, slots=True)
class _ChangedTarget:
    path: str
    symbol: str


def _refuse(code: str, detail: str) -> None:
    raise TraceVerificationError(code, detail)


def _ids(raw: str, *, kind: str, vocabulary: Mapping[str, Sequence[str]] | None) -> tuple[str, ...]:
    values = tuple(raw.split(","))
    if not values or any(not value for value in values):
        _refuse(E_TRACE_GRAMMAR, f"empty {kind} ID")
    if any("*" in value for value in values):
        _refuse(E_TRACE_WILDCARD, f"wildcard {kind} ID")
    if vocabulary is not None and any(value not in vocabulary.get(kind, ()) for value in values):
        _refuse(E_TRACE_UNKNOWN, f"unknown {kind} ID")
    return values


def parse_trace_comment(
    line: str,
    *,
    ids: Mapping[str, Sequence[str]] | None = None,
    projections: set[str] | None = None,
) -> TraceAnchor:
    """Parse exactly the generated one-line Python or TypeScript comment form."""

    match = _COMMENT.fullmatch(line)
    if match is None:
        _refuse(E_TRACE_GRAMMAR, "trace comment is not the v1 generated form")
    rule, transition, outcome, projection = match.groups()
    parts = (
        _ids(rule, kind="rule", vocabulary=ids),
        _ids(transition, kind="transition", vocabulary=ids),
        _ids(outcome, kind="outcome", vocabulary=ids),
    )
    if projections is not None and projection not in projections:
        _refuse(E_TRACE_STALE, "projection is absent from the signed manifest")
    return TraceAnchor("", "", tuple(item for part in parts for item in part), projection, "comment")


def parse_trace_sidecar(
    raw: bytes,
    *,
    ids: Mapping[str, Sequence[str]],
    projections: set[str],
) -> TraceAnchor:
    """Parse the closed `trace-sidecar-v1` object, never a permissive JSON shape."""

    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TraceVerificationError(E_TRACE_SIDECAR, "sidecar is not JSON") from exc
    required = {"version", "projection", "path", "symbol", "ids"}
    if not isinstance(value, dict) or set(value) != required or value["version"] != "trace-sidecar-v1":
        _refuse(E_TRACE_SIDECAR, "sidecar does not have the closed v1 shape")
    if not isinstance(value["path"], str) or not isinstance(value["symbol"], str):
        _refuse(E_TRACE_SIDECAR, "sidecar path or symbol is not text")
    sidecar_ids = value["ids"]
    if not isinstance(sidecar_ids, dict) or set(sidecar_ids) != {"rule", "transition", "outcome"}:
        _refuse(E_TRACE_SIDECAR, "sidecar IDs do not have the closed v1 shape")
    parts: list[tuple[str, ...]] = []
    for kind in ("rule", "transition", "outcome"):
        values = sidecar_ids[kind]
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            _refuse(E_TRACE_SIDECAR, f"sidecar {kind} IDs are not strings")
        parts.append(_ids(",".join(values), kind=kind, vocabulary=ids))
    projection = value["projection"]
    if not isinstance(projection, str) or projection not in projections:
        _refuse(E_TRACE_STALE, "sidecar projection is absent from the signed manifest")
    return TraceAnchor(value["path"], value["symbol"], tuple(item for part in parts for item in part), projection, "sidecar")


def _candidate_path(root: Path, path: str) -> Path:
    if not path or Path(path).is_absolute() or ".." in Path(path).parts:
        _refuse(E_TRACE_PROTECTED, "manifest path leaves candidate root")
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        _refuse(E_TRACE_PROTECTED, "manifest path leaves candidate root")
    return resolved


def _in_scope(path: str, scope: Mapping[str, object]) -> bool:
    include = scope.get("include")
    exclude = scope.get("exclude")
    if not isinstance(include, list) or not isinstance(exclude, list):
        _refuse(E_TRACE_AUTHORITY, "A scope is malformed")
    return any(path == item or path.startswith(f"{item}/") for item in include) and not any(
        path == item or path.startswith(f"{item}/") for item in exclude
    )


def _symbol_for(lines: list[str], start: int) -> str:
    for index in range(min(start, len(lines) - 1), -1, -1):
        if match := _SYMBOL.match(lines[index]):
            return match.group(1)
    for line in lines[start:]:
        if match := _SYMBOL.match(line):
            return match.group(1)
    return f"line:{start + 1}"


def _changed_targets(base: Path, candidate: Path, scope: Mapping[str, object]) -> tuple[_ChangedTarget, ...]:
    paths = {
        path.relative_to(root).as_posix()
        for root in (base, candidate)
        if root.exists()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in _SOURCE_SUFFIXES
    }
    changed: list[_ChangedTarget] = []
    for path in sorted(paths):
        if not _in_scope(path, scope):
            continue
        before = (base / path).read_text("utf-8").splitlines() if (base / path).is_file() else []
        after = (candidate / path).read_text("utf-8").splitlines() if (candidate / path).is_file() else []
        matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
        for tag, _left_start, _left_end, right_start, _right_end in matcher.get_opcodes():
            if tag != "equal":
                changed.append(_ChangedTarget(path, _symbol_for(after, right_start)))
    return tuple(changed)


def _comment_anchors(
    candidate: Path,
    ids: Mapping[str, Sequence[str]],
    projections: set[str],
    scope: Mapping[str, object],
) -> tuple[TraceAnchor, ...]:
    anchors: list[TraceAnchor] = []
    for source in sorted(candidate.rglob("*")):
        if not source.is_file() or source.suffix not in _SOURCE_SUFFIXES:
            continue
        path = source.relative_to(candidate).as_posix()
        if not _in_scope(path, scope):
            continue
        lines = source.read_text("utf-8").splitlines()
        for index, line in enumerate(lines):
            if "ranex-trace:" in line:
                parsed = parse_trace_comment(line, ids=ids, projections=projections)
                anchors.append(TraceAnchor(path, _symbol_for(lines, index + 1), parsed.ids, parsed.projection, "comment"))
    return tuple(anchors)


def verify_trace_coverage(
    a: Mapping[str, object],
    b: Mapping[str, object],
    base: Path,
    candidate: Path,
    *,
    exemption_claims: Sequence[tuple[str, str, str]] = (),
) -> TraceFact:
    """Cover every changed in-scope source target by one exact signed reference."""

    ids = a.get("ids")
    scope = a.get("scope")
    artifacts = b.get("artifacts")
    exemptions = b.get("exemptions")
    if not isinstance(ids, Mapping) or not isinstance(scope, Mapping) or not isinstance(artifacts, Mapping):
        _refuse(E_TRACE_AUTHORITY, "A or B lacks required trace fields")
    projection_rows = artifacts.get("trace_projections")
    sidecar_rows = artifacts.get("sidecars")
    if not isinstance(projection_rows, list) or not isinstance(sidecar_rows, list) or not isinstance(exemptions, list):
        _refuse(E_TRACE_AUTHORITY, "B trace artifacts are malformed")
    projections = {row.get("digest") for row in projection_rows if isinstance(row, Mapping)}
    if len(projections) != len(projection_rows) or any(not isinstance(item, str) for item in projections):
        _refuse(E_TRACE_AUTHORITY, "B projection rows are malformed")
    comments = _comment_anchors(candidate, ids, projections, scope)
    sidecars: list[TraceAnchor] = []
    approved_sidecar_paths: set[str] = set()
    for row in sidecar_rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str):
            _refuse(E_TRACE_SIDECAR, "approved sidecar row is malformed")
        path = row["path"]
        approved_sidecar_paths.add(path)
        file = _candidate_path(candidate, path)
        if not file.is_file():
            _refuse(E_TRACE_SIDECAR, "approved sidecar is absent")
        parsed = parse_trace_sidecar(file.read_bytes(), ids=ids, projections=projections)
        sidecars.append(TraceAnchor(parsed.path, parsed.symbol, parsed.ids, parsed.projection, "sidecar"))
    for file in candidate.rglob("*"):
        if not file.is_file() or file.suffix != ".json":
            continue
        relative = file.relative_to(candidate).as_posix()
        if relative in approved_sidecar_paths:
            continue
        try:
            value = json.loads(file.read_bytes())
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("version") == "trace-sidecar-v1":
            _refuse(E_TRACE_SIDECAR, "candidate carries an unapproved trace sidecar")
    anchors = tuple(sorted((*comments, *sidecars), key=lambda anchor: (anchor.path, anchor.symbol, anchor.form, anchor.ids)))
    if len({(anchor.path, anchor.symbol, anchor.ids, anchor.projection) for anchor in anchors}) != len(anchors):
        _refuse(E_TRACE_DUPLICATE, "duplicate current trace anchor")

    exact_exemptions: dict[str, tuple[str, str]] = {}
    for row in exemptions:
        if not isinstance(row, Mapping):
            _refuse(E_TRACE_INVENTED, "exemption is not an object")
        path, klass, reason = row.get("path"), row.get("class"), row.get("reason")
        if not isinstance(path, str) or not isinstance(klass, str) or not isinstance(reason, str):
            _refuse(E_TRACE_INVENTED, "exemption fields are malformed")
        if "*" in path or "?" in path:
            _refuse(E_TRACE_EXEMPTION_WILDCARD, "exemption path has a wildcard")
        if not reason:
            _refuse(E_TRACE_REASONLESS, "exemption has no reason")
        if path in exact_exemptions:
            _refuse(E_TRACE_DUPLICATE, "duplicate exemption path")
        exact_exemptions[path] = (klass, reason)
    for path, klass, reason in exemption_claims:
        if "*" in path or "?" in path:
            _refuse(E_TRACE_EXEMPTION_WILDCARD, "claimed exemption path has a wildcard")
        if not reason:
            _refuse(E_TRACE_EXEMPTION, "claimed exemption has no reason")
        if exact_exemptions.get(path) != (klass, reason):
            _refuse(E_TRACE_INVENTED, "claimed exemption differs from signed manifest")

    covered = exempted = 0
    for target in _changed_targets(base, candidate, scope):
        if target.path in exact_exemptions:
            exempted += 1
            continue
        matching = [anchor for anchor in anchors if anchor.path == target.path and anchor.symbol == target.symbol]
        if not matching:
            _refuse(E_TRACE_UNCOVERED, f"no anchor for {target.path}:{target.symbol}")
        if len(matching) != 1:
            _refuse(E_TRACE_AMBIGUOUS, f"multiple anchors for {target.path}:{target.symbol}")
        covered += 1
    return TraceFact(covered, exempted, anchors)
