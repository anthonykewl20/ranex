#!/usr/bin/env python3
"""v0.1.0 governing a clean EXTERNAL repository — the F-003 flow, scripted.

Proves, with the released kernel only (never the working tree), on a real
third-party repository (default benjaminp/six at a pinned commit):

  1. the frozen-checkout operator install works from a clean checkout of
     the tag — `git checkout <tag>` + `uv sync --frozen` (ADR-038/009);
  2. a clean external repository can be brought under governance with no
     undocumented manual repair: vendored kernel `src/` (tree-digest
     identical to the tag — the CLI governs the repo that contains it,
     F-003/ADR-009), committed producer keyring, gate catalog binding the
     repository's own test command, pristine frozen suite manifest;
  3. the governed cycle: `ranex run` (signed, subject-bound evidence) ->
     `gate evaluate` PASS -> `journal verify` chain=verified;
  4. the attack: ONE comment line appended to the repository's own source
     AFTER the green evidence, no re-run -> `gate evaluate` refuses with
     "evidence bound to a different subject digest", exit 1 — stale
     evidence for a changed subject is never a PASS;
  5. recovery: the work is re-run under governance -> PASS again, journal
     still verified. The gate blocks the shortcut, not the honest path.

Prerequisites, checked before any work: git and uv on PATH, a pinned
interpreter (/usr/bin/python3) that can import pytest — `ranex run`
resolves argv[0] only through system directories by design (F-003) — the
kernel tag present in this checkout, and network for the clone and
`uv sync`. Any failed step exits 2 with its name and captured output;
nothing is fabricated on failure.

Receipts: a JSON report is printed (and kept with --keep). With
--publish, two entries are appended to the proof pile
(tools/dogfood/oss_bench/proofs/) — kind "run" and the stale-evidence
attack — and the site page is regenerated from the pile.

Reproducibility: the kernel tag, external URL, and commit are pinned
constants (overridable by flags). Key material is generated fresh each
run, so digests differ between runs; verdicts, exit codes, and refusal
reasons are asserted, not eyeballed.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DOGFOOD = Path(__file__).resolve().parent
sys.path.insert(0, str(DOGFOOD / "oss_bench"))

import proofs  # noqa: E402 — the append-only pile, shared with the site page

KERNEL_TAG = "v0.1.0"
EXTERNAL_URL = "https://github.com/benjaminp/six"
EXTERNAL_REV = "c8e394065cd541a16c040515dc0afb85cf22a7c3"
EDIT_FILE = "six.py"  # the repository's own source; one comment line appended
PRODUCER = "external-proof-producer"
APPROVER = "external-proof-approver"
PINNED_PY = "/usr/bin/python3"

STALE_REASON = "evidence bound to a different subject digest"


class StepFailure(Exception):
    """A step's observed result contradicted what the flow requires."""

    def __init__(self, step: str, detail: str) -> None:
        super().__init__(f"[{step}] {detail}")
        self.step = step
        self.detail = detail


def _run(argv: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None,
         timeout: int = 600) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(a) for a in argv], cwd=str(cwd) if cwd else None,
                          env=env, capture_output=True, text=True, check=False,
                          timeout=timeout)


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-C", repo, "-c", "user.email=external-proof@ranex.invalid",
                 "-c", "user.name=ranex-external-proof", *args])


def _kernel_env(repo: Path, key: Path | None) -> dict[str, str]:
    """Environment in which the RELEASED kernel runs anchored to the external
    repository: PYTHONPATH precedes site-packages, so the vendored copy under
    <repo>/src wins over the venv's own installed project."""
    env = dict(os.environ)
    if key is not None:
        env["RANEX_SIGNING_KEY"] = str(key)
    env["PYTHONPATH"] = str(repo / "src")
    return env


def _ranex(kernel: Path, repo: Path, key: Path | None, *args: str,
           timeout: int = 900) -> subprocess.CompletedProcess[str]:
    return _run([kernel / ".venv" / "bin" / "python", "-m", "ranex.cli.main", *args],
                cwd=repo, env=_kernel_env(repo, key), timeout=timeout)


def _kernel_python(kernel: Path, repo: Path, *args: str,
                   timeout: int = 600) -> subprocess.CompletedProcess[str]:
    """Raw interpreter from the released venv, ranex imported from the
    VENDORED copy — used for the manifest freeze and the anchoring check."""
    return _run([kernel / ".venv" / "bin" / "python", *args],
                cwd=repo, env=_kernel_env(repo, None), timeout=timeout)


