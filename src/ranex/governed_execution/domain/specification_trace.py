"""Pure, fail-closed trace-reference parsing and candidate-tree coverage."""

from __future__ import annotations

import difflib
import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

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
E_TRACE_MISSING = "E-TRACE-017"

_COMMENT = re.compile(
    r"(#|//) ranex-trace: rule=([^\s]+) transition=([^\s]+) "
    r"outcome=([^\s]+) projection=(sha256:[0-9a-f]{64})\Z"
)
_SYMBOL = re.compile(r"^\s*(?:def|class|(?:export\s+)?function)\s+([A-Za-z_$][\w$]*)")
_SOURCE_SUFFIXES = {".py", ".ts", ".js"}


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
    ids: tuple[str, ...]
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
    comment_coverable: bool


def _refuse(code: str, detail: str) -> NoReturn:
    raise TraceVerificationError(code, detail)


def _ids(raw: str, *, kind: str, vocabulary: Mapping[str, Sequence[str]] | None) -> tuple[str, ...]:
    values = tuple(raw.split(","))
    if not values or any(not value for value in values):
        _refuse(E_TRACE_GRAMMAR, f"empty {kind} ID")
    if any("*" in value for value in values):
        _refuse(E_TRACE_WILDCARD, f"wildcard {kind} ID")
    if len(set(values)) != len(values):
        _refuse(E_TRACE_GRAMMAR, f"duplicate {kind} ID")
    if vocabulary is not None and any(value not in vocabulary.get(kind, ()) for value in values):
        _refuse(E_TRACE_UNKNOWN, f"unknown {kind} ID")
    return values


def parse_trace_comment(
    line: str,
    *,
    ids: Mapping[str, Sequence[str]] | None = None,
    projections: set[str] | None = None,
) -> TraceAnchor:
    """Parse exactly the generated one-line Python or ECMAScript comment form."""

    match = _COMMENT.fullmatch(line)
    if match is None:
        _refuse(E_TRACE_GRAMMAR, "trace comment is not the v1 generated form")
    _prefix, rule, transition, outcome, projection = match.groups()
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


def _symbol_starts(lines: Sequence[str]) -> tuple[tuple[int, str], ...]:
    return tuple((index, match.group(1)) for index, line in enumerate(lines) if (match := _SYMBOL.match(line)))


def _symbol_for(starts: Sequence[tuple[int, str]], position: int) -> str:
    """Resolve only against the tree's declared symbol starts, never text similarity."""

    for start, symbol in reversed(starts):
        if start <= position:
            return symbol
    for _start, symbol in starts:
        return symbol
    return f"line:{position + 1}"


def _candidate_symbols_for_change(starts: Sequence[tuple[int, str]], start: int, end: int) -> tuple[str, ...]:
    """Return every declaration introduced by a hunk, or its enclosing region."""

    introduced = tuple(symbol for symbol_start, symbol in starts if start <= symbol_start < end)
    return introduced or (_symbol_for(starts, start),)


