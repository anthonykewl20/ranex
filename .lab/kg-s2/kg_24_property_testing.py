"""Round-trip properties for a tiny CSV codec."""
from __future__ import annotations

import csv
import io
from collections.abc import Sequence


def encode(rows: Sequence[Sequence[str]]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
    writer.writerows(rows)
    return buffer.getvalue()


def decode(text: str) -> list[list[str]]:
    reader = csv.reader(io.StringIO(text))
    return [row for row in reader]


def roundtrips(rows: Sequence[Sequence[str]]) -> bool:
    return decode(encode(rows)) == [list(row) for row in rows]


def quoted_when_needed(rows: Sequence[Sequence[str]]) -> bool:
    text = encode(rows)
    has_commas = any("," in cell for row in rows for cell in row)
    quoted = '"' in text
    return not has_commas or quoted
