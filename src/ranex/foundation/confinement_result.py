"""Closed validation contract for strict-local confinement results."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import NoReturn

from ranex.foundation.canonical import canonical_json_bytes

E_C18_RESULT = "E-C18-RESULT"


class ConfinementResultError(ValueError):
    """A malformed or incomplete confinement result."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _refuse(detail: str) -> NoReturn:
    raise ConfinementResultError(E_C18_RESULT, detail)


def _validate_envelope(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        _refuse("confinement result must be a JSON object")
    expected = {
        "schema", "profile_digests", "namespace_readbacks", "cgroup_readbacks",
        "command", "teardown", "outputs",
    }
    if set(value) != expected or value.get("schema") != "ranex-confinement-result-v1":
        _refuse("confinement result has a missing, extra, or invalid field")
    return value


def _validate_value(value: object) -> tuple[dict[str, object], str]:
    result = _validate_envelope(value)
    if result.get("teardown") != {"cgroup_kill": True, "populated": 0, "cgroup_removed": True}:
        _refuse("confinement result does not prove total teardown")
    profiles = result.get("profile_digests")
    if not isinstance(profiles, dict) or set(profiles) != {"runtime", "host", "launcher"}:
        _refuse("confinement profile digests are invalid")
    for name in ("runtime", "host", "launcher"):
        digest = profiles.get(name)
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            _refuse(f"{name} confinement profile digest is invalid")
    command = result.get("command")
    if not isinstance(command, dict) or type(command.get("exit_code")) is not int:
        _refuse("confinement command exit code is invalid")
    return result, profiles["runtime"]


def validate_confinement_result(raw: bytes) -> tuple[dict[str, object], str]:
    """Accept only canonical bytes for a complete, closed result schema."""

    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConfinementResultError(
            E_C18_RESULT, f"cannot parse confinement result: {exc}"
        ) from exc
    result = _validate_envelope(value)
    if raw != canonical_json_bytes(result):
        _refuse("confinement result is not canonical JSON")
    return _validate_value(result)


def confinement_result_bytes(value: Mapping[str, object]) -> bytes:
    """Validate an in-memory result before emitting its canonical bytes."""

    result, _runtime_digest = _validate_value(dict(value))
    return canonical_json_bytes(result)
