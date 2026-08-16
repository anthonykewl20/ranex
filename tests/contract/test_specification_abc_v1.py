from __future__ import annotations

import base64
import copy
import hashlib
import json
import re
import secrets
from pathlib import Path

import pytest

import ranex.foundation.specification_abc as specification_abc
from ranex.foundation.specification_abc import (
    SpecificationABCError,
    assert_abc_chain,
    canonical_payload_bytes,
    load_error_registry,
    pae,
    parse_canonical_payload,
    parse_strict_json,
    payload_digest,
    sign_approval_payload,
    validate_approval_envelope,
    validate_approval_envelope_bytes,
    validate_generated_artifact_manifest,
    validate_generated_artifact_manifest_bytes,
    validate_spec_packet,
    validate_spec_packet_bytes,
    verify_approval_envelope,
)

VECTORS = json.loads(
    (Path(__file__).parent / "fixtures/specification/abc-v1-vectors.json").read_text("utf-8")
)


def test_positive_vectors_are_canonical_and_digest_stable() -> None:
    for vector in VECTORS["canonical"]:
        value = parse_strict_json(vector["raw"].encode())
        assert canonical_payload_bytes(value) == vector["canonical"].encode()
        assert payload_digest(value) == vector["digest"]


def test_strict_parser_accepts_a_valid_surrogate_pair() -> None:
    assert parse_strict_json(b'{"emoji":"\\uD83D\\uDE00"}') == {"emoji": "😀"}


def test_normalization_vectors_pin_distinct_byte_identities() -> None:
    for vector in VECTORS["normalization"]:
        nfc = vector["nfc"]
        nfd = vector["nfd"]
        assert payload_digest(nfc) == vector["nfc_digest"]
        assert payload_digest(nfd) == vector["nfd_digest"]
        assert payload_digest(nfc) != payload_digest(nfd)


def _set_path(value: object, path: list[str], replacement: object) -> None:
    target = value
    for name in path[:-1]:
        assert isinstance(target, dict)
        target = target[name]
    assert isinstance(target, dict)
    target[path[-1]] = replacement


def test_negative_vectors_select_registry_codes() -> None:
    for vector in VECTORS["negative"]:
        if vector.get("input_type") == "text":
            raw: object = vector["raw"]
        else:
            raw = base64.b64decode(vector["raw_base64"]) if "raw_base64" in vector else vector["raw"].encode()
        with pytest.raises(SpecificationABCError) as refused:
            if vector.get("entry_point") == "parse_canonical_payload":
                parse_canonical_payload(raw)  # type: ignore[arg-type]
            else:
                parse_strict_json(raw)  # type: ignore[arg-type]
        assert refused.value.code == vector["error"]
    for vector in VECTORS["payload_negative"]:
        value = copy.deepcopy(VECTORS["triple"][vector["source"]])
        _set_path(value, vector["path"], vector["value"])
        with pytest.raises(SpecificationABCError) as refused:
            if vector["entry_point"] == "spec_packet":
                validate_spec_packet(value)
            else:
                validate_generated_artifact_manifest(value)
        assert refused.value.code == vector["error"]
    for vector in VECTORS["approval_negative"]:
        value = {
            "version": "approval-envelope-v1",
            "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
            "payload": copy.deepcopy(VECTORS["triple"]["c_payload"]),
            "key_id": VECTORS["triple"]["key_id"],
            "signature": VECTORS["triple"]["signature"],
        }
        _set_path(value, vector["path"], vector["value"])
        with pytest.raises(SpecificationABCError) as refused:
            validate_approval_envelope(value)
        assert refused.value.code == vector["error"]
    for vector in VECTORS["signing_negative"]:
        with pytest.raises(SpecificationABCError) as refused:
            sign_approval_payload(VECTORS["triple"]["c_payload"], vector["private_key"])
        assert refused.value.code == vector["error"]


def test_recorded_vector_digests_recompute() -> None:
    triple = VECTORS["triple"]
    assert payload_digest(triple["a"]) == triple["a_digest"]
    assert payload_digest(triple["b"]) == triple["b_digest"]
    assert payload_digest(triple["c_payload"]) == triple["c_digest"]


def test_contract_vectors_pin_pae_media_types_and_c_payload_identity() -> None:
    contract = VECTORS["contract"]
    assert contract["payload_media_types"] == [
        specification_abc.SPEC_PACKET_PAYLOAD_TYPE,
        specification_abc.MANIFEST_PAYLOAD_TYPE,
        specification_abc.APPROVAL_PAYLOAD_TYPE,
    ]
    for vector in contract["pae"]:
        preimage = pae(vector["payload_type"], bytes.fromhex(vector["body_hex"]))
        assert preimage.hex() == vector["preimage_hex"]
        assert "sha256:" + hashlib.sha256(preimage).hexdigest() == vector["digest"]
    assert contract["c_authoritative_identity"] == (
        "C's authoritative identity is the approval-envelope payload digest: "
        "c_digest = payload_digest(c_payload); the detached envelope is not C's identity."
    )
    assert payload_digest(VECTORS["triple"]["c_payload"]) == VECTORS["triple"]["c_digest"]


