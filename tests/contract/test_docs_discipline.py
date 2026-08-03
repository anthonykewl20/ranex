"""The docs layer governs itself.

This project previously accumulated 561 architecture documents and zero product
code. `CLAUDE.md` states the cap that prevents a repeat; a rule an agent can read
is a suggestion, so these tests are the constraint.
"""

from __future__ import annotations

import functools
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

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

# Pinned to an immutable revision — a 40-hex commit or a release tag — and never
# to a branch. A link to `main` describes whatever main became, so a reviewer
# cannot read what was actually copied. This repo already binds evidence to a
# subject digest for exactly this reason; research is bound the same way.
#
# The tag form is deliberately narrow: `v?\d[\w.\-]*` also matched `2.x` and
# `24-feature`, which are branch names, and a branch that happens to start with
# a digit is no more fixed than one that starts with a letter. Only a
# dotted-numeric release survives, so the ambiguity a URL cannot resolve — GitHub
# spells tags and branches identically — is settled by refusing the doubtful case.
_PINNED_REVISION = re.compile(
    r"/(?:-/)?(?:blob|tree|raw|src)/(?:[0-9a-f]{40}|v?\d+(?:\.\d+)*)/",
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

# Research starts before the convenient citations: record the code-host searches
# that exposed the candidates, including mature projects deliberately rejected.
_SEARCHED = re.compile(r"^\s*[-*]?\s*(?:\*\*)?Searched(?:\*\*)?:", re.MULTILINE)
_REJECTED = re.compile(r"^\s*[-*]?\s*(?:\*\*)?Rejected(?:\*\*)?:", re.MULTILINE)

# Two, so a single lucky find cannot stand in for looking. Not more, because
# research must be efficient — this is a floor on rigour, not a reading quota.
MIN_CODE_CITATIONS = 2
MIN_REJECTED_CANDIDATES = 2

# Which ADR a prior-art directory belongs to. An ADR vouches for its own copies
# and no one else's.
_ADR_NUMBER = re.compile(r"^(ADR-\d{3})")

# A line that means to be a `Vendored:` declaration and is not one. The strict
# pattern anchors at the line end, so a trailing note — `blob:… (fetched today)`
# — matches nothing, and the entry is then reported as having no vendored file at
# all. That accuses the author of skipping the work when what they did was mistype
# it, which is the same wrong-accusation defect this repo has fixed twice before.
_VENDORED_INTENT = re.compile(r"^\s*[-*]?\s*(?:\*\*)?Vendored(?:\*\*)?:", re.MULTILINE)

# ADRs written before this rule landed on 2026-08-02. They are not retro-fitted:
# rewriting an accepted decision to satisfy a rule it predates would manufacture
# exactly the fake compliance the rule exists to prevent, and ADR-000 decides a
# document format, for which a specification genuinely is the prior art.
# Keyed on content, never on the name. A review called the filename-only version
# a mutable waiver, and it was right: an exemption that travels with a name means
# new text under an old name evades every research rule while the suite stays
# green. Pinned to the bytes each file had when the rule landed, so the moment
# one of them is edited its exemption lapses and the new rule applies to it —
# which is also the nudge toward superseding rather than rewriting.
_PRE_CODE_RULE_ADRS = {
    "ADR-000-how-we-write-adrs.md": "8233d1b1ed63a53c9e14894de8029f358e28f983",
    "ADR-001-claim-command-binding.md": "df6532def4cfd97a67ea7f255214feafda6a81f6",
    "ADR-002-committed-trust-root.md": "8e0e08174c20b922792eb742074acaa9b22eb1bb",
}


def _grandfathered(path: Path) -> bool:
    """Does this ADR predate the code-citation rule, byte for byte?"""

    return _PRE_CODE_RULE_ADRS.get(path.name) == _git_blob_sha(path)


# ADRs accepted before the search record was required, on 2026-08-02. Not
# retro-fitted, for the same reason as the map above: a search recorded after the
# decision it supposedly informed is a reconstruction, and inventing one to turn
# the suite green is precisely the fake compliance this rule exists to prevent.
#
# A separate map rather than a widened one, because the two waivers must expire
# independently — an ADR may satisfy the citation rule and not this one, and
# merging them would let either exemption carry the other. Keyed on content, so
# an edit lapses the exemption and the new rule applies to the new text.
#
# This rule exists because the omission it catches actually happened: a design
# for confinement and audit logging was produced without searching, and `in-toto`,
# `witness` and `landrun` had already solved most of it. The owner caught it.
_PRE_SEARCH_RULE_ADRS = {
    "ADR-000-how-we-write-adrs.md": "8233d1b1ed63a53c9e14894de8029f358e28f983",
    "ADR-001-claim-command-binding.md": "df6532def4cfd97a67ea7f255214feafda6a81f6",
    "ADR-002-committed-trust-root.md": "8e0e08174c20b922792eb742074acaa9b22eb1bb",
    "ADR-003-research-is-fetched-evidence.md": "7cab0069b6e41f4b6ad8042022c0396813b7561e",
    "ADR-004-environment-boundary-for-git-queries.md": "a42a9d149703060b5a095033cd40dac00931fc4f",
    "ADR-005-hermetic-observation.md": "238ca8a0e60a881efcacdd54699d4f9c7f05c8b0",
}


def _search_rule_grandfathered(path: Path) -> bool:
    """Does this ADR predate the search-record rule, byte for byte?"""

    return _PRE_SEARCH_RULE_ADRS.get(path.name) == _git_blob_sha(path)

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
    "## Prior art": 46,
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

_ALLOWED_EXACT = frozenset(
    {"CLAUDE.md", "README.md", "docs/STATE.md", "docs/MAP.md"}
)

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
    # Vendored prior art: third-party source copied in so that what an ADR
    # claims to have read is on disk, plus the NOTICE that makes copying it
    # lawful. Deliberately NOT "anything under prior-art/" — that first version
    # let an agent park arbitrary documents in an ADR's directory and walk
    # straight past the docs cap, which is the 561-file failure this repository
    # already survived once. A markdown file earns its place here only by being
    # a NOTICE, or by being vendored on the word of some ADR.
    if parent.startswith("docs/adr/prior-art/"):
        vendored = _vendored_paths()
        if posix in vendored:
            return True
        # A NOTICE only earns its place beside something it gives notice *for*.
        # Allowing the name anywhere under `prior-art/` left a directory holding
        # nothing but a NOTICE.md: admitted by the cap, and skipped by the
        # licence check, which walks directories that actually vendor something.
        # A file no rule ever looks at is the shape the 561 began as.
        if relative.name == "NOTICE.md":
            return any(claim.startswith(f"{parent}/") for claim in vendored)
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


_VENDORED = re.compile(
    r"^\s*[-*]?\s*(?:\*\*)?Vendored(?:\*\*)?:\s*`?(?P<path>docs/adr/prior-art/\S+?)`?"
    r"\s+blob:(?P<blob>[0-9a-f]{40})\s*$",
    re.MULTILINE,
)


@functools.lru_cache(maxsize=1)
def _vendored_paths() -> frozenset[str]:
    """Every repo-relative path some ADR claims to have vendored.

    What makes a file under `prior-art/` legitimate is that an ADR vouches for
    it. Nothing else in that directory has a reason to exist, so nothing else
    gets past the docs cap.

    Cached: `_is_allowed` asks this once per tracked markdown file, and without
    the cache every one of those re-read every ADR on disk. Safe because a test
    run does not edit the tree it is judging — and if that ever stops being
    true, the cache is the least of it.
    """

    claimed: set[str] = set()
    for path in _adr_files():
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None:
            continue
        claimed.update(relative for relative, _ in _VENDORED.findall(prior_art))
    return frozenset(claimed)


def _inside_repository(relative: str) -> Path | None:
    """Where `relative` lands, or None if it leaves the repository.

    Deliberately local, and the duplication is disclosed rather than hidden.
    `src/ranex/cli/confinement.py` answers this same question for the CLI, and
    the authoring contract would have this reuse it — the first version of this
    file did. But ADR-000's "Architecture surface" states that this checker
    "reads the repo tree; it imports nothing from `src/ranex/`", and contract §1
    makes a repository-local invariant outrank a generic reuse rule. So the
    boundary wins and the rule loses, on the record. If that boundary is ever
    lifted by a superseding ADR, this becomes the import.

    Resolved before it is judged, because the path comes out of prose: a first
    version compared `REPO_ROOT / relative` without resolving and accepted
    `docs/adr/prior-art/../../../../tmp/evil.go`.
    """

    if not relative or Path(relative).is_absolute():
        return None
    landed = (REPO_ROOT / relative).resolve()
    # `is_relative_to` is the documented built-in for this question (3.9+, and
    # this project is on 3.14). Hand-comparing `.parents` is the same answer
    # spelled less clearly, and the spelling is where the off-by-one lives.
    return landed if landed.is_relative_to(REPO_ROOT) else None


# SPDX-ish identifiers. A NOTICE that names a file and nothing else records no
# licence at all, which is the state this check exists to refuse.
_SPDX = re.compile(
    r"\b(?:MIT|ISC|Unlicense|CC0-1\.0|BSD(?:-[23]-Clause)?|Apache(?:-2\.0)?"
    r"|[AL]?GPL-[23]\.0(?:-only|-or-later)?|[AL]?GPL|MPL-2\.0)\b"
)

# Origin: the commit the copy was taken at, or the URL it came from.
_ORIGIN = re.compile(r"[0-9a-f]{40}|https?://\S+")


def _git_blob_sha(path: Path) -> str:
    """Git's own name for these bytes: sha1 of `blob <len>\\0` + content.

    Git's hash rather than a plain sha256, because it is the *same value*
    GitHub reports for that path at that commit — so a reviewer, or a future
    networked verifier, can compare the vendored copy against upstream without
    trusting anything this repository says. A sha256 of arbitrary content ties
    to nothing outside this repo. Taken from leitir's `SourceRef.blob_sha`,
    which pins code evidence the same way.
    """

    body = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()


def _without_git_environment() -> dict[str, str]:
    """The ambient environment with every GIT_* variable removed.

    For the same reason `git()` in `src/ranex/cli/main.py` strips it: an ambient
    GIT_DIR or GIT_INDEX_FILE names a different repository, and every question
    asked here is about THIS one. A relative GIT_DIR bought a fraudulent gate
    PASS before that fix landed. It applies to the self-tests below as well as
    to the checker — a rule that only holds when the developer's shell happens
    to be clean is not a rule.
    """

    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }


