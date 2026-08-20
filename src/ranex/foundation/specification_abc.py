"""Frozen v1 A/B/C specification contracts and byte-level identity helpers."""

from __future__ import annotations

import binascii
import hashlib
import json
import re
from collections.abc import Iterable, Mapping, Set
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
_REGISTRY_FAILURE_CODE = "E-ABC-000"

CLOSED_FIELD_SETS: dict[str, frozenset[str]] = {
    "spec_packet": frozenset({"version", "domain", "task", "revision", "semantics", "scope", "answers", "observable_outcomes", "non_goals", "oracle_provenance", "ids"}),
    "scope": frozenset({"include", "exclude"}),
    "ids": frozenset({"question", "rule", "transition", "outcome", "error", "test", "mapping"}),
    "manifest": frozenset({"version", "domain", "a_digest", "artifacts", "exemptions"}),
    "artifacts": frozenset({"pseudocode_flow", "protected", "invocation", "expected_values", "baselines", "negative_controls", "trace_projections", "sidecars"}),
    "invocation": frozenset({"argv"}),
    "artifact_row": frozenset({"path", "digest"}),
    "exemption_row": frozenset({"path", "class", "reason", "why_no_discriminating_red"}),
    "envelope": frozenset({"version", "payload_type", "payload", "key_id", "signature"}),
    "approval_payload": frozenset({"version", "domain", "task", "revision", "subject_digest", "base_digest", "a_digest", "b_digest", "principal", "key", "role", "nonce", "journal_predecessor", "time_window", "capability_request", "profile_digests"}),
    "time_window": frozenset({"not_before", "not_after"}),
    "capability_request": frozenset({"executable", "argv", "cwd", "roots", "actions", "environment", "network", "secret", "commit", "subagent"}),
    "environment": frozenset({"allow"}),
    "network": frozenset({"allow", "hosts"}),
    "secret": frozenset({"allow", "names"}),
    "commit": frozenset({"allow"}),
    "subagent": frozenset({"allow", "max_children"}),
    "profile_digests": frozenset({"base", "policy", "generator", "harness"}),
}


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
        check_order = value.get("check_order")
        if (
            not isinstance(errors, dict)
            or not isinstance(precedence, list)
            or not isinstance(check_order, list)
            or set(precedence) != set(errors)
            or set(check_order) != set(errors)
            or len(precedence) != len(errors)
            or len(check_order) != len(errors)
            or precedence != check_order
        ):
            raise ValueError("invalid specification error registry")
        for name in precedence:
            entry = errors.get(name)
            if not isinstance(entry, dict) or not isinstance(entry.get("code"), str):
                raise ValueError("invalid specification error registry")
        self.errors: dict[str, dict[str, str]] = errors
        self.check_order: tuple[str, ...] = tuple(check_order)

    def refuse(self, name: str, detail: str) -> NoReturn:
        entry = self.errors.get(name)
        if entry is None:
            raise SpecificationABCError(_REGISTRY_FAILURE_CODE, f"error registry has no entry for {name!r}")
        raise SpecificationABCError(entry["code"], f"{entry['message']}: {detail}")

    def refuse_first(self, failures: Mapping[str, str]) -> NoReturn:
        """Refuse with the earliest candidate in the registry's normative order."""
        for name in self.check_order:
            if name in failures:
                self.refuse(name, failures[name])
        raise SpecificationABCError(_REGISTRY_FAILURE_CODE, "no registered failure candidate")


class _FailureCollector:
    """Accumulate failures so registry data, not validation phase, selects one."""

    def __init__(self, registry: _Registry) -> None:
        self._registry = registry
        self._failures: dict[str, str] = {}

    def add(self, name: str, detail: str) -> None:
        self._failures.setdefault(name, detail)

    def extend(self, failures: Mapping[str, str]) -> None:
        for name, detail in failures.items():
            self.add(name, detail)

    def refuse_if_any(self) -> None:
        if self._failures:
            self._registry.refuse_first(self._failures)


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


