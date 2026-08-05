"""SLICE-009 criterion 10 — the suite-results rule has the same forgery boundary.

This file proves a **limit**, not a defence.

Everything SLICE-009 claims about skips, missing IDs and structured results can
still be true while a hostile tree fabricates the junitxml it asked pytest to
write. The rule reads the artifact structurally; it does not prove who authored
it or whether the process that wrote it was honest.

Do not "fix" the passing forgery test below by making it fail accidentally. If a
future change closes the boundary, ADR-011 and this file both need a deliberate
rewrite. If the change only breaks the demonstration, it has hidden a limit the
product promises to state plainly.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from ranex.foundation.canonical import command_digest
from ranex.governed_execution.domain.verdict import Claim, Evidence, Gate, Verdict, evaluate

SUBJECT = "sha256:" + "a" * 64
COMMAND = ["uv", "run", "pytest", "-q", "--junitxml=artifacts/junit.xml"]
COMMAND_DIGEST = command_digest(COMMAND)


@pytest.fixture()
def suite_api():
    return importlib.import_module("ranex.foundation.suite_results")


def xml_case(path: str, name: str) -> str:
    classname = path.removesuffix(".py").replace("/", ".")
    return f'<testcase classname="{classname}" name="{name}" time="0.000" />'


def junitxml(*cases: str) -> bytes:
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<testsuites><testsuite name="pytest">'
        + "".join(cases)
        + "</testsuite></testsuites>"
    ).encode("utf-8")


def test_a_forged_all_pass_artifact_still_satisfies_the_rule(suite_api) -> None:
    """Documented boundary: the parser trusts the bytes it is given.

    This is the suite-results analogue of
    `test_slice006_approved_wheel_can_lie.py`: a fabricated artifact that names
    every manifest ID as passed still satisfies the claim. The slice closes
    skip-as-success, not artifact forgery.
    """

    frozen = {
        "suite": [
            "tests/unit/test_x.py::test_one",
            "tests/unit/test_x.py::test_two",
        ],
        "expected_skips": {},
    }
    forged = junitxml(
        xml_case("tests/unit/test_x.py", "test_one"),
        xml_case("tests/unit/test_x.py", "test_two"),
    )
    parsed = suite_api.suite_results_from_junitxml(forged, frozen)
    result = evaluate(
        Gate(
            gate_id="landing",
            rule_id="TESTS_EXECUTED",
            required_claims=(
                Claim(
                    claim_id="tests-executed",
                    command_digest=COMMAND_DIGEST,
                    results_required=True,
                    manifest_digest=suite_api.manifest_digest(frozen),
                    expected_ids=tuple(frozen["suite"]),
                    expected_skips={},
                ),
            ),
            blocking=True,
        ),
        (
            Evidence(
                claim_id="tests-executed",
                subject_digest=SUBJECT,
                producer_id="worker",
                command=" ".join(COMMAND),
                command_digest=COMMAND_DIGEST,
                executable_path="/usr/bin/uv",
                exit_code=0,
                suite_results=parsed,
            ),
        ),
        subject_digest=SUBJECT,
        approver_id="reviewer",
    )

    assert result.verdict is Verdict.PASS


def test_entity_expansion_is_refused_never_expanded(suite_api) -> None:
    frozen = {
        "suite": ["tests/unit/test_x.py::test_one"],
        "expected_skips": {},
    }
    # The traditional billion-laughs shape. A safe parser refuses the DTD or
    # hits a bounded amplification limit; it must never materialise the final
    # billion repetitions in the failure text.
    payload = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
 <!ENTITY lol "lol">
 <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
 <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
 <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
 <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
 <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
 <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
 <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
 <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
 <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<testsuites>
  <testsuite name="pytest">
    <testcase classname="tests.unit.test_x" name="test_one">
      <failure>&lol9;</failure>
    </testcase>
  </testsuite>
</testsuites>
"""

    with pytest.raises(ValueError):
        suite_api.suite_results_from_junitxml(payload, frozen)


def test_oversized_artifact_is_refused(suite_api, tmp_path: Path) -> None:
    path = tmp_path / "oversized.xml"
    with path.open("wb") as handle:
        handle.write(b"<testsuites>")
        handle.truncate((50 * 1024 * 1024) + 1)

    with pytest.raises(ValueError, match="50"):
        suite_api.parse_results_artifact(
            path,
            {"suite": ["tests/unit/test_x.py::test_one"], "expected_skips": {}},
        )
