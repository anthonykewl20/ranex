#!/usr/bin/env python3
"""Two-arm ranex-vs-bare adapter over REAL VulcanBench tasks.

Arm semantics (both arms run the task's own hidden-test commands against
the task's own real repo):

  bare      — the commands run; a bare agent's "done" is its own claim.
  governed  — the same repo carries vendored ranex + committed governance;
              each test command runs under `ranex run` producing SIGNED
              evidence; `gate evaluate` decides; the journal chain must
              verify.

TWO verified integration facts shape this adapter (F-003):
  1. governed_repository_root() resolves the repo containing the CLI, so the
     ranex source is VENDORED into the task repo (committed) and the CLI is
     run with PYTHONPATH=<task-repo>/src — the kernel's own
     clone-judges-clone model.
  2. `ranex run` resolves argv[0] only through the pinned toolchain
     (/usr/bin, /bin, /usr/sbin, /sbin). Task commands naming `python` need
     a pinned interpreter WITH pytest: PREREQUISITE, checked honestly here.

Bare-arm purity (#114): the bare arm's environment is DECLARED (an explicit
allowlist plus an asserted venv-on-PATH entry), never `dict(os.environ)`,
and an in-child canary measures the environment every command actually
receives — no RANEX_* variable, no PYTHONPATH naming a ranex source root,
no vendored kernel directory on PATH — failing the whole run on
contamination instead of reporting a cleaner diff. `--contaminate` injects
exactly one contamination channel and exists only to be caught (negative
control; the run must exit 3).

MODES:
  --mode tasks     the real two-arm study (requires the pinned-python
                   pytest prerequisite; refuses to invent results without it)
  --mode plumbing  end-to-end pipeline proof on the real task repo using a
                   genuinely pinned tool (`git`) — proves vendoring, run,
                   signed evidence, gate verdict, journal verification.
                   NOT a benchmark result; never publish it as one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RANEX_REPO = HERE.parents[2]
RANEX_PY = RANEX_REPO / ".venv" / "bin" / "python"
DEFAULT_VULCAN = Path("/home/soultransit/devtony/VulcanBench")
_state = HERE / "state.json"
if _state.is_file():
    try:
        DEFAULT_VULCAN = Path(json.loads(_state.read_text()).get(
            "vulcan_root", DEFAULT_VULCAN))
    except (OSError, json.JSONDecodeError, TypeError):
        pass

sys.path.insert(0, str(RANEX_REPO / "src"))
sys.path.insert(0, str(HERE.parent))
from cmdparse import PINNED_PYTHON, parse_cmd, pinned_argv  # noqa: E402
from ranex.foundation.signing import generate_keypair  # noqa: E402

APPROVER = "oss-bench-approver"
PRODUCER = "oss-bench-producer"

# --- the bare arm is declared, measured, and provably bare (#114) ----------
#
# The bare environment used to be `dict(os.environ)` plus a venv prepend —
# defensible, but unproven: an inherited PYTHONPATH, an inherited RANEX_*
# variable, or a vendored kernel on PATH would make the bare arm quietly
# governed and the comparison would report a difference that is not there
# (upstream's ponytail benchmark nearly published a false ~4% exactly this
# way). The allowlist below IS the whole environment; the canary then
# measures what the child really received.

#: benign variables passed through from the operator's ambient environment
BARE_ENV_PASSTHROUGH: tuple[str, ...] = (
    "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "TMPDIR",
)
#: the system PATH the bare arm declares; the ranex venv is prepended as an
#: explicit, asserted entry (the deliberate bare-agent interpreter choice)
BARE_SYSTEM_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

#: negative controls (#114): each injects exactly one contamination channel
#: and exists only to be caught by the canary
CONTAMINATIONS: dict[str, Callable[[], dict[str, str]]] = {
    "pythonpath": lambda: {"PYTHONPATH": str(RANEX_REPO / "src")},
    "ranex-var": lambda: {"RANEX_SIGNING_KEY": "/tmp/bare-arm-canary.key"},
    "vendored-path": lambda: {"PATH": str(RANEX_REPO / "src")},
}

#: runs INSIDE the bare child and reports the environment the child actually
#: received — the receipt records the environment used, not the one intended
BARE_CANARY = "import json, os; print(json.dumps(dict(os.environ), sort_keys=True))"


class BareArmContaminated(RuntimeError):
    """The bare arm saw governance machinery; the run refuses to continue."""

    def __init__(self, findings: list[str]) -> None:
        super().__init__("; ".join(findings))
        self.findings = findings


def bare_environment(contaminate: str | None = None) -> dict[str, str]:
    """Construct the bare arm's environment from the declared allowlist.

    Never `dict(os.environ)`: the passthrough tuple plus the declared PATH
    are the entire environment, so a RANEX_* variable, a PYTHONPATH, or any
    other ambient inheritance is absent by construction — and the canary
    still measures the child to prove it (#114 arm 1).
    """
    env = {name: os.environ[name] for name in BARE_ENV_PASSTHROUGH
           if name in os.environ}
    env["PATH"] = f"{RANEX_PY.parent}:{BARE_SYSTEM_PATH}"
    if contaminate is not None:
        env.update(CONTAMINATIONS[contaminate]())
    return env


def contamination_findings(env: Mapping[str, str]) -> list[str]:
    """The three channels that would make a bare arm quietly governed.

    Names are reported without values: an inherited RANEX_* value could
    itself be operator secret material.
    """
    findings = []
    for name in sorted(env):
        if name.startswith("RANEX_"):
            findings.append(f"RANEX_* variable present: {name}")
    for var in ("PYTHONPATH", "PATH"):
        for entry in env.get(var, "").split(os.pathsep):
            if entry and Path(entry, "ranex").is_dir():
                findings.append(f"{var} names a ranex source root: {entry}")
    return findings


def probe_bare_environment(env: dict[str, str], cwd: Path,
                           python: str | None = None) -> dict[str, str]:
    """Measure the bare child's actual environment via an in-child canary."""

    try:
        result = subprocess.run(
            [python or str(RANEX_PY), "-c", BARE_CANARY], cwd=str(cwd),
            env=env, capture_output=True, text=True, check=False, timeout=60)
    except OSError as error:
        # A canary that cannot even launch is an unmeasurable bare arm —
        # refuse loudly rather than fall back to the intended environment.
        raise BareArmContaminated([
            f"canary interpreter could not be launched "
            f"({python or RANEX_PY}): {error}"]) from error
    if result.returncode != 0:
        raise BareArmContaminated([
            f"canary could not run in the bare child (exit "
            f"{result.returncode}): {result.stderr.strip()[:200]}"])
    return json.loads(result.stdout)


def assert_bare_environment(env: dict[str, str], cwd: Path,
                            python: str | None = None) -> dict[str, str]:
    """Probe in-child, then judge; contamination fails the run here (#114)."""

    child = probe_bare_environment(env, cwd, python=python)
    findings = contamination_findings(child)
    findings += [
        f"child environment deviates from the constructed one: {key}"
        for key in sorted(set(child) | set(env))
        if child.get(key) != env.get(key)
    ]
    if findings:
        raise BareArmContaminated(findings)
    return child


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=bench@ranex.invalid",
         "-c", "user.name=ranex-oss-bench", *args],
        capture_output=True, text=True, check=False,
    )


