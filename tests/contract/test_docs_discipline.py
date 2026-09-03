"""The docs layer governs itself.

This project previously accumulated 561 architecture documents and zero product
code. `CLAUDE.md` states the cap that prevents a repeat; a rule an agent can read
is a suggestion, so these tests are the constraint.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import subprocess
import sys
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
    ".worktrees",
    "legacy",
}

_SLICE_NAME = re.compile(r"^SLICE-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_STATUS = re.compile(r"^\*\*Status:\*\*\s+(open|blocked|done)\s*$", re.MULTILINE)

_ADR_NAME = re.compile(r"^ADR-\d{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
_ADR_STATUS = re.compile(
    r"^\*\*Status:\*\*\s+(proposed|accepted|rejected|deprecated"
    r"|superseded by ADR-\d{3})\s*$",
    re.MULTILINE,
)
_ADR_REF = re.compile(r"docs/adr/(ADR-\d{3}-[a-z0-9-]+\.md)")
ADR_MAX_LINES = 300

# An unfilled MADR scaffold must not pass for a decision. Checked after inline
# code is stripped: `{claim_id, command}` is a schema, not an unfilled blank.
_PLACEHOLDER = re.compile(r"\{[a-z][^}\n]*\}|<!--")
_CODE_SPAN = re.compile(r"`[^`]*`")


# AGENTS.md is the root-level agent-conduct rules — the harness-neutral twin
# of CLAUDE.md's conduct section. Admitted by owner direction 2026-08-17: it
# is an instructions file like CLAUDE.md, not a report, and the cap exists to
# stop report bloat, not to forbid agent instructions.
_ALLOWED_EXACT = frozenset(
    {
        "AGENTS.md",
        "CLAUDE.md",
        "README.md",
        "docs/MAP.md",
        "docs/STATE.md",
    }
)

STATE_MAX_LINES = 50

# --- pipeline skills: a closed, capped shelf ---------------------------------
#
# The shelf carries the one allowed skill. Its set is closed and named here, so
# adding or renaming a skill is a deliberate edit to this contract test — never
# a place to park documents. A count cap
# alone ("at most N skills") would admit `architecture-notes` and
# `release-history` as skills numbers 7 and 8, which is the 561-file failure
# restarting in a new costume; a named set admits nothing it does not name.
_PIPELINE_SKILLS = (
    "idea-refine",
)

# --- dogfood loop documents: a named, closed set ------------------------------
#
# tools/dogfood is operator tooling, not reports; these four files are the
# loop's interface (README: how to run it; FINDINGS/AUTOFIX: the finding and
# self-fix protocols; site/INTEGRATION.md: how the rendered site is produced).
# Named exactly, so nothing else under tools/ is admitted by the cap — the
# same closed-set discipline as the skills shelf above.
_DOGFOOD_DOCS = frozenset(
    {
        "tools/dogfood/README.md",
        "tools/dogfood/FINDINGS.md",
        "tools/dogfood/AUTOFIX.md",
        "tools/dogfood/site/INTEGRATION.md",
        # The release-triggered two-arm OSS benchmark's interface doc —
        # admitted deliberately (same conscious-extension mechanism as the
        # four above): it is the contract for how real VulcanBench results
        # are produced and consumed, not a report.
        "tools/dogfood/oss_bench/README.md",
    }
)

# Two caps, because each closes a hole the other leaves. Lines, because a skill
# is instructions and not a handbook; bytes, because a line cap alone admits
# one enormous line.
SKILL_MAX_LINES = 150
SKILL_MAX_BYTES = 10_000

# Anchored at the first byte. A frontmatter block matched anywhere in the file
# would accept a decoy inside a code fence halfway down an arbitrary document.
_SKILL_FRONTMATTER = re.compile(
    r"\A---\nname: (?P<name>[a-z0-9]+(?:-[a-z0-9]+)*)\n"
    r"description: (?P<description>[^\n]+)\n---\n"
)


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
    if posix in _DOGFOOD_DOCS:
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
    # Pipeline skills: exactly `.claude/skills/<named-skill>/SKILL.md`, where
    # the name comes from the closed set above. Nothing else under .claude/
    # is a document this repository admits.
    parts = relative.parts
    if (
        len(parts) == 4
        and parts[0] == ".claude"
        and parts[1] == "skills"
        and parts[2] in _PIPELINE_SKILLS
        and parts[3] == "SKILL.md"
    ):
        return True
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
    assert not missing, (
        "slices without a '**Status:** open|blocked|done' line: " f"{missing}"
    )


def test_blocked_slice_does_not_consume_the_single_open_slot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A named dependency pauses work without pretending that it is done."""

    blocked = tmp_path / "SLICE-998-blocked.md"
    blocked.write_text("# blocked\n\n**Status:** blocked\n", encoding="utf-8")
    active = tmp_path / "SLICE-999-active.md"
    active.write_text("# active\n\n**Status:** open\n", encoding="utf-8")
    monkeypatch.setattr(
        sys.modules[__name__], "_slice_files", lambda *, done: [] if done else [blocked, active]
    )

    test_at_most_one_slice_is_open()


