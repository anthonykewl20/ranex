"""The architecture-freeze scanner: default-deny edges, digest-bound policy.

The scanner is the deterministic counterweight to an approved module graph
(ADR-064): pure `ast`, one question per import statement — is this edge in
the freeze? These tests pin the semantics the micro-exercise proved through
the real kernel: unlisted edges are findings bound to the subject's bytes,
the freeze's canonical bytes must hash to the digest the catalog pinned, a
tree the freeze does not describe refuses rather than decorating, and the
SARIF reduces through the existing scan summary so `evaluate()` learns
nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ranex.foundation.arch_scan import (
    FREEZE_SCHEMA,
    RULE_FORBIDDEN,
    RULE_TAMPERED,
    arch_sarif_bytes,
    architecture_freeze_digest,
    freeze_digest_of_bytes,
    load_architecture_freeze_bytes,
    main,
)
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.scan_results import scan_results_from_sarif

FREEZE_REL = "governance/architecture-freeze.json"

PRISTINE_FREEZE: dict[str, Any] = {
    "schema": FREEZE_SCHEMA,
    "approved_by": "ADR-064-test",
    "package_root": "pkg",
    "modules": {
        "root": "pkg/__init__.py",
        "foundation": "pkg/foundation.py",
        "policy": "pkg/policy.py",
        "cli": "pkg/cli.py",
    },
    "allowed_edges": [
        ["cli", "foundation"],
        ["cli", "policy"],
        ["policy", "foundation"],
    ],
}

MANIFEST: dict[str, Any] = {
    "scope": sorted(
        [
            "pkg/__init__.py",
            "pkg/cli.py",
            "pkg/foundation.py",
            "pkg/policy.py",
            FREEZE_REL,
        ]
    ),
    "rules": [RULE_FORBIDDEN, RULE_TAMPERED],
    "blocking_levels": ["error"],
    "accepted": {},
}


def freeze_bytes(**overrides: Any) -> bytes:
    return canonical_json_bytes({**PRISTINE_FREEZE, **overrides})


def subject(root: Path, _freeze: bytes | None = None, **files: str | None) -> bytes:
    """Write the synthetic package plus the committed freeze; return bytes.

    A file mapped to `None` is not written — how a test shrinks the package.
    """

    default: dict[str, str | None] = {
        "pkg/__init__.py": "",
        "pkg/foundation.py": "def base():\n    return 1\n",
        "pkg/policy.py": (
            "from pkg import foundation\n\n\ndef rule():\n"
            "    return foundation.base() + 1\n"
        ),
        "pkg/cli.py": (
            "from pkg import foundation\nfrom pkg import policy\n\n\n"
            "def main():\n    return policy.rule() + foundation.base()\n"
        ),
    }
    (root / "governance").mkdir(parents=True, exist_ok=True)
    raw = _freeze if _freeze is not None else freeze_bytes()
    (root / FREEZE_REL).write_bytes(raw)
    for relative, text in {**default, **files}.items():
        path = root / relative
        if text is None:
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return raw


def scan(root: Path, raw: bytes) -> bytes:
    pinned = freeze_digest_of_bytes(raw)
    return arch_sarif_bytes(
        root, raw, freeze_relative=FREEZE_REL, expected_digest=pinned
    )


def results(sarif: bytes, root: Path, *, manifest: dict[str, Any] | None = None) -> dict:
    return scan_results_from_sarif(sarif, manifest or MANIFEST, subject_root=root)


def findings(sarif: bytes) -> list[tuple[str, str, int]]:
    return [
        (
            result["ruleId"],
            result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"],
            result["locations"][0]["physicalLocation"]["region"]["startLine"],
        )
        for result in json.loads(sarif)["runs"][0]["results"]
    ]


PLANTED_FOUNDATION = {
    "pkg/foundation.py": "def base():\n    return 1\n\nfrom pkg import policy\n"
}


# --- the freeze schema ------------------------------------------------------


def test_a_well_formed_freeze_loads_and_answers_its_digest() -> None:
    raw = freeze_bytes()
    loaded = load_architecture_freeze_bytes(raw)
    assert loaded["package_root"] == "pkg"
    assert architecture_freeze_digest(loaded).startswith("sha256:")


def test_padded_freeze_bytes_are_refused() -> None:
    padded = freeze_bytes().replace(b'{"', b'{ "', 1)  # parses, not canonical
    with pytest.raises(ValueError, match="exact canonical JSON bytes"):
        load_architecture_freeze_bytes(padded)


@pytest.mark.parametrize(
    "override, match",
    [
        ({"schema": "other-v9"}, "schema must be"),
        ({"approved_by": "  "}, "approved_by"),
        ({"package_root": "/abs"}, "package_root"),
        ({"package_root": "pkg/"}, "package_root"),
        ({"modules": {}}, "no modules"),
        ({"modules": {"bad-name": "pkg/x.py"}}, "identifier"),
        ({"modules": {"escape": "../pkg/x.py"}}, "under package_root"),
        ({"modules": {"a": "pkg/a.py", "b": "pkg/a.py"}}, "two modules"),
        ({"allowed_edges": [["cli", "ghost"]]}, "undeclared module"),
        ({"allowed_edges": [["cli", "policy"], ["cli", "policy"]]}, "twice"),
        (
            {"allowed_edges": [["policy", "foundation"], ["cli", "policy"]]},
            "sorted",
        ),
    ],
)
def test_malformed_freezes_are_refused_by_name(
    override: dict[str, Any], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        load_architecture_freeze_bytes(freeze_bytes(**override))


# --- module attribution and edge extraction ---------------------------------


def test_an_unlisted_edge_is_a_finding_at_its_statement(tmp_path: Path) -> None:
    raw = subject(tmp_path, **PLANTED_FOUNDATION)
    assert findings(scan(tmp_path, raw)) == [(RULE_FORBIDDEN, "pkg/foundation.py", 4)]


def test_an_empty_allow_list_blocks_every_edge(tmp_path: Path) -> None:
    """Default-deny: absence of declarations blocks rather than permits."""

    raw = subject(tmp_path, _freeze=freeze_bytes(allowed_edges=[]))
    found = findings(scan(tmp_path, raw))
    assert {path for _, path, _ in found} == {"pkg/cli.py", "pkg/policy.py"}


def test_relative_and_from_module_imports_resolve_to_edges(tmp_path: Path) -> None:
    raw = subject(
        tmp_path,
        **{
            "pkg/policy.py": (
                "from . import foundation\nfrom .foundation import base\n\n\n"
                "def rule():\n    return base() + 1\n"
            )
        },
    )
    assert findings(scan(tmp_path, raw)) == []


def test_an_import_of_the_package_root_is_an_edge_from_the_root_module(
    tmp_path: Path,
) -> None:
    raw = subject(tmp_path, **{"pkg/__init__.py": "from pkg import foundation\n"})
    assert findings(scan(tmp_path, raw)) == [
        (RULE_FORBIDDEN, "pkg/__init__.py", 1)
    ]


def test_a_directory_module_covers_its_files(tmp_path: Path) -> None:
    deep = freeze_bytes(
        modules={
            "root": "pkg/__init__.py",
            "deep": "pkg/deep",
            "cli": "pkg/cli.py",
        },
        allowed_edges=[["cli", "deep"]],
    )
    quiet = {
        "pkg/policy.py": None,
        "pkg/foundation.py": None,
        "pkg/deep/__init__.py": "",
        "pkg/deep/leaf.py": "",
        "pkg/cli.py": "from pkg.deep import leaf\n",
    }
    raw = subject(tmp_path, _freeze=deep, **quiet)
    assert findings(scan(tmp_path, raw)) == []
    raw = subject(
        tmp_path, _freeze=deep, **{**quiet, "pkg/deep/leaf.py": "from pkg import cli\n"}
    )
    assert findings(scan(tmp_path, raw)) == [(RULE_FORBIDDEN, "pkg/deep/leaf.py", 1)]


def test_a_file_in_no_module_refuses_the_whole_scan(tmp_path: Path) -> None:
    """The module-set analog of missing: out-of-scope findings cannot block,
    so the scan refuses (exit 2, no artifact) and absence blocks instead."""

    raw = subject(tmp_path, **{"pkg/rogue.py": "from pkg import foundation\n"})
    with pytest.raises(ValueError, match="pkg/rogue.py"):
        scan(tmp_path, raw)


def test_a_file_the_walk_cannot_parse_refuses_the_scan(tmp_path: Path) -> None:
    raw = subject(tmp_path, **{"pkg/policy.py": "def broken(:\n"})
    with pytest.raises(SyntaxError):
        scan(tmp_path, raw)


# --- finding identity -------------------------------------------------------


def test_identical_subject_bytes_answer_identical_finding_ids(
    tmp_path: Path,
) -> None:
    raw = subject(tmp_path, **PLANTED_FOUNDATION)
    first = json.loads(scan(tmp_path, raw))["runs"][0]["results"][0]
    again = json.loads(scan(tmp_path, raw))["runs"][0]["results"][0]
    assert first["fingerprints"]["ranex/v1"] == again["fingerprints"]["ranex/v1"]
    # the ID is the kernel's own shape over path, rule, region, bytes
    identifier = (
        f"pkg/foundation.py::{RULE_FORBIDDEN}::{first['fingerprints']['ranex/v1']}"
    )
    summary = results(scan(tmp_path, raw), tmp_path)
    assert [identifier, "failed"] in summary["non_passed"]


def test_moving_the_statement_changes_the_finding_id(tmp_path: Path) -> None:
    """Acceptance cannot survive the code under it changing."""

    raw = subject(
        tmp_path,
        **{
            "pkg/foundation.py": (
                "def base():\n    return 1\n\n\nfrom pkg import policy\n"
            )
        },
    )
    first = json.loads(scan(tmp_path, raw))["runs"][0]["results"][0]
    subject(
        tmp_path,
        **{
            "pkg/foundation.py": (
                "from pkg import policy\n\n\ndef base():\n    return 1\n"
            )
        },
    )
    second = json.loads(scan(tmp_path, raw))["runs"][0]["results"][0]
    assert first["fingerprints"]["ranex/v1"] != second["fingerprints"]["ranex/v1"]


# --- the digest pin ---------------------------------------------------------


def test_a_weakened_freeze_that_keeps_the_pin_is_a_tamper_finding(
    tmp_path: Path,
) -> None:
    """The plant an agent would actually reach for: add the edge it wants to
    the allow-list. The catalog's digest pin answers it."""

    pinned = freeze_digest_of_bytes(freeze_bytes())
    weakened = freeze_bytes(
        allowed_edges=[
            ["cli", "foundation"],
            ["cli", "policy"],
            ["foundation", "policy"],
            ["policy", "foundation"],
        ]
    )
    raw = subject(tmp_path, _freeze=weakened, **PLANTED_FOUNDATION)
    sarif = arch_sarif_bytes(
        tmp_path, raw, freeze_relative=FREEZE_REL, expected_digest=pinned
    )
    assert findings(sarif) == [(RULE_TAMPERED, FREEZE_REL, 1)]
    summary = results(sarif, tmp_path)
    assert [FREEZE_REL, "failed"] in summary["non_passed"]


