"""Load one gate definition from a YAML catalog.

Deliberately loads from YAML and **not** from `architecture/contracts/`.
That generated registry holds readiness gates
(`evidence_role` -> tier) while this kernel needs action gates
(`action` -> rules): five fields would have to be invented. Inventing them and
calling the result "derived from the contract tree" would be a false closure.

Closing that gap needs someone to decide what the action gates are and author
them. That decision is deferred, and this loader does not pretend otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ranex.foundation.canonical import command_digest


@dataclass(frozen=True, slots=True)
class SliceClaimDefinition:
    """A policy-owned claim identifier and the argv that satisfies it.

    argv as a sequence, never a string: comparison then needs no shell parsing,
    and argument order is structural rather than a parsing accident. The literal
    stays legible in review; the digest is what the kernel compares.
    """

    claim_id: str
    command: tuple[str, ...]
    results_artifact: str | None = None
    qualification_report: str | None = None

    @property
    def command_digest(self) -> str:
        """What the kernel compares. The same function `run` records with."""

        return command_digest(self.command)


@dataclass(frozen=True, slots=True)
class SliceGateDefinition:
    """Adapter output expressed only in policy-owned scalar values."""

    gate_id: str
    rule_id: str
    required_claims: tuple[SliceClaimDefinition, ...]
    blocking: bool


class _UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently taking the last one."""


