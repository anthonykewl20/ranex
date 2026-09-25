'"""Serializable geometry records."""'
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def distance_to(self, other: Point) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass(frozen=True)
class Segment:
    start: Point
    end: Point

    @property
    def length(self) -> float:
        return self.start.distance_to(self.end)


def encode(segments: list[Segment]) -> str:
    return json.dumps([asdict(s) for s in segments], sort_keys=True)


def decode(payload: str) -> list[Segment]:
    raw = json.loads(payload)
    return [Segment(Point(p["start"]["x"], p["start"]["y"]), Point(p["end"]["x"], p["end"]["y"])) for p in raw]
