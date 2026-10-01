"""C1: real signed qualification admission must not shift policy bindings."""
from __future__ import annotations

import runpy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from ranex.cli.main import (
    admit_records,
    refuse_executables_inside,
    refuse_foreign_policy_context,
)
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.domain import admission
from ranex.governed_execution.domain.verdict import Claim, Gate, evaluate

# Reuse the frozen, closed-schema qualification contract rather than invent a
# smaller report that production admission would never accept.
QUALIFICATION = runpy.run_path(
    str(Path(__file__).parents[1] / "contract/test_qualification_admission.py")
)
HISTORY = runpy.run_path(str(Path(__file__).parents[1] / "_history.py"))
CATALOG = "sha256:" + "e" * 64


def anchored_admission(tmp_path, records, public):
    private, history_public, _ = HISTORY["mint_service"](tmp_path)
    checkpoint = tmp_path / "checkpoint.json"
    repository = tmp_path / "candidate"
    repository.mkdir()
    HISTORY["establish"](repository, "evidence.json", checkpoint, private, history_public)
    HISTORY["write_records"](repository, "evidence.json", records, checkpoint, private, history_public)
    return admit_records(
        repository / "evidence.json", {"qualifier": public}, repository,
        gate_id="landing", catalog_digest=CATALOG,
        history_checkpoint_path=checkpoint, history_public_key=history_public,
    )


def records_and_key(monkeypatch):
    private, public = generate_keypair()
    monkeypatch.setattr(
        admission, "_read_live_durable_host_state",
        lambda: QUALIFICATION["HOST_STATE"],
    )
    honest = QUALIFICATION["raw_record"](private)
    foreign = {**honest, "claim_id": "tests-executed", "suite_results": None,
               "gate_id": "foreign"}
    body = {k: v for k, v in foreign.items() if k != "signature"}
    foreign["signature"] = sign_evidence(body, private)
    return honest, foreign, public


@pytest.mark.parametrize("qualification_first", [True, False], ids=["qualification-first", "foreign-first"])
def test_mixed_records_bind_their_own_policy(tmp_path, monkeypatch, qualification_first):
    honest, foreign, public = records_and_key(monkeypatch)
    records = [honest, foreign] if qualification_first else [foreign, honest]
    # Includes anchored history and the production admission/filter chain.
    result = anchored_admission(tmp_path, records, public)
    assert [item.claim_id for item in result.evidence] == ["host-qualification"]
    assert [(r.index, r.claim_id, r.reason) for r in result.rejections] == [
        (records.index(foreign), "tests-executed", admission.RejectionReason.POLICY_CONTEXT_MISMATCH)
    ]


@pytest.mark.parametrize("filter_name", ["policy", "containment"])
@pytest.mark.parametrize("damage", ["short", "long", "duplicate", "unmatched", "missing", "malformed", "swapped"])
def test_invalid_pairing_refuses_without_admission(tmp_path, monkeypatch, damage, filter_name):
    honest, _, public = records_and_key(monkeypatch)
    records = [honest]
    admitted = admission.admit(records, {"qualifier": public})
    assert len(admitted.evidence) == 1
    if damage in {"short", "long"}:
        evidence = () if damage == "short" else admitted.evidence * 2
        with pytest.raises(ValueError):
            replace(admitted, evidence=evidence)
        admitted = SimpleNamespace(evidence=evidence, rejections=(),
                                   evidence_indices=admitted.evidence_indices)
    elif damage == "duplicate":
        records *= 2
        admitted = admission.admit(records, {"qualifier": public})
    elif damage == "unmatched":
        admitted = replace(admitted, evidence=(replace(admitted.evidence[0], claim_id="other"),))
    elif damage == "missing":
        records = [{k: v for k, v in honest.items() if k != "claim_id"}]
    elif damage == "malformed":
        records = [{**honest, "claim_id": []}]
    else:
        # Inject a broken adapter's output: reverse only its evidence, not
        # the source records. Neither filter may trust that positional claim.
        second = {**honest, "claim_id": "other"}
        records = [honest, second]
        evidence = (replace(admitted.evidence[0], claim_id="other"), admitted.evidence[0])
        with pytest.raises(ValueError):
            replace(admitted, evidence=evidence)
        admitted = SimpleNamespace(evidence=evidence, rejections=(), evidence_indices=(0, 1))
    if filter_name == "policy":
        result = refuse_foreign_policy_context(admitted, records, "landing", CATALOG)
    else:
        result = refuse_executables_inside(admitted, records, tmp_path)
    assert result.evidence == ()
    assert result.rejections
    assert all(r.reason is admission.RejectionReason.MALFORMED_RECORD for r in result.rejections)


@pytest.mark.parametrize("damage", ["duplicate", "missing", "malformed"])
def test_bad_identity_in_production_chain_is_fail_closed(tmp_path, monkeypatch, damage):
    honest, _, public = records_and_key(monkeypatch)
    records = [honest, honest] if damage == "duplicate" else [
        {k: v for k, v in honest.items() if k != "claim_id"}
        if damage == "missing" else {**honest, "claim_id": []}
    ]
    if damage != "duplicate":
        with pytest.raises(ValueError, match="E-OBSERVATION-CHAIN"):
            anchored_admission(tmp_path, records, public)
        return  # No admission exists from which a PASS verdict could be produced.
    result = anchored_admission(tmp_path, records, public)
    single_path = tmp_path / "single"
    single_path.mkdir()
    single = anchored_admission(single_path, [honest], public)
    assert len(result.evidence) == 1
    assert result.evidence == single.evidence
    assert result.evidence_indices == (0,)
    assert result.evidence[0].claim_id == honest["claim_id"]
    gate = Gate("landing", "RULE", (Claim(honest["claim_id"], honest["command_digest"]),), True)
    assert evaluate(
        gate, result.evidence, subject_digest=QUALIFICATION["SUBJECT"], approver_id="reviewer"
    ) == evaluate(
        gate, single.evidence, subject_digest=QUALIFICATION["SUBJECT"], approver_id="reviewer"
    )