def _json_escape_failures(text: str) -> dict[str, str]:
    """Collect strict JSON escape and surrogate candidates without converting bad hex."""
    failures: dict[str, str] = {}
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
        if index + 1 >= len(text):
            failures.setdefault("escape", "unterminated escape")
            break
        if text[index + 1] != "u":
            if text[index + 1] not in '"\\/bfnrt':
                failures.setdefault("escape", "invalid escape character")
            index += 2
            continue
        unit = text[index + 2 : index + 6]
        if len(unit) != 4 or any(char not in "0123456789abcdefABCDEF" for char in unit):
            failures.setdefault("escape", "unicode escape must contain exactly four hexadecimal digits")
            index += 6
            continue
        value = int(unit, 16)
        if 0xD800 <= value <= 0xDBFF:
            next_unit = text[index + 8 : index + 12] if text[index + 6 : index + 8] == "\\u" else ""
            if len(next_unit) != 4 or any(char not in "0123456789abcdefABCDEF" for char in next_unit):
                failures.setdefault("surrogate", "high surrogate is not followed by a low surrogate")
                if text[index + 6 : index + 8] == "\\u":
                    failures.setdefault("escape", "unicode escape must contain exactly four hexadecimal digits")
                index += 6
            elif not 0xDC00 <= int(next_unit, 16) <= 0xDFFF:
                failures.setdefault("surrogate", "high surrogate is not followed by a low surrogate")
                index += 6
            else:
                index += 12
        elif 0xDC00 <= value <= 0xDFFF:
            failures.setdefault("surrogate", "low surrogate has no preceding high surrogate")
            index += 6
        else:
            index += 6
    return failures


def _duplicate_member_failures(text: str) -> dict[str, str]:
    """Lex object keys independently so a bad value cannot hide a duplicate."""

    failures: dict[str, str] = {}
    objects: list[set[str]] = []
    index = 0
    while index < len(text):
        character = text[index]
        if character == "{":
            objects.append(set())
        elif character == "}":
            if objects:
                objects.pop()
        elif character == '"':
            start = index
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == '"':
                    break
                index += 1
            token = text[start : index + 1]
            cursor = index + 1
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            if objects and cursor < len(text) and text[cursor] == ":":
                try:
                    key = json.loads(token)
                except json.JSONDecodeError:
                    key = token
                if key in objects[-1]:
                    failures.setdefault("duplicate_member", str(key))
                objects[-1].add(key)
        index += 1
    return failures


def parse_strict_json(raw: bytes, *, registry: _Registry | bytes | None = None) -> object:
    """Parse the v1 raw profile: UTF-8, unique members, safe plain integers only."""
    reg = _registry(registry)
    if not isinstance(raw, bytes):
        reg.refuse("input_type", type(raw).__name__)
    failures = _FailureCollector(reg)
    if raw.startswith(b"\xef\xbb\xbf"):
        failures.add("bom", "BOM is forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        failures.add("utf8", str(exc))
        failures.refuse_if_any()
        raise AssertionError("failure collector must refuse") from exc
    failures.extend(_json_escape_failures(text))
    failures.extend(_duplicate_member_failures(text))
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_int=_integer,
            parse_float=_float,
            parse_constant=_constant,
        )
    except _DuplicateMember as exc:
        failures.add("duplicate_member", str(exc))
    except OverflowError as exc:
        failures.add("integer_range", str(exc))
    except ValueError as exc:
        if str(exc) == "number":
            failures.add("number", "floats, exponents, and negative zero are forbidden")
        else:
            failures.add("json", str(exc))
    else:
        failures.refuse_if_any()
        return value
    # Every handler above records a failure, so this refuse always raises;
    # pyrefly cannot see that state dependency, hence the explicit shape.
    failures.refuse_if_any()
    raise AssertionError("failure collector must refuse")  # pragma: no cover - unreachable by the handlers' contract


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
        return canonical_json_bytes(value).replace(b"\xe2\x80\xa8", b"\\u2028").replace(b"\xe2\x80\xa9", b"\\u2029")
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


def _object(value: object, expected: Set[str], reg: _Registry) -> dict[str, object]:
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
    failures = _FailureCollector(reg)
    if isinstance(value, dict):
        if "version" in value and value.get("version") != "spec-packet-v1":
            failures.add("version", repr(value.get("version")))
        if set(value) != CLOSED_FIELD_SETS["spec_packet"]:
            failures.add("shape", "object has missing or extra fields")
    failures.refuse_if_any()
    packet = _object(value, CLOSED_FIELD_SETS["spec_packet"], reg)
    _version(packet, "spec-packet-v1", reg)
    _string(packet["domain"], reg); _string(packet["task"], reg); _integer_value(packet["revision"], reg)
    for name in ("semantics", "observable_outcomes", "non_goals"):
        _strings(packet[name], reg)
    scope = _object(packet["scope"], CLOSED_FIELD_SETS["scope"], reg)
    _strings(scope["include"], reg); _strings(scope["exclude"], reg)
    answers = packet["answers"]
    if not isinstance(answers, dict) or any(not isinstance(key, str) or not isinstance(item, str) for key, item in answers.items()):
        reg.refuse("shape", "answers must map strings to strings")
    provenance = packet["oracle_provenance"]
    labels = {"human", "domain-rule", "requirement", "observed-only"}
    if not isinstance(provenance, dict) or any(not isinstance(key, str) or item not in labels for key, item in provenance.items()):
        reg.refuse("shape", "oracle provenance is invalid")
    ids = _object(packet["ids"], CLOSED_FIELD_SETS["ids"], reg)
    seen_ids: set[str] = set()
    failures = _FailureCollector(reg)
    for item in ids.values():
        for identifier in _strings(item, reg):
            if not identifier.strip():
                failures.add("id_grammar", "ID must not be blank or whitespace-only")
            if identifier in seen_ids:
                failures.add("id_duplicate", identifier)
            seen_ids.add(identifier)
    failures.refuse_if_any()
    return packet


