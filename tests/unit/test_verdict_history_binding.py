
import pytest

from ranex.foundation.signing import generate_keypair
from ranex.governed_execution.domain.admission import Admission
from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate
from ranex.governed_execution.verdict_projection import project_verdict
from ranex.governed_execution.verdict_publication import publish_verdict
from ranex.governed_execution.verdict_reader import read_verdict, read_verdict_unbound

SUBJECT = "sha256:" + "a" * 64


def projected(admission):
    result = evaluate(Gate("landing", "RULE", (Claim("tests", "sha256:" + "d" * 64),), True), (), subject_digest=SUBJECT,
                      approver_id="owner")
    return project_verdict(result, admission, required_claims=("tests",), journal_head="sha256:" + "b" * 64)


def test_signed_v3_verdict_binds_exact_reconciled_history_head(tmp_path):
    private, public = generate_keypair()
    head = "sha256:" + "c" * 64
    anchor = (str(tmp_path / "observations.sqlite3"), head, 7)
    record = projected(Admission((), (), observation_checkpoint=anchor, history_verified=True))
    assert record["observation_checkpoint"] == {"log_id": anchor[0], "head": head, "position": 7}
    assert record["history_verified"] is True
    path = tmp_path / "verdict.json"
    publish_verdict(path, record, root=tmp_path, signer_id="service", private_key=private)
    read = read_verdict_unbound(path, {"service": public})
    assert str(read.state) == "verified"
    assert read.observation_checkpoint == record["observation_checkpoint"]


def test_signature_only_compatibility_cannot_certify_history_acceptance(tmp_path):
    private, public = generate_keypair()
    record = projected(Admission((), ()))
    assert record["history_verified"] is False
    assert record["observation_checkpoint"] is None
    path = tmp_path / "unanchored.json"
    publish_verdict(path, record, root=tmp_path, signer_id="service", private_key=private)
    assert str(read_verdict_unbound(path, {"service": public}).state) == "verified"
    bound = read_verdict(path, {"service": public}, subject_digest=SUBJECT, gate_id="landing",
                         catalog_digest=record["catalog_digest"], approver_id="owner")
    assert str(bound.state) == "unanchored"


@pytest.mark.parametrize("payload_type", ["application/vnd.ranex.verdict.v1+json",
                                         "application/vnd.ranex.verdict.v2+json"])
def test_archived_versions_remain_verifiable_but_cannot_certify_history(tmp_path, payload_type):
    import json

    from ranex.foundation.canonical import canonical_sha256
    from ranex.foundation.verdict_signing import sign_verdict, signed_fields_for
    private, public = generate_keypair()
    current = projected(Admission((), ()))
    fields = signed_fields_for(payload_type)
    content = {field: current[field] for field in fields}
    record = {**content, "record_digest": "sha256:" + canonical_sha256(content)}
    path = tmp_path / "legacy.json"
    path.write_text(json.dumps({"payload_type": payload_type, "record": record,
        "signatures": [{"signer_id": "service", "signature": sign_verdict(
            content, private, payload_type=payload_type)}]}))
    assert str(read_verdict_unbound(path, {"service": public}).state) == "verified"
    bound = read_verdict(path, {"service": public}, subject_digest=SUBJECT, gate_id="landing",
                         catalog_digest=record["catalog_digest"], approver_id="owner")
    assert str(bound.state) == "unanchored"


def test_bound_reader_checks_checkpoint_with_the_actual_verified_signer(tmp_path):
    from ranex.governed_execution.adapters.persistence.history import bootstrap_history, log_id
    from ranex.governed_execution.adapters.persistence.sqlite.observations import GENESIS
    private, public = generate_keypair()
    _, unrelated_public = generate_keypair()
    repository = tmp_path / "subject"
    repository.mkdir()
    evidence = repository / "evidence.json"
    checkpoint = tmp_path / "retained.json"
    bootstrap_history(evidence, checkpoint, private, public, repository)
    admission = Admission((), (), observation_checkpoint=(log_id(evidence), GENESIS, 0), history_verified=True)
    record = projected(admission)
    path = tmp_path / "verdict.json"
    publish_verdict(path, record, root=tmp_path, signer_id="service", private_key=private)
    # A retired/unrelated key listed first must not choose checkpoint authority.
    verified = read_verdict(path, {"unrelated-first": unrelated_public, "service": public},
                            subject_digest=SUBJECT, gate_id="landing",
                            catalog_digest=record["catalog_digest"], approver_id="owner",
                            repository_root=repository, history_checkpoint_path=checkpoint)
    assert str(verified.state) == "verified"
