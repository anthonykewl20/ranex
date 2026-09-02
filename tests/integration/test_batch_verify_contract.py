"""In-process coverage for approved-batch qualification verification."""

from __future__ import annotations

import hashlib
import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from ranex.cli.main import main, subject_digest_for
from ranex.foundation.canonical import canonical_json_bytes, canonical_sha256, command_digest
from ranex.foundation.signing import sign_evidence
from ranex.foundation.specification_abc import payload_digest
from ranex.governed_execution.adapters.persistence.sqlite.journal import Journal
from ranex.governed_execution.application.specification_batch import (
    BatchQualificationRecord,
    BatchRefusal,
    verify_publication_refusal,
    verify_qualification,
)

ROOT = Path(__file__).parents[2]
FIXTURES = ROOT / "tests/contract/fixtures/specification"
VECTORS = json.loads(
    (FIXTURES / "approved-batch-v1-vectors.json").read_text(encoding="utf-8")
)


@dataclass(frozen=True)
class QualificationFixture:
    artifact_manifest: Path
    artifact_path: Path
    approval_envelope: Path
    approval_payload: dict[str, object]
    journal: Path
    spec_packet: Path
    target: Path


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        capture_output=True,
        check=False,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _keygen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], producer: str
) -> tuple[Path, str]:
    key_path = tmp_path / "keys" / f"{producer}.key"
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(key_path))
    assert main(["keygen", "--producer", producer]) == 0
    public_key = next(
        line.removeprefix(f"    {producer}: ")
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(f"    {producer}: ")
    )
    assert key_path.is_file() and key_path.stat().st_mode & 0o077 == 0
    return key_path, public_key


def _approve(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    payload: dict[str, object],
    name: str,
) -> Path:
    source = tmp_path / f"{name}-payload.json"
    envelope = tmp_path / f"{name}-envelope.json"
    source.write_bytes(canonical_json_bytes(payload))
    assert main(["specification", "approve", "--payload", str(source), "--output", str(envelope)]) == 0
    assert capsys.readouterr().out == f"APPROVED  {envelope}  key_id={payload['key']}\n"
    return envelope


def _make_target(tmp_path: Path, public_key: str) -> tuple[Path, str, str]:
    target = tmp_path / "governed"
    target.mkdir()
    _git(target, "init", "--quiet", "--initial-branch=main")
    keyring = target / "governance/producers.yaml"
    keyring.parent.mkdir()
    keyring.write_text(f"producers:\n  owner: {public_key}\n", encoding="utf-8")
    _git(target, "add", "governance/producers.yaml")
    _git(
        target,
        "-c",
        "user.name=Ranex Integration",
        "-c",
        "user.email=integration@ranex.invalid",
        "commit",
        "--quiet",
        "-m",
        "test: governed verification target",
    )
    base = _git(target, "rev-parse", "HEAD")
    return target, base, subject_digest_for(target, base)


