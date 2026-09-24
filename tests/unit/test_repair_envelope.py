"""The repair envelope: bounded advisory repair detail at the read channel.

SLICE-092 / C1+C6. The envelope tells an agent WHAT failed and WHERE —
failing IDs, assertion text, file:line, repro argv, next-rung pointers —
and never proposes a fix. It is advisory read-channel bytes: no renderer
here signs, verifies, or admits anything, and no function in this module
may be importable from the evidence path.
"""

from __future__ import annotations

import json

import pytest

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.suite_results import failure_locations
from ranex.governed_execution.repair_envelope import (
    ENVELOPE_SCHEMA,
    envelope_from_projection,
    envelope_from_suite,
    envelope_packet_bytes,
    next_rung_lines,
    render_packet_text,
    validate_repair_envelope,
)

REPRO = "/usr/bin/python3 -m pytest -q governance/suite_results.xml"

FAILING_JUNIT = b"""<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="3" failures="1" errors="0" skipped="1">
  <properties><property name="ranex.pytest_observer" value="1"/></properties>
  <testcase classname="tests.test_six" name="test_one" time="0.001"/>
  <testcase classname="tests.test_six" name="test_two_off" time="0.002">
    <failure message="assert 1 == 2" type="AssertionError">self = &lt;tests.test_six&gt;
    def test_two_off():
&gt;       assert six.int2byte(1) == 2
E       assert 1 == 2
tests/test_six.py:12: AssertionError</failure>
  </testcase>
  <testcase classname="tests.test_six" name="test_skipped" time="0.000">
    <skipped type="pytest.skip" message="collection skipped"/>
  </testcase>
</testsuite>
"""


class TestFailureLocations:
    def test_extracts_id_assertion_and_file_line(self) -> None:
        detail = failure_locations(FAILING_JUNIT, require_pytest_observer=True)
        assert detail["non_passed_count"] == 2  # the failure and the skip
        assert detail["failures"] == [
            {
                "id": "tests/test_six.py::test_two_off",
                "assertion": "assert 1 == 2",
                "at": "tests/test_six.py:12",
            }
        ]

    def test_error_outcomes_carry_location_when_present(self) -> None:
        junit = (
            b'<testsuite name="pytest" tests="1" errors="1">'
            b'<testcase classname="tests.test_broken" name="test_import">'
            b'<error message="ImportError: no module named gone">tests/test_broken.py:3: '
            b"ImportError: no module named gone</error></testcase></testsuite>"
        )
        detail = failure_locations(junit)
        assert detail["failures"][0]["id"] == "tests/test_broken.py::test_import"
        assert detail["failures"][0]["at"] == "tests/test_broken.py:3"
        assert detail["failures"][0]["assertion"] == "ImportError: no module named gone"

    def test_no_location_line_leaves_at_empty_not_guessed(self) -> None:
        junit = (
            b'<testsuite name="pytest" tests="1" failures="1">'
            b'<testcase classname="tests.test_x" name="test_plain">'
            b'<failure message="boom">no frames here</failure>'
            b"</testcase></testsuite>"
        )
        detail = failure_locations(junit)
        assert detail["failures"] == [
            {"id": "tests/test_x.py::test_plain", "assertion": "boom", "at": ""}
        ]

    def test_refuses_duplicate_ids(self) -> None:
        junit = (
            b'<testsuite name="pytest" tests="2" failures="2">'
            b'<testcase classname="tests.t" name="dup"><failure message="a">x</failure></testcase>'
            b'<testcase classname="tests.t" name="dup"><failure message="b">y</failure></testcase>'
            b"</testsuite>"
        )
        with pytest.raises(ValueError, match="duplicate test ID"):
            failure_locations(junit)

    def test_refuses_dtd_declarations(self) -> None:
        junit = b'<?xml version="1.0"?><!DOCTYPE testsuite [<!ENTITY x "y">]><testsuite/>'
        with pytest.raises(ValueError, match="DTD and entity declarations are refused"):
            failure_locations(junit)

    def test_refuses_missing_pytest_observer_when_required(self) -> None:
        junit = b'<?xml version="1.0"?><testsuite name="pytest" tests="0"/>'
        with pytest.raises(ValueError, match="E-PYTEST-OBSERVER-ABSENT"):
            failure_locations(junit, require_pytest_observer=True)


