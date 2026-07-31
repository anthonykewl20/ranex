"""The docs layer governs itself.

This project previously accumulated 561 architecture documents and zero product
code. `CLAUDE.md` states the cap that prevents a repeat; a rule an agent can read
is a suggestion, so these tests are the constraint.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories whose markdown is not ours to govern.
_SKIP_DIRS = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "legacy",
}

_SLICE_NAME = re.compile(r"^SLICE-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_STATUS = re.compile(r"^\*\*Status:\*\*\s+(open|done)\s*$", re.MULTILINE)

_ALLOWED_EXACT = frozenset({"CLAUDE.md", "README.md", "docs/STATE.md"})

STATE_MAX_LINES = 50


def _tracked_markdown() -> list[Path]:
    """Every markdown file we are responsible for, relative to the repo root."""

    found: list[Path] = []
    for path in REPO_ROOT.rglob("*.md"):
        if any(part in _SKIP_DIRS for part in path.relative_to(REPO_ROOT).parts):
            continue
        found.append(path.relative_to(REPO_ROOT))
    return sorted(found)


def _is_allowed(relative: Path) -> bool:
    posix = relative.as_posix()
    if posix in _ALLOWED_EXACT:
        return True
    parent = relative.parent.as_posix()
    if parent in {"docs/slices", "docs/slices/done"}:
        return bool(_SLICE_NAME.fullmatch(relative.name))
    return False


def _slice_files(*, done: bool) -> list[Path]:
    directory = REPO_ROOT / "docs" / "slices" / ("done" if done else "")
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("SLICE-*.md") if p.is_file())


def test_no_document_exists_outside_the_allowed_set() -> None:
    """Session reports, summaries, handoffs, and plans are how bloat starts."""

    unexpected = [p.as_posix() for p in _tracked_markdown() if not _is_allowed(p)]
    assert not unexpected, (
        "these documents are not allowed by the docs cap in CLAUDE.md: "
        f"{unexpected}. Put the content in docs/STATE.md, the active slice, or "
        "the commit message instead of creating a new file."
    )


def test_at_most_one_slice_is_open() -> None:
    """The working rule: finish a slice before starting another."""

    open_slices = [
        path.name
        for path in _slice_files(done=False)
        if (match := _STATUS.search(path.read_text(encoding="utf-8")))
        and match.group(1) == "open"
    ]
    assert len(open_slices) <= 1, (
        f"{len(open_slices)} slices are open: {open_slices}. "
        "Finish one before starting another."
    )


@pytest.mark.parametrize("done", [False, True])
def test_every_slice_declares_a_status(done: bool) -> None:
    missing = [
        path.name
        for path in _slice_files(done=done)
        if _STATUS.search(path.read_text(encoding="utf-8")) is None
    ]
    assert not missing, f"slices without a '**Status:** open|done' line: {missing}"


def test_state_stays_a_pointer_not_a_log() -> None:
    """STATE.md is rewritten each session. Git already holds the history."""

    state = REPO_ROOT / "docs" / "STATE.md"
    assert state.is_file(), "docs/STATE.md is required — it is the entry point"
    lines = state.read_text(encoding="utf-8").splitlines()
    assert len(lines) <= STATE_MAX_LINES, (
        f"docs/STATE.md is {len(lines)} lines, cap is {STATE_MAX_LINES}. "
        "It is a pointer, not a log — rewrite it rather than appending."
    )


def test_state_names_the_active_slice() -> None:
    """A new session must be able to find the current work from STATE.md alone."""

    state = (REPO_ROOT / "docs" / "STATE.md").read_text(encoding="utf-8")
    match = re.search(r"^\*\*Active slice:\*\*\s+(.+)$", state, re.MULTILINE)
    assert match is not None, "docs/STATE.md must declare '**Active slice:**'"

    declared = match.group(1).strip()
    if declared.lower().startswith("none"):
        return

    referenced = re.search(r"docs/slices/(SLICE-\d{3}-[a-z0-9-]+\.md)", declared)
    assert referenced is not None, (
        f"active slice must be a docs/slices/ path or 'none', got: {declared!r}"
    )
    assert (REPO_ROOT / "docs" / "slices" / referenced.group(1)).is_file(), (
        f"docs/STATE.md points at {referenced.group(1)}, which does not exist"
    )


# --- README stays in sync with reality -------------------------------------
#
# The README is the public status page. Two documents both claiming "what we are
# working on" is how drift starts, so the overlap is checked rather than trusted.

_SLICE_STEM = re.compile(r"SLICE-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*")


def _active_slice_named_in(text: str) -> str | None:
    line = re.search(r"^\*\*Active slice:\*\*\s+(.+)$", text, re.MULTILINE)
    if line is None:
        return None
    stem = _SLICE_STEM.search(line.group(1))
    return stem.group(0) if stem else None


def test_readme_exists() -> None:
    assert (REPO_ROOT / "README.md").is_file(), "README.md is the public entry point"


def test_readme_and_state_agree_on_the_active_slice() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    state = (REPO_ROOT / "docs" / "STATE.md").read_text(encoding="utf-8")

    in_readme = _active_slice_named_in(readme)
    in_state = _active_slice_named_in(state)

    assert in_readme == in_state, (
        f"README.md says the active slice is {in_readme!r} but docs/STATE.md "
        f"says {in_state!r}. They must name the same slice."
    )


def test_readme_lists_exactly_the_finished_slices() -> None:
    """Closing a slice must update the README. Enforced, not remembered."""

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(
        r"^## Completed slices\s*\n(.*?)(?=^## |\Z)",
        readme,
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None, "README.md needs a '## Completed slices' section"

    claimed = set(_SLICE_STEM.findall(section.group(1)))
    archived = {path.stem for path in _slice_files(done=True)}

    assert claimed == archived, (
        f"README.md claims {sorted(claimed)} are complete but "
        f"docs/slices/done/ holds {sorted(archived)}. "
        "Move the slice file and update the README together."
    )
