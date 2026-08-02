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

_ADR_NAME = re.compile(r"^ADR-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ADR_STATUS = re.compile(
    r"^\*\*Status:\*\*\s+(proposed|accepted|rejected|deprecated"
    r"|superseded by ADR-\d{3})\s*$",
    re.MULTILINE,
)
_ADR_REF = re.compile(r"docs/adr/(ADR-\d{3}-[a-z0-9-]+\.md)")
_CITATION = re.compile(r"https?://\S+")

# Research is for CODE. A spec says what someone intended; a mature
# implementation says what survived contact with reality, and there is a great
# deal of open source that already solved these problems. We are not the first
# here and not the smartest: find the implementation that works, read it, copy
# what holds, and say what we deliberately did not copy.
_CODE_HOST = re.compile(
    r"https?://(?:www\.)?(?:github\.com|gitlab\.com|codeberg\.org|bitbucket\.org"
    r"|git\.sr\.ht)/\S+",
    re.IGNORECASE,
)

# Pinned to an immutable revision — a 40-hex commit or a version tag — and never
# to a branch. A link to `main` describes whatever main became, so a reviewer
# cannot read what was actually copied. This repo already binds evidence to a
# subject digest for exactly this reason; research is bound the same way.
_PINNED_REVISION = re.compile(
    r"/(?:-/)?(?:blob|tree|raw|src)/(?:[0-9a-f]{40}|v?\d[\w.\-]*)/",
    re.IGNORECASE,
)

# Copying is the point, so the licence is not paperwork. This repo is MIT, and
# pulling a copyleft implementation into it is a licensing problem that no test
# elsewhere would catch.
_LICENCE = re.compile(r"^\s*[-*]?\s*(?:\*\*)?Licen[cs]e(?:\*\*)?:", re.MULTILINE)

# CLAUDE.md has always demanded this and nothing has ever checked it: "read the
# prior art closely enough to find its known weakness; adopting a design without
# its caveats is how you ship decoration."
_WEAKNESS = re.compile(r"^\s*[-*]?\s*(?:\*\*)?Weakness(?:\*\*)?:", re.MULTILINE)

# Two, so a single lucky find cannot stand in for looking. Not more, because
# research must be efficient — this is a floor on rigour, not a reading quota.
MIN_CODE_CITATIONS = 2

# ADRs written before this rule landed on 2026-08-02. They are not retro-fitted:
# rewriting an accepted decision to satisfy a rule it predates would manufacture
# exactly the fake compliance the rule exists to prevent, and ADR-000 decides a
# document format, for which a specification genuinely is the prior art.
_PRE_CODE_RULE_ADRS = frozenset({
    "ADR-000-how-we-write-adrs.md",
    "ADR-001-claim-command-binding.md",
    "ADR-002-committed-trust-root.md",
})

# The template is MADR 4.0.0's *minimal* form, plus `### Confirmation` promoted
# from its full form, plus the sections this project adds. MADR's full template
# is deliberately not used: its option headings are variable strings
# (`### {title of option 1}`) and cannot be compiled into a check.
#
# Requiring every section, and closing the status set, exceeds MADR. That is our
# choice, not the standard's. Budgets exist because the failure mode here is not
# a missing document — it is 561 of them.
_MADR_SECTIONS = frozenset(
    {
        "## Context and Problem Statement",
        "## Decision Drivers",
        "## Considered Options",
        "## Decision Outcome",
        "### Consequences",
        "### Confirmation",
        "## More Information",
    }
)

_ADR_SECTIONS: tuple[str, ...] = (
    "## Context and Problem Statement",
    "## Decision Drivers",
    "## Prior art",
    "## Considered Options",
    "## Decision Outcome",
    "### Consequences",
    "### Confirmation",
    "## Improvements on the prior art",
    "## Architecture surface",
    "## Scope and threat delta",
    "## Quality attributes",
    "## Reversibility",
    "## Sad paths",
    "## Test strategy",
    "## Code review checklist",
    "## More Information",
)

