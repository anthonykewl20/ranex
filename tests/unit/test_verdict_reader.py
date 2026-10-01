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
        "journal_head": "sha256:" + "c" * 64,
        "history_verified": False, "observation_checkpoint": None,
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
        approvers=context.get("approvers"),
        repository_root=context.get("repository_root"),
        history_checkpoint_path=context.get("history_checkpoint_path"),
    )


def write(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_reader_state_mapping_is_total_without_default_arm() -> None:
    from ranex.governed_execution import verdict_reader

    expected = {
        "absent", "malformed", "unsigned", "bad-signature", "unknown-signer",
        "wrong-payload-type", "missing-key", "context-mismatch", "unknown-cause",
        "unapproved", "unanchored", "verified",
    }
    assert {str(state) for state in verdict_reader.ReadState} == expected
    assert set(verdict_reader.STATE_PRESENTATION) == set(verdict_reader.ReadState)


# --- RISK-07: the catalogued approver's own signature on the verdict ------
#
# The record below names approver_id "owner". `approver()` mints that
# principal's own keypair so the arms can sign, strip and mutate the second
# signature the way a real envelope carries it.


def approver() -> tuple[str, str, dict[str, tuple[str, ...]]]:
    """The catalogued approver's keypair and the reader's approver map."""

    private, public = generate_keypair()
    return private, public, {"owner": (public,)}


def cosigned(private: str, approver_private: str, projected=None) -> list[dict[str, object]]:
    from ranex.foundation import verdict_signing

    projected = projected if projected is not None else record()
    content = {key: value for key, value in projected.items() if key != "record_digest"}
    return [
        {"signer_id": SIGNER, "signature": verdict_signing.sign_verdict(content, private)},
        {"signer_id": "owner", "signature": verdict_signing.sign_verdict(content, approver_private)},
    ]


def test_reader_verifies_every_signature_and_passes_cosigned_verdict(tmp_path: Path) -> None:
    from ranex.governed_execution.adapters.persistence.history import bootstrap_history, log_id
    from ranex.governed_execution.adapters.persistence.sqlite.observations import GENESIS

    private, public = generate_keypair()
    approver_private, _, approvers = approver()
    repository = tmp_path / "subject"
    repository.mkdir()
    evidence = repository / "evidence.json"
    checkpoint = tmp_path / "history.json"
    bootstrap_history(evidence, checkpoint, private, public, repository)
    value = envelope(private, record={
        "history_verified": True,
        "observation_checkpoint": {"log_id": log_id(evidence), "head": GENESIS, "position": 0},
    })
    value["signatures"] = cosigned(private, approver_private, value["record"])
    path = write(tmp_path / "verdict.json", value)

    assert str(read(path, {SIGNER: public}, approvers=approvers,
                    repository_root=repository, history_checkpoint_path=checkpoint).state) == "verified"


def test_reader_returns_unapproved_when_catalogued_approver_did_not_sign(
    tmp_path: Path,
) -> None:
    private, public = generate_keypair()
    _, _, approvers = approver()
    # The archived shape: the verdict signer alone, the record naming an
    # approver the caller's catalog carries.
    path = write(tmp_path / "verdict.json", envelope(private))

    assert str(read(path, {SIGNER: public}, approvers=approvers).state) == "unapproved"


def test_single_signature_stays_readable_without_the_approver_catalog(
    tmp_path: Path,
) -> None:
    # ADR-057's precedent, held: a caller that verifies archives (no approver
    # map, because it is not deciding anything) still reads the single-signature
    # record VERIFIED.
    private, public = generate_keypair()
    path = write(tmp_path / "verdict.json", envelope(private))

    from ranex.governed_execution.verdict_reader import read_verdict_unbound
    assert str(read_verdict_unbound(path, {SIGNER: public}).state) == "verified"
    assert str(read(path, {SIGNER: public}).state) == "unanchored"


def test_reader_refuses_altered_or_foreign_approver_signature(tmp_path: Path) -> None:
    private, public = generate_keypair()
    _, _, approvers = approver()
    other_private, _ = generate_keypair()
    value = envelope(private)
    value["signatures"] = cosigned(private, other_private)
    path = write(tmp_path / "verdict.json", value)

    assert str(read(path, {SIGNER: public}, approvers=approvers).state) == "bad-signature"


def test_reader_refuses_unknown_or_duplicate_co_signers(tmp_path: Path) -> None:
    from ranex.foundation import verdict_signing

    private, public = generate_keypair()
    _, _, approvers = approver()
    projected = record()
    content = {key: value for key, value in projected.items() if key != "record_digest"}
    judgment = verdict_signing.sign_verdict(content, private)
    value = envelope(private)
    value["signatures"] = [
        {"signer_id": SIGNER, "signature": judgment},
        # Neither the judgment keyring nor the approver catalog carries this id.
        {"signer_id": "stranger", "signature": judgment},
    ]
    stranger = write(tmp_path / "stranger.json", value)
    assert str(read(stranger, {SIGNER: public}, approvers=approvers).state) == "unknown-signer"

    value["signatures"] = [
        {"signer_id": SIGNER, "signature": judgment},
        # One signer, two entries: which of the two is real would depend on
        # read order, so the shape itself is refused.
        {"signer_id": SIGNER, "signature": judgment},
    ]
    duplicate = write(tmp_path / "duplicate.json", value)
    assert str(read(duplicate, {SIGNER: public}, approvers=approvers).state) == "malformed"


def test_catalogued_approver_may_not_stand_in_for_the_judgment_signer(
    tmp_path: Path,
) -> None:
    # Only the approver's key signed: the record's signer-of-record is unknown
    # to the judgment keyring, so the approver cannot mint verdicts alone.
    approver_private, _, approvers = approver()
    _, judgment_public = generate_keypair()
    value = envelope(approver_private, signer_id="owner")
    path = write(tmp_path / "verdict.json", value)

    assert str(read(path, {SIGNER: judgment_public}, approvers=approvers).state) == "unknown-signer"


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
