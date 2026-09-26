#!/usr/bin/env python3
"""ADP proof — the architecture-freeze claim, governed on a real subject.

Real `ranex` subprocesses (the installed console script, real Ed25519 keys,
real journal, real Git) over a synthetic governed package whose import graph
a human-approved freeze describes — the arch-maintain micro-experiment
promoted to the shipped scanner: `ranex-arch`, the kernel's own console
script, with the freeze digest pinned in the signed argv (#110 Correction
2's admitted shape; the lab's standalone-script argv[0] and a `-m` module
form were both scaffolding — the module form loses the venv to argv[0]
resolution, measured live).

Arms (control pairs, fresh workspace per construction — evaluation of one
repo would be pseudoreplication):

  forbidden-edge-blocks x3   pristine PASS / planted `from pkg import policy`
                            in pkg/foundation.py FAIL, naming file:line and
                            the foundation->policy edge; repeats must be
                            byte-identical (determinism corroboration).
  accepted-exception         the planted finding declared --accepted PASSES;
                            the same plant under a manifest without the
                            declaration FAILs. Fingerprint identity: one ID.
  freeze-tamper              the allow-list weakened to bless the plant, with
                            the catalog's digest pin untouched: the scan
                            answers arch/freeze-tampered and the gate FAILs.
  absence-blocks             no scan recorded: FAIL naming the claim.

Run from the kernel checkout with its venv interpreter:

    .venv/bin/python tools/dogfood/arch_proof.py

Writes tools/dogfood/audits/2026-09-26-arch-freeze/ (receipt.json,
commands.json).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

KERNEL = Path(__file__).resolve().parents[2]
PY = KERNEL / ".venv" / "bin" / "python"
RANEX = KERNEL / ".venv" / "bin" / "ranex"
RANEX_ARCH = KERNEL / ".venv" / "bin" / "ranex-arch"
AUDIT = KERNEL / "tools/dogfood/audits/2026-09-26-arch-freeze"

PRODUCER = "arch-proof-producer"
SIGNER = "kernel-verdict-signer"
APPROVER = "arch-proof-approver"

ARTIFACT = "governance/scan.sarif"
MANIFEST = "governance/scan-manifest.json"
FREEZE = "governance/architecture-freeze.json"
SCOPE = sorted(
    [
        "pkg/__init__.py",
        "pkg/cli.py",
        "pkg/foundation.py",
        "pkg/policy.py",
        FREEZE,
    ]
)
RULES = ["arch/forbidden-import", "arch/freeze-tampered"]

#: Run products are ignored, exactly as the kernel repository ignores its
#: own: a governed run writes the artifact, evidence, journal and verdicts,
#: and the tree a freeze judges must stay describable by HEAD.
GITIGNORE = """governance/scan.sarif
governance/evidence.json
governance/journal.sqlite3
governance/verdicts/
"""

SUBJECT_FILES = {
    ".gitignore": GITIGNORE,
    "pkg/__init__.py": "",
    "pkg/foundation.py": "def base():\n    return 1\n",
    "pkg/policy.py": (
        "from pkg import foundation\n\n\ndef rule():\n"
        "    return foundation.base() + 1\n"
    ),
    "pkg/cli.py": (
        "from pkg import foundation\nfrom pkg import policy\n\n\n"
        "def main():\n    return policy.rule() + foundation.base()\n"
    ),
    "README.md": "# synthetic governed subject for the architecture-freeze proof\n",
}

PLANTED = "\nfrom pkg import policy  # planted forbidden edge\n"

REPEATS = 3


def freeze_value() -> dict[str, Any]:
    return {
        "schema": "ranex-architecture-freeze-v1",
        "approved_by": "ADR-064 adp-agnostic-diagnostic-plane (proposed)",
        "package_root": "pkg",
        "modules": {
            "root": "pkg/__init__.py",
            "foundation": "pkg/foundation.py",
            "policy": "pkg/policy.py",
            "cli": "pkg/cli.py",
        },
        "allowed_edges": [
            ["cli", "foundation"],
            ["cli", "policy"],
            ["policy", "foundation"],
        ],
    }


def canonical(value: Any) -> bytes:
    from ranex.foundation.canonical import canonical_json_bytes

    return canonical_json_bytes(value)


def freeze_digest(raw: bytes) -> str:
    from ranex.foundation.arch_scan import freeze_digest_of_bytes

    return freeze_digest_of_bytes(raw)


def scan_argv(digest: str) -> list[str]:
    """The shipped shape: the kernel's own console script, digest pinned.

    A governed run resolves argv[0] once and executes the resolved path, so
    a `-m` module form loses the venv's site-packages to the symlink's
    target interpreter (measured live: ModuleNotFoundError in the hermetic
    run). The console script is a regular file whose shebang re-selects the
    venv interpreter — the kernel's own bytes are what runs, and #110
    Correction 2's script-operand refusal stays satisfied because argv[0]
    is the scanner itself.
    """

    return [
        str(RANEX_ARCH),
        "check",
        "--freeze",
        FREEZE,
        "--expected-freeze-digest",
        digest,
        "--output-format=sarif",
        f"--output-file={ARTIFACT}",
    ]


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=arch-proof@ranex.invalid",
            "-c",
            "user.name=ranex-arch-proof",
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


COMMANDS: list[dict[str, Any]] = []


def ranex(
    repo: Path,
    *args: str,
    key: Path | None = None,
    verdict_key: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """The installed console script, anchored to an external checkout (ADR-052)."""

    environment = dict(os.environ)
    for variable in (
        "RANEX_SIGNING_KEY",
        "RANEX_VERDICT_SIGNING_KEY",
        "RANEX_VERDICT_DIR",
    ):
        environment.pop(variable, None)
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    if verdict_key is not None:
        environment["RANEX_VERDICT_SIGNING_KEY"] = str(verdict_key)
        environment["RANEX_VERDICT_DIR"] = "governance/verdicts"
    argv = list(args)
    selector = ["--external-repository", str(repo)]
    separator = argv.index("--") if "--" in argv else len(argv)
    return subprocess.run(
        [str(RANEX), *argv[:separator], *selector, *argv[separator:]],
        cwd=str(repo),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=600,
    )


def recorded(repo: Path, *args: str, **kw: Any) -> subprocess.CompletedProcess[str]:
    completed = ranex(repo, *args, **kw)
    COMMANDS.append(
        {
            "argv": list(args),
            "exit": completed.returncode,
            "stdout_tail": completed.stdout[-400:],
            "stderr_tail": completed.stderr[-400:],
        }
    )
    return completed


def minted(repo: Path, identity: str, key: Path) -> str:
    keygen = recorded(repo, "keygen", "--producer", identity, key=key)
    if keygen.returncode != 0 or not key.is_file():
        raise SystemExit(f"keygen failed: {keygen.stderr[-400:]}")
    return next(
        line.split()[-1].strip()
        for line in keygen.stdout.splitlines()
        if line.strip().startswith(identity)
    )


def freeze_argv(
    digest: str, accepted: dict[str, str] | None = None
) -> list[str]:
    return [
        "suite",
        "freeze",
        "--artifact",
        ARTIFACT,
        "--output",
        MANIFEST,
        "--results-reporter",
        "sarif-2.1.0",
        *[flag for path in SCOPE for flag in ("--scan-scope", path)],
        *[flag for rule in RULES for flag in ("--scan-rule", rule)],
        *[
            flag
            for finding, reason in (accepted or {}).items()
            for flag in ("--accepted", f"{finding}={reason}")
        ],
        "--",
        *scan_argv(digest),
    ]


def governed(
    workspace: Path,
    *,
    freeze_raw: bytes | None = None,
    pin: str | None = None,
    accepted: dict[str, str] | None = None,
) -> tuple[Path, Path, Path, str]:
    """A fresh governed synthetic subject, frozen over a real clean scan.

    `pin` overrides the digest the catalog binds — the tamper arm's lever:
    the subject carries weakened freeze bytes while the catalog keeps
    pinning the approved digest, which is exactly what an unapproved freeze
    edit looks like to a governed run.
    """

    raw = freeze_raw if freeze_raw is not None else canonical(freeze_value())
    digest = pin if pin is not None else freeze_digest(raw)
    repo = workspace / "subject"
    repo.mkdir(parents=True)
    for relative, text in SUBJECT_FILES.items():
        (repo / relative).parent.mkdir(parents=True, exist_ok=True)
        (repo / relative).write_text(text, encoding="utf-8")
    (repo / "governance").mkdir()
    (repo / FREEZE).write_bytes(raw)
    git(repo, "init", "-q")
    key = workspace / "producer.key"
    verdict_key = workspace / "verdict-signer.key"
    public = minted(repo, PRODUCER, key)
    signer = minted(repo, SIGNER, verdict_key)
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  {PRODUCER}: {public}\n"
        f"verdict_signer:\n  id: {SIGNER}\n  public_key: {signer}\n",
        encoding="utf-8",
    )
    (repo / "governance" / "gates.yaml").write_text(catalog(digest), encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "subject: synthetic package + approved architecture freeze")

    frozen = recorded(repo, *freeze_argv(digest, accepted))
    if frozen.returncode != 0:
        raise SystemExit(f"freeze failed:\n{frozen.stdout[-800:]}\n{frozen.stderr[-800:]}")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "governance: freeze the scan manifest")
    return repo, key, verdict_key, digest


def catalog(digest: str) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: ARCHITECTURE_FROZEN\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: architecture\n"
        f"        command: {json.dumps(scan_argv(digest))}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: sarif-2.1.0\n"
        f"        results_manifest: {MANIFEST}\n"
    )


def plant(repo: Path) -> None:
    path = repo / "pkg" / "foundation.py"
    path.write_text(path.read_text(encoding="utf-8") + PLANTED, encoding="utf-8")
    git(repo, "commit", "-qam", "planted forbidden edge: foundation -> policy")


def observed_findings(repo: Path, pinned: str | None = None) -> list[dict[str, Any]]:
    """What the scanner reports over `repo`'s working tree.

    The governed run's own artifact lives in its materialisation, disposed
    with it, so this is a direct scanner observation over the same bytes —
    the identity is byte-derived (the #97 fingerprint over the subject), so
    it is the same finding the governed run reported; the verdict, not this
    observation, is the authority. The lab learned this the same way (the
    arch-maintain report's honesty note D-series).
    """

    digest = pinned if pinned is not None else freeze_digest((repo / FREEZE).read_bytes())
    completed = subprocess.run(
        [
            str(RANEX_ARCH),
            "check",
            "--freeze",
            FREEZE,
            "--expected-freeze-digest",
            digest,
            "--output-format=sarif",
            f"--output-file={ARTIFACT}",
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if completed.returncode != 0:
        return [
            {
                "rule": "scan-refused",
                "file": None,
                "line": None,
                "detail": completed.stderr.strip().splitlines()[-1],
            }
        ]
    sarif_path = repo / ARTIFACT
    document = json.loads(sarif_path.read_text(encoding="utf-8"))
    return [
        {
            "rule": result["ruleId"],
            "file": result["locations"][0]["physicalLocation"]["artifactLocation"][
                "uri"
            ],
            "line": result["locations"][0]["physicalLocation"]["region"]["startLine"],
            "fingerprint": result["fingerprints"]["ranex/v1"],
        }
        for result in document["runs"][0]["results"]
    ]


def gate(
    repo: Path,
    key: Path,
    verdict_key: Path,
    pinned: str,
    *,
    observe: bool = True,
) -> dict[str, Any]:
    """Judge the workspace, replaying exactly the argv the catalog bound.

    `pinned` is the digest the catalog carries — the same bytes the evidence
    record's command digest covers. Recomputing it from the working tree's
    freeze would make the pin self-consistent with whatever the tree says
    today, which is precisely the silent policy change the pin exists to
    refuse.
    """

    run_exit = None
    if observe:
        observed = recorded(
            repo,
            "run",
            "--claim",
            "architecture",
            "--producer",
            PRODUCER,
            "--gate-catalog",
            "governance/gates.yaml",
            "--producers",
            "governance/producers.yaml",
            "--evidence",
            "governance/evidence.json",
            "--",
            *scan_argv(pinned),
            key=key,
        )
        run_exit = observed.returncode
    verdict = recorded(
        repo,
        "gate",
        "evaluate",
        "HEAD",
        "--gate-catalog",
        "governance/gates.yaml",
        "--producers",
        "governance/producers.yaml",
        "--evidence",
        "governance/evidence.json",
        "--approver",
        APPROVER,
        verdict_key=verdict_key,
    )
    verdict_line = next(
        (line for line in verdict.stdout.splitlines() if line.startswith(("PASS", "FAIL"))),
        None,
    )
    return {
        "run_exit": run_exit,
        "verdict": verdict_line.split()[0] if verdict_line else "ERROR",
        "evaluate_exit": verdict.returncode,
        "verdict_line": verdict_line,
        "findings": observed_findings(repo, pinned),
        "evaluate_error_tail": verdict.stderr.strip().splitlines()[-3:],
    }


def decision_core(outcome: dict[str, Any]) -> dict[str, Any]:
    """The construction-independent core of one gate outcome."""

    return {
        "verdict": outcome["verdict"],
        "run_exit": outcome["run_exit"],
        "evaluate_exit": outcome["evaluate_exit"],
        "findings": outcome["findings"],
    }


def measured(
    prepare: Callable[[Path], None] | None = None,
    *,
    observe: bool = True,
    freeze_raw: bytes | None = None,
    pin: str | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="ranex-arch-") as scratch:
        repo, key, verdict_key, pinned = governed(
            Path(scratch), freeze_raw=freeze_raw, pin=pin
        )
        if prepare is not None:
            prepare(repo)
        return gate(repo, key, verdict_key, pinned, observe=observe)


def main() -> int:
    if not RANEX.is_file():
        raise SystemExit("the installed console script is absent")
    sys.path.insert(0, str(KERNEL / "src"))
    receipts: dict[str, Any] = {
        "repeats": REPEATS,
        "scanner": "ranex-arch (the kernel's installed console script)",
        "arms": {},
    }

    # 1. forbidden-edge-blocks x3, byte-identical across repeats
    repeats: list[dict[str, Any]] = []
    for repeat in range(1, REPEATS + 1):
        start = time.monotonic()
        pristine = measured()
        planted = measured(plant)
        elapsed = round(time.monotonic() - start, 1)
        entry = {"pristine": pristine, "planted": planted, "seconds": elapsed}
        receipts["arms"][f"forbidden-edge-blocks/r{repeat}"] = entry
        repeats.append(entry)
        print(
            f"r{repeat}: pristine={pristine['verdict']} planted={planted['verdict']} "
            f"({elapsed}s) run_exit(planted)={planted['run_exit']} "
            f"findings={planted['findings'][:1]}"
        )
    receipts["summary"] = {
        "pristine_all_PASS": all(r["pristine"]["verdict"] == "PASS" for r in repeats),
        "planted_all_FAIL": all(r["planted"]["verdict"] == "FAIL" for r in repeats),
        # Byte-identity is judged on the decision core: verdict word, exits
        # and findings (whose fingerprints derive from the subject's bytes).
        # The verdict line's subject digest is excluded because each repeat
        # constructs a fresh workspace with fresh Ed25519 keys — independent
        # replication at the construction level, the lab's design; a shared
        # keyring would be shared state, and identical subject digests bought
        # that way would be pseudoreplication, not determinism.
        "pristine_byte_identical": len(
            {json.dumps(decision_core(r["pristine"]), sort_keys=True) for r in repeats}
        )
        == 1,
        "planted_byte_identical": len(
            {json.dumps(decision_core(r["planted"]), sort_keys=True) for r in repeats}
        )
        == 1,
        "planted_names_file_line_edge": all(
            r["planted"]["findings"]
            and r["planted"]["findings"][0]["file"] == "pkg/foundation.py"
            and r["planted"]["findings"][0]["rule"] == "arch/forbidden-import"
            for r in repeats
        ),
    }

    # 2. accepted-exception, both directions in one governed workspace
    with tempfile.TemporaryDirectory(prefix="ranex-arch-") as scratch:
        repo, key, verdict_key, pinned = governed(Path(scratch))
        plant(repo)
        undeclared = gate(repo, key, verdict_key, pinned)
        (finding,) = (
            f for f in observed_findings(repo) if f["rule"] == "arch/forbidden-import"
        )
        identifier = (
            f"{finding['file']}::arch/forbidden-import::{finding['fingerprint']}"
        )
        digest = freeze_digest((repo / FREEZE).read_bytes())
        # declare: re-freeze the manifest carrying the exception
        frozen = recorded(
            repo,
            *freeze_argv(
                digest,
                {identifier: "review accepted this edge pending ADR revision"},
            ),
        )
        if frozen.returncode != 0:
            raise SystemExit(
                f"accepted freeze failed:\n{frozen.stdout[-600:]}\n{frozen.stderr[-600:]}"
            )
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "governance: declare the reviewed exception")
        declared = gate(repo, key, verdict_key, pinned)
        # remove the declaration: re-freeze without --accepted
        frozen = recorded(repo, *freeze_argv(digest))
        if frozen.returncode != 0:
            raise SystemExit(
                f"plain refreeze failed:\n{frozen.stdout[-600:]}\n{frozen.stderr[-600:]}"
            )
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "governance: remove the declared exception")
        removed = gate(repo, key, verdict_key, pinned)
        receipts["arms"]["accepted-exception"] = {
            "finding_id": identifier,
            "undeclared": undeclared,
            "declared": declared,
            "removed": removed,
        }
        print(
            f"accepted: undeclared={undeclared['verdict']} "
            f"declared={declared['verdict']} removed={removed['verdict']}"
        )
        receipts["summary"]["accepted_declared_PASSes"] = declared["verdict"] == "PASS"
        receipts["summary"]["accepted_removed_FAILs"] = removed["verdict"] == "FAIL"

    # 3. freeze-tamper: weaken the allow-list, keep the catalog's pin
    weakened = dict(freeze_value())
    weakened["allowed_edges"] = [
        ["cli", "foundation"],
        ["cli", "policy"],
        ["foundation", "policy"],
        ["policy", "foundation"],
    ]

    def tamper(repo: Path) -> None:
        plant(repo)
        (repo / FREEZE).write_bytes(canonical(weakened))
        git(repo, "commit", "-qam", "tamper: weaken the freeze allow-list")

    approved = freeze_digest(canonical(freeze_value()))
    start = time.monotonic()
    tampered = measured(
        tamper, freeze_raw=canonical(weakened), pin=approved
    )
    receipts["arms"]["freeze-tamper"] = {
        "tampered": tampered,
        "seconds": round(time.monotonic() - start, 1),
    }
    print(
        f"tamper: verdict={tampered['verdict']} "
        f"findings={[(f['rule'], f['file']) for f in tampered['findings']]}"
    )
    receipts["summary"]["tampered_FAILs"] = tampered["verdict"] == "FAIL"
    receipts["summary"]["tampered_names_freeze"] = any(
        f["rule"] == "arch/freeze-tampered" and f["file"] == FREEZE
        for f in tampered["findings"]
    )

    # 4. absence-blocks: no scan recorded
    start = time.monotonic()
    positive = measured()
    absent = measured(observe=False)
    receipts["arms"]["absence-blocks"] = {
        "pristine": positive,
        "never_ran": absent,
        "seconds": round(time.monotonic() - start, 1),
    }
    print(f"absence: pristine={positive['verdict']} never_ran={absent['verdict']}")
    receipts["summary"]["absence_FAILs"] = absent["verdict"] == "FAIL"

    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "receipt.json").write_text(
        json.dumps(receipts, indent=1, sort_keys=True), encoding="utf-8"
    )
    (AUDIT / "commands.json").write_text(json.dumps(COMMANDS, indent=1), encoding="utf-8")
    failed = [name for name, ok in receipts["summary"].items() if not ok]
    if failed:
        print(f"FAILED controls: {failed}")
        return 1
    print(f"ALL CONTROLS PASS  receipts={AUDIT / 'receipt.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