# Complete is the requirement. Long is not. A section that needs more room than
# this is describing an implementation, and implementations live in code.
_SECTION_BUDGET: dict[str, int] = {
    "## Context and Problem Statement": 14,
    "## Decision Drivers": 10,
    "## Prior art": 32,
    "## Considered Options": 14,
    "## Decision Outcome": 14,
    "### Consequences": 14,
    "### Confirmation": 12,
    "## Improvements on the prior art": 22,
    "## Architecture surface": 10,
    "## Scope and threat delta": 10,
    "## Quality attributes": 10,
    "## Reversibility": 8,
    "## Sad paths": 34,
    "## Test strategy": 32,
    "## Code review checklist": 14,
    "## More Information": 12,
}

ADR_MAX_LINES = 300

# ADR-000 defines the template, so it must quote the template. It is held to
# every section and every other rule — only the line budgets are lifted.
_TEMPLATE_ADR = "ADR-000-how-we-write-adrs.md"

# Below this, "sad paths" is a gesture rather than an enumeration. Raised from 3
# on 2026-08-02: the real ADRs carry 30 and 21, so a floor of 3 was measuring
# nothing and would have passed a document that had barely looked.
MIN_SAD_PATHS = 8

# One-way doors are the ones worth arguing about before walking through.
_DOOR = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?Door(?:\*\*)?:\s*(one-way|two-way)\s*$", re.MULTILINE)

# An unfilled MADR scaffold must not pass for a decision. Checked after inline
# code is stripped: `{claim_id, command}` is a schema, not an unfilled blank.
_PLACEHOLDER = re.compile(r"\{[a-z][^}\n]*\}|<!--")
_CODE_SPAN = re.compile(r"`[^`]*`")

_TEST_PATH = re.compile(r"tests/[\w/]+\.py")

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
    if parent == "docs/adr":
        return bool(_ADR_NAME.fullmatch(relative.name))
    return False


def _adr_files() -> list[Path]:
    directory = REPO_ROOT / "docs" / "adr"
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("ADR-*.md") if p.is_file())


