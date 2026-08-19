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
- Remediation R2 (arbitration B4): the loud-no-data scope is real, not
  nominal. combine_coverage(home, children=None) accepts the run's child
  ledger — a mapping of child ID to the environment the frame wired for
  it — and a wired child that produced no data fails loudly NAMING THE
  CHILD, while a run whose ledger holds only unwired children never
  alarms. report_unmeasured(children) consumes that same real input (a
  child-id -> environment mapping) and REFUSES a bare label string
  (TypeError): it names exactly the children whose environment the frame
  did not wire.
- Remediation R3: the frame exposes probe_artifact_home_writable(home),
  the entrypoint's pre-run check — an unwritable artifact home fails
  loudly (RuntimeError naming the home and "not writable") BEFORE any
  suite run writes a single artifact; a writable home returns quietly.
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
import inspect
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


def test_readme_entrypoint_wiring_is_bound_to_wire_child_environment() -> None:
    """R6a (strengthening): the documented entrypoint's environment wiring
    is BOUND to the function — the fence's PYTHONPATH composition and
    COVERAGE_* values must equal wire_child_environment's outputs for the
    default home. Documentation that drifts from the harness is a silent
    unwired suite."""

    frame = _frame()
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = re.search(
        rf"^{re.escape(ENTRYPOINT_HEADING)}\s*\n(.*?)(?=^## |\Z)",
        readme,
        re.MULTILINE | re.DOTALL,
    )
    assert section is not None
    fence = re.search(r"```sh\n(.*?)```", section.group(1), re.DOTALL)
    assert fence is not None, "the section must carry a fenced command block"
    command = fence.group(1)

    documented_start = re.search(
        r'export COVERAGE_PROCESS_START="([^"]+)"', command
    )
    documented_file = re.search(r'export COVERAGE_FILE="([^"]+)"', command)
    documented_path = re.search(r'PYTHONPATH="([^"]+)"', command)
    assert documented_start and documented_file and documented_path, (
        f"the fence must export COVERAGE_PROCESS_START, COVERAGE_FILE and "
        f"compose PYTHONPATH explicitly: {command!r}"
    )

    def _resolved(raw: str) -> str:
        return raw.replace("$PWD", str(REPO_ROOT))

    default_wired = frame.wire_child_environment(
        {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": "src"}
    )
    assert _resolved(documented_start.group(1)) == (
        default_wired["COVERAGE_PROCESS_START"]
    ), (
        "the documented COVERAGE_PROCESS_START must equal the wiring's "
        "output for the default home"
    )
    assert _resolved(documented_file.group(1)) == default_wired["COVERAGE_FILE"], (
        "the documented COVERAGE_FILE must equal the wiring's output for "
        "the default home"
    )

    documented_entries = [
        Path(REPO_ROOT, entry).resolve()
        for entry in documented_path.group(1).split(os.pathsep)
        if entry
    ]
    wired_entries = [
        Path(REPO_ROOT, entry).resolve()
        for entry in default_wired["PYTHONPATH"].split(os.pathsep)
        if entry
    ]
    assert documented_entries == wired_entries, (
        f"the documented PYTHONPATH composition must equal the wiring's "
        f"append-last output: documented={documented_entries!r} "
        f"wired={wired_entries!r}"
    )
    assert documented_entries[-1] == Path(frame.HOOK_DIR).resolve(), (
        "the documented composition rides the hook dir LAST, exactly as "
        "the wiring appends it"
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


def _spine_unwired_child_env(clone_src: Path) -> dict[str, str]:
    """The spine's real unwired-child environment — the replace shape
    (``{**os.environ, "PYTHONPATH": <clone>/src}``) with no
    COVERAGE_PROCESS_START/COVERAGE_FILE inheritance: the recorded way a
    hook silently dies in a ``cwd=<clone>`` child."""

    clone_src.mkdir(parents=True, exist_ok=True)
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("COVERAGE_PROCESS_START", "COVERAGE_FILE", "PYTHONPATH")
    }
    env["PYTHONPATH"] = str(clone_src)
    return env


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

    # Remediation R2b (recorded transformation): the report used to take a
    # hand-passed label string; it now consumes the run's real child ledger
    # (child id -> the environment that child ran with). The assertion is
    # unchanged — unwired children are reported unmeasured, never alarming.
    unwired = _spine_unwired_child_env(Path(empty).parent / "clone" / "src")
    report = frame.report_unmeasured({"clone-child-1": unwired})
    assert isinstance(report, str) and "unmeasured" in report.lower(), (
        f"unwired children are reported unmeasured, never alarming: {report!r}"
    )


def test_wired_child_that_wrote_nothing_fails_loud_naming_the_child(
    tmp_path: Path,
) -> None:
    """R2a: a child the frame WIRED — hook promised — that produces no data
    file is a loud CoverageDataMissing failure NAMING THE CHILD. The
    construction is real: the frame-wired environment with the hook dir
    removed from the child's PYTHONPATH (shadow/loss), running a child
    that exits before any atexit coverage save — on hosts where a venv
    .pth would measure the child regardless of the hook, the early exit is
    what makes 'produced no data' true."""

    frame = _frame()
    assert "children" in inspect.signature(frame.combine_coverage).parameters, (
        "combine_coverage must accept the run's child ledger (children=...) "
        "so the loud no-data detection can name the wired child it is about"
    )
    home = tmp_path / "cov"
    home.mkdir()
    base = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
    }
    promised = frame.wire_child_environment(dict(base), coverage_home=home)
    sabotaged_path = os.pathsep.join(
        entry
        for entry in promised["PYTHONPATH"].split(os.pathsep)
        if Path(entry) != Path(frame.HOOK_DIR)
    )
    child = subprocess.run(
        [sys.executable, "-c", "import os; os._exit(0)"],
        cwd=str(tmp_path),
        env={**promised, "PYTHONPATH": sabotaged_path},
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert child.returncode == 0, child.stderr
    assert not [p for p in home.glob(".coverage.*") if p.name != ".coverage"], (
        "fixture precondition: the sabotaged wired child must have "
        f"produced no data file in {home}"
    )

    with pytest.raises(frame.CoverageDataMissing, match="wired-silent-child"):
        frame.combine_coverage(home, children={"wired-silent-child": promised})


def test_unwired_child_never_alarms_and_is_reported_from_real_environments(
    tmp_path: Path,
) -> None:
    """R2b: a child NOT wired by the frame — the spine's plain replace-shape
    environment, no COVERAGE_PROCESS_START inheritance — raises nothing,
    and appears in report_unmeasured output built from the run's real
    environments. The label-string grammar is refused outright."""

    frame = _frame()
    assert list(inspect.signature(frame.report_unmeasured).parameters) == [
        "children"
    ], (
        "report_unmeasured must consume the run's child ledger "
        "(children: child id -> environment), never a hand-passed label"
    )
    home = tmp_path / "cov"
    home.mkdir()
    unwired = _spine_unwired_child_env(tmp_path / "clone" / "src")
    child = subprocess.run(
        [sys.executable, "-c", "print('ok')"],
        cwd=str(tmp_path),
        env=unwired,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert child.returncode == 0 and child.stdout.strip() == "ok", child.stderr

    with pytest.raises(TypeError):
        frame.report_unmeasured("clone-child-1")

    report = frame.report_unmeasured({"clone-child-1": unwired})
    assert isinstance(report, str), (
        f"the report is a string naming the unmeasured children: {report!r}"
    )
    assert "clone-child-1" in report and "unmeasured" in report.lower(), (
        f"the unwired child must appear in the unmeasured report: {report!r}"
    )

    try:
        frame.combine_coverage(home, children={"clone-child-1": unwired})
    except frame.CoverageDataMissing:
        pytest.fail(
            "an unwired child's missing data must never alarm the "
            "wired-child loud path — the scope is the wiring, not the home"
        )


def test_report_unmeasured_names_exactly_the_unmeasured_children(
    tmp_path: Path,
) -> None:
    """R2c: after a combined run holding at least one measured wired child
    and one unwired child, the report names EXACTLY the unmeasured ones —
    the unwired child appears, the measured wired child does not. The
    ledger mechanism stays free; the observable does not."""

    frame = _frame()
    assert "children" in inspect.signature(frame.combine_coverage).parameters, (
        "combine_coverage must accept the run's child ledger (children=...) "
        "so a combined run can be reconciled against its real children"
    )
    home = tmp_path / "cov"
    home.mkdir()
    base = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", str(Path.home())),
    }
    wired = frame.wire_child_environment(dict(base), coverage_home=home)
    unwired = _spine_unwired_child_env(tmp_path / "clone" / "src")

    wired_child = subprocess.run(
        [sys.executable, "-c", "pass"],
        cwd=str(tmp_path),
        env=wired,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    unwired_child = subprocess.run(
        [sys.executable, "-c", "pass"],
        cwd=str(tmp_path),
        env=unwired,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert wired_child.returncode == 0, wired_child.stderr
    assert unwired_child.returncode == 0, unwired_child.stderr
    assert [p for p in home.glob(".coverage.*") if p.name != ".coverage"], (
        "fixture precondition: the wired child must have produced data"
    )

    children = {"wired-1": wired, "clone-a": unwired}
    combined = frame.combine_coverage(home, children=children)
    assert Path(combined).is_absolute() and Path(combined).is_file(), (
        "a run whose wired children measured combines without alarm"
    )

    report = frame.report_unmeasured(children)
    assert isinstance(report, str), f"the report is a string: {report!r}"
    assert "clone-a" in report, (
        f"the unwired child must be named unmeasured: {report!r}"
    )
    assert "wired-1" not in report, (
        f"a measured wired child is NOT unmeasured — the report must name "
        f"exactly the unmeasured children: {report!r}"
    )


# --- 4b. the pre-run artifact-home probe (remediation R3) ----------------------


def test_pre_run_artifact_home_probe_fails_loud_before_any_suite_run(
    tmp_path: Path,
) -> None:
    """R3: the entrypoint's pre-run writability check. An unwritable
    artifact home fails LOUDLY — RuntimeError naming the home — BEFORE any
    suite run: no artifact (no junitxml, no transcript) is written into
    it. A writable home proceeds quietly."""

    if os.geteuid() == 0:
        pytest.skip(
            "construction limit: root ignores mode bits, so chmod 0555 "
            "cannot make a directory unwritable for this test's process"
        )
    frame = _frame()
    probe = getattr(frame, "probe_artifact_home_writable", None)
    assert probe is not None and callable(probe), (
        "the frame must expose probe_artifact_home_writable(home) — the "
        "entrypoint's pre-run check (mechanism free, the observable frozen)"
    )
    assert list(inspect.signature(probe).parameters) == ["home"], (
        "probe_artifact_home_writable takes exactly the artifact home"
    )

    unwritable = tmp_path / "unwritable-home"
    unwritable.mkdir()
    unwritable.chmod(0o555)
    try:
        with pytest.raises(RuntimeError, match="not writable") as loud:
            probe(unwritable)
        assert str(unwritable) in str(loud.value), (
            f"the failure must name the artifact home: {loud.value!r}"
        )
        assert sorted(p.name for p in unwritable.iterdir()) == [], (
            "the pre-run failure leaves the artifact home untouched — no "
            "junitxml, no transcript, nothing written before the refusal"
        )
    finally:
        unwritable.chmod(0o755)

    writable = tmp_path / "writable-home"
    writable.mkdir()
    assert probe(writable) is None, (
        "a writable artifact home proceeds quietly — the probe alarms "
        "exactly on the unwritable case"
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


# --- 7. module-scope prereq re-evaluation (remediation R6b) ---------------------

_CONSUMPTION_MODULES = (
    "tests/e2e/test_slice055_fixture_consumption_a.py",
    "tests/e2e/test_slice055_fixture_consumption_b.py",
)


def test_module_scope_prereq_fixtures_re_evaluate_per_module_not_per_session(
    tmp_path: Path,
) -> None:
    """R6b: two consuming modules, one precondition flipped between them.
    Module A consumes the module-scoped prereq_signing_key fixture with
    the precondition present (its test runs); module B — same session —
    flips the precondition away before its OWN module-scoped evaluation
    and must see the flipped verdict as a skip carrying the greppable
    reason. A session-cached fixture would hand B A's verdict and run B's
    test instead. The two tiny consuming modules are this slice's
    permitted test surface; consuming the conftest fixtures here also
    kills the dead-fixture finding."""

    key = tmp_path / "worker.key"
    key.write_text("test-private-key-material\n", encoding="utf-8")
    env = {
        key_: value
        for key_, value in os.environ.items()
        if key_ not in ("COVERAGE_PROCESS_START", "COVERAGE_FILE")
    }
    env["RANEX_SIGNING_KEY"] = str(key)
    env["RANEX_SLICE055_FLIP"] = "1"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-rs",
            "--strict-config",
            "--strict-markers",
            *_CONSUMPTION_MODULES,
        ],
        cwd=str(REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, (
        f"skips are not failures; stdout tail: {completed.stdout[-800:]!r} "
        f"stderr: {completed.stderr[-800:]!r}"
    )
    assert "2 passed" not in completed.stdout, (
        "a session-cached fixture verdict would run BOTH modules' tests — "
        f"each module must re-evaluate its own precondition: {completed.stdout!r}"
    )
    assert "1 passed, 1 skipped" in completed.stdout, (
        f"module A (precondition present) passes; module B (flipped) skips: "
        f"{completed.stdout!r}"
    )
    assert "ranex-prereq:signing_key:" in completed.stdout, (
        f"module B's own skip must carry the greppable reason grammar: "
        f"{completed.stdout!r}"
    )
    assert "test_slice055_fixture_consumption_b.py" in completed.stdout, (
        f"the skip must be module B's test, not module A's: {completed.stdout!r}"
    )
