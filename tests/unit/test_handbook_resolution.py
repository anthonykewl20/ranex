"""Unit tests for the path-scoped kernel handbook resolution engine (#100).

The engine is pure: bytes in, resolution out, no IO. These tests freeze the
grammar of `governance/handbook.json`, the two-layer precedence (project >
system), the system-only content sniffer, the honest `unmatched` row, and the
digest that changes when any chapter byte changes.
"""

from __future__ import annotations

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.policy.handbook import (
    PROJECT_LAYER,
    SYSTEM_LAYER,
    HandbookEntry,
    parse_handbook_bytes,
    render_brief,
    resolve_handbook,
)


def _system(*entries: HandbookEntry) -> tuple[HandbookEntry, ...]:
    return entries


def _project(*entries: HandbookEntry) -> tuple[HandbookEntry, ...]:
    return entries


def _entry(
    path_glob: str,
    text: str,
    *,
    merge_system: bool = False,
    sniff_marker: str | None = None,
) -> HandbookEntry:
    return HandbookEntry(
        path_glob=path_glob,
        text=text,
        merge_system=merge_system,
        sniff_marker=sniff_marker,
    )


def _handbook_bytes(*entries: dict[str, object]) -> bytes:
    return canonical_json_bytes({"version": 1, "entries": list(entries)})


# --- parsing: the designated shape, and nothing else -------------------------


def test_parse_accepts_the_designated_entry_shape() -> None:
    data = _handbook_bytes(
        {"path_glob": "src/**", "text": "chapter one", "merge_system": True},
        {"path_glob": "docs/*", "text": "chapter two"},
    )
    entries = parse_handbook_bytes(PROJECT_LAYER, data)
    assert entries == (
        _entry("src/**", "chapter one", merge_system=True),
        _entry("docs/*", "chapter two"),
    )


def test_parse_preserves_declaration_order() -> None:
    data = _handbook_bytes(
        {"path_glob": "b/**", "text": "b first"},
        {"path_glob": "a/**", "text": "a second"},
        {"path_glob": "c/**", "text": "c third"},
    )
    assert [entry.path_glob for entry in parse_handbook_bytes(PROJECT_LAYER, data)] == [
        "b/**",
        "a/**",
        "c/**",
    ]


@pytest.mark.parametrize(
    "payload",
    [
        b"[]",  # a bare list is not the designated shape
        b"{}",  # entries absent
        b'{"version": 1}',  # entries absent even with a version
        b'{"version": 2, "entries": []}',  # unknown version
        b'{"entries": {}}',  # entries not a list
        b'{"entries": ["nope"]}',  # entry not an object
        b'{"entries": [{"text": "no glob"}]}',  # path_glob absent
        b'{"entries": [{"path_glob": "", "text": "empty glob"}]}',  # blank glob
        b'{"entries": [{"path_glob": "src/**"}]}',  # text absent
        b'{"entries": [{"path_glob": "src/**", "text": ""}]}',  # empty text
        b'{"entries": [{"path_glob": 1, "text": "x"}]}',  # glob not a string
        b'{"entries": [{"path_glob": "s", "text": 2}]}',  # text not a string
        b'{"entries": [{"path_glob": "s", "text": "x", "merge_system": "yes"}]}',
        b'{"entries": [{"path_glob": "s", "text": "x", "extra": 1}]}',  # unknown key
        b"not json",
    ],
)
def test_parse_refuses_every_malformed_shape(payload: bytes) -> None:
    with pytest.raises(ValueError, match="^refusing handbook"):
        parse_handbook_bytes(PROJECT_LAYER, payload)


def test_parse_refuses_sniff_marker_on_the_project_layer() -> None:
    """A sniff may decorate only the system layer (#100 arm 3's root rule)."""

    data = _handbook_bytes(
        {"path_glob": "**/*.m", "text": "x", "sniff_marker": "#import"}
    )
    with pytest.raises(ValueError, match="sniff_marker is system-layer only"):
        parse_handbook_bytes(PROJECT_LAYER, data)
    # The same bytes parse on the system layer.
    assert len(parse_handbook_bytes(SYSTEM_LAYER, data)) == 1


