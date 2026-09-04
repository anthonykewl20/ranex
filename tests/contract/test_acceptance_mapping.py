"""Contract arms for the ReadState→outcome mapping: closed and fail-closed.

Every reader state has exactly one outward outcome, only `VERIFIED` is
publishable, and the mapping is pinned against real signed publications —
built here with the same signing primitive `gate evaluate` publishes with —
so the contract is about bytes on disk, not about a table someone else
promises to keep current.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.signing import generate_keypair
from ranex.foundation.verdict_signing import PAYLOAD_TYPE, SIGNED_FIELDS, sign_verdict
from ranex.github_app.acceptance import (
    ABSENT_CODE,
    ACCEPTED,
    REJECTED_PREFIX,
    code_for_state,
    resolve_acceptance,
    verdict_path,
)
from ranex.github_app.binding import PrHeadBinding, subject_digest_for_tree
from ranex.governed_execution.verdict_reader import ReadState

GATE = "landing"
APPROVER = "operator"


def binding_for(tree: str) -> PrHeadBinding:
    return PrHeadBinding(
        head_sha="a" * 40, tree=tree, subject_digest=subject_digest_for_tree(tree)
    )


def record_content(binding: PrHeadBinding) -> dict[str, object]:
    return {
        "verdict": "PASS",
        "gate_id": GATE,
        "subject_digest": binding.subject_digest,
        "subject_lane": "PRE_READINESS_PRODUCT_SLICE",
        "catalog_digest": None,
        "approver_id": APPROVER,
        "failing_rule": None,
        "missing_claims": [],
        "considered": [],
        "causes": [],
        "rejections": [],
        "self_approval": False,
        "reason": "unit binding contract",
    }


def write_publication(
    directory: Path, binding: PrHeadBinding, private_key: str, *, signer: str = "verdict-signer"
) -> None:
    content = record_content(binding)
    record = {**content, "record_digest": "sha256:" + canonical_sha256(content)}
    envelope = {
        "payload_type": PAYLOAD_TYPE,
        "record": record,
        "signatures": [
            {"signer_id": signer, "signature": sign_verdict(content, private_key)}
        ],
    }
    path = verdict_path(directory, binding)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(envelope), encoding="utf-8")


@pytest.fixture()
def keyring() -> tuple[dict[str, str], str]:
    private, public = generate_keypair()
    return {"verdict-signer": public}, private


def test_every_reader_state_has_exactly_one_outcome() -> None:
    assert set(ReadState) == {
        "absent", "malformed", "unsigned", "bad-signature", "unknown-signer",
        "wrong-payload-type", "missing-key", "context-mismatch",
        "unknown-cause", "verified",
    }
    publishable = [state for state in ReadState if code_for_state(state) == ACCEPTED]
    assert publishable == [ReadState.VERIFIED]
    absence = [state for state in ReadState if code_for_state(state) == ABSENT_CODE]
    assert absence == [ReadState.ABSENT]
    rejected = {
        state: code_for_state(state)
        for state in ReadState
        if state not in (ReadState.VERIFIED, ReadState.ABSENT)
    }
    assert all(
        code.startswith(REJECTED_PREFIX) and code.endswith(state.value)
        for state, code in rejected.items()
    )


def test_a_verified_publication_is_the_one_publishable_outcome(
    tmp_path: Path, keyring: tuple[dict[str, str], str]
) -> None:
    keys, private = keyring
    binding = binding_for("1" * 40)
    write_publication(tmp_path, binding, private)
    acceptance = resolve_acceptance(
        tmp_path, binding, keys,
        gate_id=GATE, catalog_digest=None, approver_id=APPROVER,
    )
    assert acceptance.code == ACCEPTED
    assert acceptance.state is ReadState.VERIFIED
    assert acceptance.publishable
    assert acceptance.record is not None
    assert acceptance.record["subject_digest"] == binding.subject_digest


def test_no_publication_at_all_is_named_as_absence(tmp_path: Path) -> None:
    acceptance = resolve_acceptance(
        tmp_path, binding_for("2" * 40), {"verdict-signer": "ed25519:" + "A" * 43},
        gate_id=GATE, catalog_digest=None, approver_id=APPROVER,
    )
    assert acceptance.code == ABSENT_CODE
    assert not acceptance.publishable


def test_a_publication_for_another_subject_is_a_rejection_not_an_absence(
    tmp_path: Path, keyring: tuple[dict[str, str], str]
) -> None:
    keys, private = keyring
    written = binding_for("3" * 40)
    write_publication(tmp_path, written, private)
    # Misfiled: the asked subject's path holds a record naming another
    # subject. The path alone would call it present; the reader does not.
    asked = binding_for("4" * 40)
    verdict_path(tmp_path, asked).write_text(
        verdict_path(tmp_path, written).read_text(encoding="utf-8"), encoding="utf-8"
    )
    acceptance = resolve_acceptance(
        tmp_path, asked, keys,
        gate_id=GATE, catalog_digest=None, approver_id=APPROVER,
    )
    assert acceptance.code == f"{REJECTED_PREFIX}context-mismatch"
    assert not acceptance.publishable


def test_a_forged_signature_is_a_named_rejection(
    tmp_path: Path, keyring: tuple[dict[str, str], str]
) -> None:
    keys, private = keyring
    binding = binding_for("5" * 40)
    write_publication(tmp_path, binding, private)
    # A different honest key's signature over the same bytes: verifiable
    # structure, wrong signer — the classic forgery shape.
    other_private, _ = generate_keypair()
    path = verdict_path(tmp_path, binding)
    envelope = json.loads(path.read_text(encoding="utf-8"))
    envelope["signatures"][0]["signature"] = sign_verdict(
        {field: envelope["record"][field] for field in SIGNED_FIELDS}, other_private
    )
    path.write_text(json.dumps(envelope), encoding="utf-8")
    acceptance = resolve_acceptance(
        tmp_path, binding, keys,
        gate_id=GATE, catalog_digest=None, approver_id=APPROVER,
    )
    assert acceptance.code == f"{REJECTED_PREFIX}bad-signature"
    assert not acceptance.publishable


def test_a_stranger_signer_is_a_named_rejection(
    tmp_path: Path, keyring: tuple[dict[str, str], str]
) -> None:
    keys, private = keyring
    binding = binding_for("6" * 40)
    write_publication(tmp_path, binding, private, signer="stranger")
    acceptance = resolve_acceptance(
        tmp_path, binding, keys,
        gate_id=GATE, catalog_digest=None, approver_id=APPROVER,
    )
    assert acceptance.code == f"{REJECTED_PREFIX}unknown-signer"
    assert not acceptance.publishable


def test_the_publication_path_is_the_publishers_convention(tmp_path: Path) -> None:
    binding = binding_for("7" * 40)
    assert verdict_path(tmp_path, binding) == tmp_path / (
        binding.subject_digest.removeprefix("sha256:") + ".json"
    )
