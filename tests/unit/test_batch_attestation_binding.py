"""Qualification verification binds a verified signature to the exact payload."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256, command_digest
from ranex.foundation.signing import CATALOG_ABSENT, ENVELOPE_TYPE, GATE_ABSENT, sign_evidence
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.application import specification_batch as batch


def signed_artifact(root, vectors, *, c_digest):
    root.mkdir()
    triple = vectors["triple"]
    descriptor = json.loads(
        (
            Path(__file__).parents[1] / "contract/fixtures/specification/approved-batch-v1.json"
        ).read_bytes()
    )
    child = root / "children" / "A" / "evidence.json"
    child.parent.mkdir(parents=True)
    child.write_bytes(b"[]")
    identities = {
        "a_digest": triple["a_digest"],
        "b_digest": triple["b_digest"],
        "base_digest": triple["c_payload"]["base_digest"],
        "c_digest": c_digest,
        "child_requests_digest": vectors["digests"]["children"],
        "descriptor_digest": vectors["digests"]["descriptor"],
        "base_commit": descriptor["base_commit"],
    }
    results_digest = "sha256:" + canonical_sha256(
        {"results": [{"task_id": "A", "evidence_digest": batch._sha256(child.read_bytes())}]}
    )
    record = batch.BatchQualificationRecord(identities, results_digest, "owner")
    journal_path = root / "journal.sqlite3"
    appended = Journal(journal_path).append_if_head(None, record)
    payload = {
        **identities,
        "batch_digest": record.as_record()["batch_digest"],
        "child_results_digest": results_digest,
        "producer_id": "owner",
        "publication_allowed": False,
        "qualification_journal": {
            "head": appended.head,
            "previous_head": appended.previous_head,
            "seq": appended.position,
        },
        "qualification_record_digest": "sha256:" + canonical_sha256(record.as_record()),
        "version": "batch-qualification-payload-v1",
    }
    content = {
        "envelope_type": ENVELOPE_TYPE,
        "gate_id": GATE_ABSENT,
        "catalog_digest": CATALOG_ABSENT,
        "claim_id": "approved-batch-qualified",
        "command": "python",
        "command_digest": command_digest(("python",)),
        "confinement_profile_digest": "sha256:" + "a" * 64,
        "confinement_result_digest": "sha256:" + "b" * 64,
        "executable_path": "/usr/bin/python",
        "exit_code": 0,
        "producer_id": "owner",
        "subject_digest": payload["base_digest"],
        "suite_results": {
            "counts": {
                "errors": 0,
                "failed": 0,
                "passed": 1,
                "skipped": 0,
                "xfailed": 0,
                "xpassed": 0,
            },
            "extra_count": 0,
            "manifest_digest": identities["descriptor_digest"],
            "missing": [],
            "non_passed": [],
            "outcome_digest": batch._sha256(canonical_json_bytes(payload)),
        },
    }
    artifact = {
        "attestation": {
            **content,
            "signature": sign_evidence(content, vectors["fixture_private_key"]),
        },
        "payload": payload,
        "version": "batch-qualification-v1",
    }
    return artifact, journal_path


@pytest.mark.parametrize("transplant", [False, True])
def test_verification_requires_the_exact_signed_qualification_payload(
    tmp_path, monkeypatch, transplant
):
    fixtures = Path(__file__).parents[1] / "contract/fixtures/specification"
    vectors = json.loads((fixtures / "approved-batch-v1-vectors.json").read_bytes())
    triple = vectors["triple"]
    artifact, journal_path = signed_artifact(
        tmp_path / "current", vectors, c_digest=triple["c_digest"]
    )
    if transplant:
        old, _ = signed_artifact(tmp_path / "prior", vectors, c_digest="sha256:" + "f" * 64)
        # A real valid signature from the same producer/subject, over another batch.
        artifact["attestation"] = copy.deepcopy(old["attestation"])
    artifact_path = tmp_path / "current" / "qualification.json"
    artifact_path.write_bytes(canonical_json_bytes(artifact))
    authority = []
    envelope = {
        "version": "approval-envelope-v1",
        "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
        "payload": triple["c_payload"],
        "key_id": triple["key_id"],
        "signature": triple["signature"],
    }
    for name, value in (("a", triple["a"]), ("b", triple["b"]), ("c", envelope)):
        path = tmp_path / f"{name}.json"
        path.write_bytes(canonical_json_bytes(value))
        authority.append(path)
    keyring = f"producers:\n  owner: {triple['key_id']}\n".encode()
    monkeypatch.setattr(
        batch, "_git_text", lambda *args, **kwargs: artifact["payload"]["base_commit"]
    )
    monkeypatch.setattr(batch, "_git_blob", lambda *args, **kwargs: keyring)
    monkeypatch.setattr(
        "ranex.cli.main.subject_digest_for", lambda *args: artifact["payload"]["base_digest"]
    )
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
    arguments = dict(
        spec_packet=authority[0],
        artifact_manifest=authority[1],
        approval_envelope=authority[2],
        artifact_path=artifact_path,
        target=tmp_path,
        journal_path=journal_path,
    )
    if transplant:
        with pytest.raises(batch.BatchRefusal, match="E-BATCH-PROTECTED-ARTIFACT"):
            batch.verify_qualification(**arguments)
    else:
        result = batch.verify_qualification(**arguments)
        assert result["c_digest"] == triple["c_digest"]
    assert before == {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}
