"""Closed observation checkpoint record validation, shared by signed readers."""
from pathlib import Path
from typing import Any

GENESIS = "sha256:" + "0" * 64


def validate_checkpoint(value: Any) -> bool:
    return (
        isinstance(value, dict) and set(value) == {"log_id", "head", "position"}
        and isinstance(value["log_id"], str) and Path(value["log_id"]).is_absolute()
        and isinstance(value["head"], str) and len(value["head"]) == 71
        and value["head"].startswith("sha256:")
        and all(c in "0123456789abcdef" for c in value["head"][7:])
        and type(value["position"]) is int and value["position"] >= 0
        and ((value["position"] == 0) == (value["head"] == GENESIS))
    )
