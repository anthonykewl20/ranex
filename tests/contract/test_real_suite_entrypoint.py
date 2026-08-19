"""SLICE-055 — real-suite entrypoint and subprocess coverage harness contracts.

Frozen RED before any implementation exists (spec-prd stage 2, step 6;
ADR-032 docs/adr/ADR-032-real-e2e-suite-framework.md; issue #35). The frame
modules named below do not exist yet — the failures this file produces
against the pre-implementation tree ARE the red. From the freeze commit on,
this file is read-only to the implementer.

Interfaces frozen here (spelled in full in tests/contract/test_prereq_gates.py
and in docs/slices/SLICE-055-real-e2e-suite-framework.md):

- README carries one section `## The real-e2e suite entrypoint` documenting
  the exact command, the coverage env vars, and the duration budget. The
  section itself is implementation; this file asserts its existence and
  shape only.
- pyproject.toml gains [tool.coverage] run/report: source=src/ranex,
  parallel=true, a fail-under threshold.
- tests/e2e/_prereqs.py wiring: wire_child_environment(base, *,
  coverage_home=None) APPENDS the hook dir to the child PYTHONPATH — last,
  never replacing it (the spine's ranex() replacement is the recorded
  anti-pattern), sets absolute COVERAGE_PROCESS_START naming an existing
  config, and sets COVERAGE_FILE to <coverage_home>/.coverage where the
  default home is .local/ranex-e2e/coverage under the repository root.
- combine_coverage(home) runs `coverage combine --keep` and raises
  CoverageDataMissing (loudly) when a frame-wired child produced no
  parallel data file; report_unmeasured(label) is the non-alarming path
  for children the frame does not wire.
- The joint trace+coverage case: one real traced, coverage-measured CLI
  subprocess over a real governed subject — out-of-governed-root trace
  artifact, version-first stream, byte-identical governed outputs,
  RANEX_TRACE* absent from the observed command's environment, target
  lines still counted in the combined report.
- AC5: the manifest round-trip is the existing `ranex suite freeze`
  ceremony; the honest red form is "the two frozen files' IDs are absent
  from governance/suite_manifest.json today" and turns green only when
  the ceremony registers them without hand edits.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
E2E_DIR = REPO_ROOT / "tests" / "e2e"
CLI = (sys.executable, "-m", "ranex.cli.main")
TRACE_VARIABLES = ("RANEX_TRACE", "RANEX_TRACE_EVENT", "RANEX_TRACE_PARENT_SID")

ENTRYPOINT_HEADING = "## The real-e2e suite entrypoint"
_DURATION_BUDGET = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:ms|seconds?|secs?|minutes?|mins?|hours?)\b"
)


def _frame():
    """The frame's library module, imported lazily so the README, pyproject
    and manifest assertions below fail as clean failures — not collection
    errors — on the pre-implementation tree."""

    sys.path.insert(0, str(E2E_DIR))
    import _prereqs  # noqa: PLC0415

    return _prereqs


# --- 1. the documented entrypoint ---------------------------------------------


def test_readme_documents_the_real_suite_entrypoint() -> None:
    """One README section carries the exact command, the coverage env vars,
    and the duration budget (AC1's documentation half)."""

    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(
        rf"^{re.escape(ENTRYPOINT_HEADING)}\s*\n(.*?)(?=^## |\Z)",
        readme,
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None, (
        f"README.md must carry the section '{ENTRYPOINT_HEADING}' — the "
        "one documented full-suite entrypoint (issue #35 ownership)"
    )
    body = section.group(1)
    fence = re.search(r"```[a-z]*\n(.*?)```", body, re.DOTALL)
    assert fence is not None, "the section must carry a fenced command block"
    command = fence.group(1)
    assert "pytest" in command and "tests/e2e" in command, (
        f"the documented command must run the real suite: {command!r}"
    )
    for variable in ("COVERAGE_PROCESS_START", "COVERAGE_FILE"):
        assert variable in body, (
            f"the section must document the {variable} env var the harness "
            "wires into every child"
        )
    assert _DURATION_BUDGET.search(body) is not None, (
        "the section must state the expected duration budget"
    )


# --- 2. the coverage config block --------------------------------------------


def test_pyproject_freezes_the_coverage_block() -> None:
    """[tool.coverage] run/report: source=src/ranex, parallel=true, and a
    fail-under threshold (ADR-032's subprocess-coverage decision)."""

    config = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    coverage = config.get("tool", {}).get("coverage")
    assert isinstance(coverage, dict), (
        "pyproject.toml must carry a [tool.coverage] block"
    )
    run = coverage.get("run")
    assert isinstance(run, dict), "[tool.coverage.run] is required"
    source = run.get("source")
    sources = [source] if isinstance(source, str) else list(source or [])
    assert "src/ranex" in sources, f"coverage source must name src/ranex: {sources}"
    assert run.get("parallel") is True, "coverage run.parallel must be true"
    report = coverage.get("report")
    assert isinstance(report, dict), "[tool.coverage.report] is required"
    fail_under = report.get("fail_under")
    assert isinstance(fail_under, int) and not isinstance(fail_under, bool), (
        f"a numeric fail_under threshold is required, got {fail_under!r}"
    )
    assert fail_under >= 1, "a zero fail-under threshold measures nothing"


# --- 3. child-environment wiring ----------------------------------------------


def test_wire_child_environment_appends_hook_last_and_keeps_coverage_absolute(
    tmp_path: Path,
) -> None:
    """Append-never-replace: the hook dir rides LAST on the child's
    PYTHONPATH, the coverage config is named by an absolute existing path,
    and every process's parallel data file lands in one shared home
    (default .local/ranex-e2e/coverage/.coverage)."""

    frame = _frame()
    hook = Path(frame.HOOK_DIR)
    assert hook == E2E_DIR / "coverage", "the hook dir is tests/e2e/coverage"
    assert (hook / "sitecustomize.py").is_file(), (
        "tests/e2e/coverage/sitecustomize.py is the subprocess hook"
    )

    base = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": "/some/base"}
    wired = frame.wire_child_environment(dict(base), coverage_home=tmp_path)

    entries = wired["PYTHONPATH"].split(os.pathsep)
    assert entries[0] == "/some/base", (
        f"wiring must APPEND to PYTHONPATH, never replace it: {entries!r}"
    )
    assert entries[-1] == str(hook), (
        f"the hook dir must be appended LAST so a later sitecustomize "
        f"cannot shadow it: {entries!r}"
    )
    assert wired["PATH"] == base["PATH"], "unrelated environment is preserved"

    start = wired.get("COVERAGE_PROCESS_START")
    assert start and Path(start).is_absolute() and Path(start).is_file(), (
        f"COVERAGE_PROCESS_START must name an absolute, existing config: {start!r}"
    )
    assert wired.get("COVERAGE_FILE") == str(tmp_path / ".coverage"), (
        "an overridden home pins COVERAGE_FILE to <home>/.coverage"
    )

    default_home = frame.default_coverage_home()
    assert default_home == REPO_ROOT / ".local" / "ranex-e2e" / "coverage", (
        "the shared coverage home is .local/ranex-e2e/coverage (ignored "
        ".local/* territory, ADR-032)"
    )
    default_wired = frame.wire_child_environment(dict(base))
    assert default_wired["COVERAGE_FILE"] == str(default_home / ".coverage"), (
        "the default wiring shares one COVERAGE_FILE home across children"
    )


# --- 4. the coverage harness proof (AC2, toy-real shape) ----------------------


def _coverage_data_hash(home: Path) -> str:
    """A content hash over the combined data: measured files and their
    executed line numbers, canonically serialized."""

    from coverage import CoverageData  # noqa: PLC0415 — dev dependency, pinned

    data = CoverageData(basename=str(home / ".coverage"))
    data.read()
    snapshot = {
        measured: sorted(data.lines(measured) or [])
        for measured in sorted(data.measured_files())
    }
    return hashlib.sha256(
        json.dumps(snapshot, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _cli_lines(home: Path) -> tuple[str, list[int]]:
    from coverage import CoverageData  # noqa: PLC0415

    data = CoverageData(basename=str(home / ".coverage"))
    data.read()
    for measured in sorted(data.measured_files()):
        if measured.endswith("src/ranex/cli/main.py"):
            return measured, sorted(data.lines(measured) or [])
    raise AssertionError(
        f"no measured file under src/ranex/cli/main.py in {home}; measured: "
        f"{sorted(data.measured_files())}"
    )


def test_real_subprocess_coverage_counts_cli_lines_and_combine_keep_is_idempotent(
    tmp_path: Path,
) -> None:
    """AC2: a REAL subprocess running real ranex code under the frame's
    wiring has its target lines counted in the combined report, and
    repeated `coverage combine --keep` over the retained inputs yields an
    identical data hash."""

    frame = _frame()
    home = tmp_path / "cov"
    home.mkdir()
    base = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "PYTHONPATH": str(REPO_ROOT / "src"),
    }
    wired = frame.wire_child_environment(dict(base), coverage_home=home)
    child = subprocess.run(
        [*CLI, "--help"],
        cwd=str(REPO_ROOT),
        env=wired,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert child.returncode == 0, child.stderr

    parallel = [p for p in home.glob(".coverage.*") if p.name != ".coverage"]
    assert parallel, (
        "parallel=true must leave a suffixed data file (.coverage.<host>."
        f"<pid>.<rand>) in the shared home; home has {sorted(p.name for p in home.iterdir())}"
    )

    combined = frame.combine_coverage(home)
    assert Path(combined).is_absolute() and Path(combined).is_file()

    measured, lines = _cli_lines(home)
    assert "src/ranex/cli/main.py" in measured
    assert lines, "the CLI child's executed lines must appear with numbers"

    first = _coverage_data_hash(home)
    frame.combine_coverage(home)  # combine --keep again over retained inputs
    assert _coverage_data_hash(home) == first, (
        "repeated coverage combine --keep over retained immutable inputs "
        "must reproduce identical combined data (ADR-032 idempotence)"
    )
    _, lines_again = _cli_lines(home)
    assert lines_again == lines


def test_no_data_detection_is_loud_for_wired_children_only() -> None:
    """Sad path 7, scoped: a frame-wired child whose data file is absent
    fails loudly (never a fake zero); children the frame does not wire are
    reported unmeasured and must not alarm."""

    frame = _frame()
    assert issubclass(frame.CoverageDataMissing, RuntimeError), (
        "the no-data detection is a loud failure, not a silent zero report"
    )
    empty = Path(tempfile.mkdtemp(prefix="ranex-e2e-empty-"))
    try:
        with pytest.raises(frame.CoverageDataMissing, match=re.escape(str(empty))):
            frame.combine_coverage(empty)
    finally:
        shutil.rmtree(empty, ignore_errors=True)

    report = frame.report_unmeasured("clone-child-1")
    assert isinstance(report, str) and "unmeasured" in report.lower(), (
        f"unwired children are reported unmeasured, never alarming: {report!r}"
    )


# --- 5. the joint trace+coverage case (D5) ------------------------------------

_CHECK_SCRIPT = "grep -qx content file.txt\n"
_GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["sh", "check.sh"]
"""


class _Subject:
    """A real governed repository, canonical clone-judges-clone construction
    (tests/e2e/test_gating_real_suite.py / test_trace_invariance.py): the
    CLI tree is vendored INTO the subject so the subject's own CLI judges
    the subject."""

    def __init__(self, root: Path) -> None:
        from ranex.foundation.signing import generate_keypair

        # Resolved so coverage's stored paths and this test's expectations
        # cannot diverge through a symlinked temporary directory.
        self.root = root.resolve()
        root.mkdir(parents=True, exist_ok=True)
        private, public = generate_keypair()
        self.key = root.parent / "worker.key"
        self.key.write_text(private + "\n", encoding="utf-8")
        self.key.chmod(0o600)
        (root / "file.txt").write_text("content\n", encoding="utf-8")
        (root / "check.sh").write_text(_CHECK_SCRIPT, encoding="utf-8")
        (root / "gates.yaml").write_text(_GATES, encoding="utf-8")
        (root / "producers.yaml").write_text(
            f"producers:\n  worker: {public}\n", encoding="utf-8"
        )
        (root / ".gitignore").write_text("evidence.json\n", encoding="utf-8")
        shutil.copytree(REPO_ROOT / "src" / "ranex", root / "src" / "ranex")
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        for key, value in (("user.email", "t@example.invalid"), ("user.name", "test")):
            subprocess.run(["git", "-C", str(root), "config", key, value], check=True)
        subprocess.run(["git", "-C", str(root), "add", "."], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "initial"], check=True
        )

    def base_env(self) -> dict[str, str]:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", str(Path.home())),
            "PYTHONPATH": str(self.root / "src"),
            "RANEX_SIGNING_KEY": str(self.key),
        }
        for name in TRACE_VARIABLES:
            env.pop(name, None)
        return env

    def cli(
        self, argv: list[str], env: dict[str, str]
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [*CLI, *argv],
            cwd=str(self.root),
            env=env,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )

    def reset_outputs(self) -> None:
        for relative in ("evidence.json", "governance/journal.sqlite3"):
            leftover = self.root / relative
            if leftover.exists():
                leftover.unlink()

    def run_spine(
        self, env: dict[str, str]
    ) -> dict[str, object]:
        """One `ranex run` over the real subject, captured for neutrality."""

        self.reset_outputs()
        ran = self.cli(
            [
                "run", "--claim", "tests-executed", "--producer", "worker",
                "--repository", ".", "--evidence", "evidence.json",
                "--producers", "producers.yaml", "--", "sh", "check.sh",
            ],
            env=env,
        )
        evidence = self.root / "evidence.json"
        assert evidence.is_file(), ran.stderr
        return {
            "run_rc": ran.returncode,
            "run_out": ran.stdout,
            "run_err": ran.stderr,
            "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        }


def test_joint_trace_and_coverage_case(
    tmp_path: Path,
) -> None:
    """D5 (ADR-032 Confirmation): ONE real traced, coverage-measured CLI
    subprocess. The trace artifact lands out of every governed root with a
    version-first stream; the governed outputs stay byte-identical to the
    untraced baseline; RANEX_TRACE* never reach the observed command; and
    the child's target lines still land in the combined report."""

    frame = _frame()
    subject = _Subject(tmp_path / "governed")
    home = tmp_path / "cov"
    home.mkdir()
    # Outside the subject's governed root AND outside this checkout's root:
    # an out-of-governed-root trace target (ADR-032/ADR-031 admission rule).
    trace_target = tmp_path / "trace" / "joint.jsonl"
    trace_target.parent.mkdir()

    baseline = subject.run_spine(subject.base_env())
    assert baseline["run_rc"] == 0, baseline["run_err"]

    traced_env = frame.wire_child_environment(
        subject.base_env(), coverage_home=home
    )
    traced_env["RANEX_TRACE"] = str(trace_target)
    traced = subject.run_spine(traced_env)
    assert traced["run_rc"] == 0, traced["run_err"]

    # (a) the trace artifact exists, version-first, with real stage events
    assert trace_target.is_file(), "the traced child must admit its target"
    events = [
        json.loads(line)
        for line in trace_target.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert events and events[0]["event"] == "version", (
        "the version event is the first write on each admitted target"
    )
    assert any(event["event"] == "stage" for event in events), (
        "the CLI's stage boundary must emit into the admitted target"
    )

    # (b) verdict neutrality: governed outputs byte-identical to untraced
    for key in ("run_rc", "run_out", "run_err", "evidence_sha256"):
        assert traced[key] == baseline[key], (
            f"tracing+coverage changed {key}: baseline={baseline[key]!r} "
            f"traced={traced[key]!r}"
        )

    # (c) the propagation boundary: an observed command that branches on
    # the trace variables never sees them (branching-marker probe)
    marker = tmp_path / "leaked-marker"
    probe = (
        'if [ -n "$RANEX_TRACE$RANEX_TRACE_EVENT$RANEX_TRACE_PARENT_SID" ]; '
        f"then touch {marker}; fi"
    )
    subject.reset_outputs()
    probed = subject.cli(
        [
            "run", "--claim", "tests-executed", "--producer", "worker",
            "--repository", ".", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--", "sh", "-c", probe,
        ],
        env=traced_env,
    )
    assert probed.returncode == 0, probed.stderr
    assert not marker.exists(), (
        "RANEX_TRACE* leaked into the observed command's environment"
    )

    # (d) the traced child's lines still count in the combined report
    assert list(home.glob(".coverage.*")), (
        "the coverage-wired CLI children must leave parallel data files"
    )
    frame.combine_coverage(home)
    measured, lines = _cli_lines(home)
    assert measured.startswith(str(subject.root)), (
        f"the measured CLI file belongs to the subject tree: {measured}"
    )
    assert lines, (
        "the traced+measured CLI subprocess's target lines must appear in "
        "the combined report"
    )


# --- 6. AC5 — manifest round-trip through the freeze ceremony ------------------

_FROZEN_FILES = (
    REPO_ROOT / "tests" / "contract" / "test_prereq_gates.py",
    REPO_ROOT / "tests" / "contract" / "test_real_suite_entrypoint.py",
)


def test_both_new_contract_files_are_in_the_frozen_manifest() -> None:
    """AC5: every test ID of the two frozen files round-trips into
    governance/suite_manifest.json through `ranex suite freeze` — no hand
    edits. Honest red form: the IDs are absent today; green only after the
    post-implementation ceremony."""

    collected = subprocess.run(
        [
            sys.executable, "-m", "pytest", "-q", "--collect-only",
            *[str(path.relative_to(REPO_ROOT)) for path in _FROZEN_FILES],
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    nodeids = {
        line.strip()
        for line in collected.stdout.splitlines()
        if line.strip().startswith("tests/") and "::" in line
    }
    manifest = json.loads(
        (REPO_ROOT / "governance" / "suite_manifest.json").read_bytes()
    )
    registered = set(manifest["suite"])
    for path in _FROZEN_FILES:
        prefix = str(path.relative_to(REPO_ROOT))
        file_ids = {node for node in nodeids if node.startswith(prefix + "::")}
        assert file_ids, (
            f"{prefix} collected no test IDs — collection must succeed "
            f"post-implementation; stdout tail: {collected.stdout[-400:]!r}"
        )
        missing = sorted(file_ids - registered)
        assert not missing, (
            f"{prefix} IDs not in the frozen manifest (run the suite-freeze "
            f"ceremony; hand edits are refused): {missing}"
        )
