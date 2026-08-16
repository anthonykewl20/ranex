from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ranex.foundation.specification_abc import (
    canonical_payload_bytes,
    payload_digest,
    sign_approval_payload,
)
from ranex.governed_execution.application.specification_verification import verify_specification
from ranex.governed_execution.domain.specification_trace import TraceVerificationError

_PRIVATE_KEY = "ed25519:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _descriptor(*, path: str = "src/example.py", symbol: str = "value") -> dict[str, object]:
    return {
        "version": "trace-projection-v1",
        "path": path,
        "language": "python",
        "ids": {"rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-1"]},
        "anchor": {"symbol": symbol},
    }


def _resign(envelope: dict[str, object], manifest: dict[str, object]) -> None:
    payload = envelope["payload"]
    assert isinstance(payload, dict)
    payload["b_digest"] = payload_digest(manifest)
    envelope["signature"] = sign_approval_payload(payload, _PRIVATE_KEY)


def _triple(base: Path, candidate: Path) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    for root in (base, candidate):
        (root / "src").mkdir(parents=True)
        (root / "src/example.py").write_text("def value():\n    return 1\n", encoding="utf-8")
        (root / "oracle.json").write_text('{"O-1":"pass"}', encoding="utf-8")
        (root / "expected.json").write_text('{"O-1":"pass"}', encoding="utf-8")
    descriptor_bytes = canonical_payload_bytes(_descriptor())
    (candidate / ".ranex-trace").write_bytes(descriptor_bytes)
    projection = _digest(descriptor_bytes)
    a = {"version": "spec-packet-v1", "domain": "kernel", "task": "task-1", "revision": 1, "semantics": ["value"], "scope": {"include": ["src"], "exclude": []}, "answers": {}, "observable_outcomes": ["pass"], "non_goals": [], "oracle_provenance": {"O-1": "requirement"}, "ids": {"question": [], "rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-1"], "error": [], "test": [], "mapping": []}}
    rows = lambda name: [{"path": name, "digest": _digest((candidate / name).read_bytes())}]
    b = {"version": "generated-artifact-manifest-v1", "domain": "kernel", "a_digest": payload_digest(a), "artifacts": {"pseudocode_flow": [], "protected": rows("oracle.json"), "invocation": {"argv": ["pytest", "-q"]}, "expected_values": rows("expected.json"), "baselines": [], "negative_controls": [], "trace_projections": rows(".ranex-trace"), "sidecars": []}, "exemptions": []}
    payload = {"version": "approval-payload-v1", "domain": "kernel", "task": "task-1", "revision": 1, "subject_digest": "sha256:" + "2" * 64, "base_digest": "sha256:" + "3" * 64, "a_digest": payload_digest(a), "b_digest": payload_digest(b), "principal": "owner", "key": "ed25519:A6EHv/POEL4dcN0Y50vAmWfk1jCbpQ1fHdyGZBJVMbg=", "role": "approver", "nonce": "trace-1", "journal_predecessor": None, "time_window": {"not_before": 1, "not_after": 2}, "capability_request": {"executable": "python", "argv": ["-m", "pytest"], "cwd": ".", "roots": ["src"], "actions": ["read"], "environment": {"allow": []}, "network": {"allow": False, "hosts": []}, "secret": {"allow": False, "names": []}, "commit": {"allow": False}, "subagent": {"allow": False, "max_children": 0}}, "profile_digests": {"base": "sha256:" + "a" * 64, "policy": "sha256:" + "b" * 64, "generator": "sha256:" + "c" * 64, "harness": "sha256:" + "d" * 64}}
    envelope = {"version": "approval-envelope-v1", "payload_type": "application/vnd.ranex.approval-envelope.v1+json", "payload": payload, "key_id": payload["key"], "signature": sign_approval_payload(payload, _PRIVATE_KEY)}
    assert projection == b["artifacts"]["trace_projections"][0]["digest"]  # type: ignore[index]
    return a, b, envelope


def _projection(candidate: Path) -> str:
    return _digest((candidate / ".ranex-trace").read_bytes())