def test_unknown_slice_status_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Adding ``blocked`` does not turn status into an open vocabulary."""

    unknown = tmp_path / "SLICE-999-paused.md"
    unknown.write_text("# paused\n\n**Status:** paused\n", encoding="utf-8")
    monkeypatch.setattr(
        sys.modules[__name__], "_slice_files", lambda *, done: [] if done else [unknown]
    )

    with pytest.raises(AssertionError, match=r"open\|blocked\|done"):
        test_every_slice_declares_a_status(False)


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


def test_open_slice_adr_links_resolve() -> None:
    """ADRs are optional, but every ADR path a slice names must resolve."""

    problems: list[str] = []
    for path in _slice_files(done=False):
        for referenced in _ADR_REF.findall(path.read_text(encoding="utf-8")):
            if not (REPO_ROOT / "docs" / "adr" / referenced).is_file():
                problems.append(f"{path.name} points at {referenced}, which does not exist")
    assert not problems, "; ".join(problems)


def test_no_adr_exceeds_the_total_cap() -> None:
    oversized: list[str] = []
    for path in _adr_files():
        if path.name == "ADR-000-how-we-write-adrs.md":
            continue
        length = len(path.read_text(encoding="utf-8").splitlines())
        if length > ADR_MAX_LINES:
            oversized.append(f"{path.name} ({length} lines)")
    assert not oversized, (
        f"ADRs over the {ADR_MAX_LINES}-line cap: {oversized}. "
        "The docs layer is capped on purpose — this repo once held 561 of these."
    )


def test_no_adr_ships_an_unfilled_placeholder() -> None:
    """An unfilled MADR scaffold must not pass for a decision."""

    problems: list[str] = []
    for path in _adr_files():
        if path.name == "ADR-000-how-we-write-adrs.md":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _PLACEHOLDER.search(_CODE_SPAN.sub("", line)):
                problems.append(f"{path.name}:{number}: {line.strip()!r}")
    assert not problems, (
        f"unfilled template placeholders remain: {problems}. "
        "Fill them in or delete the line — a scaffold is not a decision."
    )


# --- Durability slices: a green, digest-bound PROTOTYPE exit record ----------
#
# ADR-015 (durable execution) is prototyped red-first in disposable harness
# worktrees; SLICE-011 consolidates the five per-claim records into one
# digest-bound exit record committed to THIS repo. ADR-015's Confirmation
# refuses a durability PRODUCTION slice (SLICE-012+) unless that PROTOTYPE record
# is green for every claim it names. A rule an agent can read is a suggestion, so
# the refusal is compiled here.
#
# The prototype record is resolved independently of which slice happens to be
# open: the prototype slice is the ADR-015-linked slice that OWNS the exit record
# (production slices carry none), searched in both docs/slices/ and
# docs/slices/done/ — because SLICE-011 is archived once it closes, and the gate
# must keep working in the post-prototype world that is the only one it will ever
# actually run in. Deriving the record from the active slice was wrong: it gated
# each slice by a record of its own, so a production slice (which owns none) was
# refused forever while the green prototype record sat unconsulted beside it.
_DURABILITY_ADR_PREFIX = "ADR-015-"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _references_durability_adr(slice_text: str) -> bool:
    """Does this slice link the durable-execution decision (ADR-015)?"""

    return any(
        name.startswith(_DURABILITY_ADR_PREFIX) for name in _ADR_REF.findall(slice_text)
    )


def _durability_slices() -> list[Path]:
    """Every slice linking ADR-015, open or archived.

    The prototype (SLICE-011) is filed into docs/slices/done/ once it closes;
    production slices open in docs/slices/. The gate must see both, or it goes
    blind the moment the prototype is archived — which is the only state it ever
    actually runs in.
    """

    found: list[Path] = []
    for done in (False, True):
        for path in _slice_files(done=done):
            if _references_durability_adr(path.read_text(encoding="utf-8")):
                found.append(path)
    return found


def _exit_record_for(slice_path: Path) -> Path | None:
    """The exit record belonging to this slice's stem, in either slice directory.

    Archival should carry the record into docs/slices/done/ alongside the slice;
    if it ever moves only the .md, the record is still found by stemming the slice
    and looking in both places.
    """

    record_name = slice_path.with_suffix(".exit-record.json").name
    for directory in (
        REPO_ROOT / "docs" / "slices",
        REPO_ROOT / "docs" / "slices" / "done",
    ):
        candidate = directory / record_name
        if candidate.is_file():
            return candidate
    return None


def _sha256_digests_within(obj: object) -> list[str]:
    """Every 64-hex value sitting at a key whose name means 'sha256 digest'.

    The exit record binds evidence in more than one shape: a list of artifact
    dicts each carrying `sha256` (claims 1-3), a dict of paths each carrying
    `sha256` (claim 4), and fixture entries carrying `digest_sha256` (claim 5).
    What is uniform is the intent — a field whose name carries 'sha256' and whose
    value is 64 hex digits is a digest binding. Collecting them all means the gate
    does not depend on one record's spelling, and survives the record's author
    renaming a key.
    """

    digests: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            if (
                isinstance(key, str)
                and "sha256" in key.lower()
                and isinstance(value, str)
                and _HEX64.match(value)
            ):
                digests.append(value)
            digests.extend(_sha256_digests_within(value))
    elif isinstance(obj, list):
        for item in obj:
            digests.extend(_sha256_digests_within(item))
    return digests


def _record_where(record_path: Path) -> str:
    return (
        record_path.relative_to(REPO_ROOT).as_posix()
        if record_path.is_relative_to(REPO_ROOT)
        else record_path.name
    )


def _validate_durability_record(record_path: Path) -> list[str]:
    """Refusal reasons for one exit record's content, or [] if it holds.

    The record (assumed to exist) must parse, declare status GREEN, name at least
    one claim, and bind every named claim by at least one sha256 digest.
    """

    where = _record_where(record_path)
    try:
        data = json.loads(record_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return [f"{where}: exit record is not valid JSON ({exc})"]
    if not isinstance(data, dict):
        return [f"{where}: exit record root is not a JSON object"]
    problems: list[str] = []
    if data.get("status") != "GREEN":
        problems.append(
            f"{where}: status is {data.get('status')!r}; a durability slice needs a "
            "GREEN record before any production slice may open."
        )
    claims = data.get("claims")
    if not isinstance(claims, list) or not claims:
        problems.append(
            f"{where}: declares no claims; a green record must bind every claim it names."
        )
        return problems
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        number = claim.get("claim", "?")
        embedded = claim.get("embedded")
        # A claim that declares a status at all must declare GREEN. Claims that
        # say nothing (the record shapes vary) are covered by the top-level status.
        if isinstance(embedded, dict) and embedded.get("status") not in (None, "GREEN"):
            problems.append(
                f"{where}: claim {number} status is {embedded.get('status')!r}; "
                "every named claim must be GREEN."
            )
        if not _sha256_digests_within(claim):
            problems.append(
                f"{where}: claim {number} binds no artifact by sha256; the record "
                "must digest-bind the evidence it claims."
            )
    return problems


def _durability_record_problems() -> list[str]:
    """Refusal reasons across every durability slice, or [] if they all hold.

    The prototype slice — the ADR-015-linked slice that owns the exit record —
    must itself carry a green, digest-bound record. A durability PRODUCTION slice
    (one that links ADR-015 but owns no record) is refused unless a green,
    digest-bound prototype record is on disk. The prototype is the authority;
    production slices are gated BY it, never by records of their own.
    """

    problems: list[str] = []
    prototype_records: list[Path] = []
    production: list[Path] = []
    for slice_path in _durability_slices():
        record = _exit_record_for(slice_path)
        if record is not None:
            prototype_records.append(record)
        else:
            production.append(slice_path)

    green_records: list[Path] = []
    for record in prototype_records:
        record_problems = _validate_durability_record(record)
        if record_problems:
            problems.extend(record_problems)
        else:
            green_records.append(record)

    # A production slice carries no record of its own; it is gated BY the
    # prototype record, so it is refused unless some prototype record is green.
    if production and not green_records:
        names = ", ".join(sorted(p.name for p in production))
        problems.append(
            f"{names}: link ADR-015 (durable execution) but no green, digest-bound "
            "PROTOTYPE record was found in docs/slices/ or docs/slices/done/. A "
            "durability production slice is gated BY the ADR-015 prototype record "
            "(docs/slices/<prototype-stem>.exit-record.json), not by a record of its own."
        )
    return problems


def test_durability_production_slice_requires_green_digest_bound_record() -> None:
    """A durability production slice is refused unless the PROTOTYPE record is green and digest-bound.

    ADR-015's Confirmation compiles this refusal: a durability production slice
    (SLICE-012+) cannot open unless the prototype exit record — digest-bound, and
    green for every claim it names — is on disk. That record belongs to the
    PROTOTYPE (the ADR-015-linked slice that owns it), resolved in docs/slices/
    or docs/slices/done/ because the prototype is archived with SLICE-011 once it
    closes. Production slices carry no record of their own; they are gated BY the
    prototype record. The prototype slice itself must still own a green,
    digest-bound record.

    DO NOT OVERCLAIM WHAT THIS GATE DOES. The artifact digests bind to files in
    disposable harness worktrees in a DIFFERENT repository that is meant to be
    deleted. A gate running in the kernel repo can verify this record is present,
    well-formed, green and digest-bound; it CANNOT re-verify the bytes, because
    that tree is meant to be deleted. Proving the record carries digests shows
    only that bytes were recorded and bound — not that the runs happened, and not
    that the bytes came from where the record says. The supervisor re-runs
    recorded per claim are the load-bearing evidence, and they too were
    observations at a point in time. This is lint with teeth, not proof, and it
    must not be described as more. (ADR-003 accepts the same limit for vendored
    prior art.)
    """

    problems = _durability_record_problems()
    assert not problems, (
        "durability slices whose ADR-015 exit record is missing, not green, or not "
        "digest-bound: " + "; ".join(problems) + ". "
        "NOTE: this gate verifies the record is present, well-formed, GREEN and "
        "digest-bound only. It cannot re-verify the artifact bytes: they live in "
        "disposable harness worktrees in a different repository that is meant to "
        "be deleted, so it proves only that bytes were recorded and bound, not "
        "that the runs happened or that the bytes came from where the record says."
    )


# --- fixtures: synthetic slices + records, none touching real docs -----------

_PROTOTYPE_SLICE = "SLICE-011-durable-execution-prototype.md"
_PRODUCTION_SLICE = "SLICE-012-durable-watchdog.md"
_GREEN_PROTOTYPE_CLAIMS = [
    {
        "claim": 1,
        "embedded": {"status": "GREEN"},
        "source_record": {"sha256": "a" * 64},
        "artifacts": [{"path": "packages/core/src/runner.ts", "sha256": "b" * 64}],
    }
]


def _write_slice(
    tmp_path: Path, name: str, *, in_done: bool = False, references_adr: bool = True
) -> Path:
    directory = tmp_path / "docs" / "slices" / ("done" if in_done else "")
    directory.mkdir(parents=True, exist_ok=True)
    slice_path = directory / name
    adr_line = (
        "**ADR:** `docs/adr/ADR-015-durable-execution-watchdog-first.md`\n"
        if references_adr
        else ""
    )
    slice_path.write_text(
        f"# {name[:-3]}\n\n**Status:** open\n\n{adr_line}\n", encoding="utf-8"
    )
    return slice_path


def _write_prototype(tmp_path: Path, *, in_done: bool = False) -> Path:
    return _write_slice(tmp_path, _PROTOTYPE_SLICE, in_done=in_done)


def _write_production(tmp_path: Path) -> Path:
    return _write_slice(tmp_path, _PRODUCTION_SLICE)


def _write_exit_record(
    slice_path: Path, *, status: str, claims: list[object]
) -> Path:
    record = slice_path.with_suffix(".exit-record.json")
    record.write_text(json.dumps({"status": status, "claims": claims}), encoding="utf-8")
    return record


def _point_gate_at(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    def fake_slice_files(done: bool) -> list[Path]:
        directory = tmp_path / "docs" / "slices" / ("done" if done else "")
        if not directory.is_dir():
            return []
        return sorted(p for p in directory.glob("SLICE-*.md") if p.is_file())

    monkeypatch.setattr(sys.modules[__name__], "_slice_files", fake_slice_files)


# --- the prototype slice itself must own a green, digest-bound record --------


def test_durability_slice_whose_record_is_not_green_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A prototype record that is not GREEN does not discharge the gate."""

    prototype = _write_prototype(tmp_path)
    _write_exit_record(prototype, status="AMBER", claims=_GREEN_PROTOTYPE_CLAIMS)
    _point_gate_at(monkeypatch, tmp_path)

    with pytest.raises(AssertionError, match="AMBER"):
        test_durability_production_slice_requires_green_digest_bound_record()