def _artifact_rows(value: object, reg: _Registry) -> None:
    if not isinstance(value, list):
        reg.refuse("shape", "artifact set must be an array")
    for item in value:
        row = _object(item, CLOSED_FIELD_SETS["artifact_row"], reg)
        _string(row["path"], reg); _digest(row["digest"], reg)


def _collect_object_candidate(value: object, expected: frozenset[str], failures: _FailureCollector) -> Mapping[str, object] | None:
    if not isinstance(value, dict) or set(value) != expected:
        failures.add("shape", "object has missing or extra fields")
        return None
    return value


def _collect_artifact_rows_candidates(value: object, failures: _FailureCollector) -> None:
    if not isinstance(value, list):
        failures.add("shape", "artifact set must be an array")
        return
    for item in value:
        row = _collect_object_candidate(item, CLOSED_FIELD_SETS["artifact_row"], failures)
        if row is not None:
            path = row["path"]
            if not isinstance(path, str) or not path:
                failures.add("shape", "required string is absent or empty")
            digest = row["digest"]
            if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
                failures.add("digest", repr(digest))


def _collect_manifest_candidates(value: object, failures: _FailureCollector) -> None:
    """Walk manifest children before precedence selects a top-level candidate."""

    if isinstance(value, dict):
        if "version" in value and value.get("version") != "generated-artifact-manifest-v1":
            failures.add("version", repr(value.get("version")))
        digest = value.get("a_digest")
        if not isinstance(digest, str) or _DIGEST.fullmatch(digest) is None:
            failures.add("digest", repr(digest))
    manifest = _collect_object_candidate(value, CLOSED_FIELD_SETS["manifest"], failures)
    if manifest is None:
        return
    artifacts = _collect_object_candidate(manifest["artifacts"], CLOSED_FIELD_SETS["artifacts"], failures)
    if artifacts is not None:
        for name in ("pseudocode_flow", "protected", "expected_values", "baselines", "negative_controls", "trace_projections", "sidecars"):
            _collect_artifact_rows_candidates(artifacts[name], failures)
        invocation = _collect_object_candidate(artifacts["invocation"], CLOSED_FIELD_SETS["invocation"], failures)
        if invocation is not None and (
            not isinstance(invocation["argv"], list)
            or any(not isinstance(item, str) for item in invocation["argv"])
        ):
            failures.add("shape", "expected a string array")
    exemptions = manifest["exemptions"]
    if not isinstance(exemptions, list):
        failures.add("shape", "exemptions must be an array")
    else:
        for item in exemptions:
            row = _collect_object_candidate(item, CLOSED_FIELD_SETS["exemption_row"], failures)
            if row is not None:
                for name in ("path", "reason", "why_no_discriminating_red"):
                    if not isinstance(row[name], str) or not row[name]:
                        failures.add("shape", "required string is absent or empty")
                if row["class"] not in {"generated", "vendor", "docs", "nonbehavioral"}:
                    failures.add("shape", "exemption class is invalid")


