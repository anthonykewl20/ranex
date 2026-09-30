"""Bounded subject snapshots owned by one SARIF interpretation, never a run cache."""
from __future__ import annotations

import sys
from collections import OrderedDict
from dataclasses import dataclass, fields, replace
from pathlib import Path

from ranex.foundation.suite_results import read_results_artifact

MAX_SUBJECT_CACHE_BYTES = 16 * 1024 * 1024
MAX_SUBJECT_CACHE_ENTRIES = 32


@dataclass(frozen=True, slots=True)
class _View:
    raw: bytes
    lines: tuple[bytes, ...] | None = None
    text_lines: tuple[str, ...] | None = None
    compact: tuple[tuple[int, str], ...] | None = None


def _normalise_excerpt(text: str) -> str:
    """Whitespace-normalise an excerpt: strip diff markers and blank lines."""

    lines: list[str] = []
    for line in text.splitlines():
        stripped = line[1:] if line[:1] in "+- " else line
        stripped = stripped.strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _storage_bytes(value: object, seen: set[int] | None = None) -> int:
    """Count retained Python objects, including keys, tuples and decoded lines.

    Sharing inside one entry is counted once; sharing across entries is counted
    twice, conservatively. No file-size-only estimate hides per-line overhead.
    """
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, _View):
        size += sum(_storage_bytes(getattr(value, field.name), seen) for field in fields(value))
    elif isinstance(value, tuple):
        size += sum(_storage_bytes(item, seen) for item in value)
    return size


class SubjectReader:
    """One parse's bounded LRU of bytes and derived line views.

    First acquisition always uses the regular-file, descriptor-confined and
    byte-bounded reader. A retained view is a consistent snapshot for this
    invocation. Every public parse constructs a new reader. Entries or derived
    views that exceed the aggregate budget are returned without retaining them;
    a smaller retained byte view remains useful when its line view is too large.
    """

    def __init__(
        self, subject_root: Path, *, max_cache_bytes: int = MAX_SUBJECT_CACHE_BYTES,
        max_entries: int = MAX_SUBJECT_CACHE_ENTRIES,
    ) -> None:
        if not isinstance(max_cache_bytes, int) or isinstance(max_cache_bytes, bool) or max_cache_bytes < 0:
            raise ValueError("subject cache byte budget must be a non-negative integer")
        if not isinstance(max_entries, int) or isinstance(max_entries, bool) or max_entries < 0:
            raise ValueError("subject cache entry budget must be a non-negative integer")
        self.subject_root = subject_root
        self.max_cache_bytes = max_cache_bytes
        self.max_entries = max_entries
        self._entries: OrderedDict[str, tuple[_View, int]] = OrderedDict()
        self._entry_bytes = 0

    @property
    def retained_bytes(self) -> int:
        return self._entry_bytes + sys.getsizeof(self._entries) if self._entries else 0

    def _remember(self, path: str, view: _View) -> None:
        if not self.max_entries or len(view.raw) > self.max_cache_bytes:
            return
        # Include the retained (view, cost) value tuple and integer as well as
        # the path and view. This deliberately overcounts its accounting tuple.
        cost = _storage_bytes((path, view)) + sys.getsizeof((view, 0)) + sys.getsizeof(0)
        if cost + sys.getsizeof(self._entries) > self.max_cache_bytes:
            return
        old = self._entries.pop(path, None)
        if old is not None:
            self._entry_bytes -= old[1]
        self._entries[path] = (view, cost)
        self._entry_bytes += cost
        while len(self._entries) > self.max_entries or self.retained_bytes > self.max_cache_bytes:
            _, (_, removed) = self._entries.popitem(last=False)
            self._entry_bytes -= removed

    def _view(self, path: str) -> _View:
        retained = self._entries.get(path)
        if retained is not None:
            self._entries.move_to_end(path)
            return retained[0]
        view = _View(read_results_artifact(path, subject_root=self.subject_root))
        self._remember(path, view)
        return view

    def read(self, path: str) -> bytes:
        return self._view(path).raw

    def lines(self, path: str) -> tuple[bytes, ...]:
        view = self._view(path)
        if view.lines is None:
            view = replace(view, lines=tuple(view.raw.splitlines(keepends=True)))
            self._remember(path, view)
        assert view.lines is not None
        return view.lines

    def text_lines(self, path: str) -> tuple[str, ...]:
        view = self._view(path)
        if view.text_lines is None:
            view = replace(view, text_lines=tuple(view.raw.decode('utf-8').splitlines(keepends=True)))
            self._remember(path, view)
        assert view.text_lines is not None
        return view.text_lines

    def compact_lines(self, path: str) -> tuple[tuple[int, str], ...]:
        view = self._view(path)
        if view.compact is None:
            compact = tuple((index, text) for index, line in enumerate(view.raw.decode('utf-8').splitlines())
                            if (text := _normalise_excerpt(line)))
            view = replace(view, compact=compact)
            self._remember(path, view)
        assert view.compact is not None
        return view.compact
