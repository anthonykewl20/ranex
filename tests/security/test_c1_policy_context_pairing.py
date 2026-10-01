"""C1: real signed qualification admission must not shift policy bindings."""
from __future__ import annotations

import json
import runpy
from dataclasses import replace
from pathlib import Path

import pytest

from ranex.cli.main import (
    admit_records, refuse_executables_inside, refuse_foreign_policy_context,
)
from ranex.foundation.signing import generate_keypair, sign_evidence
from ranex.governed_execution.domain import admission

# Reuse the frozen, closed-schema qualification contract rather than invent a
# smaller report that production admission would never accept.
QUALIFICATION = runpy.run_path(
    str(Path(__file__).parents[1] / "contract/test_qualification_admission.py")
)
CATALOG = "sha256:" + "e" * 64


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
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(records))
    # Includes reconciliation, signature/host-state admission, executable
    # containment and policy filtering: the same chain used by gate evaluate.
    result = admit_records(path, {"qualifier": public}, tmp_path,
                           gate_id="landing", catalog_digest=CATALOG)
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
    if damage == "short":
        admitted = replace(admitted, evidence=())
    elif damage == "long":
        admitted = replace(admitted, evidence=admitted.evidence * 2)
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
        admitted = replace(admitted, evidence=(
            replace(admitted.evidence[0], claim_id="other"), admitted.evidence[0],
        ))
    if filter_name == "policy":
        result = refuse_foreign_policy_context(admitted, records, "landing", CATALOG)
    else:
        result = refuse_executables_inside(admitted, records, tmp_path)
    assert result.evidence == ()
    assert result.rejections
    assert all(r.reason is admission.RejectionReason.MALFORMED_RECORD for r in result.rejections)


@pytest.mark.parametrize("damage", ["duplicate", "missing", "malformed"])
def test_bad_identity_in_production_chain_is_refused(tmp_path, monkeypatch, damage):
    honest, _, public = records_and_key(monkeypatch)
    records = [honest, honest] if damage == "duplicate" else [
        {k: v for k, v in honest.items() if k != "claim_id"}
        if damage == "missing" else {**honest, "claim_id": []}
    ]
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(records))
    result = admit_records(path, {"qualifier": public}, tmp_path,
                           gate_id="landing", catalog_digest=CATALOG)
    assert result.evidence == ()
    assert result.rejections
    assert all(r.reason is admission.RejectionReason.MALFORMED_RECORD for r in result.rejections)
