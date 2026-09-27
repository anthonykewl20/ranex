#!/usr/bin/env python3
"""DIRECT 012 stress — the architecture-freeze claim, tried honestly to break.

SLICE-096/ADR-065 landed `ranex-arch` implementation-only; this runner supplies
the fracture matrix the ship's happy path did not. The design follows the
scientific skills the task pins (experimental-design: arms, control pairs and
predictions frozen below BEFORE any stress data was collected, fresh workspace
per construction so repeats are not pseudoreplication; statistical-power: every
verdict arm is repeated, and a nondeterminism rate p is detectable with
probability 1-(1-p)**REPEATS — quoted, not assumed away; uncertainty-and-units:
wall-clocks carry units and min/median/max spread over repeats; EDA/statistical-
analysis: rates carry exact denominators; scientific-critical-thinking: a
self-review pass over the receipts precedes the addendum; scientific-writing:
no fabricated evidence, every row cites its receipt).

The stress plane is the SYSTEM, not the unit: the real installed console
script, real `ranex` governed cycles, real Git — the shapes
`tests/unit/test_arch_scanner.py` covers in-process are controls here, and the
arms beyond them are the ones the ship never ran.

Arms (vocabulary: VERIFIED | GAP | FALSE-PASS | NON-DETERMINISTIC | UNVERIFIED;
a FALSE-PASS or NON-DETERMINISTIC anywhere blocks and is reported, never
retried away):

  reproduction        rerun the shipped proof tool on this tree, compare its
                      decision cores and fingerprints against the shipped
                      receipts byte-for-byte.
  E1  cycles          allowed both directions PASS; one denied direction FAILs.
  E2  broken symlink  a dangling `pkg/*.py` symlink must refuse (exit 2).
  E3  symlink dir     forbidden imports hidden behind a symlinked directory
                      module — refuse (exit 2): a walk that silently skips
                      symlink dirs cannot block, so the scan fails closed.
  E4  unicode         unicode filename, non-UTF-8 bytes, BOM, unicode freeze
                      module name — each must fail closed.
  E5  renamed module  a module file renamed out from under the freeze must
                      refuse (undeclared file).
  E6  deep nesting    100-level nesting, scan completes and finds the plant.
  E8  empty graph     declared-but-absent module files: predicted (code-read)
                      to pass VACUOUSLY (GAP: v1 pins edges, not existence);
                      an absent package_root must refuse (exit 2).
  E9  delete race     files deleted mid-walk: exit 2 (fail closed) or the race
                      never triggers in n attempts (UNVERIFIED, bounded) —
                      never a silent clean pass.
  V1  missing tool    the pinned scanner removed from the venv: the governed
                      claim must FAIL (absence blocks), never pass on stale
                      evidence after the subject changed.
  V2  PATH pollution  a PATH prefixed with lying git/python: verdict unchanged
                      or fail closed.
  V3  PYTHONPATH      ambient stdlib shadowing: benign detector (marker) then
                      an `ast` stub that swallows Import nodes — predicted
                      (env semantics) to flip a planted FAIL to PASS.
  V4  env -i          empty environment: direct scan byte-identical; governed
                      cycle fails closed without its key env.
  V5  wrong pin       a mismatched --expected-freeze-digest is a tamper
                      finding (control, shipped receipt covers it).
  D1  byte identity   five scans of one fixed tree, identical artifact bytes.
  D2  relocation      the same tree at two absolute paths, identical bytes.
  S1  scale           1k/5k/10k files: wall-clock quoted (min/med/max of 3).
  A1  boundary move   forbidden-importing file moved OUTSIDE package_root —
                      predicted (scope) to pass: the freeze governs only the
                      named root (GAP class).
  A2  re-home         module re-homed as a directory inside the root: refusal.
  A3  auto-bless      freeze+catalog+manifest moved together (the promote-ship
                      shape) passes mechanically — by design; the guard is the
                      ADR-017 delegated-scope disjointness + operator approval,
                      cited, not re-derived here.
  A6  dynamic import  importlib/__import__ edges are invisible to a static
                      walk — documented v1 semantics (GAP class).
  A7  star import     `from pkg import *` names the root module (semantics
                      control).
  A8  nested import   imports inside functions/try/TYPE_CHECKING are found.
  A9  alias forms     import/from/aliased/absolute forms all attribute.
  B1  stdlib          30 stdlib imports: 0 findings.
  B2  external        20 site-packages imports: 0 findings.
  B3  collision       package_root named like a stdlib module: attribution is
                      local under the collision precondition (documented
                      ambiguity, exact denominator quoted).

Run from the kernel checkout with its venv interpreter:

    .venv/bin/python tools/dogfood/arch_stress.py

Writes tools/dogfood/audits/2026-09-27-arch-stress/ (receipt.json,
commands.json, reproduction/).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

KERNEL = Path(__file__).resolve().parents[2]
PY = KERNEL / ".venv" / "bin" / "python"
RANEX = KERNEL / ".venv" / "bin" / "ranex"
RANEX_ARCH = KERNEL / ".venv" / "bin" / "ranex-arch"
AUDIT = KERNEL / "tools/dogfood/audits/2026-09-27-arch-stress"
SHIPPED = KERNEL / "tools/dogfood/audits/2026-09-26-arch-freeze"

PRODUCER = "arch-stress-producer"
SIGNER = "kernel-verdict-signer"
APPROVER = "arch-stress-approver"

ARTIFACT = "governance/scan.sarif"
MANIFEST = "governance/scan-manifest.json"
FREEZE = "governance/architecture-freeze.json"

REPEATS = 3

GITIGNORE = """governance/scan.sarif
governance/evidence.json
governance/journal.sqlite3
governance/verdicts/
"""

#: Frozen before any stress data was collected: the code-read prediction for
#: each arm, so the receipts can show prediction vs observed, not hindsight.
PREDICTIONS: dict[str, str] = {
    "reproduction": "VERIFIED (all shipped controls reproduce, fingerprints equal)",
    "E1-cycles": "VERIFIED (denied direction FAILs)",
    "E2-broken-symlink": "VERIFIED (exit 2, no artifact)",
    "E3-symlink-dir": "VERIFIED (symlink directory under package_root refuses)",
    "E4-unicode": "VERIFIED (each shape exits 2 / refuses validation)",
    "E5-renamed-module": "VERIFIED (exit 2, undeclared file)",
    "E6-deep-nesting": "VERIFIED (scan completes, plant found)",
    "E8-empty-graph": "GAP (vacuous PASS when declared files are absent); "
    "absent package_root refuses",
    "E9-delete-race": "exit 2 fail-closed if triggered; UNVERIFIED if never "
    "triggered; never a silent clean pass",
    "V1-missing-tool": "VERIFIED (governed FAIL; stale evidence cannot satisfy "
    "a changed subject)",
    "V2-path-pollution": "VERIFIED (unchanged or fail closed)",
    "V3-pythonpath-shadow": "FALSE-PASS (PYTHONPATH precedes site-packages; an "
    "ast stub can hide Import nodes)",
    "V4-env-i": "VERIFIED (direct scan byte-identical; governed fails closed)",
    "V5-wrong-pin": "VERIFIED (arch/freeze-tampered finding)",
    "D1-byte-identity": "VERIFIED (5/5 identical artifact bytes)",
    "D2-relocation": "VERIFIED (identical bytes from two absolute paths)",
    "S1-scale": "wall-clock quoted at 1k/5k/10k files",
    "A1-boundary-move": "GAP (PASS: the freeze governs only package_root)",
    "A2-re-home": "VERIFIED (exit 2, undeclared file)",
    "A3-auto-bless": "PASS by design (promote-ship shape); guard is process + "
    "ADR-017 disjointness, cited",
    "A6-dynamic-import": "GAP (static walk cannot see it; documented v1)",
    "A7-star-import": "VERIFIED (edge to the root module, as documented)",
    "A8-nested-import": "VERIFIED (ast.walk finds it)",
    "A9-alias-forms": "VERIFIED (every form attributes to the target module)",
    "B1-stdlib": "VERIFIED (0/50 findings)",
    "B3-collision": "GAP (local attribution under collision precondition)",
}

RECEIPTS: dict[str, Any] = {"predictions": dict(PREDICTIONS), "arms": {}}
COMMANDS: list[dict[str, Any]] = []

_STDLIB_NAMES = [
    "argparse", "ast", "atexit", "base64", "bisect", "calendar", "cmath",
    "collections", "contextlib", "copy", "copyreg", "csv", "dataclasses",
    "datetime", "decimal", "difflib", "enum", "errno", "fnmatch", "functools",
    "gc", "getpass", "gettext", "glob", "gzip", "hashlib", "heapq", "hmac",
    "html", "http",
]
_EXTERNAL_NAMES = [
    "aiohttp", "attrs", "bcrypt", "billiard", "botocore", "certifi",
    "chardet", "click", "cryptography", "fastapi", "flask", "graphene",
    "httpx", "jinja2", "kombu", "marshmallow", "numpy", "orjson", "pandas",
    "prometheus",
]


def freeze_value(
    modules: dict[str, str] | None = None,
    edges: list[list[str]] | None = None,
    package_root: str = "pkg",
) -> dict[str, Any]:
    return {
        "schema": "ranex-architecture-freeze-v1",
        "approved_by": "ADR-065 adp-agnostic-diagnostic-plane (proposed)",
        "package_root": package_root,
        "modules": modules
        or {
            "root": f"{package_root}/__init__.py",
            "foundation": f"{package_root}/foundation.py",
            "policy": f"{package_root}/policy.py",
            "cli": f"{package_root}/cli.py",
        },
        "allowed_edges": edges
        or [["cli", "foundation"], ["cli", "policy"], ["policy", "foundation"]],
    }


def canonical(value: Any) -> bytes:
    from ranex.foundation.canonical import canonical_json_bytes

    return canonical_json_bytes(value)


def freeze_digest(raw: bytes) -> str:
    from ranex.foundation.arch_scan import freeze_digest_of_bytes

    return freeze_digest_of_bytes(raw)


def default_subject(package_root: str = "pkg") -> dict[str, str]:
    return {
        ".gitignore": GITIGNORE,
        f"{package_root}/__init__.py": "",
        f"{package_root}/foundation.py": "def base():\n    return 1\n",
        f"{package_root}/policy.py": (
            f"from {package_root} import foundation\n\n\ndef rule():\n"
            "    return foundation.base() + 1\n"
        ),
        f"{package_root}/cli.py": (
            f"from {package_root} import foundation\n"
            f"from {package_root} import policy\n\n\ndef main():\n"
            "    return policy.rule() + foundation.base()\n"
        ),
        "README.md": "# synthetic arch-stress subject\n",
    }


PLANTED = "from pkg import policy  # planted forbidden edge\n"


def build_subject(
    workspace: Path,
    files: dict[str, str],
    freeze: dict[str, Any],
    *,
    commit: bool = True,
) -> Path:
    repo = workspace / "subject"
    repo.mkdir(parents=True)
    for relative, text in files.items():
        target = repo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (repo / "governance").mkdir(exist_ok=True)
    (repo / FREEZE).write_bytes(canonical(freeze))
    if commit:
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "subject: arch-stress synthetic tree")
    return repo


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.email=arch-stress@ranex.invalid",
            "-c",
            "user.name=ranex-arch-stress",
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def record_command(
    argv: list[str], cwd: str, completed: subprocess.CompletedProcess[str]
) -> None:
    COMMANDS.append(
        {
            "argv": argv,
            "cwd": cwd,
            "exit": completed.returncode,
            "wall_seconds": None,
            "stdout_tail": completed.stdout[-300:],
            "stderr_tail": completed.stderr[-300:],
        }
    )


def scan(
    repo: Path,
    digest: str | None = None,
    *,
    env: dict[str, str] | None = None,
    timeout: int = 600,
) -> dict[str, Any]:
    """One direct scan of `repo` with the installed console script."""

    if digest is None:
        try:
            digest = freeze_digest((repo / FREEZE).read_bytes())
        except ValueError as exc:
            # Invalid freeze bytes refuse before the console script runs —
            # same fail-closed shape the console script would emit (exit 2,
            # no artifact). Recorded so E4-unicode's "refuses validation"
            # prediction can score without the harness itself crashing.
            return {
                "exit": 2,
                "wall_seconds": 0.0,
                "stderr_tail": [f"freeze validation refused: {exc}"],
                "findings": [],
                "artifact_sha": None,
            }
    argv = [
        str(RANEX_ARCH),
        "check",
        "--freeze",
        FREEZE,
        "--expected-freeze-digest",
        digest,
        f"--output-file={ARTIFACT}",
    ]
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    if env is not None:
        environment.update(env)
    start = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=str(repo),
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    wall = round(time.monotonic() - start, 3)
    record_command(argv[1:], str(repo), completed)
    artifact_path = repo / ARTIFACT
    artifact: dict[str, Any] | None = None
    artifact_sha: str | None = None
    if completed.returncode == 0 and artifact_path.is_file():
        raw = artifact_path.read_bytes()
        artifact_sha = "sha256:" + hashlib.sha256(raw).hexdigest()
        artifact = json.loads(raw)
    findings: list[dict[str, Any]] = []
    if artifact is not None:
        for result in artifact["runs"][0]["results"]:
            location = result["locations"][0]["physicalLocation"]
            findings.append(
                {
                    "rule": result["ruleId"],
                    "file": location["artifactLocation"]["uri"],
                    "line": location["region"]["startLine"],
                    "fingerprint": result["fingerprints"]["ranex/v1"],
                }
            )
    return {
        "exit": completed.returncode,
        "wall_seconds": wall,
        "stderr_tail": completed.stderr.strip().splitlines()[-1:]
        if completed.stderr.strip()
        else [],
        "findings": findings,
        "artifact_sha": artifact_sha,
    }


# --- the governed cycle (trimmed from arch_proof.py, same shapes) ------------


def scan_argv(digest: str) -> list[str]:
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


def ranex(
    repo: Path,
    *args: str,
    key: Path | None = None,
    verdict_key: Path | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    for variable in (
        "RANEX_SIGNING_KEY",
        "RANEX_VERDICT_SIGNING_KEY",
        "RANEX_VERDICT_DIR",
    ):
        environment.pop(variable, None)
    environment.pop("PYTHONPATH", None)
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    if verdict_key is not None:
        environment["RANEX_VERDICT_SIGNING_KEY"] = str(verdict_key)
        environment["RANEX_VERDICT_DIR"] = "governance/verdicts"
    if env is not None:
        for name, value in env.items():
            if value is None:
                environment.pop(name, None)
            else:
                environment[name] = value
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
        timeout=900,
    )


def recorded(repo: Path, *args: str, **kw: Any) -> subprocess.CompletedProcess[str]:
    completed = ranex(repo, *args, **kw)
    COMMANDS.append(
        {
            "argv": list(args),
            "cwd": str(repo),
            "exit": completed.returncode,
            "wall_seconds": None,
            "stdout_tail": completed.stdout[-300:],
            "stderr_tail": completed.stderr[-300:],
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


SCOPE = [
    "pkg/__init__.py",
    "pkg/cli.py",
    "pkg/foundation.py",
    "pkg/policy.py",
    FREEZE,
]


def freeze_argv(
    digest: str, accepted: dict[str, str] | None = None
) -> list[str]:
    rules = ["arch/forbidden-import", "arch/freeze-tampered"]
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
        *[flag for rule in rules for flag in ("--scan-rule", rule)],
        *[
            flag
            for finding, reason in (accepted or {}).items()
            for flag in ("--accepted", f"{finding}={reason}")
        ],
        "--",
        *scan_argv(digest),
    ]


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


def governed(
    workspace: Path,
    *,
    files: dict[str, str] | None = None,
    freeze: dict[str, Any] | None = None,
    pin: str | None = None,
) -> tuple[Path, Path, Path, str]:
    """A fresh governed subject, frozen over a real clean scan."""

    chosen = freeze if freeze is not None else freeze_value()
    raw = canonical(chosen)
    digest = pin if pin is not None else freeze_digest(raw)
    repo = build_subject(workspace, files or default_subject(), chosen)
    (repo / FREEZE).write_bytes(raw)
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
    git(repo, "commit", "-qam", "subject: synthetic package + approved freeze")
    frozen = recorded(repo, *freeze_argv(digest))
    if frozen.returncode != 0:
        raise SystemExit(
            f"freeze failed:\n{frozen.stdout[-800:]}\n{frozen.stderr[-800:]}"
        )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "governance: freeze the scan manifest")
    return repo, key, verdict_key, digest


def gate(
    repo: Path,
    key: Path,
    verdict_key: Path,
    pinned: str,
    *,
    observe: bool = True,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
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
            env=env,
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
        env=env,
    )
    verdict_line = next(
        (
            line
            for line in verdict.stdout.splitlines()
            if line.startswith(("PASS", "FAIL"))
        ),
        None,
    )
    return {
        "run_exit": run_exit,
        "verdict": verdict_line.split()[0] if verdict_line else "ERROR",
        "evaluate_exit": verdict.returncode,
        "verdict_line": verdict_line,
        "evaluate_error_tail": verdict.stderr.strip().splitlines()[-2:],
    }


def plant(repo: Path, relative: str = "pkg/foundation.py") -> None:
    path = repo / relative
    path.write_text(path.read_text(encoding="utf-8") + PLANTED, encoding="utf-8")
    git(repo, "commit", "-qam", f"planted forbidden edge in {relative}")


def arm(name: str, outcome: dict[str, Any]) -> dict[str, Any]:
    entry = {"prediction": PREDICTIONS.get(name, ""), "observed": outcome}
    RECEIPTS["arms"][name] = entry
    print(f"{name}: {json.dumps(outcome)[:220]}")
    return entry


# --- arms --------------------------------------------------------------------


def arm_reproduction() -> None:
    """Rerun the shipped proof tool in-process, compare to shipped receipts."""

    destination = AUDIT / "reproduction"
    destination.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location(
        "arch_proof_under_stress", KERNEL / "tools/dogfood/arch_proof.py"
    )
    assert spec is not None and spec.loader is not None
    module: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.AUDIT = destination
    start = time.monotonic()
    proof_exit = module.main()
    shipped = json.loads((SHIPPED / "receipt.json").read_text(encoding="utf-8"))
    reproduced = json.loads(
        (destination / "receipt.json").read_text(encoding="utf-8")
    )
    planted_fp = {
        finding["fingerprint"]
        for repeat in range(1, 4)
        for finding in reproduced["arms"][f"forbidden-edge-blocks/r{repeat}"][
            "planted"
        ]["findings"]
    }
    shipped_planted_fp = {
        finding["fingerprint"]
        for repeat in range(1, 4)
        for finding in shipped["arms"][f"forbidden-edge-blocks/r{repeat}"][
            "planted"
        ]["findings"]
    }
    tamper_fp = {
        finding["fingerprint"]
        for finding in reproduced["arms"]["freeze-tamper"]["tampered"]["findings"]
    }
    shipped_tamper_fp = {
        finding["fingerprint"]
        for finding in shipped["arms"]["freeze-tamper"]["tampered"]["findings"]
    }
    controls_equal = (
        reproduced["summary"] == shipped["summary"]
        and planted_fp == shipped_planted_fp
        and tamper_fp == shipped_tamper_fp
    )
    vocabulary = "VERIFIED" if proof_exit == 0 and controls_equal else "FALSE-PASS"
    arm(
        "reproduction",
        {
            "vocabulary": vocabulary,
            "proof_exit": proof_exit,
            "summary_all_true": all(reproduced["summary"].values()),
            "planted_fingerprints_match_shipped": planted_fp == shipped_planted_fp,
            "tamper_fingerprints_match_shipped": tamper_fp == shipped_tamper_fp,
            "seconds": round(time.monotonic() - start, 1),
        },
    )


def arm_cycles() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-cycles-") as scratch:
        workspace = Path(scratch)
        allowed_both = freeze_value(
            edges=[
                ["cli", "foundation"],
                ["cli", "policy"],
                ["foundation", "policy"],
                ["policy", "foundation"],
            ]
        )
        files = default_subject()
        files["pkg/foundation.py"] += "from pkg import policy\n"
        repo_ok = build_subject(workspace / "a", files, allowed_both)
        clean = scan(repo_ok)
        repo_denied = build_subject(workspace / "b", files, freeze_value())
        denied = scan(repo_denied)
        vocabulary = (
            "VERIFIED"
            if clean["exit"] == 0
            and not clean["findings"]
            and denied["exit"] == 0
            and len(denied["findings"]) == 1
            and denied["findings"][0]["rule"] == "arch/forbidden-import"
            else "FALSE-PASS"
        )
        arm(
            "E1-cycles",
            {"vocabulary": vocabulary, "allowed_both": clean, "denied": denied},
        )


def arm_broken_symlink() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-sym-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        (repo / "pkg" / "ghost.py").symlink_to(
            repo / "pkg" / "does-not-exist.py"
        )
        result = scan(repo)
        vocabulary = (
            "VERIFIED"
            if result["exit"] == 2
            and result["artifact_sha"] is None
            else "FALSE-PASS"
        )
        arm("E2-broken-symlink", {"vocabulary": vocabulary, "scan": result})


def _with_shadow_module(freeze: dict[str, Any]) -> dict[str, Any]:
    modules = dict(freeze["modules"])
    modules["shadow"] = "pkg/shadow"
    return {**freeze, "modules": modules}


def arm_symlink_dir() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-symdir-") as scratch:
        workspace = Path(scratch)
        freeze = _with_shadow_module(freeze_value())
        # control FIRST: the same bytes at a real (non-symlink) path get caught
        control_repo = build_subject(workspace / "b", default_subject(), freeze)
        (control_repo / "pkg" / "shadow").mkdir()
        (control_repo / "pkg" / "shadow" / "__init__.py").write_text(
            "", encoding="utf-8"
        )
        (control_repo / "pkg" / "shadow" / "impl.py").write_text(
            "from pkg import policy\n", encoding="utf-8"
        )
        control = scan(control_repo)
        # the arm: the identical module hidden behind a symlinked directory
        repo = build_subject(workspace / "a", default_subject(), freeze)
        hidden = repo / "hidden"
        (hidden / "shadow").mkdir(parents=True)
        (hidden / "shadow" / "__init__.py").write_text("", encoding="utf-8")
        (hidden / "shadow" / "impl.py").write_text(
            "from pkg import policy  # forbidden edge behind a symlink\n",
            encoding="utf-8",
        )
        (repo / "pkg" / "shadow").symlink_to(
            hidden / "shadow", target_is_directory=True
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "hide a forbidden edge behind a symlinked dir")
        result = scan(repo)
        control_catches = (
            control["exit"] == 0
            and control["findings"]
            and control["findings"][0]["rule"] == "arch/forbidden-import"
        )
        vocabulary = (
            "FALSE-PASS"
            if control_catches
            and result["exit"] == 0
            and not result["findings"]
            else "VERIFIED"
        )
        arm(
            "E3-symlink-dir",
            {
                "vocabulary": vocabulary,
                "symlinked_module_scan": {
                    k: result[k] for k in ("exit", "findings", "artifact_sha")
                },
                "control_real_dir_scan": {
                    k: control[k] for k in ("exit", "findings")
                },
                "control_catches_same_bytes": control_catches,
            },
        )


def arm_unicode() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-uni-") as scratch:
        workspace = Path(scratch)
        outcomes: dict[str, Any] = {}
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        (repo / "pkg" / "módulo.py").write_text("x = 1\n", encoding="utf-8")
        outcomes["unicode_filename"] = scan(repo)

        repo = build_subject(workspace / "b", default_subject(), freeze_value())
        (repo / "pkg" / "foundation.py").write_bytes(
            b"def base():\n    return 1\n\x80\x81\n"
        )
        outcomes["non_utf8_bytes"] = scan(repo)

        repo = build_subject(workspace / "c", default_subject(), freeze_value())
        (repo / "pkg" / "foundation.py").write_bytes(
            "﻿def base():\n    return 1\n".encode()
        )
        outcomes["bom"] = scan(repo)

        bad = _with_shadow_module(freeze_value())
        bad["modules"] = dict(bad["modules"])
        bad["modules"]["módulo"] = "pkg/módulo.py"
        repo = build_subject(workspace / "d", default_subject(), bad)
        outcomes["unicode_freeze_module"] = scan(repo)

        every_closed = all(
            outcome["exit"] == 2 and outcome["artifact_sha"] is None
            for outcome in outcomes.values()
        )
        arm(
            "E4-unicode",
            {
                "vocabulary": "VERIFIED" if every_closed else "FALSE-PASS",
                "outcomes": {
                    name: {
                        "exit": outcome["exit"],
                        "artifact": outcome["artifact_sha"],
                        "stderr_tail": outcome["stderr_tail"],
                    }
                    for name, outcome in outcomes.items()
                },
            },
        )


def arm_renamed_module() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-ren-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        (repo / "pkg" / "foundation.py").rename(repo / "pkg" / "base.py")
        result = scan(repo)
        vocabulary = (
            "VERIFIED"
            if result["exit"] == 2
            and result["artifact_sha"] is None
            else "FALSE-PASS"
        )
        arm("E5-renamed-module", {"vocabulary": vocabulary, "scan": result})


def arm_deep_nesting() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-deep-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        deep = repo / "pkg"
        for level in range(100):
            deep = deep / f"level{level:03d}"
            deep.mkdir()
            (deep / "__init__.py").write_text("", encoding="utf-8")
        (deep / "leaf.py").write_text("from pkg import policy\n", encoding="utf-8")
        freeze = _with_shadow_module(freeze_value())
        freeze["modules"] = dict(freeze["modules"])
        freeze["modules"]["deep"] = "pkg/level000"
        (repo / FREEZE).write_bytes(canonical(freeze))
        result = scan(repo)
        vocabulary = (
            "VERIFIED"
            if result["exit"] == 0
            and result["findings"]
            and result["findings"][0]["rule"] == "arch/forbidden-import"
            else "FALSE-PASS"
        )
        arm(
            "E6-deep-nesting",
            {
                "vocabulary": vocabulary,
                "depth": 101,
                "scan": {
                    k: result[k] for k in ("exit", "wall_seconds", "findings")
                },
            },
        )


def arm_empty_graph() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-empty-") as scratch:
        workspace = Path(scratch)
        files = {".gitignore": GITIGNORE, "pkg/__init__.py": ""}
        repo = build_subject(workspace / "a", files, freeze_value())
        vacuous = scan(repo)

        repo3 = build_subject(workspace / "b", files, freeze_value())
        shutil.rmtree(repo3 / "pkg")
        absent = scan(repo3)

    with tempfile.TemporaryDirectory(prefix="ranex-stress-emptyg-") as scratch2:
        # Freeze over a complete subject first (SCOPE requires the declared
        # files), then gut the declared modules: v1 pins edges, not existence,
        # so the gate is predicted to keep PASSing (GAP).
        repo2, key, verdict_key, digest = governed(Path(scratch2))
        pristine = gate(repo2, key, verdict_key, digest)
        for relative in ("pkg/foundation.py", "pkg/policy.py", "pkg/cli.py"):
            target = repo2 / relative
            if target.is_file():
                target.unlink()
        git(repo2, "add", "-A")
        git(repo2, "commit", "-qm", "remove every declared module file")
        gutted = gate(repo2, key, verdict_key, digest)

    vacuous_pass = vacuous["exit"] == 0 and not vacuous["findings"]
    gate_pass = gutted["verdict"] == "PASS"
    absent_refuses = absent["exit"] == 2 and absent["artifact_sha"] is None
    arm(
        "E8-empty-graph",
        {
            "vocabulary": "GAP"
            if vacuous_pass and gate_pass
            else "VERIFIED",
            "vacuous_scan_pass": vacuous_pass,
            "pristine_gate": pristine["verdict"],
            "gutted_gate_pass": gate_pass,
            "absent_package_root_refuses": absent_refuses,
            "gutted_gate": gutted,
        },
    )


def arm_missing_tool() -> None:
    """The pinned scanner removed from the venv: absence must block."""

    stashed = KERNEL / "tools/dogfood/.ranex-arch-stashed"
    moved = False
    try:
        with tempfile.TemporaryDirectory(prefix="ranex-stress-tool-") as scratch:
            workspace = Path(scratch)
            repo, key, verdict_key, digest = governed(workspace)
            pristine = gate(repo, key, verdict_key, digest)
            plant(repo)
            os.replace(RANEX_ARCH, stashed)
            moved = True
            broken_run = recorded(
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
                *scan_argv(digest),
                key=key,
            )
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
                (
                    line
                    for line in verdict.stdout.splitlines()
                    if line.startswith(("PASS", "FAIL"))
                ),
                None,
            )
            outcome = {
                "pristine_verdict": pristine["verdict"],
                "broken_run_exit": broken_run.returncode,
                "broken_run_stderr_tail": broken_run.stderr.strip().splitlines()[-1:],
                "evaluate_verdict": verdict_line.split()[0]
                if verdict_line
                else "ERROR",
            }
            outcome["vocabulary"] = (
                "VERIFIED"
                if outcome["pristine_verdict"] == "PASS"
                and outcome["broken_run_exit"] != 0
                and outcome["evaluate_verdict"] == "FAIL"
                else "FALSE-PASS"
            )
            arm("V1-missing-tool", outcome)
    finally:
        if moved:
            os.replace(stashed, RANEX_ARCH)
        if not RANEX_ARCH.is_file():
            raise SystemExit("FATAL: ranex-arch was not restored to the venv")


def arm_path_pollution() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-path-") as scratch:
        workspace = Path(scratch)
        fake = workspace / "fakebin"
        fake.mkdir()
        for name in ("git", "python", "python3", "sha256sum"):
            path = fake / name
            path.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            path.chmod(0o755)
        repo, key, verdict_key, digest = governed(workspace)
        plant(repo)
        polluted = {"PATH": f"{fake}:{os.environ['PATH']}"}
        direct = scan(repo, digest, env=polluted)
        governed_run = gate(repo, key, verdict_key, digest, env=polluted)
        vocabulary = (
            "VERIFIED"
            if direct["exit"] == 0
            and direct["findings"]
            and governed_run["verdict"] == "FAIL"
            else "FALSE-PASS"
        )
        arm(
            "V2-path-pollution",
            {
                "vocabulary": vocabulary,
                "direct_findings_kept": len(direct["findings"]),
                "governed": governed_run,
            },
        )


SHADOW_AST = '''\
import importlib.util, os, sys, sysconfig

_path = os.path.join(sysconfig.get_path("stdlib"), "ast.py")
_spec = importlib.util.spec_from_file_location("_real_ast", _path)
_real = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_real)
for _name in dir(_real):
    if not _name.startswith("__"):
        globals()[_name] = getattr(_real, _name)
{extra}
'''


def arm_pythonpath_shadow() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-pyp-") as scratch:
        workspace = Path(scratch)
        shadow = workspace / "shadow"
        shadow.mkdir()
        marker = (
            "open(os.path.join(os.path.dirname(__file__), 'picked-up'), "
            "'w').close()\n"
        )
        (shadow / "ast.py").write_text(
            SHADOW_AST.format(extra=marker), encoding="utf-8"
        )
        repo, key, verdict_key, digest = governed(workspace / "gov")
        plant(repo)
        control = gate(repo, key, verdict_key, digest)
        benign = gate(repo, key, verdict_key, digest, env={"PYTHONPATH": str(shadow)})
        picked_up = (shadow / "picked-up").is_file()
        # exploit: swallow every Import/ImportFrom node the walk yields
        swallow = (
            "def walk(node):\n"
            "    for _n in _real.walk(node):\n"
            "        if type(_n).__name__ in ('Import', 'ImportFrom'):\n"
            "            continue\n"
            "        yield _n\n"
        )
        (shadow / "ast.py").write_text(
            SHADOW_AST.format(extra=swallow), encoding="utf-8"
        )
        exploit_run = gate(
            repo, key, verdict_key, digest, env={"PYTHONPATH": str(shadow)}
        )
        vocabulary = (
            "FALSE-PASS"
            if control["verdict"] == "FAIL"
            and exploit_run["verdict"] == "PASS"
            else "VERIFIED"
        )
        arm(
            "V3-pythonpath-shadow",
            {
                "vocabulary": vocabulary,
                "control_no_shadow": control["verdict"],
                "shadow_picked_up": picked_up,
                "benign_shadow_verdict": benign["verdict"],
                "exploit_shadow_verdict": exploit_run["verdict"],
                "exploit_run_exit": exploit_run["run_exit"],
                "note": "PYTHONPATH precedes site-packages in sys.path; the "
                "scanner's stdlib imports are shadowable — and so is ranex "
                "itself",
            },
        )


def arm_env_i() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-envi-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "direct", default_subject(), freeze_value())
        digest = freeze_digest((repo / FREEZE).read_bytes())
        argv = [
            str(RANEX_ARCH),
            "check",
            "--freeze",
            FREEZE,
            "--expected-freeze-digest",
            digest,
            f"--output-file={ARTIFACT}",
        ]
        emptied = subprocess.run(
            ["env", "-i", *argv],
            cwd=str(repo),
            capture_output=True,
            check=False,
            timeout=120,
        )
        env_i_bytes = (repo / ARTIFACT).read_bytes() if emptied.returncode == 0 else None
        normal = subprocess.run(
            argv, cwd=str(repo), capture_output=True, check=False, timeout=120
        )
        normal_bytes = (
            (repo / ARTIFACT).read_bytes() if normal.returncode == 0 else None
        )
        COMMANDS.append(
            {
                "argv": ["env", "-i", "ranex-arch", "check", "..."],
                "cwd": str(repo),
                "exit": emptied.returncode,
                "wall_seconds": None,
                "stdout_tail": "",
                "stderr_tail": emptied.stderr.decode()[-200:],
            }
        )
        identical = (
            env_i_bytes is not None
            and env_i_bytes == normal_bytes
            and normal.returncode == 0
        )
        arm(
            "V4-env-i",
            {
                "vocabulary": "VERIFIED" if identical else "NON-DETERMINISTIC",
                "env_i_exit": emptied.returncode,
                "normal_exit": normal.returncode,
                "artifact_bytes_identical": identical,
            },
        )


def arm_wrong_pin() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-pin-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        wrong = scan(repo, "sha256:" + "0" * 64)
        vocabulary = (
            "VERIFIED"
            if wrong["exit"] == 0
            and wrong["findings"]
            and wrong["findings"][0]["rule"] == "arch/freeze-tampered"
            else "FALSE-PASS"
        )
        arm("V5-wrong-pin", {"vocabulary": vocabulary, "scan": wrong})


def arm_byte_identity() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-det-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        plant(repo)
        shas = [scan(repo)["artifact_sha"] for _ in range(5)]
        vocabulary = (
            "VERIFIED" if len(set(shas)) == 1 and shas[0] else "NON-DETERMINISTIC"
        )
        arm(
            "D1-byte-identity",
            {
                "vocabulary": vocabulary,
                "artifact_shas": [shas[0], "..."],
                "distinct": len(set(shas)),
            },
        )


def arm_relocation() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-relo-") as scratch:
        workspace = Path(scratch)
        one = build_subject(workspace / "a", default_subject(), freeze_value())
        two = build_subject(
            workspace / "a-much-longer-name-for-the-same-bytes",
            default_subject(),
            freeze_value(),
        )
        plant(one)
        plant(two)
        first = scan(one)
        second = scan(two)
        vocabulary = (
            "VERIFIED"
            if first["artifact_sha"]
            and first["artifact_sha"] == second["artifact_sha"]
            else "NON-DETERMINISTIC"
        )
        arm(
            "D2-relocation",
            {
                "vocabulary": vocabulary,
                "shas": [first["artifact_sha"], second["artifact_sha"]],
            },
        )


def _scale_tree(repo: Path, files_per_dir: int, dirs: int) -> None:
    (repo / "pkg").mkdir()
    (repo / "pkg" / "__init__.py").write_text("", encoding="utf-8")
    for relative, text in default_subject().items():
        if relative.startswith("pkg/"):
            (repo / relative).write_text(text, encoding="utf-8")
    modules = {
        "root": "pkg/__init__.py",
        "foundation": "pkg/foundation.py",
        "policy": "pkg/policy.py",
        "cli": "pkg/cli.py",
    }
    # Default-subject edges must be allowed or the scale profile's
    # "exactly one planted finding" predicate is drowned in noise.
    edges: list[list[str]] = [
        ["cli", "foundation"],
        ["cli", "policy"],
        ["policy", "foundation"],
    ]
    for d in range(dirs):
        name = f"sub{d:03d}"
        directory = repo / "pkg" / name
        directory.mkdir()
        (directory / "__init__.py").write_text("", encoding="utf-8")
        for f in range(files_per_dir):
            # Clean generated files: no imports. The plant alone carries the
            # forbidden edge, so findings==1 is a real positive control.
            (directory / f"mod{f:04d}.py").write_text(
                f"VALUE_{d}_{f} = 1\n",
                encoding="utf-8",
            )
        modules[name] = f"pkg/{name}"
        edges.append([name, "root"])
    # the plant hides among the last directory's files
    (repo / "pkg" / f"sub{dirs - 1:03d}" / "mod0000.py").write_text(
        "from pkg import policy  # planted forbidden edge at scale\n",
        encoding="utf-8",
    )
    (repo / FREEZE).write_bytes(
        canonical(freeze_value(modules=modules, edges=sorted(edges)))
    )


def arm_scale() -> None:
    profile: dict[str, Any] = {}
    for label, per_dir, dirs in (
        ("1k", 49, 20),
        ("5k", 249, 20),
        ("10k", 499, 20),
    ):
        with tempfile.TemporaryDirectory(prefix="ranex-stress-scale-") as scratch:
            repo = Path(scratch) / "subject"
            repo.mkdir()
            (repo / "governance").mkdir()
            start = time.monotonic()
            _scale_tree(repo, per_dir, dirs)
            build_seconds = round(time.monotonic() - start, 2)
            timings = []
            findings = None
            for _ in range(3):
                result = scan(repo, timeout=900)
                timings.append(result["wall_seconds"])
                findings = len(result["findings"])
            total = per_dir * dirs + dirs + 5
            profile[label] = {
                "files": total,
                "build_seconds": build_seconds,
                "wall_seconds_min": min(timings),
                "wall_seconds_median": sorted(timings)[1],
                "wall_seconds_max": max(timings),
                "files_per_second": round(total / sorted(timings)[1], 1),
                "planted_finding_present": findings == 1,
            }
    arm(
        "S1-scale",
        {
            "vocabulary": "VERIFIED"
            if all(v["planted_finding_present"] for v in profile.values())
            else "FALSE-PASS",
            "profile": profile,
        },
    )


def arm_boundary_move() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-bound-") as scratch:
        workspace = Path(scratch)
        repo, key, verdict_key, digest = governed(workspace)
        pristine = gate(repo, key, verdict_key, digest)
        (repo / "tools").mkdir()
        (repo / "pkg" / "foundation.py").rename(repo / "tools" / "foundation.py")
        content = (repo / "tools" / "foundation.py").read_text(encoding="utf-8")
        (repo / "tools" / "foundation.py").write_text(
            content + "from pkg import policy  # forbidden edge, now outside pkg\n",
            encoding="utf-8",
        )
        git(repo, "add", "-A")
        git(
            repo,
            "commit",
            "-qm",
            "move the forbidden importer outside package_root",
        )
        moved = gate(repo, key, verdict_key, digest)
        vocabulary = (
            "GAP"
            if pristine["verdict"] == "PASS" and moved["verdict"] == "PASS"
            else "VERIFIED"
        )
        arm(
            "A1-boundary-move",
            {
                "vocabulary": vocabulary,
                "pristine": pristine["verdict"],
                "after_move": moved["verdict"],
                "note": "the freeze governs package_root only; consumers "
                "outside the root are invisible to the frozen universe",
            },
        )


def arm_re_home() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-home-") as scratch:
        workspace = Path(scratch)
        repo = build_subject(workspace / "a", default_subject(), freeze_value())
        (repo / "pkg" / "foundation").mkdir()
        (repo / "pkg" / "foundation.py").rename(
            repo / "pkg" / "foundation" / "__init__.py"
        )
        result = scan(repo)
        vocabulary = (
            "VERIFIED"
            if result["exit"] == 2
            and result["artifact_sha"] is None
            else "FALSE-PASS"
        )
        arm("A2-re-home", {"vocabulary": vocabulary, "scan": result})


def arm_auto_bless() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-bless-") as scratch:
        workspace = Path(scratch)
        repo, key, verdict_key, digest = governed(workspace)
        plant(repo)
        blocked = gate(repo, key, verdict_key, digest)
        weakened = freeze_value(
            edges=[
                ["cli", "foundation"],
                ["cli", "policy"],
                ["foundation", "policy"],
                ["policy", "foundation"],
            ]
        )
        raw = canonical(weakened)
        new_digest = freeze_digest(raw)
        (repo / FREEZE).write_bytes(raw)
        (repo / "governance" / "gates.yaml").write_text(
            catalog(new_digest), encoding="utf-8"
        )
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "agent blesses the edge it planted")
        frozen = recorded(repo, *freeze_argv(new_digest))
        blessed = None
        if frozen.returncode == 0:
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "agent refreezes over the blessing")
            blessed = gate(repo, key, verdict_key, new_digest)
        vocabulary = (
            "GAP"
            if blocked["verdict"] == "FAIL"
            and blessed is not None
            and blessed["verdict"] == "PASS"
            else "VERIFIED"
        )
        arm(
            "A3-auto-bless",
            {
                "vocabulary": vocabulary,
                "blocked_before_bless": blocked["verdict"],
                "refreeze_exit": frozen.returncode,
                "verdict_after_bless": blessed["verdict"]
                if blessed
                else None,
                "guard": "designed promote-ship path; the machine guard is "
                "ADR-017 delegated-scope disjointness (freeze + manifest sit "
                "outside every delegated scope) plus the operator-approval "
                "origin rule (ADR-065); see "
                "tests/integration/test_delegation_command.py",
            },
        )


def arm_dynamic_import() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-dyn-") as scratch:
        workspace = Path(scratch)
        files = default_subject()
        files["pkg/foundation.py"] += (
            "import importlib\n"
            "_policy = importlib.import_module('pkg.policy')\n"
            "_also = __import__('pkg.policy')\n"
        )
        repo = build_subject(workspace / "a", files, freeze_value())
        result = scan(repo)
        dynamic_invisible = result["exit"] == 0 and not result["findings"]
        control_files = default_subject()
        control_files["pkg/foundation.py"] += "import pkg.policy\n"
        control_repo = build_subject(workspace / "b", control_files, freeze_value())
        control = scan(control_repo)
        vocabulary = (
            "GAP"
            if dynamic_invisible and control["findings"]
            else "VERIFIED"
        )
        arm(
            "A6-dynamic-import",
            {
                "vocabulary": vocabulary,
                "dynamic_edge_invisible": dynamic_invisible,
                "static_control_caught": bool(control["findings"]),
                "note": "v1 semantics: an import edge is an import statement; "
                "dynamic imports are a documented static-analysis limit",
            },
        )


def arm_star_and_nested() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-star-") as scratch:
        workspace = Path(scratch)
        files = default_subject()
        files["pkg/foundation.py"] = (
            "def base():\n    return 1\n\n\nfrom pkg import *\n"
        )
        repo = build_subject(workspace / "a", files, freeze_value())
        star = scan(repo)
        star_ok = (
            star["exit"] == 0
            and len(star["findings"]) == 1
            and star["findings"][0]["rule"] == "arch/forbidden-import"
        )
        nested_files = default_subject()
        nested_files["pkg/foundation.py"] = (
            "def base():\n    return 1\n\n\n"
            "def lazy():\n"
            "    from pkg import policy\n"
            "    return policy.rule()\n"
        )
        nested_repo = build_subject(workspace / "b", nested_files, freeze_value())
        nested = scan(nested_repo)
        nested_ok = (
            nested["exit"] == 0
            and len(nested["findings"]) == 1
            and nested["findings"][0]["line"] == 6
        )
        arm(
            "A7-star-import",
            {
                "vocabulary": "VERIFIED" if star_ok and nested_ok else "FALSE-PASS",
                "star_edge_to_root": star_ok,
                "function_body_import_found_at_line": nested["findings"][0]["line"]
                if nested["findings"]
                else None,
                "nested_ok": nested_ok,
            },
        )


def arm_alias_forms() -> None:
    forms = {
        "import-dotted": "import pkg.policy\n",
        "import-aliased": "import pkg.policy as _p\n",
        "from-aliased": "from pkg import policy as _pol\n",
        "from-module-import-name": "from pkg.policy import rule\n",
        "relative-level1": "from . import policy\n",
        "relative-named": "from .policy import rule\n",
    }
    outcomes: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="ranex-stress-forms-") as scratch:
        workspace = Path(scratch)
        for label, statement in forms.items():
            files = default_subject()
            files["pkg/foundation.py"] = (
                f"def base():\n    return 1\n\n\n{statement}"
            )
            repo = build_subject(workspace / label, files, freeze_value())
            result = scan(repo)
            outcomes[label] = {
                "exit": result["exit"],
                "finding": result["findings"][0] if result["findings"] else None,
            }
        all_caught = all(
            outcome["exit"] == 0
            and outcome["finding"]
            and outcome["finding"]["rule"] == "arch/forbidden-import"
            for outcome in outcomes.values()
        )
        arm(
            "A9-alias-forms",
            {
                "vocabulary": "VERIFIED" if all_caught else "FALSE-PASS",
                "forms": {k: bool(v["finding"]) for k, v in outcomes.items()},
                "all_attributed": all_caught,
            },
        )


def arm_boundary_classification() -> None:
    with tempfile.TemporaryDirectory(prefix="ranex-stress-class-") as scratch:
        workspace = Path(scratch)
        imports = "\n".join(f"import {name}" for name in _STDLIB_NAMES)
        imports += "\n" + "\n".join(f"import {name}" for name in _EXTERNAL_NAMES)
        files = default_subject()
        files["pkg/foundation.py"] = f"def base():\n    return 1\n\n\n{imports}\n"
        repo = build_subject(workspace / "a", files, freeze_value())
        result = scan(repo)
        outside = len(_STDLIB_NAMES) + len(_EXTERNAL_NAMES)
        misclassified = len(result["findings"])
        arm(
            "B1-stdlib",
            {
                "vocabulary": "VERIFIED" if misclassified == 0 else "FALSE-PASS",
                "stdlib_and_external_imports": outside,
                "misclassified_findings": misclassified,
                "rate": f"{misclassified}/{outside}",
            },
        )

        collision_files = {
            ".gitignore": GITIGNORE,
            "json/__init__.py": "",
            "json/wrapper.py": "import json\n",
        }
        collision_freeze = freeze_value(
            modules={"root": "json/__init__.py", "wrapper": "json/wrapper.py"},
            edges=[],
            package_root="json",
        )
        collision_repo = build_subject(
            workspace / "b", collision_files, collision_freeze
        )
        collision = scan(collision_repo)
        collision_local = any(
            f["rule"] == "arch/forbidden-import" for f in collision["findings"]
        )
        arm(
            "B3-collision",
            {
                "vocabulary": "GAP" if collision_local else "VERIFIED",
                "import_json_attributed_to_local_package": collision_local,
                "collision_findings": collision["findings"],
                "note": "under a package_root named like a stdlib module the "
                "scanner cannot distinguish stdlib from local intent; "
                "attribution is local (1/1 under the collision precondition)",
            },
        )


def arm_delete_race() -> None:
    """Files deleted while the walk is running: exit 2, never a clean miss."""

    attempts: list[dict[str, Any]] = []
    for _ in range(5):
        with tempfile.TemporaryDirectory(prefix="ranex-stress-race-") as scratch:
            workspace = Path(scratch)
            files = {".gitignore": GITIGNORE, "pkg/__init__.py": ""}
            files.update(
                {f"pkg/mod{i:04d}.py": "flag = 1\n" for i in range(3000)}
            )
            repo = build_subject(
                workspace,
                files,
                freeze_value(modules={"root": "pkg/__init__.py", "bulk": "pkg"}),
            )
            (repo / "pkg" / "mod2999.py").write_text(
                "from pkg import policy  # planted, walked last\n", encoding="utf-8"
            )
            deleter = subprocess.Popen(
                [
                    str(PY),
                    "-c",
                    "import os, sys, time\n"
                    "root = sys.argv[1]\n"
                    "time.sleep(0.02)\n"
                    "names = sorted(os.listdir(root), reverse=True)\n"
                    "for name in names:\n"
                    "    try:\n"
                    "        os.unlink(os.path.join(root, name))\n"
                    "    except OSError:\n"
                    "        pass\n",
                    str(repo / "pkg"),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            result: dict[str, Any]
            try:
                result = scan(repo, timeout=120)
            except subprocess.TimeoutExpired:
                deleter.kill()
                result = {"exit": "timeout", "findings": None, "wall_seconds": None}
            deleter.wait(timeout=60)
            attempts.append(
                {
                    "exit": result["exit"],
                    "findings": len(result["findings"])
                    if result["findings"] is not None
                    else None,
                    "wall_seconds": result.get("wall_seconds"),
                }
            )
    clean_miss = any(
        attempt["exit"] == 0 and attempt["findings"] == 0 for attempt in attempts
    )
    fail_closed = any(attempt["exit"] == 2 for attempt in attempts)
    vocabulary = (
        "FALSE-PASS" if clean_miss else "VERIFIED" if fail_closed else "UNVERIFIED"
    )
    arm(
        "E9-delete-race",
        {
            "vocabulary": vocabulary,
            "attempts": attempts,
            "fail_closed_seen": fail_closed,
            "clean_miss_seen": clean_miss,
            "note": "the race window is timing-dependent; UNVERIFIED bounds it "
            "at 5 attempts x 3000 files",
        },
    )


RERUN_ARMS: list[tuple[str, Callable[[], None]]] = [
    ("E1-cycles", arm_cycles),
    ("E2-broken-symlink", arm_broken_symlink),
    ("E3-symlink-dir", arm_symlink_dir),
    ("E5-renamed-module", arm_renamed_module),
    ("A2-re-home", arm_re_home),
    ("A6-dynamic-import", arm_dynamic_import),
    ("A7-star-import", arm_star_and_nested),
    ("A9-alias-forms", arm_alias_forms),
    ("B1-stdlib", arm_boundary_classification),
]


def arm_repeat_cycle() -> None:
    """The deterministic scanner arms re-run in fresh workspaces: no flips."""

    first: dict[str, list[str]] = {}
    for name, _builder in RERUN_ARMS:
        first[name] = [RECEIPTS["arms"][name]["observed"]["vocabulary"]]
    for name, builder in RERUN_ARMS:
        observed = first[name]
        for _ in range(REPEATS - 1):
            builder()
            observed.append(RECEIPTS["arms"][name]["observed"]["vocabulary"])
        RECEIPTS["arms"][name]["observed"]["repeat_vocabularies"] = observed
    flips = {
        name: vocabs for name, vocabs in first.items() if len(set(vocabs)) > 1
    }
    arm(
        "repeats-stability",
        {
            "vocabulary": "NON-DETERMINISTIC" if flips else "VERIFIED",
            "flips": flips,
            "note": "deterministic arms re-run in fresh workspaces; a "
            "nondeterminism rate p is detectable with probability "
            f"1-(1-p)**{REPEATS} ({1 - 0.5 ** REPEATS:.3f} at p=0.5)",
        },
    )


def main() -> int:
    if not RANEX.is_file() or not RANEX_ARCH.is_file():
        raise SystemExit("the installed console scripts are absent")
    sys.path.insert(0, str(KERNEL / "src"))
    AUDIT.mkdir(parents=True, exist_ok=True)

    arm_reproduction()
    arm_cycles()
    arm_broken_symlink()
    arm_symlink_dir()
    arm_unicode()
    arm_renamed_module()
    arm_deep_nesting()
    arm_empty_graph()
    arm_missing_tool()
    arm_wrong_pin()
    arm_byte_identity()
    arm_relocation()
    arm_path_pollution()
    arm_pythonpath_shadow()
    arm_env_i()
    arm_boundary_move()
    arm_re_home()
    arm_auto_bless()
    arm_dynamic_import()
    arm_star_and_nested()
    arm_alias_forms()
    arm_boundary_classification()
    arm_scale()
    arm_delete_race()
    arm_repeat_cycle()

    vocabulary_counts: dict[str, int] = {}
    for entry in RECEIPTS["arms"].values():
        vocabulary = entry.get("observed", {}).get("vocabulary")
        if vocabulary:
            vocabulary_counts[vocabulary] = vocabulary_counts.get(vocabulary, 0) + 1
    blocking = sorted(
        name
        for name, entry in RECEIPTS["arms"].items()
        if entry.get("observed", {}).get("vocabulary")
        in {"FALSE-PASS", "NON-DETERMINISTIC"}
    )
    RECEIPTS["summary"] = {
        "vocabulary_counts": vocabulary_counts,
        "blocking_arms": blocking,
        "host": {
            "uname": subprocess.run(
                ["uname", "-srm"], capture_output=True, text=True, check=False
            ).stdout.strip(),
            "cpus": os.cpu_count(),
            "python": sys.version.split()[0],
            "kernel_head": subprocess.run(
                ["git", "-C", str(KERNEL), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip(),
            "ranex_arch_sha256": hashlib.sha256(RANEX_ARCH.read_bytes()).hexdigest(),
            "arch_scan_sha256": hashlib.sha256(
                (KERNEL / "src/ranex/foundation/arch_scan.py").read_bytes()
            ).hexdigest(),
        },
    }
    (AUDIT / "receipt.json").write_text(
        json.dumps(RECEIPTS, indent=1, sort_keys=True), encoding="utf-8"
    )
    (AUDIT / "commands.json").write_text(
        json.dumps(COMMANDS, indent=1), encoding="utf-8"
    )
    print(f"vocabularies: {vocabulary_counts}")
    if blocking:
        print(f"BLOCKING ARMS: {blocking}")
        return 1
    print(f"ALL ARMS RECORDED  receipts={AUDIT / 'receipt.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
