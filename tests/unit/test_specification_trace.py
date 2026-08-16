from __future__ import annotations

import pytest

from ranex.governed_execution.domain.specification_trace import (
    TraceVerificationError,
    parse_trace_comment,
)


def test_comment_parser_accepts_only_the_generated_python_and_ecmascript_form() -> None:
    expected = ("R-1", "T-1", "O-1")
    for line in (
        "# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection=sha256:" + "a" * 64,
        "// ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection=sha256:" + "a" * 64,
    ):
        assert parse_trace_comment(line).ids == expected

    with pytest.raises(TraceVerificationError, match="E-TRACE-001"):
        parse_trace_comment("# ranex-trace: outcome=O-1 rule=R-1 transition=T-1 projection=sha256:" + "a" * 64)


@pytest.mark.parametrize(
    ("line", "code"),
    [
        ("# ranex-trace: rule=* transition=T-1 outcome=O-1 projection=sha256:" + "a" * 64, "E-TRACE-009"),
        ("# ranex-trace: rule=R-2 transition=T-1 outcome=O-1 projection=sha256:" + "a" * 64, "E-TRACE-004"),
        ("# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection=sha256:" + "b" * 64, "E-TRACE-002"),
    ],
)
def test_reference_refusals_have_distinct_stable_codes(line: str, code: str) -> None:
    with pytest.raises(TraceVerificationError) as refused:
        parse_trace_comment(line, ids={"rule": ("R-1",), "transition": ("T-1",), "outcome": ("O-1",)}, projections={"sha256:" + "a" * 64})
    assert refused.value.code == code