def validate_generated_artifact_manifest(
    value: object,
    *,
    spec_packet: object | None = None,
    registry: _Registry | bytes | None = None,
) -> dict[str, object]:
    reg = _registry(registry)
    failures = _FailureCollector(reg)
    _collect_manifest_candidates(value, failures)
    failures.refuse_if_any()
    manifest = _object(value, CLOSED_FIELD_SETS["manifest"], reg)
    _version(manifest, "generated-artifact-manifest-v1", reg)
    _string(manifest["domain"], reg); _digest(manifest["a_digest"], reg)
    artifacts = _object(manifest["artifacts"], CLOSED_FIELD_SETS["artifacts"], reg)
    for name in ("pseudocode_flow", "protected", "expected_values", "baselines", "negative_controls", "trace_projections", "sidecars"):
        _artifact_rows(artifacts[name], reg)
    invocation = _object(artifacts["invocation"], CLOSED_FIELD_SETS["invocation"], reg)
    _strings(invocation["argv"], reg)
    if not isinstance(manifest["exemptions"], list):
        reg.refuse("shape", "exemptions must be an array")
    for item in manifest["exemptions"]:
        row = _object(item, CLOSED_FIELD_SETS["exemption_row"], reg)
        _string(row["path"], reg); _string(row["reason"], reg); _string(row["why_no_discriminating_red"], reg)
        if row["class"] not in {"generated", "vendor", "docs", "nonbehavioral"}:
            reg.refuse("shape", "exemption class is invalid")
    if spec_packet is not None and manifest["a_digest"] != payload_digest(validate_spec_packet(spec_packet, registry=reg), registry=reg):
        reg.refuse("a_binding", "manifest a_digest does not bind the supplied spec packet")
    return manifest


def _key(value: object, reg: _Registry) -> str:
    try:
        _decode(value, expected=32, field="public key")
    except ValueError as exc:
        reg.refuse("shape", str(exc))
    return value  # type: ignore[return-value]


def _capability(value: object, reg: _Registry) -> None:
    request = _object(value, CLOSED_FIELD_SETS["capability_request"], reg)
    _string(request["executable"], reg); _strings(request["argv"], reg); _string(request["cwd"], reg)
    _strings(request["roots"], reg); _strings(request["actions"], reg)
    environment = _object(request["environment"], CLOSED_FIELD_SETS["environment"], reg); _strings(environment["allow"], reg)
    network = _object(request["network"], CLOSED_FIELD_SETS["network"], reg); _strings(network["hosts"], reg)
    secret = _object(request["secret"], CLOSED_FIELD_SETS["secret"], reg); _strings(secret["names"], reg)
    commit = _object(request["commit"], CLOSED_FIELD_SETS["commit"], reg)
    subagent = _object(request["subagent"], CLOSED_FIELD_SETS["subagent"], reg); _integer_value(subagent["max_children"], reg)
    for flag in (network["allow"], secret["allow"], commit["allow"], subagent["allow"]):
        if type(flag) is not bool:
            reg.refuse("shape", "capability allow value must be boolean")


def _approval_payload(value: object, reg: _Registry) -> dict[str, object]:
    payload = _object(value, CLOSED_FIELD_SETS["approval_payload"], reg)
    _version(payload, "approval-payload-v1", reg)
    for name in ("domain", "task", "principal", "role", "nonce"):
        _string(payload[name], reg)
    _integer_value(payload["revision"], reg)
    for name in ("subject_digest", "base_digest", "a_digest", "b_digest"):
        _digest(payload[name], reg)
    _key(payload["key"], reg)
    if payload["journal_predecessor"] is not None:
        _digest(payload["journal_predecessor"], reg)
    window = _object(payload["time_window"], CLOSED_FIELD_SETS["time_window"], reg)
    if _integer_value(window["not_before"], reg) > _integer_value(window["not_after"], reg):
        reg.refuse("shape", "journal sequence window is reversed")
    _capability(payload["capability_request"], reg)
    profiles = _object(payload["profile_digests"], CLOSED_FIELD_SETS["profile_digests"], reg)
    for digest in profiles.values():
        _digest(digest, reg)
    return payload


def validate_approval_envelope(value: object, *, used_nonces: Iterable[str] = (), registry: _Registry | bytes | None = None) -> dict[str, object]:
    reg = _registry(registry)
    envelope = _object(value, CLOSED_FIELD_SETS["envelope"], reg)
    if envelope["payload_type"] != APPROVAL_PAYLOAD_TYPE:
        reg.refuse("payload_type", repr(envelope["payload_type"]))
    _version(envelope, "approval-envelope-v1", reg)
    payload = _approval_payload(envelope["payload"], reg)
    _key(envelope["key_id"], reg)
    if envelope["key_id"] != payload["key"]:
        reg.refuse("key_binding", "envelope key_id does not match approval payload key")
    if payload["nonce"] in set(used_nonces):
        reg.refuse("nonce_reuse", str(payload["nonce"]))
    try:
        signature = _decode(envelope["signature"], expected=64, field="signature")
        public = _decode(payload["key"], expected=32, field="public key")
        payload_type = _payload_type_from_version(payload, reg)
        Ed25519PublicKey.from_public_bytes(public).verify(signature, pae(payload_type, canonical_payload_bytes(payload, registry=reg)))
    except (InvalidSignature, ValueError, TypeError, binascii.Error) as exc:
        reg.refuse("signature", str(exc))
    return envelope


