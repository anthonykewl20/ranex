"""Load the committed keyring that says which public key belongs to whom.

This file is the trust root. It is committed so that review is the control on
it, and every failure path here is loud rather than empty.

An empty mapping would be the worst possible failure mode: every record would be
rejected for an unknown producer, the gate would FAIL, and the output would look
exactly like a project that had simply not run its tests yet. A broken trust
root must never be mistakable for honest absence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ranex.foundation.signing import is_public_key


class KeyringError(ValueError):
    """The keyring cannot be trusted, so nothing may be admitted using it."""


class _NoDuplicateKeys(yaml.SafeLoader):
    """YAML silently keeps the last of a repeated key.

    Left alone, appending one line to this file would quietly replace a
    producer's key with no diff conflict and no error — a trust-root change
    disguised as an addition.
    """

    def construct_mapping(self, node: Any, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            # A complex key (`? [a, b]`) constructs to a list, and membership in
            # a set raises TypeError on anything unhashable. Left uncaught it
            # escapes every `except` in `load_keyring` and breaks the contract
            # stated there: a keyring this loader cannot fully trust fails as
            # KeyringError. A caller written to that contract would crash where
            # it meant to refuse — two characters of YAML for a trust-root DoS.
            try:
                duplicate = key in seen
                # `seen.add` belongs inside the guard, not after it. CPython
                # silently retries a failed `set` lookup as a `frozenset`, so a
                # `!!set` key answers `key in seen` with False and never raises;
                # `set.add` has no such retry and raised TypeError one line
                # later, outside every handler. The guard that looked complete
                # closed only the door it had been shown.
                seen.add(key)
            except TypeError as exc:
                raise KeyringError(
                    f"keyring entry {key!r} is not a usable producer id: {exc}"
                ) from exc
            if duplicate:
                raise KeyringError(f"duplicate entry for {key!r} in the keyring")
        return super().construct_mapping(node, deep=deep)


def load_keyring(path: Path | str) -> dict[str, str]:
    """Return producer_id -> `ed25519:<base64>`, reading the working tree.

    Kept for callers that genuinely mean "the file at this path". The CLI is no
    longer one of them: it hands `load_keyring_text` the bytes git records, so
    that the keyring which decides a verdict is never re-read from a name the
    observed party can repoint between the check and the load.
    """

    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise KeyringError(f"cannot read the keyring at {path}: {exc}") from exc
    return load_keyring_text(text, path)


def load_keyring_text(text: str, source: object) -> dict[str, str]:
    """Return producer_id -> `ed25519:<base64>` from keyring text already in hand.

    `source` names where the text came from, for error messages only — nothing
    here reads it. That is the point: the caller has already decided which bytes
    are trustworthy, and this function cannot go behind that decision.
    """

    path = source
    try:
        document = yaml.load(text, Loader=_NoDuplicateKeys)
    except KeyringError:
        raise
    except yaml.YAMLError as exc:
        raise KeyringError(f"keyring at {path} is not valid YAML: {exc}") from exc

    if not isinstance(document, dict):
        raise KeyringError(f"keyring at {path} must be a mapping")
    if "producers" not in document:
        raise KeyringError(f"keyring at {path} has no 'producers' mapping")

    producers = document["producers"]
    if not isinstance(producers, dict):
        raise KeyringError(f"'producers' in {path} must be a mapping")
    # `producers: {}` is a mapping, so it passes the shape check, loops zero
    # times, and returns the empty keyring this module's docstring says must
    # never be returned: every record rejects as an unknown producer, the gate
    # FAILs, and the output is indistinguishable from a project that has not run
    # its tests. Deleting the contents of the trust root must be as loud as
    # deleting the file.
    if not producers:
        raise KeyringError(
            f"'producers' in {path} is empty; an empty keyring rejects every "
            "record as an unknown producer, which reads as work never done"
        )

    keyring: dict[str, str] = {}
    owner_of: dict[str, str] = {}
    for producer_id, public_key in producers.items():
        if not isinstance(producer_id, str) or not producer_id.strip():
            raise KeyringError(f"producer id {producer_id!r} must be a non-empty string")
        if not is_public_key(public_key):
            raise KeyringError(
                f"producer {producer_id!r} has a malformed public key; "
                "expected ed25519:<base64> of 32 bytes"
            )

        # One key, one identity. If two producers share a key, whoever holds the
        # private half signs as either of them: they produce evidence as one and
        # approve as the other, and no-self-approval compares two different
        # strings and permits it. Refused here so the attack is unrepresentable
        # rather than merely discouraged by review.
        if public_key in owner_of:
            raise KeyringError(
                f"producers {owner_of[public_key]!r} and {producer_id!r} share a "
                "public key; one key may serve only one producer, or "
                "no-self-approval can be defeated by signing as either identity"
            )
        owner_of[public_key] = producer_id
        keyring[producer_id] = public_key

    return keyring


@dataclass(frozen=True, slots=True)
class TrustKeyring:
    producers: dict[str, str]
    verdict_signer_id: str
    verdict_signer_public_key: str


def load_trust_keyring(path: Path | str) -> TrustKeyring:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, yaml.YAMLError) as exc:
        raise KeyringError(f"cannot load keyring at {path}: {exc}") from exc
    return load_trust_keyring_text(text, path)


def load_trust_keyring_text(text: str, source: object) -> TrustKeyring:
    try:
        document = yaml.load(text, Loader=_NoDuplicateKeys)
    except (KeyringError, yaml.YAMLError) as exc:
        raise KeyringError(f"cannot load keyring at {source}: {exc}") from exc
    if not isinstance(document, dict) or set(document) != {"producers", "verdict_signer"}:
        raise KeyringError("keyring must contain producers and verdict_signer")
    producers = load_keyring_text(yaml.safe_dump({"producers": document["producers"]}), source)
    signer = document["verdict_signer"]
    if not isinstance(signer, dict) or set(signer) != {"id", "public_key"}:
        raise KeyringError("verdict_signer must contain exactly id and public_key")
    if signer["id"] != "kernel-verdict-signer" or not is_public_key(signer["public_key"]):
        raise KeyringError("verdict_signer is malformed")
    if signer["id"] in producers or signer["public_key"] in producers.values():
        raise KeyringError("verdict_signer may not alias a producer")
    return TrustKeyring(producers, signer["id"], signer["public_key"])