def test_parse_accepts_empty_entries_list() -> None:
    assert parse_handbook_bytes(PROJECT_LAYER, _handbook_bytes()) == ()


# --- resolution: precedence, matching, honesty -------------------------------


def test_project_rule_outranks_system_rule_on_the_same_glob() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter")),
        ["src/a.py"],
    )
    (row,) = resolution.rows
    assert row.path == "src/a.py"
    assert row.status == "matched"
    assert row.layer == PROJECT_LAYER
    assert row.pattern == "src/**"
    assert row.system_pattern == "src/**"  # both matches recorded, not just the winner
    assert not row.merged
    assert not row.sniffed
    (chapter,) = resolution.chapters
    assert chapter.text == "project chapter"
    assert chapter.layer == PROJECT_LAYER


def test_system_rule_applies_when_no_project_rule_matches() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("docs/*", "project chapter")),
        ["src/a.py"],
    )
    (row,) = resolution.rows
    assert row.layer == SYSTEM_LAYER
    assert row.pattern == "src/**"
    assert row.system_pattern == "src/**"
    (chapter,) = resolution.chapters
    assert chapter.text == "system chapter"


def test_first_match_wins_within_a_layer_in_declaration_order() -> None:
    resolution = resolve_handbook(
        _system(),
        _project(_entry("src/**", "first"), _entry("src/*.py", "second")),
        ["src/a.py"],
    )
    assert resolution.chapters[0].text == "first"


def test_merge_system_combines_system_chapter_with_project_chapter() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter", merge_system=True)),
        ["src/a.py"],
    )
    (row,) = resolution.rows
    assert row.merged
    (chapter,) = resolution.chapters
    assert chapter.merged
    assert "system chapter" in chapter.text
    assert "project chapter" in chapter.text
    # The system chapter leads and the project chapter follows (the reference
    # behaviour: system-specific guidance first, user-specific second).
    assert chapter.text.index("system chapter") < chapter.text.index("project chapter")


def test_merge_system_without_a_system_match_is_the_project_text_alone() -> None:
    resolution = resolve_handbook(
        _system(),
        _project(_entry("src/**", "project chapter", merge_system=True)),
        ["src/a.py"],
    )
    (chapter,) = resolution.chapters
    assert chapter.merged
    assert chapter.text == "project chapter"


def test_unmatched_path_is_recorded_not_dropped() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(),
        ["src/a.py", "unrelated.bin"],
    )
    assert [row.status for row in resolution.rows] == ["matched", "unmatched"]
    unmatched = resolution.rows[1]
    assert unmatched.layer is None
    assert unmatched.pattern is None
    assert unmatched.chapter_id is None
    assert unmatched.system_pattern is None
    assert not unmatched.sniffed


def test_rows_preserve_the_input_path_order() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(),
        ["z.py", "a.py", "src/m.py"],
    )
    assert [row.path for row in resolution.rows] == ["z.py", "a.py", "src/m.py"]


# --- the glob language --------------------------------------------------------


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("src/**", "src/a.py", True),
        ("src/**", "src/deep/b.py", True),
        ("src/**", "src", False),  # '**' names what is under, not the directory itself
        ("**/*.py", "a.py", True),
        ("**/*.py", "deep/b/c.py", True),
        ("**/*.py", "a.js", False),
        ("*", "a.py", True),
        ("*", "a/b.py", False),  # '*' does not cross '/'
        ("*.py", "a.py", True),
        ("?.py", "a.py", True),
        ("?.py", "ab.py", False),
        ("src/[ab]?.py", "src/ax.py", True),
        ("src/[ab]?.py", "src/cx.py", False),
        ("docs/**", "docs/x.md", True),
        ("**/test_*.py", "test_a.py", True),
        ("**/test_*.py", "tests/unit/test_a.py", True),
        ("**/test_*.py", "src/atest.py", False),  # 'test_*' must anchor at a component
        ("a.b", "axb", False),  # '.' is literal
        ("a+b", "a+b", True),  # '+' is literal
    ],
)
def test_glob_language(pattern: str, path: str, expected: bool) -> None:
    resolution = resolve_handbook(
        _system(_entry(pattern, "chapter")),
        _project(),
        [path],
    )
    assert resolution.rows[0].status == ("matched" if expected else "unmatched"), (
        f"{pattern!r} vs {path!r}"
    )


