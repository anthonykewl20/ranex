from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import payload_digest, sign_approval_envelope
from ranex.governed_execution.application.specification_verification import verify_specification
from ranex.governed_execution.domain.specification_trace import TraceVerificationError


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _triple(base: Path, candidate: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    for root in (base, candidate):
        (root / "src").mkdir(parents=True)
        (root / "src/example.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        (root / "oracle.json").write_text('{"O-1":"pass"}', encoding="utf-8")
        (root / "expected.json").write_text('{"O-1":"pass"}', encoding="utf-8")
        (root / "projection.json").write_text("projection", encoding="utf-8")
    a = {"version": "spec-packet-v1", "domain": "kernel", "task": "task-1", "revision": 1, "semantics": ["value"], "scope": {"include": ["src"], "exclude": []}, "answers": {}, "observable_outcomes": ["pass"], "non_goals": [], "oracle_provenance": {"O-1": "requirement"}, "ids": {"question": [], "rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-1"], "error": [], "test": [], "mapping": []}}
    rows = lambda name: [{"path": name, "digest": _digest((candidate / name).read_bytes())}]
    b = {"version": "generated-artifact-manifest-v1", "domain": "kernel", "a_digest": payload_digest(a), "artifacts": {"pseudocode_flow": [], "protected": rows("oracle.json"), "invocation": {"argv": ["pytest", "-q"]}, "expected_values": rows("expected.json"), "baselines": [], "negative_controls": [], "trace_projections": rows("projection.json"), "sidecars": []}, "exemptions": []}
    payload = {"version": "approval-payload-v1", "domain": "kernel", "task": "task-1", "revision": 1, "subject_digest": "sha256:" + "2" * 64, "base_digest": "sha256:" + "3" * 64, "a_digest": payload_digest(a), "b_digest": payload_digest(b), "principal": "owner", "key": "ed25519:A6EHv/POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg=", "role": "approver", "nonce": "trace-1", "journal_predecessor": None, "time_window": {"not_before": 1, "not_after": 2}, "capability_request": {"executable": "python", "argv": ["-m", "pytest"], "cwd": ".", "roots": ["src"], "actions": ["read"], "environment": {"allow": []}, "network": {"allow": False, "hosts": []}, "secret": {"allow": False, "names": []}, "commit": {"allow": False}, "subagent": {"allow": False, "max_children": 0}}, "profile_digests": {"base": "sha256:" + "a" * 64, "policy": "sha256:" + "b" * 64, "generator": "sha256:" + "c" * 64, "harness": "sha256:" + "d" * 64}}
    envelope = {"version": "approval-envelope-v1", "payload_type": "application/vnd.ranex.approval-envelope.v1+json", "payload": payload, "key_id": payload["key"], "signature": sign_approval_envelope(payload, "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=")}
    return a, b, envelope


def _anchor(candidate: Path) -> None:
    projection = _digest((candidate / "projection.json").read_bytes())
    (candidate / "src/example.py").write_text("# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection=" + projection + "\ndef value():\n    return 2\n", encoding="utf-8")


def test_comment_and_exact_exemption_cover_changed_hunks(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q")).outcomes[0].passed


@pytest.mark.parametrize(
    ("setup", "code"),
    [
        ("missing", "E-TRACE-017"),
        ("uncovered", "E-TRACE-006"),
        ("duplicate", "E-TRACE-005"),
        ("cross-task", "E-TRACE-007"),
        ("invented", "E-TRACE-010"),
        ("reasonless", "E-TRACE-012"),
    ],
)
def test_trace_and_exemption_refusal_partitions_are_distinct(tmp_path: Path, setup: str, code: str) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    if setup != "missing":
        _anchor(candidate)
    else:
        (candidate / "src/example.py").write_text("def value():\n    return 2\n", encoding="utf-8")
    if setup == "uncovered":
        (candidate / "src/example.py").write_text((candidate / "src/example.py").read_text("utf-8") + "\ndef other():\n    return 3\n", encoding="utf-8")
    elif setup == "duplicate":
        (candidate / "src/example.py").write_text((candidate / "src/example.py").read_text("utf-8").replace("\ndef value", "\n# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection=" + _digest((candidate / "projection.json").read_bytes()) + "\ndef value"), encoding="utf-8")
    elif setup == "cross-task":
        c["payload"]["task"] = "other"; c["signature"] = sign_approval_envelope(c["payload"], "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=")  # type: ignore[arg-type,index]
    elif setup == "invented":
        with pytest.raises(TraceVerificationError) as refused:
            verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"), exemptions=(("src/example.py", "nonbehavioral", "invented"),))
        assert refused.value.code == code
        return
    elif setup == "reasonless":
        b["exemptions"] = [{"path": "src/example.py", "class": "nonbehavioral", "reason": "", "why_no_discriminating_red": "no semantic change"}]
        c["payload"]["b_digest"] = payload_digest(b); c["signature"] = sign_approval_envelope(c["payload"], "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=")  # type: ignore[arg-type,index]
    with pytest.raises(TraceVerificationError) as refused:
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert refused.value.code == code


def test_sidecar_approval_and_mismatch_refusals(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    projection = _digest((candidate / "projection.json").read_bytes())
    sidecar = {"version": "trace-sidecar-v1", "projection": projection, "path": "src/example.py", "symbol": "value", "ids": {"rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-1"]}}
    (candidate / "trace.json").write_text(json.dumps(sidecar, separators=(",", ":")), encoding="utf-8")
    b["artifacts"]["sidecars"] = [{"path": "trace.json", "digest": _digest((candidate / "trace.json").read_bytes())}]  # type: ignore[index]
    c["payload"]["b_digest"] = payload_digest(b); c["signature"] = sign_approval_envelope(c["payload"], "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=")  # type: ignore[arg-type,index]
    (candidate / "src/example.py").write_text("def value():\n    return 2\n", encoding="utf-8")
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q")).trace.covered == 1
    bad = copy.deepcopy(c); bad["payload"]["b_digest"] = "sha256:" + "f" * 64
    with pytest.raises(TraceVerificationError, match="E-TRACE-003"):
        verify_specification(a, b, bad, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


def test_exemption_drift_and_moved_change_refuse(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    b["exemptions"] = [{"path": "src/example.py", "class": "nonbehavioral", "reason": "rename", "why_no_discriminating_red": "no semantic change"}]
    c["payload"]["b_digest"] = payload_digest(b); c["signature"] = sign_approval_envelope(c["payload"], "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=")  # type: ignore[arg-type,index]
    with pytest.raises(TraceVerificationError, match="E-TRACE-014"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"), exemptions=(("src/example.py", "nonbehavioral", ""),))


def test_protected_artifact_and_invocation_precede_outcome_evaluation(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    (candidate / "oracle.json").write_text("tampered", encoding="utf-8")
    with pytest.raises(TraceVerificationError, match="E-TRACE-015"):
        verify_specification(a, b, c, base, candidate, {"O-1": "wrong"}, ("wrong",))


def test_wrong_outcome_refuses_despite_current_trace_or_exemption(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    with pytest.raises(TraceVerificationError, match="E-TRACE-016"):
        verify_specification(a, b, c, base, candidate, {"O-1": "wrong"}, ("pytest", "-q"))


def test_verification_facts_are_byte_identical_for_identical_inputs(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    first = verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    second = verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert first.canonical_bytes() == second.canonical_bytes()