def test_durability_slice_whose_record_lacks_digests_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A green status with nothing bound by sha256 is a claim, not evidence."""

    prototype = _write_prototype(tmp_path)
    _write_exit_record(
        prototype, status="GREEN", claims=[{"claim": 1, "embedded": {"status": "GREEN"}}]
    )
    _point_gate_at(monkeypatch, tmp_path)

    with pytest.raises(AssertionError, match="binds no artifact by sha256"):
        test_durability_production_slice_requires_green_digest_bound_record()


def test_durability_slice_with_a_green_digest_bound_record_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The prototype's own record discharges the gate when it is green and digest-bound."""

    prototype = _write_prototype(tmp_path)
    _write_exit_record(prototype, status="GREEN", claims=_GREEN_PROTOTYPE_CLAIMS)
    _point_gate_at(monkeypatch, tmp_path)

    test_durability_production_slice_requires_green_digest_bound_record()


def test_durability_slice_without_an_exit_record_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A lone durability slice owning no record, with no prototype, is refused."""

    _write_production(tmp_path)
    _point_gate_at(monkeypatch, tmp_path)

    with pytest.raises(AssertionError, match="PROTOTYPE record"):
        test_durability_production_slice_requires_green_digest_bound_record()


def test_non_durability_slice_is_not_subject_to_the_record_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A slice that does not link ADR-015 owes no durability exit record."""

    _write_slice(tmp_path, "SLICE-012-other-work.md", references_adr=False)
    _point_gate_at(monkeypatch, tmp_path)

    test_durability_production_slice_requires_green_digest_bound_record()