def _write_qualification(
    root: Path,
    *,
    private_key: str,
    approval_payload: dict[str, object],
    base: str,
    subject_digest: str,
    journal: Path,
) -> Path:
    outcome = root / "outcome"
    evidence = []
    for task_id in ("SLICE-036-child-A", "SLICE-036-child-B", "SLICE-036-child-C"):
        path = outcome / "children" / task_id / "evidence.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_json_bytes({"task_id": task_id, "value": "ok"}))
        evidence.append(
            {
                "task_id": task_id,
                "evidence_digest": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    identities = {
        "a_digest": approval_payload["a_digest"],
        "b_digest": approval_payload["b_digest"],
        "base_commit": base,
        "base_digest": subject_digest,
        "c_digest": payload_digest(approval_payload),
        "child_requests_digest": "sha256:" + "1" * 64,
        "descriptor_digest": "sha256:" + "2" * 64,
    }
    child_results_digest = "sha256:" + canonical_sha256({"results": evidence})
    record = BatchQualificationRecord(identities, child_results_digest, "owner")
    append = Journal(journal).append_if_head(None, record)
    record_value = record.as_record()
    payload = {
        **identities,
        "batch_digest": record_value["batch_digest"],
        "child_results_digest": child_results_digest,
        "producer_id": "owner",
        "publication_allowed": False,
        "qualification_journal": {
            "head": append.head,
            "previous_head": append.previous_head,
            "seq": append.position,
        },
        "qualification_record_digest": "sha256:" + canonical_sha256(record_value),
        "version": "batch-qualification-payload-v1",
    }
    command = ("python", "-m", "ranex.cli.main", "task", "batch", "qualify")
    content = {
        "claim_id": "approved-batch-qualified",
        "command": shlex.join(command),
        "command_digest": command_digest(command),
        "confinement_profile_digest": "sha256:" + canonical_sha256({"profiles": []}),
        "confinement_result_digest": "sha256:" + canonical_sha256({"results": []}),
        "executable_path": str(Path(sys.executable).resolve()),
        "exit_code": 0,
        "producer_id": "owner",
        "subject_digest": subject_digest,
        "suite_results": {
            "counts": {"errors": 0, "failed": 0, "passed": 3, "skipped": 0, "xfailed": 0, "xpassed": 0},
            "extra_count": 0,
            "manifest_digest": identities["descriptor_digest"],
            "missing": [],
            "non_passed": [],
            "outcome_digest": "sha256:" + canonical_sha256(payload),
        },
    }
    artifact = {
        "attestation": {**content, "signature": sign_evidence(content, private_key)},
        "payload": payload,
        "version": "batch-qualification-v1",
    }
    path = outcome / "batch-qualification.json"
    path.write_bytes(canonical_json_bytes(artifact))
    return path


@pytest.fixture()
def qualification_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> QualificationFixture:
    key_path, public_key = _keygen(tmp_path, monkeypatch, capsys, "owner")
    target, base, subject_digest = _make_target(tmp_path, public_key)
    a = dict(VECTORS["triple"]["a"])
    b = dict(VECTORS["triple"]["b"])
    b["a_digest"] = payload_digest(a)
    spec_packet = tmp_path / "spec-packet.json"
    artifact_manifest = tmp_path / "artifact-manifest.json"
    spec_packet.write_bytes(canonical_json_bytes(a))
    artifact_manifest.write_bytes(canonical_json_bytes(b))
    approval_payload = dict(VECTORS["triple"]["c_payload"])
    approval_payload.update(
        {
            "a_digest": payload_digest(a),
            "b_digest": payload_digest(b),
            "base_digest": subject_digest,
            "journal_predecessor": None,
            "key": public_key,
            "subject_digest": subject_digest,
        }
    )
    approval_envelope = _approve(tmp_path, capsys, approval_payload, "approval")
    artifact_path = _write_qualification(
        tmp_path,
        private_key=key_path.read_text(encoding="utf-8").strip(),
        approval_payload=approval_payload,
        base=base,
        subject_digest=subject_digest,
        journal=tmp_path / "journal.sqlite3",
    )
    return QualificationFixture(
        artifact_manifest=artifact_manifest,
        artifact_path=artifact_path,
        approval_envelope=approval_envelope,
        approval_payload=approval_payload,
        journal=tmp_path / "journal.sqlite3",
        spec_packet=spec_packet,
        target=target,
    )


def _verify_arguments(fixture: QualificationFixture, *, manifest: Path | None = None, envelope: Path | None = None, qualification: Path | None = None) -> list[str]:
    return [
        "task", "batch", "verify",
        "--spec-packet", str(fixture.spec_packet),
        "--artifact-manifest", str(manifest or fixture.artifact_manifest),
        "--approval-envelope", str(envelope or fixture.approval_envelope),
        "--qualification", str(qualification or fixture.artifact_path),
        "--target", str(fixture.target),
        "--journal", str(fixture.journal),
    ]


def _assert_cli_refusal(capsys: pytest.CaptureFixture[str], arguments: list[str], code: str) -> None:
    assert main(arguments) == 1
    assert capsys.readouterr().err.startswith(f"ERROR  {code}:")


def test_verify_qualification_rechecks_real_signed_facts_and_cli_refusals(
    qualification_fixture: QualificationFixture,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fixture = qualification_fixture
    facts = verify_qualification(
        spec_packet=fixture.spec_packet,
        artifact_manifest=fixture.artifact_manifest,
        approval_envelope=fixture.approval_envelope,
        artifact_path=fixture.artifact_path,
        target=fixture.target,
        journal_path=fixture.journal,
    )
    assert facts["a_digest"] == fixture.approval_payload["a_digest"]
    assert facts["b_digest"] == fixture.approval_payload["b_digest"]
    assert facts["c_digest"] == payload_digest(fixture.approval_payload)
    assert facts["subject_digest"] == fixture.approval_payload["subject_digest"]
    assert facts["journal"] == json.loads(fixture.artifact_path.read_bytes())["payload"]["qualification_journal"]
    assert facts["child_results_digest"].startswith("sha256:")

    assert main(_verify_arguments(fixture)) == 0
    output = capsys.readouterr().out.splitlines()
    assert json.loads(output[0]) == facts
    assert output[1] == f"PASS  qualification={fixture.artifact_path}  VERIFIED"

    with pytest.raises(BatchRefusal, match=r"^E-BATCH-PUBLICATION-REFUSED:"):
        verify_publication_refusal(
            fixture.artifact_path,
            governed=fixture.target,
            journal_path=fixture.journal,
            candidate_repository=fixture.target,
            candidate=facts["base_commit"],
        )

    tampered_manifest = json.loads(fixture.artifact_manifest.read_bytes())
    tampered_manifest["artifacts"]["protected"][0]["digest"] = "sha256:" + "0" * 64
    tampered_manifest_path = tmp_path / "tampered-manifest.json"
    tampered_manifest_path.write_bytes(canonical_json_bytes(tampered_manifest))
    protected_payload = dict(fixture.approval_payload)
    protected_payload["b_digest"] = payload_digest(tampered_manifest)
    protected_envelope = _approve(tmp_path, capsys, protected_payload, "tampered-manifest")
    _assert_cli_refusal(
        capsys,
        _verify_arguments(fixture, manifest=tampered_manifest_path, envelope=protected_envelope),
        "E-BATCH-PROTECTED-ARTIFACT",
    )

    corrupted = json.loads(fixture.approval_envelope.read_bytes())
    signature = corrupted["signature"]
    offset = len("ed25519:")
    corrupted["signature"] = signature[:offset] + ("A" if signature[offset] != "A" else "B") + signature[offset + 1 :]
    corrupted_envelope = tmp_path / "corrupted-envelope.json"
    corrupted_envelope.write_bytes(canonical_json_bytes(corrupted))
    _assert_cli_refusal(capsys, _verify_arguments(fixture, envelope=corrupted_envelope), "E-BATCH-SCHEMA")

    _, intruder_public_key = _keygen(tmp_path, monkeypatch, capsys, "intruder")
    intruder_payload = dict(fixture.approval_payload)
    intruder_payload["key"] = intruder_public_key
    intruder_envelope = _approve(tmp_path, capsys, intruder_payload, "intruder")
    _assert_cli_refusal(capsys, _verify_arguments(fixture, envelope=intruder_envelope), "E-BATCH-STALE-BASE")

    owner_key = tmp_path / "keys" / "owner.key"
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(owner_key))
    predecessor_payload = dict(fixture.approval_payload)
    predecessor_payload["journal_predecessor"] = "sha256:" + "1" * 64
    predecessor_envelope = _approve(tmp_path, capsys, predecessor_payload, "wrong-predecessor")
    _assert_cli_refusal(capsys, _verify_arguments(fixture, envelope=predecessor_envelope), "E-BATCH-STALE-BASE")

    matching_predecessor_payload = dict(fixture.approval_payload)
    matching_predecessor_payload["journal_predecessor"] = "sha256:" + "0" * 64
    matching_predecessor_envelope = _approve(
        tmp_path, capsys, matching_predecessor_payload, "matching-predecessor"
    )
    _assert_cli_refusal(
        capsys,
        _verify_arguments(fixture, envelope=matching_predecessor_envelope),
        "E-BATCH-PROTECTED-ARTIFACT",
    )

    malformed_artifact = json.loads(fixture.artifact_path.read_bytes())
    malformed_artifact["payload"]["base_commit"] = 1
    malformed_artifact_path = tmp_path / "malformed-artifact.json"
    malformed_artifact_path.write_bytes(canonical_json_bytes(malformed_artifact))
    _assert_cli_refusal(capsys, _verify_arguments(fixture, qualification=malformed_artifact_path), "E-BATCH-SCHEMA")

    missing_payload_artifact = json.loads(fixture.artifact_path.read_bytes())
    del missing_payload_artifact["payload"]
    missing_payload_artifact_path = tmp_path / "missing-payload-artifact.json"
    missing_payload_artifact_path.write_bytes(canonical_json_bytes(missing_payload_artifact))
    _assert_cli_refusal(capsys, _verify_arguments(fixture, qualification=missing_payload_artifact_path), "E-BATCH-SCHEMA")

    unknown_base_artifact = json.loads(fixture.artifact_path.read_bytes())
    unknown_base_artifact["payload"]["base_commit"] = "0" * 40
    unknown_base_artifact_path = tmp_path / "unknown-base-artifact.json"
    unknown_base_artifact_path.write_bytes(canonical_json_bytes(unknown_base_artifact))
    _assert_cli_refusal(capsys, _verify_arguments(fixture, qualification=unknown_base_artifact_path), "E-BATCH-STALE-BASE")

    evidence_path = fixture.artifact_path.parent / "children/SLICE-036-child-A/evidence.json"
    evidence_path.write_bytes(evidence_path.read_bytes() + b" ")
    _assert_cli_refusal(capsys, _verify_arguments(fixture), "E-BATCH-PROTECTED-ARTIFACT")

    _git(fixture.target, "commit", "--allow-empty", "--quiet", "-m", "test: advance target")
    _assert_cli_refusal(capsys, _verify_arguments(fixture), "E-BATCH-STALE-BASE")