def _tracked_by_git(path: Path) -> bool:
    """Is this repo-relative file present in git's index?"""

    # "Tracked" deliberately means present in the index, not only carried by
    # HEAD: `git add` makes a new vendor file visible to reviewers in the
    # proposed change, while HEAD-only would reject it until a commit exists.
    # This does NOT prove it has been reviewed or merged; staging is an input to
    # review, not review itself. Missing git and a non-repository fail closed:
    # skipping this check would let an author manufacture that escape hatch.
    relative = path.relative_to(REPO_ROOT).as_posix()
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "ls-files",
                "--cached",
                "--error-unmatch",
                "-z",
                "--",
                f":(literal){relative}",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=_without_git_environment(),
        )
    except OSError:
        return False
    return completed.returncode == 0


def _prior_art_entries(prior_art: str) -> list[str]:
    """One block per cited implementation: from each citation to the next.

    Counting markers across the whole section was the first defect — two cited
    implementations and two `Vendored:` lines satisfied the count while belonging
    to each other in no way at all. Splitting on top-level bullets was the second:
    a review found a citation indented four spaces did not start a new block, so
    it merged into the entry above and was covered by *its* licence.

    Split on the citations themselves and neither can happen. Formatting stops
    mattering — bullets, sub-bullets, indentation, a table — because the thing an
    entry is *about* is the implementation it names, and the block runs to
    wherever the next one begins. Text before the first citation is preamble and
    cites nothing, so it is skipped rather than judged.
    """

    lines = prior_art.splitlines()
    starts = [i for i, line in enumerate(lines) if _code_citations(line)]
    bounds = starts + [len(lines)]
    return [
        "\n".join(lines[bounds[i] : bounds[i + 1]]) for i in range(len(starts))
    ]


