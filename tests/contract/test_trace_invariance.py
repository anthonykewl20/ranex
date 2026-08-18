"""SLICE-054 — trace neutrality and propagation boundary over the real spine.

ADR-031's core proof, frozen red before implementation: with tracing off vs on
— across stderr, fd, file, and directory targets — a real `ranex run` →
`gate evaluate` → `journal verify` spine over a real git subject yields
byte-identical verdict output, evidence.json bytes, journal-verify output, and
run stdout. The governed-root target refusal, the ambient strip for observed
and host-qualification environments, the worker-descriptor refusal, and the
SID tree stitched through the confinement-session controller are frozen here
too.

Real toolchains throughout: real git subjects, real ranex keys, real CLI
subprocesses (the emitter reads its environment once at import, so neutrality
arms run as fresh `python -m ranex.cli.main` processes, never in-process
re-imports). Subjects follow the canonical clone-judges-clone construction
(tests/e2e/test_gating_real_suite.py): src/ranex is vendored into and
committed with each subject, and the spine subprocesses run with
PYTHONPATH=<subject>/src so the subject's own CLI judges the subject. The fd
arm passes an open pipe descriptor to the CLI — test-side plumbing the
grammar explicitly admits. The confinement arms are host-gated with the
repo's standing skip (no delegated cgroup root), matching
tests/security/test_slice046_cmd_run_confinement.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

import ranex.observability  # noqa: F401 — the module's existence is the contract

PROJECT = Path(__file__).resolve().parents[2]
CLI = (sys.executable, "-m", "ranex.cli.main")
TRACE_VARIABLES = ("RANEX_TRACE", "RANEX_TRACE_EVENT", "RANEX_TRACE_PARENT_SID")

CHECK_SCRIPT = "grep -qx content file.txt\n"
GATES = """
gates:
  - gate_id: landing
    rule_id: TESTS_EXECUTED
    blocking: true
    required_claims:
      - claim_id: tests-executed
        command: ["sh", "check.sh"]
