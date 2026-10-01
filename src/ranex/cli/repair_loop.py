"""The C6 harness attachment: a Stop/PreToolUse hook that gates the loop.

SLICE-092 ships the oracle-science C6 structure as a harness attachment.
When the delegated agent stops, the kernel — not the agent — runs the
governed cycle observer-side: this command drives the real CLI in-process
(`run`, then `gate evaluate` with verdict publication), reads the
published verdict and repair envelope from the ADR-019 read channel, and
answers the harness in machine-consumable JSON (captain DIRECT 008). The
agent ingests only verdict + envelope; it never runs the suite itself,
never sees suite output, and never holds a credential.

The three structural walls are not re-implemented here, they are the
reason this attachment is safe: `task delegate` refuses to start a
delegated environment holding a signing credential (delegation.py), so a
hook running inside one structurally cannot run the cycle — it degrades
to reading whatever verdict is already published and says so; `ranex run`
refuses to write unsigned evidence; admission verifies signatures against
the committed keyring. Hook stdout has no path into any of the three.

The loop is fully autonomous across a miss budget (default 3, the
oracle-science 3-miss rule): each verified FAIL spends one miss, a
verified PASS resets the count, and reaching the budget stops the loop
deterministically — an approve whose reason says the budget is spent, not
a human decision and not a pane wait. The budget counter is runtime state
in the read-channel directory, keyed by repository, gate and stable harness session; it is never
evidence and never journaled.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import io
import json
import os
import sys
from pathlib import Path
from typing import Any

_STDIN_LIMIT = 1024 * 1024

# Defaults are duplicated as literals so registering the parser needs no
# import from main at module scope (main imports this module's register).
DEFAULT_GATE_CATALOG = "governance/gates.yaml"
DEFAULT_SUITE_MANIFEST = "governance/suite_manifest.json"
DEFAULT_PRODUCERS = "governance/producers.yaml"
DEFAULT_JOURNAL = "governance/journal.sqlite3"
DEFAULT_VERDICT_DIR = "governance/verdicts"


def _read_hook_stdin() -> dict[str, Any]:
    """Read the harness's hook payload, tolerating anything but trusting nothing.

    A harness always pipes the hook's stdin; an unreadable or absent stream
    (pytest's captured stdin raises on read; a closed pipe returns nothing)
    simply means no payload, and the attachment proceeds on its own args.
    Deliberately no TTY probe: printed content never varies with the
    terminal, per the frozen presentation contract.
    """

    if sys.stdin is None or sys.stdin.closed:
        return {}
    try:
        raw = sys.stdin.read(_STDIN_LIMIT)
        value = json.loads(raw) if raw.strip() else {}
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _emit(decision: str, reason: str, *, envelope: dict[str, object] | None,
          read_state: str, misses: int | None, budget: int | None) -> int:
    payload: dict[str, object] = {
        "decision": decision,
        "reason": reason,
        "envelope": envelope,
        "read_state": read_state,
    }
    if misses is not None:
        payload["misses"] = misses
    if budget is not None:
        payload["budget"] = budget
    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_cli(argv: list[str]) -> tuple[int, str]:
    """Drive the real CLI in-process, capturing everything it prints."""

    from ranex.cli.main import main

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    captured = f"{out.getvalue()}{err.getvalue()}".strip()
    return code, captured


def _budget_path(verdicts_dir: Path, loop_digest: str) -> Path:
    return verdicts_dir / f"loop-{loop_digest}.budget.json"


def _read_misses(path: Path) -> int:
    from ranex.foundation.suite_results import read_results_artifact

    try:
        path.lstat()
    except FileNotFoundError:
        return 0
    raw = read_results_artifact(path, maximum_bytes=1024)
    try:
        value = json.loads(raw)
    except ValueError as exc:
        raise ValueError("repair budget state must be valid JSON") from exc
    if (not isinstance(value, dict) or set(value) != {"misses"}
            or type(value["misses"]) is not int or value["misses"] < 0):
        raise ValueError("repair budget state must contain one non-negative integer misses")
    return value["misses"]


def _write_misses(path: Path, misses: int) -> None:
    from ranex.foundation.atomic_writer import write_atomic
    from ranex.foundation.canonical import canonical_json_bytes

    path.parent.mkdir(parents=True, exist_ok=True)
    write_atomic(path, canonical_json_bytes({"misses": misses}) + b"\n", root=path.parent)


def _update_misses(path: Path, *, reset: bool = False) -> int:
    """Serialize the complete budget transition across hook processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        previous = _read_misses(path)
        misses = 0 if reset else previous + 1
        _write_misses(path, misses)
        return misses
    finally:
        os.close(descriptor)


def cmd_task_stop_hook(args: argparse.Namespace) -> int:
    """Answer a harness Stop or PreToolUse event from the governed read channel."""

    # Imported lazily, exactly as `cmd_task_delegate` does: main imports the
    # task parsers at module scope and a top-level import here would cycle.
    from ranex.bootstrap.composition import claim_definition_for
    from ranex.cli.main import (
        EXIT_USAGE,
        SIGNING_KEY_VARIABLE,
        VERDICT_DIR_VARIABLE,
        _command_repository,
        catalog_digest_for,
        committed_trust_root,
        head_commit,
        resolve_within_repository,
        subject_digest_for,
    )
    from ranex.foundation.suite_results import read_results_artifact
    from ranex.governed_execution.repair_envelope import (
        render_packet_text,
        validate_repair_envelope,
    )
    from ranex.governed_execution.verdict_reader import ReadState, read_verdict
    from ranex.policy.adapters.configuration.yaml.producer_keyring import (
        load_trust_keyring_text,
    )

    hook = _read_hook_stdin()
    budget = max(1, int(args.budget))

    try:
        root = _command_repository(args)
        catalog_path = resolve_within_repository(root, args.gate_catalog)
        verdicts_dir = resolve_within_repository(root, args.verdicts_dir)

        if args.mode == "pretooluse":
            return _pretooluse(args, hook, root, catalog_path)

        commit = head_commit(root)
        subject = subject_digest_for(root, commit)
        subject_hex = subject.removeprefix("sha256:")

        cycle_note = ""
        if os.environ.get(SIGNING_KEY_VARIABLE):
            catalog_source = committed_trust_root(
                root, commit, args.gate_catalog, catalog_path, "gate catalog"
            )
            claim = claim_definition_for(catalog_source, args.gate, args.claim)
            if claim is None or not claim.command:
                raise ValueError(
                    f"claim {args.claim!r} in gate {args.gate!r} carries no command "
                    "to run; the hook cannot drive its governed cycle"
                )
            # The kernel runs the governed gate observer-side: the real CLI,
            # in-process, under this process's own environment. Publication
            # targets the channel this hook reads. The repository is named
            # exactly as the hook itself named it — never as an absolute
            # --repository, which the governed path refuses.
            os.environ.setdefault(VERDICT_DIR_VARIABLE, str(verdicts_dir))
            anchored = (
                ["--external-repository", str(root)]
                if getattr(args, "external_repository", None)
                else []
            )
            run_code, run_text = _run_cli(
                [
                    "run",
                    *anchored,
                    "--gate-catalog", str(args.gate_catalog),
                    "--suite-manifest", str(args.suite_manifest),
                    "--evidence", str(args.evidence),
                    "--producers", str(args.producers),
                    "--gate", args.gate,
                    "--claim", args.claim,
                    "--producer", args.producer,
                    "--",
                    *claim.command,
                ]
            )
            if run_code == EXIT_USAGE and "RECORDED" not in run_text:
                # Exit 2 alone is ambiguous — the wrapped command may exit 2
                # after its record was written. The record is the difference:
                # refused runs write nothing, so no RECORDED line exists.
                cycle_note = f"governed run refused: {run_text}"
            else:
                evaluate_code, evaluate_text = _run_cli(
                    [
                        "gate", "evaluate", commit,
                        *anchored,
                        "--gate-catalog", str(args.gate_catalog),
                        "--suite-manifest", str(args.suite_manifest),
                        "--evidence", str(args.evidence),
                        "--producers", str(args.producers),
                        "--gate", args.gate,
                        "--approver", args.approver,
                        "--journal", str(args.journal),
                    ]
                )
                if evaluate_code == EXIT_USAGE:
                    cycle_note = f"gate evaluate refused: {evaluate_text}"
        else:
            # The delegated case, and the wall speaking: no credential here,
            # so no cycle can run and none is fabricated. Whatever verdict
            # the observer already published is all there is to read.
            cycle_note = (
                "no signing credential in this environment; the governed cycle "
                "did not run (delegation.py refuses credentials in delegated "
                "environments by design)"
            )

        keyring_path = resolve_within_repository(root, args.producers)
        trust = load_trust_keyring_text(
            committed_trust_root(
                root, commit, args.producers, keyring_path, "producer keyring"
            ).decode("utf-8"),
            keyring_path,
        )
        catalog_source = committed_trust_root(
            root, commit, args.gate_catalog, catalog_path, "gate catalog"
        )
        verdict = read_verdict(
            verdicts_dir / f"{subject_hex}.json",
            {trust.verdict_signer_id: trust.verdict_signer_public_key},
            subject_digest=subject,
            gate_id=args.gate,
            catalog_digest=catalog_digest_for(catalog_source),
            approver_id=args.approver,
            approvers=trust.approvers,
            repository_root=root,
        )
        envelope: dict[str, object] | None = None
        envelope_path = verdicts_dir / f"{subject_hex}.envelope.json"
        if envelope_path.is_file():
            try:
                envelope = validate_repair_envelope(
                    json.loads(read_results_artifact(envelope_path))
                )
            except (ValueError, OSError):
                envelope = None

        from ranex.foundation.canonical import canonical_sha256

        loop_id = getattr(args, "loop_id", None) or hook.get("session_id") or "default"
        if not isinstance(loop_id, str) or not loop_id.strip():
            raise ValueError("repair loop identity must be a non-empty string")
        loop_digest = canonical_sha256({
            "repository": str(root.resolve()), "gate": args.gate,
            "claim": args.claim, "producer": args.producer,
            "approver": args.approver, "loop_id": loop_id,
        })
        budget_file = _budget_path(verdicts_dir, loop_digest)
        if verdict.state is ReadState.VERIFIED and verdict.record is not None:
            reason = render_packet_text(envelope) if envelope else (
                f"VERDICT {verdict.record['verdict']} (no envelope published)"
            )
            if cycle_note:
                reason += f"\nNOTE {cycle_note}"
            if verdict.record["verdict"] == "PASS":
                _update_misses(budget_file, reset=True)
                return _emit("approve", reason, envelope=envelope,
                             read_state=verdict.state.value, misses=0, budget=budget)
            misses = _update_misses(budget_file)
            if misses >= budget:
                # The 3-miss rule: stopping is deterministic, not babysat.
                return _emit(
                    "approve",
                    reason + f"\nSTOP miss budget exhausted ({misses}/{budget})",
                    envelope=envelope, read_state=verdict.state.value,
                    misses=misses, budget=budget,
                )
            return _emit("block", reason, envelope=envelope,
                         read_state=verdict.state.value, misses=misses, budget=budget)

        reason = (
            f"no verdict could be read for this subject ({verdict.state.value})"
            if cycle_note == ""
            else cycle_note
        )
        if envelope is not None:
            reason += "\n" + render_packet_text(envelope)
        return _emit("approve", reason, envelope=envelope,
                     read_state=verdict.state.value, misses=None, budget=budget)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE


def _pretooluse(
    args: argparse.Namespace,
    hook: dict[str, Any],
    root: Path,
    catalog_path: Path,
) -> int:
    """Block the agent from running the governed suite argv itself (C6).

    The point of the attachment: zero agent-side suite runs. If the tool
    command the harness is about to execute starts with the frozen claim
    argv, the answer is block — the governed gate provides verdict and
    envelope through the read channel, and running the suite by hand
    re-spends the tokens the whole design saves.
    """

    import shlex

    from ranex.bootstrap.composition import claim_definition_for
    from ranex.cli.main import committed_trust_root, head_commit

    tool_input = hook.get("tool_input")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return _emit("approve", "no command to judge", envelope=None,
                     read_state="n-a", misses=None, budget=None)
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        argv = list(lexer)
    except ValueError:
        return _emit("block", "unparsable command", envelope=None,
                     read_state="n-a", misses=None, budget=None)
    commit = head_commit(root)
    catalog_source = committed_trust_root(
        root, commit, args.gate_catalog, catalog_path, "gate catalog"
    )
    claim = claim_definition_for(catalog_source, args.gate, args.claim)
    frozen = list(claim.command) if claim is not None and claim.command else None
    commands: list[list[str]] = [[]]
    for token in argv:
        if token and all(char in ";&|()" for char in token):
            commands.append([])
        else:
            commands[-1].append(token)

    def unwrap(tokens: list[str]) -> list[str]:
        import re

        assignment = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
        # Each iteration removes a wrapper, so nested wrappers retain the same
        # judgment as the command they invoke. Bound expansion depth explicitly.
        for _ in range(32):
            while tokens and assignment.match(tokens[0]):
                tokens = tokens[1:]
            if not tokens:
                return tokens
            program = Path(tokens[0]).name
            if program in {"command", "exec", "time"}:
                tokens = tokens[1:]
                while tokens and tokens[0] in {"--", "-p"}:
                    tokens = tokens[1:]
                continue
            if program in {"sh", "bash", "dash", "zsh"}:
                # A shell payload has a different grammar. Require the Stop
                # hook rather than claiming arbitrary shell evaluation is safe.
                return frozen or tokens
            if program != "env":
                return tokens
            tokens = tokens[1:]
            while tokens:
                option = tokens[0]
                if assignment.match(option) or option in {"-i", "--ignore-environment", "--"}:
                    tokens = tokens[1:]
                elif option in {"-u", "--unset"} and len(tokens) > 1:
                    tokens = tokens[2:]
                elif option.startswith("--unset="):
                    tokens = tokens[1:]
                elif option in {"-S", "--split-string"} or option.startswith("--split-string="):
                    # GNU env uses its own expansion grammar, including variable
                    # substitution. Do not approve a payload we cannot evaluate.
                    return frozen or tokens
                elif option.startswith("-"):
                    return frozen or tokens
                else:
                    break
        return frozen or tokens

    if frozen and any(unwrap(tokens)[: len(frozen)] == frozen for tokens in commands):
        return _emit(
            "block",
            "the governed gate already runs this suite and answers through the "
            "verdict read channel: stop, and let the Stop hook return verdict + "
            "repair envelope",
            envelope=None, read_state="n-a", misses=None, budget=None,
        )
    return _emit("approve", "not the governed suite argv", envelope=None,
                 read_state="n-a", misses=None, budget=None)


def register(task_actions: argparse._SubParsersAction) -> None:
    """Register the attachment under `task`, the delegated-loop surface."""

    stop_hook = task_actions.add_parser(
        "stop-hook",
        help="harness Stop/PreToolUse attachment: governed cycle + repair envelope",
    )
    stop_hook.add_argument(
        "--mode", choices=["stop", "pretooluse"], default="stop",
        help="harness event being answered",
    )
    stop_hook.add_argument("--repository", default=".", help="repository root")
    stop_hook.add_argument("--gate", default="landing", help="gate the loop judges")
    stop_hook.add_argument("--claim", default="tests-executed", help="suite claim to run")
    stop_hook.add_argument("--gate-catalog", default=DEFAULT_GATE_CATALOG,
                           help="committed gate catalog")
    stop_hook.add_argument("--suite-manifest", default=DEFAULT_SUITE_MANIFEST,
                           help="committed frozen suite manifest")
    stop_hook.add_argument("--evidence", default="governance/evidence.json",
                           help="evidence records path")
    stop_hook.add_argument("--producers", default=DEFAULT_PRODUCERS,
                           help="committed producer keyring")
    stop_hook.add_argument("--journal", default=DEFAULT_JOURNAL, help="journal path")
    stop_hook.add_argument("--verdicts-dir", default=DEFAULT_VERDICT_DIR,
                           help="verdict read-channel directory")
    stop_hook.add_argument("--producer", required=True,
                           help="producer identity for the governed run")
    stop_hook.add_argument("--approver", required=True,
                           help="approver identity for the evaluation")
    stop_hook.add_argument("--loop-id", help="stable repair session identity; defaults to harness session_id, then repository/gate/claim scope")
    stop_hook.add_argument("--budget", type=int, default=3,
                           help="deterministic miss budget before the loop stops")
    stop_hook.add_argument("--external-repository",
                           help="explicit external Git checkout root (no kernel vendoring)")
    stop_hook.set_defaults(
        func=cmd_task_stop_hook, trace_dispatch_group="task.stop-hook"
    )