def pinned_python_has_pytest() -> tuple[bool, str]:
    """The real prerequisite, checked against the real pin."""
    candidates = [Path("/usr/bin/python3"), Path("/bin/python3")]
    last_miss = "no pinned python found in /usr/bin or /bin"
    for candidate in candidates:
        if not candidate.exists():
            continue
        probe = subprocess.run(
            [str(candidate), "-c", "import pytest"], capture_output=True,
            text=True, check=False,
        )
        if probe.returncode == 0:
            return True, str(candidate)
        last_miss = (
            f"{candidate} (the pinned interpreter) cannot import pytest — "
            "install it system-wide (e.g. `sudo apt install python3-pytest`) "
            "or run this study on a machine where the pinned python has pytest"
        )
    return False, last_miss


def copy_hidden_tests(tests_dir: Path, dest: Path) -> None:
    """Copy the task's hidden tests into dest. Directories included."""
    if not tests_dir.is_dir():
        return
    for item in sorted(tests_dir.iterdir()):
        if item.name == "__pycache__":
            continue
        target = dest / item.name
        if target.exists():
            raise AssertionError(f"hidden test collides with repo file: {item.name}")
        if item.is_dir():
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def gate_verdict_of(result: subprocess.CompletedProcess[str]) -> str:
    """Exit-code semantics plus the verdict line — never a substring hunt."""
    output = result.stdout
    if result.returncode == 0 and "PASS  gate=" in output:
        return "PASS"
    if result.returncode == 1 and "FAIL  gate=" in output:
        return "FAIL"
    return "ERROR"


