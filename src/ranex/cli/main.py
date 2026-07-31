"""`ranex` — the operator entry point.

One subcommand: `gate evaluate`. It answers one question — may this change land?
— from recorded evidence, and writes down why.

No model is reachable from here. Removing every credential on the machine changes
no verdict.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.cli.confinement import resolve_within_repository
from ranex.foundation.canonical import canonical_sha256
from ranex.governed_execution.api import (
    Evidence,
    Verdict,
)

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


def subject_digest_for(repository_root: Path, ref: str) -> str:
    """The exact subject: the git tree of `ref`, not a mutable branch name."""

    result = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", f"{ref}^{{tree}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot resolve ref {ref!r}: {result.stderr.strip()}")
    return "sha256:" + canonical_sha256({"tree": result.stdout.strip()})


def load_evidence(path: Path) -> tuple[Evidence, ...]:
    """Read evidence records. A missing file is no evidence, not an error."""

    if not path.exists():
        return ()
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        Evidence(
            claim_id=item["claim_id"],
            subject_digest=item["subject_digest"],
            producer_id=item["producer_id"],
            command=item["command"],
            exit_code=int(item["exit_code"]),
        )
        for item in raw
    )


def governed_repository_root() -> Path:
    """Return the Git checkout containing this CLI, independent of caller cwd."""

    installation_path = Path(__file__).resolve()
    result = subprocess.run(
        ["git", "-C", str(installation_path.parent), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            "cannot locate the repository containing the Ranex CLI: "
            f"{result.stderr.strip()}"
        )
    return Path(result.stdout.strip()).resolve()


def cmd_gate_evaluate(args: argparse.Namespace) -> int:
    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        gate_catalog = resolve_within_repository(root, args.gate_catalog)
        evidence_path = resolve_within_repository(root, args.evidence)
        journal_path = (
            resolve_within_repository(root, args.journal) if args.journal else None
        )
        subject = subject_digest_for(root, args.ref)
        evidence = load_evidence(evidence_path)
        evaluator = build_gate_evaluator(
            gate_catalog,
            journal_path,
        )
        result = evaluator.evaluate(
            args.gate,
            evidence,
            subject_digest=subject,
            approver_id=args.approver,
        )
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    if result.verdict is Verdict.PASS:
        print(f"PASS  gate={result.gate_id}  subject={result.subject_digest}")
        return EXIT_PASS

    print(f"FAIL  gate={result.gate_id}  rule={result.failing_rule}")
    print(f"      {result.reason}")
    print(f"      subject={result.subject_digest}")
    return EXIT_FAIL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ranex",
        description="Deterministic governance for AI agents that build software",
    )
    sub = parser.add_subparsers(dest="group", required=True)
    gate = sub.add_parser("gate", help="gate operations").add_subparsers(
        dest="action", required=True
    )
    ev = gate.add_parser("evaluate", help="evaluate a change against a gate")
    ev.add_argument("ref", help="git ref to evaluate")
    ev.add_argument("--repository", default=".", help="repository root")
    ev.add_argument("--gate", default="landing", help="gate id")
    ev.add_argument(
        "--gate-catalog",
        default="governance/gates.yaml",
        help="gate catalog path",
    )
    ev.add_argument(
        "--evidence",
        default="governance/evidence.json",
        help="evidence records path",
    )
    ev.add_argument("--approver", required=True, help="identity approving")
    ev.add_argument("--journal", default="governance/journal.sqlite3", help="journal path")
    ev.set_defaults(func=cmd_gate_evaluate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