# --- a production slice is gated BY the prototype record ---------------------


def test_durability_production_slice_passes_when_prototype_record_is_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A production slice is gated BY the prototype record, not by one of its own.

    This is the case ADR-015's Confirmation actually names: SLICE-012+ opens only
    when the SLICE-011 prototype record is green and digest-bound. A production
    slice carries no exit record of its own.
    """

    prototype = _write_prototype(tmp_path)
    _write_exit_record(prototype, status="GREEN", claims=_GREEN_PROTOTYPE_CLAIMS)
    _write_production(tmp_path)
    _point_gate_at(monkeypatch, tmp_path)

    test_durability_production_slice_requires_green_digest_bound_record()


def test_durability_production_slice_passes_when_prototype_is_archived(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The post-SLICE-011 world: the prototype is filed in docs/slices/done/.

    This is the only state the gate will ever actually run in once SLICE-011
    closes, so it must pass here. The record moved with the slice into done/.
    """

    prototype = _write_prototype(tmp_path, in_done=True)
    _write_exit_record(prototype, status="GREEN", claims=_GREEN_PROTOTYPE_CLAIMS)
    _write_production(tmp_path)
    _point_gate_at(monkeypatch, tmp_path)

    test_durability_production_slice_requires_green_digest_bound_record()


@pytest.mark.parametrize(
    ("bad_state", "match"),
    [
        ("missing", "PROTOTYPE record"),
        ("amber", "AMBER"),
        ("no_digest", "binds no artifact by sha256"),
    ],
)
def test_durability_production_slice_refused_when_prototype_record_is_bad(
    bad_state: str,
    match: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The gate keeps its teeth: a bad prototype record still refuses production.

    The prototype record is the authority for every production slice, so when it
    is missing, not GREEN, or lacks digests, a production slice linking ADR-015 is
    refused — never waved through on the production slice's own (absent) record.
    """

    prototype = _write_prototype(tmp_path)
    if bad_state == "amber":
        _write_exit_record(prototype, status="AMBER", claims=_GREEN_PROTOTYPE_CLAIMS)
    elif bad_state == "no_digest":
        _write_exit_record(
            prototype, status="GREEN", claims=[{"claim": 1, "embedded": {"status": "GREEN"}}]
        )
    # "missing": the prototype slice owns no record at all.
    _write_production(tmp_path)
    _point_gate_at(monkeypatch, tmp_path)

    with pytest.raises(AssertionError, match=match):
        test_durability_production_slice_requires_green_digest_bound_record()


# --- skill shelf: the shelf governs itself -----------------------------------
#
# The closed set names the only allowed skill. These checks keep the shelf what
# it claims to be: exactly the named files, each a lean, tracked, regular file
# that opens with its own identity. Two review findings shaped them: the
# markdown walk above skips directories like `legacy`, which under the shelf
# would be an invisible parking lot, so the shelf is walked raw; and a
# symlinked SKILL.md would let the suite judge bytes git does not carry, so a
# link is refused before content is read.


def _skills_root() -> Path:
    return REPO_ROOT / ".claude" / "skills"


def _skill_shelf_contents() -> list[Path]:
    """Every non-directory entry under .claude/skills — no skip filter.

    Symlinks are included even when they point at directories: a link is an
    entry in its own right here, never something to traverse.
    """

    root = _skills_root()
    if not root.is_dir():
        return []
    return sorted(
        p for p in root.rglob("*") if p.is_symlink() or not p.is_dir()
    )


# The one non-skill file the shelf carries: the upstream MIT copyright and
# permission notice for the adapted skills, fetched from the cited commit.
# MIT conditions copying on both notices travelling with the copies, and the
# closed set would otherwise refuse the very file that makes it lawful.
_SKILL_SHELF_LICENSE = "LICENSE-agent-skills.txt"

# Git's own name for the upstream LICENSE bytes, so a reviewer can compare the
# copy against addyosmani/agent-skills at the commit the skills cite without
# trusting this repository — the same binding vendored prior art uses. A name
# alone would admit any bytes wearing it.
_SKILL_SHELF_LICENSE_BLOB = "d67778ada6b9cda6227e9130da182c13e73c8b2e"


def test_the_skill_shelf_license_is_the_upstream_notice() -> None:
    """The admitted license file must hold the pinned upstream bytes."""

    path = _skills_root() / _SKILL_SHELF_LICENSE
    where = f".claude/skills/{_SKILL_SHELF_LICENSE}"
    assert not path.is_symlink(), f"{where} is a symlink, not committed evidence"
    assert path.is_file(), f"{where} is missing; the shelf test requires it"
    assert _tracked_by_git(path), f"{where} is untracked; run `git add {where}`"
    actual = _git_blob_sha(path)
    assert actual == _SKILL_SHELF_LICENSE_BLOB, (
        f"{where} holds blob {actual}, pinned {_SKILL_SHELF_LICENSE_BLOB}. "
        "These must be the upstream notice's bytes, not a file wearing its name."
    )


def test_the_skill_shelf_holds_exactly_the_pipeline_skills() -> None:
    """A closed set: nothing parked beside the skills, no stage missing."""

    expected = {_skills_root() / name / "SKILL.md" for name in _PIPELINE_SKILLS}
    expected.add(_skills_root() / _SKILL_SHELF_LICENSE)
    actual = set(_skill_shelf_contents())

    stray = sorted(
        p.relative_to(REPO_ROOT).as_posix() for p in actual - expected
    )
    assert not stray, (
        f"files on the skill shelf that are not pipeline skills: {stray}. "
        "The set is closed — a new skill is a deliberate edit to "
        "_PIPELINE_SKILLS in this test, and documents belong in docs/STATE.md, "
        "the slice, or the commit message."
    )

    missing = sorted(
        p.relative_to(REPO_ROOT).as_posix() for p in expected - actual
    )
    assert not missing, (
        f"pipeline skills missing from the shelf: {missing}. "
        "Every stage carries its skill; restore the file or supersede the "
        "pipeline decision in CLAUDE.md first."
    )


def test_every_skill_is_a_lean_tracked_regular_file() -> None:
    """Capped in two units, on disk as git sees it, never through a link."""

    problems: list[str] = []
    for name in _PIPELINE_SKILLS:
        path = _skills_root() / name / "SKILL.md"
        where = path.relative_to(REPO_ROOT).as_posix()
        if path.is_symlink():
            problems.append(
                f"{where} is a symlink; the suite would judge bytes git does "
                "not carry — vendor the content as a regular file"
            )
            continue
        if not path.is_file():
            continue  # the shelf test owns the missing-file failure
        if not _tracked_by_git(path):
            problems.append(
                f"{where} is not tracked by git; run `git add {where}` so "
                "reviewers can obtain what sessions will follow"
            )
        body = path.read_bytes()
        if len(body) > SKILL_MAX_BYTES:
            problems.append(
                f"{where} is {len(body)} bytes, cap {SKILL_MAX_BYTES}. "
                "A skill is instructions, not a handbook"
            )
        lines = len(body.decode("utf-8").splitlines())
        if lines > SKILL_MAX_LINES:
            problems.append(
                f"{where} is {lines} lines, cap {SKILL_MAX_LINES}. "
                "Say it shorter, or the detail belongs in the enforcing test"
            )
    assert not problems, "; ".join(problems)


def test_every_skill_declares_its_identity() -> None:
    """Frontmatter opens the file, names its directory, says when to use it."""

    problems: list[str] = []
    for name in _PIPELINE_SKILLS:
        path = _skills_root() / name / "SKILL.md"
        if path.is_symlink() or not path.is_file():
            continue  # owned by the shelf and regular-file tests
        where = path.relative_to(REPO_ROOT).as_posix()
        match = _SKILL_FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if match is None:
            problems.append(
                f"{where}: frontmatter must open the file as "
                "'---\\nname: <dir>\\ndescription: ...\\n---' — matched at the "
                "first byte, so a decoy block further down counts for nothing"
            )
            continue
        if match.group("name") != name:
            problems.append(
                f"{where}: frontmatter names {match.group('name')!r} but the "
                f"directory is {name!r}; they must agree"
            )
        if "Use when" not in match.group("description"):
            problems.append(
                f"{where}: description carries no 'Use when' trigger, so "
                "nothing tells a session when the skill applies"
            )
    assert not problems, "; ".join(problems)


# --- fixtures: synthetic shelves, none touching the real one -----------------

_SKILL_BODY = (
    "---\nname: {name}\ndescription: Does one stage. Use when that stage "
    "begins.\n---\n\n# {name}\n"
)


def _write_shelf(tmp_path: Path) -> Path:
    """A complete, minimal, valid shelf under tmp_path."""

    for name in _PIPELINE_SKILLS:
        skill = tmp_path / ".claude" / "skills" / name / "SKILL.md"
        skill.parent.mkdir(parents=True, exist_ok=True)
        skill.write_text(_SKILL_BODY.format(name=name), encoding="utf-8")
    (tmp_path / ".claude" / "skills" / _SKILL_SHELF_LICENSE).write_text(
        "MIT License\n", encoding="utf-8"
    )
    return tmp_path / ".claude" / "skills"


def test_a_document_parked_on_the_skill_shelf_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shelf admits the named skills and nothing beside them."""

    shelf = _write_shelf(tmp_path)
    (shelf / "idea-refine" / "handbook.md").write_text("parked\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    with pytest.raises(AssertionError, match="handbook.md"):
        test_the_skill_shelf_holds_exactly_the_pipeline_skills()


def test_a_skill_hidden_in_a_skipped_directory_is_still_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`legacy` and friends do not hide files here: the shelf is walked raw."""

    shelf = _write_shelf(tmp_path)
    hidden = shelf / "idea-refine" / "legacy"
    hidden.mkdir()
    (hidden / "notes.md").write_text("invisible?\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    with pytest.raises(AssertionError, match="notes.md"):
        test_the_skill_shelf_holds_exactly_the_pipeline_skills()


def test_a_symlinked_skill_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Content reachable only through a link is not committed evidence."""

    _write_shelf(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("mutable after review\n", encoding="utf-8")
    target = tmp_path / ".claude" / "skills" / "idea-refine" / "SKILL.md"
    target.unlink()
    target.symlink_to(outside)
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    with pytest.raises(AssertionError, match="symlink"):
        test_every_skill_is_a_lean_tracked_regular_file()


def test_a_decoy_frontmatter_block_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Identity is read at byte zero, not wherever a block happens to sit."""

    shelf = _write_shelf(tmp_path)
    decoy = (
        "# Actually an architecture report\n\n```\n---\nname: idea-refine\n"
        "description: Looks legitimate. Use when fooling a substring check.\n"
        "---\n```\n"
    )
    (shelf / "idea-refine" / "SKILL.md").write_text(decoy, encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "REPO_ROOT", tmp_path)

    with pytest.raises(AssertionError, match="first byte"):
        test_every_skill_declares_its_identity()


# --- the owner's build order: MAP records it, STATE points at it -------------
#
# Owner decision 2026-08-17: milestone 4 (real-world verification &
# observability) is built BEFORE milestone 3 (P0) and milestone 2 (background
# manager), because P0's own exit evidence strictly requires milestone 4's
# observability contract and real-e2e conventions — dependency order, not a
# competing priority. A build order an agent can read is a suggestion; these
# two checks are the constraint, so no session needs reminding.

# One dated owner-decision passage that names the reason (milestone 4 is P0's
# proof substrate) and fixes the order 4 → 3 → 2. "proof substrate" sits before
# the milestones because that is the reasoning: milestone 4 is built first AS
# the substrate; the order then follows from it. The literal "Build order:
# milestone 4" anchors the sequence to the passage's own order sentence.
_OWNER_BUILD_ORDER = re.compile(
    r"Owner decision \d{4}-\d{2}-\d{2}.+?proof substrate"
    r".+?Build order: milestone 4.+?milestone 3.+?milestone 2",
    re.DOTALL,
)


def test_map_records_owner_build_order() -> None:
    """The map carries the owner's dated build order, not a paraphrase of it."""

    where = REPO_ROOT / "docs" / "MAP.md"
    assert where.is_file(), "docs/MAP.md is the map — it must exist"
    assert _OWNER_BUILD_ORDER.search(
        where.read_text(encoding="utf-8")
    ), (
        "docs/MAP.md must carry the owner decision (dated) that fixes the "
        "build order: milestone 4 first as P0's proof substrate, then "
        "milestone 3, then milestone 2."
    )
