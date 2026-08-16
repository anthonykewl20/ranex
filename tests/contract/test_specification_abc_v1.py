from __future__ import annotations

import base64
import copy
import json
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import (
    SpecificationABCError,
    canonical_payload_bytes,
    parse_strict_json,
    payload_digest,
    sign_approval_envelope,
    validate_approval_envelope,
    validate_generated_artifact_manifest,
    validate_spec_packet,
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


def test_negative_vectors_select_registry_codes() -> None:
    for vector in VECTORS["negative"]:
        raw = base64.b64decode(vector["raw_base64"]) if "raw_base64" in vector else vector["raw"].encode()
        with pytest.raises(SpecificationABCError) as refused:
            parse_strict_json(raw)
        assert refused.value.code == vector["error"]
    for vector in VECTORS["payload_negative"]:
        value = copy.deepcopy(VECTORS["triple"][vector["source"]])
        value[vector["field"]] = vector["value"]
        with pytest.raises(SpecificationABCError) as refused:
            validate_generated_artifact_manifest(value)
        assert refused.value.code == vector["error"]


def test_recorded_vector_digests_recompute() -> None:
    triple = VECTORS["triple"]
    assert payload_digest(triple["a"]) == triple["a_digest"]
    assert payload_digest(triple["b"]) == triple["b_digest"]
    assert payload_digest(triple["c_payload"]) == triple["c_digest"]


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


def test_sign_helper_reproduces_the_frozen_detached_signature() -> None:
    triple = VECTORS["triple"]
    private = "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="
    assert sign_approval_envelope(triple["c_payload"], private) == triple["signature"]