def _marker(projection: str, symbol: str = "value", result: int = 2) -> str:
    return f"# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection={projection}\ndef {symbol}():\n    return {result}\n"


def _anchor(candidate: Path, *, symbol: str = "value", result: int = 2) -> None:
    (candidate / "src/example.py").write_text(_marker(_projection(candidate), symbol, result), encoding="utf-8")


def _add_sidecar(candidate: Path, b: dict[str, object], c: dict[str, object], *, symbol: str = "value", projection: str | None = None, raw: bytes | None = None, path: str = "trace.json") -> None:
    sidecar = {"version": "trace-sidecar-v1", "projection": projection or _projection(candidate), "path": "src/example.py", "symbol": symbol, "ids": {"rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-1"]}}
    contents = json.dumps(sidecar, separators=(",", ":")).encode() if raw is None else raw
    (candidate / path).write_bytes(contents)
    artifacts = b["artifacts"]
    assert isinstance(artifacts, dict)
    artifacts["sidecars"] = [{"path": path, "digest": _digest(contents)}]
    _resign(c, b)


def test_descriptor_bytes_projection_row_interoperate_with_comment(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    descriptor = _descriptor()
    assert _projection(candidate) == _digest(canonical_payload_bytes(descriptor))
    _anchor(candidate)
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q")).outcomes[0].passed


def test_javascript_trace_comment_is_discovered_and_covers_its_target(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    descriptor = _descriptor(path="src/example.js")
    descriptor["language"] = "javascript"
    raw = canonical_payload_bytes(descriptor)
    (candidate / ".ranex-trace-js").write_bytes(raw)
    artifacts = b["artifacts"]; assert isinstance(artifacts, dict)
    artifacts["trace_projections"].append({"path": ".ranex-trace-js", "digest": _digest(raw)})  # type: ignore[index]
    _resign(c, b)
    (base / "src/example.js").write_text("function value() { return 1; }\n", encoding="utf-8")
    (candidate / "src/example.js").write_text(
        "// ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection="
        f"{_digest(raw)}\nfunction value() {{ return 2; }}\n",
        encoding="utf-8",
    )
    facts = verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert facts.trace.covered == 1
    assert facts.trace.anchors[0].path == "src/example.js"


@pytest.mark.parametrize("field", ("domain", "revision"))
def test_canonical_abc_chain_refuses_context_drift(tmp_path: Path, field: str) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    if field == "domain":
        b["domain"] = "other"
        _resign(c, b)
    else:
        payload = c["payload"]; assert isinstance(payload, dict)
        payload["revision"] = 2; c["signature"] = sign_approval_payload(payload, _PRIVATE_KEY)
    with pytest.raises(TraceVerificationError, match="E-TRACE-007"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


@pytest.mark.parametrize(("setup", "code"), [("missing", "E-TRACE-017"), ("uncovered", "E-TRACE-006"), ("duplicate", "E-TRACE-005"), ("cross-task", "E-TRACE-007"), ("invented", "E-TRACE-010"), ("reasonless", "E-TRACE-012")])
def test_trace_and_exemption_refusal_partitions_are_distinct(tmp_path: Path, setup: str, code: str) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    if setup not in {"missing", "invented"}:
        _anchor(candidate)
    if setup == "missing":
        (candidate / "src/example.py").write_text("def value():\n    return 2\n", encoding="utf-8")
    if setup == "uncovered":
        (candidate / "src/example.py").write_text((candidate / "src/example.py").read_text("utf-8") + "\ndef other():\n    return 3\n", encoding="utf-8")
    elif setup == "duplicate":
        _add_sidecar(candidate, b, c)
    elif setup == "cross-task":
        payload = c["payload"]; assert isinstance(payload, dict)
        payload["task"] = "other"; c["signature"] = sign_approval_payload(payload, _PRIVATE_KEY)
    elif setup == "invented":
        with pytest.raises(TraceVerificationError) as refused:
            verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"), exemptions=(("src/example.py", "nonbehavioral", "invented"),))
        assert refused.value.code == code
        return
    elif setup == "reasonless":
        b["exemptions"] = [{"path": "src/example.py", "class": "nonbehavioral", "reason": "", "why_no_discriminating_red": "no semantic change"}]
        _resign(c, b)
    with pytest.raises(TraceVerificationError) as refused:
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert refused.value.code == code


@pytest.mark.parametrize("case", ("malformed", "absent", "unapproved"))
def test_malformed_absent_or_unapproved_sidecar_refuses(tmp_path: Path, case: str) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    _anchor(candidate)
    if case == "malformed":
        _add_sidecar(candidate, b, c, raw=b'{"version":"trace-sidecar-v1"}')
    elif case == "absent":
        artifacts = b["artifacts"]; assert isinstance(artifacts, dict)
        artifacts["sidecars"] = [{"path": "missing.json", "digest": "sha256:" + "a" * 64}]
        _resign(c, b)
    else:
        sidecar = {"version": "trace-sidecar-v1", "projection": _projection(candidate), "path": "src/example.py", "symbol": "value", "ids": {"rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-1"]}}
        (candidate / "unapproved.json").write_text(json.dumps(sidecar), encoding="utf-8")
    with pytest.raises(TraceVerificationError, match="E-TRACE-013"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


def test_sidecar_descriptor_language_must_match_the_anchored_source_path(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    descriptor = _descriptor()
    descriptor["language"] = "javascript"
    raw = canonical_payload_bytes(descriptor)
    (candidate / ".ranex-trace").write_bytes(raw)
    artifacts = b["artifacts"]
    assert isinstance(artifacts, dict)
    artifacts["trace_projections"] = [{"path": ".ranex-trace", "digest": _digest(raw)}]
    _resign(c, b)
    _add_sidecar(candidate, b, c, projection=_digest(raw))
    (candidate / "src/example.py").write_text("def value():\n    return 2\n", encoding="utf-8")
    with pytest.raises(TraceVerificationError) as refused:
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert refused.value.code == "E-TRACE-002"


def test_two_nonidentical_anchors_for_one_symbol_refuse(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    second = canonical_payload_bytes(_descriptor(symbol="alternate"))
    (candidate / ".ranex-trace-2").write_bytes(second)
    artifacts = b["artifacts"]; assert isinstance(artifacts, dict)
    artifacts["trace_projections"].append({"path": ".ranex-trace-2", "digest": _digest(second)})  # type: ignore[index]
    _add_sidecar(candidate, b, c, projection=_digest(second))
    with pytest.raises(TraceVerificationError, match="E-TRACE-002"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


def test_wildcard_manifest_exemption_refuses(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    b["exemptions"] = [{"path": "src/*.py", "class": "nonbehavioral", "reason": "approved", "why_no_discriminating_red": "no semantic change"}]
    _resign(c, b)
    with pytest.raises(TraceVerificationError, match="E-TRACE-011"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


def test_exact_exemption_covers_change_and_moved_change_refuses(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    b["exemptions"] = [{"path": "src/example.py", "class": "nonbehavioral", "reason": "approved", "why_no_discriminating_red": "no semantic change"}]
    _resign(c, b)
    (candidate / "src/example.py").write_text("def value():\n    return 2\n", encoding="utf-8")
    with pytest.raises(TraceVerificationError, match="E-TRACE-014"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"), exemptions=(("src/example.py", "nonbehavioral", ""),))
    facts = verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert facts.trace.covered == 0 and facts.trace.exempted >= 1
    (candidate / "src/moved.py").write_text("def moved():\n    return 2\n", encoding="utf-8")
    with pytest.raises(TraceVerificationError, match="E-TRACE-006"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


def test_deletion_and_rename_require_sidecar_but_in_place_marker_covers(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    marked = _marker(_projection(candidate), result=1)
    (base / "src/example.py").write_text(marked, encoding="utf-8")
    (candidate / "src/example.py").write_text("", encoding="utf-8")
    for root in (base, candidate):
        (root / "src/other.py").write_text("def other():\n    return 1\n", encoding="utf-8")
    with pytest.raises(TraceVerificationError) as deleted:
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert deleted.value.code == "E-TRACE-017"
    _add_sidecar(candidate, b, c)
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q")).trace.covered == 1

    base2, candidate2 = tmp_path / "base2", tmp_path / "candidate2"
    a2, b2, c2 = _triple(base2, candidate2)
    marked2 = _marker(_projection(candidate2), result=1)
    (base2 / "src/example.py").write_text(marked2, encoding="utf-8")
    (candidate2 / "src/example.py").write_text(_marker(_projection(candidate2), symbol="renamed", result=2), encoding="utf-8")
    with pytest.raises(TraceVerificationError, match="E-TRACE-002"):
        verify_specification(a2, b2, c2, base2, candidate2, {"O-1": "pass"}, ("pytest", "-q"))

    base3, candidate3 = tmp_path / "base3", tmp_path / "candidate3"
    a3, b3, c3 = _triple(base3, candidate3)
    marked3 = _marker(_projection(candidate3), result=1)
    (base3 / "src/example.py").write_text(marked3, encoding="utf-8")
    (candidate3 / "src/example.py").write_text(_marker(_projection(candidate3), result=2), encoding="utf-8")
    assert verify_specification(a3, b3, c3, base3, candidate3, {"O-1": "pass"}, ("pytest", "-q")).trace.covered == 1


def test_invalid_utf8_source_and_invocation_drift_have_typed_precedence(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    (candidate / "src/example.py").write_bytes(b"\xff\xfe")
    with pytest.raises(TraceVerificationError, match="E-TRACE-015"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))

    base2, candidate2 = tmp_path / "base2", tmp_path / "candidate2"
    a2, b2, c2 = _triple(base2, candidate2); _anchor(candidate2)
    with pytest.raises(TraceVerificationError, match="E-TRACE-015"):
        verify_specification(a2, b2, c2, base2, candidate2, {"O-1": "pass"}, ("wrong",))


def test_wrong_outcome_and_facts_are_deterministic(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate); _anchor(candidate)
    first = verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    second = verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert first.canonical_bytes() == second.canonical_bytes()
    with pytest.raises(TraceVerificationError, match="E-TRACE-016"):
        verify_specification(a, b, c, base, candidate, {"O-1": "wrong"}, ("pytest", "-q"))


@pytest.mark.parametrize("change", ("symbol", "path", "ids", "prefix"))
def test_comment_anchor_must_exactly_match_its_signed_descriptor(tmp_path: Path, change: str) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    projection = _projection(candidate)
    if change == "symbol":
        _anchor(candidate, symbol="other")
    elif change == "path":
        (candidate / "src/example.py").unlink()
        (candidate / "src/other.py").write_text(_marker(projection), encoding="utf-8")
    elif change == "ids":
        (candidate / "src/example.py").write_text(
            f"# ranex-trace: rule=R-1,R-1 transition=T-1 outcome=O-1 projection={projection}\ndef value():\n    return 2\n",
            encoding="utf-8",
        )
    else:
        (candidate / "src/example.py").write_text(
            f"// ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection={projection}\ndef value():\n    return 2\n",
            encoding="utf-8",
        )
    with pytest.raises(TraceVerificationError):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))


def test_new_multi_symbol_file_requires_an_anchor_for_each_symbol(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    descriptor = _descriptor(path="src/two.py", symbol="first")
    raw = canonical_payload_bytes(descriptor)
    (candidate / ".ranex-trace-two").write_bytes(raw)
    artifacts = b["artifacts"]; assert isinstance(artifacts, dict)
    artifacts["trace_projections"] = [{"path": ".ranex-trace-two", "digest": _digest(raw)}]
    _resign(c, b)
    projection = _digest(raw)
    (candidate / "src/two.py").write_text(
        _marker(projection, "first") + "\ndef second():\n    return 2\n", encoding="utf-8"
    )
    with pytest.raises(TraceVerificationError, match="E-TRACE-006"):
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))

    descriptor = _descriptor(path="src/two.py", symbol="second")
    raw = canonical_payload_bytes(descriptor)
    (candidate / ".ranex-trace-second").write_bytes(raw)
    artifacts["trace_projections"].append({"path": ".ranex-trace-second", "digest": _digest(raw)})  # type: ignore[index]
    _resign(c, b)
    (candidate / "src/two.py").write_text(
        _marker(projection, "first") + f"\n# ranex-trace: rule=R-1 transition=T-1 outcome=O-1 projection={_digest(raw)}\ndef second():\n    return 2\n",
        encoding="utf-8",
    )
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q")).trace.covered == 2


def test_renamed_first_symbol_and_modified_second_symbol_need_all_anchors(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    (base / "src/example.py").write_text(
        "def old():\n    return 1\n\ndef second():\n    return 1\n", encoding="utf-8"
    )
    artifacts = b["artifacts"]
    assert isinstance(artifacts, dict)
    projections: list[dict[str, str]] = []
    digests: dict[str, str] = {}
    for symbol in ("old", "renamed", "second"):
        raw = canonical_payload_bytes(_descriptor(symbol=symbol))
        path = f".{symbol}.ranex-trace"
        (candidate / path).write_bytes(raw)
        digests[symbol] = _digest(raw)
        projections.append({"path": path, "digest": digests[symbol]})
    artifacts["trace_projections"] = projections
    _resign(c, b)
    _add_sidecar(candidate, b, c, symbol="old", projection=digests["old"])
    (candidate / "src/example.py").write_text(
        "def renamed():\n    return 2\n\ndef second():\n    return 2\n", encoding="utf-8"
    )
    with pytest.raises(TraceVerificationError) as refused:
        verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q"))
    assert refused.value.code == "E-TRACE-006"

    (candidate / "src/example.py").write_text(
        _marker(digests["renamed"], "renamed")
        + "\n"
        + _marker(digests["second"], "second"),
        encoding="utf-8",
    )
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass"}, ("pytest", "-q")).trace.covered == 3


def test_every_observed_outcome_needs_a_distinct_approved_gauge_descriptor(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    a, b, c = _triple(base, candidate)
    ids = a["ids"]
    provenance = a["oracle_provenance"]
    assert isinstance(ids, dict) and isinstance(provenance, dict)
    ids["outcome"] = ["O-1", "O-2"]
    provenance["O-2"] = "requirement"
    a["observable_outcomes"] = ["pass", "pass-2"]
    (candidate / "expected.json").write_text('{"O-1":"pass","O-2":"pass-2"}', encoding="utf-8")
    artifacts = b["artifacts"]
    assert isinstance(artifacts, dict)
    artifacts["expected_values"] = [{"path": "expected.json", "digest": _digest((candidate / "expected.json").read_bytes())}]
    b["a_digest"] = payload_digest(a)
    payload = c["payload"]
    assert isinstance(payload, dict)
    payload["a_digest"] = payload_digest(a)
    _resign(c, b)
    _anchor(candidate)
    with pytest.raises(TraceVerificationError) as refused:
        verify_specification(a, b, c, base, candidate, {"O-1": "pass", "O-2": "pass-2"}, ("pytest", "-q"))
    assert refused.value.code == "E-TRACE-016"

    raw = canonical_payload_bytes({
        **_descriptor(path="src/o2.py"),
        "ids": {"rule": ["R-1"], "transition": ["T-1"], "outcome": ["O-2"]},
    })
    (candidate / ".o2.ranex-trace").write_bytes(raw)
    artifacts["trace_projections"].append({"path": ".o2.ranex-trace", "digest": _digest(raw)})  # type: ignore[index]
    _resign(c, b)
    assert verify_specification(a, b, c, base, candidate, {"O-1": "pass", "O-2": "pass-2"}, ("pytest", "-q")).outcomes[1].passed