def _notice_entry(body: str, name: str) -> str | None:
    """The NOTICE line naming `name`, or None.

    Whole-token, because `name in body` accepted a NOTICE mentioning `a.txt.gz`
    as naming `a.txt`. The line is returned rather than a boolean so the caller
    can ask what else it records — a filename alone is not a notice.
    """

    pattern = re.compile(rf"(?<![\w.\-]){re.escape(name)}(?![\w.\-])")
    for line in body.splitlines():
        if pattern.search(line):
            return line
    return None


def _pinned_code_url(url: str) -> bool:
    """Does the path, rather than URL decoration, name an immutable revision?"""

    # Reproduced: `.../blob/main/f.py?proof=/blob/<40-hex>/x` (and the same
    # payload in `#fragment`) passed when this expression searched the whole
    # URL. The query and fragment do not select the bytes a reviewer reads;
    # only the path can name the revision, so only it is eligible as evidence.
    return bool(_PINNED_REVISION.search(urlsplit(url).path))


def _code_citations(prior_art: str) -> list[str]:
    """Distinct source files on a code host, pinned to immutable revisions."""

    citations: list[str] = []
    implementations: set[tuple[str, str, str]] = set()
    for url in _CODE_HOST.findall(prior_art):
        parts = urlsplit(url)
        if not _pinned_code_url(url):
            continue
        # Reproduced: the exact pinned URL twice, and one pinned file at #L10
        # and #L20, produced two occurrences and met the two-implementation
        # floor. They are one source file, so deduplicate on its scheme, host,
        # and path. Keep the first spelling: failure messages quote it, and a
        # stable, readable diagnostic matters more than a later line anchor.
        implementation = (
            parts.scheme.lower(),
            (parts.hostname or "").lower(),
            parts.path,
        )
        if implementation not in implementations:
            implementations.add(implementation)
            citations.append(url)
    return citations


