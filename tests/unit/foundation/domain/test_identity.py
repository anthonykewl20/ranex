from __future__ import annotations

import pytest

from ranex.foundation.identity import Identity

RUN_ID = "run_01890f47-25a1-7cc1-98b3-5f5f6bb25af7"


def test_identity_parses_canonical_prefixed_uuid7() -> None:
    identity = Identity.parse(RUN_ID, expected_prefix="run")

    assert str(identity) == RUN_ID
    assert identity.prefix == "run"
    assert identity.uuid.version == 7


@pytest.mark.parametrize(
    ("value", "expected_prefix"),
    [
        (RUN_ID, "work"),
        ("run_01890f47-25a1-4cc1-98b3-5f5f6bb25af7", "run"),
        ("RUN_01890f47-25a1-7cc1-98b3-5f5f6bb25af7", "run"),
        ("run_not-a-uuid", "run"),
    ],
)
def test_identity_rejects_wrong_kind_or_noncanonical_value(
    value: str,
    expected_prefix: str,
) -> None:
    with pytest.raises(ValueError):
        Identity.parse(value, expected_prefix=expected_prefix)
