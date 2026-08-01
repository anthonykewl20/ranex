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
import os
import shlex
import stat
import subprocess
import sys
from pathlib import Path

from ranex.bootstrap.composition import build_gate_evaluator
from ranex.cli.confinement import resolve_within_repository
from ranex.foundation.canonical import canonical_sha256
from ranex.foundation.signing import (
    generate_keypair,
    public_key_for,
    sign_evidence,
)
from ranex.governed_execution.api import (
    Evidence,
    Verdict,
)
from ranex.governed_execution.domain.admission import Admission, admit
from ranex.policy.adapters.configuration.yaml.producer_keyring import (
    KeyringError,
    load_keyring,
)

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

SIGNING_KEY_VARIABLE = "RANEX_SIGNING_KEY"


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


def head_commit(repository_root: Path) -> str:
    """The commit HEAD points at, used to detect the ground moving mid-run."""

    result = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"cannot resolve HEAD: {result.stderr.strip()}")
    return result.stdout.strip()


def load_records(path: Path) -> list[object]:
    """Read the raw evidence array. A missing file is no evidence, not an error.

    A malformed file is an error, never silently no evidence. `{}` used to
    iterate zero keys and return nothing at all, which is indistinguishable
    from an honest absence and therefore the more dangerous of the two.

    Records are returned raw. Deciding which of them are evidence is admission's
    job, and it needs the signature this function deliberately does not strip.
    """

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        # The only OSError that means absence. `Path.exists()` also answers
        # False for EACCES, ENOTDIR and ELOOP, which reports a machine that
        # cannot read its own records as work never done — and chmod is a great
        # deal easier than forging a signature. Every other OSError propagates.
        return []
    except json.JSONDecodeError as exc:
        # A truncated file is corruption, not absence. Saying "no evidence"
        # here would report an interrupted write as work never done.
        raise ValueError(
            f"evidence file at {path} is corrupt and cannot be parsed: {exc}"
        ) from exc
    if not isinstance(raw, list):
        raise ValueError("evidence file must contain a JSON array")
    return list(raw)


def admitted_evidence(path: Path, keyring_path: Path) -> Admission:
    """Raw records plus the keyring, in; evidence plus rejections, out."""

    return admit(load_records(path), load_keyring(keyring_path))


