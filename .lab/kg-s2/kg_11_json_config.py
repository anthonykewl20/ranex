"""Layered JSON configuration loader."""
from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def merge(base: Mapping[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = dict(base)
    for key, value in overlay.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def load(layers: list[Path]) -> dict[str, Any]:
    config: dict[str, Any] = {}
    for layer in layers:
        if not layer.exists():
            continue
        config = merge(config, json.loads(layer.read_text(encoding="utf-8")))
    return config


def require(config: Mapping[str, Any], dotted: str) -> Any:
    node: Any = config
    for part in dotted.split("."):
        if not isinstance(node, Mapping) or part not in node:
            raise KeyError(f"missing configuration key: {dotted}")
        node = node[part]
    return node
