"""Frozen contract for SLICE-047's shared confinement-result validator.

Imports of the deliberately absent foundation module stay inside `_module()` so
the pre-implementation tree reports ordinary red assertions, not collection
errors; this mirrors the absent-controller import pattern in SLICE-017.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
from copy import deepcopy

import pytest

from ranex.foundation.canonical import canonical_json_bytes


def _sample() -> dict[str, object]:
    return {
        "schema": "ranex-confinement-result-v1",
        "profile_digests": {"runtime": "0" * 64, "host": "1" * 64, "launcher": "2" * 64},
        "namespace_readbacks": {name: "namespace-id" for name in ("user", "mount", "pid", "ipc", "network", "cgroup")},
        "cgroup_readbacks": {"limits": {"pids.max": "16"}, "events": {"populated": 0}, "usage": {"cpu_usage_usec": 1}},
        "command": {"argv_digest": "3" * 64, "exit_code": 0, "no_new_privs": True, "landlock": True, "seccomp": True},
        "teardown": {"cgroup_kill": True, "populated": 0, "cgroup_removed": True},
        "outputs": {"files": [], "bytes": 0, "inodes": 0},
    }


def _module() -> object:
    spec = importlib.util.find_spec("ranex.foundation.confinement_result")
    assert spec is not None, "SLICE-047 foundation validator module is absent"
    return importlib.import_module("ranex.foundation.confinement_result")


def test_validate_confinement_result_returns_value_and_runtime_digest() -> None:
    module = _module()
    value = _sample()
    assert module.validate_confinement_result(canonical_json_bytes(value)) == (value, "0" * 64)


@pytest.mark.parametrize("mutation", ["invalid-json", "object", "schema", "profile-set", "noncanonical", "runtime-63", "runtime-65", "runtime-upper", "command-object", "bool-exit", "live-teardown"])
def test_validate_confinement_result_refuses_every_closed_contract_partition(mutation: str) -> None:
    module = _module()
    value = _sample()
    if mutation == "invalid-json":
        raw = b"{"
    elif mutation == "object":
        raw = b"[]"
    else:
        if mutation == "schema":
            value["schema"] = "ranex-confinement-result-v2"
        elif mutation == "profile-set":
            value["profile_digests"] = {"runtime": "0" * 64, "host": "1" * 64}
        elif mutation == "noncanonical":
            raw = json.dumps(value, indent=2).encode()
        else:
            if mutation.startswith("runtime"):
                runtime = {"runtime-63": "0" * 63, "runtime-65": "0" * 65, "runtime-upper": "A" * 64}[mutation]
                value["profile_digests"] = {"runtime": runtime, "host": "1" * 64, "launcher": "2" * 64}
            elif mutation == "command-object":
                value["command"] = []
            elif mutation == "bool-exit":
                value["command"] = {**value["command"], "exit_code": True}  # type: ignore[arg-type]
            else:
                value["teardown"] = {"cgroup_kill": True, "populated": 1, "cgroup_removed": True}
        if mutation != "noncanonical":
            raw = canonical_json_bytes(value)
    with pytest.raises(module.ConfinementResultError) as refused:
        module.validate_confinement_result(raw)
    assert refused.value.code == "E-C18-RESULT"
    assert str(refused.value).startswith("E-C18-RESULT: ")


def test_confinement_result_bytes_refuses_non_hex_mapping_before_emission() -> None:
    module = _module()
    value = deepcopy(_sample())
    value["profile_digests"] = {"runtime": "g" * 64, "host": "1" * 64, "launcher": "2" * 64}
    with pytest.raises(module.ConfinementResultError) as refused:
        module.confinement_result_bytes(value)
    assert refused.value.code == "E-C18-RESULT"
