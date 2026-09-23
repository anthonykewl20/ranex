"""#110 — deliberate-shortcut markers, grepped and reduced deterministically.

A `ranex:` comment names the ceiling a simplification accepts and the trigger
that should revisit it. The scanner is pure grep: no model, no network, no
judgment. What it emits is SARIF 2.1.0 that `scan_results` already knows how
to reduce, so `evaluate()` learns nothing new and stays untouched.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from ranex.foundation.markers import (
    RULE_MALFORMED,
    RULE_NO_TRIGGER,
    RULE_SHORTCUT,
    main,
    marker_sarif_bytes,
    scan_tree,
    scanned_files,
)
from ranex.foundation.scan_results import (
    finding_id,
    scan_results_from_sarif,
    validate_scan_manifest,
)

WELL_FORMED = "# ranex: global lock; per-account locks if throughput matters"
WELL_FORMED_SLASH = "// ranex: O(n^2) scan; index when lists exceed 10k"
NO_TRIGGER = "# ranex: global lock"
EMPTY_CEILING = "# ranex: ; whenever throughput matters"
EMPTY_TRIGGER = "# ranex: global lock ;"
IN_STRING = 'phrase = "# ranex: global lock"'
IN_STRING_SLASH = 'url = "// ranex: a; b"'


def findings_by_rule(root: Path) -> dict[str, list[tuple[str, int]]]:
    grouped: dict[str, list[tuple[str, int]]] = {}
    for finding in scan_tree(root):
        grouped.setdefault(finding.rule_id, []).append((finding.path, finding.line))
    return grouped


def write_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp_path


# --- the marker line protocol ----------------------------------------------


def test_a_well_formed_marker_is_a_note_finding(tmp_path: Path) -> None:
    write_tree(tmp_path, {"six.py": f"import os\n{WELL_FORMED}\n"})
    (finding,) = scan_tree(tmp_path)
    assert finding.rule_id == RULE_SHORTCUT
    assert finding.level == "note"
    assert finding.path == "six.py"
    assert finding.line == 2
    assert "global lock" in finding.snippet and "per-account" in finding.snippet


def test_a_slash_comment_marker_is_found_in_any_language(tmp_path: Path) -> None:
    write_tree(tmp_path, {"mod.js": f"let x = 1;\n{WELL_FORMED_SLASH}\n"})
    (finding,) = scan_tree(tmp_path)
    assert finding.rule_id == RULE_SHORTCUT
    assert finding.path == "mod.js"


def test_a_marker_without_a_trigger_is_the_rotting_error(tmp_path: Path) -> None:
    """Upstream's `no-trigger` tag: a ceiling with no revisit condition is the
    marker that rots silently, so it is the finding a gate can refuse."""

    write_tree(tmp_path, {"six.py": f"import os\n{NO_TRIGGER}\n"})
    (finding,) = scan_tree(tmp_path)
    assert finding.rule_id == RULE_NO_TRIGGER
    assert finding.level == "error"


def test_a_marker_with_an_empty_half_is_malformed(tmp_path: Path) -> None:
    write_tree(tmp_path, {"a.py": f"x = 1\n{EMPTY_CEILING}\n", "b.py": f"y = 2\n{EMPTY_TRIGGER}\n"})
    grouped = findings_by_rule(tmp_path)
    assert [line for _, line in grouped[RULE_MALFORMED]] == [2, 2]
    assert all(f.level == "error" for f in scan_tree(tmp_path))


def test_a_marker_inside_a_string_literal_is_not_a_comment(tmp_path: Path) -> None:
    """Arm 6's false-positive control: documentation quoting the convention
    must not be refused as a violation."""

    write_tree(tmp_path, {
        "doc.py": f"EXAMPLE = \"# ranex: global lock; revisit when\"\n{IN_STRING}\n",
        "web.js": f"let a = 1;\n{IN_STRING_SLASH}\n",
        "note.py": "msg = '# ranex: single quoted rot'\n",
    })
    assert scan_tree(tmp_path) == ()


def test_a_real_comment_after_a_closed_string_is_still_a_finding(tmp_path: Path) -> None:
    write_tree(tmp_path, {"a.py": 'x = "a"  # ranex: ceil; trig\n'})
    (finding,) = scan_tree(tmp_path)
    assert finding.rule_id == RULE_SHORTCUT
    assert finding.line == 1


def test_escaped_quotes_do_not_close_the_string(tmp_path: Path) -> None:
    write_tree(tmp_path, {
        "a.py": 's = "he said \\"hi\\" # ranex: x; y"\n',
        "b.py": 's = "\\""  # ranex: ceil; trig\n',
    })
    (finding,) = scan_tree(tmp_path)
    assert finding.path == "b.py"


# --- the walk ----------------------------------------------------------------


def test_upstream_exclusion_directories_are_not_walked(tmp_path: Path) -> None:
    write_tree(tmp_path, {
        "ok.py": f"{WELL_FORMED}\n",
        ".git/config.py": f"{NO_TRIGGER}\n",
        "node_modules/pkg/index.js": f"{WELL_FORMED_SLASH}\n",
        "build/out.c": f"// ranex: c; t\n",
        "dist/bundle.js": f"{WELL_FORMED_SLASH}\n",
        "target/main.rs": f"// ranex: c; t\n",
        "__pycache__/m.py": f"{NO_TRIGGER}\n",
    })
    assert scanned_files(tmp_path) == ("ok.py",)
    (finding,) = scan_tree(tmp_path)
    assert finding.path == "ok.py"


def test_a_file_that_is_not_utf8_is_skipped_whole(tmp_path: Path) -> None:
    (tmp_path / "blob.bin").write_bytes(b"# ranex: a; b\n\xff\xfe not text\n")
    assert scanned_files(tmp_path) == ()
    assert scan_tree(tmp_path) == ()


def test_scan_output_is_deterministic(tmp_path: Path) -> None:
    write_tree(tmp_path, {
        "b.py": f"{NO_TRIGGER}\n",
        "a.py": f"{WELL_FORMED}\n{EMPTY_CEILING}\n",
        "c/d.py": f"{WELL_FORMED_SLASH}\n",
    })
    first, second = marker_sarif_bytes(tmp_path), marker_sarif_bytes(tmp_path)
    assert first == second
    assert scan_tree(tmp_path) == scan_tree(tmp_path)


# --- the SARIF artifact ------------------------------------------------------


def sarif_results(root: Path) -> list[dict[str, object]]:
    document = json.loads(marker_sarif_bytes(root))
    (run,) = document["runs"]
    return run["results"]


def test_the_artifact_carries_the_97_fingerprint_of_the_subject_bytes(
    tmp_path: Path,
) -> None:
    write_tree(tmp_path, {"six.py": f"import os\n{NO_TRIGGER}\n"})
    (result,) = sarif_results(tmp_path)
    region = tmp_path.joinpath("six.py").read_bytes().splitlines(keepends=True)[1]
    expected = finding_id(RULE_NO_TRIGGER, "six.py", 2, 2, region)
    assert result["fingerprints"]["ranex/v1"] == expected.split("::")[-1]
    # And the parser recomputes exactly that ID from the subject.
    manifest = validate_scan_manifest({
        "scope": ["six.py"], "rules": [RULE_MALFORMED, RULE_NO_TRIGGER, RULE_SHORTCUT],
        "blocking_levels": ["error"], "accepted": {},
    })
    summary = scan_results_from_sarif(
        marker_sarif_bytes(tmp_path), manifest, subject_root=tmp_path
    )
    assert dict(summary["non_passed"]) == {
        "six.py": "failed",
        expected: "failed",
    }


def test_every_scanned_file_is_a_witnessed_artifact(tmp_path: Path) -> None:
    write_tree(tmp_path, {"a.py": f"{WELL_FORMED}\n", "c/b.js": "let x;\n"})
    document = json.loads(marker_sarif_bytes(tmp_path))
    (run,) = document["runs"]
    witnessed = [a["location"]["uri"] for a in run["artifacts"]]
    assert witnessed == ["a.py", "c/b.js"]
    assert run["invocations"] == [{"executionSuccessful": True}]


def test_the_reducer_passes_a_well_formed_marker_and_fails_a_triggerless_one(
    tmp_path: Path,
) -> None:
    write_tree(tmp_path, {
        "good.py": f"{WELL_FORMED}\n",
        "bad.py": f"{NO_TRIGGER}\n",
    })
    manifest = validate_scan_manifest({
        "scope": ["bad.py", "good.py"],
        "rules": [RULE_MALFORMED, RULE_NO_TRIGGER, RULE_SHORTCUT],
        "blocking_levels": ["error"],
        "accepted": {},
    })
    summary = scan_results_from_sarif(
        marker_sarif_bytes(tmp_path), manifest, subject_root=tmp_path
    )
    assert dict(summary["non_passed"])["bad.py"] == "failed"
    assert summary["counts"]["failed"] == 2  # the path and the finding


def test_an_accepted_error_finding_is_a_skip_not_a_pass(tmp_path: Path) -> None:
    write_tree(tmp_path, {"bad.py": f"{NO_TRIGGER}\n"})
    region = (tmp_path / "bad.py").read_bytes().splitlines(keepends=True)[0]
    accepted_id = finding_id(RULE_NO_TRIGGER, "bad.py", 1, 1, region)
    manifest = validate_scan_manifest({
        "scope": ["bad.py"],
        "rules": [RULE_MALFORMED, RULE_NO_TRIGGER, RULE_SHORTCUT],
        "blocking_levels": ["error"],
        "accepted": {accepted_id: "review answered for this shortcut"},
    })
    summary = scan_results_from_sarif(
        marker_sarif_bytes(tmp_path), manifest, subject_root=tmp_path
    )
    assert dict(summary["non_passed"]) == {accepted_id: "skipped"}
    assert summary["counts"]["failed"] == 0


# --- the command line --------------------------------------------------------


def run_cli(root: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-P", "-m", "ranex.foundation.markers", *extra],
        cwd=root, capture_output=True, text=True, check=False,
    )


def test_the_module_entry_point_writes_the_artifact_and_exits_zero(
    tmp_path: Path,
) -> None:
    """Correction 2: the scanner ships as an installed entry point — never an
    in-tree script — and like ruff `--exit-zero` it reports through the
    artifact, because a bound `accepted` must be reachable through a zero exit."""

    write_tree(tmp_path, {"six.py": f"{NO_TRIGGER}\n"})
    completed = run_cli(
        tmp_path, "--output-format=sarif", "--output-file=governance/markers.sarif"
    )
    assert completed.returncode == 0, completed.stderr
    artifact = tmp_path / "governance/markers.sarif"
    (result,) = json.loads(artifact.read_bytes())["runs"][0]["results"]
    assert result["ruleId"] == RULE_NO_TRIGGER
    assert result["level"] == "error"


def test_the_module_entry_point_rejects_an_unknown_output_format(
    tmp_path: Path,
) -> None:
    write_tree(tmp_path, {"a.py": "x = 1\n"})
    completed = run_cli(tmp_path, "--output-format=junit", "--output-file=out.json")
    assert completed.returncode != 0


def test_main_refuses_an_unwritable_artifact(tmp_path: Path) -> None:
    write_tree(tmp_path, {"a.py": "x = 1\n"})
    assert (
        main(["--output-format=sarif", "--output-file=/proc/1/nope/out.sarif", "--root", str(tmp_path)])
        == 2
    )


def test_the_ranex_markers_subcommand_writes_the_same_artifact(
    tmp_path: Path,
) -> None:
    """The subcommand is the form a governed run binds: the console script
    keeps its own shebang and therefore its own kernel, where the module form
    resolves through the venv symlink to a bare interpreter."""

    from ranex.cli.main import main as cli_main

    write_tree(tmp_path, {"six.py": f"{NO_TRIGGER}\n"})
    artifact = tmp_path / "out.sarif"
    exit_code = cli_main([
        "markers", "--output-format=sarif",
        f"--output-file={artifact}", "--root", str(tmp_path),
    ])
    assert exit_code == 0
    (result,) = json.loads(artifact.read_bytes())["runs"][0]["results"]
    assert result["ruleId"] == RULE_NO_TRIGGER
