"""A BUILT claim in the map must name the evidence that makes it BUILT.

Issue #106. `docs/MAP.md` §16 draws each operator concern as a chain of steps
and marks every step BUILT, OPEN or ABSENT. §8.1 does the same for trust
boundaries with `CONFIRMED`. Both labels are read as "this is proven", and
until now neither had to say *by what* — the rows cited slices and ADRs, which
record that a decision was made, never that it was executed.

An accepted ADR does not make a thing CONFIRMED; §0.1 of the map says so in its
own words. This test makes that rule enforceable: a step that claims to be
built names a test file or a retained audit receipt, and the named path exists.
A row that cannot cite must be relabelled, which is the honest outcome.

Deliberately a *resolution* check, not a semantic one. It proves the citation
points at something real; it cannot prove the named test exercises the claim.
That limit is the same one §5.5 records for the bill-of-materials checker, and
naming it here keeps this test from being read as more than it is.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP = REPO_ROOT / "docs" / "MAP.md"

# A citation is a repository path a reader can open: a test module, or a
# retained receipt/driver under the dogfood tree. Slice and ADR references are
# deliberately NOT citations — they record a decision, not an execution.
_CITATION = re.compile(r"(?:tests|tools)/[A-Za-z0-9_][A-Za-z0-9_./-]*")

# `[3] BUILT  the bound command is …`, continuing over indented lines until the
# next marker or the end of the fenced block.
_STEP = re.compile(r"^\s*\[\d+\]\s+(BUILT|OPEN|ABSENT)\b")

_FENCE = "```"


def _map_text() -> str:
    return MAP.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    lines = text.splitlines()
    try:
        first = next(i for i, line in enumerate(lines) if line.startswith(start))
        last = next(i for i, line in enumerate(lines[first + 1 :], first + 1) if line.startswith(end))
    except StopIteration:  # pragma: no cover - a missing section is its own failure
        raise AssertionError(f"docs/MAP.md is missing the section {start!r}") from None
    return "\n".join(lines[first:last])


def _built_steps(text: str) -> list[tuple[str, str]]:
    """Every `[N] BUILT` step in §16, as (label, full text including wrapped lines)."""

    steps: list[tuple[str, str]] = []
    inside_fence = False
    current: list[str] | None = None
    marker = ""
    for line in text.splitlines():
        if line.strip().startswith(_FENCE):
            if current is not None:
                steps.append((marker, "\n".join(current)))
                current = None
            inside_fence = not inside_fence
            continue
        if not inside_fence:
            continue
        found = _STEP.match(line)
        if found:
            if current is not None:
                steps.append((marker, "\n".join(current)))
            marker = found.group(1)
            current = [line]
        elif current is not None:
            if line.strip() and line.startswith(" " * 6):
                current.append(line)
            else:
                steps.append((marker, "\n".join(current)))
                current = None
    if current is not None:
        steps.append((marker, "\n".join(current)))
    return [(label, body) for label, body in steps if label == "BUILT"]


def _confirmed_rows(text: str) -> list[str]:
    rows = []
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 3 and "CONFIRMED" in cells[-1]:
            rows.append(line)
    return rows


def _uncited(entries: list[str]) -> list[str]:
    return [entry for entry in entries if not _CITATION.search(entry)]


def _unresolved(entries: list[str]) -> list[str]:
    missing = []
    for entry in entries:
        for candidate in _CITATION.findall(entry):
            if not (REPO_ROOT / candidate).exists():
                missing.append(f"{candidate} (in: {entry.strip()[:70]}…)")
    return missing


def test_every_built_step_in_section_16_cites_its_evidence() -> None:
    section = _section(_map_text(), "## §16 Per-problem architecture", "## §17 ")
    bodies = [body for _, body in _built_steps(section)]
    assert bodies, "§16 declares no BUILT step; the parser or the section moved"
    uncited = _uncited(bodies)
    assert not uncited, (
        "§16 steps marked BUILT that name no test or retained receipt: "
        f"{[body.strip()[:80] for body in uncited]}. An accepted ADR or a closed "
        "slice records a decision, not an execution — cite the gauge or relabel "
        "the step OPEN."
    )


def test_every_confirmed_trust_boundary_cites_its_evidence() -> None:
    section = _section(_map_text(), "### 8.1 Trust boundaries", "### 8.2 ")
    rows = _confirmed_rows(section)
    assert rows, "§8.1 declares no CONFIRMED boundary; the parser or the table moved"
    uncited = _uncited(rows)
    assert not uncited, (
        "§8.1 boundaries marked CONFIRMED that name no test or retained receipt: "
        f"{[row[:80] for row in uncited]}."
    )


def test_every_citation_resolves() -> None:
    text = _map_text()
    entries = [body for _, body in _built_steps(_section(text, "## §16 Per-problem architecture", "## §17 "))]
    entries += _confirmed_rows(_section(text, "### 8.1 Trust boundaries", "### 8.2 "))
    unresolved = _unresolved(entries)
    assert not unresolved, (
        f"§8.1/§16 cite paths that do not exist: {unresolved}. A citation a "
        "reader cannot open is worse than none — it reads as coverage."
    )


# --- negative controls -------------------------------------------------------
#
# A check with no negative control is fluff: it passes, and nobody knows whether
# it could ever fail. These two prove the parser actually catches the shapes the
# tests above exist to refuse.


def test_an_uncited_built_step_is_caught() -> None:
    fabricated = (
        "## §16 Per-problem architecture\n\n"
        "```\n [1] BUILT  a claim with no gauge behind it (SLICE-999)\n```\n\n"
        "## §17 "
    )
    bodies = [body for _, body in _built_steps(fabricated)]
    assert bodies, "the parser did not see the fabricated BUILT step"
    assert _uncited(bodies), "an uncited BUILT step slipped past the citation check"


@pytest.mark.parametrize("path", ["tests/does_not_exist.py", "tools/dogfood/nope.json"])
def test_a_dangling_citation_is_caught(path: str) -> None:
    assert _unresolved([f" [1] BUILT  something ({path})"]), (
        f"a citation naming the missing {path} was treated as resolved"
    )