# --- the system-only content sniffer ------------------------------------------


def test_sniff_marker_entry_wins_only_when_content_agrees() -> None:
    system = (
        _entry("**/*.m", "matlab chapter"),
        _entry("**/*.m", "objc chapter", sniff_marker="#import"),
    )
    project: tuple[HandbookEntry, ...] = ()

    sniffed = resolve_handbook(system, project, ["a.m"], peeks={"a.m": "#import <Foo.h>"})
    plain = resolve_handbook(system, project, ["a.m"], peeks={"a.m": "x = 1;"})

    assert sniffed.rows[0].layer == SYSTEM_LAYER
    assert sniffed.rows[0].sniffed
    assert sniffed.chapters[0].text == "objc chapter"
    assert not plain.rows[0].sniffed
    assert plain.chapters[0].text == "matlab chapter"


def test_sniff_ignores_blank_leading_lines_and_anchors_at_line_start() -> None:
    system = (
        _entry("**/*.m", "matlab chapter"),
        _entry("**/*.m", "objc chapter", sniff_marker="#import"),
    )
    resolution = resolve_handbook(
        system, (), ["a.m"], peeks={"a.m": "\n\n   #import <Foo.h>\n"}
    )
    assert resolution.rows[0].sniffed
    # A line that merely contains the marker does not fire it.
    other = resolve_handbook(
        system, (), ["a.m"], peeks={"a.m": "fprintf('#import');"}
    )
    assert not other.rows[0].sniffed


def test_sniff_cannot_override_a_project_rule() -> None:
    """The load-bearing arm 3 rule: a heuristic never beats the operator."""

    system = (
        _entry("**/*.m", "matlab chapter"),
        _entry("**/*.m", "objc chapter", sniff_marker="#import"),
    )
    project = (_entry("**/*.m", "project chapter"),)
    resolution = resolve_handbook(
        system, project, ["a.m"], peeks={"a.m": "#import <Foo.h>"}
    )
    (row,) = resolution.rows
    assert row.layer == PROJECT_LAYER
    assert not row.sniffed
    assert resolution.chapters[0].text == "project chapter"
    # The sniff still names what the system layer WOULD have said.
    assert row.system_pattern == "**/*.m"


def test_sniff_without_a_peek_defers_to_the_path_match() -> None:
    system = (
        _entry("**/*.m", "matlab chapter"),
        _entry("**/*.m", "objc chapter", sniff_marker="#import"),
    )
    resolution = resolve_handbook(system, (), ["a.m"])
    assert not resolution.rows[0].sniffed
    assert resolution.chapters[0].text == "matlab chapter"


def test_sniffed_merge_uses_the_sniffed_system_chapter() -> None:
    system = (
        _entry("**/*.m", "matlab chapter"),
        _entry("**/*.m", "objc chapter", sniff_marker="#import"),
    )
    project = (_entry("**/*.m", "project chapter", merge_system=True),)
    resolution = resolve_handbook(
        system, project, ["a.m"], peeks={"a.m": "#import <Foo.h>"}
    )
    (chapter,) = resolution.chapters
    assert chapter.merged
    assert "objc chapter" in chapter.text
    assert chapter.text.index("objc chapter") < chapter.text.index("project chapter")


# --- chapters and the digest ---------------------------------------------------


