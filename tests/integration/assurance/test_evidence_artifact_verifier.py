from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from ranex.assurance.adapters.filesystem.artifact_verifier import (
    EvidenceArtifactError,
    verify_evidence_artifact,
)
from ranex.assurance.api.contracts import EvidenceRecord, GateOutcome
from ranex.foundation.identity import Identity


def identity(prefix: str, suffix: str) -> Identity:
    return Identity.parse(
        f"{prefix}_01890f47-25a1-7{suffix}-98b3-5f5f6bb25af7",
        expected_prefix=prefix,
    )


def record(digest: str) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=identity("evd", "401"),
        claim_id="CLAIM-ARTIFACT",
        outcome=GateOutcome.PASS,
        project_id=identity("prj", "402"),
        execution_id=identity("run", "403"),
        action="EXECUTION_START",
        subject_version=1,
        producer_id=identity("principal", "404"),
        producer_role="qualified_checker",
        command="checker",
        exit_code=0,
        observed_at="2026-07-29T06:00:00Z",
        artifact_sha256="sha256:" + digest,
    )


def test_verifier_hashes_safe_descriptor_and_marks_record_verified(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "nested" / "result.log"
    artifact.parent.mkdir()
    content = b"qualified result\n"
    artifact.write_bytes(content)
    evidence = record(hashlib.sha256(content).hexdigest())

    verified = verify_evidence_artifact(
        evidence,
        artifact_path="nested/result.log",
        evidence_root=tmp_path,
    )

    assert verified == replace(evidence, artifact_verified=True)


def test_verifier_rejects_symlink_and_digest_mismatch(tmp_path: Path) -> None:
    target = tmp_path / "target.log"
    target.write_bytes(b"target")
    (tmp_path / "link.log").symlink_to(target)

    with pytest.raises(EvidenceArtifactError, match="symlink"):
        verify_evidence_artifact(
            record(hashlib.sha256(b"target").hexdigest()),
            artifact_path="link.log",
            evidence_root=tmp_path,
        )
    with pytest.raises(EvidenceArtifactError, match="digest"):
        verify_evidence_artifact(
            record("0" * 64),
            artifact_path="target.log",
            evidence_root=tmp_path,
        )


@pytest.mark.parametrize("artifact_path", ["/etc/passwd", "../escape", "."])
def test_verifier_rejects_paths_outside_trusted_root(
    tmp_path: Path,
    artifact_path: str,
) -> None:
    with pytest.raises(EvidenceArtifactError, match="contained relative path"):
        verify_evidence_artifact(
            record("0" * 64),
            artifact_path=artifact_path,
            evidence_root=tmp_path,
        )