def journal_verified(result: subprocess.CompletedProcess[str]) -> bool:
    return result.returncode == 0 and "chain=verified" in result.stdout


def build_governed_repo(task_dir: Path, out: Path, patch: str | Path | None,
                        claim_commands: list[tuple[str, list[str]]]) -> tuple[Path, str]:
    """Task repo + hidden tests (+patch) + VENDORED ranex + governance, committed.

    patch: "gold" applies the task's gold_patch.diff; None applies nothing;
    a Path applies that (agent-produced) diff.
    """
    repo = out / "repo"
    repo.mkdir(parents=True)
    for item in (task_dir / "repo").iterdir():
        if item.is_dir():
            shutil.copytree(item, repo / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, repo / item.name)
    copy_hidden_tests(task_dir / "tests", repo)

    # The nested repository must exist BEFORE any patch is applied. `git apply`
    # from a directory without its own .git discovers an enclosing worktree and
    # — by documented git behavior — silently ignores patched paths outside the
    # current directory, exiting 0 with nothing applied. With --out inside any
    # checkout that fed the gold arm the EMPTY stub (issue #89, F-034).
    assert _git(repo, "init", "-q").returncode == 0

    if patch is not None:
        patch_path = task_dir / "gold_patch.diff" if patch == "gold" else Path(patch)
        result = subprocess.run(
            ["git", "-C", str(repo), "apply", str(patch_path)],
            capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"patch failed to apply: {result.stderr[:300]}")

    assert _git(repo, "add", "-A").returncode == 0
    label = "gold" if patch == "gold" else ("agent solution" if patch else "no patch")
    assert _git(repo, "commit", "-qm", f"task base (+{label})").returncode == 0

    # Vendor the kernel source: the CLI governs the repo that CONTAINS it.
    shutil.copytree(RANEX_REPO / "src", repo / "src", dirs_exist_ok=True)
    shutil.copy2(RANEX_REPO / "pyproject.toml", repo / "pyproject.toml")
    shutil.copy2(RANEX_REPO / "uv.lock", repo / "uv.lock")

    private, public = generate_keypair()
    (out / "keys").mkdir(exist_ok=True)
    key_path = out / "keys" / "bench.key"
    key_path.write_text(private)
    key_path.chmod(0o600)

    claims_yaml = "".join(
        "      - claim_id: {}\n        command: [{}]\n".format(
            claim_id, ", ".join(json.dumps(part) for part in argv))
        for claim_id, argv in claim_commands
    )
    (repo / "governance").mkdir(exist_ok=True)
    (repo / "governance" / "producers.yaml").write_text(
        "producers:\n  {}: {}\n".format(PRODUCER, public))
    (repo / "governance" / "gates.yaml").write_text(
        "gates:\n  - gate_id: landing\n    rule_id: TASK_TESTS\n    blocking: true\n"
        "    required_claims:\n" + claims_yaml)
    # Evidence is gitignored, mirroring the kernel repo: records are bound to
    # the exact tree digest, so the file must never be committed.
    (repo / ".gitignore").write_text("governance/evidence.json\n")
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-qm",
                "vendor ranex kernel; governance: bench keyring and task gate").returncode == 0
    (repo / "governance" / "evidence.json").write_text("[]\n")
    return repo, str(key_path)