def _section(text: str, heading: str) -> str | None:
    """The body under a heading, up to the next `## ` or end of file."""

    match = re.search(
        rf"^{re.escape(heading)}\s*$\n(.*?)(?=^#{{2,3}} |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    return None if match is None else match.group(1)


def _enumerated_items(body: str) -> int:
    """Count bullet points and table rows, ignoring table separator lines."""

    count = 0
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            count += 1
        elif stripped.startswith("|") and not set(stripped) <= set("|-: "):
            count += 1
    return count


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


# --- ADRs: no slice without a researched decision ---------------------------
#
# CLAUDE.md requires an ADR before a slice is opened, and requires it to cite
# prior art and enumerate sad paths. A rule an agent can read is a suggestion.


def test_every_adr_declares_a_status() -> None:
    missing = [p.name for p in _adr_files() if _ADR_STATUS.search(p.read_text("utf-8")) is None]
    assert not missing, (
        "ADRs without a '**Status:**' line of proposed | accepted | rejected | "
        f"deprecated | superseded by ADR-NNN: {missing}"
    )


def test_every_adr_has_the_required_sections() -> None:
    """A thin ADR is short. It is not partial."""

    problems: list[str] = []
    for path in _adr_files():
        text = path.read_text(encoding="utf-8")
        absent = [s for s in _ADR_SECTIONS if _section(text, s) is None]
        if absent:
            problems.append(f"{path.name} is missing {absent}")
    assert not problems, "; ".join(problems)


def test_every_adr_cites_a_primary_source() -> None:
    """An ADR with no citation is an opinion. Research first, invent last."""

    uncited: list[str] = []
    for path in _adr_files():
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None or not _CITATION.search(prior_art):
            uncited.append(path.name)
    assert not uncited, (
        f"ADRs whose '## Prior art' cites no source: {uncited}. "
        "Link the spec or the source file the decision was taken from."
    )


def _code_citations(prior_art: str) -> list[str]:
    """Links to a code host, pinned to a revision that cannot move."""

    return [
        url
        for url in _CODE_HOST.findall(prior_art)
        if _PINNED_REVISION.search(url)
    ]


def test_every_adr_cites_working_code_not_only_prose() -> None:
    """A specification says what someone intended. Code says what worked.

    The old rule was one URL of any kind in `## Prior art`, which a link to a
    blog post — or to this repository — satisfied. That made "research first,
    invent last" a suggestion, and this project's whole thesis is that a rule an
    agent can read is a suggestion while a rule compiled into a check is a
    constraint. So the rule is now about code: find the mature implementation
    that already works, pinned so a reviewer can read the same bytes we did.
    """

    problems: list[str] = []
    for path in _adr_files():
        if path.name in _PRE_CODE_RULE_ADRS:
            continue
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None:
            problems.append(f"{path.name}: no '## Prior art' section")
            continue
        pinned = _code_citations(prior_art)
        if len(pinned) < MIN_CODE_CITATIONS:
            unpinned = [
                url for url in _CODE_HOST.findall(prior_art)
                if not _PINNED_REVISION.search(url)
            ]
            detail = f"{len(pinned)} pinned code citation(s), need {MIN_CODE_CITATIONS}"
            if unpinned:
                detail += (
                    f"; {len(unpinned)} link(s) name a code host but no fixed "
                    f"revision, so what was read cannot be re-read: {unpinned[0]}"
                )
            problems.append(f"{path.name}: {detail}")

    assert not problems, (
        "; ".join(problems)
        + ". Cite the implementation that already solves this, at a commit or "
        "tag — not a branch, and not only a spec or an article."
    )


def test_every_code_citation_states_its_licence_and_its_weakness() -> None:
    """We are copying, so both of these are load-bearing.

    The licence decides whether we may copy at all — this repo is MIT, and a
    copyleft implementation pulled into it is a problem nothing else here would
    catch. The weakness is the half of prior art that gets skipped: CLAUDE.md
    has always said "adopting a design without its caveats is how you ship
    decoration", and until now nothing checked it. One of each per cited
    implementation, so neither can be answered once and waved at the rest.
    """

    problems: list[str] = []
    for path in _adr_files():
        if path.name in _PRE_CODE_RULE_ADRS:
            continue
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None:
            continue
        cited = len(_code_citations(prior_art))
        if not cited:
            continue
        licences = len(_LICENCE.findall(prior_art))
        weaknesses = len(_WEAKNESS.findall(prior_art))
        if licences < cited:
            problems.append(
                f"{path.name}: {cited} implementation(s) cited, {licences} "
                "'License:' line(s) — say what each one permits before copying it"
            )
        if weaknesses < cited:
            problems.append(
                f"{path.name}: {cited} implementation(s) cited, {weaknesses} "
                "'Weakness:' line(s) — name what each one gets wrong, or you have "
                "not read it closely enough to copy it"
            )

    assert not problems, "; ".join(problems)


def test_every_adr_enumerates_sad_paths() -> None:
    """The happy path is the part that was never in doubt."""

    thin: list[str] = []
    for path in _adr_files():
        body = _section(path.read_text(encoding="utf-8"), "## Sad paths")
        if body is None or _enumerated_items(body) < MIN_SAD_PATHS:
            thin.append(path.name)
    assert not thin, (
        f"ADRs enumerating fewer than {MIN_SAD_PATHS} sad paths: {thin}. "
        "List what happens when each assumption fails, not only when it holds."
    )


def test_every_open_slice_links_an_existing_adr() -> None:
    """No slice without an ADR — the link is the proof the decision was taken."""

    problems: list[str] = []
    for path in _slice_files(done=False):
        text = path.read_text(encoding="utf-8")
        referenced = _ADR_REF.search(text)
        if referenced is None:
            problems.append(f"{path.name} links no docs/adr/ADR-NNN-*.md")
            continue
        if not (REPO_ROOT / "docs" / "adr" / referenced.group(1)).is_file():
            problems.append(f"{path.name} points at {referenced.group(1)}, which does not exist")
    assert not problems, "; ".join(problems)


def test_adr_sections_appear_in_the_canonical_order() -> None:
    """Same shape every time. A template read in a different order drifts."""

    problems: list[str] = []
    for path in _adr_files():
        text = path.read_text(encoding="utf-8")
        seen = [
            (text.index(f"\n{heading}\n"), heading)
            for heading in _ADR_SECTIONS
            if f"\n{heading}\n" in text
        ]
        ordered = [heading for _, heading in sorted(seen)]
        expected = [h for h in _ADR_SECTIONS if h in ordered]
        if ordered != expected:
            problems.append(f"{path.name}: got {ordered}, expected {expected}")
    assert not problems, "; ".join(problems)


def test_every_adr_section_stays_within_budget() -> None:
    """Complete is the requirement. Long is not."""

    problems: list[str] = []
    for path in _adr_files():
        if path.name == _TEMPLATE_ADR:
            continue
        text = path.read_text(encoding="utf-8")
        for heading, budget in _SECTION_BUDGET.items():
            body = _section(text, heading)
            if body is None:
                continue
            used = len([line for line in body.splitlines() if line.strip()])
            if used > budget:
                problems.append(f"{path.name} '{heading}' is {used} lines, budget {budget}")
    assert not problems, (
        "; ".join(problems)
        + ". Say it shorter, or move the detail into code and cite the file."
    )


def test_no_adr_exceeds_the_total_cap() -> None:
    oversized: list[str] = []
    for path in _adr_files():
        if path.name == _TEMPLATE_ADR:
            continue
        length = len(path.read_text(encoding="utf-8").splitlines())
        if length > ADR_MAX_LINES:
            oversized.append(f"{path.name} ({length} lines)")
    assert not oversized, (
        f"ADRs over the {ADR_MAX_LINES}-line cap: {oversized}. "
        "The docs layer is capped on purpose — this repo once held 561 of these."
    )


def test_every_adr_declares_reversibility() -> None:
    """One-way doors are the ones worth arguing about before walking through."""

    missing: list[str] = []
    for path in _adr_files():
        body = _section(path.read_text(encoding="utf-8"), "## Reversibility")
        if body is None or _DOOR.search(body) is None:
            missing.append(path.name)
    assert not missing, (
        f"ADRs whose '## Reversibility' has no 'Door: one-way|two-way' line: {missing}"
    )


def test_every_adr_test_strategy_names_real_tests() -> None:
    """A strategy that names no test is a plan to write one later."""

    problems: list[str] = []
    for path in _adr_files():
        body = _section(path.read_text(encoding="utf-8"), "## Test strategy")
        if body is None:
            problems.append(f"{path.name} has no '## Test strategy'")
            continue
        named = _TEST_PATH.findall(body)
        if not named:
            problems.append(f"{path.name} names no tests/ path in its test strategy")
            continue
        absent = [p for p in named if not (REPO_ROOT / p).is_file()]
        if absent:
            problems.append(f"{path.name} names tests that do not exist: {absent}")
    assert not problems, "; ".join(problems)


def test_no_adr_ships_an_unfilled_placeholder() -> None:
    """An unfilled MADR scaffold must not pass for a decision."""

    problems: list[str] = []
    for path in _adr_files():
        if path.name == _TEMPLATE_ADR:  # it must quote the blank template
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _PLACEHOLDER.search(_CODE_SPAN.sub("", line)):
                problems.append(f"{path.name}:{number}: {line.strip()!r}")
    assert not problems, (
        f"unfilled template placeholders remain: {problems}. "
        "Fill them in or delete the line — a scaffold is not a decision."
    )