def check_prerequisites(kernel_repo: Path, tag: str) -> None:
    for tool in ("git", "uv"):
        if shutil.which(tool) is None:
            raise StepFailure("prerequisites", f"{tool} not on PATH")
    probe = _run([PINNED_PY, "-c", "import pytest"])
    if probe.returncode != 0:
        raise StepFailure(
            "prerequisites",
            f"{PINNED_PY} cannot import pytest — ranex run resolves argv[0] "
            "only through system directories (F-003); install system pytest "
            f"(e.g. sudo apt install python3-pytest). {probe.stderr[-200:]}")
    resolved = _run(["git", "-C", kernel_repo, "rev-parse", f"{tag}^{{}}"])
    if resolved.returncode != 0:
        raise StepFailure("prerequisites", f"tag {tag} not found in {kernel_repo}")


def provision_kernel(scratch: Path, kernel_repo: Path, tag: str) -> dict[str, Any]:
    """Clean checkout of the tag + the documented frozen install."""
    started = time.monotonic()
    kernel = scratch / "kernel"
    clone = _run(["git", "clone", "--quiet", "--no-hardlinks", kernel_repo, kernel],
                 timeout=300)
    if clone.returncode != 0:
        raise StepFailure("kernel-clone", clone.stderr[-400:])
    checked = _git(kernel, "checkout", "--quiet", tag)
    if checked.returncode != 0:
        raise StepFailure("kernel-checkout", checked.stderr[-400:])
    commit = _git(kernel, "rev-parse", "HEAD").stdout.strip()
    src_tree = _git(kernel, "rev-parse", f"{tag}:src").stdout.strip()
    sync = _run(["uv", "sync", "--frozen"], cwd=kernel, timeout=600)
    if sync.returncode != 0:
        raise StepFailure("kernel-install", sync.stderr[-600:])
    with (kernel / "pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]
    return {"commit": commit, "version": version, "src_tree": src_tree,
            "elapsed_s": round(time.monotonic() - started, 1)}


def clone_external(scratch: Path, url: str, rev: str) -> tuple[Path, dict[str, Any]]:
    """The clean external repository at a pinned commit (full clone: the
    kernel materialises from this object store and must not need network)."""
    started = time.monotonic()
    repo = scratch / "external"
    clone = _run(["git", "clone", "--quiet", url, repo], timeout=300)
    if clone.returncode != 0:
        raise StepFailure("external-clone", clone.stderr[-400:])
    if rev.upper() != "HEAD":
        checked = _git(repo, "checkout", "--quiet", rev)
        if checked.returncode != 0:
            raise StepFailure("external-checkout", checked.stderr[-400:])
    commit = _git(repo, "rev-parse", "HEAD").stdout.strip()
    # ADR-005 withdrew observation of symlink/submodule trees; refuse before
    # building governance on a tree the kernel cannot materialise.
    listing = _git(repo, "ls-files", "-s")
    carrying = [line.split()[3] for line in listing.stdout.splitlines()
                if line.split()[0] in {"120000", "160000"}]
    if carrying:
        raise StepFailure("external-checkout",
                          f"tree carries symlink/submodule entries (ADR-005 "
                          f"boundary): {carrying[:3]}")
    license_head = ""
    for name in ("LICENSE", "LICENSE.txt", "LICENSE-MIT"):
        candidate = repo / name
        if candidate.is_file():
            license_head = candidate.read_text(encoding="utf-8")[:80].strip()
            break
    facts = {"url": url, "rev": rev, "commit": commit, "license": license_head,
             "elapsed_s": round(time.monotonic() - started, 1)}
    return repo, facts


def measure_baseline(repo: Path, scratch: Path) -> dict[str, Any]:
    """The repository's own suite, run bare under the pinned interpreter:
    outcomes keyed by REAL pytest node id (junit classnames are remapped and
    the mapping verified against collection), plus the bare-CI receipt."""
    started = time.monotonic()
    collected = _run([PINNED_PY, "-m", "pytest", "-q", "--collect-only", "--no-header"],
                     cwd=repo, timeout=300)
    real_ids = sorted(line.strip() for line in collected.stdout.splitlines()
                      if "::" in line and not line.startswith("="))
    if not real_ids:
        raise StepFailure("baseline-collect",
                          collected.stdout[-300:] + collected.stderr[-300:])
    probe = scratch / "baseline.xml"
    full = _run([PINNED_PY, "-m", "pytest", "-q", f"--junitxml={probe}"],
                cwd=repo, timeout=600)
    tail = full.stdout.strip().splitlines()[-1] if full.stdout.strip() else ""
    if full.returncode != 0:
        raise StepFailure("baseline-green",
                          f"pristine suite is red under {PINNED_PY}: {tail}")
    outcomes: dict[str, str] = {}
    root = ET.fromstring(probe.read_bytes())
    for case in root.iter("testcase"):
        classname, name = case.get("classname", ""), case.get("name", "")
        parts = classname.split(".")
        node = (parts[0] + ".py"
                + ("::" + "::".join(parts[1:]) if len(parts) > 1 else "") + "::" + name)
        if case.find("skipped") is not None:
            outcomes[node] = "skipped"
        elif case.find("failure") is not None or case.find("error") is not None:
            outcomes[node] = "failed"
        else:
            outcomes[node] = "passed"
    unknown = set(outcomes) - set(real_ids)
    if unknown:
        raise StepFailure("baseline-map",
                          f"junit ids not in collection: {sorted(unknown)[:3]} "
                          "(the id mapping assumes root-level test modules)")
    passing = [i for i in real_ids if outcomes.get(i) == "passed"]
    if not passing:
        raise StepFailure("baseline-map", "no passing node ids to bind")
    return {"collected": len(real_ids), "passing": passing,
            "skipped": sum(1 for value in outcomes.values() if value == "skipped"),
            "bare_ci": {"command": f"{PINNED_PY} -m pytest -q",
                        "exit": full.returncode, "verdict": "GREEN",
                        "output_tail": tail,
                        "elapsed_s": round(time.monotonic() - started, 1)}}


def onboard_governance(kernel: Path, repo: Path, scratch: Path, tag: str,
                       passing: list[str], max_ids: int) -> dict[str, Any]:
    """Vendor the kernel + commit governance. This IS the documented external
    integration pattern (F-003): the CLI governs the repo containing it."""
    started = time.monotonic()
    selected = passing[:max_ids] if max_ids else passing
    argv = [PINNED_PY, "-m", "pytest", "-q",
            "--junitxml=governance/suite_results.xml", *selected]

    if (repo / "src").exists():
        raise StepFailure(
            "vendor", "the external repository already carries src/ — the "
            "vendored kernel would shadow repository content; refusing")
    shutil.copytree(kernel / "src", repo / "src",
                    ignore=shutil.ignore_patterns("__pycache__"))
    # APPEND the governance patterns: replacing a tracked .gitignore wholesale
    # would silently rewrite the third party's own file and could commit
    # whatever their rules were keeping out.
    governance_ignores = ("governance/evidence.json\n"
                          "governance/suite_results.xml\n"
                          "governance/journal.sqlite3\n"
                          "__pycache__/\n*.pyc\n.pytest_cache/\n")
    gitignore = repo / ".gitignore"
    existing_ignores = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    gitignore.write_text(existing_ignores + governance_ignores)
    if _git(repo, "add", "-A").returncode != 0:
        raise StepFailure("vendor-commit", "git add failed")
    if _git(repo, "commit", "-qm",
            "vendor ranex kernel src (released tag; tree-digest verified)"
            ).returncode != 0:
        raise StepFailure("vendor-commit", "git commit failed")
    vendored_tree = _git(repo, "rev-parse", "HEAD:src").stdout.strip()
    tag_tree = _git(kernel, "rev-parse", f"{tag}:src").stdout.strip()
    if vendored_tree != tag_tree:
        raise StepFailure("vendor-identity",
                          f"vendored src tree {vendored_tree} != {tag}:src {tag_tree}")

    # keygen through the released CLI: the key never enters the repository.
    key = scratch / "external-proof.key"
    keygen = _ranex(kernel, repo, key, "keygen", "--producer", PRODUCER)
    if keygen.returncode != 0 or not key.is_file():
        raise StepFailure("keygen", keygen.stderr[-400:])
    public = [line.split()[-1].strip() for line in keygen.stdout.splitlines()
              if line.strip().startswith(PRODUCER)]
    if not public:
        raise StepFailure("keygen", f"no public key printed:\n{keygen.stdout}")

    (repo / "governance").mkdir(exist_ok=True)
    (repo / "governance" / "producers.yaml").write_text(
        f"producers:\n  {PRODUCER}: {public[0]}\n")
    # The manifest is frozen by the RELEASED kernel's own code, serialised in
    # its own canonical form — never a re-implementation (F-005 item 2).
    probe = scratch / "freeze.xml"
    probe_argv = [PINNED_PY, "-m", "pytest", "-q", f"--junitxml={probe}", *selected]
    program = (
        "import pathlib, subprocess, sys\n"
        "from ranex.foundation.suite_results import freeze_manifest, canonical_json_bytes\n"
        "command = sys.argv[1:]\n"
        "junit = next(a.split('=', 1)[1] for a in command if a.startswith('--junitxml='))\n"
        "run = subprocess.run(command, capture_output=True, text=True, check=False)\n"
        "assert run.returncode == 0, run.stdout[-300:] + run.stderr[-300:]\n"
        "manifest = freeze_manifest(pathlib.Path(junit).read_bytes(), expected_skips={})\n"
        "pathlib.Path('governance/suite_manifest.json').write_bytes("
        "canonical_json_bytes(manifest))\n"
        "print(len(manifest['suite']))\n")
    freeze = _kernel_python(kernel, repo, "-c", program, *probe_argv)
    if freeze.returncode != 0:
        raise StepFailure("manifest-freeze",
                          freeze.stdout[-300:] + freeze.stderr[-300:])

    claims = ("      - claim_id: tests-executed\n        command: [{}]\n"
              "        results_artifact: governance/suite_results.xml\n").format(
        ", ".join(json.dumps(part) for part in argv))
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TASK_TESTS\n"
        "    blocking: true\n    required_claims:\n" + claims)
    if _git(repo, "add", "-A").returncode != 0 or _git(
            repo, "commit", "-qm",
            "governance: producer keyring, frozen manifest, results-bound gate"
            ).returncode != 0:
        raise StepFailure("governance-commit", "git commit failed")
    return {"key": key, "argv": argv, "selected": len(selected),
            "manifest_ids": int(freeze.stdout.strip() or 0),
            "vendored_src_tree": vendored_tree,
            "elapsed_s": round(time.monotonic() - started, 1)}