def _governed_environment(repo: Path, key_path: str) -> dict[str, str]:
    """The governed arm is governed ON PURPOSE: ambient base plus the
    vendored-kernel PYTHONPATH and the signing key (#114 arm 4 retention)."""

    env = dict(os.environ)
    env["RANEX_SIGNING_KEY"] = str(key_path)
    env["PYTHONPATH"] = str(Path(repo) / "src")
    return env


def _ranex(repo: Path, key_path: str, *args: str) -> subprocess.CompletedProcess[str]:
    repo = Path(repo).resolve()
    key = Path(key_path).resolve()
    env = _governed_environment(repo, str(key))
    return subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", *args],
        cwd=str(repo), env=env, capture_output=True, text=True, check=False,
        timeout=600,
    )


def governed_cycle(repo: Path, key_path: str,
                   claim_commands: list[tuple[str, list[str]]]) -> dict[str, Any]:
    runs = []
    for claim_id, argv in claim_commands:
        result = _ranex(repo, key_path, "run", "--claim", claim_id,
                        "--producer", PRODUCER, "--", *argv)
        runs.append({"claim": claim_id, "exit": result.returncode,
                     "error": (result.stderr.strip()[-300:]
                               if result.returncode != 0 else "")})
    verdict = _ranex(repo, key_path, "gate", "evaluate", "HEAD",
                     "--approver", APPROVER, "--journal", "governance/journal.sqlite3")
    journal = _ranex(repo, key_path, "journal", "verify",
                     "--journal", "governance/journal.sqlite3")
    return {"runs": runs, "gate_verdict": gate_verdict_of(verdict),
            "gate_output": verdict.stdout.strip()[:400] + verdict.stderr.strip()[-200:],
            "journal_verified": journal_verified(journal)}


