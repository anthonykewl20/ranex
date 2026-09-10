#!/usr/bin/env python3
"""#97 field proof — a real scanner decides a real gate, at operator level.

Everything here is the real thing: the installed `ranex` console script, a real
clone of `benjaminp/six` at a pinned commit, real ruff, a real Ed25519 producer
key, a real journal, and real Git history. No mock, no fake, no monkeypatched
seam, and no assertion about behaviour that was not executed in the run.

Each expectation is a **control pair** (`calibration.py`, #95): a positive that
must hold and a negative that must be refused, each repeated on identical input.
A green arm on its own proves only that nothing objected — so every arm here
carries the failure it exists to catch, and an arm without one is recorded GAP
rather than counted.

    uv run --frozen python tools/dogfood/sarif_proof.py

Writes `tools/dogfood/audits/<date>-sarif-reporter/sarif.json` and exits
nonzero if any control is not VERIFIED.
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOL_DIR.parents[1]
sys.path.insert(0, str(TOOL_DIR))

from calibration import Calibration, Control, Observation, Status  # noqa: E402

RANEX = REPO_ROOT / ".venv" / "bin" / "ranex"
SIX_URL = "https://github.com/benjaminp/six"
SIX_REV = "c8e394065cd541a16c040515dc0afb85cf22a7c3"
SCOPE = "six.py"
PRODUCER = "sarif-proof-producer"
SIGNER = "kernel-verdict-signer"
APPROVER = "sarif-proof-approver"
ARTIFACT = "governance/scan.sarif"
MANIFEST = "governance/scan-manifest.json"
VIOLATION = "import os  # a real unused import, added on a scratch commit\n"

#: A producer that emits a supplied SARIF under a scanner's argv shape. It is
#: how a hostile report is measured without pretending ruff would produce one.
FORGER = (
    "import sys\n"
    "out = [a for a in sys.argv if a.startswith('--output-file=')][0].split('=', 1)[1]\n"
    "open(out, 'w').write(open('forged.json').read())\n"
)


def ruff() -> str:
    found = shutil.which("ruff")
    if found is None:
        raise SystemExit("no ruff on PATH: this proof needs a real scanner")
    return found


def scan_argv(binary: str | None = None) -> list[str]:
    return [binary or ruff(), "check", "--no-cache", "--isolated", "--select=F401",
            "--output-format=sarif", f"--output-file={ARTIFACT}", SCOPE]


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=sarif-proof@ranex.invalid",
         "-c", "user.name=ranex-sarif-proof", *args],
        capture_output=True, text=True, check=False,
    )


def ranex(repo: Path, *args: str, key: Path | None = None, verdict_key: Path | None = None,
          timeout: int = 600) -> subprocess.CompletedProcess[str]:
    """The installed console script, anchored to an external checkout (ADR-052)."""

    environment = dict(os.environ)
    for variable in ("RANEX_SIGNING_KEY", "RANEX_VERDICT_SIGNING_KEY", "RANEX_VERDICT_DIR"):
        environment.pop(variable, None)
    if key is not None:
        environment["RANEX_SIGNING_KEY"] = str(key)
    if verdict_key is not None:
        environment["RANEX_VERDICT_SIGNING_KEY"] = str(verdict_key)
        environment["RANEX_VERDICT_DIR"] = "governance/verdicts"
    return subprocess.run(
        [str(RANEX), *args, "--external-repository", str(repo)],
        cwd=str(repo), env=environment, capture_output=True, text=True,
        check=False, timeout=timeout,
    )


def catalog(command: list[str]) -> str:
    return (
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: SCAN_CLEAN\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: scan\n"
        f"        command: {json.dumps(command)}\n"
        f"        results_artifact: {ARTIFACT}\n"
        "        results_reporter: sarif-2.1.0\n"
        f"        results_manifest: {MANIFEST}\n"
    )


def minted(repo: Path, identity: str, key: Path) -> str:
    """A real Ed25519 key, minted by the installed CLI, outside the repository."""

    keygen = ranex(repo, "keygen", "--producer", identity, key=key)
    if keygen.returncode != 0 or not key.is_file():
        raise SystemExit(f"keygen failed: {keygen.stderr[-400:]}")
    return next(
        line.split()[-1].strip()
        for line in keygen.stdout.splitlines()
        if line.strip().startswith(identity)
    )


def governed(workspace: Path, source: Path, command: list[str] | None = None) -> tuple[Path, Path, Path]:
    """A fresh governed clone of the pinned subject, frozen and committed."""

    repo = workspace / "subject"
    shutil.copytree(source, repo)
    key = workspace / "producer.key"
    verdict_key = workspace / "verdict-signer.key"
    public = minted(repo, PRODUCER, key)
    signer = minted(repo, SIGNER, verdict_key)
    (repo / "governance").mkdir(exist_ok=True)
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  {PRODUCER}: {public}\n"
        f"verdict_signer:\n  id: {SIGNER}\n  public_key: {signer}\n",
        encoding="utf-8",
    )
    (repo / "governance" / "gates.yaml").write_text(
        catalog(command or scan_argv()), encoding="utf-8"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "governance: producer keyring and a scan-bound gate")

    frozen = ranex(
        repo, "suite", "freeze",
        "--artifact", ARTIFACT,
        "--output", MANIFEST,
        "--results-reporter", "sarif-2.1.0",
        "--scan-scope", SCOPE,
        "--scan-rule", "F401",
        "--", *(command or scan_argv()),
    )
    if frozen.returncode != 0:
        raise SystemExit(f"freeze failed: {frozen.stdout[-400:]}{frozen.stderr[-400:]}")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "governance: freeze the scan manifest")
    return repo, key, verdict_key


def gate(repo: Path, key: Path, verdict_key: Path, *, observe: bool = True,
         command: list[str] | None = None) -> dict[str, object]:
    """Run the bound scanner (or not) and read the verdict. Facts only."""

    run_exit: int | None = None
    if observe:
        observed = ranex(
            repo, "run",
            "--claim", "scan",
            "--producer", PRODUCER,
            "--gate-catalog", "governance/gates.yaml",
            "--producers", "governance/producers.yaml",
            "--evidence", "governance/evidence.json",
            "--", *(command or scan_argv()),
            key=key,
        )
        run_exit = observed.returncode
    verdict = ranex(
        repo, "gate", "evaluate", "HEAD",
        "--gate-catalog", "governance/gates.yaml",
        "--producers", "governance/producers.yaml",
        "--evidence", "governance/evidence.json",
        "--approver", APPROVER,
        verdict_key=verdict_key,
    )
    word = "ERROR"
    for line in verdict.stdout.splitlines():
        if line.startswith(("PASS", "FAIL")):
            word = line.split()[0]
            break
    return {
        "run_exit": run_exit,
        "verdict": word,
        "evaluate_exit": verdict.returncode,
        "evidence": (repo / "governance" / "evidence.json").is_file(),
    }


def anchored(repo: Path, *, truncate: bool) -> dict[str, object]:
    """Does the journal still verify against the head its signed verdict fixed?

    ADR-057: a signed verdict fixes a chain head, so a journal that has been
    rewritten since cannot be anchored to it. Deleting the last row is the
    cheapest real rewrite there is.
    """

    verdicts = sorted((repo / "governance" / "verdicts").glob("*.json"))
    if not verdicts:
        return {"verdicts": 0, "verify_exit": None}
    if truncate:
        with sqlite3.connect(repo / "governance" / "journal.sqlite3") as connection:
            connection.execute(
                "DELETE FROM evaluations WHERE rowid = (SELECT MAX(rowid) FROM evaluations)"
            )
            connection.commit()
    verified = ranex(
        repo, "journal", "verify",
        "--journal", "governance/journal.sqlite3",
        "--against-verdict", str(verdicts[-1].relative_to(repo)),
        "--producers", "governance/producers.yaml",
    )
    return {"verdicts": len(verdicts), "verify_exit": verified.returncode}


def measured(source: Path, prepare=None, *, observe: bool = True,
             command: list[str] | None = None) -> Observation:
    """One end-to-end arm in its own workspace.

    `ok` is what was observed, never what was hoped: it is True when the gate
    PASSed. For a positive that is the expectation holding; for a negative it
    is the alarm — the check accepted what it exists to refuse.
    """

    with tempfile.TemporaryDirectory(prefix="ranex-sarif-") as scratch:
        repo, key, verdict_key = governed(Path(scratch), source, command=command)
        if prepare is not None:
            prepare(repo)
        facts = gate(repo, key, verdict_key, observe=observe, command=command)
    return Observation(ok=facts["verdict"] == "PASS", facts=facts)


def anchored_run(source: Path, *, truncate: bool) -> Observation:
    """A clean PASS, then the journal checked against the verdict that signed it."""

    with tempfile.TemporaryDirectory(prefix="ranex-anchor-") as scratch:
        repo, key, verdict_key = governed(Path(scratch), source)
        facts = gate(repo, key, verdict_key)
        facts.update(anchored(repo, truncate=truncate))
    return Observation(ok=facts["verify_exit"] == 0, facts=facts)


def inject_violation(repo: Path) -> None:
    path = repo / SCOPE
    path.write_text(VIOLATION + path.read_text(encoding="utf-8"), encoding="utf-8")
    git(repo, "commit", "-qam", "a real F401 on a scratch commit")


def widen_manifest(repo: Path) -> None:
    """Add an accepted ID after the manifest was frozen and reviewed."""

    manifest = json.loads((repo / MANIFEST).read_text(encoding="utf-8"))
    manifest["accepted"] = {f"{SCOPE}::F401::{'0' * 64}": "waved through after the fact"}
    (repo / MANIFEST).write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    git(repo, "commit", "-qam", "widen accepted after the freeze")


def forged(document: dict[str, object]):
    """Bind a producer that writes `document` instead of scanning."""

    def prepare(repo: Path) -> None:
        (repo / "forge.py").write_text(FORGER, encoding="utf-8")
        (repo / "forged.json").write_text(json.dumps(document), encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-qm", "bind a report producer that does not scan")

    return prepare


def forged_document(line: int, results: bool = True, **run_fields: object) -> dict:
    entries = [{
        "ruleId": "F401",
        "level": "error",
        "locations": [{"physicalLocation": {
            "artifactLocation": {"uri": SCOPE},
            "region": {"startLine": line, "endLine": line},
        }}],
    }] if results else []
    return {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "forger"}}, "results": entries, **run_fields}],
    }


FORGER_ARGV = ["/usr/bin/python3", "forge.py", "--output-format=sarif",
               f"--output-file={ARTIFACT}"]


def main() -> int:
    if not RANEX.is_file():
        raise SystemExit("the installed console script is absent: run `uv sync --frozen`")
    out = TOOL_DIR / "audits" / f"{date.today().isoformat()}-sarif-reporter" / "sarif.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ranex-six-") as cache:
        source = Path(cache) / "six"
        clone = subprocess.run(["git", "clone", "-q", SIX_URL, str(source)],
                               capture_output=True, text=True, check=False)
        if clone.returncode != 0:
            raise SystemExit(f"cannot clone the pinned subject: {clone.stderr[-300:]}")
        git(source, "checkout", "-q", SIX_REV)
        if git(source, "rev-parse", "HEAD").stdout.strip() != SIX_REV:
            raise SystemExit("the subject is not at its pinned commit")

        calibration = Calibration(out=out)
        calibration.run(Control(
            name="a-scan-claim-decides-a-real-gate",
            expectation="a clean scan of the pinned subject PASSes; one real F401 does not",
            positive=lambda: measured(source),
            negative=lambda: measured(source, inject_violation),
        ))
        calibration.run(Control(
            name="absence-blocks-a-scan-claim",
            expectation="evidence decides; a gate with no scan recorded cannot PASS",
            positive=lambda: measured(source),
            negative=lambda: measured(source, observe=False),
        ))
        calibration.run(Control(
            name="a-widened-manifest-does-not-carry-old-evidence",
            expectation="accepted findings added after the freeze do not rescue a run",
            positive=lambda: measured(source),
            negative=lambda: measured(
                source, lambda repo: (inject_violation(repo), widen_manifest(repo)),
            ),
        ))
        calibration.run(Control(
            name="a-forged-region-is-refused",
            expectation="a report naming a line the subject does not carry is not evidence",
            positive=lambda: measured(source),
            negative=lambda: measured(
                source, forged(forged_document(line=10_000)),
                command=FORGER_ARGV,
            ),
        ))
        calibration.run(Control(
            name="the-journal-anchors-to-the-signed-verdict",
            expectation="the chain verifies against the head its signed verdict fixed, "
                        "and a rewritten chain does not",
            positive=lambda: anchored_run(source, truncate=False),
            negative=lambda: anchored_run(source, truncate=True),
        ))
        calibration.run(Control(
            name="a-scanner-that-declares-failure-is-refused",
            expectation="executionSuccessful=false with zero findings never reads as clean",
            positive=lambda: measured(source),
            negative=lambda: measured(
                source,
                forged(forged_document(line=1, results=False,
                                       invocations=[{"executionSuccessful": False}])),
                command=FORGER_ARGV,
            ),
        ))

    calibration.save()
    unverified = [case for case in calibration.cases if case["status"] != str(Status.VERIFIED)]
    print(f"\nreceipt: {out}")
    for case in calibration.cases:
        print(f"  {case['status']:18} {case['control']}")
    return 1 if unverified else 0


if __name__ == "__main__":
    raise SystemExit(main())