def test_bound_identity_changes_when_b_or_c_changes() -> None:
    triple = VECTORS["triple"]
    changed_b = copy.deepcopy(triple["b"])
    changed_b["artifacts"]["protected"][0]["digest"] = "sha256:" + "f" * 64
    assert payload_digest(changed_b) != triple["b_digest"]
    changed_c = copy.deepcopy(triple["c_payload"])
    changed_c["role"] = "publisher"
    assert payload_digest(changed_c) != payload_digest(triple["c_payload"])


def test_envelope_signature_domain_and_nonce_controls() -> None:
    triple = VECTORS["triple"]
    envelope = {"version": "approval-envelope-v1", "payload_type": "application/vnd.ranex.approval-envelope.v1+json", "payload": triple["c_payload"], "key_id": triple["key_id"], "signature": triple["signature"]}
    assert verify_approval_envelope(envelope)
    tampered = copy.deepcopy(envelope)
    tampered["signature"] = tampered["signature"][:-1] + "A"
    with pytest.raises(SpecificationABCError, match="E-ABC-016"):
        validate_approval_envelope(tampered)
    swapped = copy.deepcopy(envelope)
    swapped["payload_type"] = "application/vnd.ranex.spec-packet.v1+json"
    with pytest.raises(SpecificationABCError, match="E-ABC-010"):
        validate_approval_envelope(swapped)
    with pytest.raises(SpecificationABCError, match="E-ABC-015"):
        validate_approval_envelope(envelope, used_nonces={"nonce-029"})


def test_manifest_enforces_its_a_binding_when_given_spec_packet() -> None:
    triple = VECTORS["triple"]
    assert validate_generated_artifact_manifest(triple["b"], spec_packet=triple["a"])
    mismatched = copy.deepcopy(triple["b"])
    vector = VECTORS["chain_negative"][0]
    _set_path(mismatched, vector["path"], vector["value"])
    with pytest.raises(SpecificationABCError, match="E-ABC-017"):
        validate_generated_artifact_manifest(mismatched, spec_packet=triple["a"])


def test_envelope_enforces_key_id_payload_key_binding() -> None:
    triple = VECTORS["triple"]
    envelope = {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": triple["c_payload"],
        "key_id": "ed25519:ICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA=",
        "signature": triple["signature"],
    }
    with pytest.raises(SpecificationABCError, match="E-ABC-018"):
        validate_approval_envelope(envelope)


def test_assert_abc_chain_enforces_a_and_b_bindings_and_envelope_validity() -> None:
    triple = VECTORS["triple"]
    envelope = {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": copy.deepcopy(triple["c_payload"]),
        "key_id": triple["key_id"],
        "signature": triple["signature"],
    }
    assert_abc_chain(triple["a"], triple["b"], envelope)
    for vector in VECTORS["chain_negative"]:
        candidate_b = copy.deepcopy(triple["b"])
        candidate_envelope = copy.deepcopy(envelope)
        target = candidate_b if vector["target"] == "b" else candidate_envelope
        _set_path(target, vector["path"], vector["value"])
        with pytest.raises(SpecificationABCError) as refused:
            assert_abc_chain(triple["a"], candidate_b, candidate_envelope)
        assert refused.value.code == vector["error"]
    invalid_signature = copy.deepcopy(envelope)
    invalid_signature["signature"] = invalid_signature["signature"][:-3] + "A=="
    with pytest.raises(SpecificationABCError, match="E-ABC-016"):
        assert_abc_chain(triple["a"], triple["b"], invalid_signature)


def test_assert_abc_chain_enforces_cross_record_context_with_a_resigned_c() -> None:
    triple = VECTORS["triple"]
    for vector in VECTORS["chain_context_negative"]:
        envelope = {
            "version": "approval-envelope-v1",
            "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
            "payload": copy.deepcopy(triple["c_payload"]),
            "key_id": triple["key_id"],
            "signature": triple["signature"],
        }
        _set_path(envelope, vector["path"], vector["value"])
        envelope["signature"] = sign_approval_payload(
            envelope["payload"],
            "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=",
        )
        with pytest.raises(SpecificationABCError) as refused:
            assert_abc_chain(triple["a"], triple["b"], envelope)
        assert refused.value.code == vector["error"]