def _payload_type_from_version(payload: Mapping[str, object], reg: _Registry) -> str:
    version = payload.get("version")
    payload_type = APPROVAL_PAYLOAD_TYPE if version == "approval-payload-v1" else None
    if payload_type is None:
        reg.refuse("payload_type", repr(payload.get("version")))
    return payload_type


def sign_approval_payload(payload: Mapping[str, object], private_key: str, *, registry: _Registry | bytes | None = None) -> str:
    reg = _registry(registry)
    checked = _approval_payload(dict(payload), reg)
    try:
        private = Ed25519PrivateKey.from_private_bytes(_decode(private_key, expected=32, field="private key"))
    except ValueError as exc:
        reg.refuse("signature", str(exc))
    public = _encode(private.public_key().public_bytes_raw())
    if public != checked["key"]:
        reg.refuse("relation", "private key does not match approval payload key")
    return _encode(private.sign(pae(_payload_type_from_version(checked, reg), canonical_payload_bytes(checked, registry=reg))))


def verify_approval_envelope(value: object, *, used_nonces: Iterable[str] = (), registry: _Registry | bytes | None = None) -> bool:
    try:
        validate_approval_envelope(value, used_nonces=used_nonces, registry=registry)
    except SpecificationABCError:
        return False
    return True


def assert_abc_chain(
    spec_packet: object,
    manifest: object,
    envelope: object,
    *,
    used_nonces: Iterable[str] = (),
    registry: _Registry | bytes | None = None,
) -> None:
    """Refuse unless B and C bind the exact supplied A/B payload identities."""
    reg = _registry(registry)
    checked_a = validate_spec_packet(spec_packet, registry=reg)
    checked_b = validate_generated_artifact_manifest(manifest, registry=reg)
    checked_envelope = _object(envelope, CLOSED_FIELD_SETS["envelope"], reg)
    checked_payload = _approval_payload(checked_envelope["payload"], reg)
    failures = _FailureCollector(reg)
    a_digest = payload_digest(checked_a, registry=reg)
    if checked_b["a_digest"] != a_digest:
        failures.add("a_binding", "manifest a_digest does not bind the supplied spec packet")
    if checked_payload["a_digest"] != a_digest:
        failures.add("a_binding", "approval payload a_digest does not bind the supplied spec packet")
    if checked_payload["b_digest"] != payload_digest(checked_b, registry=reg):
        failures.add("b_binding", "approval payload b_digest does not bind the supplied manifest")
    if checked_a["domain"] != checked_b["domain"] or checked_a["domain"] != checked_payload["domain"]:
        failures.add("context_binding", "A, B, and C domains must match exactly")
    if checked_a["task"] != checked_payload["task"] or checked_a["revision"] != checked_payload["revision"]:
        failures.add("context_binding", "A and C task and revision must match exactly")
    failures.refuse_if_any()
    validate_approval_envelope(checked_envelope, used_nonces=used_nonces, registry=reg)


def parse_canonical_payload(raw: bytes, *, registry: _Registry | bytes | None = None) -> object:
    """Parse v1 bytes and refuse semantically equivalent but noncanonical input."""
    reg = _registry(registry)
    value = parse_strict_json(raw, registry=reg)
    if raw != canonical_payload_bytes(value, registry=reg):
        reg.refuse("canonical", "raw bytes differ from canonical serialization")
    return value


def validate_spec_packet_bytes(raw: bytes, *, registry: _Registry | bytes | None = None) -> dict[str, object]:
    return validate_spec_packet(parse_canonical_payload(raw, registry=registry), registry=registry)


def validate_generated_artifact_manifest_bytes(
    raw: bytes,
    *,
    spec_packet: object | None = None,
    registry: _Registry | bytes | None = None,
) -> dict[str, object]:
    return validate_generated_artifact_manifest(
        parse_canonical_payload(raw, registry=registry),
        spec_packet=spec_packet,
        registry=registry,
    )


def validate_approval_envelope_bytes(raw: bytes, *, used_nonces: Iterable[str] = (), registry: _Registry | bytes | None = None) -> dict[str, object]:
    return validate_approval_envelope(parse_canonical_payload(raw, registry=registry), used_nonces=used_nonces, registry=registry)
