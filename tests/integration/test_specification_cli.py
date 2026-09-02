from __future__ import annotations

import json
from pathlib import Path

from ranex.cli.main import main
from ranex.cli.specification import build_parser
from ranex.foundation.canonical import canonical_json_bytes
from ranex.foundation.specification_abc import (
    assert_abc_chain,
    validate_approval_envelope_bytes,
)


def _input() -> dict[str, object]:
    triple = _triple()
    return {
        "actor_id": "owner",
        "target": "SPEC_VALIDATED",
        "base_digest": triple["c_payload"]["base_digest"],
        "spec_packet": triple["a"],
        "manifest": triple["b"],
        "approval_envelope": {
            "version": "approval-envelope-v1",
            "payload_type": "application/vnd.ranex.approval-envelope.v1+json",
            "payload": triple["c_payload"],
            "key_id": triple["key_id"],
            "signature": triple["signature"],
        },
        "questions": [{"question_id": "Q-1", "prompt": "Confirm scope", "allowed_answers": ["owner approved"]}],
        "answers": [{"question_id": "Q-1", "value": "owner approved"}],
        "observations": [],
    }


def _triple() -> dict[str, object]:
    return json.loads(
        (Path(__file__).parents[1] / "contract/fixtures/specification/abc-v1-vectors.json").read_text()
    )["triple"]


def _invalid_input() -> dict[str, object]:
    value = _input()
    value["target"] = "NOT_A_LIFECYCLE_STATE"
    return value


def _keygen(tmp_path: Path, monkeypatch, capsys, producer: str) -> tuple[Path, str]:
    key_path = tmp_path / f"{producer}.key"
    monkeypatch.setenv("RANEX_SIGNING_KEY", str(key_path))
    assert main(["keygen", "--producer", producer]) == 0
    public_key = next(
        line.removeprefix(f"    {producer}: ")
        for line in capsys.readouterr().out.splitlines()
        if line.startswith(f"    {producer}: ")
    )
    assert public_key.startswith("ed25519:")
    return key_path, public_key


def _approval_payload(public_key: str) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    triple = _triple()
    payload = dict(triple["c_payload"])
    payload["key"] = public_key
    return dict(triple["a"]), dict(triple["b"]), payload


def test_approve_signs_payload_from_keygen_key(tmp_path: Path, monkeypatch, capsys) -> None:
    _, public_key = _keygen(tmp_path, monkeypatch, capsys, "owner")
    spec_packet, manifest, payload = _approval_payload(public_key)
    source = tmp_path / "approval-payload.json"
    output = tmp_path / "approval-envelope.json"
    source.write_bytes(canonical_json_bytes(payload))

    assert main(["specification", "approve", "--payload", str(source), "--output", str(output)]) == 0

    assert capsys.readouterr().out == f"APPROVED  {output}  key_id={public_key}\n"
    envelope_bytes = output.read_bytes()
    envelope = validate_approval_envelope_bytes(envelope_bytes)
    assert envelope_bytes == canonical_json_bytes(envelope)
    assert envelope["key_id"] == payload["key"]
    assert_abc_chain(spec_packet, manifest, envelope)


def test_approve_refuses_missing_key_and_malformed_payload(tmp_path: Path, monkeypatch, capsys) -> None:
    _, public_key = _keygen(tmp_path, monkeypatch, capsys, "owner")
    _, _, payload = _approval_payload(public_key)
    source = tmp_path / "approval-payload.json"
    output = tmp_path / "approval-envelope.json"
    source.write_bytes(canonical_json_bytes(payload))
    monkeypatch.delenv("RANEX_SIGNING_KEY")

    assert main(["specification", "approve", "--payload", str(source), "--output", str(output)]) == 2
    assert capsys.readouterr().err.startswith("ERROR  RANEX_SIGNING_KEY is not set")
    assert not output.exists()

    source.write_bytes(b"{not json}")
    assert main(["specification", "approve", "--payload", str(source), "--output", str(output)]) == 2
    assert capsys.readouterr().err.startswith("ERROR  E-ABC-004:")
    assert not output.exists()


def test_approve_refuses_wrong_key_and_existing_output(tmp_path: Path, monkeypatch, capsys) -> None:
    owner_key, owner_public_key = _keygen(tmp_path, monkeypatch, capsys, "owner")
    intruder_key, _ = _keygen(tmp_path, monkeypatch, capsys, "intruder")
    _, _, payload = _approval_payload(owner_public_key)
    source = tmp_path / "approval-payload.json"
    output = tmp_path / "approval-envelope.json"
    source.write_bytes(canonical_json_bytes(payload))

    assert main(["specification", "approve", "--payload", str(source), "--output", str(output)]) == 2
    assert capsys.readouterr().err.startswith("ERROR  E-ABC-014:")
    assert not output.exists()

    monkeypatch.setenv("RANEX_SIGNING_KEY", str(owner_key))
    output.write_bytes(b"preserve-existing-envelope")
    assert main(["specification", "approve", "--payload", str(source), "--output", str(output)]) == 2
    assert capsys.readouterr().err.startswith("ERROR  [Errno 17] File exists")
    assert output.read_bytes() == b"preserve-existing-envelope"


def test_specification_parser_refusal_is_nonzero_and_stable(tmp_path, capsys) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_invalid_input()))
    parser = build_parser()
    args = parser.parse_args(["specification", "draft", "--input", str(source)])
    assert args.func(args) != 0
    assert capsys.readouterr().err == "E-SPEC-030-INVALID-INPUT\n"


def test_specification_parser_drafts_a_valid_session(tmp_path, capsys) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_input()))
    parser = build_parser()
    args = parser.parse_args(["specification", "draft", "--input", str(source)])
    assert args.func(args) == 0
    assert '"state":"DRAFT"' in capsys.readouterr().out


def test_specification_parser_draft_does_not_advance_validation(tmp_path, capsys) -> None:
    source = tmp_path / "request.json"
    request = _input()
    request["spec_packet"] = {"version": "not-a-spec-packet"}
    source.write_text(json.dumps(request))
    args = build_parser().parse_args(["specification", "draft", "--input", str(source)])
    assert args.func(args) == 0
    assert '"state":"DRAFT"' in capsys.readouterr().out


def test_specification_parser_has_isolated_subcommand_surface(tmp_path) -> None:
    parser = build_parser()
    request = tmp_path / "request.json"
    session = tmp_path / "session.json"
    request.write_text(json.dumps(_input()))
    session.write_text("{}")
    arguments = {
        "draft": ["--input", str(request)],
        "advance": ["--input", str(request), "--session", str(session)],
        "questions": ["--input", str(request)],
        "status": ["--session", str(session)],
        "approve": ["--payload", str(request), "--output", str(session)],
    }
    for command, options in arguments.items():
        args = parser.parse_args(["specification", command, *options])
        assert args is not None
