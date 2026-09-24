"""Path-scoped kernel handbook resolution — issue #100, ADR-062.

MAP §5.1 records the kernel handbook as decided-but-unbuilt: "the catalog
exists, the injection does not". This module is the injection's engine — the
pure half. It resolves which handbook chapters apply to which repository
paths, over exactly two layers (project > system; one operator, §7.2, no
custom/global layer), and produces a digest over the canonical resolution so
a delegate run can name the chapters it was given.

Everything here is a pure function of its arguments — handbook entries, paths,
and the optional content peeks the system-layer sniffer consumes. No function
in this module reads a file, runs a subprocess, or consults the environment;
the IO boundary lives in :mod:`ranex.cli.delegation`, the only consumer.
`ranex run` and `ranex gate evaluate` never import this module: a handbook
chapter is guidance, "only the kernel enforces" (§5.1), and the contract test
`tests/contract/test_handbook_surface.py` refuses any other importer.

The designated shapes follow `alibaba/open-code-review`'s rule.json at the
behaviour level (ADR-062, MAP §15.3 — intent adopted, no code copied):

- entries are ``{path_glob, text, merge_system}``, declaration order matters,
  first match wins within a layer;
- ``merge_system`` keeps the matched system chapter alongside the project
  chapter, system text first;
- a content sniffer may decorate **only** the system layer, so a project rule
  is never overridden by a heuristic. A sniff is expressed as a system-layer
  entry carrying ``sniff_marker``: it wins over the plain path match only when
  the path's first non-blank line starts with that marker. The reference
  disambiguates the shared ``.m`` extension (MATLAB vs Objective-C) this way;
  Ranex keeps the mechanism data-driven rather than hard-coding an extension.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from ranex.foundation.canonical import canonical_sha256

PROJECT_LAYER = "project"
SYSTEM_LAYER = "system"

HANDBOOK_VERSION = 1

_ENTRY_REQUIRED_KEYS = ("path_glob", "text")
_ENTRY_OPTIONAL_KEYS = ("merge_system", "sniff_marker")

#: The digest prefix the whole repository uses for SHA-256 values.
_DIGEST_PREFIX = "sha256:"

_UNMATCHED = "unmatched"
_MATCHED = "matched"


@dataclass(frozen=True, slots=True)
class HandbookEntry:
    """One declared chapter of one layer, in declaration order."""

    path_glob: str
    text: str
    merge_system: bool = False
    sniff_marker: str | None = None


@dataclass(frozen=True, slots=True)
class Chapter:
    """A resolved chapter exactly as a packet hands it to the worker."""

    chapter_id: str
    layer: str
    pattern: str
    text: str
    merged: bool
    sniffed: bool


@dataclass(frozen=True, slots=True)
class PathResolution:
    """One path's row in the resolution table.

    ``system_pattern`` records the system entry that matched the path even
    when the project layer won, so a receipt can name both matches instead of
    only the winner. It is ``None`` when no system entry matched.
    """

    path: str
    status: str
    layer: str | None
    pattern: str | None
    chapter_id: str | None
    merged: bool
    sniffed: bool
    system_pattern: str | None


@dataclass(frozen=True, slots=True)
class HandbookResolution:
    """The full resolution: distinct chapters, one row per path, one digest."""

    chapters: tuple[Chapter, ...]
    rows: tuple[PathResolution, ...]
    digest: str

    def chapter_for(self, path: str) -> Chapter | None:
        """The chapter a path resolved to, or None when it was unmatched."""

        for row in self.rows:
            if row.path != path:
                continue
            if row.chapter_id is None:
                return None
            return next(
                chapter
                for chapter in self.chapters
                if chapter.chapter_id == row.chapter_id
            )
        return None


# --- parsing: the designated shape, and nothing else -------------------------


def parse_handbook_bytes(layer: str, data: bytes) -> tuple[HandbookEntry, ...]:
    """Parse and validate one layer's handbook bytes into ordered entries.

    Refuses — rather than repairs — every shape outside the designated
    grammar: absence blocks, and a silently-defaulted handbook chapter would
    be guidance nobody wrote.
    """

    if layer not in (PROJECT_LAYER, SYSTEM_LAYER):
        raise ValueError(f"refusing handbook layer {layer!r}: unknown layer")
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"refusing handbook {layer} layer: cannot parse JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"refusing handbook {layer} layer: top level is not an object")
    version = payload.get("version", HANDBOOK_VERSION)
    if version != HANDBOOK_VERSION:
        raise ValueError(f"refusing handbook {layer} layer: unsupported version {version!r}")
    unknown = sorted(set(payload) - {"version", "entries"})
    if unknown:
        raise ValueError(
            f"refusing handbook {layer} layer: unknown top-level keys {unknown}"
        )
    entries_raw = payload.get("entries")
    if not isinstance(entries_raw, list):
        raise ValueError(
            f"refusing handbook {layer} layer: 'entries' is missing or not a list"
        )
    entries: list[HandbookEntry] = []
    for position, item in enumerate(entries_raw):
        entries.append(_parse_entry(layer, position, item))
    return tuple(entries)


def _parse_entry(layer: str, position: int, item: Any) -> HandbookEntry:
    prefix = f"refusing handbook {layer} layer entry {position}"
    if not isinstance(item, dict):
        raise ValueError(f"{prefix}: entry is not an object")
    unknown = sorted(set(item) - set(_ENTRY_REQUIRED_KEYS) - set(_ENTRY_OPTIONAL_KEYS))
    if unknown:
        raise ValueError(f"{prefix}: unknown keys {unknown}")
    for key in _ENTRY_REQUIRED_KEYS:
        if key not in item:
            raise ValueError(f"{prefix}: missing {key!r}")
    path_glob = item["path_glob"]
    if not isinstance(path_glob, str) or not path_glob.strip():
        raise ValueError(f"{prefix}: 'path_glob' must be a non-empty string")
    text = item["text"]
    if not isinstance(text, str) or not text:
        raise ValueError(f"{prefix}: 'text' must be a non-empty string")
    merge_system = item.get("merge_system", False)
    if not isinstance(merge_system, bool):
        raise ValueError(f"{prefix}: 'merge_system' must be a boolean")
    sniff_marker = item.get("sniff_marker")
    if sniff_marker is not None:
        if layer != SYSTEM_LAYER:
            raise ValueError(
                f"{prefix}: sniff_marker is system-layer only; a heuristic may "
                "never decorate a project rule"
            )
        if not isinstance(sniff_marker, str) or not sniff_marker:
            raise ValueError(f"{prefix}: 'sniff_marker' must be a non-empty string")
    return HandbookEntry(
        path_glob=path_glob,
        text=text,
        merge_system=merge_system,
        sniff_marker=sniff_marker,
    )


# --- the glob language --------------------------------------------------------
#
# A deliberately small dialect of git-style path globs, matched against
# repo-relative POSIX paths, case-sensitively (git paths are; the reference
# lowercases for portability across hosts Ranex does not serve — ADR-062):
#
#   ``**``  any characters including ``/`` (so ``src/**`` names everything
#           under ``src/`` but not ``src`` itself)
#   ``**/`` zero or more whole path components
#   ``*``   any characters except ``/``
#   ``?``   one character except ``/``
#   ``[…]`` a character class, ``a-z`` ranges only; negation forms are refused
#
# No brace expansion and no escape syntax: the knob surface stays small
# (§17.6), and everything refused here is refused loudly at match time.


@lru_cache(maxsize=256)
def _glob_regex(pattern: str) -> re.Pattern[str]:
    parts: list[str] = []
    index = 0
    length = len(pattern)
    while index < length:
        character = pattern[index]
        if character == "*":
            if pattern.startswith("**/", index):
                parts.append("(?:[^/]+/)*")
                index += 3
            elif pattern.startswith("**", index):
                parts.append(".*")
                index += 2
            else:
                parts.append("[^/]*")
                index += 1
        elif character == "?":
            parts.append("[^/]")
            index += 1
        elif character == "[":
            closing = pattern.find("]", index + 1)
            if closing == -1:
                raise ValueError(
                    f"refusing handbook glob {pattern!r}: unterminated character class"
                )
            body = pattern[index + 1 : closing]
            if body[:1] in ("^", "!"):
                raise ValueError(
                    f"refusing handbook glob {pattern!r}: character-class "
                    "negation is not part of the glob language"
                )
            if "\\" in body:
                raise ValueError(
                    f"refusing handbook glob {pattern!r}: escapes are not part "
                    "of the glob language"
                )
            if not body:
                raise ValueError(
                    f"refusing handbook glob {pattern!r}: empty character class"
                )
            parts.append(f"[{body}]")
            index = closing + 1
        else:
            parts.append(re.escape(character))
            index += 1
    return re.compile("".join(parts) + r"\Z")


def glob_matches(pattern: str, path: str) -> bool:
    """Does one path glob match one repo-relative POSIX path?"""

    return _glob_regex(pattern).match(path) is not None


# --- resolution ---------------------------------------------------------------


def resolve_handbook(
    system_entries: Sequence[HandbookEntry],
    project_entries: Sequence[HandbookEntry],
    paths: Sequence[str],
    peeks: Mapping[str, str] | None = None,
) -> HandbookResolution:
    """Resolve every path against the two layers and digest the result.

    Precedence per path: the first matching project entry wins; the first
    matching system entry applies otherwise. ``merge_system`` on the winning
    project entry keeps the matched system chapter in front of the project
    text. A sniff-marker system entry can win inside the system layer only,
    and only when the path's peeked first non-blank line starts with its
    marker — a heuristic never outranks a project rule.
    """

    chapters: list[Chapter] = []
    chapter_ids: dict[tuple[str, str, str, bool, bool], str] = {}
    pattern_occurrences: dict[str, int] = {}
    rows: list[PathResolution] = []
    for path in paths:
        system_entry, sniffed = _system_match(system_entries, path, peeks)
        project_entry = _project_match(project_entries, path)

        if project_entry is not None:
            layer = PROJECT_LAYER
            pattern = project_entry.path_glob
            merged = project_entry.merge_system
            if merged and system_entry is not None:
                text = _merge_texts(system_entry.text, project_entry.text)
            else:
                text = project_entry.text
            # The sniff never participates in a project win's own text; it
            # only ever selected the system half of a merge.
            row_sniffed = bool(merged and sniffed)
        elif system_entry is not None:
            layer = SYSTEM_LAYER
            pattern = system_entry.path_glob
            merged = False
            text = system_entry.text
            row_sniffed = sniffed
        else:
            rows.append(
                PathResolution(
                    path=path,
                    status=_UNMATCHED,
                    layer=None,
                    pattern=None,
                    chapter_id=None,
                    merged=False,
                    sniffed=False,
                    system_pattern=None,
                )
            )
            continue

        chapter_id = _chapter_id_for(
            chapters,
            chapter_ids,
            pattern_occurrences,
            layer=layer,
            pattern=pattern,
            text=text,
            merged=merged,
            sniffed=row_sniffed,
        )
        rows.append(
            PathResolution(
                path=path,
                status=_MATCHED,
                layer=layer,
                pattern=pattern,
                chapter_id=chapter_id,
                merged=merged,
                sniffed=row_sniffed,
                system_pattern=system_entry.path_glob if system_entry is not None else None,
            )
        )
    return HandbookResolution(
        chapters=tuple(chapters),
        rows=tuple(rows),
        digest=_DIGEST_PREFIX + canonical_sha256(_digest_value(chapters, rows)),
    )


def _project_match(
    entries: Sequence[HandbookEntry], path: str
) -> HandbookEntry | None:
    for entry in entries:
        if glob_matches(entry.path_glob, path):
            return entry
    return None


def _system_match(
    entries: Sequence[HandbookEntry],
    path: str,
    peeks: Mapping[str, str] | None,
) -> tuple[HandbookEntry | None, bool]:
    """The system entry for a path, and whether a content sniff selected it.

    A plain entry matches on the glob alone (first match wins). A
    sniff-marker entry matches only when the peeked content agrees; the first
    agreeing marker entry outranks the plain match — that is the entire point
    of content disambiguation — but nothing here can ever outrank the project
    layer, which is resolved separately.
    """

    fallback: HandbookEntry | None = None
    peek = peeks.get(path) if peeks is not None else None
    for entry in entries:
        if not glob_matches(entry.path_glob, path):
            continue
        if entry.sniff_marker is None:
            if fallback is None:
                fallback = entry
            continue
        if peek is not None and _peek_agrees(peek, entry.sniff_marker):
            return entry, True
    if fallback is None:
        return None, False
    return fallback, False


def _peek_agrees(peek: str, marker: str) -> bool:
    """Does the first non-blank peeked line start with the marker?"""

    for line in peek.splitlines():
        stripped = line.lstrip()
        if stripped:
            return stripped.startswith(marker)
    return False


def _merge_texts(system_text: str, project_text: str) -> str:
    """System chapter first, project chapter second (reference behaviour)."""

    if not system_text:
        return project_text
    if not project_text:
        return system_text
    return (
        "## System handbook chapter\n\n"
        + system_text
        + "\n\n---\n\n## Project handbook chapter\n\n"
        + project_text
    )


def _chapter_id_for(
    chapters: list[Chapter],
    chapter_ids: dict[tuple[str, str, str, bool, bool], str],
    pattern_occurrences: dict[str, int],
    *,
    layer: str,
    pattern: str,
    text: str,
    merged: bool,
    sniffed: bool,
) -> str:
    """Dedupe chapters by resolved content, ids stable in first-appearance order."""

    key = (layer, pattern, text, merged, sniffed)
    existing = chapter_ids.get(key)
    if existing is not None:
        return existing
    base = f"{layer}:{pattern}"
    occurrences = pattern_occurrences.get(base, 0) + 1
    pattern_occurrences[base] = occurrences
    chapter_id = base if occurrences == 1 else f"{base}#{occurrences}"
    chapter_ids[key] = chapter_id
    chapters.append(
        Chapter(
            chapter_id=chapter_id,
            layer=layer,
            pattern=pattern,
            text=text,
            merged=merged,
            sniffed=sniffed,
        )
    )
    return chapter_id


def _digest_value(
    chapters: Sequence[Chapter], rows: Sequence[PathResolution]
) -> dict[str, Any]:
    """The canonical value the resolution digest covers.

    Chapter texts are included by value, so changing one byte of any chapter
    — or of the glob that selects it, or of the merge flag — changes the
    digest. Rows are included so the digest also names the exact path table
    the packet was built from.
    """

    return {
        "chapters": [
            {
                "chapter_id": chapter.chapter_id,
                "layer": chapter.layer,
                "pattern": chapter.pattern,
                "text": chapter.text,
                "merged": chapter.merged,
                "sniffed": chapter.sniffed,
            }
            for chapter in chapters
        ],
        "rows": [
            {
                "path": row.path,
                "status": row.status,
                "layer": row.layer,
                "pattern": row.pattern,
                "chapter_id": row.chapter_id,
                "merged": row.merged,
                "sniffed": row.sniffed,
                "system_pattern": row.system_pattern,
            }
            for row in rows
        ],
    }


# --- the rendered brief ---------------------------------------------------------


def render_brief(resolution: HandbookResolution) -> str:
    """Render the packet's handbook section: chapters, then the full table.

    Every path in scope appears — matched paths name their chapter, unmatched
    paths say ``unmatched`` — because a silently dropped path is guidance the
    packet claimed to give and did not.
    """

    if not resolution.chapters and not resolution.rows:
        return ""
    lines: list[str] = [
        "## Kernel handbook — guidance, never authority",
        "",
        "These chapters are guidance for the files in scope. Only the kernel",
        "enforces; no chapter can widen, narrow or replace a gate, claim,",
        "verdict or journal rule.",
        "",
    ]
    for chapter in resolution.chapters:
        merged = "yes" if chapter.merged else "no"
        sniffed = "yes" if chapter.sniffed else "no"
        lines.append(f"### Chapter {chapter.chapter_id}")
        lines.append(
            f"(layer={chapter.layer} pattern={chapter.pattern} "
            f"merged={merged} sniffed={sniffed})"
        )
        lines.append("")
        lines.append(chapter.text)
        lines.append("")
    lines.append("### Resolution table")
    lines.append("")
    for row in resolution.rows:
        target = row.chapter_id if row.chapter_id is not None else _UNMATCHED
        lines.append(f"- {row.path} → {target}")
    return "\n".join(lines)
