from __future__ import annotations

import inspect
from pathlib import Path

import pytest


@pytest.mark.parametrize("bad", [1.5, 2**53, -(2**53), "\U0001f600"])
def test_publication_validator_refuses_cross_language_values(bad: object) -> None:
    from ranex.governed_execution.verdict_publication import validate_publication_value

    with pytest.raises(ValueError):
        validate_publication_value({"value": bad})


def test_publication_validator_refuses_non_bmp_keys() -> None:
    from ranex.governed_execution.verdict_publication import validate_publication_value

    with pytest.raises(ValueError):
        validate_publication_value({"\U0001f600": "value"})


# --- RISK-07: the approver's own signature in the published envelope ------


def _record() -> dict[str, object]:
    from ranex.foundation.canonical import canonical_sha256

    body: dict[str, object] = {
        "verdict": "FAIL", "gate_id": "landing",
        "subject_digest": "sha256:" + "a" * 64,
        "subject_lane": "PRE_READINESS_PRODUCT_SLICE",
        "catalog_digest": "sha256:" + "b" * 64,
        "approver_id": "release-approver", "failing_rule": "TESTS_EXECUTED",
        "missing_claims": ["tests"], "considered": [],
        "causes": [{"claim_id": "tests", "cause": "absent"}],
        "rejections": [], "self_approval": False,
        "reason": "no evidence for required claim: tests",
        "journal_head": "sha256:" + "c" * 64,
    }
    return {**body, "record_digest": "sha256:" + canonical_sha256(body)}


def _published(
    tmp_path: Path, signer_private: str | None = None, **kwargs: object
) -> dict[str, object]:
    import json

    from ranex.foundation.signing import generate_keypair
    from ranex.governed_execution.verdict_publication import publish_verdict

    if signer_private is None:
        signer_private, _ = generate_keypair()
    record = _record()
    publish_verdict(
        tmp_path / "verdict.json", record, root=tmp_path,
        signer_id="kernel-verdict-signer", private_key=signer_private,
        **kwargs,
    )
    return json.loads((tmp_path / "verdict.json").read_text(encoding="utf-8"))


def _approver() -> tuple[str, str]:
    from ranex.foundation.signing import generate_keypair

    private, public = generate_keypair()
    return private, public


def test_publication_without_approver_signs_once(tmp_path: Path) -> None:
    envelope = _published(tmp_path)

    assert [entry["signer_id"] for entry in envelope["signatures"]] == [
        "kernel-verdict-signer"
    ]


def test_publication_appends_the_approvers_own_signature(tmp_path: Path) -> None:
    from ranex.foundation import verdict_signing
    from ranex.foundation.signing import generate_keypair, public_key_for

    signer_private, _ = generate_keypair()
    approver_private, _ = _approver()
    envelope = _published(
        tmp_path, signer_private,
        approver=("release-approver", approver_private),
    )

    signatures = envelope["signatures"]
    assert [entry["signer_id"] for entry in signatures] == [
        "kernel-verdict-signer", "release-approver"
    ]
    # Same signed fields, same domain: both signatures cover the identical
    # content, and the approver's verifies under the approver's public half.
    content = {
        field: envelope["record"][field]
        for field in verdict_signing.SIGNED_FIELDS
    }
    assert verdict_signing.verify_verdict(
        content, signatures[1]["signature"], public_key_for(approver_private),
        payload_type=envelope["payload_type"],
    )
    # Identical-input republication is byte-identical: Ed25519 is
    # deterministic, so repeats prove the publication is reproducible.
    first = (tmp_path / "verdict.json").read_bytes()
    _published(
        tmp_path, signer_private, approver=("release-approver", approver_private)
    )
    assert (tmp_path / "verdict.json").read_bytes() == first


def test_shared_atomic_writer_is_used_by_both_callers() -> None:
    from ranex.cli import host_confinement
    from ranex.governed_execution import verdict_publication

    assert "atomic_writer" in inspect.getsource(host_confinement)
    assert "atomic_writer" in inspect.getsource(verdict_publication)
    assert "host_confinement" not in inspect.getsource(verdict_publication)


def test_atomic_publication_preserves_previous_record_on_failure(tmp_path: Path, monkeypatch) -> None:
    from ranex.foundation import atomic_writer

    target = tmp_path / "verdict.json"
    target.write_bytes(b"previous")
    monkeypatch.setattr(atomic_writer.os, "replace", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("boom")))
    with pytest.raises(OSError):
        atomic_writer.write_atomic(target, b"new", root=tmp_path)
    assert target.read_bytes() == b"previous"
    assert not list(tmp_path.glob(".verdict.json.*"))


def test_atomic_writer_refuses_intermediate_symlink_escape(tmp_path: Path) -> None:
    from ranex.foundation import atomic_writer

    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "publication").symlink_to(outside, target_is_directory=True)

    with pytest.raises(OSError):
        atomic_writer.write_atomic(
            root / "publication" / "verdict.json", b"escaped", root=root
        )

    assert not (outside / "verdict.json").exists()


def test_atomic_writer_forces_exact_read_only_mode_despite_umask(tmp_path: Path) -> None:
    import os
    import stat

    from ranex.foundation import atomic_writer

    target = tmp_path / "verdict.json"
    previous = os.umask(0o777)
    try:
        atomic_writer.write_atomic(target, b"record", root=tmp_path)
    finally:
        os.umask(previous)

    assert stat.S_IMODE(target.stat().st_mode) == 0o444
