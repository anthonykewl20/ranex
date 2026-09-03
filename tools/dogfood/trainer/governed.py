"""Corrected governed-cycle runner for the trainer.

Same end-to-end pipeline run_divergence.py proved (vendored kernel, pristine
frozen manifest, results-bound claim, signed evidence, gate, journal), with
the audit's harness defects fixed at the source:

  - node ids come from the corpus parser, never from argv[3] (C-01);
  - every scratch path is inside the caller's tempdir, no /tmp globals (C-14);
  - hidden-test directories are copied with copytree, not copy2 (C-03);
  - verdicts are read from EXIT CODES, never from prose substring (C-05);
  - each step's failure is data, not a crash.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

RANEX_REPO = Path(__file__).resolve().parents[3]
RANEX_PY = RANEX_REPO / ".venv" / "bin" / "python"
_OSS_BENCH = Path(__file__).resolve().parents[1] / "oss_bench"
sys.path.insert(0, str(_OSS_BENCH))
sys.path.insert(0, str(RANEX_REPO / "src"))

from two_arm import PRODUCER  # noqa: E402  (proven constants, not the buggy parsing)

APPROVER = "dogfood-trainer-approver"
GATE_PASS, GATE_FAIL, GATE_ERROR = "PASS", "FAIL", "ERROR"


def governed_equivalent_env(scratch: Path) -> dict[str, str]:
    """The EXACT environment a confined child sees under `ranex run`
    (cli/main.py: `PATH` pinned dirs, scratch `HOME`/`TMPDIR`, `LANG`,
    git system-config opt-outs). Probes and labels are only sound when
    they run under this env — anything weaker (e.g. merely dropping
    PYTHONPATH) lets env-dependent tests pass preflight and then
    false-diverge under governance.
    """
    home = scratch / "governed-home"
    tmp = scratch / "governed-tmp"
    home.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "LANG": "C.UTF-8",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_ATTRS_NOSYSTEM": "1",
    }


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.email=trainer@ranex.invalid",
         "-c", "user.name=ranex-trainer", *args],
        capture_output=True, text=True, check=False,
    )


def _env_with(extra: dict[str, str] | None) -> dict[str, str]:
    env = dict(os.environ)
    if extra:
        env.update(extra)
    return env


def env_extra_for(env_assignments: list[str]) -> dict[str, str]:
    """'PYTHONPATH=src:_vendor' -> {'PYTHONPATH': 'src:_vendor'} (last wins)."""
    result: dict[str, str] = {}
    for assignment in env_assignments:
        key, _, value = assignment.partition("=")
        result[key] = value
    return result


def _ranex(repo: Path, key_path: str, *args: str,
           timeout: int = 600,
           env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = _env_with(env_extra)
    env["RANEX_SIGNING_KEY"] = key_path
    # COMBINE, never clobber: the vendored kernel's src must come after the
    # task's own PYTHONPATH (e.g. PYTHONPATH=lib repos import their vendored
    # libraries from there — overwriting it silently pointed their tests at
    # system packages).
    kernel_src = str(repo / "src")
    task_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{task_path}:{kernel_src}" if task_path else kernel_src
    return subprocess.run(
        [str(RANEX_PY), "-m", "ranex.cli.main", *args],
        cwd=str(repo), env=env, capture_output=True, text=True, check=False,
        timeout=timeout,
    )


def _copy_tree(src: Path, dst: Path) -> None:
    for item in sorted(src.iterdir()):
        if item.name == "__pycache__":
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def materialize_repo(task_dir: Path, dst: Path) -> None:
    """Repo content from the corpus's on-disk shape: `repo/` dir or tarball."""
    repo_dir = task_dir / "repo"
    if repo_dir.is_dir():
        _copy_tree(repo_dir, dst)
        return
    snapshot = task_dir / "repo_snapshot.tar.gz"
    if snapshot.is_file():
        import tarfile

        with tarfile.open(snapshot, "r:gz") as archive:
            archive.extractall(dst, filter="data")
        return
    raise AssertionError(f"task carries neither repo/ nor repo_snapshot.tar.gz")


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