def test_unpinned_the_freeze_path_stays_witnessed(tmp_path: Path) -> None:
    raw = subject(tmp_path)
    sarif = arch_sarif_bytes(
        tmp_path, raw, freeze_relative=FREEZE_REL, expected_digest=None
    )
    assert results(sarif, tmp_path)["missing"] == []


# --- reduction through the real scan summary --------------------------------


def test_a_pristine_tree_reduces_to_all_passed(tmp_path: Path) -> None:
    raw = subject(tmp_path)
    summary = results(scan(tmp_path, raw), tmp_path)
    assert summary["counts"]["passed"] == len(MANIFEST["scope"])
    assert summary["non_passed"] == []
    assert summary["missing"] == []


def test_an_accepted_finding_skips_and_the_rest_passes(tmp_path: Path) -> None:
    raw = subject(tmp_path, **PLANTED_FOUNDATION)
    sarif = scan(tmp_path, raw)
    identifier = (
        f"pkg/foundation.py::{RULE_FORBIDDEN}::"
        + json.loads(sarif)["runs"][0]["results"][0]["fingerprints"]["ranex/v1"]
    )
    accepted = {**MANIFEST, "accepted": {identifier: "reviewed exception"}}
    summary = results(sarif, tmp_path, manifest=accepted)
    assert summary["counts"] == {
        "passed": len(MANIFEST["scope"]),
        "skipped": 1,
        "failed": 0,
        "errors": 0,
        "xfailed": 0,
        "xpassed": 0,
    }
    assert [identifier, "skipped"] in summary["non_passed"]


