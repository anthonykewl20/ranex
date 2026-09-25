"""RFC-3339-ish timestamp parsing with named groups."""
from __future__ import annotations

import re
from datetime import datetime

TIMESTAMP = re.compile(
    r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
    r"[Tt ]"
    r"(?P<hour>\d{2}):(?P<minute>\d{2})(?::(?P<second>\d{2})(?P<fraction>\.\d+)?)?"
    r"(?P<tz>[Zz]|[+-]\d{2}:?\d{2})?"
)


def parse(text: str) -> datetime:
    match = TIMESTAMP.fullmatch(text.strip())
    if match is None:
        raise ValueError(f"unparseable timestamp: {text!r}")
    parts = match.groupdict()
    micro = int(float(parts["fraction"] or 0) * 1_000_000)
    return datetime(
        int(parts["year"]),
        int(parts["month"]),
        int(parts["day"]),
        int(parts["hour"]),
        int(parts["minute"]),
        int(parts["second"] or 0),
        micro,
    )