def test_assert_abc_chain_selects_digest_binding_before_context_binding() -> None:
    triple = VECTORS["triple"]
    envelope = {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": copy.deepcopy(triple["c_payload"]),
        "key_id": triple["key_id"],
        "signature": triple["signature"],
    }
    envelope["payload"]["b_digest"] = "sha256:" + "f" * 64
    envelope["payload"]["domain"] = "other-domain"
    with pytest.raises(SpecificationABCError) as refused:
        assert_abc_chain(triple["a"], triple["b"], envelope)
    assert refused.value.code == "E-ABC-019"


def test_closed_payload_shapes_refuse_extra_members() -> None:
    triple = VECTORS["triple"]
    validate_spec_packet(triple["a"])
    validate_generated_artifact_manifest(triple["b"])
    invalid_a = copy.deepcopy(triple["a"])
    invalid_a["generated_digest"] = "sha256:" + "0" * 64
    with pytest.raises(SpecificationABCError, match="E-ABC-012"):
        validate_spec_packet(invalid_a)
    invalid_b = copy.deepcopy(triple["b"])
    invalid_b["version"] = "generated-artifact-manifest-v2"
    with pytest.raises(SpecificationABCError, match="E-ABC-011"):
        validate_generated_artifact_manifest(invalid_b)


def test_validator_collects_simultaneous_version_shape_and_digest_candidates() -> None:
    invalid = copy.deepcopy(VECTORS["triple"]["b"])
    invalid["version"] = "generated-artifact-manifest-v2"
    invalid["extra"] = True
    invalid["a_digest"] = "bad"
    with pytest.raises(SpecificationABCError) as refused:
        validate_generated_artifact_manifest(invalid)
    assert refused.value.code == "E-ABC-011"


def test_manifest_validator_collects_nested_shape_candidates_before_digest_precedence() -> None:
    invalid = copy.deepcopy(VECTORS["triple"]["b"])
    invalid["a_digest"] = "bad"
    invalid["artifacts"]["protected"] = [{"path": "missing-digest"}]
    with pytest.raises(SpecificationABCError) as refused:
        validate_generated_artifact_manifest(invalid)
    assert refused.value.code == "E-ABC-012"

    invalid["version"] = "generated-artifact-manifest-v2"
    with pytest.raises(SpecificationABCError) as refused:
        validate_generated_artifact_manifest(invalid)
    assert refused.value.code == "E-ABC-011"


def test_parser_collects_duplicate_member_with_bad_number_before_selecting_registry_order() -> None:
    with pytest.raises(SpecificationABCError) as refused:
        parse_strict_json(b'{"a":1,"a":-0}')
    assert refused.value.code == "E-ABC-005"


def test_sign_helper_reproduces_the_frozen_detached_signature() -> None:
    triple = VECTORS["triple"]
    private = "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
    assert sign_approval_payload(triple["c_payload"], private) == triple["signature"]


def test_bytes_entry_points_accept_canonical_contract_bytes_and_refuse_noncanonical_bytes() -> None:
    triple = VECTORS["triple"]
    envelope = {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": triple["c_payload"],
        "key_id": triple["key_id"],
        "signature": triple["signature"],
    }
    assert validate_spec_packet_bytes(canonical_payload_bytes(triple["a"])) == triple["a"]
    assert validate_generated_artifact_manifest_bytes(
        canonical_payload_bytes(triple["b"]), spec_packet=triple["a"]
    ) == triple["b"]
    assert validate_approval_envelope_bytes(canonical_payload_bytes(envelope)) == envelope
    with pytest.raises(SpecificationABCError, match="E-ABC-009"):
        validate_spec_packet_bytes(b'{"version":"spec-packet-v1", "domain":"kernel"}')


def test_registry_missing_name_refuses_with_the_meta_code() -> None:
    registry_data = json.loads(
        (Path(__file__).parents[2] / "governance/schemas/specification/error-registry-v1.json").read_text("utf-8")
    )
    registry_data["precedence"].remove("signature")
    registry_data["check_order"].remove("signature")
    del registry_data["errors"]["signature"]
    registry = load_error_registry(json.dumps(registry_data).encode())
    with pytest.raises(SpecificationABCError, match="E-ABC-000"):
        registry.refuse("signature", "missing entry")


def test_registry_order_selects_every_adjacent_simultaneous_candidate_pair() -> None:
    registry_path = Path(__file__).parents[2] / "governance/schemas/specification/error-registry-v1.json"
    registry_data = json.loads(registry_path.read_text("utf-8"))
    registry = load_error_registry(json.dumps(registry_data).encode())
    for index, first in enumerate(registry.check_order[:-1]):
        second = registry.check_order[index + 1]
        candidates = specification_abc._FailureCollector(registry)
        candidates.add(first, "first simultaneous candidate")
        candidates.add(second, "second simultaneous candidate")
        with pytest.raises(SpecificationABCError) as refused:
            candidates.refuse_if_any()
        assert refused.value.code == registry.errors[first]["code"]
        permuted_data = copy.deepcopy(registry_data)
        for name in ("precedence", "check_order"):
            permuted_data[name][index : index + 2] = [second, first]
        permuted = load_error_registry(json.dumps(permuted_data).encode())
        candidates = specification_abc._FailureCollector(permuted)
        candidates.add(first, "first simultaneous candidate")
        candidates.add(second, "second simultaneous candidate")
        with pytest.raises(SpecificationABCError) as refused:
            candidates.refuse_if_any()
        assert refused.value.code == permuted.errors[second]["code"]