def _read_source(path: Path) -> list[str]:
    try:
        return path.read_text("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise TraceVerificationError(E_TRACE_PROTECTED, f"source is not valid UTF-8: {path}") from exc


def _projection_descriptors(rows: Sequence[object], candidate: Path) -> dict[str, tuple[str, str, str, tuple[str, ...]]]:
    """Read each B-bound canonical descriptor and index its exact anchor identity."""

    descriptors: dict[str, tuple[str, str, str, tuple[str, ...]]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("path"), str) or not isinstance(row.get("digest"), str):
            _refuse(E_TRACE_AUTHORITY, "B projection row is malformed")
        file = _candidate_path(candidate, row["path"])
        if not file.is_file():
            _refuse(E_TRACE_AUTHORITY, "B projection descriptor is absent")
        raw = file.read_bytes()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        if digest != row["digest"]:
            _refuse(E_TRACE_AUTHORITY, "B projection descriptor bytes differ from its digest")
        try:
            descriptor = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise TraceVerificationError(E_TRACE_AUTHORITY, "B projection descriptor is not JSON") from exc
        if (
            not isinstance(descriptor, dict)
            or set(descriptor) != {"version", "path", "language", "ids", "anchor"}
            or descriptor.get("version") != "trace-projection-v1"
            or not isinstance(descriptor.get("path"), str)
            or descriptor.get("language") not in {"python", "typescript", "javascript", "sidecar-json"}
            or not isinstance(descriptor.get("anchor"), dict)
            or set(descriptor["anchor"]) != {"symbol"}
            or not isinstance(descriptor["anchor"].get("symbol"), str)
            or not isinstance(descriptor.get("ids"), dict)
            or set(descriptor["ids"]) != {"rule", "transition", "outcome"}
            or raw != canonical_json_bytes(descriptor)
        ):
            _refuse(E_TRACE_AUTHORITY, "B projection descriptor is not the closed canonical v1 form")
        flattened: list[str] = []
        for kind in ("rule", "transition", "outcome"):
            values = descriptor["ids"][kind]
            if not isinstance(values, list) or any(not isinstance(value, str) or not value for value in values) or len(set(values)) != len(values):
                _refuse(E_TRACE_AUTHORITY, "B projection descriptor IDs are malformed")
            flattened.extend(values)
        if digest in descriptors:
            _refuse(E_TRACE_AUTHORITY, "B repeats a projection digest")
        descriptors[digest] = (descriptor["path"], descriptor["language"], descriptor["anchor"]["symbol"], tuple(flattened))
    return descriptors


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
        before = _read_source(base / path) if (base / path).is_file() else []
        after = _read_source(candidate / path) if (candidate / path).is_file() else []
        before_symbols = _symbol_starts(before)
        after_symbols = _symbol_starts(after)
        matcher = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
        for tag, left_start, left_end, right_start, right_end in matcher.get_opcodes():
            if tag == "equal":
                continue
            base_symbols = (
                _candidate_symbols_for_change(before_symbols, left_start, left_end)
                if tag in {"delete", "replace"}
                else ()
            )
            candidate_symbols = (
                _candidate_symbols_for_change(after_symbols, right_start, right_end)
                if tag in {"insert", "replace"}
                else ()
            )
            changed.extend(
                _ChangedTarget(path, base_symbol, False)
                for base_symbol in base_symbols
                if base_symbol not in candidate_symbols
            )
            changed.extend(_ChangedTarget(path, candidate_symbol, True) for candidate_symbol in candidate_symbols)
    return tuple(dict.fromkeys(changed))


def _comment_anchors(
    candidate: Path,
    ids: Mapping[str, Sequence[str]],
    projections: set[str],
    scope: Mapping[str, object],
    descriptors: Mapping[str, tuple[str, str, str, tuple[str, ...]]],
) -> tuple[TraceAnchor, ...]:
    anchors: list[TraceAnchor] = []
    for source in sorted(candidate.rglob("*")):
        if not source.is_file() or source.suffix not in _SOURCE_SUFFIXES:
            continue
        path = source.relative_to(candidate).as_posix()
        if not _in_scope(path, scope):
            continue
        lines = _read_source(source)
        expected_prefix = {".py": "#", ".ts": "//", ".js": "//"}[source.suffix]
        expected_language = {".py": "python", ".ts": "typescript", ".js": "javascript"}[source.suffix]
        for index, line in enumerate(lines):
            if "ranex-trace:" in line:
                if not line.startswith(expected_prefix + " ranex-trace:"):
                    _refuse(E_TRACE_GRAMMAR, "trace comment prefix does not match source language")
                parsed = parse_trace_comment(line, ids=ids, projections=projections)
                if index + 1 >= len(lines) or (match := _SYMBOL.match(lines[index + 1])) is None:
                    _refuse(E_TRACE_GRAMMAR, "trace comment must directly precede a symbol")
                anchor = TraceAnchor(path, match.group(1), parsed.ids, parsed.projection, "comment")
                if descriptors.get(anchor.projection) != (anchor.path, expected_language, anchor.symbol, anchor.ids):
                    _refuse(E_TRACE_STALE, "trace comment does not match its signed descriptor")
                anchors.append(anchor)
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
    # A non-str digest cannot join the set: every row shape the filter drops
    # (non-object row, missing or non-text digest) fails the length identity
    # below with the same refusal the isinstance arm used to raise.
    projections = {digest for row in projection_rows if isinstance(row, Mapping) and isinstance((digest := row.get("digest")), str)}
    if len(projections) != len(projection_rows) or any(not isinstance(item, str) for item in projections):
        _refuse(E_TRACE_AUTHORITY, "B projection rows are malformed")
    descriptors = _projection_descriptors(projection_rows, candidate)
    comments = _comment_anchors(candidate, ids, projections, scope, descriptors)
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
        raw = file.read_bytes()
        digest = row.get("digest")
        if not isinstance(digest, str) or digest != "sha256:" + hashlib.sha256(raw).hexdigest():
            _refuse(E_TRACE_SIDECAR, "approved sidecar bytes differ from B")
        parsed = parse_trace_sidecar(raw, ids=ids, projections=projections)
        descriptor = descriptors.get(parsed.projection)
        expected_language = {".py": "python", ".ts": "typescript", ".js": "javascript"}.get(
            Path(parsed.path).suffix, "sidecar-json"
        )
        if (
            descriptor is None
            or descriptor[0] != parsed.path
            or descriptor[1] != expected_language
            or descriptor[2] != parsed.symbol
            or descriptor[3] != parsed.ids
        ):
            _refuse(E_TRACE_STALE, "trace sidecar does not match its signed descriptor")
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
    targets = _changed_targets(base, candidate, scope)
    if targets and not anchors and not exact_exemptions:
        _refuse(E_TRACE_MISSING, "candidate has no trace anchor or signed exemption")
    for target in targets:
        if target.path in exact_exemptions:
            exempted += 1
            continue
        matching = [
            anchor
            for anchor in anchors
            if anchor.path == target.path
            and anchor.symbol == target.symbol
            and (target.comment_coverable or anchor.form == "sidecar")
        ]
        if not matching:
            _refuse(E_TRACE_UNCOVERED, f"no anchor for {target.path}:{target.symbol}")
        if len(matching) != 1:
            _refuse(E_TRACE_AMBIGUOUS, f"multiple anchors for {target.path}:{target.symbol}")
        covered += 1
    return TraceFact(covered, exempted, anchors)
