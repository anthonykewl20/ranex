"""Frozen v1 A/B/C specification contracts and byte-level identity helpers."""

from __future__ import annotations

import binascii
import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import NoReturn

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.signing import _decode, _encode

SPEC_PACKET_PAYLOAD_TYPE = "application/vnd.ranex.spec-packet.v1+json"
MANIFEST_PAYLOAD_TYPE = "application/vnd.ranex.generated-artifact-manifest.v1+json"
APPROVAL_PAYLOAD_TYPE = "application/vnd.ranex.approval-envelope.v1+json"
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_MAX_SAFE_INTEGER = 2**53 - 1
_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "governance/schemas/specification/error-registry-v1.json"


class SpecificationABCError(ValueError):
    """A v1 contract refusal selected from the committed error registry."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class _DuplicateMember(ValueError):
    pass


class _Registry:
    def __init__(self, raw: bytes) -> None:
        try:
            value = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid specification error registry") from exc
        if not isinstance(value, dict) or value.get("version") != "ranex-specification-error-registry-v1":
            raise ValueError("invalid specification error registry")
        errors = value.get("errors")
        precedence = value.get("precedence")
        if not isinstance(errors, dict) or not isinstance(precedence, list) or set(precedence) != set(errors):
            raise ValueError("invalid specification error registry")
        for name in precedence:
            entry = errors.get(name)
            if not isinstance(entry, dict) or not isinstance(entry.get("code"), str):
                raise ValueError("invalid specification error registry")
        self.errors: dict[str, dict[str, str]] = errors

    def refuse(self, name: str, detail: str) -> NoReturn:
        entry = self.errors[name]
        raise SpecificationABCError(entry["code"], f"{entry['message']}: {detail}")


def load_error_registry(raw: bytes | None = None) -> _Registry:
    """Load the normative registry bytes; default bytes are the committed v1 file."""
    return _Registry(_REGISTRY_PATH.read_bytes() if raw is None else raw)


def _registry(registry: _Registry | bytes | None) -> _Registry:
    if isinstance(registry, _Registry):
        return registry
    return load_error_registry(registry)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateMember(key)
        result[key] = value
    return result


def _integer(token: str) -> int:
    if token == "-0":
        raise ValueError("number")
    value = int(token)
    if abs(value) > _MAX_SAFE_INTEGER:
        raise OverflowError(token)
    return value


def _float(_token: str) -> NoReturn:
    raise ValueError("number")


def _constant(_token: str) -> NoReturn:
    raise ValueError("number")


def _reject_lone_surrogates(text: str, reg: _Registry) -> None:
    """Validate JSON escape pairing before Python can silently preserve surrogates."""
    index = 0
    in_string = False
    while index < len(text):
        character = text[index]
        if not in_string:
            if character == '"':
                in_string = True
            index += 1
            continue
        if character == '"':
            in_string = False
            index += 1
            continue
        if character != "\\":
            index += 1
            continue
        if index + 1 >= len(text) or text[index + 1] != "u":
            index += 2
            continue
        unit = text[index + 2 : index + 6]
        if len(unit) != 4 or any(char not in "0123456789abcdefABCDEF" for char in unit):
            index += 2
            continue
        value = int(unit, 16)
        if 0xD800 <= value <= 0xDBFF:
            next_unit = text[index + 8 : index + 12] if text[index + 6 : index + 8] == "\\u" else ""
            if len(next_unit) != 4 or not 0xDC00 <= int(next_unit, 16) <= 0xDFFF:
                reg.refuse("surrogate", "high surrogate is not followed by a low surrogate")
            index += 12
        elif 0xDC00 <= value <= 0xDFFF:
            reg.refuse("surrogate", "low surrogate has no preceding high surrogate")
        else:
            index += 6


def parse_strict_json(raw: bytes, *, registry: _Registry | bytes | None = None) -> object:
    """Parse the v1 raw profile: UTF-8, unique members, safe plain integers only."""
    reg = _registry(registry)
    if not isinstance(raw, bytes):
        reg.refuse("input_type", type(raw).__name__)
    if raw.startswith(b"\xef\xbb\xbf"):
        reg.refuse("bom", "BOM is forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        reg.refuse("utf8", str(exc))
    _reject_lone_surrogates(text, reg)
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=_integer,
            parse_float=_float,
            parse_constant=_constant,
        )
    except _DuplicateMember as exc:
        reg.refuse("duplicate_member", str(exc))
    except OverflowError as exc:
        reg.refuse("integer_range", str(exc))
    except ValueError as exc:
        if str(exc) == "number":
            reg.refuse("number", "floats, exponents, and negative zero are forbidden")
        reg.refuse("json", str(exc))
    except json.JSONDecodeError as exc:
        reg.refuse("json", str(exc))


def _reject_value_surrogates(value: object, reg: _Registry) -> None:
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            reg.refuse("surrogate", "in-memory string has a surrogate")
    elif isinstance(value, list):
        for item in value:
            _reject_value_surrogates(item, reg)
    elif isinstance(value, dict):
        for key, item in value.items():
            _reject_value_surrogates(key, reg)
            _reject_value_surrogates(item, reg)
    elif isinstance(value, float):
        reg.refuse("number", "in-memory float is forbidden")
    elif type(value) is int and abs(value) > _MAX_SAFE_INTEGER:
        reg.refuse("integer_range", str(value))


def canonical_payload_bytes(value: object, *, registry: _Registry | bytes | None = None) -> bytes:
    """Return v1 canonical JSON: compact UTF-8 and Unicode code-point key order."""
    reg = _registry(registry)
    _reject_value_surrogates(value, reg)
    try:
        return canonical_json_bytes(value)
    except (TypeError, ValueError) as exc:
        reg.refuse("shape", str(exc))


def payload_digest(
    value: object,
    *,
    payload_type: str | None = None,
    registry: _Registry | bytes | None = None,
) -> str:
    """Digest canonical bytes, PAE-domain-separated for every known A/B/C payload."""
    inferred = {
        "spec-packet-v1": SPEC_PACKET_PAYLOAD_TYPE,
        "generated-artifact-manifest-v1": MANIFEST_PAYLOAD_TYPE,
        "approval-payload-v1": APPROVAL_PAYLOAD_TYPE,
        "approval-envelope-v1": APPROVAL_PAYLOAD_TYPE,
    }
    if payload_type is None and isinstance(value, dict):
        version = value.get("version")
        if isinstance(version, str):
            payload_type = inferred.get(version)
    body = canonical_payload_bytes(value, registry=registry)
    preimage = body if payload_type is None else pae(payload_type, body)
    return "sha256:" + hashlib.sha256(preimage).hexdigest()


def pae(payload_type: str, body: bytes) -> bytes:
    """DSSE v1 PAE over exact payload-type and body UTF-8 byte lengths."""
    if not isinstance(payload_type, str) or not isinstance(body, bytes):
        raise TypeError("payload_type must be str and body must be bytes")
    type_bytes = payload_type.encode("utf-8")
    return b"DSSEv1 " + str(len(type_bytes)).encode() + b" " + type_bytes + b" " + str(len(body)).encode() + b" " + body


def _object(value: object, expected: set[str], reg: _Registry) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        reg.refuse("shape", "object has missing or extra fields")
    return value


def _string(value: object, reg: _Registry) -> str:
    if not isinstance(value, str) or not value:
        reg.refuse("shape", "required string is absent or empty")
    return value


def _strings(value: object, reg: _Registry) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        reg.refuse("shape", "expected a string array")
    return value


def _integer_value(value: object, reg: _Registry) -> int:
    if type(value) is not int or value < 0:
        reg.refuse("shape", "expected a non-negative integer")
    return value


def _digest(value: object, reg: _Registry) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        reg.refuse("digest", repr(value))
    return value


def _version(value: dict[str, object], expected: str, reg: _Registry) -> None:
    if value.get("version") != expected:
        reg.refuse("version", repr(value.get("version")))


def validate_spec_packet(value: object, *, registry: _Registry | bytes | None = None) -> dict[str, object]:
    reg = _registry(registry)
    packet = _object(value, {"version", "domain", "task", "revision", "semantics", "scope", "answers", "observable_outcomes", "non_goals", "oracle_provenance", "ids"}, reg)
    _version(packet, "spec-packet-v1", reg)
    _string(packet["domain"], reg); _string(packet["task"], reg); _integer_value(packet["revision"], reg)
    for name in ("semantics", "observable_outcomes", "non_goals"):
        _strings(packet[name], reg)
    scope = _object(packet["scope"], {"include", "exclude"}, reg)
    _strings(scope["include"], reg); _strings(scope["exclude"], reg)
    answers = packet["answers"]
    if not isinstance(answers, dict) or any(not isinstance(key, str) or not isinstance(item, str) for key, item in answers.items()):
        reg.refuse("shape", "answers must map strings to strings")
    provenance = packet["oracle_provenance"]
    labels = {"human", "domain-rule", "requirement", "observed-only"}
    if not isinstance(provenance, dict) or any(not isinstance(key, str) or item not in labels for key, item in provenance.items()):
        reg.refuse("shape", "oracle provenance is invalid")
    ids = _object(packet["ids"], {"question", "rule", "transition", "outcome", "error", "test", "mapping"}, reg)
    for item in ids.values():
        _strings(item, reg)
    return packet


def _artifact_rows(value: object, reg: _Registry) -> None:
    if not isinstance(value, list):
        reg.refuse("shape", "artifact set must be an array")
    for item in value:
        row = _object(item, {"path", "digest"}, reg)
        _string(row["path"], reg); _digest(row["digest"], reg)


def validate_generated_artifact_manifest(value: object, *, registry: _Registry | bytes | None = None) -> dict[str, object]:
    reg = _registry(registry)
    manifest = _object(value, {"version", "domain", "a_digest", "artifacts", "exemptions"}, reg)
    _version(manifest, "generated-artifact-manifest-v1", reg)
    _string(manifest["domain"], reg); _digest(manifest["a_digest"], reg)
    artifacts = _object(manifest["artifacts"], {"pseudocode_flow", "protected", "invocation", "expected_values", "baselines", "negative_controls", "trace_projections", "sidecars"}, reg)
    for name in ("pseudocode_flow", "protected", "expected_values", "baselines", "negative_controls", "trace_projections", "sidecars"):
        _artifact_rows(artifacts[name], reg)
    invocation = _object(artifacts["invocation"], {"argv"}, reg)
    _strings(invocation["argv"], reg)
    if not isinstance(manifest["exemptions"], list):
        reg.refuse("shape", "exemptions must be an array")
    for item in manifest["exemptions"]:
        row = _object(item, {"path", "class", "reason", "why_no_discriminating_red"}, reg)
        _string(row["path"], reg); _string(row["reason"], reg); _string(row["why_no_discriminating_red"], reg)
        if row["class"] not in {"generated", "vendor", "docs", "nonbehavioral"}:
            reg.refuse("shape", "exemption class is invalid")
    return manifest


def _key(value: object, reg: _Registry) -> str:
    try:
        _decode(value, expected=32, field="public key")
    except ValueError as exc:
        reg.refuse("shape", str(exc))
    return value  # type: ignore[return-value]


def _capability(value: object, reg: _Registry) -> None:
    request = _object(value, {"executable", "argv", "cwd", "roots", "actions", "environment", "network", "secret", "commit", "subagent"}, reg)
    _string(request["executable"], reg); _strings(request["argv"], reg); _string(request["cwd"], reg)
    _strings(request["roots"], reg); _strings(request["actions"], reg)
    environment = _object(request["environment"], {"allow"}, reg); _strings(environment["allow"], reg)
    network = _object(request["network"], {"allow", "hosts"}, reg); _strings(network["hosts"], reg)
    secret = _object(request["secret"], {"allow", "names"}, reg); _strings(secret["names"], reg)
    commit = _object(request["commit"], {"allow"}, reg)
    subagent = _object(request["subagent"], {"allow", "max_children"}, reg); _integer_value(subagent["max_children"], reg)
    for flag in (network["allow"], secret["allow"], commit["allow"], subagent["allow"]):
        if type(flag) is not bool:
            reg.refuse("shape", "capability allow value must be boolean")


def _approval_payload(value: object, reg: _Registry) -> dict[str, object]:
    payload = _object(value, {"version", "domain", "task", "revision", "subject_digest", "base_digest", "a_digest", "b_digest", "principal", "key", "role", "nonce", "journal_predecessor", "time_window", "capability_request", "profile_digests"}, reg)
    _version(payload, "approval-payload-v1", reg)
    for name in ("domain", "task", "principal", "role", "nonce"):
        _string(payload[name], reg)
    _integer_value(payload["revision"], reg)
    for name in ("subject_digest", "base_digest", "a_digest", "b_digest"):
        _digest(payload[name], reg)
    _key(payload["key"], reg)
    if payload["journal_predecessor"] is not None:
        _digest(payload["journal_predecessor"], reg)
    window = _object(payload["time_window"], {"not_before", "not_after"}, reg)
    if _integer_value(window["not_before"], reg) > _integer_value(window["not_after"], reg):
        reg.refuse("shape", "journal sequence window is reversed")
    _capability(payload["capability_request"], reg)
    profiles = _object(payload["profile_digests"], {"base", "policy", "generator", "harness"}, reg)
    for digest in profiles.values():
        _digest(digest, reg)
    return payload


def validate_approval_envelope(value: object, *, used_nonces: Iterable[str] = (), registry: _Registry | bytes | None = None) -> dict[str, object]:
    reg = _registry(registry)
    envelope = _object(value, {"version", "payload_type", "payload", "key_id", "signature"}, reg)
    if envelope["payload_type"] != APPROVAL_PAYLOAD_TYPE:
        reg.refuse("payload_type", repr(envelope["payload_type"]))
    _version(envelope, "approval-envelope-v1", reg)
    payload = _approval_payload(envelope["payload"], reg)
    _key(envelope["key_id"], reg)
    if payload["nonce"] in set(used_nonces):
        reg.refuse("nonce_reuse", str(payload["nonce"]))
    try:
        signature = _decode(envelope["signature"], expected=64, field="signature")
        public = _decode(payload["key"], expected=32, field="public key")
        Ed25519PublicKey.from_public_bytes(public).verify(signature, pae(APPROVAL_PAYLOAD_TYPE, canonical_payload_bytes(payload, registry=reg)))
    except (InvalidSignature, ValueError, TypeError, binascii.Error) as exc:
        reg.refuse("signature", str(exc))
    return envelope


def sign_approval_envelope(payload: Mapping[str, object], private_key: str, *, registry: _Registry | bytes | None = None) -> str:
    reg = _registry(registry)
    checked = _approval_payload(dict(payload), reg)
    try:
        private = Ed25519PrivateKey.from_private_bytes(_decode(private_key, expected=32, field="private key"))
    except ValueError as exc:
        reg.refuse("signature", str(exc))
    public = _encode(private.public_key().public_bytes_raw())
    if public != checked["key"]:
        reg.refuse("relation", "private key does not match approval payload key")
    return _encode(private.sign(pae(APPROVAL_PAYLOAD_TYPE, canonical_payload_bytes(checked, registry=reg))))


def verify_approval_envelope(value: object, *, used_nonces: Iterable[str] = (), registry: _Registry | bytes | None = None) -> bool:
    try:
        validate_approval_envelope(value, used_nonces=used_nonces, registry=registry)
    except SpecificationABCError:
        return False
    return True


def parse_canonical_payload(raw: bytes, *, registry: _Registry | bytes | None = None) -> object:
    """Parse v1 bytes and refuse semantically equivalent but noncanonical input."""
    reg = _registry(registry)
    value = parse_strict_json(raw, registry=reg)
    if raw != canonical_payload_bytes(value, registry=reg):
        reg.refuse("canonical", "raw bytes differ from canonical serialization")
    return value


def validate_spec_packet_bytes(raw: bytes, *, registry: _Registry | bytes | None = None) -> dict[str, object]:
    return validate_spec_packet(parse_canonical_payload(raw, registry=registry), registry=registry)


def validate_generated_artifact_manifest_bytes(raw: bytes, *, registry: _Registry | bytes | None = None) -> dict[str, object]:
    return validate_generated_artifact_manifest(parse_canonical_payload(raw, registry=registry), registry=registry)


def validate_approval_envelope_bytes(raw: bytes, *, used_nonces: Iterable[str] = (), registry: _Registry | bytes | None = None) -> dict[str, object]:
    return validate_approval_envelope(parse_canonical_payload(raw, registry=registry), used_nonces=used_nonces, registry=registry)