"""


def _commit_repo(path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    for key, value in (("user.email", "t@example.invalid"), ("user.name", "test")):
        subprocess.run(["git", "-C", str(path), "config", key, value], check=True)
    subprocess.run(["git", "-C", str(path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-q", "-m", "initial"], check=True)
    return path


class _Subject:
    """A real governed repository plus a real producer key, outside the tree.

    Canonical clone-judges-clone construction (tests/e2e/test_gating_real_suite.py):
    the CLI tree is vendored INTO the subject and committed, so the subject's
    own CLI judges the subject — `governed_repository_root()` resolves through
    the real mechanism, with no monkeypatching anywhere.
    """

    def __init__(self, root: Path) -> None:
        from ranex.foundation.signing import generate_keypair

        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        private, public = generate_keypair()
        self.key = root.parent / "worker.key"
        self.key.write_text(private + "\n", encoding="utf-8")
        self.key.chmod(0o600)
        (root / "file.txt").write_text("content\n", encoding="utf-8")
        (root / "check.sh").write_text(CHECK_SCRIPT, encoding="utf-8")
        (root / "gates.yaml").write_text(GATES, encoding="utf-8")
        (root / "producers.yaml").write_text(
            f"producers:\n  worker: {public}\n", encoding="utf-8"
        )
        (root / ".gitignore").write_text("evidence.json\n", encoding="utf-8")
        shutil.copytree(PROJECT / "src" / "ranex", root / "src" / "ranex")
        _commit_repo(root)

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
        self,
        argv: list[str],
        extra_env: dict[str, str] | None = None,
        pass_fds: tuple[int, ...] = (),
    ) -> subprocess.CompletedProcess[str]:
        env = self.base_env()
        env.update(extra_env or {})
        return subprocess.run(
            [*CLI, *argv],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
            pass_fds=pass_fds,
        )

    def reset_outputs(self) -> None:
        for relative in ("evidence.json", "governance/journal.sqlite3"):
            leftover = self.root / relative
            if leftover.exists():
                leftover.unlink()

    def spine(
        self,
        extra_env: dict[str, str] | None = None,
        pass_fds: tuple[int, ...] = (),
    ) -> dict[str, object]:
        """One full run → gate evaluate → journal verify cycle, captured."""

        self.reset_outputs()
        ran = self.cli(
            [
                "run", "--claim", "tests-executed", "--producer", "worker",
                "--repository", ".", "--evidence", "evidence.json",
                "--producers", "producers.yaml", "--", "sh", "check.sh",
            ],
            extra_env=extra_env,
            pass_fds=pass_fds,
        )
        evaluated = self.cli(
            [
                "gate", "evaluate", "HEAD", "--repository", ".",
                "--gate-catalog", "gates.yaml", "--evidence", "evidence.json",
                "--producers", "producers.yaml",
                "--suite-manifest", "suite_manifest.json",
                "--approver", "reviewer",
            ],
            extra_env=extra_env,
            pass_fds=pass_fds,
        )
        verified = self.cli(
            [
                "journal", "verify", "--repository", ".",
                "--journal", "governance/journal.sqlite3",
            ],
            extra_env=extra_env,
            pass_fds=pass_fds,
        )
        evidence = self.root / "evidence.json"
        return {
            "run_rc": ran.returncode,
            "run_out": ran.stdout,
            "run_err": ran.stderr,
            "eval_rc": evaluated.returncode,
            "eval_out": evaluated.stdout,
            "verify_rc": verified.returncode,
            "verify_out": verified.stdout,
            "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
        }


@pytest.fixture(scope="module")
def subject(tmp_path_factory: pytest.TempPathFactory) -> _Subject:
    return _Subject(tmp_path_factory.mktemp("invariance") / "governed")


@pytest.fixture(scope="module")
def off_baseline(subject: _Subject) -> dict[str, object]:
    baseline = subject.spine()
    assert baseline["run_rc"] == 0, baseline["run_err"]
    assert baseline["eval_rc"] == 0, baseline["eval_out"]
    assert baseline["verify_rc"] == 0, baseline["verify_out"]
    assert baseline["run_err"] == "", "no trace env set: stderr must stay empty"
    return baseline


def _assert_neutral(
    arm: dict[str, object],
    baseline: dict[str, object],
    *,
    quiet_run_err: bool = False,
) -> None:
    for key in ("run_rc", "run_out", "eval_rc", "eval_out", "verify_rc", "verify_out",
                "evidence_sha256"):
        assert arm[key] == baseline[key], (
            f"tracing changed {key}: off={baseline[key]!r} on={arm[key]!r}"
        )
    if quiet_run_err:
        # S1 (remediation strengthening): a valid non-stderr target must keep
        # the run's stderr byte-empty — the stream belongs to the governed
        # command, and a valid trace target that leaks warnings or events onto
        # it is a neutrality defect of its own. Default-off keeps the refusal
        # arms (which legitimately warn) and the stderr arm unchanged.
        assert arm["run_err"] == "", (
            f"a valid off-stderr trace target leaked onto the run's stderr: "
            f"{arm['run_err']!r}"
        )


def _version_first(events: list[dict]) -> None:
    assert events, "an admitted target must receive events"
    assert events[0]["event"] == "version"


def test_stderr_target_is_verdict_neutral_over_the_spine(
    subject: _Subject, off_baseline: dict[str, object]
) -> None:
    arm = subject.spine(extra_env={"RANEX_TRACE": "1"})
    _assert_neutral(arm, off_baseline)
    assert '"event":"version"' in arm["run_err"]


def test_file_target_is_verdict_neutral_over_the_spine(
    subject: _Subject,
    off_baseline: dict[str, object],
    tmp_path: Path,
) -> None:
    target = tmp_path / "trace.jsonl"
    arm = subject.spine(extra_env={"RANEX_TRACE": str(target)})
    _assert_neutral(arm, off_baseline, quiet_run_err=True)
    events = [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line
    ]
    _version_first(events)
    assert any(event["event"] == "stage" for event in events)


def test_directory_target_is_verdict_neutral_over_the_spine(
    subject: _Subject,
    off_baseline: dict[str, object],
    tmp_path: Path,
) -> None:
    directory = tmp_path / "trace-dir"
    directory.mkdir()
    arm = subject.spine(extra_env={"RANEX_TRACE": str(directory)})
    _assert_neutral(arm, off_baseline, quiet_run_err=True)
    files = sorted(path for path in directory.iterdir() if path.is_file())
    assert files, "one file per traced process"
    for path in files:
        events = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        _version_first(events)
        assert path.name == events[0]["sid"].rsplit("/", 1)[-1]


def test_fd_target_is_verdict_neutral_over_the_spine(
    subject: _Subject, off_baseline: dict[str, object]
) -> None:
    """The pipe descriptor is passed to each CLI invocation — test-side
    plumbing the fd target grammar explicitly allows. The write end is pinned
    to single-digit fd 5 because the grammar admits single digits 2-9 only."""

    read_end, write_end = os.pipe()

    def _occupied(descriptor: int) -> int | None:
        try:
            return os.dup(descriptor)
        except OSError:
            return None

    saved = _occupied(5)
    os.dup2(write_end, 5)
    os.close(write_end)
    write_end = 5
    try:
        arm = subject.spine(extra_env={"RANEX_TRACE": "5"}, pass_fds=(5,))
        os.close(5)
        write_end = -1
        stream = b""
        while True:
            chunk = os.read(read_end, 65536)
            if not chunk:
                break
            stream += chunk
        assert stream, "an admitted fd target must receive events"
        first = json.loads(stream.split(b"\n", 1)[0].decode("utf-8"))
        assert first["event"] == "version"
    finally:
        if write_end >= 0:
            os.close(write_end)
        os.close(read_end)
        if saved is not None:
            os.dup2(saved, 5)
            os.close(saved)
    _assert_neutral(arm, off_baseline, quiet_run_err=True)


def test_governed_root_target_is_refused_and_the_run_proceeds(
    subject: _Subject, off_baseline: dict[str, object]
) -> None:
    target = subject.root / "trace.jsonl"
    arm = subject.spine(extra_env={"RANEX_TRACE": str(target)})
    _assert_neutral(arm, off_baseline)
    assert not target.exists(), "no trace byte may land in the governed tree"
    assert str(target) in arm["run_err"], "a case-(a) refusal names the full path"


def test_cli_invoked_outside_its_checkout_writes_no_trace_into_the_subject(
    tmp_path: Path,
) -> None:
    """N2(b) — cwd-anchored admission is not the CLI's governed root.

    The CLI invoked from a cwd OUTSIDE its checkout still governs the subject
    (governed_repository_root resolves the checkout containing the CLI, not
    the caller's cwd), but the emitter admits targets against the CWD's git
    root — so RANEX_TRACE=<path inside the subject's tree> sails past the
    in-repo refusal and writes into the governed tree before the command even
    runs (dirtying the subject the CLI is about to judge). The observable:
    no trace file appears inside the subject, whatever the exit path. The
    journal-verify usage error proves dispatch reached the subcommand, past
    the stage boundary that triggers admission.

    Function-scoped subject by design (round-2 harness amendment, ruled a
    construction defect): the journal-absence construction check must not
    depend on other arms' ordering — the module-scoped subject carries a
    journal left by the spine arms, which turns the same check into a
    file-order contradiction. This arm owns a fresh subject whose journal
    state is its own.
    """

    subject = _Subject(tmp_path / "governed")
    target = subject.root / "trace.jsonl"
    environment = subject.base_env() | {"RANEX_TRACE": str(target)}
    completed = subprocess.run(
        [
            *CLI,
            "journal", "verify",
            "--journal", "governance/journal.sqlite3",
        ],
        cwd=tmp_path,  # outside the subject; no .git at or above
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )

    assert completed.returncode == 2, completed.stdout + completed.stderr
    assert "does not exist" in completed.stderr, (
        "construction check: dispatch reached journal verify"
    )
    assert not target.exists(), (
        "the emitter admitted and wrote a trace file inside the governed "
        "subject's tree from an outside cwd"
    )


# --- the propagation boundary -------------------------------------------------


def test_observed_command_environments_never_see_trace_variables(
    tmp_path: Path,
) -> None:
    """An observed command that branches on the trace variables must see
    nothing, with tracing off AND on — the marker file never appears."""

    subject = _Subject(tmp_path / "governed")
    marker = tmp_path / "leaked-marker"
    probe = (
        'if [ -n "$RANEX_TRACE$RANEX_TRACE_EVENT$RANEX_TRACE_PARENT_SID" ]; '
        f"then touch {marker}; fi"
    )
    target = tmp_path / "trace.jsonl"

    for extra_env in ({}, {"RANEX_TRACE": str(target), "RANEX_TRACE_PARENT_SID": "planted"}):
        subject.reset_outputs()
        completed = subject.cli(
            [
                "run", "--claim", "tests-executed", "--producer", "worker",
                "--repository", ".", "--evidence", "evidence.json",
                "--producers", "producers.yaml", "--", "sh", "-c", probe,
            ],
            extra_env=extra_env,
        )
        assert completed.returncode == 0, completed.stderr
        assert not marker.exists(), "trace variables leaked into the observed command"
        if extra_env:
            assert target.exists(), "the on-arm must actually be tracing"


def test_host_qualification_ambient_copy_strips_trace_variables(
    tmp_path: Path,
) -> None:
    """The host-qualification path copies os.environ wholesale today; the strip
    is mandatory slice work (ADR-031 sad path 13). The qualification probe
    writes a marker when it sees any trace variable."""

    subject = _Subject(tmp_path / "qualified")
    root = subject.root
    marker = tmp_path / "ambient-marker"
    probe = (
        "import os, pathlib\n"
        "leaked = [k for k in "
        "('RANEX_TRACE', 'RANEX_TRACE_EVENT', 'RANEX_TRACE_PARENT_SID') "
        "if os.environ.get(k)]\n"
        "if leaked:\n"
        f"    pathlib.Path({str(marker)!r}).write_text(','.join(leaked))\n"
        "pathlib.Path('artifacts').mkdir(exist_ok=True)\n"
        "pathlib.Path('artifacts/qualification.json').write_text('{}')\n"
    )
    # The qualification claim's report is bound by the exact argv token
    # --report=<path> inside the catalog command itself
    # (src/ranex/policy/adapters/configuration/yaml/slice_gate_loader.py);
    # the probe ignores the extra argv element.
    command = ["python", "-c", probe, "--report=artifacts/qualification.json"]
    (root / "gates.yaml").write_text(
        "gates:\n"
        "  - gate_id: landing\n"
        "    rule_id: HOST_QUALIFIED\n"
        "    blocking: true\n"
        "    required_claims:\n"
        "      - claim_id: host-qualification\n"
        f"        command: {json.dumps(command)}\n"
        "        qualification_report: artifacts/qualification.json\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(root), "add", "gates.yaml"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-q", "-m", "qualification catalog"],
        check=True,
    )
    target = tmp_path / "trace.jsonl"

    for extra_env in ({}, {"RANEX_TRACE": str(target), "RANEX_TRACE_PARENT_SID": "planted"}):
        completed = subject.cli(
            [
                "run", "--claim", "host-qualification", "--producer", "worker",
                "--repository", ".", "--evidence", "evidence.json",
                "--producers", "producers.yaml", "--gate-catalog", "gates.yaml",
                "--", *command,
            ],
            extra_env=extra_env,
        )
        assert completed.returncode == 0, completed.stderr
        assert not marker.exists(), "the ambient copy leaked trace variables"
        if extra_env:
            assert target.exists(), "the on-arm must actually be tracing"


# --- the confinement-session seam (host-gated) --------------------------------


def _confinement_host_ready() -> tuple[bool, str]:
    required = [Path("/sys/fs/cgroup/cgroup.controllers"), Path("/usr/bin/bwrap")]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        return False, f"real host prerequisites absent: {missing}"
    if not os.access("/sys/fs/cgroup", os.W_OK):
        return False, "no delegated writable cgroup-v2 root"
    return True, ""


def _confinement_repo(tmp_path: Path) -> _Subject:
    subject = _Subject(tmp_path / "governed")
    for relative in (
        "governance/confinement/strict-local-v1.json",
        "governance/confinement/strict-local-host-v1.json",
        "governance/confinement/native-launcher-build-v1.json",
        "native/ranex-worker-launcher/launcher.c",
    ):
        destination = subject.root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PROJECT / relative, destination)
    (subject.root / ".gitignore").write_text("evidence.json\n.local/\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(subject.root), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(subject.root), "commit", "-q", "-m", "confinement inputs"],
        check=True,
    )
    return subject


def _build_launcher(subject: _Subject) -> None:
    environment = subject.base_env()
    manifest = "governance/confinement/native-launcher-build-v1.json"
    for arguments in (
        ["launcher-build", "--manifest", manifest, "--source",
         "native/ranex-worker-launcher/launcher.c", "--output",
         ".local/ranex/build/strict-local-v1/ranex-worker-launcher"],
        ["launcher-install", "--manifest", manifest, "--artifact",
         ".local/ranex/build/strict-local-v1/ranex-worker-launcher", "--destination",
         ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher"],
        ["qualify", "--profile", "governance/confinement/strict-local-host-v1.json",
         "--artifact", ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
         "--manifest", manifest, "--report",
         ".local/ranex/qualification/strict-local-v1.json"],
    ):
        completed = subprocess.run(
            [sys.executable, "-m", "ranex.cli.host_confinement", *arguments],
            cwd=subject.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr


def _find_controller(deadline: float) -> tuple[dict[str, str], list[str], dict] | None:
    """The live controller's environment, argv, and descriptor — via /proc."""

    while time.monotonic() < deadline:
        for entry in Path("/proc").iterdir():
            if not entry.name.isdigit():
                continue
            try:
                cmdline = (entry / "cmdline").read_bytes()
                environ = (entry / "environ").read_bytes()
            except OSError:
                continue
            parts = [part for part in cmdline.split(b"\0") if part]
            if b"ranex.cli.host_confinement" not in parts or b"session" not in parts:
                continue
            argv = [part.decode("utf-8", "replace") for part in parts]
            controller_env = {}
            for item in environ.split(b"\0"):
                if b"=" in item:
                    name, _, value = item.partition(b"=")
                    controller_env[name.decode("utf-8", "replace")] = value.decode(
                        "utf-8", "replace"
                    )
            descriptor_path = Path(argv[argv.index("--descriptor") + 1])
            descriptor = json.loads(descriptor_path.read_text(encoding="utf-8"))
            return controller_env, argv, descriptor
        time.sleep(0.05)
    return None


def _run_confined(subject: _Subject, extra_env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subject.cli(
        [
            "run", "--claim", "tests-executed", "--producer", "worker",
            "--repository", ".", "--evidence", "evidence.json",
            "--producers", "producers.yaml", "--confinement", "strict-local",
            "--", "/bin/sleep", "4",
        ],
        extra_env=extra_env,
    )


def test_traced_strict_local_run_chains_the_controller_and_keeps_the_descriptor_clean(
    tmp_path: Path,
) -> None:
    ready, reason = _confinement_host_ready()
    if not ready:
        pytest.skip(f"SLICE-054 real confinement unavailable: {reason}")

    subject = _confinement_repo(tmp_path)
    _build_launcher(subject)
    target = tmp_path / "controller-trace.jsonl"

    # Off arm: the controller environment is byte-identical to today's.
    process = subprocess.Popen(
        [*CLI, "run", "--claim", "tests-executed", "--producer", "worker",
         "--repository", ".", "--evidence", "evidence.json",
         "--producers", "producers.yaml", "--confinement", "strict-local",
         "--", "/bin/sleep", "4"],
        cwd=subject.root,
        env=subject.base_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    found = _find_controller(time.monotonic() + 30)
    out, err = process.communicate(timeout=180)
    assert process.returncode == 0, out + err
    assert found is not None, "the confinement controller never ran"
    controller_env, _argv, descriptor = found
    assert set(controller_env) == {"PATH", "PYTHONPATH", "LC_ALL", "TZ"}
    assert descriptor["environment"] == {"LC_ALL": "C", "TZ": "UTC"}

    # On arm: the controller gains exactly the enabled trace target variable
    # plus RANEX_TRACE_PARENT_SID (ADR-031: "by exactly the trace variables"),
    # and its chained events stitch into the parent's tree in one file.
    subject.reset_outputs()
    process = subprocess.Popen(
        [*CLI, "run", "--claim", "tests-executed", "--producer", "worker",
         "--repository", ".", "--evidence", "evidence.json",
         "--producers", "producers.yaml", "--confinement", "strict-local",
         "--", "/bin/sleep", "4"],
        cwd=subject.root,
        env=subject.base_env() | {"RANEX_TRACE": str(target)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    found = _find_controller(time.monotonic() + 30)
    out, err = process.communicate(timeout=180)
    assert process.returncode == 0, out + err
    assert found is not None, "the confinement controller never ran"
    controller_env, _argv, descriptor = found
    assert set(controller_env) == {
        "PATH", "PYTHONPATH", "LC_ALL", "TZ", "RANEX_TRACE", "RANEX_TRACE_PARENT_SID",
    }
    assert controller_env["RANEX_TRACE"] == str(target)
    assert descriptor["environment"] == {"LC_ALL": "C", "TZ": "UTC"}, (
        "the chain never rides an observed command: the launcher descriptor "
        "env stays frozen at {LC_ALL, TZ}"
    )

    events = [
        json.loads(line)
        for line in target.read_text(encoding="utf-8").splitlines()
        if line
    ]
    _version_first(events)
    parent_sids = {event["sid"] for event in events if "/" not in event["sid"]}
    assert len(parent_sids) == 1
    (parent_sid,) = parent_sids
    assert controller_env["RANEX_TRACE_PARENT_SID"] == parent_sid
    chained = [event for event in events if event["sid"].startswith(parent_sid + "/")]
    assert chained, "controller child events must carry the parent SID"
    assert all(event["sid"] != parent_sid for event in chained)

    # Sad path 7: a worker descriptor carrying RANEX_TRACE* is refused
    # pre-spawn by the controller's launcher allowlist.
    session_root = tmp_path / "hostile-session"
    for name in ("subject", "toolchain", "output", "scratch"):
        (session_root / name).mkdir(parents=True)
    for relative in (
        "governance/confinement/strict-local-v1.json",
        "governance/confinement/strict-local-host-v1.json",
        "governance/confinement/native-launcher-build-v1.json",
        ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
        ".local/ranex/qualification/strict-local-v1.json",
    ):
        destination = session_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(subject.root / relative, destination)
    from ranex.foundation.canonical import canonical_json_bytes

    hostile = {
        "schema": "ranex-confinement-command-v1",
        "argv": ["/bin/true"],
        "environment": {"LC_ALL": "C", "TZ": "UTC", "RANEX_TRACE": "1"},
        "subject": "subject",
        "toolchain": "toolchain",
        "output": "output",
        "scratch": "scratch",
        "limits": {
            "cpu_usage_usec": 1_000_000,
            "memory_bytes": 134_217_728,
            "output_bytes": 65_536,
            "output_depth": 8,
            "output_inodes": 32,
            "pids": 16,
            "wall_time_ms": 5_000,
        },
    }
    (session_root / "hostile.json").write_bytes(canonical_json_bytes(hostile))
    refused = subprocess.run(
        [sys.executable, "-m", "ranex.cli.host_confinement", "session",
         "--profile", "governance/confinement/strict-local-v1.json",
         "--host-profile", "governance/confinement/strict-local-host-v1.json",
         "--artifact", ".local/ranex/libexec/strict-local-v1/ranex-worker-launcher",
         "--manifest", "governance/confinement/native-launcher-build-v1.json",
         "--qualification", ".local/ranex/qualification/strict-local-v1.json",
         "--descriptor", "hostile.json", "--result", "result.json"],
        cwd=session_root,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONPATH": str(PROJECT / "src"),
            "LC_ALL": "C",
            "TZ": "UTC",
        },
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert refused.returncode != 0
    assert "allowlist" in refused.stdout + refused.stderr
    assert not (session_root / "result.json").exists(), (
        "a refused descriptor must never reach a spawn or a result"
    )