def test_code_citations_do_not_count_the_same_pinned_url_twice() -> None:
    """One implementation cited twice cannot satisfy the research floor."""

    url = "https://github.com/o/r/blob/0123456789abcdef0123456789abcdef01234567/f.py"
    prior_art = f"## Prior art\n\n- {url}\n- {url}\n"

    assert len(_code_citations(prior_art)) < MIN_CODE_CITATIONS


def test_vendored_implementation_must_be_tracked_by_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A working-tree-only copy is not evidence a reviewer can obtain."""

    environment = _without_git_environment()
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, env=environment)
    relative = "docs/adr/prior-art/ADR-003/upstream.py"
    vendored = tmp_path / relative
    vendored.parent.mkdir(parents=True)
    vendored.write_text("upstream bytes\n", encoding="utf-8")
    digest = _git_blob_sha(vendored)
    adr = tmp_path / "docs/adr/ADR-003-vendor-evidence.md"
    adr.parent.mkdir(parents=True, exist_ok=True)
    adr.write_text(
        "## Prior art\n\n"
        f"- Vendored: `{relative}` blob:{digest}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    with pytest.raises(AssertionError) as refused:
        test_every_cited_implementation_is_vendored_and_matches_its_digest()
    assert relative in str(refused.value)
    assert "git add" in str(refused.value)

    subprocess.run(
        ["git", "-C", str(tmp_path), "add", relative], check=True, env=environment
    )
    test_every_cited_implementation_is_vendored_and_matches_its_digest()


def test_code_citations_do_not_count_line_fragments_as_implementations() -> None:
    """Two line links into one source file are one implementation."""

    url = "https://github.com/o/r/blob/0123456789abcdef0123456789abcdef01234567/f.py"
    prior_art = f"## Prior art\n\n- {url}#L10\n- {url}#L20\n"

    assert len(_code_citations(prior_art)) < MIN_CODE_CITATIONS


def test_code_citations_count_distinct_pinned_implementations() -> None:
    """The floor remains satisfiable by two different pinned source files."""

    revision = "0123456789abcdef0123456789abcdef01234567"
    prior_art = (
        "## Prior art\n\n"
        f"- https://github.com/o/r/blob/{revision}/one.py\n"
        f"- https://github.com/o/r/blob/{revision}/two.py\n"
    )

    assert len(_code_citations(prior_art)) >= MIN_CODE_CITATIONS


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/o/r/blob/main/f.py?proof=/blob/0123456789abcdef0123456789abcdef01234567/x",
        "https://github.com/o/r/blob/main/f.py#proof=/blob/0123456789abcdef0123456789abcdef01234567/x",
    ],
)
def test_code_citations_do_not_treat_a_query_or_fragment_as_a_revision(
    url: str,
) -> None:
    """Only the path names the bytes a reviewer would read."""

    assert not _code_citations(f"## Prior art\n\n- {url}\n")


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/o/r/blob/0123456789abcdef0123456789abcdef01234567/f.py",
        "https://github.com/o/r/blob/v1.2.3/f.py",
    ],
)
def test_code_citations_keep_honestly_pinned_commits_and_tags(url: str) -> None:
    """Path-based pinning continues to accept immutable commits and tags."""

    assert _code_citations(f"## Prior art\n\n- {url}\n") == [url]


def _rejected_candidate_blocks(prior_art: str) -> list[str]:
    """One block per rejected candidate, from its marker to the next entry.

    Reasoning is allowed to wrap, so the line carrying `Rejected:` cannot be the
    whole candidate. Like `_prior_art_entries`, split on the things that give an
    entry its meaning instead of on Markdown layout: the next `Rejected:` marker
    or the next pinned code citation starts another entry. A citation on the
    marker's own line belongs to that rejected candidate, even when it happens
    to be pinned.
    """

    rejected = list(_REJECTED.finditer(prior_art))
    citation_starts = [
        citation.start()
        for citation in _CODE_HOST.finditer(prior_art)
        if _pinned_code_url(citation.group())
    ]
    blocks: list[str] = []
    for index, marker in enumerate(rejected):
        next_rejected = (
            rejected[index + 1].start()
            if index + 1 < len(rejected)
            else len(prior_art)
        )
        marker_line_end = prior_art.find("\n", marker.end())
        if marker_line_end == -1:
            marker_line_end = len(prior_art)
        next_citation = next(
            (
                start
                for start in citation_starts
                if start >= marker_line_end and start > marker.start()
            ),
            len(prior_art),
        )
        blocks.append(prior_art[marker.start() : min(next_rejected, next_citation)])
    return blocks


def test_every_adr_records_the_prior_art_search_and_rejected_candidates() -> None:
    """A citation records what was adopted; this records the alternatives weighed."""

    problems: list[str] = []
    for path in _adr_files():
        if _search_rule_grandfathered(path):
            continue
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None:
            problems.append(f"{path.name}: no '## Prior art' section")
            continue
        # This verifies that a search was RECORDED, not that one was PERFORMED:
        # an offline checker cannot observe the author running a code-host query,
        # just as Vendored evidence proves bytes were obtained and not where from.
        if not _SEARCHED.search(prior_art):
            problems.append(
                f"{path.name}: no 'Searched:' line. Record the code-host query "
                "and the host or tool used before choosing citations"
            )
        rejected = _rejected_candidate_blocks(prior_art)
        if len(rejected) < MIN_REJECTED_CANDIDATES:
            problems.append(
                f"{path.name}: {len(rejected)} 'Rejected:' candidate(s), need "
                f"{MIN_REJECTED_CANDIDATES}. Record mature code-host candidates "
                "you deliberately did not adopt"
            )
        for entry in rejected:
            if not _CODE_HOST.search(entry):
                problems.append(
                    f"{path.name}: 'Rejected:' entry has no code-host URL. Link "
                    "the candidate you weighed and say why it was not adopted"
                )
                continue
            reasoning = _CODE_HOST.sub("", entry).split(":", 1)[-1].strip()
            if len(reasoning) < 30:
                problems.append(
                    f"{path.name}: 'Rejected:' entry has only {len(reasoning)} "
                    "non-URL character(s), need 30. Say why the candidate was "
                    "not adopted, not merely that it exists"
                )

    assert not problems, "; ".join(problems)


def _search_rule_fixture(path: Path, prior_art: str) -> Path:
    """Build the smallest ADR body needed to exercise the search-record rule."""

    path.write_text(f"## Prior art\n\n{prior_art}\n", encoding="utf-8")
    return path


def test_adr_without_a_searched_line_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An author must record the code-host search, not just chosen citations."""

    adr = _search_rule_fixture(
        tmp_path / "ADR-999-search-required.md",
        "- Rejected: https://github.com/example/one This candidate lacks the needed "
        "offline verification boundary.\n"
        "- Rejected: https://gitlab.com/example/two This candidate couples policy "
        "decisions to a provider adapter.",
    )
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    with pytest.raises(AssertionError, match="Searched:"):
        test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_adr_with_one_rejected_candidate_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One rejected project cannot show that the whole problem was searched."""

    adr = _search_rule_fixture(
        tmp_path / "ADR-999-two-rejections.md",
        "- Searched: GitHub code search for offline evidence verification\n"
        "- Rejected: https://github.com/example/one This candidate lacks the needed "
        "offline verification boundary.",
    )
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    with pytest.raises(AssertionError, match="need 2"):
        test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_rejected_candidate_bare_url_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A candidate link without reasoning does not show it was weighed."""

    adr = _search_rule_fixture(
        tmp_path / "ADR-999-rejection-reasoning.md",
        "- Searched: GitHub code search for offline evidence verification\n"
        "- Rejected: https://github.com/example/one\n"
        "- Rejected: https://gitlab.com/example/two This candidate couples policy "
        "decisions to a provider adapter.",
    )
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    with pytest.raises(AssertionError, match="need 30"):
        test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_rejected_candidate_with_wrapped_reasoning_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rejection's explanation may continue below the marker line."""

    adr = _search_rule_fixture(
        tmp_path / "ADR-999-wrapped-rejection.md",
        "- Searched: GitHub code search for offline evidence verification\n"
        "- Rejected: https://github.com/example/one\n"
        "  This candidate lacks the required offline verification boundary,\n"
        "  so its provider cannot make the policy decision safely.\n"
        "- Rejected: https://gitlab.com/example/two This candidate couples policy "
        "decisions to a provider adapter.",
    )
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_rejected_candidate_block_stops_at_the_next_code_citation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prose under a later citation cannot become a bare rejection's reasoning."""

    revision = "0123456789abcdef0123456789abcdef01234567"
    adr = _search_rule_fixture(
        tmp_path / "ADR-999-rejection-boundary.md",
        "- Searched: GitHub code search for offline evidence verification\n"
        "- Rejected: https://github.com/example/one\n"
        f"- https://github.com/example/adopted/blob/{revision}/source.py\n"
        "  This unrelated prose describes the adopted implementation in detail.\n"
        "- Rejected: https://gitlab.com/example/two This candidate couples policy "
        "decisions to a provider adapter.",
    )
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    with pytest.raises(AssertionError, match="need 30"):
        test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_rejected_candidate_with_unpinned_url_and_reasoning_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rejected candidates need reasoning and a code-host URL, not a pinned revision."""

    adr = _search_rule_fixture(
        tmp_path / "ADR-999-unpinned-rejection.md",
        "- Searched: GitHub code search for offline evidence verification\n"
        "- Rejected: https://github.com/example/one This candidate lacks the needed "
        "offline verification boundary.\n"
        "- Rejected: https://gitlab.com/example/two This candidate couples policy "
        "decisions to a provider adapter.",
    )
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_grandfathered_adr_passes_the_search_rule_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The historical waiver applies only to the ADR bytes present when it landed."""

    name = next(iter(_PRE_SEARCH_RULE_ADRS))
    adr = REPO_ROOT / "docs" / "adr" / name
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    test_every_adr_records_the_prior_art_search_and_rejected_candidates()