class TestEnvelopeFromSuite:
    def test_delegate_capture_has_honest_verdict_absence(self) -> None:
        envelope = envelope_from_suite(repro_argv=REPRO, junit_bytes=FAILING_JUNIT)
        assert envelope["schema"] == ENVELOPE_SCHEMA
        assert envelope["verdict"] is None
        assert envelope["verdict_record_digest"] is None
        assert envelope["causes"] == []
        assert envelope["junit_retained"] is True
        assert envelope["failure_count"] == 2
        assert envelope["repro_argv"] == REPRO
        validate_repair_envelope(envelope)

    def test_no_junit_is_absent_not_empty_detail(self) -> None:
        envelope = envelope_from_suite(repro_argv=REPRO, junit_bytes=None)
        assert envelope["junit_retained"] is False
        assert envelope["failures"] == []
        assert envelope["failure_count"] == 0
        validate_repair_envelope(envelope)

    def test_failures_bounded_to_sixteen_with_honest_count(self) -> None:
        cases = "".join(
            f'<testcase classname="tests.test_many" name="test_{index:02d}">'
            f'<failure message="assert {index}">tests/test_many.py:{index}: AssertionError'
            "</failure></testcase>"
            for index in range(20)
        )
        junit = f'<testsuite name="pytest" tests="20" failures="20">{cases}</testsuite>'.encode()
        envelope = envelope_from_suite(repro_argv=REPRO, junit_bytes=junit)
        assert envelope["failure_count"] == 20
        assert len(envelope["failures"]) == 16
        assert envelope["failures"][0]["id"] == "tests/test_many.py::test_00"
        assert envelope["failures"][-1]["id"] == "tests/test_many.py::test_15"

    def test_assertions_bounded_to_two_hundred_chars(self) -> None:
        long_message = "x" * 900
        junit = (
            '<testsuite name="pytest" tests="1" failures="1">'
            f'<testcase classname="tests.test_long" name="test_long">'
            f'<failure message="{long_message}">tests/test_long.py:1: AssertionError'
            "</failure></testcase></testsuite>"
        ).encode()
        envelope = envelope_from_suite(repro_argv=REPRO, junit_bytes=junit)
        assert len(envelope["failures"][0]["assertion"]) == 200

    def test_identical_input_renders_byte_identical_envelopes(self) -> None:
        renders = [
            envelope_packet_bytes(envelope_from_suite(repro_argv=REPRO, junit_bytes=FAILING_JUNIT))
            for _ in range(3)
        ]
        assert renders[0] == renders[1] == renders[2]


class TestEnvelopeFromProjection:
    def _projected(self) -> dict[str, object]:
        return {
            "verdict": "FAIL",
            "gate_id": "landing",
            "subject_digest": "sha256:" + "a" * 64,
            "catalog_digest": "sha256:" + "b" * 64,
            "approver_id": "approver",
            "failing_rule": "all-required-claims",
            "missing_claims": ["tests-executed"],
            "considered": [],
            "causes": [
                {
                    "claim_id": "tests-executed",
                    "cause": "failed",
                    "detail": "non-passed: 2; missing: 0",
                }
            ],
            "rejections": [],
            "self_approval": False,
            "reason": "claim tests-executed failed",
            "journal_head": "sha256:" + "c" * 64,
            "record_digest": "sha256:" + "d" * 64,
        }

    def _evidence(self, command: str = REPRO, non_passed: int = 2):
        class _Record:
            def __init__(self) -> None:
                self.claim_id = "tests-executed"
                self.command = command
                self.suite_results = {
                    "manifest_digest": "sha256:" + "0" * 64,
                    "counts": {"passed": 0, "skipped": 0, "failed": 2, "errors": 0,
                               "xfailed": 0, "xpassed": 0},
                    "non_passed": [
                        [f"tests/test_six.py::test_{i}", "failed"] for i in range(non_passed)
                    ],
                    "missing": [],
                    "extra_count": 0,
                    "outcome_digest": "sha256:" + "1" * 64,
                }

        return [_Record()]

    def test_composes_causes_verdict_and_digest_binding(self) -> None:
        envelope = envelope_from_projection(
            projected=self._projected(),
            evidence=self._evidence(),
            junit_bytes=FAILING_JUNIT,
        )
        assert envelope["verdict"] == "FAIL"
        assert envelope["verdict_record_digest"] == self._projected()["record_digest"]
        assert envelope["causes"] == self._projected()["causes"]
        assert envelope["repro_argv"] == REPRO
        assert envelope["failure_count"] == 2
        assert envelope["failures"][0]["id"] == "tests/test_six.py::test_two_off"
        validate_repair_envelope(envelope)

    def test_no_junit_falls_back_to_summary_count_without_detail(self) -> None:
        envelope = envelope_from_projection(
            projected=self._projected(),
            evidence=self._evidence(),
            junit_bytes=None,
        )
        assert envelope["junit_retained"] is False
        assert envelope["failures"] == []
        assert envelope["failure_count"] == 2  # from the admitted suite summary

    def test_no_suite_evidence_leaves_repro_absent_honestly(self) -> None:
        envelope = envelope_from_projection(
            projected=self._projected(),
            evidence=[],
            junit_bytes=None,
        )
        assert envelope["repro_argv"] == ""
        assert envelope["next_rung"] == []
        validate_repair_envelope(envelope)

    def test_pass_verdict_renders_empty_failure_envelope(self) -> None:
        projected = self._projected()
        projected["verdict"] = "PASS"
        projected["causes"] = []
        projected["missing_claims"] = []
        envelope = envelope_from_projection(
            projected=projected,
            evidence=self._evidence(non_passed=0),
            junit_bytes=None,
        )
        assert envelope["verdict"] == "PASS"
        assert envelope["failures"] == []
        assert envelope["failure_count"] == 0