def mode_plumbing(task_dir: Path, out: Path) -> dict[str, Any]:
    """Pipeline proof with a genuinely pinned tool. Positive repo: `git
    --version` claim -> expect gate PASS. Negative repo: claim bound to a
    failing real command (`git rev-parse --verify definitely-missing-ref`)
    -> expect gate FAIL. Real commands, real verdicts, zero task results."""
    started = time.perf_counter()
    positive_claims = [("plumbing-pass", ["git", "--version"])]
    negative_claims = [("plumbing-pass", ["git", "rev-parse", "--verify",
                                          "definitely-missing-ref-0000000"])]

    repo_pos, key_pos = build_governed_repo(task_dir, out / "positive",
                                            patch=None,
                                            claim_commands=positive_claims)
    pos = governed_cycle(repo_pos, key_pos, positive_claims)
    repo_neg, key_neg = build_governed_repo(task_dir, out / "negative",
                                            patch=None,
                                            claim_commands=negative_claims)
    neg = governed_cycle(repo_neg, key_neg, negative_claims)

    report = {
        "schema": "ranex-oss-bench-plumbing-v1",
        "task": task_dir.name,
        "note": "pipeline validation on a real task repo via pinned git; "
                "NOT a benchmark result",
        "positive": pos, "negative": neg,
        "elapsed_s": round(time.perf_counter() - started, 3),
    }
    ok = (pos["gate_verdict"] == "PASS" and pos["journal_verified"]
          and neg["gate_verdict"] == "FAIL" and neg["journal_verified"])
    report["validation"] = "PASS" if ok else "FAIL"
    (out / "plumbing.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"plumbing: positive gate {pos['gate_verdict']} (journal "
          f"{'verified' if pos['journal_verified'] else 'BROKEN'}), "
          f"negative gate {neg['gate_verdict']} (journal "
          f"{'verified' if neg['journal_verified'] else 'BROKEN'}) -> "
          f"VALIDATION {report['validation']}")
    return report


def run_bare_arm(task_dir: Path, entries: list[dict[str, Any]],
                 env: dict[str, str] | None = None,
                 python: str | None = None) -> dict[str, Any]:
    """Bare ground truth: the task's own commands, probe-first (#114).

    Before every command the canary runs in-child with the exact environment
    that command will receive; contamination fails the whole run instead of
    producing a cleaner diff. The returned ground truth records the
    environment actually used — measured in the child, not intended by the
    driver.
    """
    env = bare_environment() if env is None else env
    probes = 0
    child_env: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        bare_repo = Path(tmp) / "repo"
        shutil.copytree(task_dir / "repo", bare_repo)
        copy_hidden_tests(task_dir / "tests", bare_repo)
        gold = subprocess.run(
            ["git", "-C", str(bare_repo), "apply", str(task_dir / "gold_patch.diff")],
            capture_output=True, text=True, check=False)
        bare_gold, bare_empty = [], []
        targets = [("gold", bare_gold, gold.returncode == 0),
                   ("empty", bare_empty, True)]
        for arm, sink, _ in targets:
            for entry in entries:
                if arm == "empty":
                    subprocess.run(["git", "-C", str(bare_repo), "checkout", "--", "."],
                                   capture_output=True, check=False)
                    subprocess.run(["git", "-C", str(bare_repo), "clean", "-fdq"],
                                   capture_output=True, check=False)
                    shutil.rmtree(bare_repo)
                    shutil.copytree(task_dir / "repo", bare_repo)
                    copy_hidden_tests(task_dir / "tests", bare_repo)
                child_env = assert_bare_environment(env, bare_repo, python=python)
                probes += 1
                result = subprocess.run(shlex.split(entry["cmd"]), cwd=str(bare_repo),
                                        capture_output=True, text=True, check=False,
                                        timeout=300, env=env)
                sink.append({"name": entry["name"], "exit": result.returncode})
    metadata = json.loads((task_dir / "metadata.json").read_text())
    canonical = json.dumps(child_env, sort_keys=True, separators=(",", ":"))
    return {
        "schema": "ranex-oss-bench-bare-v1", "task": metadata["id"],
        "gold": bare_gold, "empty": bare_empty,
        "environment": {
            "probe": "in-child canary (two_arm.BARE_CANARY) before every "
                     "command; the receipt records the environment used",
            "probes": probes,
            "child_env": child_env,
            "child_env_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            "contamination_findings": contamination_findings(child_env),
        },
    }


def mode_tasks(task_dir: Path, out: Path,
               contaminate: str | None = None) -> int:
    ok, detail = pinned_python_has_pytest()
    if not ok:
        print(f"PREREQUISITE-MISSING: {detail}")
        print("The governed arm refuses to run without it; no results are "
              "invented. The bare arm still runs for ground truth.")
    metadata = json.loads((task_dir / "metadata.json").read_text())
    entries = metadata["tests"]["fail_to_pass"]

    # Bare arm always runs: real ground truth from the task's own commands,
    # from a DECLARED minimal environment with the canary proving bareness
    # before every command (#114). The ranex venv interpreter stays first on
    # PATH as an explicit, asserted entry — the deliberate bare-agent choice.
    try:
        bare = run_bare_arm(task_dir, entries,
                            env=bare_environment(contaminate))
    except BareArmContaminated as caught:
        print(f"BARE-ARM-CONTAMINATED: refusing the bare arm — "
              f"{'; '.join(caught.findings)}", file=sys.stderr)
        print("No ground truth is written; a contaminated bare arm fails "
              "loudly instead of reporting a cleaner diff.", file=sys.stderr)
        return 3
    print(f"[gold ] bare {sum(1 for r in bare['gold'] if r['exit'] == 0)}/{len(entries)}")
    print(f"[empty] bare {sum(1 for r in bare['empty'] if r['exit'] == 0)}/{len(entries)}")
    (out / "bare_ground_truth.json").write_text(json.dumps(bare, indent=2) + "\n")

    if not ok:
        return 4

    claim_commands = []
    for entry in entries:
        _env, argv, node_ids = parse_cmd(entry["cmd"])
        if not node_ids:
            print(f"cmd yields no test node ids, refusing: {entry['cmd']!r}")
            return 2
        claim_commands.append((entry["name"], pinned_argv(argv, PINNED_PYTHON)))
    arms = []
    for arm, patch in (("gold", "gold"), ("empty", None)):
        started = time.perf_counter()
        repo, key_path = build_governed_repo(task_dir, out / arm, patch,
                                             claim_commands)
        cycle = governed_cycle(repo, key_path, claim_commands)
        # Retain the governed environment (#114 arm 4): names plus the two
        # governance values, recorded by shape because the scratch-absolute
        # paths differ per run — full ambient values stay out of the repo.
        governed_env = _governed_environment(repo, key_path)
        (out / arm / "governed_environment.json").write_text(json.dumps({
            "note": "deliberately governed: ambient base plus the "
                    "vendored-kernel PYTHONPATH and the signing key",
            "variable_names": sorted(governed_env),
            "ambient_variable_count": len(governed_env) - 2,
            "PYTHONPATH": "src (vendored kernel; scratch-absolute per run)",
            "RANEX_SIGNING_KEY": "keys/bench.key (scratch-absolute per run)",
            "governed_env_sha256": hashlib.sha256(json.dumps(
                {"variable_names": sorted(governed_env)},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }, indent=2) + "\n")
        arms.append({"arm": arm, "gate_verdict": cycle["gate_verdict"],
                     "journal_verified": cycle["journal_verified"],
                     "runs": cycle["runs"],
                     "elapsed_s": round(time.perf_counter() - started, 3),
                     "simulation": "gold-patch (no model) — NOT a model benchmark"})
        print(f"[{arm:5}] gate {arms[-1]['gate_verdict']} · journal "
              f"{'verified' if arms[-1]['journal_verified'] else 'BROKEN'} · "
              f"{arms[-1]['elapsed_s']}s")
    report = {"schema": "ranex-oss-bench-validation-v1", "task": metadata["id"],
              "arms": arms}
    (out / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
    valid = arms[0]["gate_verdict"] == "PASS" and arms[1]["gate_verdict"] == "FAIL" \
        and all(a["journal_verified"] for a in arms)
    print("VALIDATION", "PASS" if valid else "FAIL")
    return 0 if valid else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True)
    parser.add_argument("--suite", default="v1")
    parser.add_argument("--mode", choices=("tasks", "plumbing"), default="tasks")
    parser.add_argument("--contaminate",
                        choices=tuple(CONTAMINATIONS), default=None,
                        help="deliberately contaminate the bare arm through "
                             "one channel to prove the detector catches it "
                             "(negative control; the run must exit 3)")
    parser.add_argument("--vulcan-root", type=Path, default=DEFAULT_VULCAN)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    task_dir = args.vulcan_root / "tasks" / args.suite / args.task
    if not task_dir.is_dir():
        print(f"no such task: {task_dir}", file=sys.stderr)
        return 2
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.mode == "plumbing":
        report = mode_plumbing(task_dir, args.out)
        return 0 if report["validation"] == "PASS" else 1
    return mode_tasks(task_dir, args.out, contaminate=args.contaminate)


if __name__ == "__main__":
    raise SystemExit(main())
