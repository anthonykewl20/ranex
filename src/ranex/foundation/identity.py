from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

_PREFIX = r"[a-z][a-z0-9_]*"
_UUID7 = (
    r"[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
_IDENTITY_PATTERN = re.compile(rf"^(?P<prefix>{_PREFIX})_(?P<uuid>{_UUID7})$")
_PREFIX_PATTERN = re.compile(rf"^{_PREFIX}$")


@dataclass(frozen=True, slots=True)
class Identity:
    """An opaque canonical Ranex prefix plus UUIDv7 identity."""

    value: str
    prefix: str
    uuid: uuid.UUID

    def __post_init__(self) -> None:
        if not _PREFIX_PATTERN.fullmatch(self.prefix):
            raise ValueError("identity prefix is not canonical")
        if self.uuid.version != 7 or self.uuid.variant != uuid.RFC_4122:
            raise ValueError("identity UUID must be RFC 4122 variant UUIDv7")
        if self.value != f"{self.prefix}_{self.uuid}":
            raise ValueError("identity value does not match its canonical parts")

    @classmethod
    def parse(
        cls,
        value: str,
        *,
        expected_prefix: str | None = None,
    ) -> Identity:
        if not isinstance(value, str):
            raise TypeError("identity must be a string")
        match = _IDENTITY_PATTERN.fullmatch(value)
        if match is None:
            raise ValueError("identity must be a lowercase prefix plus UUIDv7")
        prefix = match.group("prefix")
        if expected_prefix is not None and prefix != expected_prefix:
            raise ValueError(
                f"identity prefix {prefix!r} does not match {expected_prefix!r}"
            )
        parsed_uuid = uuid.UUID(match.group("uuid"))
        return cls(value=value, prefix=prefix, uuid=parsed_uuid)

    def __str__(self) -> str:
        return self.value