class TestNextRung:
    def test_ladder_orders_l0_l1_l2(self) -> None:
        failures = [
            {"id": "tests/test_a.py::test_one", "assertion": "", "at": "src/mod.py:10"},
            {"id": "tests/test_a.py::test_two", "assertion": "", "at": "src/mod.py:20"},
        ]
        rungs = next_rung_lines(REPRO, failures)
        assert rungs[0] == "L0 /usr/bin/python3 -m py_compile src/mod.py"
        assert rungs[1] == f"L1 {REPRO} tests/test_a.py::test_one tests/test_a.py::test_two"
        assert rungs[2] == f"L2 {REPRO}"

    def test_l1_carries_at_most_eight_ids(self) -> None:
        failures = [
            {"id": f"tests/test_b.py::test_x{index:02d}", "assertion": "", "at": ""} for index in range(9)
        ]
        rungs = next_rung_lines(REPRO, failures)
        l1 = next(rung for rung in rungs if rung.startswith("L1 "))
        targeted = l1.removeprefix(f"L1 {REPRO} ").split()
        assert targeted == [failure["id"] for failure in failures[:8]]

    def test_no_python_interpreter_omits_l0(self) -> None:
        failures = [{"id": "tests/test_c.py::test_x", "assertion": "", "at": "src/x.py:1"}]
        rungs = next_rung_lines("/usr/bin/make test", failures)
        assert [rung[:2] for rung in rungs] == ["L1", "L2"]

    def test_no_located_files_omits_l0(self) -> None:
        failures = [{"id": "tests/test_d.py::test_y", "assertion": "", "at": ""}]
        rungs = next_rung_lines(REPRO, failures)
        assert [rung[:2] for rung in rungs] == ["L1", "L2"]

    def test_empty_repro_leaves_only_l2_absent(self) -> None:
        assert next_rung_lines(REPRO, []) == [f"L2 {REPRO}"]
        assert next_rung_lines("", []) == []


class TestValidation:
    def _minimal(self) -> dict[str, object]:
        return envelope_from_suite(repro_argv=REPRO, junit_bytes=None)

    def test_unknown_key_refused(self) -> None:
        value = {**self._minimal(), "extra": 1}
        with pytest.raises(ValueError, match="exactly"):
            validate_repair_envelope(value)

    def test_missing_key_refused(self) -> None:
        value = self._minimal()
        del value["repro_argv"]
        with pytest.raises(ValueError, match="exactly"):
            validate_repair_envelope(value)

    def test_bad_verdict_value_refused(self) -> None:
        value = {**self._minimal(), "verdict": "MAYBE"}
        with pytest.raises(ValueError, match="verdict"):
            validate_repair_envelope(value)

    def test_open_failure_entry_shape_refused(self) -> None:
        value = self._minimal()
        value["failures"] = [{"id": "x", "assertion": "", "at": "", "hint": "fix me"}]
        with pytest.raises(ValueError, match="failure"):
            validate_repair_envelope(value)

    def test_failure_count_below_carried_refused(self) -> None:
        value = envelope_from_suite(repro_argv=REPRO, junit_bytes=FAILING_JUNIT)
        value["failure_count"] = 0
        with pytest.raises(ValueError, match="failure_count"):
            validate_repair_envelope(value)

    def test_non_ladder_rung_refused(self) -> None:
        value = self._minimal()
        value["next_rung"] = ["just run it again"]
        with pytest.raises(ValueError, match="rung"):
            validate_repair_envelope(value)


class TestPacket:
    def test_packet_text_names_verdict_causes_failures_repro_rungs(self) -> None:
        projection = TestEnvelopeFromProjection()
        envelope = envelope_from_projection(
            projected=projection._projected(),
            evidence=projection._evidence(),
            junit_bytes=FAILING_JUNIT,
        )
        text = render_packet_text(envelope)
        assert "VERDICT FAIL" in text
        assert "CAUSE tests-executed: failed" in text
        assert "- tests/test_six.py::test_two_off | assert 1 == 2 | tests/test_six.py:12" in text
        assert f"REPRO {REPRO}" in text
        assert "NEXT L1 " in text

    def test_packet_bytes_are_canonical_json_with_newline(self) -> None:
        envelope = envelope_from_suite(repro_argv=REPRO, junit_bytes=FAILING_JUNIT)
        raw = envelope_packet_bytes(envelope)
        assert raw == canonical_json_bytes(envelope) + b"\n"
        json.loads(raw)

    def test_unretained_junit_says_so_in_the_packet(self) -> None:
        envelope = envelope_from_suite(repro_argv=REPRO, junit_bytes=None)
        assert "junit not retained" in render_packet_text(envelope)
