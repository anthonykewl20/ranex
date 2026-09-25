"""The C3 anti-slop scanner: AST census + structural slop, SARIF out.

The frozen control bank is the science bank plus the two plants the wave-1
ruling promoted. Three slop plants (body-removed, tautology,
assert-commented) and six known-good edits come from the kernel-oracle
science run (§3.3, receipts `c3-antislop.json`); snapshot-blind-update and
input-range-narrowing are adopted as behaviour from oracle-gate's
AI-test-weakening enumeration (CC-BY-4.0, methodology only). Every plant
must block; every known-good edit must not fire. Pure `ast` — no model, no
network, no judgment; `evaluate()` learns nothing.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

from ranex.foundation.antislop import (
    RULE_CENSUS,
    RULE_PASS_BODY,
    RULE_RANGE_NARROW,
    RULE_SNAPSHOT_BLIND,
    RULE_TAUTOLOGY,
    antislop_sarif_bytes,
    census_of_tree,
    scan_tree,
)
from ranex.foundation.scan_results import _region_bytes, _subject_relative, finding_id

# --- the science bank -------------------------------------------------------

#: SLOP-S1-a: a real assertion replaced by `pass` (body removed).
BODY_REMOVED = (
    "def test_add_doc():\n"
    "    pass\n"
)
#: SLOP-S1-b: the assertion replaced by a constant truth.
TAUTOLOGY = (
    "def test_add_doc():\n"
    "    assert True\n"
)
#: The approved body the science bank froze: one real assertion.
APPROVED_SINGLE = (
    "def test_add_doc():\n"
    "    assert add_doc(1) == '1'\n"
)
#: SLOP-S1-c shape: four real assertions in the approved tree...
APPROVED_FOUR = (
    "def test_integer_types():\n"
    "    assert add_doc(1) == '1'\n"
    "    assert add_doc(-1) == '-1'\n"
    "    assert add_doc(0) == '0'\n"
    "    assert add_doc(1.0) == '1.0'\n"
)
#: ...one commented out in the candidate (assert count 3 < frozen 4).
ASSERT_COMMENTED = (
    "def test_integer_types():\n"
    "    assert add_doc(1) == '1'\n"
    "    assert add_doc(-1) == '-1'\n"
    "    # assert add_doc(0) == '0'\n"
    "    assert add_doc(1.0) == '1.0'\n"
)

# --- the wave-1 promotion plants --------------------------------------------

#: S2-g: blindly updating snapshots so a snapshot test stops asserting.
SNAPSHOT_FLAG = (
    "import subprocess\n"
    "\n"
    "def test_render():\n"
    "    assert render() == snapshot()\n"
    "    subprocess.check_call(['pytest', '--snapshot-update'])\n"
)
SNAPSHOT_KWARG = (
    "def test_render():\n"
    "    assert_match_snapshot(render(), update=True)\n"
)
#: S2-h: narrowing generated-input ranges so a property test stops probing.
RANGE_NARROW_EXAMPLES = (
    "from hypothesis import given, settings, strategies as st\n"
    "\n"
    "@settings(max_examples=1)\n"
    "@given(st.integers())\n"
    "def test_roundtrip(value):\n"
    "    assert roundtrip(value) == value\n"
)
RANGE_NARROW_POINT = (
    "from hypothesis import given, strategies as st\n"
    "\n"
    "@given(st.integers(min_value=0, max_value=0))\n"
    "def test_roundtrip(value):\n"
    "    assert roundtrip(value) == value\n"
)

#: Known-good generated input: a real range and a real sample size.
RANGE_HONEST = (
    "from hypothesis import given, settings, strategies as st\n"
    "\n"
    "@settings(max_examples=50)\n"
    "@given(st.integers(min_value=-1000, max_value=1000))\n"
    "def test_roundtrip(value):\n"
    "    assert roundtrip(value) == value\n"
)


def write_tree(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return tmp_path


def census(tmp_path: Path, files: dict[str, str]) -> dict[str, int]:
    return {
        entry.test_id: entry.count
        for entry in census_of_tree(write_tree(tmp_path, files))
    }


def rules(tmp_path: Path, files: dict[str, str]) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = {}
    for finding in scan_tree(write_tree(tmp_path, files)):
        grouped.setdefault(finding.rule_id, []).append(finding.line)
    return grouped


# --- the census: what the freeze records, what the reduction compares --------


def test_a_real_assertion_censuses_as_one(tmp_path: Path) -> None:
    assert census(tmp_path, {"test_six.py": APPROVED_SINGLE}) == {
        "test_six.py::test_add_doc": 1
    }


def test_assertion_equivalent_calls_count_like_asserts(tmp_path: Path) -> None:
    """The science run's own detector bug: `test_print_exceptions` carries no
    `assert` at all, only `pytest.raises` — and is a real test. Counting
    literal `assert` statements alone made known-good trees false-fail."""

    body = (
        "import pytest\n"
        "\n"
        "def test_print_exceptions():\n"
        "    with pytest.raises(ValueError):\n"
        "        print_exceptions()\n"
    )
    assert census(tmp_path, {"test_six.py": body}) == {
        "test_six.py::test_print_exceptions": 1
    }
    assert rules(tmp_path, {"test_six.py": body}) == {}


def test_unittest_assert_methods_count(tmp_path: Path) -> None:
    body = (
        "import unittest\n"
        "\n"
        "class TestX(unittest.TestCase):\n"
        "    def test_integer_types(self):\n"
        "        self.assertEqual(add_doc(1), '1')\n"
        "        self.assertRaises(TypeError, add_doc, None)\n"
    )
    assert census(tmp_path, {"test_six.py": body}) == {
        "test_six.py::TestX::test_integer_types": 2
    }


def test_only_test_functions_are_censused(tmp_path: Path) -> None:
    body = (
        "def helper():\n"
        "    assert True\n"
        "\n"
        "def test_real():\n"
        "    assert helper() is None\n"
    )
    assert census(tmp_path, {"test_six.py": body}) == {"test_six.py::test_real": 1}


def test_census_is_scoped_to_test_files(tmp_path: Path) -> None:
    assert census(tmp_path, {"six.py": APPROVED_SINGLE}) == {}


# --- the science slop plants: each fires its structural rule -----------------


def test_body_removed_is_a_pass_body_finding(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_six.py": BODY_REMOVED}) == {
        RULE_PASS_BODY: [1]
    }
    assert census(tmp_path, {"test_six.py": BODY_REMOVED}) == {
        "test_six.py::test_add_doc": 0
    }


def test_tautology_is_an_error_finding(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_six.py": TAUTOLOGY}) == {RULE_TAUTOLOGY: [2]}


def test_other_constant_truths_are_tautologies(tmp_path: Path) -> None:
    for constant in ("1", '"six"', "not False", "not ''"):
        body = f"def test_t():\n    assert {constant}\n"
        assert list(rules(tmp_path, {"test_six.py": body})) == [RULE_TAUTOLOGY], constant


def test_a_real_comparison_is_not_a_tautology(tmp_path: Path) -> None:
    for honest in ("add_doc(1) == '1'", "result", "len(items) > 0"):
        body = f"def test_t():\n    assert {honest}\n"
        assert rules(tmp_path, {"test_six.py": body}) == {}, honest


def test_assert_commented_leaves_no_structural_trace_but_drops_the_census(
    tmp_path: Path,
) -> None:
    """The plant the census exists for: nothing structural is wrong with the
    candidate tree — it is simply doing less than the frozen tree promised."""

    assert rules(tmp_path, {"test_six.py": ASSERT_COMMENTED}) == {}
    assert census(tmp_path, {"test_six.py": ASSERT_COMMENTED}) == {
        "test_six.py::test_integer_types": 3
    }
    assert census(tmp_path, {"test_six.py": APPROVED_FOUR}) == {
        "test_six.py::test_integer_types": 4
    }


# --- the wave-1 plants -------------------------------------------------------


def test_snapshot_update_flag_is_a_finding(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_render.py": SNAPSHOT_FLAG}) == {
        RULE_SNAPSHOT_BLIND: [5]
    }


def test_snapshot_update_kwarg_is_a_finding(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_render.py": SNAPSHOT_KWARG}) == {
        RULE_SNAPSHOT_BLIND: [2]
    }


def test_an_honest_snapshot_test_does_not_fire(tmp_path: Path) -> None:
    body = (
        "def test_render():\n"
        "    assert render() == snapshot()\n"
        "    assert_match_snapshot(render())\n"
    )
    assert rules(tmp_path, {"test_render.py": body}) == {}


def test_narrowed_example_count_is_a_finding(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_props.py": RANGE_NARROW_EXAMPLES}) == {
        RULE_RANGE_NARROW: [3]
    }


def test_point_input_range_is_a_finding(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_props.py": RANGE_NARROW_POINT}) == {
        RULE_RANGE_NARROW: [3]
    }


def test_honest_generated_ranges_do_not_fire(tmp_path: Path) -> None:
    assert rules(tmp_path, {"test_props.py": RANGE_HONEST}) == {}


# --- the six known-good edits: none may fire --------------------------------


def test_known_good_edits_never_fire(tmp_path: Path) -> None:
    bank = {
        # KG-S1-01: a comment in the library file.
        "six.py": APPROVED_SINGLE.replace("def test_", "# a comment\ndef test_"),
        # KG-S1-02: a comment inside the test body.
        "test_comment.py": (
            "def test_add_doc():\n"
            "    # why 1: the smallest positive integer\n"
            "    assert add_doc(1) == '1'\n"
        ),
        # KG-S1-03: a blank line in the library file.
        "test_blank.py": "def test_add_doc():\n\n    assert add_doc(1) == '1'\n",
        # KG-S1-04: a module docstring in the test file.
        "test_docstring.py": (
            '"""Tests for add_doc."""\n\n'
            "def test_add_doc():\n"
            "    assert add_doc(1) == '1'\n"
        ),
        # KG-S1-05: a comment beside the import.
        "test_import.py": (
            "import six  # the module under test\n\n"
            "def test_add_doc():\n"
            "    assert six.add_doc(1) == '1'\n"
        ),
        # KG-S1-06: extra whitespace inside the test file.
        "test_whitespace.py": (
            "def test_add_doc():\n"
            "    assert add_doc(1) == '1'\n"
            "\n"
        ),
    }
    assert rules(tmp_path, bank) == {}
    assert census(tmp_path, bank)["test_comment.py::test_add_doc"] == 1


# --- the artifact: SARIF the #97 machinery can bind -------------------------


def test_sarif_carries_witnesses_fingerprints_and_census(tmp_path: Path) -> None:
    root = write_tree(tmp_path, {"test_six.py": TAUTOLOGY})
    raw = antislop_sarif_bytes(root)
    document = json.loads(raw)
    assert document["version"] == "2.1.0"
    (run,) = document["runs"]
    assert run["invocations"] == [{"executionSuccessful": True}]
    assert [a["location"]["uri"] for a in run["artifacts"]] == ["test_six.py"]
    by_rule = {r["ruleId"]: r for r in run["results"]}
    assert set(by_rule) == {RULE_TAUTOLOGY, RULE_CENSUS}
    tautology = by_rule[RULE_TAUTOLOGY]
    assert tautology["level"] == "error"
    physical = tautology["locations"][0]["physicalLocation"]
    path = _subject_relative(physical["artifactLocation"]["uri"], root)
    region = physical["region"]
    material = _region_bytes(root, path, region["startLine"], region["endLine"], None)
    assert tautology["fingerprints"]["ranex/v1"] == finding_id(
        RULE_TAUTOLOGY, path, region["startLine"], region["endLine"], material
    ).split("::")[-1]
    census = by_rule[RULE_CENSUS]
    assert census["level"] == "none"
    assert census["message"]["text"] == "test_six.py::test_add_doc effective_asserts=1"


def test_sarif_is_byte_deterministic(tmp_path: Path) -> None:
    root = write_tree(tmp_path, {"test_six.py": APPROVED_FOUR})
    assert antislop_sarif_bytes(root) == antislop_sarif_bytes(root)


def test_a_syntax_error_is_refused_not_swallowed(tmp_path: Path) -> None:
    root = write_tree(tmp_path, {"test_six.py": "def test_t(:\n    pass\n"})
    try:
        antislop_sarif_bytes(root)
    except SyntaxError:
        return
    raise AssertionError("a file the interpreter cannot parse must be refused")


def test_the_scanner_module_is_stdlib_ast_only() -> None:
    """No runtime dependency may creep in: `ast` and the SARIF fingerprint,
    nothing else new under the sun."""

    import ranex.foundation.antislop as module

    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    imports = {
        node.names[0].name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    } | {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    assert imports <= {
        "__future__", "argparse", "ast", "collections.abc", "dataclasses",
        "os", "pathlib", "sys",
        "ranex.foundation.atomic_writer",
        "ranex.foundation.canonical",
        "ranex.foundation.scan_results",
    }