def test_legacy_sign_helper_is_not_public() -> None:
    assert not hasattr(specification_abc, "sign_approval_envelope")


def _assert_schema_fields(schema: dict[str, object], fields: frozenset[str]) -> None:
    assert set(schema["required"]) == fields
    assert set(schema["properties"]) == fields


def test_schema_closed_field_sets_match_the_implementation() -> None:
    schemas = {
        path.name: json.loads(path.read_text("utf-8"))
        for path in (Path(__file__).parents[2] / "governance/schemas/specification").glob("*.schema.json")
    }
    fields = specification_abc.CLOSED_FIELD_SETS
    spec = schemas["spec-packet-v1.schema.json"]
    _assert_schema_fields(spec, fields["spec_packet"])
    _assert_schema_fields(spec["properties"]["scope"], fields["scope"])
    _assert_schema_fields(spec["properties"]["ids"], fields["ids"])

    manifest = schemas["generated-artifact-manifest-v1.schema.json"]
    _assert_schema_fields(manifest, fields["manifest"])
    _assert_schema_fields(manifest["properties"]["artifacts"], fields["artifacts"])
    _assert_schema_fields(manifest["properties"]["artifacts"]["properties"]["invocation"], fields["invocation"])
    _assert_schema_fields(manifest["$defs"]["artifactList"]["items"], fields["artifact_row"])
    _assert_schema_fields(manifest["properties"]["exemptions"]["items"], fields["exemption_row"])

    approval = schemas["approval-envelope-v1.schema.json"]
    _assert_schema_fields(approval, fields["envelope"])
    payload = approval["$defs"]["payload"]
    _assert_schema_fields(payload, fields["approval_payload"])
    _assert_schema_fields(payload["properties"]["time_window"], fields["time_window"])
    capability = payload["properties"]["capability_request"]
    _assert_schema_fields(capability, fields["capability_request"])
    _assert_schema_fields(capability["properties"]["environment"], fields["environment"])
    _assert_schema_fields(capability["properties"]["network"], fields["network"])
    _assert_schema_fields(capability["properties"]["secret"], fields["secret"])
    _assert_schema_fields(capability["properties"]["commit"], fields["commit"])
    _assert_schema_fields(capability["properties"]["subagent"], fields["subagent"])
    _assert_schema_fields(payload["properties"]["profile_digests"], fields["profile_digests"])

    assert spec["$defs"]["idList"]["items"] == {"type": "string", "minLength": 1, "pattern": "\\S"}
    assert manifest["$defs"]["artifactList"]["items"]["properties"]["path"]["minLength"] == 1
    assert manifest["properties"]["exemptions"]["items"]["properties"]["path"]["minLength"] == 1
    assert manifest["properties"]["exemptions"]["items"]["properties"]["reason"]["minLength"] == 1
    assert manifest["properties"]["exemptions"]["items"]["properties"]["why_no_discriminating_red"]["minLength"] == 1
    for name in ("domain", "task", "principal", "role", "nonce"):
        assert payload["properties"][name]["minLength"] == 1
    for name in ("executable", "cwd"):
        assert capability["properties"][name]["minLength"] == 1
    public_key_pattern = approval["$defs"]["publicKey"]["pattern"]
    signature_pattern = approval["properties"]["signature"]["pattern"]
    assert public_key_pattern == "^ed25519:[A-Za-z0-9+/]{42}[AEIMQUYcgkosw048]=$"
    assert signature_pattern == "^ed25519:[A-Za-z0-9+/]{85}[AQgw]==$"
    patterns = {"publicKey": public_key_pattern, "signature": signature_pattern}
    for alias in VECTORS["base64_aliases"]:
        assert re.fullmatch(patterns[alias["schema"]], alias["value"]) is None
    for _ in range(128):
        assert base64.b64encode(secrets.token_bytes(32)).decode()[-2] in "AEIMQUYcgkosw048"
        assert base64.b64encode(secrets.token_bytes(64)).decode()[-3] in "AQgw"
    window = payload["properties"]["time_window"]
    assert window["properties"]["not_before"]["minimum"] == 0
    assert window["properties"]["not_after"]["minimum"] == 0
    assert "not_before must be less than or equal to not_after" in window["description"]
    assert "not_before <= not_after" in VECTORS["contract"]["time_window"]