def governed_cycle(kernel: Path, repo: Path, key: Path,
                   argv: list[str]) -> dict[str, Any]:
    """run -> gate evaluate -> journal verify; every verdict from exit codes."""
    started = time.monotonic()
    run = _ranex(kernel, repo, key, "run", "--claim", "tests-executed",
                 "--producer", PRODUCER, "--", *argv)
    if run.returncode != 0 or "RECORDED" not in run.stdout:
        raise StepFailure("governed-run",
                          f"exit {run.returncode}: {run.stdout[-200:]}{run.stderr[-300:]}")
    gate = _ranex(kernel, repo, key, "gate", "evaluate", "HEAD",
                  "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    if gate.returncode != 0 or not gate.stdout.startswith("PASS"):
        raise StepFailure("governed-gate",
                          f"exit {gate.returncode}: {gate.stdout}{gate.stderr[-200:]}")
    journal = _ranex(kernel, repo, key, "journal", "verify",
                     "--journal", "governance/journal.sqlite3")
    if journal.returncode != 0 or "chain=verified" not in journal.stdout:
        raise StepFailure("governed-journal",
                          f"exit {journal.returncode}: {journal.stdout}{journal.stderr[-200:]}")
    return {"run_command": "ranex run --claim tests-executed --producer "
            f"{PRODUCER} -- {' '.join(argv)}",
            "run_exit": run.returncode, "run_error": "",
            "gate_verdict": "PASS", "gate_output": gate.stdout.strip(),
            "journal_output": journal.stdout.strip(), "journal_verified": True,
            "elapsed_s": round(time.monotonic() - started, 1)}


def stale_attack(kernel: Path, repo: Path, key: Path, edit_file: str) -> dict[str, Any]:
    """The demonstration: change the subject AFTER green evidence, do NOT
    re-run, and the gate must refuse the stale evidence by name."""
    started = time.monotonic()
    before = _ranex(kernel, repo, key, "gate", "evaluate", "HEAD",
                    "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    if before.returncode != 0 or not before.stdout.startswith("PASS"):
        raise StepFailure("attack-before", before.stdout + before.stderr[-200:])
    target = repo / edit_file
    if not target.is_file():
        raise StepFailure("attack-edit", f"{edit_file} not in repository root")
    with target.open("a", encoding="utf-8") as handle:
        handle.write("\n# governance proof: the subject changed after evidence\n")
    if _git(repo, "add", "-A").returncode != 0 or _git(
            repo, "commit", "-qm", "change the subject under governance"
            ).returncode != 0:
        raise StepFailure("attack-edit", "git commit failed")
    after = _ranex(kernel, repo, key, "gate", "evaluate", "HEAD",
                   "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    if after.returncode != 1 or STALE_REASON not in after.stdout:
        raise StepFailure("attack-refusal",
                          f"expected exit 1 naming '{STALE_REASON}', got "
                          f"exit {after.returncode}: {after.stdout}{after.stderr[-200:]}")
    journal = _ranex(kernel, repo, key, "journal", "verify",
                     "--journal", "governance/journal.sqlite3")
    if journal.returncode != 0:
        raise StepFailure("attack-journal", journal.stdout + journal.stderr[-200:])
    return {"before": {"gate_output": before.stdout.strip(), "exit": before.returncode},
            "after": {"gate_output": after.stdout.strip(), "exit": after.returncode},
            "journal_after_refusal": journal.stdout.strip(),
            "edit": {"file": edit_file,
                     "kind": "one comment line appended after green evidence, no re-run"},
            "elapsed_s": round(time.monotonic() - started, 1)}


def _publish_entries(receipt: dict[str, Any], date: str) -> list[Path]:
    """Append run + attack entries to the pile (idempotent per kernel commit
    AND external revision) and regenerate the site page from the archive."""
    identity = receipt["external"]
    kernel_commit = receipt["kernel"]["commit"]
    task = f"external:{identity['url'].split('/')[-1]}"
    run_id = "external-{}-{}".format(identity["url"].split("/")[-1],
                                     identity["commit"][:8])
    existing = proofs.corpus()
    written: list[Path] = []
    if (run_id, kernel_commit) not in {
            (e.get("run_id"), e.get("kernel_head"))
            for e in existing if e.get("kind") == "run"}:
        written.append(proofs.append_external({
            "schema": proofs.SCHEMA, "kind": "run", "date": date,
            "kernel_head": kernel_commit, "kernel_version": receipt["kernel"]["version"],
            "task": task, "run_id": run_id,
            "model": None, "tokens": None, "cost_usd": None, "agentless": True,
            "external": identity, "bare_ci": receipt["baseline"]["bare_ci"],
            "ranex_gate": receipt["cycle"],
            "duration_s": receipt["cycle"]["elapsed_s"],
            "flow_elapsed_s": receipt["elapsed_s"]}))
    if ("stale-proof-external", kernel_commit, identity["commit"]) not in {
            (e.get("attack"), e.get("kernel_head"), e.get("external", {}).get("commit"))
            for e in existing}:
        written.append(proofs.append_external({
            "schema": proofs.SCHEMA, "kind": "attack", "attack": "stale-proof-external",
            "date": date, "kernel_head": kernel_commit,
            "kernel_version": receipt["kernel"]["version"],
            "task": task, "run_id": "external-stale", "model": None,
            "fault_injected": True, "external": identity,
            "before": receipt["attack"]["before"], "after": receipt["attack"]["after"],
            "edit": receipt["attack"]["edit"],
            "journal_after_refusal": receipt["attack"]["journal_after_refusal"],
            "caught": receipt["attack"]["after"]["exit"] == 1}))
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tag", default=KERNEL_TAG, help="released kernel tag")
    parser.add_argument("--url", default=EXTERNAL_URL, help="external repository URL")
    parser.add_argument("--rev", default=EXTERNAL_REV,
                        help="pinned commit (or HEAD for the external tip)")
    parser.add_argument("--edit-file", default=EDIT_FILE,
                        help="repository file changed for the stale-evidence attack")
    parser.add_argument("--max-ids", type=int, default=0,
                        help="bound the bound test selection (0 = all passing)")
    parser.add_argument("--publish", action="store_true",
                        help="append proof-pile entries and regenerate the site page")
    parser.add_argument("--keep", action="store_true",
                        help="keep the scratch directory and write receipt.json there")
    args = parser.parse_args()

    started = time.monotonic()
    try:
        check_prerequisites(REPO_ROOT, args.tag)
        print("prerequisites: git, uv, pinned pytest, tag — OK")
        keep_dir: Path | None = None
        scratch_parent = Path(tempfile.mkdtemp(prefix="ranex-external-proof-"))
        scratch = scratch_parent / "run"
        scratch.mkdir()
        try:
            kernel_facts = provision_kernel(scratch, REPO_ROOT, args.tag)
            kernel = scratch / "kernel"
            print(f"kernel: {args.tag} @ {kernel_facts['commit'][:12]} "
                  f"(v{kernel_facts['version']}, src tree {kernel_facts['src_tree'][:12]})")
            repo, identity = clone_external(scratch, args.url, args.rev)
            print(f"external: {args.url} @ {identity['commit'][:12]}")
            baseline = measure_baseline(repo, scratch)
            print(f"baseline: {baseline['collected']} collected, "
                  f"{len(baseline['passing'])} passing, {baseline['skipped']} "
                  f"skipped — GREEN")
            onboarding = onboard_governance(kernel, repo, scratch, args.tag,
                                            baseline["passing"], args.max_ids)
            key: Path = onboarding.pop("key")
            argv: list[str] = onboarding.pop("argv")
            print(f"onboarded: vendored src tree == {args.tag}:src "
                  f"({onboarding['vendored_src_tree'][:12]}), "
                  f"{onboarding['selected']} ids bound, manifest froze "
                  f"{onboarding['manifest_ids']}")
            anchored = _kernel_python(kernel, repo, "-c", "import ranex; print(ranex.__file__)")
            if str(repo / "src") not in anchored.stdout:
                raise StepFailure(
                    "anchoring",
                    f"ranex resolves from {anchored.stdout.strip()!r} "
                    f"(stderr: {anchored.stderr.strip()[-200:]!r}), not the "
                    "vendored copy under the external repository")
            cycle = governed_cycle(kernel, repo, key, argv)
            print(f"governed cycle: run exit {cycle['run_exit']}, gate PASS, "
                  f"journal verified ({cycle['elapsed_s']}s)")
            attack = stale_attack(kernel, repo, key, args.edit_file)
            print(f"attack: refused — '{STALE_REASON}' "
                  f"(exit {attack['after']['exit']})")
            recovery = governed_cycle(kernel, repo, key, argv)
            print(f"recovery: gate {recovery['gate_verdict']} after re-running "
                  f"the work ({recovery['elapsed_s']}s)")

            identity["kernel_tag"] = args.tag
            identity["kernel_install"] = (
                "git checkout <tag> + uv sync --frozen (frozen-checkout "
                "operator install, ADR-038/009)")
            identity["vendored_src_tree"] = onboarding["vendored_src_tree"]
            identity["tag_src_tree"] = kernel_facts["src_tree"]
            identity["vendored_identical_to_tag"] = True
            identity["selected_ids"] = onboarding["selected"]
            receipt = {"schema": "ranex-external-proof-v1",
                       "date": datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d"),
                       "kernel": kernel_facts, "external": identity,
                       "baseline": {k: v for k, v in baseline.items() if k != "passing"},
                       "cycle": cycle, "attack": attack, "recovery": recovery,
                       "elapsed_s": round(time.monotonic() - started, 1)}
            if args.keep:
                (scratch_parent / "receipt.json").write_text(
                    json.dumps(receipt, indent=2, sort_keys=True) + "\n")
                keep_dir = scratch_parent
        finally:
            if keep_dir is None:
                shutil.rmtree(scratch_parent, ignore_errors=True)
            else:
                print(f"scratch kept: {keep_dir}")
        if args.publish:
            written = _publish_entries(receipt, receipt["date"])
            import oss_report_site
            page = oss_report_site.generate_page(DOGFOOD / "site")
            print("published: " + (", ".join(p.name for p in written)
                                   if written else "entries already present (idempotent)")
                  + f"; page: {page}")
        print(json.dumps(receipt, indent=2, sort_keys=True))
        return 0
    except StepFailure as failure:
        print(f"FAILED {failure.step}: {failure.detail}", file=sys.stderr)
        return 2
    except Exception as failure:  # noqa: BLE001 — the contract is exit 2 + named cause
        print(f"FAILED unexpected {type(failure).__name__}: {failure}",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
