"""Pure validation for values crossing the Python/TypeScript boundary."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

_SAFE = 2**53 - 1


def validate_publication_value(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("floats cannot be published")
    if isinstance(value, int) and not isinstance(value, bool) and not -_SAFE <= value <= _SAFE:
        raise ValueError("integer is outside the TypeScript safe range")
    if isinstance(value, str) and any(ord(char) > 0xFFFF for char in value):
        raise ValueError("non-BMP Unicode cannot be published")
    if isinstance(value, Mapping):
        for key, item in value.items():
            validate_publication_value(key)
            validate_publication_value(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            validate_publication_value(item)