def _no_duplicates(
    loader: yaml.SafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate key in gate catalog: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(  # type: ignore[no-untyped-call]
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates
)


_CLAIM_KEYS = {"claim_id", "command", "results_artifact", "qualification_report"}

_SHAPE = "{claim_id: <id>, command: [<argv>, ...]}"


def _claim_definition(gate_id: str, entry: Any) -> SliceClaimDefinition:
    """One `required_claims` entry, or raise.

    Absence blocks, at construction. A claim with no declared command is a claim
    whose satisfaction is undefined, and an undefined claim cannot block — so
    every shape that fails to name an argv is refused here, where the operator's
    file is read, rather than defaulted into a gate that decorates.
    """

    if not isinstance(entry, dict):
        # The pre-SLICE-003 shape lands here: a bare string was coerced with
        # `str(claim)` and declared nothing about what satisfying it required.
        raise ValueError(
            f"gate {gate_id!r}: required_claims entry {entry!r} must be a mapping "
            f"of the form {_SHAPE}; a claim that names no command has no defined "
            "way to be satisfied"
        )

    unknown = set(entry) - _CLAIM_KEYS
    if unknown:
        # The claim entry is part of the trust root now, so `waiver: yes` must
        # not be silently ignored here any more than it is on the gate.
        raise ValueError(
            f"gate {gate_id!r}: unknown keys in required_claims entry: "
            f"{sorted(unknown)}"
        )

    claim_id = entry.get("claim_id")
    if not isinstance(claim_id, str) or not claim_id.strip():
        raise ValueError(
            f"gate {gate_id!r}: required_claims entry must carry a non-empty "
            f"string claim_id, got {claim_id!r}"
        )

    if "command" not in entry:
        raise ValueError(
            f"gate {gate_id!r}: claim {claim_id!r} declares no command, so what "
            f"would satisfy it is undefined; write it as {_SHAPE}"
        )

    command = entry["command"]
    if not isinstance(command, list) or not command:
        raise ValueError(
            f"gate {gate_id!r}: claim {claim_id!r} must declare command as a "
            f"non-empty list of argv strings, got {command!r}. A string would "
            "need shell parsing and an empty list binds nothing"
        )
    if not all(isinstance(part, str) and part for part in command):
        raise ValueError(
            f"gate {gate_id!r}: claim {claim_id!r} declares a command that is not "
            f"an argv — every element must be a non-empty string, got {command!r}"
        )

    results_artifact: str | None = None
    if "results_artifact" in entry:
        candidate = entry["results_artifact"]
        if (
            not isinstance(candidate, str)
            or not candidate
            or Path(candidate).is_absolute()
            or any(part == ".." for part in Path(candidate).parts)
        ):
            raise ValueError(
                f"gate {gate_id!r}: claim {claim_id!r} results_artifact must be "
                "a non-empty relative path confined below the repository"
            )
        token = f"--junitxml={candidate}"
        if token not in command:
            raise ValueError(
                f"gate {gate_id!r}: claim {claim_id!r} must bind results_artifact "
                f"with the exact argv token {token!r}"
            )
        results_artifact = candidate

    qualification_report: str | None = None
    if "qualification_report" in entry:
        if results_artifact is not None:
            raise ValueError(
                f"gate {gate_id!r}: claim {claim_id!r} results_artifact and "
                "qualification_report are mutually exclusive"
            )
        candidate = entry["qualification_report"]
        if (
            not isinstance(candidate, str)
            or not candidate
            or Path(candidate).is_absolute()
            or any(part == ".." for part in Path(candidate).parts)
        ):
            raise ValueError(
                f"gate {gate_id!r}: claim {claim_id!r} qualification_report must be "
                "a non-empty relative path confined below the repository"
            )
        token = f"--report={candidate}"
        if token not in command:
            raise ValueError(
                f"gate {gate_id!r}: claim {claim_id!r} must bind "
                f"qualification_report with the exact argv token {token!r}"
            )
        qualification_report = candidate

    return SliceClaimDefinition(
        claim_id=claim_id,
        command=tuple(command),
        results_artifact=results_artifact,
        qualification_report=qualification_report,
    )


def load_gate(
    catalog_path: Path,
    gate_id: str,
) -> SliceGateDefinition:
    """Return the named gate, reading the working tree.

    Kept for callers that mean "the file at this path". The CLI is no longer
    one of them — it parses the bytes git records, so the catalog that decides
    a verdict cannot be swapped between the trust-root check and the load.
    """

    return load_gate_text(Path(catalog_path).read_text(encoding="utf-8"), gate_id)


def load_gate_text(text: str, gate_id: str) -> SliceGateDefinition:
    """Return the named gate from catalog text already in hand, or raise.

    A malformed catalog never yields a gate. Nothing here touches a filesystem:
    which bytes are the catalog is the caller's decision and cannot be revisited.
    """

    try:
        document = yaml.load(text, Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        # Wrapped here, in the adapter that chose YAML, rather than left to
        # escape into the CLI. An unwrapped `YAMLError` reached `main()` as a
        # traceback, and an uncaught exception exits 1 — which is EXIT_FAIL, the
        # code meaning "the gate was not satisfied". A catalog that could not be
        # parsed evaluated nothing, and must never share an answer with a gate
        # that was evaluated and refused. The keyring loader already wraps the
        # identical input class; the other half of the trust root now matches.
        raise ValueError(f"gate catalog is not valid YAML: {exc}") from exc
    if not isinstance(document, dict):
        raise ValueError("gate catalog must be a mapping")

    gates = document.get("gates")
    if not isinstance(gates, list) or not gates:
        raise ValueError("gate catalog must declare a non-empty 'gates' list")

    matches = [g for g in gates if isinstance(g, dict) and g.get("gate_id") == gate_id]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one gate {gate_id!r}, found {len(matches)}")

    entry = matches[0]
    allowed = {"gate_id", "rule_id", "required_claims", "blocking"}
    unknown = set(entry) - allowed
    if unknown:
        raise ValueError(f"unknown keys in gate {gate_id!r}: {sorted(unknown)}")

    claims = entry.get("required_claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError(f"gate {gate_id!r} must declare required_claims")
    blocking = entry.get("blocking", True)
    if blocking is not True:
        raise ValueError(f"gate {gate_id!r} must be blocking")

    required_claims = tuple(_claim_definition(gate_id, claim) for claim in claims)

    # `Gate` refuses duplicates too, but the ambiguity is written here: two
    # entries for one claim mean one of the two commands silently decides it,
    # and that has no defined answer to give the layer above.
    seen = [claim.claim_id for claim in required_claims]
    duplicates = sorted({name for name in seen if seen.count(name) > 1})
    if duplicates:
        raise ValueError(
            f"gate {gate_id!r} declares required_claims more than once: "
            f"{', '.join(duplicates)}; one claim names one command"
        )

    return SliceGateDefinition(
        gate_id=str(entry["gate_id"]),
        rule_id=str(entry["rule_id"]),
        required_claims=required_claims,
        blocking=True,
    )
