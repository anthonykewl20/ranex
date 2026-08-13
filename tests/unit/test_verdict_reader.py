from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.signing import generate_keypair

SUBJECT = "sha256:" + "a" * 64
CATALOG = "sha256:" + "b" * 64
SIGNER = "kernel-verdict-signer"


def record() -> dict[str, object]:
    body = {
        "verdict": "FAIL", "gate_id": "landing", "subject_digest": SUBJECT,
        "subject_lane": "PRE_READINESS_PRODUCT_SLICE", "catalog_digest": CATALOG,
        "approver_id": "owner", "failing_rule": "TESTS_EXECUTED",
        "missing_claims": ["tests"], "considered": [],
        "causes": [{"claim_id": "tests", "cause": "absent"}],
        "rejections": [], "self_approval": False,
        "reason": "no evidence for required claim: tests",
    }
    return {**body, "record_digest": "sha256:" + canonical_sha256(body)}


def envelope(private: str, **overrides: object) -> dict[str, object]:
    from ranex.foundation import verdict_signing

    projected = record()
    projected.update(overrides.pop("record", {}))
    content = {key: value for key, value in projected.items() if key != "record_digest"}
    projected["record_digest"] = "sha256:" + canonical_sha256(content)
    return {
        "payload_type": overrides.pop("payload_type", verdict_signing.PAYLOAD_TYPE),
        "record": projected,
        "signatures": overrides.pop("signatures", [{
            "signer_id": overrides.pop("signer_id", SIGNER),
            "signature": verdict_signing.sign_verdict(content, private),
        }]),
    }


def read(path: Path, keyring: dict[str, str], **context: object):
    from ranex.governed_execution.verdict_reader import read_verdict

    return read_verdict(
        path, keyring,
        subject_digest=context.get("subject_digest", SUBJECT),
        gate_id=context.get("gate_id", "landing"),
        catalog_digest=context.get("catalog_digest", CATALOG),
        approver_id=context.get("approver_id", "owner"),
    )


def write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_reader_state_mapping_is_total_without_default_arm() -> None:
    from ranex.governed_execution import verdict_reader

    expected = {
        "absent", "malformed", "unsigned", "bad-signature", "unknown-signer",
        "wrong-payload-type", "missing-key", "context-mismatch", "unknown-cause",
        "verified",
    }
    assert {str(state) for state in verdict_reader.ReadState} == expected
    assert set(verdict_reader.STATE_PRESENTATION) == set(verdict_reader.ReadState)


def test_reader_distinguishes_absence_and_missing_key(tmp_path: Path) -> None:
    private, public = generate_keypair()
    assert str(read(tmp_path / "absent.json", {SIGNER: public}).state) == "absent"
    path = write(tmp_path / "verdict.json", envelope(private))
    assert str(read(path, {}).state) == "missing-key"


@pytest.mark.parametrize(
    "mutation, expected",
    [
        ("bad-signature", "bad-signature"), ("unknown-signer", "unknown-signer"),
        ("wrong-payload-type", "wrong-payload-type"), ("zero-signatures", "unsigned"),
        ("unknown-cause", "unknown-cause"),
    ],
)
def test_reader_maps_signed_transport_refusals(tmp_path: Path, mutation: str, expected: str) -> None:
    private, public = generate_keypair()
    value = envelope(private)
    if mutation == "bad-signature":
        other_private, _ = generate_keypair()
        value["signatures"][0]["signature"] = envelope(other_private)["signatures"][0]["signature"]
    elif mutation == "unknown-signer":
        value["signatures"][0]["signer_id"] = "other"
    elif mutation == "wrong-payload-type":
        value["payload_type"] = "text/plain"
    elif mutation == "zero-signatures":
        value["signatures"] = []
    else:
        value = envelope(private, record={
            "causes": [{"claim_id": "tests", "cause": "future-cause"}],
        })
    state = read(write(tmp_path / "verdict.json", value), {SIGNER: public}).state
    assert str(state) == expected


@pytest.mark.parametrize("field", ["subject_digest", "gate_id", "catalog_digest", "approver_id"])
def test_reader_refuses_every_context_mismatch(tmp_path: Path, field: str) -> None:
    private, public = generate_keypair()
    path = write(tmp_path / "verdict.json", envelope(private))
    context = {field: "sha256:" + "c" * 64 if "digest" in field else "other"}
    assert str(read(path, {SIGNER: public}, **context).state) == "context-mismatch"


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), "\ud800"])
def test_reader_returns_malformed_for_noncanonical_json_values(tmp_path: Path, bad: object) -> None:
    private, public = generate_keypair()
    value = envelope(private)
    value["record"]["reason"] = bad
    path = write(tmp_path / "verdict.json", value)

    assert str(read(path, {SIGNER: public}).state) == "malformed"