def test_changed_grandfathered_adr_is_not_exempt_from_the_search_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Changing grandfathered content lapses its waiver instead of carrying it forward."""

    name = next(iter(_PRE_SEARCH_RULE_ADRS))
    source = REPO_ROOT / "docs" / "adr" / name
    adr = tmp_path / name
    adr.write_text(source.read_text(encoding="utf-8") + "\nChanged bytes.\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "_adr_files", lambda: [adr])

    with pytest.raises(AssertionError, match="Searched:"):
        test_every_adr_records_the_prior_art_search_and_rejected_candidates()


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
        if _grandfathered(path):
            continue
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None:
            problems.append(f"{path.name}: no '## Prior art' section")
            continue
        pinned = _code_citations(prior_art)
        if len(pinned) < MIN_CODE_CITATIONS:
            unpinned = [
                url for url in _CODE_HOST.findall(prior_art)
                if not _pinned_code_url(url)
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
        if _grandfathered(path):
            continue
        prior_art = _section(path.read_text(encoding="utf-8"), "## Prior art")
        if prior_art is None:
            continue
        for entry in _prior_art_entries(prior_art):
            # Counted, not merely present: a single line can carry two links, and
            # one licence answering for both is the same pooling defect one
            # scale down. `_code_citations` deduplicates one source file cited
            # twice, so that file needs one licence and one weakness, not two:
            # one implementation, one licence, rather than a relaxed count.
            cited = _code_citations(entry)
            if len(_LICENCE.findall(entry)) < len(cited):
                problems.append(
                    f"{path.name}: the entry citing {cited[0]} states no "
                    "'License:' — say what it permits before copying it"
                )
            if len(_WEAKNESS.findall(entry)) < len(cited):
                problems.append(
                    f"{path.name}: the entry citing {cited[0]} states no "
                    "'Weakness:' — name what it gets wrong, or you have not read "
                    "it closely enough to copy it"
                )

    assert not problems, "; ".join(problems)


def test_every_cited_implementation_is_vendored_and_matches_its_digest() -> None:
    """The cited code must be on disk, and be the bytes the ADR says it is.

    Pinning a permalink checks a *shape*. An agent can invent a well-formed
    commit SHA and a confident weakness without opening a browser — reproduced
    against this very checker before this test existed. You cannot, however,
    produce a file you never fetched.

    **State plainly what this proves and what it does not.** It proves the ADR
    is internally consistent and that some real bytes were obtained: it catches
    the agent that cited from memory, which is the failure that actually
    happens. It does NOT prove those bytes came from the cited URL — an agent
    determined to lie can vendor a file it wrote itself and record its hash. The
    trust boundary moved from "trust the citation" to "trust the fetch", and
    closing the rest needs a second, independent fetch of the cited URL, which
    a hermetic suite with no network cannot do. Bazel's `http_archive` is the
    model: it verifies the hash of *what it downloaded* before using it. Until
    a fetching verifier exists, this is lint with teeth and not proof, and it
    must not be described as more.

    The blob hash is git's, so a human can check it against GitHub by eye.
    """

    problems: list[str] = []
    for path in _adr_files():
        if _grandfathered(path):
            continue
        text = path.read_text(encoding="utf-8")
        prior_art = _section(text, "## Prior art")
        if prior_art is None:
            continue
        # Per entry, so a `Vendored:` line answers for the citation it sits
        # beside. Counting across the section let two vendored files satisfy two
        # citations they had nothing to do with.
        for entry in _prior_art_entries(prior_art):
            cited = _code_citations(entry)
            if len(_VENDORED.findall(entry)) < len(cited):
                problems.append(
                    f"{path.name}: the entry citing {cited[0]} has no "
                    "'Vendored:' line. Fetch that file at that commit into "
                    "docs/adr/prior-art/ and record `<path> blob:<40-hex>`"
                )

        # An ADR vendors into its own directory, and each citation gets its own
        # file. Without those two rules the whole check was hollow: a review
        # reproduced two citations both naming `.../ADR-003/NOTICE.md` as their
        # source — the notice check skips NOTICE.md and skips directories holding
        # nothing else, so every rule passed with no code fetched at all. A
        # vendored file must therefore be a source file, distinct, and under the
        # directory belonging to the ADR that claims it.
        number = _ADR_NUMBER.match(path.name)
        owner = (
            (REPO_ROOT / "docs" / "adr" / "prior-art" / number.group(1)).resolve()
            if number
            else None
        )
        # Keyed on the *resolved* file, never on the string. A review found
        # `ADR-003/source.py` and `ADR-003/missing/../source.py` are two strings
        # and one file, so one fetch satisfied two citations — the hollow
        # evidence this check exists to refuse, spelled differently. Everything
        # below judges where the path lands, so an alias and a symlink both
        # collapse onto the file they name.
        claimed: set[Path] = set()
        contents: set[str] = set()

        # Named before it is counted. A malformed declaration must say so rather
        # than vanish and leave the entry looking unvendored.
        intended = len(_VENDORED_INTENT.findall(prior_art))
        parsed = len(_VENDORED.findall(prior_art))
        if intended > parsed:
            problems.append(
                f"{path.name}: {intended - parsed} line(s) begin 'Vendored:' and "
                "do not parse. The form is `<path> blob:<40-hex>` and nothing "
                "after it — a trailing note makes the whole line invisible"
            )

        for relative, recorded in _VENDORED.findall(prior_art):
            # Confined before it is opened. The path comes out of prose, and an
            # unresolved join accepts `../../..`: a vendored file landing outside
            # the tree is not committed and not reviewable, which is the point.
            local = _inside_repository(relative)
            if local is None:
                problems.append(
                    f"{path.name}: vendored path {relative} does not stay inside "
                    "the repository, so it is not committed evidence"
                )
                continue
            if local.name == "NOTICE.md":
                problems.append(
                    f"{path.name}: {relative} is a notice, not a fetched "
                    "implementation; vendoring it proves nothing was obtained"
                )
                continue
            if owner is not None and owner not in local.parents:
                problems.append(
                    f"{path.name}: {relative} lands outside {owner.name}/, so "
                    "this ADR is vouching for a file it does not own"
                )
                continue
            if local in claimed:
                problems.append(
                    f"{path.name}: {relative} resolves to a file already vendored "
                    "for another citation; one fetched file cannot stand in for two"
                )
                continue
            claimed.add(local)
            if not local.is_file():
                problems.append(
                    f"{path.name}: vendored file {relative} is not on disk, so "
                    "nothing was actually fetched"
                )
                continue
            if not _tracked_by_git(local):
                problems.append(
                    f"{path.name}: vendored file {relative} is not tracked by "
                    f"git; run `git add {relative}` so reviewers can obtain it"
                )
                continue
            actual = _git_blob_sha(local)
            if actual != recorded:
                problems.append(
                    f"{path.name}: {relative} and the ADR disagree — the file's "
                    f"blob is {actual}, the ADR records {recorded}"
                )
                continue
            # Distinct *content*, not merely distinct paths. Refusing the name
            # `NOTICE.md` and deduplicating resolved paths still let the notice's
            # own bytes be copied — or hard-linked — under two source names and
            # recorded twice: two citations, two files, one text, nothing
            # fetched. A review reproduced it end to end, clone-stable. Two
            # implementations that are byte-identical are one implementation.
            if actual in contents:
                problems.append(
                    f"{path.name}: {relative} is byte-identical to another file "
                    "vendored here; two citations cannot rest on one text"
                )
                continue
            contents.add(actual)
            notice = local.parent / "NOTICE.md"
            if notice.is_file() and _git_blob_sha(notice) == actual:
                problems.append(
                    f"{path.name}: {relative} holds the notice's own bytes under "
                    "a source name; the notice is not an implementation"
                )

    assert not problems, "; ".join(problems)


def test_vendored_prior_art_carries_its_notice() -> None:
    """Copying third-party source is a licensing act, not a filing decision.

    Every permissive licence this project can accept — MIT, BSD, Apache-2.0 —
    requires the copyright notice and licence text to travel with the copy, and
    Apache-2.0 additionally requires any NOTICE to be preserved. A GPL file
    vendored into an MIT repository is worse than untidy: it changes what this
    repository may be distributed under. None of that is visible to any other
    check here, and no test elsewhere in this project would ever catch it.

    One `NOTICE.md` per ADR's prior-art directory, naming each vendored file's
    origin, commit and licence. Enforced because an unenforced licence rule is
    the kind that is remembered right up until the moment it matters.
    """

    root = REPO_ROOT / "docs" / "adr" / "prior-art"
    if not root.is_dir():
        return

    problems: list[str] = []
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
        # Recursive, because `iterdir` saw only the top level: a claimed path
        # like `ADR-003/src/source.py` left this list empty, the directory was
        # skipped, and third-party code shipped with no origin and no licence
        # recorded anywhere. One notice per ADR covers everything beneath it.
        vendored = [
            p for p in directory.rglob("*")
            if p.is_file() and p.name != "NOTICE.md"
        ]
        if not vendored:
            continue
        notice = directory / "NOTICE.md"
        if not notice.is_file():
            problems.append(
                f"{directory.relative_to(REPO_ROOT)} vendors "
                f"{len(vendored)} file(s) and carries no NOTICE.md"
            )
            continue
        body = notice.read_text(encoding="utf-8")
        where = (directory / "NOTICE.md").relative_to(REPO_ROOT)
        # Named by path within the ADR's directory, not by bare filename: two
        # nested sources can share a name, and then one entry would answer for
        # both. For a flat copy this is just the filename, as before.
        for copied in sorted(
            p.relative_to(directory).as_posix() for p in vendored
        ):
            # Whole-token, not substring: `a.txt in "see a.txt.gz"` was True, so
            # a NOTICE naming a different file counted as naming this one.
            entry = _notice_entry(body, copied)
            if entry is None:
                problems.append(f"{where} does not name {copied}")
                continue
            # Naming the file was the whole test, and a bare filename records no
            # licence and no provenance — exactly the evidence the rule exists to
            # keep. The line must say where the copy came from and what it
            # permits, or it is a filing note wearing a NOTICE's name.
            if not _ORIGIN.search(entry):
                problems.append(
                    f"{where}: the entry for {copied} records no origin — give "
                    "the URL or the commit it was taken at"
                )
            if not _SPDX.search(entry):
                problems.append(
                    f"{where}: the entry for {copied} names no licence, so "
                    "nothing here says we are allowed to have copied it"
                )

    assert not problems, "; ".join(problems)


def test_nothing_sits_in_prior_art_that_no_adr_claims() -> None:
    """Vendor what you cite, and cite what you vendor — both directions.

    The other checks run outward from the ADR: every citation must name a file.
    Nothing ran inward, so a file could sit under `prior-art/` that no ADR
    vouches for — copied third-party source in the tree with no decision behind
    it, no licence recorded, and nothing that would ever look at it again.
    """

    root = REPO_ROOT / "docs" / "adr" / "prior-art"
    if not root.is_dir():
        return

    claimed = _vendored_paths()
    problems = [
        str(found.relative_to(REPO_ROOT))
        for found in sorted(root.rglob("*"))
        if found.is_file()
        and found.name != "NOTICE.md"
        and str(found.relative_to(REPO_ROOT)) not in claimed
    ]
    assert not problems, (
        f"vendored files no ADR claims: {problems}. Cite them in a "
        "`Vendored:` line, or delete them — third-party source with no decision "
        "behind it is exactly what the docs cap exists to keep out."
    )


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
