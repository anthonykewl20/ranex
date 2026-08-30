"""ADR-040 — registered specification lifecycle CLI surface."""

from __future__ import annotations

import json
from pathlib import Path

from ranex.cli.main import (
    _dispatch_stage,
    build_parser,
    cmd_specification_draft,
    main,
)


def _input() -> dict[str, object]:
    triple = json.loads(
        (
            Path(__file__).parents[1]
            / "contract/fixtures/specification/abc-v1-vectors.json"
        ).read_text(encoding="utf-8")
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
        "questions": [
            {
                "question_id": "Q-1",
                "prompt": "Confirm scope",
                "allowed_answers": ["owner approved"],
            }
        ],
        "answers": [{"question_id": "Q-1", "value": "owner approved"}],
        "observations": [],
    }


def test_specification_draft_is_bound_to_the_aliased_command(tmp_path: Path) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_input()), encoding="utf-8")

    args = build_parser().parse_args(["specification", "draft", "--input", str(source)])

    assert args.func is cmd_specification_draft


def test_registered_specification_draft_preserves_invalid_input_refusal(
    tmp_path: Path, capsys
) -> None:
    source = tmp_path / "request.json"
    invalid = _input()
    invalid["target"] = "NOT_A_LIFECYCLE_STATE"
    source.write_text(json.dumps(invalid), encoding="utf-8")

    assert main(["specification", "draft", "--input", str(source)]) == 2
    assert capsys.readouterr().err == "E-SPEC-030-INVALID-INPUT\n"


def test_registered_specification_draft_prints_canonical_draft_session(
    tmp_path: Path, capsys
) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_input()), encoding="utf-8")
    args = build_parser().parse_args(["specification", "draft", "--input", str(source)])

    assert args.func(args) == 0
    assert '"state":"DRAFT"' in capsys.readouterr().out


def test_registered_specification_draft_resolves_the_schema_stage_pair(
    tmp_path: Path,
) -> None:
    source = tmp_path / "request.json"
    source.write_text(json.dumps(_input()), encoding="utf-8")
    args = build_parser().parse_args(["specification", "draft", "--input", str(source)])

    assert _dispatch_stage(args) == (
        "cli.specification.draft.start",
        "cli.specification.draft.end",
    )
