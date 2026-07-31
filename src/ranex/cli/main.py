"""`ranex` — the operator entry point.

Two subcommands, and together they close the loop:

`run` observes a command and writes down what it saw. `gate evaluate` answers one
question — may this change land? — from those observations, and writes down why.

Neither reaches a model. Removing every credential on the machine changes no
verdict, and changes nothing `run` records.
"""

from __future__ import annotations

import argparse
import json
import shlex
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


def uncommitted_paths(
    repository_root: Path,
    *,
    ignoring: Path | None = None,
) -> tuple[str, ...]:
    """Paths where the working tree differs from HEAD.

    Untracked files count. They are absent from HEAD's tree yet present when a
    command runs, so a digest of HEAD would not describe what was observed.

    `ignoring` exempts Ranex's own evidence file. It is written only after the
    observed command has already exited, so it cannot have influenced the
    outcome — and without the exemption the second `run` in a repository would
    always refuse itself.
    """

    result = subprocess.run(
        ["git", "-C", str(repository_root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot read repository status: {result.stderr.strip()}")

    exempt: str | None = None
    if ignoring is not None:
        try:
            exempt = ignoring.resolve().relative_to(repository_root).as_posix()
        except ValueError:
            exempt = None

    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:  # a rename reports "old -> new"
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if path and path != exempt:
            dirty.append(path)
    return tuple(sorted(dirty))


def record_evidence(path: Path, record: dict[str, object]) -> None:
    """Write one record, replacing any earlier one for the same claim+producer.

    Replacing rather than appending keeps one producer's latest observation of a
    claim authoritative. Records from other claims or other producers are left
    untouched — this file is shared.
    """

    kept: list[dict[str, object]] = []
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            raise ValueError("evidence file must contain a JSON array")
        kept = [
            item
            for item in existing
            if not (
                isinstance(item, dict)
                and item.get("claim_id") == record["claim_id"]
                and item.get("producer_id") == record["producer_id"]
            )
        ]

    kept.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(kept, indent=2) + "\n", encoding="utf-8")


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


def cmd_run(args: argparse.Namespace) -> int:
    """Run a command and record what was observed. Never judge it.

    Exits with the wrapped command's own exit code so `run && gate evaluate`
    composes. A failing command is honest evidence of failure, not a usage
    error — only refusals to record are, and those exit 2 having written
    nothing.
    """

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]

    try:
        governed_root = governed_repository_root()
        root = resolve_within_repository(governed_root, args.repository)
        if root != governed_root:
            raise ValueError(
                f"second-repository targets are refused: {args.repository!r}"
            )
        evidence_path = resolve_within_repository(root, args.evidence)
        if not command:
            raise ValueError("a command is required after --")

        # Refuse before running, not after: a claim we cannot honestly bind to a
        # subject should cost nothing to discover.
        dirty = uncommitted_paths(root, ignoring=evidence_path)
        if dirty:
            raise ValueError(
                "refusing to record evidence against a dirty working tree; "
                f"{args.ref} does not describe: {', '.join(dirty)}"
            )
        subject = subject_digest_for(root, args.ref)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    completed = subprocess.run(command, cwd=root, check=False)

    try:
        record_evidence(
            evidence_path,
            {
                "claim_id": args.claim,
                "subject_digest": subject,
                "producer_id": args.producer,
                "command": shlex.join(command),
                "exit_code": int(completed.returncode),
            },
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(
        f"RECORDED  claim={args.claim}  producer={args.producer}  "
        f"exit={completed.returncode}"
    )
    print(f"          subject={subject}")
    return int(completed.returncode)


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

    rn = sub.add_parser("run", help="run a command and record evidence of it")
    rn.add_argument("--claim", required=True, help="claim this evidences")
    rn.add_argument("--producer", required=True, help="identity running the command")
    rn.add_argument("--repository", default=".", help="repository root")
    rn.add_argument("--ref", default="HEAD", help="git ref the evidence binds to")
    rn.add_argument(
        "--evidence",
        default="governance/evidence.json",
        help="evidence records path",
    )
    rn.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to run, after --",
    )
    rn.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