def test_two_scans_of_one_tree_are_byte_identical(tmp_path: Path) -> None:
    raw = subject(tmp_path, **PLANTED_FOUNDATION)
    assert scan(tmp_path, raw) == scan(tmp_path, raw)


# --- the module entry point -------------------------------------------------


def test_the_module_entry_point_writes_the_artifact_and_exits_zero(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = subject(tmp_path)
    output = tmp_path / "out.sarif"
    code = main(
        [
            "check",
            "--freeze",
            str(tmp_path / FREEZE_REL),
            "--root",
            str(tmp_path),
            "--expected-freeze-digest",
            freeze_digest_of_bytes(raw),
            "--output-format",
            "sarif",
            "--output-file",
            str(output),
        ]
    )
    assert code == 0
    assert findings(output.read_bytes()) == []
    assert capsys.readouterr().out == ""


def test_the_digest_verb_prints_the_canonical_digest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = subject(tmp_path)
    assert main(["digest", "--freeze", str(tmp_path / FREEZE_REL)]) == 0
    assert capsys.readouterr().out.strip() == freeze_digest_of_bytes(raw)


def test_a_missing_freeze_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = main(
        [
            "check",
            "--freeze",
            str(tmp_path / FREEZE_REL),
            "--root",
            str(tmp_path),
            "--output-format",
            "sarif",
            "--output-file",
            str(tmp_path / "out.sarif"),
        ]
    )
    assert code == 2
    assert "cannot complete the scan" in capsys.readouterr().err