class GovernedRepo:
    """A governed task repo built from corpus truth; commits are explicit."""

    def __init__(self, task_dir: Path, out: Path, node_ids: list[str],
                 alt_manifest_suite: list[str] | None = None,
                 env_extra: dict[str, str] | None = None) -> None:
        from ranex.foundation.signing import generate_keypair

        self.env_extra = env_extra or {}

        self.root = out / "repo"
        self.root.mkdir(parents=True)
        materialize_repo(task_dir, self.root)
        tests_dir = task_dir / "tests"
        if tests_dir.is_dir():
            for item in sorted(tests_dir.iterdir()):
                if item.name == "__pycache__":
                    continue
                if (self.root / item.name).exists():
                    raise AssertionError(f"hidden test collides with repo file: {item.name}")
                if item.is_dir():
                    shutil.copytree(item, self.root / item.name)
                else:
                    shutil.copy2(item, self.root / item.name)
        assert _git(self.root, "init", "-q").returncode == 0
        assert _git(self.root, "add", "-A").returncode == 0
        assert _git(self.root, "commit", "-qm", "task base + pristine tests").returncode == 0

        # Freeze the manifest under CONFINEMENT-EQUIVALENT conditions (the
        # exact governed child env, not a weaker approximation): the frozen
        # ID set must be collectable the same way the governed run will.
        with tempfile.NamedTemporaryFile(dir=out, suffix=".xml", delete=False) as probe:
            probe_path = Path(probe.name)
        try:
            run = subprocess.run(
                ["/usr/bin/python3", "-m", "pytest", "-q", f"--junitxml={probe_path}",
                 *sorted(set(node_ids))],
                cwd=str(self.root), capture_output=True, text=True, check=False,
                timeout=120, env=governed_equivalent_env(out),
            )
            _ = run  # pre-fix tests are red by contract; the manifest records IDs only
            from ranex.foundation.suite_results import freeze_manifest

            manifest = freeze_manifest(probe_path.read_bytes(), expected_skips={})
        finally:
            probe_path.unlink(missing_ok=True)
        # The manifest must cover the contracted tests. A probe that
        # collected nothing (pytest usage error, crashed collection) still
        # yields a VALID empty manifest — which the gate would satisfy
        # vacuously. Spelling subtlety: the kernel synthesizes junit ids as
        # `classname.py::name`, so a class-nested pytest id (file.py::Cls::
        # test) freezes as `file/Cls.py::test` — a different spelling of
        # the same test. Exact set equality is demanded only when every
        # contracted id is plain top-level shape; otherwise coverage is
        # asserted at the test-name level.
        manifest_ids = set(manifest["suite"])
        assert manifest_ids, "frozen manifest is empty (probe collected nothing)"
        plain = [nid for nid in set(node_ids) if nid.count("::") == 1]
        if len(plain) == len(set(node_ids)):
            assert manifest_ids == set(node_ids), (
                f"frozen manifest does not match the contracted ids: "
                f"missing={sorted(set(node_ids) - manifest_ids)[:3]} "
                f"extra={sorted(manifest_ids - set(node_ids))[:3]}"
            )
        else:
            manifest_names = {mid.rsplit("::", 1)[-1] for mid in manifest_ids}
            contracted_names = {nid.rsplit("::", 1)[-1] for nid in node_ids}
            missing = sorted(contracted_names - manifest_names)
            assert not missing, (
                f"frozen manifest misses contracted test names: {missing[:3]}"
            )
        (self.root / "governance").mkdir(exist_ok=True)
        (self.root / "governance" / "suite_manifest.json").write_bytes(_canonical(manifest))
        if alt_manifest_suite is not None:
            # A second COMMITTED manifest with a different suite: legal input
            # (review saw it), used by the cross-bind exercise — evidence
            # summarised against this while the claim binds the pristine one.
            alt = {"suite": sorted(set(alt_manifest_suite)), "expected_skips": {}}
            (self.root / "governance" / "alt-manifest.json").write_bytes(_canonical(alt))

        # Vendor the kernel: governed_repository_root() resolves the repo that
        # CONTAINS the CLI (F-003), so the subject carries its own copy.
        shutil.copytree(RANEX_REPO / "src", self.root / "src", dirs_exist_ok=True)
        shutil.copy2(RANEX_REPO / "pyproject.toml", self.root / "pyproject.toml")
        shutil.copy2(RANEX_REPO / "uv.lock", self.root / "uv.lock")

        private, public = generate_keypair()
        (out / "keys").mkdir(exist_ok=True)
        self.key_path = out / "keys" / "trainer.key"
        self.key_path.write_text(private)
        self.key_path.chmod(0o600)
        (self.root / "governance" / "producers.yaml").write_text(
            "producers:\n  {}: {}\n".format(PRODUCER, public))
        self.junit_argv = [
            "/usr/bin/python3", "-m", "pytest", "-q",
            "--junitxml=governance/suite_results.xml", *sorted(set(node_ids)),
        ]
        (self.root / "governance" / "gates.yaml").write_text(
            "gates:\n  - gate_id: landing\n    rule_id: TASK_TESTS\n    blocking: true\n"
            "    required_claims:\n      - claim_id: tests-executed\n"
            "        command: [{}]\n"
            "        results_artifact: governance/suite_results.xml\n".format(
                ", ".join(json.dumps(part) for part in self.junit_argv)))
        (self.root / ".gitignore").write_text(
            "governance/evidence.json\ngovernance/suite_results.xml\n"
            "__pycache__/\n*.pyc\n.pytest_cache/\n")
        assert _git(self.root, "add", "-A").returncode == 0
        assert _git(self.root, "commit", "-qm",
                    "governance: pristine frozen manifest + results-bound gate").returncode == 0

    def apply_patch(self, patch: Path | None, message: str) -> bool:
        """Apply a diff and commit it. False if it makes no net change."""
        if patch is not None:
            result = subprocess.run(
                ["git", "-C", str(self.root), "apply", str(patch)],
                capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise AssertionError(f"patch failed to apply: {result.stderr[:200]}")
        status = _git(self.root, "status", "--porcelain")
        if not status.stdout.strip():
            return False
        assert _git(self.root, "add", "-A").returncode == 0
        assert _git(self.root, "commit", "-qm", message).returncode == 0
        return True

    def commit_working_tree(self, message: str) -> bool:
        status = _git(self.root, "status", "--porcelain")
        if not status.stdout.strip():
            return False
        assert _git(self.root, "add", "-A").returncode == 0
        assert _git(self.root, "commit", "-qm", message).returncode == 0
        return True

    def run_claim(self, *extra_run_args: str) -> dict[str, Any]:
        return self._capture(self._ranex(
            "run", "--claim", "tests-executed", "--producer", PRODUCER,
            *extra_run_args, "--", *self.junit_argv))

    def evaluate(self) -> dict[str, Any]:
        return self._capture(self._ranex(
            "gate", "evaluate", "HEAD", "--approver", APPROVER,
            "--journal", "governance/journal.sqlite3", timeout=120))

    def verify_journal(self) -> dict[str, Any]:
        return self._capture(self._ranex(
            "journal", "verify", "--journal", "governance/journal.sqlite3", timeout=120))

    def _ranex(self, *args: str, timeout: int = 600) -> subprocess.CompletedProcess[str]:
        return _ranex(self.root, str(self.key_path), *args, timeout=timeout,
                      env_extra=self.env_extra)

    @staticmethod
    def _capture(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
        return {"exit": result.returncode,
                "stdout": result.stdout.strip()[:1500],
                "stderr": result.stderr.strip()[-400:]}


def verdict_of(gate_result: dict[str, Any]) -> str:
    """Exit-code semantics PLUS the verdict line: 0→PASS, 1→FAIL only when
    the output actually carries `PASS  gate=`/`FAIL  gate=` (an uncaught
    crash also exits 1 and must never be graded as a judged FAIL), anything
    else is an error, never a guess."""
    output = gate_result["stdout"]
    if gate_result["exit"] == 0 and "PASS  gate=" in output:
        return GATE_PASS
    if gate_result["exit"] == 1 and "FAIL  gate=" in output:
        return GATE_FAIL
    return GATE_ERROR


def journal_ok(journal_result: dict[str, Any]) -> bool:
    return journal_result["exit"] == 0
