from __future__ import annotations

import json
from pathlib import Path

from ranex.cli.specification import build_parser


def _input() -> dict[str, object]:
    triple = json.loads(
        (Path(__file__).parents[1] / "contract/fixtures/specification/abc-v1-vectors.json").read_text()
    )["triple"]
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


def _invalid_input() -> dict[str, object]:
    value = _input()
    value["spec_packet"] = {"version": "not-a-spec-packet"}
    return value


def test_specification_parser_refusal_is_nonzero_and_stable(tmp_path, capsys) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_invalid_input()))
    parser = build_parser()
    args = parser.parse_args(["specification", "draft", "--input", str(source)])
    assert args.func(args) != 0
    assert "E-SPEC-030-" in capsys.readouterr().err


def test_specification_parser_drafts_a_valid_session(tmp_path, capsys) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_input()))
    parser = build_parser()
    args = parser.parse_args(["specification", "draft", "--input", str(source)])
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
    }
    for command, options in arguments.items():
        args = parser.parse_args(["specification", command, *options])
        assert args is not None