def test_chapters_dedupe_by_resolved_content_in_first_appearance_order() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter")),
        ["src/a.py", "docs/x.md", "src/b.py"],
    )
    assert [chapter.chapter_id for chapter in resolution.chapters] == [
        "project:src/**",
    ]
    assert resolution.chapter_for("src/a.py").text == "project chapter"
    assert resolution.chapter_for("src/b.py") is resolution.chapters[0]
    assert resolution.chapter_for("docs/x.md") is None


def test_same_pattern_different_resolved_text_gets_distinct_chapters() -> None:
    system = (
        _entry("**/*.m", "matlab chapter"),
        _entry("**/*.m", "objc chapter", sniff_marker="#import"),
    )
    project = _project(_entry("**/*.m", "project chapter", merge_system=True))
    # Both paths match the same project entry, but the merge pulls a different
    # system chapter into each: same pattern, two resolved texts, two ids.
    resolution = resolve_handbook(
        system,
        project,
        ["plain.m", "cocoa.m"],
        peeks={"cocoa.m": "#import <Foo.h>"},
    )
    ids = [chapter.chapter_id for chapter in resolution.chapters]
    assert ids == ["project:**/*.m", "project:**/*.m#2"]
    assert "matlab chapter" in resolution.chapters[0].text
    assert "objc chapter" in resolution.chapters[1].text


def test_digest_is_stable_across_identical_repeats() -> None:
    system = _system(_entry("src/**", "system chapter"))
    project = _project(_entry("src/**", "project chapter"))
    paths = ["src/a.py", "src/b.py", "other.bin"]
    first = resolve_handbook(system, project, paths)
    for _ in range(3):
        repeat = resolve_handbook(system, project, paths)
        assert repeat.digest == first.digest
        assert repeat.rows == first.rows
        assert repeat.chapters == first.chapters


def test_one_byte_of_chapter_text_changes_the_digest() -> None:
    paths = ["src/a.py"]
    base = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter")),
        paths,
    )
    changed_text = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter!")),
        paths,
    )
    changed_glob = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("sre/**", "project chapter")),
        paths,
    )
    changed_merge = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter", merge_system=True)),
        paths,
    )
    for other in (changed_text, changed_glob, changed_merge):
        assert other.digest != base.digest


def test_digest_format_is_prefixed_sha256_over_canonical_bytes() -> None:
    import hashlib

    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(),
        ["src/a.py"],
    )
    assert resolution.digest == "sha256:" + hashlib.sha256(
        canonical_json_bytes(
            {
                "chapters": [
                    {
                        "chapter_id": chapter.chapter_id,
                        "layer": chapter.layer,
                        "pattern": chapter.pattern,
                        "text": chapter.text,
                        "merged": chapter.merged,
                        "sniffed": chapter.sniffed,
                    }
                    for chapter in resolution.chapters
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
                    for row in resolution.rows
                ],
            }
        )
    ).hexdigest()


def test_empty_resolution_still_digests_honestly() -> None:
    resolution = resolve_handbook((), (), ["a.py"])
    assert resolution.chapters == ()
    assert resolution.rows[0].status == "unmatched"
    assert resolution.digest.startswith("sha256:")


# --- the rendered brief ---------------------------------------------------------


def test_render_brief_names_chapters_and_every_path() -> None:
    resolution = resolve_handbook(
        _system(_entry("src/**", "system chapter")),
        _project(_entry("src/**", "project chapter")),
        ["src/a.py", "src/b.py", "docs/x.md"],
    )
    brief = render_brief(resolution)
    assert "guidance" in brief  # the brief states its own non-authority
    assert "project chapter" in brief
    assert "src/a.py" in brief
    assert "docs/x.md" in brief
    assert "unmatched" in brief
    # Deterministic render: same resolution, same bytes.
    assert render_brief(resolution) == brief


def test_render_brief_is_empty_for_no_layers_and_no_paths() -> None:
    resolution = resolve_handbook((), (), [])
    assert resolution.digest
    # A render of nothing is not a brief; callers skip injection when no layer
    # exists at all.
    assert render_brief(resolution) == ""
