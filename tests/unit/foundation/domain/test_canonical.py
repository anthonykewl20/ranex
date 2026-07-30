from __future__ import annotations

import math

import pytest

from ranex.foundation.canonical import canonical_json, canonical_json_bytes


def test_canonical_json_is_compact_sorted_and_unicode_preserving() -> None:
    value = {
        "z": [3, {"β": "snowman ☃"}],
        "a": True,
    }

    assert canonical_json(value) == '{"a":true,"z":[3,{"β":"snowman ☃"}]}'
    assert canonical_json_bytes(value) == (
        b'{"a":true,"z":[3,{"\xce\xb2":"snowman \xe2\x98\x83"}]}'
    )


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_canonical_json_rejects_non_finite_numbers(value: float) -> None:
    with pytest.raises(ValueError):
        canonical_json({"unsafe": value})