def nearest_existing_directory(path: Path) -> Path:
    """The closest ancestor of `path`, or `path` itself, that exists.

    Neither git nor `os.access` can answer a question about a path that does not
    exist yet. The directory that would hold it is what constrains it.
    """

    candidate = path
    while not candidate.is_dir() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def git_common_dir(directory: Path) -> Path | None:
    """The object store of the repository `directory` sits in, or None.

    Two checkouts of one repository have different toplevels and the same common
    dir. That is exactly what makes them one repository for the only question
    asked here: could a file written under this path be committed?
    """

    result = subprocess.run(
        ["git", "-C", str(directory), "rev-parse", "--git-common-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    # Relative when asked from inside the checkout, absolute when asked from a
    # linked worktree. Joining onto the directory it was asked from normalises
    # both; an absolute answer replaces the left side.
    return (directory / result.stdout.strip()).resolve()


def committable_into(target: Path, governed_root: Path) -> bool:
    """Would `target` land in the governed repository's history if committed?

    Containment under the root is the obvious half. The other half is a linked
    worktree: `git worktree add` produces a second checkout at an unrelated path
    that shares one object store, so a private key written there is `git add`-able
    and reachable from the main checkout while every containment check passes.
    Only git knows which checkouts those are, so ask it from the target's own
    directory.
    """

    if target == governed_root or governed_root in target.parents:
        return True
    common = git_common_dir(nearest_existing_directory(target))
    return common is not None and common == git_common_dir(governed_root)


def private_signing_key(governed_root: Path) -> str:
    """Read the producer's private key from the environment.

    Refuses a key any other account can read. `keygen` writes 0600, but a key
    copied between machines usually arrives with whatever mode the copy gave it,
    and a world-readable signing key makes the whole slice decorative.

    Refuses a key inside the repository for the same reason `keygen` refuses to
    create one there. A refusal only at the point of creation is advisory: the
    key can be placed by hand, and a `.gitignore` entry keeps `git status` clean
    so nothing else notices it is one `git add -f` from being published.
    """

    raw_path = os.environ.get(SIGNING_KEY_VARIABLE)
    if not raw_path:
        raise ValueError(
            f"{SIGNING_KEY_VARIABLE} is not set, so nothing can sign this "
            "record; refusing to write unsigned evidence"
        )
    # Resolved before it is judged: the check must be about the file that will
    # actually be read, not about the name it was reached by.
    key_path = Path(raw_path).resolve()
    if not key_path.is_file():
        raise ValueError(f"{SIGNING_KEY_VARIABLE} points at no file: {key_path}")

    if committable_into(key_path, governed_root):
        raise ValueError(
            f"refusing to sign with the private key at {key_path}: it is inside "
            "the repository under governance and therefore committable. Keys "
            "live outside the tree"
        )

    mode = stat.S_IMODE(key_path.stat().st_mode)
    if mode & 0o077:
        raise ValueError(
            f"private key {key_path} is mode {oct(mode)}; it must not be "
            "readable by group or other. chmod 600 it"
        )
    return key_path.read_text(encoding="utf-8").strip()


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
        # --ignore-submodules=none overrides any submodule.<name>.ignore or
        # diff.ignoreSubmodules setting. Left to the repository's own config, a
        # changed submodule is invisible here while still being present when the
        # command runs — a dirty tree bound to a clean digest.
        [
            "git",
            "-C",
            str(repository_root),
            "status",
            "--porcelain",
            "--ignore-submodules=none",
        ],
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
        payload = line[3:]
        # A rename reports "old -> new" and touches BOTH paths. Taking only the
        # destination let `git mv victim.txt <evidence>` report clean: the
        # destination was exempt, so the source's deletion vanished with it.
        candidates = payload.split(" -> ", 1) if " -> " in payload else [payload]
        for candidate in candidates:
            path = candidate.strip().strip('"')
            if path and path != exempt:
                dirty.append(path)
    return tuple(sorted(dirty))


def refuse_unwritable_evidence(path: Path) -> None:
    """Refuse now if the record could not be written afterwards.

    Probes without creating anything: an existing file must be writable, and an
    absent one needs a directory that accepts it, since `record_evidence` creates
    the missing parents itself.
    """

    if path.exists():
        if not os.access(path, os.W_OK):
            raise ValueError(f"evidence file at {path} cannot be written to")
        return
    directory = nearest_existing_directory(path.parent)
    if not os.access(directory, os.W_OK | os.X_OK):
        raise ValueError(
            f"cannot create the evidence file at {path}: {directory} is not writable"
        )


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
        keyring_path = resolve_within_repository(root, args.producers)
        journal_path = (
            resolve_within_repository(root, args.journal) if args.journal else None
        )
        subject = subject_digest_for(root, args.ref)
        admission = admitted_evidence(evidence_path, keyring_path)
        evaluator = build_gate_evaluator(
            gate_catalog,
            journal_path,
        )
        result = evaluator.evaluate(
            args.gate,
            admission.evidence,
            subject_digest=subject,
            approver_id=args.approver,
        )
    except (
        KeyringError,
        ValueError,
        TypeError,
        KeyError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    if result.verdict is Verdict.PASS:
        print(f"PASS  gate={result.gate_id}  subject={result.subject_digest}")
    else:
        print(f"FAIL  gate={result.gate_id}  rule={result.failing_rule}")

    # Reported whatever the verdict. A forgery the gate happened to pass without
    # is still a forgery, and returning early on PASS made a probe that leaves no
    # trace — which is a probe worth repeating.
    for rejection in admission.rejections:
        print(
            f"      REFUSED record {rejection.index} "
            f"[{rejection.reason}] {rejection.detail}"
        )

    if result.verdict is Verdict.PASS:
        return EXIT_PASS

    # Three different events arrive as `missing_claims`, and the operator must
    # not have to guess which one happened: a record was refused (an attack), a
    # record describes another tree (a replay), or the work was never done. The
    # kernel names them in one sentence because it judges claims, not causes;
    # partitioning per claim here is what keeps a forgery from being printed
    # under the phrasing reserved for honest absence.
    explained = {rejection.claim_id for rejection in admission.rejections}
    missing = set(result.missing_claims)
    replayed = {
        item.claim_id
        for item in admission.evidence
        if item.claim_id in missing and item.subject_digest != result.subject_digest
    }
    refused = sorted(missing & explained)
    absent = sorted(missing - explained - replayed)

    if refused:
        print(
            f"      {len(admission.rejections)} record(s) were refused above; "
            f"no verifying evidence remains for: {', '.join(refused)}"
        )
    if absent:
        print(f"      no evidence for required claim: {', '.join(absent)}")
    if result.reason and (replayed or not missing):
        # The kernel's own diagnosis, kept whenever it says something the
        # partition cannot: stale evidence is the replay that subject binding
        # exists to catch, and a self-approval refusal names no claim at all.
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
        keyring_path = resolve_within_repository(root, args.producers)
        if not command:
            raise ValueError("a command is required after --")

        # Everything that can refuse, refuses before the command runs. A test
        # suite is expensive; discovering afterwards that the record cannot be
        # written honestly wastes all of it.
        private_key = private_signing_key(governed_root)
        keyring = load_keyring(keyring_path)
        registered = keyring.get(args.producer)
        if registered is None:
            raise ValueError(
                f"producer {args.producer!r} is not in {keyring_path.name}; "
                "register its public key before recording evidence"
            )
        if public_key_for(private_key) != registered:
            raise ValueError(
                f"the key in {SIGNING_KEY_VARIABLE} is not the key registered "
                f"for producer {args.producer!r}; the record would be written "
                "and then refused at evaluation"
            )

        # Whether the record can be written is knowable now. Left to
        # `record_evidence`, a corrupt or unwritable evidence file is discovered
        # only once the command has run, changed the tree, and left no record of
        # having done so.
        load_records(evidence_path)
        refuse_unwritable_evidence(evidence_path)

        # Refuse before running, not after: a claim we cannot honestly bind to a
        # subject should cost nothing to discover.
        dirty = uncommitted_paths(root, ignoring=evidence_path)
        if dirty:
            raise ValueError(
                "refusing to record evidence against a dirty working tree; "
                f"HEAD does not describe: {', '.join(dirty)}"
            )
        # HEAD, always, and deliberately not selectable. The command runs against
        # the checked-out tree, so naming any other ref would record a digest for
        # a tree that was never observed — a false claim reachable straight from
        # the documented interface.
        subject = subject_digest_for(root, "HEAD")
        started_at = head_commit(root)
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    try:
        # The observed command is the agent's work, untrusted by definition.
        # Inheriting $RANEX_SIGNING_KEY hands it the producer's private key, and
        # a key the subject of the observation can read lets it sign whatever
        # record it likes — signatures would then prove only that something ran
        # on this machine. The key was read before this point; the child has no
        # use for the variable.
        environment = {
            name: value
            for name, value in os.environ.items()
            if name != SIGNING_KEY_VARIABLE
        }
        completed = subprocess.run(command, cwd=root, check=False, env=environment)
    except OSError as exc:
        print(f"ERROR  cannot run {command[0]!r}: {exc}", file=sys.stderr)
        return EXIT_USAGE

    try:
        # Removing --ref shut one door; the command could still walk through
        # another by checking out elsewhere, leaving the recorded digest
        # describing a tree it never ran against. Creating files is legitimate
        # and must still pass — moving HEAD never is.
        if head_commit(root) != started_at:
            raise ValueError(
                "refusing to record evidence: the command moved HEAD from "
                f"{started_at[:12]} during the run, so {subject[:19]}… "
                "does not describe what was observed"
            )
        content = {
            "claim_id": args.claim,
            "subject_digest": subject,
            "producer_id": args.producer,
            "command": shlex.join(command),
            "exit_code": int(completed.returncode),
        }
        record_evidence(
            evidence_path,
            {**content, "signature": sign_evidence(content, private_key)},
        )
    except (ValueError, TypeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(
        f"RECORDED  claim={args.claim}  producer={args.producer}  "
        f"exit={completed.returncode}"
    )
    print(f"          subject={subject}")
    return int(completed.returncode)


def cmd_keygen(args: argparse.Namespace) -> int:
    """Generate a producer's signing key, outside the repository.

    The confinement here is the inverse of `resolve_within_repository`: that
    refuses paths outside the repository, this refuses paths inside it. The
    slice's premise is that private keys never enter the tree, and an
    environment variable pointing inward must be refused rather than obeyed —
    otherwise the key ends up committed and every other guarantee is theatre.
    """

    try:
        governed_root = governed_repository_root()

        raw_path = os.environ.get(SIGNING_KEY_VARIABLE)
        if not raw_path:
            raise ValueError(
                f"{SIGNING_KEY_VARIABLE} is not set; point it at the file the "
                "private key should live in, outside this repository"
            )

        target = Path(raw_path)
        if not target.is_absolute():
            # A relative path resolves against whatever the current directory
            # happens to be, which is very often the repository itself.
            raise ValueError(
                f"{SIGNING_KEY_VARIABLE} must be an absolute path, got {raw_path!r}"
            )
        target = target.resolve()

        if committable_into(target, governed_root):
            raise ValueError(
                f"refusing to write a private key inside the repository: {target}. "
                "Private keys must never be committable"
            )
        if target.is_dir():
            raise ValueError(f"{SIGNING_KEY_VARIABLE} is a directory: {target}")
        if target.exists():
            # Replacing a key silently orphans every record it ever signed.
            raise ValueError(
                f"refusing to overwrite the existing key at {target}; "
                "remove it deliberately if you mean to replace it"
            )

        private_key, public_key = generate_keypair()
        target.parent.mkdir(parents=True, exist_ok=True)
        # Created 0600, not chmod'ed to 0600 afterwards: between creation and
        # chmod the key would briefly be world-readable.
        handle = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(handle, "w", encoding="utf-8") as file:
            file.write(private_key + "\n")
    except (ValueError, OSError) as exc:
        print(f"ERROR  {exc}", file=sys.stderr)
        return EXIT_USAGE

    print(f"WROTE  {target}  mode 0600")
    print("       register the producer by adding this line to the keyring:")
    print(f"  {args.producer}: {public_key}")
    return EXIT_PASS


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
    ev.add_argument(
        "--producers",
        default="governance/producers.yaml",
        help="committed keyring of producer public keys",
    )
    ev.add_argument("--approver", required=True, help="identity approving")
    ev.add_argument("--journal", default="governance/journal.sqlite3", help="journal path")
    ev.set_defaults(func=cmd_gate_evaluate)

    rn = sub.add_parser("run", help="run a command and record evidence of it")
    rn.add_argument("--claim", required=True, help="claim this evidences")
    rn.add_argument("--producer", required=True, help="identity running the command")
    rn.add_argument("--repository", default=".", help="repository root")
    # No --ref. The subject is always HEAD, because HEAD is what the command
    # runs against. Offering a choice offers a way to record a false claim.
    rn.add_argument(
        "--evidence",
        default="governance/evidence.json",
        help="evidence records path",
    )
    rn.add_argument(
        "--producers",
        default="governance/producers.yaml",
        help="committed keyring of producer public keys",
    )
    rn.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="the command to run, after --",
    )
    rn.set_defaults(func=cmd_run)

    kg = sub.add_parser("keygen", help="generate a producer signing key")
    kg.add_argument("--producer", required=True, help="identity the key belongs to")
    kg.set_defaults(func=cmd_keygen)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
