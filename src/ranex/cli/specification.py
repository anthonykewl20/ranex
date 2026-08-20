"""Standalone argparse surface for specification lifecycle records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from ranex.foundation.canonical import canonical_json
from ranex.governed_execution.application.specification import advance, draft, render_questions
from ranex.governed_execution.domain.specification import (
    ClarificationAnswer,
    ClarificationInput,
    LifecycleSession,
    LifecycleState,
    Question,
    RefusalCode,
)


def _load_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _input(path: str) -> ClarificationInput:
    value = _load_json(path)
    if not isinstance(value, dict):
        raise ValueError("request must be an object")
    questions = value.get("questions")
    answers = value.get("answers")
    observations = value.get("observations")
    # The casts on actor_id/base_digest satisfy the type-checker only — no
    # runtime validation happens here. The domain owns those refusals:
    # advance() refuses an empty actor as MISSING_ACTOR and a mismatched
    # base_digest as STALE_BASE.
    if not isinstance(questions, list) or not isinstance(answers, list) or not isinstance(observations, list):
        raise ValueError("request has invalid clarification fields")
    return ClarificationInput(
        actor_id=cast(str, value.get("actor_id")),
        target=LifecycleState(value.get("target")),
        base_digest=cast(str, value.get("base_digest")),
        spec_packet=value.get("spec_packet"),
        manifest=value.get("manifest"),
        approval_envelope=value.get("approval_envelope"),
        questions=tuple(
            Question(row["question_id"], row["prompt"], tuple(row["allowed_answers"]))
            for row in questions
        ),
        answers=tuple(ClarificationAnswer(row["question_id"], row["value"]) for row in answers),
        observations=tuple(tuple(row) for row in observations),
    )


def _print_refusal(code: RefusalCode) -> int:
    print(str(code), file=sys.stderr)
    return 2


def cmd_draft(args: argparse.Namespace) -> int:
    try:
        request = _input(args.input)
        session = draft(request)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return _print_refusal(RefusalCode.INVALID_INPUT)
    print(canonical_json(session.as_record()))
    return 0


def cmd_advance(args: argparse.Namespace) -> int:
    try:
        request = _input(args.input)
        session = LifecycleSession.from_record(_load_json(args.session))
        result = advance(session, request)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return _print_refusal(RefusalCode.INVALID_INPUT)
    if not result.accepted:
        return _print_refusal(result.code or RefusalCode.INVALID_INPUT)
    print(canonical_json(result.session.as_record()))
    return 0


def cmd_questions(args: argparse.Namespace) -> int:
    try:
        print(render_questions(_input(args.input)))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return _print_refusal(RefusalCode.INVALID_INPUT)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    try:
        session = LifecycleSession.from_record(_load_json(args.session))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return _print_refusal(RefusalCode.INVALID_INPUT)
    print(canonical_json(session.as_record()))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ranex-specification")
    root = parser.add_subparsers(dest="command", required=True)
    specification = root.add_parser("specification")
    commands = specification.add_subparsers(dest="specification_command", required=True)
    for name, function, options in (
        ("draft", cmd_draft, ("input",)),
        ("advance", cmd_advance, ("input", "session")),
        ("questions", cmd_questions, ("input",)),
        ("status", cmd_status, ("session",)),
    ):
        command = commands.add_parser(name)
        for option in options:
            command.add_argument(f"--{option}", required=True)
        command.set_defaults(func=function)
    return parser


__all__ = ["build_parser", "cmd_advance", "cmd_draft", "cmd_questions", "cmd_status"]
